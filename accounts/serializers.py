
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validate registration data and create an inactive user."""

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "display_name",
            "password",
            "confirm_password",
        ]

    def validate(self, attrs):
        # Ensure both password fields match before creating the user.
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        # The confirmation is only for validation, not for storage.
        attrs.pop("confirm_password")
        return attrs

    def create(self, validated_data):
        # New accounts remain inactive until email verification.
        return User.objects.create_user(
            **validated_data,
            is_active=False,
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """Expose read-only profile information."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "display_name",
            "created_at",
        ]
        read_only_fields = fields


class ChangePasswordSerializer(serializers.Serializer):
    """Validate the current password and the requested new password."""

    old_password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
        validators=[validate_password],
    )
    confirm_new_password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
    )

    def validate_old_password(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Your current password is incorrect."
            )

        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({
                "confirm_new_password": "The new passwords do not match."
            })

        return attrs
