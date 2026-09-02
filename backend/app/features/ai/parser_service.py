"""
AI Parser Service (WS7 — hosted-first)

Natural language -> structured expense data via Google Gemini, with
personality-flavored commentary.

Key resolution order (01 §6): the user's own BYOK key if stored, else the
server's GEMINI_API_KEY. Hosted (server-key) parses are metered per user per
calendar month by consume_free_parse(); BYOK parses are unmetered.

All model calls are async (client.aio) with a hard timeout so a slow
upstream cannot stall the event loop or hold SSE connections open (B-H8).
"""
import json
import re
import uuid
from collections.abc import Iterator
from decimal import Decimal, InvalidOperation

from google import genai
from google.genai import types as genai_types
from sqlmodel import Session, select

from app.core.config import settings
from app.features.ai.models import AIPersonality, AIUsage
from app.features.auth.models import User
from app.features.groups.models import GroupSettings

# Constants
# Must be a model ID the live Gemini API actually SERVES for generateContent —
# and models.list is NOT proof: it lists models that 404 on generateContent for
# newer keys (gemini-2.5-flash-lite is "no longer available to new users"). The
# tests mock the client, so a wrong/dead ID here passes CI and only fails on the
# first real call in prod (which is how "gemini-3-flash" — never a real ID —
# shipped and broke parsing). Verified 2026-09-02 with a real generateContent
# POST: gemini-3.5-flash-lite works (current flash-lite tier); gemini-2.5-flash
# also works if the non-lite tier is wanted. Re-verify with a real POST, NOT
# models.list, before changing:
#   curl -H "x-goog-api-key: $KEY" -X POST -H "Content-Type: application/json" \
#     -d '{"contents":[{"parts":[{"text":"hi"}]}]}' \
#     https://generativelanguage.googleapis.com/v1beta/models/<ID>:generateContent
MODEL = "gemini-3.5-flash-lite"

# Personality system prompts for commentary generation.
# Capped at "funny" (UX-H5) — no roast mode; the mediator never attacks.
PERSONALITY_PROMPTS = {
    "professional": "You are a professional financial assistant. Parse expenses accurately and provide clear, concise commentary.",
    "friendly": "You are a friendly expense tracking buddy. Parse expenses and give cheerful, helpful commentary.",
    "funny": "You are a humorous expense companion. Parse expenses accurately but add witty, lighthearted commentary. Never mock the user or other people.",
}

# Prompt template for expense extraction
PARSING_PROMPT_TEMPLATE = """
Extract expense information from the following text. Return ONLY valid JSON in this exact format:
{{
    "amount": <decimal number>,
    "description": <cleaned description string>,
    "confidence": <float 0.0-1.0>
}}

Text: {text}
"""

# JSON Schema the model must conform to (Interactions API structured output via
# response_format). Enforced server-side so the parse can't come back as prose
# or malformed JSON; _extract_json still handles the rare code-fence wrapper.
EXPENSE_SCHEMA = {
    "type": "object",
    "properties": {
        "amount": {"type": "number"},
        "description": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["amount", "description", "confidence"],
}


class AIParseError(Exception):
    """
    A parse failure with a user-safe, mediator-voice message.

    Raised after SSE streaming has begun (headers already sent), so the
    router forwards `message` as an error event rather than an HTTP status.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def resolve_api_key(user: User) -> tuple[str, bool] | None:
    """
    Pick the Gemini key for this request: BYOK first, else the server key.

    Returns (api_key, is_byok), or None when neither exists (hosted AI not
    configured on this deployment and the user stored no key).
    """
    from app.core.security import decrypt_api_key

    if user.gemini_api_key_encrypted:
        return decrypt_api_key(user.gemini_api_key_encrypted), True
    if settings.GEMINI_API_KEY:
        return settings.GEMINI_API_KEY, False
    return None


def get_gemini_client(api_key: str) -> genai.Client:
    """
    Build a Gemini client with a hard per-call timeout (B-H8).

    GEMINI_BASE_URL, when set, redirects calls to a proxy or test double.
    """
    http_options = genai_types.HttpOptions(
        timeout=settings.AI_PARSE_TIMEOUT_SECONDS * 1000,  # milliseconds
    )
    if settings.GEMINI_BASE_URL:
        http_options.base_url = settings.GEMINI_BASE_URL
    return genai.Client(api_key=api_key, http_options=http_options)


def get_group_personality(session: Session, group_id: uuid.UUID) -> AIPersonality:
    """
    Get AI personality setting for a group. Default to friendly.

    Creates the default settings row if missing (flush only — the router
    commits, ARCH-001). Unknown stored values fall back to friendly rather
    than erroring: the enum shrank in WS7 when roast mode was removed.
    """
    group_settings = session.exec(
        select(GroupSettings).where(GroupSettings.group_id == group_id)
    ).first()

    if not group_settings:
        group_settings = GroupSettings(group_id=group_id, ai_personality="friendly")
        session.add(group_settings)
        session.flush()

    try:
        return AIPersonality(group_settings.ai_personality)
    except ValueError:
        return AIPersonality.FRIENDLY


def consume_free_parse(session: Session, user_id: uuid.UUID) -> bool:
    """
    Reserve one hosted parse from the user's monthly free quota.

    Locks the (user, month) counter row (FOR UPDATE — WS4/M8 discipline) so
    concurrent requests serialize instead of overshooting the limit, then
    increments it. Flushes only; the router commits BEFORE streaming starts,
    so a reserved unit persists even if the model call later fails (the unit
    is spent — model calls cost money whether or not they parse well).

    Returns False when the quota is exhausted.
    """
    from sqlalchemy.exc import IntegrityError

    from app.features.auth.models import utc_now

    period = utc_now().strftime("%Y-%m")

    def _locked_row() -> AIUsage | None:
        return session.exec(
            select(AIUsage)
            .where(AIUsage.user_id == user_id, AIUsage.period == period)
            .with_for_update()
        ).first()

    usage = _locked_row()
    if usage is None:
        usage = AIUsage(user_id=user_id, period=period, parse_count=0)
        session.add(usage)
        try:
            session.flush()
        except IntegrityError:
            # Concurrent first parse of the month created the row between our
            # select and insert (uq_ai_usage_user_period) — take theirs.
            session.rollback()
            usage = _locked_row()
            if usage is None:  # pragma: no cover - row must exist post-conflict
                return False

    if usage.parse_count >= settings.AI_FREE_MONTHLY_PARSES:
        return False

    usage.parse_count += 1
    session.add(usage)
    session.flush()
    return True


def _extract_json(raw: str) -> dict:
    """Parse the model's JSON, tolerating a ```json ... ``` fence."""
    text = raw.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    if fence:
        text = fence.group(1)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("expected a JSON object", text, 0)
    return parsed


async def parse_expense_text(text: str, client: genai.Client) -> dict:
    """
    Extract {amount, description, confidence} from natural language.

    Raises AIParseError (user-safe message) when the model output is not
    usable: unparseable JSON, invalid amount, or confidence below 0.7.
    """
    # Interactions API (google-genai >= 2.3; generateContent is legacy as of
    # 2026-06). response_format enforces the JSON shape server-side — verified
    # 2026-09-02 that the array form {type,mime_type,schema} is the one the API
    # accepts (an object, or type="json_schema", is rejected 400). store=False
    # keeps the user's expense text off Google's servers; _extract_json remains
    # the net for the rare ```json code-fence wrapper.
    interaction = await client.aio.interactions.create(
        model=MODEL,
        input=PARSING_PROMPT_TEMPLATE.format(text=text),
        response_format=[
            {"type": "text", "mime_type": "application/json", "schema": EXPENSE_SCHEMA}
        ],
        store=False,
    )

    try:
        parsed = _extract_json(interaction.output_text or "")
    except json.JSONDecodeError:
        raise AIParseError(
            "I couldn't understand that expense. Please try rephrasing it."
        )

    if parsed.get("confidence", 0.0) < 0.7:
        raise AIParseError(
            "I couldn't quite understand that expense. Could you rephrase it? "
            "Try including the amount and a brief description."
        )

    try:
        amount = Decimal(str(parsed["amount"]))
    except (KeyError, InvalidOperation):
        amount = None
    if amount is None or amount <= 0 or not str(parsed.get("description", "")).strip():
        raise AIParseError(
            "I couldn't quite understand that expense. Could you rephrase it? "
            "Try including the amount and a brief description."
        )

    return {
        "amount": amount,
        "description": str(parsed["description"]).strip(),
        "confidence": float(parsed["confidence"]),
    }


async def generate_commentary(
    original_text: str,
    parsed_data: dict,
    personality: AIPersonality,
    client: genai.Client,
) -> str:
    """
    Generate personality-flavored commentary for the parsed expense.

    Falls back to a plain restatement if the model returns nothing usable —
    commentary is garnish, never worth failing the parse over.
    """
    commentary_prompt = f"""
    Based on this expense data, generate a short (1-2 sentences) personality-driven commentary:

    Original: "{original_text}"
    Parsed: {parsed_data["description"]} for {parsed_data["amount"]}
    Confidence: {parsed_data["confidence"]}

    Personality: {personality.value}
    """

    interaction = await client.aio.interactions.create(
        model=MODEL,
        input=commentary_prompt,
        system_instruction=PERSONALITY_PROMPTS[personality.value],
        store=False,
    )

    commentary = (interaction.output_text or "").strip()
    if not commentary:
        commentary = (
            f"Got it — {parsed_data['description']} for {parsed_data['amount']}."
        )
    return commentary


def chunk_commentary(commentary: str) -> Iterator[str]:
    """
    Split commentary into word-level SSE chunks (B-H8 — the old
    one-event-per-character stream sent hundreds of events per sentence).
    """
    words = commentary.split(" ")
    for i, word in enumerate(words):
        yield word if i == len(words) - 1 else word + " "
