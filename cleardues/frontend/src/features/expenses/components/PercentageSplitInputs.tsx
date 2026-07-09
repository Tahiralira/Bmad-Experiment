import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { BalanceDisplay } from "@/components/ui/balance-display"
import { Check } from "lucide-react"
import { motion } from "framer-motion"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import type { GroupMember } from "../types"

interface PercentageSplitInputsProps {
  /** Group members to allocate percentages to */
  members: GroupMember[]
  /** Members excluded from the split (Story 3.8) */
  excludedMembers: Set<string>
  /** Current percentages for each member (user_id -> percentage) */
  percentages: Map<string, number>
  /** Total expense amount for calculating amounts */
  totalAmount: number
  /** Callback when user changes percentage for a member */
  onPercentageChange: (memberId: string, percentage: number) => void
}

/**
 * Percentage Split Inputs Component
 *
 * Displays inline percentage inputs for each group member in percentage split mode.
 * Shows real-time calculation of resulting amounts.
 *
 * Features:
 * - Member chips with inline percentage input fields
 * - BalanceDisplay component for calculated amount display
 * - "%" suffix with calculated amount below
 * - Numeric input (0-100) for each member
 * - Teal checkmark when valid percentage entered
 * - Real-time calculation shows resulting amount for each percentage
 * - Visual indicator shows total percentage progress toward 100%
 * - Progress bar showing total percentage with color coding
 *
 * @example
 * ```tsx
 * <PercentageSplitInputs
 *   members={members}
 *   percentages={percentages}
 *   totalAmount={100}
 *   onPercentageChange={(memberId, percentage) => setPercentage(memberId, percentage)}
 * />
 * ```
 */
export function PercentageSplitInputs({
  members,
  excludedMembers,
  percentages,
  totalAmount,
  onPercentageChange,
}: PercentageSplitInputsProps) {
  // Filter out excluded members (Story 3.8)
  const includedMembers = members.filter((m) => !excludedMembers.has(m.user_id))

  // Calculate total percentage (only for included members)
  const totalPercentage = Array.from(percentages.entries())
    .filter(([memberId]) => !excludedMembers.has(memberId))
    .reduce((sum, [, pct]) => sum + pct, 0)

  const isExactMatch = Math.abs(totalPercentage - 100) < 0.01
  const isOverAllocated = totalPercentage > 100

  return (
    <div className="percentage-split-inputs-container">
      {/* Total percentage progress indicator */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-text-primary">
            Total Percentage:
          </span>
          <span className={cn(
            "text-sm font-semibold",
            isExactMatch && "text-success",
            isOverAllocated && "text-destructive",
            !isExactMatch && !isOverAllocated && "text-text-secondary"
          )}>
            {totalPercentage.toFixed(1)}%
          </span>
        </div>
        <Progress
          value={Math.min(totalPercentage, 100)}
          className={cn(
            "h-2",
            isExactMatch && "bg-success",
            isOverAllocated && "bg-destructive"
          )}
        />
      </div>

      {/* Member percentage inputs (only included members shown) */}
      <div className="space-y-2">
        {includedMembers.map((member) => {
          // Safe fallback: use email if full_name is null, fallback to "??"
          const initials = member.full_name
            ? member.full_name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
            : (member.email || "??").slice(0, 2)

          const percentage = percentages.get(member.user_id) || 0
          const calculatedAmount = (totalAmount * percentage) / 100
          const hasPercentage = percentage > 0

          return (
            <motion.div
              key={member.user_id}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg border",
                hasPercentage ? "border-action bg-action/5" : "border-border bg-surface"
              )}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Avatar className="w-8 h-8">
                {member.avatar_url && <AvatarImage src={member.avatar_url} />}
                <AvatarFallback
                  className={cn(
                    "text-xs",
                    hasPercentage ? "bg-action text-white" : "bg-muted text-text-secondary"
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
                  value={percentage === 0 ? "0" : percentage || ""}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value)
                    // Only update if valid number (not NaN) and in range [0, 100]
                    if (!isNaN(value) && value >= 0 && value <= 100) {
                      onPercentageChange(member.user_id, value)
                    }
                  }}
                  placeholder="0"
                  step="0.1"
                  min="0"
                  max="100"
                  aria-label={`Percentage for ${member.full_name || member.email}`}
                  className={cn(
                    "w-20 pl-3 pr-7 py-2 text-right rounded-md border",
                    "text-sm font-medium",
                    "focus:outline-none focus:ring-2 focus:ring-action",
                    hasPercentage && "border-action bg-action/10"
                  )}
                />
                <span className="absolute right-2.5 text-sm text-text-secondary">
                  %
                </span>
                {hasPercentage && (
                  <Check className="absolute right-7 w-4 h-4 text-action" />
                )}
              </div>

              {/* Calculated amount display */}
              {hasPercentage && (
                <div className="w-24 text-right">
                  <div className="text-xs text-text-secondary">Amount:</div>
                  <BalanceDisplay
                    amount={calculatedAmount}
                    variant="body"
                    className="text-sm"
                  />
                </div>
              )}
            </motion.div>
          )
        })}
      </div>

      {/* Validation message */}
      {!isExactMatch && (
        <p className="text-xs text-text-secondary mt-3">
          {isOverAllocated
            ? `Over-allocated by ${(totalPercentage - 100).toFixed(1)}%`
            : `Allocate ${(100 - totalPercentage).toFixed(1)}% more`}
        </p>
      )}
    </div>
  )
}
