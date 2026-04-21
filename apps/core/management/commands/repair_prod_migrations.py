from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Nuclear repair of migration history to handle Phase 4 modularization'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting nuclear migration repair...'))
        
        with connection.cursor() as cursor:
            # Check if django_migrations table exists
            cursor.execute("SELECT to_regclass('django_migrations');")
            if not cursor.fetchone()[0]:
                self.stdout.write(self.style.SUCCESS('django_migrations table not found. Skipping (fresh DB).'))
                return

            self.stdout.write("Truncating django_migrations table for a clean Phase 4 initialization...")
            cursor.execute("DELETE FROM django_migrations;")
            
            rows_deleted = cursor.rowcount
            self.stdout.write(self.style.SUCCESS(f"Successfully cleared {rows_deleted} migration records."))
            self.stdout.write(self.style.SUCCESS("System is ready for 'migrate --fake-initial'."))
