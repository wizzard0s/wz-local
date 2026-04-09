# wz_local

Local development suite for the WZ workspace.

## Purpose

`wz_local` contains real, running project instances. These are not generic or reusable templates — they are the live tools the WZ team uses day-to-day. A project starts here, gets proven, and is later extracted into `wz_systems` as a generic suite member when it is stable enough to serve other teams or contexts.

## Subprojects

| Subproject | Status | Description |
|---|---|---|
| `wztrack/` | active | WZTrack project management tool |

## Suite contract

- Every subproject has its own `docker-compose.yml`, `backend/`, and `frontend/` (or equivalent stack).
- Every subproject is tracked as a project inside WZTrack itself (under the WZT project key).
- Local credentials and keys live in `.env` at the subproject root — never committed.
- A subproject is ready for promotion to `wz_systems` when: it has passing tests, Alembic migrations, and a `.env.example`.
