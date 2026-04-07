# Expenses feature service - CRUD operations for expenses
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from sqlmodel import Session, select

from app.features.expenses.models import Expense, ExpenseCreate, ExpenseStatus, ExpenseUpdate
from app.features.groups.models import GroupMember


def is_user_group_member(
    session: Session, user_id: uuid.UUID, group_id: uuid.UUID
) -> bool:
    """Check if user is a member of the specified group."""
    statement = select(GroupMember).where(
        GroupMember.user_id == user_id, GroupMember.group_id == group_id
    )
    return session.exec(statement).first() is not None


def filter_included_members(
    member_ids: List[uuid.UUID],
    excluded_user_ids: List[uuid.UUID] | None = None
) -> List[uuid.UUID]:
    """
    Filter out excluded members from the member list.

    Args:
        member_ids: All group member IDs
        excluded_user_ids: Members to exclude

    Returns:
        List of included member IDs

    Raises:
        ValueError: If fewer than 2 members remain after exclusion
    """
    excluded_set = set(excluded_user_ids) if excluded_user_ids else set()
    included_members = [m for m in member_ids if m not in excluded_set]

    if len(included_members) < 2:
        raise ValueError(
            "At least 2 members must be included in the split. "
            f"Currently have {len(included_members)} member(s)."
        )

    return included_members


def create_expense(
    session: Session, expense_in: ExpenseCreate, current_user_id: uuid.UUID
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


def update_expense(
    session: Session, expense: Expense, update_data: ExpenseUpdate
) -> Expense:
    """
    Update expense fields. Only updates provided (non-None) fields.

    Args:
        session: Database session
        expense: Existing Expense object to update
        update_data: ExpenseUpdate with optional fields

    Returns:
        Updated Expense object
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(expense, field, value)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


def calculate_equal_split(
    total_amount: Decimal,
    member_ids: list[uuid.UUID],
    excluded_user_ids: list[uuid.UUID] | None = None,
    payer_id: uuid.UUID | None = None,
) -> list[dict]:
    """
    Calculate equal split amounts among group members.

    Args:
        total_amount: Total expense amount
        member_ids: All group member IDs
        excluded_user_ids: Members to exclude from split (optional)
        payer_id: The expense creator (absorbs rounding difference)

    Returns:
        List of {user_id, amount_owed} for included members

    Raises:
        ValueError: If fewer than 2 members are included in the split

    Examples:
        >>> calculate_equal_split(Decimal("100.00"), [id1, id2, id3, id4])
        [{'user_id': id1, 'amount_owed': Decimal('25.00')}, ...]

        >>> calculate_equal_split(Decimal("100.00"), [id1, id2, id3])
        [{'user_id': id1, 'amount_owed': Decimal('33.34')}, ...]  # payer absorbs 0.01
    """
    # Filter out excluded members and validate minimum
    included_members = filter_included_members(member_ids, excluded_user_ids)

    # Calculate equal amount
    amount_per_person = total_amount / Decimal(len(included_members))

    # Round to 2 decimal places using half-up rounding
    amount_rounded = amount_per_person.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Calculate total after rounding
    rounded_total = amount_rounded * Decimal(len(included_members))

    # Handle penny mismatch: payer absorbs difference
    difference = total_amount - rounded_total
    splits = []

    for user_id in included_members:
        amount = amount_rounded
        # Payer absorbs rounding difference
        if payer_id and user_id == payer_id:
            amount += difference
        splits.append({
            "user_id": user_id,
            "amount_owed": amount
        })

    return splits


def calculate_unequal_split(
    total_amount: Decimal,
    splits: list[dict],
    member_ids: list[uuid.UUID] | None = None,
    excluded_user_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """
    Validate and prepare unequal split amounts.

    Args:
        total_amount: Total expense amount
        splits: List of {user_id, amount} specified by user
        member_ids: All group member IDs (for validation)
        excluded_user_ids: Members to exclude from split (optional)

    Returns:
        List of {user_id, amount_owed} validated

    Raises:
        ValueError: If amounts don't sum to total or fewer than 2 members after exclusion

    Examples:
        >>> calculate_unequal_split(
        ...     Decimal("100.00"),
        ...     [{"user_id": id1, "amount": 50.00}, {"user_id": id2, "amount": 50.00}]
        ... )
        [{'user_id': id1, 'amount_owed': Decimal('50.00')}, ...]
    """
    excluded_set = set(excluded_user_ids) if excluded_user_ids else set()

    # Filter out excluded members from splits
    included_splits = [
        s for s in splits
        if uuid.UUID(str(s["user_id"])) not in excluded_set
    ]

    # Validate minimum members
    if len(included_splits) < 2:
        raise ValueError(
            f"At least 2 members must be included in the split. "
            f"Currently have {len(included_splits)} member(s)."
        )

    # Sum all provided amounts
    provided_total = sum(Decimal(str(s["amount"])) for s in included_splits)

    # Validate sum matches total (within 0.01 tolerance for floating point)
    if abs(provided_total - total_amount) > Decimal("0.01"):
        raise ValueError(
            f"Split amounts (Rs {provided_total}) must equal "
            f"total expense amount (Rs {total_amount})"
        )

    # Return validated splits with safe UUID conversion
    validated_splits = []
    for split_item in included_splits:
        # Safe UUID conversion - handle both string and UUID objects
        user_id_val = split_item["user_id"]
        if isinstance(user_id_val, uuid.UUID):
            user_id = user_id_val
        else:
            user_id = uuid.UUID(str(user_id_val))

        validated_splits.append({
            "user_id": user_id,
            "amount_owed": Decimal(str(split_item["amount"]))
        })

    return validated_splits


def calculate_percentage_split(
    total_amount: Decimal,
    splits: list[dict],
    member_ids: list[uuid.UUID] | None = None,
    excluded_user_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """
    Validate percentages and calculate split amounts.

    Args:
        total_amount: Total expense amount
        splits: List of {user_id, percentage} specified by user
        member_ids: All group member IDs (for validation)
        excluded_user_ids: Members to exclude from split (optional)

    Returns:
        List of {user_id, amount_owed} calculated

    Raises:
        ValueError: If percentages don't sum to 100 or fewer than 2 members after exclusion

    Examples:
        >>> calculate_percentage_split(
        ...     Decimal("100.00"),
        ...     [{"user_id": id1, "percentage": 60.0}, {"user_id": id2, "percentage": 40.0}]
        ... )
        [{'user_id': id1, 'amount_owed': Decimal('60.00')}, ...]
    """
    excluded_set = set(excluded_user_ids) if excluded_user_ids else set()

    # Filter out excluded members from splits
    included_splits = [
        s for s in splits
        if uuid.UUID(str(s["user_id"])) not in excluded_set
    ]

    # Validate minimum members
    if len(included_splits) < 2:
        raise ValueError(
            f"At least 2 members must be included in the split. "
            f"Currently have {len(included_splits)} member(s)."
        )

    # Sum all provided percentages
    total_percentage = sum(Decimal(str(s["percentage"])) for s in included_splits)

    # Validate sum equals 100 (within 0.01 tolerance)
    if abs(total_percentage - Decimal("100")) > Decimal("0.01"):
        raise ValueError(
            f"Split percentages ({total_percentage}%) must equal 100%"
        )

    # Calculate amounts and handle rounding
    calculated_splits = []
    remaining_amount = total_amount

    for i, split_item in enumerate(included_splits):
        # Safe UUID conversion - handle both string and UUID objects
        user_id_val = split_item["user_id"]
        if isinstance(user_id_val, uuid.UUID):
            user_id = user_id_val
        else:
            user_id = uuid.UUID(str(user_id_val))

        percentage = Decimal(str(split_item["percentage"]))

        # Calculate amount for this member
        if i == len(included_splits) - 1:
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
