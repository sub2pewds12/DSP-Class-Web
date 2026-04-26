from django import forms
from .models import Team

class TeamSettingsForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'project_name', 'project_description', 'avatar']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].widget = forms.FileInput(attrs={'class': 'form-control rounded-4 bg-soft text-main border-soft shadow-sm custom-file-input'})
        for name, field in self.fields.items():
            if name != 'avatar':
                field.widget.attrs.update({'class': 'form-control rounded-4 bg-soft text-main border-soft shadow-sm'})
            
            if name == 'project_description':
                field.widget.attrs.update({'rows': 4})
