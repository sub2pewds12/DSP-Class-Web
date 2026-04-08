from django import forms
from django.core.exceptions import ValidationError
from .models import Team, Student, SystemSettings

class TeamRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    email = forms.EmailField()
    team_choice = forms.ModelChoiceField(queryset=Team.objects.all(), required=False, empty_label="--- Join an Existing Team ---")
    new_team_name = forms.CharField(max_length=255, required=False, label="Or Create a New Team")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        team_choice = cleaned_data.get('team_choice')
        new_team_name = cleaned_data.get('new_team_name')

        # Check if student is already assigned
        if email:
            student = Student.objects.filter(email=email).first()
            if student and student.team:
                raise ValidationError("A student with this email is already assigned to a team.")

        # Require one of team_choice or new_team_name
        if team_choice and new_team_name:
            raise ValidationError("Please either join an existing team or create a new one, not both.")
        if not team_choice and not new_team_name:
            raise ValidationError("Please select an existing team to join or provide a name for a new team.")

        # If joining an existing team, check capacity
        if team_choice:
            settings = SystemSettings.objects.first()
            max_size = settings.max_team_size if settings else 4
            if team_choice.members.count() >= max_size:
                raise ValidationError(f"The team '{team_choice.name}' is already at maximum capacity ({max_size} members).")
            
        return cleaned_data
