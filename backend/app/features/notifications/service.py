# Notifications service (WS12 — Nudge Engine: Infra + Level 1).
#
# The sweep is a plain, idempotent function. It is deliberately NOT a Celery
# task: Render's free tier has no background worker and no cron job, so a
# broker plus two extra processes would buy a scheduler that production
# cannot run. Instead the same function is driven by whatever can wake up —
# a GitHub Actions cron in staging/production, a test calling it directly,
# a developer curling it locally. Introducing Celery later means changing
# the trigger, not the engine. (Decision: WS12, amends 10-execution-plan.md;
# architecture.md §real-time updated to match.)
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import sqlalchemy as sa
from sqlmodel import Session, select

from app.core.config import settings
from app.core.currency import DEFAULT_CURRENCY
from app.features.auth.models import User
from app.features.expenses.models import (
    Expense,
    ExpenseSplit,
    ExpenseStatus,
    SplitStatus,
)
from app.features.groups.models import ExpenseGroup, GroupSettings
from app.features.notifications.models import (
    EVENT_NUDGE_LEVEL_1,
    Notification,
    NotificationPreference,
    NotificationStatus,
    NudgeLevel,
    NudgeState,
    NudgeSweepResult,
)

logger = logging.getLogger(__name__)


# === Preferences ===


def get_or_create_preferences(
    session: Session, user_id: uuid.UUID
) -> NotificationPreference:
    """
    A user's preferences, created with defaults on first access. Absence of
    a row means "never touched the settings", not "opted out" — so the row
    is materialised rather than treated as a silent opt-out.
    """
    prefs = session.exec(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
    ).first()
    if prefs is None:
        prefs = NotificationPreference(user_id=user_id)
        session.add(prefs)
        session.flush()
        session.refresh(prefs)
    return prefs


def is_within_quiet_hours(prefs: NotificationPreference, now: datetime) -> bool:
    """
    Whether `now` (an aware UTC instant) falls inside the user's local quiet
    hours. A window whose start is after its end wraps midnight — 22 → 8 is
    the common case, so wrapping is the norm rather than an edge case.

    An unknown timezone string degrades to UTC rather than raising: a typo
    in a preference must not take the whole sweep down.
    """
    start, end = prefs.quiet_hours_start, prefs.quiet_hours_end
    if start is None or end is None or start == end:
        return False

    try:
        local = now.astimezone(ZoneInfo(prefs.timezone))
    except (ZoneInfoNotFoundError, ValueError):
        logger.warning(
            "Unknown timezone %r on preferences %s; treating as UTC",
            prefs.timezone,
            prefs.id,
        )
        local = now.astimezone(timezone.utc)

    hour = local.hour
    if start < end:
        return start <= hour < end
    # Wrapping window: inside if we're at/after the start OR before the end.
    return hour >= start or hour < end


# === Debt discovery ===


@dataclass(frozen=True)
class DebtRelationship:
    """
    One person owing another inside one group — the ONLY unit the nudge
    engine addresses. `amount` is already netted across both directions and
    across every expense between the pair; `oldest_confirmed_at` is when the
    earliest still-unsettled split in that relationship was confirmed, which
    is what "debt age" means here.
    """

    group_id: uuid.UUID
    group_name: str
    currency: str
    debtor_id: uuid.UUID
    creditor_id: uuid.UUID
    creditor_name: str | None
    amount: Decimal
    oldest_confirmed_at: datetime


def find_debt_relationships(
    session: Session, *, group_id: uuid.UUID | None = None
) -> list[DebtRelationship]:
    """
    Every outstanding debt relationship, netted per (group, debtor,
    creditor), across confirmed splits on confirmed expenses.

    Same balance semantics as the dashboard and pairwise-balances (WS5/WS6):
    settled splits drop out; splits with an in-flight settlement claim still
    count until that claim is confirmed — a claim is a promise, not a
    payment, and nudging on a promise is exactly the product's job.

    One query for all groups, not a loop over members: the sweep runs over
    the whole system, so an N+1 across every group would be the engine's
    performance ceiling.
    """
    rows = session.exec(
        select(
            Expense.group_id.label("group_id"),
            ExpenseSplit.user_id.label("debtor_id"),
            Expense.payer_id.label("creditor_id"),
            sa.func.sum(ExpenseSplit.amount_owed).label("total"),
            sa.func.min(Expense.confirmed_at).label("oldest"),
        )
        .select_from(Expense)
        .join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)
        .where(
            Expense.status == ExpenseStatus.CONFIRMED,
            ExpenseSplit.status == SplitStatus.CONFIRMED,
            ExpenseSplit.user_id != Expense.payer_id,
            *([Expense.group_id == group_id] if group_id else []),
        )
        .group_by(Expense.group_id, ExpenseSplit.user_id, Expense.payer_id)
    ).all()

    # Net the two directions against each other. A owing B 50 while B owes A
    # 30 is one debt of 20, and only A gets nudged — nudging both sides of a
    # mutual balance is how an app becomes noise.
    gross: dict[tuple[uuid.UUID, uuid.UUID, uuid.UUID], tuple[Decimal, datetime]] = {}
    for row in rows:
        gross[(row.group_id, row.debtor_id, row.creditor_id)] = (
            Decimal(row.total or 0),
            row.oldest,
        )

    netted: list[tuple[uuid.UUID, uuid.UUID, uuid.UUID, Decimal, datetime]] = []
    seen: set[tuple[uuid.UUID, frozenset[uuid.UUID]]] = set()
    for (gid, debtor, creditor), (amount, oldest) in gross.items():
        pair_key = (gid, frozenset({debtor, creditor}))
        if pair_key in seen:
            continue
        seen.add(pair_key)

        reverse_amount, reverse_oldest = gross.get((gid, creditor, debtor), (Decimal(0), None))
        net = amount - reverse_amount
        if net > 0:
            owed_by, owed_to = debtor, creditor
        elif net < 0:
            owed_by, owed_to, net = creditor, debtor, -net
        else:
            # Mutually cancelled — nothing to nudge about.
            continue

        # Age from the earliest unsettled split on either side: the debt has
        # existed since the first expense that created it.
        candidates = [d for d in (oldest, reverse_oldest) if d is not None]
        if not candidates:
            continue
        netted.append((gid, owed_by, owed_to, net, min(candidates)))

    if not netted:
        return []

    group_ids = {n[0] for n in netted}
    user_ids = {n[2] for n in netted}

    groups = {
        g.id: g
        for g in session.exec(
            select(ExpenseGroup).where(ExpenseGroup.id.in_(group_ids))
        ).all()
    }
    group_currency = {
        s.group_id: s.currency
        for s in session.exec(
            select(GroupSettings).where(GroupSettings.group_id.in_(group_ids))
        ).all()
    }
    users = {
        u.id: u
        for u in session.exec(select(User).where(User.id.in_(user_ids))).all()
    }

    relationships: list[DebtRelationship] = []
    for gid, debtor_id, creditor_id, amount, oldest in netted:
        group = groups.get(gid)
        if group is None:
            continue
        creditor = users.get(creditor_id)
        relationships.append(
            DebtRelationship(
                group_id=gid,
                group_name=group.name,
                currency=group_currency.get(gid) or DEFAULT_CURRENCY,
                debtor_id=debtor_id,
                creditor_id=creditor_id,
                creditor_name=_display_name(creditor),
                amount=amount.quantize(Decimal("0.01")),
                oldest_confirmed_at=_as_aware(oldest),
            )
        )
    return relationships


def _display_name(user: User | None) -> str | None:
    """
    How a counterparty is named in a notification.

    Deliberately NOT `full_name or email` (the in-app pattern): a nudge
    renders on a lock screen, where a full email address is both ugly and
    more exposure than the moment needs. Falls back to the address's local
    part, which identifies the person to someone who already knows them
    without publishing the whole address.
    """
    if user is None:
        return None
    if user.full_name:
        return user.full_name
    return user.email.split("@")[0] if user.email else None


def _as_aware(value: datetime) -> datetime:
    """
    Postgres hands back aware datetimes; SQLite (and some drivers) do not.
    Naive values are UTC by construction here — every timestamp column in
    this schema is timezone-aware (WS5/B-H9).
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def get_or_create_nudge_state(
    session: Session,
    *,
    user_id: uuid.UUID,
    group_id: uuid.UUID,
    counterparty_user_id: uuid.UUID,
) -> NudgeState:
    """The engine's memory row for one relationship, created on demand."""
    state = session.exec(
        select(NudgeState).where(
            NudgeState.user_id == user_id,
            NudgeState.group_id == group_id,
            NudgeState.counterparty_user_id == counterparty_user_id,
        )
    ).first()
    if state is None:
        state = NudgeState(
            user_id=user_id,
            group_id=group_id,
            counterparty_user_id=counterparty_user_id,
        )
        session.add(state)
        session.flush()
        session.refresh(state)
    return state


# === Copy ===


def render_level_1(rel: DebtRelationship) -> tuple[str, str]:
    """
    The Level 1 message: factual, calm, and about a relationship rather than
    a receipt. It states the balance and names the group — enough to act on,
    with no urgency the debt has not yet earned.

    Deliberately NOT personality-flavoured: the group's `ai_personality`
    shapes the mediator's commentary while you're in the app and chose to be
    there. An unrequested notification is the wrong place to be funny.
    """
    who = rel.creditor_name or "someone in the group"
    amount = f"{rel.amount:.2f} {rel.currency}"
    title = f"You owe {who} {amount}"
    body = (
        f"That's your balance with {who} in {rel.group_name}. "
        "Open ClearDues to settle up whenever suits you."
    )
    return title, body


# === Sweep ===


def run_nudge_sweep(
    session: Session,
    *,
    now: datetime | None = None,
    group_id: uuid.UUID | None = None,
    dry_run: bool = False,
) -> NudgeSweepResult:
    """
    Find every debt relationship owed a Level 1 nudge, deliver it, and
    record what happened.

    Idempotent by cooldown: a relationship nudged inside
    NUDGE_COOLDOWN_HOURS is skipped, so running the sweep twice in a minute
    (a retried cron, an impatient curl) sends nothing twice. That, not the
    schedule, is what bounds the cadence.

    Callers own the transaction — the router commits (ARCH-001).
    """
    # Imported here: delivery pulls in optional third-party push/email
    # machinery, and the sweep's logic must stay importable (and testable)
    # even where those are absent.
    from app.features.notifications.delivery import deliver

    now = now or datetime.now(timezone.utc)
    threshold = timedelta(hours=settings.NUDGE_LEVEL_1_AFTER_HOURS)
    cooldown = timedelta(hours=settings.NUDGE_COOLDOWN_HOURS)

    result = NudgeSweepResult(
        relationships_examined=0,
        nudges_sent=0,
        suppressed_quiet_hours=0,
        suppressed_snoozed=0,
        suppressed_muted=0,
        suppressed_cooldown=0,
        deliveries={},
    )

    relationships = find_debt_relationships(session, group_id=group_id)
    prefs_cache: dict[uuid.UUID, NotificationPreference] = {}

    for rel in relationships:
        result.relationships_examined += 1

        if rel.amount < settings.NUDGE_MIN_AMOUNT:
            continue
        if now - rel.oldest_confirmed_at < threshold:
            continue

        prefs = prefs_cache.get(rel.debtor_id)
        if prefs is None:
            prefs = get_or_create_preferences(session, rel.debtor_id)
            prefs_cache[rel.debtor_id] = prefs

        if not prefs.nudges_enabled:
            result.suppressed_muted += 1
            continue

        state = get_or_create_nudge_state(
            session,
            user_id=rel.debtor_id,
            group_id=rel.group_id,
            counterparty_user_id=rel.creditor_id,
        )

        if state.muted:
            result.suppressed_muted += 1
            continue
        if state.snoozed_until and _as_aware(state.snoozed_until) > now:
            result.suppressed_snoozed += 1
            continue
        if state.last_nudged_at and now - _as_aware(state.last_nudged_at) < cooldown:
            result.suppressed_cooldown += 1
            continue
        # Quiet hours are checked LAST of the suppressors: they defer a
        # nudge rather than cancelling it, so the state row must stay
        # untouched and the next sweep outside the window will send it.
        if is_within_quiet_hours(prefs, now):
            result.suppressed_quiet_hours += 1
            continue

        title, body = render_level_1(rel)
        if dry_run:
            result.nudges_sent += 1
            continue

        outcomes = deliver(
            session,
            user_id=rel.debtor_id,
            prefs=prefs,
            title=title,
            body=body,
            group_id=rel.group_id,
        )

        for outcome in outcomes:
            session.add(
                Notification(
                    user_id=rel.debtor_id,
                    group_id=rel.group_id,
                    counterparty_user_id=rel.creditor_id,
                    event_type=EVENT_NUDGE_LEVEL_1,
                    level=NudgeLevel.LEVEL_1.value,
                    channel=outcome.channel,
                    status=outcome.status,
                    amount=rel.amount,
                    currency=rel.currency,
                    title=title,
                    body=body,
                    detail=outcome.detail,
                    sent_at=now,
                )
            )
            key = f"{outcome.channel.value}:{outcome.status.value}"
            result.deliveries[key] = result.deliveries.get(key, 0) + 1

        # The cooldown starts when the nudge was ATTEMPTED, not when it was
        # confirmed delivered. If every channel failed, retrying on the next
        # sweep would mean re-attempting a broken channel every few minutes;
        # the failure is recorded and the relationship waits its turn.
        state.last_nudged_at = now
        state.last_level = NudgeLevel.LEVEL_1.value
        state.updated_at = now
        session.add(state)

        if any(o.status == NotificationStatus.SENT for o in outcomes):
            result.nudges_sent += 1

    session.flush()
    return result
