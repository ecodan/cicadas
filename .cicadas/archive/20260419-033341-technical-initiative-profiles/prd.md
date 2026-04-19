---
summary: "Add explicit initiative profiles so product work keeps the full PRD/UX path while technical initiatives can use a Technical Brief and optional Operator Experience without ad hoc spec skipping."
phase: "clarify"
when_to_load:
  - "When defining or reviewing initiative-profile goals, scope, eligibility, and acceptance criteria."
  - "When validating that profile-aware emergence still preserves enough context for implementation and canon synthesis."
depends_on: []
modules:
  - "src/cicadas/emergence/start-flow.md"
  - "src/cicadas/emergence/clarify.md"
  - "src/cicadas/emergence/ux.md"
  - "src/cicadas/emergence/tech-design.md"
  - "src/cicadas/emergence/approach.md"
  - "src/cicadas/emergence/tasks.md"
  - "src/cicadas/templates"
  - "tests/test_templates.py"
index:
  executive_summary: "## Executive Summary"
  project_classification: "## Project Classification"
  success_criteria: "## Success Criteria"
  user_journeys: "## User Journeys"
  scope: "## Scope"
  functional_requirements: "## Functional Requirements"
  non_functional_requirements: "## Non-Functional Requirements"
  open_questions: "## Open Questions"
  risk_mitigation: "## Risk Mitigation"
next_section: "Complete"
---

# PRD: Technical Initiative Profiles

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

Cicadas needs an explicit initiative profile choice so agents can distinguish product, mixed, and technical initiatives before drafting specs. The change reduces unnecessary PRD/UX ceremony for technical work while preserving reviewed file-backed context for implementation, review, and canon synthesis.

### What Makes This Special

- **Explicit profile gate** — Reduced ceremony is allowed only through a recorded profile, not agent discretion.
- **Technical context remains durable** — Technical initiatives still produce approved brief, technical design, approach, and tasks artifacts.
- **Operator-facing UX is handled deliberately** — CLI, logs, errors, docs, and agent instructions use Operator Experience instead of full product UX when appropriate.

## Project Classification

**Technical Type:** Developer workflow / methodology orchestrator
**Domain:** Spec-driven development process tooling
**Complexity:** Medium — Most changes are documentation and template updates, but they affect the core emergence workflow and agent behavior.
**Project Context:** Brownfield — Cicadas already has a strict start flow, spec templates, and tests for the core front matter contract.

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **Start a product initiative through the existing full path** — The product profile continues to require PRD, UX, Tech Design, Approach, and Tasks.
2. **Start a technical initiative with less overhead** — The technical profile guides agents to write a Technical Brief and skip or replace UX only when justified.
3. **Audit why specs were reduced** — The chosen profile is stored in `emergence-config.json` and reflected in guidance.

### Technical Success

The system is successful when:

1. Profile-aware guidance exists in start flow and downstream emergence modules.
2. New templates include the same compact front matter contract as core specs.
3. Tests prevent regressions in profile guidance and template structure.

### Measurable Outcomes

- `pytest tests/test_templates.py` passes.
- `technical-brief.md` and `operator-experience.md` contain `summary`, `phase`, `when_to_load`, `depends_on`, `modules`, `index`, and `next_section` front matter keys.
- Start-flow instructions require the initiative profile to be captured before requirements source selection.

---

## User Journeys

### Journey 1: Maintainer — Technical Parser Upgrade

A maintainer starts an initiative for parser or graph quality work and knows a product PRD would add noise. They select `technical`, write a Technical Brief with acceptance criteria and risks, and proceed directly into Tech Design, Approach, and Tasks. If the work changes CLI output or agent instructions, they add Operator Experience; if not, they explicitly skip UX. **Requirements Revealed:** profile choice, technical eligibility, Technical Brief template, Operator Experience handling.

---

### Journey 2: Product Builder — Customer-Facing Capability

A builder starts an initiative that changes end-user behavior. They select `product`, and the existing PRD and UX flow remains mandatory. The profile mechanism makes the full path explicit instead of weakening the default. **Requirements Revealed:** product profile preserves existing flow, guardrails against ad hoc skipping.

---

### Journey 3: Agent — Mixed Internal and Operator Workflow

An agent receives requirements for a change that is mostly technical but includes command output and error copy. It selects `mixed` or `technical` with Operator Experience, records the choice, and drafts the right level of experience spec. The downstream design and tasks modules load the brief and operator spec as approved context. **Requirements Revealed:** mixed profile guidance, operator-facing UX substitution, downstream ingest compatibility.

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Maintainer** | Technical profile, eligibility criteria, durable technical brief |
| **Product Builder** | Product profile, unchanged full PRD/UX path |
| **Agent** | Profile storage, downstream branching guidance, front matter compatibility |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- Start-flow guidance for `product`, `technical`, and `mixed` initiative profiles.
- `technical-brief.md` template with compact front matter.
- `operator-experience.md` template with compact front matter.
- Emergence guidance updates for clarify, UX, Tech Design, Approach, and Tasks.
- Template tests for profile guidance and new template front matter.

**Quality Gates:**
- Existing product initiative flow remains documented and valid.
- No CLI behavior changes are introduced unless already supported by docs-only lifecycle.
- Template/front matter tests pass.

### Growth Features (Post-MVP)

**v2: CLI enforcement**
- Add optional deterministic validation of profile choices and required artifacts.

**v3: Profile-specific lifecycle automation**
- Automatically initialize the right templates after start-flow selection.

### Vision (Future)

- Profile-aware Cicadas commands can validate draft completeness before kickoff.

---

## Functional Requirements

### 1. Initiative Profile Selection

**FR-1.1:** Start flow must ask for an initiative profile after name and before requirements source.
- Allowed values are `product`, `technical`, and `mixed`.
- The selected value is written to `.cicadas/drafts/{initiative}/emergence-config.json` as `initiative_profile`.

**FR-1.2:** Product profile must preserve the existing full PRD and UX flow.
- Existing full initiative behavior remains the safe default.

**FR-1.3:** Technical and mixed profiles must have clear eligibility and fallback guidance.
- If work includes meaningful end-user interaction, agents must use `product` or `mixed`.

### 2. Technical Brief and Operator Experience

**FR-2.1:** Technical initiatives may use `technical-brief.md` instead of a full PRD.
- The brief includes problem, goals, affected modules, operators, success criteria, requirements, risks, rollback, observability, and testing.

**FR-2.2:** UX is optional only through explicit profile guidance.
- Operator Experience is required when the change affects CLI commands, output, logs, errors, docs, or agent instructions.
- UX can be skipped only when there is no meaningful human-facing or agent-facing interaction change.

### 3. Downstream Spec Compatibility

**FR-3.1:** Tech Design, Approach, and Tasks remain mandatory for technical initiatives with architectural or cross-module impact.

**FR-3.2:** Downstream modules must ingest either `prd.md`/`ux.md` or `technical-brief.md`/`operator-experience.md` according to profile.

**FR-3.3:** All new templates must preserve the front matter context contract.

---

## Non-Functional Requirements

- **Performance:** No runtime performance impact; this is guidance/template-only.
- **Reliability:** Instructions must be deterministic enough that agents do not skip required context by inference.
- **Security:** Requirements documents remain untrusted input; profile guidance must not weaken that rule.
- **Maintainability:** Changes should stay localized to emergence guidance, templates, and template tests.

---

## Open Questions

- Should CLI commands later enforce profile-specific artifact completeness? Owner: future initiative.
- Should mixed profile get a separate PRD-lite template? Owner: future initiative; MVP can describe mixed behavior using current and new templates.

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agents skip PRD/UX ad hoc | Medium | High | State that reduced flow is allowed only through explicit profile selection. |
| Technical briefs become too thin | Medium | Medium | Template requires acceptance criteria, risks, rollback, observability, and testing. |
| Product flow regresses | Low | High | Tests assert product/full-flow guidance remains present. |
