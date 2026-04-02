# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import UTC, datetime

from graph_extract.common import build_structural_graph
from graph_extract.javascript import analyzer_status as javascript_analyzer_status
from graph_extract.java import analyzer_status as java_analyzer_status
from graph_extract.rust import analyzer_status as rust_analyzer_status
from graph_store import connect_graph, initialize_schema, replace_graph
from scan_repo import run_scan
from utils import graph_db_path, load_graph_metadata, load_repo_metadata, load_repo_tree, save_graph_metadata


def run_graph_build(language_filter: str = "auto", force: bool = False) -> int:
    existing = load_graph_metadata()
    if existing and not force:
        print("[INFO] Existing graph metadata found. Rebuilding because graph builds are explicit and replace derived state.")

    if load_repo_metadata() is None or load_repo_tree() is None:
        run_scan(progress_mode="off")

    build_id = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    nodes, edges, stats = build_structural_graph(build_id)
    conn = connect_graph(graph_db_path())
    try:
        initialize_schema(conn)
        replace_graph(conn, nodes, edges, build_id)
    finally:
        conn.close()

    save_graph_metadata(
        {
            "schema_version": 1,
            "build_id": build_id,
            "generated_at": build_id,
            "freshness": "fresh",
            "languages_requested": language_filter,
            "indexed_languages": stats["indexed_languages"],
            "seeded_areas": stats["seeded_areas"],
            "file_count": stats["file_count"],
            "analyzers": {
                "python": stats.get("python_stats", {}).get("python_mode", "structural"),
                "javascript": javascript_analyzer_status(),
                "java": java_analyzer_status(),
                "rust": rust_analyzer_status(),
            },
            "symbols_indexed": stats.get("python_stats", {}).get("symbols_indexed", 0),
        }
    )

    print(f"[OK]   Graph build complete: {graph_db_path()}")
    print(f"[INFO] Build ID: {build_id}")
    print(f"[INFO] Indexed languages: {', '.join(stats['indexed_languages']) if stats['indexed_languages'] else 'none'}")
    print(f"[INFO] Seeded areas: {len(stats['seeded_areas'])}")
    return 0
