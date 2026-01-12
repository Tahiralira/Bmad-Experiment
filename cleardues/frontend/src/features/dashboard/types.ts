export interface GroupBalanceSummary {
  group_id: string
  group_name: string
  net_balance: number // Positive = owed to user, negative = user owes
  last_activity: string // ISO datetime string
  member_count: number
}

export interface DashboardResponse {
  groups: GroupBalanceSummary[]
  total_balance: number
  count: number
}
