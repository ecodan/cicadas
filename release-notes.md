# Release Notes

## Unreleased

### Added

- **Initiative profiles**: The standard start flow now records `product`, `technical`, or `mixed` initiative profiles. Technical initiatives can use a new Technical Brief template and optional Operator Experience template while Tech Design, Approach, and Tasks remain mandatory for cross-module work.
- **Template coverage**: `tests/test_templates.py` now verifies the technical-profile templates share the compact front matter contract and that profile-aware guidance stays documented.

### Changed

- **UXD mock-up contract**: Screen-based UX drafts now require at least one editable HTML/CSS mock-up under `.cicadas/drafts/{initiative}/mockups/` before UX approval. The `ux.md` template includes a dedicated mock-up section, screenshot previews remain optional, and operator-only flows still use `operator-experience.md`.

## Version 0.8.3

### Unreleased

- **Skill builder removal**: Removed the built-in skill-builder triggers from `src/cicadas/SKILL.md` and marked the legacy skill-authoring docs as deprecated.

## Version 0.8.2

### Unreleased

- **Scan exclusions**: `scan_repository` now skips directories containing a `SKILL.md` file (SDD installs and agent skill bundles at arbitrary paths), root-level hidden/underscore dirs whose names contain a known SDD tool substring (`bmad`, `cicadas`, `gsd`, `openspec`), and any paths listed in the new `scan_exclude_paths` key in `.cicadas/config.json`. This prevents SDD state/output directories like `_bmad-output/` and vendored SDD installs from inflating `meaningful_file_count`, `estimated_loc`, and slice candidates.

## Version 0.8.0

### Added

- Adaptive canon bootstrap that classifies repos as `normal-repo`, `large-repo`, or `mega-repo`, writes `repo.json` / `repo-tree.jsonl` / `repo-context.md`, and seeds lazy `slices/` packs only for larger repos.
- Code Graph DB (currently supports python and java) to assist the coding agent in navigating large- and mega-repos.

### Changed

- Initiative completion now uses targeted canon reconcile for large and mega repos, updating touched slices by default and refreshing top-level orientation docs only when durable repo-wide truth changed.
- `init` no longer creates an empty `.cicadas/canon/modules/` directory up front.
- Optional code graph builds now write progressively to staged SQLite tables under `.cicadas/graph/`, emit `progress.json` / `progress-log.jsonl` with elapsed time and ETA, and expose `graph tail` / `graph watch` for long-running local builds.
- Code graph routing is more useful on large repos: deterministic `area-plan.json` output now captures seeded routing areas, `graph search` adds graph-native file/symbol/entrypoint search, `--exclude-tests` filters operational hunts, and JavaScript/TypeScript now have structural graph indexing.
- Java graph extraction now uses a structural baseline plus resumable semantic enrichment batches. Successful semantic batches are retained even when some files fail, bad files are quarantined via batch bisection, and graph metadata now reports `structural`, `semantic`, or `hybrid` Java coverage.
- Repo scan now excludes local Cicadas workspaces like `.cicadas-skill/` from inventory, scale heuristics, and graph routing seeds so repo graphs stay focused on operational code.

## Version 0.7.5

- **Context Optimization**: The five core initiative templates (`prd.md`, `ux.md`, `tech-design.md`, `approach.md`, `tasks.md`) now share a compact machine-readable front matter contract with `summary`, `modules`, `depends_on`, and `index` fields so agents can reload approved context without re-reading full drafting threads.
- **Reset Rules**: `SKILL.md` now defines explicit Branch Reset, Phase Reset, and Partition Reset rules. These rules re-anchor agents on approved file-backed state, reload indexed sections first, and opportunistically ask the host to clear or compact context when supported.
- **Clarify / Canon Routing**: `emergence/clarify.md` now refreshes the new front matter fields instead of `steps_completed`, `templates/canon-summary.md` includes a branch-start routing cue for compact context loading, and the synthesized canon now documents the compact-context workflow.
- **Verification**: Added `tests/test_templates.py` to verify the front matter contract, Clarify front matter guidance, and canon summary routing hint.
- **Common CLI Fix**: `cicadas.py` now forwards option-style subcommand arguments like `update-index --branch ... --summary ...` correctly instead of rejecting or misrouting them, and `tests/test_cli.py` includes a regression test for wrapper-based `update-index`.
- **Worktree Ergonomics**: Initiative and lightweight (`fix/`, `tweak/`, `skill/`) worktrees are no longer created implicitly by default. `.cicadas/config.json` now supports `auto_worktrees.initiatives`, `auto_worktrees.lightweight`, and `auto_worktrees.parallel_features`, and both `kickoff.py` and `branch.py` accept `--worktree` for explicit opt-in.
- **Safer Parent Resolution**: `branch.py` now resolves parent refs against both local branches and `origin/...`, so feature creation still works when the intended initiative parent exists only as a remote-tracking branch.
- **Visibility & Coverage**: `status.py` now lists initiative worktrees, `check.py` warns on stale initiative worktrees, and new integration tests cover config-enabled worktrees, remote-only parent refs, and worktree creation failure handling.
- **Common CLI Surface**: Added `src/cicadas/scripts/cicadas.py` and `command_registry.py` as the repo-local command entrypoint for deterministic Cicadas operations. The new surface wraps lifecycle, review, event, skill, and token commands behind one agent-discoverable `--help` tree while preserving the underlying scripts for compatibility.
- **CLI Coverage**: Added `tests/test_cli.py` to verify top-level help, representative command dispatch, lifecycle mutation through the wrapper, token subcommands, `update-index` forwarding, and clean failure on malformed `tokens show --full` input.
- **Docs**: Updated the canonical docs to explain the compact context contract, reset-boundary behavior, common CLI usage, and the new worktree defaults. Evals remain future work; these releases only add the scaffolding for better context hygiene.

## Version 0.7.0

- **Machine-Testable Partition Specs**: `approach.md` template now includes `#### Artifact Type`, `#### How to Run`, and `#### Acceptance Criteria` subsections in each partition block. `emergence/approach.md` (Step 4b) guides agents to infer artifact type, generate How to Run from `package.json`/`pyproject.toml`/`Makefile`/`Dockerfile`, and produce acceptance criteria by artifact type (rest-api → endpoint assertions, web-ui → interaction criteria, cli → stdout/exit, library → return values, background-service → side effects, full-stack → combined). `<!-- NEEDS MANUAL REVIEW -->` flags non-deterministic or external-dependency criteria.
- **Event Log Infrastructure**: New `emit_event.py` and `get_events.py` scripts. Each initiative maintains an append-only `events.jsonl` at `.cicadas/active/{initiative}/events.jsonl`. `emit_event.py` writes typed events with `fcntl.flock` for concurrent-write safety. `get_events.py` reads and filters by `--type` (exact or prefix), `--since` (ISO 8601), and `--last N`; outputs JSONL to stdout; exits 0 with empty output when `events.jsonl` is absent.
- **Event Log Integration**: Lifecycle scripts now emit events automatically: `kickoff.py` → `initiative.kicked_off`; `branch.py` → `branch.created` and `worktree.created`; `archive.py` → `specs.archived`; `open_pr.py` → `pr.opened` (gh/glab success) and `pr.blocked` (BLOCK verdict). All calls use `utils.emit()` — a non-fatal lazy-import wrapper so emit failures never abort primary operations.
- **Status event display**: `status.py` now shows the 5 most recent events per active initiative in the status output, with graceful handling of missing `events.jsonl`.
- **Implementation Rules 9 & 10**: `implementation.md` adds Rule 9 (emit `task.complete` after each task checkbox) and Rule 10 (emit `partition.complete` before partition PR, with `summary`, `canon_entry`, and `notes_for_evaluator` fields).
- **SKILL.md Event Log section**: New "Event Log" subsection in Operations documents the event log path, `emit_event`/`get_events` CLI, event schema, full lifecycle and agent event type tables, and the design invariant (`get_events.py` is the only consumer interface — direct file reads are forbidden).
- **utils.emit()**: Shared non-fatal event emitter added to `utils.py`. Replaces per-script `_emit` helpers; all lifecycle scripts import `emit` from utils.
- **Tests**: 16 new tests for `emit_event.py` and `get_events.py` (concurrent writes, type prefix matching, `--last`, `--since`, missing file); 4 new integration tests asserting events land in `events.jsonl` after kickoff, create_branch, and archive; 1 new test asserting `status.py` displays Recent events. 251 tests total.

## Version 0.6.3

- **Worktree Support**: `kickoff.py` now creates a linked git worktree (`../{repo}-initiative-{name}`) instead of switching the main worktree to the new branch. `branch.py` extended to also create worktrees for `fix/`, `tweak/`, and `skill/` branches (previously only parallel `feat/` partitions used worktrees). Multiple Cicadas workstreams can now run simultaneously without branch-stomping.
- **Registry Root Detection**: New `get_registry_root()` and `get_registry_dir()` in `utils.py`. Detects linked worktrees via `.git` file vs directory and routes `registry.json`/`index.json` I/O to the primary worktree, keeping shared state authoritative across all linked worktrees.
- **archive.py**: Added initiative-level worktree removal on archive (branch worktrees already worked; initiatives now cleaned up too).
- **Tests**: `CicadasTest.tearDown` now cleans up linked worktrees before deleting temp repos. New tests for `get_registry_root()`, `get_registry_dir()`, and kickoff worktree behavior. Updated branch and orchestration tests to reflect new worktree-first behavior (main worktree stays on default branch).

## Version 0.6.2

- **1-PR Archive Flow**: `archive.py` now snapshots the initiative's registry metadata into a `.cicadas_metadata.json` file within the archive folder. This allows you to include the archive move and registry cleanup in your main PR for a single-commit finalization.
- **Unarchive Script**: New `unarchive.py` tool. If a PR needs rework after being archived, run `cicadas unarchive {name}` to instantly restore the registry state and move files back to `active/`.
- **Integrated Guidance**: `open_pr.py` now detects initiative branches and recommends the 1-PR flow. `lifecycle-default.json` updated to prioritize Synthesize → Archive → Open PR sequence.
- **Tests**: New `tests/test_unarchive.py` validates metadata snapshotting and state restoration.

## Version 0.6.1

- **Agent Skill Authoring**: New `skill/` branch prefix and full skill lifecycle. `skill-create.md` — dialogue-driven authoring: start flow → 4-question clarifying dialogue → complete SKILL.md + optional bundled files (`scripts/`, `references/`, `assets/`) + `eval_queries.json` draft → kickoff + branch + validate. `skill-edit.md` — one diagnostic question, minimum-change before/after proposal, validate on apply. `validate_skill.py` — spec-compliance validator (name charset/length/dir-match, description ≤1024 chars, frontmatter delimiters; stdlib regex, handles single-line, folded, and block YAML scalars). `skill_publish.py` — copy or symlink active skill to `publish_dir` with pre-publish validation gate; reads destination from `emergence-config.json`. `skill-SKILL.md` scaffold template. `skill/` added to `branch.py`, `abort.py`, `archive.py`, `status.py` (new "Active Skills" display section). `start-flow.md` updated: new Publish destination step (skills only), skill column in scoping table, Building on AI? skips eval-status follow-up for skills. `SKILL.md` updated: branch hierarchy, Skills Operations section, Builder commands, CLI entries. 22 new tests (14 for validate_skill, 8 for skill_publish) plus skill/ regression assertions across 4 existing test files. 174 tests total.

## Version 0.6.0

- **Building on AI**: Start flow now asks "Is this project building on AI? (yes/no)" and, if yes, eval status (already have / will do). Choices are stored in `emergence-config.json`. Initiatives with "will do" evals: optional eval-spec authoring (template + LLMOps playbook) after PRD/UX/Tech; Approach asks eval placement (before build / in parallel) with parallel warning. Tweaks and bug fixes with "will do": optional eval/benchmark reminder in tweaklet/buglet. Cicadas does not run or host evals. New `emergence/eval-spec.md` instruction module and `templates/eval-spec.md`. SKILL.md, HOW-TO.md, CLAUDE.md, and canon updated.
- **parse_partitions_dag fallback**: When PyYAML is not installed, `utils.parse_partitions_dag()` uses a regex-based fallback to parse the `yaml partitions` block so tests and branch/worktree logic work in minimal environments.

## Version 0.5.6

- **Instruction module terminology**: Replaced all uses of "subagent" with "instruction module" throughout `SKILL.md`, `EMERGENCE.md`, and all `emergence/*.md` files. Emergence files are inline role-switches in the current context window — no separate agent process is spawned. The old term was misleading to integrators.
- **Prompt injection guardrails**: Added explicit untrusted-input warnings to `clarify.md` (before reading `requirements.md` / `loom.md`) and `bootstrap.md`. Added corresponding Guardrail #8 to `SKILL.md`.
- **Balanced elicitation inlined**: Deleted `emergence/balanced-elicitation.md` (28-line file); content inlined as a full appendix in `clarify.md`. References in `tech-design.md` and `ux.md` updated to point to the appendix.
- **Process banner consistency**: Added `FOLLOW THIS PROCESS EXACTLY. DO NOT SKIP STEPS UNLESS INSTRUCTED.` to all 7 emergence files (`clarify`, `ux`, `tech-design`, `approach`, `tasks`, `tweak`, `bug-fix`). Was previously present on only 2, implying the others were optional.
- **Mode selection decision rule**: `tasks.md` now states when to use Foundation Mode vs. Feature Mode — greenfield/standalone → Foundation; existing system → Feature.
- **Resuming Mid-Initiative**: New `## Resuming Mid-Initiative` section in `SKILL.md` guides context recovery when picking up an in-progress session.
- **Branch cleanup**: Added branch deletion steps to both "Complete an Initiative" (Step 4) and "Lightweight Paths" (Step 7) in `SKILL.md`.
- **Bug fixes**: Fixed `approach.md` asking for PR preference when `lifecycle.json` already exists (now skips); fixed `ux.md` Canon Check reading `product-overview.md` instead of `ux-overview.md`; fixed `bug-fix.md` and `tweak.md` using `{initiative}` instead of `{name}` in artifact paths.
- **Implementation rules**: `implementation.md` is now the single canonical source for implementation guardrails; `SKILL.md` contains a pointer only (eliminates drift risk).
- **Script failure recovery**: Added Guardrail #9 to `SKILL.md` with recovery guidance when a script fails mid-operation.

## Version 0.5.5

- **Standard start flow**: When starting an initiative, tweak, or bug, the agent now runs a single mandatory sequence first: name (confirm even if given) → create draft folder → requirements source and pace (initiatives only) → PR preference → then collect requirements or draft the spec. New `emergence/start-flow.md` is the source of truth; Clarify, Tweak, and Bug Fix subagents embed this flow. EMERGENCE.md, SKILL.md, and HOW-TO.md updated; README, src/cicadas/README, agents.md, and CLAUDE.md reference the flow.
- **Clarify intake options**: At the start of Clarify, the Builder can choose how to provide requirements: **Q&A** (interactive), **Doc** (place a requirements document at `.cicadas/drafts/{initiative}/requirements.md`), or **Loom** (record in Loom, then save the transcript to `.cicadas/drafts/{initiative}/loom.md`). The agent fills the PRD from the doc or transcript. `EMERGENCE.md` now includes a "Requirements intake (Clarify)" subsection for discoverability. New regression test `tests/test_emergence_clarify.py` asserts that `clarify.md` documents the Intake step and file paths.

## Version 0.5.4
- **Context Injection at Branch Start**: `branch.py` now writes `context.md` to the project root for sequential (non-worktree) branches, matching the existing behavior for parallel/worktree branches. Every registered branch now receives a canon summary + scoped module snapshots + `approach.md` + `tasks.md` at start. New `templates/canon-summary.md` template added. `synthesis-prompt.md` updated with Step 5 to produce `canon/summary.md` (300–500 token agent-optimized snapshot) as part of every canon synthesis run. `SKILL.md` synthesis step updated accordingly.

## Version 0.5.3
- **Code Review as Merge Gate**: Code review is now a persistent artifact, not an ephemeral console report. The Code Review subagent writes a structured `review.md` to `.cicadas/active/{initiative}/` with one of three verdicts: `PASS`, `PASS WITH NOTES`, or `BLOCK`. New `scripts/review.py` reads the verdict and returns exit codes (0=PASS/PASS WITH NOTES, 1=BLOCK, 2=not found). `open_pr.py` checks the verdict before opening a PR and refuses on `BLOCK`. Verdict strings updated throughout `emergence/code-review.md` (was `MERGE-READY`/`NEEDS-WORK`). New `templates/review.md` template. 13 new tests.

## Version 0.5.2
- **Token Usage Logging**: New `tokens.py` module (`init_log`, `append_entry`, `load_log`) adds an append-only `tokens.json` log to every initiative. Created at kickoff, moves with specs through active → archive. Scripts write null phase-boundary entries; agents self-append real counts when the runtime exposes them. `history.py` now renders a per-initiative token summary (input/output/cached by phase) in the HTML timeline. 25 new tests.
- **Emergence Pace Selection**: `clarify.md` step 0 now asks the Builder their preferred review cadence — `section` (pause after each section), `doc` (pause after each complete doc, default), or `all` (draft everything then present). Choice is stored in `emergence-config.json` in the drafts folder; every subsequent emergence agent (UX, Tech Design, Approach, Tasks) reads it and enforces the stop rule.
- **PR Boundary Reminder**: `clarify.md` Process Preview now explicitly notes that Approach will ask about PR boundaries and create `lifecycle.json`, preventing agents from skipping that step.
- **Implementation guardrails**: Require Reflect and task updates before every commit on feat/task branches; require Code Review before committing on feature branches. `implementation.md` and `SKILL.md` updated; new "Implementation agent rules (all environments)" section in SKILL so Cursor and other non–Claude Code envs get the same guardrails from the skill file alone.
- **Install & docs**: Cursor integration now copies `SKILL.md` (was `skill.md`). README, HOW-TO, and CLAUDE.md clarify that `CLAUDE.md` is Claude Code–only and other envs use the skill for guardrails.
- **Installer**: Added `rovodev` agent integration — `bash install.sh --agent rovodev` creates `.rovodev/skills/cicadas` symlink to the install dir. Documented in README.md, HOW-TO.md, and src/cicadas/README.md.

## Version 0.5.1
- **Code Review**: New optional agent operation (`emergence/code-review.md`) for spec-anchored evaluation of code diffs. Covers task completeness, acceptance criteria, architectural conformance, module scope, Reflect completeness, security (OWASP patterns), correctness (9 named bug patterns with explicit blocking thresholds), and code quality. Produces an ephemeral advisory report with tiered findings (Blocking / Advisory) and a `MERGE-READY` / `NEEDS-WORK` verdict. Supports feature branches (Full mode) and fix/tweak branches (Lightweight mode).
- **SKILL.md**: Added Code Review to Agent Operations, Agent Autonomy Boundaries table, Builder Commands (`"Code review"`, `"Review feature"`, `"Review fix"`, `"Review tweak"`), and quick reference table.
- **Lint fixes**: Resolved pre-existing `ruff` errors in `history.py` (`timezone.utc` → `UTC`, two long CSS lines) and `tests/test_init.py` (unused import).

## Version 0.5.0
- **Lifecycle & PRs**: Per-initiative `lifecycle.json` (in drafts/active) defines PR boundaries (specs, initiatives, features, tasks) and an ordered step list. Created during Approach via `create_lifecycle.py`; promoted at kickoff and archived with the initiative.
- **Status merge detection**: When `lifecycle.json` exists, `status.py` reports which branches are merged (git-based) and suggests the next lifecycle step (Merged/Next).
- **open_pr.py**: New script to open a PR from the current branch (tries `gh` → `glab` → Bitbucket URL → fallback). Host-agnostic; no API keys.
- **SKILL/HOW-TO/CLAUDE**: Updated Complete feature/initiative for PR-at-boundary wording, lifecycle step 5b, and create_lifecycle/open_pr in CLI references.
- **Requirement change**: Cicadas now requires **Python 3.11+** (was 3.13+). The scripts use stdlib only (e.g. `datetime.UTC`); the installer and docs have been updated accordingly.

## Version 0.4.0
- **New Feature**: Added `install.sh` — a single-command bash installer that checks for Python 3.12+, downloads Cicadas from the GitHub archive URL, extracts to `src/cicadas/` (configurable via `--dir`), and calls `init.py` to bootstrap `.cicadas/`.
- **Agent Integrations**: `--agent` flag supports `claude-code` (symlink at `.claude/skills/cicadas`), `antigravity` (symlink at `.agents/skills/cicadas`), and `cursor` (copies `SKILL.md` to `.cursor/rules/cicadas.mdc`). Interactive agent prompt when stdin is a tty; skipped gracefully in `curl | bash` context.
- **Update Workflow**: `--update` flag re-downloads and overwrites skill files without touching `.cicadas/` state or re-running init.
- **Docs**: `README.md` and `HOW-TO.md` updated with one-liner install, agent integration table, and update workflow.
- **Tests**: Added 2 tests to `test_init.py` covering hook installation loop and `__main__` entry point; `init.py` coverage 74% → 97%. Overall test coverage 83% → 84% (54 tests).
- **Canon**: Updated `product-overview.md` and `tech-overview.md` with installer feature, distribution architecture, and agent integration conventions.

## Version 0.3.5
- **Bug Fix**: Fixed `archive.py` leaving orphaned branch entries in `registry.json` after archiving an initiative; associated branches (matching `initiative` field) are now deregistered automatically.
- **Tests**: Added regression test `test_archive_initiative_deregisters_associated_branches` in `test_archive_status.py`.

## Version 0.3.4
- **New Script**: Added `src/cicadas/scripts/abort.py` — context-aware escape hatch that detects the current branch type (`tweak/`, `fix/`, `feat/`, `initiative/`) and rolls back the appropriate scope, prompting whether to move promoted active specs back to drafts or delete them entirely.
- **Skill Update**: Added `"Abort"` builder command and `abort.py` entry to the CLI Quick Reference in `SKILL.md`.
- **Docs**: Updated `README.md`, `HOW-TO.md`, `src/cicadas/README.md`, and `CLAUDE.md` to document the new command.
- **Tests**: Added `tests/test_abort.py` with 14 tests at 86% coverage.
- **Dev Dependencies**: Added `pytest` and `pytest-cov` to `pyproject.toml`.

## Version 0.3.3
- **Bug Fix**: Fixed `branch.py` creating orphaned nested active directories (e.g. `active/tweak/X`) for lightweight fix/tweak branches; active dirs now consistently use the initiative name (`active/{name}/`).
- **Test Infrastructure**: Added `tests/conftest.py` to ensure scripts dir is in `sys.path` before test collection, fixing test isolation failure.
- **Tests**: Added two regression tests for the active dir convention in `test_branch.py`.

## Version 0.3.2
- **New Script**: Added `src/cicadas/scripts/history.py` — generates a self-contained HTML timeline (`.cicadas/canon/history.html`) from archived specs and the index ledger.
- **Skill Update**: Added `"Project history"` / `"Generate history"` builder command and `history.py` entry to the CLI quick reference in `SKILL.md`.

## Version 0.3.1
- **Claude Code Integration**: Added `CLAUDE.md` with build/test/lint commands and codebase architecture overview.
- **Skill Registration**: Created `.claude/skills/` directory with a symlink to `src/cicadas/`, registering Cicadas as a native Claude Code skill.
- **SKILL.md Compliance**: Renamed `skill.md` to `SKILL.md` per Anthropic convention; fixed missing opening `---` frontmatter fence.
- **SKILL.md Improvements**: Added `allowed-tools`, `argument-hint`, and trigger-keyword-style `description` for reliable auto-invocation.
- **SKILL.md Bug Fixes**: Corrected duplicate `emergence/` directory tree (scripts were misplaced), removed orphaned Bootstrap/Synthesis block, and added `{cicadas-dir}` definition note.

## Version 0.3.0
- **Lightweight Paths (Bugs & Tweaks)**: Introduced streamlined workflows for simple bug fixes and small tweaks: `fix/` and `tweak/` branches (fork from main), minimal specs (`buglet.md`, `tweaklet.md`), and emergence subagents (Bug-fix, Tweak). Scripts updated to support relaxed validation, direct-from-main branching, and status/history for fix/tweak.
- **Test Coverage**: Achieved >75% code coverage (83% overall) for all core scripts.
- **Mock-Free Testing**: Refactored the test suite to use real file system operations and Git scaffolding instead of mocks.
- **Linting & Formatting**: Integrated `ruff` and `pre-commit` hooks for automated code quality checks.
- **Refactoring**: Renamed `signal.py` to `signalboard.py` to resolve Python standard library collisions.
- **Reliability**: Fixed internal bugs in `update_index.py` and improved JSON serialization for `Path` objects.

## Version 0.2.1
- Renamed the core skill directory from `scripts/chorus/` to `src/cicadas/`.
- Created an Antigravity skill symlink in `.agents/skills/cicadas` pointing to the new `src/cicadas/` location.
- Updated documentation (`README.md`) to reflect the new paths and branding changes from Chorus to Cicadas.
- Updated all skill files to use relative paths within the skill.
- Created a comprehensive README instruction file
