from .base import *
import dj_database_url

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Production security settings (only active when DEBUG is off)
if not DEBUG:
    # 1. HSTS & SSL
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # 2. Cookie Security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'

    # 3. Header Hardening
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'

    # Trusted Origins
    CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://dsp-class-web.onrender.com').split(',')

# Database Configuration
# We surgically strip 'pgbouncer' flags to prevent driver parsing errors on Render
raw_db_url = os.environ.get('DATABASE_URL', os.environ.get('PROD_DB_URL'))
if raw_db_url and 'pgbouncer' in raw_db_url:
    raw_db_url = raw_db_url.split('?')[0]

DATABASES = {
    'default': dj_database_url.config(
        default=raw_db_url or f"sqlite:///{BASE_DIR}/db.sqlite3",
        conn_max_age=0,
        ssl_require=not DEBUG
    )
}

# Instrument with Prometheus
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default']['ENGINE'] = 'django_prometheus.db.backends.sqlite3'
elif DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    DATABASES['default']['ENGINE'] = 'django_prometheus.db.backends.postgresql'

# NUCLEAR OPTION: Explicitly remove 'pgbouncer' from OPTIONS to prevent driver crashes
if 'pgbouncer' in DATABASES['default'].get('OPTIONS', {}):
    DATABASES['default']['OPTIONS'].pop('pgbouncer', None)

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_TIMEOUT = 5
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Cloudinary Configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.RawMediaCloudinaryStorage'
