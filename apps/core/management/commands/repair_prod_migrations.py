from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Nuclear repair of migration history to handle Phase 4 modularization'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Checking for migration drift...'))
        
        with connection.cursor() as cursor:
            # 1. Check Academia App (Problematic 'is_active' column)
            cursor.execute("SELECT 1 FROM django_migrations WHERE app = 'academia' AND name = '0003_assignment_is_active' LIMIT 1;")
            if not cursor.fetchone():
                cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_name='teams_assignment' AND column_name='is_active' LIMIT 1;")
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING("Detected 'is_active' column in 'teams_assignment' without migration record. Faking 'academia'..."))
                    call_command('migrate', 'academia', fake=True, interactive=False, verbosity=1)

            # 2. Check Users App (Problematic 'can_grade' column)
            cursor.execute("SELECT 1 FROM django_migrations WHERE app = 'users' AND name = '0002_customuser_can_grade_and_more' LIMIT 1;")
            if not cursor.fetchone():
                cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_name='users_customuser' AND column_name='can_grade' LIMIT 1;")
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING("Detected 'can_grade' column in 'users_customuser' without migration record. Faking 'users'..."))
                    call_command('migrate', 'users', fake=True, interactive=False, verbosity=1)

            # 3. Standard Fake Initial for all apps (safely handles new tables)
            self.stdout.write("Running fake-initial for all apps...")
            call_command('migrate', fake_initial=True, interactive=False, verbosity=1)

        self.stdout.write(self.style.SUCCESS("Migration sync check complete."))
