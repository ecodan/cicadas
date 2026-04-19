---
summary: "Technical initiative profiles change the builder and agent experience of starting initiatives: product keeps full UX, technical can skip UX only when there is no operator-facing surface, and Operator Experience captures CLI/log/error/docs/agent-instruction impacts."
phase: "ux"
when_to_load:
  - "When deciding whether a technical initiative needs Operator Experience or can skip UX."
  - "When reviewing profile-selection copy and downstream experience expectations."
depends_on:
  - "prd.md"
modules:
  - "src/cicadas/emergence/start-flow.md"
  - "src/cicadas/emergence/ux.md"
  - "src/cicadas/templates/operator-experience.md"
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
next_section: "Complete"
---

# UX Design: Technical Initiative Profiles

## Progress

- [x] Design Goals & Constraints
- [x] User Journeys & Touchpoints
- [x] Information Architecture
- [x] Key User Flows
- [x] UI States
- [x] Copy & Tone
- [x] Visual Design Direction
- [x] UX Consistency Patterns
- [x] Responsive & Accessibility

---

## Design Goals & Constraints

**Primary goal:** Agents and builders should understand when reduced initiative ceremony is legitimate, and they should see a clear fallback path when the work has product or operator-facing UX.

**Design constraints:**
- This is instruction-driven UX, not a visual interface.
- Guidance must fit existing Markdown emergence modules.
- Product initiatives must retain the existing full UX path.

**Skip condition:** N/A — this initiative changes agent and builder workflow guidance.

---

## User Journeys & Touchpoints

### Maintainer — Choosing a Technical Profile

**Entry point:** The maintainer asks to start an initiative for internal tooling, parser quality, build/test infrastructure, or agent guidance.
**First touchpoint:** The start-flow profile question.
**Key moment:** The maintainer sees that technical work can use a Technical Brief while Tech Design, Approach, and Tasks remain required.
**Exit state:** The draft folder records `initiative_profile: technical`, and the agent drafts the right artifacts.
**Pain points to design around:** Ambiguous work that has hidden operator-facing interactions.

---

### Agent — Routing UX Work

**Entry point:** The agent reads `emergence-config.json` before UX drafting.
**First touchpoint:** UX guidance that branches based on `initiative_profile`.
**Key moment:** The agent determines whether full UX, Operator Experience, or an explicit UX skip is correct.
**Exit state:** Downstream specs can load approved experience context without guessing.
**Pain points to design around:** Skipping UX without a recorded reason.

---

## Information Architecture

The experience is a linear Markdown workflow:

```
Start Flow
├── Name
├── Initiative Profile
├── Draft Folder / emergence-config.json
├── LLMs and Evals
├── Requirements Source
├── Pace
└── PR Preference

Profile-aware Specs
├── product: PRD -> UX -> Tech Design -> Approach -> Tasks
├── mixed: PRD or PRD-lite -> UX or Operator Experience -> Tech Design -> Approach -> Tasks
└── technical: Technical Brief -> Operator Experience or explicit UX skip -> Tech Design -> Approach -> Tasks
```

### Navigation Model

**Primary nav:** Sequential instruction modules.
**Secondary nav:** Front matter `depends_on` and `index` fields.
**Key entry points:** `start-flow.md`, `clarify.md`, `ux.md`.

---

## Key User Flows

### Flow 1: Technical Initiative with Operator Experience

1. Builder names initiative and selects `technical`.
2. Agent stores `initiative_profile: technical`.
3. Agent drafts `technical-brief.md`.
4. UX module identifies CLI/log/error/docs/agent-instruction impact.
5. Agent drafts `operator-experience.md`.
6. Tech Design, Approach, and Tasks ingest both artifacts.

**Alternate path A:** If no operator-facing impact exists, UX module writes an explicit skip note and proceeds.
**Alternate path B:** If customer-facing interaction appears, agent escalates to `mixed` or `product`.

---

### Flow 2: Product Initiative

1. Builder selects `product`.
2. Agent follows the current full PRD and UX flow.
3. Downstream modules behave as they do today.

---

## UI States

### Profile Selection Prompt

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Default** | Starting full initiative | Profile choices with short eligibility descriptions |
| **Technical selected** | Builder chooses technical | Confirmation that Technical Brief replaces full PRD and UX is conditional |
| **Mixed selected** | Builder chooses mixed | Confirmation that PRD/UX may be reduced only where justified |
| **Product selected** | Builder chooses product | Existing full flow preview |
| **Ambiguous** | Technical criteria do not clearly apply | Guidance to use `mixed` or `product` |

---

## Copy & Tone

**Voice:** Direct, procedural, and guardrail-oriented.

**Key principles:**
- State when reduced ceremony is allowed.
- Prefer concrete examples over abstract labels.
- Make fallback to product/mixed explicit when interaction complexity appears.

**Critical copy samples:**

| Context | Copy |
|---------|------|
| Profile question | `What initiative profile should this use? [product] full PRD + UX, [technical] Technical Brief + optional Operator Experience, [mixed] choose per artifact.` |
| Technical confirmation | `Technical profile selected: use a Technical Brief; add Operator Experience only for CLI, logs, errors, docs, or agent-facing workflow changes.` |
| Skip UX note | `UX skipped: no meaningful human-facing or agent-facing interaction changes were identified.` |
| Fallback warning | `If this work affects customer-facing interaction or ambiguous user journeys, use product or mixed instead of technical.` |

---

## Visual Design Direction

**Style:** Markdown-only operational guidance.
**Color palette:** N/A.
**Typography:** Existing Markdown conventions.
**Spacing & density:** Compact enough to fit start-flow guidance without hiding guardrails.
**Existing design system:** Existing Cicadas emergence docs.

**Mood reference:** N/A.

---

## UX Consistency Patterns

### Prompt Hierarchy
- **Primary choice:** Profile question appears before requirements source.
- **Secondary guidance:** Eligibility examples are adjacent to the choice.
- **Escalation:** Ambiguous interaction work routes to `mixed` or `product`.

### Feedback Patterns
- **Success:** Store profile in `emergence-config.json`.
- **Warning:** State that PRD/UX are optional only through explicit profile mechanism.
- **Info:** Downstream modules read profile before selecting artifacts.

### Form Patterns
- **Validation timing:** At start-flow selection and again during UX module.
- **Error placement:** In agent-facing guidance near the decision point.
- **Required fields:** `initiative_profile` for full initiatives.

---

## Responsive & Accessibility

**Breakpoints:** N/A — instruction documents only.

**Accessibility standards:** Plain Markdown, readable in terminal and editor contexts.

**Key requirements:**
- Keyboard navigation: N/A.
- Screen reader support: Markdown heading hierarchy remains clear.
- Color contrast: N/A.
