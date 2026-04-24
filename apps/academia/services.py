from typing import List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from apps.academia.models import Assignment, TeamSubmission, SubmissionFile, ClassDocument
from apps.users.models import CustomUser

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
            TeamSubmission.objects.filter(team=team, assignment=assignment).delete()
            
            submission = TeamSubmission.objects.create(
                team=team,
                assignment=assignment,
                title=title,
                submitted_by=user
            )
            
            for f in files:
                SubmissionFile.objects.create(submission=submission, file=f)
                
        return submission

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
        return Assignment.objects.create(
            title=title,
            description=description,
            deadline=deadline,
            created_by=user,
            instruction_file=instruction_file
        )

    @staticmethod
    def upload_document(
        user: CustomUser,
        title: str,
        file: UploadedFile
    ) -> ClassDocument:
        """Uploads a class document."""
        return ClassDocument.objects.create(
            title=title,
            file=file,
            uploaded_by=user
        )
