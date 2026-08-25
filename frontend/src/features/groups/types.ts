/**
 * Groups feature types.
 *
 * WS11 — this file is now a **naming layer over the generated client**, not a
 * second source of truth. Every shape here comes from `src/client/types.gen.ts`,
 * which is generated from the backend's OpenAPI schema by
 * `npm run generate-client`. It used to hand-restate all of them, which meant a
 * backend field change compiled fine and broke at runtime.
 *
 * `groups` is WS11's exemplar for this pattern; the other features still carry
 * hand-written types and are queued to follow.
 *
 * Two rules:
 *  1. Never redeclare a shape the backend already describes. Alias it.
 *  2. If a generated type is weaker than it should be (a bare `string` where
 *     the API really returns a closed set), fix the **backend schema** and
 *     regenerate — do not "correct" it here. That is how `ai_personality`
 *     became a union rather than `string`.
 */

import type {
  ExpenseGroupCreate as GeneratedExpenseGroupCreate,
  ExpenseGroupDetail as GeneratedExpenseGroupDetail,
  ExpenseGroupWithMembers,
  GroupInvitePublic,
  GroupInvitesPublic,
  GroupMemberPublic as GeneratedGroupMemberPublic,
  GroupMembersListResponse as GeneratedGroupMembersListResponse,
  GroupInviteResponse as GeneratedGroupInviteResponse,
  GroupSettingsPublic,
  GroupSettingsUpdate as GeneratedGroupSettingsUpdate,
  InvitePreview as GeneratedInvitePreview,
  PairwiseBalanceItem as GeneratedPairwiseBalanceItem,
  PairwiseBalancesPublic,
} from "@/client"

/** A group as it appears in the user's group list. */
export type ExpenseGroup = ExpenseGroupWithMembers

/**
 * Group detail (WS5/B-H7): backing type for /groups/$groupId.
 * `net_balance` is the current user's balance in this group — Decimal on the
 * wire, e.g. "12.50" (positive = owed to the user).
 */
export type ExpenseGroupDetail = GeneratedExpenseGroupDetail

export type ExpenseGroupCreate = GeneratedExpenseGroupCreate

// === Invite Types ===

export type GroupInvite = GroupInvitePublic
export type GroupInviteResponse = GeneratedGroupInviteResponse
export type GroupInvitesResponse = GroupInvitesPublic

/** What an invited person sees BEFORE joining (WS8/S5-M4; public in WS10.3). */
export type InvitePreview = GeneratedInvitePreview

// === Pairwise Balances (WS6/S2-F9) ===

/**
 * One counterparty row of "who owes whom exactly". Decimal strings on the
 * wire; net = they_owe_you - you_owe_them (positive = they owe the user).
 */
export type PairwiseBalanceItem = GeneratedPairwiseBalanceItem
export type PairwiseBalancesResponse = PairwiseBalancesPublic

// === Group Settings (WS6 strict mode + WS7 AI personality) ===

export type GroupSettings = GroupSettingsPublic
export type GroupSettingsUpdate = GeneratedGroupSettingsUpdate

/**
 * Capped at "funny" (UX-H5) — the roast mode was removed in WS7.
 * Derived from the response schema so the backend's `Literal` stays the one
 * definition of what a personality can be.
 */
export type AIPersonality = GroupSettingsPublic["ai_personality"]

// === Member Types ===

export type GroupMemberPublic = GeneratedGroupMemberPublic
export type GroupMembersListResponse = GeneratedGroupMembersListResponse
