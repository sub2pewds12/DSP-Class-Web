from django.utils import timezone
from .models import Student, Team, Lecturer, CustomUser, ClassDocument, TeamSubmission, Assignment
from .forms import (
    TeamRegistrationForm, UserRegistrationForm, DocumentUploadForm, 
    TeamProjectForm, StudentRoleForm, AssignmentForm, AssignmentSubmissionForm
)

@login_required
def dashboard_view(request):
    if request.user.role == 'LECTURER':
        return redirect('teacher_dashboard')
    
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
                assign_id = request.POST.get('assignment_id')
                assignment = get_object_or_404(Assignment, id=assign_id)
                assign_form = AssignmentSubmissionForm(request.POST, request.FILES)
                if assign_form.is_valid():
                    sub = assign_form.save(commit=False)
                    sub.team = team
                    sub.assignment = assignment
                    sub.submitted_by = request.user
                    sub.save()
                    
                    status = "on time"
                    if sub.submitted_at > assignment.deadline:
                        status = "LATE"
                    messages.success(request, f"Successfully submitted to '{assignment.title}' ({status}).")
                    return redirect('dashboard')

        # Annotate assignments with student's team submissions
        for a in assignments:
            a.team_submission = team.submissions.filter(assignment=a).first()
            if a.team_submission:
                a.is_late = a.team_submission.submitted_at > a.deadline

        return render(request, 'teams/dashboard.html', {
            'student': student, 
            'team': team,
            'documents': documents,
            'assignments': assignments,
            'project_form': TeamProjectForm(instance=team),
            'role_form': StudentRoleForm(instance=student),
            'assign_form': AssignmentSubmissionForm(),
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
    
    Lecturer.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        if 'upload_doc' in request.POST:
            doc_form = DocumentUploadForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.uploaded_by = request.user
                doc.save()
                messages.success(request, f"Document '{doc.title}' uploaded.")
                return redirect('teacher_dashboard')
        
        elif 'create_assignment' in request.POST:
            assign_form = AssignmentForm(request.POST, request.FILES)
            if assign_form.is_valid():
                assign = assign_form.save(commit=False)
                assign.created_by = request.user
                assign.save()
                messages.success(request, f"Assignment '{assign.title}' set with deadline: {assign.deadline}")
                return redirect('teacher_dashboard')

    teams = Team.objects.prefetch_related('members__user', 'submissions__assignment').all()
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    assignments = Assignment.objects.all().order_by('-deadline')
    
    # Process teams to check if submissions were late
    for t in teams:
        for s in t.submissions.all():
            if s.assignment:
                s.is_late = s.submitted_at > s.assignment.deadline

    return render(request, 'teams/teacher_dashboard.html', {
        'teams': teams, 
        'assignments': assignments,
        'doc_form': DocumentUploadForm(),
        'assign_form': AssignmentForm(),
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
