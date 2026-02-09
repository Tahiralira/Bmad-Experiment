import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/shared/api"
import type { Expense, ExpenseCreate, EqualSplitRequest, UnequalSplitRequest, ExpenseSplitResponse } from "../types"

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

async function updateExpenseSplit(
  expenseId: string,
  data: EqualSplitRequest | UnequalSplitRequest
): Promise<ExpenseSplitResponse> {
  return __request(OpenAPI, {
    method: "PUT",
    url: `/api/v1/expenses/${expenseId}/split`,
    body: data,
    errors: {
      400: "Invalid split configuration or split type not implemented",
      403: "Only expense creator can modify split",
      404: "Expense not found",
    },
  })
}

export function useUpdateExpenseSplit() {
  const queryClient = useQueryClient()

  return useMutation<
    ExpenseSplitResponse,
    Error,
    { expenseId: string; data: EqualSplitRequest | UnequalSplitRequest }
  >({
    mutationFn: ({ expenseId, data }) => updateExpenseSplit(expenseId, data),
    onSuccess: () => {
      // Invalidate dashboard to refresh balances
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      // Invalidate expense queries
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      // Invalidate group balances
      queryClient.invalidateQueries({ queryKey: ["group-balances"] })
    },
    onError: (error) => {
      // Show error toast to user
      toast.error(`Failed to save split: ${error.message}`)
    },
  })
}
