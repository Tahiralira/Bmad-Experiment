/**
 * OAuth callback page that handles the redirect from OAuth providers.
 * Reads the JWT token from URL params and stores it in localStorage.
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"

import { AuthLayout } from "@/components/Common/AuthLayout"

export const Route = createFileRoute("/auth/callback")({
  component: OAuthCallbackPage,
  validateSearch: (search: Record<string, unknown>) => ({
    token: search.token as string | undefined,
    error: search.error as string | undefined,
    message: search.message as string | undefined,
  }),
  head: () => ({
    meta: [
      {
        title: "Completing Sign In - ClearDues",
      },
    ],
  }),
})

function OAuthCallbackPage() {
  const navigate = useNavigate()
  const { token, error, message } = Route.useSearch()
  const [status, setStatus] = useState<"loading" | "error">("loading")
  const [errorMessage, setErrorMessage] = useState<string>("")

  useEffect(() => {
    if (error) {
      setStatus("error")
      setErrorMessage(message || getErrorMessage(error))
      return
    }

    if (token) {
      // Store token and redirect to dashboard
      localStorage.setItem("access_token", token)
      navigate({ to: "/" })
      return
    }

    // No token or error - something went wrong
    setStatus("error")
    setErrorMessage("No authentication token received. Please try again.")
  }, [token, error, message, navigate])

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

function getErrorMessage(errorCode: string): string {
  const errorMessages: Record<string, string> = {
    oauth_failed: "OAuth authentication failed. Please try again.",
    no_email:
      "Could not retrieve your email from the OAuth provider. Please try a different login method.",
    no_provider_id:
      "Could not verify your identity with the OAuth provider. Please try again.",
    inactive: "Your account has been deactivated. Please contact support.",
  }
  return (
    errorMessages[errorCode] ||
    "An unexpected error occurred. Please try again."
  )
}
