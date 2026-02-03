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
  created_at: string
  updated_at: string
}

export interface ExpenseCreate {
  group_id: string
  amount: number
  description: string
  payer_id?: string // Defaults to current user if not provided
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
