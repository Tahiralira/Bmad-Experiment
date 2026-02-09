# Session Context - ClearDues Project

**Last Updated:** 2026-02-09 (Story 3.6 ready-for-dev - Split Logic Unequal Custom Amounts)
**Purpose:** Quick context load for new AI sessions. READ THIS FIRST.

---

## Project Status at a Glance

| Epic | Status | Stories |
|------|--------|---------|
| Epic 1: Auth | DONE | 6/6 |
| Epic 2: Groups & Dashboard | DONE | 4/4 |
| **Epic 2.5: UX Foundation** | **DONE** | 7/7 ✅ |
| Epic 3: Expenses | **IN-PROGRESS** | 5/8 (3.1-3.5 done) |
| Epic 4-7 | BACKLOG | 0/18 |
| Epic 8: UX Polish | BACKLOG (Post-MVP) | 0/4 |

**Current Progress:** 21 stories completed, 25 remaining (Story 3.6 ready for development)

> **IMPORTANT:** Story 3.6 (Unequal Custom Amounts) ready for development! This story enables users to specify custom amounts for each group member with real-time validation feedback. Builds on Story 3.5's split foundation.

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

---

## Next Up

**Epic 3: Smart Expense Entry** 🔄 IN-PROGRESS (5/8 done, 1 ready-for-dev)
- Story 3.1: Create Expense Model and Basic Entry ← **DONE** ✓
- Story 3.2: Natural Language Input Interface ← **DONE** ✓
- Story 3.3: AI Parsing Service Integration ← **DONE** ✓
- Story 3.4: Manual Override of Parsed Data ← **DONE** ✓
- Story 3.5: Split Logic - Equal Split ← **DONE** ✓
- Story 3.6: Split Logic - Unequal Custom Amounts ← **READY FOR DEV**
- Story 3.7: Split Logic - Percentage Split ← **NEXT**
- Story 3.8: Exclude Members from Expense

**Key Pattern from Story 3.5 Code Review:**
- Always call split mutation AFTER expense creation (needs expense ID from response)
- Add `onError` toast notifications to all mutations
- Add reverse relationships to User model for efficient queries
- GroupMember type has both `id` (join table) and `user_id` (actual user) - use `user_id` consistently

---

## How to Update This File

This file should be updated:
1. After completing each epic
2. When new critical learnings are discovered
3. When architecture changes significantly

Keep it SHORT - this is meant for quick loading, not comprehensive docs.
