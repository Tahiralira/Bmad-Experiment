# Story 2.5.1: Design System Token Migration

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **frontend developer**,
I want to replace the current color/typography tokens with the UX specification palette,
so that all subsequent components use the correct visual language.

## Acceptance Criteria

1. **Given** the existing Tailwind/shadcn configuration
   **When** I update the design tokens
   **Then** the warm minimal palette is applied:
   - background: #FDFBF7 (light), #1A1A1A (dark)
   - surface: #FAF8F5 (light), #252525 (dark)
   - action: #3D9A94 (muted teal)
   - success: #D4A857 (warm amber)

2. **And** Inter font family is configured (variable font)

3. **And** spacing scale uses 4px base unit

4. **And** border-radius tokens are soft (8-12px)

5. **And** shadow system uses subtle depth

6. **And** existing components are updated to use new tokens

7. **And** both light and dark themes work correctly

## Tasks / Subtasks

- [x] Task 1: Update CSS variables with UX spec color palette (AC: #1, #7)
  - [x] Replace OKLCH colors in `src/index.css` with hex values from UX spec
  - [x] Add new semantic tokens: `surface`, `surface-elevated`, `action`, `action-hover`, `success`, `success-subtle`
  - [x] Configure both `:root` (light) and `.dark` (dark) theme variables
  - [x] Add accent colors: `info`, `warning`, `error` with correct soft tones

- [x] Task 2: Configure Inter font family (AC: #2)
  - [x] Install Inter variable font (Google Fonts or local)
  - [x] Add `@font-face` or Google Fonts import to `index.css`
  - [x] Update Tailwind font-family to use Inter as default sans-serif
  - [x] Configure font-feature-settings for optimal rendering

- [x] Task 3: Update spacing scale (AC: #3)
  - [x] Configure 4px base unit in CSS variables
  - [x] Add spacing tokens: `space-1` through `space-12`
  - [x] Verify Tailwind's default spacing aligns (or create custom)

- [x] Task 4: Update border-radius tokens (AC: #4)
  - [x] Replace current `--radius` with soft corners: 6px (sm), 10px (md), 16px (lg)
  - [x] Update `--radius-full` for pills/avatars (9999px)

- [x] Task 5: Configure shadow system (AC: #5)
  - [x] Add `--shadow-sm`, `--shadow-md`, `--shadow-lg` CSS variables
  - [x] Use subtle depth values from UX spec

- [x] Task 6: Add animation tokens (AC: foundation)
  - [x] Add duration tokens: `--duration-fast` (150ms), `--duration-normal` (200ms), `--duration-slow` (300ms)
  - [x] Add easing tokens: `--easing-default`, `--easing-spring`
  - [x] Configure `prefers-reduced-motion` media query styles

- [x] Task 7: Update existing shadcn components to use new tokens (AC: #6)
  - [x] Button component: use `action` color for primary
  - [x] Card component: use `surface` and `border` tokens (fixed: rounded-md + shadow-md per UX spec)
  - [x] Input component: verified already uses correct border/focus ring (no changes needed)
  - [x] Verify all components render correctly with new palette

- [x] Task 8: Verify theme switching (AC: #7)
  - [x] Test light mode renders correctly
  - [x] Test dark mode renders correctly
  - [x] Verify smooth 200ms transition on theme change
  - [x] Test system preference detection works

- [x] Task 9: Run frontend tests and build (AC: ALL)
  - [x] Run `npm run typecheck` - no errors (via build script)
  - [x] Run `npm run build` - successful build
  - [x] Manual visual verification of Dashboard and Group screens

## Dev Notes

### CRITICAL: This is the foundation story for Epic 2.5 (UX Foundation)

Story 2.5.1 establishes the ClearDues visual identity. All subsequent UX stories (Agent Orb, Orbital Navigation, Smart Input) depend on these design tokens being correctly configured. **Get the tokens right - they affect every component.**

**Key Design Philosophy:**
- **Warm Minimal:** Soft neutrals, not clinical fintech (cream backgrounds, not pure white)
- **Payment = Silence:** Success is amber (not green), debt amounts never red
- **Human, Not Robotic:** Subtle animations, comfortable density, rounded corners

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
frontend/src/
├── index.css                    # UPDATE: CSS variables, font import
├── components/
│   └── ui/
│       ├── button.tsx           # VERIFY: Primary uses action color
│       ├── card.tsx             # VERIFY: Uses surface tokens
│       └── input.tsx            # VERIFY: Uses new focus ring
└── tailwind.config.ts           # OPTIONAL: Custom theme if needed
```

**Naming Conventions (MANDATORY):**
- CSS variables: `--token-name` (kebab-case)
- Tailwind classes: `bg-background`, `text-primary` (semantic names)
- Colors: Never hardcode hex values in components

### Current State Analysis

**Current Setup (from exploration):**
- Tailwind CSS v4 with `@tailwindcss/vite` plugin
- shadcn/ui configured with "New York" style
- OKLCH color space currently used
- Theme provider supports `light`, `dark`, `system` modes
- CSS variables defined in `src/index.css`

**What Needs to Change:**
1. Replace OKLCH values with hex values from UX spec
2. Add missing semantic tokens (surface, action, success)
3. Configure Inter font (currently using default)
4. Update shadow system to subtle depth values
5. Add animation/timing tokens

### Technical Requirements

**CSS Variables Migration (UPDATE frontend/src/index.css):**

Replace the current `:root` block with:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');

:root {
  /* Base Unit */
  --spacing-unit: 4px;

  /* Border Radius (Soft Corners) */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Shadows (Subtle Depth) */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);

  /* Animation Tokens */
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --easing-default: cubic-bezier(0.4, 0, 0.2, 1);
  --easing-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* ========== LIGHT THEME ========== */

  /* Background Colors */
  --background: #FDFBF7;           /* Warm white - page background */
  --foreground: #1F1E1C;           /* Warm black - primary text */

  /* Surface Colors */
  --surface: #FAF8F5;              /* Soft cream - cards, containers */
  --surface-elevated: #FFFFFF;     /* Pure white - modals, sheets */

  /* Border Colors */
  --border: #E8E4DD;               /* Sand - dividers, outlines */
  --input: #E8E4DD;                /* Sand - input borders */
  --ring: #3D9A94;                 /* Muted teal - focus ring */

  /* Text Colors */
  --text-primary: #1F1E1C;         /* Warm black */
  --text-secondary: #6B6660;       /* Warm gray */
  --text-muted: #9C9790;           /* Light gray */

  /* Action Colors (Primary) */
  --primary: #3D9A94;              /* Muted teal - CTAs */
  --primary-foreground: #FFFFFF;   /* White text on primary */
  --action: #3D9A94;               /* Alias for primary */
  --action-hover: #2D7A75;         /* Deeper teal on hover */

  /* Secondary Colors */
  --secondary: #FAF8F5;            /* Surface color */
  --secondary-foreground: #1F1E1C; /* Text on secondary */

  /* Muted Colors */
  --muted: #FAF8F5;                /* Surface for muted backgrounds */
  --muted-foreground: #6B6660;     /* Secondary text */

  /* Accent Colors */
  --accent: #FAF8F5;               /* Light accent background */
  --accent-foreground: #1F1E1C;    /* Text on accent */

  /* Success Colors (Amber - NOT Green) */
  --success: #D4A857;              /* Warm amber - completion */
  --success-foreground: #1F1E1C;   /* Dark text on success */
  --success-subtle: #FDF8ED;       /* Amber tint background */

  /* Semantic Colors */
  --info: #5B8FB9;                 /* Soft blue */
  --info-foreground: #FFFFFF;
  --warning: #CC8B4D;              /* Muted orange */
  --warning-foreground: #1F1E1C;
  --error: #C97C7C;                /* Soft coral */
  --error-foreground: #FFFFFF;
  --destructive: #C97C7C;          /* Alias for error */
  --destructive-foreground: #FFFFFF;

  /* Card Colors */
  --card: #FAF8F5;                 /* Surface */
  --card-foreground: #1F1E1C;      /* Primary text */

  /* Popover Colors */
  --popover: #FFFFFF;              /* Elevated surface */
  --popover-foreground: #1F1E1C;   /* Primary text */

  /* Chart Colors (Data Visualization) */
  --chart-1: #3D9A94;              /* Teal */
  --chart-2: #D4A857;              /* Amber */
  --chart-3: #5B8FB9;              /* Blue */
  --chart-4: #CC8B4D;              /* Orange */
  --chart-5: #8B7355;              /* Brown */

  /* Sidebar Colors */
  --sidebar-background: #FAF8F5;
  --sidebar-foreground: #1F1E1C;
  --sidebar-primary: #3D9A94;
  --sidebar-primary-foreground: #FFFFFF;
  --sidebar-accent: #FDFBF7;
  --sidebar-accent-foreground: #1F1E1C;
  --sidebar-border: #E8E4DD;
  --sidebar-ring: #3D9A94;
}

.dark {
  /* ========== DARK THEME ========== */

  /* Background Colors */
  --background: #1A1A1A;           /* Deep charcoal */
  --foreground: #F5F5F5;           /* Off-white */

  /* Surface Colors */
  --surface: #252525;              /* Dark gray */
  --surface-elevated: #2E2E2E;     /* Elevated gray */

  /* Border Colors */
  --border: #3A3A3A;               /* Muted border */
  --input: #3A3A3A;
  --ring: #3D9A94;                 /* Teal focus ring */

  /* Text Colors */
  --text-primary: #F5F5F5;         /* Off-white */
  --text-secondary: #A0A0A0;       /* Muted gray */
  --text-muted: #707070;           /* Dim gray */

  /* Action Colors */
  --primary: #3D9A94;
  --primary-foreground: #FFFFFF;
  --action: #3D9A94;
  --action-hover: #4DB0A9;         /* Lighter on dark bg */

  /* Secondary Colors */
  --secondary: #252525;
  --secondary-foreground: #F5F5F5;

  /* Muted Colors */
  --muted: #252525;
  --muted-foreground: #A0A0A0;

  /* Accent Colors */
  --accent: #252525;
  --accent-foreground: #F5F5F5;

  /* Success Colors */
  --success: #D4A857;
  --success-foreground: #1A1A1A;
  --success-subtle: #2A2518;

  /* Semantic Colors */
  --info: #5B8FB9;
  --info-foreground: #1A1A1A;
  --warning: #CC8B4D;
  --warning-foreground: #1A1A1A;
  --error: #C97C7C;
  --error-foreground: #1A1A1A;
  --destructive: #C97C7C;
  --destructive-foreground: #1A1A1A;

  /* Card Colors */
  --card: #252525;
  --card-foreground: #F5F5F5;

  /* Popover Colors */
  --popover: #2E2E2E;
  --popover-foreground: #F5F5F5;

  /* Chart Colors */
  --chart-1: #4DB0A9;
  --chart-2: #E5BC6A;
  --chart-3: #6BA0CA;
  --chart-4: #DD9C5E;
  --chart-5: #9C8466;

  /* Sidebar Colors */
  --sidebar-background: #1A1A1A;
  --sidebar-foreground: #F5F5F5;
  --sidebar-primary: #3D9A94;
  --sidebar-primary-foreground: #FFFFFF;
  --sidebar-accent: #252525;
  --sidebar-accent-foreground: #F5F5F5;
  --sidebar-border: #3A3A3A;
  --sidebar-ring: #3D9A94;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Theme Transition */
* {
  transition-property: background-color, border-color, color;
  transition-duration: var(--duration-normal);
  transition-timing-function: var(--easing-default);
}

/* Inter Font Configuration */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Color Migration Reference

| Old Token (OKLCH) | New Token (Hex) | Light Value | Dark Value |
|-------------------|-----------------|-------------|------------|
| `--background` | `--background` | #FDFBF7 | #1A1A1A |
| `--foreground` | `--foreground` | #1F1E1C | #F5F5F5 |
| `--primary` | `--primary` (teal) | #3D9A94 | #3D9A94 |
| N/A | `--surface` (NEW) | #FAF8F5 | #252525 |
| N/A | `--action` (NEW) | #3D9A94 | #3D9A94 |
| N/A | `--success` (amber) | #D4A857 | #D4A857 |
| `--destructive` | `--error` (coral) | #C97C7C | #C97C7C |

### Typography Scale

```css
/* Typography Variables (add to :root) */
:root {
  --font-display: 32px;      /* Dashboard balance */
  --font-title: 24px;        /* Page titles */
  --font-heading: 18px;      /* Section headers */
  --font-body: 16px;         /* Default text */
  --font-body-small: 14px;   /* Secondary content */
  --font-caption: 12px;      /* Labels, timestamps */

  --font-weight-regular: 400;
  --font-weight-medium: 500;

  --line-height-tight: 1.2;
  --line-height-snug: 1.3;
  --line-height-normal: 1.5;
}
```

### Spacing Scale (4px Base)

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
}
```

### Button Component Update Example

**VERIFY button.tsx uses action color:**

The CVA variants should use:
```tsx
const buttonVariants = cva(
  "...",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-action-hover",
        // Note: --action and --primary are the same (teal)
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        // ...
      },
    },
  }
)
```

### Project Structure Notes

**Frontend Changes Only:**
```
frontend/src/
├── index.css                    # UPDATE: Replace OKLCH with UX spec tokens
├── components/
│   └── ui/
│       ├── button.tsx           # VERIFY: Uses --primary (teal)
│       ├── card.tsx             # VERIFY: Uses --card (surface)
│       └── input.tsx            # VERIFY: Uses --ring (teal focus)
└── main.tsx                     # NO CHANGE (ThemeProvider already set)
```

**No Backend Changes Required** - This is a frontend-only story.

### Previous Story Intelligence

**From Story 3.1 (Create Expense Model):**
- Frontend uses shadcn/ui components (Button, Input, Label)
- Components already use CSS variables via Tailwind classes
- ThemeProvider wraps entire app in `main.tsx`
- Build and typecheck commands work correctly

**From Story 2.4 (Dashboard):**
- Dashboard components use `Card` from shadcn/ui
- Balance displays use Tailwind classes for styling
- Dark mode toggle exists in Appearance component

**Patterns to Maintain:**
- Continue using shadcn/ui components
- Use Tailwind utility classes (not inline styles)
- CSS variables for all colors (enables theme switching)
- Component variants via CVA (class-variance-authority)

### Git Intelligence

**Recent Commits:**
- `461f3cf` - feat: Complete Story 3.1 - Create expense model and basic entry
- `bff8605` - feat: Complete Story 2.4 - Dashboard with Net Balances + Epic 2 Complete

**Commit Message Format:**
```
feat: Complete Story 2.5.1 - Design system token migration
```

### Testing Commands

```bash
# Frontend type check
cd frontend && npm run typecheck

# Frontend build
cd frontend && npm run build

# Start dev server for visual testing
cd frontend && npm run dev

# Manual verification checklist:
# 1. Open http://localhost:5173
# 2. Check light mode: Warm white background (#FDFBF7)
# 3. Toggle to dark mode: Deep charcoal background (#1A1A1A)
# 4. Verify buttons are muted teal (#3D9A94)
# 5. Check card backgrounds are soft cream (light) / dark gray (dark)
# 6. Test theme system preference follows device setting
```

### CRITICAL Rules for Implementation

1. **NO RED FOR DEBT:** Never use error/destructive colors for monetary amounts. Debt is shown in `text-primary` (neutral).

2. **SEMANTIC NAMING:** Use `--action` not `--teal`, `--success` not `--amber`. Colors by purpose, not hue.

3. **BOTH THEMES:** Every color token MUST have light AND dark values. Test both.

4. **NO HARDCODED HEX:** Components use Tailwind classes (`bg-primary`) not hex values (`bg-[#3D9A94]`).

5. **INTER FONT:** The font MUST be Inter. Don't skip the font import.

6. **SOFT CORNERS:** Use `--radius-md` (10px) for cards, not sharp corners.

7. **SUBTLE SHADOWS:** Shadows are barely visible. Don't increase opacity.

### Epic 2.5 Context

This is Story 1 of 7 in Epic 2.5 (UX Foundation & Design System):
- **2.5.1** (this) - Design system token migration
- 2.5.2 - Agent Orb component
- 2.5.3 - Orbital navigation system
- 2.5.4 - Smart Input modal foundation
- 2.5.5 - Swipeable card base component
- 2.5.6 - Balance display component
- 2.5.7 - Update existing screens to new design system

**Dependencies:** All subsequent Epic 2.5 stories depend on these design tokens.

### Accessibility Requirements

- **Text Contrast:** 4.5:1 minimum for body text, 3:1 for large text
- **Focus Ring:** 3px teal ring on all focusable elements (--ring: #3D9A94)
- **Reduced Motion:** Disable animations when `prefers-reduced-motion: reduce`
- **Color Independence:** Never convey meaning by color alone

### References

- [Source: epics.md - Story 2.5.1](../_bmad-output/planning-artifacts/epics.md#story-251-design-system-token-migration)
- [Source: ux-design-specification.md - Design Tokens](../_bmad-output/planning-artifacts/ux-design-specification.md)
- [Source: architecture.md - Frontend Stack](../_bmad-output/planning-artifacts/architecture.md)
- [Existing Code: frontend/src/index.css](../../frontend/src/index.css)
- [Existing Code: components/ui/button.tsx](../../frontend/src/components/ui/button.tsx)
- [Previous Story: 3-1-create-expense-model-and-basic-entry.md](./3-1-create-expense-model-and-basic-entry.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Fixed CSS @import order warning by moving Google Fonts import before Tailwind imports

### Completion Notes List

- Replaced all OKLCH color values with hex values from UX specification
- Added comprehensive light and dark theme support with warm minimal palette
- Configured Inter font via Google Fonts with font-feature-settings for optimal rendering
- Added 4px base spacing scale (space-1 through space-12)
- Configured soft corner radius tokens (6px, 10px, 16px)
- Added subtle shadow system with low opacity values
- Implemented animation tokens with reduced motion support
- Updated Button component to use explicit action-hover color
- Updated Card component to use rounded-md (10px) and shadow-md per UX spec
- Verified ThemeProvider supports light/dark/system modes
- Build passes successfully with no errors

### Code Review Fixes (2026-01-14)

- Fixed Card component: changed `rounded-lg` to `rounded-md` (UX spec requires 10px for cards)
- Fixed Card component: changed `shadow-sm` to `shadow-md` (UX spec requires shadow-md for cards)
- Clarified Input component task: already had correct styling, no changes needed

### Change Log

- 2026-01-14: Story created by create-story workflow
- 2026-01-14: Implemented design system token migration - all acceptance criteria satisfied
- 2026-01-14: Code review fixes - Card component border-radius and shadow aligned with UX spec

### File List

- frontend/src/index.css (modified) - Complete redesign with UX spec tokens
- frontend/src/components/ui/button.tsx (modified) - Updated hover state to use action-hover
- frontend/src/components/ui/card.tsx (modified) - Updated to use rounded-lg soft corners
