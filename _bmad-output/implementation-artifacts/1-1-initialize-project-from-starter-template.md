# Story 1.1: Initialize Project from Starter Template

Status: done

## Story

As a **development team**,
I want to initialize the project using the full-stack-fastapi-template,
so that we have a production-ready foundation with Docker, PostgreSQL, and modern tooling configured.

## Acceptance Criteria

1. **Given** the cookiecutter command is available
   **When** I run `cookiecutter https://github.com/tiangolo/full-stack-fastapi-template`
   **Then** the project is initialized with FastAPI backend, React frontend, PostgreSQL database, and Docker configuration

2. **And** the development environment runs successfully with `docker-compose up`

3. **And** the default authentication endpoints are accessible

## Tasks / Subtasks

- [x] Task 1: Install prerequisites (AC: #1)
  - [x] Verify Python 3.10+ is installed (Python 3.13.4)
  - [x] Verify Node.js 18+ is installed (v22.16.0)
  - [x] Verify Docker and Docker Compose are installed (Docker 28.1.1, Compose v2.35.1)
  - [x] Install cookiecutter: `pip install cookiecutter` (Note: Used direct git clone instead)

- [x] Task 2: Initialize project from template (AC: #1)
  - [x] Run: `git clone https://github.com/fastapi/full-stack-fastapi-template.git cleardues` (direct clone - cookiecutter not required)
  - [x] Configure project name as "ClearDues" (.env updated)
  - [x] Configure project slug as "cleardues" (.env updated)
  - [x] Accept default settings for other options
  - [x] Verify generated project structure (backend/, frontend/, docker-compose.yml present)

- [x] Task 3: Start development environment (AC: #2)
  - [x] Navigate to project directory
  - [x] Run: `docker-compose up -d`
  - [x] Verify all containers start successfully (backend, frontend, db, etc.)
  - [x] Check container logs for errors

- [x] Task 4: Verify authentication endpoints (AC: #3)
  - [x] Access API docs at `http://localhost:8000/docs`
  - [x] Test login endpoint: `POST /api/v1/login/access-token`
  - [x] Test user creation endpoint (if available)
  - [x] Verify JWT token generation works

- [x] Task 5: Document initial setup
  - [x] Record any environment-specific configurations
  - [x] Note any issues encountered and solutions

## Dev Notes

### Architecture Compliance

**CRITICAL:** This story establishes the foundation. The template provides:
- FastAPI backend with SQLModel ORM
- React + TypeScript + Vite frontend
- PostgreSQL database
- Docker Compose for local development
- Pre-built JWT authentication with OAuth2

**Source:** [architecture.md - Starter Template Evaluation](_bmad-output/planning-artifacts/architecture.md)

### Technical Stack (From Architecture)

| Component | Technology | Version |
|-----------|------------|---------|
| Backend Framework | FastAPI | Latest stable |
| ORM | SQLModel | Latest stable |
| Database | PostgreSQL | 15+ |
| Frontend | React + TypeScript | React 18+, TS 5+ |
| Build Tool | Vite | Latest stable |
| Package Manager | Poetry (backend), npm (frontend) | - |
| Containerization | Docker + Docker Compose | - |

### Initialization Command

```bash
cookiecutter https://github.com/tiangolo/full-stack-fastapi-template
```

**Expected Prompts:**
- `project_name`: ClearDues
- `project_slug`: cleardues
- `secret_key`: (generate random)
- `first_superuser_email`: admin@cleardues.local
- `first_superuser_password`: (set secure password)
- `postgres_server`: db
- `postgres_db`: app

### Expected Project Structure After Init

```
cleardues/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── crud/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── .env
```

### Project Structure Notes

**IMPORTANT:** After this story, Story 1.2 will reorganize to feature-based architecture:
- Backend: `/backend/app/features/{name}/`
- Frontend: `/frontend/src/features/{name}/`

Do NOT reorganize in this story - just initialize the template as-is.

### References

- [Source: architecture.md - Selected Starter](_bmad-output/planning-artifacts/architecture.md#selected-starter-full-stack-fastapi-template)
- [Source: architecture.md - Initialization Command](_bmad-output/planning-artifacts/architecture.md#initialization-command)
- [Source: epics.md - Story 1.1](_bmad-output/planning-artifacts/epics.md#story-11-initialize-project-from-starter-template)
- [Template Repo: github.com/tiangolo/full-stack-fastapi-template](https://github.com/tiangolo/full-stack-fastapi-template)

### Verification Commands

```bash
# Check Docker containers
docker-compose ps

# View backend logs
docker-compose logs backend

# Access API docs
open http://localhost:8000/docs

# Access frontend
open http://localhost:5173
```

### Known Considerations

1. **Windows Users:** May need WSL2 for Docker performance
2. **Port Conflicts:** Default ports are 8000 (backend), 5173 (frontend), 5432 (postgres)
3. **First Run:** Initial `docker-compose up` may take several minutes to build images

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101) via Claude Code CLI

### Debug Log References

- Docker containers verified running: `docker compose ps` showed all 6 services healthy
- Backend health check: `GET /api/v1/utils/health-check/` returning 200 OK
- API docs accessible at `http://localhost:8000/docs`

### Completion Notes List

1. **Template Method Changed**: Used `git clone` instead of `cookiecutter` as the template now uses `copier` (see `cleardues/copier.yml`). The AC referenced outdated cookiecutter approach.
2. **Project Configuration**: Updated `.env` with project name "ClearDues" and stack name "cleardues"
3. **All Services Running**: backend, frontend, db, adminer, mailcatcher, proxy (traefik) all healthy
4. **Auth Endpoints Available**: `/api/v1/login/access-token`, `/api/v1/users/signup`, `/api/v1/users/me` all present
5. **Security Fix**: Updated `.gitignore` to exclude `.env` files with secrets from version control

### File List

**Project Root (`cleardues/`)**
- `.env` - Environment configuration (gitignored - contains secrets)
- `.gitignore` - Updated with comprehensive exclusions
- `docker-compose.yml` - Production Docker configuration
- `docker-compose.override.yml` - Local development overrides
- `README.md` - Template documentation
- `LICENSE` - MIT License
- `copier.yml` - Template configuration

**Backend (`cleardues/backend/`)**
- `app/main.py` - FastAPI application entry point
- `app/api/main.py` - API router configuration
- `app/api/routes/login.py` - Authentication endpoints
- `app/api/routes/users.py` - User management endpoints
- `app/api/deps.py` - Dependency injection
- `app/core/config.py` - Settings management
- `app/core/security.py` - JWT and password utilities
- `app/models.py` - SQLModel database models
- `app/crud.py` - Database operations
- `pyproject.toml` - Python dependencies (uv/hatch)
- `Dockerfile` - Backend container definition
- `alembic.ini` - Database migrations config
- `app/alembic/` - Migration scripts

**Frontend (`cleardues/frontend/`)**
- `package.json` - Node.js dependencies
- `src/` - React + TypeScript source
- `Dockerfile` - Frontend container definition
- `vite.config.ts` - Vite build configuration

### Senior Developer Review (AI)

**Review Date:** 2026-01-06
**Reviewer:** Claude Opus 4.5 (Code Review Workflow)

**Findings Addressed:**
1. Updated `.gitignore` to exclude `.env` and other sensitive/generated files
2. Documented all implementation details in Dev Agent Record
3. Verified all ACs met with running containers

**Verification:**
- AC #1: Project initialized with FastAPI, React, PostgreSQL, Docker
- AC #2: `docker compose up` runs successfully (6 containers healthy)
- AC #3: Auth endpoints accessible at `/api/v1/login/*` and `/api/v1/users/*`

**Status:** APPROVED - Ready for commit
