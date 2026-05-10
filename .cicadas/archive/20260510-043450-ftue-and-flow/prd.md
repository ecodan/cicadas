---
summary: "ftue-and-flow improves the first-time user experience and ongoing process legibility of Cicadas for solo developers. It introduces a full tutorial mode at init, toggleable next-step hints after every CLI command, better status readability, and clearer getting-started documentation — all additive, never breaking existing workflows."
phase: "clarify"
when_to_load:
  - "When defining or reviewing initiative goals, users, scope, success criteria, and risks."
  - "When validating that implementation still aligns with the intended problem and outcomes."
depends_on: []
modules:
  - "src/cicadas/scripts/init.py"
  - "src/cicadas/scripts/cicadas.py"
  - "src/cicadas/scripts/status.py"
  - "src/cicadas/scripts/kickoff.py"
  - "src/cicadas/scripts/branch.py"
  - "src/cicadas/scripts/utils.py"
  - "README.md"
  - "HOW-TO.md"
  - "src/cicadas/emergence/"
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

# PRD: ftue-and-flow

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

---

## Executive Summary

Cicadas is powerful but opaque — new users frequently stall at the mental model, the first commands, and the invisible connections between phases. `ftue-and-flow` fixes this by introducing a full interactive tutorial mode at `cicadas init`, toggleable next-step hints after every CLI command, and clearer documentation. The goal: a solo developer installs Cicadas and successfully completes their first full task cycle (clarify → kickoff → branch → implement → PR) without external help.

### What Makes This Special

- **Tutorial-first init** — Instead of silently creating a `.cicadas/` folder and leaving the user stranded, `cicadas init` can walk the user through a toy initiative that teaches every concept hands-on.
- **Breadcrumbs by default** — Every CLI command prints a concise "Next:" hint, so the next step is always one line away. Veterans can suppress this with a flag or config setting — no noise for experienced users.
- **Additive, non-breaking** — Every improvement is opt-in or purely additive. Existing workflows, output formats, and automation scripts are entirely unaffected.

---

## Project Classification

**Technical Type:** Developer Tool  
**Domain:** Productivity / Developer Experience  
**Complexity:** Medium — touches CLI scripts, templates, documentation, and the emergence flow; no new external dependencies  
**Project Context:** Brownfield — layered on top of the existing Cicadas CLI and methodology

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **Complete the first task cycle unassisted** — A brand-new user can go from `cicadas init` to a merged task branch PR without consulting external docs or asking for help.
2. **Always know the next step** — At every point in the flow, the user can see what command to run next without reading the README.
3. **Suppress guidance when ready** — An experienced user can silence all hints with a single config toggle and see no change to their existing output.

### Technical Success

The system is successful when:

1. **All hint output is additive** — No existing command output is removed or reformatted; hints appear as a distinct trailing block.
2. **Tutorial mode is self-contained** — The tutorial creates a real `.cicadas/` structure and real git artifacts; it is not a simulation.
3. **All new behavior is tested** — New CLI output, tutorial flow, and config toggle have test coverage.

### Measurable Outcomes

- A new user can reach their first merged task branch PR in a single session (target: < 30 minutes from install).
- The `--no-hints` flag (or `hints: false` in config) produces output byte-for-byte identical to current output.
- Getting-started documentation covers the full cycle with working commands a user can copy-paste.

---

## User Journeys

### Journey 1: Alex — Solo Developer, First Project

Alex is a senior engineer who heard about Cicadas from a colleague and installs it on a greenfield side project. They run `cicadas init` and are immediately confronted with a silent success message and a folder. They open the README, but it assumes familiarity with terms like "canon," "emergence," and "initiative branch" — all foreign. Alex types `cicadas` to see a command list, picks `kickoff`, and gets a usage error because there's no draft yet. Thirty minutes later, frustrated, they close the terminal. 

With `ftue-and-flow`: Alex runs `cicadas init`, is offered a tutorial, and follows a guided walkthrough that creates a toy "hello-cicadas" initiative, explains each concept inline, and ends with Alex having pushed a real feature branch. The next-step hints then carry them through their real first initiative.

**Requirements Revealed:** Tutorial mode at init, inline concept explanations, next-step hints on every command, clear first-run success state.

---

### Journey 2: Jordan — Returning User After a Break

Jordan used Cicadas six months ago and is picking up a new project. They remember the general shape but can't recall the exact command sequence after kickoff. They run `cicadas status` and see branch names and states, but nothing tells them what to do next. They dig through README and the SKILL.md file to find the next step.

With `ftue-and-flow`: Jordan runs `cicadas status` and sees a "Next:" section that identifies the logical next lifecycle step and prints the exact command. They're back in flow in under a minute.

**Requirements Revealed:** Context-aware next-step output in `status`, lifecycle-aware "Next" suggestions, hints for returning users.

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Alex (first-timer)** | Tutorial mode, concept explanations, next-step hints, good getting-started docs |
| **Jordan (returning user)** | Status improvements, lifecycle-aware next-step, suppression for experts |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- **Toggleable next-step hints** — After every CLI command that advances the lifecycle (init, kickoff, branch, status, archive, update-index, open-pr), print a concise "Next:" block. Suppressed when `--no-hints` is passed or `hints: false` is set in `.cicadas/config.json`. Default: on.
- **Tutorial mode at `cicadas init`** — When `--tutorial` flag is passed (or offered interactively on first run), walk through a complete toy initiative: creates real `.cicadas/` structure, a real draft, real kickoff, real branch, and explains each step inline. Ends at the point where the user would implement a task.
- **`cicadas status` next-step awareness** — When `lifecycle.json` is present, status already surfaces "Next"; extend this to also work when lifecycle is absent, inferring the next logical step from registry state.
- **README & HOW-TO rewrite** — Replace the current reference-style docs with a getting-started narrative that covers the full first cycle with copy-paste commands.

**Quality Gates:**
- All hint output is additive — `--no-hints` produces zero diff against current output.
- Tutorial mode creates real git artifacts (not simulated).
- All new behavior covered by tests.
- Existing test suite passes without modification.

### Growth Features (Post-MVP)

**v2: Contextual Help**
- `--explain` flag on any command prints a paragraph describing what the command does, why it exists, and how it fits the flow.
- `cicadas help <command>` extended with examples and cross-references.

**v3: Interactive Flow Coach**
- An optional "coach" mode that watches git state and proactively reminds users of Reflect before commit, Code Review before PR, etc.

### Vision (Future)

- Web-based interactive tutorial that mirrors the CLI experience for onboarding workshops.
- Telemetry-driven improvement: opt-in usage signals identify where users stall most frequently.

---

## Functional Requirements

### 1. Next-Step Hints

**FR-1.1:** After every lifecycle-advancing CLI command, the system MUST print a "Next:" hint block below the existing output.
- The hint block is visually distinct (e.g., a blank line separator and a `💡 Next:` prefix).
- The hint contains the exact command to run next, with a one-sentence explanation.
- The hint is context-aware: it varies based on current lifecycle state (e.g., after `kickoff`, hint points to `branch`; after `branch`, hint points to implement + reflect + open-pr).

**FR-1.2:** The system MUST support suppressing hints globally via config.
- `hints: false` in `.cicadas/config.json` suppresses all hint output.
- When suppressed, command output is byte-for-byte identical to current behavior.

**FR-1.3:** The system MUST support suppressing hints per-invocation via a CLI flag.
- `--no-hints` on any command suppresses hint output for that invocation only.
- This flag is available on all lifecycle commands.

**FR-1.4:** Hint suppression MUST be additive — no existing output is removed or reformatted regardless of hint state.

---

### 2. Tutorial Mode

**FR-2.1:** `cicadas init` MUST offer a tutorial mode.
- On first run (no existing `.cicadas/` directory), the user is asked: "Would you like a guided tutorial? (yes / no)".
- `cicadas init --tutorial` skips the prompt and goes directly to tutorial mode.
- `cicadas init --no-tutorial` skips the prompt and performs the standard init only.

**FR-2.2:** Tutorial mode MUST create real Cicadas artifacts.
- Creates a real `.cicadas/` structure (identical to standard init).
- Creates a real draft initiative (`hello-cicadas`) with pre-filled spec stubs.
- Runs real `kickoff` and `branch` commands, creating real git branches.
- No simulation — the tutorial state is a real, usable Cicadas project state.

**FR-2.3:** Tutorial mode MUST explain each concept inline as it executes.
- Before each step, print a 2–3 sentence explanation of what is about to happen and why.
- After each step, print what was created/changed and where to find it.
- The tutorial covers: init → draft → kickoff → branch → (implement placeholder) → next steps.

**FR-2.4:** Tutorial mode MUST end with a clear summary and pointer to next steps.
- Print a "You're ready!" summary listing what was created.
- Print the next command to run to start their first real initiative.

---

### 3. Status Next-Step Awareness

**FR-3.1:** `cicadas status` MUST always show a "Next:" suggestion, even when no `lifecycle.json` is present.
- When lifecycle is present: existing behavior (already shows "Next" from lifecycle steps).
- When lifecycle is absent: infer next step from registry state (e.g., "No active initiatives — run `cicadas init` to get started" or "Initiative X has no feature branches — run `cicadas branch ...`").
- When no `.cicadas/` exists at all: print a friendly bootstrap message.

**FR-3.2:** The inferred next-step suggestion MUST include the exact command to run, not just a description.

---

### 4. Documentation

**FR-4.1:** `README.md` MUST include a getting-started section that covers the full first cycle.
- Narrative prose (not just a command list) that explains each phase.
- Copy-paste commands that work in a real repo.
- Covers: install → init → first initiative → kickoff → branch → implement → PR → merge.

**FR-4.2:** `HOW-TO.md` MUST be updated to reflect the new tutorial mode and hint system.
- Documents how to enable/disable hints.
- Documents how to run the tutorial.

---

## Non-Functional Requirements

- **Performance:** Hint output must add < 50ms to any command's wall time. Tutorial mode is interactive and has no latency constraint beyond normal git operations.
- **Reliability:** `--no-hints` and `hints: false` must be 100% reliable — any accidental hint output in suppressed mode is a bug. Tutorial mode must be idempotent: running it twice on the same repo must not corrupt state (it should detect the existing `hello-cicadas` initiative and skip or warn).
- **Security:** Tutorial creates real git branches — must not push to remote automatically. All tutorial artifacts must be clearly labeled so users know they're tutorial artifacts.
- **Maintainability:** Hint strings must be centralized (not scattered across scripts) so they can be updated in one place. Tutorial flow must be a single script, not distributed logic. Test coverage ≥ 80% on all new code paths.

---

## Open Questions

~~- **Q1**: Separate `tutorial.py` or integrated into `init.py`?~~ **Resolved: separate `tutorial.py`.**
~~- **Q2**: Hints default-on for all users or only new installs?~~ **Resolved: default-on for all users; can be toggled off per-initiative at any time.**
~~- **Q3**: Visual treatment for hint blocks?~~ **Resolved: ANSI color (must degrade gracefully when stdout is not a TTY).**
~~- **Q4**: `config.json` boolean vs sentinel file?~~ **Resolved: `hints` boolean in `.cicadas/config.json` (per-initiative, not global).**

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hint output breaks pipe/scripting usage | Medium | High | `--no-hints` flag; hints written to stderr or only when stdout is a TTY (TBD in tech design) |
| Tutorial creates orphan git branches cluttering repos | Low | Medium | Label tutorial branches clearly (`tutorial/hello-cicadas`); document cleanup; consider auto-cleanup at tutorial end |
| Existing test suite breaks due to changed stdout | Medium | High | Hints are additive and suppressed by `--no-hints`; all existing tests run with `--no-hints` or equivalent |
| Scope creep into full CLI redesign | Medium | Medium | MVP is strictly additive — no refactoring of existing output formats allowed in this initiative |
| Tutorial becomes stale as CLI evolves | Low | Medium | Tutorial is driven by real scripts, not hardcoded strings — it stays current automatically |
