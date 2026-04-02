---
summary: "Adapt Cicadas bootstrap and canon synthesis so larger repos use minimal orientation plus seeded slice packs that help agents plan the next local change safely, while small repos keep the simpler narrative-plus-modules canon."
phase: "clarify"
when_to_load:
  - "When defining or reviewing initiative goals, users, scope, success criteria, and risks."
  - "When validating that implementation still aligns with the intended problem and outcomes."
depends_on: []
modules:
  - "src/cicadas/emergence"
  - "src/cicadas/templates"
  - "src/cicadas/scripts"
  - ".cicadas/canon"
index:
  executive_summary: "## Executive Summary"
  project_classification: "## Project Classification"
  success_criteria: "## Success Criteria"
  user_journeys: "## User Journeys"
  scope: "## Scope"
  functional_requirements: "## Functional Requirements"
  non_functional_requirements: "## Non-Functional Requirements"
  open_questions: "## Open Questions"
  risk_mitigation: "## Risk Mitigation"
next_section: "Builder review"
---

# PRD: Repo Adaptability

## Progress

- [x] Executive Summary
- [x] Project Classification
- [x] Success Criteria
- [x] User Journeys
- [x] Scope & Phasing
- [x] Functional Requirements
- [x] Non-Functional Requirements
- [x] Open Questions
- [x] Risk Mitigation

## Executive Summary

Cicadas needs an adaptive canon model that changes with repository scale so bootstrap produces documentation that helps agents route and implement brownfield work safely, not just understand the product at a high level. This initiative keeps small repos simple, but for larger repos shifts from taxonomy-heavy canon toward minimal orientation plus seeded slice packs that help an agent decide where to start, what boundaries matter, and how to validate the next local change.

### What Makes This Special

- **Operational canon instead of uniform canon** — The initiative optimizes canon for safe action in brownfield repos, especially where routing is harder than product understanding.
- **Scale-aware bootstrap** — Bootstrap will classify repos as `normal-repo`, `large-repo`, or `mega-repo` before synthesis, so Cicadas can generate the right depth and artifact mix.
- **Seeded slices for larger repos** — `large-repo` and `mega-repo` modes should bias toward a few strong local slice packs instead of broad parallel hierarchies.
- **Brownfield usefulness as the acceptance bar** — Success is defined by whether an agent can answer “where do I start and what do I inspect next?” for real maintenance tasks.

## Project Classification

**Technical Type:** Developer Tool / Methodology Orchestrator  
**Domain:** Developer Infrastructure / AI-assisted Software Development  
**Complexity:** High — This changes Cicadas’ bootstrap strategy, canon information architecture, templates, and quality bar across multiple workflow stages.  
**Project Context:** Brownfield — Cicadas already supports bootstrap, canon synthesis, canon templates, and brownfield-oriented workflows, but its current canon model is optimized for smaller repositories.

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **Bootstrap a repo into the correct canon mode** — Cicadas explains whether the repo was classified as `normal-repo`, `large-repo`, or `mega-repo`, and the evidence is understandable enough for the Builder to trust or challenge it.
2. **Route brownfield work faster** — A Builder or agent can use generated canon to find the likely owning area, nearby areas, and first files/tests to inspect without reading a broad linear summary front-to-back.
3. **Use canon that matches repo reality** — Generated canon feels narrative for small repos, layered for large repos, and routing-first for mega repos, without forcing one uniform documentation depth everywhere.

### Technical Success

The system is successful when:

1. Bootstrap records repo-scale classification, evidence, and expected canon shape in durable workflow artifacts.
2. Canon synthesis supports scale-specific artifact families, especially seeded `slices/` packs for larger repos.
3. Templates and guidance define selective depth so Cicadas can seed a few slices, defer most local canon, and deepen it from real work later.
4. The project defines measurable evaluation criteria and benchmark-style validation for brownfield usefulness by repo scale.

### Measurable Outcomes

- For benchmark tasks, generated canon should support reporting `top-1` and `top-3` owning-area accuracy, time to first plausible area, time to first useful file, and time to first relevant test.
- Large- and mega-repo bootstrap outputs should include routing-oriented artifacts in 100% of classified runs.
- Scale detection must use multiple structural signals and not rely on line count alone.

---

## User Journeys

### Journey 1: Builder on a Large Repo — Routing the First Safe Change

A Builder brings Cicadas into a large brownfield repository where the codebase spans several architectural layers and product areas. They do not primarily need a polished narrative summary; they need to know where a bug fix or small feature should start, which neighboring areas are likely involved, and which tests and runtime paths matter first. During bootstrap, Cicadas classifies the repo as large, explains the evidence, and produces orientation plus routing artifacts that let the Builder route work confidently without spelunking the entire repository. Success feels like opening the right area docs first and avoiding a day of wrong turns.

**Requirements Revealed:** repo-scale classification, evidence capture, seeded slice generation, neighboring-slice guidance, test/runtime path guidance.

---

### Journey 2: Agent in a Mega Repo — Finding Ownership Before Coding

An implementation agent is asked to handle a brownfield change in a mega-repo where similar concepts exist in multiple packages, platforms, and plugin surfaces. A single broad tech overview is not enough because the main risk is starting in the wrong local slice and touching the wrong layer casually. Cicadas’ mega-repo canon gives the agent a small, trustworthy slice pack that points to likely ownership boundaries, likely neighbors, first files, first tests, and common traps. Success feels like getting to a plausible owner quickly with fewer wrong-area starts and safer initial file inspection.

**Requirements Revealed:** mega-repo mode, seeded local slices, local traps and invariants, compact reload artifacts, guardrails for high-risk areas.

---

### Journey 3: Cicadas Maintainer — Evolving Canon from Real Maintenance Work

A Cicadas maintainer wants canon quality to improve as the tool is used on real initiatives and bug fixes, rather than pretending one bootstrap pass will be perfect forever. They need the system to define what “useful” means, benchmark it by repo class, and leave room for iterative deepening of high-value areas over time. As they refine the system, they can update guidance, templates, and evaluation criteria based on recent successful work rather than expanding every module uniformly. Success feels like a canon strategy that learns from actual maintenance needs and stays practical to maintain.

**Requirements Revealed:** brownfield usefulness evaluation, benchmark task sets, iterative refinement guidance, selective depth strategy, migration path from current canon behavior.

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Builder on a large repo** | repo classification, evidence capture, seeded slices, neighboring-slice guidance, first-test and runtime-path guidance |
| **Implementation agent on a mega repo** | seeded slices, compact reload artifacts, likely owning slices, local traps, safe-start guidance |
| **Cicadas maintainer** | evaluation criteria, benchmark corpus guidance, selective depth policy, migration guidance, iterative deepening strategy |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- Add explicit canon modes: `normal-repo`, `large-repo`, and `mega-repo`.
- Define repo-scale detection heuristics that use structural and operational signals beyond line count.
- Record selected scale, supporting evidence, and expected canon shape during bootstrap.
- Update canon generation guidance and templates so outputs differ by repo mode.
- Introduce slice-oriented canon artifacts for large and mega repos under `slices/{slice-name}/`, seeded lazily during bootstrap.
- Define selective-depth guidance for deep-canoned, shallow-canoned, and deferred areas.
- Define contiguous-by-default slice selection, with multi-path slices allowed only when repeated real work shows strong co-change.
- Add brownfield usefulness acceptance criteria and benchmark-task guidance by repo scale.
- Encourage human hand-editing of the first large/mega orientation docs so repo history, intent, and "why" context are preserved and carried forward.
- Document migration guidance from the current canon model to the adaptive one.
- Keep the canon model forward-compatible with a follow-on graph-backed routing layer so machine navigation can move out of prose if that project succeeds.

**Quality Gates:**
- Bootstrap and synthesis guidance unambiguously describe when each canon mode applies and which artifacts it must produce.
- Templates and tests cover the new artifact structure and contract well enough to prevent silent regressions in canon shape.
- Evaluation guidance makes it possible to compare canon usefulness across repo modes using consistent metrics.

### Growth Features (Post-MVP)

**v2: Feedback-Driven Refinement**
- Support “validated by recent change” style updates so slice depth can improve from actual maintenance work.
- Add stronger workflows for refining seeded slices after successful real-world changes.

**v3: Graph-Backed Routing**
- Integrate a graph-backed code understanding layer for dependency traversal, interaction mapping, blast-radius analysis, and inside-out brownfield routing.
- Shift mechanically derivable navigation and adjacency questions toward the graph layer while keeping canon focused on meaning, boundaries, invariants, and change guidance.

**v4: Assisted Classification and Evaluation**
- Add more automated benchmark support or helper tooling for scoring routing accuracy and first-step usefulness.

### Vision (Future)

- Cicadas becomes adaptable enough to bootstrap anything from a compact single-product repo to a layered enterprise mega-repo with canon that is genuinely useful for day-two brownfield work.

---

## Functional Requirements

### 1. Repo-Scale Classification

**FR-1.1:** Cicadas must classify a repository into one of three canon modes: `normal-repo`, `large-repo`, or `mega-repo`.
- Classification must happen before canon synthesis begins.
- Classification output must be explicit enough for downstream guidance and artifact selection to consume.

**FR-1.2:** Repo-scale detection must consider multiple structural and operational signals.
- Signals must include top-level modules/packages, architectural layers, diversity of build/test/package/runtime paths, meaningful change-owning areas, plugin or product-family sprawl, and whether brownfield work usually requires routing first.
- Line count alone must not determine scale.

**FR-1.3:** Cicadas must apply an explicit decision heuristic when choosing the repo scale.
- Choose `normal-repo` when the repo has a small number of meaningful subsystems, one canon set can plausibly be read front-to-back, and most brownfield changes can be localized after reading product and tech overviews plus a modest set of module docs.
- Choose `large-repo` when routing matters, multiple architectural layers exist, and a bounded set of area docs can still cover most common work without requiring a routing-first map of many ownership zones.
- Choose `mega-repo` when the hardest part of brownfield work is finding the owning area, similar concepts appear in multiple layers or product families, packaging/runtime/test paths vary materially by area, and a single linear canon would be too shallow to be operationally useful.
- The heuristic should prioritize operational routing difficulty over raw repository size, and ambiguous cases must be resolved by asking which canon shape would best support the repo's most common future maintenance tasks.

**FR-1.4:** Bootstrap must record the selected scale, evidence for the choice, and the expected canon shape.
- Evidence should help the Builder understand why the repo was classified that way.
- Stored outputs must preserve enough context for later review or synthesis.

---

### 2. Scale-Specific Canon Design

**FR-2.1:** Cicadas must define required canon artifacts per repo scale.
- `normal-repo` requires `product-overview.md`, `tech-overview.md`, optional `ux-overview.md`, `modules/*.md`, and a compact canon summary.
- `large-repo` requires `product-overview.md`, `tech-overview.md`, `summary.md`, and a few seeded `slices/{slice-name}/` packs.
- `mega-repo` requires `product-overview.md`, `tech-overview.md`, `summary.md`, and a few seeded `slices/{slice-name}/` packs, with neighboring-slice guidance and stronger local invariants.

**FR-2.2:** Cicadas must distinguish canon layers and describe their purpose.
- Orientation canon explains product, repo shape, architectural layers, and major build/test/package/runtime paths.
- Slice canon explains what a local region is for, what belongs there, what must remain true, where changes usually start, and what nearby slices matter.
- Change guidance should live inside slice packs by default instead of in a separate always-on playbook hierarchy.

**FR-2.3:** Canon guidance must optimize for operational usefulness, not uniform completeness.
- Small repos should stay mostly narrative and explanatory.
- Large repos should become layered reference systems.
- Mega repos should become routing-first execution aids.

**FR-2.4:** Adaptive canon must remain forward-compatible with a follow-on graph-backed routing system.
- Canon should prioritize durable human-centric value such as area purpose, architectural boundaries, invariants, risky edges, common wrong turns, and change strategy.
- Machine-navigation details that can be derived mechanically should be structured so they can later move behind a graph-backed system without invalidating the canon model.

---

### 3. Selective Depth and Coverage

**FR-3.1:** Cicadas must define how bootstrap chooses where to go deep in large and mega repos.
- Selection signals should include likely churn, architectural centrality, test richness, runtime/package centrality, routing-hub importance, and likelihood of future brownfield change.

**FR-3.2:** Bootstrap guidance must explicitly mark deep-canoned, shallow-canoned, and deferred areas.
- The system must not imply that every leaf area receives identical treatment.
- Deferred areas should still be visible enough that maintainers know they were intentionally not expanded yet.

---

### 4. Brownfield Usefulness Evaluation

**FR-4.1:** Cicadas must define a brownfield usefulness acceptance bar for canon.
- Canon must help answer where to start, what to read second, which nearby areas to inspect, what not to touch casually, what tests to run first, and which runtime/package path matters.

**FR-4.2:** Cicadas must define benchmark task sets by repo scale.
- Benchmark tasks should cover bug fixes, brownfield feature edits, endpoint or contract changes, frontend regressions, permission/workflow/configuration changes, and build/package/runtime issues.
- Each benchmark task should include expected likely owners, neighbors, first files, and first tests.

**FR-4.3:** Cicadas must define comparison metrics for canon usefulness by mode.
- Metrics should include top-1 owning-area accuracy, top-3 owning-area accuracy, time to first plausible area, time to first useful file, wrong-area starts, files opened before correct owner, time to first relevant test, and human usefulness rating.

**FR-4.4:** The initiative must document how canon quality can improve through real maintenance work over time.
- Guidance should support refining seeded slices from recent successful changes without requiring full re-documentation of every local area.

**FR-4.5:** This initiative must explicitly treat graph-backed machine navigation as a dependent follow-on direction, not an MVP assumption.
- If the graph-backed follow-on succeeds, canon should evolve to become more human-centric while the graph handles inside-out traversal, adjacency, and dependency-oriented routing.
- If the graph-backed follow-on fails or is deferred, machine-navigation-heavy canon ideas should remain in a parking lot rather than expanding this initiative’s MVP scope prematurely.

---

### 5. Migration and Maintainability

**FR-5.1:** Cicadas must provide migration guidance from the current mostly uniform canon behavior to the adaptive canon model.
- Guidance should explain how existing bootstrap and canon synthesis assumptions change.
- Guidance should help maintainers reason about backward compatibility for current canon artifacts and workflows.

**FR-5.2:** The initiative must update bootstrap and canon-generation guidance, templates, and related docs consistently.
- The maintained guidance should describe how repo mode affects artifact creation, routing emphasis, and acceptance expectations.

---

## Non-Functional Requirements

- **Performance:** Scale detection and adaptive bootstrap guidance should remain lightweight enough for agent-led repo discovery; the process should not require exhaustive enumeration of every leaf module before producing useful canon.
- **Reliability:** Classification and artifact-selection rules must be deterministic enough that two careful agents working from the same repo evidence reach substantially similar canon-mode outcomes.
- **Security:** Routing and playbook guidance must avoid encouraging broad unsafe edits; generated canon should explicitly call out “do not touch casually” areas when risk is high.
- **Maintainability:** New templates, guidance, and tests must make the adaptive canon model understandable to future Cicadas maintainers and extensible to additional repo patterns without rewriting the whole workflow; the canon architecture should also preserve a clean seam for later graph-backed routing.

---

## Open Questions

- What is the minimum durable artifact or metadata location for recording repo-scale evidence so later synthesis and maintenance flows can rely on it? Owner: implementation design. Urgency: high.
- Should compact area-level reload artifacts for mega repos be separate files, front matter summaries, or both? Owner: implementation design. Urgency: high.
- How much of scale detection should be deterministic script logic versus agent judgment encoded in bootstrap guidance? Owner: implementation design. Urgency: medium.
- Which existing canon consumers, if any, assume the current module-oriented artifact set and need compatibility handling? Owner: implementation design. Urgency: medium.
- What exact boundary should exist between adaptive canon and a future graph-backed routing layer so the systems complement rather than duplicate each other? Owner: follow-on architecture design. Urgency: medium.

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Repo-scale heuristics are too vague and produce inconsistent classifications | Med | High | Define explicit evidence signals, preserve rationale in artifacts, and add tests/examples that anchor the thresholds. |
| The initiative produces more documents without actually improving routing usefulness | Med | High | Make benchmark-style brownfield usefulness the acceptance bar and require routing-first artifacts for large and mega repos. |
| Adaptive canon adds too much maintenance burden for Cicadas maintainers | Med | Med | Use selective depth, deferred-area marking, and iterative deepening so only high-value areas receive deep canon investment. |
| Existing bootstrap or synthesis assumptions break when artifact sets vary by repo mode | Med | High | Include migration guidance, update templates/docs together, and add tests for mode-specific artifact expectations. |
| Canon over-invests in machine-navigation detail that should belong to a future graph layer | Med | Med | Keep this initiative centered on human judgment and durable routing guidance, and park graph-like navigation depth unless the follow-on graph project succeeds. |
