# WZTrack

Unified project management, requirements wiki, and QA tracking platform for the Wizzard suite.

## Features

- Kanban board — backlog, sprints, custom workflow states
- Requirements wiki — BRDs, SDDs, structured page templates with version history
- Test case management — test plans, test runs, evidence capture
- Requirements traceability — REQ-ID → card → test result
- User and role management — admin, manager, developer, QA, viewer
- Project maps and release readiness dashboards

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Ant Design v5 |
| Charting | Apache ECharts (dashboards) + Plotly.js (reports) |
| Bundler | Webpack 5 |
| Backend | Python 3.12 + FastAPI |
| Database | PostgreSQL — `wztrack` schema |
| Auth | JWT (RS256) |
| Container | Docker + Docker Compose |

## Before you begin

- Docker and Docker Compose installed
- PostgreSQL running (or use the compose stack)
- Node.js 20+ and Python 3.12+
- Copy `.env.example` to `.env` and fill in values

## Quick start

```bash
# Start the full stack
docker compose up -d

# Frontend dev server
cd frontend && npm install && npm run dev

# Backend dev server
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8097
```

## Project structure

```
wztrack/
  docs/           Planning documents — BRD, architecture, roadmap, standards
  backend/        FastAPI application
  frontend/       React application
  docker-compose.yml
  .env.example
```

## Ports

| Service | Port |
|---|---|
| Frontend (dev) | 3097 |
| Backend API | 8097 |
| PostgreSQL | 5432 (shared) |
