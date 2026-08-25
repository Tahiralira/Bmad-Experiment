# Notifications feature router (WS12 — Nudge Engine: Infra + Level 1).
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.features.auth.models import User
from app.features.groups.models import ExpenseGroup, GroupMember
from app.features.notifications import service
from app.features.notifications.delivery import push_available
from app.features.notifications.models import (
    NotificationPreferencePublic,
    NotificationPreferenceUpdate,
    NudgeRelationshipPublic,
    NudgeState,
    NudgeStateUpdate,
    NudgeSweepResult,
    PushSubscription,
    PushSubscriptionCreate,
    PushSubscriptionPublic,
    VapidPublicKeyResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# A user with more registered devices than this is almost certainly a bug or
# an abuse attempt, not someone with eleven browsers.
MAX_SUBSCRIPTIONS_PER_USER = 10


def _to_public(prefs) -> NotificationPreferencePublic:
    return NotificationPreferencePublic(
        nudges_enabled=prefs.nudges_enabled,
        push_enabled=prefs.push_enabled,
        email_enabled=prefs.email_enabled,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end,
        timezone=prefs.timezone,
    )


# === Preferences ===


@router.get("/preferences", response_model=NotificationPreferencePublic)
def get_my_preferences(
    session: SessionDep, current_user: CurrentUser
) -> NotificationPreferencePublic:
    """The caller's notification preferences, defaulted on first read."""
    prefs = service.get_or_create_preferences(session, current_user.id)
    session.commit()
    session.refresh(prefs)
    return _to_public(prefs)


@router.put("/preferences", response_model=NotificationPreferencePublic)
def update_my_preferences(
    *,
    session: SessionDep,
    body: NotificationPreferenceUpdate,
    current_user: CurrentUser,
) -> NotificationPreferencePublic:
    """
    Partially update the caller's preferences. Omitted fields are left
    alone; `clear_quiet_hours` is the explicit way to remove the window,
    since a null hour otherwise means "unchanged".
    """
    prefs = service.get_or_create_preferences(session, current_user.id)

    for field in ("nudges_enabled", "push_enabled", "email_enabled", "timezone"):
        value = getattr(body, field)
        if value is not None:
            setattr(prefs, field, value)

    if body.clear_quiet_hours:
        prefs.quiet_hours_start = None
        prefs.quiet_hours_end = None
    else:
        if body.quiet_hours_start is not None:
            prefs.quiet_hours_start = body.quiet_hours_start
        if body.quiet_hours_end is not None:
            prefs.quiet_hours_end = body.quiet_hours_end

    prefs.updated_at = datetime.now(timezone.utc)
    session.add(prefs)
    session.commit()
    session.refresh(prefs)
    return _to_public(prefs)


# === Web push subscriptions ===


@router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
def get_vapid_public_key() -> VapidPublicKeyResponse:
    """
    The server's VAPID public key, or null when push is not configured.

    Public by design: it is a public key, and the client needs it BEFORE
    asking for notification permission — prompting for a permission the
    server cannot act on spends the one prompt a browser ever grants.
    """
    return VapidPublicKeyResponse(
        key=settings.VAPID_PUBLIC_KEY if push_available() else None
    )


@router.post(
    "/subscriptions", response_model=PushSubscriptionPublic, status_code=201
)
def register_push_subscription(
    *,
    session: SessionDep,
    body: PushSubscriptionCreate,
    current_user: CurrentUser,
    user_agent: str | None = Header(default=None),
) -> PushSubscriptionPublic:
    """
    Register (or re-claim) a browser push endpoint for the caller.

    Re-registering an endpoint the caller already owns refreshes its keys
    instead of 409ing — browsers rotate subscription keys on their own
    schedule, and the client re-posts on every load, so this is the normal
    path, not an error.
    """
    existing = session.exec(
        select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    ).first()

    if existing is not None:
        # An endpoint is unique to one browser profile. If it comes back
        # under a different account, that browser was re-used — move it
        # rather than leaving the previous owner's nudges going to someone
        # else's device.
        existing.user_id = current_user.id
        existing.p256dh = body.p256dh
        existing.auth = body.auth
        existing.user_agent = (user_agent or None) and user_agent[:300]
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return PushSubscriptionPublic(
            id=existing.id,
            endpoint=existing.endpoint,
            created_at=existing.created_at,
        )

    count = len(
        session.exec(
            select(PushSubscription).where(
                PushSubscription.user_id == current_user.id
            )
        ).all()
    )
    if count >= MAX_SUBSCRIPTIONS_PER_USER:
        raise HTTPException(
            status_code=409,
            detail=(
                f"You can register up to {MAX_SUBSCRIPTIONS_PER_USER} devices "
                "for notifications. Remove one to add another."
            ),
        )

    sub = PushSubscription(
        user_id=current_user.id,
        endpoint=body.endpoint,
        p256dh=body.p256dh,
        auth=body.auth,
        user_agent=(user_agent or None) and user_agent[:300],
    )
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return PushSubscriptionPublic(
        id=sub.id, endpoint=sub.endpoint, created_at=sub.created_at
    )


@router.delete("/subscriptions", status_code=204)
def delete_push_subscription(
    *, session: SessionDep, endpoint: str, current_user: CurrentUser
) -> None:
    """
    Unregister one of the caller's push endpoints (the browser unsubscribed,
    or the user switched push off). Deleting an endpoint that isn't there is
    a success — the desired state is "not subscribed" either way.
    """
    sub = session.exec(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == current_user.id,
        )
    ).first()
    if sub is not None:
        session.delete(sub)
        session.commit()


# === Per-relationship mute / snooze ===


@router.get("/relationships", response_model=list[NudgeRelationshipPublic])
def list_nudge_relationships(
    session: SessionDep, current_user: CurrentUser
) -> list[NudgeRelationshipPublic]:
    """
    The caller's nudgeable relationships and their mute/snooze state — one
    row per (group, counterparty), which is the unit the engine addresses.

    Includes relationships with no state row yet (never nudged), so the
    settings screen can offer "mute this one" before the first reminder
    rather than only after it has already arrived.
    """
    relationships = service.find_debt_relationships(session)
    mine = [r for r in relationships if r.debtor_id == current_user.id]

    states = {
        (s.group_id, s.counterparty_user_id): s
        for s in session.exec(
            select(NudgeState).where(NudgeState.user_id == current_user.id)
        ).all()
    }

    out: list[NudgeRelationshipPublic] = []
    for rel in mine:
        state = states.get((rel.group_id, rel.creditor_id))
        out.append(
            NudgeRelationshipPublic(
                group_id=rel.group_id,
                group_name=rel.group_name,
                counterparty_user_id=rel.creditor_id,
                counterparty_name=rel.creditor_name,
                muted=bool(state and state.muted),
                snoozed_until=state.snoozed_until if state else None,
            )
        )
    out.sort(key=lambda r: (r.group_name, r.counterparty_name or ""))
    return out


@router.put(
    "/relationships/{group_id}/{counterparty_user_id}",
    response_model=NudgeRelationshipPublic,
)
def update_nudge_relationship(
    *,
    group_id: uuid.UUID,
    counterparty_user_id: uuid.UUID,
    session: SessionDep,
    body: NudgeStateUpdate,
    current_user: CurrentUser,
) -> NudgeRelationshipPublic:
    """
    Mute or snooze reminders about ONE relationship.

    Snooze defers (1/3/7 days per the duration picker); mute has no end
    date. `snooze_days: 0` clears an active snooze. Muting is the PRD's
    stop signal at relationship granularity — the user silences one awkward
    debt without going dark on the whole product.
    """
    group = session.get(ExpenseGroup, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found.")

    # The caller must be in the group. Without this, the endpoint would let
    # anyone create nudge_state rows naming arbitrary users and groups.
    membership = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
        )
    ).first()
    if membership is None:
        raise HTTPException(
            status_code=403, detail="You're not a member of that group."
        )
    counterparty_membership = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == counterparty_user_id,
        )
    ).first()
    if counterparty_membership is None:
        raise HTTPException(
            status_code=404, detail="That person isn't in this group."
        )

    state = service.get_or_create_nudge_state(
        session,
        user_id=current_user.id,
        group_id=group_id,
        counterparty_user_id=counterparty_user_id,
    )

    if body.muted is not None:
        state.muted = body.muted
    if body.snooze_days is not None:
        state.snoozed_until = (
            None
            if body.snooze_days == 0
            else datetime.now(timezone.utc) + timedelta(days=body.snooze_days)
        )
    state.updated_at = datetime.now(timezone.utc)
    session.add(state)
    session.commit()
    session.refresh(state)

    counterparty = session.get(User, counterparty_user_id)
    return NudgeRelationshipPublic(
        group_id=group_id,
        group_name=group.name,
        counterparty_user_id=counterparty_user_id,
        counterparty_name=(counterparty.full_name or counterparty.email)
        if counterparty
        else None,
        muted=state.muted,
        snoozed_until=state.snoozed_until,
    )


# === Scheduler entry point ===


@router.post("/internal/run-sweep", response_model=NudgeSweepResult)
def run_sweep(
    *,
    session: SessionDep,
    x_nudge_secret: str | None = Header(default=None),
    dry_run: bool = False,
) -> NudgeSweepResult:
    """
    Run one nudge sweep. This is the scheduler's entry point.

    Render's free tier has no background worker and no cron job, so the
    trigger lives outside the app: a GitHub Actions cron POSTs here on a
    schedule (`.github/workflows/nudge-sweep.yml`). The engine itself is an
    ordinary function — swapping in Celery beat later changes the caller,
    not this code.

    Auth is a shared secret in `X-Nudge-Secret`, compared in constant time.
    When `NUDGE_CRON_SECRET` is unset the route 404s: an unconfigured
    deployment exposes no sweep endpoint at all, rather than one guarded by
    an empty string.
    """
    if not settings.NUDGE_CRON_SECRET:
        raise HTTPException(status_code=404, detail="Not Found")
    if not x_nudge_secret or not secrets.compare_digest(
        x_nudge_secret, settings.NUDGE_CRON_SECRET
    ):
        raise HTTPException(status_code=403, detail="Forbidden")

    result = service.run_nudge_sweep(session, dry_run=dry_run)
    # The router owns the commit (ARCH-001): notification rows and the
    # nudge_state cooldown stamps land in ONE transaction, so a crash
    # mid-sweep cannot leave a nudge recorded as sent with no cooldown set
    # (which would re-nudge on the next run).
    session.commit()
    return result
