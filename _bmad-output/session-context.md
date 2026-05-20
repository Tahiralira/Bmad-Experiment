# Session Context - ClearDues Project

**Last Updated:** 2026-05-19 (Story 4.5 code review complete - Epic 4 DONE!)
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
| Epic 5-7 | BACKLOG | 0/18 |
| Epic 8: UX Polish | BACKLOG (Post-MVP) | 0/4 |

**Current Progress:** 30 stories completed, 15 remaining (Epic 5 next)

> **IMPORTANT:** Story 4.5 (Activity Feed Display) CODE REVIEW COMPLETE! ✅ 10 issues found, 7 fixed (3 HIGH, 4 MEDIUM). Key fixes: useCallback-in-JSX anti-pattern, broken loading state, duplicate log entries, missing pagination on all-groups view, dead code removed, shared utility refactored.

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

---

## Next Up

**Epic 4: Trust & Confirmation Workflow** ✅ COMPLETE! (5/5 done)
- Story 4.1: Creator-Only Edit Restriction ← **DONE** ✓
- Story 4.2: Expense Confirmation Workflow ← **DONE** ✓
- Story 4.3: Finalize Expense After All Confirmations ← **DONE** ✓
- Story 4.4: Immutable Audit Log for All Actions ← **DONE** ✓
- Story 4.5: Activity Feed Display ← **DONE** ✓

**Epic 5: Settlement & Payment Tracking** ← **NEXT**
- Story 5.1: Mark Debt as Settled / Claim Payment

**Key Pattern from Story 4.3 Code Review:**
- Use `datetime.now(timezone.utc)` not deprecated `datetime.utcnow()`
- Use aggregated SQL (CASE expressions) instead of N+1 loops for balance calculations
- Redis clients should be module-level singletons, not created per function call
- Hide UI action buttons when entity status prevents action (e.g., confirmed expenses)
- Add REDIS_HOST/REDIS_PORT to config instead of reusing unrelated settings

**Key Pattern from Story 3.5 Code Review:**
- Always call split mutation AFTER expense creation (needs expense ID from response)
- Add `onError` toast notifications to all mutations
- Add reverse relationships to User model for efficient queries
- GroupMember type has both `id` (join table) and `user_id` (actual user) - use `user_id` consistently

**Key Pattern from Story 3.6 Code Review:**
- Safe UUID conversion: Check `isinstance(user_id, UUID)` before converting (handles both string and UUID objects)
- Frontend NaN handling: `parseFloat("")` returns `NaN`, validate with `!isNaN(value)` before using
- Null safety: Use explicit null checks for optional fields (e.g., `member.full_name ? ... : ...`)
- Loading states: Disable buttons during mutations with `isPending` flag and show "Saving..." text
- State reset: Clear custom amounts when switching away from unequal split to avoid stale data

---

## How to Update This File

This file should be updated:
1. After completing each epic
2. When new critical learnings are discovered
3. When architecture changes significantly

Keep it SHORT - this is meant for quick loading, not comprehensive docs.
