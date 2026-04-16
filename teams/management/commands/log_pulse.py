import time
from django.core.management.base import BaseCommand
from django.db import connection, OperationalError
from django.utils import timezone
from teams.models import SystemPulse
from teams.utils.email_service import send_html_email

class Command(BaseCommand):
    help = 'Logs a system pulse with DB latency and alerts on failure'

    def handle(self, *args, **options):
        start_time = time.time()
        try:
            # Measure DB Latency by performing a simple query
            connection.ensure_connection()
            status = 'OPERATIONAL'
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            latency = (time.time() - start_time) * 1000 # Convert to ms
            
            # Simple latency boundaries
            if latency > 1000:
                status = 'WARNING'
            if latency > 5000:
                status = 'CRITICAL'

            SystemPulse.objects.create(
                status=status,
                latency=latency
            )
            
            if status == 'CRITICAL':
                self.send_emergency_alert(f"EXTREME LATENCY: {latency:.2f}ms", "System is responding but extremely slow.")
                
            self.stdout.write(self.style.SUCCESS(f'Pulse logged: {status} ({latency:.2f}ms)'))
            
        except (OperationalError, Exception) as e:
            latency = (time.time() - start_time) * 1000
            SystemPulse.objects.create(
                status='DOWN',
                latency=latency,
                info=str(e)
            )
            self.send_emergency_alert("DATABASE CONNECTION FAILED", str(e))
            self.stdout.write(self.style.ERROR(f'Pulse logged: DOWN ({latency:.2f}ms)'))

    def send_emergency_alert(self, title, message):
        send_html_email(
            subject=f"EMERGENCY: {title}",
            template_name='teams/emails/system_alert.html',
            context={
                'alert_title': title,
                'error_message': message,
                'timestamp': timezone.now(),
                'module': 'Infrastructure Monitor (Pulse)',
                'dashboard_url': 'http://localhost:8000/dev-dashboard/'
            },
            recipient_list=['sub2pewds10102005@gmail.com']
        )
