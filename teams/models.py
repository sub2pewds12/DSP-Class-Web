from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('LECTURER', 'Lecturer/Teacher'),
        ('DEV', 'Developer/Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

class SystemSettings(models.Model):
    max_team_size = models.IntegerField(default=4)

    def save(self, *args, **kwargs):
        if not self.pk and SystemSettings.objects.exists():
            return SystemSettings.objects.first()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"System Settings (Max Size: {self.max_team_size})"

    class Meta:
        verbose_name_plural = "System Settings"


class Team(models.Model):
    name = models.CharField(max_length=255, unique=True)
    project_name = models.CharField(max_length=255, blank=True)
    project_description = models.TextField(blank=True)
    leader = models.ForeignKey('Student', null=True, blank=True, on_delete=models.SET_NULL, related_name='led_teams')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.pk:
            settings = SystemSettings.objects.first()
            max_size = settings.max_team_size if settings else 4
            if self.members.count() > max_size:
                raise ValidationError(f"Team cannot have more than {max_size} members.")

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name='members')
    role = models.CharField(max_length=255, blank=True, default="Member")

    def __str__(self):
        return f"Student: {self.user.get_full_name()}"

class Lecturer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lecturer_profile')
    department = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Lecturer: {self.user.get_full_name()}"

class Developer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='developer_profile')
    access_level = models.IntegerField(default=1) # Can be used for tiered dev perms

    def __str__(self):
        return f"Developer: {self.user.get_full_name()}"

class ClassDocument(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='class_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')

    def __str__(self):
        return self.title

class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instruction_file = models.FileField(upload_to='assignment_instructions/', null=True, blank=True)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_assignments')
    grades_released = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class TeamSubmission(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='team_submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    grade = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f"{self.team.name} - {self.title}"
