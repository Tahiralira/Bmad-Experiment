/**
 * ClearDues UI Components
 *
 * Custom design system components for ClearDues application.
 * These components implement the Epic 2.5 UX Foundation & Design System.
 *
 * @module components/ui
 */

// Balance Display (Story 2.5.6)
export { BalanceDisplay } from "./balance-display"
export type { BalanceDisplayProps, BalanceDisplayVariant } from "./balance-display"

// Swipeable Card (Story 2.5.5)
export { SwipeableCard } from "./swipeable-card"
export type { SwipeableCardProps } from "./swipeable-card"

// Smart Input Modal lives in features/expenses/components (the ui/ copy was
// an unused duplicate and has been removed)

// Bottom Navigation (replaces Orbital Navigation from Story 2.5.3)
export { BottomNav } from "./bottom-nav"
export type { BottomNavProps } from "./bottom-nav"

// Agent Orb (Story 2.5.2)
export { AgentOrb } from "./agent-orb"
export type { AgentOrbProps } from "./agent-orb"
