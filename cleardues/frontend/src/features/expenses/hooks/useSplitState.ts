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
  /** Custom amounts for unequal split (user_id -> amount) */
  customAmounts: Map<string, number>
  /** Set custom amount for a member (unequal split) */
  setCustomAmount: (memberId: string, amount: number) => void
  /** Percentages for percentage split (user_id -> percentage) */
  percentages: Map<string, number>
  /** Set percentage for a member (percentage split) */
  setPercentage: (memberId: string, percentage: number) => void
  /** Total percentage (for percentage split validation) */
  totalPercentage: number
  /** Calculated split amounts (user_id -> amount) */
  splitAmounts: Map<string, number>
  /** Remaining amount to allocate (unequal split only) */
  remainingAmount: number
  /** Whether the split configuration is valid (>= 2 members, amounts match total for unequal/percentage) */
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
 * - Custom amounts for unequal splits
 * - Percentages for percentage splits
 * - Split amount calculations
 * - Validation (min 2 members, amounts match total for unequal/percentage)
 *
 * Implements equal split (Story 3.5), unequal split (Story 3.6), and percentage split (Story 3.7).
 * Future stories will add shares split calculation.
 *
 * @example
 * ```tsx
 * const {
 *   splitType,
 *   setSplitType,
 *   excludedMembers,
 *   toggleMemberExclusion,
 *   customAmounts,
 *   setCustomAmount,
 *   percentages,
 *   setPercentage,
 *   totalPercentage,
 *   splitAmounts,
 *   remainingAmount,
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
  const [customAmounts, setCustomAmounts] = useState<Map<string, number>>(new Map())
  const [percentages, setPercentages] = useState<Map<string, number>>(new Map())

  // Enhanced setSplitType that clears state when switching away from unequal/percentage split
  const handleSetSplitType = useCallback((newType: SplitType) => {
    setSplitType((prevType) => {
      // If switching from unequal to anything else, clear custom amounts
      if (prevType === "unequal" && newType !== "unequal") {
        setCustomAmounts(new Map())
      }
      // If switching from percentage to anything else, clear percentages
      if (prevType === "percentage" && newType !== "percentage") {
        setPercentages(new Map())
      }
      return newType
    })
  }, [])

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
      // Equal split calculation. The rounding remainder is absorbed by the
      // payer REGARDLESS of their position in the members array (S4-M1: the
      // old index check only balanced when the payer happened to be last —
      // Rs 100 / 3 with the payer first displayed 33.33 × 3 = 99.99).
      // When the payer is not part of the split, the last member absorbs it
      // so the shares always sum to the total.
      const share =
        Math.round((totalAmount / includedMembers.length) * 100) / 100
      const includedIds = includedMembers.map((m) => m.user_id || m.id)
      const payerIncluded = !!payerId && includedIds.includes(payerId)
      const absorberId = payerIncluded
        ? payerId
        : includedIds[includedIds.length - 1]

      const absorberAmount =
        Math.round((totalAmount - share * (includedIds.length - 1)) * 100) /
        100

      const amounts = new Map<string, number>()
      for (const memberId of includedIds) {
        amounts.set(memberId, memberId === absorberId ? absorberAmount : share)
      }

      return amounts
    }

    if (splitType === "unequal") {
      // For unequal split, filter out excluded members from custom amounts
      const amounts = new Map<string, number>()
      customAmounts.forEach((amount, memberId) => {
        // Only include amounts for non-excluded members
        if (!excludedMembers.has(memberId)) {
          amounts.set(memberId, amount)
        }
      })
      return amounts
    }

    if (splitType === "percentage") {
      // For percentage split, filter out excluded members from percentages
      const amounts = new Map<string, number>()
      let runningTotal = 0

      // Convert percentages Map to array, filter excluded members, and sort by user_id
      const percentageEntries = Array.from(percentages.entries())
        .filter(([memberId]) => !excludedMembers.has(memberId))
        .sort((a, b) => a[0].localeCompare(b[0]))

      percentageEntries.forEach(([memberId, percentage], index) => {
        let amount: number
        if (index === percentageEntries.length - 1) {
          // Last member gets remainder (to avoid rounding errors)
          amount = Math.round((totalAmount - runningTotal) * 100) / 100
        } else {
          amount = Math.round((totalAmount * percentage / 100) * 100) / 100
          runningTotal += amount
        }
        amounts.set(memberId, amount)
      })

      return amounts
    }

    // Other split types will be implemented in future stories
    return new Map<string, number>()
  }, [splitType, totalAmount, members, excludedMembers, payerId, customAmounts, percentages])

  // Calculate remaining amount for unequal split (only counts included members)
  const remainingAmount = useMemo(() => {
    if (splitType !== "unequal") {
      return 0
    }

    // Sum amounts only for included (non-excluded) members
    let allocated = 0
    customAmounts.forEach((amount, memberId) => {
      if (!excludedMembers.has(memberId)) {
        allocated += amount
      }
    })
    return totalAmount - allocated
  }, [splitType, customAmounts, totalAmount, excludedMembers])

  // Calculate total percentage for percentage split (only counts included members)
  const totalPercentage = useMemo(() => {
    if (splitType !== "percentage") {
      return 0
    }

    // Sum percentages only for included (non-excluded) members
    let total = 0
    percentages.forEach((percentage, memberId) => {
      if (!excludedMembers.has(memberId)) {
        total += percentage
      }
    })
    return total
  }, [splitType, percentages, excludedMembers])
  // Set custom amount for a member (unequal split)
  const setCustomAmount = useCallback((memberId: string, amount: number) => {
    setCustomAmounts((prev) => {
      const newMap = new Map(prev)
      if (amount > 0) {
        newMap.set(memberId, amount)
      } else {
        newMap.delete(memberId)
      }
      return newMap
    })
  }, [])

  // Set percentage for a member (percentage split)
  const setPercentage = useCallback((memberId: string, percentage: number) => {
    setPercentages((prev) => {
      const newMap = new Map(prev)
      if (percentage >= 0 && percentage <= 100) {
        newMap.set(memberId, percentage)
      } else {
        newMap.delete(memberId)
      }
      return newMap
    })
  }, [])

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

    // Additional validation for unequal split
    if (splitType === "unequal") {
      // EVERY included member must have an amount (S4-M2: comparing raw map
      // sizes let stale amounts of since-excluded members stand in for
      // included members who never got one — submitting a "split" that
      // silently omitted someone)
      const missingAmount = members.some((m) => {
        const memberId = m.user_id || m.id
        return !excludedMembers.has(memberId) && !customAmounts.has(memberId)
      })
      if (missingAmount) {
        return {
          isValid: false,
          validationError: "All included members must have an amount specified",
        }
      }

      // Amounts must sum to total (matches backend error message format)
      if (Math.abs(remainingAmount) >= 0.01) {
        const currentTotal = totalAmount - remainingAmount
        return {
          isValid: false,
          validationError: `Split amounts (Rs ${currentTotal.toFixed(2)}) must equal total expense amount (Rs ${totalAmount.toFixed(2)})`,
        }
      }
    }

    // Additional validation for percentage split (Story 3.7)
    if (splitType === "percentage") {
      // Count included members
      const includedCount = members.filter(m => {
        const memberId = m.user_id || m.id
        return !excludedMembers.has(memberId)
      }).length

      // All included members must have percentages
      const includedPercentageCount = Array.from(percentages.entries())
        .filter(([memberId]) => !excludedMembers.has(memberId))
        .length

      if (includedPercentageCount !== includedCount) {
        return {
          isValid: false,
          validationError: "All included members must have a percentage specified",
        }
      }

      // Percentages must sum to 100 (matches backend error message format)
      if (Math.abs(totalPercentage - 100) >= 0.01) {
        return {
          isValid: false,
          validationError: `Split percentages (${totalPercentage.toFixed(1)}%) must equal 100%`,
        }
      }
    }

    return {
      isValid: true,
      validationError: null,
    }
    // Map/Set identities (not .size) — the S4-M2 check depends on WHICH
    // members have amounts, and state setters always produce new instances
  }, [members, excludedMembers, splitType, customAmounts, remainingAmount, totalAmount, percentages, totalPercentage])

  return {
    splitType,
    setSplitType: handleSetSplitType,
    excludedMembers,
    toggleMemberExclusion,
    customAmounts,
    setCustomAmount,
    percentages,
    setPercentage,
    totalPercentage,
    splitAmounts,
    remainingAmount,
    isValid,
    validationError,
  }
}
