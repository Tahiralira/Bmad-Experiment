"""WS13 — Nudge Engine: Level 2 escalation and the ladder's end.

Three things are worth stating about what these tests guard.

**The ladder is a conversation, not a calendar.** Level 2 requires a Level 1
to have actually been sent. A five-day-old debt the engine has never spoken
about still opens gently — `test_old_debt_still_opens_at_level_1` is the
difference between an agent with manners and one that shouts at strangers.

**The ladder ends.** Level 3 is cut from the product, so Level 2 is the top
rung, and `test_ladder_goes_quiet_after_the_cap` asserts the engine stops of
its own accord rather than repeating its firmest message forever.

**Cut means the copy too.** `test_level_2_never_mentions_anyone_else` guards
the line between the rungs, which is the subject of the sentence: Level 2
talks about the person you owe; Level 3 would talk about your standing among
your friends. That is how a cut level grows back by accident.

Time is INJECTED throughout rather than slept or configured away: every
sweep is handed an explicit `now`, so cooldowns are exercised at their real
production durations.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.features.notifications import service as nudge_service
from app.features.notifications.models import (
    EVENT_NUDGE_LEVEL_1,
    EVENT_NUDGE_LEVEL_2,
    NudgeState,
)

# Reuse WS12's fixtures wholesale — the engine under test is the same one,
# and a second copy of these helpers would be a second thing to keep true.
from tests.api.routes.test_nudges import (
    _age_expenses,
    _confirmed_expense,
    _notifications_for,
    _two_member_group,
)

LEVEL_1_AGE = settings.NUDGE_LEVEL_1_AFTER_HOURS
LEVEL_2_AGE = settings.NUDGE_LEVEL_2_AFTER_HOURS
LEVEL_2_COOLDOWN = settings.NUDGE_LEVEL_2_COOLDOWN_HOURS
MAX_LEVEL_2 = settings.NUDGE_LEVEL_2_MAX_REMINDERS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sweep(db: Session, group_id: str, *, now: datetime | None = None):
    result = nudge_service.run_nudge_sweep(db, now=now, group_id=uuid.UUID(group_id))
    db.commit()
    return result


def _state(db: Session, group_id: str, debtor_id: uuid.UUID) -> NudgeState:
    db.expire_all()
    return db.exec(
        select(NudgeState).where(
            NudgeState.user_id == debtor_id,
            NudgeState.group_id == uuid.UUID(group_id),
        )
    ).one()


def _levels_sent(db: Session, user_id: uuid.UUID) -> list[int]:
    """
    The level of each REMINDER a user received, oldest first.

    Deduplicated by send instant, because one reminder writes one
    `notification` row PER CHANNEL — a push attempt and an email attempt,
    both recorded even when they skip. Counting rows would count channels
    and report every nudge twice.
    """
    reminders = sorted(
        (
            n
            for n in _notifications_for(db, user_id)
            if n.event_type in (EVENT_NUDGE_LEVEL_1, EVENT_NUDGE_LEVEL_2)
        ),
        key=lambda n: n.sent_at,
    )
    levels: list[int] = []
    seen: set[datetime] = set()
    for note in reminders:
        if note.sent_at in seen:
            continue
        seen.add(note.sent_at)
        levels.append(note.level)
    return levels


def _noon_today() -> datetime:
    """
    A start time that keeps a multi-day walk clear of the 22->08 quiet
    window at every step, and that moves with the calendar instead of
    rotting into a hardcoded date the way WS12's did.
    """
    return datetime.now(timezone.utc).replace(
        hour=12, minute=0, second=0, microsecond=0
    )


def _climb_to_level_2(client: TestClient, db: Session, amount: str = "80.00"):
    """
    Walk one relationship from a fresh debt up to a delivered Level 2.

    Returns (group, owner_headers, member_headers, owner_id, member_id, now)
    where `now` is the instant the Level 2 went out.
    """
    group, owner_h, member_h, owner_id, member_id = _two_member_group(client, db)
    _confirmed_expense(client, owner_h, [owner_h, member_h], group["id"], amount=amount)
    _age_expenses(db, group["id"], hours=LEVEL_1_AGE + 1)

    t0 = _noon_today()
    first = _sweep(db, group["id"], now=t0)
    assert first.nudges_by_level == {"level_1": 1}

    # Past both the Level 1 cooldown and the Level 2 age threshold.
    t1 = t0 + timedelta(hours=settings.NUDGE_COOLDOWN_HOURS + 1)
    second = _sweep(db, group["id"], now=t1)
    assert second.nudges_by_level == {"level_2": 1}

    return group, owner_h, member_h, owner_id, member_id, t1


def _burn_remaining_level_2s(db: Session, group_id: str, start: datetime) -> datetime:
    """Spend every Level 2 the cap allows after the first. Returns the clock."""
    now = start
    for _ in range(MAX_LEVEL_2 - 1):
        now = now + timedelta(hours=LEVEL_2_COOLDOWN + 1)
        assert _sweep(db, group_id, now=now).nudges_by_level == {"level_2": 1}
    return now


# ---------------------------------------------------------------------------
# The ladder
# ---------------------------------------------------------------------------


def test_level_1_escalates_to_level_2(client: TestClient, db: Session) -> None:
    """The whole point of WS13: the second reminder is a DIFFERENT reminder."""
    _, _, _, _, member_id, _ = _climb_to_level_2(client, db)

    assert _levels_sent(db, member_id) == [1, 2]

    level_2 = [n for n in _notifications_for(db, member_id) if n.level == 2]
    assert level_2, "expected a Level 2 notification"
    assert all(n.event_type == EVENT_NUDGE_LEVEL_2 for n in level_2)

    # Tone progression, not just a counter: Level 2 is written from the
    # creditor's side, which is what makes it contextual rather than louder.
    body = level_2[0].body.lower()
    assert "out of pocket" in body
    assert "covered this" in body


def test_level_2_never_mentions_anyone_else(client: TestClient, db: Session) -> None:
    """
    Level 3 is cut, and cut means the copy too.

    Comparative language is how the cut level grows back in by accident, one
    well-meaning copy edit at a time. This test is deliberately about words
    rather than behaviour, because the words ARE the feature here.
    """
    _, _, _, _, member_id, _ = _climb_to_level_2(client, db)
    level_2 = [n for n in _notifications_for(db, member_id) if n.level == 2][0]
    text = f"{level_2.title} {level_2.body}".lower()

    for social in (
        "everyone else",
        "the others",
        "rest of the group",
        "have already",
        "only one",
        "last person",
    ):
        assert social not in text, f"Level 2 copy drifted into social pressure: {social!r}"


def test_old_debt_still_opens_at_level_1(client: TestClient, db: Session) -> None:
    """
    A debt ALREADY past the Level 2 age gets Level 1 first.

    Escalation is a property of the conversation, not the calendar. Without
    this, the engine's opening line to anyone whose debt predates their
    first sweep — engine off, snooze lapsed, mute lifted — would be its
    firmest one.
    """
    group, owner_h, member_h, _, member_id = _two_member_group(client, db)
    _confirmed_expense(client, owner_h, [owner_h, member_h], group["id"])
    _age_expenses(db, group["id"], hours=LEVEL_2_AGE * 3)

    result = _sweep(db, group["id"], now=_noon_today())

    assert result.nudges_by_level == {"level_1": 1}
    assert _levels_sent(db, member_id) == [1]
    assert _state(db, group["id"], member_id).last_level == 1


def test_level_2_has_a_shorter_cooldown(client: TestClient, db: Session) -> None:
    """
    Frequency progression: at Level 2 the gap narrows.

    Asserted behaviourally rather than by reading the settings back — the
    sweep that sends here happens at an interval that would still have been
    suppressed while the relationship sat at Level 1.
    """
    assert LEVEL_2_COOLDOWN < settings.NUDGE_COOLDOWN_HOURS

    group, _, _, _, member_id, t1 = _climb_to_level_2(client, db)
    gid = group["id"]

    too_soon = t1 + timedelta(hours=LEVEL_2_COOLDOWN - 1)
    assert _sweep(db, gid, now=too_soon).suppressed_cooldown == 1
    assert _levels_sent(db, member_id) == [1, 2]

    ready = t1 + timedelta(hours=LEVEL_2_COOLDOWN + 1)
    assert _sweep(db, gid, now=ready).nudges_by_level == {"level_2": 1}
    assert _levels_sent(db, member_id) == [1, 2, 2]


def test_ladder_goes_quiet_after_the_cap(client: TestClient, db: Session) -> None:
    """
    With Level 3 cut, SILENCE is the last rung.

    An engine that repeats its firmest message forever is the nagging the
    product exists to remove, so the cap is a product guarantee rather than
    a tuning detail. The debt stays visible in the app; the agent simply
    stops bringing it up.
    """
    group, _, _, _, member_id, t1 = _climb_to_level_2(client, db)
    gid = group["id"]

    now = _burn_remaining_level_2s(db, gid, t1)
    at_cap = _levels_sent(db, member_id)
    assert at_cap.count(2) == MAX_LEVEL_2

    # From here the engine says nothing — however long it waits.
    for extra_days in (1, 30, 365):
        result = _sweep(db, gid, now=now + timedelta(days=extra_days))
        assert result.suppressed_exhausted == 1
        assert result.nudges_sent == 0
    assert _levels_sent(db, member_id) == at_cap


def test_exhaustion_is_reported_not_merely_silent(
    client: TestClient, db: Session
) -> None:
    """
    An operator must be able to tell "stopped on purpose" from "broken".

    A sweep that has gone quiet and a sweep that is failing look identical
    from outside — both send nothing — so exhaustion is a counted outcome,
    and the settings screen says so to the person being nudged.
    """
    group, _, member_h, _, member_id, t1 = _climb_to_level_2(client, db)
    _burn_remaining_level_2s(db, group["id"], t1)

    r = client.get(
        f"{settings.API_V1_STR}/notifications/relationships", headers=member_h
    )
    assert r.status_code == 200
    row = next(x for x in r.json() if x["group_id"] == group["id"])
    assert row["last_level"] == 2
    assert row["reminders_exhausted"] is True
