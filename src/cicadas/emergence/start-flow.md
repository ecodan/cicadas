# Standard Start Flow

**All** entry points (initiative, tweak, bug, skill) MUST run this flow before collecting requirements or drafting specs. No matter how the user phrases the request, execute these steps in order. If the user provides information up front (e.g. "Start a tweak called XYZ"), pre-populate the answers but **still run the flow and verify** (e.g. "What is the name? 1. XYZ, 2. Other (enter the name)").

## Mandatory sequence

1. **Name** — Get the initiative / tweak / bug / skill name. Confirm even when the user already said it (offer "1. {their name}, 2. Other").
2. **Create draft folder** — Ensure `.cicadas/drafts/{name}/` exists and create any initial files (e.g. `emergence-config.json` for initiatives, or lifecycle when PR preference is set).
3. **Initiative profile** (initiatives only) — Ask: *"What initiative profile should this use? [product] full PRD + UX, [technical] Technical Brief + optional Operator Experience, [mixed] choose the appropriate artifact per surface."* Write `initiative_profile: "product" | "technical" | "mixed"` to `.cicadas/drafts/{name}/emergence-config.json` (merge with existing keys). If no profile exists on an older draft, treat it as `"product"` for backward compatibility. PRD and UXD become optional only through this explicit profile mechanism; agents MUST NOT skip them ad hoc.
4. **LLMs and Evals?** — Ask: *"Will this feature or change be powered by LLMs and may require ML evals to ensure quality? (yes / no)"*. If the user says **no**, write `building_on_ai: false` to `.cicadas/drafts/{name}/emergence-config.json` (merge with existing keys, e.g. `pace` or `initiative_profile`), then continue to step 5 (initiatives) or step 7/8 (tweaks/bugs/skills). If the user says **yes**, write `building_on_ai: true`, then — **for initiatives, tweaks, and bugs only** — ask: *"This change involves LLMs. Experimentation and evals may be required. Does this project already have completed evals, or will you be doing evals? (already have / will do)"*. Write `eval_status: "already_have"` or `eval_status: "will_do"` to `emergence-config.json` (merge with existing keys), then continue. **For skills**, skip the eval-status follow-up (skill evals are Post-MVP); write only `building_on_ai: true` and continue. **Config**: The agent MUST read the existing file (if present), update only `building_on_ai` and when applicable `eval_status`, then write back so other keys (e.g. `pace` or `initiative_profile`) are preserved.
5. **Requirements source** (initiatives only) — How will requirements be provided? **[Q]** Q&A, **[D]** Doc, **[L]** Loom.
6. **Pace** (initiatives only) — How often to pause for review? **[S]** Section, **[D]** Doc, **[A]** All.
7. **Publish destination** (skills only) — Where should the finished skill be published? Detect common directories in the project root in this order: `config.json skill_publish_dir` key → `.agents/skills/` → `.claude/skills/` → `src/` → `skills/`. Offer the first detected path as the default, plus `.claude/skills/`, "Enter custom path", and "Don't publish". Write the chosen base path to `emergence-config.json` as `publish_dir` (null if "Don't publish").
8. **PR preference** — When merging to master (or initiative): **[F]** Feature PRs, **[I]** Initiative PR only, **[N]** None. Then run `create_lifecycle.py` with the matching flags (see each instruction module for exact args).

Then **start collecting requirements** via Q&A, doc, or Loom as chosen.

## Initiative profiles

Initiative profiles control the clarify and experience artifacts for full initiatives only:

| Profile | Clarify Artifact | Experience Artifact | Required Later Specs |
|---------|------------------|---------------------|----------------------|
| `product` | Full `prd.md` | Full `ux.md` | Tech Design, Approach, Tasks |
| `mixed` | `prd.md` or `technical-brief.md` | `ux.md` or `operator-experience.md` | Tech Design, Approach, Tasks |
| `technical` | `technical-brief.md` | Skip UX only when there is no meaningful human-facing or agent-facing interaction; otherwise `operator-experience.md` | Tech Design, Approach, Tasks |

Use the `technical` profile when most of these are true: primary users are maintainers, agents, operators, or developers; there is no customer-facing UI change; there is no major product workflow change; the work is infrastructure, refactor, parser/extractor, migration, performance, internal CLI, testing, build-system, or agent-guidance focused; success can be expressed as technical acceptance criteria; and the experience surface is limited to CLI output, logs, error messages, docs, or agent instructions.

If the work includes meaningful end-user interaction, product positioning, or ambiguous user journeys, use `product` or `mixed`.

## Scoping by type

| Step                | Initiative | Tweak | Bug | Skill |
|---------------------|------------|-------|-----|-------|
| Name                | ✓          | ✓     | ✓   | ✓     |
| Draft folder        | ✓          | ✓     | ✓   | ✓     |
| Initiative profile  | ✓          | —     | —   | —     |
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
