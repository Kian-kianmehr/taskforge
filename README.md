# TaskForge

A project management REST API built with Django and Django REST Framework.

## Tech Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- PostgreSQL
- Git & GitHub

## Overview

TaskForge is a backend engineering project focused on REST API design, authentication, authorization, relational data modeling, automated testing, and maintainable application architecture.

## Current Progress

### Completed: Accounts API

- Custom email-based user model
- User registration and email verification
- JWT login and token refresh
- Current-user profile endpoint
- Password change and password reset
- Login rate limiting
- Refresh-token revocation on logout
- Automated account test suite
- Authentication API documentation

### Next: Project Domain

The next milestone is to implement the project and membership data models, database constraints, migrations, and model tests before adding project REST endpoints.

Track the work in [Issue #1](https://github.com/Kian-kianmehr/taskforge/issues/1).

## Planned Development

- Project creation, retrieval, update, and archiving
- Project membership management
- Task management and assignment
- Object-level authorization and validation
- Filtering, ordering, and pagination
- API documentation
- PostgreSQL integration
- CI, Docker, and deployment

## Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations and start the development server:

```bash
python manage.py migrate
python manage.py runserver
```

Run tests:

```bash
python manage.py test
```

## Project Status

Under active development. The accounts foundation is implemented; project and task management are the next development phases.
