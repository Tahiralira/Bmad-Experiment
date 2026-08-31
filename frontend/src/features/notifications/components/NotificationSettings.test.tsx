/**
 * NotificationSettings — the per-relationship ladder status (WS13).
 *
 * Someone opens this screen because the agent is bothering them, and the
 * first thing they reach for is Mute. What these tests guard is that the
 * screen tells them where each balance actually stands BEFORE they press
 * it — first reminder, second reminder, or the engine having already
 * stopped on its own. A mute button pressed blind is how the product loses
 * a user it had not yet annoyed, and "no more reminders" is the one line
 * that can prevent it.
 */
import { render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

const { mockPrefs, mockRelationships, mockVapid } = vi.hoisted(() => ({
  mockPrefs: vi.fn(),
  mockRelationships: vi.fn(),
  mockVapid: vi.fn(),
}))

vi.mock("../api/notifications", () => ({
  useNotificationPreferences: () => mockPrefs(),
  useUpdateNotificationPreferences: () => ({ mutate: vi.fn() }),
  useNudgeRelationships: () => mockRelationships(),
  useUpdateNudgeRelationship: () => ({ mutate: vi.fn() }),
  useVapidPublicKey: () => mockVapid(),
  useRegisterPushSubscription: () => ({ mutate: vi.fn() }),
  useDeletePushSubscription: () => ({ mutate: vi.fn() }),
}))

vi.mock("../lib/push", () => ({
  checkPushSupport: () => ({ supported: false, reason: "test" }),
  getPermission: () => "default",
  subscribeToPush: vi.fn(),
  unsubscribeFromPush: vi.fn(),
}))

import { NotificationSettings } from "./NotificationSettings"

type Relationship = {
  group_id: string
  group_name: string
  counterparty_user_id: string
  counterparty_name: string | null
  muted: boolean
  snoozed_until: string | null
  last_level?: number | null
  reminders_exhausted?: boolean
}

function relationship(overrides: Partial<Relationship> = {}): Relationship {
  return {
    group_id: "g1",
    group_name: "Trip to Lisbon",
    counterparty_user_id: "u1",
    counterparty_name: "Alex",
    muted: false,
    snoozed_until: null,
    last_level: null,
    reminders_exhausted: false,
    ...overrides,
  }
}

/** The status line is rendered as "<group> · <status>". */
function statusLine(): string {
  return screen.getByText(/Trip to Lisbon/).textContent ?? ""
}

describe("NotificationSettings — ladder status", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockPrefs.mockReturnValue({
      data: {
        nudges_enabled: true,
        push_enabled: true,
        email_enabled: true,
        quiet_hours_start: 22,
        quiet_hours_end: 8,
        timezone: "UTC",
      },
      isLoading: false,
    })
    mockVapid.mockReturnValue({ data: { key: null } })
    mockRelationships.mockReturnValue({ data: [relationship()] })
  })

  it("says nothing about a balance the agent has never mentioned", () => {
    render(<NotificationSettings />)
    expect(statusLine()).toBe("Trip to Lisbon")
  })

  it("reports the first reminder", () => {
    mockRelationships.mockReturnValue({ data: [relationship({ last_level: 1 })] })
    render(<NotificationSettings />)
    expect(statusLine()).toContain("first reminder sent")
  })

  it("reports the escalation", () => {
    mockRelationships.mockReturnValue({ data: [relationship({ last_level: 2 })] })
    render(<NotificationSettings />)
    expect(statusLine()).toContain("second reminder sent")
  })

  it("says the agent has stopped, rather than just falling silent", () => {
    // The load-bearing one. With Level 3 cut, silence is the last rung —
    // and an engine that stopped on purpose looks exactly like a broken one
    // unless it says so.
    mockRelationships.mockReturnValue({
      data: [relationship({ last_level: 2, reminders_exhausted: true })],
    })
    render(<NotificationSettings />)
    expect(statusLine()).toContain("no more reminders")
    expect(statusLine()).not.toContain("second reminder sent")
  })

  it("lets an explicit choice outrank whatever the engine was doing", () => {
    // Muted and snoozed are things the USER did; the ladder is something
    // the engine did. Showing the engine's state over the user's own
    // decision would read as the app ignoring them.
    mockRelationships.mockReturnValue({
      data: [
        relationship({
          muted: true,
          last_level: 2,
          reminders_exhausted: true,
        }),
      ],
    })
    render(<NotificationSettings />)
    expect(statusLine()).toContain("muted")
    expect(statusLine()).not.toContain("no more reminders")
  })

  it("shows a live snooze ahead of the ladder, and ignores an expired one", () => {
    const tomorrow = new Date(Date.now() + 86_400_000).toISOString()
    mockRelationships.mockReturnValue({
      data: [relationship({ snoozed_until: tomorrow, last_level: 1 })],
    })
    const { unmount } = render(<NotificationSettings />)
    expect(statusLine()).toContain("snoozed until")
    unmount()

    const yesterday = new Date(Date.now() - 86_400_000).toISOString()
    mockRelationships.mockReturnValue({
      data: [relationship({ snoozed_until: yesterday, last_level: 1 })],
    })
    render(<NotificationSettings />)
    expect(statusLine()).toContain("first reminder sent")
    expect(statusLine()).not.toContain("snoozed until")
  })
})
