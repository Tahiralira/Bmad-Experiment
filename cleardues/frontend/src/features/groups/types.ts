export interface ExpenseGroup {
  id: string
  name: string
  created_by: string
  created_at: string
  updated_at: string
  member_count?: number
}

/**
 * Group detail (WS5/B-H7): backing type for /groups/$groupId.
 * net_balance is the current user's balance in this group — Decimal on the
 * wire, e.g. "12.50" (positive = owed to the user).
 */
export interface ExpenseGroupDetail extends ExpenseGroup {
  member_count: number
  net_balance: string
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

// === Invite Types ===

export interface GroupInvite {
  id: string
  group_id: string
  token: string
  expires_at: string
  created_at: string
  invite_url?: string
}

export interface GroupInviteResponse {
  invite?: GroupInvite
  group?: ExpenseGroup
  message: string
}

// === Member Types ===

export interface GroupMemberPublic {
  id: string
  user_id: string
  role: "owner" | "member"
  joined_at: string
  full_name: string | null
  email: string
}

export interface GroupMembersListResponse {
  members: GroupMemberPublic[]
  count: number
}
