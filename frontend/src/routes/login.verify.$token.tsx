import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { useEffect, useRef, useState } from "react"
import { AuthService } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import { isLoggedIn } from "@/hooks/useAuth"
import { EVENTS, track } from "@/lib/analytics"
import { processPendingInvite } from "./invite.$token"

export const Route = createFileRoute("/login/verify/$token")({
  component: VerifyLoginMagicLink,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Logging In - ClearDues",
      },
    ],
  }),
})

function VerifyLoginMagicLink() {
  const { token } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const hasAttempted = useRef(false)

  const verifyMutation = useMutation({
    mutationFn: () => AuthService.verifyLoginMagicLink({ token }),
    onSuccess: (data) => {
      // Store the access token
      localStorage.setItem("access_token", data.access_token)
      track(EVENTS.AUTH_LOGGED_IN, { method: "magic_link" })
      // Invalidate user query to refresh
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      // Check for pending invite token from before login
      const pendingInviteToken = processPendingInvite()
      if (pendingInviteToken) {
        // Redirect to accept the pending invite
        navigate({
          to: "/invite/$token",
          params: { token: pendingInviteToken },
        })
      } else {
        // Redirect to dashboard
        navigate({ to: "/" })
      }
    },
    onError: (error: Error & { body?: { detail?: string } }) => {
      const message =
        error.body?.detail || error.message || "Login verification failed"
      setError(message)
    },
  })

  useEffect(() => {
    // Only verify once on mount (prevents double-verification in React Strict Mode)
    if (!hasAttempted.current) {
      hasAttempted.current = true
      verifyMutation.mutate()
    }
  }, [verifyMutation])

  if (error) {
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>

          <div className="space-y-2">
            <h1 className="text-title font-semibold">Login Failed</h1>
            <p className="text-muted-foreground">{error}</p>
          </div>

          <div className="space-y-4">
            <a
              href="/login"
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Request a new login link
            </a>

            <p className="text-sm text-muted-foreground">
              Don't have an account?{" "}
              <a href="/register" className="underline underline-offset-4">
                Register
              </a>
            </p>
          </div>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />

        <div className="space-y-2">
          <h1 className="text-title font-semibold">Logging you in...</h1>
          <p className="text-muted-foreground">
            Please wait while we verify your login link.
          </p>
        </div>
      </div>
    </AuthLayout>
  )
}

export default VerifyLoginMagicLink
