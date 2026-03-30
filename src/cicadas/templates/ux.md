
---
summary: "{One tight paragraph summarizing the intended builder or end-user experience, key interaction goals, and main UX constraints. Keep it compact enough to reuse at later workflow boundaries.}"
phase: "ux"
when_to_load:
  - "When designing or reviewing journeys, flows, states, copy, and interaction constraints."
  - "When implementation questions depend on experience details rather than product goals alone."
depends_on:
  - "prd.md"
modules:
  - "{Primary user-facing surface, workflow, or interaction area affected}"
index:
  design_goals: "## Design Goals & Constraints"
  journeys: "## User Journeys & Touchpoints"
  information_architecture: "## Information Architecture"
  key_flows: "## Key User Flows"
  ui_states: "## UI States"
  copy_tone: "## Copy & Tone"
  visual_design: "## Visual Design Direction"
  consistency: "## UX Consistency Patterns"
  accessibility: "## Responsive & Accessibility"
next_section: "Design Goals & Constraints"
---

# UX Design: {Initiative Name}

## Progress

- [ ] Design Goals & Constraints
- [ ] User Journeys & Touchpoints
- [ ] Information Architecture
- [ ] Key User Flows
- [ ] UI States
- [ ] Copy & Tone
- [ ] Visual Design Direction
- [ ] UX Consistency Patterns
- [ ] Responsive & Accessibility

---

## Design Goals & Constraints

**Primary goal:** {What does a great first-use experience feel like? What emotional outcome are we designing for?}

**Design constraints:**
- {Platform / device targets}
- {Existing design system or style guide to follow — or "none, establish new"}
- {Technical constraints that affect UX (e.g., no realtime, offline-first, CLI-only)}

**Skip condition:** If this is a backend-only change with no UI impact, state that here and stop: `N/A — Backend Only`.

---

## User Journeys & Touchpoints

{For each persona from the PRD, describe their path through the product. Focus on the moments that matter: first contact, first success, recovering from errors.}

### {Persona 1} — {Journey Arc}

**Entry point:** {How do they arrive? (Search, referral, direct link, email)}
**First touchpoint:** {First screen/command/interaction they encounter}
**Key moment:** {The moment they understand the product's value}
**Exit state:** {What does success look like at the end of this journey?}
**Pain points to design around:** {Potential confusion, friction, anxiety}

---

### {Persona 2} — {Journey Arc}

**Entry point:** {…}
**First touchpoint:** {…}
**Key moment:** {…}
**Exit state:** {…}
**Pain points to design around:** {…}

---

## Information Architecture

{Define the structural skeleton of the product. What are the top-level areas? How do users navigate between them?}

### Site/App Map

```
{Top Level}
├── {Section A}
│   ├── {Sub-section 1}
│   └── {Sub-section 2}
├── {Section B}
└── {Section C}
```

### Navigation Model

**Primary nav:** {Tab bar / sidebar / top nav / command palette / none}
**Secondary nav:** {Breadcrumbs / sub-tabs / contextual menus}
**Key entry points:** {Landing page / onboarding / dashboard / direct deep link}

---

## Key User Flows

{For each critical path, describe the step-by-step interaction sequence. Include decision points and alternate paths.}

### Flow 1: {Flow Name} (Happy Path)

1. {Step 1 — user action}
2. {Step 2 — system response}
3. {Step 3 — user action}
4. {Outcome}

**Alternate path A:** {If X, then Y}
**Alternate path B:** {If Z, then W}

---

### Flow 2: {Flow Name}

1. {Step 1}
2. {Step 2}
3. {Outcome}

---

## UI States

{Every view must be designed for all of its possible states, not just the happy path.}

### {Screen / Component Name}

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | {No data yet} | {Prompt, illustration, or CTA} |
| **Loading** | {Async operation in progress} | {Spinner, skeleton, or progress} |
| **Populated** | {Data present} | {Normal view} |
| **Error** | {Operation failed} | {Message + recovery action} |
| **Success** | {Operation completed} | {Confirmation + next action} |
| **Disabled** | {Feature unavailable} | {Greyed out + explanation why} |

---

## Copy & Tone

**Voice:** {How does the product "speak"? e.g., direct and technical / warm and encouraging / minimal}

**Key principles:**
- {Principle 1: e.g., "Never blame the user in error messages"}
- {Principle 2: e.g., "Use active verbs for CTAs"}
- {Principle 3: e.g., "Avoid jargon in onboarding, allow it for advanced flows"}

**Critical copy samples:**

| Context | Copy |
|---------|------|
| Primary CTA | `{exact text}` |
| Empty state headline | `{exact text}` |
| Primary error message | `{exact text}` |
| Success confirmation | `{exact text}` |
| Onboarding headline | `{exact text}` |

---

## Visual Design Direction

**Style:** {Minimal / Bold / Data-dense / Conversational / Terminal / etc.}
**Color palette:** {Describe or reference — e.g., dark background, accent color, semantic colors for status}
**Typography:** {Font family / weight hierarchy — e.g., Inter, monospace for code}
**Spacing & density:** {Compact / comfortable / spacious}
**Existing design system:** {Name of system to follow, or "Establish new — see above"}

**Mood reference:** {Optional: describe the "feel" — e.g., "VS Code meets Linear — focused, dark, fast"}

---

## UX Consistency Patterns

{Define how the product handles common interaction situations so all screens feel coherent.}

### Button Hierarchy
- **Primary action:** {Description — e.g., filled, brand color, one per screen}
- **Secondary action:** {e.g., outlined, can be multiple}
- **Destructive action:** {e.g., red, requires confirmation dialog}

### Feedback Patterns
- **Success:** {e.g., Toast notification, top-right, 3s auto-dismiss}
- **Error:** {e.g., Inline below the failing element + toast for system errors}
- **Warning:** {e.g., Banner above affected content}
- **Info:** {e.g., Inline hint text}

### Form Patterns
- **Validation timing:** {On blur / on submit / real-time}
- **Error placement:** {Below each field / summary at top}
- **Required fields:** {Marked with * / all optional explicit}

### Navigation Patterns
- **Active state:** {How users know where they are}
- **Back navigation:** {Browser back / explicit back button / breadcrumb}

### Modal & Overlay Patterns
- **When to use modals:** {Confirmation dialogs, forms — not for content}
- **Dismissal:** {Click outside / ESC / explicit close button}

---

## Responsive & Accessibility

**Breakpoints:**

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| Mobile | {< Xpx} | {Single col / stacked nav} |
| Tablet | {X–Ypx} | {…} |
| Desktop | {> Ypx} | {…} |

**Accessibility standards:** {WCAG 2.1 AA / AA+ / not applicable}

**Key requirements:**
- {Keyboard navigation: full / partial / N/A}
- {Screen reader support: required / optional}
- {Color contrast: AA minimum}
- {Touch targets: 44×44px minimum on mobile}
- {Reduced motion: respect prefers-reduced-motion}
