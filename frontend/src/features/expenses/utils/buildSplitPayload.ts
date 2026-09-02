import type {
  SplitType,
  EqualSplitRequest,
  UnequalSplitRequest,
  PercentageSplitRequest,
} from "../types"

export type SplitPayload =
  | EqualSplitRequest
  | UnequalSplitRequest
  | PercentageSplitRequest

interface BuildSplitPayloadArgs {
  splitType: SplitType
  excludedMembers: Set<string>
  customAmounts: Map<string, number>
  percentages: Map<string, number>
}

/**
 * Turn the split editor's state into the exact body the split API expects.
 *
 * The UI reasons in terms of who's INCLUDED, but the API takes
 * `excluded_user_ids` plus per-member amounts/percentages. Keeping the
 * conversion here means the AI preview and the manual form build an identical
 * body from identical state — one pipeline for both entry points (audit F3).
 *
 * Stale entries for members excluded AFTER their amount/percentage was set
 * are dropped (S4-M2), so an excluded person can never leak into the splits
 * array.
 */
export function buildSplitPayload({
  splitType,
  excludedMembers,
  customAmounts,
  percentages,
}: BuildSplitPayloadArgs): SplitPayload {
  const excluded_user_ids = Array.from(excludedMembers)

  if (splitType === "equal") {
    return { type: "equal", excluded_user_ids }
  }

  if (splitType === "unequal") {
    return {
      type: "unequal",
      splits: Array.from(customAmounts.entries())
        .filter(([userId]) => !excludedMembers.has(userId))
        .map(([user_id, amount]) => ({ user_id, amount })),
      excluded_user_ids,
    }
  }

  if (splitType === "percentage") {
    return {
      type: "percentage",
      splits: Array.from(percentages.entries())
        .filter(([userId]) => !excludedMembers.has(userId))
        .map(([user_id, percentage]) => ({ user_id, percentage })),
      excluded_user_ids,
    }
  }

  // "shares" is not implemented (its picker card is disabled). Guard rather
  // than silently send a body the backend can't parse.
  throw new Error(`Split type "${splitType}" is not supported yet`)
}
