import type { APIRequestContext } from "@playwright/test"

type Email = {
  id: number
  recipients: string[]
  subject: string
}

/**
 * Mailcatcher wraps each recipient in angle brackets: "<user@example.com>".
 */
function addressedTo(email: Email, recipient: string): boolean {
  return email.recipients.some((r) => r.includes(recipient))
}

async function findEmail({
  request,
  filter,
}: {
  request: APIRequestContext
  filter?: (email: Email) => boolean
}) {
  const response = await request.get(`${process.env.MAILCATCHER_HOST}/messages`)

  let emails = await response.json()

  if (filter) {
    emails = emails.filter(filter)
  }

  const email = emails[emails.length - 1]

  if (email) {
    return email as Email
  }

  return null
}

export function findLastEmail({
  request,
  filter,
  timeout = 10000,
}: {
  request: APIRequestContext
  filter?: (email: Email) => boolean
  timeout?: number
}) {
  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(
      () => reject(new Error("Timeout while trying to get latest email")),
      timeout,
    ),
  )

  const checkEmails = async () => {
    while (true) {
      const emailData = await findEmail({ request, filter })

      if (emailData) {
        return emailData
      }
      // Wait for 100ms before checking again
      await new Promise((resolve) => setTimeout(resolve, 100))
    }
  }

  return Promise.race([timeoutPromise, checkEmails()])
}

/**
 * Pull the magic-link URL out of the newest email sent to `recipient`.
 *
 * The backend builds the link as `{FRONTEND_HOST}/login/verify/{token}` for a
 * login and `{FRONTEND_HOST}/verify/{token}` for a first-time registration
 * (backend/app/utils.py). We match either and return the **path**, so the test
 * can navigate relative to Playwright's baseURL — FRONTEND_HOST inside the
 * compose network is not necessarily the host the browser is talking to.
 */
export async function getMagicLinkPath({
  request,
  recipient,
  timeout = 10000,
}: {
  request: APIRequestContext
  recipient: string
  timeout?: number
}): Promise<string> {
  const email = await findLastEmail({
    request,
    filter: (e) => addressedTo(e, recipient),
    timeout,
  })

  if (!email) {
    throw new Error(`No email arrived for ${recipient}`)
  }

  // `.html`, not `.source`: the MJML-built HTML part is base64-encoded in the
  // raw message, so the URL is not greppable there.
  const body = await (
    await request.get(`${process.env.MAILCATCHER_HOST}/messages/${email.id}.html`)
  ).text()

  const match = body.match(/https?:\/\/[^\s"'<>]+?(\/(?:login\/)?verify\/[A-Za-z0-9._-]+)/)

  if (!match) {
    throw new Error(
      `Could not find a magic link in the email to ${recipient}. ` +
        `Subject was "${email.subject}".`,
    )
  }

  return match[1]
}

/**
 * Mailcatcher keeps every message for the life of the container. Clearing
 * between journeys keeps "the newest email for this address" unambiguous.
 */
export async function clearMailcatcher(request: APIRequestContext) {
  await request.delete(`${process.env.MAILCATCHER_HOST}/messages`)
}
