# Backward compatibility layer - re-exports from feature modules
# This file allows existing imports to continue working during migration
# New code should import directly from app.features.auth.models

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
    TokenPayload,
    NewPassword,
    Message,
    # Item models (temporary - will be moved to expenses feature)
    Item,
    ItemBase,
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)

__all__ = [
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
    "TokenPayload",
    "NewPassword",
    "Message",
    # Item models
    "Item",
    "ItemBase",
    "ItemCreate",
    "ItemPublic",
    "ItemsPublic",
    "ItemUpdate",
]
