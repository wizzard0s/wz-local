"""
seed_devenv_structure.py

Adds the WZ2 project suite structure requirements and stories to the DEVENV project in WZTrack.

Usage:
    python seed_devenv_structure.py [--base-url http://localhost:8000] [--email admin@wztrack.io] [--password admin1234]
"""

import argparse
import requests

BASE_URL = "http://localhost:8000"
EMAIL = "admin@wztrack.io"
PASSWORD = "admin1234"

# ─── New requirement ──────────────────────────────────────────────────────────

NEW_REQUIREMENT = {
    "title": "WZ2 workspace organised as named project suites with subprojects",
    "description": (
        "The WZ2 workspace `projects/` directory is the root for all WZ development work. "
        "Projects are grouped into named suites. Each suite is a directory containing a `suite.json` manifest, "
        "a `README.md`, and zero or more subproject directories.\n\n"
        "**Suite types:**\n"
        "- `wz_local` — live instances tied to this workstation; the sandbox where new projects are proven\n"
        "- `wz_systems` — generic, reusable versions promoted from `wz_local` once promotion criteria are met\n\n"
        "**Naming convention:** All suite and subproject directory names use underscores (e.g. `wz_local`, `wz_systems`, `wztrack`).\n\n"
        "**WZTrack is the registry:** Every subproject is tracked as a project inside WZTrack itself. "
        "Suite membership, status, and promotion state are captured in the corresponding WZTrack project."
    ),
    "acceptance_criteria": (
        "- `WZ2/projects/` contains only suite directories — no loose subproject folders.\n"
        "- Each suite directory contains a `suite.json` with: `name`, `description`, `subprojects[]`, `status`.\n"
        "- Each suite directory contains a `README.md` describing its purpose and the promotion/membership rules.\n"
        "- `wz_local/wztrack/` exists and contains the current WZTrack subproject.\n"
        "- `wz_systems/` exists as a placeholder with empty `subprojects: []` and `status: planned`.\n"
        "- All suite and subproject folder names use underscores, not hyphens or spaces.\n"
        "- A subproject may not be added to `wz_systems` without meeting the documented promotion criteria."
    ),
    "priority": "must",
    "status": "approved",
}

# ─── New epic + stories ───────────────────────────────────────────────────────

NEW_ISSUES = [
    {
        "title": "[EPIC] WZ2 project suite structure",
        "type": "epic",
        "priority": "high",
        "state": "Done",
        "story_points": 0,
        "description": (
            "Define, document, and implement the WZ2 project suite structure. "
            "This governs where all WZ development work lives, how suites are defined, "
            "and how subprojects are promoted from local instances to the generic systems suite."
        ),
    },
    {
        "title": "Create wz_local suite scaffold (suite.json + README)",
        "type": "task",
        "priority": "high",
        "state": "Done",
        "story_points": 1,
        "description": (
            "Create `WZ2/projects/wz_local/suite.json` and `WZ2/projects/wz_local/README.md`.\n\n"
            "`suite.json` declares: name, description, subprojects list (currently wztrack), status=active.\n"
            "`README.md` describes the purpose of wz_local, its membership rules, and the contract for each subproject."
        ),
        "decisions": (
            "wz_local is for live, real instances tied to this workstation — not generic templates. "
            "The distinction from wz_systems is that wz_local projects have environment-specific configuration "
            "and are not expected to be deployed elsewhere without changes."
        ),
        "test_requirements": (
            "- `WZ2/projects/wz_local/suite.json` exists and parses as valid JSON.\n"
            "- `suite.json` contains: name, description, subprojects (array), status fields.\n"
            "- `WZ2/projects/wz_local/README.md` exists and documents purpose and contract."
        ),
        "uat_criteria": (
            "A new developer can read `README.md` and `suite.json` and understand what wz_local is for "
            "and what rules apply to adding a subproject to it."
        ),
    },
    {
        "title": "Move wztrack/ into wz_local/ suite",
        "type": "task",
        "priority": "high",
        "state": "Done",
        "story_points": 2,
        "description": (
            "Move `WZ2/projects/wztrack/` to `WZ2/projects/wz_local/wztrack/`.\n\n"
            "The Docker Compose stack, backend, frontend, and all seed/migration scripts move with it. "
            "Update any absolute paths in scripts and documentation that reference the old location."
        ),
        "decisions": (
            "The move was performed with robocopy because VS Code holds file locks on the source directory "
            "during an active session. The old `wztrack/` directory will be deleted when VS Code is reloaded. "
            "No Docker rebuild is needed — the stack binds to the Docker socket, not to the host file path."
        ),
        "investigations": (
            "Check whether any CI scripts, VS Code workspace settings, or task definitions reference "
            "`WZ2/projects/wztrack` by absolute path. Update them to `WZ2/projects/wz_local/wztrack`."
        ),
        "test_requirements": (
            "- `WZ2/projects/wz_local/wztrack/docker-compose.yml` exists.\n"
            "- `docker compose up` from `wz_local/wztrack/` starts all three containers cleanly.\n"
            "- All seed and migration scripts run correctly from the new path.\n"
            "- Old `WZ2/projects/wztrack/` directory no longer exists after VS Code reload."
        ),
        "uat_criteria": (
            "After the move, `docker compose up --build` from `wz_local/wztrack/` starts the full stack "
            "and the app is accessible at http://localhost:8080 with no errors."
        ),
    },
    {
        "title": "Create wz_systems suite scaffold (suite.json + README)",
        "type": "task",
        "priority": "high",
        "state": "Done",
        "story_points": 1,
        "description": (
            "Create `WZ2/projects/wz_systems/suite.json` and `WZ2/projects/wz_systems/README.md`.\n\n"
            "`suite.json` declares: name, description, `subprojects: []`, `status: planned`.\n"
            "`README.md` describes the purpose of wz_systems, the promotion criteria, and the planned future subprojects."
        ),
        "decisions": (
            "wz_systems starts empty — no subproject folders are created until a project meets the promotion criteria. "
            "The README documents the planned subprojects (wztrack, wizzardauth, wizzardchat, etc.) but they are listed "
            "as 'planned', not created as empty stubs."
        ),
        "test_requirements": (
            "- `WZ2/projects/wz_systems/suite.json` exists, is valid JSON, and has `subprojects: []`.\n"
            "- `WZ2/projects/wz_systems/README.md` exists and documents promotion criteria.\n"
            "- No subproject subdirectories exist under `wz_systems/` at this stage."
        ),
        "uat_criteria": (
            "A developer reading `wz_systems/README.md` can answer: what is here, why is it empty, "
            "what is planned, and what must happen before something is added."
        ),
    },
    {
        "title": "Document suite promotion criteria for wz_local → wz_systems",
        "type": "story",
        "priority": "high",
        "state": "To Do",
        "story_points": 2,
        "description": (
            "Define and document the exact criteria a subproject must meet before it can be promoted "
            "from `wz_local` to `wz_systems`. Add these to `wz_systems/README.md` and as a requirement in DEVENV.\n\n"
            "Draft criteria:\n"
            "1. Passing automated test suite (unit + integration)\n"
            "2. Alembic migrations in place\n"
            "3. `.env.example` committed and complete\n"
            "4. No hardcoded localhost or environment assumptions\n"
            "5. At least one successful deployment outside the original dev machine"
        ),
        "decisions": (
            "Criteria must be objective and verifiable — not subjective ('it feels ready'). "
            "Each criterion maps to a specific check that can be automated or reviewed in a PR."
        ),
        "investigations": (
            "Review what WZTrack currently lacks relative to these criteria. "
            "Each gap becomes a WZT story (Alembic, .env.example, test suite, etc.)."
        ),
        "test_requirements": (
            "- Promotion criteria are written in `wz_systems/README.md` as a numbered, verifiable checklist.\n"
            "- A DEVENV requirement exists for the criteria contract.\n"
            "- Each criterion maps to at least one open WZT or DEVENV story."
        ),
        "uat_criteria": (
            "Given current WZTrack state, a developer can run through the checklist and identify exactly "
            "which criteria are met and which are not — with no ambiguity."
        ),
    },
    {
        "title": "Update VS Code workspace and task definitions to new wztrack path",
        "type": "task",
        "priority": "medium",
        "state": "To Do",
        "story_points": 1,
        "description": (
            "Scan VS Code workspace settings (`.code-workspace`), task definitions (`.vscode/tasks.json`), "
            "and any launch configs for references to the old `WZ2/projects/wztrack` path. "
            "Update all references to `WZ2/projects/wz_local/wztrack`."
        ),
        "investigations": (
            "Check: WZ2 `.code-workspace` file, `.vscode/tasks.json`, `.vscode/launch.json`, "
            "any `settings.json` entries, and the WZ2 `copilot-instructions.md` files."
        ),
        "test_requirements": (
            "- `grep -r 'projects/wztrack' WZ2/.vscode WZ2/.github` returns no matches.\n"
            "- All VS Code tasks that reference the wztrack directory run successfully from the new path."
        ),
        "uat_criteria": (
            "Opening VS Code with the WZ2 workspace active and running the docker task for wztrack "
            "uses the correct new path."
        ),
    },
    {
        "title": "Delete stale WZ2/projects/wztrack/ after VS Code reload",
        "type": "task",
        "priority": "medium",
        "state": "To Do",
        "story_points": 1,
        "description": (
            "The original `WZ2/projects/wztrack/` directory could not be removed during the initial move "
            "because VS Code holds file locks on active workspace folders. "
            "After reloading VS Code with the updated workspace (pointing to `wz_local/wztrack`), "
            "delete the stale `WZ2/projects/wztrack/` directory."
        ),
        "decisions": (
            "Use `Remove-Item -Recurse -Force` or Windows Explorer. "
            "Verify `wz_local/wztrack/` is identical before deleting — do not delete until confirmed."
        ),
        "test_requirements": (
            "- `Test-Path 'WZ2/projects/wztrack'` returns False after cleanup.\n"
            "- `WZ2/projects/wz_local/wztrack/` contains all expected files.\n"
            "- Docker stack still starts cleanly after the delete."
        ),
        "uat_criteria": (
            "The WZ2 projects directory contains only: `wz_local/`, `wz_systems/`. "
            "No stale `wztrack/` folder exists at the root of `projects/`."
        ),
    },
    {
        "title": "Define suite.json schema and validate it in CI",
        "type": "story",
        "priority": "medium",
        "state": "Backlog",
        "story_points": 3,
        "description": (
            "Create a JSON schema for `suite.json` so all suites are validated consistently. "
            "Add a `validate.ps1` check (or extend the existing one) that reads every `suite.json` "
            "under `WZ2/projects/` and validates it against the schema."
        ),
        "decisions": (
            "Schema should enforce: name (string), description (string), subprojects (array of objects with name/path/description/status), "
            "status (enum: active | planned | archived)."
        ),
        "investigations": (
            "Check if `WIZZARDSDK/validate.ps1` can be extended to also validate workspace structure, "
            "or if a separate `WZ2/validate.ps1` is cleaner."
        ),
        "test_requirements": (
            "- A `suite.json` missing the `status` field fails validation.\n"
            "- All current suite manifests (`wz_local`, `wz_systems`) pass validation.\n"
            "- Validation runs in under 5 seconds."
        ),
        "uat_criteria": (
            "Run the validation script from the WZ2 root. It reports pass/fail per suite and "
            "exits with code 0 when all suites are valid."
        ),
    },
    {
        "title": "Add wz_local and wz_systems to WZ2 copilot-instructions.md",
        "type": "task",
        "priority": "medium",
        "state": "To Do",
        "story_points": 1,
        "description": (
            "Update `WZ2/.github/copilot-instructions.md` to document the suite structure: "
            "the `projects/` layout, the two suites, the naming convention (underscores), "
            "and the rule that `wz_systems` is empty until promotion criteria are met."
        ),
        "test_requirements": (
            "- `copilot-instructions.md` folder boundary table includes both `wz_local/` and `wz_systems/`.\n"
            "- The naming convention (underscores) is explicitly stated.\n"
            "- The promotion rule is documented."
        ),
        "uat_criteria": (
            "GitHub Copilot, when working in the WZ2 workspace, correctly understands that new subprojects "
            "go under `wz_local/` and that `wz_systems/` requires promotion criteria."
        ),
    },
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def login(session):
    r = session.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    r.raise_for_status()
    session.headers["Authorization"] = "Bearer " + r.json()["access_token"]
    print("Logged in.")


def find_project(session, key):
    r = session.get(f"{BASE_URL}/api/v1/projects/")
    r.raise_for_status()
    data = r.json()
    for p in (data["data"] if isinstance(data, dict) else data):
        if p["key"] == key:
            return p
    raise SystemExit(f"Project {key} not found.")


def list_requirements(session, project_id):
    r = session.get(f"{BASE_URL}/api/v1/requirements/project/{project_id}")
    r.raise_for_status()
    data = r.json()
    return data["data"] if isinstance(data, dict) else data


def list_issues(session, project_id):
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


def list_states(session, project_id):
    r = session.get(f"{BASE_URL}/api/v1/projects/{project_id}/states/")
    r.raise_for_status()
    data = r.json()
    return data["data"] if isinstance(data, dict) else data


def find_state(states, name):
    for s in states:
        if s["name"].lower() == name.lower():
            return s
    return states[0]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    global BASE_URL, EMAIL, PASSWORD
    parser = argparse.ArgumentParser()
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
    pid = devenv["id"]
    print(f"DEVENV project: {pid}")

    # Add requirement
    print("\n── Requirements ──")
    existing_reqs = {r["title"] for r in list_requirements(session, pid)}
    if NEW_REQUIREMENT["title"] in existing_reqs:
        print(f"  Already exists: {NEW_REQUIREMENT['title'][:60]}")
    else:
        payload = {
            "title": NEW_REQUIREMENT["title"],
            "description": NEW_REQUIREMENT["description"],
            "acceptance_criteria": NEW_REQUIREMENT["acceptance_criteria"],
            "priority": NEW_REQUIREMENT["priority"],
            "status": NEW_REQUIREMENT["status"],
        }
        r = session.post(f"{BASE_URL}/api/v1/requirements/project/{pid}", json=payload)
        if r.ok:
            print(f"  Created: {NEW_REQUIREMENT['title'][:70]}")
        else:
            print(f"  WARN: {r.text[:120]}")

    # Add issues
    print("\n── Issues ──")
    states = list_states(session, pid)
    existing_issues = {i["title"] for i in list_issues(session, pid)}
    added = 0
    for issue in NEW_ISSUES:
        if issue["title"] in existing_issues:
            print(f"  Already exists: {issue['title'][:60]}")
            continue
        state = find_state(states, issue.get("state", "Backlog"))
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
        r = session.post(f"{BASE_URL}/api/v1/issues/project/{pid}", json=payload)
        if r.ok:
            added += 1
            print(f"  Created: {issue['title'][:70]}")
        else:
            print(f"  WARN: {issue['title'][:50]}: {r.text[:100]}")

    print(f"\nDone — {added} issues added.")


if __name__ == "__main__":
    main()
