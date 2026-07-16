---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-01-05'
inputDocuments:
  - "c:/Users/aheedtahir/Bmad-Experiment/_bmad-output/planning-artifacts/prd.md"
workflowType: 'architecture'
project_name: 'ClearDues'
user_name: 'Aheedtahir'
date: '2026-01-05'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
Analysis of 19 FRs indicates a system focused on:
- **Low-Friction Entry:** Natural language processing for expense creation.
- **Complex Transaction Logic:** Handling splits, exclusions, and confirmations.
- **Agentic Behavior:** Active state management for debt chasing (notifications).
- **Trust:** Immutable audit logs for all actions.
- **Offline-First:** Robust local storage and sync logic.

**Non-Functional Requirements:**
Critical NFRs driving architecture:
- **Real-Time Responsiveness:** <200ms sync via WebSockets.
- **Offline Durability:** Local-first data architecture.
- **Concurrency:** Support for 1,000+ simultaneous connections (Python Async).
- **Security:** "Walled Garden" closed auth system.

**Scale & Complexity:**
Project is classified as **Medium** complexity.
- Primary domain: **Mobile-First PWA (Fintech)**
- Complexity level: **Medium** (High interaction/logic, low reg compliance)
- Estimated architectural components: **10-15** (Client, API, WS Gateway, Task Queue, DB, Cache, AI Service, etc.)

### Technical Constraints & Dependencies

- **Backend:** Python (FastAPI/Django Channels) mandatory for async/AI alignment.
- **Protocol:** WebSockets (wss://) required for core features.
- **Deployment:** Mobile-first PWA (no native stores initially).
- **Auth:** Strict "Walled Garden" (JWT/OAuth).

### Cross-Cutting Concerns Identified

- **Real-Time Synchronization:** Impacting all data-modification flows.
- **Offline/Sync Engine:** Complex conflict resolution and queue management.
- **Audit Logging:** Centralized, immutable record-keeping middleware.
- **Notification Scheduling:** "Agent" state machine independent of user sessions.

## Starter Template Evaluation

### Primary Technology Domain

**Full-Stack Web Application (PWA-Ready)** based on project requirements analysis.

### Starter Options Considered

1.  **FARM Stack Templates** (FastAPI + React + MongoDB):
    -   *Pros:* Great for unstructured data; flexible schema.
    -   *Cons:* User requested PostgreSQL; Relational model (Users/Groups/Debts) fits SQL better.

2.  **Full-Stack FastAPI Template** (FastAPI + React + PostgreSQL):
    -   *Pros:* Official styling from FastAPI creator; Includes Postgres, Docker, and modern React (Vite).
    -   *Cons:* Can be heavy (includes Celery, Traefik, etc.), but this matches our "Medium complexity" and "Real-time" needs.

### Selected Starter: `full-stack-fastapi-template`

**Rationale for Selection:**
This is the industry-standard reference architecture for the requested stack (FastAPI + React + Postgres).
-   **Backend:** FastAPI with **SQLModel** (ideal for Postgres).
-   **Frontend:** **React** with **Vite** and **TypeScript** (User's "best fit" request).
-   **Infrastructure:** Fully dockerized (deployed via Docker Compose on a VPS — decided WS9, 2026-07-15).
-   **PWA/Real-Time:** Vite support makes PWA additions easy; FastAPI native WebSockets ready.

**Initialization Command:**

```bash
cookiecutter https://github.com/tiangolo/full-stack-fastapi-template
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
-   **Backend:** Python 3.10+ (FastAPI)
-   **Frontend:** TypeScript (React)
-   **Runtime:** Docker (Containerized for consistency)

**Styling Solution:**
-   **Chakra UI** (or Tailwind in newer forks) - Provides accessible, composable components for the dashboard.

**Build Tooling:**
-   **Frontend:** Vite (Fast builds, HMR)
-   **DB:** Alembic (Migrations)
-   **ORM:** SQLModel (Pydantic + SQLAlchemy)

**Testing Framework:**
-   **Backend:** Pytest (Integrated in Docker)
-   **Frontend:** Jest/Vitest

**Code Organization:**
-   **Backend:** Modular structure (API router, CRUD, Schemas, Models).
-   **Frontend:** Component-based architecture with Hooks.

**Development Experience:**
-   **Hot Reload:** Live coding for both backend and frontend via Docker volumes.
-   **Auth:** Pre-built JWT with OAuth2 support.

**Note:** Project initialization using this command should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
-   **State Management:** Redux Toolkit (Selected for scalability).
-   **Offline Strategy:** TanStack Query + Persist (Selected for "Medium" complexity).
-   **Deployment Target:** Vercel (frontend) + Render (backend) + Neon (Postgres),
    free tiers until rollout (OWNER DECISION WS9.5, 2026-07-16 — supersedes both the
    original Railway selection and WS9's compose-on-VPS, which is kept as fallback in
    `deployment-vps.md`). WS12's Redis/Celery lands on Render Key Value +
    background workers.

### Data Architecture

-   **Database:** **PostgreSQL** (Relational integrity for complex debt graphs).
-   **Validation:** **Pydantic** (Backend) + **Zod** (Frontend).
-   **Offline Sync:** **TanStack Query Persist** (Local caching) + "Mutation Queue" pattern for offline actions.

### Authentication & Security

-   **Auth Method:** **OAuth2 + JWT** (Provided by Starter).
-   **Security:** "Walled Garden" - No public read access; all routes require valid Bearer token.
-   **Sensitive Data:** All financial input sanitization via Pydantic validators.

### API & Communication Patterns

-   **Protocol:**
    -   **REST:** Standard CRUD (Users, Groups, Debts).
    -   **WebSockets:** Real-time events (Bill splits, Chat).
-   **Message Broker:** **Redis Pub/Sub** (Confirmed).
    -   *Usage:* Broadcasting updates from "Worker" to "Connected Clients".

### Frontend Architecture

-   **State Management:** **Redux Toolkit** (Selected).
    -   *Rationale:* Standardized state container for scaling the MVP; robust debugging tools.
-   **Data Fetching:** **TanStack Query** (React Query).
    -   *Rationale:* Manages server state, caching, and offline persistence seamlessly.

### Infrastructure & Deployment

-   **Platform:** **Vercel (SPA) + Render (FastAPI) + Neon (Postgres 17)** — owner
    decision WS9.5, 2026-07-16, chosen for genuinely free tiers until rollout.
    -   *Artifacts:* `render.yaml` blueprint (repo root), `frontend/vercel.json`
        (SPA rewrite + security headers), nightly Neon pg_dump via GitHub Actions
        (`.github/workflows/db-backup.yml`), first-deploy guide `deployment.md`.
    -   *Cost:* $0 until rollout; upgrade triggers documented in deployment.md §8
        (Render Starter $7/mo at first real users; Vercel Pro or Cloudflare Pages at
        monetization; Neon Launch at >0.5 GB).
    -   *Fallback:* the WS9 compose-on-VPS stack, verified end-to-end, in
        `deployment-vps.md`.
-   **CI/CD:** GitHub Actions (root-level `ci.yml`, live since WS1) as the quality gate;
    Vercel/Render auto-deploy `main` on push (monorepo Root Directory + build filters).

### Decision Impact Analysis

**Implementation Sequence:**
1.  Init Project (FastAPI + Redux Starter).
2.  Wire Neon + Render + Vercel per the WS9.5 guide (`deployment.md`); Redis lands with WS12 (Render Key Value).
3.  Implement "Real-time" socket layer (Redis connection).
4.  Build "Offline" Mutation Queue (TanStack).

**Cross-Component Dependencies:**
-   **Redux <-> WebSocket:** Socket events must dispatch Redux actions to update UI state instantly.
-   **TanStack <-> Redux:** Clear separation needed; TanStack handles *Server State* (Caching), Redux handles *Client State* (UI interactions).

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
4 areas where AI agents could make different choices (Naming, Structure, Events, Error Handling).

### Naming Patterns

**Database Naming Conventions:**
-   **Tables:** `snake_case`, plural (e.g., `users`, `expense_groups`).
-   **Columns:** `snake_case` (e.g., `created_at`, `is_active`).
-   **Foreign Keys:** `singular_table_id` (e.g., `user_id`, `group_id`).

**API Naming Conventions:**
-   **Endpoints:** RESTful, plural nouns, hyphenated (e.g., `GET /api/v1/expense-groups`).
-   **JSON Fields:** `snake_case` (Matches Python backend models by default).
    -   *Rationale:* Avoids excessive "magic" middleware. Frontend maps to camelCase if needed, but 'snake_case' on wire is the source of truth.

**Code Naming Conventions:**
-   **Python (Backend):** `snake_case` for everything (standard PEP-8).
-   **TypeScript (Frontend):**
    -   Variables/Functions: `camelCase` (e.g., `getUserData`).
    -   Components: `PascalCase` (e.g., `ExpenseCard.tsx`).
    -   Types/Interfaces: `PascalCase` (e.g., `interface User`).

### Structure Patterns

**Project Organization:**
-   **Feature-Based:** Code organized by domain feature rather than technical type.
    -   *Example:* `/features/auth/*` (contains components, api, hooks) rather than `/components/auth` + `/hooks/auth`.
    -   *Rationale:* scalable for "Medium" complexity; keeps related code together.

**File Structure Patterns:**
-   **Tests:** Co-located with source files.
    -   `Login.tsx` -> `Login.test.tsx`
    -   `auth.service.ts` -> `auth.service.test.ts`

### Communication Patterns

**Event System Patterns (Redis Pub/Sub):**
-   **Naming:** `domain.entity.action` (e.g., `billing.expense.created`).
-   **Payload:** Standard Envelope.
    ```json
    {
      "event": "billing.expense.created",
      "timestamp": "2026-01-05T...",
      "payload": { "id": "123", "amount": 50 }
    }
    ```

**State Management Patterns:**
-   **Server State:** TanStack Query.
-   **Client State:** Redux Toolkit.
-   **No Overlap:** Do not store API responses in Redux unless transforming heavily for UI state.

### Process Patterns

**Error Handling Patterns:**
-   **Backend:** Raise `HTTPException(status_code=..., detail="...")`.
-   **Frontend:**
    -   Global: Axios interceptor triggers "Toast" for 5xx/4xx errors.
    -   Local: Form fields show inline validation errors (Zod).

### Enforcement Guidelines

**All AI Agents MUST:**
1.  Respect `snake_case` for API JSON payloads.
2.  Place new features in `/features/{name}` directory.
3.  Use the standard Event Envelope for Redis messages.

**Pattern Examples:**

**Good (API):**
```python
# Returns snake_case JSON
return {"user_id": 123, "full_name": "Alex"}
```

**Anti-Pattern (API):**
```python
# Do NOT force camelCase manually in backend
return {"userId": 123, "fullName": "Alex"}
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
ClearDues/
├── .github/workflows/         # CI/CD Pipelines
├── backend/                   # FastAPI Backend
│   ├── app/
│   │   ├── core/              # Global Config (DB, Security, Settings)
│   │   ├── features/          # Domain Modules
│   │   │   ├── auth/          # Authentication (Login, Register)
│   │   │   ├── expenses/      # Expense Logic (NLP, Parsing, CRUD)
│   │   │   ├── groups/        # Group Management
│   │   │   └── notifications/ # Alerts & background tasks
│   │   ├── models/            # Shared Pydantic Models
│   │   ├── api/               # API Router v1
│   │   └── main.py            # App Entrypoint
│   ├── tests/                 # Pytest Suite
│   ├── pyproject.toml         # Poetry Dependecies
│   └── alembic.ini            # DB Migrations Config
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── features/          # UI Logic Modules
│   │   │   ├── auth/          # Login Screens
│   │   │   ├── dashboard/     # Balances & Activity
│   │   │   └── expenses/      # Add/Edit Expense Forms
│   │   ├── shared/            # Reusable Code
│   │   │   ├── api/           # Axios & TanStack Query Setup
│   │   │   ├── components/    # UI Kit (Buttons, Inputs)
│   │   │   ├── hooks/         # Custom Hooks (useSocket)
│   │   │   └── store/         # Redux Slices
│   │   ├── App.tsx            # Main Router
│   │   └── main.tsx           # Entrypoint
│   ├── package.json           # NPM Dependencies
│   └── vite.config.ts         # Build Config
│
└── infra/                     # Infrastructure
    ├── docker/                # Dockerfiles
    └── docker-compose.yml     # Local Dev Stack
```

### Architectural Boundaries

**API Boundaries:**
-   **External:** `/api/v1/*` (REST) and `/ws/*` (WebSockets).
-   **Internal:** Service Layer functions (e.g., `expenses.service.create_expense`) are the boundary between API routes and DB.

**Component Boundaries:**
-   **Frontend:** Features are self-contained. `frontend/features/auth` should not import heavily from `frontend/features/expenses`. Shared logic moves to `frontend/shared`.
-   **State:** Redux handles global UI state (Theme, User Session). TanStack Query handles all Server Data.

**Data Boundaries:**
-   **Schema:** Defined in `backend/app/features/{name}/models.py` (SQLModel).
-   **Access:** Only Service Layer functions access the DB directly. API Routes call Services.

### Requirements to Structure Mapping

**Features:**
-   **User Management:** `backend/app/features/auth` + `frontend/src/features/auth`
-   **Expense Input:** `backend/app/features/expenses` (Handling NLP) + `frontend/src/features/expenses`
-   **Notifications:** `backend/app/features/notifications` (Celery Tasks)

**Cross-Cutting Concerns:**
-   **Real-Time:** `backend/app/core/socket.py` + `frontend/src/shared/hooks/useSocket.ts`
-   **Offline Sync:** `frontend/src/shared/api/mutationQueue.ts` (TanStack Logic)

### Integration Points

**Internal Communication:**
-   **API -> Service:** Direct function calls.
-   **Service -> Worker:** Celery Task Dispatch (`notifications.tasks.send_nudge`).
-   **Worker -> API:** Redis Pub/Sub for specific events.

**Data Flow:**
1.  User Input -> React Component -> Redux (UI State) -> TanStack Mutation
2.  TanStack -> Axios -> FastAPI Endpoint -> Service Layer
3.  Service Layer -> SQLModel -> PostgreSQL
4.  Service Layer -> Redis (Event) -> WebSocket -> Frontend Client Update

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
FastAPI (Backend) + Redux (Frontend State) + compose-on-VPS (Deployment, per WS9) creates a coherent loop. The "Feature-based" folder structure aligns perfectly with the scalable nature of the chosen stack.

**Pattern Consistency:**
The agreed `snake_case` (API) vs `camelCase` (Frontend) pattern is supported by the standard behavior of the chosen frameworks, minimizing friction.

**Structure Alignment:**
The decision to use strict Feature Modules (`/features/auth`, `/features/expenses`) directly supports the "Medium" complexity requirement, preventing the "giant components folder" anti-pattern.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
-   **User Management:** Covered by `features/auth` + PostgreSQL Users table.
-   **Expense Input:** Covered by `features/expenses` + NLP Service.
-   **Real-time Extensions:** Covered by Redis Pub/Sub + WebSocket layer.

**Functional Requirements Coverage:**
All 19 FRs map to specific backend services or frontend features defined in the structure.

**Non-Functional Requirements Coverage:**
-   **Offline:** Covered by TanStack Query Persist.
-   **Real-time:** Covered by Redis/WebSockets.
-   **Security:** Covered by "Walled Garden" Auth middleware in `core`.

### Implementation Readiness Validation ✅

**Decision Completeness:**
All critical decisions (State, DB, Offline, Deployment) are made and documented.

**Structure Completeness:**
Full directory tree is defined.

**Pattern Completeness:**
Naming and Communication patterns are locked.

### Gap Analysis Results

**None Critical.**
*Note:* Specific library choices for "Chart/Graphing" (for later analytics) were deferred, which is appropriate for MVP.

### Architecture Completeness Checklist

**✅ Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
1.  **Clear Boundaries:** Feature-based structure prevents spaghetti code.
2.  **Robust Stack:** Industry-standard choices (FastAPI/React/Postgres) reduce risk.
3.  **Scalable State:** Redux + TanStack separates concerns effectively.

### Implementation Handoff

**AI Agent Guidelines:**

-   Follow all architectural decisions exactly as documented
-   Use implementation patterns consistently across all components
-   Respect project structure and boundaries
-   Refer to this document for all architectural questions

**First Implementation Priority:**
Initialize with `full-stack-fastapi-template`, then immediately strictly reorganize into the `/features` directory structure defined in `architecture.md`.

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-01-05
**Document Location:** c:/Users/aheedtahir/Bmad-Experiment/_bmad-output/planning-artifacts/architecture.md

### Final Architecture Deliverables

**📋 Complete Architecture Document**
-   All architectural decisions documented with specific versions
-   Implementation patterns ensuring AI agent consistency
-   Complete project structure with all files and directories
-   Requirements to architecture mapping
-   Validation confirming coherence and completeness

**🏗️ Implementation Ready Foundation**
-   **4** critical architectural decisions made (State, DB, Offline, Deployment)
-   **4** implementation pattern categories defined (Naming, Structure, Events, Process)
-   **19** functional requirements fully supported

**📚 AI Agent Implementation Guide**
-   Technology stack with verified versions (FastAPI, React, Redux, compose-on-VPS)
-   Consistency rules that prevent implementation conflicts
-   Project structure with clear boundaries
-   Integration patterns and communication standards

### Quality Assurance Checklist

**✅ Architecture Coherence**
- [x] All decisions work together without conflicts
- [x] Technology choices are compatible
- [x] Patterns support the architectural decisions
- [x] Structure aligns with all choices

**✅ Requirements Coverage**
- [x] All functional requirements are supported
- [x] All non-functional requirements are addressed
- [x] Cross-cutting concerns are handled
- [x] Integration points are defined

**✅ Implementation Readiness**
- [x] Decisions are specific and actionable
- [x] Patterns prevent agent conflicts
- [x] Structure is complete and unambiguous
- [x] Examples are provided for clarity

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Begin implementation using the architectural decisions and patterns documented herein.
