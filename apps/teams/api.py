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
from apps.core.services.audit_service import AuditService
from apps.core.services.search_service import SearchService
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

# --- Search Schemas ---

class SearchStudentSchema(Schema):
    id: int
    name: str
    username: str
    team: str
    team_id: Optional[int]
    role: str

class SearchTeamSchema(Schema):
    id: int
    name: str
    project: str
    leader: str

class SearchAssignmentSchema(Schema):
    id: int
    title: str
    deadline: str

class SearchResponse(Schema):
    students: List[SearchStudentSchema]
    teams: List[SearchTeamSchema]
    assignments: List[SearchAssignmentSchema]

# --- System & Incident Management (Dev) ---

@api.get("/health", tags=["System"])
def health_check_api(request):
    """Lighweight endpoint for external monitoring services."""
    return {"status": "OK", "message": "SYSTEM_OPERATIONAL"}



# --- Student Actions ---

@api.post("/student/project-update", response={200: SuccessResponse, 403: SuccessResponse}, tags=["Student"])
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

@api.post("/student/submit-assignment", response={200: SuccessResponse, 400: SuccessResponse, 403: SuccessResponse}, tags=["Student"])
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
        SubmissionService.create_submission(
            user=request.user,
            assignment=assignment,
            title=f"Submission for {assignment.title}",
            files=files
        )
    except ValueError as e:
        return 400, {"status": "error", "message": str(e)}
        
    return {"status": "success", "message": f"Successfully submitted {len(files)} files."}

# --- Lecturer Actions ---

@api.post("/lecturer/create-assignment", response={200: SuccessResponse, 403: SuccessResponse}, tags=["Lecturer"])
def create_assignment_api(request, data: AssignmentSchema, instr_file: Optional[UploadedFile] = File(None)):
    """Create a new course assignment."""
    if not getattr(request.user, 'can_manage_assignments', False):
        return 403, {"status": "error", "message": "Unauthorized: Requires Assignment Management permission."}
    
    # Simple deadline parsing
    assign = AssignmentService.create_assignment(
        user=request.user,
        title=data.title,
        deadline=data.deadline,
        description=data.description,
        instruction_file=instr_file
    )
    return {"status": "success", "message": f"Assignment '{assign.title}' created."}

@api.post("/lecturer/upload-document", response={200: SuccessResponse, 403: SuccessResponse}, tags=["Lecturer"])
def upload_document_api(request, title: str, file: UploadedFile = File(...)):
    """Upload a new material for the class."""
    if not getattr(request.user, 'can_manage_assignments', False):
        return 403, {"status": "error", "message": "Unauthorized: Requires Assignment Management permission."}
    
    doc = AssignmentService.upload_document(
        user=request.user,
        title=title,
        file=file
    )
    return {"status": "success", "message": f"Document '{doc.title}' uploaded."}

@api.post("/lecturer/grade-submission/{sub_id}", response={200: SuccessResponse, 403: SuccessResponse}, tags=["Lecturer"])
def grade_submission_api(request, sub_id: int, data: GradeUpdateSchema):
    """Assign/Update a grade and feedback for a team submission."""
    if not getattr(request.user, 'can_grade', False):
        return 403, {"status": "error", "message": "Unauthorized: Requires Grading permission."}
    
    submission = get_object_or_404(TeamSubmission, pk=sub_id)
    SubmissionService.grade_submission(
        submission=submission,
        grade=data.grade,
        feedback=data.feedback
    )
    
    return {"status": "success", "message": f"Grade updated for {submission.team.name}."}

@api.post("/lecturer/release-grades/{assign_id}", response={200: SuccessResponse, 403: SuccessResponse}, tags=["Lecturer"])
def release_grades_api(request, assign_id: int):
    """Release grades for an assignment, making them visible to students."""
    if not getattr(request.user, 'can_grade', False):
        return 403, {"status": "error", "message": "Unauthorized: Requires Grading permission."}
    
    assignment = get_object_or_404(Assignment, pk=assign_id)
    assignment.grades_released = True
    assignment.save()
    
    AuditService.log_event(
        action="GRADES_RELEASE",
        target_type="Assignment",
        target_id=str(assign_id),
        description=f"Grades released for assignment '{assignment.title}'."
    )
    
    return {"status": "success", "message": f"Grades released for '{assignment.title}'."}

@api.post("/lecturer/delete-document/{doc_id}", response={200: SuccessResponse, 403: SuccessResponse}, tags=["Lecturer"])
def delete_document_api(request, doc_id: int):
    """Permanently delete a class document."""
    if not getattr(request.user, 'can_manage_assignments', False):
        return 403, {"status": "error", "message": "Unauthorized: Requires Assignment Management permission."}
    
    doc = get_object_or_404(ClassDocument, pk=doc_id)
    title = doc.title
    doc.delete()
    return {"status": "success", "message": f"Document '{title}' deleted."}

# --- Dev Actions ---

@api.post("/dev/approve-user/{user_id}", response={200: SuccessResponse, 403: SuccessResponse}, tags=["Dev"])
def approve_user_api(request, user_id: int):
    """Approve a pending user registration and notify them via email."""
    if not getattr(request.user, 'can_manage_teams', False):
        return 403, {"status": "error", "message": "Unauthorized: Requires Team Management permission."}
        
    user = get_object_or_404(CustomUser, id=user_id)
    UserService.approve_user(user_id, request)
    
    return {"status": "success", "message": f"User '{user.get_full_name()}' approved."}

@api.post("/dev/deny-user/{user_id}", response={200: SuccessResponse, 403: SuccessResponse}, tags=["Dev"])
def deny_user_api(request, user_id: int):
    """Deny and delete a pending user registration."""
    if not getattr(request.user, 'can_manage_teams', False):
        return 403, {"status": "error", "message": "Unauthorized: Requires Team Management permission."}
        
    user = get_object_or_404(CustomUser, id=user_id)
    name = UserService.deny_user(user_id)
    
    return {"status": "success", "message": f"User '{name}' denied and removed."}

@api.get("/dev/supabase-status", response={200: dict, 403: SuccessResponse}, tags=["Dev"])
def get_supabase_status(request):
    """Asynchronous heartbeat for the Supabase platform."""
    if not getattr(request.user, 'can_manage_system', False):
        return 403, {"status": "error", "message": "Unauthorized: Requires System Management permission."}
        
    from apps.core.supabase_service import SupabaseService
    return SupabaseService.check_connection()

# --- General Actions ---

@api.post("/submission/{sub_id}/delete", response={200: SuccessResponse, 403: SuccessResponse}, tags=["General"])
def delete_submission_api(request, sub_id: int):
    """Allows Team Leaders or Lecturers to remove a submission."""
    submission = get_object_or_404(TeamSubmission, pk=sub_id)
    
    is_leader = (hasattr(request.user, 'student_profile') and 
                 request.user.student_profile.team == submission.team and 
                 submission.team.leader == request.user.student_profile)
    
    if getattr(request.user, 'can_manage_assignments', False) or is_leader:
        title = SubmissionService.delete_submission(submission, request.user)
        return {"status": "success", "message": f"Submission '{title}' removed."}
    
    return 403, {"status": "error", "message": "Unauthorized to delete this submission."}

@api.get("/search/global", response=SearchResponse, tags=["General"])
def global_search_api(request, q: str):
    """
    Universal search bar endpoint.
    Requires at least 2 characters.
    """
    if not q or len(q) < 2:
        return {"students": [], "teams": [], "assignments": []}
    
    return SearchService.global_search(q)
