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
from .utils.email_service import send_html_email
from .forms import (
    TeamRegistrationForm, UserRegistrationForm, DocumentUploadForm, 
    TeamProjectForm, StudentRoleForm, AssignmentForm, AssignmentSubmissionForm,
    GradeSubmissionForm
)


@login_required
def dashboard_view(request, team_id=None):
    if not getattr(request.user, 'is_approved', False):
        return redirect('pending_approval')
        
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

    if team:
        if not team.leader and team.members.exists():
            # Auto-assign first member as leader if missing
            team.leader = team.members.first()
            team.save()

        # Forms (only for members with appropriate permissions)
        project_form = TeamProjectForm(instance=team)
        role_form = StudentRoleForm(instance=student)
        assign_form = AssignmentSubmissionForm()

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
            
            # Extract role and set approval state
            role = form.cleaned_data.get('role', 'STUDENT')
            user.role = role
            if role == 'STUDENT':
                user.is_approved = True
            else:
                user.is_approved = False
                
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            
            # Handle Student Auto-Approval
            if role == 'STUDENT':
                Student.objects.get_or_create(user=user)
                login(request, user, backend='teams.backends.CaseInsensitiveModelBackend')
                messages.success(request, f"Welcome, {user.first_name}! Your account has been created successfully.")
                return redirect('dashboard')
            
            # Handle Staff/Dev Registration (Requires Approval)
            if role == 'DEV':
                from .models import Developer
                Developer.objects.get_or_create(user=user)
            else:
                Lecturer.objects.get_or_create(user=user)
            
            # Trigger Admin Notification
            send_html_email(
                subject=f"Access Request: {role} - {user.get_full_name()}",
                template_name='teams/emails/admin_request.html',
                context={
                    'user_name': user.get_full_name(),
                    'user_email': user.email,
                    'requested_role': role,
                    'dashboard_url': request.build_absolute_uri('/dev-dashboard/')
                },
                recipient_list=['sub2pewds10102005@gmail.com']
            )
            
            messages.info(request, f"Registration submitted. An administrator must approve your {role.lower()} access.")
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

    # Fetch Data for UI (Sync to 100-pulse window)
    pulses_history = SystemPulse.objects.all()[:100]
    # For Chart.js - latest 100 in chronological order
    graph_pulses = list(reversed(SystemPulse.objects.all()[:100]))
    
    # --- Advanced Infrastructure Analytics Engine ---
    recent_p = list(pulses_history)
    advanced_insights = []
    health_score = 100
    severity = "success"
    
    if recent_p:
        # 1. Volatility Index (Jitter Detection)
        latencies = [p.latency for p in recent_p]
        jitters = [abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))]
        avg_volatility = sum(jitters) / len(jitters) if jitters else 0
        
        # 2. Consistency Index (Percentile Benchmarking)
        # Using 500ms as a fixed "High Performance" threshold for this academic context
        consistent_pulses = len([p for p in recent_p if p.latency < 500 and p.status != 'DOWN'])
        consistency_pct = (consistent_pulses / len(recent_p)) * 100
        
        # 3. Performance Momentum (Trend: Last 20 vs Previous 80)
        current_window = latencies[:20]
        baseline_window = latencies[20:100]
        curr_avg = sum(current_window)/len(current_window) if current_window else 0
        base_avg = sum(baseline_window)/len(baseline_window) if baseline_window else 0
        momentum = "STABLE"
        if curr_avg < base_avg * 0.9: momentum = "IMPROVING"
        elif curr_avg > base_avg * 1.1: momentum = "DEGRADING"
        
        # 4. Friction Analysis (Error Hotspots)
        from django.db.models import Count
        hotspot = SystemError.objects.values('url').annotate(count=Count('id')).order_by('-count').first()
        
        # Synthesis
        if avg_volatility > 200:
            advanced_insights.append({"type": "volatility", "label": "High Volatility", "text": f"Response jitter is elevated ({avg_volatility:.1f}ms). Connection quality is inconsistent.", "icon": "bi-reception-2"})
        else:
            advanced_insights.append({"type": "volatility", "label": "Signal Stable", "text": "Latency variance is within nominal limits. Signal consistency is high.", "icon": "bi-reception-4 text-success"})

        if consistency_pct < 90:
            advanced_insights.append({"type": "consistency", "label": "Consistency Drop", "text": f"System fell below performance baseline for {100-consistency_pct:.0f}% of recent cycles.", "icon": "bi-activity text-warning"})
        
        if hotspot and hotspot['count'] > 2:
            advanced_insights.append({"type": "friction", "label": "Service Friction", "text": f"Recurrent failures detected on endpoint: {hotspot['url']}. Potential logic bottleneck.", "icon": "bi-exclamation-octagon text-danger"})
            health_score -= 15

        # Final Scoring logic
        health_score -= (avg_volatility / 50)  # Volatility penalty
        health_score -= (100 - consistency_pct) # Consistency penalty
        if momentum == "DEGRADING": health_score -= 10
        health_score = max(5, min(100, health_score))
        
        if health_score < 70: severity = "warning"
        if health_score < 40 or any(p.status == 'DOWN' for p in recent_p[:5]): severity = "danger"

        # Predictive Insight
        if momentum == "DEGRADING" and health_score < 80:
            analysis_msg = "Degradation trend detected. System consistency is decreasing; resource scaling or error audit recommended."
        elif health_score > 90:
            analysis_msg = "Infrastructure is operating at peak efficiency with negligible friction and high signal consistency."
        else:
            analysis_msg = "System is operational with moderate data-flow variance. No immediate critical interventions required."

    system_analysis = {
        'message': analysis_msg if recent_p else "Collecting telemetry...",
        'score': int(health_score),
        'severity': severity,
        'momentum': momentum,
        'volatility': f"{avg_volatility:.1f}ms",
        'consistency': f"{consistency_pct:.0f}%",
        'insights': advanced_insights[:3] # Show top 3
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
    system_errors = SystemError.objects.all()[:15]
    unresolved_count = SystemError.objects.filter(is_resolved=False).count()

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
