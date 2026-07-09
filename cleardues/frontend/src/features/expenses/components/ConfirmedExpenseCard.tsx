import { useState, useCallback, useEffect } from "react"
import { CheckCircle, Clock, Banknote } from "lucide-react"
import { toast } from "sonner"

import { SwipeableCard } from "@/components/ui/swipeable-card"
import { BalanceDisplay } from "@/components/ui/balance-display"
import { cn } from "@/lib/utils"
import { useSettleExpense } from "../api/expenses"
import type { Expense, ExpenseSplit } from "../types"

// =============================================================================
// Types
// =============================================================================

interface ConfirmedExpenseCardProps {
  /** The confirmed expense */
  expense: Expense
  /** The current user's split in this expense */
  split: ExpenseSplit
  /** Name of the expense owner (payer) for "Awaiting confirmation from [Owner]" */
  ownerName: string | null
  /** Optional className for styling */
  className?: string
}

// =============================================================================
// Undo Toast Duration
// =============================================================================

const UNDO_TIMEOUT_MS = 3000

// =============================================================================
// Main Component
// =============================================================================

/**
 * Displays a confirmed expense card with swipe-to-settle functionality.
 * Story 5.1: Mark Debt as Settled (Claim Payment)
 *
 * Features:
 * - Swipe right to trigger "Mark Paid" action
 * - Optimistic UI showing "Awaiting confirmation" state immediately
 * - Undo toast with 3-second countdown
 * - Desktop fallback: "Mark Paid" button on hover
 * - Keyboard accessible (ArrowRight to reveal, Enter to trigger)
 */
export function ConfirmedExpenseCard({
  expense,
  split,
  ownerName,
  className,
}: ConfirmedExpenseCardProps) {
  const settleMutation = useSettleExpense()
  const [isOptimisticSettled, setIsOptimisticSettled] = useState(false)

  // Revert optimistic state if the actual mutation fails
  useEffect(() => {
    if (settleMutation.isError && isOptimisticSettled) {
      setIsOptimisticSettled(false)
    }
  }, [settleMutation.isError, isOptimisticSettled])

  /**
   * Handle the Mark Paid action.
   * Uses optimistic UI: immediately shows "awaiting confirmation" state,
   * then sends the actual API request. Shows an undo toast for 3 seconds.
   */
  const handleMarkPaid = useCallback(() => {
    // Optimistic update - immediately show awaiting state
    setIsOptimisticSettled(true)

    // Show undo toast
    const undoId = "undo-settle-" + expense.id
    let isUndone = false

    toast("Settlement claim submitted", {
      id: undoId,
      duration: UNDO_TIMEOUT_MS,
      action: {
        label: "Undo",
        onClick: () => {
          isUndone = true
          setIsOptimisticSettled(false)
          toast.dismiss(undoId)
        },
      },
      onAutoClose: () => {
        // Toast auto-closed without undo → send the actual mutation
        if (!isUndone) {
          settleMutation.mutate(expense.id)
        }
      },
    })
  }, [expense.id, settleMutation])

  // If optimistically settled or actually settled, show awaiting state
  const isSettled = isOptimisticSettled || settleMutation.isSuccess

  return (
    <SwipeableCard
      rightAction={{
        icon: Banknote,
        label: "Mark Paid",
        onTrigger: handleMarkPaid,
        variant: "default",
      }}
      disabled={isSettled}
      ariaLabel={`Expense: ${expense.description}`}
      className={className}
    >
      <div
        className={cn(
          "rounded-lg border p-4 transition-colors",
          isSettled
            ? "border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/30"
            : "border-border bg-surface-elevated"
        )}
      >
        {/* Header: Description + Status */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-base font-medium">
              {expense.description}
            </h3>
            <p className="text-sm text-muted-foreground">
              Total: Rs {expense.amount.toFixed(2)}
            </p>
          </div>

          {isSettled ? (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
              <Clock className="h-3 w-3" />
              Pending
            </span>
          ) : (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-success-subtle px-2.5 py-1 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-200">
              <CheckCircle className="h-3 w-3" />
              Confirmed
            </span>
          )}
        </div>

        {/* Amount */}
        <div className="mt-3 flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Your share</p>
            <BalanceDisplay amount={split.amount_owed} variant="title" />
          </div>
        </div>

        {/* Awaiting confirmation state */}
        {isSettled && (
          <div className="mt-3 flex items-center gap-2 text-sm text-amber-700 dark:text-amber-300">
            <Clock className="h-4 w-4 animate-pulse" />
            <span>
              Awaiting confirmation from{" "}
              {ownerName || "expense owner"}
            </span>
          </div>
        )}

        {/* Desktop fallback: Mark Paid button (visible on hover, hidden on settled) */}
        {!isSettled && (
          <div className="mt-3 hidden md:flex md:justify-end">
            <button
              type="button"
              onClick={handleMarkPaid}
              className={cn(
                "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium",
                "bg-primary text-primary-foreground shadow-sm",
                "opacity-0 transition-opacity duration-150",
                "group-hover:opacity-100", // SwipeableCard wraps with group
                "hover:bg-primary/90",
                "focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              )}
            >
              <Banknote className="h-4 w-4" />
              Mark Paid
            </button>
          </div>
        )}
      </div>
    </SwipeableCard>
  )
}
