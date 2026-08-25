# Session Context - ClearDues Project

**Last Updated:** 2026-08-25 (WS11 done — Docs Floor + Test Journeys + PWA Shell:
README/LICENSE/SECURITY floor, template exhaust deleted, 12 Playwright journeys in
CI, generated-OpenAPI-client decision with groups as the exemplar, installable PWA
shell with the SW deliberately kept off API responses)

> **REPO LAYOUT (WS9.6, 2026-07-16):** the `cleardues/` wrapper folder is GONE —
> `backend/`, `frontend/`, compose files, and deployment docs live at the repo
> root. Any `cleardues/<path>` reference in documents written before this date
> means `<path>` today. Three files had NEVER been in git because the old root
> .gitignore's broad patterns (`package.json`, `lib/`, `build/`) swallowed them:
> `frontend/package.json`, `frontend/src/lib/utils.ts`,
> `backend/app/email-templates/build/*.html` — rescued in WS9.6; a fresh clone
> before that could not build. Docker compose project name is now pinned
> (`name: cleardues`) so local volumes survived the move.
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
| Epic 6-7 | BACKLOG | 0/10 |
| Epic 8: UX Polish | BACKLOG (Post-MVP) | 1/4 |

**Current Progress:** 33 of 47 stories done, 14 remaining.

> These counts are **derived from** `implementation-artifacts/sprint-status.yaml`
> — that file is the source of truth, this table is a convenience copy.
> Reconciled 2026-08-25 (WS11, S7-M2): the old row said "32 completed, 13
> remaining", "Epic 6-7 0/18" (they hold 10 stories, not 18 — the 18 was
> copied from CLAUDE.md's "Epic 4-7" row), and "Epic 8 0/4" (8-1
> ai-personality-selector shipped early in WS7). If you touch a story status,
> change sprint-status.yaml first and re-derive these.

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
> WS6 (Aggregate Settle-Up + Confirmation Policy) DONE 2026-07-13 on branch
> `ws6/settle-up`: **settlement now matches human behavior** — the
> 12-expense scenario settles in ONE claim + ONE confirmation (proven in the
> browser: Rs 600 across 12 expenses → one settle-up → one confirm → all
> settled, balances 0, 12-entry audit fan-out). (a) Aggregate claims:
> SettlementClaim.expense_split_id nullable + group_id/counterparty_user_id;
> settlement_claim_split link table whose UNIQUE(expense_split_id) is the
> concurrency guard (racing claims → 409); netting covers both directions,
> net 0.00 clears an even pair, wrong direction 400; per-expense path kept
> for partial payments (overlap 409s both ways). (b) 72h auto-confirm with
> owner dispute window — LAZY SWEEPS on claim-surfacing reads (no Celery
> until WS12), commit-only-if-swept; reject after the window confirms
> instead + 409; auto_confirm_at on the wire. (c) strict_mode on
> GroupSettings (default OFF): expenses auto-confirm 3 days after splits
> assigned unless someone objects; strict = the original Epic 4 ceremony;
> owner-only PATCH /expense-groups/{id}/settings. (d) Pairwise balances
> (S2-F9): GET .../pairwise-balances + "Between you and…" section, two-step
> inline Settle up, AggregateClaimCard both roles. Backend **232 passed / 2
> skipped**; frontend **98 passed / 2 skipped**, main chunk 172.9 kB gz.
> Key learnings: (1) an EXISTS subquery whose table is already in the outer
> FROM auto-correlates itself away (InvalidRequestError: "no FROM clauses")
> — alias the inner table (`sa.orm.aliased`); (2) shared confirm/reject
> endpoints branching on a nullable discriminator column beat parallel
> aggregate endpoints — the frontend reuses the same mutations; (3) UI must
> not offer actions the backend will always 409 (Mark Paid hidden while a
> settle-up covers the expense).
> WS7 (Real AI Path, hosted-first) DONE 2026-07-14 on branch `ws7/real-ai`:
> **FR1 exists for the first time** — the review had found every layer of
> the AI slice was fiction (B-C1 broken endpoint, S4-C2 setTimeout mock,
> B-C2 no key write path). Proven in the browser: type "Paid 450 for
> biryani lunch with the team" → SSE commentary streams → editable preview
> → manual Confirm → Rs 450.00 in the ledger. (a) Hosted-first: server
> `GEMINI_API_KEY`, resolution `user_key if set else server_key`, `ai_usage`
> per-user monthly quota (20 free, FOR UPDATE + unique-race fallback, 429),
> BYOK demoted to PUT/DELETE /users/me/api-key (encrypted, quota-exempt,
> no onboarding UI). (b) B-C5/S5-C1: dedicated `ENCRYPTION_KEY` (fail-fast
> outside local) + HKDF-SHA256 domain-separated derivation; false AES-256
> claims corrected; no key migration needed (nothing ever stored). (c)
> B-H8: async `client.aio` + 30s timeout, JSON response_mime_type,
> word-level commentary chunks, honest contract — pre-stream = real
> 403/422/429/503, mid-stream = error events on 200. (d) Frontend: real
> fetch-stream SSE client + AbortController, mock deleted, error/
> low-confidence mediator states; auto-confirm machinery deleted (UX-H6
> — manual confirm only). (e) ai_personality write path via WS6's settings
> PATCH, capped professional/friendly/funny (f3-pbs REMOVED, UX-H5);
> "Mediator tone" select in group settings (Epic 8.1 shipped early).
> Backend **259 passed / 0 skipped** (first zero-skip run); frontend **86
> passed**, main chunk 172.5 kB gz. Screenshots →
> `_bmad-output/implementation-artifacts/ws7-screenshots/`.
> Key learnings: (1) SSE endpoints must do auth/quota/settings work (and
> COMMIT) before returning StreamingResponse — the generator runs after
> dependency teardown, so snapshot ORM attrs first (expired instance access
> mid-stream = phantom generic error); (2) real HTTP status codes
> pre-stream beat error-events-on-200 for everything that can fail before
> headers are sent; (3) EventSource can't POST — read response.body with a
> buffered frame parser; (4) to E2E without a vendor key, point the SDK at
> a wire-compatible local fake via `GEMINI_BASE_URL` (google-genai
> HttpOptions.base_url). Going live with real Gemini = set GEMINI_API_KEY
> in .env, nothing else.
> WS8 (Template Purge & Security Hardening) DONE 2026-07-15 on branch
> `ws8/template-purge`: **attack surface halved** — the FastAPI template's
> parallel password-auth stack is gone (no /login/access-token,
> /password-recovery, /reset-password, /signup, /private, /admin, /items;
> Item table dropped; superuser user CRUD deleted; ChangePassword/Admin/
> Items/DataTable UI deleted; test fixtures mint JWTs directly).
> (a) S5-H1: OAuth callback now redirects with a 2-min SINGLE-USE code →
> `POST /auth/oauth/exchange` returns the JWT in the body — tokens never
> ride URLs; every JWT carries a `jti`, `revoked_token` table +
> POST /auth/logout = real server-side logout; login lifetime 30d→14d.
> (b) S5-H2: slowapi per-IP limits (10/min auth, 20/min AI parse, 200/min
> default, mediator-voice 429; in-memory per worker until WS12 Redis).
> (c) S5-M1/M6: security headers on API middleware + nginx (CSP, nosniff,
> DENY, no-referrer, HSTS outside local); allow_credentials=False.
> (d) S5-M3: Google OIDC rejects unverified emails (email_unverified code).
> (e) S5-M4: invite GET = read-only preview; joining = explicit POST from
> a landing page ("You're invited to X — Join"); max_uses cap (default 10,
> locked increment), owner revocation + list; revoke button in UI.
> (f) S5-C2/H4/M7, S6-H1: starlette 0.38.6→1.3.1 (CVE-2024-47874), fastapi
> 0.139, sentry 2.65 (send_default_pii=False), authlib≥1.3.1, slowapi;
> both Dockerfile syncs --locked (build fails on lock drift).
> (g) S5-M2: OAuth errors redirect with generic codes; str(e) → server log.
> (h) UX-H4/S4-M4: `getApiErrorMessage` mediator mapper — server detail
> passes through, transport failures become calm copy; no raw "Network
> Error"; handleError.bind contortion gone.
> Backend **249 passed / 0 skipped** (14 new WS8 security tests; template
> tests died with their endpoints); frontend **86 passed**, main chunk
> **169.2 kB gz**. Migration b2c3d4e5f6a7; `alembic check` clean. Live
> proof: template routes 404, headers on every response, 11th rapid auth
> hit 429s; Playwright 13/13 (invite preview→Join→group screen, SPA
> template routes dead, no Password tab, mediator OAuth-error copy).
> Screenshots → `_bmad-output/implementation-artifacts/ws8-screenshots/`.
> Key learnings: (1) converting a state-changing GET to preview-GET +
> action-POST silently breaks old tests — they still 200 on the GET but
> nothing mutates; grep every test call site of the old URL (8 fixed).
> (2) slowapi: construct the Limiter with enabled=settings.RATE_LIMIT_ENABLED,
> set it False in conftest BEFORE app import, and flip `limiter.enabled`
> inside the one test that asserts 429s. (3) Cold Vite dev loads apply the
> theme class late — Playwright screenshots must wait for body
> backgroundColor, not just element presence (extends the WS3 lesson).
> (4) Never point pydantic EmailStr test data at `.test` TLDs —
> email-validator rejects special-use domains (same trap as WS4's
> anonymized emails).
> WS9 (Deploy & Ops) DONE 2026-07-16 on branch `ws9/deploy-ops`:
> **the stack is deployable, backed up, and documented** — compose-on-VPS
> behind Traefik is the committed target (Railway claims purged from
> architecture.md/epics.md/CLAUDE.md; Swarm + docker-compose-v1 scripts
> deleted). (a) Backups (S6-C2/M5): custom postgres:17 sidecar
> (`scripts/db-backup.sh`) — nightly daemon (03:00 UTC, 14-day retention)
> + `pre-migrate-dump` one-shot GATING prestart (migrations never run
> without a fresh dump; failed dump fails the deploy); **restore drill
> executed** — pg_restore into a scratch DB matched live counts exactly
> (12/15/28/97). (b) Hardening (S6-H4): backend python:3.10-full →
> **3.13-slim** (1.98 GB → 464 MB), non-root USER, tests + dev deps out of
> prod (INSTALL_DEV arg; override mounts tests so in-container pytest still
> works); frontend npm ci + nginx:1.27-alpine (75 MB) + gzip + immutable
> /assets caching via `expires` (add_header would drop the WS8 security
> headers); memory limits + json-file 10m×3 log caps everywhere incl.
> Traefik. (c) Adminer OUT of prod compose (override-only); db/playwright
> no longer get the full .env (S5-H3/M1). (d) deployment.md replaced with
> the real runbook (secrets checklist + ENCRYPTION_KEY bricking warning,
> deploy, rollback-from-dump, restore drill, monitoring, owner to-dos).
> (e) Repo extraction DRILLED (subtree split, 55 commits); copier/fastapi-org
> template machinery deleted. Backend **249 passed / 0 skipped on 3.13**
> (2 template pre-start tests were doubly fake — py3.13's mock exposed
> them; rewritten); frontend 86 passed; main chunk 169.9 kB gz.
> Key learnings: (1) locked native deps can predate a new Python's wheels —
> relock the family (httptools/uvloop/uvicorn/watchfiles/websockets), never
> apt-get gcc into a slim image; (2) py3.13 mock rejects misspelled
> assertions (`.called_once_with`) — such tests never asserted anything,
> and patching "sqlmodel.Session" doesn't intercept `from sqlmodel import
> Session` (patch the name in the module under test); (3) nginx
> location-level add_header WIPES inherited headers — use `expires` for
> cache control; (4) test restore commands by RUNNING them: psql wants
> PGPASSWORD, not POSTGRES_PASSWORD (drill caught the runbook bug).
>
> WS9.5 (Replatform to Vercel + Render + Neon) DONE 2026-07-16 on branch
> `ws9.5/replatform`: **owner decision same day superseded WS9's
> compose-on-VPS** — Vercel (SPA) + Render (API) + Neon (Postgres 17) +
> cleardues.site, chosen for free tiers; Neon over Supabase (no 7-day
> pause, sub-second scale-to-zero resume, ~6h free restore window); repo
> extraction DEFERRED (monorepo Root Directory on both platforms + WS1
> root CI make nesting harmless; revisit WS11/WS13). Prepped:
> `render.yaml` blueprint (uv auto-detect, free plan, startup migrations
> — no preDeployCommand on free/Docker), `frontend/vercel.json` (SPA
> rewrite + WS8 headers + caching), `pool_pre_ping` + `POSTGRES_SSLMODE`
> (Neon DSN; local DSN unchanged, 2 tests), nightly Neon pg_dump GH
> Actions workflow (PGDG client 17, 30-day artifacts; cron only fires
> from the DEFAULT branch), deployment.md rewritten as a first-deploy
> walkthrough (VPS runbook → deployment-vps.md fallback).
> Key learnings: (1) Render preDeployCommand is paid-AND-non-Docker only
> — free tier puts `alembic upgrade head` in the start command; (2) Neon
> free ≠ Supabase free in idle behavior (suspend/instant-resume vs
> 7-day pause) and Neon direct host (no `-pooler`) must be used for
> migrations/pg_dump; (3) container app/ code is IMAGE-BAKED — tests/
> mount doesn't cover app edits, `docker compose cp` still required
> (re-learned); (4) GitHub scheduled workflows run ONLY from the default
> branch — deploy prerequisite is merging the ws-chain to main.
>
> WS10 SPLIT (owner decision 2026-07-20): WS10 (Growth Wiring & Analytics,
> ~1 week / 7 tasks) is broken into ATOMIC sub-sessions WS10.1–WS10.7 — one
> per conversation, none bloated. Full breakdown in
> `10-execution-plan.md` WS10 section. Analytics = PostHog + Sentry as ONE
> dedicated task (WS10.6) where the code lands here and the OWNER configures
> the instances on Render + Vercel. Payments (WS10.2) = per-user GLOBAL
> handles + a frictionless custom-handle path.
>
> WS10.1 (Currency Foundation) DONE 2026-07-20 on branch `ws10.1/currency`:
> **ClearDues is now global-market — no hardcoded "Rs".** Currency is a
> per-group setting (`GroupSettings.currency`, ISO-4217, default USD,
> locale-guessed at group create; migration c1d2e3f4a5b6). (a) Frontend
> `lib/currency.ts`: `formatCurrency` (Intl.NumberFormat, per-currency
> decimals, tolerates Decimal-string wire amounts, USD/0 fallback — never
> throws in render), `getCurrencySymbol`, `guessLocaleCurrency`
> (region→currency). (b) Threading: a `CurrencyProvider`/`useCurrency`
> context wraps the single-currency group subtree (GroupLedgerScreen +
> SmartInputModal) so deep money components format without prop-drilling;
> the two genuinely cross-group surfaces pass explicit per-item currency —
> dashboard rows (`GroupBalanceSummary.currency`) and /pending
> (`PendingConfirmationPublic.currency`). (c) Dashboard aggregate hero hides
> when groups span currencies (`DashboardResponse.currency` null) — summing
> across currencies is meaningless; per-group rows carry their own. (d)
> Backend `app/core/currency.py` curated ~46-code supported set + validation
> (422 on unknown, case-insensitive); mirrored to a frontend constant for the
> pickers (group settings owner-editable + create-group). Backend **258
> passed / 0 skipped**, `alembic check` clean; frontend typecheck green,
> **94 passed**, main chunk 170.16 kB gz.
> Key learnings: (1) `import app` in the backend container resolves to
> `/app/app` (the baked package) — `docker cp <abs-src> cleardues-backend-1:/app/`
> is required to sync app edits (and the PowerShell tool's cwd PERSISTS across
> calls, so a stray `cd frontend` silently breaks relative docker-cp sources);
> (2) dashboard-aggregating tests must mint a FRESH user — the shared
> normal_user accumulates committed groups from sibling tests and pollutes the
> cross-group total; (3) currency threading via React context is far less
> churn than prop-drilling ~14 components, and isolated component tests just
> get the USD default; (4) browser-pane screenshots still hang on this project
> and direct :5173→:8000 access is CORS-blocked — Playwright remains the
> pixel-proof fallback.
>
> WS10.2 (Payment Links + Universal Mark-as-Paid) DONE 2026-07-21 on branch
> `ws10.2/payment-links`: **you can now pay who you owe from the settle screen.**
> Per-user GLOBAL payment handles (`payment_method` table, migration
> c2d3e4f5a6b7; unique per user+provider+handle, cap 12, CASCADE + PII-scrub on
> account soft-delete). (a) `app/core/payment_providers.py` is the single source
> of truth for valid provider codes AND `build_pay_url` — venmo/paypal/cashapp/
> revolut deep-link to profile pages, upi → `upi://pay?pa=`, iban → copy-only,
> custom → a pasted https link becomes a button else copy-only. Handles are
> URL-encoded and custom URLs are restricted to http(s) (the custom handle
> renders as an <a href>, so a javascript:/data: payload would be stored XSS —
> rejected). The frontend `lib/payment-providers.ts` mirror holds ONLY
> presentation metadata; pay_url is server-computed and never duplicated. (b)
> Self-service CRUD `/users/me/payment-methods` (422 unknown provider,
> 409 duplicate/cap). (c) Counterparty lookup
> `GET /expense-groups/{id}/members/{uid}/payment-methods` gated by SHARED group
> membership (403 non-member caller, 404 target-not-in-group) — handles are
> public only to people in a group with you. (d) `PaymentHandles` (Pay deep-link
> + always Copy) surfaced at BOTH settle surfaces: the pairwise "Between you
> and…" settle-up confirm and the per-expense "Ready to settle" card;
> `PaymentMethodsManager` is a new Settings tab. Backend **288 passed / 0
> skipped** (+30), `alembic check` clean; frontend typecheck green, **103
> passed** (+9), main chunk 170.20 kB gz (payments in its own 1.37 kB chunk).
> Screenshots → `_bmad-output/implementation-artifacts/ws10.2-screenshots/`.
> Key learnings: (1) the nginx build is IMAGE-BAKED and ships a strict CSP
> (`connect-src 'self' https:`) that blocks the local http://localhost:8000 API —
> THIS is WS10.1's "CORS-blocked" wall (it's CSP). Pixel proof: `docker compose
> cp frontend/dist/. frontend:/usr/share/nginx/html/` to serve the fresh build,
> then Playwright with `bypassCSP:true` + a JWT in localStorage; the CSP stays
> verified by WS8's tests, never bypassed in prod. (2) `.local` and `.test`/
> `.invalid` TLDs fail email-validator — seed demo users with `@*.example.com`
> (same trap as WS4/WS8). (3) keep URL-construction server-side and give the
> frontend only display metadata — one source of truth, and the XSS-scheme guard
> lives in one place.
>
> WS10.3 (Invite public preview + OAuth-return) DONE 2026-07-21 on branch
> `ws10.3/invite-public`: **an invited person now sees the group before signing
> in and joins in one tap.** (a) New optional-auth dependency
> `OptionalCurrentUser` (deps.py, `OAuth2PasswordBearer(auto_error=False)`) that
> NEVER raises — no token, bad token, revoked, or inactive user all resolve to
> None. (b) `GET /expense-groups/invite/{token}` is now PUBLIC: `already_member`
> is only computed when authed (False for anonymous), `inviter_name` added,
> per-IP `PREVIEW_LIMIT` (30/min) as defense-in-depth. No migration (reuses
> GroupInvite). (c) Frontend `invite.$token.tsx` dropped the force-redirect to
> /login — logged-out visitors see "<inviter> invited you to <group> — N members"
> + one-tap "Continue with Google to join" (OAuthButtons gained `beforeRedirect`
> to stash the token + `showDivider`/`label` props) and an email fallback;
> signed-in visitors get the explicit Join button. (d) `auth.callback.tsx`
> auto-accepts the pending invite after the code exchange and lands the user in
> the group; magic-link carry (login.verify) unchanged. Backend **294 passed / 0
> skipped** (+6); frontend typecheck green, **103 passed**, build green.
> Screenshots → `_bmad-output/implementation-artifacts/ws10.3-screenshots/`.
> Key learnings: (1) for a public endpoint that personalizes when signed in, use
> a SEPARATE optional-auth dep (`auto_error=False`) — never loosen the strict
> `CurrentUser` (it stays a hard gate everywhere else). (2) The invite carry is
> pure frontend: sessionStorage survives the same-tab OAuth round trip, so
> `beforeRedirect` stashes the token and the callback replays it — no backend
> OAuth-state threading needed. (3) Playwright can't leave the page and still
> read sessionStorage; to assert the OAuth-carry, fulfill the OAuth-login
> navigation with **HTTP 204** (browsers stay on the current document for a 204),
> then read sessionStorage. `window.location.assign` can't be redefined on the
> instance ("Cannot redefine property").
>
> WS10.4 (Onboarding first-60-seconds) DONE 2026-07-21 on branch
> `ws10.4/onboarding`: **the organic path now has an aha before any setup, and
> no empty screen is a dead end.** (a) Sandbox parse: `ExpenseParseRequest.
> group_id` is now OPTIONAL — the parse endpoint skips the membership gate and
> defaults to friendly when no group_id is sent (grouped parses unchanged). It
> never persists (parse only ever returns data) and is metered like any hosted
> parse (a model call costs money; 429 on exhausted quota; no separate quota
> bucket). Frontend `parseExpense` groupId optional; new `OnboardingSandbox`
> renders on the empty dashboard: type an expense → real streamed commentary →
> read-only "here's what I read" preview (formatCurrency in the locale currency)
> → always-present "Create your first group" CTA. NO migration (request-field
> plumbing only). (b) Group templates: `ExpenseGroupCreate.strict_mode`
> (optional) threaded into `create_expense_group` → seeds GroupSettings;
> `features/groups/templates.ts` defines Roommates/Trip/Dinner (name + strictMode
> + social-contract blurb); CreateGroupForm chips prefill the name (only while
> it's still a template default — never clobbers a typed name) + send strict_mode.
> All three ship strict_mode OFF per S2 §6; the per-template field + optional
> payload keep nudge-cadence / settlement-cycle presets ready for WS12. (c) Empty
> states name the next action: groups page gains a "Create your first group"
> button (was text-only), activity "no groups" gains a CTA, dashboard empty state
> IS the sandbox. Backend **298 passed / 0 skipped** (+4), `alembic check` clean;
> frontend typecheck green, **111 passed** (+8), main chunk 170.40 kB gz.
> Screenshots → `_bmad-output/implementation-artifacts/ws10.4-screenshots/` (16,
> Playwright + API interception — no live Gemini needed).
> Key learnings: (1) a public/optional surface over an otherwise strict endpoint
> is cleanest as an OPTIONAL field guarded at the top (skip membership when
> group_id is None) — the strict path stays byte-identical, mirroring WS10.3's
> optional-auth dep. (2) The generated `GroupsService.createGroup` body type is
> loose (`{name}`) and `data` is passed as a variable, so extra optional fields
> (currency in WS10.1, strict_mode now) flow through at runtime with no client
> regeneration. (3) For pixel proof that needs a live backend + AI, Playwright
> `page.route` interception (canned dashboard JSON + a hand-rolled SSE parse
> response) beats wiring the real stack — it sidesteps the nginx CSP /
> cross-origin :8000 wall AND the absent GEMINI_API_KEY. Register the catch-all
> route FIRST (Playwright matches routes in reverse registration order).
>
> WS10.5 (Monetization Spec — DOC ONLY) DONE 2026-07-21 on branch
> `ws10.5/monetization`: **the one-page spec S1 §5 / S9 §6.4 demanded before
> Epic 6 now exists** — `_bmad-output/planning-artifacts/monetization-spec.md`.
> Consolidates S1 §5/§6, S2 §7/§9, S9 §6.4 into the accountable decision
> framework that makes "is feature X free or Pro?" answerable. Model: freemium ·
> organizer-pays · annual-first · USD-first, with a **non-negotiable free floor**
> (everything a Borrower does + unlimited groups/manual expenses — protects the
> network effect). Pricing USD-first (owner set 2026-07-22, undercutting S1 §5's
> $4.99/$39.99): **Pro $1.99/mo, $19.99/yr** (~16% off; thin gap — "set-and-forget"
> carries annual, not the discount), **Trip Pass $4.99 one-time / one group / 90
> days** (now positioned as pay-once-cover-everyone, NOT a cheaper Pro), **Group
> Pro** (one seat upgrades the group). Tier matrix carries an honest
> **Enforcement-today** column — the ONLY live code-enforced gate is the AI quota
> (`AI_FREE_MONTHLY_PARSES = 20`, config.py:131; spec number matches the code, not
> "e.g."); every Pro feature marked *planned* is free-because-absent until both it
> and the billing layer exist. Payment deep links stay FREE (WS10.2 — highest-intent
> moment). 7-row paywall-placement table (surface / trigger / soft-vs-hard gate /
> mediator-voice copy / status; AI-quota gate is SOFT — manual entry is always the
> fallback). Target **2–4% free→paid** + guardrail metrics (invite→join,
> mute-rate kill switch) handed to WS10.6 to instrument. Explicit out-of-scope:
> **NO billing/Stripe/entitlement built — beta ships free-only + instrumented; the
> paywall+billing build-out is Phase 4/post-beta.** No gates run (doc only, no code).
> Key learnings: (1) a monetization spec has to be pinned to the code it claims to
> price — the review said "~20 parses/mo (e.g.)", the spec says 20 *because
> config.py:131 says 20*, with a "don't drift them apart" note; (2) mark
> not-yet-built Pro features free-because-absent, not free-by-policy, so the doc
> stays honest under DoD and no one thinks the gate already ships; (3) keep the
> free floor a hard constraint the doc can veto scope against — that's the whole
> point of writing it.
>
> WS10.6 (Observability: PostHog + Sentry) DONE 2026-07-23 on branch
> `ws10.6/observability`: **the beta is measurable — every WS10.5 §8 metric
> that can exist today has an event, and errors report home.** All env-gated:
> unset keys = complete no-op (nothing even downloads). (a)
> `frontend/src/lib/analytics.ts` — typed `domain.entity.action` taxonomy
> (22 live events; the EVENTS map is the single source of truth, spec doc
> changes in the same commit) + PostHog wrapper: posthog-js DYNAMICALLY
> imported (own 77 kB gz chunk, fetched only when VITE_POSTHOG_KEY is set;
> pre-load events queue and flush in order), identify(user UUID) ONLY — no
> email/name (owner decision, matches S5-M7), autocapture/replay/auto-
> pageviews OFF, `advanced_disable_flags: true` (the remote config.js script
> would violate the prod CSP script-src 'self' — FE-010), and `sanitizeUrl`
> scrubs invite/verify tokens + OAuth ?code= from every outbound URL
> (an invite token in an analytics payload is a join credential). (b) ~20
> call sites: auth signed_up/logged_in/logged_out; group created
> (template/currency/strict) + settings updated; invite created/viewed
> (anonymous-capable)/joined (explicit|oauth_return) — the invite→join
> guardrail; ai parse started/completed/failed + quota.exhausted (paywall
> fuel gauge); expense created (source + was_edited = Trust Score)/
> confirmed/rejected; settlement claim created/confirmed (claim_age_hours =
> settlement velocity)/rejected; payment method/link/copy by provider;
> deduped SPA $pageviews. Reserved, NOT captured: nudge.notification.sent/
> muted (WS12 kill switch), billing.paywall.* (Phase 4). (c) Sentry
> frontend `@sentry/react` STATIC import (boot errors are the point;
> ~+5 kB gz tree-shaken, errors-only), gated on VITE_SENTRY_DSN, scrubbed
> beforeSend/beforeBreadcrumb; root errorComponent now passes the error to
> captureException (was swallowed). Backend init confirmed + `environment`
> tag. (d) Docs: `planning-artifacts/analytics-spec.md` (taxonomy contract,
> metric→event mapping, 5 dashboard recipes, privacy invariants, honest
> blind spots — lazy auto-confirm sweeps settle server-side so
> claim.confirmed undercounts); deployment.md §6.5 owner runbook + §7
> funnel-proof line; frontend/README env vars. Backend **298 passed / 0
> skipped**; frontend typecheck green, **127 passed** (+16), main chunk
> **175.55 kB gz** (≤250). Live smoke: dev server + throwaway key → app
> boots clean, chunk lazy-loads, distinct_id persisted, ONLY /e/ capture
> traffic (no config.js, no /flags).
> Key learnings: (1) posthog-js by default injects a REMOTE config.js
> <script> — under script-src 'self' it dies silently; `advanced_disable_
> flags: true` drops both that script and the /flags XHR, leaving only
> fetch-based capture (verify via performance.getEntriesByType("resource")).
> (2) Analytics SDK loading should match its failure cost: Sentry static
> (missing a boot error defeats its purpose), PostHog lazy behind a queue
> (losing 300ms of analytics costs nothing, 77 kB gz off the main chunk).
> (3) Put track() calls in mutation onSuccess at the API-hook layer when the
> event needs no UI context, at the component only when it does (template
> choice, was_edited diff) — grep the hook's call sites first; a hook-level
> event on a hook used twice double-fires. (4) The browser pane's network
> reader missed cross-origin capture requests; performance resource entries
> inside the page are the reliable proof.
>
> **Next: WS10.7 (Push) is BLOCKED on WS11/WS12 → next runnable session is
> WS11 (Docs Floor + Test Journeys + PWA Shell). OWNER ACTIONS: deployment.md
> first-deploy walkthrough now includes §6.5 (create PostHog project + two
> Sentry projects, set VITE_POSTHOG_KEY / VITE_SENTRY_DSN on Vercel and
> SENTRY_DSN on Render) and the §7 checklist gained the cold
> invite→join→activation funnel proof; rotate the exposed PAT + repoint
> remote (unchanged).**

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
- **Streaming AI text (WS7)**: SUPERSEDED — the setInterval typing effect (and its useStreamingText hook) was deleted with the AI mock. Real commentary streams over SSE; consume with a fetch body reader (EventSource can't POST) and append chunks to state. Abort in-flight parses with AbortController on modal close/unmount.
- **Feature-Specific Components**: Create feature-specific versions of generic UI components (e.g., `/features/expenses/components/SmartInputModal` vs `/components/ui/smart-input-modal`) for better separation of concerns.

### Testing
- **Tests pass alone, fail together** → Database state leaking, use rollback fixtures

---

## Architecture Quick Reference

```
Backend: FastAPI + SQLModel + PostgreSQL
Frontend: React + TypeScript + Vite + TanStack (Router + Query)
Infra: Docker Compose (dev + prod; VPS behind Traefik — decided WS9)

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
cd frontend && npm run typecheck

# Frontend build
cd frontend && npm run build
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
- WS6 Aggregate Settle-Up + Confirmation Policy ← **DONE** ✓ (2026-07-13;
  branch ws6/settle-up; settle-with-X netting one-claim-one-confirm, 72h
  auto-confirm dispute window via lazy sweeps, strict-mode toggle, pairwise
  balance view; backend 232 passed, frontend 98 passed)
- WS7 Real AI Path ← **DONE** ✓ (2026-07-14; branch ws7/real-ai;
  hosted-first Gemini + 20-parse monthly quota, BYOK demoted, dedicated
  ENCRYPTION_KEY + HKDF, async client + honest SSE contract, real frontend
  SSE consumption, manual-confirm only, Mediator-tone setting capped at
  funny; backend 259 passed / 0 skipped, frontend 86 passed. Live Gemini
  needs only GEMINI_API_KEY in .env)
- WS8 Template Purge & Security Hardening ← **DONE** ✓ (2026-07-15; branch
  ws8/template-purge; password-auth stack + /admin + /items deleted, OAuth
  one-time-code delivery + jti revocation + logout, per-IP rate limits,
  security headers, OIDC email_verified, invite preview/POST-accept/caps/
  revocation, starlette CVE cleared + sentry 2.x + --locked builds,
  mediator error mapper; backend 249 passed / 0 skipped, frontend 86
  passed, main chunk 169.2 kB gz)
- WS9 Deploy & Ops ← **DONE** ✓ (2026-07-16; branch ws9/deploy-ops;
  compose-on-VPS committed + Railway/Swarm purged, backup sidecar +
  pre-migration dump gate + EXECUTED restore drill, python:3.13-slim
  non-root images (464 MB / 75 MB), Adminer out of prod, env_file scoped,
  log caps + memory limits, real runbook in deployment.md, repo extraction
  drilled; backend 249 passed / 0 skipped on 3.13, frontend 86 passed.
  Staging TLS + uptime-alert verification pend on owner-provisioned
  VPS/domain — see deployment.md §7 owner to-dos)
- WS9.5 Replatform ← **DONE** ✓ (2026-07-16; branch ws9.5/replatform;
  Vercel + Render + Neon free-tier stack prepped end-to-end: render.yaml,
  vercel.json, Neon-ready engine/DSN, nightly backup workflow,
  first-deploy walkthrough in deployment.md; VPS path → deployment-vps.md)
- WS10 Growth Wiring & Analytics ← **SPLIT into WS10.1–WS10.7** (atomic
  sub-sessions, run one per conversation; see 10-execution-plan.md)
  - WS10.1 Currency Foundation ← **DONE** ✓ (2026-07-20; branch
    ws10.1/currency; per-group ISO-4217 currency, formatCurrency util +
    context, all "Rs" purged, currency pickers; backend 258, frontend 94)
  - WS10.2 Payment Links + Mark-as-Paid ← **DONE** ✓ (2026-07-21; branch
    ws10.2/payment-links; per-user global handle registry, provider deep-links
    + copy, counterparty surface at both settle paths, Settings manager;
    backend 288, frontend 103)
  - WS10.3 Invite public preview + OAuth-return ← **DONE** ✓ (2026-07-21;
    branch ws10.3/invite-public; public unauth preview + inviter_name, one-tap
    Google join carrying the token → auto-land in group; backend 294, frontend
    103)
  - WS10.4 Onboarding first-60s ← **DONE** ✓ (2026-07-21; branch
    ws10.4/onboarding; organic sandbox parse [group_id optional], group templates
    Roommates/Trip/Dinner, next-action empty states; backend 298, frontend 111)
  - WS10.5 Monetization spec (doc) ← **DONE** ✓ (2026-07-21; branch
    ws10.5/monetization; `planning-artifacts/monetization-spec.md` — freemium/
    organizer-pays/annual-first, Pro $1.99/mo·$19.99/yr + Trip Pass $4.99 + Group Pro,
    tier matrix w/ honest enforcement-today column, AI quota pinned to
    config.py:131=20, 7 paywall placements, 2–4% conversion target; no code)
  - WS10.6 Observability ← **DONE** ✓ (2026-07-23; branch
    ws10.6/observability; 22-event domain.entity.action taxonomy + PostHog
    wrapper [UUID-only identity, no autocapture/replay/flags, token-scrubbed
    URLs, lazy chunk], Sentry frontend static + backend env tag, analytics-spec
    + deployment.md §6.5 owner runbook; backend 298, frontend 127, main chunk
    175.55 kB gz; owner sets the env keys to switch it on)
  - WS10.7 Push — **PARTIALLY UNBLOCKED by WS11** (the service worker now
    exists). Runnable standalone slice: permission-prompt UX after the first
    confirmed expense + subscription/preference store. Actual delivery still
    needs WS12.
- WS11 Docs Floor + Test Journeys + PWA Shell ← **DONE** ✓ (2026-08-25; branch
  ws11/docs-e2e-pwa). Four things landed:
  1. **Docs floor** — repo-root README (what/status/stack/quickstart/layout),
     LICENSE re-attributed to ClearDues with the template-derivation notice kept,
     backend/README rewritten around the feature-based layout + real Alembic
     workflow, SECURITY.md given a real contact + scope + safe harbour.
     `release-notes.md` (755 lines of upstream changelog) and all 7 template
     `img/` screenshots deleted.
  2. **Tracking reconciled** (S7-M2/M4) — counts were wrong in three places and
     are now derived from sprint-status.yaml: **33 of 47 done, 14 remaining**
     (was "32 done, 13 remaining"), Epic 6-7 **0/10** (was 0/18), Epic 8 **1/4**
     (was 0/4). All 11 bypassed "⚠️ BEFORE PRODUCTION" items are annotated
     done / deferred-with-link / dropped-with-reason. The Epic-4 testing-infra
     BLOCKER really was bypassed — it landed in WS1, months after epic-4 closed
     — and is now recorded as a bypass rather than quietly dropped.
  3. **Test journeys** — 4 template Playwright specs + 3 template helpers
     deleted; **12 tests across 5 specs** written (magic-link sign-in, group
     create+invite, expense confirm/reject, settle-up, plus a CSP-header guard),
     with a new `e2e` CI job that stands the real compose stack up and uploads
     the Playwright report. **These were not green when written** — they passed
     once, then failed. Three real defects, now fixed:
     - The suite **trips the app's own auth rate limit** (10/minute per IP, WS8)
       after ~20 registrations. Fix: `RATE_LIMIT_AUTH` setting, **default still
       10/minute so production is unchanged**, raised to 1000/minute only for the
       e2e stack (ci.yml + local .env); limiting stays ENABLED and every other
       tier is untouched. `AUTH_LIMIT` became a *callable* so slowapi re-reads it
       per request, which lets `test_ws8_security` pin 10/minute for itself
       (solution-patterns TEST-008).
     - **Every test shares one account** (one storageState), so `/pending` and
       `/groups` mix all tests' rows. Hardcoded descriptions collided across
       parallel tests, and `.first()` on the Confirm button confirmed *another*
       test's expense. Fix: `uniqueLabel()` + row-scoped `actOnPending()`
       (TEST-007).
     - `waitForURL` returns while the previous route is **still mounted**, so
       `getByText("1 member")` matched 6 list cards and died on strict mode. Fix:
       wait for the detail `<h1>`, and assert member counts through
       `expectMemberCount()`. A duplicate `createGroup` in group-invite.spec.ts
       was deleted in favour of the shared helper.
     Verified with **9 consecutive clean full-suite runs** plus a CI-shaped
     single-worker run — one green run proves nothing here.
  4. **PWA install shell** — vite-plugin-pwa, 4 brand icons, per-scheme
     theme-color. `runtimeCaching: []` + an `/api/` navigate-fallback denylist
     keep the SW off API responses on purpose: **offline data is out of scope**,
     because a stale balance shown as current is worse than no balance.
  Also: the API-client question (S7-M3) is **decided — regenerate**. There is a
  `scripts/generate-client.sh`, the rule is in frontend/README, and **groups** is
  the migrated exemplar; 32 hand-built `__request` call sites in
  auth/dashboard/expenses are queued to follow. Two backend response schemas were
  tightened so the generated client stops lying (`ExpenseGroupDetail` defaults
  dropped; `ai_personality` → `Literal`). **`scripts/generate-client.sh` was
  itself broken** — it ran `python -c "import app.main"` on the *host*, and the
  backend's deps only exist in the image, so the freshly-documented command could
  not run on any checkout. It goes through `docker compose exec` now, refuses to
  regenerate from an empty dump, and was verified by actually running it.
  Gates: backend **298 passed**, `uv lock --check` in sync, frontend **127
  passed**, typecheck + build green, **12/12 journeys pass (9 runs in a row)**,
  main chunk 175.79 kB gz.
  Key learning: the in-app Browser pane **cannot register service workers at all**
  — registration fails with "unknown error occurred when fetching the script"
  while a plain fetch() of the same URL returns 200. Verify SW/PWA work in real
  Chromium via Playwright instead (solution-patterns FE-011).
  **Owner action:** `security@cleardues.site` (SECURITY.md) must be a real,
  monitored mailbox before beta.

**Next runnable: WS12 (Nudge Engine: Infra + Level 1)** — the product's reason to
exist. WS10.7's standalone slice can be folded in or run first; its delivery half
needs WS12 either way.

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
