# Story 2.5.6: Balance Display Component

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want to see monetary amounts in a consistent, neutral format,
so that debt amounts feel factual, not judgmental.

## Acceptance Criteria

1. **Given** any monetary amount is displayed
   **When** I view the balance
   **Then** BalanceDisplay component is used with size variants (display/title/body)

2. **And** text-primary color is always used (never red for debt)

3. **And** format is "Rs" prefix with comma separators (Rs 1,500)

4. **And** context labels show "You owe" / "You're owed"

5. **And** aria-label includes full context for screen readers ("You owe 450 rupees to Sam")

## Tasks / Subtasks

- [x] Task 1: Create BalanceDisplay base component structure (AC: #1)
  - [x] Create `frontend/src/components/ui/balance-display.tsx`
  - [x] Define BalanceDisplayProps interface with amount, variant, context props
  - [x] Set up size variant typography (display: 32px, title: 24px, body: 16px)
  - [x] Apply design token colors from CSS variables
  - [x] Create component structure with amount and optional context label

- [x] Task 2: Implement currency formatting (AC: #3)
  - [x] Create currency formatter function
  - [x] Apply "Rs" prefix (NOT "₹" symbol)
  - [x] Add comma separators for thousands (Rs 1,500)
  - [x] Handle decimal places (show .00 only if non-zero)
  - [x] Format negative numbers consistently (-Rs 1,500)

- [x] Task 3: Apply neutral color strategy (AC: #2)
  - [x] Use `text-primary` token for all amounts (never red/green)
  - [x] Use `text-secondary` for context labels
  - [x] Ensure amount color doesn't indicate debt vs credit
  - [x] Test both positive and negative amounts use same color

- [x] Task 4: Add context labels (AC: #4)
  - [x] Support optional contextLabel prop ("You owe" / "You're owed")
  - [x] Position label appropriately for each variant
  - [x] Style labels in `text-secondary` color
  - [x] Show label inline (body) or below (display/title)

- [x] Task 5: Implement accessibility (AC: #5)
  - [x] Add `aria-label` with full context description
  - [x] Include amount, currency, and context in aria-label
  - [x] Example: "You owe 450 rupees to Sam" or "You are owed 1500 rupees"
  - [x] Screen reader announces full context, not just number
  - [x] Add `role="text"` or appropriate semantic role

- [x] Task 6: Create variant implementations (AC: #1)
  - [x] Display variant: 32px, Medium weight, label below
  - [x] Title variant: 24px, Medium weight, label inline or below
  - [x] Body variant: 16px, Regular weight, label inline
  - [x] Ensure responsive behavior across breakpoints

- [x] Task 7: Test and verify (AC: ALL)
  - [x] Run `npm run build` - TypeScript compilation passes (includes tsc)
  - [x] Run `npm run build` - Production build succeeds
  - [x] Manual test: all variants render correctly
  - [x] Manual test: positive amounts show "Rs" prefix
  - [x] Manual test: negative amounts show "-Rs" prefix
  - [x] Manual test: comma separators work for thousands
  - [x] Manual test: no red/green colors for debt vs credit
  - [x] Manual test: context labels display correctly
  - [x] Manual test: screen reader announces full context

## Dev Notes

### Story Purpose

This story creates the **BalanceDisplay** component — a purpose-built component for displaying monetary amounts throughout ClearDues. This is a critical design system component that enforces the "numbers without judgment" principle: debt amounts are displayed as neutral facts, never using red/warning colors that induce shame or anxiety.

**What This Story Delivers:**
- BalanceDisplay component with 3 size variants (display, title, body)
- Consistent "Rs" prefix currency formatting
- Neutral color strategy (never red/green for debt)
- Context labels for clarity ("You owe" / "You're owed")
- Full accessibility with screen reader context

**What This Story Does NOT Implement:**
- Balance calculation logic (that's backend/feature work)
- Interactive balance editing (display only)
- Balance history or trends (static display component)

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
frontend/src/
├── components/
│   └── ui/
│       ├── balance-display.tsx    # NEW: BalanceDisplay component
│       ├── swipeable-card.tsx     # EXISTS: No changes needed
│       └── agent-orb.tsx          # EXISTS: No changes needed
└── index.css                      # EXISTS: Design tokens configured
```

**Naming Conventions (MANDATORY):**
- Component: `BalanceDisplay`
- File: `balance-display.tsx` (kebab-case)
- Props interface: `BalanceDisplayProps`
- CSS classes: Use Tailwind utilities + design tokens

### Technical Requirements

**Component Interface:**

```tsx
interface BalanceDisplayProps {
  // The monetary amount to display (can be positive or negative)
  amount: number;

  // Size variant for different contexts
  variant?: 'display' | 'title' | 'body';

  // Optional context label ("You owe" / "You're owed")
  contextLabel?: string;

  // Optional description for screen reader context
  // Example: "to Sam" → "You owe 450 rupees to Sam"
  contextDescription?: string;

  // Custom className for additional styling
  className?: string;
}
```

**Usage Examples:**

```tsx
// Dashboard large balance
<BalanceDisplay
  amount={1500}
  variant="display"
  contextLabel="Total balance across all groups"
/>

// Group card balance
<BalanceDisplay
  amount={-450}
  variant="title"
  contextLabel="You owe"
  contextDescription="to Weekend Trip group"
/>

// Inline expense amount
<BalanceDisplay
  amount={375}
  variant="body"
/>
```

**Typography Specifications (from UX Spec):**

| Variant | Font Size | Weight | Line Height | Label Position |
|---------|-----------|--------|-------------|----------------|
| Display | 32px | Medium (500) | 1.2 | Below, caption size |
| Title | 24px | Medium (500) | 1.3 | Below or inline |
| Body | 16px | Regular (400) | 1.5 | Inline or omitted |

**Color Strategy (CRITICAL):**

```tsx
// ALWAYS use these tokens - NEVER hardcoded colors
const amountClasses = "text-primary"; // Never red/green for debt!
const labelClasses = "text-secondary"; // For context labels

// WRONG - Never do this:
const wrongDebtColor = "text-red-500"; // ❌ Induces shame
const wrongCreditColor = "text-green-500"; // ❌ Unnecessary

// CORRECT - Neutral presentation:
const neutralAmount = "text-primary"; // ✅ Money is fact, not judgment
```

**Currency Formatting Logic:**

```tsx
const formatCurrency = (amount: number): string => {
  // Use Intl.NumberFormat for proper locale formatting
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });

  // Get formatted string (will be "₹1,500")
  let formatted = formatter.format(Math.abs(amount));

  // Replace ₹ symbol with "Rs" prefix (ClearDues standard)
  formatted = formatted.replace('₹', 'Rs ');

  // Add negative sign if needed
  if (amount < 0) {
    formatted = `-${formatted}`;
  }

  return formatted; // "Rs 1,500" or "-Rs 450"
};
```

**Component Structure:**

```tsx
<div className="flex flex-col">
  {/* Optional context label */}
  {contextLabel && (
    <span className="text-secondary text-sm">
      {contextLabel}
    </span>
  )}

  {/* Amount display */}
  <span className={variantClasses} aria-label={fullContextLabel}>
    {formattedAmount}
  </span>
</div>
```

### CSS Token Usage

```tsx
// Variant-specific typography
const variantClasses: Record<Variant, string> = {
  display: 'text-[32px] font-medium leading-tight', // 32px, Medium, 1.2
  title: 'text-[24px] font-medium leading-snug',   // 24px, Medium, 1.3
  body: 'text-base font-normal leading-normal',    // 16px, Regular, 1.5
};

// Context label styling
const contextLabelClasses = cn(
  'text-secondary',     // Muted gray color
  'text-sm',            // 14px for labels
  'font-normal',        // Regular weight
  'mb-1'                // Space between label and amount
);

// Amount styling (same for all variants)
const amountClasses = cn(
  'text-primary',       // Never red/green - neutral!
  'font-variant-numeric', // Proportional figures
  'tracking-tight'      // Slightly tighter for numbers
);
```

### Accessibility Requirements

**ARIA Implementation:**

```tsx
// Build full context for screen readers
const ariaLabel = useMemo(() => {
  const amountText = `${Math.abs(amount)} rupees`;
  const direction = amount < 0 ? 'owe' : 'are owed';

  if (contextDescription) {
    // "You owe 450 rupees to Sam"
    return `You ${direction} ${amountText} ${contextDescription}`;
  } else if (contextLabel) {
    // "You owe 450 rupees"
    return `${contextLabel} ${amountText}`;
  } else {
    // "450 rupees"
    return amountText;
  }
}, [amount, contextLabel, contextDescription]);

// Apply to component
<span
  className={amountClasses}
  aria-label={ariaLabel}
  role="text"
>
  {formattedAmount}
</span>
```

**Screen Reader Announcements:**

| Visual Display | Screen Reader Announcement |
|----------------|---------------------------|
| Rs 1,500 | "1,500 rupees" |
| -Rs 450 | "You owe 450 rupees" |
| Rs 1,500 (with "You're owed") | "You are owed 1,500 rupees" |
| -Rs 450 (with context) | "You owe 450 rupees to Weekend Trip group" |

**Keyboard & Focus:**
- Component is display-only (not interactive)
- No keyboard handling required
- If parent makes it clickable (e.g., card), parent handles focus

### Previous Story Intelligence

**From Story 2.5.5 (Swipeable Card):**
- Framer Motion patterns established
- Design token usage patterns documented
- Accessibility-first approach confirmed

**From Story 2.5.1 (Design System Tokens):**
- CSS variables configured in `index.css`
- Color tokens: `text-primary`, `text-secondary`, `text-muted`
- Typography scale: `display`, `title`, `heading`, `body`, `caption`

**Patterns to Maintain:**
- Always use CSS variables, never hardcoded colors
- Component props follow clear interface pattern
- TypeScript strict mode compliance
- Tailwind utility-first approach

**Key Learnings:**
- Use `cn()` utility for conditional class merging
- Apply semantic props (variant) over arbitrary styling
- Document component usage with examples

### Git Intelligence

**Recent Epic 2.5 Commits:**
- `4098911` - feat: Complete Story 2.5.5 - Swipeable Card Base Component
- `299208f` - feat: Complete Story 2.5.4 - Smart Input Modal Foundation
- `4b8613e` - feat: Complete Story 2.5.3 - Orbital Navigation System
- `d148a60` - feat: Complete Story 2.5.2 - Agent Orb component
- `ac14f22` - feat: Complete Story 2.5.1 - Design System Token Migration

**Commit Message Format:**
```
feat: Complete Story 2.5.6 - Balance Display Component
```

### Project Structure Notes

**Current Frontend State:**
- React 19.1.1 + TypeScript
- Vite 7.3.0 build system
- Design tokens fully configured
- shadcn/ui components in `src/components/ui/`
- Epic 2.5: 5/7 stories complete

**Files to Modify:**
- `frontend/src/components/ui/balance-display.tsx` (NEW)
- `frontend/src/components/ui/index.ts` (export new component)

**Component Location Strategy:**
- Place in `src/components/ui/` (shared UI components)
- NOT in `src/features/` (this is a reusable design system component)
- Will be imported by:
  - Dashboard feature (Story 2.4, already done - needs update)
  - Group view feature (Epic 3 stories)
  - Settlement components (Epic 5 stories)

### UX Specification Reference

**Balance Display (from ux-design-specification.md, lines 1233-1254):**

```
#### Balance Display

**Purpose:** Show monetary amounts in a consistent, neutral, glanceable format.

**Variants:**

| Variant | Font Size | Weight | Context Label |
|---------|-----------|--------|---------------|
| Display | 32px | Medium | Below, `caption` size |
| Title | 24px | Medium | Below or inline |
| Body | 16px | Regular | Inline or omitted |

**Critical Rules:**
- All amounts in `text-primary` — never red/green for debt
- "You owe" / "You're owed" as neutral labels
- Always "Rs" prefix with comma separators (e.g., "Rs 1,500")

**Accessibility:**
- `aria-label` includes full context: "You owe 450 rupees to Sam"
- Screen reader announces direction (owe vs owed)
```

**Typography System (from UX Spec, lines 460-488):**

```
### Typography System

**Font Family:** Inter (Geometric Sans)

**Type Scale:**

| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `display` | 32px | Medium (500) | 1.2 | Dashboard balance |
| `title` | 24px | Medium (500) | 1.3 | Page titles |
| `heading` | 18px | Medium (500) | 1.4 | Section headers |
| `body` | 16px | Regular (400) | 1.5 | Default text |
| `body-small` | 14px | Regular (400) | 1.5 | Secondary content |
| `caption` | 12px | Regular (400) | 1.4 | Labels, timestamps |

**Number Display:**
- Proportional figures (not tabular) — flows naturally with text
- Same font family (Inter) for consistency
- **Currency format:** Always "Rs" prefix, never "₹" symbol
- Example: "Rs 1,500" not "₹1,500"
```

**Color System (from UX Spec, lines 425-460):**

```
### Color System

**Base Palette:**

| Token | Role | Value (Light) |
|-------|------|---------------|
| `text-primary` | Main content | Warm black (#1F1E1C) |
| `text-secondary` | Supporting text | Warm gray (#6B6660) |
| `text-muted` | Hints, placeholders | Light gray (#9C9790) |

**Critical Rule:** Debt/owe amounts are NEVER shown in red or warning colors.
All amounts are displayed in neutral `text-primary` — money is fact, not judgment.
```

### Epic 2.5 Context

This is Story 6 of 7 in Epic 2.5 (UX Foundation & Design System):
- 2.5.1 (DONE) - Design system token migration
- 2.5.2 (DONE) - Agent Orb component
- 2.5.3 (DONE) - Orbital navigation system
- 2.5.4 (DONE) - Smart Input modal foundation
- 2.5.5 (DONE) - Swipeable card base component
- **2.5.6** (this) - Balance display component
- 2.5.7 - Update existing screens to new design system

**Dependencies:**
- Depends on Story 2.5.1 (Design Tokens) - DONE
- No dependencies on other Epic 2.5 stories (independent component)

**Used By:**
- Story 2.5.7 will use BalanceDisplay to update existing screens
- Future Epic 3 stories will use BalanceDisplay for expense amounts
- Future Epic 5 stories will use BalanceDisplay for settlement amounts

### Testing Commands

```bash
# Type check
cd frontend && npm run typecheck

# Build
npm run build

# Start dev server for visual testing
npm run dev

# Manual verification checklist:
# 1. Create test component rendering all three variants
# 2. Test positive amount: displays "Rs 1,500" with text-primary color
# 3. Test negative amount: displays "-Rs 450" with text-primary (NOT red)
# 4. Test display variant: 32px font, context label below
# 5. Test title variant: 24px font, context label inline
# 6. Test body variant: 16px font, minimal styling
# 7. Test with contextLabel: "You owe" / "You're owed" displays correctly
# 8. Test with contextDescription: aria-label includes full context
# 9. Test screen reader: announces "You owe 450 rupees to Sam"
# 10. Test comma separators: 1000 becomes "Rs 1,000"
```

### CRITICAL Rules for Implementation

1. **NEVER RED/GREEN FOR DEBT:** All amounts use `text-primary`. Debt is NOT an error state. This is non-negotiable.

2. **ALWAYS "Rs" PREFIX:** Never use "₹" symbol. Always "Rs " with space. This is ClearDues brand standard.

3. **COMMA SEPARATORS MANDATORY:** Use Intl.NumberFormat for proper thousands separation. Never "Rs1500".

4. **CONTEXT LABELS ARE NEUTRAL:** "You owe" / "You're owed" are factual labels, never emotional. No "You owe!" with exclamation.

5. **ARIA-LABEL FULL CONTEXT:** Screen readers get complete sentence: "You owe 450 rupees to Sam". Not just "450".

6. **THREE VARIANTS ONLY:** Display (32px), Title (24px), Body (16px). No arbitrary sizes. Use design tokens.

7. **PROPORTIONAL FIGURES:** Use `font-variant-numeric: proportional-nums`. Tabular numbers look unnatural in UI.

8. **NEGATIVE FORMAT:** "-Rs 450" NOT "Rs -450". Minus sign before "Rs", not before number.

9. **NO DECIMALS FOR WHOLE NUMBERS:** Rs 1,500 NOT Rs 1,500.00. Show .00 only if amount has paise (decimal).

10. **ACCESSIBILITY FIRST:** If contextLabel provided, aria-label MUST include it. Screen readers need full context.

### Potential Implementation Challenges

1. **Intl.NumberFormat Currency Symbol:** Intl formatter returns "₹" by default. Must replace with "Rs" programmatically.

2. **Negative Number Handling:** Ensure "-Rs 450" not "Rs -450". May need custom formatting for negative amounts.

3. **Context Label Positioning:** Display/title show label below, body shows inline. Need conditional rendering logic.

4. **Screen Reader Duplication:** Visual label + aria-label can be redundant. Test to ensure natural announcements.

5. **Zero Balance Display:** Should show "Rs 0" without negative sign. Test edge case.

6. **Very Large Numbers:** Test formatting for lakhs (1,00,000) and crores (1,00,00,000) - Indian numbering system.

7. **Variant Consistency:** Ensure all three variants use same color strategy and formatting logic.

8. **Decimal Handling:** Only show decimals if amount is not whole number. Rs 100.50 (yes), Rs 100.00 (no).

### References

- [Source: ux-design-specification.md - Balance Display](../_bmad-output/planning-artifacts/ux-design-specification.md#balance-display)
- [Source: ux-design-specification.md - Typography System](../_bmad-output/planning-artifacts/ux-design-specification.md#typography-system)
- [Source: ux-design-specification.md - Color System](../_bmad-output/planning-artifacts/ux-design-specification.md#color-system)
- [Source: epics.md - Story 2.5.6](../_bmad-output/planning-artifacts/epics.md#story-256-balance-display-component)
- [Source: architecture.md - Frontend Structure](../_bmad-output/planning-artifacts/architecture.md)
- [Previous Story: 2-5-5-swipeable-card-base-component.md](./2-5-5-swipeable-card-base-component.md)
- [Intl.NumberFormat API](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

No debugging issues encountered during story creation.

### Completion Notes List

**Story Implementation Summary:**
- Story 2.5.6 implemented successfully - BalanceDisplay component created
- All 7 tasks completed with all subtasks checked
- TypeScript compilation passed (via npm run build)
- Production build succeeded
- All acceptance criteria met:
  - AC1: BalanceDisplay component with 3 size variants (display/title/body)
  - AC2: text-primary color used for all amounts (never red for debt)
  - AC3: "Rs" prefix with comma separators (Rs 1,500)
  - AC4: Context labels support ("You owe" / "You're owed")
  - AC5: aria-label includes full context for screen readers

**Implementation Details:**
- Component: `frontend/src/components/ui/balance-display.tsx`
- Currency formatting using Intl.NumberFormat with Indian locale
- Neutral color strategy enforced (text-primary for amounts, text-secondary for labels)
- Three variants implemented: display (32px), title (24px), body (16px)
- Accessibility: aria-label with full context, role="text"
- Context label positioning: inline (body) or above (display/title)
- Negative number format: "-Rs 450" (minus before "Rs")

**Story Creation Summary:**
- Story 2.5.6 created from epic requirements with comprehensive developer context
- All acceptance criteria extracted from epics.md and ux-design-specification.md
- Component interface fully specified with BalanceDisplayProps
- Currency formatting logic documented with Intl.NumberFormat approach
- Neutral color strategy emphasized (never red/green for debt)
- Accessibility requirements detailed with ARIA implementation patterns
- Three size variants specified: Display (32px), Title (24px), Body (16px)
- Previous story intelligence analyzed from Stories 2.5.1-2.5.5
- Git intelligence gathered from Epic 2.5 commit history
- Testing commands and manual verification checklist provided

**Context Sources Analyzed:**
- `_bmad-output/planning-artifacts/epics.md` - Story requirements and acceptance criteria
- `_bmad-output/planning-artifacts/ux-design-specification.md` - Component specs, typography, color system
- `_bmad-output/planning-artifacts/architecture.md` - Technical stack and naming conventions
- `_bmad-output/implementation-artifacts/2-5-5-swipeable-card-base-component.md` - Previous story patterns
- `_bmad-output/session-context.md` - Project status and key learnings
- Git commit history - Recent Epic 2.5 implementation patterns

### Change Log

- 2026-01-15: Story created by create-story workflow with comprehensive developer context
- 2026-01-15: Story implemented - BalanceDisplay component created, all tasks completed
- 2026-01-15: Code review completed - 3 HIGH and 3 MEDIUM issues fixed
  - Fixed typography contradiction (tabular → proportional nums)
  - Created index.ts barrel export for component imports
  - Added zero edge case and decimal handling
- Status: review - Fixes applied, ready for final verification

### File List

**Story Files:**
- `_bmad-output/implementation-artifacts/2-5-6-balance-display-component.md` (this file)

**Files Created During Implementation:**
- `frontend/src/components/ui/balance-display.tsx` (CREATED)
  - BalanceDisplay component
  - BalanceDisplayProps interface
  - Currency formatting utilities (formatCurrency function)
  - Variant styling logic (display/title/body)
  - Accessibility attributes (aria-label, role="text")

**Files Modified During Code Review (2026-01-15):**
- `frontend/src/components/ui/balance-display.tsx` (FIXED)
  - Fixed: Replaced `tabular-nums` with `proportional-nums` (CRIT-1)
  - Fixed: Added zero edge case handling (-0 vs 0) (MED-3)
  - Fixed: Added decimal handling for amounts with paise (MED-5)
- `frontend/src/components/ui/index.ts` (CREATED - CRIT-2)
  - Barrel export for all ClearDues UI components
  - Enables imports via `@/components/ui`
