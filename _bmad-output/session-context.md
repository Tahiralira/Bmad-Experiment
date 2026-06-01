# Session Context - ClearDues Project

**Last Updated:** 2026-06-01 (Story 5.1 code review complete - Epic 5 in progress!)
**Purpose:** Quick context load for new AI sessions. READ THIS FIRST.

---

## Project Status at a Glance

| Epic | Status | Stories |
|------|--------|---------|
| Epic 1: Auth | DONE | 6/6 |
| Epic 2: Groups & Dashboard | DONE | 4/4 |
| **Epic 2.5: UX Foundation** | **DONE** | 7/7 ✅ |
| Epic 3: Expenses | **DONE** | 8/8 ✅ |
| **Epic 4: Trust & Confirmation** | **DONE** | 5/5 ✅ |
| **Epic 5: Settlement** | **IN-PROGRESS** | 1/3 |
| Epic 6-7 | BACKLOG | 0/18 |
| Epic 8: UX Polish | BACKLOG (Post-MVP) | 0/4 |

**Current Progress:** 31 stories completed, 14 remaining (Story 5.1 done ✅)

> **IMPORTANT:** Story 5.1 code review PASSED — 6 issues found and fixed (3 HIGH, 3 MEDIUM). Key fixes: ValueError→HTTPException pattern, N+1 query→JOIN, optimistic UI error recovery. Pre-existing test suite issue (`GroupSettings | None` SQLAlchemy error) blocks pytest.

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
- **Modal Animations**: When animating from a specific element position, use `originX` and `originY` to set transform origin
- **Focus Return Timing**: Focus return timeout must be longer than exit animation duration (e.g., 250ms > 200ms animation)
- **Typography for Numbers**: Use `proportional-nums` for inline text (natural flow), NOT `tabular-nums` (monospace). Only use tabular-nums for data tables where alignment matters.
- **Streaming Text Effect**: Use `setInterval` with character-by-character string concatenation for natural reading pace (30-50ms per character). Cleanup intervals on unmount to prevent memory leaks. Use refs to avoid stale closure issues in setInterval callbacks.
- **Feature-Specific Components**: Create feature-specific versions of generic UI components (e.g., `/features/expenses/components/SmartInputModal` vs `/components/ui/smart-input-modal`) for better separation of concerns.

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
6. **Don't let story File List drift from git reality** - Update File List after EVERY commit to match actual changes
7. **Don't claim testing without documentation** - Add testing evidence section (browsers, breakpoints tested, accessibility checks)
8. **Don't leave unused variables** - Fix TypeScript "declared but never used" errors immediately
9. **Don't use deprecated session.query()** - Use `session.exec(delete(...))` or `session.exec(select(...))` in SQLModel
10. **Don't return `dict` from FastAPI endpoints** - Use proper response_model for OpenAPI schema generation
11. **Don't forget to invalidate all related queries** - After mutations, invalidate audit-log queries too
12. **Don't call useCallback inside JSX** - It's a rules-of-hooks violation; lift callbacks to the component level
13. **Don't duplicate utility functions** - Extract to shared utils and import from one place
14. **Don't forget pagination on aggregated views** - If one view has Load More, the combined view needs it too
15. **Don't use `X | None` type annotations in SQLModel Relationship fields** - SQLAlchemy's mapper tries to resolve `X | None` as a class name string and fails. Use `Optional[X]` or separate the annotation.
16. **Don't access `.router` on already-imported router objects** - `from x import router as y` then `y.router` fails. Use just `y`.
17. **Don't invent new error handling patterns** — Check how existing endpoints handle errors (HTTPException in router, not ValueError string-prefixes in service)
18. **Don't write optimistic UI without error recovery** — Always add `useEffect` to revert optimistic state when `mutation.isError` is true

---

## Next Up

**Epic 4: Trust & Confirmation Workflow** ✅ COMPLETE! (5/5 done + retro)

**Epic 5: Settlement & Payment Tracking** ← **IN-PROGRESS** (1/3)
- Story 5.1: Mark Debt as Settled / Claim Payment ← **DONE** ✓ (code review passed)
- Story 5.2: Owner Confirms Settlement ← **NEXT**
- Story 5.3: Settlement Audit Trail ← **BACKLOG**

**Pre-existing Issue Found:** `GroupSettings | None` SQLAlchemy relationship error in `ExpenseGroup` model breaks ALL pytest tests. Backend server runs fine. Needs fix before tests can run.

**Key Retro Agreement:** Fix issues as they appear — no deferred batch fixes.

**Key Pattern from Story 4.3 Code Review:**
- Use `datetime.now(timezone.utc)` not deprecated `datetime.utcnow()`
- Use aggregated SQL (CASE expressions) instead of N+1 loops for balance calculations
- Redis clients should be module-level singletons, not created per function call
- Hide UI action buttons when entity status prevents action (e.g., confirmed expenses)
- Add REDIS_HOST/REDIS_PORT to config instead of reusing unrelated settings

**Key Pattern from Story 5.1 Code Review:**
- Router handles validation (404, 400, 403, 409) with HTTPException — service returns result/sentinel
- Use JOIN queries for list endpoints that need related data (avoid N+1 per-item queries)
- Extract shared response builders (like `_build_claim_public`) to deduplicate field mapping
- Optimistic UI MUST have error recovery: `useEffect(() => { if (mutation.isError) revert() })`

---

## How to Update This File

This file should be updated:
1. After completing each epic
2. When new critical learnings are discovered
3. When architecture changes significantly

Keep it SHORT - this is meant for quick loading, not comprehensive docs.
