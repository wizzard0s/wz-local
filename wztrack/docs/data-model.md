# WZTrack — Data Model

**Document ID:** DM-WZTRACK-001
**Version:** 1.0
**Status:** Approved

---

## Before you begin

All tables live in the PostgreSQL `wztrack` schema. Every table has `id` (UUID PK), `created_at`, `updated_at`, and `deleted_at` (soft delete). Queries always filter `WHERE deleted_at IS NULL`.

---

## 1. Users and authentication

### `wztrack.users`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| email | varchar(255) | UNIQUE NOT NULL |
| display_name | varchar(150) | NOT NULL |
| password_hash | varchar(255) | bcrypt hash |
| role | varchar(50) | admin / manager / developer / qa / viewer |
| is_active | boolean | default true |
| created_at | timestamptz | NOT NULL, default now() |
| updated_at | timestamptz | NOT NULL, default now() |
| deleted_at | timestamptz | NULL = active |

### `wztrack.sessions`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK → users.id |
| token_hash | varchar(255) | SHA-256 of refresh token |
| expires_at | timestamptz | 30 days from issue |
| created_at | timestamptz | |
| revoked_at | timestamptz | NULL = valid |

---

## 2. Projects and membership

### `wztrack.projects`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| key | varchar(20) | UNIQUE — e.g. CHAT, FLOW |
| name | varchar(255) | NOT NULL |
| description | text | |
| owner_id | uuid | FK → users.id |
| status | varchar(50) | active / archived |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| deleted_at | timestamptz | |

### `wztrack.project_members`

| Column | Type | Notes |
|---|---|---|
| project_id | uuid | FK → projects.id, PK |
| user_id | uuid | FK → users.id, PK |
| role | varchar(50) | project-level override |
| joined_at | timestamptz | |

### `wztrack.workflow_states`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| project_id | uuid | FK → projects.id |
| name | varchar(100) | e.g. "In Review" |
| category | varchar(50) | backlog / in_progress / review / done / cancelled |
| position | int | sort order on board |
| color | varchar(7) | hex colour for UI |
| created_at | timestamptz | |

---

## 3. Issues

### `wztrack.issues`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| project_id | uuid | FK → projects.id |
| sequence_number | int | auto-increment per project |
| title | varchar(500) | NOT NULL |
| description | text | rich text |
| type | varchar(50) | epic / story / task / bug / subtask |
| priority | varchar(50) | urgent / high / medium / low |
| status_id | uuid | FK → workflow_states.id |
| assignee_id | uuid | FK → users.id, nullable |
| reporter_id | uuid | FK → users.id |
| sprint_id | uuid | FK → sprints.id, nullable |
| parent_id | uuid | FK → issues.id, subtask only |
| story_points | int | |
| due_date | date | |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| deleted_at | timestamptz | |

### `wztrack.sprints`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| project_id | uuid | FK → projects.id |
| name | varchar(255) | |
| goal | text | |
| status | varchar(50) | draft / active / completed |
| start_date | date | |
| end_date | date | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `wztrack.issue_links`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| source_id | uuid | FK → issues.id |
| target_id | uuid | FK → issues.id |
| link_type | varchar(50) | blocks / is_blocked_by / relates_to / duplicates |

### `wztrack.comments`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| issue_id | uuid | FK → issues.id |
| author_id | uuid | FK → users.id |
| body | text | |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| deleted_at | timestamptz | |

### `wztrack.attachments`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| issue_id | uuid | FK → issues.id, nullable |
| test_result_id | uuid | FK → test_results.id, nullable |
| uploaded_by | uuid | FK → users.id |
| filename | varchar(255) | original filename |
| storage_path | varchar(500) | relative path on disk |
| mime_type | varchar(100) | |
| size_bytes | bigint | |
| created_at | timestamptz | |

### `wztrack.audit_log`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| entity_type | varchar(100) | issue / requirement / test_run |
| entity_id | uuid | |
| action | varchar(100) | state_transition / qa_gate_override / etc. |
| actor_id | uuid | FK → users.id |
| old_value | jsonb | |
| new_value | jsonb | |
| note | text | override reason |
| created_at | timestamptz | |

---

## 4. Requirements

### `wztrack.requirements`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| project_id | uuid | FK → projects.id |
| sequence_number | int | auto-increment per project (never reused) |
| req_id | varchar(50) | computed: REQ-{KEY}-{seq} |
| title | varchar(500) | |
| description | text | |
| acceptance_criteria | text | |
| priority | varchar(50) | must / should / could / wont |
| status | varchar(50) | draft / approved / implemented / verified |
| created_by | uuid | FK → users.id |
| current_version | int | increments on each edit |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| deleted_at | timestamptz | |

### `wztrack.requirement_versions`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| requirement_id | uuid | FK → requirements.id |
| version | int | |
| title | varchar(500) | snapshot |
| description | text | snapshot |
| acceptance_criteria | text | snapshot |
| changed_by | uuid | FK → users.id |
| changed_at | timestamptz | |
| change_note | text | |

### `wztrack.requirement_issues`

| Column | Type | Notes |
|---|---|---|
| requirement_id | uuid | FK → requirements.id, PK |
| issue_id | uuid | FK → issues.id, PK |

---

## 5. Wiki

### `wztrack.wiki_pages`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| project_id | uuid | FK → projects.id |
| parent_id | uuid | FK → wiki_pages.id, nullable |
| slug | varchar(300) | URL-safe, unique per project |
| title | varchar(500) | |
| content | text | rich text (TipTap JSON or Markdown) |
| template_type | varchar(50) | blank / brd / sdd / meeting / decision / adr |
| current_version | int | |
| created_by | uuid | FK → users.id |
| updated_by | uuid | FK → users.id |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| deleted_at | timestamptz | |

### `wztrack.wiki_page_versions`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| page_id | uuid | FK → wiki_pages.id |
| version | int | |
| title | varchar(500) | snapshot |
| content | text | snapshot |
| changed_by | uuid | FK → users.id |
| changed_at | timestamptz | |

---

## 6. Test management

### `wztrack.test_plans`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| project_id | uuid | FK → projects.id |
| sprint_id | uuid | FK → sprints.id, nullable |
| name | varchar(255) | |
| description | text | |
| status | varchar(50) | draft / active / completed |
| created_by | uuid | FK → users.id |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| deleted_at | timestamptz | |

### `wztrack.test_cases`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| project_id | uuid | FK → projects.id |
| test_plan_id | uuid | FK → test_plans.id |
| title | varchar(500) | |
| preconditions | text | |
| steps | jsonb | `[{order, action, expected}]` |
| expected_result | text | |
| created_by | uuid | FK → users.id |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| deleted_at | timestamptz | |

### `wztrack.test_runs`

| Column | Type | Notes |
|---|---|---|
| id | uuid | PK |
| test_case_id | uuid | FK → test_cases.id |
| issue_id | uuid | FK → issues.id, nullable |
| status | varchar(50) | pass / fail / blocked / skipped |
| notes | text | |
| executed_by | uuid | FK → users.id |
| executed_at | timestamptz | |
| created_at | timestamptz | |

### `wztrack.requirement_test_cases`

| Column | Type | Notes |
|---|---|---|
| requirement_id | uuid | FK → requirements.id, PK |
| test_case_id | uuid | FK → test_cases.id, PK |

---

## 7. Key indexes

```sql
-- Issues
CREATE INDEX idx_issues_project_status ON wztrack.issues(project_id, status_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_issues_assignee ON wztrack.issues(assignee_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_issues_sprint ON wztrack.issues(sprint_id) WHERE deleted_at IS NULL;

-- Requirements
CREATE UNIQUE INDEX idx_requirements_seq ON wztrack.requirements(project_id, sequence_number);

-- Audit log
CREATE INDEX idx_audit_entity ON wztrack.audit_log(entity_type, entity_id);

-- Sessions
CREATE INDEX idx_sessions_user ON wztrack.sessions(user_id) WHERE revoked_at IS NULL;
CREATE UNIQUE INDEX idx_sessions_token ON wztrack.sessions(token_hash);

-- Wiki full-text search
CREATE INDEX idx_wiki_fts ON wztrack.wiki_pages USING gin(to_tsvector('english', title || ' ' || content));
```
