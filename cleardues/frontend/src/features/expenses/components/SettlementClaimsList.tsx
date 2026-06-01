import { CheckCircle } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { usePendingSettlementClaims } from "../api/expenses"
import { SettlementClaimCard } from "./SettlementClaimCard"

// =============================================================================
// Props
// =============================================================================

interface SettlementClaimsListProps {
  /** Optional className for styling */
  className?: string
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * Displays a list of pending settlement claims for the expense owner to review.
 * Story 5.2: Owner Confirms Settlement
 *
 * Shows claims where the current user is the expense owner (payer)
 * and someone has submitted a settlement claim awaiting confirmation.
 *
 * Features:
 * - List of SettlementClaimCard components
 * - Empty state: celebratory "All settled" with amber accent
 * - Skeleton loading state (3 skeleton cards)
 */
export function SettlementClaimsList({ className }: SettlementClaimsListProps) {
  const { data: pendingClaims, isLoading, error } = usePendingSettlementClaims()

  if (isLoading) {
    return <SettlementClaimsSkeleton />
  }

  if (error) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        Failed to load settlement claims. Please try again.
      </div>
    )
  }

  if (!pendingClaims?.length) {
    return (
      <CelebratoryEmptyState />
    )
  }

  return (
    <div className={className}>
      <div className="space-y-3">
        {pendingClaims.map((item) => (
          <SettlementClaimCard
            key={item.claim.id}
            claim={item.claim}
            expense={item.expense}
          />
        ))}
      </div>
    </div>
  )
}

// =============================================================================
// Celebratory Empty State (Payment = Silence UX)
// =============================================================================

/**
 * Calm, non-intrusive empty state shown when all settlement claims are processed.
 * Amber-tinted background with peaceful "All settled" message.
 * No confetti, no sound — silence is the reward.
 */
function CelebratoryEmptyState() {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-8 text-center dark:border-amber-800 dark:bg-amber-950/30">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/50">
        <CheckCircle className="h-6 w-6 text-amber-600 dark:text-amber-400" />
      </div>
      <p className="text-lg font-medium text-amber-800 dark:text-amber-200">
        All settled
      </p>
      <p className="mt-1 text-sm text-amber-600 dark:text-amber-400">
        No pending settlement claims to review
      </p>
    </div>
  )
}

// =============================================================================
// Skeleton Loading State
// =============================================================================

function SettlementClaimsSkeleton() {
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
            <div className="flex gap-2">
              <Skeleton className="h-10 flex-1" />
              <Skeleton className="h-10 flex-1" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
