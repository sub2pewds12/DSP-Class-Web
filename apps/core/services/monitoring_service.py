import os
import threading
import time
import requests
import logging
from datetime import datetime
from django.conf import settings
from apps.core.services.telemetry_service import TelemetryService
from apps.core.services.statuspage_service import StatuspageService
from apps.core.services.infrastructure import InfrastructureService

logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Ships internal telemetry to Grafana Cloud in the background.
    Acts as a 'mini-agent' inside the Django application.
    """
    
    _thread = None
    _stop_event = threading.Event()

    # Credentials (Initialized from environment)
    user_id = os.getenv('GRAFANA_CLOUD_USER_ID')
    remote_write_url = os.getenv('GRAFANA_CLOUD_REMOTE_WRITE_URL')
    metrics_token = os.getenv('GRAFANA_CLOUD_METRICS_TOKEN')

    @classmethod
    def start_heartbeat(cls):
        """Starts the background monitoring thread if not already running."""
        if cls._thread is not None and cls._thread.is_alive():
            return
            
        cls._stop_event.clear()
        cls._thread = threading.Thread(target=cls._heartbeat_loop, daemon=True)
        cls._thread.start()
        logger.info("Grafana Cloud Heartbeat Service started.")

    @classmethod
    def stop_heartbeat(cls):
        """Stops the background monitoring thread."""
        cls._stop_event.set()

    @classmethod
    def _heartbeat_loop(cls):
        """Main loop that collects and ships metrics every 60 seconds."""
        # Give the app a few seconds to warm up
        time.sleep(10)
        
        while not cls._stop_event.is_set():
            try:
                print(f"\n[Heartbeat] Pulse triggered at {datetime.now().strftime('%H:%M:%S')}")
                cls.ship_metrics()
                # Automated Health Check, Metrics Shipping, and Statuspage Sync
                InfrastructureService.perform_health_check()
            except Exception as e:
                # Robust logging to prevent charmap encoding errors on Windows
                error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                logger.error(f"Grafana Cloud Ship Failed: {error_msg}")
            
            # Sleep for 60 seconds (or until stopped)
            cls._stop_event.wait(60)

    @classmethod
    def ship_to_grafana(cls):
        """Alias for backward compatibility."""
        return cls.ship_metrics()

    @classmethod
    def ship_metrics(cls):
        """
        Collects current telemetry and sends it to Grafana Cloud.
        Uses the InfluxDB compatibility endpoint for lightweight pushing.
        """
        if not all([cls.user_id, cls.remote_write_url, cls.metrics_token]):
            print("⚠️ MonitoringService: Missing credentials in .env. Skipping...")
            return

        # 1. Get live metrics from our existing TelemetryService
        metrics = TelemetryService.get_live_metrics()

        print(f"📡 MonitoringService: Shipping pulse...")
        print(f"   📊 Requests: {metrics.get('requests_total', 0)} | Latency: {metrics.get('avg_latency', 0)}ms")
        
        # 2. Format as 'Line Protocol' (InfluxDB style - accepted by Grafana Cloud)
        # Structure: measurement,tags fields (No explicit timestamp - let Cloud assign 'now')
        lines = [
            f"dsp_v3_requests,env=dev value={metrics.get('requests_total', 0)}",
            f"dsp_v3_latency,env=dev value={metrics.get('avg_latency', 0)}",
            f"dsp_v3_db_ops,env=dev value={metrics.get('db_queries_total', 0)}",
            f"dsp_v3_heartbeat,env=dev value=1"
        ]
        
        # Add status code breakdown
        for status, count in metrics.get('responses_by_status', {}).items():
            lines.append(f"dsp_v3_responses,env=dev,status={status} count={count}")

        payload = "\n".join(lines)

        # 3. Ship to Cloud
        try:
            response = requests.post(
                cls.remote_write_url,
                data=payload,
                auth=(cls.user_id, cls.metrics_token),
                timeout=10
            )

            if response.status_code >= 200 and response.status_code < 300:
                print(f"✅ MonitoringService: Heartbeat shipped successfully! ({len(lines)} metrics)")
            else:
                print(f"❌ MonitoringService: Failed to ship metrics. Status: {response.status_code}, Body: {response.text}")

        except Exception as e:
            print(f"🚨 MonitoringService Error: {str(e)}")
