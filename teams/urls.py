from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.gallery_view, name='gallery'),
    path('hub/', views.dashboard_view, name='dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('guide/', views.guide_view, name='guide'),
    path('dev-dashboard/', views.dev_dashboard, name='dev_dashboard'),
    
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

    # Gallery actions
    path('submission/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('assignment/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignment/<int:pk>/grades/', views.view_grades, name='view_grades'),
    path('grade/<int:pk>/', views.grade_submission, name='grade_submission'),
    path('document/<int:pk>/delete/', views.delete_document, name='delete_document'),
]
