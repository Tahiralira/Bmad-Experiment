import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

import { useGroupSettings, useUpdateGroupSettings } from "../api/groups"

interface Props {
  groupId: string
  /** Only the group owner can change settings; members see the state */
  isOwner: boolean
}

/**
 * Group settings (WS6): the strict-mode toggle — the group's confirmation
 * social contract.
 *
 * OFF (default): expenses confirm quietly after a 3-day objection window;
 * anyone can still confirm early or reject.
 * ON: every participant must explicitly confirm each expense (the original
 * ceremony).
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
  )
}
