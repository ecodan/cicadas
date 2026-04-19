# Technical Initiative Profile Plan

## Problem

Cicadas currently treats all full initiatives as if they need the same PRD -> UX -> Tech Design -> Approach -> Tasks flow. That is appropriate for product-facing work, but it can add avoidable ceremony for mostly technical initiatives such as parsers, graph quality, internal CLI behavior, build/test infrastructure, refactors, migrations, and performance work.

The goal is to reduce unnecessary spec overhead while preserving the decision record Cicadas needs for safe implementation and later canon synthesis.

## Recommendation

Add an explicit initiative profile choice during start flow:

- `product`
- `technical`
- `mixed`

The selected profile controls whether the initiative uses the full PRD/UXD flow or a lighter technical path.

## Proposed Flow

| Profile | Clarify Artifact | UX Artifact | Required Later Specs |
|---------|------------------|-------------|----------------------|
| `product` | Full PRD | Full UXD | Tech Design, Approach, Tasks |
| `mixed` | Full or PRD-lite | UXD or Operator Experience | Tech Design, Approach, Tasks |
| `technical` | Technical Brief | Skip UXD or Operator Experience | Tech Design, Approach, Tasks |

## Technical Initiative Eligibility

An initiative may use the `technical` profile when most of these are true:

- Primary users are maintainers, agents, operators, or developers.
- There is no customer-facing UI change.
- There is no major product workflow change.
- Work is infrastructure, refactor, parser/extractor, migration, performance, internal CLI, testing, build-system, or agent-guidance focused.
- Success can be expressed as technical acceptance criteria.
- The UX surface is limited to CLI output, logs, error messages, docs, or agent instructions.

If the work includes meaningful end-user interaction, product positioning, or ambiguous user journeys, use `product` or `mixed`.

## Technical Brief Contents

For `technical` initiatives, replace full PRD with a Technical Brief containing:

- Problem statement
- Goals and non-goals
- Affected modules
- Users/operators affected
- Success criteria
- Functional requirements or acceptance criteria
- Risks and rollback considerations
- Observability and testing expectations

## UX Handling

For `technical` initiatives, UXD should be optional.

Use Operator Experience instead of full UXD when the work changes:

- CLI commands or flags
- command output
- logs or progress display
- error/fallback messages
- agent instructions
- documentation workflow

Skip UX entirely only when there is no meaningful human-facing or agent-facing interaction change.

## Implementation Notes

- Update `start-flow.md` to ask for initiative profile after name and before requirements source.
- Store the profile in `emergence-config.json`.
- Add a `technical-brief.md` template.
- Add or adapt an `operator-experience.md` template.
- Update clarify/UX/tech/approach/task emergence guidance to branch based on profile.
- Preserve front matter contracts on all artifacts so compact context reload still works.
- Keep Tech Design, Approach, and Tasks mandatory for technical initiatives with architectural or cross-module impact.

## Guardrail

PRD and UXD should become optional only through the explicit profile mechanism. Agents should not skip them ad hoc. The reduced flow must still produce enough approved context for implementation, review, and canon synthesis.
