import { Link } from "@tanstack/react-router"
import { Check, Edit2 } from "lucide-react"
import { BalanceDisplay } from "@/components/ui/balance-display"
import { SwipeableCard } from "@/components/ui/swipeable-card"
import { useDashboard } from "../api/dashboard"
import type { GroupBalanceSummary } from "../types"

export function Dashboard() {
  const { data, isLoading, error, refetch } = useDashboard()

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {/* Total Balance skeleton */}
        <div className="bg-surface-elevated border border-border rounded-md p-6 shadow-sm">
          <div className="h-4 bg-border rounded w-24 mb-2" />
          <div className="h-8 bg-border rounded w-32 mb-1" />
          <div className="h-3 bg-border rounded w-20" />
        </div>
        {/* Group cards skeleton */}
        <div className="h-5 bg-border rounded w-28" />
        <div className="h-20 bg-surface border border-border rounded" />
        <div className="h-20 bg-surface border border-border rounded" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-surface border border-border rounded-md">
        <p className="text-primary mb-3">
          Failed to load dashboard: {error.message}
        </p>
        <button
          type="button"
          onClick={() => refetch()}
          className="px-4 py-2 bg-action text-background rounded hover:opacity-90 transition-opacity"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (!data?.groups.length) {
    return (
      <div className="text-center py-8 bg-surface border border-border rounded-md">
        <h2 className="text-title font-medium text-primary mb-2">
          No groups yet
        </h2>
        <p className="text-secondary mb-4">
          Create a group to start tracking expenses with friends
        </p>
        <Link
          to="/groups"
          className="inline-block px-4 py-2 bg-action text-background rounded hover:opacity-90 transition-opacity"
        >
          Create Group
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Total Balance Header */}
      <div className="bg-surface-elevated border border-border rounded-md p-6 shadow-sm">
        <h1 className="text-heading font-medium text-secondary mb-2">
          Total Balance
        </h1>
        <BalanceDisplay
          amount={data.total_balance}
          variant="display"
          contextLabel={`Across ${data.count} group${data.count !== 1 ? "s" : ""}`}
          contextDescription="Your net balance across all expense groups"
        />
      </div>

      {/* Groups List */}
      <div className="space-y-3">
        <h2 className="text-heading font-medium text-primary">Your Groups</h2>
        {data.groups.map((group) => (
          <GroupCard key={group.group_id} group={group} />
        ))}
      </div>
    </div>
  )
}

interface GroupCardProps {
  group: GroupBalanceSummary
}

function GroupCard({ group }: GroupCardProps) {
  // TODO: Update to `/groups/${group.group_id}` when group detail route is implemented
  return (
    <SwipeableCard
      leftAction={{
        icon: Edit2,
        label: "Edit group",
        onTrigger: () => {
          // TODO: Implement edit group functionality (Epic 3)
        },
      }}
      rightAction={{
        icon: Check,
        label: "Settle up",
        onTrigger: () => {
          // TODO: Implement settle up functionality (Epic 3)
        },
      }}
      ariaLabel={`Group ${group.group_name}`}
    >
      <Link to="/groups" className="block">
        <div className="flex justify-between items-center">
          <div className="min-w-0 flex-1 mr-4">
            <h3 className="text-heading font-medium text-primary truncate">
              {group.group_name}
            </h3>
            <p className="text-body-small text-secondary">
              {group.member_count} member{group.member_count !== 1 ? "s" : ""}{" "}
              &bull; {formatLastActivity(group.last_activity)}
            </p>
          </div>
          <div className="flex-shrink-0">
            <BalanceDisplay
              amount={group.net_balance}
              variant="title"
              contextLabel={group.net_balance < 0 ? "You owe" : "You're owed"}
              contextDescription={`in ${group.group_name}`}
            />
          </div>
        </div>
      </Link>
    </SwipeableCard>
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
