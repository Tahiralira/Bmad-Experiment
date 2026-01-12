import { useMutation, useQueryClient } from "@tanstack/react-query"

import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/shared/api"
import type { Expense, ExpenseCreate } from "../types"

async function createExpense(data: ExpenseCreate): Promise<Expense> {
  return __request(OpenAPI, {
    method: "POST",
    url: "/api/v1/expenses/",
    body: data,
    errors: {
      401: "Unauthorized",
      403: "Not a member of this group",
      404: "Group not found",
    },
  })
}

export function useCreateExpense() {
  const queryClient = useQueryClient()

  return useMutation<Expense, Error, ExpenseCreate>({
    mutationFn: createExpense,
    onSuccess: () => {
      // Invalidate dashboard to refresh balances (future: when expenses affect balance)
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      // Invalidate any expense lists for this group
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
    },
  })
}
