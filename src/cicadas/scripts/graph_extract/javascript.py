# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from pathlib import Path

from graph_ir import GraphEdge, GraphNode

IMPORT_RE = re.compile(r"""import\s+.+?\s+from\s+['"]([^'"]+)['"]""")
EXPORT_FROM_RE = re.compile(r"""export\s+.+?\s+from\s+['"]([^'"]+)['"]""")
REQUIRE_RE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")
FUNCTION_RE = re.compile(r"""^\s*(?:export\s+)?function\s+([A-Za-z_]\w*)\s*\(""", re.MULTILINE)
CLASS_RE = re.compile(r"""^\s*(?:export\s+)?class\s+([A-Za-z_]\w*)\b""", re.MULTILINE)
CONST_RE = re.compile(r"""^\s*(?:export\s+)?const\s+([A-Za-z_]\w*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_]\w*)\s*=>""", re.MULTILINE)
DEFAULT_EXPORT_RE = re.compile(r"""export\s+default\s+(?:function|class)?\s*([A-Za-z_]\w*)?""")


def _hash_id(*parts: str) -> str:
    digest = hashlib.sha1("::".join(parts).encode()).hexdigest()[:16]
    return digest


def _node_id(kind: str, name: str) -> str:
    return f"{kind}:{_hash_id(kind, name)}"


def _edge_id(kind: str, src_id: str, dst_id: str) -> str:
    return f"{kind}:{_hash_id(kind, src_id, dst_id)}"


def _is_ui_surface(rel_path: str, symbol_name: str | None = None) -> bool:
    combined = f"{rel_path} {symbol_name or ''}".lower()
    return any(
        token in combined
        for token in ("component", "screen", "view", "page", "dialog", "modal", "route", "frontend", "ui", "tsx", "jsx")
    )


def analyzer_status() -> str:
    return "structural"


def _read_source_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def extract_javascript_graph(
    root: Path,
    file_entries: list[dict],
    build_id: str,
    area_lookup: dict[str, str | None],
    progress: Callable[[dict], None] | None = None,
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    js_entries = [
        entry
        for entry in file_entries
        if entry.get("language") in {"javascript", "typescript"} and entry.get("path")
    ]
    total_js_files = len(js_entries)
    processed_js_files = 0
    symbols_indexed = 0

    if progress is not None:
        progress(
            {
                "phase": "javascript_extraction",
                "message": f"javascript extraction started ({total_js_files} files)",
                "javascript_files_total": total_js_files,
                "javascript_files_processed": 0,
            }
        )

    for entry in js_entries:
        rel_path = entry["path"]
        area_name = area_lookup.get(rel_path)
        path = root / rel_path
        try:
            source = _read_source_text(path)
        except OSError:
            processed_js_files += 1
            continue

        file_id = _node_id("file", rel_path)
        file_nodes: list[GraphNode] = []
        file_edges: list[GraphEdge] = []

        seen_symbols: set[str] = set()
        for matcher, symbol_type in ((FUNCTION_RE, "function"), (CLASS_RE, "class"), (CONST_RE, "function")):
            for match in matcher.finditer(source):
                symbol_name = match.group(1)
                if not symbol_name or symbol_name in seen_symbols:
                    continue
                seen_symbols.add(symbol_name)
                symbol_id = _node_id("symbol", f"{rel_path}:{symbol_name}")
                file_nodes.append(
                    GraphNode(
                        node_id=symbol_id,
                        kind="symbol",
                        name=symbol_name,
                        language=entry.get("language"),
                        path=rel_path,
                        area=area_name,
                        build_id=build_id,
                        metadata={
                            "symbol_type": symbol_type,
                            "simple_name": symbol_name,
                            "surface_kind": "ui_surface" if _is_ui_surface(rel_path, symbol_name) else "operational",
                        },
                    )
                )
                file_edges.append(GraphEdge(edge_id=_edge_id("declares", file_id, symbol_id), kind="declares", src_id=file_id, dst_id=symbol_id, build_id=build_id))
                symbols_indexed += 1
                if _is_ui_surface(rel_path, symbol_name):
                    entrypoint_id = _node_id("entrypoint", f"{rel_path}:{symbol_name}")
                    file_nodes.append(
                        GraphNode(
                            node_id=entrypoint_id,
                            kind="entrypoint",
                            name=symbol_name,
                            language=entry.get("language"),
                            path=rel_path,
                            area=area_name,
                            build_id=build_id,
                            metadata={"surface_kind": "ui_surface", "source_symbol": symbol_id},
                        )
                    )
                    file_edges.append(GraphEdge(edge_id=_edge_id("enters_at", file_id, entrypoint_id), kind="enters_at", src_id=file_id, dst_id=entrypoint_id, build_id=build_id))
                    file_edges.append(GraphEdge(edge_id=_edge_id("declares", symbol_id, entrypoint_id), kind="declares", src_id=symbol_id, dst_id=entrypoint_id, build_id=build_id))

        default_match = DEFAULT_EXPORT_RE.search(source)
        if default_match and _is_ui_surface(rel_path, default_match.group(1) or Path(rel_path).stem):
            entrypoint_name = default_match.group(1) or Path(rel_path).stem
            entrypoint_id = _node_id("entrypoint", f"{rel_path}:default:{entrypoint_name}")
            file_nodes.append(
                GraphNode(
                    node_id=entrypoint_id,
                    kind="entrypoint",
                    name=entrypoint_name,
                    language=entry.get("language"),
                    path=rel_path,
                    area=area_name,
                    build_id=build_id,
                    metadata={"surface_kind": "ui_surface", "export_kind": "default"},
                )
            )
            file_edges.append(GraphEdge(edge_id=_edge_id("enters_at", file_id, entrypoint_id), kind="enters_at", src_id=file_id, dst_id=entrypoint_id, build_id=build_id))

        imports = sorted(set(IMPORT_RE.findall(source) + EXPORT_FROM_RE.findall(source) + REQUIRE_RE.findall(source)))
        for imported in imports:
            dep_id = _node_id("external_dep", imported)
            file_nodes.append(
                GraphNode(
                    node_id=dep_id,
                    kind="external_dep",
                    name=imported,
                    language=entry.get("language"),
                    path=rel_path,
                    area=area_name,
                    build_id=build_id,
                    metadata={"surface_kind": "dependency"},
                )
            )
            file_edges.append(GraphEdge(edge_id=_edge_id("imports", file_id, dep_id), kind="imports", src_id=file_id, dst_id=dep_id, build_id=build_id))

        if emit is not None and (file_nodes or file_edges):
            emit(file_nodes, file_edges)
        else:
            nodes.extend(file_nodes)
            edges.extend(file_edges)

        processed_js_files += 1
        if progress is not None and (processed_js_files == total_js_files or processed_js_files % 200 == 0):
            progress(
                {
                    "phase": "javascript_extraction",
                    "message": f"javascript extraction processed {processed_js_files}/{total_js_files} files",
                    "javascript_files_total": total_js_files,
                    "javascript_files_processed": processed_js_files,
                }
            )

    return nodes, edges, {
        "symbols_indexed": symbols_indexed,
        "javascript_mode": "structural" if total_js_files else "disabled",
        "javascript_files_processed": processed_js_files,
    }
