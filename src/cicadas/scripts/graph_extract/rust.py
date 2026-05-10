# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from pathlib import Path

from graph_ir import GraphEdge, GraphNode, fact_metadata
from graph_extract.tree_sitter_adapter import language_capability, load_language
from utils import load_repo_tree

TEST_ATTR_RE = re.compile(
    r"#\[(?:test|tokio::test|rstest|test_case|should_panic|wasm_bindgen_test)\b",
    re.IGNORECASE,
)
MOD_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+([A-Za-z_]\w*)\b", re.MULTILINE)
STRUCT_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?struct\s+([A-Za-z_]\w*)\b", re.MULTILINE)
ENUM_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?enum\s+([A-Za-z_]\w*)\b", re.MULTILINE)
FN_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:const\s+)?(?:unsafe\s+)?fn\s+([A-Za-z_]\w*)\b",
    re.MULTILINE,
)
IMPL_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?impl\b([^{;]*)", re.MULTILINE)
USE_RE = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)


def _hash_id(*parts: str) -> str:
    digest = hashlib.sha1("::".join(parts).encode()).hexdigest()[:16]
    return digest


def _node_id(kind: str, name: str) -> str:
    return f"{kind}:{_hash_id(kind, name)}"


def _edge_id(kind: str, src_id: str, dst_id: str) -> str:
    return f"{kind}:{_hash_id(kind, src_id, dst_id)}"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _is_rust_test_file(rel_path: str) -> bool:
    rel_lower = rel_path.replace("\\", "/").lower()
    return (
        "/tests/" in rel_lower
        or rel_lower.startswith("tests/")
        or rel_lower.startswith("test/")
        or rel_lower.endswith("_test.rs")
        or rel_lower.endswith("tests.rs")
        or rel_lower.endswith("test.rs")
    )


def _window_before(source_bytes: bytes, start_byte: int, width: int = 240) -> str:
    window = source_bytes[max(0, start_byte - width) : start_byte].decode("utf-8", errors="ignore").lower()
    lines = window.splitlines()
    return "\n".join(lines[-4:])


def _is_testish(source_bytes: bytes, rel_path: str, start_byte: int, symbol_name: str) -> bool:
    if _is_rust_test_file(rel_path):
        return True
    if symbol_name.startswith("test") or "test_" in symbol_name.lower():
        return True
    return bool(TEST_ATTR_RE.search(_window_before(source_bytes, start_byte)))


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _impl_display_name(text: str) -> str:
    head = text.split("{", 1)[0].strip()
    return _normalize_whitespace(head.removeprefix("impl").strip()) or "impl"


def _use_display_name(text: str) -> str:
    body = text.strip().removeprefix("use").strip().rstrip(";")
    return _normalize_whitespace(body) or "use"


def _make_symbol(
    *,
    file_nodes: list[GraphNode],
    file_edges: list[GraphEdge],
    discovered: list[dict],
    file_id: str,
    rel_path: str,
    qualified_name: str,
    simple_name: str,
    kind: str,
    symbol_type: str,
    area_name: str | None,
    build_id: str,
    extraction_source: str,
    is_test_symbol: bool = False,
) -> str:
    symbol_id = _node_id("symbol", f"{rel_path}:{qualified_name}")
    fact_source = "tree-sitter" if extraction_source == "tree-sitter" else "fallback-structural"
    confidence = "high" if fact_source == "tree-sitter" else "medium"
    symbol_node = GraphNode(
        node_id=symbol_id,
        kind="symbol",
        name=qualified_name,
        language="rust",
        path=rel_path,
        area=area_name,
        build_id=build_id,
        metadata=fact_metadata(fact_source, confidence, analyzer=f"rust-{extraction_source}", symbol_type=symbol_type, simple_name=simple_name),
    )
    file_nodes.append(symbol_node)
    file_edges.append(
        GraphEdge(
            edge_id=_edge_id("declares", file_id, symbol_id),
            kind="declares",
            src_id=file_id,
            dst_id=symbol_id,
            build_id=build_id,
            metadata=fact_metadata(fact_source, confidence, analyzer=f"rust-{extraction_source}"),
        )
    )
    discovered.append(
        {
            "node_id": symbol_id,
            "simple_name": simple_name,
            "file_path": rel_path,
            "is_test_symbol": is_test_symbol,
            "kind": kind,
        }
    )
    if is_test_symbol:
        test_id = _node_id("test", f"{rel_path}:{qualified_name}")
        file_nodes.append(
            GraphNode(
                node_id=test_id,
                kind="test",
                name=qualified_name,
                language="rust",
                path=rel_path,
                area=area_name,
                build_id=build_id,
                metadata=fact_metadata(fact_source, confidence, analyzer=f"rust-{extraction_source}", source_symbol=symbol_id, simple_name=simple_name),
            )
        )
        file_edges.append(
            GraphEdge(
                edge_id=_edge_id("declares", symbol_id, test_id),
                kind="declares",
                src_id=symbol_id,
                dst_id=test_id,
                build_id=build_id,
                metadata=fact_metadata(fact_source, confidence, analyzer=f"rust-{extraction_source}"),
            )
        )
    return symbol_id


def _rust_repo_file_count() -> int:
    repo_tree = load_repo_tree() or []
    return sum(1 for entry in repo_tree if entry.get("kind") == "file" and entry.get("language") == "rust" and entry.get("path"))


def analyzer_capability() -> dict:
    tree_sitter_capability = language_capability("rust")
    rust_files_total = _rust_repo_file_count()
    if rust_files_total == 0:
        mode = "disabled"
    elif tree_sitter_capability.get("available"):
        mode = "tree-sitter"
    else:
        mode = "fallback"
    detail = tree_sitter_capability.get("detail") or "rust structural fallback is available"
    if rust_files_total == 0:
        detail = f"{detail}; no Rust files discovered"
    return {
        "available": bool(tree_sitter_capability.get("available")),
        "package": tree_sitter_capability.get("package"),
        "grammar": tree_sitter_capability.get("grammar"),
        "mode": mode,
        "detail": detail,
        "rust_files_total": rust_files_total,
    }


def analyzer_status() -> str:
    return str(analyzer_capability().get("mode", "unavailable"))


def _ts_parser_and_capability() -> tuple[object | None, dict]:
    language_object, capability = load_language("rust")
    if language_object is None:
        return None, capability
    try:
        import tree_sitter  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - metadata path
        return None, {
            "available": False,
            "package": capability.get("package"),
            "grammar": capability.get("grammar"),
            "mode": "unavailable",
            "detail": f"tree_sitter import failed after grammar lookup: {exc.__class__.__name__}: {exc}",
        }

    parser = tree_sitter.Parser()
    try:
        if hasattr(parser, "set_language"):
            parser.set_language(language_object)
        else:
            parser.language = language_object
    except Exception as exc:  # pragma: no cover - metadata path
        return None, {
            "available": False,
            "package": capability.get("package"),
            "grammar": capability.get("grammar"),
            "mode": "unavailable",
            "detail": f"tree_sitter parser setup failed: {exc.__class__.__name__}: {exc}",
        }
    return parser, capability


def _ts_text(source_bytes: bytes, node: object) -> str:
    start = getattr(node, "start_byte", None)
    end = getattr(node, "end_byte", None)
    if start is None or end is None:
        return ""
    return source_bytes[start:end].decode("utf-8", errors="ignore").strip()


def _ts_field_text(source_bytes: bytes, node: object, field_name: str) -> str:
    child = getattr(node, "child_by_field_name", lambda _name: None)(field_name)
    if child is None:
        return ""
    return _ts_text(source_bytes, child)


def _extract_from_tree_sitter(
    *,
    root: Path,
    file_entries: list[dict],
    build_id: str,
    area_lookup: dict[str, str | None],
    progress: Callable[[dict], None] | None = None,
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    parser, capability = _ts_parser_and_capability()
    if parser is None:
        return [], [], {
            "rust_mode": "fallback" if file_entries else "disabled",
            "rust_files_processed": 0,
            "symbols_indexed": 0,
            "capability": capability,
        }

    rust_entries = [entry for entry in file_entries if entry.get("language") == "rust" and entry.get("path")]
    total_rust_files = len(rust_entries)
    if progress is not None:
        progress(
            {
                "phase": "rust_extraction",
                "message": f"rust extraction started ({total_rust_files} files, tree-sitter)",
                "rust_files_total": total_rust_files,
                "rust_files_processed": 0,
            }
        )

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    discovered: list[dict] = []
    processed_rust_files = 0
    symbols_indexed = 0

    for entry in rust_entries:
        rel_path = entry["path"]
        path = root / rel_path
        area_name = area_lookup.get(rel_path)
        file_id = _node_id("file", rel_path)
        file_nodes: list[GraphNode] = []
        file_edges: list[GraphEdge] = []
        try:
            source_bytes = _read_bytes(path)
        except OSError:
            processed_rust_files += 1
            continue

        try:
            tree = parser.parse(source_bytes)
        except Exception:
            processed_rust_files += 1
            continue

        root_node = getattr(tree, "root_node", None)
        if root_node is None:
            processed_rust_files += 1
            continue

        def visit(node: object, scope: list[str]) -> None:
            node_type = getattr(node, "type", "")
            node_text = _ts_text(source_bytes, node)
            next_scope = scope

            if node_type == "mod_item":
                module_name = _ts_field_text(source_bytes, node, "name") or _normalize_whitespace(node_text.split("{", 1)[0].removeprefix("mod").strip())
                if module_name:
                    qualified = "::".join([*scope, module_name]) if scope else module_name
                    is_test_symbol = _is_testish(source_bytes, rel_path, getattr(node, "start_byte", 0), module_name)
                    _make_symbol(
                        file_nodes=file_nodes,
                        file_edges=file_edges,
                        discovered=discovered,
                        file_id=file_id,
                        rel_path=rel_path,
                        qualified_name=qualified,
                        simple_name=module_name,
                        kind="module",
                        symbol_type="module",
                        area_name=area_name,
                        build_id=build_id,
                        extraction_source="tree-sitter",
                        is_test_symbol=is_test_symbol,
                    )
                    symbols_indexed_local[0] += 1
                    next_scope = [*scope, module_name]
            elif node_type == "struct_item":
                struct_name = _ts_field_text(source_bytes, node, "name") or _normalize_whitespace(node_text.split("{", 1)[0].removeprefix("struct").strip())
                if struct_name:
                    qualified = "::".join([*scope, struct_name]) if scope else struct_name
                    is_test_symbol = _is_testish(source_bytes, rel_path, getattr(node, "start_byte", 0), struct_name)
                    _make_symbol(
                        file_nodes=file_nodes,
                        file_edges=file_edges,
                        discovered=discovered,
                        file_id=file_id,
                        rel_path=rel_path,
                        qualified_name=qualified,
                        simple_name=struct_name,
                        kind="struct",
                        symbol_type="struct",
                        area_name=area_name,
                        build_id=build_id,
                        extraction_source="tree-sitter",
                        is_test_symbol=False,
                    )
                    symbols_indexed_local[0] += 1
            elif node_type == "enum_item":
                enum_name = _ts_field_text(source_bytes, node, "name") or _normalize_whitespace(node_text.split("{", 1)[0].removeprefix("enum").strip())
                if enum_name:
                    qualified = "::".join([*scope, enum_name]) if scope else enum_name
                    is_test_symbol = _is_testish(source_bytes, rel_path, getattr(node, "start_byte", 0), enum_name)
                    _make_symbol(
                        file_nodes=file_nodes,
                        file_edges=file_edges,
                        discovered=discovered,
                        file_id=file_id,
                        rel_path=rel_path,
                        qualified_name=qualified,
                        simple_name=enum_name,
                        kind="enum",
                        symbol_type="enum",
                        area_name=area_name,
                        build_id=build_id,
                        extraction_source="tree-sitter",
                        is_test_symbol=False,
                    )
                    symbols_indexed_local[0] += 1
            elif node_type == "impl_item":
                impl_name = _impl_display_name(node_text)
                if impl_name:
                    qualified = "::".join([*scope, impl_name]) if scope else impl_name
                    _make_symbol(
                        file_nodes=file_nodes,
                        file_edges=file_edges,
                        discovered=discovered,
                        file_id=file_id,
                        rel_path=rel_path,
                        qualified_name=qualified,
                        simple_name=impl_name,
                        kind="impl",
                        symbol_type="impl",
                        area_name=area_name,
                        build_id=build_id,
                        extraction_source="tree-sitter",
                        is_test_symbol=False,
                    )
                    symbols_indexed_local[0] += 1
                    next_scope = [*scope, impl_name]
            elif node_type == "function_item":
                fn_name = _ts_field_text(source_bytes, node, "name") or _normalize_whitespace(node_text.split("(", 1)[0].removeprefix("fn").strip())
                if fn_name:
                    qualified = "::".join([*scope, fn_name]) if scope else fn_name
                    is_test_symbol = _is_testish(source_bytes, rel_path, getattr(node, "start_byte", 0), fn_name)
                    _make_symbol(
                        file_nodes=file_nodes,
                        file_edges=file_edges,
                        discovered=discovered,
                        file_id=file_id,
                        rel_path=rel_path,
                        qualified_name=qualified,
                        simple_name=fn_name,
                        kind="function",
                        symbol_type="function",
                        area_name=area_name,
                        build_id=build_id,
                        extraction_source="tree-sitter",
                        is_test_symbol=is_test_symbol,
                    )
                    symbols_indexed_local[0] += 1
            elif node_type == "use_declaration":
                use_name = _use_display_name(node_text)
                if use_name:
                    qualified = "::".join([*scope, use_name]) if scope else use_name
                    _make_symbol(
                        file_nodes=file_nodes,
                        file_edges=file_edges,
                        discovered=discovered,
                        file_id=file_id,
                        rel_path=rel_path,
                        qualified_name=qualified,
                        simple_name=use_name,
                        kind="use",
                        symbol_type="use",
                        area_name=area_name,
                        build_id=build_id,
                        extraction_source="tree-sitter",
                        is_test_symbol=False,
                    )
                    symbols_indexed_local[0] += 1

            for child in getattr(node, "named_children", []) or []:
                visit(child, next_scope)

        symbols_indexed_local = [0]
        visit(root_node, [])

        if emit is not None and (file_nodes or file_edges):
            emit(file_nodes, file_edges)
        else:
            nodes.extend(file_nodes)
            edges.extend(file_edges)

        symbols_indexed += symbols_indexed_local[0]
        processed_rust_files += 1
        if progress is not None and (processed_rust_files == total_rust_files or processed_rust_files % 200 == 0):
            progress(
                {
                    "phase": "rust_extraction",
                    "message": f"rust extraction processed {processed_rust_files}/{total_rust_files} files (tree-sitter)",
                    "rust_files_total": total_rust_files,
                    "rust_files_processed": processed_rust_files,
                }
            )

    return nodes, edges, {
        "rust_mode": "tree-sitter" if total_rust_files else "disabled",
        "rust_files_processed": processed_rust_files,
        "symbols_indexed": symbols_indexed,
        "capability": capability,
    }


def _extract_from_regex(
    *,
    root: Path,
    file_entries: list[dict],
    build_id: str,
    area_lookup: dict[str, str | None],
    progress: Callable[[dict], None] | None = None,
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
    mode: str = "fallback",
) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    rust_entries = [entry for entry in file_entries if entry.get("language") == "rust" and entry.get("path")]
    total_rust_files = len(rust_entries)
    if progress is not None:
        progress(
            {
                "phase": "rust_extraction",
                "message": f"rust extraction started ({total_rust_files} files, {mode})",
                "rust_files_total": total_rust_files,
                "rust_files_processed": 0,
            }
        )

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    processed_rust_files = 0
    symbols_indexed = 0

    for entry in rust_entries:
        rel_path = entry["path"]
        path = root / rel_path
        area_name = area_lookup.get(rel_path)
        file_id = _node_id("file", rel_path)
        file_nodes: list[GraphNode] = []
        file_edges: list[GraphEdge] = []
        try:
            source_text = _read_text(path)
        except OSError:
            processed_rust_files += 1
            continue

        discovered: list[dict] = []
        seen_offsets: set[tuple[int, int]] = set()

        def record_match(
            match: re.Match[str],
            symbol_type: str,
            name: str,
            *,
            scope: str = "",
            allow_test_node: bool = False,
        ) -> None:
            nonlocal symbols_indexed
            start, end = match.span()
            if (start, end) in seen_offsets:
                return
            seen_offsets.add((start, end))
            qualified = f"{scope}::{name}" if scope else name
            is_test_symbol = allow_test_node and _is_testish(source_text.encode("utf-8", errors="ignore"), rel_path, start, name)
            _make_symbol(
                file_nodes=file_nodes,
                file_edges=file_edges,
                discovered=discovered,
                file_id=file_id,
                rel_path=rel_path,
                qualified_name=qualified,
                simple_name=name,
                kind=symbol_type,
                symbol_type=symbol_type,
                area_name=area_name,
                build_id=build_id,
                extraction_source=mode,
                is_test_symbol=is_test_symbol,
            )
            symbols_indexed += 1

        for match in MOD_RE.finditer(source_text):
            record_match(match, "module", match.group(1), allow_test_node=True)
        for match in STRUCT_RE.finditer(source_text):
            record_match(match, "struct", match.group(1))
        for match in ENUM_RE.finditer(source_text):
            record_match(match, "enum", match.group(1))
        for match in FN_RE.finditer(source_text):
            record_match(match, "function", match.group(1), allow_test_node=True)
        for match in IMPL_RE.finditer(source_text):
            impl_name = _normalize_whitespace(match.group(1).strip())
            if impl_name:
                record_match(match, "impl", _impl_display_name(f"impl {impl_name}"))
        for match in USE_RE.finditer(source_text):
            use_name = _normalize_whitespace(match.group(1).strip())
            if use_name:
                record_match(match, "use", use_name)

        if emit is not None and (file_nodes or file_edges):
            emit(file_nodes, file_edges)
        else:
            nodes.extend(file_nodes)
            edges.extend(file_edges)

        processed_rust_files += 1
        if progress is not None and (processed_rust_files == total_rust_files or processed_rust_files % 200 == 0):
            progress(
                {
                    "phase": "rust_extraction",
                    "message": f"rust extraction processed {processed_rust_files}/{total_rust_files} files ({mode})",
                    "rust_files_total": total_rust_files,
                    "rust_files_processed": processed_rust_files,
                }
            )

    return nodes, edges, {
        "rust_mode": "disabled" if total_rust_files == 0 else mode,
        "rust_files_processed": processed_rust_files,
        "symbols_indexed": symbols_indexed,
        "capability": analyzer_capability(),
    }


def extract_rust_graph(
    root: Path,
    file_entries: list[dict],
    build_id: str,
    area_lookup: dict[str, str | None],
    progress: Callable[[dict], None] | None = None,
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    rust_entries = [entry for entry in file_entries if entry.get("language") == "rust" and entry.get("path")]
    if not rust_entries:
        return [], [], {
            "rust_mode": "disabled",
            "rust_files_processed": 0,
            "symbols_indexed": 0,
            "capability": analyzer_capability(),
        }

    parser, _capability = _ts_parser_and_capability()
    if parser is not None:
        try:
            return _extract_from_tree_sitter(
                root=root,
                file_entries=file_entries,
                build_id=build_id,
                area_lookup=area_lookup,
                progress=progress,
                emit=emit,
            )
        except Exception:
            pass

    return _extract_from_regex(
        root=root,
        file_entries=file_entries,
        build_id=build_id,
        area_lookup=area_lookup,
        progress=progress,
        emit=emit,
        mode="fallback",
    )
