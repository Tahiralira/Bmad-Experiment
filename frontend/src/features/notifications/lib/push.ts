/**
 * Web Push plumbing (WS12).
 *
 * Everything here is capability-checked and returns a reason rather than
 * throwing. Push is unavailable in more real situations than it is available
 * — iOS Safari before the PWA is installed, Firefox with push disabled,
 * private windows, http origins, a server with no VAPID keypair — and each
 * of those needs different copy, not a crash.
 */

export type PushSupport =
  | { supported: true }
  | { supported: false; reason: "no-service-worker" | "no-push-api" | "insecure" }

export function checkPushSupport(): PushSupport {
  // Push requires a secure context. localhost counts as secure, which is why
  // this checks the flag rather than the protocol.
  if (!window.isSecureContext) {
    return { supported: false, reason: "insecure" }
  }
  if (!("serviceWorker" in navigator)) {
    return { supported: false, reason: "no-service-worker" }
  }
  if (!("PushManager" in window) || !("Notification" in window)) {
    return { supported: false, reason: "no-push-api" }
  }
  return { supported: true }
}

export function getPermission(): NotificationPermission | "unsupported" {
  if (!("Notification" in window)) return "unsupported"
  return Notification.permission
}

/**
 * The VAPID public key travels as base64url but `PushManager.subscribe`
 * wants raw bytes. Padding is re-added because base64url drops it and
 * `atob` requires it.
 */
function urlBase64ToUint8Array(base64: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4)
  const normalized = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/")
  const raw = window.atob(normalized)
  // Backed by a plain ArrayBuffer, not the generic ArrayBufferLike: a
  // SharedArrayBuffer is not a valid `applicationServerKey`, and TS 5.7's
  // generic Uint8Array is what surfaces that.
  const output = new Uint8Array(new ArrayBuffer(raw.length))
  for (let i = 0; i < raw.length; i++) {
    output[i] = raw.charCodeAt(i)
  }
  return output
}

/** The browser's key material, in the shape the backend stores. */
export type SubscriptionKeys = {
  endpoint: string
  p256dh: string
  auth: string
}

function encodeKey(subscription: PushSubscription, name: "p256dh" | "auth"): string {
  const key = subscription.getKey(name)
  if (!key) return ""
  return window.btoa(String.fromCharCode(...new Uint8Array(key)))
}

export function serializeSubscription(
  subscription: PushSubscription,
): SubscriptionKeys {
  return {
    endpoint: subscription.endpoint,
    p256dh: encodeKey(subscription, "p256dh"),
    auth: encodeKey(subscription, "auth"),
  }
}

/**
 * Subscribe this browser to push, returning the key material the backend
 * needs. Returns null when the user denies permission or the browser
 * refuses — both are ordinary outcomes, not errors.
 *
 * An existing subscription is REUSED rather than replaced: re-subscribing
 * rotates the endpoint, which would orphan the row the server already has.
 */
export async function subscribeToPush(
  vapidPublicKey: string,
): Promise<SubscriptionKeys | null> {
  const support = checkPushSupport()
  if (!support.supported) return null

  const permission = await Notification.requestPermission()
  if (permission !== "granted") return null

  const registration = await navigator.serviceWorker.ready
  const existing = await registration.pushManager.getSubscription()
  if (existing) {
    return serializeSubscription(existing)
  }

  const subscription = await registration.pushManager.subscribe({
    // Required by Chrome: a push that shows no notification is not allowed.
    // The SW shows one for every message, so this is a true statement.
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
  })
  return serializeSubscription(subscription)
}

/**
 * Unsubscribe this browser. Returns the endpoint that was removed so the
 * caller can tell the server which row to drop, or null if there was
 * nothing subscribed.
 */
export async function unsubscribeFromPush(): Promise<string | null> {
  const support = checkPushSupport()
  if (!support.supported) return null

  const registration = await navigator.serviceWorker.ready
  const subscription = await registration.pushManager.getSubscription()
  if (!subscription) return null

  const { endpoint } = subscription
  await subscription.unsubscribe()
  return endpoint
}

/** The current subscription, if this browser already has one. */
export async function getExistingSubscription(): Promise<SubscriptionKeys | null> {
  const support = checkPushSupport()
  if (!support.supported) return null
  try {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()
    return subscription ? serializeSubscription(subscription) : null
  } catch {
    return null
  }
}
