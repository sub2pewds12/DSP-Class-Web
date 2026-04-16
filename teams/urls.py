from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.gallery_view, name='gallery'),
    path('hub/', views.dashboard_view, name='dashboard'),
    path('hub/<int:team_id>/', views.dashboard_view, name='dashboard_with_team'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('guide/', views.guide_view, name='guide'),
    path('dev-dashboard/', views.dev_dashboard, name='dev_dashboard'),
    path('storage-analytics/', views.storage_analytics_view, name='storage_analytics'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
    path('user/<int:user_id>/approve/', views.approve_user, name='approve_user'),
    path('user/<int:user_id>/deny/', views.deny_user, name='deny_user'),
    path('health-check/', views.health_check, name='health_check'),
    
    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Built-in Password Reset for the Gmail "Set Initial Password" flow
    # These typically use standard templates at registration/password_reset_*
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Action endpoints
    path('submission/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('assignment/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignment/<int:pk>/grades/', views.view_grades, name='view_grades'),
    path('assignment/<int:pk>/release/', views.release_grades, name='release_grades'),
    path('grade/<int:pk>/', views.grade_submission, name='grade_submission'),
    path('document/<int:pk>/delete/', views.delete_document, name='delete_document'),
    path('submission/<int:pk>/delete/', views.delete_submission, name='delete_submission'),
    
    # Incident Logic
    path('incident/<int:pk>/resolve/', views.resolve_error, name='resolve_error'),
    path('incident/bulk-resolve/', views.bulk_resolve_errors, name='bulk_resolve_errors'),
    path('incident/sanitize/', views.sanitize_logs, name='sanitize_logs'),
]
