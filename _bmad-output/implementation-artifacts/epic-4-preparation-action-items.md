# Epic 4 Preparation Action Items
**Generated:** 2026-02-17
**Purpose:** Complete outstanding work from Epics 1, 2, 2.5, and 3 before starting Epic 4: Trust & Confirmation Workflow

---

## Overview

**Total Preparation Effort:** ~15-17 hours + 4-6 hours (testing infrastructure) = **19-23 hours**

**Status:** BLOCKED - Epic 4 cannot start until ALL action items are complete

**Critical Insight:** Compound debt accumulation across 4 consecutive epics. Every epic inherited debt from previous ones without completing any. Breaking this pattern NOW.

---

## Priority 1: FAST WINS (Start Here)

### 1. Story 3.8 Implementation Completion
**Owner:** Charlie (Dev)
**Estimate:** 2-3 hours
**Status:** PENDING

**Issue:** Story 3.8 (Exclude Members from Expense) marked "done" with 0 tasks checked. Either:
- Complete all 11 tasks in story file, OR
- Properly mark story as incomplete and defer to Epic 4

**Action Steps:**
1. Open: `_bmad-output/implementation-artifacts/stories/3-8-exclude-members-from-expense.md`
2. Review task checklist
3. **Option A:** Complete all 11 tasks and mark as done
4. **Option B:** Mark story as incomplete with clear rationale

**File:** `stories/3-8-exclude-members-from-expense.md:1-200`

---

### 2. Single Source of Truth Documentation
**Owner:** Bob (PM/SM)
**Estimate:** 30 minutes
**Status:** PENDING

**Issue:** No enforced process for `sprint-status.yaml` being the authoritative source. Story files and sprint-status drift apart.

**Action Steps:**
1. Document story status workflow in `CLAUDE.md`
2. Add rule: "sprint-status.yaml is ALWAYS the source of truth"
3. Add update checklist for story completion:
   - All ACs met
   - All tasks complete
   - Code review passed
   - Tests passing
   - sprint-status.yaml updated

**File:** `CLAUDE.md` (add new section after Sprint Status)

---

### 3. Console.log Placeholder Removal
**Owner:** Charlie (Dev)
**Estimate:** 1 hour
**Status:** PENDING

**Issue:** Epic 2.5 left console.log placeholders throughout codebase. Create technical debt on day 1.

**Action Steps:**
1. Search codebase for `console.log` patterns
2. Remove debug statements from production code
3. Keep only intentional error logging

**Command:**
```bash
# Find all console.log statements
grep -r "console.log" frontend/src --include="*.ts" --include="*.tsx"
```

---

## Priority 2: PROCESS IMPROVEMENTS

### 4. Story 3.6 Status Resolution
**Owner:** Bob (PM/SM)
**Estimate:** 30 minutes
**Status:** PENDING

**Issue:** Story 3.6 status inconsistency between story file and sprint-status.yaml.

**Action Steps:**
1. Open: `stories/3-6-split-logic-unequal-custom-amounts.md`
2. Verify actual completion state
3. Align story file status with sprint-status.yaml
4. Update sprint-status.yaml to reflect TRUE state

---

### 5. Add Security to AC Checklist
**Owner:** Bob (PM/SM)
**Estimate:** 2 hours
**Status:** PENDING

**Issue:** From Epic 1 retrospective - "Add Security to AC Checklist" never done. Epic 4 stories need security review baked in.

**Action Steps:**
1. Open: `_bmad/bmm/templates/create-story.md` (or equivalent)
2. Add Security section to story template
3. Include items like:
   - Input validation
   - SQL injection prevention
   - XSS protection
   - Authorization checks
   - Rate limiting (if applicable)

**Template File:** `_bmad/bmm/templates/create-story.md`

---

### 6. Define "Minimum Viable Story" (MVS) Standard
**Owner:** Bob (PM/SM)
**Estimate:** 2-3 hours
**Status:** PENDING

**Issue:** From Epic 2 retrospective - no clear definition of what "done" means. Stories marked done with incomplete work.

**Action Steps:**
1. Create MVS checklist in `CLAUDE.md`
2. Define minimum requirements for story completion:
   - All ACs met and tested
   - All tasks completed
   - Code review approved
   - Edge cases handled
   - Error messages clear
   - Accessible (basic WCAG compliance)
3. Reference in story template

**Output:** Add MVS section to `CLAUDE.md`

---

### 7. Clarify Code Review Scoping
**Owner:** Bob (PM/SM)
**Estimate:** 1 hour
**Status:** PENDING

**Issue:** From Epic 2 retrospective - unclear what "must fix" vs "nice to have" in code review.

**Action Steps:**
1. Document code review scope in `CLAUDE.md`
2. Define severity levels:
   - **CRITICAL:** Must fix before merge (security bugs, data loss risks)
   - **HIGH:** Should fix before next epic (performance issues, bad practices)
   - **MEDIUM:** Track in technical-debt-log.yaml
   - **LOW:** Optional improvements

**Output:** Add Code Review Scope section to `CLAUDE.md`

---

### 8. Document Docker Volume Workaround
**Owner:** Charlie (Dev)
**Estimate:** 30 minutes
**Status:** PENDING

**Issue:** From Epic 1 retrospective - docker compose file copy workaround not documented.

**Action Steps:**
1. Document the workaround in `CLAUDE.md` under Known Issues
2. Include full command and explanation

**Add to CLAUDE.md:**
```markdown
## Known Issues

### Docker Volume Permissions
**Symptom:** Permission errors accessing PostgreSQL volumes
**Solution:** Copy docker-compose file with volume workaround:
```bash
# Workaround: Copy compose file with adjusted volume permissions
cp docker-compose.yml.backup docker-compose.yml
```
**Prevention:** Document in developer onboarding
```

---

## Priority 3: DEFERRED TASK TRACKING

### 9. Create Deferred Task Tracking Standard
**Owner:** Bob (PM/SM)
**Estimate:** 1 week (ongoing process)
**Status:** PENDING

**Issue:** No standard for tracking deferred tasks during story work. Items get lost.

**Action Steps:**
1. Define format for deferred tasks in story files
2. Add section to story template: `## Deferred Tasks`
3. Include fields:
   - Task description
   - Why deferred
   - Priority
   - Estimated effort
   - Target epic/story
4. Create process for reviewing deferred tasks

**Output:** Update story template, document in `CLAUDE.md`

---

### 10. Document Story Status Workflow
**Owner:** Bob (PM/SM)
**Estimate:** This week
**Status:** PENDING

**Issue:** No clear workflow for story status transitions and who triggers them.

**Action Steps:**
1. Document status transitions in `CLAUDE.md`
2. Define roles:
   - Dev: Moves story from "in-progress" → "review"
   - Code Review: Moves story from "review" → "done" (with fixes)
   - PM: Creates next story after "done"
3. Add gatekeeper checks:
   - Story cannot be "review" unless all tasks complete
   - Story cannot be "done" unless code review approved

**Output:** Add Story Status Workflow section to `CLAUDE.md`

---

## Priority 4: BIG BLOCKER (Do LAST)

### 11. Setup Automated Testing Infrastructure
**Owner:** Dana (Test Architect) + Charlie (Dev support)
**Estimate:** 4-6 hours
**Status:** BLOCKER - Epic 4 CANNOT START until this is complete

**Issue:** Testing infrastructure gap identified in Epic 2.5 (HIGH priority), worsened in Epic 3. Stories repeatedly noted "tests written but not executed (requires Docker environment)".

**Action Steps:**

**Step 1: Pytest Configuration (Charlie) - 1 hour**
1. Configure pytest for backend tests
2. Create `conftest.py` with test fixtures
3. Setup test database isolation
4. Configure coverage reporting

**Files:**
- `backend/pyproject.toml` (pytest config)
- `backend/tests/conftest.py` (fixtures)

**Step 2: CI Pipeline Setup (Dana) - 2 hours**
1. Configure GitHub Actions workflow for CI
2. Setup automated test runs on PRs
3. Add quality gates (test coverage, linting)
4. Configure build and deployment pipelines

**File:** `.github/workflows/ci.yml`

**Step 3: Write Tests for Epic 3 Stories (Dana + Charlie) - 2-3 hours**
1. Write tests for Story 3.1 (Expense Model)
2. Write tests for Story 3.2-3.3 (AI Parsing)
3. Write tests for Story 3.5-3.8 (Split Logic)
4. Ensure all tests pass

**Files:**
- `backend/tests/test_expenses.py`
- `backend/tests/test_ai_parsing.py`
- `backend/tests/test_split_logic.py`

**Step 4: Run Tests and Verify (Charlie) - 1 hour**
1. Execute full test suite
2. Review coverage report (aim for 80%+)
3. Fix any failing tests
4. Document test execution in CI

**Commands:**
```bash
# Run backend tests
cd backend
docker compose exec backend pytest -v --cov=app --cov-report=html

# Run specific test file
docker compose exec backend pytest tests/test_expenses.py -v
```

---

## Priority 5: UX POLISH

### 12. Fix Group Detail Navigation
**Owner:** Elena (UX Designer)
**Estimate:** 3-4 hours
**Status:** PENDING

**Issue:** From Epic 2.5 retrospective - Story 2.5.7 navigation goes to wrong page.

**Action Steps:**
1. Open: `stories/2-5-7-update-existing-screens-to-new-design-system.md`
2. Review navigation requirements
3. Update frontend routing to navigate to specific group detail page
4. Test navigation flow end-to-end

**File to investigate:**
- `frontend/src/features/groups/components/GroupCard.tsx` (or similar)
- `frontend/src/router/index.tsx` (routing configuration)

---

## Action Item Summary by Team Member

### Bob (PM/SM) - Process & Tracking
| Task | Estimate | Priority |
|------|----------|----------|
| Single Source of Truth Documentation | 30 min | P1 |
| Story 3.6 Status Resolution | 30 min | P1 |
| Add Security to AC Checklist | 2 hours | P2 |
| Define "Minimum Viable Story" Standard | 2-3 hours | P2 |
| Clarify Code Review Scoping | 1 hour | P2 |
| Create Deferred Task Tracking Standard | 1 week | P3 |
| Document Story Status Workflow | This week | P3 |

**Total Bob Time:** 7-8 hours (over 1-2 weeks)

---

### Charlie (Dev/Architect) - Implementation & Docs
| Task | Estimate | Priority |
|------|----------|----------|
| Story 3.8 Implementation Completion | 2-3 hours | P1 |
| Console.log Placeholder Removal | 1 hour | P1 |
| Document Docker Volume Workaround | 30 min | P2 |
| Pytest Configuration (Testing Infra) | 1 hour | P4 |
| Run Tests and Verify (Testing Infra) | 1 hour | P4 |
| Write Tests for Epic 3 (Testing Infra) | 2-3 hours | P4 |

**Total Charlie Time:** 7-9 hours (over 1 week)

---

### Dana (Test Architect) - Testing Infrastructure
| Task | Estimate | Priority |
|------|----------|----------|
| CI Pipeline Setup | 2 hours | P4 |
| Write Tests for Epic 3 | 2-3 hours | P4 |

**Total Dana Time:** 4-5 hours (over 1 week)

---

### Elena (UX Designer) - UX Polish
| Task | Estimate | Priority |
|------|----------|----------|
| Fix Group Detail Navigation | 3-4 hours | P5 |

**Total Elena Time:** 3-4 hours (over 1 week)

---

## Execution Strategy

### Recommended Start Order

**Week 1: Fast Wins + Process Foundation**
1. Day 1: Bob completes P1 tasks (Single Source of Truth, Story 3.6)
2. Day 1-2: Charlie completes P1 tasks (Story 3.8, Console.log removal)
3. Day 2-3: Bob completes P2 tasks (Security AC, MVS, Code Review Scope)
4. Day 3: Charlie documents Docker workaround

**Week 1-2: Deferred Tasks + Testing Setup**
5. Ongoing: Bob creates Deferred Task Standard and documents Status Workflow
6. Day 4-5: Charlie sets up Pytest configuration
7. Day 5: Dana configures CI Pipeline

**Week 2: Testing Infrastructure (BLOCKER)**
8. Day 6-7: Dana + Charlie write tests for Epic 3
9. Day 7: Charlie runs tests and verifies coverage
10. Day 8: Elena fixes group navigation (can be done in parallel)

**Week 2: Epic 4 Ready**
11. All action items complete
12. Epic 4 can begin

---

## Completion Checklist

Before starting Epic 4, verify:

- [ ] Story 3.8 properly completed or marked incomplete
- [ ] Single Source of Truth documented in CLAUDE.md
- [ ] All console.log placeholders removed
- [ ] Story 3.6 status aligned across all files
- [ ] Security added to story AC checklist template
- [ ] "Minimum Viable Story" standard defined and documented
- [ ] Code Review scope clarified and documented
- [ ] Docker workaround documented in CLAUDE.md
- [ ] Deferred Task Tracking standard created
- [ ] Story Status Workflow documented
- [ ] Pytest configured and tests passing for Epic 3
- [ ] CI Pipeline configured with quality gates
- [ ] Test coverage >= 80%
- [ ] Group detail navigation fixed

**All items checked above? Epic 4 can begin.**

---

## References

### Primary Documents
- [Epic 3 Retrospective](epic-3-retro-2026-02-17.md)
- [Epic 2.5 Retrospective](epic-2-5-retro-2026-01-20.md)
- [Epic 2 Retrospective](epic-2-retro-2026-01-20.md)
- [Epic 1 Retrospective](epic-1-retro-2026-01-20.md)

### Tracking Files
- [Sprint Status](sprint-status.yaml)
- [Technical Debt Log](technical-debt-log.yaml)
- [Session Context](../session-context.md)

### Next Epic
- [Epic 4 Definition](../planning-artifacts/epics.md) - Trust & Confirmation Workflow

---

**End of Document**
