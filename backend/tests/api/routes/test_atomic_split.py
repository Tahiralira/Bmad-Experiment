"""
Atomic create-with-split endpoint + participant notification (audit findings
F1/F9/F10/F8).

Before these, POST /expenses only ever created a bare DRAFT and the client
had to chain a second PUT /{id}/split call — which the UI skipped by default,
so expenses shipped with no splits at all. The create endpoint now takes an
optional `split` body and does both in one transaction.
"""
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.features.auth.models import UserCreate
from app.features.expenses.models import Expense, ExpenseStatus
from app.features.notifications.models import (
    EVENT_EXPENSE_SPLIT_ASSIGNED,
    Notification,
)
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)


def _authed_user(db: Session) -> tuple[dict[str, str], uuid.UUID]:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    return token_headers_for_user(user), user.id


def _two_member_group(
    client: TestClient, db: Session
) -> tuple[str, dict[str, str], uuid.UUID, dict[str, str], uuid.UUID]:
    owner_headers, owner_id = _authed_user(db)
    member_headers, member_id = _authed_user(db)
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=owner_headers,
        json={"name": f"Atomic {uuid.uuid4().hex[:8]}"},
    )
    assert r.status_code == 201
    group = r.json()
    # Invite + accept so the group has two members
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=owner_headers,
    )
    assert r.status_code == 201
    token = r.json()["invite"]["token"]
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/invite/{token}/accept",
        headers=member_headers,
    )
    assert r.status_code == 200
    return group["id"], owner_headers, owner_id, member_headers, member_id


def test_create_with_equal_split_persists_splits_and_goes_pending(
    client: TestClient, db: Session
) -> None:
    """The atomic path writes the splits and moves the expense into
    confirmation in ONE call — no separate PUT /split needed (F1/F9)."""
    group_id, owner_headers, _owner_id, _member_headers, _member_id = (
        _two_member_group(client, db)
    )

    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=owner_headers,
        json={
            "group_id": group_id,
            "amount": "100.00",
            "description": "Dinner",
            "split": {"type": "equal"},
        },
    )
    assert r.status_code == 200
    expense = r.json()
    # The expense left DRAFT the moment it was split
    assert expense["status"] == ExpenseStatus.PENDING_CONFIRMATION.value

    r = client.get(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/splits",
        headers=owner_headers,
    )
    assert r.status_code == 200
    splits = r.json()
    assert splits["count"] == 2
    total = sum(Decimal(s["amount_owed"]) for s in splits["data"])
    assert total == Decimal("100.00")


def test_create_with_bad_split_is_atomic_no_orphan_draft(
    client: TestClient, db: Session
) -> None:
    """A domain-invalid split rolls the whole request back — the expense is
    NOT left behind as a split-less DRAFT (the F9 orphan the two-call flow
    could produce)."""
    group_id, owner_headers, _owner_id, _member_headers, _member_id = (
        _two_member_group(client, db)
    )
    stranger = uuid.uuid4()  # not a member of this group

    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=owner_headers,
        json={
            "group_id": group_id,
            "amount": "100.00",
            "description": "Should not persist",
            "split": {"type": "equal", "excluded_user_ids": [str(stranger)]},
        },
    )
    assert r.status_code == 400

    # Nothing was committed — the group has no expenses at all
    remaining = db.exec(
        select(Expense).where(Expense.group_id == uuid.UUID(group_id))
    ).all()
    assert remaining == []


def test_create_with_duplicate_participant_unequal_is_400(
    client: TestClient, db: Session
) -> None:
    """A repeated member in an unequal split is a clean 400, not the raw 500
    the unique constraint used to throw (F10)."""
    group_id, owner_headers, owner_id, _member_headers, _member_id = (
        _two_member_group(client, db)
    )

    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=owner_headers,
        json={
            "group_id": group_id,
            "amount": "100.00",
            "description": "Dup member",
            "split": {
                "type": "unequal",
                "splits": [
                    {"user_id": str(owner_id), "amount": "50.00"},
                    {"user_id": str(owner_id), "amount": "50.00"},
                ],
            },
        },
    )
    assert r.status_code == 400


def test_split_assignment_notifies_non_payer_only(
    client: TestClient, db: Session
) -> None:
    """Each non-payer participant is told they have a share to confirm; the
    payer is not notified about their own expense (F8)."""
    group_id, owner_headers, owner_id, _member_headers, member_id = (
        _two_member_group(client, db)
    )

    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=owner_headers,
        json={
            "group_id": group_id,
            "amount": "100.00",
            "description": "Groceries",
            "split": {"type": "equal"},
        },
    )
    assert r.status_code == 200

    db.expire_all()
    member_notes = db.exec(
        select(Notification).where(
            Notification.user_id == member_id,
            Notification.event_type == EVENT_EXPENSE_SPLIT_ASSIGNED,
        )
    ).all()
    assert len(member_notes) >= 1

    payer_notes = db.exec(
        select(Notification).where(
            Notification.user_id == owner_id,
            Notification.event_type == EVENT_EXPENSE_SPLIT_ASSIGNED,
        )
    ).all()
    assert payer_notes == []
