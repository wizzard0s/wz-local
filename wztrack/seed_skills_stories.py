"""
Seed DEVENV stories for requirements_elicitation and story_writer skills.
Creates one epic + two stories in WZTrack DEVENV project.
"""
import requests

BASE = "http://localhost:8000/api/v1"
DEVENV_PROJECT_ID = "e020829c-11d1-4f21-9ee6-5d69f02b1ff3"

def login():
    r = requests.post(f"{BASE}/auth/login", json={"email": "admin@wztrack.io", "password": "admin1234"})
    r.raise_for_status()
    return r.json()["access_token"]

def get_state_id(token, name="Backlog"):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/projects/{DEVENV_PROJECT_ID}/states/", headers=headers)
    r.raise_for_status()
    states = r.json()
    for s in states:
        if s.get("name", "").lower() == name.lower():
            return s["id"]
    return states[0]["id"]

def create_issue(token, state_id, payload):
    headers = {"Authorization": f"Bearer {token}"}
    payload["status_id"] = state_id  # API field is status_id, not state_id
    r = requests.post(f"{BASE}/issues/project/{DEVENV_PROJECT_ID}", json=payload, headers=headers)
    r.raise_for_status()
    return r.json()

def main():
    token = login()
    print("Logged in.")
    state_id = get_state_id(token, "Backlog")
    print(f"Backlog state ID: {state_id}")

    # Epic
    epic = create_issue(token, state_id, {
        "title": "Reusable elicitation and story writing skills",
        "description": (
            "**Why this epic exists**\n"
            "Formalise the two-skill workflow used to gather requirements and produce sprint-ready stories "
            "so that every feature built across the Wizzard suite starts with a precise spec and ends with "
            "INVEST-compliant stories. These skills replace ad-hoc questioning and story writing.\n\n"
            "**Skills in scope**\n"
            "- `requirements_elicitation` — structured stakeholder interview → YAML spec\n"
            "- `story_writer` — YAML spec → INVEST stories + GWT acceptance criteria\n\n"
            "**Out of scope**\n"
            "- Story points calibration (covered by team norms)\n"
            "- Sprint assignment or backlog ordering"
        ),
        "type": "Epic",
        "priority": "High",
    })
    epic_id = epic["id"]
    print(f"Epic created: {epic_id}")

    # Story 1 — requirements_elicitation skill
    s1 = create_issue(token, state_id, {
        "title": "Apply requirements_elicitation skill on every feature request",
        "description": (
            "As a developer or Copilot agent receiving a feature request,\n"
            "I need a way to run the `requirements_elicitation` skill before writing any code or stories,\n"
            "So that every feature starts with a fully-specified, testable requirements spec.\n\n"
            "---\n\n"
            "**Acceptance Criteria**\n\n"
            "**Scenario: New feature request arrives**\n\n"
            "Given a user or stakeholder describes a new capability in natural language\n"
            "When the `requirements_elicitation` skill is invoked\n"
            "Then the skill conducts up to three rounds of structured questions\n"
            "  And produces a YAML spec with all Five Dimensions populated\n"
            "  And the spec has no [TBD] fields before being marked as agreed\n\n"
            "**Scenario: Skill is skipped**\n\n"
            "Given a feature request arrives without an accompanying spec\n"
            "When a developer or agent attempts to write stories or code directly\n"
            "Then the work is blocked until the requirements_elicitation skill has been run\n"
            "  And the resulting YAML spec is linked to the stories\n\n"
            "---\n\n"
            "**Skill location:** `SKILLS/requirements_elicitation/`\n"
            "**Activation:** Described in `skill.yaml` — invoke whenever classification is `new-feature`, "
            "`problem-statement`, or `feature-request`.\n"
            "**Usage protocol:** This skill must always be used. It is not optional."
        ),
        "type": "Story",
        "priority": "High",
        "story_points": 1,
        "decisions": "Skill-first protocol is mandatory across all Wizzard projects.",
        "investigations": "Skill built in SKILLS/requirements_elicitation/. See instructions.md for full protocol.",
        "test_requirements": "Verify that the YAML spec output passes the Five Dimensions quality checklist.",
        "uat_criteria": "A feature request processed through the skill produces a spec that a developer can act on without a single follow-up question.",
    })
    print(f"Story 1 created: {s1['id']}")

    # Story 2 — story_writer skill
    s2 = create_issue(token, state_id, {
        "title": "Apply story_writer skill after every requirements spec",
        "description": (
            "As a developer or Copilot agent holding a completed requirements spec,\n"
            "I need a way to run the `story_writer` skill to convert it into sprint-ready stories,\n"
            "So that every story in WZTrack is INVEST-compliant and has testable acceptance criteria before sprint planning.\n\n"
            "---\n\n"
            "**Acceptance Criteria**\n\n"
            "**Scenario: Spec is ready for story writing**\n\n"
            "Given a YAML requirements spec with status = agreed exists\n"
            "When the `story_writer` skill is invoked\n"
            "Then it produces one story per functional requirement\n"
            "  And each story passes the INVEST filter\n"
            "  And each story has at least one unhappy-path Given/When/Then scenario\n"
            "  And each story includes a DoR checklist\n\n"
            "**Scenario: Story is too large**\n\n"
            "Given the story_writer estimates a story at more than 5 points\n"
            "When it outputs that story\n"
            "Then it also outputs a split recommendation using one of the nine splitting patterns\n"
            "  And no story with > 5 points enters the backlog without a split plan\n\n"
            "---\n\n"
            "**Skill location:** `SKILLS/story_writer/`\n"
            "**Activation:** Described in `skill.yaml` — invoke immediately after "
            "`requirements_elicitation` output is approved.\n"
            "**Usage protocol:** This skill must always be used. It is not optional."
        ),
        "type": "Story",
        "priority": "High",
        "story_points": 1,
        "decisions": "story_writer is the mandatory step between spec and backlog creation.",
        "investigations": "Skill built in SKILLS/story_writer/. See instructions.md for full protocol.",
        "test_requirements": "Verify INVEST filter passes for every story produced. Verify unhappy-path scenario present.",
        "uat_criteria": "QA can write a failing test from the acceptance criteria without asking for clarification.",
    })
    print(f"Story 2 created: {s2['id']}")
    print("\nAll done. Epic + 2 stories created in DEVENV.")

if __name__ == "__main__":
    main()
