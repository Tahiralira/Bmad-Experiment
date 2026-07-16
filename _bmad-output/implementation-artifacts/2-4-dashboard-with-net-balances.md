# Story 2.4: Dashboard with Net Balances

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **registered user**,
I want to view a dashboard showing my net balance across all groups,
so that I can quickly understand my overall financial standing.

## Acceptance Criteria

1. **Given** I am a member of multiple groups with recorded expenses
   **When** I view the dashboard
   **Then** I see a summary of all groups I belong to

2. **And** for each group, I see my net balance (positive if owed to me, negative if I owe)

3. **And** the balance is calculated from all confirmed expenses in the group

4. **And** groups are sorted by most recent activity

5. **And** the frontend fetches data via API: `GET /api/v1/users/me/dashboard`

6. **And** the API returns json with snake_case fields: `group_name`, `net_balance`, `last_activity`

## Tasks / Subtasks

- [x] Task 1: Create Dashboard schemas in auth/models.py (AC: #5, #6)
  - [x] Add `GroupBalanceSummary` schema with `group_id`, `group_name`, `net_balance`, `last_activity`, `member_count`
  - [x] Add `DashboardResponse` wrapper schema with `groups`, `total_balance`, `count`
  - [x] Ensure all fields use snake_case as per architecture

- [x] Task 2: Create dashboard service function in auth/service.py (AC: #1, #2, #3, #4)
  - [x] Add `get_user_dashboard()` function that fetches all groups for a user
  - [x] For each group, calculate net_balance (placeholder: 0 until expenses exist)
  - [x] Include last_activity timestamp from group's updated_at
  - [x] Order by most recent activity (updated_at DESC)
  - [x] Return list of GroupBalanceSummary objects

- [x] Task 3: Create GET /users/me/dashboard endpoint in auth/router.py (AC: #5, #6)
  - [x] Add endpoint to users_router as `GET /me/dashboard`
  - [x] Require authentication (CurrentUser dependency)
  - [x] Return DashboardResponse with groups and total balance
  - [x] Full endpoint path: `GET /api/v1/users/me/dashboard`

- [x] Task 4: Write backend tests (AC: ALL)
  - [x] Test getting dashboard as authenticated user
  - [x] Test dashboard returns user's groups with correct fields
  - [x] Test groups are sorted by most recent activity
  - [x] Test net_balance is 0 (no expenses yet)
  - [x] Test unauthenticated returns 401
  - [x] Add tests to `backend/tests/api/routes/test_users.py`

- [x] Task 5: Create frontend Dashboard types (AC: #6)
  - [x] Add `GroupBalanceSummary` interface to `frontend/src/features/dashboard/types.ts`
  - [x] Add `DashboardResponse` interface
  - [x] Create types.ts file in dashboard feature

- [x] Task 6: Create TanStack Query hook for dashboard (AC: #5)
  - [x] Create `frontend/src/features/dashboard/api/dashboard.ts`
  - [x] Add `useDashboard()` hook to fetch GET /users/me/dashboard
  - [x] Export from api/index.ts

- [x] Task 7: Create Dashboard React component (AC: #1, #2)
  - [x] Create `frontend/src/features/dashboard/components/Dashboard.tsx`
  - [x] Display list of groups with name, net balance, and last activity
  - [x] Show positive balances in green, negative in red, zero in gray
  - [x] Display total balance across all groups
  - [x] Handle loading and empty states
  - [x] Create components/index.ts for exports

- [x] Task 8: Create dashboard route page (AC: ALL)
  - [x] Create `frontend/src/routes/_layout/index.tsx` (or update existing)
  - [x] Integrate Dashboard component as the home page
  - [x] Add navigation link to dashboard in layout

## Dev Notes

### CRITICAL: This story completes Epic 2 (Group Management & Dashboard)

Story 2.4 adds the main dashboard view showing net balances across all groups. This is the final story in Epic 2. **Important:** Since expenses don't exist yet (Epic 3), all net balances will be 0 until expense functionality is implemented.

**Key Implementation Points:**
- The endpoint path `/api/v1/users/me/dashboard` goes in the existing `users_router` (prefix `/users`)
- Net balance calculation is a placeholder (returns 0) until Epic 3 adds expenses
- Groups are sorted by `updated_at` descending (most recent activity)
- This is a **read-only** story with no database changes required

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
backend/app/
├── features/auth/
│   ├── models.py      # ADD: GroupBalanceSummary, DashboardResponse schemas
│   ├── service.py     # ADD: get_user_dashboard() function
│   └── router.py      # ADD: GET /me/dashboard endpoint to users_router
└── tests/api/routes/test_users.py  # ADD: dashboard tests

frontend/src/
├── features/dashboard/
│   ├── api/
│   │   ├── dashboard.ts       # CREATE: useDashboard hook
│   │   └── index.ts           # CREATE: exports
│   ├── components/
│   │   ├── Dashboard.tsx      # CREATE: main component
│   │   └── index.ts           # CREATE: exports
│   ├── types.ts               # CREATE: TypeScript interfaces
│   └── index.ts               # UPDATE: exports
```

**Naming Conventions (MANDATORY):**
- API JSON fields: `snake_case` (e.g., `net_balance`, `group_name`, `last_activity`)
- Python: `snake_case` (PEP-8)
- TypeScript variables: `camelCase`
- TypeScript components: `PascalCase`

**API Endpoint Pattern:**
```
GET /api/v1/users/me/dashboard   - Get user's dashboard with group balances
```

### Technical Requirements

**GroupBalanceSummary Schema (ADD to backend/app/features/auth/models.py):**
```python
class GroupBalanceSummary(SQLModel):
    """Summary of a group with net balance for dashboard display."""
    group_id: uuid.UUID
    group_name: str
    net_balance: float  # Positive = owed to user, negative = user owes
    last_activity: datetime
    member_count: int


class DashboardResponse(SQLModel):
    """Response schema for user dashboard."""
    groups: list[GroupBalanceSummary]
    total_balance: float  # Sum of all net_balances
    count: int  # Number of groups
```

**Service Layer Function (ADD to backend/app/features/auth/service.py):**
```python
from app.features.groups.models import ExpenseGroup, GroupMember
from app.features.auth.models import GroupBalanceSummary
from sqlalchemy import func

def get_user_dashboard(session: Session, user_id: uuid.UUID) -> list[GroupBalanceSummary]:
    """
    Get dashboard data for a user showing all groups with net balances.

    Currently returns 0 for all net_balances as expenses are not yet implemented.
    When expenses are added in Epic 3, this function will calculate actual balances.

    Args:
        session: Database session
        user_id: UUID of the user

    Returns:
        List of GroupBalanceSummary objects ordered by most recent activity
    """
    # Subquery to count members per group
    member_count_subq = (
        select(GroupMember.group_id, func.count().label("member_count"))
        .group_by(GroupMember.group_id)
        .subquery()
    )

    # Main query to get user's groups with member counts
    statement = (
        select(
            ExpenseGroup.id,
            ExpenseGroup.name,
            ExpenseGroup.updated_at,
            member_count_subq.c.member_count,
        )
        .join(GroupMember, GroupMember.group_id == ExpenseGroup.id)
        .join(member_count_subq, member_count_subq.c.group_id == ExpenseGroup.id)
        .where(GroupMember.user_id == user_id)
        .order_by(ExpenseGroup.updated_at.desc())  # Most recent activity first
    )

    results = session.exec(statement).all()

    return [
        GroupBalanceSummary(
            group_id=row.id,
            group_name=row.name,
            net_balance=0.0,  # Placeholder until expenses implemented (Epic 3)
            last_activity=row.updated_at,
            member_count=row.member_count,
        )
        for row in results
    ]
```

**Router Endpoint (ADD to backend/app/features/auth/router.py - users_router section):**
```python
from app.features.auth.models import (
    # ... existing imports ...
    GroupBalanceSummary,
    DashboardResponse,
)


@users_router.get("/me/dashboard", response_model=DashboardResponse)
def get_dashboard(
    session: SessionDep,
    current_user: CurrentUser,
) -> DashboardResponse:
    """
    Get the current user's dashboard with group balances.

    Returns all groups the user is a member of with their net balance
    (positive if owed to user, negative if user owes).
    Groups are sorted by most recent activity.
    """
    groups = auth_service.get_user_dashboard(session, current_user.id)
    total_balance = sum(g.net_balance for g in groups)

    return DashboardResponse(
        groups=groups,
        total_balance=total_balance,
        count=len(groups),
    )
```

### Frontend Implementation Details

**TypeScript Types (CREATE frontend/src/features/dashboard/types.ts):**
```typescript
export interface GroupBalanceSummary {
  group_id: string
  group_name: string
  net_balance: number  // Positive = owed to user, negative = user owes
  last_activity: string  // ISO datetime string
  member_count: number
}

export interface DashboardResponse {
  groups: GroupBalanceSummary[]
  total_balance: number
  count: number
}
```

**TanStack Query Hook (CREATE frontend/src/features/dashboard/api/dashboard.ts):**
```typescript
import { useQuery } from "@tanstack/react-query"
import { OpenAPI, __request } from "../../../client/core/request"
import type { DashboardResponse } from "../types"

async function getDashboard(): Promise<DashboardResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/users/me/dashboard",
    errors: {
      401: "Unauthorized",
    },
  })
}

export function useDashboard() {
  return useQuery<DashboardResponse, Error>({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  })
}
```

**Dashboard Component (CREATE frontend/src/features/dashboard/components/Dashboard.tsx):**
```typescript
import { useDashboard } from "../api/dashboard"
import type { GroupBalanceSummary } from "../types"
import { Link } from "@tanstack/react-router"

export function Dashboard() {
  const { data, isLoading, error } = useDashboard()

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-600 p-4 bg-red-50 rounded">
        Failed to load dashboard: {error.message}
      </div>
    )
  }

  if (!data?.groups.length) {
    return (
      <div className="text-center py-8">
        <h2 className="text-xl font-semibold text-gray-600 mb-2">
          No groups yet
        </h2>
        <p className="text-gray-500 mb-4">
          Create a group to start tracking expenses with friends
        </p>
        <Link
          to="/groups"
          className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Create Group
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Total Balance Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-lg font-medium text-gray-500">Total Balance</h1>
        <p className={`text-3xl font-bold ${getBalanceColor(data.total_balance)}`}>
          {formatBalance(data.total_balance)}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Across {data.count} group{data.count !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Groups List */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Your Groups</h2>
        {data.groups.map((group) => (
          <GroupCard key={group.group_id} group={group} />
        ))}
      </div>
    </div>
  )
}

function GroupCard({ group }: { group: GroupBalanceSummary }) {
  return (
    <Link
      to="/groups"
      className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-medium">{group.group_name}</h3>
          <p className="text-sm text-gray-500">
            {group.member_count} member{group.member_count !== 1 ? "s" : ""} &bull;{" "}
            {formatLastActivity(group.last_activity)}
          </p>
        </div>
        <div className={`text-lg font-semibold ${getBalanceColor(group.net_balance)}`}>
          {formatBalance(group.net_balance)}
        </div>
      </div>
    </Link>
  )
}

function getBalanceColor(balance: number): string {
  if (balance > 0) return "text-green-600"
  if (balance < 0) return "text-red-600"
  return "text-gray-500"
}

function formatBalance(balance: number): string {
  const sign = balance > 0 ? "+" : ""
  return `${sign}$${Math.abs(balance).toFixed(2)}`
}

function formatLastActivity(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return "Today"
  if (diffDays === 1) return "Yesterday"
  if (diffDays < 7) return `${diffDays} days ago`
  return date.toLocaleDateString()
}
```

### Project Structure Notes

**Backend Changes:**
```
backend/app/
├── features/auth/
│   ├── models.py           # UPDATE: Add GroupBalanceSummary, DashboardResponse
│   ├── service.py          # UPDATE: Add get_user_dashboard() function
│   └── router.py           # UPDATE: Add GET /me/dashboard endpoint
└── tests/api/routes/
    └── test_users.py       # UPDATE: Add dashboard tests
```

**Frontend Changes:**
```
frontend/src/
├── features/dashboard/
│   ├── api/
│   │   ├── dashboard.ts           # CREATE: useDashboard hook
│   │   └── index.ts               # CREATE: exports
│   ├── components/
│   │   ├── Dashboard.tsx          # CREATE: main component
│   │   └── index.ts               # CREATE: exports
│   ├── types.ts                   # CREATE: TypeScript interfaces
│   └── index.ts                   # UPDATE: exports
```

### Previous Story Intelligence

**From Story 2.3 (View Group Members):**
- Schema pattern: `SQLModel` base class for response schemas
- Service pattern: Use subqueries for efficient JOINs
- Router pattern: `SessionDep` and `CurrentUser` dependencies
- TanStack Query pattern: `useQuery` with `queryKey` and `queryFn`

**From Story 2.1 (Create Expense Group):**
- ExpenseGroup model with `updated_at` field for activity tracking
- GroupMember join table for user-group relationships
- `get_user_groups_with_member_count()` pattern to reuse

**Patterns to Reuse:**
- Service function returns data objects, router wraps in response schema
- Subquery pattern for efficient member counting
- Frontend component with loading/error/empty states
- Query key naming: `["dashboard"]` for cache management

### Git Intelligence

**Recent Commits:**
- `f214516` - feat: Complete Story 2.3 - View group members list
- `1d6b5dc` - feat: Complete Story 2.2 - Invite members via deep link
- `a6fc3a8` - feat: Complete Story 2.1 - Create expense group

**Commit Message Format:**
```
feat: Complete Story 2.4 - Dashboard with net balances
```

### Testing Commands

```bash
# Start Docker containers
docker compose up -d

# Run backend tests (no migration needed - read-only story)
docker compose exec backend pytest -v tests/api/routes/test_users.py -k dashboard

# Run all backend tests
docker compose exec backend pytest -v

# Test endpoint manually - Get dashboard
curl http://localhost:8000/api/v1/users/me/dashboard \
  -H "Authorization: Bearer <token>"

# Frontend build check
cd frontend && npm run build

# Frontend type check
cd frontend && npm run typecheck
```

### API Contract

**GET /api/v1/users/me/dashboard**
```
// Request
GET /api/v1/users/me/dashboard
Authorization: Bearer <jwt_token>

// Response 200 OK
{
  "groups": [
    {
      "group_id": "550e8400-e29b-41d4-a716-446655440000",
      "group_name": "Weekend Trip",
      "net_balance": 0.00,
      "last_activity": "2026-01-12T10:30:00Z",
      "member_count": 4
    },
    {
      "group_id": "660e8400-e29b-41d4-a716-446655440001",
      "group_name": "Roommates",
      "net_balance": 0.00,
      "last_activity": "2026-01-10T14:20:00Z",
      "member_count": 3
    }
  ],
  "total_balance": 0.00,
  "count": 2
}

// Response 401 Unauthorized (no token)
{
  "detail": "Not authenticated"
}
```

### Important Notes for Developer

1. **No Migration Required**: This is a read-only story that queries existing tables. No Alembic migration needed.

2. **Net Balance Placeholder**: All `net_balance` values will be `0.0` until Epic 3 (Smart Expense Entry) implements expenses. The infrastructure is ready for future calculation.

3. **Endpoint Location**: Add to existing `users_router` in `auth/router.py` since it's a user-specific endpoint (`/users/me/dashboard`).

4. **Import GroupMember from groups**: The service function needs to import from `app.features.groups.models`.

5. **Activity Sorting**: Use `ExpenseGroup.updated_at.desc()` for "most recent activity" sorting.

6. **Frontend Dashboard Feature**: Create the full dashboard feature folder structure under `frontend/src/features/dashboard/`.

7. **Balance Display Logic**:
   - Positive (green): You are owed money
   - Negative (red): You owe money
   - Zero (gray): Settled

8. **Epic 2 Completion**: This is the final story in Epic 2. Upon completion, Epic 2 status should be updated to "done".

### References

- [Source: epics.md - Story 2.4](../_bmad-output/planning-artifacts/epics.md#story-24-dashboard-with-net-balances)
- [Source: architecture.md - API Patterns](../_bmad-output/planning-artifacts/architecture.md#api--communication-patterns)
- [Source: architecture.md - Frontend Architecture](../_bmad-output/planning-artifacts/architecture.md#frontend-architecture)
- [Source: prd.md - FR3](../_bmad-output/planning-artifacts/prd.md#user--group-management)
- [Existing Code: features/auth/router.py](../../backend/app/features/auth/router.py)
- [Existing Code: features/groups/models.py](../../backend/app/features/groups/models.py)
- [Previous Story: 2-3-view-group-members-list.md](./2-3-view-group-members-list.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - implementation proceeded without issues

### Completion Notes List

- All 8 tasks completed successfully
- Backend: Added dashboard schemas, service function, and API endpoint to auth feature
- Backend tests: Added 6 comprehensive tests covering authenticated access, group data, sorting, balance values, and unauthenticated rejection
- Frontend: Created complete dashboard feature with types, API hook, and component
- Frontend integration: Updated home route to display Dashboard component
- Sidebar navigation: Added Groups link for easy access to expense groups
- All acceptance criteria satisfied:
  - AC#1: Dashboard shows summary of all user's groups
  - AC#2: Net balance displayed per group (currently 0.0 as placeholder)
  - AC#3: Balance calculation infrastructure ready (placeholder until Epic 3)
  - AC#4: Groups sorted by most recent activity (updated_at DESC)
  - AC#5: Frontend fetches via GET /api/v1/users/me/dashboard
  - AC#6: API returns snake_case fields (group_name, net_balance, last_activity)

### File List

**Backend (Modified):**
- backend/app/features/auth/models.py - Added GroupBalanceSummary, DashboardResponse schemas
- backend/app/features/auth/service.py - Added get_user_dashboard() function
- backend/app/features/auth/router.py - Added GET /me/dashboard endpoint
- backend/tests/api/routes/test_users.py - Added 6 dashboard tests

**Frontend (Created):**
- frontend/src/features/dashboard/types.ts - TypeScript interfaces
- frontend/src/features/dashboard/api/dashboard.ts - useDashboard hook
- frontend/src/features/dashboard/api/index.ts - API exports
- frontend/src/features/dashboard/components/Dashboard.tsx - Main component
- frontend/src/features/dashboard/components/index.ts - Component exports

**Frontend (Modified):**
- frontend/src/features/dashboard/index.ts - Updated exports
- frontend/src/routes/_layout/index.tsx - Integrated Dashboard component
- frontend/src/components/Sidebar/AppSidebar.tsx - Added Groups navigation link

## Senior Developer Review (AI)

**Review Date:** 2026-01-12
**Reviewer:** Claude Opus 4.5 (code-review workflow)
**Verdict:** APPROVED with fixes applied

### Review Summary

| Category | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 5 (all fixed) |
| Low | 4 (logged) |

### AC Validation

| AC# | Status | Evidence |
|-----|--------|----------|
| AC#1 | PASS | Dashboard shows groups list |
| AC#2 | PASS | GroupCard displays net_balance |
| AC#3 | PASS | Placeholder 0.0 (expected per story) |
| AC#4 | PASS | service.py:286 order_by(updated_at.desc()) |
| AC#5 | PASS | dashboard.ts:10 correct URL |
| AC#6 | PASS | models.py uses snake_case |

### Task Audit

All 8 tasks verified as actually implemented. No false claims.

### Issues Found & Fixed

**MEDIUM (5 - All Fixed):**
1. **M1:** Added comment explaining circular import in service.py:266
2. **M2:** Added TODO for group detail route + truncation for long names
3. **M3:** Added future date handling in formatLastActivity
4. **M4:** Switched to Intl.NumberFormat for locale-aware currency
5. **M5:** Added retry button with refetch in error state

**Bonus Fixes:**
- Added dark mode support throughout Dashboard.tsx
- Improved loading skeleton to match actual layout

**LOW (4 - Logged to technical-debt-log.yaml):**
1. No explicit snake_case field verification in tests
2. Loading skeleton structure (resolved)
3. GroupCard text truncation (resolved)
4. Dark mode support (resolved)

### Files Modified in Review

- backend/app/features/auth/service.py - Added circular import comment
- frontend/src/features/dashboard/components/Dashboard.tsx - Fixed M2-M5 + dark mode

## Change Log

- 2026-01-12: Story 2.4 created via create-story workflow - Dashboard with net balances
- 2026-01-12: Story 2.4 implementation completed - All 8 tasks done, ready for review
- 2026-01-12: Senior Developer Review completed - 5 MEDIUM issues fixed, 4 LOW logged, APPROVED

