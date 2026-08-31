"""WS12 — Nudge Engine: Infra + Level 1.

The load-bearing test in this file is
`test_twelve_expenses_produce_one_nudge`: nudges are per-relationship
per-group, never per-expense. Everything else guards the suppressors that
keep a reminder engine from becoming a nagging engine — cooldown, snooze,
mute, quiet hours, and the global kill switch.

Delivery itself is asserted through recorded outcomes rather than by
reaching a real push service: with no VAPID keypair configured, push
records SKIPPED, which is the honest behaviour of an unconfigured
deployment and the one every test run should see.
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.features.auth.models import UserCreate
from app.features.expenses.models import Expense
from app.features.notifications import service as nudge_service
from app.features.notifications.models import (
    EVENT_NUDGE_LEVEL_1,
    Notification,
    NotificationChannel,
    NotificationStatus,
    NudgeState,
    PushSubscription,
)
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)


# ---------------------------------------------------------------------------
# Helpers (same shape as test_settle_up.py)
# ---------------------------------------------------------------------------


def _make_authed_user(db: Session) -> tuple[dict[str, str], uuid.UUID]:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    return token_headers_for_user(user), user.id


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
        f"{settings.API_V1_STR}/expense-groups/invite/{token}/accept",
        headers=member_headers,
    )
    assert r.status_code == 200


def _confirmed_expense(
    client: TestClient,
    payer_headers: dict[str, str],
    confirmer_headers_list: list[dict[str, str]],  # EVERY participant, payer included
    group_id: str,
    amount: str = "100.00",
    description: str = "Nudge test expense",
) -> dict:
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
            f"{settings.API_V1_STR}/expenses/{expense['id']}/confirm", headers=headers
        )
        assert r.status_code == 200
    return expense


def _two_member_group(
    client: TestClient, db: Session
) -> tuple[dict, dict[str, str], dict[str, str], uuid.UUID, uuid.UUID]:
    owner_headers, owner_id = _make_authed_user(db)
    member_headers, member_id = _make_authed_user(db)
    group = _create_group(client, owner_headers, f"WS12 {uuid.uuid4().hex[:8]}")
    _join_group(client, group["id"], owner_headers, member_headers)
    return group, owner_headers, member_headers, owner_id, member_id


def _age_expenses(db: Session, group_id: str, hours: int) -> None:
    """
    Backdate a group's confirmed expenses so the debt is old enough to nudge.
    Faster and more honest than sleeping, and it exercises the same
    `confirmed_at`-based age arithmetic the engine uses in production.
    """
    past = datetime.now(timezone.utc) - timedelta(hours=hours)
    expenses = db.exec(
        select(Expense).where(Expense.group_id == uuid.UUID(group_id))
    ).all()
    for expense in expenses:
        expense.confirmed_at = past
        db.add(expense)
    db.commit()


def _notifications_for(db: Session, user_id: uuid.UUID) -> list[Notification]:
    db.expire_all()
    return list(
        db.exec(
            select(Notification).where(Notification.user_id == user_id)
        ).all()
    )


# ---------------------------------------------------------------------------
# The core contract: per-relationship, per-group — never per-expense
# ---------------------------------------------------------------------------


def test_twelve_expenses_produce_one_nudge(client: TestClient, db: Session) -> None:
    """
    Twelve unsettled dinners between the same two people are ONE debt and
    must produce ONE reminder. This is the failure mode 02 Phase B named:
    a per-expense engine would send twelve notifications for one dinner
    habit and be uninstalled the same evening.
    """
    group, owner_headers, member_headers, owner_id, member_id = _two_member_group(
        client, db
    )
    for i in range(12):
        _confirmed_expense(
            client,
            owner_headers,
            [owner_headers, member_headers],
            group["id"],
            amount="50.00",
            description=f"Dinner {i} {uuid.uuid4().hex[:6]}",
        )
    _age_expenses(db, group["id"], hours=48)

    result = nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()

    # ONE relationship, examined once — not twelve expenses examined twelve
    # times. Delivery outcomes are deliberately not asserted here: whether a
    # channel actually lands depends on ambient SMTP/VAPID config, and this
    # test is about the unit of nudging, not about transport (WS10.6's
    # lesson — tests must not depend on ambient .env config).
    assert result.relationships_examined == 1

    borrower_notifications = _notifications_for(db, member_id)
    assert {n.event_type for n in borrower_notifications} == {EVENT_NUDGE_LEVEL_1}
    # Every record describes the SAME single debt: 12 × 50.00 split two ways
    # = 25.00 each = 300.00 owed, as one number rather than twelve.
    assert {n.amount for n in borrower_notifications} == {Decimal("300.00")}
    # At most one attempt per channel — never one per expense.
    assert len(borrower_notifications) == len(
        {n.channel for n in borrower_notifications}
    )

    # The lender is owed money and is never nudged about it.
    assert _notifications_for(db, owner_id) == []

    # Exactly one state row exists for the relationship — the schema has
    # nowhere to put a per-expense nudge.
    states = db.exec(
        select(NudgeState).where(NudgeState.group_id == uuid.UUID(group["id"]))
    ).all()
    assert len(states) == 1
    assert states[0].user_id == member_id
    assert states[0].counterparty_user_id == owner_id


def test_mutual_debt_nets_and_only_the_net_debtor_is_nudged(
    client: TestClient, db: Session
) -> None:
    """A owes B 100, B owes A 60 → one debt of 40, and only A hears about it."""
    group, owner_headers, member_headers, owner_id, member_id = _two_member_group(
        client, db
    )
    # Owner pays 200 → member owes 100.
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="200.00"
    )
    # Member pays 120 → owner owes 60.
    _confirmed_expense(
        client, member_headers, [member_headers, owner_headers], group["id"], amount="120.00"
    )
    _age_expenses(db, group["id"], hours=48)

    relationships = nudge_service.find_debt_relationships(
        db, group_id=uuid.UUID(group["id"])
    )
    assert len(relationships) == 1
    rel = relationships[0]
    assert rel.debtor_id == member_id
    assert rel.creditor_id == owner_id
    assert rel.amount == pytest.approx(40.00, abs=0.01)


def test_settled_debt_is_not_nudged(client: TestClient, db: Session) -> None:
    """Once the balance clears, the relationship drops out of the sweep."""
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="80.00"
    )
    _age_expenses(db, group["id"], hours=48)

    assert (
        len(nudge_service.find_debt_relationships(db, group_id=uuid.UUID(group["id"])))
        == 1
    )

    # Settle up and have the creditor confirm.
    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/aggregate",
        headers=member_headers,
        json={"group_id": group["id"], "counterparty_user_id": str(_owner_of(db, group))},
    )
    assert r.status_code in (200, 201)
    claim_id = r.json()["id"]
    r = client.post(
        f"{settings.API_V1_STR}/expenses/settlement-claims/{claim_id}/confirm",
        headers=owner_headers,
    )
    assert r.status_code == 200

    assert (
        nudge_service.find_debt_relationships(db, group_id=uuid.UUID(group["id"])) == []
    )


def _owner_of(db: Session, group: dict) -> uuid.UUID:
    return uuid.UUID(group["created_by"])


# ---------------------------------------------------------------------------
# Timing and the suppressors
# ---------------------------------------------------------------------------


def test_fresh_debt_is_below_the_age_threshold(
    client: TestClient, db: Session
) -> None:
    """
    A debt agreed to minutes ago gets no reminder. The first thing you see
    after confirming a split must not be a demand for the money.
    """
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="60.00"
    )

    result = nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()

    assert result.relationships_examined == 1
    assert _notifications_for(db, member_id) == []


def test_cooldown_makes_repeat_sweeps_idempotent(
    client: TestClient, db: Session
) -> None:
    """
    Running the sweep twice in a row sends one nudge, not two. The cron may
    retry, a developer may curl it — the cadence is bounded by the cooldown,
    not by how often the trigger fires.
    """
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="60.00"
    )
    _age_expenses(db, group["id"], hours=48)

    nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()
    first = len(_notifications_for(db, member_id))
    assert first >= 1

    second_result = nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()

    assert second_result.suppressed_cooldown == 1
    assert len(_notifications_for(db, member_id)) == first


def test_mute_suppresses_the_relationship(client: TestClient, db: Session) -> None:
    """Muting one relationship silences it without going dark elsewhere."""
    group, owner_headers, member_headers, owner_id, member_id = _two_member_group(
        client, db
    )
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="60.00"
    )
    _age_expenses(db, group["id"], hours=48)

    r = client.put(
        f"{settings.API_V1_STR}/notifications/relationships/{group['id']}/{owner_id}",
        headers=member_headers,
        json={"muted": True},
    )
    assert r.status_code == 200
    assert r.json()["muted"] is True

    result = nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()

    assert result.suppressed_muted == 1
    assert _notifications_for(db, member_id) == []


def test_snooze_defers_then_expires(client: TestClient, db: Session) -> None:
    """Snooze holds the nudge, and the nudge returns when the snooze lapses."""
    group, owner_headers, member_headers, owner_id, member_id = _two_member_group(
        client, db
    )
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="60.00"
    )
    _age_expenses(db, group["id"], hours=48)

    r = client.put(
        f"{settings.API_V1_STR}/notifications/relationships/{group['id']}/{owner_id}",
        headers=member_headers,
        json={"snooze_days": 3},
    )
    assert r.status_code == 200
    assert r.json()["snoozed_until"] is not None

    result = nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()
    assert result.suppressed_snoozed == 1
    assert _notifications_for(db, member_id) == []

    # Let the snooze lapse: the reminder comes back rather than being lost.
    state = db.exec(
        select(NudgeState).where(
            NudgeState.user_id == member_id,
            NudgeState.group_id == uuid.UUID(group["id"]),
        )
    ).one()
    state.snoozed_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.add(state)
    db.commit()

    nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()
    assert len(_notifications_for(db, member_id)) >= 1


def test_quiet_hours_defer_without_consuming_the_nudge(
    client: TestClient, db: Session
) -> None:
    """
    Quiet hours postpone; they do not cancel. The state row must be left
    untouched so the next sweep outside the window still sends — otherwise
    a nightly-scheduled nudge would be silently dropped forever.
    """
    group, owner_headers, member_headers, owner_id, member_id = _two_member_group(
        client, db
    )
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="60.00"
    )
    _age_expenses(db, group["id"], hours=48)

    # Anchored to TODAY, not to a hardcoded date. `_age_expenses` backdates
    # from the real clock, so a fixed `now` silently drifts out from under
    # the aged data: written on 2026-08-25 this read as a 48h-old debt, and
    # by 2026-08-31 the same line described a debt confirmed four days in
    # the injected future, which the sweep skipped as too young — the test
    # went green-to-red on a calendar page, testing nothing in between.
    now = datetime.now(timezone.utc).replace(
        hour=23, minute=30, second=0, microsecond=0
    )  # inside 22→08
    result = nudge_service.run_nudge_sweep(
        db, now=now, group_id=uuid.UUID(group["id"])
    )
    db.commit()

    assert result.suppressed_quiet_hours == 1
    assert _notifications_for(db, member_id) == []

    state = db.exec(
        select(NudgeState).where(
            NudgeState.user_id == member_id,
            NudgeState.group_id == uuid.UUID(group["id"]),
        )
    ).one()
    assert state.last_nudged_at is None

    # Same debt, mid-morning: it goes out.
    later = (now + timedelta(days=1)).replace(hour=10, minute=0)
    nudge_service.run_nudge_sweep(db, now=later, group_id=uuid.UUID(group["id"]))
    db.commit()
    assert len(_notifications_for(db, member_id)) >= 1


def test_global_kill_switch_silences_everything(
    client: TestClient, db: Session
) -> None:
    """`nudges_enabled: false` is the PRD's stop signal — it must be absolute."""
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="60.00"
    )
    _age_expenses(db, group["id"], hours=48)

    r = client.put(
        f"{settings.API_V1_STR}/notifications/preferences",
        headers=member_headers,
        json={"nudges_enabled": False},
    )
    assert r.status_code == 200
    assert r.json()["nudges_enabled"] is False

    result = nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()

    assert result.suppressed_muted == 1
    assert _notifications_for(db, member_id) == []


def test_tiny_debt_is_below_the_notification_floor(
    client: TestClient, db: Session
) -> None:
    """Nobody should get a push notification about 25 cents."""
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="0.50"
    )
    _age_expenses(db, group["id"], hours=48)

    nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()
    assert _notifications_for(db, member_id) == []


# ---------------------------------------------------------------------------
# Quiet-hours arithmetic (the wrapping window is the normal case)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("start", "end", "hour_utc", "tz", "expected"),
    [
        (22, 8, 23, "UTC", True),      # inside, after midnight-wrap start
        (22, 8, 3, "UTC", True),       # inside, past midnight
        (22, 8, 12, "UTC", False),     # outside
        (22, 8, 8, "UTC", False),      # end is exclusive
        (22, 8, 22, "UTC", True),      # start is inclusive
        (9, 17, 12, "UTC", True),      # non-wrapping window, inside
        (9, 17, 20, "UTC", False),     # non-wrapping window, outside
        (None, None, 3, "UTC", False),  # no quiet hours configured
        # 23:00 UTC is 08:00 next day in Tokyo — outside a 22→08 window.
        (22, 8, 23, "Asia/Tokyo", False),
        # A typo'd zone must degrade to UTC, not take the sweep down.
        (22, 8, 23, "Not/AZone", True),
    ],
)
def test_quiet_hours_window(
    db: Session,
    start: int | None,
    end: int | None,
    hour_utc: int,
    tz: str,
    expected: bool,
) -> None:
    _, user_id = _make_authed_user(db)
    prefs = nudge_service.get_or_create_preferences(db, user_id)
    prefs.quiet_hours_start = start
    prefs.quiet_hours_end = end
    prefs.timezone = tz
    db.add(prefs)
    db.commit()

    now = datetime(2026, 8, 25, hour_utc, 0, tzinfo=timezone.utc)
    assert nudge_service.is_within_quiet_hours(prefs, now) is expected


# ---------------------------------------------------------------------------
# Preferences + push subscription API
# ---------------------------------------------------------------------------


def test_preferences_default_on_first_read(client: TestClient, db: Session) -> None:
    headers, _ = _make_authed_user(db)
    r = client.get(
        f"{settings.API_V1_STR}/notifications/preferences", headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["nudges_enabled"] is True
    assert body["push_enabled"] is True
    assert body["email_enabled"] is True
    assert body["quiet_hours_start"] == 22
    assert body["quiet_hours_end"] == 8


def test_preferences_partial_update_leaves_other_fields_alone(
    client: TestClient, db: Session
) -> None:
    headers, _ = _make_authed_user(db)
    r = client.put(
        f"{settings.API_V1_STR}/notifications/preferences",
        headers=headers,
        json={"email_enabled": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["email_enabled"] is False
    assert body["push_enabled"] is True
    assert body["quiet_hours_start"] == 22


def test_clear_quiet_hours_is_explicit(client: TestClient, db: Session) -> None:
    """A null hour means 'unchanged'; clearing needs the explicit flag."""
    headers, _ = _make_authed_user(db)
    r = client.put(
        f"{settings.API_V1_STR}/notifications/preferences",
        headers=headers,
        json={"quiet_hours_start": None, "quiet_hours_end": None},
    )
    assert r.json()["quiet_hours_start"] == 22

    r = client.put(
        f"{settings.API_V1_STR}/notifications/preferences",
        headers=headers,
        json={"clear_quiet_hours": True},
    )
    assert r.json()["quiet_hours_start"] is None
    assert r.json()["quiet_hours_end"] is None


def test_invalid_quiet_hour_is_rejected(client: TestClient, db: Session) -> None:
    headers, _ = _make_authed_user(db)
    r = client.put(
        f"{settings.API_V1_STR}/notifications/preferences",
        headers=headers,
        json={"quiet_hours_start": 25},
    )
    assert r.status_code == 422


def test_preferences_require_auth(client: TestClient) -> None:
    assert (
        client.get(f"{settings.API_V1_STR}/notifications/preferences").status_code
        == 401
    )


def test_vapid_key_is_null_when_push_unconfigured(client: TestClient) -> None:
    """
    The client must be able to learn push is unavailable BEFORE prompting —
    a browser grants the permission prompt once.
    """
    r = client.get(f"{settings.API_V1_STR}/notifications/vapid-public-key")
    assert r.status_code == 200
    assert r.json()["key"] is None


def test_push_subscription_roundtrip(client: TestClient, db: Session) -> None:
    headers, user_id = _make_authed_user(db)
    endpoint = f"https://push.example.com/{uuid.uuid4().hex}"
    payload = {"endpoint": endpoint, "p256dh": "key-material", "auth": "auth-secret"}

    r = client.post(
        f"{settings.API_V1_STR}/notifications/subscriptions",
        headers=headers,
        json=payload,
    )
    assert r.status_code == 201
    assert r.json()["endpoint"] == endpoint

    # Re-registering the same endpoint refreshes rather than 409s — browsers
    # rotate keys and the client re-posts on every load.
    r = client.post(
        f"{settings.API_V1_STR}/notifications/subscriptions",
        headers=headers,
        json={**payload, "p256dh": "rotated-key"},
    )
    assert r.status_code == 201
    db.expire_all()
    subs = db.exec(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    ).all()
    assert len(subs) == 1
    assert subs[0].p256dh == "rotated-key"

    r = client.delete(
        f"{settings.API_V1_STR}/notifications/subscriptions",
        headers=headers,
        params={"endpoint": endpoint},
    )
    assert r.status_code == 204
    db.expire_all()
    assert (
        db.exec(
            select(PushSubscription).where(PushSubscription.user_id == user_id)
        ).all()
        == []
    )


def test_endpoint_moves_to_the_new_owner_on_reregistration(
    client: TestClient, db: Session
) -> None:
    """
    A shared browser signed into a second account must not keep delivering
    the first account's nudges to that device.
    """
    first_headers, first_id = _make_authed_user(db)
    second_headers, second_id = _make_authed_user(db)
    endpoint = f"https://push.example.com/{uuid.uuid4().hex}"
    payload = {"endpoint": endpoint, "p256dh": "k", "auth": "a"}

    client.post(
        f"{settings.API_V1_STR}/notifications/subscriptions",
        headers=first_headers,
        json=payload,
    )
    client.post(
        f"{settings.API_V1_STR}/notifications/subscriptions",
        headers=second_headers,
        json=payload,
    )

    db.expire_all()
    sub = db.exec(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    ).one()
    assert sub.user_id == second_id
    assert (
        db.exec(
            select(PushSubscription).where(PushSubscription.user_id == first_id)
        ).all()
        == []
    )


# ---------------------------------------------------------------------------
# Relationship listing + authorization
# ---------------------------------------------------------------------------


def test_relationships_list_shows_only_the_callers_debts(
    client: TestClient, db: Session
) -> None:
    group, owner_headers, member_headers, owner_id, _ = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="60.00"
    )

    r = client.get(
        f"{settings.API_V1_STR}/notifications/relationships", headers=member_headers
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["counterparty_user_id"] == str(owner_id)
    assert rows[0]["muted"] is False

    # The creditor is owed money, so has no nudgeable relationship.
    r = client.get(
        f"{settings.API_V1_STR}/notifications/relationships", headers=owner_headers
    )
    assert r.json() == []


def test_cannot_mute_a_relationship_in_a_group_you_are_not_in(
    client: TestClient, db: Session
) -> None:
    """
    Without the membership gate this endpoint would let anyone create
    nudge_state rows naming arbitrary users and groups.
    """
    group, owner_headers, member_headers, owner_id, _ = _two_member_group(client, db)
    outsider_headers, _ = _make_authed_user(db)

    r = client.put(
        f"{settings.API_V1_STR}/notifications/relationships/{group['id']}/{owner_id}",
        headers=outsider_headers,
        json={"muted": True},
    )
    assert r.status_code == 403


def test_cannot_mute_against_a_non_member(client: TestClient, db: Session) -> None:
    group, owner_headers, member_headers, _, _ = _two_member_group(client, db)
    _, stranger_id = _make_authed_user(db)

    r = client.put(
        f"{settings.API_V1_STR}/notifications/relationships/{group['id']}/{stranger_id}",
        headers=member_headers,
        json={"muted": True},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# The scheduler entry point
# ---------------------------------------------------------------------------


def test_sweep_endpoint_404s_when_no_secret_is_configured(
    client: TestClient,
) -> None:
    """
    An unconfigured deployment exposes no sweep endpoint at all, rather than
    one guarded by an empty string.
    """
    assert not settings.NUDGE_CRON_SECRET
    r = client.post(f"{settings.API_V1_STR}/notifications/internal/run-sweep")
    assert r.status_code == 404


def test_sweep_endpoint_rejects_a_wrong_secret(client: TestClient) -> None:
    original = settings.NUDGE_CRON_SECRET
    settings.NUDGE_CRON_SECRET = "the-real-secret"
    try:
        r = client.post(
            f"{settings.API_V1_STR}/notifications/internal/run-sweep",
            headers={"X-Nudge-Secret": "not-the-secret"},
        )
        assert r.status_code == 403

        r = client.post(
            f"{settings.API_V1_STR}/notifications/internal/run-sweep"
        )
        assert r.status_code == 403
    finally:
        settings.NUDGE_CRON_SECRET = original


def test_sweep_endpoint_runs_with_the_right_secret(
    client: TestClient, db: Session
) -> None:
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="75.00"
    )
    _age_expenses(db, group["id"], hours=48)

    original = settings.NUDGE_CRON_SECRET
    settings.NUDGE_CRON_SECRET = "the-real-secret"
    try:
        r = client.post(
            f"{settings.API_V1_STR}/notifications/internal/run-sweep",
            headers={"X-Nudge-Secret": "the-real-secret"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["relationships_examined"] >= 1
    finally:
        settings.NUDGE_CRON_SECRET = original

    assert len(_notifications_for(db, member_id)) >= 1


def test_dry_run_changes_nothing(client: TestClient, db: Session) -> None:
    """`dry_run` must be safe to point at production to see what would go out."""
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="75.00"
    )
    _age_expenses(db, group["id"], hours=48)

    result = nudge_service.run_nudge_sweep(
        db, group_id=uuid.UUID(group["id"]), dry_run=True
    )
    db.commit()

    assert result.nudges_sent == 1
    assert _notifications_for(db, member_id) == []
    state = db.exec(
        select(NudgeState).where(NudgeState.user_id == member_id)
    ).first()
    assert state is None or state.last_nudged_at is None


# ---------------------------------------------------------------------------
# Delivery bookkeeping
# ---------------------------------------------------------------------------


def test_undeliverable_nudge_is_recorded_not_dropped(
    client: TestClient, db: Session
) -> None:
    """
    With no VAPID keypair and no push subscription, the nudge still leaves a
    record saying WHY it didn't land — "why didn't I get it?" must be
    answerable without reading server logs.
    """
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="90.00"
    )
    _age_expenses(db, group["id"], hours=48)

    nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()

    notifications = _notifications_for(db, member_id)
    push = [n for n in notifications if n.channel == NotificationChannel.PUSH]
    assert len(push) == 1
    assert push[0].status == NotificationStatus.SKIPPED
    assert push[0].detail is not None
    # The rendered copy is stored, not re-derived later.
    assert push[0].title.startswith("You owe ")
    assert group["name"] in push[0].body


def test_push_disabled_in_preferences_falls_through_to_email(
    client: TestClient, db: Session
) -> None:
    group, owner_headers, member_headers, _, member_id = _two_member_group(client, db)
    _confirmed_expense(
        client, owner_headers, [owner_headers, member_headers], group["id"], amount="90.00"
    )
    _age_expenses(db, group["id"], hours=48)

    client.put(
        f"{settings.API_V1_STR}/notifications/preferences",
        headers=member_headers,
        json={"push_enabled": False},
    )

    nudge_service.run_nudge_sweep(db, group_id=uuid.UUID(group["id"]))
    db.commit()

    channels = {n.channel for n in _notifications_for(db, member_id)}
    assert NotificationChannel.PUSH in channels
    assert NotificationChannel.EMAIL in channels


# ---------------------------------------------------------------------------
# VAPID key handling
# ---------------------------------------------------------------------------


def test_vapid_private_key_accepts_pem_and_base64url() -> None:
    """
    Regression: pywebpush's `from_string` base64url-DECODES whatever it is
    given, so a PEM private key fails with an opaque "ASN.1 parsing error"
    and push dies silently in production. Found by running the real push
    path, not by reading the docs — so both forms are normalized, and both
    are pinned here.
    """
    import base64

    from cryptography.hazmat.primitives import serialization
    from py_vapid import Vapid01

    from app.features.notifications.delivery import _vapid_private_key

    vapid = Vapid01()
    vapid.generate_keys()
    pem = vapid.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    der_b64 = (
        base64.urlsafe_b64encode(
            vapid.private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        .decode()
        .rstrip("=")
    )

    original = settings.VAPID_PRIVATE_KEY
    try:
        # A pasted PEM is converted to the form pywebpush can load…
        settings.VAPID_PRIVATE_KEY = pem
        normalized = _vapid_private_key()
        assert "-----BEGIN" not in normalized
        assert Vapid01.from_string(normalized) is not None

        # …and an already-encoded key is passed through untouched.
        settings.VAPID_PRIVATE_KEY = der_b64
        assert _vapid_private_key() == der_b64
        assert Vapid01.from_string(der_b64) is not None
    finally:
        settings.VAPID_PRIVATE_KEY = original


def test_push_is_skipped_not_failed_when_unconfigured() -> None:
    """
    No VAPID keypair is a configuration state, not an error. It must record
    SKIPPED so an operator can tell "push isn't set up" apart from "push is
    broken".
    """
    from app.features.notifications.delivery import push_available

    assert push_available() is False
