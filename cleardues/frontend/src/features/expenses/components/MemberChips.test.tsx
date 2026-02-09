import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { MemberChips } from "./MemberChips"
import type { GroupMember } from "../types"

describe("MemberChips", () => {
  const mockMembers: GroupMember[] = [
    { id: "1", user_id: "1", full_name: "Alice Johnson", email: "alice@example.com" },
    { id: "2", user_id: "2", full_name: "Bob Smith", email: "bob@example.com" },
    { id: "3", user_id: "3", full_name: "Charlie Brown", email: "charlie@example.com" },
  ]

  it("renders all group members as chips", () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(["1", "2", "3"])

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    expect(screen.getByText("Alice Johnson")).toBeInTheDocument()
    expect(screen.getByText("Bob Smith")).toBeInTheDocument()
    expect(screen.getByText("Charlie Brown")).toBeInTheDocument()
  })

  it("shows correct count in label", () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(["1", "2"]) // Only 2 of 3

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    expect(screen.getByText(/Split between \(2 of 3 selected\)/i)).toBeInTheDocument()
  })

  it("displays included members with full color and checkmark", () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(["1"])

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    const aliceChip = screen.getByText("Alice Johnson").closest("button")
    expect(aliceChip).toHaveClass("border-action")
    expect(aliceChip).not.toHaveClass("opacity-60")
  })

  it("displays excluded members with grayscale and strikethrough", () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(["1", "3"]) // Bob excluded

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    const bobChip = screen.getByText("Bob Smith").closest("button")
    expect(bobChip).toHaveClass("opacity-60")

    const bobName = screen.getByText("Bob Smith")
    expect(bobName).toHaveClass("line-through")
  })

  it("calls onToggleInclude when chip is tapped", () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(["1", "2", "3"])

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    const aliceChip = screen.getByText("Alice Johnson").closest("button")
    fireEvent.click(aliceChip!)

    expect(onToggle).toHaveBeenCalledWith("1")
  })

  it("generates correct initials from full name", () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(["1"])

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    // Alice Johnson -> AJ
    expect(screen.getByText("AJ")).toBeInTheDocument()
    // Bob Smith -> BS
    expect(screen.getByText("BS")).toBeInTheDocument()
  })

  it("handles members without full_name (uses email)", () => {
    const membersWithoutName: GroupMember[] = [
      { id: "1", user_id: "1", full_name: null, email: "alice@unknown.com" },
    ]
    const onToggle = vi.fn()
    const includedMembers = new Set(["1"])

    render(
      <MemberChips
        members={membersWithoutName}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    // Should show email prefix "alice" when no full_name
    expect(screen.getByText("alice")).toBeInTheDocument()
  })

  it("shows 'Tap to toggle' help text", () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(["1"])

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    expect(screen.getByText("Tap to toggle include/exclude")).toBeInTheDocument()
  })
})
