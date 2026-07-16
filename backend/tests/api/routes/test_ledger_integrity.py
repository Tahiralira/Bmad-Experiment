"""WS4 — Ledger Integrity tests.

Covers the fixes from execution-plan Work Session 4:
- H2: editing amount/payer re-opens consent (revert to DRAFT, splits deleted)
- H3: rejecting a split reverts to DRAFT instead of silently redistributing
- H5: services never commit; operation + audit entry are atomic
- C4: user deletion is soft (anonymize), blocked while unsettled, and the
      database itself refuses hard deletes of users with financial rows
- M1: dashboard balances are exact decimal strings on the wire
- M9: GET /users/{id} 404s for a nonexistent id instead of 500ing
"""
import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.features.auth.models import User, UserCreate
from app.features.expenses import service as expense_service
from app.features.expenses.models import (
    AuditActionType,
    AuditLog,
    Expense,
    ExpenseCreate,
    ExpenseSplit,
    ExpenseStatus,
    SplitStatus,
)
from app.features.groups.models import ExpenseGroup
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_authed_user(
    client: TestClient, db: Session
) -> tuple[dict[str, str], uuid.UUID, str]:
    """Create a fresh user with a directly-minted JWT (WS8: no password
    login endpoint exists); returns (headers, user_id, email)."""
    email = random_email()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=random_lower_string())
    )
    return (token_headers_for_user(user), user.id, email)


def _create_group(client: TestClient, headers: dict[str, str], name: str) -> dict:
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/", headers=headers, json={"name": name}
    )
    assert r.status_code == 201
    return r.json()


def _join_group(
    client: TestClient,
    group_id: str,
    owner_headers: dict[str, str],
    member_headers: dict[str, str],
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group_id}/invites",
        headers=owner_headers,
    )
    assert r.status_code == 201
    token = r.json()["invite"]["token"]
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/invite/{token}/accept", headers=member_headers
    )
    assert r.status_code == 200


def _create_expense(
    client: TestClient,
    headers: dict[str, str],
    group_id: str,
    amount: str = "100.00",
    description: str = "Integrity test expense",
) -> dict:
    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=headers,
        json={"group_id": group_id, "amount": amount, "description": description},
    )
    assert r.status_code == 200
    return r.json()


def _equal_split(client: TestClient, headers: dict[str, str], expense_id: str) -> None:
    r = client.put(
        f"{settings.API_V1_STR}/expenses/{expense_id}/split",
        headers=headers,
        json={"type": "equal"},
    )
    assert r.status_code == 200


def _two_member_expense_with_split(
    client: TestClient, db: Session
) -> tuple[dict, dict[str, str], dict[str, str], uuid.UUID, uuid.UUID]:
    """Fresh owner + member, one group, one 100.00 expense, equal split."""
    owner_headers, owner_id, _ = _make_authed_user(client, db)
    member_headers, member_id, _ = _make_authed_user(client, db)
    group = _create_group(client, owner_headers, f"WS4 {uuid.uuid4().hex[:8]}")
    _join_group(client, group["id"], owner_headers, member_headers)
    expense = _create_expense(client, owner_headers, group["id"])
    _equal_split(client, owner_headers, expense["id"])
    return expense, owner_headers, member_headers, owner_id, member_id


def _get_splits(db: Session, expense_id: str) -> list[ExpenseSplit]:
    db.expire_all()
    return list(
        db.exec(
            select(ExpenseSplit).where(
                ExpenseSplit.expense_id == uuid.UUID(expense_id)
            )
        ).all()
    )


# ---------------------------------------------------------------------------
# H2 — editing amount/payer re-opens consent
# ---------------------------------------------------------------------------


def test_edit_amount_reverts_to_draft_and_deletes_splits(
    client: TestClient, db: Session
) -> None:
    expense, owner_headers, member_headers, _, _ = _two_member_expense_with_split(
        client, db
    )

    # Member has already consented to their half
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/confirm",
        headers=member_headers,
    )
    assert r.status_code == 200

    # Creator changes the amount → consent re-opens
    r = client.patch(
        f"{settings.API_V1_STR}/expenses/{expense['id']}",
        headers=owner_headers,
        json={"amount": "500.00"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "draft"

    # No splits survive — nobody stays confirmed on numbers they never saw
    assert _get_splits(db, expense["id"]) == []

    # The member's pending-confirmations worklist is empty again
    r = client.get(
        f"{settings.API_V1_STR}/expenses/pending-confirmations",
        headers=member_headers,
    )
    assert expense["id"] not in [
        item["expense"]["id"] for item in r.json()
    ]

    # The audit trail records the revert
    db.expire_all()
    edit_entry = db.exec(
        select(AuditLog)
        .where(AuditLog.expense_id == uuid.UUID(expense["id"]))
        .where(AuditLog.action_type == AuditActionType.EDITED)
    ).one()
    assert edit_entry.changes_json["before"]["amount"] == "100.00"
    assert edit_entry.changes_json["after"]["amount"] == "500.00"
    assert edit_entry.changes_json["before"]["status"] == "pending_confirmation"
    assert edit_entry.changes_json["after"]["status"] == "draft"


def test_edit_description_only_keeps_splits_and_status(
    client: TestClient, db: Session
) -> None:
    expense, owner_headers, _, _, _ = _two_member_expense_with_split(client, db)

    r = client.patch(
        f"{settings.API_V1_STR}/expenses/{expense['id']}",
        headers=owner_headers,
        json={"description": "Renamed, money untouched"},
    )
    assert r.status_code == 200
    # Description doesn't change what anyone owes: no revert
    assert r.json()["status"] == "pending_confirmation"
    assert len(_get_splits(db, expense["id"])) == 2


def test_edit_payer_reverts_to_draft(client: TestClient, db: Session) -> None:
    expense, owner_headers, _, _, member_id = _two_member_expense_with_split(
        client, db
    )

    # Changing who is owed the money re-opens consent too
    r = client.patch(
        f"{settings.API_V1_STR}/expenses/{expense['id']}",
        headers=owner_headers,
        json={"payer_id": str(member_id)},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "draft"
    assert _get_splits(db, expense["id"]) == []


def test_edit_amount_on_draft_without_splits_stays_draft(
    client: TestClient, db: Session
) -> None:
    owner_headers, _, _ = _make_authed_user(client, db)
    group = _create_group(client, owner_headers, f"WS4 draft {uuid.uuid4().hex[:8]}")
    expense = _create_expense(client, owner_headers, group["id"])

    r = client.patch(
        f"{settings.API_V1_STR}/expenses/{expense['id']}",
        headers=owner_headers,
        json={"amount": "77.00"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "draft"
    assert r.json()["amount"] == "77.00"


# ---------------------------------------------------------------------------
# H3 — rejection reverts to DRAFT, never redistributes
# ---------------------------------------------------------------------------


def test_reject_reverts_expense_to_draft_and_deletes_all_splits(
    client: TestClient, db: Session
) -> None:
    expense, _, member_headers, _, _ = _two_member_expense_with_split(client, db)

    r = client.post(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/reject",
        headers=member_headers,
    )
    assert r.status_code == 200
    assert r.json()["remaining_splits"] == 0

    db.expire_all()
    db_expense = db.get(Expense, uuid.UUID(expense["id"]))
    assert db_expense.status == ExpenseStatus.DRAFT
    # No redistribution: every split is gone, amounts untouched elsewhere
    assert _get_splits(db, expense["id"]) == []
    assert db_expense.amount == Decimal("100.00")

    # Rejection is in the audit trail with the status transition
    reject_entry = db.exec(
        select(AuditLog)
        .where(AuditLog.expense_id == uuid.UUID(expense["id"]))
        .where(AuditLog.action_type == AuditActionType.REJECTED)
    ).one()
    assert reject_entry.changes_json["before"]["status"] == "pending_confirmation"
    assert reject_entry.changes_json["after"]["status"] == "draft"


def test_payer_reject_after_other_confirmed_no_stuck_state(
    client: TestClient, db: Session
) -> None:
    """Old behavior stranded the expense in PENDING_CONFIRMATION forever when
    the last pending member rejected (finalize only ran on the confirm path).
    New behavior: revert to DRAFT — never stuck, nobody's confirmed amount is
    silently rewritten."""
    expense, owner_headers, member_headers, _, _ = _two_member_expense_with_split(
        client, db
    )

    # Member confirms; only the payer's own split is still pending
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/confirm",
        headers=member_headers,
    )
    assert r.status_code == 200

    # Payer rejects their own split (e.g. realizes the split is wrong)
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/reject",
        headers=owner_headers,
    )
    assert r.status_code == 200

    db.expire_all()
    db_expense = db.get(Expense, uuid.UUID(expense["id"]))
    assert db_expense.status == ExpenseStatus.DRAFT
    assert _get_splits(db, expense["id"]) == []

    # Re-split works: the flow is recoverable, not stuck
    _equal_split(client, owner_headers, expense["id"])
    db.expire_all()
    assert db.get(Expense, uuid.UUID(expense["id"])).status == (
        ExpenseStatus.PENDING_CONFIRMATION
    )
    assert len(_get_splits(db, expense["id"])) == 2


# ---------------------------------------------------------------------------
# H5 — services never commit; audit entries are atomic with their operations
# ---------------------------------------------------------------------------


def test_service_layer_never_commits_and_audit_is_atomic(db: Session) -> None:
    superuser = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    assert superuser is not None

    group = ExpenseGroup(name="Atomicity probe", created_by=superuser.id)
    db.add(group)
    db.flush()

    expense = expense_service.create_expense(
        db,
        ExpenseCreate(
            group_id=group.id, amount=Decimal("42.00"), description="probe"
        ),
        superuser.id,
    )
    expense_id = expense.id

    # Inside the (uncommitted) transaction both rows are visible together
    assert db.get(Expense, expense_id) is not None
    audit_rows = db.exec(
        select(AuditLog).where(AuditLog.expense_id == expense_id)
    ).all()
    assert len(audit_rows) == 1
    assert audit_rows[0].action_type == AuditActionType.CREATED

    # The service never committed: rolling back erases operation AND audit —
    # they live or die together
    db.rollback()
    assert db.get(Expense, expense_id) is None
    assert (
        db.exec(select(AuditLog).where(AuditLog.expense_id == expense_id)).first()
        is None
    )


# ---------------------------------------------------------------------------
# C4 — soft delete, deletion blocking, and DB-level hard-delete refusal
# ---------------------------------------------------------------------------


def test_db_refuses_hard_delete_of_user_with_financial_rows(db: Session) -> None:
    """The RESTRICT FK migration is the last line of defense: even code that
    bypasses the soft-delete endpoint cannot destroy shared financial rows."""
    user = User(email=random_email(), hashed_password="not-a-real-hash")
    db.add(user)
    db.flush()
    group = ExpenseGroup(name="FK probe", created_by=user.id)
    db.add(group)
    db.flush()
    expense = Expense(
        group_id=group.id,
        amount=Decimal("10.00"),
        description="FK probe",
        payer_id=user.id,
        created_by=user.id,
    )
    db.add(expense)
    db.flush()

    db.delete(user)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_account_deletion_blocked_until_settled_then_anonymized(
    client: TestClient, db: Session
) -> None:
    expense, owner_headers, member_headers, owner_id, member_id = (
        _two_member_expense_with_split(client, db)
    )

    # Debtor cannot leave while their split is pending
    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=member_headers)
    assert r.status_code == 409

    # Payer cannot leave while owed money either
    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=owner_headers)
    assert r.status_code == 409

    # Confirm both splits → expense CONFIRMED
    for headers in (member_headers, owner_headers):
        r = client.post(
            f"{settings.API_V1_STR}/expenses/{expense['id']}/confirm",
            headers=headers,
        )
        assert r.status_code == 200

    # Confirmed-but-unsettled still blocks
    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=member_headers)
    assert r.status_code == 409

    # Settle: debtor claims, owner confirms → expense SETTLED
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/settle",
        headers=member_headers,
    )
    assert r.status_code == 201
    claim_id = r.json()["id"]
    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim_id}/confirm",
        headers=owner_headers,
    )
    assert r.status_code == 200

    # Now the debtor can delete their account — softly
    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=member_headers)
    assert r.status_code == 200

    db.expire_all()
    deleted = db.get(User, member_id)
    assert deleted is not None
    assert deleted.is_active is False
    assert deleted.deleted_at is not None
    assert deleted.email.startswith("deleted-")
    assert deleted.full_name == "Deleted User"

    # Shared financial history survives the deletion intact
    db_expense = db.get(Expense, uuid.UUID(expense["id"]))
    assert db_expense is not None
    assert db_expense.status == ExpenseStatus.SETTLED
    member_split = db.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.expense_id == uuid.UUID(expense["id"]))
        .where(ExpenseSplit.user_id == member_id)
    ).one()
    assert member_split.status == SplitStatus.SETTLED
    assert (
        db.exec(
            select(AuditLog).where(
                AuditLog.expense_id == uuid.UUID(expense["id"])
            )
        ).first()
        is not None
    )

    # The payer is fully settled too and may also leave
    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=owner_headers)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# M9 — 404 guard on GET /users/{id}
# ---------------------------------------------------------------------------


def test_read_user_by_id_endpoint_removed(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """GET /users/{id} was template admin surface; WS8 deleted it outright
    (the WS4/M9 404-guard fix is moot — the whole route is gone)."""
    r = client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# M1 — dashboard balances are exact decimal strings
# ---------------------------------------------------------------------------


def test_dashboard_balances_exact_decimal_strings(
    client: TestClient, db: Session
) -> None:
    expense, owner_headers, member_headers, _, _ = _two_member_expense_with_split(
        client, db
    )
    for headers in (member_headers, owner_headers):
        r = client.post(
            f"{settings.API_V1_STR}/expenses/{expense['id']}/confirm",
            headers=headers,
        )
        assert r.status_code == 200

    r = client.get(f"{settings.API_V1_STR}/users/me/dashboard", headers=owner_headers)
    assert r.status_code == 200
    data = r.json()
    group_row = next(
        g for g in data["groups"] if g["group_id"] == expense["group_id"]
    )
    # Exact decimal strings, not floats: the payer is owed exactly half
    assert group_row["net_balance"] == "50.00"

    r = client.get(
        f"{settings.API_V1_STR}/users/me/dashboard", headers=member_headers
    )
    member_row = next(
        g for g in r.json()["groups"] if g["group_id"] == expense["group_id"]
    )
    assert member_row["net_balance"] == "-50.00"
