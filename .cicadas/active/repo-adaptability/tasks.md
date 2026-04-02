---
summary: "Deliver Bootstrap V3 in six partitions: strengthen evidence and build discovery first, add scale-floor classification and slice-aware canon strategy planning, implement orientation-plus-seeded-slices generation and guidance updates in parallel, finish bootstrap validation, and then add targeted canon reconcile for initiative completion."
phase: "tasks"
when_to_load:
  - "When selecting the next implementation task or reviewing completion state."
  - "When checking partition progress, PR boundaries, or execution sequencing."
depends_on:
  - "prd.md"
  - "ux.md"
  - "tech-design.md"
  - "approach.md"
modules:
  - "src/cicadas/scripts"
  - "src/cicadas/emergence"
  - "src/cicadas/templates"
  - "tests"
index:
  partition_one: "## Partition: feat/bootstrap-v2-evidence-foundation"
  partition_two: "## Partition: feat/bootstrap-v2-classification-planning"
  initiative_boundary: "## Initiative Boundary"
next_section: "## Partition: feat/bootstrap-v2-evidence-foundation"
---

# Tasks: Repo Adaptability

## Partition: feat/bootstrap-v2-evidence-foundation

- [x] Expand `src/cicadas/scripts/scan_repo.py` so `scan-repo` gathers stronger evidence: meaningful file count, estimated LoC, language totals, top-level fanout, and major structural surfaces. <!-- id: 1 -->
- [x] Add build/workspace discovery for Java, Node/TS, Python, and Rust, preferring declared build structure over directory heuristics when present. <!-- id: 2 -->
- [x] Add shared metadata helpers in `src/cicadas/scripts/utils.py` for recording build systems, declared modules, major code zones, test surfaces, runtime/package surfaces, and override-friendly meaningful-file filtering rules. <!-- id: 3 -->
- [x] Preserve streaming inventory output and progress reporting while keeping ignored/generated/local/agentic content excluded from meaningful-file metrics by default. <!-- id: 4 -->
- [x] Add real-filesystem tests covering build detection, evidence gathering, excluded content, and scan output shape across representative repo layouts. <!-- id: 5 -->

## Partition: feat/bootstrap-v2-classification-planning

- [x] Refactor classification logic in `src/cicadas/scripts/scan_repo.py` and `src/cicadas/scripts/utils.py` into explicit scale signals, structure signals, and final `max(scale_class, topology_class)` decision behavior. <!-- id: 10 -->
- [x] Enforce the agreed scale floors: `normal-repo` below `1K meaningful files` and `100K LoC`, `large-repo` at `1K+` or `100K+`, and `mega-repo` at `25K+` or `2M+`. <!-- id: 11 -->
- [x] Replace or demote confusing user-facing terms like `ownership_zone_candidates` and `runtime_paths` in favor of clearer routing and structure language. <!-- id: 12 -->
- [x] Add canon strategy selection to `repo.json`, including chosen strategy, planned root docs, seeded slice packs, optional module docs, deferred slices, validation steps, and uncertainty. <!-- id: 13 -->
- [x] Update `src/cicadas/emergence/bootstrap.md` and related tests so classification and strategy explanations are understandable to a human reviewer. <!-- id: 14 -->

## Partition: feat/bootstrap-v2-canon-generation

- [x] Refactor `src/cicadas/scripts/synthesize.py` to consume generation targets from `repo.json` rather than inferring canon shape ad hoc from repo mode alone. <!-- id: 20 -->
- [x] Support flat canon for small repos and orientation plus seeded `slices/` generation for large and mega repos. <!-- id: 21 -->
- [x] Keep `repo-context.md` as the compact structural reload artifact and use `repo-tree.jsonl` only when deeper structural evidence is required. <!-- id: 22 -->
- [x] Preserve lazy metadata backfill for older repos by routing missing adaptive metadata recovery through the evolved `scan-repo` path. <!-- id: 23 -->
- [x] Add temp-repo tests for strategy-driven generation, seeded slice outputs, and legacy fallback behavior. <!-- id: 24 -->

## Partition: feat/bootstrap-v2-guidance-and-templates

- [x] Update `src/cicadas/emergence/bootstrap.md` to describe the V2 stages: evidence gathering, build-first discovery, classification, strategy planning, generation, and QA. <!-- id: 30 -->
- [x] Update `src/cicadas/templates/synthesis-prompt.md`, `src/cicadas/templates/canon-summary.md`, and related templates to use clearer language like major code zones, slices, neighboring slices, and declared modules. <!-- id: 31 -->
- [x] Add and wire the minimum slice templates so large/mega repos can seed `summary`, `boundaries`, `architecture`, `invariants`, and `change-guide` docs. <!-- id: 32 -->
- [x] Refresh `README.md` and nearby docs to explain the evolved `scan-repo` workflow and the rationale behind flat and locality-first canon strategies. <!-- id: 33 -->

## Partition: feat/bootstrap-v2-qa-and-validation

- [x] Add validation helpers that compare generated canon artifacts against the selected strategy and gathered build/structure evidence, especially seeded slices. <!-- id: 40 -->
- [x] Implement best-effort autocorrection for cheap validation failures such as missing planned docs, broken links, or omitted references to obvious major modules. <!-- id: 41 -->
- [x] Add end-to-end tests covering normal, large, and mega repos, especially build-defined monorepos whose scale should force `mega-repo`. <!-- id: 42 -->
- [x] Update completion summaries so bootstrap reports scale findings, detected build/workspace structure, chosen repo mode, chosen canon strategy, generated artifacts, deferred areas, and uncertainty. <!-- id: 43 -->
- [x] Run the relevant test suites and resolve any regressions so Bootstrap V2 is stable before the initiative boundary. <!-- id: 44 -->

## Partition: feat/bootstrap-v3-targeted-reconcile

- [x] Add helper logic in `src/cicadas/scripts/utils.py` and `src/cicadas/scripts/synthesize.py` to compute the touched canon scope for initiative completion from changed paths, spec-declared modules, and known slices. <!-- id: 50 -->
- [x] Keep full initiative-end canon synthesis for `normal-repo`, but make `large-repo` and `mega-repo` use targeted reconcile by default. <!-- id: 51 -->
- [x] Add heuristics that update `product-overview.md`, `tech-overview.md`, and `summary.md` only when the initiative changed durable repo-wide truth. <!-- id: 52 -->
- [x] Update touched slice packs by default and expand to neighboring slices only when interfaces, boundaries, or invariants changed. <!-- id: 53 -->
- [x] Create a new slice during initiative completion only when the implementation proved the existing slice is too broad for future safe work. <!-- id: 54 -->
- [x] Update `src/cicadas/templates/synthesis-prompt.md` and lifecycle guidance in `src/cicadas/SKILL.md` so initiative completion explicitly follows full synthesis for `normal-repo` and targeted reconcile for `large-repo` / `mega-repo`. <!-- id: 55 -->
- [x] Add real-filesystem tests for normal-repo full synthesis, large-repo targeted reconcile, and a boundary-shift case that pulls in one neighboring slice. <!-- id: 56 -->

## Initiative Boundary

- [ ] Open PR: initiative/repo-adaptability -> master and await merge approval before continuing <!-- id: 100 -->
