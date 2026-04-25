from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Nuclear repair of migration history to handle Phase 4 modularization'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Checking for migration drift...'))
        
        # Mapping of app to a table that indicates it was already applied
        drift_check = {
            'contenttypes': 'django_content_type',
            'auth': 'auth_user',
            'admin': 'django_admin_log',
            'sessions': 'django_session',
            'users': 'users_customuser',
            'teams': 'teams_team',
            'academia': 'teams_assignment',
        }

        with connection.cursor() as cursor:
            for app, table in drift_check.items():
                # Check if the app is already in django_migrations
                cursor.execute("SELECT 1 FROM django_migrations WHERE app = %s LIMIT 1;", [app])
                already_recorded = cursor.fetchone()

                if not already_recorded:
                    # App is not recorded. Check if its table exists.
                    cursor.execute("SELECT to_regclass(%s);", [table])
                    table_exists = cursor.fetchone()[0]

                    if table_exists:
                        self.stdout.write(self.style.WARNING(f"App '{app}' has existing tables but no migration history. Syncing (faking)..."))
                        call_command('migrate', app, fake=True, interactive=False, verbosity=1)
                    else:
                        self.stdout.write(f"App '{app}' is new or table-less. Standard migration will handle it.")
                else:
                    self.stdout.write(self.style.SUCCESS(f"App '{app}' is already in sync."))

        self.stdout.write(self.style.SUCCESS("Migration sync check complete."))
