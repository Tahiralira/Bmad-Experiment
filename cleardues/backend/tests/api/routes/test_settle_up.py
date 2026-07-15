"""WS6 — Aggregate settle-up + confirmation policy tests.

Covers execution-plan Work Session 6:
- POST /expenses/settlement-claims/aggregate  ("Settle with X" netting)
- GET  /expenses/settlement-claims/aggregate  (pending settle-ups, both roles)
- GET  /expense-groups/{id}/pairwise-balances (who owes whom exactly, S2-F9)
- GET/PATCH /expense-groups/{id}/settings     (strict mode toggle)
- 72h settlement auto-confirm with owner dispute window
- non-strict expense auto-confirm after the objection window

The acceptance scenario: a 12-expense pile between one pair settles in ONE
claim and ONE confirmation.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.features.auth.models import UserCreate
from app.features.expenses.models import (
    Expense,
    ExpenseSplit,
    SettlementClaim,
)
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)


# ---------------------------------------------------------------------------
# Helpers (same shape as test_ledger_api.py)
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


def _confirmed_expense(
    client: TestClient,
    payer_headers: dict[str, str],
    confirmer_headers_list: list[dict[str, str]],
    group_id: str,
    amount: str = "100.00",
    description: str = "Settle-up test expense",
) -> dict:
    """Create an expense, equal-split it, and have every participant confirm."""
    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=payer_headers,
        json={"group_id": group_id, "amount": amount, "description": description},
    )
    assert r.status_code == 200
    expense = r.json()

    r = client.put(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
        headers=payer_headers,
        json={"type": "equal"},
    )
    assert r.status_code == 200

    for headers in confirmer_headers_list:
        r = client.post(
            f"{settings.API_V1_STR}/expenses/{expense['id']}/confirm",
            headers=headers,
        )
        assert r.status_code == 200

    return expense


def _two_member_group(
    client: TestClient, db: Session
) -> tuple[dict, dict[str, str], dict[str, str], uuid.UUID, uuid.UUID]:
    owner_headers, owner_id, _ = _make_authed_user(client, db)
    member_headers, member_id, _ = _make_authed_user(client, db)
    group = _create_group(client, owner_headers, f"WS6 {uuid.uuid4().hex[:8]}")
    _join_group(client, group["id"], owner_headers, member_headers)
    return group, owner_headers, member_headers, owner_id, member_id


def _settle_up(
    client: TestClient,
    headers: dict[str, str],
    group_id: str,
    counterparty_user_id: uuid.UUID,
) -> "object":
    return client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/aggregate",
        headers=headers,
        json={
            "group_id": group_id,
            "counterparty_user_id": str(counterparty_user_id),
        },
    )


def _expense_status(db: Session, expense_id: str) -> str:
    db.expire_all()
    expense = db.get(Expense, uuid.UUID(expense_id))
    return expense.status.value


def _split_statuses(db: Session, expense_id: str) -> list[str]:
    db.expire_all()
    splits = db.exec(
        select(ExpenseSplit).where(
            ExpenseSplit.expense_id == uuid.UUID(expense_id)
        )
    ).all()
    return [s.status.value for s in splits]


def _backdate_claim(db: Session, claim_id: str, hours: int) -> None:
    claim = db.get(SettlementClaim, uuid.UUID(claim_id))
    claim.claimed_at = datetime.now(timezone.utc) - timedelta(hours=hours)
    db.add(claim)
    db.commit()


def _backdate_expense_splits(db: Session, expense_id: str, days: int) -> None:
    splits = db.exec(
        select(ExpenseSplit).where(
            ExpenseSplit.expense_id == uuid.UUID(expense_id)
        )
    ).all()
    for split in splits:
        split.created_at = datetime.now(timezone.utc) - timedelta(days=days)
        db.add(split)
    db.commit()


# ---------------------------------------------------------------------------
# THE acceptance scenario: 12 expenses → one claim → one confirm
# ---------------------------------------------------------------------------


def test_twelve_expense_scenario_settles_in_one_claim_one_confirm(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)

    expenses = [
        _confirmed_expense(
            client, owner_h, [owner_h, member_h], group["id"],
            amount="100.00", description=f"Trip expense {i}",
        )
        for i in range(12)
    ]

    # Pairwise balance before: member owes owner 12 × 50
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/pairwise-balances",
        headers=member_h,
    )
    assert r.status_code == 200
    balances = r.json()["data"]
    assert len(balances) == 1
    assert balances[0]["user_id"] == str(owner_id)
    assert balances[0]["you_owe_them"] == "600.00"
    assert balances[0]["they_owe_you"] == "0.00"
    assert balances[0]["net"] == "-600.00"

    # ONE claim covers all 12 expenses
    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 201
    claim = r.json()
    assert claim["amount"] == "600.00"
    assert claim["expense_split_id"] is None
    assert claim["group_id"] == group["id"]
    assert claim["counterparty_user_id"] == str(owner_id)
    assert claim["covered_split_count"] == 12
    assert claim["covered_expense_count"] == 12
    assert claim["status"] == "pending"
    assert claim["auto_confirm_at"] is not None

    # ONE confirmation settles everything
    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim['id']}/confirm",
        headers=owner_h,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "confirmed"

    for expense in expenses:
        assert _expense_status(db, expense["id"]) == "settled"
        assert set(_split_statuses(db, expense["id"])) == {"settled"}

    # Balances are cleared on both sides
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/pairwise-balances",
        headers=member_h,
    )
    assert r.json()["data"] == []
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}", headers=owner_h
    )
    assert r.json()["net_balance"] == "0.00"

    # Audit fan-out: every covered expense records the settle-up
    r = client.get(
        f"{settings.API_V1_STR}/expenses/{expenses[0]['id']}/audit-log",
        headers=owner_h,
    )
    entries = r.json()["data"]
    settled = [e for e in entries if e["action_type"] == "settled"]
    assert any(
        (e["changes_json"] or {}).get("after", {}).get("settle_up") for e in settled
    )


# ---------------------------------------------------------------------------
# Netting math
# ---------------------------------------------------------------------------


def test_netting_across_both_directions(client: TestClient, db: Session) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)

    # Owner pays 100 → member owes 50; member pays 40 → owner owes 20
    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )
    e2 = _confirmed_expense(
        client, member_h, [owner_h, member_h], group["id"], amount="40.00"
    )

    # Member owes the net: 50 - 20 = 30
    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 201
    claim = r.json()
    assert claim["amount"] == "30.00"
    assert claim["covered_split_count"] == 2
    assert claim["covered_expense_count"] == 2

    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim['id']}/confirm",
        headers=owner_h,
    )
    assert r.status_code == 200

    # BOTH directions cleared
    assert _expense_status(db, e1["id"]) == "settled"
    assert _expense_status(db, e2["id"]) == "settled"


def test_zero_net_settle_up_clears_even_pair(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)

    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="80.00"
    )
    e2 = _confirmed_expense(
        client, member_h, [owner_h, member_h], group["id"], amount="80.00"
    )

    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 201
    claim = r.json()
    assert claim["amount"] == "0.00"

    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim['id']}/confirm",
        headers=owner_h,
    )
    assert r.status_code == 200
    assert _expense_status(db, e1["id"]) == "settled"
    assert _expense_status(db, e2["id"]) == "settled"


def test_wrong_direction_settle_up_rejected(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )

    # The OWNER is owed — they cannot claim they paid the member
    r = _settle_up(client, owner_h, group["id"], member_id)
    assert r.status_code == 400
    assert "settle up with you" in r.json()["detail"]


def test_nothing_to_settle_rejected(client: TestClient, db: Session) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 400
    assert "all settled" in r.json()["detail"]


def test_settle_up_validation(client: TestClient, db: Session) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    outsider_h, outsider_id, _ = _make_authed_user(client, db)

    # Self-settle
    r = _settle_up(client, member_h, group["id"], member_id)
    assert r.status_code == 400

    # Counterparty not a member
    r = _settle_up(client, member_h, group["id"], outsider_id)
    assert r.status_code == 400

    # Caller not a member
    r = _settle_up(client, outsider_h, group["id"], owner_id)
    assert r.status_code == 403

    # Group not found
    r = _settle_up(client, member_h, str(uuid.uuid4()), owner_id)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Interaction with the per-expense path (kept for partial payments)
# ---------------------------------------------------------------------------


def test_per_expense_claim_excluded_from_netting(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)

    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )
    _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="60.00"
    )

    # Member already claimed e1 individually (in-flight)
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{e1['id']}/settle", headers=member_h
    )
    assert r.status_code == 201

    # Settle-up nets only the unclaimed expense (60 / 2 = 30)
    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 201
    assert r.json()["amount"] == "30.00"
    assert r.json()["covered_split_count"] == 1


def test_per_expense_settle_conflicts_with_aggregate_coverage(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )

    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 201

    # The split is spoken for by the pending settle-up
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{e1['id']}/settle", headers=member_h
    )
    assert r.status_code == 409

    # And a second settle-up finds nothing left to cover
    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 400


def test_partial_coverage_leaves_third_member_untouched(
    client: TestClient, db: Session
) -> None:
    owner_h, owner_id, _ = _make_authed_user(client, db)
    member_h, member_id, _ = _make_authed_user(client, db)
    third_h, third_id, _ = _make_authed_user(client, db)
    group = _create_group(client, owner_h, f"WS6 trio {uuid.uuid4().hex[:8]}")
    _join_group(client, group["id"], owner_h, member_h)
    _join_group(client, group["id"], owner_h, third_h)

    # 90 split three ways: member and third each owe owner 30
    expense = _confirmed_expense(
        client, owner_h, [owner_h, member_h, third_h], group["id"], amount="90.00"
    )

    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 201
    assert r.json()["amount"] == "30.00"

    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{r.json()['id']}/confirm",
        headers=owner_h,
    )
    assert r.status_code == 200

    # Third member's debt is untouched; the expense is NOT settled yet
    assert _expense_status(db, expense["id"]) == "confirmed"
    db.expire_all()
    third_split = db.exec(
        select(ExpenseSplit).where(
            ExpenseSplit.expense_id == uuid.UUID(expense["id"]),
            ExpenseSplit.user_id == third_id,
        )
    ).one()
    assert third_split.status.value == "confirmed"


# ---------------------------------------------------------------------------
# Aggregate claim review flow (confirm / reject / list)
# ---------------------------------------------------------------------------


def test_only_counterparty_can_process_aggregate_claim(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )

    r = _settle_up(client, member_h, group["id"], owner_id)
    claim_id = r.json()["id"]

    # The claimant cannot confirm their own claim
    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim_id}/confirm",
        headers=member_h,
    )
    assert r.status_code == 403
    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim_id}/reject",
        headers=member_h,
    )
    assert r.status_code == 403


def test_aggregate_reject_allows_reclaim(client: TestClient, db: Session) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )

    r = _settle_up(client, member_h, group["id"], owner_id)
    claim_id = r.json()["id"]

    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim_id}/reject",
        headers=owner_h,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert r.json()["rejected_at"] is not None

    # Nothing settled; the debt stands and can be re-claimed
    assert _expense_status(db, e1["id"]) == "confirmed"
    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 201


def test_aggregate_claims_list_shows_both_roles(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )

    r = _settle_up(client, member_h, group["id"], owner_id)
    assert r.status_code == 201

    # Claimant sees it
    r = client.get(
        f"{settings.API_V1_STR}/expenses/settlement-claims/aggregate",
        headers=member_h,
        params={"group_id": group["id"]},
    )
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["data"][0]["claimant_user_id"] == str(member_id)

    # Counterparty sees it too
    r = client.get(
        f"{settings.API_V1_STR}/expenses/settlement-claims/aggregate",
        headers=owner_h,
        params={"group_id": group["id"]},
    )
    assert r.json()["count"] == 1
    assert r.json()["data"][0]["counterparty_user_id"] == str(owner_id)


# ---------------------------------------------------------------------------
# Pairwise balances (S2-F9)
# ---------------------------------------------------------------------------


def test_pairwise_balances_math_with_three_members(
    client: TestClient, db: Session
) -> None:
    owner_h, owner_id, _ = _make_authed_user(client, db)
    member_h, member_id, _ = _make_authed_user(client, db)
    third_h, third_id, _ = _make_authed_user(client, db)
    group = _create_group(client, owner_h, f"WS6 pw {uuid.uuid4().hex[:8]}")
    _join_group(client, group["id"], owner_h, member_h)
    _join_group(client, group["id"], owner_h, third_h)

    # Owner pays 90 (member + third each owe 30); member pays 30 (owner and
    # third each owe 10)
    _confirmed_expense(
        client, owner_h, [owner_h, member_h, third_h], group["id"], amount="90.00"
    )
    _confirmed_expense(
        client, member_h, [owner_h, member_h, third_h], group["id"], amount="30.00"
    )

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/pairwise-balances",
        headers=owner_h,
    )
    assert r.status_code == 200
    by_id = {item["user_id"]: item for item in r.json()["data"]}

    member_row = by_id[str(member_id)]
    assert member_row["they_owe_you"] == "30.00"
    assert member_row["you_owe_them"] == "10.00"
    assert member_row["net"] == "20.00"

    third_row = by_id[str(third_id)]
    assert third_row["they_owe_you"] == "30.00"
    assert third_row["you_owe_them"] == "0.00"
    assert third_row["net"] == "30.00"


def test_pairwise_balances_member_only(client: TestClient, db: Session) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    outsider_h, _, _ = _make_authed_user(client, db)
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/pairwise-balances",
        headers=outsider_h,
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# 72h auto-confirm + dispute window
# ---------------------------------------------------------------------------


def test_expired_per_expense_claim_auto_confirms_on_read(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )

    r = client.post(
        f"{settings.API_V1_STR}/expenses/{e1['id']}/settle", headers=member_h
    )
    assert r.status_code == 201
    claim = r.json()
    assert claim["auto_confirm_at"] is not None

    _backdate_claim(db, claim["id"], hours=73)

    # The owner's worklist sweep confirms the expired claim
    r = client.get(
        f"{settings.API_V1_STR}/expenses/settlement-claims/pending-for-owner",
        headers=owner_h,
    )
    assert r.status_code == 200
    assert all(item["claim"]["id"] != claim["id"] for item in r.json())

    assert _expense_status(db, e1["id"]) == "settled"

    # The audit trail records the silence-was-consent confirmation
    r = client.get(
        f"{settings.API_V1_STR}/expenses/{e1['id']}/audit-log", headers=owner_h
    )
    assert any(
        "auto_confirmed" in ((e["changes_json"] or {}).get("after") or {})
        for e in r.json()["data"]
    )


def test_expired_aggregate_claim_auto_confirms_on_read(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )

    r = _settle_up(client, member_h, group["id"], owner_id)
    claim = r.json()
    _backdate_claim(db, claim["id"], hours=73)

    r = client.get(
        f"{settings.API_V1_STR}/expenses/settlement-claims/aggregate",
        headers=owner_h,
        params={"group_id": group["id"]},
    )
    assert r.status_code == 200
    assert r.json()["count"] == 0

    assert _expense_status(db, e1["id"]) == "settled"


def test_reject_after_dispute_window_confirms_instead(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )

    r = client.post(
        f"{settings.API_V1_STR}/expenses/{e1['id']}/settle", headers=member_h
    )
    claim = r.json()
    _backdate_claim(db, claim["id"], hours=73)

    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim['id']}/reject",
        headers=owner_h,
    )
    assert r.status_code == 409
    assert "dispute window" in r.json()["detail"]
    assert _expense_status(db, e1["id"]) == "settled"


def test_fresh_claim_is_not_swept(client: TestClient, db: Session) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    e1 = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{e1['id']}/settle", headers=member_h
    )
    claim = r.json()

    r = client.get(
        f"{settings.API_V1_STR}/expenses/settlement-claims/pending-for-owner",
        headers=owner_h,
    )
    assert any(item["claim"]["id"] == claim["id"] for item in r.json())
    assert _expense_status(db, e1["id"]) == "confirmed"


# ---------------------------------------------------------------------------
# Strict mode (per-group confirmation policy)
# ---------------------------------------------------------------------------


def test_group_settings_default_and_owner_only_toggle(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
        headers=member_h,
    )
    assert r.status_code == 200
    assert r.json()["strict_mode"] is False

    # Members cannot toggle
    r = client.patch(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
        headers=member_h,
        json={"strict_mode": True},
    )
    assert r.status_code == 403

    # The owner can
    r = client.patch(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
        headers=owner_h,
        json={"strict_mode": True},
    )
    assert r.status_code == 200
    assert r.json()["strict_mode"] is True

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
        headers=owner_h,
    )
    assert r.json()["strict_mode"] is True


def test_non_strict_expense_auto_confirms_after_window(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)

    # Split assigned but nobody confirms
    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=owner_h,
        json={"group_id": group["id"], "amount": "100.00",
              "description": "Quiet consent"},
    )
    expense = r.json()
    r = client.put(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
        headers=owner_h,
        json={"type": "equal"},
    )
    assert r.status_code == 200

    _backdate_expense_splits(db, expense["id"], days=4)

    # Any group read sweeps it to confirmed
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/expenses",
        headers=member_h,
    )
    assert r.status_code == 200
    row = next(
        item for item in r.json()["data"] if item["expense"]["id"] == expense["id"]
    )
    assert row["expense"]["status"] == "confirmed"
    assert set(_split_statuses(db, expense["id"])) == {"confirmed"}

    # Audit records the no-objection confirmation
    r = client.get(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/audit-log",
        headers=owner_h,
    )
    assert any(
        "auto_confirmed" in ((e["changes_json"] or {}).get("after") or {})
        for e in r.json()["data"]
        if e["action_type"] == "confirmed"
    )


def test_strict_mode_expense_never_auto_confirms(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)

    r = client.patch(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
        headers=owner_h,
        json={"strict_mode": True},
    )
    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=owner_h,
        json={"group_id": group["id"], "amount": "100.00",
              "description": "Strict ceremony"},
    )
    expense = r.json()
    r = client.put(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
        headers=owner_h,
        json={"type": "equal"},
    )
    assert r.status_code == 200

    _backdate_expense_splits(db, expense["id"], days=10)

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/expenses",
        headers=member_h,
    )
    row = next(
        item for item in r.json()["data"] if item["expense"]["id"] == expense["id"]
    )
    assert row["expense"]["status"] == "pending_confirmation"


def test_non_strict_member_can_still_reject_within_window(
    client: TestClient, db: Session
) -> None:
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)

    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=owner_h,
        json={"group_id": group["id"], "amount": "100.00",
              "description": "Objection window"},
    )
    expense = r.json()
    r = client.put(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
        headers=owner_h,
        json={"type": "equal"},
    )
    assert r.status_code == 200

    # Confirmation is opt-in, rejection still works (consent re-opens)
    r = client.post(
        f"{settings.API_V1_STR}/expenses/{expense['id']}/reject",
        headers=member_h,
    )
    assert r.status_code == 200
    assert _expense_status(db, expense["id"]) == "draft"
