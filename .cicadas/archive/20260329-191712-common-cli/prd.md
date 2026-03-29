---
next_section: "UX"
---

# PRD: common-cli

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

`common-cli` consolidates Cicadas' script-sprawl behind a single repo-local command surface that development agents can discover and operate through help text and subcommands. It is for agent-driven workflows first: instead of invoking many Python scripts directly, agents should use one stable CLI interface that preserves per-project versioning and avoids a machine-global installation model.

### What Makes This Special

- **Agent-first discoverability** — The CLI is designed so an agent can learn usage from `--help` instead of hardcoding many script paths and argument shapes.
- **Repo-local version ownership** — Each project keeps the Cicadas behavior it expects without depending on a globally installed tool.
- **Thin wrapper, not a workflow rewrite** — MVP focuses on wrapping existing deterministic scripts and updating docs, minimizing lifecycle disruption while improving interface consistency.

## Project Classification

**Technical Type:** Developer Tool
**Domain:** Infrastructure / Agent Workflow
**Complexity:** Medium — The initiative changes the public invocation surface for many existing lifecycle utilities, but should largely preserve underlying behavior.
**Project Context:** Brownfield — Cicadas already has working deterministic Python scripts and skill/docs that refer to them directly.

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **Discover Cicadas capabilities through one entrypoint** — An agent can run a single Cicadas command with `--help` and identify available operations without reading multiple script files.
2. **Execute lifecycle operations through stable subcommands** — An agent can perform status, kickoff, branch, archive, and related operations without invoking script files directly.
3. **Operate consistently across repos** — An agent can use the same command shape in different Cicadas-managed projects while each repo preserves its own implementation version.

### Technical Success

The system is successful when:

1. **All existing deterministic lifecycle scripts are reachable through the common CLI without behavioral regression.**
2. **Cicadas documentation and skill instructions point to the CLI contract instead of direct script paths wherever appropriate.**

### Measurable Outcomes

- All current user-facing deterministic Cicadas operations are exposed as CLI subcommands with working `--help` output.
- Core Cicadas docs and skill instructions no longer require direct `python .../scripts/*.py` invocation for standard flows.

---

## User Journeys

### Journey 1: Development Agent — Learn and Execute a Lifecycle Command

A development agent enters a Cicadas-managed repository and needs to understand what operations are available without relying on stale embedded knowledge. It discovers a single repo-local Cicadas command, runs `--help`, and finds subcommands for the lifecycle actions it needs. The agent uses that one interface to perform operations like status checks or kickoff without reasoning about individual script filenames. Success means the agent can stay focused on workflow intent instead of reverse-engineering Cicadas' implementation layout.

**Requirements Revealed:** single entrypoint, self-describing help output, stable subcommand naming, parity with existing script capabilities.

---

### Journey 2: Cicadas Maintainer — Evolve the Interface Without Global Install Drift

A Cicadas maintainer wants to improve ergonomics by reducing the number of script-shaped commands exposed in skills and docs. They introduce a repo-local CLI layer that wraps the existing deterministic tools and update documentation to reference the new interface. Because the CLI ships with the repo, different projects can adopt it on their own schedules without forcing users to keep a global install in sync. Success means maintainers can improve interface consistency while preserving per-project version control.

**Requirements Revealed:** repo-local distribution, backward-compatible wrapping strategy, documentation migration, per-project versioning.

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Development Agent** | single entrypoint, help-driven discovery, stable subcommands, full operation coverage |
| **Cicadas Maintainer** | repo-local versioning, documentation migration, low-regression wrapper architecture |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- Introduce a common repo-local Cicadas CLI that exposes subcommands for all existing deterministic Cicadas scripts.
- Update Cicadas markdown documentation and skill instructions to use the CLI instead of direct script invocation for standard user-facing flows.

**Quality Gates:**
- Existing deterministic behavior remains intact behind the new CLI interface.
- The CLI is sufficiently discoverable for agents via consistent subcommand naming and `--help` output.

### Growth Features (Post-MVP)

**v2: Packaging and Distribution**
- Evaluate optional packaging or launcher strategies once skills and versioning have a clearer distribution model.

**v3: Agent-Specific Ergonomics**
- Add richer machine-friendly help or structured command introspection if plain CLI help proves insufficient.

### Vision (Future)

- Cicadas presents one stable command contract regardless of internal implementation details or future packaging model.

---

## Functional Requirements

### 1. Common Command Surface

**FR-1.1:** Cicadas must provide one repo-local CLI entrypoint for deterministic lifecycle operations.
- The entrypoint must be the recommended invocation path for agents and maintainers.

**FR-1.2:** The CLI must expose subcommands corresponding to the existing deterministic scripts.
- Standard lifecycle operations such as init, kickoff, branch, status, check, signal, archive, prune, history, lifecycle creation, skill validation, and skill publish must be invocable through the CLI.

**FR-1.3:** The CLI must provide built-in help output at the top level and for subcommands.
- Help text must be sufficient for an agent to identify the purpose and parameters of a command at runtime.

---

### 2. Behavioral Parity and Migration

**FR-2.1:** The CLI must delegate to existing deterministic functionality without materially changing lifecycle semantics in MVP.
- Wrapping the scripts should not require redesigning the underlying workflow during this initiative.

**FR-2.2:** Cicadas documentation and skill instructions must reference the CLI contract instead of direct script paths for normal usage.
- Markdown references should teach the common entrypoint as the public interface.

**FR-2.3:** The repo must preserve project-local ownership of Cicadas behavior.
- The MVP must not require a machine-global Cicadas installation in order to use the new interface.

---

## Non-Functional Requirements

- **Performance:** CLI startup and dispatch overhead should remain small relative to current script execution, and should not noticeably degrade interactive usage.
- **Reliability:** Each wrapped subcommand should return clear exit codes and surface underlying failures without hiding actionable error details.
- **Security:** The CLI must not introduce new privilege assumptions or remote installation requirements; it should preserve the repository's existing local execution model.
- **Maintainability:** Command registration and help text should be organized so adding or updating a lifecycle command does not require editing many duplicated docs or wrappers.

---

## Open Questions

- Should direct script entrypoints remain supported as compatibility shims during migration, or is updating internal references sufficient for MVP?
- Does agent optimization require plain argparse-style help only, or should the CLI eventually expose structured metadata for commands?

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Wrapper layer drifts from underlying script behavior | Medium | High | Keep MVP focused on delegation to existing implementations, and validate parity with tests around core commands. |
| Documentation migration leaves mixed invocation patterns that confuse agents | Medium | Medium | Audit skill/docs references systematically and update the common user-facing paths in the same initiative. |
| Entry-point choice creates avoidable churn later | Medium | Medium | Choose a command contract that can survive future packaging changes, and treat distribution details as an internal concern. |
