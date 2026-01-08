# Groups feature models - ExpenseGroup, GroupMember, and related schemas
import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

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
    updated_at: datetime = Field(
        default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now}
    )

    # Relationships
    creator: User = Relationship()
    members: list["GroupMember"] = Relationship(
        back_populates="group", cascade_delete=True
    )


# Role constants
GROUP_ROLE_OWNER = "owner"
GROUP_ROLE_MEMBER = "member"


class GroupMember(SQLModel, table=True):
    """
    Join table tracking user membership in expense groups.
    """

    __tablename__ = "group_member"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member_group_user"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(
        foreign_key="expense_group.id", nullable=False, index=True
    )
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    role: str = Field(default=GROUP_ROLE_MEMBER, max_length=20)
    joined_at: datetime = Field(default_factory=utc_now)

    # Relationships
    group: ExpenseGroup = Relationship(back_populates="members")
    user: User = Relationship()
