
---
summary: "{One tight paragraph summarizing the initiative's goals, users, and intended outcome. Keep it compact enough to serve as a low-cost reload artifact.}"
phase: "clarify"
when_to_load:
  - "When defining or reviewing initiative goals, users, scope, success criteria, and risks."
  - "When validating that implementation still aligns with the intended problem and outcomes."
depends_on: []
modules:
  - "{Primary code, workflow, or product area this initiative changes}"
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
next_section: "Executive Summary"
---

# PRD: {Initiative Name}

## Progress

- [ ] Executive Summary
- [ ] Project Classification
- [ ] Success Criteria
- [ ] User Journeys
- [ ] Scope & Phasing
- [ ] Functional Requirements
- [ ] Non-Functional Requirements
- [ ] Open Questions
- [ ] Risk Mitigation

## Executive Summary

{1–3 sentence elevator pitch. What is this, who is it for, and what is the single most important thing it achieves?}

### What Makes This Special

- **{Differentiator 1}** — {Why it matters}
- **{Differentiator 2}** — {Why it matters}
- **{Differentiator 3}** — {Why it matters}

## Project Classification

**Technical Type:** {e.g. Consumer App / Developer Tool / Internal Service / Framework}
**Domain:** {e.g. Productivity / Scientific / Entertainment / Infrastructure}
**Complexity:** {Low / Medium / High} — {1-sentence justification}
**Project Context:** {Greenfield / Brownfield — brief note on existing system if brownfield}

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **{Outcome 1}** — {How we know this is true}
2. **{Outcome 2}** — {How we know this is true}
3. **{Outcome 3}** — {How we know this is true}

### Technical Success

The system is successful when:

1. **{Technical criterion 1}**
2. **{Technical criterion 2}**

### Measurable Outcomes

- {Specific, quantifiable metric 1}
- {Specific, quantifiable metric 2}

---

## User Journeys

{For each user type, write a 3–5 sentence narrative: who they are, what problem they have, how they discover and use this system, and what success looks like for them. End each with a "Requirements Revealed" summary.}

### Journey 1: {Persona Name} — {Short Arc Title}

{Narrative paragraph...}

**Requirements Revealed:** {Key capability areas this journey defines.}

---

### Journey 2: {Persona Name} — {Short Arc Title}

{Narrative paragraph...}

**Requirements Revealed:** {Key capability areas this journey defines.}

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **{Persona 1}** | {comma-separated capabilities} |
| **{Persona 2}** | {comma-separated capabilities} |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- {Deliverable 1}
- {Deliverable 2}

**Quality Gates:**
- {Gate 1}
- {Gate 2}

### Growth Features (Post-MVP)

**v2: {Theme}**
- {Feature}

**v3: {Theme}**
- {Feature}

### Vision (Future)

- {Long-term capability}

---

## Functional Requirements

{Group requirements by capability area. Use FR-X.Y numbering for cross-reference by downstream docs.}

### 1. {Capability Area Name}

**FR-1.1:** {What the system must do — user-observable behavior}
- {Sub-detail or acceptance criterion}

**FR-1.2:** {Next requirement}
- {Sub-detail}

---

### 2. {Capability Area Name}

**FR-2.1:** {Requirement}

---

## Non-Functional Requirements

- **Performance:** {Latency, throughput, or scale targets — be quantitative where possible}
- **Reliability:** {Error handling, uptime, or data integrity requirements}
- **Security:** {Auth, input validation, data protection requirements}
- **Maintainability:** {Code quality, extensibility, or test coverage expectations}

---

## Open Questions

- {Unresolved question 1 — who needs to answer it and when?}
- {Unresolved question 2}
- {Unresolved question 3}

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| {Risk 1} | Low/Med/High | Low/Med/High | {How we address it} |
| {Risk 2} | Low/Med/High | Low/Med/High | {How we address it} |
