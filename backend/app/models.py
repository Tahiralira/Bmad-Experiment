# Backward compatibility layer - re-exports from feature modules
# This file allows existing imports to continue working during migration
# New code should import directly from app.features.auth.models

from sqlmodel import SQLModel

from app.features.auth.models import (
    # User models
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    # Auth models
    Token,
    TokenWithUser,
    TokenPayload,
    Message,
    # Magic link models
    MagicLinkToken,
    MagicLinkRequest,
    # Session security models (WS8)
    LoginCode,
    RevokedToken,
    # Payment methods (WS10.2)
    PaymentMethod,
    # Auth method constants
    AUTH_METHOD_PASSWORD,
    AUTH_METHOD_MAGIC_LINK,
    AUTH_METHOD_OAUTH,
)

__all__ = [
    # SQLModel for alembic
    "SQLModel",
    # User models
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
    # Auth models
    "Token",
    "TokenWithUser",
    "TokenPayload",
    "Message",
    # Magic link models
    "MagicLinkToken",
    "MagicLinkRequest",
    # Session security models (WS8)
    "LoginCode",
    "RevokedToken",
    # Payment methods (WS10.2)
    "PaymentMethod",
    # Auth method constants
    "AUTH_METHOD_PASSWORD",
    "AUTH_METHOD_MAGIC_LINK",
    "AUTH_METHOD_OAUTH",
]

# Register ALL feature models with SQLModel metadata. Prestart (initial_data),
# alembic/env.py, and tests rely on "import app.models" loading the complete
# schema — without these, mapper configuration fails on cross-feature
# relationships (e.g. User.expense_splits -> ExpenseSplit) and Alembic
# autogenerate is blind to every feature table.
from app.features.groups import models as _groups_models  # noqa: E402,F401
from app.features.expenses import models as _expenses_models  # noqa: E402,F401
from app.features.ai import models as _ai_models  # noqa: E402,F401
from app.features.notifications import models as _notifications_models  # noqa: E402,F401
