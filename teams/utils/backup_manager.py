import os
import shutil
from datetime import datetime, timedelta
from django.conf import settings

class BackupManager:
    @staticmethod
    def create_backup():
        """Creates a copy of the current sqlite database."""
        db_path = settings.DATABASES['default']['NAME']
        if not os.path.exists(db_path):
            return None
        
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')
        
        shutil.copy2(db_path, backup_path)
        return backup_path

    @staticmethod
    def rotate_backups(days=90):
        """Removes backups older than the specified number of days."""
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            return
            
        cutoff = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('db_backup_') and filename.endswith('.sqlite3'):
                file_path = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff:
                    os.remove(file_path)
