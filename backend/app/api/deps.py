import uuid
from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User

# The tokenUrl is OpenAPI-docs cosmetics only — bearer extraction works
# regardless. There is no password token endpoint anymore (WS8); tokens come
# from magic-link verification or the OAuth code exchange.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/oauth/exchange"
)

# Optional variant (WS10.3): a public endpoint that PERSONALIZES when a token
# is present but never rejects when it isn't. auto_error=False returns None
# instead of raising 401 on a missing Authorization header.
optional_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/oauth/exchange",
    auto_error=False,
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        # jti is mandatory (WS8/S5-H1): a token that can't be revoked is not
        # a valid session. Pre-WS8 tokens (no jti) are rejected wholesale.
        jti = uuid.UUID(token_data.jti) if token_data.jti else None
    except (InvalidTokenError, ValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    if jti is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    # Revocation check (logout / compromised-token kill switch). One indexed
    # PK lookup per request, alongside the user load below.
    from app.features.auth import service as auth_service

    if auth_service.is_token_revoked(session, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This session has been signed out. Please log in again.",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_user_optional(
    session: SessionDep,
    token: Annotated[str | None, Depends(optional_oauth2)],
) -> User | None:
    """Resolve the user if a valid token is present, else None (never raises).

    For public endpoints that personalize output for a signed-in caller (WS10.3
    invite preview: 'already a member?'). Any auth problem — no token, bad
    token, revoked, missing/inactive user — resolves to None, so an anonymous
    visitor and a broken token both just get the public view.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        jti = uuid.UUID(token_data.jti) if token_data.jti else None
    except (InvalidTokenError, ValidationError, ValueError):
        return None
    if jti is None:
        return None
    from app.features.auth import service as auth_service

    if auth_service.is_token_revoked(session, jti):
        return None
    user = session.get(User, token_data.sub)
    if not user or not user.is_active:
        return None
    return user


OptionalCurrentUser = Annotated[User | None, Depends(get_current_user_optional)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
