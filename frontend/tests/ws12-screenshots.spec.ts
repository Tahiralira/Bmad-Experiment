import fs from "node:fs"
import path from "node:path"

import { expect, test, type Page } from "@playwright/test"

import { createConfirmedExpense, createGroupWithMember } from "./utils/groups"
import { randomTeamName, uniqueLabel } from "./utils/random"

/**
 * WS12 visual proof (DoD v2 #2): every new surface at 375px and 1280px, in
 * both themes. Run explicitly — it is excluded from the CI journeys because
 * it asserts nothing; it exists so a human looks at the pixels, which is the
 * failure Epic 2.5 shipped invisible text for five months by skipping.
 *
 *   npx playwright test --project=chromium ws12-screenshots
 */

// Playwright runs with the cwd at frontend/; __dirname is not defined under
// this project's ESM setup.
const OUT = path.resolve(
  process.cwd(),
  "../_bmad-output/implementation-artifacts/ws12-screenshots",
)

const VIEWPORTS = [
  { label: "375", width: 375, height: 812 },
  { label: "1280", width: 1280, height: 900 },
]

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate((t) => {
    window.localStorage.setItem("vite-ui-theme", t)
  }, theme)
  await page.reload()
  // Cold loads apply the theme class late (WS3/WS8 lesson) — wait for the
  // painted background, not merely for an element to exist.
  await page.waitForFunction(
    (t) =>
      document.documentElement.classList.contains(t) &&
      getComputedStyle(document.body).backgroundColor !== "",
    theme,
  )
}

async function shoot(page: Page, name: string) {
  await page.waitForTimeout(250) // let any toast settle
  await page.screenshot({
    path: path.join(OUT, `${name}.png`),
    fullPage: true,
  })
}

test.beforeAll(() => {
  fs.mkdirSync(OUT, { recursive: true })
})

test.describe("WS12 screenshots", () => {
  test("notification settings, both themes and both widths", async ({
    page,
    browser,
  }) => {
    test.setTimeout(120_000)

    // A real open balance so the per-relationship section has something in it
    // — an empty settings screen would prove nothing about the feature.
    const groupName = randomTeamName()
    const { groupUrl, memberContext, memberPage } = await createGroupWithMember(
      page,
      browser,
      groupName,
    )

    try {
      await createConfirmedExpense(page, memberPage, {
        groupUrl,
        groupName,
        amount: "64.00",
        description: uniqueLabel("WS12 shot dinner"),
      })

      for (const viewport of VIEWPORTS) {
        await memberPage.setViewportSize({
          width: viewport.width,
          height: viewport.height,
        })
        for (const theme of ["light", "dark"] as const) {
          await memberPage.goto("/settings")
          await setTheme(memberPage, theme)
          await memberPage.getByRole("tab", { name: "Notifications" }).click()
          await expect(
            memberPage.getByLabel("Turn off all reminders"),
          ).toBeVisible()
          await shoot(
            memberPage,
            `notification-settings-${theme}-${viewport.label}`,
          )

          // The muted state reads differently — capture it too, since "what
          // does an off switch look like when it's off" is the whole point.
          const killSwitch = memberPage.getByLabel("Turn off all reminders")
          await killSwitch.click()
          await expect(killSwitch).toBeChecked()
          await shoot(
            memberPage,
            `notification-settings-muted-${theme}-${viewport.label}`,
          )
          await killSwitch.click()
          await expect(killSwitch).not.toBeChecked()
        }
      }
    } finally {
      await memberContext.close()
    }
  })

  test("push permission prompt on the dashboard", async ({ page, browser }) => {
    test.setTimeout(120_000)

    const groupName = randomTeamName()
    const { groupUrl, memberContext, memberPage } = await createGroupWithMember(
      page,
      browser,
      groupName,
    )

    try {
      await createConfirmedExpense(page, memberPage, {
        groupUrl,
        groupName,
        amount: "42.00",
        description: uniqueLabel("WS12 prompt dinner"),
      })

      // Two stubs, both needed only to PHOTOGRAPH a surface that is correctly
      // invisible here:
      //   1. Playwright's context reports Notification.permission === "denied",
      //      and the prompt deliberately never re-asks after a denial.
      //   2. This stack has no VAPID keypair (the honest default), and the
      //      prompt deliberately never asks when the server couldn't deliver.
      // Both refusals are asserted for real in PushPermissionPrompt.test.tsx.
      await memberPage.addInitScript(() => {
        Object.defineProperty(Notification, "permission", {
          get: () => "default",
          configurable: true,
        })
      })
      await memberPage.route("**/api/v1/notifications/vapid-public-key", (r) =>
        r.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ key: "BLgamyc_stub_public_key_for_pixels" }),
        }),
      )

      for (const viewport of VIEWPORTS) {
        await memberPage.setViewportSize({
          width: viewport.width,
          height: viewport.height,
        })
        for (const theme of ["light", "dark"] as const) {
          await memberPage.goto("/")
          await setTheme(memberPage, theme)
          await expect(
            memberPage.getByText(/Want ClearDues to keep track for you\?/i),
          ).toBeVisible()
          await shoot(memberPage, `push-prompt-${theme}-${viewport.label}`)
        }
      }
    } finally {
      await memberContext.close()
    }
  })
})
