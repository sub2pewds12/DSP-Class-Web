from django.contrib import admin
from .models import SystemSettings, SystemError

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('max_team_size',)

    def has_add_permission(self, request):
        if SystemSettings.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(SystemError)
class SystemErrorAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'message', 'is_resolved')
    list_filter = ('is_resolved',)
    search_fields = ('message', 'stack_trace', 'url')
