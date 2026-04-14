from django.test import TestCase, Client
from django.urls import reverse
from ..models import CustomUser, Student, Team

class TeamRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='st@test.com', email='st@test.com', password='pw', role='STUDENT'
        )
        self.student = Student.objects.create(user=self.user)
        self.team = Team.objects.create(name="Team Alpha")

    def test_joining_team(self):
        self.client.login(username='st@test.com', password='pw')
        response = self.client.post(reverse('dashboard'), {
            'team_choice': self.team.id,
            'new_team_name': ''
        })
        self.student.refresh_from_db()
        self.assertEqual(self.student.team, self.team)
