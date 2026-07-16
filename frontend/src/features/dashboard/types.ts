// Balances arrive as decimal STRINGS (e.g. "12.50"), not numbers: the backend
// keeps money as Decimal to the wire (WS4/M1) and Decimal serializes to a
// JSON string. Convert with Number() at the point of display/comparison.
export interface GroupBalanceSummary {
  group_id: string
  group_name: string
  net_balance: string // Positive = owed to user, negative = user owes
  last_activity: string // ISO datetime string
  member_count: number
}

export interface DashboardResponse {
  groups: GroupBalanceSummary[]
  total_balance: string
  count: number
}
