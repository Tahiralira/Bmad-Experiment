"""
AI Parsing Feature - Pydantic Models

Defines request/response schemas for AI-powered expense parsing.
Supports 4 personality modes for commentary generation.
"""
import uuid
from decimal import Decimal
from enum import Enum as PyEnum

from pydantic import BaseModel, Field


# === Enums ===


class AIPersonality(str, PyEnum):
    """
    AI personality modes for expense commentary.

    Each personality uses a different system prompt to guide
    the tone and style of AI-generated commentary.
    """

    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    FUNNY = "funny"
    F3_PBS = "f3-pbs"  # Roast mode - dark humor


class ParseStreamEventType(str, PyEnum):
    """SSE event types for streaming responses."""

    COMMENTARY = "commentary"
    COMPLETE = "complete"
    ERROR = "error"


# === Request/Response Models ===


class ExpenseParseRequest(BaseModel):
    """
    Request body for AI expense parsing.

    User provides natural language expense description along with
    group context (for personality settings and member validation).

    If personality is not provided, the group's default personality will be used.
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language expense description",
    )
    group_id: uuid.UUID = Field(..., description="Group ID for context and personality settings")
    personality: AIPersonality | None = Field(
        default=None, description="AI personality mode (uses group default if not provided)"
    )


class ExpenseParseResponse(BaseModel):
    """
    Response from AI expense parsing.

    Contains structured expense data extracted from natural language,
    along with confidence score and personality-flavored commentary.
    """

    amount: Decimal = Field(..., gt=0, description="Parsed expense amount")
    description: str = Field(..., min_length=1, description="Cleaned expense description")
    payer_id: uuid.UUID = Field(..., description="Payer user ID (defaults to current user)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
    commentary: str = Field(..., description="Personality-flavored AI commentary")


class ParseStreamEvent(BaseModel):
    """
    SSE event for streaming responses.

    Events are streamed in real-time:
    - COMMENTARY: Character-by-character commentary chunks
    - COMPLETE: Final parsed expense data
    - ERROR: Error message (no API key, low confidence, etc.)
    """

    type: ParseStreamEventType
    data: dict | None = None
    error: str | None = None
