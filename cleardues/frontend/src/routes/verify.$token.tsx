import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { useEffect, useRef, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { AuthLayout } from "@/components/Common/AuthLayout"
import { AuthService } from "@/client"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/verify/$token")({
  component: VerifyMagicLink,
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
        title: "Verifying - ClearDues",
      },
    ],
  }),
})

function VerifyMagicLink() {
  const { token } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const hasAttempted = useRef(false)

  const verifyMutation = useMutation({
    mutationFn: () => AuthService.verifyMagicLink({ token }),
    onSuccess: (data) => {
      // Store the access token
      localStorage.setItem("access_token", data.access_token)
      // Invalidate user query to refresh
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      // Redirect to dashboard
      navigate({ to: "/" })
    },
    onError: (error: Error & { body?: { detail?: string } }) => {
      const message = error.body?.detail || error.message || "Verification failed"
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
            <h1 className="text-2xl font-bold">Verification Failed</h1>
            <p className="text-muted-foreground">{error}</p>
          </div>

          <div className="space-y-4">
            <a
              href="/register"
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Request a new magic link
            </a>

            <p className="text-sm text-muted-foreground">
              Or{" "}
              <a href="/login" className="underline underline-offset-4">
                log in with password
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
          <h1 className="text-2xl font-bold">Verifying your account...</h1>
          <p className="text-muted-foreground">
            Please wait while we complete your registration.
          </p>
        </div>
      </div>
    </AuthLayout>
  )
}

export default VerifyMagicLink
