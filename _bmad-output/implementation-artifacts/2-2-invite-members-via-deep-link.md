# Story 2.2: Invite Members via Deep Link

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **group creator**,
I want to generate and share an invite link,
so that others can join my expense group easily.

## Acceptance Criteria

1. **Given** I have created a group
   **When** I generate an invite link
   **Then** a unique shareable URL is created with a token (e.g., `/invite/{token}`)

2. **And** the token is stored with the group_id and expiration (30 days)

3. **And** when a user clicks the link and is logged in, they are added to the group

4. **And** if not logged in, they are prompted to register/login first, then added

5. **And** the invite link can be used multiple times until expired

6. **And** expired tokens return appropriate error message

7. **And** the API endpoint follows naming convention: `GET /api/v1/expense-groups/invite/{token}`

## Tasks / Subtasks

- [x] Task 1: Create GroupInvite SQLModel (AC: #1, #2)
  - [x] Define `GroupInvite` model in `backend/app/features/groups/models.py`
  - [x] Add fields: `id` (uuid.UUID), `group_id` (uuid.UUID FK), `token` (str, unique, indexed)
  - [x] Add `expires_at` (datetime) for 30-day expiration
  - [x] Add `created_by` (uuid.UUID FK) to track who created the invite
  - [x] Add `created_at` timestamp using `utc_now` pattern
  - [x] Add `generate_token()` classmethod using `secrets.token_urlsafe(32)`
  - [x] Set `__tablename__ = "group_invite"` (singular, matching existing pattern)
  - [x] Add Pydantic schemas: `GroupInviteCreate`, `GroupInvitePublic`, `GroupInviteResponse`

- [x] Task 2: Create Alembic migration (AC: #2)
  - [x] Generate migration: `alembic revision --autogenerate -m "add_group_invite"`
  - [x] Review generated migration for correct table name and foreign keys
  - [x] Add indexes on `token` (unique) and `group_id`
  - [x] Run migration: `alembic upgrade head`
  - [x] Verify table exists in database

- [x] Task 3: Create invite service layer functions (AC: #1, #2, #3, #5, #6)
  - [x] Create `create_group_invite()` in `backend/app/features/groups/service.py`
  - [x] Create `get_invite_by_token()` function
  - [x] Create `accept_invite()` function - adds user as member if not already
  - [x] Create `is_invite_valid()` helper - checks expiration and group existence
  - [x] Create `get_group_invites()` function - list active invites for a group

- [x] Task 4: Create POST endpoint for generating invites (AC: #1, #2)
  - [x] Add `POST /expense-groups/{group_id}/invites` endpoint to router.py
  - [x] Verify current user is the group creator/owner
  - [x] Return 403 if not owner
  - [x] Generate token with 30-day expiration
  - [x] Return invite URL and expiration date

- [x] Task 5: Create GET endpoint for accepting invites (AC: #3, #4, #5, #6, #7)
  - [x] Add `GET /expense-groups/invite/{token}` endpoint to router.py
  - [x] Look up invite by token
  - [x] Return 404 if token not found
  - [x] Return 410 Gone if token expired
  - [x] Check if group still exists (return 404 if deleted)
  - [x] If user already a member, return success with message
  - [x] Add user as member with role="member"
  - [x] Return group details and success message

- [x] Task 6: Write backend tests (AC: ALL)
  - [x] Test creating invite as group owner
  - [x] Test creating invite as non-owner returns 403
  - [x] Test accepting valid invite adds user to group
  - [x] Test accepting invite when already member returns success
  - [x] Test expired token returns 410 Gone
  - [x] Test invalid/nonexistent token returns 404
  - [x] Test invite can be used multiple times by different users
  - [x] Add tests to `backend/tests/api/routes/test_groups.py`

- [x] Task 7: Create frontend invite generation UI (AC: #1)
  - [x] Create `GenerateInviteButton.tsx` component
  - [x] Add `useCreateInvite` mutation hook in `api/groups.ts`
  - [x] Display generated invite URL with copy button
  - [x] Show expiration date
  - [x] Add share functionality (if Web Share API available)

- [x] Task 8: Create frontend invite acceptance page (AC: #3, #4)
  - [x] Create `/invite/{token}` route in frontend router
  - [x] Create `AcceptInvitePage.tsx` component
  - [x] If logged in: call accept endpoint, redirect to group
  - [x] If not logged in: store token in sessionStorage, redirect to login
  - [x] After login: check sessionStorage for pending invite, accept it
  - [x] Show loading, success, and error states

- [x] Task 9: Update types and exports (AC: ALL)
  - [x] Add `GroupInvite` types to `frontend/src/features/groups/types.ts`
  - [x] Export new components from feature index

## Dev Notes

### CRITICAL: This story builds on Story 2.1 - Create Expense Group

Story 2.2 adds invite functionality to the existing group infrastructure. The `GroupInvite` model follows the same pattern as `MagicLinkToken` from the auth feature.

**Key Differences from MagicLinkToken:**
- Invite tokens can be used **multiple times** (no `used_at` tracking needed)
- Links to `group_id` instead of `email`
- 30-day expiration (vs 15 minutes for magic links)
- Only group owner can generate invites

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
backend/app/
├── features/groups/
│   ├── models.py      # ADD: GroupInvite model and schemas
│   ├── service.py     # ADD: Invite CRUD functions
│   └── router.py      # ADD: Invite endpoints
└── alembic/versions/  # New migration file (CREATE)

frontend/src/
├── features/groups/
│   ├── api/
│   │   └── groups.ts      # ADD: useCreateInvite, useAcceptInvite hooks
│   ├── components/
│   │   ├── GenerateInviteButton.tsx  # CREATE
│   │   └── index.ts                  # UPDATE exports
│   ├── pages/
│   │   └── AcceptInvitePage.tsx      # CREATE
│   └── types.ts           # ADD: GroupInvite types
└── routes/                # ADD: /invite/:token route
```

**Naming Conventions (MANDATORY):**
- Database table: `group_invite` (singular, snake_case)
- Database columns: `snake_case` (e.g., `group_id`, `expires_at`, `created_by`)
- API JSON: `snake_case` fields
- Python: `snake_case` (PEP-8)
- TypeScript variables: `camelCase`
- TypeScript components: `PascalCase`

**API Endpoint Pattern:**
```
POST /api/v1/expense-groups/{group_id}/invites   - Create invite (owner only)
GET  /api/v1/expense-groups/invite/{token}       - Accept invite (any authenticated user)
GET  /api/v1/expense-groups/{group_id}/invites   - List invites (owner only, optional)
```

### Technical Requirements

**GroupInvite Model (ADD to backend/app/features/groups/models.py):**
```python
import secrets
from datetime import datetime, timedelta

# Add to existing imports at top of file

# === ADD: Invite Schemas ===

class GroupInvitePublic(SQLModel):
    """Response schema for a group invite."""
    id: uuid.UUID
    group_id: uuid.UUID
    token: str
    expires_at: datetime
    created_at: datetime
    invite_url: str | None = None  # Computed field


class GroupInviteResponse(SQLModel):
    """Response after creating or accepting an invite."""
    invite: GroupInvitePublic | None = None
    group: ExpenseGroupPublic | None = None
    message: str


# === ADD: Database Model ===

# Invite expiration constant (30 days)
INVITE_EXPIRATION_DAYS = 30


class GroupInvite(SQLModel, table=True):
    """
    Invite tokens for joining expense groups via shareable links.
    Unlike magic link tokens, these can be used multiple times until expiration.
    """
    __tablename__ = "group_invite"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="expense_group.id", nullable=False, index=True)
    token: str = Field(unique=True, index=True, max_length=64)
    expires_at: datetime
    created_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    group: "ExpenseGroup" = Relationship()

    @classmethod
    def generate_token(cls) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(32)

    @classmethod
    def default_expiration(cls) -> datetime:
        """Get default expiration datetime (30 days from now)."""
        return utc_now() + timedelta(days=INVITE_EXPIRATION_DAYS)

    def is_expired(self) -> bool:
        """Check if this invite has expired."""
        return utc_now() > self.expires_at
```

**Service Layer Functions (ADD to backend/app/features/groups/service.py):**
```python
# Add imports at top
from datetime import datetime
from app.features.groups.models import (
    # ... existing imports ...
    GroupInvite,
    GroupInvitePublic,
    INVITE_EXPIRATION_DAYS,
)
from app.features.auth.models import utc_now

# === ADD: Invite Functions ===

def create_group_invite(
    session: Session,
    group_id: uuid.UUID,
    creator_id: uuid.UUID,
) -> GroupInvite:
    """
    Create a new invite token for a group.

    Args:
        session: Database session
        group_id: UUID of the group to create invite for
        creator_id: UUID of the user creating the invite (must be owner)

    Returns:
        Created GroupInvite with token
    """
    invite = GroupInvite(
        group_id=group_id,
        token=GroupInvite.generate_token(),
        expires_at=GroupInvite.default_expiration(),
        created_by=creator_id,
    )
    session.add(invite)
    session.flush()
    session.refresh(invite)
    return invite


def get_invite_by_token(session: Session, token: str) -> GroupInvite | None:
    """Get an invite by its token."""
    statement = select(GroupInvite).where(GroupInvite.token == token)
    return session.exec(statement).first()


def is_invite_valid(invite: GroupInvite) -> tuple[bool, str]:
    """
    Check if an invite is valid.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if invite.is_expired():
        return False, "This invite link has expired"
    return True, ""


def accept_invite(
    session: Session,
    invite: GroupInvite,
    user_id: uuid.UUID,
) -> tuple[bool, str]:
    """
    Accept an invite and add user to the group.

    Args:
        session: Database session
        invite: The invite to accept
        user_id: UUID of the user accepting the invite

    Returns:
        Tuple of (success, message)
    """
    # Check if already a member
    if is_group_member(session, invite.group_id, user_id):
        return True, "You are already a member of this group"

    # Add as member
    member = GroupMember(
        group_id=invite.group_id,
        user_id=user_id,
        role=GROUP_ROLE_MEMBER,
    )
    session.add(member)
    session.flush()

    return True, "Successfully joined the group"


def is_group_owner(session: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Check if user is the owner of the group."""
    statement = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.role == GROUP_ROLE_OWNER
    )
    return session.exec(statement).first() is not None


def get_group_invites(session: Session, group_id: uuid.UUID) -> list[GroupInvite]:
    """Get all active (non-expired) invites for a group."""
    statement = (
        select(GroupInvite)
        .where(
            GroupInvite.group_id == group_id,
            GroupInvite.expires_at > utc_now()
        )
        .order_by(GroupInvite.created_at.desc())
    )
    return list(session.exec(statement).all())
```

**Router Endpoints (ADD to backend/app/features/groups/router.py):**
```python
# Add imports
from fastapi import HTTPException, status
from app.core.config import settings
from app.features.groups.models import (
    # ... existing imports ...
    GroupInvite,
    GroupInvitePublic,
    GroupInviteResponse,
)

# === ADD: Invite Endpoints ===

@router.post("/{group_id}/invites", response_model=GroupInviteResponse, status_code=201)
def create_invite(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupInviteResponse:
    """
    Generate an invite link for a group.

    Only the group owner can generate invites.
    """
    # Verify group exists
    group = service.get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

    # Verify user is owner
    if not service.is_group_owner(session, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can generate invite links"
        )

    invite = service.create_group_invite(session, group_id, current_user.id)
    session.commit()

    # Build invite URL
    invite_url = f"{settings.FRONTEND_HOST}/invite/{invite.token}"

    return GroupInviteResponse(
        invite=GroupInvitePublic(
            id=invite.id,
            group_id=invite.group_id,
            token=invite.token,
            expires_at=invite.expires_at,
            created_at=invite.created_at,
            invite_url=invite_url,
        ),
        message="Invite link created successfully"
    )


@router.get("/invite/{token}", response_model=GroupInviteResponse)
def accept_invite(
    token: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupInviteResponse:
    """
    Accept a group invite using the invite token.

    The authenticated user will be added as a member of the group.
    """
    # Look up invite
    invite = service.get_invite_by_token(session, token)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite link"
        )

    # Check if valid
    is_valid, error_msg = service.is_invite_valid(invite)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=error_msg
        )

    # Get group (verify it still exists)
    group = service.get_group_by_id(session, invite.group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The group no longer exists"
        )

    # Accept the invite
    success, message = service.accept_invite(session, invite, current_user.id)
    session.commit()

    return GroupInviteResponse(
        group=ExpenseGroupPublic(
            id=group.id,
            name=group.name,
            created_by=group.created_by,
            created_at=group.created_at,
            updated_at=group.updated_at,
        ),
        message=message
    )
```

**Migration Pattern:**
```python
# alembic/versions/xxx_add_group_invite.py
def upgrade():
    op.create_table(
        'group_invite',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['expense_group.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_group_invite_token', 'group_invite', ['token'], unique=True)
    op.create_index('ix_group_invite_group_id', 'group_invite', ['group_id'])


def downgrade():
    op.drop_table('group_invite')
```

### Frontend Implementation Details

**TanStack Query Hooks (ADD to frontend/src/features/groups/api/groups.ts):**
```typescript
// Add types import
import type { GroupInvite, GroupInviteResponse } from '../types'

// === ADD: Invite hooks ===

async function createInvite(groupId: string): Promise<GroupInviteResponse> {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`${API_BASE}/${groupId}/invites`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create invite')
  }

  return response.json()
}

async function acceptInvite(token: string): Promise<GroupInviteResponse> {
  const authToken = localStorage.getItem('access_token')
  const response = await fetch(`${API_BASE}/invite/${token}`, {
    headers: {
      Authorization: `Bearer ${authToken}`,
    },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to accept invite')
  }

  return response.json()
}

export function useCreateInvite() {
  return useMutation({
    mutationFn: createInvite,
  })
}

export function useAcceptInvite() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: acceptInvite,
    onSuccess: () => {
      // Invalidate groups list to show new membership
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}
```

**TypeScript Types (ADD to frontend/src/features/groups/types.ts):**
```typescript
// === ADD: Invite types ===

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
```

**GenerateInviteButton Component:**
```typescript
// frontend/src/features/groups/components/GenerateInviteButton.tsx
import { useState } from 'react'

import { useCreateInvite } from '../api/groups'

interface Props {
  groupId: string
}

export function GenerateInviteButton({ groupId }: Props) {
  const [inviteUrl, setInviteUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const createInvite = useCreateInvite()

  const handleGenerate = async () => {
    try {
      const result = await createInvite.mutateAsync(groupId)
      if (result.invite?.invite_url) {
        setInviteUrl(result.invite.invite_url)
      }
    } catch (err) {
      console.error('Failed to create invite:', err)
    }
  }

  const handleCopy = async () => {
    if (inviteUrl) {
      await navigator.clipboard.writeText(inviteUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleShare = async () => {
    if (inviteUrl && navigator.share) {
      try {
        await navigator.share({
          title: 'Join my expense group',
          text: 'Click to join our expense tracking group',
          url: inviteUrl,
        })
      } catch (err) {
        // User cancelled or share failed, fall back to copy
        handleCopy()
      }
    } else {
      handleCopy()
    }
  }

  if (!inviteUrl) {
    return (
      <button
        onClick={handleGenerate}
        disabled={createInvite.isPending}
        className="rounded-md bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50"
      >
        {createInvite.isPending ? 'Generating...' : 'Generate Invite Link'}
      </button>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 rounded-md border bg-gray-50 p-2">
        <input
          type="text"
          value={inviteUrl}
          readOnly
          className="flex-1 bg-transparent text-sm"
        />
        <button
          onClick={handleCopy}
          className="rounded px-2 py-1 text-sm hover:bg-gray-200"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <button
        onClick={handleShare}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
      >
        Share Invite
      </button>
    </div>
  )
}
```

**AcceptInvitePage Component:**
```typescript
// frontend/src/features/groups/pages/AcceptInvitePage.tsx
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from '@tanstack/react-router'

import { useAcceptInvite } from '../api/groups'

const PENDING_INVITE_KEY = 'pending_invite_token'

export function AcceptInvitePage() {
  const { token } = useParams({ from: '/invite/$token' })
  const navigate = useNavigate()
  const acceptInvite = useAcceptInvite()
  const [error, setError] = useState<string | null>(null)

  const isAuthenticated = !!localStorage.getItem('access_token')

  useEffect(() => {
    if (!isAuthenticated) {
      // Store token and redirect to login
      sessionStorage.setItem(PENDING_INVITE_KEY, token)
      navigate({ to: '/login', search: { returnTo: `/invite/${token}` } })
      return
    }

    // Accept the invite
    acceptInvite.mutate(token, {
      onSuccess: (data) => {
        // Redirect to group or dashboard
        navigate({ to: '/' })
      },
      onError: (err) => {
        setError(err.message)
      },
    })
  }, [token, isAuthenticated])

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Redirecting to login...</p>
      </div>
    )
  }

  if (acceptInvite.isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Joining group...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-red-600">{error}</p>
        <button
          onClick={() => navigate({ to: '/' })}
          className="text-blue-600 underline"
        >
          Go to Dashboard
        </button>
      </div>
    )
  }

  return null
}

// Helper to check and process pending invites after login
export function processPendingInvite(): string | null {
  const token = sessionStorage.getItem(PENDING_INVITE_KEY)
  if (token) {
    sessionStorage.removeItem(PENDING_INVITE_KEY)
  }
  return token
}
```

### Project Structure Notes

**Backend Changes:**
```
backend/app/
├── features/groups/
│   ├── models.py           # UPDATE: Add GroupInvite, schemas
│   ├── service.py          # UPDATE: Add invite functions
│   └── router.py           # UPDATE: Add invite endpoints
├── core/config.py          # VERIFY: FRONTEND_HOST setting exists
└── alembic/versions/
    └── xxx_add_group_invite.py  # CREATE
```

**Frontend Changes:**
```
frontend/src/
├── features/groups/
│   ├── api/
│   │   └── groups.ts                # UPDATE: Add invite hooks
│   ├── components/
│   │   ├── GenerateInviteButton.tsx # CREATE
│   │   └── index.ts                 # UPDATE: Export new component
│   ├── pages/
│   │   └── AcceptInvitePage.tsx     # CREATE
│   └── types.ts                     # UPDATE: Add invite types
└── routes/
    └── __root.tsx or routes.tsx     # UPDATE: Add /invite/:token route
```

### Previous Story Intelligence

**From Story 2.1 (Create Expense Group):**
- `ExpenseGroup` and `GroupMember` models established
- `create_expense_group()` pattern shows how to add member after group creation
- `is_group_member()` function available for checking membership
- Router pattern with `SessionDep` and `CurrentUser` dependencies
- Transaction handling: service uses `flush()`, router calls `commit()`

**From Story 1.4 (Magic Link):**
- `MagicLinkToken` model shows token generation pattern: `secrets.token_urlsafe(32)`
- Token expiration pattern with `expires_at` field
- Token validation pattern

**Patterns to Reuse:**
- `secrets.token_urlsafe(32)` for secure token generation (from MagicLinkToken)
- `utc_now()` for timestamp fields
- `SessionDep` and `CurrentUser` dependencies
- Service layer returns model, router calls commit
- 410 Gone status for expired tokens

### Git Intelligence

**Recent Commits:**
- `a6fc3a8` - feat: Complete Story 2.1 - Create expense group
- `b9df621` - feat: Complete Story 1.6 - Social Authentication (OAuth) + Epic 1 Complete

**Commit Message Format:**
```
feat: Complete Story 2.2 - Invite members via deep link
```

### Testing Commands

```bash
# Start Docker containers
docker compose up -d

# Run migration
docker compose exec backend alembic upgrade head

# Run backend tests
docker compose exec backend pytest -v tests/api/routes/test_groups.py -k invite

# Run all backend tests
docker compose exec backend pytest -v

# Test endpoint manually - Create invite
curl -X POST http://localhost:8000/api/v1/expense-groups/{group_id}/invites \
  -H "Authorization: Bearer <token>"

# Test endpoint manually - Accept invite
curl http://localhost:8000/api/v1/expense-groups/invite/{invite_token} \
  -H "Authorization: Bearer <token>"

# Frontend build check
cd frontend && npm run build

# Frontend type check
cd frontend && npm run typecheck
```

### API Contract

**POST /api/v1/expense-groups/{group_id}/invites**
```
// Request
POST /api/v1/expense-groups/550e8400-e29b-41d4-a716-446655440000/invites
Authorization: Bearer <jwt_token>

// Response 201 Created
{
  "invite": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "group_id": "550e8400-e29b-41d4-a716-446655440000",
    "token": "abc123xyz...",
    "expires_at": "2026-02-07T10:30:00Z",
    "created_at": "2026-01-08T10:30:00Z",
    "invite_url": "http://localhost:5173/invite/abc123xyz..."
  },
  "message": "Invite link created successfully"
}

// Response 403 Forbidden (not owner)
{
  "detail": "Only the group owner can generate invite links"
}

// Response 404 Not Found (group doesn't exist)
{
  "detail": "Group not found"
}
```

**GET /api/v1/expense-groups/invite/{token}**
```
// Request
GET /api/v1/expense-groups/invite/abc123xyz...
Authorization: Bearer <jwt_token>

// Response 200 OK
{
  "group": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Weekend Trip",
    "created_by": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2026-01-08T10:30:00Z",
    "updated_at": "2026-01-08T10:30:00Z"
  },
  "message": "Successfully joined the group"
}

// Response 200 OK (already member)
{
  "group": { ... },
  "message": "You are already a member of this group"
}

// Response 404 Not Found (invalid token)
{
  "detail": "Invalid invite link"
}

// Response 410 Gone (expired)
{
  "detail": "This invite link has expired"
}
```

### References

- [Source: epics.md - Story 2.2](../_bmad-output/planning-artifacts/epics.md#story-22-invite-members-via-deep-link)
- [Source: architecture.md - API Patterns](../_bmad-output/planning-artifacts/architecture.md#api--communication-patterns)
- [Source: architecture.md - Naming Conventions](../_bmad-output/planning-artifacts/architecture.md#naming-patterns)
- [Existing Code: features/groups/models.py](../../backend/app/features/groups/models.py)
- [Existing Code: features/groups/service.py](../../backend/app/features/groups/service.py)
- [Existing Code: features/groups/router.py](../../backend/app/features/groups/router.py)
- [Existing Code: features/auth/models.py - MagicLinkToken](../../backend/app/features/auth/models.py)
- [Previous Story: 2-1-create-expense-group.md](./2-1-create-expense-group.md)

### Important Notes for Developer

1. **Token Pattern**: Follow `MagicLinkToken` pattern exactly - use `secrets.token_urlsafe(32)` for security.

2. **Multi-Use Tokens**: Unlike magic links, invite tokens can be used multiple times. Do NOT add `used_at` tracking.

3. **Owner-Only**: Only the group OWNER (role="owner") can create invites. Check role, not just membership.

4. **410 Gone vs 404**: Use 410 for expired tokens (resource existed but is gone), 404 for invalid tokens.

5. **Frontend Auth Flow**: Handle unauthenticated users by storing token in sessionStorage before redirect.

6. **FRONTEND_HOST Setting**: Ensure `settings.FRONTEND_HOST` is configured in `backend/app/core/config.py`.

7. **Import secrets**: Add `import secrets` at the top of models.py if not present.

8. **Cascade Delete**: GroupInvite should cascade delete when the group is deleted.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

- Code review performed and fixes applied for AC #4 (pending invite flow after login)
- Added error display and expiration date to GenerateInviteButton

### File List

**Backend - Modified:**
- `backend/app/features/groups/models.py` - Added GroupInvite model, schemas
- `backend/app/features/groups/router.py` - Added invite endpoints
- `backend/app/features/groups/service.py` - Added invite service functions
- `backend/tests/api/routes/test_groups.py` - Added invite tests
- `backend/tests/conftest.py` - Added GroupInvite to cleanup, second_user fixture

**Backend - Created:**
- `backend/app/alembic/versions/d7e8f9a0b1c2_add_group_invite.py` - Migration for group_invite table

**Frontend - Modified:**
- `frontend/src/features/groups/api/groups.ts` - Added invite API hooks
- `frontend/src/features/groups/components/index.ts` - Export GenerateInviteButton
- `frontend/src/features/groups/types.ts` - Added GroupInvite types
- `frontend/src/routes/login.verify.$token.tsx` - Process pending invite after login (code review fix)

**Frontend - Created:**
- `frontend/src/features/groups/components/GenerateInviteButton.tsx` - Invite generation UI
- `frontend/src/routes/invite.$token.tsx` - Invite acceptance page
