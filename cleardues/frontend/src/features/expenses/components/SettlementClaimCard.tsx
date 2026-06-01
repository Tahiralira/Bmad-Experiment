import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Check, X, Clock } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { BalanceDisplay } from "@/components/ui/balance-display"
import { cn } from "@/lib/utils"
import { useConfirmSettlement, useRejectSettlement } from "../api/expenses"
import { formatRelativeTime } from "../utils/timeFormat"

// =============================================================================
// Types
// =============================================================================

interface SettlementClaimCardProps {
  /** The settlement claim data */
  claim: {
    id: string
    amount: number
    claimed_at: string
    user_name: string | null
  }
  /** The associated expense */
  expense: {
    description: string
    amount: number
  }
  /** Optional className for styling */
  className?: string
}

// =============================================================================
// Animation Constants
// =============================================================================

const GLOW_DURATION_MS = 300
const COLLAPSE_DURATION_MS = 300

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
 * - "Payment = Silence" animation on confirm:
 *   Amber glow → card collapses → removed from list
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

  const handleConfirm = useCallback(() => {
    setOptimisticState("confirmed")
    // Start glow animation, then collapse
    setTimeout(() => {
      setIsRemoving(true)
    }, GLOW_DURATION_MS)
    confirmMutation.mutate(claim.id)
  }, [claim.id, confirmMutation])

  const handleReject = useCallback(() => {
    setOptimisticState("rejected")
    rejectMutation.mutate(claim.id)
  }, [claim.id, rejectMutation])

  const claimantName = claim.user_name || "Someone"

  return (
    <AnimatePresence>
      {!isRemoving && (
        <motion.div
          layout
          initial={{ opacity: 1, scale: 1 }}
          animate={
            optimisticState === "confirmed"
              ? {
                  opacity: 0,
                  scale: 0.98,
                  transition: {
                    duration: COLLAPSE_DURATION_MS / 1000,
                    delay: GLOW_DURATION_MS / 1000,
                  },
                }
              : { opacity: 1, scale: 1 }
          }
          exit={{
            opacity: 0,
            height: 0,
            marginBottom: 0,
            transition: { duration: COLLAPSE_DURATION_MS / 1000 },
          }}
        >
          <Card
            className={cn(
              "transition-all duration-300",
              optimisticState === "confirmed" &&
                "border-amber-400 shadow-[0_0_15px_rgba(251,191,36,0.4)] dark:border-amber-500 dark:shadow-[0_0_15px_rgba(245,158,11,0.3)]",
              optimisticState === "rejected" &&
                "border-red-300 dark:border-red-700",
              className
            )}
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
                  <BalanceDisplay amount={claim.amount} variant="title" />
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Total expense</p>
                  <p className="text-lg font-semibold">
                    Rs {expense.amount.toFixed(2)}
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
        </motion.div>
      )}
    </AnimatePresence>
  )
}
