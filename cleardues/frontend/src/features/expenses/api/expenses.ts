import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/shared/api"
import type {
  Expense,
  ExpenseCreate,
  ExpenseUpdate,
  EqualSplitRequest,
  UnequalSplitRequest,
  PercentageSplitRequest,
  ExpenseSplitResponse,
  ExpenseSplit,
  ExpenseRejectResponse,
  PendingConfirmation,
} from "../types"


// =============================================================================
// Story 4.1: Update Expense API
// =============================================================================

async function updateExpense(
  expenseId: string,
  data: ExpenseUpdate
): Promise<Expense> {
  return __request(OpenAPI, {
    method: "PATCH",
    url: `/api/v1/expenses/${expenseId}`,
    body: data,
    errors: {
      401: "Unauthorized",
      403: "Only the expense creator can edit this expense",
      404: "Expense not found",
    },
  })
}

export function useUpdateExpense() {
  const queryClient = useQueryClient()

  return useMutation<Expense, Error, { expenseId: string; data: ExpenseUpdate }>({
    mutationFn: ({ expenseId, data }) => updateExpense(expenseId, data),
    onSuccess: (_, variables) => {
      // Invalidate the specific expense query
      queryClient.invalidateQueries({ queryKey: ["expenses", variables.expenseId] })
      // Invalidate expense lists
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      // Invalidate dashboard (balances might change)
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
    onError: (error) => {
      toast.error(`Failed to update expense: ${error.message}`)
    },
  })
}

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
  data: EqualSplitRequest | UnequalSplitRequest | PercentageSplitRequest
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
    { expenseId: string; data: EqualSplitRequest | UnequalSplitRequest | PercentageSplitRequest }
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

// =============================================================================
// Story 4.2: Expense Confirmation Workflow
// =============================================================================

async function confirmExpense(expenseId: string): Promise<ExpenseSplit> {
  return __request(OpenAPI, {
    method: "POST",
    url: `/api/v1/expenses/${expenseId}/confirm`,
    errors: {
      401: "Unauthorized",
      403: "Cannot confirm this expense",
      404: "Expense not found",
    },
  })
}

export function useConfirmExpense() {
  const queryClient = useQueryClient()

  return useMutation<ExpenseSplit, Error, string>({
    mutationFn: (expenseId) => confirmExpense(expenseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-confirmations"] })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      toast.success("Expense confirmed")
    },
    onError: (error) => {
      toast.error(`Failed to confirm expense: ${error.message}`)
    },
  })
}

async function rejectExpense(
  expenseId: string,
  reason?: string
): Promise<ExpenseRejectResponse> {
  return __request(OpenAPI, {
    method: "POST",
    url: `/api/v1/expenses/${expenseId}/reject`,
    body: { reason },
    errors: {
      401: "Unauthorized",
      403: "Cannot reject this expense",
      404: "Expense not found",
    },
  })
}

export function useRejectExpense() {
  const queryClient = useQueryClient()

  return useMutation<ExpenseRejectResponse, Error, { expenseId: string; reason?: string }>({
    mutationFn: ({ expenseId, reason }) => rejectExpense(expenseId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-confirmations"] })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      toast.success("Expense rejected")
    },
    onError: (error) => {
      toast.error(`Failed to reject expense: ${error.message}`)
    },
  })
}

async function getPendingConfirmations(): Promise<PendingConfirmation[]> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/expenses/pending-confirmations",
    errors: {
      401: "Unauthorized",
    },
  })
}

export function usePendingConfirmations() {
  return useQuery<PendingConfirmation[], Error>({
    queryKey: ["pending-confirmations"],
    queryFn: getPendingConfirmations,
  })
}
