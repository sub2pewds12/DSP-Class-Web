from django.urls import path
from django.contrib.auth import views as auth_views
from django_ratelimit.decorators import ratelimit
from django.views.generic import RedirectView
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
    path('settings/', views.settings_view, name='settings'),
    path('health-check/', views.health_check, name='health_check'),
    
    # Legacy Redirects (Fixes old log errors)
    path('dev/dashboard/', RedirectView.as_view(url='/dev-dashboard/', permanent=True)),
    path('gallery/', RedirectView.as_view(url='/', permanent=True)),
    
    # Auth
    path('signup/', ratelimit(key='ip', rate='3/m', block=True)(views.signup_view), name='signup'),
    path('login/', ratelimit(key='ip', rate='5/m', block=True)(auth_views.LoginView.as_view(template_name='teams/registration/login.html', redirect_authenticated_user=True)), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Built-in Password Reset for the Gmail "Set Initial Password" flow
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='teams/registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='teams/registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='teams/registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='teams/registration/password_reset_complete.html'), name='password_reset_complete'),
    
    # Password Change
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='teams/registration/password_change_form.html', success_url='/settings/'), name='password_change'),

    # Action endpoints
    path('submission/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('assignment/<int:pk>/grades/', views.view_grades, name='view_grades'),
    path('submission/<int:pk>/delete/', views.delete_submission, name='delete_submission'),
    path('submission/<int:pk>/grade/', views.grade_submission, name='grade_submission'),
    path('assignment/<int:pk>/release/', views.release_grades, name='release_grades'),
    path('document/upload/', ratelimit(key='ip', rate='10/m', block=True)(views.upload_document), name='upload_document'),
    
]
