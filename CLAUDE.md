# Project Context: ClearDues

ClearDues is an AI-powered "Agentic Mediator" PWA designed to manage and settle shared expenses with "Progressive Urgency" notifications.

## 🛠 Tech Stack
- **Backend**: FastAPI (Python) + SQLModel (ORM)
- **Frontend**: React + TypeScript + Vite + Redux Toolkit + TanStack Query
- **Database**: PostgreSQL
- **Real-Time**: WebSockets + Redis Pub/Sub
- **Worker**: Celery + Redis
- **Infra**: Docker + Railway (Target)

## 📐 Architectural Patterns
- **Directory Structure**: Feature-based (`/backend/app/features/{name}`, `/frontend/src/features/{name}`)
- **Naming Conventions**: 
  - API/DB: `snake_case`
  - Frontend Code: `camelCase` (Components in `PascalCase`)
- **State Management**: Redux for UI state; TanStack Query for server state.
- **Communication**: Redis events named `domain.entity.action`.
- **Boundaries**: Strictly use the Service Layer for DB access.

## 🚀 Commands (Standard Starter)
- **Install**: `npm install` (frontend), `poetry install` (backend)
- **Dev**: `docker-compose up`
- **Frontend Test**: `npm test`
- **Backend Test**: `pytest`
- **Migrations**: `alembic upgrade head`

## 📊 Current Status
- **Phase**: Solutioning Complete -> Implementation Starting.
- **Next Task**: **Epic 1: Story 1.1** - Initialize project using the `full-stack-fastapi-template`.
- **References**: 
  - [prd.md](./_bmad-output/planning-artifacts/prd.md)
  - [architecture.md](./_bmad-output/planning-artifacts/architecture.md)
  - [epics.md](./_bmad-output/planning-artifacts/epics.md) (35 stories defined)
