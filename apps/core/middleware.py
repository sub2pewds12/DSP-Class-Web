import traceback
import threading
import os
from django.core.mail import send_mail
from django.conf import settings
from .models import SystemError

_thread_locals = threading.local()

def get_current_request():
    """Safely retrieves the current request from thread storage."""
    return getattr(_thread_locals, 'request', None)

class ErrorMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        from django.http import Http404
        from .services.notification_service import NotificationService

        # 1. Ignore 404 errors (too much noise for email)
        if isinstance(exception, Http404):
            return None

        try:
            # 2. Capture details
            path = request.path
            user = request.user if request.user.is_authenticated else None
            
            # 3. Sentry Integration (Primary Error Tracker)
            from sentry_sdk import set_tag, set_user, capture_exception
            if user:
                set_user({"id": user.id, "email": user.email, "username": user.username})
                set_tag("user_role", user.role)
            set_tag("path", path)
            
            # Capture to Sentry
            capture_exception(exception)
            
        except Exception as e:
            # Prevent the monitor itself from crashing the app
            print(f"Failed to capture error to Sentry: {e}")
        
        return None # Let Django's default error handling take over

class ActivityTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update the system activity timestamp in cache
        from django.core.cache import cache
        from django.utils import timezone
        import time
        from .services.telemetry_service import TelemetryService
        
        # 1. Start timer
        start_time = time.time()
        
        # 2. Track activity
        cache.set('last_system_activity', timezone.now(), 86400)
        
        # 3. Get response
        response = self.get_response(request)
        
        # 4. Calculate latency and record pulse
        duration_ms = (time.time() - start_time) * 1000
        
        # We don't record the telemetry endpoint itself to avoid noise
        if not request.path.startswith('/internal/telemetry/') and not request.path.startswith('/static/'):
            TelemetryService.record_pulse(response.status_code, duration_ms)
            
        return response

class AuditContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request in thread-local storage for global access (e.g. in AuditService)
        _thread_locals.request = request
        
        response = self.get_response(request)
        
        # Cleanup to prevent memory leaks or cross-thread pollution
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
            
        return response
