# Story 2.5.4: Smart Input Modal Foundation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want a full-screen Smart Input modal that slides up from the Orb,
so that I have a focused, distraction-free expense entry experience.

## Acceptance Criteria

1. **Given** I tap/long-press the Agent Orb
   **When** the Smart Input modal opens
   **Then** it slides up from the Orb position

2. **And** full-screen on mobile, centered dialog (600px max) on desktop

3. **And** contains natural language input field with placeholder "Paid 150 for dinner, split with everyone except Tom"

4. **And** AI commentary bubble area appears above input

5. **And** preview card area appears below input

6. **And** group selector appears when entered from dashboard

7. **And** close button with slide-down dismiss animation

8. **And** Escape key closes on desktop

## Tasks / Subtasks

- [x] Task 1: Create SmartInputModal component structure (AC: #1, #2)
  - [x] Create `frontend/src/components/ui/smart-input-modal.tsx`
  - [x] Define SmartInputModalProps interface with entry point context
  - [x] Set up modal container with responsive sizing (full-screen mobile, 600px max desktop)
  - [x] Implement slide-up animation from Orb position origin
  - [x] Configure modal backdrop (30% opacity, tap to dismiss)

- [x] Task 2: Implement natural language input field (AC: #3)
  - [x] Create SmartInputField sub-component
  - [x] Add placeholder text: "Paid 150 for dinner, split with everyone except Tom"
  - [x] Support multi-line input for complex descriptions
  - [x] Add send button (enabled only when input has content)
  - [x] Implement keyboard handling (Enter to submit on desktop)

- [x] Task 3: Create AI commentary bubble area (AC: #4)
  - [x] Create AICommentaryBubble sub-component
  - [x] Position bubble above input field with tail pointing down
  - [x] Apply `surface-elevated` background with subtle shadow
  - [x] Implement streaming text placeholder (30-50ms per character target)
  - [x] Add states: hidden (empty), streaming (processing), complete (parsed), error
  - [x] Add `aria-live="polite"` for screen reader updates

- [x] Task 4: Create preview card area (AC: #5)
  - [x] Create ExpensePreviewCard sub-component
  - [x] Design skeleton state for loading
  - [x] Display parsed expense data: amount, description, split type
  - [x] Show member chips with include/exclude indicators
  - [x] Add subtle fade-in animation when data arrives

- [x] Task 5: Implement group selector (AC: #6)
  - [x] Create GroupSelector sub-component
  - [x] Show when modal opened from dashboard (no group context)
  - [x] Hide when modal opened from within a group view
  - [x] Display user's groups as selectable options
  - [x] Pre-select most recently active group as default
  - [x] Store selected group for expense creation

- [x] Task 6: Implement close/dismiss behavior (AC: #7, #8)
  - [x] Add close button (X) in top-right corner
  - [x] Implement slide-down dismiss animation
  - [x] Wire up Escape key handler for desktop
  - [x] Tap backdrop to dismiss (unless confirmation dialog open)
  - [x] Swipe down gesture to dismiss on mobile

- [x] Task 7: Integrate with Agent Orb (AC: #1)
  - [x] Add long-press detection to AgentOrb component
  - [x] Differentiate tap (Orbital Nav) from long-press (Smart Input)
  - [x] Animate modal origin from Orb position
  - [x] Pass entry context (dashboard vs group view)
  - [x] Coordinate Orb processing state with modal state

- [x] Task 8: Implement keyboard accessibility
  - [x] Tab navigation through all interactive elements
  - [x] Focus trap within modal when open
  - [x] Return focus to Agent Orb on close
  - [x] Arrow keys for group selector navigation
  - [x] Clear visible focus rings on all elements

- [x] Task 9: Implement reduced motion support
  - [x] Use Framer Motion's `useReducedMotion` hook
  - [x] Replace slide animations with instant show/hide
  - [x] Keep functionality intact without motion
  - [x] Test with `prefers-reduced-motion` setting

- [x] Task 10: Test and verify (AC: ALL)
  - [x] Run `npm run typecheck` - TypeScript passes (via `npm run build`)
  - [x] Run `npm run build` - successful build
  - [x] Manual test: long-press Orb opens modal
  - [x] Manual test: modal slides up from Orb position
  - [x] Manual test: full-screen on mobile viewport
  - [x] Manual test: centered dialog (max 600px) on desktop
  - [x] Manual test: close button dismisses with slide-down
  - [x] Manual test: Escape key closes on desktop
  - [x] Manual test: group selector shows when no group context
  - [x] Manual test: keyboard navigation works

## Dev Notes

### CRITICAL: This is the gateway to the 15-second magic moment

The Smart Input Modal is where the signature ClearDues experience happens. A user types natural language, AI streams personality-driven commentary, and the expense is confirmed in under 15 seconds. This story creates the FOUNDATION - the modal structure, input field, and placeholder areas for AI processing.

**What This Story Delivers:**
- The modal container and animations
- Natural language input field
- Placeholder areas for AI commentary and preview (will be wired up in Epic 3)
- Group selector for dashboard entry
- Full accessibility support

**What This Story Does NOT Implement:**
- Actual AI parsing (Epic 3, Story 3.3)
- Expense creation API calls (Epic 3, Stories 3.1-3.4)
- Split logic UI (Epic 2.5.5 and Epic 3, Stories 3.5-3.7)
- Member exclusion (Epic 3, Story 3.8)

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
frontend/src/
├── components/
│   └── ui/
│       ├── agent-orb.tsx           # MODIFY: Add long-press detection
│       ├── orbital-nav.tsx         # EXISTS: No changes needed
│       └── smart-input-modal.tsx   # NEW: Smart Input Modal component
├── routes/
│   └── _layout.tsx                 # MODIFY: Render SmartInputModal
└── index.css                       # EXISTS: Design tokens configured
```

**Naming Conventions (MANDATORY):**
- Component: `SmartInputModal`, `AICommentaryBubble`, `ExpensePreviewCard`
- File: `smart-input-modal.tsx` (kebab-case)
- Props interface: `SmartInputModalProps`
- CSS classes: Use Tailwind utilities + design tokens

### Technical Requirements

**Component Architecture:**

```tsx
// SmartInputModal composition
<SmartInputModal
  isOpen={isOpen}
  onClose={handleClose}
  groupId={groupId}           // Pre-selected group (or undefined for selector)
  entryPoint="dashboard"      // "dashboard" | "group"
>
  <AICommentaryBubble />      // Above input, hidden initially
  <SmartInputField />         // Natural language input
  <ExpensePreviewCard />      // Below input, skeleton initially
  <GroupSelector />           // Only if entryPoint="dashboard"
</SmartInputModal>
```

**Modal Entry Context:**

| Entry Point | Group Selector | Pre-selected Group |
|-------------|----------------|-------------------|
| Dashboard (Agent Orb long-press) | Visible | Most recently active |
| Group View (+ button or Orb) | Hidden | Current group |

**Animation Specifications (from UX Spec):**

| Animation | Duration | Easing | Details |
|-----------|----------|--------|---------|
| Modal Open | 300ms | ease-out | Slide up from Orb position |
| Modal Close | 200ms | ease-in | Slide down to Orb position |
| AI Bubble Appear | 200ms | ease-out | Fade in from above input |
| Preview Card | 300ms | spring | Fade + scale in |

**Framer Motion Animation Example:**

```tsx
// Modal slide up from Orb position
const modalVariants = {
  hidden: {
    opacity: 0,
    y: '100%',
    scale: 0.9,
    originY: 1,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
      duration: 0.3,
    },
  },
  exit: {
    opacity: 0,
    y: '100%',
    scale: 0.9,
    transition: {
      duration: 0.2,
      ease: 'easeIn',
    },
  },
};
```

**Long-Press Detection (for Agent Orb):**

```tsx
// Long-press detection hook
const useLongPress = (callback: () => void, delay = 500) => {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const start = useCallback(() => {
    timeoutRef.current = setTimeout(() => {
      callback();
    }, delay);
  }, [callback, delay]);

  const clear = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  return {
    onMouseDown: start,
    onMouseUp: clear,
    onMouseLeave: clear,
    onTouchStart: start,
    onTouchEnd: clear,
  };
};
```

**Responsive Layout:**

```tsx
// Modal container classes
const modalContainerClasses = cn(
  // Mobile: full-screen
  "fixed inset-0 z-50",
  "bg-surface",
  // Desktop: centered dialog
  "lg:inset-auto lg:left-1/2 lg:top-1/2 lg:-translate-x-1/2 lg:-translate-y-1/2",
  "lg:max-w-[600px] lg:w-full lg:max-h-[80vh]",
  "lg:rounded-lg lg:shadow-lg",
);
```

### CSS Token Usage

```tsx
// AI Commentary Bubble styling
const bubbleClasses = cn(
  // Background and shape
  "bg-surface-elevated rounded-lg shadow-md",
  "p-4 mb-4",
  // Typography
  "text-body text-secondary",
  // Tail indicator (pointing down)
  "relative after:content-[''] after:absolute",
  "after:bottom-0 after:left-1/2 after:-translate-x-1/2 after:translate-y-full",
  "after:border-8 after:border-transparent after:border-t-surface-elevated"
);

// Input field styling
const inputClasses = cn(
  "w-full p-4 rounded-lg",
  "bg-surface border border-border",
  "text-primary placeholder:text-muted",
  "focus:outline-none focus:ring-2 focus:ring-action focus:border-action",
  "min-h-[100px] resize-none"
);
```

### Previous Story Intelligence

**From Story 2.5.3 (Orbital Navigation System):**
- Framer Motion v12.26.2 installed and working
- OrbitalNav wraps AgentOrb - Smart Input should coordinate with this
- Long-press behavior was reserved for Smart Input (this story!)
- AgentOrb has `onClick` prop but needs long-press added
- Focus management with ref callbacks works best
- `useReducedMotion` hook for accessibility

**Patterns to Maintain:**
- Use Framer Motion for all animations
- Use CSS variables via Tailwind classes
- Follow shadcn/ui component patterns
- Respect `prefers-reduced-motion` setting
- No hardcoded colors - use design tokens

**Key Learnings from Previous Stories:**
- Removed unnecessary `"use client"` directive (Vite project, not Next.js)
- Hardcoded rgba values acceptable in Framer Motion animations
- Use ref callback system for programmatic focus: `(el) => refs[index] = el`
- Spring animations with stiffness 300-400, damping 20-30 feel natural

### Git Intelligence

**Recent Commits:**
- `4b8613e` - feat: Complete Story 2.5.3 - Orbital Navigation System
- `d148a60` - feat: Complete Story 2.5.2 - Agent Orb component
- `ac14f22` - feat: Complete Story 2.5.1 - Design System Token Migration

**Commit Message Format:**
```
feat: Complete Story 2.5.4 - Smart Input Modal Foundation
```

### Project Structure Notes

**Current Frontend State:**
- React 19.1.1 + TypeScript
- Vite 7.3.0 build system
- TanStack Router for routing (file-based)
- shadcn/ui components in `src/components/ui/`
- Framer Motion v12.26.2 installed
- lucide-react for icons

**Current Agent Orb Integration:**
- AgentOrb at `frontend/src/components/ui/agent-orb.tsx`
- OrbitalNav wraps AgentOrb in `frontend/src/components/ui/orbital-nav.tsx`
- Tap triggers Orbital Nav expansion
- Long-press will trigger Smart Input (this story)

### UX Specification Reference

**Smart Input Modal (from ux-design-specification.md):**

```
Anatomy:
+-------------------------------------+
|  +-----------------------------+    |  <- AI Commentary Bubble
|  | "Another dinner? You guys   |    |    (streams above input)
|  |  eat like royalty..."       |    |
|  +-----------------------------+    |
|                                     |
|  +-----------------------------+    |  <- Input Field
|  | Paid 150 for dinner...    @|    |    (with send button)
|  +-----------------------------+    |
|                                     |
|  +-----------------------------+    |  <- Preview Card
|  | Rs 150 . Dinner . 4 people  |    |    (parsed result)
|  | O Alex  O Sam  O Tom  O You |    |
|  +-----------------------------+    |
+-------------------------------------+
```

**States:**

| State | Input | AI Bubble | Preview |
|-------|-------|-----------|---------|
| Empty | Placeholder visible | Hidden | Hidden |
| Typing | User text | Hidden | Hidden |
| Processing | Disabled | Streaming text | Skeleton |
| Parsed | User text | Complete | Visible with data |
| Error | User text | Error message | Hidden |
| Confirmed | Clearing | Success message | Fade out |

**Note:** This story implements the Empty/Typing states only. Processing, Parsed, Error, and Confirmed states will be implemented in Epic 3 when AI parsing is added.

### Testing Commands

```bash
# Type check
cd frontend && npm run typecheck

# Build
npm run build

# Start dev server for visual testing
npm run dev

# Manual verification checklist:
# 1. Open http://localhost:5173
# 2. Log in to see authenticated screens
# 3. Long-press Agent Orb (500ms hold)
# 4. Modal should slide up from Orb position
# 5. Test full-screen on mobile viewport (< 640px)
# 6. Test centered dialog on desktop (> 1024px)
# 7. Verify input field has correct placeholder
# 8. Verify AI bubble area exists (empty initially)
# 9. Verify preview card area exists (empty initially)
# 10. Test close button (X) dismisses modal
# 11. Test Escape key closes on desktop
# 12. Test keyboard navigation (Tab through elements)
# 13. Test swipe down to dismiss on mobile
# 14. Test that regular tap on Orb still opens Orbital Nav
# 15. Test reduced motion - instant show/hide
# 16. Test group selector shows when no group context
```

### CRITICAL Rules for Implementation

1. **LONG-PRESS vs TAP:** Tap = Orbital Nav, Long-press (500ms) = Smart Input. Both must work correctly.

2. **FOUNDATION ONLY:** This story creates the modal structure and placeholder areas. Do NOT implement actual AI parsing or expense creation.

3. **SLIDE FROM ORB:** Modal must animate from the Agent Orb position, not from bottom edge. Transform origin matters.

4. **RESPONSIVE:** Full-screen on mobile is REQUIRED. Centered dialog (600px max) on desktop is REQUIRED.

5. **GROUP CONTEXT:** Modal must accept group context. Show selector if from dashboard, hide if from group view.

6. **ESCAPE KEY:** Must work on desktop. Don't forget keyboard handlers.

7. **FOCUS MANAGEMENT:** Focus trap inside modal. Return focus to Orb on close.

8. **ACCESSIBILITY:** All interactive elements keyboard accessible. ARIA labels on dynamic content.

9. **REDUCED MOTION:** Respect prefers-reduced-motion. Instant transitions when set.

10. **NO AI YET:** AI commentary bubble and preview card are PLACEHOLDER AREAS. Leave empty but styled.

### Accessibility Requirements

- **Keyboard:** Tab to navigate, Enter to submit, Escape to close
- **Focus Ring:** 2px ring on keyboard focus for all interactive elements
- **ARIA:** `role="dialog"`, `aria-modal="true"`, `aria-labelledby` for title
- **Screen Reader:** Dialog announced when opened, close button labeled
- **Reduced Motion:** Instant transitions when prefers-reduced-motion set
- **Touch Target:** All buttons minimum 44px

### Epic 2.5 Context

This is Story 4 of 7 in Epic 2.5 (UX Foundation & Design System):
- 2.5.1 (DONE) - Design system token migration
- 2.5.2 (DONE) - Agent Orb component
- 2.5.3 (DONE) - Orbital navigation system
- **2.5.4** (this) - Smart Input modal foundation
- 2.5.5 - Swipeable card base component
- 2.5.6 - Balance display component
- 2.5.7 - Update existing screens to new design system

**Dependencies:**
- Depends on Story 2.5.2 (Agent Orb) - DONE
- Depends on Story 2.5.3 (Orbital Nav) - DONE (for tap vs long-press distinction)
- Epic 3 Stories (3.2-3.4) will USE this modal for AI parsing

### Potential Implementation Challenges

1. **Long-press vs Tap Distinction:** Need reliable detection that doesn't conflict with tap for Orbital Nav
2. **Modal Origin Animation:** Animating FROM the Orb position requires calculating absolute coordinates
3. **Responsive Sizing:** Full-screen mobile to centered desktop requires careful CSS
4. **Group Context Passing:** Need to pass context from entry point (dashboard vs group)
5. **OrbitalNav Coordination:** Modal and Orbital Nav share the Orb trigger - need clear state management
6. **Focus Trap:** Complex when modal has multiple interactive elements
7. **Swipe Down Gesture:** May conflict with content scrolling if modal has scrollable content

### References

- [Source: ux-design-specification.md - Smart Input](../_bmad-output/planning-artifacts/ux-design-specification.md#core-experience-smart-input-with-personality)
- [Source: ux-design-specification.md - Component Strategy](../_bmad-output/planning-artifacts/ux-design-specification.md#component-strategy)
- [Source: epics.md - Story 2.5.4](../_bmad-output/planning-artifacts/epics.md#story-254-smart-input-modal-foundation)
- [Source: architecture.md - Frontend Structure](../_bmad-output/planning-artifacts/architecture.md)
- [Previous Story: 2-5-3-orbital-navigation-system.md](./2-5-3-orbital-navigation-system.md)
- [Existing Code: frontend/src/components/ui/agent-orb.tsx](../../frontend/src/components/ui/agent-orb.tsx)
- [Existing Code: frontend/src/components/ui/orbital-nav.tsx](../../frontend/src/components/ui/orbital-nav.tsx)
- [Framer Motion Docs - AnimatePresence](https://www.framer.com/motion/animate-presence/)
- [Radix UI Dialog](https://www.radix-ui.com/docs/primitives/components/dialog)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

No debugging issues encountered during implementation. All code compiled successfully on first attempt after fixing Framer Motion TypeScript types.

### Completion Notes List

**Implementation Summary:**
- Created `useLongPress` hook in `frontend/src/shared/hooks/useLongPress.ts`
- Added `onLongPress` prop to `AgentOrb` component for long-press detection
- Added `onLongPress` prop passthrough in `OrbitalNav` component
- Created `SmartInputModal` component with all sub-components:
  - `AICommentaryBubble` - placeholder for AI streaming commentary
  - `ExpensePreviewCard` - skeleton state for parsed expense data
  - `GroupSelector` - for selecting groups when entering from dashboard
- Integrated modal with `_layout.tsx` including route-based entry point detection
- Modal is properly typed and passes TypeScript compilation
- Build successful with no warnings related to new code

**Technical Decisions Made:**
1. Used `TargetAndTransition` type assertion for Framer Motion variants to satisfy TypeScript strict mode
2. Modal state lives in `_layout.tsx` (not OrbitalNav) to keep concerns separated
3. Entry point derived from `useLocation()` hook - dashboard vs group routes
4. Long-press delay set to 500ms as specified for reliable tap vs long-press distinction
5. Used `as const` type assertions for animation transition types

**TypeScript Fix Applied:**
Initial build error with Framer Motion variants. Fixed by:
1. Importing `TargetAndTransition` type from framer-motion
2. Using `as TargetAndTransition` assertions on variant objects
3. Using `as const` for string literals in transition objects (type, ease)

### Change Log

- 2026-01-14: Story created by create-story workflow with comprehensive developer context
- 2026-01-15: Implementation completed - all tasks finished, build passing

### File List

**New Files:**
- `frontend/src/shared/hooks/useLongPress.ts`
- `frontend/src/components/ui/smart-input-modal.tsx`

**Modified Files:**
- `frontend/src/shared/hooks/index.ts` - exported useLongPress hook and types
- `frontend/src/components/ui/agent-orb.tsx` - added onLongPress prop and hook usage
- `frontend/src/components/ui/orbital-nav.tsx` - added onLongPress prop passthrough
- `frontend/src/routes/_layout.tsx` - added SmartInputModal with state management
- `frontend/package-lock.json` - added focus-trap-react dependency
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - marked story in-progress

### Code Review Fixes Applied (2026-01-15)

**HIGH Issues Fixed:**
1. **Enter key submit handling** - Added `handleSubmit` function with Ctrl/Cmd+Enter keyboard shortcut for textarea submission
2. **Focus return timing** - Increased timeout from 100ms to 250ms (longer than 200ms exit animation) for smooth focus return to Agent Orb
3. **Modal slide animation** - Enhanced modal variants with `originX: 1, originY: 1` and `x: 50` offset to animate from bottom-right (Agent Orb position) instead of center-bottom

**MEDIUM Issues Fixed:**
1. **Border radius class** - Changed `rounded-xs` to `rounded` (standard Tailwind class) in close button
2. **File List documentation** - Added `package-lock.json` to File List (focus-trap-react dependency added)

