import { OpenAPI } from "@/shared/api"

import type { ExpenseParseResponse } from "../types"

/**
 * Client for POST /expenses/parse (WS7 — the real AI path, S4-C2).
 *
 * The endpoint streams Server-Sent Events over a POST response, which
 * EventSource cannot do — so this reads the fetch body stream directly.
 *
 * Error contract (mirrors the backend docstring):
 * - Pre-stream failures are HTTP errors with a mediator-voice `detail`
 *   (403 not a member, 429 free quota exhausted, 503 AI unavailable).
 * - Mid-stream failures arrive as `{"type":"error","error":"..."}` events.
 * Both surface here as ParseError with a user-displayable message.
 */

export class ParseError extends Error {}

type ParseStreamEvent =
  | { type: "commentary"; data: { text: string } }
  | { type: "complete"; data: Record<string, unknown> }
  | { type: "error"; error: string }

export interface ParseExpenseOptions {
  text: string
  /**
   * Group to parse within. Omit for a SANDBOX onboarding parse (WS10.4) — the
   * "try one expense" aha moment before the user has any group. The backend
   * skips the membership check when no group_id is sent.
   */
  groupId?: string
  /** Called for each commentary chunk (word-level) as it streams in */
  onCommentary?: (chunk: string) => void
  /** Abort when the modal closes / a new parse supersedes this one */
  signal?: AbortSignal
}

const GENERIC_ERROR =
  "Something went wrong talking to the AI. Please try again or use the manual form."

export async function parseExpense({
  text,
  groupId,
  onCommentary,
  signal,
}: ParseExpenseOptions): Promise<ExpenseParseResponse> {
  const token = localStorage.getItem("access_token") || ""
  const response = await fetch(`${OpenAPI.BASE}/api/v1/expenses/parse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    // Send group_id only when parsing within a group; a sandbox parse omits it.
    body: JSON.stringify(groupId ? { text, group_id: groupId } : { text }),
    signal,
  })

  if (!response.ok) {
    let detail = GENERIC_ERROR
    try {
      const body = await response.json()
      if (typeof body?.detail === "string") detail = body.detail
    } catch {
      // non-JSON error body — keep the generic message
    }
    throw new ParseError(detail)
  }

  if (!response.body) {
    throw new ParseError("Streaming isn't supported in this browser.")
  }

  let complete: ExpenseParseResponse | null = null

  const handleLine = (line: string) => {
    if (!line.startsWith("data: ")) return
    let event: ParseStreamEvent
    try {
      event = JSON.parse(line.slice("data: ".length)) as ParseStreamEvent
    } catch {
      return // tolerate a malformed frame rather than dropping the parse
    }
    if (event.type === "commentary") {
      onCommentary?.(event.data.text)
    } else if (event.type === "error") {
      throw new ParseError(event.error || GENERIC_ERROR)
    } else if (event.type === "complete") {
      const data = event.data
      complete = {
        ...data,
        // Decimal string on the wire (WS4/M1) -> number for the edit buffer
        amount: Number(data.amount),
      } as ExpenseParseResponse
    }
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let boundary: number
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        for (const line of frame.split("\n")) handleLine(line)
      }
    }
    // a final frame without a trailing blank line still counts
    for (const line of buffer.split("\n")) handleLine(line)
  } finally {
    reader.releaseLock()
  }

  if (!complete) {
    throw new ParseError("The parse ended unexpectedly. Please try again.")
  }
  return complete
}
