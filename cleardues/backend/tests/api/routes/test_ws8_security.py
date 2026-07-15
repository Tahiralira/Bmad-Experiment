"""WS8 — template purge & security hardening.

Covers: template routes are gone (404), security headers, per-IP rate
limiting, one-time OAuth login codes, JWT revocation (logout), and invite
usage caps / revocation.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import ALGORITHM
from app.features.auth import service as auth_service
from app.models import UserCreate
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)


def _make_user(db: Session):
    return crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )


# ---------------------------------------------------------------------------
# Template surface is dead (S5-H5, S4-H2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/login/access-token"),
        ("POST", "/login/test-token"),
        ("POST", "/password-recovery/someone@example.com"),
        ("POST", "/reset-password/"),
        ("POST", "/users/signup"),
        ("PATCH", "/users/me/password"),
        ("POST", "/private/users/"),
        ("GET", "/users/"),  # superuser list
        ("POST", "/users/"),  # superuser create
    ],
)
def test_template_routes_are_gone(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    method: str,
    path: str,
) -> None:
    """The parallel password-auth stack and admin CRUD return 404 even for a
    superuser — deleted, not just gated."""
    r = client.request(
        method, f"{settings.API_V1_STR}{path}", headers=superuser_token_headers
    )
    assert r.status_code in (404, 405), f"{method} {path} -> {r.status_code}"


# ---------------------------------------------------------------------------
# Security headers (S5-M1)
# ---------------------------------------------------------------------------


def test_security_headers_present(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert r.headers["Content-Security-Policy"] == (
        "default-src 'none'; frame-ancestors 'none'"
    )
    # HSTS is staging/production-only; local (test) responses must not pin it
    assert "Strict-Transport-Security" not in r.headers


# ---------------------------------------------------------------------------
# Per-IP rate limiting (S5-H2)
# ---------------------------------------------------------------------------


def test_rate_limit_trips_on_auth_endpoint(client: TestClient) -> None:
    """The auth tier (10/minute per IP) returns a mediator-voice 429."""
    limiter.enabled = True
    try:
        codes = []
        for _ in range(12):
            r = client.post(
                f"{settings.API_V1_STR}/auth/oauth/exchange",
                json={"code": "x" * 32},
            )
            codes.append(r.status_code)
        assert 429 in codes, codes
        throttled = [c for c in codes if c == 429]
        assert len(throttled) >= 2  # everything past the 10th
        r = client.post(
            f"{settings.API_V1_STR}/auth/oauth/exchange", json={"code": "x" * 32}
        )
        assert r.status_code == 429
        assert "breather" in r.json()["detail"]
    finally:
        limiter.enabled = False


# ---------------------------------------------------------------------------
# One-time OAuth login codes (S5-H1)
# ---------------------------------------------------------------------------


def test_login_code_expires(client: TestClient, db: Session) -> None:
    user = _make_user(db)
    raw_code = auth_service.create_login_code(db, user.id)
    # Manually expire it
    from app.models import LoginCode

    code_row = db.exec(
        select(LoginCode).where(
            LoginCode.code_hash == auth_service.hash_token(raw_code)
        )
    ).one()
    code_row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(code_row)
    db.commit()

    r = client.post(
        f"{settings.API_V1_STR}/auth/oauth/exchange", json={"code": raw_code}
    )
    assert r.status_code == 400
    assert "expired or was already used" in r.json()["detail"]


def test_login_code_is_hashed_at_rest(db: Session) -> None:
    user = _make_user(db)
    raw_code = auth_service.create_login_code(db, user.id)
    from app.models import LoginCode

    rows = db.exec(select(LoginCode).where(LoginCode.user_id == user.id)).all()
    assert rows
    assert all(row.code_hash != raw_code for row in rows)


# ---------------------------------------------------------------------------
# JWT revocation via logout (S5-H1)
# ---------------------------------------------------------------------------


def test_logout_revokes_token(client: TestClient, db: Session) -> None:
    user = _make_user(db)
    headers = token_headers_for_user(user)

    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200

    r = client.post(f"{settings.API_V1_STR}/auth/logout", headers=headers)
    assert r.status_code == 200

    # The same token is dead everywhere now
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 401

    # Logging out an already-revoked token is also a 401 (not a 500)
    r = client.post(f"{settings.API_V1_STR}/auth/logout", headers=headers)
    assert r.status_code == 401


def test_token_without_jti_rejected(client: TestClient, db: Session) -> None:
    """Pre-WS8 tokens (no jti claim) can't be revoked, so they don't
    authenticate at all."""
    user = _make_user(db)
    legacy = jwt.encode(
        {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "sub": str(user.id),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {legacy}"},
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Invite usage caps + revocation + preview (S5-M4)
# ---------------------------------------------------------------------------


def _create_group_with_invite(
    client: TestClient, headers: dict[str, str], max_uses: int
) -> tuple[dict, dict]:
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=headers,
        json={"name": f"WS8 invite test {uuid.uuid4().hex[:6]}"},
    )
    assert r.status_code == 201
    group = r.json()
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=headers,
        json={"max_uses": max_uses},
    )
    assert r.status_code == 201
    return group, r.json()["invite"]


def test_invite_usage_cap_enforced(client: TestClient, db: Session) -> None:
    owner = _make_user(db)
    owner_headers = token_headers_for_user(owner)
    group, invite = _create_group_with_invite(client, owner_headers, max_uses=1)

    joiner1 = _make_user(db)
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}/accept",
        headers=token_headers_for_user(joiner1),
    )
    assert r.status_code == 200

    joiner2 = _make_user(db)
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}/accept",
        headers=token_headers_for_user(joiner2),
    )
    assert r.status_code == 410
    assert "usage limit" in r.json()["detail"]


def test_invite_revocation(client: TestClient, db: Session) -> None:
    owner = _make_user(db)
    owner_headers = token_headers_for_user(owner)
    group, invite = _create_group_with_invite(client, owner_headers, max_uses=10)

    # Member (non-owner) cannot revoke
    joiner = _make_user(db)
    joiner_headers = token_headers_for_user(joiner)
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}/accept",
        headers=joiner_headers,
    )
    assert r.status_code == 200
    r = client.delete(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites/{invite['id']}",
        headers=joiner_headers,
    )
    assert r.status_code == 403

    # Owner revokes; the link dies immediately
    r = client.delete(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites/{invite['id']}",
        headers=owner_headers,
    )
    assert r.status_code == 200

    stranger = _make_user(db)
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}/accept",
        headers=token_headers_for_user(stranger),
    )
    assert r.status_code == 410
    assert "revoked" in r.json()["detail"]

    # Revoked invites disappear from the owner's list
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
        headers=owner_headers,
    )
    assert r.status_code == 200
    assert invite["id"] not in [i["id"] for i in r.json()["data"]]


def test_invite_preview_does_not_join(client: TestClient, db: Session) -> None:
    """GET is read-only now — prefetchers can't join groups (S5-M4)."""
    owner = _make_user(db)
    owner_headers = token_headers_for_user(owner)
    group, invite = _create_group_with_invite(client, owner_headers, max_uses=10)

    visitor = _make_user(db)
    visitor_headers = token_headers_for_user(visitor)
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{invite['token']}",
        headers=visitor_headers,
    )
    assert r.status_code == 200
    preview = r.json()
    assert preview["group_name"] == group["name"]
    assert preview["member_count"] == 1
    assert preview["already_member"] is False

    # Previewing consumed nothing and added nobody
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group['id']}/members",
        headers=owner_headers,
    )
    assert r.json()["count"] == 1
