---
summary: "{One tight paragraph summarizing operator-facing commands, output, errors, logs, docs, or agent-instruction changes. Keep it compact enough for downstream implementation context.}"
phase: "ux"
when_to_load:
  - "When a technical or mixed initiative affects CLI commands, command output, logs, progress, errors, docs, or agent-facing workflow."
  - "When implementation questions depend on operator-facing behavior rather than product UI behavior."
depends_on:
  - "technical-brief.md or prd.md"
modules:
  - "{Primary operator-facing surface or workflow this initiative changes}"
index:
  operator_goals: "## Operator Goals and Constraints"
  surfaces: "## Affected Surfaces"
  flows: "## Operator Flows"
  states: "## States and Feedback"
  copy: "## Copy and Message Guidelines"
  accessibility: "## Accessibility and Readability"
next_section: "Operator Goals and Constraints"
---

# Operator Experience: {Initiative Name}

## Progress

- [ ] Operator Goals and Constraints
- [ ] Affected Surfaces
- [ ] Operator Flows
- [ ] States and Feedback
- [ ] Copy and Message Guidelines
- [ ] Accessibility and Readability

## Operator Goals and Constraints

**Primary goal:** {What should maintainers, agents, developers, or operators be able to do confidently?}

**Constraints:**
- {CLI/log/docs/agent workflow constraint}
- {Compatibility or scripting constraint}
- {Noise, verbosity, or failure-mode constraint}

## Affected Surfaces

| Surface | Change | Compatibility Notes |
|---------|--------|---------------------|
| `{command/output/log/doc/instruction}` | {Expected experience change} | {Backward compatibility or migration note} |

## Operator Flows

### Flow 1: {Flow Name}

1. {Operator action}
2. {System or agent response}
3. {Observable success state}

**Alternate path:** {Failure, warning, or fallback behavior}

## States and Feedback

| State | Trigger | Operator Sees |
|-------|---------|---------------|
| **Start** | {Initial action} | {Prompt, command, or instruction} |
| **Progress** | {Long-running or multi-step work} | {Status, log, or guidance} |
| **Success** | {Completion} | {Confirmation or next action} |
| **Warning** | {Recoverable issue} | {Actionable warning} |
| **Error** | {Blocking issue} | {Actionable failure message} |

## Copy and Message Guidelines

- {Message principle, e.g. concise, actionable, stable for scripts}
- {Exact phrase or format to use when needed}
- {Words, tone, or ambiguity to avoid}

## Accessibility and Readability

- **Terminal readability:** {Line length, indentation, color dependence, or plain-text fallback}
- **Screen reader / editor readability:** {Heading structure, labels, or not applicable}
- **Machine readability:** {Stable output format, flags, JSON mode, or not applicable}
