import { expect, type APIRequestContext, type Page } from "@playwright/test"

import { getMagicLinkPath } from "./mailcatcher"

/**
 * Register a brand-new account and land it signed in.
 *
 * ClearDues is passwordless: the only way in is to ask for a magic link and
 * follow it. These journeys drive that for real — request the link through the
 * UI, read the email out of mailcatcher, follow it — rather than injecting a
 * token, so a break anywhere in that chain fails the test.
 */
export async function registerAndSignIn(
  page: Page,
  request: APIRequestContext,
  email: string,
): Promise<void> {
  await page.goto("/register")

  await page.getByTestId("email-input").fill(email)
  await page.getByRole("button", { name: "Send Magic Link" }).click()

  await expect(
    page.getByRole("heading", { name: "Check your email" }),
  ).toBeVisible()

  const linkPath = await getMagicLinkPath({ request, recipient: email })

  await page.goto(linkPath)
  await page.waitForURL("/")
}

/**
 * Sign in an account that already exists.
 */
export async function signIn(
  page: Page,
  request: APIRequestContext,
  email: string,
): Promise<void> {
  await page.goto("/login")

  await page.getByTestId("email-input").fill(email)
  await page.getByRole("button", { name: "Send Login Link" }).click()

  await expect(
    page.getByRole("heading", { name: "Check your email" }),
  ).toBeVisible()

  const linkPath = await getMagicLinkPath({ request, recipient: email })

  await page.goto(linkPath)
  await page.waitForURL("/")
}
