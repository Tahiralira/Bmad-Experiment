---
stepsCompleted: [1, 2, 3, 4, 6, 7, 8, 9, 10, 11]
inputDocuments: ['c:/Users/aheedtahir/Bmad-Experiment/_bmad-output/planning-artifacts/product-brief-ClearDues-2026-01-05.md', 'c:/Users/aheedtahir/Bmad-Experiment/_bmad-output/analysis/brainstorming-session-2026-01-05.md', 'c:/Users/aheedtahir/Bmad-Experiment/ClearDues/PRD.md']
workflowType: 'prd'
lastStep: 10
briefCount: 1
researchCount: 0
brainstormingCount: 1
projectDocsCount: 1
---

# Product Requirements Document - ClearDues

**Author:** Aheedtahir
**Date:** 2026-01-05

## Executive Summary

ClearDues is an AI-powered "Agentic Mediator" designed to eliminate the social friction of shared expenses. It solves the awkwardness of "begging" friends for money by acting as a neutral third party that handles the entire lifecycle of a debt—from conversational input ("Paid 150 for dinner...") to final settlement. Unlike passive tracking tools, ClearDues actively manages the relationship health of the group.

### What Makes This Special

*   **Agentic Mediation:** The system chases the money, not the user.
*   **Progressive Urgency:** Notifications evolve from informative updates to social pressure based on time and context.
*   **Payment = Silence:** Immediate closure ensures the "Nag" stops exactly when it should.

## Project Classification

**Technical Type:** web_app (Mobile-First PWA)
**Domain:** fintech (Expense Management)
**Complexity:** medium
**Project Context:** Brownfield - extending existing system

**Classification Rationale:**
While purely financial apps are typically "High" complexity, the explicit exclusion of payment processing (Stripe/Venmo) and bank synchronization (Plaid) allows us to treat this as a "Medium" complexity Information System with a focus on UX and Logic rather than Regulatory Compliance.

## Success Criteria

### User Success
*   **Speed to Done:** Time from *Chat Input* to *Expense Confirmed* < 15 seconds.
*   **Trust Score:** Edit Rate on AI extractions < 10%.
*   **Offline Confidence:** Users can view balances and add manual expenses even without connectivity.

### Business Success
*   **Settlement Velocity:** Debts settled 20% faster than manual baseline.
*   **Viral Loop:** ≥ 1 Group Created per active user.

### Technical Success
*   **Performance:** Time to Interactive (TTI) < 2 seconds on 4G networks.
*   **Offline Capability:** "Read & Write" (Manual Entry) supported offline; AI features degrade gracefully.
*   **Extraction Accuracy:** >90% success rate on complex natural language inputs.

### Measurable Outcomes
*   **Escalation Efficacy:** % of debts settled via "Contextual Reminders" (Level 2) vs "Social Pressure" (Level 3).

## Product Scope

### MVP - Minimum Viable Product
*   **Core 3:** Smart Input (NLP), Social Engine (Escalation), Trust Architecture (Audit).
*   **Offline Mode:** Manual expense entry + Read-only access to balances.
*   **Platform:** Mobile-First PWA.

### Growth Features (Post-MVP)
*   **Visual Evidence:** Receipt Scanning / OCR.
*   **Settlement Integration:** Deep links to Payment Apps (Venmo/UPI).
*   **Export:** PDF/CSV export for group archives.

### Vision (Future)
*   **Travel Mode:** Multi-currency support for trip groups.
*   **Full Agent:** Automated settlement and "Financial Diplomat" for all shared finances.

## User Journeys

### Journey 1: Alex (The Organizer) - "The Frictionless Entry"
Alex pays $120 for a group dinner. Usually, he'd dread the "admin," but he opens ClearDues and types: *"Paid 120 for dinner, exclude Tom."*
*   **The Scalable Moment:** The AI parses this in <2s, instantly handles the "Exclude" logic, and presents a draft.
*   **Outcome:** Alex hits "Confirm" in under 10 seconds total. He feels *relief*, not "admin fatigue."

### Journey 2: Sam (The Borrower) - "The Gentle Nudge"
Sam forgot to pay Alex. In a typical app, he'd get a generic spam notification. In ClearDues:
*   **Day 3:** He gets a "Level 2" context notification: *"Sam, just a heads up, Alex settled the dinner bill."*
*   **Action:** It feels helpful, not demanding. He taps "Mark Paid."
*   **Outcome:** The "Nag" stops immediately. The friendship remains awkward-free.

### Journey 3: Alex (The Correction) - "Scalable Trust"
*Scenario:* The AI mistakenly splits the bill 4 ways instead of 3.
*   **The Conflict:** Alex notices the bad math.
*   **The Fix:** He taps "Edit Split" -> "Equally between 3". The system recalculates *instantly* and updates the audit trail: *"User Manual Override: Split Logic."*
*   **Scalability Win:** The system accepts the correction gracefully, logs the logic change, and ensures the ledger remains balanced. The user trusts the tool *more* because it handled the error transparently.

### Journey Requirements Summary
*   **NLP Pipeline:** Capability to parse "Exclude/Split" logic (Journey 1).
*   **State Machine:** Notification engine that tracks "Nag Level" per debt (Journey 2).
*   **Atomic Transactions:** Ability to revert/edit a split without corrupting group balances (Journey 3).

## Innovation & Novel Patterns

### Detected Innovation Areas
*   **Agentic Mediation (Active vs. Passive):** Shifting the burden of "Ask" from the user to the Agent. The system actively pursues debt resolution rather than just recording it.
*   **Payment = Silence (Value by Subtraction):** The core value proposition is the *removal* of notifications and social noise. Success is defined by the absence of interaction (peace of mind).

### Market Context & Competitive Landscape
*   **Landscape:** Incumbents (Splitwise, Tricount) act as passive "Shared Ledgers" or data entry tools. They rely on users to check balances.
*   **Differentiation:** ClearDues introduces an *active participant* (the Agent) into the group dynamic, changing the social contract.

### Validation Approach
*   **Hypothesis:** Users will prefer a "Nudging Agent" over direct confrontation.
*   **Metric:** "Escalation Efficacy" - measuring the success rate of Level 2 (Gentle) vs Level 3 (Firm) reminders.
*   **Stop Signal:** High "Mute/Block" rates on Agent notifications would invalidate the "Friendly Nudge" hypothesis.

### Risk Mitigation
*   **Risk:** "Bot Annoyance" - The Agent becomes irritating rather than helpful.
*   **Mitigation:** "Contextual Awareness" - limiting notifications based on time, location, and user interaction history (e.g., no nags during work hours).
*   **Fallback:** Users can throttle or mute the Agent, reverting to a passive "Ledger Mode" (MVP fallback).

## Web App Specific Requirements

### Project-Type Overview
ClearDues will be a **Real-Time PWA** built with a **Python Backend**. It requires persistent WebSocket connections for instant collaboration ("Chat" and "Split Updates") and maintains a strict "Walled Garden" security model.

### Technical Architecture Considerations
*   **Backend Language:** Python (likely FastAPI/Django Channels) to support async high-concurrency for real-time features.
*   **Real-Time Protocol:** WebSockets (wss://) required for:
    *   Instant Bill Splitting (User A edits, User B sees change immediately).
    *   Chat Stream (Agent interactions).
*   **Browser Support:** Mobile-First focus (Touch targets, Viewport usage) but functional on Desktop (Responsive Design).

### Implementation Considerations
*   **Authentication:** "Walled Garden" - No public routes. JWT/OAuth required immediately upon entry.
*   **Offline Strategy:** Optimistic UI updates (Client assumes success) with background Python API sync when connection restores.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Platform MVP
**Philosophy:** Build a robust, scalable foundation (Real-Time Python Backend) immediately to support high-concurrency interaction, rather than a throwaway prototype. We accept a slightly higher initial build cost for zero technical debt during the "Growth" phase.
**Resource Requirements:** Small technical team (1-2 devs) with strong Python/Async experience.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
*   Journey 1: Frictionless Entry (Organizer)
*   Journey 2: Gentle Nudge (Borrower - Level 1/2)
*   Journey 3: Correction & Scalability (Trust)

**Must-Have Capabilities:**
*   **Real-Time Sync:** WebSockets for instant updates.
*   **NLP Engine:** Text-to-Transaction parsing (Expense, Amount, Split).
*   **Trust Architecture:** Immutable Audit Trail for every action.
*   **Offline Mode:** Optimistic UI with background sync.

### Post-MVP Features

**Phase 2 (Growth):**
*   **Visual Evidence:** OCR / Receipt Scanning.
*   **Social Escalation:** Level 3 "Social Pressure" notifications.
*   **Complex Graphs:** Visualization of debt networks.

**Phase 3 (Expansion):**
*   **Financial Agent:** Automated Settlement integrations (Venmo/UPI deep links).
*   **Travel Mode:** Multi-currency support.
*   **Auto-Settle:** Rules for automatic debt resolution.

### Risk Mitigation Strategy

**Technical Risks:**
*   *Risk:* Real-time sync complexity.
*   *Mitigation:* Use established library (e.g., FastAPI + Socket.IO) rather than rolling custom WebSocket handling.

**Market Risks:**
*   *Risk:* Users ignore "Gentle Nudges".
*   *Mitigation:* Monitor "Settlement Velocity" closely in MVP. If slow, prioritize Phase 2 "Social Pressure" features earlier.

## Functional Requirements

### User & Group Management
*   **FR1:** User can authenticate via keyless entry (Magic Link/OTP) or Social Auth.
*   **FR2:** User can create a Group and invite others via a deep link.
*   **FR3:** User can view a dashboard of "Net Balances" across all groups.

### Expense Input & Processing
*   **FR4:** User can input expenses via natural language text (e.g., "Paid 60 for lunch") or simple numeric strings.
*   **FR5:** System must parse [Amount], [Payer], [Payee(s)], and [Description] from text input.
*   **FR6:** User can manually override/edit the System's parsed output before saving.

### Transaction Logic & Workflow
*   **FR7:** User can specify split logic: "Equal", "Unequal", "Percentage", or "Shares".
*   **FR8:** User can "Exclude" specific group members from a transaction.
*   **FR9:** **(Restriction):** Only the *Creator* of an expense can edit its details.
*   **FR10:** **(Confirmation):** Involved members must "Confirm" an expense before it is finalized as debt.

### Agentic Notification & Settlement
*   **FR11:** System must schedule "Nudge" notifications based on debt age (Level 1/2).
*   **FR12:** User can "Snooze" a notification.
*   **FR13:** User can "Mark as Settled" (claim payment).
*   **FR14:** **(Confirmation):** Expense Owner must "Confirm" a settlement claim before the debt is cleared.
*   **FR19:** User can configure a "Settlement Cycle" (e.g., Weekly on Thursdays) to suppress daily nags and trigger a "Settlement Day" summary.

### Trust & Audit
*   **FR15:** System must record an immutable "Audit Log" for every creation, edit, confirmation, and settlement.
*   **FR16:** User can view the "Activity Feed" showing who changed what and when.

### Offline & Sync
*   **FR17:** User can create/edit expenses while offline (stored locally).
*   **FR18:** System must sync local changes to the server upon reconnection, rejecting edits to records not owned by the user.

## Non-Functional Requirements

### Performance
*   **NFR1 (In-App Latency):** When User A edits a split, User B must see the update within **200ms** (via WebSockets).
*   **NFR2 (Load Time):** App must be interactive (TTI) within **1.5 seconds** on a standard 4G connection.
*   **NFR3 (AI Latency):** Simple text parsing ("Paid 50") must return a structured draft in under **2 seconds**.

### Security
*   **NFR4 (Encryption):** All financial data encrypted At Rest (AES-256) and In Transit (TLS 1.3).
*   **NFR5 (Rate Limiting):** API must reject aggressive scraping (>100 req/min) to protect backend costs.

### Reliability & Scalability
*   **NFR6 (Offline Durability):** Unsynced data must persist locally indefinitely (protecting against app closure before sync).
*   **NFR7 (Concurrency):** Backend MVP must support at least **1,000 concurrent WebSocket connections** without degradation.
