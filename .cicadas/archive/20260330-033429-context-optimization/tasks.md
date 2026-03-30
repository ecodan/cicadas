---
summary: Execute context optimization by standardizing front matter in templates, teaching Cicadas reset-and-reload rules, and verifying the contract without introducing a new persistent context file.
phase: tasks
when_to_load:
  - When selecting the next implementation task.
  - When checking partition status and PR boundaries.
depends_on:
  - prd.md
  - ux.md
  - tech-design.md
  - approach.md
modules:
  - src/cicadas/SKILL.md
  - src/cicadas/templates/prd.md
  - src/cicadas/templates/ux.md
  - src/cicadas/templates/tech-design.md
  - src/cicadas/templates/approach.md
  - src/cicadas/templates/tasks.md
  - src/cicadas/templates/canon-summary.md
  - tests
index:
  frontmatter_contract: "## Partition: feat/frontmatter-contract"
  skill_reset_rules: "## Partition: feat/skill-reset-rules"
  context_verification: "## Partition: feat/context-verification"
next_section: "## Partition: feat/frontmatter-contract"
---

# Tasks: context-optimization

## Partition: feat/frontmatter-contract

- [x] Define the shared front matter schema for core initiative specs: required keys, allowed semantics, and compact-summary expectations <!-- id: 1 -->
- [x] Update `src/cicadas/templates/prd.md` to include the standardized front matter and section index <!-- id: 2 -->
- [x] Update `src/cicadas/templates/ux.md` to include the standardized front matter and section index <!-- id: 3 -->
- [x] Update `src/cicadas/templates/tech-design.md` to include the standardized front matter and section index <!-- id: 4 -->
- [x] Update `src/cicadas/templates/approach.md` to include the standardized front matter and section index <!-- id: 5 -->
- [x] Update `src/cicadas/templates/tasks.md` to include the standardized front matter and section index <!-- id: 6 -->
- [x] Check template consistency and note any schema refinements needed before skill updates <!-- id: 7 -->

## Partition: feat/skill-reset-rules

- [x] Update `src/cicadas/SKILL.md` to instruct agents to create and refresh front matter during emergence and Reflect <!-- id: 10 -->
- [x] Add a Branch Reset rule describing the compact reload set at branch start <!-- id: 11 -->
- [x] Add a Phase Reset rule for post-approval handoff between Clarify, UX, Tech, Approach, and Tasks <!-- id: 12 -->
- [x] Add a Partition Reset rule that defaults new partition work to partition-scoped context <!-- id: 13 -->
- [x] Add opportunistic host hints to clear, compact, or fresh-start context at reset boundaries when supported <!-- id: 14 -->
- [x] Document escalation rules for when agents may open full documents beyond front matter and indexed sections <!-- id: 15 -->
- [x] Clarify that reset rules re-anchor authority to approved file-backed context and do not guarantee memory eviction in a long-lived session <!-- id: 16 -->
- [x] Feature branch merged directly into `initiative/context-optimization` because feature PRs are disabled in `lifecycle.json` <!-- id: 17 -->

## Partition: feat/context-verification

- [x] Decide whether `src/cicadas/templates/canon-summary.md` needs a small active-spec routing note while keeping it the shared compact context file <!-- id: 20 -->
- [x] Add or update tests that verify the new template contract and any helper behavior introduced by the implementation <!-- id: 21 -->
- [x] Verify fallback expectations for older specs without front matter and document any limitations <!-- id: 22 -->
- [x] Run the relevant test suite and record results <!-- id: 23 -->
- [x] Feature branch merged directly into `initiative/context-optimization` because feature PRs are disabled in `lifecycle.json` <!-- id: 24 -->

## Initiative Boundary

- [ ] Open PR: initiative/context-optimization -> master and await merge approval before continuing <!-- id: 100 -->
