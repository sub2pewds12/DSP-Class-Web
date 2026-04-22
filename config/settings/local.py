from .base import *
import dj_database_url
import os
from dotenv import load_dotenv

# Load secret box (.env)
load_dotenv(os.path.join(BASE_DIR, '.env'))

# We surgically strip 'pgbouncer' flags to prevent driver parsing errors on Render
raw_db_url = os.environ.get('DATABASE_URL')
if raw_db_url and 'pgbouncer' in raw_db_url:
    raw_db_url = raw_db_url.split('?')[0]

DEBUG = True

DATABASES = {
    'default': dj_database_url.config(
        default=raw_db_url or f"sqlite:///{BASE_DIR}/db.sqlite3",
        conn_max_age=600,
        ssl_require=False
    )
}

# Optimize SQLite for local development concurrency
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default']['OPTIONS'] = {
        'timeout': 20,
    }

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files (no Cloudinary for local dev usually, keep it simple)
# But we can override DEFAULT_FILE_STORAGE here if we want to test S3/Cloudinary locally.
# For now, stick to standard local storage.
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
