"""WS13 — "Cleared without asking" + the kill-switch metrics.

The cleared notification is the brand promise compressed into one sentence:
*you got your money back, and you never had to be the one who brings it up*
(02 §7, wow moment #2). Most of this file exists to make sure that sentence
is only ever said where it is TRUE — which means refusing to send it more
often than sending it:

- nobody was nudged        → the creditor may well have asked in person
- the debt is partly paid  → nothing has been cleared yet
- it already went out      → saying it twice makes it a receipt

The metrics half covers the other WS13 promise: the PRD's stop signal has to
be observable. `mute_rate` over an empty denominator is null, never 0.0 —
"nobody minds" and "nobody has been asked yet" are different findings, and
only one of them should keep a product shipping.
"""

import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.features.notifications import service as nudge_service
from app.features.notifications.models import (
    EVENT_NUDGE_CLEARED,
    Notification,
    NotificationStatus,
    NudgeState,
)
from tests.api.routes.test_nudge_level_2 import (
    _climb_to_level_2,
    _noon_today,
    _sweep,
)
from tests.api.routes.test_nudges import (
    _age_expenses,
    _confirmed_expense,
    _notifications_for,
    _two_member_group,
)

API = settings.API_V1_STR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settle_up(
    client: TestClient,
    headers: dict[str, str],
    group_id: str,
    counterparty_user_id: uuid.UUID,
):
    return client.post(
        f"{API}/expenses/settlement-claims/aggregate",
        headers=headers,
        json={
            "group_id": group_id,
            "counterparty_user_id": str(counterparty_user_id),
        },
    )


def _settle_and_confirm(
    client: TestClient,
    db: Session,
    group_id: str,
    debtor_headers: dict[str, str],
    creditor_headers: dict[str, str],
    creditor_id: uuid.UUID,
) -> dict:
    """The debtor claims they paid; the creditor confirms. The full loop."""
    r = _settle_up(client, debtor_headers, group_id, creditor_id)
    assert r.status_code == 201, r.text
    claim = r.json()

    r = client.post(
        f"{API}/expenses/settlement-claims/{claim['id']}/confirm",
        headers=creditor_headers,
    )
    assert r.status_code == 200, r.text
    db.expire_all()
    return claim


def _cleared_for(db: Session, user_id: uuid.UUID) -> list[Notification]:
    return [
        n
        for n in _notifications_for(db, user_id)
        if n.event_type == EVENT_NUDGE_CLEARED
    ]


def _state_for(db: Session, group_id: str, debtor_id: uuid.UUID) -> NudgeState:
    db.expire_all()
    return db.exec(
        select(NudgeState).where(
            NudgeState.user_id == debtor_id,
            NudgeState.group_id == uuid.UUID(group_id),
        )
    ).one()


# ---------------------------------------------------------------------------
# "Cleared without asking"
# ---------------------------------------------------------------------------


def test_cleared_notification_goes_to_the_creditor(
    client: TestClient, db: Session
) -> None:
    """
    The wow moment: the person who was OWED money hears that it arrived.

    Addressed to the creditor, not the debtor — the debtor already knows
    they paid, and telling them would be a receipt. The whole sentence is
    for the person who spent days not asking.
    """
    group, owner_h, member_h, owner_id, member_id, _ = _climb_to_level_2(client, db)

    _settle_and_confirm(client, db, group["id"], member_h, owner_h, owner_id)

    cleared = _cleared_for(db, owner_id)
    assert cleared, "creditor should have been told their dues cleared"
    assert not _cleared_for(db, member_id), "the payer does not need a receipt"

    assert "never had to ask" in cleared[0].body.lower()
    # The amount is the debt that cleared, not zero.
    assert cleared[0].amount > 0
    # Level 0: this is not a rung on the urgency ladder. Filing it as Level
    # 1 would quietly inflate Escalation Efficacy with a message that never
    # nudged anybody.
    assert cleared[0].level == 0


def test_no_cleared_notification_when_nobody_was_nudged(
    client: TestClient, db: Session
) -> None:
    """
    "You never had to ask" is a claim about the agent's work.

    If the engine never nudged, the creditor may well have asked in person —
    over dinner, in the group chat — and the app has no way to know it
    didn't. Silence is the only honest option, so the notification is
    refused rather than guessed at.
    """
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    _confirmed_expense(client, owner_h, [owner_h, member_h], group["id"])

    _settle_and_confirm(client, db, group["id"], member_h, owner_h, owner_id)

    assert _cleared_for(db, owner_id) == []
    # No nudge ever happened, so there is no ladder row to reset either.
    assert (
        db.exec(
            select(NudgeState).where(
                NudgeState.user_id == member_id,
                NudgeState.group_id == uuid.UUID(group["id"]),
            )
        ).first()
        is None
    )


def test_partial_payment_is_not_a_clearing(client: TestClient, db: Session) -> None:
    """
    A per-expense settlement that leaves a balance clears nothing.

    The check recomputes the netted balance rather than trusting the claim
    amount: a claim says what someone paid, not whether anything is left.
    """
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    first = _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="100.00"
    )
    _confirmed_expense(
        client, owner_h, [owner_h, member_h], group["id"], amount="60.00"
    )
    _age_expenses(db, group["id"], hours=settings.NUDGE_LEVEL_1_AFTER_HOURS + 1)
    _sweep(db, group["id"], now=_noon_today())

    # Settle only the first expense — the second one's half is still owed.
    splits = client.get(
        f"{API}/expenses/{first['id']}/splits", headers=member_h
    ).json()
    mine = next(s for s in splits["data"] if s["user_id"] == str(member_id))
    r = client.post(
        f"{API}/expenses/{first['id']}/settle",
        headers=member_h,
        json={"expense_split_id": mine["id"]},
    )
    assert r.status_code == 201, r.text
    claim = r.json()
    r = client.post(
        f"{API}/expenses/settlement-claims/{claim['id']}/confirm", headers=owner_h
    )
    assert r.status_code == 200, r.text

    assert _cleared_for(db, owner_id) == [], "a partial payment cleared nothing"
    # The ladder is still running, because the debt still exists.
    assert _state_for(db, group["id"], member_id).last_level == 1


def test_cleared_notification_is_sent_once(client: TestClient, db: Session) -> None:
    """
    Clearing `last_level` both ends the ladder and closes this door.

    Re-running the announcement against an already-cleared relationship must
    say nothing: told twice, the wow moment becomes a duplicate receipt.
    """
    group, owner_h, member_h, owner_id, member_id, _ = _climb_to_level_2(client, db)
    _settle_and_confirm(client, db, group["id"], member_h, owner_h, owner_id)
    assert len(_cleared_for(db, owner_id)) >= 1
    before = len(_cleared_for(db, owner_id))

    sent_again = nudge_service.notify_debt_cleared(
        db,
        group_id=uuid.UUID(group["id"]),
        debtor_id=member_id,
        creditor_id=owner_id,
        amount=nudge_service.Decimal("40.00"),
        currency="USD",
    )
    db.commit()

    assert sent_again is False
    assert len(_cleared_for(db, owner_id)) == before


def test_clearing_resets_the_ladder_but_keeps_the_cooldown(
    client: TestClient, db: Session
) -> None:
    """
    A settled debt starts the next conversation from the beginning — but not
    the next reminder from zero seconds.

    `last_level` resets so a new debt between the same pair opens gently at
    Level 1 rather than resuming mid-escalation. `last_nudged_at` is
    deliberately KEPT: WS12's cooldown has to survive a debt going to zero
    and coming back, or the next expense between these two would be nudged
    the moment it lands.
    """
    group, owner_h, member_h, owner_id, member_id, _ = _climb_to_level_2(client, db)
    before = _state_for(db, group["id"], member_id)
    assert before.last_level == 2
    assert before.level_2_count == 1
    nudged_at = before.last_nudged_at

    _settle_and_confirm(client, db, group["id"], member_h, owner_h, owner_id)

    after = _state_for(db, group["id"], member_id)
    assert after.last_level is None, "the ladder should start over"
    assert after.level_2_count == 0
    assert after.last_nudged_at == nudged_at, "the cooldown must survive settlement"


def test_cleared_notification_respects_the_kill_switch(
    client: TestClient, db: Session
) -> None:
    """
    Someone who switched reminders off stays switched off.

    Good news is still news, and the kill switch is the PRD's stop signal —
    honouring it only for messages the user dislikes would make it a
    preference rather than a promise.
    """
    group, owner_h, member_h, owner_id, member_id, _ = _climb_to_level_2(client, db)

    r = client.put(
        f"{API}/notifications/preferences",
        headers=owner_h,
        json={"nudges_enabled": False},
    )
    assert r.status_code == 200

    _settle_and_confirm(client, db, group["id"], member_h, owner_h, owner_id)

    assert _cleared_for(db, owner_id) == []
    # The ladder still resets — the debt really is gone, whatever the
    # creditor chose to hear about it.
    assert _state_for(db, group["id"], member_id).last_level is None


def test_quiet_hours_move_the_good_news_to_email(
    client: TestClient, db: Session
) -> None:
    """
    Quiet hours can't DEFER here — there is no later pass to pick this up —
    so instead of dropping the message or buzzing someone at 3am, it changes
    channel. Email is waiting in the morning.
    """
    group, owner_h, member_h, owner_id, member_id, _ = _climb_to_level_2(client, db)

    # Put the creditor's quiet hours around the CURRENT hour, through the
    # real preferences API, so the settlement below travels the production
    # path at a moment that genuinely falls inside the window. Faking the
    # clock or stubbing the quiet-hours check would test the mock instead.
    hour = datetime.now(timezone.utc).hour
    r = client.put(
        f"{API}/notifications/preferences",
        headers=owner_h,
        json={"quiet_hours_start": hour, "quiet_hours_end": (hour + 1) % 24},
    )
    assert r.status_code == 200, r.text

    _settle_and_confirm(client, db, group["id"], member_h, owner_h, owner_id)

    cleared = _cleared_for(db, owner_id)
    assert cleared, "the message should be routed, not dropped"
    push_rows = [n for n in cleared if n.channel.value == "push"]
    assert push_rows, "the skipped push attempt should still be recorded"
    assert push_rows[0].status == NotificationStatus.SKIPPED
    assert "quiet hours" in (push_rows[0].detail or "")
    # Email was still attempted rather than the message being dropped.
    assert [n for n in cleared if n.channel.value == "email"]


def test_a_broken_notification_cannot_break_a_settlement(
    client: TestClient, db: Session, monkeypatch
) -> None:
    """
    The load-bearing safety property of putting delivery on a request path.

    Someone settling a debt must not have their settlement fail because a
    push service misbehaved. `notify_debt_cleared` runs inside a SAVEPOINT
    and swallows everything — here the delivery layer is made to explode
    outright, and the settlement still lands.
    """
    group, owner_h, member_h, owner_id, member_id, _ = _climb_to_level_2(client, db)

    def _explode(*args, **kwargs):
        raise RuntimeError("push service on fire")

    monkeypatch.setattr(
        "app.features.notifications.delivery.deliver", _explode, raising=True
    )

    _settle_and_confirm(client, db, group["id"], member_h, owner_h, owner_id)

    # The settlement is real: the balance is gone.
    assert (
        nudge_service.find_debt_relationships(db, group_id=uuid.UUID(group["id"]))
        == []
    )
    # And no half-written notification survived the rollback.
    assert _cleared_for(db, owner_id) == []


# ---------------------------------------------------------------------------
# Kill-switch metrics (analytics-spec §4 "Mute rate")
# ---------------------------------------------------------------------------


def _metrics(client: TestClient, secret: str = "test-cron-secret", **params):
    return client.get(
        f"{API}/notifications/internal/nudge-metrics",
        headers={"X-Nudge-Secret": secret},
        params=params,
    )


def test_metrics_endpoint_is_secret_guarded(
    client: TestClient, monkeypatch
) -> None:
    """
    It reports on people who are not the caller, so it belongs to the
    operator running the cron rather than to any logged-in user. Unset
    secret 404s: an unconfigured deployment exposes no internal surface at
    all, rather than one guarded by an empty string.
    """
    monkeypatch.setattr(settings, "NUDGE_CRON_SECRET", "", raising=False)
    assert _metrics(client).status_code == 404

    monkeypatch.setattr(settings, "NUDGE_CRON_SECRET", "right", raising=False)
    assert _metrics(client, secret="wrong").status_code == 403
    assert _metrics(client, secret="right").status_code == 200


def test_mute_rate_is_null_not_zero_before_anyone_is_nudged(
    client: TestClient, monkeypatch
) -> None:
    """
    An unknown rate is not a zero rate.

    Over an empty denominator "0%" reads as "nobody minds", when it means
    "nobody has been asked yet" — and this is the number the PRD would halt
    the product on. Reported as null so the difference survives the trip to
    a dashboard.
    """
    monkeypatch.setattr(settings, "NUDGE_CRON_SECRET", "right", raising=False)
    # A one-day window that predates any nudge this suite has sent.
    body = _metrics(client, secret="right", window_days=1).json()

    if body["users_nudged"] == 0:
        assert body["mute_rate"] is None
    else:  # pragma: no cover - depends on suite ordering
        assert isinstance(body["mute_rate"], float)


def test_metrics_count_sends_by_level_and_mutes_by_person(
    client: TestClient, db: Session, monkeypatch
) -> None:
    """
    The two halves of the kill-switch metric, from the database.

    PostHog holds the numerator (the browser fires `nudge.notification.
    muted`) but structurally cannot hold the denominator: sends happen
    server-side in the sweep, so no browser ever witnesses one.
    """
    monkeypatch.setattr(settings, "NUDGE_CRON_SECRET", "right", raising=False)

    group, _, member_h, _, member_id, t1 = _climb_to_level_2(client, db)

    # Force the delivery record to SENT. Nothing is deliverable in tests —
    # no VAPID keypair, no SMTP — and the metric deliberately counts people
    # who were REACHED, so a suite where every attempt SKIPs would measure
    # an empty set and assert nothing.
    for note in _notifications_for(db, member_id):
        note.status = NotificationStatus.SENT
        db.add(note)
    db.commit()

    before = _metrics(client, secret="right").json()
    assert before["users_nudged"] >= 1
    assert before["sends_by_level"].get("level_1", 0) >= 1
    assert before["sends_by_level"].get("level_2", 0) >= 1

    # Now this person mutes the relationship — the stop signal firing.
    r = client.put(
        f"{API}/notifications/relationships/{group['id']}/{_creditor_of(db, member_id)}",
        headers=member_h,
        json={"muted": True},
    )
    assert r.status_code == 200, r.text

    after = _metrics(client, secret="right").json()
    assert after["users_muted_relationship"] > before["users_muted_relationship"]
    assert after["users_muted_any"] > before["users_muted_any"]
    assert after["mute_rate"] is not None and after["mute_rate"] > 0


def _creditor_of(db: Session, debtor_id: uuid.UUID) -> uuid.UUID:
    db.expire_all()
    return db.exec(
        select(NudgeState.counterparty_user_id).where(
            NudgeState.user_id == debtor_id
        )
    ).first()


def test_metrics_reject_a_silly_window(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "NUDGE_CRON_SECRET", "right", raising=False)
    assert _metrics(client, secret="right", window_days=0).status_code == 422
    assert _metrics(client, secret="right", window_days=9999).status_code == 422
