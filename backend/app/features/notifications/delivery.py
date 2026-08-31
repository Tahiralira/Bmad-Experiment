# Notification delivery (WS12) — web push primary, email fallback.
#
# Both channels degrade to a recorded SKIP rather than an exception. A nudge
# that cannot be delivered is a product problem, not a request failure: the
# sweep must finish and say what happened, and one user's dead push endpoint
# must never abort everyone else's reminders.
#
# Email ships COMPLETE but inert: `settings.emails_enabled` is False until an
# SMTP provider is configured (deployment.md §6.6), exactly the env-gated
# pattern WS10.6 used for PostHog/Sentry. Setting SMTP_HOST turns it on with
# no code change.
import base64
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.config import settings
from app.features.auth.models import User
from app.features.notifications.models import (
    NotificationChannel,
    NotificationPreference,
    NotificationStatus,
    PushSubscription,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeliveryOutcome:
    """What happened on one channel for one recipient."""

    channel: NotificationChannel
    status: NotificationStatus
    detail: str | None = None


# How long to wait on ONE push endpoint. The sweep is a background job with
# nobody watching, so it can be patient.
PUSH_TIMEOUT_SECONDS = 10.0
# The budget when delivery happens inside a request the user is waiting on —
# WS13's "cleared without asking" fires from settlement confirmation. A push
# service that hasn't answered in three seconds is not about to make the
# moment better, and the notification is recorded as FAILED rather than
# holding up the settlement that caused it.
PUSH_TIMEOUT_INLINE_SECONDS = 3.0


def push_available() -> bool:
    """Whether this deployment can send web push at all."""
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def deliver(
    session: Session,
    *,
    user_id: uuid.UUID,
    prefs: NotificationPreference,
    title: str,
    body: str,
    group_id: uuid.UUID,
    suppress_push: bool = False,
    push_timeout: float = PUSH_TIMEOUT_SECONDS,
) -> list[DeliveryOutcome]:
    """
    Deliver one notification across the recipient's enabled channels.

    Push is attempted first and email is the FALLBACK, not a duplicate: a
    successful push means no email. Two buzzes for one debt is precisely the
    nagging the product promises not to do. Email still fires when push is
    unavailable, unsubscribed, denied, or failed — which is also the iOS
    story, where push needs an installed PWA.

    `suppress_push` skips the buzzing channel for THIS message only, without
    touching the stored preference. WS13's "cleared without asking" uses it
    during quiet hours: that message can't be deferred to a later sweep the
    way a nudge can, so instead of dropping it or overriding the user's
    preference it changes channel and lands in the morning's inbox.

    `push_timeout` is per endpoint. The sweep can afford to wait; anything
    delivering from inside a user's own request cannot, and passes a
    smaller number (see PUSH_TIMEOUT_INLINE_SECONDS).
    """
    outcomes: list[DeliveryOutcome] = []

    pushed = False
    if suppress_push:
        outcomes.append(
            DeliveryOutcome(
                NotificationChannel.PUSH,
                NotificationStatus.SKIPPED,
                "quiet hours",
            )
        )
    elif prefs.push_enabled:
        push_outcome = _deliver_push(
            session,
            user_id=user_id,
            title=title,
            body=body,
            group_id=group_id,
            timeout=push_timeout,
        )
        outcomes.append(push_outcome)
        pushed = push_outcome.status == NotificationStatus.SENT
    else:
        outcomes.append(
            DeliveryOutcome(
                NotificationChannel.PUSH,
                NotificationStatus.SKIPPED,
                "push disabled in preferences",
            )
        )

    if pushed:
        return outcomes

    if prefs.email_enabled:
        outcomes.append(
            _deliver_email(session, user_id=user_id, title=title, body=body)
        )
    else:
        outcomes.append(
            DeliveryOutcome(
                NotificationChannel.EMAIL,
                NotificationStatus.SKIPPED,
                "email disabled in preferences",
            )
        )

    return outcomes


# === Web push ===


def _vapid_private_key() -> str:
    """
    The VAPID private key in the ONE format pywebpush accepts.

    `py_vapid.Vapid01.from_string` strips newlines and base64url-DECODES the
    value, so a PEM (with its `-----BEGIN...` armor) fails with an opaque
    "ASN.1 parsing error" — caught by running the real push path rather than
    by reading the docs. Raw base64url and bare-DER base64 both work as-is;
    a PEM is converted here so that whichever form the operator pastes into
    the env var, push works.
    """
    raw = settings.VAPID_PRIVATE_KEY.strip()
    if "-----BEGIN" not in raw:
        return raw

    from cryptography.hazmat.primitives import serialization

    key = serialization.load_pem_private_key(raw.encode(), password=None)
    der = key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return base64.urlsafe_b64encode(der).decode().rstrip("=")


def _deliver_push(
    session: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    body: str,
    group_id: uuid.UUID,
    timeout: float = PUSH_TIMEOUT_SECONDS,
) -> DeliveryOutcome:
    if not push_available():
        return DeliveryOutcome(
            NotificationChannel.PUSH,
            NotificationStatus.SKIPPED,
            "no VAPID keypair configured",
        )

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:  # pragma: no cover - dependency is declared
        return DeliveryOutcome(
            NotificationChannel.PUSH,
            NotificationStatus.SKIPPED,
            "pywebpush not installed",
        )

    subs = session.exec(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    ).all()
    if not subs:
        return DeliveryOutcome(
            NotificationChannel.PUSH,
            NotificationStatus.SKIPPED,
            "no push subscriptions",
        )

    payload = json.dumps(
        {
            "title": title,
            "body": body,
            # Deep link straight to the group whose balance this is about —
            # a nudge that lands you on a dashboard has made you do the
            # finding, which is the work the product exists to remove.
            "url": f"{settings.FRONTEND_HOST}/groups/{group_id}",
            # One tag per group collapses repeat nudges about the same group
            # into a single notification rather than stacking them.
            "tag": f"nudge-{group_id}",
        }
    )

    sent = 0
    expired: list[PushSubscription] = []
    last_error: str | None = None

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=_vapid_private_key(),
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                timeout=timeout,
            )
            sub.last_used_at = datetime.now(timezone.utc)
            session.add(sub)
            sent += 1
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)
            last_error = f"{status or 'error'}"
            # 404/410 are the push service telling us this endpoint is dead
            # (browser uninstalled, subscription rotated). Keeping it would
            # mean retrying a guaranteed failure on every future sweep.
            if status in (404, 410):
                expired.append(sub)
            else:
                logger.warning("Web push failed for user %s: %s", user_id, exc)
        except Exception as exc:  # network/DNS/timeout
            last_error = type(exc).__name__
            logger.warning("Web push error for user %s: %s", user_id, exc)

    for sub in expired:
        session.delete(sub)

    if sent:
        return DeliveryOutcome(NotificationChannel.PUSH, NotificationStatus.SENT)
    if expired and last_error is None:
        return DeliveryOutcome(
            NotificationChannel.PUSH,
            NotificationStatus.SKIPPED,
            "all subscriptions expired",
        )
    return DeliveryOutcome(
        NotificationChannel.PUSH,
        NotificationStatus.FAILED,
        (last_error or "unknown push error")[:300],
    )


# === Email ===


def _deliver_email(
    session: Session, *, user_id: uuid.UUID, title: str, body: str
) -> DeliveryOutcome:
    if not settings.emails_enabled:
        return DeliveryOutcome(
            NotificationChannel.EMAIL,
            NotificationStatus.SKIPPED,
            "SMTP not configured",
        )

    user = session.get(User, user_id)
    if user is None or not user.email:
        return DeliveryOutcome(
            NotificationChannel.EMAIL,
            NotificationStatus.SKIPPED,
            "no recipient address",
        )

    try:
        from app.utils import render_email_template, send_email

        # `render_email_template` renders Jinja WITHOUT autoescape, and both
        # `title` and `body` carry user-supplied text (group name, display
        # name) — so they are escaped here rather than trusted.
        html = render_email_template(
            template_name="nudge_reminder.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "title": _escape(title),
                "body": _escape(body),
                "link": settings.FRONTEND_HOST,
            },
        )
        send_email(email_to=user.email, subject=title, html_content=html)
        return DeliveryOutcome(NotificationChannel.EMAIL, NotificationStatus.SENT)
    except Exception as exc:
        logger.warning("Nudge email failed for user %s: %s", user_id, exc)
        return DeliveryOutcome(
            NotificationChannel.EMAIL,
            NotificationStatus.FAILED,
            type(exc).__name__,
        )


def _escape(value: str) -> str:
    """
    Escape before interpolating into the HTML template. The copy is
    server-rendered today, but it carries a user-supplied group name and
    display name — the two places an injected `<script>` would ride in.
    """
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
