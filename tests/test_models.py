import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Profile, Task


User = get_user_model()


@pytest.mark.django_db
def test_profile_auto_created_on_user_creation():
    user = User.objects.create_user(
        username="newuser",
        email="new@example.com",
        password="password123",
    )

    # Profile should be auto-created by the post_save signal
    profile = Profile.objects.get(user=user)
    assert profile.role == "member"


@pytest.mark.django_db
def test_task_is_overdue(team, team_lead_user, member_user):
    overdue_deadline = timezone.now() - timedelta(days=1)
    task = Task.objects.create(
        title="Overdue Task",
        description="Past deadline",
        team=team,
        assigned_to=member_user,
        created_by=team_lead_user,
        status="todo",
        priority="medium",
        deadline=overdue_deadline,
    )

    assert task.is_overdue is True


@pytest.mark.django_db
def test_team_member_count(team, team_lead_user, member_user):
    # From the fixture, the team should have exactly these two members
    assert team.members.count() == 2
    usernames = set(team.members.values_list("username", flat=True))
    assert {"lead", "member"} <= usernames

