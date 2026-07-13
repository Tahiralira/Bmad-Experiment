/**
 * AggregateClaimCard tests (WS6)
 *
 * One aggregate settle-up claim, seen from both sides: the counterparty
 * reviews (Confirm/Reject + 72h auto-confirm note), the claimant waits.
 */

import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

import { AggregateClaimCard } from "./AggregateClaimCard"
import type { SettlementClaimPublic } from "../types"

const mockConfirmMutate = vi.fn()
const mockRejectMutate = vi.fn()

vi.mock("../api/expenses", () => ({
  useConfirmSettlement: () => ({
    mutate: mockConfirmMutate,
    isPending: false,
    isError: false,
  }),
  useRejectSettlement: () => ({
    mutate: mockRejectMutate,
    isPending: false,
    isError: false,
  }),
}))

const CLAIMANT_ID = "aaaa1111-0000-0000-0000-000000000001"
const COUNTERPARTY_ID = "aaaa1111-0000-0000-0000-000000000002"

const claim: SettlementClaimPublic = {
  id: "cccc1111-0000-0000-0000-000000000001",
  expense_split_id: null,
  claimant_user_id: CLAIMANT_ID,
  amount: "600.00",
  status: "pending",
  claimed_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  confirmed_at: null,
  rejected_at: null,
  created_at: new Date().toISOString(),
  user_name: "Sam",
  group_id: "11111111-1111-1111-1111-111111111111",
  counterparty_user_id: COUNTERPARTY_ID,
  counterparty_name: "Alex",
  covered_split_count: 12,
  covered_expense_count: 12,
  auto_confirm_at: new Date(Date.now() + 71 * 60 * 60 * 1000).toISOString(),
}

describe("AggregateClaimCard", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("lets the counterparty review: names, coverage, net, countdown", () => {
    render(<AggregateClaimCard claim={claim} currentUserId={COUNTERPARTY_ID} />)

    expect(screen.getByText("Settle-up from Sam")).toBeInTheDocument()
    expect(
      screen.getByText(/paid you the net across 12 expenses/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/auto-confirms in 2 days/i)).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /confirm settle-up from sam/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /reject settle-up from sam/i }),
    ).toBeInTheDocument()
  })

  it("confirm fires the settlement mutation with the claim id", () => {
    render(<AggregateClaimCard claim={claim} currentUserId={COUNTERPARTY_ID} />)

    fireEvent.click(
      screen.getByRole("button", { name: /confirm settle-up from sam/i }),
    )
    expect(mockConfirmMutate).toHaveBeenCalledWith(claim.id)
  })

  it("reject fires the reject mutation", () => {
    render(<AggregateClaimCard claim={claim} currentUserId={COUNTERPARTY_ID} />)

    fireEvent.click(
      screen.getByRole("button", { name: /reject settle-up from sam/i }),
    )
    expect(mockRejectMutate).toHaveBeenCalledWith(claim.id)
  })

  it("shows the claimant a waiting state with no actions", () => {
    render(<AggregateClaimCard claim={claim} currentUserId={CLAIMANT_ID} />)

    expect(screen.getByText("Settle-up with Alex")).toBeInTheDocument()
    expect(
      screen.getByText(/waiting on alex to confirm/i),
    ).toBeInTheDocument()
    expect(screen.queryByRole("button")).toBeNull()
  })
})
