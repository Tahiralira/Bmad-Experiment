/**
 * ExpensePreviewCard Component Tests
 *
 * Tests the expense preview card that displays parsed expense data:
 * - Placeholder state (Story 3.2)
 * - Loading state (Story 3.4 - skeleton)
 * - Ready state (Story 3.4 - actual data)
 * - Error state (Story 3.4)
 */

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { ExpensePreviewCard } from "./ExpensePreviewCard"

describe("ExpensePreviewCard", () => {
  // ========== Placeholder State (Story 3.2) ==========
  describe("Placeholder State", () => {
    it("shows placeholder text when status is placeholder", () => {
      render(<ExpensePreviewCard data={null} status="placeholder" />)

      expect(screen.getByText("Enter expense above to see preview")).toBeInTheDocument()
    })

    it("has correct styling for placeholder state", () => {
      const { container } = render(
        <ExpensePreviewCard data={null} status="placeholder" />
      )

      const card = container.querySelector(".mt-4.p-6.rounded-lg")
      expect(card).toBeInTheDocument()
    })

    it("renders placeholder when data is null and status is placeholder", () => {
      const { container } = render(
        <ExpensePreviewCard data={null} status="placeholder" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })
  })

  // ========== Loading State (Story 3.4) ==========
  describe("Loading State (Story 3.4)", () => {
    it("shows loading skeleton when status is loading", () => {
      const { container } = render(<ExpensePreviewCard data={null} status="loading" />)

      // Should have pulse animation
      const skeleton = container.querySelector(".animate-pulse")
      expect(skeleton).toBeInTheDocument()
    })

    it("shows multiple skeleton lines for loading state", () => {
      const { container } = render(<ExpensePreviewCard data={null} status="loading" />)

      // Should have 3 skeleton bars (h-4 bg-muted)
      const bars = container.querySelectorAll(".h-4.bg-muted")
      expect(bars.length).toBe(3)
    })
  })

  // ========== Ready/Error States (Story 3.4) ==========
  describe("Ready State (Story 3.4)", () => {
    it("returns null when status is ready (not implemented yet)", () => {
      const { container } = render(
        <ExpensePreviewCard data={null} status="ready" />
      )

      // Story 3.4: Will display parsed expense details
      // For now, returns null
      expect(container.firstChild).toBeNull()
    })
  })

  describe("Error State (Story 3.4)", () => {
    it("shows error message when status is error (Story 3.4)", () => {
      render(<ExpensePreviewCard data={null} status="error" />)

      expect(
        screen.getByText(/Failed to parse expense/)
      ).toBeInTheDocument()
    })
  })

  // ========== Custom Styling ==========
  describe("Custom Styling", () => {
    it("accepts custom className", () => {
      const { container } = render(
        <ExpensePreviewCard data={null} status="placeholder" className="custom-class" />
      )

      const card = container.querySelector(".custom-class")
      expect(card).toBeInTheDocument()
    })
  })

  // ========== Data Prop (Future Use) ==========
  describe("Data Prop", () => {
    it("accepts data prop but doesn't use it yet (Story 3.2)", () => {
      // Data prop is typed as `null` in Story 3.2
      // Will be used in Story 3.4 for parsed expense data
      const { container } = render(
        <ExpensePreviewCard data={null} status="placeholder" />
      )

      expect(container.firstChild).toBeInTheDocument()
    })

    it("has placeholder comment about future data usage", () => {
      // This test documents that data prop will be used in Story 3.4
      const { container } = render(
        <ExpensePreviewCard data={null} status="placeholder" />
      )

      // Component renders successfully with null data
      expect(container.firstChild).toBeInTheDocument()
    })
  })
})
