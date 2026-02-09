import { useState, useMemo, useCallback } from "react"
import { SplitType } from "../types"
import type { GroupMember } from "../types"

interface UseSplitStateProps {
  /** Total expense amount */
  totalAmount: number
  /** All group members */
  members: GroupMember[]
  /** Initial split type (default: equal) */
  initialType?: SplitType
  /** Payer ID (for rounding difference absorption) */
  payerId?: string
}

interface UseSplitStateReturn {
  /** Current split type */
  splitType: SplitType
  /** Set split type */
  setSplitType: (type: SplitType) => void
  /** Set of excluded member IDs */
  excludedMembers: Set<string>
  /** Toggle member exclusion */
  toggleMemberExclusion: (memberId: string) => void
  /** Calculated split amounts (user_id -> amount) */
  splitAmounts: Map<string, number>
  /** Whether the split configuration is valid (>= 2 members) */
  isValid: boolean
  /** Validation error message */
  validationError: string | null
}

/**
 * Split State Management Hook
 *
 * Manages state for expense splitting:
 * - Split type (equal, unequal, percentage, shares)
 * - Member exclusions
 * - Split amount calculations
 * - Validation (min 2 members)
 *
 * Only implements equal split calculation in Story 3.5.
 * Future stories will add other split type calculations.
 *
 * @example
 * ```tsx
 * const {
 *   splitType,
 *   setSplitType,
 *   excludedMembers,
 *   toggleMemberExclusion,
 *   splitAmounts,
 *   isValid,
 *   validationError
 * } = useSplitState({
 *   totalAmount: 1500,
 *   members: groupMembers,
 *   payerId: currentUserId
 * })
 * ```
 */
export function useSplitState({
  totalAmount,
  members,
  initialType = "equal",
  payerId,
}: UseSplitStateProps): UseSplitStateReturn {
  const [splitType, setSplitType] = useState<SplitType>(initialType)
  const [excludedMembers, setExcludedMembers] = useState<Set<string>>(new Set())

  // Calculate split amounts based on type and exclusions
  const splitAmounts = useMemo(() => {
    const includedMembers = members.filter((m) => {
      const memberId = m.user_id || m.id
      return !excludedMembers.has(memberId)
    })

    if (includedMembers.length < 2) {
      return new Map<string, number>()
    }

    if (splitType === "equal") {
      // Equal split calculation
      const amountPerPerson = totalAmount / includedMembers.length

      const amounts = new Map<string, number>()
      let runningTotal = 0

      includedMembers.forEach((member, index) => {
        let amount = Math.round(amountPerPerson * 100) / 100

        // Payer absorbs rounding difference
        const memberId = member.user_id || member.id
        if (payerId && memberId === payerId && index === includedMembers.length - 1) {
          amount = Math.round((totalAmount - runningTotal) * 100) / 100
        }

        amounts.set(memberId, amount)
        runningTotal += amount
      })

      return amounts
    }

    // Other split types will be implemented in future stories
    return new Map<string, number>()
  }, [splitType, totalAmount, members, excludedMembers, payerId])

  // Toggle member exclusion
  const toggleMemberExclusion = useCallback((memberId: string) => {
    setExcludedMembers((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(memberId)) {
        newSet.delete(memberId)
      } else {
        newSet.add(memberId)
      }
      return newSet
    })
  }, [])

  // Validate split configuration
  const { isValid, validationError } = useMemo(() => {
    const includedCount = members.length - excludedMembers.size

    if (includedCount < 2) {
      return {
        isValid: false,
        validationError: "At least 2 members required for split",
      }
    }

    return {
      isValid: true,
      validationError: null,
    }
  }, [members.length, excludedMembers.size])

  return {
    splitType,
    setSplitType,
    excludedMembers,
    toggleMemberExclusion,
    splitAmounts,
    isValid,
    validationError,
  }
}
