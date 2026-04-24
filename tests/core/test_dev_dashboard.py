from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.teams.models import Developer, Team, TeamSubmission, Student, SystemSettings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
import shutil
import os

User = get_user_model()

@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class DevDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a DEV user
        cls.dev_user = User.objects.create_user(
            username='dev@test.com', 
            email='dev@test.com', 
            password='pw', 
            role='DEV'
        )
        Developer.objects.create(user=cls.dev_user)
        
        # Create a Student user for access testing
        cls.student_user = User.objects.create_user(
            username='student@test.com', 
            email='student@test.com', 
            password='pw', 
            role='STUDENT'
        )
        Student.objects.create(user=cls.student_user)

        # Create some data for the dashboard
        cls.team = Team.objects.create(name="Team Alpha")
        SystemSettings.objects.create(max_team_size=5)
        
        TeamSubmission.objects.create(
            team=cls.team,
            title="Artifact 1",
            submitted_by=cls.student_user,
            file=SimpleUploadedFile("t1.txt", b"c")
        )

    def test_dev_dashboard_access(self):
        """Verify only DEV users can access the dev dashboard."""
        # 1. Anonymous user -> Redirect to login
        response = self.client.get(reverse('dev_dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dev_dashboard')}")

        # 2. Student user -> Redirect to student dashboard
        self.client.login(username='student@test.com', password='pw')
        response = self.client.get(reverse('dev_dashboard'), follow=True)
        self.assertRedirects(response, reverse('dashboard'))
        self.client.logout()

        # 3. DEV user -> Success
        self.client.login(username='dev@test.com', password='pw')
        response = self.client.get(reverse('dev_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teams/dev_dashboard.html')
        self.assertContains(response, "Developer")
        self.assertContains(response, "Control Center")
        self.assertContains(response, "Team Alpha")

    def test_dev_redirection_from_root(self):
        """Verify DEV users are redirected to their dashboard from the main entry point."""
        self.client.login(username='dev@test.com', password='pw')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('dev_dashboard'))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if os.path.exists('media'):
            shutil.rmtree('media')
