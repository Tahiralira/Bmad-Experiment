import { Activity } from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"

import { useGroupAuditLog } from "../api/expenses"
import type { AuditLog } from "../types"
import { ActivityFeedItem } from "./ActivityFeedItem"

const PAGE_SIZE = 20

interface ActivityFeedProps {
  groupId: string
  title?: string
}

export function ActivityFeed({
  groupId,
  title = "Activity",
}: ActivityFeedProps) {
  const [allLogs, setAllLogs] = useState<AuditLog[]>([])
  const [currentOffset, setCurrentOffset] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const isFirstPage = currentOffset === 0

  const { data, isLoading, error } = useGroupAuditLog(
    groupId,
    PAGE_SIZE,
    currentOffset
  )

  const prevOffsetRef = useRef(0)

  // When new data arrives, merge it into the accumulated list
  useEffect(() => {
    if (!data?.data) return

    if (isFirstPage) {
      // First page: replace entirely
      setAllLogs(data.data)
    } else if (currentOffset !== prevOffsetRef.current) {
      // New page loaded: append
      setAllLogs((prev) => {
        const newIds = new Set(prev.map((l) => l.id))
        const unique = data.data.filter((l) => !newIds.has(l.id))
        return [...prev, ...unique]
      })
      prevOffsetRef.current = currentOffset
    }

    setTotalCount(data.count)
  }, [data, isFirstPage, currentOffset])

  // Reset on group change
  useEffect(() => {
    setAllLogs([])
    setCurrentOffset(0)
    setTotalCount(0)
    prevOffsetRef.current = 0
  }, [groupId])

  const hasMore = allLogs.length < totalCount

  const handleLoadMore = useCallback(() => {
    setCurrentOffset((prev) => prev + PAGE_SIZE)
  }, [])

  if (isLoading && allLogs.length === 0) {
    return (
      <div className="space-y-4">
        {title && (
          <h2 className="text-heading font-medium text-primary">{title}</h2>
        )}
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start gap-3">
              <div className="size-9 rounded-full bg-muted" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/4" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        {title && (
          <h2 className="text-heading font-medium text-primary">{title}</h2>
        )}
        <p className="text-sm text-destructive">
          Failed to load activity: {error.message}
        </p>
      </div>
    )
  }

  if (!allLogs.length) {
    return (
      <div className="space-y-4">
        {title && (
          <h2 className="text-heading font-medium text-primary">{title}</h2>
        )}
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-muted">
            <Activity className="size-6 text-muted-foreground" />
          </div>
          <h3 className="text-sm font-semibold text-foreground">
            No activity yet
          </h3>
          <p className="text-xs text-muted-foreground">
            Actions will appear here as they happen
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {title && (
        <h2 className="text-heading font-medium text-primary">{title}</h2>
      )}
      <div className="divide-y divide-border">
        {allLogs.map((log) => (
          <ActivityFeedItem key={log.id} log={log} />
        ))}
      </div>

      {hasMore && (
        <div className="flex justify-center pt-4">
          <button
            onClick={handleLoadMore}
            disabled={isLoading}
            className="rounded-md px-4 py-2 text-sm text-primary hover:bg-accent transition-colors disabled:opacity-50"
          >
            {isLoading ? "Loading..." : "Load more"}
          </button>
        </div>
      )}
    </div>
  )
}
