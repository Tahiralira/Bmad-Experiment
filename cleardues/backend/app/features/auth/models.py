# Auth feature models - User and authentication-related schemas
import secrets
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

# Avoid circular imports - ExpenseSplit is only used for type hints
if TYPE_CHECKING:
    from app.features.expenses.models import ExpenseSplit


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Helper function for UTC timestamp
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Authentication methods
AUTH_METHOD_PASSWORD = "password"
AUTH_METHOD_MAGIC_LINK = "magic_link"
AUTH_METHOD_OAUTH = "oauth"


# Database model, database table inferred from class name
class User(UserBase, table=True):
    __tablename__ = "user"  # Explicit table name (singular, not plural per architecture.md)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str  # For magic_link users, this is a random placeholder
    auth_method: str = Field(default=AUTH_METHOD_PASSWORD, max_length=20)
    # OAuth fields
    oauth_provider: str | None = Field(default=None, max_length=50)
    oauth_provider_id: str | None = Field(default=None, max_length=255)
    # AI API key field (encrypted at rest per NFR4)
    gemini_api_key_encrypted: str | None = Field(
        default=None,
        max_length=512,
        description="Encrypted Gemini API key for this user (AES-256)",
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    expense_splits: list["ExpenseSplit"] = Relationship(back_populates="user")


# Magic link token for passwordless authentication
class MagicLinkToken(SQLModel, table=True):
    """
    Stores one-time use magic link tokens for passwordless registration/login.
    Tokens are stored in database (not JWT) to allow immediate invalidation.
    """
    __tablename__ = "magic_link_token"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, max_length=255)
    token: str = Field(unique=True, index=True, max_length=64)
    expires_at: datetime
    used_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def generate_token(cls) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(32)


# Schema for magic link registration request
class MagicLinkRequest(SQLModel):
    """Request schema for magic link registration."""
    email: EmailStr = Field(max_length=255)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Token response with user info for magic link verification
class TokenWithUser(Token):
    """Token response that includes user information after magic link verification."""
    user: "UserPublic"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# Item model - temporarily kept here for backward compatibility
# Will be moved to expenses feature in future stories
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# === Dashboard Schemas (Story 2.4) ===


class GroupBalanceSummary(SQLModel):
    """Summary of a group with net balance for dashboard display."""

    group_id: uuid.UUID
    group_name: str
    net_balance: float  # Positive = owed to user, negative = user owes
    last_activity: datetime
    member_count: int


class DashboardResponse(SQLModel):
    """Response schema for user dashboard."""

    groups: list[GroupBalanceSummary]
    total_balance: float  # Sum of all net_balances
    count: int  # Number of groups
