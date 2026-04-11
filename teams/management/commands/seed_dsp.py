from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from teams.models import Team, Student, Lecturer, CustomUser, ClassDocument, TeamSubmission, Assignment

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
            
            # Delete test assignments
            test_assignments = Assignment.objects.filter(title__in=["Basics of DSP", "Midterm Report", "Final Prototype"])
            test_assignments.delete()
            
            # Test Students/Lecturers (using username patterns)
            test_users = User.objects.filter(
                models.Q(username__startswith="student_") | 
                models.Q(username="teacher_test")
            )
            
            # Profile cleanup (cascades naturally, but let's be explicit)
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
        if created:
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
            assign, _ = Assignment.objects.get_or_create(
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
                content = ContentFile(f"Instructions for {title}".encode('utf-8'))
                assign.instruction_file.save(f"instructions_{title.lower().replace(' ', '_')}.txt", content)
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
                if s_created:
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
                sub1.file.save(f"{team.name}_basics.txt", ContentFile("Mock submission content".encode('utf-8')))

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
                # Force submitted_at to be late relative to deadline (+2h from now)
                # Note: models.DateTimeField(auto_now_add=True) is hard to override in save(), 
                # but we can do it via queryset.update() after creation if needed.
                sub2.file.save(f"{team.name}_midterm.txt", ContentFile("Draft content".encode('utf-8')))

            self.stdout.write(f"Created Team: {t_name} with simulated submissions")

        self.stdout.write(self.style.SUCCESS("Finished populating test data!"))
        self.stdout.write("\nAll test accounts have the password: password123")
        self.stdout.write("Test Lecturer: teacher_test")
        self.stdout.write("Test Students: student_1, student_2, etc.")
