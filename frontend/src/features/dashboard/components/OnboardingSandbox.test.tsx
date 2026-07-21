/**
 * OnboardingSandbox tests (WS10.4 / S2 §6)
 *
 * The organic-path "try one expense" aha: a real hosted parse with NO group
 * (sandbox), a read-only preview of what the AI read, a mediator-voice error
 * path, and a next-action CTA that's always present.
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"

const { mockParseExpense } = vi.hoisted(() => ({ mockParseExpense: vi.fn() }))

// Router Link → plain anchor (no router context in unit tests).
vi.mock("@tanstack/react-router", () => ({
  Link: ({ to, children, ...props }: Record<string, unknown>) => (
    <a href={typeof to === "string" ? to : "#"} {...props}>
      {children as React.ReactNode}
    </a>
  ),
}))

vi.mock("@/features/expenses/api/parse", () => {
  class ParseError extends Error {}
  return {
    ParseError,
    parseExpense: (opts: unknown) => mockParseExpense(opts),
  }
})

import { OnboardingSandbox } from "./OnboardingSandbox"
import { ParseError } from "@/features/expenses/api/parse"

describe("OnboardingSandbox", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("shows the welcome, a disabled Try it, and an always-present create CTA", () => {
    render(<OnboardingSandbox />)

    expect(screen.getByText(/Welcome to ClearDues/i)).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /try it/i }),
    ).toBeDisabled()
    // Empty state always names the next action.
    expect(
      screen.getByRole("link", { name: /create your first group/i }),
    ).toBeInTheDocument()
  })

  it("parses without a group and shows what the AI read", async () => {
    mockParseExpense.mockImplementation(async (opts: { onCommentary?: (c: string) => void }) => {
      opts.onCommentary?.("Got it! ")
      return {
        amount: 40,
        description: "Pizza",
        payer_id: "u1",
        confidence_score: 0.95,
        commentary: "Got it!",
      }
    })

    render(<OnboardingSandbox />)

    fireEvent.change(screen.getByLabelText(/describe an expense/i), {
      target: { value: "Paid 40 for pizza with Sam" },
    })
    fireEvent.click(screen.getByRole("button", { name: /try it/i }))

    await waitFor(() =>
      expect(screen.getByText(/here's what i read/i)).toBeInTheDocument(),
    )
    expect(screen.getByText("Pizza")).toBeInTheDocument()
    // Amount rendered through formatCurrency (jsdom locale → USD "$40.00").
    expect(screen.getByText(/40\.00/)).toBeInTheDocument()

    // Sandbox: parseExpense was called WITHOUT a groupId.
    const arg = mockParseExpense.mock.calls[0][0]
    expect(arg.text).toBe("Paid 40 for pizza with Sam")
    expect(arg.groupId).toBeUndefined()
  })

  it("surfaces a mediator-voice error when the parse fails", async () => {
    mockParseExpense.mockRejectedValue(
      new ParseError("You've used all your free AI parses for this month."),
    )

    render(<OnboardingSandbox />)
    fireEvent.change(screen.getByLabelText(/describe an expense/i), {
      target: { value: "gibberish" },
    })
    fireEvent.click(screen.getByRole("button", { name: /try it/i }))

    const alert = await screen.findByRole("alert")
    expect(alert).toHaveTextContent(/free AI parses/i)
  })
})
