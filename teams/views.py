from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Team
from .forms import TeamRegistrationForm

def dashboard_view(request):
    # Check if student has a session
    student_email = request.session.get('student_email')
    
    if student_email:
        student = Student.objects.filter(email=student_email).first()
        if student and student.team:
            return render(request, 'teams/dashboard.html', {'student': student, 'team': student.team})
        else:
            del request.session['student_email']

    if request.method == 'POST':
        form = TeamRegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            team_choice = form.cleaned_data['team_choice']
            new_team_name = form.cleaned_data['new_team_name']

            student, created = Student.objects.get_or_create(
                email=email,
                defaults={'first_name': first_name, 'last_name': last_name}
            )

            if team_choice:
                team = team_choice
            else:
                team, t_created = Team.objects.get_or_create(name=new_team_name)

            student.team = team
            student.save()

            request.session['student_email'] = student.email
            messages.success(request, "Successfully joined the team!")
            return redirect('dashboard')
    else:
        form = TeamRegistrationForm()

    return render(request, 'teams/register.html', {'form': form})

def gallery_view(request):
    teams = Team.objects.prefetch_related('members').all()
    return render(request, 'teams/gallery.html', {'teams': teams})
