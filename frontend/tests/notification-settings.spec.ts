import { expect, test } from "@playwright/test"

import { createConfirmedExpense, createGroupWithMember } from "./utils/groups"
import { randomTeamName, uniqueLabel } from "./utils/random"

/**
 * The nudge engine's user-reachable half (WS12).
 *
 * A reminder engine with no visible off switch is a liability, so the thing
 * this journey proves is not that reminders arrive — it is that a real person
 * can get to the controls from the app's entry point and turn them off. The
 * sending side is covered by backend tests and a live push proof; what those
 * cannot cover is whether the settings are actually reachable.
 */
test.describe("notification settings", () => {
  test("a signed-in person can reach the reminder controls and turn them off", async ({
    page,
  }) => {
    await page.goto("/settings")

    await page.getByRole("tab", { name: "Notifications" }).click()

    // The stop control comes first — someone arriving here annoyed should not
    // have to read a form to find it.
    const killSwitch = page.getByLabel("Turn off all reminders")
    await expect(killSwitch).toBeVisible()
    await expect(killSwitch).not.toBeChecked()

    await killSwitch.click()
    await expect(page.getByText("Notification settings saved")).toBeVisible()
    await expect(killSwitch).toBeChecked()

    // It survives a reload — this is a stored preference, not UI state.
    await page.reload()
    await page.getByRole("tab", { name: "Notifications" }).click()
    await expect(page.getByLabel("Turn off all reminders")).toBeChecked()

    // And back on again, so the account is left as it was found.
    await page.getByLabel("Turn off all reminders").click()
    await expect(page.getByText("Notification settings saved")).toBeVisible()
    await expect(page.getByLabel("Turn off all reminders")).not.toBeChecked()
  })

  test("quiet hours can be set and removed", async ({ page }) => {
    await page.goto("/settings")
    await page.getByRole("tab", { name: "Notifications" }).click()

    // These journeys share one account (the storage state from auth.setup),
    // and the quiet-hours controls sit inside a fieldset the kill switch
    // disables. Assert the starting state rather than inheriting whatever a
    // sibling test left behind — WS11's TEST-007 lesson, applied to
    // preferences instead of expense descriptions.
    const killSwitch = page.getByLabel("Turn off all reminders")
    if (await killSwitch.isChecked()) {
      await killSwitch.click()
      await expect(killSwitch).not.toBeChecked()
    }

    // Defaults to a 22:00 → 08:00 window.
    await expect(page.getByLabel("Quiet hours start")).toBeVisible()

    await page.getByRole("button", { name: "Remove" }).click()
    await expect(page.getByText("Notification settings saved")).toBeVisible()
    await expect(
      page.getByRole("button", { name: "Set quiet hours" }),
    ).toBeVisible()

    await page.getByRole("button", { name: "Set quiet hours" }).click()
    await expect(page.getByLabel("Quiet hours start")).toBeVisible()
  })

  test("an open balance can be muted from settings, per relationship", async ({
    page,
    browser,
  }) => {
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
        amount: "50.00",
        description: uniqueLabel("WS12 nudge dinner"),
      })

      // The member owes money, so they have exactly one nudgeable
      // relationship — and can silence that one without going dark on the
      // rest of the product.
      await memberPage.goto("/settings")
      await memberPage.getByRole("tab", { name: "Notifications" }).click()

      const relationship = memberPage
        .getByRole("listitem")
        .filter({ hasText: groupName })
      await expect(relationship).toHaveCount(1)

      await relationship.getByRole("button", { name: "Mute" }).click()
      await expect(memberPage.getByText("Reminders muted")).toBeVisible()

      await memberPage.reload()
      await memberPage.getByRole("tab", { name: "Notifications" }).click()
      await expect(
        memberPage
          .getByRole("listitem")
          .filter({ hasText: groupName })
          .getByRole("button", { name: "Unmute" }),
      ).toBeVisible()
    } finally {
      await memberContext.close()
    }
  })
})
