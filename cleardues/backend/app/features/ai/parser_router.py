"""
AI Parser Router - SSE Streaming Endpoint (WS7 — hosted-first)

POST /expenses/parse streams the parse over Server-Sent Events: word-level
commentary chunks, then one `complete` event with the structured expense.

Honest error contract (B-H8 — the old docstring advertised 400s that never
happened):
- BEFORE the stream starts, failures are real HTTP errors:
  401 unauthenticated, 403 not a group member, 422 malformed body,
  429 monthly free quota exhausted, 503 hosted AI not configured.
- AFTER streaming begins (headers already sent, always HTTP 200), failures
  arrive as `{"type": "error", "error": "..."}` events: model timeout,
  unusable model output, low confidence.
"""
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, SessionDep
from app.features.ai import parser_service
from app.features.ai.models import ExpenseParseRequest, ExpenseParseResponse, ParseStreamEvent
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

    Hosted-first (WS7): requests run on the server's Gemini key with a
    monthly free quota per user; users with a stored BYOK key use their own
    key, unmetered. Streams word-level commentary chunks via SSE, then the
    final parsed data.

    **Example request**:
    ```json
    {
        "text": "Paid 60 for lunch with the team",
        "group_id": "550e8400-e29b-41d4-a716-446655440000",
        "personality": "friendly"
    }
    ```

    **SSE events** (HTTP 200):
    - `{"type":"commentary","data":{"text":"Got "}}` — word-level chunks
    - `{"type":"complete","data":{...ExpenseParseResponse...}}`
    - `{"type":"error","error":"..."}` — mid-stream failure only

    **HTTP errors (before any streaming)**:
    - 401 not authenticated / 422 malformed body
    - 403 not a member of the group
    - 429 monthly free-parse quota exhausted
    - 503 hosted AI not configured and no BYOK key stored

    **Personality modes**: `professional`, `friendly` (default), `funny`.
    """
    # --- Pre-flight: real HTTP errors while we still can (before streaming) ---
    if not is_group_member(
        session, group_id=expense_in.group_id, user_id=current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You must be a member of this group to parse expenses.",
        )

    resolved = parser_service.resolve_api_key(current_user)
    if resolved is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "AI parsing isn't available right now. "
                "You can still add the expense manually."
            ),
        )
    api_key, is_byok = resolved

    if not is_byok and not parser_service.consume_free_parse(
        session, current_user.id
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "You've used all your free AI parses for this month — "
                "they reset next month. Manual entry is always free."
            ),
        )

    personality = expense_in.personality or parser_service.get_group_personality(
        session, expense_in.group_id
    )

    # Snapshot before commit: the generator below runs AFTER this function
    # returns, when the session dependency has torn down — touching the
    # (expired) ORM user there would raise mid-stream.
    payer_id = current_user.id

    # The one commit for this request (ARCH-001): persists the reserved quota
    # unit and any default settings row. It must happen here — once streaming
    # starts there is no router "after" to commit in.
    session.commit()

    client = parser_service.get_gemini_client(api_key)

    async def event_generator():
        try:
            parsed = await parser_service.parse_expense_text(
                text=expense_in.text, client=client
            )

            commentary = await parser_service.generate_commentary(
                original_text=expense_in.text,
                parsed_data=parsed,
                personality=personality,
                client=client,
            )

            for chunk in parser_service.chunk_commentary(commentary):
                event = ParseStreamEvent(type="commentary", data={"text": chunk})
                yield f"data: {event.model_dump_json()}\n\n"

            parsed_response = ExpenseParseResponse(
                amount=parsed["amount"],
                description=parsed["description"],
                payer_id=payer_id,
                confidence_score=parsed["confidence"],
                commentary=commentary,
            )
            event = ParseStreamEvent(
                type="complete", data=parsed_response.model_dump(mode="json")
            )
            yield f"data: {event.model_dump_json()}\n\n"

        except parser_service.AIParseError as e:
            event = ParseStreamEvent(type="error", error=e.message)
            yield f"data: {event.model_dump_json()}\n\n"
        except (TimeoutError, httpx.TimeoutException):
            event = ParseStreamEvent(
                type="error",
                error="The AI took too long to respond. Please try again.",
            )
            yield f"data: {event.model_dump_json()}\n\n"
        except Exception:
            # No str(e) to the client — model/library errors can leak
            # internals (S5-M2 pattern).
            event = ParseStreamEvent(
                type="error",
                error="An unexpected error occurred. Please try again.",
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
