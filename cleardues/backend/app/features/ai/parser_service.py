"""
AI Parser Service

Core AI-powered expense parsing logic using Google Gemini 3 API.
Provides natural language to structured expense data conversion
with personality-flavored commentary.
"""
import uuid
import json
from decimal import Decimal

from fastapi import HTTPException
from google import genai
from sqlmodel import Session, select

from app.features.ai.models import (
    AIPersonality,
    ExpenseParseResponse,
)
from app.features.groups.models import GroupSettings

# Constants
MODEL = "gemini-3-flash"

# Personality system prompts for commentary generation
PERSONALITY_PROMPTS = {
    "professional": "You are a professional financial assistant. Parse expenses accurately and provide clear, concise commentary.",
    "friendly": "You are a friendly expense tracking buddy. Parse expenses and give cheerful, helpful commentary.",
    "funny": "You are a humorous expense companion. Parse expenses accurately but add witty, lighthearted commentary.",
    "f3-pbs": "You are an unhinged roast comic. Parse expenses correctly and savage the user's spending with dark humor. No boundaries.",
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


def get_gemini_client(api_key_encrypted: str) -> genai.Client:
    """
    Create Gemini client with user's decrypted API key.

    Each user provides their own Gemini API key (stored encrypted).
    This function decrypts the key and creates a client instance.

    Args:
        api_key_encrypted: User's encrypted Gemini API key from database

    Returns:
        genai.Client: Configured Gemini API client
    """
    from app.core.security import decrypt_api_key

    api_key = decrypt_api_key(api_key_encrypted)
    return genai.Client(api_key=api_key)


def get_group_personality(session: Session, group_id: uuid.UUID) -> AIPersonality:
    """
    Get AI personality setting for a group. Default to friendly.

    If the group has no settings record, creates default settings
    with ai_personality="friendly".

    Args:
        session: Database session
        group_id: Group UUID to get personality for

    Returns:
        AIPersonality: The personality enum value for this group
    """
    settings = session.exec(
        select(GroupSettings).where(GroupSettings.group_id == group_id)
    ).first()

    if not settings:
        # Create default settings
        settings = GroupSettings(group_id=group_id, ai_personality="friendly")
        session.add(settings)
        session.commit()

    return AIPersonality(settings.ai_personality)


def generate_commentary(
    original_text: str,
    parsed_data: dict,
    personality: AIPersonality,
    client: genai.Client,
) -> str:
    """
    Generate personality-flavored commentary based on parsed expense.

    Uses the Gemini API with personality-specific system prompts
    to generate witty, friendly, professional, or roast-style commentary.

    Args:
        original_text: User's original expense description
        parsed_data: Parsed expense data (amount, description, confidence)
        personality: AI personality mode
        client: Gemini API client (reused for efficiency)

    Returns:
        str: Generated commentary text (1-2 sentences)
    """
    commentary_prompt = f"""
    Based on this expense data, generate a short (1-2 sentences) personality-driven commentary:

    Original: "{original_text}"
    Parsed: {parsed_data["description"]} for ${parsed_data["amount"]}
    Confidence: {parsed_data["confidence"]}

    Personality: {personality.value}
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=commentary_prompt,
        config={"system_instruction": PERSONALITY_PROMPTS[personality.value]},
    )

    return response.text.strip()


def parse_expense_text(
    text: str,
    personality: AIPersonality,
    current_user_id: uuid.UUID,
    api_key_encrypted: str | None,
) -> ExpenseParseResponse:
    """
    Parse natural language expense text using Gemini API.

    This is the core parsing function that:
    1. Validates user has configured their API key
    2. Calls Gemini API with personality-specific prompts
    3. Validates confidence score (must be >= 0.7)
    4. Generates personality-flavored commentary
    5. Returns structured expense data

    Args:
        text: Natural language expense description
        personality: AI personality mode
        current_user_id: Current user's UUID (defaults as payer)
        api_key_encrypted: User's encrypted Gemini API key

    Returns:
        ExpenseParseResponse with parsed data

    Raises:
        HTTPException: If parsing fails or confidence < 0.7
        HTTPException: If user has no API key configured
    """
    # 0. Validate user has API key
    if not api_key_encrypted:
        raise HTTPException(
            status_code=400,
            detail="Please add your Gemini API key in settings to use AI expense parsing. Get your free key at: https://ai.google.dev/gemini-api/docs/quickstart",
        )

    # 1. Create client with user's API key
    client = get_gemini_client(api_key_encrypted)

    # 2. Generate system prompt based on personality
    system_prompt = PERSONALITY_PROMPTS[personality.value]

    # 3. Call Gemini API for expense parsing
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            {"role": "user", "parts": [{"text": PARSING_PROMPT_TEMPLATE.format(text=text)}]}
        ],
        config={"system_instruction": system_prompt},
    )

    # 4. Parse JSON response
    try:
        parsed = json.loads(response.text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="I couldn't understand that expense. Please try rephrasing it.",
        )

    # 5. Validate confidence score
    if parsed.get("confidence", 0.0) < 0.7:
        raise HTTPException(
            status_code=400,
            detail="I couldn't quite understand that expense. Could you rephrase it? Try including the amount and a brief description.",
        )

    # 6. Generate personality-flavored commentary
    commentary = generate_commentary(text, parsed, personality, client)

    # 7. Return response
    return ExpenseParseResponse(
        amount=Decimal(str(parsed["amount"])),
        description=parsed["description"],
        payer_id=current_user_id,
        confidence_score=parsed["confidence"],
        commentary=commentary,
    )
