"""
AI Parsing Tests (rewritten in WS7 — the real AI path)

Covers:
- SSE endpoint with REAL group membership and a full payload assertion on the
  `complete` event (the assertion whose absence hid B-C1 for months)
- hosted-first key resolution (user BYOK key, else server key, else 503)
- monthly free-parse quota (429 when exhausted; BYOK exempt; period rollover)
- honest error contract: pre-stream HTTP errors vs mid-stream error events
- BYOK endpoints PUT/DELETE /users/me/api-key (encrypted at rest)
- group ai_personality write path, capped at funny (UX-H5)
- ENCRYPTION_KEY-derived Fernet key (B-C5)
"""
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.security import decrypt_api_key, encrypt_api_key, get_encryption_key
from app.features.ai import parser_service
from app.features.ai.models import AIPersonality, AIUsage
from app.features.auth.models import User, UserCreate
from app.features.groups.models import ExpenseGroup, GroupSettings
from tests.utils.utils import (
    random_email,
    random_lower_string,
    token_headers_for_user,
)

PARSE_JSON = '{"amount": 60.0, "description": "Lunch", "confidence": 0.95}'
COMMENTARY = "Got it! Lunch for 60."


# ---------------------------------------------------------------------------
# Helpers (same shape as test_settle_up.py)
# ---------------------------------------------------------------------------


def _make_authed_user(
    client: TestClient, db: Session
) -> tuple[dict[str, str], uuid.UUID, str]:
    """Create a fresh user with a directly-minted JWT (WS8: no password
    login endpoint exists); returns (headers, user_id, email)."""
    email = random_email()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=random_lower_string())
    )
    return (token_headers_for_user(user), user.id, email)


def _create_group(client: TestClient, headers: dict[str, str], name: str) -> dict:
    r = client.post(
        f"{settings.API_V1_STR}/expense-groups/", headers=headers, json={"name": name}
    )
    assert r.status_code == 201
    return r.json()


def _create_group_row(db: Session) -> uuid.UUID:
    """Bare group row for service-level tests (group_settings FK needs it)."""
    user = db.exec(select(User)).first()
    group = ExpenseGroup(
        name=f"AI Test Group {uuid.uuid4().hex[:6]}", created_by=user.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group.id


def _mock_gemini_client(
    parse_json: str = PARSE_JSON, commentary: str = COMMENTARY
) -> Mock:
    """A genai.Client double: first interactions.create parses, second is
    commentary. The Interactions API exposes the result as .output_text."""
    client = Mock()
    client.aio.interactions.create = AsyncMock(
        side_effect=[Mock(output_text=parse_json), Mock(output_text=commentary)]
    )
    return client


def _sse_events(body: str) -> list[dict]:
    return [
        json.loads(line[len("data: "):])
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


def _parse_request(group_id: str, text: str = "Paid 60 for lunch") -> dict:
    return {"text": text, "group_id": group_id, "personality": "friendly"}


# =============================================================================
# Unit tests — parser service
# =============================================================================


class TestParserService:
    def test_parse_expense_success(self):
        client = _mock_gemini_client()
        parsed = asyncio.run(
            parser_service.parse_expense_text(text="Paid 60 for lunch", client=client)
        )
        assert str(parsed["amount"]) == "60.0"
        assert parsed["description"] == "Lunch"
        assert parsed["confidence"] == 0.95

    def test_parse_requests_structured_json_schema(self):
        # Interactions API structured output: the parse must pass the expense
        # JSON schema via response_format, and must not persist the prompt.
        client = _mock_gemini_client()
        asyncio.run(
            parser_service.parse_expense_text(text="Paid 60 for lunch", client=client)
        )
        kwargs = client.aio.interactions.create.call_args.kwargs
        assert kwargs["response_format"] == [
            {
                "type": "text",
                "mime_type": "application/json",
                "schema": parser_service.EXPENSE_SCHEMA,
            }
        ]
        assert kwargs["store"] is False

    def test_parse_tolerates_json_code_fence(self):
        client = _mock_gemini_client(parse_json=f"```json\n{PARSE_JSON}\n```")
        parsed = asyncio.run(
            parser_service.parse_expense_text(text="Paid 60 for lunch", client=client)
        )
        assert parsed["description"] == "Lunch"

    def test_parse_low_confidence_raises(self):
        client = _mock_gemini_client(
            parse_json='{"amount": 60.0, "description": "Lunch", "confidence": 0.5}'
        )
        with pytest.raises(parser_service.AIParseError) as exc_info:
            asyncio.run(
                parser_service.parse_expense_text(text="mumble", client=client)
            )
        assert "couldn't quite understand" in exc_info.value.message

    def test_parse_invalid_json_raises(self):
        client = _mock_gemini_client(parse_json="Not valid JSON")
        with pytest.raises(parser_service.AIParseError) as exc_info:
            asyncio.run(
                parser_service.parse_expense_text(text="gibberish", client=client)
            )
        assert "couldn't understand" in exc_info.value.message

    def test_parse_nonpositive_amount_raises(self):
        client = _mock_gemini_client(
            parse_json='{"amount": -5, "description": "Lunch", "confidence": 0.9}'
        )
        with pytest.raises(parser_service.AIParseError):
            asyncio.run(
                parser_service.parse_expense_text(text="weird", client=client)
            )

    def test_commentary_uses_personality_prompt(self):
        client = _mock_gemini_client()
        # consume the parse call so commentary is next
        parsed = asyncio.run(
            parser_service.parse_expense_text(text="Paid 60 for lunch", client=client)
        )
        commentary = asyncio.run(
            parser_service.generate_commentary(
                original_text="Paid 60 for lunch",
                parsed_data=parsed,
                personality=AIPersonality.FUNNY,
                client=client,
            )
        )
        assert commentary == COMMENTARY
        kwargs = client.aio.interactions.create.call_args.kwargs
        assert (
            kwargs["system_instruction"]
            == parser_service.PERSONALITY_PROMPTS["funny"]
        )

    def test_commentary_falls_back_when_model_returns_nothing(self):
        client = Mock()
        client.aio.interactions.create = AsyncMock(return_value=Mock(output_text=""))
        commentary = asyncio.run(
            parser_service.generate_commentary(
                original_text="Paid 60 for lunch",
                parsed_data={"amount": "60.0", "description": "Lunch", "confidence": 0.95},
                personality=AIPersonality.FRIENDLY,
                client=client,
            )
        )
        assert "Lunch" in commentary

    def test_chunk_commentary_yields_words(self):
        chunks = list(parser_service.chunk_commentary("Got it! Lunch for 60."))
        assert chunks == ["Got ", "it! ", "Lunch ", "for ", "60."]
        assert "".join(chunks) == "Got it! Lunch for 60."

    def test_roast_mode_is_gone(self):
        # UX-H5: the personality cap is a product decision, not an accident
        assert "f3-pbs" not in parser_service.PERSONALITY_PROMPTS
        assert {p.value for p in AIPersonality} == {
            "professional",
            "friendly",
            "funny",
        }


class TestKeyResolution:
    def test_byok_key_wins(self, db, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        user = db.exec(select(User)).first()
        user.gemini_api_key_encrypted = encrypt_api_key("user-own-key-1234567890")
        resolved = parser_service.resolve_api_key(user)
        assert resolved == ("user-own-key-1234567890", True)

    def test_server_key_is_default(self, db, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        user = db.exec(select(User)).first()
        user.gemini_api_key_encrypted = None
        resolved = parser_service.resolve_api_key(user)
        assert resolved == ("server-key", False)

    def test_no_key_anywhere_is_none(self, db, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        user = db.exec(select(User)).first()
        user.gemini_api_key_encrypted = None
        assert parser_service.resolve_api_key(user) is None


class TestGroupPersonality:
    def test_creates_default(self, db):
        group_id = _create_group_row(db)
        personality = parser_service.get_group_personality(db, group_id)
        row = db.exec(
            select(GroupSettings).where(GroupSettings.group_id == group_id)
        ).first()
        assert row is not None
        assert row.ai_personality == "friendly"
        assert personality == AIPersonality.FRIENDLY

    def test_uses_existing(self, db):
        group_id = _create_group_row(db)
        db.add(GroupSettings(group_id=group_id, ai_personality="funny"))
        db.commit()
        assert parser_service.get_group_personality(db, group_id) == AIPersonality.FUNNY

    def test_unknown_stored_value_falls_back_to_friendly(self, db):
        # rows written before the WS7 enum cap (e.g. "f3-pbs") must not 500
        group_id = _create_group_row(db)
        db.add(GroupSettings(group_id=group_id, ai_personality="f3-pbs"))
        db.commit()
        assert (
            parser_service.get_group_personality(db, group_id)
            == AIPersonality.FRIENDLY
        )


class TestEncryption:
    def test_api_key_encryption_decryption(self):
        original = "AIzaSyC_test_api_key_12345"
        encrypted = encrypt_api_key(original)
        assert encrypted != original
        assert decrypt_api_key(encrypted) == original

    def test_fernet_key_derivation_is_stable_and_keyed(self, monkeypatch):
        # HKDF from the dedicated ENCRYPTION_KEY (B-C5): deterministic for a
        # given secret, different for a different secret.
        monkeypatch.setattr(settings, "ENCRYPTION_KEY", "secret-a")
        key_a1 = get_encryption_key()
        key_a2 = get_encryption_key()
        monkeypatch.setattr(settings, "ENCRYPTION_KEY", "secret-b")
        key_b = get_encryption_key()
        assert key_a1 == key_a2
        assert key_a1 != key_b
        # and it is not the old truncate-pad of the secret
        import base64

        assert key_a1 != base64.urlsafe_b64encode(b"secret-a".ljust(32, b"0"))


# =============================================================================
# Unit tests — quota
# =============================================================================


class TestQuota:
    def test_consume_increments(self, db):
        user = db.exec(select(User)).first()
        assert parser_service.consume_free_parse(db, user.id) is True
        assert parser_service.consume_free_parse(db, user.id) is True
        row = db.exec(select(AIUsage).where(AIUsage.user_id == user.id)).first()
        assert row.parse_count == 2

    def test_consume_exhausted(self, db, monkeypatch):
        monkeypatch.setattr(settings, "AI_FREE_MONTHLY_PARSES", 2)
        user = db.exec(select(User)).first()
        assert parser_service.consume_free_parse(db, user.id) is True
        assert parser_service.consume_free_parse(db, user.id) is True
        assert parser_service.consume_free_parse(db, user.id) is False
        row = db.exec(select(AIUsage).where(AIUsage.user_id == user.id)).first()
        assert row.parse_count == 2  # the denied call must not increment

    def test_quota_resets_each_month(self, db, monkeypatch):
        monkeypatch.setattr(settings, "AI_FREE_MONTHLY_PARSES", 1)
        user = db.exec(select(User)).first()
        db.add(AIUsage(user_id=user.id, period="2020-01", parse_count=99))
        db.commit()
        # an exhausted PAST month must not count against the current one
        assert parser_service.consume_free_parse(db, user.id) is True


# =============================================================================
# Integration tests — the SSE endpoint
# =============================================================================


class TestParserRouter:
    def test_parse_sse_complete_payload(self, client, db, monkeypatch):
        """The B-C1 regression test: real membership, full payload assertion.

        The old test asserted only status/content-type, so an endpoint that
        denied every request for months still passed.
        """
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        headers, user_id, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "AI Parse Group")

        with patch(
            "app.features.ai.parser_service.get_gemini_client",
            return_value=_mock_gemini_client(),
        ):
            r = client.post(
                f"{settings.API_V1_STR}/expenses/parse",
                json=_parse_request(group["id"], "Paid 60 for lunch with the team"),
                headers=headers,
            )

        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]

        events = _sse_events(r.text)
        assert [e["type"] for e in events][-1] == "complete"
        assert all(e["type"] != "error" for e in events)

        commentary = "".join(
            e["data"]["text"] for e in events if e["type"] == "commentary"
        )
        assert commentary == COMMENTARY

        complete = events[-1]["data"]
        assert complete["amount"] == "60.0"  # Decimal string on the wire
        assert complete["description"] == "Lunch"
        assert complete["payer_id"] == str(user_id)
        assert complete["confidence_score"] == 0.95
        assert complete["commentary"] == COMMENTARY

    def test_parse_sandbox_no_group_succeeds(self, client, db, monkeypatch):
        """WS10.4: an organic-path sandbox parse omits group_id — it skips the
        membership gate, defaults to friendly, is metered like any hosted
        parse, and creates no group state."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        headers, user_id, _ = _make_authed_user(client, db)

        with patch(
            "app.features.ai.parser_service.get_gemini_client",
            return_value=_mock_gemini_client(),
        ):
            r = client.post(
                f"{settings.API_V1_STR}/expenses/parse",
                json={"text": "Paid 40 for pizza with the team"},
                headers=headers,
            )

        assert r.status_code == 200
        events = _sse_events(r.text)
        assert events[-1]["type"] == "complete"
        assert all(e["type"] != "error" for e in events)
        complete = events[-1]["data"]
        assert complete["amount"] == "60.0"  # from the mock parse JSON
        assert complete["payer_id"] == str(user_id)

        # Metered like any hosted parse — a sandbox call still costs money.
        usage = db.exec(select(AIUsage).where(AIUsage.user_id == user_id)).first()
        assert usage is not None and usage.parse_count == 1

    def test_parse_sandbox_is_metered_429_when_exhausted(
        self, client, db, monkeypatch
    ):
        """The sandbox is a real model call — an exhausted quota 429s it too."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        monkeypatch.setattr(settings, "AI_FREE_MONTHLY_PARSES", 0)
        headers, _, _ = _make_authed_user(client, db)

        r = client.post(
            f"{settings.API_V1_STR}/expenses/parse",
            json={"text": "Paid 40 for pizza"},
            headers=headers,
        )
        assert r.status_code == 429
        assert "free AI parses" in r.json()["detail"]

    def test_parse_non_member_is_403(self, client, db, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        owner_headers, _, _ = _make_authed_user(client, db)
        outsider_headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, owner_headers, "Members Only")

        r = client.post(
            f"{settings.API_V1_STR}/expenses/parse",
            json=_parse_request(group["id"]),
            headers=outsider_headers,
        )
        assert r.status_code == 403
        assert "member of this group" in r.json()["detail"]

    def test_parse_no_key_anywhere_is_503(self, client, db, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "No AI Configured")

        r = client.post(
            f"{settings.API_V1_STR}/expenses/parse",
            json=_parse_request(group["id"]),
            headers=headers,
        )
        assert r.status_code == 503
        assert "manually" in r.json()["detail"]

    def test_parse_quota_exhausted_is_429(self, client, db, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        monkeypatch.setattr(settings, "AI_FREE_MONTHLY_PARSES", 0)
        headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "Quota Group")

        r = client.post(
            f"{settings.API_V1_STR}/expenses/parse",
            json=_parse_request(group["id"]),
            headers=headers,
        )
        assert r.status_code == 429
        assert "free AI parses" in r.json()["detail"]

    def test_parse_increments_usage(self, client, db, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        headers, user_id, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "Metered Group")

        with patch(
            "app.features.ai.parser_service.get_gemini_client",
            return_value=_mock_gemini_client(),
        ):
            r = client.post(
                f"{settings.API_V1_STR}/expenses/parse",
                json=_parse_request(group["id"]),
                headers=headers,
            )
        assert r.status_code == 200

        row = db.exec(select(AIUsage).where(AIUsage.user_id == user_id)).first()
        assert row is not None
        assert row.parse_count == 1

    def test_parse_byok_bypasses_quota_and_uses_user_key(
        self, client, db, monkeypatch
    ):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        monkeypatch.setattr(settings, "AI_FREE_MONTHLY_PARSES", 0)  # hosted closed
        headers, user_id, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "BYOK Group")

        user = db.get(User, user_id)
        user.gemini_api_key_encrypted = encrypt_api_key("byok-user-key-1234567890")
        db.add(user)
        db.commit()

        with patch(
            "app.features.ai.parser_service.get_gemini_client",
            return_value=_mock_gemini_client(),
        ) as get_client:
            r = client.post(
                f"{settings.API_V1_STR}/expenses/parse",
                json=_parse_request(group["id"]),
                headers=headers,
            )

        assert r.status_code == 200
        assert _sse_events(r.text)[-1]["type"] == "complete"
        get_client.assert_called_once_with("byok-user-key-1234567890")
        # BYOK must not touch the meter
        assert (
            db.exec(select(AIUsage).where(AIUsage.user_id == user_id)).first() is None
        )

    def test_parse_low_confidence_streams_error_event(
        self, client, db, monkeypatch
    ):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "Low Confidence Group")

        low_conf = '{"amount": 60.0, "description": "Lunch", "confidence": 0.4}'
        with patch(
            "app.features.ai.parser_service.get_gemini_client",
            return_value=_mock_gemini_client(parse_json=low_conf),
        ):
            r = client.post(
                f"{settings.API_V1_STR}/expenses/parse",
                json=_parse_request(group["id"], "asdfghjkl"),
                headers=headers,
            )

        assert r.status_code == 200  # headers already sent — honest contract
        events = _sse_events(r.text)
        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert "couldn't quite understand" in events[0]["error"]

    def test_parse_timeout_streams_timeout_error(self, client, db, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "Timeout Group")

        slow_client = Mock()
        slow_client.aio.interactions.create = AsyncMock(
            side_effect=httpx.ReadTimeout("upstream too slow")
        )
        with patch(
            "app.features.ai.parser_service.get_gemini_client",
            return_value=slow_client,
        ):
            r = client.post(
                f"{settings.API_V1_STR}/expenses/parse",
                json=_parse_request(group["id"]),
                headers=headers,
            )

        events = _sse_events(r.text)
        assert events[0]["type"] == "error"
        assert "took too long" in events[0]["error"]

    def test_parse_model_crash_streams_generic_error(
        self, client, db, monkeypatch
    ):
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-key")
        headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "Crash Group")

        broken_client = Mock()
        broken_client.aio.interactions.create = AsyncMock(
            side_effect=RuntimeError("secret internal detail")
        )
        with patch(
            "app.features.ai.parser_service.get_gemini_client",
            return_value=broken_client,
        ):
            r = client.post(
                f"{settings.API_V1_STR}/expenses/parse",
                json=_parse_request(group["id"]),
                headers=headers,
            )

        events = _sse_events(r.text)
        assert events[0]["type"] == "error"
        assert "unexpected error" in events[0]["error"]
        assert "secret internal detail" not in r.text  # no leakage (S5-M2)

    def test_parse_unauthenticated_is_401(self, client, db):
        r = client.post(
            f"{settings.API_V1_STR}/expenses/parse",
            json=_parse_request(str(uuid.uuid4())),
        )
        assert r.status_code == 401


# =============================================================================
# Integration tests — BYOK endpoints
# =============================================================================


class TestApiKeyEndpoints:
    def test_put_stores_encrypted(self, client, db):
        headers, user_id, _ = _make_authed_user(client, db)
        plaintext = "AIzaSy-my-very-own-gemini-key"

        r = client.put(
            f"{settings.API_V1_STR}/users/me/api-key",
            json={"api_key": plaintext},
            headers=headers,
        )
        assert r.status_code == 200

        user = db.get(User, user_id)
        db.refresh(user)
        assert user.gemini_api_key_encrypted is not None
        assert plaintext not in user.gemini_api_key_encrypted
        assert decrypt_api_key(user.gemini_api_key_encrypted) == plaintext

    def test_delete_clears_key(self, client, db):
        headers, user_id, _ = _make_authed_user(client, db)
        client.put(
            f"{settings.API_V1_STR}/users/me/api-key",
            json={"api_key": "AIzaSy-key-to-be-deleted-123"},
            headers=headers,
        )

        r = client.delete(
            f"{settings.API_V1_STR}/users/me/api-key", headers=headers
        )
        assert r.status_code == 200

        user = db.get(User, user_id)
        db.refresh(user)
        assert user.gemini_api_key_encrypted is None

    def test_put_rejects_implausibly_short_key(self, client, db):
        headers, _, _ = _make_authed_user(client, db)
        r = client.put(
            f"{settings.API_V1_STR}/users/me/api-key",
            json={"api_key": "short"},
            headers=headers,
        )
        assert r.status_code == 422


# =============================================================================
# Integration tests — group ai_personality write path (capped at funny)
# =============================================================================


class TestGroupPersonalitySettings:
    def test_owner_sets_personality(self, client, db):
        headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "Tone Group")

        r = client.patch(
            f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
            json={"ai_personality": "funny"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["ai_personality"] == "funny"
        # strict_mode untouched by the partial update
        assert r.json()["strict_mode"] is False

        r = client.get(
            f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
            headers=headers,
        )
        assert r.json()["ai_personality"] == "funny"

    def test_roast_mode_rejected(self, client, db):
        headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "No Roast Group")

        r = client.patch(
            f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
            json={"ai_personality": "f3-pbs"},
            headers=headers,
        )
        assert r.status_code == 422

    def test_member_cannot_set_personality(self, client, db):
        owner_headers, _, _ = _make_authed_user(client, db)
        member_headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, owner_headers, "Owner Only Tone")

        r = client.post(
            f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
            headers=owner_headers,
        )
        token = r.json()["invite"]["token"]
        r = client.post(
            f"{settings.API_V1_STR}/expense-groups/invite/{token}/accept",
            headers=member_headers,
        )
        assert r.status_code == 200

        r = client.patch(
            f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
            json={"ai_personality": "professional"},
            headers=member_headers,
        )
        assert r.status_code == 403

    def test_strict_mode_only_update_keeps_personality(self, client, db):
        headers, _, _ = _make_authed_user(client, db)
        group = _create_group(client, headers, "Partial Update Group")

        client.patch(
            f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
            json={"ai_personality": "professional"},
            headers=headers,
        )
        r = client.patch(
            f"{settings.API_V1_STR}/expense-groups/{group['id']}/settings",
            json={"strict_mode": True},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["strict_mode"] is True
        assert r.json()["ai_personality"] == "professional"
