/**
 * Error monitoring (WS10.6) — Sentry, env-gated on VITE_SENTRY_DSN.
 *
 * Statically imported (unlike PostHog's lazy load) on purpose: the most
 * valuable frontend errors are boot-time failures (white screen before a
 * lazily-loaded SDK would ever arrive). Errors-only — no tracing, no
 * replay — keeps the tree-shaken cost small against the ≤250 kB gz main
 * chunk budget.
 *
 * Privacy mirrors the backend init (WS8/S5-M7, app/main.py): no default
 * PII, and capability URLs (invite/verify tokens, OAuth one-time codes)
 * are scrubbed from events and breadcrumbs via the shared sanitizeUrl.
 */

import * as Sentry from "@sentry/react"
import type { Breadcrumb, ErrorEvent } from "@sentry/react"

import { sanitizeUrl } from "./analytics"

/** beforeSend hook — scrub token-bearing URLs off the event envelope. */
export function scrubEvent(event: ErrorEvent): ErrorEvent {
  if (event.request?.url) {
    event.request.url = sanitizeUrl(event.request.url)
  }
  const referer = event.request?.headers?.Referer
  if (referer && event.request?.headers) {
    event.request.headers.Referer = sanitizeUrl(referer)
  }
  return event
}

/** beforeBreadcrumb hook — navigation/fetch crumbs carry URLs too. */
export function scrubBreadcrumb(crumb: Breadcrumb): Breadcrumb {
  if (crumb.data) {
    for (const key of ["url", "to", "from"]) {
      const value = crumb.data[key]
      if (typeof value === "string") {
        crumb.data[key] = sanitizeUrl(value)
      }
    }
  }
  return crumb
}

/**
 * Initialize Sentry. Call once at app boot, before render; a missing
 * VITE_SENTRY_DSN leaves the SDK dormant (captureError becomes a no-op).
 */
export function initErrorMonitoring(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn) return
  Sentry.init({
    dsn,
    // Vercel builds run in "production" mode; anything else is a dev build.
    environment: import.meta.env.MODE,
    sendDefaultPii: false,
    beforeSend: scrubEvent,
    beforeBreadcrumb: scrubBreadcrumb,
  })
}

/**
 * Report a caught error (router error boundaries, explicit catches).
 * Safe without init — Sentry drops it when no client is configured.
 */
export function captureError(error: unknown): void {
  Sentry.captureException(error)
}
