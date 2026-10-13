# TaskForge API — Data Model

**Version:** 1.0  
**Database:** PostgreSQL  
**ORM:** Django ORM

## 1. Design Principles

- Use Django's built-in user model through `settings.AUTH_USER_MODEL`.
- Use explicit foreign-key relationships.
- Use a separate membership table because membership has its own lifecycle and permissions.
- Use soft deletion for projects through an archive timestamp.
- Use database constraints for rules that can be enforced locally in the database.
- Validate cross-table business rules in the application and test them.

## 2. Entities

### 2.1 User

Use Django's configured user model rather than creating a custom user table without a demonstrated need.

Relevant fields are provided by the configured user model, including a primary key, username or other login identifier, email where configured, and password hash.

Relationships:

- A user can own multiple projects.
- A user can have multiple project memberships.
- A user can be assigned multiple tasks.

### 2.2 Project

| Field | Type / rule | Purpose |
|---|---|---|
| `id` | Primary key | Unique project identifier |
| `owner_id` | Foreign key to User, required | Project owner |
| `name` | String, required | Project name |
| `description` | Text, optional | Project details |
| `created_at` | Timestamp | Creation time |
| `updated_at` | Timestamp | Last update time |
| `archived_at` | Nullable timestamp | Archive state |

Rules:

- `archived_at = NULL` means the project is active.
- A non-null `archived_at` means the project is archived.
- Archiving does not delete tasks or memberships.
- Only the owner can archive or restore the project.
- Default active-project queries must exclude archived projects.

### 2.3 ProjectMembership

This entity represents a registered user's membership in a project.

| Field | Type / rule | Purpose |
|---|---|---|
| `id` | Primary key | Unique membership identifier |
| `project_id` | Foreign key to Project | Associated project |
| `user_id` | Foreign key to User | Associated user |
| `joined_at` | Timestamp | Membership creation time |

Rules:

- A unique constraint on `(project_id, user_id)` prevents duplicate membership.
- The project owner is represented by `Project.owner_id`; they do not need a duplicate membership record.
- Removing a membership revokes the user's member-level access.
- An owner cannot be removed through the member-removal operation.
- Only the owner can manage membership in the MVP.

There is no `role` field in this table for the MVP because members have one uniform member role. Ownership is represented by `Project.owner_id`. A separate role field can be added if additional member roles become necessary.

### 2.4 Task

| Field | Type / rule | Purpose |
|---|---|---|
| `id` | Primary key | Unique task identifier |
| `project_id` | Foreign key to Project | Parent project |
| `title` | String, required | Task title |
| `description` | Text, optional | Task details |
| `status` | Choice field, default `todo` | Current task status |
| `assignee_id` | Nullable foreign key to User | Assigned user |
| `created_at` | Timestamp | Creation time |
| `updated_at` | Timestamp | Last update time |
| `due_date` | Nullable date | Optional deadline |

Allowed status values:

- `todo`
- `in_progress`
- `done`

Rules:

- Every task belongs to exactly one project.
- A task may be unassigned.
- If assigned, the assignee must be the project's owner or a current project member.
- Only the project owner or the task's current assignee can edit the task.
- Task mutations are blocked while the project is archived.

## 3. Relationships

- User `1 → many` Project through `Project.owner_id`.
- User `many ↔ many` Project through `ProjectMembership`.
- Project `1 → many` Task.
- User `1 → many` Task through the optional assignee relationship.

The owner-to-project relationship and the membership relationship are separate. A user can own one project and belong to another.

## 4. Deletion and Retention

- Project deletion is implemented as archiving, not physical deletion.
- Existing tasks and memberships remain attached to an archived project.
- Restoring a project makes it active again without recreating its related data.
- Removing a membership does not automatically delete tasks assigned to that user.
- If a former member remains assigned to a task, they no longer have member access. The owner should reassign that task if necessary.

## 5. Integrity Constraints

Enforce these rules where practical:

1. `Project.owner_id` must reference an existing user.
2. `ProjectMembership.project_id` and `ProjectMembership.user_id` must reference existing records.
3. `(project_id, user_id)` must be unique in `ProjectMembership`.
4. `Task.project_id` must reference an existing project.
5. `Task.assignee_id` may be null; if non-null, it must reference an existing user.
6. Task status must be one of the allowed values.

The rule that an assignee must belong to the same project is a cross-table rule. It requires application-level validation and automated tests unless a more advanced database enforcement strategy is deliberately introduced.

## 6. Indexing Considerations

Start with the foreign-key indexes provided by Django and PostgreSQL. Add targeted indexes only when query patterns justify them.

Potential candidates after measurement:

- Tasks by project and status.
- Tasks by assignee.
- Active projects by owner and archive state.

Do not add indexes indiscriminately: they consume storage and add overhead to writes.

## 7. Open Technical Considerations

Before production hardening, review:

- Whether task deletion should follow the same authorization policy as task editing.
- Whether project owners need a membership-history record.
- Whether reassignment and membership removal need transactional handling.
- Whether task activity history is necessary.
- Whether project names need uniqueness within a user or globally.

These are deliberate future review points, not reasons to expand the MVP now.