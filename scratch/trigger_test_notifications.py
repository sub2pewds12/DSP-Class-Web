import os
import sys
sys.path.append(os.getcwd())
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.core.services import InfrastructureService
from apps.core.utils.email_service import send_html_email
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def trigger_tests():
    print("Starting Test Notification Storm...")

    # 1. Test System Error Alert
    print("Sending System Error Alert...")
    from apps.core.models import SystemError
    mock_error = SystemError.objects.create(
        message="Test Exception: Database connection latency high (MOCKED)",
        stack_trace="Traceback (mock):\n  File 'infrastructure.py', line 42\n    raise ConnectionError('Latency too high')",
        url="/dev-dashboard/",
        user=User.objects.filter(is_superuser=True).first()
    )
    InfrastructureService.send_system_error_alert(mock_error)

    # 2. Test User Registration Alert
    print("Sending User Registration Alert...")
    mock_user = User.objects.filter(role='STUDENT').first()
    if mock_user:
        send_html_email(
            subject=f"Access Request: STUDENT - {mock_user.get_full_name()}",
            template_name='teams/emails/admin_request.html',
            context={
                'user_name': mock_user.get_full_name(),
                'user_email': mock_user.email,
                'requested_role': 'STUDENT',
                'dashboard_url': 'http://localhost:8000/dev-dashboard/'
            },
            recipient_list=[settings.EMAIL_REDIRECT_RECIPIENT]
        )
    else:
        print("No mock user found for registration test.")

    # 3. Test Approval (User Set)
    print("Sending User Approval Notification...")
    send_html_email(
        subject="Welcome to DSP Class Web",
        template_name='teams/emails/user_approved.html',
        context={
            'user_name': "Alexander Student",
            'role_name': "TEAM LEAD",
            'login_url': 'http://localhost:8000/login/'
        },
        recipient_list=['alexander@example.com']
    )

    # 4. Test Denial (User Set)
    print("Sending User Denial Notification...")
    send_html_email(
        subject="Application Update: DSP Class Hub",
        template_name='teams/emails/user_denied.html',
        context={
            'user_name': "Jordan Applicant",
            'role_name': "STUDENT"
        },
        recipient_list=['jordan@example.com']
    )

    print("\n✅ All test triggers fired! Check your inbox at sub2pewds10102005@gmail.com")

if __name__ == "__main__":
    trigger_tests()
