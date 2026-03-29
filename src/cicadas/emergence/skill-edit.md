
# Instruction Module: Skill Edit

## Role

You are the **Skill Edit instruction module**. Your goal is to make a targeted, minimum-change edit to an existing skill based on the Builder's feedback, then validate the result.

## Triggers

This module is invoked when the Builder says any of:
- "edit skill {name}"
- "update skill {name}"
- "fix skill {name}"
- "the skill isn't triggering" / "the skill keeps firing" / "the skill output is wrong"

## Process

FOLLOW THIS PROCESS EXACTLY. DO NOT SKIP STEPS UNLESS INSTRUCTED.

1.  **Resolve skill path**

    Determine which skill directory to edit (in order of preference):
    - If on branch `skill/{slug}`: use `.cicadas/active/skill-{slug}/`
    - If not yet kicked off: use `.cicadas/drafts/skill-{slug}/`
    - If the Builder names the skill explicitly, use that name to resolve

    Read `SKILL.md` from the resolved path before asking any questions.

2.  **One diagnostic question**

    Ask exactly one question to diagnose the problem. Choose the framing that matches the Builder's trigger phrase:

    > *"What's the issue?*
    > *  A. It's not firing when it should (under-triggering)*
    > *  B. It fires when it shouldn't (over-triggering)*
    > *  C. It fires at the right time but the output is wrong"*

    Do not ask multiple questions. Do not ask for examples at this stage — the diagnosis alone is enough to proceed.

3.  **Propose minimum change**

    Based on the diagnosis:

    | Diagnosis | Typical minimum change |
    |-----------|----------------------|
    | **Under-triggering** | Broaden `description`: add missing trigger contexts, remove overly specific constraints |
    | **Over-triggering** | Narrow `description`: add explicit exclusions, tighten trigger conditions |
    | **Wrong output** | Edit `## Instructions` body: fix the step(s) producing incorrect output |

    Present the proposed change as a **before / after diff** with a one-sentence rationale:

    ```
    Before:
      description: Use when the user asks to process CSV files.

    After:
      description: Use when the user asks to process, parse, or transform tabular data,
        including CSV, TSV, or spreadsheet imports. Do not trigger for generic data
        analysis questions that don't involve file ingestion.

    Rationale: Added TSV/spreadsheet coverage (under-triggering) and excluded generic
    analysis queries (over-triggering guard).
    ```

    If the fix requires editing bundled files (`scripts/`, `references/`), show those diffs too.

    Ask: *"Does this look right? I'll apply it once you confirm."*

4.  **Apply on approval**

    On Builder approval:

    a. Edit the file(s) in the resolved skill directory.

    b. Run validation:
       ```
       python {cicadas-dir}/scripts/cicadas.py validate-skill {slug}
       ```
       If validation fails, fix autonomously if unambiguous (e.g., description now too long after expansion — trim to 1024 chars), re-validate, and report. If the violation requires a content decision, surface it before writing.

    c. Report outcome:
       ```
       ✓ skill/{slug} updated and valid.
       Changed: {list of files changed}
       ```

    d. If `eval_queries.json` exists in the skill directory, offer:
       *"I can update the eval queries to cover the new trigger condition. Want me to add entries? (yes / no)"*

## Artifacts

- **Modified**: `.cicadas/active/skill-{slug}/SKILL.md` and/or bundled files
- **Validated**: `python {cicadas-dir}/scripts/cicadas.py validate-skill ...` exits 0 after edit

## Escalation

If the Builder's feedback reveals the skill needs a fundamentally different purpose or scope (e.g., "actually this should handle three separate use cases"), suggest starting a new skill with `skill-create.md` or restructuring the current one from scratch via the creation flow.

---
_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
