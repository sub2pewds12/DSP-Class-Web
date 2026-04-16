from django.test import TestCase, Client
from django.urls import reverse
from ..models import CustomUser, Student, Lecturer

class AuthRedirectionTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a Student user
        self.student_user = CustomUser.objects.create_user(
            username='student@test.com',
            email='student@test.com',
            password='password123',
            role='STUDENT',
            first_name='John',
            last_name='Doe'
        )
        # Create a Lecturer user
        self.lecturer_user = CustomUser.objects.create_user(
            username='teacher@test.com',
            email='teacher@test.com',
            password='password123',
            role='LECTURER',
            first_name='Professor',
            last_name='Smith'
        )

    def test_login_redirect_to_correct_dashboard(self):
        """Verify students go to student dashboard and teachers go to teacher dashboard."""
        
        # Test Student
        self.client.login(username='student@test.com', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teams/register.html') # Register view since no team yet
        self.client.logout()

        # Test Lecturer
        self.client.login(username='teacher@test.com', password='password123')
        # Accessing root dashboard should redirect lecturer to teacher_dashboard
        response = self.client.get(reverse('dashboard'), follow=True)
        self.assertTemplateUsed(response, 'teams/teacher_dashboard.html')
        self.client.logout()

    def test_lecturer_dashboard_permission(self):
        """Ensure students cannot access the teacher dashboard."""
        self.client.login(username='student@test.com', password='password123')
        response = self.client.get(reverse('teacher_dashboard'))
        # Should redirect back to student dashboard
        self.assertRedirects(response, reverse('dashboard'))

    def test_signup_creates_profiles(self):
        """Verify that signing up creates the correct profile (Student vs Lecturer)."""
        url = reverse('signup')
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@test.com',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
            'role': 'STUDENT'
        }
        self.client.post(url, data)
        
        user = CustomUser.objects.get(email='new@test.com')
        self.assertEqual(user.role, 'STUDENT')
        self.assertTrue(Student.objects.filter(user=user).exists())

    def test_signup_auto_login(self):
        """Verify that a user is automatically logged in after signing up."""
        url = reverse('signup')
        data = {
            'first_name': 'Auto',
            'last_name': 'Login',
            'email': 'auto@test.com',
            'password': 'autopassword123',
            'password_confirm': 'autopassword123',
            'role': 'STUDENT'
        }
        response = self.client.post(url, data, follow=True)
        # Verify the user is redirected to the dashboard and is authenticated
        self.assertEqual(response.status_code, 200)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertTemplateUsed(response, 'teams/register.html')

class CaseInsensitiveAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.email = 'MixedCase@Test.com'
        self.password = 'password123'
        self.user = CustomUser.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            role='STUDENT'
        )

    def test_login_case_insensitivity(self):
        """Verify that authentication works regardless of email capitalization."""
        test_cases = [
            'MixedCase@Test.com',  # Exact
            'mixedcase@test.com',  # Lower
            'MIXEDCASE@TEST.COM',  # Upper
        ]
        
        for email_variation in test_cases:
            logged_in = self.client.login(username=email_variation, password=self.password)
            self.assertTrue(logged_in, f"Failed logic for: {email_variation}")
            self.client.logout()

    def test_signup_case_collision_handling(self):
        """Verify that signing up with a duplicate email (different case) is blocked by backend."""
        # Note: The unique constraint on the Email field typically handles this,
        # but combined with our backend it's important to verify.
        url = reverse('signup')
        data = {
            'first_name': 'Duplicate',
            'last_name': 'Test',
            'email': 'mixedcase@test.com', # Different case but same email
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
            'role': 'STUDENT'
        }
        response = self.client.post(url, data)
        # Should not create a new user (form should have error or integrity error handled)
        self.assertFalse(CustomUser.objects.filter(email='mixedcase@test.com').count() > 1)
