# Auth feature models - User and authentication-related schemas
import secrets
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel

from app.core.payment_providers import (
    MAX_HANDLE_LENGTH,
    MAX_LABEL_LENGTH,
    is_supported_provider,
)

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


# === Payment Method Schemas (WS10.2) ===


def _clean_handle(v: str) -> str:
    stripped = v.strip()
    if not stripped:
        raise ValueError("Handle cannot be empty")
    return stripped


def _clean_label(v: str | None) -> str | None:
    if v is None:
        return None
    stripped = v.strip()
    return stripped or None


class PaymentMethodCreate(SQLModel):
    """Register one payment handle (WS10.2).

    `provider` is validated against the supported registry (422 on unknown)
    and lower-cased; `handle` is trimmed and must be non-empty. Validation is
    deliberately permissive on the handle's shape — handle formats differ by
    country, and the settle UI's whole point is frictionless capture.
    """

    provider: str = Field(max_length=20)
    handle: str = Field(min_length=1, max_length=MAX_HANDLE_LENGTH)
    label: str | None = Field(default=None, max_length=MAX_LABEL_LENGTH)

    @field_validator("provider")
    @classmethod
    def _validate_provider(cls, v: str) -> str:
        code = v.lower().strip()
        if not is_supported_provider(code):
            raise ValueError(f"Unsupported payment provider: {v}")
        return code

    @field_validator("handle")
    @classmethod
    def _validate_handle(cls, v: str) -> str:
        return _clean_handle(v)

    @field_validator("label")
    @classmethod
    def _validate_label(cls, v: str | None) -> str | None:
        return _clean_label(v)


class PaymentMethodUpdate(SQLModel):
    """Update a handle's value or label (provider is fixed — delete + re-add
    to change it). Fields optional; send only what changes."""

    handle: str | None = Field(default=None, min_length=1, max_length=MAX_HANDLE_LENGTH)
    label: str | None = Field(default=None, max_length=MAX_LABEL_LENGTH)

    @field_validator("handle")
    @classmethod
    def _validate_handle(cls, v: str | None) -> str | None:
        return None if v is None else _clean_handle(v)

    @field_validator("label")
    @classmethod
    def _validate_label(cls, v: str | None) -> str | None:
        return _clean_label(v)


class PaymentMethodPublic(SQLModel):
    """A payment handle as shown in the UI.

    Used for BOTH the owner's own list and a counterparty's handles surfaced at
    settle time — payment handles are shared with the people who owe you by
    design. `pay_url` is the server-computed deep link (None = copy-only);
    `provider_name` is the display name.
    """

    id: uuid.UUID
    provider: str
    provider_name: str
    handle: str
    label: str | None = None
    pay_url: str | None = None


class PaymentMethodsPublic(SQLModel):
    data: list["PaymentMethodPublic"]
    count: int


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


# Per-user payment handles (WS10.2). GLOBAL, not per-group: a person's Venmo /
# UPI / IBAN is the same wherever they settle. Surfaced to a counterparty at the
# moment they owe money (authorized by shared group membership), so it is NOT
# encrypted — unlike the Gemini key, the whole point is for others to see it.
class PaymentMethod(SQLModel, table=True):
    __tablename__ = "payment_method"
    __table_args__ = (
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "handle",
            name="uq_payment_method_user_provider_handle",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )
    provider: str = Field(max_length=20)
    handle: str = Field(max_length=MAX_HANDLE_LENGTH)
    label: str | None = Field(default=None, max_length=MAX_LABEL_LENGTH)
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=_AWARE_DATETIME,
        sa_column_kwargs={"onupdate": utc_now},
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
