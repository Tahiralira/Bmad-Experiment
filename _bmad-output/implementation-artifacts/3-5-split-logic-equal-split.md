# Story 3.5: Split Logic - Equal Split

Status: done

## Story

As a **expense creator**,
I want to split an expense equally among all group members,
So that everyone pays their fair share automatically.

## Acceptance Criteria

1. **Given** I have created an expense with an amount
   **When** I select "Equal Split" option
   **Then** the expense is divided equally among all active group members

2. **And** a `expense_splits` table stores the split: `{expense_id, user_id, amount_owed}`

3. **And** each member's owed amount = total_amount / number_of_members

4. **And** the split is calculated server-side for accuracy

5. **And** the API call: `PUT /api/v1/expenses/{expense_id}/split` with `{type: "equal"}`

6. **Given** the split type selector is displayed
   **When** I select the Equal split card
   **Then** the card shows three equal horizontal bars icon

7. **And** the selected card has teal border + tinted background

8. **And** member chips display below with toggle include/exclude capability

9. **Given** I have created an expense and am setting the split
   **When** I view the split options
   **Then** I see visual cards for Equal, Unequal, Percentage, Shares split types

10. **And** Equal split is selected by default

11. **And** I can tap any card to select that split type

12. **Given** Equal split is selected
   **When** I view the member list
   **Then** I see all group members displayed as chips with avatars

13. **And** I can tap a chip to toggle include/exclude for that member

14. **And** excluded members are grayed out with struck-through name

15. **And** the split amounts recalculate automatically when members are excluded

16. **Given** I am viewing split amounts for Equal split
   **When** a member is excluded
   **Then** the amount per person = total_amount / (number_of_members - excluded_count)

17. **And** the amounts are displayed using the BalanceDisplay component with "Rs" prefix

18. **Given** I have selected the split type and member exclusions
   **When** I confirm the expense
   **Then** the split is saved to the `expense_splits` table

19. **And** each included member has a record with their calculated amount_owed

20. **And** excluded members have no records in expense_splits

21. **Given** the split calculation happens on the backend
   **When** I request an equal split
   **Then** the server calculates amounts using decimal.Decimal for accuracy

22. **And** amounts are rounded to 2 decimal places

23. **And** if rounding causes a penny mismatch, the payer absorbs the difference

24. **Given** I am editing an existing expense's split
   **When** I change from Unequal to Equal split
   **Then** the system recalculates equal amounts for all included members

25. **And** existing split records are replaced with new equal split records

## Tasks / Subtasks

- [x] Task 1: Create ExpenseSplit Model and Table (AC: #2, #4, #21, #22)
  - [x] Create `backend/app/features/expenses/models.py` ExpenseSplit model
  - [x] Add fields: id, expense_id, user_id, amount_owed, created_at
  - [x] Add relationship: ExpenseSplit → Expense (many-to-one)
  - [x] Add relationship: ExpenseSplit → User (many-to-one)
  - [x] Use Decimal for amount_owed with 2 decimal places
  - [x] Add unique constraint: (expense_id, user_id) - one split per user per expense
  - [x] Create Alembic migration for expense_splits table

- [x] Task 2: Backend Equal Split Calculation (AC: #3, #4, #21, #22, #23)
  - [x] Create `backend/app/features/expenses/service.py` calculate_equal_split() function
  - [x] Accept parameters: expense_id, total_amount, member_ids, excluded_user_ids=[]
  - [x] Calculate: amount_per_person = total_amount / (member_count - excluded_count)
  - [x] Use Python Decimal for precise division
  - [x] Handle rounding: round to 2 decimal places
  - [x] Handle penny mismatch: subtract remainder from payer's share
  - [x] Return list of {user_id, amount_owed} for included members

- [x] Task 3: Backend Split API Endpoint (AC: #5, #24, #25)
  - [x] Create `PUT /api/v1/expenses/{expense_id}/split` endpoint
  - [x] Accept request body: {type: "equal", excluded_user_ids: string[]}
  - [x] Validate: expense exists, user is expense creator
  - [x] Validate: type is "equal"
  - [x] Call calculate_equal_split() from service
  - [x] Delete existing splits for this expense
  - [x] Create new ExpenseSplit records
  - [x] Return 200 with updated split data
  - [x] Add error handling for invalid expense_id, insufficient members

- [x] Task 4: Frontend Split Types Enum (AC: #9, #10, #11)
  - [x] Create `frontend/src/features/expenses/types.ts` SplitType enum
  - [x] Values: "equal", "unequal", "percentage", "shares"
  - [x] Create SplitTypeOption interface for UI display
  - [x] Add split type labels and icons

- [x] Task 5: Frontend SplitPicker Component (AC: #6, #7, #9, #10, #11)
  - [x] Create `frontend/src/features/expenses/components/SplitPicker.tsx`
  - [x] Display 4 visual cards: Equal, Unequal, Percentage, Shares
  - [x] Equal split: three equal horizontal bars icon (lucide: equal-icon)
  - [x] Unequal split: three bars of different lengths icon
  - [x] Percentage split: "%" symbol with example percentages icon
  - [x] Shares split: stacked squares representing share units
  - [x] Selected card: teal (action) border + tinted background
  - [x] Default selection: Equal split
  - [x] On tap: update selected split type state
  - [x] Disable non-equal cards for this story (show "coming soon" tooltip)

- [x] Task 6: Frontend MemberChips Component (AC: #8, #13, #14, #15)
  - [x] Create `frontend/src/features/expenses/components/MemberChips.tsx`
  - [x] Accept props: members, included_members (Set), onToggleInclude
  - [x] Display each member as chip: avatar + name
  - [x] Included members: full color avatar, teal checkmark icon
  - [x] Excluded members: grayscale avatar, struck-through name, muted X icon
  - [x] On tap: toggle include/exclude status
  - [x] Maintain group context - show who's out, not just who's in
  - [x] Use Avatar component from shadcn/ui

- [x] Task 7: Frontend Equal Split Amounts Display (AC: #16, #17)
  - [x] Create `frontend/src/features/expenses/components/SplitAmountsDisplay.tsx`
  - [x] Calculate amount_per_person for Equal split
  - [x] Display each included member with their amount
  - [x] Use BalanceDisplay component for currency formatting
  - [x] Format: "Rs 1,500" with comma separators
  - [x] Recalculate automatically when member exclusion changes
  - [x] Show "per person" label for clarity

- [x] Task 8: Frontend Split State Management (AC: #15, #16, #19, #20)
  - [x] Create `frontend/src/features/expenses/hooks/useSplitState.ts`
  - [x] Manage state: split_type, excluded_members (Set)
  - [x] Calculate split amounts based on type and exclusions
  - [x] For Equal split: amount = total / (members - excluded)
  - [x] Return: split_amounts (Map<user_id, amount>)
  - [x] Handle rounding mismatch for display
  - [x] Validate: at least 2 members included

- [x] Task 9: Frontend Split Mutation Hook (AC: #18, #19, #20)
  - [x] Create `frontend/src/features/expenses/api/useUpdateExpenseSplit.ts`
  - [x] Use TanStack Query mutation
  - [x] Call `PUT /api/v1/expenses/{expense_id}/split`
  - [x] Send: {type: "equal", excluded_user_ids: string[]}
  - [x] On success: invalidate queries for expense and group balances
  - [x] On error: show toast notification
  - [x] Return loading, error, mutate states

- [x] Task 10: Integrate SplitPicker with EditableExpensePreview (AC: #9, #10, #11)
  - [x] Modify `frontend/src/features/expenses/components/EditableExpensePreview.tsx`
  - [x] Add "complex edit mode" state expansion (deferred from Story 3.4)
  - [x] Add "Edit Details" button to expand modal
  - [x] Show SplitPicker component in expanded mode
  - [x] Show MemberChips component below SplitPicker
  - [x] Show SplitAmountsDisplay with calculated amounts
  - [x] Add "Done" button to collapse back to simple mode
  - [x] Maintain edited state across mode switches

- [x] Task 11: Frontend Validation (AC: #23, #24)
  - [x] Validate: at least 2 members must be included
  - [x] If only 1 member: show error "At least 2 members required for split"
  - [x] Validate: split amounts sum to total (within 0.01 tolerance)
  - [x] Disable confirm button when validation fails
  - [x] Show inline error message below validation failures

- [x] Task 12: Backend Testing (AC: #3, #4, #21, #22, #23)
  - [x] Test calculate_equal_split() with various amounts
  - [x] Test rounding: 100 / 3 = 33.33 each, payer absorbs 0.01
  - [x] Test with excluded members
  - [x] Test edge cases: 2 members, all members, 1 member excluded
  - [x] Test API endpoint with valid requests
  - [x] Test API validation: non-existent expense, non-creator user

- [x] Task 13: Frontend Testing (AC: #1, #13, #14, #15, #16)
  - [x] Test SplitPicker: select Equal, verify visual state
  - [x] Test MemberChips: tap to toggle include/exclude
  - [x] Test split recalculation when member excluded
  - [x] Test validation: 1 member shows error
  - [x] Test confirm action: API call succeeds, modal closes
  - [x] Test currency formatting with BalanceDisplay

## Dev Notes

### CRITICAL: This Story Implements Split Logic Foundation

Story 3.5 is the **first of four split logic stories** (3.5-3.8). This story establishes the foundation for expense splitting:
- Creates the `expense_splits` table (backend data model)
- Implements equal split calculation (business logic)
- Creates the split picker UI component (user interface)
- Enables member exclusion (user control)
- Sets patterns for the remaining split types (unequal, percentage, shares)

**Get this foundation right** - the next three stories will build on these patterns.

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
Backend:
├── backend/app/features/expenses/
│   ├── models.py                    # MODIFY: Add ExpenseSplit model
│   ├── service.py                   # MODIFY: Add calculate_equal_split()
│   └── router.py                    # MODIFY: Add PUT /expenses/{id}/split endpoint
├── alembic/versions/
│   └── XXX_create_expense_splits.py # CREATE: Migration for expense_splits table

Frontend:
├── frontend/src/features/expenses/
│   ├── components/
│   │   ├── SplitPicker.tsx          # CREATE: Visual split type selector
│   │   ├── MemberChips.tsx          # CREATE: Member include/exclude chips
│   │   ├── SplitAmountsDisplay.tsx  # CREATE: Display calculated amounts
│   │   └── EditableExpensePreview.tsx  # MODIFY: Add complex edit mode
│   ├── hooks/
│   │   ├── useSplitState.ts         # CREATE: Split state management
│   │   └── useUpdateExpenseSplit.ts # CREATE: Split mutation hook
│   ├── api/
│   │   └── expenseApi.ts            # MODIFY: Add updateSplit() function
│   └── types.ts                     # MODIFY: Add split types

Shared UI:
└── frontend/src/components/ui/
    └── avatar.tsx                   # USE: For member chips (shadcn/ui)
```

**Naming Conventions (MANDATORY):**
- Backend models: `PascalCase` (e.g., `ExpenseSplit`)
- Backend tables: `snake_case` (e.g., `expense_splits`)
- Backend columns: `snake_case` (e.g., `amount_owed`, `expense_id`)
- Backend functions: `snake_case` (e.g., `calculate_equal_split`)
- Frontend components: `PascalCase` (e.g., `SplitPicker`, `MemberChips`)
- Frontend hooks: `camelCase` starting with `use` (e.g., `useSplitState`)
- Frontend types/interfaces: `PascalCase` (e.g., `SplitType`, `SplitState`)
- API endpoints: kebab-case (e.g., `/api/v1/expenses/{expense_id}/split`)

### Technical Requirements

**Backend - ExpenseSplit Model:**
```python
# backend/app/features/expenses/models.py
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from decimal import Decimal
from datetime import datetime
import uuid

class ExpenseSplit(SQLModel, table=True):
    __tablename__ = "expense_splits"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    expense_id: uuid.UUID = Field(foreign_key="expenses.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    amount_owed: Decimal = Field(max_digits=10, decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    expense: "Expense" = Relationship(back_populates="splits")
    user: "User" = Relationship(back_populates="expense_splits")

    __table_args__ = (
        # Unique constraint: one split per user per expense
        sa.UniqueConstraint("expense_id", "user_id", name="uq_expense_user_split"),
    )

# Update Expense model to include splits relationship
class Expense(SQLModel, table=True):
    # ... existing fields ...

    # Add this relationship
    splits: list[ExpenseSplit] = Relationship(back_populates="expense")
```

**Backend - Equal Split Calculation:**
```python
# backend/app/features/expenses/service.py
from decimal import Decimal, ROUND_HALF_UP
from typing import List
from uuid import UUID

def calculate_equal_split(
    total_amount: Decimal,
    member_ids: List[UUID],
    excluded_user_ids: List[UUID] = [],
    payer_id: UUID = None
) -> List[dict]:
    """
    Calculate equal split amounts among group members.

    Args:
        total_amount: Total expense amount
        member_ids: All group member IDs
        excluded_user_ids: Members to exclude from split
        payer_id: The expense creator (absorbs rounding difference)

    Returns:
        List of {user_id, amount_owed} for included members
    """
    # Filter out excluded members
    included_members = [m for m in member_ids if m not in excluded_user_ids]

    if len(included_members) < 2:
        raise ValueError("At least 2 members required for split")

    # Calculate equal amount
    amount_per_person = total_amount / Decimal(len(included_members))

    # Round to 2 decimal places
    amount_rounded = amount_per_person.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Calculate total after rounding
    rounded_total = amount_rounded * Decimal(len(included_members))

    # Handle penny mismatch: payer absorbs difference
    difference = total_amount - rounded_total
    splits = []

    for user_id in included_members:
        amount = amount_rounded
        # Payer absorbs rounding difference
        if user_id == payer_id:
            amount += difference
        splits.append({
            "user_id": user_id,
            "amount_owed": amount
        })

    return splits
```

**Backend - Split API Endpoint:**
```python
# backend/app/features/expenses/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from uuid import UUID

from app.features.expenses.service import calculate_equal_split
from app.features.expenses.models import ExpenseSplit, Expense
from app.core.db import get_db

router = APIRouter()

@router.put("/expenses/{expense_id}/split")
def update_expense_split(
    expense_id: UUID,
    split_data: dict,  # {"type": "equal", "excluded_user_ids": []}
    session: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)  # Your auth dependency
):
    # Get expense
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    # Verify user is expense creator
    if expense.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only expense creator can modify split"
        )

    split_type = split_data.get("type")
    excluded_ids = split_data.get("excluded_user_ids", [])

    if split_type == "equal":
        # Get group members (this would come from your group service)
        member_ids = [m.id for m in expense.group.members]

        # Calculate split
        splits_data = calculate_equal_split(
            total_amount=expense.amount,
            member_ids=member_ids,
            excluded_user_ids=excluded_ids,
            payer_id=expense.payer_id
        )

        # Delete existing splits
        session.query(ExpenseSplit).filter(
            ExpenseSplit.expense_id == expense_id
        ).delete()

        # Create new splits
        for split in splits_data:
            expense_split = ExpenseSplit(
                expense_id=expense_id,
                user_id=split["user_id"],
                amount_owed=split["amount_owed"]
            )
            session.add(expense_split)

        session.commit()

        return {
            "expense_id": expense_id,
            "split_type": "equal",
            "splits": splits_data
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Split type '{split_type}' not yet implemented"
        )
```

**Frontend - Split Types:**
```typescript
// frontend/src/features/expenses/types.ts
export enum SplitType {
  EQUAL = "equal",
  UNEQUAL = "unequal",
  PERCENTAGE = "percentage",
  SHARES = "shares"
}

export interface SplitTypeOption {
  type: SplitType
  label: string
  icon: string // Lucide icon name
  disabled?: boolean
  disabledReason?: string
}

export const SPLIT_TYPE_OPTIONS: SplitTypeOption[] = [
  {
    type: SplitType.EQUAL,
    label: "Equal",
    icon: "equal"
  },
  {
    type: SplitType.UNEQUAL,
    label: "Unequal",
    icon: "bar-chart-2",
    disabled: true,
    disabledReason: "Coming in Story 3.6"
  },
  {
    type: SplitType.PERCENTAGE,
    label: "Percentage",
    icon: "percent",
    disabled: true,
    disabledReason: "Coming in Story 3.7"
  },
  {
    type: SplitType.SHARES,
    label: "Shares",
    icon: "squares-3-by-3",
    disabled: true,
    disabledReason: "Coming in Story 3.8"
  }
]

export interface SplitState {
  type: SplitType
  excludedMembers: Set<string>
  amounts: Map<string, number> // user_id -> amount_owed
}

export interface EqualSplitRequest {
  type: "equal"
  excluded_user_ids: string[]
}
```

**Frontend - SplitPicker Component:**
```typescript
// frontend/src/features/expenses/components/SplitPicker.tsx
import { SplitType, SPLIT_TYPE_OPTIONS } from '../types'
import { motion } from 'framer-motion'
import * as Icons from 'lucide-react'
import { cn } from '@/lib/utils'

interface SplitPickerProps {
  selectedType: SplitType
  onSelectType: (type: SplitType) => void
}

export function SplitPicker({ selectedType, onSelectType }: SplitPickerProps) {
  return (
    <div className="split-picker-container">
      <label className="text-sm font-medium text-primary">Split Type</label>

      <div className="grid grid-cols-4 gap-3 mt-2">
        {SPLIT_TYPE_OPTIONS.map((option) => {
          const Icon = Icons[option.icon as keyof typeof Icons]
          const isSelected = selectedType === option.type

          return (
            <motion.button
              key={option.type}
              onClick={() => !option.disabled && onSelectType(option.type)}
              disabled={option.disabled}
              className={cn(
                "split-type-card",
                "relative flex flex-col items-center justify-center",
                "p-4 rounded-lg border-2 transition-all",
                "min-h-[100px]",
                isSelected && "border-action bg-action/10",
                !isSelected && "border-border bg-surface",
                option.disabled && "opacity-50 cursor-not-allowed"
              )}
              whileHover={!option.disabled ? { scale: 1.02 } : undefined}
              whileTap={!option.disabled ? { scale: 0.98 } : undefined}
            >
              {Icon && <Icon className="w-6 h-6 mb-2" />}
              <span className="text-xs font-medium">{option.label}</span>

              {option.disabled && (
                <div className="absolute inset-0 flex items-center justify-center bg-surface/80 rounded-lg">
                  <span className="text-[10px] text-muted text-center px-1">
                    {option.disabledReason}
                  </span>
                </div>
              )}
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}
```

**Frontend - MemberChips Component:**
```typescript
// frontend/src/features/expenses/components/MemberChips.tsx
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Check, X } from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface GroupMember {
  id: string
  full_name: string
  email?: string
  avatar_url?: string
}

interface MemberChipsProps {
  members: GroupMember[]
  includedMembers: Set<string>
  onToggleInclude: (memberId: string) => void
}

export function MemberChips({ members, includedMembers, onToggleInclude }: MemberChipsProps) {
  return (
    <div className="member-chips-container">
      <label className="text-sm font-medium text-primary">
        Split Between ({members.length - (members.length - includedMembers.size)} selected)
      </label>

      <div className="flex flex-wrap gap-2 mt-2">
        {members.map((member) => {
          const isIncluded = includedMembers.has(member.id)
          const initials = member.full_name
            .split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2)

          return (
            <motion.button
              key={member.id}
              onClick={() => onToggleInclude(member.id)}
              className={cn(
                "member-chip",
                "flex items-center gap-2 px-3 py-2 rounded-full border",
                "transition-all",
                isIncluded
                  ? "border-action bg-action/5"
                  : "border-border bg-surface opacity-60"
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Avatar className="w-6 h-6">
                {member.avatar_url && <AvatarImage src={member.avatar_url} />}
                <AvatarFallback className={cn(
                  "text-xs",
                  isIncluded ? "bg-action text-white" : "bg-muted text-muted-foreground"
                )}>
                  {initials}
                </AvatarFallback>
              </Avatar>

              <span className={cn(
                "text-sm font-medium",
                isIncluded ? "text-primary" : "text-muted line-through"
              )}>
                {member.full_name}
              </span>

              <div className="w-4 h-4">
                {isIncluded ? (
                  <Check className="w-4 h-4 text-action" />
                ) : (
                  <X className="w-4 h-4 text-muted-foreground" />
                )}
              </div>
            </motion.button>
          )
        })}
      </div>

      <p className="text-xs text-muted mt-2">
        Tap to toggle include/exclude
      </p>
    </div>
  )
}
```

**Frontend - useSplitState Hook:**
```typescript
// frontend/src/features/expenses/hooks/useSplitState.ts
import { useState, useMemo, useCallback } from 'react'
import { SplitType } from '../types'
import type { GroupMember } from '@/features/groups/types'

interface UseSplitStateProps {
  totalAmount: number
  members: GroupMember[]
  initialType?: SplitType
  payerId?: string
}

export function useSplitState({
  totalAmount,
  members,
  initialType = SplitType.EQUAL,
  payerId
}: UseSplitStateProps) {
  const [splitType, setSplitType] = useState<SplitType>(initialType)
  const [excludedMembers, setExcludedMembers] = useState<Set<string>>(new Set())

  // Calculate split amounts based on type and exclusions
  const splitAmounts = useMemo(() => {
    const includedMembers = members.filter(m => !excludedMembers.has(m.id))

    if (includedMembers.length < 2) {
      return new Map<string, number>()
    }

    if (splitType === SplitType.EQUAL) {
      // Equal split calculation
      const amountPerPerson = totalAmount / includedMembers.length

      const amounts = new Map<string, number>()
      let runningTotal = 0

      includedMembers.forEach((member, index) => {
        let amount = Math.round(amountPerPerson * 100) / 100

        // Payer absorbs rounding difference
        if (member.id === payerId && index === includedMembers.length - 1) {
          amount = Math.round((totalAmount - runningTotal) * 100) / 100
        }

        amounts.set(member.id, amount)
        runningTotal += amount
      })

      return amounts
    }

    // Other split types will be implemented in future stories
    return new Map<string, number>()
  }, [splitType, totalAmount, members, excludedMembers, payerId])

  const toggleMemberExclusion = useCallback((memberId: string) => {
    setExcludedMembers(prev => {
      const newSet = new Set(prev)
      if (newSet.has(memberId)) {
        newSet.delete(memberId)
      } else {
        newSet.add(memberId)
      }
      return newSet
    })
  }, [])

  const isValid = useMemo(() => {
    const includedCount = members.length - excludedMembers.size
    return includedCount >= 2
  }, [members.length, excludedMembers.size])

  return {
    splitType,
    setSplitType,
    excludedMembers,
    toggleMemberExclusion,
    splitAmounts,
    isValid
  }
}
```

### Project Structure Notes

**This story CREATES:**
- `backend/app/features/expenses/models.py` (ExpenseSplit model, relationship to Expense)
- `alembic/versions/XXX_create_expense_splits.py` (Migration for expense_splits table)
- `backend/app/features/expenses/service.py` (calculate_equal_split function)
- `backend/app/features/expenses/router.py` (PUT /expenses/{id}/split endpoint)
- `frontend/src/features/expenses/components/SplitPicker.tsx`
- `frontend/src/features/expenses/components/MemberChips.tsx`
- `frontend/src/features/expenses/components/SplitAmountsDisplay.tsx`
- `frontend/src/features/expenses/hooks/useSplitState.ts`
- `frontend/src/features/expenses/api/useUpdateExpenseSplit.ts`

**This story MODIFIES:**
- `backend/app/features/expenses/models.py` (Add splits relationship to Expense)
- `frontend/src/features/expenses/components/EditableExpensePreview.tsx` (Add complex edit mode)
- `frontend/src/features/expenses/types.ts` (Add split types)

### Previous Story Intelligence

**From Story 3.1 (Create Expense Model and Basic Entry):**
- Expense model exists with `status`, `amount`, `description`, `payer_id`, `group_id`
- Expense creation API: `POST /api/v1/expenses`
- **Integration Point:** Add splits relationship to Expense model

**From Story 3.4 (Manual Override of Parsed Data):**
- EditableExpensePreview has "complex edit mode" skeleton (deferred)
- Inline editing for amount, description, payer exists
- **Integration Point:** Expand complex edit mode to show SplitPicker and MemberChips

**From Story 2.5 (UX Foundation & Design System):**
- Design system tokens established (action color for selected state)
- Avatar component from shadcn/ui for member display
- BalanceDisplay component for currency formatting
- **Apply:** Use design tokens for all styling, maintain visual consistency

**From Epic 2 Stories (Groups & Dashboard):**
- Group members can be fetched via group API
- Member data structure includes: id, full_name, email, avatar_url
- **Integration Point:** Fetch group members for MemberChips display

### Git Intelligence

**Recent Commits (Analysis):**
- `e221eac` - fix: Code review fixes for Story 3.4 - Manual Override of Parsed Data
  - **Insight:** EditableExpensePreview stable, ready to extend with split logic
- `4cdce04` - feat: Complete Story 3.3 - AI Parsing Service Integration
  - **Insight:** SSE streaming stable, can use similar patterns for real-time updates

**Commit Message Format:**
```
feat: Complete Story 3.5 - Split logic - equal split
```

**Library Versions:**
- SQLModel (backend ORM)
- Python Decimal for precise financial calculations
- Framer Motion (frontend animations)
- TanStack Query (API mutations)
- shadcn/ui (Avatar, Card components)

### Testing Requirements

**Backend Tests (Pytest):**
```python
# backend/app/features/expenses/tests/test_split_service.py
import pytest
from decimal import Decimal
from app.features.expenses.service import calculate_equal_split

def test_equal_split_exact_division():
    """Test equal split when amount divides evenly"""
    splits = calculate_equal_split(
        total_amount=Decimal("100.00"),
        member_ids=["user1", "user2", "user3", "user4"],
        excluded_user_ids=[],
        payer_id="user1"
    )

    assert len(splits) == 4
    assert all(s["amount_owed"] == Decimal("25.00") for s in splits)

def test_equal_split_with_rounding():
    """Test equal split with rounding mismatch"""
    splits = calculate_equal_split(
        total_amount=Decimal("100.00"),
        member_ids=["user1", "user2", "user3"],
        excluded_user_ids=[],
        payer_id="user1"
    )

    # 100 / 3 = 33.33 each, payer absorbs 0.01
    assert splits[0]["amount_owed"] == Decimal("33.34")  # Payer
    assert splits[1]["amount_owed"] == Decimal("33.33")
    assert splits[2]["amount_owed"] == Decimal("33.33")

def test_equal_split_with_excluded_members():
    """Test equal split with member exclusions"""
    splits = calculate_equal_split(
        total_amount=Decimal("100.00"),
        member_ids=["user1", "user2", "user3", "user4"],
        excluded_user_ids=["user3"],
        payer_id="user1"
    )

    assert len(splits) == 3
    assert all(s["amount_owed"] == Decimal("33.33")[:5] for s in splits)

def test_equal_split_minimum_members():
    """Test that at least 2 members are required"""
    with pytest.raises(ValueError, match="At least 2 members"):
        calculate_equal_split(
            total_amount=Decimal("100.00"),
            member_ids=["user1"],
            excluded_user_ids=[],
            payer_id="user1"
        )
```

**Frontend Tests (Vitest):**
```typescript
// SplitPicker.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { SplitPicker } from './SplitPicker'
import { SplitType } from '../types'

describe('SplitPicker', () => {
  test('renders all 4 split type cards', () => {
    render(<SplitPicker selectedType={SplitType.EQUAL} onSelectType={() => {}} />)
    expect(screen.getByText('Equal')).toBeInTheDocument()
    expect(screen.getByText('Unequal')).toBeInTheDocument()
    expect(screen.getByText('Percentage')).toBeInTheDocument()
    expect(screen.getByText('Shares')).toBeInTheDocument()
  })

  test('selects Equal split by default', () => {
    const onSelectType = vi.fn()
    render(<SplitPicker selectedType={SplitType.EQUAL} onSelectType={onSelectType} />)

    const equalCard = screen.getByText('Equal').closest('button')
    expect(equalCard).toHaveClass('border-action')
  })

  test('disabled cards show coming soon message', () => {
    render(<SplitPicker selectedType={SplitType.EQUAL} onSelectType={() => {}} />)

    expect(screen.getByText('Coming in Story 3.6')).toBeInTheDocument()
  })
})

// MemberChips.test.tsx
describe('MemberChips', () => {
  const mockMembers = [
    { id: '1', full_name: 'Alex', email: 'alex@example.com' },
    { id: '2', full_name: 'Sam', email: 'sam@example.com' },
    { id: '3', full_name: 'Tom', email: 'tom@example.com' }
  ]

  test('toggles member exclusion on tap', () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(['1', '2', '3'])

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    fireEvent.click(screen.getByText('Alex'))
    expect(onToggle).toHaveBeenCalledWith('1')
  })

  test('shows excluded members with strikethrough', () => {
    const onToggle = vi.fn()
    const includedMembers = new Set(['1', '3']) // Sam excluded

    render(
      <MemberChips
        members={mockMembers}
        includedMembers={includedMembers}
        onToggleInclude={onToggle}
      />
    )

    const samChip = screen.getByText('Sam')
    expect(samChip).toHaveClass('line-through')
  })
})

// useSplitState.test.ts
import { renderHook, act } from '@testing-library/react'
import { useSplitState } from './useSplitState'

describe('useSplitState', () => {
  test('calculates equal split amounts correctly', () => {
    const members = [
      { id: '1', full_name: 'Alex' },
      { id: '2', full_name: 'Sam' },
      { id: '3', full_name: 'Tom' }
    ]

    const { result } = renderHook(() =>
      useSplitState({ totalAmount: 150, members, payerId: '1' })
    )

    expect(result.current.splitAmounts.get('1')).toBe(50)
    expect(result.current.splitAmounts.get('2')).toBe(50)
    expect(result.current.splitAmounts.get('3')).toBe(50)
  })

  test('recalculates when member is excluded', () => {
    const members = [
      { id: '1', full_name: 'Alex' },
      { id: '2', full_name: 'Sam' },
      { id: '3', full_name: 'Tom' }
    ]

    const { result } = renderHook(() =>
      useSplitState({ totalAmount: 150, members, payerId: '1' })
    )

    act(() => {
      result.current.toggleMemberExclusion('3')
    })

    // 150 / 2 = 75 each
    expect(result.current.splitAmounts.get('1')).toBe(75)
    expect(result.current.splitAmounts.get('2')).toBe(75)
    expect(result.current.splitAmounts.has('3')).toBe(false)
  })

  test('validates minimum 2 members', () => {
    const members = [
      { id: '1', full_name: 'Alex' },
      { id: '2', full_name: 'Sam' }
    ]

    const { result } = renderHook(() =>
      useSplitState({ totalAmount: 100, members, payerId: '1' })
    )

    expect(result.current.isValid).toBe(true)

    act(() => {
      result.current.toggleMemberExclusion('2')
    })

    expect(result.current.isValid).toBe(false)
  })
})
```

### API Contract

**Request:**
```typescript
PUT /api/v1/expenses/{expense_id}/split

{
  "type": "equal",
  "excluded_user_ids": ["user-3", "user-4"]  // Optional
}
```

**Response:**
```typescript
{
  "expense_id": "uuid",
  "split_type": "equal",
  "splits": [
    {
      "user_id": "user-1",
      "amount_owed": 33.34
    },
    {
      "user_id": "user-2",
      "amount_owed": 33.33
    }
  ]
}
```

### Important Notes for Developer

1. **Backend Decimal Precision:** Always use Python's `Decimal` for financial calculations. Never use float for money.

2. **Rounding Strategy:** Use `ROUND_HALF_UP` for fair rounding. The payer absorbs the penny difference to ensure splits sum to total.

3. **Unique Constraint:** The expense_splits table must have unique constraint on (expense_id, user_id) to prevent duplicate splits.

4. **Frontend Validation:** Disable confirm button when fewer than 2 members are included. Show inline error message.

5. **Member Exclusion:** Excluded members should stay visible in MemberChips with struck-through name (maintains group context).

6. **Split Type Cards:** Only Equal split is enabled in this story. Other cards should show "coming soon" tooltip when tapped.

7. **Complex Edit Mode:** This story implements the "complex edit mode" that was deferred from Story 3.4. Add "Edit Details" button to EditableExpensePreview.

8. **State Management:** Use TanStack Query's mutation for API calls. Invalidate queries after successful split update.

9. **Design System:** Use `action` color for selected split card (teal border + tinted background). Use `text-muted` for excluded members.

10. **Currency Formatting:** Always use BalanceDisplay component for amounts. Format as "Rs 1,500" with comma separators.

11. **Avatar Fallbacks:** Generate initials from full_name (first letter of first and last name, max 2 chars).

12. **Mobile-First:** Ensure SplitPicker cards are touch-friendly (min 44x44px tap targets). Test on mobile viewport.

13. **Animation Timing:** Keep card selection animations under 200ms. Use Framer Motion `transition={{ duration: 0.2 }}`.

14. **Error Handling:** If split API fails, show error toast and keep modal open. Don't collapse complex edit mode on error.

15. **Success Feedback:** On successful split save, show success toast and collapse complex edit mode back to simple mode.

16. **Test Coverage:** Aim for 80% test coverage. Test rounding, exclusions, validation, edge cases.

17. **Alembic Migration:** Remember to create and run migration for expense_splits table. Use `alembic revision --autogenerate`.

18. **Database Cascade:** Consider cascade delete: if expense is deleted, delete associated splits.

19. **API Authentication:** Use your auth dependency (e.g., `get_current_user_id`) to verify user is logged in.

20. **Creator-Only Restriction:** Only the expense creator (created_by) can modify the split. This aligns with FR9 from PRD.

### Epic 3 Context

This is Story 5 of 8 in Epic 3 (Smart Expense Entry):
- 3.1 - Create expense model and basic entry ✅ DONE
- 3.2 - Natural language input interface ✅ DONE
- 3.3 - AI parsing service integration ✅ DONE
- 3.4 - Manual override of parsed data ✅ DONE
- **3.5 (this)** - Split logic - equal split
- 3.6 - Split logic - unequal amounts (NEXT)
- 3.7 - Split logic - percentage split
- 3.8 - Exclude members from expense

**Dependencies:**
- This story DEPENDS ON: Story 3.1 (Expense model), Story 3.4 (EditableExpensePreview)
- This story ENABLES: Later split stories (3.6-3.8) - they will add other split type implementations

### NFR Compliance

**NFR2 (Load Time):** Keep component render time under 1.5s on 4G.

**Accuracy:** Financial calculations must be precise. Use Decimal type on backend, round to 2 decimals.

### UX Requirements Summary

**From PRD (FR7):** "User can specify split logic: Equal, Unequal, Percentage, or Shares" - This story implements Equal split.

**From UX Design Specification:**
- **Visual Split Picker:** Select split type via visual cards with icons
- **Member Chips:** Toggle include/exclude with visual feedback
- **BalanceDisplay:** Use neutral currency formatting (Rs prefix, no red/green)
- **15-Second Goal:** Equal split should be fast (default selection, tap to exclude)

### References

- [Source: epics.md - Story 3.5](_bmad-output/planning-artifacts/epics.md#story-35-split-logic---equal-split)
- [Source: architecture.md - Backend Architecture](_bmad-output/planning-artifacts/architecture.md#backend-architecture)
- [Source: prd.md - FR7](_bmad-output/planning-artifacts/prd.md#transaction-logic--workflow)
- [Source: ux-design-specification.md - Smart Input](_bmad-output/planning-artifacts/ux-design-specification.md#core-experience-smart-input-with-personality)
- [Previous Story: 3-4-manual-override-of-parsed-data.md](_bmad-output/implementation-artifacts/3-4-manual-override-of-parsed-data.md)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

N/A - Story creation complete, implementation pending dev-story workflow.

### Completion Notes List

**Story 3.5 Context Creation Complete!**

**Story Summary:**
- **Epic:** Epic 3 - Smart Expense Entry (Story 5 of 8)
- **Title:** Split Logic - Equal Split
- **Status:** ready-for-dev
- **Dependencies:** Story 3.1 (Expense model), Story 3.4 (EditableExpensePreview)

**Key Features:**
1. **Backend Data Model:** ExpenseSplit table with many-to-one relationships to Expense and User
2. **Equal Split Calculation:** Server-side calculation with Decimal precision, rounding handling
3. **Split API:** PUT endpoint to update expense splits
4. **SplitPicker UI:** Visual card selector for split types (Equal enabled, others coming soon)
5. **MemberChips:** Toggle include/exclude with visual feedback (struck-through, grayscale)
6. **SplitAmountsDisplay:** Show calculated amounts per person with BalanceDisplay
7. **Complex Edit Mode:** Expand EditableExpensePreview to show split controls
8. **Validation:** Minimum 2 members, inline errors, disable confirm

**Comprehensive Context Provided:**
- ✅ Epic context with all 8 stories
- ✅ Previous story intelligence (3.1, 3.4)
- ✅ Architecture compliance (file locations, naming conventions)
- ✅ Technical requirements (backend model, calculation, API; frontend components)
- ✅ UX requirements (visual split picker, member chips, currency formatting)
- ✅ Testing requirements (backend unit tests, frontend component tests)
- ✅ API contracts (request/response schemas)
- ✅ NFR compliance (accuracy, load time)
- ✅ 20 detailed developer notes

**Developer Has Everything Needed:**
- Complete backend model (ExpenseSplit with relationships)
- Equal split calculation algorithm with rounding
- API endpoint specification
- Frontend component structure (SplitPicker, MemberChips, SplitAmountsDisplay)
- State management hook (useSplitState)
- Integration points with previous stories
- Testing strategies for backend and frontend
- Design system integration

**Next Steps:**
1. Run `dev-story` workflow to implement Story 3.5
2. Create ExpenseSplit model with unique constraint
3. Implement calculate_equal_split() with Decimal precision
4. Create PUT /expenses/{id}/split API endpoint
5. Build SplitPicker, MemberChips, SplitAmountsDisplay components
6. Integrate with EditableExpensePreview complex edit mode
7. Add validation for minimum 2 members
8. Test rounding, exclusions, edge cases
9. Verify mobile responsiveness
10. Ensure design system token usage

**Ready for Implementation:**
The developer agent now has comprehensive guidance to implement equal split functionality that establishes the foundation for all remaining split logic stories.

### File List

**Story File:**
- _bmad-output/implementation-artifacts/3-5-split-logic-equal-split.md (this file)

**Backend Files to Create:**
- alembic/versions/XXX_create_expense_splits.py (NEW - migration)

**Backend Files to Modify:**
- backend/app/features/expenses/models.py (MODIFY - add ExpenseSplit model, update Expense model)
- backend/app/features/expenses/service.py (MODIFY - add calculate_equal_split())
- backend/app/features/expenses/router.py (MODIFY - add PUT /expenses/{id}/split endpoint)

**Frontend Files to Create:**
- frontend/src/features/expenses/components/SplitPicker.tsx (NEW)
- frontend/src/features/expenses/components/MemberChips.tsx (NEW)
- frontend/src/features/expenses/components/SplitAmountsDisplay.tsx (NEW)
- frontend/src/features/expenses/hooks/useSplitState.ts (NEW)
- frontend/src/features/expenses/api/useUpdateExpenseSplit.ts (NEW)

**Frontend Files to Modify:**
- frontend/src/features/expenses/components/EditableExpensePreview.tsx (MODIFY - add complex edit mode)
- frontend/src/features/expenses/types.ts (MODIFY - add split types)

**Reference Documents:**
- _bmad-output/planning-artifacts/epics.md (Epic 3 stories)
- _bmad-output/planning-artifacts/architecture.md (Architecture patterns)
- _bmad-output/planning-artifacts/prd.md (FR7 - split logic)
- _bmad-output/planning-artifacts/ux-design-specification.md (UX patterns)
- _bmad-output/implementation-artifacts/3-4-manual-override-of-parsed-data.md (Previous story)
- _bmad-output/implementation-artifacts/3-1-create-expense-model-and-basic-entry.md (Expense model)
- _bmad-output/session-context.md (Project context)
- _bmad-output/implementation-artifacts/solution-patterns.yaml (Known issues)
