import time
from django.core.management.base import BaseCommand
from django.db import connection, OperationalError
from teams.models import SystemPulse

class Command(BaseCommand):
    help = 'Logs a system pulse with DB latency'

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
            self.stdout.write(self.style.SUCCESS(f'Pulse logged: {status} ({latency:.2f}ms)'))
            
        except (OperationalError, Exception) as e:
            latency = (time.time() - start_time) * 1000
            SystemPulse.objects.create(
                status='DOWN',
                latency=latency,
                info=str(e)
            )
            self.stdout.write(self.style.ERROR(f'Pulse logged: DOWN ({latency:.2f}ms)'))
