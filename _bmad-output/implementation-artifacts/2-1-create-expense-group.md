# Story 2.1: Create Expense Group

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **registered user**,
I want to create a new expense group with a name,
so that I can organize expenses with specific people.

## Acceptance Criteria

1. **Given** I am logged in
   **When** I create a group with a name (e.g., "Weekend Trip")
   **Then** a new group is created in the database with my user as the creator/owner

2. **And** the group model includes: `id`, `name`, `created_by`, `created_at`, `updated_at`

3. **And** I am automatically added as a member of the group

4. **And** a `group_member` join table tracks user-group relationships

5. **And** the API endpoint follows naming convention: `POST /api/v1/expense-groups`

6. **And** the table uses snake_case naming: `expense_group`, `group_member`

## Tasks / Subtasks

- [x] Task 1: Create ExpenseGroup SQLModel (AC: #1, #2, #6)
  - [x] Define `ExpenseGroup` model in `backend/app/features/groups/models.py`
  - [x] Add fields: `id` (uuid.UUID), `name` (str), `created_by` (uuid.UUID FK)
  - [x] Add timestamp fields: `created_at`, `updated_at` (using `utc_now` pattern from auth/models.py)
  - [x] Set `__tablename__ = "expense_group"` (singular, matching existing pattern)
  - [x] Add `creator: User = Relationship()` for back_populates
  - [x] Add Pydantic request/response schemas: `ExpenseGroupCreate`, `ExpenseGroupPublic`

- [x] Task 2: Create GroupMember join table model (AC: #3, #4, #6)
  - [x] Define `GroupMember` model as SQLModel with `table=True`
  - [x] Add fields: `id` (uuid.UUID), `group_id` (uuid.UUID FK), `user_id` (uuid.UUID FK)
  - [x] Add `joined_at` timestamp field
  - [x] Add `role` field (str, default="member", values: "owner", "member")
  - [x] Set `__tablename__ = "group_member"` (singular)
  - [x] Create unique constraint on (group_id, user_id) combination

- [x] Task 3: Create Alembic migration (AC: #2, #4, #6)
  - [x] Generate migration: `alembic revision --autogenerate -m "add_expense_group_and_group_member"`
  - [x] Review generated migration for correct table names and foreign keys
  - [x] Add indexes on `group_member.group_id` and `group_member.user_id`
  - [x] Run migration: `alembic upgrade head`
  - [x] Verify tables exist in database

- [x] Task 4: Create group service layer (AC: #1, #3)
  - [x] Create `create_expense_group()` function in `backend/app/features/groups/service.py`
  - [x] Accept `session`, `name`, `creator_id` parameters
  - [x] Create ExpenseGroup record with creator_id in `created_by`
  - [x] Automatically create GroupMember record with role="owner"
  - [x] Return created group with member info
  - [x] Add `get_group_by_id()` helper function
  - [x] Add `get_user_groups()` to list all groups for a user

- [x] Task 5: Create POST endpoint (AC: #1, #5)
  - [x] Add `POST /` endpoint to `backend/app/features/groups/router.py`
  - [x] Use `CurrentUser` dependency for authentication
  - [x] Validate group name (non-empty, max 100 chars)
  - [x] Call service layer to create group
  - [x] Return 201 with created group data
  - [x] Add proper docstring for OpenAPI docs

- [x] Task 6: Register router in main app (AC: #5)
  - [x] Verify `groups.router` is registered in `backend/app/api/main.py`
  - [x] Ensure prefix is `/expense-groups` (already set in router.py)
  - [x] Verify endpoint appears in `/docs` at correct path

- [x] Task 7: Write backend tests
  - [x] Test creating a group as authenticated user
  - [x] Test creator is automatically added as member with "owner" role
  - [x] Test creating group with empty name returns 422
  - [x] Test creating group while unauthenticated returns 401
  - [x] Test group appears in user's group list after creation
  - [x] Add tests to `backend/tests/api/routes/test_groups.py`

- [x] Task 8: Create frontend API integration (AC: #1)
  - [x] Create `frontend/src/features/groups/api/` directory
  - [x] Add `groups.ts` with TanStack Query hooks
  - [x] Create `useCreateGroup` mutation hook
  - [x] Create `useUserGroups` query hook
  - [x] Add types in `frontend/src/features/groups/types.ts`

- [x] Task 9: Create basic frontend UI (AC: #1)
  - [x] Create `frontend/src/features/groups/components/CreateGroupForm.tsx`
  - [x] Add name input field with validation
  - [x] Add submit button with loading state
  - [x] Show success toast on creation
  - [x] Redirect to group page or dashboard after creation

## Dev Notes

### CRITICAL: This is the first story in Epic 2 - Group Management & Dashboard

Story 2.1 establishes the foundation for all group-related functionality. The ExpenseGroup and GroupMember models created here will be used by:
- Story 2.2: Invite Members via Deep Link
- Story 2.3: View Group Members List
- Story 2.4: Dashboard with Net Balances
- All of Epic 3: Smart Expense Entry (expenses belong to groups)

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
backend/app/
├── features/groups/
│   ├── models.py      # ExpenseGroup, GroupMember, schemas (UPDATE)
│   ├── service.py     # Business logic (UPDATE)
│   ├── router.py      # API endpoints (UPDATE)
│   └── __init__.py
├── api/main.py        # Register groups router (VERIFY)
└── alembic/versions/  # New migration file (CREATE)

frontend/src/
├── features/groups/
│   ├── api/
│   │   └── groups.ts      # TanStack Query hooks (CREATE)
│   ├── components/
│   │   └── CreateGroupForm.tsx  # Group creation UI (CREATE)
│   ├── types.ts           # TypeScript types (CREATE)
│   └── index.ts           # Feature exports (CREATE)
```

**Naming Conventions (MANDATORY):**
- Database tables: `snake_case`, **singular** (following existing pattern: `user`, `magic_link_token`)
- Database columns: `snake_case` (e.g., `created_by`, `group_id`)
- API JSON: `snake_case` fields
- Python: `snake_case` (PEP-8)
- TypeScript variables: `camelCase`
- TypeScript components: `PascalCase`
- TypeScript types/interfaces: `PascalCase`

**API Endpoint Pattern:**
```
POST /api/v1/expense-groups    - Create new group (this story)
GET  /api/v1/expense-groups    - List user's groups (future)
GET  /api/v1/expense-groups/{id} - Get group details (future)
```

### Technical Requirements

**ExpenseGroup Model (backend/app/features/groups/models.py):**
```python
import uuid
from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel

from app.features.auth.models import User, utc_now


# === Request/Response Schemas ===

class ExpenseGroupCreate(SQLModel):
    """Request schema for creating a group."""
    name: str = Field(min_length=1, max_length=100)


class ExpenseGroupPublic(SQLModel):
    """Response schema for a group."""
    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ExpenseGroupWithMembers(ExpenseGroupPublic):
    """Response schema for a group with member count."""
    member_count: int = 0


# === Database Models ===

class ExpenseGroup(SQLModel, table=True):
    """
    Expense group for organizing shared expenses among members.
    """
    __tablename__ = "expense_group"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    created_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})

    # Relationships
    creator: User = Relationship()
    members: list["GroupMember"] = Relationship(back_populates="group", cascade_delete=True)


# Role constants
GROUP_ROLE_OWNER = "owner"
GROUP_ROLE_MEMBER = "member"


class GroupMember(SQLModel, table=True):
    """
    Join table tracking user membership in expense groups.
    """
    __tablename__ = "group_member"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="expense_group.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    role: str = Field(default=GROUP_ROLE_MEMBER, max_length=20)
    joined_at: datetime = Field(default_factory=utc_now)

    # Relationships
    group: ExpenseGroup = Relationship(back_populates="members")
    user: User = Relationship()

    class Config:
        # Ensure unique constraint on (group_id, user_id)
        pass
```

**Service Layer Pattern (backend/app/features/groups/service.py):**
```python
import uuid
from sqlmodel import Session, select

from app.features.groups.models import (
    ExpenseGroup,
    ExpenseGroupCreate,
    GroupMember,
    GROUP_ROLE_OWNER,
)


def create_expense_group(
    session: Session,
    group_in: ExpenseGroupCreate,
    creator_id: uuid.UUID
) -> ExpenseGroup:
    """
    Create a new expense group and add creator as owner.

    Args:
        session: Database session
        group_in: Group creation data
        creator_id: UUID of the user creating the group

    Returns:
        Created ExpenseGroup with creator as member
    """
    # Create the group
    group = ExpenseGroup(
        name=group_in.name,
        created_by=creator_id,
    )
    session.add(group)
    session.flush()  # Get the group.id before creating member

    # Add creator as owner member
    member = GroupMember(
        group_id=group.id,
        user_id=creator_id,
        role=GROUP_ROLE_OWNER,
    )
    session.add(member)
    session.commit()
    session.refresh(group)

    return group


def get_group_by_id(session: Session, group_id: uuid.UUID) -> ExpenseGroup | None:
    """Get a group by ID."""
    return session.get(ExpenseGroup, group_id)


def get_user_groups(session: Session, user_id: uuid.UUID) -> list[ExpenseGroup]:
    """Get all groups where user is a member."""
    statement = (
        select(ExpenseGroup)
        .join(GroupMember)
        .where(GroupMember.user_id == user_id)
        .order_by(ExpenseGroup.updated_at.desc())
    )
    return list(session.exec(statement).all())


def is_group_member(session: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Check if user is a member of the group."""
    statement = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    )
    return session.exec(statement).first() is not None
```

**Router Pattern (backend/app/features/groups/router.py):**
```python
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.features.groups import service
from app.features.groups.models import (
    ExpenseGroup,
    ExpenseGroupCreate,
    ExpenseGroupPublic,
    ExpenseGroupWithMembers,
    GroupMember,
)

router = APIRouter(prefix="/expense-groups", tags=["groups"])


@router.post("/", response_model=ExpenseGroupPublic, status_code=201)
def create_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_in: ExpenseGroupCreate,
) -> ExpenseGroup:
    """
    Create a new expense group.

    The authenticated user becomes the owner of the group and is
    automatically added as a member.
    """
    group = service.create_expense_group(
        session=session,
        group_in=group_in,
        creator_id=current_user.id,
    )
    return group


@router.get("/", response_model=list[ExpenseGroupWithMembers])
def list_user_groups(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[dict]:
    """
    List all expense groups the current user is a member of.
    """
    groups = service.get_user_groups(session, current_user.id)

    # Add member counts
    result = []
    for group in groups:
        member_count = session.exec(
            select(GroupMember).where(GroupMember.group_id == group.id)
        ).all()
        result.append({
            **group.model_dump(),
            "member_count": len(member_count),
        })

    return result
```

**Migration Pattern:**
```python
# alembic/versions/xxx_add_expense_group_and_group_member.py
def upgrade():
    # Create expense_group table
    op.create_table(
        'expense_group',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_expense_group_name', 'expense_group', ['name'])

    # Create group_member table
    op.create_table(
        'group_member',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['expense_group.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_member_group_id', 'group_member', ['group_id'])
    op.create_index('ix_group_member_user_id', 'group_member', ['user_id'])
    # Unique constraint to prevent duplicate memberships
    op.create_unique_constraint('uq_group_member_group_user', 'group_member', ['group_id', 'user_id'])


def downgrade():
    op.drop_table('group_member')
    op.drop_table('expense_group')
```

### Frontend Implementation Details

**TanStack Query Hooks (frontend/src/features/groups/api/groups.ts):**
```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { ExpenseGroup, ExpenseGroupCreate } from '../types'

const API_BASE = '/api/v1/expense-groups'

async function createGroup(data: ExpenseGroupCreate): Promise<ExpenseGroup> {
  const token = localStorage.getItem('access_token')
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create group')
  }

  return response.json()
}

async function fetchUserGroups(): Promise<ExpenseGroup[]> {
  const token = localStorage.getItem('access_token')
  const response = await fetch(API_BASE, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch groups')
  }

  return response.json()
}

export function useCreateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createGroup,
    onSuccess: () => {
      // Invalidate and refetch groups list
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useUserGroups() {
  return useQuery({
    queryKey: ['groups'],
    queryFn: fetchUserGroups,
  })
}
```

**TypeScript Types (frontend/src/features/groups/types.ts):**
```typescript
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
  role: 'owner' | 'member'
  joined_at: string
}
```

**Create Group Form Component:**
```typescript
// frontend/src/features/groups/components/CreateGroupForm.tsx
import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'

import { useCreateGroup } from '../api/groups'

export function CreateGroupForm() {
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const createGroup = useCreateGroup()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError('Group name is required')
      return
    }

    try {
      await createGroup.mutateAsync({ name: name.trim() })
      // Redirect to dashboard or group list
      navigate({ to: '/' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create group')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium">
          Group Name
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Weekend Trip"
          maxLength={100}
          className="mt-1 block w-full rounded-md border px-3 py-2"
          disabled={createGroup.isPending}
        />
      </div>

      {error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      <button
        type="submit"
        disabled={createGroup.isPending}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {createGroup.isPending ? 'Creating...' : 'Create Group'}
      </button>
    </form>
  )
}
```

### Project Structure Notes

**Backend Changes:**
```
backend/app/
├── features/groups/
│   ├── models.py           # UPDATE: Add ExpenseGroup, GroupMember, schemas
│   ├── service.py          # UPDATE: Add CRUD functions
│   └── router.py           # UPDATE: Add POST / endpoint
├── api/main.py             # VERIFY: groups router registered
└── alembic/versions/
    └── xxx_add_expense_group_and_group_member.py  # CREATE
```

**Frontend Changes:**
```
frontend/src/features/groups/
├── api/
│   └── groups.ts           # CREATE: TanStack Query hooks
├── components/
│   └── CreateGroupForm.tsx # CREATE: Group creation form
├── types.ts                # CREATE: TypeScript types
└── index.ts                # CREATE: Feature exports
```

### Previous Story Intelligence

**From Story 1.6 (Social Authentication):**
- OAuth flow establishes pattern for external redirects
- JWT token stored in localStorage - reuse for API calls
- SessionMiddleware pattern for state management

**From Story 1.5 (Login with JWT):**
- `CurrentUser` dependency available for authenticated endpoints
- 401 error handling interceptor already implemented
- Token included in Authorization header

**From Story 1.3 (Database Models):**
- `utc_now()` helper function defined in `auth/models.py` - **REUSE**
- UUID as primary key pattern established
- `created_at`/`updated_at` timestamp pattern established

**Patterns to Reuse:**
- UUID primary keys with `uuid.uuid4` default factory
- `utc_now()` for timestamp fields
- `SessionDep` and `CurrentUser` dependencies from `app.api.deps`
- SQLModel table=True pattern
- Foreign key with ondelete="CASCADE"

### Git Intelligence

**Recent Commits:**
- `b9df621` - feat: Complete Story 1.6 - Social Authentication (OAuth) + Epic 1 Complete
- `43ed2c5` - feat: Complete Story 1.5 - User login with JWT authentication
- `df16775` - feat: Complete Story 1.4 - User registration with magic link

**Commit Message Format:**
```
feat: Complete Story 2.1 - Create expense group
```

### Testing Commands

```bash
# Start Docker containers
docker compose up -d

# Run migration
docker compose exec backend alembic upgrade head

# Run backend tests
docker compose exec backend pytest -v tests/api/routes/test_groups.py

# Run all backend tests
docker compose exec backend pytest -v

# Test endpoint manually
curl -X POST http://localhost:8000/api/v1/expense-groups \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Weekend Trip"}'

# Frontend build check
cd frontend && npm run build

# Frontend type check
cd frontend && npm run typecheck
```

### API Contract

**POST /api/v1/expense-groups**
```
// Request
POST /api/v1/expense-groups
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Weekend Trip"
}

// Response 201 Created
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Weekend Trip",
  "created_by": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2026-01-08T10:30:00Z",
  "updated_at": "2026-01-08T10:30:00Z"
}

// Response 401 Unauthorized
{
  "detail": "Not authenticated"
}

// Response 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "type": "string_too_short"
    }
  ]
}
```

**GET /api/v1/expense-groups**
```
// Request
GET /api/v1/expense-groups
Authorization: Bearer <jwt_token>

// Response 200 OK
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Weekend Trip",
    "created_by": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2026-01-08T10:30:00Z",
    "updated_at": "2026-01-08T10:30:00Z",
    "member_count": 1
  }
]
```

### References

- [Source: epics.md - Story 2.1](../_bmad-output/planning-artifacts/epics.md#story-21-create-expense-group)
- [Source: architecture.md - Project Structure](../_bmad-output/planning-artifacts/architecture.md#complete-project-directory-structure)
- [Source: architecture.md - Naming Patterns](../_bmad-output/planning-artifacts/architecture.md#naming-patterns)
- [Existing Code: features/auth/models.py](../../backend/app/features/auth/models.py)
- [Existing Code: features/groups/models.py](../../backend/app/features/groups/models.py)
- [Existing Code: features/groups/router.py](../../backend/app/features/groups/router.py)
- [Existing Code: features/groups/service.py](../../backend/app/features/groups/service.py)
- [Previous Story: 1-6-social-authentication-oauth.md](./1-6-social-authentication-oauth.md)

### Important Notes for Developer

1. **Table Naming**: Use **singular** form (`expense_group`, `group_member`) matching the existing pattern in `user` table, NOT the plural form mentioned in architecture.md. The codebase has established singular as the convention.

2. **Import `utc_now`**: Import from `app.features.auth.models` - do NOT redefine it.

3. **Dependencies**: Use existing `SessionDep` and `CurrentUser` from `app.api.deps`.

4. **Router Registration**: The groups router should already be registered. Verify it appears in `/docs`.

5. **Unique Constraint**: The GroupMember table MUST have a unique constraint on (group_id, user_id) to prevent duplicate memberships.

6. **Cascade Delete**: Both foreign keys should have `ondelete="CASCADE"` for proper cleanup.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 97 backend tests pass (including 8 new group tests)
- Frontend build successful
- Database migration applied (c5e9f3a1b2d4)

### Completion Notes List

- Implemented ExpenseGroup and GroupMember models with proper relationships
- Created service layer with CRUD functions (create_expense_group, get_group_by_id, get_user_groups, is_group_member)
- Implemented POST /api/v1/expense-groups and GET /api/v1/expense-groups endpoints
- Added 8 comprehensive backend tests covering all acceptance criteria
- Created frontend API integration using TanStack Query hooks (useCreateGroup, useUserGroups)
- Built CreateGroupForm component with validation and success toast
- All acceptance criteria met and verified through tests

### File List

**Backend (Modified/Created):**
- backend/app/features/groups/models.py (MODIFIED)
- backend/app/features/groups/service.py (MODIFIED)
- backend/app/features/groups/router.py (MODIFIED)
- backend/app/api/main.py (MODIFIED - added groups router)
- backend/app/alembic/versions/c5e9f3a1b2d4_add_expense_group_and_group_member.py (CREATED)
- backend/tests/api/routes/test_groups.py (CREATED)
- backend/tests/conftest.py (MODIFIED - added group cleanup)

**Frontend (Created):**
- frontend/src/features/groups/types.ts (CREATED)
- frontend/src/features/groups/api/groups.ts (CREATED)
- frontend/src/features/groups/api/index.ts (CREATED)
- frontend/src/features/groups/components/CreateGroupForm.tsx (CREATED)
- frontend/src/features/groups/components/index.ts (CREATED)
- frontend/src/features/groups/hooks/index.ts (CREATED)
- frontend/src/features/groups/index.ts (CREATED)
- frontend/src/features/index.ts (MODIFIED)
- frontend/src/client/sdk.gen.ts (MODIFIED - added GroupsService)

## Change Log

- 2026-01-08: Story 2.1 implementation complete - Create expense group feature with backend API, database models, tests, and frontend integration
- 2026-01-08: Code review completed - 4 MEDIUM issues fixed (see review notes below)

## Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5 (Adversarial Code Review)
**Date:** 2026-01-08
**Outcome:** APPROVED (after fixes)

### Review Summary

| Category | Result |
|----------|--------|
| All ACs Implemented | 6/6 |
| All Tasks Complete | 9/9 |
| Tests Passing | 8/8 |
| High Issues | 0 |
| Medium Issues Fixed | 4/4 |
| Low Issues (Deferred) | 2 |

### Issues Found & Fixed

**MEDIUM #1: N+1 Query Problem** (FIXED)
- Location: `router.py:44-54`
- Problem: Separate DB query for each group to get member count
- Fix: Added `get_user_groups_with_member_count()` using single query with subquery

**MEDIUM #2: Inefficient Member Count** (FIXED)
- Location: `service.py:77-80`
- Problem: Fetched all records to count them
- Fix: Changed to use `func.count()` with SQL COUNT

**MEDIUM #3: Service Layer Transaction** (FIXED)
- Location: `service.py:45`
- Problem: `commit()` inside service broke transaction composition
- Fix: Moved to router endpoint, service now uses `flush()` only

**MEDIUM #4: Return Type Mismatch** (FIXED)
- Location: `router.py:40`
- Problem: Type annotation said `list[dict]` but response_model was `list[ExpenseGroupWithMembers]`
- Fix: Changed return type to `list[ExpenseGroupWithMembers]`

### Low Issues (Deferred)

1. Missing index on `created_by` field - Consider adding if "groups by creator" queries needed
2. `sprint-status.yaml` not in File List - Tracking file, expected

### Files Modified During Review

- `backend/app/features/groups/service.py` - Performance optimizations, transaction handling
- `backend/app/features/groups/router.py` - Optimized list endpoint, fixed types

### Verification

All 8 tests pass after fixes applied.
