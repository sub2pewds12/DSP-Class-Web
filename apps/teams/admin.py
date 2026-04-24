from django.contrib import admin
from .models import Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_name', 'member_count', 'created_at')
    search_fields = ('name', 'project_name')

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Member Count'
