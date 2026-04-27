from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('LECTURER', 'Lecturer/Teacher'),
        ('DEV', 'Developer/Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    email = models.EmailField(unique=True)
    is_approved = models.BooleanField(default=True)

    # Granular Permissions
    can_grade = models.BooleanField(default=False)
    can_manage_assignments = models.BooleanField(default=False)
    can_manage_teams = models.BooleanField(default=False)
    can_manage_system = models.BooleanField(default=False)

    # Profile Fields (v2)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/users/', null=True, blank=True)
    email_notifications = models.BooleanField(default=True)

    
    class Meta:
        db_table = 'teams_customuser'

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def save(self, *args, **kwargs):
        if self.is_approved:
            if self.role == 'DEV':
                self.is_staff = True
                self.is_superuser = True
                # Devs get all permissions
                self.can_grade = True
                self.can_manage_assignments = True
                self.can_manage_teams = True
                self.can_manage_system = True
            elif self.role == 'LECTURER':
                self.is_staff = True
                self.is_superuser = False
                # Lecturers get teaching/management permissions
                self.can_grade = True
                self.can_manage_assignments = True
                self.can_manage_teams = True
                self.can_manage_system = False
            else:
                self.is_staff = False
                self.is_superuser = False
                # Students get no admin permissions by default
                self.can_grade = False
                self.can_manage_assignments = False
                self.can_manage_teams = False
                self.can_manage_system = False
        else:
            self.is_staff = False
            self.is_superuser = False
            self.can_grade = False
            self.can_manage_assignments = False
            self.can_manage_teams = False
            self.can_manage_system = False

        super().save(*args, **kwargs)

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    team = models.ForeignKey('teams.Team', null=True, blank=True, on_delete=models.SET_NULL, related_name='members')
    role = models.CharField(max_length=255, blank=True, default="Member")
    role_description = models.TextField(blank=True, help_text="Detailed description of your role responsibilities.")
    student_id = models.CharField(max_length=20, blank=True, unique=True, null=True)
    academic_year = models.CharField(max_length=10, blank=True, null=True, verbose_name="Batch")
    github_username = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    website_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'teams_student'

    def __str__(self):
        return f"Student: {self.user.get_full_name()}"

class Lecturer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lecturer_profile')
    department = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'teams_lecturer'

    def __str__(self):
        return f"Lecturer: {self.user.get_full_name()}"

class Developer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='developer_profile')
    access_level = models.IntegerField(default=1)
    github_username = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'teams_developer'

    def __str__(self):
        return f"Developer: {self.user.get_full_name()}"
