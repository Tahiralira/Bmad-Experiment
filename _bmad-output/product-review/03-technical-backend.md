# Session 3 — Technical Review: Backend

**Date:** 2026-07-06
**Scope:** Part 3a — backend architecture, API design, DB models/migrations, service
layer, error handling, logging, backend tests, the pytest-blocking SQLAlchemy bug.
**Inputs read:** architecture.md, entire `backend/` tree (app + tests +
alembic), technical-debt-log.yaml, solution-patterns.yaml, findings 01–02.

---

## 1. Verdict Up Front

The backend is **better-crafted at the micro level than expected** (Decimal money on
core tables, hashed magic-link tokens, batch queries to kill N+1s, real authorization
checks on almost every endpoint) but **structurally dishonest at the macro level**: the
codebase claims capabilities it does not have. Three flagship claims are false today:

1. **"AI parsing works (FR1)"** — it is broken for 100% of requests by a
   swapped-argument bug, AND no user can ever configure the API key it requires,
   AND no group can ever change the AI personality. Three independent showstoppers.
2. **"Real-time via WebSockets + Redis + Celery"** — none of it exists. The single
   piece of event-publishing code silently no-ops because `redis` isn't even a
   dependency.
3. **"125 tests passing"** — the suite cannot run at all (SQLAlchemy annotation bug),
   12 AI tests reference a fixture that has never existed, and the tests that do exist
   assert so weakly they passed over the top of the broken AI endpoint.

This matches the Session 2 diagnosis (zero deployments, velocity decay): the process
marks stories "done" against a test suite nobody has run in months. The good news: every
CRITICAL item below is a small, local fix (hours, not weeks). The bad news: the invariant
violations in the money paths (H2, H3) mean **the ledger itself cannot currently be
trusted**, which for a trust-centric fintech product is the whole game.

**Backend health score: 4.5/10.** Solid starter-template bones and decent per-endpoint
hygiene, dragged down by unrun tests, dead architecture, and broken money invariants.

---

## 2. Findings Summary

| ID | Severity | Finding | Effort to fix |
|----|----------|---------|---------------|
| C1 | CRITICAL | AI parse membership check has swapped args — feature 100% broken | 5 min + test |
| C2 | CRITICAL | BYOK has no write path — no endpoint to save a Gemini key | 0.5–1 day |
| C3 | CRITICAL | Test suite cannot run (`GroupSettings \| None` annotation) + phantom `db_session` fixture | 2–4 hours |
| C4 | CRITICAL | `DELETE /users/me` either 500s or cascade-deletes shared financial records | 0.5–1 day |
| C5 | CRITICAL | Fernet key derived from possibly-ephemeral SECRET_KEY → stored API keys can be permanently bricked | 2–4 hours |
| H1 | HIGH | Real-time layer (Redis/WebSockets/Celery) unimplemented; publish code silently no-ops | decision + N days |
| H2 | HIGH | Editing expense amount never recalculates splits → splits ≠ total | 2–4 hours |
| H3 | HIGH | Reject-split flow: 5 distinct integrity bugs in one function | 1 day |
| H4 | HIGH | Settlement rejection never sets REJECTED status; returns stale "pending" | 1–2 hours |
| H5 | HIGH | Transaction discipline: 2–4 commits per operation; audit entries can be silently lost | 1–2 days |
| H6 | HIGH | Split endpoint takes raw `dict`; defined Pydantic schemas never used; 3× duplicated validation; 500 on bad UUID | 1 day |
| H7 | HIGH | API completeness: no way to GET an expense, list a group's expenses, or view splits | 1–2 days |
| H8 | HIGH | Blocking synchronous Gemini calls inside async SSE generator stall the event loop | 0.5 day |
| H9 | HIGH | Alembic autogenerate blind to all feature models; schema drift already present | 2 hours |
| H10 | HIGH | Test infra unsafe (wipes configured DB) + incomplete teardown + assertion-free tests | 1–2 days |
| M1–M12 | MEDIUM | See Section 5 | — |
| L1–L6 | LOW | See Section 6 | — |

---

## 3. CRITICAL Findings

### C1 — AI expense parsing is broken for every request (swapped arguments)

`app/features/ai/parser_router.py:67`:

```python
if not is_user_group_member(session, expense_in.group_id, current_user.id):
```

The signature (`app/features/expenses/service.py:71`) is
`is_user_group_member(session, user_id, group_id)`. The router passes **group_id as
user_id and user_id as group_id**, so the query looks for a GroupMember whose user_id
equals the group's UUID — which never exists. Every parse request, for every user, in
every group, returns *"You must be a member of this group to parse expenses."*

**FR1 — the natural-language entry point, the product's first differentiator — has
never worked through the API.** Session 1 rated the AI feature as "implemented"; that
must be downgraded to "implemented but non-functional."

Why tests didn't catch it: the SSE endpoint returns HTTP 200 even for error events, and
`test_parse_expense_sse_streaming` asserts only `status_code == 200` and the
content-type header. The error path IS the response and the test can't tell.
Additionally the 12 AI tests can't run at all (see C3).

Root cause worth fixing at the pattern level: the codebase has **two near-identical
membership helpers with opposite parameter orders** —
`expenses.service.is_user_group_member(session, user_id, group_id)` and
`groups.service.is_group_member(session, group_id, user_id)`. This footgun already
fired once; it will fire again. (See M10.)

**Impact:** flagship feature dead. **Effort:** one-line fix; plus a real test that
asserts the SSE `complete` event payload. 30 minutes.

### C2 — BYOK cannot be configured: `encrypt_api_key` is only ever called by tests

`gemini_api_key_encrypted` exists on the User model and migration, and
`decrypt_api_key` is used by the parser — but **no endpoint anywhere accepts an API
key from a user.** `UserUpdateMe` has only `full_name` and `email`. Grep confirms
`encrypt_api_key` appears in `core/security.py` and `tests/` only.

So even after fixing C1, the parser's step-2 check ("no API key configured") fails for
every real user forever. The error message helpfully tells users to "add your Gemini
API key in settings" — a settings screen and endpoint that do not exist.

Same pattern, second instance: **`GroupSettings.ai_personality` has no write path
either.** The only code that ever writes it is the read-path default-creation in
`parser_service.get_group_personality`. The four personality modes (including the
"f3-pbs" roast mode that Session 1 flagged as a differentiator) are unreachable — every
group is permanently "friendly."

**Impact:** the whole AI slice is a Potemkin feature: storage, parsing, personalities
all coded, no way in. **Effort:** `PUT /users/me/api-key` (+ DELETE), and
`PATCH /expense-groups/{id}/settings` with owner check — 0.5–1 day including tests.
**Strategic note for Session 9:** Session 1 already recommended killing BYOK for a
managed-key model; if that's adopted, build the managed path instead of the missing
BYOK endpoints — don't pay this cost twice.

### C3 — The test suite cannot run, and part of it never could

Two independent blockers:

1. **The known SQLAlchemy bug** (Sessions 1–2, confirmed at
   `app/features/groups/models.py:102`):

   ```python
   settings: "GroupSettings | None" = Relationship(back_populates="group")
   ```

   SQLModel cannot resolve a PEP-604 union inside a forward-reference string here;
   mapper configuration fails, and since `conftest.py` imports `app.main`, **all 193
   collected test functions across 13 files die at import time.** Fix: change the
   annotation to `Optional["GroupSettings"]` (and audit the other models for the same
   pattern — the rest currently use plain or quoted non-union annotations, which are
   fine). This is a two-line fix that has been "known" long enough to appear in three
   tracking files while five stories shipped on top of it.

2. **The 12 AI-parsing tests reference a `db_session` fixture that is defined
   nowhere.** conftest.py defines `db`, not `db_session`. These tests have errored at
   setup since the day they were written — they were never green. The story that
   introduced them was marked done with "tests passing."

Consequence: the MVS standard's "Tests Passing" gate (CLAUDE.md) has been rubber-stamped
for months. This is a process failure as much as a code failure — flag for the Session 9
action plan: **"suite green in CI" must become a hard gate before any further story.**

**Impact:** zero regression protection on a money-handling backend. **Effort:** fix
annotation (30 min), rename/alias fixture (30 min), then triage whatever actually fails
once the suite runs (budget 2–4 hours; expect real failures — e.g., the AI router tests
assert pre-C1-fix behavior).

### C4 — Account deletion destroys or deadlocks shared financial records

`DELETE /users/me` (`auth/router.py:292`) does `session.delete(current_user)`. At the
DB level (`e8f9a0b1c2d3` migration): `expense.payer_id` and `expense.created_by` are
both `ON DELETE CASCADE`, and `expense_split.user_id` cascades too. But
`audit_log.expense_id`/`user_id` (migration `5e78d661700e`) and
`settlement_claim.claimant_user_id` have **no** ondelete.

So deleting a user takes one of two bad paths:

- **If audit rows or settlement claims reference their expenses/user:** the cascade is
  blocked by the FK → `IntegrityError` → unhandled 500. Account deletion is simply
  broken for any user who has done anything.
- **If not:** the cascade **silently deletes expenses the user paid for in shared
  groups**, including every other member's splits — other people's debt records vanish.
  For a product whose PRD centerpiece is an immutable audit trail and trust, this is a
  data-loss landmine. FR-level violation: audit logs must outlive the entities they
  describe.

**Correct design:** soft-delete/anonymize users (`is_active=False`, scrub PII), keep
financial rows; forbid hard delete when the user is payer on any non-settled expense.
**Impact:** data loss / broken endpoint on a required GDPR-ish flow. **Effort:** 0.5–1
day (endpoint logic + migration to change FK behavior + tests).

### C5 — Encryption key management can permanently brick stored user API keys

`core/config.py:34`: `SECRET_KEY: str = secrets.token_urlsafe(32)` — if the env var is
missing, each process start generates a **new** secret. `core/security.py:47` derives
the Fernet key from SECRET_KEY by truncate-pad (`[:32].ljust(32, b"0")`), and module
import instantiates a global `_fernet`.

Consequences:

- If SECRET_KEY is not pinned in the environment (nothing in the backend enforces that
  it is — the "changethis" guard only catches the literal placeholder), every restart
  invalidates all JWTs **and makes every stored `gemini_api_key_encrypted`
  permanently undecryptable.** Unlike JWTs, that's unrecoverable data loss.
- Any intentional SECRET_KEY rotation also bricks all stored keys — there is no key
  versioning or re-encryption path. Rotating the app secret (routine security hygiene)
  is now coupled to destroying user data.
- The derivation is truncate-pad, not a KDF, and the docstrings/model comment claim
  "AES-256 (NFR4)" while Fernet is AES-128-CBC. NFR4 is not met as written.
  (Crypto-strength details → Session 5; the **data-loss coupling** is the backend bug.)

**Impact:** silent, unrecoverable loss of user credentials on restart/rotation.
**Effort:** dedicated `ENCRYPTION_KEY` setting (fail-fast if absent outside local) +
HKDF derivation + one-time migration — 2–4 hours. Moot if BYOK is dropped (Session 1),
but the SECRET_KEY-must-be-pinned fix is needed regardless for JWT stability.

---

## 4. HIGH Findings

### H1 — The architecture's real-time core does not exist; the one event publisher silently no-ops

architecture.md's critical decisions: WebSockets for real-time, Redis Pub/Sub broker,
Celery worker, `core/socket.py`, standard event envelope
(`{event, timestamp, payload}`). Reality:

- **Zero WebSocket code** anywhere in `app/` (grep confirms; only uv.lock matches).
- **No Celery**, no worker, no task queue.
- **`redis` is not in pyproject.toml dependencies.** The only publisher,
  `publish_expense_confirmed_event` (`expenses/service.py:490`), does `import redis`
  inside a try/except that swallows **all** exceptions with a warning log. The
  ImportError means this function has never published anything, in any environment,
  and nobody noticed — because nothing consumes the events either.
- The payload it would send uses a flat `event_type` shape and `float(expense.amount)`,
  violating both the architecture's envelope contract and Decimal discipline.

This is worse than "not built yet": it's **dead code wearing the architecture's
uniform**, which misleads every future story (and every AI agent reading the code) into
believing the rail exists. Epic 6 (agentic notifications — the product's reason to
exist, per Session 1) is designed on top of this rail.

**Recommendation:** delete `publish_expense_confirmed_event` and
`notify_group_of_finalized_expense` (also dead — logged as 4.3-L2) now, and make an
explicit architecture decision before Epic 6: either build the Redis/WS layer as its own
story (3–5 days) or descope real-time from MVP and amend architecture.md. Don't let
Epic 6 stories discover this mid-implementation.
**Impact:** Epic 6 blocked on phantom infrastructure; NFR1 (<200ms sync) currently
fiction. **Effort:** deletion 1 hour; the real decision is roadmap-level (Session 9).

### H2 — Editing an expense's amount orphans its splits

`PATCH /expenses/{expense_id}` allows the creator to change `amount` while status is
DRAFT **or PENDING_CONFIRMATION**. Splits are never touched (`update_expense` only sets
expense fields). Result: splits that no longer sum to the expense amount, and — worse —
members who already confirmed a split of Rs 500 are now silently party to a Rs 5,000
expense. The audit log records the edit but nothing re-opens consent.

**Fix:** on amount change with existing splits, either (a) delete splits and revert to
DRAFT (simplest, forces re-split + re-confirm), or (b) recalculate equal splits and
reset all splits to PENDING. Option (a) recommended — it preserves the Epic 4 trust
contract ("what you confirmed is what you owe").
**Impact:** ledger integrity + consent violation in the core money path. **Effort:**
2–4 hours + tests.

### H3 — `reject_expense_split` is five bugs in one function (`expenses/service.py:607`)

When a member rejects a split, the code deletes their split and redistributes
`expense.amount / len(remaining_splits)` across whoever is left. Problems:

1. **Overwrites already-CONFIRMED splits' amounts without resetting their status** —
   members stay "confirmed" on numbers they never saw. Same consent violation as H2.
2. **Destroys unequal/percentage splits** — a rejection converts any split type into
   equal shares, silently discarding the creator's configuration.
3. **Unquantized division** — `100 / 3` produces a repeating Decimal; the payer-absorbs-
   remainder logic from `calculate_equal_split` is not reused, so stored amounts can sum
   to 99.99 against a 100.00 expense (Numeric(10,2) rounds per-row).
4. **Never re-checks finalization** — if the last PENDING member rejects while everyone
   else is CONFIRMED, the expense stays PENDING_CONFIRMATION forever (finalize is only
   triggered from the confirm path). Stuck state, user-visible.
5. **Can leave a single split** (even just the payer's own), violating the "at least 2
   members" invariant enforced everywhere else — and leaving an "expense" where the
   payer owes themselves the full amount.

**Recommended semantics:** rejection should NOT auto-redistribute. Set the expense back
to DRAFT (or a REJECTED-attention state), notify the creator, and require an explicit
re-split. That matches the trust-workflow product framing and deletes all five bugs at
once. **Impact:** core money-path integrity. **Effort:** 1 day including tests and a
product-behavior decision (flag to Session 9).

### H4 — Settlement rejection never records the rejection on the claim

`reject_settlement_claim` (`expenses/service.py:1018`) builds the response **before**
mutating anything, never sets `status = REJECTED` or `rejected_at`, and then deletes the
claim row. Consequences: the API returns a claim object still saying `"pending"` (the
docstring and Story 5.2 say it returns the rejected state); `rejected_at` is dead
schema; `SettlementClaimStatus.REJECTED` is an enum value that can never exist in the
DB. The audit log alone remembers the rejection. Deleting-to-allow-reclaim is a fine
design, but the response/model should tell the truth: set status+rejected_at on the
in-memory object before building the response, or return a purpose-built response
schema. **Impact:** wrong API contract on a shipped Story 5.2 path; frontend showing
stale "pending." **Effort:** 1–2 hours.

### H5 — No transactional discipline; the audit trail is not actually guaranteed

Two conflicting idioms coexist: groups service uses flush-and-caller-commits (router
commits once — correct); expenses service **commits internally 2–4 times per
operation**. E.g. `create_expense` commits the expense, then commits the audit entry;
`update_expense_split` (router) commits splits, then status, then audit — three
transactions for one logical action. Failure between commits yields: expenses without
CREATED audit entries, splits assigned without status transition, finalized expenses
without CONFIRMED audit rows. For a product whose PRD sells an **immutable, complete**
audit trail, "usually written, in a separate transaction" is not a guarantee — it's a
race. Also, `record_audit`'s try/except wraps only object construction (which cannot
fail meaningfully); the real failure point is the later commit, which is unprotected —
so the "non-blocking" docstring claim is false.

**Fix:** adopt one-transaction-per-request everywhere (services flush, the request
commits once — the groups idiom); audit writes join the same transaction so an operation
and its audit entry are atomic. Add this to solution-patterns.yaml as the canonical
pattern. **Impact:** auditability guarantee, partial-write bugs. **Effort:** 1–2 days
(mechanical but touches most expense service functions + tests).

### H6 — The split endpoint bypasses the API layer's own validation machinery

`PUT /expenses/{expense_id}/split` takes `split_data: dict = Body(...)`. The models file
defines `EqualSplitRequest`, `UnequalSplitRequest`, `PercentageSplitRequest` — **none
are used anywhere.** In their place: ~220 lines of hand-rolled validation in the router,
with the member-lookup/validation block copy-pasted three times, and
`uuid.UUID(str(excluded_id))` raising an unhandled ValueError → **500 on malformed
input** (e.g. `"excluded_user_ids": ["not-a-uuid"]`). OpenAPI docs for the body are an
empty object, so the generated client/frontend gets no typing. Fix: discriminated union
(`Annotated[Union[...], Field(discriminator="type")]`), collapse the router to ~40
lines, move member validation to one service function. **Impact:** 500s on bad input,
docs/codegen broken for the most complex endpoint, 3× maintenance surface.
**Effort:** 1 day.

### H7 — The API cannot display the ledger it stores

Missing read/manage endpoints, verified against both routers:

- `GET /expenses/{id}` — no way to fetch one expense
- `GET /expense-groups/{id}/expenses` (or `GET /expenses?group_id=`) — **no way to list
  a group's expenses at all**
- `GET /expenses/{id}/splits` — no way to see who owes what on an expense (the payer
  can only infer state from pending-claims lists)
- `GET /expense-groups/{id}` — no group detail (root cause behind frontend debt item
  RETRO-2.5-H2 "group navigation broken")
- No `DELETE /expenses/{id}` (DRAFT cleanup), no leave-group, no remove-member, no
  delete-group

The only expense reads that exist are role-scoped worklists (pending-confirmations,
pending-settlements, claims-for-owner) and the audit log. A member who confirmed
yesterday cannot ask "what do I owe in this group right now?" — which is the app's core
screen. Session 2's "no aggregate settle-up" CRITICAL is the same gap one level up.
**Impact:** frontend cannot build the group ledger view; core UX blocked. **Effort:**
1–2 days for the read endpoints (balance/ledger aggregation exists in
`get_user_dashboard` and can be generalized).

### H8 — Blocking LLM calls inside the async SSE generator freeze the event loop

`parse_expense` is the only `async` route in the codebase, and it's the one that makes
**synchronous** network calls: `client.models.generate_content(...)` twice (parse +
commentary), sequentially, with no timeout, inside the async generator. While Gemini
responds (seconds), the entire event loop — every other request on the worker — stalls.
This inverts FastAPI's model (sync routes get threadpools; async routes must not block)
and makes NFR7 (1,000 concurrent connections) unreachable. Also: the "streaming" is
theater — the full commentary is already computed, then re-chunked one SSE event **per
character**; and errors stream inside a 200 response while the docstring advertises
400s. Fix: `google-genai`'s async client (or `run_in_executor`), add a timeout, chunk
by word/sentence, and document the SSE error contract honestly. **Impact:** platform-
wide latency under any AI usage; NFR7. **Effort:** 0.5 day.

### H9 — Alembic autogenerate is blind to every table added since Epic 1

`alembic/env.py:21` imports only `app.models` — the auth/back-compat shim. Groups,
expenses, splits, audit_log, settlement_claim, group_settings never enter
`SQLModel.metadata` for autogenerate. That's why every Epic 2–5 migration was
hand-written, and drift already exists: `settlement_claim`/`audit_log` use **naive**
`sa.DateTime()` while expense uses `DateTime(timezone=True)` (naive vs aware timestamps
in the same schema — comparison bugs waiting); `settlement_claim.status` is unbounded
`sa.String()` vs String(20/30) elsewhere. Fix: import all feature model modules in
env.py, then run one autogenerate diff against a clean DB and reconcile. **Impact:**
every future story hand-writes migrations and drifts further. **Effort:** 2 hours.
(Positive note: the migration chain itself is clean — single linear head
`a6b7c8d9e0f1`; debt item 5.1-L1 can be closed.)

### H10 — Test infrastructure is unsafe and self-deceiving

- **conftest `db` fixture runs against whatever DB the settings point to and deletes
  every row at session end** (`delete(User)` etc.). Run pytest with a dev `.env` and
  your dev data is gone. There is no separate test database or transaction-rollback
  isolation (solution-patterns TEST-002 describes the symptom without fixing the
  cause).
- **Teardown is incomplete and will itself crash:** it never deletes `Expense` or
  `ExpenseSplit`, but deletes `ExpenseGroup` — `expense.group_id` FK (CASCADE) saves
  it, but `audit_log -> expense` (no ondelete) makes the AuditLog-then-later ordering
  fragile; any future FK without cascade breaks teardown.
- **Assertion quality:** the AI SSE tests assert only status/content-type (how C1
  survived); `test_split_nonexistent_expense_returns_404` style tests are fine, but
  there are no tests for: expense edit vs splits (H2), reject redistribution (H3),
  settlement rejection response shape (H4), concurrency/idempotency, or any Decimal
  drift property.
- **Typing is decorative:** mypy strict is configured, yet
  `settle_expense_split -> SettlementClaimPublic` actually returns
  `None | str | SettlementClaimPublic`. mypy clearly isn't being run either (it cannot
  pass); same for the sentinel-string returns pattern (M4).

**Fix:** dedicated test DB (env override + fail-fast guard if `ENVIRONMENT != local`),
per-test transaction rollback, delete the manual teardown, and add mypy + pytest to a
CI gate (CI itself is Session 6 scope, but the gate decision belongs in the action
plan). **Impact:** the only safety net for a money backend is currently a hazard.
**Effort:** 1–2 days.

---

## 5. MEDIUM Findings

- **M1 — Money as float at the edges.** `GroupBalanceSummary.net_balance` /
  `DashboardResponse.total_balance` are `float` (`auth/models.py:183–199`), populated
  via `float(...)` + `round(...,2)` (`auth/service.py:336,344`); the dead Redis event
  also floats the amount. Core tables are Decimal — keep it Decimal to the wire.
  *Effort: 1–2 hours.*
- **M2 — Dashboard "last activity" is wrong.** It's `expense_group.updated_at`, which
  only changes when the group row changes (rename). Adding/confirming expenses doesn't
  touch it, so dashboard ordering and "last_activity" are lies. Either bump the group
  row on expense writes or derive `MAX(expense.updated_at)`. *Effort: 2–3 hours.*
- **M3 — State-changing GETs.** `GET /expense-groups/invite/{token}` joins a group;
  `GET /auth/verify/{token}` creates a user and burns the token; magic-link login GET
  likewise. Email security scanners and link prefetchers issue GETs — they can consume
  magic links before the human clicks (classic magic-link failure) — and REST semantics
  say GET must be safe. Make them POST from the frontend landing page. *Effort: 2–4
  hours across backend+frontend.*
- **M4 — Sentinel-string error contract.** Services return `"CONFLICT"` /
  `"FORBIDDEN"` / `None` (e.g. `settle_expense_split` returns a string against a
  `SettlementClaimPublic` annotation). solution-patterns TEST-003 institutionalized
  this. Replace with typed results or domain exceptions + FastAPI exception handlers;
  update TEST-003 so the anti-pattern stops replicating. *Effort: 0.5–1 day.*
- **M5 — Starter-template residue contradicts the "Walled Garden".** Three coexisting
  registration paths (password `/users/signup`, magic-link `/auth/register`, OAuth),
  password login + recovery for a product that is magic-link/OAuth-only, the `Item`
  model/table still in the production schema, `/private` router, `crud.py`/`models.py`
  compat shims marked "temporary" since Epic 1. Each is attack surface, test burden,
  and confusion for agent-driven development. Decide the supported auth matrix and
  delete the rest. *Effort: 1 day + migration to drop `item`.*
- **M6 — Query hygiene.** `get_pending_confirmations_for_user` does a per-split
  `session.get(Expense)` N+1 (the settlement equivalents already use JOINs — copy
  them); `check_all_splits_confirmed/settled` load full rows where a COUNT suffices;
  audit-log `limit` is uncapped (limit=10^9 is accepted). *Effort: 2–3 hours.*
- **M7 — No logging strategy.** `logging.basicConfig` fires as an import side effect
  of `utils.py`; feature code does ad-hoc `import logging` inside functions; there is
  no request logging, no correlation IDs, no structured format, and Sentry only
  activates outside local. For "agentic" background behavior (Epic 6) observability is
  load-bearing — decide a logging setup in `main.py` now. *Effort: 0.5 day.*
- **M8 — Concurrency unaddressed in money paths.** No row locking or idempotency
  anywhere: double-click settle → the unique index saves the data but the loser gets a
  raw IntegrityError 500 (not the designed 409); two last-member confirms racing can
  both/neither trigger finalize; claim confirm/reject race on the same claim is
  check-then-act. Postgres `SELECT ... FOR UPDATE` on the split/claim rows is enough.
  *Effort: 0.5–1 day.*
- **M9 — `GET /users/{user_id}` returns `None` → 500** when a superuser queries a
  nonexistent id (no 404 guard before the permission branch). *Effort: 15 min.*
- **M10 — Kill one of the twin membership helpers.** `is_user_group_member(session,
  user_id, group_id)` vs `is_group_member(session, group_id, user_id)` (root cause of
  C1). Keep one, keyword-only args (`*, user_id, group_id`). *Effort: 1–2 hours.*
- **M11 — Notifications feature is an unmounted placeholder** — router exists but is
  not included in `api/main.py`; models.py/service.py are comment-only. Harmless today,
  but it means Epic 6 starts from zero despite the directory suggesting otherwise.
  *Effort: n/a (expectation-setting for Session 9 roadmap).*
- **M12 — Read paths that write.** `get_group_personality` creates and commits a
  GroupSettings row inside the parse request; invite-accept commits inside a GET (see
  M3). Keep reads read-only. *Effort: 1 hour.*

---

## 6. LOW Findings

- **L1** — `deps.get_current_user` returns 403 for bad tokens (should be 401 +
  `WWW-Authenticate`), 404 for a deleted user's valid token; status-guard violations
  use 403 where 409 fits better (confirm/reject on finalized expense). API-consistency
  pass recommended.
- **L2** — "Rs" currency hardcoded in **backend** error messages
  (`calculate_unequal_split`) — the same i18n debt as frontend 5.2-L2.
- **L3** — `TokenPayload` has no `type` claim; password-reset JWTs and access JWTs are
  distinguishable only by accident (sub=email vs UUID). Add `type` claims. (Details →
  Session 5.)
- **L4** — Docstring drift: SSE endpoint documents 400s it never returns;
  `reject_settlement_claim` docstring describes status updates that don't happen (H4);
  `ExpenseConfirmRequest` is an empty schema kept only for documentation.
- **L5** — `GroupMemberPublic` exposes every member's email to all group members —
  acceptable now, but flag as a privacy decision (Session 5).
- **L6** — Existing logged LOWs re-confirmed and still valid: 5.2-L1 (mixed import
  styles in expenses router), 4.3-L2 (dead `notify_group_of_finalized_expense` —
  upgraded into H1's deletion recommendation), 5.1-L2 (string amount assertions).
  Debt item 5.1-L1 (migration chain) can be **closed** — chain verified linear, single
  head.

---

## 7. Architecture Conformance (vs architecture.md)

| Decision | Status |
|---|---|
| FastAPI + SQLModel + Postgres | ✅ In place |
| Feature-based directories | ✅ Mostly (dashboard logic lives in auth feature — schemas in `auth/models.py`, queries in `auth/service.py`; belongs in groups or its own feature) |
| Service layer owns DB access | ⚠️ Leaky — expenses router runs its own queries/deletes/commits (split endpoint), groups router commits directly |
| snake_case API JSON | ✅ Consistent |
| RESTful plural hyphenated endpoints | ⚠️ `/expense-groups` ✅, but state-changing GETs (M3) and worklist-style routes deviate |
| Error handling via HTTPException | ⚠️ Contradicted by sentinel-string returns (M4) |
| Redis Pub/Sub + event envelope | ❌ Not implemented; only publisher is dead code with wrong envelope (H1) |
| WebSockets `/ws/*`, `core/socket.py` | ❌ Absent |
| Celery worker | ❌ Absent |
| Offline/mutation-queue support | ❌ Nothing server-side (idempotency keys, sync endpoints) |
| Tests co-located / green | ❌ Central `tests/` dir (fine), but suite cannot run (C3) |
| CI/CD (GitHub Actions) | ❌ None found (Session 6 to confirm) |

The unimplemented half of this table is precisely the half Epic 6+ depends on.
architecture.md should be amended (it also still describes Poetry, Chakra UI, and a
`models/` dir that don't match reality — Session 7 material).

---

## 8. Prioritized Fix List (impact × effort)

**Do immediately (unblocks everything, < 1 day total):**
1. C3 fix #1 — `Optional["GroupSettings"]` annotation → suite runs again.
2. C1 — swap the arguments; add a real SSE-payload assertion.
3. C3 fix #2 — `db_session` → `db` fixture; triage the first honest test run.
4. M9 — 404 guard in `read_user_by_id`.

**This sprint (restores truthfulness of the money paths):**
5. H2 + H3 — expense-edit and reject semantics (one product decision covers both:
   "any change to amount/participants reverts to DRAFT and re-opens consent").
6. H4 — settlement rejection status/response.
7. H5 — one-transaction-per-request refactor; audit entries atomic with operations.
8. C4 — soft-delete users; FK policy migration.
9. H10 — test DB isolation + guard.

**Before Epic 6 starts:**
10. H1 — delete dead event code; explicit build-or-descope decision on Redis/WS/Celery.
11. C2 — API-key + personality write paths **or** managed-key pivot (Session 1 rec).
12. C5 — dedicated encryption key + fail-fast secrets.
13. H7 — ledger read endpoints (also unblocks Session 2's settle-up redesign).
14. H8, H6, H9, M1–M8 as capacity allows — none are safe to carry into a public beta.

---

## 9. Corrections to Prior Session Facts

- Session 1: "BYOK is implemented" → **storage + decrypt-on-read only.** No write path
  (C2), and the parse endpoint that consumes it is broken (C1). Functionally, AI
  parsing has never been usable end-to-end through the API.
- Session 2: "Backend: 125 tests" → 193 test functions exist today; **none can
  execute** (C3), and 12 never could.
- Debt log 5.1-L1 (migration-chain risk) → verified resolved; chain is linear.

## 10. Inputs for Later Sessions

- **Session 4 (frontend):** H7 explains missing group-detail screens; check how the
  frontend consumes the split endpoint's undocumented dict body and untyped OpenAPI.
- **Session 5 (security):** C5 (key derivation, AES claim), M3 (GET side effects),
  L1/L3 (status codes, token typing), JWT-in-URL on OAuth callback
  (`auth/router.py:734`), `str(e)` leaked into OAuth error redirects, password-recovery
  endpoint's 404 enumeration vs magic-link's anti-enumeration, 8-day/30-day
  non-revocable JWTs, member email exposure (L5).
- **Session 6 (infra):** no CI found in-tree; test-DB isolation (H10); redis/celery
  absent from dependencies (H1); Sentry gating.
- **Session 7 (docs):** architecture.md drift (Section 7); docstring/API doc lies (L4).
- **Session 9 (synthesis):** the pattern across C1/C2/C3/H1 is one meta-finding —
  **features are being declared done without an executable definition of done.** The
  single highest-leverage process fix is a green-suite CI gate; the single highest-
  leverage product fix remains Session 2's re-sequenced roadmap, now with a
  "backend-integrity hardening" workstream (Section 8) inserted before any beta.
