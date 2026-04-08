from django.contrib import admin
from .models import SystemSettings, Team, Student

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('max_team_size',)

    def has_add_permission(self, request):
        if SystemSettings.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'member_count', 'created_at')

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Member Count'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'team')
    list_filter = ('team',)
