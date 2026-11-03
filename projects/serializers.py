from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Project, ProjectMembership, Task

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    is_archived = serializers.BooleanField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "owner_id", "name", "description", "created_at", "updated_at", "archived_at", "is_archived", "member_count"]
        read_only_fields = ["id", "owner_id", "created_at", "updated_at", "archived_at", "is_archived", "member_count"]


class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    display_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ["id", "user_id", "email", "display_name", "joined_at"]
        read_only_fields = fields


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = User.objects.get(email__iexact=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("No active user exists with this email.")
        project = self.context["project"]
        if project.owner_id == self.user.pk:
            raise serializers.ValidationError("The project owner is not a member.")
        if ProjectMembership.objects.filter(project=project, user=self.user).exists():
            raise serializers.ValidationError("This user is already a project member.")
        return value

    def save(self, **kwargs):
        return ProjectMembership.objects.create(project=self.context["project"], user=self.user)


class TaskSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee", queryset=User.objects.filter(is_active=True),
        required=False, allow_null=True,
    )
    assignee_email = serializers.EmailField(source="assignee.email", read_only=True)

    class Meta:
        model = Task
        fields = ["id", "project_id", "title", "description", "status", "assignee_id", "assignee_email", "due_date", "created_at", "updated_at"]
        read_only_fields = ["id", "project_id", "created_at", "updated_at", "assignee_email"]

    def validate(self, attrs):
        project = self.context.get("project") or getattr(self.instance, "project", None)
        assignee = attrs.get("assignee", getattr(self.instance, "assignee", None))
        if assignee and project:
            is_owner = project.owner_id == assignee.pk
            is_member = ProjectMembership.objects.filter(project=project, user=assignee).exists()
            if not (is_owner or is_member):
                raise serializers.ValidationError({"assignee_id": "Assignee must be the project owner or an active member."})
        return attrs
