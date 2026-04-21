from .base import *
import dj_database_url

DEBUG = True

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR}/db.sqlite3",
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
