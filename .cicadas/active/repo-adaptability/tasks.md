---
summary: "Deliver Bootstrap V2 in five partitions: strengthen evidence and build discovery first, then add scale-floor classification and canon strategy planning, then implement strategy-driven canon generation and guidance updates in parallel, and finish with QA/autocorrection and end-to-end validation."
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

- [ ] Expand `src/cicadas/scripts/scan_repo.py` so `scan-repo` gathers stronger evidence: meaningful file count, estimated LoC, language totals, top-level fanout, and major structural surfaces. <!-- id: 1 -->
- [ ] Add build/workspace discovery for Java, Node/TS, Python, and Rust, preferring declared build structure over directory heuristics when present. <!-- id: 2 -->
- [ ] Add shared metadata helpers in `src/cicadas/scripts/utils.py` for recording build systems, declared modules, major code zones, test surfaces, runtime/package surfaces, and override-friendly meaningful-file filtering rules. <!-- id: 3 -->
- [ ] Preserve streaming inventory output and progress reporting while keeping ignored/generated/local/agentic content excluded from meaningful-file metrics by default. <!-- id: 4 -->
- [ ] Add real-filesystem tests covering build detection, evidence gathering, excluded content, and scan output shape across representative repo layouts. <!-- id: 5 -->

## Partition: feat/bootstrap-v2-classification-planning

- [ ] Refactor classification logic in `src/cicadas/scripts/scan_repo.py` and `src/cicadas/scripts/utils.py` into explicit scale signals, structure signals, and final `max(scale_class, topology_class)` decision behavior. <!-- id: 10 -->
- [ ] Enforce the agreed scale floors: `normal-repo` below `1K meaningful files` and `100K LoC`, `large-repo` at `1K+` or `100K+`, and `mega-repo` at `25K+` or `2M+`. <!-- id: 11 -->
- [ ] Replace or demote confusing user-facing terms like `ownership_zone_candidates` and `runtime_paths` in favor of clearer routing and structure language. <!-- id: 12 -->
- [ ] Add canon strategy selection to `repo.json`, including chosen strategy, planned root docs, planned module docs, selective snapshots, deferred areas, validation steps, and uncertainty. <!-- id: 13 -->
- [ ] Update `src/cicadas/emergence/bootstrap.md` and related tests so classification and strategy explanations are understandable to a human reviewer. <!-- id: 14 -->

## Partition: feat/bootstrap-v2-canon-generation

- [ ] Refactor `src/cicadas/scripts/synthesize.py` to consume generation targets from `repo.json` rather than inferring canon shape ad hoc from repo mode alone. <!-- id: 20 -->
- [ ] Support flat, routed, and hierarchical canon generation, including root orientation docs, routed docs, selective snapshots, and nested `modules/` canon for mega repos. <!-- id: 21 -->
- [ ] Keep `repo-context.md` as the compact structural reload artifact and use `repo-tree.jsonl` only when deeper structural evidence is required. <!-- id: 22 -->
- [ ] Preserve lazy metadata backfill for older repos by routing missing adaptive metadata recovery through the evolved `scan-repo` path. <!-- id: 23 -->
- [ ] Add temp-repo tests for strategy-driven generation, hierarchical module outputs, and legacy fallback behavior. <!-- id: 24 -->

## Partition: feat/bootstrap-v2-guidance-and-templates

- [ ] Update `src/cicadas/emergence/bootstrap.md` to describe the V2 stages: evidence gathering, build-first discovery, classification, strategy planning, generation, and QA. <!-- id: 30 -->
- [ ] Update `src/cicadas/templates/synthesis-prompt.md`, `src/cicadas/templates/canon-summary.md`, and related templates to use clearer language like major code zones, working areas, routing surfaces, and declared modules. <!-- id: 31 -->
- [ ] Adjust hierarchical guidance and template responsibilities so mega-repo sub-canons live under `modules/` and remain aware of root canon. <!-- id: 32 -->
- [ ] Refresh `README.md` and nearby docs to explain the evolved `scan-repo` workflow and the rationale behind flat, routed, and hierarchical canon strategies. <!-- id: 33 -->

## Partition: feat/bootstrap-v2-qa-and-validation

- [ ] Add validation helpers that compare generated canon artifacts against the selected strategy and gathered build/structure evidence. <!-- id: 40 -->
- [ ] Implement best-effort autocorrection for cheap validation failures such as missing planned docs, broken links, or omitted references to obvious major modules. <!-- id: 41 -->
- [ ] Add end-to-end tests covering normal, large, and mega repos, especially build-defined monorepos whose scale should force `mega-repo`. <!-- id: 42 -->
- [ ] Update completion summaries so bootstrap reports scale findings, detected build/workspace structure, chosen repo mode, chosen canon strategy, generated artifacts, deferred areas, and uncertainty. <!-- id: 43 -->
- [ ] Run the relevant test suites and resolve any regressions so Bootstrap V2 is stable before the initiative boundary. <!-- id: 44 -->

## Initiative Boundary

- [ ] Open PR: initiative/repo-adaptability -> master and await merge approval before continuing <!-- id: 100 -->
