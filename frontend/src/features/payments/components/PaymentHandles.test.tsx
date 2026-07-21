/**
 * PaymentHandles tests (WS10.2)
 *
 * The counterparty payment surface shown at settle time: a "Pay" deep link
 * where one exists, always a Copy button, and a calm empty state.
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"

import { PaymentHandles } from "./PaymentHandles"
import type { PaymentMethod } from "../types"

const mockUseCounterparty = vi.fn()

vi.mock("../api/payments", () => ({
  useCounterpartyPaymentMethods: (
    groupId: string,
    userId: string,
    enabled: boolean,
  ) => mockUseCounterparty(groupId, userId, enabled),
}))

const GROUP_ID = "11111111-1111-1111-1111-111111111111"
const USER_ID = "22222222-2222-2222-2222-222222222222"

const venmo: PaymentMethod = {
  id: "m1",
  provider: "venmo",
  provider_name: "Venmo",
  handle: "@alice",
  label: null,
  pay_url: "https://venmo.com/u/alice",
}

const iban: PaymentMethod = {
  id: "m2",
  provider: "iban",
  provider_name: "Bank transfer (IBAN)",
  handle: "GB33BUKB20201555555555",
  label: "Main account",
  pay_url: null,
}

function setMethods(methods: PaymentMethod[], overrides = {}) {
  mockUseCounterparty.mockReturnValue({
    data: { data: methods, count: methods.length },
    isLoading: false,
    error: null,
    ...overrides,
  })
}

function renderIt() {
  return render(
    <PaymentHandles
      groupId={GROUP_ID}
      counterpartyUserId={USER_ID}
      counterpartyName="Alice"
    />,
  )
}

describe("PaymentHandles", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renders a Pay deep link for a provider that supports one", () => {
    setMethods([venmo])
    renderIt()

    expect(screen.getByText("Pay Alice")).toBeInTheDocument()
    const link = screen.getByRole("link", { name: /pay via venmo/i })
    expect(link).toHaveAttribute("href", "https://venmo.com/u/alice")
    expect(link).toHaveAttribute("target", "_blank")
    expect(link).toHaveAttribute("rel", "noopener noreferrer")
  })

  it("shows copy-only (no Pay link) for IBAN and renders its label", () => {
    setMethods([iban])
    renderIt()

    expect(screen.queryByRole("link")).toBeNull()
    expect(screen.getByText(/Main account · GB33BUKB20201555555555/)).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /copy bank transfer/i }),
    ).toBeInTheDocument()
  })

  it("copies the handle to the clipboard", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    setMethods([venmo])
    renderIt()

    fireEvent.click(screen.getByRole("button", { name: /copy venmo/i }))
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("@alice"))
    expect(await screen.findByText("Copied")).toBeInTheDocument()
  })

  it("shows a helpful empty state when the payee has no handles", () => {
    setMethods([])
    renderIt()

    expect(
      screen.getByText(/Alice hasn't added a payment method yet/i),
    ).toBeInTheDocument()
  })

  it("renders nothing loud while loading", () => {
    setMethods([], { isLoading: true, data: undefined })
    renderIt()

    expect(screen.getByText(/loading payment options/i)).toBeInTheDocument()
  })
})
