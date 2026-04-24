import os
import subprocess
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connection

class BackupService:
    """
    Automated Backup Engine for PostgreSQL/Supabase.
    Handles snapshots, retention, and restoration.
    """
    
    BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')
    PSQL_PATH = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
    PG_DUMP_PATH = r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"

    @classmethod
    def ensure_backup_dir(cls):
        if not os.path.exists(cls.BACKUP_DIR):
            os.makedirs(cls.BACKUP_DIR)

    @classmethod
    def get_db_url(cls):
        # Extract URL from settings or env
        # Django stores it in settings.DATABASES['default']
        db_config = settings.DATABASES.get('default', {})
        user = db_config.get('USER')
        password = db_config.get('PASSWORD')
        host = db_config.get('HOST')
        port = db_config.get('PORT')
        name = db_config.get('NAME')
        
        if not all([user, password, host, port, name]):
            # Fallback to env if settings are parsed differently
            return os.getenv('DATABASE_URL')
            
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    @classmethod
    def take_snapshot(cls, label="auto"):
        """Takes a full database dump using pg_dump."""
        cls.ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{label}_{timestamp}.sql"
        filepath = os.path.join(cls.BACKUP_DIR, filename)
        
        db_url = cls.get_db_url()
        
        try:
            # Add sslmode=require for Supabase if not in URL
            if 'supabase' in db_url and 'sslmode' not in db_url:
                db_url += "?sslmode=require"
                
            cmd = [cls.PG_DUMP_PATH, "--dbname", db_url, "--file", filepath, "--no-owner", "--no-privileges"]
            
            # Use subprocess to run the dump
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # After successful backup, run cleanup
                cls.cleanup_old_backups()
                return {
                    "status": "success",
                    "file": filename,
                    "path": filepath,
                    "size": os.path.getsize(filepath)
                }
            else:
                return {"status": "error", "message": result.stderr}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @classmethod
    def cleanup_old_backups(cls, quota=10, max_age_days=7):
        """Implements Smart Retention Policy."""
        cls.ensure_backup_dir()
        backups = []
        
        for f in os.listdir(cls.BACKUP_DIR):
            if not f.endswith('.sql'):
                continue
            
            # Skip protected files
            if ".locked" in f or "rescue" in f.lower():
                continue
                
            path = os.path.join(cls.BACKUP_DIR, f)
            mtime = os.path.getmtime(path)
            backups.append({"name": f, "path": path, "mtime": mtime})
            
        # Sort by mtime (oldest first)
        backups.sort(key=lambda x: x['mtime'])
        
        # 1. Age-based cleanup
        cutoff = time.time() - (max_age_days * 86400)
        remaining = []
        for b in backups:
            if b['mtime'] < cutoff:
                try:
                    os.remove(b['path'])
                except:
                    pass
            else:
                remaining.append(b)
                
        # 2. Quota-based cleanup (keep only latest 'quota' files)
        if len(remaining) > quota:
            to_delete = remaining[:-quota]
            for b in to_delete:
                try:
                    os.remove(b['path'])
                except:
                    pass

    @classmethod
    def list_backups(cls):
        """Lists all available backups with metadata."""
        cls.ensure_backup_dir()
        backups = []
        for f in os.listdir(cls.BACKUP_DIR):
            if not f.endswith('.sql'):
                continue
            path = os.path.join(cls.BACKUP_DIR, f)
            stats = os.stat(path)
            backups.append({
                "name": f,
                "size_mb": round(stats.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "is_protected": ".locked" in f or "rescue" in f.lower()
            })
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)

    @classmethod
    def restore_snapshot(cls, filename):
        """Automates the psql restore process."""
        filepath = os.path.join(cls.BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            return {"status": "error", "message": "File not found."}
            
        db_url = cls.get_db_url()
        
        try:
            # 1. Clear Schema first
            drop_cmd = [cls.PSQL_PATH, db_url, "-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"]
            subprocess.run(drop_cmd, capture_output=True)
            
            # 2. Restore
            restore_cmd = [cls.PSQL_PATH, db_url, "-f", filepath]
            result = subprocess.run(restore_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"status": "success", "message": "Database restored successfully."}
            else:
                return {"status": "error", "message": result.stderr}
        except Exception as e:
            return {"status": "error", "message": str(e)}
