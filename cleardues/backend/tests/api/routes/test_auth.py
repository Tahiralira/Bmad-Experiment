"""Tests for magic link authentication endpoints."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.crud import create_user
from app.features.auth import service as auth_service
from app.models import (
    AUTH_METHOD_MAGIC_LINK,
    MagicLinkToken,
    User,
    UserCreate,
)
from tests.utils.utils import random_email


def test_request_magic_link_new_email(client: TestClient, db: Session) -> None:
    """Test requesting magic link for a new email creates token."""
    email = random_email()

    with patch("app.features.auth.router.settings") as mock_settings:
        mock_settings.emails_enabled = False  # Disable email sending
        r = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={"email": email},
        )

    assert r.status_code == 200
    response = r.json()
    assert "message" in response
    assert "magic link" in response["message"].lower()

    # Verify token was created
    statement = select(MagicLinkToken).where(MagicLinkToken.email == email)
    token = db.exec(statement).first()
    assert token is not None
    assert token.used_at is None
    assert token.expires_at > datetime.now(timezone.utc)


def test_request_magic_link_existing_user(client: TestClient, db: Session) -> None:
    """Test requesting magic link for existing user returns same message (no enumeration)."""
    # Create an existing user first
    email = random_email()
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=True,
    )
    create_user(session=db, user_create=user_create)

    r = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email},
    )

    assert r.status_code == 200
    response = r.json()
    assert "message" in response
    # Same message as for new email (prevents enumeration)
    assert "magic link" in response["message"].lower()


def test_verify_magic_link_valid_token(client: TestClient, db: Session) -> None:
    """Test verifying a valid magic link token creates user and returns JWT."""
    email = random_email()

    # Generate token directly - returns (token_obj, raw_token)
    token_obj, raw_token = auth_service.generate_magic_link_token(session=db, email=email)

    r = client.get(f"{settings.API_V1_STR}/auth/verify/{raw_token}")

    assert r.status_code == 200
    response = r.json()

    # Should have access token
    assert "access_token" in response
    assert response["token_type"] == "bearer"

    # Should have user info
    assert "user" in response
    assert response["user"]["email"] == email

    # Verify user was created in DB
    user_statement = select(User).where(User.email == email)
    user = db.exec(user_statement).first()
    assert user is not None
    assert user.auth_method == AUTH_METHOD_MAGIC_LINK
    assert user.is_active is True

    # Verify token was marked as used
    db.refresh(token_obj)
    assert token_obj.used_at is not None


def test_verify_magic_link_expired_token(client: TestClient, db: Session) -> None:
    """Test verifying an expired token fails."""
    email = random_email()

    # Create an expired token with hashed token stored
    raw_token = MagicLinkToken.generate_token()
    expired_token = MagicLinkToken(
        email=email,
        token=auth_service.hash_token(raw_token),  # Store hashed
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
    )
    db.add(expired_token)
    db.commit()

    r = client.get(f"{settings.API_V1_STR}/auth/verify/{raw_token}")

    assert r.status_code == 400
    response = r.json()
    assert "detail" in response
    assert "expired" in response["detail"].lower() or "invalid" in response["detail"].lower()


def test_verify_magic_link_used_token(client: TestClient, db: Session) -> None:
    """Test verifying an already used token fails."""
    email = random_email()

    # Create a used token with hashed token stored
    raw_token = MagicLinkToken.generate_token()
    used_token = MagicLinkToken(
        email=email,
        token=auth_service.hash_token(raw_token),  # Store hashed
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        used_at=datetime.now(timezone.utc),  # Already used
    )
    db.add(used_token)
    db.commit()

    r = client.get(f"{settings.API_V1_STR}/auth/verify/{raw_token}")

    assert r.status_code == 400
    response = r.json()
    assert "detail" in response


def test_verify_magic_link_invalid_token(client: TestClient) -> None:
    """Test verifying a non-existent token fails."""
    r = client.get(f"{settings.API_V1_STR}/auth/verify/invalid-token-12345")

    assert r.status_code == 400
    response = r.json()
    assert "detail" in response
    assert "invalid" in response["detail"].lower() or "expired" in response["detail"].lower()


def test_verify_magic_link_existing_user(client: TestClient, db: Session) -> None:
    """Test verifying token for email that now has a user returns error."""
    email = random_email()

    # Generate token - returns (token_obj, raw_token)
    _, raw_token = auth_service.generate_magic_link_token(session=db, email=email)

    # Create user with same email before verification
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=True,
    )
    create_user(session=db, user_create=user_create)

    r = client.get(f"{settings.API_V1_STR}/auth/verify/{raw_token}")

    assert r.status_code == 400
    response = r.json()
    assert "detail" in response
    assert "already exists" in response["detail"].lower()


def test_token_not_reusable(client: TestClient, db: Session) -> None:
    """Test that a token cannot be used twice."""
    email = random_email()

    # Generate token - returns (token_obj, raw_token)
    _, raw_token = auth_service.generate_magic_link_token(session=db, email=email)

    # First verification should succeed
    r1 = client.get(f"{settings.API_V1_STR}/auth/verify/{raw_token}")
    assert r1.status_code == 200

    # Second verification should fail
    r2 = client.get(f"{settings.API_V1_STR}/auth/verify/{raw_token}")
    assert r2.status_code == 400


def test_rate_limiting(client: TestClient, db: Session) -> None:
    """Test that rate limiting prevents too many magic link requests."""
    email = random_email()

    with patch("app.features.auth.router.settings") as mock_settings:
        mock_settings.emails_enabled = False

        # Make 3 requests (the limit)
        for _ in range(3):
            r = client.post(
                f"{settings.API_V1_STR}/auth/register",
                json={"email": email},
            )
            assert r.status_code == 200

    # Count tokens created for this email
    statement = select(MagicLinkToken).where(MagicLinkToken.email == email)
    tokens = db.exec(statement).all()
    assert len(tokens) == 3  # Should have exactly 3 tokens

    # 4th request should be rate limited (no new token created)
    with patch("app.features.auth.router.settings") as mock_settings:
        mock_settings.emails_enabled = False
        r = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={"email": email},
        )
        assert r.status_code == 200  # Still returns 200 to prevent enumeration

    # Should still have only 3 tokens (4th was rate limited)
    tokens = db.exec(statement).all()
    assert len(tokens) == 3


# ============================================================================
# LOGIN TESTS (Story 1.5)
# ============================================================================


def test_login_magic_link_existing_user(client: TestClient, db: Session) -> None:
    """Test requesting login magic link for existing user sends magic link."""
    email = random_email()

    # Create an existing user first
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=True,
    )
    create_user(session=db, user_create=user_create)

    with patch("app.features.auth.router.settings") as mock_settings:
        mock_settings.emails_enabled = False
        r = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": email},
        )

    assert r.status_code == 200
    response = r.json()
    assert "message" in response
    assert "magic" in response["message"].lower() or "login" in response["message"].lower()

    # Verify token was created for login
    statement = select(MagicLinkToken).where(MagicLinkToken.email == email)
    token = db.exec(statement).first()
    assert token is not None
    assert token.used_at is None


def test_login_magic_link_nonexistent_user(client: TestClient, db: Session) -> None:
    """Test requesting login magic link for non-existent user returns same message (no enumeration)."""
    email = random_email()  # This email doesn't exist

    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email},
    )

    assert r.status_code == 200
    response = r.json()
    assert "message" in response
    # Same generic message for security (prevents enumeration)
    assert "magic" in response["message"].lower() or "login" in response["message"].lower()

    # No token should be created for non-existent user
    statement = select(MagicLinkToken).where(MagicLinkToken.email == email)
    token = db.exec(statement).first()
    assert token is None


def test_login_magic_link_inactive_user(client: TestClient, db: Session) -> None:
    """Test requesting login magic link for inactive user returns same message (no enumeration)."""
    email = random_email()

    # Create an inactive user
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=False,
    )
    create_user(session=db, user_create=user_create)

    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email},
    )

    assert r.status_code == 200
    response = r.json()
    assert "message" in response
    # Same generic message for security

    # No token should be created for inactive user
    statement = select(MagicLinkToken).where(MagicLinkToken.email == email)
    token = db.exec(statement).first()
    assert token is None


def test_login_verify_valid_token_existing_user(client: TestClient, db: Session) -> None:
    """Test verifying a valid login token for existing user returns JWT."""
    email = random_email()

    # Create an existing user first
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=True,
    )
    user = create_user(session=db, user_create=user_create)

    # Generate token for login
    _, raw_token = auth_service.generate_magic_link_token(session=db, email=email)

    r = client.get(f"{settings.API_V1_STR}/auth/login/verify/{raw_token}")

    assert r.status_code == 200
    response = r.json()

    # Should have access token
    assert "access_token" in response
    assert response["token_type"] == "bearer"

    # Should have user info
    assert "user" in response
    assert response["user"]["email"] == email


def test_login_verify_valid_token_no_user(client: TestClient, db: Session) -> None:
    """Test verifying login token for non-existent user returns error."""
    email = random_email()

    # Generate token but don't create user
    _, raw_token = auth_service.generate_magic_link_token(session=db, email=email)

    r = client.get(f"{settings.API_V1_STR}/auth/login/verify/{raw_token}")

    assert r.status_code == 404
    response = r.json()
    assert "detail" in response
    assert "not found" in response["detail"].lower() or "register" in response["detail"].lower()


def test_login_verify_inactive_user(client: TestClient, db: Session) -> None:
    """Test verifying login token for inactive user returns error."""
    email = random_email()

    # Create an inactive user
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=False,
    )
    create_user(session=db, user_create=user_create)

    # Generate token
    _, raw_token = auth_service.generate_magic_link_token(session=db, email=email)

    r = client.get(f"{settings.API_V1_STR}/auth/login/verify/{raw_token}")

    assert r.status_code == 400
    response = r.json()
    assert "detail" in response
    assert "deactivated" in response["detail"].lower() or "inactive" in response["detail"].lower()


def test_login_verify_expired_token(client: TestClient, db: Session) -> None:
    """Test verifying an expired login token fails."""
    email = random_email()

    # Create user
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=True,
    )
    create_user(session=db, user_create=user_create)

    # Create an expired token
    raw_token = MagicLinkToken.generate_token()
    expired_token = MagicLinkToken(
        email=email,
        token=auth_service.hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(expired_token)
    db.commit()

    r = client.get(f"{settings.API_V1_STR}/auth/login/verify/{raw_token}")

    assert r.status_code == 400
    response = r.json()
    assert "detail" in response
    assert "expired" in response["detail"].lower() or "invalid" in response["detail"].lower()


def test_login_rate_limiting(client: TestClient, db: Session) -> None:
    """Test that rate limiting prevents too many login magic link requests."""
    email = random_email()

    # Create a user for login
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=True,
    )
    create_user(session=db, user_create=user_create)

    with patch("app.features.auth.router.settings") as mock_settings:
        mock_settings.emails_enabled = False

        # Make 3 requests (the limit)
        for _ in range(3):
            r = client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={"email": email},
            )
            assert r.status_code == 200

    # Count tokens created
    statement = select(MagicLinkToken).where(MagicLinkToken.email == email)
    tokens = db.exec(statement).all()
    assert len(tokens) == 3

    # 4th request should be rate limited
    with patch("app.features.auth.router.settings") as mock_settings:
        mock_settings.emails_enabled = False
        r = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": email},
        )
        assert r.status_code == 200  # Still 200 to prevent enumeration

    # Should still have only 3 tokens
    tokens = db.exec(statement).all()
    assert len(tokens) == 3


def test_login_jwt_30_day_expiration(client: TestClient, db: Session) -> None:
    """Test that login verification returns JWT with 30-day expiration per PRD 'Walled Garden'."""
    import jwt
    from app.core.config import settings as app_settings
    from app.core.security import ALGORITHM

    email = random_email()

    # Create an existing user
    user_create = UserCreate(
        email=email,
        password="testpassword123",
        is_active=True,
    )
    create_user(session=db, user_create=user_create)

    # Generate login token
    _, raw_token = auth_service.generate_magic_link_token(session=db, email=email)

    # Verify login
    r = client.get(f"{settings.API_V1_STR}/auth/login/verify/{raw_token}")
    assert r.status_code == 200

    response = r.json()
    access_token = response["access_token"]

    # Decode the JWT and verify expiration
    decoded = jwt.decode(access_token, app_settings.SECRET_KEY, algorithms=[ALGORITHM])

    # Check that expiration is approximately 30 days from now
    exp_timestamp = decoded["exp"]
    now = datetime.now(timezone.utc).timestamp()
    days_until_expiry = (exp_timestamp - now) / (60 * 60 * 24)

    # Allow 1 minute tolerance for test execution time
    assert 29.99 <= days_until_expiry <= 30.01, f"JWT expiration should be ~30 days, got {days_until_expiry:.2f} days"
