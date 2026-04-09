"""
WZTrack patch script — adds requirements and issues to an existing project.
Does not touch project/states/wiki. Idempotent: skips existing titles.

Usage:
    python patch_project.py --data-file seed_patch_wzt_story_standard.json
"""
import json
import sys
import argparse
import urllib.request
import urllib.error
import os

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@wztrack.io"
ADMIN_PASSWORD = "admin1234"


def api(method: str, path: str, body=None, token: str = None):
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


def main():
    global BASE_URL
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url",  default=BASE_URL)
    parser.add_argument("--email",     default=ADMIN_EMAIL)
    parser.add_argument("--password",  default=ADMIN_PASSWORD)
    parser.add_argument("--data-file", required=True)
    args = parser.parse_args()
    BASE_URL = args.base_url.rstrip("/")

    with open(args.data_file, encoding="utf-8") as fh:
        patch = json.load(fh)

    print(f"Logging in as {args.email} ...")
    token = login(args.email, args.password)
    print("OK\n")

    # Find project
    project_key = patch["project_key"]
    resp = api("GET", "/projects/", token=token) or {}
    projects = resp.get("data", [])
    proj = next((p for p in projects if p["key"] == project_key), None)
    if proj is None:
        print(f"Project '{project_key}' not found.")
        sys.exit(1)
    proj_id = proj["id"]
    print(f"Project: {proj['name']} (id={proj_id})\n")

    # Requirements
    if patch.get("requirements"):
        print("Patching requirements ...")
        resp = api("GET", f"/requirements/project/{proj_id}", token=token) or {}
        existing_titles = {r["title"] for r in resp.get("data", [])}
        for req in patch["requirements"]:
            if req["title"] in existing_titles:
                print(f"  Skipping (exists): {req['title'][:70]}")
                continue
            desired_status = req.pop("_status", None)
            post_body = {k: v for k, v in req.items() if not k.startswith("_")}
            result = api("POST", f"/requirements/project/{proj_id}", body=post_body, token=token)
            if result:
                print(f"  Created: {result.get('req_id')} — {result['title'][:70]}")
                if desired_status and desired_status != result.get("status"):
                    api("PATCH", f"/requirements/{result['id']}", body={"status": desired_status}, token=token)
                    print(f"    -> status: {desired_status}")

    # Issues
    if patch.get("issues"):
        print("\nPatching issues ...")
        # Get current state map
        all_states = api("GET", f"/projects/{proj_id}/states", token=token) or []
        state_map = {s["name"]: s["id"] for s in all_states}

        # Get existing issues (all pages)
        existing_titles = set()
        page = 1
        while True:
            resp = api("GET", f"/issues/project/{proj_id}?page={page}&page_size=100", token=token) or {}
            data = resp.get("data", [])
            existing_titles.update(i["title"] for i in data)
            meta = resp.get("meta", {})
            if page >= meta.get("pages", 1):
                break
            page += 1

        for issue in patch["issues"]:
            if issue["title"] in existing_titles:
                print(f"  Skipping (exists): {issue['title'][:70]}")
                continue
            state_name = issue.pop("state")
            state_id = state_map.get(state_name)
            if state_id is None:
                state_id = next(iter(state_map.values()), None)
                print(f"  WARNING: state '{state_name}' not found, using first state.")
            payload = {**issue, "status_id": state_id}
            result = api("POST", f"/issues/project/{proj_id}", body=payload, token=token)
            if result:
                print(f"  Created: {proj['key']}-{result['sequence_number']} {result['title'][:65]}")
            issue["state"] = state_name

    print("\nDone.")


if __name__ == "__main__":
    main()
