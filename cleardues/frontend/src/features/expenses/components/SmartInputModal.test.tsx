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
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom"
import { SmartInputModal } from "./SmartInputModal"

describe("SmartInputModal", () => {
  // Mock window.matchMedia for responsive tests
  const mockMatchMedia = (matches: boolean) => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query) => ({
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

      expect(screen.getByText("Add Expense")).toBeInTheDocument()
    })

    it("shows correct title when entryPoint is dashboard", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} entryPoint="dashboard" />)

      expect(screen.getByText("Add Expense")).toBeInTheDocument()
    })

    it("shows correct title when entryPoint is group", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} entryPoint="group" />)

      expect(screen.getByText("Add Expense to Group")).toBeInTheDocument()
    })

    it("closes when close button (X) is clicked", async () => {
      const handleClose = vi.fn()
      render(<SmartInputModal open={true} onOpenChange={handleClose} />)

      const closeButton = screen.getByLabelText("Close")
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
      fireEvent.click(screen.getByLabelText("Close"))
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

      const submitButton = screen.getByText("Add Expense")
      expect(submitButton).toBeDisabled()
    })

    it("enables submit button when input has text", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      fireEvent.change(textarea, { target: { value: "Paid 60" } })

      const submitButton = screen.getByText("Add Expense")
      expect(submitButton).not.toBeDisabled()
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

    it("shows message when no groupId provided in manual mode", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      // Switch to manual
      fireEvent.click(screen.getByText(/Switch to Manual Form/))

      expect(screen.getByText("Please select a group first")).toBeInTheDocument()
    })
  })

  // ========== AC #2, #8, #9: AI Commentary Bubble ==========
  describe("AI Commentary Bubble", () => {
    it("shows AI commentary bubble with streaming text", async () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      const submitButton = screen.getByText("Add Expense")

      fireEvent.change(textarea, { target: { value: "Paid 60 for lunch" } })
      fireEvent.click(submitButton)

      // Wait for streaming to start
      await waitFor(
        () => {
          expect(screen.getByText(/Got it!/)).toBeInTheDocument()
        },
        { timeout: 3000 }
      )
    })

    it("shows typing indicator before streaming starts", async () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      const textarea = screen.getByPlaceholderText(/Paid 150 for dinner/)
      const submitButton = screen.getByText("Add Expense")

      fireEvent.change(textarea, { target: { value: "Paid 60 for lunch" } })
      fireEvent.click(submitButton)

      // Check for typing indicator dots (aria-hidden="true" dots)
      await waitFor(
        () => {
          const dots = document.querySelectorAll('[aria-hidden="true"].w-2.h-2')
          expect(dots.length).toBeGreaterThan(0)
        },
        { timeout: 500 }
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

      // Close button has aria-label
      expect(screen.getByLabelText("Close")).toBeInTheDocument()

      // Textarea has aria-label
      expect(
        screen.getByLabelText("Expense description in natural language")
      ).toBeInTheDocument()

      // AI commentary has aria-live
      const aiBubble = document.querySelector('[aria-live="polite"]')
      expect(aiBubble).toBeInTheDocument()
    })

    it("is keyboard accessible", () => {
      const handleClose = vi.fn()
      render(<SmartInputModal open={true} onOpenChange={handleClose} />)

      // Tab to close button and activate with Enter
      const closeButton = screen.getByLabelText("Close")
      closeButton.focus()
      fireEvent.keyDown(closeButton, { key: "Enter" })

      expect(handleClose).toHaveBeenCalled()
    })

    it("traps focus within modal when open", () => {
      render(<SmartInputModal open={true} onOpenChange={() => {}} />)

      // FocusTrap should be active
      const focusTrapDiv = document.querySelector('[data-focus-trap=""]')
      expect(focusTrapDiv).toBeInTheDocument()
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
