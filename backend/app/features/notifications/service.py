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
    EVENT_NUDGE_CLEARED,
    NUDGE_EVENT_BY_LEVEL,
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationStatus,
    NudgeLevel,
    NudgeMetrics,
    NudgeState,
    NudgeSweepResult,
)

logger = logging.getLogger(__name__)


# === Preferences ===


def get_or_create_preferences(
    session: Session, user_id: uuid.UUID, *, for_update: bool = False
) -> NotificationPreference:
    """
    A user's preferences, created with defaults on first access. Absence of
    a row means "never touched the settings", not "opted out" — so the row
    is materialised rather than treated as a silent opt-out.

    `for_update` takes a row lock (WS4/M8's discipline). Every write to this
    table is a read-modify-write of ONE row, so two concurrent partial
    updates from the same account — two tabs, a phone and a laptop — would
    otherwise lose one another: whichever committed second would write back
    the whole row including the field it never touched. Found in WS13 by
    Playwright running three notification specs in parallel as one user,
    where switching reminders off would silently revert. CI never saw it
    (`workers: 1`), which is exactly why it survived WS12.
    """
    statement = select(NotificationPreference).where(
        NotificationPreference.user_id == user_id
    )
    if for_update:
        statement = statement.with_for_update()
    prefs = session.exec(statement).first()
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


# === The ladder ===


def _next_level(state: NudgeState, age: timedelta) -> int | None:
    """
    Which rung this relationship is owed next, or None when the ladder is
    spent and the engine should stay quiet.

    Two rules define Progressive Urgency here:

    1. **You always get the gentle one first.** Level 2 requires a Level 1
       to have actually been sent, never merely that the debt is old enough.
       A debt discovered at five days — the engine was off, the user had it
       muted, a snooze just lapsed — still opens with Level 1. Escalation is
       a property of the CONVERSATION, not of the calendar; the alternative
       is someone's first ever word from the agent being its firmest.

    2. **The ladder ends.** Level 3 is cut from the product, so Level 2 is
       the top rung, and a top rung that repeats forever is the nagging
       ClearDues exists to remove. After NUDGE_LEVEL_2_MAX_REMINDERS the
       answer is None and the agent says nothing further about this debt.
    """
    if state.last_level is None:
        return NudgeLevel.LEVEL_1.value

    if state.last_level >= NudgeLevel.LEVEL_2.value:
        if state.level_2_count >= settings.NUDGE_LEVEL_2_MAX_REMINDERS:
            return None
        return NudgeLevel.LEVEL_2.value

    # Had Level 1. Old enough for the contextual nudge?
    if age >= timedelta(hours=settings.NUDGE_LEVEL_2_AFTER_HOURS):
        return NudgeLevel.LEVEL_2.value
    return NudgeLevel.LEVEL_1.value


def _cooldown_for(last_level: int | None) -> timedelta:
    """
    How long to wait after a nudge before the next one may go out.

    This is the FREQUENCY half of Progressive Urgency: once a relationship
    is at Level 2 the gap narrows, so an older debt is heard from more
    often. The tone escalates and the cadence escalates with it — a firmer
    message sent at the same leisurely interval would not be an escalation.
    """
    if last_level is not None and last_level >= NudgeLevel.LEVEL_2.value:
        return timedelta(hours=settings.NUDGE_LEVEL_2_COOLDOWN_HOURS)
    return timedelta(hours=settings.NUDGE_COOLDOWN_HOURS)


def is_exhausted(state: NudgeState) -> bool:
    """Whether the engine has deliberately stopped nudging this relationship."""
    return (
        state.last_level is not None
        and state.last_level >= NudgeLevel.LEVEL_2.value
        and state.level_2_count >= settings.NUDGE_LEVEL_2_MAX_REMINDERS
    )


def _days_ago(then: datetime, now: datetime) -> str:
    """
    Debt age in whole days, phrased for a lock screen.

    Rounded DOWN, never up: the number appears in a message whose whole
    claim is that it is telling you something true, and "6 days" about a
    five-and-a-half-day-old debt is the small dishonesty that makes the
    rest of the sentence worth less.
    """
    days = max((now - then).days, 0)
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    return f"{days} days ago"


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


def render_level_2(rel: DebtRelationship, now: datetime) -> tuple[str, str]:
    """
    The Level 2 message: the same debt, told from the CREDITOR's side.

    The context is deliberately narrow — what the person owed money did
    (they covered it) and how long they have been waiting. That is the
    escalation the PRD's Journey 2 describes: it reframes the balance from
    an admin task into someone else's real money, which is what makes it
    feel helpful rather than demanding.

    What it deliberately does NOT say is what anyone ELSE in the group has
    done. "Three of four have paid" would be more persuasive and would be
    Level 3 — social pressure — which is cut from the product (02 Phase B).
    The line between the two rungs is exactly this: Level 2 tells you about
    the person you owe; Level 3 would tell you about your standing among
    your friends. Only one of those is the agent's business.
    """
    who = rel.creditor_name or "someone in the group"
    amount = f"{rel.amount:.2f} {rel.currency}"
    when = _days_ago(rel.oldest_confirmed_at, now)
    title = f"{who} is still owed {amount}"
    body = (
        f"{who} covered this {when} in {rel.group_name} and is still out of "
        "pocket. Settling takes a tap."
    )
    return title, body


def render_cleared(
    *, counterparty_name: str | None, group_name: str, amount: Decimal, currency: str
) -> tuple[str, str]:
    """
    The "cleared without asking" message (02 §7, wow moment #2) — the only
    notification in the product that is purely good news.

    It is addressed to the CREDITOR, and its second sentence is the entire
    brand promise: they got their money back and never had to be the person
    who brings it up. That sentence is only allowed to be said where it is
    true, which is why `notify_debt_cleared` refuses to send it unless this
    engine really did the asking.
    """
    who = counterparty_name or "Someone in the group"
    money = f"{amount:.2f} {currency}"
    title = f"{who} settled up — {money}"
    body = (
        f"Your balance with {who} in {group_name} is clear. "
        "You never had to ask."
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

    result = NudgeSweepResult(
        relationships_examined=0,
        nudges_sent=0,
        nudges_by_level={},
        suppressed_quiet_hours=0,
        suppressed_snoozed=0,
        suppressed_muted=0,
        suppressed_cooldown=0,
        suppressed_exhausted=0,
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
        # Checked before the cooldown because exhaustion is PERMANENT: a
        # relationship the engine has finished with should report as
        # exhausted every sweep, not spend a day looking merely cooled-down.
        if is_exhausted(state):
            result.suppressed_exhausted += 1
            continue
        if state.last_nudged_at and now - _as_aware(
            state.last_nudged_at
        ) < _cooldown_for(state.last_level):
            result.suppressed_cooldown += 1
            continue
        # Quiet hours are checked LAST of the suppressors: they defer a
        # nudge rather than cancelling it, so the state row must stay
        # untouched and the next sweep outside the window will send it.
        if is_within_quiet_hours(prefs, now):
            result.suppressed_quiet_hours += 1
            continue

        level = _next_level(state, now - rel.oldest_confirmed_at)
        if level is None:  # pragma: no cover - is_exhausted caught this above
            result.suppressed_exhausted += 1
            continue

        if level >= NudgeLevel.LEVEL_2.value:
            title, body = render_level_2(rel, now)
        else:
            title, body = render_level_1(rel)

        if dry_run:
            result.nudges_sent += 1
            key = f"level_{level}"
            result.nudges_by_level[key] = result.nudges_by_level.get(key, 0) + 1
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
                    event_type=NUDGE_EVENT_BY_LEVEL[level],
                    level=level,
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
        #
        # The LADDER advances on the same rule, for the same reason: a rung
        # is spent by being climbed. Tying it to delivery success instead
        # would let a user with a dead push endpoint and no email accumulate
        # an unbounded backlog of undeliverable Level 2s.
        state.last_nudged_at = now
        state.last_level = level
        if level >= NudgeLevel.LEVEL_2.value:
            state.level_2_count += 1
        state.updated_at = now
        session.add(state)

        key = f"level_{level}"
        result.nudges_by_level[key] = result.nudges_by_level.get(key, 0) + 1

        if any(o.status == NotificationStatus.SENT for o in outcomes):
            result.nudges_sent += 1

    session.flush()
    return result


# === "Cleared without asking" (WS13 — 02 §7, wow moment #2) ===


def notify_debt_cleared(
    session: Session,
    *,
    group_id: uuid.UUID,
    debtor_id: uuid.UUID,
    creditor_id: uuid.UUID,
    amount: Decimal,
    currency: str,
    now: datetime | None = None,
) -> bool:
    """
    Tell the CREDITOR their balance cleared — and that they never had to ask.

    Fires INLINE from settlement confirmation rather than from the sweep,
    because this is the one notification whose value is in its timing: an
    hour-late "you've been paid" is a receipt, and the point of this one is
    the moment. Delivery cost is kept off the critical path by the
    guarantees below, not by deferring it.

    Three rules make the sentence honest:

    1. **Only if the agent actually asked.** `last_level is None` means no
       ladder is running for this relationship, so nobody was nudged and
       "you never had to ask" would be a lie — the creditor may well have
       asked in person. Returns False and says nothing.
    2. **Only if the debt is really gone.** A partial settlement leaves a
       balance; recomputing beats trusting the caller's claim amount.
    3. **Only once.** Clearing `last_level` both ends the ladder and closes
       this door, so a second confirmation in the same breath (two claims,
       an auto-confirm racing a manual one) finds nothing to announce.

    Never raises: the caller is in the middle of settling a debt, and a
    failed notification must not fail a settlement. Everything runs inside a
    SAVEPOINT, so a database error here rolls back the notification alone
    and leaves the settlement's own writes intact.

    Callers own the transaction (ARCH-001) — this flushes, never commits.
    """
    try:
        with session.begin_nested():
            return _notify_debt_cleared_inner(
                session,
                group_id=group_id,
                debtor_id=debtor_id,
                creditor_id=creditor_id,
                amount=amount,
                currency=currency,
                now=now,
            )
    except Exception as exc:
        logger.warning(
            "Cleared-debt notification failed for group %s (%s → %s): %s",
            group_id,
            debtor_id,
            creditor_id,
            exc,
        )
        return False


def _notify_debt_cleared_inner(
    session: Session,
    *,
    group_id: uuid.UUID,
    debtor_id: uuid.UUID,
    creditor_id: uuid.UUID,
    amount: Decimal,
    currency: str,
    now: datetime | None,
) -> bool:
    from app.features.notifications.delivery import (
        PUSH_TIMEOUT_INLINE_SECONDS,
        deliver,
    )

    now = now or datetime.now(timezone.utc)

    state = session.exec(
        select(NudgeState).where(
            NudgeState.user_id == debtor_id,
            NudgeState.group_id == group_id,
            NudgeState.counterparty_user_id == creditor_id,
        )
    ).first()
    # Rule 1 and rule 3, in one condition.
    if state is None or state.last_level is None:
        return False

    # Rule 2: still owing means this was a partial payment, not a clearing.
    still_owing = any(
        rel.debtor_id == debtor_id and rel.creditor_id == creditor_id
        for rel in find_debt_relationships(session, group_id=group_id)
    )
    if still_owing:
        return False

    # The ladder is over either way — the debt is gone. Reset it BEFORE the
    # delivery decisions below, so a creditor who has switched reminders off
    # doesn't leave a stale ladder that would resume mid-escalation on the
    # relationship's next debt.
    #
    # `last_nudged_at` is deliberately NOT cleared: WS12's cooldown has to
    # survive a debt going to zero and coming back, or a new expense between
    # the same two people could be nudged the moment it lands.
    state.last_level = None
    state.level_2_count = 0
    state.updated_at = now
    session.add(state)

    prefs = get_or_create_preferences(session, creditor_id)
    if not prefs.nudges_enabled:
        # They asked for silence. Good news is still news.
        session.flush()
        return False

    group = session.get(ExpenseGroup, group_id)
    debtor = session.get(User, debtor_id)
    title, body = render_cleared(
        counterparty_name=_display_name(debtor),
        group_name=group.name if group else "your group",
        amount=amount,
        currency=currency,
    )

    # Quiet hours can't DEFER here the way they do in the sweep — there is no
    # later pass to pick this up — so instead of dropping the message or
    # overriding the preference, it changes channel. Email arrives without
    # buzzing anyone at 3am, and is waiting in the morning.
    quiet = is_within_quiet_hours(prefs, now)

    outcomes = deliver(
        session,
        user_id=creditor_id,
        prefs=prefs,
        title=title,
        body=body,
        group_id=group_id,
        suppress_push=quiet,
        # This runs while someone waits for their settlement to confirm.
        push_timeout=PUSH_TIMEOUT_INLINE_SECONDS,
    )

    for outcome in outcomes:
        session.add(
            Notification(
                user_id=creditor_id,
                group_id=group_id,
                counterparty_user_id=debtor_id,
                event_type=EVENT_NUDGE_CLEARED,
                # Level 0: this is not a rung on the urgency ladder. Storing
                # it as Level 1 would quietly inflate Escalation Efficacy
                # with notifications that never nudged anyone.
                level=0,
                channel=outcome.channel,
                status=outcome.status,
                amount=amount,
                currency=currency,
                title=title,
                body=body,
                detail=outcome.detail
                or ("quiet hours — email only" if quiet else None),
                sent_at=now,
            )
        )

    session.flush()
    return any(o.status == NotificationStatus.SENT for o in outcomes)


# === Kill-switch telemetry (WS13 — analytics-spec §4 "Mute rate") ===

# Event types that represent the agent nudging someone. `EVENT_NUDGE_CLEARED`
# is deliberately not among them: being told you were paid is not a nudge,
# and counting it as one would dilute the very rate the PRD uses to decide
# whether to stop the product.
_REMINDER_EVENTS = tuple(NUDGE_EVENT_BY_LEVEL.values())


def compute_nudge_metrics(
    session: Session, *, window_days: int = 30, now: datetime | None = None
) -> NudgeMetrics:
    """
    The kill-switch numbers, straight from the database.

    PostHog cannot compute the mute RATE on its own: it sees the browser
    firing `nudge.notification.muted` but never sees a send, because sends
    happen server-side in the sweep. analytics-spec §4 spells out the
    consequence — the denominator has to come from the API database, and
    substituting a client-side proxy "would flatter the metric the PRD
    relies on to stop the product". This function is that denominator,
    published so the weekly review is a page load rather than a psql
    session against production.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)

    sent_in_window = [
        sa.and_(
            Notification.status == NotificationStatus.SENT,
            Notification.sent_at >= cutoff,
        )
    ]

    nudged_user_ids = set(
        session.exec(
            select(Notification.user_id)
            .where(
                Notification.event_type.in_(_REMINDER_EVENTS),
                *sent_in_window,
            )
            .distinct()
        ).all()
    )

    # Muted counts are restricted to people who were actually REACHED. The
    # metric is "share of nudged people who switch reminders off": someone
    # who muted before ever hearing from the agent is not evidence about
    # the agent, and including them would move the stop signal for reasons
    # that have nothing to do with nudging.
    muted_global: set[uuid.UUID] = set()
    muted_relationship: set[uuid.UUID] = set()
    if nudged_user_ids:
        muted_global = set(
            session.exec(
                select(NotificationPreference.user_id).where(
                    NotificationPreference.user_id.in_(nudged_user_ids),
                    NotificationPreference.nudges_enabled == False,  # noqa: E712
                )
            ).all()
        )
        muted_relationship = set(
            session.exec(
                select(NudgeState.user_id)
                .where(
                    NudgeState.user_id.in_(nudged_user_ids),
                    NudgeState.muted == True,  # noqa: E712
                )
                .distinct()
            ).all()
        )

    muted_any = muted_global | muted_relationship

    level_rows = session.exec(
        select(Notification.level, sa.func.count())
        .where(Notification.event_type.in_(_REMINDER_EVENTS), *sent_in_window)
        .group_by(Notification.level)
    ).all()
    channel_rows = session.exec(
        select(Notification.channel, sa.func.count())
        .where(Notification.event_type.in_(_REMINDER_EVENTS), *sent_in_window)
        .group_by(Notification.channel)
    ).all()

    sends_by_level = {f"level_{level}": count for level, count in level_rows}
    sends_by_channel = {
        (channel.value if isinstance(channel, NotificationChannel) else str(channel)): count
        for channel, count in channel_rows
    }
    notifications_sent = sum(sends_by_level.values())

    cleared = session.exec(
        select(sa.func.count())
        .select_from(Notification)
        .where(Notification.event_type == EVENT_NUDGE_CLEARED, *sent_in_window)
    ).one()

    exhausted = session.exec(
        select(sa.func.count())
        .select_from(NudgeState)
        .where(
            NudgeState.last_level >= NudgeLevel.LEVEL_2.value,
            NudgeState.level_2_count >= settings.NUDGE_LEVEL_2_MAX_REMINDERS,
        )
    ).one()

    return NudgeMetrics(
        window_days=window_days,
        users_nudged=len(nudged_user_ids),
        users_muted_global=len(muted_global),
        users_muted_relationship=len(muted_relationship),
        users_muted_any=len(muted_any),
        # An unknown rate is reported as null, never as 0.0. Over an empty
        # denominator "0% mute rate" reads as "nobody minds" when it
        # actually means "nobody has been asked yet" — and this is the
        # number the PRD would stop the product on.
        mute_rate=(
            round(len(muted_any) / len(nudged_user_ids), 4)
            if nudged_user_ids
            else None
        ),
        notifications_sent=notifications_sent,
        sends_by_level=sends_by_level,
        sends_by_channel=sends_by_channel,
        debts_cleared_after_nudge=int(cleared),
        relationships_exhausted=int(exhausted),
    )
