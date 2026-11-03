from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Project, ProjectMembership, Task

User = get_user_model()


class ProjectModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongTestPassword123!")

    def test_project_is_created_for_owner(self):
        project = Project.objects.create(owner=self.owner, name="Website Redesign")
        self.assertEqual(project.owner, self.owner)
        self.assertEqual(project.description, "")
        self.assertIsNone(project.archived_at)
        self.assertFalse(project.is_archived)
        self.assertIn(project, self.owner.owned_projects.all())

    def test_project_can_have_description(self):
        project = Project.objects.create(owner=self.owner, name="API", description="Backend API")
        self.assertEqual(project.description, "Backend API")

    def test_project_archive_state(self):
        project = Project.objects.create(owner=self.owner, name="Archive")
        project.archived_at = timezone.now()
        project.save(update_fields=["archived_at"])
        project.refresh_from_db()
        self.assertTrue(project.is_archived)

    def test_project_updated_at_changes_on_save(self):
        project = Project.objects.create(owner=self.owner, name="Timestamp")
        old = project.updated_at
        project.name = "Updated"
        project.save()
        project.refresh_from_db()
        self.assertGreaterEqual(project.updated_at, old)


class ProjectMembershipModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongTestPassword123!")
        self.member = User.objects.create_user(email="member@example.com", password="StrongTestPassword123!")
        self.project = Project.objects.create(owner=self.owner, name="TaskForge API")

    def test_membership_connects_project_and_user(self):
        membership = ProjectMembership.objects.create(project=self.project, user=self.member)
        self.assertEqual(membership.project, self.project)
        self.assertEqual(membership.user, self.member)
        self.assertIsNotNone(membership.joined_at)

    def test_duplicate_membership_is_rejected(self):
        ProjectMembership.objects.create(project=self.project, user=self.member)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProjectMembership.objects.create(project=self.project, user=self.member)

    def test_same_user_can_join_different_projects(self):
        other = Project.objects.create(owner=self.owner, name="Docs")
        ProjectMembership.objects.create(project=self.project, user=self.member)
        ProjectMembership.objects.create(project=other, user=self.member)
        self.assertEqual(self.member.project_memberships.count(), 2)

    def test_deleting_project_deletes_memberships(self):
        membership = ProjectMembership.objects.create(project=self.project, user=self.member)
        self.project.delete()
        self.assertFalse(ProjectMembership.objects.filter(pk=membership.pk).exists())


class ProjectAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongTestPassword123!")
        self.member = User.objects.create_user(email="member@example.com", password="StrongTestPassword123!")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="StrongTestPassword123!")
        self.project = Project.objects.create(owner=self.owner, name="Alpha")
        self.member_url = "/api/projects/{}/members/".format(self.project.pk)

    def auth(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")

    def test_owner_can_create_and_list_projects(self):
        self.auth(self.owner)
        response = self.client.post("/api/projects/", {"name": "New"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["owner_id"], self.owner.pk)
        self.assertEqual(self.client.get("/api/projects/").status_code, 200)

    def test_member_can_view_but_not_edit_project(self):
        ProjectMembership.objects.create(project=self.project, user=self.member)
        self.auth(self.member)
        self.assertEqual(self.client.get(f"/api/projects/{self.project.pk}/").status_code, 200)
        self.assertEqual(self.client.patch(f"/api/projects/{self.project.pk}/", {"name": "Hack"}, format="json").status_code, 403)

    def test_outsider_cannot_retrieve_project(self):
        self.auth(self.outsider)
        self.assertEqual(self.client.get(f"/api/projects/{self.project.pk}/").status_code, 404)

    def test_owner_can_add_and_remove_member(self):
        self.auth(self.owner)
        response = self.client.post(self.member_url, {"email": self.member.email}, format="json")
        self.assertEqual(response.status_code, 201)
        membership_id = response.data["id"]
        response = self.client.delete(self.member_url + f"?membership_id={membership_id}")
        self.assertEqual(response.status_code, 204)

    def test_non_owner_cannot_manage_members(self):
        ProjectMembership.objects.create(project=self.project, user=self.member)
        self.auth(self.member)
        self.assertEqual(self.client.post(self.member_url, {"email": self.outsider.email}, format="json").status_code, 403)

    def test_archive_and_restore(self):
        self.auth(self.owner)
        self.assertEqual(self.client.post(f"/api/projects/{self.project.pk}/archive/").status_code, 200)
        self.project.refresh_from_db()
        self.assertTrue(self.project.is_archived)
        self.assertEqual(self.client.post(f"/api/projects/{self.project.pk}/restore/").status_code, 200)
        self.project.refresh_from_db()
        self.assertFalse(self.project.is_archived)


class TaskAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="StrongTestPassword123!")
        self.member = User.objects.create_user(email="member@example.com", password="StrongTestPassword123!")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="StrongTestPassword123!")
        self.project = Project.objects.create(owner=self.owner, name="Alpha")
        ProjectMembership.objects.create(project=self.project, user=self.member)

    def auth(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")

    def test_owner_can_create_task(self):
        self.auth(self.owner)
        response = self.client.post("/api/tasks/", {"project": self.project.pk, "title": "Ship API"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], Task.Status.TODO)

    def test_member_can_create_and_view_task(self):
        self.auth(self.member)
        response = self.client.post("/api/tasks/", {"project": self.project.pk, "title": "Write docs"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/api/tasks/").status_code, 200)

    def test_outsider_cannot_create_or_view_tasks(self):
        self.auth(self.outsider)
        self.assertEqual(self.client.post("/api/tasks/", {"project": self.project.pk, "title": "No"}, format="json").status_code, 403)
        self.assertEqual(self.client.get("/api/tasks/").data["count"], 0)

    def test_only_owner_or_assignee_can_edit(self):
        task = Task.objects.create(project=self.project, title="Assigned", assignee=self.member)
        self.auth(self.member)
        self.assertEqual(self.client.patch(f"/api/tasks/{task.pk}/", {"status": "done"}, format="json").status_code, 200)
        other = Task.objects.create(project=self.project, title="Unassigned")
        self.assertEqual(self.client.patch(f"/api/tasks/{other.pk}/", {"status": "done"}, format="json").status_code, 403)

    def test_assignee_must_be_project_member(self):
        self.auth(self.owner)
        response = self.client.post("/api/tasks/", {"project": self.project.pk, "title": "Bad assignment", "assignee_id": self.outsider.pk}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_archived_project_blocks_task_mutations(self):
        self.project.archived_at = timezone.now()
        self.project.save()
        self.auth(self.owner)
        response = self.client.post("/api/tasks/", {"project": self.project.pk, "title": "Blocked"}, format="json")
        self.assertEqual(response.status_code, 403)
