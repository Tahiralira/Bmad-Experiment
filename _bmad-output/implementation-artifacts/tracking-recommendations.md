# Development Metrics & Tracking Recommendations

**Created:** 2026-01-12
**Purpose:** Guide for data collection to improve AI-assisted development quality

---

## Already Tracking (Good!)

### 1. Technical Debt Log (`technical-debt-log.yaml`)
- LOW severity issues from code reviews
- Categorized by type (security, UX, performance, etc.)
- Prioritization recommendations

### 2. Story Files
- Acceptance criteria completion
- Task completion status
- Dev agent records (model used, file list, completion notes)

### 3. Sprint Status (`sprint-status.yaml`)
- Story progress tracking
- Epic completion status

---

## Recommended Additional Tracking

### 1. Code Review Metrics (`code-review-metrics.yaml`)

Track per story:
```yaml
story_2_4:
  review_date: "2026-01-12"
  review_duration_minutes: 15
  issues_found:
    critical: 0
    high: 0
    medium: 5
    low: 4
  issues_fixed: 5
  issues_deferred: 4
  ac_validation:
    total: 6
    passed: 6
    failed: 0
  task_audit:
    total: 8
    verified: 8
    false_claims: 0
```

**Why:** Identifies patterns - which epics have more issues? Which issue types recur?

---

### 2. Implementation Patterns Log (`patterns-learned.yaml`)

Document reusable patterns discovered:
```yaml
patterns:
  - id: "tanstack-query-hook"
    discovered_in: "Story 2.4"
    category: "frontend"
    description: "Standard TanStack Query hook pattern"
    example_file: "frontend/src/features/dashboard/api/dashboard.ts"
    reuse_count: 4

  - id: "sqlmodel-response-schema"
    discovered_in: "Story 2.1"
    category: "backend"
    description: "SQLModel for API response schemas"
    example_file: "backend/app/features/auth/models.py"
    reuse_count: 6
```

**Why:** Speeds up future development by referencing proven patterns.

---

### 3. Regression Risk Log (`regression-risks.yaml`)

Track areas prone to breaking:
```yaml
risks:
  - id: "auth-import-cycle"
    file: "backend/app/features/auth/service.py"
    description: "Circular import between auth and groups modules"
    workaround: "Import inside function"
    stories_affected: ["2.4"]
    risk_level: "medium"
    mitigation: "Consider shared types module"

  - id: "frontend-route-changes"
    file: "frontend/src/routes/"
    description: "TanStack Router file-based routing is sensitive to structure"
    stories_affected: ["2.4"]
    risk_level: "low"
```

**Why:** Prevents future stories from breaking existing functionality.

---

### 4. Test Coverage Gaps (`test-coverage-gaps.yaml`)

Document what's NOT tested:
```yaml
gaps:
  - feature: "OAuth flow"
    type: "integration"
    reason: "Requires mock OAuth provider"
    priority: "medium"
    stories_affected: ["1.6"]

  - feature: "WebSocket real-time updates"
    type: "e2e"
    reason: "Not yet implemented"
    priority: "high"
    stories_affected: []  # Future epics
```

**Why:** Ensures critical paths get test coverage before production.

---

### 5. AI Agent Performance Log (`ai-agent-performance.yaml`)

Track AI-specific metrics:
```yaml
story_2_4:
  agent_model: "Claude Opus 4.5"
  implementation_quality:
    first_pass_success: true
    review_issues_count: 9
    review_fixes_needed: 5
  common_mistakes: []
  time_saved_estimate: "4 hours vs manual"

cumulative:
  stories_completed: 10
  average_issues_per_story: 7
  most_common_issue_type: "security"
  most_common_fix_type: "dark_mode_support"
```

**Why:** Identifies AI weaknesses to address in prompts or agent instructions.

---

### 6. Dependency Health (`dependency-health.yaml`)

Track third-party risks:
```yaml
backend:
  - package: "fastapi"
    version: "0.115.0"
    last_audit: "2026-01-12"
    known_issues: []
    update_available: false

  - package: "sqlmodel"
    version: "0.0.22"
    last_audit: "2026-01-12"
    known_issues:
      - "No async support yet"
    update_available: true

frontend:
  - package: "@tanstack/react-query"
    version: "5.x"
    last_audit: "2026-01-12"
    known_issues: []
```

**Why:** Proactive security and compatibility management.

---

### 7. Architecture Decision Records (`adr/`)

Document key decisions:
```
_bmad-output/adr/
├── 001-feature-based-architecture.md
├── 002-magic-link-auth.md
├── 003-oauth-provider-selection.md
└── 004-dashboard-in-auth-feature.md
```

Each ADR:
```markdown
# ADR-004: Dashboard Endpoint in Auth Feature

**Status:** Accepted
**Date:** 2026-01-12
**Context:** Where to place dashboard endpoint?
**Decision:** Added to auth/router.py (users_router)
**Rationale:** Dashboard is user-specific, follows /users/me pattern
**Consequences:** Auth feature grows, may need splitting later
```

**Why:** Prevents re-debating decisions and explains "why" to future developers.

---

## Quick Start: Minimum Viable Tracking

If you can only add 2-3 things:

1. **`code-review-metrics.yaml`** - Quantifies quality over time
2. **`patterns-learned.yaml`** - Accelerates future development
3. **`regression-risks.yaml`** - Prevents breaking changes

---

## Implementation Priority

| File | Effort | Value | Priority |
|------|--------|-------|----------|
| technical-debt-log.yaml | Done | High | ✅ |
| code-review-metrics.yaml | Low | High | 1 |
| patterns-learned.yaml | Low | High | 2 |
| regression-risks.yaml | Low | Medium | 3 |
| ai-agent-performance.yaml | Medium | Medium | 4 |
| test-coverage-gaps.yaml | Medium | High | 5 |
| adr/ | Medium | High | 6 |
| dependency-health.yaml | Low | Medium | 7 |

---

## Automation Opportunities

Consider adding to code review workflow:
1. Auto-populate `code-review-metrics.yaml` from review findings
2. Auto-extract patterns from story completion notes
3. Alert on recurring issue types (>3 of same type across stories)
