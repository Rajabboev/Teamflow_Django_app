from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Profile, Team, Tag, Task, Feedback


User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo data for Teamflow (users, teams, tasks, feedback)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # Users and profiles
        users_definitions = [
            ("lead1", "lead1@example.com", "team_lead"),
            ("lead2", "lead2@example.com", "team_lead"),
            ("member1", "member1@example.com", "member"),
            ("member2", "member2@example.com", "member"),
        ]

        users = {}
        for username, email, role in users_definitions:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email},
            )
            if created:
                user.set_password("password123")
                user.save()
            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={"role": role},
            )
            if profile.role != role:
                profile.role = role
                profile.save()
            users[username] = user

        # Tags
        tag_defs = [
            ("Bug", "#dc3545"),
            ("Feature", "#0d6efd"),
            ("Urgent", "#ffc107"),
        ]
        tags = {}
        for name, color in tag_defs:
            tag, _ = Tag.objects.get_or_create(name=name, defaults={"color": color})
            # keep color updated if it changed
            if tag.color != color:
                tag.color = color
                tag.save()
            tags[name] = tag

        # Teams
        backend_team, _ = Team.objects.get_or_create(
            name="Backend Team",
            defaults={
                "description": "Handles APIs and data processing.",
                "created_by": users["lead1"],
            },
        )
        backend_team.members.add(
            users["lead1"],
            users["member1"],
        )

        frontend_team, _ = Team.objects.get_or_create(
            name="Frontend Team",
            defaults={
                "description": "Owns UI/UX and client-side logic.",
                "created_by": users["lead2"],
            },
        )
        frontend_team.members.add(
            users["lead2"],
            users["member2"],
        )

        now = timezone.now()

        # Tasks
        t1, _ = Task.objects.get_or_create(
            title="Fix login bug",
            team=backend_team,
            defaults={
                "description": "Users cannot log in with correct credentials.",
                "assigned_to": users["member1"],
                "created_by": users["lead1"],
                "status": "in_progress",
                "priority": "high",
                "deadline": now + timedelta(days=1),
            },
        )
        t1.tags.set([tags["Bug"], tags["Urgent"]])

        t2, _ = Task.objects.get_or_create(
            title="Add password reset flow",
            team=backend_team,
            defaults={
                "description": "Implement password reset using email token.",
                "assigned_to": users["member1"],
                "created_by": users["lead1"],
                "status": "todo",
                "priority": "medium",
                "deadline": now + timedelta(days=3),
            },
        )
        t2.tags.set([tags["Feature"]])

        t3, _ = Task.objects.get_or_create(
            title="Redesign dashboard",
            team=frontend_team,
            defaults={
                "description": "Modernize dashboard and improve usability.",
                "assigned_to": users["member2"],
                "created_by": users["lead2"],
                "status": "todo",
                "priority": "medium",
                "deadline": now + timedelta(days=5),
            },
        )
        t3.tags.set([tags["Feature"]])

        t4, _ = Task.objects.get_or_create(
            title="Fix broken avatar upload",
            team=frontend_team,
            defaults={
                "description": "Avatar uploads fail for large images.",
                "assigned_to": users["member2"],
                "created_by": users["lead2"],
                "status": "todo",
                "priority": "high",
                "deadline": now - timedelta(days=1),  # overdue
            },
        )
        t4.tags.set([tags["Bug"], tags["Urgent"]])

        # Feedback
        Feedback.objects.get_or_create(
            task=t1,
            author=users["lead1"],
            defaults={
                "content": "Investigated root cause, working on fix.",
                "rating": 4,
            },
        )
        Feedback.objects.get_or_create(
            task=t3,
            author=users["lead2"],
            defaults={
                "content": "Initial mockups look good, focus on responsiveness.",
                "rating": 5,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

