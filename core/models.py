from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    ROLE_CHOICES = [
        ('team_lead', 'Team Lead'),
        ('member', 'Member'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    avatar = models.FileField(upload_to='avatars/', blank=True, null=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.get_username()} ({self.get_role_display()})"


class Team(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_teams',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7)  # hex e.g. #FF5733

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
    )
    deadline = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField('Tag', related_name='tasks', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self) -> bool:
        """
        Return True if the task has a past deadline and is not done.
        """
        if not self.deadline:
            return False
        return self.deadline < timezone.now() and self.status != 'done'


class Feedback(models.Model):
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='feedbacks',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks',
    )
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback by {self.author} on {self.task} ({self.rating}/5)"
