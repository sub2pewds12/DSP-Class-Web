from django.core.cache import cache
import hashlib

class NotificationService:
    """
    Centralized logic for smart notifications, throttling, and alert batching.
    """

    @staticmethod
    def should_throttle(key_prefix, message, cooldown_minutes=10):
        """
        Determines if a notification should be throttled based on its content.
        Returns True if the notification should be BLOCKED (already sent recently).
        """
        # Create a unique hash of the message to identify duplicates
        msg_hash = hashlib.md5(message.encode('utf-8')).hexdigest()
        cache_key = f"notify_throttle_{key_prefix}_{msg_hash}"
        
        if cache.get(cache_key):
            return True # Throttle it!
        
        # Set the throttle for the specified cooldown period
        cache.set(cache_key, True, cooldown_minutes * 60)
        return False # Safe to send
