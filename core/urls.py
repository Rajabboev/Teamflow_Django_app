from django.urls import path
from django.http import JsonResponse

from . import views

app_name = "core"


def health(request):
    """
    Simple health check endpoint for monitoring.
    Used by CI/CD and load balancers.
    """
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Health check
    path("health/", health, name="health"),

    # Home & Auth
    path("", views.home, name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),

    # Teams
    path("teams/", views.TeamListView.as_view(), name="team_list"),
    path("teams/create/", views.TeamCreateView.as_view(), name="team_create"),
    path("teams/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
    path(
        "teams/<int:pk>/add-member/",
        views.TeamAddMemberView.as_view(),
        name="team_add_member",
    ),
    path(
        "teams/<int:pk>/remove-member/<int:user_id>/",
        views.TeamRemoveMemberView.as_view(),
        name="team_remove_member",
    ),

    # Members
    path("members/add/", views.AddMemberView.as_view(), name="add_member"),

    # Tasks
    path("tasks/", views.TaskListView.as_view(), name="task_list"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),

    # Feedback
    path(
        "tasks/<int:task_pk>/feedback/",
        views.FeedbackCreateView.as_view(),
        name="feedback_create",
    ),
]
