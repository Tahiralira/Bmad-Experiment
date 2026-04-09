export type ExpenseStatus =
  | "draft"
  | "pending_confirmation"
  | "confirmed"
  | "settled"

export interface Expense {
  id: string
  group_id: string
  amount: number
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
 * AI-parsed expense response from Story 3.3's SSE endpoint
 * This is the data format returned by the AI parsing service
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
  amount_owed: number
  status: SplitStatus
  confirmed_at: string | null
  created_at: string
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
}

export interface AuditLogsResponse {
  data: AuditLog[]
  count: number
}
