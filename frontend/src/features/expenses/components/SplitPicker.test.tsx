import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { SplitPicker } from "./SplitPicker"
import type { SplitType } from "../types"

describe("SplitPicker", () => {
  it("renders all 4 split type cards", () => {
    const onSelectType = vi.fn()
    render(<SplitPicker selectedType={"equal" as SplitType} onSelectType={onSelectType} />)

    expect(screen.getByText("Equal")).toBeInTheDocument()
    expect(screen.getByText("Unequal")).toBeInTheDocument()
    expect(screen.getByText("Percentage")).toBeInTheDocument()
    expect(screen.getByText("Shares")).toBeInTheDocument()
  })

  it("selects Equal split by default", () => {
    const onSelectType = vi.fn()
    render(<SplitPicker selectedType={"equal" as SplitType} onSelectType={onSelectType} />)

    const equalCard = screen.getByText("Equal").closest("button")
    expect(equalCard).toHaveClass("border-action")
  })

  it("calls onSelectType when a card is clicked", () => {
    const onSelectType = vi.fn()
    render(<SplitPicker selectedType={"equal" as SplitType} onSelectType={onSelectType} />)

    const equalCard = screen.getByText("Equal").closest("button")
    fireEvent.click(equalCard!)

    expect(onSelectType).toHaveBeenCalledWith("equal")
  })

  it("has no gated cards — every split type is live (audit F13)", () => {
    render(<SplitPicker selectedType={"equal" as SplitType} onSelectType={() => {}} />)

    // Shares shipped, so no card carries a "Coming in Story ..." message.
    expect(screen.queryByText(/Coming in Story/i)).not.toBeInTheDocument()
  })

  it("selects the Shares split when its card is clicked", () => {
    const onSelectType = vi.fn()
    render(<SplitPicker selectedType={"equal" as SplitType} onSelectType={onSelectType} />)

    const sharesCard = screen.getByText("Shares").closest("button")
    expect(sharesCard).not.toBeDisabled()
    fireEvent.click(sharesCard!)
    expect(onSelectType).toHaveBeenCalledWith("shares")
  })
})
