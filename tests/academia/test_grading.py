from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.teams.models import CustomUser, Student, Team, Assignment, TeamSubmission

@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class GradingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.lecturer_user = CustomUser.objects.create_user(
            username='teacher@test.com', email='teacher@test.com', password='pw', role='LECTURER'
        )
        self.student_user = CustomUser.objects.create_user(
            username='st@test.com', email='st@test.com', password='pw', role='STUDENT'
        )
        self.student = Student.objects.create(user=self.student_user)
        self.team = Team.objects.create(name="Team Beta")
        self.student.team = self.team
        self.student.save()
        
        self.assignment = Assignment.objects.create(
            title="Grading Test",
            deadline=timezone.now() + timezone.timedelta(days=1),
            created_by=self.lecturer_user
        )
        
        self.submission = TeamSubmission.objects.create(
            team=self.team,
            assignment=self.assignment,
            title="Work",
            submitted_by=self.student_user,
            file=SimpleUploadedFile("work.txt", b"content")
        )

    def test_lecturer_grades_submission(self):
        self.client.login(username='teacher@test.com', password='pw')
        response = self.client.post(reverse('grade_submission', args=[self.submission.id]), {
            'grade': 85,
            'feedback': 'Good effort'
        }, follow=True)
        
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.grade, 85)
        self.assertEqual(self.submission.feedback, 'Good effort')

    def test_grade_visibility_logic(self):
        """Student should not see grade until released."""
        self.submission.grade = 100
        self.submission.feedback = "Top tier"
        self.submission.save()
        
        # 1. Check BEFORE release
        self.client.login(username='st@test.com', password='pw')
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, 'Top tier')
        
        # 2. Release grades
        self.client.logout()
        self.client.login(username='teacher@test.com', password='pw')
        self.client.get(reverse('release_grades', args=[self.assignment.id]))
        
        # 3. Check AFTER release
        self.client.logout()
        self.client.login(username='st@test.com', password='pw')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Top tier')
        self.assertContains(response, '100%')
