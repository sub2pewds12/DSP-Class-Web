from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import SystemSettings, SystemPulse, SystemError

# Proxy imports for backward compatibility during Phase 1
from apps.users.models import CustomUser, Student, Lecturer, Developer
from apps.academia.models import ClassDocument, Assignment, TeamSubmission, SubmissionFile

class Team(models.Model):
    name = models.CharField(max_length=255, unique=True)
    project_name = models.CharField(max_length=255, blank=True)
    project_description = models.TextField(blank=True)
    leader = models.ForeignKey('users.Student', null=True, blank=True, on_delete=models.SET_NULL, related_name='led_teams')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.pk:
            settings = SystemSettings.get_settings()
            max_size = settings.max_team_size
            if self.members.count() > max_size:
                raise ValidationError(f"Team cannot have more than {max_size} members.")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'teams_team'
