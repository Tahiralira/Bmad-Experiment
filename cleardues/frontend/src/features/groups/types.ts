export interface ExpenseGroup {
  id: string
  name: string
  created_by: string
  created_at: string
  updated_at: string
  member_count?: number
}

export interface ExpenseGroupCreate {
  name: string
}

export interface GroupMember {
  id: string
  group_id: string
  user_id: string
  role: "owner" | "member"
  joined_at: string
}
