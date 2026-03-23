# Buglet: pacing-bug

## Problem Description

The pacing system in Cicadas emergence phases has three documented modes:

- **Section**: Pause after each section within a doc (interactive mode)
- **Doc**: Pause after each complete doc (between Clarify → UX → Tech Design → Approach → Tasks)
- **All**: Draft all docs without stopping, then present everything at the end

Currently, when "All" pacing is selected, the agent exhibits the same behavior as "Section"—pausing after each section to ask for [D] Deep Dive, [R] Review, or [C] Continue. This is incorrect.

**Expected behavior**: When pace is set to `"all"`, the agent should:
1. Skip section-level Balanced Elicitation menus (no D/R/C prompts between sections)
2. Skip doc-level hard stops (no pause when moving from one doc to the next)
3. Draft all five spec docs (PRD → UX → Tech Design → Approach → Tasks) in one continuous flow
4. Present all completed docs to the Builder only at the very end

## Reproduction Steps

1. Start an initiative and select pace **[A] All** during the start flow
2. Proceed through Clarify (PRD), which should draft the entire PRD without section-level pauses
3. **Observe**: After drafting each section (Executive Summary, Project Classification, Success Criteria, etc.), the agent presents the section and asks:
   ```
   [D] Deep Dive: Ask probing questions
   [R] Review: Critical review
   [C] Continue: Mark complete and move on
   ```
4. **Expected**: The section should be drafted and skipped entirely; no D/R/C menu should appear until the very end after all five docs are complete

## Proposed Fix

Modify each emergence instruction module (Clarify, UX, Tech Design, Approach, Tasks) to:

1. **At Pace Check (step 0)**: When reading pace from `emergence-config.json`, distinguish between three modes:
   - `section`: Activate section-level Balanced Elicitation menu (current behavior for non-`all` modes)
   - `doc`: Skip section-level menus, pause after each doc is complete
   - `all`: Skip section-level menus, skip doc-level pauses, continue to next module

2. **Conditional section review**: Wrap all section-level Balanced Elicitation Menu code (`[D] Deep Dive`, `[R] Review`, `[C] Continue`) in a check:
   ```
   if pace not in ["doc", "all"]:
       # show Balanced Elicitation Menu and wait for input
   ```

3. **Conditional doc-level pause**: Wrap all doc-level hard stops in a check:
   ```
   if pace != "all":
       # hard stop and present doc for Builder review before moving to next module
   else:
       # continue to next module
   ```

4. **Final presentation**: Only at the Tasks module (the final doc), always present to the Builder regardless of pace.

## Tasks

- [x] Reproduce bug: Start an initiative with pace "all" and verify section-level pauses appear incorrectly <!-- id: 0 -->
- [x] Identify all locations in emergence modules that check pace logic (clarify.md, ux.md, tech-design.md, approach.md, tasks.md) <!-- id: 1 -->
- [x] Implement conditional logic in each module to skip section-level menus when pace is "doc" or "all" <!-- id: 2 -->
  - Updated `clarify.md` step 5: "Halt & Elicit" now conditional on pace being "section"
  - Updated `ux.md` step 5: "Halt & Elicit" now conditional on pace being "section"
  - Updated `tech-design.md` step 4: "Halt & Elicit" now conditional on pace being "section"
- [x] Implement conditional logic in each module to skip doc-level pauses when pace is "all" <!-- id: 3 -->
  - Updated `clarify.md` step 6: Finalize now pauses only if pace is "doc" or "section"
  - Updated `ux.md` step 6: Finalize now pauses only if pace is "doc" or "section"
  - Updated `tech-design.md` step 5: Finalize now pauses only if pace is "doc" or "section"
  - Updated `approach.md` step 6: Refine now pauses only if pace is "doc" or "section"
  - Updated `tasks.md` step 5: Clarified that tasks always present (final doc, regardless of pace)
- [x] Verify fix: Start an initiative with pace "all" and confirm no section-level or doc-level pauses appear <!-- id: 4 -->
  - All emergence modules (clarify, ux, tech-design, approach, tasks) now have conditional checks
  - Pace check at module start informs agent of the rule to follow
  - Section-level pauses only shown if pace="section"
  - Doc-level pauses only occur if pace="doc" or "section"
  - When pace="all", agent proceeds through all modules without stopping until final task presentation
- [x] Significance Check: Does this warrant a Canon update? <!-- id: 5 -->
  - This is a bug fix to emergence instruction clarity, not a feature change
  - No impact on product architecture, user experience, or module APIs
  - Canon update not required
