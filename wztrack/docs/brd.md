# WZTrack — Business Requirements Document

**Document ID:** BRD-WZTRACK-001
**Version:** 0.1 — Draft
**Date:** 2026-04-09
**Author:** Nico de Beer
**Status:** Draft

---

## Before you begin

This document defines the business requirements for WZTrack — the internal project management and QA tracking platform for the Wizzard suite. Read the architecture document (`architecture.md`) and data model (`data-model.md`) alongside this document.

---

## 1. Objective

Build a self-hosted, open-source-licensed platform that replaces the need for Jira, Confluence, and TestRail. WZTrack must manage the full software delivery lifecycle for the Wizzard platform: from requirement capture through to QA sign-off and release.

**One clear takeaway:** A card cannot be marked Done without a linked passing test run. Every piece of work is traceable from requirement to evidence.

---

## 2. Scope

### In scope

- Project and workspace management
- Kanban board with custom workflow states
- Backlog management and sprint planning
- Requirements management (structured BRDs, SDDs, decision logs)
- Wiki with versioned pages and templates
- Test plan and test case management
- Test run execution with evidence capture
- Requirements traceability matrix
- User management and role-based access control
- Release readiness dashboard
- API-first design — all features accessible via REST API

### Out of scope (v1)

- Time tracking
- Customer-facing portal
- Email or SMS notifications (webhook support only in v1)
- Mobile app
- Git integration (planned v2)
- CI/CD pipeline integration (planned v2)

---

## 3. Stakeholders

| Role | Responsibility |
|---|---|
| Business analyst | Define requirements, review BRDs, manage backlog |
| Developer | Implement cards, link commits to issues |
| QA engineer | Write and execute test cases, capture evidence |
| Project manager | Sprint planning, release readiness review |
| Administrator | User management, project configuration |

---

## 4. Functional requirements

### 4.1 User management

| ID | Requirement |
|---|---|
| REQ-USR-001 | The system must support user registration with email and password |
| REQ-USR-002 | Passwords must be stored as bcrypt hashes — never plaintext |
| REQ-USR-003 | The system must support five roles: admin, manager, developer, qa, viewer |
| REQ-USR-004 | An admin must be able to change any user's role |
| REQ-USR-005 | A viewer may read all content but may not create or modify anything |
| REQ-USR-006 | The system must issue JWT access tokens (RS256) on login |
| REQ-USR-007 | Access tokens must expire after 60 minutes; refresh tokens after 30 days |
| REQ-USR-008 | A first admin account must be seeded on first startup from environment variables |

### 4.2 Projects

| ID | Requirement |
|---|---|
| REQ-PRJ-001 | A project has a unique key (e.g. CHAT, FLOW) used to prefix all issue IDs |
| REQ-PRJ-002 | Any authenticated user may view projects they are a member of |
| REQ-PRJ-003 | Only admin or manager may create a project |
| REQ-PRJ-004 | Each project has its own configurable workflow states |
| REQ-PRJ-005 | Workflow states have a category: backlog, in_progress, review, done, cancelled |
| REQ-PRJ-006 | A project must have at least one state in the done category to enable QA gate |

### 4.3 Issues (cards)

| ID | Requirement |
|---|---|
| REQ-ISS-001 | Every issue has an auto-incremented human-readable ID per project (CHAT-001) |
| REQ-ISS-002 | Issue types: epic, story, task, bug, subtask |
| REQ-ISS-003 | Priority levels: urgent, high, medium, low |
| REQ-ISS-004 | An issue may link to one or more requirement IDs |
| REQ-ISS-005 | An issue may have subtasks (one level only — no deep nesting) |
| REQ-ISS-006 | Moving an issue to a done-category state must check the QA gate |
| REQ-ISS-007 | QA gate: the issue must have at least one linked test run with status pass |
| REQ-ISS-008 | An admin or manager may override the QA gate with a written justification |
| REQ-ISS-009 | All state transitions must be recorded in an audit log with user and timestamp |
| REQ-ISS-010 | Issues may have file attachments (max 10 MB per file) |

### 4.4 Requirements

| ID | Requirement |
|---|---|
| REQ-REQ-001 | Every requirement has a stable auto-generated ID scoped to the project (REQ-CHAT-001) |
| REQ-REQ-002 | Requirement IDs must never be reused, even after deletion |
| REQ-REQ-003 | A requirement has: ID, title, description, acceptance criteria, status, created by, version |
| REQ-REQ-004 | Requirement status: draft, approved, implemented, verified |
| REQ-REQ-005 | All changes to a requirement must be versioned with a diff-viewable history |
| REQ-REQ-006 | A requirement in approved or later status requires manager approval to change |

### 4.5 Wiki

| ID | Requirement |
|---|---|
| REQ-WIKI-001 | Wiki pages are organized in a project-scoped page tree |
| REQ-WIKI-002 | Pages support rich text editing (headings, tables, code blocks, embedded images) |
| REQ-WIKI-003 | Every save creates a new version; all versions are stored and viewable |
| REQ-WIKI-004 | Page templates: blank, BRD, SDD, meeting notes, decision record, ADR |
| REQ-WIKI-005 | A page may be linked to issues and requirements by their IDs |
| REQ-WIKI-006 | Pages are full-text searchable across all projects the user has access to |

### 4.6 Test case management

| ID | Requirement |
|---|---|
| REQ-QA-001 | Test cases are organised under test plans |
| REQ-QA-002 | A test case has: title, preconditions, ordered steps, expected results, linked requirement IDs |
| REQ-QA-003 | A test run records: result (pass/fail/blocked/skipped), notes, evidence files, run by, run at |
| REQ-QA-004 | Evidence files may be screenshots, logs, or any file type (max 20 MB) |
| REQ-QA-005 | A failed test run must allow the tester to create a linked bug issue directly |
| REQ-QA-006 | A test plan has a status: draft, active, completed |
| REQ-QA-007 | Only a user with the qa or admin role may mark a test run as pass |

### 4.7 Traceability

| ID | Requirement |
|---|---|
| REQ-TRC-001 | The system must provide a traceability matrix view per project |
| REQ-TRC-002 | The matrix shows: requirement → linked issues → linked test cases → latest test run result |
| REQ-TRC-003 | Requirements with no linked issue are flagged as unplanned |
| REQ-TRC-004 | Requirements with no linked test case are flagged as untested |
| REQ-TRC-005 | The matrix must be exportable as CSV |

### 4.8 Dashboards and reporting

| ID | Requirement |
|---|---|
| REQ-RPT-001 | Project dashboard: open issues by status, sprint burndown, blocked items |
| REQ-RPT-002 | Release readiness: total issues, done count, QA pass rate, open blockers |
| REQ-RPT-003 | All charts use Apache ECharts |

---

## 5. Non-functional requirements

| ID | Requirement |
|---|---|
| REQ-NF-001 | API response time under 200 ms for all list endpoints (p95, local hardware) |
| REQ-NF-002 | All API endpoints require authentication except `POST /auth/login` and `POST /auth/register` |
| REQ-NF-003 | All data stored in the `wztrack` PostgreSQL schema — no cross-schema dependencies |
| REQ-NF-004 | The application must start cleanly from `docker compose up` with no manual DB setup |
| REQ-NF-005 | All file uploads stored on local filesystem (configurable path); S3-compatible in v2 |
| REQ-NF-006 | CORS must be restricted to configured origins — no wildcard in production |

---

## 6. Acceptance criteria (system-level)

A release of WZTrack is accepted when:

1. All REQ-USR-* requirements have at least one passing test run linked
2. All REQ-ISS-* requirements have at least one passing test run linked
3. A QA engineer can create a test plan, execute it, attach evidence, and close an issue end-to-end without leaving the tool
4. The traceability matrix shows 100% requirement coverage for at least one test project
5. The tool runs offline via `docker compose up` on a clean machine with no internet connection

---

## 7. Open items

| ID | Question | Owner | Status |
|---|---|---|---|
| OI-001 | Rich text editor — TipTap or ProseMirror directly? | Dev | Open |
| OI-002 | File storage path convention for Docker volume mount | Dev | Open |
| OI-003 | Export format for traceability matrix — CSV only or also PDF? | BA | Open |
