import { Clock } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { BalanceDisplay } from "@/components/ui/balance-display"
import { usePendingSettlements } from "../api/expenses"
import type { PendingSettlement } from "../types"
import { formatRelativeTime } from "../utils/timeFormat"

// =============================================================================
// Props
// =============================================================================

interface PendingSettlementsListProps {
  /** Optional className for styling */
  className?: string
  /** When set, only claims for expenses in this group are shown (WS5) */
  groupId?: string
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * Displays a list of expenses with pending settlement claims.
 * Story 5.1: Mark Debt as Settled (Claim Payment)
 *
 * Shows each expense where the user has submitted a settlement claim
 * that is still awaiting owner confirmation.
 */
export function PendingSettlementsList({
  className,
  groupId,
}: PendingSettlementsListProps) {
  const { data, isLoading, error } = usePendingSettlements()
  const pendingSettlements = groupId
    ? data?.filter((item) => item.expense.group_id === groupId)
    : data

  if (isLoading) {
    return <PendingSettlementsSkeleton />
  }

  if (error) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        Failed to load pending settlements. Please try again.
      </div>
    )
  }

  if (!pendingSettlements?.length) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <p className="text-lg font-medium">No pending settlements</p>
        <p className="text-sm">
          Expenses you mark as paid will appear here while awaiting confirmation.
        </p>
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="space-y-3">
        {pendingSettlements.map((item) => (
          <PendingSettlementCard key={item.claim.id} item={item} />
        ))}
      </div>
    </div>
  )
}

// =============================================================================
// Sub-components
// =============================================================================

interface PendingSettlementCardProps {
  item: PendingSettlement
}

function PendingSettlementCard({ item }: PendingSettlementCardProps) {
  const { expense, claim } = item

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{expense.description}</CardTitle>
          <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
            <Clock className="h-3 w-3" />
            Pending
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Amount */}
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
      </CardContent>
    </Card>
  )
}

function PendingSettlementsSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-3">
            <div className="flex justify-between">
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-6 w-16" />
            </div>
            <div className="flex justify-between">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-24" />
            </div>
            <Skeleton className="h-4 w-32" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
