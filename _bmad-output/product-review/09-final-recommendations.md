# Session 9 — Final Synthesis & Action Plan

**Date:** 2026-07-07
**Scope:** Part 8 — scores, biggest problems/opportunities, feature add/remove, GTM
strategy, impact-vs-effort prioritized action plan.
**Inputs:** Findings files 01–08 only (per plan — no source code re-read). Citations use
`S{n}` for session files and the finding IDs defined there (e.g., `S3-C1`, `S8-UX-C2`).

---

## 1. The One-Paragraph Verdict

ClearDues is **a genuinely good product thesis wearing a costume of a finished product.**
The insight (social friction, not arithmetic, is the unsolved problem — S1) is defensible
and unclaimed; the design identity (warm-minimal palette, the Orb, mediator voice,
Payment = Silence — S8) is real IP. But after 32 "done" stories: no user can create an
expense through the UI (S4-C1), the flagship AI feature is a mock on the frontend and
broken three independent ways on the backend (S4-C2, S3-C1/C2), the differentiator
(Epic 6) has neither code nor infrastructure substrate (S3-H1, S6-H2), the test suites
have never run (S3-C3, S4-C3), all 13 CI workflows are dead (S6-C1), nothing has ever
been deployed, and there are zero users. The single most important fact about this
project is that **every quality gate it believes it has is fictional**, and the single
most important milestone is **first contact with real users (the Phase C private beta,
S2 §8)**. Everything below is organized around those two facts.

---

## 2. Scores

Weighting note (per S2's handoff): scores weight the zero-users, zero-deployments
reality heavily. A component that exists but is unreachable by any user scores as
not existing.

| Axis | Score | Basis |
|---|---|---|
| **Product — thesis & strategy** | **7 / 10** | Agentic mediation + trust architecture is a real, defensible, unclaimed position (S1). Docked for: differentiator sequenced last (S1-W1), settlement model that fights human behavior (S2 §4), no monetization artifact anywhere (S1 §5), retention paradox unaddressed (S1-W8). |
| **Product — as shipped** | **1.5 / 10** | Core loop inoperable end-to-end (S4-C1/C2/C4, S3-H7); "done" means component-complete, not user-complete, across Epics 2.5–5 (S4 §1, S8 §9). Post-review fixes (bottom nav, token repair, modal crash) lifted this from ~1. |
| **Architecture** | **3.5 / 10** | Micro-level craft is real (Decimal money, hashed tokens, batch queries — S3 §1); macro level is dishonest: real-time/worker tier is fiction on paper, in code, and in compose (S3-H1, S6-H2), money-path invariants broken (S3-H2/H3/H4/H5), docs describe a stack that doesn't exist (S7-C1). |
| **Design** | **4.5 / 10** | Spec 7/10, implemented 2/10 at review time (S8); same-day post-review fixes resolved the two verified showstoppers (tokens, orbital nav) and the never-opening modal, moving implemented reality to ~3.5–4. Brand floor still absent (S8-UX-H1); IA still not the spec's (S8-UX-H2). |
| **Security** | **3.5 / 10** | Magic-link auth genuinely solid; everything around it is not (S5 §1): triple-duty SECRET_KEY with data-bricking default (S5-C1), unpinned crypto deps that silently re-resolve in Docker (S5-C2, S6-H1), 30-day JWT in URL (S5-H1), public Adminer in prod compose (S5-H3), live template password stack (S5-H5). |
| **Infrastructure & operability** | **2.5 / 10** | Dead CI, no backups, three contradictory deploy paths, no monitoring (S6-C1/C2/C3, H3). Good local dev — all inherited. ~4 dev-days from a deployable beta stack once code fixes land (S6). |
| **Documentation** | **4 / 10** | AI-facing docs ~7/10 (best-in-repo); human-facing ~1.5/10 — unedited template debris, CLAUDE.md materially false with OVERRIDE authority (S7-C1), docs that teach the Alembic bug (S7-H2). |
| **Business readiness** | **2 / 10** | No pricing, tiers, paywall placement, or conversion target exists in any artifact (S1 §5); BYOK simultaneously kills onboarding and gives away the premium gate (S1 §6); "Rs" hardcodes spread through 8+ files with no currency abstraction for a global product (S2 §10, S4-M3); PRD success metrics have zero instrumentation (S2 §9). |
| **Subscription viability** | **5 / 10 today → ~7 / 10 achievable** | Narrowly yes (S1 §2): organizer-pays, annual-first, freemium with hosted-AI quota as the gate, Trip Pass for the episodic segment. Conditional on killing default-BYOK, shipping Epic 6 (the thing people would pay for), and instrumentation. Without those three, it is 2/10 — there is currently nothing to charge for and no way to measure willingness to pay. |
| **Overall project health** | **3 / 10** | Strong thesis, strong design identity, above-average per-component craft — invalidated by fictional quality gates, an inoperable core loop, an unbuilt differentiator, and zero external contact. Recoverable: almost every CRITICAL is small and local. |

---

## 3. The Five Meta-Problems (what the 100+ findings collapse into)

Every session found the same disease in a different organ. Fixing findings one at a
time without naming the diseases guarantees recurrence.

### MP1 — The definition of done is fiction (root cause of ~70% of all findings)
No automated gate has ever run (S6-C1). 193 backend tests cannot execute (S3-C3);
1,356 lines of frontend tests never compiled (S4-C3); `npm run typecheck` fails today;
no story was ever visually verified (S8 — invisible text shipped for ~5 months);
sprint-status's own "BLOCKER for Epic 4" was bypassed silently (S7-M4). Stories pass
"code review" as components and are never connected into user-reachable flows (S4 §1).
**Fix class:** process, not code — see Action Plan Phase 0. This is the highest-leverage
work in the entire review.

### MP2 — The differentiator does not exist, and nothing under it does either
Epic 6 is the product (S1-W1). It has: no code (S3-H1), no Redis/Celery/scheduler in
any compose file, `redis`/`celery` not even declared dependencies (S6-H2), a dead event
publisher that silently no-ops (S3-H1), and — critically — a settlement model that would
make the agent spam users 12 times per relationship per trip (S2 §4). The "stop signal"
hypothesis the whole product rests on remains unvalidated. **Fix class:** re-sequenced
roadmap (S2 Phases A–C) + aggregate settle-up before any nudge ships.

### MP3 — The ledger cannot be trusted, in a product selling trust
Editing an amount orphans splits (S3-H2); rejection rewrites confirmed splits and
converts split types (S3-H3); settlement rejection returns stale state (S3-H4); audit
entries can be silently lost across multi-commit operations (S3-H5); account deletion
either 500s or cascade-deletes other people's financial records (S3-C4); dashboard
balances are float; there are no backups of any kind (S6-C2). **Fix class:** a
"ledger integrity" workstream — mostly hours-to-days each, non-negotiable before beta.

### MP4 — The business model is self-defeating as configured
BYOK gates the flagship feature behind obtaining a Google API key (>95% of mainstream
users will never activate it — S1 §6), hands away the single best subscription
justification, and doesn't even work (no endpoint to save a key — S3-C2). Meanwhile
mandatory confirmation ceremonies (S1-W2/W3) add friction Splitwise doesn't have, and
no monetization artifact exists to arbitrate scope decisions. **Fix class:** hosted AI
+ quota as default, strict-mode/auto-confirm policies, one-page monetization spec.

### MP5 — The project is dressed as another product
Login footer says "Full Stack FastAPI Template - 2026" (S8-UX-H1); README, SECURITY.md
(routing vuln reports to tiangolo), release notes, deployment docs are all the unedited
template (S7); a parallel password-auth stack, /admin, /items are live attack surface
(S4-H2, S5-H5); ~2,500+ lines of template code ship in the bundle. **Fix class:** one
deletion-heavy purge pass — cheap, and a prerequisite for showing the app to anyone.

---

## 4. The Five Biggest Opportunities

1. **Splitwise's self-inflicted wound.** The category leader monetized by rate-limiting
   free expense entries and took a lasting reputation hit (S1 §2). "Unlimited expenses,
   free, forever" is a direct raid message that costs nothing — it's already the plan.
2. **An unclaimed position.** No incumbent chases the money for you (agentic mediation),
   and none combines shared + personal capture ("every expense in one place — share the
   ones that are shared," S2 §3). Both halves are articulated and neither is built.
3. **The behavioral-data moat.** Which tone/timing/escalation settles debts fastest per
   relationship type — no competitor has this data, and it compounds (S2 Gap C). Requires
   the instrumentation that currently doesn't exist; name it in the vision.
4. **Design identity as brand IP.** The palette, the Orb, amber-settled/never-red,
   mediator voice, silence-as-reward — S8 verified these are distinctive and mostly
   cheap to surface. The risk was concentrated in the novelty features (orbital nav,
   roast mode, auto-confirm), which are now removed or removable.
5. **Small fixes, outsized visible quality.** The review demonstrated this live: the two
   worst UX defects (~5 months old) were fixed in one day post-review. The infra gap is
   ~4 dev-days (S6); docs ~1.5 (S7). The distance between "embarrassing" and "credible
   beta" is weeks, not quarters — *if* velocity is protected by MP1's fix.

---

## 5. Feature Triage (consolidated add / keep / cut)

### Add before beta (Phase A–C; all small unless noted)
| Feature | Why | Effort |
|---|---|---|
| **Aggregate settle-up** ("Settle with Alex", net across expenses) | Blocks Epic 6 — without it the agent spams per-expense (S2 §4, CRITICAL) | Medium |
| **Hosted AI + free quota (~20 parses/mo); BYOK demoted to hidden setting** | Unblocks onboarding AND creates the premium gate (S1 §6); build this *instead of* the missing BYOK endpoints — don't pay twice (S3-C2) | Small–Medium |
| **Strict-mode toggle** (confirmation opt-in per group) + **settlement auto-confirm after 72h** | Removes the two friction ceremonies vs Splitwise (S1-W2/W3); the built workflows remain as strict mode | Small |
| **Invite public preview page** | The viral loop's conversion point; currently a login wall (S2-F1, CRITICAL) | Small |
| **Payment deep links** (configurable registry: Venmo, PayPal.Me, Cash App, Revolut, UPI, … + universal "mark as paid" fallback) at settle time | Highest-intent moment (S1-W4) | Small |
| **Push permission flow + email fallback** | The product IS notifications; ask after first confirmed expense (S2-F7) | Small |
| **Product analytics + event taxonomy + activation metric** | PRD success metrics and the mute-rate kill-switch are currently unmeasurable (S2 §9) | Small–Medium |
| **"Cleared without asking" success notification** | The brand promise made visible; wow moment #2 (S2 §7) | Small |

### Add post-beta (Phase D, informed by real usage)
Quick Capture pillar (groupless expense + convert-to-shared + category tag + monthly
total, with S2 §3's strict non-goals: no bank sync, no budgets, never "personal
finance"); Recurring expenses (roommate LTV segment — S1-W5); Debt simplification
(most-loved competitor feature, pure math — S1); Agent's Monthly Report (best
subscription justification in the product — S2 §7); Trip closing ceremony (cheap,
best organic-sharing artifact — S2-F12); Receipt OCR (premium anchor, Phase 2).

### Keep, stop investing
Four split modes (sunk cost); WebSocket real-time as an NFR (refetch-on-focus is 95% of
the value — build the Redis/worker tier for Epic 6's *scheduler* needs, not for <200ms
sync); component-level polish on already-good components.

### Cut / defer / delete
| Item | Action | Basis |
|---|---|---|
| **BYOK as default** | Demote to hidden power-user setting | S1 §6 — strongest recommendation in the review |
| **AI Personality Selector (8.1)** | Cut from roadmap | Pre-PMF vanity (S1) |
| **Level 3 "Social Pressure"** | Defer; per-member opt-in + mute telemetry required to revisit | Brand-killing scenario (S1-W6, S8-UX-H5) |
| **F3-PBS "roast mode" / "no boundaries" language** | Excise from all artifacts; cap personality at Funny for MVP | Contradicts the product's own constitution (S8-UX-H5) |
| **3-second auto-confirm** | Manual confirm only for MVP | Auto-committing money records on a timer (S8-UX-H6) |
| **Offline mutation queue (7.3–7.5)** | Defer indefinitely; keep read-only offline cache (7.1/7.2) | Highest-bug-risk code serving the rarest scenario (S1, S2 Phase E) |
| **Settlement cycles (6.5)** | Defer to premium build-out | S2 Phase B |
| **Template surface** (password auth, /admin, /items, /private, branding, sidebar, DataTable, release-notes, img/) | Delete (~1 day, mostly `git rm`) | S4-H2, S5-H5, S7-M6 |
| **Dead code wearing the architecture's uniform** (event publisher, notify stub, Swarm deploy script, 12 of 13 workflows, Hidden Nav spec section) | Delete now | S3-H1, S6-C3/L2, S8-UX-H3 |
| **Adminer in production compose** | Remove | S5-H3 |

---

## 6. Go-to-Market Strategy

### 6.1 Market: global from day one (DECIDED 2026-07-07)
ClearDues targets a global market — anyone, anywhere. This resolves Session 2's
"market ambiguity" risk and converts it into three concrete engineering requirements
that must land before beta:

1. **Currency becomes data, not branding.** The hardcoded "Rs" (8+ files, plus the UX
   spec framing it as a *brand standard* — S4-M3, S8-UX-M5) is now a defect class: one
   `formatCurrency` util + a per-group currency setting (locale-detected default),
   ISO-4217 codes end-to-end, `Intl.NumberFormat` driven by the user's locale. No
   currency string is ever hardcoded again.
2. **Payment deep links are a registry, not a rail.** Settle-up offers whatever the
   users configure (Venmo, PayPal.Me, Cash App, Revolut, UPI, IBAN copy, …) plus a
   universal "mark as paid" fallback — the highest-intent moment works in every market
   with zero per-market builds.
3. **Notification channels must not assume any one platform.** iOS PWA push is fragile
   (S2 §10), so email ships as a first-class nudge channel beside web push from day
   one; revisit a native wrapper (Capacitor) only if beta data demands it.

Copy and pricing are English/USD first with i18n-ready formatting throughout; regional
pricing is a post-PMF optimization, not a launch decision. The Splitwise-raid message
("unlimited expenses, free, forever") runs globally from launch.
*Impact: every currency, payment, and channel decision becomes decidable. Effort: the
decision is made; the currency/payment-registry work is costed in Phase 2.4.*

### 6.2 Positioning
Lead with the nag engine, never the AI entry (NL parsing is commodity — S1-W7):
**"The app that asks for the money so you don't have to."** Secondary: "The basics are
free, forever" (anti-Splitwise). The trust architecture (immutable audit, visible edit
history) is the proof layer under both claims — market what's already built.

### 6.3 Motion: beta → loop → segments
1. **Private beta (the next milestone, non-negotiable):** 5–10 real groups from the
   team's own trips/flat/friends. Success = the activation metric (user in a group with
   ≥2 members and ≥1 confirmed expense within 48h — S2 §9) plus the PRD's settlement-
   velocity and mute-rate metrics, all instrumentable only after the analytics story.
2. **The viral loop is the growth engine:** every group invite is an acquisition event.
   The deep-link invite exists (Story 2.2); the preview page (S2-F1) is what converts
   it. Instrument invite→join→activation as the one funnel that matters.
3. **Trips acquire, roommates pay** (S1 §3): market to trip season, convert the
   roommate organizers caught in the net. Recurring expenses is the retention feature
   that makes the roommate segment stick — schedule it immediately post-beta.

### 6.4 Monetization (from S1 §5, held as the accountable spec)
Freemium, organizer-pays, annual-first. Free forever: everything a borrower does,
unlimited groups and manual expenses, equal splits, Level 1 nudges, ~20 AI parses/month.
Pro ($4.99/mo, $39.99/yr, anchored just under Splitwise Pro, annual pushed hard):
unlimited AI, nudge/escalation policy customization, recurring expenses, insights (once
Quick Capture data exists), export, receipt OCR later. Plus **Trip Pass** (one-time,
90 days, one group) for the episodic segment and **Group Pro** (one subscriber upgrades
the whole group). Target 2–4% free→paid. **Deliverable before Epic 6: the one-page
monetization spec (tier matrix, quota numbers, paywall placements, conversion target)**
— it does not exist and every scope debate needs it (S1 §5).

---

## 7. Prioritized Action Plan (impact × effort)

Sequenced by one principle (S2): *does this block a 10-group private beta?* Estimates
assume the S3–S8 per-finding numbers; "d" = dev-days. Phases are strictly ordered;
items within a phase can interleave.

### Phase 0 — Make "done" mean something again (~2 d, do before ANY new story)
| # | Action | Impact | Effort | Source |
|---|---|---|---|---|
| 0.1 | Fix `Optional["GroupSettings"]` annotation + `db_session`→`db` fixture; triage first honest test run | Un-bricks all 193 backend tests | 0.5 d | S3-C3 |
| 0.2 | Install vitest/RTL + config; make `npm run typecheck` green | Un-bricks 1,356 lines of frontend tests; restores the documented verify command | 0.5 d | S4-C3 |
| 0.3 | Root-level `.github/workflows/ci.yml` (working-directory: cleardues): backend pytest, frontend typecheck+build, uv-lock freshness check | Converts S3/S4/S5-class rot from chronic to impossible — highest process ROI in the review | 0.5 d | S6-C1, S6-H1 |
| 0.4 | DoD amendments: (a) suite green in CI required; (b) UI stories attach 375px+1280px screenshots + axe smoke; (c) story is done only if the feature is *user-reachable* from app entry; (d) no epic closes past a live BLOCKER note | Kills MP1 at the workflow level, not per-bug | 0.25 d | S3 §9, S8 §10, S7-M4 |
| 0.5 | Rewrite CLAUDE.md: status delegated to sprint-status.yaml, real stack, caveat/remove broken commands | Every future AI session works from true context | 0.25 d | S7-C1 |

### Phase 1 — Ledger integrity + an operable core loop (~3 weeks)
| # | Action | Impact | Effort | Source |
|---|---|---|---|---|
| 1.1 | Money-path fixes as one product decision ("any amount/participant change reverts to DRAFT and re-opens consent"): expense-edit recalc, reject semantics, settlement-rejection status | Ledger becomes trustworthy — the whole game for this product | 2–3 d | S3-H2/H3/H4 |
| 1.2 | One-transaction-per-request refactor; audit entries atomic with operations | The "immutable audit trail" claim becomes true | 1–2 d | S3-H5 |
| 1.3 | Soft-delete/anonymize users; FK policy migration | Closes the destroy-other-people's-records path | 1 d | S3-C4, S5-M5 |
| 1.4 | Ledger read endpoints (GET expense, list group expenses, splits, group detail) + `/groups/$groupId` route + mount Story 5.1 UI + group-scoped claims | The app can finally display what it stores; unblocks Epic 5 end-to-end | 3–4 d | S3-H7, S4-H3/C4/M6 |
| 1.5 | Wire expense entry: group selector / per-group mount, thread groupId | The core loop becomes operable | 1–2 d | S4-C1 |
| 1.6 | **Aggregate settle-up** (net per relationship per group, atomic fan-out, per-expense path kept for partial payments) + 72h auto-confirm | Prerequisite for Epic 6 not being spam | 3–4 d | S2 §4 |
| 1.7 | Real AI path, hosted-key-first: fix swapped args, server-key resolution + per-user quota counter, async Gemini client + timeout, real SSE client + auth-context user, delete the mock | FR1 exists for the first time; the premium gate exists | 4–5 d | S3-C1/C2/H8, S4-C2, S1 §6 |
| 1.8 | Secrets/key hygiene: dedicated ENCRYPTION_KEY + fail-fast pinning, `uv lock` + `--locked` in Dockerfile, bump starlette/authlib/sentry | Removes the data-bricking and supply-chain landmines | 1 d | S3-C5, S5-C1/C2/H4, S6-H1 |
| 1.9 | Restrict auto-logout to 401; mediator-voice error mapper | Permission denials stop destroying sessions; the brand gets a voice where users actually meet it | 0.5 d | S4-H1, S8-UX-H4 |

### Phase 2 — Launch blockers (~2 weeks)
| # | Action | Impact | Effort | Source |
|---|---|---|---|---|
| 2.1 | Template purge: password-auth routes/models, /admin, /items, /private, components, branding, favicon, footer, greeting + brand floor (logo, titles) | Attack surface halved; the app becomes ClearDues | 2 d | S4-H2, S5-H5, S8-UX-H1 |
| 2.2 | Security pass: OAuth token via one-time code or HttpOnly cookie, rate limiting on auth+AI, security headers, allow_credentials off, email_verified check, invite→POST + revocation | Closes every remaining S5 HIGH/MEDIUM that touches beta users | 3 d | S5-H1/H2/M1/M3/M4/M6 |
| 2.3 | Deploy: commit to compose-on-VPS for beta (delete Swarm + Railway claims), nightly pg_dump→object storage + tested restore, uptime monitor, log rotation, image hardening (non-root py3.13-slim, npm ci, limits), remove Adminer from prod, env_file scoping, extract cleardues/ to its own repo, rotate the PAT | A deployable, backed-up, monitored stack — first deploy ever | 4 d | S6 §Recommended Path |
| 2.4 | Growth wiring: invite preview page, strict-mode toggle, currency setting + `formatCurrency` util (kills the "Rs" hardcodes), payment deep links (configurable registry), push permission flow, analytics (PostHog) + event taxonomy + activation funnel | The beta can convert, retain, and be measured — globally | 5–6 d | S2-F1/F7/F11, S1 #3/#5, S2 §9 |
| 2.5 | Docs floor: root README + LICENSE, SECURITY.md contact, backend README rewrite, runbook, reconcile tracking numbers, bless the one API-client pattern | The repo survives its first external reader | 1.5 d | S7 top-10 |
| 2.6 | Replace 4 stale Playwright specs with 3–4 magic-link-aware smoke journeys; PWA install shell (manifest + icons + SW) | Real e2e coverage of real flows; "installable" stops being fiction | 2 d | S4-H5/H4 |
| 2.7 | Write the monetization spec (global market, USD-first pricing, currency-aware) | Every future scope call becomes decidable | 0.5 d | S1 §5, S2 §10 |

### Phase 3 — Epic 6 core, then BETA (~2–3 weeks)
| # | Action | Impact | Effort | Source |
|---|---|---|---|---|
| 3.1 | Provision Redis + Celery worker + beat in compose; delete dead publisher; adopt the event envelope for real | The differentiator gets a substrate | 1 d | S6-H2, S3-H1 |
| 3.2 | Nudge engine Levels 1–2, **per-relationship per-group** (never per-expense — written into ACs), snooze, quiet hours | The product's reason to exist ships | 8–10 d | S2 Phase B |
| 3.3 | "Cleared without asking" notification; mute/block-rate telemetry wired to the PRD kill-switch | The brand promise made visible; the stop signal observable | 1 d | S2 §7/§9 |
| 3.4 | **→ PRIVATE BETA: 5–10 real groups.** Weekly metric review against activation, settlement velocity, mute rate | First contact with reality after 47 stories | — | S2 §8 |

### Phase 4 — Post-beta (sequenced by beta data)
Quick Capture epic (S2 §3 scope contract) → Roommate Pack (recurring expenses, debt
simplification, monthly digest) → monetization build-out (quota paywall, Pro, Trip
Pass) → Agent's Monthly Report → trip closing ceremony → receipt OCR. Group
end-of-life and member-exit flows (S2-F4/F5) should be pulled forward the moment beta
groups hit them — they will, in week one.

**Total to beta: roughly 40–45 dev-days of focused work (~8–9 working weeks solo).**
The honest caveat: Epic 4 alone took 3.5 months (S2). The velocity bet is Phase 0 —
working gates and a runnable suite are what turn the estimate from fiction into a plan.
If velocity doesn't recover after Phase 0–1, cut Phase 2 scope (PWA shell, parts of
2.4) before ever cutting Phase 3: **shipping nudges to 10 real groups is the only
result that validates or kills this product.**

---

## 8. Risks to the Plan Itself

| Risk | Mitigation |
|---|---|
| **Velocity decay recurs** (17 stories/2wks → 5 stories/3.5mo) | Phase 0 is the treatment (manual-verification tax was the prime suspect — S2 §10). Track stories/week from Phase 1; if it doesn't double, the problem is elsewhere — stop and diagnose before Phase 2. |
| **Scope creep re-delays first contact** | The MVS "no scope creep" rule now has a sharper form: *nothing enters Phases 1–3 that isn't in this plan without removing something of equal size.* Session 2's principle stands: resist any addition that delays the beta. |
| **The nudge hypothesis fails in beta** | That is a success of the process, not a failure — it's why the beta exists. The kill-switch metric (mute/block rate) is now instrumentable (2.4); honor it. Quick Capture (Phase 4) is the documented pivot surface if mediation underwhelms but capture retains. |
| **iOS users in beta groups** | Web push on iOS is fragile; email ships as a first-class nudge channel (6.1, Phase 2.4), not a fallback. Do not spend on Capacitor before beta data. |
| **One-person bus factor on ops** | The Phase 2.3 runbook + tested restore is the minimum; keep it one page and current. |

---

## 9. Review Retrospective (what this 9-session process itself proved)

- **The adversarial split-session design worked:** each session materially corrected its
  predecessors (S3 downgraded S1's "BYOK implemented"; S4 exposed S2's test understatement;
  S8 falsified S4's accessibility framing and Epic 2.5's "done") — single-pass review
  would have preserved those errors.
- **Live verification beats code reading:** the two most user-visible defects in the
  product (invisible text, offscreen navigation) were invisible to code review and
  instant on a screenshot. The DoD change (0.4b) is this review's most durable output.
- **Same-day proof of recoverability:** three CRITICALs (orbital nav, token system,
  modal crash) were fixed and verified within hours of being found (S8 post-review).
  The codebase is not rotten — its feedback loops were. Restore the loops and the
  existing component quality becomes an asset.

**Final word:** ClearDues does not need a rebuild, a re-plan, or new ideas. It needs
its gates turned on, its ledger made honest, its differentiator built on the roadmap it
already has, and ten real groups using it. Everything in this file serves that sentence.
