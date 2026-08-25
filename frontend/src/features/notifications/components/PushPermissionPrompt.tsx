import { Bell, X } from "lucide-react"
import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"

import {
  useRegisterPushSubscription,
  useVapidPublicKey,
} from "../api/notifications"
import { checkPushSupport, getPermission, subscribeToPush } from "../lib/push"

// Dismissal is remembered locally, not server-side: it's a UI preference
// about this browser, and the browser is also where the permission lives.
const DISMISSED_KEY = "cleardues:push-prompt-dismissed"

/**
 * The push permission ask (WS10.7, delivered in WS12).
 *
 * Shown ONLY after the user has a confirmed expense — i.e. after they have
 * something a reminder could be about. A browser grants the permission
 * prompt once and a denial is close to permanent, so asking on first load,
 * before the app has done anything for them, spends the single most
 * valuable interaction the product gets.
 *
 * This is a soft pre-prompt: clicking "Remind me" is what triggers the
 * browser's real dialog. Dismissing costs nothing and can be undone from
 * notification settings.
 */
export function PushPermissionPrompt({ eligible }: { eligible: boolean }) {
  const { data: vapid } = useVapidPublicKey()
  const registerPush = useRegisterPushSubscription()
  const [dismissed, setDismissed] = useState(true)
  const [permission, setPermission] = useState(getPermission())

  useEffect(() => {
    try {
      setDismissed(localStorage.getItem(DISMISSED_KEY) === "1")
    } catch {
      // Private mode or blocked storage — show the prompt; a duplicate ask
      // is better than never asking.
      setDismissed(false)
    }
  }, [])

  const support = checkPushSupport()

  // Every condition must hold: the user has something to be reminded about,
  // the browser can do push, the server can send it, and we haven't already
  // asked or been answered.
  if (
    !eligible ||
    dismissed ||
    !support.supported ||
    !vapid?.key ||
    permission !== "default"
  ) {
    return null
  }

  const dismiss = () => {
    setDismissed(true)
    try {
      localStorage.setItem(DISMISSED_KEY, "1")
    } catch {
      // Nothing to do — the in-memory state already hid it for this session.
    }
  }

  const enable = async () => {
    const subscription = await subscribeToPush(vapid.key!)
    setPermission(getPermission())
    if (subscription) {
      registerPush.mutate(subscription)
    }
    // Granted or denied, the ask is done — don't re-prompt either way.
    dismiss()
  }

  return (
    <div
      role="region"
      aria-label="Notification reminder offer"
      // Stacked below sm, a row above it. `flex-1` alone let the copy shrink
      // to a ~100px column at 375px rather than pushing the buttons onto
      // their own line — caught in the DoD screenshots, not in review.
      className="border-border bg-card flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-center"
    >
      <div className="flex items-start gap-3 sm:items-center">
        <Bell
          className="text-muted-foreground mt-0.5 size-5 shrink-0 sm:mt-0"
          aria-hidden="true"
        />
        <div className="min-w-0">
          <p className="font-medium">Want ClearDues to keep track for you?</p>
          <p className="text-muted-foreground text-sm">
            One quiet reminder when a balance has been sitting a while — never
            per expense, and you can mute any of it.
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 sm:ml-auto">
        <Button size="sm" onClick={enable}>
          Remind me
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={dismiss}
          aria-label="Not now"
        >
          <X className="size-4" />
        </Button>
      </div>
    </div>
  )
}
