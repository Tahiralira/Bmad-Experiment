"""WS10.2 — payment methods registry + counterparty lookup tests.

Covers:
- self-service CRUD under /users/me/payment-methods (create/list/update/delete)
- validation: unknown provider (422), blank handle (422), duplicate (409), cap (409)
- pay_url is server-computed and returned to the client
- counterparty lookup gated by SHARED group membership (403 non-member, 404
  target-not-in-group)
- payment handles are scrubbed on account soft-delete (they are PII)
"""
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.payment_providers import MAX_METHODS_PER_USER
from app.features.auth.models import PaymentMethod, UserCreate
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)

PM_URL = f"{settings.API_V1_STR}/users/me/payment-methods"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_authed_user(db: Session) -> tuple[dict[str, str], uuid.UUID]:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    return token_headers_for_user(user), user.id


def _create_group(client: TestClient, headers: dict[str, str]) -> str:
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=headers,
        json={"name": f"PM {uuid.uuid4().hex[:8]}"},
    )
    assert r.status_code == 201
    return r.json()["id"]


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


# ---------------------------------------------------------------------------
# Self-service CRUD
# ---------------------------------------------------------------------------


def test_list_empty_by_default(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    r = client.get(PM_URL, headers=headers)
    assert r.status_code == 200
    assert r.json() == {"data": [], "count": 0}


def test_create_returns_computed_pay_url(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    r = client.post(
        PM_URL, headers=headers, json={"provider": "venmo", "handle": "@alice"}
    )
    assert r.status_code == 201
    body = r.json()
    assert body["provider"] == "venmo"
    assert body["provider_name"] == "Venmo"
    assert body["handle"] == "@alice"
    assert body["pay_url"] == "https://venmo.com/u/alice"


def test_create_then_list(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    client.post(PM_URL, headers=headers, json={"provider": "paypal", "handle": "bob"})
    client.post(
        PM_URL,
        headers=headers,
        json={"provider": "iban", "handle": "GB33BUKB20201555555555", "label": "Bank"},
    )
    r = client.get(PM_URL, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    iban = next(m for m in data["data"] if m["provider"] == "iban")
    assert iban["pay_url"] is None  # copy-only
    assert iban["label"] == "Bank"


def test_custom_https_becomes_link(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    r = client.post(
        PM_URL,
        headers=headers,
        json={"provider": "custom", "handle": "https://wise.com/pay/alice"},
    )
    assert r.status_code == 201
    assert r.json()["pay_url"] == "https://wise.com/pay/alice"


def test_update_handle_recomputes_pay_url(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    created = client.post(
        PM_URL, headers=headers, json={"provider": "venmo", "handle": "@old"}
    ).json()
    r = client.put(
        f"{PM_URL}/{created['id']}", headers=headers, json={"handle": "@new"}
    )
    assert r.status_code == 200
    assert r.json()["handle"] == "@new"
    assert r.json()["pay_url"] == "https://venmo.com/u/new"


def test_delete_removes_method(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    created = client.post(
        PM_URL, headers=headers, json={"provider": "cashapp", "handle": "$x"}
    ).json()
    r = client.delete(f"{PM_URL}/{created['id']}", headers=headers)
    assert r.status_code == 200
    r = client.get(PM_URL, headers=headers)
    assert r.json()["count"] == 0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_unknown_provider_rejected(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    r = client.post(
        PM_URL, headers=headers, json={"provider": "bitcoin", "handle": "x"}
    )
    assert r.status_code == 422


def test_blank_handle_rejected(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    r = client.post(
        PM_URL, headers=headers, json={"provider": "venmo", "handle": "   "}
    )
    assert r.status_code == 422


def test_duplicate_handle_rejected(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    payload = {"provider": "venmo", "handle": "@dup"}
    assert client.post(PM_URL, headers=headers, json=payload).status_code == 201
    r = client.post(PM_URL, headers=headers, json=payload)
    assert r.status_code == 409


def test_per_user_cap_enforced(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    for i in range(MAX_METHODS_PER_USER):
        r = client.post(
            PM_URL, headers=headers, json={"provider": "custom", "handle": f"h{i}"}
        )
        assert r.status_code == 201
    r = client.post(
        PM_URL, headers=headers, json={"provider": "custom", "handle": "one-too-many"}
    )
    assert r.status_code == 409


def test_update_to_existing_handle_rejected(client: TestClient, db: Session):
    headers, _ = _make_authed_user(db)
    client.post(PM_URL, headers=headers, json={"provider": "venmo", "handle": "@a"})
    second = client.post(
        PM_URL, headers=headers, json={"provider": "venmo", "handle": "@b"}
    ).json()
    r = client.put(f"{PM_URL}/{second['id']}", headers=headers, json={"handle": "@a"})
    assert r.status_code == 409


def test_cannot_touch_another_users_method(client: TestClient, db: Session):
    owner_headers, _ = _make_authed_user(db)
    created = client.post(
        PM_URL, headers=owner_headers, json={"provider": "venmo", "handle": "@mine"}
    ).json()
    other_headers, _ = _make_authed_user(db)
    assert (
        client.put(
            f"{PM_URL}/{created['id']}", headers=other_headers, json={"handle": "@hax"}
        ).status_code
        == 404
    )
    assert (
        client.delete(f"{PM_URL}/{created['id']}", headers=other_headers).status_code
        == 404
    )


def test_requires_auth(client: TestClient):
    assert client.get(PM_URL).status_code == 401


# ---------------------------------------------------------------------------
# Counterparty lookup (surfaced at settle time)
# ---------------------------------------------------------------------------


def test_group_member_sees_counterparty_handles(client: TestClient, db: Session):
    owner_headers, _ = _make_authed_user(db)
    member_headers, member_id = _make_authed_user(db)
    group_id = _create_group(client, owner_headers)
    _join_group(client, group_id, owner_headers, member_headers)

    # The member (payee) registers a handle
    client.post(
        PM_URL, headers=member_headers, json={"provider": "paypal", "handle": "payme"}
    )

    # The owner (payer) can see it at settle time
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group_id}/members/{member_id}/payment-methods",
        headers=owner_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["data"][0]["pay_url"] == "https://paypal.me/payme"


def test_non_member_cannot_read_handles(client: TestClient, db: Session):
    owner_headers, owner_id = _make_authed_user(db)
    group_id = _create_group(client, owner_headers)
    outsider_headers, _ = _make_authed_user(db)

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group_id}/members/{owner_id}/payment-methods",
        headers=outsider_headers,
    )
    assert r.status_code == 403


def test_target_not_in_group_is_404(client: TestClient, db: Session):
    owner_headers, _ = _make_authed_user(db)
    group_id = _create_group(client, owner_headers)
    _, stranger_id = _make_authed_user(db)  # never joined

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/{group_id}/members/{stranger_id}/payment-methods",
        headers=owner_headers,
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Privacy: handles are scrubbed on account soft-delete
# ---------------------------------------------------------------------------


def test_handles_scrubbed_on_account_deletion(client: TestClient, db: Session):
    headers, user_id = _make_authed_user(db)
    client.post(PM_URL, headers=headers, json={"provider": "venmo", "handle": "@bye"})

    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200

    remaining = db.exec(
        select(PaymentMethod).where(PaymentMethod.user_id == user_id)
    ).all()
    assert remaining == []
