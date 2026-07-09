# Session 8 — UX/UI & Design Direction Review

**Date:** 2026-07-06
**Scope:** ux-design-specification.md, ux-design-directions.html, ux-integration-plan.md,
implemented frontend UX (design tokens, OrbitalNav, AgentOrb, SwipeableCard,
BalanceDisplay, Dashboard, Groups, layout, theme), live app inspection.
**Method:** Full read of all three UX planning artifacts; source read of the Epic 2.5
component layer; **verification against the built CSS bundle** (`dist/assets/index-*.css`);
and a **live run of the app** (Vite dev server, client-side auth gate bypassed via the
key-existence-only token check noted in S4-M8, 375×812 mobile viewport). Screenshots and
DOM measurements were taken of the login page, dashboard, and the expanded Orbital Nav.
Severity per CLAUDE.md review scoping. Cross-references: `S4-*` = 04-technical-frontend.md,
`B-*` = 03-technical-backend.md.

---

## 1. Verdict Up Front

**The UX specification is the strongest planning artifact in this repository — and the
implemented UX is the weakest deliverable in it.** These are two separate failures with
one shared root cause: nothing in this product has ever been *looked at* on a real screen
as part of any story's definition of done.

**The spec (7/10):** genuinely thoughtful. "Payment = Silence," emotional-neutrality rules
(no red debt, no judgment framing), the warm-minimal palette that deliberately avoids
fintech clichés, the passive-member test, and a written anti-pattern list are better
product thinking than most funded consumer apps produce. Its two structural flaws: it
**contradicts itself on navigation** (a "Hidden Nav" pill component AND an "Orbital Nav"
are both fully specified, never reconciled), and in three places it **chooses novelty over
its own stated values** (orbit-only navigation, long-press-only entry to the flagship
flow, and an "unhinged, no boundaries" roast mode inside a product whose first emotional
principle is that the app is never judgmental).

**The implementation (2/10):** verified live —

1. **The design-token migration (Story 2.5.1) does not function.** The spec's text-color
   utilities collide with shadcn's surface-color namespace: `text-secondary` and
   `text-muted` compile to *near-white surface colors* (contrast **~1.0–1.15:1 — invisible
   in both themes**), `text-primary` compiles to the **teal action color** (3.2:1 in light
   mode — fails WCAG AA body text), and the entire spec type scale (`text-display/title/
   heading/body-small/caption`) plus the shadow system **generate no CSS at all**.
   85 usages across 22 files — every ClearDues-native screen.
2. **Orbital Navigation is unusable on the primary platform.** On a 375px viewport,
   measured live: **2 of 5 destinations render fully offscreen**, a third is a clipped
   sliver, and all icons are flex-squished to 22×48px ovals (below the spec's own 44px
   touch minimum). The nav also auto-hides after 3 seconds.
3. **The first impression is still the FastAPI template**: login page footer reads
   "Full Stack FastAPI Template - 2026" with GitHub/X/LinkedIn links, the dashboard greets
   with the template's "Hi, 👋 Welcome back, nice to see you again!", errors surface as
   raw "Network Error" strings rendered in teal, and devtools ship in the page.

Epic 2.5 is marked done (7/7). Its centerpiece deliverables — the token system and the
navigation system — have never worked. The spec's Storybook, axe-core CI, per-sprint
screen-reader testing, and device matrix exist only as text.

**UX health score: 3/10** (spec 7/10, implemented experience 2/10).

---

## 2. Findings Summary

| ID | Severity | Finding |
|----|----------|---------|
| UX-C1 | CRITICAL | Design-token migration mis-wired: invisible secondary/muted text (≈1:1 contrast, both themes), teal "primary" text, type scale + shadow tokens generate no CSS. 85 usages / 22 files |
| UX-C2 | CRITICAL | Orbital Nav broken on mobile: 2 of 5 destinations offscreen, 1 clipped, icons squished to 22×48px (flex-shrink + wrong arc geometry) |
| UX-C3 | CRITICAL | Core actions undiscoverable by design: 100% of navigation behind an unlabeled orb tap; the flagship expense entry behind an unhinted 500ms long-press — which then silently no-ops (S4-C1) |
| UX-H1 | HIGH | First-run/brand experience is the unmodified template (login footer, FastAPI favicon/titles, template greeting, social links, devtools) |
| UX-H2 | HIGH | Implemented information architecture bears no resemblance to the spec's 3-layer model: no group view feed, no expense list anywhere, desktop master-detail on mobile |
| UX-H3 | HIGH | Spec self-contradiction: Hidden Nav (bottom pill) and Orbital Nav both fully specified; 4 vs 5 destinations; implementation picked one, spec never updated |
| UX-H4 | HIGH | Error voice violates the Mediator principle: raw axios "Network Error" shown to users, error text rendered teal (via C1), API `detail` messages replaced by hardcoded strings (S4-M4) |
| UX-H5 | HIGH | F3-PBS "roast mode" contradicts the product's core emotional-design principles and is a brand/content-safety liability; also currently fiction (no personality write path, B-C2) |
| UX-H6 | HIGH | 3-second auto-confirm default commits financial records without explicit user confirmation |
| UX-H7 | HIGH | WCAG AA commitment systematically unmet: contrast (C1), touch targets (C2), 3s non-adjustable timeout (WCAG 2.2.1), zero automated or manual a11y testing ever run |
| UX-M1 | MEDIUM | Shadow tokens defined but unwired — `.shadow-*` utilities compile to Tailwind defaults, not the spec's "subtle depth" values |
| UX-M2 | MEDIUM | Inter loaded as render-blocking Google Fonts `@import` (3 static weights, not the spec'd variable font; third-party request on every load of a "sub-1.5s on 4G" app) |
| UX-M3 | MEDIUM | "Payment = Silence" reward moments unimplemented: no settlement fade-out reachable, no zero-balance celebration state |
| UX-M4 | MEDIUM | Two design languages coexist: ClearDues screens use (broken) spec tokens; Groups/template screens use shadcn tokens (`text-muted-foreground`, `text-red-600`, `font-bold`) |
| UX-M5 | MEDIUM | `en-IN` locale + "Rs" prefix hardcoded in the display layer while the product targets a global market (UX face of S4-M3) |
| UX-M6 | MEDIUM | Dead swipe affordances on dashboard cards (reveal actions that do nothing, S4-L4) train users that gestures in this app are fake |
| UX-L1 | LOW | Template screens use `font-bold`/`text-2xl`, violating the spec's "no bold weights" calm-typography rule; unused 600 weight downloaded |
| UX-L2 | LOW | BalanceDisplay double-encodes debt: "-Rs 450" *and* "You owe" label (spec: amounts are neutral facts, direction comes from the label) |
| UX-L3 | LOW | Nonstandard `role="text"` on amount spans; aria-label duplicates visible content in a way VoiceOver reads twice |
| UX-L4 | LOW | Agent Orb overlaps the footer content on mobile (no reserved bottom safe-area) |

---

## 3. CRITICAL Findings

### UX-C1 — The design-token migration does not function (Story 2.5.1)

The spec defines text colors as `text-primary/secondary/muted` and a type scale
`display/title/heading/body/body-small/caption`. `index.css` declares these as raw CSS
variables (`--text-secondary: #6b6660`, `--font-title: 24px`, …) — **but never maps them
into Tailwind v4's `--color-*` / `--text-*` theme namespaces**, while the shadcn template
variables *are* mapped (`--color-primary: var(--primary)`, etc.). Consequences, verified
in the built CSS bundle and in the running app:

| Class used in code | Author intent (spec) | What it actually compiles to | Live result (dark mode) |
|---|---|---|---|
| `text-primary` | Warm black `#1F1E1C` body text | `color: var(--primary)` = **teal #3D9A94** | All "primary" text is brand-teal; 3.2:1 on light bg — fails AA |
| `text-secondary` | Warm gray `#6B6660` | `color: var(--secondary)` = **surface cream #FAF8F5** (dark: `#252525`) | rgb(37,37,37) on rgb(26,26,26) — **~1.1:1, invisible** |
| `text-muted` | Light gray `#9C9790` | `color: var(--muted)` = same surface color | **Invisible** |
| `text-title`, `text-heading`, `text-body-small`, `text-caption`, `text-display` | 24/18/14/12/32px scale | **No CSS generated at all** (absent from bundle) | Everything renders at inherited 16px |
| `shadow-sm/md/lg` | Spec's subtle-depth shadows | Tailwind default shadows (`--shadow-*` declared in `:root`, never consumed) | Spec shadow system inert |

Grep: **85 occurrences across 22 files** — Dashboard, BalanceDisplay, SmartInputModal,
ActivityFeed, SplitPicker, MemberChips, login/register, every Epic 2.5–5 screen. The
correct gray *does* exist in the app — as shadcn's `text-muted-foreground` — which only
the **template** screens use. So the old template UI renders correctly and every new
ClearDues screen renders wrong: secondary labels ("Total Balance", member counts,
timestamps, context labels) are invisible, headings don't scale, and body text is teal.

This is simultaneously the repo's largest accessibility defect and proof that **no Epic
2.5+ story was ever visually verified**: invisible text on the dashboard cannot survive
one honest manual test. Seven stories cited "manual testing" and passed code review
because reviewers read class names (`text-secondary` *looks* right) rather than pixels.

**Impact:** Every ClearDues screen fails WCAG at the "can you read it at all" level; the
entire visual-hierarchy layer of the design system is a no-op.
**Effort:** Low (half a day) — map the tokens in `@theme` (e.g. `--color-content-primary`,
`--text-title: 24px`…), rename the colliding utilities once
(`text-secondary` → `text-content-secondary` or adopt shadcn's `muted-foreground`
semantics), and add one Playwright screenshot test so this class of bug can never pass
silently again.

### UX-C2 — Orbital Navigation is unusable on the primary platform

Measured live on a 375×812 viewport with the nav expanded (`orbital-nav.tsx`):

| Destination | Measured rect (viewport w=375) | State |
|---|---|---|
| Home | x218, 22×48px | Visible, squished oval |
| Groups | x291, 22×48px | Visible, squished oval |
| Pending | x363–385 | **Clipped at screen edge** |
| Activity | **x406** | **Fully offscreen** |
| Profile | **x407** | **Fully offscreen** |

Two independent bugs compound:

1. **Wrong arc geometry.** `calculateOrbitalPosition` spans **-135° → +45°** — for an orb
   anchored in the bottom-right *corner*, that aims two icons toward the right edge and
   bottom-right, where no screen exists. A corner anchor has one usable quadrant:
   the arc must span **180° → 270°** (left → top). The spec's own ASCII diagram
   (icons at top/left/bottom around the orb) describes the correct layout; the code
   implements a different one.
2. **Flex-shrink squish.** The orbital icons are children of a
   `flex items-center justify-center` container sized by the 57px orb; the five 48px
   icons are row-laid-out and shrunk to **22×48px** *before* being transformed to their
   orbit offsets — half the spec's 44px minimum touch target, and visibly oval.

Add the behavioral finding: the expanded nav **auto-hides after 3 seconds** (verified —
it collapsed faster than a screenshot round-trip, twice). Three seconds to visually parse
five unlabeled icons and hit a 22px target is not a navigation system; it is a reflex
test. Story 2.5.3's AC ("icons animate outward… keyboard navigation…") all check
individual boxes while the composed result was never opened on a phone-sized window.

**Impact:** On mobile, 40% of the app's destinations (Activity, Profile/Settings) are
unreachable by touch, full stop. This blocks Story 4.5's activity feed and all settings.
**Effort:** Low to patch (fix arc range, `flex-none`/absolute-position icons, extend or
remove auto-hide) — but see §7: patching should be secondary to replacing the pattern.

### UX-C3 — The two core actions are locked behind invisible interactions

The complete interaction inventory for a new user on the dashboard:

- **All navigation:** tap an unlabeled pulsing teal squircle (no icon that says "menu",
  no label, no onboarding, no tooltip on touch devices) → radial icons appear for 3s.
- **Add expense (the "15-second magic moment," the product's reason to exist):**
  **press and hold the same orb for 500ms**. Nothing in the UI, at any point, tells the
  user a long-press exists. There is no visible add-expense button on the dashboard, on
  group cards (the spec's "Add Expense" card action was never built), or in GroupDetail
  (S4-C1). And a user who *discovers* the long-press reaches a modal that has no group
  selector and **silently no-ops on submit** (S4-C1).

The spec itself demoted the flagship action to long-press ("Long-press Orb → Smart Input
modal (primary action)") — an interaction with near-zero organic discoverability that
iOS/Android reserve for *secondary* context menus. The three-layer failure (hidden
trigger → hidden gesture → silent no-op) means the core loop is not merely broken
(Session 3/4 established that); it is **undiscoverable even in the version where it
worked**.

**Impact:** First-session abandonment; the "First Expense Magic" trust moment can never
occur. **Effort:** Low for affordances (visible Add Expense buttons on dashboard cards +
group view; first-run coach mark on the orb); the underlying wiring is S4-C1.

---

## 4. HIGH Findings

### UX-H1 — The first impression is another product

Verified live: the login page — the single highest-stakes screen for a product whose
invite flow dumps cold invitees on it (Session 2's "Walled Garden") — shows **"Full Stack
FastAPI Template - 2026"** with GitHub/X/LinkedIn icons in the footer. The favicon and
`<title>` are FastAPI's (S4-H2). Post-login, the dashboard's first line is the template's
"Hi, 👋 Welcome back, nice to see you again!" (`_layout/index.tsx:24-27`) — template
voice, `text-2xl` template typography — not the spec's greeting + total-balance header.
TanStack Query/Router devtool buttons float over the product UI in dev builds and both
libraries ship in `dependencies` (S4-L3). There is no ClearDues logo asset anywhere.

For the stated goal — *premium, minimal, timeless* — this is disqualifying: the app
currently has no brand at all. **Impact:** Zero credibility with any beta invitee.
**Effort:** Low — a logo, favicon, titles, footer, and greeting rewrite is a day; full
template purge is S4's fix #5.

### UX-H2 — The implemented IA is not the specified IA

Spec: Dashboard (card stack + quick actions) → Group View (chat-style expense feed +
balance) → Smart Input Modal, connected by slide transitions and deep links.
Implementation: Dashboard (closest to spec, minus quick actions) → `/groups` — a
**two-pane desktop master-detail** (list left, `useState` detail right, S4-H3: no URL, no
back button, stale snapshot) whose detail pane shows members, an *unscoped* cross-group
claims list (S4-M6), and activity — **but no expenses and no balance**. The chat-style
feed, the screen the entire "agent-first" concept hangs on, does not exist on any route;
`ActivityFeed` renders plain rows, and no screen can list a group's expenses (B-H7).
Screen transitions: none of the specified ones exist. On mobile the two-pane layout
stacks awkwardly; selecting a group scrolls the user to a panel below the fold.

**Impact:** The product's designed mental model (glance → drill in → act) is absent; what
shipped is CRUD panels. **Effort:** Medium — `/groups/$groupId` route (S4-H3) + one
mobile-first group screen composing the already-built feed/claim/expense components;
blocked on B-H7 for the ledger.

### UX-H3 — The spec ships two competing navigation systems

"Design Direction Decision" and "Component Strategy" fully specify **Hidden Nav**: a
32px translucent pill, bottom-*left*, expanding into a conventional bottom nav bar with
4 destinations. "UX Consistency Patterns" then introduces **Orbital Navigation** around
the orb as *the* navigation pattern ("Instead of a traditional bottom nav bar…"), also
4 destinations. Both remain in the final document with no supersession note; the
integration plan's Story 2.5.3 builds Orbital; the implementation added a 5th
destination (Pending) found in neither. A designer, a developer, and a reviewer reading
this spec today would each build a different nav. This is how C2 happened: the ASCII
art from one section and the behavior tables from another were stitched together.

**Impact:** Direct cause of drift + rework; makes the spec unreliable as the contract it
is supposed to be. **Effort:** Trivial — one decision, one edit pass (do it as part of §8).

### UX-H4 — The Mediator has no voice where it matters most

The spec's most defensible differentiator is tone: calm third-party language, "no
technical jargon" (MVS #6), errors that never blame. Reality (verified live): dashboard
failure renders **"Failed to load dashboard: Network Error"** — a raw axios string — in
**teal** (via C1) on a template screen. The hand-rolled API layer *replaces* useful server
`detail` messages with generic hardcoded strings (S4-M4), so when real errors flow, users
will get the wrong words in the wrong voice. Meanwhile the one place personality *was*
invested — AI commentary — is a mock (S4-C2). The emotional-design layer exists nowhere
a user would actually encounter emotion (errors, empty states, waiting).

**Impact:** Brand voice is a spec fiction; error moments actively read as broken
software. **Effort:** Low — a 20-line error-message mapper with mediator-voice copy +
fix S4-M4's message swallowing.

### UX-H5 — F3-PBS "roast mode" contradicts the product's own constitution

The same document that mandates *"Emotional Neutrality — never judgmental"*, *"Numbers
Without Judgment — '$50' not 'You still owe $50!'"*, and *"To Prevent: Guilt, Shame"*
also specifies a mode whose sample output is **"Rs 1,500 for fries?! Did you eat the
whole potato farm? Rs 375 each, chunky."** — body-shaming adjacent humor about money,
"no boundaries" by declared design, powered by a user-supplied Gemini key with no
moderation layer specified anywhere. One passive member (the persona the spec says every
decision must protect) receiving one roast they didn't opt into is a group-deleting
event. It is also a moderation/brand liability the moment a screenshot leaves the app,
and — per B-C2 — there is currently no way to even set a personality, so all four modes
are fiction.

This is not "delete the personality system" (per-group AI tone is a real differentiator).
It is: cap the spectrum at "Funny," require *every member's* opt-in (not the group
creator's) for anything sharper, specify output guardrails as acceptance criteria, and
drop "no limits/no boundaries" from the vocabulary of a money product.
**Impact:** Existential for the "trusted mediator" positioning if shipped as specced.
**Effort:** Trivial now (spec edit); expensive after a viral screenshot.

### UX-H6 — Auto-confirm writes financial records on a timer

Spec: "Auto-confirm: result confirms after 3 seconds if no intervention" (user-preference,
but presented as a first-class mode of the core flow). A parser with a stated 90% accuracy
target, auto-committing money records against a 3-second countdown — on the product whose
pitch is *eliminating* money disputes — inverts "Trust Through Transparency: every AI
decision is visible and editable." The undo toast is also 3s. WCAG 2.2.1 (adjustable
timing) applies to both. Given B-H2/M1 (splits already disagree between preview and
storage), auto-confirm converts parse errors directly into ledger disputes.

**Impact:** Wrong-money writes at ~10% of flagship-flow usage.
**Effort:** Trivial — make manual confirm the only MVP mode; revisit auto-confirm
post-beta with accuracy telemetry (which requires the analytics story Session 2 flagged).

### UX-H7 — The WCAG AA commitment is unmet on every systemic axis

Component-level ARIA is genuinely good (S4 noted it; SwipeableCard's keyboard
alternatives, MemberChips' checkbox semantics, BalanceDisplay's context labels,
reduced-motion handling throughout). But the spec's *system-level* commitments are all
unmet: **contrast** — invisible text app-wide (C1); **touch targets** — 22px nav icons
(C2) vs the promised 44px; **timing** — 3s nav auto-hide and 3s auto-confirm/undo with no
pause/extend (spec explicitly promised "timeout extensions"); **testing** — axe-core in
CI (no CI exists, S6), Lighthouse 95+, per-sprint VoiceOver/NVDA passes, jsx-a11y — none
ever configured or run. Accessibility here is a code-review aesthetic, not a property of
the product.

**Impact:** Legal-exposure-grade gaps for any public launch; excludes low-vision users
entirely. **Effort:** C1+C2 fixes get 80% of the way; add jsx-a11y + one axe smoke test
to the launch-blocker epic (pairs with S6's CI resurrection).

---

## 5. MEDIUM / LOW Findings (condensed)

- **UX-M1 (shadows unwired)** — same mapping bug class as C1; fix in the same pass.
- **UX-M2 (font loading)** — `@import` of Google Fonts CSS blocks first paint on 4G, adds
  a third-party request (GDPR-relevant for EU beta), loads 3 static weights instead of
  the spec'd variable font, including a 600 weight the design system forbids. Fix:
  self-host `Inter var` woff2, `font-display: swap`. Effort: 1 hour.
- **UX-M3 (missing reward moments)** — settlement fade-out-with-amber-glow, zero-balance
  celebration card, and the "silence" empty states are the emotional payoff of the entire
  design and exist nowhere (partly blocked by C4/B-H7 — the cards that would fade are
  unmounted). The one empty state that exists (no-groups) is decent.
- **UX-M4 (two design languages)** — Groups screen: `text-red-600` error (spec: never
  red), `text-muted-foreground`, `font-bold`, shadcn `accent` selection tints. New
  screens: broken spec tokens. Users cross a visible style boundary every navigation.
  Merges into the C1 token repair + H1 template purge.
- **UX-M5 (currency/locale)** — `Intl.NumberFormat("en-IN")` + "Rs" replace hardcoded at
  the component level (S4-M3 lists 8+ files); the spec hardcodes "Rs" as a *brand
  standard* while the product targets a global market (decided 2026-07-07). A currency prop on
  BalanceDisplay + one `formatCurrency` util now, or every display component is rework.
- **UX-M6 (dead gestures)** — dashboard swipe reveals "Edit"/"Settle up" buttons that do
  nothing (S4-L4). Gesture affordances that lie are worse than none: users learn *not* to
  swipe, poisoning the (spec-central) swipe-to-settle pattern before it ships. Hide until
  wired.
- **UX-L1** — template `font-bold` violates the medium-max weight rule; trivial, dies
  with H1.
- **UX-L2** — "-Rs 450" + "You owe" double-encodes direction; spec wants the label to
  carry direction and the amount to stay a neutral fact. One-line fix in BalanceDisplay.
- **UX-L3** — `role="text"` is nonstandard (WAI-ARIA rejected it); the aria-label
  restating the visible amount causes double-announcement in VoiceOver. Use visually
  hidden text or `aria-describedby`.
- **UX-L4** — orb (fixed bottom-6 right-6) overlaps footer content on mobile; reserve
  bottom padding or drop the footer (it's template anyway).

---

## 6. What Is Actually Good (keep these)

Adversarial review obligates honesty in both directions:

- **The palette is a real asset.** Warm cream/charcoal neutrals + muted teal + amber
  success is distinctive, calm, and colorblind-safe; "amber = settled, never green/red"
  is a genuinely original fintech choice. Verified correctly declared in CSS (the
  *mapping*, not the palette, is what's broken).
- **The emotional framework** (Payment = Silence, system absorbs awkwardness, private
  balances, notification restraint) is a differentiated product thesis worth protecting
  from the novelty features it currently shares a document with.
- **Component craftsmanship is above grade:** AgentOrb's state system (idle/processing/
  success with reduced-motion fallbacks), SwipeableCard's threshold/haptic/keyboard/
  hover-fallback completeness, BalanceDisplay's screen-reader context — these match
  their specs almost line-for-line.
- **The spec's anti-pattern list** ("no form fatigue, no anxiety colors, no public shame,
  no notification spam") remains the correct rubric — the fastest way to critique the
  current app is to observe it now violates none of these *only because nothing works*.
- **System-default theming** implemented correctly (corrects S4's note — ThemeProvider
  defaults to `system`, per spec).

---

## 7. Orbital Navigation — Risk Assessment (session-mandated)

**Recommendation: retire Orbital Nav as the sole navigation. Keep the Agent Orb as the
expense-entry FAB. Adopt a standard bottom tab bar.** Confidence: high.

| Risk axis | Assessment | Evidence |
|---|---|---|
| Feasibility | Failed in practice | C2: 2/5 destinations offscreen, 22px targets, shipped broken for ~5 months undetected |
| Discoverability | No affordance says "navigation lives here"; radial menus are a game convention, not an app one (Jakob's Law: users spend most time in *other* apps) | C3; no onboarding exists or is planned in any story |
| Time pressure | 3s auto-hide < scan time for 5 unlabeled icons; measured collapsing faster than a tool round-trip | Live verification; WCAG 2.2.1 |
| Overloading | One 57px control = navigate (tap) + create (long-press) + processing indicator + success indicator; on desktop, hover-expand *and* click-to-input conflict | Spec's own desktop table: click = modal, hover = nav — a 300ms-pause distinction users won't form a model of |
| Scalability | Arc geometry hard-caps ~5 targets in a corner quadrant; app already grew from 4 to 5; Epic 6 (notifications) will want a 6th | Nav items drift H3 |
| Accessibility | Icon-only (labels are sr-only), no visible labels ever, timing-dependent, tiny targets | H7 |
| Uniqueness value | Real but misplaced: the *Orb* (identity, states, glow) carries the distinctiveness; the *radial menu* carries all the risk | — |

**What replaces it:** Design Direction 1's bottom tab bar — which the team already
mocked, and rated "familiar… easy to understand" before rejecting it for being "too
typical" — with the Agent Orb docked as the bar's center or right action. This preserves
100% of the visual identity (the pulsing orb remains the most prominent object on
screen), makes all destinations permanently visible with labels, restores 44px+ targets,
and deletes the discoverability, timing, and geometry problems in one move. Long-press
becomes unnecessary: orb tap = Smart Input (its natural meaning once nav moves to the
bar). Keep the orbital expansion, if desired, as a desktop-hover flourish where it
measurably works.

**Impact:** unblocks Activity/Settings on mobile, makes the flagship flow one visible
tap. **Effort:** 1–2 days (the tab bar is the trivial half; deleting orbital complexity
pays back in bundle size — framer-motion usage shrinks).

---

## 8. Design Direction: Revamp Proposal (premium / minimal / timeless)

The brief's three goals map to specific, mostly cheap moves. The spec needs a v1.1
editing pass, not a rewrite:

**Keep (the identity core):** warm-minimal palette; amber-success/neutral-debt color
constitution; Inter with the calm 400/500 weight discipline; soft radii + subtle shadows
(once wired); the Orb as brand centerpiece and entry point; card-stack dashboard;
full-screen Smart Input; chat-style group feed; Payment = Silence reward mechanics.

**Change:**
1. **Navigation:** bottom tab bar + Orb (per §7). Update spec, delete Hidden Nav
   section, mark Orbital as desktop flourish. *Timeless* means navigation no one has to
   learn.
2. **Personality system:** cap at Funny for MVP; per-member opt-in and specified output
   guardrails before any roast tier returns; excise "unhinged/no boundaries" language
   from all artifacts. *Premium* products are never one screenshot from a trust incident.
3. **Confirmation:** manual confirm only for MVP (H6). The 15-second target survives —
   confirm is the 15th second.
4. **Voice everywhere, not only in AI commentary:** mediator-tone error copy, empty
   states, and notification templates are cheaper than the streaming feature and deliver
   the same differentiation on day one (H4, M3).
5. **Brand floor:** name, logomark, favicon, titles, login footer, greeting (H1). A
   *minimal* design with someone else's logo is just unfinished.
6. **Process guarantee:** every UI story's DoD gains "screenshot at 375px and 1280px
   attached; axe smoke passes." C1 and C2 were both one-glance bugs. This is the
   cheapest finding in this review and the only one that prevents recurrence.

**Sequencing (aligned to Session 2's Phase A–E roadmap):** token repair (C1/M1, 0.5–1d)
and nav replacement (C2/C3/§7, 1–2d) are Phase-A work — they gate every other frontend
story's verifiability. Brand floor + error voice (H1/H4, ~1.5d) belong in the
launch-blocker epic beside S4's template purge. IA completion (H2) rides the ledger
endpoints (B-H7). Total distinct-to-this-session effort: **~4–5 dev-days** on top of
Sessions 3/4's functional fixes.

---

## 9. Corrections to Prior Session Facts

- **S4 "real accessibility work (focus traps, ARIA labels, reduced-motion)"** — true at
  component level, but must now carry the caveat that the app's dominant a11y failure is
  visual (C1/C2) and invisible to code reading; net accessibility is far worse than S4's
  framing implies.
- **S4 §10 "dark theme default via template ThemeProvider"** — incorrect. Default is
  `system`, which conforms to the spec. (Verified in source and live.)
- **Session 2 "Epic 2.5 DONE (7/7)"** — stands formally, but 2.5.1 (tokens) and 2.5.3
  (Orbital Nav) never functioned; Epic 2.5 is "done" in the same component-not-product
  sense S3/S4 documented for Epics 3–5.

## 10. Inputs for Session 9

- **Scores:** UX specification 7/10; implemented UX 2/10; combined design health **3/10**.
- The two verified showstoppers (invisible text, offscreen navigation) are ~2 dev-days
  combined and should headline the impact-vs-effort matrix: highest visible-quality gain
  per hour available anywhere in this codebase.
- Process root cause to carry into the action plan: **no visual verification exists in
  dev-story or code-review workflows** — every S8 CRITICAL would have been caught by one
  screenshot. Recommend making this a workflow change (BMAD post-hook or DoD line), not
  a one-off fix.
- Strategy input: the design *identity* (palette, orb, mediator voice, silence-as-reward)
  is real IP worth building the brand on; the design *novelty* (orbital nav, roast mode,
  auto-confirm) is where all the risk concentrates. Session 9's feature add/remove list
  should treat those as separable.
- Subscription-viability input: nothing in the current UX signals "premium" to a paying
  user (H1); the cheapest premium signals are brand floor + motion discipline + the
  settlement reward moment (M3), all pre-revenue work.

---

## Post-Review Update (2026-07-06, same day — user-approved changes applied)

- **UX-C2/C3 partially RESOLVED:** Orbital Nav removed entirely (`orbital-nav.tsx`
  deleted). New `bottom-nav.tsx`: persistent labeled bottom tab bar (5 destinations,
  75×56px targets, active-state highlight, safe-area padding). Agent Orb retained as a
  floating action button above the bar; **single tap now opens Smart Input** (long-press
  eliminated). Verified live at 375px in both themes; build passes.
- **NEW CRITICAL found and fixed during verification:** `SmartInputModal` crashed on
  every open — `focus-trap-react`'s `FocusTrap` was given a render-prop function child
  (an API that library does not have), throwing `React.Children.only` on mount, silently
  swallowed by the route error boundary. **The modal had never opened once** — this
  supersedes S4-C1's framing ("opens but submit no-ops"); in reality Stories 2.5.4 and
  3.2–3.7 shipped atop a modal that always crashed. Fixed by passing a single element
  child. The modal now renders and opens; S4-C1 (no groupId → submit no-op) and S4-C2
  (mock AI parse) remain outstanding.
- Pre-existing, still open: Radix `DialogTitle` accessibility warning in SmartInputModal.
- **UX-C1 + UX-M1 RESOLVED (token repair, same day):** `index.css` `@theme` now maps
  the text hierarchy (`--color-text-*` → `text-text-primary/secondary/muted` utilities),
  the full type scale (`--text-display/title/heading/body/body-small/caption` with
  line-heights), and the spec shadow system. Bare `text-primary/secondary/muted` usages
  with text-color intent (Dashboard, BalanceDisplay, MemberChips) renamed to
  `text-text-*`; teal-intent usages (shadcn link variants, login/register links,
  load-more buttons) left as-is. Garbage classes fixed (`title` → `text-title
  font-medium`, bare `body-small` → `text-body-small`); bogus `font-variant-numeric`
  class dropped. Dead duplicate `ui/smart-input-modal.tsx` deleted (S4-M9). Verified
  live both themes: secondary text now #6B6660/#A0A0A0 (≈5.3:1 / ≈7:1 contrast, AA
  pass), primary text warm black (not teal), type scale renders 24/18/14px. Build
  passes. Note for UX-H7: contrast + type hierarchy axes now largely addressed;
  touch targets fixed by the bottom nav; timing (auto-confirm/undo) still open.
