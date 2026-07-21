import {
  Plus,
  Pencil,
  Check,
  X,
  Banknote,
  PieChart,
} from "lucide-react"
import { type ElementType, useState } from "react"

import { useCurrency } from "@/lib/currency-context"
import type { AuditActionType, AuditLog } from "../types"
import {
  formatActivityEntry,
  getActionColor,
  getUserInitials,
} from "../utils/activityFormatters"
import { formatRelativeTime } from "../utils/timeFormat"

const ACTION_ICONS: Record<AuditActionType, ElementType> = {
  created: Plus,
  edited: Pencil,
  confirmed: Check,
  rejected: X,
  settled: Banknote,
  split_updated: PieChart,
}

interface ActivityFeedItemProps {
  log: AuditLog
  showGroupName?: string
}

export function ActivityFeedItem({
  log,
  showGroupName,
}: ActivityFeedItemProps) {
  const [isHovered, setIsHovered] = useState(false)
  const currency = useCurrency()
  const Icon = ACTION_ICONS[log.action_type] || Plus
  const colorClass = getActionColor(log.action_type)
  const initials = getUserInitials(log.user_name)
  const description = formatActivityEntry(log, currency)

  return (
    <div
      className="animate-in fade-in-0 duration-150 flex items-start gap-3 py-3"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Avatar */}
      <div className="relative flex-shrink-0">
        <div className="flex size-9 items-center justify-center rounded-full bg-muted text-xs font-semibold text-muted-foreground">
          {initials}
        </div>
        <div
          className={`absolute -bottom-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full bg-surface ${colorClass}`}
        >
          <Icon className="size-2.5" strokeWidth={2.5} />
        </div>
      </div>

      {/* Content bubble */}
      <div className="min-w-0 flex-1">
        <div className="rounded-xl rounded-tl-sm bg-surface border border-border px-3.5 py-2.5">
          <p className="text-sm text-foreground leading-relaxed">
            {description}
          </p>
          {showGroupName && (
            <p className="mt-1 text-xs text-muted-foreground">
              in {showGroupName}
            </p>
          )}
        </div>
        <p
          className="mt-1 pl-1 text-xs text-muted-foreground"
          title={new Date(log.created_at).toLocaleString()}
        >
          {isHovered
            ? new Date(log.created_at).toLocaleString()
            : formatRelativeTime(log.created_at)}
        </p>
      </div>
    </div>
  )
}
