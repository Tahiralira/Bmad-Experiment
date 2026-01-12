# Project Context: ClearDues

ClearDues is an AI-powered "Agentic Mediator" PWA designed to manage and settle shared expenses with "Progressive Urgency" notifications.

## CRITICAL: Session Startup Protocol

**Before starting ANY work, load these files in order:**

1. **Quick Context** (ALWAYS): `_bmad-output/session-context.md`
   - Project status, key learnings, common mistakes to avoid

2. **Sprint Status** (ALWAYS): `_bmad-output/implementation-artifacts/sprint-status.yaml`
   - Current epic/story status, what's in progress

3. **Solution Patterns** (When debugging): `_bmad-output/implementation-artifacts/solution-patterns.yaml`
   - Known issues and their fixes (saves tokens by not re-debugging)

4. **Technical Debt** (During reviews): `_bmad-output/implementation-artifacts/technical-debt-log.yaml`
   - Deferred LOW severity issues to address later

**Why?** These logs contain learned solutions that save debugging time and tokens.

## 📊 Current Status

| Epic | Status | Progress |
|------|--------|----------|
| Epic 1: Auth | DONE | 6/6 |
| Epic 2: Groups & Dashboard | DONE | 4/4 |
| Epic 3: Expenses | BACKLOG | 0/8 |
| Epic 4-7 | BACKLOG | 0/18 |

**Next:** Epic 3, Story 3.1 - Create expense model and basic entry

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

When encountering and solving new issues:
1. **Add to solution-patterns.yaml** with symptoms, cause, solution, prevention
2. **Update session-context.md** if it's a critical learning
3. **Update technical-debt-log.yaml** for deferred LOW issues

## References

- [PRD](./_bmad-output/planning-artifacts/prd.md)
- [Architecture](./_bmad-output/planning-artifacts/architecture.md)
- [Epics](./_bmad-output/planning-artifacts/epics.md)
- [Sprint Status](./_bmad-output/implementation-artifacts/sprint-status.yaml)
- [Solution Patterns](./_bmad-output/implementation-artifacts/solution-patterns.yaml)
