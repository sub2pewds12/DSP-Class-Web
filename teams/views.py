from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from .models import Student, Team, Lecturer, CustomUser
from .forms import TeamRegistrationForm, UserRegistrationForm

@login_required
def dashboard_view(request):
    if request.user.role == 'LECTURER':
        return redirect('teacher_dashboard')
    
    # STUDENT logic: Ensure profile exists
    student, created = Student.objects.get_or_create(user=request.user)
    
    if student.team:
        return render(request, 'teams/dashboard.html', {'student': student, 'team': student.team})

    if request.method == 'POST':
        form = TeamRegistrationForm(request.POST)
        if form.is_valid():
            team_choice = form.cleaned_data['team_choice']
            new_team_name = form.cleaned_data['new_team_name']

            if team_choice:
                team = team_choice
            else:
                team, t_created = Team.objects.get_or_create(name=new_team_name)

            student.team = team
            student.save()
            messages.success(request, f"Successfully joined the team: {team.name}")
            return redirect('dashboard')
    else:
        form = TeamRegistrationForm()

    return render(request, 'teams/register.html', {'form': form})

@login_required
def teacher_dashboard(request):
    if request.user.role != 'LECTURER':
        return redirect('dashboard')
    
    teams = Team.objects.prefetch_related('members__user').all()
    # Create a lecturer profile if missing
    Lecturer.objects.get_or_create(user=request.user)
    
    return render(request, 'teams/teacher_dashboard.html', {'teams': teams})

def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email # Use email as username
            user.save()
            
            # Create profiles
            role = form.cleaned_data.get('role')
            if role == 'STUDENT':
                Student.objects.create(user=user)
            else:
                Lecturer.objects.create(user=user)
            
            # Trigger "Set Password" email using standard Django PasswordResetForm
            reset_form = PasswordResetForm({'email': user.email})
            if reset_form.is_valid():
                try:
                    reset_form.save(
                        request=request,
                        use_https=request.is_secure(),
                        subject_template_name='registration/password_set_subject.txt',
                        email_template_name='registration/password_set_email.html',
                    )
                    messages.success(request, "Account created! Please check your Gmail to set your initial password.")
                except Exception as e:
                    # Log failure to console for debugging on Render
                    print(f"SMTP Error: {e}")
                    # Log failure but allow signup to finish.
                    messages.warning(request, "Account created, but we couldn't send the onboarding email. Please try the 'Forgot Password' link later or contact the teacher.")
            
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/signup.html', {'form': form})

def gallery_view(request):
    teams = Team.objects.prefetch_related('members__user').all()
    return render(request, 'teams/gallery.html', {'teams': teams})
