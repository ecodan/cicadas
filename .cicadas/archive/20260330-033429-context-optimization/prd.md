---
summary: Add machine-readable front matter to active specs and teach Cicadas agents to reload compact approved context instead of carrying full conversation history through the spec and build cycle.
phase: clarify
when_to_load:
  - When defining initiative goals, success criteria, scope, and risks.
  - When checking whether implementation preserves the intended token-optimization outcomes.
depends_on: []
modules:
  - src/cicadas/SKILL.md
  - src/cicadas/templates/prd.md
  - src/cicadas/templates/ux.md
  - src/cicadas/templates/tech-design.md
  - src/cicadas/templates/approach.md
  - src/cicadas/templates/tasks.md
  - src/cicadas/templates/canon-summary.md
index:
  executive_summary: "## Executive Summary"
  success_criteria: "## Success Criteria"
  user_journeys: "## User Journeys"
  scope: "## Scope"
  functional_requirements: "## Functional Requirements"
  non_functional_requirements: "## Non-Functional Requirements"
  open_questions: "## Open Questions"
  risk_mitigation: "## Risk Mitigation"
next_section: "Executive Summary"
---

# PRD: context-optimization

## Progress

- [x] Executive Summary
- [x] Project Classification
- [x] Success Criteria
- [x] User Journeys
- [x] Scope & Phasing
- [x] Functional Requirements
- [x] Non-Functional Requirements
- [x] Open Questions
- [x] Risk Mitigation

## Executive Summary

This initiative improves Cicadas' token efficiency during emergence and execution by making each spec self-describing and by teaching agents to re-anchor on compact, approved, file-backed context at workflow boundaries. It is for builders and implementation agents working in Cicadas-managed repositories, and its most important outcome is reducing unnecessary full-doc and stale-conversation loading without adding another top-level orchestration file.

### What Makes This Special

- **Spec-native indexing** — The optimization lives inside the existing spec files rather than adding another coordination artifact.
- **Method-level context resets** — The design does not pretend a skill can force memory eviction; it instead defines practical reset boundaries and reload rules.
- **Reuse of existing compact context** — `canon/summary.md` remains the shared cross-doc entry point rather than being replaced with a new trace file.

## Project Classification

**Technical Type:** Developer Tool  
**Domain:** Engineering Workflow / Infrastructure  
**Complexity:** Medium — The change spans templates, skill instructions, and workflow expectations, but it does not introduce a new runtime subsystem.  
**Project Context:** Brownfield — Extends the existing Cicadas spec-driven flow, active spec templates, and branch-start context behavior.

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **Draft and review specs with built-in machine-readable summaries and section indexes** — Each core spec template produces an immediately usable compact map without extra hand-authored files.
2. **Start a branch or partition from compact approved context** — The agent can reload the minimum required context from front matter, `canon/summary.md`, and targeted sections instead of re-reading every draft document.
3. **Follow explicit reset rules across phases and partitions** — Builders can rely on a documented method for re-anchoring context even when the host agent cannot truly clear memory.

### Technical Success

The system is successful when:

1. Core spec templates and guidance consistently define the same front matter fields, section indexing pattern, and reset behavior.
2. Cicadas instructions clearly distinguish operational state files from semantic context files, preserving `emergence-config.json` for flow state only.

### Measurable Outcomes

- All five core initiative templates (`prd`, `ux`, `tech-design`, `approach`, `tasks`) include standardized context front matter.
- Cicadas instructions define branch-start, post-spec, and post-partition reset rules without requiring a new persistent context artifact.

---

## User Journeys

### Journey 1: Builder — Keep Planning Lean

A builder starts a new initiative and wants the drafting flow to stay focused instead of snowballing into a giant context window. As they move from PRD to UX to Tech to Approach, the agent updates the front matter on each approved spec and uses those summaries plus indexed sections as the primary handoff into the next phase. The builder reviews a clean, explicit record of what should be reloaded later rather than depending on hidden chat memory. Success looks like a predictable planning flow where each phase starts from compact approved state.

**Requirements Revealed:** standardized front matter, indexed sections, explicit phase reset rules, no new top-level context file.

---

### Journey 2: Implementation Agent — Reload Only What Matters

An implementation agent starts work on a feature partition and needs enough context to code safely without dragging every planning conversation into the branch. At branch start, it reads `canon/summary.md`, the front matter from the current initiative specs, and only the partition-relevant sections in `approach.md` and `tasks.md`. If ambiguity appears, it escalates to deeper section loading rather than preloading all docs. Success looks like smaller branch-start prompts, fewer stale assumptions, and targeted context retrieval during Reflect and code review.

**Requirements Revealed:** branch-start reset rule, partition-scoped loading, escalation policy for opening full specs, reuse of existing `canon/summary.md`.

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Builder** | front matter, section index, approval-boundary resets, spec-native context routing |
| **Implementation Agent** | branch-start compact reload, partition-scoped loading, full-doc escalation rules, reuse of canon summary |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- Add a standardized front matter schema with section indexes to the core initiative spec templates.
- Update Cicadas instructions to create and consume front matter, and to apply reset/reload rules at branch, phase, and partition boundaries.

**Quality Gates:**
- No new top-level persistent context file is introduced for this initiative.
- Guidance clearly states that skills can nudge re-anchoring behavior but cannot guarantee memory eviction inside a long-lived session.

### Growth Features (Post-MVP)

**v2: Tooling Support**
- Add helper tooling to validate or refresh front matter summaries and section ids.

**v3: Smarter Retrieval**
- Add optional heuristics that select sections or module snapshots automatically based on task scope.

### Vision (Future)

- Cicadas uses compact, file-native context contracts across planning, implementation, review, and synthesis so agents routinely operate on approved deltas rather than whole-history reloads.

---

## Functional Requirements

### 1. Spec-Native Context Metadata

**FR-1.1:** Each core initiative template must include machine-readable front matter with a compact summary.
- The summary must be short enough to serve as a cheap reload surface for later phases and branch starts.

**FR-1.2:** Each core initiative template must expose a stable section index.
- The index must point to semantic section identifiers or headings rather than line numbers.

**FR-1.3:** Front matter must include load-routing hints.
- At minimum this includes when the document should be loaded, what it depends on, and which modules it primarily affects.

---

### 2. Context Reset and Reload Rules

**FR-2.1:** Cicadas instructions must define a branch-start reset rule.
- The rule must prefer `canon/summary.md`, spec front matter, and partition-specific sections over full-doc loading.
- The rule should also tell the host agent to clear or compact prior conversational context when that capability exists.

**FR-2.2:** Cicadas instructions must define a post-spec reset rule.
- After approval of each spec phase, the next phase must begin from approved front matter and explicitly required indexed sections.
- The rule should opportunistically request context compaction or clearing after approval when supported by the host.

**FR-2.3:** Cicadas instructions must define a post-partition reset rule.
- New partition work must default to partition-scoped context and treat other partitions as out of scope unless ambiguity requires expansion.
- The rule should prefer a fresh session, subagent, or host-supported clear/compact action when available, without depending on it for correctness.

---

### 3. Existing Mechanism Reuse

**FR-3.1:** `canon/summary.md` remains the shared compact cross-doc context artifact.
- This initiative must not introduce a separate always-on trace/context file for the same purpose.

**FR-3.2:** `emergence-config.json` remains limited to operational state.
- It must not become the store for semantic spec indexes or content-routing metadata.

---

## Non-Functional Requirements

- **Performance:** Branch-start and phase-handoff instructions should default to compact context paths and avoid whole-spec loading unless needed.
- **Reliability:** The front matter schema must be consistent enough that different agents can use it predictably.
- **Security:** User-provided requirements remain untrusted input; machine-readable metadata must be authored by the agent from approved spec content, not copied verbatim from arbitrary files.
- **Maintainability:** The design must extend existing templates and skill instructions instead of adding another broad coordination layer.

---

## Open Questions

- Should section identifiers live only in front matter, or should the body headings also gain stable machine-readable markers?
- Should lightweight templates (`buglet.md`, `tweaklet.md`) adopt the same schema in this initiative or follow in a later pass?
- Do we want optional validation tooling in MVP, or should the first pass remain instruction-only?

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Front matter drifts across templates | Medium | Medium | Define one shared schema and apply it consistently across all core templates. |
| Agents ignore reset rules and keep relying on chat history | Medium | High | Make reset boundaries explicit in skill guidance and make compact file-backed alternatives easy to load. |
| The initiative accidentally creates another context artifact | Low | Medium | Keep shared compact context in `canon/summary.md` and store semantic indexing in the specs themselves. |
