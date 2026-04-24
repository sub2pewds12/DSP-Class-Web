from django.db.models import Q
from apps.users.models import Student
from apps.academia.models import Assignment, TeamSubmission
from apps.teams.models import Team

class SearchService:
    @staticmethod
    def global_search(query: str):
        """
        Performs a comprehensive search across Students, Teams, and Assignments.
        Returns a dictionary of results grouped by type.
        """
        if not query or len(query) < 2:
            return {"students": [], "teams": [], "assignments": []}

        # Search Students
        students = Student.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(role__icontains=query)
        ).select_related('user', 'team').distinct()[:10]

        # Search Teams
        teams = Team.objects.filter(
            Q(name__icontains=query) |
            Q(project_name__icontains=query)
        ).select_related('leader__user').distinct()[:10]

        # Search Assignments
        assignments = Assignment.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).distinct()[:10]

        return {
            "students": [
                {
                    "id": s.id,
                    "name": s.user.get_full_name(),
                    "username": s.user.username,
                    "team": s.team.name if s.team else "No Team",
                    "team_id": s.team.id if s.team else None,
                    "role": s.role or "Member"
                } for s in students
            ],
            "teams": [
                {
                    "id": t.id,
                    "name": t.name,
                    "project": t.project_name or "TBD",
                    "leader": t.leader.user.get_full_name() if t.leader else "None"
                } for t in teams
            ],
            "assignments": [
                {
                    "id": a.id,
                    "title": a.title,
                    "deadline": a.deadline.strftime("%Y-%m-%d")
                } for a in assignments
            ]
        }
