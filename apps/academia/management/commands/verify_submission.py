from django.core.management.base import BaseCommand
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from apps.users.models import CustomUser, Student
from apps.academia.models import Assignment, TeamSubmission, SubmissionFile
from teams.models import Team

class Command(BaseCommand):
    help = 'Verifies the multi-file upload logic'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Multi-File Upload Verification..."))
        
        # 1. Setup Test Data
        user = CustomUser.objects.filter(role='STUDENT').first()
        if not user:
            self.stdout.write("Creating test user...")
            user = CustomUser.objects.create_user(
                username='test_student@example.com', 
                password='password123', 
                email='test_student@example.com', 
                role='STUDENT'
            )
        
        # Check if student profile exists
        student, created = Student.objects.get_or_create(user=user)
        
        # Create or Get Team
        team = Team.objects.create(name="Verification Test Team")
        student.team = team
        student.save()
        
        # Set leader
        team.leader = student
        team.save()
        
        assignment = Assignment.objects.create(
            title="Verification Test Assignment", 
            deadline="2027-01-01 00:00:00"
        )
        
        client = Client()
        # Use email-based login for current auth logic
        client.login(username=user.email, password='password123')
        
        try:
            # 2. Test Success Case (2 files)
            self.stdout.write(self.style.NOTICE("\nTest 1: Valid 2-file upload..."))
            f1 = SimpleUploadedFile("test1.pdf", b"pdf content", content_type="application/pdf")
            f2 = SimpleUploadedFile("test2.png", b"png content", content_type="image/png")
            
            response = client.post(reverse('dashboard'), {
                'upload_assignment': '1',
                'assignment_id': assignment.id,
                'title': 'Test Verification 1',
                'files': [f1, f2]
            })
            
            sub = TeamSubmission.objects.filter(title='Test Verification 1').first()
            if sub and sub.files.count() == 2:
                self.stdout.write(self.style.SUCCESS("SUCCESS: 2 files uploaded and recorded."))
            else:
                self.stdout.write(self.style.ERROR(f"FAILED: Expected 2 files, found {sub.files.count() if sub else 0}"))

            # 3. Test Invalid Type (.exe)
            self.stdout.write(self.style.NOTICE("\nTest 2: Invalid file type (.exe)..."))
            f_exe = SimpleUploadedFile("virus.exe", b"exe content", content_type="application/octet-stream")
            response = client.post(reverse('dashboard'), {
                'upload_assignment': '1',
                'assignment_id': assignment.id,
                'title': 'Test Verification EXE',
                'files': [f_exe]
            })
            
            sub_exe = TeamSubmission.objects.filter(title='Test Verification EXE').first()
            if not sub_exe:
                self.stdout.write(self.style.SUCCESS("SUCCESS: EXE file rejected as expected."))
            else:
                self.stdout.write(self.style.ERROR("FAILED: EXE file was incorrectly accepted."))

        finally:
            # 4. Cleanup
            self.stdout.write(self.style.NOTICE("\nCleaning up test data..."))
            team.delete()
            assignment.delete()
            self.stdout.write(self.style.SUCCESS("Verification complete."))
