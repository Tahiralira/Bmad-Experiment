import { expect, test } from "@playwright/test"

/**
 * The journeys run with `bypassCSP: true` (see playwright.config.ts), which
 * means they cannot catch a broken Content-Security-Policy. This spec is the
 * compensating check: it asserts the header the production image actually
 * serves.
 *
 * It is the ONLY automated coverage of the frontend CSP. The backend's own
 * headers are covered separately by
 * backend/tests/api/routes/test_ws8_security.py::test_security_headers_present.
 *
 * Keep this in step with nginx.conf and vercel.json — all three must agree, or
 * production and the local image diverge silently.
 */

const EXPECTED_CSP = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'self' https:",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ")

test.describe("security headers", () => {
  test("the served app carries the expected CSP", async ({ request }) => {
    const response = await request.get("/")
    const headers = response.headers()

    test.skip(
      !(headers.server ?? "").includes("nginx"),
      "CSP is added by the nginx image, not the Vite dev server — " +
        "run `docker compose up -d frontend` to exercise this.",
    )

    expect(headers["content-security-policy"]).toBe(EXPECTED_CSP)
  })
})
