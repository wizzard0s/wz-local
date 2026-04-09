"""
Patch script — adds new requirements to WZT and updates all existing issues
in both WZT and DEVENV with the enriched story fields (decisions, investigations,
test_requirements, uat_criteria).

Run: python patch_issues.py
"""
import json
import sys
import os
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@wztrack.io"
ADMIN_PASSWORD = "admin1234"


def api(method, path, body=None, token=None):
    url = BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        print(f"  ERROR {exc.code} {method} {path}: {exc.read().decode()[:300]}")
        return None


def login():
    body = json.dumps({"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).encode()
    req = urllib.request.Request(
        BASE_URL + "/auth/login",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())["access_token"]
    except urllib.error.HTTPError as exc:
        print(f"Login failed: {exc.read().decode()}")
        sys.exit(1)


def get_project_id(key, token):
    resp = api("GET", "/projects/", token=token) or {}
    for p in resp.get("data", []):
        if p["key"] == key:
            return p["id"]
    return None


def get_all_issues(project_id, token):
    issues = []
    page = 1
    while True:
        resp = api("GET", f"/issues/project/{project_id}?page={page}&page_size=100", token=token) or {}
        batch = resp.get("data", [])
        issues.extend(batch)
        meta = resp.get("meta", {})
        if page >= meta.get("pages", 1):
            break
        page += 1
    return issues


# ---------------------------------------------------------------------------
# New WZT requirements — story standard
# ---------------------------------------------------------------------------
WZT_NEW_REQUIREMENTS = [
    {
        "title": "Enriched story format: decisions, investigations, test requirements, UAT criteria",
        "description": "Every story and task must carry structured content beyond a title and description. The issue model must provide dedicated fields for open decisions that need to be made, investigations required before work can begin, explicit test requirements describing what must be verified, and UAT acceptance criteria that the product owner will use to sign off. These fields are set when a story is created or refined and updated as work progresses.",
        "acceptance_criteria": "- Issue model exposes `decisions`, `investigations`, `test_requirements`, `uat_criteria` as nullable text fields.\n- All four fields are editable via PATCH /issues/{id}.\n- All four fields are returned in GET /issues/{id} and the list endpoint.\n- Fields are visible in the issue detail view in the frontend.\n- OpenAPI docs accurately describe each field.",
        "priority": "must",
        "_status": "approved"
    },
    {
        "title": "UAT sign-off action on issues",
        "description": "A story cannot be marked done without explicit user acceptance sign-off by a product owner, manager, or admin. The sign-off action records who approved it, when, and optionally why. It is a first-class action separate from a comment — it produces a permanent, unforgeable audit entry.",
        "acceptance_criteria": "- POST /issues/{id}/uat-signoff sets uat_approved=true, uat_approved_by (user id), and uat_approved_at (timestamp).\n- Only admin or manager roles can call the endpoint.\n- Calling the endpoint twice returns HTTP 409 Conflict.\n- The action is recorded in the audit log with action=uat_signoff.\n- uat_approved, uat_approved_by, and uat_approved_at appear in IssueOut.",
        "priority": "must",
        "_status": "approved"
    },
    {
        "title": "Done gate requires passing test run AND UAT sign-off",
        "description": "An issue may not transition to any workflow state with category 'done' unless two conditions are both met: at least one linked test run with status 'pass' exists, and the issue has been UAT signed off. Both conditions must fail independently so the error message tells the developer exactly what is missing.",
        "acceptance_criteria": "- PATCH /issues/{id} to a Done state with no passing test run returns HTTP 422 with code DONE_GATE_BLOCKED.\n- PATCH /issues/{id} to a Done state with no UAT sign-off returns HTTP 422 with code DONE_GATE_BLOCKED.\n- The message lists which conditions failed.\n- Admin and manager may supply override_reason to bypass the gate; the override is logged as done_gate_override in the audit log.",
        "priority": "must",
        "_status": "approved"
    },
    {
        "title": "Issue audit history endpoint",
        "description": "Every significant action on an issue must be accessible as a time-ordered audit trail. State transitions, UAT sign-offs, done gate overrides, and any action that writes to the audit log must appear in the issue history. This is the primary evidence record proving how and when a story was developed and accepted.",
        "acceptance_criteria": "- GET /issues/{id}/history returns all audit log entries for that issue ordered by created_at ascending.\n- Each entry includes: action, actor_id, old_value, new_value, note, created_at.\n- State transitions are always logged.\n- UAT sign-offs are always logged.\n- Done gate overrides are always logged.\n- The endpoint is accessible to any authenticated project member.",
        "priority": "must",
        "_status": "approved"
    },
    {
        "title": "Screenshot and file evidence attachments on issues",
        "description": "Developers and QA engineers must be able to attach evidence files to any issue. Attachments are the physical proof backing the audit trail — screenshots of working features, exported test reports, and signed-off documents. Without attachments the history is words only; with them it is verifiable evidence.",
        "acceptance_criteria": "- POST /issues/{id}/attachments accepts multipart/form-data uploads.\n- Accepted MIME types: image/png, image/jpeg, image/gif, image/webp, application/pdf, text/plain, text/csv.\n- Max file size: 10 MB per attachment.\n- GET /issues/{id}/attachments returns list with filename, mime_type, size_bytes, uploaded_by, created_at.\n- Files are served via an authenticated download URL.\n- Attachment list is included in the issue detail view.",
        "priority": "must",
        "_status": "draft"
    },
]

# ---------------------------------------------------------------------------
# Enriched issue content keyed by title (matched by startswith for safety)
# Each entry provides the four new fields for PATCH.
# ---------------------------------------------------------------------------
ISSUE_ENRICHMENT = {
    # ---- WZT issues -------------------------------------------------------
    "[EPIC] Authentication and user management": {
        "decisions": "- Use RS256 asymmetric JWT (not HS256) so public key can be shared with other services without exposing the signing secret.\n- Access token TTL: 60 minutes. Refresh token TTL: 30 days.\n- No session store in v1 — stateless auth only. Token blocklist deferred to post-v1.",
        "investigations": "- Confirm email-validator TLD restrictions — `.local` is rejected. Use `.io` or `.com` for seed accounts.\n- Investigate passlib + bcrypt version compatibility before pinning dependencies.",
        "test_requirements": "- Login with valid credentials returns access_token and refresh_token.\n- Login with wrong password returns HTTP 401.\n- Expired access token is rejected with HTTP 401.\n- Refresh with valid refresh_token issues new token pair.\n- Logout endpoint returns HTTP 204.",
        "uat_criteria": "- Product owner can log in with the seeded admin account.\n- Invalid credentials are rejected with a clear error message.\n- Session survives a page reload (token stored and re-used).\n- Logging out ends the session and requires re-login.",
    },
    "[EPIC] Project management": {
        "decisions": "- Project keys are uppercase alphanumeric, max 10 chars, unique across the instance.\n- Admin sees all projects. Non-admin sees only projects they are a member of.\n- Project deletion is a soft delete (deleted_at) — data is never permanently removed in v1.",
        "investigations": "- Determine whether project owner is always a member or a separate concept.",
        "test_requirements": "- POST /projects/ with duplicate key returns HTTP 409.\n- Non-admin cannot see projects they are not a member of.\n- PATCH /projects/{id} by non-owner returns HTTP 403.",
        "uat_criteria": "- Manager can create a project and see it in the list immediately.\n- Developer added as member can access the project; removing them removes access.\n- Project description and name can be edited by the owner.",
    },
    "[EPIC] Issue board": {
        "decisions": "- Issue sequence numbers are per-project (WZT-1, WZT-2) not global.\n- Board groups issues by workflow state columns.\n- Filtering by assignee, type, and priority in v1. Sprint filtering in v1 if sprint model is complete.",
        "investigations": "- Evaluate whether drag-and-drop state changes should go through the same PATCH endpoint (yes — keeps gate enforcement centralised).",
        "test_requirements": "- Issue sequence numbers are unique per project and auto-increment.\n- Board displays all non-deleted issues grouped by state.\n- Moving an issue to Done triggers the done gate check.",
        "uat_criteria": "- User can create an issue from the board and see it appear in the correct column.\n- Dragging an issue to Done without passing test run and UAT is blocked with an error message.\n- Filters narrow the visible issues correctly.",
    },
    "[EPIC] Requirements management": {
        "decisions": "- Requirements are versioned: every PATCH creates a RequirementVersion record. The current_version counter increments on every update.\n- Status flow: draft -> in-review -> approved -> deprecated. Only approved requirements are eligible for traceability links.\n- req_id format: {PROJECT_KEY}-R{N} (e.g. WZT-R001).",
        "investigations": "- Confirm whether requirements need their own approval workflow with designated approvers or if any manager/admin can approve.",
        "test_requirements": "- PATCH /requirements/{id} increments current_version.\n- Status transition from approved to draft is rejected.\n- req_id is unique per project and auto-generated.",
        "uat_criteria": "- BA can create a requirement in draft, submit for review, and approve it.\n- Each edit produces a new version visible in the version history.\n- Approved requirements are linkable to issues in the traceability view.",
    },
    "[EPIC] Test case management and QA gate": {
        "decisions": "- Test cases belong to a test plan which belongs to a project.\n- Test runs are linked to both a test case and an issue (the linkage is what enables the done gate check).\n- QA gate v1: at least one TestRun with status=pass linked to the issue. UAT sign-off is a separate, parallel requirement.",
        "investigations": "- Determine whether automated test cases need a different type field or can share the same model with type=automated.",
        "test_requirements": "- Test run with status=pass linked to issue allows Done transition (combined with UAT sign-off).\n- Test run with status=fail does not satisfy the gate.\n- Multiple test runs on the same case — only the most recent matters for gate evaluation (or any pass is sufficient).",
        "uat_criteria": "- QA engineer can create a test plan, add test cases, link them to requirements, and record a run.\n- After a passing run is recorded, the developer can attempt to move the issue to Done.\n- Without a passing run, Done transition is blocked with a clear message.",
    },
    "[EPIC] Wiki": {
        "decisions": "- Wikis are per-project. Cross-project links are plain URLs, not first-class references in v1.\n- Page slugs are auto-generated from titles (kebab-case, unique per project).\n- All edits are versioned (WikiPageVersion table).",
        "investigations": "- Confirm whether page hierarchy (parent_id) needs to be reflected in the URL slug or just in the sidebar tree.",
        "test_requirements": "- POST /wiki/project/{id} with duplicate title generates a unique slug (appends -2, -3 etc).\n- All page edits increment current_version.\n- Deleted pages are soft-deleted and not returned in list.",
        "uat_criteria": "- User can create a page, edit it, and see the version counter increment.\n- Page content renders as formatted Markdown in the reader.\n- Page tree shows parent-child relationships in the sidebar.",
    },
    "Implement RS256 JWT auth endpoints": {
        "decisions": "- Use python-jose for JWT encoding/decoding with RS256 algorithm.\n- Token payload: sub (user id), type (access|refresh), exp.\n- No JTI in v1 (blocklist deferred).",
        "investigations": "- Confirmed: python-jose supports RS256 with PEM keys loaded from string.\n- Confirmed: pydantic-settings reads `\\n` from .env as literal backslash+n — must double-escape in config.py replace call.",
        "test_requirements": "- POST /auth/login returns {access_token, refresh_token, token_type: bearer}.\n- POST /auth/refresh with valid refresh_token returns new pair.\n- POST /auth/refresh with access_token (wrong type) returns 401.\n- POST /auth/logout returns 204.",
        "uat_criteria": "- Admin can log in via the UI and access protected pages.\n- Token is stored in localStorage under the correct key.\n- Refreshing the browser does not log the user out.",
    },
    "Implement user registration": {
        "decisions": "- Registration is open in v1 (no invite-only). Any email can register.\n- Default role for self-registered users: developer.\n- Admin is seeded from ADMIN_EMAIL env var on first startup.",
        "investigations": "- Confirmed: email-validator rejects .local TLD. Seed email must use a publicly routable domain.",
        "test_requirements": "- POST /auth/register with valid email and password returns token pair.\n- POST /auth/register with duplicate email returns 409.\n- Registered user can immediately log in.",
        "uat_criteria": "- New user can register, log in, and see their profile.\n- Duplicate registration is rejected with a clear error.",
    },
    "Project CRUD API": {
        "decisions": "- Key is uppercased automatically on create.\n- Owner is set to the creating user (not a body field).\n- DELETE is a soft delete — issues and requirements are retained.",
        "investigations": "- No external dependencies — straightforward CRUD.",
        "test_requirements": "- GET /projects/ returns only projects the current user is a member of (unless admin).\n- POST /projects/ with duplicate key returns 409.\n- PATCH /projects/{id} by non-member returns 403.\n- DELETE /projects/{id} sets deleted_at.",
        "uat_criteria": "- Manager creates a project and sees it in the project list.\n- Project key appears in issue sequence numbers (WZT-1).\n- Editing project name is reflected immediately in the header.",
    },
    "Configurable workflow states per project": {
        "decisions": "- States have categories: unstarted, started, done, cancelled.\n- Category determines gate checks (done triggers the done gate).\n- States are ordered by position field, not by creation time.",
        "investigations": "- Confirmed: issue status_id is a FK to workflow_states. States cannot be deleted if any issues reference them.",
        "test_requirements": "- POST /projects/{id}/states creates a state scoped to that project.\n- States from project A do not appear in project B.\n- GET /projects/{id}/states returns states ordered by position.",
        "uat_criteria": "- Manager can add a custom state and see it appear as a board column.\n- Re-ordering states by position is reflected on the board.",
    },
    "Issue CRUD with auto sequence numbers": {
        "decisions": "- Sequence numbers are per-project and never reused even if an issue is deleted.\n- parent_id enables epic-story-task hierarchy.\n- type enum: epic, story, task, bug, spike.",
        "investigations": "- Sequence number generation: use MAX(sequence_number) + 1 inside the create transaction to avoid races.",
        "test_requirements": "- Two simultaneous issue creates in the same project produce unique sequence numbers.\n- Deleted issues do not reuse sequence numbers.\n- Parent issue must belong to the same project.",
        "uat_criteria": "- Created issue appears in the board with correct WZT-N number.\n- Story linked to an epic appears nested under the epic in the tree view.\n- Deleting an issue removes it from the board but the sequence gap is visible if numbers are shown.",
    },
    "Requirements CRUD with version history": {
        "decisions": "- Every PATCH (including status changes) creates a RequirementVersion.\n- current_version on the Requirement row reflects the latest version number.\n- change_note on the update body is stored with the version record.",
        "investigations": "- Confirmed: status transition rules — draft -> in-review -> approved -> deprecated only (no backwards transitions from approved).",
        "test_requirements": "- GET /requirements/{id} after two edits has current_version=2.\n- Version history endpoint returns all versions ordered ascending.\n- Backwards status transition (approved -> draft) returns 422.",
        "uat_criteria": "- BA edits a requirement and sees version number increment.\n- Each version shows what changed and who changed it.\n- Approved requirements can be linked to issues in the traceability view.",
    },
    "Wiki pages CRUD with versioning": {
        "decisions": "- Slug is auto-generated from title on create. If slug already exists, append -2, -3.\n- All edits (title or content) increment current_version.\n- Deletion is soft (deleted_at) — wiki is auditable.",
        "investigations": "- No blocking investigations.",
        "test_requirements": "- Creating a page with the same title as an existing page generates a unique slug.\n- PATCH /wiki/{id} increments current_version.\n- Deleted pages return 404.",
        "uat_criteria": "- User creates a page and immediately sees it in the wiki sidebar.\n- Editing saves correctly and version counter increments.\n- Pages render Markdown including tables and code blocks.",
    },
    "Test plan and test case management API": {
        "decisions": "- Test plans group test cases. A plan belongs to a project (and optionally a sprint).\n- Test cases can be linked to requirements via RequirementTestCase join table.\n- Test case steps are stored as JSON array: [{order, action, expected}].",
        "investigations": "- Determine whether a test case can belong to multiple plans (no — one plan per case in v1).\n- Confirm whether automated test cases need a separate runner integration (out of scope v1).",
        "test_requirements": "- POST /testcases/plans/project/{id} creates a plan scoped to the project.\n- POST /testcases/cases/plan/{id} creates a case with steps as JSON.\n- GET /testcases/cases/{id} returns the case with full steps array.\n- Link endpoint POST /testcases/links/requirement/{req_id}/case/{case_id} creates the join record.",
        "uat_criteria": "- QA engineer creates a test plan, adds test cases with steps, and links them to requirements.\n- Test case steps are visible in the detail view with numbered actions and expected results.\n- Traceability matrix shows requirement coverage once cases are linked.",
    },
    "Test run recording and QA gate enforcement": {
        "decisions": "- A test run is recorded against a case AND an issue.\n- Status values: pass, fail, blocked, skipped.\n- Any pass on any run linked to the issue satisfies the gate (not just the most recent).\n- PATCH /issues/{id} to a Done state checks: pass_count > 0 AND uat_approved=true.",
        "investigations": "- Confirm: does a second failing run after a passing run revoke Done eligibility? Decision: no, any historical pass is sufficient. Regression tracking is a separate concern.",
        "test_requirements": "- POST /testcases/runs/case/{id} with status=pass allows the linked issue to transition to Done (once UAT is also signed off).\n- POST /testcases/runs/case/{id} with status=fail does not block existing passes.\n- PATCH /issues/{id} to Done without any pass returns 422 DONE_GATE_BLOCKED.",
        "uat_criteria": "- QA records a passing test run and notifies the developer.\n- Developer can then move the issue to Done (after UAT sign-off).\n- Attempting Done without a pass shows a specific error in the UI.",
    },
    "Traceability matrix API": {
        "decisions": "- Matrix endpoint: GET /traceability/project/{id}\n- Response structure: list of requirements, each with linked issues and linked test cases (via RequirementTestCase).\n- Coverage = (requirements with at least one linked passing test case) / total requirements * 100.",
        "investigations": "- Confirm whether test case pass/fail status is factored into coverage (yes — only cases with at least one passing run count as covered).",
        "test_requirements": "- Matrix includes all non-deleted requirements for the project.\n- Each requirement shows linked_issues and linked_test_cases arrays.\n- Coverage percentage is correctly calculated.",
        "uat_criteria": "- Stakeholder opens the traceability page and sees all 8 requirements with their linked issues.\n- Requirements with no linked test cases show 0% coverage.\n- After linking a test case and recording a pass, coverage for that requirement changes to 100%.",
    },
    "File attachment upload on issues": {
        "decisions": "- Attachments stored in /uploads Docker volume, not object storage in v1.\n- Path structure: /uploads/{project_id}/{issue_id}/{uuid}_{filename}\n- Authenticated download URL: GET /issues/{id}/attachments/{attachment_id}/download",
        "investigations": "- Confirm max upload size — 10 MB per file, no per-issue limit in v1.\n- MIME type validation must be done on server from file content (not just filename extension).",
        "test_requirements": "- POST /issues/{id}/attachments with a valid PNG returns 201 with attachment metadata.\n- Upload of a file > 10 MB returns 413.\n- Upload of a disallowed MIME type returns 415.\n- GET download URL for attachment returns the file with correct Content-Type header.",
        "uat_criteria": "- Developer attaches a screenshot to an issue and sees it appear in the attachments list.\n- Clicking the attachment opens/downloads the file.\n- Attachment is visible in the issue history as evidence.",
    },
    "Frontend: login page": {
        "decisions": "- Token stored in Zustand store and persisted to localStorage.\n- On app load, if token exists and is not expired, skip login.\n- Redirect target after login: project list page.",
        "investigations": "- Confirmed: Ant Design Form handles validation, no custom validation library needed.",
        "test_requirements": "- Login form submits to POST /auth/login via the axios api client.\n- Invalid credentials show an error message below the form.\n- Token is stored in localStorage after successful login.",
        "uat_criteria": "- User sees the login page on first visit.\n- Entering correct credentials logs in and redirects to the project list.\n- Entering wrong credentials shows a red error message without a page reload.",
    },
    "Frontend: project list and creation": {
        "decisions": "- Project list is the landing page after login.\n- Create project modal: fields are key (uppercase enforced client-side) and name. Description optional.\n- Empty state shows a call-to-action to create the first project.",
        "investigations": "- Confirm whether key uniqueness error from API (409) should show inline on the key field or as a toast.",
        "test_requirements": "- GET /projects/ is called on mount and results rendered as cards or table rows.\n- Create modal posts to POST /projects/ and updates the list on success.\n- 409 from API shows an inline error on the key field.",
        "uat_criteria": "- Manager sees existing projects on login.\n- Clicking Create opens the modal; submitting creates the project and it appears in the list.\n- Duplicate key shows a clear error on the field itself.",
    },
    "Frontend: Kanban board": {
        "decisions": "- Columns are generated from GET /projects/{id}/states ordered by position.\n- Drag and drop calls PATCH /issues/{id} with the new status_id.\n- Done gate errors from the API are shown as a blocking modal (not a toast) — the move is animated back to the previous column.",
        "investigations": "- Evaluate dnd-kit vs react-beautiful-dnd. Decision: dnd-kit (actively maintained, works with React 18 strict mode).",
        "test_requirements": "- Board renders all non-deleted issues in correct columns after GET /issues/project/{id}.\n- Drag to Done triggers PATCH and displays gate error modal if 422 returned.\n- Issue cards show title, priority badge, type icon, and sequence number.",
        "uat_criteria": "- User sees all issues in the correct columns.\n- Dragging an issue updates the column immediately (optimistic) and reverts if the API rejects it.\n- Done gate error is explained clearly so the user knows what to do next.",
    },
    "Frontend: requirements list and editor": {
        "decisions": "- Requirements list is a table with columns: req_id, title, priority, status, version.\n- Inline editor opens as a right-side drawer, not a separate page.\n- Acceptance criteria rendered as Markdown.",
        "investigations": "- Confirm whether creating a requirement needs a separate Create modal or can reuse the drawer.",
        "test_requirements": "- List fetches GET /requirements/project/{id} and renders paginated.\n- Editing title/description calls PATCH and increments version in the UI.\n- Status badge updates after status PATCH.",
        "uat_criteria": "- BA opens the requirements page and sees all 8 requirements with correct status badges.\n- Editing a requirement and saving increments the version number visible in the table.\n- Approval status change is reflected immediately without a full page reload.",
    },
    "Frontend: wiki reader and editor": {
        "decisions": "- Wiki uses a split view: page tree on the left, content on the right.\n- Content is rendered Markdown. Edit mode swaps the rendered view for a textarea.\n- Save calls PATCH /wiki/{id}. Slug updates if title changes.",
        "investigations": "- Confirm Markdown rendering library. Decision: marked.js (already used in WizzardAI codebase).",
        "test_requirements": "- Page list fetches GET /wiki/project/{id} and renders as a tree.\n- Clicking a page fetches GET /wiki/{id} and renders content as Markdown.\n- Edit mode saves via PATCH and returns to read mode with updated content.",
        "uat_criteria": "- User can navigate to any wiki page from the sidebar tree.\n- Editing a page and saving shows the updated content immediately.\n- Tables and code blocks in Markdown render correctly.",
    },
    # ---- DEVENV issues ----------------------------------------------------
    "Fix Docker context - switch from desktop-linux to default": {
        "decisions": "- Rancher Desktop uses the 'default' context via npipe `docker_engine`. This is not the same as Docker Desktop's `desktop-linux` context.",
        "investigations": "- Confirmed: `docker context ls` showed `desktop-linux` as active, pointing to a non-existent Docker Desktop pipe. Rancher Desktop registers under `default`.",
        "test_requirements": "- `docker context ls` shows `default` as active with `npipe:////./pipe/docker_engine`.\n- `docker ps` returns successfully after context switch.\n- `docker compose up` starts containers without connection errors.",
        "uat_criteria": "- All docker commands run without 'Cannot connect to the Docker daemon' errors.\n- `docker context rm desktop-linux` completes without error leaving only default context.",
    },
    "Add pydantic[email] to requirements.txt": {
        "decisions": "- EmailStr from pydantic requires the email-validator extra package. It is not included in the base pydantic package.",
        "investigations": "- Confirmed: `pydantic==2.10.3` alone does not install email-validator. `pydantic[email]==2.10.3` is required.",
        "test_requirements": "- `docker compose up --build` completes without ImportError for EmailStr.\n- POST /auth/register with a valid email does not return a 500.",
        "uat_criteria": "- API container starts cleanly. Login endpoint accepts email-format credentials.",
    },
    "Remove -> None return annotations from HTTP 204 routes": {
        "decisions": "- FastAPI 0.111+ raises AssertionError at startup for routes that have `status_code=204` AND a `-> None` return annotation, because it interprets `None` as an explicit response model.\n- Fix: remove the `-> None` annotation. The function can still return nothing.",
        "investigations": "- Affected files: auth.py (logout), issues.py (delete_issue), projects.py (add_member), testcases.py (link_requirement), users.py (delete_user), wiki.py (delete_page).",
        "test_requirements": "- API container starts without AssertionError.\n- All 6 affected endpoints return HTTP 204 with empty body.",
        "uat_criteria": "- API startup log shows 'Application startup complete' with no assertion errors.",
    },
    "Pin bcrypt==3.2.2 to fix passlib 1.7.4 incompatibility": {
        "decisions": "- bcrypt 4.x changed internal behaviour that passlib 1.7.4 depends on for the 73-byte wrap-bug detection test. Pinning to 3.2.2 restores compatibility without patching passlib.",
        "investigations": "- Confirmed: bcrypt 4.x raises AttributeError or returns unexpected result for passlib's internal `_bcrypt__about__` check. bcrypt 3.2.2 passes cleanly.",
        "test_requirements": "- `import passlib; from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt']); ctx.verify('test', ctx.hash('test'))` returns True.\n- Login endpoint returns token pair for correct credentials.",
        "uat_criteria": "- User can log in with the seeded admin credentials without 500 errors.",
    },
    "Fix JWT PEM key double-escape in .env and config.py": {
        "decisions": "- .env stores PEM keys with newlines as `\\n` (backslash + n). pydantic-settings reads this as the two-character sequence `\\n`, not a real newline. The config.py property must replace `\\\\n` (Python string: backslash + n) with `\\n` (real newline).",
        "investigations": "- Root cause confirmed by printing the raw key string in Python: `\\n` appeared as literal characters, not newlines. python-jose's RS256 decoder failed with InvalidByte on the malformed PEM.",
        "test_requirements": "- `settings.jwt_private_key_pem` contains real newline characters between PEM lines.\n- POST /auth/login returns HTTP 200 with token pair.\n- JWT decode of the returned token succeeds without InvalidByte error.",
        "uat_criteria": "- Login works end-to-end. Token is accepted by protected endpoints.",
    },
    "Change admin seed email from .local to .io TLD": {
        "decisions": "- email-validator treats `.local` as a reserved TLD and rejects it. Admin seed email changed to `admin@wztrack.io`.",
        "investigations": "- Confirmed: `email_validator.validate_email('admin@wztrack.local')` raises EmailNotValidError. `.io` passes.",
        "test_requirements": "- API container starts and seeds admin user without validation error.\n- POST /auth/login with `admin@wztrack.io` returns token pair.\n- Volume reset (`docker compose down -v && up`) re-seeds correctly.",
        "uat_criteria": "- Admin login works with the documented credentials from .env.example.",
    },
    "Remap frontend port from 80 to 8080 for Rancher Desktop": {
        "decisions": "- Rancher Desktop's `host-switch.exe` binds port 80 on the Windows host. The frontend nginx must be mapped to a different host port. 8080 chosen as the standard alternative.",
        "investigations": "- Confirmed: `netstat -ano | findstr :80` showed a Rancher Desktop process holding port 80. No other service needs 80 on this machine.",
        "test_requirements": "- `docker compose up` completes without 'bind: address already in use' for port 80.\n- `curl http://localhost:8080` returns HTTP 200 with the React app HTML.",
        "uat_criteria": "- Frontend is accessible at http://localhost:8080.\n- All API calls from the frontend proxy correctly through nginx to the API container.",
    },
    "Fix nginx Host header to preserve port ($http_host)": {
        "decisions": "- nginx `$host` variable strips the port (returns `localhost` not `localhost:8080`). FastAPI uses the Host header to build redirect Location URLs. Using `$host` causes trailing-slash redirects to go to port 80 (CORS blocked). Changed to `$http_host` which preserves the port.",
        "investigations": "- Confirmed: browser DevTools showed redirect from `http://localhost:8080/api/v1/projects` to `http://localhost/api/v1/projects/` (port stripped). After fix the redirect goes to `http://localhost:8080/api/v1/projects/`.",
        "test_requirements": "- GET http://localhost:8080/api/v1/projects (without trailing slash) follows redirect to http://localhost:8080/api/v1/projects/ without CORS error.\n- Browser console shows no CORS policy errors on API calls.",
        "uat_criteria": "- App loads data from the API without CORS errors.\n- No manual URL workarounds needed by developers.",
    },
    "Create .env.example with all required variables": {
        "decisions": "- .env.example documents every required variable with placeholder values and a one-line comment.\n- Actual .env is in .gitignore and never committed.\n- RS256 key generation command is included as a comment in the file.",
        "investigations": "- List of required variables: DB_USER, DB_PASSWORD, DB_NAME, DATABASE_URL, JWT_PRIVATE_KEY, JWT_PUBLIC_KEY, ADMIN_EMAIL, ADMIN_PASSWORD, CORS_ORIGINS, DB_SCHEMA.",
        "test_requirements": "- `cp .env.example .env` followed by filling in real values allows a clean `docker compose up --build` to succeed.\n- All variables referenced in docker-compose.yml and config.py have a corresponding entry in .env.example.",
        "uat_criteria": "- A new developer can clone the repo, follow the setup guide, and have the stack running using only .env.example as a reference.",
    },
    "Initialise Alembic and create baseline migration": {
        "decisions": "- Replace `Base.metadata.create_all` on startup with `alembic upgrade head`.\n- Baseline migration generated from current models using `alembic revision --autogenerate`.\n- Migration command runs in the API container entrypoint before uvicorn starts.",
        "investigations": "- Confirm whether asyncpg is compatible with Alembic's sync migration runner. Alembic requires a sync engine for migrations — use `psycopg2` driver in alembic.ini, `asyncpg` for runtime.",
        "test_requirements": "- `alembic upgrade head` against a fresh database creates all tables.\n- `alembic downgrade -1` rolls back the baseline migration without error.\n- Subsequent model changes produce new migration files via `alembic revision --autogenerate`.",
        "uat_criteria": "- `docker compose up` on a clean volume completes with all tables created via Alembic (not create_all).\n- Adding a new model field and running autogenerate produces a non-empty migration file.",
    },
    "Write Pytest integration test suite for API": {
        "decisions": "- Use pytest-asyncio with httpx.AsyncClient and a test database (separate schema or in-memory SQLite where possible).\n- Fixtures: one per test session for DB setup, one per test for auth token.\n- Cover: auth, project CRUD, issue CRUD, done gate, UAT sign-off, requirements, wiki.",
        "investigations": "- Confirm pytest-asyncio version compatibility with Python 3.12 and FastAPI's lifespan.\n- Determine whether to use a real test Postgres container or SQLite for tests.",
        "test_requirements": "- All test files pass with `pytest tests/ -v` exit code 0.\n- Auth tests cover: register, login, refresh, logout, invalid credentials.\n- Done gate tests cover: blocked by missing test run, blocked by missing UAT, pass both, override by admin.",
        "uat_criteria": "- Running `pytest tests/ -v` in the API container produces a green test report.\n- CI pipeline runs the suite on every push and fails if any test regresses.",
    },
}


def main():
    print("Logging in ...")
    token = login()
    print("OK\n")

    # ------------------------------------------------------------------ add WZT requirements
    print("Adding new WZT requirements (story standard) ...")
    wzt_id = get_project_id("WZT", token)
    if not wzt_id:
        print("  WZT project not found — skipping requirements.")
    else:
        resp = api("GET", f"/requirements/project/{wzt_id}", token=token) or {}
        existing_titles = {r["title"] for r in resp.get("data", [])}
        for req in WZT_NEW_REQUIREMENTS:
            if req["title"] in existing_titles:
                print(f"  Already exists: {req['title'][:70]}")
                continue
            desired_status = req.pop("_status", None)
            result = api("POST", f"/requirements/project/{wzt_id}", body={k: v for k, v in req.items()}, token=token)
            if result:
                print(f"  Created: {result.get('req_id')} — {result['title'][:70]}")
                if desired_status and desired_status != result.get("status"):
                    api("PATCH", f"/requirements/{result['id']}", body={"status": desired_status}, token=token)
                    print(f"    -> status: {desired_status}")
            req["_status"] = desired_status  # restore

    # ------------------------------------------------------------------ patch issues in both projects
    for project_key in ("WZT", "DEVENV"):
        print(f"\nPatching issues in {project_key} with enriched content ...")
        pid = get_project_id(project_key, token)
        if not pid:
            print(f"  Project {project_key} not found, skipping.")
            continue
        issues = get_all_issues(pid, token)
        print(f"  Found {len(issues)} issues.")
        patched = 0
        for issue in issues:
            title = issue["title"]
            enrichment = None
            for key, data in ISSUE_ENRICHMENT.items():
                if title == key or title.startswith(key[:50]):
                    enrichment = data
                    break
            if enrichment is None:
                continue
            # Only patch if at least one field is not yet set
            needs_patch = any(issue.get(f) is None for f in enrichment)
            if not needs_patch:
                continue
            patch_body = {k: v for k, v in enrichment.items() if issue.get(k) is None}
            result = api("PATCH", f"/issues/{issue['id']}", body=patch_body, token=token)
            if result:
                patched += 1
                print(f"  Patched: {title[:70]}")
        print(f"  {patched} issues updated.")

    print("\nDone.")


if __name__ == "__main__":
    main()
