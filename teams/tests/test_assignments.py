from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from ..models import CustomUser, Student, Team, Assignment, TeamSubmission

@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class AssignmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create Lecturer
        self.lecturer_user = CustomUser.objects.create_user(
            username='teacher@test.com', email='teacher@test.com', 
            password='pw', role='LECTURER'
        )
        # Create Student and Team
        self.student_user = CustomUser.objects.create_user(
            username='st@test.com', email='st@test.com', 
            password='pw', role='STUDENT'
        )
        self.student = Student.objects.create(user=self.student_user)
        self.team = Team.objects.create(name="Team Alpha")
        self.student.team = self.team
        self.student.save()
        self.team.leader = self.student
        self.team.save()

    def test_lecturer_creates_assignment(self):
        self.client.login(username='teacher@test.com', password='pw')
        deadline = timezone.now() + timedelta(days=7)
        response = self.client.post(reverse('teacher_dashboard'), {
            'create_assignment': '1',
            'title': 'Test Assignment',
            'description': 'Test Desc',
            'deadline': deadline.strftime('%Y-%m-%dT%H:%M')
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Assignment.objects.filter(title='Test Assignment').exists())

    def test_student_submits_assignment(self):
        # Create an assignment first
        assignment = Assignment.objects.create(
            title="Final Project",
            deadline=timezone.now() + timedelta(days=1),
            created_by=self.lecturer_user
        )
        
        self.client.login(username='st@test.com', password='pw')
        mock_file = SimpleUploadedFile("project.pdf", b"file_content", content_type="application/pdf")
        
        response = self.client.post(reverse('dashboard'), {
            'upload_assignment': '1',
            'assignment_id': assignment.id,
            'title': 'Our Submission',
            'file': mock_file
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TeamSubmission.objects.filter(team=self.team, assignment=assignment).exists())
        
    def test_late_submission_label(self):
        # Create a past assignment
        assignment = Assignment.objects.create(
            title="Past Due",
            deadline=timezone.now() - timedelta(days=1),
            created_by=self.lecturer_user
        )
        
        self.client.login(username='st@test.com', password='pw')
        mock_file = SimpleUploadedFile("late.pdf", b"late_content", content_type="application/pdf")
        
        self.client.post(reverse('dashboard'), {
            'upload_assignment': '1',
            'assignment_id': assignment.id,
            'title': 'Late Submission',
            'file': mock_file
        })
        
        # Check if dashboard shows LATE status
        response = self.client.get(reverse('dashboard'))
        # Search for assignment in list
        filtered_assign = [a for a in response.context['assignments'] if a.id == assignment.id][0]
        self.assertTrue(filtered_assign.is_late)
