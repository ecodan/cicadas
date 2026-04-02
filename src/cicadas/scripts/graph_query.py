# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from utils import format_graph_status, graph_available, graph_db_path, load_graph_metadata


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(graph_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_file(conn: sqlite3.Connection, target: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM graph_nodes WHERE kind = 'file' AND path = ?", (target,)).fetchone()
    if row is not None:
        return row
    return conn.execute("SELECT * FROM graph_nodes WHERE kind = 'file' AND path LIKE ?", (f"%{target}",)).fetchone()


def _resolve_symbol(conn: sqlite3.Connection, target: str) -> sqlite3.Row | None:
    target_simple = target.split(".")[-1]
    return conn.execute(
        """
        SELECT * FROM graph_nodes
        WHERE kind = 'symbol'
          AND (
            name = ?
            OR json_extract(metadata_json, '$.simple_name') = ?
            OR name LIKE ?
          )
        ORDER BY CASE WHEN name = ? THEN 0 ELSE 1 END, name
        LIMIT 1
        """,
        (target, target_simple, f"%{target}", target),
    ).fetchone()


def _coverage_text() -> str:
    metadata = load_graph_metadata() or {}
    analyzers = metadata.get("analyzers", {})
    return ", ".join(f"{name}={status}" for name, status in sorted(analyzers.items())) or "unknown"


def _header(title: str) -> list[str]:
    metadata = load_graph_metadata() or {}
    return [
        title,
        f"Freshness: {metadata.get('freshness', 'unknown')}",
        f"Coverage: {_coverage_text()}",
    ]


def _missing_graph_message() -> str:
    return "[ERR] Graph support is not initialized for this repo.\n" + format_graph_status()


def query_area(target: str) -> tuple[int, str]:
    if not graph_available():
        return 1, _missing_graph_message()
    with _connect() as conn:
        file_row = _resolve_file(conn, target)
        if file_row:
            lines = _header(f"Owning area for `{target}`")
            lines.append(f"- Area: {file_row['area'] or 'unknown'}")
            lines.append(f"- File: {file_row['path']}")
            return 0, "\n".join(lines)

        symbol_row = _resolve_symbol(conn, target)
        if symbol_row:
            lines = _header(f"Owning area for `{target}`")
            lines.append(f"- Area: {symbol_row['area'] or 'unknown'}")
            lines.append(f"- Symbol: {symbol_row['name']}")
            lines.append(f"- File: {symbol_row['path'] or 'unknown'}")
            return 0, "\n".join(lines)

    return 1, f"[ERR] No graph results found for `{target}`."


def query_tests(target: str) -> tuple[int, str]:
    if not graph_available():
        return 1, _missing_graph_message()
    with _connect() as conn:
        symbol_row = _resolve_symbol(conn, target)
        if symbol_row is None:
            return 1, f"[ERR] No symbol found for `{target}`."
        rows = conn.execute(
            """
            SELECT t.name, t.path
            FROM graph_edges e
            JOIN graph_nodes t ON t.node_id = e.src_id
            WHERE e.kind = 'tests' AND e.dst_id = ?
            ORDER BY t.path, t.name
            """,
            (symbol_row["node_id"],),
        ).fetchall()
        lines = _header(f"Tests for `{target}`")
        if not rows:
            lines.append("- No direct graph-linked tests found.")
            lines.append("- Note: coverage may be structural-only for this target.")
            return 0, "\n".join(lines)
        for row in rows:
            lines.append(f"- {row['name']} ({row['path']})")
        return 0, "\n".join(lines)


def query_neighbors(target: str) -> tuple[int, str]:
    if not graph_available():
        return 1, _missing_graph_message()
    with _connect() as conn:
        file_row = _resolve_file(conn, target)
        symbol_row = None if file_row is not None else _resolve_symbol(conn, target)
        area_name = None
        if file_row is not None:
            area_name = file_row["area"]
        elif symbol_row is not None:
            area_name = symbol_row["area"]
        else:
            area_name = target

        metadata = load_graph_metadata() or {}
        seeded_areas = metadata.get("seeded_areas") or []
        neighbors = [area for area in seeded_areas if area.get("name") != area_name]
        lines = _header(f"Neighbors for `{target}`")
        lines.append(f"- Owning area: {area_name or 'unknown'}")
        if not neighbors:
            lines.append("- No neighboring seeded areas found.")
            return 0, "\n".join(lines)
        for area in neighbors[:5]:
            lines.append(f"- Neighbor: {area['name']} (paths: {', '.join(area.get('paths', []))})")
        lines.append("- Note: neighbor results are currently seeded from canon routing areas.")
        return 0, "\n".join(lines)


def query_callers(target: str) -> tuple[int, str]:
    if not graph_available():
        return 1, _missing_graph_message()
    with _connect() as conn:
        symbol_row = _resolve_symbol(conn, target)
        if symbol_row is None:
            return 1, f"[ERR] No symbol found for `{target}`."
        rows = conn.execute(
            """
            SELECT s.name, s.path
            FROM graph_edges e
            JOIN graph_nodes s ON s.node_id = e.src_id
            WHERE e.kind = 'calls' AND e.dst_id = ?
            ORDER BY s.path, s.name
            """,
            (symbol_row["node_id"],),
        ).fetchall()
        lines = _header(f"Callers of `{target}`")
        if not rows:
            lines.append("- No direct callers found in the current graph build.")
            return 0, "\n".join(lines)
        for row in rows:
            lines.append(f"- {row['name']} ({row['path']})")
        return 0, "\n".join(lines)


def query_callees(target: str) -> tuple[int, str]:
    if not graph_available():
        return 1, _missing_graph_message()
    with _connect() as conn:
        symbol_row = _resolve_symbol(conn, target)
        if symbol_row is None:
            return 1, f"[ERR] No symbol found for `{target}`."
        rows = conn.execute(
            """
            SELECT s.name, s.path
            FROM graph_edges e
            JOIN graph_nodes s ON s.node_id = e.dst_id
            WHERE e.kind = 'calls' AND e.src_id = ?
            ORDER BY s.path, s.name
            """,
            (symbol_row["node_id"],),
        ).fetchall()
        lines = _header(f"Callees of `{target}`")
        if not rows:
            lines.append("- No direct callees found in the current graph build.")
            return 0, "\n".join(lines)
        for row in rows:
            lines.append(f"- {row['name']} ({row['path']})")
        return 0, "\n".join(lines)


def query_signature_impact(target: str) -> tuple[int, str]:
    if not graph_available():
        return 1, _missing_graph_message()
    with _connect() as conn:
        symbol_row = _resolve_symbol(conn, target)
        if symbol_row is None:
            return 1, f"[ERR] No symbol found for `{target}`."
        callers = conn.execute(
            """
            SELECT s.name, s.path
            FROM graph_edges e
            JOIN graph_nodes s ON s.node_id = e.src_id
            WHERE e.kind = 'calls' AND e.dst_id = ?
            ORDER BY s.path, s.name
            """,
            (symbol_row["node_id"],),
        ).fetchall()
        tests = conn.execute(
            """
            SELECT t.name, t.path
            FROM graph_edges e
            JOIN graph_nodes t ON t.node_id = e.src_id
            WHERE e.kind = 'tests' AND e.dst_id = ?
            ORDER BY t.path, t.name
            """,
            (symbol_row["node_id"],),
        ).fetchall()
        area = symbol_row["area"] or "unknown"
        lines = _header(f"Signature impact for `{target}`")
        lines.append(f"- Symbol: {symbol_row['name']} ({symbol_row['path'] or 'unknown'})")
        lines.append(f"- Owning area: {area}")
        lines.append(f"- Direct callers: {len(callers)}")
        for row in callers[:10]:
            lines.append(f"  - {row['name']} ({row['path']})")
        lines.append(f"- Linked tests: {len(tests)}")
        for row in tests[:10]:
            lines.append(f"  - {row['name']} ({row['path']})")
        if not callers and not tests:
            lines.append("- Note: the current graph build has limited semantic coverage for this symbol.")
        return 0, "\n".join(lines)


def query_route(target: str) -> tuple[int, str]:
    if not graph_available():
        return 1, _missing_graph_message()
    metadata = load_graph_metadata() or {}
    seeded_areas = metadata.get("seeded_areas") or []
    lines = _header(f"Route for `{target}`")
    if not seeded_areas:
        lines.append("- No seeded areas are available yet.")
    else:
        for area in seeded_areas[:3]:
            lines.append(f"- Candidate area: {area['name']} (paths: {', '.join(area.get('paths', []))})")
    lines.append("- Note: natural-language routing is heuristic in the current build.")
    return 0, "\n".join(lines)


def dispatch_query(command: str, target: str) -> tuple[int, str]:
    handlers = {
        "area": query_area,
        "neighbors": query_neighbors,
        "tests": query_tests,
        "callers": query_callers,
        "callees": query_callees,
        "signature-impact": query_signature_impact,
        "route": query_route,
    }
    if command not in handlers:
        return 1, f"[ERR] Unsupported graph query command: {command}"
    return handlers[command](target)
