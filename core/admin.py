from django.contrib import admin

from .models import Profile, Team, Tag, Task, Feedback


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'avatar')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


class TeamMemberInline(admin.TabularInline):
    model = Team.members.through
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    inlines = [TeamMemberInline]
    exclude = ('members',)
    readonly_fields = ('created_at',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'team',
        'assigned_to',
        'created_by',
        'status',
        'priority',
        'deadline',
        'created_at',
    )
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('content',)
    readonly_fields = ('created_at',)
