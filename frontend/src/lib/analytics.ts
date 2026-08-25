/**
 * Product analytics (WS10.6) — PostHog, frontend-only, env-gated.
 *
 * - No-op unless VITE_POSTHOG_KEY is set: local dev, tests, and any deploy
 *   without a key send NOTHING (the SDK is never even downloaded).
 * - posthog-js loads via dynamic import so it stays out of the main chunk;
 *   events fired before it finishes loading are queued and flushed in order.
 * - Privacy posture matches the backend's (WS8/S5-M7): identify() with the
 *   user's opaque UUID only — never email or name; autocapture and session
 *   recording are OFF, so ONLY the explicit taxonomy below ever ships.
 * - Capability URLs (invite tokens, magic-link tokens, OAuth one-time codes)
 *   are scrubbed from every URL-ish property via sanitizeUrl — an invite
 *   token in an analytics payload would be a join-the-group credential.
 *
 * Event names follow `domain.entity.action` (S2 §9 — the same convention the
 * WS12 event envelope will use). The full taxonomy, funnel definitions, and
 * owner setup runbook live in
 * `_bmad-output/planning-artifacts/analytics-spec.md`.
 */

// ---------------------------------------------------------------------------
// Event taxonomy — the ONLY names that may be captured. Add here first;
// keep analytics-spec.md in sync.
// ---------------------------------------------------------------------------

export const EVENTS = {
  // Auth (activation funnel step 0). signed_up fires only on the email
  // registration verify — OAuth first-logins are indistinguishable from
  // returning logins client-side (use PostHog person first-seen for those).
  AUTH_SIGNED_UP: "auth.user.signed_up", // { method: "magic_link" }
  AUTH_LOGGED_IN: "auth.user.logged_in", // { method: "oauth" | "magic_link" }
  AUTH_LOGGED_OUT: "auth.user.logged_out",

  // Groups (activation funnel steps 1–2; invite→join guardrail)
  GROUP_CREATED: "group.group.created", // { template, currency, strict_mode }
  GROUP_SETTINGS_UPDATED: "group.settings.updated", // { setting }
  INVITE_CREATED: "group.invite.created",
  INVITE_VIEWED: "group.invite.viewed", // { logged_in } — fires anonymously too
  INVITE_JOINED: "group.invite.joined", // { method: "explicit" | "oauth_return" }

  // AI parse (edit-rate numerator source; quota = the paywall's fuel gauge)
  PARSE_STARTED: "ai.parse.started", // { sandbox }
  PARSE_COMPLETED: "ai.parse.completed", // { sandbox, confidence }
  PARSE_FAILED: "ai.parse.failed", // { sandbox, reason }
  QUOTA_EXHAUSTED: "ai.quota.exhausted", // fired alongside the quota 429

  // Expenses (activation funnel step 3; edit rate via was_edited)
  EXPENSE_CREATED: "expense.expense.created", // { source: "ai" | "manual", was_edited? }
  EXPENSE_CONFIRMED: "expense.expense.confirmed",
  EXPENSE_REJECTED: "expense.expense.rejected",

  // Settlement (settlement velocity)
  CLAIM_CREATED: "settlement.claim.created", // { kind: "aggregate" | "per_expense" }
  CLAIM_CONFIRMED: "settlement.claim.confirmed", // { kind, claim_age_hours }
  CLAIM_REJECTED: "settlement.claim.rejected",

  // Payments (WS10.2 — settle-moment intent)
  PAYMENT_METHOD_ADDED: "payment.method.added", // { provider }
  PAYMENT_LINK_CLICKED: "payment.link.clicked", // { provider }
  PAYMENT_HANDLE_COPIED: "payment.handle.copied", // { provider }

  // WS12 — the PRD's kill-switch metric. { scope: "all" | "relationship" }.
  // Never carries who was muted or the quiet-hours schedule: the rate is the
  // signal, and when someone sleeps is not analytics data.
  NUDGE_MUTED: "nudge.notification.muted",
} as const

/**
 * Reserved names for features that DON'T EXIST yet — recorded now so the
 * taxonomy is stable when they land. Do not capture these before their
 * feature ships (DoD: no green assertions of absent behavior).
 */
export const RESERVED_EVENTS = {
  // Still reserved after WS12: nudges are DELIVERED server-side by the sweep,
  // and there is no backend analytics client, so the browser cannot honestly
  // capture "sent". The `notification` table is the source of truth for send
  // volume; mute RATE pairs that with NUDGE_MUTED above (analytics-spec §6).
  NUDGE_SENT: "nudge.notification.sent",
  PAYWALL_VIEWED: "billing.paywall.viewed", // Phase 4 (monetization-spec §5)
  PAYWALL_CONVERTED: "billing.paywall.converted", // Phase 4
} as const

export type AnalyticsEvent = (typeof EVENTS)[keyof typeof EVENTS]

export type AnalyticsProps = Record<
  string,
  string | number | boolean | null | undefined
>

// ---------------------------------------------------------------------------
// URL scrubbing — shared with Sentry (lib/sentry.ts)
// ---------------------------------------------------------------------------

/**
 * Redact capability tokens from a URL or path before it leaves the app:
 * /invite/{token} and /verify/{token} (incl. /login/verify/{token}) path
 * segments, and the OAuth one-time ?code= parameter (WS8/S5-H1).
 */
export function sanitizeUrl(url: string): string {
  return url
    .replace(/\/(invite|verify)\/[^/?#]+/g, "/$1/:token")
    .replace(/([?&]code=)[^&#]+/g, "$1redacted")
}

const URL_PROPERTY_KEYS = [
  "$current_url",
  "$pathname",
  "$referrer",
  "$initial_current_url",
  "$initial_pathname",
  "$initial_referrer",
]

/** posthog-js `sanitize_properties` hook — scrubs every URL-ish property. */
export function sanitizeProperties(
  props: Record<string, unknown>,
): Record<string, unknown> {
  const scrub = (obj: Record<string, unknown>) => {
    for (const key of URL_PROPERTY_KEYS) {
      const value = obj[key]
      if (typeof value === "string") obj[key] = sanitizeUrl(value)
    }
  }
  scrub(props)
  // Person properties ride along nested under $set / $set_once
  for (const nested of ["$set", "$set_once"]) {
    const value = props[nested]
    if (value && typeof value === "object") {
      scrub(value as Record<string, unknown>)
    }
  }
  return props
}

// ---------------------------------------------------------------------------
// Client lifecycle
// ---------------------------------------------------------------------------

/** The slice of posthog-js this module uses (kept narrow for testability). */
export interface PostHogClient {
  init(key: string, config: Record<string, unknown>): unknown
  capture(event: string, props?: Record<string, unknown>): unknown
  identify(id: string): unknown
  reset(): unknown
}

type AnalyticsOp = (client: PostHogClient) => void

// disabled: client === null && pending === null
// loading:  client === null && pending === [...queued ops]
// ready:    client !== null
let client: PostHogClient | null = null
let pending: AnalyticsOp[] | null = null
let identifiedId: string | null = null

const enqueue = (op: AnalyticsOp): void => {
  if (client) {
    op(client)
  } else if (pending) {
    pending.push(op)
  }
  // else: analytics disabled — drop silently
}

export interface InitAnalyticsOptions {
  key?: string
  host?: string
  /** Test seam — defaults to the real dynamic import of posthog-js. */
  loadPostHog?: () => Promise<{ default: PostHogClient }>
}

/**
 * Initialize PostHog. Call once at app boot; a missing VITE_POSTHOG_KEY
 * makes every analytics function a permanent no-op. Never throws — a
 * failed SDK load must not break the app.
 */
export async function initAnalytics(
  options: InitAnalyticsOptions = {},
): Promise<void> {
  if (client || pending) return // already initialized (or initializing)
  const key = options.key ?? import.meta.env.VITE_POSTHOG_KEY
  if (!key) return // env-gated: stays a no-op

  pending = []
  const host =
    options.host ?? import.meta.env.VITE_POSTHOG_HOST ?? "https://us.i.posthog.com"
  const load = options.loadPostHog ?? (() => import("posthog-js"))
  try {
    const mod = await load()
    const posthog = mod.default
    posthog.init(key, {
      api_host: host,
      // Explicit taxonomy only — no autocapture, no recording, no auto
      // pageviews (SPA route changes are captured manually in main.tsx).
      autocapture: false,
      capture_pageview: false,
      capture_pageleave: false,
      disable_session_recording: true,
      // No feature flags AND no remote-config script: the prod CSP is
      // script-src 'self', which would block posthog's config.js — with
      // flags disabled the SDK falls back to local config and only ever
      // talks to the capture endpoint over fetch (connect-src allows it).
      advanced_disable_flags: true,
      // No cookies; single-origin SPA doesn't need cross-domain identity.
      persistence: "localStorage",
      // Anonymous visitors (invite previews) stay cheap anonymous events.
      person_profiles: "identified_only",
      sanitize_properties: sanitizeProperties,
    })
    client = posthog
    const ops = pending
    pending = null
    for (const op of ops) op(posthog)
  } catch {
    pending = null // SDK load failed (offline, blocked) — disable quietly
  }
}

// ---------------------------------------------------------------------------
// Capture API
// ---------------------------------------------------------------------------

/** Capture a taxonomy event. Safe to call anywhere, any time. */
export function track(event: AnalyticsEvent, props?: AnalyticsProps): void {
  enqueue((ph) => ph.capture(event, props))
}

/** Manual SPA pageview (autocapture pageviews are off). */
export function trackPageview(pathname: string): void {
  enqueue((ph) =>
    ph.capture("$pageview", {
      $current_url: sanitizeUrl(window.location.origin + pathname),
      $pathname: sanitizeUrl(pathname),
    }),
  )
}

/**
 * Tie events to the signed-in user's opaque UUID — never email or name
 * (UUID-only decision, WS10.6). Repeat calls with the same id are dropped.
 */
export function identifyUser(userId: string): void {
  if (!userId || userId === identifiedId) return
  identifiedId = userId
  enqueue((ph) => ph.identify(userId))
}

/** Detach identity on logout so a shared device doesn't cross-attribute. */
export function resetAnalytics(): void {
  identifiedId = null
  enqueue((ph) => ph.reset())
}

/** Test-only: return the module to its pristine (disabled) state. */
export function __resetAnalyticsForTests(): void {
  client = null
  pending = null
  identifiedId = null
}
