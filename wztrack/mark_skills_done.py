"""Mark the two skill stories and their epic as Done in DEVENV."""
import requests

BASE = "http://localhost:8000/api/v1"
DEVENV = "e020829c-11d1-4f21-9ee6-5d69f02b1ff3"

ISSUE_IDS = [
    ("b34bfad9-0364-4979-a168-483ac9a095c5", "Epic — Reusable elicitation and story writing skills"),
    ("3886b53d-d9f1-4a0f-bb69-80c6caf022ee", "Story — Apply requirements_elicitation skill"),
    ("bd1cf6b6-abd1-485f-8684-570b1604b2a9", "Story — Apply story_writer skill"),
]

r = requests.post(f"{BASE}/auth/login", json={"email": "admin@wztrack.io", "password": "admin1234"})
r.raise_for_status()
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

states = requests.get(f"{BASE}/projects/{DEVENV}/states/", headers=h).json()
done = next((s for s in states if s["name"].lower() == "done"), None)
if not done:
    # Try common alternatives
    done = next((s for s in states if s["name"].lower() in ("completed", "closed", "finished")), states[-1])
print(f"Done state: {done['id']} ({done['name']})")

for issue_id, label in ISSUE_IDS:
    r = requests.patch(f"{BASE}/issues/{issue_id}", json={"status_id": done["id"]}, headers=h)
    r.raise_for_status()
    print(f"  ✓ {label}")

print("\nAll skill stories marked as Done.")
