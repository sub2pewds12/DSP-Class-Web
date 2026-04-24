import traceback
import threading
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
            msg = str(exception)
            stack = traceback.format_exc()
            path = request.path
            user = request.user if request.user.is_authenticated else None
            
            # 3. Log to Database (always log, even if throttled)
            error_log = SystemError.objects.create(
                message=msg,
                stack_trace=stack,
                url=path,
                user=user
            )

            # 4. Smart Notification Check
            # We use a 10-minute cooldown for the exact same error message
            if NotificationService.should_throttle('critical_error', msg, cooldown_minutes=10):
                return None # Silence! 

            # 5. Send Email Alert
            subject = f"CRITICAL: Fatal Error at {path}"
            body = f"""A fatal system error has occurred.

Error: {msg}
URL: {path}
User: {user.username if user else 'Anonymous'}
Timestamp: {error_log.timestamp}

--- Stack Trace ---
{stack}

Log ID: {error_log.id}
Resolve here: {request.build_absolute_uri('/dev-dashboard/')}
"""
            recipient = getattr(settings, 'EMAIL_HOST_USER', 'sub2pewds10102005@gmail.com')
            
            from django.core.mail import send_mail
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=True,
            )
            
        except Exception as e:
            # Prevent the logger itself from crashing the app
            print(f"Failed to log/email system error: {e}")
        
        return None # Let Django's default error handling take over

class ActivityTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update the system activity timestamp in cache
        from django.core.cache import cache
        from django.utils import timezone
        from .utils.monitoring import start_ghost_heartbeat
        
        # We track any request as 'activity' to keep the monitoring alive during use
        cache.set('last_system_activity', timezone.now(), 86400)
        
        # Ensure the 'Ghost Heartbeat' thread is running (Free tier background worker)
        # This is non-blocking and self-shuts-down after 30 mins of idle time.
        try:
            start_ghost_heartbeat()
        except:
            pass # Never let monitoring fail the main request
        
        return self.get_response(request)

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
