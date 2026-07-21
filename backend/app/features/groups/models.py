# Groups feature models - ExpenseGroup, GroupMember, GroupInvite, and related schemas
import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal, Optional

import sqlalchemy as sa
from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.core.currency import DEFAULT_CURRENCY, is_supported_currency
from app.features.auth.models import User, utc_now

# Timezone-aware timestamps to match the migrations (WS5/B-H9 reconcile)
_AWARE_DATETIME = sa.DateTime(timezone=True)


# === Request/Response Schemas ===


class ExpenseGroupCreate(SQLModel):
    """Request schema for creating a group."""

    name: str = Field(min_length=1, max_length=100)
    # WS10.1: the client passes a locale-detected ISO-4217 currency so a new
    # group starts in a sensible currency (editable in settings). Optional —
    # omitted/invalid falls back to the default via the service.
    currency: str | None = Field(default=None, max_length=3)


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


class ExpenseGroupDetail(ExpenseGroupWithMembers):
    """Response schema for the group detail screen (WS5/B-H7).

    net_balance is the requesting user's balance in this group, computed the
    same way as the dashboard: positive = owed to the user, negative = user
    owes. Decimal to the wire (serialized as a string, e.g. "12.50")."""

    net_balance: Decimal = Decimal("0.00")
    # WS10.1: the group's ISO-4217 currency — every amount in this group is in
    # it, so the whole ledger screen renders through one code.
    currency: str = DEFAULT_CURRENCY


# === Member Schemas ===


class GroupMemberPublic(SQLModel):
    """Response schema for a group member with user details."""

    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    full_name: str | None
    email: str


class GroupMembersListResponse(SQLModel):
    """Response schema for list of group members."""

    members: list[GroupMemberPublic]
    count: int


# === Invite Schemas ===


class GroupInviteCreate(SQLModel):
    """Request schema for creating an invite (WS8/S5-M4: capped usage)."""

    max_uses: int = Field(default=10, ge=1, le=100)


class GroupInvitePublic(SQLModel):
    """Response schema for a group invite."""

    id: uuid.UUID
    group_id: uuid.UUID
    token: str
    expires_at: datetime
    created_at: datetime
    max_uses: int
    use_count: int
    revoked_at: datetime | None = None
    invite_url: str | None = None  # Computed field


class GroupInviteResponse(SQLModel):
    """Response after creating or accepting an invite."""

    invite: GroupInvitePublic | None = None
    group: ExpenseGroupPublic | None = None
    message: str


class GroupInvitesPublic(SQLModel):
    """Owner-facing list of a group's invites (for revocation)."""

    data: list[GroupInvitePublic]
    count: int


class InvitePreview(SQLModel):
    """What an invited person sees BEFORE joining (WS8/S5-M4; public in WS10.3).

    Accepting used to be a state-changing GET — any link prefetcher could
    join a group. Now GET shows this preview and joining is an explicit POST
    from the landing page. WS10.3 makes this preview PUBLIC (no auth): a
    logged-out invitee sees the group before deciding to sign in, so
    `already_member` is only meaningful when a caller is authenticated
    (False for anonymous visitors).
    """

    group_id: uuid.UUID
    group_name: str
    member_count: int
    expires_at: datetime
    already_member: bool
    # WS10.3: "<inviter> invited you to <group>" on the public landing page.
    inviter_name: str | None = None


# === Database Models ===


class ExpenseGroup(SQLModel, table=True):
    """
    Expense group for organizing shared expenses among members.
    """

    __tablename__ = "expense_group"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    created_by: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=_AWARE_DATETIME,
        sa_column_kwargs={"onupdate": utc_now},
    )

    # Relationships
    creator: User = Relationship()
    members: list["GroupMember"] = Relationship(
        back_populates="group", cascade_delete=True
    )
    settings: Optional["GroupSettings"] = Relationship(back_populates="group")


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
        foreign_key="expense_group.id", nullable=False, index=True,
        ondelete="CASCADE",
    )
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )
    role: str = Field(default=GROUP_ROLE_MEMBER, max_length=20)
    joined_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)

    # Relationships
    group: ExpenseGroup = Relationship(back_populates="members")
    user: User = Relationship()


# Invite expiration constant (30 days)
INVITE_EXPIRATION_DAYS = 30


# === AI Personality Settings ===


# AI personalities a group may choose. Capped at "funny" (WS7/UX-H5): the
# f3-pbs roast mode was removed before it ever had a write path — an
# "agentic mediator" that mocks users about money is a brand liability.
ALLOWED_AI_PERSONALITIES = ("professional", "friendly", "funny")


class GroupSettingsPublic(SQLModel):
    """Response schema for group settings (WS6 strict mode + WS7 personality
    + WS10.1 currency)."""

    group_id: uuid.UUID
    strict_mode: bool
    ai_personality: str
    currency: str


class GroupSettingsUpdate(SQLModel):
    """Request schema for updating group settings (owner only).

    All fields optional — send only what changes (exclude_unset semantics).
    """

    strict_mode: bool | None = None
    ai_personality: Literal["professional", "friendly", "funny"] | None = None
    # WS10.1: ISO-4217 currency. Validated against the supported set (422 on an
    # unknown code) and uppercased so "usd" and "USD" both work.
    currency: str | None = None

    @field_validator("currency")
    @classmethod
    def _validate_currency(cls, v: str | None) -> str | None:
        if v is None:
            return None
        upper = v.upper()
        if not is_supported_currency(upper):
            raise ValueError(f"Unsupported currency code: {v}")
        return upper


class GroupSettings(SQLModel, table=True):
    """
    AI personality and other group-specific settings.

    Stores per-group configuration for AI features,
    such as personality mode for expense parsing commentary.

    strict_mode (WS6): when True, every participant must explicitly confirm
    an expense (the original Epic 4 workflow). When False (the default),
    confirmation is opt-in — expenses auto-confirm after
    EXPENSE_AUTO_CONFIRM_DAYS unless someone rejects first.
    """

    __tablename__ = "group_settings"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(
        foreign_key="expense_group.id", unique=True, index=True, ondelete="CASCADE"
    )
    ai_personality: str = Field(default="friendly", index=True)
    strict_mode: bool = Field(default=False)
    # WS10.1: per-group ISO-4217 currency (global market). Every amount in the
    # group is denominated in it.
    currency: str = Field(default=DEFAULT_CURRENCY, max_length=3)
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=_AWARE_DATETIME,
        sa_column_kwargs={"onupdate": utc_now},
    )

    # Relationship
    group: ExpenseGroup = Relationship(back_populates="settings")


class GroupInvite(SQLModel, table=True):
    """
    Invite tokens for joining expense groups via shareable links.

    Multi-use up to max_uses (WS8/S5-M4 — a leaked link is no longer an
    unlimited door), revocable by the owner, and expiring after 30 days.
    """

    __tablename__ = "group_invite"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(
        foreign_key="expense_group.id", nullable=False, index=True,
        ondelete="CASCADE",
    )
    token: str = Field(unique=True, index=True, max_length=64)
    expires_at: datetime = Field(sa_type=_AWARE_DATETIME)
    max_uses: int = Field(default=10)
    use_count: int = Field(default=0)
    revoked_at: datetime | None = Field(default=None, sa_type=_AWARE_DATETIME)
    created_by: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)

    # Relationships
    group: ExpenseGroup = Relationship()

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
