# UX Integration Plan for ClearDues

**Created:** 2026-01-14
**Purpose:** Integrate UX Design Specification into existing epics and plan design artifacts

---

## Strategy Overview

The UX specification introduces significant changes that affect all remaining epics. Rather than retrofitting UX into each story, we create a **UX Foundation Epic** that establishes the design system BEFORE continuing with Epic 3.

```
Current:  Epic 1 (Done) → Epic 2 (Done) → Epic 3 → Epic 4 → Epic 5 → Epic 6 → Epic 7

Proposed: Epic 1 (Done) → Epic 2 (Done) → Epic 2.5 (UX Foundation) → Epic 3 → ... → Epic 7

Alternative (lighter):
          Epic 1 (Done) → Epic 2 (Done) → Epic 3 (with UX tasks) → Epic 4 → ... → Epic 8 (UX Polish)
```

**Recommendation:** Insert Epic 2.5 (UX Foundation) to avoid rework and ensure consistency.

---

## New Epic: 2.5 - UX Foundation & Design System

**Purpose:** Establish the visual foundation and core components defined in the UX specification before building features on top.

### Story 2.5.1: Design System Token Migration

As a **frontend developer**,
I want to replace the current color/typography tokens with the UX specification palette,
So that all subsequent components use the correct visual language.

**Acceptance Criteria:**
- [ ] Replace current Tailwind theme with warm minimal palette
  - background: #FDFBF7 (light), #1A1A1A (dark)
  - surface: #FAF8F5 (light), #252525 (dark)
  - action: #3D9A94 (muted teal)
  - success: #D4A857 (warm amber)
- [ ] Configure Inter font family (variable font)
- [ ] Set up spacing scale (4px base unit)
- [ ] Configure border-radius tokens (soft 8-12px)
- [ ] Configure shadow system (subtle depth)
- [ ] Update existing components to use new tokens
- [ ] Both light and dark themes working correctly

### Story 2.5.2: Agent Orb Component

As a **user**,
I want to see an animated Agent Orb as the primary action trigger,
So that I have a distinctive, engaging way to interact with ClearDues.

**Acceptance Criteria:**
- [ ] Create AgentOrb component with squircle shape (56-64px)
- [ ] Implement idle animation (gentle pulse glow, breathing scale)
- [ ] Implement tap/click states (scale up, ripple effect)
- [ ] Implement processing state (faster pulse)
- [ ] Implement success state (amber flash)
- [ ] Position bottom-right corner
- [ ] Accessible: keyboard focusable, aria-label
- [ ] Respects prefers-reduced-motion

### Story 2.5.3: Orbital Navigation System

As a **user**,
I want navigation options that orbit from the Agent Orb,
So that I can navigate without persistent nav chrome cluttering the screen.

**Acceptance Criteria:**
- [ ] Create OrbitalNav component with 4 destinations (Home, Groups, Activity, Profile)
- [ ] Mobile: tap Orb to expand orbital icons
- [ ] Desktop: hover Orb to expand orbital icons
- [ ] Icons animate outward with staggered spring timing
- [ ] Tap orbital icon to navigate, orbitals retract
- [ ] Tap away or tap Orb again to dismiss
- [ ] Auto-hide after 3 seconds of inactivity
- [ ] Keyboard navigation: arrows to cycle, enter to select
- [ ] Replace current sidebar navigation

### Story 2.5.4: Smart Input Modal Foundation

As a **user**,
I want a full-screen Smart Input modal that slides up from the Orb,
So that I have a focused, distraction-free expense entry experience.

**Acceptance Criteria:**
- [ ] Create SmartInputModal component
- [ ] Slide-up animation from Orb position
- [ ] Full-screen on mobile, centered dialog (600px) on desktop
- [ ] Natural language input field with placeholder
- [ ] AI commentary bubble area (above input)
- [ ] Preview card area (below input)
- [ ] Group selector (when entered from dashboard)
- [ ] Close button with slide-down dismiss
- [ ] Keyboard: Escape to close

### Story 2.5.5: Swipeable Card Base Component

As a **user**,
I want to swipe cards left/right to reveal quick actions,
So that I can edit or settle expenses with minimal taps.

**Acceptance Criteria:**
- [ ] Create SwipeableCard component using gesture library
- [ ] Swipe left reveals Edit action
- [ ] Swipe right reveals Mark Paid action
- [ ] 30% threshold reveals action, 60% auto-triggers
- [ ] Haptic feedback on mobile (if available)
- [ ] Desktop fallback: hover reveals action buttons
- [ ] Snap-back animation on incomplete swipe

### Story 2.5.6: Balance Display Component

As a **user**,
I want to see monetary amounts in a consistent, neutral format,
So that debt amounts feel factual, not judgmental.

**Acceptance Criteria:**
- [ ] Create BalanceDisplay component with size variants (display/title/body)
- [ ] Always use text-primary color (never red for debt)
- [ ] "Rs" prefix with comma separators (Rs 1,500)
- [ ] Context labels: "You owe" / "You're owed"
- [ ] aria-label with full context for screen readers

### Story 2.5.7: Update Existing Screens to New Design System

As a **user**,
I want the existing dashboard and group screens to use the new design,
So that the app feels consistent with the new UX direction.

**Acceptance Criteria:**
- [ ] Dashboard uses new color palette and typography
- [ ] Group list uses new card styling
- [ ] Replace sidebar with Orbital Navigation
- [ ] Add Agent Orb to all screens
- [ ] Existing functionality preserved
- [ ] Dark mode works correctly with new tokens

---

## Epic 3: Smart Expense Entry (UX-Enhanced)

The existing Epic 3 stories remain, but with UX integration:

### Story 3.1: Create Expense Model and Basic Entry
*No UX changes - backend/data model story*

### Story 3.2: Natural Language Input Interface
**UX Enhancement:** Use SmartInputModal from 2.5.4 instead of basic form

**Additional AC:**
- [ ] Input opens via Agent Orb tap (long-press or double-tap)
- [ ] Or via + button in Group View
- [ ] AI commentary bubble shows during processing
- [ ] Streaming text at 30-50ms per character

### Story 3.3: AI Parsing Service Integration
**UX Enhancement:** Add personality selection and streaming

**Additional AC:**
- [ ] Support 4 personality modes (Professional, Friendly, Funny, F3-PBS)
- [ ] Return streaming-compatible response format
- [ ] Include personality-flavored commentary in response

### Story 3.4: Manual Override of Parsed Data
**UX Enhancement:** Dual-mode editing (inline vs modal)

**Additional AC:**
- [ ] Simple edits (amount, description): inline in preview card
- [ ] Complex edits (split, members): tap to expand modal
- [ ] Changes highlighted with subtle animation

### Story 3.5-3.8: Split Logic Stories
**UX Enhancement:** Visual Split Picker component

**Additional AC:**
- [ ] Use visual card selector (Equal/Unequal/Percentage/Shares icons)
- [ ] Member Chips with toggle include/exclude
- [ ] Excluded members grayed + struck through (not hidden)

---

## Epic 4: Trust & Confirmation Workflow (UX-Enhanced)

### Story 4.5: Activity Feed Display
**UX Enhancement:** Chat-style feed in Group View

**Additional AC:**
- [ ] Activity items styled as chat bubbles
- [ ] AI personality comments appear inline
- [ ] Streaming effect for new entries

---

## Epic 5: Settlement & Payment Tracking (UX-Enhanced)

### Story 5.1: Mark Debt as Settled
**UX Enhancement:** Swipe-to-settle gesture

**Additional AC:**
- [ ] Swipe right on expense card triggers Mark Paid
- [ ] Optimistic UI: immediate visual update
- [ ] Undo toast with 3-second countdown
- [ ] Card fades out with amber glow on confirmation

### Story 5.2: Owner Confirms Settlement
**UX Enhancement:** "Payment = Silence" pattern

**Additional AC:**
- [ ] Confirmed settlement: card disappears completely
- [ ] Zero balance: celebratory empty state with amber tint
- [ ] No unnecessary notifications after settlement

---

## Epic 6: Notifications (UX-Enhanced)

### Story 6.4: Snooze Notification
**UX Enhancement:** Swipe gesture support

**Additional AC:**
- [ ] Swipe left on notification to reveal snooze options
- [ ] Duration picker: 1 day, 3 days, 1 week

---

## Epic 7: Offline Capability (No Major UX Changes)

Stories remain as-is. Offline indicators use new design tokens.

---

## Post-MVP: Epic 8 - UX Polish & Advanced Features

After all functional epics complete:

### Story 8.1: AI Personality Selector
- [ ] Group settings page with personality picker
- [ ] F3-PBS warning modal with explicit opt-in
- [ ] Preview sample commentary before selection

### Story 8.2: Desktop Power Features
- [ ] Cmd/Ctrl+N: Quick add expense
- [ ] Cmd/Ctrl+K: Command palette
- [ ] Keyboard shortcuts for common actions
- [ ] Hover-based Orb expansion

### Story 8.3: Animation Polish
- [ ] Page transition animations
- [ ] Micro-interactions refinement
- [ ] Loading state skeleton patterns
- [ ] Reduced motion alternatives

### Story 8.4: Accessibility Audit & Fixes
- [ ] Screen reader testing pass
- [ ] Keyboard navigation audit
- [ ] Color contrast verification
- [ ] Touch target sizing check

---

## Design Artifact Plans

### 1. Wireframe Generation Plan

**Tool:** Excalidraw (free, collaborative) or Figma (if available)

**Scope:** Key screens based on UX spec screen hierarchy

| Wireframe | Priority | Based On |
|-----------|----------|----------|
| Dashboard with Group Cards | P0 | UX Spec: Design Direction |
| Group View with Chat Feed | P0 | UX Spec: Journey 1 |
| Smart Input Modal | P0 | UX Spec: Smart Input Component |
| Agent Orb + Orbital Nav | P0 | UX Spec: Navigation Patterns |
| Expense Card (Swipeable) | P1 | UX Spec: Swipeable Card |
| Settlement Flow | P1 | UX Spec: Journey 2 |
| Edit Expense Modal | P1 | UX Spec: Journey 3 |
| Empty States | P2 | UX Spec: Empty States |
| Settings/Profile | P2 | Standard patterns |

**Deliverable:** Low-fidelity wireframes showing layout, component placement, and flow

**Recommended Workflow:**
```
/bmad:bmm:workflows:create-excalidraw-wireframe
```

### 2. Interactive Prototype Plan

**Tool:** Figma (prototyping mode) or ProtoPie (for advanced animations)

**Scope:** Clickable prototype demonstrating key flows

| Prototype Flow | Priority | Interactions |
|----------------|----------|--------------|
| Add Expense (Orb → Modal → Confirm) | P0 | Tap, streaming text, card appearance |
| Orbital Navigation | P0 | Expand/collapse animation |
| Settlement Flow | P1 | Swipe gesture, fade-out |
| Error Correction | P1 | Inline edit, modal edit |

**Deliverable:** Clickable prototype for user testing before implementation

**Recommended Approach:**
1. Build wireframes first
2. Add interactions in Figma
3. Test with 3-5 users
4. Iterate based on feedback
5. Finalize before development

### 3. Figma Visual Design Plan

**Scope:** High-fidelity UI implementation with design tokens

| Figma Deliverable | Contents |
|-------------------|----------|
| **Design Tokens** | Color variables, typography styles, spacing, shadows |
| **Component Library** | Agent Orb, Smart Input, Swipeable Card, Balance Display, etc. |
| **Screen Designs** | All key screens in light + dark mode |
| **Responsive Variants** | Mobile, Tablet, Desktop breakpoints |
| **Interaction Specs** | Animation timing, easing curves, state transitions |
| **Developer Handoff** | Inspect mode with CSS/token values |

**Recommended Structure:**
```
ClearDues Design System (Figma)
├── 🎨 Foundations
│   ├── Colors (light/dark)
│   ├── Typography
│   ├── Spacing & Layout
│   └── Effects (shadows, blur)
├── 🧩 Components
│   ├── Agent Orb
│   ├── Orbital Nav
│   ├── Smart Input
│   ├── Swipeable Card
│   ├── Balance Display
│   ├── Member Chips
│   └── [shadcn overrides]
├── 📱 Screens - Mobile
│   ├── Dashboard
│   ├── Group View
│   ├── Smart Input Modal
│   └── Settings
├── 💻 Screens - Desktop
│   └── [responsive variants]
└── 🔄 Prototypes
    ├── Add Expense Flow
    ├── Settlement Flow
    └── Navigation Flow
```

---

## Implementation Order Recommendation

```
Phase 1: UX Foundation (Epic 2.5)
  └─ Stories 2.5.1-2.5.7 (design system + core components)

Phase 2: Feature Development with UX (Epic 3-7)
  └─ Each story includes UX-enhanced acceptance criteria

Phase 3: UX Polish (Epic 8)
  └─ Advanced features, animation polish, accessibility

Design Artifacts (Parallel Track):
  └─ Wireframes → Prototype → Visual Design → Developer Handoff
```

---

## Wireframe/Prototype/Figma: Execution Options

### Option A: Design-First (Recommended for Quality)
1. Create wireframes before Epic 2.5
2. Build prototype, test with users
3. Finalize Figma designs
4. Implement Epic 2.5 based on finalized designs
5. Continue Epic 3+

**Pros:** Higher quality, user-tested, clear implementation target
**Cons:** Delays development start by 1-2 weeks

### Option B: Parallel Design + Development
1. Start Epic 2.5 with UX spec as reference
2. Create wireframes/prototype in parallel
3. Iterate on both tracks
4. Finalize Figma during Epic 3

**Pros:** Faster start, iterative approach
**Cons:** Potential rework if designs diverge

### Option C: Code-First, Design-Document (Current Approach)
1. Implement Epic 2.5 directly from UX spec
2. Create Figma as documentation after code
3. Use Figma for future features

**Pros:** Fastest to working code
**Cons:** No user testing, Figma becomes post-hoc documentation

---

## Summary: Recommended Path Forward

1. **Insert Epic 2.5** (UX Foundation) before Epic 3
2. **Create wireframes** for key screens using Excalidraw
3. **Build lightweight prototype** for Add Expense flow
4. **Implement Epic 2.5** stories (7 stories, ~2-3 sessions)
5. **Continue Epic 3+** with UX-enhanced acceptance criteria
6. **Build Figma library** during/after Epic 3 for documentation
7. **Epic 8** for polish after functional completion

This approach balances quality with velocity — you get the distinctive UX without excessive delay.
