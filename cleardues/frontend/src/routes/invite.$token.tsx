import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { useEffect, useRef, useState } from "react"

import { AuthLayout } from "@/components/Common/AuthLayout"
import { useAcceptInvite } from "@/features/groups/api/groups"
import { isLoggedIn } from "@/hooks/useAuth"

const PENDING_INVITE_KEY = "pending_invite_token"

export const Route = createFileRoute("/invite/$token")({
  component: AcceptInvitePage,
  beforeLoad: async ({ params }) => {
    if (!isLoggedIn()) {
      // Store token for after login
      sessionStorage.setItem(PENDING_INVITE_KEY, params.token)
      throw redirect({
        to: "/login",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Accept Invite - ClearDues",
      },
    ],
  }),
})

function AcceptInvitePage() {
  const { token } = Route.useParams()
  const navigate = useNavigate()
  const acceptInvite = useAcceptInvite()
  const [error, setError] = useState<string | null>(null)
  const hasAttempted = useRef(false)

  useEffect(() => {
    // Only accept once on mount
    if (!hasAttempted.current) {
      hasAttempted.current = true
      acceptInvite.mutate(token, {
        onSuccess: () => {
          // Clear any stored token
          sessionStorage.removeItem(PENDING_INVITE_KEY)
          // Redirect to dashboard
          navigate({ to: "/" })
        },
        onError: (err: Error & { body?: { detail?: string } }) => {
          const message =
            err.body?.detail || err.message || "Failed to accept invite"
          setError(message)
        },
      })
    }
  }, [token, acceptInvite, navigate])

  if (error) {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="rounded-full bg-red-100 p-4">
            <svg
              className="h-12 w-12 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-bold">Could Not Join Group</h1>
            <p className="text-muted-foreground">{error}</p>
          </div>

          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Go to Dashboard
          </a>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />

        <div className="space-y-2">
          <h1 className="text-2xl font-bold">Joining group...</h1>
          <p className="text-muted-foreground">
            Please wait while we add you to the expense group.
          </p>
        </div>
      </div>
    </AuthLayout>
  )
}

// Helper to check and process pending invites after login
export function processPendingInvite(): string | null {
  const token = sessionStorage.getItem(PENDING_INVITE_KEY)
  if (token) {
    sessionStorage.removeItem(PENDING_INVITE_KEY)
  }
  return token
}

export default AcceptInvitePage
