import os
from supabase import create_client, Client
from django.conf import settings

class SupabaseService:
    """
    Centralized service for interacting with the Supabase platform.
    Uses the modern Publishable Key security model.
    """
    
    _client: Client = None

    @classmethod
    def get_client(cls) -> Client:
        """
        Initializes and returns a singleton instance of the Supabase Client.
        """
        if cls._client is None:
            url = os.environ.get('SUPABASE_URL')
            key = os.environ.get('SUPABASE_KEY')
            
            if not url or not key:
                raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in environment.")
            
            cls._client = create_client(url, key)
        
        return cls._client

    @classmethod
    def check_connection(cls):
        """
        Performs a 'Heartbeat' check by listing project storage buckets.
        This verifies that the Publishable Key and URL are valid.
        """
        try:
            client = cls.get_client()
            # Simple list call to verify connectivity and authentication
            client.storage.list_buckets()
            return {
                "status": "CONNECTED",
                "message": "Supabase API Handshake Successful",
                "severity": "success"
            }
        except Exception as e:
            return {
                "status": "DISCONNECTED",
                "message": f"API Handshake Failed: {str(e)}",
                "severity": "danger"
            }
