import { afterEach, describe, expect, it, vi } from "vitest"

import { checkPushSupport, getPermission, serializeSubscription } from "./push"

/**
 * jsdom has neither a PushManager nor a service worker, which makes it a
 * good stand-in for the browsers where push genuinely is unavailable. These
 * tests pin the capability checks that decide whether the app ever asks for
 * the permission — getting them wrong either wastes the one prompt a browser
 * grants, or hides the feature from browsers that support it.
 */

const originalIsSecureContext = window.isSecureContext

function setSecureContext(value: boolean) {
  Object.defineProperty(window, "isSecureContext", {
    value,
    configurable: true,
    writable: true,
  })
}

afterEach(() => {
  setSecureContext(originalIsSecureContext)
  vi.unstubAllGlobals()
  // biome-ignore lint/performance/noDelete: restoring the jsdom global
  delete (window as unknown as Record<string, unknown>).PushManager
  // biome-ignore lint/performance/noDelete: restoring the jsdom global
  delete (window as unknown as Record<string, unknown>).Notification
})

describe("checkPushSupport", () => {
  it("reports insecure contexts first — push needs HTTPS", () => {
    setSecureContext(false)
    expect(checkPushSupport()).toEqual({
      supported: false,
      reason: "insecure",
    })
  })

  it("reports a missing service worker", () => {
    setSecureContext(true)
    const nav = navigator as unknown as Record<string, unknown>
    const had = "serviceWorker" in nav
    if (had) delete nav.serviceWorker
    try {
      expect(checkPushSupport()).toEqual({
        supported: false,
        reason: "no-service-worker",
      })
    } finally {
      if (had) nav.serviceWorker = {}
    }
  })

  it("reports a missing Push API even when a service worker exists", () => {
    setSecureContext(true)
    const nav = navigator as unknown as Record<string, unknown>
    nav.serviceWorker = {}
    expect(checkPushSupport()).toEqual({
      supported: false,
      reason: "no-push-api",
    })
  })

  it("reports support when the secure context, SW and Push API are all present", () => {
    setSecureContext(true)
    const nav = navigator as unknown as Record<string, unknown>
    nav.serviceWorker = {}
    vi.stubGlobal("PushManager", class {})
    vi.stubGlobal("Notification", { permission: "default" })
    expect(checkPushSupport()).toEqual({ supported: true })
  })
})

describe("getPermission", () => {
  it("says 'unsupported' rather than guessing when Notification is absent", () => {
    expect(getPermission()).toBe("unsupported")
  })

  it("passes the browser's answer through", () => {
    vi.stubGlobal("Notification", { permission: "denied" })
    expect(getPermission()).toBe("denied")
  })
})

describe("serializeSubscription", () => {
  it("base64-encodes the browser's key material for the wire", () => {
    const encode = (text: string) => {
      const bytes = new Uint8Array(text.length)
      for (let i = 0; i < text.length; i++) bytes[i] = text.charCodeAt(i)
      return bytes.buffer
    }
    const subscription = {
      endpoint: "https://push.example.com/abc",
      getKey: (name: string) =>
        name === "p256dh" ? encode("public-key") : encode("auth-secret"),
    } as unknown as PushSubscription

    expect(serializeSubscription(subscription)).toEqual({
      endpoint: "https://push.example.com/abc",
      p256dh: window.btoa("public-key"),
      auth: window.btoa("auth-secret"),
    })
  })

  it("degrades to an empty string when a key is missing rather than throwing", () => {
    const subscription = {
      endpoint: "https://push.example.com/abc",
      getKey: () => null,
    } as unknown as PushSubscription

    expect(serializeSubscription(subscription)).toEqual({
      endpoint: "https://push.example.com/abc",
      p256dh: "",
      auth: "",
    })
  })
})
