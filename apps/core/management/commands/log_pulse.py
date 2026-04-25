from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.services.infrastructure import InfrastructureService
from apps.core.services.statuspage_service import StatuspageService
import os
import time
from apps.core.utils.email_service import send_html_email

class Command(BaseCommand):
    help = 'Logs a system pulse and ships real data to Statuspage. Supports continuous daemon mode.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true', help='Run as a continuous daemon')
        parser.add_argument('--interval', type=int, default=60, help='Interval between pulses in seconds (default: 60)')

    def handle(self, *args, **options):
        is_loop = options.get('loop')
        interval = options.get('interval')
        
        if is_loop:
            self.stdout.write(self.style.SUCCESS(f'Pulse Monitor started in Daemon mode (Interval: {interval}s)'))
            while True:
                self.perform_pulse()
                time.sleep(interval)
        else:
            self.perform_pulse()

    def perform_pulse(self):
        latencies = InfrastructureService.measure_latencies()
        db_latency = latencies.get('db_latency')
        media_latency = latencies.get('media_latency')
        
        if db_latency:
            db_metric_id = os.getenv('STATUSPAGE_METRIC_DB_LATENCY')
            StatuspageService.submit_metric_point(db_metric_id, db_latency)
            self.stdout.write(self.style.SUCCESS(f'DB Pulse shipped: {db_latency:.2f}ms'))
        
        if media_latency:
            media_metric_id = os.getenv('STATUSPAGE_METRIC_MEDIA_LATENCY')
            StatuspageService.submit_metric_point(media_metric_id, media_latency)
            self.stdout.write(self.style.SUCCESS(f'Media Pulse shipped: {media_latency:.2f}ms'))
        
        if not db_latency and not media_latency:
            self.stdout.write(self.style.ERROR('Pulse failed: Could not measure any latencies'))

    def send_emergency_alert(self, title, message):
        send_html_email(
            subject=f"EMERGENCY: {title}",
            template_name='core/emails/system_alert.html',
            context={
                'alert_title': title,
                'error_message': message,
                'timestamp': timezone.now(),
                'module': 'Infrastructure Monitor (Pulse)',
                'dashboard_url': 'http://localhost:8000/dev-dashboard/'
            },
            recipient_list=['sub2pewds10102005@gmail.com']
        )
