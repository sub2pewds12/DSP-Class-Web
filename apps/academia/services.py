from typing import List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from apps.academia.models import Assignment, TeamSubmission, SubmissionFile, ClassDocument
from apps.users.models import CustomUser
from apps.core.services.audit_service import AuditService
from apps.core.models import AuditLog
from django.core.cache import cache
from django.db.models import Avg, Max, Q

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
        
        # File type validation
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.rtf',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.jpg', '.jpeg', '.png', '.gif', '.svg',
            '.py', '.ipynb', '.m', '.cpp', '.c', '.h', '.java', '.html', '.css', '.js', '.json'
        ]
        import os
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValueError(f"File type '{ext}' is not supported. Allowed types are: {', '.join(allowed_extensions)}")
        
        with transaction.atomic():
            # Append Logic: Find existing submission or create a new one
            old_subs = TeamSubmission.objects.filter(team=team, assignment=assignment)
            if old_subs.exists():
                submission = old_subs.first()
                # Update metadata for the new append action
                from django.utils import timezone
                submission.title = title
                submission.submitted_by = user
                submission.submitted_at = timezone.now()
                submission.save()
                
                AuditService.log_event(
                    action="SUBMISSION_APPEND",
                    target_type="Assignment",
                    target_id=str(assignment.id),
                    description=f"Team '{team.name}' appended files to their submission for '{assignment.title}'.",
                    metadata={"team": team.name, "assignment": assignment.title, "new_files": len(files)}
                )
            else:
                submission = TeamSubmission.objects.create(
                    team=team,
                    assignment=assignment,
                    title=title,
                    submitted_by=user
                )
                
                AuditService.log_event(
                    action="SUBMISSION_CREATE",
                    target_type="Assignment",
                    target_id=str(assignment.id),
                    description=f"Team '{team.name}' created a new submission for '{assignment.title}'.",
                    metadata={"team_id": team.id, "files_count": len(files)}
                )
            
            for f in files:
                SubmissionFile.objects.create(submission=submission, file=f)
            
            # Audit the deadline status
            status = "on time"
            if submission.submitted_at and assignment.deadline and submission.submitted_at > assignment.deadline:
                status = "LATE"
                
        # Invalidate dashboard caches
        cache.delete_many(["dashboard_teacher", "dashboard_students"])
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
        # Invalidate teacher dashboard cache (student dashboard might also need it if grades released)
        cache.delete_many(["dashboard_teacher", "dashboard_students"])
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
        # Invalidate caches
        cache.delete_many(["dashboard_teacher", "dashboard_students"])
        return title

class AcademiaService:
    """
    Handles course actions related to assignments, documents, and student roles.
    """

    @staticmethod
    def release_grades(assignment: Assignment, user: CustomUser) -> Assignment:
        """Releases grades for an assignment and logs the event."""
        assignment.grades_released = True
        assignment.save()

        AuditService.log_event(
            action="GRADES_RELEASED",
            target_type="Assignment",
            target_id=str(assignment.id),
            description=f"Grades for '{assignment.title}' released by {user.username}.",
            metadata={"title": assignment.title, "released_by": user.username}
        )
        # Invalidate student dashboard cache to show released grades
        cache.delete("dashboard_students")
        return assignment
    
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
    def get_student_roles(student):
        """
        Parses a student's comma-separated role string and maps to icons.
        Returns a dict with 'role_list', 'role_icons', and 'role_data'.
        """
        if not student:
            return {'role_list': [], 'role_icons': [], 'role_data': [], 'role_icon': 'person'}

        role_icon_map = {
            'leader': 'terminal-fill', 'project lead': 'terminal-fill',
            'architect': 'diagram-3-fill', 'systems architect': 'diagram-3-fill',
            'signal': 'activity', 'dsp engineer': 'activity',
            'algorithm': 'braces', 'algorithm developer': 'braces',
            'embedded': 'cpu-fill', 'embedded engineer': 'cpu-fill',
            'analyst': 'bar-chart-fill', 'quality engineer': 'bar-chart-fill',
            'writer': 'file-earmark-text', 'technical writer': 'file-earmark-text',
            'developer': 'code-slash', 'designer': 'palette2', 'researcher': 'search'
        }
        
        # Support multiple roles (comma separated)
        raw_roles = [r.strip() for r in (student.role or "").split(',') if r.strip()]
        if not raw_roles: raw_roles = ["Member"]
        
        role_list = raw_roles
        role_icons = [role_icon_map.get(r.lower(), 'person-badge') for r in raw_roles]
        role_data = [{'label': label, 'icon': icon} for label, icon in zip(role_list, role_icons)]
        
        return {
            'role_list': role_list,
            'role_icons': role_icons,
            'role_data': role_data,
            'role_icon': role_icons[0] if role_icons else 'person-badge'
        }

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
        # Invalidate caches
        cache.delete_many(["dashboard_teacher", "dashboard_students"])
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
        # Invalidate caches
        cache.delete_many(["dashboard_teacher", "dashboard_students"])
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

    @staticmethod
    def get_teacher_dashboard_context(user: CustomUser):
        """
        Gathers all data needed for the lecturer dashboard (Cached).
        """
        def _get_context():
            from apps.teams.models import Team, ClassDocument, Assignment, Lecturer
            Lecturer.objects.get_or_create(user=user)

            teams = Team.objects.prefetch_related(
                'members__user',
                'submissions__assignment',
                'submissions__files'
            ).all().order_by('name')

            documents = ClassDocument.objects.all().order_by('-uploaded_at')
            assignments = Assignment.objects.all().order_by('-deadline')
            
            trends = AcademiaService.get_submission_trends()
            
            # Offload status mapping logic to service
            teams = AcademiaService.get_team_status_matrix(teams, assignments)

            return {
                'teams': teams,
                'documents': list(documents),
                'assignments': list(assignments),
                'trend_labels': trends['labels'],
                'trend_data': trends['data'],
                'trend_details': trends['details'],
            }

        # Global cache for teacher dashboard (shared across lecturers)
        return cache.get_or_set("dashboard_teacher", _get_context, timeout=300)

    @staticmethod
    def get_assignment_stats(assignment_id: int):
        """Calculates anonymized statistics for an assignment."""
        stats = TeamSubmission.objects.filter(
            assignment_id=assignment_id, 
            grade__isnull=False
        ).aggregate(avg=Avg('grade'), max=Max('grade'))
        
        return {
            'average': round(stats['avg'] or 0, 1),
            'high': stats['max'] or 0
        }

    @staticmethod
    def get_student_dashboard_context(user: CustomUser, team=None):
        """
        Gathers data for the student dashboard (Cached partially).
        """
        from apps.teams.models import ClassDocument, Assignment
        from django.db.models import Prefetch

        def _get_docs_and_assigns():
            documents = ClassDocument.objects.all().order_by('-uploaded_at')
            assignments = Assignment.objects.all().order_by('-deadline')
            return list(documents), list(assignments)

        # Cache global documents and assignments
        documents, assignments_raw = cache.get_or_set("dashboard_students", _get_docs_and_assigns, timeout=300)
        
        # Clone assignments to avoid modifying cached objects shared across sessions
        import copy
        assignments = [copy.copy(a) for a in assignments_raw]

        # Enrichment: Team Activity Feed
        team_activity = []
        if team:
            # Fetch logs involving team members or explicit team_id metadata
            team_member_ids = team.members.values_list('user_id', flat=True)
            team_activity = AuditLog.objects.filter(
                Q(actor_id__in=team_member_ids) | Q(metadata__team_id=team.id)
            ).select_related('actor').order_by('-timestamp')[:10]

            # Attach team-specific submissions with their files
            team_subs = team.submissions.prefetch_related('files').all().order_by('-submitted_at')
            for a in assignments:
                matching_sub = next((s for s in team_subs if s.assignment_id == a.id), None)
                a.team_submission = matching_sub
                a.is_submitted = matching_sub is not None

            # NEW: Enrichment: Member Status & Roles
            from django.db.models import Max
            last_activities = AuditLog.objects.filter(
                actor_id__in=team_member_ids
            ).values('actor_id').annotate(last_active=Max('timestamp'))
            
            activity_map = {item['actor_id']: item['last_active'] for item in last_activities}
            from django.utils import timezone
            now = timezone.now()
            
            for m in team.members.all():
                m.last_active = activity_map.get(m.user_id)
                # Online if active in the last 10 minutes
                m.is_online = m.last_active and (now - m.last_active).total_seconds() < 600
                
                # Use centralized role mapping
                roles = AcademiaService.get_student_roles(m)
                m.role_list = roles['role_list']
                m.role_icons = roles['role_icons']
                m.role_data = roles['role_data']
                m.role_icon = roles['role_icon']

        # Enrichment: Dashboard Deadlines (Prioritize upcoming, then recently passed to fill 4 slots)
        from django.utils import timezone
        now = timezone.now()
        upcoming = sorted([a for a in assignments if a.deadline > now and a.is_active], key=lambda x: x.deadline)
        passed = sorted([a for a in assignments if a.deadline <= now and a.is_active], key=lambda x: x.deadline, reverse=True)
        
        compact_deadlines = (upcoming + passed)[:4]
        next_deadline = upcoming[0] if upcoming else None

        # Metadata for the Visual Role Selector
        role_metadata = [
            {'id': 'Leader', 'label': 'Project Lead', 'icon': 'terminal-fill', 'desc': 'Oversees project architecture and delivery milestones.'},
            {'id': 'Architect', 'label': 'Systems Architect', 'icon': 'diagram-3-fill', 'desc': 'Integrates high-level hardware and software design.'},
            {'id': 'Signal', 'label': 'DSP Engineer', 'icon': 'activity', 'desc': 'Specializes in signal processing theory and mathematics.'},
            {'id': 'Algorithm', 'label': 'Algorithm Developer', 'icon': 'braces', 'desc': 'Implements core algorithms and analyzes computational complexity.'},
            {'id': 'Embedded', 'label': 'Embedded Engineer', 'icon': 'cpu-fill', 'desc': 'Develops low-level firmware and hardware logic.'},
            {'id': 'Analyst', 'label': 'Quality Engineer', 'icon': 'bar-chart-fill', 'desc': 'Performs signal verification and performance analysis.'},
            {'id': 'Writer', 'label': 'Technical Writer', 'icon': 'file-earmark-text', 'desc': 'Maintains technical documentation and project reports.'},
        ]
        role_ids_only = [r['id'] for r in role_metadata]

        return {
            'documents': documents,
            'assignments': assignments,
            'team_activity': team_activity,
            'next_deadline': next_deadline,
            'upcoming_deadlines': upcoming,
            'compact_deadlines': compact_deadlines,
            'role_metadata': role_metadata,
            'role_ids_only': role_ids_only,
            'now': now,
        }

# Backward compatibility
AssignmentService = AcademiaService
