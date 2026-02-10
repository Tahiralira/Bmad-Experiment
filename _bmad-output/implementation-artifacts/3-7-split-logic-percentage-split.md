# Story 3.7: Split Logic - Percentage Split

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **expense creator**,
I want to split an expense by percentages,
So that I can handle proportional sharing (e.g., 60/40 split).

## Acceptance Criteria

1. **Given** I have created an expense with an amount
   **When** I select "Percentage Split" option
   **Then** I can assign percentages to each member

2. **And** each member's owed amount = (total_amount * their_percentage / 100)

3. **And** the system validates that percentages sum to 100

4. **And** if percentages don't add up to 100, an error is shown

5. **And** amounts are calculated server-side to avoid rounding errors

6. **And** the API call: `PUT /api/v1/expenses/{expense_id}/split` with `{type: "percentage", splits: [{user_id, percentage}]}`

7. **Given** the split type selector is displayed
   **When** I select the Percentage split card
   **Then** the card shows "%" symbol with example percentages icon

8. **And** the selected card has teal border + tinted background

9. **And** the card is no longer disabled (enabled in this story)

10. **Given** Percentage split is selected
    **When** I view the member list
    **Then** percentage input appears next to each member chip

11. **And** I can type percentages (0-100) for each member

12. **Given** I am entering percentages
    **When** I type percentages
    **Then** real-time calculation shows resulting amount for each percentage

13. **And** a visual indicator shows total percentage progress toward 100%

14. **Given** I have entered percentages that don't sum to 100
    **When** I try to confirm
    **Then** the system shows error: "Percentages must sum to 100% (current: X%)"

15. **And** the confirm button is disabled until percentages sum to 100

16. **Given** the percentages sum to 100 exactly
    **When** I confirm the expense
    **Then** the split is saved to the `expense_splits` table

17. **And** each member has a record with their calculated amount_owed

18. **And** the backend calculates amounts using: (total_amount * percentage / 100)

19. **Given** I am editing an existing expense's split
    **When** I change from Equal to Percentage split
    **Then** the system populates percentage inputs with equal distribution (100 / num_members)

20. **And** I can modify individual percentages as needed

## Tasks / Subtasks

- [x] Task 1: Backend Percentage Split Calculation (AC: #2, #3, #5, #18)
  - [x] Create `backend/app/features/expenses/service.py` calculate_percentage_split() function
  - [x] Accept parameters: total_amount, splits: [{user_id, percentage}]
  - [x] Validate: sum of percentages equals 100 (within 0.01 tolerance)
  - [x] Calculate each member's amount: (total_amount * percentage / 100)
  - [x] Handle rounding: distribute remainder to avoid penny loss
  - [x] Return list of {user_id, amount_owed} for all splits
  - [x] Raise ValueError if percentages don't sum to 100

- [x] Task 2: Backend Split API Enhancement (AC: #6, #16, #17)
  - [x] Modify `PUT /api/v1/expenses/{expense_id}/split` endpoint
  - [x] Accept request body for percentage: {type: "percentage", splits: [{user_id, percentage}]}
  - [x] Validate: expense exists, user is expense creator
  - [x] Call calculate_percentage_split() from service
  - [x] Delete existing splits for this expense
  - [x] Create new ExpenseSplit records with calculated amounts
  - [x] Return 200 with updated split data
  - [x] Add error handling for validation failures

- [x] Task 3: Frontend SplitPicker Update (AC: #7, #8, #9)
  - [x] Modify `frontend/src/features/expenses/types.ts` (SplitPicker uses types.ts for config)
  - [x] Remove disabled state from Percentage split card
  - [x] Remove "coming soon" tooltip
  - [x] Enable click/tap for Percentage selection

- [x] Task 4: Frontend Percentage Split Inputs (AC: #10, #11)
  - [x] Create `frontend/src/features/expenses/components/PercentageSplitInputs.tsx`
  - [x] Display member chips with inline percentage input fields
  - [x] Use BalanceDisplay component for calculated amount display
  - [x] Format: "%" suffix with calculated amount below
  - [x] Accept numeric input (0-100) for each member
  - [x] Show teal checkmark when valid percentage entered

- [x] Task 5: Frontend Real-Time Calculation (AC: #12, #13)
  - [x] Add real-time calculation: (total_amount * percentage / 100)
  - [x] Display calculated amount for each member using BalanceDisplay
  - [x] Show total percentage progress indicator (0-100%)
  - [x] Visual indicator: progress bar or circular indicator
  - [x] Show progress in success color when at 100%
  - [x] Show progress in muted color when approaching 100%
  - [x] Show progress in error color when over 100%

- [x] Task 6: Frontend Split State Management (AC: #18, #19)
  - [x] Modify `frontend/src/features/expenses/hooks/useSplitState.ts`
  - [x] Add percentages state: Map<user_id, number>
  - [x] Add setPercentage function for individual member percentages
  - [x] Calculate total percentage for validation
  - [x] Validate: percentages sum to 100 (within 0.01 tolerance)
  - [x] Return isValid flag (true when percentages sum to 100)

- [x] Task 7: Frontend Validation & Error Display (AC: #14, #15)
  - [x] Add validation error message component
  - [x] Show error when percentages don't sum to 100
  - [x] Format: "Percentages must sum to 100% (current: X%)"
  - [x] Disable confirm button when validation fails
  - [x] Show inline error below percentage inputs

- [x] Task 8: Frontend Split Mutation Enhancement (AC: #16, #17, #19)
  - [x] Modify `frontend/src/features/expenses/api/expenses.ts`
  - [x] Handle percentage split type in mutation
  - [x] Send: {type: "percentage", splits: [{user_id, percentage}]}
  - [x] On success: invalidate queries for expense and group balances
  - [x] On error: show toast with validation message
  - [x] Return loading, error, mutate states

- [x] Task 9: Frontend Integration with EditableExpensePreview (AC: #19, #20)
  - [x] Modify `frontend/src/features/expenses/components/EditableExpensePreview.tsx`
  - [x] Show PercentageSplitInputs component when Percentage selected
  - [x] Show total percentage progress indicator above inputs
  - [x] Pre-populate percentages when switching from Equal split (100 / num_members)
  - [x] Maintain edited state across mode switches

- [x] Task 10: Backend Testing (AC: #2, #3, #5, #18)
  - [x] Test calculate_percentage_split() with various percentages
  - [x] Test validation: percentages less than 100 (error)
  - [x] Test validation: percentages greater than 100 (error)
  - [x] Test validation: percentages equal to 100 (success)
  - [x] Test API endpoint with valid percentage split requests
  - [x] Test API validation: non-existent expense, non-creator user
  - [x] Test rounding distribution for amounts with decimals

- [x] Task 11: Frontend Testing (AC: #10, #11, #12, #14, #15)
  - [x] Test PercentageSplitInputs: enter percentages for each member
  - [x] Test real-time calculation: displays correct amounts
  - [x] Test total percentage indicator: updates correctly
  - [x] Test validation: error shows when percentages don't sum to 100
  - [x] Test confirm button: disabled when invalid, enabled when valid
  - [x] Test calculated amount formatting with BalanceDisplay
  - [x] Test switch from Equal to Percentage: percentages pre-populate

## Dev Notes

### CRITICAL: This Story Builds on Stories 3.5 and 3.6 Foundation

Story 3.7 is the **third of four split logic stories** (3.5-3.8). This story extends the split foundation:
- Uses the same `expense_splits` table created in Story 3.5
- Extends the same split API endpoint created in Story 3.5
- Reuses the same SplitPicker, MemberChips components from Story 3.5
- Adds a new PercentageSplitInputs component for percentage entry
- Enhances useSplitState hook to handle percentages
- **Inspired by Story 3.6 patterns:** Reuses the validation approach from UnequalSplitInputs

**Key Difference from Equal and Unequal Splits:**
- **Equal Split:** System calculates amounts automatically (total / num_members)
- **Unequal Split:** User enters custom amounts, system validates only
- **Percentage Split:** User enters percentages, system calculates amounts AND validates sum

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
Backend:
├── backend/app/features/expenses/
│   ├── service.py                   # MODIFY: Add calculate_percentage_split()
│   └── router.py                    # MODIFY: Add percentage split handling

Frontend:
├── frontend/src/features/expenses/
│   ├── components/
│   │   ├── SplitPicker.tsx          # MODIFY: Enable percentage card
│   │   ├── PercentageSplitInputs.tsx # CREATE: Percentage inputs
│   │   └── EditableExpensePreview.tsx  # MODIFY: Add percentage mode
│   ├── hooks/
│   │   └── useSplitState.ts         # MODIFY: Add percentages state
│   └── api/
│       └── useUpdateExpenseSplit.ts # MODIFY: Handle percentage split
```

**Naming Conventions (MANDATORY):**
- Backend functions: `snake_case` (e.g., `calculate_percentage_split`)
- Frontend components: `PascalCase` (e.g., `PercentageSplitInputs`)
- Frontend hooks: `camelCase` starting with `use` (e.g., `useSplitState`)
- API request fields: `snake_case` (e.g., `user_id`, `percentage`)
- Frontend state: `camelCase` (e.g., `percentages`, `setPercentage`)

### Technical Requirements

**Backend - Percentage Split Calculation:**
```python
# backend/app/features/expenses/service.py
from decimal import Decimal
from typing import List, Dict
from uuid import UUID

def calculate_percentage_split(
    total_amount: Decimal,
    splits: List[Dict[str, any]]
) -> List[dict]:
    """
    Validate percentages and calculate split amounts.

    Args:
        total_amount: Total expense amount
        splits: List of {user_id, percentage} specified by user

    Returns:
        List of {user_id, amount_owed} calculated

    Raises:
        ValueError: If percentages don't sum to 100
    """
    # Sum all provided percentages
    total_percentage = sum(Decimal(str(s["percentage"])) for s in splits)

    # Validate sum equals 100 (within 0.01 tolerance)
    if abs(total_percentage - Decimal("100")) > Decimal("0.01"):
        raise ValueError(
            f"Split percentages ({total_percentage}%) must equal 100%"
        )

    # Calculate amounts and handle rounding
    calculated_splits = []
    remaining_amount = total_amount

    for i, split in enumerate(splits):
        user_id = UUID(split["user_id"])
        percentage = Decimal(str(split["percentage"]))

        # Calculate amount for this member
        if i == len(splits) - 1:
            # Last member gets remainder (to avoid rounding errors)
            amount_owed = remaining_amount
        else:
            amount_owed = (total_amount * percentage / Decimal("100")).quantize(Decimal("0.01"))
            remaining_amount -= amount_owed

        calculated_splits.append({
            "user_id": user_id,
            "amount_owed": amount_owed
        })

    return calculated_splits
```

**Backend - Split API Enhancement:**
```python
# backend/app/features/expenses/router.py
@router.put("/expenses/{expense_id}/split")
def update_expense_split(
    expense_id: UUID,
    split_data: dict,
    session: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    # ... existing expense and creator validation ...

    split_type = split_data.get("type")

    if split_type == "equal":
        # ... existing equal split logic ...

    elif split_type == "unequal":
        # ... existing unequal split logic ...

    elif split_type == "percentage":
        # Validate splits provided
        splits_data = split_data.get("splits", [])
        if not splits_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Percentage split requires 'splits' array with user_id and percentage"
            )

        # Calculate and validate percentage split
        validated_splits = calculate_percentage_split(
            total_amount=expense.amount,
            splits=splits_data
        )

        # Delete existing splits
        session.query(ExpenseSplit).filter(
            ExpenseSplit.expense_id == expense_id
        ).delete()

        # Create new splits
        for split in validated_splits:
            expense_split = ExpenseSplit(
                expense_id=expense_id,
                user_id=split["user_id"],
                amount_owed=split["amount_owed"]
            )
            session.add(expense_split)

        session.commit()

        return {
            "expense_id": expense_id,
            "split_type": "percentage",
            "splits": validated_splits
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Split type '{split_type}' not yet implemented"
        )
```

**Frontend - Percentage Split Types:**
```typescript
// frontend/src/features/expenses/types.ts
export interface PercentageSplitRequest {
  type: "percentage"
  splits: Array<{
    user_id: string
    percentage: number
  }>
}

export interface PercentageSplitState {
  percentages: Map<string, number>  // user_id -> percentage
  totalPercentage: number  // sum of all percentages
}
```

**Frontend - PercentageSplitInputs Component:**
```typescript
// frontend/src/features/expenses/components/PercentageSplitInputs.tsx
import { useState, useMemo } from 'react'
import { BalanceDisplay } from '@/components/ui/balance-display'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Check } from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Progress } from '@/components/ui/progress'

interface GroupMember {
  id: string
  full_name: string
  email?: string
  avatar_url?: string
}

interface PercentageSplitInputsProps {
  members: GroupMember[]
  percentages: Map<string, number>
  totalAmount: number
  onPercentageChange: (memberId: string, percentage: number) => void
}

export function PercentageSplitInputs({
  members,
  percentages,
  totalAmount,
  onPercentageChange
}: PercentageSplitInputsProps) {
  // Calculate total percentage
  const totalPercentage = useMemo(() => {
    return Array.from(percentages.values()).reduce((sum, pct) => sum + pct, 0)
  }, [percentages])

  const isExactMatch = Math.abs(totalPercentage - 100) < 0.01
  const isOverAllocated = totalPercentage > 100

  return (
    <div className="percentage-split-inputs-container">
      {/* Total percentage progress indicator */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-primary">
            Total Percentage:
          </span>
          <span className={cn(
            "text-sm font-bold",
            isExactMatch && "text-success",
            isOverAllocated && "text-destructive",
            !isExactMatch && !isOverAllocated && "text-muted-foreground"
          )}>
            {totalPercentage.toFixed(1)}%
          </span>
        </div>
        <Progress
          value={Math.min(totalPercentage, 100)}
          className={cn(
            "h-2",
            isExactMatch && "bg-success",
            isOverAllocated && "bg-destructive"
          )}
        />
      </div>

      {/* Member percentage inputs */}
      <div className="space-y-2">
        {members.map((member) => {
          const initials = member.full_name
            .split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2)

          const percentage = percentages.get(member.id) || 0
          const calculatedAmount = (totalAmount * percentage / 100)
          const hasPercentage = percentage > 0

          return (
            <motion.div
              key={member.id}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg border",
                hasPercentage ? "border-action bg-action/5" : "border-border bg-surface"
              )}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Avatar className="w-8 h-8">
                {member.avatar_url && <AvatarImage src={member.avatar_url} />}
                <AvatarFallback className={cn(
                  "text-xs",
                  hasPercentage ? "bg-action text-white" : "bg-muted text-muted-foreground"
                )}>
                  {initials}
                </AvatarFallback>
              </Avatar>

              <span className="flex-1 text-sm font-medium text-primary">
                {member.full_name}
              </span>

              <div className="relative flex items-center gap-2">
                <input
                  type="number"
                  value={percentage || ''}
                  onChange={(e) => onPercentageChange(member.id, parseFloat(e.target.value) || 0)}
                  placeholder="0"
                  step="0.1"
                  min="0"
                  max="100"
                  className={cn(
                    "w-20 pl-3 pr-8 py-2 text-right rounded-md border",
                    "text-sm font-medium",
                    "focus:outline-none focus:ring-2 focus:ring-action",
                    hasPercentage && "border-action bg-action/10"
                  )}
                />
                <span className="absolute right-3 text-sm text-muted-foreground">
                  %
                </span>
                {hasPercentage && (
                  <Check className="absolute right-8 w-4 h-4 text-action" />
                )}
              </div>

              {/* Calculated amount display */}
              {hasPercentage && (
                <div className="w-24 text-right">
                  <div className="text-xs text-muted-foreground">Amount:</div>
                  <BalanceDisplay
                    amount={calculatedAmount}
                    variant="body"
                    className="text-sm"
                  />
                </div>
              )}
            </motion.div>
          )
        })}
      </div>

      {/* Validation message */}
      {!isExactMatch && (
        <p className="text-xs text-muted-foreground mt-3">
          {isOverAllocated
            ? `Over-allocated by ${(totalPercentage - 100).toFixed(1)}%`
            : `Allocate ${(100 - totalPercentage).toFixed(1)}% more`
          }
        </p>
      )}
    </div>
  )
}
```

**Frontend - useSplitState Hook Enhancement:**
```typescript
// frontend/src/features/expenses/hooks/useSplitState.ts
export function useSplitState({
  totalAmount,
  members,
  initialType = SplitType.EQUAL,
  payerId
}: UseSplitStateProps) {
  const [splitType, setSplitType] = useState<SplitType>(initialType)
  const [excludedMembers, setExcludedMembers] = useState<Set<string>>(new Set())
  const [customAmounts, setCustomAmounts] = useState<Map<string, number>>(new Map())
  const [percentages, setPercentages] = useState<Map<string, number>>(new Map())

  // Calculate total percentage for validation
  const totalPercentage = useMemo(() => {
    if (splitType !== SplitType.PERCENTAGE) return 0

    return Array.from(percentages.values()).reduce((sum, pct) => sum + pct, 0)
  }, [splitType, percentages])

  // Set percentage for a member
  const setPercentage = useCallback((memberId: string, percentage: number) => {
    setPercentages(prev => {
      const newMap = new Map(prev)
      if (percentage >= 0 && percentage <= 100) {
        newMap.set(memberId, percentage)
      } else {
        newMap.delete(memberId)
      }
      return newMap
    })
  }, [])

  // Validate split based on type
  const isValid = useMemo(() => {
    if (splitType === SplitType.EQUAL) {
      const includedCount = members.length - excludedMembers.size
      return includedCount >= 2
    }

    if (splitType === SplitType.UNEQUAL) {
      // All members must have amounts
      if (customAmounts.size !== members.length) return false
      // Amounts must sum to total
      const allocated = Array.from(customAmounts.values()).reduce((sum, amount) => sum + amount, 0)
      return Math.abs(totalAmount - allocated) < 0.01
    }

    if (splitType === SplitType.PERCENTAGE) {
      // All members must have percentages
      if (percentages.size !== members.length) return false
      // Percentages must sum to 100
      return Math.abs(totalPercentage - 100) < 0.01
    }

    return false
  }, [splitType, members.length, excludedMembers.size, customAmounts, percentages, totalPercentage, totalAmount])

  return {
    splitType,
    setSplitType,
    excludedMembers,
    toggleMemberExclusion,
    customAmounts,
    setCustomAmount,
    percentages,
    setPercentage,
    totalPercentage,
    isValid
  }
}
```

### Project Structure Notes

**This story CREATES:**
- `frontend/src/features/expenses/components/PercentageSplitInputs.tsx`

**This story MODIFIES:**
- `backend/app/features/expenses/service.py` (add calculate_percentage_split())
- `backend/app/features/expenses/router.py` (handle percentage split type)
- `frontend/src/features/expenses/components/SplitPicker.tsx` (enable percentage card)
- `frontend/src/features/expenses/hooks/useSplitState.ts` (add percentages state)
- `frontend/src/features/expenses/api/useUpdateExpenseSplit.ts` (handle percentage type)
- `frontend/src/features/expenses/components/EditableExpensePreview.tsx` (show percentage inputs)

**This story REUSES from Story 3.5 and 3.6:**
- `ExpenseSplit` model (already exists)
- SplitPicker component (exists, just enable percentage card)
- MemberChips component (exists, reused for member display)
- BalanceDisplay component (exists, for currency formatting)
- useSplitState hook (exists, extend with percentages)
- Split API endpoint (exists, add percentage type handling)
- Progress component (from shadcn/ui for percentage indicator)

### Previous Story Intelligence

**From Story 3.5 (Split Logic - Equal Split):**
- ExpenseSplit table exists with `expense_id`, `user_id`, `amount_owed`
- Split API endpoint exists: `PUT /api/v1/expenses/{expense_id}/split`
- SplitPicker component exists with 4 cards (equal, unequal, percentage, shares)
- useSplitState hook exists with equal split logic
- **Integration Point:** Add percentage split type to existing endpoint and hook

**From Story 3.6 (Split Logic - Unequal Custom Amounts):**
- UnequalSplitInputs component provides pattern for percentage inputs
- Real-time validation pattern established (remaining amount → total percentage)
- Color-coded validation pattern (muted/success/destructive)
- Map-based state management for user-specific values
- **Key Pattern:** Reuse the validation approach but adapt for percentages (0-100 range instead of variable amounts)

**From Story 3.4 (Manual Override of Parsed Data):**
- EditableExpensePreview has complex edit mode for advanced edits
- **Integration Point:** Show PercentageSplitInputs in complex edit mode when percentage selected

**From Story 3.1 (Create Expense Model and Basic Entry):**
- Expense model exists with `amount`, `group_id`, `payer_id`
- **Integration Point:** Fetch group members for split display

**From Story 2.5 (UX Foundation & Design System):**
- Design system tokens established (action color, success color for validation)
- BalanceDisplay component for currency formatting
- Progress component available for percentage indicator
- **Apply:** Use success color when total percentage is 100%, muted color for approaching, destructive for over 100%

### Git Intelligence

**Recent Commits (Analysis):**
- `e0f9efb` - chore: Update sprint status - Story 3.6 complete after code review
  - **Insight:** Story 3.6 completed successfully with code review fixes applied
- `5213215` - fix: Code review fixes for Story 3.6 - Split Logic Unequal Custom Amounts
  - **Insight:** Adversarial code review found issues with validation, null safety, and state management
  - **Learnings:** Apply the same fixes to percentage split (validate all fields, handle NaN/null, proper state reset)
- `3708b73` - fix: Code review fixes for Story 3.5 - Split Logic Equal Split
  - **Insight:** Story 3.5 established robust split foundation patterns
  - **Learnings:** Follow the same patterns for percentage split (API structure, validation, error handling)

**Commit Message Format:**
```
feat: Complete Story 3.7 - Split logic - percentage split
```

**Library Versions:**
- Python Decimal for precise financial calculations
- Framer Motion for animations
- TanStack Query for API mutations
- shadcn/ui (Input, Avatar, Progress components)

### Testing Requirements

**Backend Tests (Pytest):**
```python
# backend/app/features/expenses/tests/test_split_service.py
import pytest
from decimal import Decimal
from app.features.expenses.service import calculate_percentage_split

def test_percentage_split_exact_100():
    """Test percentage split when percentages sum to 100"""
    splits = [
        {"user_id": "user1", "percentage": 60.0},
        {"user_id": "user2", "percentage": 40.0}
    ]

    result = calculate_percentage_split(
        total_amount=Decimal("100.00"),
        splits=splits
    )

    assert len(result) == 2
    assert result[0]["amount_owed"] == Decimal("60.00")
    assert result[1]["amount_owed"] == Decimal("40.00")

def test_percentage_split_under_100():
    """Test that percentages under 100 raise error"""
    splits = [
        {"user_id": "user1", "percentage": 50.0},
        {"user_id": "user2", "percentage": 30.0}
    ]  # Total = 80, should be 100

    with pytest.raises(ValueError, match="must equal 100%"):
        calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

def test_percentage_split_over_100():
    """Test that percentages over 100 raise error"""
    splits = [
        {"user_id": "user1", "percentage": 70.0},
        {"user_id": "user2", "percentage": 50.0}
    ]  # Total = 120, should be 100

    with pytest.raises(ValueError, match="must equal 100%"):
        calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

def test_percentage_split_rounding():
    """Test that rounding is handled correctly"""
    splits = [
        {"user_id": "user1", "percentage": 33.33},
        {"user_id": "user2", "percentage": 33.33},
        {"user_id": "user3", "percentage": 33.34}
    ]  # Total = 100.00

    result = calculate_percentage_split(
        total_amount=Decimal("100.00"),
        splits=splits
    )

    # Verify amounts sum to total (last member gets remainder)
    total_calculated = sum(s["amount_owed"] for s in result)
    assert total_calculated == Decimal("100.00")

def test_percentage_split_three_way_split():
    """Test equal three-way percentage split"""
    splits = [
        {"user_id": "user1", "percentage": 33.33},
        {"user_id": "user2", "percentage": 33.33},
        {"user_id": "user3", "percentage": 33.34}
    ]

    result = calculate_percentage_split(
        total_amount=Decimal("100.00"),
        splits=splits
    )

    assert len(result) == 3
    # Verify sum is exactly 100.00 (last member gets rounding remainder)
    total = sum(s["amount_owed"] for s in result)
    assert total == Decimal("100.00")
```

**Frontend Tests (Vitest):**
```typescript
// PercentageSplitInputs.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { PercentageSplitInputs } from './PercentageSplitInputs'

describe('PercentageSplitInputs', () => {
  const mockMembers = [
    { id: '1', full_name: 'Alex' },
    { id: '2', full_name: 'Sam' },
    { id: '3', full_name: 'Tom' }
  ]

  test('displays total percentage progress', () => {
    const percentages = new Map([
      ['1', 50],
      ['2', 30]
    ])

    render(
      <PercentageSplitInputs
        members={mockMembers}
        percentages={percentages}
        totalAmount={100}
        onPercentageChange={() => {}}
      />
    )

    expect(screen.getByText(/total percentage/i)).toBeInTheDocument()
    expect(screen.getByText(/80\.0%/)).toBeInTheDocument()  // 50 + 30
  })

  test('shows success state when at 100%', () => {
    const percentages = new Map([
      ['1', 60],
      ['2', 40]
    ])  // Total = 100%

    render(
      <PercentageSplitInputs
        members={mockMembers}
        percentages={percentages}
        totalAmount={100}
        onPercentageChange={() => {}}
      />
    )

    // Total percentage should show 100.0%
    expect(screen.getByText(/100\.0%/)).toBeInTheDocument()
  })

  test('shows calculated amount for each percentage', () => {
    const percentages = new Map([
      ['1', 60],
      ['2', 40]
    ])

    render(
      <PercentageSplitInputs
        members={mockMembers}
        percentages={percentages}
        totalAmount={100}
        onPercentageChange={() => {}}
      />
    )

    // Should show Rs 60.00 for 60% and Rs 40.00 for 40%
    expect(screen.getByText(/Rs.*60/)).toBeInTheDocument()
    expect(screen.getByText(/Rs.*40/)).toBeInTheDocument()
  })

  test('calls onPercentageChange when user types percentage', () => {
    const onPercentageChange = vi.fn()
    const percentages = new Map()

    render(
      <PercentageSplitInputs
        members={mockMembers}
        percentages={percentages}
        totalAmount={100}
        onPercentageChange={onPercentageChange}
      />
    )

    const input = screen.getAllByPlaceholderText('0')[0]
    fireEvent.change(input, { target: { value: '50' } })

    expect(onPercentageChange).toHaveBeenCalledWith('1', 50)
  })
})

// useSplitState.test.ts - add percentage split tests
describe('useSplitState - percentage split', () => {
  test('calculates total percentage correctly', () => {
    const members = [
      { id: '1', full_name: 'Alex' },
      { id: '2', full_name: 'Sam' }
    ]

    const { result } = renderHook(() =>
      useSplitState({ totalAmount: 100, members })
    )

    act(() => {
      result.current.setSplitType(SplitType.PERCENTAGE)
      result.current.setPercentage('1', 60)
      result.current.setPercentage('2', 40)
    })

    expect(result.current.totalPercentage).toBe(100)
  })

  test('validates when percentages sum to 100', () => {
    const members = [
      { id: '1', full_name: 'Alex' },
      { id: '2', full_name: 'Sam' }
    ]

    const { result } = renderHook(() =>
      useSplitState({ totalAmount: 100, members })
    )

    act(() => {
      result.current.setSplitType(SplitType.PERCENTAGE)
      result.current.setPercentage('1', 60)
      result.current.setPercentage('2', 40)
    })

    expect(result.current.isValid).toBe(true)
  })

  test('invalidates when percentages do not sum to 100', () => {
    const members = [
      { id: '1', full_name: 'Alex' },
      { id: '2', full_name: 'Sam' }
    ]

    const { result } = renderHook(() =>
      useSplitState({ totalAmount: 100, members })
    )

    act(() => {
      result.current.setSplitType(SplitType.PERCENTAGE)
      result.current.setPercentage('1', 50)
      result.current.setPercentage('2', 30)
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
  "type": "percentage",
  "splits": [
    {
      "user_id": "user-1",
      "percentage": 60.0
    },
    {
      "user_id": "user-2",
      "percentage": 40.0
    }
  ]
}
```

**Response (Success):**
```typescript
{
  "expense_id": "uuid",
  "split_type": "percentage",
  "splits": [
    {
      "user_id": "user-1",
      "amount_owed": 60.00
    },
    {
      "user_id": "user-2",
      "amount_owed": 40.00
    }
  ]
}
```

**Response (Validation Error):**
```typescript
{
  "detail": "Split percentages (80.0%) must equal 100%"
}
```

### Important Notes for Developer

1. **Enable Percentage Card:** Remove the disabled state and "coming soon" message from the Percentage split card in SplitPicker.

2. **Progress Indicator:** Use shadcn/ui Progress component to show total percentage progress visually (0-100%).

3. **Real-Time Calculation:** Show calculated amount below each percentage input as user types. This helps users understand the impact of their percentages.

4. **Rounding Strategy:** Use the "remainder to last member" strategy to avoid penny loss:
   - Calculate amounts normally for all but last member
   - Last member gets remaining amount (ensures sum equals total exactly)

5. **Pre-population:** When switching from Equal to Percentage, pre-populate percentage inputs with equal distribution (100 / num_members). For example, with 3 members: 33.33%, 33.33%, 33.34%.

6. **Validation UX:** Show total percentage progress with visual indicator:
   - Muted text/color: Still allocating (total < 100%)
   - Success color/text: Fully allocated (total = 100%)
   - Destructive color/text: Over-allocated (total > 100%)

7. **Decimal Precision:** Use step="0.1" on percentage inputs for one decimal place. This allows precise splits like 33.3%.

8. **Backend Validation:** Always validate percentages sum to 100 on backend. Never trust frontend validation.

9. **Error Messaging:** Provide clear error messages showing both expected total and current sum: "Percentages must sum to 100% (current: 80.0%)".

10. **Confirm Button:** Disable confirm button until percentages sum to 100 exactly. Show inline error explaining why.

11. **Currency Formatting:** Always use BalanceDisplay component for calculated amounts (Rs prefix, comma separators).

12. **Input Constraints:** Set min="0" and max="100" on percentage inputs. Use step="0.1" for decimal precision.

13. **Member Display:** Reuse MemberChips pattern but add percentage input field and calculated amount display below each chip.

14. **State Management:** Store percentages in a Map<user_id, number> for efficient lookups.

15. **Mobile UX:** Ensure percentage inputs are touch-friendly (min 44x44px tap targets). Show numeric keypad on mobile.

16. **Animation Timing:** Keep animations under 200ms. Use Framer Motion for smooth transitions.

17. **Accessibility:** Add aria-label to percentage inputs: "Percentage for {member name}". Use semantic HTML for validation messages.

18. **Testing Coverage:** Test validation edge cases: under 100%, over 100%, exact 100%, rounding distribution.

19. **Integration Test:** Verify that switching from Equal to Percentage pre-populates percentages correctly (equal distribution).

20. **Zero Percentage Handling:** If user enters 0 for a member, treat as "0% share" rather than error. The member will owe Rs 0.

21. **Progress Component:** Use shadcn/ui Progress component for visual percentage indicator. Customize colors based on validation state.

22. **Calculated Amount Display:** Show calculated amount below each percentage input in a subtle format (smaller text, muted color) to avoid clutter.

23. **Backend Efficiency:** The percentage split function validates AND calculates. This is different from unequal split (validate only).

24. **Success Feedback:** On successful split save, show success toast and collapse complex edit mode back to simple mode.

### Epic 3 Context

This is Story 7 of 8 in Epic 3 (Smart Expense Entry):
- 3.1 - Create expense model and basic entry ✅ DONE
- 3.2 - Natural language input interface ✅ DONE
- 3.3 - AI parsing service integration ✅ DONE
- 3.4 - Manual override of parsed data ✅ DONE
- 3.5 - Split logic - equal split ✅ DONE
- 3.6 - Split logic - unequal amounts ✅ DONE
- **3.7 (this)** - Split logic - percentage split
- 3.8 - Exclude members from expense (NEXT)

**Dependencies:**
- This story DEPENDS ON: Story 3.1 (Expense model), Story 3.4 (EditableExpensePreview), Story 3.5 (Split foundation), Story 3.6 (Unequal split patterns)
- This story ENABLES: Story 3.8 (Exclude members) - will complete the split logic feature set

### NFR Compliance

**NFR1 (In-App Latency):** Real-time validation feedback should be instant (<100ms). Use debounced input if needed.

**Accuracy:** Financial calculations must be precise. Use "remainder to last member" strategy to avoid rounding errors.

**NFR2 (Load Time):** Keep component render time under 1.5s on 4G.

### UX Requirements Summary

**From PRD (FR7):** "User can specify split logic: Equal, Unequal, Percentage, or Shares" - This story implements Percentage split.

**From UX Design Specification:**
- **Visual Split Picker:** Percentage card shows "%" symbol with example percentages icon
- **Inline Editing:** Percentage inputs appear next to each member chip
- **Real-Time Calculation:** Show resulting amount for each percentage
- **Progress Indicator:** Visual indicator showing total percentage progress toward 100%
- **BalanceDisplay:** Use neutral currency formatting (Rs prefix, no red/green)

### References

- [Source: epics.md - Story 3.7](_bmad-output/planning-artifacts/epics.md#story-37-split-logic---percentage-split)
- [Source: architecture.md - Backend Architecture](_bmad-output/planning-artifacts/architecture.md#backend-architecture)
- [Source: prd.md - FR7](_bmad-output/planning-artifacts/prd.md#transaction-logic--workflow)
- [Previous Story: 3-6-split-logic-unequal-custom-amounts.md](_bmad-output/implementation-artifacts/3-6-split-logic-unequal-custom-amounts.md)
- [Previous Story: 3-5-split-logic-equal-split.md](_bmad-output/implementation-artifacts/3-5-split-logic-equal-split.md)
- [Previous Story: 3-4-manual-override-of-parsed-data.md](_bmad-output/implementation-artifacts/3-4-manual-override-of-parsed-data.md)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

N/A - Story creation complete, implementation pending dev-story workflow.

### Completion Notes List

**Story 3.7 Creation Complete!**

**Story Summary:**
- **Epic:** Epic 3 - Smart Expense Entry (Story 7 of 8)
- **Title:** Split Logic - Percentage Split
- **Status:** ready-for-dev
- **Dependencies:** Story 3.1 (Expense model), Story 3.4 (EditableExpensePreview), Story 3.5 (Split foundation), Story 3.6 (Unequal split patterns)

**Comprehensive Context Provided:**
1. ✅ **Story Requirements** - 20 BDD-formatted acceptance criteria from epics.md
2. ✅ **Task Breakdown** - 11 tasks with 50+ subtasks covering backend, frontend, and testing
3. ✅ **Architecture Compliance** - File locations, naming conventions, project structure
4. ✅ **Technical Specifications** - Complete code examples for backend and frontend
5. ✅ **Previous Story Intelligence** - Patterns learned from Stories 3.5 and 3.6
6. ✅ **Git Intelligence** - Recent commit analysis and learnings
7. ✅ **API Contract** - Request/response schemas with examples
8. ✅ **Testing Requirements** - Comprehensive test cases for backend and frontend
9. ✅ **Developer Notes** - 24 important notes covering edge cases and UX patterns
10. ✅ **Epic Context** - Position within Epic 3 and dependencies

**Key Implementation Patterns:**
- **Backend:** calculate_percentage_split() with rounding strategy (remainder to last member)
- **Frontend:** PercentageSplitInputs component with real-time calculation and progress indicator
- **Validation:** Total percentage must equal 100% (with 0.01 tolerance)
- **UX:** Visual progress indicator + calculated amounts for each percentage
- **State Management:** Map-based percentages state in useSplitState hook

**Next Steps for Developer:**
1. Review all acceptance criteria and technical requirements
2. Run `dev-story` workflow to begin implementation
3. Follow the file structure and naming conventions specified
4. Implement backend percentage split calculation first
5. Implement frontend PercentageSplitInputs component
6. Add comprehensive tests as specified
7. Run code review before marking story complete

**Developer Guardrails:**
- Use Progress component from shadcn/ui for percentage indicator
- Apply rounding strategy to avoid penny loss (remainder to last member)
- Pre-populate equal distribution when switching from Equal to Percentage
- Validate on both frontend (UX) and backend (security)
- Follow patterns from Story 3.6 (UnequalSplitInputs) for consistency

### File List

**Story File:**
- _bmad-output/implementation-artifacts/3-7-split-logic-percentage-split.md (this file)

**Reference Documents:**
- _bmad-output/planning-artifacts/epics.md (Epic 3 stories)
- _bmad-output/planning-artifacts/architecture.md (Architecture patterns)
- _bmad-output/planning-artifacts/prd.md (FR7 - split logic)
- _bmad-output/implementation-artifacts/3-6-split-logic-unequal-custom-amounts.md (Previous story - unequal patterns)
- _bmad-output/implementation-artifacts/3-5-split-logic-equal-split.md (Split foundation)
- _bmad-output/implementation-artifacts/3-4-manual-override-of-parsed-data.md (Edit mode)
- _bmad-output/session-context.md (Project context)
- _bmad-output/implementation-artifacts/solution-patterns.yaml (Known issues)
