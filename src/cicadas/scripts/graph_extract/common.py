# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
from pathlib import Path

from graph_ir import GraphEdge, GraphNode
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


def _area_for_path(rel_path: str, areas: list[dict]) -> str | None:
    for area in areas:
        for prefix in area["paths"]:
            normalized = prefix.strip("/")
            if rel_path == normalized or rel_path.startswith(f"{normalized}/"):
                return area["name"]
    return None


def build_structural_graph(build_id: str) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    root = get_project_root()
    repo_metadata = load_repo_metadata()
    repo_tree = load_repo_tree() or []
    areas = _seeded_areas(repo_metadata)
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    repo_name = root.name
    repo_id = _node_id("repo", repo_name)
    nodes.append(GraphNode(node_id=repo_id, kind="repo", name=repo_name, build_id=build_id, metadata={"root": str(root)}))

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
                metadata={"paths": area["paths"], "source": area["source"]},
            )
        )
        edges.append(GraphEdge(edge_id=_edge_id("contains", repo_id, area_id), kind="contains", src_id=repo_id, dst_id=area_id, build_id=build_id))

    file_count = 0
    for entry in repo_tree:
        if entry.get("kind") != "file":
            continue
        rel_path = entry.get("path")
        if not rel_path:
            continue
        file_count += 1
        area_name = _area_for_path(rel_path, areas)
        file_id = _node_id("file", rel_path)
        nodes.append(
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
            edges.append(GraphEdge(edge_id=_edge_id("contains", area_id, file_id), kind="contains", src_id=area_id, dst_id=file_id, build_id=build_id))
            edges.append(GraphEdge(edge_id=_edge_id("owns", area_id, file_id), kind="owns", src_id=area_id, dst_id=file_id, build_id=build_id, derived=True))

        rel_lower = rel_path.lower()
        if "test" in rel_lower or rel_path.startswith("tests/"):
            test_id = _node_id("test", rel_path)
            nodes.append(
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
            edges.append(GraphEdge(edge_id=_edge_id("declares", file_id, test_id), kind="declares", src_id=file_id, dst_id=test_id, build_id=build_id))

    file_entries = [entry for entry in repo_tree if entry.get("kind") == "file"]
    area_lookup = {entry.get("path"): _area_for_path(entry.get("path", ""), areas) for entry in file_entries if entry.get("path")}
    python_nodes, python_edges, python_stats = extract_python_graph(root=root, file_entries=file_entries, build_id=build_id, area_lookup=area_lookup)
    nodes.extend(python_nodes)
    edges.extend(python_edges)

    return nodes, edges, {
        "indexed_languages": sorted({entry.get("language") for entry in repo_tree if entry.get("kind") == "file" and entry.get("language")}),
        "seeded_areas": [{"name": area["name"], "paths": area["paths"], "source": area["source"]} for area in areas],
        "file_count": file_count,
        "python_stats": python_stats,
    }
