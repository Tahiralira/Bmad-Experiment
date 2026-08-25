import type { Page } from "@playwright/test"

const API_URL = process.env.VITE_API_URL ?? "http://localhost:8000"

/**
 * Borrow the signed-in user's token so a test can talk to the API directly.
 *
 * Used only for steps the UI genuinely cannot perform — see `applyEqualSplit`.
 * Anything a user can do, the journeys do through the interface.
 */
async function authHeader(page: Page): Promise<Record<string, string>> {
  const token = await page.evaluate(() =>
    window.localStorage.getItem("access_token"),
  )

  if (!token) {
    throw new Error("No access_token in localStorage — is this page signed in?")
  }

  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
}

export function groupIdFromUrl(groupUrl: string): string {
  const id = new URL(groupUrl).pathname.split("/").pop()
  if (!id) throw new Error(`No group id in ${groupUrl}`)
  return id
}

/** The newest expense in a group, as the API sees it. */
export async function latestExpense(
  page: Page,
  groupId: string,
): Promise<{ id: string; status: string; description: string }> {
  const res = await page.request.get(
    `${API_URL}/api/v1/expense-groups/${groupId}/expenses`,
    { headers: await authHeader(page) },
  )

  if (!res.ok()) {
    throw new Error(`Listing expenses failed: ${res.status()} ${await res.text()}`)
  }

  const body = await res.json()
  const first = body.data?.[0]?.expense ?? body.data?.[0]

  if (!first) {
    throw new Error(`Group ${groupId} has no expenses`)
  }

  return first
}

/**
 * Split an expense equally across the group.
 *
 * ⚠️ This is a **workaround for a gap in the product**, not a testing
 * shortcut. `ExpenseForm` (the manual "Add Expense" path) posts only
 * `{group_id, amount, description}`, which leaves the expense in `draft`.
 * Nothing in the UI can then assign splits to it: `SplitPicker` is rendered
 * only by `EditableExpensePreview`, which sits behind the AI parse flow, and
 * an expense row on the ledger merely expands. So a manually-created expense
 * can never reach `pending_confirmation`, never be confirmed, and never move
 * a balance.
 *
 * Driving the AI path instead would make CI depend on a hosted LLM key, so
 * these journeys apply the split over the API and continue through the UI
 * from there. When the manual form grows a split step, delete this and let the
 * journey click it.
 */
export async function applyEqualSplit(
  page: Page,
  expenseId: string,
): Promise<void> {
  const res = await page.request.put(
    `${API_URL}/api/v1/expenses/${expenseId}/split`,
    { headers: await authHeader(page), data: { type: "equal" } },
  )

  if (!res.ok()) {
    throw new Error(
      `Applying the equal split failed: ${res.status()} ${await res.text()}`,
    )
  }
}
