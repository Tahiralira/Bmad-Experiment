import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { request as __request } from "@/client/core/request"
import { EVENTS, track } from "@/lib/analytics"
import { DEFAULT_CURRENCY, formatCurrency } from "@/lib/currency"
import { OpenAPI } from "@/shared/api"
import type {
  AggregateSettleUpRequest,
  Expense,
  ExpenseCreate,
  ExpenseUpdate,
  EqualSplitRequest,
  UnequalSplitRequest,
  PercentageSplitRequest,
  SharesSplitRequest,
  ExpenseSplitResponse,
  ExpenseSplit,
  ExpenseSplitsResponse,
  ExpenseRejectResponse,
  GroupExpensesResponse,
  PendingConfirmation,
  AuditLogsResponse,
  SettlementClaimPublic,
  SettlementClaimsResponse,
  PendingSettlement,
} from "../types"


// =============================================================================
// WS5 (B-H7): Ledger read API
// =============================================================================

async function getGroupExpenses(
  groupId: string,
  limit = 50,
  offset = 0,
): Promise<GroupExpensesResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/${groupId}/expenses`,
    query: { limit, offset },
    errors: {
      401: "Unauthorized",
      403: "You are not a member of this group",
      404: "Group not found",
    },
  })
}

export function useGroupExpenses(groupId: string, limit = 50, offset = 0) {
  return useQuery<GroupExpensesResponse, Error>({
    // Under the ["expenses"] prefix so every existing mutation invalidation
    // (create/split/confirm/reject/settle) refreshes the ledger too
    queryKey: ["expenses", "group", groupId, limit, offset],
    queryFn: () => getGroupExpenses(groupId, limit, offset),
    enabled: !!groupId,
  })
}

async function getExpenseSplits(
  expenseId: string,
): Promise<ExpenseSplitsResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expenses/${expenseId}/splits`,
    errors: {
      401: "Unauthorized",
      403: "Not a member of this group",
      404: "Expense not found",
    },
  })
}

export function useExpenseSplits(expenseId: string, enabled = true) {
  return useQuery<ExpenseSplitsResponse, Error>({
    queryKey: ["expenses", expenseId, "splits"],
    queryFn: () => getExpenseSplits(expenseId),
    enabled: enabled && !!expenseId,
  })
}


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
      // Invalidate audit logs (edits create audit entries)
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
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
      // A create-with-split now moves an expense straight into confirmation,
      // so refresh every surface a split touches — not just the ledger.
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["pending-confirmations"] })
      queryClient.invalidateQueries({ queryKey: ["group-balances"] })
      queryClient.invalidateQueries({ queryKey: ["pairwise-balances"] })
      queryClient.invalidateQueries({ queryKey: ["groups"] })
      // Invalidate audit logs (creation + split create audit entries)
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
    },
  })
}

async function updateExpenseSplit(
  expenseId: string,
  data:
    | EqualSplitRequest
    | UnequalSplitRequest
    | PercentageSplitRequest
    | SharesSplitRequest
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
    { expenseId: string; data: EqualSplitRequest | UnequalSplitRequest | PercentageSplitRequest | SharesSplitRequest }
  >({
    mutationFn: ({ expenseId, data }) => updateExpenseSplit(expenseId, data),
    onSuccess: () => {
      // Invalidate dashboard to refresh balances
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      // Invalidate expense queries
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      // Invalidate group balances
      queryClient.invalidateQueries({ queryKey: ["group-balances"] })
      // Invalidate audit logs (split updates create audit entries)
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
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
      // WS10.6: activation funnel step 3 (first confirmed expense)
      track(EVENTS.EXPENSE_CONFIRMED)
      queryClient.invalidateQueries({ queryKey: ["pending-confirmations"] })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["group-balances"] })
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
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
      track(EVENTS.EXPENSE_REJECTED)
      queryClient.invalidateQueries({ queryKey: ["pending-confirmations"] })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
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

// =============================================================================
// Story 4.4: Audit Log API
// =============================================================================

async function getExpenseAuditLog(
  expenseId: string,
  limit = 50,
  offset = 0
): Promise<AuditLogsResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expenses/${expenseId}/audit-log`,
    query: { limit, offset },
    errors: {
      401: "Unauthorized",
      403: "Not a member of this group",
      404: "Expense not found",
    },
  })
}

export function useExpenseAuditLog(
  expenseId: string | undefined,
  limit = 50,
  offset = 0
) {
  return useQuery<AuditLogsResponse, Error>({
    queryKey: ["audit-log", expenseId, limit, offset],
    queryFn: () => getExpenseAuditLog(expenseId!, limit, offset),
    enabled: !!expenseId,
  })
}

async function getGroupAuditLog(
  groupId: string,
  limit = 50,
  offset = 0
): Promise<AuditLogsResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/${groupId}/audit-log`,
    query: { limit, offset },
    errors: {
      401: "Unauthorized",
      403: "Not a member of this group",
      404: "Group not found",
    },
  })
}

export function useGroupAuditLog(
  groupId: string | undefined,
  limit = 50,
  offset = 0
) {
  return useQuery<AuditLogsResponse, Error>({
    queryKey: ["group-audit-log", groupId, limit, offset],
    queryFn: () => getGroupAuditLog(groupId!, limit, offset),
    enabled: !!groupId,
  })
}

// =============================================================================
// Story 5.1: Settlement Claims
// =============================================================================

async function settleExpense(expenseId: string): Promise<SettlementClaimPublic> {
  return __request(OpenAPI, {
    method: "POST",
    url: `/api/v1/expenses/${expenseId}/settle`,
    errors: {
      400: "Expense must be confirmed before settling",
      403: "You are not involved in this expense",
      404: "Expense not found",
      409: "Settlement already claimed for this expense",
    },
  })
}

export function useSettleExpense() {
  const queryClient = useQueryClient()

  return useMutation<SettlementClaimPublic, Error, string>({
    mutationFn: (expenseId) => settleExpense(expenseId),
    onSuccess: () => {
      track(EVENTS.CLAIM_CREATED, { kind: "per_expense" })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["pending-settlements"] })
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
      toast.success("Settlement claim submitted")
    },
    onError: (error) => {
      toast.error(`Failed to submit settlement: ${error.message}`)
    },
  })
}

async function getPendingSettlements(): Promise<PendingSettlement[]> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/expenses/pending-settlements",
    errors: {
      401: "Unauthorized",
    },
  })
}

export function usePendingSettlements() {
  return useQuery<PendingSettlement[], Error>({
    queryKey: ["pending-settlements"],
    queryFn: getPendingSettlements,
  })
}

// =============================================================================
// Story 5.2: Owner Confirms Settlement
// =============================================================================

async function confirmSettlement(claimId: string): Promise<SettlementClaimPublic> {
  return __request(OpenAPI, {
    method: "POST",
    url: `/api/v1/expenses/settlement-claims/${claimId}/confirm`,
    errors: {
      403: "Only the expense owner can confirm settlements",
      404: "Settlement claim not found",
      409: "Settlement claim has already been processed",
    },
  })
}

export function useConfirmSettlement() {
  const queryClient = useQueryClient()

  return useMutation<SettlementClaimPublic, Error, string>({
    mutationFn: (claimId) => confirmSettlement(claimId),
    onSuccess: (claim) => {
      // WS10.6: settlement velocity — how long the claim sat open before
      // the counterparty confirmed (PRD's time-to-settle proxy).
      const ageMs = Date.now() - Date.parse(claim.created_at)
      track(EVENTS.CLAIM_CONFIRMED, {
        kind: claim.expense_split_id ? "per_expense" : "aggregate",
        claim_age_hours: Number.isFinite(ageMs)
          ? Math.round((ageMs / 36e5) * 10) / 10
          : null,
        covered_expense_count: claim.covered_expense_count,
      })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["pending-settlements"] })
      queryClient.invalidateQueries({ queryKey: ["pending-settlement-claims"] })
      queryClient.invalidateQueries({ queryKey: ["aggregate-claims"] })
      queryClient.invalidateQueries({ queryKey: ["pairwise-balances"] })
      queryClient.invalidateQueries({ queryKey: ["groups"] })
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-balances"] })
      toast.success("Settlement confirmed")
    },
    onError: (error) => {
      toast.error(`Failed to confirm settlement: ${error.message}`)
    },
  })
}

async function rejectSettlement(claimId: string): Promise<SettlementClaimPublic> {
  return __request(OpenAPI, {
    method: "POST",
    url: `/api/v1/expenses/settlement-claims/${claimId}/reject`,
    errors: {
      403: "Only the expense owner can reject settlements",
      404: "Settlement claim not found",
      409: "Settlement claim has already been processed",
    },
  })
}

export function useRejectSettlement() {
  const queryClient = useQueryClient()

  return useMutation<SettlementClaimPublic, Error, string>({
    mutationFn: (claimId) => rejectSettlement(claimId),
    onSuccess: (claim) => {
      track(EVENTS.CLAIM_REJECTED, {
        kind: claim.expense_split_id ? "per_expense" : "aggregate",
      })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["pending-settlements"] })
      queryClient.invalidateQueries({ queryKey: ["pending-settlement-claims"] })
      queryClient.invalidateQueries({ queryKey: ["aggregate-claims"] })
      queryClient.invalidateQueries({ queryKey: ["pairwise-balances"] })
      queryClient.invalidateQueries({ queryKey: ["groups"] })
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-balances"] })
      toast.success("Settlement rejected")
    },
    onError: (error) => {
      toast.error(`Failed to reject settlement: ${error.message}`)
    },
  })
}

async function getPendingSettlementClaims(
  groupId?: string,
): Promise<PendingSettlement[]> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/expenses/settlement-claims/pending-for-owner",
    query: groupId ? { group_id: groupId } : undefined,
    errors: {
      401: "Unauthorized",
    },
  })
}

/**
 * Pending claims awaiting the current user's (owner's) confirmation.
 * Pass groupId to scope to one group (WS5/S4-M6 — a group screen must not
 * show other groups' claims).
 */
export function usePendingSettlementClaims(groupId?: string) {
  return useQuery<PendingSettlement[], Error>({
    queryKey: ["pending-settlement-claims", groupId ?? "all"],
    queryFn: () => getPendingSettlementClaims(groupId),
  })
}

// =============================================================================
// WS6: Aggregate settle-up ("Settle with X")
// =============================================================================

async function getAggregateClaims(
  groupId?: string,
): Promise<SettlementClaimsResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/expenses/settlement-claims/aggregate",
    query: groupId ? { group_id: groupId } : undefined,
    errors: {
      401: "Unauthorized",
    },
  })
}

/**
 * Pending aggregate settle-up claims involving the current user — as
 * claimant (waiting on the counterparty) or counterparty (awaiting review).
 */
export function useAggregateClaims(groupId?: string) {
  return useQuery<SettlementClaimsResponse, Error>({
    queryKey: ["aggregate-claims", groupId ?? "all"],
    queryFn: () => getAggregateClaims(groupId),
  })
}

async function createAggregateSettlement(
  data: AggregateSettleUpRequest,
): Promise<SettlementClaimPublic> {
  return __request(OpenAPI, {
    method: "POST",
    url: "/api/v1/expenses/settlement-claims/aggregate",
    body: data,
    errors: {
      400: "Nothing to settle with this member",
      403: "You are not a member of this group",
      404: "Group not found",
      409: "A settlement is already in flight for these expenses",
    },
  })
}

/**
 * "Settle with X" (WS6): nets every confirmed expense between the caller
 * and the counterparty into ONE claim awaiting ONE confirmation.
 */
export function useSettleUp(currency: string = DEFAULT_CURRENCY) {
  const queryClient = useQueryClient()

  return useMutation<SettlementClaimPublic, Error, AggregateSettleUpRequest>({
    mutationFn: createAggregateSettlement,
    onSuccess: (claim) => {
      track(EVENTS.CLAIM_CREATED, {
        kind: "aggregate",
        covered_expense_count: claim.covered_expense_count,
      })
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["aggregate-claims"] })
      queryClient.invalidateQueries({ queryKey: ["pairwise-balances"] })
      queryClient.invalidateQueries({ queryKey: ["audit-log"] })
      queryClient.invalidateQueries({ queryKey: ["group-audit-log"] })
      const who = claim.counterparty_name ?? "them"
      toast.success(
        `Settle-up recorded — ${formatCurrency(claim.amount, currency)} to ${who}, awaiting their confirmation`,
      )
    },
    onError: (error) => {
      toast.error(`Couldn't settle up: ${error.message}`)
    },
  })
}
