# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import time
from pathlib import Path

from utils import graph_area_plan_path, graph_dir, graph_progress_log_path, graph_progress_path


def _format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{value}B"


def _load_progress_snapshot() -> dict | None:
    path = graph_progress_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _load_progress_events() -> list[dict]:
    path = graph_progress_log_path()
    if not path.exists():
        return []
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _spool_summary() -> list[str]:
    spool_dir = graph_dir() / "spool"
    if not spool_dir.exists():
        return ["- Spool: not created yet"]
    lines = []
    for name in ("nodes.jsonl", "edges.jsonl"):
        path = spool_dir / name
        if path.exists():
            lines.append(f"- {name}: {_format_bytes(path.stat().st_size)}")
        else:
            lines.append(f"- {name}: missing")
    return lines


def _area_plan_summary() -> list[str]:
    path = graph_area_plan_path()
    if not path.exists():
        return ["- Area plan: not created yet"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"- Area plan: unreadable ({path})"]
    return [f"- Area plan: {len(payload.get('areas', []))} areas ({path.name})"]


def render_progress_tail(lines: int = 10) -> str:
    snapshot = _load_progress_snapshot()
    events = _load_progress_events()
    if snapshot is None and not events:
        return "No graph progress recorded yet."

    output = ["Graph build tail"]
    if snapshot is not None:
        output.extend(
            [
                f"- Status: {snapshot.get('status', 'unknown')}",
                f"- Phase: {snapshot.get('phase', 'unknown')}",
                f"- Percent: {snapshot.get('percent_complete', 0)}%",
                f"- Elapsed: {snapshot.get('elapsed_seconds', 0)}s",
                f"- ETA: {snapshot.get('eta_seconds', 'unknown')}s",
                f"- Message: {snapshot.get('message', '')}",
                (
                    f"- Files: structural {snapshot.get('structural_files_processed', 0)}/"
                    f"{snapshot.get('structural_files_total', 0)}, python {snapshot.get('python_files_processed', 0)}/"
                    f"{snapshot.get('python_files_total', 0)}, java {snapshot.get('java_files_processed', 0)}/"
                    f"{snapshot.get('java_files_total', 0)}"
                ),
                (
                    f"- Stage rows: nodes {snapshot.get('stage_nodes_written', 0)}, "
                    f"edges {snapshot.get('stage_edges_written', 0)}"
                ),
            ]
        )
    output.extend(_spool_summary())
    output.extend(_area_plan_summary())
    if events:
        output.append("- Recent events:")
        for event in events[-lines:]:
            output.append(
                f"  {event.get('updated_at', event.get('timestamp', 'unknown'))} "
                f"{event.get('phase', 'unknown')} {event.get('percent_complete', 0)}% "
                f"{event.get('message', '')}"
            )
    return "\n".join(output)


def watch_progress(interval_seconds: float = 2.0, max_updates: int | None = None) -> int:
    seen: tuple[str | None, str | None] | None = None
    emitted = 0
    while True:
        snapshot = _load_progress_snapshot()
        if snapshot is not None:
            current = (snapshot.get("updated_at"), snapshot.get("phase"))
            if current != seen:
                print(render_progress_tail(lines=5), flush=True)
                print("", flush=True)
                seen = current
                emitted += 1
                if max_updates is not None and emitted >= max_updates:
                    return 0
                if snapshot.get("status") in {"complete", "failed"}:
                    return 0
        else:
            print("Waiting for graph progress to appear...", flush=True)
            emitted += 1
            if max_updates is not None and emitted >= max_updates:
                return 0
        time.sleep(max(0.2, interval_seconds))
