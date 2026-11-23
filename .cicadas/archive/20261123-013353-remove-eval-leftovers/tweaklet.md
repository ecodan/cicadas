
# Tweaklet: remove-eval-leftovers

## Intent
Finish removing the "LLMs and Evals / Building on AI" concept from Cicadas. The prompts, `eval-spec` files and skill logic were removed in v1.0.0 (`remove-evals-and-cross-initiative`), but stale references remained in docs, a test fixture and a bundled skill config. Make the repo consistent with the shipped behavior: the start flow has no AI/eval question.

## Proposed Change (as implemented)
- `src/cicadas/README.md`: removed the eval-spec / eval placement / benchmark-reminder sentences from the `emergence/` bullet, the `eval-spec.md` mention from the `templates/` bullet, and the "LLMs and Evals?" step plus closing eval sentence from the start-flow paragraph.
- `docs/cicadas-user-manual.md`: removed the "Building on AI?" step and the eval spec / reminder sentence from the start-flow paragraph.
- `tests/test_skill_publish.py`: dropped `building_on_ai` from the fixture config.
- `.claude/skills/test-coverage-review/emergence-config.json`: **diverged from plan.** Kept the file, since `publish_dir` is live config used by `skill-publish`. Removed only the `building_on_ai` key.
- `release-notes.md`: added a line under v1.0.0 Removals about the cleanup and a note that stale installs need `install.sh --update`.

**Out of scope**
- `.cicadas/canon/` (cannot be edited on a branch), `.cicadas/archive/**`, and the other active initiative's config.
- `graph eval` and the `notes_for_evaluator` / Step 4b Chorus evaluator material are unrelated to AI evals.
- Stale vendored copies of Cicadas in other projects, which still prompt for this. They need `install.sh --update` in each project, not a change here.

## Tasks
- [x] Implement tweak <!-- id: 10 -->
- [x] Verify functionality: grep for `eval-spec|Building on AI|LLMs and Evals|building_on_ai` outside canon/archive/active/release-notes is clean (only the registry intent text and local settings match); full suite 398 passed, 1 skipped <!-- id: 11 -->
- [x] Significance Check: Does this warrant a Canon update? Yes. `canon/summary.md`, `product-overview.md` and `tech-overview.md` still describe Building on AI and eval-spec. Canon can't be written on a branch, so refresh it on `master` after merge. <!-- id: 12 -->
