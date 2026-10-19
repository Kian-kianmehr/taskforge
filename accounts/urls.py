from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    MeView,
    ChangePasswordView,
    LoginView,
    PasswordResetView,
    PasswordResetConfirmView,
    VerifyEmailView,
    LogoutView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/",ChangePasswordView.as_view(),name="change-password",),
    path("password-reset/",PasswordResetView.as_view(),name="password-reset",),
    path("password-reset/confirm/",PasswordResetConfirmView.as_view(),name="password-reset-confirm",),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("logout/", LogoutView.as_view(), name="logout"),
]