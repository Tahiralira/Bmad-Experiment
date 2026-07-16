import { renderHook, act } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { useSplitState } from "./useSplitState"
import type { GroupMember } from "../types"

describe("useSplitState", () => {
  const mockMembers: GroupMember[] = [
    { id: "1", user_id: "1", full_name: "Alice", email: "alice@example.com" },
    { id: "2", user_id: "2", full_name: "Bob", email: "bob@example.com" },
    { id: "3", user_id: "3", full_name: "Charlie", email: "charlie@example.com" },
  ]

  it("calculates equal split amounts correctly", () => {
    const { result } = renderHook(() =>
      useSplitState({
        totalAmount: 150,
        members: mockMembers,
        payerId: "1",
      })
    )

    expect(result.current.splitAmounts.get("1")).toBe(50)
    expect(result.current.splitAmounts.get("2")).toBe(50)
    expect(result.current.splitAmounts.get("3")).toBe(50)
  })

  it("recalculates when member is excluded", () => {
    const { result } = renderHook(() =>
      useSplitState({
        totalAmount: 150,
        members: mockMembers,
        payerId: "1",
      })
    )

    act(() => {
      result.current.toggleMemberExclusion("3")
    })

    // 150 / 2 = 75 each for remaining members
    expect(result.current.splitAmounts.get("1")).toBe(75)
    expect(result.current.splitAmounts.get("2")).toBe(75)
    expect(result.current.splitAmounts.has("3")).toBe(false)
  })

  it("validates minimum 2 members", () => {
    const { result } = renderHook(() =>
      useSplitState({
        totalAmount: 100,
        members: mockMembers,
        payerId: "1",
      })
    )

    expect(result.current.isValid).toBe(true)

    act(() => {
      result.current.toggleMemberExclusion("2")
      result.current.toggleMemberExclusion("3")
    })

    // Only 1 member left - should be invalid
    expect(result.current.isValid).toBe(false)
    expect(result.current.validationError).toBe("At least 2 members required for split")
  })

  // S4-M1 (fixed in WS5): the payer absorbs the rounding remainder no matter
  // where they sit in the members array
  it("handles rounding correctly", () => {
    const { result } = renderHook(() =>
      useSplitState({
        totalAmount: 100,
        members: mockMembers,
        payerId: "1",
      })
    )

    // 100 / 3 = 33.33 each, payer absorbs 0.01
    expect(result.current.splitAmounts.get("1")).toBe(33.34) // Payer with adjustment
    expect(result.current.splitAmounts.get("2")).toBe(33.33)
    expect(result.current.splitAmounts.get("3")).toBe(33.33)
  })

  it("last member absorbs rounding when the payer is excluded", () => {
    const { result } = renderHook(() =>
      useSplitState({
        totalAmount: 100,
        members: mockMembers,
        payerId: "1",
      })
    )

    act(() => {
      result.current.toggleMemberExclusion("1") // exclude the payer
    })

    // 100 / 2 = 50 each — and the shares must still sum to the total
    const amounts = result.current.splitAmounts
    expect(amounts.has("1")).toBe(false)
    const sum = [...amounts.values()].reduce((a, b) => a + b, 0)
    expect(Math.round(sum * 100) / 100).toBe(100)
  })

  // S4-M2 (fixed in WS5): a stale amount left behind by an excluded member
  // must not stand in for an included member who never got one
  it("invalidates unequal split when an included member has no amount", () => {
    const { result } = renderHook(() =>
      useSplitState({
        totalAmount: 100,
        members: mockMembers,
        payerId: "1",
      })
    )

    act(() => {
      result.current.setSplitType("unequal")
    })
    act(() => {
      // Alice covers the total; Charlie gets an amount then is excluded.
      // Bob (included) never gets an amount — the old size-based check
      // counted Charlie's stale entry and passed validation.
      result.current.setCustomAmount("1", 100)
      result.current.setCustomAmount("3", 50)
    })
    act(() => {
      result.current.toggleMemberExclusion("3")
    })

    expect(result.current.isValid).toBe(false)
    expect(result.current.validationError).toBe(
      "All included members must have an amount specified"
    )
  })
})
