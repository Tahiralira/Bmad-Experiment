# Auth feature router - API routes for authentication and user management
#
# WS8 (template purge): the FastAPI template's parallel password-auth stack is
# GONE — no /login/access-token, /password-recovery, /reset-password,
# /users/signup, /users/me/password, and no superuser user-management CRUD.
# ClearDues is passwordless: magic links and OAuth are the only ways in.

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import jwt
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from app.api.deps import (
    CurrentUser,
    SessionDep,
    TokenDep,
)
from app.core import security
from app.core.config import settings
from app.core.limiter import AUTH_LIMIT, limiter
from app.core.oauth import oauth, SUPPORTED_PROVIDERS, is_provider_configured
from app.core.security import get_password_hash
from app.features.auth.models import (
    ApiKeyUpdate,
    LoginCodeExchange,
    Message,
    TokenWithUser,
    User,
    UserPublic,
    UserUpdateMe,
    MagicLinkRequest,
    AUTH_METHOD_MAGIC_LINK,
    DashboardResponse,
)
from app.features.auth import service as auth_service
from app.utils import generate_magic_link_email, send_email

logger = logging.getLogger(__name__)

# Main auth router - will be included in api/main.py
router = APIRouter()

# Users router
users_router = APIRouter(prefix="/users", tags=["users"])

# Auth router for magic link registration/verification + OAuth
auth_router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# USER ROUTES (self-service only — the admin CRUD died with the template)
# ============================================================================


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


@users_router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@users_router.put("/me/api-key", response_model=Message)
def set_my_api_key(
    *, session: SessionDep, body: ApiKeyUpdate, current_user: CurrentUser
) -> Message:
    """
    Store the user's own Gemini API key (BYOK — WS7).

    Advanced escape hatch, deliberately absent from onboarding: hosted AI is
    the default. Parses with a stored key bypass the monthly free quota.
    The key is Fernet-encrypted at rest and never returned by any endpoint.
    """
    current_user.gemini_api_key_encrypted = security.encrypt_api_key(body.api_key)
    session.add(current_user)
    session.commit()
    return Message(message="API key saved. Your parses now use your own key.")


@users_router.delete("/me/api-key", response_model=Message)
def delete_my_api_key(
    *, session: SessionDep, current_user: CurrentUser
) -> Message:
    """
    Remove the user's stored Gemini API key (back to hosted AI).
    """
    current_user.gemini_api_key_encrypted = None
    session.add(current_user)
    session.commit()
    return Message(message="API key removed. Your parses now use the free tier.")


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

    # WS10.1: total_balance only makes sense in a single currency. Expose the
    # shared currency when every group agrees; None signals the frontend to
    # hide the aggregate hero and render per-group rows instead.
    currencies = {g.currency for g in groups}
    shared_currency = currencies.pop() if len(currencies) == 1 else None

    return DashboardResponse(
        groups=groups,
        total_balance=total_balance,
        count=len(groups),
        currency=shared_currency,
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


# ============================================================================
# MAGIC LINK AUTH ROUTES
# ============================================================================


@auth_router.post("/register", response_model=Message)
@limiter.limit(AUTH_LIMIT)
def request_magic_link(
    request: Request, session: SessionDep, body: MagicLinkRequest
) -> Message:
    """
    Request a magic link for passwordless registration.

    Generates a magic link token and sends it to the user's email.
    Returns a generic success message regardless of whether the email exists
    (to prevent email enumeration attacks).

    Rate limited per email (3/hour) and per IP (WS8/S5-H2).
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
@limiter.limit(AUTH_LIMIT)
def verify_magic_link(
    request: Request, session: SessionDep, token: str
) -> TokenWithUser:
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
@limiter.limit(AUTH_LIMIT)
def request_login_magic_link(
    request: Request, session: SessionDep, body: MagicLinkRequest
) -> Message:
    """
    Request a magic link for passwordless login.

    Only works for registered users. Returns generic message
    regardless of whether email exists (prevents enumeration).

    Rate limited per email (3/hour) and per IP (WS8/S5-H2).
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
@limiter.limit(AUTH_LIMIT)
def verify_login_magic_link(
    request: Request, session: SessionDep, token: str
) -> TokenWithUser:
    """
    Verify a login magic link token.

    Unlike registration verification, this does NOT create a user.
    User must already exist. Returns a revocable JWT
    (LOGIN_TOKEN_EXPIRE_DAYS).
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

    # Long-lived login JWT (revocable via jti — WS8/S5-H1)
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
# SESSION MANAGEMENT (WS8/S5-H1)
# ============================================================================


@auth_router.post("/logout", response_model=Message)
def logout(
    session: SessionDep, token: TokenDep, current_user: CurrentUser
) -> Message:
    """
    Revoke the current access token server-side.

    Clearing localStorage alone leaves the JWT valid until expiry; this adds
    its jti to the revocation list so the token is dead everywhere.
    """
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
    )
    auth_service.revoke_token(
        session,
        jti=uuid.UUID(payload["jti"]),
        user_id=current_user.id,
        expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    )
    session.commit()
    return Message(message="Signed out. That session can't be used again.")


# ============================================================================
# OAUTH ROUTES (Story 1.6; token delivery reworked in WS8/S5-H1)
# ============================================================================


def _oauth_error_redirect(error_code: str) -> RedirectResponse:
    """Redirect to the frontend with a generic error CODE only (S5-M2):
    exception text never rides a URL — details go to the server log."""
    return RedirectResponse(
        url=f"{settings.FRONTEND_HOST}/auth/callback?error={error_code}"
    )


@auth_router.get("/oauth/{provider}/login")
@limiter.limit(AUTH_LIMIT)
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
@limiter.limit(AUTH_LIMIT)
async def oauth_callback(
    request: Request,
    provider: str,
    session: SessionDep,
) -> RedirectResponse:
    """
    Handle OAuth callback from provider.

    Exchanges the authorization code for provider tokens, creates/links the
    user, then redirects to the frontend with a SHORT-LIVED ONE-TIME CODE —
    never the JWT itself (WS8/S5-H1: query strings land in access logs,
    history, and Referer headers). The frontend swaps the code for the JWT
    at POST /auth/oauth/exchange.
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
    except Exception:
        logger.exception("OAuth token exchange failed for provider %s", provider)
        return _oauth_error_redirect("oauth_failed")

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
        # S5-M3: never link an OAuth identity to an account via an email the
        # provider hasn't verified — that's a silent account-takeover path.
        # (GitHub's branch below already selects only verified emails.)
        if user_info.get("email_verified") is not True:
            logger.warning("Google OAuth login with unverified email rejected")
            return _oauth_error_redirect("email_unverified")
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
        return _oauth_error_redirect("no_email")

    if not provider_id:
        return _oauth_error_redirect("no_provider_id")

    # Find or create user (handles account linking)
    user = auth_service.find_or_create_oauth_user(
        session=session,
        email=email,
        full_name=full_name,
        provider=provider,
        provider_id=provider_id
    )

    if not user.is_active:
        return _oauth_error_redirect("inactive")

    # One-time code instead of the JWT (WS8/S5-H1): 2-minute, single-use,
    # hashed at rest. The frontend exchanges it immediately via POST.
    login_code = auth_service.create_login_code(session, user.id)
    session.commit()

    return RedirectResponse(
        url=f"{settings.FRONTEND_HOST}/auth/callback?code={login_code}"
    )


@auth_router.post("/oauth/exchange", response_model=TokenWithUser)
@limiter.limit(AUTH_LIMIT)
def exchange_login_code(
    request: Request, session: SessionDep, body: LoginCodeExchange
) -> TokenWithUser:
    """
    Exchange a one-time OAuth login code for an access token.

    The code arrives via the OAuth callback redirect; it is single-use and
    expires in 2 minutes. The JWT is delivered in this POST response body —
    never in a URL.
    """
    user = auth_service.consume_login_code(session, body.code)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="This sign-in link has expired or was already used. "
            "Please sign in again.",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated.")
    session.commit()

    access_token_expires = timedelta(days=settings.LOGIN_TOKEN_EXPIRE_DAYS)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    return TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


# Include sub-routers into main auth router
router.include_router(users_router)
router.include_router(auth_router)
