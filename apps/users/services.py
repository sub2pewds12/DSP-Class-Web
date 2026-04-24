from django.db import transaction
from django.contrib.auth import login
from apps.users.models import CustomUser, Student, Lecturer, Developer
from apps.core.utils.email_service import send_html_email
from apps.core.services.audit_service import AuditService

class UserService:
    """
    Handles user lifecycle, registration, and administrative approvals.
    """

    @staticmethod
    def register_user(form_data, request=None):
        """
        Creates a new user with the appropriate profile and approval state.
        
        Args:
            form_data: Cleaned data from UserRegistrationForm.
            request: Optional HttpRequest for login/notifications.
        """
        email = form_data.get('email')
        role = form_data.get('role', 'STUDENT')
        password = form_data.get('password')
        
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=form_data.get('first_name', ''),
                last_name=form_data.get('last_name', ''),
                role=role
            )
            
            # 1. Student Logic: Auto-approvals
            if role == 'STUDENT':
                user.is_approved = True
                user.save()
                Student.objects.create(user=user)
                
                # Send automatic welcome email
                send_html_email(
                    subject="Welcome to DSP Class Hub",
                    template_name='teams/emails/user_approved.html',
                    context={
                        'user_name': user.first_name,
                        'role_name': 'STUDENT',
                        'login_url': request.build_absolute_uri('/login/') if request else '/login/'
                    },
                    recipient_list=[user.email]
                )

                AuditService.log_event(
                    action="AUTO_APPROVAL",
                    target_type="User",
                    target_id=str(user.id),
                    description=f"Student '{user.get_full_name()}' auto-approved upon registration.",
                    metadata={"email": user.email}
                )

                if request:
                    login(request, user, backend='apps.users.backends.CaseInsensitiveModelBackend')
                return user, True # (user, is_auto_approved)
            
            # 2. Staff/Dev Logic: Requires manual approval
            user.is_approved = False
            user.save()
            
            if role == 'DEV':
                Developer.objects.create(user=user)
            else:
                Lecturer.objects.create(user=user)
                
            # 3. Notification Logic (ONLY for non-students)
            UserService._notify_admin_of_request(user, role, request)
            
            return user, False

    @staticmethod
    def approve_user(user_id, request=None):
        """Approves a pending user and sends confirmation email."""
        user = CustomUser.objects.get(id=user_id)
        user.is_approved = True
        user.save()
        
        send_html_email(
            subject="Your Account has been Approved!",
            template_name='teams/emails/user_approved.html',
            context={
                'user_name': user.first_name,
                'role_name': user.role,
                'login_url': request.build_absolute_uri('/login/') if request else '/login/'
            },
            recipient_list=[user.email]
        )
        
        AuditService.log_event(
            action="USER_APPROVAL",
            target_type="User",
            target_id=str(user_id),
            description=f"{user.get_role_display()} '{user.get_full_name()}' approved by administrative action.",
            metadata={"email": user.email, "role": user.role}
        )
        return user

    @staticmethod
    def deny_user(user_id):
        """Denies and deletes a pending user registration safely."""
        from django.shortcuts import get_object_or_404
        try:
            user = CustomUser.objects.get(id=user_id)
            name = user.get_full_name()
            email = user.email
            role = user.role
            user.delete()
            
            send_html_email(
                subject="Application Status Update",
                template_name='teams/emails/user_denied.html',
                context={'user_name': name, 'role_name': role},
                recipient_list=[email]
            )

            AuditService.log_event(
                action="USER_DENIAL",
                target_type="User",
                target_id=str(user_id),
                description=f"{role} '{name}' denied and removed by administrative action.",
                metadata={"email": email}
            )
            return name
        except CustomUser.DoesNotExist:
            return "User already processed"

    @staticmethod
    def _notify_admin_of_request(user, role, request=None):
        """Triggers email notification to the administrator."""
        from apps.core.services.notification_service import NotificationService
        
        # We throttle registration alerts to once every 5 minutes to prevent floods
        # We use a broad key since these are all "Access Requests"
        if NotificationService.should_throttle('access_request', 'new_registration_alert', cooldown_minutes=5):
            return 
            
        send_html_email(
            subject=f"Access Request: {role} - {user.get_full_name()}",
            template_name='teams/emails/admin_request.html',
            context={
                'user_name': user.get_full_name(),
                'user_email': user.email,
                'requested_role': role,
                'dashboard_url': request.build_absolute_uri('/dev-dashboard/') if request else '/dev-dashboard/'
            },
            recipient_list=['sub2pewds10102005@gmail.com']
        )
