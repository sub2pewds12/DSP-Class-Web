from django import forms
from .models import ClassDocument, Assignment, TeamSubmission

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = ClassDocument
        fields = ['title', 'file']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'instruction_file', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['instruction_file'].required = False
        for name, field in self.fields.items():
            if name != 'deadline':
                field.widget.attrs.update({'class': 'form-control'})

class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = TeamSubmission
        fields = ['title']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = TeamSubmission
        fields = ['grade', 'feedback']
        widgets = {
            'grade': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': '0-100'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your comments...'}),
        }

from django.core.exceptions import ValidationError
from teams.models import Team, SystemSettings

class TeamRegistrationForm(forms.Form):
    team_choice = forms.ModelChoiceField(queryset=Team.objects.all(), required=False, empty_label="--- Join an Existing Team ---")
    new_team_name = forms.CharField(max_length=255, required=False, label="Or Create a New Team")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        team_choice = cleaned_data.get('team_choice')
        new_team_name = cleaned_data.get('new_team_name')

        if team_choice and new_team_name:
            raise ValidationError("Please either join an existing team or create a new one, not both.")
        if not team_choice and not new_team_name:
            raise ValidationError("Please select an existing team to join or provide a name for a new team.")

        if team_choice:
            settings = SystemSettings.objects.first()
            max_size = settings.max_team_size if settings else 4
            if team_choice.members.count() >= max_size:
                raise ValidationError(f"The team '{team_choice.name}' is already at maximum capacity ({max_size} members).")
            
        return cleaned_data

class TeamProjectForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['project_name', 'project_description']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
