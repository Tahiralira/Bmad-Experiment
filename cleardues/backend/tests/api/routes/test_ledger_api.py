"""WS5 — Ledger API tests (B-H7, S4-M6, B-M2).

Covers the read endpoints added in execution-plan Work Session 5:
- GET /expenses/{id}                       (single expense, member-only)
- GET /expenses/{id}/splits                (who owes what, with names)
- GET /expense-groups/{id}                 (group detail + net balance)
- GET /expense-groups/{id}/expenses        (ledger list with my_split)
- GET /expenses/settlement-claims/pending-for-owner?group_id= (S4-M6 scope)
- dashboard last_activity reflects expense writes, not just group renames
  (B-M2)
"""
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.features.auth.models import UserCreate
from tests.utils.utils import random_email, random_lower_string


# ---------------------------------------------------------------------------
# Helpers (same shape as test_ledger_integrity.py)
# ---------------------------------------------------------------------------


def _make_authed_user(
    client: TestClient, db: Session
) -> tuple[dict[str, str], uuid.UUID, str]:
    """Create a fresh user and log in; returns (headers, user_id, email)."""
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    assert r.status_code == 200
    return (
        {"Authorization": f"Bearer {r.json()['access_token']}"},
        user.id,
        email,
    )


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
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{token}", headers=member_headers
    )
    assert r.status_code == 200


def _create_expense(
    client: TestClient,
    headers: dict[str, str],
    group_id: str,
    amount: str = "100.00",
    description: str = "Ledger API test expense",
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


def _two_member_group(
    client: TestClient, db: Session
) -> tuple[dict, dict[str, str], dict[str, str], uuid.UUID, uuid.UUID]:
    owner_headers, owner_id, _ = _make_authed_user(client, db)
    member_headers, member_id, _ = _make_authed_user(client, db)
    group = _create_group(client, owner_headers, f"WS5 {uuid.uuid4().hex[:8]}")
    _join_group(client, group["id"], owner_headers, member_headers)
    return group, owner_headers, member_headers, owner_id, member_id


def _confirm(client: TestClient, headers: dict[str, str], expense_id: str) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{expense_id}/confirm", headers=headers
    )
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# GET /expenses/{id}
# ---------------------------------------------------------------------------


def test_get_expense_member_only(client: TestClient, db: Session) -> None:
    group, owner_headers, member_headers, _, _ = _two_member_group(client, db)
    expense = _create_expense(client, owner_headers, group["id"])

    # A member (not just the creator) can read it
    r = client.get(
        f"{settings.API_V1_STR}/expenses/{expense['id']}", headers=member_headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == expense["id"]
    assert body["amount"] == "100.00"
    assert body["status"] == "draft"

    # A non-member gets 403
    outsider_headers, _, _ = _make_authed_user(client, db)
    r = client.get(
        f"{settings.API_V1_STR}/expenses/{expense['id']}", headers=outsider_headers
    )
    assert r.status_code == 403

    # Nonexistent expense is 404
    r = client.get(
        f"{settings.API_V1_STR}/expenses/{uuid.uuid4()}", headers=owner_headers
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /expense-groups/{id}/expenses — the group ledger
# ---------------------------------------------------------------------------


def test_list_group_expenses_with_my_split(client: TestClient, db: Session) -> None:
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)

    split_expense = _create_expense(
        client, owner_headers, group["id"], description="Split one"
    )
    _equal_split(client, owner_headers, split_expense["id"])
    draft_expense = _create_expense(
        client, owner_headers, group["id"], amount="40.00", description="Draft one"
    )

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/expenses",
        headers=member_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2

    # Newest first
    assert body["data"][0]["expense"]["id"] == draft_expense["id"]
    assert body["data"][1]["expense"]["id"] == split_expense["id"]

    # my_split attached where the member holds a split, null otherwise
    assert body["data"][0]["my_split"] is None
    my_split = body["data"][1]["my_split"]
    assert my_split is not None
    assert my_split["user_id"] == str(member_id)
    assert my_split["amount_owed"] == "50.00"
    assert my_split["status"] == "pending"

    # Non-member gets 403
    outsider_headers, _, _ = _make_authed_user(client, db)
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/expenses",
        headers=outsider_headers,
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /expenses/{id}/splits — who owes what
# ---------------------------------------------------------------------------


def test_get_expense_splits_with_names(client: TestClient, db: Session) -> None:
    group, owner_headers, member_headers, owner_id, member_id = _two_member_group(
        client, db
    )
    expense = _create_expense(client, owner_headers, group["id"])
    _equal_split(client, owner_headers, expense["id"])

    r = client.get(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/splits",
        headers=member_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    by_user = {s["user_id"]: s for s in body["data"]}
    assert set(by_user) == {str(owner_id), str(member_id)}
    for split in body["data"]:
        assert split["amount_owed"] == "50.00"
        assert split["user_name"]  # name or email is always populated


# ---------------------------------------------------------------------------
# GET /expense-groups/{id} — group detail with net balance
# ---------------------------------------------------------------------------


def test_group_detail_membership_and_balance(
    client: TestClient, db: Session
) -> None:
    group, owner_headers, member_headers, _, _ = _two_member_group(client, db)

    # Before any confirmed expense the balance is zero
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}", headers=owner_headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == group["id"]
    assert body["member_count"] == 2
    assert body["net_balance"] == "0.00"

    # Confirm a 100.00 equal-split expense paid by the owner
    expense = _create_expense(client, owner_headers, group["id"])
    _equal_split(client, owner_headers, expense["id"])
    _confirm(client, member_headers, expense["id"])
    _confirm(client, owner_headers, expense["id"])

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}", headers=owner_headers
    )
    assert r.json()["net_balance"] == "50.00"

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}", headers=member_headers
    )
    assert r.json()["net_balance"] == "-50.00"

    # Non-member gets 403, nonexistent group 404
    outsider_headers, _, _ = _make_authed_user(client, db)
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}",
        headers=outsider_headers,
    )
    assert r.status_code == 403
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{uuid.uuid4()}", headers=owner_headers
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# S4-M6 — group-scoped pending settlement claims
# ---------------------------------------------------------------------------


def test_pending_claims_for_owner_group_scope(
    client: TestClient, db: Session
) -> None:
    owner_headers, _, _ = _make_authed_user(client, db)
    member_headers, _, _ = _make_authed_user(client, db)

    group_a = _create_group(client, owner_headers, f"WS5A {uuid.uuid4().hex[:8]}")
    group_b = _create_group(client, owner_headers, f"WS5B {uuid.uuid4().hex[:8]}")
    _join_group(client, group_a["id"], owner_headers, member_headers)
    _join_group(client, group_b["id"], owner_headers, member_headers)

    # One confirmed + claimed expense per group
    claims = {}
    for group in (group_a, group_b):
        expense = _create_expense(client, owner_headers, group["id"])
        _equal_split(client, owner_headers, expense["id"])
        _confirm(client, member_headers, expense["id"])
        _confirm(client, owner_headers, expense["id"])
        r = client.post(
            f"{settings.API_V1_STR}/expenses/{expense['id']}/settle",
            headers=member_headers,
        )
        assert r.status_code == 201
        claims[group["id"]] = expense["id"]

    # Unscoped: both claims
    r = client.get(
        f"{settings.API_V1_STR}/expenses/settlement-claims/pending-for-owner",
        headers=owner_headers,
    )
    assert r.status_code == 200
    expense_ids = {item["expense"]["id"] for item in r.json()}
    assert claims[group_a["id"]] in expense_ids
    assert claims[group_b["id"]] in expense_ids

    # Scoped to group A: only group A's claim (S4-M6 — the group screen must
    # not attribute other groups' claims to this group)
    r = client.get(
        f"{settings.API_V1_STR}/expenses/settlement-claims/pending-for-owner",
        headers=owner_headers,
        params={"group_id": group_a["id"]},
    )
    assert r.status_code == 200
    scoped = [item["expense"]["id"] for item in r.json()]
    assert scoped == [claims[group_a["id"]]]


# ---------------------------------------------------------------------------
# B-M2 — dashboard last_activity reflects expense writes
# ---------------------------------------------------------------------------


def test_dashboard_last_activity_reflects_expense_writes(
    client: TestClient, db: Session
) -> None:
    owner_headers, _, _ = _make_authed_user(client, db)
    member_headers, _, _ = _make_authed_user(client, db)

    group_old = _create_group(client, owner_headers, f"WS5old {uuid.uuid4().hex[:8]}")
    group_new = _create_group(client, owner_headers, f"WS5new {uuid.uuid4().hex[:8]}")
    _join_group(client, group_old["id"], owner_headers, member_headers)

    # Baseline: the later-created group leads the dashboard
    r = client.get(f"{settings.API_V1_STR}/users/me/dashboard", headers=owner_headers)
    assert r.status_code == 200
    order = [g["group_id"] for g in r.json()["groups"]]
    assert order.index(group_new["id"]) < order.index(group_old["id"])

    # An expense write in the older group must move it to the top — the group
    # row itself never changes (B-M2: updated_at only moved on renames)
    expense = _create_expense(client, owner_headers, group_old["id"])
    _equal_split(client, owner_headers, expense["id"])

    r = client.get(f"{settings.API_V1_STR}/users/me/dashboard", headers=owner_headers)
    groups = {g["group_id"]: g for g in r.json()["groups"]}
    order = [g["group_id"] for g in r.json()["groups"]]
    assert order.index(group_old["id"]) < order.index(group_new["id"])
    assert (
        groups[group_old["id"]]["last_activity"]
        >= groups[group_new["id"]]["last_activity"]
    )
