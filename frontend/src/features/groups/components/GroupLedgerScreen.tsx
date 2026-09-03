import { Link } from "@tanstack/react-router"
import { ArrowLeft, Banknote, ChevronDown, ChevronUp, Plus } from "lucide-react"
import { useRef, useState } from "react"

import { BalanceDisplay } from "@/components/ui/balance-display"
import { Button } from "@/components/ui/button"
import { formatCurrency } from "@/lib/currency"
import { CurrencyProvider, useCurrency } from "@/lib/currency-context"
import {
  useAggregateClaims,
  useExpenseAuditLog,
  useExpenseSplits,
  useGroupExpenses,
  usePendingSettlements,
} from "@/features/expenses/api/expenses"
import { ActivityFeed } from "@/features/expenses/components/ActivityFeed"
import { AggregateClaimCard } from "@/features/expenses/components/AggregateClaimCard"
import { AuditLogList } from "@/features/expenses/components/AuditLogList"
import { ConfirmedExpenseCard } from "@/features/expenses/components/ConfirmedExpenseCard"
import { PendingSettlementsList } from "@/features/expenses/components/PendingSettlementsList"
import { SettlementClaimsList } from "@/features/expenses/components/SettlementClaimsList"
import { SmartInputModal } from "@/features/expenses/components/SmartInputModal"
import type { ExpenseStatus, GroupExpenseItem } from "@/features/expenses/types"
import { useAuth } from "@/hooks/useAuth"

import { useGroupDetail, useGroupMembers } from "../api/groups"
import { GenerateInviteButton } from "./GenerateInviteButton"
import { GroupSettingsPanel } from "./GroupSettingsPanel"
import { MembersList } from "./MembersList"
import { PairwiseBalances } from "./PairwiseBalances"

interface Props {
  groupId: string
}

/**
 * The group ledger screen (WS5/S4-C4) — backing component for
 * /groups/$groupId. Everything is derived from the query cache (S4-H3), so
 * refetches and mutations update the screen instead of a stale snapshot.
 *
 * Sections: balance header, expense ledger (expandable rows with splits +
 * audit trail), ready-to-settle cards (Story 5.1), claims awaiting the
 * owner's review (Story 5.2, group-scoped per S4-M6), the user's own
 * pending claims, and members.
 */
export function GroupLedgerScreen({ groupId }: Props) {
  const { user } = useAuth()
  const { data: group, isLoading, error } = useGroupDetail(groupId)
  const { data: ledger } = useGroupExpenses(groupId)
  const { data: myPendingClaims } = usePendingSettlements()
  const { data: membersData } = useGroupMembers(groupId)
  const { data: aggregateClaims } = useAggregateClaims(groupId)

  const [isAddExpenseOpen, setIsAddExpenseOpen] = useState(false)
  const addExpenseRef = useRef<HTMLButtonElement>(
    null as HTMLButtonElement | null,
  )

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6" aria-hidden="true">
        <div className="h-4 w-24 rounded bg-border" />
        <div className="h-8 w-48 rounded bg-border" />
        <div className="border-y border-border divide-y divide-border">
          <div className="h-16" />
          <div className="h-16" />
          <div className="h-16" />
        </div>
      </div>
    )
  }

  if (error || !group) {
    return (
      <div className="space-y-4 py-8 text-center">
        <p className="text-body text-text-primary">
          This group couldn't be loaded.
        </p>
        <p className="text-body-small text-text-secondary">
          It may not exist, or you may not be a member.
        </p>
        <Button variant="outline" asChild>
          <Link to="/groups">Back to groups</Link>
        </Button>
      </div>
    )
  }

  const memberNameById = new Map(
    (membersData?.members ?? []).map((m) => [
      m.user_id,
      m.full_name || m.email,
    ]),
  )

  const items = ledger?.data ?? []

  // Aggregate settle-ups (WS6), split by which side of them the user is on
  const settleUps = aggregateClaims?.data ?? []
  const settleUpsForMyReview = settleUps.filter(
    (claim) => claim.counterparty_user_id === user?.id,
  )
  const mySettleUps = settleUps.filter(
    (claim) => claim.claimant_user_id === user?.id,
  )
  const pendingCounterpartyIds = new Set(
    mySettleUps
      .map((claim) => claim.counterparty_user_id)
      .filter((id): id is string => id !== null),
  )

  // Confirmed expenses where the user still owes their share and hasn't
  // already claimed payment — the "Mark Paid" path (Story 5.1). Expenses
  // covered by a pending settle-up with their payer are spoken for (WS6):
  // Mark Paid would always 409, so don't offer it.
  const claimedExpenseIds = new Set(
    (myPendingClaims ?? []).map((item) => item.expense.id),
  )
  const readyToSettle = items.filter(
    ({ expense, my_split }) =>
      expense.status === "confirmed" &&
      my_split?.status === "confirmed" &&
      expense.payer_id !== user?.id &&
      !claimedExpenseIds.has(expense.id) &&
      !pendingCounterpartyIds.has(expense.payer_id),
  )

  const myGroupClaims = (myPendingClaims ?? []).filter(
    (item) => item.expense.group_id === groupId,
  )

  const isOwner = (membersData?.members ?? []).some(
    (m) => m.user_id === user?.id && m.role === "owner",
  )

  const netBalance = Number(group.net_balance)

  // Light pending-vs-confirmed affordance (audit F11): balances only count
  // CONFIRMED expenses, so a freshly-added split shows no balance movement.
  // Surface what's still awaiting confirmation — derivable from the ledger
  // alone: for an expense I paid, others will owe me (amount − my share); for
  // one I didn't, I'll owe my share once I confirm.
  const pending = items.reduce(
    (acc, { expense, my_split }) => {
      if (expense.status !== "pending_confirmation") return acc
      const myShare = my_split ? Number(my_split.amount_owed) : 0
      if (expense.payer_id === user?.id) {
        acc.net += Number(expense.amount) - myShare
        acc.count += 1
      } else if (my_split && my_split.status === "pending") {
        acc.net -= myShare
        acc.count += 1
      }
      return acc
    },
    { net: 0, count: 0 },
  )
  const pendingNoun = pending.count === 1 ? "expense" : "expenses"
  const pendingLabel =
    pending.count === 0
      ? null
      : Math.abs(pending.net) < 0.005
        ? `${pending.count} pending ${pendingNoun} awaiting confirmation`
        : pending.net > 0
          ? `+${formatCurrency(pending.net, group.currency)} once ${pending.count} pending ${pendingNoun} confirm`
          : `−${formatCurrency(Math.abs(pending.net), group.currency)} once ${pending.count} pending ${pendingNoun} confirm`

  return (
    <CurrencyProvider currency={group.currency}>
    <div className="space-y-8">
      {/* Header */}
      <header className="space-y-4">
        <Link
          to="/groups"
          className="inline-flex items-center gap-1 text-body-small text-text-secondary hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          All groups
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-title font-semibold tracking-tight truncate">
              {group.name}
            </h1>
            <p className="text-body-small text-text-secondary">
              {group.member_count} member{group.member_count !== 1 ? "s" : ""}{" "}
              &bull; created {new Date(group.created_at).toLocaleDateString()}
            </p>
          </div>
          <GenerateInviteButton groupId={groupId} />
        </div>

        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-1">
              Your balance
            </p>
            <BalanceDisplay
              amount={netBalance}
              variant="display"
              contextLabel={netBalance < 0 ? "You owe" : "You're owed"}
              contextDescription={`in ${group.name}`}
            />
            {pendingLabel && (
              <p className="mt-1.5 text-caption text-text-muted tabular-nums">
                {pendingLabel}
              </p>
            )}
          </div>
          <Button ref={addExpenseRef} onClick={() => setIsAddExpenseOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add expense
          </Button>
        </div>
      </header>

      {/* Who owes whom exactly (WS6/S2-F9) — the settle-up entry point */}
      <section aria-label="Balances with members" className="space-y-2">
        <h2 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted">
          Between you and…
        </h2>
        <PairwiseBalances
          groupId={groupId}
          pendingCounterpartyIds={pendingCounterpartyIds}
        />
      </section>

      {/* Ready to settle — confirmed shares the user can mark as paid */}
      {readyToSettle.length > 0 && (
        <section aria-label="Ready to settle" className="space-y-3">
          <h2 className="flex items-center gap-2 text-caption font-medium uppercase tracking-[0.06em] text-text-muted">
            <Banknote className="h-4 w-4" />
            Ready to settle
          </h2>
          {readyToSettle.map(({ expense, my_split }) => (
            <ConfirmedExpenseCard
              key={expense.id}
              expense={expense}
              split={my_split!}
              ownerName={memberNameById.get(expense.payer_id) ?? null}
            />
          ))}
        </section>
      )}

      {/* Expense ledger */}
      <section aria-label="Expenses">
        <h2 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-2">
          Expenses
        </h2>
        {items.length === 0 ? (
          <div className="border-y border-border py-10 text-center">
            <p className="text-body text-text-primary">No expenses yet</p>
            <p className="text-body-small text-text-secondary mt-1">
              Add the first expense — ClearDues keeps score from there.
            </p>
          </div>
        ) : (
          <ul className="border-y border-border divide-y divide-border">
            {items.map((item) => (
              <ExpenseRow
                key={item.expense.id}
                item={item}
                payerName={memberNameById.get(item.expense.payer_id) ?? null}
              />
            ))}
          </ul>
        )}
      </section>

      {/* Claims awaiting the owner's confirmation (Story 5.2 + WS6
          settle-ups) */}
      <section aria-label="Settlement claims" className="space-y-3">
        <h2 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted">
          Awaiting your review
        </h2>
        {settleUpsForMyReview.map((claim) => (
          <AggregateClaimCard
            key={claim.id}
            claim={claim}
            currentUserId={user?.id ?? ""}
          />
        ))}
        <SettlementClaimsList
          groupId={groupId}
          suppressEmptyState={settleUpsForMyReview.length > 0}
        />
      </section>

      {/* The user's own claims awaiting the owner (Story 5.1 + WS6
          settle-ups) */}
      {(myGroupClaims.length > 0 || mySettleUps.length > 0) && (
        <section aria-label="Your pending claims" className="space-y-3">
          <h2 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted">
            Your pending claims
          </h2>
          {mySettleUps.map((claim) => (
            <AggregateClaimCard
              key={claim.id}
              claim={claim}
              currentUserId={user?.id ?? ""}
            />
          ))}
          {myGroupClaims.length > 0 && (
            <PendingSettlementsList groupId={groupId} />
          )}
        </section>
      )}

      {/* Members */}
      <section aria-label="Members" className="border-t border-border pt-4">
        <MembersList groupId={groupId} />
      </section>

      {/* Group settings (WS6 — the confirmation social contract) */}
      <section
        aria-label="Group settings"
        className="border-t border-border pt-4"
      >
        <h2 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-2">
          Settings
        </h2>
        <GroupSettingsPanel groupId={groupId} isOwner={isOwner} />
      </section>

      {/* Group-level activity feed (was on the old detail panel) */}
      <section aria-label="Recent activity" className="border-t border-border pt-4">
        <ActivityFeed groupId={groupId} title="Recent Activity" />
      </section>

      {/* Per-group expense entry (WS5/S4-C1) */}
      <SmartInputModal
        open={isAddExpenseOpen}
        onOpenChange={setIsAddExpenseOpen}
        groupId={groupId}
        entryPoint="group"
        triggerRef={addExpenseRef}
      />
    </div>
    </CurrencyProvider>
  )
}

// =============================================================================
// Expense row — expandable ledger line
// =============================================================================

const STATUS_LABELS: Record<ExpenseStatus, string> = {
  draft: "Draft",
  pending_confirmation: "Awaiting confirmations",
  confirmed: "Confirmed",
  settled: "Settled",
}

const STATUS_CLASSES: Record<ExpenseStatus, string> = {
  draft: "bg-muted text-muted-foreground",
  pending_confirmation:
    "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200",
  confirmed:
    "bg-success-subtle text-green-800 dark:bg-green-900/30 dark:text-green-200",
  settled: "bg-muted text-muted-foreground",
}

interface ExpenseRowProps {
  item: GroupExpenseItem
  payerName: string | null
}

function ExpenseRow({ item, payerName }: ExpenseRowProps) {
  const { expense, my_split } = item
  const currency = useCurrency()
  const [expanded, setExpanded] = useState(false)

  // Fetched lazily on expand: who owes what + the expense's audit trail
  const { data: splits } = useExpenseSplits(expense.id, expanded)
  const { data: auditLog } = useExpenseAuditLog(
    expanded ? expense.id : undefined,
  )

  return (
    <li>
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        className="flex w-full min-h-14 items-center justify-between gap-4 py-3 text-left hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
      >
        <div className="min-w-0 flex-1">
          <p className="text-body font-medium text-text-primary truncate">
            {expense.description}
          </p>
          <p className="text-body-small text-text-secondary">
            {payerName ? `Paid by ${payerName}` : " "} &bull;{" "}
            {new Date(expense.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASSES[expense.status]}`}
          >
            {STATUS_LABELS[expense.status]}
          </span>
          <div className="text-right">
            <p className="text-body font-semibold tabular-nums text-text-primary">
              {formatCurrency(expense.amount, currency)}
            </p>
            {my_split && (
              <p className="text-body-small tabular-nums text-text-secondary">
                Your share: {formatCurrency(my_split.amount_owed, currency)}
              </p>
            )}
          </div>
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-text-muted" />
          ) : (
            <ChevronDown className="h-4 w-4 text-text-muted" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="space-y-4 pb-4 pl-1">
          {/* Who owes what */}
          <div>
            <h3 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-1">
              Split
            </h3>
            {!splits ? (
              <p className="text-body-small text-text-secondary">
                Loading split…
              </p>
            ) : splits.count === 0 ? (
              <p className="text-body-small text-text-secondary">
                Not split yet — the creator still needs to assign shares.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {splits.data.map((split) => (
                  <li
                    key={split.id}
                    className="flex items-center justify-between py-2"
                  >
                    <span className="text-body-small text-text-primary">
                      {split.user_name}
                    </span>
                    <span className="text-body-small tabular-nums text-text-secondary">
                      {formatCurrency(split.amount_owed, currency)} &bull;{" "}
                      {split.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Immutable audit trail (Story 4.4 — AuditLogList mount, S4-C4) */}
          <div>
            <h3 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-1">
              History
            </h3>
            <AuditLogList
              logs={auditLog?.data ?? []}
              totalCount={auditLog?.count ?? 0}
            />
          </div>
        </div>
      )}
    </li>
  )
}
