from django.db import models
from django.conf import settings

class ClassDocument(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='class_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'teams_classdocument'

class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instruction_file = models.FileField(upload_to='assignment_instructions/', null=True, blank=True)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_assignments')
    grades_released = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'teams_assignment'

class TeamSubmission(models.Model):
    # Use string reference to avoid circular import with teams app
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='team_submissions/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    grade = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    @property
    def is_late(self) -> bool:
        """Checks if the submission was made after the assignment deadline."""
        if self.assignment and self.submitted_at and self.assignment.deadline:
            return self.submitted_at > self.assignment.deadline
        return False

    def __str__(self):
        return f"{self.title} (Team Submission)"

    class Meta:
        db_table = 'teams_teamsubmission'

class SubmissionFile(models.Model):
    submission = models.ForeignKey(TeamSubmission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='team_submissions/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.submission.title}"

    class Meta:
        db_table = 'teams_submissionfile'
