from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.features.groups.models import (
    ExpenseGroup,
    GroupInvite,
    GroupMember,
    GROUP_ROLE_MEMBER,
    GROUP_ROLE_OWNER,
)


def test_create_group(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating a group as authenticated user."""
    data = {"name": "Weekend Trip"}
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content
    assert "created_by" in content
    assert "created_at" in content
    assert "updated_at" in content


def test_create_group_creator_is_owner_member(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test creator is automatically added as member with 'owner' role."""
    data = {"name": "Test Owner Group"}
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    group_id = content["id"]

    # Check that group member was created
    statement = select(GroupMember).where(GroupMember.group_id == group_id)
    member = db.exec(statement).first()
    assert member is not None
    assert member.role == GROUP_ROLE_OWNER
    assert str(member.user_id) == content["created_by"]


def test_create_group_empty_name(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating group with empty name returns 422."""
    data = {"name": ""}
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 422
    content = response.json()
    assert "detail" in content


def test_create_group_unauthenticated(client: TestClient) -> None:
    """Test creating group while unauthenticated returns 401."""
    data = {"name": "Unauthorized Group"}
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        json=data,
    )
    # FastAPI OAuth2 returns 401 for missing token
    assert response.status_code == 401


def test_list_user_groups(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test group appears in user's group list after creation."""
    # Create a group first
    data = {"name": "List Test Group"}
    create_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert create_response.status_code == 201
    created_group = create_response.json()

    # Fetch user's groups
    response = client.get(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    groups = response.json()

    # Find our created group
    group_ids = [g["id"] for g in groups]
    assert created_group["id"] in group_ids

    # Check the group has member_count
    created_in_list = next(g for g in groups if g["id"] == created_group["id"])
    assert "member_count" in created_in_list
    assert created_in_list["member_count"] >= 1


def test_list_groups_unauthenticated(client: TestClient) -> None:
    """Test listing groups while unauthenticated returns 401."""
    response = client.get(f"{settings.API_V1_STR}/expense-groups/")
    assert response.status_code == 401


def test_create_group_name_max_length(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating group with name at max length (100 chars)."""
    data = {"name": "A" * 100}
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert len(content["name"]) == 100


def test_create_group_name_too_long(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating group with name over max length returns 422."""
    data = {"name": "A" * 101}
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 422


# === Invite Tests ===


def test_create_invite_as_owner(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating an invite as group owner."""
    # Create a group first
    group_data = {"name": "Invite Test Group"}
    create_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert create_response.status_code == 201
    group = create_response.json()

    # Create invite
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 201
    content = response.json()
    assert "invite" in content
    assert "message" in content
    assert content["invite"]["group_id"] == group["id"]
    assert "token" in content["invite"]
    assert "expires_at" in content["invite"]
    assert "invite_url" in content["invite"]


def test_create_invite_as_non_owner(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
) -> None:
    """Test creating invite as non-owner returns 403."""
    # Create a group as normal user
    group_data = {"name": "Non-Owner Invite Test Group"}
    create_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert create_response.status_code == 201
    group = create_response.json()

    # Try to create invite as second user (not a member)
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=second_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert "Only the group owner can generate invite links" in content["detail"]


def test_create_invite_nonexistent_group(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating invite for nonexistent group returns 404."""
    fake_group_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"{settings.API_V1_STR}/expense-groups/{fake_group_id}/invites",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404


def test_accept_valid_invite(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Test accepting a valid invite adds user to group."""
    # Create a group as normal user
    group_data = {"name": "Accept Invite Test Group"}
    create_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert create_response.status_code == 201
    group = create_response.json()

    # Create invite
    invite_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=normal_user_token_headers,
    )
    assert invite_response.status_code == 201
    invite = invite_response.json()["invite"]

    # Accept invite as second user
    accept_response = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}",
        headers=second_user_token_headers,
    )
    assert accept_response.status_code == 200
    content = accept_response.json()
    assert "group" in content
    assert content["group"]["id"] == group["id"]
    assert content["message"] == "Successfully joined the group"

    # Verify user is now a member
    statement = select(GroupMember).where(
        GroupMember.group_id == group["id"]
    )
    members = db.exec(statement).all()
    assert len(members) == 2  # Owner + new member


def test_accept_invite_already_member(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Test accepting invite when already a member returns success message."""
    # Create a group
    group_data = {"name": "Already Member Test Group"}
    create_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert create_response.status_code == 201
    group = create_response.json()

    # Create invite
    invite_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=normal_user_token_headers,
    )
    assert invite_response.status_code == 201
    invite = invite_response.json()["invite"]

    # Accept invite as same user (owner, already a member)
    accept_response = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}",
        headers=normal_user_token_headers,
    )
    assert accept_response.status_code == 200
    content = accept_response.json()
    assert "You are already a member" in content["message"]


def test_accept_invalid_invite_token(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test accepting invalid token returns 404."""
    response = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/invalid-token-12345",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "Invalid invite link" in content["detail"]


def test_accept_expired_invite(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Test accepting expired invite returns 410 Gone."""
    # Create a group
    group_data = {"name": "Expired Invite Test Group"}
    create_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert create_response.status_code == 201
    group = create_response.json()

    # Create invite
    invite_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=normal_user_token_headers,
    )
    assert invite_response.status_code == 201
    invite = invite_response.json()["invite"]

    # Manually expire the invite in DB
    statement = select(GroupInvite).where(GroupInvite.token == invite["token"])
    db_invite = db.exec(statement).first()
    db_invite.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(db_invite)
    db.commit()

    # Try to accept expired invite
    accept_response = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}",
        headers=second_user_token_headers,
    )
    assert accept_response.status_code == 410
    content = accept_response.json()
    assert "expired" in content["detail"].lower()


def test_invite_can_be_used_multiple_times(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Test that the same invite can be used by multiple users."""
    # Create a group
    group_data = {"name": "Multi-Use Invite Test Group"}
    create_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert create_response.status_code == 201
    group = create_response.json()

    # Create invite
    invite_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=normal_user_token_headers,
    )
    assert invite_response.status_code == 201
    invite = invite_response.json()["invite"]

    # First user accepts
    accept_response1 = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}",
        headers=second_user_token_headers,
    )
    assert accept_response1.status_code == 200

    # Second user accepts same invite
    accept_response2 = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}",
        headers=superuser_token_headers,
    )
    assert accept_response2.status_code == 200

    # Verify both are now members
    statement = select(GroupMember).where(
        GroupMember.group_id == group["id"]
    )
    members = db.exec(statement).all()
    assert len(members) == 3  # Owner + 2 new members
