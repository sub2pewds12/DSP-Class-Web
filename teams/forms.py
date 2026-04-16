from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Team, Student, SystemSettings, Lecturer, ClassDocument, TeamSubmission, Assignment

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict role choices to STUDENT only for public signups
        self.fields['role'].choices = [('STUDENT', 'Student')]
        for field in self.fields.values():
            if not isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match!")
        return cleaned_data

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

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = ClassDocument
        fields = ['title', 'file']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class TeamProjectForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['project_name', 'project_description']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class StudentRoleForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['role']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget.attrs.update({'class': 'form-control', 'placeholder': 'e.g. Lead Coder, Designer...'})

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

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class AssignmentSubmissionForm(forms.ModelForm):
    files = forms.FileField(
        widget=MultipleFileInput(attrs={
            'multiple': True,
            'class': 'form-control',
            'accept': '.pdf,.zip,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.png,.jpg,.jpeg,.gif'
        }),
        label="Select Files",
        help_text="Upload up to 10 files (max 50MB total)"
    )

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
