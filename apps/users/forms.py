from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

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
        self.fields['role'].choices = User.ROLE_CHOICES
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

from apps.users.models import Student

class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(required=True, label="First Name")
    last_name = forms.CharField(required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'bio', 'avatar', 'email_notifications']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].widget = forms.FileInput(attrs={'class': 'form-control rounded-4 bg-soft text-main border-soft shadow-sm custom-file-input'})
        for name, field in self.fields.items():
            if name == 'avatar':
                continue
            
            if name == 'email_notifications':
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control rounded-4 bg-soft text-main border-soft shadow-sm'})

class StudentProfileForm(forms.ModelForm):
    student_id = forms.CharField(required=True, label="Student ID")

    class Meta:
        model = Student
        fields = ['student_id']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control rounded-4 bg-soft text-main border-soft shadow-sm',
                'placeholder': 'Enter your student ID'
            })

class StudentRoleForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['role']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget.attrs.update({'class': 'form-control', 'placeholder': 'e.g. Lead Coder, Designer...'})
