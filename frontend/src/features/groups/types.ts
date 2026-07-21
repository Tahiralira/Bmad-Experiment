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
  /** WS10.1: the group's ISO-4217 currency; the whole ledger renders in it */
  currency: string
}

export interface ExpenseGroupCreate {
  name: string
  /** WS10.1: locale-detected ISO-4217 currency for the new group (optional) */
  currency?: string
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
  max_uses: number
  use_count: number
  revoked_at?: string | null
  invite_url?: string
}

export interface GroupInviteResponse {
  invite?: GroupInvite
  group?: ExpenseGroup
  message: string
}

export interface GroupInvitesResponse {
  data: GroupInvite[]
  count: number
}

/** What an invited person sees BEFORE joining (WS8/S5-M4; public in WS10.3). */
export interface InvitePreview {
  group_id: string
  group_name: string
  member_count: number
  expires_at: string
  already_member: boolean
  /** WS10.3: "<inviter> invited you to <group>" on the public landing. */
  inviter_name: string | null
}

// === Pairwise Balances (WS6/S2-F9) ===

/**
 * One counterparty row of "who owes whom exactly". Decimal strings on the
 * wire; net = they_owe_you - you_owe_them (positive = they owe the user).
 */
export interface PairwiseBalanceItem {
  user_id: string
  user_name: string | null
  they_owe_you: string
  you_owe_them: string
  net: string
}

export interface PairwiseBalancesResponse {
  data: PairwiseBalanceItem[]
  count: number
}

// === Group Settings (WS6 strict mode + WS7 AI personality) ===

/** Capped at "funny" (UX-H5) — the roast mode was removed in WS7 */
export type AIPersonality = "professional" | "friendly" | "funny"

export interface GroupSettings {
  group_id: string
  strict_mode: boolean
  ai_personality: AIPersonality
  /** WS10.1: the group's ISO-4217 currency */
  currency: string
}

/** PATCH body — send only the fields that change */
export interface GroupSettingsUpdate {
  strict_mode?: boolean
  ai_personality?: AIPersonality
  currency?: string
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
