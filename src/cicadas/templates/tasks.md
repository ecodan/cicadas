
---
summary: "{One tight paragraph summarizing the execution plan, current partition focus, and the most important delivery checkpoints. Keep it compact enough to drive next-task selection.}"
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
  - "{Primary files, modules, or packages targeted by these tasks}"
index:
  partition_one: "## Partition: feat/{branch-name-1}"
  partition_two: "## Partition: feat/{branch-name-2}"
  initiative_boundary: "## Initiative Boundary"
next_section: "## Partition: feat/{branch-name-1}"
---

# Tasks: {Initiative Name}

<!-- Add one section per partition defined in approach.md. -->
<!-- Use the format shown below for task lines, with unique numeric ids. -->
<!-- Inject Open PR tasks only at the lifecycle boundaries configured for this initiative. -->

## Partition: feat/{branch-name-1}

- [ ] {First concrete, testable task for this partition} <!-- id: 1 -->
- [ ] {Next task for this partition} <!-- id: 2 -->
<!-- Optional: inject a feature-boundary PR task here only when lifecycle.json enables feature PRs. -->

## Partition: feat/{branch-name-2}

- [ ] {First concrete, testable task for this partition} <!-- id: 10 -->
- [ ] {Next task for this partition} <!-- id: 11 -->

## Initiative Boundary

- [ ] Open PR: initiative/{initiative-name} -> master and await merge approval before continuing <!-- id: 100 -->
