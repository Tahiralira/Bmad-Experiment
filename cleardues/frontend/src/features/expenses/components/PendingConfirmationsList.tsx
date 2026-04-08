import { Check, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { BalanceDisplay } from "@/components/ui/balance-display"
import {
  usePendingConfirmations,
  useConfirmExpense,
  useRejectExpense,
} from "../api/expenses"
import type { PendingConfirmation } from "../types"

interface PendingConfirmationsListProps {
  /** Optional callback when a confirmation action is taken */
  onConfirmAction?: (expense: PendingConfirmation) => void
  /** Optional className for styling */
  className?: string
}

/**
 * Displays a list of expenses pending user confirmation.
 * Story 4.2: Expense Confirmation Workflow
 *
 * Shows each expense with:
 * - Amount the user owes
 * - Total expense amount
 * - Who paid
 * - Description
 * - Split breakdown
 * - Confirm and Reject buttons
 */
export function PendingConfirmationsList({
  onConfirmAction,
  className,
}: PendingConfirmationsListProps) {
  const { data: pendingConfirmations, isLoading, error } = usePendingConfirmations()
  const confirmMutation = useConfirmExpense()
  const rejectMutation = useRejectExpense()

  if (isLoading) {
    return <PendingConfirmationsSkeleton />
  }

  if (error) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        Failed to load pending confirmations. Please try again.
      </div>
    )
  }

  if (!pendingConfirmations?.length) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <p className="text-lg font-medium">All caught up!</p>
        <p className="text-sm">No expenses pending your confirmation.</p>
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="space-y-4">
        {pendingConfirmations.map((item) => (
          <PendingConfirmationCard
            key={item.expense.id}
            item={item}
            onConfirm={() => {
              confirmMutation.mutate(item.expense.id)
              onConfirmAction?.(item)
            }}
            onReject={() => {
              rejectMutation.mutate({ expenseId: item.expense.id })
              onConfirmAction?.(item)
            }}
            isConfirming={confirmMutation.isPending}
            isRejecting={rejectMutation.isPending}
          />
        ))}
      </div>
    </div>
  )
}

interface PendingConfirmationCardProps {
  item: PendingConfirmation
  onConfirm: () => void
  onReject: () => void
  isConfirming: boolean
  isRejecting: boolean
}

function PendingConfirmationCard({
  item,
  onConfirm,
  onReject,
  isConfirming,
  isRejecting,
}: PendingConfirmationCardProps) {
  const { expense, split } = item
  const isProcessing = isConfirming || isRejecting

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{expense.description}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Amount owed and total */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Your share</p>
            <BalanceDisplay
              amount={split.amount_owed}
              variant="title"
            />
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Total expense</p>
            <p className="text-lg font-semibold">${expense.amount.toFixed(2)}</p>
          </div>
        </div>

        {/* Status badge */}
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
            Pending your confirmation
          </span>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <Button
            variant="default"
            className="flex-1"
            onClick={onConfirm}
            disabled={isProcessing}
          >
            <Check className="mr-2 h-4 w-4" />
            {isConfirming ? "Confirming..." : "Confirm"}
          </Button>
          <Button
            variant="destructive"
            className="flex-1"
            onClick={onReject}
            disabled={isProcessing}
          >
            <X className="mr-2 h-4 w-4" />
            {isRejecting ? "Rejecting..." : "Reject"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function PendingConfirmationsSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-4">
            <Skeleton className="h-6 w-3/4" />
            <div className="flex justify-between">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-24" />
            </div>
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
