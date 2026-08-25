/**
 * PushPermissionPrompt tests (WS10.7 delivered in WS12).
 *
 * A browser grants the notification-permission prompt ONCE, and a denial is
 * effectively permanent. Every test here guards one of the conditions that
 * must hold before the app is allowed to spend it.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

const { mockVapid, mockRegister, mockSubscribe, mockSupport, mockPermission } =
  vi.hoisted(() => ({
    mockVapid: vi.fn(),
    mockRegister: vi.fn(),
    mockSubscribe: vi.fn(),
    mockSupport: vi.fn(),
    mockPermission: vi.fn(),
  }))

vi.mock("../api/notifications", () => ({
  useVapidPublicKey: () => mockVapid(),
  useRegisterPushSubscription: () => ({ mutate: mockRegister }),
}))

vi.mock("../lib/push", () => ({
  checkPushSupport: () => mockSupport(),
  getPermission: () => mockPermission(),
  subscribeToPush: (key: string) => mockSubscribe(key),
}))

import { PushPermissionPrompt } from "./PushPermissionPrompt"

const OFFER = /Want ClearDues to keep track for you\?/i

describe("PushPermissionPrompt", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    mockSupport.mockReturnValue({ supported: true })
    mockPermission.mockReturnValue("default")
    mockVapid.mockReturnValue({ data: { key: "a-public-key" } })
  })

  it("offers reminders once there is a balance to be reminded about", () => {
    render(<PushPermissionPrompt eligible={true} />)
    expect(screen.getByText(OFFER)).toBeInTheDocument()
  })

  it("stays silent before the user has any open balance", () => {
    render(<PushPermissionPrompt eligible={false} />)
    expect(screen.queryByText(OFFER)).not.toBeInTheDocument()
  })

  it("stays silent when the server has no VAPID key — the prompt would be wasted", () => {
    mockVapid.mockReturnValue({ data: { key: null } })
    render(<PushPermissionPrompt eligible={true} />)
    expect(screen.queryByText(OFFER)).not.toBeInTheDocument()
  })

  it("stays silent when the browser cannot do push", () => {
    mockSupport.mockReturnValue({ supported: false, reason: "no-push-api" })
    render(<PushPermissionPrompt eligible={true} />)
    expect(screen.queryByText(OFFER)).not.toBeInTheDocument()
  })

  it("never re-asks once the browser has already answered", () => {
    mockPermission.mockReturnValue("denied")
    render(<PushPermissionPrompt eligible={true} />)
    expect(screen.queryByText(OFFER)).not.toBeInTheDocument()

    mockPermission.mockReturnValue("granted")
    render(<PushPermissionPrompt eligible={true} />)
    expect(screen.queryByText(OFFER)).not.toBeInTheDocument()
  })

  it("registers the subscription with the server when the user accepts", async () => {
    const subscription = {
      endpoint: "https://push.example.com/x",
      p256dh: "k",
      auth: "a",
    }
    mockSubscribe.mockResolvedValue(subscription)

    render(<PushPermissionPrompt eligible={true} />)
    fireEvent.click(screen.getByRole("button", { name: /remind me/i }))

    await waitFor(() => {
      expect(mockSubscribe).toHaveBeenCalledWith("a-public-key")
      expect(mockRegister).toHaveBeenCalledWith(subscription)
    })
  })

  it("does not register anything when the user denies the browser prompt", async () => {
    mockSubscribe.mockResolvedValue(null)

    render(<PushPermissionPrompt eligible={true} />)
    fireEvent.click(screen.getByRole("button", { name: /remind me/i }))

    await waitFor(() => expect(mockSubscribe).toHaveBeenCalled())
    expect(mockRegister).not.toHaveBeenCalled()
    // The ask is spent either way — asking again after a denial is nagging.
    await waitFor(() =>
      expect(screen.queryByText(OFFER)).not.toBeInTheDocument(),
    )
  })

  it("remembers a dismissal across mounts", async () => {
    const { unmount } = render(<PushPermissionPrompt eligible={true} />)
    fireEvent.click(screen.getByRole("button", { name: /not now/i }))
    expect(screen.queryByText(OFFER)).not.toBeInTheDocument()
    unmount()

    render(<PushPermissionPrompt eligible={true} />)
    await waitFor(() =>
      expect(screen.queryByText(OFFER)).not.toBeInTheDocument(),
    )
  })
})
