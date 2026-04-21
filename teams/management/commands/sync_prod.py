from django.core.management.base import BaseCommand
from django.db import transaction
from teams.models import CustomUser, Team, Student, Lecturer, Assignment, TeamSubmission, SubmissionFile, ClassDocument
from apps.core.utils.backup_manager import BackupManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Syncs business data from production Postgres to local SQLite'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Ultra-Sync Engine..."))
        
        # 1. Backup local DB first
        backup_path = BackupManager.create_backup()
        if backup_path:
            self.stdout.write(self.style.SUCCESS(f"Pre-sync backup created: {backup_path}"))
            BackupManager.rotate_backups(days=90) # Clean up older than July
        
        try:
            with transaction.atomic():
                # 2. Sync Users (Ignoring Local Dev)
                self.stdout.write("Syncing Users...")
                prod_users = CustomUser.objects.using('production').exclude(email='sub2pewds10102005@gmail.com')
                for p_user in prod_users:
                    local_user, created = CustomUser.objects.update_or_create(
                        email=p_user.email,
                        defaults={
                            'username': p_user.username,
                            'first_name': p_user.first_name,
                            'last_name': p_user.last_name,
                            'role': p_user.role,
                            'is_staff': p_user.is_staff,
                            'is_active': p_user.is_active,
                            'password': p_user.password, # Sync hash directly
                        }
                    )

                # 3. Sync Teams
                self.stdout.write("Syncing Teams...")
                prod_teams = Team.objects.using('production').all()
                for p_team in prod_teams:
                    Team.objects.update_or_create(
                        id=p_team.id,
                        defaults={
                            'name': p_team.name,
                            'project_name': p_team.project_name,
                            'project_description': p_team.project_description,
                            'created_at': p_team.created_at,
                        }
                    )

                # 4. Sync Students
                self.stdout.write("Syncing Student Profiles...")
                prod_students = Student.objects.using('production').all()
                for p_student in prod_students:
                    # Resolve local user
                    try:
                        l_user = CustomUser.objects.get(email=p_student.user.email)
                        l_team = Team.objects.filter(id=p_student.team_id).first() if p_student.team_id else None
                        Student.objects.update_or_create(
                            id=p_student.id,
                            defaults={
                                'user': l_user,
                                'team': l_team,
                                'role': p_student.role,
                            }
                        )
                    except CustomUser.DoesNotExist:
                        continue

                # 5. Sync Lecturers
                self.stdout.write("Syncing Lecturer Profiles...")
                prod_lecturers = Lecturer.objects.using('production').all()
                for p_lecturer in prod_lecturers:
                    try:
                        l_user = CustomUser.objects.get(email=p_lecturer.user.email)
                        Lecturer.objects.update_or_create(
                            id=p_lecturer.id,
                            defaults={
                                'user': l_user,
                                'department': p_lecturer.department,
                            }
                        )
                    except CustomUser.DoesNotExist:
                        continue

                # 6. Sync Assignments
                self.stdout.write("Syncing Assignments...")
                prod_assignments = Assignment.objects.using('production').all()
                for p_assignment in prod_assignments:
                    try:
                        l_user = CustomUser.objects.get(email=p_assignment.created_by.email)
                        Assignment.objects.update_or_create(
                            id=p_assignment.id,
                            defaults={
                                'title': p_assignment.title,
                                'description': p_assignment.description,
                                'instruction_file': p_assignment.instruction_file,
                                'deadline': p_assignment.deadline,
                                'created_at': p_assignment.created_at,
                                'created_by': l_user,
                                'grades_released': p_assignment.grades_released,
                            }
                        )
                    except CustomUser.DoesNotExist:
                        continue

                # 7. Sync Submissions
                self.stdout.write("Syncing Submissions...")
                prod_submissions = TeamSubmission.objects.using('production').all()
                for p_sub in prod_submissions:
                    try:
                        l_team = Team.objects.get(id=p_sub.team.id)
                        l_user = CustomUser.objects.get(email=p_sub.submitted_by.email)
                        l_assignment = Assignment.objects.filter(id=p_sub.assignment_id).first()
                        TeamSubmission.objects.update_or_create(
                            id=p_sub.id,
                            defaults={
                                'team': l_team,
                                'assignment': l_assignment,
                                'title': p_sub.title,
                                'submitted_at': p_sub.submitted_at,
                                'submitted_by': l_user,
                                'grade': p_sub.grade,
                                'feedback': p_sub.feedback,
                            }
                        )
                    except (Team.DoesNotExist, CustomUser.DoesNotExist):
                        continue

                # 8. Sync Submission Files
                prod_files = SubmissionFile.objects.using('production').all()
                for p_file in prod_files:
                    try:
                        l_sub = TeamSubmission.objects.get(id=p_file.submission.id)
                        SubmissionFile.objects.update_or_create(
                            id=p_file.id,
                            defaults={
                                'submission': l_sub,
                                'file': p_file.file,
                                'uploaded_at': p_file.uploaded_at,
                            }
                        )
                    except TeamSubmission.DoesNotExist:
                        continue

                # 9. Sync Class Documents
                prod_docs = ClassDocument.objects.using('production').all()
                for p_doc in prod_docs:
                    try:
                        l_user = CustomUser.objects.get(email=p_doc.uploaded_by.email)
                        ClassDocument.objects.update_or_create(
                            id=p_doc.id,
                            defaults={
                                'title': p_doc.title,
                                'file': p_doc.file,
                                'uploaded_at': p_doc.uploaded_at,
                                'uploaded_by': l_user,
                            }
                        )
                    except CustomUser.DoesNotExist:
                        continue

            self.stdout.write(self.style.SUCCESS("Ultra-Sync Complete! Local data mirrored from production."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Sync Failed: {str(e)}"))
            raise e
