from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()

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



class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/accounts/login/"
        self.refresh_url = "/accounts/token/refresh/"

        self.email = "login@example.com"
        self.password = "StrongTestPass123!"

        self.user = get_user_model().objects.create_user(
            email=self.email,
            password=self.password,
        )

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.email,
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_refresh_returns_new_access_token(self):
        login_response = self.client.post(
            self.login_url,
            {
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

class MeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="kian@example.com",
            password="TestPassword123!",
            display_name="Kian",
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_me_returns_authenticated_user_profile(self):
        self.authenticate(self.user)

        response = self.client.get("/accounts/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(
            response.data["display_name"],
            self.user.display_name,
        )
        self.assertIn("created_at", response.data)

    def test_me_requires_authentication(self):
        response = self.client.get("/accounts/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_me_returns_only_authenticated_users_profile(self):
        self.authenticate(self.user)

        User.objects.create_user(
            email="another@example.com",
            password="AnotherPassword123!",
            display_name="Another User",
        )

        response = self.client.get("/accounts/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertNotEqual(
            response.data["email"],
            "another@example.com",
        )




class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="password-test@example.com",
            display_name="Password Test",
            password="CurrentPassword123!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/accounts/change-password/"

    def test_change_password_successfully(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "CurrentPassword123!",
                "new_password": "NewPassword456!",
                "confirm_new_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword456!"))
        self.assertFalse(self.user.check_password("CurrentPassword123!"))
        self.assertNotEqual(
            self.user.password,
            "NewPassword456!",
        )

    def test_change_password_with_wrong_old_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "WrongPassword123!",
                "new_password": "NewPassword456!",
                "confirm_new_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("CurrentPassword123!"))

    def test_change_password_with_mismatched_new_passwords(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "CurrentPassword123!",
                "new_password": "NewPassword456!",
                "confirm_new_password": "DifferentPassword789!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("CurrentPassword123!"))

    def test_change_password_without_authentication(self):
        client = APIClient()

        response = client.post(
            self.url,
            {
                "old_password": "CurrentPassword123!",
                "new_password": "NewPassword456!",
                "confirm_new_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_change_password_with_invalid_new_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "CurrentPassword123!",
                "new_password": "123",
                "confirm_new_password": "123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("CurrentPassword123!"))