from typing import List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from apps.academia.models import Assignment, TeamSubmission, SubmissionFile, ClassDocument
from apps.users.models import CustomUser
from apps.core.services.audit_service import AuditService

class SubmissionService:
    """
    Handles student assignment submissions logic.
    """
    
    @staticmethod
    def create_submission(
        user: CustomUser, 
        assignment: Assignment, 
        title: str, 
        files: List[UploadedFile]
    ) -> TeamSubmission:
        """
        Creates a new submission for a team and attaches files.
        """
        if not hasattr(user, 'student_profile') or not user.student_profile.team:
            raise ValueError("User must be part of a team to submit assignments.")
            
        team = user.student_profile.team
        
        with transaction.atomic():
            # Enforcement: New submissions replace ALL previous files for this assignment
            old_subs = TeamSubmission.objects.filter(team=team, assignment=assignment)
            if old_subs.exists():
                AuditService.log_event(
                    action="SUBMISSION_OVERWRITE",
                    target_type="Assignment",
                    target_id=str(assignment.id),
                    description=f"Team '{team.name}' updated their submission for '{assignment.title}'. Old records purged.",
                    metadata={"team": team.name, "assignment": assignment.title}
                )
            old_subs.delete()
            
            submission = TeamSubmission.objects.create(
                team=team,
                assignment=assignment,
                title=title,
                submitted_by=user
            )
            
            for f in files:
                SubmissionFile.objects.create(submission=submission, file=f)
            
            # Audit the creation
            status = "on time"
            if submission.submitted_at and assignment.deadline and submission.submitted_at > assignment.deadline:
                status = "LATE"
                
            AuditService.log_event(
                action="SUBMISSION_CREATE",
                target_type="Assignment",
                target_id=str(assignment.id),
                description=f"Team '{team.name}' submitted files for '{assignment.title}' ({status}).",
                metadata={"team_id": team.id, "files_count": len(files), "status": status}
            )
                
        return submission

    @staticmethod
    def grade_submission(submission, grade, feedback):
        """Updates the grade and feedback for a submission."""
        submission.grade = grade
        submission.feedback = feedback
        submission.save()
        
        AuditService.log_event(
            action="GRADE_UPDATE",
            target_type="TeamSubmission",
            target_id=str(submission.id),
            description=f"Grade updated for {submission.team.name} on '{submission.assignment.title}'.",
            metadata={"grade": str(grade), "team": submission.team.name}
        )
        return submission

    @staticmethod
    def delete_submission(submission, user_requesting):
        """Safely deletes a submission and logs the event."""
        title = submission.title
        team_name = submission.team.name
        
        submission.delete()
        
        AuditService.log_event(
            action="SUBMISSION_DELETE",
            target_type="TeamSubmission",
            target_id=str(submission.id),
            description=f"Submission '{title}' for team '{team_name}' was deleted by {user_requesting.username}.",
            metadata={"team": team_name, "deleted_by": user_requesting.username}
        )
        return title

class AssignmentService:
    """
    Handles lecturer actions related to assignments and documents.
    """
    
    @staticmethod
    def get_team_status_matrix(teams, assignments):
        """
        Creates a status map for a list of teams across assignments.
        Returns the teams with an 'assignment_status' attribute attached.
        """
        for t in teams:
            t.assignment_status = []
            # Optimization: Use a dictionary for faster lookups
            team_subs = {s.assignment_id: s for s in t.submissions.all()}
            
            for a in assignments:
                # Determine the 'best' submission (latest)
                sub = team_subs.get(a.id)
                t.assignment_status.append({
                    'assignment': a, 
                    'submission': sub,
                })
        return teams

    @staticmethod
    def create_assignment(
        user: CustomUser,
        title: str,
        deadline: str,
        description: str = "",
        instruction_file: Optional[UploadedFile] = None
    ) -> Assignment:
        """Creates a new assignment."""
        assign = Assignment.objects.create(
            title=title,
            description=description,
            deadline=deadline,
            created_by=user,
            instruction_file=instruction_file
        )
        
        AuditService.log_event(
            action="ASSIGNMENT_CREATE",
            target_type="Assignment",
            target_id=str(assign.id),
            description=f"New assignment '{title}' created by {user.username}.",
            metadata={"title": title, "deadline": str(deadline)}
        )
        return assign

    @staticmethod
    def upload_document(
        user: CustomUser,
        title: str,
        file: UploadedFile
    ) -> ClassDocument:
        """Uploads a class document."""
        doc = ClassDocument.objects.create(
            title=title,
            file=file,
            uploaded_by=user
        )
        
        AuditService.log_event(
            action="DOCUMENT_UPLOAD",
            target_type="ClassDocument",
            target_id=str(doc.id),
            description=f"Document '{title}' uploaded by {user.username}.",
            metadata={"title": title}
        )
        return doc

    @staticmethod
    def get_submission_trends(days=14):
        """Calculates submission trends for dashboard charts."""
        from django.utils import timezone
        last_n_days = timezone.now() - timezone.timedelta(days=days)
        trends_raw = TeamSubmission.objects.filter(submitted_at__gte=last_n_days).select_related('team').order_by('submitted_at')
        
        trends_map = {}
        for sub in trends_raw:
            d = sub.submitted_at.date()
            if d not in trends_map:
                trends_map[d] = {'count': 0, 'teams': set()}
            trends_map[d]['count'] += 1
            trends_map[d]['teams'].add(sub.team.name)

        sorted_dates = sorted(trends_map.keys())
        labels = [d.strftime('%b %d') for d in sorted_dates]
        data = [trends_map[d]['count'] for d in sorted_dates]
        
        details = []
        for d in sorted_dates:
            teams_list = list(trends_map[d]['teams'])
            detail = ", ".join(teams_list[:3])
            if len(teams_list) > 3:
                detail += f" and {len(teams_list) - 3} more..."
            details.append(detail)
            
        return {
            'labels': labels,
            'data': data,
            'details': details
        }
