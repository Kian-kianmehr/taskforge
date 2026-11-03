# TaskForge

TaskForge is a collaborative project and task management application. It provides a REST API for managing projects, memberships, and tasks. A React-based web frontend is also being developed for the platform.

## Features

### Backend

- Email-based user accounts
- Email verification and password recovery
- JWT authentication
- Project creation, editing, archiving, and restoration
- Project membership management
- Task creation, assignment, status updates, and due dates
- Role-based permissions for project owners, members, and task assignees
- Filtering, search, ordering, and pagination
- OpenAPI schema and interactive Swagger documentation
- Automated tests and GitHub Actions CI
- SQLite for local development and PostgreSQL support with Docker Compose

### Frontend

The frontend is being built with **React** and **Vite** to provide the user-facing interface for working with projects and tasks.

AI tools assisted with frontend implementation and UI development. They were used as development aids; the resulting code is intended to remain reviewable and maintainable as part of the project.

> **Note:** The frontend source is not currently included in the `master` branch. The setup instructions below therefore cover the backend only.

## Technology Stack

| Area | Technologies |
| --- | --- |
| Backend | Python, Django, Django REST Framework |
| Authentication | JSON Web Tokens (JWT) |
| API documentation | OpenAPI, drf-spectacular, Swagger UI |
| Frontend (in development) | React, Vite |
| Database | SQLite, PostgreSQL |
| Deployment | Docker, Docker Compose, Gunicorn |
| Quality | Django tests, GitHub Actions |

## Project Structure

```text
taskforge/
├── accounts/          # Authentication and account management
├── config/            # Django project configuration
├── docs/              # API, authentication, and requirements docs
├── projects/          # Projects, memberships, and tasks
├── .github/           # GitHub Actions workflows
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Getting Started

### Backend

**Requirements:** Python 3.12+

1. Clone the repository:

   ```bash
   git clone https://github.com/Kian-kianmehr/taskforge.git
   cd taskforge
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   On Windows, activate it with:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. Install dependencies and configure the environment:

   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   ```

4. Apply migrations and start the development server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

The example environment uses SQLite and console email delivery. Configure the SMTP variables in `.env` to send real emails.

## API

When the backend is running, the following endpoints are available:

| Resource | URL |
| --- | --- |
| Authentication | `/accounts/` |
| Projects and tasks | `/api/` |
| Swagger UI | `/api/docs/` |
| OpenAPI schema | `/api/schema/` |
| Django admin | `/admin/` |

Protected API endpoints use a JWT access token:

```http
Authorization: Bearer <access_token>
```

More detailed documentation:

- [API reference](docs/api.md)
- [Authentication](docs/authentication.md)
- [Requirements](docs/requirements.md)

## Running Tests

Run the backend checks from the repository root:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts projects
```

GitHub Actions runs the configured checks on pushes to the `master` branch.

## Docker

Copy `.env.example` to `.env`, set a unique `DJANGO_SECRET_KEY` and a strong `DB_PASSWORD`, then run:

```bash
docker compose up --build
```

Docker Compose starts PostgreSQL and the Django application served by Gunicorn.

For a production deployment, set `DJANGO_DEBUG=False`, configure `DJANGO_ALLOWED_HOSTS`, use HTTPS, and store secrets in an appropriate secret manager.

## Authorization Rules

- Project owners can manage project settings and memberships.
- Owners and members can view project data and create tasks.
- Only the project owner or the current task assignee can update a task.
- Only the project owner can delete a task.
- Deleting a project archives it instead of physically deleting it.
- Archived projects are read-only until restored.
- Task assignees must be the project owner or a current project member.

## Project Status

The backend API and its core project, membership, task, and authentication workflows are implemented. The React frontend is under development with assistance from AI tools and is not yet present in the public `master` branch.
