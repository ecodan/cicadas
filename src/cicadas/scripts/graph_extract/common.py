# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from graph_ir import GraphEdge, GraphNode
from graph_extract.javascript import extract_javascript_graph
from graph_extract.java import extract_java_graph
from graph_extract.python import extract_python_graph
from utils import (
    get_project_root,
    load_repo_metadata,
    load_repo_tree,
)


def _hash_id(*parts: str) -> str:
    digest = hashlib.sha1("::".join(parts).encode()).hexdigest()[:16]
    return digest


def _node_id(kind: str, name: str) -> str:
    return f"{kind}:{_hash_id(kind, name)}"


def _edge_id(kind: str, src_id: str, dst_id: str) -> str:
    return f"{kind}:{_hash_id(kind, src_id, dst_id)}"


def _seeded_areas(repo_metadata: dict | None) -> list[dict]:
    candidate_slices = (repo_metadata or {}).get("candidate_slices") or []
    areas = []
    for slice_info in candidate_slices:
        name = slice_info.get("name")
        paths = slice_info.get("paths") or []
        if name and paths:
            areas.append({"name": name, "paths": paths, "source": "candidate_slices"})
    if areas:
        return areas

    scan = (repo_metadata or {}).get("scan", {})
    ownership = scan.get("ownership_zone_candidates") or scan.get("runtime_paths") or []
    return [{"name": path.replace("/", "-"), "paths": [path], "source": "ownership_zone_candidates"} for path in ownership if path]


def _join_segments(segments: list[str]) -> str:
    return "/".join(part for part in segments if part)


def _path_depth(path: str) -> int:
    return len([part for part in path.split("/") if part])


def _area_routing_confidence(*, file_count: int, depth: int) -> str:
    if depth >= 3 and 200 <= file_count <= 8000:
        return "high"
    if depth >= 2 and 50 <= file_count <= 10000:
        return "medium"
    return "low"


def _area_modernity(paths: list[str]) -> str:
    joined = " ".join(paths).lower()
    if any(token in joined for token in ("modern", "next", "react", "frontend", "ui", "webapp", "client")):
        return "modern"
    if any(token in joined for token in ("legacy", "old", "deprecated")):
        return "legacy"
    return "mixed"


def _refine_seeded_areas(file_entries: list[dict], areas: list[dict]) -> list[dict]:
    if not areas:
        return []
    file_paths = [entry.get("path") for entry in file_entries if entry.get("path")]
    refined: list[dict] = []
    seen_names: set[str] = set()

    for area in areas:
        area_paths = area.get("paths") or []
        matching_paths = [
            rel_path
            for rel_path in file_paths
            for prefix in area_paths
            if rel_path == prefix.strip("/") or rel_path.startswith(f"{prefix.strip('/')}/")
        ]
        matching_paths = sorted(set(matching_paths))
        file_count = len(matching_paths)
        depth = max((_path_depth(prefix.strip("/")) for prefix in area_paths if prefix.strip("/")), default=1)
        enriched = dict(area)
        enriched["file_count"] = file_count
        enriched["depth"] = depth
        enriched["routing_confidence"] = _area_routing_confidence(file_count=file_count, depth=depth)
        enriched["modernity"] = _area_modernity(area_paths)
        if enriched["name"] not in seen_names:
            refined.append(enriched)
            seen_names.add(enriched["name"])

        if file_count < 20:
            continue

        child_counts: Counter[str] = Counter()
        for rel_path in matching_paths:
            for prefix in area_paths:
                normalized = prefix.strip("/")
                if rel_path == normalized:
                    continue
                if not rel_path.startswith(f"{normalized}/"):
                    continue
                suffix = rel_path[len(normalized) + 1 :]
                parts = [part for part in suffix.split("/") if part]
                if not parts:
                    continue
                child_prefix = _join_segments([normalized, parts[0]])
                child_counts[child_prefix] += 1

        split_threshold = max(3, min(300, file_count // 5))
        meaningful_children = [child for child, count in child_counts.items() if count >= split_threshold]
        if len(meaningful_children) < 2:
            continue

        for child_prefix in sorted(meaningful_children):
            child_name = child_prefix.replace("/", "-")
            if child_name in seen_names:
                continue
            child_file_count = child_counts[child_prefix]
            child_depth = _path_depth(child_prefix)
            refined.append(
                {
                    "name": child_name,
                    "paths": [child_prefix],
                    "source": f"{area.get('source', 'unknown')}:refined",
                    "parent_area": area.get("name"),
                    "file_count": child_file_count,
                    "depth": child_depth,
                    "routing_confidence": _area_routing_confidence(file_count=child_file_count, depth=child_depth),
                    "modernity": _area_modernity([child_prefix]),
                }
            )
            seen_names.add(child_name)

    return refined


def _area_for_path(rel_path: str, areas: list[dict]) -> str | None:
    best_match: tuple[int, str] | None = None
    for area in areas:
        for prefix in area["paths"]:
            normalized = prefix.strip("/")
            if rel_path == normalized or rel_path.startswith(f"{normalized}/"):
                score = len(normalized)
                if best_match is None or score > best_match[0]:
                    best_match = (score, area["name"])
    if best_match is not None:
        return best_match[1]
    return None


def build_structural_graph(
    build_id: str,
    progress: Callable[[dict], None] | None = None,
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    root = get_project_root()
    repo_metadata = load_repo_metadata()
    repo_tree = load_repo_tree() or []
    file_entries = [entry for entry in repo_tree if entry.get("kind") == "file" and entry.get("path")]
    areas = _refine_seeded_areas(file_entries, _seeded_areas(repo_metadata))
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    total_python_files = sum(1 for entry in file_entries if entry.get("language") == "python")
    total_javascript_files = sum(1 for entry in file_entries if entry.get("language") in {"javascript", "typescript"})
    total_java_files = sum(1 for entry in file_entries if entry.get("language") == "java")

    repo_name = root.name
    repo_id = _node_id("repo", repo_name)
    nodes.append(GraphNode(node_id=repo_id, kind="repo", name=repo_name, build_id=build_id, metadata={"root": str(root)}))
    if progress is not None:
        progress(
            {
                "phase": "inventory",
                "message": f"loaded repo inventory ({len(repo_tree)} entries)",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": 0,
                "python_files_total": total_python_files,
                "python_files_processed": 0,
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": 0,
                "java_files_total": total_java_files,
                "java_files_processed": 0,
            }
        )

    area_ids: dict[str, str] = {}
    for area in areas:
        area_id = _node_id("area", area["name"])
        area_ids[area["name"]] = area_id
        nodes.append(
            GraphNode(
                node_id=area_id,
                kind="area",
                name=area["name"],
                build_id=build_id,
                metadata={
                    "paths": area["paths"],
                    "source": area["source"],
                    "file_count": area.get("file_count", 0),
                    "routing_confidence": area.get("routing_confidence", "low"),
                    "modernity": area.get("modernity", "mixed"),
                    "parent_area": area.get("parent_area"),
                },
            )
        )
        edges.append(GraphEdge(edge_id=_edge_id("contains", repo_id, area_id), kind="contains", src_id=repo_id, dst_id=area_id, build_id=build_id))
    if emit is not None and (nodes or edges):
        emit(nodes, edges)
        nodes = []
        edges = []
    if progress is not None:
        progress(
            {
                "phase": "inventory",
                "message": f"seeded {len(areas)} areas",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": 0,
                "python_files_total": total_python_files,
                "python_files_processed": 0,
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": 0,
                "java_files_total": total_java_files,
                "java_files_processed": 0,
            }
        )

    file_count = 0
    processed_files = 0
    structural_nodes: list[GraphNode] = []
    structural_edges: list[GraphEdge] = []
    for entry in file_entries:
        rel_path = entry.get("path")
        file_count += 1
        processed_files += 1
        area_name = _area_for_path(rel_path, areas)
        file_id = _node_id("file", rel_path)
        structural_nodes.append(
            GraphNode(
                node_id=file_id,
                kind="file",
                name=Path(rel_path).name,
                language=entry.get("language"),
                path=rel_path,
                area=area_name,
                build_id=build_id,
                metadata={"extension": entry.get("extension"), "summary": entry.get("summary")},
            )
        )
        if area_name and area_name in area_ids:
            area_id = area_ids[area_name]
            structural_edges.append(GraphEdge(edge_id=_edge_id("contains", area_id, file_id), kind="contains", src_id=area_id, dst_id=file_id, build_id=build_id))
            structural_edges.append(GraphEdge(edge_id=_edge_id("owns", area_id, file_id), kind="owns", src_id=area_id, dst_id=file_id, build_id=build_id, derived=True))

        rel_lower = rel_path.lower()
        if "test" in rel_lower or rel_path.startswith("tests/"):
            test_id = _node_id("test", rel_path)
            structural_nodes.append(
                GraphNode(
                    node_id=test_id,
                    kind="test",
                    name=Path(rel_path).stem,
                    language=entry.get("language"),
                    path=rel_path,
                    area=area_name,
                    build_id=build_id,
                    metadata={"source_file": rel_path},
                )
            )
            structural_edges.append(GraphEdge(edge_id=_edge_id("declares", file_id, test_id), kind="declares", src_id=file_id, dst_id=test_id, build_id=build_id))
        if emit is not None and (len(structural_nodes) >= 500 or len(structural_edges) >= 1000):
            emit(structural_nodes, structural_edges)
            structural_nodes = []
            structural_edges = []
        if progress is not None and processed_files % 500 == 0:
            progress(
                {
                    "phase": "structural_index",
                    "message": f"indexed structural file nodes {processed_files}",
                    "repo_entries_total": len(repo_tree),
                    "structural_files_total": len(file_entries),
                    "structural_files_processed": processed_files,
                    "python_files_total": total_python_files,
                    "python_files_processed": 0,
                    "javascript_files_total": total_javascript_files,
                    "javascript_files_processed": 0,
                    "java_files_total": total_java_files,
                    "java_files_processed": 0,
                }
            )
    if emit is not None and (structural_nodes or structural_edges):
        emit(structural_nodes, structural_edges)
        structural_nodes = []
        structural_edges = []
    else:
        nodes.extend(structural_nodes)
        edges.extend(structural_edges)

    if progress is not None:
        progress(
            {
                "phase": "structural_index",
                "message": f"indexed structural file nodes {processed_files}",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": processed_files,
                "python_files_total": total_python_files,
                "python_files_processed": 0,
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": 0,
                "java_files_total": total_java_files,
                "java_files_processed": 0,
            }
        )

    area_lookup = {entry.get("path"): _area_for_path(entry.get("path", ""), areas) for entry in file_entries if entry.get("path")}

    if progress is not None:
        progress(
            {
                "phase": "python_extraction",
                "message": f"starting python semantic extraction ({total_python_files} files)",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": processed_files,
                "python_files_total": total_python_files,
                "python_files_processed": 0,
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": 0,
                "java_files_total": total_java_files,
                "java_files_processed": 0,
            }
        )
    python_nodes, python_edges, python_stats = extract_python_graph(
        root=root,
        file_entries=file_entries,
        build_id=build_id,
        area_lookup=area_lookup,
        progress=progress,
        emit=emit,
    )
    nodes.extend(python_nodes)
    edges.extend(python_edges)
    if progress is not None:
        progress(
            {
                "phase": "python_extraction",
                "message": "python semantic extraction finished "
                f"({python_stats.get('python_files_processed', 0)} files, {python_stats.get('symbols_indexed', 0)} symbols)",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": processed_files,
                "python_files_total": total_python_files,
                "python_files_processed": python_stats.get("python_files_processed", 0),
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": 0,
                "java_files_total": total_java_files,
                "java_files_processed": 0,
                "symbols_indexed": python_stats.get("symbols_indexed", 0),
            }
        )

    if progress is not None:
        progress(
            {
                "phase": "javascript_extraction",
                "message": f"starting javascript extraction ({total_javascript_files} files)",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": processed_files,
                "python_files_total": total_python_files,
                "python_files_processed": python_stats.get("python_files_processed", 0),
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": 0,
                "java_files_total": total_java_files,
                "java_files_processed": 0,
            }
        )
    javascript_nodes, javascript_edges, javascript_stats = extract_javascript_graph(
        root=root,
        file_entries=file_entries,
        build_id=build_id,
        area_lookup=area_lookup,
        progress=progress,
        emit=emit,
    )
    nodes.extend(javascript_nodes)
    edges.extend(javascript_edges)
    if progress is not None:
        progress(
            {
                "phase": "javascript_extraction",
                "message": "javascript extraction finished "
                f"({javascript_stats.get('javascript_files_processed', 0)} files, {javascript_stats.get('symbols_indexed', 0)} symbols)",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": processed_files,
                "python_files_total": total_python_files,
                "python_files_processed": python_stats.get("python_files_processed", 0),
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": javascript_stats.get("javascript_files_processed", 0),
                "java_files_total": total_java_files,
                "java_files_processed": 0,
                "javascript_symbols_indexed": javascript_stats.get("symbols_indexed", 0),
            }
        )

    if progress is not None:
        progress(
            {
                "phase": "java_extraction",
                "message": f"starting java extraction ({total_java_files} files)",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": processed_files,
                "python_files_total": total_python_files,
                "python_files_processed": python_stats.get("python_files_processed", 0),
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": javascript_stats.get("javascript_files_processed", 0),
                "java_files_total": total_java_files,
                "java_files_processed": 0,
            }
        )
    java_nodes, java_edges, java_stats = extract_java_graph(
        root=root,
        file_entries=file_entries,
        build_id=build_id,
        area_lookup=area_lookup,
        progress=progress,
        emit=emit,
    )
    nodes.extend(java_nodes)
    edges.extend(java_edges)
    if progress is not None:
        progress(
            {
                "phase": "java_extraction",
                "message": "java extraction finished "
                f"({java_stats.get('java_files_processed', 0)} files, {java_stats.get('symbols_indexed', 0)} symbols)",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": processed_files,
                "python_files_total": total_python_files,
                "python_files_processed": python_stats.get("python_files_processed", 0),
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": javascript_stats.get("javascript_files_processed", 0),
                "java_files_total": total_java_files,
                "java_files_processed": java_stats.get("java_files_processed", 0),
                "java_symbols_indexed": java_stats.get("symbols_indexed", 0),
            }
        )

    if progress is not None:
        progress(
            {
                "phase": "assembly",
                "message": f"graph assembly finished ({len(nodes)} nodes, {len(edges)} edges before dedupe)",
                "repo_entries_total": len(repo_tree),
                "structural_files_total": len(file_entries),
                "structural_files_processed": processed_files,
                "python_files_total": total_python_files,
                "python_files_processed": python_stats.get("python_files_processed", 0),
                "javascript_files_total": total_javascript_files,
                "javascript_files_processed": javascript_stats.get("javascript_files_processed", 0),
                "java_files_total": total_java_files,
                "java_files_processed": java_stats.get("java_files_processed", 0),
                "nodes_count": len(nodes),
                "edges_count": len(edges),
            }
        )

    return nodes, edges, {
        "indexed_languages": sorted({entry.get("language") for entry in repo_tree if entry.get("kind") == "file" and entry.get("language")}),
        "seeded_areas": [
            {
                "name": area["name"],
                "paths": area["paths"],
                "source": area["source"],
                "file_count": area.get("file_count", 0),
                "routing_confidence": area.get("routing_confidence", "low"),
                "modernity": area.get("modernity", "mixed"),
                "parent_area": area.get("parent_area"),
                "depth": area.get("depth", 1),
            }
            for area in areas
        ],
        "file_count": file_count,
        "python_stats": python_stats,
        "javascript_stats": javascript_stats,
        "java_stats": java_stats,
    }
