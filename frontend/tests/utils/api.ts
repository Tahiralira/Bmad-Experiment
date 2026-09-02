import type { Page } from "@playwright/test"

const API_URL = process.env.VITE_API_URL ?? "http://localhost:8000"

/**
 * Borrow the signed-in user's token so a test can READ API state for an
 * assertion (see `latestExpense`). Anything a user can DO, the journeys do
 * through the interface.
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
