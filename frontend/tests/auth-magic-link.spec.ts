import { expect, test } from "@playwright/test"

import { randomEmail } from "./utils/random"
import { getMagicLinkPath } from "./utils/mailcatcher"

// A signed-out journey — do not inherit the shared authenticated state.
test.use({ storageState: { cookies: [], origins: [] } })

test.describe("magic-link sign-in", () => {
  test("a new person registers, follows the emailed link, and lands signed in", async ({
    page,
    request,
  }) => {
    const email = randomEmail()

    await page.goto("/register")
    await page.getByTestId("email-input").fill(email)
    await page.getByRole("button", { name: "Send Magic Link" }).click()

    // The app must not confirm or deny whether the address already existed.
    await expect(
      page.getByRole("heading", { name: "Check your email" }),
    ).toBeVisible()
    await expect(page.getByText(email)).toBeVisible()

    const linkPath = await getMagicLinkPath({ request, recipient: email })
    expect(linkPath).toMatch(/^\/verify\//)

    await page.goto(linkPath)
    await page.waitForURL("/")

    // Signed in: the login form is gone and the app shell is rendered.
    await expect(
      page.getByRole("heading", { name: "Login to your account" }),
    ).toHaveCount(0)
  })

  test("an existing account signs in through /login", async ({
    page,
    request,
  }) => {
    const email = randomEmail()

    // Create the account first.
    await page.goto("/register")
    await page.getByTestId("email-input").fill(email)
    await page.getByRole("button", { name: "Send Magic Link" }).click()
    await page.goto(await getMagicLinkPath({ request, recipient: email }))
    await page.waitForURL("/")

    // Now sign in again from a clean slate.
    await page.context().clearCookies()
    await page.evaluate(() => window.localStorage.clear())

    await page.goto("/login")
    await page.getByTestId("email-input").fill(email)
    await page.getByRole("button", { name: "Send Login Link" }).click()
    await expect(
      page.getByRole("heading", { name: "Check your email" }),
    ).toBeVisible()

    const loginPath = await getMagicLinkPath({ request, recipient: email })
    expect(loginPath).toMatch(/^\/login\/verify\//)

    await page.goto(loginPath)
    await page.waitForURL("/")
  })

  test("a tampered token is rejected", async ({ page }) => {
    await page.goto("/login/verify/not-a-real-token")

    await expect(
      page.getByRole("heading", { name: "Login Failed" }),
    ).toBeVisible()

    // Rejection must not leave a usable session behind.
    const token = await page.evaluate(() =>
      window.localStorage.getItem("access_token"),
    )
    expect(token).toBeNull()
  })
})
