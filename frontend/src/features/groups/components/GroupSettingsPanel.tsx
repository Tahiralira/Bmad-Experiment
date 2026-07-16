import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { useGroupSettings, useUpdateGroupSettings } from "../api/groups"
import type { AIPersonality } from "../types"

interface Props {
  groupId: string
  /** Only the group owner can change settings; members see the state */
  isOwner: boolean
}

const PERSONALITY_OPTIONS: Array<{ value: AIPersonality; label: string }> = [
  { value: "professional", label: "Professional — clear and to the point" },
  { value: "friendly", label: "Friendly — warm and helpful" },
  { value: "funny", label: "Funny — a light joke now and then" },
]

/**
 * Group settings: the strict-mode toggle (WS6 — the group's confirmation
 * social contract) and the AI mediator's tone (WS7 — capped at Funny, UX-H5).
 *
 * Strict mode OFF (default): expenses confirm quietly after a 3-day
 * objection window; anyone can still confirm early or reject.
 * ON: every participant must explicitly confirm each expense.
 */
export function GroupSettingsPanel({ groupId, isOwner }: Props) {
  const { data: settings, isLoading } = useGroupSettings(groupId)
  const updateSettings = useUpdateGroupSettings(groupId)

  if (isLoading || !settings) {
    return (
      <div className="h-12 animate-pulse rounded bg-border" aria-hidden="true" />
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-3 py-2">
        <Checkbox
          id={`strict-mode-${groupId}`}
          checked={settings.strict_mode}
          disabled={!isOwner || updateSettings.isPending}
          onCheckedChange={(checked) =>
            updateSettings.mutate({ strict_mode: checked === true })
          }
          className="mt-0.5"
          aria-describedby={`strict-mode-desc-${groupId}`}
        />
        <div className="min-w-0">
          <Label
            htmlFor={`strict-mode-${groupId}`}
            className="text-body font-medium text-text-primary"
          >
            Strict confirmations
          </Label>
          <p
            id={`strict-mode-desc-${groupId}`}
            className="mt-0.5 text-body-small text-text-secondary"
          >
            {settings.strict_mode
              ? "Every share needs an explicit confirmation before an expense counts."
              : "Expenses confirm quietly after 3 days unless someone objects. Anyone can still confirm early or reject."}
            {!isOwner && " Only the group owner can change this."}
          </p>
        </div>
      </div>

      <div className="py-2">
        <Label
          htmlFor={`ai-personality-${groupId}`}
          className="text-body font-medium text-text-primary"
        >
          Mediator tone
        </Label>
        <p
          id={`ai-personality-desc-${groupId}`}
          className="mt-0.5 mb-2 text-body-small text-text-secondary"
        >
          How the AI comments when someone adds an expense.
          {!isOwner && " Only the group owner can change this."}
        </p>
        <Select
          value={settings.ai_personality}
          disabled={!isOwner || updateSettings.isPending}
          onValueChange={(value) =>
            updateSettings.mutate({ ai_personality: value as AIPersonality })
          }
        >
          <SelectTrigger
            id={`ai-personality-${groupId}`}
            className="w-full"
            aria-describedby={`ai-personality-desc-${groupId}`}
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PERSONALITY_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
