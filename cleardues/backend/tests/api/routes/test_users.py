import uuid
from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)


def test_get_users_superuser_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER


def test_update_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    full_name = "Updated Name"
    email = random_email()
    data = {"full_name": full_name, "email": email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name

    user_query = select(User).where(User.email == email)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == email
    assert user_db.full_name == full_name


def test_update_user_me_email_exists(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    data = {"email": user.email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


def test_delete_user_me(client: TestClient, db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    user_id = user.id

    headers = token_headers_for_user(user)

    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert r.status_code == 200
    assert "Account deleted" in r.json()["message"]

    # WS4/C4: soft delete — the row survives (financial records reference it)
    # but PII is anonymized and login is disabled.
    db.expire_all()
    result = db.exec(select(User).where(User.id == user_id)).first()
    assert result is not None
    assert result.is_active is False
    assert result.deleted_at is not None
    assert result.email != username
    assert result.email.startswith("deleted-")
    assert result.full_name == "Deleted User"
    assert result.oauth_provider is None
    assert result.gemini_api_key_encrypted is None

    # The soft-deleted user's token no longer authenticates
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 400  # "Inactive user"


def test_delete_user_me_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )
    assert r.status_code == 403
    response = r.json()
    assert response["detail"] == "Super users are not allowed to delete themselves"


def test_get_dashboard_authenticated(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test getting dashboard as an authenticated user."""
    r = client.get(
        f"{settings.API_V1_STR}/users/me/dashboard",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "groups" in data
    assert "total_balance" in data
    assert "count" in data
    assert isinstance(data["groups"], list)
    # WS4/M1: money is Decimal to the wire — serialized as a decimal string
    assert isinstance(data["total_balance"], str)
    Decimal(data["total_balance"])  # parseable as an exact decimal
    assert isinstance(data["count"], int)


def test_get_dashboard_unauthenticated(client: TestClient) -> None:
    """Test that unauthenticated requests return 401."""
    r = client.get(f"{settings.API_V1_STR}/users/me/dashboard")
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"


def test_get_dashboard_with_groups(client: TestClient, db: Session) -> None:
    """Test dashboard returns user's groups with correct fields."""
    from datetime import datetime, timezone, timedelta
    from app.features.groups.models import ExpenseGroup, GroupMember, GROUP_ROLE_OWNER

    # Create a test user
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create groups with different updated_at times
    group1 = ExpenseGroup(
        name="Test Group 1",
        created_by=user.id,
        updated_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db.add(group1)
    db.commit()
    db.refresh(group1)

    group2 = ExpenseGroup(
        name="Test Group 2",
        created_by=user.id,
        updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(group2)
    db.commit()
    db.refresh(group2)

    # Add user as member of both groups
    member1 = GroupMember(
        group_id=group1.id,
        user_id=user.id,
        role=GROUP_ROLE_OWNER,
    )
    member2 = GroupMember(
        group_id=group2.id,
        user_id=user.id,
        role=GROUP_ROLE_OWNER,
    )
    db.add(member1)
    db.add(member2)
    db.commit()

    headers = token_headers_for_user(user)

    r = client.get(f"{settings.API_V1_STR}/users/me/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert data["count"] == 2
    assert len(data["groups"]) == 2

    # Verify correct fields in response
    for group in data["groups"]:
        assert "group_id" in group
        assert "group_name" in group
        assert "net_balance" in group
        assert "last_activity" in group
        assert "member_count" in group


def test_get_dashboard_groups_sorted_by_activity(client: TestClient, db: Session) -> None:
    """Test that groups are sorted by most recent activity (updated_at DESC)."""
    from datetime import datetime, timezone, timedelta
    from app.features.groups.models import ExpenseGroup, GroupMember, GROUP_ROLE_OWNER

    # Create a test user
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create groups - older group first, newer group second
    older_group = ExpenseGroup(
        name="Older Group",
        created_by=user.id,
        updated_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db.add(older_group)
    db.commit()
    db.refresh(older_group)

    newer_group = ExpenseGroup(
        name="Newer Group",
        created_by=user.id,
        updated_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(newer_group)
    db.commit()
    db.refresh(newer_group)

    # Add user as member
    member1 = GroupMember(group_id=older_group.id, user_id=user.id, role=GROUP_ROLE_OWNER)
    member2 = GroupMember(group_id=newer_group.id, user_id=user.id, role=GROUP_ROLE_OWNER)
    db.add(member1)
    db.add(member2)
    db.commit()

    headers = token_headers_for_user(user)

    r = client.get(f"{settings.API_V1_STR}/users/me/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # Newer group should be first (most recent activity)
    assert data["groups"][0]["group_name"] == "Newer Group"
    assert data["groups"][1]["group_name"] == "Older Group"


def test_get_dashboard_net_balance_is_zero(client: TestClient, db: Session) -> None:
    """Test that net_balance is 0 (no expenses implemented yet)."""
    from app.features.groups.models import ExpenseGroup, GroupMember, GROUP_ROLE_OWNER

    # Create a test user
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a group
    group = ExpenseGroup(name="Balance Test Group", created_by=user.id)
    db.add(group)
    db.commit()
    db.refresh(group)

    # Add user as member
    member = GroupMember(group_id=group.id, user_id=user.id, role=GROUP_ROLE_OWNER)
    db.add(member)
    db.commit()

    headers = token_headers_for_user(user)

    r = client.get(f"{settings.API_V1_STR}/users/me/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # All net_balance values should be 0 — as exact decimal strings (WS4/M1)
    assert data["count"] == 1
    assert Decimal(data["groups"][0]["net_balance"]) == Decimal("0.00")
    assert Decimal(data["total_balance"]) == Decimal("0.00")


def test_get_dashboard_empty_for_new_user(client: TestClient, db: Session) -> None:
    """Test that dashboard returns empty list for user with no groups."""
    # Create a test user with no groups
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    headers = token_headers_for_user(user)

    r = client.get(f"{settings.API_V1_STR}/users/me/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert data["groups"] == []
    assert data["count"] == 0
    assert Decimal(data["total_balance"]) == Decimal("0.00")
