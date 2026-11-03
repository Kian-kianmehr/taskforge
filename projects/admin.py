from django.contrib import admin

from .models import Project, ProjectMembership, Task


class MembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at", "archived_at")
    list_filter = ("archived_at", "created_at")
    search_fields = ("name", "owner__email")
    inlines = (MembershipInline, TaskInline)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "assignee", "due_date")
    list_filter = ("status", "due_date")
    search_fields = ("title", "project__name", "assignee__email")
