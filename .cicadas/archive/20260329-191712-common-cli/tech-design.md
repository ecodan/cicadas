---
next_section: "Approach"
---

# Tech Design: common-cli

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

**Summary:** The technical solution is to add a common repo-local CLI script inside `src/cicadas/scripts/` that becomes the public invocation surface for deterministic Cicadas operations, while preserving the existing script implementations as the behavioral core during MVP. This keeps the change narrow: agents and docs move to one command contract, but the underlying lifecycle logic remains in the current scripts until a later refactor proves worthwhile.

The CLI should be implemented as a Python script entrypoint that dispatches to named subcommands, each of which delegates to an existing script module or extracted `main(argv)`-style function. The architecture emphasizes discoverability, parity, and low migration risk: command registration should be centralized, help text should be generated from the public command table, and existing behavior should remain testable through both legacy script paths and the new CLI during the transition.

### Cross-Cutting Concerns

1. **Behavioral parity** — The CLI must not subtly change lifecycle semantics, exit codes, or expected output in MVP.
2. **Discoverability** — Help text is a runtime contract for agents, so command descriptions and argument exposure must be explicit and centrally maintained.
3. **Migration safety** — Documentation and skill instructions must move to the CLI without breaking internal maintainability or forcing an all-at-once rewrite of deterministic logic.

### Brownfield Notes

This initiative touches the existing script surface in `src/cicadas/scripts/`, the Cicadas skill/docs that currently teach direct script invocation, and the test suite around deterministic utilities. It must not change `.cicadas/` storage layout, lifecycle semantics, or the current repo-local distribution model. Existing script modules should remain the source of operational behavior during MVP, even if some internal refactoring is needed to make them cleanly callable from a shared CLI script in the same directory.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.11+ | Matches the current deterministic implementation and existing runtime expectations. |
| **Framework** | Standard library `argparse` | Sufficient for a repo-local CLI, keeps help output predictable, and avoids adding packaging-oriented abstractions too early. |
| **Database** | None | Cicadas state remains filesystem- and JSON-based. |
| **ORM / Query** | None | Not applicable. |
| **Auth** | None | Local repo command execution only; no new auth boundary introduced. |
| **Testing** | `pytest` | Already available in the repo dev dependencies and well-suited for CLI-focused command tests. |
| **Key Libraries** | Existing standard library + current utility modules | Minimizes risk and keeps the wrapper layer thin. |

**New dependencies introduced:**
- None planned for MVP — the CLI should use standard library tooling unless an implementation blocker is discovered.

**Dependencies explicitly rejected:**
- `click` / `typer` — helpful for polished CLIs, but unnecessary for MVP and likely to over-center Python packaging before the broader Cicadas distribution model is settled.
- A machine-global installer dependency — rejected because it would weaken per-project versioning and conflict with repo-local ownership.

---

## Project / Module Structure

```text
/Users/dcripe/dev/code/thirdparty/cicadas/
├── src/cicadas/
│   ├── scripts/
│   │   ├── cicadas.py              # New common CLI entrypoint and parser bootstrap
│   │   ├── command_registry.py     # Shared subcommand metadata and registration helpers
│   │   ├── *.py                    # [MODIFIED] Existing implementations made callable from the common CLI
│   │   └── utils.py                # [MODIFIED] Shared helpers remain here unless a cleaner module split emerges
│   └── README.md                   # [MODIFIED] Public usage updated to the CLI contract
├── tests/
│   ├── test_cli.py                 # New CLI-level dispatch/help coverage
│   └── ...                         # [MODIFIED] Existing script tests extended for parity where needed
├── README.md                       # [MODIFIED] User-facing examples updated to common CLI
└── .agents / skill docs            # [MODIFIED] Instructions updated to teach CLI instead of script paths
```

**Key structural decisions:**
- The new public interface lives in `src/cicadas/scripts/` to stay aligned with the Anthropic Standard Skills script layout.
- Command registration should be centralized in a small shared registry module so top-level help, subcommand wiring, and documentation have one source of truth.
- Refactoring script modules to expose callable entry functions is allowed, but full relocation of all business logic out of `scripts/` is not required for MVP.

---

## Architecture Decisions (ADRs)

### ADR-1: Introduce a thin CLI wrapper instead of rewriting script implementations

**Decision:** Add a new repo-local CLI layer that delegates to existing deterministic implementations, rather than rewriting all lifecycle logic into a new command architecture in one step.

**Rationale:** The initiative’s value is interface consolidation and discoverability, not behavioral redesign. A thin wrapper lowers regression risk, keeps tests meaningful, and allows documentation to converge on a single command surface quickly.

**Affects:** `src/cicadas/scripts/cicadas.py`, `src/cicadas/scripts/command_registry.py`, existing script entrypoints, CLI tests, documentation.

---

### ADR-2: Use standard-library `argparse` for MVP command parsing

**Decision:** Build the CLI on `argparse` rather than adding a third-party CLI framework.

**Rationale:** `argparse` is already available, produces familiar help output, and avoids coupling the command surface to a Python packaging story that is still unsettled. It is fully adequate for top-level and subcommand help, which are the main UX requirements.

**Affects:** CLI parser implementation, help text conventions, test fixtures.

---

### ADR-3: Keep the command contract repo-local and versioned with the project

**Decision:** The canonical CLI entrypoint will be shipped as a script inside the repo’s `src/cicadas/scripts/` directory and invoked from the project’s own Cicadas copy, rather than assuming a machine-global install.

**Rationale:** Repo-local ownership is one of the initiative’s core constraints. It preserves per-project versioning and prevents the public command contract from drifting independently of the repository’s Cicadas behavior.

**Affects:** Script layout, documentation examples, skill instructions, future packaging choices.

---

### ADR-4: Centralize subcommand metadata in a registry module

**Decision:** Define subcommands and their descriptions in a central registry module inside `src/cicadas/scripts/` instead of scattering parser setup across many files or embedding command names only in docs.

**Rationale:** The help surface is now a public interface. Centralized metadata reduces drift between command wiring, help text, and documentation, and makes command audits easier as the surface evolves.

**Affects:** `src/cicadas/scripts/command_registry.py`, `src/cicadas/scripts/cicadas.py`, documentation generation conventions, tests.

---

### ADR-5: Preserve legacy script entrypoints during migration, but demote them from public documentation

**Decision:** Existing script entrypoints may remain callable during MVP for compatibility and incremental migration, but docs and skill guidance should treat the common CLI as the default interface.

**Rationale:** This reduces rollout risk and avoids forcing an all-at-once implementation refactor, while still achieving the initiative’s user-facing goal of one taught interface. It also gives maintainers room to clean up internal structure after the public contract is in place.

**Affects:** Script modules, docs, tests, maintenance expectations for deprecated paths.

---

## Data Models

### New Models

The initiative does not require changes to `.cicadas/` project-state schemas. The primary new data model is an in-code command registry used to define the public command surface.

```python
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CommandSpec:
    name: str
    help: str
    register_parser: Callable
    run: Callable
```

**Key field decisions:**
- `name` — explicit canonical subcommand token so docs and parser wiring share one identifier.
- `help` — treated as public runtime copy for top-level discovery.
- `register_parser` — keeps argument-definition logic close to the command implementation without hardwiring it into the top-level entrypoint.
- `run` — enables uniform dispatch after parsing.

### Modified Models

| Model | Change | Migration Required? |
|-------|--------|-------------------|
| `.cicadas/*` initiative state files | No schema change | No |
| Existing script module API surface | Add callable entry function where missing | No |
| Documentation command examples | Replace script-path invocations with CLI subcommands | No |

### Schema / Migration Notes

No data migration is required because this initiative changes invocation and documentation, not stored project state. If any script currently depends on `__name__ == "__main__"`-style inline parsing, that logic should be extracted into callable functions without altering the underlying `.cicadas/` file formats.

---

## API & Interface Design

### New Endpoints / Commands

The canonical public interface should follow one base script with shallow verb-style subcommands. The command contract should be equivalent to:

```text
python {cicadas-dir}/scripts/cicadas.py --help
python {cicadas-dir}/scripts/cicadas.py status
python {cicadas-dir}/scripts/cicadas.py check
python {cicadas-dir}/scripts/cicadas.py kickoff <name> [--intent "..."]
python {cicadas-dir}/scripts/cicadas.py branch <branch-name> --initiative <name> [--intent "..."] [--modules "..."]
python {cicadas-dir}/scripts/cicadas.py create-lifecycle <name> [--active] [--pr-specs] [--pr-initiatives|--no-pr-initiatives] [--pr-features|--no-pr-features] [--pr-tasks]
python {cicadas-dir}/scripts/cicadas.py open-pr [--base <branch>]
python {cicadas-dir}/scripts/cicadas.py archive <name> --type <branch|initiative>
python {cicadas-dir}/scripts/cicadas.py prune <name> --type <branch|initiative>
python {cicadas-dir}/scripts/cicadas.py validate-skill <slug-or-path>
python {cicadas-dir}/scripts/cicadas.py skill-publish <slug> [--publish-dir DIR] [--symlink] [--force]
python {cicadas-dir}/scripts/cicadas.py emit-event --initiative <name> --type <event-type> [--data JSON]
python {cicadas-dir}/scripts/cicadas.py get-events --initiative <name> [--type prefix] [--since ISO8601] [--last N]
```

Help behavior:
- `python {cicadas-dir}/scripts/cicadas.py --help` lists all supported subcommands with one-line descriptions.
- `python {cicadas-dir}/scripts/cicadas.py <subcommand> --help` shows exact arguments and a concise purpose statement.
- Unknown subcommands should produce a non-zero exit code and point back to top-level help.

### Interface Contracts

```python
def build_parser() -> argparse.ArgumentParser:
    ...


def main(argv: list[str] | None = None) -> int:
    ...


def register_subcommands(subparsers) -> None:
    ...
```

Command handler contract:
- Each subcommand handler accepts parsed arguments and returns an integer exit code.
- Script-backed handlers may delegate by invoking the existing script entrypoints with explicit argv lists, while native handlers may call extracted implementation functions directly.
- Underlying stdout/stderr should pass through unchanged unless the CLI needs to add minimal context for parser-level failures.

### Backward Compatibility

Direct script execution may remain available during MVP as a compatibility path, but `python {cicadas-dir}/scripts/cicadas.py ...` becomes the documented interface. Existing users and tests that call scripts directly should keep working until a later cleanup initiative explicitly removes those paths. If deprecation messaging is added, it should be concise and must not interfere with script output contracts relied on by tests.

---

## Implementation Patterns & Conventions

### Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| CLI modules | `snake_case.py` | `cicadas.py`, `command_registry.py` |
| Subcommand names | kebab-case in user-facing CLI | `create-lifecycle`, `open-pr`, `skill-publish` |
| Python handlers | `snake_case` | `register_status_command()` |
| Shared specs | `PascalCase` dataclasses or simple functions | `CommandSpec` |
| Tests | `test_*.py` | `test_cli.py` |

### Error Handling Pattern

```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except SystemExit:
        raise
```

**Rules:**
- Parser errors should remain standard CLI usage errors with clear non-zero exits.
- Do not swallow underlying script failures; preserve actionable stderr and exit status.
- Keep wrapper-level messaging minimal so existing command outputs remain recognizable.

### Testing Pattern

```python
def test_top_level_help_lists_known_commands():
    ...


def test_status_subcommand_dispatches_successfully():
    ...
```

**Coverage expectations:** Cover top-level help, representative subcommand dispatch, unknown-command handling, and at least one parity test for delegated behavior on critical commands.
**Mocking strategy:** Prefer real temp repositories and filesystem interactions for command behavior; only use mocks for narrow parser/dispatch logic that has no I/O side effects.

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| Input validation | Use parser-level argument validation and preserve existing script validation for filesystem and git operations. |
| Accidental behavior change | Keep wrapper logic thin and route to existing deterministic implementations to reduce new attack or failure surface. |
| Command injection via shell-style composition | Invoke Python functions or explicit argv lists rather than shelling out through string concatenation inside the CLI wrapper. |
| Secrets / sensitive output | Preserve current local-execution model and avoid adding telemetry or remote dependency behavior in MVP. |

### Performance

| Concern | Target | Approach |
|---------|--------|---------|
| CLI startup overhead | Negligible relative to existing script runtime | Use standard library parsing and lazy-load heavier command modules if needed |
| Help responsiveness | Immediate on local execution | Keep command registry lightweight and avoid expensive repository scans during parser construction |
| Command execution parity | No meaningful regression from current script path | Delegate directly to current implementations rather than adding extra subprocess layers where possible |

### Observability

This initiative should not add a new telemetry system. Observability should rely on existing command output and test coverage.
- **Logs:** Preserve current stderr/stdout behavior from delegated implementations.
- **Metrics:** None required for MVP.
- **Traces:** None required for MVP.

---

## Implementation Sequence

1. **Foundation** *(blocking)* — Decide the canonical base invocation shape, add `cicadas.py`, and define the centralized command registry.
2. **Core dispatch** *(depends on 1)* — Wire representative subcommands and establish the pattern for delegating into existing script implementations.
3. **Full command coverage** *(depends on 2)* — Expose all deterministic script-backed operations through the common CLI, including less-frequent commands like events, tokens, review, synthesize, and unarchive where appropriate.
4. **Documentation migration** *(depends on 2, can overlap with 3)* — Update skill instructions, README content, and command references to teach the CLI contract.
5. **Testing** *(parallel with 2-4)* — Add CLI tests and parity coverage for critical command flows using real temp repos where behavior matters.
6. **Compatibility cleanup** *(depends on 3-5)* — Decide whether any direct-script compatibility notes or lightweight shims are needed, and ensure the final docs present one canonical path.

**Parallel work opportunities:** One implementation stream can build parser/dispatch infrastructure while another audits and updates documentation references, as long as the subcommand names are agreed early. Test additions can also proceed once the base contract is stable.

**Known implementation risks:**
- Some scripts may not currently expose clean callable entrypoints and may need light refactoring before they can be dispatched consistently.
- Command naming choices made now will become sticky because docs and agent behavior will train on them quickly.
- Full help discoverability may expose inconsistencies in existing script argument naming that should be normalized carefully without breaking compatibility.
