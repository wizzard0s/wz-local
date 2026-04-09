"""
WZTrack project seed script.
Reads seed_data.json and calls the WZTrack API to create all project data.

Usage:
    python seed_project.py [--base-url URL] [--email EMAIL] [--password PASSWORD]
"""
import json
import sys
import argparse
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@wztrack.io"
ADMIN_PASSWORD = "admin1234"


def api(method: str, path: str, body=None, token: str = None) -> dict:
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
        body_text = exc.read().decode()
        print(f"  ERROR {exc.code} {method} {path}: {body_text[:300]}")
        return None


def login(email: str, password: str) -> str:
    body = json.dumps({"email": email, "password": password}).encode()
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


import urllib.parse  # noqa: E402  (used by urllib.request internally)


def main():
    global BASE_URL
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url",  default=BASE_URL)
    parser.add_argument("--email",     default=ADMIN_EMAIL)
    parser.add_argument("--password",  default=ADMIN_PASSWORD)
    parser.add_argument("--data-file", default=None, help="Path to seed JSON file (default: seed_data.json next to this script)")
    args = parser.parse_args()

    BASE_URL = args.base_url.rstrip("/")

    import os
    if args.data_file:
        data_file = args.data_file
    else:
        data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data.json")
    with open(data_file, encoding="utf-8") as fh:
        seed = json.load(fh)

    print(f"Logging in as {args.email} ...")
    token = login(args.email, args.password)
    print("OK\n")

    # ------------------------------------------------------------------ project
    print("Creating project ...")
    project = seed["project"]
    resp = api("GET", "/projects/", token=token) or {}
    existing = resp.get("data", []) if isinstance(resp, dict) else resp
    proj_id = None
    for p in existing:
        if p.get("key") == project["key"]:
            proj_id = p["id"]
            print(f"  Project '{project['key']}' already exists (id={proj_id}), skipping.")
            break

    if proj_id is None:
        result = api("POST", "/projects/", body=project, token=token)
        if result is None:
            print("  Failed to create project — aborting.")
            sys.exit(1)
        proj_id = result["id"]
        print(f"  Created: {result['name']} (id={proj_id})")

    # ------------------------------------------------------------------ states
    print("\nCreating workflow states ...")
    existing_states = api("GET", f"/projects/{proj_id}/states", token=token) or []
    existing_names = {s["name"] for s in existing_states}
    state_map = {s["name"]: s["id"] for s in existing_states}

    for state in seed["states"]:
        if state["name"] in existing_names:
            print(f"  State '{state['name']}' already exists, skipping.")
            continue
        result = api("POST", f"/projects/{proj_id}/states", body=state, token=token)
        if result:
            state_map[result["name"]] = result["id"]
            print(f"  Created: {result['name']}")

    # Refresh state map in case some existed
    all_states = api("GET", f"/projects/{proj_id}/states", token=token) or []
    state_map = {s["name"]: s["id"] for s in all_states}

    # ------------------------------------------------------------------ requirements
    print("\nCreating requirements ...")
    resp = api("GET", f"/requirements/project/{proj_id}", token=token) or {}
    existing_reqs = resp.get("data", []) if isinstance(resp, dict) else resp
    existing_req_titles = {r["title"] for r in existing_reqs}

    for req in seed["requirements"]:
        if req["title"] in existing_req_titles:
            print(f"  Req '{req['title'][:60]}' already exists, skipping.")
            continue
        desired_status = req.pop("_status", None)
        post_body = {k: v for k, v in req.items() if not k.startswith("_")}
        result = api("POST", f"/requirements/project/{proj_id}", body=post_body, token=token)
        if result:
            req_id = result.get("req_id", "?")
            print(f"  Created: {req_id} — {result['title'][:60]}")
            if desired_status and desired_status != result.get("status"):
                api("PATCH", f"/requirements/{result['id']}", body={"status": desired_status}, token=token)
                print(f"    -> status set to '{desired_status}'")

    # ------------------------------------------------------------------ wiki
    print("\nCreating wiki pages ...")
    resp = api("GET", f"/wiki/project/{proj_id}", token=token) or {}
    existing_wiki = resp.get("data", []) if isinstance(resp, dict) else resp
    existing_wiki_titles = {w["title"] for w in existing_wiki}

    for page in seed["wiki"]:
        if page["title"] in existing_wiki_titles:
            print(f"  Wiki '{page['title'][:60]}' already exists, skipping.")
            continue
        result = api("POST", f"/wiki/project/{proj_id}", body=page, token=token)
        if result:
            print(f"  Created: {result['title'][:60]}")

    # ------------------------------------------------------------------ issues
    print("\nCreating issues ...")
    resp = api("GET", f"/issues/project/{proj_id}", token=token) or {}
    existing_issues = resp.get("data", []) if isinstance(resp, dict) else resp
    existing_issue_titles = {i["title"] for i in existing_issues}

    for issue in seed["issues"]:
        if issue["title"] in existing_issue_titles:
            print(f"  Issue '{issue['title'][:60]}' already exists, skipping.")
            continue

        state_name = issue.pop("state")
        state_id = state_map.get(state_name)
        if state_id is None:
            print(f"  WARNING: state '{state_name}' not found, placing in first state.")
            state_id = next(iter(state_map.values()), None)

        payload = {**issue, "status_id": state_id}
        result = api("POST", f"/issues/project/{proj_id}", body=payload, token=token)
        if result:
            seq = result.get("sequence_number", "?")
            print(f"  Created: {result.get('project_key','')}-{seq} {result['title'][:55]}")

        issue["state"] = state_name  # restore for idempotency on re-run

    print("\nDone.")


if __name__ == "__main__":
    main()
