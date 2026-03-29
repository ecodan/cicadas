
# PRD: Partition Acceptance

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

Cicadas partition specs are human-readable planning documents. Chorus's partition-level execution model requires specs an automated evaluator can act on directly — falsifiable pass/fail criteria, a declared artifact type, and exact startup commands. Separately, Cicadas has no transparent observation layer: state transitions (initiative registered, branch created, task complete, partition complete, PR opened) are visible to humans via `status.py` but not machine-readable, making automated orchestration opaque. This initiative adds both: machine-testable partition specs and a general-purpose, append-only event log that any observer — human or Chorus — can consume.

### What Makes This Special

- **Machine-testable specs by default** — Acceptance criteria are falsifiable per-item checkboxes generated during Emergence, not prose summaries added post-hoc.
- **Transparent state machine** — Every significant Cicadas lifecycle transition is recorded as a typed event; observers don't need to reverse-engineer state from git history or registry diffs.
- **One-way dependency preserved** — Chorus consumes Cicadas events via `get_events`; Cicadas knows nothing about Chorus.

## Project Classification

**Technical Type:** Developer Tool / Framework
**Domain:** Infrastructure / AI-assisted development
**Complexity:** Medium — new scripts with file locking, integration into multiple existing scripts, plus template and instruction module changes
**Project Context:** Brownfield — extending existing Cicadas templates, emergence modules, and lifecycle scripts

---

## Success Criteria

### User Success

A Builder (or orchestrator) achieves success when:

1. **Partition specs are evaluatable without clarification** — After Emergence, each partition section in `approach.md` contains Acceptance Criteria, Artifact Type, and How to Run; an evaluator agent can consume the spec directly.
2. **State transitions are observable** — Any observer can call `get_events --initiative foo` and receive a chronological, typed stream of what happened to that initiative.
3. **Partition completion is machine-detectable** — When a coding agent finishes a partition, it emits a `partition.complete` event with structured payload; the supervisor detects this via `get_events` without polling git or watching arbitrary directories.

### Technical Success

The system is successful when:

1. `emit_event.py` writes typed, timestamped events to `.cicadas/active/{initiative}/events.jsonl` safely under concurrent access.
2. `get_events.py` returns a filtered, sorted event stream; no consumer touches `events.jsonl` directly.
3. `kickoff.py`, `branch.py`, `archive.py`, and `open_pr.py` each emit appropriate events as side effects.
4. `implementation.md` directs coding agents to emit `task.complete` and `partition.complete` events.
5. The `approach.md` template includes per-partition `## Acceptance Criteria`, `## Artifact Type`, and `## How to Run` subsections.
6. `emergence/approach.md` instructs the agent to generate those subsections during drafting.

### Measurable Outcomes

- Running `get_events --initiative foo` after a kickoff returns at least one `initiative.kicked_off` event.
- A spec produced by the updated Emergence flow can be consumed by a Chorus evaluator without Builder clarification.

---

## User Journeys

### Journey 1: Chorus Supervisor — Detecting Partition Completion

A coding agent finishes its assigned partition. Per `implementation.md`, it calls `emit_event.py --type partition.complete --data '{...}'`. The Chorus supervisor, polling or watching, calls `get_events --initiative foo --type partition.complete --since {start}` and receives the event with summary, canon candidate, and evaluator notes. It triggers the evaluator. No shared directory, no sentinel file, no Chorus-specific path in Cicadas.

**Requirements Revealed:** `emit_event.py`, `get_events.py` with type/since filtering, `partition.complete` event schema.

---

### Journey 2: Builder — Checking Initiative Progress

A Builder runs `status.py` and sees not just current branch/merge state but a recent event log: "14:32 branch.created feat/data-layer | 14:45 task.complete migrate schema | 15:10 partition.complete feat/data-layer". Full picture without querying git, reading registry, or parsing tasks.md manually.

**Requirements Revealed:** `status.py` integration, human-readable event surfacing.

---

### Journey 3: Coding Agent — Task and Partition Completion

The coding agent checks off a task in `tasks.md` and immediately calls `emit_event.py --type task.complete --data '{"task": "...", "branch": "..."}'`. When all partition tasks are done, it calls `emit_event.py --type partition.complete --data '{"summary": "...", "canon_entry": "...", "notes_for_evaluator": "..."}'`. Both events land in the initiative's `events.jsonl` and are immediately available to any observer.

**Requirements Revealed:** Coding agent instructions in `implementation.md`, event payload schemas, `emit_event.py` callable from any worktree.

---

### Journey 4: Builder — Running Emergence

The agent reads project tooling (`package.json`, `pyproject.toml`, `Makefile`, `Dockerfile`), infers artifact type, generates `## How to Run` with exact commands, and produces `## Acceptance Criteria` with falsifiable items. Untestable items are flagged `<!-- NEEDS MANUAL REVIEW -->`. Builder reviews and approves before kickoff.

**Requirements Revealed:** Artifact type inference, How to Run generation from tooling, untestable criterion flagging.

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Chorus Supervisor** | `get_events` with type/since filtering, `partition.complete` schema |
| **Builder** | `status.py` event surfacing, human-readable output |
| **Coding Agent** | `emit_event.py` callable from any worktree, task/partition schemas |
| **Builder (Emergence)** | Artifact type inference, AC generation, How to Run from tooling |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- `emit_event.py` — append events to `events.jsonl` with flock
- `get_events.py` — read and filter event stream
- Event emission wired into `kickoff.py`, `branch.py`, `archive.py`, `open_pr.py`
- `implementation.md` updated with task/partition completion event rules
- `status.py` surfaces recent events inline
- `approach.md` template updated with AC, Artifact Type, How to Run per partition
- `emergence/approach.md` updated with generation guidance
- `SKILL.md` documents event log in Operations section

**Quality Gates:**
- `emit_event.py` is safe under concurrent writes from parallel worktrees
- `get_events.py` is the only consumer of `events.jsonl` — no other code reads the file directly
- All existing tests pass; new tests cover emit and get

### Growth Features (Post-MVP)

**v2: Cicadas CLI**
- Unified `cicadas` entrypoint; `emit_event` and `get_events` become subcommands

**v3: Event-driven status**
- `status.py` derives state primarily from the event log rather than from git + registry separately

### Vision (Future)

- Per-branch event files if single-file contention becomes real at scale (two-way door, `get_events` abstraction makes this transparent)
- Event replay for audit and debugging

---

## Functional Requirements

### 1. Partition Spec Template

**FR-1.1:** `approach.md` template MUST include, within each partition section, three subsections: `#### Acceptance Criteria`, `#### Artifact Type`, and `#### How to Run`.

**FR-1.2:** `#### Acceptance Criteria` MUST use checkbox format (`- [ ]`) with example good/bad items and a `<!-- NEEDS MANUAL REVIEW -->` example.

**FR-1.3:** `#### Artifact Type` MUST enumerate valid values: `web-ui | rest-api | cli | library | background-service | full-stack`.

**FR-1.4:** `#### How to Run` MUST include `start`, `ready-check`, and `teardown` fields; `start` MAY be omitted for libraries and CLIs.

---

### 2. Emergence Guidance

**FR-2.1:** `emergence/approach.md` MUST instruct the agent to infer artifact type from partition description; ask when ambiguous.

**FR-2.2:** MUST instruct the agent to generate acceptance criteria matched to the artifact type.

**FR-2.3:** MUST instruct the agent to generate `#### How to Run` by detecting `package.json`, `pyproject.toml`, `Makefile`, or `Dockerfile`.

**FR-2.4:** MUST instruct the agent to flag untestable criteria with `<!-- NEEDS MANUAL REVIEW -->`.

---

### 3. Event Log — Write

**FR-3.1:** `emit_event.py` MUST append a single JSON line to `.cicadas/active/{initiative}/events.jsonl` in the primary worktree (via `get_registry_root()`).

**FR-3.2:** Each event MUST include: `timestamp` (ISO 8601), `type` (dotted string), `initiative`, `branch` (current branch at time of emission), and `data` (type-specific payload object).

**FR-3.3:** `emit_event.py` MUST use `fcntl.flock(LOCK_EX)` before writing and `LOCK_UN` after, so concurrent calls from parallel worktrees are safe.

**FR-3.4:** If `events.jsonl` does not exist, `emit_event.py` MUST create it (including parent directory).

---

### 4. Event Log — Read

**FR-4.1:** `get_events.py` MUST be the only interface for reading `events.jsonl`; no other script or agent reads the file directly.

**FR-4.2:** `get_events.py` MUST accept `--initiative`, optional `--type` (exact match or prefix), and optional `--since` (ISO 8601 timestamp) filters.

**FR-4.3:** Output MUST be JSONL to stdout, chronologically sorted, one event per line.

---

### 5. System Event Emission

**FR-5.1:** `kickoff.py` MUST emit `initiative.kicked_off` after registration completes.

**FR-5.2:** `branch.py` MUST emit `branch.created` after registration, and `worktree.created` if a worktree was created.

**FR-5.3:** `archive.py` MUST emit `specs.archived` after moving specs to archive.

**FR-5.4:** `open_pr.py` MUST emit `pr.opened` (with URL if available) or `pr.blocked` (if review verdict is BLOCK).

---

### 6. Agent Event Emission

**FR-6.1:** `implementation.md` MUST include a rule directing the coding agent to call `emit_event.py --type task.complete` after checking off each task in `tasks.md`.

**FR-6.2:** `implementation.md` MUST include a rule directing the coding agent to call `emit_event.py --type partition.complete` with `summary`, `canon_entry`, and `notes_for_evaluator` payload fields when all partition tasks are done.

**FR-6.3:** `SKILL.md` MUST document the event log, `get_events` interface, and the `task.complete` / `partition.complete` event types in the Operations section.

---

### 7. Status Integration

**FR-7.1:** `status.py` MUST display the most recent N events (suggested: 5) for each active initiative, sourced via `get_events`.

---

## Non-Functional Requirements

- **Concurrency:** `emit_event.py` must be safe when called simultaneously from multiple worktrees. `flock` is sufficient for local filesystems.
- **Backward compatibility:** Initiatives without `events.jsonl` must not cause errors in `status.py` or `get_events.py` — treat as empty event stream.
- **Maintainability:** No consumer reads `events.jsonl` directly; all reads go through `get_events`. This makes future format changes (e.g. per-branch files) transparent.

---

## Open Questions

- None.

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Emergence agent generates vague criteria despite instructions | Med | Med | `<!-- NEEDS MANUAL REVIEW -->` flag + Builder review before kickoff |
| How to Run inference fails for unusual build systems | Low | Low | Agent falls back to placeholder with `<!-- NEEDS MANUAL REVIEW -->` |
| `flock` not available on Windows | Low | Low | Cicadas runs on Unix (Mac/Linux); document this assumption |
| Coding agents forget to emit events | Med | Low | Low severity — events are informational; git state remains the authority |
| Existing tests break from script side-effect changes | Med | Med | Add `events.jsonl` assertions to test suite; run full suite before merging P3 |
