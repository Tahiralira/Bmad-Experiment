---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: ['c:/Users/aheedtahir/Bmad-Experiment/ClearDues/PRD.md', 'c:/Users/aheedtahir/Bmad-Experiment/_bmad-output/analysis/brainstorming-session-2026-01-05.md']
date: 2026-01-05
author: Aheedtahir
---

# Product Brief: ClearDues

## Executive Summary

ClearDues is an AI-powered "Agentic Mediator" designed to eliminate the social friction of shared expenses. Unlike traditional tools that merely track debts, ClearDues actively manages the lifecycle of a shared expense—from unstructured conversational input to payment settlement—acting as a neutral third party to handle the awkwardness of reminders ("nagging") and the complexity of splits.

---

## Core Vision

### Problem Statement

Managing shared emotions is harder than managing shared math. Users dread the "admin" of expense tracking not because subtraction is difficult, but because "begging" friends for money is socially awkward, reminders feel like harassment, and lack of closure creates anxiety.

### Problem Impact

This friction leads to uncollected debts, strained relationships ("money ruins friendships"), and eventual abandonment of tracking tools in favor of "letting it slide," which causes long-term resentment.

### Why Existing Solutions Fall Short

Current apps are passive ledgers. They require manual data entry (high operational friction) and force users to be the "enforcer" for collections (high social friction). They track *what* is owed, but fail to facilitate the *repayment*.

### Proposed Solution

A "Neutral Mediator" Agent that:
1.  **Accepts Natural Language:** "Paid 150 for dinner, exclude Tom" (Removes entry friction/math).
2.  **Automates the Nag:** Uses "Progressive Escalation" (Informative -> Contextual -> Social Pressure) to chase payments.
3.  **Ensures Trust:** Provides visible audit trails so users trust the AI's math.

### Key Differentiators

*   **Agentic Mediation:** The system, not the user, chases the money.
*   **Progressive Urgency:** Notifications evolve to match the context (freeing the lender from being the "bad guy").
*   **Payment = Silence:** Immediate closure and dopamine ("Settled").

## Target Users

### Primary Users

#### 1. "The Organizer" (The Lender)
*   **Role:** The person who pays the bill and manages the mental load of recovery.
*   **Pain Point:** Social friction of asking for money; feeling like a nag.
*   **Motivation:** Wants quick settlement without damaging relationships.
*   **Key Interaction:** Wants frictionless, natural language input ("Paid 150...").

#### 2. "The Borrower" (The Forgetful Friend)
*   **Role:** The person who owes money but procrastinates or forgets.
*   **Pain Point:** Anxiety from unstructured debts; irritation from constant reminders.
*   **Motivation:** Wants a neutral system to tell them *exactly* what to pay and when.
*   **Key Interaction:** Respond to "Progressive Escalation" notifications; seeks "Payment = Silence."

### Secondary Users (Roles & Constraints)

#### 1. "The Group Creator" (Transient Role)
*   **Definition:** The Organizer at the moment of group setup.
*   **Function:** Sets the "Social Contract" (Reminder strictness, Mutual Awareness).
*   **Constraint:** *Do not build complex admin dashboards.* This is a one-time setup action.

#### 2. "The Passive Member" (Retention Risk)
*   **Definition:** Members who rarely add expenses or owe large amounts.
*   **Risk:** They perceive the app as "noisy" and are the first to uninstall.
*   **Design Rule:** *Design to NOT annoy them.* Minimal notifications, clear summaries, no forced engagement.

## Success Metrics

### User Success (Trust & Efficiency)
*   **Speed to Done:** Time from *Chat Input* to *Expense Confirmed* < 15 seconds. (User spends time *verifying*, not *entering*).
*   **Trust Score (The "Lazy Metric"):** Edit Rate on AI extractions < 10%. (Users trust the auto-split without manual correction).

### Business Objectives (Retention)
*   **Relationship Health:** "Settlement Velocity" (Average days to settle) improves by 20% vs. estimated manual baseline.
*   **Core Loop:** ≥ 1 Group Created per active user (Viral coefficient proxy).

### Key Performance Indicators
1.  **Extraction Accuracy:** % of "Complex Natural Language" inputs parsed correctly on first try.
2.  **Escalation Efficacy:** % of debts settled after "Level 2" notification (Contextual Reminder) preventing social friction.

## MVP Scope

### Core Features (The "Core 3")
1.  **Smart Input:** LLM-powered parsing of natural language text to structured expense data (Gemini/GROQ).
2.  **Social Engine:** Progressive Notification Logic (Level 1 -> 3) to automate the "nag."
3.  **Trust Architecture:** Visible Audit Trail for every AI calculation & "Edit" history.
4.  **Foundational:** User Auth (Email/OAuth), Group Management, & Basic Balances (Net Dues).

### Out of Scope for MVP (The "Trap" Avoidance)
*   **Payment Processing:** We track debts, we do not move money (No Stripe/Venmo integration).
*   **Bank Sync:** No Plaid integration. Rely on user input/evidence.
*   **Complex Analytics:** No "Spending Trends" or charts.
*   **Multi-Currency:** Single currency per group to capture 90% of use cases without engineering overhead.

### MVP Success Criteria
*   Validated user trust (low edit rate) and improved settlement times (velocity).
*   Technical stability of the NLP extraction pipeline (>90% accuracy).

### Future Vision
*   **Automated Settlement:** Integration with payment providers for 1-click settle.
*   **Visual Evidence:** Receipt scanning/OCR (from the Brainstorming "Nice-to-Have").
*   **Travel Mode:** Multi-currency support for trip groups.

<!-- Content will be appended sequentially through collaborative workflow steps -->
