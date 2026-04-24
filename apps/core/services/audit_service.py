from apps.core.models import AuditLog
from apps.core.middleware import get_current_request

class AuditService:
    @staticmethod
    def log_event(action, target_type, target_id="", description="", metadata=None, actor=None):
        """
        Creates an audit log entry.
        
        Args:
            action (str): The action performed (e.g., 'GRADE_CHANGE').
            target_type (str): The type of object affected (e.g., 'Assignment').
            target_id (str): The ID of the affected object.
            description (str): Human-readable summary of the action.
            metadata (dict): Optional extra data (e.g., {'old': 5, 'new': 10}).
            actor (User): Optional user who performed the action. If None, it tries to get from request.
        """
        request = get_current_request()
        
        # Determine actor
        if not actor and request and request.user.is_authenticated:
            actor = request.user
            
        # Capture technical context
        ip = ""
        ua = ""
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            ua = request.META.get('HTTP_USER_AGENT', '')

        # Create the log
        return AuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            description=description,
            metadata=metadata or {},
            ip_address=ip,
            user_agent=ua
        )
