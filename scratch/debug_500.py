import os
import django
import sys

# Set up Django environment
sys.path.append(r'd:\DSP Class Web')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teams.models import Team, Student, Assignment, TeamSubmission, Lecturer, CustomUser
from django.template.loader import render_to_string
from django.test import RequestFactory

def debug_teacher_dashboard():
    print("--- Starting Diagnostic Trace ---")
    
    # 1. Check for any LECTURER users
    lecturers = CustomUser.objects.filter(role='LECTURER')
    if not lecturers.exists():
        print("No lecturers found in DB. Creating dummy for test...")
        user = CustomUser.objects.create_user(username='test_lecturer', email='test@test.com', role='LECTURER')
    else:
        user = lecturers.first()
        print(f"Testing with user: {user.email}")

    # 2. Simulate the view logic
    try:
        print("Pre-fetching teams...")
        teams = Team.objects.prefetch_related(
            'members__user', 
            'submissions__assignment'
        ).all().order_by('name')
        
        print("Processing submissions for is_late...")
        for t in teams:
            for s in t.submissions.all():
                s.is_late = False
                if s.assignment and s.submitted_at and s.assignment.deadline:
                    try:
                        s.is_late = s.submitted_at > s.assignment.deadline
                    except Exception as e:
                        print(f"CRASH during date comparison for Team {t.name}, Submission {s.id}: {e}")
                        raise e
        
        print("Logic pass SUCCESS. Attempting Template Render...")
        
        factory = RequestFactory()
        request = factory.get('/teacher/')
        request.user = user
        
        # We need to simulate the full context
        from teams.forms import DocumentUploadForm, AssignmentForm, GradeSubmissionForm
        from teams.models import ClassDocument
        
        context = {
            'teams': teams, 
            'assignments': Assignment.objects.all().order_by('-deadline'),
            'doc_form': DocumentUploadForm(),
            'assign_form': AssignmentForm(),
            'grade_form': GradeSubmissionForm(),
            'documents': ClassDocument.objects.all().order_by('-uploaded_at')
        }
        
        rendered = render_to_string('teams/teacher_dashboard.html', context, request=request)
        print("Render SUCCESS. Total characters:", len(rendered))
        
    except Exception as e:
        print(f"DIAGNOSTIC FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_teacher_dashboard()
