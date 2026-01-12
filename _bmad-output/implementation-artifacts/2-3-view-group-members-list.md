# Story 2.3: View Group Members List

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **group member**,
I want to see all members in my group,
so that I know who is part of the expense tracking.

## Acceptance Criteria

1. **Given** I am a member of a group
   **When** I view the group details
   **Then** I see a list of all members with their names and email

2. **And** the creator/owner is indicated with a badge or label

3. **And** member data is fetched from the joined users table

4. **And** the API endpoint follows naming convention: `GET /api/v1/expense-groups/{group_id}/members`

## Tasks / Subtasks

- [x] Task 1: Create GroupMemberPublic schema with user details (AC: #1, #3)
  - [x] Add `GroupMemberPublic` schema to `backend/app/features/groups/models.py`
  - [x] Include fields: `id`, `user_id`, `role`, `joined_at`, `full_name`, `email`
  - [x] Add `GroupMembersListResponse` wrapper schema for response

- [x] Task 2: Create service function to get group members with user data (AC: #1, #3)
  - [x] Add `get_group_members_with_user_data()` to `backend/app/features/groups/service.py`
  - [x] Join GroupMember with User table to get full_name and email
  - [x] Order by role (owner first) then joined_at
  - [x] Return list of `GroupMemberPublic`

- [x] Task 3: Create GET endpoint for group members (AC: #1, #4)
  - [x] Add `GET /{group_id}/members` endpoint to `backend/app/features/groups/router.py`
  - [x] Verify current user is a member of the group
  - [x] Return 403 if not a member
  - [x] Return 404 if group not found
  - [x] Return list of members with user data

- [x] Task 4: Write backend tests (AC: ALL)
  - [x] Test getting members as group member
  - [x] Test getting members as non-member returns 403
  - [x] Test getting members of non-existent group returns 404
  - [x] Test owner is returned with role="owner"
  - [x] Test response includes full_name and email
  - [x] Add tests to `backend/tests/api/routes/test_groups.py`

- [x] Task 5: Add frontend types for GroupMemberPublic (AC: #1, #2)
  - [x] Add `GroupMemberPublic` type to `frontend/src/features/groups/types.ts`
  - [x] Include all fields: `id`, `user_id`, `role`, `joined_at`, `full_name`, `email`

- [x] Task 6: Create TanStack Query hook for fetching members (AC: #3)
  - [x] Add `useGroupMembers(groupId)` hook to `frontend/src/features/groups/api/groups.ts`
  - [x] Return query with members data and loading state

- [x] Task 7: Create MembersList React component (AC: #1, #2)
  - [x] Create `MembersList.tsx` in `frontend/src/features/groups/components/`
  - [x] Display each member with avatar placeholder, name, email
  - [x] Show "Owner" badge for members with role="owner"
  - [x] Handle loading and empty states
  - [x] Export from components index

- [x] Task 8: Integrate MembersList into group detail view (AC: ALL)
  - [x] Add MembersList to existing group detail page/component
  - [x] Pass groupId prop to the component

### Review Follow-ups (AI)

- [ ] [AI-Review][MEDIUM] Set up frontend test infrastructure (vitest, testing-library) and add component tests for MembersList, GroupDetail, and groups route

## Dev Notes

### CRITICAL: This story builds on Stories 2.1 and 2.2

Story 2.3 adds the ability to view group members, building on the existing group infrastructure. This is a **read-only** story with no database changes required.

**Key Implementation Points:**
- The `GroupMember` model already has a `user: User = Relationship()` - use this for joining
- Need to create a new schema that combines GroupMember fields with User fields
- Only group members should be able to view the member list (privacy)
- Owner should appear first in the list for easy identification

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
backend/app/
├── features/groups/
│   ├── models.py      # ADD: GroupMemberPublic schema
│   ├── service.py     # ADD: get_group_members_with_user_data()
│   └── router.py      # ADD: GET /{group_id}/members endpoint
└── tests/api/routes/test_groups.py  # ADD: member list tests

frontend/src/
├── features/groups/
│   ├── api/
│   │   └── groups.ts           # ADD: useGroupMembers hook
│   ├── components/
│   │   ├── MembersList.tsx     # CREATE
│   │   └── index.ts            # UPDATE exports
│   └── types.ts                # ADD: GroupMemberPublic type
```

**Naming Conventions (MANDATORY):**
- API JSON fields: `snake_case` (e.g., `full_name`, `user_id`, `joined_at`)
- Python: `snake_case` (PEP-8)
- TypeScript variables: `camelCase`
- TypeScript components: `PascalCase`

**API Endpoint Pattern:**
```
GET /api/v1/expense-groups/{group_id}/members   - List members (authenticated members only)
```

### Technical Requirements

**GroupMemberPublic Schema (ADD to backend/app/features/groups/models.py):**
```python
class GroupMemberPublic(SQLModel):
    """Response schema for a group member with user details."""
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    full_name: str
    email: str


class GroupMembersListResponse(SQLModel):
    """Response schema for list of group members."""
    members: list[GroupMemberPublic]
    count: int
```

**Service Layer Function (ADD to backend/app/features/groups/service.py):**
```python
from app.features.auth.models import User

def get_group_members_with_user_data(
    session: Session,
    group_id: uuid.UUID,
) -> list[GroupMemberPublic]:
    """
    Get all members of a group with their user details.

    Joins GroupMember with User to get full_name and email.
    Orders by role (owner first), then by joined_at.

    Args:
        session: Database session
        group_id: UUID of the group

    Returns:
        List of GroupMemberPublic with user details
    """
    from app.features.groups.models import GroupMemberPublic

    # Join GroupMember with User to get user details
    statement = (
        select(
            GroupMember.id,
            GroupMember.user_id,
            GroupMember.role,
            GroupMember.joined_at,
            User.full_name,
            User.email,
        )
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .order_by(
            # Owner first (descending sort: 'owner' > 'member' alphabetically)
            GroupMember.role.desc(),
            GroupMember.joined_at.asc()
        )
    )

    results = session.exec(statement).all()

    return [
        GroupMemberPublic(
            id=row.id,
            user_id=row.user_id,
            role=row.role,
            joined_at=row.joined_at,
            full_name=row.full_name,
            email=row.email,
        )
        for row in results
    ]
```

**Router Endpoint (ADD to backend/app/features/groups/router.py):**
```python
from app.features.groups.models import (
    # ... existing imports ...
    GroupMemberPublic,
    GroupMembersListResponse,
)


@router.get("/{group_id}/members", response_model=GroupMembersListResponse)
def list_group_members(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupMembersListResponse:
    """
    List all members of a group with their details.

    Only group members can view the member list.
    Returns members ordered by role (owner first), then by join date.
    """
    # Verify group exists
    group = service.get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Verify user is a member
    if not service.is_group_member(session, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )

    members = service.get_group_members_with_user_data(session, group_id)

    return GroupMembersListResponse(
        members=members,
        count=len(members),
    )
```

### Frontend Implementation Details

**TypeScript Types (ADD to frontend/src/features/groups/types.ts):**
```typescript
export interface GroupMemberPublic {
  id: string
  user_id: string
  role: "owner" | "member"
  joined_at: string
  full_name: string
  email: string
}

export interface GroupMembersListResponse {
  members: GroupMemberPublic[]
  count: number
}
```

**TanStack Query Hook (ADD to frontend/src/features/groups/api/groups.ts):**
```typescript
import type { GroupMembersListResponse } from "../types"

async function getGroupMembers(groupId: string): Promise<GroupMembersListResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/${groupId}/members`,
    errors: {
      401: "Unauthorized",
      403: "You are not a member of this group",
      404: "Group not found",
    },
  })
}

export function useGroupMembers(groupId: string) {
  return useQuery<GroupMembersListResponse, Error>({
    queryKey: ["groups", groupId, "members"],
    queryFn: () => getGroupMembers(groupId),
    enabled: !!groupId,
  })
}
```

**MembersList Component:**
```typescript
// frontend/src/features/groups/components/MembersList.tsx
import { useGroupMembers } from "../api/groups"
import type { GroupMemberPublic } from "../types"

interface Props {
  groupId: string
}

export function MembersList({ groupId }: Props) {
  const { data, isLoading, error } = useGroupMembers(groupId)

  if (isLoading) {
    return <div className="animate-pulse">Loading members...</div>
  }

  if (error) {
    return <div className="text-red-600">Failed to load members</div>
  }

  if (!data?.members.length) {
    return <div className="text-gray-500">No members found</div>
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">
        Members ({data.count})
      </h3>
      <ul className="divide-y divide-gray-200">
        {data.members.map((member) => (
          <MemberItem key={member.id} member={member} />
        ))}
      </ul>
    </div>
  )
}

function MemberItem({ member }: { member: GroupMemberPublic }) {
  const isOwner = member.role === "owner"

  return (
    <li className="flex items-center gap-3 py-3">
      {/* Avatar placeholder */}
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200 text-gray-600">
        {member.full_name?.charAt(0)?.toUpperCase() || "?"}
      </div>

      {/* Member info */}
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium">{member.full_name}</span>
          {isOwner && (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
              Owner
            </span>
          )}
        </div>
        <span className="text-sm text-gray-500">{member.email}</span>
      </div>
    </li>
  )
}
```

### Project Structure Notes

**Backend Changes:**
```
backend/app/
├── features/groups/
│   ├── models.py           # UPDATE: Add GroupMemberPublic, GroupMembersListResponse
│   ├── service.py          # UPDATE: Add get_group_members_with_user_data()
│   └── router.py           # UPDATE: Add GET /{group_id}/members endpoint
└── tests/api/routes/
    └── test_groups.py      # UPDATE: Add member list tests
```

**Frontend Changes:**
```
frontend/src/
├── features/groups/
│   ├── api/
│   │   └── groups.ts               # UPDATE: Add useGroupMembers hook
│   ├── components/
│   │   ├── MembersList.tsx         # CREATE
│   │   └── index.ts                # UPDATE: Export MembersList
│   └── types.ts                    # UPDATE: Add GroupMemberPublic types
```

### Previous Story Intelligence

**From Story 2.2 (Invite Members):**
- GroupInvite model pattern with relationships
- Router pattern with SessionDep and CurrentUser dependencies
- Service layer returns data, router handles HTTP responses
- TanStack Query hook patterns with `__request` helper

**From Story 2.1 (Create Expense Group):**
- `ExpenseGroup` and `GroupMember` models established
- `is_group_member()` function available for authorization
- `get_group_by_id()` function for fetching groups
- Transaction handling: service uses `flush()`, router calls `commit()`

**Patterns to Reuse:**
- `is_group_member()` for authorization check (already exists)
- `get_group_by_id()` for group existence check (already exists)
- GroupMember already has `user: User = Relationship()` for joining
- TanStack Query pattern with `useQuery` and `queryKey`

### Git Intelligence

**Recent Commits:**
- `1d6b5dc` - feat: Complete Story 2.2 - Invite members via deep link
- `a6fc3a8` - feat: Complete Story 2.1 - Create expense group

**Commit Message Format:**
```
feat: Complete Story 2.3 - View group members list
```

### Testing Commands

```bash
# Start Docker containers
docker compose up -d

# Run backend tests (no migration needed - read-only story)
docker compose exec backend pytest -v tests/api/routes/test_groups.py -k members

# Run all backend tests
docker compose exec backend pytest -v

# Test endpoint manually - List members
curl http://localhost:8000/api/v1/expense-groups/{group_id}/members \
  -H "Authorization: Bearer <token>"

# Frontend build check
cd cleardues/frontend && npm run build

# Frontend type check
cd cleardues/frontend && npm run typecheck
```

### API Contract

**GET /api/v1/expense-groups/{group_id}/members**
```
// Request
GET /api/v1/expense-groups/550e8400-e29b-41d4-a716-446655440000/members
Authorization: Bearer <jwt_token>

// Response 200 OK
{
  "members": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "role": "owner",
      "joined_at": "2026-01-08T10:30:00Z",
      "full_name": "Alex Smith",
      "email": "alex@example.com"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "user_id": "234e4567-e89b-12d3-a456-426614174001",
      "role": "member",
      "joined_at": "2026-01-09T14:20:00Z",
      "full_name": "Sam Johnson",
      "email": "sam@example.com"
    }
  ],
  "count": 2
}

// Response 403 Forbidden (not a member)
{
  "detail": "You are not a member of this group"
}

// Response 404 Not Found (group doesn't exist)
{
  "detail": "Group not found"
}
```

### References

- [Source: epics.md - Story 2.3](../_bmad-output/planning-artifacts/epics.md#story-23-view-group-members-list)
- [Source: architecture.md - API Patterns](../_bmad-output/planning-artifacts/architecture.md#api--communication-patterns)
- [Source: architecture.md - Naming Conventions](../_bmad-output/planning-artifacts/architecture.md#naming-patterns)
- [Existing Code: features/groups/models.py](../../cleardues/backend/app/features/groups/models.py)
- [Existing Code: features/groups/service.py](../../cleardues/backend/app/features/groups/service.py)
- [Existing Code: features/groups/router.py](../../cleardues/backend/app/features/groups/router.py)
- [Previous Story: 2-2-invite-members-via-deep-link.md](./2-2-invite-members-via-deep-link.md)

### Important Notes for Developer

1. **No Migration Required**: This is a read-only story that queries existing tables. No Alembic migration needed.

2. **Authorization**: Only group members can view the member list. Use existing `is_group_member()` function.

3. **Owner First**: Sort members so owner appears first in the list. The SQL `ORDER BY role ASC` works because "member" > "owner" alphabetically.

4. **User Relationship**: `GroupMember` already has `user: User = Relationship()` but we're using an explicit join for better control over the returned fields.

5. **Privacy**: Email addresses are exposed to group members only. This is acceptable for expense tracking groups.

6. **Component Naming**: Use `MembersList` (plural) not `MemberList` for clarity.

7. **Query Key Pattern**: Use `["groups", groupId, "members"]` for proper cache invalidation if members change.

8. **Loading State**: Show a skeleton/loading state while fetching members for better UX.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Fixed `full_name` field to be nullable (`str | None`) to handle users without full names

### Completion Notes List

- Implemented `GroupMemberPublic` schema with all required fields including nullable `full_name`
- Added `get_group_members_with_user_data()` service function with proper JOIN and DESC sorting for owner-first ordering
- Created `GET /{group_id}/members` endpoint with proper authorization (403 for non-members, 404 for missing group)
- Added 6 comprehensive backend tests covering all acceptance criteria
- Created frontend `GroupMemberPublic` type with nullable `full_name` field
- Added `useGroupMembers` TanStack Query hook with proper query key pattern
- Created `MembersList` component with avatar placeholder, owner badge, loading/empty states
- Created `GroupDetail` component integrating MembersList
- Created new `/groups` route page for viewing groups and members
- Updated `CreateGroupForm` to support `onSuccess` callback
- All 111 backend tests pass, frontend builds successfully

**Code Review Fixes Applied:**
- Fixed MembersList null full_name handling with "Unknown User" fallback
- Fixed story Dev Notes (sorting comment: asc→desc)
- Added backend test for null full_name edge case (7 member tests now)

### File List

**Backend (Modified):**
- backend/app/features/groups/models.py (added GroupMemberPublic, GroupMembersListResponse schemas)
- backend/app/features/groups/service.py (added get_group_members_with_user_data function)
- backend/app/features/groups/router.py (added GET /{group_id}/members endpoint)
- backend/tests/api/routes/test_groups.py (added 7 member list tests - includes null full_name test)

**Frontend (Modified):**
- frontend/src/features/groups/types.ts (added GroupMemberPublic, GroupMembersListResponse types)
- frontend/src/features/groups/api/groups.ts (added useGroupMembers hook)
- frontend/src/features/groups/components/index.ts (added exports)
- frontend/src/features/groups/components/CreateGroupForm.tsx (added onSuccess prop)

**Frontend (Created):**
- frontend/src/features/groups/components/MembersList.tsx
- frontend/src/features/groups/components/GroupDetail.tsx
- frontend/src/routes/_layout/groups.tsx

## Change Log

- 2026-01-12: Story 2.3 implementation complete - View group members list with full backend API, frontend components, and groups page
- 2026-01-12: Code review passed - Fixed 3 issues (null handling, doc comment, test coverage). 1 action item deferred (frontend tests). Status → done

