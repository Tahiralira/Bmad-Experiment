export const randomEmail = () =>
  `test_${Math.random().toString(36).substring(7)}@example.com`

export const randomTeamName = () =>
  `Team ${Math.random().toString(36).substring(7)}`

export const randomPassword = () => `${Math.random().toString(36).substring(2)}`

export const slugify = (text: string) =>
  text
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^\w-]+/g, "")

/**
 * A label that cannot collide with another test's, or with a previous run's.
 *
 * Expense descriptions must be unique because `/pending` spans groups: the
 * chromium project shares ONE signed-in account (playwright/.auth/user.json),
 * so every test's expenses land in the same person's queue and parallel
 * workers see each other's rows.
 */
export const uniqueLabel = (prefix: string) =>
  `${prefix} ${Math.random().toString(36).slice(2, 9)}`
