/** Future-facing counterpart of formatRelativeTime (WS6 — dispute-window
 * countdowns like "in 2 days"). Past or imminent dates read as "soon". */
export function formatTimeUntil(dateStr: string): string {
  const diffMs = new Date(dateStr).getTime() - Date.now()
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffMin < 1) return "soon"
  if (diffMin < 60) return `in ${diffMin}m`
  if (diffHour < 24) return `in ${diffHour}h`
  return `in ${diffDay} day${diffDay === 1 ? "" : "s"}`
}

export function formatRelativeTime(dateStr: string): string {
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
