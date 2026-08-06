import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import {
  __resetAnalyticsForTests,
  EVENTS,
  RESERVED_EVENTS,
  identifyUser,
  initAnalytics,
  resetAnalytics,
  sanitizeProperties,
  sanitizeUrl,
  track,
  trackPageview,
  type PostHogClient,
} from "./analytics"
import { scrubBreadcrumb, scrubEvent } from "./sentry"

function makeFakePostHog() {
  const client: PostHogClient = {
    init: vi.fn(),
    capture: vi.fn(),
    identify: vi.fn(),
    reset: vi.fn(),
  }
  const loader = vi.fn(async () => ({ default: client }))
  return { client, loader }
}

beforeEach(() => {
  __resetAnalyticsForTests()
  // initAnalytics falls back to import.meta.env for both of these, so a real
  // .env.local would otherwise leak in: a key flips the env-gating tests, and a
  // non-US host breaks the default-api_host assertion. Unset them so every test
  // supplies its own key/host when it wants one.
  vi.stubEnv("VITE_POSTHOG_KEY", undefined)
  vi.stubEnv("VITE_POSTHOG_HOST", undefined)
})

afterEach(() => {
  vi.unstubAllEnvs()
})

describe("event taxonomy", () => {
  it("every event name follows domain.entity.action", () => {
    const shape = /^[a-z]+\.[a-z_]+\.[a-z_]+$/
    for (const name of [
      ...Object.values(EVENTS),
      ...Object.values(RESERVED_EVENTS),
    ]) {
      expect(name).toMatch(shape)
    }
  })

  it("has no duplicate names across live and reserved events", () => {
    const all = [
      ...Object.values(EVENTS),
      ...Object.values(RESERVED_EVENTS),
    ] as string[]
    expect(new Set(all).size).toBe(all.length)
  })
})

describe("sanitizeUrl", () => {
  it("redacts invite tokens", () => {
    expect(sanitizeUrl("https://app.example.com/invite/abc123XYZ")).toBe(
      "https://app.example.com/invite/:token",
    )
  })

  it("redacts magic-link verify tokens (both routes)", () => {
    expect(sanitizeUrl("/verify/tok-en_1")).toBe("/verify/:token")
    expect(sanitizeUrl("/login/verify/tok-en_2")).toBe("/login/verify/:token")
  })

  it("redacts the OAuth one-time code param", () => {
    expect(
      sanitizeUrl("https://x.example.com/auth/callback?code=SECRET&state=s"),
    ).toBe("https://x.example.com/auth/callback?code=redacted&state=s")
  })

  it("leaves ordinary URLs untouched", () => {
    const url = "https://app.example.com/groups/1b2c?tab=ledger"
    expect(sanitizeUrl(url)).toBe(url)
  })
})

describe("sanitizeProperties", () => {
  it("scrubs URL-ish properties at the top level and in $set_once", () => {
    const props = sanitizeProperties({
      $current_url: "https://a.example.com/invite/tok",
      $referrer: "https://a.example.com/login/verify/tok",
      other: "untouched",
      $set_once: { $initial_current_url: "https://a.example.com/invite/tok" },
    })
    expect(props.$current_url).toBe("https://a.example.com/invite/:token")
    expect(props.$referrer).toBe("https://a.example.com/login/verify/:token")
    expect(props.other).toBe("untouched")
    expect(
      (props.$set_once as Record<string, unknown>).$initial_current_url,
    ).toBe("https://a.example.com/invite/:token")
  })
})

describe("env gating", () => {
  it("is a permanent no-op without a key (never loads the SDK)", async () => {
    const { client, loader } = makeFakePostHog()
    await initAnalytics({ loadPostHog: loader }) // no key
    track(EVENTS.AUTH_LOGGED_IN, { method: "oauth" })
    identifyUser("user-1")
    resetAnalytics()
    expect(loader).not.toHaveBeenCalled()
    expect(client.capture).not.toHaveBeenCalled()
  })

  it("survives an SDK load failure without throwing", async () => {
    const loader = vi.fn(async () => {
      throw new Error("blocked by adblock")
    })
    await expect(
      initAnalytics({ key: "phc_test", loadPostHog: loader }),
    ).resolves.toBeUndefined()
    // Analytics is now disabled; captures are dropped silently.
    expect(() => track(EVENTS.AUTH_LOGGED_OUT)).not.toThrow()
  })
})

describe("initialized capture", () => {
  it("flushes queued events in order once the SDK loads", async () => {
    const { client } = makeFakePostHog()
    let release: () => void = () => {}
    const gate = new Promise<void>((resolve) => {
      release = resolve
    })
    const gatedLoader = vi.fn(async () => {
      await gate
      return { default: client }
    })
    const initPromise = initAnalytics({
      key: "phc_test",
      loadPostHog: gatedLoader,
    })
    // Fired while the SDK is still "downloading"
    track(EVENTS.GROUP_CREATED, { template: "trip" })
    track(EVENTS.INVITE_CREATED)
    expect(client.capture).not.toHaveBeenCalled()

    release()
    await initPromise

    expect(client.capture).toHaveBeenNthCalledWith(
      1,
      "group.group.created",
      { template: "trip" },
    )
    expect(client.capture).toHaveBeenNthCalledWith(
      2,
      "group.invite.created",
      undefined,
    )
    // Post-load events go straight through
    track(EVENTS.EXPENSE_CONFIRMED)
    expect(client.capture).toHaveBeenLastCalledWith(
      "expense.expense.confirmed",
      undefined,
    )
  })

  it("configures PostHog with the privacy posture (no autocapture/recording)", async () => {
    const { client, loader } = makeFakePostHog()
    await initAnalytics({ key: "phc_test", loadPostHog: loader })
    expect(client.init).toHaveBeenCalledWith(
      "phc_test",
      expect.objectContaining({
        api_host: "https://us.i.posthog.com",
        autocapture: false,
        capture_pageview: false,
        disable_session_recording: true,
        advanced_disable_flags: true,
        persistence: "localStorage",
        person_profiles: "identified_only",
        sanitize_properties: sanitizeProperties,
      }),
    )
  })

  it("dedupes identify calls and resumes after reset", async () => {
    const { client, loader } = makeFakePostHog()
    await initAnalytics({ key: "phc_test", loadPostHog: loader })
    identifyUser("user-1")
    identifyUser("user-1")
    expect(client.identify).toHaveBeenCalledTimes(1)
    resetAnalytics()
    expect(client.reset).toHaveBeenCalledTimes(1)
    identifyUser("user-1")
    expect(client.identify).toHaveBeenCalledTimes(2)
  })

  it("sanitizes manual pageview URLs", async () => {
    const { client, loader } = makeFakePostHog()
    await initAnalytics({ key: "phc_test", loadPostHog: loader })
    trackPageview("/invite/secret-token")
    expect(client.capture).toHaveBeenCalledWith("$pageview", {
      $current_url: `${window.location.origin}/invite/:token`,
      $pathname: "/invite/:token",
    })
  })

  it("only initializes once", async () => {
    const { loader } = makeFakePostHog()
    await initAnalytics({ key: "phc_test", loadPostHog: loader })
    await initAnalytics({ key: "phc_test", loadPostHog: loader })
    expect(loader).toHaveBeenCalledTimes(1)
  })
})

describe("Sentry scrubbing", () => {
  it("scrubEvent redacts token-bearing request URLs and Referer", () => {
    const event = scrubEvent({
      type: undefined,
      request: {
        url: "https://app.example.com/invite/tok?code=abc",
        headers: { Referer: "https://app.example.com/verify/tok" },
      },
    } as Parameters<typeof scrubEvent>[0])
    expect(event.request?.url).toBe(
      "https://app.example.com/invite/:token?code=redacted",
    )
    expect(event.request?.headers?.Referer).toBe(
      "https://app.example.com/verify/:token",
    )
  })

  it("scrubBreadcrumb redacts navigation and fetch URLs", () => {
    const crumb = scrubBreadcrumb({
      category: "navigation",
      data: {
        from: "/invite/tok",
        to: "/login/verify/tok",
        url: "https://api.example.com/api/v1/expense-groups/invite/tok",
      },
    })
    expect(crumb.data?.from).toBe("/invite/:token")
    expect(crumb.data?.to).toBe("/login/verify/:token")
    expect(crumb.data?.url).toBe(
      "https://api.example.com/api/v1/expense-groups/invite/:token",
    )
  })
})
