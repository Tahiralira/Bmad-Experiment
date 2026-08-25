/**
 * Groups API hooks.
 *
 * WS11 exemplar: every call goes through the generated `GroupsService`. There
 * are no hand-built `__request(OpenAPI, { method, url })` calls left in this
 * file — a renamed path or a changed body now fails `npm run typecheck`
 * instead of 404-ing in front of a user.
 *
 * The generated services map only 422 to a message; that is fine. FastAPI
 * sends its own `detail` on every HTTPException and `getApiErrorMessage`
 * reads `body.detail` first, so the server's wording is what users see —
 * exactly as it was with the hand-written error maps.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { EVENTS, track } from "@/lib/analytics"
import { GroupsService } from "@/shared/api"
import { getApiErrorMessage } from "@/utils"
import type {
  ExpenseGroup,
  ExpenseGroupCreate,
  ExpenseGroupDetail,
  GroupInviteResponse,
  GroupInvitesResponse,
  GroupMembersListResponse,
  GroupSettings,
  GroupSettingsUpdate,
  InvitePreview,
  PairwiseBalancesResponse,
} from "../types"

export function useCreateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ExpenseGroupCreate) =>
      GroupsService.createGroup({ requestBody: data }),
    onSuccess: () => {
      // Invalidate and refetch groups list
      queryClient.invalidateQueries({ queryKey: ["groups"] })
    },
  })
}

export function useUserGroups() {
  return useQuery<ExpenseGroup[], Error>({
    queryKey: ["groups"],
    queryFn: GroupsService.listUserGroups,
  })
}

// === Group Detail (WS5/B-H7 — backs the /groups/$groupId screen) ===

export function useGroupDetail(groupId: string) {
  return useQuery<ExpenseGroupDetail, Error>({
    queryKey: ["groups", groupId, "detail"],
    queryFn: () => GroupsService.getGroupDetail({ groupId }),
    enabled: !!groupId,
  })
}

// === Pairwise Balances (WS6/S2-F9) ===

export function usePairwiseBalances(groupId: string) {
  return useQuery<PairwiseBalancesResponse, Error>({
    queryKey: ["pairwise-balances", groupId],
    queryFn: () => GroupsService.getPairwiseBalances({ groupId }),
    enabled: !!groupId,
  })
}

// === Group Settings (WS6 strict mode + WS7 AI personality) ===

export function useGroupSettings(groupId: string) {
  return useQuery<GroupSettings, Error>({
    queryKey: ["groups", groupId, "settings"],
    queryFn: () => GroupsService.getGroupSettings({ groupId }),
    enabled: !!groupId,
  })
}

const PERSONALITY_TOAST: Record<GroupSettings["ai_personality"], string> = {
  professional: "The mediator will keep it strictly business",
  friendly: "The mediator is back to its friendly self",
  funny: "The mediator will crack a joke now and then",
}

export function useUpdateGroupSettings(groupId: string) {
  const queryClient = useQueryClient()

  return useMutation<GroupSettings, Error, GroupSettingsUpdate>({
    mutationFn: (data) =>
      GroupsService.updateGroupSettings({ groupId, requestBody: data }),
    onSuccess: (settings, variables) => {
      queryClient.setQueryData(["groups", groupId, "settings"], settings)
      // WS10.6: one event per changed field (the UI PATCHes one at a time)
      for (const setting of [
        "strict_mode",
        "ai_personality",
        "currency",
      ] as const) {
        if (variables[setting] !== undefined) {
          track(EVENTS.GROUP_SETTINGS_UPDATED, { setting })
        }
      }
      if (variables.strict_mode !== undefined) {
        toast.success(
          settings.strict_mode
            ? "Strict mode on — every share needs an explicit confirmation"
            : "Strict mode off — expenses confirm quietly unless someone objects",
        )
      }
      if (variables.ai_personality !== undefined) {
        toast.success(PERSONALITY_TOAST[settings.ai_personality])
      }
      if (variables.currency !== undefined) {
        toast.success(`Group currency set to ${settings.currency}`)
      }
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error))
    },
  })
}

// === Invite API (WS8/S5-M4: preview via GET, join via explicit POST,
// owner revocation, usage caps) ===

export function useCreateInvite() {
  return useMutation({
    mutationFn: (groupId: string) => GroupsService.createInvite({ groupId }),
    onSuccess: () => {
      track(EVENTS.INVITE_CREATED)
    },
  })
}

export function useInvitePreview(token: string) {
  return useQuery<InvitePreview, Error>({
    queryKey: ["invite-preview", token],
    queryFn: () => GroupsService.previewInvite({ token }),
    enabled: !!token,
    retry: false,
  })
}

export function useAcceptInvite() {
  const queryClient = useQueryClient()

  return useMutation<GroupInviteResponse, Error, string>({
    mutationFn: (token: string) => GroupsService.acceptInvite({ token }),
    onSuccess: () => {
      // The signed-in explicit Join; the OAuth-return auto-join tracks
      // itself in auth.callback.tsx with method: "oauth_return".
      track(EVENTS.INVITE_JOINED, { method: "explicit" })
      // Invalidate groups list to show new membership
      queryClient.invalidateQueries({ queryKey: ["groups"] })
    },
  })
}

export function useRevokeInvite(groupId: string) {
  return useMutation({
    mutationFn: (inviteId: string) =>
      GroupsService.revokeInvite({ groupId, inviteId }),
    onSuccess: (result) => {
      toast.success(result.message)
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error))
    },
  })
}

export function useGroupInvites(groupId: string, enabled: boolean) {
  return useQuery<GroupInvitesResponse, Error>({
    queryKey: ["groups", groupId, "invites"],
    queryFn: () => GroupsService.listInvites({ groupId }),
    enabled,
  })
}

// === Members API ===

export function useGroupMembers(groupId: string) {
  return useQuery<GroupMembersListResponse, Error>({
    queryKey: ["groups", groupId, "members"],
    queryFn: () => GroupsService.listGroupMembers({ groupId }),
    enabled: !!groupId,
  })
}
