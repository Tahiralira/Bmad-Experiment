import { useState } from "react"

import { getApiErrorMessage } from "@/utils"
import { useCreateInvite, useRevokeInvite } from "../api/groups"
import type { GroupInvite } from "../types"

interface Props {
  groupId: string
}

export function GenerateInviteButton({ groupId }: Props) {
  const [invite, setInvite] = useState<GroupInvite | null>(null)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const createInvite = useCreateInvite()
  const revokeInvite = useRevokeInvite(groupId)

  const handleGenerate = async () => {
    setError(null)
    try {
      const result = await createInvite.mutateAsync(groupId)
      if (result.invite?.invite_url) {
        setInvite(result.invite)
      }
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  const handleRevoke = () => {
    if (!invite) return
    revokeInvite.mutate(invite.id, {
      onSuccess: () => {
        setInvite(null)
      },
    })
  }

  const formatExpirationDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const handleCopy = async () => {
    if (invite?.invite_url) {
      await navigator.clipboard.writeText(invite.invite_url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleShare = async () => {
    if (invite?.invite_url && navigator.share) {
      try {
        await navigator.share({
          title: "Join my expense group",
          text: "Click to join our expense tracking group",
          url: invite.invite_url,
        })
      } catch {
        // User cancelled or share failed, fall back to copy
        handleCopy()
      }
    } else {
      handleCopy()
    }
  }

  if (!invite) {
    return (
      <div className="space-y-2">
        <button
          onClick={handleGenerate}
          disabled={createInvite.isPending}
          className="min-h-11 rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {createInvite.isPending ? "Generating..." : "Generate Invite Link"}
        </button>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 rounded-md border bg-muted p-2">
        <input
          type="text"
          value={invite.invite_url ?? ""}
          readOnly
          className="flex-1 bg-transparent text-sm"
        />
        <button
          onClick={handleCopy}
          className="rounded px-2 py-1 text-sm hover:bg-accent"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <p className="text-xs text-muted-foreground">
        Good for {invite.max_uses}{" "}
        {invite.max_uses === 1 ? "join" : "joins"} · expires{" "}
        {formatExpirationDate(invite.expires_at)}
      </p>
      <div className="flex gap-2">
        <button
          onClick={handleShare}
          className="min-h-11 flex-1 rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
        >
          Share Invite
        </button>
        <button
          onClick={handleRevoke}
          disabled={revokeInvite.isPending}
          className="min-h-11 rounded-md border border-destructive px-4 py-2 text-destructive hover:bg-destructive/10 disabled:opacity-50"
        >
          {revokeInvite.isPending ? "Revoking..." : "Revoke"}
        </button>
      </div>
    </div>
  )
}
