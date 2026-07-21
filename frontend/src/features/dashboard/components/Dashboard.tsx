import { Link } from "@tanstack/react-router"

import { BalanceDisplay } from "@/components/ui/balance-display"
import { Button } from "@/components/ui/button"
import { useDashboard } from "../api/dashboard"
import type { GroupBalanceSummary } from "../types"

export function Dashboard() {
  const { data, isLoading, error, refetch } = useDashboard()

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6" aria-hidden="true">
        {/* Balance hero skeleton */}
        <div className="space-y-2 pt-2">
          <div className="h-3 w-28 rounded bg-border" />
          <div className="h-8 w-40 rounded bg-border" />
          <div className="h-3 w-24 rounded bg-border" />
        </div>
        {/* Ledger row skeletons */}
        <div className="border-y border-border divide-y divide-border">
          <div className="h-16" />
          <div className="h-16" />
          <div className="h-16" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4 py-8 text-center">
        <p className="text-body text-text-primary">
          Your balances didn't load.
        </p>
        <p className="text-body-small text-text-secondary">
          Check your connection and try again — nothing has been lost.
        </p>
        <Button variant="outline" onClick={() => refetch()}>
          Try again
        </Button>
      </div>
    )
  }

  if (!data?.groups.length) {
    return (
      <div className="space-y-4 py-12 text-center">
        <h2 className="text-title font-semibold text-text-primary">
          Nothing to keep score of yet
        </h2>
        <p className="text-body text-text-secondary">
          Start a group and add one expense — ClearDues takes it from there.
        </p>
        <Button asChild>
          <Link to="/groups">Start a group</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Balance hero — a single total only makes sense in one currency
          (WS10.1). When groups span currencies, the backend sends currency:
          null; we drop the aggregate and let the per-group rows carry it. */}
      <header className="pt-2">
        {data.currency ? (
          <>
            <p className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-1">
              Total balance
            </p>
            <BalanceDisplay
              amount={Number(data.total_balance)}
              variant="display"
              currency={data.currency}
              contextDescription="across all groups"
            />
            <p className="text-body-small text-text-secondary mt-1">
              Across {data.count} group{data.count !== 1 ? "s" : ""}
            </p>
          </>
        ) : (
          <>
            <p className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-1">
              Your balances
            </p>
            <p className="text-body text-text-primary">
              Your groups use different currencies — see each below.
            </p>
            <p className="text-body-small text-text-secondary mt-1">
              Across {data.count} group{data.count !== 1 ? "s" : ""}
            </p>
          </>
        )}
      </header>

      {/* Groups ledger */}
      <section aria-label="Your groups">
        <h2 className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted mb-2">
          Your groups
        </h2>
        <ul className="border-y border-border divide-y divide-border">
          {data.groups.map((group) => (
            <GroupRow key={group.group_id} group={group} />
          ))}
        </ul>
      </section>
    </div>
  )
}

interface GroupRowProps {
  group: GroupBalanceSummary
}

function GroupRow({ group }: GroupRowProps) {
  return (
    <li>
      <Link
        to="/groups/$groupId"
        params={{ groupId: group.group_id }}
        className="flex min-h-14 items-center justify-between gap-4 py-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset hover:bg-accent transition-colors"
        aria-label={`Group ${group.group_name}`}
      >
        <div className="min-w-0 flex-1">
          <h3 className="text-body font-semibold text-text-primary truncate">
            {group.group_name}
          </h3>
          <p className="text-body-small text-text-secondary">
            {group.member_count} member{group.member_count !== 1 ? "s" : ""}{" "}
            &bull; {formatLastActivity(group.last_activity)}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <BalanceDisplay
            amount={Number(group.net_balance)}
            variant="title"
            currency={group.currency}
            contextLabel={Number(group.net_balance) < 0 ? "You owe" : "You're owed"}
            contextDescription={`in ${group.group_name}`}
          />
        </div>
      </Link>
    </li>
  )
}

function formatLastActivity(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  // Handle future dates (e.g., clock skew, timezone issues)
  if (diffDays < 0) return "Just now"
  if (diffDays === 0) return "Today"
  if (diffDays === 1) return "Yesterday"
  if (diffDays < 7) return `${diffDays} days ago`
  return date.toLocaleDateString()
}
