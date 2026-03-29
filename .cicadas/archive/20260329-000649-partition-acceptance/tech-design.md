
# Tech Design: Partition Acceptance

## Progress

- [x] Overview & Context
- [x] Tech Stack & Dependencies
- [x] Project / Module Structure
- [x] Architecture Decisions (ADRs)
- [x] Data Models
- [x] API & Interface Design
- [x] Implementation Patterns & Conventions
- [x] Security & Performance
- [x] Implementation Sequence

---

## Overview & Context

**Summary:** Two parallel tracks. Track 1 is purely textual: add `#### Acceptance Criteria`, `#### Artifact Type`, and `#### How to Run` subsections to each partition block in `approach.md`, and update `emergence/approach.md` to generate them. Track 2 is new infrastructure: a typed, append-only event log (`events.jsonl`) per initiative, written via `emit_event.py` (which encapsulates `flock` for concurrent-write safety) and read exclusively via `get_events.py`. Track 2 then gets wired into existing lifecycle scripts as emission side-effects, into `implementation.md` for coding agent rules, and into `status.py` for human visibility.

### Cross-Cutting Concerns

1. **`get_registry_root()` routing** — All event log writes must go through `get_registry_root()` so linked worktrees write to the primary worktree's `.cicadas/`. This is the same pattern used by all existing scripts for `registry.json`.
2. **`get_events` as the abstraction boundary** — No script, test, or agent reads `events.jsonl` directly. This decouples consumers from the file format and makes future layout changes (e.g. per-branch files) transparent.
3. **Events are informational, not authoritative** — Git state and `registry.json` remain the source of truth. Events can be missing without breaking Cicadas. This keeps the coupling loose.

### Brownfield Notes

- `kickoff.py`, `branch.py`, `archive.py`, `open_pr.py` each get one `emit_event()` call added at their natural completion point. No existing logic changes.
- `status.py` adds a call to `get_events` per active initiative; output is appended to the existing status report.
- `utils.py` has no file-locking utilities today — locking lives in `emit_event.py` only.
- `branch.py` parses only the `yaml partitions` fenced block from `approach.md`; the new subsections are outside that block and don't affect the parser.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.12 (tests) / 3.13 (scripts) | Existing constraint |
| **Locking** | `fcntl.flock` (stdlib) | No new dependencies; sufficient for local filesystems |
| **Serialization** | JSONL (one JSON object per line) | Append-friendly; easy to stream and filter |
| **Testing** | stdlib `unittest` | Existing constraint |

**New dependencies introduced:** None.

---

## Project / Module Structure

```
src/cicadas/
├── scripts/
│   ├── emit_event.py        # [NEW] Append typed event to events.jsonl with flock
│   ├── get_events.py        # [NEW] Read and filter event stream; only consumer of events.jsonl
│   ├── kickoff.py           # [MODIFIED] Emit initiative.kicked_off
│   ├── branch.py            # [MODIFIED] Emit branch.created, worktree.created
│   ├── archive.py           # [MODIFIED] Emit specs.archived
│   ├── open_pr.py           # [MODIFIED] Emit pr.opened or pr.blocked
│   └── status.py            # [MODIFIED] Surface recent events per initiative
├── templates/
│   └── approach.md          # [MODIFIED] Add AC, Artifact Type, How to Run per partition block
├── emergence/
│   └── approach.md          # [MODIFIED] Add generation guidance for new subsections
├── implementation.md         # [MODIFIED] Add task.complete and partition.complete emission rules
└── SKILL.md                  # [MODIFIED] Document event log in Operations section
```

**Key structural decisions:**
- `emit_event.py` is a standalone script (not a utility function in `utils.py`) so it can be called by coding agents via CLI without importing Cicadas internals.
- `get_events.py` is also a standalone script for the same reason — Chorus calls it directly.
- Locking is entirely inside `emit_event.py`; callers don't manage locks.

---

## Architecture Decisions (ADRs)

### ADR-1: Single `events.jsonl` per initiative, not per-branch files

**Decision:** One append-only JSONL file at `.cicadas/active/{initiative}/events.jsonl`, written by all agents and scripts involved in the initiative.

**Rationale:** A single file gives observers a unified chronological timeline without needing to discover and merge multiple files. Concurrent write safety is handled by `flock` inside `emit_event.py`. Event emission frequency is "development speed" (tens of events per initiative, not thousands per second), so lock contention is negligible. Per-branch files are a future option if scale requires it — `get_events` abstraction makes this a two-way door.

**Affects:** `emit_event.py`, `get_events.py`, all callers

---

### ADR-2: `emit_event.py` as CLI script, not utility function

**Decision:** Event emission is exposed as a CLI script (`python emit_event.py --type ... --data ...`), not as a Python function imported by other scripts.

**Rationale:** Coding agents running in worktrees call it via shell command, consistent with how they call `signal.py`, `open_pr.py`, etc. Python callers (other scripts) can also invoke it via `subprocess` or import it — but the CLI interface is the contract. This means agents don't need to know the internal data format; they just call the script.

**Affects:** `emit_event.py`, `kickoff.py`, `branch.py`, `archive.py`, `open_pr.py`

---

### ADR-3: `flock` for concurrent write safety

**Decision:** `emit_event.py` acquires an exclusive `fcntl.flock` on `events.jsonl` before appending and releases it after.

**Rationale:** Multiple partition worktrees may emit events concurrently (e.g. two agents completing tasks at the same moment). `flock` serializes these safely on POSIX filesystems (macOS, Linux) without a separate lock file. Windows is not a supported platform for Cicadas scripts.

**Affects:** `emit_event.py`

---

### ADR-4: Events are informational, not authoritative

**Decision:** `registry.json` and git state remain the source of truth. Events cannot be queried by Cicadas scripts for decision-making (e.g. "is this branch registered?" still reads registry, not events).

**Rationale:** Keeps the event log as a one-way observation channel. Avoids creating circular dependencies where Cicadas scripts need to read their own event log to function. Also means missing events (e.g. an agent that forgot to emit) don't break the system.

**Affects:** All scripts — they emit but never read events for decisions

---

### ADR-5: New partition spec subsections embedded in approach.md, not in separate files

**Decision:** `#### Acceptance Criteria`, `#### Artifact Type`, and `#### How to Run` are subsections inside each partition block in `approach.md`, not separate per-partition files.

**Rationale:** Keeps the partition spec self-contained. The evaluator reads one document and locates each partition by section heading. Separate files add file-management overhead and fragment the spec. The `yaml partitions` block (machine-read by `branch.py`) is unchanged.

**Affects:** `templates/approach.md`, `emergence/approach.md`

---

## Data Models

### Event Schema

```json
{
  "timestamp": "2026-03-28T14:32:01.123456Z",
  "type": "branch.created",
  "initiative": "partition-acceptance",
  "branch": "feat/event-log-infrastructure",
  "data": { }
}
```

**Field rules:**
- `timestamp` — ISO 8601 with microseconds, UTC, emitted at write time
- `type` — dotted namespace string; see event catalog below
- `initiative` — initiative name from registry context or `--initiative` arg
- `branch` — current git branch at time of emission (`git branch --show-current`)
- `data` — type-specific payload; always an object (never null/array)

### Event Catalog

| Type | Emitter | Key `data` fields |
|------|---------|-------------------|
| `initiative.kicked_off` | `kickoff.py` | `intent`, `owner` |
| `branch.created` | `branch.py` | `modules`, `intent`, `initiative` |
| `worktree.created` | `branch.py` | `worktree_path` |
| `specs.archived` | `archive.py` | `archive_path`, `archive_type` |
| `pr.opened` | `open_pr.py` | `base_branch`, `platform`, `url` |
| `pr.blocked` | `open_pr.py` | `base_branch`, `verdict` |
| `task.complete` | coding agent | `task` (description string) |
| `partition.complete` | coding agent | `summary`, `canon_entry`, `notes_for_evaluator` |

### `events.jsonl` location

`.cicadas/active/{initiative}/events.jsonl` — always in the primary worktree, resolved via `get_registry_root()`.

---

## API & Interface Design

### `emit_event.py`

```
python emit_event.py \
  --initiative {name} \
  --type {event-type} \
  [--data '{json-object}']   # defaults to {}
```

- `--initiative` is required (cannot always be auto-detected in worktrees)
- Exits 0 on success, non-zero on write failure
- Creates `events.jsonl` if absent (including parent dir)

### `get_events.py`

```
python get_events.py \
  --initiative {name} \
  [--type {prefix-or-exact}]   # e.g. "partition" matches "partition.complete"
  [--since {ISO-8601}]
  [--last {N}]                  # most recent N events
```

- Outputs JSONL to stdout, chronologically sorted
- Exits 0 even if no events match (empty output)
- Exits 1 if `events.jsonl` is malformed

### Backward Compatibility

`status.py`, `kickoff.py`, etc. must handle the case where `events.jsonl` does not exist (older initiatives). Treat as empty — no error.

---

## Implementation Patterns & Conventions

### Event Emission in Scripts

```python
# At the end of the successful path in kickoff.py:
subprocess.run([
    sys.executable, str(Path(__file__).parent / "emit_event.py"),
    "--initiative", name,
    "--type", "initiative.kicked_off",
    "--data", json.dumps({"intent": intent, "owner": owner}),
], check=False)  # Never let event emission failure abort the main script
```

**Rule:** Event emission is always `check=False` — a failure to emit must never abort the primary operation.

### Agent Invocation (from implementation.md)

```bash
python {cicadas-dir}/scripts/emit_event.py \
  --initiative {initiative-name} \
  --type task.complete \
  --data '{"task": "Create models/user.py: Define User class"}'
```

### Testing Pattern

```python
class TestEmitEvent(CicadasTest):
    def test_creates_events_file(self):
        self.init_git()
        # call emit_event.py via subprocess
        # assert events.jsonl exists and contains one valid JSON line
```

**Coverage expectation:** `emit_event.py` and `get_events.py` at 90%+; integration tests use real temp filesystem (no mocks for file I/O).

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| Agent-controlled `--data` content | `data` is stored as-is; `get_events` outputs it as-is; consumers are responsible for treating it as data |
| Path traversal via `--initiative` | Validate initiative name against `[a-z0-9-]+` pattern before constructing path |

### Performance

Lock hold time is the duration of a single JSONL line write — microseconds. No concern at development-speed event rates.

### Observability

The event log is itself the observability layer. `status.py` surfaces the last 5 events per initiative.

---

## Implementation Sequence

1. **P1 (parallel)** — Template changes: `approach.md` template + `emergence/approach.md` guidance
2. **P2 (parallel)** — Event infrastructure: `emit_event.py`, `get_events.py`, tests
3. **P3 (depends on P2)** — Integration: wire emit into `kickoff.py`, `branch.py`, `archive.py`, `open_pr.py`; update `status.py`; update `implementation.md` and `SKILL.md`

**Parallel work:** P1 and P2 share no files and can run concurrently in isolated worktrees.

**Known implementation risks:**
- Existing `test_kickoff.py`, `test_branch.py` etc. may need minor updates if they assert on exact script output that now includes event emission messages.
- `emit_event.py` called via `subprocess` from other scripts: use `sys.executable` to ensure the same Python interpreter is used.
