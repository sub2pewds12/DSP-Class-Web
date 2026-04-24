from django.db import models
from django.conf import settings

class SystemSettings(models.Model):
    max_team_size = models.IntegerField(default=4)

    def save(self, *args, **kwargs):
        if not self.pk and SystemSettings.objects.exists():
            return None # Prevent multiple instances via save
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Returns the singleton settings instance, creating it if necessary."""
        settings, created = cls.objects.get_or_create(id=1)
        return settings

    def __str__(self):
        return f"System Settings (ID: {self.id})"

    class Meta:
        db_table = 'teams_systemsettings'
        verbose_name_plural = "System Settings"


class SystemError(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)
    stack_trace = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        db_table = 'teams_systemerror'

class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)  # e.g., 'GRADE_CHANGE', 'USER_APPROVAL'
    target_type = models.CharField(max_length=100) # e.g., 'Assignment', 'User'
    target_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        db_table = 'teams_auditlog'
