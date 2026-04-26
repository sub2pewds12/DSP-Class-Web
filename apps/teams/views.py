from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import requests

def health_check(request):
    """Lighweight endpoint for external monitoring services."""
    return HttpResponse("SYSTEM_OPERATIONAL", status=200)
from .models import Team, Student, Lecturer, CustomUser, SystemSettings
from apps.academia.models import ClassDocument, TeamSubmission, Assignment
from apps.core.utils.email_service import send_html_email
from .forms import TeamSettingsForm
from apps.users.forms import UserRegistrationForm, StudentRoleForm, UserEditForm, StudentProfileForm
from apps.academia.forms import (
    DocumentUploadForm, AssignmentForm, AssignmentSubmissionForm, 
    GradeSubmissionForm, TeamRegistrationForm, TeamProjectForm
)
from apps.academia.services import SubmissionService, AssignmentService
from apps.users.services import UserService
from apps.core.services import InfrastructureService
from .services import TeamService


@login_required
def dashboard_view(request, team_id=None):
    if not getattr(request.user, 'is_approved', False):
        return redirect('pending_approval')
        
    if request.user.role == 'LECTURER':
        return redirect('teacher_dashboard')
    if request.user.role == 'DEV' and not team_id:
        return redirect('dev_dashboard')

    student, _ = Student.objects.get_or_create(user=request.user)
    
    # Determine team context
    team = student.team
    is_read_only = False
    if team_id:
        team = get_object_or_404(Team, id=team_id)
        if request.user.role != 'DEV' and not team.members.filter(user=request.user).exists():
            messages.error(request, "Access restricted.")
            return redirect('dashboard')
        if request.user.role == 'DEV' and not team.members.filter(user=request.user).exists():
            is_read_only = True

    # Handle Actions
    if request.method == 'POST':
        if team and 'upload_assignment' in request.POST:
            form = AssignmentSubmissionForm(request.POST, request.FILES)
            if form.is_valid():
                assignment = get_object_or_404(Assignment, id=request.POST.get('assignment_id'))
                files = request.FILES.getlist('files')
                if not files:
                    messages.error(request, "Please select at least one file.")
                    return redirect('dashboard')
                
                try:
                    SubmissionService.create_submission(
                        user=request.user,
                        assignment=assignment,
                        title=form.cleaned_data['title'],
                        files=files
                    )
                    messages.success(request, f"Assignment '{assignment.title}' submitted.")
                except ValueError as e:
                    messages.error(request, str(e))
                return redirect('dashboard')
        
        elif not team:
            form = TeamRegistrationForm(request.POST)
            if form.is_valid():
                try:
                    team = TeamService.join_or_create_team(
                        student=student,
                        team_choice=form.cleaned_data.get('team_choice'),
                        new_team_name=form.cleaned_data.get('new_team_name')
                    )
                    messages.success(request, f"Joined {team.name}")
                    return redirect('dashboard')
                except (ValueError, IntegrityError) as e:
                    messages.error(request, str(e))
                    return redirect('dashboard')

    # Use Service Layer for Context
    context = AssignmentService.get_student_dashboard_context(request.user, team=team)
    
    # Simulation Mode: If no assignment is found, mock one for the "Mission Control" tile (DEBUG ONLY)
    next_deadline = context.get('next_deadline')
    from django.conf import settings
    if not next_deadline and settings.DEBUG:
        from django.utils import timezone
        from datetime import timedelta
        class MockAssignment:
            def __init__(self):
                self.title = "Final Project Submission (SIMULATED)"
                self.deadline = timezone.now() + timedelta(days=2, hours=14, minutes=30)
        next_deadline = MockAssignment()

    # Simulation Mode: Mock activity for "Latest Activities" feed if empty (DEBUG ONLY)
    team_activity = context.get('team_activity', [])
    if not team_activity and settings.DEBUG:
        from django.utils import timezone
        from datetime import timedelta
        class MockLog:
            def __init__(self, actor_name, desc, minutes_ago):
                self.actor = type('MockActor', (), {'username': actor_name})
                self.description = desc
                self.timestamp = timezone.now() - timedelta(minutes=minutes_ago)
        
        team_activity = [
            MockLog("alex_dev", "Updated the project topic: 'Real-time Signal Processing with Python'", 12),
            MockLog("sarah_design", "Changed their role to 'UI/UX Lead'", 45),
            MockLog("system", "New resource 'DSP Algorithm Guide.pdf' was added", 120),
        ]

    if team:
        return render(request, 'teams/dashboard.html', {
            'student': student,
            'team': team,
            'documents': context['documents'],
            'assignments': context['assignments'],
            'next_deadline': next_deadline,
            'team_activity': team_activity,
            'project_form': TeamProjectForm(instance=team),
            'role_form': StudentRoleForm(instance=student),
            'assign_form': AssignmentSubmissionForm(),
            'is_read_only': is_read_only
        })

    return render(request, 'teams/register.html', {
        'form': TeamRegistrationForm(),
        'documents': context['documents']
    })

def guide_view(request):
    return render(request, 'teams/guide.html')

@login_required
def teacher_dashboard(request):
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
        
    # Offload all dashboard context gathering to service
    context = AssignmentService.get_teacher_dashboard_context(request.user)

    if request.method == 'POST':
        if 'create_assignment' in request.POST:
            assign_form = AssignmentForm(request.POST, request.FILES)
            if assign_form.is_valid():
                AssignmentService.create_assignment(
                    user=request.user,
                    title=assign_form.cleaned_data['title'],
                    deadline=assign_form.cleaned_data['deadline'],
                    description=assign_form.cleaned_data['description'],
                    instruction_file=request.FILES.get('instruction_file')
                )
                messages.success(request, "Assignment created successfully.")
                return redirect('teacher_dashboard')
        
    return render(request, 'teams/teacher_dashboard.html', {
        'teams': context['teams'], 
        'assignments': context['assignments'],
        'doc_form': DocumentUploadForm(),
        'assign_form': AssignmentForm(),
        'grade_form': GradeSubmissionForm(),
        'documents': context['documents'],
        'trend_labels': context['trend_labels'],
        'trend_data': context['trend_data'],
        'trend_details': context['trend_details']
    })




@login_required
def delete_submission(request, pk):
    submission = get_object_or_404(TeamSubmission, pk=pk)
    # Only the team leader or a lecturer can delete a submission
    is_leader = hasattr(request.user, 'student_profile') and \
                submission.team.leader == request.user.student_profile
    
    if request.user.role in ['LECTURER', 'DEV'] or is_leader:
        title = SubmissionService.delete_submission(submission, request.user)
        messages.success(request, f"Submission '{title}' removed.")
    else:
        messages.error(request, "You do not have permission to delete this submission.")
    
    return redirect('dashboard' if request.user.role == 'STUDENT' else 'teacher_dashboard')

@login_required
def grade_submission(request, pk):
    if request.user.role not in ['LECTURER', 'DEV']:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    
    submission = get_object_or_404(TeamSubmission, pk=pk)
    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST)
        if form.is_valid():
            SubmissionService.grade_submission(
                submission=submission,
                grade=form.cleaned_data['grade'],
                feedback=form.cleaned_data['feedback']
            )
            messages.success(request, f"Submission for {submission.team.name} graded.")
    return redirect('teacher_dashboard')

@login_required
def release_grades(request, pk):
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
    
    assignment = get_object_or_404(Assignment, pk=pk)
    AssignmentService.release_grades(assignment, request.user)
    messages.success(request, f"Grades for '{assignment.title}' have been released.")
    return redirect('teacher_dashboard')

@login_required
def upload_document(request):
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            AssignmentService.upload_document(
                user=request.user,
                title=form.cleaned_data['title'],
                file=request.FILES['file']
            )
            messages.success(request, "Document uploaded successfully.")
    return redirect('teacher_dashboard')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user, is_auto_approved = UserService.register_user(form.cleaned_data, request)
            
            if is_auto_approved:
                messages.success(request, f"Welcome, {user.first_name}! Your account has been created successfully.")
                return redirect('dashboard')
            
            messages.info(request, f"Registration submitted. An administrator must approve your {user.role.lower()} access.")
            return redirect('pending_approval')
    else:
        form = UserRegistrationForm()
    return render(request, 'teams/registration/signup.html', {'form': form})

@login_required
def dev_dashboard(request):
    if not getattr(request.user, 'is_approved', False):
        return redirect('pending_approval')
        
    if request.user.role != 'DEV':
        return redirect('dashboard')
    
    # Offload all monitoring logic to service
    telemetry = InfrastructureService.get_dev_dashboard_telemetry()

    return render(request, 'teams/dev_dashboard.html', telemetry)

def gallery_view(request):
    if request.user.is_authenticated and not getattr(request.user, 'is_approved', False):
        return redirect('pending_approval')
    teams = Team.objects.prefetch_related('members__user').all()
    return render(request, 'teams/gallery.html', {'teams': teams})


@login_required
def storage_analytics_view(request):
    if not getattr(request.user, 'is_approved', False):
        return redirect('pending_approval')
        
    if request.user.role != 'DEV':
        return redirect('dashboard')
        
    storage_stats = InfrastructureService.get_storage_analytics()
    
    # 3. Recent Assets (Aggregated for UI)
    recent_docs = list(ClassDocument.objects.order_by('-uploaded_at')[:5])
    recent_subs = list(TeamSubmission.objects.exclude(file='').select_related('team').order_by('-submitted_at')[:5])
    
    def get_human_size(file_obj):
        try:
            size = file_obj.size
            if size < 1024: return f"{size} B"
            if size < 1024 * 1024: return f"{round(size/1024, 1)} KB"
            return f"{round(size/(1024*1024), 1)} MB"
        except: return "0 B"

    for doc in recent_docs: doc.file_size = get_human_size(doc.file)
    for sub in recent_subs: sub.file_size = get_human_size(sub.file)
    
    return render(request, 'teams/storage_analytics.html', {
        'stats': storage_stats,
        'recent_docs': recent_docs,
        'recent_subs': recent_subs,
        'cloudinary_portal': storage_stats['portal_url']
    })

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

def pending_approval_view(request):
    return render(request, 'teams/registration/pending_approval.html')

@login_required
def settings_view(request):
    user = request.user
    student_profile = getattr(user, 'student_profile', None)
    
    # Identify if the user is a team leader
    managed_team = None
    if student_profile and student_profile.team:
        if student_profile.team.leader == student_profile:
            managed_team = student_profile.team

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'personal':
            user_form = UserEditForm(request.POST, request.FILES, instance=user, prefix='user')
            profile_form = StudentProfileForm(request.POST, instance=student_profile, prefix='profile') if student_profile else None
            team_form = TeamSettingsForm(instance=managed_team, prefix='team') if managed_team else None
            
            if user_form.is_valid() and (not profile_form or profile_form.is_valid()):
                user_form.save()
                if profile_form:
                    profile_form.save()
                messages.success(request, "Personal profile updated successfully.")
                return redirect('settings')
        
        elif form_type == 'team' and managed_team:
            user_form = UserEditForm(instance=user, prefix='user')
            profile_form = StudentProfileForm(instance=student_profile, prefix='profile') if student_profile else None
            team_form = TeamSettingsForm(request.POST, request.FILES, instance=managed_team, prefix='team')
            
            if team_form.is_valid():
                team_form.save()
                messages.success(request, "Team settings updated successfully.")
                return redirect('settings')
        
        messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserEditForm(instance=user, prefix='user')
        profile_form = StudentProfileForm(instance=student_profile, prefix='profile') if student_profile else None
        team_form = TeamSettingsForm(instance=managed_team, prefix='team') if managed_team else None
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'team_form': team_form,
        'managed_team': managed_team,
    }
    return render(request, 'teams/settings.html', context)
