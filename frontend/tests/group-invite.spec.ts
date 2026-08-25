import { expect, test } from "@playwright/test"

import { registerAndSignIn } from "./utils/auth"
import { createGroup, expectMemberCount } from "./utils/groups"
import { randomEmail, randomTeamName } from "./utils/random"

/**
 * The viral loop: an owner creates a group, generates an invite, and someone
 * else joins through it. This is the one flow the product cannot grow without.
 */


test.describe("group invite loop", () => {
  test("an owner creates a group and a second person joins by invite link", async ({
    page,
    browser,
  }) => {
    const groupName = randomTeamName()

    // --- Owner creates the group -------------------------------------------
    const groupUrl = await createGroup(page, groupName)
    await expectMemberCount(page, 1)

    // --- Owner generates an invite -----------------------------------------
    await page.getByRole("button", { name: "Generate Invite Link" }).click()

    const inviteInput = page.locator('input[readonly]')
    await expect(inviteInput).toBeVisible()
    const inviteUrl = await inviteInput.inputValue()
    expect(inviteUrl).toContain("/invite/")

    const invitePath = new URL(inviteUrl).pathname

    // --- A second person registers and joins --------------------------------
    const joinerContext = await browser.newContext({
      storageState: { cookies: [], origins: [] },
      bypassCSP: true,
    })
    const joinerPage = await joinerContext.newPage()

    try {
      await registerAndSignIn(
        joinerPage,
        joinerContext.request,
        randomEmail(),
      )

      await joinerPage.goto(invitePath)
      await expect(
        joinerPage.getByRole("heading", { name: new RegExp(groupName) }),
      ).toBeVisible()

      await joinerPage
        .getByRole("button", { name: new RegExp(`Join ${groupName}`) })
        .click()

      // Accepting drops them straight into the group they just joined.
      await joinerPage.waitForURL(/\/groups\/[0-9a-f-]+$/)

      // The joiner now sees the group among their own.
      await joinerPage.goto("/groups")
      await expect(
        joinerPage.getByRole("link", { name: new RegExp(groupName) }),
      ).toBeVisible()
    } finally {
      await joinerContext.close()
    }

    // --- The owner's view reflects the new member ---------------------------
    await page.goto(groupUrl)
    await expectMemberCount(page, 2)
  })

  test("an invite link preview does not join you on its own", async ({
    page,
    browser,
  }) => {
    const groupName = randomTeamName()
    const groupUrl = await createGroup(page, groupName)

    await page.getByRole("button", { name: "Generate Invite Link" }).click()
    const inviteUrl = await page.locator('input[readonly]').inputValue()
    const invitePath = new URL(inviteUrl).pathname

    const lurkerContext = await browser.newContext({
      storageState: { cookies: [], origins: [] },
      bypassCSP: true,
    })
    const lurkerPage = await lurkerContext.newPage()

    try {
      await registerAndSignIn(lurkerPage, lurkerContext.request, randomEmail())

      // Look at the invite, then walk away without pressing Join (WS8/S5-M4:
      // viewing an invite must never be a membership side effect).
      await lurkerPage.goto(invitePath)
      await expect(
        lurkerPage.getByRole("button", { name: new RegExp(`Join ${groupName}`) }),
      ).toBeVisible()
      await lurkerPage.goto("/groups")
      await expect(
        lurkerPage.getByRole("link", { name: new RegExp(groupName) }),
      ).toHaveCount(0)
    } finally {
      await lurkerContext.close()
    }

    await page.goto(groupUrl)
    await expectMemberCount(page, 1)
  })
})
