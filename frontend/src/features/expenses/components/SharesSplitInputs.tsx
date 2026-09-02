import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { BalanceDisplay } from "@/components/ui/balance-display"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import type { GroupMember } from "../types"

interface SharesSplitInputsProps {
  /** Group members to allocate shares to */
  members: GroupMember[]
  /** Members excluded from the split */
  excludedMembers: Set<string>
  /** Current share weights for each member (user_id -> integer shares) */
  shares: Map<string, number>
  /** Total expense amount for previewing resulting amounts */
  totalAmount: number
  /** Callback when user changes a member's share count */
  onShareChange: (memberId: string, shares: number) => void
}

/**
 * Shares Split Inputs (audit F13).
 *
 * Weighted split: each included member is given a positive integer number of
 * shares, and the total is apportioned by weight (2 shares owes twice 1). The
 * amount shown per member is a live preview; SplitAmountsDisplay renders the
 * authoritative rounded amounts.
 */
export function SharesSplitInputs({
  members,
  excludedMembers,
  shares,
  totalAmount,
  onShareChange,
}: SharesSplitInputsProps) {
  const includedMembers = members.filter(
    (m) => !excludedMembers.has(m.user_id || m.id),
  )

  const totalShares = includedMembers.reduce(
    (sum, m) => sum + (shares.get(m.user_id || m.id) ?? 0),
    0,
  )

  return (
    <div className="shares-split-inputs-container">
      {/* Total shares indicator */}
      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm font-medium text-text-primary">
          Total shares:
        </span>
        <span className="text-sm font-semibold text-text-secondary">
          {totalShares}
        </span>
      </div>

      <div className="space-y-2">
        {includedMembers.map((member) => {
          const memberId = member.user_id || member.id
          const initials = member.full_name
            ? member.full_name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()
                .slice(0, 2)
            : (member.email || "??").slice(0, 2)

          const memberShares = shares.get(memberId) ?? 0
          const hasShares = memberShares > 0
          const amount =
            totalShares > 0 ? (totalAmount * memberShares) / totalShares : 0

          return (
            <div
              key={memberId}
              className={cn(
                "animate-in fade-in-0 duration-150",
                "flex items-center gap-3 p-3 rounded-lg border",
                hasShares
                  ? "border-action bg-action/5"
                  : "border-border bg-surface",
              )}
            >
              <Avatar className="w-8 h-8">
                {member.avatar_url && <AvatarImage src={member.avatar_url} />}
                <AvatarFallback
                  className={cn(
                    "text-xs",
                    hasShares
                      ? "bg-action text-white"
                      : "bg-muted text-text-secondary",
                  )}
                >
                  {initials}
                </AvatarFallback>
              </Avatar>

              <span className="flex-1 text-sm font-medium text-text-primary">
                {member.full_name || member.email}
              </span>

              <div className="relative flex items-center gap-2">
                <input
                  type="number"
                  value={memberShares === 0 ? "" : memberShares}
                  onChange={(e) => {
                    if (e.target.value === "") {
                      onShareChange(memberId, 0)
                      return
                    }
                    const value = parseInt(e.target.value, 10)
                    if (!isNaN(value) && value >= 0) {
                      onShareChange(memberId, value)
                    }
                  }}
                  placeholder="0"
                  step="1"
                  min="1"
                  aria-label={`Shares for ${member.full_name || member.email}`}
                  className={cn(
                    "w-16 px-3 py-2 text-right rounded-md border text-sm font-medium",
                    "focus:outline-none focus:ring-2 focus:ring-action",
                    hasShares && "border-action bg-action/10",
                  )}
                />
                {hasShares && <Check className="w-4 h-4 text-action" />}
              </div>

              {hasShares && totalShares > 0 && (
                <div className="w-24 text-right">
                  <div className="text-xs text-text-secondary">Amount:</div>
                  <BalanceDisplay
                    amount={amount}
                    variant="body"
                    className="text-sm"
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>

      <p className="mt-3 text-xs text-text-secondary">
        Shares split the total by weight — a member with 2 shares owes twice one
        with 1.
      </p>
    </div>
  )
}
