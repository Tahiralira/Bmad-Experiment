import { AxiosError } from "axios"
import type { ApiError } from "./client"

// Mediator-voice error mapping (WS8/UX-H4, S4-M4).
//
// Two rules:
// 1. If the server sent a `detail`, SHOW IT — backend messages are already
//    written in the mediator's voice ("You still have unsettled expenses…").
//    Replacing them with hardcoded strings hid the real cause (S4-M4).
// 2. If there is no server message (network down, timeout, 5xx with no
//    body), never surface raw transport strings like axios's "Network
//    Error" — translate to calm, human copy (UX-H4).

const FALLBACK_MESSAGE =
  "Something went wrong on our side. Give it a moment and try again."

const NETWORK_MESSAGE =
  "We couldn't reach ClearDues. Check your connection and try again."

/** Extract the friendliest available message from any API/network error. */
export function getApiErrorMessage(err: unknown): string {
  // Transport-level failures have no server response to speak for them
  if (err instanceof AxiosError && !err.response) {
    return NETWORK_MESSAGE
  }
  if (err instanceof TypeError) {
    // fetch() network failure ("Failed to fetch")
    return NETWORK_MESSAGE
  }

  const body = (err as ApiError | undefined)?.body as
    | { detail?: unknown }
    | null
    | undefined
  const detail = body?.detail

  // Server spoke — pass its message through untouched
  if (typeof detail === "string" && detail.trim()) {
    return detail
  }
  // Pydantic validation errors: [{loc, msg, type}, ...]
  if (Array.isArray(detail) && detail.length > 0 && detail[0]?.msg) {
    return String(detail[0].msg)
  }

  const status = (err as ApiError | undefined)?.status
  if (typeof status === "number" && status >= 500) {
    return FALLBACK_MESSAGE
  }

  return FALLBACK_MESSAGE
}

/** Show an error toast with the mediator-voice message. */
export function handleError(err: unknown, showToast: (msg: string) => void) {
  showToast(getApiErrorMessage(err))
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
