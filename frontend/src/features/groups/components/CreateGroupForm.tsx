import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { SUPPORTED_CURRENCIES, guessLocaleCurrency } from "@/lib/currency"
import { useCustomToast } from "@/shared/hooks/useCustomToast"

import { useCreateGroup } from "../api/groups"
import {
  GROUP_TEMPLATES,
  TEMPLATE_SUGGESTED_NAMES,
  type GroupTemplateId,
} from "../templates"

interface Props {
  onSuccess?: () => void
}

export function CreateGroupForm({ onSuccess }: Props) {
  const [name, setName] = useState("")
  // Locale-detected default (WS10.1) — editable before creating, and later in
  // group settings.
  const [currency, setCurrency] = useState<string>(() => guessLocaleCurrency())
  // WS10.4: onboarding template. Presets the name + the social contract
  // (strict_mode). null = no template chosen; the backend then uses its
  // default. Selecting a chip fills the name only while it's still a template
  // default, so a user's own typed name is never clobbered.
  const [templateId, setTemplateId] = useState<GroupTemplateId | null>(null)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const createGroup = useCreateGroup()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const selectedTemplate =
    GROUP_TEMPLATES.find((t) => t.id === templateId) ?? null

  const handleSelectTemplate = (id: GroupTemplateId) => {
    // Toggle off if the same chip is tapped again.
    if (id === templateId) {
      setTemplateId(null)
      return
    }
    const template = GROUP_TEMPLATES.find((t) => t.id === id)
    if (!template) return
    setTemplateId(id)
    // Only auto-fill the name if the user hasn't typed one of their own.
    const trimmed = name.trim()
    if (!trimmed || TEMPLATE_SUGGESTED_NAMES.has(trimmed)) {
      setName(template.suggestedName)
    }
  }

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
      await createGroup.mutateAsync({
        name: trimmedName,
        currency,
        // Only send the preset when a template is chosen; otherwise let the
        // backend default stand (WS10.4).
        ...(selectedTemplate
          ? { strict_mode: selectedTemplate.strictMode }
          : {}),
      })
      showSuccessToast("Group created successfully!")
      if (onSuccess) {
        onSuccess()
      } else {
        // Redirect to groups page
        navigate({ to: "/groups" })
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create group"
      setError(message)
      showErrorToast(message)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* WS10.4: onboarding templates — one tap presets the name + the social
          contract instead of asking configuration questions. */}
      <div className="space-y-2">
        <Label asChild>
          <span id="group-template-label">Start from a template</span>
        </Label>
        <div
          role="group"
          aria-labelledby="group-template-label"
          className="flex flex-wrap gap-2"
        >
          {GROUP_TEMPLATES.map((template) => {
            const selected = template.id === templateId
            return (
              <button
                key={template.id}
                type="button"
                onClick={() => handleSelectTemplate(template.id)}
                aria-pressed={selected}
                disabled={createGroup.isPending}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  "disabled:opacity-50 disabled:cursor-not-allowed",
                  selected
                    ? "border-primary bg-primary/10 text-primary font-medium"
                    : "border-border text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
              >
                <span aria-hidden="true">{template.emoji}</span>
                {template.label}
              </button>
            )
          })}
        </div>
        <p className="text-sm text-muted-foreground min-h-[1.25rem]">
          {selectedTemplate
            ? selectedTemplate.blurb
            : "Optional — pick one to prefill, or just name your group below."}
        </p>
      </div>

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

      <div className="space-y-2">
        <Label htmlFor="create-group-currency">Currency</Label>
        <Select
          value={currency}
          onValueChange={setCurrency}
          disabled={createGroup.isPending}
        >
          <SelectTrigger id="create-group-currency" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SUPPORTED_CURRENCIES.map((c) => (
              <SelectItem key={c.code} value={c.code}>
                {c.code} — {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">
          All expenses in this group use this currency. You can change it later.
        </p>
      </div>

      {error && <div className="text-sm text-destructive">{error}</div>}

      <Button type="submit" disabled={createGroup.isPending} className="w-full">
        {createGroup.isPending ? "Creating..." : "Create Group"}
      </Button>
    </form>
  )
}

export default CreateGroupForm
