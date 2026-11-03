from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Project, ProjectMembership, Task
from .permissions import ProjectObjectPermission, TaskObjectPermission, can_access_project
from .serializers import AddMemberSerializer, MembershipSerializer, ProjectSerializer, TaskSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectObjectPermission]

    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.annotate(member_count=Count("memberships")).filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()
        if self.action == "list" and self.request.query_params.get("include_archived") != "true":
            queryset = queryset.filter(archived_at__isnull=True)
        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.is_archived:
            raise PermissionDenied("Archived projects are read-only.")
        serializer.save()

    def perform_destroy(self, instance):
        if not instance.is_archived:
            instance.archived_at = timezone.now()
            instance.save(update_fields=["archived_at", "updated_at"])

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        project = self.get_object()
        if project.owner_id != request.user.pk:
            raise PermissionDenied("Only the project owner can archive it.")
        if not project.is_archived:
            project.archived_at = timezone.now()
            project.save(update_fields=["archived_at", "updated_at"])
        return Response(self.get_serializer(project).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        project = self.get_object()
        if project.owner_id != request.user.pk:
            raise PermissionDenied("Only the project owner can restore it.")
        if project.is_archived:
            project.archived_at = None
            project.save(update_fields=["archived_at", "updated_at"])
        return Response(self.get_serializer(project).data)

    @action(detail=True, methods=["get", "post", "delete"], url_path="members")
    def members(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            return Response(MembershipSerializer(project.memberships.select_related("user"), many=True).data)
        if project.owner_id != request.user.pk:
            raise PermissionDenied("Only the project owner can manage members.")
        if project.is_archived:
            raise PermissionDenied("Archived projects are read-only.")
        if request.method == "POST":
            serializer = AddMemberSerializer(data=request.data, context={"project": project})
            serializer.is_valid(raise_exception=True)
            membership = serializer.save()
            return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)
        membership_id = request.query_params.get("membership_id")
        if not membership_id:
            return Response({"detail": "membership_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = ProjectMembership.objects.filter(project=project, pk=membership_id).delete()
        if not deleted:
            return Response({"detail": "Membership not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, TaskObjectPermission]
    http_method_names = ["get", "post", "patch", "put", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.select_related("project", "assignee").filter(
            Q(project__owner=user) | Q(project__memberships__user=user)
        ).distinct()
        params = self.request.query_params
        if params.get("project"):
            queryset = queryset.filter(project_id=params["project"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("assignee"):
            queryset = queryset.filter(assignee_id=params["assignee"])
        if params.get("due_before"):
            queryset = queryset.filter(due_date__lte=params["due_before"])
        if params.get("search"):
            queryset = queryset.filter(Q(title__icontains=params["search"]) | Q(description__icontains=params["search"]))
        ordering = params.get("ordering", "-created_at")
        if ordering.lstrip("-") in {"created_at", "due_date", "title", "status"}:
            queryset = queryset.order_by(ordering)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_id = self.request.data.get("project") or self.request.query_params.get("project")
        if project_id and self.action in {"create", "update", "partial_update"}:
            try:
                project = Project.objects.get(pk=project_id)
            except (Project.DoesNotExist, ValueError):
                return context
            context["project"] = project
        return context

    def perform_create(self, serializer):
        project_id = self.request.data.get("project")
        try:
            project = Project.objects.get(pk=project_id)
        except (Project.DoesNotExist, ValueError, TypeError):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"project": "A valid project ID is required."})
        if not can_access_project(self.request.user, project):
            raise PermissionDenied("You do not have access to this project.")
        if project.is_archived:
            raise PermissionDenied("Archived projects are read-only.")
        serializer.save(project=project)

    def perform_update(self, serializer):
        if self.get_object().project.is_archived:
            raise PermissionDenied("Archived projects are read-only.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.project.is_archived:
            raise PermissionDenied("Archived projects are read-only.")
        if instance.project.owner_id != self.request.user.pk:
            raise PermissionDenied("Only the project owner can delete tasks.")
        instance.delete()
