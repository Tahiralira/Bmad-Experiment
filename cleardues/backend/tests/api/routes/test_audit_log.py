"""Tests for Story 4.4: Immutable Audit Log for All Actions."""
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.features.expenses.models import AuditActionType, AuditLog


def _create_group_and_expense(
    client: TestClient, headers: dict[str, str], description: str = "Test Expense"
) -> dict:
    """Helper: create a group and an expense, return expense JSON."""
    group_data = {"name": f"Audit Test Group {description}"}
    group_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=headers,
        json=group_data,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    expense_data = {
        "group_id": group["id"],
        "amount": "60.00",
        "description": description,
    }
    response = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=headers,
        json=expense_data,
    )
    assert response.status_code == 200
    return response.json()


def _add_second_user_to_group(
    client: TestClient,
    group_id: str,
    owner_headers: dict[str, str],
    second_user_headers: dict[str, str],
) -> str:
    """Helper: invite and accept a second user into a group. Returns second user ID."""
    # Create invite
    invite_response = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group_id}/invites",
        headers=owner_headers,
    )
    assert invite_response.status_code == 201
    token = invite_response.json()["invite"]["token"]

    # Get second user ID
    second_group = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=second_user_headers,
        json={"name": "Second User Temp Group"},
    )
    second_user_id = second_group.json()["created_by"]

    # Accept invite
    accept_response = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{token}",
        headers=second_user_headers,
    )
    assert accept_response.status_code == 200
    return second_user_id


def _setup_expense_with_two_members_and_split(
    client: TestClient,
    owner_headers: dict[str, str],
    second_user_headers: dict[str, str],
    description: str = "Test Expense",
) -> dict:
    """Helper: create group+expense with 2 members and equal split. Returns expense JSON."""
    expense = _create_group_and_expense(client, owner_headers, description)
    _add_second_user_to_group(
        client, expense["group_id"], owner_headers, second_user_headers
    )

    # Create equal split (now has 2 members)
    split_response = client.put(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
        headers=owner_headers,
        json={"type": "equal"},
    )
    assert split_response.status_code == 200
    return expense


def test_audit_entry_created_on_expense_creation(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test that creating an expense creates an audit log entry."""
    expense = _create_group_and_expense(client, normal_user_token_headers)

    statement = select(AuditLog).where(AuditLog.expense_id == expense["id"])
    audit_entries = db.exec(statement).all()
    assert len(audit_entries) == 1
    entry = audit_entries[0]
    assert entry.action_type == AuditActionType.CREATED
    assert entry.changes_json is not None
    assert entry.changes_json["after"]["description"] == "Test Expense"
    assert entry.changes_json["after"]["amount"] == "60.00"


def test_audit_entry_captures_before_after_on_edit(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test that editing an expense captures before/after in audit log."""
    expense = _create_group_and_expense(client, normal_user_token_headers)

    edit_data = {"description": "Updated Lunch"}
    response = client.patch(
        f"{settings.API_V1_STR}/expenses/{expense['id']}",
        headers=normal_user_token_headers,
        json=edit_data,
    )
    assert response.status_code == 200

    statement = select(AuditLog).where(AuditLog.expense_id == expense["id"])
    audit_entries = db.exec(statement).all()
    assert len(audit_entries) == 2

    edit_entry = [e for e in audit_entries if e.action_type == AuditActionType.EDITED][0]
    assert edit_entry.changes_json is not None
    assert edit_entry.changes_json["before"]["description"] == "Test Expense"
    assert edit_entry.changes_json["after"]["description"] == "Updated Lunch"


def test_audit_entry_created_on_confirm(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Test that confirming a split creates a 'confirmed' audit log entry."""
    expense = _setup_expense_with_two_members_and_split(
        client, normal_user_token_headers, second_user_token_headers, "Confirm Test"
    )

    # Confirm as second user
    confirm_response = client.post(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/confirm",
        headers=second_user_token_headers,
    )
    assert confirm_response.status_code == 200

    # Check audit log for confirmed entry from second user
    statement = select(AuditLog).where(
        AuditLog.expense_id == expense["id"],
        AuditLog.action_type == AuditActionType.CONFIRMED,
    )
    audit_entries = db.exec(statement).all()
    assert len(audit_entries) >= 1


def test_audit_entry_created_on_reject(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Test that rejecting a split creates a 'rejected' audit log entry."""
    expense = _setup_expense_with_two_members_and_split(
        client, normal_user_token_headers, second_user_token_headers, "Reject Test"
    )

    # Reject as second user
    reject_response = client.post(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/reject",
        headers=second_user_token_headers,
    )
    assert reject_response.status_code == 200

    # Check audit log for rejected entry
    statement = select(AuditLog).where(
        AuditLog.expense_id == expense["id"],
        AuditLog.action_type == AuditActionType.REJECTED,
    )
    audit_entries = db.exec(statement).all()
    assert len(audit_entries) == 1


def test_audit_logs_queryable_by_expense_id(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test that audit logs are queryable via the API endpoint."""
    expense = _create_group_and_expense(client, normal_user_token_headers)

    response = client.get(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/audit-log",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert len(data["data"]) >= 1
    assert data["data"][0]["action_type"] == "created"
    assert data["data"][0]["expense_id"] == expense["id"]


def test_non_members_cannot_retrieve_audit_logs(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
) -> None:
    """Test that non-group members cannot retrieve audit logs."""
    expense = _create_group_and_expense(client, normal_user_token_headers)

    response = client.get(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/audit-log",
        headers=second_user_token_headers,
    )
    assert response.status_code == 403


def test_audit_log_on_split_update(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    second_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """Test that updating a split creates a 'split_updated' audit log entry."""
    expense = _create_group_and_expense(client, normal_user_token_headers, "Split Audit Test")
    _add_second_user_to_group(
        client, expense["group_id"], normal_user_token_headers, second_user_token_headers
    )

    # Create equal split (now has 2 members)
    response = client.put(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
        headers=normal_user_token_headers,
        json={"type": "equal"},
    )
    assert response.status_code == 200

    # Check audit log for split_updated entry
    statement = select(AuditLog).where(
        AuditLog.expense_id == expense["id"],
        AuditLog.action_type == AuditActionType.SPLIT_UPDATED,
    )
    audit_entries = db.exec(statement).all()
    assert len(audit_entries) == 1
    assert audit_entries[0].changes_json is not None
    assert audit_entries[0].changes_json["after"]["type"] == "equal"
