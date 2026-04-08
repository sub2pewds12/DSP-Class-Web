from django.db import models
from django.core.exceptions import ValidationError

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
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name='members')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
