#  Product Requirements Document (PRD)

## Product Name (Working)

**ClearDues** (placeholder)

> *An AI-powered expense agent that tracks, explains, and settles shared finances.*

---

#  1. Product Vision

### Problem

Managing expenses—especially shared ones—is mentally taxing, socially awkward, and operationally inefficient. Existing apps track numbers but don’t **manage coordination, intent, or closure**.

### Solution

An **agentic expense management platform** that:

* Understands expenses via conversation
* Manages shared groups intelligently
* Drives settlements to completion
* Uses **user-provided AI APIs** to stay free and scalable

---

#  2. Target Users

### MVP Target

* Tech-savvy individuals
* Flatmates, couples, small groups, friends, office colleageus
* Early adopters comfortable with AI concepts

### Full Product Target

* General consumers
* Households
* Travel groups
* Teams & contractors

---

#  3. Core Value Proposition

> “Tell it what happened. It handles the rest.”

---

#  PART A — MVP PRD

##  MVP Goal

Prove that:

1. Conversational expense input reduces friction
2. AI-managed groups reduce conflict
3. Users are willing to bring their own AI key

---

##  MVP Feature Set

###  User Accounts

**Requirements**

* Email / OAuth login
* Profile (name, currency, timezone)
* API key storage (Gemini + GROQ)

**Acceptance Criteria**

* User can log in and use manual features without AI
* API keys are encrypted and never exposed

---

###  BYO-AI Setup

**Requirements**

* Select AI provider (Gemini / GROQ)
* Paste API key
* Test connection
* Show quota + last usage

**Non-Goals (MVP)**

* Auto key provisioning
* Paid AI plans

---

###  Conversational Expense Input

**Requirements**

* Chat interface
* User can type:

  * “Paid $120 for groceries for me and Sam” (Selectable Currency, can be pak rupees)
* AI extracts:

  * Amount
  * Participants
  * Category
  * Split

**Fallback**

* Manual expense form if AI unavailable

---

###  Groups & Shared Expenses

**Requirements**

* Create group (Admin Roles , not anyone can just join or add others etc)
* Add members
* Add shared expenses
* Auto-split equally by default
* View balances per member

---

###  Balance & Dues Tracking

**Requirements**

* Per-group balances
* Who owes whom
* Net balance calculation

**Non-Goals**

* Payment processing
* Bank sync

---

###  AI Quota Exhaustion Handling

**Requirements**

* Detect quota exhaustion
* Gracefully disable AI
* Display:

  * Reason
  * Reset estimate
* Manual mode continues

---

##  MVP Non-Functional Requirements

| Area        | Requirement                |
| ----------- | -------------------------- |
| Security    | Encrypt API keys           |
| Privacy     | No training on user data   |
| Performance | Chat response < 3s         |
| Reliability | Manual flows never blocked |

---

##  MVP Success Metrics

* Expense added in < 30 seconds
* ≥ 60% users enable AI
* ≥ 3 expenses added in first session
* ≥ 1 group created per active user

---