from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from .models import Student, Team, Lecturer, CustomUser, ClassDocument
from .forms import TeamRegistrationForm, UserRegistrationForm, DocumentUploadForm

@login_required
def dashboard_view(request):
    if request.user.role == 'LECTURER':
        return redirect('teacher_dashboard')
    
    # STUDENT logic: Ensure profile exists
    student, created = Student.objects.get_or_create(user=request.user)
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    
    if student.team:
        return render(request, 'teams/dashboard.html', {
            'student': student, 
            'team': student.team,
            'documents': documents
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

    teams = Team.objects.prefetch_related('members__user').all()
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
