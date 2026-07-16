# Project Context: ClearDues

ClearDues is an AI-powered "Agentic Mediator" PWA designed to manage and settle shared
expenses with "Progressive Urgency" notifications. Target market: **global** (no
hardcoded currency or market-specific rails — decided 2026-07-07).

## 📊 Current Status

**This file carries NO status of its own — hand-duplicated status rots.**
Always read the live sources:

1. `_bmad-output/implementation-artifacts/sprint-status.yaml` — epic/story progress
2. `_bmad-output/session-context.md` — latest learnings and context
3. `_bmad-output/product-review/10-execution-plan.md` — **the plan of record**: the
   consolidated work-session tracker driving current development (WS1–WS13 → private
   beta). The 9-session review behind it lives in `_bmad-output/product-review/`.

## CRITICAL: Session Startup Protocol

**BMAD workflows automatically load tracking files via pre-hooks (Step 0).**

When running `/bmad:bmm:workflows:dev-story` or `/bmad:bmm:workflows:code-review`,
these files are auto-loaded:

| File | Purpose | Auto-Loaded | Auto-Updated |
|------|---------|-------------|--------------|
| `session-context.md` | Project status, key learnings | Yes | Yes (post-hook) |
| `sprint-status.yaml` | Epic/story progress | Yes | Yes |
| `solution-patterns.yaml` | Known issues and fixes | Yes | Yes (post-hook) |
| `technical-debt-log.yaml` | Deferred LOW issues | Yes | Yes (code-review) |

**For non-BMAD work**, manually load `session-context.md`, `sprint-status.yaml`, and
the execution plan (`10-execution-plan.md`) first.

## 🛠 Tech Stack (what actually exists in the code)

- **Backend**: FastAPI (Python 3.13) + SQLModel (ORM) + Alembic
- **Frontend**: React 19 + TypeScript + Vite + TanStack Router/Query
  (NO Redux — local state + TanStack Query is the pattern)
- **Database**: PostgreSQL
- **Infra**: Docker Compose everywhere — local dev via the compose override;
  staging/production = the same stack on one VPS behind Traefik (decided WS9;
  runbook: `cleardues/deployment.md`)

**Planned but NOT yet present** (do not assume these exist): WebSockets, Redis
Pub/Sub, Celery workers (all arrive with the nudge engine in WS12), PWA service
worker (WS11).

## 📐 Architectural Patterns

- **Directory Structure**: Feature-based (`/backend/app/features/{name}`,
  `/frontend/src/features/{name}`)
- **Naming**: API/DB `snake_case`; frontend `camelCase` (components `PascalCase`)
- **State**: TanStack Query for server state; React local state for UI state
- **Boundaries**: Service layer owns DB access
- **Models**: `backend/app/models.py` imports ALL feature model modules — prestart,
  alembic, and tests rely on it registering the complete schema. New feature model
  modules MUST be added to its imports.

## 🚀 Commands

```bash
# Start everything (from cleardues/)
docker compose up -d

# Backend tests — runs against a dedicated <db>_test database (auto-created);
# refuses to run unless ENVIRONMENT=local
docker compose exec backend pytest -q

# Frontend checks (from cleardues/frontend/)
npm run typecheck && npm run test && npm run build

# Dependency lock must stay in sync (CI enforces this)
docker compose exec backend uv lock --check

# Alembic migrations
docker compose exec backend alembic upgrade head
```

CI (`.github/workflows/ci.yml` at the **repo root** — GitHub ignores nested
`.github/` dirs) runs: backend pytest + lock check, frontend typecheck + unit tests
+ build, on pushes to `main` and all PRs.

## ✅ Definition of Done v2 (every story, no exceptions)

1. **CI green** — backend pytest, frontend typecheck + tests + build all pass. A
   story cannot be "ready for review" with a red or skipped gate.
2. **UI stories ship visual proof** — screenshots at 375px AND 1280px, both themes,
   attached to the story/completion notes. (Epic 2.5 shipped invisible text and
   offscreen navigation for 5 months because nobody looked.)
3. **User-reachable = done** — a feature is complete only when a real user can reach
   it from the app's entry point. Component-complete is NOT done (root failure of
   Epics 2.5–5).
4. **No epic closes past a live BLOCKER** — a BLOCKER note in sprint-status.yaml must
   be resolved, deferred-with-link, or dropped-with-reason before its epic is `done`.
5. **Known-bug tests stay honest** — use `it.fails`/`xfail`/`skip` with a reason
   pointing at the fix's work session, never a green assertion of broken behavior.

## Security Checklist for Story Acceptance Criteria

For each new story, add a "### Security Considerations" section after Acceptance
Criteria covering (mark [x] when implemented and tested):

1. **Input Validation** — validated on frontend AND backend; typed schemas (no raw
   `dict` bodies)
2. **Authorization** — group membership / ownership checks on every action
3. **SQL Injection** — parameterized queries only (SQLModel handles this; never
   concatenate SQL)
4. **XSS** — framework escaping; sanitize user content
5. **Rate Limiting** — document if the endpoint needs it
6. **Data Privacy** — expose only necessary fields; no sensitive data in logs
7. **Error Messages** — generic in production; no stack traces to the frontend

## Minimum Viable Story (MVS) Standard

A story is NOT "done" unless ALL of:

1. All acceptance criteria verified passing
2. All tasks checked off
3. Code review passed (no CRITICAL/HIGH blockers)
4. Tests passing **in CI** (deferral requires documented rationale)
5. Edge cases handled (null, boundary, error states)
6. Clear user-facing error messages
7. Loading states for async operations
8. Basic accessibility (keyboard nav, ARIA, focus management)
9. Type safety complete (no unjustified `any`)
10. Code hygiene (no commented-out code, no placeholder logs)
11. Documentation updated — **including human docs** (README/runbooks), not only
    BMAD artifacts
12. Core functionality included — not deferred to a "future story"
13. NO scope creep — nothing enters that isn't in the story/work session without
    removing something of equal size
14. Definition of Done v2 (above) satisfied

## Code Review Scoping

| Level | Definition | Blocks | Action |
|-------|------------|--------|--------|
| **CRITICAL** | Security holes, data loss, broken user flows | Story completion | Fix before merge |
| **HIGH** | Performance problems, anti-patterns, significant bugs | Next epic | Fix before next epic |
| **MEDIUM** | UX-affecting but non-blocking | No | Log to technical-debt-log.yaml |
| **LOW** | Polish, style | No | Optional suggestions |

Reviews focus on AC violations and CRITICAL/HIGH issues. Do not review style,
naming, or personal preferences unless they cause bugs or maintenance burden.

## Known Issues Quick Reference

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError in Docker | `docker compose build --no-cache` |
| Connection refused localhost:5432 | Use service name `db` not `localhost` |
| Circular import error | Import inside function or use TYPE_CHECKING |
| Route not found 404 | Check TanStack Router file naming conventions |
| Data not updating after mutation | Add `queryClient.invalidateQueries` |
| Mapper "failed to locate a name" | Add the feature models module to `app/models.py` imports |
| `PendingRollbackError` cascade in tests | Already handled by conftest's autouse rollback fixture |
| jsdom: focus-trap "no tabbable node" | Handled via `tabbableOptions.displayCheck` in test mode |

**Full solutions:** `_bmad-output/implementation-artifacts/solution-patterns.yaml`

## Logging Requirements

BMAD workflows auto-update tracking files via post-hooks (dev-story →
session-context/solution-patterns; code-review → technical-debt-log). For non-BMAD
work: new issue solved → `solution-patterns.yaml`; critical learning →
`session-context.md`; deferred LOW issue → `technical-debt-log.yaml`; work-session
progress → check off in `10-execution-plan.md`.

## References

### Plan of Record
- [Execution Plan (WS1–WS13)](./_bmad-output/product-review/10-execution-plan.md)
- [Review Findings 01–09](./_bmad-output/product-review/)

### Planning
- [PRD](./_bmad-output/planning-artifacts/prd.md)
- [Architecture](./_bmad-output/planning-artifacts/architecture.md) — ⚠️ real-time/
  Redux/PWA sections describe PLANNED, not current, state (rewrite lands in WS11)
- [Epics](./_bmad-output/planning-artifacts/epics.md)
- [UX Design Spec v2 — "Quiet Ink"](./_bmad-output/planning-artifacts/ux-design-spec-v2.md)
  — ADOPTED 2026-07-07 (WS2); supersedes
  [v1](./_bmad-output/planning-artifacts/ux-design-specification.md), whose visual
  system (warm-cream palette, orb, orbital nav) is void

### Tracking (auto-managed by BMAD)
- [Sprint Status](./_bmad-output/implementation-artifacts/sprint-status.yaml)
- [Solution Patterns](./_bmad-output/implementation-artifacts/solution-patterns.yaml)
- [Technical Debt](./_bmad-output/implementation-artifacts/technical-debt-log.yaml)
- [Session Context](./_bmad-output/session-context.md)

### Guides
- [BMAD Usage Guide](./_bmad/bmm/docs/BMAD-USAGE-GUIDE.md)
- [Tracking Setup Guide](./_bmad/bmm/docs/TRACKING-SETUP-GUIDE.md)
