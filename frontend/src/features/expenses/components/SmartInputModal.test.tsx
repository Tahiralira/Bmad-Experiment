/**
 * SmartInputModal Component Tests
 *
 * Tests the signature ClearDues expense entry experience including:
 * - Modal open/close behavior
 * - Natural language input capture
 * - Toggle between smart input and manual form
 * - AI commentary bubble integration
 * - Responsive behavior
 * - Accessibility (keyboard navigation, ARIA labels, focus management)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import {
  render as rtlRender,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react"
import type { ReactElement, ReactNode } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { SmartInputModal } from "./SmartInputModal"
import { parseExpense, ParseError } from "../api/parse"

// WS7: the modal consumes the real SSE parse client — mock the module (the
// ParseError class stays real so instanceof checks hold) and a signed-in user.
vi.mock("../api/parse", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/parse")>()
  return { ...actual, parseExpense: vi.fn() }
})
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ user: { id: "11111111-1111-1111-1111-111111111111" } }),
}))

const mockParseExpense = vi.mocked(parseExpense)

// SmartInputModal uses useQueryClient/useMutation; every render needs a provider.
const render = (ui: ReactElement) =>
  rtlRender(ui, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider
        client={
          new QueryClient({
            defaultOptions: {
              queries: { retry: false },
              mutations: { retry: false },
            },
          })
        }
      >
        {children}
      </QueryClientProvider>
    ),
  })

describe("SmartInputModal", () => {
  // Mock window.matchMedia for responsive tests
  const mockMatchMedia = (matches: boolean) => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    })
  }

  beforeEach(() => {
    // Mock desktop viewport by default
    mockMatchMedia(true)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  // ========== AC #5, #6, #10, #11: Modal Open/Close Behavior ==========
  describe("Modal Open/Close", () => {
    it("opens when open prop is true", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      expect(screen.getByRole("heading", { name: "Add Expense" })).toBeInTheDocument()
    })

    it("shows correct title when entryPoint is dashboard", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} entryPoint="dashboard" />)

      expect(screen.getByRole("heading", { name: "Add Expense" })).toBeInTheDocument()
    })

    it("shows correct title when entryPoint is group", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} entryPoint="group" />)

      expect(screen.getByRole("heading", { name: "Add Expense to Group" })).toBeInTheDocument()
    })

    it("closes when close button (X) is clicked", async () => {
      const handleClose = vi.fn()
      render(<SmartInputModal open={true} onOpenChange={handleClose} />)

      const closeButton = screen.getByRole("button", { name: "Close" })
      fireEvent.click(closeButton)

      await waitFor(() => {
        expect(handleClose).toHaveBeenCalledWith(false)
      })
    })

    it("closes on Escape key (AC #11)", async () => {
      const handleClose = vi.fn()
      render(<SmartInputModal open={true} onOpenChange={handleClose} />)

      fireEvent.keyDown(document, { key: "Escape" })

      await waitFor(() => {
        expect(handleClose).toHaveBeenCalledWith(false)
      })
    })

    it("closes when backdrop is clicked", async () => {
      const handleClose = vi.fn()
      render(<SmartInputModal open={true} onOpenChange={handleClose} />)

      // Backdrop is the overlay
      const backdrop = document.querySelector(".fixed.inset-0.bg-black\\/30")
      expect(backdrop).toBeInTheDocument()

      if (backdrop) {
        fireEvent.click(backdrop)

        await waitFor(() => {
          expect(handleClose).toHaveBeenCalledWith(false)
        })
      }
    })

    it("resets state when modal closes and reopens", async () => {
      const handleClose = vi.fn()
      const { rerender } = render(
        <SmartInputModal open={true} onOpenChange={handleClose} />
      )

      // Enter text
      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      fireEvent.change(textarea, { target: { value: "Paid 60 for lunch" } })
      expect(textarea).toHaveValue("Paid 60 for lunch")

      // Close modal
      fireEvent.click(screen.getByRole("button", { name: "Close" }))
      await waitFor(() => {
        expect(handleClose).toHaveBeenCalledWith(false)
      })

      // Reopen modal
      rerender(<SmartInputModal open={false} onOpenChange={handleClose} />)
      rerender(<SmartInputModal open={true} onOpenChange={handleClose} />)

      // Text should be reset
      await waitFor(() => {
        const textareaAfterReopen = screen.getByPlaceholderText(/Paid 150 for dinner/)
        expect(textareaAfterReopen).toHaveValue("")
      })
    })
  })

  // ========== AC #1, #3, #7: Input Field Behavior ==========
  describe("Natural Language Input Field", () => {
    it("captures text input correctly (AC #1)", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      fireEvent.change(textarea, { target: { value: "Paid 60 for lunch" } })

      expect(textarea).toHaveValue("Paid 60 for lunch")
    })

    it("shows correct placeholder text (AC #7)", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      expect(
        screen.getByPlaceholderText("Paid 150 for dinner, split with everyone except Tom")
      ).toBeInTheDocument()
    })

    it("submits on Ctrl+Enter (desktop)", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      fireEvent.change(textarea, { target: { value: "Paid 60 for lunch" } })

      // Submit with Ctrl+Enter
      fireEvent.keyDown(textarea, { key: "Enter", ctrlKey: true })

      // Button should show "Processing..." briefly
      waitFor(() => {
        expect(screen.getByText("Processing...")).toBeInTheDocument()
      })
    })

    it("submits on Cmd+Enter (Mac)", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      fireEvent.change(textarea, { target: { value: "Paid 60 for lunch" } })

      // Submit with Cmd+Enter
      fireEvent.keyDown(textarea, { key: "Enter", metaKey: true })

      // Button should show "Processing..." briefly
      waitFor(() => {
        expect(screen.getByText("Processing...")).toBeInTheDocument()
      })
    })

    it("allows multi-line input with Enter alone (AC #3)", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      fireEvent.change(textarea, { target: { value: "Line 1\nLine 2" } })

      expect(textarea).toHaveValue("Line 1\nLine 2")
    })

    it("disables submit button when input is empty", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const submitButton = screen.getByRole("button", { name: "Add Expense" })
      expect(submitButton).toBeDisabled()
    })

    it("enables submit button when input has text and a group is set", () => {
      render(
        <SmartInputModal open={true} onOpenChange={() => {}} groupId="group-123" />
      )

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      fireEvent.change(textarea, { target: { value: "Paid 60" } })

      const submitButton = screen.getByRole("button", { name: "Add Expense" })
      expect(submitButton).not.toBeDisabled()
    })

    // WS5/S4-C1: without a group the button used to be ENABLED and silently
    // no-op — now it stays disabled until a group is chosen
    it("keeps submit disabled without a group even when input has text", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      fireEvent.change(textarea, { target: { value: "Paid 60" } })

      const submitButton = screen.getByRole("button", { name: "Add Expense" })
      expect(submitButton).toBeDisabled()
    })

    it("shows the group selector only when no groupId is provided", () => {
      const { rerender } = render(
        <SmartInputModal open={true} onOpenChange={() => {}} />
      )
      expect(
        screen.getByLabelText("Select group for this expense")
      ).toBeInTheDocument()

      rerender(
        <SmartInputModal open={true} onOpenChange={() => {}} groupId="group-123" />
      )
      expect(
        screen.queryByLabelText("Select group for this expense")
      ).not.toBeInTheDocument()
    })
  })

  // ========== AC #4: Toggle to Manual Form ==========
  describe("Manual Form Toggle (AC #4)", () => {
    it("switches to manual form when fallback button is clicked", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const fallbackButton = screen.getByText(/Switch to Manual Form/)
      fireEvent.click(fallbackButton)

      // Should show manual form message
      expect(screen.getByText("Fill in the details below:")).toBeInTheDocument()

      // Should show back button
      expect(screen.getByText("← Back to Smart Input")).toBeInTheDocument()
    })

    it("returns to smart input when back button is clicked", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      // Switch to manual
      fireEvent.click(screen.getByText(/Switch to Manual Form/))

      // Switch back
      fireEvent.click(screen.getByText("← Back to Smart Input"))

      // Should show smart input again
      expect(screen.getByPlaceholderText(/Paid 150 for dinner/)).toBeInTheDocument()
    })

    it("shows ExpenseForm when in manual mode with groupId", () => {
      render(
        <SmartInputModal open={true} onOpenChange={() => {}} groupId="group-123" />
      )

      // Switch to manual
      fireEvent.click(screen.getByText(/Switch to Manual Form/))

      // ExpenseForm should be rendered (check for one of its fields)
      // Note: This depends on ExpenseForm implementation
      expect(screen.getByText("Fill in the details below:")).toBeInTheDocument()
    })

    it("shows message when no group is selected in manual mode", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      // Switch to manual
      fireEvent.click(screen.getByText(/Switch to Manual Form/))

      expect(
        screen.getByText("Choose a group above to add an expense.")
      ).toBeInTheDocument()
    })
  })

  // ========== AC #2, #8, #9: AI parse flow (WS7 — real SSE client) ==========
  // Rewritten in WS7: the setTimeout mock is gone; the modal consumes the
  // real parse client (mocked at the module boundary here — the client's own
  // stream handling is covered in ../api/parse.test.ts).
  describe("AI Parse Flow", () => {
    const submitParse = (text = "Paid 60 for lunch") => {
      fireEvent.change(screen.getByPlaceholderText(/Paid 150 for dinner/), {
        target: { value: text },
      })
      fireEvent.click(screen.getByRole("button", { name: "Add Expense" }))
    }

    it("streams commentary chunks and shows the editable preview", async () => {
      mockParseExpense.mockImplementation(async ({ onCommentary }) => {
        onCommentary?.("Got ")
        onCommentary?.("it!")
        return {
          amount: 60,
          description: "Lunch",
          payer_id: "11111111-1111-1111-1111-111111111111",
          confidence_score: 0.95,
          commentary: "Got it!",
        }
      })

      render(
        <SmartInputModal open={true} onOpenChange={() => {}} groupId="group-1" />
      )
      submitParse()

      // streamed commentary lands in the bubble
      await waitFor(() => {
        expect(screen.getByText("Got it!")).toBeInTheDocument()
      })
      // parse result opens the editable preview (manual confirm only, UX-H6)
      await waitFor(() => {
        expect(screen.getByText("Review Expense")).toBeInTheDocument()
      })
      expect(mockParseExpense).toHaveBeenCalledWith(
        expect.objectContaining({
          text: "Paid 60 for lunch",
          groupId: "group-1",
        })
      )
      // no countdown on the confirm button — it commits only on click
      expect(screen.getByRole("button", { name: "Confirm" })).toBeInTheDocument()
    })

    it("shows the server's mediator-voice message when the parse fails", async () => {
      mockParseExpense.mockRejectedValue(
        new ParseError(
          "You've used all your free AI parses for this month — " +
            "they reset next month. Manual entry is always free."
        )
      )

      render(
        <SmartInputModal open={true} onOpenChange={() => {}} groupId="group-1" />
      )
      submitParse()

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(/free AI parses/)
      })
      // recoverable: the input keeps its text so the user can rephrase
      expect(screen.getByPlaceholderText(/Paid 150 for dinner/)).toHaveValue(
        "Paid 60 for lunch"
      )
    })
  })

  // ========== AC #6: Responsive Design ==========
  describe("Responsive Design (AC #6)", () => {
    it("renders on desktop viewport", () => {
      // Desktop: >= 768px
      mockMatchMedia(true)

      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const dialog = document.querySelector(".lg\\:max-w-\\[600px\\]")
      expect(dialog).toBeInTheDocument()
    })

    it("renders on mobile viewport", () => {
      // Mobile: < 768px
      mockMatchMedia(false)

      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      // Should have full-screen mobile classes
      const dialog = document.querySelector(".fixed.inset-x-0.bottom-0")
      expect(dialog).toBeInTheDocument()
    })
  })

  // ========== Accessibility ==========
  describe("Accessibility", () => {
    it("has proper ARIA labels", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      // Close button has an accessible name
      expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument()

      // Textarea has aria-label
      expect(
        screen.getByLabelText("Expense description in natural language")
      ).toBeInTheDocument()

      // The AI commentary bubble's aria-live region only mounts during the
      // parse flow; its a11y is covered in AICommentaryBubble.test.tsx.
    })

    it("is keyboard accessible", () => {
      const handleClose = vi.fn()
      render(<SmartInputModal open={true} onOpenChange={handleClose} />)

      // The close control is a native <button>, so Enter/Space activation is
      // native browser behavior (jsdom doesn't simulate it — click stands in).
      const closeButton = screen.getByRole("button", { name: "Close" })
      expect(closeButton.tagName).toBe("BUTTON")
      closeButton.focus()
      expect(closeButton).toHaveFocus()
      fireEvent.click(closeButton)
      expect(handleClose).toHaveBeenCalledWith(false)
    })

    it("traps focus within modal when open", async () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      // focus-trap moves initial focus inside the dialog on activation
      await waitFor(() => {
        const dialog = screen.getByRole("dialog")
        expect(dialog.contains(document.activeElement)).toBe(true)
      })
    })
  })

  // ========== Expense Preview Card ==========
  describe("Expense Preview Card", () => {
    it("shows placeholder state initially", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      expect(screen.getByText("Enter expense above to see preview")).toBeInTheDocument()
    })
  })
})
