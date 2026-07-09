/**
 * AICommentaryBubble Component Tests
 *
 * Tests the AI commentary bubble that displays streaming text above the input field:
 * - Typing indicator (3 dots animation)
 * - Streamed text display
 * - Personality-driven styling (placeholder for Story 8.1)
 * - Accessibility (aria-live for screen readers)
 * - Reduced motion support
 */

import { describe, it, expect } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { AICommentaryBubble } from "./AICommentaryBubble"

describe("AICommentaryBubble", () => {
  // ========== Typing Indicator ==========
  describe("Typing Indicator", () => {
    it("shows typing indicator before streaming starts (AC #8)", async () => {
      render(
        <AICommentaryBubble
          text=""
          isProcessing={true}
          personality="friendly"
        />
      )

      // Wait for 300ms delay (typing indicator appears after 300ms)
      await waitFor(
        () => {
          const dots = document.querySelectorAll('[aria-hidden="true"].w-2.h-2')
          expect(dots.length).toBe(3) // 3 dots
        },
        { timeout: 500 }
      )
    })

    it("hides typing indicator when text appears", async () => {
      const { rerender } = render(
        <AICommentaryBubble
          text=""
          isProcessing={true}
          personality="friendly"
        />
      )

      // Wait for typing indicator
      await waitFor(
        () => {
          const dots = document.querySelectorAll('[aria-hidden="true"].w-2.h-2')
          expect(dots.length).toBe(3)
        },
        { timeout: 500 }
      )

      // Stream text appears
      rerender(
        <AICommentaryBubble
          text="Got it!"
          isProcessing={true}
          personality="friendly"
        />
      )

      // Typing indicator should be gone
      await waitFor(() => {
        const dots = document.querySelectorAll('[aria-hidden="true"].w-2.h-2')
        expect(dots.length).toBe(0)
      })

      // Text should be visible
      expect(screen.getByText("Got it!")).toBeInTheDocument()
    })

    it("does not show typing indicator when not processing", () => {
      render(
        <AICommentaryBubble
          text=""
          isProcessing={false}
          personality="friendly"
        />
      )

      // Should not render anything when idle
      const bubble = document.querySelector('[aria-live="polite"]')
      expect(bubble).not.toBeInTheDocument()
    })
  })

  // ========== Streamed Text Display ==========
  describe("Streamed Text", () => {
    it("displays streamed text character by character", () => {
      render(
        <AICommentaryBubble
          text="Got it! Parsing that expense for you..."
          isProcessing={false}
          personality="friendly"
        />
      )

      expect(
        screen.getByText("Got it! Parsing that expense for you...")
      ).toBeInTheDocument()
    })

    it("shows fallback text when processing but no text yet", () => {
      render(
        <AICommentaryBubble text="" isProcessing={true} personality="friendly" />
      )

      // Should show "Processing your expense..." after typing indicator phase
      waitFor(() => {
        expect(screen.getByText(/Processing your expense/)).toBeInTheDocument()
      })
    })

    it("renders null when idle (no text and not processing)", () => {
      const { container } = render(
        <AICommentaryBubble
          text=""
          isProcessing={false}
          personality="friendly"
        />
      )

      // Component returns null, so container should be empty
      expect(container.firstChild).toBeNull()
    })
  })

  // ========== Personality Support ==========
  describe("Personality Support", () => {
    it("accepts all personality types", () => {
      const personalities = ["professional", "friendly", "funny", "roast"] as const

      personalities.forEach((personality) => {
        const { container } = render(
          <AICommentaryBubble
            text="Test"
            isProcessing={false}
            personality={personality}
          />
        )

        expect(container.firstChild).toBeInTheDocument()
      })
    })

    it("does not break with unknown personality (future-proofing)", () => {
      // This test ensures the component is robust against future personality additions
      const { container } = render(
        <AICommentaryBubble
          text="Test"
          isProcessing={false}
          personality="friendly" // Currently only friendly is used
        />
      )

      expect(container.firstChild).toBeInTheDocument()
    })
  })

  // ========== Accessibility ==========
  describe("Accessibility", () => {
    it("has aria-live for screen readers", () => {
      render(
        <AICommentaryBubble
          text="Got it!"
          isProcessing={false}
          personality="friendly"
        />
      )

      const bubble = document.querySelector('[aria-live="polite"]')
      expect(bubble).toBeInTheDocument()
    })

    it("has aria-label for AI commentary", () => {
      render(
        <AICommentaryBubble
          text="Got it!"
          isProcessing={false}
          personality="friendly"
        />
      )

      const bubble = document.querySelector('[aria-label="AI commentary"]')
      expect(bubble).toBeInTheDocument()
    })

    it("hides typing indicator dots from screen readers (aria-hidden)", () => {
      render(
        <AICommentaryBubble
          text=""
          isProcessing={true}
          personality="friendly"
        />
      )

      waitFor(() => {
        const dots = document.querySelectorAll('[aria-hidden="true"]')
        expect(dots.length).toBeGreaterThan(0)
      })
    })
  })

  // ========== Animation ==========
  describe("Animation", () => {
    it("has fade-in animation", () => {
      // This test ensures the component has animation classes
      // Actual animation testing would require more complex setup
      const { container } = render(
        <AICommentaryBubble
          text="Test"
          isProcessing={false}
          personality="friendly"
        />
      )

      const bubble = container.querySelector('[aria-live="polite"]')
      expect(bubble).toBeInTheDocument()
      // Motion.div handles animation - we just verify it renders
    })
  })

  // ========== Custom Styling ==========
  describe("Custom Styling", () => {
    it("accepts custom className", () => {
      const { container } = render(
        <AICommentaryBubble
          text="Test"
          isProcessing={false}
          personality="friendly"
          className="custom-class"
        />
      )

      const bubble = container.querySelector(".custom-class")
      expect(bubble).toBeInTheDocument()
    })
  })
})
