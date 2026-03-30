# Product Overview

> Canon document. Updated by the Synthesis agent at the close of each initiative.

## What This Is

Cicadas is a sustainable **spec-driven development (SDD)** methodology and toolset designed for human-AI pairing. It treats specifications (PRDs, designs, task lists) as disposable, expiring inputs and ensures the codebase remains the single source of truth.

## Why It Exists

Standard development processes often lead to "documentation rot" or "unplanned work" where code and specifications diverge. Cicadas fixes this by:
1.  **Enforcing Upfront Planning**: No code is written without a reviewed task list.
2.  **Maintaining Synchronization**: "Reflect" operations keep active specs in sync with architectural reality during development.
3.  **Reverse-Engineering Memory**: Permanent documentation (Canon) is synthesized from the code at the end of an initiative, rather than maintained manually.

---

## Users & Journeys

### AI-Ready Developer — The Builder

**Who they are:** A software engineer who utilizes agentic AI to build and maintain high-quality systems. They care about velocity, correctness, and minimizing "lore" hidden in Slack or brains.

**Their journey:** They begin by clarifying an idea into a PRD, drafting technical designs, and slicing work into registered feature branches. They guide implementation agents through a rigorous outer loop of development.

**Key needs:**
- Clear, unambiguous specs for agents.
- Conflict detection across parallel feature branches.
- Low-friction workflows for simple fixes and tweaks.

---

## Core Features (Current)

| Feature | Description | Status |
|---------|-------------|--------|
| **Standard Initiative** | Full 5-document spec suite (PRD, UX, Tech, Approach, Tasks) for complex features. | Shipped |
| **Lightweight Paths** | Streamlined workflows for bugs (`fix/`) and tweaks (`tweak/`) using single branches and minimal specs (`buglet.md`, `tweaklet.md`). | Shipped |
| **Orchestrator CLI** | Automated scripts for kickoff, branching, status tracking, signaling, and archiving. | Shipped |
| **Lifecycle & PRs** | Per-initiative `lifecycle.json` (PR boundaries + steps), `create_lifecycle.py`, `open_pr.py`, status merge detection (git-based); host-agnostic. | Shipped |
| **Synthesis** | Automated generation of Canon documentation from code and expired specs. | Shipped |
| **Signaling** | Asynchronous coordination between parallel branches via a central registry. | Shipped |
| **Installer** | One-command installation with Python 3.11+ check, GitHub archive distribution, agent integration setup (`claude-code`, `cursor`, `antigravity`, `rovodev`), and `--update` workflow. | Shipped |
| **Code Review** | Optional agent operation for spec-anchored evaluation of code diffs. Covers task completeness, architectural conformance, security (OWASP), correctness bugs, and code quality. Produces an ephemeral advisory report with tiered findings and a merge verdict. Supports feature, fix, and tweak branches. | Shipped |
| **Clarify Intake** | At Clarify start, the Builder can choose Q&A (interactive), Doc (`drafts/{initiative}/requirements.md`), or Loom (`drafts/{initiative}/loom.md`); the agent fills the PRD from the doc or transcript. | Shipped |
| **Building on AI** | Start flow asks "Is this project building on AI? (yes/no)" and, if yes, eval status (already have / will do). Persisted in `emergence-config.json`. Initiatives: optional eval spec (template + LLMOps playbook) after PRD/UX/Tech; Approach asks eval placement (before build / in parallel) with parallel warning. Tweaks/bugs: optional eval/benchmark reminder in tweaklet/buglet. Cicadas does not run or host evals. | Shipped |
| **Compact Context Contract** | Core initiative specs now include machine-readable front matter (`summary`, `modules`, `depends_on`, `index`) so agents can reload approved context from the spec files themselves instead of re-reading full drafting threads. | Shipped |
| **Context Reset Workflow** | Cicadas now documents Branch Reset, Phase Reset, and Partition Reset rules that re-anchor agents on `canon/summary.md`, spec front matter, and indexed sections first. Hosts may clear or compact context opportunistically, but file-backed state remains authoritative. | Shipped |
| **Template Contract Verification** | `tests/test_templates.py` verifies the front matter contract, Clarify's front matter refresh guidance, and the branch-start routing cue in `canon-summary.md`. | Shipped |

## Out of Scope (Intentional)

- **CI/CD Management** — Cicadas manages the *development* lifecycle and specifications; it does not replace deployment pipelines.
- **Project Management UI** — Cicadas lives in the terminal and filesystem; it is not a Jira/Linear replacement.
- **Package Manager Distribution** — Installer uses GitHub archive URL directly; npm/pip/homebrew distribution is future scope.

---

## Success Criteria

- **Spec Freshness**: Active specs match the codebase 100% at the time of merge.
- **Reduced Friction**: Bug fixes and tweaks move from draft to merge in < 50% of the time required for a standard initiative.
- **Zero-Friction Install**: `curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash` works in any fresh git repository in under 60 seconds.

---

_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
