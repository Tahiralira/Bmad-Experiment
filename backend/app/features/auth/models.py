# Auth feature models - User and authentication-related schemas
import secrets
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

# Timezone-aware timestamps to match the migrations (WS5/B-H9 reconcile)
_AWARE_DATETIME = sa.DateTime(timezone=True)

# Avoid circular imports - ExpenseSplit is only used for type hints
if TYPE_CHECKING:
    from app.features.expenses.models import ExpenseSplit


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive on user creation. The password is a bootstrap-only
# concept (superuser seed + test fixtures) — there is NO password login
# endpoint (WS8 deleted the template's parallel password-auth stack).
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class ApiKeyUpdate(SQLModel):
    """BYOK (WS7): the user's own Gemini API key. Never returned by any API."""

    api_key: str = Field(min_length=20, max_length=200)


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
    # BYOK Gemini key (WS7: hidden power-user escape hatch — hosted AI is
    # the default). Encrypted at rest with Fernet (AES-128-CBC + HMAC) under
    # the dedicated ENCRYPTION_KEY — see app/core/security.py.
    gemini_api_key_encrypted: str | None = Field(
        default=None,
        max_length=512,
        description="User's own Gemini API key, Fernet-encrypted at rest",
    )
    # Soft-delete marker (WS4/C4): users with financial history are never
    # hard-deleted — PII is anonymized and login disabled, financial rows stay.
    deleted_at: datetime | None = Field(default=None, sa_type=_AWARE_DATETIME)
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=_AWARE_DATETIME,
        sa_column_kwargs={"onupdate": utc_now},
    )
    expense_splits: list["ExpenseSplit"] = Relationship(back_populates="user")

    # Composite unique index from the OAuth migration (declared here so
    # alembic autogenerate sees it — WS5/B-H9 reconcile)
    __table_args__ = (
        sa.Index(
            "ix_user_oauth_provider_id",
            "oauth_provider",
            "oauth_provider_id",
            unique=True,
        ),
    )


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
    expires_at: datetime = Field(sa_type=_AWARE_DATETIME)
    used_at: datetime | None = Field(default=None, sa_type=_AWARE_DATETIME)
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)

    @classmethod
    def generate_token(cls) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(32)


# Schema for magic link registration request
class MagicLinkRequest(SQLModel):
    """Request schema for magic link registration."""
    email: EmailStr = Field(max_length=255)


# One-time login code for OAuth token delivery (WS8/S5-H1).
# The OAuth callback used to put the 30-day JWT itself in the redirect URL —
# straight into access logs, browser history, and Referer headers. Now the
# redirect carries only a short-lived single-use code; the frontend exchanges
# it for the JWT via POST, so the long-lived credential never rides a URL.
class LoginCode(SQLModel, table=True):
    __tablename__ = "login_code"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )
    # SHA-256 of the raw code, same at-rest discipline as magic-link tokens
    code_hash: str = Field(unique=True, index=True, max_length=64)
    expires_at: datetime = Field(sa_type=_AWARE_DATETIME)
    used_at: datetime | None = Field(default=None, sa_type=_AWARE_DATETIME)
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)


class LoginCodeExchange(SQLModel):
    """Request schema for exchanging a one-time OAuth login code for a JWT."""

    code: str = Field(min_length=16, max_length=128)


# Server-side JWT revocation (WS8/S5-H1): every access token carries a `jti`;
# a revoked jti is rejected by get_current_user until the token would have
# expired anyway (expires_at marks when the row can be purged).
class RevokedToken(SQLModel, table=True):
    __tablename__ = "revoked_token"

    jti: uuid.UUID = Field(primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )
    expires_at: datetime = Field(sa_type=_AWARE_DATETIME)
    revoked_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)


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
    jti: str | None = None


# === Dashboard Schemas (Story 2.4) ===


class GroupBalanceSummary(SQLModel):
    """Summary of a group with net balance for dashboard display.

    Balances are Decimal end-to-end (WS4/M1): the core tables store
    Numeric(10,2) and converting to float at the API edge reintroduced the
    representation drift the schema exists to prevent. Serializes as a JSON
    string (e.g. "12.50"), same as every other monetary field.
    """

    group_id: uuid.UUID
    group_name: str
    net_balance: Decimal  # Positive = owed to user, negative = user owes
    last_activity: datetime
    member_count: int
    # WS10.1: the group's ISO-4217 currency — the dashboard spans groups, so
    # each row renders in its own currency.
    currency: str = "USD"


class DashboardResponse(SQLModel):
    """Response schema for user dashboard."""

    groups: list[GroupBalanceSummary]
    total_balance: Decimal  # Sum of all net_balances
    count: int  # Number of groups
    # WS10.1: the shared currency when every group uses the same one, else None.
    # total_balance is only meaningful when this is set — the frontend hides the
    # aggregate hero and relies on per-group rows when groups span currencies
    # (summing across currencies has no meaning).
    currency: str | None = None
