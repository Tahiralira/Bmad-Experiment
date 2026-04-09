# Expenses feature models - Expense, ExpenseSplit, and related schemas
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

import sqlalchemy as sa
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


class ExpenseUpdate(SQLModel):
    """Request schema for updating an expense. All fields optional (partial update)."""

    amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    payer_id: uuid.UUID | None = None


class ExpensePublic(SQLModel):
    """Response schema for an expense."""

    id: uuid.UUID
    group_id: uuid.UUID
    amount: Decimal
    description: str
    payer_id: uuid.UUID
    created_by: uuid.UUID
    status: ExpenseStatus
    confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ExpensesPublic(SQLModel):
    """Response schema for list of expenses."""

    data: list[ExpensePublic]
    count: int


# === Split Request/Response Schemas ===


class SplitItem(SQLModel):
    """Individual split item in response."""

    user_id: uuid.UUID
    amount_owed: Decimal


class EqualSplitRequest(SQLModel):
    """Request schema for creating equal split."""

    type: str = "equal"
    excluded_user_ids: list[uuid.UUID] = []


class UnequalSplitItem(SQLModel):
    """Individual split item for unequal split request."""

    user_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class UnequalSplitRequest(SQLModel):
    """Request schema for creating unequal split."""

    type: str = "unequal"
    splits: list[UnequalSplitItem]
    excluded_user_ids: list[uuid.UUID] = []


class PercentageSplitItem(SQLModel):
    """Individual split item for percentage split request."""

    user_id: uuid.UUID
    percentage: Decimal = Field(ge=0, le=100, decimal_places=2)


class PercentageSplitRequest(SQLModel):
    """Request schema for creating percentage split."""

    type: str = "percentage"
    splits: list[PercentageSplitItem]
    excluded_user_ids: list[uuid.UUID] = []


class ExpenseSplitPublic(SQLModel):
    """Response schema for expense split."""

    id: uuid.UUID
    expense_id: uuid.UUID
    user_id: uuid.UUID
    amount_owed: Decimal
    status: SplitStatus
    confirmed_at: datetime | None
    created_at: datetime


class ExpenseSplitResponse(SQLModel):
    """Response schema for split creation/update."""

    expense_id: uuid.UUID
    split_type: str
    splits: list[SplitItem]
    excluded_user_ids: list[uuid.UUID] = []


# === Confirmation Request/Response Schemas (Story 4.2) ===


class ExpenseConfirmRequest(SQLModel):
    """Request schema for confirming an expense split."""

    pass  # No fields needed - expense_id comes from URL path


class ExpenseRejectRequest(SQLModel):
    """Request schema for rejecting an expense split."""

    reason: str | None = Field(default=None, max_length=500)


class PendingConfirmationPublic(SQLModel):
    """Response schema for pending confirmation with expense and split details."""

    expense: ExpensePublic
    split: "ExpenseSplitPublic"


class ExpenseRejectResponse(SQLModel):
    """Response schema for expense rejection."""

    message: str
    remaining_splits: int


# === Audit Log Types and Schemas (Story 4.4) ===


class AuditActionType(str, PyEnum):
    """Types of actions that can be audited."""

    CREATED = "created"
    EDITED = "edited"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    SETTLED = "settled"
    SPLIT_UPDATED = "split_updated"


class AuditLogPublic(SQLModel):
    """Response schema for audit log entries."""

    id: uuid.UUID
    expense_id: uuid.UUID
    user_id: uuid.UUID
    action_type: AuditActionType
    changes_json: dict | None
    created_at: datetime


class AuditLogsPublic(SQLModel):
    """Response schema for paginated audit log entries."""

    data: list[AuditLogPublic]
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
    confirmed_at: datetime | None = None
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

    Unique constraint: One split per user per expense.
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

    # Table constraints
    __table_args__ = (
        sa.UniqueConstraint(
            "expense_id", "user_id", name="uq_expense_user_split"
        ),
    )


class AuditLog(SQLModel, table=True):
    """
    Immutable audit log for all expense-related actions.
    Write-only: No UPDATE or DELETE operations allowed.
    """

    __tablename__ = "audit_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    expense_id: uuid.UUID = Field(
        foreign_key="expense.id", nullable=False, index=True
    )
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    action_type: AuditActionType = Field(nullable=False)
    changes_json: dict | None = Field(default=None, sa_column=sa.Column(sa.JSON))
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    expense: Expense = Relationship()
    user: User = Relationship()
