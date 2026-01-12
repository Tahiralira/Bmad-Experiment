# Expenses feature models - Expense, ExpenseSplit, and related schemas
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlmodel import Field, Relationship, SQLModel

from app.features.auth.models import User, utc_now
from app.features.groups.models import ExpenseGroup


class ExpenseStatus(str, PyEnum):
    """Status lifecycle for expenses."""

    DRAFT = "draft"  # Initial state when created
    PENDING_CONFIRMATION = "pending_confirmation"  # Splits assigned, awaiting confirms
    CONFIRMED = "confirmed"  # All members confirmed
    SETTLED = "settled"  # Debts paid off


class SplitStatus(str, PyEnum):
    """Status for individual expense splits."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SETTLED = "settled"


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
    group_id: uuid.UUID = Field(
        foreign_key="expense_group.id", nullable=False, index=True
    )
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    description: str = Field(max_length=500)
    payer_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    created_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    status: ExpenseStatus = Field(default=ExpenseStatus.DRAFT)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now}
    )

    # Relationships
    group: ExpenseGroup = Relationship()
    payer: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Expense.payer_id]"}
    )
    creator: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Expense.created_by]"}
    )
    splits: list["ExpenseSplit"] = Relationship(
        back_populates="expense", cascade_delete=True
    )


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
