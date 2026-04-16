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
def dashboard_view(request, team_id=None):
    if request.user.role == 'LECTURER':
        return redirect('teacher_dashboard')
    
    # Clear any stale modal error markers
    if 'form_error_id' in request.session:
        error_id = request.session.pop('form_error_id')
    else:
        error_id = None

    student, created = Student.objects.get_or_create(user=request.user)
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    assignments = Assignment.objects.all().order_by('-deadline')
    
    # Determine the target team and access mode
    is_read_only = False
    if team_id:
        team = get_object_or_404(Team, id=team_id)
        # Developers can see any team; others must be members
        if request.user.role == 'DEV':
            if not team.members.filter(user=request.user).exists():
                is_read_only = True
        else:
            if not team.members.filter(user=request.user).exists():
                messages.error(request, "Access restricted. You can only view dashboards for teams you belong to.")
                return redirect('dashboard')
    else:
        team = student.team

    if team:
        if not team.leader and team.members.exists():
            # Auto-assign first member as leader if missing (legacy or dev-created)
            team.leader = team.members.first()
            team.save()

        # Disable POST processing if in read-only mode
        if request.method == 'POST' and not is_read_only:
            if 'update_project' in request.POST and student == team.leader:
                project_form = TeamProjectForm(request.POST, instance=team)
                if project_form.is_valid():
                    project_form.save()
                    messages.success(request, "Project details updated successfully.")
                    return redirect('dashboard_with_team', team_id=team.id) if team_id else redirect('dashboard')
            
            elif 'update_role' in request.POST:
                role_form = StudentRoleForm(request.POST, instance=student)
                if role_form.is_valid():
                    role_form.save()
                    messages.success(request, "Your role has been updated.")
                    return redirect('dashboard_with_team', team_id=team.id) if team_id else redirect('dashboard')

            elif 'upload_assignment' in request.POST:
                assign_id = request.POST.get('assignment_id')
                assignment = get_object_or_404(Assignment, id=assign_id)
                assign_form = AssignmentSubmissionForm(request.POST, request.FILES)
                
                if assign_form.is_valid():
                    files = request.FILES.getlist('files')
                    
                    # 1. Validate File Count
                    if len(files) > 10:
                        messages.error(request, "Maximum of 10 files allowed.")
                        request.session['form_error_id'] = assign_id
                        return redirect('dashboard_with_team', team_id=team.id) if team_id else redirect('dashboard')
                    
                    # 2. Validate Total Size (50MB)
                    total_size = sum(f.size for f in files)
                    if total_size > 50 * 1024 * 1024:
                        messages.error(request, "Total file size exceeds 50MB limit.")
                        request.session['form_error_id'] = assign_id
                        return redirect('dashboard_with_team', team_id=team.id) if team_id else redirect('dashboard')
                    
                    # 3. Validate File Types (No executables)
                    allowed_exts = ['.pdf', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.png', '.jpg', '.jpeg', '.gif']
                    import os
                    for f in files:
                        ext = os.path.splitext(f.name)[1].lower()
                        if ext not in allowed_exts:
                            messages.error(request, f"File type '{ext}' not allowed. Only documents and images are permitted.")
                            request.session['form_error_id'] = assign_id
                            return redirect('dashboard_with_team', team_id=team.id) if team_id else redirect('dashboard')

                    # All validations passed
                    sub = assign_form.save(commit=False)
                    sub.team = team
                    sub.assignment = assignment
                    sub.submitted_by = request.user
                    sub.save()
                    
                    # Create SubmissionFile objects
                    from .models import SubmissionFile
                    for f in files:
                        SubmissionFile.objects.create(submission=sub, file=f)
                    
                    status = "on time"
                    if sub.submitted_at and assignment.deadline and sub.submitted_at > assignment.deadline:
                        status = "LATE"
                    messages.success(request, f"Successfully submitted {len(files)} files to '{assignment.title}' ({status}).")
                    return redirect('dashboard_with_team', team_id=team.id) if team_id else redirect('dashboard')
                else:
                    request.session['form_error_id'] = assign_id

        # Annotate assignments
        for a in assignments:
            a.team_submission = team.submissions.filter(assignment=a).order_by('-submitted_at').first()
            if a.team_submission and a.team_submission.submitted_at and a.deadline:
                a.is_late = a.team_submission.submitted_at > a.deadline
            else:
                a.is_late = False

        # Forms (only for members with appropriate permissions)
        project_form = TeamProjectForm(instance=team)
        role_form = StudentRoleForm(instance=student)
        assign_form = AssignmentSubmissionForm()

        return render(request, 'teams/dashboard.html', {
            'student': student, 
            'team': team,
            'documents': documents,
            'assignments': assignments,
            'project_form': project_form,
            'role_form': role_form,
            'assign_form': assign_form,
            'error_id': error_id,
            'is_read_only': is_read_only,
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
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
    
    # Ensure lecturer profile exists
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

    # Prefetch with safer logic
    teams = Team.objects.prefetch_related(
        'members__user', 
        'submissions__assignment',
        'submissions__files'
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
                    try:
                        sub.is_late = sub.submitted_at > a.deadline
                    except (TypeError, ValueError):
                        sub.is_late = False
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
            messages.success(request, f"Grade updated for {submission.team.name}.")
    
    return redirect('teacher_dashboard')

@login_required
def release_grades(request, pk):
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
    
    assignment = get_object_or_404(Assignment, pk=pk)
    assignment.grades_released = True
    assignment.save()
    messages.success(request, f"Grades released for '{assignment.title}'. Students can now see their results!")
    return redirect('teacher_dashboard')

@login_required
def delete_document(request, pk):
    if request.user.role not in ['LECTURER', 'DEV']:
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
    
    if request.user.role in ['LECTURER', 'DEV'] or is_leader:
        title = submission.title
        submission.delete()
        messages.success(request, f"Submission '{title}' removed.")
    else:
        messages.error(request, "You do not have permission to delete this submission.")
    
    return redirect('dashboard' if request.user.role == 'STUDENT' else 'teacher_dashboard')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email # Use email as username
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            
            # Create profiles
            # Security: Force role to STUDENT regardless of POST data
            role = 'STUDENT'
            if role == 'STUDENT':
                Student.objects.get_or_create(user=user)
            elif role == 'DEV':
                from .models import Developer
                Developer.objects.get_or_create(user=user)
            else:
                Lecturer.objects.get_or_create(user=user)
            
            # Automatically log the user in after signup
            login(request, user, backend='teams.backends.CaseInsensitiveModelBackend')
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created successfully.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def dev_dashboard(request):
    if request.user.role != 'DEV':
        return redirect('dashboard')
    
    from django.db.models import Count, Q
    from django.db.models.functions import TruncDate
    from django.db import connection, OperationalError
    from django.conf import settings
    import platform
    import sys
    import django

    # 1. System Infrastructure Portals
    portals = {
        'admin': '/admin/',
        'render': 'https://dashboard.render.com',
        'cloudinary': f"https://cloudinary.com/console/cloud/{settings.CLOUDINARY_STORAGE['CLOUD_NAME']}",
        'postgres': 'https://dashboard.render.com', # Generic Render dash, user can find DB there
        'gmail': 'https://myaccount.google.com/apppasswords',
    }

    # 2. Advanced DB Diagnostics (Extra Detailed)
    db_telemetry = {
        'Team': Team.objects.count(),
        'Student': Student.objects.count(),
        'Assignment': Assignment.objects.count(),
        'Submission': TeamSubmission.objects.count(),
        'Lecturer': Lecturer.objects.count(),
        'ClassDocument': ClassDocument.objects.count(),
        'User': CustomUser.objects.count(),
        'db_engine': settings.DATABASES['default'].get('ENGINE', 'Unknown').split('.')[-1],
        'db_host': settings.DATABASES['default'].get('HOST', 'localhost'),
        'db_status': 'Unknown'
    }

    try:
        connection.ensure_connection()
        db_telemetry['db_status'] = 'Connected'
    except OperationalError:
        db_telemetry['db_status'] = 'Error'
    except Exception:
        db_telemetry['db_status'] = 'Error'

    # 3. Submission Activity Trends (Last 14 days)
    last_14_days = timezone.now() - timezone.timedelta(days=14)
    submission_trends = TeamSubmission.objects.filter(
        submitted_at__gte=last_14_days
    ).annotate(
        date=TruncDate('submitted_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Convert to JSON-friendly format for Chart.js
    trend_labels = [s['date'].strftime('%b %d') for s in submission_trends]
    trend_data = [s['count'] for s in submission_trends]

    # 2. Team Size Distribution
    team_sizes = Team.objects.annotate(
        m_count=Count('members')
    ).values('m_count').annotate(
        t_count=Count('id')
    ).order_by('m_count')
    
    size_labels = [f"{s['m_count']} Members" for s in team_sizes]
    size_data = [s['t_count'] for s in team_sizes]

    # 3. Role Breakdown
    roles = CustomUser.objects.values('role').annotate(count=Count('id'))
    role_labels = [r['role'] for r in roles]
    role_data = [r['count'] for r in roles]

    # 4. System & Platform Data
    sys_info = {
        'os': platform.system(),
        'os_release': platform.release(),
        'python_version': sys.version.split(' ')[0],
        'django_version': django.get_version() if 'django' in sys.modules else 'Unknown',
        'teams_count': Team.objects.count(),
        'students_count': Student.objects.count(),
        'submissions_count': TeamSubmission.objects.count(),
        'docs_count': ClassDocument.objects.count(),
    }

    # 5. Recent Activity Feed
    recent_activity = TeamSubmission.objects.select_related('team', 'submitted_by').all().order_by('-submitted_at')[:15]

    return render(request, 'teams/dev_dashboard.html', {
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'size_labels': size_labels,
        'size_data': size_data,
        'role_labels': role_labels,
        'role_data': role_data,
        'sys_info': sys_info,
        'recent_activity': recent_activity,
        'settings': SystemSettings.objects.first(),
        'portals': portals,
        'db_telemetry': db_telemetry,
    })

def gallery_view(request):
    teams = Team.objects.prefetch_related('members__user').all()
    return render(request, 'teams/gallery.html', {'teams': teams})

def guide_view(request):
    return render(request, 'teams/guide.html')

@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(TeamSubmission, pk=pk)
    # Security: Only team members or lecturers can see details
    if request.user.role not in ['LECTURER', 'DEV']:
        if not hasattr(request.user, 'student_profile') or request.user.student_profile.team != submission.team:
            messages.error(request, "Access denied.")
            return redirect('dashboard')
    
    return render(request, 'teams/submission_detail.html', {'submission': submission})

@login_required
def submit_assignment(request, pk):
    # This URL is now handled via POST to dashboard, but kept as a redirect 
    # to maintain compatibility with any old links.
    return redirect('dashboard')

@login_required
def view_grades(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if not assignment.grades_released:
        messages.warning(request, "Grades have not been released yet.")
        return redirect('dashboard')
    
    submission = None
    if hasattr(request.user, 'student_profile') and request.user.student_profile.team:
        submission = TeamSubmission.objects.filter(team=request.user.student_profile.team, assignment=assignment).first()
    
    return render(request, 'teams/view_grades.html', {'assignment': assignment, 'submission': submission})
