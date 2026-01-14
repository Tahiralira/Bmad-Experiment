# Session Context - ClearDues Project

**Last Updated:** 2026-01-14
**Purpose:** Quick context load for new AI sessions. READ THIS FIRST.

---

## Project Status at a Glance

| Epic | Status | Stories |
|------|--------|---------|
| Epic 1: Auth | DONE | 6/6 |
| Epic 2: Groups & Dashboard | DONE | 4/4 |
| **Epic 2.5: UX Foundation** | **IN-PROGRESS** | 3/7 (2.5.1-2.5.3 done) |
| Epic 3: Expenses | PAUSED | 1/8 (3.1 done, waiting for 2.5) |
| Epic 4-7 | BACKLOG | 0/18 |
| Epic 8: UX Polish | BACKLOG (Post-MVP) | 0/4 |

**Current Progress:** 14 stories completed/in-review, 32 remaining

> **IMPORTANT:** Epic 2.5 was inserted AFTER Epic 3 started. Complete Epic 2.5 FIRST before resuming Epic 3. The UX foundation is required for remaining Epic 3 stories.

---

## Critical Files to Check

Before starting ANY work, check these logs:

| File | Purpose | When to Check |
|------|---------|---------------|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Current story status | Always |
| `_bmad-output/implementation-artifacts/solution-patterns.yaml` | Known issues & fixes | When debugging |
| `_bmad-output/implementation-artifacts/technical-debt-log.yaml` | Deferred issues | During reviews |
| `_bmad-output/session-context.md` | This file | Start of session |

---

## Key Learnings (Token Savers)

### Docker Issues
- **"ModuleNotFoundError in container"** → Rebuild: `docker compose build --no-cache`
- **"Connection refused localhost:5432"** → Use service name `db` not `localhost`
- **"File changes not visible in Docker"** (Windows) → Use `docker compose cp` to sync files

### Import Issues
- **Circular imports between features** → Import inside function OR use `TYPE_CHECKING`
- Example: `auth.service` imports `groups.models` inside function (see service.py:266)

### Frontend Patterns
- **TanStack Router**: Use `_layout` prefix, `$param.tsx` for dynamic routes
- **TanStack Query**: Always `invalidateQueries` after mutations
- **Framer Motion**: Use `TargetAndTransition` type, not `Variants` when passing animations to `animate` prop directly
- **Focus Management**: When managing refs for focus, use callback refs (`(el) => refsArray[index] = el`) rather than `useRef` alone

### Testing
- **Tests pass alone, fail together** → Database state leaking, use rollback fixtures

---

## Architecture Quick Reference

```
Backend: FastAPI + SQLModel + PostgreSQL
Frontend: React + TypeScript + Vite + TanStack (Router + Query)
Infra: Docker Compose (dev), Railway (prod target)

Directory Pattern: Feature-based
- backend/app/features/{name}/ → models.py, service.py, router.py
- frontend/src/features/{name}/ → types.ts, api/, components/

Naming:
- API/DB: snake_case
- Frontend code: camelCase
- Components: PascalCase
```

---

## Common Commands

```bash
# Start everything
docker compose up -d

# Backend tests
docker compose exec backend pytest -v

# Frontend type check
cd cleardues/frontend && npm run typecheck

# Frontend build
cd cleardues/frontend && npm run build
```

---

## What NOT to Do (Past Mistakes)

1. **Don't skip log checks** - Solution patterns file has saved hours of debugging
2. **Don't assume localhost works in Docker** - Use service names
3. **Don't forget query invalidation** - Frontend will show stale data
4. **Don't create circular imports** - Plan module dependencies first
5. **Don't mark tasks done without evidence** - Code review WILL catch false claims

---

## Next Up

**Epic 2.5: UX Foundation & Design System** (7 stories)
- Story 2.5.1: Design System Token Migration ← **DONE** ✓
- Story 2.5.2: Agent Orb Component ← **DONE** ✓
- Story 2.5.3: Orbital Navigation System ← **DONE** ✓
- Story 2.5.4: Smart Input Modal Foundation ← **NEXT** (ready for create-story)
- Story 2.5.5: Swipeable Card Base Component
- Story 2.5.6: Balance Display Component
- Story 2.5.7: Update Existing Screens

**Then:** Epic 3: Smart Expense Entry (8 stories, Story 3.1 done)

---

## How to Update This File

This file should be updated:
1. After completing each epic
2. When new critical learnings are discovered
3. When architecture changes significantly

Keep it SHORT - this is meant for quick loading, not comprehensive docs.
