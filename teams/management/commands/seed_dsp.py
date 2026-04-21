from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from teams.models import Team
from apps.users.models import Student, Lecturer, CustomUser
from apps.academia.models import ClassDocument, TeamSubmission, Assignment

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates or clears the DSP project registration database'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear all data instead of populating')

    def handle(self, *args, **options):
        test_team_names = ["Cyber Shadows", "Robo Pulse", "Signal Sentinels"]
        
        if options['clear']:
            self.stdout.write("Surgically removing ONLY test data...")
            
            # Find the test teams
            test_teams = Team.objects.filter(name__in=test_team_names)
            
            # Submissions for those teams
            TeamSubmission.objects.filter(team__in=test_teams).delete()
            
            # Test Users
            test_users = User.objects.filter(
                models.Q(username__startswith="student_") | 
                models.Q(username="teacher_test")
            )

            # Delete ALL assignments created by the test teacher
            Assignment.objects.filter(created_by__in=test_users).delete()
            
            # Profile cleanup
            Student.objects.filter(user__in=test_users).delete()
            Lecturer.objects.filter(user__in=test_users).delete()
            
            # Delete teams and users
            test_teams.delete()
            test_users.delete()
            
            self.stdout.write(self.style.SUCCESS("Test data removed. Your real data remains untouched!"))
            return

        self.stdout.write("Populating database with test data...")

        # 1. Create a Test Lecturer
        lecturer_user, created = User.objects.get_or_create(
            username="teacher_test",
            defaults={
                "email": "teacher@test.com",
                "role": "LECTURER",
                "first_name": "Dr.",
                "last_name": "Professor"
            }
        )
        lecturer_user.set_password("password123")
        lecturer_user.save()
        Lecturer.objects.get_or_create(user=lecturer_user, department="DSP Engineering")
        
        lecturer_profile = lecturer_user.lecturer_profile

        # 2. Create Assignments (Past, Present, Future)
        now = timezone.now()
        assignments_data = [
            ("Basics of DSP", "Exercise on signal convolution.", now - timedelta(days=7), True),
            ("Midterm Report", "Analysis of real-time signals.", now + timedelta(hours=2), False),
            ("Final Prototype", "Working hardware demonstration.", now + timedelta(days=60), False),
        ]
        
        created_assignments = []
        for title, desc, deadline, released in assignments_data:
            assign, _ = Assignment.objects.update_or_create(
                title=title,
                defaults={
                    "description": desc,
                    "deadline": deadline,
                    "created_by": lecturer_user,
                    "grades_released": released
                }
            )
            # Add mock instruction file
            if not assign.instruction_file:
                try:
                    content = ContentFile(f"Instructions for {title}".encode('utf-8'))
                    assign.instruction_file.save(f"instructions_{title.lower().replace(' ', '_')}.txt", content)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping instruction file for {title}: {str(e)}"))
            created_assignments.append(assign)

        # 3. Create Teams and Simulating Submissions
        teams_data = [
            ("Cyber Shadows", "Real-time Encryption Algorithm", "Developing a high-speed DSP based encryption"),
            ("Robo Pulse", "Autonomous Drone Navigation", "Using Fourier transforms for signal processing in drone sensors"),
            ("Signal Sentinels", "Weather Forecast Radar", "Filtering noise from satellite weather data")
        ]

        roles = ["Team Leader", "Software Engineer", "Systems Architect", "Documentation Lead"]
        
        student_count = 1
        for t_name, proj_name, proj_desc in teams_data:
            team, _ = Team.objects.get_or_create(
                name=t_name,
                defaults={
                    "project_name": proj_name,
                    "project_description": proj_desc
                }
            )
            
            # Create 4 students for each team
            for i in range(4):
                s_user, s_created = User.objects.get_or_create(
                    username=f"student_{student_count}",
                    defaults={
                        "email": f"student{student_count}@uni.edu",
                        "role": "STUDENT",
                        "first_name": f"Student",
                        "last_name": f"Number {student_count}"
                    }
                )
                s_user.set_password("password123")
                s_user.save()
                
                student, _ = Student.objects.get_or_create(user=s_user)
                student.team = team
                student.role = roles[i % len(roles)]
                student.save()
                
                # Assign first student as leader
                if i == 0:
                    team.leader = student
                    team.save()

                student_count += 1
            
            # Simulating Submissions for this team
            # 1. Past assignment (Graded)
            sub1, s_created = TeamSubmission.objects.get_or_create(
                team=team, 
                assignment=created_assignments[0],
                defaults={
                    "title": "Module 1 Submission",
                    "submitted_by": team.leader.user,
                    "grade": 95,
                    "feedback": "Perfect signal filtering logic. Well documented."
                }
            )
            if s_created:
                try:
                    sub1.file.save(f"{team.name}_basics.txt", ContentFile("Mock submission content".encode('utf-8')))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping submission file 1 for {team.name}: {str(e)}"))

            # 2. Midterm (Late)
            sub2, s_created = TeamSubmission.objects.get_or_create(
                team=team,
                assignment=created_assignments[1],
                defaults={
                    "title": "Midterm Draft",
                    "submitted_by": team.leader.user,
                }
            )
            if s_created:
                try:
                    sub2.file.save(f"{team.name}_midterm.txt", ContentFile("Draft content".encode('utf-8')))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipping submission file 2 for {team.name}: {str(e)}"))

            self.stdout.write(f"Created Team: {t_name} with simulated submissions")

        self.stdout.write(self.style.SUCCESS("Finished populating test data!"))
        self.stdout.write("\nAll test accounts have the password: password123")
        self.stdout.write("Test Lecturer: teacher_test")
        self.stdout.write("Test Students: student_1, student_2, etc.")
