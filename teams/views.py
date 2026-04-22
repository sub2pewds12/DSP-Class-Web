from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import requests

def health_check(request):
    """Lighweight endpoint for external monitoring services."""
    return HttpResponse("SYSTEM_OPERATIONAL", status=200)
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
import math, platform, sys, django, threading
from .models import Student, Team, Lecturer, CustomUser, ClassDocument, TeamSubmission, Assignment, SystemSettings
from apps.core.utils.email_service import send_html_email
from apps.users.forms import UserRegistrationForm, StudentRoleForm
from apps.academia.forms import (
    DocumentUploadForm, AssignmentForm, AssignmentSubmissionForm, 
    GradeSubmissionForm, TeamRegistrationForm, TeamProjectForm
)
from apps.academia.services import SubmissionService, AssignmentService
from apps.users.services import UserService
from apps.core.services import InfrastructureService


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
                team_choice = form.cleaned_data['team_choice']
                if team_choice: team = team_choice
                else: team = Team.objects.create(name=form.cleaned_data['new_team_name'])
                
                student.team = team
                student.save()
                if team.members.count() == 1:
                    team.leader = student
                    team.save()
                messages.success(request, f"Joined {team.name}")
                return redirect('dashboard')

    # Prepare Context
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    assignments = Assignment.objects.all().order_by('-deadline')

    if team:
        for a in assignments:
            a.team_submission = team.submissions.filter(assignment=a).order_by('-submitted_at').first()
            a.is_late = a.team_submission.is_late if a.team_submission else False
            
        return render(request, 'teams/dashboard.html', {
            'student': student,
            'team': team,
            'documents': documents,
            'assignments': assignments,
            'project_form': TeamProjectForm(instance=team),
            'role_form': StudentRoleForm(instance=student),
            'assign_form': AssignmentSubmissionForm(),
            'is_read_only': is_read_only
        })

    return render(request, 'teams/register.html', {
        'form': TeamRegistrationForm(),
        'documents': documents
    })

def guide_view(request):
    return render(request, 'teams/guide.html')

@login_required
def teacher_dashboard(request):
    if not getattr(request.user, 'is_approved', False):
        return redirect('pending_approval')
        
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
    
    # Ensure lecturer profile exists
    Lecturer.objects.get_or_create(user=request.user)
    
    # Prefetch with safer logic
    teams = Team.objects.prefetch_related(
        'members__user', 
        'submissions__assignment',
        'submissions__files'
    ).all().order_by('name')
    
    documents = ClassDocument.objects.all().order_by('-uploaded_at')
    assignments = Assignment.objects.all().order_by('-deadline')
    
    # Offload status mapping logic to service
    teams = AssignmentService.get_team_status_matrix(teams, assignments)

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

@login_required
def grade_submission(request, pk):
    if request.user.role not in ['LECTURER', 'DEV']:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    
    submission = get_object_or_404(TeamSubmission, pk=pk)
    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST)
        if form.is_valid():
            submission.grade = form.cleaned_data['grade']
            submission.feedback = form.cleaned_data['feedback']
            submission.save()
            messages.success(request, f"Submission for {submission.team.name} graded.")
    return redirect('teacher_dashboard')

@login_required
def release_grades(request, pk):
    if request.user.role not in ['LECTURER', 'DEV']:
        return redirect('dashboard')
    
    assignment = get_object_or_404(Assignment, pk=pk)
    assignment.grades_released = True
    assignment.save()
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
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def dev_dashboard(request):
    if not getattr(request.user, 'is_approved', False):
        return redirect('pending_approval')
        
    if request.user.role != 'DEV':
        return redirect('dashboard')
    
    from django.db.models import Count, Q
    from django.db.models.functions import TruncDate
    from django.db import connection, OperationalError
    from django.conf import settings
    from .models import SystemPulse, SystemError
    from django.core.management import call_command
    from django.core.cache import cache
    import platform
    import sys
    import django
    import time
    import os
    import threading

    # --- Ultra-Sync Trigger ---
    sync_status = "idle"
    if os.getenv('PROD_DB_URL'):
        # Only check/sync every 5 minutes to avoid overloading production
        last_sync = cache.get('last_prod_sync_time')
        now = timezone.now()
        
        if not last_sync or (now - last_sync).total_seconds() > 300:
            def run_sync():
                try:
                    call_command('sync_prod')
                    cache.set('last_prod_sync_time', timezone.now(), 3600)
                    cache.set('last_sync_result', 'success', 3600)
                except Exception as e:
                    cache.set('last_sync_result', f'failed: {str(e)}', 3600)

            threading.Thread(target=run_sync, daemon=True).start()
            sync_status = "syncing"
        else:
            sync_status = cache.get('last_sync_result', 'idle')

    # --- Pulse & Monitoring Logic (READ-ONLY) ---
    last_pulse = SystemPulse.objects.first()

    # Offload Analytics to Core Service
    analytics = InfrastructureService.get_system_analytics(pulses_window=100)
    
    pulses_history = analytics['pulses']
    graph_pulses = list(reversed(pulses_history)) 
    recent_p = pulses_history # For histogram logic
    advanced_insights = analytics['insights']
    health_score = analytics['health']
    momentum = analytics['momentum']
    severity = analytics['severity']
    analysis_msg = analytics['message']
    
    system_analysis = {
        'message': analysis_msg,
        'score': int(health_score),
        'severity': severity,
        'momentum': momentum,
        'volatility': f"{analytics['volatility']:.1f}ms",
        'consistency': f"{analytics['consistency']:.0f}%",
        'insights': advanced_insights[:3] 
    }
    
    # Rolling Uptime Calculation (Last 100 pulses in current cycle)
    total_p_window = len(recent_p)
    up_p_window = len([p for p in recent_p if p.status in ['OPERATIONAL', 'WARNING']])
    uptime_pct = (up_p_window / total_p_window * 100) if total_p_window > 0 else 100

    # Normalization for Logarithmic Histogram UI
    window_max_latency = max([p.latency for p in recent_p] + [800]) 
    # Use log10(val + 1) to handle 0ms latencies safely
    log_max_latency = math.log10(window_max_latency + 1)
    
    # Log-calibrated Y-Axis benchmarks (Powers of 10)
    log_benchmarks = [
        {'label': f"{int(window_max_latency)}ms", 'pos': 100},
        {'label': "100ms", 'pos': (math.log10(100+1) / log_max_latency * 100) if log_max_latency > 2 else 50},
        {'label': "10ms", 'pos': (math.log10(10+1) / log_max_latency * 100) if log_max_latency > 1 else 10},
        {'label': "0ms", 'pos': 0}
    ]

    # Pre-calculate logarithmic heights for template rendering
    for p in recent_p:
        if p.status == 'DOWN':
            p.log_h = 100
        else:
            # log10(val+1) provides a safe lower bound for UI visibility
            p.log_h = (math.log10(p.latency + 1) / log_max_latency) * 100

    # Formatting for Chart.js
    pulse_labels = []
    pulse_data = []

    # System Errors
    show_archive = request.GET.get('archive') == '1'
    if show_archive:
        system_errors = SystemError.objects.filter(is_resolved=True).order_by('-timestamp')[:50]
    else:
        system_errors = SystemError.objects.filter(is_resolved=False).order_by('-timestamp')[:20]
        
    unresolved_count = SystemError.objects.filter(is_resolved=False).count()

    from apps.core.supabase_service import SupabaseService
    supabase_status = SupabaseService.check_connection()

    # 1. System Infrastructure Portals
    portals = {
        'admin': '/admin/',
        'render': 'https://dashboard.render.com',
        'cloudinary': f"https://cloudinary.com/console/cloud/{settings.CLOUDINARY_STORAGE['CLOUD_NAME']}/media_library",
        'openapi': '/api/openapi.json',
        'uptime_status': 'https://stats.uptimerobot.com/eX7GdUhav0',
        'uptime_dashboard': 'https://dashboard.uptimerobot.com/monitors',
    }

    # 2. Optimized DB Telemetry
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
        'db_status': 'Connected' if last_pulse and last_pulse.status != 'DOWN' else 'Unknown'
    }

    # 3. Submission Trends
    last_14_days = timezone.now() - timezone.timedelta(days=14)
    submission_trends = TeamSubmission.objects.filter(submitted_at__gte=last_14_days).annotate(date=TruncDate('submitted_at')).values('date').annotate(count=Count('id')).order_by('date')
    trend_labels = [s['date'].strftime('%b %d') for s in submission_trends]
    trend_data = [s['count'] for s in submission_trends]

    # ... other stats ...

    roles = CustomUser.objects.values('role').annotate(count=Count('id'))
    role_labels = [r['role'] for r in roles]
    role_data = [r['count'] for r in roles]

    sys_info = {
        'os': platform.system(),
        'os_release': platform.release(),
        'python_version': sys.version.split(' ')[0],
        'django_version': django.get_version(),
        'uptime_pct': f"{uptime_pct:.1f}%",
        'unresolved_errors': unresolved_count,
        'teams_count': Team.objects.count(),
        'students_count': Student.objects.count(),
        'submissions_count': TeamSubmission.objects.count(),
        'docs_count': ClassDocument.objects.count(),
    }

    recent_activity = TeamSubmission.objects.select_related('team', 'submitted_by').all().order_by('-submitted_at')[:15]

    # Fetch pending access requests
    pending_users = CustomUser.objects.filter(is_approved=False).order_by('-date_joined')

    return render(request, 'teams/dev_dashboard.html', {
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'role_labels': role_labels,
        'role_data': role_data,
        'sys_info': sys_info,
        'recent_activity': recent_activity,
        'settings': SystemSettings.objects.first(),
        'portals': portals,
        'db_telemetry': db_telemetry,
        'pulses': pulses_history,
        'pulse_labels': pulse_labels,
        'pulse_data': pulse_data,
        'window_max_latency': window_max_latency,
        'log_max_latency': log_max_latency,
        'log_benchmarks': log_benchmarks,
        'system_errors': system_errors,
        'show_archive': show_archive,
        'supabase_status': supabase_status,
        'sync_status': sync_status,
        'current_status': last_pulse.status if last_pulse else 'UNKNOWN',
        'system_analysis': system_analysis,
        'pending_users': pending_users
    })

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
        
    from .models import ClassDocument, TeamSubmission, SubmissionFile, Assignment
    from django.conf import settings
    import cloudinary.api
    import os
    
    # Configure Cloudinary
    os.environ['CLOUDINARY_URL'] = f"cloudinary://{settings.CLOUDINARY_STORAGE['API_KEY']}:{settings.CLOUDINARY_STORAGE['API_SECRET']}@{settings.CLOUDINARY_STORAGE['CLOUD_NAME']}"
    
    storage_stats = {
        'total_files': 0,
        'breakdown': {'Images': 0, 'Documents': 0, 'Others': 0},
        'usage': {'used': 0, 'limit': 1000, 'pct': 0},
        'bandwidth': {'used': 0, 'limit': 1000, 'pct': 0},
        'resources': 0,
        'plan': 'N/A'
    }
    
    # 1. Fetch Cloudinary SDK Stats
    try:
        usage = cloudinary.api.usage()
        storage_stats['plan'] = usage.get('plan', 'Cloudinary Free')
        
        # Storage (Convert to MB/GB if needed, assuming bytes for now)
        storage = usage.get('storage', {})
        storage_stats['usage']['used'] = round(storage.get('usage', 0) / (1024 * 1024), 2) # MB
        storage_stats['usage']['limit'] = round(storage.get('limit', 0) / (1024 * 1024), 2) # MB
        storage_stats['usage']['pct'] = storage.get('used_percent', 0)
        
        # Bandwidth
        bandwidth = usage.get('bandwidth', {})
        storage_stats['bandwidth']['used'] = round(bandwidth.get('usage', 0) / (1024 * 1024), 2) # MB
        storage_stats['bandwidth']['limit'] = round(bandwidth.get('limit', 0) / (1024 * 1024), 2) # MB
        storage_stats['bandwidth']['pct'] = bandwidth.get('used_percent', 0)
        
        storage_stats['resources'] = usage.get('resources', 0)
    except Exception as e:
        # Graceful failure - log error but keep moving
        pass
        
    # 2. Local Database Overlay
    doc_count = ClassDocument.objects.count()
    sub_count = SubmissionFile.objects.count()
    assign_count = Assignment.objects.exclude(instruction_file='').count()
    storage_stats['total_files'] = doc_count + sub_count + assign_count
    
    # 3. Recent Assets
    recent_docs = ClassDocument.objects.order_by('-uploaded_at')[:5]
    recent_subs = SubmissionFile.objects.select_related('submission__team').order_by('-uploaded_at')[:5]
    
    # 4. External Portal URL (Direct to Media Library)
    cloudinary_portal = f"https://cloudinary.com/console/cloud/{settings.CLOUDINARY_STORAGE['CLOUD_NAME']}/media_library"
    
    return render(request, 'teams/storage_analytics.html', {
        'stats': storage_stats,
        'recent_docs': recent_docs,
        'recent_subs': recent_subs,
        'cloudinary_portal': cloudinary_portal
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
    return render(request, 'registration/pending_approval.html')
