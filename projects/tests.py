from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from .models import Project, ProjectMembership


User = get_user_model()


class ProjectModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongTestPassword123!",
        )

    def test_project_is_created_for_owner(self):
        project = Project.objects.create(
            owner=self.owner,
            name="Website Redesign",
        )

        self.assertEqual(project.owner, self.owner)
        self.assertEqual(project.name, "Website Redesign")
        self.assertEqual(project.description, "")
        self.assertIsNone(project.archived_at)
        self.assertFalse(project.is_archived)
        self.assertIn(project, self.owner.owned_projects.all())

    def test_project_can_have_description(self):
        project = Project.objects.create(
            owner=self.owner,
            name="API",
            description="Backend API development",
        )

        self.assertEqual(project.description, "Backend API development")

    def test_project_archive_state_is_derived_from_archived_at(self):
        project = Project.objects.create(
            owner=self.owner,
            name="Archived project",
        )
        self.assertFalse(project.is_archived)

        project.archived_at = timezone.now()
        project.save(update_fields=["archived_at"])

        project.refresh_from_db()
        self.assertTrue(project.is_archived)

    def test_project_updated_at_changes_on_save(self):
        project = Project.objects.create(
            owner=self.owner,
            name="Timestamp test",
        )
        original_updated_at = project.updated_at

        project.name = "Updated timestamp test"
        project.save()
        project.refresh_from_db()

        self.assertGreaterEqual(project.updated_at, original_updated_at)


class ProjectMembershipModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongTestPassword123!",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="StrongTestPassword123!",
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name="TaskForge API",
        )

    def test_membership_connects_project_and_user(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.assertEqual(membership.project, self.project)
        self.assertEqual(membership.user, self.member)
        self.assertIn(membership, self.project.memberships.all())
        self.assertIn(membership, self.member.project_memberships.all())
        self.assertIsNotNone(membership.joined_at)

    def test_duplicate_membership_is_rejected_by_database(self):
        ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProjectMembership.objects.create(
                    project=self.project,
                    user=self.member,
                )

    def test_same_user_can_join_different_projects(self):
        another_project = Project.objects.create(
            owner=self.owner,
            name="Documentation",
        )

        first = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
        )
        second = ProjectMembership.objects.create(
            project=another_project,
            user=self.member,
        )

        self.assertNotEqual(first.project_id, second.project_id)
        self.assertEqual(self.member.project_memberships.count(), 2)

    def test_deleting_project_deletes_its_memberships(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
        )

        self.project.delete()

        self.assertFalse(
            ProjectMembership.objects.filter(pk=membership.pk).exists()
        )
