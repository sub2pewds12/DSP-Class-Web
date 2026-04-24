import os
import django
import random
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.teams.models import Team
from apps.academia.models import Assignment, TeamSubmission
from apps.users.models import CustomUser

def run_stress_test():
    print("STARTING: Chart Stress Test...")
    
    # 1. Get or create a base user (Lecturer or anyone available)
    user = CustomUser.objects.filter(role='LECTURER').first() or CustomUser.objects.first()
    if not user:
        print("ERROR: No users found in database. Please register at least one user first.")
        return

    # 2. Setup Test Context
    team, _ = Team.objects.get_or_create(name="Chart Stress Test Team")
    assignment, _ = Assignment.objects.get_or_create(
        title="Stress Test Assignment",
        defaults={
            'deadline': timezone.now() + timezone.timedelta(days=30), 
            'created_by': user,
            'description': 'Automated stress test assignment for chart validation.'
        }
    )

    # 3. Generate Data for the last 14 days
    print("GENERATING: 14 days of submission data...")
    total_created = 0
    
    for day_offset in range(14):
        # We target each day specifically
        target_date = timezone.now() - timezone.timedelta(days=day_offset)
        
        # Random number of submissions for this day to create a "Natural" looking chart
        # We vary the count so the line graph goes up and down
        num_subs = random.randint(3, 12)
        
        for i in range(num_subs):
            sub = TeamSubmission.objects.create(
                team=team,
                assignment=assignment,
                title=f"Stress Test Sub - Day {day_offset} #{i}",
                submitted_by=user
            )
            # FORCE the timestamp back in time via .update() 
            # (bypass auto_now_add)
            TeamSubmission.objects.filter(pk=sub.pk).update(submitted_at=target_date)
            total_created += 1
        
        print(f"  - Day {day_offset}: Created {num_subs} submissions.")

    print(f"\nSUCCESS! Created {total_created} submissions across 14 days.")
    print("Refresh your dashboard to see the 'Submission Activity' chart populated.")

if __name__ == "__main__":
    run_stress_test()
