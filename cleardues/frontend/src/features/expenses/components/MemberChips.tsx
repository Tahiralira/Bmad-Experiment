import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Check, X } from "lucide-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import type { GroupMember } from "../types"

interface MemberChipsProps {
  /** All group members */
  members: GroupMember[]
  /** Set of member IDs that are included in the split */
  includedMembers: Set<string>
  /** Callback when user toggles a member's include/exclude status */
  onToggleInclude: (memberId: string) => void
}

/**
 * Member Chips Component
 *
 * Displays group members as chips with avatars.
 * Users can tap to toggle include/exclude for each member.
 *
 * Visual states:
 * - Included: Full color avatar, teal checkmark, normal text
 * - Excluded: Grayscale avatar, X icon, struck-through name
 *
 * @example
 * ```tsx
 * <MemberChips
 *   members={groupMembers}
 *   includedMembers={includedSet}
 *   onToggleInclude={toggleMember}
 * />
 * ```
 */
export function MemberChips({
  members,
  includedMembers,
  onToggleInclude,
}: MemberChipsProps) {
  const includedCount = includedMembers.size
  const totalCount = members.length

  return (
    <div className="flex flex-col gap-1.5">
      <label className="block text-xs font-medium text-text-secondary">
        Split between ({includedCount} of {totalCount} selected)
      </label>

      <div className="flex flex-wrap gap-2">
        {members.map((member) => {
          const isIncluded = includedMembers.has(member.user_id || member.id)

          // Generate initials from full name
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
            <motion.button
              key={member.user_id || member.id}
              type="button"
              onClick={() => onToggleInclude(member.user_id || member.id)}
              className={cn(
                "member-chip",
                "flex items-center gap-2 px-3 py-2 rounded-full border",
                "transition-all",
                isIncluded
                  ? "border-action bg-action/5"
                  : "border-border bg-surface opacity-60",
                "hover:border-action/50 hover:bg-action/5",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action"
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ duration: 0.2 }}
            >
              <Avatar className="w-6 h-6">
                {member.avatar_url && (
                  <AvatarImage src={member.avatar_url} alt={member.full_name || undefined} />
                )}
                <AvatarFallback
                  className={cn(
                    "text-xs",
                    isIncluded ? "bg-action text-white" : "bg-muted text-muted-foreground"
                  )}
                >
                  {initials}
                </AvatarFallback>
              </Avatar>

              <span
                className={cn(
                  "text-sm font-medium",
                  isIncluded ? "text-primary" : "text-text-secondary line-through"
                )}
              >
                {member.full_name || member.email?.split("@")[0]}
              </span>

              <div className="w-4 h-4 flex items-center justify-center">
                {isIncluded ? (
                  <Check className="w-4 h-4 text-action" />
                ) : (
                  <X className="w-4 h-4 text-muted-foreground" />
                )}
              </div>
            </motion.button>
          )
        })}
      </div>

      <p className="text-xs text-text-tertiary">
        Tap to toggle include/exclude
      </p>
    </div>
  )
}
