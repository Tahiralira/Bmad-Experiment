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
})
