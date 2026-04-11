from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('gallery/', views.gallery_view, name='gallery'),
    
    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Built-in Password Reset for the Gmail "Set Initial Password" flow
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    
    # Document Management
    path('document/delete/<int:pk>/', views.delete_document, name='delete_document'),
    path('submission/delete/<int:pk>/', views.delete_submission, name='delete_submission'),
]
