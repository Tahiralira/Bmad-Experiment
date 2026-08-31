import fs from "node:fs"
import path from "node:path"

import { expect, test, type Page } from "@playwright/test"

import { createConfirmedExpense, createGroupWithMember } from "./utils/groups"
import { randomTeamName, uniqueLabel } from "./utils/random"

/**
 * WS13 visual proof (DoD v2 #2): the per-relationship ladder status, at
 * 375px and 1280px, in both themes.
 *
 *   npx playwright test --project=visual ws13-screenshots
 *
 * Excluded from the CI journeys for the same reason as WS12's: it captures
 * pixels and asserts nothing about behaviour. It exists so a human LOOKS at
 * the result — the discipline that caught two real layout bugs in WS12 that
 * every other gate passed.
 *
 * The relationships response is STUBBED. Reaching the interesting states for
 * real would mean a debt aged past 24h, a sweep, another 72h, and another
 * sweep — four days of wall clock that no screenshot run can wait for, and
 * that the backend already proves in `test_nudge_level_2.py` with injected
 * time. The stub photographs the surface; the tests assert the behaviour.
 * (Same split WS12 used for the push prompt.)
 */

const OUT = path.resolve(
  process.cwd(),
  "../_bmad-output/implementation-artifacts/ws13-screenshots",
)

const VIEWPORTS = [
  { label: "375", width: 375, height: 812 },
  { label: "1280", width: 1280, height: 900 },
]

/** The status line each stubbed state must actually render. */
const EXPECTED_STATUS: Record<string, RegExp> = {
  "level-1": /first reminder sent/,
  "level-2": /second reminder sent/,
  exhausted: /no more reminders/,
  "muted-outranks-ladder": /· muted/,
}

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate((t) => {
    window.localStorage.setItem("vite-ui-theme", t)
  }, theme)
  await page.reload()
  await page.waitForFunction(
    (t) =>
      document.documentElement.classList.contains(t) &&
      getComputedStyle(document.body).backgroundColor !== "",
    theme,
  )
}

async function shoot(page: Page, name: string) {
  await page.waitForTimeout(250)
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true })
}

test.beforeAll(() => {
  fs.mkdirSync(OUT, { recursive: true })
})

test.describe("WS13 screenshots", () => {
  test("the nudge ladder, every rung, both themes and both widths", async ({
    page,
    browser,
  }) => {
    test.setTimeout(180_000)

    // A real group and a real open balance underneath the stub, so the rest
    // of the screen (and its layout at 375px) is genuine.
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
        amount: "58.00",
        description: uniqueLabel("WS13 shot dinner"),
      })

      // Capture the real shape the API returns, then re-serve it with only
      // the ladder fields changed — the group name, counterparty and ids
      // stay real, so the pixels are of this actual group.
      // Absolute URL: there is no dev-server proxy — the SPA talks to
      // VITE_API_URL (localhost:8000) directly, so a root-relative path here
      // would hit Vite and 404.
      const real = await memberPage.evaluate(async () => {
        const res = await fetch(
          "http://localhost:8000/api/v1/notifications/relationships",
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
          },
        )
        return res.json()
      })
      expect(Array.isArray(real)).toBe(true)
      expect(real.length).toBeGreaterThan(0)

      const STATES = [
        { name: "level-1", patch: { last_level: 1 } },
        { name: "level-2", patch: { last_level: 2 } },
        {
          name: "exhausted",
          patch: { last_level: 2, reminders_exhausted: true },
        },
        {
          name: "muted-outranks-ladder",
          patch: { last_level: 2, reminders_exhausted: true, muted: true },
        },
      ]

      for (const viewport of VIEWPORTS) {
        await memberPage.setViewportSize({
          width: viewport.width,
          height: viewport.height,
        })

        for (const theme of ["light", "dark"] as const) {
          for (const state of STATES) {
            await memberPage.route(
              "**/api/v1/notifications/relationships",
              (route) =>
                route.fulfill({
                  status: 200,
                  contentType: "application/json",
                  body: JSON.stringify(
                    real.map((r: object) => ({ ...r, ...state.patch })),
                  ),
                }),
            )

            await memberPage.goto("/settings")
            await setTheme(memberPage, theme)
            await memberPage
              .getByRole("tab", { name: "Notifications" })
              .click()
            await expect(
              memberPage.getByText("Specific balances"),
            ).toBeVisible()

            // The ONE thing worth asserting in a pixel spec. WS12's two real
            // layout bugs were both this: content pushing the page wider
            // than the viewport at 375px, which every other gate passed and
            // only a measurement caught. Cheap to check on every state, so
            // the next person doesn't have to notice it by eye.
            const scrollWidth = await memberPage.evaluate(
              () => document.body.scrollWidth,
            )
            expect(
              scrollWidth,
              `${state.name} @${viewport.label} scrolls sideways`,
            ).toBeLessThanOrEqual(viewport.width)

            // And the status line itself is really on screen — otherwise a
            // stale build photographs beautifully and proves nothing (which
            // is exactly what the first run of this spec did).
            await expect(
              memberPage.getByText(EXPECTED_STATUS[state.name]),
            ).toBeVisible()

            await shoot(
              memberPage,
              `ladder-${state.name}-${theme}-${viewport.label}`,
            )
            await memberPage.unroute(
              "**/api/v1/notifications/relationships",
            )
          }
        }
      }
    } finally {
      await memberContext.close()
    }
  })
})
