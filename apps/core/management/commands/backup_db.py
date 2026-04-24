from django.core.management.base import BaseCommand
from apps.core.services.backup_service import BackupService
import sys

class Command(BaseCommand):
    help = 'Managed Database Backup Engine (Snapshots, Retention, Restoration)'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='List all available backups')
        parser.add_argument('--restore', type=str, help='Restore a specific backup file')
        parser.add_argument('--cleanup', action='store_true', help='Force run the retention cleanup policy')
        parser.add_argument('--label', type=str, default='manual', help='Label for the backup (default: manual)')

    def handle(self, *args, **options):
        if options['list']:
            backups = BackupService.list_backups()
            self.stdout.write(self.style.SUCCESS(f"\n{'Name':<40} | {'Size':<10} | {'Created At':<25} | {'Protected'}"))
            self.stdout.write("-" * 90)
            for b in backups:
                prot = " [LOCKED]" if b['is_protected'] else ""
                self.stdout.write(f"{b['name']:<40} | {b['size_mb']:>7.2f} MB | {b['created_at']:<25} | {prot}")
            return

        if options['restore']:
            filename = options['restore']
            confirm = input(f"WARNING: This will WIPE the current database and restore from '{filename}'. Continue? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING("Restoration cancelled."))
                return
                
            self.stdout.write(f"Restoring {filename}...")
            result = BackupService.restore_snapshot(filename)
            if result['status'] == 'success':
                self.stdout.write(self.style.SUCCESS("Restoration complete!"))
            else:
                self.stdout.write(self.style.ERROR(f"Restoration failed: {result.get('message')}"))
            return

        if options['cleanup']:
            self.stdout.write("Running retention policy cleanup...")
            BackupService.cleanup_old_backups()
            self.stdout.write(self.style.SUCCESS("Cleanup complete."))
            return

        # Default action: Take Backup
        self.stdout.write("Initializing manual database snapshot...")
        result = BackupService.take_snapshot(label=options['label'])
        
        if result['status'] == 'success':
            self.stdout.write(self.style.SUCCESS(f"Snapshot created: {result['file']}"))
            self.stdout.write(f"Path: {result['path']}")
            self.stdout.write(f"Size: {result['size'] / 1024:.1f} KB")
        else:
            self.stdout.write(self.style.ERROR(f"Snapshot failed: {result.get('message')}"))
            sys.exit(1)
