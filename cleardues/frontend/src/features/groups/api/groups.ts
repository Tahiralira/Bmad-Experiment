import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { request as __request } from "@/client/core/request"
import { GroupsService, OpenAPI } from "@/shared/api"
import type {
  ExpenseGroup,
  ExpenseGroupCreate,
  ExpenseGroupDetail,
  GroupInviteResponse,
  GroupMembersListResponse,
  GroupSettings,
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

async function getGroupDetail(groupId: string): Promise<ExpenseGroupDetail> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/${groupId}`,
    errors: {
      401: "Unauthorized",
      403: "You are not a member of this group",
      404: "Group not found",
    },
  })
}

export function useGroupDetail(groupId: string) {
  return useQuery<ExpenseGroupDetail, Error>({
    queryKey: ["groups", groupId, "detail"],
    queryFn: () => getGroupDetail(groupId),
    enabled: !!groupId,
  })
}

// === Pairwise Balances (WS6/S2-F9) ===

async function getPairwiseBalances(
  groupId: string,
): Promise<PairwiseBalancesResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/${groupId}/pairwise-balances`,
    errors: {
      401: "Unauthorized",
      403: "You are not a member of this group",
      404: "Group not found",
    },
  })
}

export function usePairwiseBalances(groupId: string) {
  return useQuery<PairwiseBalancesResponse, Error>({
    queryKey: ["pairwise-balances", groupId],
    queryFn: () => getPairwiseBalances(groupId),
    enabled: !!groupId,
  })
}

// === Group Settings (WS6 — strict mode) ===

async function getGroupSettings(groupId: string): Promise<GroupSettings> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/${groupId}/settings`,
    errors: {
      401: "Unauthorized",
      403: "You are not a member of this group",
      404: "Group not found",
    },
  })
}

export function useGroupSettings(groupId: string) {
  return useQuery<GroupSettings, Error>({
    queryKey: ["groups", groupId, "settings"],
    queryFn: () => getGroupSettings(groupId),
    enabled: !!groupId,
  })
}

async function updateGroupSettings(
  groupId: string,
  data: { strict_mode: boolean },
): Promise<GroupSettings> {
  return __request(OpenAPI, {
    method: "PATCH",
    url: `/api/v1/expense-groups/${groupId}/settings`,
    body: data,
    errors: {
      401: "Unauthorized",
      403: "Only the group owner can change group settings",
      404: "Group not found",
    },
  })
}

export function useUpdateGroupSettings(groupId: string) {
  const queryClient = useQueryClient()

  return useMutation<GroupSettings, Error, { strict_mode: boolean }>({
    mutationFn: (data) => updateGroupSettings(groupId, data),
    onSuccess: (settings) => {
      queryClient.setQueryData(["groups", groupId, "settings"], settings)
      toast.success(
        settings.strict_mode
          ? "Strict mode on — every share needs an explicit confirmation"
          : "Strict mode off — expenses confirm quietly unless someone objects",
      )
    },
    onError: (error) => {
      toast.error(`Couldn't update settings: ${error.message}`)
    },
  })
}

// === Invite API ===

async function createInvite(groupId: string): Promise<GroupInviteResponse> {
  return __request(OpenAPI, {
    method: "POST",
    url: `/api/v1/expense-groups/${groupId}/invites`,
    errors: {
      401: "Unauthorized",
      403: "Only the group owner can generate invite links",
      404: "Group not found",
    },
  })
}

async function acceptInvite(token: string): Promise<GroupInviteResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/invite/${token}`,
    errors: {
      401: "Unauthorized",
      404: "Invalid invite link",
      410: "This invite link has expired",
    },
  })
}

export function useCreateInvite() {
  return useMutation({
    mutationFn: createInvite,
  })
}

export function useAcceptInvite() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: acceptInvite,
    onSuccess: () => {
      // Invalidate groups list to show new membership
      queryClient.invalidateQueries({ queryKey: ["groups"] })
    },
  })
}

// === Members API ===

async function getGroupMembers(
  groupId: string,
): Promise<GroupMembersListResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/${groupId}/members`,
    errors: {
      401: "Unauthorized",
      403: "You are not a member of this group",
      404: "Group not found",
    },
  })
}

export function useGroupMembers(groupId: string) {
  return useQuery<GroupMembersListResponse, Error>({
    queryKey: ["groups", groupId, "members"],
    queryFn: () => getGroupMembers(groupId),
    enabled: !!groupId,
  })
}
