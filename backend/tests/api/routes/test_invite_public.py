"""WS10.3 — public invite preview tests.

The invite preview is now UNAUTHENTICATED: a logged-out invitee sees
"<inviter> invited you to <group> — N members" before deciding to sign in.
`already_member` is only meaningful for an authenticated caller.
"""
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.features.auth.models import UserCreate
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)


def _make_user(db: Session, full_name: str | None = None):
    return crud.create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(),
            password=random_lower_string(),
            full_name=full_name,
        ),
    )


def _create_group_with_invite(
    client: TestClient, headers: dict[str, str]
) -> tuple[str, str]:
    g = client.post(
        f"{settings.API_V1_STR}/expense-groups/",
        headers=headers,
        json={"name": "Weekend in Porto"},
    )
    assert g.status_code == 201
    gid = g.json()["id"]
    inv = client.post(
        f"{settings.API_V1_STR}/expense-groups/{gid}/invites", headers=headers
    )
    assert inv.status_code == 201
    return gid, inv.json()["invite"]["token"]


def test_preview_is_public_and_names_the_inviter(client: TestClient, db: Session):
    owner = _make_user(db, full_name="Alex Rivera")
    owner_headers = token_headers_for_user(owner)
    _, token = _create_group_with_invite(client, owner_headers)

    # No Authorization header at all — a logged-out invitee
    r = client.get(f"{settings.API_V1_STR}/expense-groups/invite/{token}")
    assert r.status_code == 200
    body = r.json()
    assert body["group_name"] == "Weekend in Porto"
    assert body["member_count"] == 1
    assert body["inviter_name"] == "Alex Rivera"
    # Anonymous visitors are never "already a member"
    assert body["already_member"] is False


def test_authed_member_sees_already_member(client: TestClient, db: Session):
    owner = _make_user(db, full_name="Owner")
    owner_headers = token_headers_for_user(owner)
    _, token = _create_group_with_invite(client, owner_headers)

    # The owner (a member) previews with auth → already_member True
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{token}",
        headers=owner_headers,
    )
    assert r.status_code == 200
    assert r.json()["already_member"] is True


def test_authed_non_member_is_not_already_member(client: TestClient, db: Session):
    owner = _make_user(db, full_name="Owner")
    owner_headers = token_headers_for_user(owner)
    _, token = _create_group_with_invite(client, owner_headers)

    visitor_headers = token_headers_for_user(_make_user(db))
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{token}",
        headers=visitor_headers,
    )
    assert r.status_code == 200
    assert r.json()["already_member"] is False


def test_invalid_token_404_without_auth(client: TestClient, db: Session):
    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/not-a-real-token"
    )
    assert r.status_code == 404


def test_revoked_token_410_without_auth(client: TestClient, db: Session):
    owner = _make_user(db, full_name="Owner")
    owner_headers = token_headers_for_user(owner)
    gid, token = _create_group_with_invite(client, owner_headers)

    # Revoke the invite, then a logged-out visitor gets a clean 410
    invites = client.get(
        f"{settings.API_V1_STR}/expense-groups/{gid}/invites", headers=owner_headers
    ).json()["data"]
    invite_id = invites[0]["id"]
    assert (
        client.delete(
            f"{settings.API_V1_STR}/expense-groups/{gid}/invites/{invite_id}",
            headers=owner_headers,
        ).status_code
        == 200
    )

    r = client.get(f"{settings.API_V1_STR}/expense-groups/invite/{token}")
    assert r.status_code == 410


def test_bad_token_header_falls_back_to_public_view(client: TestClient, db: Session):
    """A garbage Authorization header must not 401 the public preview — it
    resolves to the anonymous view (OptionalCurrentUser never raises)."""
    owner = _make_user(db, full_name="Owner")
    owner_headers = token_headers_for_user(owner)
    _, token = _create_group_with_invite(client, owner_headers)

    r = client.get(
        f"{settings.API_V1_STR}/expense-groups/invite/{token}",
        headers={"Authorization": "Bearer garbage.token.value"},
    )
    assert r.status_code == 200
    assert r.json()["already_member"] is False
