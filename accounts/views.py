# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

# Django REST Framework imports
from rest_framework import generics, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# JWT authentication and local application imports
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)
from .throttles import LoginRateThrottle


# Use the custom user model configured in Django settings.
User = get_user_model()



class RegisterView(APIView):
    """Register a new user and send an email verification link."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the inactive user account.
        user = serializer.save()

        # Generate a user ID and a time-limited verification token.
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Build the verification URL for the frontend.
        verification_url = (
            f"{settings.EMAIL_VERIFICATION_URL}"
            f"?uid={uid}&token={token}"
        )

        # Send the verification link to the registered email address.
        send_mail(
            subject="TaskForge - Verify Your Email",
            message=(
                "Welcome to TaskForge!\n\n"
                "Please verify your email address using this link:\n"
                f"{verification_url}\n\n"
                "If you did not create this account, you can ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {
                "message": (
                    "Registration successful. "
                    "Please check your email to verify your account."
                )
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(RetrieveAPIView):
    """Return the profile of the currently authenticated user."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    """Allow an authenticated user to change their password."""

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class LoginView(TokenObtainPairView):
    """Issue JWT tokens with login rate limiting."""

    throttle_classes = [LoginRateThrottle]


class PasswordResetView(APIView):
    """Send password-reset links without revealing account existence."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()

        if not email:
            return Response(
                {"detail": "If an account exists, a reset email will be sent."},
                status=status.HTTP_200_OK,
            )

        users = User.objects.filter(
            email__iexact=email,
            is_active=True,
        )

        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Build the reset link for the frontend.
            reset_url = (
                f"{settings.PASSWORD_RESET_URL}"
                f"?uid={uid}&token={token}"
            )

            send_mail(
                subject="TaskForge - Password Reset",
                message=(
                    "We received a request to reset your password.\n\n"
                    f"Use this link to reset it:\n{reset_url}\n\n"
                    "If you did not request this, ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        return Response(
            {"detail": "If an account exists, a reset email will be sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Validate a reset token and set a new password."""

    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not uid or not token or not new_password:
            return Response(
                {"detail": "uid, token and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id, is_active=True)
        except (ValueError, TypeError, OverflowError, UnicodeDecodeError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply Django's configured password-strength validators.
        try:
            validate_password(new_password, user=user)
        except ValidationError as exc:
            return Response(
                {"new_password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    """Activate a user account after validating the email token."""

    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")

        if not uid or not token:
            return Response(
                {"detail": "uid and token are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)
        except (
            ValueError,
            TypeError,
            OverflowError,
            UnicodeDecodeError,
            User.DoesNotExist,
        ):
            return Response(
                {"detail": "Invalid or expired verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_active:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_200_OK,
            )

        # Activate the account only after the token has been validated.
        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response(
            {"detail": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )
