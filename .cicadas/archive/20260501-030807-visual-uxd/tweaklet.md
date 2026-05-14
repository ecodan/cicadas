# Tweaklet: visual-uxd

## Intent
Make Cicadas generate HTML/CSS mock-ups as part of UXD drafting when an initiative has meaningful visual UI surfaces, so builders get a concrete, editable design artifact instead of prose alone.

## Proposed Change
- Update the UX emergence instructions in `src/cicadas/emergence/ux.md` to distinguish visual UI work from CLI/operator-only work and require at least one HTML/CSS mock-up artifact for screen-based flows.
- Extend `src/cicadas/templates/ux.md` so the UXD format has an explicit place for HTML/CSS mock-up references, along with optional screenshot previews and optional generated imagery used only for illustrative content.
- Document the new expectation in `src/cicadas/README.md` and add a lightweight regression check in `tests/test_templates.py` so the UX workflow and template both keep the HTML/CSS mock-up requirement visible.
- Keep the scope tweak-sized by treating this as instruction/template behavior only; do not add new Cicadas CLI commands or a general-purpose rendering pipeline in this change.

## Implementation Notes
- Implemented in `src/cicadas/emergence/ux.md`, `src/cicadas/templates/ux.md`, `src/cicadas/README.md`, `README.md`, and `tests/test_templates.py`.
- The UX instructions now require a real HTML/CSS mock-up file under `.cicadas/drafts/{initiative}/mockups/` before UXD approval for visual UI work.
- This tweak intentionally does not add a renderer or CLI command; it changes the authoring contract so future UXD flows produce editable mock-up artifacts.

## Tasks
- [x] Update UX emergence instructions to require HTML/CSS mock-ups for visual UI flows and preserve the current operator-experience path for non-visual work. <!-- id: 10 -->
- [x] Add a mock-up section to the UX template and document how builders/agents should reference the HTML/CSS artifact plus optional previews. <!-- id: 11 -->
- [x] Update docs and regression coverage for the new UXD HTML/CSS mock-up expectation. <!-- id: 12 -->
- [x] Verify functionality (`uv run pytest tests/test_templates.py`). <!-- id: 13 -->
- [x] Significance Check: No separate canon synthesis required for this tweak; the source UX instructions/templates and repo docs were updated directly. <!-- id: 14 -->
