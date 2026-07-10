import { useState, useEffect } from "react"
import { Check, X, Clock } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { BalanceDisplay } from "@/components/ui/balance-display"
import { cn } from "@/lib/utils"
import { useConfirmSettlement, useRejectSettlement } from "../api/expenses"
import type { Expense, SettlementClaimPublic } from "../types"
import { formatRelativeTime } from "../utils/timeFormat"

// =============================================================================
// Types
// =============================================================================

interface SettlementClaimCardProps {
  /** The settlement claim data */
  claim: Pick<
    SettlementClaimPublic,
    "id" | "amount" | "claimed_at" | "user_name"
  >
  /** The associated expense */
  expense: Pick<Expense, "description" | "amount">
  /** Optional className for styling */
  className?: string
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * Displays a pending settlement claim for an expense owner to review.
 * Story 5.2: Owner Confirms Settlement
 *
 * Features:
 * - Displays claimant name, amount, claimed date, expense description
 * - "Confirm" (amber/success) and "Reject" (muted/destructive) buttons
 * - Optimistic UI: immediate visual update on confirm/reject
 * - Error recovery: useEffect reverts on mutation failure
 * - "Payment = Silence" on confirm: the settle-glow animation (the app's
 *   single choreographed animation, design v2 §3.5) plays, then the card is
 *   removed from the list at animation end
 */
export function SettlementClaimCard({
  claim,
  expense,
  className,
}: SettlementClaimCardProps) {
  const confirmMutation = useConfirmSettlement()
  const rejectMutation = useRejectSettlement()

  const [optimisticState, setOptimisticState] = useState<
    "pending" | "confirmed" | "rejected"
  >("pending")
  const [isRemoving, setIsRemoving] = useState(false)

  // Revert optimistic state on confirm error
  useEffect(() => {
    if (confirmMutation.isError && optimisticState === "confirmed") {
      setOptimisticState("pending")
      setIsRemoving(false)
    }
  }, [confirmMutation.isError, optimisticState])

  // Revert optimistic state on reject error
  useEffect(() => {
    if (rejectMutation.isError && optimisticState === "rejected") {
      setOptimisticState("pending")
    }
  }, [rejectMutation.isError, optimisticState])

  const handleConfirm = () => {
    setOptimisticState("confirmed")
    // The settle-glow animation plays; removal happens on its onAnimationEnd
    confirmMutation.mutate(claim.id)
  }

  const handleRemoveAfterSettle = () => {
    setIsRemoving(true)
  }

  const handleReject = () => {
    setOptimisticState("rejected")
    rejectMutation.mutate(claim.id)
  }

  const claimantName = claim.user_name || "Someone"
  const isConfirmed = optimisticState === "confirmed"

  if (isRemoving) {
    return null
  }

  return (
    <Card
      className={cn(
        optimisticState === "rejected" && "border-destructive",
        isConfirmed && "settle-glow",
        className
      )}
      onAnimationEnd={isConfirmed ? handleRemoveAfterSettle : undefined}
    >
      <CardContent className="space-y-3 p-4">
        {/* Header: Description + Claimant */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-base font-medium">
              {expense.description}
            </h3>
            <p className="text-sm text-muted-foreground">
              From: {claimantName}
            </p>
          </div>

          {optimisticState === "pending" && (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
              <Clock className="h-3 w-3" />
              Pending
            </span>
          )}
        </div>

        {/* Amounts */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Amount claimed</p>
            <BalanceDisplay amount={Number(claim.amount)} variant="title" />
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Total expense</p>
            <p className="text-lg font-semibold">
              Rs {expense.amount}
            </p>
          </div>
        </div>

        {/* Claim date */}
        <p className="text-xs text-muted-foreground">
          Claimed {formatRelativeTime(claim.claimed_at)}
        </p>

        {/* Action Buttons */}
        {optimisticState === "pending" && (
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={handleConfirm}
              disabled={confirmMutation.isPending || rejectMutation.isPending}
              className={cn(
                "inline-flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5",
                "text-sm font-medium transition-colors",
                "bg-amber-500 text-white shadow-sm",
                "hover:bg-amber-600",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
              aria-label="Confirm settlement claim"
            >
              <Check className="h-4 w-4" />
              Confirm
            </button>
            <button
              type="button"
              onClick={handleReject}
              disabled={confirmMutation.isPending || rejectMutation.isPending}
              className={cn(
                "inline-flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5",
                "text-sm font-medium transition-colors",
                "border border-border bg-surface-elevated text-muted-foreground",
                "hover:bg-muted hover:text-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
              aria-label="Reject settlement claim"
            >
              <X className="h-4 w-4" />
              Reject
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
