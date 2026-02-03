import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"
import { EditableExpensePreview } from "./EditableExpensePreview"
import type { ExpenseParseResponse } from "../types"
import type { ExpenseCreate } from "../types"

export interface ExpensePreviewCardProps {
  /** Parsed expense data (null in placeholder state) */
  data: ExpenseParseResponse | null
  /** Current state of the preview card */
  status: "placeholder" | "loading" | "ready" | "error"
  /** Called when expense is confirmed/saved */
  onConfirm?: (editedData: ExpenseCreate) => Promise<void>
  /** Called when user discards the expense */
  onDiscard?: () => void
  /** Group ID for fetching members */
  groupId?: string
  /** Auto-confirm enabled preference (default: false) */
  autoConfirmEnabled?: boolean
  /** Additional className for styling */
  className?: string
}

/**
 * Expense Preview Card - displays parsed expense data below the input field.
 *
 * In Story 3.2, this component shows a placeholder state.
 * In Story 3.4, it displays actual parsed expense details with editable fields.
 *
 * @example
 * ```tsx
 * <ExpensePreviewCard
 *   data={parsedData} // Parsed expense data from AI
 *   status="ready"
 *   onConfirm={handleConfirm}
 *   onDiscard={handleDiscard}
 *   groupId="group-123"
 * />
 * ```
 */
export function ExpensePreviewCard({
  data,
  status,
  onConfirm,
  onDiscard,
  groupId,
  autoConfirmEnabled = false,
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

  // Ready state (Story 3.4) - Display editable preview
  if (status === "ready" && data && onConfirm && onDiscard && groupId) {
    return (
      <EditableExpensePreview
        parsedData={data}
        onConfirm={onConfirm}
        onDiscard={onDiscard}
        groupId={groupId}
        autoConfirmEnabled={autoConfirmEnabled}
        className={cn("mt-4", className)}
      />
    )
  }

  // Error state (Story 3.4)
  if (status === "error") {
    return (
      <motion.div
        initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={cn(
          "mt-4 p-4 rounded-lg",
          "bg-error/10 border border-error/30",
          className
        )}
      >
        <p className="text-error text-sm">
          Failed to parse expense. Please try again or switch to manual form.
        </p>
      </motion.div>
    )
  }

  return null
}
