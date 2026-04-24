import os
import django
import random
from django.utils import timezone
from django.core.files.base import ContentFile

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.academia.models import TeamSubmission, Assignment, SubmissionFile
from apps.teams.models import Team
from apps.users.models import CustomUser

def run_stress_test(count=50):
    print(f"🚀 Starting Stress Test: Generating {count} real PDF submissions...")
    
    # 1. Get or create dependencies
    team = Team.objects.first()
    assignment = Assignment.objects.first()
    user = CustomUser.objects.filter(role='DEV').first()
    
    if not (team and assignment and user):
        print("❌ Error: Missing Team, Assignment, or Dev User. Please ensure base data exists.")
        return

    test_ids = []
    
    # 2. Generate Submissions
    for i in range(count):
        title = f"Stress Test Submission #{i+1}"
        # Create a dummy PDF content
        pdf_content = b"%PDF-1.4\n%TEST DATA STRESS TEST\n%%EOF"
        
        sub = TeamSubmission.objects.create(
            team=team,
            assignment=assignment,
            title=title,
            submitted_by=user,
            submitted_at=timezone.now()
        )
        
        # Attach real file
        sub.file.save(f"stress_test_{i}.pdf", ContentFile(pdf_content))
        sub.save()
        
        test_ids.append(sub.id)
        if i % 10 == 0:
            print(f"  ... {i} submissions created")

    print(f"✅ Success! {count} real submissions generated.")
    return test_ids

def cleanup_test(test_ids):
    print(f"🚮 Cleaning up {len(test_ids)} test records and files...")
    subs = TeamSubmission.objects.filter(id__in=test_ids)
    
    for sub in subs:
        # Delete physical file
        if sub.file:
            if os.path.exists(sub.file.path):
                os.remove(sub.file.path)
        sub.delete()
    
    print("✨ Environment sanitized. All test artifacts removed.")

if __name__ == "__main__":
    # We will run this in chunks via the shell or as a script
    ids = run_stress_test(50)
    # The cleanup will be called manually after the user confirms
    with open('last_test_ids.txt', 'w') as f:
        f.write(','.join(map(str, ids)))
