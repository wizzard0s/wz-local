param([string]$Base = "http://localhost:8080/api/v1")

$h = @{ "Content-Type" = "application/json" }
$token = (Invoke-RestMethod -Uri "$Base/auth/login" -Method Post -Headers $h `
  -Body '{"email":"admin@wztrack.io","password":"admin1234"}').access_token
$h["Authorization"] = "Bearer $token"
Write-Host "[1/6] Auth OK"

# ── Project ──────────────────────────────────────────────────────────────────
$proj = Invoke-RestMethod -Uri "$Base/projects/" -Method Post -Headers $h -Body (@{
  key         = "WZT"
  name        = "WZTrack Platform"
  description = "Full lifecycle project tracking platform covering issue management, requirements, QA, test cases and traceability."
} | ConvertTo-Json)
$pid = $proj.id
Write-Host "[2/6] Project created: $pid"

# ── Workflow states ──────────────────────────────────────────────────────────
$stateDefs = @(
  @{name="Backlog";     category="unstarted"; position=0; color="#6b7280"},
  @{name="To Do";       category="unstarted"; position=1; color="#3b82f6"},
  @{name="In Progress"; category="started";   position=2; color="#f59e0b"},
  @{name="In Review";   category="started";   position=3; color="#8b5cf6"},
  @{name="Done";        category="done";      position=4; color="#10b981"},
  @{name="Cancelled";   category="cancelled"; position=5; color="#ef4444"}
)
$st = @{}
foreach ($s in $stateDefs) {
  $r = Invoke-RestMethod -Uri "$Base/projects/$pid/states" -Method Post -Headers $h -Body ($s | ConvertTo-Json)
  $st[$s.name] = $r.id
}
Write-Host "[3/6] Workflow states: $($st.Keys -join ', ')"

# ── BA Requirements ──────────────────────────────────────────────────────────
$reqs = @(
  @{
    title               = "User authentication and role-based access control"
    description         = "The platform must authenticate all users with email and password credentials using RS256 JWT tokens. Access to features must be gated by user role: admin, manager, developer, and viewer."
    acceptance_criteria = "- Admin can access all features.`n- Viewer role is read-only.`n- Expired tokens are rejected with 401.`n- Passwords are stored as bcrypt hashes."
    priority            = "must"
    status              = "approved"
  },
  @{
    title               = "Project creation and membership management"
    description         = "Users with admin or manager role must be able to create projects, assign a unique project key, and add or remove members with specific roles."
    acceptance_criteria = "- Project key must be unique and uppercase alphanumeric.`n- Admin sees all projects. Non-admin sees only member projects.`n- Member roles: owner, manager, developer, viewer."
    priority            = "must"
    status              = "approved"
  },
  @{
    title               = "Issue board with configurable workflow states"
    description         = "Each project must have a Kanban-style board where issues can be moved through configurable workflow states grouped by category: unstarted, started, done, cancelled."
    acceptance_criteria = "- States are per-project and configurable.`n- Issues can be filtered by assignee, priority, type, and sprint.`n- Board reflects real-time state changes."
    priority            = "must"
    status              = "approved"
  },
  @{
    title               = "Requirements management with version history"
    description         = "The platform must allow business analysts to capture, version, and approve requirements. Each change must produce a new version record without losing prior versions."
    acceptance_criteria = "- Requirements have unique IDs (prefix-NNN format).`n- Every update increments version number.`n- Status flow: draft -> in-review -> approved -> deprecated.`n- Approved requirements can be linked to issues for traceability."
    priority            = "must"
    status              = "approved"
  },
  @{
    title               = "Test case management and QA gate"
    description         = "Developers and QA engineers must be able to create test plans, write test cases linked to requirements, and record test runs. A QA gate must block issues from moving to Done without a passing test run."
    acceptance_criteria = "- Test cases link to requirements via traceability matrix.`n- Test run statuses: pass, fail, blocked, skipped.`n- Issue cannot be set to a Done state without at least one passing test run linked."
    priority            = "must"
    status              = "approved"
  },
  @{
    title               = "Wiki for project documentation"
    description         = "Each project must provide a rich wiki where team members can maintain living documentation including architecture decisions, runbooks, and onboarding guides."
    acceptance_criteria = "- Pages support Markdown content.`n- Page slugs are auto-generated from titles.`n- All changes are versioned.`n- Pages are scoped per project."
    priority            = "should"
    status              = "approved"
  },
  @{
    title               = "File attachment support on issues"
    description         = "Users must be able to attach files (screenshots, logs, specs) to issues. The platform must enforce a max file size and store attachments securely on the server."
    acceptance_criteria = "- Max issue attachment: 10 MB.`n- Supported MIME types: image/*, application/pdf, text/*.`n- Attachments are accessible via authenticated download URL."
    priority            = "should"
    status              = "draft"
  },
  @{
    title               = "Reporting and traceability matrix"
    description         = "The platform must provide a traceability view that maps requirements to linked issues and test cases, allowing stakeholders to assess coverage and progress at a glance."
    acceptance_criteria = "- Matrix shows requirement -> issue -> test case linkage.`n- Coverage percentage shown per requirement.`n- Exportable to CSV."
    priority            = "could"
    status              = "draft"
  }
)

foreach ($req in $reqs) {
  Invoke-RestMethod -Uri "$Base/requirements/project/$pid" -Method Post -Headers $h -Body ($req | ConvertTo-Json) | Out-Null
}
Write-Host "[4/6] $($reqs.Count) BA requirements created"

# ── Wiki pages ───────────────────────────────────────────────────────────────
$pages = @(
  @{
    title   = "Project overview"
    content = "# WZTrack Platform`n`n## What is WZTrack?`n`nWZTrack is a full lifecycle project tracking platform built for software teams. It covers issue management, requirements engineering, test case management, QA gates, traceability, and a project wiki.`n`n## Goals`n`n- Provide a single source of truth for requirements, work items, and quality evidence.`n- Enforce a traceable path from business requirement to tested, deployed feature.`n- Keep documentation close to the work with a per-project wiki.`n`n## Stakeholders`n`n| Role | Name | Responsibility |`n|---|---|---|`n| Product Owner | TBD | Approves requirements and priorities |`n| BA Lead | TBD | Writes and maintains requirements |`n| Tech Lead | TBD | Owns architecture decisions |`n| QA Lead | TBD | Owns test plans and QA gate policy |"
  },
  @{
    title   = "Architecture decision record — technology stack"
    content = "# ADR-001: Technology stack selection`n`n**Date:** 2026-04-09  **Status:** Accepted`n`n## Context`n`nThe team needed a modern, maintainable stack for WZTrack that supports async operations, strong type safety, and a clean API-first architecture.`n`n## Decision`n`n| Layer | Technology | Rationale |`n|---|---|---|`n| API | FastAPI + Python 3.12 | Async-native, auto OpenAPI docs, type safety via Pydantic |`n| Database | PostgreSQL 16 | JSONB support, mature async driver (asyncpg) |`n| ORM | SQLAlchemy 2 (async) | Type-safe mapped columns, migration support via Alembic |`n| Auth | RS256 JWT | Stateless, supports key rotation |`n| Frontend | React 18 + TypeScript | Component model, strong ecosystem |`n| UI Components | Ant Design 5 | Comprehensive, accessible component set |`n| Containerisation | Docker Compose | Portable, reproducible dev environment |`n`n## Consequences`n`n- All API responses are schema-validated by Pydantic.`n- Frontend calls the API exclusively via `/api/v1` — no direct DB access.`n- Migrations are managed with Alembic; no ad-hoc schema changes."
  },
  @{
    title   = "Development setup guide"
    content = "# Development setup guide`n`n## Before you begin`n`n- Docker Desktop or Rancher Desktop installed and running`n- Git configured with your credentials`n- Port 8080 and 8000 available on your machine`n`n## Steps`n`n1. Clone the repository.`n2. Copy `.env.example` to `.env` and fill in any required values.`n3. Run `docker compose up --build` from the `wztrack/` directory.`n4. Access the app at `http://localhost:8080`.`n5. Log in with the seed admin account: `admin@wztrack.io` / `admin1234`.`n6. Change the admin password immediately after first login.`n`n## Port reference`n`n| Service | Host port | Container port |`n|---|---|---|`n| Frontend (nginx) | 8080 | 80 |`n| API (uvicorn) | 8000 | 8000 |`n| PostgreSQL | not exposed | 5432 |`n`n## Troubleshooting`n`n- **Docker context wrong:** run `docker context use default` if the daemon is unreachable.`n- **Port 80 conflict:** Rancher Desktop owns port 80 on Windows — use 8080.`n- **bcrypt error on startup:** ensure `bcrypt==3.2.2` is pinned in `requirements.txt`."
  },
  @{
    title   = "QA gate policy"
    content = "# QA gate policy`n`n## Purpose`n`nThis policy defines the quality gate that all issues must pass before they can move to a Done workflow state.`n`n## Gate rule`n`nAn issue cannot transition to any workflow state with category `done` unless it has at least one linked test run with status `pass`.`n`n## Workflow`n`n1. Developer creates issue and writes code.`n2. QA engineer creates a test case and links it to the issue.`n3. QA engineer records a test run against the test case.`n4. If the run passes, the developer or QA can move the issue to Done.`n5. If no passing run exists, the API returns HTTP 422 with code `QA_GATE_BLOCKED`.`n`n## Exceptions`n`nExceptions to this policy must be approved by the QA Lead and documented in a comment on the issue before the state is changed manually via a DB update."
  }
)

foreach ($page in $pages) {
  Invoke-RestMethod -Uri "$Base/wiki/project/$pid" -Method Post -Headers $h -Body ($page | ConvertTo-Json) | Out-Null
}
Write-Host "[5/6] $($pages.Count) wiki pages created"

# ── Dev board stories & tasks ────────────────────────────────────────────────
$todoId   = $st["To Do"]
$inProgId = $st["In Progress"]
$doneId   = $st["Done"]
$backlogId = $st["Backlog"]

$issues = @(
  # Epics / Stories
  @{title="[EPIC] Authentication & user management";     type="epic";  priority="urgent"; status_id=$todoId;   story_points=0;  description="Covers user registration, login, JWT issuance, refresh, logout, and role-based access control."},
  @{title="[EPIC] Project management";                   type="epic";  priority="high";   status_id=$todoId;   story_points=0;  description="Project CRUD, membership management, and per-project workflow state configuration."},
  @{title="[EPIC] Issue board";                          type="epic";  priority="high";   status_id=$inProgId; story_points=0;  description="Issue creation, Kanban board UI, sprint management, filtering and search."},
  @{title="[EPIC] Requirements management";              type="epic";  priority="high";   status_id=$inProgId; story_points=0;  description="BA requirements CRUD with versioning, status workflow, and traceability links."},
  @{title="[EPIC] Test case management & QA gate";       type="epic";  priority="high";   status_id=$todoId;   story_points=0;  description="Test plans, test cases, test runs, and QA gate enforcement on Done transitions."},
  @{title="[EPIC] Wiki";                                 type="epic";  priority="medium"; status_id=$doneId;   story_points=0;  description="Per-project wiki with Markdown content, versioning, and slugged URLs."},

  # Dev stories
  @{title="Implement RS256 JWT auth endpoints";          type="story"; priority="urgent"; status_id=$doneId;   story_points=5;  description="POST /auth/login, /auth/refresh, /auth/logout — stateless RS256 tokens with 60-min access + 30-day refresh."},
  @{title="Implement user registration";                 type="story"; priority="high";   status_id=$doneId;   story_points=3;  description="POST /auth/register — validate email, hash password with bcrypt, return token pair."},
  @{title="Project CRUD API";                            type="story"; priority="high";   status_id=$doneId;   story_points=5;  description="GET /projects, POST /projects, GET /projects/{id}, PATCH /projects/{id}, DELETE /projects/{id}."},
  @{title="Configurable workflow states per project";    type="story"; priority="high";   status_id=$doneId;   story_points=3;  description="POST /projects/{id}/states — allow each project to define its own Kanban columns with category mapping."},
  @{title="Issue CRUD with sequence numbers";            type="story"; priority="high";   status_id=$inProgId; story_points=5;  description="Issues get auto-incremented sequence numbers per project (WZT-1, WZT-2…). Supports type, priority, assignee, sprint, story points."},
  @{title="Requirements CRUD with version history";      type="story"; priority="high";   status_id=$inProgId; story_points=8;  description="Every requirement update creates a RequirementVersion record. req_id auto-generated as {PROJECT_KEY}-R{N}."},
  @{title="Wiki pages CRUD with versioning";             type="story"; priority="medium"; status_id=$doneId;   story_points=3;  description="Markdown wiki pages per project. Auto-slug from title. All edits versioned."},
  @{title="Test plan and test case management";          type="story"; priority="high";   status_id=$todoId;   story_points=8;  description="Test plans scoped to project. Test cases linked to requirements. Supports manual and automated case types."},
  @{title="Test run recording and QA gate";              type="story"; priority="high";   status_id=$todoId;   story_points=5;  description="Record pass/fail/blocked/skipped runs against test cases. Enforce QA gate: no Done without passing run."},
  @{title="Traceability matrix API";                     type="story"; priority="medium"; status_id=$todoId;   story_points=5;  description="GET /traceability/project/{id} — returns requirement -> issue -> test case linkage map with coverage stats."},
  @{title="File attachment upload on issues";            type="story"; priority="medium"; status_id=$backlogId; story_points=5; description="Multipart upload endpoint. Max 10 MB. Stored in /uploads volume. Authenticated download URL."},
  @{title="Frontend: login page";                        type="story"; priority="urgent"; status_id=$doneId;   story_points=2;  description="Ant Design login form. Posts to /api/v1/auth/login. Stores JWT in Zustand store. Redirects to dashboard."},
  @{title="Frontend: project list and creation";         type="story"; priority="high";   status_id=$inProgId; story_points=3;  description="List user's projects. Create project modal with key + name validation."},
  @{title="Frontend: Kanban board";                      type="story"; priority="high";   status_id=$todoId;   story_points=8;  description="Drag-and-drop Kanban board grouped by workflow state. Swimlane by assignee option. Real-time state update via PATCH."},
  @{title="Frontend: requirements list and editor";      type="story"; priority="high";   status_id=$todoId;   story_points=5;  description="Table view of requirements with status badges. Inline editor for description and acceptance criteria."},
  @{title="Frontend: wiki reader and editor";            type="story"; priority="medium"; status_id=$todoId;   story_points=3;  description="Render Markdown wiki pages. Inline edit mode with preview. Page tree navigation."},

  # Tasks
  @{title="Pin bcrypt==3.2.2 to fix passlib compatibility";  type="task"; priority="urgent"; status_id=$doneId;  story_points=1; description="passlib 1.7.4 + bcrypt 4.x incompatibility — bcrypt 4 rejects 73-byte wrap-bug detection password. Pin to 3.2.2."},
  @{title="Fix FastAPI 204 route -> None annotation issue";   type="task"; priority="high";   status_id=$doneId;  story_points=1; description="FastAPI interprets -> None on 204 routes as NoneType response model, triggering assertion. Remove return annotations."},
  @{title="Fix JWT PEM key double-escape in .env";            type="task"; priority="high";   status_id=$doneId;  story_points=1; description="pydantic-settings reads \\n from .env as literal backslash+n. config.py jwt_private_key_pem must replace \\\\n not \\n."},
  @{title="Switch frontend port from 80 to 8080";             type="task"; priority="high";   status_id=$doneId;  story_points=1; description="Rancher Desktop host-switch process owns port 80 on Windows. Map nginx to 8080:80 and update CORS_ORIGINS."},
  @{title="Change admin seed email from .local to .io TLD";   type="task"; priority="high";   status_id=$doneId;  story_points=1; description="email-validator rejects .local as a reserved TLD. Changed admin email to admin@wztrack.io."},
  @{title="Set up Alembic migrations";                        type="task"; priority="medium"; status_id=$backlogId; story_points=3; description="Replace auto create_all on startup with proper Alembic migration chain. Required before any production deployment."},
  @{title="Add token blocklist for logout invalidation";      type="task"; priority="medium"; status_id=$backlogId; story_points=3; description="Current logout is stateless. Add Redis-backed blocklist so revoked tokens are rejected before expiry."},
  @{title="Write Pytest integration test suite";              type="task"; priority="medium"; status_id=$backlogId; story_points=5; description="Cover auth, project CRUD, issue CRUD, QA gate, and traceability endpoints with async test client."}
)

$created = 0
foreach ($issue in $issues) {
  $body = $issue | ConvertTo-Json
  Invoke-RestMethod -Uri "$Base/issues/project/$pid" -Method Post -Headers $h -Body $body | Out-Null
  $created++
}
Write-Host "[6/6] $created issues created on the dev board"
Write-Host ""
Write-Host "Done. Open http://localhost:8080 to view the project."
