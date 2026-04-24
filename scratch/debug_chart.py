import os
import django
from django.utils import timezone
from django.db.models.functions import TruncDate
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.academia.models import TeamSubmission

def debug_trends():
    total = TeamSubmission.objects.count()
    print(f"Total Submissions in DB: {total}")
    
    last_14 = timezone.now() - timezone.timedelta(days=14)
    trends = TeamSubmission.objects.filter(
        submitted_at__gte=last_14
    ).annotate(
        date=TruncDate('submitted_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    print(f"Trends Query Result Count: {len(trends)}")
    for t in trends:
        print(f" - {t['date']}: {t['count']}")

if __name__ == "__main__":
    debug_trends()
