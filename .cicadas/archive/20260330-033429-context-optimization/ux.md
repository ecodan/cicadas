---
summary: This initiative changes agent workflow UX rather than end-user product UI; the experience goal is a calmer, more predictable drafting and implementation flow with explicit context reload boundaries and less invisible memory dependence.
phase: ux
when_to_load:
  - When defining builder and agent interaction patterns across phase boundaries.
  - When checking whether prompts, approvals, and reset rules are understandable.
depends_on:
  - prd.md
modules:
  - src/cicadas/SKILL.md
  - src/cicadas/emergence/clarify.md
  - src/cicadas/emergence/ux.md
  - src/cicadas/emergence/tech-design.md
  - src/cicadas/emergence/approach.md
  - src/cicadas/emergence/tasks.md
index:
  design_goals: "## Design Goals & Constraints"
  journeys: "## User Journeys & Touchpoints"
  information_architecture: "## Information Architecture"
  key_flows: "## Key User Flows"
  ui_states: "## UI States"
  copy_tone: "## Copy & Tone"
  consistency: "## UX Consistency Patterns"
  accessibility: "## Responsive & Accessibility"
next_section: "Design Goals & Constraints"
---

# UX Design: context-optimization

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

## Design Goals & Constraints

**Primary goal:** Make Cicadas feel deliberate and lightweight for builders and agents by replacing implicit memory reliance with explicit approved context handoffs.

**Design constraints:**
- Primary interaction surface is markdown specs plus natural-language builder/agent conversations.
- Existing Cicadas file conventions should be preserved; avoid introducing another durable coordination file if existing files can carry the needed context.
- The experience must acknowledge that skills cannot force memory eviction inside a long-lived conversation.

**Skip condition:** N/A — Backend/Workflow UX Only. There is no end-user product UI, but there is still important interaction design for builders and agents.

---

## User Journeys & Touchpoints

### Builder — Approve and Move Forward

**Entry point:** Builder starts an initiative and provides requirements in conversation.  
**First touchpoint:** The drafted spec includes front matter that summarizes the document and lists its indexed sections.  
**Key moment:** After approval, the next phase starts from compact approved context instead of replaying the whole conversation.  
**Exit state:** The builder understands exactly what context the next phase or branch should reload.  
**Pain points to design around:** Hidden carryover from prior turns, repeated restatement, and vague “memory reset” claims the host cannot enforce.

---

### Implementation Agent — Start Focused

**Entry point:** The agent begins a feature branch or partition.  
**First touchpoint:** It reads `canon/summary.md`, then front matter and the indexed sections for the current partition.  
**Key moment:** The agent stays in-scope without loading unrelated partitions or entire spec files unless ambiguity requires it.  
**Exit state:** Work starts with enough context to be safe, but not enough to bloat the context window.  
**Pain points to design around:** Overloading the branch start prompt, opening unrelated docs, and conflating “nudge” with “guarantee.”

---

## Information Architecture

### Site/App Map

```text
Spec File
├── Front Matter
│   ├── summary
│   ├── when_to_load
│   ├── depends_on
│   ├── modules
│   └── index
└── Body
    ├── canonical section headings
    └── detailed content
```

### Navigation Model

**Primary nav:** Front matter summary and index first, then targeted section loading.  
**Secondary nav:** Existing document headings referenced by semantic ids or exact headings.  
**Key entry points:** branch start, next spec phase after approval, new partition start, Reflect on changed scope.

---

## Key User Flows

### Flow 1: Phase Handoff (Happy Path)

1. Agent drafts the current spec phase.
2. Builder reviews and approves the document.
3. Agent refreshes the document front matter to match the approved state.
4. If the host supports it, the agent clears or compacts prior conversational context.
5. Agent begins the next phase by reading only approved summaries and explicitly required indexed sections.
6. Detailed prior drafting context stays out of the default load path.

**Alternate path A:** If the next phase finds ambiguity, it opens only the referenced detailed section rather than the full prior spec set.  
**Alternate path B:** If the builder revises the approved document, the front matter is updated before the next handoff.

---

### Flow 2: Branch or Partition Start

1. Agent starts registered work for a partition.
2. If the host supports it, the agent starts from a fresh or compacted context.
3. Agent reads `canon/summary.md`.
4. Agent reads front matter for `approach.md` and `tasks.md`, then the current partition sections.
5. Agent loads additional spec sections only when needed for ambiguity, compatibility, or acceptance criteria.
6. Implementation begins with partition-scoped context.

---

## UI States

### Spec Context Contract

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | Legacy spec without front matter | Agent notes missing metadata and falls back to document headings/manual reading |
| **Loading** | Starting a new phase or branch | Agent reads compact artifacts first |
| **Populated** | Front matter present and current | Agent uses summary + index + selected sections |
| **Error** | Front matter and body disagree | Agent surfaces inconsistency and asks for clarification or corrects during Reflect |
| **Success** | Approval boundary completed | Agent continues with compact approved context |
| **Disabled** | Host cannot truly clear memory | Skill explains that reset is procedural, asks for clear/compact opportunistically, and still reloads from file-backed context |

---

## Copy & Tone

**Voice:** Direct, calm, and transparent about what the agent can and cannot guarantee.

**Key principles:**
- Be explicit that the method re-anchors context; do not claim hard memory deletion unless the host supports fresh sessions.
- Ask the host to clear or compact context when possible, but never depend on that behavior for correctness.
- Prefer “reload approved context” over “forget everything.”
- Keep boundary instructions short enough to actually be followed during branch starts and handoffs.

**Critical copy samples:**

| Context | Copy |
|---------|------|
| Boundary instruction | `Treat this boundary as a fresh-context start. Reload approved summaries and indexed sections first.` |
| Escalation instruction | `Open full documents only if summaries or indexed sections are insufficient.` |
| Limitation statement | `This reset changes what to trust and reload; it does not guarantee memory eviction inside a long-lived session.` |
| Branch-start cue | `Start from canon summary, then current partition summaries and sections.` |
| Approval cue | `Refresh front matter before continuing to the next phase.` |

---

## Visual Design Direction

**Style:** Documentation-first, compact, and operational.  
**Color palette:** Not applicable.  
**Typography:** Markdown headings plus machine-readable front matter.  
**Spacing & density:** Dense enough for quick scanning; summaries should remain short.  
**Existing design system:** Follow existing Cicadas markdown conventions.

**Mood reference:** “Clear runbook, not chat transcript.”

---

## UX Consistency Patterns

### Button Hierarchy
- **Primary action:** Approve and proceed with compact context reload.
- **Secondary action:** Open a specific indexed section for more detail.
- **Destructive action:** None in this UX flow.

### Feedback Patterns
- **Success:** Agent states the next phase or branch will begin from approved summaries and indexed sections.
- **Error:** Agent points out stale or inconsistent metadata before proceeding.
- **Warning:** Agent warns when it must expand beyond compact context because ambiguity remains.
- **Info:** Agent explains why a deeper section is being opened.

### Form Patterns
- **Validation timing:** On approval boundaries and before branch start.
- **Error placement:** Inline in the agent response or Reflect update.
- **Required fields:** Summary and index are required for core templates.

### Navigation Patterns
- **Active state:** Current phase or partition is named explicitly in the doc and agent response.
- **Back navigation:** Re-open indexed sections from the approved spec rather than searching the transcript.

### Modal & Overlay Patterns
- **When to use modals:** Not applicable.
- **Dismissal:** Not applicable.

---

## Responsive & Accessibility

**Breakpoints:**

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| Mobile | N/A | Markdown-first workflow |
| Tablet | N/A | Markdown-first workflow |
| Desktop | N/A | Markdown-first workflow |

**Accessibility standards:** Documentation should remain plain-text readable and screen-reader friendly.

**Key requirements:**
- Front matter keys should be stable and human-readable.
- Headings referenced in `index` should stay easy to navigate in plain markdown.
- Boundary instructions should be concise and unambiguous.
- Avoid relying on color, layout, or hidden UI state to convey reset behavior.
