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

  it("disabled cards show coming soon message", () => {
    render(<SplitPicker selectedType={"equal" as SplitType} onSelectType={() => {}} />)

    expect(screen.getByText("Coming in Story 3.6")).toBeInTheDocument()
    expect(screen.getByText("Coming in Story 3.7")).toBeInTheDocument()
    expect(screen.getByText("Coming in Story 3.8")).toBeInTheDocument()
  })

  it("disabled cards are not clickable", () => {
    const onSelectType = vi.fn()
    render(<SplitPicker selectedType={"equal" as SplitType} onSelectType={onSelectType} />)

    const unequalCard = screen.getByText("Unequal").closest("button")
    expect(unequalCard).toBeDisabled()
  })
})
