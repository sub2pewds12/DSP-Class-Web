from django.contrib import admin
from .models import Assignment, TeamSubmission, SubmissionFile, ClassDocument

class SubmissionFileInline(admin.TabularInline):
    model = SubmissionFile
    extra = 0

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'deadline', 'created_by', 'grades_released')
    list_filter = ('grades_released', 'deadline')
    search_fields = ('title', 'description')

@admin.register(TeamSubmission)
class TeamSubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'team', 'assignment', 'submitted_at', 'grade')
    list_filter = ('assignment', 'submitted_at')
    search_fields = ('title', 'team__name', 'assignment__title')
    inlines = [SubmissionFileInline]

@admin.register(ClassDocument)
class ClassDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'uploaded_by')
    search_fields = ('title',)
