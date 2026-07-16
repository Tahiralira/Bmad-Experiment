# WS3 Implementation Kit — "Quiet Ink" (zero-decision edition)

**Purpose:** everything WS3 needs, pre-decided. The implementing session makes NO design
choices — it pastes the files below, applies the find/replace tables, runs the gates,
and takes screenshots. Where this kit and anything else disagree, **this kit wins**
(it was derived from `ux-design-spec-v2.md` + a live audit of the code on 2026-07-07).

**Read first:** `ux-design-spec-v2.md` §1–§3 for the *why*. This file is the *how*.

**Naming note (do not "fix" this):** the spec calls the interactive ink-teal
`--accent`. In code it stays on the shadcn names `--primary` / `--action` /
`--ring`, because 40+ components already consume those. Code `--accent` remains the
shadcn *quiet hover surface* token. Never point `--accent` at teal (that is exactly
the UX-C1 collision class).

**Execution order matters.** Do the tasks in the numbered order; each leaves the
build green. Commit after each task.

---

## Task 0 — Branch & baseline

```bash
git checkout -b ws3/quiet-ink
cd frontend && npm run typecheck && npm run test && npm run build
```
All three must be green BEFORE starting (they were on 2026-07-07). Record the current
`dist/assets/*.js` gzip sizes from the build output — you'll report the delta at the end.

---

## Task 1 — Dependencies & build config

### 1a. package.json

```bash
cd frontend
npm uninstall framer-motion react-icons
npm uninstall @tanstack/react-query-devtools @tanstack/react-router-devtools
npm install -D @tanstack/react-query-devtools @tanstack/react-router-devtools
```

(react-icons is used only by `Common/Footer.tsx`, which Task 3 deletes. framer-motion
consumers are all removed in Tasks 5–6 — the uninstall now is safe because nothing is
imported until you finish; if you prefer, run the uninstall after Task 6 instead. Either
order is fine; the END state is what's checked.)

### 1b. `vite.config.ts` — replace entire file

```ts
import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vitest/config"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom"],
          "vendor-tanstack": [
            "@tanstack/react-router",
            "@tanstack/react-query",
            "@tanstack/react-table",
          ],
          "vendor-forms": ["react-hook-form", "zod", "@hookform/resolvers"],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
})
```

### 1c. `src/routes/__root.tsx` — replace entire file (devtools out of prod bundle)

```tsx
import { createRootRoute, HeadContent, Outlet } from "@tanstack/react-router"
import { lazy, Suspense } from "react"
import ErrorComponent from "@/components/Common/ErrorComponent"
import NotFound from "@/components/Common/NotFound"

// Devtools are lazy + DEV-gated so they are tree-shaken out of the production bundle.
const RouterDevtools = import.meta.env.DEV
  ? lazy(() =>
      import("@tanstack/react-router-devtools").then((m) => ({
        default: m.TanStackRouterDevtools,
      })),
    )
  : () => null
const QueryDevtools = import.meta.env.DEV
  ? lazy(() =>
      import("@tanstack/react-query-devtools").then((m) => ({
        default: m.ReactQueryDevtools,
      })),
    )
  : () => null

export const Route = createRootRoute({
  component: () => (
    <>
      <HeadContent />
      <Outlet />
      {import.meta.env.DEV && (
        <Suspense fallback={null}>
          <RouterDevtools position="bottom-right" />
          <QueryDevtools initialIsOpen={false} />
        </Suspense>
      )}
    </>
  ),
  notFoundComponent: () => <NotFound />,
  errorComponent: () => <ErrorComponent />,
})
```

Gate: `npm run typecheck && npm run build` — green before moving on.

---

## Task 2 — Tokens: replace `src/index.css` entirely

This single file does ~60% of the restyle: every component that reads tokens
(62 `text-text-*` usages, all shadcn primitives) re-skins itself. Paste exactly:

```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  /* Border Radius — radius lives on CONTROLS only (Quiet Ink: surfaces are square,
     separated by hairlines; buttons/inputs 8px, sheets 12px, FAB/avatars full) */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 12px;
  --radius-full: 9999px;

  /* Colors - mapped from CSS variables */
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);

  /* Surface Colors */
  --color-surface: var(--surface);
  --color-surface-elevated: var(--surface-elevated);

  /* Action Colors */
  --color-action: var(--action);
  --color-action-hover: var(--action-hover);

  /* Success = SETTLED (amber, never green) */
  --color-success: var(--success);
  --color-success-foreground: var(--success-foreground);
  --color-success-subtle: var(--success-subtle);

  /* Semantic Colors */
  --color-info: var(--info);
  --color-info-foreground: var(--info-foreground);
  --color-warning: var(--warning);
  --color-warning-foreground: var(--warning-foreground);
  --color-error: var(--error);
  --color-error-foreground: var(--error-foreground);

  /* Text Hierarchy Colors — tokens are namespaced "text-*" so the generated
     utilities are text-text-primary / text-text-secondary / text-text-muted.
     Do NOT map these to --color-primary/secondary/muted: those are shadcn
     SURFACE/ACTION tokens, not text colors. */
  --color-text-primary: var(--text-primary);
  --color-text-secondary: var(--text-secondary);
  --color-text-muted: var(--text-muted);

  /* Typography Scale — Quiet Ink (v2): 28/20/17/15/13/11 */
  --text-display: 28px;
  --text-display--line-height: 1.2;
  --text-title: 20px;
  --text-title--line-height: 1.3;
  --text-heading: 17px;
  --text-heading--line-height: 1.4;
  --text-body: 15px;
  --text-body--line-height: 1.5;
  --text-body-small: 13px;
  --text-body-small--line-height: 1.5;
  --text-caption: 11px;
  --text-caption--line-height: 1.4;

  /* Shadows — NONE at rest (Quiet Ink). Every resting shadow utility resolves to
     nothing; only the overlay shadow (shadow-lg/xl, used by dialogs/sheets/FAB)
     renders. This mechanically strips shadows app-wide. */
  --shadow-2xs: 0 0 #0000;
  --shadow-xs: 0 0 #0000;
  --shadow-sm: 0 0 #0000;
  --shadow-md: 0 0 #0000;
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.14);
  --shadow-xl: 0 12px 32px rgba(0, 0, 0, 0.14);

  /* Chart Colors */
  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);

  /* Sidebar Colors (template screens only — deleted in WS8; kept so nothing breaks) */
  --color-sidebar: var(--sidebar-background);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);

  /* Font Family — SYSTEM STACK, zero download (Quiet Ink) */
  --font-sans:
    system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial,
    sans-serif;
}

:root {
  /* ========== BASE UNITS ========== */
  --spacing-unit: 4px;

  /* Spacing Scale (4px base) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* Border Radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;
  --radius: 8px; /* Default radius for shadcn controls */

  /* Overlay shadow (the ONLY shadow in the system) */
  --shadow-overlay: 0 12px 32px rgba(0, 0, 0, 0.14);

  /* Animation Tokens — opacity/transform only, nothing infinite */
  --duration-fast: 120ms;
  --duration-normal: 150ms;
  --duration-slow: 300ms;
  --easing-default: cubic-bezier(0.4, 0, 0.2, 1);

  /* ========== LIGHT THEME — "paper" ========== */

  --background: #fcfcfb;
  --foreground: #1c1b1a;

  --surface: #fcfcfb; /* flat: same as background — separation via hairlines */
  --surface-elevated: #ffffff; /* overlays only: modals, sheets, popovers */

  --border: #e7e5e1;
  --input: #e7e5e1;
  --ring: #1f6e68;

  /* Text hierarchy */
  --text-primary: #1c1b1a; /* ink — 16.8:1 */
  --text-secondary: #6e6b66; /* 5.3:1 */
  --text-muted: #93908a; /* 3.2:1 — ≥14px non-essential text ONLY */

  /* Interactive ink-teal (spec §3 "--accent") */
  --primary: #1f6e68; /* 6.0:1 on paper */
  --primary-foreground: #ffffff;
  --action: #1f6e68;
  --action-hover: #16544f;

  /* Quiet fills */
  --secondary: #f4f3f0;
  --secondary-foreground: #1c1b1a;
  --muted: #f4f3f0;
  --muted-foreground: #6e6b66;
  --accent: #f1f0ed; /* hover surface — NEVER teal */
  --accent-foreground: #1c1b1a;

  /* Settled (amber — never green) */
  --success: #8f681c; /* text-safe 5.0:1 */
  --success-foreground: #ffffff;
  --success-subtle: #f7efd9;

  /* Semantic */
  --info: #5c6470;
  --info-foreground: #ffffff;
  --warning: #8f681c;
  --warning-foreground: #ffffff;
  --error: #a05a52; /* muted clay — never bright red. 5.0:1 */
  --error-foreground: #ffffff;
  --destructive: #a05a52;
  --destructive-foreground: #ffffff;

  --card: #fcfcfb;
  --card-foreground: #1c1b1a;
  --popover: #ffffff;
  --popover-foreground: #1c1b1a;

  --chart-1: #1f6e68;
  --chart-2: #8f681c;
  --chart-3: #6e6b66;
  --chart-4: #a05a52;
  --chart-5: #93908a;

  --sidebar-background: #fcfcfb;
  --sidebar-foreground: #1c1b1a;
  --sidebar-primary: #1f6e68;
  --sidebar-primary-foreground: #ffffff;
  --sidebar-accent: #f1f0ed;
  --sidebar-accent-foreground: #1c1b1a;
  --sidebar-border: #e7e5e1;
  --sidebar-ring: #1f6e68;
}

.dark {
  /* ========== DARK THEME ========== */

  --background: #141414;
  --foreground: #eceae6;

  --surface: #141414;
  --surface-elevated: #1e1e1d;

  --border: #2b2a28;
  --input: #2b2a28;
  --ring: #57b3aa;

  --text-primary: #eceae6; /* 15.6:1 */
  --text-secondary: #a3a09b; /* 7.1:1 */
  --text-muted: #767370; /* 3.9:1 — ≥14px non-essential only */

  --primary: #57b3aa; /* 7.4:1 */
  --primary-foreground: #101010;
  --action: #57b3aa;
  --action-hover: #6fc4bb;

  --secondary: #201f1e;
  --secondary-foreground: #eceae6;
  --muted: #201f1e;
  --muted-foreground: #a3a09b;
  --accent: #222120;
  --accent-foreground: #eceae6;

  --success: #d3a44e; /* 8.1:1 */
  --success-foreground: #141414;
  --success-subtle: #26200f;

  --info: #a3a09b;
  --info-foreground: #141414;
  --warning: #d3a44e;
  --warning-foreground: #141414;
  --error: #ce8a80; /* 6.2:1 */
  --error-foreground: #141414;
  --destructive: #ce8a80;
  --destructive-foreground: #141414;

  --card: #141414;
  --card-foreground: #eceae6;
  --popover: #1e1e1d;
  --popover-foreground: #eceae6;

  --chart-1: #57b3aa;
  --chart-2: #d3a44e;
  --chart-3: #a3a09b;
  --chart-4: #ce8a80;
  --chart-5: #767370;

  --sidebar-background: #141414;
  --sidebar-foreground: #eceae6;
  --sidebar-primary: #57b3aa;
  --sidebar-primary-foreground: #101010;
  --sidebar-accent: #222120;
  --sidebar-accent-foreground: #eceae6;
  --sidebar-border: #2b2a28;
  --sidebar-ring: #57b3aa;
}

/* The settle moment — the app's single choreographed animation (spec §3.5).
   Apply .settle-glow to a row when its settlement is confirmed. */
@keyframes settle-glow {
  0% {
    background-color: transparent;
    box-shadow: inset 0 0 0 0 var(--success);
  }
  30% {
    background-color: var(--success-subtle);
    box-shadow: inset 0 0 0 1px var(--success);
  }
  100% {
    background-color: var(--success-subtle);
    box-shadow: inset 0 0 0 0 transparent;
  }
}
.settle-glow {
  animation: settle-glow 400ms var(--easing-default) both;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms;
    animation-iteration-count: 1;
    transition-duration: 0.01ms;
  }
}

@layer base {
  * {
    @apply border-border outline-ring/50;
  }

  /* Theme Transition - smooth color changes */
  *:not([data-no-transition]) {
    transition-property: background-color, border-color, color, fill, stroke;
    transition-duration: var(--duration-normal);
    transition-timing-function: var(--easing-default);
  }

  body {
    @apply bg-background text-foreground;
    font-family:
      system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial,
      sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  button,
  [role="button"] {
    cursor: pointer;
  }
}
```

Notes on what changed vs old file (for the reviewer, not for you to re-decide):
Google Fonts `@import` deleted; Inter `font-feature-settings` deleted (Inter-specific);
type scale 32/24/18/16/14/12 → 28/20/17/15/13/11; all resting shadows zeroed at the
token level; radius 10 → 8 default; palette per spec §3; `--easing-spring` deleted
(nothing springs anymore); settle-glow keyframes added.

Gate: `npm run build` green. The app will already look ~80% Quiet Ink.

---

## Task 3 — Brand floor

### 3a. `index.html` — replace entire file

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ClearDues</title>
    <meta
      name="description"
      content="ClearDues keeps score of shared expenses so you never have to ask."
    />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="theme-color" content="#fcfcfb" media="(prefers-color-scheme: light)" />
    <meta name="theme-color" content="#141414" media="(prefers-color-scheme: dark)" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="./src/main.tsx"></script>
  </body>
</html>
```

### 3b. `public/favicon.svg` — new file (the ClearDues mark: a balanced ledger, "=")

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1F6E68"/><rect x="16" y="25" width="32" height="6" rx="3" fill="#FCFCFB"/><rect x="16" y="37" width="32" height="6" rx="3" fill="#FCFCFB"/></svg>
```

### 3c. Delete template assets

```bash
git rm frontend/public/assets/images/fastapi-icon.svg \
       frontend/public/assets/images/fastapi-icon-light.svg \
       frontend/public/assets/images/fastapi-logo.svg \
       frontend/public/assets/images/fastapi-logo-light.svg \
       frontend/public/assets/images/favicon.png
```

### 3d. `src/components/Common/Logo.tsx` — replace entire file (wordmark, no images)

```tsx
import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

/** The ClearDues mark: a balanced ledger ("="). Renders in the accent color. */
function LogoGlyph({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      aria-hidden="true"
      className={cn("size-6 shrink-0", className)}
    >
      <rect width="64" height="64" rx="14" className="fill-primary" />
      <rect x="16" y="25" width="32" height="6" rx="3" className="fill-background" />
      <rect x="16" y="37" width="32" height="6" rx="3" className="fill-background" />
    </svg>
  )
}

export function Logo({ variant = "full", className, asLink = true }: LogoProps) {
  const content =
    variant === "icon" ? (
      <LogoGlyph className={className} />
    ) : (
      <span className={cn("inline-flex items-center gap-2", className)}>
        <LogoGlyph />
        <span className="text-heading font-semibold tracking-tight text-text-primary">
          ClearDues
        </span>
      </span>
    )

  if (!asLink) {
    return content
  }

  return (
    <Link to="/" aria-label="ClearDues home">
      {content}
    </Link>
  )
}
```

### 3e. Delete the template footer

```bash
git rm frontend/src/components/Common/Footer.tsx
```

Then remove its two usages (both files are fully replaced below anyway):
`src/components/Common/AuthLayout.tsx` (Task 3f) and `src/routes/_layout.tsx` (Task 5b).

### 3f. `src/components/Common/AuthLayout.tsx` — replace entire file

```tsx
import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-svh flex-col p-6 md:p-10">
      <div className="flex items-center justify-between">
        <Logo asLink={false} />
        <Appearance />
      </div>
      <div className="flex flex-1 items-center justify-center py-12">
        <div className="w-full max-w-xs">{children}</div>
      </div>
    </div>
  )
}
```

### 3g. Copy & weight fixes on ClearDues-facing auth screens

Apply these mechanical replacements in `src/routes/login.tsx`,
`src/routes/register.tsx`, `src/routes/invite.$token.tsx`,
`src/routes/auth.callback.tsx`, `src/routes/login.verify.$token.tsx`,
`src/routes/verify.$token.tsx`:

| Find | Replace with |
|---|---|
| `text-2xl font-bold` | `text-title font-semibold` |
| `font-bold` (remaining) | `font-semibold` |
| `bg-green-100` | `bg-success-subtle` |
| `text-green-600` | `text-success` |
| `text-red-` (any shade) | `text-destructive` |
| `bg-red-` (any shade) | `bg-destructive` |

**Do NOT touch** (template files, deleted in WS8 — restyling them is wasted work):
`signup.tsx`, `recover-password.tsx`, `reset-password.tsx`, `_layout/items.tsx`,
`_layout/admin.tsx`, `components/Items/**`, `components/Admin/**`,
`components/UserSettings/ChangePassword.tsx`, `components/Pending/PendingItems.tsx`,
`components/Pending/PendingUsers.tsx`.

Also apply the same table to these ClearDues files (grep confirmed occurrences):
`_layout/settings.tsx`, `_layout/pending.tsx`, `_layout/activity.tsx`,
`_layout/groups.tsx`, `features/groups/components/MembersList.tsx`,
`features/groups/components/GenerateInviteButton.tsx`,
`features/groups/components/GroupDetail.tsx`, `Common/ErrorComponent.tsx`,
`Common/NotFound.tsx`, `features/expenses/components/ActivityFeed.tsx`,
`features/expenses/utils/activityFormatters.ts`,
`features/expenses/components/ConfirmedExpenseCard.tsx`,
`features/expenses/components/PendingConfirmationsList.tsx`,
`features/expenses/components/PercentageSplitInputs.tsx`.

Gate: `npm run typecheck && npm run build`.

---

## Task 4 — Primitives

### 4a. `src/components/ui/button.tsx` — replace the `buttonVariants` definition only

44px touch targets: default buttons grow to h-11. Everything else in the file stays.

```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-action-hover",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40",
        outline:
          "border border-border bg-transparent hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-accent",
        ghost:
          "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-11 px-5 py-2 has-[>svg]:px-4",
        sm: "h-9 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5",
        lg: "h-12 rounded-md px-6 has-[>svg]:px-5",
        icon: "size-11",
        "icon-sm": "size-9",
        "icon-lg": "size-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```

(Changes: `transition-all`→`transition-colors`; destructive uses tokens not `text-white`;
outline loses `shadow-xs` + dark input tints; sizes bumped for 44px targets.)

### 4b. `src/components/ui/input.tsx` — replace the input `className` string set

In the `cn(...)` call, replace the first string with:

```
"file:text-foreground placeholder:text-text-muted selection:bg-primary selection:text-primary-foreground border-input h-11 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 text-base transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm"
```

(Changes: `h-9`→`h-11` (44px), `shadow-xs` removed, `dark:bg-input/30` removed —
inputs are transparent on paper with a hairline, placeholder uses text-muted token.)
Leave the other two strings (focus/aria-invalid) unchanged.

### 4c. `src/components/ui/card.tsx` — replace the `Card` function's className only

```tsx
function Card({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card"
      className={cn(
        "bg-background text-foreground flex flex-col gap-4 border border-border py-4",
        className
      )}
      {...props}
    />
  )
}
```

(Flat: no rounding, no shadow, background = paper. `CardHeader/Content/Footer` px-6
stay as-is.) Where ClearDues screens need *lists*, they use the ledger-row pattern
(Task 5c), not Card.

### 4d. `src/components/ui/bottom-nav.tsx` — replace the two `cn(...)` class lists

Nav element classes:

```
"fixed inset-x-0 bottom-0 z-40",
"border-t border-border bg-background",
"pb-[env(safe-area-inset-bottom)]",
className,
```

Link classes:

```
"flex min-h-14 flex-col items-center justify-center gap-1",
"text-text-muted transition-colors",
"hover:text-text-primary",
"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
"data-[status=active]:text-primary",
```

And the label span becomes:

```tsx
<span className="text-caption font-medium uppercase tracking-[0.06em] leading-none">
  {item.label}
</span>
```

(Solid paper background — no translucency/blur; caption-style labels; active = ink-teal.)

### 4e. NEW FILE `src/components/ui/fab.tsx` — the orb's replacement

```tsx
import * as React from "react"
import { Plus } from "lucide-react"

import { cn } from "@/lib/utils"

export interface FabProps extends React.ComponentProps<"button"> {
  /** Custom aria-label (default: "Add an expense") */
  ariaLabel?: string
}

/**
 * Fab — the app's single floating action button. Tap = Smart Input.
 *
 * Replaces AgentOrb (WS2 decision: the "agent" lives in the mediator voice and
 * AI commentary, not in a glowing object). No idle animation by design.
 */
const Fab = React.forwardRef<HTMLButtonElement, FabProps>(
  ({ className, ariaLabel = "Add an expense", ...props }, ref) => (
    <button
      ref={ref}
      type="button"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex size-14 items-center justify-center rounded-full",
        "bg-primary text-primary-foreground shadow-lg",
        "transition-[transform,background-color] duration-150 hover:bg-action-hover active:scale-95",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        className,
      )}
      {...props}
    >
      <Plus className="size-6" aria-hidden="true" />
    </button>
  ),
)
Fab.displayName = "Fab"

export { Fab }
```

### 4f. `src/components/ui/index.ts` — replace entire file

```ts
/**
 * ClearDues UI Components
 *
 * Custom design system components for ClearDues ("Quiet Ink", design v2).
 *
 * @module components/ui
 */

// Balance Display
export { BalanceDisplay } from "./balance-display"
export type { BalanceDisplayProps, BalanceDisplayVariant } from "./balance-display"

// Bottom Navigation
export { BottomNav } from "./bottom-nav"
export type { BottomNavProps } from "./bottom-nav"

// Floating Action Button (replaces AgentOrb, design v2)
export { Fab } from "./fab"
export type { FabProps } from "./fab"
```

### 4g. `src/components/ui/balance-display.tsx` — replace entire file

Fixes in one pass: tabular numerals (spec §3.3), label carries direction so the amount
is an unsigned neutral fact when a label exists (UX-L2), no nonstandard `role="text"`
and no double-announcement (UX-L3), new type scale.

```tsx
import { useMemo } from "react"

import { cn } from "@/lib/utils"

/**
 * Size variants for different display contexts
 */
export type BalanceDisplayVariant = "display" | "title" | "body"

/**
 * Props for the BalanceDisplay component
 */
export interface BalanceDisplayProps {
  /**
   * The monetary amount to display (can be positive or negative)
   * Negative numbers indicate debt/owe, positive indicate credit/owed
   */
  amount: number

  /**
   * Size variant for different contexts
   * - display: 28px - dashboard balance hero
   * - title: 20px - card/row amounts
   * - body: 15px - inline amounts
   */
  variant?: BalanceDisplayVariant

  /**
   * Optional context label ("You owe" / "You're owed").
   * When present, the label carries direction and the amount renders UNSIGNED —
   * amounts are neutral facts (design v2 constitution; v1 UX-L2).
   */
  contextLabel?: string

  /**
   * Optional description for screen reader context
   * Example: "to Sam" → "You owe 450 rupees to Sam"
   */
  contextDescription?: string

  /**
   * Custom className for additional styling
   */
  className?: string
}

/**
 * Currency formatter with "Rs" prefix.
 * NOTE: hardcoded currency is a known WS10 item (per-group currency + formatCurrency
 * util). Do not fix here — WS3 is visual only.
 */
function formatCurrency(amount: number, signed: boolean): string {
  const absAmount = amount === 0 ? 0 : Math.abs(amount)

  const hasDecimals = absAmount % 1 !== 0
  const fractionDigits = hasDecimals ? 2 : 0

  const formatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })

  let formatted = formatter.format(absAmount).replace("₹", "Rs ")

  if (signed && amount < 0) {
    formatted = `-${formatted}`
  }

  return formatted
}

/**
 * Variant-specific typography classes (design v2 type scale)
 */
const variantClasses: Record<BalanceDisplayVariant, string> = {
  display: "text-display font-semibold",
  title: "text-title font-semibold",
  body: "text-body font-normal",
}

/**
 * BalanceDisplay component
 *
 * Displays monetary amounts in a consistent, neutral format.
 * Never uses red/green colors for debt - money is fact, not judgment.
 */
export function BalanceDisplay({
  amount,
  variant = "body",
  contextLabel,
  contextDescription,
  className,
}: BalanceDisplayProps) {
  // With a direction label, the amount is an unsigned neutral fact.
  const formattedAmount = useMemo(
    () => formatCurrency(amount, !contextLabel),
    [amount, contextLabel],
  )

  // Full sentence for screen readers; the visual spans are hidden from AT so
  // nothing is announced twice (v1 UX-L3).
  const srText = useMemo(() => {
    const amountText = `${Math.abs(amount)} rupees`
    const direction = amount < 0 ? "owe" : "are owed"

    if (contextDescription) {
      return `You ${direction} ${amountText} ${contextDescription}`
    }
    if (contextLabel) {
      return `${contextLabel} ${amountText}`
    }
    return amountText
  }, [amount, contextLabel, contextDescription])

  const showLabelAbove = variant === "display" || variant === "title"

  return (
    <div className={cn("flex flex-col", className)}>
      <span className="sr-only">{srText}</span>

      {contextLabel && showLabelAbove && (
        <span
          className="text-text-secondary text-body-small font-normal mb-1"
          aria-hidden="true"
        >
          {contextLabel}
        </span>
      )}

      <span
        className={cn(
          variantClasses[variant],
          // Neutral ink, tabular figures (design v2: tabular-nums mandatory on amounts)
          "text-text-primary tabular-nums tracking-tight",
        )}
        aria-hidden="true"
      >
        {contextLabel && variant === "body" && (
          <span className="text-text-secondary font-normal mr-1">
            {contextLabel}
          </span>
        )}
        {formattedAmount}
      </span>
    </div>
  )
}

export default BalanceDisplay
```

Gate: `npm run typecheck` (test failures for balance-display are expected until
Task 7 updates assertions).

---

## Task 5 — Layout & Dashboard

### 5a. Delete the orb and its hook

```bash
git rm frontend/src/components/ui/agent-orb.tsx
git rm frontend/src/shared/hooks/useLongPress.ts
```

Remove the `useLongPress` export line from `src/shared/hooks/index.ts`.
(Verified 2026-07-07: agent-orb is useLongPress's only consumer.)

### 5b. `src/routes/_layout.tsx` — replace entire file

```tsx
import {
  createFileRoute,
  Outlet,
  redirect,
  useLocation,
} from "@tanstack/react-router"
import { useCallback, useRef, useState } from "react"

import { BottomNav } from "@/components/ui/bottom-nav"
import { Fab } from "@/components/ui/fab"
import { SmartInputModal } from "@/features/expenses/components"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  const [isSmartInputOpen, setIsSmartInputOpen] = useState(false)
  const location = useLocation()
  // Ref for the FAB to return focus when the modal closes
  const fabRef = useRef<HTMLButtonElement>(null as HTMLButtonElement | null)

  const handleOpenSmartInput = useCallback(() => {
    setIsSmartInputOpen(true)
  }, [])

  const handleCloseSmartInput = useCallback(() => {
    setIsSmartInputOpen(false)
    // Focus return is handled by SmartInputModal using triggerRef
  }, [])

  // Determine entry point from route
  const entryPoint =
    location.pathname === "/" || location.pathname === "/dashboard"
      ? "dashboard"
      : "group"

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Main content area - bottom padding clears the fixed nav + FAB */}
      <main className="flex-1 p-6 pb-28 md:p-8 md:pb-28">
        <div className="mx-auto max-w-2xl">
          <Outlet />
        </div>
      </main>

      {/* Floating action button — tap to add an expense */}
      <Fab
        ref={fabRef}
        onClick={handleOpenSmartInput}
        className="fixed bottom-20 right-4 z-50"
      />

      {/* Persistent bottom tab bar navigation */}
      <BottomNav />

      {/* Smart Input Modal - triggered by the FAB */}
      <SmartInputModal
        open={isSmartInputOpen}
        onOpenChange={(open) => !open && handleCloseSmartInput()}
        entryPoint={entryPoint}
        triggerRef={fabRef}
      />
    </div>
  )
}

export default Layout
```

(Also changed: template Footer removed; content column `max-w-7xl` → `max-w-2xl` —
a ledger is a single readable column, not an admin dashboard.)

### 5c. `src/routes/_layout/index.tsx` — replace entire file (template greeting dies)

```tsx
import { createFileRoute } from "@tanstack/react-router"

import { Dashboard } from "@/features/dashboard"

export const Route = createFileRoute("/_layout/")({
  component: DashboardPage,
  head: () => ({
    meta: [
      {
        title: "Dashboard - ClearDues",
      },
    ],
  }),
})

function DashboardPage() {
  return <Dashboard />
}
```

### 5d. `src/features/dashboard/components/Dashboard.tsx` — replace entire file

The ledger-row dashboard: balance hero, hairline rows, no cards, no dead swipe
gestures (v1 UX-M6), mediator-voice copy.

```tsx
import { Link } from "@tanstack/react-router"

import { BalanceDisplay } from "@/components/ui/balance-display"
import { Button } from "@/components/ui/button"
import { useDashboard } from "../api/dashboard"
import type { GroupBalanceSummary } from "../types"

export function Dashboard() {
  const { data, isLoading, error, refetch } = useDashboard()

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6" aria-hidden="true">
        {/* Balance hero skeleton */}
        <div className="space-y-2 pt-2">
          <div className="h-3 w-28 rounded bg-border" />
          <div className="h-8 w-40 rounded bg-border" />
          <div className="h-3 w-24 rounded bg-border" />
        </div>
        {/* Ledger row skeletons */}
        <div className="border-y border-border divide-y divide-border">
          <div className="h-16" />
          <div className="h-16" />
          <div className="h-16" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4 py-8 text-center">
        <p className="text-body text-text-primary">
          Your balances didn't load.
        </p>
        <p className="text-body-small text-text-secondary">
          Check your connection and try again — nothing has been lost.
        </p>
        <Button variant="outline" onClick={() => refetch()}>
          Try again
        </Button>
      </div>
    )
  }

  if (!data?.groups.length) {
    return (
      <div className="space-y-4 py-12 text-center">
        <h2 className="text-title font-semibold text-text-primary">
          Nothing to keep score of yet
        </h2>
        <p className="text-body text-text-secondary">
          Start a group and add one expense — ClearDues takes it from there.
        </p>
        <Button asChild>
          <Link to="/groups">Start a group</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Balance hero */}
      <header className="pt-2">
        <p className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-1">
          Total balance
        </p>
        <BalanceDisplay
          amount={data.total_balance}
          variant="display"
          contextDescription="across all groups"
        />
        <p className="text-body-small text-text-secondary mt-1">
          Across {data.count} group{data.count !== 1 ? "s" : ""}
        </p>
      </header>

      {/* Groups ledger */}
      <section aria-label="Your groups">
        <h2 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-2">
          Your groups
        </h2>
        <ul className="border-y border-border divide-y divide-border">
          {data.groups.map((group) => (
            <GroupRow key={group.group_id} group={group} />
          ))}
        </ul>
      </section>
    </div>
  )
}

interface GroupRowProps {
  group: GroupBalanceSummary
}

function GroupRow({ group }: GroupRowProps) {
  // TODO: Update to `/groups/${group.group_id}` when the group detail route lands (WS5)
  return (
    <li>
      <Link
        to="/groups"
        className="flex min-h-14 items-center justify-between gap-4 py-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset hover:bg-accent transition-colors"
        aria-label={`Group ${group.group_name}`}
      >
        <div className="min-w-0 flex-1">
          <h3 className="text-body font-semibold text-text-primary truncate">
            {group.group_name}
          </h3>
          <p className="text-body-small text-text-secondary">
            {group.member_count} member{group.member_count !== 1 ? "s" : ""}{" "}
            &bull; {formatLastActivity(group.last_activity)}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <BalanceDisplay
            amount={group.net_balance}
            variant="title"
            contextLabel={group.net_balance < 0 ? "You owe" : "You're owed"}
            contextDescription={`in ${group.group_name}`}
          />
        </div>
      </Link>
    </li>
  )
}

function formatLastActivity(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  // Handle future dates (e.g., clock skew, timezone issues)
  if (diffDays < 0) return "Just now"
  if (diffDays === 0) return "Today"
  if (diffDays === 1) return "Yesterday"
  if (diffDays < 7) return `${diffDays} days ago`
  return date.toLocaleDateString()
}
```

### 5e. Delete SwipeableCard (framer-motion consumer; dead gestures)

```bash
git rm frontend/src/components/ui/swipeable-card.tsx
```

Remove its export lines from `src/components/ui/index.ts` (already gone if you pasted
4f). If a `swipeable-card` test file exists, delete it too. Swipe-to-settle returns in
WS6 as a fresh CSS/pointer-events implementation wired to real actions.

Gate: `npm run typecheck && npm run build`.

---

## Task 6 — framer-motion purge (remaining 10 files)

**The universal recipe** (applies to every file in the table): delete the
`framer-motion` import line; change `<motion.TAG` → `<TAG` (and the closing tag);
delete these props wherever they appear: `initial`, `animate`, `exit`, `variants`,
`transition`, `layout`, `whileHover`, `whileTap`, `drag`, `dragConstraints`,
`dragElastic`, `onDragEnd`, `style={{ y }}`; delete `useReducedMotion()` calls and
every `shouldReduceMotion` branch (keep the NON-reduced branch's *content*, not its
animation); delete now-unused `TargetAndTransition`/`Variants` type imports and any
orphaned `xxxVariants`/`xxxAnimation` const definitions. Then add the CSS class listed
below to the element that used to animate. `tw-animate-css` is already installed and
provides `animate-in`/`fade-in-0`/`slide-in-from-bottom-4`/`zoom-in-95` etc.

| File | Element that animated | Class to add |
|---|---|---|
| `SmartInputModal.tsx` | modal root `motion.div` (line ~305) | `data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:slide-in-from-bottom-4 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:slide-out-to-bottom-4 duration-200` |
| `AICommentaryBubble.tsx` | root `motion.div` | `animate-in fade-in-0 slide-in-from-bottom-1 duration-150` |
| `ExpensePreviewCard.tsx` | both `motion.div`s | `animate-in fade-in-0 duration-150` |
| `EditableExpensePreview.tsx` | root `motion.div` (~273) | `animate-in fade-in-0 duration-150` |
| `EditableExpensePreview.tsx` | `AnimatePresence` block (~438–507) | remove `AnimatePresence`, keep the conditional render, add `animate-in fade-in-0 duration-150` to the inner div |
| `ActivityFeedItem.tsx` | root `motion.div` | `animate-in fade-in-0 duration-150` |
| `PercentageSplitInputs.tsx` | row `motion.div` | `animate-in fade-in-0 duration-150` |
| `UnequalSplitInputs.tsx` | row `motion.div` | `animate-in fade-in-0 duration-150` |
| `MemberChips.tsx` | chip `motion.button` | `transition-transform duration-100 active:scale-95` |
| `SplitPicker.tsx` | option `motion.button` | `transition-transform duration-100 active:scale-95` |
| `inline-input.tsx` | wrapper `motion.div` | nothing — error state is already conveyed by the ring/border color |

**SmartInputModal.tsx — extra deletions** (it has gesture machinery beyond the recipe):
delete the `useMotionValue` line (`const y = useMotionValue(0)`), the
`SWIPE_DISMISS_THRESHOLD` const, the whole `handleDragEnd` function, the
`modalVariants` const, the `PanInfo` type import, and the drag-handle indicator block
(the `aria-hidden` div with `touch-none` just inside the FocusTrap — swipe-to-dismiss
is gone, so its affordance must go too; the modal closes via its Close button and
overlay click). Keep FocusTrap, keep the Radix structure, keep all state logic.

**SettlementClaimCard.tsx — the settle moment lives here.** Remove
`AnimatePresence`/`motion.div` per the recipe, then wire the one choreographed
animation: on the element that previously exit-animated when a claim is
confirmed/settled, apply `className="settle-glow"` (defined in index.css) at the
moment the settled state becomes true. If the component removes the card from the
list after settling, delay the removal until animation end:

```tsx
<div
  className={cn(rowClasses, isSettled && "settle-glow")}
  onAnimationEnd={isSettled ? handleRemoveAfterSettle : undefined}
>
```

where `handleRemoveAfterSettle` is whatever callback previously ran on the
AnimatePresence exit completion. No other component gets this animation.

After the purge:

```bash
grep -r "framer-motion" frontend/src   # MUST return nothing
npm uninstall framer-motion                      # if not already done in Task 1
```

Gate: `npm run typecheck && npm run build`.

---

## Task 7 — Tests

1. Run `npm run test`. Expected breakage clusters and their fixes:
   - **balance-display / Dashboard tests:** amounts with a `contextLabel` no longer
     render a `-` sign, `role="text"` is gone (query by the `sr-only` text instead),
     skeleton/error/empty copy changed to the Task 5d strings. Update assertions to
     the new behavior — the new behavior is correct by spec.
   - **framer-motion mocks:** any test mocking `framer-motion` — delete the mock.
   - **SmartInputModal tests:** drag-to-dismiss tests (if any) — delete; the gesture
     no longer exists. Focus-trap/jsdom workaround stays untouched.
   - **Known-bug markers stay honest:** the existing `it.fails` (S4-M1 rounding, fix
     in WS5) and skipped mock-AI tests (WS7) must remain marked, not "fixed".
2. Add the axe smoke test (spec §6.7). New dev deps + file:

```bash
npm install -D vitest-axe axe-core
```

New file `src/test/a11y.smoke.test.tsx`:

```tsx
import { render } from "@testing-library/react"
import { axe } from "vitest-axe"
import "vitest-axe/extend-expect"

import { BalanceDisplay } from "@/components/ui/balance-display"
import { Button } from "@/components/ui/button"
import { Fab } from "@/components/ui/fab"

// Axe smoke: catches missing labels/roles/contrast-adjacent markup regressions in
// the design-system primitives. Full-page axe runs land with the Playwright
// journeys in WS11.
describe("a11y smoke (design system primitives)", () => {
  it("BalanceDisplay has no violations", async () => {
    const { container } = render(
      <BalanceDisplay amount={-450} variant="title" contextLabel="You owe" />,
    )
    expect(await axe(container)).toHaveNoViolations()
  })

  it("Button has no violations", async () => {
    const { container } = render(<Button>Settle up</Button>)
    expect(await axe(container)).toHaveNoViolations()
  })

  it("Fab has no violations", async () => {
    const { container } = render(<Fab />)
    expect(await axe(container)).toHaveNoViolations()
  })
})
```

If `vitest-axe`'s matcher types clash with the installed vitest major, fall back to
`expect((await axe(container)).violations).toEqual([])` — same guarantee, no matcher.

Gate: `npm run test` fully green (with the honest `it.fails`/skips still marked).

---

## Task 8 — Verification & reporting (Definition of Done)

1. **Gates:** `npm run typecheck && npm run test && npm run build` green; backend
   untouched but run `docker compose exec backend pytest -q` anyway (DoD v2 #1).
2. **Bundle report:** from the build output, record gzip sizes of every JS chunk.
   Budgets (spec §5): main app chunk **≤ 250 KB gz**; no chunk contains framer-motion,
   react-icons, or devtools (verify: `grep -l "framer" dist/assets/*.js` → empty).
   Web font transfer must be **0 KB** and third-party requests at first paint **0**
   (verify: `grep -ri "fonts.googleapis" dist/` → empty).
3. **Screenshots (DoD v2 #2):** 375px and 1280px, light and dark = 8 shots minimum,
   covering: login, dashboard (with data), dashboard (empty state), Smart Input open.
   Attach to the WS3 completion notes in the execution plan.
4. **Manual pass:** every bottom-nav destination reachable; FAB opens Smart Input and
   focus returns to FAB on close; keyboard-only walk of login → dashboard → modal;
   template routes (/items, /admin) still render (unstyled is fine — they die in WS8).
5. **Tracker updates:** check WS3 boxes in `10-execution-plan.md` with the measured
   bundle numbers in the notes; session-context.md learnings; any deferred LOW issue
   → technical-debt-log.yaml.

**Explicit WS3 non-goals (do NOT do these, they are other sessions' scope):**
currency/"Rs" purge (WS10) · `/groups/$groupId` route + group ledger screen (WS5) ·
real AI/SSE in Smart Input (WS7) · deleting template routes/components (WS8) ·
swipe-to-settle (WS6) · PWA manifest (WS11).

---

## Appendix A — Copy deck (exact strings, mediator voice)

| Location | String |
|---|---|
| Dashboard balance label | `Total balance` |
| Dashboard groups heading | `Your groups` |
| Dashboard empty title | `Nothing to keep score of yet` |
| Dashboard empty body | `Start a group and add one expense — ClearDues takes it from there.` |
| Dashboard empty CTA | `Start a group` |
| Dashboard error line 1 | `Your balances didn't load.` |
| Dashboard error line 2 | `Check your connection and try again — nothing has been lost.` |
| Dashboard error CTA | `Try again` |
| FAB aria-label | `Add an expense` |
| App `<title>` | `ClearDues` |
| Meta description | `ClearDues keeps score of shared expenses so you never have to ask.` |

Voice rules for any copy not listed: calm third party, no exclamation marks except
in genuine celebration, no blame, no jargon, errors always say what to do next.

## Appendix B — What the reviewer should check (for /code-review)

1. No `framer-motion`, `react-icons`, or devtools in prod bundle. Fonts: zero requests.
2. No resting shadows anywhere except dialogs/sheets/FAB (`shadow-lg`).
3. `--accent` is NOT teal (UX-C1 class). `text-text-*` utilities still resolve.
4. All touch targets ≥44px: buttons h-11, nav rows min-h-14, FAB size-14.
5. Amounts: `tabular-nums`, unsigned when a direction label is present.
6. Template files were NOT restyled (wasted-work check).
7. The settle-glow animation exists exactly once (SettlementClaimCard).
8. Screenshots at both viewports/themes attached; `it.fails`/skip markers intact.
