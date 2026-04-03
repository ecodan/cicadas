# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from utils import get_project_root, graph_usage_path, load_graph_metadata, load_json


def _current_branch(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=root, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return ""


def _parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def detect_work_context() -> dict:
    root = get_project_root()
    branch = _current_branch(root)
    registry = load_json(root / ".cicadas" / "registry.json")

    initiative = None
    work_type = "ad-hoc"
    if branch.startswith("initiative/"):
        initiative = branch.split("/", 1)[1]
        work_type = "initiative"
    elif branch.startswith("feat/"):
        info = registry.get("branches", {}).get(branch, {})
        initiative = info.get("initiative")
        work_type = "initiative" if initiative else "ad-hoc"
    elif branch.startswith("fix/"):
        initiative = branch.split("/", 1)[1]
        work_type = "bug"
    elif branch.startswith("tweak/"):
        initiative = branch.split("/", 1)[1]
        work_type = "tweak"
    elif branch.startswith("skill/"):
        initiative = branch.split("/", 1)[1]
        work_type = "skill"

    return {"initiative": initiative, "work_type": work_type, "branch": branch or None}


def append_usage_entry(
    *,
    command: str,
    query_kind: str,
    target_type: str,
    operation_name: str,
    end_to_end_ms: int,
    graph_query_ms: int | None = None,
    result_count: int = 0,
    usefulness_tags: list[str] | None = None,
    metadata: dict | None = None,
) -> None:
    path = graph_usage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    graph_meta = load_graph_metadata() or {}
    work = detect_work_context()
    entry = {
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "build_id": graph_meta.get("build_id"),
        "initiative": work["initiative"],
        "work_type": work["work_type"],
        "branch": work["branch"],
        "command": command,
        "query_kind": query_kind,
        "target_type": target_type,
        "operation_name": operation_name,
        "call_duration_ms": graph_query_ms if graph_query_ms is not None else end_to_end_ms,
        "end_to_end_ms": end_to_end_ms,
        "graph_query_ms": graph_query_ms,
        "result_count": result_count,
        "freshness": graph_meta.get("freshness", "unknown"),
        "coverage": graph_meta.get("analyzers", {}),
        "usefulness_tags": usefulness_tags or [],
        "metadata": metadata or {},
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True))
        f.write("\n")


def load_usage_entries() -> list[dict]:
    path = graph_usage_path()
    if not path.exists():
        return []

    entries: list[dict] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            entries.append({"corrupt": True, "raw": line, "lineno": lineno})
    return entries


def _filtered_entries(initiative: str | None = None, since: str | None = None) -> tuple[list[dict], int]:
    entries = load_usage_entries()
    corrupt_count = sum(1 for entry in entries if entry.get("corrupt"))
    valid_entries = [entry for entry in entries if not entry.get("corrupt")]

    if initiative is not None:
        valid_entries = [entry for entry in valid_entries if entry.get("initiative") == initiative]

    since_dt = _parse_iso8601(since)
    if since_dt is not None:
        filtered: list[dict] = []
        for entry in valid_entries:
            entry_dt = _parse_iso8601(entry.get("timestamp"))
            if entry_dt is not None and entry_dt >= since_dt:
                filtered.append(entry)
        valid_entries = filtered

    return valid_entries, corrupt_count


def _group_entries(entries: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        grouped[entry.get("query_kind", "unknown")].append(entry)
    return grouped


def _avg(items: list[dict], field: str) -> int:
    values = [item.get(field) for item in items if isinstance(item.get(field), int | float)]
    if not values:
        return 0
    return round(sum(values) / len(values))


def render_usage_report(initiative: str | None = None, since: str | None = None, view: str = "table") -> str:
    entries, corrupt_count = _filtered_entries(initiative=initiative, since=since)
    grouped = _group_entries(entries)

    if view == "json":
        return json.dumps(
            {
                "initiative": initiative,
                "since": since,
                "corrupt_entries": corrupt_count,
                "entries": entries,
            },
            indent=2,
        )

    if view == "html":
        rows = []
        for query_kind, items in sorted(grouped.items()):
            rows.append(
                "<tr>"
                f"<td>{query_kind}</td>"
                f"<td>{len(items)}</td>"
                f"<td>{_avg(items, 'call_duration_ms')}</td>"
                f"<td>{_avg(items, 'end_to_end_ms')}</td>"
                f"<td>{_avg(items, 'graph_query_ms')}</td>"
                "</tr>"
            )
        body = "".join(rows) or "<tr><td colspan='5'>No graph usage recorded yet.</td></tr>"
        scope = []
        if initiative:
            scope.append(f"initiative={initiative}")
        if since:
            scope.append(f"since={since}")
        scope_text = ", ".join(scope) if scope else "all"
        return (
            "<html><body><h1>Graph Usage</h1>"
            f"<p>Scope: {scope_text}</p>"
            f"<p>Corrupt entries ignored: {corrupt_count}</p>"
            "<table><thead><tr><th>Query</th><th>Count</th><th>Avg call duration ms</th><th>Avg end-to-end ms</th><th>Avg graph query ms</th></tr></thead>"
            f"<tbody>{body}</tbody></table></body></html>"
        )

    if not entries:
        if corrupt_count:
            return f"No graph usage recorded yet. Corrupt entries ignored: {corrupt_count}"
        return "No graph usage recorded yet."

    lines = ["Graph usage summary"]
    if initiative:
        lines.append(f"Initiative: {initiative}")
    if since:
        lines.append(f"Since: {since}")
    lines.append(f"Entries: {len(entries)}")
    if corrupt_count:
        lines.append(f"Corrupt entries ignored: {corrupt_count}")
    for query_kind, items in sorted(grouped.items()):
        avg_call_duration_ms = _avg(items, "call_duration_ms")
        avg_end_to_end_ms = _avg(items, "end_to_end_ms")
        avg_graph_query_ms = _avg(items, "graph_query_ms")
        lines.append(
            f"- {query_kind}: count={len(items)}, "
            f"avg_call_duration_ms={avg_call_duration_ms}, "
            f"avg_end_to_end_ms={avg_end_to_end_ms}, "
            f"avg_graph_query_ms={avg_graph_query_ms}"
        )
    return "\n".join(lines)
