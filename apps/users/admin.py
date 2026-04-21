from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Student, Lecturer, Developer

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_approved', 'is_staff')
    list_filter = ('role', 'is_approved', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Account Status', {'fields': ('role', 'is_approved')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Account Status', {'fields': ('role', 'is_approved')}),
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_email', 'team', 'role')
    list_filter = ('team', 'role')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'department')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'department')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'github_username')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
