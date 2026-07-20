import { useState } from "react"

import { Button } from "@/components/ui/button"
import { useSettleUp } from "@/features/expenses/api/expenses"
import { formatCurrency } from "@/lib/currency"
import { useCurrency } from "@/lib/currency-context"

import { usePairwiseBalances } from "../api/groups"

interface Props {
  groupId: string
  /** Counterparty user ids that already have a pending settle-up with the
   * current user — their rows show the in-flight state instead of a button */
  pendingCounterpartyIds: Set<string>
}

/**
 * "Who owes whom, exactly" (WS6/S2-F9): one hairline row per counterparty
 * with the net between them and the current user, and the "Settle up"
 * action when the user owes — the entry point for aggregate settle-up.
 *
 * Settle up is a two-step inline confirm (no timers, no auto-anything —
 * product constitution: manual confirm only).
 */
export function PairwiseBalances({ groupId, pendingCounterpartyIds }: Props) {
  const { data, isLoading, error } = usePairwiseBalances(groupId)
  const currency = useCurrency()
  const settleUp = useSettleUp(currency)
  const [confirmingId, setConfirmingId] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2" aria-hidden="true">
        <div className="h-12 rounded bg-border" />
        <div className="h-12 rounded bg-border" />
      </div>
    )
  }

  if (error) {
    return (
      <p className="text-body-small text-text-secondary">
        Balances couldn't be loaded. Pull to refresh or try again shortly.
      </p>
    )
  }

  const items = data?.data ?? []

  if (items.length === 0) {
    return (
      <p className="border-y border-border py-6 text-center text-body-small text-text-secondary">
        Nothing outstanding between you and anyone here.
      </p>
    )
  }

  const handleSettleUp = (counterpartyId: string) => {
    settleUp.mutate(
      { group_id: groupId, counterparty_user_id: counterpartyId },
      { onSettled: () => setConfirmingId(null) },
    )
  }

  return (
    <ul className="border-y border-border divide-y divide-border">
      {items.map((item) => {
        const net = Number(item.net)
        const userOwes = net < 0
        const name = item.user_name ?? "A member"
        const hasPendingSettleUp = pendingCounterpartyIds.has(item.user_id)
        const isConfirming = confirmingId === item.user_id

        return (
          <li
            key={item.user_id}
            className="flex min-h-14 flex-wrap items-center justify-between gap-x-4 gap-y-2 py-3"
          >
            <div className="min-w-0">
              <p className="text-body font-medium text-text-primary truncate">
                {name}
              </p>
              <p className="text-body-small tabular-nums text-text-secondary">
                {net === 0
                  ? "You're even — settle up to clear the ledger"
                  : userOwes
                    ? `You owe ${formatCurrency(item.you_owe_them, currency)}${
                        Number(item.they_owe_you) > 0
                          ? ` · they owe ${formatCurrency(item.they_owe_you, currency)}`
                          : ""
                      }`
                    : `Owes you ${formatCurrency(item.they_owe_you, currency)}${
                        Number(item.you_owe_them) > 0
                          ? ` · you owe ${formatCurrency(item.you_owe_them, currency)}`
                          : ""
                      }`}
              </p>
            </div>

            {net > 0 ? (
              <span className="text-body font-semibold tabular-nums text-text-primary">
                {formatCurrency(item.net, currency)}
              </span>
            ) : hasPendingSettleUp ? (
              <span className="text-body-small text-text-secondary">
                Settle-up pending
              </span>
            ) : isConfirming ? (
              <div className="flex items-center gap-2">
                <span className="text-body-small text-text-secondary">
                  Paid {name} {formatCurrency(Math.abs(net), currency)}?
                </span>
                <Button
                  size="sm"
                  onClick={() => handleSettleUp(item.user_id)}
                  disabled={settleUp.isPending}
                >
                  Yes, I paid
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setConfirmingId(null)}
                  disabled={settleUp.isPending}
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setConfirmingId(item.user_id)}
                aria-label={`Settle up with ${name}`}
              >
                Settle up
              </Button>
            )}
          </li>
        )
      })}
    </ul>
  )
}
