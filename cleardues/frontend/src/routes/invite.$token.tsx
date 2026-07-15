/**
 * Invite landing page (WS8/S5-M4).
 *
 * Joining used to happen automatically on page load (a state-changing GET —
 * any link prefetcher could join a group). Now the page shows a read-only
 * preview ("X invited you — N members") and joining is an explicit POST
 * behind a button. WS10 extends this into the public preview page.
 */

import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import { AuthLayout } from "@/components/Common/AuthLayout"
import { useAcceptInvite, useInvitePreview } from "@/features/groups/api/groups"
import { isLoggedIn } from "@/hooks/useAuth"
import { getApiErrorMessage } from "@/utils"

const PENDING_INVITE_KEY = "pending_invite_token"

export const Route = createFileRoute("/invite/$token")({
  component: InviteLandingPage,
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
        title: "Group Invite - ClearDues",
      },
    ],
  }),
})

function InviteLandingPage() {
  const { token } = Route.useParams()
  const navigate = useNavigate()
  const preview = useInvitePreview(token)
  const acceptInvite = useAcceptInvite()
  const [joinError, setJoinError] = useState<string | null>(null)

  const handleJoin = () => {
    setJoinError(null)
    acceptInvite.mutate(token, {
      onSuccess: (result) => {
        sessionStorage.removeItem(PENDING_INVITE_KEY)
        if (result.group?.id) {
          navigate({
            to: "/groups/$groupId",
            params: { groupId: result.group.id },
          })
        } else {
          navigate({ to: "/" })
        }
      },
      onError: (err: unknown) => {
        setJoinError(getApiErrorMessage(err))
      },
    })
  }

  if (preview.isLoading) {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
          <p className="text-muted-foreground">Looking up this invite...</p>
        </div>
      </AuthLayout>
    )
  }

  const error =
    joinError ?? (preview.error ? getApiErrorMessage(preview.error) : null)
  if (error || !preview.data) {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="space-y-2">
            <h1 className="text-title font-semibold">Could Not Join Group</h1>
            <p className="text-muted-foreground">
              {error ?? "This invite link doesn't seem to work."}
            </p>
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

  const { group_id, group_name, member_count, already_member } = preview.data

  if (already_member) {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="space-y-2">
            <h1 className="text-title font-semibold">You're already in</h1>
            <p className="text-muted-foreground">
              You're already a member of {group_name}.
            </p>
          </div>
          <button
            onClick={() =>
              navigate({
                to: "/groups/$groupId",
                params: { groupId: group_id },
              })
            }
            className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Open {group_name}
          </button>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="space-y-2">
          <h1 className="text-title font-semibold">
            You're invited to {group_name}
          </h1>
          <p className="text-muted-foreground">
            {member_count} {member_count === 1 ? "member" : "members"} split
            expenses here. Joining shares your name and email with the group.
          </p>
        </div>

        <div className="flex flex-col items-center gap-3">
          <button
            onClick={handleJoin}
            disabled={acceptInvite.isPending}
            className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {acceptInvite.isPending ? "Joining..." : `Join ${group_name}`}
          </button>
          <a
            href="/"
            className="text-sm text-muted-foreground underline underline-offset-4"
          >
            Not now
          </a>
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

export default InviteLandingPage
