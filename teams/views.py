from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Student, Team, Lecturer, CustomUser, ClassDocument, TeamSubmission, Assignment, SystemSettings
from .forms import (
    TeamRegistrationForm, UserRegistrationForm, DocumentUploadForm, 
    TeamProjectForm, StudentRoleForm, AssignmentForm, AssignmentSubmissionForm,
    GradeSubmissionForm
)

@login_required
def dashboard_view(request):
    if request.user.role == 'LECTURER':
        return redirect('teacher_dashboard')
    # DEV can access student view directly, no auto-redirect to dev_dashboard
    
    student, created = Student.objects.get_or_create(user=request.user)
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    assignments = Assignment.objects.all().order_by('-deadline')
    
    if student.team:
        team = student.team
        if not team.leader:
            team.leader = student
            team.save()

        if request.method == 'POST':
            if 'update_project' in request.POST and student == team.leader:
                proj_form = TeamProjectForm(request.POST, instance=team)
                if proj_form.is_valid():
                    proj_form.save()
                    messages.success(request, "Project details updated!")
                    return redirect('dashboard')
            
            elif 'update_role' in request.POST:
                role_form = StudentRoleForm(request.POST, instance=student)
                if role_form.is_valid():
                    role_form.save()
                    messages.success(request, "Your role updated!")
                    return redirect('dashboard')
        
        else:
            proj_form = TeamProjectForm(instance=team)
            role_form = StudentRoleForm(instance=student)

        # Build assignment status for student
        team_subs = {s.assignment_id: s for s in team.submissions.all()}
        for a in assignments:
            sub = team_subs.get(a.id)
            if sub:
                sub.is_late = sub.submitted_at > a.deadline if sub.submitted_at and a.deadline else False
            a.user_submission = sub

        return render(request, 'teams/dashboard.html', {
            'student': student,
            'team': team,
            'proj_form': proj_form,
            'role_form': role_form,
            'documents': documents,
            'assignments': assignments,
        })
    
    else:
        # Show team registration form
        if request.method == 'POST':
            form = TeamRegistrationForm(request.POST)
            if form.is_valid():
                team = form.save()
                student.team = team
                student.role = "Team Leader"
                student.save()
                team.leader = student
                team.save()
                messages.success(request, f"Team '{team.name}' registered!")
                return redirect('dashboard')
        else:
            form = TeamRegistrationForm()
        
        return render(request, 'teams/dashboard.html', {'form': form, 'student': student})

@login_required
def teacher_dashboard(request):
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        if 'upload_document' in request.POST:
            doc_form = DocumentUploadForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.uploaded_by = request.user
                doc.save()
                messages.success(request, "Document uploaded!")
                return redirect('teacher_dashboard')
        
        elif 'create_assignment' in request.POST:
            assign_form = AssignmentForm(request.POST, request.FILES)
            if assign_form.is_valid():
                assign = assign_form.save(commit=False)
                assign.created_by = request.user
                assign.save()
                messages.success(request, "Assignment created!")
                return redirect('teacher_dashboard')

        elif 'release_all_grades' in request.POST:
            Assignment.objects.filter(created_by=request.user).update(grades_released=True)
            messages.success(request, "All grades released to students!")
            return redirect('teacher_dashboard')

    teams = Team.objects.prefetch_related(
        'members__user', 
        'submissions__assignment'
    ).all().order_by('name')
    
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    assignments = Assignment.objects.all().order_by('-deadline')
    
    # Process teams to check if submissions were late with safeguards
    # and build a comprehensive status map for the assignment grid
    for t in teams:
        t.assignment_status = []
        # Create a dictionary of the team's submissions keyed by assignment ID
        # (Picking the latest submission if multiple exist)
        team_subs = {}
        for s in t.submissions.all():
            if s.assignment_id not in team_subs or s.submitted_at > team_subs[s.assignment_id].submitted_at:
                team_subs[s.assignment_id] = s
        
        for a in assignments:
            sub = team_subs.get(a.id)
            if sub:
                sub.is_late = False
                if sub.submitted_at and a.deadline:
                    sub.is_late = sub.submitted_at > a.deadline
            t.assignment_status.append({'assignment': a, 'submission': sub})

    # Only initialize new forms if they weren't already created (and potentially failed) during POST
    if 'doc_form' not in locals(): doc_form = DocumentUploadForm()
    if 'assign_form' not in locals(): assign_form = AssignmentForm()

    return render(request, 'teams/teacher_dashboard.html', {
        'teams': teams, 
        'assignments': assignments,
        'doc_form': doc_form,
        'assign_form': assign_form,
        'grade_form': GradeSubmissionForm(),
        'documents': documents
    })

@login_required
def grade_submission(request, pk):
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
        
    submission = get_object_or_404(TeamSubmission, pk=pk)
    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, f"Grade updated for {submission.team.name}")
    return redirect('teacher_dashboard')

@login_required
def delete_document(request, pk):
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
    doc = get_object_or_404(ClassDocument, pk=pk)
    doc.delete()
    messages.success(request, "Document deleted.")
    return redirect('teacher_dashboard')

def gallery_view(request):
    teams = Team.objects.all().order_by('name')
    return render(request, 'teams/gallery.html', {'teams': teams})

def guide_view(request):
    # Only show published documents to guest/all
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    return render(request, 'teams/guide.html', {'documents': documents})

def submission_detail(request, pk):
    submission = get_object_or_404(TeamSubmission, pk=pk)
    return render(request, 'teams/submission_detail.html', {'submission': submission})

@login_required
def submit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    student = getattr(request.user, 'student_profile', None)
    
    if not student or not student.team:
        messages.error(request, "You must be in a team to submit assignments.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.team = student.team
            submission.submitted_by = request.user
            submission.submitted_at = timezone.now()
            submission.save()
            messages.success(request, f"Successfully submitted {assignment.title}!")
            return redirect('dashboard')
    else:
        form = AssignmentSubmissionForm()
        
    return render(request, 'teams/submit_assignment.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
def view_grades(request, pk):
    # Assignment-specific grade view (not yet implemented fully in UI)
    return redirect('dashboard')

@login_required
def dev_dashboard(request):
    if request.user.role != 'DEV':
        return redirect('dashboard')
    
    users = CustomUser.objects.all()
    teams = Team.objects.all()
    # Add stats
    return render(request, 'teams/dev_dashboard.html', {
        'users': users,
        'teams': teams
    })

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('dashboard' if user.role == 'STUDENT' else 'teacher_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/signup.html', {'form': form})
