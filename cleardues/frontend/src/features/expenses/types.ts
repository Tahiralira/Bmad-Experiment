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
