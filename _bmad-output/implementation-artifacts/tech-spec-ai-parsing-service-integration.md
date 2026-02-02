---
title: 'AI Parsing Service Integration'
slug: 'ai-parsing-service-integration'
created: '2026-01-20'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.10+', 'FastAPI', 'SQLModel', 'PostgreSQL', 'Pydantic v2', 'pytest', 'google-genai SDK', 'Gemini 2.5 Flash']
files_to_modify: ['pyproject.toml', 'app/api/main.py', 'app/features/groups/models.py', 'app/features/auth/models.py', 'app/core/security.py', 'alembic/versions/*_add_group_settings.py', 'alembic/versions/*_add_user_gemini_key.py']
code_patterns: ['Feature-based architecture', 'Service layer pattern', 'UUID primary keys', 'Enum status fields', 'SessionDep/CurrentUser dependencies', 'HTTPException for errors', 'SSE streaming with FastAPI']
test_patterns: ['pytest with TestClient', 'Session-scoped fixtures', 'normal_user_token_headers fixture', 'Status code assertions', 'Response structure validation', 'DB verification']
---

# Tech-Spec: AI Parsing Service Integration

**Created:** 2026-01-20

## Overview

### Problem Statement

Users need to record expenses quickly using conversational text without manually filling forms. The current SmartInputModal (Story 3.2) captures natural language input and displays it with streaming AI commentary, but lacks the backend parsing service to extract structured expense data (amount, description, payer).

### Solution

Integrate Google Gemini 3 API for natural language expense parsing with server-sent events (SSE) streaming for real-time AI commentary. Create a separate `app/features/ai/` module following the project's feature-based architecture pattern. Add a `group_settings` table for AI personality configuration.

### Scope

**In Scope:**

1. **Backend AI Parsing Module**
   - New `app/features/ai/` feature directory with `parser_service.py` and `parser_router.py`
   - New `POST /api/v1/expenses/parse` endpoint with SSE streaming support
   - Integration with Google Gemini 3 API using the newer `google-genai` Python SDK (not the older `google-generativeai` package)

2. **Database Schema**
   - `group_settings` table with columns: `id`, `group_id`, `ai_personality`, `created_at`, `updated_at`
   - `ai_personality` enum: `professional`, `friendly`, `funny`, `f3-pbs`
   - `users` table: Add `gemini_api_key_encrypted` column (encrypted at rest, AES-256 per NFR4)
   - Alembic migrations for both schema changes

3. **AI Integration**
   - Response format: `{amount, description, payer_id, confidence_score, commentary}`
   - Commentary streamed via Server-Sent Events (SSE) for real-time display
   - 4 AI personality modes with personality-flavored system prompts
   - Error handling: return error for low confidence (< 0.7 threshold) with user-friendly message
   - Performance: Parse in under 2 seconds (NFR3 requirement)

4. **Configuration**
   - Each user provides their own Gemini API key (stored encrypted in database)
   - Add `gemini_api_key` column to `users` table (encrypted at rest per NFR4)
   - Add `google-genai` to `pyproject.toml` (newer SDK, not `google-generativeai`)
   - Model: `gemini-2.5-flash` (fast, cost-effective for parsing)
   - Make API key entry extremely easy for users (quick setup flow)

5. **Pydantic Models**
   - Request model: `ExpenseParseRequest(text: str, group_id: UUID, personality: AIPersonality)`
   - Response model: `ExpenseParseResponse(amount: Decimal, description: str, payer_id: UUID, confidence_score: float, commentary: str)`
   - SSE Event model: `ParseStreamEvent(type: str, data: dict)`

**Out of Scope:**

- Frontend integration with SmartInputModal (Story 3.4 - Manual Override of Parsed Data)
- Group settings UI for personality selection (Story 8.1 - AI Personality Selector)
- Split logic parsing (Stories 3.5-3.7 - Equal/Unequal/Percentage splits)
- Member exclusion parsing (Story 3.8 - Exclude Members)
- Expense preview card display and editing workflow (Story 3.4)
- Frontend SSE client implementation (Story 3.4)

## Context for Development

### Codebase Patterns

**Feature-Based Architecture:**
- Backend: `backend/app/features/{name}/` containing `models.py`, `service.py`, `router.py`
- Frontend: `frontend/src/features/{name}/` containing `types.ts`, `api/`, `components/`
- Naming: `snake_case` for API/DB, `camelCase` for frontend code, `PascalCase` for components

**Service Layer Pattern:**
- Service functions in `service.py` handle all database access
- Router functions in `router.py` validate permissions, then call service
- Example: `router.py` checks user is group member, then calls `service.create_expense()`

**State Management:**
- TanStack Query (React Query) for server state mutations
- Always `invalidateQueries` after mutations to refresh data
- Query keys follow pattern: `["dashboard"]`, `["expenses"]`, `["expenses", id]`

**Database:**
- SQLModel ORM (Pydantic + SQLAlchemy)
- Alembic for migrations
- UUIDs for primary keys (not integers)
- `created_at`, `updated_at` timestamps on all models

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `backend/app/features/expenses/router.py` | Reference: Router pattern, prefix="/expenses", authentication deps |
| `backend/app/features/expenses/service.py` | Reference: Service layer pattern, DB access abstraction, validation logic |
| `backend/app/features/expenses/models.py` | Reference: ExpenseCreate/ExpensePublic Pydantic models, ExpenseStatus enum |
| `backend/app/features/groups/models.py` | **MODIFY**: Add GroupSettings model with ai_personality field |
| `backend/app/api/main.py` | **MODIFY**: Include AI router (api_router.include_router) |
| `backend/app/api/deps.py` | Reference: SessionDep, CurrentUser dependencies for auth |
| `backend/app/core/config.py` | Reference: Settings pattern using pydantic-settings, .env file location |
| `backend/tests/conftest.py` | Reference: Test fixtures (client, normal_user_token_headers, db Session) |
| `backend/tests/api/routes/test_expenses.py` | Reference: Test naming, structure, status assertions, DB verification |
| `backend/pyproject.toml` | **MODIFY**: Add `google-genai>=1.0.0` and `cryptography` to dependencies |
| `alembic/versions/*_add_group_settings.py` | **CREATE**: New migration for group_settings table |
| `alembic/versions/*_add_user_gemini_key.py` | **CREATE**: New migration for users.gemini_api_key_encrypted |

### Investigation Findings

**Confirmed Architecture Patterns:**

1. **Package Management**: Uses `pyproject.toml` with `uv` (NOT `requirements.txt` as initially noted)
   - Dependencies are listed in `[project.dependencies]` section
   - Dev dependencies in `[tool.uv.dev-dependencies]`
   - Add `google-genai>=1.0.0` to dependencies list

2. **Feature Module Structure**:
   - Existing: `auth/`, `expenses/`, `groups/`, `notifications/`
   - **NEW**: Create `ai/` module following same pattern
   - Each feature has: `__init__.py`, `models.py`, `service.py`, `router.py`

3. **Database Model Conventions**:
   - All tables use UUID primary keys with `Field(default_factory=uuid.uuid4)`
   - Timestamps use `default_factory=utc_now` helper from `auth.models`
   - Foreign keys use `Field(foreign_key="table.id")` with snake_case table names
   - Relationships defined with `Relationship()` and `back_populates`
   - Enum classes inherit from `str` and `PyEnum` (e.g., `ExpenseStatus(str, PyEnum)`)

4. **Router Pattern**:
   - Router prefix: `router = APIRouter(prefix="/expenses", tags=["expenses"])`
   - Import and include in `app/api/main.py`: `api_router.include_router(expenses_router)`
   - Path functions use `SessionDep` and `CurrentUser` type annotations for dependency injection
   - Error responses use `HTTPException(status_code=..., detail="...")`

5. **Service Layer Pattern**:
   - Service functions take `Session` as first parameter
   - Service functions handle all DB operations (no DB access in router)
   - Router validates business rules (permissions, existence checks), service handles CRUD
   - Example from expenses: `is_user_group_member()` helper in service

6. **Test Patterns**:
   - Tests located in `tests/api/routes/test_{feature}.py` mirroring router structure
   - Fixtures in `tests/conftest.py`: `client`, `normal_user_token_headers`, `second_user_token_headers`, `db`
   - Test naming: `test_{action}_{condition}_{expected_result}` (e.g., `test_create_expense_as_group_member`)
   - Assertions: `assert response.status_code == 200`, `assert content["field"] == expected`
   - Database verification using `select(Model).where(Model.id == id)`
   - Clean up in conftest respects foreign key constraints (delete in correct order)

7. **Environment Variables**:
   - Config uses `pydantic-settings.BaseSettings`
   - `.env` file location: `../.env` (one level above backend dir)
   - Auto-detects `GEMINI_API_KEY` from environment (no code change needed)
   - Settings accessed via `settings` singleton from `app.core.config`

**Clean Slate Confirmation:**

No existing AI/NLP integration found in the codebase. This is a greenfield implementation with no legacy constraints. The new `app/features/ai/` module will establish the pattern for future AI features.

### Technical Decisions

**1. AI Provider: Google Gemini 3**
- **Selected Model**: `gemini-2.5-flash` (fast, cost-effective, good for parsing)
- **SDK**: `google-genai` (the newer official SDK, NOT `google-generativeai`)
- **Installation**: `pip install -q -U google-genai`
- **API Key**: Set as environment variable `GEMINI_API_KEY` (auto-detected by SDK)
- **Documentation**: [Gemini API Quickstart](https://ai.google.dev/gemini-api/docs/quickstart) (updated 2025-12-18)

**2. Streaming Approach: Server-Sent Events (SSE)**
- Backend streams AI commentary chunks via SSE endpoint
- Format: `data: {"type": "commentary", "text": "..."}\n\n`
- Final message: `data: {"type": "complete", "parsed_data": {...}}\n\n`
- Frontend SSE client integration deferred to Story 3.4

**3. Architecture: Separate AI Feature Module**
- Create `backend/app/features/ai/` module (not add to expenses/)
- Follows feature-based architecture pattern
- Reusable for future AI features (e.g., smart notifications, suggested settlements)
- Module contains: `__init__.py`, `parser_service.py`, `parser_router.py`, `models.py`

**4. Personality Storage: group_settings Table**
- New table `group_settings` with one-to-one relationship to `expense_groups`
- Columns: `id`, `group_id` (FK), `ai_personality` (enum), `created_at`, `updated_at`
- Allows per-group AI personality configuration
- Extensible for future group settings (e.g., settlement cycle, notification preferences)

**5. Error Handling: Low Confidence Threshold**
- If AI confidence score < 0.7, return error response
- Error message: "I couldn't quite understand that expense. Could you rephrase it? Try including the amount and a brief description."
- Status code: 400 Bad Request with error detail
- Frontend can show error and prompt user to rephrase or switch to manual form

**6. System Prompts for Personalities**
- 4 personality modes: `professional`, `friendly`, `funny`, `f3-pbs`
- Each personality has a custom system prompt injected into Gemini API call
- Prompts guide the tone and style of AI commentary (not the parsing logic)
- Parsing logic remains consistent; only commentary text changes

## Implementation Plan

### Tasks

> **IMPORTANT**: All tasks must be completed in the listed order. Do not skip or reorder tasks.

#### Task 1: Create AI Feature Module Structure

**File**: `backend/app/features/ai/__init__.py`
- Create new AI feature directory following existing pattern
- Add `__init__.py` with module docstring

#### Task 2: Create Pydantic Models for AI Parsing

**File**: `backend/app/features/ai/models.py`

Create the following Pydantic models:

1. **AIPersonality Enum**:
   ```python
   class AIPersonality(str, Enum):
       PROFESSIONAL = "professional"
       FRIENDLY = "friendly"
       FUNNY = "funny"
       F3_PBS = "f3-pbs"
   ```

2. **ExpenseParseRequest** (request body):
   ```python
   class ExpenseParseRequest(BaseModel):
       text: str = Field(..., min_length=1, max_length=500, description="Natural language expense description")
       group_id: UUID = Field(..., description="Group ID for context and personality settings")
       personality: AIPersonality = Field(default=AIPersonality.FRIENDLY, description="AI personality mode")
   ```

3. **ExpenseParseResponse** (final response):
   ```python
   class ExpenseParseResponse(BaseModel):
       amount: Decimal = Field(..., gt=0, description="Parsed expense amount")
       description: str = Field(..., min_length=1, description="Cleaned expense description")
       payer_id: UUID = Field(..., description="Payer user ID (defaults to current user)")
       confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
       commentary: str = Field(..., description="Personality-flavored AI commentary")
   ```

4. **ParseStreamEvent** (SSE event):
   ```python
   class ParseStreamEventType(str, Enum):
       COMMENTARY = "commentary"
       COMPLETE = "complete"
       ERROR = "error"

   class ParseStreamEvent(BaseModel):
       type: ParseStreamEventType
       data: dict | None = None
       error: str | None = None
   ```

#### Task 3: Create Database Migrations

**Files**:
- `backend/app/features/groups/models.py` (add GroupSettings model)
- `backend/app/features/auth/models.py` (add gemini_api_key_encrypted to User model)
- `alembic/versions/XXXX_add_group_settings.py` (new migration for group_settings)
- `alembic/versions/XXXX_add_user_gemini_key.py` (new migration for users table)

**Changes**:

1. **Add GroupSettings Model** to `backend/app/features/groups/models.py`:
   ```python
   class GroupSettings(SQLModel, table=True):
       __tablename__ = "group_settings"

       id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
       group_id: uuid.UUID = Field(foreign_key="expense_groups.id", unique=True, index=True)
       ai_personality: str = Field(default="friendly", index=True)
       created_at: datetime = Field(default_factory=datetime.utcnow)
       updated_at: datetime = Field(default_factory=datetime.utcnow)

       # Relationship
       group: "ExpenseGroup" = Relationship(back_populates="settings")
   ```

2. **Update ExpenseGroup Model** (add relationship):
   ```python
   class ExpenseGroup(SQLModel, table=True):
       # ... existing fields ...
       settings: GroupSettings | None = Relationship(back_populates="group")
   ```

3. **Create Alembic Migration for group_settings**:
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "add group settings table"
   ```
   - Review generated migration
   - Ensure `group_settings.ai_personality` has default value "friendly"
   - Apply migration: `docker compose exec backend alembic upgrade head`

4. **Add gemini_api_key_encrypted to User Model** in `backend/app/features/auth/models.py`:
   ```python
   class User(SQLModel, table=True):
       # ... existing fields ...
       gemini_api_key_encrypted: str | None = Field(
           default=None,
           max_length=512,
           description="Encrypted Gemini API key for this user (AES-256)"
       )
   ```

5. **Create Alembic Migration for users.gemini_api_key_encrypted**:
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "add user gemini api key"
   ```
   - Review generated migration
   - Ensure column is nullable (optional until user provides key)
   - Apply migration: `docker compose exec backend alembic upgrade head`

---

#### Task 4: Implement API Key Encryption Utility

**File**: `backend/app/core/security.py` (or new file if needed)
**Action**: Add encryption/decryption functions for API keys
**Notes**:
- Use `cryptography` library (Fernet symmetric encryption)
- Use `settings.SECRET_KEY` for encryption key
- Functions: `encrypt_api_key(plaintext: str) -> str`, `decrypt_api_key(encrypted: str) -> str`

**Implementation**:
```python
from cryptography.fernet import Fernet

def get_encryption_key() -> bytes:
    """Get encryption key from SECRET_KEY."""
    from app.core.config import settings
    # Use SECRET_KEY as base for encryption key
    return base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32].ljust(32, b'0'))

_fernet = Fernet(get_encryption_key())

def encrypt_api_key(plaintext: str) -> str:
    """Encrypt API key for storage."""
    return _fernet.encrypt(plaintext.encode()).decode()

def decrypt_api_key(encrypted: str) -> str:
    """Decrypt API key for use."""
    return _fernet.decrypt(encrypted.encode()).decode()
```

---

#### Task 5: Implement AI Parser Service

**File**: `backend/app/features/ai/parser_service.py`

Create the parser service with:

1. **Gemini Client Initialization** (per-user client):
   ```python
   from google import genai
   from app.core.security import decrypt_api_key

   MODEL = "gemini-2.5-flash"

   def get_gemini_client(api_key_encrypted: str) -> genai.Client:
       """Create Gemini client with user's decrypted API key."""
       api_key = decrypt_api_key(api_key_encrypted)
       return genai.Client(api_key=api_key)
   ```

**NOTE**: Client is created per-request using the current user's decrypted API key, NOT from environment. Each user must provide their own Gemini API key.

2. **Personality System Prompts**:
   ```python
   PERSONALITY_PROMPTS = {
       "professional": "You are a professional financial assistant. Parse expenses accurately and provide clear, concise commentary.",
       "friendly": "You are a friendly expense tracking buddy. Parse expenses and give cheerful, helpful commentary.",
       "funny": "You are a humorous expense companion. Parse expenses accurately but add witty, lighthearted commentary.",
       "f3-pbs": "You are an unhinged roast comic. Parse expenses correctly and savage the user's spending with dark humor. No boundaries."
   }
   ```

3. **Parsing Prompt Template**:
   ```python
   PARSING_PROMPT = """
   Extract expense information from the following text. Return ONLY valid JSON in this exact format:
   {{
       "amount": <decimal number>,
       "description": <cleaned description string>,
       "confidence": <float 0.0-1.0>
   }}

   Text: {text}
   """
   ```

4. **Main Parse Function**:
   ```python
   async def parse_expense_text(
       text: str,
       personality: AIPersonality,
       current_user_id: UUID,
       api_key_encrypted: str  # User's encrypted API key
   ) -> ExpenseParseResponse:
       """
       Parse natural language expense text using Gemini API.

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
               detail="Please add your Gemini API key in settings to use AI expense parsing."
           )

       # 1. Create client with user's API key
       client = get_gemini_client(api_key_encrypted)

       # 2. Generate system prompt based on personality
       system_prompt = PERSONALITY_PROMPTS[personality.value]

       # 3. Call Gemini API
       response = client.models.generate_content(
           model=MODEL,
           contents=[
               {"role": "user", "parts": [{"text": PARSING_PROMPT_TEMPLATE.format(text=text)}]}
           ],
           config={"system_instruction": system_prompt}
       )

       # 3. Parse JSON response
       parsed = json.loads(response.text)

       # 4. Validate confidence score
       if parsed.get("confidence", 0.0) < 0.7:
           raise HTTPException(
               status_code=400,
               detail="I couldn't quite understand that expense. Could you rephrase it? Try including the amount and a brief description."
           )

       # 5. Generate personality-flavored commentary (reuse client)
       commentary = await generate_commentary(text, parsed, personality, client)

       # 6. Return response
       return ExpenseParseResponse(
           amount=Decimal(str(parsed["amount"])),
           description=parsed["description"],
           payer_id=current_user_id,
           confidence_score=parsed["confidence"],
           commentary=commentary
       )
   ```

5. **Commentary Generation Function**:
   ```python
   async def generate_commentary(
       original_text: str,
       parsed_data: dict,
       personality: AIPersonality,
       client: genai.Client  # Pass client for efficiency
   ) -> str:
       """Generate personality-flavored commentary based on parsed expense."""

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
           config={"system_instruction": PERSONALITY_PROMPTS[personality.value]}
       )

       return response.text.strip()
   ```

6. **Helper Function**: Get group personality settings
   ```python
   def get_group_personality(session: Session, group_id: UUID) -> AIPersonality:
       """Get AI personality setting for a group. Default to friendly."""
       from app.features.groups.models import GroupSettings

       settings = session.exec(
           select(GroupSettings).where(GroupSettings.group_id == group_id)
       ).first()

       if not settings:
           # Create default settings
           settings = GroupSettings(group_id=group_id, ai_personality="friendly")
           session.add(settings)
           session.commit()

       return AIPersonality(settings.ai_personality)
   ```

#### Task 6: Create SSE Streaming Endpoint

**File**: `backend/app/features/ai/parser_router.py`

Create the router with SSE streaming endpoint:

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.deps import SessionDep, CurrentUser
from app.features.ai.models import ExpenseParseRequest, ParseStreamEvent
from app.features.ai import parser_service
import json

router = APIRouter(prefix="/expenses", tags=["ai-parsing"])

@router.post("/parse")
async def parse_expense(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_in: ExpenseParseRequest
) -> StreamingResponse:
    """
    Parse natural language expense text using AI.

    Streams commentary chunks via SSE, then sends final parsed data.

    Requires user to have Gemini API key configured in their profile.
    """

    async def event_generator():
        try:
            # 1. Check user has API key
            if not current_user.gemini_api_key_encrypted:
                event = ParseStreamEvent(
                    type="error",
                    error="Please add your Gemini API key in settings to use AI expense parsing. Get your free key at: https://ai.google.dev/gemini-api/docs/quickstart"
                )
                yield f"data: {event.model_dump_json()}\n\n"
                return

            # 2. Get group personality if not specified
            if not expense_in.personality:
                expense_in.personality = parser_service.get_group_personality(
                    session, expense_in.group_id
                )

            # 3. Generate commentary and stream it
            commentary_prompt = f"""
            Generate a short, {expense_in.personality.value} commentary for this expense text:
            "{expense_in.text}"

            Keep it to 1-2 sentences. Be {expense_in.personality.value}.
            """

            # For now: Simulate streaming (TODO: Integrate actual Gemini streaming in future story)
            # Parse expense data first
            parsed_response = await parser_service.parse_expense_text(
                text=expense_in.text,
                personality=expense_in.personality,
                current_user_id=current_user.id,
                api_key_encrypted=current_user.gemini_api_key_encrypted
            )

            # Stream character-by-character for commentary
            commentary = parsed_response.commentary
            for char in commentary:
                event = ParseStreamEvent(
                    type="commentary",
                    data={"text": char}
                )
                yield f"data: {event.model_dump_json()}\n\n"

            # 4. Send complete event
            event = ParseStreamEvent(
                type="complete",
                data=parsed_response.model_dump()
            )
            yield f"data: {event.model_dump_json()}\n\n"

        except HTTPException as e:
            # Forward HTTP exceptions as error events
            event = ParseStreamEvent(
                type="error",
                error=e.detail
            )
            yield f"data: {event.model_dump_json()}\n\n"
        except Exception as e:
            # Unexpected errors
            event = ParseStreamEvent(
                type="error",
                error="An unexpected error occurred. Please try again."
            )
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

#### Task 7: Register AI Router with Main App

**File**: `backend/app/api/main.py`

1. Import AI router:
   ```python
   from app.features.ai import parser_router
   ```

2. Include router in app:
   ```python
   api_router.include_router(parser_router.router)
   ```

---

#### Task 8: Create Unit Tests for Parser Service

**File**: `backend/tests/api/routes/test_ai_parsing.py`

Create comprehensive unit tests for AI parsing service:

1. **test_parse_expense_success**:
   - Mock Gemini API response with valid JSON and high confidence
   - Assert `ExpenseParseResponse` is returned correctly
   - Assert confidence >= 0.7 passes

2. **test_parse_expense_low_confidence_raises_400**:
   - Mock Gemini API to return confidence < 0.7
   - Assert HTTPException 400 is raised
   - Assert error message is user-friendly

3. **test_parse_expense_no_api_key_raises_400**:
   - Call with `api_key_encrypted=None`
   - Assert HTTPException 400 with "add your Gemini API key" message

4. **test_parse_expense_invalid_json_raises_400**:
   - Mock Gemini API to return invalid JSON
   - Assert HTTPException 400 with user-friendly error

5. **test_parse_expense_all_personalities**:
   - Test all 4 personality modes: professional, friendly, funny, f3-pbs
   - Assert correct system prompt is used for each
   - Mock commentary generation for each personality

6. **test_get_group_personality_creates_default**:
   - Call with group_id that has no settings
   - Assert GroupSettings is created with ai_personality="friendly"
   - Assert returned personality is FRIENDLY

7. **test_get_group_personality_uses_existing**:
   - Create GroupSettings with ai_personality="funny"
   - Call get_group_personality
   - Assert returned personality is FUNNY (not default)

8. **test_api_key_encryption_decryption**:
   - Test `encrypt_api_key()` and `decrypt_api_key()` functions
   - Assert encrypted key is different from plaintext
   - Assert decrypted key matches original

---

#### Task 9: Create Router Integration Tests

**File**: `backend/tests/api/routes/test_ai_parsing.py` (same file as service tests)

Create integration tests for the router:

1. **test_parse_expense_sse_streaming**:
   - Send POST request to `/api/v1/expenses/parse` with valid data
   - Assert response is `text/event-stream` content type
   - Parse SSE events and validate structure
   - Assert final event contains `complete` type with parsed data

2. **test_parse_expense_no_api_key_returns_error**:
   - Create user with `gemini_api_key_encrypted=None`
   - Send parsing request
   - Assert error event with "add your Gemini API key" message

3. **test_parse_expense_unauthenticated_raises_401**:
   - Test endpoint without auth token
   - Assert status code 401

4. **test_parse_expense_with_gibberish_raises_400**:
   - Mock Gemini API to return low confidence for gibberish input
   - Assert appropriate error response

---

#### Task 10: Manual Testing and Validation

1. **Start backend with Gemini API key**:
   ```bash
   docker compose down
   echo "GEMINI_API_KEY=your_api_key_here" >> backend/.env
   docker compose up --build
   ```

2. **Test endpoint with curl**:
   ```bash
   curl -N http://localhost:8000/api/v1/expenses/parse \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "text": "Paid 60 for lunch with the team",
       "group_id": "GROUP_UUID",
       "personality": "friendly"
     }'
   ```

3. **Verify**:
   - SSE events stream in real-time
   - Commentary chunks arrive incrementally
   - Final event contains parsed expense data
   - Response time < 2 seconds
   - Confidence scores are reasonable

4. **Test all personalities**:
   - Professional, Friendly, Funny, F3-PBS
   - Verify commentary tone matches personality

5. **Test error cases**:
   - Gibberish input (low confidence)
   - Missing amount
   - Very long descriptions

### Acceptance Criteria

**Given** a user submits natural language expense text via POST `/api/v1/expenses/parse`
**When** the text is sent to the AI parsing endpoint
**Then** the system:
1. Extracts `amount`, `description`, and `payer_id` from text
2. Generates personality-flavored commentary based on group settings
3. Streams commentary chunks via Server-Sent Events (SSE)
4. Returns final parsed data as JSON: `{amount, description, payer_id, confidence_score, commentary}`
5. Completes parsing in under 2 seconds (NFR3)
6. Returns 400 error with user-friendly message if confidence < 0.7

**Given** the AI service is configured with different personality modes
**When** a parsing request is made with a specific personality
**Then** the system:
1. Uses the correct system prompt for that personality
2. Generates commentary matching the personality tone (professional/friendly/funny/f3-pbs)
3. Maintains consistent parsing accuracy regardless of personality

**Given** a group has no personality settings configured
**When** a parsing request is made for that group
**Then** the system:
1. Creates default group settings with `ai_personality = "friendly"`
2. Uses "friendly" personality for parsing and commentary

**Given** the backend tests are run
**When** `pytest backend/app/features/ai/` is executed
**Then** all tests pass, including:
- Unit tests for `parse_expense_text()` function
- Unit tests for `generate_commentary()` function
- Unit tests for `get_group_personality()` function
- Integration tests for SSE streaming endpoint
- Error handling tests for low confidence scores

## Additional Context

### Dependencies

**Python Packages:**
- `google-genai>=1.0.0` - Google Gen AI SDK for Gemini API integration
- `cryptography` - For encrypting API keys at rest (AES-256, NFR4 compliance)

**User-Provided:**
- Each user provides their own Gemini API key (free at [Google AI Studio](https://ai.google.dev/gemini-api/docs/quickstart))
- API keys stored encrypted in database (`users.gemini_api_key_encrypted`)
- Error message guides users to get API key if not configured

**External APIs:**
- Google Gemini 3 API (`gemini-2.5-flash` model)
- API endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`

### Testing Strategy

**Unit Tests** (`test_parser_service.py`):
- Mock `google.genai.Client` responses using `unittest.mock`
- Test parsing logic, confidence validation, personality prompts
- Test group settings creation and retrieval
- Test error handling for invalid JSON, low confidence

**Integration Tests** (`test_parser_router.py`):
- Use TestClient from FastAPI
- Test SSE streaming endpoint returns correct content-type
- Parse SSE events and validate structure
- Test authentication and error scenarios

**Manual Testing**:
- Use curl or Postman to test SSE endpoint
- Verify real-time streaming of commentary chunks
- Test all 4 personality modes
- Measure response times to ensure < 2 seconds

### Notes

**API Key Entry UX** (Important for user experience):
- Story 3.3 does NOT include a UI for users to input their Gemini API key
- Error message will guide users: "Please add your Gemini API key in settings. Get your free key at: https://ai.google.dev/gemini-api/docs/quickstart"
- **Future story** should add a simple settings page where users can:
  1. Paste their Gemini API key (input field with "Show/Hide" toggle)
  2. Click "Test Connection" button to validate the key
  3. See success confirmation or error message
  4. Link to Gemini API documentation for help
- This makes API key entry "extremely easy" as requested

**Gemini API Documentation Sources:**
- [Gemini API Quickstart](https://ai.google.dev/gemini-api/docs/quickstart) - Official quickstart guide (last updated 2025-12-18)
- [Google Gen AI Python SDK GitHub](https://github.com/googleapis/python-genai) - Official SDK repository
- [Gemini API Reference](https://ai.google.dev/api) - Complete API documentation
- [Gemini 3 API Guide](https://www.godofprompt.ai/blog/gemini-3-api-guide) - Comprehensive usage guide

**SSE Implementation References:**
- [Gemini 3.0 Pro SSE Streaming Response and Cross-Region Latency Optimization](https://www.cnblogs.com/llm-api/p/19429126/) - SSE streaming implementation guide
- [SSE (Server-Sent Events) Python Tutorial](https://blog.csdn.net/Bruce__taotao/article/details/148278142) - Python SSE parsing examples

**Key Implementation Notes:**
- Use the NEWER `google-genai` SDK, NOT the older `google-generativeai` package
- Model: `gemini-2.5-flash` (fast, cost-effective for parsing tasks)
- SDK auto-detects `GEMINI_API_KEY` environment variable
- SSE format: `data: {json}\n\n` with proper double newlines
- Disable nginx buffering: `X-Accel-Buffering: no` header
- F3-PBS personality should include warning about dark humor in system prompt

**Performance Considerations:**
- Target: Parse in under 2 seconds (NFR3 requirement)
- Use async/await for non-blocking Gemini API calls
- Consider caching common expense patterns (future enhancement)
- Monitor API usage and implement rate limiting if needed (NFR5)

**Future Enhancements (Out of Scope for this story):**
- Split logic parsing (equal/unequal/percentage splits) - Stories 3.5-3.7
- Member exclusion parsing - Story 3.8
- Frontend SSE client integration - Story 3.4
- Group settings UI - Story 8.1
- Multi-currency support
- Expense categorization (food, travel, etc.)
