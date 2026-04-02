# Routing Guide

> Canon document. Generated for repositories where brownfield work needs routing help before implementation starts.

## When To Start Here

- Use this guide when the task begins from a symptom, failing test, endpoint, package, or unclear owning area.
- Prefer this guide before broad orientation docs when multiple neighboring areas may plausibly own the change.

## Routing Rules

- If the change is about `{change-type}`, start in `{area-or-module}`.
- If the first guess touches permissions, packaging, runtime assembly, or workflow boundaries, inspect neighboring areas before editing.
- If the task is mechanical adjacency or dependency traversal, prefer graph-backed tooling when available; otherwise use `repo-context.md` plus targeted area docs.
- Keep graph area names aligned with canon slices and ownership language so `graph area` and this guide reinforce the same first-hop routing decisions.

## Optional Graph Shortcuts

- `python src/cicadas/scripts/cicadas.py graph area {artifact}` when the owning area is unclear
- `python src/cicadas/scripts/cicadas.py graph neighbors {artifact}` when boundary-crossing edits look likely
- `python src/cicadas/scripts/cicadas.py graph tests {symbol}` or `graph signature-impact {symbol}` when a failing test or signature change is the entrypoint

## Nearby Areas

- `{area-a}` — {Why it is a common neighbor}
- `{area-b}` — {Why it is a common neighbor}

## Common Wrong Turns

- `{wrong-turn}` — {Why it causes wasted motion or unsafe edits}

## Build, Test, And Runtime Notes

- Build: `{key build path or command}`
- Test: `{first test path or command}`
- Runtime: `{runtime path or environment note}`
