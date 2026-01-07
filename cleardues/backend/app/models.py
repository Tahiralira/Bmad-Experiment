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
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    UpdatePassword,
    # Auth models
    Token,
    TokenWithUser,
    TokenPayload,
    NewPassword,
    Message,
    # Magic link models
    MagicLinkToken,
    MagicLinkRequest,
    # Auth method constants
    AUTH_METHOD_PASSWORD,
    AUTH_METHOD_MAGIC_LINK,
    AUTH_METHOD_OAUTH,
    # Item models (temporary - will be moved to expenses feature)
    Item,
    ItemBase,
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)

__all__ = [
    # SQLModel for alembic
    "SQLModel",
    # User models
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
    "UserRegister",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
    "UpdatePassword",
    # Auth models
    "Token",
    "TokenWithUser",
    "TokenPayload",
    "NewPassword",
    "Message",
    # Magic link models
    "MagicLinkToken",
    "MagicLinkRequest",
    # Auth method constants
    "AUTH_METHOD_PASSWORD",
    "AUTH_METHOD_MAGIC_LINK",
    "AUTH_METHOD_OAUTH",
    # Item models
    "Item",
    "ItemBase",
    "ItemCreate",
    "ItemPublic",
    "ItemsPublic",
    "ItemUpdate",
]
