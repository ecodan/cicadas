# Project Overview: Cicadas

This repository contains the official implementation of the **Cicadas Method**—a sustainable, spec-driven development methodology designed for high-velocity engineering.

## 🔄 Dogfooding
Cicadas is both the **product** and the **process**. We use the Cicadas methodology (partitions, initiative branches, and Reflect operations) to evolve and maintain this orchestrator. Every change to this codebase follows the same rigorous spec-to-code-to-canon flow it enables for others.

## 📂 Project Structure

### Source & Code
- **[src/](src/)**: The main source directory.
- **[src/cicadas/](src/cicadas/)**: Contains the core logic of the orchestrator, including the repo-local common CLI at `scripts/cicadas.py`, its command registry, lifecycle scripts (kickoff, branch, status, create_lifecycle, open_pr, review, emit_event, get_events, validate_skill, skill_publish, unarchive), adaptive canon/bootstrap and targeted reconcile logic in `scripts/scan_repo.py`, `scripts/synthesize.py`, and `scripts/utils.py`, the optional code-graph toolchain (`graph_build.py`, `graph_query.py`, `graph_observe.py`, staged SQLite storage, Java/JS extractors, and the Java semantic harness), emergence instruction modules (the **standard start flow** in `emergence/start-flow.md` for initiative/tweak/bug/skill, initiative profiles for product/technical/mixed planning paths, **skill-create.md** and **skill-edit.md** for dialogue-driven Agent Skill authoring, plus **Building on AI** — gate and eval status in start flow, optional eval spec for initiatives, eval/benchmark reminder for tweaks/bugs), and spec/canon templates including Technical Brief, Operator Experience, and seeded slice packs for large/mega repos. The core initiative and technical-profile templates share compact front matter and section indexes so agents can restart from approved file-backed context.
- **[tests/](tests/)**: A comprehensive suite of unit and integration tests ensuring the reliability of the CLI scripts and orchestration logic, including `tests/test_templates.py` for the front matter contract and context-routing guidance.

### Agent & Methodology Memory
- **[.agents/](.agents/)**: Stores agentic configuration, including custom skills (like the `cicadas` skill itself) and automated workflows that guide the AI's behavior.
- **[.cicadas/](.cicadas/)**: The "Institutional Memory" of the project. This directory tracks active initiatives, holds the authoritative **Canon** (reverse-engineered from code), now including repo-scale metadata such as `repo.json`, `repo-tree.jsonl`, `repo-context.md`, and optional `canon/slices/` for larger repos, maintains the registry of partitions and signals, stores local worktree defaults in `config.json`, and can optionally hold `.cicadas/graph/` with staged graph artifacts, observability logs, area planning output, and extractor diagnostics for large-repo routing.

## 📖 Further Reading
- **Root [README.md](README.md)**: High-level introduction, philosophy, and quick-start guide.
- **[src/cicadas/README.md](src/cicadas/README.md)**: Detailed technical breakdown of the orchestrator's architecture, directory structure, and operational formulas.

## 🧪 Testing Conventions

Tests live in `tests/` and are written in `unittest` style with real temporary filesystems and real git repos — **not mocks**. The suite is commonly run with `pytest`, but the testing bias stays the same: Cicadas scripts touch the filesystem and git directly, so mocking these layers hides the integration bugs that matter. Prefer real temp git repos (`tempfile.mkdtemp()` + `git init`) over `unittest.mock`. Mocks are acceptable only for pure logic with no I/O side-effects (e.g. string parsing).

---
_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
