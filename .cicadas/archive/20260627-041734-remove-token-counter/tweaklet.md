---
summary: "Remove non-functional token counter: delete tokens.py and all call sites across scripts, CLI, history renderer, and tests"
phase: "tweak"
modules:
  - "src/cicadas/scripts/tokens.py"
  - "src/cicadas/scripts/kickoff.py"
  - "src/cicadas/scripts/branch.py"
  - "src/cicadas/scripts/command_registry.py"
  - "src/cicadas/scripts/history.py"
  - "tests/test_tokens.py"
  - "tests/test_cli.py"
  - "tests/test_kickoff.py"
  - "tests/test_history.py"
---

## Intent

Remove the token counter system entirely. It was designed to log token usage per initiative/phase into `tokens.json` files, but no agent environment currently populates it with real data — calls are written with `source="unavailable"` at kickoff and branch time, and no tooling reads the counts back in a meaningful way. The feature creates dead code and test surface with no working end-to-end value.

## Scope Check

- **< 100 LOC net change**: Yes — ~120 LOC deleted, 0 added (net negative).
- **No new dependencies**: Yes.
- **No architectural impact**: Yes — token logging was a side effect; removing it does not change any observable workflow.
- **Escalation criteria**: None triggered.

## Tasks

- [x] Delete `src/cicadas/scripts/tokens.py`
- [x] `kickoff.py`: remove `from tokens import append_entry` import; remove `append_entry(...)` call at lifecycle/kickoff boundary
- [x] `branch.py`: remove `from tokens import append_entry` import; remove `append_entry(...)` call at implementation/branch-start boundary
- [x] `command_registry.py`: remove `from tokens import VALID_SOURCES, append_entry, init_log, load_log`; delete `TOKENS_USAGE` constant, `_tokens_parser()`, `_handle_tokens()` functions; remove `tokens` subcommand from `get_commands()` and `build_arg_parser()`
- [x] `history.py`: remove `from tokens import load_log`; delete `load_token_summary()` function; remove `token_summary` field from `_load_archive_entry()`; remove `token_block` rendering from `_render_entry()`; remove `.tokens` and `.token-table` CSS rules
- [x] Delete `tests/test_tokens.py`
- [x] `tests/test_cli.py`: remove any test cases or assertions covering the `tokens` subcommand
- [x] `tests/test_kickoff.py`: remove assertions that check `tokens.json` was created during kickoff
- [x] `tests/test_history.py`: remove `load_token_summary` import and any test cases or assertions covering token rendering in history HTML
- [x] Run tests: `PYTHONPATH=src/cicadas/scripts:tests python3 -m unittest discover -s tests/` — all pass
- [x] Grep gate: `grep -r "tokens\.py\|append_entry\|init_log\|load_log\|token_summary\|VALID_SOURCES\|tokens_command" src/ tests/` — no matches
