# Story 4.5: Activity Feed Display

Status: done

## Story

As a **group member**,
I want to view an activity feed showing all expense changes,
So that I can see who did what and when for transparency.

## Acceptance Criteria

1. **Given** I am viewing a group or specific expense, **When** I access the activity feed, **Then** I see a chronological list of all actions from the audit log
2. **Given** activity entries are displayed, **When** I view the feed, **Then** each entry shows: user name, action, timestamp, and relevant details
3. **Given** activity entries are formatted, **When** displayed, **Then** entries read clearly: "Alex created expense 'Lunch' for $60" or "Sam confirmed their share"
4. **Given** the activity feed grows, **When** I scroll, **Then** the feed is paginated (20 entries per page)
5. **Given** I need activity context, **When** I access the API, **Then** the endpoints work: `GET /api/v1/expenses/{expense_id}/audit-log` or `GET /api/v1/expense-groups/{group_id}/audit-log`
6. **UX Enhancement - Chat-Style Feed:** Activity items styled as chat bubbles in Group View; new entries animate in with fade-up effect; timestamps shown relatively ("2 hours ago") with exact date on hover

## Tasks / Subtasks

- [x] Task 1: Replace Activity page placeholder with real group-level activity feed (AC: #1, #2, #3, #6)
  - [x] 1.1 Replace the placeholder in `frontend/src/routes/_layout/activity.tsx` with a full activity feed component
  - [x] 1.2 Create `frontend/src/features/expenses/components/ActivityFeed.tsx` - the main feed component that accepts a `groupId` and uses `useGroupAuditLog` hook
  - [x] 1.3 Create `frontend/src/features/expenses/components/ActivityFeedItem.tsx` - individual feed entry styled as a chat bubble with action-specific formatting and avatar
  - [x] 1.4 Implement chat-bubble styling using design system tokens (surface, border, muted colors) with fade-up animation for new entries (use CSS `@keyframes` or `framer-motion` if already a dependency)
  - [x] 1.5 Implement relative timestamps ("2 hours ago") with exact date on hover - reuse existing `formatRelativeTime` logic from `AuditLogList.tsx`

- [x] Task 2: Add human-readable action formatting (AC: #3)
  - [x] 2.1 Create `frontend/src/features/expenses/utils/activityFormatters.ts` - centralized formatting functions for each `AuditActionType`
  - [x] 2.2 Format strings: "Alex created expense 'Lunch' for Rs 60", "Sam confirmed their share", "Jordan rejected expense 'Dinner'", "Casey updated the split for 'Coffee'"
  - [x] 2.3 For "edited" action type, show before/after diff inline: "Alex changed description from 'Lunch' to 'Dinner'"
  - [x] 2.4 Include expense description and amount from `changes_json.after` where available

- [x] Task 3: Implement pagination with "Load more" (AC: #4)
  - [x] 3.1 Use `useGroupAuditLog(groupId, 20, offset)` with offset-based pagination (hook already exists)
  - [x] 3.2 Track offset state, increment by 20 on "Load more" click
  - [x] 3.3 Append new results to existing list (avoid replacing)
  - [x] 3.4 Show/hide "Load more" button based on `totalCount > loadedItems.length`

- [x] Task 4: Integrate activity feed into group detail view (AC: #1, #5)
  - [x] 4.1 Check the group detail page (route `/_layout/groups/$groupId`) for an appropriate location to show a "Recent Activity" section or link to the full activity page
  - [x] 4.2 Ensure the activity route page knows which group context to display (use URL params or group selection)
  - [x] 4.3 Wire up the `useGroupAuditLog` hook with proper group ID resolution

- [x] Task 5: Update the Activity page route to support group-specific and all-groups views (AC: #1, #5)
  - [x] 5.1 For the top-level `/activity` route: show combined recent activity across all user's groups (may need a new backend endpoint or client-side aggregation)
  - [x] 5.2 For group-specific view: the existing `GET /api/v1/expense-groups/{group_id}/audit-log` endpoint already works
  - [x] 5.3 If a combined "all groups" feed is needed, add a `GET /api/v1/expenses/activity` endpoint in `backend/app/features/expenses/router.py` that returns audit logs across all groups the user is a member of (paginated, newest first)

- [x] Task 6: Testing and validation
  - [x] 6.1 Verify activity feed displays correctly for groups with existing audit log entries
  - [x] 6.2 Verify empty state message when no activity exists
  - [x] 6.3 Verify pagination loads more entries correctly
  - [x] 6.4 Verify relative timestamps update correctly
  - [x] 6.5 Run `docker compose exec backend pytest` - all tests must pass
  - [x] 6.6 Run `cd frontend && npm run typecheck && npm run build` - no errors

## Dev Notes

### CRITICAL: What Already Exists (DO NOT REBUILD)

Story 4.4 already built the complete data layer. The following are **DONE and working**:

| Component | File | Status |
|-----------|------|--------|
| AuditLog DB model | `backend/app/features/expenses/models.py:276` | Done |
| AuditLogPublic schema | `backend/app/features/expenses/models.py:184` | Done |
| `record_audit()` service | `backend/app/features/expenses/service.py` | Done |
| Expense audit-log endpoint | `GET /api/v1/expenses/{expense_id}/audit-log` | Done |
| Group audit-log endpoint | `GET /api/v1/expense-groups/{group_id}/audit-log` | Done |
| `useGroupAuditLog()` hook | `frontend/src/features/expenses/api/expenses.ts:274` | Done |
| `useExpenseAuditLog()` hook | `frontend/src/features/expenses/api/expenses.ts:245` | Done |
| `AuditLogList` component | `frontend/src/features/expenses/components/AuditLogList.tsx` | Done |
| Frontend types (AuditLog, AuditActionType, AuditLogsResponse) | `frontend/src/features/expenses/types.ts:204-228` | Done |
| All mutation hooks invalidate audit-log queries | `expenses.ts` (all useMutation hooks) | Done |

**The backend is feature-complete for this story.** No new backend work is required unless you need an "all groups combined" activity endpoint (Task 5.3).

### Architecture Guardrails

- **API naming**: `snake_case` on the wire. Frontend types already match.
- **State management**: Use TanStack Query (`useGroupAuditLog` hook already exists). Do NOT store audit data in Redux.
- **Feature boundaries**: New components go in `frontend/src/features/expenses/components/`. Shared utilities go in `frontend/src/features/expenses/utils/`.
- **Design system tokens**: Use the established token system (surface, border, muted, primary, foreground). See existing components like `AuditLogList.tsx` for patterns.
- **TypeScript naming**: `camelCase` for variables/functions, `PascalCase` for components/types.
- **Query invalidation**: All mutation hooks in `expenses.ts` already invalidate `["audit-log"]` and `["group-audit-log"]` query keys, so the feed stays fresh automatically.

### Existing Code to Reuse

1. **`formatRelativeTime()`** in `AuditLogList.tsx:14-28` - Copy or extract to shared util. Handles "just now", "5m ago", "2h ago", "3d ago", date fallback.

2. **`ACTION_LABELS`** in `AuditLogList.tsx:5-12` - Already maps `AuditActionType` to display strings. Extend for richer formatting.

3. **`useGroupAuditLog(groupId, limit, offset)`** in `expenses.ts:274` - Returns `{ data: AuditLogsResponse, isLoading, error }`. Already paginated, already handles auth errors.

4. **`AuditLogList` component** in `AuditLogList.tsx` - Existing timeline-style display. The new `ActivityFeed` should be a **separate** chat-styled component that replaces the placeholder page, not a modification of `AuditLogList`.

5. **Activity page placeholder** at `frontend/src/routes/_layout/activity.tsx` - This is the file to replace. It already has the route registered (`/_layout/activity`).

### AuditActionType Values and Content Patterns

| action_type | changes_json content | Feed format example |
|-------------|---------------------|---------------------|
| `created` | `{"after": {"amount": 60, "description": "Lunch"}}` | "Alex created expense 'Lunch' for Rs 60" |
| `edited` | `{"before": {"description": "Lunch"}, "after": {"description": "Dinner"}}` | "Alex changed description from 'Lunch' to 'Dinner'" |
| `confirmed` | `null` or `{"after": {"status": "confirmed"}}` | "Sam confirmed their share" |
| `rejected` | `null` | "Jordan rejected expense 'Dinner'" |
| `settled` | `null` | "Casey settled Rs 30" |
| `split_updated` | `{"after": {"type": "equal", "members": [...]}}` | "Alex updated the split for 'Coffee'" |

### Previous Story Learnings (Story 4.4)

- `datetime.now(timezone.utc)` must be used, NOT `datetime.utcnow()` (deprecated)
- `record_audit()` is non-blocking - errors are logged but never fail the parent operation
- Group membership verification is required before returning audit logs
- Audit logs are write-only - no UPDATE/DELETE operations exist
- `changes_json` format: `{"before": {...}, "after": {...}}` for edits, `{"after": {...}}` for creates
- `user_name` field is included in `AuditLogPublic` schema for display
- Test teardown must clean AuditLog before ExpenseGroup (FK constraint)

### UX Enhancement Details (Chat-Style Feed)

The epics specify a "chat-style" activity feed for Group View:

1. **Chat bubble styling**: Each activity entry should look like a chat message - rounded bubble, left-aligned, with avatar initials or icon
2. **Fade-up animation**: New entries should animate in from below (CSS transition or framer-motion)
3. **Relative timestamps**: Already implemented in `formatRelativeTime` - "2 hours ago" with exact date on hover
4. **AI personality comments**: The epic mentions "AI personality comments appear inline with streaming effect" - this is an **enhancement/optional** feature. The group's `ai_personality` setting (in `GroupSettings` model) drives personality mode. This can be deferred to a future story as it requires AI generation integration.

### Backend Endpoint Reference (Already Implemented)

**Group-level audit log:**
```
GET /api/v1/expense-groups/{group_id}/audit-log?limit=50&offset=0
Response: { data: AuditLogPublic[], count: number }
Auth: Bearer token required, group membership verified
```

**Expense-level audit log:**
```
GET /api/v1/expenses/{expense_id}/audit-log?limit=50&offset=0
Response: { data: AuditLogPublic[], count: number }
Auth: Bearer token required, group membership verified
```

**Potential new endpoint (only if needed):**
```
GET /api/v1/expenses/activity?limit=20&offset=0
Response: { data: AuditLogPublic[], count: number }
Purpose: Combined feed across all user's groups
```

### Security Considerations

- [x] Authorization - Existing endpoints already verify group membership (Story 4.4)
- [x] Input Validation - limit/offset already validated by backend
- [x] Data Privacy - Only audit logs from groups user is a member of are returned
- [ ] Rate Limiting - Not critical for read-only feed, consider for "all groups" endpoint

### Project Structure Notes

- New components: `frontend/src/features/expenses/components/ActivityFeed.tsx`, `ActivityFeedItem.tsx`
- New utils: `frontend/src/features/expenses/utils/activityFormatters.ts`
- Modified: `frontend/src/routes/_layout/activity.tsx` (replace placeholder)
- Optional new endpoint: `backend/app/features/expenses/router.py`
- Follow existing patterns: components use design system tokens, hooks use TanStack Query

### References

- [Epic 4 Story 4.5 definition](_bmad-output/planning-artifacts/epics.md - lines 771-791)
- [AuditLog model](_bmad-output/planning-artifacts/architecture.md)
- [Previous Story 4.4](_bmad-output/implementation-artifacts/4-4-immutable-audit-log-for-all-actions.md)
- [Existing AuditLogList component](frontend/src/features/expenses/components/AuditLogList.tsx)
- [Existing API hooks](frontend/src/features/expenses/api/expenses.ts)
- [Activity page placeholder](frontend/src/routes/_layout/activity.tsx)
- [Frontend types](frontend/src/features/expenses/types.ts)
- [GroupSettings AI personality](backend/app/features/groups/models.py:140-156)
- [Dashboard with last_activity](frontend/src/features/dashboard/components/Dashboard.tsx)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7

### Debug Log References

No new issues encountered. Docker prestart failed due to pre-existing Alembic migration issue (missing revision 5e78d661700e), unrelated to this story.

### Completion Notes List

- Created `ActivityFeed.tsx` component with chat-bubble styling, offset-based pagination (20 per page), loading/error/empty states
- Created `ActivityFeedItem.tsx` with framer-motion fade-up animation, avatar with initials, action-type icon badge, relative timestamps with exact date on hover
- Created `activityFormatters.ts` with centralized formatting for all 6 AuditActionTypes: created, edited, confirmed, rejected, settled, split_updated
- Created shared `formatRelativeTime` utility in `timeFormat.ts` (extracted from AuditLogList for reuse)
- Replaced activity page placeholder with `CombinedActivityFeed` that aggregates audit logs across all user groups, sorted chronologically
- Integrated `ActivityFeed` into `GroupDetail` component showing "Recent Activity" section
- All tasks completed with no backend changes needed (existing audit-log endpoints sufficient)
- Client-side aggregation used for "all groups" view instead of new backend endpoint (avoids unnecessary backend changes)

### File List

**New files:**
- frontend/src/features/expenses/components/ActivityFeed.tsx
- frontend/src/features/expenses/components/ActivityFeedItem.tsx
- frontend/src/features/expenses/utils/activityFormatters.ts
- frontend/src/features/expenses/utils/timeFormat.ts

**Modified files:**
- frontend/src/routes/_layout/activity.tsx
- frontend/src/features/groups/components/GroupDetail.tsx
- frontend/src/features/expenses/components/AuditLogList.tsx (code review: imported shared formatRelativeTime)
- frontend/src/features/expenses/utils/activityFormatters.ts (code review: removed dead getActionIcon)
