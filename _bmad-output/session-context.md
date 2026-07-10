# Session Context - ClearDues Project

**Last Updated:** 2026-07-10 (WS5 done — ledger API + group screen: core loop operable end-to-end)
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
| **Epic 5: Settlement** | **IN-PROGRESS** | 2/3 |
| Epic 6-7 | BACKLOG | 0/18 |
| Epic 8: UX Polish | BACKLOG (Post-MVP) | 0/4 |

**Current Progress:** 32 stories completed, 13 remaining (Story 5.2 done ✅)

> **IMPORTANT:** Work now runs from the execution plan
> (`_bmad-output/product-review/10-execution-plan.md`), not story-by-story.
> WS1 (gates) DONE 2026-07-07: pytest green (the `GroupSettings | None` blocker is
> FIXED), frontend typecheck/tests/build green, root-level CI live.
> WS2 (design direction) DONE 2026-07-07: **Direction A "Quiet Ink" adopted** —
> see `_bmad-output/planning-artifacts/ux-design-spec-v2.md` (supersedes v1 spec).
> WS3 (design implementation) DONE 2026-07-09 on branch `ws3/quiet-ink`: v2
> tokens live, brand floor laid (ClearDues name/favicon/logomark, FastAPI
> branding deleted), orb → FAB, framer-motion + react-icons purged, main chunk
> **435.6 → 170.6 kB gz** (budget ≤250 ✓), fonts 0 KB. Screenshots:
> `_bmad-output/implementation-artifacts/ws3-screenshots/`. Key learnings:
> (1) `import * as Icons from "lucide-react"` bundled the whole icon set AND
> its kebab-case lookups silently rendered no icon — always import icons by
> name; (2) `preview_screenshot` MCP tool times out against the Vite dev
> server — use Playwright directly for visual proof; (3) devtools packages must
> be version-pinned to the app's router (1.142.11), latest peer-conflicts.
> WS4 (ledger integrity, backend) DONE 2026-07-09 on branch
> `ws4/ledger-integrity`: (a) consent contract — editing amount/payer or
> rejecting a split reverts the expense to DRAFT and deletes ALL splits (no
> silent redistribution, B-H2/H3); (b) **ARCH-001 canonical transaction
> pattern** — services flush, routers commit ONCE, audit entries atomic with
> operations (B-H5); (c) settlement rejection returns truthful
> REJECTED+rejected_at (B-H4); (d) user deletion is SOFT (anonymize + block
> while unsettled) with CASCADE→RESTRICT FK migration `b8c9d0e1f2a3` (B-C4);
> (e) FOR UPDATE row locks on confirm/reject/settle paths, IntegrityError→409
> (B-M8); (f) dashboard balances Decimal-to-the-wire as strings, frontend
> types updated (B-M1); (g) twin membership helper killed — keyword-only
> `is_group_member(session, *, group_id, user_id)` (B-M10, mechanically fixed
> B-C1). Backend **203 passed / 2 skipped**; frontend gates green.
> Key learnings: (1) anonymized emails must avoid `.invalid`/`.test`
> (email-validator special-use rejection → 500 on response serialization);
> (2) compose `develop.watch` sync is NOT active on long-running containers —
> `docker compose cp` before every in-container pytest run.
> WS5 (Ledger API + Group Screen) DONE 2026-07-10 on branch `ws5/ledger-api`:
> **the core loop is user-operable for the first time** — proven in the
> browser: create → split → confirm → settle → view, all reachable from the
> app entry point. (a) Ledger read API (B-H7): GET expense / expense splits
> (with names) / group detail (member_count + caller's net_balance) / group
> expenses (caller's split LEFT-JOINed per row); group-scoped
> settlement-claims (S4-M6). (b) Split endpoint typed: discriminated-union
> `SplitRequest` + one `apply_split()` service fn — malformed bodies 422, no
> more 500s (B-H6). (c) **`alembic check` clean for the first time** (B-H9):
> models pin sa_type aware timestamps + non-native enums + FK ondelete;
> migration c4d5e6f7a8b9 fixed the stray naive/unbounded columns. (d)
> `/groups/$groupId` deep-linkable GroupLedgerScreen (S4-H3/C4) mounting
> ConfirmedExpenseCard / PendingSettlementsList / SettlementClaimsList /
> AuditLogList; expense entry wired with group selector in SmartInputModal +
> real auth user (S4-C1); 401-only logout, 403 → toast (S4-H1); split-math
> fixes (S4-M1/M2). Dashboard last_activity now reflects expense writes
> (B-M2). Backend **210 passed / 2 skipped**; frontend **88 passed / 2
> skipped**, main chunk 172.3 kB gz.
> Key learnings: (1) expense/split/claim amounts were ALWAYS strings on the
> wire (pydantic Decimal) — the frontend `number` types + `.toFixed()` only
> survived because those components were unmounted dead code; wire types are
> now strings end-to-end. (2) TanStack Router: a child route under a parent
> WITHOUT an `<Outlet/>` never renders — un-nest with a trailing underscore
> (`groups_.$groupId.tsx` → /groups/$groupId). (3) SQLAlchemy enum columns
> store NAMES ("DRAFT") not values — reconcile DDL with
> `sa.Enum(native_enum=False, length=N)`, never switch to sa.String (silent
> data mismatch). (4) SQLModel `Field(sa_type=..., ondelete=...)` is enough
> to make autogenerate agree with hand-written migrations — no sa_column
> rewrites needed.
> **Next: WS6 (Aggregate Settle-Up + Confirmation Policy) — or WS7/WS8 per
> dependency map (WS5 unblocked both).**

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
- **Framer Motion**: REMOVED in design v2 (WS3) — do not add it back; use CSS transitions/`tw-animate-css` utilities (see ws3-implementation-kit.md Task 6 recipe)
- **Focus Management**: When managing refs for focus, use callback refs (`(el) => refsArray[index] = el`) rather than `useRef` alone
- **Modal Animations**: When animating from a specific element position, use `originX` and `originY` to set transform origin
- **Focus Return Timing**: Focus return timeout must be longer than exit animation duration (e.g., 250ms > 200ms animation)
- **Typography for Numbers**: SUPERSEDED by design v2 — `tabular-nums` is MANDATORY on every monetary amount and digit column (ux-design-spec-v2.md §3.3). The old proportional-nums guidance is void.
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
19. **Don't assume "check all X done" works when owner has their own record** — When using check_all_X patterns, verify the owner's record can reach the target status or needs auto-transition

---

## Next Up

**Plan of record:** `_bmad-output/product-review/10-execution-plan.md` (WS1–WS13 → beta)
- WS1 Gates & Truth ← **DONE** ✓ (2026-07-07; both suites green, CI live)
- WS2 Design Direction v2 ← **DONE** ✓ (2026-07-07; "Quiet Ink" adopted)
- WS3 Design System Implementation ← **DONE** ✓ (2026-07-09; branch ws3/quiet-ink)
- WS4 Ledger Integrity (backend) ← **DONE** ✓ (2026-07-09; branch
  ws4/ledger-integrity; consent revert, ARCH-001 transactions, soft delete,
  row locks, Decimal wire; backend 203 passed)
- WS5 Ledger API + Group Screen ← **DONE** ✓ (2026-07-10; branch
  ws5/ledger-api; read endpoints, typed split schemas, alembic check clean,
  /groups/$groupId ledger screen, expense entry wired — core loop operable
  end-to-end in the browser; backend 210 passed, frontend 88 passed)
- WS6 Aggregate Settle-Up + Confirmation Policy ← **NEXT** (settle-with-X
  netting, 72h auto-confirm, per-group strict mode, pairwise balance view);
  WS7 (real AI) is also unblocked and can run in parallel

**Key WS2 decisions for WS3:** framer-motion deleted, no shadows at rest, template
components (Items/Admin/ChangePassword) NOT restyled (deleted in WS8), one
choreographed animation only (settle moment ≤400ms), Google Fonts @import removed.

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

**Key Pattern from Story 5.2 Code Review:**
- When using "check all X done" patterns, verify the entity OWNER's own record can reach the target status — auto-settle the payer's split when confirming settlement claims
- Batch-fetch related entities (users) instead of per-row lookups in JOIN query result loops
- Extract shared error handling helpers (`_handle_settlement_result`) to deduplicate sentinel→HTTPException translation
- Don't use `useCallback` with `useMutation()` as a dep — mutation object changes every render, making the memoization useless

---

## How to Update This File

This file should be updated:
1. After completing each epic
2. When new critical learnings are discovered
3. When architecture changes significantly

Keep it SHORT - this is meant for quick loading, not comprehensive docs.
