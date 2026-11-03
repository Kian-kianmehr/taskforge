# TaskForge API

All endpoints under `/api/` require a JWT access token in the `Authorization: Bearer <access_token>` header.

## Projects

- `GET /api/projects/` — list projects visible to the caller; active projects by default.
- `POST /api/projects/` — create a project; caller becomes owner.
- `GET /api/projects/{id}/` — retrieve a visible project.
- `PATCH/PUT /api/projects/{id}/` — update; owner only.
- `DELETE /api/projects/{id}/` — archive; owner only.
- `POST /api/projects/{id}/archive/` and `/restore/` — archive or restore.
- `GET /api/projects/{id}/members/` — list members.
- `POST /api/projects/{id}/members/` — add an active registered user by email; owner only.
- `DELETE /api/projects/{id}/members/?membership_id={id}` — remove member; owner only.

Pass `include_archived=true` to list archived projects too. Create project body: `{"name":"Website redesign","description":"Refresh the website"}`. Add member body: `{"email":"member@example.com"}`.

## Tasks

- `GET /api/tasks/` — list accessible tasks.
- `POST /api/tasks/` — create task.
- `GET /api/tasks/{id}/` — retrieve task.
- `PATCH/PUT /api/tasks/{id}/` — update; owner or current assignee.
- `DELETE /api/tasks/{id}/` — delete; project owner only.

Example task body:

```json
{"project":1,"title":"Implement login","description":"Add validation","status":"todo","assignee_id":2,"due_date":"2027-01-15"}
```

Statuses: `todo`, `in_progress`, `done`. Assignee must be project owner or current member. Omit `assignee_id` or use null for unassigned tasks.

Task filters: `project`, `status`, `assignee`, `due_before`, `search` (title/description), and `ordering` (`created_at`, `due_date`, `title`, `status`, optionally prefixed with `-`). Pagination uses `page` and `page_size` (maximum 100), returning `count`, `next`, `previous`, and `results`.

## Authorization

Only owners and members can view project/task data. Members cannot change project settings or membership. Owners and members can create tasks. Only owner or current assignee can update a task; only owner can delete it. Archived projects reject mutations and retain related records. Inaccessible detail resources return 404; validation errors return 400, permission failures 403, and unauthenticated requests 401.
