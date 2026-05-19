import { useState } from "react"

import type { AuditLog, AuditActionType } from "../types"

const ACTION_LABELS: Record<AuditActionType, string> = {
  created: "created",
  edited: "edited",
  confirmed: "confirmed",
  rejected: "rejected",
  settled: "settled",
  split_updated: "updated the split for",
}

function formatRelativeTime(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diffMs = now - then
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) return "just now"
  if (diffMin < 60) return `${diffMin}m ago`
  if (diffHour < 24) return `${diffHour}h ago`
  if (diffDay < 7) return `${diffDay}d ago`
  return new Date(dateStr).toLocaleDateString()
}

interface AuditLogListProps {
  logs: AuditLog[]
  totalCount: number
  onLoadMore?: () => void
  isLoadingMore?: boolean
}

export function AuditLogList({
  logs,
  totalCount,
  onLoadMore,
  isLoadingMore,
}: AuditLogListProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  if (!logs.length) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        No activity recorded yet.
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {logs.map((log) => (
        <div
          key={log.id}
          className="flex items-start gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-muted/50"
          onMouseEnter={() => setHoveredId(log.id)}
          onMouseLeave={() => setHoveredId(null)}
        >
          <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary/60" />

          <div className="min-w-0 flex-1">
            <p className="text-sm">
              <span className="font-medium text-foreground">
                {log.user_name || "Unknown user"}
              </span>{" "}
              <span className="text-muted-foreground">
                {ACTION_LABELS[log.action_type]}
              </span>{" "}
              <span className="text-muted-foreground">
                expense
                {log.changes_json?.after?.description
                  ? ` "${log.changes_json.after.description as string}"`
                  : log.changes_json?.after?.amount
                    ? ` for Rs ${log.changes_json.after.amount as string}`
                    : ""}
              </span>
            </p>

            {log.changes_json?.before && log.changes_json.after && (
              <div className="mt-1 text-xs text-muted-foreground">
                {Object.keys(log.changes_json.after).map((field) => {
                  const before = log.changes_json!.before?.[field]
                  const after = log.changes_json!.after?.[field]
                  if (before !== after && before !== undefined) {
                    return (
                      <span key={field} className="mr-2">
                        {field}:{" "}
                        <span className="line-through">{String(before)}</span>{" "}
                        → <span className="text-foreground">{String(after)}</span>
                      </span>
                    )
                  }
                  return null
                })}
              </div>
            )}

            <p
              className="mt-0.5 text-xs text-muted-foreground"
              title={new Date(log.created_at).toLocaleString()}
            >
              {hoveredId === log.id
                ? new Date(log.created_at).toLocaleString()
                : formatRelativeTime(log.created_at)}
            </p>
          </div>
        </div>
      ))}

      {logs.length < totalCount && onLoadMore && (
        <div className="flex justify-center pt-2">
          <button
            onClick={onLoadMore}
            disabled={isLoadingMore}
            className="rounded-md px-4 py-2 text-sm text-primary hover:bg-muted disabled:opacity-50"
          >
            {isLoadingMore ? "Loading..." : "Load more"}
          </button>
        </div>
      )}
    </div>
  )
}
