# ClearDues UX Design Specification v2 — "Quiet Ink"

**Status:** ADOPTED (user decision, WS2, 2026-07-07)
**Supersedes:** `ux-design-specification.md` (v1). v1's visual system (warm-cream palette,
Agent Orb, Orbital Nav / Hidden Nav sections) is void. v1's *product-behavior* principles
survive only where restated in §2 of this document.
**Produced by:** Work Session 2 (`10-execution-plan.md`). Rendered candidate previews:
https://claude.ai/code/artifact/2013e5de-4d4b-46e9-922e-5274a025907e
**Implemented by:** WS3 (Design System Implementation & Brand Floor) — via
`ws3-implementation-kit.md` (same directory), which turns this spec into paste-ready
files and mechanical find/replace steps. **Implementers: work from the kit, not from
this document.** Where the two differ, the kit wins (it was audited against the live
code on 2026-07-07).

---

## 1. Decision Record

Three candidates were rendered and reviewed (A "Quiet Ink", B "Warm Minimal Distilled",
C "Crisp Utility"). The user chose:

| Decision | Outcome |
|---|---|
| Direction | **A — Quiet Ink.** Paper-and-ink minimalism: flat surfaces, hairline dividers, ledger-row layout, structure over decoration. |
| Typography | **System font stack, zero download.** The app renders in the platform's native voice (SF Pro / Roboto / Segoe UI). |
| Agent Orb | **Retired.** Replaced by a plain circular "+" FAB. The "agent" identity lives in the mediator voice and AI commentary, not a glowing object. |
| Accent | **Ink-teal, per Direction A as presented** (`#1F6E68` light / `#57B3AA` dark). Retains a thread of brand continuity with v1's teal. |
| Palette | Warm cream ground replaced by near-white paper; warm-black ink retained in spirit (slightly warmer neutrals than pure gray). |
| Voice | **Confirmed kept** — calm mediator tone everywhere (errors, empty states, notifications), personality capped at "Funny" (S8 UX-H5). |
| Navigation | **Confirmed kept** — post-S8 bottom tab bar + FAB. Tap FAB = Smart Input. No hidden gestures, no auto-hide, no long-press entry points. |

**Design thesis:** a mediator should feel like quiet, neutral paper — a well-set ledger
page — not like software performing calmness. The interface disappears; the names and
numbers are the design.

---

## 2. Product Constitution (kept from v1 on merit)

These are behavior rules, not aesthetics. Every WS3+ story inherits them:

1. **No red debt.** Amounts are neutral facts set in ink; direction comes from the label
   ("you owe" / "you're owed"), never from alarm color. Amounts never double-encode
   direction (no "−$450" *plus* "you owe" — the label carries direction, S8 UX-L2).
2. **Settled = amber, never green/red.** Amber is the only celebratory color in the app.
3. **Payment = Silence.** Settled things get quieter, not louder. The settle moment is
   the app's single choreographed animation (§6).
4. **Emotional neutrality.** No judgment framing, no guilt/shame mechanics, no
   notification spam. Anti-pattern list from v1 remains the review rubric.
5. **44px minimum touch targets.** No exceptions (S8 UX-C2 must never recur).
6. **WCAG AA.** Every token pair in §3 ships with a verified contrast ratio; axe smoke
   test required in CI (WS3).
7. **Manual confirm only.** No timer-based commits of financial records (S8 UX-H6).
   No timed UI (no auto-hide, no non-adjustable timeouts — WCAG 2.2.1).
8. **Both themes, system default.** Light and dark are designed together; neither is an
   afterthought.

---

## 3. Token Set

Implementation note for WS3: map these through Tailwind v4 `@theme` with **namespaced
text tokens** (`--color-text-*` → `text-text-*` utilities). The UX-C1 collision class
(text tokens shadowing shadcn surface tokens) must not recur. Delete unused v1 tokens
(surface tints, chart palette, sidebar set) rather than carrying them.

### 3.1 Color — Light ("paper")

| Token | Value | Role | Contrast (on paper) |
|---|---|---|---|
| `--background` | `#FCFCFB` | Page ground ("paper") | — |
| `--surface-elevated` | `#FFFFFF` | Modals, sheets, popovers only | — |
| `--text-primary` | `#1C1B1A` | Ink — headings, amounts, body | 16.8:1 |
| `--text-secondary` | `#6E6B66` | Supporting labels, metadata | 5.3:1 |
| `--text-muted` | `#93908A` | Timestamps, hints (large/secondary only) | 3.2:1 (min 14px, non-essential) |
| `--border` | `#E7E5E1` | Hairline dividers, input strokes | — |
| `--accent` | `#1F6E68` | Interactive only: buttons, links, active tab, focus ring | 6.0:1 |
| `--accent-hover` | `#16544F` | Hover/pressed | — |
| `--accent-foreground` | `#FFFFFF` | Text on accent | 6.0:1 on accent |
| `--settled` | `#8F681C` | "Settled" text and icons (amber family, AA-safe) | 5.0:1 |
| `--settled-accent` | `#A87B22` | Amber glow / large settled indicators (≥3:1 UI use) | 3.7:1 |
| `--settled-subtle` | `#F7EFD9` | Settled row background tint | — |
| `--error` | `#A05A52` | Error text/borders (muted clay — never bright red) | 5.0:1 |

### 3.2 Color — Dark

| Token | Value | Role | Contrast (on bg) |
|---|---|---|---|
| `--background` | `#141414` | Page ground | — |
| `--surface-elevated` | `#1E1E1D` | Modals, sheets, popovers | — |
| `--text-primary` | `#ECEAE6` | Ink | 15.6:1 |
| `--text-secondary` | `#A3A09B` | Supporting | 7.1:1 |
| `--text-muted` | `#767370` | Timestamps, hints | 3.9:1 |
| `--border` | `#2B2A28` | Hairlines | — |
| `--accent` | `#57B3AA` | Interactive | 7.4:1 |
| `--accent-hover` | `#6FC4BB` | Hover/pressed | — |
| `--accent-foreground` | `#101010` | Text on accent | 7.0:1 on accent |
| `--settled` | `#D3A44E` | Settled text/icons | 8.1:1 |
| `--settled-accent` | `#D3A44E` | Same value in dark | — |
| `--settled-subtle` | `#26200F` | Settled row tint | — |
| `--error` | `#CE8A80` | Error | 6.2:1 |

Dark elevation is expressed by surface color (`--surface-elevated`), never by shadow.

### 3.3 Typography

```
--font-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

- **Zero font download.** Delete the Google Fonts `@import` (S8 UX-M2). No `@font-face`.
- **Two weights only:** 400 (regular) and 600 (semibold). No 500, no bold-700.
- **`font-variant-numeric: tabular-nums` is mandatory on every monetary amount** and any
  column of digits.
- Keep `-webkit-font-smoothing: antialiased`.

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `--text-display` | 28px / 1.2 | 600 | Balance hero, one per screen max |
| `--text-title` | 20px / 1.3 | 600 | Screen titles |
| `--text-heading` | 17px / 1.4 | 600 | Section heads, card titles |
| `--text-body` | 15px / 1.5 | 400 | Default |
| `--text-body-small` | 13px / 1.5 | 400 | Metadata, secondary rows |
| `--text-caption` | 11px / 1.4 | 400, +0.06em tracking, uppercase | Labels, nav items |

### 3.4 Spacing, Radii, Elevation

- **Spacing:** unchanged 4px base scale (`4/8/12/16/20/24/32/48`). List rows: 56px height.
- **Radii:** surfaces are square. Radius exists on *controls only*:
  `--radius-control: 8px` (buttons, inputs), `--radius-sheet: 12px` (modal/sheet top
  corners), `--radius-full: 9999px` (FAB, avatars, pills).
- **Shadows: none at rest.** Cards are replaced by full-bleed rows separated by hairline
  `--border` dividers. Exactly one shadow token exists, for overlays:
  `--shadow-overlay: 0 12px 32px rgba(0,0,0,0.14)` (light only; dark uses surface color).

### 3.5 Motion

- `--duration-fast: 120ms`, `--duration-normal: 150ms`, easing `cubic-bezier(0.4,0,0.2,1)`.
- **Allowed properties: opacity and transform only.** No infinite/idle animations
  anywhere (the orb pulse dies with the orb). No animation over 300ms except:
- **The settle moment (the one choreographed animation):** on settlement confirmation the
  row tints `--settled-subtle`, glows once with `--settled-accent`, then fades to its
  quiet settled state — ≤400ms total, CSS-only. This is v1's "Payment = Silence" payoff
  (S8 UX-M3), finally specified as buildable.
- `prefers-reduced-motion`: all of the above collapse to instant state changes (keep the
  existing global rule).
- **framer-motion is deleted from the dependency graph.** Nothing in this system needs it.

---

## 4. Component Restyle Inventory (WS3 work list)

### 4.1 Delete (not restyle)

| Component | Action |
|---|---|
| `ui/agent-orb.tsx` | Delete. Replace with plain FAB (56px circle, `--accent` bg, "+" glyph, `--shadow-overlay` in light). AI activity is shown as a text-based thinking indicator inside Smart Input, not on the FAB. |
| `Common/Footer.tsx` | Delete (FastAPI template footer with social links). Nothing replaces it. |
| Template feature UI (`Items/*`, `Admin/*`, `Pending/PendingItems|PendingUsers`, `UserSettings/ChangePassword`) | **Do not restyle** — scheduled for deletion in WS8. Restyling them is wasted work. |
| `ui/swipeable-card.tsx` usage on Dashboard | Unmount the dead swipe affordances until actions are wired (S8 UX-M6). Component may stay in the tree for WS6. |

### 4.2 Restyle — shadcn primitives (one design language; kills S8 UX-M4)

`button`, `input`, `label`, `form`, `select`, `checkbox`, `dialog`, `sheet`,
`dropdown-menu`, `tabs`, `tooltip`, `alert`, `badge`, `avatar`, `separator`,
`skeleton`, `sonner` (toasts), `loading-button`, `progress`, `inline-input`,
`card` (repurposed as the full-bleed ledger row), `table`, `pagination`.

Treatment: square surfaces, hairline borders, 8px control radius, two font weights,
accent used only on the primary action per view. Destructive actions use `--error`
(muted clay), never saturated red.

### 4.3 Restyle — ClearDues screens & components

| Area | Components | Notes |
|---|---|---|
| Navigation | `ui/bottom-nav.tsx` | Caption-size uppercase labels, `--accent` active state, hairline top border, safe-area padding kept. FAB docks above it. |
| Dashboard | `features/dashboard/Dashboard.tsx`, `ui/balance-display.tsx` | Balance hero in `--text-display` tabular figures; group rows as hairline ledger rows; delete the template greeting ("Hi, 👋…") for date + total-balance header. |
| Groups | `GroupDetail.tsx`, `MembersList.tsx`, `CreateGroupForm.tsx`, `GenerateInviteButton.tsx` | Restyle to rows; the `/groups/$groupId` route itself is WS5 scope. |
| Expense flow | `SmartInputModal.tsx`, `MemberChips.tsx`, `SplitPicker.tsx`, `UnequalSplitInputs.tsx`, `PercentageSplitInputs.tsx`, `SplitAmountsDisplay.tsx`, `ExpensePreviewCard.tsx`, `EditableExpensePreview.tsx`, `ExpenseForm.tsx`, `AICommentaryBubble.tsx` | Full-screen sheet (12px top radius); amounts tabular; AI commentary styled as quiet secondary text, not a chat bubble balloon. |
| Ledger/activity | `ActivityFeed.tsx`, `ActivityFeedItem.tsx`, `AuditLogList.tsx`, `ConfirmedExpenseCard.tsx`, `PendingConfirmationsList.tsx`, `PendingSettlementsList.tsx`, `SettlementClaimsList.tsx`, `SettlementClaimCard.tsx` | Ledger rows; settled rows use `--settled*` tokens + the settle moment (§3.5). |
| Auth | `routes/login.tsx`, `routes/register.tsx`, `AuthLayout.tsx`, `OAuthButtons.tsx`, `Logo.tsx` | Brand floor: ClearDues wordmark (system-stack 600, ink; no logo image needed for beta), new favicon (minimal ink-teal glyph — final mark chosen in WS3), correct `<title>`s, template footer gone. |
| System | `theme-provider.tsx`, `Common/ErrorComponent.tsx`, `NotFound.tsx`, `Appearance.tsx`, `Common/DataTable.tsx` | Error/empty states get mediator-voice copy (pairs with WS8's error mapper); theming logic unchanged. |

---

## 5. Performance Budget ("lighter, faster" made measurable)

CI/verification gates for WS3 and every UI story after it:

| Metric | Budget | Current |
|---|---|---|
| Web font transfer | **0 KB** (system stack) | ~3 static Inter weights via render-blocking Google Fonts `@import` |
| Third-party requests at first paint | **0** | 1 (fonts.googleapis.com) |
| Main JS chunk (gz) | **≤ 250 KB**, vendor-split | ~1.48 MB single chunk (S4-M5) |
| `framer-motion` | **removed from `dependencies`** | shipped to every user |
| Devtools (`@tanstack/*-devtools`) | dev-only, never in prod bundle | in `dependencies` (S4-L3) |
| LCP (mid-tier Android, 4G throttle) | **< 1.2 s** | unmeasured |
| Lighthouse performance (mobile) | **≥ 90** | unmeasured |
| Animation | opacity/transform only; nothing infinite; ≤400ms max (settle moment) | permanent orb pulse |

WS3 must report measured bundle size against this table in its completion notes
(execution-plan Ground Rule 4 analog for perf).

---

## 6. Accessibility Requirements (system-level, testable)

1. All §3 token pairs meet the ratios listed; any new pair added later needs a computed
   ratio in the PR description.
2. `--text-muted` is restricted to non-essential text ≥14px (it is 3.2:1 in light mode).
3. Focus: `:focus-visible` ring, 2px `--accent`, 2px offset, on every interactive element.
4. Touch targets ≥44×44px including the bottom nav and FAB.
5. No timed UI: nothing auto-hides, auto-confirms, or expires without a user-adjustable
   control (WCAG 2.2.1; S8 UX-H6/C2).
6. `prefers-reduced-motion` respected globally (exists; keep).
7. WS3 adds an axe smoke test + 375px/1280px screenshot proof in both themes to CI/DoD.
8. Amount announcements: use visually-hidden text or `aria-describedby` for direction
   context; no nonstandard `role="text"`, no double-announcement (S8 UX-L3).

---

## 7. Voice (unchanged, now load-bearing)

With the orb retired and decoration stripped, the mediator voice **is** the brand:

- Errors: calm, specific, third-party tone. Never raw axios strings ("Network Error"),
  never blame. (Mapper implementation lands in WS8; copy standards live here.)
- Empty states name the next action ("Add your first expense — just type it").
- AI personality capped at "Funny"; "unhinged/no boundaries" language is excised from all
  artifacts (S8 UX-H5). Per-member opt-in required for anything sharper, post-beta.
- Notifications follow Progressive Urgency rules (WS12/WS13) and inherit this tone.

---

## 8. Out of Scope for This Spec

- No implementation in WS2 (this document is the WS3 contract).
- Screen *information architecture* changes (group ledger screen, `/groups/$groupId`)
  are WS5; this spec governs how they look when built.
- Payment-link registry, currency formatting (WS10) — but note: currency is per-group
  (global market), so no token or component may hardcode a currency symbol.
