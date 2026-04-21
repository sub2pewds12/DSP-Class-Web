from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.models import SystemError
from apps.core.services import InfrastructureService

@receiver(post_save, sender=SystemError)
def alert_admin_on_error(sender, instance, created, **kwargs):
    """
    Triggered when a SystemError is logged.
    Uses NotificationService to send the actual alert.
    """
    if created:
        InfrastructureService.send_system_error_alert(instance)
