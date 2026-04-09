"""
migrate_devenv.py

Cleans up the DEVENV project in WZTrack:
  1. Cancels all current DEVENV issues (Docker/infra contamination — belongs in WZT).
  2. Adds the Docker/infra items as a new epic + issues in WZT.
  3. Updates the DEVENV project description.
  4. Creates 12 new DEVENV requirements for WZ development standards.
  5. Creates 3 wiki pages for the standards content.
  6. Creates 16 issues for WZ standards work.

Usage:
    python migrate_devenv.py [--base-url http://localhost:8000] [--email admin@wztrack.io] [--password admin1234]
"""

import argparse
import json
import sys
import requests

BASE_URL = "http://localhost:8000"
EMAIL = "admin@wztrack.io"
PASSWORD = "admin1234"


def login(session: requests.Session) -> str:
    r = session.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    r.raise_for_status()
    token = r.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("Logged in.")
    return token


def find_project(session: requests.Session, key: str) -> dict:
    r = session.get(f"{BASE_URL}/api/v1/projects/")
    r.raise_for_status()
    data = r.json()
    items = data["data"] if isinstance(data, dict) else data
    for p in items:
        if p["key"] == key:
            return p
    raise SystemExit(f"Project {key} not found.")


def list_issues(session: requests.Session, project_id: str) -> list:
    all_issues = []
    page = 1
    while True:
        r = session.get(f"{BASE_URL}/api/v1/issues/project/{project_id}", params={"page": page, "page_size": 100})
        r.raise_for_status()
        data = r.json()
        items = data["data"] if isinstance(data, dict) else data
        all_issues.extend(items)
        meta = data.get("meta", {})
        if not meta or page >= meta.get("total_pages", 1):
            break
        page += 1
    return all_issues


def list_states(session: requests.Session, project_id: str) -> list:
    r = session.get(f"{BASE_URL}/api/v1/projects/{project_id}/states/")
    r.raise_for_status()
    data = r.json()
    return data["data"] if isinstance(data, dict) else data


def find_state(states: list, category: str = None, name: str = None) -> dict:
    for s in states:
        if name and s["name"].lower() == name.lower():
            return s
        if category and name is None and s["category"] == category:
            return s
    return states[0]


def list_requirements(session: requests.Session, project_id: str) -> list:
    r = session.get(f"{BASE_URL}/api/v1/requirements/project/{project_id}")
    r.raise_for_status()
    data = r.json()
    return data["data"] if isinstance(data, dict) else data


def list_wiki(session: requests.Session, project_id: str) -> list:
    r = session.get(f"{BASE_URL}/api/v1/wiki/project/{project_id}")
    r.raise_for_status()
    data = r.json()
    return data["data"] if isinstance(data, dict) else data


# ─── Step 1: Cancel all current DEVENV issues ────────────────────────────────

def cancel_devenv_issues(session: requests.Session, devenv: dict):
    print("\n── Step 1: Cancel contaminated DEVENV issues ──")
    states = list_states(session, devenv["id"])
    cancelled = find_state(states, name="Cancelled")
    if not cancelled:
        print("  WARNING: No 'Cancelled' state found — skipping cancellation.")
        return
    issues = list_issues(session, devenv["id"])
    cancelled_count = 0
    for issue in issues:
        if issue.get("state_id") == cancelled["id"]:
            print(f"  Already cancelled: {issue['title']}")
            continue
        r = session.patch(
            f"{BASE_URL}/api/v1/issues/{issue['id']}",
            json={
                "state_id": cancelled["id"],
                "description": (issue.get("description") or "") +
                    "\n\n[MIGRATED] This item was in DEVENV by mistake. "
                    "It relates to WZTrack infrastructure, not WZ platform development standards. "
                    "Moved to the WZT project."
            }
        )
        if r.ok:
            print(f"  Cancelled: {issue['title']}")
            cancelled_count += 1
        else:
            print(f"  WARN: Could not cancel {issue['title']}: {r.text[:80]}")
    print(f"  {cancelled_count} issues cancelled.")


# ─── Step 2: Add Docker/infra epic + items to WZT ────────────────────────────

WZT_INFRA_REQUIREMENTS = [
    {
        "title": "Containerised development environment via Docker Compose",
        "description": "All WZTrack services (API, frontend, database) must run as Docker containers orchestrated by a single docker-compose.yml.",
        "acceptance_criteria": "- `docker compose up --build` starts all three services.\n- No service depends on host-installed Python, Node, or PostgreSQL.\n- Environment variables loaded from `.env`.",
        "priority": "must",
    },
    {
        "title": "PostgreSQL database with persistent volume and health check",
        "description": "The database container must persist data across container restarts. The API must not start until the DB passes its health check.",
        "acceptance_criteria": "- Named volume `wztrack_pgdata` survives `docker compose down`.\n- API declares `depends_on: db: condition: service_healthy`.\n- Health check uses `pg_isready`.",
        "priority": "must",
    },
    {
        "title": "API secrets management via .env and pydantic-settings",
        "description": "All sensitive configuration must be supplied via environment variables loaded from a `.env` file. No secrets committed to source control.",
        "acceptance_criteria": "- `.env` in `.gitignore`.\n- `.env.example` committed with placeholder values.\n- `pydantic-settings` `Settings` class loads all config.",
        "priority": "must",
    },
    {
        "title": "RS256 JWT key generation and correct PEM encoding",
        "description": "Private and public keys generated with openssl, stored in `.env` with newlines as `\\n`, correctly decoded at runtime.",
        "acceptance_criteria": "- Keys generated with `openssl genrsa` and `openssl rsa -pubout`.\n- `config.py` replaces `\\\\n` with `\\n` in key properties.\n- Login returns valid JWT with no decode errors.",
        "priority": "must",
    },
    {
        "title": "Alembic migrations for production schema evolution",
        "description": "Replace `create_all` on startup with Alembic migrations before any production deployment.",
        "acceptance_criteria": "- Alembic initialised, baseline migration created.\n- `alembic upgrade head` runs cleanly from empty DB.\n- API container runs migrations before uvicorn.",
        "priority": "must",
    },
    {
        "title": "JWT token invalidation via blocklist on logout",
        "description": "A Redis-backed blocklist invalidates logged-out tokens before their natural expiry.",
        "acceptance_criteria": "- Logout adds token JTI to Redis with TTL.\n- Middleware rejects blocklisted tokens with HTTP 401.\n- Blocklist entries expire automatically.",
        "priority": "should",
    },
]

WZT_INFRA_ISSUES = [
    {"title": "[EPIC] WZTrack infrastructure and deployment setup",   "type": "epic",  "priority": "high",   "state": "In Progress", "story_points": 0,  "description": "All Docker Compose, database, JWT, nginx, and production-readiness work for the WZTrack platform itself."},
    {"title": "Create .env.example with all required variables",      "type": "story", "priority": "high",   "state": "To Do",       "story_points": 2,  "description": "Commit a .env.example with placeholder values for DATABASE_URL, JWT_PRIVATE_KEY, JWT_PUBLIC_KEY, ADMIN_EMAIL, CORS_ORIGINS. Include instructions for generating RS256 keys.",
     "test_requirements": ".env.example contains every variable used by config.py. A developer can copy it to .env, fill in values, and start the stack without extra research.",
     "uat_criteria": "A developer with no prior WZTrack context can use .env.example to configure the stack correctly on first attempt.",
     "decisions": "Placeholder values must include comments explaining format — especially the \\n encoding for PEM keys."},
    {"title": "Initialise Alembic and create baseline migration",     "type": "story", "priority": "high",   "state": "To Do",       "story_points": 3,  "description": "Replace create_all on startup with Alembic. Run alembic init, create baseline migration from current models, verify alembic upgrade head from empty DB.",
     "test_requirements": "alembic upgrade head runs cleanly from an empty database. alembic downgrade -1 reverses the baseline without errors.",
     "uat_criteria": "docker compose up starts the API with schema applied via Alembic, not create_all.",
     "decisions": "Baseline must capture current schema including all 7 new issue columns added via ALTER TABLE.",
     "investigations": "Current schema was partially migrated manually (ALTER TABLE for decisions, investigations, test_requirements, uat_criteria, uat_approved, uat_approved_by, uat_approved_at). Baseline migration must reflect actual DB state."},
    {"title": "Run Alembic migrations in API container entrypoint",   "type": "task",  "priority": "high",   "state": "To Do",       "story_points": 1,  "description": "Add `alembic upgrade head` to the API container startup command before uvicorn."},
    {"title": "Add Redis service to docker-compose for token blocklist", "type": "story", "priority": "medium", "state": "Backlog",   "story_points": 2,  "description": "Add a Redis container to docker-compose.yml. API depends_on redis (healthy). Used for logout token blocklist."},
    {"title": "Implement JWT token blocklist using Redis",             "type": "story", "priority": "medium", "state": "Backlog",     "story_points": 5,  "description": "On logout, add token JTI to Redis with TTL matching remaining token lifetime. Middleware rejects blocklisted tokens.",
     "test_requirements": "After logout, the same JWT cannot authenticate. Token blocked with HTTP 401. Token entry in Redis expires at the same time the JWT would have expired.",
     "uat_criteria": "Log out from the browser, attempt an API call with the old token — must receive 401.",
     "decisions": "Use JTI claim as the Redis key. TTL = (token exp - now) in seconds.",
     "investigations": "Confirm python-jose includes a JTI claim in issued tokens. If not, add it in the token creation step."},
    {"title": "Add GitHub Actions CI workflow",                       "type": "story", "priority": "medium", "state": "Backlog",     "story_points": 3,  "description": "Workflow on push to main: ruff lint, mypy type check, pytest, Docker image builds. Fail fast.",
     "test_requirements": "Workflow passes on a clean main branch. A linting violation causes the workflow to fail at the lint step.",
     "uat_criteria": "The Actions tab shows a green check on every passing commit and a red X on any commit that fails lint or tests.",
     "decisions": "Use matrix strategy if running tests against multiple Python versions — start with 3.12 only.",
     "investigations": "Check if a .github/workflows directory exists. If so, review existing workflows before adding."},
    {"title": "Write Pytest integration test suite for API",          "type": "story", "priority": "medium", "state": "Backlog",     "story_points": 5,  "description": "Async test client covering: login, refresh, logout, project CRUD, issue CRUD, requirements CRUD, done gate enforcement, UAT sign-off, history endpoint.",
     "test_requirements": "pytest exits with code 0 on a clean database. Done-gate test confirms 422 when trying to transition without passing test run and UAT.",
     "uat_criteria": "Test suite runs in CI and all tests pass on main branch.",
     "decisions": "Use pytest-asyncio + httpx.AsyncClient against a test PostgreSQL container. Do not share state between tests.",
     "investigations": "Check if any tests already exist in the backend/ directory."},
    {"title": "Document secret rotation procedure",                   "type": "task",  "priority": "low",    "state": "Backlog",     "story_points": 2,  "description": "Runbook for rotating RS256 JWT keys in production without invalidating active sessions. Steps: generate new pair, update .env, rolling restart, verify."},
]


def add_wzt_infra_items(session: requests.Session, wzt: dict):
    print("\n── Step 2: Add Docker/infra items to WZT ──")
    states = list_states(session, wzt["id"])
    existing_reqs = list_requirements(session, wzt["id"])
    existing_titles = {r["title"] for r in existing_reqs}

    added_reqs = 0
    for req in WZT_INFRA_REQUIREMENTS:
        if req["title"] in existing_titles:
            print(f"  Req already exists: {req['title'][:60]}")
            continue
        payload = {
            "title": req["title"],
            "description": req["description"],
            "acceptance_criteria": req.get("acceptance_criteria", ""),
            "priority": req["priority"],
            "status": "draft",
        }
        r = session.post(f"{BASE_URL}/api/v1/requirements/project/{wzt['id']}", json=payload)
        if r.ok:
            print(f"  Created req: {req['title'][:60]}")
            added_reqs += 1
        else:
            print(f"  WARN: {req['title'][:50]}: {r.text[:80]}")

    existing_issues = list_issues(session, wzt["id"])
    existing_issue_titles = {i["title"] for i in existing_issues}

    added_issues = 0
    for issue in WZT_INFRA_ISSUES:
        if issue["title"] in existing_issue_titles:
            print(f"  Issue already exists: {issue['title'][:60]}")
            continue
        state = find_state(states, name=issue.get("state", "Backlog"))
        payload = {
            "title": issue["title"],
            "description": issue.get("description", ""),
            "type": issue.get("type", "story"),
            "priority": issue.get("priority", "medium"),
            "state_id": state["id"],
            "story_points": issue.get("story_points", 0),
        }
        for field in ("decisions", "investigations", "test_requirements", "uat_criteria"):
            if field in issue:
                payload[field] = issue[field]
        r = session.post(f"{BASE_URL}/api/v1/issues/project/{wzt['id']}", json=payload)
        if r.ok:
            print(f"  Created issue: {issue['title'][:60]}")
            added_issues += 1
        else:
            print(f"  WARN: {issue['title'][:50]}: {r.text[:80]}")

    print(f"  {added_reqs} requirements added, {added_issues} issues added to WZT.")


# ─── Step 3: Rebuild DEVENV with correct standards content ───────────────────

def load_v2_data() -> dict:
    import pathlib
    f = pathlib.Path(__file__).parent / "seed_data_devenv_v2.json"
    with open(f, encoding="utf-8") as fh:
        return json.load(fh)


def update_devenv_project(session: requests.Session, devenv: dict, v2: dict):
    print("\n── Step 3: Update DEVENV project metadata ──")
    r = session.patch(
        f"{BASE_URL}/api/v1/projects/{devenv['id']}",
        json={
            "name": v2["project_update"]["name"],
            "description": v2["project_update"]["description"],
        }
    )
    if r.ok:
        print(f"  Project updated: {v2['project_update']['name']}")
    else:
        print(f"  WARN: Could not update project: {r.text[:120]}")


def create_devenv_requirements(session: requests.Session, devenv: dict, v2: dict):
    print("\n── Step 4: Create new DEVENV requirements ──")
    existing = {r["title"] for r in list_requirements(session, devenv["id"])}
    added = 0
    for req in v2["requirements"]:
        if req["title"] in existing:
            print(f"  Already exists: {req['title'][:60]}")
            continue
        payload = {
            "title": req["title"],
            "description": req["description"],
            "acceptance_criteria": req.get("acceptance_criteria", ""),
            "priority": req["priority"],
            "status": req.get("_status", "draft"),
        }
        r = session.post(f"{BASE_URL}/api/v1/requirements/project/{devenv['id']}", json=payload)
        if r.ok:
            added += 1
            print(f"  Created: {req['title'][:60]}")
        else:
            print(f"  WARN: {req['title'][:50]}: {r.text[:80]}")
    print(f"  {added} requirements created.")


def create_devenv_wiki(session: requests.Session, devenv: dict, v2: dict):
    print("\n── Step 5: Create DEVENV wiki pages ──")
    existing = {w["title"] for w in list_wiki(session, devenv["id"])}
    added = 0
    for page in v2["wiki"]:
        if page["title"] in existing:
            print(f"  Already exists: {page['title']}")
            continue
        r = session.post(f"{BASE_URL}/api/v1/wiki/project/{devenv['id']}", json={
            "title": page["title"],
            "content": page["content"],
        })
        if r.ok:
            added += 1
            print(f"  Created: {page['title']}")
        else:
            print(f"  WARN: {page['title']}: {r.text[:80]}")
    print(f"  {added} wiki pages created.")


def create_devenv_issues(session: requests.Session, devenv: dict, v2: dict):
    print("\n── Step 6: Create new DEVENV issues ──")
    states = list_states(session, devenv["id"])
    existing = {i["title"] for i in list_issues(session, devenv["id"])}
    added = 0
    for issue in v2["issues"]:
        if issue["title"] in existing:
            print(f"  Already exists: {issue['title'][:60]}")
            continue
        state = find_state(states, name=issue.get("state", "Backlog"))
        payload = {
            "title": issue["title"],
            "description": issue.get("description", ""),
            "type": issue.get("type", "story"),
            "priority": issue.get("priority", "medium"),
            "state_id": state["id"],
            "story_points": issue.get("story_points", 0),
        }
        for field in ("decisions", "investigations", "test_requirements", "uat_criteria"):
            if field in issue:
                payload[field] = issue[field]
        r = session.post(f"{BASE_URL}/api/v1/issues/project/{devenv['id']}", json=payload)
        if r.ok:
            added += 1
            print(f"  Created: {issue['title'][:60]}")
        else:
            print(f"  WARN: {issue['title'][:50]}: {r.text[:80]}")
    print(f"  {added} issues created.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    global BASE_URL, EMAIL, PASSWORD
    parser = argparse.ArgumentParser(description="Migrate DEVENV from Docker/infra to WZ dev standards.")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--email", default=EMAIL)
    parser.add_argument("--password", default=PASSWORD)
    args = parser.parse_args()
    BASE_URL = args.base_url.rstrip("/")
    EMAIL = args.email
    PASSWORD = args.password

    session = requests.Session()
    login(session)

    devenv = find_project(session, "DEVENV")
    wzt = find_project(session, "WZT")
    print(f"Found DEVENV: {devenv['id']}")
    print(f"Found WZT:    {wzt['id']}")

    v2 = load_v2_data()

    cancel_devenv_issues(session, devenv)
    add_wzt_infra_items(session, wzt)
    update_devenv_project(session, devenv, v2)
    create_devenv_requirements(session, devenv, v2)
    create_devenv_wiki(session, devenv, v2)
    create_devenv_issues(session, devenv, v2)

    print("\nMigration complete.")
    print("  - Contaminated DEVENV issues cancelled and moved to WZT.")
    print("  - DEVENV rebuilt as WZ platform development standards project.")


if __name__ == "__main__":
    main()
