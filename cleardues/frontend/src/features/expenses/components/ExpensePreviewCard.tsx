import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"

export interface ExpensePreviewCardProps {
  /** Parsed expense data (null in placeholder state) */
  data: null
  /** Current state of the preview card */
  status: "placeholder" | "loading" | "ready" | "error"
  /** Additional className for styling */
  className?: string
}

/**
 * Expense Preview Card - displays parsed expense data below the input field.
 *
 * In Story 3.2, this component shows a placeholder state.
 * In Story 3.4, it will display actual parsed expense details with editable fields.
 *
 * @example
 * ```tsx
 * <ExpensePreviewCard
 *   data={null} // No parsed data yet (Story 3.3)
 *   status="placeholder"
 * />
 * ```
 */
export function ExpensePreviewCard({
  data: _data, // Will be used in Story 3.4 to display parsed expense details
  status,
  className,
}: ExpensePreviewCardProps) {
  const shouldReduceMotion = useReducedMotion()

  // Placeholder state (Story 3.2)
  if (status === "placeholder") {
    return (
      <motion.div
        initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={cn(
          "mt-4 p-6 rounded-lg",
          "bg-surface border border-border",
          "text-center",
          className
        )}
      >
        <p className="text-text-muted body-small">
          Enter expense above to see preview
        </p>
      </motion.div>
    )
  }

  // Loading state (Story 3.4)
  if (status === "loading") {
    return (
      <div className={cn("mt-4 p-4 rounded-lg", "bg-surface-elevated border border-border")}>
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-3">
            <div className="h-4 bg-muted rounded w-3/4" />
            <div className="h-4 bg-muted rounded w-1/2" />
            <div className="h-4 bg-muted rounded w-1/3" />
          </div>
        </div>
      </div>
    )
  }

  // Ready/Error states (Story 3.4)
  // TODO: Implement in Story 3.4 after AI parsing is ready
  return null
}
