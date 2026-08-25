import { test as setup } from "@playwright/test"

import { registerAndSignIn } from "./utils/auth"
import { randomEmail } from "./utils/random"

const authFile = "playwright/.auth/user.json"

/**
 * Creates the shared signed-in account the chromium project reuses.
 *
 * Before WS11 this filled a password field that the app no longer has — the
 * template's password login was removed in WS8, so the whole suite was
 * authenticating against a form that had ceased to exist.
 */
setup("authenticate", async ({ page, request }) => {
  await registerAndSignIn(page, request, randomEmail())
  await page.context().storageState({ path: authFile })
})
