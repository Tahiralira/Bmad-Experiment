import { BalanceDisplay } from "@/components/ui/balance-display"
import type { GroupMember } from "../types"

interface SplitAmountsDisplayProps {
  /** Total expense amount */
  totalAmount: number
  /** Calculated split amounts per user (user_id -> amount) */
  splitAmounts: Map<string, number>
  /** All group members */
  members: GroupMember[]
  /** Set of included member IDs */
  includedMembers: Set<string>
}

/**
 * Split Amounts Display Component
 *
 * Shows how much each member owes for the expense.
 * Uses BalanceDisplay component for currency formatting (Rs prefix, comma separators).
 * Only shows amounts for included members.
 *
 * @example
 * ```tsx
 * <SplitAmountsDisplay
 *   totalAmount={1500}
 *   splitAmounts={amountsMap}
 *   members={groupMembers}
 *   includedMembers={includedSet}
 * />
 * ```
 */
export function SplitAmountsDisplay({
  totalAmount,
  splitAmounts,
  members,
  includedMembers,
}: SplitAmountsDisplayProps) {
  const includedMembersList = members.filter(
    (m) => includedMembers.has(m.user_id || m.id)
  )

  if (includedMembersList.length === 0) {
    return null
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="block text-xs font-medium text-text-secondary">
        Amount per person
      </label>

      <div className="space-y-2">
        {includedMembersList.map((member) => {
          const memberId = member.user_id || member.id
          const amount = splitAmounts.get(memberId)

          if (amount === undefined) return null

          // Generate initials
          const initials = (
            member.full_name ||
            member.email?.split("@")[0] ||
            "U"
          )
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2)

          return (
            <div
              key={memberId}
              className="flex items-center justify-between p-3 rounded-lg bg-surface border border-border"
            >
              <div className="flex items-center gap-3">
                {/* Avatar/Initials */}
                <div className="w-8 h-8 rounded-full bg-action/10 flex items-center justify-center">
                  <span className="text-xs font-medium text-action">
                    {initials}
                  </span>
                </div>

                {/* Member name */}
                <span className="text-sm font-medium text-text-primary">
                  {member.full_name || member.email?.split("@")[0]}
                </span>
              </div>

              {/* Amount */}
              <BalanceDisplay
                amount={amount}
                variant="body"
              />
            </div>
          )
        })}
      </div>

      {/* Total summary */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-surface-elevated border border-border mt-2">
        <span className="text-xs font-medium text-text-secondary">
          Total expense
        </span>
        <BalanceDisplay
          amount={totalAmount}
          variant="body"
        />
      </div>
    </div>
  )
}
