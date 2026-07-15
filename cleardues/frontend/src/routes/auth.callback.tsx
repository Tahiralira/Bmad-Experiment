/**
 * OAuth callback page.
 *
 * WS8/S5-H1: the backend redirects here with a short-lived ONE-TIME CODE
 * (never the JWT — tokens in URLs land in access logs and history). This
 * page immediately exchanges the code for the access token via POST.
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useEffect, useRef, useState } from "react"

import { request as __request } from "@/client/core/request"
import { AuthLayout } from "@/components/Common/AuthLayout"
import { OpenAPI } from "@/shared/api"
import { getApiErrorMessage } from "@/utils"

export const Route = createFileRoute("/auth/callback")({
  component: OAuthCallbackPage,
  validateSearch: (search: Record<string, unknown>) => ({
    code: search.code as string | undefined,
    error: search.error as string | undefined,
  }),
  head: () => ({
    meta: [
      {
        title: "Completing Sign In - ClearDues",
      },
    ],
  }),
})

interface TokenWithUser {
  access_token: string
  token_type: string
}

function OAuthCallbackPage() {
  const navigate = useNavigate()
  const { code, error } = Route.useSearch()
  const [status, setStatus] = useState<"loading" | "error">("loading")
  const [errorMessage, setErrorMessage] = useState<string>("")
  const hasExchanged = useRef(false)

  useEffect(() => {
    if (error) {
      setStatus("error")
      setErrorMessage(getErrorMessage(error))
      return
    }

    if (code) {
      // Exchange the one-time code for the access token (exactly once —
      // the code is single-use, so a StrictMode double-run would fail)
      if (hasExchanged.current) {
        return
      }
      hasExchanged.current = true
      __request<TokenWithUser>(OpenAPI, {
        method: "POST",
        url: "/api/v1/auth/oauth/exchange",
        body: { code },
        mediaType: "application/json",
      })
        .then((response) => {
          localStorage.setItem("access_token", response.access_token)
          navigate({ to: "/" })
        })
        .catch((err: unknown) => {
          setStatus("error")
          setErrorMessage(getApiErrorMessage(err))
        })
      return
    }

    // No code or error - something went wrong
    setStatus("error")
    setErrorMessage("That sign-in didn't complete. Please try again.")
  }, [code, error, navigate])

  if (status === "error") {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="rounded-full bg-destructive p-4">
            <svg
              className="h-12 w-12 text-destructive"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          <div className="space-y-2">
            <h1 className="text-title font-semibold">Authentication Failed</h1>
            <p className="text-muted-foreground">{errorMessage}</p>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => navigate({ to: "/login" })}
              className="text-primary underline underline-offset-4"
            >
              Try again
            </button>
          </div>
        </div>
      </AuthLayout>
    )
  }

  // Loading state
  return (
    <AuthLayout>
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="animate-spin h-12 w-12 border-4 border-primary border-t-transparent rounded-full" />
        <div className="space-y-2">
          <h1 className="text-title font-semibold">Completing sign in...</h1>
          <p className="text-muted-foreground">
            Please wait while we complete your authentication.
          </p>
        </div>
      </div>
    </AuthLayout>
  )
}

// The backend sends generic error CODES only (WS8/S5-M2) — human copy
// lives here, in the mediator's voice.
function getErrorMessage(errorCode: string): string {
  const errorMessages: Record<string, string> = {
    oauth_failed: "That sign-in didn't complete. Please try again.",
    email_unverified:
      "Your email address isn't verified with that provider yet. Verify it there first, then try again.",
    no_email:
      "We couldn't get your email from that provider. Please try a different sign-in method.",
    no_provider_id:
      "We couldn't verify your identity with that provider. Please try again.",
    inactive: "This account has been deactivated. Please contact support.",
  }
  return (
    errorMessages[errorCode] ||
    "That sign-in didn't complete. Please try again."
  )
}
