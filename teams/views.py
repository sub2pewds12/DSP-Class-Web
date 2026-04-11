from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from .models import Student, Team, Lecturer, CustomUser, ClassDocument, TeamSubmission
from .forms import TeamRegistrationForm, UserRegistrationForm, DocumentUploadForm, TeamProjectForm, StudentRoleForm, AssignmentUploadForm

@login_required
def dashboard_view(request):
    if request.user.role == 'LECTURER':
        return redirect('teacher_dashboard')
    
    student, created = Student.objects.get_or_create(user=request.user)
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    
    if student.team:
        team = student.team
        # First person joining/creating is the leader
        if not team.leader:
            team.leader = student
            team.save()

        if request.method == 'POST':
            if 'update_project' in request.POST and student == team.leader:
                project_form = TeamProjectForm(request.POST, instance=team)
                if project_form.is_valid():
                    project_form.save()
                    messages.success(request, "Project details updated successfully.")
                    return redirect('dashboard')
            
            elif 'update_role' in request.POST:
                role_form = StudentRoleForm(request.POST, instance=student)
                if role_form.is_valid():
                    role_form.save()
                    messages.success(request, "Your role has been updated.")
                    return redirect('dashboard')

            elif 'upload_assignment' in request.POST:
                assign_form = AssignmentUploadForm(request.POST, request.FILES)
                if assign_form.is_valid():
                    sub = assign_form.save(commit=False)
                    sub.team = team
                    sub.submitted_by = request.user
                    sub.save()
                    messages.success(request, f"Assignment '{sub.title}' submitted successfully.")
                    return redirect('dashboard')

        # Prep forms for display
        return render(request, 'teams/dashboard.html', {
            'student': student, 
            'team': team,
            'documents': documents,
            'project_form': TeamProjectForm(instance=team),
            'role_form': StudentRoleForm(instance=student),
            'assign_form': AssignmentUploadForm(),
            'submissions': team.submissions.all().order_by('-submitted_at')
        })

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
            
            # If they are the first member, they become the leader
            if team.members.count() == 1:
                team.leader = student
                team.save()

            messages.success(request, f"Successfully joined the team: {team.name}")
            return redirect('dashboard')
    else:
        form = TeamRegistrationForm()

    return render(request, 'teams/register.html', {'form': form, 'documents': documents})

@login_required
def teacher_dashboard(request):
    if request.user.role != 'LECTURER':
        return redirect('dashboard')
    
    # Create a lecturer profile if missing
    Lecturer.objects.get_or_create(user=request.user)
    
    if request.method == 'POST' and 'upload_doc' in request.POST:
        doc_form = DocumentUploadForm(request.POST, request.FILES)
        if doc_form.is_valid():
            doc = doc_form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()
            messages.success(request, f"Document '{doc.title}' uploaded successfully.")
            return redirect('teacher_dashboard')
    else:
        doc_form = DocumentUploadForm()

    teams = Team.objects.prefetch_related('members__user', 'submissions').all()
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    
    return render(request, 'teams/teacher_dashboard.html', {
        'teams': teams, 
        'doc_form': doc_form,
        'documents': documents
    })

@login_required
def delete_document(request, pk):
    if request.user.role != 'LECTURER':
        return redirect('dashboard')
    doc = get_object_or_404(ClassDocument, pk=pk)
    title = doc.title
    doc.delete()
    messages.success(request, f"Document '{title}' deleted.")
    return redirect('teacher_dashboard')

@login_required
def delete_submission(request, pk):
    submission = get_object_or_404(TeamSubmission, pk=pk)
    # Only the team leader or a lecturer can delete a submission
    is_leader = hasattr(request.user, 'student_profile') and request.user.student_profile.team == submission.team and submission.team.leader == request.user.student_profile
    
    if request.user.role == 'LECTURER' or is_leader:
        title = submission.title
        submission.delete()
        messages.success(request, f"Submission '{title}' removed.")
    else:
        messages.error(request, "You do not have permission to delete this submission.")
    
    return redirect('dashboard' if request.user.role == 'STUDENT' else 'teacher_dashboard')

def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email # Use email as username
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            
            # Create profiles
            role = form.cleaned_data.get('role')
            if role == 'STUDENT':
                Student.objects.get_or_create(user=user)
            else:
                Lecturer.objects.get_or_create(user=user)
            
            # Automatically log the user in after signup
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created successfully.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/signup.html', {'form': form})

def gallery_view(request):
    teams = Team.objects.prefetch_related('members__user').all()
    return render(request, 'teams/gallery.html', {'teams': teams})
