import { BellOff, Clock } from "lucide-react"
import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"

import {
  useDeletePushSubscription,
  useNotificationPreferences,
  useNudgeRelationships,
  useRegisterPushSubscription,
  useUpdateNotificationPreferences,
  useUpdateNudgeRelationship,
  useVapidPublicKey,
} from "../api/notifications"
import {
  checkPushSupport,
  getPermission,
  subscribeToPush,
  unsubscribeFromPush,
} from "../lib/push"

const HOURS = Array.from({ length: 24 }, (_, h) => h)

function formatHour(hour: number): string {
  const suffix = hour < 12 ? "am" : "pm"
  const display = hour % 12 === 0 ? 12 : hour % 12
  return `${display}:00${suffix}`
}

function formatSnooze(until: string | null): string | null {
  if (!until) return null
  const date = new Date(until)
  if (Number.isNaN(date.getTime()) || date <= new Date()) return null
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

/**
 * Where one balance stands with the agent, in the plainest words available
 * (WS13).
 *
 * Someone about to press Mute deserves to know whether the agent is on its
 * first gentle reminder or has already stopped on its own — a mute button
 * pressed blind is how a product loses a user it had not yet annoyed. The
 * order is deliberate: an explicit user choice (muted, snoozed) always
 * outranks whatever the engine would otherwise be doing.
 */
function describeNudgeStatus(rel: {
  muted: boolean
  snoozed_until: string | null
  last_level?: number | null
  reminders_exhausted?: boolean
}): string | null {
  if (rel.muted) return "muted"

  const snoozedUntil = formatSnooze(rel.snoozed_until)
  if (snoozedUntil) return `snoozed until ${snoozedUntil}`

  // Level 3 does not exist, so this is the end of the line rather than a
  // pause. Said out loud, because an agent that stopped on purpose and one
  // that is broken look identical from the outside.
  if (rel.reminders_exhausted) return "no more reminders"

  if (rel.last_level === 2) return "second reminder sent"
  if (rel.last_level === 1) return "first reminder sent"
  return null
}

/**
 * Notification settings (WS12). Three layers, coarsest first:
 *   1. the global kill switch,
 *   2. per-channel and quiet hours,
 *   3. per-relationship mute/snooze — the one that lets someone silence one
 *      awkward debt without going dark on the whole product.
 *
 * The order matters: someone arriving here annoyed should find the "stop"
 * control immediately, not after a form.
 */
export function NotificationSettings() {
  const { data: prefs, isLoading } = useNotificationPreferences()
  const update = useUpdateNotificationPreferences()
  const { data: vapid } = useVapidPublicKey()
  const { data: relationships } = useNudgeRelationships()
  const updateRelationship = useUpdateNudgeRelationship()
  const registerPush = useRegisterPushSubscription()
  const deletePush = useDeletePushSubscription()

  const [permission, setPermission] = useState(getPermission())
  const support = checkPushSupport()

  // The browser's permission can change outside this tab (site settings,
  // another window), so re-read it when the tab regains focus rather than
  // trusting the value captured at mount.
  useEffect(() => {
    const refresh = () => setPermission(getPermission())
    window.addEventListener("focus", refresh)
    return () => window.removeEventListener("focus", refresh)
  }, [])

  if (isLoading || !prefs) {
    return <p className="text-muted-foreground text-sm">Loading…</p>
  }

  const pushConfigured = Boolean(vapid?.key)
  const quietHoursOn =
    prefs.quiet_hours_start !== null && prefs.quiet_hours_end !== null

  const handlePushToggle = async (enabled: boolean) => {
    if (enabled && vapid?.key) {
      const subscription = await subscribeToPush(vapid.key)
      setPermission(getPermission())
      if (!subscription) {
        // Denied or unavailable — leave the preference off rather than
        // storing a promise the browser won't keep.
        return
      }
      registerPush.mutate(subscription)
    }
    if (!enabled) {
      const endpoint = await unsubscribeFromPush()
      if (endpoint) deletePush.mutate({ endpoint })
    }
    update.mutate({ push_enabled: enabled })
  }

  return (
    <div className="flex flex-col gap-6 max-w-xl">
      {/* 1 — the stop control, first */}
      <section className="flex flex-col gap-2">
        <div className="flex items-start gap-3">
          <Checkbox
            id="nudges-enabled"
            checked={!prefs.nudges_enabled}
            onCheckedChange={(checked) =>
              update.mutate({ nudges_enabled: !checked })
            }
          />
          <div className="grid gap-1">
            <Label
              htmlFor="nudges-enabled"
              className="flex items-center gap-2 font-medium"
            >
              <BellOff className="size-4" aria-hidden="true" />
              Turn off all reminders
            </Label>
            <p className="text-muted-foreground text-sm">
              ClearDues stops reminding you about anything. Your balances stay
              exactly as they are — you'll just have to come looking.
            </p>
          </div>
        </div>
      </section>

      <Separator />

      {/* 2 — channels and timing */}
      <fieldset
        disabled={!prefs.nudges_enabled}
        className="flex flex-col gap-5 disabled:opacity-50"
      >
        <legend className="sr-only">Reminder delivery</legend>

        <section className="flex flex-col gap-3">
          <h3 className="font-medium">How to reach you</h3>

          <div className="flex items-start gap-3">
            <Checkbox
              id="push-enabled"
              checked={prefs.push_enabled && permission === "granted"}
              disabled={!support.supported || !pushConfigured}
              onCheckedChange={(checked) => handlePushToggle(Boolean(checked))}
            />
            <div className="grid gap-1">
              <Label htmlFor="push-enabled">Push notifications</Label>
              {!pushConfigured ? (
                <p className="text-muted-foreground text-sm">
                  Push isn't available on this server yet. Reminders will come
                  by email.
                </p>
              ) : !support.supported ? (
                <p className="text-muted-foreground text-sm">
                  {support.reason === "insecure"
                    ? "Push needs a secure connection."
                    : "This browser can't receive push notifications. On iPhone, add ClearDues to your Home Screen first."}
                </p>
              ) : permission === "denied" ? (
                <p className="text-muted-foreground text-sm">
                  Notifications are blocked for this site. You'll need to allow
                  them in your browser settings to turn this back on.
                </p>
              ) : (
                <p className="text-muted-foreground text-sm">
                  A quiet nudge on your device when a balance has been sitting
                  a while.
                </p>
              )}
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Checkbox
              id="email-enabled"
              checked={prefs.email_enabled}
              onCheckedChange={(checked) =>
                update.mutate({ email_enabled: Boolean(checked) })
              }
            />
            <div className="grid gap-1">
              <Label htmlFor="email-enabled">Email</Label>
              <p className="text-muted-foreground text-sm">
                Used only when a push can't reach you — never both for the same
                reminder.
              </p>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-3">
          <h3 className="flex items-center gap-2 font-medium">
            <Clock className="size-4" aria-hidden="true" />
            Quiet hours
          </h3>
          <p className="text-muted-foreground text-sm">
            Nothing arrives during these hours. A reminder that would have
            landed then waits until the window is over.
          </p>

          {quietHoursOn ? (
            <div className="flex flex-wrap items-center gap-2">
              <Select
                value={String(prefs.quiet_hours_start)}
                onValueChange={(v) =>
                  update.mutate({ quiet_hours_start: Number(v) })
                }
              >
                <SelectTrigger className="w-32" aria-label="Quiet hours start">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {HOURS.map((h) => (
                    <SelectItem key={h} value={String(h)}>
                      {formatHour(h)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <span className="text-muted-foreground text-sm">to</span>
              <Select
                value={String(prefs.quiet_hours_end)}
                onValueChange={(v) =>
                  update.mutate({ quiet_hours_end: Number(v) })
                }
              >
                <SelectTrigger className="w-32" aria-label="Quiet hours end">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {HOURS.map((h) => (
                    <SelectItem key={h} value={String(h)}>
                      {formatHour(h)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => update.mutate({ clear_quiet_hours: true })}
              >
                Remove
              </Button>
            </div>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="self-start"
              onClick={() =>
                update.mutate({ quiet_hours_start: 22, quiet_hours_end: 8 })
              }
            >
              Set quiet hours
            </Button>
          )}
        </section>
      </fieldset>

      {/* 3 — per-relationship */}
      {relationships && relationships.length > 0 && (
        <>
          <Separator />
          <section className="flex flex-col gap-3">
            <h3 className="font-medium">Specific balances</h3>
            <p className="text-muted-foreground text-sm">
              Mute or snooze reminders about one person in one group, without
              changing anything else.
            </p>

            <ul className="flex flex-col gap-2">
              {relationships.map((rel) => {
                const snoozedUntil = formatSnooze(rel.snoozed_until)
                const status = describeNudgeStatus(rel)
                return (
                  <li
                    key={`${rel.group_id}-${rel.counterparty_user_id}`}
                    className="border-border flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium">
                        {rel.counterparty_name ?? "Someone in the group"}
                      </p>
                      <p className="text-muted-foreground truncate text-sm">
                        {rel.group_name}
                        {status ? ` · ${status}` : ""}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <Select
                        value=""
                        onValueChange={(v) =>
                          updateRelationship.mutate({
                            groupId: rel.group_id,
                            counterpartyUserId: rel.counterparty_user_id,
                            snooze_days: Number(v),
                          })
                        }
                      >
                        <SelectTrigger
                          className="w-32"
                          aria-label={`Snooze reminders about ${rel.counterparty_name ?? "this balance"}`}
                        >
                          <SelectValue placeholder="Snooze" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">1 day</SelectItem>
                          <SelectItem value="3">3 days</SelectItem>
                          <SelectItem value="7">1 week</SelectItem>
                          {snoozedUntil && (
                            <SelectItem value="0">Cancel snooze</SelectItem>
                          )}
                        </SelectContent>
                      </Select>

                      <Button
                        variant={rel.muted ? "secondary" : "outline"}
                        size="sm"
                        onClick={() =>
                          updateRelationship.mutate({
                            groupId: rel.group_id,
                            counterpartyUserId: rel.counterparty_user_id,
                            muted: !rel.muted,
                          })
                        }
                      >
                        {rel.muted ? "Unmute" : "Mute"}
                      </Button>
                    </div>
                  </li>
                )
              })}
            </ul>
          </section>
        </>
      )}
    </div>
  )
}
