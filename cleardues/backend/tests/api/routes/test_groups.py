from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.features.groups.models import ExpenseGroup, GroupMember, GROUP_ROLE_OWNER


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
