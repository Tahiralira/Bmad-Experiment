# Story 4.4: Immutable Audit Log for All Actions

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **system**,
I want to record every expense-related action in an immutable audit log,
so that there is a complete, transparent history of all changes.

## Acceptance Criteria

1. **Given** any expense mutation occurs (create, edit, confirm, settle)
   **When** the action is processed
   **Then** an audit log entry is created in the `audit_logs` table

2. **Given** an audit log entry is created
   **When** the entry is stored
   **Then** the log includes: `{id, expense_id, user_id, action_type, changes_json, timestamp}`

3. **Given** different types of expense actions
   **When** the action_type is recorded
   **Then** action_type values include: "created", "edited", "confirmed", "settled", "rejected"

4. **Given** an edit action occurs
   **When** the audit log entry is created
   **Then** changes_json stores before/after values for the edited fields

5. **Given** audit logs exist for an expense
   **When** they are queried
   **Then** logs are write-only (no delete/update operations allowed)
   **And** logs are indexed by expense_id for fast retrieval

### Security Considerations

- [x] Input Validation - action_type validated against enum, expense_id/user_id validated as UUID
- [x] Authorization - Audit log creation is system-triggered (internal service calls), retrieval requires group membership
- [x] SQL Injection - SQLModel/SQLAlchemy prevents injection automatically
- [x] Data Privacy - Audit logs contain only expense-related data, no sensitive user info beyond user_id
- [x] Error Message Security - Internal logging errors logged server-side, not exposed to users
- [x] Rate Limiting - Not applicable for internal logging; retrieval endpoint inherits existing auth rate limits
- [x] Immutability Enforcement - No UPDATE or DELETE endpoints/operations on audit_logs table; enforce at DB level via trigger or app-level guard

### Minimum Viable Story

- All 5 acceptance criteria met and verified
- AuditLog model created with immutable constraint
- Service-layer helper function to create audit entries from any expense mutation
- All existing expense mutation points (create, update, confirm, reject, finalize, split) create audit log entries
- Audit logs queryable by expense_id (index)
- No deferred core functionality

## Tasks / Subtasks

- [x] Task 1: Create AuditLog Model and Migration (AC: #1, #2, #3, #5)
  - [x] Create `AuditLog` model in `backend/app/features/expenses/models.py` (or new `audit.py` module)
  - [x] Define fields: `id` (UUID), `expense_id` (FK), `user_id` (FK), `action_type` (enum), `changes_json` (JSON), `timestamp`
  - [x] Create `AuditActionType` enum: "created", "edited", "confirmed", "settled", "rejected", "split_updated"
  - [x] Add index on `expense_id` for fast retrieval
  - [x] Create Alembic migration for `audit_log` table
  - [x] Add response schema `AuditLogPublic` for API responses

- [x] Task 2: Create Audit Service Layer (AC: #1, #2, #3, #4)
  - [x] Create `record_audit()` helper function in service layer
  - [x] Accept: expense_id, user_id, action_type, before_data (optional), after_data (optional)
  - [x] Serialize before/after into `changes_json` as `{"before": {...}, "after": {...}}`
  - [x] Ensure `record_audit()` is non-blocking and logs errors without failing the parent operation

- [x] Task 3: Integrate Audit Logging into Existing Mutations (AC: #1, #3, #4)
  - [x] Hook `record_audit()` into `create_expense()` — action_type: "created"
  - [x] Hook `record_audit()` into `update_expense()` — action_type: "edited", capture before/after
  - [x] Hook `record_audit()` into `confirm_expense_split()` — action_type: "confirmed"
  - [x] Hook `record_audit()` into `reject_expense_split()` — action_type: "rejected"
  - [x] Hook `record_audit()` into `finalize_expense()` — action_type: "confirmed" (expense-level)
  - [x] Hook `record_audit()` into split creation in router (`update_expense_split` endpoint) — action_type: "split_updated"

- [x] Task 4: Create Audit Log Retrieval Endpoint (AC: #5)
  - [x] Add `GET /api/v1/expenses/{expense_id}/audit-log` endpoint
  - [x] Verify user is member of the expense's group before returning logs
  - [x] Return list of `AuditLogPublic` sorted by timestamp descending
  - [x] Add endpoint for group-level: `GET /api/v1/expense-groups/{group_id}/audit-log`
  - [x] Add pagination support (limit/offset, default 50)

- [x] Task 5: Frontend Types and API (AC: #5)
  - [x] Add `AuditLog` type to `frontend/src/features/expenses/types.ts`
  - [x] Add `useExpenseAuditLog()` query hook in `expenses.ts`
  - [x] Add `useGroupAuditLog()` query hook

- [x] Task 6: Frontend Audit Log Display Component (AC: #5)
  - [x] Create `AuditLogList` component in `frontend/src/features/expenses/components/`
  - [x] Display entries chronologically with user name, action, timestamp
  - [x] Format entries: "Alex created expense 'Lunch' for Rs 60" or "Sam confirmed their share"
  - [x] Show relative timestamps ("2 hours ago") with exact date on hover
  - [x] Paginated display (load more button)

- [x] Task 7: Immutability Enforcement (AC: #5)
  - [x] Add app-level guard: `record_audit()` uses INSERT only, no update/delete functions exist
  - [x] Verify no UPDATE/DELETE routes exist for audit_logs in router
  - [ ] (Optional/Future) Add database trigger to prevent UPDATE/DELETE on audit_log table

- [x] Task 8: Backend Testing (AC: #1-#5)
  - [x] Test: Audit entry created on expense creation
  - [x] Test: Audit entry captures before/after on edit
  - [x] Test: Audit entry created on confirm and reject
  - [x] Test: Audit logs are indexed and queryable by expense_id
  - [x] Test: Non-members cannot retrieve audit logs for an expense

## Dev Notes

### CRITICAL: This Story Continues Epic 4 — Trust & Confirmation

Story 4.4 is the **fourth of 5 stories** in Epic 4 (Trust & Confirmation Workflow). This story provides the **immutable audit trail** (FR15) that Story 4.5 (Activity Feed) will display.

**Dependency Flow:**
- Story 4.1 (Creator-Only Edit Restriction) → Story 4.2 (Confirmation Workflow) → Story 4.3 (Finalize Expense) → **Story 4.4 (Audit Log)** → Story 4.5 (Activity Feed)

**Key Insight:** Audit logging is a **cross-cutting concern** — it must hook into ALL existing expense mutations, not create new business logic.

### EXISTING CODE — DO NOT REINVENT

**All expense mutations that need audit hooks:**

| Function | File | Current Location | Action Type |
|----------|------|-----------------|-------------|
| `create_expense()` | `service.py:59` | Creates Expense with status DRAFT | "created" |
| `update_expense()` | `service.py:92` | Updates expense fields | "edited" |
| `confirm_expense_split()` | `service.py:458` | Confirms a user's split | "confirmed" |
| `reject_expense_split()` | `service.py:503` | Deletes split, recalculates | "rejected" |
| `finalize_expense()` | `service.py:356` | Sets expense to CONFIRMED | "confirmed" |
| Split creation in router | `router.py:339-352` | Creates ExpenseSplit records | "split_updated" |

**ExpenseStatus enum already exists** (`models.py:14`): DRAFT, PENDING_CONFIRMATION, CONFIRMED, SETTLED

**Expense model fields** (`models.py:173`): id, group_id, amount, description, payer_id, created_by, status, confirmed_at, created_at, updated_at

**User model** in `auth/models.py` — has `full_name` field for display in audit entries

### Architecture Compliance

**File Locations (MUST FOLLOW):**
```
Backend:
├── backend/app/features/expenses/
│   ├── models.py     # ADD: AuditLog model, AuditActionType enum, AuditLogPublic schema
│   ├── service.py    # ADD: record_audit() helper, integrate into existing functions
│   └── router.py     # ADD: GET /expenses/{id}/audit-log endpoint

Frontend:
├── frontend/src/features/expenses/
│   ├── types.ts      # ADD: AuditLog type
│   ├── api/expenses.ts  # ADD: useExpenseAuditLog(), useGroupAuditLog() hooks
│   └── components/AuditLogList.tsx  # NEW: Audit log display component
```

**Naming Conventions (MANDATORY):**
- Table: `audit_log` (snake_case, singular per existing pattern — `expense`, `expense_split`)
- Enum: `AuditActionType` (PascalCase)
- Service function: `record_audit` (snake_case)
- API endpoint: `GET /api/v1/expenses/{expense_id}/audit-log` (kebab-case URL)
- Frontend type: `AuditLog` (PascalCase)
- Frontend hook: `useExpenseAuditLog` (camelCase)

### Technical Requirements

**Backend — AuditLog Model:**
```python
# backend/app/features/expenses/models.py

class AuditActionType(str, PyEnum):
    """Types of actions that can be audited."""
    CREATED = "created"
    EDITED = "edited"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    SETTLED = "settled"       # Future: Story 5.x
    SPLIT_UPDATED = "split_updated"


class AuditLog(SQLModel, table=True):
    """
    Immutable audit log for all expense-related actions.
    Write-only: No UPDATE or DELETE operations allowed.
    """
    __tablename__ = "audit_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    expense_id: uuid.UUID = Field(foreign_key="expense.id", nullable=False, index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    action_type: AuditActionType = Field(nullable=False)
    changes_json: dict | None = Field(default=None, sa_column=sa.Column(sa.JSON))
    created_at: datetime = Field(default_factory=utc_now)

    # Relationships
    expense: Expense = Relationship()
    user: User = Relationship()


class AuditLogPublic(SQLModel):
    """Response schema for audit log entries."""
    id: uuid.UUID
    expense_id: uuid.UUID
    user_id: uuid.UUID
    action_type: AuditActionType
    changes_json: dict | None
    created_at: datetime
```

**Backend — record_audit() Helper:**
```python
# backend/app/features/expenses/service.py

def record_audit(
    session: Session,
    *,
    expense_id: uuid.UUID,
    user_id: uuid.UUID,
    action_type: AuditActionType,
    before_data: dict | None = None,
    after_data: dict | None = None,
) -> None:
    """
    Create an immutable audit log entry.

    Non-blocking: logs errors but does not fail the parent operation.
    """
    import logging
    try:
        changes = None
        if before_data is not None or after_data is not None:
            changes = {"before": before_data, "after": after_data}

        audit_entry = AuditLog(
            expense_id=expense_id,
            user_id=user_id,
            action_type=action_type,
            changes_json=changes,
        )
        session.add(audit_entry)
        # NOTE: Do NOT commit here — let the parent operation's commit handle it
        # This ensures atomicity: if the parent fails, the audit entry rolls back too
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to record audit log: {e}")
```

**Backend — Integration Pattern (example for create_expense):**
```python
def create_expense(session: Session, expense_in: ExpenseCreate, current_user_id: uuid.UUID) -> Expense:
    expense = Expense(
        group_id=expense_in.group_id,
        amount=expense_in.amount,
        description=expense_in.description,
        payer_id=expense_in.payer_id or current_user_id,
        created_by=current_user_id,
        status=ExpenseStatus.DRAFT,
    )
    session.add(expense)
    session.commit()
    session.refresh(expense)

    # Audit log — after commit so expense.id exists
    record_audit(session, expense_id=expense.id, user_id=current_user_id,
                 action_type=AuditActionType.CREATED,
                 after_data={"amount": str(expense.amount), "description": expense.description})
    session.commit()

    return expense
```

**Backend — Integration Pattern (example for update_expense with before/after):**
```python
def update_expense(session: Session, expense: Expense, update_data: ExpenseUpdate) -> Expense:
    # Capture BEFORE state
    before_data = {
        "amount": str(expense.amount),
        "description": expense.description,
        "payer_id": str(expense.payer_id),
    }

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(expense, field, value)
    session.add(expense)
    session.commit()
    session.refresh(expense)

    # Capture AFTER state (only changed fields)
    after_data = {}
    for field in update_dict:
        after_data[field] = str(getattr(expense, field))

    record_audit(session, expense_id=expense.id, user_id=expense.created_by,
                 action_type=AuditActionType.EDITED,
                 before_data={k: before_data[k] for k in after_data},
                 after_data=after_data)
    session.commit()

    return expense
```

**IMPORTANT:** The `record_audit()` function does NOT commit — it adds to the session. The parent operation must commit. This ensures atomicity. For operations that already commit (like `create_expense`), call `record_audit()` after the initial commit, then commit again for the audit entry. This is acceptable because audit logging should not block the primary operation.

**Frontend — Types:**
```typescript
// frontend/src/features/expenses/types.ts

export type AuditActionType = "created" | "edited" | "confirmed" | "rejected" | "settled" | "split_updated"

export interface AuditLog {
  id: string
  expense_id: string
  user_id: string
  action_type: AuditActionType
  changes_json: { before?: Record<string, unknown>; after?: Record<string, unknown> } | null
  created_at: string
}
```

### API Contract

**New Endpoints:**

```
GET /api/v1/expenses/{expense_id}/audit-log
Authorization: Bearer <token>

Response (200):
[
  {
    "id": "uuid",
    "expense_id": "uuid",
    "user_id": "uuid",
    "action_type": "created",
    "changes_json": null,
    "created_at": "2026-04-09T12:00:00Z"
  }
]

Errors:
404: Expense not found
403: Not a member of this group
```

```
GET /api/v1/expense-groups/{group_id}/audit-log?limit=50&offset=0
Authorization: Bearer <token>

Response (200):
{
  "data": [...],
  "count": 120
}

Errors:
404: Group not found
403: Not a member of this group
```

### Audit Action Flow

| Action | Trigger Point | action_type | changes_json |
|--------|--------------|-------------|-------------|
| Expense created | `create_expense()` | "created" | `{"after": {"amount": "60.00", "description": "Lunch"}}` |
| Expense edited | `update_expense()` | "edited" | `{"before": {"description": "Lunch"}, "after": {"description": "Dinner"}}` |
| Split updated | Router split endpoint | "split_updated" | `{"after": {"type": "equal", "members": 4}}` |
| Split confirmed | `confirm_expense_split()` | "confirmed" | `null` |
| Split rejected | `reject_expense_split()` | "rejected" | `null` |
| Expense finalized | `finalize_expense()` | "confirmed" | `{"after": {"status": "confirmed"}}` |
| Expense settled | Future (Story 5.x) | "settled" | Future |

### Previous Story Intelligence

**From Story 4.3 (Finalize Expense):**
- `finalize_expense()` function exists in `service.py:356`
- `confirm_expense_split()` at `service.py:458` — triggers finalization after last split confirms
- Redis event pattern: `billing.expense.confirmed` — audit should NOT replace this, they serve different purposes
- Module-level Redis singleton pattern for connection reuse
- Use `datetime.now(timezone.utc)` NOT `datetime.utcnow()` (deprecated)
- Net balance calculation uses aggregated SQL with CASE expressions (Story 4.3 code review fix)
- Config has `REDIS_HOST` and `REDIS_PORT` settings

**From Story 4.2 (Expense Confirmation Workflow):**
- `confirm_expense_split()` and `reject_expense_split()` patterns established
- Status guard pattern: Check `expense.status` before operations
- `HTTPException(status_code=403, detail="...")` for authorization errors

**From Story 4.1 (Creator-Only Edit Restriction):**
- `created_by` field comparison pattern for authorization
- Immutable expenses after `CONFIRMED` or `SETTLED` status

**From Story 3.5-3.8 (Split Logic):**
- Split creation happens in router `update_expense_split()` (`router.py:339-352`)
- Existing splits deleted before new ones created
- `ExpenseSplit` model has `expense_id`, `user_id`, `amount_owed` fields

### Git Intelligence

**Recent Commits (Epic 4):**
```
57c3dea - feat: Complete Story 4.2 - Expense confirmation workflow
5ca13fe - feat: Complete Story 4.1 - Creator-only edit restriction
```

**Patterns Established:**
- Commit message format: `feat: Complete Story 4.4 - Immutable audit log for all actions`
- Story file committed to git
- Alembic migrations in `backend/app/alembic/versions/`

**Commit Message for This Story:**
```
feat: Complete Story 4.4 - Immutable audit log for all actions
```

### NFR Compliance

**NFR1 (In-App Latency):** Audit recording is a simple INSERT (~10ms). Retrieval indexed by `expense_id` for fast queries.

**NFR4 (Encryption):** All data encrypted at rest (PostgreSQL) and in transit (TLS).

**NFR5 (Rate Limiting):** Not applicable for internal audit recording. Retrieval inherits existing auth.

**Audit Log Growth:** `changes_json` is a JSON column. For MVP, this is acceptable. Consider partitioning or archival for production scale (future optimization, not this story).

### Project Structure Notes

**This story ADDS:**
- `AuditLog` model and `AuditActionType` enum in `models.py`
- `AuditLogPublic` response schema in `models.py`
- `record_audit()` function in `service.py`
- Two GET endpoints in `router.py` for expense-level and group-level audit logs
- `AuditLog` type in `frontend/src/features/expenses/types.ts`
- `useExpenseAuditLog()` and `useGroupAuditLog()` hooks in `frontend/src/features/expenses/api/expenses.ts`
- `AuditLogList` component in `frontend/src/features/expenses/components/AuditLogList.tsx`
- Alembic migration for `audit_log` table

**This story MODIFIES:**
- `create_expense()` in `service.py` — add `record_audit()` call
- `update_expense()` in `service.py` — add before/after capture + `record_audit()` call
- `confirm_expense_split()` in `service.py` — add `record_audit()` call
- `reject_expense_split()` in `service.py` — add `record_audit()` call
- `finalize_expense()` in `service.py` — add `record_audit()` call
- `update_expense_split()` endpoint in `router.py` — add `record_audit()` call for split changes

### References

- [Source: epics.md - Story 4.4](_bmad-output/planning-artifacts/epics.md#story-44-immutable-audit-log-for-all-actions)
- [Source: architecture.md - Cross-Cutting Concerns](_bmad-output/planning-artifacts/architecture.md#cross-cutting-concerns-identified) — "Audit Logging: Centralized, immutable record-keeping middleware"
- [Source: architecture.md - Event System](_bmad-output/planning-artifacts/architecture.md#communication-patterns) — Redis event pattern (audit logs are separate from events)
- [Source: prd.md - FR15](_bmad-output/planning-artifacts/prd.md) — "System must record an immutable 'Audit Log' for every creation, edit, confirmation, and settlement"
- [Source: models.py](backend/app/features/expenses/models.py) — Expense, ExpenseSplit models
- [Source: service.py](backend/app/features/expenses/service.py) — All mutation functions that need audit hooks
- [Source: router.py](backend/app/features/expenses/router.py) — Split creation endpoint
- [Previous Story: 4.3](_bmad-output/implementation-artifacts/4-3-finalize-expense-after-all-confirmations.md) — Finalization patterns, code review learnings
- [Previous Story: 4.2](_bmad-output/implementation-artifacts/4-2-expense-confirmation-workflow.md) — Confirmation/rejection patterns

## Dev Agent Record

### Agent Model Used

Claude (glm-5.1)

### Debug Log References

- Fixed migration fork: `f1a2b3c4d5e6` had wrong `down_revision`, causing alembic multi-head error
- Fixed corrupted function definitions in service.py from edit operations
- Fixed pre-existing bug: `update_expense_split` endpoint used `Session` instead of `SessionDep`
- Added expense status transition DRAFT → PENDING_CONFIRMATION when splits are assigned (required for confirm/reject workflow)
- Updated conftest.py cleanup to delete AuditLog records before ExpenseGroup (FK constraint)

### Completion Notes List

- ✅ AuditLog model created with AuditActionType enum and AuditLogPublic/AuditLogsPublic schemas
- ✅ record_audit() helper: non-blocking, INSERT-only, logs errors without failing parent operation
- ✅ Integrated into all 6 mutation points: create, update, confirm_split, reject_split, finalize, split_update
- ✅ Two GET endpoints: expense-level and group-level audit log retrieval with pagination
- ✅ Frontend types, API hooks (useExpenseAuditLog, useGroupAuditLog), and AuditLogList component
- ✅ Immutability enforced: no UPDATE/DELETE operations exist for audit_logs
- ✅ 7 backend tests pass, full suite (125 tests) passes with no regressions
- ✅ Frontend build succeeds with no new errors

### File List

**New Files:**
- `backend/app/alembic/versions/5e78d661700e_add_audit_log_table.py`
- `frontend/src/features/expenses/components/AuditLogList.tsx`
- `backend/tests/api/routes/test_audit_log.py`

**Modified Files:**
- `backend/app/features/expenses/models.py` — Added AuditLog model, AuditActionType enum, AuditLogPublic/AuditLogsPublic schemas (with user_name field)
- `backend/app/features/expenses/service.py` — Added record_audit(), _build_audit_log_public(), get_expense_audit_logs(), get_group_audit_logs(); integrated audit calls into create/update/confirm/reject/finalize; update_expense now accepts current_user_id
- `backend/app/features/expenses/router.py` — Added audit-log endpoint; added split_updated audit call; fixed Session→SessionDep; added DRAFT→PENDING_CONFIRMATION transition; replaced deprecated session.query() with session.exec(delete())
- `backend/app/features/groups/router.py` — Added group-level audit-log endpoint with proper AuditLogsPublic response model
- `frontend/src/features/expenses/types.ts` — Added AuditActionType, AuditLog (with user_name), AuditLogsResponse types
- `frontend/src/features/expenses/api/expenses.ts` — Added useExpenseAuditLog(), useGroupAuditLog() hooks; added audit-log query invalidation to all mutation hooks
- `frontend/src/features/expenses/components/AuditLogList.tsx` — Display user name alongside action
- `backend/tests/conftest.py` — Added AuditLog cleanup in teardown
- `backend/tests/api/routes/test_audit_log.py` — Fixed weak assertion (>= 1 → == 1)
- `backend/app/alembic/versions/f1a2b3c4d5e6_add_expense_split_unique_constraint.py` — Fixed down_revision fork
- `backend/app/alembic/versions/f2a3b4c5d6e7_add_confirmed_at_to_expense.py` — Added confirmed_at column (from Story 4.3 scope)
- `backend/app/core/config.py` — Added REDIS_HOST/REDIS_PORT settings (from Story 4.3 scope)
- `frontend/src/features/expenses/components/PendingConfirmationsList.tsx` — Minor updates for confirmed_at display

### Change Log

- 2026-04-09: Story 4.4 implementation complete - Immutable audit log for all actions
- 2026-04-09: Code review fixes applied — 4 MEDIUM + 5 LOW issues resolved:
  - MEDIUM-001: Updated File List to include all git-committed files
  - MEDIUM-002: Replaced deprecated session.query() with session.exec(delete()) in router.py
  - MEDIUM-003: Fixed group audit-log endpoint to return AuditLogsPublic response model
  - MEDIUM-004: Improved record_audit() structured logging with exc_info=True
  - LOW-001: Added user_name to AuditLogPublic schema and AuditLogList component
  - LOW-002: Added audit-log query invalidation to all mutation hooks
  - LOW-003: update_expense() now accepts current_user_id for correct edit attribution
  - LOW-004: get_group_audit_logs() uses JOIN instead of subquery
  - LOW-005: Fixed test assertion from >= 1 to == 1
