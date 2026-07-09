# Session 2 — Vision, Strategy & Roadmap Redesign

**Date:** 2026-07-06
**Scope:** Part 2 — vision completeness, personal expense tracking pillar, missing
flows, onboarding, retention, revised roadmap and MVP.
**Inputs read:** epics.md (full), epic retros (velocity + learnings), Session 1
findings (01-product-business-review.md).

---

## 1. Verdict Up Front

1. **Personal expense tracking: yes — but as a narrow "Quick Capture" wedge, not a
   second product.** It fixes your three weakest points (cold-start onboarding, the
   retention paradox, and the insights upsell) at low marginal cost, because the Smart
   Input pipeline is identical. But the moment you call it "personal finance" you enter
   a graveyard category and get judged against bank-sync apps. Section 3 has the exact
   scoping.
2. **A new CRITICAL product flaw surfaced in this session: settlement is modeled
   per-expense, but humans settle per-relationship.** A 23-expense trip requires 23
   claims + 23 confirmations to get square. This must be fixed before Epic 6 ships
   nudges, or the agent will nag people 23 times about one trip. Section 4.
3. **The most dangerous fact in the project is not on any roadmap: zero users, slowing
   velocity.** Epics 1–2.5 (17 stories) took ~2 weeks; Epic 3 (8 stories) ~4 weeks;
   Epic 4 (5 stories) ~3.5 months; Epic 5 is at 2/3 after ~5 weeks. Deployment is
   deferred ("bundled after Epic 5"), frontend tests are manual-only, and the PRD's
   success metrics have no instrumentation stories anywhere. At current velocity, the
   current plan delivers first user contact in 2027. The redesigned roadmap
   (Section 8) is built around one principle: **ship a private beta immediately after
   Epic 6 core, cut everything that doesn't serve that.**

---

## 2. Is the Product Vision Complete? (No — Three Gaps)

The documented vision (PRD): Smart Input → Social Engine → Trust Architecture, with a
"Financial Diplomat" north star. Good bones. Three structural gaps:

**Gap A — The vision ends at the exact moment the product's name begins.** "ClearDues"
promises *clearing*. But settlement is the least-designed pillar: per-expense claims,
double confirmation, no aggregate settle-up, no debt simplification, no payment links.
The loop the vision sells (entry → nudge → **cleared**) has a weak final act.
→ Promote **Settlement Intelligence** to an explicit fourth pillar.

**Gap B — Nothing brings a user back after silence.** "Payment = Silence" is the right
promise and a retention trap (Session 1, W8). The vision needs a reason for a
settled-up user to return.
→ Promote **Quick Capture (personal ledger)** to a fifth pillar — Section 3.

**Gap C — The moat is undefined.** NL parsing is commodity (Session 1, W7). The real
long-term moat is **behavioral data about what nudges work** — which tone, timing, and
escalation settles debts fastest per relationship type. No competitor has this data.
The vision should name it, and the instrumentation gap (Section 9) currently makes it
impossible to collect.

---

## 3. Personal Expense Tracking — The Direct Answer

### Should it become a core pillar? Yes — with strict framing.

**What's genuinely right about your instinct:**
- **It solves the cold-start problem.** Today a new user with no group and no friends
  on the app hits a dead end — the product is useless alone. Quick Capture gives solo
  value in the first 60 seconds, before any invite is sent. For a network product,
  single-player utility is the classic bootstrapping fix.
- **It solves the retention paradox.** Daily personal entries = daily habit = the app
  is open when the next shared expense happens.
- **Marginal cost is genuinely low.** A personal expense is a group expense with no
  group: same Smart Input, same parse, same list rendering, no splits, no
  confirmations, no nudges. Roughly one small epic.
- **The combined positioning is differentiated.** Splitwise doesn't do personal;
  personal-finance apps don't do splitting. "Every expense in one place — share the
  ones that are shared" is a real, unclaimed position.
- **The killer flow is capture-first, split-later.** Today the Smart Input demands a
  group up front. Real life: you enter "Paid 800 for groceries," and only later think
  "actually, half of that was the flat's." **Convert-to-shared** is the bridge feature
  that makes the two pillars one product instead of two tabs.

**What's dangerous about it (respect these or don't build it):**
- Personal finance is a graveyard: Mint is dead, the category is saturated with free
  tools, and users who hear "track your finances" expect bank sync, budgets, and
  reports. You have (correctly) scoped out Plaid. A manual-entry personal finance app
  in 2026 loses to every bank's own app.
- Focus: the agentic-mediation hypothesis is still unvalidated. Building pillar five
  before pillar two exists would be two half-products.

**The scoping contract (write these into the epic as explicit NON-goals):**
- No bank sync. No budgets. No net worth. No investment tracking. No charts in v1.
- v1 = groupless expenses + personal list + convert-to-shared + AI category tag
  (nearly free — the parser already reads descriptions) + one monthly total.
- Never market it as "personal finance." Market it as *capture*: "Type any expense in
  5 seconds. Share it later if it's shared."
- Insights/spending summaries come later as a **premium** feature, once months of data
  exist (this is the monetization payoff — Session 1's tier matrix gets its
  "insights" row from here).

**Sequencing:** after Epic 6 core + beta launch (see Section 8). It's an activation
and retention feature — those matter once real users exist, and beta feedback will
tell you whether solo capture or group mechanics need the next iteration.

---

## 4. NEW CRITICAL FINDING — The Settlement Model Doesn't Match Human Behavior

**Evidence (epics.md):** Settlement claims are per-expense (`POST
/api/v1/expenses/{expense_id}/settle`, Story 5.1), each requiring owner confirmation
(Story 5.2). Balances are net per group (Story 2.4), but there is no flow to settle a
*balance* — only individual expenses.

**Why this is critical:**
- A trip with 23 expenses where Sam owes Alex across 12 of them requires **12
  claim-swipes by Sam and 12 confirmations by Alex** to record what was, in reality,
  one bank transfer. Nobody will do this.
- Epic 6 will nag **per expense-debt**. Sam gets 12 nudges about one relationship.
  That converts "gentle mediator" into spam and triggers the PRD's own stop-signal
  (mute/block rates) through sheer mechanics, not tone.
- Splitwise settles per-relationship-balance for exactly this reason.

**Fix (before Epic 6 ships):** Add **aggregate settle-up**: "Settle with Alex" →
one claim covering the net amount across all confirmed expenses between the pair in
the group → one confirmation (or auto-confirm timeout, Session 1 W3) → all covered
splits marked settled atomically, one audit entry fan-out. The per-expense path you
built remains as the partial-payment edge case. Nudges must be **per-relationship
per-group**, never per-expense — write that into Epic 6 ACs now.

---

## 5. Missing User Flows (Inventory)

| # | Missing flow | Severity | Notes |
|---|---|---|---|
| F1 | **Invite landing preview** — invitee currently hits the "Walled Garden" login wall knowing nothing | CRITICAL | This is the viral loop's conversion point. Needs a public route: "Alex invited you to 'Goa Trip' — 4 members," THEN auth. One page, outsized impact. |
| F2 | **Aggregate settle-up** | CRITICAL | Section 4. |
| F3 | **Onboarding / first-run** — no epic or story anywhere; empty dashboard + an orb | HIGH | Section 6. |
| F4 | **Group end-of-life** — leave group, archive finished trip, delete group | HIGH | Trips END. There's no closure flow — also a missed wow moment (F12). |
| F5 | **Member exits with outstanding debt** — remove member / member leaves | HIGH | Undefined behavior; will happen in week one of any beta. |
| F6 | **Rejected-expense recovery** — Story 4.2 allows Reject, then... nothing | MEDIUM | Dead end: what does the creator see? Edit-and-resubmit loop is undefined. |
| F7 | **Push notification permission flow** — the product IS notifications; no story asks for permission, times the ask, or handles denial (email fallback) | HIGH | Ask after first confirmed expense, never on first load. |
| F8 | **Profile & preferences** — no stories for profile edit, currency, general notification prefs (6.5 covers only settlement cycle) | MEDIUM | |
| F9 | **Pairwise balance detail** — dashboard shows net per group; "who owes whom, exactly" breakdown is unspecified | MEDIUM | Prerequisite for F2 UI. |
| F10 | **Post-confirmation edit / dispute** — FR9 covers who edits; nothing covers editing after finalization | MEDIUM | Immutable + wrong = dispute flow needed eventually; document the v1 answer ("delete & recreate" is fine if stated). |
| F11 | **Currency selection** — "Rs" is hardcoded into BalanceDisplay ACs (Story 2.5.6) | MEDIUM | RESOLVED 2026-07-07: market is GLOBAL. Currency becomes a per-group setting + `formatCurrency` util (see S9 §6.1). |
| F12 | **Trip closing ceremony** — "everyone's settled" group summary (totals, biggest spender, shareable card) | LOW (high upside) | The single best organic-sharing artifact this product can produce. |

---

## 6. Onboarding — Design the First 60 Seconds

There is currently no onboarding design at all. The target experience:

1. **Invitee path (most common entry!):** WhatsApp link → public preview (F1) →
   one-tap OAuth → lands *inside the group* seeing real expenses. Time-to-value: ~15s.
   Never route an invitee through a generic empty dashboard.
2. **Organic path:** first screen offers "Try it — type an expense." Sandbox parse
   (hosted AI — this entire flow is impossible under BYOK, which is why Session 1's
   fix is a launch blocker). The parse IS the aha moment; let it happen before any
   setup.
3. **Group creation templates:** "Roommates / Trip / Dinner" chips that preset the
   social contract (strict-mode off, nudge policy, settlement cycle) instead of
   asking configuration questions.
4. **Push permission** requested after the first confirmed expense — the moment the
   user has something to be notified about (F7).
5. **Empty states as tutorial:** every empty screen names the one next action.
   (Hand off to Session 8 for design treatment.)

---

## 7. Retention, Wow Moments, and Subscription Drivers

**Retention (in priority order):**
1. Quick Capture daily habit (Section 3).
2. Recurring expenses — roommate segment (Session 1, W5).
3. **The Agent's Monthly Report:** "Your March: Rs 23,400 shared across 2 groups. I
   sent 4 reminders so you didn't have to. Average settle time: 2.1 days." The agent
   showing its own work is retention + brand + the single best subscription
   justification in the product. Cheap to build once instrumentation exists.
4. Group digest notifications (weekly summary in lieu of per-event noise).

**Wow moments (ranked by shareability):**
1. First AI parse with streaming commentary (exists — must be free & instant).
2. **"Your dues were cleared — you never had to ask."** The notification when a nudge
   works. This is the brand promise made visible; it currently isn't planned anywhere.
   Add to Epic 6.
3. One payment clears N debts (aggregate settle + simplification).
4. Trip closing ceremony with shareable summary card (F12).
5. Invite preview → inside the group in two taps.

**Subscription drivers** (extends Session 1 tier matrix): unlimited AI, nudge policy
customization, recurring expenses, insights from capture data, monthly report detail,
export, Trip Pass. Nothing new needed here — the point is these all *depend* on
hosted AI + instrumentation landing first.

---

## 8. Redesigned Roadmap

Principle: **the next milestone is not an epic — it's first contact with real users.**
Everything is sequenced by "does this block a 10-group private beta?"

**Phase A — Close the loop (now → ~4 weeks):**
- Story 5.3 settlement audit trail (finish — small).
- **NEW Story 5.4: Aggregate settle-up** (Section 4 — do not enter Epic 6 without it).
- **NEW Story 5.5: Settlement auto-confirm timeout** (72h, owner can dispute).

**Phase B — The differentiator, slimmed (Epic 6 core):**
- 6.1 Celery infra, 6.2 Level 1, 6.3 Level 2 (re-scoped to per-relationship, not
  per-expense), 6.4 Snooze.
- NEW 6.6: Push permission flow + email fallback (F7).
- NEW 6.7: "Cleared without asking" success notification (wow #2).
- **Defer:** 6.5 settlement cycles (premium, later). **Defer Level 3 entirely**
  (Session 1, W6).

**Phase C — Launch blockers (new epic; most items are small):**
- Hosted AI + free quota; BYOK demoted to hidden setting (Session 1 #1).
- Strict-mode toggle: confirmation becomes per-group opt-in (Session 1 W2).
- Invite public preview page (F1).
- Payment deep links at settle time (Session 1 W4).
- Product analytics + event taxonomy matching PRD metrics (Section 9).
- Fix the pytest-blocking SQLAlchemy bug; minimal CI; deploy pipeline to Railway.
  (Details belong to Sessions 3 & 6 — listed here because they gate launch.)
- **→ PRIVATE BETA: 5–10 real groups (your own trips/flat + friends).**

**Phase D — Post-beta, informed by real usage:**
- **NEW Epic: Quick Capture** (Section 3 scope: groupless expense, personal list,
  convert-to-shared, AI category tag, monthly total).
- **NEW Epic: Roommate Pack:** recurring expenses, monthly digest, debt
  simplification across group.
- Monetization build-out: quota paywall, Pro tier, Trip Pass (per Session 1).

**Phase E — Later:**
- Epic 7 slimmed: keep 7.1/7.2 (offline read cache — cheap); **cut 7.3–7.5** (offline
  mutation queue + conflict resolution) until users demand it. Highest-bug-risk code
  in the plan, serving the rarest scenario.
- Receipt OCR (premium anchor), multi-currency, group archive ceremony (F12, could
  move earlier — it's cheap), Epic 8 minus 8.1 (personality selector stays cut;
  accessibility work should be continuous, not an end-phase audit).

**Revised MVP definition** (replaces "Epics 1–7"): *Epics 1–5 as built + Epic 6 core +
Phase C launch blockers.* Explicitly OUT of MVP: offline writes, settlement cycles,
Level 3, personality selector, percentage/share splits (already built — fine, but
they'd not make this cut again).

---

## 9. The Instrumentation Gap (CRITICAL, invisible until launch)

The PRD defines precise success criteria — settlement velocity +20%, edit rate <10%,
escalation efficacy, mute/block stop-signal — and **not one story in any epic collects
any of them.** There is no analytics integration, no event taxonomy, no funnel
definition. The PRD's own kill-switch metric (mute rates on agent notifications)
cannot be observed.

Required (Phase C): lightweight product analytics (e.g., self-hosted PostHog — fits
the Docker/Railway stack), an event taxonomy mirroring the Redis event names
(`domain.entity.action` — the convention already exists, reuse it), and one activation
definition to rally around. Suggested: **activation = user is in a group with ≥2
members and ≥1 confirmed expense within 48h of signup.**

---

## 10. Strategic Risk Register (new items surfaced this session)

| Risk | Why it matters | Mitigation |
|---|---|---|
| **iOS PWA push fragility** | The product IS notifications. On iOS, web push requires 16.4+ AND add-to-home-screen first; delivery is less reliable than native. The core value prop degrades on half the world's premium phones. | RESOLVED direction (S9 §6.1): email ships as a first-class nudge channel beside web push from day one; Capacitor native wrapper only if beta data demands it. Do not discover this in beta. |
| **Market ambiguity** | "Rs" hardcoded (2.5.6) conflicts with the product's global intent; different markets have different payment rails and pricing power. | RESOLVED 2026-07-07: market is GLOBAL. Currency = per-group setting + `formatCurrency`; payment deep links = user-configurable registry with a universal "mark as paid" fallback; USD-first pricing, regional pricing post-PMF. |
| **Velocity decay** | 17 stories in 2 weeks → 5 stories in 3.5 months. If unaddressed, the redesigned roadmap dates are fiction too. | Sessions 3–4 will look for causes (test suite broken → manual verification tax is the prime suspect). Treat the pytest fix + CI as velocity investments, not chores. |
| **Zero-feedback building** | 32 stories, 0 users. Every subsequent story compounds unvalidated assumptions. | Phase C beta is the fix; resist any scope addition that delays it. |

---

## 11. Future Epic Ideas Backlog (beyond Phase E — parked, not planned)

- **Messaging-bot interface (WhatsApp/Telegram)** — enter expenses & receive nudges
  where the group already talks; high-leverage acquisition wherever groups organize
  over chat.
- Receipt OCR with line-item assignment ("who had the steak").
- Debt simplification across groups (global netting).
- Group "social contract" presets marketplace (strictness/tone bundles).
- Shared subscriptions tracker (Netflix/Spotify splits — recurring + reminder synergy).
- Insights premium tier (needs Quick Capture data history).
- Financial Diplomat (PRD north star): auto-negotiated settlement plans.

---

## 12. Handoffs to Later Sessions

- **Session 3 (backend):** verify settlement schema can support aggregate claims
  (claim ↔ multiple splits); assess pytest blocker + CI as velocity fixes; check event
  naming consistency for the analytics taxonomy.
- **Session 6 (infra):** Railway deploy pipeline is a launch blocker (Phase C); iOS
  push architecture decision; PostHog hosting.
- **Session 8 (UX):** onboarding first-60-seconds flows (Section 6); invite preview
  page; empty-state system; trip-closing ceremony design; Orbital Nav
  discoverability risk in the invitee path (a first-time invitee must find their way
  with zero chrome — stress-test this).
- **Session 9 (synthesis):** hold the final action plan accountable to Phase C as the
  next milestone; scores should weight the zero-users fact heavily.
