# Expenses feature service - CRUD operations for expenses
import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlmodel import Session, select

from app.features.expenses.models import Expense, ExpenseCreate, ExpenseStatus
from app.features.groups.models import GroupMember


def is_user_group_member(
    session: Session, user_id: uuid.UUID, group_id: uuid.UUID
) -> bool:
    """Check if user is a member of the specified group."""
    statement = select(GroupMember).where(
        GroupMember.user_id == user_id, GroupMember.group_id == group_id
    )
    return session.exec(statement).first() is not None


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
    excluded_user_ids = excluded_user_ids or []

    # Filter out excluded members
    included_members = [m for m in member_ids if m not in excluded_user_ids]

    # Validate minimum members
    if len(included_members) < 2:
        raise ValueError("At least 2 members required for split")

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
