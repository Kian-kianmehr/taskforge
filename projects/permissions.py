from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import ProjectMembership


def can_access_project(user, project):
    return bool(user and user.is_authenticated and (
        project.owner_id == user.pk
        or ProjectMembership.objects.filter(project=project, user=user).exists()
    ))


class ProjectObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return can_access_project(request.user, obj)
        return obj.owner_id == request.user.pk


class TaskObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not can_access_project(request.user, obj.project):
            return False
        if request.method in SAFE_METHODS:
            return True
        return obj.project.owner_id == request.user.pk or obj.assignee_id == request.user.pk
