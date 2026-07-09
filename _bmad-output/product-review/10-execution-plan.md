# ClearDues Execution Plan — Master Work Tracker

**Created:** 2026-07-07
**Purpose:** The single plan of record for acting on the 9-session review. It
consolidates all findings (01–08) through the Session 9 synthesis (09) into
dependency-ordered **work sessions**, each sized to fit one focused conversation.
This file supersedes any per-session follow-up: never work "from Session N's file"
directly — work from here, and use the session files only as the referenced inputs.

**Why consolidated (not session-by-session):** the review sessions are diagnoses, not
work packages. The same fix appears in 3–4 session files (CI in S3/S4/S6/S7; template
purge in S4/S5/S7/S8; currency in S2/S4/S8), and dependencies cross sessions (frontend
screens need backend endpoints; CI needs the test fixes first). Executing per-session
would duplicate work and break ordering. Session 9 already merged everything —
this file breaks that merge into runnable units.

**How to run a work session:** open a fresh conversation and say:
`Run Work Session N of the execution plan in _bmad-output/product-review/10-execution-plan.md`

---

## Ground Rules (every work session)

1. **Load only what's listed.** Each session names its input files/sections. Do not
   re-read the whole review; the inputs contain everything needed.
2. **Leave the gates green.** From WS1 onward: backend pytest, `npm run typecheck`,
   and `npm run build` must pass at the end of every session. A session that breaks a
   gate is not done.
3. **User-complete, not component-complete.** A task is done only when the feature is
   reachable by a real user from the app's entry point. (The #1 failure mode of
   Epics 2.5–5 — S9 MP1.)
4. **UI work ships with proof:** screenshot at 375px and 1280px, both themes, attached
   or described in the session's completion notes.
5. **Check off here when done.** Mark tasks `[x]`, set the session Status line, and note
   any deviations/deferrals inline. This file is the source of truth for progress.
6. **Update BMAD tracking as usual** (sprint-status.yaml, session-context.md) when
   stories/epics are touched, but this tracker drives the sequence. For larger units
   (WS12/WS13 nudge engine), optionally spin formal BMAD stories via `create-story`.
7. **No scope creep:** nothing enters a session that isn't in its task list without
   removing something of equal size. The milestone is the private beta; resist
   anything that delays it (S2 §8, S9 §7).
8. **Market is GLOBAL (decided 2026-07-07):** no hardcoded currency, no
   market-specific rails; currency is a per-group setting, payment links are a
   configurable registry, email is a first-class notification channel.

---

## Work Session Checklist

### PHASE 0 — Foundation (do first; nothing else starts until WS1 is done)

- [x] **WS1 — Gates & Truth** (≈2 days)
      Goal: make "done" mean something — runnable tests, green typecheck, working CI,
      truthful CLAUDE.md.
      Inputs: 03 §3 (C3), 04 §3 (C3), 06 (C1, H1 CI notes), 07 (C1, H3).
      Tasks:
      - [x] Fix `GroupSettings | None` → `Optional["GroupSettings"]`
            (backend `groups/models.py:102`); audited other models — no other
            quoted-union annotations
      - [x] Renamed the phantom `db_session` fixture usages → `db`; triaged the
            first honest run of both suites (see notes)
      - [x] Test DB safety: dedicated `<db>_test` database (auto-created), schema
            built from the REAL alembic migrations (not create_all — models declare
            naive datetimes while migrations are timezone-aware), fail-fast guard on
            `ENVIRONMENT != local`, autouse rollback fixture (kills the
            PendingRollbackError cascade: one failure used to error 73 later tests)
      - [x] Frontend: vitest + jsdom + RTL + jest-dom installed, vitest config +
            `test` script added, all 17 typecheck errors fixed → typecheck green
      - [x] Root-level `.github/workflows/ci.yml`: backend pytest + `uv lock
            --check` + `uv sync --locked`, frontend typecheck + unit tests + build;
            13 dead workflows + dead dependabot.yml deleted
      - [x] CLAUDE.md rewritten: status delegated to live files, real stack,
            working commands, Known Issues deduped, execution-plan pointer added
      - [x] DoD v2 written into CLAUDE.md (CI green, visual proof, user-reachable,
            no-live-BLOCKER, honest known-bug tests) + MVS updated
      Verification: DONE 2026-07-07 —
      **backend 192 passed / 2 skipped (0 failed)** — first green run ever;
      **frontend 80 passed / 1 expected-fail / 2 skipped**, typecheck + build green;
      `uv lock --check` passes.
      Notes / deviations (all documented in code comments):
      - PULLED FORWARD from WS8: `uv lock` regenerated — authlib 1.7.2 (clears
        CVE-2024-37568), cryptography 49, google-genai 2.10 now locked; the
        committed lock finally matches shipped images. Version BUMPS
        (starlette≥0.40, sentry 2.x, Dockerfile `--locked`) remain WS8.
      - REAL BUGS FOUND+FIXED by the resurrected tests: (1) `useStreamingText`
        skipped the first character and appended "undefined" (stale ref read in
        React state updater); (2) `app/models.py` shim registered only auth models
        — prestart crashed on fresh `docker compose up` (User→ExpenseSplit mapper);
        now imports all feature models, which also un-blinds Alembic autogenerate
        (reconcile diff still WS5); (3) SmartInputModal tests needed a
        QueryClientProvider + focus-trap jsdom displayCheck workaround.
      - Never-could-run test debris repaired: test_settlement.py had a destroyed
        `def` line (SyntaxError since creation) + phantom invite routes
        (`/invite` vs `/invites`, POST-accept vs GET) + wrong response shape;
        split tests asserted single-member splits and auto-redistribution that
        were never implemented; 2 pending-list tests made order-dependent
        assertions (now baseline-relative).
      - Marked honestly instead of fixed here: frontend S4-M1 rounding bug =
        `it.fails` (WS5); 2 mock-AI modal tests = skip (WS7); 2 backend AI router
        tests = skip (B-C1 swapped args, WS7).
      - CI runs on the next push/PR — its first live run is the real test of 0.3.
      Status: DONE 2026-07-07 (changes uncommitted — commit when ready)

### PHASE D — Design Revamp (user-led; run WS2 next per user preference; WS3 after WS1)

- [x] **WS2 — Design Direction v2 (planning session, no code)** (≈1 day, interactive)
      Goal: replace the current design direction with something **minimal, lighter,
      faster** per user preference. The current design is explicitly not liked —
      S8's "keep" list (palette, orb, warm-minimal) is *input, not constraint*; the
      user's new direction overrides it.
      Inputs: 08 §6/§8 (what exists and what was judged good/bad), current
      `index.css` tokens, live screenshots; user participates in this session.
      Suggested vehicle: `/bmad:bmm:workflows:create-ux-design` or a direct design
      conversation producing the artifact.
      Tasks:
      - [x] Explore 2–3 lightweight direction candidates (visual language, type,
            color, density, motion budget) — with rendered previews/mockups
            (3 candidates rendered as phone-frame mockups, both themes:
            https://claude.ai/code/artifact/2013e5de-4d4b-46e9-922e-5274a025907e)
      - [x] User picks direction; document decisions (what replaces the orb/palette/
            voice, or confirms them) — **Direction A "Quiet Ink" chosen**: paper/ink
            minimalism, system fonts (0 KB download), hairline ledger rows, orb
            RETIRED (plain + FAB), ink-teal accent kept, mediator voice confirmed
      - [x] Produce `ux-design-spec-v2.md`: token set (colors, type scale, spacing,
            radii, shadows), component restyle inventory, performance budget
            (bundle/font/motion — "lighter and faster" made measurable)
            → `_bmad-output/planning-artifacts/ux-design-spec-v2.md`
      - [x] Reconcile with the spec's still-valid principles worth keeping regardless
            of aesthetics: emotional neutrality, no-red-debt (or a deliberate
            replacement), 44px touch targets, WCAG AA → spec §2 "Product
            Constitution" (8 rules incl. manual-confirm-only, no timed UI)
      Non-goals: no implementation in this session.
      Notes: perf budget set as CI-verifiable gates (0 KB fonts, main chunk
      ≤250 KB gz vs current ~1.48 MB, framer-motion deleted, LCP <1.2s). Template
      components (Items/Admin/ChangePassword) explicitly excluded from WS3 restyle —
      they die in WS8. Live screenshots taken at 375px (login dark, dashboard light)
      via Vite dev server with auth-gate bypass; backend not needed.
      Status: DONE 2026-07-07 (spec adopted; WS3 is the implementation session)

- [x] **WS3 — Design System Implementation & Brand Floor** (≈3–4 days; likely less —
      see kit note below)
      Goal: implement the v2 tokens, restyle existing screens, and make the app look
      like ClearDues instead of the FastAPI template.
      Depends on: WS1 (gates), WS2 (spec).
      Inputs: **`_bmad-output/planning-artifacts/ws3-implementation-kit.md` — START
      HERE and follow it verbatim.** The kit (produced 2026-07-07 from a live code
      audit) contains every decision pre-made: complete paste-ready files (index.css,
      index.html, favicon.svg, Logo, AuthLayout, _layout, Dashboard, BalanceDisplay,
      Fab, __root, vite.config), mechanical find/replace tables, the framer-motion
      purge recipe per file, the copy deck, and the verification checklist. Use
      `ux-design-spec-v2.md` only for rationale; 08/04 only if something is ambiguous
      — the kit overrides both where they differ.
      Tasks:
      - [x] Implement v2 tokens in `index.css` `@theme` (correctly namespaced —
            the UX-C1 collision class must not recur); migrate the `text-text-*`
            usages to the v2 names
      - [x] Restyle Dashboard, Groups, Login/Register, SmartInputModal, bottom nav,
            activity feed to the v2 system; eliminate the shadcn-vs-spec split
            (UX-M4) so one design language remains
      - [x] Brand floor: app name, logomark/favicon, page titles, login footer,
            dashboard greeting; delete FastAPI SVGs/branding
      - [x] Self-host the chosen font — SUPERSEDED by kit: v2 spec chose the
            SYSTEM font stack (0 KB download), so nothing to self-host; the
            render-blocking Google Fonts import is deleted (UX-M2 closed)
      - [x] Performance pass per WS2 budget: vendor chunking / lazy-load heavy libs
            (S4-M5, 1.48 MB main chunk), remove template deps that go with deleted UI
      - [x] Hide dead swipe gestures until wired (UX-M6) — SwipeableCard deleted;
            SmartInputModal drag-to-dismiss + handle removed
      Verification: DONE 2026-07-09 —
      **Gates:** backend 192 passed/2 skipped; frontend typecheck green,
      **83 passed / 1 expected-fail (S4-M1) / 2 skipped (WS7)** incl. new axe
      smoke tests; build green.
      **Bundle (gzip):** main chunk **170.6 kB** (was 435.6 kB; budget ≤250 kB ✓);
      vendor-tanstack 49.2 + vendor-forms 27.1 + vendor-react 4.2; CSS 14.3;
      total-first-paint ≈265 kB gz vs ~450 kB before. Fonts **0 KB** / 0
      third-party requests (`fonts.googleapis` absent from dist ✓); no
      framer-motion / react-icons / devtools in any chunk ✓.
      **Screenshots:** 16 shots (login, dashboard-data, dashboard-empty,
      smart-input × 375px/1280px × light/dark) →
      `_bmad-output/implementation-artifacts/ws3-screenshots/`.
      **Manual pass (Playwright-automated, 12/12):** all 5 bottom-nav
      destinations land; FAB opens Smart Input, Escape closes, focus returns to
      FAB; keyboard-only Tab→Enter opens modal; /items and /admin still render.
      Notes / deviations:
      - Kit gap: ConfirmedExpenseCard was an unlisted SwipeableCard consumer —
        unwrapped; its Mark Paid button (was desktop-hover-only) is now always
        visible since swipe was the only mobile path (gesture returns WS6).
      - BONUS BUG FIXED: SplitPicker's `import * as Icons from "lucide-react"`
        bundled the ENTIRE lucide set (≈580 kB min) — and its kebab-case lookups
        never matched lucide's PascalCase exports, so split icons never rendered.
        Explicit icon map fixed both (this was most of the bundle win).
      - vitest-axe matcher doesn't register under vitest 4 → used the kit's
        sanctioned fallback (assert on `.violations` directly).
      - Devtools pinned to app's router version (1.142.11) — latest devtools
        peer-requires router-core ≥1.170.
      - Amber hardcodes on Pending badges (outside kit scope) → logged WS3-L1
        in technical-debt-log.yaml.
      Status: DONE 2026-07-09 (branch ws3/quiet-ink, 8 commits)

### PHASE 1 — Ledger Integrity & Core Loop (backend-heavy; WS4 can start in parallel with WS2)

- [ ] **WS4 — Ledger Integrity (backend)** (≈1 week)
      Goal: the ledger becomes trustworthy — the whole game for this product.
      Depends on: WS1.
      Inputs: 03 §3–§5 (C4, H2, H3, H4, H5, M1, M8, M9, M10).
      Tasks:
      - [ ] Product decision implemented: "any change to amount/participants reverts
            the expense to DRAFT and re-opens consent" — fixes expense-edit orphaning
            (H2) and replaces reject-redistribution with reject→DRAFT + notify (H3)
      - [ ] Settlement rejection sets REJECTED status + `rejected_at` truthfully (H4)
      - [ ] One-transaction-per-request refactor; audit entries atomic with their
            operations (H5); add the canonical pattern to solution-patterns.yaml
      - [ ] Soft-delete/anonymize users; FK policy migration; block hard delete with
            unsettled shared splits (C4)
      - [ ] Row locking / idempotency on settle+confirm paths (M8); Decimal to the
            wire on dashboard balances (M1); 404 guard in `read_user_by_id` (M9)
      - [ ] Kill one of the twin membership helpers; keyword-only args (M10)
      - [ ] Tests for every fix (the suite runs now — use it)
      Verification: suite green in CI including new integrity tests.
      Status: pending

- [ ] **WS5 — Ledger API + Group Screen** (≈1 week)
      Goal: the app can display what it stores; the core loop becomes operable.
      Depends on: WS4 (service-layer semantics settled). Styling: use existing
      components; WS3 restyles globally via tokens.
      Inputs: 03 (H7, H6, H9, M2, M6), 04 (C1, C4, H1, H3, M6, M1, M2).
      Tasks:
      - [ ] Backend read endpoints: GET expense, list group expenses, expense splits,
            group detail; group-scoped settlement-claims variant (B-H7, S4-M6)
      - [ ] Split endpoint: discriminated-union Pydantic schemas replace the raw
            `dict` + 220 lines of hand-rolled validation (B-H6)
      - [ ] Alembic env.py imports all feature models; autogenerate diff reconciled
            (B-H9)
      - [ ] `/groups/$groupId` route; detail derived from query cache (S4-H3);
            dashboard last-activity fixed (B-M2)
      - [ ] Group ledger screen: expense list + balances; mount ConfirmedExpenseCard /
            PendingSettlementsList / AuditLogList (S4-C4)
      - [ ] Wire expense entry: per-group entry point + group selector in
            SmartInputModal; thread groupId (S4-C1)
      - [ ] Global handler: logout on 401 only; 403 → toast via router (S4-H1)
      - [ ] Frontend split-math fixes (S4-M1 payer-position rounding, M2 stale
            excluded amounts)
      Verification: a user can create → split → confirm → view an expense end-to-end
      in the browser; screenshots attached.
      Status: pending

- [ ] **WS6 — Aggregate Settle-Up + Confirmation Policy** (≈4–5 days)
      Goal: settlement matches human behavior; the friction ceremonies become opt-in.
      Depends on: WS5.
      Inputs: 02 §4, 09 §5 (strict mode, auto-confirm), 03 (settlement schema notes).
      Tasks:
      - [ ] Aggregate settle-up: "Settle with X" nets all confirmed expenses between
            the pair in a group → one claim → one confirmation → covered splits
            settled atomically, one audit fan-out; per-expense path kept for partial
            payments
      - [ ] Settlement auto-confirm after 72h with owner dispute window
      - [ ] Per-group "strict mode" toggle: expense confirmation becomes opt-in;
            default OFF with auto-confirm after N days (existing workflow = strict
            mode implementation)
      - [ ] Pairwise balance detail view ("who owes whom exactly" — S2-F9, the UI
            prerequisite for settle-up)
      Verification: 12-expense scenario settles in one claim + one confirm; tests
      cover netting math.
      Status: pending

- [ ] **WS7 — Real AI Path (hosted-first)** (≈1 week)
      Goal: FR1 exists for the first time; the premium gate exists.
      Depends on: WS5 (expense create path works).
      Inputs: 03 (C1, C2, C5, H8), 04 (C2), 01 §6 (hosted-AI model), 05 (C1 key notes).
      Tasks:
      - [ ] Fix the swapped-args membership check (B-C1) + a real SSE-payload test
      - [ ] Hosted AI default: server-side key, resolution order
            `user_key if set else server_key`; per-user monthly quota counter
            (~20 free parses)
      - [ ] BYOK demoted: `PUT/DELETE /users/me/api-key` as a hidden advanced
            setting; never in onboarding
      - [ ] Dedicated `ENCRYPTION_KEY` (fail-fast outside local) + proper derivation;
            fix the false "AES-256" claim; migration plan for existing keys (B-C5)
      - [ ] Async Gemini client + timeout; chunk commentary by word/sentence; honest
            SSE error contract (B-H8)
      - [ ] Frontend: real SSE/EventSource consumption, auth-context user ID, delete
            the setTimeout mock and `"user-123"` (S4-C2); error/low-confidence states
      - [ ] Manual confirm only (no 3s auto-confirm — UX-H6)
      - [ ] Group `ai_personality` write path (owner-only PATCH) capped at Funny, or
            explicitly defer with the default documented (B-C2, UX-H5)
      Verification: type a real sentence → parsed by a real model → confirmed →
      correct expense in the ledger. Demo recording/screenshots.
      Status: pending

### PHASE 2 — Launch Blockers

- [ ] **WS8 — Template Purge & Security Hardening** (≈1 week)
      Goal: attack surface halved; secrets and deps stop being landmines.
      Depends on: WS1; ideally after WS3 (so deletions don't collide with restyling).
      Inputs: 05 (all C/H/M items), 04 (H2, M8), 06 (H1).
      Tasks:
      - [ ] Delete the parallel password-auth stack: /signup, /login/access-token,
            /password-recovery, /reset-password, /private, ChangePassword UI, /admin,
            /items + backend routers/models + `Item` table migration (S5-H5, S4-H2)
      - [ ] OAuth token delivery: one-time code exchange or HttpOnly cookie — never
            a URL query param; shorten lifetime; revocation/jti list (S5-H1)
      - [ ] Rate limiting: per-IP on auth endpoints + AI parse; global default
            (S5-H2)
      - [ ] Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
            on API + nginx; `allow_credentials=False` (S5-M1, M6)
      - [ ] Google OIDC: require `email_verified` before account linking (S5-M3)
      - [ ] Invite accept → POST from a landing page; add revocation + usage caps
            (S5-M4; pairs with WS10's preview page)
      - [ ] `uv lock` regenerate; `--locked` in both Dockerfile syncs; pin
            authlib≥1.3.1, bump starlette≥0.40, sentry-sdk 2.x with PII scrubbing
            (S5-C2/H4/M7, S6-H1)
      - [ ] OAuth error redirect: generic code only, no `str(e)` (S5-M2)
      - [ ] Mediator-voice error mapper: no raw "Network Error", stop swallowing
            server `detail` (UX-H4, S4-M4)
      Verification: suite green; manual pass over auth flows; template routes 404.
      Status: pending

- [ ] **WS9 — Deploy & Ops (first deployment ever)** (≈1 week)
      Goal: a deployable, backed-up, monitored stack.
      Depends on: WS1 (CI), WS8 (image/deps hardening overlaps).
      Inputs: 06 (entire Recommended Path), 05 (H3).
      Tasks:
      - [ ] Commit to compose-on-VPS for beta; delete the Swarm script and the
            Railway claims from planning docs (S6-C3)
      - [ ] Extract `cleardues/` to its own repository; rotate the PAT; credential
            helper (S6-M4, M3)
      - [ ] Nightly `pg_dump` → object storage + one **tested** restore; pre-migration
            dump in prestart (S6-C2, M5)
      - [ ] Image hardening: python:3.13-slim, non-root USER, drop tests COPY,
            `npm ci`, pinned nginx, resource limits, gzip + cache headers (S6-H4)
      - [ ] Remove Adminer from prod compose; scope env_file per service (S5-H3,
            S6-M1)
      - [ ] Uptime monitor on health-check; log rotation on all services + Traefik
            (S6-H3)
      - [ ] Deploy staging; write the 1–2 page ClearDues runbook (provision, secrets
            checklist incl. encryption-key warning, deploy, rollback, restore)
            (S6-M2)
      Verification: app reachable on a real domain over TLS; restore drill executed
      once; uptime alert fires on a test outage.
      Status: pending

- [ ] **WS10 — Growth Wiring & Analytics** (≈1 week)
      Goal: the beta can convert, retain, and be measured — globally.
      Depends on: WS5, WS6; WS9 for PostHog hosting.
      Inputs: 02 (F1, F7, §6, §9), 09 §6 (global-market requirements, monetization).
      Tasks:
      - [ ] Invite public preview page: "X invited you to 'Trip' — N members" →
            one-tap OAuth → land inside the group (S2-F1)
      - [ ] Currency: `formatCurrency` util + per-group currency setting
            (locale-detected default, ISO-4217); purge all "Rs" hardcodes (8+ files,
            backend error strings included)
      - [ ] Payment deep links registry: user-configurable (Venmo, PayPal.Me, Cash
            App, Revolut, UPI, IBAN copy, …) + universal "mark as paid" at settle time
      - [ ] Push permission flow: ask after first confirmed expense, email fallback
            path wired (email is first-class, not fallback-only)
      - [ ] Analytics: self-hosted PostHog + event taxonomy (`domain.entity.action`)
            + activation funnel (group ≥2 members + ≥1 confirmed expense within 48h)
            + PRD metrics (settlement velocity, edit rate, mute rate)
      - [ ] Write the monetization spec: tier matrix, quota numbers, paywall
            placements, USD-first pricing, 2–4% conversion target
      - [ ] Onboarding first-60-seconds: sandbox "try one expense" parse on the
            organic path; group templates (Roommates/Trip/Dinner) presetting the
            social contract; empty states name the next action (S2 §6)
      Verification: cold invite→join→activation funnel visible in PostHog end-to-end.
      Status: pending

- [ ] **WS11 — Docs Floor + Test Journeys + PWA Shell** (≈3 days)
      Goal: the repo survives its first external reader; real flows have automated
      coverage; the app is installable.
      Depends on: WS8 (template deletion settles what docs describe).
      Inputs: 07 (top-10 table), 04 (H5, H4).
      Tasks:
      - [ ] Repo-root README (what/status/stack/quickstart/layout) + LICENSE decision;
            strip cleardues/README to dev setup; delete template badges/screenshots/
            release-notes/img/ (S7-H1, M6)
      - [ ] backend/README rewrite: feature-based architecture, real migration
            workflow (S7-H2); SECURITY.md contact fixed (S7-M1)
      - [ ] Reconcile session-context/sprint-status numbers; annotate the bypassed
            BLOCKER items (S7-M2, M4)
      - [ ] Decide + document the one API-client pattern (regenerate OpenAPI client
            vs bless hand-rolled) and migrate one feature as the exemplar (S7-M3)
      - [ ] Delete 4 template Playwright specs; write 3–4 ClearDues smoke journeys
            (magic link via mailcatcher, group create+invite, expense confirm,
            settle-up) wired into CI (S4-H5)
      - [ ] PWA install shell: manifest, icons (v2 brand), service worker via
            vite-plugin-pwa, theme-color meta — install-shell only, offline data
            explicitly out (S4-H4)
      Verification: e2e smokes green in CI; Lighthouse PWA installability passes.
      Status: pending

### PHASE 3 — The Differentiator → BETA

- [ ] **WS12 — Nudge Engine: Infra + Level 1** (≈1 week)
      Goal: the product's reason to exist gets a substrate and its first level.
      Depends on: WS6 (aggregate settle-up — nudges must be per-relationship),
      WS9 (somewhere to run), WS10 (telemetry).
      Inputs: 09 Phase 3, 02 Phase B, 03 (H1 — delete dead publisher first), 06 (H2).
      Tasks:
      - [ ] Delete `publish_expense_confirmed_event` + `notify_group_of_finalized_
            expense` dead code; add redis + celery worker + beat to compose; declare
            deps; adopt the event envelope for real
      - [ ] Level 1 nudges: gentle reminders, **per-relationship per-group, never
            per-expense** (written into ACs); channels: web push + email
      - [ ] Snooze + quiet hours
      - [ ] Notification permission UX from WS10 wired to real notifications
      Verification: a scheduled nudge fires end-to-end (beat → worker → push/email)
      on staging.
      Status: pending

- [ ] **WS13 — Nudge Engine: Level 2 + Beta Launch** (≈1 week)
      Goal: progressive urgency ships; beta goes live.
      Depends on: WS12; all Phase 2 sessions done.
      Tasks:
      - [ ] Level 2 escalation (frequency/tone progression per the social contract);
            Level 3 remains cut
      - [ ] "Cleared without asking" success notification (the brand promise made
            visible)
      - [ ] Mute/block-rate telemetry wired to the PRD kill-switch dashboard
      - [ ] WS load/scheduler sanity check on staging (NFR honesty — declare real
            numbers, not aspirations)
      - [ ] Beta checklist: seed 5–10 real groups, weekly metric review cadence
            (activation, settlement velocity, mute rate), feedback channel
      - [ ] **→ LAUNCH PRIVATE BETA**
      Status: pending

### PHASE 4 — Post-Beta (sequence by beta data; do not pre-build)

Parked, in likely order: Quick Capture epic (S2 §3 scope contract) → Roommate Pack
(recurring expenses, debt simplification, monthly digest) → monetization build-out
(quota paywall, Pro tier, Trip Pass, Group Pro) → Agent's Monthly Report → trip
closing ceremony → receipt OCR. Pull group end-of-life / member-exit flows
(S2-F4/F5) forward the moment a beta group hits them — they will, in week one.

---

## Dependency Map (summary)

```
WS1 (gates) ─┬─► WS4 (ledger integrity) ─► WS5 (ledger API+UI) ─► WS6 (settle-up) ─┐
             │                                        └─► WS7 (real AI)            │
             ├─► WS2 (design v2 spec) ─► WS3 (design implementation) ─┐            │
             ├─► WS8 (purge+security) ─► WS9 (deploy+ops) ────────────┼────────────┤
             │                                └─► WS10 (growth+analytics) ─────────┤
             │                                └─► WS11 (docs+e2e+PWA)              │
             └──────────────────────────────────────► WS12 (nudges L1) ─► WS13 ─► BETA
```

Parallelism notes: WS2 (design planning) can run immediately — it's a conversation,
not code. WS4 (backend) and WS3 (design implementation) don't collide. WS8 should
land after WS3 so deletions and restyling don't fight over the same files.

## Budget

~45–50 dev-days of focused work across WS1–WS13 (the design revamp adds ~4–5 days
over the original Session 9 estimate). The velocity bet is WS1: if stories/week
doesn't visibly recover after WS1+WS4, stop and diagnose before proceeding (S9 §8).
If cuts are ever needed: cut Phase 2 scope (PWA shell, parts of WS10/WS11) before
Phase 3 — shipping nudges to 10 real groups is the only result that validates or
kills the product.
