import { Link } from "@tanstack/react-router"

import { useDashboard } from "../api/dashboard"
import type { GroupBalanceSummary } from "../types"

export function Dashboard() {
  const { data, isLoading, error, refetch } = useDashboard()

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {/* Total Balance skeleton */}
        <div className="bg-gray-200 dark:bg-gray-700 rounded-lg p-6">
          <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-24 mb-2"></div>
          <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-32 mb-1"></div>
          <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-20"></div>
        </div>
        {/* Group cards skeleton */}
        <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-28"></div>
        <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-600 dark:text-red-400 p-4 bg-red-50 dark:bg-red-900/20 rounded">
        <p className="mb-3">Failed to load dashboard: {error.message}</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (!data?.groups.length) {
    return (
      <div className="text-center py-8">
        <h2 className="text-xl font-semibold text-gray-600 dark:text-gray-300 mb-2">
          No groups yet
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-4">
          Create a group to start tracking expenses with friends
        </p>
        <Link
          to="/groups"
          className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Create Group
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Total Balance Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h1 className="text-lg font-medium text-gray-500 dark:text-gray-400">Total Balance</h1>
        <p className={`text-3xl font-bold ${getBalanceColor(data.total_balance)}`}>
          {formatBalance(data.total_balance)}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Across {data.count} group{data.count !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Groups List */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Your Groups</h2>
        {data.groups.map((group) => (
          <GroupCard key={group.group_id} group={group} />
        ))}
      </div>
    </div>
  )
}

function GroupCard({ group }: { group: GroupBalanceSummary }) {
  // TODO: Update to `/groups/${group.group_id}` when group detail route is implemented
  return (
    <Link
      to="/groups"
      className="block bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex justify-between items-center">
        <div className="min-w-0 flex-1 mr-4">
          <h3 className="font-medium truncate">{group.group_name}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {group.member_count} member{group.member_count !== 1 ? "s" : ""} &bull;{" "}
            {formatLastActivity(group.last_activity)}
          </p>
        </div>
        <div className={`text-lg font-semibold flex-shrink-0 ${getBalanceColor(group.net_balance)}`}>
          {formatBalance(group.net_balance)}
        </div>
      </div>
    </Link>
  )
}

function getBalanceColor(balance: number): string {
  if (balance > 0) return "text-green-600 dark:text-green-400"
  if (balance < 0) return "text-red-600 dark:text-red-400"
  return "text-gray-500 dark:text-gray-400"
}

function formatBalance(balance: number): string {
  // Use Intl.NumberFormat for locale-aware currency formatting
  // TODO: Make currency configurable via user settings or app config
  const formatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  const sign = balance > 0 ? "+" : ""
  return `${sign}${formatter.format(Math.abs(balance))}`
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
