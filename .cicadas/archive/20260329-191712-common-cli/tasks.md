# Tasks: common-cli

## Mode B: Feature (Vertical Slices)

### Feature: CLI Foundation (`feat/cli-foundation`)
- [x] Create `src/cicadas/scripts/cicadas.py` as the common repo-local CLI entrypoint with top-level `argparse` parsing and subcommand dispatch. <!-- id: 100 -->
- [x] Create `src/cicadas/scripts/command_registry.py` to centralize subcommand metadata, parser registration, and one-line help text. <!-- id: 101 -->
- [x] Wire an initial representative subcommand set in the common CLI, covering at least `status`, `check`, and `kickoff`. <!-- id: 102 -->
- [x] Add `tests/test_cli.py` covering top-level help, unknown subcommand handling, and representative dispatch behavior. <!-- id: 103 -->
- [x] Verify `python src/cicadas/scripts/cicadas.py --help` and `python src/cicadas/scripts/cicadas.py status` succeed in a real repo context. <!-- id: 104 -->

### Feature: Command Coverage and Parity (`feat/cli-command-coverage`)
- [x] Audit existing files in `src/cicadas/scripts/` and identify which ones should be exposed as public CLI subcommands in MVP. <!-- id: 200 -->
- [x] Refactor script entrypoints that still require inline parsing so they can be called cleanly from `cicadas.py` without changing lifecycle semantics. <!-- id: 201 -->
- [x] Register the full deterministic command surface in the common CLI, including lifecycle, skill, event, and maintenance-oriented commands that remain public. <!-- id: 202 -->
- [x] Add parity-focused tests for representative CLI-dispatched commands, including `status`, `check`, and at least one mutating command in a temp repo fixture. <!-- id: 203 -->
- [x] Verify subcommand-specific help output for representative advanced commands such as `create-lifecycle`, `validate-skill`, and `get-events`. <!-- id: 204 -->

### Feature: Documentation and Skill Migration (`feat/cli-doc-migration`)
- [x] Audit `README.md`, `src/cicadas/README.md`, `src/cicadas/SKILL.md`, and `src/cicadas/emergence/*.md` for public examples that invoke scripts directly. <!-- id: 300 -->
- [x] Update core user-facing lifecycle examples to use `python {cicadas-dir}/scripts/cicadas.py ...` as the canonical interface. <!-- id: 301 -->
- [x] Update skill and emergence instructions to teach the common CLI while preserving lifecycle semantics, PR rules, and autonomy boundaries. <!-- id: 302 -->
- [x] Review the updated docs for mixed old/new command surfaces and resolve any remaining drift or intentional exceptions. <!-- id: 303 -->
- [x] Validate by searching the agreed user-facing docs for direct script invocations and confirming only intentional exceptions remain. <!-- id: 304 -->

### Initiative Completion
- [x] Run a final consistency pass across implementation, tests, and docs to confirm the common CLI is now the taught public interface. <!-- id: 400 -->
- [x] Reflect the active specs to match final implementation details before opening the initiative PR. <!-- id: 401 -->
- [ ] Open PR: initiative/common-cli → master and await merge approval before continuing <!-- id: PR-initiative -->
