import os
import django
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from teams.models import User, Team, Assignment, TeamSubmission, SubmissionFile

def run_verification():
    print("Starting Multi-File Upload Verification...")
    
    # 1. Setup Test Data
    user = User.objects.filter(role='STUDENT').first()
    if not user:
        print("Creating test user...")
        user = User.objects.create_user(username='test_student', password='password123', email='test@example.com', role='STUDENT')
    
    team = Team.objects.create(name="Test Team", created_by=user)
    # Ensure user is in team if there's a Student model
    from teams.models import Student
    Student.objects.create(user=user, team=team)
    
    assignment = Assignment.objects.create(title="Test Assignment", deadline="2027-01-01 00:00:00")
    
    client = Client()
    client.login(username=user.username, password='password123')
    
    # 2. Test Success Case (2 files)
    print("\nTest 1: Valid 2-file upload...")
    f1 = SimpleUploadedFile("test1.pdf", b"pdf content", content_type="application/pdf")
    f2 = SimpleUploadedFile("test2.png", b"png content", content_type="image/png")
    
    response = client.post(reverse('dashboard'), {
        'upload_assignment': '1',
        'assignment_id': assignment.id,
        'title': 'Test Submission 1',
        'files': [f1, f2]
    })
    
    sub = TeamSubmission.objects.filter(title='Test Submission 1').first()
    if sub and sub.files.count() == 2:
        print("SUCCESS: 2 files uploaded and recorded.")
    else:
        print(f"FAILED: Expected 2 files, found {sub.files.count() if sub else 0}")

    # 3. Test Invalid Type (.exe)
    print("\nTest 2: Invalid file type (.exe)...")
    f_exe = SimpleUploadedFile("virus.exe", b"exe content", content_type="application/octet-stream")
    response = client.post(reverse('dashboard'), {
        'upload_assignment': '1',
        'assignment_id': assignment.id,
        'title': 'Test Submission EXE',
        'files': [f_exe]
    })
    
    sub_exe = TeamSubmission.objects.filter(title='Test Submission EXE').first()
    if not sub_exe:
        print("SUCCESS: EXE file rejected as expected.")
    else:
        print("FAILED: EXE file was incorrectly accepted.")

    # 4. Cleanup
    print("\nCleaning up test data...")
    team.delete()
    assignment.delete()
    print("Verification complete.")

if __name__ == "__main__":
    run_verification()
