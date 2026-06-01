import type { AuditActionType, AuditLog } from "../types"

export function formatActivityEntry(log: AuditLog): string {
  const user = log.user_name || "Someone"

  switch (log.action_type) {
    case "created":
      return formatCreatedEntry(user, log)
    case "edited":
      return formatEditedEntry(user, log)
    case "confirmed":
      return `${user} confirmed their share`
    case "rejected":
      return formatRejectedEntry(user, log)
    case "settled":
      return formatSettledEntry(user, log)
    case "split_updated":
      return formatSplitUpdatedEntry(user, log)
    default:
      return `${user} performed an action`
  }
}

function formatCreatedEntry(user: string, log: AuditLog): string {
  const after = log.changes_json?.after
  const description = after?.description as string | undefined
  const amount = after?.amount as number | undefined

  if (description && amount != null) {
    return `${user} created expense "${description}" for Rs ${amount}`
  }
  if (description) {
    return `${user} created expense "${description}"`
  }
  if (amount != null) {
    return `${user} created an expense for Rs ${amount}`
  }
  return `${user} created an expense`
}

function formatEditedEntry(user: string, log: AuditLog): string {
  const before = log.changes_json?.before
  const after = log.changes_json?.after

  if (!before || !after) {
    return `${user} edited an expense`
  }

  const parts: string[] = []
  for (const field of Object.keys(after)) {
    const beforeVal = before[field]
    const afterVal = after[field]
    if (beforeVal !== afterVal && beforeVal !== undefined) {
      const fieldName = formatFieldName(field)
      parts.push(
        `${fieldName} from "${String(beforeVal)}" to "${String(afterVal)}"`
      )
    }
  }

  if (parts.length === 0) {
    return `${user} edited an expense`
  }

  return `${user} changed ${parts.join(", ")}`
}

function formatRejectedEntry(user: string, log: AuditLog): string {
  const before = log.changes_json?.before
  const after = log.changes_json?.after

  // Owner rejected a settlement claim: before has status "pending", after has status "rejected"
  if (before?.status === "pending" && after?.status === "rejected") {
    return `${user} rejected a settlement claim`
  }

  // Standard expense rejection
  const description = after?.description as string | undefined

  if (description) {
    return `${user} rejected expense "${description}"`
  }
  return `${user} rejected an expense`
}

function formatSettledEntry(user: string, log: AuditLog): string {
  const before = log.changes_json?.before
  const after = log.changes_json?.after

  // Owner confirmation: before has status "pending" and after has status "confirmed"
  if (before?.status === "pending" && after?.status === "confirmed") {
    const amount = before?.amount as number | undefined
    if (amount != null) {
      return `${user} confirmed settlement of Rs ${amount}`
    }
    return `${user} confirmed a settlement`
  }

  // Claim creation: after has status "pending" (original Story 5.1 behavior)
  if (after?.status === "pending") {
    const amount = after?.amount as number | undefined
    if (amount != null) {
      return `${user} marked Rs ${amount} as settled`
    }
    return `${user} marked an expense as settled`
  }

  // Fallback
  const amount = after?.amount as number | undefined
  if (amount != null) {
    return `${user} marked Rs ${amount} as settled`
  }
  return `${user} marked an expense as settled`
}

function formatSplitUpdatedEntry(user: string, log: AuditLog): string {
  const after = log.changes_json?.after
  const description = after?.description as string | undefined

  if (description) {
    return `${user} updated the split for "${description}"`
  }
  return `${user} updated the expense split`
}

function formatFieldName(field: string): string {
  const names: Record<string, string> = {
    description: "description",
    amount: "amount",
    split_type: "split type",
  }
  return names[field] || field
}

export function getUserInitials(name: string | null): string {
  if (!name) return "?"
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return parts[0].slice(0, 2).toUpperCase()
}

export function getActionColor(
  actionType: AuditActionType
): string {
  const colors: Record<AuditActionType, string> = {
    created: "text-emerald-500",
    edited: "text-blue-500",
    confirmed: "text-green-500",
    rejected: "text-red-500",
    settled: "text-amber-500",
    split_updated: "text-violet-500",
  }
  return colors[actionType]
}
