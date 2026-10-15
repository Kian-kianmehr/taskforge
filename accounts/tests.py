
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/accounts/register/"
        self.user_data = {
            "email": "test@example.com",
            "display_name": "Test User",
            "password": "StrongTestPass123!",
        }

    def test_register_creates_user(self):
        response = self.client.post(
            self.url,
            self.user_data,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertTrue(
            get_user_model().objects.filter(
                email="test@example.com"
            ).exists()
        )

    def test_register_hashes_password(self):
        self.client.post(
            self.url,
            self.user_data,
            format="json",
        )

        user = get_user_model().objects.get(
            email="test@example.com"
        )

        self.assertNotEqual(
            user.password,
            self.user_data["password"],
        )
        self.assertTrue(
            user.check_password(self.user_data["password"])
        )

    def test_register_rejects_duplicate_email(self):
        first_response = self.client.post(
            self.url,
            self.user_data,
            format="json",
        )

        second_response = self.client.post(
            self.url,
            self.user_data,
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 1)
