import { createFileRoute } from "@tanstack/react-router"
import { Activity } from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"

import { useUserGroups } from "@/features/groups/api/groups"
import { useGroupAuditLog } from "@/features/expenses/api/expenses"
import type { AuditLog } from "@/features/expenses/types"
import { ActivityFeedItem } from "@/features/expenses/components/ActivityFeedItem"

export const Route = createFileRoute("/_layout/activity")({
  component: ActivityPage,
})

const PAGE_SIZE = 20

interface LogWithGroup extends AuditLog {
  group_name?: string
}

function ActivityPage() {
  const { data: groups, isLoading: groupsLoading } = useUserGroups()

  if (groupsLoading) {
    return (
      <div className="flex flex-col gap-6">
        <PageHeader />
        <LoadingSkeleton />
      </div>
    )
  }

  if (!groups?.length) {
    return (
      <div className="flex flex-col gap-6">
        <PageHeader />
        <EmptyState type="no-groups" />
      </div>
    )
  }

  return <CombinedActivityFeed groups={groups} />
}

function CombinedActivityFeed({
  groups,
}: {
  groups: { id: string; name: string }[]
}) {
  const [allLogs, setAllLogs] = useState<LogWithGroup[]>([])
  const [loadedGroupIds, setLoadedGroupIds] = useState<Set<string>>(new Set())
  const [displayCount, setDisplayCount] = useState(PAGE_SIZE)
  const groupIdsKey = groups.map((g) => g.id).join(",")

  const handleGroupLogs = useCallback(
    (groupId: string, logs: LogWithGroup[]) => {
      setAllLogs((prev) => {
        const existingIds = new Set(prev.map((l) => l.id))
        const unique = logs.filter((l) => !existingIds.has(l.id))
        const merged = [...prev, ...unique]
        merged.sort(
          (a, b) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime()
        )
        return merged
      })
      setLoadedGroupIds((prev) => new Set(prev).add(groupId))
    },
    []
  )

  // Reset on group list change
  const prevGroupIdsRef = useRef(groupIdsKey)
  useEffect(() => {
    if (prevGroupIdsRef.current !== groupIdsKey) {
      setAllLogs([])
      setLoadedGroupIds(new Set())
      setDisplayCount(PAGE_SIZE)
      prevGroupIdsRef.current = groupIdsKey
    }
  }, [groupIdsKey])

  const isLoading = loadedGroupIds.size < groups.length
  const visibleLogs = allLogs.slice(0, displayCount)
  const hasMore = displayCount < allLogs.length

  return (
    <div className="flex flex-col gap-6">
      <PageHeader />
      <div className="relative">
        {groups.map((group) => (
          <GroupLogLoader
            key={group.id}
            groupId={group.id}
            groupName={group.name}
            onLogsLoaded={handleGroupLogs}
          />
        ))}

        {isLoading && allLogs.length === 0 ? (
          <LoadingSkeleton />
        ) : allLogs.length === 0 ? (
          <EmptyState type="no-activity" />
        ) : (
          <>
            <div className="divide-y divide-border">
              {visibleLogs.map((log) => (
                <ActivityFeedItem
                  key={log.id}
                  log={log}
                  showGroupName={log.group_name}
                />
              ))}
            </div>
            {hasMore && (
              <div className="flex justify-center pt-4">
                <button
                  onClick={() => setDisplayCount((c) => c + PAGE_SIZE)}
                  className="rounded-md px-4 py-2 text-sm text-primary hover:bg-accent transition-colors"
                >
                  Load more
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function GroupLogLoader({
  groupId,
  groupName,
  onLogsLoaded,
}: {
  groupId: string
  groupName: string
  onLogsLoaded: (groupId: string, logs: LogWithGroup[]) => void
}) {
  const { data } = useGroupAuditLog(groupId, PAGE_SIZE, 0)

  useEffect(() => {
    if (!data?.data) return
    const withGroup: LogWithGroup[] = data.data.map((log) => ({
      ...log,
      group_name: groupName,
    }))
    onLogsLoaded(groupId, withGroup)
  }, [data, groupName, groupId, onLogsLoaded])

  return null
}

function PageHeader() {
  return (
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-foreground">
        Activity Feed
      </h1>
      <p className="text-muted-foreground">
        Recent activity across your expense groups
      </p>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-start gap-3">
          <div className="size-9 rounded-full bg-muted" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-muted rounded w-3/4" />
            <div className="h-3 bg-muted rounded w-1/4" />
          </div>
        </div>
      ))}
    </div>
  )
}

function EmptyState({ type }: { type: "no-groups" | "no-activity" }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center rounded-lg border border-border bg-surface">
      <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-muted">
        <Activity className="size-6 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold text-foreground">
        {type === "no-groups" ? "No groups yet" : "No activity yet"}
      </h3>
      <p className="text-sm text-muted-foreground">
        {type === "no-groups"
          ? "Join or create a group to see activity here"
          : "Actions will appear here as they happen in your groups"}
      </p>
    </div>
  )
}

export default ActivityPage
