---
summary: "{One tight paragraph summarizing the technical problem, affected operators/modules, and success criteria. Keep it compact enough to serve as a low-cost reload artifact.}"
phase: "clarify"
when_to_load:
  - "When defining or reviewing technical initiative goals, module scope, acceptance criteria, risks, rollback, observability, and tests."
  - "When downstream Tech Design, Approach, or Tasks need the approved technical problem statement without loading a product PRD."
depends_on: []
modules:
  - "{Primary module, package, script, or workflow this technical initiative changes}"
index:
  problem: "## Problem Statement"
  goals_non_goals: "## Goals and Non-Goals"
  affected_modules: "## Affected Modules"
  users_operators: "## Users and Operators Affected"
  success_criteria: "## Success Criteria"
  requirements: "## Functional Requirements and Acceptance Criteria"
  risks_rollback: "## Risks and Rollback"
  observability_testing: "## Observability and Testing Expectations"
  open_questions: "## Open Questions"
next_section: "Problem Statement"
---

# Technical Brief: {Initiative Name}

## Progress

- [ ] Problem Statement
- [ ] Goals and Non-Goals
- [ ] Affected Modules
- [ ] Users and Operators Affected
- [ ] Success Criteria
- [ ] Functional Requirements and Acceptance Criteria
- [ ] Risks and Rollback
- [ ] Observability and Testing Expectations
- [ ] Open Questions

## Problem Statement

{Describe the technical problem, why it matters now, and what failure mode or inefficiency exists in the current system.}

## Goals and Non-Goals

### Goals

- {Goal 1}
- {Goal 2}
- {Goal 3}

### Non-Goals

- {Explicitly out-of-scope item}
- {Explicitly out-of-scope item}

## Affected Modules

| Module / Path | Expected Change | Notes |
|---------------|-----------------|-------|
| `{path}` | {Add / modify / remove / document} | {Important boundary or constraint} |

## Users and Operators Affected

| Operator / User | Impact |
|-----------------|--------|
| {Maintainer / agent / developer / operator} | {How their workflow changes} |

## Success Criteria

- {Falsifiable technical outcome}
- {Falsifiable technical outcome}
- {Quality or maintainability outcome}

## Functional Requirements and Acceptance Criteria

### FR-1: {Capability Area}

- **Requirement:** {What must change}
- **Acceptance criteria:**
  - {Observable pass/fail criterion}
  - {Observable pass/fail criterion}

### FR-2: {Capability Area}

- **Requirement:** {What must change}
- **Acceptance criteria:**
  - {Observable pass/fail criterion}

## Risks and Rollback

| Risk | Likelihood | Impact | Mitigation | Rollback |
|------|------------|--------|------------|----------|
| {Risk} | Low/Med/High | Low/Med/High | {Mitigation} | {How to back out safely} |

## Observability and Testing Expectations

- **Observability:** {Logs, metrics, diagnostics, status output, or explicit none}
- **Tests:** {Targeted tests, integration tests, fixtures, evals, or benchmark expectations}
- **Manual verification:** {Any manual review that remains necessary}

## Open Questions

- {Question, owner, urgency}
