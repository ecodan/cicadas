---
summary: "Two fully independent partitions: feat/remove-evals deletes the two eval-spec files and surgically removes all evals/LLMs content from emergence markdown and SKILL.md (9 file edits + grep gate); feat/registry-root-docs-version removes get_registry_root() from utils.py, fixes emit_event.py, trims test_utils.py, updates agents.md + docs + README, bumps version to 1.0.0, and adds a release note (10 file edits + test run + grep gate). Both merge to the initiative branch, then a single PR to master."
phase: "tasks"
when_to_load:
  - "When selecting the next implementation task or reviewing completion state."
  - "When checking partition progress or grep-gate acceptance criteria."
depends_on:
  - "technical-brief.md"
  - "tech-design.md"
  - "approach.md"
modules:
  - "src/cicadas/emergence/"
  - "src/cicadas/templates/eval-spec.md"
  - "src/cicadas/SKILL.md"
  - "src/cicadas/scripts/utils.py"
  - "src/cicadas/scripts/emit_event.py"
  - "tests/test_utils.py"
  - "README.md"
  - "agents.md"
  - "docs/"
  - "pyproject.toml"
  - "release-notes.md"
index:
  partition_remove_evals: "## Partition: feat/remove-evals"
  partition_registry_docs: "## Partition: feat/registry-root-docs-version"
  initiative_boundary: "## Initiative Boundary"
next_section: "## Partition: feat/remove-evals"
---

# Tasks: remove-evals-and-cross-initiative

## Partition: feat/remove-evals

- [ ] Delete `src/cicadas/emergence/eval-spec.md` <!-- id: 1 -->
  - Done: file does not exist

- [ ] Delete `src/cicadas/templates/eval-spec.md` <!-- id: 2 -->
  - Done: file does not exist

- [ ] Edit `src/cicadas/emergence/start-flow.md`: remove the entire step 3 body ("LLMs and Evals?"); renumber old steps 4–7 to 3–6; update the "Mandatory sequence" narrative and any cross-references that say "step 4/5/6/7" to the new numbers; remove the "LLMs and Evals?" row from the scoping table; remove any eval-specific description paragraph <!-- id: 3 -->
  - Done: no occurrence of `LLMs and Evals`, `eval_status`, `building_on_ai` in the file; step numbering runs 1–6 with no gap

- [ ] Edit `src/cicadas/emergence/clarify.md`: remove "LLMs and Evals?" from the step 0 start-flow summary name list (the inline list of steps the Builder runs) <!-- id: 4 -->
  - Done: no occurrence of `LLMs and Evals` or `building_on_ai` in the file

- [ ] Edit `src/cicadas/emergence/tweak.md`: remove step 0d (the LLMs-and-Evals question sub-step) and remove the "LLM and Eval reminder" block <!-- id: 5 -->
  - Done: no occurrence of `LLMs and Evals`, `eval_status`, `building_on_ai` in the file

- [ ] Edit `src/cicadas/emergence/bug-fix.md`: remove step 0d (the LLMs-and-Evals question sub-step) and remove the "LLM and Eval reminder" block <!-- id: 6 -->
  - Done: no occurrence of `LLMs and Evals`, `eval_status`, `building_on_ai` in the file

- [ ] Edit `src/cicadas/emergence/approach.md`: remove step 3 (eval-spec offer, eval placement question, and `eval_placement` write to emergence-config.json) <!-- id: 7 -->
  - Done: no occurrence of `eval_status`, `eval_placement`, `eval-spec`, `building_on_ai` in the file

- [ ] Edit `src/cicadas/SKILL.md`: (a) remove the "LLMs and Evals" sub-section under Emergence; (b) update the Emergence process table — remove the "LLMs and Evals" step row and the "LLMs and Evals" column in the scoping table; (c) remove the paragraph in the Emergence section that describes the evals question chain and `eval_status`/`building_on_ai` writes; (d) remove any documentation of `get_registry_root()`, primary-worktree routing, or worktree-aware registry root from the Architecture/Utilities/Notes sections <!-- id: 8 -->
  - Done: no occurrence of `LLMs and Evals`, `eval_status`, `building_on_ai`, `eval-spec`, or `get_registry_root` in SKILL.md

- [ ] Run grep gate across all of `src/cicadas/`: `grep -rn "eval_status\|building_on_ai\|eval.spec\|eval-spec\|get_registry_root" src/cicadas/` → must return zero results <!-- id: 9 -->
  - Done: command exits with no output

---

## Partition: feat/registry-root-docs-version

- [ ] Edit `src/cicadas/scripts/utils.py`: delete the entire `get_registry_root()` function (currently lines 22–49); change the body of `get_registry_dir()` to the one-liner `return get_project_root() / ".cicadas"` and remove its docstring referencing primary-worktree routing <!-- id: 10 -->
  - Done: `grep -n "get_registry_root" src/cicadas/scripts/utils.py` returns zero results; `get_registry_dir()` body is a single `return` line

- [ ] Edit `src/cicadas/scripts/emit_event.py`: (a) change `from utils import get_registry_root, load_config` → `from utils import get_registry_dir, load_config`; (b) change the `events_path` construction from `get_registry_root() / ".cicadas" / "active" / initiative / "events.jsonl"` → `get_registry_dir() / "active" / initiative / "events.jsonl"` <!-- id: 11 -->
  - Done: `grep "get_registry_root" src/cicadas/scripts/emit_event.py` returns zero results; `get_registry_dir` appears in the import line

- [ ] Edit `tests/test_utils.py`: rename class `TestGetRegistryRoot` → `TestGetRegistryDir`; delete `test_primary_worktree_returns_self` and `test_linked_worktree_returns_primary`; keep `test_get_registry_dir_returns_cicadas_subdir` (no edits to the kept test body) <!-- id: 12 -->
  - Done: `grep "get_registry_root\|TestGetRegistryRoot\|test_primary_worktree\|test_linked_worktree" tests/test_utils.py` returns zero results; `TestGetRegistryDir` class exists with one test

- [ ] Run full test suite and confirm all tests pass: `PYTHONPATH=src/cicadas/scripts:tests python3 -m unittest discover -s tests/` <!-- id: 13 -->
  - Done: output shows no failures or errors; exit code 0

- [ ] Edit `agents.md`: remove "Building on AI — gate and eval status in start flow, optional eval spec for initiatives, eval/benchmark reminder for tweaks/bugs" from the `src/cicadas/` description bullet <!-- id: 14 -->
  - Done: `grep -n "Building on AI\|eval_status\|building_on_ai" agents.md` returns zero results

- [ ] Edit `docs/cicadas-method-general.md`: (a) remove `Building on AI? and eval status` from the `emergence-config.json` field comment (~line 116); (b) remove the sentence starting "The standard start flow also records Building on AI?" (~line 162); (c) remove the gap table row `X1` ("Signals are intra-initiative only: No formal mechanism for cross-initiative notifications") (~line 502); (d) remove the cross-initiative future-vision paragraph (~line 533) <!-- id: 15 -->
  - Done: `grep -n "Building on AI\|eval_status\|building_on_ai\|cross-initiative\|get_registry_root" docs/cicadas-method-general.md` returns zero results (or only results unrelated to the removed features)

- [ ] Edit `README.md`: grep for evals and cross-initiative registry mentions (`grep -n "eval_status\|building_on_ai\|eval.spec\|get_registry_root\|cross-initiative registry\|LLMs and Evals" README.md`) and remove any found <!-- id: 16 -->
  - Done: the grep above returns zero results

- [ ] Edit `pyproject.toml`: change `version = "0.3.1"` → `version = "1.0.0"` <!-- id: 17 -->
  - Done: `grep "^version" pyproject.toml` returns `version = "1.0.0"`

- [ ] Edit `release-notes.md`: prepend a `## v1.0.0` section documenting: (1) removal of the LLMs-and-evals question chain from all start flows and emergence modules, deletion of eval-spec files; (2) removal of `get_registry_root()` cross-worktree routing from `utils.py` and `emit_event.py`; (3) doc cleanup across SKILL.md, README.md, agents.md, docs/ <!-- id: 18 -->
  - Done: `release-notes.md` starts with `## v1.0.0`

- [ ] Run final grep gate: `grep -rn "get_registry_root" src/ tests/` → must return zero results <!-- id: 19 -->
  - Done: command exits with no output

---

## Initiative Boundary

- [ ] Open PR: initiative/remove-evals-and-cross-initiative → master and await merge approval before continuing <!-- id: PR-initiative -->
