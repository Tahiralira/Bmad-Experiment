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

- [x] **WS4 — Ledger Integrity (backend)** (≈1 week; done in 1 session)
      Goal: the ledger becomes trustworthy — the whole game for this product.
      Depends on: WS1.
      Inputs: 03 §3–§5 (C4, H2, H3, H4, H5, M1, M8, M9, M10).
      Tasks:
      - [x] Product decision implemented: "any change to amount/participants reverts
            the expense to DRAFT and re-opens consent" — fixes expense-edit orphaning
            (H2) and replaces reject-redistribution with reject→DRAFT + notify (H3).
            Consent fields = amount + payer_id; description-only edits don't revert.
            All splits are deleted on revert (audit records before/after status).
            "Notify creator" = status change + audit entry until WS12's nudge infra.
      - [x] Settlement rejection sets REJECTED status + `rejected_at` truthfully (H4)
            — set on the claim before the response is built; delete-to-allow-reclaim
            kept (REJECTED persists in the audit log by design, per 03 §4)
      - [x] One-transaction-per-request refactor; audit entries atomic with their
            operations (H5); canonical pattern → solution-patterns.yaml **ARCH-001**
            (services flush, routers commit once; record_audit no longer swallows
            errors — an operation without its audit row can't persist)
      - [x] Soft-delete/anonymize users; FK policy migration; block hard delete with
            unsettled shared splits (C4) — DELETE /users/me and admin DELETE
            /users/{id} both: 409 while unsettled, else anonymize (PII scrub, OAuth
            ids cleared, magic-link tokens invalidated, is_active=False,
            deleted_at). Migration b8c9d0e1f2a3: user.deleted_at +
            expense.payer_id/created_by + expense_split.user_id CASCADE→RESTRICT.
      - [x] Row locking / idempotency on settle+confirm paths (M8) — FOR UPDATE on
            expense row (confirm/reject/split-edit), split row (settle), claim→split
            →expense (claim confirm/reject, fixed lock order); IntegrityError on
            double-claim → 409 not 500. Decimal to the wire on dashboard balances
            (M1) — net_balance/total_balance now exact decimal strings; frontend
            dashboard types updated. 404 guard in `read_user_by_id` (M9).
      - [x] Kill one of the twin membership helpers; keyword-only args (M10) —
            `expenses.service.is_user_group_member` deleted; all call sites use
            `groups.service.is_group_member(session, *, group_id, user_id)`.
      - [x] Tests for every fix — 11 new tests in
            `tests/api/routes/test_ledger_integrity.py` (H2×4, H3×2, H5 atomicity
            via rollback probe, C4×2 incl. DB-level RESTRICT probe, M9, M1 exact
            "50.00"/"-50.00" assertions); H4 assertions added to test_settlement;
            5 existing tests updated to the new soft-delete/Decimal contracts.
      Verification: DONE 2026-07-09 — **backend 203 passed / 2 skipped** (was 192);
      frontend typecheck green, 83 passed / 1 expected-fail / 2 skipped, build green
      (main chunk unchanged 170.6 kB gz); migration applied to dev DB and verified
      (FKs confdeltype='r'); live health-check + /docs 200 after upgrade.
      Notes / deviations:
      - B-C1 (AI parse swapped args) got mechanically fixed by the M10 refactor —
        writing `user_id=group_id` keyword args deliberately would have been
        absurd. WS7 still owes the real SSE-payload test; the 2 skipped AI router
        tests stay skipped until then.
      - Anonymized email domain must dodge email-validator's special-use list
        (.invalid/.test reject → response 500s); used
        `deleted-{id}@anonymized.example.com`.
      - Admin DELETE /users/{id} (template endpoint, dies in WS8) routed through
        the same soft-delete path rather than left as a hard-delete hole.
      Status: DONE 2026-07-09 (branch ws4/ledger-integrity)

- [x] **WS5 — Ledger API + Group Screen** (≈1 week; done in 1 session)
      Goal: the app can display what it stores; the core loop becomes operable.
      Depends on: WS4 (service-layer semantics settled). Styling: use existing
      components; WS3 restyles globally via tokens.
      Inputs: 03 (H7, H6, H9, M2, M6), 04 (C1, C4, H1, H3, M6, M1, M2).
      Tasks:
      - [x] Backend read endpoints: GET /expenses/{id}, GET /expense-groups/{id}
            (member_count + user's net_balance), GET /expense-groups/{id}/expenses
            (ledger with the caller's own split LEFT-JOINed per row), GET
            /expenses/{id}/splits (with names); `?group_id=` scope on
            settlement-claims/pending-for-owner (B-H7, S4-M6). B-M6 folded in:
            pending-confirmations N+1 → JOIN; audit-log/ledger limits capped
            via Query(ge/le).
      - [x] Split endpoint: discriminated-union `SplitRequest` (Literal type
            discriminator) replaces the raw `dict`; validation + calculation +
            persistence live in one `apply_split()` service function; malformed
            bodies (bad UUIDs, unknown types) 422 instead of 500 (B-H6)
      - [x] Alembic reconciled (B-H9): env.py already saw all models via the WS1
            app.models shim — the real work was making models render the exact
            migration DDL (sa_type aware timestamps, sa.Enum(native_enum=False,
            length) since enum columns store NAMES, Field(ondelete=...) matching
            FK policy, oauth composite index, named unique constraint) +
            migration c4d5e6f7a8b9 converting the stray naive columns
            (audit_log, settlement_claim, expense.confirmed_at,
            user.created_at/updated_at) and pinning unbounded status VARCHARs.
            **`alembic check` is clean for the first time**; downgrade exercised.
      - [x] `/groups/$groupId` route (file `groups_.$groupId.tsx` — trailing
            underscore un-nests since the list route has no Outlet); detail from
            query cache; dashboard + groups list link to it (S4-H3). Dashboard
            last_activity = max(group.updated_at, MAX(expense.updated_at)),
            ordering follows it (B-M2).
      - [x] GroupLedgerScreen: balance hero, expense ledger with expandable rows
            (splits + per-expense AuditLogList audit trail), ConfirmedExpenseCard
            "Mark Paid" section, PendingSettlementsList + SettlementClaimsList
            (both group-scoped), MembersList, ActivityFeed (S4-C4). GroupDetail
            panel deleted.
      - [x] Expense entry wired (S4-C1): per-group Add-expense button threads
            groupId; global FAB gains a group selector; submit disabled until a
            group is chosen (was a silent no-op); `"user-123"` replaced with the
            real auth-context user id.
      - [x] Global handler: logout on 401 only, router.navigate not hard
            redirect; 403 → toast with server detail (query cache only —
            mutations already toast) (S4-H1)
      - [x] Split-math fixes: payer absorbs rounding regardless of position
            (S4-M1 `it.fails` flipped to a real pass); unequal validation
            requires an amount for every INCLUDED member + stale excluded
            entries filtered from submissions (S4-M2)
      Verification: DONE 2026-07-10 —
      **Core loop proven in the browser end-to-end:** create (smart-input UI,
      real payer) → equal split (complex-mode UI) → member confirm (API) +
      owner confirm (/pending UI) → CONFIRMED with exact balances ("You are
      owed 30 rupees" from the new detail endpoint) → member claims (API) →
      owner confirms claim on the group screen → SETTLED badge, "All settled"
      state; expanded row shows both splits + 8-entry audit history.
      **Gates:** backend **210 passed / 2 skipped** (was 203; 8 new WS5 tests
      in test_ledger_api.py + 422 split contract tests); frontend typecheck
      green, **88 passed / 2 skipped** (S4-M1 expected-fail now passes; 4 new
      tests), build green — main chunk **172.3 kB gz** (budget ≤250).
      **Screenshots:** group ledger screen at 375px + 1280px in dark AND light,
      dashboard 375px dark, smart-input modal (group-screen entry + FAB entry
      with group selector) — captured via preview browser during the live run.
      Notes / deviations:
      - Decimal-to-the-wire (WS4/M1) was already the API's real behavior for
        expense/split/claim amounts — the frontend types said `number` and the
        `.toFixed()` consumers were unmounted dead code that would have crashed
        on first render. Types are now `string` and the four consumer cards
        fixed; caught only because WS5 mounts them.
      - "user-123" deletion pulled forward from WS7: entry wiring is unusable
        without a real payer UUID (confirm would 422 every time). The
        setTimeout mock parse itself stays for WS7 as planned.
      - Unknown split type now 422s (schema) instead of the hand-rolled 400;
        one test updated to the new contract.
      - a11y: SmartInputModal heading became a real Radix DialogTitle (console
        error found during browser verification).
      Status: DONE 2026-07-10 (branch ws5/ledger-api, 3 commits)

- [x] **WS6 — Aggregate Settle-Up + Confirmation Policy** (≈4–5 days; done in 1 session)
      Goal: settlement matches human behavior; the friction ceremonies become opt-in.
      Depends on: WS5.
      Inputs: 02 §4, 09 §5 (strict mode, auto-confirm), 03 (settlement schema notes).
      Tasks:
      - [x] Aggregate settle-up: "Settle with X" nets all confirmed expenses between
            the pair in a group → one claim → one confirmation → covered splits
            settled atomically, one audit fan-out; per-expense path kept for partial
            payments. Schema: SettlementClaim.expense_split_id nullable + group_id/
            counterparty_user_id; settlement_claim_split link table (UNIQUE per
            split = the two-claims-race guard → 409). Netting covers BOTH
            directions (net can be 0.00 — clears an even pair); wrong-direction
            claims 400 ("they should settle up with you"). Per-expense settle on a
            covered split 409s and vice versa (excluded from netting). Migration
            d5e6f7a8b9c0; `alembic check` still clean; downgrade exercised.
      - [x] Settlement auto-confirm after 72h with owner dispute window — lazy
            sweeps on every claim-surfacing read/write path (commit-if-swept;
            WS12's scheduler takes this over); reject after the window closes
            confirms instead + 409 with the dispute-window message;
            auto_confirm_at on the wire so the UI shows "auto-confirms in 2 days".
      - [x] Per-group "strict mode" toggle (GroupSettings.strict_mode, default
            OFF): confirmation opt-in — expenses auto-confirm 3 days after splits
            are assigned (EXPENSE_AUTO_CONFIRM_DAYS; re-split restarts the
            window); members can still confirm early or reject (reject → DRAFT
            unchanged). GET/PATCH /expense-groups/{id}/settings (PATCH
            owner-only, 403 for members); toggle UI in the group screen with
            member-visible read-only state.
      - [x] Pairwise balance detail view (S2-F9): GET /expense-groups/{id}/
            pairwise-balances (per-counterparty they_owe_you / you_owe_them /
            net, Decimal strings); "Between you and…" section on the group
            screen with two-step inline "Settle up" confirm (manual only),
            in-flight "Settle-up pending" state, AggregateClaimCard for both
            roles (reviewer Confirm/Reject + countdown; claimant waiting).
      Verification: DONE 2026-07-13 —
      **12-expense scenario proven in the browser end-to-end:** Sam owed Alex
      across 12 confirmed expenses (Rs 600) → pairwise row "You owe Rs 600.00"
      → ONE settle-up (claim covers 12 splits/12 expenses) → Alex sees ONE
      review card → ONE confirm → all 12 expenses SETTLED, balances Rs 0 both
      sides, 12-entry audit fan-out in the activity feed. Strict-mode toggle
      exercised live (PATCH 200, copy flips). Same scenario + netting math,
      dispute window, and strict mode covered by tests.
      **Gates:** backend **232 passed / 2 skipped** (was 210; 22 new tests in
      test_settle_up.py); frontend typecheck green, **98 passed / 2 skipped**
      (10 new), build green — main chunk **172.9 kB gz** (budget ≤250);
      `uv lock --check` passes.
      **Screenshots:** 8 shots (pairwise-owes, settle-up pending, review card,
      all-settled × 375px/1280px × light/dark) →
      `_bmad-output/implementation-artifacts/ws6-screenshots/`.
      Notes / deviations:
      - "Ready to settle" per-expense cards now hide while a settle-up with
        that payer is pending (Mark Paid would always 409 — don't offer it).
      - Confirm/reject endpoints are shared between claim shapes; the service
        branches on expense_split_id IS NULL. Lock order claim → splits (id
        order) → expenses (id order) keeps WS4/M8 discipline.
      - Balances still count splits with in-flight claims as owed (consistent
        with the dashboard); only confirmation settles them.
      - No Celery yet by design: auto-confirm is lazy-swept on reads. The
        sweep commits on read endpoints only when it changed rows.
      Status: DONE 2026-07-13 (branch ws6/settle-up)

- [x] **WS7 — Real AI Path (hosted-first)** (≈1 week; done in 1 session)
      Goal: FR1 exists for the first time; the premium gate exists.
      Depends on: WS5 (expense create path works).
      Inputs: 03 (C1, C2, C5, H8), 04 (C2), 01 §6 (hosted-AI model), 05 (C1 key notes).
      Tasks:
      - [x] B-C1 was already mechanically fixed by WS4's keyword-only helper;
            this session added what actually catches it: a real SSE-payload
            test with real group membership asserting the `complete` event
            (amount/description/payer/confidence). The 2 skipped tests are
            rewritten; test_ai_parsing.py 10 → 37 tests, 0 skips.
      - [x] Hosted AI default: `GEMINI_API_KEY` setting; resolution
            `user_key if set else server_key` (neither → 503); per-user
            monthly quota — `ai_usage` table (UNIQUE user+period, FOR UPDATE
            + IntegrityError-race fallback), `AI_FREE_MONTHLY_PARSES=20`,
            429 with mediator-voice copy when exhausted; BYOK exempt
      - [x] BYOK demoted: `PUT/DELETE /users/me/api-key` (min-length 422,
            encrypted at rest, never returned, quota bypass); no onboarding
            UI by design — endpoints only until a power-user settings screen
      - [x] Dedicated `ENCRYPTION_KEY` (fail-fast validator outside local;
            "changethis" guard) + HKDF-SHA256 derivation with domain-separated
            salt/info; false "AES-256" claims corrected (Fernet = AES-128-CBC
            + HMAC); migration plan: NONE NEEDED — B-C2 proved no write path
            ever shipped, so no real key was ever stored under the old scheme
      - [x] Async Gemini (`client.aio`) + `AI_PARSE_TIMEOUT_SECONDS=30` via
            HttpOptions; `response_mime_type: application/json` on the parse
            call (+ code-fence tolerance); commentary chunked by WORD; honest
            error contract: pre-stream failures are real HTTP codes
            (403/422/429/503), mid-stream failures are `error` events on a
            200 — docstring now says exactly that (B-H8)
      - [x] Frontend: `api/parse.ts` fetch-stream SSE client (EventSource
            can't POST) with buffered frame parsing + AbortController;
            setTimeout mock deleted; error/low-confidence states show the
            server's mediator-voice message (`role="alert"`); dead
            useStreamingText + useAutoConfirm hooks deleted with their tests
      - [x] Manual confirm only (UX-H6): auto-confirm countdown machinery
            removed end-to-end (EditableExpensePreview / ExpensePreviewCard
            props gone) — financial records never commit on a timer
      - [x] `ai_personality` write path: folded into WS6's
            PATCH /expense-groups/{id}/settings (owner-only, partial
            updates); Literal-capped at professional/friendly/funny — f3-pbs
            REMOVED from the enum and prompts (UX-H5), stored unknowns fall
            back to friendly; "Mediator tone" select in group settings UI
            (member-visible, owner-editable) — Epic 8.1 effectively shipped
      Verification: DONE 2026-07-14 —
      **Full flow in the browser:** typed "Paid 450 for biryani lunch with
      the team" → SSE commentary streamed into the bubble → Review Expense
      preview (450 / "Biryani lunch with the team" / real payer) → manual
      Confirm → expense in the group ledger (Rs 450.00, Draft) + activity
      feed entry. Low-confidence sentence → mediator error card. NOTE: run
      against a local Gemini-wire-compatible fake (`GEMINI_BASE_URL`) because
      no real GEMINI_API_KEY exists in this environment — the entire
      HTTP/SSE/parse/quota path is real; putting a key in .env is the only
      step left for live Gemini.
      **Gates:** backend **259 passed / 0 skipped** (was 232/2 — first
      zero-skip run); frontend typecheck green, **86 passed** (98 → 86: 14
      dead-hook tests deleted, 7 added), build green — main chunk
      **172.5 kB gz** (budget ≤250); `uv lock --check` passes; migration
      af5ea3c202c0 applied, `alembic check` clean, downgrade exercised.
      **Screenshots:** 7 shots (smart-input parsed × 375/1280 × light/dark,
      group screen w/ Mediator tone × 2, parse-error 375) →
      `_bmad-output/implementation-artifacts/ws7-screenshots/`.
      Notes / deviations:
      - FOUND+FIXED during verification: modal content taller than its
        `max-h-[80vh]` had no `overflow-y-auto` — Confirm was unreachable on
        short viewports once real commentary+preview filled the modal.
      - `session.commit()` happens in the router BEFORE streaming starts
        (quota unit + lazy settings row) — once SSE begins there is no
        "after" to commit in; ARCH-001's one-commit rule is kept with the
        commit relocated, documented in the router.
      - Gotcha for future SSE endpoints: the response generator runs AFTER
        the session dependency tears down — snapshot ORM values (payer_id)
        before returning StreamingResponse, or the expired instance raises
        mid-stream (surfaced as a phantom generic error event).
      - Frontend `ExpenseParseResponse.amount` stays `number` (edit-buffer
        type); the wire's Decimal string is converted once in parse.ts.
      Status: DONE 2026-07-14 (branch ws7/real-ai)

### PHASE 2 — Launch Blockers

- [x] **WS8 — Template Purge & Security Hardening** (≈1 week; done in 1 session)
      Goal: attack surface halved; secrets and deps stop being landmines.
      Depends on: WS1; ideally after WS3 (so deletions don't collide with restyling).
      Inputs: 05 (all C/H/M items), 04 (H2, M8), 06 (H1).
      Tasks:
      - [x] Delete the parallel password-auth stack: /signup, /login/access-token,
            /login/test-token, /password-recovery, /reset-password (+HTML variant),
            /users/me/password, /private, superuser user CRUD (list/create/patch/
            delete/read-by-id), ChangePassword UI, /admin, /items, Pending/DataTable
            components + `Item` model/table migration, reset/new-account email
            templates, password-reset JWT helpers (S5-H5, S4-H2). Test fixtures now
            mint JWTs directly — no password endpoint to round-trip through.
      - [x] OAuth token delivery (S5-H1): callback redirects with a 2-minute
            SINGLE-USE code (SHA-256 at rest, FOR UPDATE consume) →
            `POST /auth/oauth/exchange` returns the JWT in the response body —
            tokens never ride URLs. Lifetime 30d → 14d (PRD deviation, documented:
            revocable tokens halve the blast radius). Every JWT carries a `jti`;
            `revoked_token` table + `POST /auth/logout` = real server-side logout
            (frontend logout fires it, fire-and-forget); jti-less legacy tokens
            rejected outright.
      - [x] Rate limiting (S5-H2): slowapi per-IP — 10/min auth tier (magic-link
            request/verify, oauth login/callback/exchange), 20/min AI parse,
            200/min global default via middleware; mediator-voice 429. In-memory
            per worker (≤4× configured) — Redis backend arrives with WS12 infra.
      - [x] Security headers (S5-M1, M6): API middleware (nosniff, X-Frame-Options
            DENY, Referrer-Policy no-referrer, CSP default-src 'none' except /docs,
            HSTS outside local) + nginx.conf for the SPA (self-hosted CSP,
            frame-ancestors 'none', HSTS); `allow_credentials=False`.
      - [x] Google OIDC: login/linking rejected unless `email_verified is True`
            → generic `email_unverified` redirect code (S5-M3)
      - [x] Invite accept → POST from a landing page (S5-M4): GET /invite/{token}
            is now a read-only PREVIEW (group name/member count/already-member);
            joining is `POST .../accept` behind an explicit "Join <group>" button.
            max_uses cap (default 10, 1–100 at creation, locked increment —
            already-member consumes no use), owner revocation
            (DELETE /{group}/invites/{id}) + owner list endpoint; revoke button in
            the invite UI.
      - [x] Deps (S5-C2/H4/M7, S6-H1): relock — starlette 0.38.6 → 1.3.1
            (CVE-2024-47874 cleared), fastapi 0.139, sentry-sdk 2.65
            (`send_default_pii=False`), authlib floor ≥1.3.1 (1.7.2 locked),
            slowapi added; BOTH Dockerfile syncs `--locked` (build now fails on
            lock drift instead of silently re-resolving).
      - [x] OAuth error redirect: generic `?error=<code>` only; `str(e)` goes to
            the server log (S5-M2); frontend maps codes to mediator copy
      - [x] Mediator-voice error mapper (UX-H4, S4-M4): `getApiErrorMessage` —
            server `detail` passes through untouched, transport failures become
            calm copy (no raw "Network Error"); `handleError.bind` contortion
            removed (S4-L2); calm error-toast title
      Verification: DONE 2026-07-15 —
      **Gates:** backend **249 passed / 0 failed / 0 skipped** (14 new WS8
      security tests; count down from 259 because ~24 template-endpoint tests
      died with their endpoints); frontend typecheck green, **86 passed**,
      build green — main chunk **169.2 kB gz** (was 172.5; budget ≤250);
      `uv lock --check` passes; migration b2c3d4e5f6a7 applied, `alembic check`
      clean, downgrade exercised.
      **Live API proof:** all six template routes 404; security headers on every
      response; rate limiter allows exactly 10 auth-tier hits then 429s with
      mediator copy (curl, real container).
      **Browser proof (Playwright, 13/13):** invite landing preview → explicit
      Join POST → lands inside the group screen; already-member state; /signup,
      /recover-password, /admin, /items dead in the SPA; Settings has no
      Password tab (title now "Settings - ClearDues"); OAuth error codes render
      mediator copy. **Screenshots:** 8 shots (invite landing 375-dark +
      1280-light, group-after-join, already-member, settings ×2, template-404,
      oauth-error) → `_bmad-output/implementation-artifacts/ws8-screenshots/`.
      Notes / deviations:
      - LOGIN_TOKEN_EXPIRE_DAYS 30 → 14 deviates from the PRD's "Walled
        Garden"; justified by revocation existing now. Revisit if beta users
        complain about re-auth frequency.
      - Existing pre-WS8 sessions are invalidated (tokens lack jti) — acceptable
        pre-beta, zero real users.
      - OAuth one-time-code flow proven via mocked provider (tests) + error-path
        browser check; full live-Google pass needs real client creds (WS9
        staging).
      - Invite GET→preview is a trap for old tests: they still got 200 (preview)
        but nobody joined — converted 8 helper call sites to POST /accept.
      - Browser-pane clicks/screenshots hung against the Vite dev server;
        Playwright fallback used per the WS3 learning. New wrinkle: on cold dev
        loads the theme class applies late — wait for body backgroundColor
        before screenshotting.
      - Adminer removal + env_file scoping stay WS9 scope (S5-H3, S6-M1), as
        planned. Generated client still ships dead template services — WS11
        owns the client decision (S7-M3).
      Status: DONE 2026-07-15 (branch ws8/template-purge)

- [x] **WS9 — Deploy & Ops** (≈1 week; done in 1 session — staging deploy itself
      awaits user-provisioned VPS, see notes)
      Goal: a deployable, backed-up, monitored stack.
      Depends on: WS1 (CI), WS8 (image/deps hardening overlaps).
      Inputs: 06 (entire Recommended Path), 05 (H3).
      Tasks:
      - [x] Commit to compose-on-VPS for beta; delete the Swarm script and the
            Railway claims from planning docs (S6-C3) — deploy.sh (Swarm) +
            build.sh/build-push.sh (docker-compose v1) deleted; Railway claims
            replaced with the decision in architecture.md (6 sites), epics.md,
            CLAUDE.md, session-context.md
      - [x] Extract `cleardues/` to its own repository; rotate the PAT; credential
            helper (S6-M4, M3) — extraction DRILLED (subtree split, 55 commits
            preserved, verified, drill branch removed); copier machinery +
            fastapi-org community files deleted (cleardues/.github FUNDING/
            ISSUE_TEMPLATE/DISCUSSION_TEMPLATE/labeler, .copier/, hooks/,
            copier.yml). Final push + PAT rotation + remote repoint are OWNER
            ACTIONS (deployment.md §7): repointing the remote was blocked by the
            session permission layer, and gh CLI is authenticated to a different
            account — nothing I can rotate from here.
      - [x] Nightly `pg_dump` + one **tested** restore; pre-migration dump gating
            prestart (S6-C2, M5) — custom 80-line sidecar on postgres:17 (no
            third-party image holding DB creds; pg_dump always matches server):
            `db-backup` daemon (03:00 UTC, 14-day retention) + `pre-migrate-dump`
            one-shot wired db→dump→prestart→backend so migrations NEVER run
            without a fresh dump (a failed dump fails the deploy). Offsite = host
            rclone cron documented in the runbook (object storage is per-VPS).
      - [x] Image hardening (S6-H4): backend python:3.10-full → 3.13-slim
            (1.98 GB → 464 MB), non-root USER app, tests/ + dev deps out of prod
            (INSTALL_DEV build arg; override mounts tests + installs dev deps so
            `docker compose exec backend pytest` still works), healthcheck
            curl → python urllib (slim has no curl); frontend `npm ci`,
            nginx:1 → 1.27-alpine (226 MB → 75 MB), gzip + immutable /assets
            caching + no-cache index (via `expires` so WS8 security headers keep
            inheriting); memory limits on every service; CI UV_PYTHON 3.10 → 3.13
      - [x] Remove Adminer from prod compose (kept in override for local dev);
            env_file scoped — db + playwright no longer receive the full .env
            (S5-H3, S6-M1)
      - [x] Log rotation json-file 10m×3 on all services + Traefik; uptime
            monitor documented as a day-one runbook step (external account —
            can't be created from here) (S6-H3)
      - [x] ClearDues runbook written — deployment.md fully replaced (provision,
            DNS, Traefik bootstrap, secrets checklist incl. ENCRYPTION_KEY
            bricking warning, deploy, rollback incl. restore-from-pre-migrate-
            dump, backups + offsite, quarterly restore drill, monitoring, owner
            to-dos). Staging deploy NOT executed: no VPS/domain exists in this
            environment — runbook §1–3 is the exact procedure (S6-M2)
      Verification: DONE 2026-07-16 (except live-staging items, see notes) —
      **Backend suite on the hardened 3.13 image: 249 passed / 0 failed /
      0 skipped** (2 template pre-start tests were DOUBLY fake — misspelled
      `.called_once_with` non-assertion + patching "sqlmodel.Session" which the
      code never looks up; py3.13 exposed them, both rewritten to assert for
      real). Frontend typecheck green, **86 passed**, build green — main chunk
      **169.9 kB gz** (budget ≤250). `uv lock --check` passes after the 3.13
      relock (httptools/uvloop/uvicorn/watchfiles/websockets — locked versions
      predated cp313 wheels; gcc-on-slim build failure fixed the right way).
      **Live local proof of the prod topology:** `docker compose up` ran
      db → pre-migrate-dump (84 KB dump written) → prestart → backend healthy
      under the new python-urllib healthcheck, as user `app` on Python 3.13.14;
      nightly daemon scheduled ("nightly backups at 03:00 UTC, keeping 14
      days"); **restore drill EXECUTED**: pg_restore of the pre-migrate dump
      into restore_drill matched live counts exactly (12 users / 15 expenses /
      28 splits / 97 audit rows), manual-dump command proven, scratch DB
      dropped. Prod compose config validates; prod backend image: whoami=app,
      no /app/tests, pytest absent, `import app.main` OK. Prod frontend
      container curl-proven: `/` no-cache + all WS8 security headers,
      `/assets/*.js` gzip + max-age=31536000, headers intact on both.
      Notes / deviations:
      - REMAINING FOR OWNER (all documented in deployment.md §7 + §1–3, §6):
        (1) provision VPS + domain and run the runbook — "reachable over TLS"
        and "uptime alert fires" are unverifiable without them; (2) rotate the
        exposed PAT and re-point the remote (permission layer correctly blocked
        me from changing where pushes go); (3) create the new GitHub repo and
        push the drilled extraction; (4) create the uptime monitor.
      - Restore-drill runbook snippet initially failed in the drill itself
        (psql reads PGPASSWORD, not POSTGRES_PASSWORD) — fixed in the runbook;
        this is exactly why the drill is a task and not a doc.
      - pre-migrate-dump also runs on local `up` (~1s) — deliberate: the
        backup path gets exercised on every developer boot.
      - S6-L2 remainder (pre-commit `language: unsupported`, test-local.sh on
        docker-compose v1) logged as WS9-L1 in technical-debt-log; WS11 owns.
      - Sentry SDK 2.x was already done in WS8; S6-H3's Sentry item needed no
        work here.
      Status: DONE 2026-07-16 (branch ws9/deploy-ops; staging execution = owner
      runbook items above)

- [x] **WS9.5 — Replatform to Vercel + Render + Neon** (unplanned session,
      2026-07-16; owner decision same day supersedes WS9's compose-on-VPS)
      Goal: free-tier PaaS deployment prepped so a first-time deployer can go
      live in ~45 min. Owner chose Vercel (SPA) / Render (API) / Neon
      (Postgres) / cleardues.site purely for free tiers; Neon picked over
      Supabase (no 7-day pause, instant scale-to-zero resume, ~6h restore
      window on free). Repo extraction DEFERRED by owner decision — WS1's
      root CI + both platforms' monorepo Root Directory support make nesting
      harmless for now; revisit at WS11/WS13 (extraction stays drilled).
      Tasks:
      - [x] `frontend/vercel.json` — SPA rewrite + WS8 security
            headers ported from nginx.conf + immutable /assets + no-cache HTML
      - [x] `render.yaml` blueprint (repo root): python runtime + uv
            (auto-detected via uv.lock in rootDir backend), free
            plan, startup migrations (free tier has no preDeployCommand),
            health-check path, buildFilters, generateValue secrets
            (SECRET_KEY/ENCRYPTION_KEY), sync:false prompts for the rest
      - [x] Neon-ready backend: `pool_pre_ping` on the engine (scale-to-zero
            drops idle conns) + `POSTGRES_SSLMODE` setting appended to the
            DSN query (empty = local DSN byte-identical; 2 new tests)
      - [x] `.github/workflows/db-backup.yml`: nightly 03:00 UTC pg_dump of
            Neon (PGDG client 17), 30-day private artifacts, manual-run
            testable; Neon free keeps only ~6h history so this IS the backup
            (S6-C2 continuity). NOTE: cron fires only from the default
            branch — deploy prerequisite is merging to main.
      - [x] deployment.md rewritten as a first-time-deployer walkthrough
            (Neon → Render blueprint → Vercel import → DNS for
            cleardues.site → Google OAuth console → backup secret + restore
            drill → verify checklist → paid-upgrade triggers →
            troubleshooting); WS9 VPS runbook preserved as
            deployment-vps.md (fallback, marked superseded)
      - [x] Plan-of-record updated (architecture.md, CLAUDE.md, this file,
            session-context, memory)
      Verification: backend suite green incl. 2 new config tests (see WS9.5
      notes in session-context); render.yaml/vercel.json/workflow validated;
      Render start command exercised in the local 3.13 container. Live
      Vercel/Render/Neon wiring is owner-executed by design (accounts are
      theirs) — deployment.md §7 is the acceptance checklist.
      Notes:
      - Vercel Hobby is licensed non-commercial; monetization TESTING on it
        is warn-first risk in practice (Vercel says it notifies before
        acting but reserves no-notice takedown). Trigger table in
        deployment.md §8: real charges → Vercel Pro or Cloudflare Pages.
      - SMTP intentionally deferred: first login path is Google OAuth;
        magic-link email needs an SMTP provider env-var drop later.
      Status: DONE 2026-07-16 (branch ws9.5/replatform)

- [x] **WS9.6 — Repo flatten & cleanup** (unplanned session, 2026-07-16;
      supersedes WS9.5's "nesting is harmless" call — Vercel's root-directory
      picker in practice only descends one level, so `cleardues/frontend` was
      unselectable)
      Goal: pre-merge-to-main cleanup; `backend/` and `frontend/` selectable
      by PaaS root-directory pickers.
      Tasks:
      - [x] Flattened: everything under `cleardues/` git-mv'd to the repo
            root (306 tracked renames); `cleardues/` is gone. S6-M4's
            "extract to own repo" is now equivalent to just pushing this
            repo to a new remote (deployment-vps.md §7 updated).
      - [x] RESCUED FILES the old root .gitignore silently excluded from git
            (CI never caught it — it only runs on main/PRs, and neither had
            happened since the files appeared): `frontend/package.json`
            (bare `package.json` ignore line!), `frontend/src/lib/utils.ts`
            (bare `lib/`), `backend/app/email-templates/build/*.html` (bare
            `build/`). A fresh clone could not build the frontend at all.
      - [x] .gitignore rewritten: the two .gitignores merged at root, broad
            Python-template patterns (`lib/`, `build/`, `dist/`,
            `package.json`) removed or anchored (`/frontend/dist/`)
      - [x] Junk deleted: `nul` ×2, `temp.py` (S6-L3); foreign-tool configs
            removed from tracking (`.kilocodemodes`, `.github/agents/` —
            BMAD-generated for Kilo Code / GitHub Copilot, unused,
            recoverable from git history)
      - [x] `name: cleardues` pinned in docker-compose.yml — the project
            name used to come from the `cleardues/` folder name; pinning
            preserves the existing app-db-data volume and container names
      - [x] Path-reference sweep: `cleardues/<x>` → `<x>` across CLAUDE.md,
            ci.yml, db-backup.yml, render.yaml (rootDir/buildFilters →
            `backend`), deployment.md (Vercel Root Directory → `frontend`),
            deployment-vps.md, trackers, and story/planning artifacts.
            Product-review docs 00–09 keep their historical `cleardues/`
            narrative where it *describes* the old layout (findings are
            point-in-time records).
      Verification: backend 251 passed (after `docker compose build backend`
      — see solution-patterns: tests are volume-mounted but app code runs
      from the image); frontend typecheck + 86 tests + build green; compose
      stack restarted from the new root and healthy.
      Status: DONE 2026-07-16 (branch ws9.6/repo-restructure)

- [ ] **WS10 — Growth Wiring & Analytics** (≈1 week — SPLIT into atomic
      sub-sessions WS10.1–WS10.7, owner decision 2026-07-20: run one task per
      conversation so none bloats; see per-sub-session status below)
      Goal: the beta can convert, retain, and be measured — globally.
      Depends on: WS5, WS6; WS9 for PostHog hosting.
      Inputs: 02 (F1, F7, §6, §9), 09 §6 (global-market requirements, monetization).

    - [x] **WS10.1 — Currency Foundation** (this is the market-global money layer
          the settle UI / payments / onboarding all render through — done FIRST)
          Depends on: WS5, WS6.
          - [x] `formatCurrency(amount, currency, {signed, locale})` util +
                `getCurrencySymbol` + `guessLocaleCurrency` (region→currency) in
                `frontend/src/lib/currency.ts`; `Intl.NumberFormat` (per-currency
                decimals — JPY 0, most 2); tolerates Decimal-string wire amounts and
                falls back to USD/0 rather than throwing in render
          - [x] `GroupSettings.currency` (ISO-4217, default USD, locale-guess seeded
                at group create via `ExpenseGroupCreate.currency`) + migration
                `c1d2e3f4a5b6`; GET/PATCH settings expose+validate it (422 on unknown,
                case-insensitive). Backend `app/core/currency.py` curated ~46-code
                supported set (global, mirrored to a frontend constant)
          - [x] Purged all 16 "Rs" hardcodes + a stray `$` in inline-input; threaded
                currency via a `CurrencyProvider`/`useCurrency` context for the
                single-currency group subtree (GroupLedgerScreen + SmartInputModal),
                explicit per-item currency for cross-group surfaces (dashboard rows,
                /pending). Dashboard aggregate hero hides when groups span currencies
                (`DashboardResponse.currency` null) — summing across currencies is
                meaningless
          - [x] Currency picker in group settings (owner-editable) + create-group
                (locale-detected default)
          Verification: DONE 2026-07-20 — **backend 258 passed / 0 failed / 0
          skipped** (was 251; +7 currency tests: create default/with/unknown,
          detail, settings case-insensitive update, 422 reject, dashboard
          shared-vs-mixed); `alembic check` clean; frontend typecheck green,
          **94 passed** (+8 formatCurrency unit tests), build green — main chunk
          **170.16 kB gz** (budget ≤250). Live backend proof: `GET
          /expense-groups/{id}` → 200 `"currency":"EUR"` after a settings PATCH.
          Live frontend proof: create-group currency picker renders the full
          ISO-4217 list with the locale-detected default (USD) selected (browser
          read_page against the nginx build).
          NOTE: full-app pixel screenshots not captured — the browser-pane
          screenshot tool hangs against this project (documented WS3+ limitation)
          and direct :5173→:8000 access is CORS-blocked; Playwright is the
          established fallback (WS3/WS8) if pixel proof is required before merge.
          Status: DONE 2026-07-20 (branch ws10.1/currency)

    - [x] **WS10.2 — Payment Links Registry + Universal Mark-as-Paid**
          Depends on: WS6, WS10.1. Owner: per-user GLOBAL handles; cover major
          providers (Venmo, PayPal.Me, Cash App, Revolut, UPI, IBAN-copy) + a
          frictionless CUSTOM handle path (countries differ); deep-link where
          supported else copy; surface counterparty handles + "mark as paid" at settle.
          - [x] `payment_method` table (per-user, GLOBAL — not per-group; a
                person's Venmo/UPI/IBAN is the same wherever they settle) +
                migration `c2d3e4f5a6b7`; unique per (user, provider, handle),
                per-user cap (12), CASCADE on hard-delete + PII-scrub on
                soft-delete. Self-service CRUD under `/users/me/payment-methods`
                (provider validated against registry → 422; duplicate/cap → 409).
          - [x] `app/core/payment_providers.py` registry (single source of truth
                for valid codes + `build_pay_url`): venmo/paypal/cashapp/revolut
                deep-link to profile pages, upi → `upi://pay?pa=`, iban → copy-only,
                custom → pasted https link becomes a button else copy-only. Handles
                URL-encoded; custom URLs restricted to http(s) (stored-XSS guard on
                the rendered href). Frontend `lib/payment-providers.ts` mirror holds
                ONLY presentation metadata (names/placeholders) — pay_url is
                server-computed, never duplicated.
          - [x] Counterparty lookup `GET /expense-groups/{id}/members/{uid}/
                payment-methods`, authorized by SHARED group membership (caller a
                member → 403 else; target a member → 404 else). Handles are meant
                to be seen by the people who owe you — public within that boundary.
          - [x] Universal mark-as-paid: `PaymentHandles` (Pay deep-link where one
                exists + always Copy) surfaced at BOTH settle surfaces — the
                pairwise "Between you and…" settle-up confirm AND the per-expense
                "Ready to settle" card, before the pay action. Manager
                (`PaymentMethodsManager`) added as a Settings tab.
          Verification: DONE 2026-07-21 — **backend 288 passed / 0 skipped** (was
          258; +30: 13 provider-URL unit tests incl. XSS-scheme rejection + 17 API
          tests incl. CRUD/validation/cap/dup/counterparty-authz/soft-delete scrub);
          `alembic check` clean, downgrade exercised. Frontend typecheck green,
          **103 passed** (+9: registry + PaymentHandles), build green — main chunk
          **170.20 kB gz** (budget ≤250), payments split to its own 1.37 kB chunk.
          **Screenshots (Playwright, real seeded scenario — You owe Alex $50):** 8
          shots (group settle-up with Alex's Venmo/PayPal Pay-links + IBAN copy-only,
          and Settings manager × 375px/1280px × light/dark) →
          `_bmad-output/implementation-artifacts/ws10.2-screenshots/`.
          Notes / deviations:
          - The nginx build serves an image-baked bundle + a strict CSP
            (`connect-src 'self' https:`) that blocks the http://localhost:8000 API
            locally — this is the "CORS-blocked" wall WS10.1 hit (it's CSP). Pixel
            proof path: `docker compose cp frontend/dist/. frontend:/usr/share/
            nginx/html/` to serve the fresh build, then Playwright with
            `bypassCSP:true` + a minted JWT in localStorage. The CSP itself stays
            verified by WS8's tests, not bypassed in production.
          - Edit endpoint (`PUT /users/me/payment-methods/{id}`) exists + tested but
            the manager UI does add + remove only (change = remove & re-add) — the
            same lean-UI call as BYOK's keyed endpoints.
          Status: DONE 2026-07-21 (branch ws10.2/payment-links)

    - [x] **WS10.3 — Invite Public Preview + OAuth-return** (S2-F1)
          Depends on: WS8. Current preview endpoint requires auth — add an UNAUTH
          public preview + landing ("X invited you to 'Trip' — N members"),
          one-tap OAuth carrying the token → auto-land inside the group.
          - [x] Optional-auth dependency `OptionalCurrentUser` (deps.py,
                `auto_error=False` bearer) — never raises, so an anonymous
                visitor and a broken token both get the public view.
          - [x] `GET /expense-groups/invite/{token}` is now PUBLIC: no auth
                required, `already_member` only computed when authed (False for
                anonymous), `inviter_name` added to the preview, per-IP
                `PREVIEW_LIMIT` (30/min) defense-in-depth on the unauth endpoint.
                No new table/migration (reuses GroupInvite).
          - [x] Public landing (`invite.$token.tsx`): dropped the force-redirect
                to /login. Logged-out visitors see "<inviter> invited you to
                <group> — N members" with one-tap "Continue with Google to join"
                (stashes the token via OAuthButtons `beforeRedirect`) + an email
                fallback; signed-in visitors get the explicit Join button.
          - [x] OAuth-return auto-join (`auth.callback.tsx`): after the code
                exchange, `processPendingInvite()` → POST accept → land inside the
                group; invalid/expired invite falls through to the dashboard.
                Magic-link carry (login.verify) unchanged.
          Verification: DONE 2026-07-21 — **backend 294 passed / 0 skipped** (was
          288; +6 public-preview tests: unauth 200 + inviter_name, authed
          member/non-member already_member, invalid 404, revoked 410, garbage
          bearer → public view). Frontend typecheck green, **103 passed**, build
          green — main chunk unchanged (~170 kB gz). The existing WS8
          preview-does-not-join test stays green (auth still personalizes).
          **Screenshots (Playwright, real seeded invite):** 6 — public landing
          (Jordan Lee → "Roommates", Google CTA + email fallback) × 375px/1280px ×
          light/dark, plus the logged-in Join view × light/dark →
          `_bmad-output/implementation-artifacts/ws10.3-screenshots/`. **OAuth-carry
          proven:** clicking "Continue with Google to join" fires the OAuth login
          request AND stashes `pending_invite_token` (204-nav trick keeps the doc
          alive to read sessionStorage).
          Notes / deviations:
          - Full live-Google round trip still needs real client creds (WS8's
            standing gap) — the carry glue + accept path are proven with a minted
            JWT + the real accept endpoint; only Google's redirect is stubbed.
          - Route components aren't unit-tested in this repo (thin, and
            OAuthButtons reads `import.meta.env` at module load) — the flow is
            proven via Playwright, matching WS3/WS8/WS10.2.
          Status: DONE 2026-07-21 (branch ws10.3/invite-public)

    - [x] **WS10.4 — Onboarding First-60-Seconds** (S2 §6)
          Depends on: WS7, WS10.1. Sandbox "try one expense" parse on the organic
          path; group templates (Roommates/Trip/Dinner) presetting the social
          contract; empty states name the next action.
          - [x] Sandbox parse: `ExpenseParseRequest.group_id` made OPTIONAL; the
                parse endpoint skips the membership gate + defaults to friendly
                when no group_id is sent (grouped parses unchanged). It never
                persists — only returns parsed data — and is metered like any
                hosted parse (a model call costs money; 429 on exhausted quota).
                Frontend `parseExpense` groupId optional (omits group_id from the
                body). New `OnboardingSandbox` renders on the empty dashboard
                (organic path): type an expense → real streamed commentary →
                read-only "here's what I read" preview (formatCurrency in the
                locale currency) → always-present "Create your first group" CTA.
                No migration (request-field plumbing only).
          - [x] Group templates: `ExpenseGroupCreate.strict_mode` (optional)
                threaded into `create_expense_group` → seeds GroupSettings.
                `frontend/src/features/groups/templates.ts` defines Roommates/
                Trip/Dinner (name + strictMode + a social-contract blurb); chips
                in CreateGroupForm prefill the name (only while it's still a
                template default — never clobbers a typed name) + send strict_mode.
                All three ship strict_mode OFF per S2 §6 ("strict-mode off"); the
                per-template field + optional payload keep nudge-cadence /
                settlement-cycle presets ready to attach at WS12 without reshaping
                call sites.
          - [x] Empty states name the next action: groups page gains a "Create
                your first group" button (was text-only); activity "no groups"
                gains a "Create a group" CTA; dashboard empty state IS the sandbox.
          Verification: DONE 2026-07-21 — **backend 298 passed / 0 skipped** (was
          294; +2 sandbox parse [no-group success + metered 429], +2 group-template
          [default strict off, template presets strict]); `alembic check` clean (no
          schema change). Frontend typecheck green, **111 passed** (was 103; +3
          OnboardingSandbox, +4 CreateGroupForm templates, +1 parse omits group_id),
          build green — main chunk **170.40 kB gz** (budget ≤250).
          **Screenshots (Playwright, API-intercepted — no live Gemini needed):** 16
          — sandbox idle + sandbox aha (parsed preview) + groups-empty + create-group
          templates, each × 375px/1280px × light/dark →
          `_bmad-output/implementation-artifacts/ws10.4-screenshots/`.
          Notes / deviations:
          - Sandbox is auth-gated (user is signed in on the organic path; "before
            any setup" means before a GROUP, not before auth) and consumes the
            normal monthly free quota — no separate quota bucket invented.
          - Screenshot proof used Playwright request interception (canned dashboard
            + SSE parse) rather than a live backend, sidestepping the nginx CSP /
            cross-origin :8000 wall and the absent GEMINI_API_KEY entirely.
          Status: DONE 2026-07-21 (branch ws10.4/onboarding)

    - [x] **WS10.5 — Monetization Spec** (DOC ONLY, no code)
          Tier matrix, quota numbers (align w/ WS7 AI_FREE_MONTHLY_PARSES=20),
          paywall placements, USD-first pricing, 2–4% conversion target.
          - [x] Wrote `_bmad-output/planning-artifacts/monetization-spec.md` — the
                one-page accountable spec S1 §5 / S9 §6.4 demanded before Epic 6.
                Consolidates S1 §5/§6, S2 §7/§9, S9 §6.4 into: model in one line
                (freemium · organizer-pays · annual-first · USD-first); USD pricing
                table (Pro $1.99/mo · $19.99/yr · Trip Pass $4.99 one-time · Group
                Pro); tier matrix with an honest **Enforcement-today** column
                (only the AI quota is a live gate); the AI quota section pinned to
                the code (`AI_FREE_MONTHLY_PARSES = 20`, config.py:131 — spec number
                matches, not "e.g."); 7-row paywall-placement table (surface /
                trigger / soft-vs-hard gate / mediator-voice copy / build status);
                non-negotiable free floor (network-effect protection — never gate a
                Borrower); 2–4% conversion target + guardrail metrics (invite→join,
                mute-rate kill switch) for WS10.6 to instrument; explicit
                out-of-scope (NO billing built — beta ships free-only + instrumented,
                monetization build-out is Phase 4); open decisions to re-verify at
                launch; full source-traceability appendix.
          Verification: DOC ONLY — no gates run (no code touched). Spec numbers
          cross-checked against live code (config.py:131 = 20; BYOK exempt; payment
          deep links free per WS10.2; per-group USD-default currency per WS10.1).
          Status: DONE 2026-07-21

    - [x] **WS10.6 — Observability: PostHog + Sentry** (owner's dedicated task)
          Depends on: WS10.1–.4. ALL instrumentation code, env-gated
          (VITE_POSTHOG_KEY / SENTRY_DSN, no-op unset): PostHog event taxonomy
          (`domain.entity.action`) + activation funnel (group ≥2 members + ≥1
          confirmed expense within 48h) + PRD metrics (settlement velocity, edit
          rate, mute rate); Sentry frontend (@sentry/react) + confirm backend DSN
          wiring (sentry-sdk already 2.65 from WS8). OWNER configures the instances
          on Render + Vercel.
          - [x] `frontend/src/lib/analytics.ts` — typed 22-event taxonomy (the
                EVENTS map is the single source of truth) + env-gated PostHog
                wrapper: posthog-js via DYNAMIC import (stays out of the main
                chunk; pre-load events queue and flush in order), identify by
                opaque user UUID ONLY (no email/name — owner decision), autocapture
                + session replay + auto-pageviews all OFF, `advanced_disable_flags`
                (CSP: the remote config.js script would violate script-src 'self',
                FE-010), capability-URL scrubbing (`sanitizeUrl` strips invite/
                verify tokens + OAuth ?code= from every outbound URL property).
          - [x] ~20 call sites wired: auth signed_up/logged_in(oauth|magic_link)/
                logged_out; group created (template/currency/strict_mode) +
                settings updated; invite created/viewed(anon-capable)/joined
                (explicit|oauth_return); ai parse started/completed/failed +
                quota.exhausted (the 429 — paywall fuel gauge); expense created
                (source ai|manual + was_edited = PRD Trust Score)/confirmed/
                rejected; settlement claim created/confirmed(claim_age_hours =
                settlement velocity)/rejected; payment method.added/link.clicked/
                handle.copied; deduped SPA $pageviews via router.subscribe.
                Reserved (NOT captured — features absent): nudge.notification.
                sent/muted (WS12 kill switch), billing.paywall.viewed/converted
                (Phase 4).
          - [x] Sentry frontend: `@sentry/react` STATICALLY imported (boot/white-
                screen errors are the point), errors-only (no tracing/replay),
                gated on VITE_SENTRY_DSN, sendDefaultPii false, beforeSend +
                beforeBreadcrumb scrub token URLs, router errorComponent now
                passes the error through to captureException (it was swallowed).
          - [x] Sentry backend: WS8 wiring confirmed (SENTRY_DSN + non-local gate,
                render.yaml slot exists); added `environment` tag to init.
          - [x] Docs: `planning-artifacts/analytics-spec.md` (taxonomy contract,
                metric→event mapping, 5 PostHog dashboard recipes, privacy
                invariants, known blind spots: lazy auto-confirm sweeps are
                server-side → claim.confirmed undercounts); deployment.md §6.5
                owner runbook (PostHog + 2 Sentry projects + env vars) + §7 funnel
                proof checklist line; frontend/README observability section.
          Verification: DONE 2026-07-23 (code side) — backend **298 passed / 0
          skipped** (no schema change); frontend typecheck green, **127 passed**
          (+16 analytics/scrub unit tests), build green — main chunk **175.55 kB
          gz** (budget ≤250; Sentry ~+5 kB tree-shaken, posthog-js in a lazy
          77 kB gz chunk fetched only when a key is set). LIVE smoke (vite dev +
          throwaway key, browser pane): app boots clean, posthog chunk lazy-loads,
          SDK persists distinct_id to localStorage, and the ONLY outbound
          observability request is the /e/ capture call (no config.js script, no
          /flags — CSP-safe). Cold invite→join→activation funnel visible in
          PostHog remains OWNER-RUN (deployment.md §7) once instances exist.
          Status: DONE 2026-07-23 (branch ws10.6/observability)

    - [x] **WS10.7 — Push Permission Flow + Email-first Notifications**
          ~~BLOCKED on WS11 (service worker) + WS12 (delivery backend)~~ —
          **DELIVERED INSIDE WS12** 2026-08-25, exactly as this entry predicted
          ("actual delivery folds into WS12"). The permission prompt (gated on a
          real open balance, on push support, and on the server actually having a
          VAPID key), the `push_subscription` + `notification_preference` stores,
          and both delivery channels all landed there. Nothing remains here.
          Status: DONE 2026-08-25 (in branch ws12/nudge-engine)

- [x] **WS11 — Docs Floor + Test Journeys + PWA Shell** (≈3 days) — **DONE** 2026-08-25
      Goal: the repo survives its first external reader; real flows have automated
      coverage; the app is installable.
      Depends on: WS8 (template deletion settles what docs describe).
      Inputs: 07 (top-10 table), 04 (H5, H4).
      Branch: `ws11/docs-e2e-pwa`.
      Tasks:
      - [x] Repo-root README (what/status/stack/quickstart/layout) + LICENSE decision;
            strip the template README.md (at repo root since WS9.6) to dev setup;
            delete template badges/screenshots/
            release-notes/img/ (S7-H1, M6)
            → README rewritten; LICENSE = MIT, copyright ClearDues, with the
            template-derivation notice kept; `release-notes.md` (755 lines of
            upstream changelog) and all 7 `img/` template screenshots deleted.
      - [x] backend/README rewrite: feature-based architecture, real migration
            workflow (S7-H2); SECURITY.md contact fixed (S7-M1)
            → SECURITY.md now points at security@cleardues.site with scope and
            safe-harbour text. **Owner action: that mailbox must actually exist.**
      - [x] Reconcile session-context/sprint-status numbers; annotate the bypassed
            BLOCKER items (S7-M2, M4)
            → counts corrected to 33/47 done, 14 remaining (was "32 done, 13
            remaining"); Epic 6-7 0/10 (was 0/18); Epic 8 1/4 (was 0/4). All 11
            bypassed "⚠️ BEFORE PRODUCTION" items annotated done /
            deferred-with-link / dropped-with-reason in sprint-status.yaml, and the
            4 verifiably-fixed retro items flipped to `resolved` in
            technical-debt-log.yaml. The Epic-4 blocker bypass is recorded as a
            bypass, not papered over.
      - [x] Decide + document the one API-client pattern (regenerate OpenAPI client
            vs bless hand-rolled) and migrate one feature as the exemplar (S7-M3)
            → DECISION: regenerate. `scripts/generate-client.sh` + frontend/README
            rule; **groups** is the migrated exemplar (zero hand-built `__request`
            left in it). 32 call sites in auth/dashboard/expenses still to follow.
            Two backend schemas tightened so the generated client stops lying:
            `ExpenseGroupDetail` defaults dropped, `ai_personality` → `Literal`.
            `scripts/generate-client.sh` itself was broken — it shelled out to a
            host Python with the backend importable, which no checkout has — so
            the newly-documented workflow could not run. Rewritten to go through
            `docker compose exec`, with a guard against regenerating from an empty
            dump; verified by running it (client comes back byte-identical).
      - [x] Delete 4 template Playwright specs; write 3–4 ClearDues smoke journeys
            (magic link via mailcatcher, group create+invite, expense confirm,
            settle-up) wired into CI (S4-H5)
            → 4 template specs + 3 template helpers deleted; 5 specs / 12 tests
            written (the 4 journeys + a CSP-header guard). New `e2e` CI job stands
            the real compose stack up and uploads the Playwright report.
            **The suite was not actually green when written** — it passed once and
            failed on re-run. Three defects, all fixed and each now a solution
            pattern: (a) the suite trips the app's own 10/minute auth rate limit
            after ~20 registrations → `RATE_LIMIT_AUTH` setting, default unchanged,
            raised only for the e2e stack, limiting stays ON (TEST-008); (b) all
            tests share one account, so hardcoded descriptions collided and
            `.first()` confirmed other tests' expenses → unique labels + row-scoped
            actions (TEST-007); (c) `waitForURL` returns while the previous list is
            still mounted, so `getByText("1 member")` matched 6 list cards → wait
            for the detail heading, and scope member-count assertions. A duplicate
            `createGroup` in group-invite.spec.ts was deleted in favour of the
            shared helper. Now **9 consecutive clean full-suite runs**.
      - [x] PWA install shell: manifest, icons (v2 brand), service worker via
            vite-plugin-pwa, theme-color meta — install-shell only, offline data
            explicitly out (S4-H4)
            → vite-plugin-pwa, 4 generated icons (192/512/maskable-512/apple-180),
            per-scheme theme-color. `runtimeCaching: []` and an `/api/`
            navigate-fallback denylist keep the SW off API responses — a stale
            balance shown as current is worse than no balance.
      Verification: e2e smokes green in CI; Lighthouse PWA installability passes.
      Result: backend **298 passed** (incl. the rate-limit test, now pinned to
      10/minute so it cannot inherit the e2e override), `uv lock --check` in sync,
      frontend **127 passed**, typecheck + build green, **12/12 Playwright
      journeys pass — 9 runs in a row, plus a CI-shaped single-worker run**; main
      chunk 175.79 kB gz (budget ≤250 ✓). PWA verified in real Chromium: the SW
      registers, activates, and serves the navigation; manifest carries every
      field Chrome's installability check requires (name, short_name, start_url,
      standalone, 192+512+maskable icons, secure context); an `/api/` request is
      passed through, not answered from cache. Lighthouse CLI was not installed,
      so its individual criteria were asserted directly rather than via a
      Lighthouse run.
      Status: DONE

### PHASE 3 — The Differentiator → BETA

- [x] **WS12 — Nudge Engine: Infra + Level 1** (≈1 week) — **DONE** 2026-08-25
      Goal: the product's reason to exist gets a substrate and its first level.
      Depends on: WS6 (aggregate settle-up — nudges must be per-relationship),
      WS9 (somewhere to run), WS10 (telemetry).
      Inputs: 09 Phase 3, 02 Phase B, 03 (H1 — delete dead publisher first), 06 (H2).
      Branch: `ws12/nudge-engine`.
      **SCOPE AMENDMENT (owner decision, 2026-08-25):** this session's task list
      said "add redis + celery worker + beat to compose". It was **not built**.
      Render's free plan has no background worker and no cron job (both paid,
      from $7/mo each), so a broker plus two processes would have bought a
      scheduler production cannot run. Instead the engine is a plain idempotent
      `run_nudge_sweep()` and the **trigger** is a GitHub Actions cron against a
      secret-guarded HTTP endpoint — free, and the same code path in dev, CI and
      production. Moving to Celery later changes the trigger, not the engine.
      Recorded in architecture.md ("WS12 CORRECTION"). S6-H2's "provision the
      worker tier" is therefore answered by *descope-with-reason*, not by
      building it; NFR7 (1k WebSockets) stays explicitly unvalidated.
      Tasks:
      - [x] Delete `publish_expense_confirmed_event` + `notify_group_of_finalized_
            expense` dead code; ~~add redis + celery worker + beat to compose~~;
            declare deps; adopt the event envelope for real
            → both dead functions and their call sites deleted, plus the orphaned
            `REDIS_HOST`/`REDIS_PORT` settings (03-H1's "dead code wearing the
            architecture's uniform" is gone). Envelope adopted as the
            `notification.event_type` field on the `domain.entity.action`
            convention — the same vocabulary as the WS10.6 analytics taxonomy,
            rather than a shape for a bus that does not exist. Dep added:
            `pywebpush` (brings py-vapid + http-ece).
      - [x] Level 1 nudges: gentle reminders, **per-relationship per-group, never
            per-expense** (written into ACs); channels: web push + email
            → enforced by the SCHEMA, not by discipline: `nudge_state` is
            UNIQUE(user, group, counterparty), so there is nowhere to record a
            per-expense nudge. Debts net across both directions and across every
            expense between a pair; only the net debtor is nudged. Push is
            primary, email is a FALLBACK (a successful push suppresses the
            email — never two buzzes for one debt). Email ships complete but
            inert until SMTP is set, the WS10.6 env-gating pattern.
      - [x] Snooze + quiet hours
            → snooze 1/3/7 days per relationship; mute per relationship; a global
            kill switch. Quiet hours are per-user local wall-clock with a
            midnight-wrapping window (default 22→08) and DEFER rather than
            cancel — the state row is left untouched so the next sweep outside
            the window still sends.
      - [x] Notification permission UX from WS10 wired to real notifications
            (this is WS10.7, which was blocked on exactly this session)
            → the prompt appears only once the user has a real open balance, and
            only if the browser can do push AND the server has a VAPID key —
            a browser grants that prompt once, so it is never spent on a feature
            that would have nothing to say. Settings gained a Notifications tab
            (kill switch first, then channels/quiet hours, then per-relationship).
      Verification: DONE — backend **337 passed / 0 skipped** (+39), `alembic
      check` clean (migration `c3d4e5f6a7b8`, 4 tables); frontend typecheck green,
      **143 passed** (+16), build green, main chunk **176.12 kB gz** (≤250);
      `importScripts("/push-sw.js")` verified in the built SW. LIVE PROOF: a
      Level 1 nudge was delivered end-to-end by web push — real VAPID keypair,
      real browser-side EC keys, sweep → `aes128gcm`-encrypted 376-byte payload
      POSTed with an `authorization: vapid t=<ES256 JWT>` header, and
      `deliveries: {push:sent: 1}` with NO email, proving the fallback. Email
      separately proven end-to-end via mailcatcher. **Found by running it:**
      pywebpush base64url-DECODES `vapid_private_key`, so a pasted PEM dies with
      an opaque ASN.1 error — the server now normalizes both forms, and the
      runbook's key-generation command was executed verbatim before being
      documented (WS9's lesson).
      Visual proof (DoD v2 #2) → `_bmad-output/implementation-artifacts/
      ws12-screenshots/` — 12 shots, both themes × 375/1280, of the
      Notifications tab (normal + muted) and the push prompt, captured by a
      dedicated `visual` Playwright project kept out of the CI journeys.
      **Looking at them caught two real layout bugs that every other gate
      passed:** (a) the fourth settings tab pushed the tab strip to 420px, so
      the whole page scrolled sideways at 375px (`document.body.scrollWidth`
      444 vs a 375 viewport — measured, not eyeballed) → the strip now wraps;
      (b) the push prompt's `flex-1` copy shrank to a ~100px column instead of
      pushing the buttons to their own line → it now stacks below `sm`. This
      is exactly the Epic 2.5 failure mode (offscreen navigation shipped for
      five months) and exactly why the rule exists.
      e2e: **15/15 Playwright journeys** (the WS11 twelve, unchanged, plus 3
      new notification-settings journeys proving the controls are reachable
      and the off switch persists) — green on two consecutive full runs.
      Not on staging: the deploy is still unperformed (WS9.5 owner actions
      outstanding), so "on staging" could not be satisfied by anyone this
      session. §6.6a's dry-run is the owner's one-click equivalent.
      Status: DONE

- [x] **WS13 — Nudge Engine: Level 2 + Beta Launch** (≈1 week) — **CODE DONE**
      2026-08-31; **BETA NOT LAUNCHED** (owner action, see the last task)
      Goal: progressive urgency ships; beta goes live.
      Depends on: WS12; all Phase 2 sessions done.
      Branch: `ws13/nudge-level-2`.
      Tasks:
      - [x] Level 2 escalation (frequency/tone progression per the social contract);
            Level 3 remains cut
            → **tone**: Level 2 retells the same debt from the CREDITOR's side
            plus its age ("… covered this 4 days ago and is still out of
            pocket"). It deliberately says nothing about what other members
            have done — that is Level 3 by another name, and a test
            (`test_level_2_never_mentions_anyone_else`) guards the copy, not
            just the behaviour. **frequency**: the cooldown narrows from 72h
            to 48h once a relationship reaches Level 2.
            Two decisions beyond the story AC: (a) Level 2 requires a Level 1
            to have actually been SENT — a five-day-old debt the engine has
            never mentioned still opens gently, because escalation is a
            property of the conversation, not the calendar; (b) **the ladder
            ends** — with Level 3 cut there is no rung above Level 2, so the
            engine goes quiet after `NUDGE_LEVEL_2_MAX_REMINDERS` (4) rather
            than repeating its firmest message forever, and says so in
            Settings ("no more reminders"). New column
            `nudge_state.level_2_count`, migration `d4e5f6a7b8c9`.
      - [x] "Cleared without asking" success notification (the brand promise made
            visible)
            → sent to the CREDITOR, **inline from settlement confirmation**
            (owner decision) rather than from the sweep, because the value of
            this one is its timing. Refused wherever the sentence would be
            false: no nudge was ever sent (the creditor may have asked in
            person), the debt is only partly paid, or it already went out.
            Covers auto-confirmed settlements too — a creditor who never even
            responded is the purest case. Runs in a SAVEPOINT and never
            raises: a broken push service cannot fail somebody's settlement
            (`test_a_broken_notification_cannot_break_a_settlement`). Push is
            capped at 3s inline vs 10s in the sweep. During quiet hours it
            changes channel to email rather than dropping the message or
            buzzing someone at 3am.
      - [x] Mute/block-rate telemetry wired to the PRD kill-switch dashboard
            → the numerator shipped in WS12 (`nudge.notification.muted`). The
            missing half was the DENOMINATOR, which PostHog structurally
            cannot hold: sends happen server-side, so no browser ever
            witnesses one. `GET /notifications/internal/nudge-metrics` (same
            cron-secret guard as the sweep) returns mute rate over people
            actually REACHED, plus sends by level/channel, debts cleared after
            a nudge, and relationships the ladder exhausted. `mute_rate` is
            **null, not 0.0**, before anyone has been nudged — "nobody minds"
            and "nobody has been asked yet" must not look identical on the one
            number the PRD would halt the product on.
      - [x] ~~WS load/scheduler sanity check on staging~~ (NFR honesty — declare real
            numbers, not aspirations) — **measured LOCALLY; staging does not
            exist** (WS9.5 owner actions still outstanding, same as in WS12).
            `backend/scripts/nudge_benchmark.py`, re-runnable. Beta scale (149
            relationships): sweep **102 ms** dry / **230 ms** writing. Stress
            (3,049): **2.9 s** dry / **6.0 s** writing — comfortably inside the
            cron's 180 s budget. Linear at ~2 ms/relationship, dominated by one
            `nudge_state` lookup per relationship (an N+1; logged as debt, does
            not block the beta). "WS" in the original task meant WebSockets:
            **NFR7 (1k concurrent WebSockets) and NFR1 (200 ms real-time) are
            UNVALIDATED AND UNMET** — there are no WebSockets, descoped in WS12.
            Stated plainly in beta-launch.md rather than left as an aspiration.
      - [x] Beta checklist: seed 5–10 real groups, weekly metric review cadence
            (activation, settlement velocity, mute rate), feedback channel
            → **`beta-launch.md`** (linked from README): pre-flight gates, the
            expectations text to send with every invite, how to onboard real
            groups through the product's own invite flow (**no seeding rows
            into production**), the 30-minute weekly review with a mute-rate
            reading table, feedback-channel choice, and **kill criteria
            written down before the data arrives** (>25% mute rate sustained
            over two reviews = stop and rethink, do not tune the copy and
            carry on).
      - [ ] **→ LAUNCH PRIVATE BETA** — **BLOCKED, owner action.** Nothing is
            deployed: WS9.5's Neon/Render/Vercel/domain/Google-login steps have
            never been performed, so there is no system to invite anyone to.
            deployment.md §0–§7 first, then beta-launch.md §1.
      Verification: backend **355 passed / 0 skipped** (+18), `alembic check`
      clean (migration `d4e5f6a7b8c9`); frontend typecheck green, **149
      passed** (+6), build green, main chunk **176.15 kB gz** (≤250);
      e2e **15/15 Playwright journeys, green on 8 consecutive parallel runs**.
      Visual proof (DoD v2 #2) → `_bmad-output/implementation-artifacts/
      ws13-screenshots/` — 16 shots, both themes × 375/1280, of all four
      ladder states.
      **Found by running it — three things no gate would have caught:**
      (a) the first screenshot run PASSED while photographing **stale pre-WS13
      UI** — compose serves the *built* frontend image on :5173 and Playwright
      reuses it, so the spec now asserts each status line is visible and that
      `document.body.scrollWidth <= 375`, turning a pixel dump into a real
      guard; (b) WS12's `test_quiet_hours_defer_without_consuming_the_nudge`
      had a hardcoded `2026-08-25` tested against relatively-backdated data —
      green on the day it was written, red six days later, testing nothing in
      between (now anchored to today); (c) the WS12 notification journeys
      flaked ~1 run in 3 under `fullyParallel` — three tests sharing one
      account, where the kill-switch test disables the fieldset the
      quiet-hours test is clicking. CI never saw it (`workers: 1`). Fixed by
      making that describe serial, and separately by locking the preferences
      row on write (`with_for_update`) — a genuine lost update where two
      devices changing different settings would clobber each other.
      Status: CODE DONE; beta launch pending the owner's deploy

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
