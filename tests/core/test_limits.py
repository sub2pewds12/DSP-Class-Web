from django.test import TestCase
from teams.models import Team, Student, CustomUser, SystemSettings
from apps.academia.forms import TeamRegistrationForm

class TeamLimitTests(TestCase):
    def setUp(self):
        # Set max size to 2 for easier testing
        SystemSettings.objects.create(max_team_size=2)
        self.team = Team.objects.create(name="Small Team")
        
        # Add 2 members (Reach capacity)
        for i in range(2):
            user = CustomUser.objects.create_user(
                username=f'user{i}@test.com', email=f'user{i}@test.com', 
                password='pw', role='STUDENT'
            )
            student = Student.objects.create(user=user, team=self.team)
            if i == 0:
                self.team.leader = student
                self.team.save()

    def test_team_capacity_form_validation(self):
        """Form should fail if joining a full team."""
        form_data = {
            'team_choice': self.team.id,
            'new_team_name': ''
        }
        form = TeamRegistrationForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn("already at maximum capacity", form.errors['__all__'][0])

    def test_new_team_creation_ignores_limit(self):
        """Creating a new team should still work regardless of other teams' capacity."""
        form_data = {
            'team_choice': '',
            'new_team_name': 'Brand New Team'
        }
        form = TeamRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
