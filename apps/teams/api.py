from ninja import NinjaAPI, Schema, File
from ninja.files import UploadedFile
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import PermissionDenied
import requests
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from apps.users.models import CustomUser, Student
from apps.core.models import SystemError
from apps.academia.models import Assignment, TeamSubmission, SubmissionFile, ClassDocument
from .models import Team
from apps.academia.services import SubmissionService, AssignmentService
from apps.users.services import UserService
from apps.core.utils.email_service import send_html_email

api = NinjaAPI(
    title="Smart Incident Hub & Academic API", 
    version="1.1.0",
    description="Interactive Explorer for all platform actions (Student, Lecturer, and Dev portals)."
)

# --- Common Schemas ---

class SuccessResponse(Schema):
    status: str
    message: str

class BulkResolveSchema(Schema):
    pattern: str

# --- Student Schemas ---

class ProjectUpdateSchema(Schema):
    project_name: str
    project_description: str

class RoleUpdateSchema(Schema):
    role: str

# --- Lecturer Schemas ---

class GradeUpdateSchema(Schema):
    grade: int
    feedback: str

class AssignmentSchema(Schema):
    title: str
    description: str
    deadline: str # Will parse to datetime

class DocumentSchema(Schema):
    title: str

# --- System & Incident Management (Dev) ---

@api.get("/health", tags=["System"])
def health_check_api(request):
    """Lighweight endpoint for external monitoring services."""
    return {"status": "OK", "message": "SYSTEM_OPERATIONAL"}

@api.post("/incident/{error_id}/resolve", response=SuccessResponse, tags=["Incidents"])
def resolve_incident(request, error_id: int):
    """Resolves a single incident by ID."""
    if getattr(request.user, 'role', '') != 'DEV':
        return 403, {"status": "error", "message": "Unauthorized"}
        
    error = get_object_or_404(SystemError, id=error_id)
    error.is_resolved = True
    error.save()
    return {"status": "success", "message": f"Incident {error_id} resolved."}

@api.post("/incident/bulk-resolve", response=SuccessResponse, tags=["Incidents"])
def bulk_resolve_incidents(request, data: BulkResolveSchema):
    """Resolves all unresolved incidents where the message contains the specified pattern."""
    if getattr(request.user, 'role', '') != 'DEV':
        return 403, {"status": "error", "message": "Unauthorized"}
        
    updated_count = SystemError.objects.filter(
        is_resolved=False, 
        message__icontains=data.pattern
    ).update(is_resolved=True)
    
    return {"status": "success", "message": f"Bulk resolved {updated_count} incidents matching '{data.pattern}'."}

@api.post("/incident/sanitize", response=SuccessResponse, tags=["Incidents"])
def sanitize_logs_api(request):
    """Automated log cleanup via concurrent URL probing."""
    if getattr(request.user, 'role', '') != 'DEV':
        return 403, {"status": "error", "message": "Unauthorized"}
        
    unresolved = list(SystemError.objects.filter(is_resolved=False).order_by('-timestamp')[:100])
    url_to_errors = {}
    for err in unresolved:
        if err.url:
            if err.url not in url_to_errors: url_to_errors[err.url] = []
            url_to_errors[err.url].append(err)
            
    if not url_to_errors:
        return {"status": "success", "message": "No unique URLs found in logs."}
        
    def check_url(url):
        try:
            resp = requests.get(request.build_absolute_uri(url), timeout=1.5, verify=False)
            if resp.status_code < 400: return url
        except: pass
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_url, url_to_errors.keys()))
        
    resolved_ids = [err.id for url in results if url for err in url_to_errors[url]]
    if resolved_ids:
        SystemError.objects.filter(id__in=resolved_ids).update(is_resolved=True)
                
    return {"status": "success", "message": f"Processed top 100. {len(resolved_ids)} incidents auto-resolved."}

# --- Student Actions ---

@api.post("/student/project-update", response=SuccessResponse, tags=["Student"])
def update_project_details(request, data: ProjectUpdateSchema):
    """Allows Team Leaders to update their project name and description."""
    student = get_object_or_404(Student, user=request.user)
    team = student.team
    if not team or team.leader != student:
        return 403, {"status": "error", "message": "Only the Team Leader can update project details."}
    
    team.project_name = data.project_name
    team.project_description = data.project_description
    team.save()
    return {"status": "success", "message": "Project details updated successfully."}

@api.post("/student/role-update", response=SuccessResponse, tags=["Student"])
def update_student_role(request, data: RoleUpdateSchema):
    """Update your role description within your team (e.g., 'Frontend Dev')."""
    student = get_object_or_404(Student, user=request.user)
    student.role = data.role
    student.save()
    return {"status": "success", "message": "Your role has been updated."}

@api.post("/student/submit-assignment", response=SuccessResponse, tags=["Student"])
def submit_assignment_api(request, assignment_id: int, files: List[UploadedFile] = File(...)):
    """
    Submits project files for an assignment. 
    Validation: Max 10 files, Max 50MB total, restrictive extensions.
    """
    student = get_object_or_404(Student, user=request.user)
    team = student.team
    if not team:
        return 403, {"status": "error", "message": "You must be in a team to submit assignments."}
        
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if not assignment.is_active:
        return 400, {"status": "error", "message": "Submissions are closed for this assignment."}
    
    # Validation logic
    if len(files) > 10:
        return 400, {"status": "error", "message": "Maximum of 10 files allowed."}
    
    total_size = sum(f.size for f in files)
    if total_size > 50 * 1024 * 1024:
        return 400, {"status": "error", "message": "Total file size exceeds 50MB limit."}
    
    allowed_exts = ['.pdf', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.png', '.jpg', '.jpeg', '.gif']
    for f in files:
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in allowed_exts:
            return 400, {"status": "error", "message": f"File type '{ext}' not allowed."}

    try:
        sub = SubmissionService.create_submission(
            user=request.user,
            assignment=assignment,
            title=f"Submission for {assignment.title}",
            files=files
        )
    except ValueError as e:
        return 400, {"status": "error", "message": str(e)}
    
    status = "on time"
    if sub.submitted_at and assignment.deadline and sub.submitted_at > assignment.deadline:
        status = "LATE"
        
    return {"status": "success", "message": f"Successfully submitted {len(files)} files ({status})."}

# --- Lecturer Actions ---

@api.post("/lecturer/create-assignment", response=SuccessResponse, tags=["Lecturer"])
def create_assignment_api(request, data: AssignmentSchema, instr_file: Optional[UploadedFile] = File(None)):
    """Create a new course assignment."""
    if request.user.role not in ['LECTURER', 'DEV']:
        return 403, {"status": "error", "message": "Unauthorized"}
    
    # Simple deadline parsing
    assign = AssignmentService.create_assignment(
        user=request.user,
        title=data.title,
        deadline=data.deadline,
        description=data.description,
        instruction_file=instr_file
    )
    return {"status": "success", "message": f"Assignment '{assign.title}' created."}

@api.post("/lecturer/upload-document", response=SuccessResponse, tags=["Lecturer"])
def upload_document_api(request, title: str, file: UploadedFile = File(...)):
    """Upload a new material for the class."""
    if request.user.role not in ['LECTURER', 'DEV']:
        return 403, {"status": "error", "message": "Unauthorized"}
    
    doc = AssignmentService.upload_document(
        user=request.user,
        title=title,
        file=file
    )
    return {"status": "success", "message": f"Document '{doc.title}' uploaded."}

@api.post("/lecturer/grade-submission/{sub_id}", response=SuccessResponse, tags=["Lecturer"])
def grade_submission_api(request, sub_id: int, data: GradeUpdateSchema):
    """Assign/Update a grade and feedback for a team submission."""
    if request.user.role not in ['LECTURER', 'DEV']:
        return 403, {"status": "error", "message": "Unauthorized"}
    
    submission = get_object_or_404(TeamSubmission, pk=sub_id)
    submission.grade = data.grade
    submission.feedback = data.feedback
    submission.save()
    
    return {"status": "success", "message": f"Grade updated for {submission.team.name}."}

@api.post("/lecturer/release-grades/{assign_id}", response=SuccessResponse, tags=["Lecturer"])
def release_grades_api(request, assign_id: int):
    """Release grades for an assignment, making them visible to students."""
    if request.user.role not in ['LECTURER', 'DEV']:
        return 403, {"status": "error", "message": "Unauthorized"}
    
    assignment = get_object_or_404(Assignment, pk=assign_id)
    assignment.grades_released = True
    assignment.save()
    
    return {"status": "success", "message": f"Grades released for '{assignment.title}'."}

@api.post("/lecturer/delete-document/{doc_id}", response=SuccessResponse, tags=["Lecturer"])
def delete_document_api(request, doc_id: int):
    """Permanently delete a class document."""
    if request.user.role not in ['LECTURER', 'DEV']:
        return 403, {"status": "error", "message": "Unauthorized"}
    
    doc = get_object_or_404(ClassDocument, pk=doc_id)
    title = doc.title
    doc.delete()
    return {"status": "success", "message": f"Document '{title}' deleted."}

# --- Dev Actions ---

@api.post("/dev/approve-user/{user_id}", response=SuccessResponse, tags=["Dev"])
def approve_user_api(request, user_id: int):
    """Approve a pending user registration and notify them via email."""
    if getattr(request.user, 'role', '') != 'DEV':
        return 403, {"status": "error", "message": "Unauthorized"}
        
    user = get_object_or_404(CustomUser, id=user_id)
    UserService.approve_user(user_id, request)
    return {"status": "success", "message": f"User '{user.get_full_name()}' approved."}

@api.post("/dev/deny-user/{user_id}", response=SuccessResponse, tags=["Dev"])
def deny_user_api(request, user_id: int):
    """Deny and delete a pending user registration."""
    if getattr(request.user, 'role', '') != 'DEV':
        return 403, {"status": "error", "message": "Unauthorized"}
        
    user = get_object_or_404(CustomUser, id=user_id)
    name = user.get_full_name()
    UserService.deny_user(user_id)
    return {"status": "success", "message": f"User '{name}' denied and removed."}

@api.get("/dev/supabase-status", tags=["Dev"])
def get_supabase_status(request):
    """Asynchronous heartbeat for the Supabase platform."""
    if getattr(request.user, 'role', '') != 'DEV':
        return 403, {"status": "error", "message": "Unauthorized"}
        
    from apps.core.supabase_service import SupabaseService
    return SupabaseService.check_connection()

# --- General Actions ---

@api.post("/submission/{sub_id}/delete", response=SuccessResponse, tags=["General"])
def delete_submission_api(request, sub_id: int):
    """Allows Team Leaders or Lecturers to remove a submission."""
    submission = get_object_or_404(TeamSubmission, pk=sub_id)
    
    is_leader = (hasattr(request.user, 'student_profile') and 
                 request.user.student_profile.team == submission.team and 
                 submission.team.leader == request.user.student_profile)
    
    if request.user.role in ['LECTURER', 'DEV'] or is_leader:
        title = submission.title
        submission.delete()
        return {"status": "success", "message": f"Submission '{title}' removed."}
    
    return 403, {"status": "error", "message": "Unauthorized to delete this submission."}
