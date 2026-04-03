# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sqlite3
import time
import re
import json

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


def _success_meta(*, result_count: int, usefulness_tags: list[str] | None = None, metadata: dict | None = None) -> dict:
    return {
        "result_count": result_count,
        "usefulness_tags": usefulness_tags or [],
        "metadata": metadata or {},
    }


def _is_test_path(path: str | None) -> bool:
    if not path:
        return False
    rel_lower = path.lower()
    return (
        "src/test/" in rel_lower
        or rel_lower.startswith("test/")
        or rel_lower.startswith("tests/")
        or "/tests/" in rel_lower
        or rel_lower.endswith("test.java")
        or rel_lower.endswith("_test.py")
        or rel_lower.endswith("test.py")
    )


def _filter_test_rows(rows: list[sqlite3.Row], *, exclude_tests: bool) -> list[sqlite3.Row]:
    if not exclude_tests:
        return rows
    return [row for row in rows if not _is_test_path(row["path"])]


def _area_index() -> dict[str, dict]:
    metadata = load_graph_metadata() or {}
    return {area.get("name"): area for area in metadata.get("seeded_areas") or [] if area.get("name")}


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-zA-Z0-9]+", value.lower()) if token}


def _surface_kind(path: str | None, name: str, kind: str) -> str:
    combined = f"{path or ''} {name}".lower()
    if kind == "test" or _is_test_path(path):
        return "test"
    if any(token in combined for token in ("dto", "serializer", "serde", "mapper", "fixture")):
        return "support"
    if any(token in combined for token in ("ui", "frontend", "component", "screen", "view", "page", "dialog", "modal")):
        return "ui_surface"
    if kind == "file" and any((path or "").lower().endswith(ext) for ext in (".tsx", ".jsx", ".vue")):
        return "ui_surface"
    return "operational"


def _row_surface_kind(row: sqlite3.Row) -> str:
    try:
        metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
    except Exception:
        metadata = {}
    if metadata.get("surface_kind"):
        return metadata["surface_kind"]
    return _surface_kind(row["path"], row["name"], row["kind"])


def _search_rank(row: sqlite3.Row, query: str, area_details: dict[str, dict]) -> tuple[int, int, str, str]:
    name = row["name"] or ""
    path = row["path"] or ""
    kind = row["kind"] or ""
    query_lower = query.lower()
    score = 0
    if name.lower() == query_lower or path.lower() == query_lower:
        score += 100
    if query_lower in name.lower():
        score += 40
    if query_lower in path.lower():
        score += 30
    overlap = len(_tokenize(query) & _tokenize(f"{name} {path}"))
    score += overlap * 8

    surface_kind = _row_surface_kind(row)
    if surface_kind == "ui_surface":
        score += 18
    elif surface_kind == "operational":
        score += 10
    elif surface_kind == "support":
        score -= 8
    elif surface_kind == "test":
        score -= 20

    area = area_details.get(row["area"] or "", {})
    if area.get("modernity") == "modern":
        score += 12
    elif area.get("modernity") == "legacy":
        score -= 8
    if area.get("routing_confidence") == "high":
        score += 8
    elif area.get("routing_confidence") == "low":
        score -= 4

    return score, 0 if kind == "entrypoint" else 1, path, name


def _route_rank(area: dict, query: str) -> tuple[int, int, str]:
    name = area.get("name", "")
    paths = " ".join(area.get("paths", []))
    score = 0
    overlap = len(_tokenize(query) & _tokenize(f"{name} {paths}"))
    score += overlap * 10
    if area.get("modernity") == "modern":
        score += 8
    elif area.get("modernity") == "legacy":
        score -= 6
    confidence = area.get("routing_confidence", "low")
    if confidence == "high":
        score += 12
    elif confidence == "medium":
        score += 6
    file_count = int(area.get("file_count", 0) or 0)
    if 1000 <= file_count <= 8000:
        score += 10
    elif 200 <= file_count < 1000:
        score += 6
    elif file_count > 10000:
        score -= 8
    return score, int(area.get("depth", 1) or 1) * -1, name


def query_area(target: str, *, exclude_tests: bool = False) -> tuple[int, str, dict]:
    if not graph_available():
        return 1, _missing_graph_message(), _success_meta(result_count=0, usefulness_tags=["graph-unavailable"], metadata={"target": target})

    with _connect() as conn:
        file_row = _resolve_file(conn, target)
        if file_row:
            lines = _header(f"Owning area for `{target}`")
            lines.append(f"- Area: {file_row['area'] or 'unknown'}")
            lines.append(f"- File: {file_row['path']}")
            area = _area_index().get(file_row["area"] or "", {})
            if area:
                lines.append(f"- Confidence: {area.get('routing_confidence', 'low')}")
                lines.append(f"- Modernity: {area.get('modernity', 'mixed')}")
            return 0, "\n".join(lines), _success_meta(
                result_count=1,
                usefulness_tags=["helped-route"],
                metadata={"target": target, "top_area": file_row["area"], "exclude_tests": exclude_tests},
            )

        symbol_row = _resolve_symbol(conn, target)
        if symbol_row:
            lines = _header(f"Owning area for `{target}`")
            lines.append(f"- Area: {symbol_row['area'] or 'unknown'}")
            lines.append(f"- Symbol: {symbol_row['name']}")
            lines.append(f"- File: {symbol_row['path'] or 'unknown'}")
            area = _area_index().get(symbol_row["area"] or "", {})
            if area:
                lines.append(f"- Confidence: {area.get('routing_confidence', 'low')}")
                lines.append(f"- Modernity: {area.get('modernity', 'mixed')}")
            return 0, "\n".join(lines), _success_meta(
                result_count=1,
                usefulness_tags=["helped-route"],
                metadata={"target": target, "top_area": symbol_row["area"], "exclude_tests": exclude_tests},
            )

    return 1, f"[ERR] No graph results found for `{target}`.", _success_meta(result_count=0, metadata={"target": target, "exclude_tests": exclude_tests})


def query_tests(target: str, *, exclude_tests: bool = False) -> tuple[int, str, dict]:
    if not graph_available():
        return 1, _missing_graph_message(), _success_meta(result_count=0, usefulness_tags=["graph-unavailable"], metadata={"target": target})

    with _connect() as conn:
        symbol_row = _resolve_symbol(conn, target)
        if symbol_row is None:
            return 1, f"[ERR] No symbol found for `{target}`.", _success_meta(result_count=0, metadata={"target": target, "exclude_tests": exclude_tests})

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
            return 0, "\n".join(lines), _success_meta(result_count=0, metadata={"target": target, "exclude_tests": exclude_tests})

        for row in rows:
            lines.append(f"- {row['name']} ({row['path']})")

        return 0, "\n".join(lines), _success_meta(
            result_count=len(rows),
            usefulness_tags=["helped-find-tests"],
            metadata={"target": target, "top_test": rows[0]["path"], "exclude_tests": exclude_tests},
        )


def query_neighbors(target: str, *, exclude_tests: bool = False) -> tuple[int, str, dict]:
    if not graph_available():
        return 1, _missing_graph_message(), _success_meta(result_count=0, usefulness_tags=["graph-unavailable"], metadata={"target": target})

    with _connect() as conn:
        file_row = _resolve_file(conn, target)
        symbol_row = None if file_row is not None else _resolve_symbol(conn, target)
        if file_row is not None:
            area_name = file_row["area"]
        elif symbol_row is not None:
            area_name = symbol_row["area"]
        else:
            area_name = target

        metadata = load_graph_metadata() or {}
        seeded_areas = metadata.get("seeded_areas") or []
        owning_area = next((area for area in seeded_areas if area.get("name") == area_name), None)
        owning_parent = (owning_area or {}).get("parent_area")
        neighbors = [area for area in seeded_areas if area.get("name") != area_name]
        if owning_parent:
            sibling_neighbors = [area for area in neighbors if area.get("parent_area") == owning_parent]
            if sibling_neighbors:
                neighbors = sibling_neighbors
        neighbors = sorted(
            neighbors,
            key=lambda area: (
                0 if area.get("routing_confidence") == "high" else 1 if area.get("routing_confidence") == "medium" else 2,
                0 if area.get("modernity") == "modern" else 1,
                area.get("name", ""),
            ),
        )
        lines = _header(f"Neighbors for `{target}`")
        lines.append(f"- Owning area: {area_name or 'unknown'}")
        if not neighbors:
            lines.append("- No neighboring seeded areas found.")
            return 0, "\n".join(lines), _success_meta(result_count=0, metadata={"target": target, "top_area": area_name, "exclude_tests": exclude_tests})

        top_neighbors = neighbors[:5]
        for area in top_neighbors:
            lines.append(
                f"- Neighbor: {area['name']} "
                f"(paths: {', '.join(area.get('paths', []))}; confidence: {area.get('routing_confidence', 'low')}; "
                f"files: {area.get('file_count', 0)})"
            )
        lines.append("- Note: neighbor results are currently seeded from canon routing areas.")
        return 0, "\n".join(lines), _success_meta(
            result_count=len(top_neighbors),
            usefulness_tags=["helped-route"],
            metadata={"target": target, "top_area": area_name, "exclude_tests": exclude_tests},
        )


def query_callers(target: str, *, exclude_tests: bool = False) -> tuple[int, str, dict]:
    if not graph_available():
        return 1, _missing_graph_message(), _success_meta(result_count=0, usefulness_tags=["graph-unavailable"], metadata={"target": target})

    with _connect() as conn:
        symbol_row = _resolve_symbol(conn, target)
        if symbol_row is None:
            return 1, f"[ERR] No symbol found for `{target}`.", _success_meta(result_count=0, metadata={"target": target, "exclude_tests": exclude_tests})

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
        rows = _filter_test_rows(rows, exclude_tests=exclude_tests)

        lines = _header(f"Callers of `{target}`")
        if not rows:
            lines.append("- No direct callers found in the current graph build.")
            if exclude_tests:
                lines.append("- Test artifacts were excluded from results.")
            return 0, "\n".join(lines), _success_meta(result_count=0, metadata={"target": target, "exclude_tests": exclude_tests})

        for row in rows:
            lines.append(f"- {row['name']} ({row['path']})")

        return 0, "\n".join(lines), _success_meta(
            result_count=len(rows),
            usefulness_tags=["helped-blast-radius"],
            metadata={"target": target, "exclude_tests": exclude_tests},
        )


def query_callees(target: str, *, exclude_tests: bool = False) -> tuple[int, str, dict]:
    if not graph_available():
        return 1, _missing_graph_message(), _success_meta(result_count=0, usefulness_tags=["graph-unavailable"], metadata={"target": target})

    with _connect() as conn:
        symbol_row = _resolve_symbol(conn, target)
        if symbol_row is None:
            return 1, f"[ERR] No symbol found for `{target}`.", _success_meta(result_count=0, metadata={"target": target, "exclude_tests": exclude_tests})

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
        rows = _filter_test_rows(rows, exclude_tests=exclude_tests)

        lines = _header(f"Callees of `{target}`")
        if not rows:
            lines.append("- No direct callees found in the current graph build.")
            if exclude_tests:
                lines.append("- Test artifacts were excluded from results.")
            return 0, "\n".join(lines), _success_meta(result_count=0, metadata={"target": target, "exclude_tests": exclude_tests})

        for row in rows:
            lines.append(f"- {row['name']} ({row['path']})")

        return 0, "\n".join(lines), _success_meta(result_count=len(rows), metadata={"target": target, "exclude_tests": exclude_tests})


def query_signature_impact(target: str, *, exclude_tests: bool = False) -> tuple[int, str, dict]:
    if not graph_available():
        return 1, _missing_graph_message(), _success_meta(result_count=0, usefulness_tags=["graph-unavailable"], metadata={"target": target})

    with _connect() as conn:
        symbol_row = _resolve_symbol(conn, target)
        if symbol_row is None:
            return 1, f"[ERR] No symbol found for `{target}`.", _success_meta(result_count=0, metadata={"target": target, "exclude_tests": exclude_tests})

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
        callers = _filter_test_rows(callers, exclude_tests=exclude_tests)
        if exclude_tests:
            tests = []
        area = symbol_row["area"] or "unknown"
        lines = _header(f"Signature impact for `{target}`")
        lines.append(f"- Symbol: {symbol_row['name']} ({symbol_row['path'] or 'unknown'})")
        lines.append(f"- Owning area: {area}")
        lines.append(f"- Direct callers: {len(callers)}")
        for row in callers[:10]:
            lines.append(f"- Caller: {row['name']} ({row['path']})")
        lines.append(f"- Linked tests: {len(tests)}")
        for row in tests[:10]:
            lines.append(f"- Test: {row['name']} ({row['path']})")
        if exclude_tests:
            lines.append("- Test artifacts were excluded from this impact view.")
        if not callers and not tests:
            lines.append("- Note: the current graph build has limited semantic coverage for this symbol.")

        return 0, "\n".join(lines), _success_meta(
            result_count=len(callers) + len(tests),
            usefulness_tags=["helped-blast-radius"],
            metadata={"target": target, "top_area": area, "exclude_tests": exclude_tests},
        )


def query_route(target: str, *, exclude_tests: bool = False) -> tuple[int, str, dict]:
    if not graph_available():
        return 1, _missing_graph_message(), _success_meta(result_count=0, usefulness_tags=["graph-unavailable"], metadata={"target": target})

    metadata = load_graph_metadata() or {}
    seeded_areas = metadata.get("seeded_areas") or []
    lines = _header(f"Route for `{target}`")
    if not seeded_areas:
        lines.append("- No seeded areas are available yet.")
        top_area = None
        top_confidence = None
    else:
        ranked_areas = sorted(seeded_areas, key=lambda area: _route_rank(area, target), reverse=True)
        top_area = ranked_areas[0]["name"] if ranked_areas else None
        top_confidence = ranked_areas[0].get("routing_confidence") if ranked_areas else None
        for area in ranked_areas[:5]:
            lines.append(
                f"- Candidate area: {area['name']} "
                f"(paths: {', '.join(area.get('paths', []))}; confidence: {area.get('routing_confidence', 'low')}; "
                f"modernity: {area.get('modernity', 'mixed')}; files: {area.get('file_count', 0)})"
            )
    lines.append("- Note: natural-language routing is heuristic in the current build.")
    return 0, "\n".join(lines), _success_meta(
        result_count=min(len(seeded_areas), 5),
        usefulness_tags=["helped-route"],
        metadata={"target": target, "exclude_tests": exclude_tests, "top_area": top_area, "routing_confidence": top_confidence},
    )


def query_search(
    target: str,
    *,
    exclude_tests: bool = False,
    kinds: list[str] | None = None,
    limit: int = 10,
) -> tuple[int, str, dict]:
    if not graph_available():
        return 1, _missing_graph_message(), _success_meta(result_count=0, usefulness_tags=["graph-unavailable"], metadata={"target": target})

    valid_kinds = tuple(kinds or ["entrypoint", "file", "symbol", "test"])
    predicates = ["(name LIKE ? OR path LIKE ?)"]
    params: list[object] = [f"%{target}%", f"%{target}%"]
    if valid_kinds:
        predicates.append(f"kind IN ({', '.join('?' for _ in valid_kinds)})")
        params.extend(valid_kinds)

    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT kind, name, path, area, metadata_json
            FROM graph_nodes
            WHERE {' AND '.join(predicates)}
            LIMIT 250
            """,
            tuple(params),
        ).fetchall()
    rows = _filter_test_rows(rows, exclude_tests=exclude_tests)
    area_details = _area_index()
    ranked_rows = sorted(rows, key=lambda row: _search_rank(row, target, area_details), reverse=True)[: max(1, limit)]

    lines = _header(f"Search results for `{target}`")
    if not ranked_rows:
        lines.append("- No matching graph nodes found.")
        if exclude_tests:
            lines.append("- Test artifacts were excluded from results.")
        return 0, "\n".join(lines), _success_meta(
            result_count=0,
            metadata={"target": target, "exclude_tests": exclude_tests, "kinds": list(valid_kinds), "limit": limit},
        )

    for row in ranked_rows:
        area = area_details.get(row["area"] or "", {})
        surface_kind = _row_surface_kind(row)
        lines.append(
            f"- {row['kind']}: {row['name']} "
            f"({row['path'] or 'unknown'}; area: {row['area'] or 'unknown'}; "
            f"surface: {surface_kind}; confidence: {area.get('routing_confidence', 'low')}; "
            f"modernity: {area.get('modernity', 'mixed')})"
        )

    return 0, "\n".join(lines), _success_meta(
        result_count=len(ranked_rows),
        usefulness_tags=["helped-route", "helped-search"],
        metadata={
            "target": target,
            "exclude_tests": exclude_tests,
            "kinds": list(valid_kinds),
            "limit": limit,
            "top_kind": ranked_rows[0]["kind"] if ranked_rows else None,
            "top_area": ranked_rows[0]["area"] if ranked_rows else None,
        },
    )


def dispatch_query(
    command: str,
    target: str,
    *,
    exclude_tests: bool = False,
    kinds: list[str] | None = None,
    limit: int = 10,
) -> tuple[int, str, dict]:
    handlers = {
        "area": query_area,
        "neighbors": query_neighbors,
        "tests": query_tests,
        "callers": query_callers,
        "callees": query_callees,
        "signature-impact": query_signature_impact,
        "route": query_route,
        "search": query_search,
    }
    if command not in handlers:
        return 1, f"[ERR] Unsupported graph query command: {command}", _success_meta(result_count=0, metadata={"target": target})

    start = time.perf_counter()
    if command == "search":
        code, output, meta = handlers[command](target, exclude_tests=exclude_tests, kinds=kinds, limit=limit)
    else:
        code, output, meta = handlers[command](target, exclude_tests=exclude_tests)
    meta = dict(meta)
    meta["graph_query_ms"] = round((time.perf_counter() - start) * 1000)
    return code, output, meta
