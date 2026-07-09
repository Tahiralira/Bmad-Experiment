# Auth feature router - API routes for authentication and user management
# Consolidates login and user routes from the original api/routes/ directory

import secrets
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import col, delete, func, select
from starlette.requests import Request

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.features.auth.models import (
    Item,
    Message,
    NewPassword,
    Token,
    TokenWithUser,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    MagicLinkRequest,
    AUTH_METHOD_MAGIC_LINK,
    DashboardResponse,
)
from app.features.auth import service as auth_service
from app.core.oauth import oauth, SUPPORTED_PROVIDERS, is_provider_configured
from app.utils import (
    generate_new_account_email,
    generate_magic_link_email,
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

# Main auth router - will be included in api/main.py
router = APIRouter()

# Login router
login_router = APIRouter(tags=["login"])

# Users router
users_router = APIRouter(prefix="/users", tags=["users"])

# Auth router for magic link registration/verification
auth_router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# LOGIN ROUTES
# ============================================================================

@login_router.post("/login/access-token")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = auth_service.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@login_router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@login_router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = auth_service.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@login_router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = auth_service.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@login_router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = auth_service.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )


# ============================================================================
# USER ROUTES
# ============================================================================

@users_router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@users_router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = auth_service.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = auth_service.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@users_router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    if user_in.email:
        existing_user = auth_service.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@users_router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@users_router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@users_router.get("/me/dashboard", response_model=DashboardResponse)
def get_dashboard(
    session: SessionDep,
    current_user: CurrentUser,
) -> DashboardResponse:
    """
    Get the current user's dashboard with group balances.

    Returns all groups the user is a member of with their net balance
    (positive if owed to user, negative if user owes).
    Groups are sorted by most recent activity.
    """
    groups = auth_service.get_user_dashboard(session, current_user.id)
    total_balance = sum((g.net_balance for g in groups), Decimal("0.00"))

    return DashboardResponse(
        groups=groups,
        total_balance=total_balance,
        count=len(groups),
    )


@users_router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own account (soft delete — WS4/C4).

    Expenses and splits are records shared with other people, so the account
    is anonymized (PII scrubbed, login disabled) rather than hard-deleted;
    financial history and the audit trail stay intact. Deletion is blocked
    while the user still has unsettled expenses.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    if auth_service.has_unsettled_obligations(session, current_user.id):
        raise HTTPException(
            status_code=409,
            detail="You still have unsettled expenses. Settle up with your "
            "groups before deleting your account.",
        )
    auth_service.soft_delete_user(session, current_user)
    session.commit()
    return Message(
        message="Account deleted. Your personal data has been removed; "
        "settled expense history is kept for your groups' records."
    )


@users_router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = auth_service.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = auth_service.create_user(session=session, user_create=user_create)
    return user


@users_router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user is not None and user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    # 404 guard (WS4/M9): returning None made response validation 500
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@users_router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = auth_service.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = auth_service.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@users_router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user (soft delete — WS4/C4).

    Same semantics as self-deletion: anonymize + disable login, keep shared
    financial records, refuse while the user has unsettled expenses.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    if auth_service.has_unsettled_obligations(session, user.id):
        raise HTTPException(
            status_code=409,
            detail="User still has unsettled expenses and cannot be deleted.",
        )
    statement = delete(Item).where(col(Item.owner_id) == user_id)
    session.exec(statement)  # type: ignore
    auth_service.soft_delete_user(session, user)
    session.commit()
    return Message(message="User deleted successfully")


# ============================================================================
# MAGIC LINK AUTH ROUTES
# ============================================================================


@auth_router.post("/register", response_model=Message)
def request_magic_link(session: SessionDep, body: MagicLinkRequest) -> Message:
    """
    Request a magic link for passwordless registration.

    Generates a magic link token and sends it to the user's email.
    Returns a generic success message regardless of whether the email exists
    (to prevent email enumeration attacks).

    Rate limited to 3 requests per email per hour.
    """
    # Check if user already exists
    existing_user = auth_service.get_user_by_email(session=session, email=body.email)
    if existing_user:
        # User already exists - still return success message for security
        # (prevents email enumeration)
        return Message(
            message="If an account exists or can be created, we've sent a magic link"
        )

    # Check rate limiting
    if auth_service.is_rate_limited(session=session, email=body.email):
        # Return same message to prevent enumeration, but don't create token
        return Message(
            message="If an account exists or can be created, we've sent a magic link"
        )

    # Generate magic link token (returns tuple of token object and raw token)
    _, raw_token = auth_service.generate_magic_link_token(session=session, email=body.email)

    # Send email with magic link (use raw_token for the URL, not hashed)
    if settings.emails_enabled:
        email_data = generate_magic_link_email(
            email_to=body.email,
            token=raw_token,
            valid_minutes=auth_service.MAGIC_LINK_EXPIRE_MINUTES,
        )
        send_email(
            email_to=body.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )

    return Message(
        message="If an account exists or can be created, we've sent a magic link"
    )


@auth_router.get("/verify/{token}", response_model=TokenWithUser)
def verify_magic_link(session: SessionDep, token: str) -> TokenWithUser:
    """
    Verify a magic link token and create the user account.

    If the token is valid:
    - Creates a new user account (passwordless)
    - Marks the token as used
    - Returns a JWT access token for the user
    """
    # Verify token
    magic_token = auth_service.verify_magic_link_token(session=session, token_str=token)

    if not magic_token:
        # Token doesn't exist or is expired
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token. Please request a new magic link."
        )

    # Check if user already exists (shouldn't happen normally, but handle edge case)
    existing_user = auth_service.get_user_by_email(session=session, email=magic_token.email)
    if existing_user:
        # Mark token as used
        auth_service.mark_token_as_used(session=session, token=magic_token)
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists. Please log in."
        )

    # Create passwordless user with random placeholder password
    placeholder_password = secrets.token_urlsafe(32)
    user = User(
        email=magic_token.email,
        hashed_password=get_password_hash(placeholder_password),
        auth_method=AUTH_METHOD_MAGIC_LINK,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Mark token as used
    auth_service.mark_token_as_used(session=session, token=magic_token)

    # Generate JWT access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    return TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


# ============================================================================
# LOGIN MAGIC LINK ROUTES (Story 1.5)
# ============================================================================


@auth_router.post("/login", response_model=Message)
def request_login_magic_link(session: SessionDep, body: MagicLinkRequest) -> Message:
    """
    Request a magic link for passwordless login.

    Only works for registered users. Returns generic message
    regardless of whether email exists (prevents enumeration).

    Rate limited to 3 requests per email per hour.
    """
    # Check if user exists
    existing_user = auth_service.get_user_by_email(session=session, email=body.email)

    if not existing_user:
        # User doesn't exist - return same message for security
        return Message(
            message="If an account exists, we've sent a magic login link"
        )

    # Check if user is active
    if not existing_user.is_active:
        return Message(
            message="If an account exists, we've sent a magic login link"
        )

    # Check rate limiting
    if auth_service.is_rate_limited(session=session, email=body.email):
        return Message(
            message="If an account exists, we've sent a magic login link"
        )

    # Generate magic link token
    _, raw_token = auth_service.generate_magic_link_token(session=session, email=body.email)

    # Send email with magic link (is_login=True for login flow)
    if settings.emails_enabled:
        email_data = generate_magic_link_email(
            email_to=body.email,
            token=raw_token,
            valid_minutes=auth_service.MAGIC_LINK_EXPIRE_MINUTES,
            is_login=True,
        )
        send_email(
            email_to=body.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )

    return Message(message="If an account exists, we've sent a magic login link")


@auth_router.get("/login/verify/{token}", response_model=TokenWithUser)
def verify_login_magic_link(session: SessionDep, token: str) -> TokenWithUser:
    """
    Verify a login magic link token.

    Unlike registration verification, this does NOT create a user.
    User must already exist. Returns JWT with 30-day expiration per PRD.
    """
    # Verify token
    magic_token = auth_service.verify_magic_link_token(session=session, token_str=token)

    if not magic_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token. Please request a new login link."
        )

    # Get existing user (MUST exist for login)
    user = auth_service.get_user_by_email(session=session, email=magic_token.email)
    if not user:
        auth_service.mark_token_as_used(session=session, token=magic_token)
        raise HTTPException(
            status_code=404,
            detail="Account not found. Please register first."
        )

    if not user.is_active:
        auth_service.mark_token_as_used(session=session, token=magic_token)
        raise HTTPException(
            status_code=400,
            detail="Account is deactivated."
        )

    # Mark token as used
    auth_service.mark_token_as_used(session=session, token=magic_token)

    # Generate JWT with 30-day expiration (PRD "Walled Garden")
    access_token_expires = timedelta(days=settings.LOGIN_TOKEN_EXPIRE_DAYS)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    return TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


# ============================================================================
# OAUTH ROUTES (Story 1.6)
# ============================================================================


@auth_router.get("/oauth/{provider}/login")
async def oauth_login(request: Request, provider: str) -> RedirectResponse:
    """
    Initiate OAuth login flow for the specified provider.
    Redirects user to provider's consent screen.

    Supported providers: google, github
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported OAuth provider: {provider}. Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    if not is_provider_configured(provider):
        raise HTTPException(
            status_code=503,
            detail=f"OAuth provider '{provider}' is not configured. Please set the required environment variables."
        )

    # Build callback URL
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/oauth/{provider}/callback"

    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)


@auth_router.get("/oauth/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: str,
    session: SessionDep,
) -> RedirectResponse:
    """
    Handle OAuth callback from provider.
    Exchanges authorization code for token, creates/links user, returns JWT.
    Redirects to frontend with token in query parameter.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported OAuth provider: {provider}"
        )

    if not is_provider_configured(provider):
        raise HTTPException(
            status_code=503,
            detail=f"OAuth provider '{provider}' is not configured"
        )

    client = oauth.create_client(provider)

    try:
        token = await client.authorize_access_token(request)
    except Exception as e:
        # Redirect to frontend with error
        error_url = f"{settings.FRONTEND_HOST}/auth/callback?error=oauth_failed&message={str(e)}"
        return RedirectResponse(url=error_url)

    # Extract user info based on provider
    email: str | None = None
    full_name: str | None = None
    provider_id: str | None = None

    if provider == "google":
        # Google returns userinfo in the token for OpenID Connect
        user_info = token.get("userinfo")
        if not user_info:
            # Fallback to fetching userinfo separately
            resp = await client.get("userinfo")
            user_info = resp.json()
        email = user_info.get("email")
        full_name = user_info.get("name")
        provider_id = user_info.get("sub")  # Google's unique user ID

    elif provider == "github":
        # GitHub requires separate API calls
        resp = await client.get("user")
        user_info = resp.json()
        provider_id = str(user_info.get("id"))
        full_name = user_info.get("name") or user_info.get("login")

        # GitHub may not include email in profile - need separate call
        email = user_info.get("email")
        if not email:
            emails_resp = await client.get("user/emails")
            emails = emails_resp.json()
            # Find primary verified email
            for e in emails:
                if e.get("primary") and e.get("verified"):
                    email = e.get("email")
                    break

    if not email:
        error_url = f"{settings.FRONTEND_HOST}/auth/callback?error=no_email&message=Could not retrieve email from OAuth provider"
        return RedirectResponse(url=error_url)

    if not provider_id:
        error_url = f"{settings.FRONTEND_HOST}/auth/callback?error=no_provider_id&message=Could not retrieve user ID from OAuth provider"
        return RedirectResponse(url=error_url)

    # Find or create user (handles account linking)
    user = auth_service.find_or_create_oauth_user(
        session=session,
        email=email,
        full_name=full_name,
        provider=provider,
        provider_id=provider_id
    )

    if not user.is_active:
        error_url = f"{settings.FRONTEND_HOST}/auth/callback?error=inactive&message=Account is deactivated"
        return RedirectResponse(url=error_url)

    # Generate JWT with 30-day expiration (PRD "Walled Garden")
    access_token_expires = timedelta(days=settings.LOGIN_TOKEN_EXPIRE_DAYS)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    # Redirect to frontend with token
    frontend_callback_url = f"{settings.FRONTEND_HOST}/auth/callback?token={access_token}"
    return RedirectResponse(url=frontend_callback_url)


# Include sub-routers into main auth router
router.include_router(login_router)
router.include_router(users_router)
router.include_router(auth_router)
