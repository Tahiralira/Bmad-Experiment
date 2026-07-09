# Story 5.3: Settlement Audit Trail

Status: ready-for-dev
<!-- Ultimate context engine analysis completed - comprehensive developer guide created -->

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **group member**,
I want to see a clear record of all settlements,
so that I can verify payment history and resolve disputes.

## Acceptance Criteria

1. **Given** settlements have occurred in my group, **When** I call `GET /api/v1/expense-groups/{group_id}/settlements`, **Then** I receive a paginated list of all settlement claims for that group with status (pending, confirmed, rejected)
2. **Given** I am a group member, **When** I view settlement history, **Then** each entry shows: payer name, amount, claim date, confirmation date (if confirmed), rejection date (if rejected), status, and expense description
3. **Given** settlement claims exist, **When** the group activity feed is viewed, **Then** settlement history is visible as part of the activity feed (ALREADY DONE — audit log entries from Stories 5.1/5.2 flow into the feed)
4. **Given** an expense has status SETTLED, **When** it appears in any expense list, **Then** it displays a "Settled" badge in the UI
5. **Given** I am NOT a member of the group, **When** I call the settlements endpoint, **Then** the API returns 403 Forbidden
6. **Given** the group does not exist, **When** I call the settlements endpoint, **Then** the API returns 404 Not Found
7. **Given** no settlements exist in a group, **When** I view settlement history, **Then** I see an appropriate empty state message
8. **Given** a settlement list endpoint is called, **When** results exceed page size, **Then** pagination is supported with limit/offset parameters

## Tasks / Subtasks

- [ ] Task 1: Backend — Settlement history response schema (AC: #1, #2)
  - [ ] 1.1 Add `SettlementHistoryEntry` schema to `cleardues/backend/app/features/expenses/models.py`:
    - Fields: `claim` (SettlementClaimPublic), `expense_description` (str), `expense_id` (uuid.UUID), `split_amount` (Decimal)
    - Groups all data needed for a single settlement history row
  - [ ] 1.2 Add `SettlementHistoryPublic` schema (pagination wrapper):
    - Fields: `data` (list[SettlementHistoryEntry]), `count` (int)
    - Follows existing `AuditLogsPublic` pattern from Story 4.4

- [ ] Task 2: Backend — Settlement history service function (AC: #1, #2, #5, #6, #8)
  - [ ] 2.1 Add `get_group_settlement_history(session, group_id, user_id, limit, offset)` to `cleardues/backend/app/features/expenses/service.py`:
    - Verify group exists (return None → router: 404)
    - Verify user is group member via `is_user_group_member()` (return "FORBIDDEN" → router: 403)
    - JOIN query: `select(SettlementClaim, ExpenseSplit, Expense).join(ExpenseSplit).join(Expense).where(Expense.group_id == group_id)`
    - Order by `SettlementClaim.claimed_at.desc()` (newest first)
    - Apply limit/offset pagination
    - Count query for total (same filters, no limit/offset)
    - Batch-load claimant users: collect `claimant_user_id` values, fetch Users, build lookup dict
    - Build `SettlementHistoryEntry` objects using `_build_claim_public()` + expense description + split amount
    - Return `SettlementHistoryPublic(data=[...], count=N)`
    - **FOLLOW the EXACT pattern from `get_claims_awaiting_owner_confirmation()`** — same 3-table JOIN, same batch user loading, same `_build_claim_public()` reuse

- [ ] Task 3: Backend — Settlement history endpoint (AC: #1, #5, #6, #8)
  - [ ] 3.1 Add `GET /expense-groups/{group_id}/settlements` endpoint to `cleardues/backend/app/features/groups/router.py`:
    - **NOTE: This goes in the GROUPS router**, not the expenses router (per AC endpoint path)
    - Requires `SessionDep` + `CurrentUser` dependencies
    - Query params: `limit: int = 20`, `offset: int = 0`
    - Calls `expenses_service.get_group_settlement_history(session, group_id, current_user.id, limit, offset)`
    - Handle sentinel responses: None → 404, "FORBIDDEN" → 403
    - Returns 200 OK with `SettlementHistoryPublic`
    - **FOLLOW the EXACT pattern from the existing `GET /expense-groups/{group_id}/audit-log` endpoint** in the groups router

- [ ] Task 4: Frontend — TypeScript types for settlement history (AC: #1, #2)
  - [ ] 4.1 Add `SettlementHistoryEntry` interface to `cleardues/frontend/src/features/expenses/types.ts`:
    - Fields: `claim` (SettlementClaimPublic), `expenseDescription` (string), `expenseId` (string), `splitAmount` (number)
  - [ ] 4.2 Add `SettlementHistoryResponse` interface:
    - Fields: `data` (SettlementHistoryEntry[]), `count` (number)

- [ ] Task 5: Frontend — API hook for settlement history (AC: #1, #8)
  - [ ] 5.1 Add `getGroupSettlementHistory(groupId, limit, offset)` async function to `cleardues/frontend/src/features/expenses/api/expenses.ts`:
    - `GET /api/v1/expense-groups/{groupId}/settlements?limit={limit}&offset={offset}`
    - Error map: 403, 404
  - [ ] 5.2 Add `useGroupSettlementHistory(groupId)` query hook:
    - Query key: `["settlement-history", groupId, limit, offset]`
    - Follow `useGroupAuditLog()` pattern for pagination
    - Stale time: 30s (settlement data changes infrequently)

- [ ] Task 6: Frontend — SettlementHistoryList component (AC: #1, #2, #7, #8)
  - [ ] 6.1 Create `cleardues/frontend/src/features/expenses/components/SettlementHistoryList.tsx`:
    - Fetches data with `useGroupSettlementHistory(groupId)`
    - Each row shows: payer name, amount, expense description, claim date, confirmation/rejection date (if applicable), status badge
    - Status badge colors: pending (amber), confirmed (green/success), rejected (destructive/red)
    - Pagination: "Load more" button (same pattern as ActivityFeed)
    - Empty state: "No settlements yet" with subtle messaging
    - Skeleton loading state (3 skeleton rows)
    - Error state with retry button

- [ ] Task 7: Frontend — "Settled" badge on settled expenses (AC: #4)
  - [ ] 7.1 Update expense card components to show "Settled" badge:
    - Identify where expense cards render (ConfirmedExpenseCard, expense lists)
    - Add conditional badge: if `expense.status === "settled"`, show green/amber "Settled" badge
    - Badge style: use `bg-success-subtle text-success` or amber variant from design system
    - Position: top-right of card or inline with status area

- [ ] Task 8: Frontend — Integrate settlement history into group detail view (AC: #1)
  - [ ] 8.1 Add "Settlement History" section to `cleardues/frontend/src/features/groups/components/GroupDetail.tsx`:
    - Place after SettlementClaimsList section
    - Section header with Banknote icon (consistent with settlement UI)
    - Renders `SettlementHistoryList` component

- [ ] Task 9: Frontend — Update existing settlement mutation hooks to invalidate settlement history (AC: #1)
  - [ ] 9.1 Add `["settlement-history"]` to invalidation lists in:
    - `useConfirmSettlement()` onSuccess
    - `useRejectSettlement()` onSuccess
    - `useSettleExpense()` onSuccess

- [ ] Task 10: Testing and validation
  - [ ] 10.1 Backend: Write tests for `get_group_settlement_history()` in `cleardues/backend/tests/api/routes/test_settlement.py`:
    - Successful retrieval (returns all claims for group)
    - Pagination (limit/offset works correctly)
    - Not a group member (403)
    - Group not found (404)
    - Empty group (returns empty data list, count 0)
    - Claims from multiple expenses appear in the response
    - Confirmed claims show `confirmed_at`, rejected claims show `rejected_at`
  - [ ] 10.2 Frontend: Run `cd cleardues/frontend && npm run typecheck && npm run build` — no errors
  - [ ] 10.3 Manual: Verify settlement history list shows correct data for a group with multiple settlements
  - [ ] 10.4 Manual: Verify "Settled" badge appears on settled expense cards
  - [ ] 10.5 Manual: Verify pagination "Load more" works
  - [ ] 10.6 Manual: Verify empty state when no settlements exist

## Dev Notes

### CRITICAL: What Already Exists (DO NOT REBUILD)

The following infrastructure is **DONE** from Stories 4.4, 5.1, and 5.2. Story 5.3 is primarily a **read-only listing view** — NO new mutation logic needed.

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| SettlementClaim table model | `models.py:332-362` | Done | All fields: `claimed_at`, `confirmed_at`, `rejected_at`, `status` |
| SettlementClaimStatus enum | `models.py:31-36` | Done | `PENDING`, `CONFIRMED`, `REJECTED` |
| SettlementClaimPublic schema | `models.py:181-194` | Done | All fields including `confirmed_at`, `rejected_at`, `user_name` |
| `_build_claim_public()` helper | `service.py:821-843` | Done | Enriches claim with `user_name` via batch query |
| `confirm_settlement_claim()` | `service.py` | Done | Creates CONFIRMED claims + audit entries |
| `reject_settlement_claim()` | `service.py` | Done | Creates REJECTED claims + audit entries |
| `settle_expense_split()` | `service.py` | Done | Creates PENDING claims + audit entries |
| `get_claims_awaiting_owner_confirmation()` | `service.py` | Done | **CLOSEST PATTERN** — 3-table JOIN (Claim→Split→Expense) with batch user loading. REUSE THIS PATTERN for group settlements |
| `get_pending_settlements_for_user()` | `service.py` | Done | Claimant's pending claims |
| AuditLog model + `record_audit()` | `models.py`, `service.py` | Done | Immutable audit for all settlement actions |
| `get_group_audit_logs()` | `service.py` | Done | Group-level paginated audit retrieval |
| Group audit log endpoint | `router.py` (groups) | Done | `GET /expense-groups/{group_id}/audit-log` — **EXACT ROUTING PATTERN** for Story 5.3 |
| Activity feed formatters | `activityFormatters.ts` | Done | `formatSettledEntry()` + `formatRejectedEntry()` already handle settlements |
| ActivityFeed component | `ActivityFeed.tsx` | Done | Shows settlement audit entries in group view — AC#3 is ALREADY MET |
| `useGroupAuditLog()` hook | `expenses.ts` | Done | Fetches group audit log — settlement entries already appear |
| Frontend `SettlementClaimPublic` type | `types.ts:233-253` | Done | Full interface with all fields |
| `_handle_settlement_result()` helper | `router.py` | Done | Sentinel→HTTPException translation |
| ExpenseStatus.SETTLED | `models.py:14-20` | Done | Expense status enum value exists |
| `check_all_splits_settled()` | `service.py` | Done | Auto-transitions expense to SETTLED |
| Groups router | `router.py` (groups) | Done | Place new endpoint here — `/expense-groups/{group_id}/settlements` |

### AC#3 is ALREADY DONE

The activity feed already shows settlement history. Stories 5.1 and 5.2 create audit log entries for every settlement action (claim, confirm, reject). These flow into `ActivityFeed` via `useGroupAuditLog()`. **No additional work needed for AC#3.**

### Settlement Lifecycle State Machine (Context)

```
Split exists (confirmed) → Claimant marks "Mark Paid" → SettlementClaim(PENDING)
  → Owner confirms → SettlementClaim(CONFIRMED) + Split(SETTLED) + AuditLog(SETTLED)
  → Owner rejects → SettlementClaim(DELETED) + AuditLog(REJECTED) preserves history
  → ALL splits SETTLED → Expense(SETTLED)
```

### Data Flow: Group Settlement History (NEW for 5.3)

```
1. User opens group detail → navigates to Settlement History tab/section
2. Frontend: GET /api/v1/expense-groups/{group_id}/settlements?limit=20&offset=0
3. Backend:
   a. Verify group exists (404)
   b. Verify user is group member (403)
   c. JOIN query: SettlementClaim + ExpenseSplit + Expense
   d. Filter: Expense.group_id == group_id
   e. Batch-load claimant users (avoid N+1)
   f. Return paginated: { data: [...], count: N }
4. Frontend: render SettlementHistoryList with status badges, dates, amounts
5. If no settlements → show empty state
6. Pagination: "Load more" button pattern (same as ActivityFeed)
```

### Architecture Compliance Guardrails

- **API naming**: `snake_case` on the wire. New endpoint: `GET /expense-groups/{group_id}/settlements`
- **Router placement**: This endpoint goes in the **groups router** (`backend/app/features/groups/router.py`), NOT the expenses router. The AC specifies `/expense-groups/{group_id}/settlements` which falls under the groups prefix.
- **Service placement**: The service function `get_group_settlement_history()` goes in `expenses/service.py` since it queries expense/settlement tables. The groups router calls into the expenses service (cross-feature service call — already established pattern from `is_user_group_member()`).
- **Sentinel pattern**: Service returns `None` for group not found, `"FORBIDDEN"` for non-member. Router translates to HTTPException.
- **Feature boundaries**: All settlement code stays in `backend/app/features/expenses/` (service, models). Only the routing endpoint is in groups router.
- **State management**: TanStack Query for server state. Do NOT store settlement history in Redux.
- **TypeScript naming**: `camelCase` for variables/functions, `PascalCase` for components/types.
- **Query key**: `["settlement-history", groupId, limit, offset]` — include pagination params for proper cache separation.
- **Query invalidation**: After existing settlement mutations (confirm, reject, settle), add `["settlement-history"]` to their invalidation lists so the history view refreshes.
- **Pagination format**: `{ data: [...], count: N }` — matches `AuditLogsPublic` pattern from Story 4.4.
- **Use `datetime.now(timezone.utc)`** — NOT deprecated `datetime.utcnow()`
- **Use `session.exec(select(...))`** — NOT deprecated `session.query()`
- **JOIN queries for list endpoints** — Avoid N+1 per-item queries. Batch-load users.

### Error Response Patterns (Follow Existing)

| Scenario | Status | Error Message |
|----------|--------|---------------|
| Not authenticated | 401 | "Unauthorized" (handled by `get_current_user_id`) |
| Not a group member | 403 | "You are not a member of this group" |
| Group not found | 404 | "Group not found" |

### Backend Service Function Pattern

**Group settlement history (follows `get_claims_awaiting_owner_confirmation()` pattern):**
```python
def get_group_settlement_history(
    session: Session, group_id: uuid.UUID, current_user_id: uuid.UUID,
    limit: int = 20, offset: int = 0
) -> SettlementHistoryPublic | str | None:
    """
    Get all settlement claims for a group (paginated).

    Validates: group exists, user is member.
    Returns: paginated list of settlement history entries with enriched data.
    """
    # 1. Verify group exists (None → router: 404)
    # 2. Verify membership via is_user_group_member() ("FORBIDDEN" → router: 403)
    # 3. Count query: select(func.count()).select_from(SettlementClaim).join(Split).join(Expense).where(group_id)
    # 4. Data query: select(SettlementClaim, ExpenseSplit, Expense).join(...).where(group_id).order_by(claimed_at.desc()).limit().offset()
    # 5. Batch-load claimant users (collect IDs → fetch Users → build dict)
    # 6. Build SettlementHistoryEntry list using _build_claim_public() + expense.description + split.amount
    # 7. Return SettlementHistoryPublic(data=[...], count=N)
```

**NOTE on rejected claims:** When an owner rejects a claim, Story 5.2 DELETES the claim record (to allow re-claim). Only PENDING and CONFIRMED claims exist in the `settlement_claim` table. Rejection history is preserved in the **audit log** only. The settlement history endpoint will show PENDING and CONFIRMED claims — this is correct behavior. The activity feed (AC#3, already done) shows rejection history via audit log.

### Frontend Hook Pattern

**Settlement history hook (follows `useGroupAuditLog()` pattern):**
```typescript
async function getGroupSettlementHistory(
  groupId: string, limit: number = 20, offset: number = 0
): Promise<SettlementHistoryResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/expense-groups/{groupId}/settlements",
    path: { groupId },
    query: { limit, offset },
    errors: { 403: "Not a group member", 404: "Group not found" },
  })
}

export function useGroupSettlementHistory(groupId: string, limit = 20, offset = 0) {
  return useQuery<SettlementHistoryResponse, Error>({
    queryKey: ["settlement-history", groupId, limit, offset],
    queryFn: () => getGroupSettlementHistory(groupId, limit, offset),
    staleTime: 30_000, // settlement data changes infrequently
  })
}
```

### "Settled" Badge Implementation

On expense cards where `expense.status === "settled"`:
- Use a small badge/tag component
- Style: `bg-success-subtle text-success border-success` (amber/green from design system)
- Text: "Settled"
- Position: top-right corner of card or inline next to status indicator
- Check these components for badge placement:
  - `ConfirmedExpenseCard.tsx` — most likely candidate, shows expenses in confirmed state
  - Any expense list/grid component that displays expenses with status

### Previous Story Intelligence (Story 5.2 — Code Review)

These learnings from Story 5.2 code review are CRITICAL for this story:

1. **Payer split auto-settle** — `confirm_settlement_claim()` auto-settles the payer's own split when confirming. The `check_all_splits_settled()` function accounts for this. Story 5.3 queries should see all splits as SETTLED for fully-settled expenses.
2. **Batch-fetch related entities** — Use `User.id.in_(user_ids)` with a dict lookup instead of N+1 per-row user loading. Follow the pattern in `get_claims_awaiting_owner_confirmation()`.
3. **Extract shared helpers** — `_handle_settlement_result()` deduplicates sentinel→HTTPException translation. Use it in the new endpoint.
4. **Don't use `useCallback` with `useMutation()`** — Mutation object changes every render, making `useCallback` useless. Keep hooks simple.
5. **`_build_claim_public()` is the standard** — Always use it for enriching claim data with `user_name`.

### Previous Story Intelligence (Story 4.4 — Audit Log)

- `changes_json` format: `{"before": {...}, "after": {...}}`
- Audit log is non-blocking — errors logged but never fail parent operation
- `record_audit()` does NOT commit — parent handles commit for atomicity
- Group audit log endpoint pattern is the EXACT template for Story 5.3 endpoint

### Git Intelligence Summary

Recent commits show consistent patterns:
- Stories 5.1 and 5.2 established the full settlement lifecycle (claim → confirm/reject)
- Activity feed already renders settlement audit entries (Story 4.5 + 5.2 updates)
- Code review fixes focus on: N+1 queries, unused callbacks, shared helper extraction
- Testing: `test_settlement.py` has 20 tests across Stories 5.1/5.2 — add Story 5.3 tests to same file

### Project Context Reference

- **Architecture**: [architecture.md](_bmad-output/planning-artifacts/architecture.md)
- **PRD**: FR13 (Mark debts as settled), FR15 (immutable audit log), FR19 (Settlement Cycle)
- **UX Design**: [ux-design-specification.md](_bmad-output/planning-artifacts/ux-design-specification.md)
- **Previous Story 5.2**: [5-2-owner-confirms-settlement.md](_bmad-output/implementation-artifacts/5-2-owner-confirms-settlement.md)
- **Previous Story 5.1**: [5-1-mark-debt-as-settled-claim-payment.md](_bmad-output/implementation-artifacts/5-1-mark-debt-as-settled-claim-payment.md)
- **Previous Story 4.4**: [4-4-immutable-audit-log-for-all-actions.md](_bmad-output/implementation-artifacts/4-4-immutable-audit-log-for-all-actions.md)
- **Solution Patterns**: [solution-patterns.yaml](_bmad-output/implementation-artifacts/solution-patterns.yaml)

### Security Considerations

- [x] Input Validation — `group_id` validated as UUID by FastAPI path parameter; `limit`/`offset` validated as int with defaults
- [x] Authorization — User must be group member (verified via `is_user_group_member()`); returns 403 if not member
- [x] SQL Injection — SQLModel/SQLAlchemy prevents injection automatically
- [x] Data Privacy — Settlement history only visible to group members
- [x] Error Message Security — Generic 404/403 errors, no internal details exposed
- [ ] Rate Limiting — Consider limiting settlement history requests per minute (not critical for read-only endpoint)

### Project Structure Notes

**No new backend service files needed** — all code added to existing files:

**New frontend files:**
- `cleardues/frontend/src/features/expenses/components/SettlementHistoryList.tsx`

**Files to modify:**
- `cleardues/backend/app/features/expenses/models.py` — Add `SettlementHistoryEntry` + `SettlementHistoryPublic` schemas
- `cleardues/backend/app/features/expenses/service.py` — Add `get_group_settlement_history()`
- `cleardues/backend/app/features/groups/router.py` — Add `GET /expense-groups/{group_id}/settlements` endpoint
- `cleardues/frontend/src/features/expenses/types.ts` — Add `SettlementHistoryEntry` + `SettlementHistoryResponse` types
- `cleardues/frontend/src/features/expenses/api/expenses.ts` — Add `useGroupSettlementHistory()` hook
- `cleardues/frontend/src/features/expenses/components/index.ts` — Export `SettlementHistoryList`
- `cleardues/frontend/src/features/expenses/components/ConfirmedExpenseCard.tsx` (or similar) — Add "Settled" badge
- `cleardues/frontend/src/features/groups/components/GroupDetail.tsx` — Add Settlement History section
- `cleardues/frontend/src/features/expenses/api/expenses.ts` — Add `["settlement-history"]` to existing mutation invalidation lists
- `cleardues/backend/tests/api/routes/test_settlement.py` — Add Story 5.3 tests

**No Alembic migration needed** — All required tables and columns exist from Stories 5.1/5.2.

### References

- [Epic 5 Story 5.3 definition](_bmad-output/planning-artifacts/epics.md#L843)
- [FR13: Mark debts as settled](_bmad-output/planning-artifacts/prd.md)
- [FR15: Immutable audit log](_bmad-output/planning-artifacts/prd.md)
- [Architecture: API patterns](_bmad-output/planning-artifacts/architecture.md)
- [UX: Settlement Flow](_bmad-output/planning-artifacts/ux-design-specification.md)
- [Previous Story 5.2](_bmad-output/implementation-artifacts/5-2-owner-confirms-settlement.md)
- [Previous Story 5.1](_bmad-output/implementation-artifacts/5-1-mark-debt-as-settled-claim-payment.md)
- [Previous Story 4.4](_bmad-output/implementation-artifacts/4-4-immutable-audit-log-for-all-actions.md)
- [SettlementClaim model](cleardues/backend/app/features/expenses/models.py)
- [Expense service — JOIN query pattern](cleardues/backend/app/features/expenses/service.py)
- [Groups router — audit-log endpoint pattern](cleardues/backend/app/features/groups/router.py)
- [Frontend types](cleardues/frontend/src/features/expenses/types.ts)
- [Frontend API hooks](cleardues/frontend/src/features/expenses/api/expenses.ts)
- [Activity formatters](cleardues/frontend/src/features/expenses/utils/activityFormatters.ts)
- [Solution patterns](_bmad-output/implementation-artifacts/solution-patterns.yaml)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
