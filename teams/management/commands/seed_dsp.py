import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from teams.models import Team, Student, Lecturer, ClassDocument, TeamSubmission

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates or clears the DSP project registration database'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear all data instead of populating')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Clearing all data...")
            # Delete in order of dependencies
            TeamSubmission.objects.all().delete()
            ClassDocument.objects.all().delete()
            Lecturer.objects.all().delete()
            Student.objects.all().delete()
            Team.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()
            self.stdout.write(self.style.SUCCESS("Database cleared successfully!"))
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

        # 2. Create Teams
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
            
            self.stdout.write(f"Created Team: {t_name}")

        self.stdout.write(self.style.SUCCESS("Finished populating test data!"))
        self.stdout.write("\nAll test accounts have the password: password123")
        self.stdout.write("Test Lecturer: teacher_test")
        self.stdout.write("Test Students: student_1, student_2, etc.")
