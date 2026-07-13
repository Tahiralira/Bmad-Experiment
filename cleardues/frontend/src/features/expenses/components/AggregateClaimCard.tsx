import { useEffect, useState } from "react"
import { Check, Clock, X } from "lucide-react"

import { BalanceDisplay } from "@/components/ui/balance-display"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

import { useConfirmSettlement, useRejectSettlement } from "../api/expenses"
import type { SettlementClaimPublic } from "../types"
import { formatRelativeTime, formatTimeUntil } from "../utils/timeFormat"

interface AggregateClaimCardProps {
  claim: SettlementClaimPublic
  /** The signed-in user's id — decides which side of the claim they see */
  currentUserId: string
  className?: string
}

/**
 * One aggregate settle-up claim (WS6): "X says they've paid you the net"
 * covering every confirmed expense between the pair in the group.
 *
 * Counterparty view: Confirm / Reject with the 72h auto-confirm note.
 * Claimant view: waiting state with the same countdown.
 *
 * Follows SettlementClaimCard's optimistic pattern: immediate visual state,
 * error recovery via useEffect, settle-glow then removal on confirm.
 */
export function AggregateClaimCard({
  claim,
  currentUserId,
  className,
}: AggregateClaimCardProps) {
  const confirmMutation = useConfirmSettlement()
  const rejectMutation = useRejectSettlement()

  const [optimisticState, setOptimisticState] = useState<
    "pending" | "confirmed" | "rejected"
  >("pending")
  const [isRemoving, setIsRemoving] = useState(false)

  useEffect(() => {
    if (confirmMutation.isError && optimisticState === "confirmed") {
      setOptimisticState("pending")
      setIsRemoving(false)
    }
  }, [confirmMutation.isError, optimisticState])

  useEffect(() => {
    if (rejectMutation.isError && optimisticState === "rejected") {
      setOptimisticState("pending")
    }
  }, [rejectMutation.isError, optimisticState])

  const isReviewer = claim.counterparty_user_id === currentUserId
  const claimantName = claim.user_name || "Someone"
  const counterpartyName = claim.counterparty_name || "them"
  const expenseNoun =
    claim.covered_expense_count === 1
      ? "1 expense"
      : `${claim.covered_expense_count} expenses`

  const isConfirmed = optimisticState === "confirmed"

  if (isRemoving) {
    return null
  }

  return (
    <Card
      className={cn(
        optimisticState === "rejected" && "border-destructive",
        isConfirmed && "settle-glow",
        className,
      )}
      onAnimationEnd={isConfirmed ? () => setIsRemoving(true) : undefined}
    >
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="text-base font-medium">
              {isReviewer
                ? `Settle-up from ${claimantName}`
                : `Settle-up with ${counterpartyName}`}
            </h3>
            <p className="text-sm text-muted-foreground">
              {isReviewer
                ? `${claimantName} says they've paid you the net across ${expenseNoun}`
                : `Covers ${expenseNoun} — waiting on ${counterpartyName} to confirm`}
            </p>
          </div>

          {optimisticState === "pending" && (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
              <Clock className="h-3 w-3" />
              Pending
            </span>
          )}
        </div>

        <div>
          <p className="text-sm text-muted-foreground">Net amount</p>
          <BalanceDisplay amount={Number(claim.amount)} variant="title" />
        </div>

        <p className="text-xs text-muted-foreground">
          Claimed {formatRelativeTime(claim.claimed_at)}
          {claim.auto_confirm_at &&
            ` · auto-confirms ${formatTimeUntil(claim.auto_confirm_at)}`}
        </p>

        {isReviewer && optimisticState === "pending" && (
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={() => {
                setOptimisticState("confirmed")
                confirmMutation.mutate(claim.id)
              }}
              disabled={confirmMutation.isPending || rejectMutation.isPending}
              className={cn(
                "inline-flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5",
                "text-sm font-medium transition-colors",
                "bg-amber-500 text-white shadow-sm",
                "hover:bg-amber-600",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400",
                "disabled:pointer-events-none disabled:opacity-50",
              )}
              aria-label={`Confirm settle-up from ${claimantName}`}
            >
              <Check className="h-4 w-4" />
              Confirm
            </button>
            <button
              type="button"
              onClick={() => {
                setOptimisticState("rejected")
                rejectMutation.mutate(claim.id)
              }}
              disabled={confirmMutation.isPending || rejectMutation.isPending}
              className={cn(
                "inline-flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5",
                "text-sm font-medium transition-colors",
                "border border-border bg-surface-elevated text-muted-foreground",
                "hover:bg-muted hover:text-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:pointer-events-none disabled:opacity-50",
              )}
              aria-label={`Reject settle-up from ${claimantName}`}
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
