/**
 * CreateGroupForm template tests (WS10.4 / S2 §6)
 *
 * Onboarding templates preset the name + the social contract (strict_mode)
 * with one tap, without clobbering a name the user typed themselves.
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"

const { mockMutateAsync, mockNavigate } = vi.hoisted(() => ({
  mockMutateAsync: vi.fn(),
  mockNavigate: vi.fn(),
}))

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => mockNavigate,
}))

vi.mock("../api/groups", () => ({
  useCreateGroup: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
}))

vi.mock("@/shared/hooks/useCustomToast", () => ({
  useCustomToast: () => ({
    showSuccessToast: vi.fn(),
    showErrorToast: vi.fn(),
  }),
}))

import { CreateGroupForm } from "./CreateGroupForm"

describe("CreateGroupForm templates", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockMutateAsync.mockResolvedValue(undefined)
  })

  it("prefills the name and shows the blurb when a template is picked", () => {
    render(<CreateGroupForm />)

    const chip = screen.getByRole("button", { name: /roommates/i })
    fireEvent.click(chip)

    expect(chip).toHaveAttribute("aria-pressed", "true")
    expect(screen.getByLabelText(/group name/i)).toHaveValue("Roommates")
    expect(
      screen.getByText(/expenses confirm quietly/i),
    ).toBeInTheDocument()
  })

  it("sends strict_mode from the chosen template on submit", async () => {
    render(<CreateGroupForm />)
    fireEvent.click(screen.getByRole("button", { name: /trip/i }))
    fireEvent.click(screen.getByRole("button", { name: /^create group$/i }))

    await waitFor(() => expect(mockMutateAsync).toHaveBeenCalledTimes(1))
    const body = mockMutateAsync.mock.calls[0][0]
    expect(body.name).toBe("Trip")
    expect(body.strict_mode).toBe(false)
  })

  it("omits strict_mode entirely when no template is chosen", async () => {
    render(<CreateGroupForm />)
    fireEvent.change(screen.getByLabelText(/group name/i), {
      target: { value: "Book Club" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^create group$/i }))

    await waitFor(() => expect(mockMutateAsync).toHaveBeenCalledTimes(1))
    const body = mockMutateAsync.mock.calls[0][0]
    expect(body.name).toBe("Book Club")
    expect(body).not.toHaveProperty("strict_mode")
  })

  it("does not overwrite a name the user already typed", () => {
    render(<CreateGroupForm />)
    fireEvent.change(screen.getByLabelText(/group name/i), {
      target: { value: "Ski House 2026" },
    })
    fireEvent.click(screen.getByRole("button", { name: /dinner/i }))

    expect(screen.getByLabelText(/group name/i)).toHaveValue("Ski House 2026")
  })
})
