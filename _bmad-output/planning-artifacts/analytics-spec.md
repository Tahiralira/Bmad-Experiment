# ClearDues Analytics Spec (WS10.6)

**Status:** ADOPTED 2026-07-23 · **Owner setup:** [deployment.md §6.5](../../deployment.md)
**Code:** `frontend/src/lib/analytics.ts` (taxonomy + PostHog wrapper),
`frontend/src/lib/sentry.ts` (error monitoring), `backend/app/main.py` (backend Sentry).

This is the contract between the code and the dashboards. The `EVENTS` map in
`analytics.ts` is the single source of truth for names; **this doc must change in
the same commit as that map.** Everything is env-gated (`VITE_POSTHOG_KEY`,
`VITE_SENTRY_DSN`, `SENTRY_DSN`) — unset means a complete no-op.

---

## 1. Decisions (locked 2026-07-23)

| Decision | Choice | Why |
|---|---|---|
| Capture side | **Frontend-only** (posthog-js) | Every WS10.6 metric is a user-driven UI action; no backend dep or per-request latency on Render free tier |
| Identity | **Opaque user UUID only** — never email/name | Matches the WS8 privacy posture (`send_default_pii=False` everywhere); cross-reference the DB when a human name is needed |
| Autocapture / session replay | **Both OFF** | Clean taxonomy, no accidental PII (amounts/descriptions in DOM), replay's remote recorder script would violate the CSP |
| Naming | `domain.entity.action` | S2 §9 — same convention the WS12 event envelope will use |
| Token hygiene | Invite/verify tokens + OAuth codes scrubbed from ALL outbound URLs | An invite token in an analytics payload is a join-the-group credential |

---

## 2. Event taxonomy (live)

Every event carries PostHog defaults ($current_url etc., scrubbed) plus the
listed properties. Amounts and free-text (names, descriptions, handles) are
**never** properties.

| Event | Fires when | Properties | Instrumented at |
|---|---|---|---|
| `auth.user.signed_up` | Registration magic-link verified | `method: "magic_link"` | `routes/verify.$token.tsx` |
| `auth.user.logged_in` | OAuth exchange / login magic-link verified | `method: "oauth" \| "magic_link"` | `auth.callback.tsx`, `login.verify.$token.tsx`, `useAuth` |
| `auth.user.logged_out` | Logout clicked | — | `useAuth.logout` |
| `group.group.created` | Group created | `template: "roommates"\|"trip"\|"dinner"\|"none"`, `currency`, `strict_mode` | `CreateGroupForm` |
| `group.settings.updated` | Owner changes a group setting | `setting: "strict_mode"\|"ai_personality"\|"currency"` | `useUpdateGroupSettings` |
| `group.invite.created` | Invite link generated | — | `useCreateInvite` |
| `group.invite.viewed` | Invite landing preview loads (anonymous OK) | `logged_in` | `invite.$token.tsx` |
| `group.invite.joined` | Invite accepted | `method: "explicit" \| "oauth_return"` | `useAcceptInvite`, `auth.callback.tsx` |
| `ai.parse.started` | Parse submitted (grouped or sandbox) | `sandbox` | `api/parse.ts` |
| `ai.parse.completed` | Parse stream completed | `sandbox`, `confidence` | `api/parse.ts` |
| `ai.parse.failed` | Parse failed | `sandbox`, `reason: "http_<status>"\|"stream_error"\|"incomplete_stream"` | `api/parse.ts` |
| `ai.quota.exhausted` | Parse hit the monthly-quota 429 | `sandbox` | `api/parse.ts` |
| `expense.expense.created` | Expense saved | `source: "ai"\|"manual"`, AI-only: `was_edited`, `confidence` | `SmartInputModal`, `ExpenseForm` |
| `expense.expense.confirmed` | Split confirmed | — | `useConfirmExpense` |
| `expense.expense.rejected` | Split rejected | — | `useRejectExpense` |
| `settlement.claim.created` | Settle-up / per-expense settle submitted | `kind: "aggregate"\|"per_expense"`, aggregate: `covered_expense_count` | `useSettleUp`, `useSettleExpense` |
| `settlement.claim.confirmed` | Counterparty confirms | `kind`, `claim_age_hours`, `covered_expense_count` | `useConfirmSettlement` |
| `settlement.claim.rejected` | Counterparty rejects | `kind` | `useRejectSettlement` |
| `payment.method.added` | Payment handle saved | `provider` | `useCreatePaymentMethod` |
| `payment.link.clicked` | "Pay" deep link tapped at settle | `provider` | `PaymentHandles` |
| `payment.handle.copied` | Handle copied at settle | `provider` | `PaymentHandles` |
| `$pageview` | SPA route change (manual, deduped, token-scrubbed) | PostHog defaults | `main.tsx` router subscribe |

**Known blind spots (accepted, frontend-only capture):** the WS6 lazy
auto-confirm sweep (72h window) settles claims server-side with no client
event — `settlement.claim.confirmed` undercounts by the auto-confirmed share;
OAuth first-login is not distinguishable from a returning login client-side
(use the person's first-seen date instead). Revisit both if/when WS12 adds
server-side capture.

## 3. Reserved names (do NOT capture before the feature exists)

| Event | Lands with |
|---|---|
| `nudge.notification.sent` | WS12 nudge engine |
| `nudge.notification.muted` | WS12 — **the kill-switch metric** (S1-W6) |
| `billing.paywall.viewed` | Phase 4 billing (monetization-spec §5) |
| `billing.paywall.converted` | Phase 4 billing |

---

## 4. Metric → event mapping

From [monetization-spec §8](./monetization-spec.md) and the PRD success criteria:

| Metric | Definition | Built from |
|---|---|---|
| **Activation** (S2 §9) | person: joined/created a group that reaches ≥2 members AND ≥1 confirmed expense, within 48h of first-seen | Funnel: (`auth.user.signed_up` OR first `auth.user.logged_in`) → (`group.group.created` OR `group.invite.joined`) → `expense.expense.confirmed`, conversion window 48h. The "≥2 members" leg rides on `group.invite.joined` by the *counterparty* — see §5 dashboard notes |
| **Invite → join rate** (guardrail) | joins ÷ views, and views ÷ creations | Funnel: `group.invite.created` → `group.invite.viewed` → `group.invite.joined` |
| **AI-quota-exhaustion rate** | % of AI users who hit the cap in a month | Unique persons with `ai.quota.exhausted` ÷ unique persons with `ai.parse.started` |
| **Edit rate / Trust Score** (PRD <10%) | AI expenses edited before confirm | `expense.expense.created` where `source="ai"`: `was_edited=true` share |
| **Settlement velocity** (PRD) | time debts sit before settling | `claim_age_hours` on `settlement.claim.confirmed` (claim-open → confirmed). NOTE: expense-confirmed → claim-created latency additionally visible as funnel time between `expense.expense.confirmed` and `settlement.claim.created` |
| **Mute rate** (kill switch) | — **not measurable until WS12** | reserved `nudge.notification.muted` ÷ `nudge.notification.sent` |
| **Payment-rail intent** | which providers people actually use at settle | `payment.link.clicked` + `payment.handle.copied` by `provider` |
| Free→paid conversion, paywall per-surface rates | — Phase 4, needs billing | reserved `billing.paywall.*` |

## 5. PostHog dashboards to build (owner, ~20 min, once §6.5 env vars are live)

1. **Activation funnel** — New funnel insight: step 1 `auth.user.signed_up`
   OR `auth.user.logged_in` (first time), step 2 `group.group.created` OR
   `group.invite.joined`, step 3 `expense.expense.confirmed`; conversion
   window 48 hours. (PostHog can't natively assert "the *group* reached 2
   members" from frontend events — the practical beta proxy: an inviter
   counts as activated when someone else joins their group, which shows up
   as the invitee's `group.invite.joined`. Weekly-review the raw numbers.)
2. **Invite health (guardrail)** — funnel `group.invite.created` →
   `group.invite.viewed` → `group.invite.joined`; watch after ANY paywall or
   nudge change (monetization-spec §8 guardrail rule).
3. **AI trust** — trend: `was_edited` breakdown on `expense.expense.created`
   (`source=ai`); target <10% edited. Add `ai.parse.failed` by `reason`.
4. **Quota fuel gauge** — monthly uniques: `ai.quota.exhausted` vs
   `ai.parse.started` uniques.
5. **Settlement velocity** — trend of median `claim_age_hours` on
   `settlement.claim.confirmed`; plus payment-provider breakdown from
   `payment.link.clicked` / `payment.handle.copied`.

### 5a. Existing PostHog instance (recorded WS11)

A PostHog project and a first pass of auto-generated insights already exist —
created 2026-07-27 by `npx @posthog/wizard`, **not** hand-built to the §5
definitions above. Project **529917** (US Cloud).

| Asset | URL |
|---|---|
| Dashboard "Analytics basics (wizard)" | https://us.posthog.com/project/529917/dashboard/1909960 |
| Activation funnel (wizard) | https://us.posthog.com/project/529917/insights/25PU8gZi |
| Invite conversion funnel (wizard) | https://us.posthog.com/project/529917/insights/z2lmKB2J |
| AI parse success rate (wizard) | https://us.posthog.com/project/529917/insights/ibED0V0R |
| Settlement velocity (wizard) | https://us.posthog.com/project/529917/insights/6JKT8BVr |
| Expense creation by source (wizard) | https://us.posthog.com/project/529917/insights/WaF4MzPX |

⚠️ These are a starting point, not the contract. Each still has to be
reconciled against its §5 definition before the WS13 weekly metric review —
in particular the 48h conversion window on activation, and median (not mean)
`claim_age_hours` on settlement velocity. §5 wins where they disagree.

Nothing has been recorded into this project yet: the live bundle still carries
no `phc_` key (deployment.md §6.5, §40). The key exists in the owner's local
`frontend/.env.local` and needs pasting into Vercel.

## 6. Sentry

- **Frontend** (`lib/sentry.ts`): `@sentry/react`, statically imported so
  boot/white-screen errors are caught; errors-only (no tracing/replay);
  gated on `VITE_SENTRY_DSN`; router error boundary reports via
  `captureError`; URLs scrubbed by the same `sanitizeUrl` as analytics.
- **Backend** (`app/main.py`, since WS8): `sentry-sdk[fastapi]` 2.x, gated on
  `SENTRY_DSN` AND `ENVIRONMENT != "local"`; `send_default_pii=False`;
  `environment` tag added in WS10.6.
- Two separate Sentry projects (React + FastAPI) — one DSN each.

## 7. Privacy invariants (enforced in code + tests)

1. Identify by user UUID only; no email/name person properties, ever.
2. No autocapture, no session replay, no auto pageviews.
3. `sanitizeUrl` strips `/invite/{token}`, `/verify/{token}`,
   `/login/verify/{token}`, and `?code=` from every outbound URL property,
   Sentry request URL, and breadcrumb (unit-tested in `analytics.test.ts`).
4. Event properties never contain amounts, descriptions, group names, or
   payment handles.
5. Adding an event = add to `EVENTS` + this doc in the same change; nothing
   captures outside the taxonomy.
