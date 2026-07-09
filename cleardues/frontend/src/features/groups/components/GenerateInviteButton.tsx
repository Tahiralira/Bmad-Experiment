import { useState } from "react"

import { useCreateInvite } from "../api/groups"

interface Props {
  groupId: string
}

export function GenerateInviteButton({ groupId }: Props) {
  const [inviteUrl, setInviteUrl] = useState<string | null>(null)
  const [expiresAt, setExpiresAt] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const createInvite = useCreateInvite()

  const handleGenerate = async () => {
    setError(null)
    try {
      const result = await createInvite.mutateAsync(groupId)
      if (result.invite?.invite_url) {
        setInviteUrl(result.invite.invite_url)
        setExpiresAt(result.invite.expires_at ?? null)
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create invite"
      setError(errorMessage)
    }
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
    if (inviteUrl) {
      await navigator.clipboard.writeText(inviteUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleShare = async () => {
    if (inviteUrl && navigator.share) {
      try {
        await navigator.share({
          title: "Join my expense group",
          text: "Click to join our expense tracking group",
          url: inviteUrl,
        })
      } catch {
        // User cancelled or share failed, fall back to copy
        handleCopy()
      }
    } else {
      handleCopy()
    }
  }

  if (!inviteUrl) {
    return (
      <div className="space-y-2">
        <button
          onClick={handleGenerate}
          disabled={createInvite.isPending}
          className="rounded-md bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50"
        >
          {createInvite.isPending ? "Generating..." : "Generate Invite Link"}
        </button>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 rounded-md border bg-gray-50 p-2">
        <input
          type="text"
          value={inviteUrl}
          readOnly
          className="flex-1 bg-transparent text-sm"
        />
        <button
          onClick={handleCopy}
          className="rounded px-2 py-1 text-sm hover:bg-gray-200"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      {expiresAt && (
        <p className="text-xs text-gray-500">
          Expires: {formatExpirationDate(expiresAt)}
        </p>
      )}
      <button
        onClick={handleShare}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
      >
        Share Invite
      </button>
    </div>
  )
}
