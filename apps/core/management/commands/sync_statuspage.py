from django.core.management.base import BaseCommand
from apps.core.services.statuspage_service import StatuspageService
import json

class Command(BaseCommand):
    help = 'Synchronizes internal infrastructure health with Atlassian Statuspage'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Statuspage synchronization...'))
        
        try:
            result = StatuspageService.sync_infrastructure()
            self.stdout.write(self.style.SUCCESS(
                f"Successfully synced. Health Score: {result['health_score']}, Pushed Status: {result['status_pushed']}"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Sync failed: {str(e)}"))
