"""
AI Parser Router - SSE Streaming Endpoint

Provides Server-Sent Events (SSE) streaming endpoint for real-time
AI expense parsing. Streams commentary chunks character-by-character
for the "typing" effect, then sends final parsed data.
"""
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, SessionDep
from app.features.ai import parser_service
from app.features.ai.models import ExpenseParseRequest, ParseStreamEvent
from app.features.groups.service import is_group_member

router = APIRouter()

parser_router = APIRouter(prefix="/expenses", tags=["ai-parsing"])


@parser_router.post("/parse")
async def parse_expense(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_in: ExpenseParseRequest,
) -> StreamingResponse:
    """
    Parse natural language expense text using AI.

    Streams commentary chunks via SSE, then sends final parsed data.

    **Authentication**: Requires valid JWT token
    **API Key**: User must have Gemini API key configured in their profile
    **Streaming**: Response uses Server-Sent Events (SSE) format

    **Example Request**:
    ```json
    {
        "text": "Paid 60 for lunch with the team",
        "group_id": "550e8400-e29b-41d4-a716-446655440000",
        "personality": "friendly"
    }
    ```

    **Response Format** (SSE Stream):
    - Commentary events: `{"type":"commentary","data":{"text":"G"}}`
    - Complete event: `{"type":"complete","data":{...}}`
    - Error event: `{"type":"error","error":"..."}`

    **Personality Modes**:
    - `professional`: Clear, concise commentary
    - `friendly`: Cheerful, helpful tone (default)
    - `funny`: Witty, lighthearted commentary
    - `f3-pbs`: Dark humor roast mode (no boundaries)

    **Error Cases**:
    - 400: No API key configured - "Please add your Gemini API key..."
    - 400: Low confidence - "I couldn't quite understand that expense..."
    - 400: Invalid JSON - "I couldn't understand that expense..."
    """
    async def event_generator():
        try:
            # 1. Validate user is member of group
            # (WS4/M10: keyword-only helper replaces the twin whose positional
            # args were transposed here for months — review B-C1)
            if not is_group_member(
                session, group_id=expense_in.group_id, user_id=current_user.id
            ):
                event = ParseStreamEvent(
                    type="error",
                    error="You must be a member of this group to parse expenses.",
                )
                yield f"data: {event.model_dump_json()}\n\n"
                return

            # 2. Check user has API key
            if not current_user.gemini_api_key_encrypted:
                event = ParseStreamEvent(
                    type="error",
                    error="Please add your Gemini API key in settings to use AI expense parsing. Get your free key at: https://ai.google.dev/gemini-api/docs/quickstart",
                )
                yield f"data: {event.model_dump_json()}\n\n"
                return

            # 3. Get group personality if not specified
            if not expense_in.personality:
                expense_in.personality = parser_service.get_group_personality(
                    session, expense_in.group_id
                )

            # 4. Parse expense (generates commentary internally)
            parsed_response = parser_service.parse_expense_text(
                text=expense_in.text,
                personality=expense_in.personality,
                current_user_id=current_user.id,
                api_key_encrypted=current_user.gemini_api_key_encrypted,
            )

            # 5. Stream commentary character-by-character
            commentary = parsed_response.commentary
            for char in commentary:
                event = ParseStreamEvent(type="commentary", data={"text": char})
                yield f"data: {event.model_dump_json()}\n\n"

            # 6. Send complete event
            event = ParseStreamEvent(
                type="complete", data=parsed_response.model_dump()
            )
            yield f"data: {event.model_dump_json()}\n\n"

        except HTTPException as e:
            # Forward HTTP exceptions as error events
            event = ParseStreamEvent(type="error", error=e.detail)
            yield f"data: {event.model_dump_json()}\n\n"
        except Exception as e:
            # Unexpected errors
            event = ParseStreamEvent(
                type="error", error="An unexpected error occurred. Please try again."
            )
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# Include router in module router
router.include_router(parser_router)
