# WZTrack — Architecture Document

**Document ID:** ARCH-WZTRACK-001
**Version:** 1.0
**Date:** 2025-01-01
**Status:** Approved

---

## Before you begin

Read `brd.md` for functional requirements. This document describes how WZTrack is structured — its layers, components, communication patterns, and directory layout.

---

## 1. System overview

WZTrack is a self-hosted, API-first project management and QA tracking platform. It consists of three main components that communicate over HTTP:

```
┌─────────────────────────────────────────┐
│              Browser (React SPA)        │
│      Ant Design v5 + Apache ECharts     │
└────────────────┬────────────────────────┘
                 │ HTTPS (REST JSON)
┌────────────────▼────────────────────────┐
│          FastAPI Backend (Python 3.12)  │
│   JWT RS256 auth · Pydantic v2 schemas  │
│   SQLAlchemy 2.0 async · asyncpg        │
└────────────────┬────────────────────────┘
                 │ asyncpg
┌────────────────▼────────────────────────┐
│       PostgreSQL — wztrack schema       │
│   Soft deletes · UUID PKs · JSONB       │
└─────────────────────────────────────────┘
```

File uploads are stored to a local filesystem volume. An S3-compatible adapter is planned for v2.

---

## 2. Technology decisions

| Layer | Technology | Version | Reason |
|---|---|---|---|
| Frontend framework | React | 18 | Established ecosystem, Ant Design support |
| UI component library | Ant Design | v5 | Complete component set, theme tokens |
| Frontend bundler | Webpack 5 | 5.x | Module Federation for future micro-frontend split |
| Charts | Apache ECharts | 5.x | Dashboards and burndown charts |
| Reports | Plotly.js | 2.x | Traceability matrix and data tables |
| Backend framework | FastAPI | 0.115.x | Async, automatic OpenAPI docs |
| Python runtime | CPython | 3.12 | Latest stable |
| ORM | SQLAlchemy | 2.0 async | Type-safe, async support |
| DB driver | asyncpg | 0.29.x | Async PostgreSQL |
| Data validation | Pydantic | v2 | Fast, type-driven |
| Auth | JWT RS256 | python-jose | Asymmetric signing |
| Password hashing | bcrypt | passlib[bcrypt] | OWASP recommended |
| Container | Docker + Compose | v2 | Single-command startup |

---

## 3. Directory structure

```
wztrack/
├── docs/                    ← Project documentation
│   ├── architecture.md      ← This file
│   ├── brd.md               ← Business requirements
│   └── data-model.md        ← DB schema + ERD description
├── backend/
│   ├── main.py              ← FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic/             ← DB migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   └── app/
│       ├── config.py        ← pydantic-settings env config
│       ├── database.py      ← async engine + session factory
│       ├── security.py      ← JWT + bcrypt helpers
│       ├── dependencies.py  ← FastAPI Depends declarations
│       ├── models/          ← SQLAlchemy ORM models
│       │   ├── base.py
│       │   ├── user.py
│       │   ├── project.py
│       │   ├── issue.py
│       │   ├── requirement.py
│       │   ├── wiki.py
│       │   └── testcase.py
│       ├── schemas/         ← Pydantic v2 request/response schemas
│       │   ├── auth.py
│       │   ├── user.py
│       │   ├── project.py
│       │   ├── issue.py
│       │   ├── requirement.py
│       │   ├── wiki.py
│       │   └── testcase.py
│       ├── routers/         ← FastAPI route handlers
│       │   ├── auth.py
│       │   ├── users.py
│       │   ├── projects.py
│       │   ├── issues.py
│       │   ├── requirements.py
│       │   ├── wiki.py
│       │   ├── testcases.py
│       │   └── traceability.py
│       └── services/        ← Business logic layer
│           ├── auth.py
│           ├── user.py
│           ├── project.py
│           ├── issue.py
│           ├── requirement.py
│           ├── wiki.py
│           └── testcase.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── webpack.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── theme.ts         ← Ant Design token configuration
│       ├── styles/
│       │   ├── global.css
│       │   └── tokens.css
│       ├── services/
│       │   └── api.ts       ← Axios instance + interceptors
│       ├── store/
│       │   └── auth.ts      ← Zustand auth store
│       ├── components/
│       │   ├── layout/
│       │   └── common/
│       └── pages/
│           ├── auth/
│           ├── dashboard/
│           ├── projects/
│           ├── kanban/
│           ├── backlog/
│           ├── requirements/
│           ├── wiki/
│           ├── testcases/
│           ├── traceability/
│           └── settings/
├── uploads/                 ← File upload volume (gitignored)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. Authentication flow

```
Client                    FastAPI                  PostgreSQL
   │                         │                          │
   │──POST /auth/login──────▶│                          │
   │                         │──SELECT user by email──▶│
   │                         │◀─user row────────────────│
   │                         │  bcrypt.verify()         │
   │◀──{access_token,        │                          │
   │    refresh_token}───────│                          │
   │                         │                          │
   │──GET /projects          │                          │
   │  Authorization: Bearer  │                          │
   │  <access_token>────────▶│                          │
   │                         │  jwt.decode(RS256)       │
   │                         │  Depends(get_current)    │
   │◀──200 {data: [...]}─────│                          │
```

- Access tokens: 60-minute expiry, RS256 signed, payload includes `user_id`, `email`, `role`
- Refresh tokens: 30-day expiry, stored as hash in `sessions` table
- Token rotation: each refresh issues a new refresh token and invalidates the old one

---

## 5. QA gate

The QA gate is the core integrity rule. When any issue state transition targets a state in the `done` category:

1. The API checks `SELECT COUNT(*) FROM test_results WHERE issue_id = ? AND status = 'pass'`
2. If count = 0, the API returns `HTTP 422` with `code: QA_GATE_BLOCKED`
3. An admin or manager may pass `"override_reason": "<text>"` in the request body to bypass the gate
4. The override is logged to the `audit_log` table with the reason and approver

---

## 6. API design

- Base path: `/api/v1/`
- All endpoints require `Authorization: Bearer <token>` except `/auth/login` and `/auth/register`
- List responses: `{ "data": [...], "meta": { "total": int, "page": int, "page_size": int, "pages": int } }`
- Error responses: `{ "error": { "code": str, "message": str, "details": any } }`
- Pagination: `?page=1&page_size=25` query params on all list endpoints
- HTTP status codes: 200, 201, 204, 400, 401, 403, 404, 422, 500

---

## 7. Data access rules

| Role | Create | Read | Update | Delete |
|---|---|---|---|---|
| admin | All | All | All | Soft delete all |
| manager | Issues, requirements, wiki, test plans | All in member projects | Issues, requirements, wiki, test plans | Issues (own) |
| developer | Issues, comments, wiki | All in member projects | Own issues | None |
| qa | Test cases, test runs, evidence | All in member projects | Own test results | None |
| viewer | None | All in member projects | None | None |

---

## 8. Deployment

WZTrack runs as three containers:

| Container | Image | Port |
|---|---|---|
| `wztrack-api` | `wztrack/backend:latest` | 8000 (internal) |
| `wztrack-fe` | `wztrack/frontend:latest` | 80 (nginx) |
| `wztrack-db` | `postgres:16-alpine` | 5432 (internal) |

A reverse proxy (nginx in the frontend container or external Caddy) terminates TLS and routes `/api/*` to the backend and everything else to the React SPA.

---

## 9. Security considerations

- CORS configured to allowed origins only — no wildcard in production
- File uploads: MIME type validation + extension allow-list + size limit (10 MB issues, 20 MB evidence)
- File paths stored as relative paths — never user-supplied paths written to disk
- Rate limiting on `/auth/login` — 10 req/min per IP
- RS256 private key stored as environment variable — never committed
- All SQL via SQLAlchemy ORM — no raw f-string queries
