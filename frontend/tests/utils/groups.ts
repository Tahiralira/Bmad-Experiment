import { expect, type Browser, type BrowserContext, type Page } from "@playwright/test"

import { registerAndSignIn } from "./auth"
import { randomEmail } from "./random"

/**
 * Create a group as the signed-in user and land on its detail screen.
 * Returns the group's URL.
 */
export async function createGroup(page: Page, name: string): Promise<string> {
  await page.goto("/groups")
  await page.getByRole("button", { name: "Create Group" }).click()

  const dialog = page.getByRole("dialog")
  await expect(dialog.getByText("Create New Group")).toBeVisible()

  await dialog.getByLabel("Group Name").fill(name)
  await dialog.getByRole("button", { name: "Create Group" }).click()

  await expect(dialog).toBeHidden()

  const groupLink = page.getByRole("link", { name: new RegExp(name) })
  await expect(groupLink).toBeVisible()
  await groupLink.click()
  await page.waitForURL(/\/groups\/[0-9a-f-]+$/)

  // waitForURL is not enough. TanStack Router flips the URL before the new
  // route renders, so for a moment the *list* is still mounted — and the
  // shared test account accumulates groups, so a caller asserting
  // `getByText("1 member")` next matched five or six list cards and failed
  // on strict mode. Wait for the detail screen's own heading instead.
  await expect(page.getByRole("heading", { level: 1, name })).toBeVisible()

  return page.url()
}

/**
 * The group detail header's "N members • created ..." line.
 *
 * Scoped by the "• created" suffix, which only the detail header has: the
 * /groups list cards render a bare "N members", so an unscoped match hits
 * every card the account has ever made.
 */
export async function expectMemberCount(
  page: Page,
  count: number,
): Promise<void> {
  const plural = count === 1 ? "member" : "members"
  await expect(
    page.getByText(new RegExp(`^${count} ${plural} • created `)),
  ).toBeVisible()
}

/** Generate an invite for the open group and return its path. */
export async function generateInvitePath(page: Page): Promise<string> {
  await page.getByRole("button", { name: "Generate Invite Link" }).click()

  const inviteInput = page.locator("input[readonly]")
  await expect(inviteInput).toBeVisible()
  const inviteUrl = await inviteInput.inputValue()

  return new URL(inviteUrl).pathname
}

export type GroupWithMember = {
  groupUrl: string
  groupName: string
  memberContext: BrowserContext
  memberPage: Page
  memberEmail: string
}

/**
 * Set up the shape every ledger journey needs: a group owned by `page`'s user
 * with one other real member, signed in in their own browser context.
 *
 * The second member is registered through the real magic-link flow rather than
 * seeded through the API — an expense's confirmation rules depend on genuine
 * membership rows, and a shortcut here would hide a broken join.
 *
 * Callers must close `memberContext`.
 */
export async function createGroupWithMember(
  page: Page,
  browser: Browser,
  groupName: string,
): Promise<GroupWithMember> {
  const groupUrl = await createGroup(page, groupName)
  const invitePath = await generateInvitePath(page)

  const memberContext = await browser.newContext({
    storageState: { cookies: [], origins: [] },
    bypassCSP: true,
  })
  const memberPage = await memberContext.newPage()
  const memberEmail = randomEmail()

  await registerAndSignIn(memberPage, memberContext.request, memberEmail)
  await memberPage.goto(invitePath)
  await memberPage
    .getByRole("button", { name: new RegExp(`Join ${groupName}`) })
    .click()
  await memberPage.waitForURL(/\/groups\/[0-9a-f-]+$/)

  await page.goto(groupUrl)
  await expectMemberCount(page, 2)

  return { groupUrl, groupName, memberContext, memberPage, memberEmail }
}

/**
 * Add an expense to the currently-open group through the manual form.
 *
 * Deliberately not the AI path: parsing calls a hosted LLM, which needs a key
 * CI does not have and would make the journey depend on a third party's
 * latency and wording. The manual form exercises the same create endpoint.
 */
/**
 * The one card on `/pending` that belongs to `description`.
 *
 * Scoping matters more here than it looks. `/pending` spans every group the
 * signed-in person belongs to, and the chromium project shares ONE account
 * across all tests — so with parallel workers the queue holds other tests'
 * expenses too. The earlier `getByRole("button", { name: /^Confirm/ }).first()`
 * clicked whatever happened to be on top, which confirmed a *different*
 * test's expense and left this one pending. It passed or failed on timing.
 */
export function pendingCard(page: Page, description: string) {
  return page.locator('[data-slot="card"]').filter({ hasText: description })
}

/** Act on the pending card for `description` and wait for it to leave the queue. */
export async function actOnPending(
  page: Page,
  description: string,
  action: "Confirm" | "Reject",
): Promise<void> {
  const card = pendingCard(page, description)
  await expect(card).toBeVisible()
  await card.getByRole("button", { name: new RegExp(`^${action}`) }).click()
  await expect(card).toHaveCount(0)
}
/**
 * Drive an expense all the way to `confirmed` so a journey can start from a
 * real, settle-able balance.
 *
 * Both people confirm: every split starts pending, the payer's included.
 */
export async function createConfirmedExpense(
  ownerPage: Page,
  memberPage: Page,
  {
    groupUrl,
    groupName,
    amount,
    description,
  }: {
    groupUrl: string
    groupName: string
    amount: string
    description: string
  },
): Promise<void> {
  await ownerPage.goto(groupUrl)
  // The manual form splits the expense as it creates it, so both members can
  // confirm their share straight away.
  await addExpenseManually(ownerPage, { groupName, amount, description })

  for (const person of [memberPage, ownerPage]) {
    await person.goto("/pending")
    await actOnPending(person, description, "Confirm")
  }
}

export async function addExpenseManually(
  page: Page,
  {
    groupName,
    amount,
    description,
  }: { groupName: string; amount: string; description: string },
): Promise<void> {
  await page.getByRole("button", { name: "Add an expense" }).click()

  const dialog = page.getByRole("dialog")

  // The group is never preselected, even when the modal is opened from a
  // group's own page — the form stays at "Choose a group above to add an
  // expense" until one is picked.
  await dialog
    .getByRole("combobox", { name: "Select group for this expense" })
    .click()
  await page.getByRole("option", { name: groupName }).click()

  await dialog.getByRole("button", { name: "Switch to Manual Form" }).click()

  await dialog.getByLabel("Amount").fill(amount)
  await dialog.getByLabel("Description").fill(description)
  await dialog.getByRole("button", { name: "Add Expense" }).click()

  await expect(dialog).toBeHidden()
}
