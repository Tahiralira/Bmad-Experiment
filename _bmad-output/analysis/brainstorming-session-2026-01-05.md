---
stepsCompleted: [1, 2, 3, 4]
session_active: false
workflow_completed: true
inputDocuments: []
session_topic: 'ClearDues - AI-powered expense agent'
session_goals: 'Define MVP features, Identify technical risks, Refine user flows for conversational expense input'
selected_approach: 'AI-Recommended Techniques'
techniques_used: []
ideas_generated: []
context_file: 'c:/Users/aheedtahir/Bmad-Experiment/_bmad/bmm/data/project-context-template.md'
---

# Brainstorming Session Results

**Facilitator:** Aheedtahir
**Date:** 2026-01-05

## Session Overview

**Topic:** ClearDues - AI-powered expense agent
**Goals:** Define MVP features, Identify technical risks, Refine user flows for conversational expense input

### Context Guidance

_Project Context: ClearDues - An agentic expense management platform._

### Session Setup

_Session initialized based on PRD analysis._

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** ClearDues - AI-powered expense agent with focus on MVP features, technical risks, and conversational flows

**Recommended Techniques:**

- **Role Playing (Empathy Mapping):** We'll step into the shoes of different "ClearDues" users (e.g., the person who always pays, the forgetful flatmate) to understand the emotional and practical friction of shared expenses.
- **SCAMPER Method:** We'll use this to innovate on standard expense tracking. Substitute manual entry with AI, Combine chat with ledger, etc.
- **Reverse Brainstorming (Pre-Mortem):** We'll actively try to "break" the system by asking how it could fail (e.g., privacy leaks, wrong splits) to build robust defenses.

**AI Rationale:** This sequence moves from **Understanding** (Role Play) to **Ideating** (SCAMPER) to **De-risking** (Pre-Mortem), perfectly matching your goals of defining a user-centric, robust MVP.

## Technique Execution Results

### 1. Role Playing (Empathy Mapping) - "The Organizer"

**User Insights & Pain Points:**
- **Social Friction:** The "begging" dynamic. Asking for money feels wrong/awkward. Reminders are irritating.
- **Ambiguity:** Lack of clear deadlines ("should be asap").
- **Operational Friction:** Manual data entry is a blocker. Needs to be "extreme ease of use" (e.g., just typing "150").
- **Complex Splits:** Needs to handle scenarios like "Member 2 pays 2 shares" without complex UI forms.
- **Agent Opportunity:** The Agent can take the "social hit" of nagging, removing the awkwardness between friends.
- **NLP Syntax Gold Standard:** "Paid 150 for dinner at roadhouse, exclude tom , add 2 for harry".
    - *Analysis:* "add 2" implicitly means "2 shares" or "2x weight". "Exclude" manages dynamic group participation.

### 2. Role Playing (Empathy Mapping) - "The Borrower"

**User Insights & Solutions:**
- **The "Neutral Mediator" Philosophy:** The app must be a neutral party, not an enforcer. "Social awareness is more effective than system nagging."
- **Notification Escalation Model (Progressive Urgency):**
    - *L1 (Day 0):* Informative ("You owe Alex..."). No pressure.
    - *L2 (Day 2-3):* Contextual ("Alex hasn’t received..."). Framed as upkeep.
    - *L3 (Day 5-7):* Social Friction ("Pending since 7 days" + Avatar). Creates passive discomfort.
    - *L4 (Opt-in):* Mutual Awareness ("Alex can see this...").
- **Key Features:**
    - **Payment = Silence:** Immediate cessation of reminders upon payment.
    - **Snooze with Accountability:** "Remind me after salary" (System: "You'll be reminded").
    - **Passive Pressure:** UI cues (Red dots, color changes) instead of spam updates.

### 3. SCAMPER Ideation (Substitute & Combine)

**Analysis of "Real-time" vs "Post-Event":**
- **Constraint:** Users typically track expenses *after* the event, not during payment. "Real-time balancing" (telling Tom to pay) requires a behavior change that might be too high friction for MVP.
- **S (Substitute):**
    - *Idea:* Substitute **App Interface** with **Chat Interface** (WhatsApp/Telegram). *Status: Nice-to-Have (Post-MVP)*.
    - *Idea:* Substitute **Manual Typing** with **Evidence** (Screenshots). *Status: Nice-to-Have (Post-MVP)*.
- **C (Combine):**
    - *Decision:* Calendar integration should be **Optional**. Not everyone wants their social calendar linked to finances.

### 4. Reverse Brainstorming (Pre-Mortem) - "Why ClearDues Failed"

**Critical Risks identified:**
- **Trust Failure:** AI Hallucination with *no explanation*. If users don't see "How amount was calculated" (Audit Trail), they leave.
- **Operational Failure:** AI Quota exhaustion -> "Costly" or "Broken" state.
- **Psychological Failure:** Lack of "Closure Dopamine." Failing to make users feel *Organized, Fair, Calm, Respected*.
- **Engagement Failure:** No "lightweight loops" or summary insights. Just raw data entry.

**Mitigation strategies implied:**
- **Visible Logic:** AI must show its work ("User A: $50 because X").
- **Audit Trail:** "Edits without visibility" is a killer. Every change needs a history.
- **Emotional Design:** Optimize for "Calm" and "Respect" (e.g., the notification model).

## Idea Organization and Prioritization

**Thematic Organization:**

*   **Theme 1: The "Smart Input" (Frictionless Entry)**
    *   *Core:* Natural Language Processing ("Paid 150, exclude tom...").
    *   *Support:* Implicit logic (Bot handling the math).
    *   *Closure:* Payment = Silence.

*   **Theme 2: The "Gentle Mediator" (Social Engineering)**
    *   *Core:* Progressive Escalation (Informative -> Contextual -> Social Friction).
    *   *Support:* Meaningful Snooze ("Remind me after salary").
    *   *Role:* Agent takes the "Social Hit".

*   **Theme 3: Trust Architecture (Anti-Failure)**
    *   *Core:* Visible Audit Trail (Explain *how* the split was calculated).
    *   *Support:* "Passive Pressure" UI cues.

**Prioritization Results (MVP Must-Haves):**

1.  **Natural Language Processing:** The primary interface for reducing input friction.
2.  **Progressive Escalation:** The core differentiator for "Agentic" vs. "Static" expense tracking.
3.  **Visible Audit Trail:** The critical trust layer to prevent abandonment due to "hallucination fear".

**Action Planning:**

*   **Natural Language Processing:**
    *   *Next Step:* Define "Golden Test Set" of 20 complex phrases (e.g., "split 2:1", "exclude X").
    *   *Metric:* 100% extraction accuracy on test set.
*   **Progressive Escalation:**
    *   *Next Step:* Map notification state machine (Day 0 -> Day 7). Write copy for each level.
    *   *Metric:* Notification logic fires correctly in scenarios.
*   **Visible Audit Trail:**
    *   *Next Step:* Design "Expense Detail" view to show `Calculation Logic` text.
    *   *Metric:* User can trace every split amount to a rule.

## Session Summary and Insights

**Key Achievements:**
- Defined a **Human-Centric MVP** focused on social friction, not just math.
- Identified the **"Golden Standard"** for input (NLP) and notification (Escalation).
- De-risked the project by identifying the **"Trust Gap"** and solving it with Audit Trails.

**Session Reflections:**
This session moved ClearDues from a generic "Expense Bot" to a socially intelligent "Agentic Mediator." The focus on *feeling* (Calm, Respected) vs. *doing* (Tracking) is the key differentiator.
