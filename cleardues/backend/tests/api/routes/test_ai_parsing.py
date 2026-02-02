"""
AI Parsing Service Tests

Comprehensive unit and integration tests for AI-powered expense parsing.
Tests cover service logic, router endpoints, and error handling.
"""
import uuid
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.core.security import encrypt_api_key, decrypt_api_key
from app.features.ai import parser_service
from app.features.ai.models import AIPersonality
from app.features.groups.models import GroupSettings


# =============================================================================
# Unit Tests - Parser Service
# =============================================================================


class TestParserService:
    """Unit tests for AI parser service functions."""

    def test_parse_expense_success(self, db_session):
        """Test successful expense parsing with high confidence."""
        # Mock Gemini API response with valid JSON and high confidence
        mock_response = Mock()
        mock_response.text = '{"amount": 60.0, "description": "Lunch", "confidence": 0.95}'

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("app.features.ai.parser_service.get_gemini_client", return_value=mock_client):
            result = parser_service.parse_expense_text(
                text="Paid 60 for lunch",
                personality=AIPersonality.FRIENDLY,
                current_user_id=uuid.uuid4(),
                api_key_encrypted=encrypt_api_key("test_api_key"),
            )

        # Verify parsed data
        assert result.amount == Decimal("60.0")
        assert result.description == "Lunch"
        assert result.confidence_score == 0.95
        assert result.commentary  # Commentary should be generated

    def test_parse_expense_low_confidence_raises_400(self, db_session):
        """Test that low confidence scores raise 400 error."""
        # Mock Gemini API to return low confidence
        mock_response = Mock()
        mock_response.text = '{"amount": 60.0, "description": "Lunch", "confidence": 0.5}'

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("app.features.ai.parser_service.get_gemini_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                parser_service.parse_expense_text(
                    text="Paid 60 for lunch",
                    personality=AIPersonality.FRIENDLY,
                    current_user_id=uuid.uuid4(),
                    api_key_encrypted=encrypt_api_key("test_api_key"),
                )

        assert exc_info.value.status_code == 400
        assert "couldn't quite understand" in exc_info.value.detail

    def test_parse_expense_no_api_key_raises_400(self, db_session):
        """Test that missing API key raises 400 with helpful message."""
        with pytest.raises(HTTPException) as exc_info:
            parser_service.parse_expense_text(
                text="Paid 60 for lunch",
                personality=AIPersonality.FRIENDLY,
                current_user_id=uuid.uuid4(),
                api_key_encrypted=None,
            )

        assert exc_info.value.status_code == 400
        assert "add your Gemini API key" in exc_info.value.detail

    def test_parse_expense_invalid_json_raises_400(self, db_session):
        """Test that invalid JSON from AI raises 400 error."""
        # Mock Gemini API to return invalid JSON
        mock_response = Mock()
        mock_response.text = "Not valid JSON"

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("app.features.ai.parser_service.get_gemini_client", return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                parser_service.parse_expense_text(
                    text="gibberish text",
                    personality=AIPersonality.FRIENDLY,
                    current_user_id=uuid.uuid4(),
                    api_key_encrypted=encrypt_api_key("test_api_key"),
                )

        assert exc_info.value.status_code == 400
        assert "couldn't understand" in exc_info.value.detail

    def test_parse_expense_all_personalities(self, db_session):
        """Test all 4 personality modes use correct system prompts."""
        from app.features.ai.parser_service import PERSONALITY_PROMPTS

        personalities = [
            AIPersonality.PROFESSIONAL,
            AIPersonality.FRIENDLY,
            AIPersonality.FUNNY,
            AIPersonality.F3_PBS,
        ]

        mock_response = Mock()
        mock_response.text = '{"amount": 60.0, "description": "Lunch", "confidence": 0.95}'

        for personality in personalities:
            mock_client = Mock()
            mock_client.models.generate_content.return_value = mock_response

            with patch("app.features.ai.parser_service.get_gemini_client", return_value=mock_client):
                result = parser_service.parse_expense_text(
                    text="Paid 60 for lunch",
                    personality=personality,
                    current_user_id=uuid.uuid4(),
                    api_key_encrypted=encrypt_api_key("test_api_key"),
                )

            # Verify commentary was generated (should vary by personality)
            assert result.commentary
            assert result.confidence_score == 0.95

            # Verify correct system prompt was used
            assert mock_client.models.generate_content.called
            # Get the kwargs from the second call (first call is parsing, second is commentary)
            # We need to check that system_instruction was passed
            call_args_list = mock_client.models.generate_content.call_args_list
            # At least one call should have system_instruction matching personality
            found_correct_prompt = False
            for call in call_args_list:
                if "config" in call[1] and "system_instruction" in call[1]["config"]:
                    if call[1]["config"]["system_instruction"] == PERSONALITY_PROMPTS[personality.value]:
                        found_correct_prompt = True
                        break
            assert found_correct_prompt, f"System prompt for {personality.value} not found in API calls"

    def test_get_group_personality_creates_default(self, db_session):
        """Test that missing group settings are created with default."""
        group_id = uuid.uuid4()

        personality = parser_service.get_group_personality(db_session, group_id)

        # Verify GroupSettings was created
        settings = db_session.exec(
            select(GroupSettings).where(GroupSettings.group_id == group_id)
        ).first()

        assert settings is not None
        assert settings.ai_personality == "friendly"
        assert personality == AIPersonality.FRIENDLY

    def test_get_group_personality_uses_existing(self, db_session):
        """Test that existing group settings are respected."""
        group_id = uuid.uuid4()

        # Create GroupSettings with custom personality
        settings = GroupSettings(group_id=group_id, ai_personality="funny")
        db_session.add(settings)
        db_session.commit()

        personality = parser_service.get_group_personality(db_session, group_id)

        # Assert returned personality is FUNNY (not default)
        assert personality == AIPersonality.FUNNY

    def test_api_key_encryption_decryption(self):
        """Test that encryption/decryption functions work correctly."""
        original_key = "AIzaSyC_test_api_key_12345"

        # Encrypt
        encrypted = encrypt_api_key(original_key)
        assert encrypted != original_key  # Encrypted should be different

        # Decrypt
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original_key  # Decrypted matches original


# =============================================================================
# Integration Tests - Parser Router
# =============================================================================


class TestParserRouter:
    """Integration tests for AI parsing router endpoints."""

    def test_parse_expense_sse_streaming(self, client, normal_user_token_headers, db_session):
        """Test SSE streaming endpoint returns correct content-type."""
        # Mock the parsing service to avoid actual API calls
        group_id = uuid.uuid4()

        with patch("app.features.ai.parser_service.parse_expense_text") as mock_parse:
            mock_parse.return_value = Mock(
                amount=Decimal("60.0"),
                description="Lunch with team",
                payer_id=uuid.uuid4(),
                confidence_score=0.95,
                commentary="Got it! Lunch for $60.",
            )

            response = client.post(
                "/api/v1/expenses/parse",
                json={
                    "text": "Paid 60 for lunch with the team",
                    "group_id": str(group_id),
                    "personality": "friendly",
                },
                headers=normal_user_token_headers,
            )

        # Verify SSE content type
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_parse_expense_no_api_key_returns_error(self, client, normal_user_token_headers, db_session):
        """Test that user without API key gets error event."""
        group_id = uuid.uuid4()

        # Create user with gemini_api_key_encrypted=None (default)
        response = client.post(
            "/api/v1/expenses/parse",
            json={
                "text": "Paid 60 for lunch",
                "group_id": str(group_id),
            },
            headers=normal_user_token_headers,
        )

        # Should return error event
        assert response.status_code == 200
        assert "add your Gemini API key" in response.text

    def test_parse_expense_unauthenticated_raises_401(self, client, db_session):
        """Test endpoint without auth token returns 401."""
        group_id = uuid.uuid4()

        response = client.post(
            "/api/v1/expenses/parse",
            json={
                "text": "Paid 60 for lunch",
                "group_id": str(group_id),
            },
        )

        assert response.status_code == 401

    def test_parse_expense_with_gibberish_raises_400(self, client, normal_user_token_headers, db_session):
        """Test gibberish input returns low confidence error."""
        group_id = uuid.uuid4()

        # Mock low confidence response
        with patch("app.features.ai.parser_service.parse_expense_text") as mock_parse:
            mock_parse.side_effect = HTTPException(
                status_code=400,
                detail="I couldn't quite understand that expense. Could you rephrase it?"
            )

            response = client.post(
                "/api/v1/expenses/parse",
                json={
                    "text": "asdfghjkl",
                    "group_id": str(group_id),
                },
                headers=normal_user_token_headers,
            )

        # Should return error event
        assert response.status_code == 200
        assert "couldn't quite understand" in response.text
