# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from graph_ir import GraphEdge, GraphNode
from utils import get_project_root

PACKAGE_RE = re.compile(r"^\s*package\s+([A-Za-z_][\w\.]*)\s*;", re.MULTILINE)
CLASS_RE = re.compile(r"\b(class|interface|enum|record)\s+([A-Za-z_]\w*)")
METHOD_RE = re.compile(
    r"""
    ^\s*
    (?:(?:public|protected|private|static|final|native|synchronized|abstract|default|strictfp)\s+)*
    [A-Za-z_][\w<>\[\]., ?]*
    \s+
    (?P<name>[A-Za-z_]\w*)
    \s*\(
    [^)]*
    \)
    \s*
    (?:throws\s+[A-Za-z_][\w.,\s]*)?
    \{
    """,
    re.MULTILINE | re.VERBOSE,
)
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
CALL_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "new",
    "throw",
    "super",
    "this",
    "assert",
    "try",
    "synchronized",
}


def _hash_id(*parts: str) -> str:
    digest = hashlib.sha1("::".join(parts).encode()).hexdigest()[:16]
    return digest


def _node_id(kind: str, name: str) -> str:
    return f"{kind}:{_hash_id(kind, name)}"


def _edge_id(kind: str, src_id: str, dst_id: str) -> str:
    return f"{kind}:{_hash_id(kind, src_id, dst_id)}"


def _semantic_source_path() -> Path:
    return Path(__file__).resolve().parents[1] / "graph_tools" / "java_semantic" / "src" / "cicadas" / "graphtools" / "SemanticGraphExtractor.java"


def _semantic_classes_dir(root: Path) -> Path:
    return root / ".cicadas" / "graph" / "tools" / "java-semantic" / "classes"


def _semantic_work_dir(root: Path) -> Path:
    return root / ".cicadas" / "graph" / "tools" / "java-semantic"


def _has_java_toolchain() -> bool:
    return shutil.which("javac") is not None and shutil.which("java") is not None and _semantic_source_path().exists()


def analyzer_status() -> str:
    if _has_java_toolchain():
        return "semantic-ready"
    return "structural"


def analyzer_details(root: Path | None = None) -> dict:
    if root is None:
        root = get_project_root()
    javac_path = shutil.which("javac")
    java_path = shutil.which("java")
    semantic_source = _semantic_source_path()
    semantic_classes = _semantic_classes_dir(root)
    return {
        "mode": analyzer_status(),
        "javac_found": bool(javac_path),
        "javac_path": javac_path,
        "java_found": bool(java_path),
        "java_path": java_path,
        "semantic_source_exists": semantic_source.exists(),
        "semantic_source_path": str(semantic_source),
        "semantic_classes_dir_exists": semantic_classes.exists(),
        "semantic_classes_dir": str(semantic_classes),
    }


@dataclass
class _JavaSymbol:
    node: GraphNode
    simple_name: str
    file_path: str
    is_test_symbol: bool


def _package_name(source: str) -> str:
    match = PACKAGE_RE.search(source)
    return match.group(1) if match else ""


def _class_name(source: str, rel_path: str) -> str:
    match = CLASS_RE.search(source)
    if match:
        return match.group(2)
    return Path(rel_path).stem


def _is_test_file(rel_path: str) -> bool:
    rel_lower = rel_path.lower()
    return "src/test/java/" in rel_lower or rel_lower.startswith("test/") or rel_lower.endswith("test.java")


def _method_body(source: str, start_index: int) -> str:
    brace_index = source.find("{", start_index)
    if brace_index == -1:
        return ""
    depth = 1
    idx = brace_index + 1
    while idx < len(source) and depth > 0:
        char = source[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        idx += 1
    if idx <= brace_index + 1:
        return ""
    return source[brace_index + 1 : idx - 1]


def _extract_java_graph_structural(
    root: Path,
    file_entries: list[dict],
    build_id: str,
    area_lookup: dict[str, str | None],
    progress: Callable[[dict], None] | None = None,
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    discovered: list[_JavaSymbol] = []
    calls_by_symbol: dict[str, list[str]] = defaultdict(list)

    java_file_entries = [entry for entry in file_entries if entry.get("language") == "java" and entry.get("path")]
    total_java_files = len(java_file_entries)
    if progress is not None:
        progress(
            {
                "phase": "java_extraction",
                "message": f"java extraction started ({total_java_files} files)",
                "java_files_total": total_java_files,
                "java_files_processed": 0,
            }
        )

    processed_java_files = 0
    for entry in java_file_entries:
        rel_path = entry.get("path")
        if not rel_path:
            continue
        path = root / rel_path
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            processed_java_files += 1
            if progress is not None and (processed_java_files == total_java_files or processed_java_files % 200 == 0):
                progress(
                    {
                        "phase": "java_extraction",
                        "message": f"java extraction processed {processed_java_files}/{total_java_files} files",
                        "java_files_total": total_java_files,
                        "java_files_processed": processed_java_files,
                    }
                )
            continue

        package = _package_name(source)
        class_name = _class_name(source, rel_path)
        class_symbol_name = f"{package}.{class_name}" if package else class_name
        area_name = area_lookup.get(rel_path)
        is_test_file = _is_test_file(rel_path)

        class_id = _node_id("symbol", f"{rel_path}:{class_symbol_name}")
        class_node = GraphNode(
            node_id=class_id,
            kind="symbol",
            name=class_symbol_name,
            language="java",
            path=rel_path,
            area=area_name,
            build_id=build_id,
            metadata={"symbol_type": "class", "simple_name": class_name, "package": package, "extraction_source": "structural"},
        )
        discovered.append(_JavaSymbol(node=class_node, simple_name=class_name, file_path=rel_path, is_test_symbol=is_test_file))
        file_nodes: list[GraphNode] = [class_node]
        file_id = _node_id("file", rel_path)
        file_edges: list[GraphEdge] = [GraphEdge(edge_id=_edge_id("declares", file_id, class_id), kind="declares", src_id=file_id, dst_id=class_id, build_id=build_id)]

        for method_match in METHOD_RE.finditer(source):
            method_name = method_match.group("name")
            symbol_name = f"{class_symbol_name}#{method_name}"
            symbol_id = _node_id("symbol", f"{rel_path}:{symbol_name}")
            is_test_symbol = is_test_file or method_name.startswith("test")
            symbol_node = GraphNode(
                node_id=symbol_id,
                kind="symbol",
                name=symbol_name,
                language="java",
                path=rel_path,
                area=area_name,
                build_id=build_id,
                metadata={"symbol_type": "method", "simple_name": method_name, "package": package, "extraction_source": "structural"},
            )
            discovered.append(_JavaSymbol(node=symbol_node, simple_name=method_name, file_path=rel_path, is_test_symbol=is_test_symbol))
            file_nodes.append(symbol_node)
            file_edges.append(GraphEdge(edge_id=_edge_id("declares", file_id, symbol_id), kind="declares", src_id=file_id, dst_id=symbol_id, build_id=build_id))

            if is_test_symbol:
                test_id = _node_id("test", f"{rel_path}:{symbol_name}")
                file_nodes.append(
                    GraphNode(
                        node_id=test_id,
                        kind="test",
                        name=symbol_name,
                        language="java",
                        path=rel_path,
                        area=area_name,
                        build_id=build_id,
                        metadata={"source_symbol": symbol_id, "simple_name": method_name, "extraction_source": "structural"},
                    )
                )
                file_edges.append(GraphEdge(edge_id=_edge_id("declares", symbol_id, test_id), kind="declares", src_id=symbol_id, dst_id=test_id, build_id=build_id))

            method_body = _method_body(source, method_match.start())
            for call_match in CALL_RE.finditer(method_body):
                callee_name = call_match.group(1)
                if callee_name in CALL_KEYWORDS:
                    continue
                calls_by_symbol[symbol_id].append(callee_name)

        if emit is not None and (file_nodes or file_edges):
            emit(file_nodes, file_edges)
        else:
            nodes.extend(file_nodes)
            edges.extend(file_edges)

        processed_java_files += 1
        if progress is not None and (processed_java_files == total_java_files or processed_java_files % 200 == 0):
            progress(
                {
                    "phase": "java_extraction",
                    "message": f"java extraction processed {processed_java_files}/{total_java_files} files",
                    "java_files_total": total_java_files,
                    "java_files_processed": processed_java_files,
                }
            )

    if progress is not None:
        progress(
            {
                "phase": "java_relation_resolution",
                "message": "java extraction starting relation resolution",
                "java_files_total": total_java_files,
                "java_files_processed": processed_java_files,
                "java_relation_sources_total": len(calls_by_symbol),
                "java_relation_sources_processed": 0,
            }
        )

    by_simple_name: dict[str, list[_JavaSymbol]] = defaultdict(list)
    symbols_by_id: dict[str, _JavaSymbol] = {}
    test_nodes_by_symbol: dict[str, str] = {}
    for symbol in discovered:
        by_simple_name[symbol.simple_name].append(symbol)
        symbols_by_id[symbol.node.node_id] = symbol
    for node in nodes:
        if node.kind == "test":
            source_symbol = node.metadata.get("source_symbol")
            if source_symbol:
                test_nodes_by_symbol[source_symbol] = node.node_id

    relation_sources_processed = 0
    relation_sources_total = len(calls_by_symbol)
    for source_symbol_id, callees in calls_by_symbol.items():
        source_symbol = symbols_by_id.get(source_symbol_id)
        if source_symbol is None:
            relation_sources_processed += 1
            continue
        for callee_name in callees:
            targets = by_simple_name.get(callee_name, [])
            if len(targets) != 1:
                continue
            target = targets[0]
            relation_edges: list[GraphEdge] = [
                GraphEdge(
                    edge_id=_edge_id("calls", source_symbol_id, target.node.node_id),
                    kind="calls",
                    src_id=source_symbol_id,
                    dst_id=target.node.node_id,
                    build_id=build_id,
                    metadata={"extraction_source": "structural"},
                )
            ]
            if source_symbol.is_test_symbol and source_symbol_id in test_nodes_by_symbol:
                test_node_id = test_nodes_by_symbol[source_symbol_id]
                relation_edges.append(
                    GraphEdge(
                        edge_id=_edge_id("tests", test_node_id, target.node.node_id),
                        kind="tests",
                        src_id=test_node_id,
                        dst_id=target.node.node_id,
                        build_id=build_id,
                        derived=True,
                        metadata={"extraction_source": "structural"},
                    )
                )
            if emit is not None:
                emit([], relation_edges)
            else:
                edges.extend(relation_edges)
        relation_sources_processed += 1
        if progress is not None and (relation_sources_processed == relation_sources_total or relation_sources_processed % 2000 == 0):
            progress(
                {
                    "phase": "java_relation_resolution",
                    "message": f"java relation resolution processed {relation_sources_processed}/{relation_sources_total} sources",
                    "java_files_total": total_java_files,
                    "java_files_processed": processed_java_files,
                    "java_relation_sources_total": relation_sources_total,
                    "java_relation_sources_processed": relation_sources_processed,
                }
            )

    return nodes, edges, {
        "symbols_indexed": len(discovered),
        "java_mode": "structural" if total_java_files else "disabled",
        "java_files_processed": processed_java_files,
    }


def _compile_semantic_extractor(root: Path) -> Path:
    source_file = _semantic_source_path()
    classes_dir = _semantic_classes_dir(root)
    target_class = classes_dir / "cicadas" / "graphtools" / "SemanticGraphExtractor.class"
    classes_dir.mkdir(parents=True, exist_ok=True)

    needs_compile = not target_class.exists() or source_file.stat().st_mtime > target_class.stat().st_mtime
    if not needs_compile:
        return classes_dir

    cmd = ["javac", "-d", str(classes_dir), str(source_file)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return classes_dir


def _source_roots_from_files(root: Path, java_paths: list[str]) -> list[Path]:
    roots: set[Path] = set()
    for rel in java_paths:
        rel_path = Path(rel)
        rel_str = rel_path.as_posix()
        marker = "/src/main/java/"
        test_marker = "/src/test/java/"
        if marker in rel_str:
            before, _, _ = rel_str.partition(marker)
            roots.add((root / before / "src" / "main" / "java").resolve())
        elif test_marker in rel_str:
            before, _, _ = rel_str.partition(test_marker)
            roots.add((root / before / "src" / "test" / "java").resolve())
        else:
            roots.add((root / rel_path.parent).resolve())
    return sorted(roots)


def _source_root_for_file(root: Path, rel_path: str) -> Path:
    roots = _source_roots_from_files(root, [rel_path])
    return roots[0]


def _semantic_batches(root: Path, java_paths: list[str], max_files_per_batch: int = 4000) -> list[tuple[list[str], list[Path]]]:
    batches: list[tuple[list[str], list[Path]]] = []
    current_paths: list[str] = []
    current_roots: list[Path] = []
    current_root_set: set[Path] = set()

    for rel_path in java_paths:
        source_root = _source_root_for_file(root, rel_path)
        if len(current_paths) >= max_files_per_batch:
            batches.append((current_paths, current_roots))
            current_paths = []
            current_roots = []
            current_root_set = set()
        current_paths.append(rel_path)
        if source_root not in current_root_set:
            current_root_set.add(source_root)
            current_roots.append(source_root)

    if current_paths:
        batches.append((current_paths, current_roots))
    return batches


def _write_semantic_manifest(work_dir: Path, payload: dict) -> None:
    (work_dir / "last-run.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _tail_text(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[-limit:]


def _batch_can_reuse(batch_dir: Path, batch_paths: list[str], source_roots: list[Path]) -> bool:
    files_file = batch_dir / "files.txt"
    roots_file = batch_dir / "source-roots.txt"
    output_file = batch_dir / "semantic.tsv"
    if not files_file.exists() or not roots_file.exists() or not output_file.exists():
        return False
    expected_files = "\n".join(batch_paths) + "\n"
    expected_roots = "\n".join(str(path) for path in source_roots) + "\n"
    return (
        files_file.read_text(encoding="utf-8", errors="ignore") == expected_files
        and roots_file.read_text(encoding="utf-8", errors="ignore") == expected_roots
    )


def _run_semantic_extractor(
    root: Path,
    java_paths: list[str],
    progress: Callable[[dict], None] | None = None,
) -> tuple[Path, dict]:
    classes_dir = _compile_semantic_extractor(root)
    work_dir = _semantic_work_dir(root)
    work_dir.mkdir(parents=True, exist_ok=True)
    persisted_output = work_dir / "last-semantic.tsv"
    persisted_output.write_text("", encoding="utf-8")
    batches = _semantic_batches(root, java_paths)
    manifest_batches: list[dict] = []
    quarantined_files: list[dict[str, str]] = []
    completed_files = 0

    def write_manifest(status: str, **extra: object) -> None:
        payload = {
            "status": status,
            "classes_dir": str(classes_dir),
            "batch_count": len(batches),
            "completed_files": completed_files,
            "quarantined_files": quarantined_files,
            "batches": manifest_batches,
            "combined_output": str(persisted_output),
        }
        payload.update(extra)
        _write_semantic_manifest(work_dir, payload)

    def append_output(output_file: Path) -> None:
        if not output_file.exists() or output_file.stat().st_size <= 0:
            return
        with open(persisted_output, "a", encoding="utf-8") as combined, open(output_file, "r", encoding="utf-8") as batch_output:
            shutil.copyfileobj(batch_output, combined)

    def process_batch(batch_name: str, batch_label: str, batch_paths: list[str], source_roots: list[Path]) -> None:
        nonlocal completed_files
        batch_dir = work_dir / batch_name
        batch_dir.mkdir(parents=True, exist_ok=True)
        files_file = batch_dir / "files.txt"
        roots_file = batch_dir / "source-roots.txt"
        output_file = batch_dir / "semantic.tsv"
        stdout_file = batch_dir / "stdout.log"
        stderr_file = batch_dir / "stderr.log"

        files_file.write_text("\n".join(batch_paths) + "\n", encoding="utf-8")
        roots_file.write_text("\n".join(str(path) for path in source_roots) + "\n", encoding="utf-8")

        batch_record = {
            "batch_name": batch_name,
            "batch_label": batch_label,
            "file_count": len(batch_paths),
            "source_roots": [str(path) for path in source_roots],
            "stdout_log": str(stdout_file),
            "stderr_log": str(stderr_file),
            "output_file": str(output_file),
        }

        if _batch_can_reuse(batch_dir, batch_paths, source_roots):
            batch_record["returncode"] = 0
            batch_record["reused"] = True
            batch_record["status"] = "complete"
            manifest_batches.append(batch_record)
            append_output(output_file)
            completed_files += len(batch_paths)
            if progress is not None:
                progress(
                    {
                        "phase": "java_semantic_enrichment",
                        "message": f"java semantic enrichment reused {batch_label} ({len(batch_paths)} files)",
                        "java_files_total": len(java_paths),
                        "java_files_processed": completed_files,
                    }
                )
            write_manifest("running")
            return

        absolute_files = [str((root / rel).resolve()) for rel in batch_paths]
        cmd = [
            "java",
            "-cp",
            str(classes_dir),
            "cicadas.graphtools.SemanticGraphExtractor",
            "--root",
            str(root.resolve()),
            "--output",
            str(output_file),
            "--files-file",
            str(files_file),
            "--source-roots-file",
            str(roots_file),
        ]
        if progress is not None:
            progress(
                {
                    "phase": "java_semantic_enrichment",
                    "message": f"java semantic enrichment {batch_label} ({len(batch_paths)} files)",
                    "java_files_total": len(java_paths),
                    "java_files_processed": completed_files,
                }
            )
        (batch_dir / "files-absolute.txt").write_text("\n".join(absolute_files) + "\n", encoding="utf-8")
        with open(stdout_file, "w", encoding="utf-8") as stdout_handle, open(stderr_file, "w", encoding="utf-8") as stderr_handle:
            files_file.write_text("\n".join(absolute_files) + "\n", encoding="utf-8")
            completed = subprocess.run(cmd, check=False, stdout=stdout_handle, stderr=stderr_handle, text=True)
        files_file.write_text("\n".join(batch_paths) + "\n", encoding="utf-8")

        batch_record["returncode"] = completed.returncode
        batch_record["reused"] = False

        if completed.returncode == 0:
            batch_record["status"] = "complete"
            manifest_batches.append(batch_record)
            append_output(output_file)
            completed_files += len(batch_paths)
            write_manifest("running")
            return

        stderr_tail = _tail_text(stderr_file)
        batch_record["status"] = "failed"
        batch_record["stderr_tail"] = stderr_tail[:1000]
        manifest_batches.append(batch_record)
        write_manifest("running", failed_batch=batch_name, stderr_tail=stderr_tail)

        if len(batch_paths) == 1:
            quarantined_files.append(
                {
                    "path": batch_paths[0],
                    "batch_name": batch_name,
                    "stderr_tail": stderr_tail[:1000],
                }
            )
            if progress is not None:
                progress(
                    {
                        "phase": "java_semantic_enrichment",
                        "message": f"java semantic enrichment quarantined {batch_paths[0]}",
                        "java_files_total": len(java_paths),
                        "java_files_processed": completed_files,
                    }
                )
            write_manifest("running", failed_batch=batch_name, stderr_tail=stderr_tail)
            return

        if progress is not None:
            progress(
                {
                    "phase": "java_semantic_enrichment",
                    "message": f"java semantic enrichment bisecting {batch_label} after failure ({len(batch_paths)} files)",
                    "java_files_total": len(java_paths),
                    "java_files_processed": completed_files,
                }
            )
        midpoint = max(1, len(batch_paths) // 2)
        left_paths = batch_paths[:midpoint]
        right_paths = batch_paths[midpoint:]
        left_roots = _source_roots_from_files(root, left_paths)
        right_roots = _source_roots_from_files(root, right_paths)
        process_batch(f"{batch_name}-a", f"{batch_label}a", left_paths, left_roots)
        process_batch(f"{batch_name}-b", f"{batch_label}b", right_paths, right_roots)

    for batch_index, (batch_paths, source_roots) in enumerate(batches, start=1):
        process_batch(f"batch-{batch_index:04d}", f"batch {batch_index}/{len(batches)}", batch_paths, source_roots)

    final_status = "complete" if not quarantined_files else "partial"
    write_manifest(final_status)
    return persisted_output, {
        "batch_count": len(batches),
        "completed_batches": sum(1 for batch in manifest_batches if batch.get("status") == "complete"),
        "reused_batches": sum(1 for batch in manifest_batches if batch.get("reused")),
        "quarantined_files": len(quarantined_files),
    }


def _parse_semantic_output(
    *,
    output_path: Path,
    build_id: str,
    area_lookup: dict[str, str | None],
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], int]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    symbol_name_to_id: dict[str, str] = {}
    symbol_name_to_is_test: dict[str, bool] = {}
    source_symbol_to_test_node: dict[str, str] = {}

    node_batch: list[GraphNode] = []
    edge_batch: list[GraphEdge] = []
    lines = output_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        if parts[0] == "SYMBOL" and len(parts) >= 9:
            symbol_kind, name, simple_name, rel_path, _line_no, _owner, package_name, is_test_raw = parts[1:9]
            normalized_name = name
            if symbol_kind in {"method", "constructor"}:
                normalized_name = re.sub(r"\([^)]*\)$", "", name)
            area_name = area_lookup.get(rel_path)
            symbol_id = _node_id("symbol", f"{rel_path}:{normalized_name}")
            node = GraphNode(
                node_id=symbol_id,
                kind="symbol",
                name=normalized_name,
                language="java",
                path=rel_path,
                area=area_name,
                build_id=build_id,
                metadata={"symbol_type": symbol_kind, "simple_name": simple_name, "package": package_name, "full_name": name, "extraction_source": "semantic"},
            )
            node_batch.append(node)
            symbol_name_to_id[name] = symbol_id
            symbol_name_to_id[normalized_name] = symbol_id
            is_test_symbol = is_test_raw == "1"
            symbol_name_to_is_test[name] = is_test_symbol
            symbol_name_to_is_test[normalized_name] = is_test_symbol
            file_id = _node_id("file", rel_path)
            edge_batch.append(GraphEdge(edge_id=_edge_id("declares", file_id, symbol_id), kind="declares", src_id=file_id, dst_id=symbol_id, build_id=build_id))
            if is_test_symbol:
                test_id = _node_id("test", f"{rel_path}:{name}")
                node_batch.append(
                    GraphNode(
                        node_id=test_id,
                        kind="test",
                        name=name,
                        language="java",
                        path=rel_path,
                        area=area_name,
                        build_id=build_id,
                        metadata={"source_symbol": symbol_id, "simple_name": simple_name, "extraction_source": "semantic"},
                    )
                )
                edge_batch.append(GraphEdge(edge_id=_edge_id("declares", symbol_id, test_id), kind="declares", src_id=symbol_id, dst_id=test_id, build_id=build_id))
                source_symbol_to_test_node[symbol_id] = test_id
            if emit is not None and (len(node_batch) >= 500 or len(edge_batch) >= 1000):
                emit(node_batch, edge_batch)
                node_batch = []
                edge_batch = []

    if emit is not None and (node_batch or edge_batch):
        emit(node_batch, edge_batch)
        node_batch = []
        edge_batch = []
    else:
        nodes.extend(node_batch)
        edges.extend(edge_batch)

    for line in lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        if parts[0] == "REL" and len(parts) >= 6:
            edge_kind, src_name, dst_name, rel_path, resolved_raw = parts[1:6]
            resolved = resolved_raw == "1"
            src_id = symbol_name_to_id.get(src_name)
            if src_id is None:
                continue

            if edge_kind == "imports":
                dep_id = _node_id("external_dep", dst_name)
                relation_nodes = [
                    GraphNode(
                        node_id=dep_id,
                        kind="external_dep",
                        name=dst_name,
                        language="java",
                        path=rel_path,
                        area=area_lookup.get(rel_path),
                        build_id=build_id,
                        metadata={"extraction_source": "semantic"},
                    )
                ]
                relation_edges = [
                    GraphEdge(
                        edge_id=_edge_id("imports", _node_id("file", rel_path), dep_id),
                        kind="imports",
                        src_id=_node_id("file", rel_path),
                        dst_id=dep_id,
                        build_id=build_id,
                    )
                ]
                if emit is not None:
                    emit(relation_nodes, relation_edges)
                else:
                    nodes.extend(relation_nodes)
                    edges.extend(relation_edges)
                continue

            dst_id = symbol_name_to_id.get(dst_name)
            if dst_id is None:
                if not resolved:
                    continue
                dst_id = _node_id("external_dep", dst_name)
                relation_nodes = [
                    GraphNode(
                        node_id=dst_id,
                        kind="external_dep",
                        name=dst_name,
                        language="java",
                        path=rel_path,
                        area=area_lookup.get(rel_path),
                        build_id=build_id,
                        metadata={"extraction_source": "semantic"},
                    )
                ]
            else:
                relation_nodes = []

            mapped_kind = edge_kind if edge_kind in {"calls", "depends_on", "implements", "imports"} else "references"
            relation_edges = [
                GraphEdge(
                    edge_id=_edge_id(mapped_kind, src_id, dst_id),
                    kind=mapped_kind,  # type: ignore[arg-type]
                    src_id=src_id,
                    dst_id=dst_id,
                    build_id=build_id,
                    derived=not resolved,
                    metadata={"java_rel_path": rel_path, "resolved": resolved, "extraction_source": "semantic"},
                )
            ]
            if mapped_kind == "calls" and symbol_name_to_is_test.get(src_name) and src_id in source_symbol_to_test_node:
                test_id = source_symbol_to_test_node[src_id]
                relation_edges.append(
                    GraphEdge(
                        edge_id=_edge_id("tests", test_id, dst_id),
                        kind="tests",
                        src_id=test_id,
                        dst_id=dst_id,
                        build_id=build_id,
                        derived=True,
                        metadata={"java_rel_path": rel_path, "resolved": resolved, "extraction_source": "semantic"},
                    )
                )
            if emit is not None:
                emit(relation_nodes, relation_edges)
            else:
                nodes.extend(relation_nodes)
                edges.extend(relation_edges)

    if emit is None:
        unique_nodes = {node.node_id: node for node in nodes}
        unique_edges = {edge.edge_id: edge for edge in edges}
        return list(unique_nodes.values()), list(unique_edges.values()), len(symbol_name_to_id)
    return [], [], len(symbol_name_to_id)


def extract_java_graph(
    root: Path,
    file_entries: list[dict],
    build_id: str,
    area_lookup: dict[str, str | None],
    progress: Callable[[dict], None] | None = None,
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    java_paths = [entry.get("path") for entry in file_entries if entry.get("language") == "java" and entry.get("path")]
    total_java_files = len(java_paths)
    if total_java_files == 0:
        return [], [], {"symbols_indexed": 0, "java_mode": "disabled", "java_files_processed": 0}

    if not _has_java_toolchain():
        return _extract_java_graph_structural(root, file_entries, build_id, area_lookup, progress=progress, emit=emit)

    nodes, edges, structural_stats = _extract_java_graph_structural(root, file_entries, build_id, area_lookup, progress=progress, emit=emit)

    if progress is not None:
        progress(
            {
                "phase": "java_semantic_enrichment",
                "message": f"starting java semantic enrichment ({total_java_files} files)",
                "java_files_total": total_java_files,
                "java_files_processed": structural_stats.get("java_files_processed", 0),
            }
        )

    semantic_stats = {"symbols_indexed": 0, "completed_batches": 0, "batch_count": 0, "reused_batches": 0}
    semantic_output = _semantic_work_dir(root) / "last-semantic.tsv"
    try:
        semantic_output, semantic_stats = _run_semantic_extractor(root=root, java_paths=java_paths, progress=progress)
        if progress is not None:
            progress(
                {
                    "phase": "java_semantic_enrichment",
                    "message": "java semantic enrichment completed, parsing output",
                    "java_files_total": total_java_files,
                    "java_files_processed": total_java_files,
                }
            )
        semantic_nodes, semantic_edges, semantic_symbols_indexed = _parse_semantic_output(
            output_path=semantic_output,
            build_id=build_id,
            area_lookup=area_lookup,
            emit=emit,
        )
        nodes.extend(semantic_nodes)
        edges.extend(semantic_edges)
        java_mode = "hybrid" if semantic_stats.get("quarantined_files", 0) else "semantic"
        return nodes, edges, {
            "symbols_indexed": max(structural_stats.get("symbols_indexed", 0), semantic_symbols_indexed),
            "java_mode": java_mode,
            "java_files_processed": total_java_files,
            "java_structural_symbols_indexed": structural_stats.get("symbols_indexed", 0),
            "java_semantic_symbols_indexed": semantic_symbols_indexed,
            "java_semantic_batches_total": semantic_stats.get("batch_count", 0),
            "java_semantic_batches_completed": semantic_stats.get("completed_batches", 0),
            "java_semantic_batches_reused": semantic_stats.get("reused_batches", 0),
            "java_semantic_quarantined_files": semantic_stats.get("quarantined_files", 0),
        }
    except Exception as exc:
        partial_semantic_symbols = 0
        if semantic_output.exists() and semantic_output.stat().st_size > 0:
            semantic_nodes, semantic_edges, partial_semantic_symbols = _parse_semantic_output(
                output_path=semantic_output,
                build_id=build_id,
                area_lookup=area_lookup,
                emit=emit,
            )
            nodes.extend(semantic_nodes)
            edges.extend(semantic_edges)
        if progress is not None:
            message = f"java semantic enrichment failed; retaining structural coverage ({exc})"
            if partial_semantic_symbols:
                message = f"java semantic enrichment partially applied ({partial_semantic_symbols} semantic symbols); structural coverage retained ({exc})"
            progress(
                {
                    "phase": "java_semantic_enrichment",
                    "message": message,
                    "java_files_total": total_java_files,
                    "java_files_processed": total_java_files,
                }
            )
        return nodes, edges, {
            "symbols_indexed": max(structural_stats.get("symbols_indexed", 0), partial_semantic_symbols),
            "java_mode": "hybrid" if partial_semantic_symbols else "structural",
            "java_files_processed": total_java_files,
            "java_structural_symbols_indexed": structural_stats.get("symbols_indexed", 0),
            "java_semantic_symbols_indexed": partial_semantic_symbols,
            "java_semantic_batches_total": semantic_stats.get("batch_count", 0),
            "java_semantic_batches_completed": semantic_stats.get("completed_batches", 0),
            "java_semantic_batches_reused": semantic_stats.get("reused_batches", 0),
            "java_semantic_quarantined_files": semantic_stats.get("quarantined_files", 0),
            "java_semantic_error": str(exc),
        }
