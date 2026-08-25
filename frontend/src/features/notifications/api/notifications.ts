import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import type {
  NotificationPreferencePublic,
  NotificationPreferenceUpdate,
  NudgeRelationshipPublic,
  NudgeStateUpdate,
} from "@/client"
import { NotificationsService } from "@/client"
import { EVENTS, track } from "@/lib/analytics"
import { getApiErrorMessage } from "@/utils"

// Every call goes through the GENERATED client (the WS11 rule) — no
// hand-built URLs, no hand-maintained response types.

const PREFERENCES_KEY = ["notification-preferences"]
const RELATIONSHIPS_KEY = ["nudge-relationships"]
const VAPID_KEY = ["vapid-public-key"]

// === Preferences ===

export function useNotificationPreferences() {
  return useQuery<NotificationPreferencePublic, Error>({
    queryKey: PREFERENCES_KEY,
    queryFn: () => NotificationsService.getMyPreferences(),
  })
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient()
  return useMutation<
    NotificationPreferencePublic,
    Error,
    NotificationPreferenceUpdate
  >({
    mutationFn: (requestBody) =>
      NotificationsService.updateMyPreferences({ requestBody }),
    onSuccess: (prefs, variables) => {
      // The PRD's kill-switch metric: turning nudges OFF is the stop signal
      // the product is required to be able to see. Only the transition is
      // tracked, and only as a boolean — never the quiet-hours schedule,
      // which would say when someone sleeps.
      if (variables.nudges_enabled === false) {
        track(EVENTS.NUDGE_MUTED, { scope: "all" })
      }
      queryClient.setQueryData(PREFERENCES_KEY, prefs)
      toast.success("Notification settings saved")
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  })
}

// === Per-relationship mute / snooze ===

export function useNudgeRelationships() {
  return useQuery<Array<NudgeRelationshipPublic>, Error>({
    queryKey: RELATIONSHIPS_KEY,
    queryFn: () => NotificationsService.listNudgeRelationships(),
  })
}

type RelationshipUpdate = {
  groupId: string
  counterpartyUserId: string
} & NudgeStateUpdate

export function useUpdateNudgeRelationship() {
  const queryClient = useQueryClient()
  return useMutation<NudgeRelationshipPublic, Error, RelationshipUpdate>({
    mutationFn: ({ groupId, counterpartyUserId, ...body }) =>
      NotificationsService.updateNudgeRelationship({
        groupId,
        counterpartyUserId,
        requestBody: body,
      }),
    onSuccess: (relationship, variables) => {
      if (variables.muted === true) {
        track(EVENTS.NUDGE_MUTED, { scope: "relationship" })
      }
      queryClient.invalidateQueries({ queryKey: RELATIONSHIPS_KEY })
      toast.success(
        relationship.muted
          ? "Reminders muted"
          : relationship.snoozed_until
            ? "Reminders snoozed"
            : "Reminders on",
      )
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  })
}

// === Web push ===

/**
 * The server's VAPID public key, or null when push isn't configured.
 *
 * Fetched BEFORE any permission prompt: a browser grants that prompt once,
 * and spending it on a server that cannot send push wastes it permanently.
 */
export function useVapidPublicKey() {
  return useQuery<{ key: string | null }, Error>({
    queryKey: VAPID_KEY,
    queryFn: () => NotificationsService.getVapidPublicKey(),
    staleTime: Infinity,
  })
}

export function useRegisterPushSubscription() {
  return useMutation<
    unknown,
    Error,
    { endpoint: string; p256dh: string; auth: string }
  >({
    mutationFn: (requestBody) =>
      NotificationsService.registerPushSubscription({ requestBody }),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  })
}

export function useDeletePushSubscription() {
  return useMutation<unknown, Error, { endpoint: string }>({
    mutationFn: ({ endpoint }) =>
      NotificationsService.deletePushSubscription({ endpoint }),
    // Deliberately quiet: this fires as cleanup when the user switches push
    // off, and they already got feedback from the toggle itself.
  })
}
