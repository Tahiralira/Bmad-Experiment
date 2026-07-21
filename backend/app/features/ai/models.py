"""
AI Parsing Feature - Models

Request/response schemas for AI-powered expense parsing plus the AIUsage
table backing the hosted free-tier quota (WS7).

Personality modes are capped at "funny" (UX-H5): the former f3-pbs roast
mode contradicted the product's emotional-neutrality constitution and was
removed before it ever had a write path.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

import sqlalchemy as sa
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, SQLModel

from app.features.auth.models import utc_now

# Timezone-aware timestamps to match the migrations (WS5/B-H9 reconcile)
_AWARE_DATETIME = sa.DateTime(timezone=True)


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


class ParseStreamEventType(str, PyEnum):
    """SSE event types for streaming responses."""

    COMMENTARY = "commentary"
    COMPLETE = "complete"
    ERROR = "error"


# === Quota table (WS7 — hosted free tier) ===


class AIUsage(SQLModel, table=True):
    """
    Per-user, per-calendar-month counter of hosted AI parses.

    One row per (user, "YYYY-MM") period; the parse endpoint locks and
    increments it before calling the model, so concurrent requests cannot
    overshoot the free quota. BYOK users never touch this table.
    """

    __tablename__ = "ai_usage"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "period", name="uq_ai_usage_user_period"),
    )

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", index=True, ondelete="CASCADE"
    )
    period: str = Field(max_length=7)  # calendar month, e.g. "2026-07"
    parse_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now, sa_type=_AWARE_DATETIME)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=_AWARE_DATETIME,
        sa_column_kwargs={"onupdate": utc_now},
    )


# === Request/Response Models ===


class ExpenseParseRequest(BaseModel):
    """
    Request body for AI expense parsing.

    User provides natural language expense description along with optional
    group context (for personality settings and member validation).

    group_id is optional (WS10.4): omit it for a SANDBOX parse on the organic
    onboarding path — the "try one expense" aha moment that happens before the
    user has created any group. A sandbox parse skips group membership, uses
    the default personality, and (like every hosted parse) still counts against
    the user's monthly free quota because it costs a real model call. It never
    persists anything — the endpoint only ever returns parsed data.

    If personality is not provided, the group's default personality will be
    used (or the friendly default for a sandbox parse).
    """

    text: str = PydanticField(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language expense description",
    )
    group_id: uuid.UUID | None = PydanticField(
        default=None,
        description=(
            "Group ID for context and personality settings. Omit for a "
            "sandbox onboarding parse (no group required)."
        ),
    )
    personality: AIPersonality | None = PydanticField(
        default=None,
        description="AI personality mode (uses group default if not provided)",
    )


class ExpenseParseResponse(BaseModel):
    """
    Response from AI expense parsing.

    Contains structured expense data extracted from natural language,
    along with confidence score and personality-flavored commentary.
    Amount serializes as a decimal string on the wire (WS4/M1).
    """

    amount: Decimal = PydanticField(..., gt=0, description="Parsed expense amount")
    description: str = PydanticField(
        ..., min_length=1, description="Cleaned expense description"
    )
    payer_id: uuid.UUID = PydanticField(
        ..., description="Payer user ID (defaults to current user)"
    )
    confidence_score: float = PydanticField(
        ..., ge=0.0, le=1.0, description="AI confidence score"
    )
    commentary: str = PydanticField(
        ..., description="Personality-flavored AI commentary"
    )


class ParseStreamEvent(BaseModel):
    """
    SSE event for streaming responses.

    Events are streamed in real-time:
    - COMMENTARY: word-level commentary chunks
    - COMPLETE: final parsed expense data
    - ERROR: mid-stream failure (model error, low confidence, bad JSON)
    """

    type: ParseStreamEventType
    data: dict | None = None
    error: str | None = None
