# Expenses feature service - CRUD operations for expenses
import uuid

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
