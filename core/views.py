from django.contrib.auth import get_user_model, login, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
    TemplateView,
)

from .forms import (
    RegisterForm,
    ProfileForm,
    TeamForm,
    TaskForm,
    TaskStatusOnlyForm,
    FeedbackForm,
    AddMemberForm,
)
from .models import Profile, Team, Task, Feedback

User = get_user_model()


# ---------- Mixins ----------

class TeamLeadRequiredMixin(LoginRequiredMixin):
    """Only team leads can access this view."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role != 'team_lead':
            from django.contrib import messages
            messages.error(request, 'Only team leads can perform this action.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


# ---------- Auth ----------

class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegisterForm
    template_name = 'core/auth/register.html'
    success_url = reverse_lazy('core:dashboard')
    success_message = 'Account created. Welcome!'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class LoginView(auth_views.LoginView):
    template_name = 'core/auth/login.html'
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    next_page = 'core:login'


class ProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'core/profile.html'
    success_url = reverse_lazy('core:profile')

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(
            user=self.request.user,
            defaults={'role': 'member'},
        )
        return profile

    def get_success_url(self):
        return reverse_lazy('core:profile')


# ---------- Dashboard ----------

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tasks = Task.objects.filter(assigned_to=user)
        now = timezone.now()
        context['tasks'] = tasks[:10]
        context['total_tasks'] = tasks.count()
        context['overdue_count'] = tasks.filter(deadline__lt=now).exclude(status='done').count()
        context['done_count'] = tasks.filter(status='done').count()
        context['in_progress_count'] = tasks.filter(status='in_progress').count()
        context['now'] = now
        return context


# ---------- Teams ----------

class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'core/teams/list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        user = self.request.user
        return Team.objects.filter(
            Q(created_by=user) | Q(members=user)
        ).distinct()


class AddMemberView(TeamLeadRequiredMixin, SuccessMessageMixin, FormView):
    """Team leads only: create a new user (new hire) and optionally add to teams."""
    form_class = AddMemberForm
    template_name = 'core/members/add.html'
    success_url = reverse_lazy('core:team_list')
    success_message = 'New member added successfully.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user
        kwargs['teams_queryset'] = Team.objects.filter(
            Q(created_by=user) | Q(members=user)
        ).distinct()
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        qs = self.get_form_kwargs().get('teams_queryset', Team.objects.none())
        form.fields['teams'].queryset = qs
        return form

    def form_valid(self, form):
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
        )
        Profile.objects.update_or_create(
            user=user,
            defaults={'role': form.cleaned_data['role']},
        )
        for team in form.cleaned_data.get('teams') or []:
            team.members.add(user)
        return super().form_valid(form)


class TeamCreateView(TeamLeadRequiredMixin, SuccessMessageMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'core/teams/create.html'
    success_url = reverse_lazy('core:team_list')
    success_message = 'Team created.'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'core/teams/detail.html'
    context_object_name = 'team'

    def get_queryset(self):
        user = self.request.user
        return Team.objects.filter(
            Q(created_by=user) | Q(members=user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_lead'] = self.object.created_by_id == self.request.user.id
        return context


class TeamAddMemberView(LoginRequiredMixin, View):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        if team.created_by_id != request.user.id:
            from django.contrib import messages
            messages.error(request, 'Only the team creator can add members.')
            return redirect('core:team_detail', pk=pk)
        username = request.POST.get('username')
        if username:
            user = User.objects.filter(username=username).first()
            if user and user not in team.members.all():
                team.members.add(user)
                from django.contrib import messages
                messages.success(request, f'Added {username}.')
        return redirect('core:team_detail', pk=pk)


class TeamRemoveMemberView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        team = get_object_or_404(Team, pk=pk)
        if team.created_by_id != request.user.id:
            from django.contrib import messages
            messages.error(request, 'Only the team creator can remove members.')
            return redirect('core:team_detail', pk=pk)
        team.members.remove(user_id)
        from django.contrib import messages
        messages.success(request, 'Member removed.')
        return redirect('core:team_detail', pk=pk)


# ---------- Tasks ----------

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'core/tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        qs = Task.objects.filter(
            Q(assigned_to=self.request.user)
            | Q(team__members=self.request.user)
            | Q(team__created_by=self.request.user)
        ).distinct().select_related("team", "assigned_to", "created_by").prefetch_related("tags")
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        deadline = self.request.GET.get('deadline')
        if deadline == 'overdue':
            qs = qs.filter(deadline__lt=timezone.now()).exclude(status='done')
        elif deadline == 'upcoming':
            qs = qs.filter(deadline__gte=timezone.now()).exclude(status='done')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['priority_filter'] = self.request.GET.get('priority', '')
        context['deadline_filter'] = self.request.GET.get('deadline', '')
        context['now'] = timezone.now()
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'core/tasks/detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.filter(
            Q(assigned_to=self.request.user)
            | Q(team__members=self.request.user)
            | Q(team__created_by=self.request.user)
        ).distinct().prefetch_related("feedbacks", "feedbacks__author", "tags")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_give_feedback'] = getattr(
            self.request.user, 'profile', None
        ) and self.request.user.profile.role == 'team_lead'
        context['now'] = timezone.now()
        return context


class TaskCreateView(TeamLeadRequiredMixin, SuccessMessageMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'core/tasks/form.html'
    success_message = 'Task created.'

    def get_success_url(self):
        return reverse_lazy('core:task_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if 'team' in form.fields:
            user = self.request.user
            form.fields['team'].queryset = Team.objects.filter(
                Q(created_by=user) | Q(members=user)
            ).distinct()
        return form


class TaskUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Task
    template_name = 'core/tasks/form.html'
    success_message = 'Task updated.'

    def get_form_class(self):
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role == 'member':
            return TaskStatusOnlyForm
        return TaskForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if 'team' in form.fields:
            user = self.request.user
            form.fields['team'].queryset = Team.objects.filter(
                Q(created_by=user) | Q(members=user)
            ).distinct()
        return form

    def get_success_url(self):
        return reverse_lazy('core:task_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return Task.objects.filter(
            Q(assigned_to=self.request.user)
            | Q(team__members=self.request.user)
            | Q(team__created_by=self.request.user)
        ).distinct()


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('core:task_list')
    template_name = 'core/tasks/delete.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.filter(
            Q(assigned_to=self.request.user)
            | Q(team__members=self.request.user)
            | Q(team__created_by=self.request.user)
        ).distinct()


# ---------- Feedback ----------

class FeedbackCreateView(TeamLeadRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = 'core/feedback/form.html'
    success_message = 'Feedback added.'

    def get_task(self):
        return get_object_or_404(
            Task.objects.filter(
                Q(assigned_to=self.request.user)
                | Q(team__members=self.request.user)
                | Q(team__created_by=self.request.user)
            ).distinct(),
            pk=self.kwargs['task_pk'],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task'] = self.get_task()
        return context

    def form_valid(self, form):
        form.instance.task = self.get_task()
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('core:task_detail', kwargs={'pk': self.kwargs['task_pk']})


# ---------- Home ----------

def home(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return redirect('core:login')
