# ClearDues Monetization Spec

**Created:** 2026-07-21 (WS10.5 — doc only, no code)
**Status:** ADOPTED — the accountable spec for every scope decision before Epic 6 / beta.
**Owner decision inputs:** market is GLOBAL / USD-first (2026-07-07); freemium,
organizer-pays, annual-first (held from S1 §5, ratified S9 §6.4).
**Source of record:** review Session 1 §5 (monetization model) + §6 (BYOK kill),
Session 2 §7 (subscription drivers) + §9 (metrics), Session 9 §6.4 (held as the
accountable spec). Where those differ, this file is now the merge.

> **Why this doc exists (S1 §5, S9 MP4):** no planning artifact mentioned pricing,
> tiers, paywall placement, or a conversion target — so no scope debate could be
> settled ("is feature X free or Pro?" had no answer). This is the one-page answer.
> It is a **decision framework, not an implementation**: no billing/subscription
> system is built yet (see §9). Numbers here align with what the code already
> enforces (§4) and set the target for what the paywall build will enforce later.

---

## 1. The model in one line

**Freemium · Organizer-pays · Annual-first · Global/USD-first.**
The one person per group who feels the pain (the Organizer) can pay to remove
friction; **everyone a Borrower does is free forever** so the network effect
survives. The Splitwise raid message — *"unlimited expenses, free, forever"* — runs
globally from launch and is a hard constraint on this spec, not marketing gloss.

**Three structural facts this model is built around (S1 §2):**
1. **You pay to remove limits, not for delight.** Splitwise only monetized by
   rate-limiting free *entries* and took a lasting reputation hit. We do the
   opposite and make it our wedge — manual entry is never gated.
2. **Success = user absence** ("Payment = Silence"). Usage is episodic (a trip, a
   dinner, a semester). → **Annual-first**; monthly is priced to be unattractive.
3. **Asymmetric willingness to pay.** The whole group must join; only the Organizer
   will pay. → **Never put friction on a Borrower.** Any charge on the debtor kills
   the network.

Highest-LTV segment is **roommates** (persistent, real money, monthly pain);
**trips** are the viral acquisition channel. Market to trips, convert the roommate
organizers caught in the net.

---

## 2. Pricing (USD-first)

| Plan | Price (USD) | Billing | Who it's for |
|---|---|---|---|
| **Free** | $0 | — | Everyone. Non-negotiable floor (§7). |
| **ClearDues Pro — monthly** | **$1.99 / mo** | recurring | The higher effective rate; episodic users churn between trips, so monthly is the impulse option, not the deal. |
| **ClearDues Pro — annual** | **$19.99 / yr** (~$1.67/mo, ≈16% off monthly) | recurring | The push. Survives the gap between trips and matches the roommate lease cycle; only ~$3.89/yr cheaper than paying monthly, so lean on "set-and-forget," not raw discount. |
| **Trip Pass** | **$4.99 one-time** | one-time | Full Pro for **one group, 90 days**. Converts trip organizers who will never subscribe. Note the deliberate inversion at these prices: Trip Pass ($4.99) covers a *whole group* for 90 days while personal Pro is $1.99/mo — it's positioned as "pay once, cover everyone, no subscription," not as a cheaper Pro. |
| **Group Pro** | = one Pro seat | recurring | One subscriber upgrades the **whole group's** Pro experience. Matches "I organize, I'll cover the app"; turns every Pro user into an in-group ad. |

**Anchoring:** Pro is set **aggressively below Splitwise Pro** (owner decision
2026-07-22 — $1.99/$19.99, undercutting S1 §5's $4.99/$39.99 starting point). At this
price the play is volume and a frictionless "yes," not margin-per-seat; the 2–4%
conversion target (§8) is what makes it work. Re-verify Splitwise's live price before
launch (§10). **Regional pricing is a post-PMF optimization**, not a launch decision
(S9 §6.1): USD everywhere at launch, with i18n-ready formatting already shipped
(`formatCurrency`, WS10.1). Group *ledger* currency is per-group and free; only the
*subscription* is USD-first.

---

## 3. Tier matrix

Free is generous by design. The **Enforcement** column is honest about today: only
the AI quota is a live, code-enforced gate (§4). Everything marked *planned* becomes a
gate when both the feature **and** the billing layer (§9) exist — until then it is
free-because-absent, not free-by-policy.

| Capability | Free | Pro | Enforcement today |
|---|---|---|---|
| Join / confirm / settle / view balances (everything a Borrower does) | ✅ | ✅ | **Free forever — never gated (§7)** |
| Unlimited groups | ✅ | ✅ | Live, free |
| Unlimited **manual** expense entry | ✅ | ✅ | Live, free (the anti-Splitwise wedge) |
| All 4 split modes (equal / unequal / % / exclude) | ✅ | ✅ | Live, free (built; table stakes) |
| Aggregate settle-up + pairwise balances | ✅ | ✅ | Live, free (WS6) |
| **Payment deep links + mark-as-paid at settle** | ✅ | ✅ | Live, **free** (WS10.2) — highest-intent value moment; gating it would be self-defeating |
| Invite preview + one-tap join (viral loop) | ✅ | ✅ | Live, free (WS10.3) |
| Activity feed + immutable audit log | ✅ | ✅ | Live, free |
| Strict-mode confirmation toggle | ✅ | ✅ | Live, free (WS6) — the *policy* is free; escalation *tuning* below is Pro |
| Per-group currency + Mediator-tone selector | ✅ | ✅ | Live, free (WS7/WS10.1) |
| **AI parsing (hosted)** | **20 / user / month** | **Unlimited** | **Live gate (§4).** Pro-unlimited path needs billing (§9) |
| BYOK (own Gemini key) | ✅ unlimited, unmetered | ✅ | Live, free — hidden power-user escape hatch (§4) |
| Level 1 nudges (gentle reminders) | ✅ | ✅ | Planned (WS12) — free |
| **Advanced nudge/escalation config** (policies, settlement cycles [FR19], quiet hours, per-member strictness) | ❌ | ✅ | Planned (WS12+) |
| **Recurring expenses** (rent, utilities — roommate anchor) | ❌ | ✅ | Planned (post-beta) |
| **Export** (CSV / PDF) | ❌ | ✅ | Planned (trivial gate) |
| **Receipt OCR** (line-item assignment) | ❌ | ✅ | Planned (Phase 2 — top Splitwise-Pro conversion feature) |
| **Spending insights / Agent's Monthly Report detail** | ❌ | ✅ | Planned (needs data history — S2 §7) |

**Pro's anchor feature is "unlimited AI entry."** It is simultaneously the single most
defensible subscription justification (AI cost is real, ongoing, and yours to control)
and the reason **default BYOK had to die** (S1 §6): BYOK gave that anchor away, kept no
margin, and inherited the support burden for keys you don't control. BYOK survives only
as a buried 1%-power-user gesture, never in onboarding.

---

## 4. The AI quota — the one live gate

**`AI_FREE_MONTHLY_PARSES = 20`** hosted parses per user per **calendar month**
(`backend/app/core/config.py:131`; enforced in `parser_service.consume_free_parse`,
429 on exhaustion). This spec's number **matches the code** — do not drift them apart.

- **Why 20:** enough to form the Smart-Input habit for a casual user; **exhausted by a
  heavy Organizer** — precisely the persona who converts. It is the natural
  free→Pro pressure point.
- **Why it's cheap to give away:** a flash-class parse costs ~**$0.0001–0.001** per
  call (S1 §6). 20 parses ≈ a fraction of a cent per user/month — noise next to
  Postgres/Render hosting. The quota exists to **create the gate**, not to cap cost.
  This makes the number safe to tune upward if activation data wants it.
- **BYOK is exempt** (their key, their bill) and **manual entry is unlimited** — so
  hitting the cap never blocks recording an expense (§5, soft gate). This is the
  network-effect guarantee in code form.
- **Sandbox onboarding parse (WS10.4) draws from the same 20** — no separate bucket.

**To turn this into revenue, the billing layer (§9) must add:** a Pro entitlement that
lifts the cap to unlimited, and the upsell copy on the 429 path (today's 429 is a plain
mediator "quota reached" message with no upgrade CTA).

---

## 5. Paywall placements (upgrade triggers)

Which screens surface the paywall, the trigger, the gate type, and the mediator-voice
copy tone. **Gate type matters:** *soft* = the feature degrades gracefully to a free
fallback (protects the network); *hard* = unavailable without Pro (fine for features
that don't exist on Free at all). **Never a hard gate on anything a Borrower touches.**

| # | Surface | Trigger | Gate | Copy tone (mediator voice) | Status |
|---|---|---|---|---|---|
| 1 | **Smart Input modal** | 21st AI parse in a month | **Soft** — manual entry stays available | "That's your 20 free AI entries for the month. Type this one in yourself, or go Pro for unlimited — the basics stay free either way." | **Live trigger (429); needs upsell CTA** |
| 2 | Group settings → recurring expense | Roommate schedules rent/utilities | Hard (feature absent on Free) | "Set it once, I'll log it every month — that's a Pro feature." | Planned (post-beta) |
| 3 | Group settings → Social Contract / nudge tuning | Editing escalation policy, settlement cycle, quiet hours, per-member strictness | Hard | "Fine-tune how hard I chase, per person — Pro." | Planned (WS12+) |
| 4 | Group screen → Export | Tap Export CSV/PDF | Hard | "Download the whole ledger — Pro." | Planned |
| 5 | Smart Input → attach receipt | Photo attach / OCR | Hard | "Let me read the receipt and split line by line — Pro." | Planned (Phase 2) |
| 6 | Dashboard → Insights / Monthly Report | Open the report detail | Hard | "Your month, and the work I saved you — the full report is Pro." | Planned (needs history) |
| 7 | **Trip Pass offer** | Trip-template group created, or nearing settle-up | Soft (contextual offer, not a block) | "Going Pro for just this trip? $4.99 covers the whole group for 90 days." | Planned |

**Placement principles:** (a) show the paywall **at the moment of intent**, never on a
cold settings page; (b) always name the free fallback in the same breath ("type it in
yourself"); (c) copy is calm and mediator-voiced — no dark patterns, no shame, no timed
pressure (Product Constitution, ux-design-spec-v2 §2). The 429/upsell copy passes
through `getApiErrorMessage` (WS8) so tone stays consistent.

---

## 6. Trip Pass & Group Pro — fitting the episodic reality

- **Trip Pass ($4.99, one-time, one group, 90 days):** the episodic segment (trip
  organizers) will *never* subscribe monthly, but will pay once to smooth one trip.
  Low cannibalization: recurring subscribers are the roommate segment, not the trip
  segment. Surface it on Trip-template groups (WS10.4 templates already tag these).
- **Group Pro (one seat upgrades the group):** matches the real social dynamic — the
  organizer covers the app for everyone. Every Pro user becomes an in-group
  advertisement, and it removes the "why should *I* pay when *they* benefit" objection.

Both are **add-ons to the same Pro entitlement**, not separate SKUs to build — the
billing layer (§9) models them as *scope of a Pro grant* (per-user vs per-group vs
time-boxed-per-group).

---

## 7. Non-negotiable free floor (network-effect protection)

These **never** move behind a paywall. Charging for any of them breaks the network the
whole product depends on (S1 §2, §5):

1. **Everything a Borrower does** — join, confirm, settle, dispute, view balances.
2. **Unlimited groups and unlimited manual expenses** — the anti-Splitwise wedge; this
   is the acquisition message, not a feature to erode later.
3. **Equal/unequal/% splits, aggregate settle-up, payment deep links, Level 1 nudges,
   activity feed, invite preview.** The entire *core loop* is free.
4. **A working amount of AI** (20/mo) — enough to experience the flagship feature.

If a future scope debate proposes gating any row here to hit a revenue number, the
answer is no — find the revenue in §3's Pro column instead.

---

## 8. Conversion target & guardrail metrics

**Primary target: 2–4% free→paid** (realistic for this category; S1 §5, S9 §6.4).
Annual-first — measure **annual** conversions as the real signal; monthly is expected
to churn between trips.

**Instrument before Epic 6 (WS10.6 wires PostHog/Sentry) — these numbers are currently
unmeasurable (S2 §9, S9 MP*):**

| Metric | Why | Kind |
|---|---|---|
| Free→Paid conversion (annual + monthly split) | The target itself (2–4%) | Revenue |
| **AI-quota-exhaustion rate** | The primary paywall's fuel — how many users even *reach* the cap | Leading indicator |
| Paywall view → upgrade rate, per surface (§5) | Which trigger converts; kill the ones that don't | Revenue |
| Activation funnel (group ≥2 members + ≥1 confirmed expense within 48h) | Conversion is meaningless without activation first | Health |
| **Invite → join rate** | Network-effect health; if a paywall dents this, the pricing is wrong | **Guardrail** |
| **Nudge mute / block rate** | Brand kill-switch (S1-W6) — a monetized nag that gets muted is worse than no nag | **Guardrail** |
| Settlement velocity (avg time-to-settle) | The PRD's core value proof and the Monthly Report's headline | Health |

**Guardrail rule:** if enabling a paywall measurably drops invite→join or spikes mute
rate, the gate is mispriced or misplaced — revert it before chasing the conversion
number. Revenue never wins against network health pre-PMF.

---

## 9. What this doc does NOT cover (deliberately out of scope)

- **No billing/payments integration is built.** No Stripe, no subscription entitlement,
  no Pro flag on the user, no receipts/invoicing. This spec is the *decision
  framework*; the **monetization build-out (paywall enforcement + billing) is Phase 4 /
  post-beta** (10-execution-plan §Phase 4). Beta ships **free-only** and instrumented —
  we measure willingness to pay before we collect it.
- **No feature is newly gated by this doc.** Marking a *planned* feature "Pro" in §3
  commits its eventual pricing; it does not build the gate. When the feature lands, its
  story inherits the gate from here.
- **Regional pricing, tax/VAT handling, currency of the subscription itself** — post-PMF
  (§2).

Landing this spec is the deliverable the review demanded before Epic 6 (S1 #8, S9
§6.4). It does not depend on any of the above being built.

---

## 10. Open decisions / re-verify before launch

1. **Splitwise Pro's live price** — $1.99/$19.99 was set to sit aggressively under
   Splitwise Pro. Re-check the current competitor price at launch; the gap is the point,
   so confirm we're still clearly under (and sanity-check we're not *so* cheap it reads
   as low-value).
2. **Group Pro scope mechanics** — does one Group Pro seat lift *every* member's AI
   quota, or only unlock group-level Pro features (export, nudge config)? Decide when
   the billing layer is designed; leans toward group-features + organizer's own
   unlimited AI, to avoid a cost blowout from N members parsing freely.
3. **Trip Pass vs Group Pro overlap** — Trip Pass is effectively "Group Pro, 90 days,
   one-time." Confirm they're one entitlement with different scopes at build time (§6).
4. **Quota tuning** — 20/mo is the launch number (matches code). Revisit against
   activation data: if too few users reach the cap, the paywall has no fuel; if
   activation suffers, raise it (cost headroom is large — §4).
5. **Annual discount depth** — currently ~16% ($19.99/yr ≈ $1.67/mo effective vs
   $1.99/mo). That's a thin gap; if annual take-rate is low, either widen it (drop the
   annual price) or accept that at these absolute numbers "set-and-forget" carries the
   annual, not the discount. A/B post-beta.

---

## Appendix — source traceability

| This spec | Review source |
|---|---|
| Freemium, organizer-pays, annual-first; free floor; **Pro $1.99/$19.99** (owner override 2026-07-22 of S1 §5's $4.99/$39.99); Trip Pass $4.99; Group Pro | S1 §5 (Monetization Strategy) |
| Kill default BYOK, keep as hidden escape hatch; hosted-AI quota as the gate; ~20 parses/mo | S1 §6 (BYOK) — implemented WS7 |
| Structural facts (pay-to-remove-limits, user-absence, asymmetric WTP); roommate=LTV, trip=viral | S1 §2–§4 |
| Subscription drivers (unlimited AI, nudge config, recurring, insights, Monthly Report, export, OCR) | S2 §7 |
| Metrics unmeasurable today; activation funnel; mute-rate kill switch | S2 §9 |
| Global market, USD-first pricing, regional pricing post-PMF | S2 §10, S9 §6.1 |
| "Held as the accountable spec"; 2–4% conversion; deliverable before Epic 6 | S9 §6.4 |
| Live quota number `AI_FREE_MONTHLY_PARSES = 20`, BYOK exempt | `backend/app/core/config.py:131`, `parser_service.py` (WS7) |
| Payment deep links free at settle | WS10.2 (`payment_providers`, `PaymentHandles`) |
| Per-group currency, `formatCurrency`, USD default | WS10.1 |
| Group templates tag Trip groups (Trip Pass surface) | WS10.4 (`features/groups/templates.ts`) |
