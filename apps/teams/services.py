from django.db import transaction, IntegrityError
from .models import Team, Student, SystemSettings
from apps.core.services.audit_service import AuditService

class TeamService:
    """
    Handles team lifecycle, formation, and member management.
    """

    @staticmethod
    def join_or_create_team(student, team_choice=None, new_team_name=None):
        """
        Allows a student to either join an existing team or create a new one.
        
        Args:
            student: The Student profile instance.
            team_choice: An existing Team instance (optional).
            new_team_name: String name for a new team (optional).
            
        Returns:
            Team: The team instance joined or created.
            
        Raises:
            ValueError: If validation fails or team is full.
            IntegrityError: If team name is already taken.
        """
        if team_choice and new_team_name:
            raise ValueError("Specify either an existing team or a new team name, not both.")
        
        with transaction.atomic():
            if team_choice:
                # Joining existing team
                settings = SystemSettings.objects.first()
                max_size = settings.max_team_size if settings else 4
                
                if team_choice.members.count() >= max_size:
                    raise ValueError(f"Team '{team_choice.name}' is already at maximum capacity ({max_size}).")
                
                team = team_choice
            else:
                # Creating new team
                if not new_team_name:
                    raise ValueError("Team name is required for new team creation.")
                
                try:
                    team = Team.objects.create(name=new_team_name)
                except IntegrityError:
                    raise IntegrityError(f"Team name '{new_team_name}' is already taken.")
            
            # Associate student with team
            student.team = team
            student.save()
            
            # If student is the first member, they become leader
            if team.members.count() == 1:
                team.leader = student
                team.save()
                
            # Audit the event
            AuditService.log_event(
                action="TEAM_JOIN" if team_choice else "TEAM_CREATE",
                target_type="Team",
                target_id=str(team.id),
                description=f"Student '{student.user.get_full_name()}' {'joined' if team_choice else 'created'} team '{team.name}'.",
                metadata={"team_id": team.id, "is_leader": team.leader == student}
            )
            
            return team
