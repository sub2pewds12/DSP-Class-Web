import traceback
from django.core.mail import send_mail
from django.conf import settings
from .models import SystemError

class ErrorMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        try:
            # 1. Capture details
            msg = str(exception)
            stack = traceback.format_exc()
            path = request.path
            user = request.user if request.user.is_authenticated else None
            
            # 2. Log to Database
            error_log = SystemError.objects.create(
                message=msg,
                stack_trace=stack,
                url=path,
                user=user
            )

            # 3. Send Email Alert
            subject = f"CRITICAL: Fatal Error at {path}"
            body = f"""A fatal system error has occurred.

Error: {msg}
URL: {path}
User: {user.username if user else 'Anonymous'}
Timestamp: {error_log.timestamp}

--- Stack Trace ---
{stack}

Log ID: {error_log.id}
Resolve here: http://localhost:8000/dev/dashboard/ (Local)
"""
            recipient = getattr(settings, 'EMAIL_HOST_USER', 'sub2pewds10102005@gmail.com')
            
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
