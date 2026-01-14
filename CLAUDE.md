# Project Context: ClearDues

ClearDues is an AI-powered "Agentic Mediator" PWA designed to manage and settle shared expenses with "Progressive Urgency" notifications.

## CRITICAL: Session Startup Protocol

**BMAD workflows automatically load tracking files via pre-hooks (Step 0).**

When running `/bmad:bmm:workflows:dev-story` or `/bmad:bmm:workflows:code-review`, these files are auto-loaded:

| File | Purpose | Auto-Loaded | Auto-Updated |
|------|---------|-------------|--------------|
| `session-context.md` | Project status, key learnings | Yes (Step 0) | Yes (Post-hook) |
| `sprint-status.yaml` | Epic/story progress | Yes (Step 1) | Yes (Step 9/5) |
| `solution-patterns.yaml` | Known issues and fixes | Yes (Step 0) | Yes (Post-hook) |
| `technical-debt-log.yaml` | Deferred LOW issues | Yes (Step 0) | Yes (code-review) |

**For non-BMAD work**, manually load these files first:
1. `_bmad-output/session-context.md` - Quick context
2. `_bmad-output/implementation-artifacts/sprint-status.yaml` - Current progress
3. `_bmad-output/implementation-artifacts/solution-patterns.yaml` - Debugging help

**Full setup guide:** `_bmad/bmm/docs/TRACKING-SETUP-GUIDE.md`

## 📊 Current Status

| Epic | Status | Progress |
|------|--------|----------|
| Epic 1: Auth | DONE | 6/6 |
| Epic 2: Groups & Dashboard | DONE | 4/4 |
| **Epic 2.5: UX Foundation** | **NEXT** | 0/7 |
| Epic 3: Expenses | IN-PROGRESS | 1/8 |
| Epic 4-7 | BACKLOG | 0/18 |
| Epic 8: UX Polish | BACKLOG (Post-MVP) | 0/4 |

**Next:** Epic 2.5, Story 2.5.1 - Design System Token Migration

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

## 🚀 Commands

```bash
# Start everything
docker compose up -d

# Backend tests
docker compose exec backend pytest -v

# Frontend type/build check
cd cleardues/frontend && npm run typecheck && npm run build

# Alembic migrations
docker compose exec backend alembic upgrade head
```

## Known Issues Quick Reference

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError in Docker | `docker compose build --no-cache` |
| Connection refused localhost:5432 | Use service name `db` not `localhost` |
| Circular import error | Import inside function or use TYPE_CHECKING |
| Route not found 404 | Check TanStack Router file naming conventions |
| Data not updating after mutation | Add `queryClient.invalidateQueries` |

**Full solutions:** See `solution-patterns.yaml`

## Logging Requirements

**BMAD workflows automatically update tracking files via post-hooks.**

| Workflow | Auto-Updates |
|----------|--------------|
| `dev-story` | session-context.md, solution-patterns.yaml (if new issues solved) |
| `code-review` | session-context.md, technical-debt-log.yaml (LOW items), solution-patterns.yaml (if patterns found) |

**For non-BMAD work**, manually update when:
1. **New issue solved** -> Add to `solution-patterns.yaml` (symptoms, cause, solution, prevention)
2. **Critical learning** -> Update `session-context.md`
3. **Deferred LOW issue** -> Add to `technical-debt-log.yaml`

## References

### Planning
- [PRD](./_bmad-output/planning-artifacts/prd.md)
- [Architecture](./_bmad-output/planning-artifacts/architecture.md)
- [Epics](./_bmad-output/planning-artifacts/epics.md)
- [UX Design Specification](./_bmad-output/planning-artifacts/ux-design-specification.md)
- [Design Artifact Plan](./_bmad-output/planning-artifacts/design-artifact-plan.md)

### Tracking (Auto-managed by BMAD)
- [Sprint Status](./_bmad-output/implementation-artifacts/sprint-status.yaml)
- [Solution Patterns](./_bmad-output/implementation-artifacts/solution-patterns.yaml)
- [Technical Debt](./_bmad-output/implementation-artifacts/technical-debt-log.yaml)
- [Session Context](./_bmad-output/session-context.md)

### Guides
- [BMAD Usage Guide](./_bmad/bmm/docs/BMAD-USAGE-GUIDE.md) - Complete workflow guide from planning to deployment
- [Tracking Setup Guide](./_bmad/bmm/docs/TRACKING-SETUP-GUIDE.md) - Pre/post hooks and tracking files documentation
