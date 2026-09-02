# Notifications feature models (WS12 — Nudge Engine: Infra + Level 1).
#
# The one structural commitment this file makes: a nudge is addressed to a
# RELATIONSHIP inside a GROUP — (debtor, creditor, group) — never to an
# expense. `nudge_state`'s unique constraint is what enforces it; twelve
# unsettled dinners between the same two people are one debt and can produce
# at most one nudge. Per-expense nudging is the failure mode the product
# review named explicitly (02 Phase B), so it is prevented by the schema
# rather than by developer discipline.
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlmodel import Field, SQLModel, UniqueConstraint

from app.features.auth.models import utc_now

# Timezone-aware timestamps to match the migrations (WS5/B-H9 reconcile).
_AWARE_DATETIME = sa.DateTime(timezone=True)

# SQLAlchemy enum columns store member NAMES, not values (WS5 learning) —
# native_enum=False + an explicit length keeps DDL and models reconcilable.


class NotificationChannel(str, PyEnum):
    """How a notification was (or would be) delivered."""

    PUSH = "push"
    EMAIL = "email"


class NotificationStatus(str, PyEnum):
    """Terminal state of one delivery attempt on one channel."""

    SENT = "sent"
    FAILED = "failed"
    # The nudge was owed but deliberately not delivered on this channel —
    # no subscription, channel switched off, or email inert because SMTP is
    # unconfigured. Recorded rather than dropped so "why didn't I get it?"
    # is answerable without reading logs.
    SKIPPED = "skipped"


class NudgeLevel(int, PyEnum):
    """
    Progressive Urgency levels (PRD §FR11).

    Level 1 (WS12) — a gentle, factual statement of the balance.
    Level 2 (WS13) — the contextual nudge: the same debt, now told from the
    creditor's side and with its age attached.
    Level 3 — social pressure — is CUT from the product (02 Phase B, "defer
    Level 3 entirely"), and is cut in the strong sense: the ladder has no
    third rung, so Level 2 is the top. Because a top rung that repeated
    forever would become the nagging ClearDues exists to remove, the engine
    goes quiet after NUDGE_LEVEL_2_MAX_REMINDERS. Silence is the last rung.
    """

    LEVEL_1 = 1
    LEVEL_2 = 2


# The event envelope, adopted for real (03-technical-backend H1). The old
# Redis publisher used a flat ad-hoc shape for a bus that never existed; the
# name is now the notification's own type field and follows the SAME
# `domain.entity.action` convention as the WS10.6 analytics taxonomy, so one
# vocabulary covers both. Redis Pub/Sub is descoped — see architecture.md.
EVENT_NUDGE_LEVEL_1 = "nudge.reminder.level_1"
EVENT_NUDGE_LEVEL_2 = "nudge.reminder.level_2"
# The brand promise made visible (02 §7, wow moment #2): the person who was
# OWED money is told their dues cleared — and that they never had to ask,
# because the agent did the asking. Sent only where that sentence is true:
# only if this engine actually nudged the relationship. See
# `notify_debt_cleared`.
EVENT_NUDGE_CLEARED = "nudge.debt.cleared"
# A member has just been assigned a share of a newly-split expense and needs
# to confirm it (audit finding F8 — before this, participants only found out
# by opening /pending). Not a rung on the urgency ladder: it fires once, at
# split time, carries no level, and is the FIRST thing the participant hears
# about the debt. See `notify_split_assigned`.
EVENT_EXPENSE_SPLIT_ASSIGNED = "expense.split.assigned"

# Level → event name. Kept as a mapping rather than an f-string so an
# unknown level fails loudly at the lookup instead of inventing an event
# type the analytics taxonomy has never heard of.
NUDGE_EVENT_BY_LEVEL: dict[int, str] = {
    NudgeLevel.LEVEL_1.value: EVENT_NUDGE_LEVEL_1,
    NudgeLevel.LEVEL_2.value: EVENT_NUDGE_LEVEL_2,
}


# === Tables ===


class NotificationPreference(SQLModel, table=True):
    """
    Per-user delivery preferences. One row per user, created lazily on first
    read or write — absence means "all defaults", never "no nudges".

    `nudges_enabled` is the user-facing kill switch the PRD requires
    (mute rate is the product's stop signal); turning it off suppresses
    every nudge on every channel without deleting push subscriptions, so
    turning it back on needs no permission re-prompt.
    """

    __tablename__ = "notification_preference"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_notification_preference_user"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )

    nudges_enabled: bool = Field(default=True)
    push_enabled: bool = Field(default=True)
    email_enabled: bool = Field(default=True)

    # Quiet hours as local wall-clock hours [start, end), interpreted in
    # `timezone`. Both None = no quiet hours. start > end wraps midnight
    # (22 → 8 is the useful case, so wrapping is the norm, not an edge case).
    quiet_hours_start: int | None = Field(default=22, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=8, ge=0, le=23)
    # IANA zone name. Nudges are about someone's evening, not the server's.
    timezone: str = Field(default="UTC", max_length=64)

    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)


class NudgeState(SQLModel, table=True):
    """
    The engine's memory for ONE debt relationship in ONE group.

    UNIQUE(user_id, group_id, counterparty_user_id) is the guarantee that
    nudges are per-relationship-per-group: there is nowhere to record a
    per-expense nudge even if someone tried. `user_id` is the debtor (the
    person nudged); `counterparty_user_id` is the creditor.

    Rows are created on first nudge and outlive settlement — the cooldown
    and any snooze must survive a debt going to zero and coming back, or a
    borrower could be re-nudged the moment a new expense lands.
    """

    __tablename__ = "nudge_state"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "group_id",
            "counterparty_user_id",
            name="uq_nudge_state_relationship",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )
    group_id: uuid.UUID = Field(
        foreign_key="expense_group.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    counterparty_user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )

    last_nudged_at: datetime | None = Field(default=None, sa_type=_AWARE_DATETIME)
    # Where this relationship sits on the ladder RIGHT NOW. None means the
    # ladder is not running: either it never started, or the debt cleared
    # and the success notification already went out. That second meaning is
    # what makes `notify_debt_cleared` idempotent without another column —
    # it fires only while a ladder is active, and clearing `last_level` is
    # what ends it.
    last_level: int | None = Field(default=None)
    # How many Level 2 reminders this relationship has had. The cap
    # (NUDGE_LEVEL_2_MAX_REMINDERS) is the ladder's end: with Level 3 cut,
    # something has to stop the top rung repeating forever.
    level_2_count: int = Field(default=0)
    # User-chosen deferral for this one relationship ("not about Sam, not
    # this week"). Distinct from `muted`, which has no end date.
    snoozed_until: datetime | None = Field(default=None, sa_type=_AWARE_DATETIME)
    muted: bool = Field(default=False)

    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)


class Notification(SQLModel, table=True):
    """
    One delivery attempt on one channel — the auditable record of what the
    agent actually said, to whom, and whether it arrived.

    The rendered `title`/`body` are stored rather than re-derived: the copy
    is the product, and "what did it say to me on Tuesday" must be
    answerable after the balance has changed.
    """

    __tablename__ = "notification"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )
    group_id: uuid.UUID = Field(
        foreign_key="expense_group.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    counterparty_user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", nullable=True, ondelete="SET NULL"
    )

    event_type: str = Field(max_length=64, index=True)
    level: int = Field(default=NudgeLevel.LEVEL_1.value)
    channel: NotificationChannel = Field(
        sa_type=sa.Enum(NotificationChannel, native_enum=False, length=20),
    )
    status: NotificationStatus = Field(
        sa_type=sa.Enum(NotificationStatus, native_enum=False, length=20),
    )

    # Snapshot of the debt at send time. Amounts are Decimal end-to-end and
    # string on the wire (WS5 learning); currency comes from the group.
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = Field(max_length=3)

    title: str = Field(max_length=200)
    body: str = Field(max_length=500)
    # Why a SKIPPED/FAILED attempt didn't land. Never surfaced to the user.
    detail: str | None = Field(default=None, max_length=300)

    sent_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)


class PushSubscription(SQLModel, table=True):
    """
    One browser push endpoint (Web Push / RFC 8030). A user may have several
    — phone, laptop, installed PWA — so the unique key is the endpoint, not
    the user.

    `p256dh` and `auth` are the browser's own public key material for
    payload encryption. They are not credentials of ours and cannot be used
    to read anything; they only let this server encrypt a payload that only
    that browser can open.
    """

    __tablename__ = "push_subscription"
    __table_args__ = (
        UniqueConstraint("endpoint", name="uq_push_subscription_endpoint"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, index=True, ondelete="CASCADE"
    )

    endpoint: str = Field(max_length=500)
    p256dh: str = Field(max_length=200)
    auth: str = Field(max_length=100)
    user_agent: str | None = Field(default=None, max_length=300)

    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    last_used_at: datetime | None = Field(default=None, sa_type=_AWARE_DATETIME)


# === Request/Response Schemas ===


class NotificationPreferencePublic(SQLModel):
    """Response schema for GET/PUT /users/me/notification-preferences."""

    nudges_enabled: bool
    push_enabled: bool
    email_enabled: bool
    quiet_hours_start: int | None
    quiet_hours_end: int | None
    timezone: str


class NotificationPreferenceUpdate(SQLModel):
    """
    Request schema for PUT /users/me/notification-preferences. Every field
    is optional — a partial update leaves the rest untouched.
    """

    nudges_enabled: bool | None = None
    push_enabled: bool | None = None
    email_enabled: bool | None = None
    quiet_hours_start: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=None, ge=0, le=23)
    timezone: str | None = Field(default=None, max_length=64)
    # Explicitly clear quiet hours (distinct from "leave unchanged", which
    # is what a plain None on the two hour fields means).
    clear_quiet_hours: bool | None = None


class PushSubscriptionCreate(SQLModel):
    """Request schema for POST /users/me/push-subscriptions."""

    endpoint: str = Field(min_length=1, max_length=500)
    p256dh: str = Field(min_length=1, max_length=200)
    auth: str = Field(min_length=1, max_length=100)


class PushSubscriptionPublic(SQLModel):
    """Response schema for a registered push endpoint."""

    id: uuid.UUID
    endpoint: str
    created_at: datetime


class VapidPublicKeyResponse(SQLModel):
    """
    Response for GET /notifications/vapid-public-key. `key` is null when the
    server has no VAPID keypair configured — the client then knows push is
    unavailable and doesn't prompt for a permission it can't use.
    """

    key: str | None


class NudgeRelationshipPublic(SQLModel):
    """One nudgeable relationship's mute/snooze state, for the settings UI."""

    group_id: uuid.UUID
    group_name: str
    counterparty_user_id: uuid.UUID
    counterparty_name: str | None
    muted: bool
    snoozed_until: datetime | None
    # Where the ladder stands, shown to the person being nudged. Someone
    # deciding whether to mute deserves to know whether the agent is on its
    # first gentle reminder or its last one — the alternative is a mute
    # button pressed blind.
    last_level: int | None = None
    # True once the Level 2 cap is reached: the engine has gone quiet about
    # this debt of its own accord. Saying so is the difference between an
    # agent that stops and an agent that merely happens not to have sent
    # anything today.
    reminders_exhausted: bool = False


class NudgeStateUpdate(SQLModel):
    """Request schema for muting or snoozing one relationship."""

    muted: bool | None = None
    # Snooze duration in days (1, 3 or 7 per the Epic 6.4 duration picker).
    # 0 clears an active snooze.
    snooze_days: int | None = Field(default=None, ge=0, le=30)


class NudgeSweepResult(SQLModel):
    """
    What one sweep did — the cron endpoint's response body, and the only
    view an operator gets of a system whose success looks like silence.
    `nudges_by_level` is what makes Escalation Efficacy (PRD §Validation)
    measurable at all: how much of the ladder people actually needed.
    """

    relationships_examined: int
    nudges_sent: int
    nudges_by_level: dict[str, int] = Field(default_factory=dict)
    suppressed_quiet_hours: int
    suppressed_snoozed: int
    suppressed_muted: int
    suppressed_cooldown: int
    # Relationships the engine has deliberately stopped nudging: the Level 2
    # cap is spent. Counted rather than silently skipped, so "the agent went
    # quiet" is a number an operator can see rather than an absence.
    suppressed_exhausted: int = 0
    deliveries: dict[str, int]


class NudgeMetrics(SQLModel):
    """
    The server-side half of the PRD's kill-switch metric (analytics-spec §4,
    "Mute rate").

    PostHog holds the numerator — `nudge.notification.muted`, fired by the
    browser when someone switches reminders off. It cannot hold the
    denominator: nudges are DELIVERED server-side by the sweep, so no
    browser ever witnesses a send, and a client-side proxy would flatter the
    one metric the PRD relies on to STOP the product. These counts come
    straight from the `notification` and `nudge_state` tables.

    `mute_rate` is the number the stop signal is read off: muted people ÷
    people who were actually reached. It is null when nobody has been
    nudged yet — a rate over an empty denominator is not 0%, it is unknown,
    and reporting it as 0% would read as "nobody minds" on day one.
    """

    window_days: int
    # People who received at least one nudge that was actually SENT on some
    # channel. Attempts that were skipped or failed are excluded: someone
    # who was never reached cannot have been annoyed.
    users_nudged: int
    # Of those, how many have since silenced reminders — globally
    # (nudges_enabled = false) or on any single relationship.
    users_muted_global: int
    users_muted_relationship: int
    users_muted_any: int
    mute_rate: float | None
    # Volume, for context on the rate. A 50% mute rate over two people is
    # noise; over two hundred it is the stop signal.
    notifications_sent: int
    sends_by_level: dict[str, int]
    sends_by_channel: dict[str, int]
    # Debts that cleared after the agent had nudged — the brand promise
    # actually landing. The counterweight to mute rate: if this is rising
    # faster than mutes, the nudging is working.
    debts_cleared_after_nudge: int
    # Relationships where the ladder ran out and the engine went quiet.
    # Rising here means Level 2 is not converting and the escalation is
    # being ignored rather than obeyed.
    relationships_exhausted: int
