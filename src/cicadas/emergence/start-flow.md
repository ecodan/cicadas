# Standard Start Flow

> Deprecated for skill authoring: the `skill` branch of this flow is retained
> only for legacy compatibility. Initiative, tweak, and bug flows remain the
> current Cicadas entrypoints.

All current entry points (initiative, tweak, bug) MUST run this flow before
collecting requirements or drafting specs. The legacy `skill` path is still
documented below for compatibility only. No matter how the user phrases the
request, execute the applicable steps in order. If the user provides
information up front (e.g. "Start a tweak called XYZ"), pre-populate the
answers but **still run the flow and verify** (e.g. "What is the name? 1. XYZ,
2. Other (enter the name)").

## Mandatory sequence

1. **Name** — Get the initiative / tweak / bug / skill name. Confirm even when the user already said it (offer "1. {their name}, 2. Other").
2. **Create draft folder** — Ensure `.cicadas/drafts/{name}/` exists and create any initial files (e.g. `emergence-config.json` for initiatives, or lifecycle when PR preference is set).
3. **Requirements source** (initiatives only) — How will requirements be provided? **[Q]** Q&A, **[D]** Doc, **[L]** Loom.
4. **Pace** (initiatives only) — How often to pause for review? **[S]** Section, **[D]** Doc, **[A]** All.
5. **Publish destination** (skills only) — Where should the finished skill be published? Detect common directories in the project root in this order: `config.json skill_publish_dir` key → `.agents/skills/` → `.claude/skills/` → `src/` → `skills/`. Offer the first detected path as the default, plus `.claude/skills/`, "Enter custom path", and "Don't publish". Write the chosen base path to `emergence-config.json` as `publish_dir` (null if "Don't publish").
6. **PR preference** — When merging to master (or initiative): **[F]** Feature PRs, **[I]** Initiative PR only, **[N]** None. Then run `create_lifecycle.py` with the matching flags (see each instruction module for exact args).

Then **start collecting requirements** via Q&A, doc, or Loom as chosen.

## Scoping by type

| Step                | Initiative | Tweak | Bug | Skill |
|---------------------|------------|-------|-----|-------|
| Name                | ✓          | ✓     | ✓   | ✓     |
| Draft folder        | ✓          | ✓     | ✓   | ✓     |
| Req source          | ✓ (Q/D/L)  | —     | —   | —     |
| Pace                | ✓ (S/D/A)  | —     | —   | —     |
| Publish destination | —          | —     | —   | ✓     |
| PR preference       | ✓          | ✓     | ✓   | ✓     |

Initiatives run all steps except Publish destination. Tweaks and bugs run Name
→ Draft folder → PR preference, then their own clarify/draft steps. Skills run
Name → Draft folder → Publish destination → PR preference, then
`skill-create.md` (deprecated legacy path).

## References

- Initiative start: [Clarify](./clarify.md) (runs this flow then PRD drafting).
- Tweak start: [Tweak](./tweak.md) (runs this flow then tweaklet).
- Bug start: [Bug Fix](./bug-fix.md) (runs this flow then buglet).
- Skill start (deprecated legacy path): [Skill Create](./skill-create.md) (runs this flow then dialogue-driven SKILL.md authoring).

---
_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
