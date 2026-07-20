/**
 * PairwiseBalances tests (WS6/S2-F9)
 *
 * The "who owes whom exactly" rows and the two-step "Settle up" flow —
 * the UI entry point for aggregate settle-up.
 */

import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

import { PairwiseBalances } from "./PairwiseBalances"
import type { PairwiseBalanceItem } from "../types"

const mockUsePairwiseBalances = vi.fn()
const mockSettleUpMutate = vi.fn()

vi.mock("../api/groups", () => ({
  usePairwiseBalances: (groupId: string) => mockUsePairwiseBalances(groupId),
}))

vi.mock("@/features/expenses/api/expenses", () => ({
  useSettleUp: () => ({ mutate: mockSettleUpMutate, isPending: false }),
}))

const GROUP_ID = "11111111-1111-1111-1111-111111111111"

function setBalances(items: PairwiseBalanceItem[]) {
  mockUsePairwiseBalances.mockReturnValue({
    data: { data: items, count: items.length },
    isLoading: false,
    error: null,
  })
}

const theyOweRow: PairwiseBalanceItem = {
  user_id: "aaaa1111-0000-0000-0000-000000000001",
  user_name: "Alex",
  they_owe_you: "600.00",
  you_owe_them: "0.00",
  net: "600.00",
}

const youOweRow: PairwiseBalanceItem = {
  user_id: "aaaa1111-0000-0000-0000-000000000002",
  user_name: "Sam",
  they_owe_you: "20.00",
  you_owe_them: "50.00",
  net: "-30.00",
}

describe("PairwiseBalances", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("shows the net amount without a settle button when they owe you", () => {
    setBalances([theyOweRow])
    render(
      <PairwiseBalances groupId={GROUP_ID} pendingCounterpartyIds={new Set()} />,
    )

    // No CurrencyProvider wraps the render → formatCurrency uses the USD
    // default (WS10.1). Group-scoped screens supply the real currency.
    expect(screen.getByText("Alex")).toBeInTheDocument()
    expect(screen.getByText("$600.00")).toBeInTheDocument()
    expect(screen.getByText(/owes you \$600\.00/i)).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /settle up/i })).toBeNull()
  })

  it("nets both directions in the row copy when you owe", () => {
    setBalances([youOweRow])
    render(
      <PairwiseBalances groupId={GROUP_ID} pendingCounterpartyIds={new Set()} />,
    )

    expect(
      screen.getByText(/you owe \$50\.00 · they owe \$20\.00/i),
    ).toBeInTheDocument()
  })

  it("settles up via the two-step confirm", () => {
    setBalances([youOweRow])
    render(
      <PairwiseBalances groupId={GROUP_ID} pendingCounterpartyIds={new Set()} />,
    )

    // Step 1: the intent
    fireEvent.click(screen.getByRole("button", { name: /settle up with sam/i }))
    // Nothing sent yet — manual confirm only (product constitution)
    expect(mockSettleUpMutate).not.toHaveBeenCalled()
    expect(screen.getByText(/paid sam \$30\.00\?/i)).toBeInTheDocument()

    // Step 2: the confirmation
    fireEvent.click(screen.getByRole("button", { name: /yes, i paid/i }))
    expect(mockSettleUpMutate).toHaveBeenCalledWith(
      {
        group_id: GROUP_ID,
        counterparty_user_id: youOweRow.user_id,
      },
      expect.anything(),
    )
  })

  it("cancel backs out without sending anything", () => {
    setBalances([youOweRow])
    render(
      <PairwiseBalances groupId={GROUP_ID} pendingCounterpartyIds={new Set()} />,
    )

    fireEvent.click(screen.getByRole("button", { name: /settle up with sam/i }))
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }))

    expect(mockSettleUpMutate).not.toHaveBeenCalled()
    expect(
      screen.getByRole("button", { name: /settle up with sam/i }),
    ).toBeInTheDocument()
  })

  it("shows the in-flight state instead of a button when a settle-up is pending", () => {
    setBalances([youOweRow])
    render(
      <PairwiseBalances
        groupId={GROUP_ID}
        pendingCounterpartyIds={new Set([youOweRow.user_id])}
      />,
    )

    expect(screen.getByText(/settle-up pending/i)).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /settle up/i })).toBeNull()
  })

  it("shows the calm empty state when nothing is outstanding", () => {
    setBalances([])
    render(
      <PairwiseBalances groupId={GROUP_ID} pendingCounterpartyIds={new Set()} />,
    )

    expect(
      screen.getByText(/nothing outstanding between you and anyone here/i),
    ).toBeInTheDocument()
  })
})
