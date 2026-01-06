---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: 
  - "c:/Users/aheedtahir/Bmad-Experiment/_bmad-output/planning-artifacts/prd.md"
  - "c:/Users/aheedtahir/Bmad-Experiment/_bmad-output/planning-artifacts/architecture.md"
status: complete
---

# ClearDues - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for ClearDues, decomposing the requirements from the PRD and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**FR1:** User can authenticate via keyless entry (Magic Link/OTP) or Social Auth.

**FR2:** User can create a Group and invite others via a deep link.

**FR3:** User can view a dashboard of "Net Balances" across all groups.

**FR4:** User can input expenses via natural language text (e.g., "Paid 60 for lunch") or simple numeric strings.

**FR5:** System must parse [Amount], [Payer], [Payee(s)], and [Description] from text input.

**FR6:** User can manually override/edit the System's parsed output before saving.

**FR7:** User can specify split logic: "Equal", "Unequal", "Percentage", or "Shares".

**FR8:** User can "Exclude" specific group members from a transaction.

**FR9:** **(Restriction):** Only the *Creator* of an expense can edit its details.

**FR10:** **(Confirmation):** Involved members must "Confirm" an expense before it is finalized as debt.

**FR11:** System must schedule "Nudge" notifications based on debt age (Level 1/2).

**FR12:** User can "Snooze" a notification.

**FR13:** User can "Mark as Settled" (claim payment).

**FR14:** **(Confirmation):** Expense Owner must "Confirm" a settlement claim before the debt is cleared.

**FR15:** System must record an immutable "Audit Log" for every creation, edit, confirmation, and settlement.

**FR16:** User can view the "Activity Feed" showing who changed what and when.

**FR17:** User can create/edit expenses while offline (stored locally).

**FR18:** System must sync local changes to the server upon reconnection, rejecting edits to records not owned by the user.

**FR19:** User can configure a "Settlement Cycle" (e.g., Weekly on Thursdays) to suppress daily nags and trigger a "Settlement Day" summary.

### Non-Functional Requirements

**NFR1 (In-App Latency):** When User A edits a split, User B must see the update within **200ms** (via WebSockets).

**NFR2 (Load Time):** App must be interactive (TTI) within **1.5 seconds** on a standard 4G connection.

**NFR3 (AI Latency):** Simple text parsing ("Paid 50") must return a structured draft in under **2 seconds**.

**NFR4 (Encryption):** All financial data encrypted At Rest (AES-256) and In Transit (TLS 1.3).

**NFR5 (Rate Limiting):** API must reject aggressive scraping (>100 req/min) to protect backend costs.

**NFR6 (Offline Durability):** Unsynced data must persist locally indefinitely (protecting against app closure before sync).

**NFR7 (Concurrency):** Backend MVP must support at least **1,000 concurrent WebSocket connections** without degradation.

### Additional Requirements

**Architecture & Infrastructure:**
- **Starter Template:** Initialize project using `full-stack-fastapi-template` (cookiecutter https://github.com/tiangolo/full-stack-fastapi-template)
- **Project Reorganization:** Immediately reorganize into `/features` directory structure after initialization
- **Database:** PostgreSQL with SQLModel ORM
- **Frontend Stack:** React + TypeScript + Vite
- **State Management:** Redux Toolkit (client state) + TanStack Query (server state)
- **Real-Time Communication:** WebSockets with Redis Pub/Sub message broker
- **Deployment Platform:** Railway (supports FastAPI + Celery + Redis + Postgres)
- **Authentication:** OAuth2 + JWT with "Walled Garden" security (no public routes)
- **Offline Strategy:** TanStack Query Persist + Mutation Queue pattern
- **Background Processing:** Celery worker for notification scheduling and async tasks

**Implementation Patterns:**
- **Naming Conventions:** snake_case for API/DB, camelCase for frontend code
- **Project Structure:** Feature-based organization (`/features/{name}`)
- **Event System:** Redis Pub/Sub with `domain.entity.action` naming (e.g., `billing.expense.created`)
- **Error Handling:** HTTPException on backend, Axios interceptor + Zod validation on frontend
- **Testing:** Co-located test files (Pytest for backend, Vitest for frontend)

**Strict Boundaries:**
- Tests co-located with source files
- Service Layer is boundary between API routes and database
- Features are self-contained (shared logic in `/shared` directory)
- Clear separation: Redux for UI state, TanStack Query for server state

### FR Coverage Map

- FR1: Epic 1 - User authentication (Magic Link/OTP/Social Auth)
- FR2: Epic 2 - Create groups and invite via deep link
- FR3: Epic 2 - View dashboard of net balances
- FR4: Epic 3 - Natural language expense input
- FR5: Epic 3 - AI parsing of amount, payer, payees, description
- FR6: Epic 3 - Manual override of parsed output
- FR7: Epic 3 - Specify split logic (Equal/Unequal/Percentage/Shares)
- FR8: Epic 3 - Exclude specific group members
- FR9: Epic 4 - Only creator can edit expense details
- FR10: Epic 4 - Members must confirm expenses before finalization
- FR11: Epic 6 - Schedule nudge notifications based on debt age
- FR12: Epic 6 - Snooze notifications
- FR13: Epic 5 - Mark debts as settled
- FR14: Epic 5 - Owner must confirm settlement claims
- FR15: Epic 4 - Immutable audit log for all actions
- FR16: Epic 4 - View activity feed showing changes
- FR17: Epic 7 - Create/edit expenses offline
- FR18: Epic 7 - Sync local changes on reconnection
- FR19: Epic 6 - Configure settlement cycles to manage notification frequency

## Epic List

### Epic 1: Project Foundation & Authentication
Users can securely access the ClearDues platform with modern authentication methods and have a working development environment ready for all features.

**FRs covered:** FR1  
**Additional Requirements:** Starter template initialization, project reorganization, database setup, deployment infrastructure

**User Outcome:** New users can register and log in; development team has a production-ready foundation.

---

### Epic 2: Group Management & Dashboard
Users can create expense groups, invite friends, and view their financial standing across all groups at a glance.

**FRs covered:** FR2, FR3

**User Outcome:** Users can organize expenses by groups and understand "who owes what" instantly.

---

### Epic 3: Smart Expense Entry
Users can add expenses naturally using conversational text, with AI parsing the details and allowing manual corrections before saving.

**FRs covered:** FR4, FR5, FR6, FR7, FR8

**User Outcome:** Users can record expenses in seconds without tedious forms or manual calculations.

---

### Epic 4: Trust & Confirmation Workflow
Users can safely collaborate on expenses through a confirmation system that ensures transparency and prevents unauthorized changes.

**FRs covered:** FR9, FR10, FR15, FR16

**User Outcome:** Users trust the system because every action is recorded, visible, and requires proper authorization.

---

### Epic 5: Settlement & Payment Tracking
Users can mark debts as settled and owners can confirm settlements, with a clear audit trail of all payment activities.

**FRs covered:** FR13, FR14

**User Outcome:** Users can track when debts are paid and close the loop on expenses without confusion.

---

### Epic 6: Agentic Notifications & Nudges
Users receive intelligent, context-aware reminders about outstanding debts and can manage notification preferences without feeling nagged.

**FRs covered:** FR11, FR12, FR19

**User Outcome:** Users are gently reminded to settle debts without awkward direct confrontation, and the system adapts to their preferences.

---

### Epic 7: Offline Capability & Sync
Users can view balances and create expenses even without internet connectivity, with automatic synchronization when connection returns.

**FRs covered:** FR17, FR18  
**Additional Requirements:** Offline strategy (TanStack Query Persist, Mutation Queue)

**User Outcome:** Users can use ClearDues anywhere, anytime, without worrying about connectivity.

---

## Epic 1: Project Foundation & Authentication

Users can securely access the ClearDues platform with modern authentication methods and have a working development environment ready for all features.

### Story 1.1: Initialize Project from Starter Template

As a **development team**,
I want to initialize the project using the full-stack-fastapi-template,
So that we have a production-ready foundation with Docker, PostgreSQL, and modern tooling configured.

**Acceptance Criteria:**

**Given** the cookiecutter command is available
**When** I run `cookiecutter https://github.com/tiangolo/full-stack-fastapi-template`
**Then** the project is initialized with FastAPI backend, React frontend, PostgreSQL database, and Docker configuration
**And** the development environment runs successfully with `docker-compose up`
**And** the default authentication endpoints are accessible

### Story 1.2: Reorganize to Feature-Based Architecture

As a **development team**,
I want to reorganize the project into feature-based directory structure,
So that the codebase follows the architecture patterns defined in `architecture.md`.

**Acceptance Criteria:**

**Given** the starter template is initialized
**When** I reorganize the backend structure into `/features/{name}` directories
**Then** the following feature directories exist: `auth`, `expenses`, `groups`, `notifications`
**And** each feature directory contains its own models, services, and API routes
**And** the core directory contains global configuration (DB, Security, Settings)
**And** the frontend is organized with `src/features/{name}` structure
**And** all existing tests pass after reorganization

### Story 1.3: Configure Database Models for Users

As a **backend developer**,
I want to create the User model with required fields,
So that users can be stored in PostgreSQL with proper validation.

**Acceptance Criteria:**

**Given** SQLModel and PostgreSQL are configured
**When** I create the User model in `backend/app/features/auth/models.py`
**Then** the model includes: `id`, `email`, `full_name`, `is_active`, `created_at`, `updated_at`
**And** email field has unique constraint
**And** Alembic migration is created for the users table
**And** the migration runs successfully against the database
**And** the table uses snake_case naming convention

### Story 1.4: User Registration with Magic Link

As a **new user**,
I want to register using my email address and receive a magic link,
So that I can create an account without setting a password.

**Acceptance Criteria:**

**Given** I am on the registration page
**When** I submit my email address
**Then** a unique magic link token is generated and stored with expiration (15 minutes)
**And** an email is sent to my address with the magic link
**And** clicking the magic link validates the token and creates my user account
**And** I am redirected to the dashboard with a valid JWT token
**And** expired tokens are rejected with appropriate error message
**And** the API endpoint follows naming convention: `POST /api/v1/auth/register`

### Story 1.5: User Login with JWT Authentication

As a **registered user**,
I want to log in with my email and receive a magic login link,
So that I can access my account securely without remembering passwords.

**Acceptance Criteria:**

**Given** I have a registered account
**When** I request a login link with my email
**Then** a magic link is sent to my email address
**And** clicking the link validates my identity
**And** I receive a JWT access token (expires in 30 days per PRD "Walled Garden")
**And** the token is stored securely in frontend (httpOnly cookie or secure storage)
**And** all subsequent API requests include the Bearer token
**And** invalid or expired tokens return 401 Unauthorized
**And** the API endpoint follows naming convention: `POST /api/v1/auth/login`

### Story 1.6: Social Authentication (OAuth)

As a **new or existing user**,
I want to log in using Google or other social providers,
So that I can access the platform using my existing accounts.

**Acceptance Criteria:**

**Given** OAuth2 providers are configured (Google, GitHub)
**When** I click "Login with Google"
**Then** I am redirected to Google's OAuth consent screen
**And** after approval, I am redirected back with authorization code
**And** the backend exchanges the code for user info
**And** a user account is created or linked if it exists
**And** I receive a JWT token and am logged in
**And** my profile is populated with data from the OAuth provider (email, full_name)
**And** the API endpoint follows naming convention: `GET /api/v1/auth/oauth/{provider}`

---

## Epic 2: Group Management & Dashboard

Users can create expense groups, invite friends, and view their financial standing across all groups at a glance.

### Story 2.1: Create Expense Group

As a **registered user**,
I want to create a new expense group with a name,
So that I can organize expenses with specific people.

**Acceptance Criteria:**

**Given** I am logged in
**When** I create a group with a name (e.g., "Weekend Trip")
**Then** a new group is created in the database with my user as the creator/owner
**And** the group model includes: `id`, `name`, `created_by`, `created_at`, `updated_at`
**And** I am automatically added as a member of the group
**And** a `group_members` join table tracks user-group relationships
**And** the API endpoint follows naming convention: `POST /api/v1/expense-groups`
**And** the table uses snake_case naming: `expense_groups`, `group_members`

### Story 2.2: Invite Members via Deep Link

As a **group creator**,
I want to generate and share an invite link,
So that others can join my expense group easily.

**Acceptance Criteria:**

**Given** I have created a group
**When** I generate an invite link
**Then** a unique shareable URL is created with a token (e.g., `/invite/{token}`)
**And** the token is stored with the group_id and expiration (30 days)
**And** when a user clicks the link and is logged in, they are added to the group
**And** if not logged in, they are prompted to register/login first, then added
**And** the invite link can be used multiple times until expired
**And** expired tokens return appropriate error message
**And** the API endpoint follows naming convention: `GET /api/v1/expense-groups/invite/{token}`

### Story 2.3: View Group Members List

As a **group member**,
I want to see all members in my group,
So that I know who is part of the expense tracking.

**Acceptance Criteria:**

**Given** I am a member of a group
**When** I view the group details
**Then** I see a list of all members with their names and email
**And** the creator/owner is indicated with a badge or label
**And** member data is fetched from the joined users table
**And** the API endpoint follows naming convention: `GET /api/v1/expense-groups/{group_id}/members`

### Story 2.4: Dashboard with Net Balances

As a **registered user**,
I want to view a dashboard showing my net balance across all groups,
So that I can quickly understand my overall financial standing.

**Acceptance Criteria:**

**Given** I am a member of multiple groups with recorded expenses
**When** I view the dashboard
**Then** I see a summary of all groups I belong to
**And** for each group, I see my net balance (positive if owed to me, negative if I owe)
**And** the balance is calculated from all confirmed expenses in the group
**And** groups are sorted by most recent activity
**And** the frontend fetches data via API: `GET /api/v1/users/me/dashboard`
**And** the API returns json with snake_case fields: `group_name`, `net_balance`, `last_activity`

---

## Epic 3: Smart Expense Entry

Users can add expenses naturally using conversational text, with AI parsing the details and allowing manual corrections before saving.

### Story 3.1: Create Expense Model and Basic Entry

As a **group member**,
I want to add a simple numeric expense to my group,
So that I can track who paid and how much.

**Acceptance Criteria:**

**Given** I am a member of a group
**When** I create an expense with amount, description, and payer
**Then** an expense record is created in the database
**And** the expense model includes: `id`, `group_id`, `amount`, `description`, `payer_id`, `created_by`, `status`, `created_at`
**And** the status is set to "draft" initially
**And** the API endpoint follows naming convention: `POST /api/v1/expenses`
**And** the table uses snake_case naming: `expenses`

### Story 3.2: Natural Language Input Interface

As a **group member**,
I want to type expenses in plain English (e.g., "Paid 60 for lunch"),
So that I can add expenses quickly without forms.

**Acceptance Criteria:**

**Given** I am on the expense creation page
**When** I type "Paid 60 for lunch" in a text input field
**Then** the text is captured and ready to be sent to the parsing service
**And** the frontend UI shows a loading state while parsing
**And** the input field supports multi-line for complex descriptions
**And** there is a fallback button to switch to manual/structured form if preferred

### Story 3.3: AI Parsing Service Integration

As a **system**,
I want to parse natural language text into structured expense data,
So that users don't have to manually fill forms.

**Acceptance Criteria:**

**Given** a user submits natural language text
**When** the text is sent to the AI parsing endpoint
**Then** the system extracts: amount, description, payer (defaults to current user)
**And** the parsing completes in under 2 seconds (NFR3)
**And** the parsed data is returned as JSON: `{amount, description, payer_id, confidence_score}`
**And** if parsing fails or confidence is low, an error is returned
**And** the AI service endpoint: `POST /api/v1/expenses/parse`
**And** the service uses OpenAI API or similar NLP provider

### Story 3.4: Manual Override of Parsed Data

As a **group member**,
I want to review and edit AI-parsed expense data before saving,
So that I can correct any mistakes before finalizing.

**Acceptance Criteria:**

**Given** the AI has parsed my text input
**When** I review the parsed data (amount, description, payer)
**Then** I can edit any field inline before confirming
**And** changed fields are highlighted to show what was modified
**And** the original AI suggestion is available for reference
**And** I can confirm and save the expense after reviewing
**And** or discard and start over if completely wrong

### Story 3.5: Split Logic - Equal Split

As a **expense creator**,
I want to split an expense equally among all group members,
So that everyone pays their fair share automatically.

**Acceptance Criteria:**

**Given** I have created an expense with an amount
**When** I select "Equal Split" option
**Then** the expense is divided equally among all active group members
**And** a `expense_splits` table stores the split: `{expense_id, user_id, amount_owed}`
**And** each member's owed amount = total_amount / number_of_members
**And** the split is calculated server-side for accuracy
**And** the API call: `PUT /api/v1/expenses/{expense_id}/split` with `{type: "equal"}`

### Story 3.6: Split Logic - Unequal/Custom Amounts

As a **expense creator**,
I want to specify custom amounts for each person,
So that I can handle unequal splits (e.g., someone ordered more).

**Acceptance Criteria:**

**Given** I have created an expense
**When** I select "Unequal" split and specify amounts per member
**Then** each member's owed amount is set to the custom value I specified
**And** the system validates that the sum of splits equals the total expense amount
**And** if amounts don't match total, an error is shown
**And** the API validates the split logic on the backend
**And** the API call: `PUT /api/v1/expenses/{expense_id}/split` with `{type: "unequal", splits: [{user_id, amount}]}`

### Story 3.7: Split Logic - Percentage Split

As a **expense creator**,
I want to split an expense by percentages,
So that I can handle proportional sharing (e.g., 60/40 split).

**Acceptance Criteria:**

**Given** I have created an expense
**When** I select "Percentage" split and assign percentages to members
**Then** each member's owed amount = (total_amount * their_percentage / 100)
**And** the system validates that percentages sum to 100
**And** if percentages don't add up, an error is shown
**And** amounts are calculated server-side to avoid rounding errors
**And** the API call: `PUT /api/v1/expenses/{expense_id}/split` with `{type: "percentage", splits: [{user_id, percentage}]}`

### Story 3.8: Exclude Members from Expense

As a **expense creator**,
I want to exclude specific group members from an expense,
So that I can handle situations where not everyone participated.

**Acceptance Criteria:**

**Given** I am creating an expense in a group
**When** I select "Exclude" for specific members
**Then** only the non-excluded members are included in the split calculation
**And** excluded members do not appear in the `expense_splits` table for this expense
**And** the UI shows clearly who is included/excluded
**And** I can change exclusions before finalizing the expense
**And** the API accepts an `excluded_user_ids` array in the split request

---

## Epic 4: Trust & Confirmation Workflow

Users can safely collaborate on expenses through a confirmation system that ensures transparency and prevents unauthorized changes.

### Story 4.1: Creator-Only Edit Restriction

As a **system**,
I want to ensure only the expense creator can edit expense details,
So that unauthorized changes are prevented and trust is maintained.

**Acceptance Criteria:**

**Given** an expense exists with a specific creator
**When** a user attempts to edit the expense
**Then** the API checks if the user_id matches the `created_by` field
**And** if the user is not the creator, a 403 Forbidden error is returned
**And** the error message clearly states: "Only the expense creator can edit this expense"
**And** the frontend disables edit buttons for non-creators
**And** the restriction is enforced on the backend, not just frontend

### Story 4.2: Expense Confirmation Workflow

As a **group member**,
I want to review and confirm expenses I'm involved in,
So that I agree with the charges before they become official debt.

**Acceptance Criteria:**

**Given** an expense has been created with splits
**When** I am listed as owing money in the split
**Then** the expense status is "pending_confirmation" for me
**And** I see the expense in my "Pending Confirmation" list
**And** I can view full details: amount owed, total, payer, description, split breakdown
**And** I can "Confirm" or "Reject" the expense
**And** if I confirm, my confirmation is recorded: `{expense_id, user_id, confirmed_at}`
**And** the endpoint: `POST /api/v1/expenses/{expense_id}/confirm`

### Story 4.3: Finalize Expense After All Confirmations

As a **system**,
I want to automatically finalize an expense when all involved members confirm,
So that the debt becomes official and tracking begins.

**Acceptance Criteria:**

**Given** an expense is pending confirmation from multiple members
**When** the last required member confirms
**Then** the expense status changes from "pending_confirmation" to "confirmed"
**And** the confirmed debts are now visible in net balance calculations
**And** the expense timestamp is updated: `confirmed_at`
**And** a confirmation event is published: `billing.expense.confirmed` (Redis Pub/Sub)
**And** all group members receive a notification that the expense is finalized

### Story 4.4: Immutable Audit Log for All Actions

As a **system**,
I want to record every expense-related action in an immutable audit log,
So that there is a complete, transparent history of all changes.

**Acceptance Criteria:**

**Given** any expense mutation occurs (create, edit, confirm, settle)
**When** the action is processed
**Then** an audit log entry is created in the `audit_logs` table
**And** the log includes: `{id, expense_id, user_id, action_type, changes_json, timestamp}`
**And** action_type values: "created", "edited", "confirmed", "settled", "rejected"
**And** changes_json stores before/after values for edits
**And** audit logs are write-only (no delete/update operations allowed)
**And** logs are indexed by expense_id for fast retrieval

### Story 4.5: Activity Feed Display

As a **group member**,
I want to view an activity feed showing all expense changes,
So that I can see who did what and when for transparency.

**Acceptance Criteria:**

**Given** I am viewing a group or specific expense
**When** I access the activity feed
**Then** I see a chronological list of all actions from the audit log
**And** each entry shows: user name, action, timestamp, and relevant details
**And** entries are formatted clearly: "Alex created expense 'Lunch' for $60" or "Sam confirmed their share"
**And** the feed is paginated (20 entries per page)
**And** the API endpoint: `GET /api/v1/expenses/{expense_id}/activity` or `GET /api/v1/expense-groups/{group_id}/activity`

---

## Epic 5: Settlement & Payment Tracking

Users can mark debts as settled and owners can confirm settlements, with a clear audit trail of all payment activities.

### Story 5.1: Mark Debt as Settled (Claim Payment)

As a **debt payer**,
I want to mark a debt as "settled" after I've paid,
So that I can notify the expense creator that payment is complete.

**Acceptance Criteria:**

**Given** I owe money on a confirmed expense
**When** I click "Mark as Settled"
**Then** a settlement claim is created in `settlement_claims` table
**And** the claim includes: `{id, expense_id, user_id, amount, status: "pending", claimed_at}`
**And** the claim status is "pending" until the expense owner confirms
**And** I see the expense in my "Pending Settlement Confirmation" list
**And** the API endpoint: `POST /api/v1/expenses/{expense_id}/settle`

### Story 5.2: Owner Confirms Settlement

As an **expense creator (owner)**,
I want to confirm that I received payment,
So that the debt is officially cleared from the system.

**Acceptance Criteria:**

**Given** someone has marked their debt as settled
**When** I review the settlement claim
**Then** I see the claim details: who paid, amount, when claimed
**And** I can "Confirm" or "Reject" the settlement
**And** if I confirm, the settlement status changes to "confirmed"
**And** the debt is removed from balance calculations
**And** the settlement is recorded in the audit log
**And** the API endpoint: `POST /api/v1/settlement-claims/{claim_id}/confirm`

### Story 5.3: Settlement Audit Trail

As a **group member**,
I want to see a clear record of all settlements,
So that I can verify payment history and resolve disputes.

**Acceptance Criteria:**

**Given** settlements have occurred in my group
**When** I view the settlement history
**Then** I see all settlement claims with their status (pending, confirmed, rejected)
**And** each entry shows: payer, amount, claim date, confirmation date, status
**And** the history is part of the activity feed
**And** settled expenses are marked with a "Settled" badge in the UI
**And** the API endpoint returns settlement data: `GET /api/v1/expense-groups/{group_id}/settlements`

---

## Epic 6: Agentic Notifications & Nudges

Users receive intelligent, context-aware reminders about outstanding debts and can manage notification preferences without feeling nagged.

### Story 6.1: Background Job Infrastructure (Celery)

As a **system**,
I want to set up Celery workers for background task processing,
So that notifications can be scheduled and sent asynchronously.

**Acceptance Criteria:**

**Given** the FastAPI backend is running
**When** Celery worker is started with Redis as the broker
**Then** the worker connects successfully to Redis
**And** Celery is configured in `backend/app/core/celery.py`
**And** a sample task can be queued and executed
**And** task results are stored in Redis
**And** the worker can be run via Docker: `docker-compose up celery-worker`

### Story 6.2: Schedule Level 1 Notifications (Initial Reminder)

As a **system**,
I want to send a gentle initial reminder 24 hours after an expense is confirmed,
So that borrowers are informed about their outstanding debts.

**Acceptance Criteria:**

**Given** an expense is confirmed with outstanding debts
**When** 24 hours have passed since confirmation
**Then** a Celery task is triggered to send Level 1 notification
**And** the notification is sent to all members who owe money and haven't settled
**And** the message is informative: "Reminder: You have a pending balance of $X with [Group Name]"
**And** notification is delivered via email or in-app notification
**And** a `notifications` table tracks: `{id, user_id, expense_id, level, sent_at, status}`

### Story 6.3: Schedule Level 2 Notifications (Contextual Nudge)

As a **system**,
I want to send a more direct reminder 3 days after an expense is confirmed if still unpaid,
So that borrowers are gently nudged to settle.

**Acceptance Criteria:**

**Given** an expense remains unsettled 3 days after confirmation
**When** the scheduled time arrives
**Then** a Level 2 notification is sent
**And** the message is contextual: "Sam, just a heads up, Alex settled the dinner bill" (as per PRD)
**And** the message feels helpful, not demanding
**And** the notification level is stored in the database
**And** users who have already settled do not receive the notification

### Story 6.4: Snooze Notification

As a **debt payer**,
I want to snooze a notification for a specific period,
So that I can defer reminders without being nagged repeatedly.

**Acceptance Criteria:**

**Given** I receive a notification about an outstanding debt
**When** I click "Snooze" and select a duration (1 day, 3 days, 1 week)
**Then** the notification is marked as snoozed until the selected time
**And** no further notifications are sent for that expense during the snooze period
**And** after the snooze period ends, normal notification schedule resumes
**And** the snooze is stored: `{notification_id, snoozed_until}`
**And** the API endpoint: `POST /api/v1/notifications/{notification_id}/snooze`

### Story 6.5: Settlement Cycle Configuration

As a **user**,
I want to configure a weekly settlement cycle (e.g., every Thursday),
So that I receive one summary instead of daily reminders.

**Acceptance Criteria:**

**Given** I have notification preferences
**When** I enable "Settlement Cycle" and select a day (e.g., Thursday)
**Then** daily individual notifications are suppressed
**And** instead, I receive a single summary notification on the selected day
**And** the summary lists all outstanding debts with totals
**And** the preference is stored in user settings: `{user_id, settlement_cycle_enabled, settlement_day}`
**And** the Celery task respects this preference when scheduling
**And** the API endpoint: `PUT /api/v1/users/me/notification-preferences`

---

## Epic 7: Offline Capability & Sync

Users can view balances and create expenses even without internet connectivity, with automatic synchronization when connection returns.

### Story 7.1: Configure TanStack Query with Persistence

As a **frontend developer**,
I want to set up TanStack Query with persistence plugin,
So that cached data is available offline.

**Acceptance Criteria:**

**Given** TanStack Query is installed
**When** I configure the persistence plugin with IndexedDB
**Then** all query data is automatically cached locally
**And** cached data persists across browser sessions
**And** the cache is restored on app load even when offline
**And** stale data is indicated with a visual badge ("offline mode")
**And** the configuration is in `frontend/src/shared/api/queryClient.ts`

### Story 7.2: View Balances Offline (Read-Only)

As a **user**,
I want to view my group balances and expense history when offline,
So that I can check what I owe without internet.

**Acceptance Criteria:**

**Given** I have previously loaded my dashboard while online
**When** I go offline and open the app
**Then** I see my cached dashboard data (groups, balances, expenses)
**And** the UI shows a banner: "Offline Mode - Data may be outdated"
**And** navigation between cached pages works smoothly
**And** data remains accessible even after closing and reopening the browser
**And** no API calls are made (checked via network tab)

### Story 7.3: Create Expense Offline with Mutation Queue

As a **user**,
I want to create a manual expense while offline,
So that I can record expenses immediately even without connectivity.

**Acceptance Criteria:**

**Given** I am offline
**When** I create an expense via manual entry (not AI parsing)
**Then** the expense is stored in a local mutation queue
**And** the UI shows optimistic update (expense appears in list)
**And** a "pending sync" indicator is shown on the expense
**And** the mutation queue is persisted in IndexedDB
**And** AI parsing is disabled/grayed out with message "Available when online"

### Story 7.4: Sync Offline Changes on Reconnection

As a **system**,
I want to automatically sync queued mutations when connection is restored,
So that offline-created expenses are saved to the server.

**Acceptance Criteria:**

**Given** I have queued mutations while offline
**When** my internet connection is restored
**Then** TanStack Query automatically detects the connection
**And** all queued mutations are sent to the server in order
**And** successful syncs update the local cache and remove "pending sync" badge
**And** failed syncs (e.g., due to conflicts) show error messages
**And** the user is notified: "Synced X expenses successfully"

### Story 7.5: Conflict Resolution - Reject Unauthorized Edits

As a **system**,
I want to reject offline edits to expenses not owned by the user,
So that creator-only restrictions are enforced even during sync.

**Acceptance Criteria:**

**Given** a user attempts to edit an expense they didn't create while offline
**When** the sync occurs
**Then** the server validates the `created_by` field
**And** edits from non-creators are rejected with 403 error
**And** the rejected changes are shown to the user with explanation
**And** the user can choose to "Discard" the rejected local change
**And** legitimate changes (user's own expenses) sync successfully
