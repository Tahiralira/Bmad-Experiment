import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { GroupsService } from "@/shared/api"
import type { ExpenseGroup, ExpenseGroupCreate } from "../types"

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
