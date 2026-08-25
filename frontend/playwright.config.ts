import { defineConfig, devices } from '@playwright/test';
import 'dotenv/config'

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /**
   * Reporter to use. See https://playwright.dev/docs/test-reporters
   * CI gets a readable log plus an HTML report to upload as an artifact —
   * `blob` is for merging shards, and this suite runs as one job.
   */
  reporter: process.env.CI
    ? [['list'], ['html', { open: 'never' }]]
    : 'html',
  /**
   * These journeys drive a real stack: every magic-link step waits on the API
   * to render a template and hand it to SMTP before the UI advances. The 5s
   * default is under that on a cold container and produced failures that
   * looked like broken selectors.
   */
  expect: { timeout: 15_000 },
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:5173',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',

    /**
     * The production frontend image ships WS8's strict CSP
     * (`connect-src 'self' https:`), which blocks the plain-http
     * `localhost:8000` API — every request fails with `REQFAILED … csp`
     * and the app renders but does nothing (solution-patterns FE-008).
     *
     * Bypassing it in the test browser makes the suite behave identically
     * whether it runs against the nginx image or the Vite dev server, so a
     * developer with `docker compose up` running gets the same result as CI.
     *
     * This does weaken what e2e can catch, so `csp-headers.spec.ts` asserts
     * the served header directly — that spec is the frontend CSP's only
     * coverage (the backend's own CSP is covered by
     * backend/tests/api/routes/test_ws8_security.py).
     */
    bypassCSP: true,
  },

  /* Configure projects for major browsers */
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },

    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // {
    //   name: 'firefox',
    //   use: {
    //     ...devices['Desktop Firefox'],
    //     storageState: 'playwright/.auth/user.json',
    //   },
    //   dependencies: ['setup'],
    // },

    // {
    //   name: 'webkit',
    //   use: {
    //     ...devices['Desktop Safari'],
    //     storageState: 'playwright/.auth/user.json',
    //   },
    //   dependencies: ['setup'],
    // },

    /* Test against mobile viewports. */
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },

    /* Test against branded browsers. */
    // {
    //   name: 'Microsoft Edge',
    //   use: { ...devices['Desktop Edge'], channel: 'msedge' },
    // },
    // {
    //   name: 'Google Chrome',
    //   use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    // },
  ],

  /**
   * Reuse whatever is already serving 5173 — in CI that is the compose
   * `frontend` container, locally it is either that or a dev server the
   * developer already has running. Only when nothing answers does Playwright
   * start one itself.
   *
   * This used to be `!process.env.CI`, which meant a developer with
   * `docker compose up` running silently tested a *different* server than CI
   * did (and hit the CSP wall the container serves).
   */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
  },
});
