from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.features.expenses.models import Expense, ExpenseStatus


def test_create_expense_as_group_member(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating an expense as an authenticated group member."""
    # First create a group
    group_data = {"name": "Expense Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Create an expense in the group
    expense_data = {
        "group_id": group["id"],
        "amount": "50.00",
        "description": "Lunch at restaurant",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["group_id"] == group["id"]
    assert content["description"] == expense_data["description"]
    assert "id" in content
    assert "payer_id" in content
    assert "created_by" in content
    assert "status" in content
    assert "created_at" in content
    assert "updated_at" in content


def test_create_expense_has_correct_default_status(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test that new expenses have status 'draft' by default."""
    # Create a group
    group_data = {"name": "Default Status Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Create an expense
    expense_data = {
        "group_id": group["id"],
        "amount": "25.50",
        "description": "Coffee",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "draft"


def test_create_expense_payer_defaults_to_current_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test that payer_id defaults to current user if not provided."""
    # Create a group
    group_data = {"name": "Payer Default Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Create an expense without specifying payer_id
    expense_data = {
        "group_id": group["id"],
        "amount": "30.00",
        "description": "Groceries",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 200
    content = response.json()
    # payer_id should equal created_by (current user)
    assert content["payer_id"] == content["created_by"]


def test_create_expense_non_member_returns_403(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
) -> None:
    """Test creating expense as non-member returns 403 Forbidden."""
    # Create a group as normal user
    group_data = {"name": "Non-Member Expense Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Try to create expense as second user (not a member)
    expense_data = {
        "group_id": group["id"],
        "amount": "50.00",
        "description": "Unauthorized expense",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=second_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 403
    content = response.json()
    assert "must be a member of the group" in content["detail"]


def test_create_expense_invalid_group_returns_404(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating expense with invalid group_id returns 404."""
    fake_group_id = "00000000-0000-0000-0000-000000000000"
    expense_data = {
        "group_id": fake_group_id,
        "amount": "50.00",
        "description": "Invalid group expense",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 404
    content = response.json()
    assert "Group not found" in content["detail"]


def test_create_expense_unauthenticated_returns_401(client: TestClient) -> None:
    """Test creating expense without authentication returns 401."""
    fake_group_id = "00000000-0000-0000-0000-000000000000"
    expense_data = {
        "group_id": fake_group_id,
        "amount": "50.00",
        "description": "Unauthenticated expense",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        json=expense_data,
    )
    assert response.status_code == 401


def test_create_expense_with_invalid_amount(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating expense with invalid amount returns 422."""
    # Create a group
    group_data = {"name": "Invalid Amount Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Try to create expense with negative amount
    expense_data = {
        "group_id": group["id"],
        "amount": "-10.00",
        "description": "Negative amount",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 422


def test_create_expense_with_zero_amount(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating expense with zero amount returns 422."""
    # Create a group
    group_data = {"name": "Zero Amount Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Try to create expense with zero amount
    expense_data = {
        "group_id": group["id"],
        "amount": "0.00",
        "description": "Zero amount",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 422


def test_create_expense_with_empty_description(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating expense with empty description returns 422."""
    # Create a group
    group_data = {"name": "Empty Description Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Try to create expense with empty description
    expense_data = {
        "group_id": group["id"],
        "amount": "50.00",
        "description": "",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 422


def test_create_expense_with_non_member_payer_returns_400(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Test creating expense with payer_id of non-member returns 400."""
    # Create a group as normal user
    group_data = {"name": "Payer Validation Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Get second user's ID by creating a group and checking created_by
    second_group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=second_user_token_headers,
        json={"name": "Second User Group"},
    )
    assert second_group_response.status_code == 201
    second_user_id = second_group_response.json()["created_by"]

    # Try to create expense with payer_id of second user (not a member of first group)
    expense_data = {
        "group_id": group["id"],
        "amount": "50.00",
        "description": "Expense with non-member payer",
        "payer_id": second_user_id,
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "Payer must be a member of the group" in content["detail"]


def test_create_expense_stores_in_database(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test that created expense is properly stored in database."""
    # Create a group
    group_data = {"name": "Database Storage Test Group"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=normal_user_token_headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    # Create an expense
    expense_data = {
        "group_id": group["id"],
        "amount": "75.50",
        "description": "Database test expense",
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user_token_headers,
        json=expense_data,
    )
    assert response.status_code == 200
    content = response.json()

    # Verify expense exists in database
    statement = select(Expense).where(Expense.id == content["id"])
    db_expense = db.exec(statement).first()
    assert db_expense is not None
    assert str(db_expense.group_id) == group["id"]
    assert db_expense.description == expense_data["description"]
    assert db_expense.status == ExpenseStatus.DRAFT
