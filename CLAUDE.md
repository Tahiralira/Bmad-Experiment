# Project Context: ClearDues

ClearDues is an AI-powered "Agentic Mediator" PWA designed to manage and settle shared expenses with "Progressive Urgency" notifications.

## CRITICAL: Session Startup Protocol

**BMAD workflows automatically load tracking files via pre-hooks (Step 0).**

When running `/bmad:bmm:workflows:dev-story` or `/bmad:bmm:workflows:code-review`, these files are auto-loaded:

| File | Purpose | Auto-Loaded | Auto-Updated |
|------|---------|-------------|--------------|
| `session-context.md` | Project status, key learnings | Yes (Step 0) | Yes (Post-hook) |
| `sprint-status.yaml` | Epic/story progress | Yes (Step 1) | Yes (Step 9/5) |
| `solution-patterns.yaml` | Known issues and fixes | Yes (Step 0) | Yes (Post-hook) |
| `technical-debt-log.yaml` | Deferred LOW issues | Yes (Step 0) | Yes (code-review) |

**For non-BMAD work**, manually load these files first:
1. `_bmad-output/session-context.md` - Quick context
2. `_bmad-output/implementation-artifacts/sprint-status.yaml` - Current progress
3. `_bmad-output/implementation-artifacts/solution-patterns.yaml` - Debugging help

**Full setup guide:** `_bmad/bmm/docs/TRACKING-SETUP-GUIDE.md`

## 📊 Current Status

| Epic | Status | Progress |
|------|--------|----------|
| Epic 1: Auth | DONE | 6/6 |
| Epic 2: Groups & Dashboard | DONE | 4/4 |
| **Epic 2.5: UX Foundation** | **NEXT** | 0/7 |
| Epic 3: Expenses | IN-PROGRESS | 1/8 |
| Epic 4-7 | BACKLOG | 0/18 |
| Epic 8: UX Polish | BACKLOG (Post-MVP) | 0/4 |

**Next:** Epic 2.5, Story 2.5.1 - Design System Token Migration

## 🛠 Tech Stack

- **Backend**: FastAPI (Python) + SQLModel (ORM)
- **Frontend**: React + TypeScript + Vite + Redux Toolkit + TanStack Query
- **Database**: PostgreSQL
- **Real-Time**: WebSockets + Redis Pub/Sub
- **Worker**: Celery + Redis
- **Infra**: Docker + Railway (Target)

## 📐 Architectural Patterns

- **Directory Structure**: Feature-based (`/backend/app/features/{name}`, `/frontend/src/features/{name}`)
- **Naming Conventions**:
  - API/DB: `snake_case`
  - Frontend Code: `camelCase` (Components in `PascalCase`)
- **State Management**: Redux for UI state; TanStack Query for server state.
- **Communication**: Redis events named `domain.entity.action`.
- **Boundaries**: Strictly use Service Layer for DB access.

## 🚀 Commands

```bash
# Start everything
docker compose up -d

# Backend tests
docker compose exec backend pytest -v

# Frontend type/build check
cd cleardues/frontend && npm run typecheck && npm run build

# Alembic migrations
docker compose exec backend alembic upgrade head
```

## Known Issues Quick Reference

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError in Docker | `docker compose build --no-cache` |
| Connection refused localhost:5432 | Use service name `db` not `localhost` |
| Circular import error | Import inside function or use TYPE_CHECKING |
| Route not found 404 | Check TanStack Router file naming conventions |
| Data not updating after mutation | Add `queryClient.invalidateQueries` |

**Full solutions:** See `solution-patterns.yaml`

## Logging Requirements

**BMAD workflows automatically update tracking files via post-hooks.**

| Workflow | Auto-Updates |
|----------|--------------|
| `dev-story` | session-context.md, solution-patterns.yaml (if new issues solved) |
| `code-review` | session-context.md, technical-debt-log.yaml (LOW items), solution-patterns.yaml (if patterns found) |

**For non-BMAD work**, manually update when:
1. **New issue solved** -> Add to `solution-patterns.yaml` (symptoms, cause, solution, prevention)
2. **Critical learning** -> Update `session-context.md`
3. **Deferred LOW issue** -> Add to `technical-debt-log.yaml`

## Security Checklist for Story Acceptance Criteria

**Note:** Security considerations must be explicitly documented in all story acceptance criteria going forward (from Epic 1 retrospective action item, completed in Epic 4 Priority 2).

### Required Security Checks for All Stories

When creating or reviewing stories, ensure the following security items are addressed:

1. **Input Validation** ✅
   - All user inputs validated on both frontend and backend
   - Type checking for expected data types
   - Length/format validation for strings and numbers
   - Sanitization of user-provided data

2. **Authorization Checks** ✅
   - User must be member of group to perform action
   - Only expense creator can modify/confirm expense (Epic 4)
   - Only group creator/admin can manage group settings

3. **SQL Injection Prevention** ✅
   - Use parameterized queries (SQLModel/SQLAlchemy handles this)
   - Never concatenate strings into SQL queries
   - Validate user IDs before database operations

4. **XSS Protection** ✅
   - Sanitize all user-provided content before rendering
   - Use framework-provided escaping for dynamic content
   - Validate and restrict allowed HTML/markdown

5. **Rate Limiting (if applicable)** ⚠️
   - Document if story requires rate limiting
   - Implement per-endpoint or per-user rate limits
   - Prevent abuse of API endpoints

6. **Data Privacy** ✅
   - Only expose necessary user data in API responses
   - Remove sensitive data from logs
   - Validate data before storing in database

7. **Error Message Security** ✅
   - Generic error messages in production (no internal system details)
   - Detailed errors only in development/debug mode
   - Never expose stack traces to frontend

### Applying Security Checklist

For each new story:
1. Add "### Security Considerations" section after Acceptance Criteria
2. Include relevant items from above checklist
3. Mark each item as [ ] (unchecked) and verify during implementation
4. Update to [x] when implemented and tested

### Examples

**Backend Story Security Section Example:**
```markdown
### Security Considerations

- [x] Input Validation - All API inputs validated with SQLModel models
- [x] Authorization - `get_current_user_id` dependency ensures user is authenticated
- [x] SQL Injection - SQLModel/SQLAlchemy prevents injection automatically
- [ ] Rate Limiting - Not applicable for this endpoint
```

**Frontend Story Security Section Example:**
```markdown
### Security Considerations

- [x] Input Validation - Zod schemas validate all form inputs
- [x] XSS Protection - React and shadcn/ui components escape content by default
- [ ] Rate Limiting - Not applicable for this component
```

## Minimum Viable Story (MVS) Standard

**Note:** From Epic 2 retrospective - core functionality was being deferred as "enhancement." This standard prevents incomplete stories from being marked "done."

### MVS Checklist (All Required for Story Completion)

A story is NOT "done" unless ALL of the following are met:

#### Functional Requirements
1. ✅ **All Acceptance Criteria Met** - Every AC must be verified and passing
2. ✅ **All Tasks Complete** - Every task in story file must have [x] marked

#### Quality Requirements
3. ✅ **Code Review Passed** - No CRITICAL/HIGH blockers; code review approved
4. ✅ **Tests Passing** - Tests run successfully or documented as deferred (with rationale)
5. ✅ **Edge Cases Handled** - Null handling, boundary conditions, error states
6. ✅ **Error Messages Clear** - User-friendly error messages, not technical jargon
7. ✅ **Loading States** - Proper loading indicators for async operations
8. ✅ **Accessible** - Basic WCAG compliance (keyboard nav, ARIA labels, focus management)

#### Technical Requirements
9. ✅ **Type Safety** - TypeScript/Python types are complete, no `any` without justification
10. ✅ **Code Hygiene** - No commented-out code, consistent formatting, no console.log placeholders
11. ✅ **Documentation Updated** - Any code changes reflected in relevant documentation

#### Scope Requirements
12. ✅ **Core Functionality Included** - Main story feature complete, not deferred to "future story"
13. ❌ **NO SCOPE CREEP** - Stories cannot add unrequested features
14. ✅ **No Deferred Core Items** - Deferred items must be enhancements, not core functionality

### Applying MVS Standard

When creating stories:
- Include "### Minimum Viable Story" section referencing this checklist
- For each story, verify MVS items during code review

When reviewing stories:
- Reject stories with deferred core functionality
- Ensure all MVS items are complete before approving "done"

When implementing stories:
- Dev must verify all MVS items before marking "ready for review"
- Code review must verify all MVS items before marking "done"

### MVS in Action - Example from Epic 3

**Bad Example (Story 3.4):**
- Complex split editing deferred to "future story"
- Issue: Core functionality deferred as enhancement

**Good Example (Story 3.5):**
- Equal split with MemberChips fully implemented
- All tasks marked complete
- Code review approved

## Code Review Scoping

**Note:** From Epic 2 retrospective - unclear what "must fix" vs "nice to have." This standard clarifies review boundaries.

**Status:** Completed in Epic 4 Priority 2 (documented for reference; full implementation via BMAD workflow updates to story templates recommended)

### Severity Levels

| Level | Definition | Blocks | Example | Tracking |
|--------|------------|--------|---------|----------|
| **CRITICAL** | Security vulnerabilities, data loss risks, blocking bugs | Yes (story completion) | Fix before merge |
| **HIGH** | Performance issues, bad practices, significant bugs | Yes (next epic) | Fix before next epic |
| **MEDIUM** | Affects user experience but not blocking | No | Log to technical-debt-log.yaml |
| **LOW** | Polish, optimizations, style improvements | No | Optional improvements |

### Code Review Scope

**Code Review Focus:**
- Review acceptance criteria violations (CRITICAL)
- Review CRITICAL and HIGH severity issues only
- MEDIUM issues tracked but not blocking completion
- LOW issues noted as suggestions only

**Code Review Must NOT Review:**
- Code style (unless it affects maintainability)
- Variable naming (unless it causes bugs)
- Minor optimizations
- Personal preferences

### Review Decision Making

**For Each Issue Found:**

1. **Is it a CRITICAL bug?**
   - Security vulnerability? → CRITICAL
   - Data corruption risk? → CRITICAL
   - Could crash system? → CRITICAL
   - Breaks user flow completely? → CRITICAL

2. **Is it a HIGH severity issue?**
   - Significant performance problem? → HIGH
   - Anti-pattern that causes maintenance burden? → HIGH
   - Repeated code duplication? → HIGH
   - Breaking architectural rule? → HIGH

3. **Is it a MEDIUM issue?**
   - Affects UX but workaround exists? → MEDIUM
   - Missing error handling for edge case? → MEDIUM
   - Unclear error message? → MEDIUM
   - Inconsistent validation? → MEDIUM

4. **Is it a LOW issue?**
   - Minor optimization opportunity? → LOW
   - Style preference? → LOW
   - Cosmetic improvements? → LOW
   - Code formatting suggestion? → LOW

**Action Based on Severity:**

- **CRITICAL:** Mark story "in-progress" and require fix before "review"
- **HIGH:** Note as blocker for next epic, can complete story with fix in next epic
- **MEDIUM:** Add to technical-debt-log.yaml with story ID, can continue
- **LOW:** Mention in review comments, optional to address

### Examples

**CRITICAL Issue Example:**
```
CRITICAL-001: SQL Injection Vulnerability
Severity: CRITICAL
Action: Mark story in-progress, must fix before review completion
```

**HIGH Issue Example:**
```
HIGH-001: N+1 Query Problem
Severity: HIGH
Action: Note as blocker, fix in next epic or create follow-up story
```

**MEDIUM Issue Example:**
```
MEDIUM-001: Missing Error State for Loading
Severity: MEDIUM
Action: Add to technical-debt-log.yaml, story can complete
```

**LOW Issue Example:**
```
LOW-001: Variable Naming Convention Suggestion
Severity: LOW
Action: Noted in review, optional to address later
```

## Known Issues

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError in Docker | `docker compose build --no-cache` |
| Connection refused localhost:5432 | Use service name `db` not `localhost` |
| Circular import error | Import inside function or use TYPE_CHECKING |
| Route not found 404 | Check TanStack Router file naming conventions |
| Data not updating after mutation | Add `queryClient.invalidateQueries` |

**Full solutions:** See `solution-patterns.yaml`

## References

### Planning
- [PRD](./_bmad-output/planning-artifacts/prd.md)
- [Architecture](./_bmad-output/planning-artifacts/architecture.md)
- [Epics](./_bmad-output/planning-artifacts/epics.md)
- [UX Design Specification](./_bmad-output/planning-artifacts/ux-design-specification.md)
- [Design Artifact Plan](./_bmad-output/planning-artifacts/design-artifact-plan.md)

### Tracking (Auto-managed by BMAD)
- [Sprint Status](./_bmad-output/implementation-artifacts/sprint-status.yaml)
- [Solution Patterns](./_bmad-output/implementation-artifacts/solution-patterns.yaml)
- [Technical Debt](./_bmad-output/implementation-artifacts/technical-debt-log.yaml)
- [Session Context](./_bmad-output/session-context.md)

### Guides
- [BMAD Usage Guide](./_bmad/bmm/docs/BMAD-USAGE-GUIDE.md) - Complete workflow guide from planning to deployment
- [Tracking Setup Guide](./_bmad/bmm/docs/TRACKING-SETUP-GUIDE.md) - Pre/post hooks and tracking files documentation
