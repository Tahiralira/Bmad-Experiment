# Story 1.3: Configure Database Models for Users

Status: done

## Story

As a **backend developer**,
I want to create the User model with required fields,
so that users can be stored in PostgreSQL with proper validation.

## Acceptance Criteria

1. **Given** SQLModel and PostgreSQL are configured
   **When** I create the User model in `backend/app/features/auth/models.py`
   **Then** the model includes: `id`, `email`, `full_name`, `is_active`, `created_at`, `updated_at`

2. **And** email field has unique constraint

3. **And** Alembic migration is created for the users table

4. **And** the migration runs successfully against the database

5. **And** the table uses snake_case naming convention

## Tasks / Subtasks

- [x] Task 1: Add timestamp fields to User model (AC: #1)
  - [x] Add `created_at: datetime` field with `default_factory=utc_now`
  - [x] Add `updated_at: datetime` field with `default_factory=utc_now`
  - [x] Ensure `updated_at` auto-updates on record modification (SQLAlchemy `onupdate`)

- [x] Task 2: Verify existing User model fields (AC: #1, #2, #5)
  - [x] Confirm `id` field exists (uuid.UUID with default_factory)
  - [x] Confirm `email` field exists with unique constraint and index
  - [x] Confirm `full_name` field exists
  - [x] Confirm `is_active` field exists with default True
  - [x] Verify snake_case table naming (table name should be `user`)

- [x] Task 3: Create Alembic migration (AC: #3)
  - [x] Generate migration: `docker compose exec backend alembic revision --autogenerate -m "add_created_at_updated_at_to_user"`
  - [x] Review generated migration for correctness
  - [x] Ensure migration adds `created_at` and `updated_at` columns

- [x] Task 4: Run migration and verify (AC: #4, #5)
  - [x] Run migration: `docker compose exec backend alembic upgrade head`
  - [x] Verify columns exist in PostgreSQL: `docker compose exec db psql -U postgres -d app -c "\d user"`
  - [x] Confirm column names are snake_case

- [x] Task 5: Run tests to ensure no regressions
  - [x] Run backend tests: `docker compose exec backend pytest`
  - [x] Verify all 55+ existing tests pass

## Dev Notes

### CRITICAL CONTEXT - User Model Already Exists

**The User model already exists** in `backend/app/features/auth/models.py` from Story 1.2.

**Current User model fields:**
- `id: uuid.UUID` - Primary key (already uses UUID, not integer)
- `email: EmailStr` - With `unique=True, index=True, max_length=255`
- `full_name: str | None` - With `max_length=255`
- `is_active: bool` - Default `True`
- `is_superuser: bool` - Default `False`
- `hashed_password: str` - For password auth
- `items: list["Item"]` - Relationship (temporary, from starter template)

**MISSING FIELDS (to be added):**
- `created_at: datetime`
- `updated_at: datetime`

### Architecture Compliance

**File Location:** `backend/app/features/auth/models.py`

**Naming Conventions (from architecture.md):**
- Database tables: `snake_case`, singular (e.g., `user`, not `users`)
- Columns: `snake_case` (e.g., `created_at`, not `createdAt`)
- Python code: `snake_case` (PEP-8)

**SQLModel Pattern:**
```python
from datetime import datetime
from sqlmodel import Field

class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
```

### Existing Migration Context

**Current Alembic migrations:**
1. `e2412789c190_initialize_models.py` - Initial models (User, Item)
2. `d98dd8ec85a3_edit_replace_id_integers_in_all_models_.py` - Changed id to UUID
3. `9c0a54914c78_add_max_length_for_string_varchar_.py` - Added max_length constraints
4. `1a31ce608336_add_cascade_delete_relationships.py` - Added cascade delete

**New migration will be #5** - Adding timestamp fields to User.

### Previous Story Intelligence (Story 1.2)

**Key Learnings:**
- Template uses `uv` for Python package management (not Poetry)
- Feature-based structure is now in place
- `app/models.py` re-exports from `features/auth/models.py` for backward compatibility
- All 55 backend tests pass after reorganization
- Docker containers work: `docker compose up`

**Code Pattern Established:**
```python
# Import from feature module directly
from app.features.auth.models import User, UserCreate, UserPublic
```

### Technical Requirements

**SQLModel + SQLAlchemy:**
- SQLModel is a thin wrapper around SQLAlchemy
- Use `sa_column_kwargs` for SQLAlchemy-specific options
- For `onupdate`, use SQLAlchemy's column-level onupdate

**Timestamp Implementation Options:**

**Option 1 - Simple (SQLModel default_factory):**
```python
created_at: datetime = Field(default_factory=datetime.utcnow)
updated_at: datetime = Field(default_factory=datetime.utcnow)
```
Note: `updated_at` won't auto-update on modifications with this approach.

**Option 2 - Auto-Update (SQLAlchemy sa_column):**
```python
from sqlalchemy import Column, DateTime
from datetime import datetime

created_at: datetime = Field(
    sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
)
updated_at: datetime = Field(
    sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
)
```

**Recommended: Option 2** for production-ready timestamp handling.

### Testing Commands

```bash
# Start containers
docker compose up -d

# Generate migration
docker compose exec backend alembic revision --autogenerate -m "add_created_at_updated_at_to_user"

# Run migration
docker compose exec backend alembic upgrade head

# Verify database schema
docker compose exec db psql -U postgres -d app -c "\d user"

# Run tests
docker compose exec backend pytest

# Check migration history
docker compose exec backend alembic history
```

### Project Structure Notes

- **Model Location:** `backend/app/features/auth/models.py` (NOT `backend/app/models.py`)
- **Migration Location:** `backend/app/alembic/versions/`
- **Backward Compatibility:** `backend/app/models.py` re-exports from feature module

### Potential Issues

1. **Existing data:** If database has existing User records without timestamps, migration needs to handle this:
   ```python
   # In migration, set default value for existing rows
   op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))
   op.execute("UPDATE user SET created_at = NOW() WHERE created_at IS NULL")
   op.alter_column('user', 'created_at', nullable=False)
   ```

2. **Test fixtures:** Existing tests may need updating if they create Users without timestamps.

3. **Item model:** Still exists temporarily - ignore for this story (will be cleaned up later).

### References

- [Source: architecture.md - Naming Patterns](../_bmad-output/planning-artifacts/architecture.md#naming-patterns)
- [Source: architecture.md - Data Architecture](../_bmad-output/planning-artifacts/architecture.md#data-architecture)
- [Source: epics.md - Story 1.3](../_bmad-output/planning-artifacts/epics.md#story-13-configure-database-models-for-users)
- [Source: Story 1.2 - Previous Story](./1-2-reorganize-to-feature-based-architecture.md)
- [Existing Code: features/auth/models.py](../../backend/app/features/auth/models.py)
- [Existing Migration: e2412789c190](../../backend/app/alembic/versions/e2412789c190_initialize_models.py)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101) via Claude Code CLI

### Debug Log References

- Backend tests: 55 passed, 15 warnings in 12.73s
- Database schema verified via `\d user` - all columns present with snake_case naming
- Migration `848b1a80cc28_add_created_at_updated_at_to_user.py` applied successfully

### Completion Notes List

1. **Added timestamp fields to User model** - Used `default_factory=utc_now` with timezone-aware datetime for both fields
2. **Used SQLAlchemy's sa_column_kwargs** for `onupdate` on `updated_at` field
3. **Created Alembic migration** - Manually created due to Alembic autogenerate not detecting sa_column changes
4. **Migration handles existing data** - Uses nullable=True → UPDATE → nullable=False pattern
5. **Fixed SQLModel import in app/models.py** - Added re-export of SQLModel for alembic env.py compatibility
6. **Rebuilt Docker image** - Required because Docker was using pre-built image without feature-based structure

### Code Review Improvements (Applied automatically)

**Date:** 2026-01-07

**Issues Fixed by Code Review:**

1. **Added explicit `__tablename__ = "user"`** to User model for clarity
   - Note: Architecture.md specifies plural table names (e.g., `users`), but existing migrations use singular (`user`)
   - Kept singular for consistency with existing database schema

2. **Enhanced migration with database-level features:**
   - Added `timezone=True` for DateTime columns (prevents timezone-aware vs naive mismatch)
   - Added `server_default=sa.text("now()")` for both timestamp columns
   - Added PostgreSQL trigger function for auto-updating `updated_at` at database level
   - Now works correctly even with raw SQL updates, not just ORM

3. **Added comprehensive timestamp tests** in `tests/crud/test_user.py`:
   - `test_user_has_created_at_timestamp()` - Verifies created_at is set on creation
   - `test_user_has_updated_at_timestamp()` - Verifies updated_at is set on creation
   - `test_user_updated_at_changes_on_update()` - Verifies updated_at auto-updates on modification

4. **Updated File List** to include sprint-status.yaml (was modified but not documented)

**Review Findings:** 3 High, 4 Medium, 2 Low issues - All HIGH and MEDIUM issues fixed automatically

### File List

**Modified Files:**
- `backend/app/features/auth/models.py` - Added `created_at` and `updated_at` fields with utc_now helper, explicit `__tablename__`
- `backend/app/models.py` - Added SQLModel re-export for backward compatibility
- `backend/tests/crud/test_user.py` - Added 3 tests for timestamp behavior
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Updated story status to "review"

**New Files:**
- `backend/app/alembic/versions/848b1a80cc28_add_created_at_updated_at_to_user.py` - Migration for timestamp columns with timezone support, server defaults, and auto-update trigger

## Change Log

- 2026-01-06: Story implementation complete - added timestamp fields, created migration, all 55 tests pass
- 2026-01-07: Code review complete - enhanced migration with timezone support and database trigger, added timestamp tests (3 new tests), documented architecture naming note
