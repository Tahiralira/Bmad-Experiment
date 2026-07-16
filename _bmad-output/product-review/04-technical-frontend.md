# Session 4 — Technical Review: Frontend

**Date:** 2026-07-06
**Scope:** `frontend/src/`, `package.json`, Vite/TS/Biome/Playwright configs
**Method:** Full source read of app code (generated `src/client/` skimmed only), plus
verification runs of `npm run typecheck` (FAILS, 17 errors) and `npm run build`
(passes, 13.4s). Severity per CLAUDE.md review scoping. Cross-references use the
Session 3 finding IDs (`B-C1`…`B-H10`) for backend items.

---

## 1. Verdict Up Front

The frontend is a set of decent components without an application wired around
them. Individual component quality is genuinely above average for this codebase's
stage — strict TypeScript with only two `any`s in app code, real accessibility work
(focus traps, ARIA labels, reduced-motion support), idiomatic TanStack Query. But
the integration layer was never built:

- **No user can create an expense through the UI.** The only entry point mounts
  without a `groupId` and silently no-ops (C1).
- **The flagship AI parsing experience is a hardcoded mock** — every input parses
  to "Lunch with team, $60" with a fake user ID (C2).
- **All 1,356 lines of unit tests have never compiled** — the test frameworks they
  import were never installed (C3).
- **The debtor half of the settlement loop (Story 5.1's UI) is never mounted** (C4).
- The FastAPI template the project started from still ships: a parallel
  password-auth system, admin panel, "Items" demo CRUD, FastAPI logos and page
  titles (H2).
- The documented architecture (Redux, WebSockets, PWA) matches nothing in the
  code — zero Redux, zero WebSocket/SSE client code, zero PWA infrastructure.

The pattern mirrors Session 3's backend conclusion and sharpens it: stories were
built as isolated component deliverables, passed "code review" as components, and
were never connected into user-reachable flows. Epics 3–5 are "done" on paper;
none of them is operable end-to-end from the browser.

**Frontend health score: 4/10** (components 6.5/10, application integration 2/10).

---

## 2. Findings Summary

| ID | Severity | Finding |
|----|----------|---------|
| C1 | CRITICAL | No UI path exists to create an expense — sole entry point mounts without `groupId` and no-ops |
| C2 | CRITICAL | AI parsing is a hardcoded `setTimeout` mock with fake user ID `"user-123"`; no SSE client exists |
| C3 | CRITICAL | All 7 unit-test files import uninstalled frameworks; `npm run typecheck` fails today |
| C4 | CRITICAL | Story 5.1's settle-up UI (`ConfirmedExpenseCard`, `PendingSettlementsList`) is never mounted |
| H1 | HIGH | Global handler logs users out on any 403 — business authorization denials destroy the session |
| H2 | HIGH | Template app still shipped: parallel password auth, /admin, /items, FastAPI branding |
| H3 | HIGH | Groups have no URL — detail view is ephemeral `useState`, no deep-linking, stale after refetch |
| H4 | HIGH | PWA readiness is zero: no manifest, no service worker, no offline anything |
| H5 | HIGH | All 4 Playwright specs test the template's password flows, which no longer exist |
| H6 | HIGH | No real-time client code (mirror of backend B-H1); architecture doc is fiction on both ends |
| M1–M9 | MEDIUM | Split rounding, validation hole, currency sprawl, hand-rolled API layer, 436KB gzip bundle, mis-scoped claims list, lint exclusions, localStorage tokens, dead duplicate modal |
| L1–L8 | LOW | Import-path triplication, `bind(this)` contortion, no-op swipe actions, dead template logic |

---

## 3. CRITICAL Findings

### C1 — No user can create an expense through the UI

The only expense-entry UI in the app is `SmartInputModal` (smart mode + manual
`ExpenseForm` mode). It is mounted exactly once, in `_layout.tsx:61`, **without a
`groupId` prop**. Consequences:

- Smart mode: `handleSmartSubmit` at `SmartInputModal.tsx:146` starts with
  `if (!inputText.trim() || !groupId) return` — the "Add Expense" button silently
  does nothing. No error, no toast, no disabled state.
- Manual mode: renders "Please select a group first" (`SmartInputModal.tsx:439`) —
  but no group selector exists anywhere in the app, despite the prop docs
  ("if provided, selector is hidden") implying one.
- `GroupDetail.tsx` — the one place with group context — renders members,
  settlement claims, and activity, but **no add-expense button and no second
  `SmartInputModal` mount**.

Every Epic 3 story (3.1 form, 3.2 NL input, 3.4 editable preview, 3.5–3.7 splits)
built a component; none of them is reachable with a valid `groupId`. This is the
frontend root cause pairing with backend B-H7 (no ledger endpoints): the group
screen can neither show expenses nor add them.

**Impact:** The product's core loop is dead in the shipped UI.
**Effort:** Medium — add a group selector to the modal (or mount per-group in
`GroupDetail`) and thread `groupId`; the components themselves largely exist.

### C2 — AI parsing is a hardcoded mock; confirming would write fake data

`SmartInputModal.tsx:145–171`: `handleSmartSubmit` runs `setTimeout(…, 2000)` and
sets hardcoded parse results — `{ amount: 60.00, description: "Lunch with team",
confidence_score: 0.95 }` — regardless of what the user typed. The payer comes from
`SmartInputModal.tsx:122`: `const [currentUserId] = useState<string>("user-123")`
with a `// TODO: Get currentUserId from auth context`.

If the flow were reachable (see C1), pressing Confirm calls the **real**
`POST /api/v1/expenses/` with the mock-derived data, including
`payer_id: "user-123"` — a non-UUID that the backend would reject (422) or worse.

There is **zero SSE/EventSource client code in the entire `src/`** (verified by
grep). The `// TODO: Replace with actual SSE endpoint call in Story 3.3
integration` comment is still present although Story 3.3 is marked done, and the
file's git history shows it was last touched by Story 3.5 code-review fixes —
three stories' worth of reviews passed over a mocked core feature.

Combined with backend B-C1 (membership check with swapped args) and B-C2 (no way
to save a Gemini key): **the frontend mock and the backend endpoint were each
built against a counterpart that doesn't exist, and nothing ever integrated
them.** FR1, the product's stated differentiator, is fictional at every layer.

**Impact:** Flagship feature does not exist as far as any user is concerned.
**Effort:** High — real SSE consumption, auth-context user ID, error/confidence
states, plus backend B-C1/B-C2 fixes as prerequisites.

### C3 — The unit test suite has never compiled

Seven test files, 1,356 lines total (`SmartInputModal.test.tsx`,
`AICommentaryBubble.test.tsx`, `ExpensePreviewCard.test.tsx`,
`MemberChips.test.tsx`, `SplitPicker.test.tsx`, `useSplitState.test.ts`,
`useStreamingText.test.ts`) import `vitest`, `@testing-library/react`, and
`@testing-library/jest-dom`. **None of these packages is in `package.json`; there
is no vitest config and no `test` script.** Verified directly:

- `npm run typecheck` → **17 errors**, all `TS2307 Cannot find module 'vitest'/
  '@testing-library/react'` plus latent errors *inside* the test files (`TS6133`,
  `TS7006`, `TS2304`) proving they were never typechecked even once when written.
- `npm run build` → **passes**, because `tsconfig.build.json` explicitly excludes
  `**/*.test.*` — the build config was edited to route around the broken tests
  rather than fix them.

So the project's own documented verification command (CLAUDE.md:
`npm run typecheck && npm run build`) fails at step one today, and every Epic
2.5/3 story that claimed component tests as a deliverable shipped dead code. This
is worse than having no tests: it created false confidence that reviews cited
("tests written") while providing zero regression protection. It also directly
violates MVS criterion #4.

**Impact:** All frontend quality claims in stories 2.5.x–3.x are unverifiable;
CI (when it exists) would be red on day one.
**Effort:** Low to make them runnable (`vitest` + `jsdom` + RTL + config + script);
unknown-but-real effort to make them pass, since they've never executed.

### C4 — Story 5.1's settle-up UI is unreachable dead code

`ConfirmedExpenseCard.tsx` (185 lines — the "mark as settled" button with
optimistic state) and `PendingSettlementsList.tsx` (149 lines) are exported from
the feature barrel but **imported by no route and no parent component** (verified
by grep; the only barrel consumer is `_layout.tsx`, which takes only
`SmartInputModal`). `AuditLogList.tsx` is likewise never mounted.

The settlement loop is therefore half-wired: `GroupDetail` mounts
`SettlementClaimsList` (Story 5.2 — the owner's *confirm* side), but no debtor can
ever *create* a claim, because the UI that does it is unmounted — and there is
nowhere to mount it, since no screen lists confirmed expenses (backend B-H7: the
list endpoints don't exist).

**Impact:** Epic 5 (2/3 "done") is not operable end-to-end by any user.
**Effort:** Blocked on backend ledger endpoints (B-H7); then low-medium to build a
group ledger screen that hosts these cards.

---

## 4. HIGH Findings

### H1 — Any 403 destroys the user's session

`main.tsx:21–26`: the global `QueryCache`/`MutationCache` error handler treats 401
and 403 identically — remove token, hard-redirect to `/login`. But this app uses
403 for **business authorization**: "Only the expense creator can edit" (Story
4.1), "Not a member of this group", "Only the expense owner can confirm
settlements" (Story 5.2). A member tapping Confirm on a settlement they don't own
gets logged out of the entire app mid-session. The `window.location.href` redirect
additionally throws away all SPA state instead of using the router.

**Impact:** Routine permission denials read as "the app crashed and logged me
out". **Effort:** Low — handle 401 only; surface 403 as a toast; use router
navigation.

### H2 — The FastAPI template still ships as live product surface

- **A parallel password-auth system is reachable by URL:** `/signup` (password
  registration), `/recover-password`, `/reset-password`, plus a "Password" tab in
  Settings (`ChangePassword`) — in a product whose Epic 1 replaced passwords with
  magic links. Two account-creation flows now coexist (`/register` = magic link,
  `/signup` = password).
- `/admin` (user management CRUD) and `/items` (the template's demo entity) are
  live routes hitting `ItemsService`/`UsersService`.
- Branding: `index.html` title is **"Full Stack FastAPI Project"** with FastAPI
  favicon; `Logo.tsx` imports four FastAPI SVGs; page titles say "Settings -
  FastAPI Cloud", "Items - FastAPI Cloud".
- `components/Admin/`, `components/Items/`, `components/Pending/`,
  `components/UserSettings/`, `DataTable`, `sidebar.tsx` (737 lines, unused since
  OrbitalNav replaced the sidebar) — roughly 2,500+ lines of template code
  maintained, typechecked, and shipped.

Session 5 should treat the parallel auth surface as an attack-surface finding.

**Impact:** Confused UX, doubled auth surface, unprofessional branding for any
beta user. **Effort:** Low-medium — mostly deletion; verify backend routers for
items/password-auth in Session 5.

### H3 — Groups have no URL; detail state is an ephemeral snapshot

`routes/_layout/groups.tsx:30`: the selected group lives in
`useState<ExpenseGroup | null>` holding a **captured list item**. There is no
`/groups/$groupId` route (the Dashboard `GroupCard` links to `/groups` with a
`// TODO: Update to /groups/${group.group_id} when group detail route is
implemented`). Consequences: no deep-linking, no shareable/bookmarkable group,
refresh loses context, back button doesn't work, and after a query invalidation
the detail panel renders the stale snapshot rather than fresh cache data (e.g.,
`member_count` won't update after an invite is accepted).

This is the concrete mechanism behind the RETRO-2.5-H2 navigation debt.

**Impact:** Core navigation broken for the product's main object.
**Effort:** Medium — add `$groupId` route, derive detail from query cache.

### H4 — "PWA" exists nowhere in the code

The PRD/architecture define ClearDues as a PWA. The frontend has: no
`manifest.webmanifest`, no service worker, no `vite-plugin-pwa`, no app icons
(only FastAPI SVGs), no `theme-color`/apple-touch meta, no offline handling, no
install prompt. `useQuery` calls have no `networkMode`/persistence tuning; an
offline open renders a blank shell that fails every fetch.

**Impact:** A core product claim (installable, mobile-first) is unimplemented and
unplanned in any story. **Effort:** Low for install-shell (plugin + manifest +
icons); high for genuine offline data (cache persistence + mutation queue) —
recommend explicitly scoping the latter out for beta and adding the former to the
launch-blocker epic proposed in Session 2.

### H5 — The E2E suite tests an application that no longer exists

All four Playwright specs (`tests/login.spec.ts`, `sign-up.spec.ts`,
`reset-password.spec.ts`, `user-settings.spec.ts`) are unmodified template tests
driving password fields (`getByTestId("password-input")`) against the magic-link
login page — they fail immediately. Zero ClearDues journeys (magic link, group
create, invite accept, expense confirm, settlement) have any automated coverage.
Combined with C3, **effective automated frontend coverage of the actual product
is zero**, matching the Epic 4 retro's "manual only" admission — except the repo
contains ~1,900 lines of test code implying otherwise.

**Impact:** Every frontend change ships unverified. **Effort:** Medium — delete
template specs; write 3–4 magic-link-aware smoke journeys (needs mailcatcher
helper already present in `tests/utils/mailcatcher.ts`).

### H6 — No real-time client; the architecture document is fiction on both ends

Zero `WebSocket`/`EventSource` usage in `src/` (verified). "Real-time" today is
TanStack Query's default `staleTime: 0` plus mutation-driven invalidation storms —
i.e., other users' changes appear only on remount/refocus. This mirrors backend
B-H1 (no WebSocket/Celery/Redis code). Not an implementation bug — nothing
consumes what doesn't exist — but architecture.md's "WebSockets + Redis Pub/Sub"
and CLAUDE.md's tech-stack table describe neither codebase.

**Impact:** Multi-user staleness; misleading docs for every future contributor.
**Effort:** Roadmap decision (Session 9): either build the layer with Epic 6 or
rewrite the architecture doc to polling-first honestly.

---

## 5. MEDIUM Findings

### M1 — Equal-split rounding only balances if the payer is last in the array
`useSplitState.ts:126–137`: the payer absorbs the rounding remainder **only when
`index === includedMembers.length - 1`** — i.e., only if the payer happens to be
the final element of the members array. Otherwise (e.g., Rs 100 / 3 with payer
first) every member gets 33.33 and the displayed split sums to 99.99 ≠ total. The
backend computes its own splits (and per B-H2/B-H3 has its own bugs), so frontend
preview and stored truth can disagree by cents — in a product whose pitch is
eliminating money disputes. **Fix:** absorb remainder on the payer regardless of
position (compute others first, payer = total − sum). Effort: low.

### M2 — Unequal-split validation counts stale amounts of excluded members
`useSplitState.ts:273`: validity requires `customAmounts.size >= includedCount`,
but `customAmounts` retains entries for members excluded *after* their amount was
set (exclusion doesn't clear amounts). Example: A=100 (total), C=50 then C
excluded, B never filled → size 2 ≥ included 2 passes, remainder = 0 passes, and a
"split" omitting included member B is submitted. Whether the backend catches it is
unverified (B-H6 notes the split endpoint bypasses validation machinery). **Fix:**
validate that every *included* member has an amount. Effort: low.

### M3 — Hardcoded "Rs" currency has metastasized
Session 2 recorded it in `BalanceDisplay`; it is actually in **8+ files**:
`balance-display.tsx` (₹→"Rs" replace on `en-IN` formatting),
`useSplitState.ts:285` (validation strings), `activityFormatters.ts` (4 message
templates), `AuditLogList.tsx:62`, `UnequalSplitInputs.tsx:160–161`, the dead
`ui/smart-input-modal.tsx:173`. There is no currency abstraction; the product
targets a global market (decided 2026-07-07). Every day this spreads it gets costlier.
**Fix:** one `formatCurrency` util now; real currency setting later. Effort: low.

### M4 — Hand-rolled API layer duplicates backend contracts by hand
An OpenAPI codegen pipeline exists and works (`openapi-ts.config.ts`,
`client/sdk.gen.ts`, `types.gen.ts`) and template code uses it — but **every
ClearDues feature module bypasses it**, calling `__request` from
`@/client/core/request` with hand-typed URL strings and ~250 lines of hand-written
response types (`features/expenses/types.ts`, `features/groups/types.ts`,
`features/dashboard/types.ts`). Nothing guarantees these match backend schemas —
exactly the drift class that produced the `id` vs `user_id` confusion the
`GroupMember` comment warns about. The custom `errors:` maps also **replace**
server `detail` messages with hardcoded strings, hiding real error causes. **Fix:**
regenerate client from the live OpenAPI spec and migrate feature APIs to it.
Effort: medium.

### M5 — 1.48 MB single main chunk (436 KB gzip)
Verified by build: `index-BNPlC_kJ.js` is 1,484.97 kB minified. Router
`autoCodeSplitting` splits routes, but they're trivial (2–14 kB) while framer-
motion, all Radix primitives, react-table, lucide, and both devtools live in the
entry chunk. For a mobile-first "PWA" this is a heavy first load on mid-range
devices. **Fix:** `manualChunks` for vendor split; lazy-load framer-motion-heavy
components; drop template deps (react-table goes with H2's DataTable). Effort:
low-medium.

### M6 — SettlementClaimsList shows other groups' claims inside a group panel
`GroupDetail.tsx:35` mounts `SettlementClaimsList` with no `groupId`; the hook
fetches `/expenses/settlement-claims/pending-for-owner` — **all** of the owner's
pending claims across every group, rendered under a specific group's heading.
Users will attribute claims to the wrong group. (Backend offers no group-scoped
variant — add to B-H7's endpoint gap.) Effort: low (filter client-side by the
group's expense IDs once a ledger exists; properly, a scoped endpoint).

### M7 — The custom design system is exempt from linting
`biome.json` excludes `src/components/ui/**` entirely — appropriate for vendored
shadcn files, but ~2,200 lines of *bespoke* Epic 2.5 components live there
(`orbital-nav` 487, `swipeable-card` 483, `smart-input-modal` 471, `agent-orb`
304, `inline-input` 228, `balance-display` 187) and have never been linted. The
`lint` script also runs with `--unsafe` autofixes. **Fix:** move custom components
out of `ui/` (or un-exclude them); drop `--unsafe`. Effort: low.

### M8 — Auth token handling (flagging for Session 5)
JWT in `localStorage` (XSS-exfiltratable; no httpOnly option), `isLoggedIn()` =
key-exists check (expired tokens render the app shell, then H1's handler evicts),
`OpenAPI.TOKEN` reads it per request. Standard-but-weak; Session 5 owns the
recommendation (httpOnly cookie vs. accepted risk + CSP).

### M9 — A dead 471-line duplicate of the flagship modal
`components/ui/smart-input-modal.tsx` is an unused, drifted copy of
`features/expenses/components/SmartInputModal.tsx` (468 lines), both exporting
`SmartInputModal` from their barrels. Which one is canonical is invisible to a new
contributor (the *feature* one is mounted). It also still contains its own "Rs"
hardcode and mock logic. **Fix:** delete. Effort: trivial.

---

## 6. LOW Findings

- **L1 — Triple import paths for the same modules:** `@/hooks/useAuth` and
  `@/hooks/useCustomToast` are re-export shims; `@/shared/api` re-exports
  `@/client`; feature code imports from all three spellings plus
  `@/client/core/request` directly. Pick one path, delete the shims.
- **L2 — `handleError.bind(showErrorToast)`** (`utils.ts:16`, used in auth hooks):
  passing the toast via `this` is a needless contortion; make it a parameter.
- **L3 — Devtools mounted unconditionally** in `__root.tsx` and shipped in
  `dependencies` (they no-op in prod builds but belong in `devDependencies`
  behind a dev-only lazy import).
- **L4 — Dashboard swipe actions are no-ops:** `Dashboard.tsx:98–111` — "Edit
  group" and "Settle up" swipe reveals do nothing (`// TODO … (Epic 3)`, two
  epics stale). Shipping discoverable-but-dead gestures erodes trust; hide until
  implemented.
- **L5 — Duplicate Escape/close handling** in `SmartInputModal` (window listener
  + Radix's built-in) and state reset in three places (`handleClose`, open-effect,
  confirm path) — consolidation would prevent the classes of stale-state bugs the
  timeouts paper over.
- **L6 — `settings.tsx` dead template logic:** `tabsConfig.slice(0, 3)` on a
  3-item array is a no-op superuser branch; page title still "FastAPI Cloud".
  Superseded if H2's cleanup lands.
- **L7 — `m.user_id || m.id` fallback** (`useSplitState.ts:111,130` etc.)
  silently substitutes the join-table row ID that `types.ts:156` explicitly warns
  against; if `user_id` is ever falsy that's a bug to surface, not mask.
- **L8 — Group list `member_count || 1`** (`groups.tsx:102`) masks a missing
  backend field with a guess.

---

## 7. Architecture Conformance (vs architecture.md / CLAUDE.md)

| Claim | Reality | Assessment |
|-------|---------|------------|
| Redux Toolkit for UI state | **No Redux anywhere** (not even installed) | Deviation is *correct* — local state + TanStack Query suffices — but docs describe a stack that never existed |
| TanStack Query for server state | Yes, idiomatic; thorough invalidation | Conforms |
| WebSockets + Redis real-time | Zero client code (H6) | Docs fiction, both ends |
| PWA | Zero PWA code (H4) | Docs fiction |
| Feature-based directories | ClearDues code conforms; template dirs (`components/Admin|Items|Pending|UserSettings`) violate | Partial |
| Frontend naming conventions | Followed | Conforms |
| TypeScript strictness | `strict: true`, 2 `any`s in app code | Exceeds — genuinely good |

---

## 8. Prioritized Fix List (impact × effort)

1. **Wire expense entry** (C1) — medium effort, unblocks the entire product loop.
2. **Restrict logout to 401** (H1) — one-line class of fix, prevents session-loss
   bug from poisoning all testing of Epics 4–5 flows.
3. **Install vitest + make typecheck green** (C3) — low effort, restores the
   documented verification command and reveals which tests ever worked.
4. **Group detail route `/groups/$groupId`** (H3) — medium, prerequisite for the
   ledger screen that C4 and B-H7 need.
5. **Delete template surface** (H2 + M9 + L6) — low, mostly `git rm`; shrinks
   attack surface before Session 5's audit and the bundle (M5).
6. **Real AI-parse integration** (C2) — high effort, sequenced after backend
   B-C1/B-C2; until then, remove or clearly label the mock so no beta user sees
   fake parsing.
7. **Ledger screen + settle-up mount** (C4) — blocked on B-H7 endpoints.
8. **Currency util** (M3) + **split-math fixes** (M1, M2) — low effort, do
   alongside any Epic 5 completion work.
9. **PWA install-shell** (H4) + **replace template e2e with 3 smoke journeys**
   (H5) — belongs in the Session 2 launch-blocker epic.

---

## 9. Corrections to Prior Session Facts

- Session 2: "Frontend tests: manual only" → **understated.** 1,356 lines of unit
  tests + 4 e2e specs exist in-repo; none has ever run (C3, H5). The repo
  *appears* tested and is not.
- Session 2: "'Rs' hardcoded in BalanceDisplay" → **understated**: 8+ files (M3).
- Session 1/2 framing "Epic 3 done except 3.8" → components exist, but no expense
  can be created via UI (C1) and AI input is mocked (C2); "done" is
  component-complete, not user-complete.

## 10. Inputs for Later Sessions

- **Session 5 (Security):** localStorage JWT (M8); 401/403 conflation (H1);
  parallel password-auth routes + `/admin`, `/items` exposure (H2) — verify the
  backend routers behind them; state-changing group-join via GET
  (`acceptInvite` GETs `/invite/{token}` — CSRF/prefetch-triggerable join).
- **Session 6 (Infra):** no CI — note that `npm run typecheck` fails today, so
  any CI must start from C3's fix; 436 KB gzip bundle (M5); nginx configs present
  but unreviewed here.
- **Session 7 (Docs):** CLAUDE.md tech stack lists Redux (absent); architecture.md
  real-time/PWA claims (H4, H6); CLAUDE.md's own verify command broken (C3).
- **Session 8 (UX):** OrbitalNav is the *sole* navigation (hidden behind an orb
  interaction — discoverability risk); long-press is the only path to expense
  entry (C1); no group deep-links (H3); dead swipe gestures (L4); dark theme
  default via template `ThemeProvider`.
