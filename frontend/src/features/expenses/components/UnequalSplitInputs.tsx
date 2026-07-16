import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { BalanceDisplay } from "@/components/ui/balance-display"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import type { GroupMember } from "../types"

interface UnequalSplitInputsProps {
  /** Group members to allocate amounts to */
  members: GroupMember[]
  /** Members excluded from the split (Story 3.8) */
  excludedMembers: Set<string>
  /** Current custom amounts for each member (user_id -> amount) */
  customAmounts: Map<string, number>
  /** Total expense amount to allocate */
  totalAmount: number
  /** Callback when user changes amount for a member */
  onAmountChange: (memberId: string, amount: number) => void
}

/**
 * Unequal Split Amount Inputs Component
 *
 * Displays inline amount inputs for each group member in unequal split mode.
 * Shows real-time validation with remaining amount display.
 *
 * Features:
 * - Member chips with inline amount input fields
 * - BalanceDisplay component for currency prefix
 * - "Rs" prefix with comma separators
 * - Numeric input for each member
 * - Teal checkmark when amount entered
 * - Real-time remaining amount calculation
 * - Color-coded validation (muted/success/destructive)
 *
 * @example
 * ```tsx
 * <UnequalSplitInputs
 *   members={members}
 *   customAmounts={customAmounts}
 *   totalAmount={100}
 *   onAmountChange={(memberId, amount) => setCustomAmount(memberId, amount)}
 * />
 * ```
 */
export function UnequalSplitInputs({
  members,
  excludedMembers,
  customAmounts,
  totalAmount,
  onAmountChange,
}: UnequalSplitInputsProps) {
  // Filter out excluded members (Story 3.8)
  const includedMembers = members.filter((m) => !excludedMembers.has(m.user_id))

  // Calculate remaining amount (only for included members)
  const remaining = includedMembers.reduce((sum, member) => {
    const amount = customAmounts.get(member.user_id) || 0
    return sum - amount
  }, totalAmount)

  const isExactMatch = Math.abs(remaining) < 0.01
  const isOverAllocated = remaining < 0

  return (
    <div className="unequal-split-inputs-container">
      {/* Remaining amount display */}
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm font-medium text-text-primary">
          Remaining to allocate:
        </span>
        <BalanceDisplay
          amount={Math.abs(remaining)}
          variant="body"
          className={cn(
            isExactMatch && "text-success",
            isOverAllocated && "text-destructive",
            !isExactMatch && !isOverAllocated && "text-text-secondary"
          )}
        />
      </div>

      {/* Member amount inputs (only included members shown) */}
      <div className="space-y-2">
        {includedMembers.map((member) => {
          // Safe fallback: use email if full_name is null, fallback to "??"
          const initials = member.full_name
            ? member.full_name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
            : (member.email || "??").slice(0, 2)

          const amount = customAmounts.get(member.user_id) || 0
          const hasAmount = amount > 0

          return (
            <div
              key={member.user_id}
              className={cn(
                "animate-in fade-in-0 duration-150",
                "flex items-center gap-3 p-3 rounded-lg border",
                hasAmount ? "border-action bg-action/5" : "border-border bg-surface"
              )}
            >
              <Avatar className="w-8 h-8">
                {member.avatar_url && <AvatarImage src={member.avatar_url} />}
                <AvatarFallback
                  className={cn(
                    "text-xs",
                    hasAmount ? "bg-action text-white" : "bg-muted text-text-secondary"
                  )}
                >
                  {initials}
                </AvatarFallback>
              </Avatar>

              <span className="flex-1 text-sm font-medium text-text-primary">
                {member.full_name || member.email}
              </span>

              <div className="relative flex items-center">
                <span className="absolute left-3 text-sm text-text-secondary">
                  Rs
                </span>
                <input
                  type="number"
                  value={amount || ""}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value)
                    // Only update if valid number (not NaN) and non-negative
                    if (!isNaN(value) && value >= 0) {
                      onAmountChange(member.user_id, value)
                    }
                  }}
                  placeholder="0"
                  step="0.01"
                  min="0"
                  max={totalAmount}
                  aria-label={`Amount for ${member.full_name || member.email}`}
                  className={cn(
                    "w-28 pl-8 pr-8 py-2 text-right rounded-md border",
                    "text-sm font-medium",
                    "focus:outline-none focus:ring-2 focus:ring-action",
                    hasAmount && "border-action bg-action/10"
                  )}
                />
                {hasAmount && (
                  <Check className="absolute right-3 w-4 h-4 text-action" />
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Validation message */}
      {!isExactMatch && (
        <p className="text-xs text-text-secondary mt-3">
          {isOverAllocated
            ? `Over-allocated by Rs ${Math.abs(remaining).toFixed(2)}`
            : `Allocate Rs ${remaining.toFixed(2)} more`}
        </p>
      )}
    </div>
  )
}
