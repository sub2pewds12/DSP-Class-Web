from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.teams.models import CustomUser, Student, Team, TeamSubmission, Assignment

@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class PermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Teacher
        self.teacher = CustomUser.objects.create_user(
            username='teacher@test.com', email='teacher@test.com', password='pw', role='LECTURER'
        )
        # Leader
        self.leader_user = CustomUser.objects.create_user(
            username='leader@test.com', email='leader@test.com', password='pw', role='STUDENT'
        )
        self.leader = Student.objects.create(user=self.leader_user)
        self.team = Team.objects.create(name="Team Permission", leader=self.leader)
        self.leader.team = self.team
        self.leader.save()
        
        # Member (Non-leader)
        self.member_user = CustomUser.objects.create_user(
            username='member@test.com', email='member@test.com', password='pw', role='STUDENT'
        )
        self.member = Student.objects.create(user=self.member_user, team=self.team)
        
        # Other Student
        self.other_user = CustomUser.objects.create_user(
            username='other@test.com', email='other@test.com', password='pw', role='STUDENT'
        )
        
        self.submission = TeamSubmission.objects.create(
            team=self.team,
            title="Work",
            submitted_by=self.leader_user,
            file=SimpleUploadedFile("work.txt", b"content")
        )

    def test_student_cannot_access_teacher_dashboard(self):
        self.client.login(username='member@test.com', password='pw')
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_student_cannot_grade_direct_link(self):
        self.client.login(username='member@test.com', password='pw')
        response = self.client.post(reverse('grade_submission', args=[self.submission.id]), {
            'grade': 100
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.submission.refresh_from_db()
        self.assertIsNone(self.submission.grade)

    def test_delete_submission_permissions(self):
        # 1. Other student tries to delete -> Error
        self.client.login(username='other@test.com', password='pw')
        response = self.client.post(reverse('delete_submission', args=[self.submission.id]), follow=True)
        self.assertContains(response, "You do not have permission")
        self.assertTrue(TeamSubmission.objects.filter(id=self.submission.id).exists())
        
        # 2. Team member (non-leader) tries to delete -> Error
        self.client.login(username='member@test.com', password='pw')
        response = self.client.post(reverse('delete_submission', args=[self.submission.id]), follow=True)
        self.assertContains(response, "You do not have permission")
        self.assertTrue(TeamSubmission.objects.filter(id=self.submission.id).exists())

        # 3. Team leader tries to delete -> Success
        self.client.login(username='leader@test.com', password='pw')
        response = self.client.post(reverse('delete_submission', args=[self.submission.id]), follow=True)
        # Be more lenient with substring match and check DB
        self.assertContains(response, "removed") 
        self.assertFalse(TeamSubmission.objects.filter(id=self.submission.id).exists())
