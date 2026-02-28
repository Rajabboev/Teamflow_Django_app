import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Profile, Team, Task


User = get_user_model()


@pytest.fixture
def member_user(db):
    """
    Regular team member user with Profile(role='member').
    """
    user = User.objects.create_user(
        username="member",
        email="member@example.com",
        password="password123",
    )
    profile = user.profile  # auto-created by signal
    profile.role = "member"
    profile.save()
    return user


@pytest.fixture
def team_lead_user(db):
    """
    Team lead user with Profile(role='team_lead').
    """
    user = User.objects.create_user(
        username="lead",
        email="lead@example.com",
        password="password123",
    )
    profile = user.profile  # auto-created by signal
    profile.role = "team_lead"
    profile.save()
    return user


@pytest.fixture
def team(db, team_lead_user, member_user):
    team = Team.objects.create(
        name="Alpha Team",
        description="Test team",
        created_by=team_lead_user,
    )
    team.members.add(team_lead_user, member_user)
    return team


@pytest.fixture
def task(db, team, team_lead_user, member_user):
    """
    A basic task assigned to the member and created by the team lead.
    """
    return Task.objects.create(
        title="Test Task",
        description="Task description",
        team=team,
        assigned_to=member_user,
        created_by=team_lead_user,
        status="todo",
        priority="medium",
        deadline=timezone.now() + timedelta(days=1),
    )

