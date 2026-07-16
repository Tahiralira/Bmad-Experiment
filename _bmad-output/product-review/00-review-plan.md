# ClearDues Comprehensive Review — Master Plan

**Purpose:** Full product, technical, security, infra, docs, and UX review, split into
independent sessions to avoid context bloat. Each session loads ONLY its listed inputs
plus this file, writes findings to its own numbered file, and checks itself off here.

**How to run a session:** Open a fresh conversation and say:
`Run Session N of the review plan in _bmad-output/product-review/00-review-plan.md`

---

## Session Checklist

- [x] **Session 1 — Product & Business Analysis** (Part 1)
      Inputs: prd.md, product-brief, epics.md (headings), backend/app/features/ai/
      Output: `01-product-business-review.md`
      Status: DONE 2026-07-06

- [x] **Session 2 — Vision, Strategy & Roadmap Redesign** (Part 2)
      Covers: personal expense tracking pillar, missing flows, onboarding, retention,
      revised epic roadmap, revised MVP scope.
      Inputs: epics.md (full), all epic retros, 01-product-business-review.md
      Output: `02-vision-strategy-roadmap.md`
      Status: DONE 2026-07-06

- [x] **Session 3 — Technical Review: Backend** (Part 3a)
      Covers: architecture, API design, DB models/migrations, service layer,
      error handling, logging, backend tests, the pytest-blocking SQLAlchemy bug.
      Inputs: architecture.md, backend/, technical-debt-log.yaml,
      solution-patterns.yaml
      Output: `03-technical-backend.md`
      Status: DONE 2026-07-06

- [x] **Session 4 — Technical Review: Frontend** (Part 3b)
      Covers: state management (Redux vs TanStack Query split), component structure,
      type safety, performance, frontend testing (currently none?), PWA/offline readiness.
      Inputs: frontend/src/, package.json, vite config
      Output: `04-technical-frontend.md`
      Status: DONE 2026-07-06

- [x] **Session 5 — Security Audit** (Part 4)
      Covers: auth flows (magic link, JWT, OAuth), authorization checks per endpoint,
      API-key encryption at rest, rate limiting (NFR5 — implemented?), CSRF/XSS,
      session management, dependency audit, secrets in docker-compose.
      Inputs: backend auth + core modules, docker-compose files, SECURITY.md
      Output: `05-security-audit.md`
      Status: DONE 2026-07-06

- [x] **Session 6 — Deployment & Infrastructure** (Part 5)
      Covers: Docker setup, Railway readiness, CI/CD (currently none?), monitoring,
      backups, environment management, scaling (NFR7: 1k WebSocket connections), cost.
      Inputs: docker-compose*.yml, Dockerfiles, deployment.md, hooks/, scripts/
      Output: `06-deployment-infra.md`
      Status: DONE 2026-07-06

- [x] **Session 7 — Documentation Review** (Part 6)
      Covers: README, CLAUDE.md (KNOWN STALE: status table says Epic 2.5 next; reality
      is Epic 5 at 2/3), BMAD artifacts consistency, missing API docs, onboarding docs.
      Inputs: CLAUDE.md, README.md, development.md, deployment.md, BMAD guides
      Output: `07-documentation-review.md`
      Status: DONE 2026-07-06

- [x] **Session 8 — UX/UI & Design Direction** (Part 7)
      Covers: full design-direction critique and revamp proposal (premium/minimal/
      timeless goals), information architecture, Orbital Navigation risk assessment,
      component/state design, accessibility, mobile experience.
      Inputs: ux-design-specification.md, ux-design-directions.html,
      ux-integration-plan.md, frontend components, live app screenshots if possible
      Output: `08-ux-design-direction.md`
      Status: DONE 2026-07-06 (included live app run + screenshots at 375px)

- [x] **Session 9 — Final Synthesis & Action Plan** (Part 8)
      Covers: scores (product, architecture, design, business, subscription viability),
      biggest problems/opportunities, features to add/remove, GTM strategy,
      impact-vs-effort prioritized action plan.
      Inputs: ALL findings files 01–08 (nothing else — no source code)
      Output: `09-final-recommendations.md`
      Status: DONE 2026-07-07 — ALL 9 SESSIONS COMPLETE. Headline outputs: overall
      project health 3/10; five meta-problems (fictional DoD, unbuilt differentiator,
      untrustworthy ledger, self-defeating BYOK model, template costume); ~40–45
      dev-days to private beta via Phases 0–3; market decision: GLOBAL (currency as a
      setting, payment-link registry, email as first-class nudge channel).
      Full details: 09-final-recommendations.md.
      Execution: see `10-execution-plan.md` — the consolidated work-session tracker
      that supersedes per-session follow-up.

---

## Ground Rules (apply to every session)

1. Be adversarial — find weaknesses, don't validate.
2. Severity-tag findings: CRITICAL / HIGH / MEDIUM / LOW (per CLAUDE.md review scoping).
3. Every recommendation must state impact AND effort.
4. Cross-reference, don't re-derive: read prior findings files instead of re-reading source.
5. Findings files are the single source of truth; chat summaries are secondary.

## Key Facts Established in Session 1 (do not re-verify)

- Progress: Epics 1–4 DONE, Epic 5 at 2/3 (session-context.md is current; CLAUDE.md table is stale).
- BYOK is implemented: `User.gemini_api_key_encrypted`, Fernet-style encrypt/decrypt in
  `app/core/security.py`; AI parse returns 400 without a key.
- No planning artifact mentions pricing, subscription, premium tiers, or BYOK.
- Known blocker: `GroupSettings | None` SQLAlchemy annotation breaks the entire pytest suite.
- Epic 6 (Agentic Notifications — the core differentiator) is not yet started.

## Key Facts Established in Session 2 (do not re-verify)

- Zero users / zero deployments: release is "bundled after Epic 5"; nothing has shipped.
- Velocity decay: Epics 1–2.5 (17 stories) ≈ 2 weeks; Epic 3 ≈ 4 weeks; Epic 4 ≈ 3.5
  months (retro dates 2026-02-17 → 2026-06-01); Epic 5 at 2/3 after ~5 weeks.
- Frontend tests: manual only (confirmed in Epic 4 retro). Backend: 125 tests, but the
  suite is currently broken by the SQLAlchemy annotation bug.
- CRITICAL product flaw: settlement is per-expense (claim + confirm each), no aggregate
  settle-up per relationship. Epic 6 nudges would fire per-expense → spam.
- No analytics/instrumentation story exists anywhere; PRD success metrics unmeasurable.
- "Rs" currency hardcoded in BalanceDisplay (Story 2.5.6); market decided GLOBAL
  (2026-07-07) — currency must become a per-group setting with a formatCurrency util.
- Invite flow has no public preview — invitees hit the login wall blind ("Walled Garden").
- Session 2 proposed a re-sequenced roadmap (Phases A–E) with private beta after
  Epic 6 core + launch-blocker epic; Quick Capture (personal expenses) approved as a
  post-beta pillar with strict non-goals (no bank sync, no budgets).

## Key Facts Established in Session 3 (do not re-verify)

- AI parsing (FR1) is broken end-to-end: membership check has swapped args
  (parser_router.py:67), no endpoint exists to save a Gemini API key, and group
  ai_personality has no write path. Session 1's "BYOK implemented" = read side only.
- Real-time layer does not exist: zero WebSocket/Celery code; `redis` not even a
  dependency — the one event publisher silently no-ops via swallowed ImportError.
- Test suite: 193 test functions, none can run (GroupSettings annotation at
  groups/models.py:102; fix is `Optional["GroupSettings"]`); 12 AI tests reference a
  nonexistent `db_session` fixture and never passed. conftest wipes the configured DB.
- Money-path integrity bugs: editing amount never recalcs splits; reject flow rewrites
  confirmed splits + converts any split type to equal + never re-checks finalization;
  settlement rejection never sets REJECTED. Dashboard balances are float, not Decimal.
- DELETE /users/me either 500s (audit FK) or cascade-deletes shared expenses.
- Fernet key derived from SECRET_KEY (which defaults to random-per-process) — restart
  or rotation permanently bricks stored encrypted API keys; "AES-256" NFR4 claim false
  (Fernet = AES-128).
- No GET-expense / list-group-expenses / view-splits endpoints — frontend cannot render
  a group ledger (root cause of RETRO-2.5-H2 navigation debt).
- Alembic autogenerate blind to all feature models (env.py imports only app.models);
  migration chain itself verified linear (debt 5.1-L1 closable).
- Backend health score: 4.5/10. Full details: 03-technical-backend.md.

## Key Facts Established in Session 4 (do not re-verify)

- No Redux anywhere (correct choice, but architecture.md/CLAUDE.md stack is wrong);
  TanStack Query usage is idiomatic; TypeScript strict with only 2 `any`s in app code.
- Expense creation is unreachable in the UI: the sole SmartInputModal mount
  (_layout.tsx) passes no groupId → submit silently no-ops; GroupDetail has no
  add-expense button. AI parsing is a hardcoded setTimeout mock ("Lunch with team",
  $60, payer "user-123"); zero SSE/EventSource client code exists.
- All 7 unit-test files (1,356 lines) import vitest/@testing-library — neither
  installed; `npm run typecheck` FAILS today (17 errors); `npm run build` passes
  because tsconfig.build.json excludes tests. All 4 Playwright specs are stale
  template password-auth tests. Effective automated frontend coverage: zero.
- Story 5.1 debtor UI (ConfirmedExpenseCard, PendingSettlementsList) is never
  mounted — settlement loop half-wired (owner confirm side is mounted in GroupDetail
  but shows claims from ALL groups, unscoped).
- Global handler logs users out on ANY 403 (business authz denials kill the session).
- FastAPI template still ships: parallel password auth (/signup, /recover-password,
  /reset-password, ChangePassword), /admin, /items, FastAPI logos/titles/favicon.
- No group URL (/groups/$groupId missing); detail is ephemeral useState snapshot.
- PWA readiness zero: no manifest, no service worker, no vite-plugin-pwa, no icons.
- Main bundle 1.48 MB min / 436 KB gzip single chunk (verified build).
- "Rs" hardcoded in 8+ files; equal-split rounding only balances if payer is last
  in members array; accepting an invite is a state-changing GET (Session 5 input).
- Frontend health score: 4/10. Full details: 04-technical-frontend.md.

## Key Facts Established in Session 5 (do not re-verify)

- Recorded at the end of `05-security-audit.md` (not duplicated here). Headlines:
  security posture 3.5/10; one SECRET_KEY does JWT + Fernet + session cookie duty and
  defaults to random-per-process; uv.lock omits authlib/cryptography/google-genai;
  OAuth delivers a 30-day JWT in a URL query param; public Adminer in prod compose;
  template password-auth stack still live and enumerable; magic-link auth itself is solid.

## Key Facts Established in Session 6 (do not re-verify)

- CI/CD is entirely dead: 13 workflows + dependabot sit in `cleardues/.github/`, but
  the git repo root is `Bmad-Experiment/` — GitHub never scans them. Triggers also
  target `master` (default branch is `main`) and self-hosted runners that don't exist.
  No automated gate has ever run on this codebase (root cause of the S3/S4/S5 rot).
- No backups of any kind: one Docker volume, no dumps/offsite/restore runbook;
  `docker compose down -v` appears in scripts and the (dead) CI workflow.
- Three contradictory deployment paths, none ever executed: Railway (planning docs
  only, zero artifacts, config.py can't consume DATABASE_URL), Traefik/VPS (template
  compose + deployment.md — 100% unedited, still `fastapi-project.example.com`), and
  Docker Swarm (`scripts/deploy.sh`).
- backend/Dockerfile:41's plain `uv sync` silently re-locks in-container, installing
  unpinned authlib/cryptography/google-genai every build (authlib is a top-level
  import at core/oauth.py:6). `redis`/`celery` are in neither uv.lock nor pyproject.
- No Redis/Celery/WebSocket services in any compose file — NFR7 (1k WebSockets) is
  unsupported and untestable; Epic 6 has no infra substrate and no scheduler exists.
- No monitoring or log rotation; only a Sentry DSN passthrough (EOL SDK). Backend
  healthcheck endpoint exists and is wired in compose.
- Backend image: root user, full python:3.10 (EOL Oct 2026), ships tests/; frontend:
  `npm install` not `npm ci`, floating nginx:1 tag; no resource limits; full `.env`
  (SMTP/OAuth/SECRET_KEY) injected into the Postgres container via env_file.
- A GitHub PAT sits in plaintext in the local git remote URL (rotate + credential helper).
- `.env` re-verified as gitignored and absent from all git history (S5 claim confirmed).
- Infra readiness score: 2.5/10; ~4 dev-days to a deployable, backed-up, monitored
  beta stack once S3/S4 code fixes land. Full details: 06-deployment-infra.md.

## Key Facts Established in Session 7 (do not re-verify)

- All human-facing docs (README, development.md, deployment.md, backend/frontend
  READMEs, SECURITY.md, release-notes.md) are unedited FastAPI-template files, last
  touched at Story 1.6. No repo-root README exists at all; no LICENSE decision for
  ClearDues itself; SECURITY.md routes vuln reports to security@tiangolo.com.
- CLAUDE.md (auto-loaded every session) is materially false: 5-months-stale status
  table, phantom stack (Redux/WebSockets/Redis/Celery — none exist), and both
  documented verification commands fail today. Root cause: it hand-duplicates status
  that sprint-status.yaml already owns.
- backend/README.md teaches the app/models.py monolith pattern — the documented root
  of the S3 Alembic autogenerate blindness.
- Every documented quality gate fails (pytest, typecheck, Playwright, "CI runs tests
  automatically"); nothing flags the gap.
- AI-facing docs are the repo's best (BMAD guides, session-context learnings, story
  files), but session-context.md self-contradicts (Epic 5 "1/3" vs "2/3"; "13
  remaining" vs actual 15; "Epic 6-7 0/18" vs actual 0/10) and sprint-status.yaml
  still lists "Setup Automated Testing Infrastructure — BLOCKER for Epic 4" as
  pending above `epic-4: done`.
- Generated OpenAPI client frozen at Epic 2 (no expense/settlement services); Epics
  3–5 hand-roll via `@/client/core/request`, a pattern documented nowhere. Swagger
  /docs is the only API reference and still advertises template endpoints.
- Docs pattern: only files a BMAD hook auto-touches stay current; MVS checklist item
  11 ("Documentation Updated") never enforced for human docs.
- Documentation health score: 4/10 (AI-facing ~7/10, human-facing ~1.5/10); ~1.5
  dev-days to fix. Full details: 07-documentation-review.md.

## Key Facts Established in Session 8 (do not re-verify)

- Verified live (built CSS + running app at 375px): Story 2.5.1's token migration never
  functioned — `text-secondary`/`text-muted` compile to shadcn *surface* colors
  (~1.0–1.15:1 contrast, invisible in BOTH themes), `text-primary` compiles to the teal
  action color (3.2:1, fails AA light), and the entire spec type scale + shadow tokens
  generate no CSS. 85 usages / 22 files — every ClearDues screen.
- Verified live: Orbital Nav is unusable on mobile — 2 of 5 destinations render fully
  offscreen (wrong arc: -135°→+45° from a bottom-right anchor), icons flex-squished to
  22×48px, menu auto-hides in 3s. Activity + Settings are untappable on a phone.
- Sole expense entry is an unhinted 500ms long-press on the unlabeled orb (which then
  no-ops per S4-C1); sole navigation is an unlabeled orb tap. No onboarding exists.
- First impression is the template: login footer "Full Stack FastAPI Template - 2026",
  FastAPI favicon/titles, template greeting on dashboard, raw "Network Error" strings
  rendered in teal. ThemeProvider default is `system` (S4's "dark default" note wrong).
- The UX spec itself self-contradicts: Hidden Nav (bottom-left pill) AND Orbital Nav are
  both fully specified, never reconciled; implementation added a 5th destination found in
  neither. F3-PBS "no boundaries" roast mode + 3s auto-confirm contradict the spec's own
  emotional-neutrality/trust principles.
- Session 8 recommendation: retire Orbital as sole nav (bottom tab bar + Orb as
  expense FAB), cap personality at Funny for MVP, manual confirm only. Token repair +
  nav replacement ≈ 2 dev-days, highest visible-quality ROI in the codebase.
- Scores: UX spec 7/10, implemented UX 2/10, combined design health 3/10. Process root
  cause: no story was ever visually verified — recommend screenshot-in-DoD workflow
  change. Full details: 08-ux-design-direction.md.
- POST-REVIEW (same day, user-approved): Orbital Nav deleted and replaced with a
  labeled bottom tab bar (`bottom-nav.tsx`); Agent Orb kept as FAB, single tap now
  opens Smart Input. During verification a NEW critical was found+fixed: SmartInputModal
  crashed on every open (FocusTrap given a nonexistent render-prop API →
  React.Children.only throw, swallowed by route error boundary) — the modal had NEVER
  opened; supersedes S4-C1's "opens but no-ops" framing. S4-C1 (no groupId) and S4-C2
  (mock AI) still open. See Post-Review Update in 08-ux-design-direction.md.
- POST-REVIEW 2: UX-C1 + UX-M1 RESOLVED — design tokens repaired in index.css @theme
  (text hierarchy via `text-text-*` utilities, full type scale, spec shadows); mixed
  usages renamed; dead `ui/smart-input-modal.tsx` deleted (closes S4-M9). Verified
  live in both themes (AA contrast restored). Details in 08's Post-Review Update.
