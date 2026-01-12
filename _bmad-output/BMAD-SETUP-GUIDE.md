# BMAD Setup & Customization Guide

**Author:** Aheedtahir
**Version:** 1.0
**Created:** 2026-01-12
**Purpose:** Complete guide to set up BMAD with preferred customizations on any new project

---

## Table of Contents

1. [Quick Start Checklist](#quick-start-checklist)
2. [Initial BMAD Installation](#initial-bmad-installation)
3. [Configuration Files Setup](#configuration-files-setup)
4. [Project Learning System](#project-learning-system)
5. [CLAUDE.md Template](#claudemd-template)
6. [Workflow Customizations](#workflow-customizations)
7. [Code Review Preferences](#code-review-preferences)
8. [Tracking & Logging System](#tracking--logging-system)
9. [Best Practices Learned](#best-practices-learned)
10. [Common Issues & Fixes](#common-issues--fixes)

---

## Quick Start Checklist

After installing BMAD on a new project, do these in order:

- [ ] Install BMAD core module
- [ ] Create `_bmad/bmm/config.yaml` with full settings
- [ ] Update `_bmad/core/config.yaml` with project_logs
- [ ] Create `_bmad-output/session-context.md`
- [ ] Create `_bmad-output/implementation-artifacts/` folder structure
- [ ] Create tracking files (solution-patterns, technical-debt, etc.)
- [ ] Update `CLAUDE.md` with startup protocol
- [ ] Run first planning workflow to validate setup

---

## Initial BMAD Installation

### Step 1: Install BMAD

```bash
# In your project root
npx bmad-installer
```

Select modules:
- **Core** (required)
- **BMM** (Main Method - for full SDLC workflows)
- **BMB** (optional - for building custom agents/workflows)

### Step 2: Verify Installation

Check these folders exist:
```
project-root/
├── _bmad/
│   ├── core/
│   │   ├── config.yaml
│   │   └── tasks/
│   ├── bmm/
│   │   ├── agents/
│   │   └── workflows/
│   └── bmb/ (if installed)
└── _bmad-output/
    └── (generated artifacts go here)
```

---

## Configuration Files Setup

### 1. Core Config (`_bmad/core/config.yaml`)

```yaml
# CORE Module Configuration
user_name: Aheedtahir
communication_language: English
document_output_language: English
output_folder: "{project-root}/_bmad-output"

# =============================================================================
# PROJECT LEARNING SYSTEM - Auto-check these files at workflow start
# =============================================================================
project_logs:
  session_context: "{project-root}/_bmad-output/session-context.md"
  sprint_status: "{project-root}/_bmad-output/implementation-artifacts/sprint-status.yaml"
  solution_patterns: "{project-root}/_bmad-output/implementation-artifacts/solution-patterns.yaml"
  technical_debt: "{project-root}/_bmad-output/implementation-artifacts/technical-debt-log.yaml"
  tracking_recommendations: "{project-root}/_bmad-output/implementation-artifacts/tracking-recommendations.md"

startup_protocol: |
  Before starting ANY BMAD workflow or implementation task:
  1. Load session_context for project status and key learnings
  2. Check sprint_status for current epic/story progress
  3. When debugging: Check solution_patterns for known fixes
  4. During reviews: Check technical_debt for deferred issues

logging_requirements: |
  When encountering and solving new issues:
  1. Add to solution_patterns.yaml with symptoms, cause, solution, prevention
  2. Update session_context.md if it's a critical learning
  3. Update technical_debt.yaml for deferred LOW severity issues
  4. Update sprint_status.yaml when story status changes
```

### 2. BMM Config (`_bmad/bmm/config.yaml`)

**IMPORTANT:** This file often doesn't exist after installation. Create it!

```yaml
# BMM Module Configuration
user_name: Aheedtahir
communication_language: English
document_output_language: English
user_skill_level: intermediate  # beginner | intermediate | expert

# Output paths
output_folder: "{project-root}/_bmad-output"
planning_artifacts: "{project-root}/_bmad-output/planning-artifacts"
implementation_artifacts: "{project-root}/_bmad-output/implementation-artifacts"

# Project logs (same as core config)
project_logs:
  session_context: "{project-root}/_bmad-output/session-context.md"
  sprint_status: "{implementation_artifacts}/sprint-status.yaml"
  solution_patterns: "{implementation_artifacts}/solution-patterns.yaml"
  technical_debt: "{implementation_artifacts}/technical-debt-log.yaml"
  tracking_recommendations: "{implementation_artifacts}/tracking-recommendations.md"

# Quick fixes (inline for fast reference)
quick_fixes:
  docker_module_not_found: "docker compose build --no-cache"
  connection_refused_localhost: "Use service name 'db' instead of 'localhost'"
  circular_import: "Import inside function or use TYPE_CHECKING"
  route_not_found_404: "Check TanStack Router file naming conventions"
  data_not_updating: "Add queryClient.invalidateQueries in onSuccess"

startup_protocol: |
  Before starting ANY BMAD workflow or implementation task:
  1. Load session_context for project status and key learnings
  2. Check sprint_status for current epic/story progress
  3. When debugging: Check solution_patterns for known fixes
  4. During reviews: Check technical_debt for deferred issues

logging_requirements: |
  When encountering and solving new issues:
  1. Add to solution_patterns.yaml with symptoms, cause, solution, prevention
  2. Update session_context.md if it's a critical learning
  3. Update technical_debt.yaml for deferred LOW severity issues
  4. Update sprint_status.yaml when story status changes
```

---

## Project Learning System

### Folder Structure

Create this structure in `_bmad-output/`:

```
_bmad-output/
├── session-context.md              # Quick context for new sessions
├── planning-artifacts/             # PRD, architecture, epics, UX
│   ├── prd.md
│   ├── architecture.md
│   ├── epics.md
│   └── ux-design.md (if applicable)
└── implementation-artifacts/       # Stories, tracking, logs
    ├── sprint-status.yaml          # Epic/story progress
    ├── solution-patterns.yaml      # Problem/solution KB
    ├── technical-debt-log.yaml     # Deferred LOW issues
    ├── tracking-recommendations.md # Metrics guide
    └── {story-files}.md            # Individual story files
```

### File Templates

#### session-context.md

```markdown
# Session Context - [PROJECT NAME]

**Last Updated:** [DATE]
**Purpose:** Quick context load for new AI sessions. READ THIS FIRST.

---

## Project Status at a Glance

| Epic | Status | Stories |
|------|--------|---------|
| Epic 1: [Name] | [STATUS] | X/Y |
| Epic 2: [Name] | [STATUS] | X/Y |

**Current Progress:** X stories completed, Y remaining

---

## Critical Files to Check

| File | Purpose | When to Check |
|------|---------|---------------|
| `sprint-status.yaml` | Current story status | Always |
| `solution-patterns.yaml` | Known issues & fixes | When debugging |
| `technical-debt-log.yaml` | Deferred issues | During reviews |

---

## Key Learnings (Token Savers)

### [Category 1] Issues
- **"[Symptom]"** → [Quick fix]

### [Category 2] Issues
- **"[Symptom]"** → [Quick fix]

---

## Architecture Quick Reference

```
Backend: [Stack]
Frontend: [Stack]
Database: [Stack]
Infra: [Stack]

Directory Pattern: [Pattern]
Naming: API/DB: snake_case, Frontend: camelCase
```

---

## Common Commands

```bash
# [Command descriptions]
```

---

## What NOT to Do (Past Mistakes)

1. [Mistake 1]
2. [Mistake 2]

---

## Next Up

**[Next Epic/Story]**
```

#### solution-patterns.yaml

```yaml
# Solution Patterns Log
metadata:
  version: "1.0"
  total_patterns: 0
  categories:
    - docker
    - database
    - frontend
    - backend
    - testing
    - git
    - imports
    - deployment

# =============================================================================
# DOCKER PATTERNS
# =============================================================================
docker: []

# =============================================================================
# DATABASE PATTERNS
# =============================================================================
database: []

# =============================================================================
# IMPORT / CIRCULAR DEPENDENCY PATTERNS
# =============================================================================
imports: []

# =============================================================================
# FRONTEND PATTERNS
# =============================================================================
frontend: []

# =============================================================================
# TESTING PATTERNS
# =============================================================================
testing: []

# =============================================================================
# GIT PATTERNS
# =============================================================================
git: []

# =============================================================================
# QUICK REFERENCE (Most Common Issues)
# =============================================================================
quick_reference: []

# =============================================================================
# HOW TO ADD NEW PATTERNS
# =============================================================================
# When you encounter a new issue:
# 1. Add pattern under appropriate category
# 2. Include: symptoms, root_cause, solution, prevention
# 3. Add to quick_reference if common
# 4. Update metadata.total_patterns count
#
# Example:
#   - id: "CATEGORY-XXX"
#     title: "Brief description"
#     symptoms:
#       - "What you see"
#     root_cause: "Why it happens"
#     solution: |
#       Step by step fix
#     prevention: "How to avoid in future"
#     stories_encountered: ["X.X"]
#     tokens_saved_estimate: "~XXX per occurrence"
```

#### technical-debt-log.yaml

```yaml
# Technical Debt Log
metadata:
  version: "1.0"
  created_at: "[DATE]"
  last_review: "[STORY]"
  total_items: 0
  status_legend:
    open: "Not yet addressed"
    in_progress: "Currently being worked on"
    resolved: "Fixed in a later story"
    wont_fix: "Decided not to address (with reason)"

# =============================================================================
# EPIC 1: [Name]
# =============================================================================
epic_1:
  story_1_1:
    title: "[Story Title]"
    reviewed: false
    items: []
    notes: ""

# =============================================================================
# SUMMARY BY CATEGORY
# =============================================================================
summary:
  by_type:
    test-coverage: 0
    security: 0
    ux: 0
    performance: 0
    validation: 0
    accessibility: 0
  by_status:
    open: 0
    resolved: 0
    in_progress: 0
    wont_fix: 0
  by_effort:
    small: 0
    medium: 0
    large: 0

# =============================================================================
# RECOMMENDED PRIORITIZATION
# =============================================================================
prioritization:
  high_value_quick_wins: []
  should_address_before_production: []
  nice_to_have: []
```

---

## CLAUDE.md Template

Replace your project's CLAUDE.md with this template:

```markdown
# Project Context: [PROJECT NAME]

[Brief 1-2 sentence description]

## CRITICAL: Session Startup Protocol

**Before starting ANY work, load these files in order:**

1. **Quick Context** (ALWAYS): `_bmad-output/session-context.md`
   - Project status, key learnings, common mistakes to avoid

2. **Sprint Status** (ALWAYS): `_bmad-output/implementation-artifacts/sprint-status.yaml`
   - Current epic/story status, what's in progress

3. **Solution Patterns** (When debugging): `_bmad-output/implementation-artifacts/solution-patterns.yaml`
   - Known issues and their fixes (saves tokens by not re-debugging)

4. **Technical Debt** (During reviews): `_bmad-output/implementation-artifacts/technical-debt-log.yaml`
   - Deferred LOW severity issues to address later

**Why?** These logs contain learned solutions that save debugging time and tokens.

## 📊 Current Status

| Epic | Status | Progress |
|------|--------|----------|
| Epic 1: [Name] | [STATUS] | X/Y |

**Next:** [Next story]

## 🛠 Tech Stack

- **Backend**: [Stack]
- **Frontend**: [Stack]
- **Database**: [Stack]
- **Infra**: [Stack]

## 📐 Architectural Patterns

- **Directory Structure**: [Pattern]
- **Naming Conventions**:
  - API/DB: `snake_case`
  - Frontend Code: `camelCase` (Components in `PascalCase`)
- [Other patterns]

## 🚀 Commands

```bash
# Start everything
[command]

# Tests
[command]

# Build
[command]
```

## Known Issues Quick Reference

| Problem | Solution |
|---------|----------|
| [Issue 1] | [Fix 1] |
| [Issue 2] | [Fix 2] |

**Full solutions:** See `solution-patterns.yaml`

## Logging Requirements

When encountering and solving new issues:
1. **Add to solution-patterns.yaml** with symptoms, cause, solution, prevention
2. **Update session-context.md** if it's a critical learning
3. **Update technical-debt-log.yaml** for deferred LOW issues

## References

- [PRD](./_bmad-output/planning-artifacts/prd.md)
- [Architecture](./_bmad-output/planning-artifacts/architecture.md)
- [Epics](./_bmad-output/planning-artifacts/epics.md)
- [Sprint Status](./_bmad-output/implementation-artifacts/sprint-status.yaml)
- [Solution Patterns](./_bmad-output/implementation-artifacts/solution-patterns.yaml)
```

---

## Workflow Customizations

### Preferred Workflow Order

1. **Planning Phase:**
   - `/bmad:bmm:workflows:create-product-brief` - Initial idea capture
   - `/bmad:bmm:workflows:create-prd` - Detailed requirements
   - `/bmad:bmm:workflows:create-architecture` - Technical design
   - `/bmad:bmm:workflows:create-ux-design` - UI/UX (if applicable)
   - `/bmad:bmm:workflows:create-epics-and-stories` - Break into work items

2. **Implementation Phase:**
   - `/bmad:bmm:workflows:sprint-planning` - Initialize sprint tracking
   - `/bmad:bmm:workflows:create-story` - Create next story file
   - `/bmad:bmm:workflows:dev-story` - Implement the story
   - `/bmad:bmm:workflows:code-review` - Review implementation

3. **Maintenance:**
   - `/bmad:bmm:workflows:retrospective` - After epic completion

### Workflow Preferences

| Workflow | Preference |
|----------|------------|
| code-review | Run in separate chat for fresh perspective |
| dev-story | Use YOLO mode sparingly, prefer step-by-step |
| create-story | Always validate before dev-story |

---

## Code Review Preferences

### Adversarial Review Settings

The code review workflow should:

1. **Find 3-10 issues minimum** - No "looks good" reviews
2. **Validate all claims** - Check git vs story File List
3. **Categorize findings:**
   - CRITICAL: Tasks marked [x] but not done, security vulnerabilities
   - HIGH: ACs not implemented, false claims
   - MEDIUM: Code quality, performance, UX issues
   - LOW: Style, documentation, nice-to-haves

### After Review Actions

1. **Fix all MEDIUM+ issues** before marking story done
2. **Log LOW issues** to technical-debt-log.yaml
3. **Update solution-patterns.yaml** with any new debugging learnings
4. **Update sprint-status.yaml** with new status

### Review Checklist

```markdown
- [ ] All ACs validated against implementation
- [ ] All tasks [x] verified in code
- [ ] Git changes match story File List
- [ ] Security review performed
- [ ] Test coverage adequate
- [ ] Code quality acceptable
- [ ] LOW issues logged to technical debt
- [ ] Story status updated
- [ ] Sprint status synced
```

---

## Tracking & Logging System

### What to Track

| Priority | File | Purpose |
|----------|------|---------|
| 1 | solution-patterns.yaml | Problem/solution KB (token saver) |
| 2 | technical-debt-log.yaml | Deferred LOW issues |
| 3 | sprint-status.yaml | Epic/story progress |
| 4 | session-context.md | Quick context for new sessions |

### Optional Additional Tracking

| File | Purpose |
|------|---------|
| code-review-metrics.yaml | Quantify quality trends |
| patterns-learned.yaml | Reusable code patterns |
| regression-risks.yaml | Areas prone to breaking |
| ai-agent-performance.yaml | Track AI weaknesses |

### When to Update Logs

| Event | Update |
|-------|--------|
| Solve a bug that took >5 min | solution-patterns.yaml |
| Complete code review | technical-debt-log.yaml |
| Change story status | sprint-status.yaml |
| Complete an epic | session-context.md |
| Learn critical pattern | session-context.md |

---

## Best Practices Learned

### Session Management

1. **Always check logs first** - Saves tokens by not re-debugging
2. **Keep session-context.md short** - It's for fast loading
3. **Update logs as you go** - Don't batch updates

### Code Implementation

1. **Read files before editing** - Claude Code requires this
2. **Use parallel tool calls** - Faster execution
3. **Don't over-engineer** - Only add what's requested
4. **Follow existing patterns** - Check previous story implementations

### Testing

1. **Write tests with implementation** - Not after
2. **Test edge cases** - Future dates, empty states, etc.
3. **Verify in Docker** - localhost != container networking

### Git Practices

1. **Commit after each story** - Not after multiple stories
2. **Use conventional commits** - `feat:`, `fix:`, `refactor:`
3. **Don't amend pushed commits** - Unless explicitly requested

### BMAD Workflow Tips

1. **Fresh chat for reviews** - Different perspective
2. **YOLO mode carefully** - Only for simple, well-defined tasks
3. **Validate stories** - Before running dev-story
4. **Check sprint status** - Before starting any work

---

## Common Issues & Fixes

### Docker Issues

| Issue | Fix |
|-------|-----|
| ModuleNotFoundError in container | `docker compose build --no-cache` |
| Connection refused localhost:5432 | Use service name `db` not `localhost` |
| Permission denied on mounted volume | Add `user: "${UID}:${GID}"` to compose |

### Import Issues

| Issue | Fix |
|-------|-----|
| Circular import error | Import inside function or use TYPE_CHECKING |
| Partially initialized module | Check import order, use lazy imports |

### Frontend Issues

| Issue | Fix |
|-------|-----|
| Route not found 404 | Check TanStack Router file naming |
| Data not updating after mutation | Add `queryClient.invalidateQueries` |
| Type errors after API change | Regenerate OpenAPI client |

### Database Issues

| Issue | Fix |
|-------|-----|
| Multiple migration heads | `alembic merge -m "merge" rev1 rev2` |
| Relationship not loading | Define both sides with `back_populates` |

### Testing Issues

| Issue | Fix |
|-------|-----|
| Tests pass alone, fail together | Database state leaking, use rollback |
| Fixture not found | Move to conftest.py at appropriate level |

---

## Setup Verification Checklist

After setting up BMAD on a new project, verify:

- [ ] `_bmad/core/config.yaml` has project_logs section
- [ ] `_bmad/bmm/config.yaml` exists with full settings
- [ ] `_bmad-output/session-context.md` created
- [ ] `_bmad-output/implementation-artifacts/` folder exists
- [ ] `solution-patterns.yaml` created (even if empty)
- [ ] `technical-debt-log.yaml` created (even if empty)
- [ ] `CLAUDE.md` has startup protocol section
- [ ] Test a workflow runs without config errors

---

## Quick Reference Card

### Starting a New Session

```
1. Load session-context.md
2. Check sprint-status.yaml
3. Load solution-patterns.yaml (if debugging)
```

### After Solving a Bug

```
1. Add to solution-patterns.yaml
2. Update session-context.md (if critical)
```

### After Code Review

```
1. Fix MEDIUM+ issues
2. Log LOW issues to technical-debt-log.yaml
3. Update sprint-status.yaml
4. Mark story as done
```

### After Completing Epic

```
1. Update session-context.md
2. Run retrospective workflow (optional)
3. Update CLAUDE.md status table
```

---

**Keep this guide updated as you discover new preferences and patterns!**
