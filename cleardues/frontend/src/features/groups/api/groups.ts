import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { request as __request } from "@/client/core/request"
import { GroupsService, OpenAPI } from "@/shared/api"
import type {
  ExpenseGroup,
  ExpenseGroupCreate,
  GroupInviteResponse,
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
