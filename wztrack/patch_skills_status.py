"""Patch the three skills items to set status_id = Backlog and fix seed script."""
import requests

BASE = "http://localhost:8000/api/v1"
DEVENV = "e020829c-11d1-4f21-9ee6-5d69f02b1ff3"
ISSUE_IDS = [
    "b34bfad9-0364-4979-a168-483ac9a095c5",
    "3886b53d-d9f1-4a0f-bb69-80c6caf022ee",
    "bd1cf6b6-abd1-485f-8684-570b1604b2a9",
]

r = requests.post(f"{BASE}/auth/login", json={"email": "admin@wztrack.io", "password": "admin1234"})
r.raise_for_status()
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

states = requests.get(f"{BASE}/projects/{DEVENV}/states/", headers=h).json()
backlog = next((s for s in states if s["name"].lower() == "backlog"), states[0])
print(f"Backlog: {backlog['id']} ({backlog['name']})")

for issue_id in ISSUE_IDS:
    r = requests.patch(f"{BASE}/issues/{issue_id}", json={"status_id": backlog["id"]}, headers=h)
    r.raise_for_status()
    print(f"  ✓ {r.json()['title']}")

print("Done.")
