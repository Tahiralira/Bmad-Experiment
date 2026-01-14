# Design Artifact Execution Plan

**Created:** 2026-01-14
**Purpose:** Parallel track plan for wireframes, interactive prototypes, and Figma high-fidelity designs

---

## Overview

Design artifacts run as a **parallel track** alongside development. They do NOT block Epic 2.5 or Epic 3 but enhance quality and enable user testing.

```
Development Track:     Epic 2.5 ──────────► Epic 3 ──────────► Epic 4+
                          │                   │                   │
Design Track:          Wireframes ──► Prototype ──► Figma Hi-Fi ──► Handoff
                          │                   │
                       (P0 screens)     (user testing)
```

---

## Phase 1: Wireframes (During Epic 2.5)

**When:** Start immediately, complete during Epic 2.5 development
**Tool:** Excalidraw (via `/bmad:bmm:workflows:create-excalidraw-wireframe`)
**Output:** Low-fidelity wireframes showing layout, component placement, and flow

### Priority P0 Wireframes (Must Have)

| Screen | Key Elements | Reference |
|--------|--------------|-----------|
| **Dashboard with Group Cards** | Total balance, group card stack, Agent Orb position | UX Spec: Design Direction |
| **Group View with Chat Feed** | Header, balance, chat-style expense feed, + button | UX Spec: Journey 1 |
| **Smart Input Modal** | NL input, AI bubble, preview card, group selector | UX Spec: Smart Input Component |
| **Agent Orb + Orbital Nav** | Orb states, orbital positions, animation frames | UX Spec: Navigation Patterns |

### Priority P1 Wireframes (Should Have)

| Screen | Key Elements | Reference |
|--------|--------------|-----------|
| **Expense Card (Swipeable)** | Card layout, swipe reveal zones, action buttons | UX Spec: Swipeable Card |
| **Settlement Flow** | Mark Paid, awaiting confirmation, completion states | UX Spec: Journey 2 |
| **Edit Expense Modal** | Split picker cards, member chips, inline editing | UX Spec: Journey 3 |

### Priority P2 Wireframes (Nice to Have)

| Screen | Key Elements | Reference |
|--------|--------------|-----------|
| **Empty States** | Zero balance celebration, no groups, no expenses | UX Spec: Empty States |
| **Settings/Profile** | Notification preferences, account settings | Standard patterns |

### Execution Commands

```bash
# For each wireframe, run:
/bmad:bmm:workflows:create-excalidraw-wireframe

# Specify the screen name and reference UX spec sections
```

---

## Phase 2: Interactive Prototype (After Epic 2.5, During Epic 3)

**When:** After wireframes approved, during Epic 3 development
**Tool:** Figma (prototyping mode) or ProtoPie for advanced animations
**Output:** Clickable prototype for user testing

### Prototype Flows (in priority order)

| Flow | Screens Involved | Key Interactions |
|------|------------------|------------------|
| **Add Expense (Orb → Modal → Confirm)** | Dashboard, Smart Input Modal, Group View | Tap Orb, streaming text animation, preview card, confirm |
| **Orbital Navigation** | Any screen with Orb | Expand/collapse animation, icon hover states |
| **Settlement Flow** | Group View, Expense Card | Swipe gesture simulation, fade-out on confirm |
| **Error Correction** | Smart Input Modal, Edit Modal | Inline edit, modal edit transitions |

### User Testing Plan

**Test participants:** 3-5 target users (Organizers and Borrowers)
**Test duration:** 15-20 minutes per user
**Test tasks:**
1. Add an expense using natural language
2. Navigate between Home and Groups
3. Mark a debt as paid
4. Edit an incorrectly parsed expense

**Success metrics:**
- Task completion rate > 90%
- Time to add expense < 20 seconds
- Zero navigation confusion

---

## Phase 3: Figma Visual Design (During Epic 3-4)

**When:** After prototype validated, parallel with Epic 3-4
**Tool:** Figma
**Output:** High-fidelity designs with design system documentation

### Figma File Structure

```
ClearDues Design System (Figma)
├── 🎨 Foundations
│   ├── Colors
│   │   ├── Light Mode Palette
│   │   └── Dark Mode Palette
│   ├── Typography
│   │   └── Inter font scale (display → caption)
│   ├── Spacing & Layout
│   │   └── 4px grid system
│   └── Effects
│       └── Shadows (sm, md, lg)
│
├── 🧩 Components
│   ├── Agent Orb
│   │   ├── States (idle, hover, pressed, processing, success)
│   │   └── Animation specs
│   ├── Orbital Nav
│   │   ├── Expanded state
│   │   └── Icon variants
│   ├── Smart Input
│   │   ├── Input field
│   │   ├── AI commentary bubble
│   │   └── Preview card
│   ├── Swipeable Card
│   │   ├── Default state
│   │   ├── Swipe reveal (left/right)
│   │   └── Action buttons
│   ├── Balance Display
│   │   └── Size variants (display, title, body)
│   ├── Member Chips
│   │   ├── Included state
│   │   └── Excluded state
│   ├── Split Picker
│   │   └── Card variants (Equal, Unequal, Percentage, Shares)
│   └── [shadcn overrides]
│       └── Button, Input, Card customizations
│
├── 📱 Screens - Mobile (<640px)
│   ├── Dashboard
│   ├── Group View
│   ├── Smart Input Modal
│   ├── Edit Expense Modal
│   └── Settings
│
├── 💻 Screens - Desktop (>1024px)
│   └── Responsive variants of all screens
│
└── 🔄 Prototypes
    ├── Add Expense Flow
    ├── Settlement Flow
    └── Navigation Flow
```

### Design Token Documentation

Include in Figma:
- Color variables with semantic names
- Typography styles with usage guidelines
- Spacing scale with examples
- Component variants with state documentation

---

## Phase 4: Developer Handoff (Before Epic 5)

**When:** Before starting Epic 5
**Tool:** Figma Inspect mode
**Output:** Exportable assets, CSS values, interaction specs

### Handoff Checklist

- [ ] All components have inspect-ready styles
- [ ] Animation timing documented (duration, easing)
- [ ] Assets exported (SVG icons, optimized images)
- [ ] Responsive breakpoints documented
- [ ] Interaction states fully specified
- [ ] Accessibility requirements noted per component

---

## Timeline Summary

| Phase | Starts | Ends | Blocking? |
|-------|--------|------|-----------|
| **Wireframes** | Now | End of Epic 2.5 | No |
| **Prototype** | After Epic 2.5 | Mid-Epic 3 | No |
| **User Testing** | After prototype | Before Epic 4 | Soft (informs iteration) |
| **Figma Hi-Fi** | During Epic 3 | End of Epic 4 | No |
| **Handoff** | Before Epic 5 | Before Epic 5 | Yes (for polish stories) |

---

## Execution Commands

### Create Wireframes

```bash
# Dashboard wireframe
/bmad:bmm:workflows:create-excalidraw-wireframe
# Describe: "ClearDues Dashboard with group cards, Agent Orb, warm minimal palette"

# Smart Input Modal wireframe
/bmad:bmm:workflows:create-excalidraw-wireframe
# Describe: "ClearDues Smart Input Modal with NL input, AI bubble, preview card"
```

### Create Diagrams (optional)

```bash
# User flow diagram
/bmad:bmm:workflows:create-excalidraw-flowchart
# Describe: "Add Expense user flow from Dashboard to confirmation"

# Component hierarchy
/bmad:bmm:workflows:create-excalidraw-diagram
# Describe: "ClearDues component architecture showing Orb, Orbital Nav, Smart Input relationships"
```

---

## Next Actions

1. **Immediate:** Create P0 wireframes (Dashboard, Smart Input, Agent Orb)
2. **During Epic 2.5:** Finalize all P0/P1 wireframes
3. **After Epic 2.5:** Build clickable prototype
4. **During Epic 3:** User testing + Figma hi-fi
5. **Before Epic 5:** Complete developer handoff
