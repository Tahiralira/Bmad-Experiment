# Backward compatibility layer - re-exports from feature modules
# This file allows existing imports to continue working during migration
# New code should import directly from app.features.auth.service

from app.features.auth.service import (
    create_user,
    update_user,
    get_user_by_email,
    authenticate,
    create_item,
)

__all__ = [
    "create_user",
    "update_user",
    "get_user_by_email",
    "authenticate",
    "create_item",
]
