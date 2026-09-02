import { useEffect } from "react"

import { SplitPicker } from "./SplitPicker"
import { MemberChips } from "./MemberChips"
import { SplitAmountsDisplay } from "./SplitAmountsDisplay"
import { UnequalSplitInputs } from "./UnequalSplitInputs"
import { PercentageSplitInputs } from "./PercentageSplitInputs"
import { SharesSplitInputs } from "./SharesSplitInputs"
import type { UseSplitStateReturn } from "../hooks/useSplitState"
import type { GroupMember } from "../types"

interface SplitFieldsProps {
  /** All group members */
  members: GroupMember[]
  /** Total expense amount (drives the per-person amounts) */
  totalAmount: number
  /** Split state from useSplitState (owned by the parent so it can read the
   *  final configuration at submit time). */
  split: UseSplitStateReturn
}

/**
 * The split editor — split type, participant chips, per-member inputs, and the
 * live amount breakdown. Presentational: the parent owns `useSplitState` and
 * passes it in, so both the AI preview and the manual form drive the SAME
 * editor and build the SAME payload (audit F3 — one split pipeline).
 *
 * Always visible during expense creation (audit F1/F4): splitting is the core
 * action, not something hidden behind an "Edit Details" gear. The chips render
 * the INCLUSION set (audit F2), so everyone — including the creator — shows as
 * selected by default and tapping a chip removes that person.
 */
export function SplitFields({ members, totalAmount, split }: SplitFieldsProps) {
  const {
    splitType,
    setSplitType,
    excludedMembers,
    includedMembers,
    toggleMemberExclusion,
    customAmounts,
    setCustomAmount,
    percentages,
    setPercentage,
    shares,
    setShare,
    splitAmounts,
    validationError,
  } = split

  // Pre-populate custom amounts when switching to unequal (Story 3.6): seed
  // with the current equal shares so the user edits from a valid starting point.
  useEffect(() => {
    if (
      splitType === "unequal" &&
      customAmounts.size === 0 &&
      splitAmounts.size > 0
    ) {
      splitAmounts.forEach((amount, memberId) => setCustomAmount(memberId, amount))
    }
  }, [splitType, splitAmounts, customAmounts.size, setCustomAmount])

  // Pre-populate percentages when switching to percentage (Story 3.7): even
  // distribution across all members.
  useEffect(() => {
    if (
      splitType === "percentage" &&
      percentages.size === 0 &&
      members.length > 0
    ) {
      const equalPercentage = 100 / members.length
      members.forEach((member) =>
        setPercentage(member.user_id || member.id, equalPercentage),
      )
    }
  }, [splitType, percentages.size, members.length, members, setPercentage])

  // Pre-populate shares when switching to shares (audit F13): 1 share each,
  // i.e. an even split the user can then reweight.
  useEffect(() => {
    if (splitType === "shares" && shares.size === 0 && members.length > 0) {
      members.forEach((member) => setShare(member.user_id || member.id, 1))
    }
  }, [splitType, shares.size, members.length, members, setShare])

  return (
    <div className="flex flex-col gap-3">
      <SplitPicker selectedType={splitType} onSelectType={setSplitType} />

      {splitType === "unequal" && (
        <UnequalSplitInputs
          members={members}
          excludedMembers={excludedMembers}
          customAmounts={customAmounts}
          totalAmount={totalAmount}
          onAmountChange={setCustomAmount}
        />
      )}

      {splitType === "percentage" && (
        <PercentageSplitInputs
          members={members}
          excludedMembers={excludedMembers}
          percentages={percentages}
          totalAmount={totalAmount}
          onPercentageChange={setPercentage}
        />
      )}

      {splitType === "shares" && (
        <SharesSplitInputs
          members={members}
          excludedMembers={excludedMembers}
          shares={shares}
          totalAmount={totalAmount}
          onShareChange={setShare}
        />
      )}

      {/* Inclusion set (audit F2) — everyone selected by default */}
      <MemberChips
        members={members}
        includedMembers={includedMembers}
        onToggleInclude={toggleMemberExclusion}
      />

      <SplitAmountsDisplay
        totalAmount={totalAmount}
        splitAmounts={splitAmounts}
        members={members}
        includedMembers={includedMembers}
      />

      {validationError && (
        <p className="text-xs text-error" role="alert">
          {validationError}
        </p>
      )}
    </div>
  )
}
