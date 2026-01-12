# Story 3.1: Create Expense Model and Basic Entry

Status: done

## Story

As a **group member**,
I want to add a simple numeric expense to my group,
so that I can track who paid and how much.

## Acceptance Criteria

1. **Given** I am a member of a group
   **When** I create an expense with amount, description, and payer
   **Then** an expense record is created in the database

2. **And** the expense model includes: `id`, `group_id`, `amount`, `description`, `payer_id`, `created_by`, `status`, `created_at`

3. **And** the status is set to "draft" initially

4. **And** the API endpoint follows naming convention: `POST /api/v1/expenses`

5. **And** the table uses snake_case naming: `expenses`

6. **And** the expense is associated with a valid group the user belongs to

7. **And** invalid group_id or non-member user returns 403 Forbidden

## Tasks / Subtasks

- [x] Task 1: Create Expense database model (AC: #2, #3, #5)
  - [x] Create `Expense` model in `backend/app/features/expenses/models.py`
  - [x] Add fields: id, group_id, amount, description, payer_id, created_by, status, created_at, updated_at
  - [x] Set status default to "draft" using ExpenseStatus enum
  - [x] Add foreign keys to expense_group and user tables
  - [x] Create Alembic migration

- [x] Task 2: Create ExpenseSplit model for future split logic (AC: foundation for Epic 3)
  - [x] Create `ExpenseSplit` model with expense_id, user_id, amount_owed, status
  - [x] Add to same migration as Expense model

- [x] Task 3: Create request/response schemas (AC: #2, #5)
  - [x] Add `ExpenseCreate` schema for POST request body
  - [x] Add `ExpensePublic` schema for response
  - [x] Add `ExpenseStatus` enum (draft, pending_confirmation, confirmed, settled)
  - [x] Ensure all fields use snake_case

- [x] Task 4: Create expense service layer (AC: #1, #6, #7)
  - [x] Add `create_expense()` function in `service.py`
  - [x] Validate user is member of group before creating
  - [x] Return 403 if user not in group
  - [x] Set created_by to current user

- [x] Task 5: Create POST /expenses endpoint (AC: #1, #4)
  - [x] Add `expenses_router` in `router.py` with prefix `/expenses`
  - [x] Create `POST /` endpoint for expense creation
  - [x] Register router in main.py API routes
  - [x] Remove or deprecate items_router (legacy)

- [x] Task 6: Write backend tests (AC: ALL)
  - [x] Test creating expense as group member
  - [x] Test expense has correct fields and default status
  - [x] Test non-member cannot create expense in group (403)
  - [x] Test invalid group_id returns 404
  - [x] Test unauthenticated returns 401

- [x] Task 7: Create frontend expense types (AC: #2)
  - [x] Add `Expense`, `ExpenseCreate` interfaces in `frontend/src/features/expenses/types.ts`
  - [x] Add `ExpenseStatus` type

- [x] Task 8: Create TanStack mutation for creating expense (AC: #4)
  - [x] Create `frontend/src/features/expenses/api/expenses.ts`
  - [x] Add `useCreateExpense()` mutation hook
  - [x] Add query invalidation for dashboard

- [x] Task 9: Create basic expense form component (AC: #1)
  - [x] Create `frontend/src/features/expenses/components/ExpenseForm.tsx`
  - [x] Form fields: amount (number), description (text), group selector
  - [x] Submit calls useCreateExpense mutation
  - [x] Show success/error feedback

## Dev Notes

### CRITICAL: This is the foundation story for Epic 3 (Smart Expense Entry)

Story 3.1 establishes the core expense data model and basic CRUD operations. All subsequent stories in Epic 3 (NLP parsing, split logic, exclusions) build on this foundation. **Get the model right - it's the hardest to change later.**

**Key Design Decisions:**
- Expense status starts as "draft" - becomes "pending_confirmation" when splits are applied (Story 3.5+)
- The `payer_id` field tracks WHO PAID, while `created_by` tracks WHO ENTERED the expense (may differ)
- ExpenseSplit model is created now but populated in Stories 3.5-3.8

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
backend/app/
├── features/expenses/
│   ├── models.py      # UPDATE: Add Expense, ExpenseSplit, ExpenseStatus, schemas
│   ├── service.py     # UPDATE: Add create_expense() function
│   └── router.py      # UPDATE: Replace items_router with expenses_router
├── api/main.py        # UPDATE: Register expenses router
└── tests/api/routes/
    └── test_expenses.py  # CREATE: Expense endpoint tests

frontend/src/
├── features/expenses/
│   ├── api/
│   │   ├── expenses.ts    # CREATE: useCreateExpense hook
│   │   └── index.ts       # CREATE: exports
│   ├── components/
│   │   ├── ExpenseForm.tsx   # CREATE: basic form component
│   │   └── index.ts          # CREATE: exports
│   ├── types.ts              # CREATE: TypeScript interfaces
│   └── index.ts              # UPDATE: exports
```

**Naming Conventions (MANDATORY):**
- API JSON fields: `snake_case` (e.g., `group_id`, `payer_id`, `created_by`)
- Python: `snake_case` (PEP-8)
- TypeScript variables: `camelCase`
- TypeScript components: `PascalCase`
- Database table: `expense` (singular, snake_case)

### Technical Requirements

**Expense Model (UPDATE backend/app/features/expenses/models.py):**
```python
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlmodel import Field, Relationship, SQLModel

from app.features.auth.models import User, utc_now
from app.features.groups.models import ExpenseGroup


class ExpenseStatus(str, PyEnum):
    """Status lifecycle for expenses."""
    DRAFT = "draft"                       # Initial state when created
    PENDING_CONFIRMATION = "pending_confirmation"  # Splits assigned, awaiting confirms
    CONFIRMED = "confirmed"               # All members confirmed
    SETTLED = "settled"                   # Debts paid off


# === Request/Response Schemas ===

class ExpenseCreate(SQLModel):
    """Request schema for creating an expense."""
    group_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    description: str = Field(min_length=1, max_length=500)
    payer_id: uuid.UUID | None = None  # Defaults to current user if not provided


class ExpensePublic(SQLModel):
    """Response schema for an expense."""
    id: uuid.UUID
    group_id: uuid.UUID
    amount: Decimal
    description: str
    payer_id: uuid.UUID
    created_by: uuid.UUID
    status: ExpenseStatus
    created_at: datetime
    updated_at: datetime


class ExpensesPublic(SQLModel):
    """Response schema for list of expenses."""
    data: list[ExpensePublic]
    count: int


# === Database Models ===

class Expense(SQLModel, table=True):
    """
    Expense record in a group.

    Tracks who paid (payer_id) and who created (created_by) the expense.
    Status progresses: draft -> pending_confirmation -> confirmed -> settled
    """
    __tablename__ = "expense"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="expense_group.id", nullable=False, index=True)
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    description: str = Field(max_length=500)
    payer_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    created_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    status: ExpenseStatus = Field(default=ExpenseStatus.DRAFT)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})

    # Relationships
    group: ExpenseGroup = Relationship()
    payer: User = Relationship(sa_relationship_kwargs={"foreign_keys": "[Expense.payer_id]"})
    creator: User = Relationship(sa_relationship_kwargs={"foreign_keys": "[Expense.created_by]"})
    splits: list["ExpenseSplit"] = Relationship(back_populates="expense", cascade_delete=True)


class SplitStatus(str, PyEnum):
    """Status for individual expense splits."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SETTLED = "settled"


class ExpenseSplit(SQLModel, table=True):
    """
    Individual debt record from an expense split.

    Created when expense is split (Stories 3.5-3.8).
    Each split represents what one user owes from the expense.
    """
    __tablename__ = "expense_split"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    expense_id: uuid.UUID = Field(foreign_key="expense.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    amount_owed: Decimal = Field(max_digits=10, decimal_places=2)
    status: SplitStatus = Field(default=SplitStatus.PENDING)
    confirmed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    expense: Expense = Relationship(back_populates="splits")
    user: User = Relationship()
```

**Service Layer (UPDATE backend/app/features/expenses/service.py):**
```python
import uuid
from decimal import Decimal

from sqlmodel import Session, select

from app.features.expenses.models import Expense, ExpenseCreate, ExpenseStatus
from app.features.groups.models import GroupMember


def is_user_group_member(session: Session, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
    """Check if user is a member of the specified group."""
    statement = select(GroupMember).where(
        GroupMember.user_id == user_id,
        GroupMember.group_id == group_id
    )
    return session.exec(statement).first() is not None


def create_expense(
    session: Session,
    expense_in: ExpenseCreate,
    current_user_id: uuid.UUID
) -> Expense:
    """
    Create a new expense in a group.

    Args:
        session: Database session
        expense_in: Expense creation data
        current_user_id: ID of the user creating the expense

    Returns:
        Created Expense object

    Note:
        - payer_id defaults to current_user_id if not provided
        - status is always DRAFT for new expenses
        - Caller must verify user is member of group first
    """
    expense = Expense(
        group_id=expense_in.group_id,
        amount=expense_in.amount,
        description=expense_in.description,
        payer_id=expense_in.payer_id or current_user_id,
        created_by=current_user_id,
        status=ExpenseStatus.DRAFT,
    )
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense
```

**Router Endpoint (UPDATE backend/app/features/expenses/router.py):**
```python
import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.features.expenses import service as expense_service
from app.features.expenses.models import ExpenseCreate, ExpensePublic
from app.features.groups.models import ExpenseGroup

router = APIRouter()

expenses_router = APIRouter(prefix="/expenses", tags=["expenses"])


@expenses_router.post("/", response_model=ExpensePublic)
def create_expense(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_in: ExpenseCreate,
) -> ExpensePublic:
    """
    Create a new expense in a group.

    The current user must be a member of the group.
    If payer_id is not provided, defaults to the current user.
    New expenses start with status 'draft'.
    """
    # Verify group exists
    group = session.get(ExpenseGroup, expense_in.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify user is member of group
    if not expense_service.is_user_group_member(
        session, current_user.id, expense_in.group_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You must be a member of the group to create expenses"
        )

    # If payer_id provided, verify payer is also a group member
    if expense_in.payer_id and expense_in.payer_id != current_user.id:
        if not expense_service.is_user_group_member(
            session, expense_in.payer_id, expense_in.group_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Payer must be a member of the group"
            )

    expense = expense_service.create_expense(session, expense_in, current_user.id)
    return ExpensePublic.model_validate(expense)


# Include expenses router
router.include_router(expenses_router)
```

**CRITICAL: Register Router in main.py (UPDATE backend/app/api/main.py):**
```python
# Add to imports
from app.features.expenses.router import router as expenses_router

# Add to router includes (after existing routers)
api_router.include_router(expenses_router)
```

### Frontend Implementation Details

**TypeScript Types (CREATE frontend/src/features/expenses/types.ts):**
```typescript
export type ExpenseStatus = "draft" | "pending_confirmation" | "confirmed" | "settled"

export interface Expense {
  id: string
  group_id: string
  amount: number
  description: string
  payer_id: string
  created_by: string
  status: ExpenseStatus
  created_at: string
  updated_at: string
}

export interface ExpenseCreate {
  group_id: string
  amount: number
  description: string
  payer_id?: string  // Defaults to current user
}

export interface ExpensesResponse {
  data: Expense[]
  count: number
}
```

**TanStack Mutation (CREATE frontend/src/features/expenses/api/expenses.ts):**
```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { OpenAPI, __request } from "../../../client/core/request"
import type { Expense, ExpenseCreate } from "../types"

async function createExpense(data: ExpenseCreate): Promise<Expense> {
  return __request(OpenAPI, {
    method: "POST",
    url: "/api/v1/expenses/",
    body: data,
    errors: {
      401: "Unauthorized",
      403: "Not a member of this group",
      404: "Group not found",
    },
  })
}

export function useCreateExpense() {
  const queryClient = useQueryClient()

  return useMutation<Expense, Error, ExpenseCreate>({
    mutationFn: createExpense,
    onSuccess: () => {
      // Invalidate dashboard to refresh balances (future: when expenses affect balance)
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      // Invalidate any expense lists for this group
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
    },
  })
}
```

**Basic Form Component (CREATE frontend/src/features/expenses/components/ExpenseForm.tsx):**
```typescript
import { useState } from "react"
import { useCreateExpense } from "../api/expenses"
import type { ExpenseCreate } from "../types"

interface ExpenseFormProps {
  groupId: string
  onSuccess?: () => void
  onCancel?: () => void
}

export function ExpenseForm({ groupId, onSuccess, onCancel }: ExpenseFormProps) {
  const [amount, setAmount] = useState("")
  const [description, setDescription] = useState("")
  const createExpense = useCreateExpense()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const expenseData: ExpenseCreate = {
      group_id: groupId,
      amount: parseFloat(amount),
      description: description.trim(),
    }

    try {
      await createExpense.mutateAsync(expenseData)
      setAmount("")
      setDescription("")
      onSuccess?.()
    } catch (error) {
      // Error handled by mutation
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="amount" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Amount
        </label>
        <div className="mt-1 relative rounded-md shadow-sm">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-500 sm:text-sm">$</span>
          </div>
          <input
            type="number"
            id="amount"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="block w-full pl-7 pr-3 py-2 border border-gray-300 rounded-md dark:bg-gray-800 dark:border-gray-600"
            placeholder="0.00"
            required
          />
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Description
        </label>
        <input
          type="text"
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-800 dark:border-gray-600"
          placeholder="What was this expense for?"
          maxLength={500}
          required
        />
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={createExpense.isPending}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {createExpense.isPending ? "Creating..." : "Add Expense"}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Cancel
          </button>
        )}
      </div>

      {createExpense.isError && (
        <p className="text-red-600 text-sm">
          {createExpense.error.message || "Failed to create expense"}
        </p>
      )}
    </form>
  )
}
```

### Project Structure Notes

**Backend Changes:**
```
backend/app/
├── features/expenses/
│   ├── models.py           # UPDATE: Add Expense, ExpenseSplit, schemas, enums
│   ├── service.py          # UPDATE: Add create_expense(), is_user_group_member()
│   └── router.py           # UPDATE: Replace items_router with expenses_router
├── api/main.py             # UPDATE: Register expenses router
└── tests/api/routes/
    └── test_expenses.py    # CREATE: Expense endpoint tests
```

**Frontend Changes:**
```
frontend/src/features/expenses/
├── api/
│   ├── expenses.ts         # CREATE: useCreateExpense hook
│   └── index.ts            # CREATE: exports
├── components/
│   ├── ExpenseForm.tsx     # CREATE: basic form component
│   └── index.ts            # CREATE: exports
├── types.ts                # CREATE: TypeScript interfaces
└── index.ts                # UPDATE: exports
```

### Previous Story Intelligence

**From Story 2.4 (Dashboard with Net Balances):**
- Schema pattern: `SQLModel` base class for response schemas
- Service pattern: Separate validation from creation logic
- Router pattern: `SessionDep` and `CurrentUser` dependencies
- TanStack pattern: `useMutation` with `queryClient.invalidateQueries`

**From Story 2.1 (Create Expense Group):**
- GroupMember model structure for membership checks
- Pattern for group ownership/membership validation

**Patterns to Reuse:**
- Service function handles business logic, router handles HTTP concerns
- Always verify group membership before group-scoped operations
- Use `model_validate` for converting between SQLModel types
- TanStack mutations with optimistic updates and cache invalidation

### Git Intelligence

**Recent Commits:**
- `bff8605` - feat: Complete Story 2.4 - Dashboard with Net Balances + Epic 2 Complete
- `f214516` - feat: Complete Story 2.3 - View group members list
- `1d6b5dc` - feat: Complete Story 2.2 - Invite members via deep link

**Commit Message Format:**
```
feat: Complete Story 3.1 - Create expense model and basic entry
```

### Alembic Migration

**CREATE migration (after creating models):**
```bash
docker compose exec backend alembic revision --autogenerate -m "add_expense_and_expense_split_tables"
docker compose exec backend alembic upgrade head
```

**Expected SQL (approximate):**
```sql
CREATE TABLE expense (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES expense_group(id),
    amount DECIMAL(10,2) NOT NULL,
    description VARCHAR(500) NOT NULL,
    payer_id UUID NOT NULL REFERENCES "user"(id),
    created_by UUID NOT NULL REFERENCES "user"(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX ix_expense_group_id ON expense(group_id);
CREATE INDEX ix_expense_payer_id ON expense(payer_id);

CREATE TABLE expense_split (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_id UUID NOT NULL REFERENCES expense(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES "user"(id),
    amount_owed DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    confirmed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX ix_expense_split_expense_id ON expense_split(expense_id);
CREATE INDEX ix_expense_split_user_id ON expense_split(user_id);
```

### Testing Commands

```bash
# Start Docker containers
docker compose up -d

# Generate and run migration
docker compose exec backend alembic revision --autogenerate -m "add_expense_tables"
docker compose exec backend alembic upgrade head

# Run expense tests
docker compose exec backend pytest -v tests/api/routes/test_expenses.py

# Run all backend tests
docker compose exec backend pytest -v

# Test endpoint manually - Create expense
curl -X POST http://localhost:8000/api/v1/expenses/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"group_id": "<uuid>", "amount": 50.00, "description": "Lunch"}'

# Frontend build check
cd cleardues/frontend && npm run build

# Frontend type check
cd cleardues/frontend && npm run typecheck
```

### API Contract

**POST /api/v1/expenses/**
```
// Request
POST /api/v1/expenses/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "group_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 60.00,
  "description": "Dinner at restaurant",
  "payer_id": null  // Optional - defaults to current user
}

// Response 200 OK
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "group_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "60.00",
  "description": "Dinner at restaurant",
  "payer_id": "110e8400-e29b-41d4-a716-446655440001",
  "created_by": "110e8400-e29b-41d4-a716-446655440001",
  "status": "draft",
  "created_at": "2026-01-12T10:30:00Z",
  "updated_at": "2026-01-12T10:30:00Z"
}

// Response 403 Forbidden (not a group member)
{
  "detail": "You must be a member of the group to create expenses"
}

// Response 404 Not Found (invalid group)
{
  "detail": "Group not found"
}

// Response 401 Unauthorized (no token)
{
  "detail": "Not authenticated"
}
```

### Important Notes for Developer

1. **Migration Required**: This story adds new database tables. Run Alembic migration BEFORE testing.

2. **Remove Legacy Items Router**: The current `router.py` has `items_router` from the starter template. Replace it entirely with `expenses_router`.

3. **Decimal vs Float**: Use `Decimal` for amounts in Python (precision), but frontend can use `number` (JS converts correctly).

4. **Status Enum**: Use Python `str, PyEnum` pattern for SQLModel compatibility. The status field stores the string value.

5. **Two User References**: `payer_id` = who paid, `created_by` = who entered. Both reference User table but serve different purposes.

6. **ExpenseSplit Table**: Create the table now even though splits are added in Stories 3.5-3.8. This avoids a migration later.

7. **utc_now Import**: Import from `app.features.auth.models` where it's already defined.

8. **Router Registration**: Don't forget to add the router to `api/main.py` - common miss!

9. **Relationship FK Disambiguation**: Expense has TWO foreign keys to User. Use `sa_relationship_kwargs` to disambiguate.

### Epic 3 Context

This is Story 1 of 8 in Epic 3 (Smart Expense Entry):
- **3.1** (this) - Create expense model and basic entry
- 3.2 - Natural language input interface
- 3.3 - AI parsing service integration
- 3.4 - Manual override of parsed data
- 3.5 - Split logic - equal split
- 3.6 - Split logic - unequal amounts
- 3.7 - Split logic - percentage split
- 3.8 - Exclude members from expense

**Dependencies:** All subsequent stories depend on this model.

### References

- [Source: epics.md - Story 3.1](../_bmad-output/planning-artifacts/epics.md#story-31-create-expense-model-and-basic-entry)
- [Source: architecture.md - Data Architecture](../_bmad-output/planning-artifacts/architecture.md#data-architecture)
- [Source: architecture.md - API Patterns](../_bmad-output/planning-artifacts/architecture.md#api--communication-patterns)
- [Source: prd.md - FR4-FR8](../_bmad-output/planning-artifacts/prd.md#expense-input--processing)
- [Existing Code: features/groups/models.py](../../cleardues/backend/app/features/groups/models.py)
- [Existing Code: features/expenses/models.py](../../cleardues/backend/app/features/expenses/models.py) (placeholder)
- [Previous Story: 2-4-dashboard-with-net-balances.md](./2-4-dashboard-with-net-balances.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Implementation proceeded without blocking issues.

### Completion Notes List

- Implemented Expense and ExpenseSplit database models with proper foreign key relationships
- Used `str, PyEnum` pattern for status enums for SQLModel compatibility
- Created manual Alembic migration (e8f9a0b1c2d3) for expense and expense_split tables
- Replaced legacy items_router with expenses_router - deleted test_items.py as items endpoint no longer exists
- Backend tests: 10 new expense tests, 117 total tests passing (excluding removed items tests)
- Frontend uses shadcn/ui components (Button, Input, Label) for consistent styling
- ExpenseForm component is a basic form - group selector will be enhanced in future stories

### Senior Developer Review (AI)

**Review Date:** 2026-01-12
**Reviewer:** Claude Opus 4.5 (Adversarial Code Review)
**Outcome:** APPROVED with fixes applied

**Issues Found & Fixed:**
1. **[MEDIUM] Stale comment in main.py** - Changed "items routes (temporary)" to "expense management routes"
2. **[MEDIUM] Missing test for payer validation** - Added `test_create_expense_with_non_member_payer_returns_400` (now 11 tests)
3. **[MEDIUM] Redundant router pattern** - Simplified router.py to use single `router` with prefix (consistent with groups/auth routers)

**AC Clarifications (Not Bugs):**
- AC #5: Story Dev Notes specify singular table name (`expense`), AC says plural (`expenses`). Implementation follows Dev Notes - singular is valid convention.
- AC #7: Invalid group returns 404 (not 403). This is correct RESTful behavior - 404 for non-existent resources.

**Final Test Results:** 118 tests passing, 0 failures

### Change Log

- 2026-01-12: Code review complete - 3 MEDIUM issues fixed, status updated to done
- 2026-01-12: Story 3.1 implementation complete (Tasks 1-9)

### File List

**Backend - New/Modified:**
- cleardues/backend/app/features/expenses/models.py (MODIFIED - added Expense, ExpenseSplit, schemas)
- cleardues/backend/app/features/expenses/service.py (MODIFIED - added create_expense, is_user_group_member)
- cleardues/backend/app/features/expenses/router.py (MODIFIED - replaced items_router with expenses_router)
- cleardues/backend/app/alembic/versions/e8f9a0b1c2d3_add_expense_and_expense_split.py (NEW - migration)
- cleardues/backend/tests/api/routes/test_expenses.py (NEW - 11 tests, including payer validation test added during review)

**Backend - Deleted:**
- cleardues/backend/tests/api/routes/test_items.py (DELETED - legacy items tests)

**Frontend - New/Modified:**
- cleardues/frontend/src/features/expenses/types.ts (NEW)
- cleardues/frontend/src/features/expenses/api/expenses.ts (NEW)
- cleardues/frontend/src/features/expenses/api/index.ts (NEW)
- cleardues/frontend/src/features/expenses/components/ExpenseForm.tsx (NEW)
- cleardues/frontend/src/features/expenses/components/index.ts (NEW)
- cleardues/frontend/src/features/expenses/index.ts (MODIFIED - added exports)

