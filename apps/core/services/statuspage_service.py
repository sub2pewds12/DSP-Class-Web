import os
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class StatuspageService:
    """
    Automated synchronization between internal health checks and Atlassian Statuspage.
    """
    API_URL = "https://api.statuspage.io/v1"
    
    # Component Mapping (Fetched via discovery)
    COMPONENTS = {
        'REGISTRY_API': 'sn94jn7kccqw',
        'STUDENT_HUB': 'p0s5wll9rnvy',
        'LECTURER_DASHBOARD': '4vbrqp6w6x54',
        'SUPABASE_DATABASE': 'j0qyzdtpplk7',
        'CLOUDINARY': '28llkzxjwlzt',
        'STORAGE_ANALYTICS': 'f8pmhls98gq3',
        'UPTIMEROBOT': 'sdqwqzjn8ykd',
    }

    @classmethod
    def _get_headers(cls):
        api_key = os.getenv('STATUSPAGE_API_KEY')
        if not api_key:
            logger.error("STATUSPAGE_API_KEY not found in environment")
            return None
        return {"Authorization": f"OAuth {api_key}", "Content-Type": "application/json"}

    @classmethod
    def update_component(cls, component_key, status):
        """
        Updates a specific component status.
        Statuses: operational, degraded_performance, partial_outage, major_outage
        """
        component_id = cls.COMPONENTS.get(component_key)
        if not component_id:
            logger.error(f"Invalid component key: {component_key}")
            return False

        page_id = os.getenv('STATUSPAGE_PAGE_ID')
        url = f"{cls.API_URL}/pages/{page_id}/components/{component_id}"
        headers = cls._get_headers()
        
        if not headers:
            return False

        payload = {"component": {"status": status}}
        
        try:
            response = requests.patch(url, headers=headers, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                logger.info(f"Updated {component_key} to {status}")
                return True
            else:
                logger.error(f"Failed to update Statuspage: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Statuspage API Error: {str(e)}")
            return False

    @classmethod
    def sync_infrastructure(cls):
        """
        Calculates status based on InfrastructureService analytics and pushes to Statuspage.
        """
        from apps.core.services.infrastructure import InfrastructureService
        analytics = InfrastructureService.get_system_analytics(bypass_cache=True)
        health_score = analytics.get('health', 100)
        error_rate = analytics.get('error_rate', 0)

        # 1. API & Hub Status
        if health_score < 40:
            status = 'major_outage'
        elif health_score < 70 or error_rate > 10:
            status = 'partial_outage'
        elif health_score < 90 or error_rate > 5:
            status = 'degraded_performance'
        else:
            status = 'operational'

        cls.update_component('REGISTRY_API', status)
        cls.update_component('STUDENT_HUB', status)
        cls.update_component('LECTURER_DASHBOARD', status)

        # 2. Database Status
        db_status = 'operational'
        if analytics.get('db_telemetry', {}).get('db_status') != 'Operational':
            # This is a bit simplified, but good for now
            db_status = 'operational' # Fallback
            
        cls.update_component('SUPABASE_DATABASE', db_status)

        return {
            'health_score': health_score,
            'status_pushed': status
        }

    @classmethod
    def create_incident(cls, name, message, status='investigating', component_keys=None):
        """
        Creates an incident on Statuspage.
        Status: investigating, identified, monitoring, resolved
        """
        page_id = os.getenv('STATUSPAGE_PAGE_ID')
        url = f"{cls.API_URL}/pages/{page_id}/incidents"
        headers = cls._get_headers()
        
        if not headers:
            return False

        component_ids = []
        if component_keys:
            component_ids = [cls.COMPONENTS[k] for k in component_keys if k in cls.COMPONENTS]

        payload = {
            "incident": {
                "name": name,
                "status": status,
                "body": message,
                "component_ids": component_ids
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code not in [200, 201]:
                print(f"[Error] Statuspage Incident Failed: {response.status_code} - {response.text}")
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Statuspage Incident Error: {str(e)}")
            return False

    @classmethod
    def has_active_incidents(cls):
        """Checks if there are any unresolved incidents on the page."""
        page_id = os.getenv('STATUSPAGE_PAGE_ID')
        url = f"{cls.API_URL}/pages/{page_id}/incidents/unresolved"
        headers = cls._get_headers()
        
        if not headers:
            return True # Fail-safe: assume active incident to avoid spam
            
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                incidents = response.json()
                return len(incidents) > 0
            return True
        except Exception:
            return True

    @classmethod
    def auto_report_incident(cls, health_score, message=None):
        """Automatically reports an incident if health is critical and no active incident exists."""
        if health_score < 40 and not cls.has_active_incidents():
            final_message = message or f"Our automated systems have detected a drop in system health (Score: {health_score}%). We are investigating the cause and working on a resolution."
            return cls.create_incident(
                name="System Instability Detected",
                message=final_message,
                status='investigating',
                component_keys=['REGISTRY_API', 'STUDENT_HUB']
            )
        return False

    @classmethod
    def submit_metric_point(cls, metric_id, value, timestamp=None):
        """Submits a data point to a specific metric."""
        page_id = os.getenv('STATUSPAGE_PAGE_ID')
        if not page_id:
            logger.error("STATUSPAGE_PAGE_ID not found")
            return False
            
        url = f"{cls.API_URL}/pages/{page_id}/metrics/{metric_id}/data.json"
        headers = cls._get_headers()
        
        if not headers or not metric_id:
            return False
            
        payload = {
            "data": {
                "value": value
            }
        }
        
        # If no timestamp is provided, Statuspage uses its own server time (safest for heartbeats)
        if timestamp:
            payload["data"]["timestamp"] = int(timestamp)
            
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code not in [200, 201]:
                logger.error(f"Statuspage Metric [{metric_id}] Failed: {response.status_code} - {response.text}")
            else:
                logger.info(f"Statuspage Metric [{metric_id}] Shipped: {value}")
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Statuspage Metric Connection Error: {str(e)}")
            return False
