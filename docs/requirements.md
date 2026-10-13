# TaskForge API — Requirements Specification

**Version:** 1.0  
**Status:** Approved for MVP implementation  
**Application type:** REST API  
**Technology:** Python, Django, Django REST Framework, PostgreSQL

## 1. Purpose

TaskForge is a backend API for managing projects, project memberships, and tasks. It provides authentication, role-based access control, task assignment, filtering, pagination, and project archiving.

The MVP focuses on correctness, security, maintainability, and reliable deployment rather than feature quantity.

## 2. Scope

### Included

- User registration and authentication
- Project creation and management
- Project membership management
- Task creation, retrieval, updating, and deletion
- Task assignment and status management
- Authorization and input validation
- Filtering, searching, ordering, and pagination
- Automated tests and API documentation
- PostgreSQL, Docker, CI, and deployment

### Excluded

- Frontend application
- Email invitations
- Chat and real-time notifications
- File uploads
- Billing and subscriptions
- AI-powered functionality
- Microservices and distributed infrastructure

## 3. User Roles

### Project Owner

The user recorded as the owner of a project. The owner can manage project settings and memberships, archive and restore the project, and manage its tasks.

### Project Member

A registered user who has been added to a project. Members can view project information and create tasks, subject to the rules below.

A user can own one project and be a member of another.

## 4. Functional Requirements

### FR-01 — Authentication

- Users can register and authenticate.
- Protected endpoints require valid authentication.
- Passwords must be handled using Django's supported password-hashing mechanisms.
- Authentication and authorization must be treated as separate concerns.

### FR-02 — Project Management

- Authenticated users can create projects.
- A project's owner is the user who created it.
- Owners can view and update their projects.
- Project access is restricted to the owner and authorized members.
- Owners can archive and restore projects.

### FR-03 — Membership Management

- Only the project owner can add or remove members.
- Only existing registered users can be added.
- A user cannot have duplicate membership records for the same project.
- Removing a member revokes that user's project access.
- A user cannot access private project data simply by knowing its ID.

### FR-04 — Task Management

- Authorized users can create tasks within a project.
- Tasks belong to exactly one project.
- Tasks contain a title, optional description, status, optional assignee, creation timestamp, and optional due date.
- Task lists support filtering, ordering, and pagination.

### FR-05 — Task Assignment

- A task may be unassigned.
- An assignee must be the project owner or an active member of the project.
- Removing a member must not leave their account with continued access to the project.

### FR-06 — Task Editing Authorization

- The project owner can edit any task in their project.
- The task's current assignee can edit that task while they remain authorized to access the project.
- Other members may view tasks but cannot edit tasks assigned to someone else.
- Authorization must be checked on the server for every relevant request; hiding an action in a client interface is not sufficient.

### FR-07 — Task Status

Allowed statuses:

- `todo`
- `in_progress`
- `done`

Invalid status values must be rejected.

### FR-08 — Project Archiving

- Archiving a project sets its archive timestamp; it does not physically delete the project.
- Archived projects are excluded from default active-project listings.
- The owner can retrieve and restore an archived project.
- Existing tasks, memberships, and task history remain stored.
- Archived projects are read-only in the MVP: task creation, task editing, membership changes, and other project mutations are blocked until restoration.

### FR-09 — Validation and Error Handling

- Invalid input must return a clear, consistent client-facing error.
- Missing resources and unauthorized access must be handled deliberately.
- Responses must not reveal passwords, secrets, stack traces, or sensitive implementation details.
- Data integrity must be enforced in the application and, where practical, through database constraints.

### FR-10 — API Documentation

The API must document endpoints, authentication, permissions, request and response formats, filtering, pagination, and common errors.

## 5. Non-Functional Requirements

### Security
- Secrets and production credentials must not be committed to version control.
- Production settings must disable debug mode and configure allowed hosts appropriately.
- Object-level authorization must prevent insecure direct object reference vulnerabilities.

### Data Integrity
- Foreign-key relationships must be explicit.
- A user can have at most one membership record per project.
- Task assignment must follow the project-membership rules.

### Maintainability
- Modules and functions must have clear responsibilities.
- Business rules must be understandable and documented.
- Dependencies and setup instructions must be reproducible.

### Testability
Automated tests must cover core behavior, invalid input, permissions, archiving, and important data-integrity rules.

### Deployment
A developer must be able to configure, run, test, and deploy the application using documented instructions.

## 6. Definition of Done

The MVP is complete when:

1. The main project, membership, and task workflows work.
2. Authorization rules are enforced and tested.
3. Project archiving and restoration work without losing related data.
4. Database migrations can be applied to a clean database.
5. Automated tests pass.
6. API documentation and setup instructions are available.
7. CI executes the test suite.
8. The application is deployed to a production-like environment without exposing secrets.