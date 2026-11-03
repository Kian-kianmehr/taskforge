# TaskForge

TaskForge is a Django REST API for collaborative project and task management.

## Features

- Email-based accounts, email verification, JWT authentication and password recovery
- Project creation, updates, archiving and restoration
- Project membership management
- Task creation, assignment, status updates and due dates
- Owner/member/assignee authorization
- Filtering, search, ordering and pagination
- OpenAPI schema and Swagger UI
- Automated tests and GitHub Actions CI
- SQLite for local development and PostgreSQL support through Docker Compose

## Quick start

Requirements: Python 3.12+.

```bash
git clone https://github.com/Kian-kianmehr/taskforge.git
cd taskforge
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

The example environment uses SQLite and console email delivery. Configure SMTP variables in .env to send real emails.

## API

- Authentication: /accounts/
- Projects and tasks: /api/
- Swagger UI: /api/docs/
- OpenAPI schema: /api/schema/
- Admin: /admin/

See docs/api.md, docs/authentication.md, and docs/requirements.md.

## Tests

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts projects
```

GitHub Actions runs these checks on pushes to master.

## Docker

Copy .env.example to .env, set a unique DJANGO_SECRET_KEY and DB_PASSWORD, then run:

```bash
docker compose up --build
```

Compose starts PostgreSQL and Django with Gunicorn. Set DJANGO_DEBUG=False and configure DJANGO_ALLOWED_HOSTS for production-like use. Use HTTPS and a managed secret store for a public deployment.

## Authorization rules

- Owners manage project settings and memberships.
- Owners and members can view project data and create tasks.
- Only the owner or current assignee can edit a task.
- Only the project owner can delete a task.
- Project deletion archives instead of physically deleting.
- Archived projects are read-only until restored.
- Task assignees must be the project owner or a current member.

## Status

MVP backend API implemented. See CI for the latest automated verification.
