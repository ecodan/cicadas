---
summary: "Build the profile-aware emergence guidance in `feat/initiative-profile-guidance`: add Technical Brief and Operator Experience templates, update start-flow and downstream modules, add tests, then open an initiative PR to master."
phase: "tasks"
when_to_load:
  - "When selecting the next task for the initiative-profile implementation."
  - "When checking completion state before Reflect, review, commit, or PR handoff."
depends_on:
  - "prd.md"
  - "ux.md"
  - "tech-design.md"
  - "approach.md"
modules:
  - "src/cicadas/emergence"
  - "src/cicadas/templates"
  - "tests/test_templates.py"
index:
  initiative_profile_guidance: "## Partition: feat/initiative-profile-guidance"
  initiative_boundary: "## Initiative Boundary"
next_section: "## Partition: feat/initiative-profile-guidance"
---

# Tasks: Technical Initiative Profiles

## Partition: feat/initiative-profile-guidance

- [x] Add `technical-brief.md` template with required technical initiative sections and context front matter <!-- id: 1 -->
- [x] Add `operator-experience.md` template for CLI/log/error/docs/agent-facing experience decisions with context front matter <!-- id: 2 -->
- [x] Update `start-flow.md` to collect and store `initiative_profile` for full initiatives after name and before requirements source <!-- id: 3 -->
- [x] Update `clarify.md` so product uses PRD, technical uses Technical Brief, and mixed selects the appropriate clarify artifact <!-- id: 4 -->
- [x] Update `ux.md` so product uses full UX, technical can write Operator Experience or explicitly skip UX, and mixed chooses per surface <!-- id: 5 -->
- [x] Update `tech-design.md`, `approach.md`, and `tasks.md` to ingest profile-appropriate source artifacts while keeping Tech Design, Approach, and Tasks mandatory <!-- id: 6 -->
- [x] Extend `tests/test_templates.py` for new template front matter and profile guidance regressions <!-- id: 7 -->
- [x] Run targeted tests and fix any regressions <!-- id: 8 -->
- [x] Reflect completed implementation in active tasks before commit <!-- id: 9 -->

## Initiative Boundary

- [ ] Open PR: initiative/technical-initiative-profiles -> master and await merge approval before continuing <!-- id: 100 -->
