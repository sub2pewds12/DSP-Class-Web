from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    label = 'core'
    verbose_name = 'System Infrastructure'

    def ready(self):
        import apps.core.signals
        
        # Start the Grafana Cloud Heartbeat (only in the main process)
        import os
        if os.environ.get('RUN_MAIN') == 'true' or os.getenv('KUBERNETES_SERVICE_HOST'):
            from apps.core.services.monitoring_service import MonitoringService
            MonitoringService.start_heartbeat()
