import logging
from django.db.models.signals import pre_migrate
from django.dispatch import receiver
from apps.core.services.backup_service import BackupService

logger = logging.getLogger(__name__)

@receiver(pre_migrate)
def auto_backup_before_migration(sender, **kwargs):
    """
    Automatically triggers a database snapshot before any migrations are applied.
    """
    # We only want to run this once per 'migrate' command, not for every app
    # Django signals send the 'app_config' as sender
    # We'll use a simple flag to ensure it only runs once in the current process
    if not getattr(auto_backup_before_migration, '_already_run', False):
        print("\n[BACKUP] Initializing automatic pre-migration snapshot...")
        result = BackupService.take_snapshot(label="pre_migrate")
        
        if result['status'] == 'success':
            print(f"[BACKUP] Snapshot created: {result['file']} ({result['size'] / 1024:.1f} KB)")
        else:
            print(f"[BACKUP] WARNING: Automatic snapshot failed! {result.get('message')}")
            
        auto_backup_before_migration._already_run = True
