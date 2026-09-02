export type ExpenseStatus =
  | "draft"
  | "pending_confirmation"
  | "confirmed"
  | "settled"

export interface Expense {
  id: string
  group_id: string
  /** Decimal on the wire (WS4/M1): exact string like "100.00" */
  amount: string
  description: string
  payer_id: string
  created_by: string
  status: ExpenseStatus
  confirmed_at: string | null
  created_at: string
  updated_at: string
}

export interface ExpenseCreate {
  group_id: string
  amount: number
  description: string
  payer_id?: string // Defaults to current user if not provided
  /**
   * Optional split applied atomically with creation (audit F9). Same
   * discriminated union the PUT /expenses/{id}/split endpoint accepts. Omit
   * to create a bare draft (legacy behaviour).
   */
  split?: EqualSplitRequest | UnequalSplitRequest | PercentageSplitRequest
}

export interface ExpenseUpdate {
  amount?: number
  description?: string
  payer_id?: string
}

export interface ExpensesResponse {
  data: Expense[]
  count: number
}

/**
 * One row of a group's ledger (WS5/B-H7): the expense plus the current
 * user's own split — null when they are not part of the split.
 */
export interface GroupExpenseItem {
  expense: Expense
  my_split: ExpenseSplit | null
}

export interface GroupExpensesResponse {
  data: GroupExpenseItem[]
  count: number
}

export interface ExpenseSplitsResponse {
  data: ExpenseSplit[]
  count: number
}

/**
 * AI-parsed expense from the /expenses/parse SSE endpoint (WS7).
 * The wire sends `amount` as a decimal string (WS4/M1); the parse client
 * (api/parse.ts) converts it to a number for this edit buffer.
 */
export interface ExpenseParseResponse {
  /** Parsed amount */
  amount: number
  /** Parsed description */
  description: string
  /** Payer ID (current user's UUID) */
  payer_id: string
  /** AI confidence score (0.0-1.0) */
  confidence_score: number
  /** AI personality commentary */
  commentary: string
}

/**
 * Edit state for editable expense preview
 * Tracks which fields have been modified
 */
export interface ExpenseEditState {
  /** Original AI-parsed data */
  originalData: ExpenseParseResponse
  /** Currently edited data */
  editedData: ExpenseParseResponse
  /** Set of fields that have been edited */
  editedFields: Set<keyof ExpenseParseResponse>
}

// =============================================================================
// Split Types (Story 3.5 - Equal Split)
// =============================================================================

export type SplitType = "equal" | "unequal" | "percentage" | "shares"

export interface SplitTypeOption {
  type: SplitType
  label: string
  icon: string // Lucide icon name
  disabled?: boolean
  disabledReason?: string
}

export const SPLIT_TYPE_OPTIONS: SplitTypeOption[] = [
  {
    type: "equal",
    label: "Equal",
    icon: "equal",
  },
  {
    type: "unequal",
    label: "Unequal",
    icon: "bar-chart-2",
  },
  {
    type: "percentage",
    label: "Percentage",
    icon: "percent",
  },
  {
    type: "shares",
    label: "Shares",
    icon: "squares-3-by-3",
    disabled: true,
    disabledReason: "Coming in Story 3.8",
  },
]

export interface SplitState {
  type: SplitType
  excludedMembers: Set<string>
  amounts: Map<string, number> // user_id -> amount_owed
}

export interface SplitItem {
  user_id: string
  amount_owed: number
}

export interface EqualSplitRequest {
  type: "equal"
  excluded_user_ids: string[]
}

export interface UnequalSplitItem {
  user_id: string
  amount: number
}

export interface UnequalSplitRequest {
  type: "unequal"
  splits: UnequalSplitItem[]
  excluded_user_ids: string[]
}

export interface PercentageSplitItem {
  user_id: string
  percentage: number
}

export interface PercentageSplitRequest {
  type: "percentage"
  splits: PercentageSplitItem[]
  excluded_user_ids: string[]
}

export interface ExpenseSplitResponse {
  expense_id: string
  split_type: string
  splits: SplitItem[]
  excluded_user_ids: string[]
}

// Group member type for split functionality
// NOTE: Matches backend GroupMemberPublic schema which has both fields:
// - id: GroupMember table row ID (join table primary key)
// - user_id: The actual user UUID - ALWAYS use this for user identification
export interface GroupMember {
  /** GroupMember table row ID (join table primary key) */
  id: string
  /** The actual user UUID - use this for user identification and split calculations */
  user_id: string
  full_name: string | null // Backend returns null for members without names
  email: string
  avatar_url?: string
}

// =============================================================================
// Confirmation Types (Story 4.2 - Expense Confirmation Workflow)
// =============================================================================

export type SplitStatus = "pending" | "confirmed" | "settled"

export interface ExpenseSplit {
  id: string
  expense_id: string
  user_id: string
  /** Decimal on the wire (WS4/M1): exact string like "50.00" */
  amount_owed: string
  status: SplitStatus
  confirmed_at: string | null
  created_at: string
  /** Populated by GET /expenses/{id}/splits (WS5) */
  user_name?: string | null
}

export interface ExpenseConfirmRequest {
  // No fields needed - expense_id comes from URL
}

export interface ExpenseRejectRequest {
  reason?: string // Optional reason for rejection
}

export interface ExpenseRejectResponse {
  message: string
  remaining_splits: number
}

export interface PendingConfirmation {
  expense: Expense
  split: ExpenseSplit
  /** WS10.1: the expense's group currency (/pending spans groups) */
  currency: string
}

// =============================================================================
// Audit Log Types (Story 4.4 - Immutable Audit Log)
// =============================================================================

export type AuditActionType =
  | "created"
  | "edited"
  | "confirmed"
  | "rejected"
  | "settled"
  | "split_updated"

export interface AuditLog {
  id: string
  expense_id: string
  user_id: string
  action_type: AuditActionType
  changes_json: {
    before?: Record<string, unknown>
    after?: Record<string, unknown>
  } | null
  created_at: string
  user_name: string | null
}

export interface AuditLogsResponse {
  data: AuditLog[]
  count: number
}

// =============================================================================
// Settlement Claim Types (Story 5.1 - Mark Debt as Settled)
// =============================================================================

export type SettlementClaimStatus = "pending" | "confirmed" | "rejected"

export interface SettlementClaimPublic {
  id: string
  /** null for aggregate settle-up claims (WS6) */
  expense_split_id: string | null
  claimant_user_id: string
  /** Decimal on the wire (WS4/M1): exact string like "50.00" */
  amount: string
  status: SettlementClaimStatus
  claimed_at: string
  confirmed_at: string | null
  rejected_at: string | null
  created_at: string
  user_name: string | null
  // WS6 — set on aggregate settle-up claims
  group_id: string | null
  counterparty_user_id: string | null
  counterparty_name: string | null
  covered_split_count: number
  covered_expense_count: number
  /** When this pending claim auto-confirms (end of the 72h dispute
   * window); null once processed */
  auto_confirm_at: string | null
}

export interface SettlementClaimsResponse {
  data: SettlementClaimPublic[]
  count: number
}

/** "Settle with X" (WS6): net all confirmed expenses between the caller and
 * one counterparty in a group into a single claim. */
export interface AggregateSettleUpRequest {
  group_id: string
  counterparty_user_id: string
}

export interface PendingSettlement {
  expense: Expense
  split: ExpenseSplit
  claim: SettlementClaimPublic
}
