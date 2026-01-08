import { useState } from "react"
import { useNavigate } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCustomToast } from "@/shared/hooks/useCustomToast"

import { useCreateGroup } from "../api/groups"

export function CreateGroupForm() {
  const [name, setName] = useState("")
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const createGroup = useCreateGroup()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const trimmedName = name.trim()
    if (!trimmedName) {
      setError("Group name is required")
      return
    }

    if (trimmedName.length > 100) {
      setError("Group name must be 100 characters or less")
      return
    }

    try {
      await createGroup.mutateAsync({ name: trimmedName })
      showSuccessToast("Group created successfully!")
      // Redirect to dashboard or group list
      navigate({ to: "/" })
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create group"
      setError(message)
      showErrorToast(message)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Group Name</Label>
        <Input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Weekend Trip"
          maxLength={100}
          disabled={createGroup.isPending}
        />
        <p className="text-sm text-muted-foreground">
          Give your group a descriptive name
        </p>
      </div>

      {error && (
        <div className="text-sm text-destructive">{error}</div>
      )}

      <Button
        type="submit"
        disabled={createGroup.isPending}
        className="w-full"
      >
        {createGroup.isPending ? "Creating..." : "Create Group"}
      </Button>
    </form>
  )
}

export default CreateGroupForm
