# Standard Start Flow

**All** entry points (initiative, tweak, bug, skill) MUST run this flow before collecting requirements or drafting specs. No matter how the user phrases the request, execute these steps in order. If the user provides information up front (e.g. "Start a tweak called XYZ"), pre-populate the answers but **still run the flow and verify** (e.g. "What is the name? 1. XYZ, 2. Other (enter the name)").

## Mandatory sequence

1. **Name** — Get the initiative / tweak / bug / skill name. Confirm even when the user already said it (offer "1. {their name}, 2. Other").
2. **Create draft folder** — Ensure `.cicadas/drafts/{name}/` exists and create any initial files (e.g. `emergence-config.json` for initiatives, or lifecycle when PR preference is set).
3. **LLMs and Evals?** — Ask: *"Will this feature or change be powered by LLMs and may require ML evals to ensure quality? (yes / no)"*. If the user says **no**, write `building_on_ai: false` to `.cicadas/drafts/{name}/emergence-config.json` (merge with existing keys, e.g. `pace`), then continue to step 4 (initiatives) or step 6/7 (tweaks/bugs/skills). If the user says **yes**, write `building_on_ai: true`, then — **for initiatives, tweaks, and bugs only** — ask: *"This change involves LLMs. Experimentation and evals may be required. Does this project already have completed evals, or will you be doing evals? (already have / will do)"*. Write `eval_status: "already_have"` or `eval_status: "will_do"` to `emergence-config.json` (merge with existing keys), then continue. **For skills**, skip the eval-status follow-up (skill evals are Post-MVP); write only `building_on_ai: true` and continue. **Config**: The agent MUST read the existing file (if present), update only `building_on_ai` and when applicable `eval_status`, then write back so other keys (e.g. `pace`) are preserved.
4. **Requirements source** (initiatives only) — How will requirements be provided? **[Q]** Q&A, **[D]** Doc, **[L]** Loom.
5. **Pace** (initiatives only) — How often to pause for review? **[S]** Section, **[D]** Doc, **[A]** All.
6. **Publish destination** (skills only) — Where should the finished skill be published? Detect common directories in the project root in this order: `config.json skill_publish_dir` key → `.agents/skills/` → `.claude/skills/` → `src/` → `skills/`. Offer the first detected path as the default, plus `.claude/skills/`, "Enter custom path", and "Don't publish". Write the chosen base path to `emergence-config.json` as `publish_dir` (null if "Don't publish").
7. **PR preference** — When merging to master (or initiative): **[F]** Feature PRs, **[I]** Initiative PR only, **[N]** None. Then run `create_lifecycle.py` with the matching flags (see each instruction module for exact args).

Then **start collecting requirements** via Q&A, doc, or Loom as chosen.

## Scoping by type

| Step                | Initiative | Tweak | Bug | Skill |
|---------------------|------------|-------|-----|-------|
| Name                | ✓          | ✓     | ✓   | ✓     |
| Draft folder        | ✓          | ✓     | ✓   | ✓     |
| LLMs and Evals?     | ✓          | ✓     | ✓   | ✓     |
| Req source          | ✓ (Q/D/L)  | —     | —   | —     |
| Pace                | ✓ (S/D/A)  | —     | —   | —     |
| Publish destination | —          | —     | —   | ✓     |
| PR preference       | ✓          | ✓     | ✓   | ✓     |

Initiatives run all steps except Publish destination. Tweaks and bugs run Name → Draft folder → LLMs and Evals? → PR preference, then their own clarify/draft steps. Skills run Name → Draft folder → LLMs and Evals? → Publish destination → PR preference, then `skill-create.md`.

## References

- Initiative start: [Clarify](./clarify.md) (runs this flow then PRD drafting).
- Tweak start: [Tweak](./tweak.md) (runs this flow then tweaklet).
- Bug start: [Bug Fix](./bug-fix.md) (runs this flow then buglet).
- Skill start: [Skill Create](./skill-create.md) (runs this flow then dialogue-driven SKILL.md authoring).

---
_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
