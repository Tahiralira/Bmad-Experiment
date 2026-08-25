import { expect, test } from "@playwright/test"

import { applyEqualSplit, groupIdFromUrl, latestExpense } from "./utils/api"
import {
  actOnPending,
  addExpenseManually,
  createGroupWithMember,
} from "./utils/groups"
import { randomTeamName, uniqueLabel } from "./utils/random"

/**
 * The core ledger action: money goes in, the other person confirms it, and
 * both sides agree on the balance.
 *
 * Note the split step runs over the API — the manual form cannot produce a
 * splittable expense today. `applyEqualSplit` documents why.
 */
test.describe("expense confirmation", () => {
  test("the manual form creates an expense on the group ledger", async ({
    page,
    browser,
  }) => {
    const groupName = randomTeamName()
    const description = uniqueLabel("WS11 dinner")
    const { groupUrl, memberContext } = await createGroupWithMember(
      page,
      browser,
      groupName,
    )

    try {
      await page.goto(groupUrl)
      await addExpenseManually(page, {
        groupName,
        amount: "84.00",
        description,
      })

      await page.goto(groupUrl)
      const expenses = page.getByRole("region", { name: "Expenses" })
      await expect(expenses.getByText(description)).toBeVisible()
      await expect(expenses.getByText("$84.00")).toBeVisible()

      // Current behaviour: no split, so it stays a draft. When the manual
      // form learns to split, this assertion should be the thing that fails.
      const expense = await latestExpense(page, groupIdFromUrl(groupUrl))
      expect(expense.status).toBe("draft")
    } finally {
      await memberContext.close()
    }
  })

  test("a split expense reaches the other member, who confirms it", async ({
    page,
    browser,
  }) => {
    const groupName = randomTeamName()
    const description = uniqueLabel("WS11 dinner")
    const { groupUrl, memberContext, memberPage } =
      await createGroupWithMember(page, browser, groupName)

    try {
      await page.goto(groupUrl)
      await addExpenseManually(page, {
        groupName,
        amount: "84.00",
        description,
      })

      const expense = await latestExpense(page, groupIdFromUrl(groupUrl))
      await applyEqualSplit(page, expense.id)

      // The other member is now asked to confirm their share. It leaves the
      // pending queue once confirmed.
      await memberPage.goto("/pending")
      await actOnPending(memberPage, description, "Confirm")

      // Every split starts pending, the payer's included — the expense is not
      // finalized until the owner confirms their own share too.
      await page.goto("/pending")
      await actOnPending(page, description, "Confirm")

      // Now it counts: the member owes half of the $84.
      const expenseAfter = await latestExpense(page, groupIdFromUrl(groupUrl))
      expect(expenseAfter.status).toBe("confirmed")

      await page.goto(groupUrl)
      const balances = page.getByRole("region", {
        name: "Balances with members",
      })
      // Direction matters as much as the number — assert both.
      await expect(balances.getByText("Owes you $42.00")).toBeVisible()
    } finally {
      await memberContext.close()
    }
  })

  test("a member can reject a share they disagree with", async ({
    page,
    browser,
  }) => {
    const groupName = randomTeamName()
    const description = uniqueLabel("WS11 disputed charge")
    const { groupUrl, memberContext, memberPage } =
      await createGroupWithMember(page, browser, groupName)

    try {
      await page.goto(groupUrl)
      await addExpenseManually(page, {
        groupName,
        amount: "500.00",
        description,
      })

      const expense = await latestExpense(page, groupIdFromUrl(groupUrl))
      await applyEqualSplit(page, expense.id)

      await memberPage.goto("/pending")
      await actOnPending(memberPage, description, "Reject")
    } finally {
      await memberContext.close()
    }
  })
})
