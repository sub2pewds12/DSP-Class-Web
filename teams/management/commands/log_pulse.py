from django.core.management.base import BaseCommand
from django.utils import timezone
from teams.utils.monitoring import execute_pulse, prune_old_pulses
from teams.utils.email_service import send_html_email
import time

class Command(BaseCommand):
    help = 'Logs a system pulse with DB latency and alerts on failure. Supports continuous daemon mode.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true', help='Run as a continuous daemon')
        parser.add_argument('--interval', type=int, default=60, help='Interval between pulses in seconds (default: 60)')

    def handle(self, *args, **options):
        is_loop = options.get('loop')
        interval = options.get('interval')
        
        if is_loop:
            self.stdout.write(self.style.SUCCESS(f'Pulse Monitor started in Daemon mode (Interval: {interval}s)'))
            iteration = 0
            while True:
                status, latency = execute_pulse()
                self.stdout.write(self.style.SUCCESS(f'Pulse logged: {status} ({latency:.2f}ms)'))

                if status == 'CRITICAL':
                    self.send_emergency_alert(f"EXTREME LATENCY: {latency:.2f}ms", "System is slow.")

                iteration += 1
                if iteration % 30 == 0:
                    prune_old_pulses()

                time.sleep(interval)
        else:
            status, latency = execute_pulse()
            self.stdout.write(self.style.SUCCESS(f'Pulse logged: {status} ({latency:.2f}ms)'))

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
