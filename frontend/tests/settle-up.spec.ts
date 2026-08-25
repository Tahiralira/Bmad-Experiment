import { expect, test } from "@playwright/test"

import { createConfirmedExpense, createGroupWithMember } from "./utils/groups"
import { randomTeamName, uniqueLabel } from "./utils/random"

/**
 * Settling is the point of the product — the balance a nudge would chase is
 * the balance this journey clears. Both halves are deliberate: the debtor
 * *claims* they paid, and the creditor confirms it. Nothing settles itself.
 */
test.describe("settle up", () => {
  test("the debtor marks paid, the creditor confirms, and the balance clears", async ({
    page,
    browser,
  }) => {
    const groupName = randomTeamName()
    const description = uniqueLabel("WS11 settle dinner")
    const { groupUrl, memberContext, memberPage, memberEmail } =
      await createGroupWithMember(page, browser, groupName)

    try {
      await createConfirmedExpense(page, memberPage, {
        groupUrl,
        groupName,
        amount: "84.00",
        description,
      })

      // The member owes half.
      await memberPage.goto(groupUrl)
      const memberBalances = memberPage.getByRole("region", {
        name: "Balances with members",
      })
      await expect(memberBalances.getByText("You owe $42.00")).toBeVisible()

      // --- Debtor claims they paid ------------------------------------------
      await memberPage
        .getByRole("button", { name: /^Settle up with / })
        .first()
        .click()
      await memberPage.getByRole("button", { name: "Yes, I paid" }).click()

      // The claim is now waiting on the other side; it must NOT self-clear.
      await expect(memberPage.getByText("Settle-up pending")).toBeVisible()

      // --- Creditor confirms -------------------------------------------------
      await page.goto(groupUrl)
      const claims = page.getByRole("region", { name: "Settlement claims" })
      await expect(
        claims.getByRole("heading", {
          name: `Settle-up from ${memberEmail}`,
        }),
      ).toBeVisible()

      await page
        .getByRole("button", { name: /^Confirm settle-up from / })
        .first()
        .click()

      // --- Balance is clear on both sides ------------------------------------
      await expect(
        page
          .getByRole("region", { name: "Balances with members" })
          .getByText(/Owes you \$/),
      ).toHaveCount(0)

      await memberPage.goto(groupUrl)
      await expect(
        memberPage
          .getByRole("region", { name: "Balances with members" })
          .getByText(/You owe \$/),
      ).toHaveCount(0)
    } finally {
      await memberContext.close()
    }
  })

  test("a settle-up claim does not clear the balance until it is confirmed", async ({
    page,
    browser,
  }) => {
    const groupName = randomTeamName()
    const description = uniqueLabel("WS11 unconfirmed claim")
    const { groupUrl, memberContext, memberPage } =
      await createGroupWithMember(page, browser, groupName)

    try {
      await createConfirmedExpense(page, memberPage, {
        groupUrl,
        groupName,
        amount: "60.00",
        description,
      })

      await memberPage.goto(groupUrl)
      await memberPage
        .getByRole("button", { name: /^Settle up with / })
        .first()
        .click()
      await memberPage.getByRole("button", { name: "Yes, I paid" }).click()
      await expect(memberPage.getByText("Settle-up pending")).toBeVisible()

      // The creditor has not confirmed, so they are still owed the money.
      await page.goto(groupUrl)
      await expect(
        page
          .getByRole("region", { name: "Balances with members" })
          .getByText("Owes you $30.00"),
      ).toBeVisible()
    } finally {
      await memberContext.close()
    }
  })
})
