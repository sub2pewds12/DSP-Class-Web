from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Surgically repairs migration history on production to handle modularization refactor'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting production migration repair...'))
        
        # We need to clear the records of apps that prevent the new 'users' 0001_initial from running.
        # Specifically, any app that depends on AUTH_USER_MODEL but is already marked as 'applied'.
        apps_to_clear = ['admin', 'auth', 'contenttypes', 'authtoken', 'sessions', 'teams']
        
        with connection.cursor() as cursor:
            # Check if django_migrations table exists
            cursor.execute("SELECT to_regclass('django_migrations');")
            if not cursor.fetchone()[0]:
                self.stdout.write(self.style.SUCCESS('django_migrations table not found. Skipping repair (fresh DB).'))
                return

            self.stdout.write(f"Clearing migration records for: {', '.join(apps_to_clear)}")
            
            # Using parameterized query for safety even in a repair script
            placeholders = ', '.join(['%s'] * len(apps_to_clear))
            query = f"DELETE FROM django_migrations WHERE app IN ({placeholders})"
            cursor.execute(query, apps_to_clear)
            
            rows_deleted = cursor.rowcount
            self.stdout.write(self.style.SUCCESS(f"Successfully cleared {rows_deleted} migration records."))
            self.stdout.write(self.style.SUCCESS("Post-repair: Run 'migrate --fake-initial' to rebuild history safely."))
