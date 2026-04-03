# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from graph_extract.java import analyzer_details as java_analyzer_details
from graph_extract.javascript import analyzer_status as javascript_analyzer_status
from graph_extract.rust import analyzer_status as rust_analyzer_status
from utils import graph_db_path, graph_metadata_path, graph_progress_path, load_graph_metadata


def render_doctor_report() -> str:
    root = Path.cwd()
    metadata = load_graph_metadata() or {}
    java = java_analyzer_details(root)
    lines = [
        "Graph doctor",
        f"- Root: {root}",
        f"- Graph metadata: {'present' if graph_metadata_path().exists() else 'missing'} ({graph_metadata_path()})",
        f"- Graph DB: {'present' if graph_db_path().exists() else 'missing'} ({graph_db_path()})",
        f"- Graph progress file: {'present' if graph_progress_path().exists() else 'missing'} ({graph_progress_path()})",
        f"- Last build ID: {metadata.get('build_id', 'none')}",
        "Analyzers:",
        f"- Python: {metadata.get('analyzers', {}).get('python', 'semantic')}",
        f"- JavaScript: {javascript_analyzer_status()}",
        f"- Rust: {rust_analyzer_status()}",
        f"- Java mode: {java['mode']}",
        f"- Java toolchain: javac={'yes' if java['javac_found'] else 'no'}, java={'yes' if java['java_found'] else 'no'}",
        f"- Java semantic source: {'present' if java['semantic_source_exists'] else 'missing'} ({java['semantic_source_path']})",
        f"- Java semantic classes dir: {'present' if java['semantic_classes_dir_exists'] else 'missing'} ({java['semantic_classes_dir']})",
    ]
    if not java["javac_found"] or not java["java_found"]:
        lines.append("- Note: Java semantic extraction requires both `javac` and `java` on PATH.")
    if not java["semantic_source_exists"]:
        lines.append("- Note: vendored SemanticGraphExtractor.java is missing; Java falls back to structural mode.")
    return "\n".join(lines)
