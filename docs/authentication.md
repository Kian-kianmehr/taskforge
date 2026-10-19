# TaskForge — Authentication API Documentation

## Overview

TaskForge uses Django REST Framework and JSON Web Tokens (JWT) for authentication.

### Base URL

```text
http://127.0.0.1:8009
```

### Authentication

For endpoints that require authentication, include the access token in the request header:

```http
Authorization: Bearer <access_token>
```

Use the `Content-Type: application/json` header for JSON request bodies.

### Endpoint Summary

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| POST | `/accounts/register/` | No | Register a new account |
| POST | `/accounts/login/` | No | Log in and obtain JWT tokens |
| POST | `/accounts/token/refresh/` | No | Obtain a new access token |
| GET | `/accounts/me/` | Required | Retrieve the current user's profile |
| POST | `/accounts/change-password/` | Required | Change the current user's password |
| POST | `/accounts/password-reset/` | No | Request a password reset |
| POST | `/accounts/password-reset/confirm/` | No | Set a new password using a reset token |
| POST | `/accounts/verify-email/` | No | Verify an email address |
| POST | `/accounts/logout/` | Required | Revoke a refresh token |

---

## 1. Register

**Endpoint:** `POST /accounts/register/`

Creates a new user account and sends an email verification link.

### Request

```json
{
  "email": "user@example.com",
  "display_name": "Example User",
  "password": "StrongPassword123!",
  "confirm_password": "StrongPassword123!"
}
```

### Behavior

- Validates the submitted registration data.
- Rejects duplicate email addresses.
- Validates the password and checks that the password confirmation matches.
- Stores the password securely using Django's password hashing.
- Creates the account as inactive until email verification.
- Sends an email containing the verification link.

The exact response body and status code should match the current `RegisterView`.

---

## 2. Login

**Endpoint:** `POST /accounts/login/`

Authenticates a user and returns JWT tokens.

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

### Successful response

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

### Behavior

- Rejects invalid credentials.
- Users must verify their email before logging in.
- Login attempts are rate-limited to 5 requests per minute according to the configured throttle rate.

Keep both tokens private. Use the access token to authenticate protected requests.

---

## 3. Refresh Access Token

**Endpoint:** `POST /accounts/token/refresh/`

Obtains a new access token using a refresh token.

### Request

```json
{
  "refresh": "<refresh_token>"
}
```

### Successful response

```json
{
  "access": "<new_access_token>"
}
```

### Behavior

- Does not normally require an access token.
- Rejects invalid, expired, or revoked refresh tokens.
- The returned access token is used for subsequent authenticated requests.

---

## 4. Retrieve Current User

**Endpoint:** `GET /accounts/me/`

Returns the authenticated user's profile.

### Headers

```http
Authorization: Bearer <access_token>
```

### Behavior

- Requires authentication.
- Returns the profile of the currently authenticated user.
- Requests without valid authentication credentials are rejected.

The response fields are defined by `UserProfileSerializer`.

---

## 5. Change Password

**Endpoint:** `POST /accounts/change-password/`

Changes the password of the authenticated user.

### Headers

```http
Authorization: Bearer <access_token>
```

### Behavior

- Requires authentication.
- Validates the current password.
- Validates the new password.
- Checks the password confirmation.
- Saves the new password using secure password hashing.

The request field names and successful response should match `ChangePasswordSerializer` and `ChangePasswordView`.

---

## 6. Request Password Reset

**Endpoint:** `POST /accounts/password-reset/`

Requests a password-reset email.

### Behavior

- Accepts the user's email address.
- Sends a password-reset link when appropriate.
- Uses a generic response to avoid revealing whether an email address belongs to an account.

The exact request and response formats are defined by `PasswordResetView`.

---

## 7. Confirm Password Reset

**Endpoint:** `POST /accounts/password-reset/confirm/`

Sets a new password using the credentials supplied through the password-reset flow.

### Behavior

- Validates the user identifier and reset token.
- Validates the new password and its confirmation.
- Rejects invalid or expired reset credentials.
- Invalidates the reset token after a successful password change, according to the current implementation.

Use the exact field names expected by `PasswordResetConfirmView` and its serializer.

---

## 8. Verify Email

**Endpoint:** `POST /accounts/verify-email/`

Verifies a user's email address using the identifier and token from the verification link.

### Request

```json
{
  "uid": "<encoded_user_id>",
  "token": "<verification_token>"
}
```

### Successful response

```json
{
  "detail": "Email verified successfully."
}
```

### Behavior

- Rejects missing or invalid verification credentials.
- Activates the account when the token is valid.
- Handles already-verified accounts according to the current view implementation.

---

## 9. Logout

**Endpoint:** `POST /accounts/logout/`

Revokes the supplied refresh token by adding it to the token blacklist.

### Headers

```http
Authorization: Bearer <access_token>
```

### Request

```json
{
  "refresh": "<refresh_token>"
}
```

### Successful response

```json
{
  "detail": "Successfully logged out."
}
```

### Error responses

Missing refresh token:

```json
{
  "detail": "Refresh token is required."
}
```

Invalid or expired refresh token:

```json
{
  "detail": "Invalid or expired refresh token."
}
```

### Important note

Revoking a refresh token prevents it from being used to obtain new access tokens. An already-issued access token may remain valid until it expires.

---

## Security Notes

- Never commit access tokens, refresh tokens, passwords, or production secrets to version control.
- Use HTTPS in production.
- Keep Django's secret key and email credentials in environment variables.
- Use short-lived access tokens and an appropriate refresh-token lifetime.
- Protect endpoints that expose user-specific data with authentication and authorization checks.
- Keep automated tests for invalid credentials, password changes, password resets, rate limiting, and refresh-token revocation.

## Development

Run the Django development server:

```bash
python manage.py runserver 8009
```

Run account tests:

```bash
python manage.py test accounts
```
