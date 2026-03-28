# Project Overview: Cicadas

This repository contains the official implementation of the **Cicadas Method**—a sustainable, spec-driven development methodology designed for high-velocity engineering.

## 🔄 Dogfooding
Cicadas is both the **product** and the **process**. We use the Cicadas methodology (partitions, initiative branches, and Reflect operations) to evolve and maintain this orchestrator. Every change to this codebase follows the same rigorous spec-to-code-to-canon flow it enables for others.

## 📂 Project Structure

### Source & Code
- **[src/](src/)**: The main source directory.
  - **[src/cicadas/](src/cicadas/)**: Contains the core logic of the orchestrator, including lifecycle scripts (kickoff, branch, status, create_lifecycle, open_pr, review, emit_event, get_events, validate_skill, skill_publish, unarchive), emergence instruction modules (the **standard start flow** in `emergence/start-flow.md` for initiative/tweak/bug/skill, **skill-create.md** and **skill-edit.md** for dialogue-driven Agent Skill authoring, plus **Building on AI** — gate and eval status in start flow, optional eval spec for initiatives, eval/benchmark reminder for tweaks/bugs), and spec templates (including `skill-SKILL.md` scaffold).
- **[tests/](tests/)**: A comprehensive suite of unit and integration tests ensuring the reliability of the CLI scripts and orchestration logic.

### Agent & Methodology Memory
- **[.agents/](.agents/)**: Stores agentic configuration, including custom skills (like the `cicadas` skill itself) and automated workflows that guide the AI's behavior.
- **[.cicadas/](.cicadas/)**: The "Institutional Memory" of the project. This directory tracks active initiatives, holds the authoritative **Canon** (reverse-engineered from code), and maintains the registry of partitions and signals.

## 📖 Further Reading
- **Root [README.md](README.md)**: High-level introduction, philosophy, and quick-start guide.
- **[src/cicadas/README.md](src/cicadas/README.md)**: Detailed technical breakdown of the orchestrator's architecture, directory structure, and operational formulas.

## 🧪 Testing Conventions

Tests live in `tests/` and use `unittest` with real temporary filesystems and real git repos — **not mocks**. Cicadas scripts touch the filesystem and git directly; mocking these layers hides the integration bugs that matter. Prefer real temp git repos (`tempfile.mkdtemp()` + `git init`) over `unittest.mock`. Mocks are acceptable only for pure logic with no I/O side-effects (e.g. string parsing).

---
_Copyright 2026 Cicadas Contributors_
_SPDX-License-Identifier: Apache-2.0_
