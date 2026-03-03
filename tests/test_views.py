import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from core.models import Task, Feedback

User = get_user_model()


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    url = reverse("core:dashboard")
    response = client.get(url)
    assert response.status_code == 302
    # Redirects to login with ?next=
    assert reverse("core:login") in response.url


@pytest.mark.django_db
def test_register_creates_user(client):
    url = reverse("core:register")
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "role": "member",
        "password1": "StrongPass123!",
        "password2": "StrongPass123!",
    }
    response = client.post(url, data)

    # Should redirect to dashboard
    assert response.status_code == 302
    assert reverse("core:dashboard") in response.url

    user = User.objects.get(username="newuser")
    assert user.email == "newuser@example.com"
    # Profile and role should be set
    assert user.profile.role == "member"


@pytest.mark.django_db
def test_task_create_by_team_lead_success(client, team_lead_user, member_user, team):
    client.force_login(team_lead_user)
    url = reverse("core:task_create")

    before_count = Task.objects.count()
    data = {
        "title": "Lead created task",
        "description": "Created by lead",
        "team": team.id,
        "assigned_to": member_user.id,
        "status": "todo",
        "priority": "medium",
        "deadline": "",
        "tags": [],
    }
    response = client.post(url, data)
    assert response.status_code == 302

    after_count = Task.objects.count()
    assert after_count == before_count + 1


@pytest.mark.django_db
def test_task_create_by_member_forbidden(client, member_user, team):
    client.force_login(member_user)
    url = reverse("core:task_create")

    before_count = Task.objects.count()
    data = {
        "title": "Member created task",
        "description": "Should not be allowed",
        "team": team.id,
        "assigned_to": member_user.id,
        "status": "todo",
        "priority": "medium",
        "deadline": "",
        "tags": [],
    }
    response = client.post(url, data)

    # TeamLeadRequiredMixin should redirect to dashboard with error message
    assert response.status_code == 302
    assert reverse("core:dashboard") in response.url
    assert Task.objects.count() == before_count


@pytest.mark.django_db
def test_feedback_only_team_lead_can_post(client, task, team_lead_user, member_user):
    # Team lead can post feedback
    client.force_login(team_lead_user)
    url = reverse("core:feedback_create", kwargs={"task_pk": task.pk})
    data = {"content": "Great job", "rating": 5}
    response = client.post(url, data)
    assert response.status_code == 302
    assert Feedback.objects.filter(task=task, author=team_lead_user).count() == 1

    # Member cannot post feedback
    client.logout()
    client.force_login(member_user)
    response = client.post(url, data)
    # Redirected to dashboard by TeamLeadRequiredMixin
    assert response.status_code == 302
    assert reverse("core:dashboard") in response.url
    # No new feedback from member
    assert Feedback.objects.filter(task=task, author=member_user).count() == 0


@pytest.mark.django_db
def test_task_list_filters_by_status(client, member_user, team_lead_user, team):
    # Create tasks with different statuses for the same user
    done_task = Task.objects.create(
        title="Done task",
        description="Done",
        team=team,
        assigned_to=member_user,
        created_by=team_lead_user,
        status="done",
        priority="medium",
        deadline=timezone.now() - timedelta(days=1),
    )
    todo_task = Task.objects.create(
        title="Todo task",
        description="Todo",
        team=team,
        assigned_to=member_user,
        created_by=team_lead_user,
        status="todo",
        priority="medium",
        deadline=timezone.now() + timedelta(days=1),
    )

    client.force_login(member_user)
    url = reverse("core:task_list")
    response = client.get(url, {"status": "done"})

    assert response.status_code == 200
    tasks = list(response.context["tasks"])
    assert done_task in tasks
    assert todo_task not in tasks
