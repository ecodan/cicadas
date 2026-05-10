# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from pathlib import Path

from graph_ir import GraphEdge, GraphNode, fact_metadata
from graph_extract.tree_sitter_adapter import language_capability, load_language

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


def analyzer_capability() -> dict:
    javascript = language_capability("javascript")
    typescript = language_capability("typescript")
    available = bool(javascript.get("available") or typescript.get("available"))
    return {
        "available": available,
        "mode": "tree-sitter" if available else "fallback-structural",
        "javascript": javascript,
        "typescript": typescript,
    }


def analyzer_status() -> str:
    return str(analyzer_capability().get("mode", "fallback-structural"))


def _tree_sitter_language_for_path(rel_path: str, language: str | None) -> str:
    suffix = Path(rel_path).suffix.lower()
    if suffix == ".tsx":
        return "tsx"
    if suffix == ".ts":
        return "typescript"
    if suffix == ".jsx":
        return "javascript"
    if language == "typescript":
        return "typescript"
    return "javascript"


def _parser_for_language(language_key: str) -> tuple[object | None, dict]:
    language_object, capability = load_language(language_key)
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


def _read_source_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def _read_source_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _ts_text(source_bytes: bytes, node: object) -> str:
    start = getattr(node, "start_byte", None)
    end = getattr(node, "end_byte", None)
    if start is None or end is None:
        return ""
    return source_bytes[start:end].decode("utf-8", errors="ignore").strip()


def _ts_field(node: object, field_name: str) -> object | None:
    return getattr(node, "child_by_field_name", lambda _name: None)(field_name)


def _ts_field_text(source_bytes: bytes, node: object, field_name: str) -> str:
    child = _ts_field(node, field_name)
    if child is None:
        return ""
    return _ts_text(source_bytes, child).strip().strip("'\"`")


def _first_named_child_of_type(node: object, node_types: set[str]) -> object | None:
    for child in getattr(node, "named_children", []) or []:
        if getattr(child, "type", "") in node_types:
            return child
    return None


def _string_node_value(source_bytes: bytes, node: object | None) -> str:
    if node is None:
        return ""
    return _ts_text(source_bytes, node).strip().strip("'\"`")


def _variable_declarator_name(source_bytes: bytes, node: object) -> str:
    name = _ts_field_text(source_bytes, node, "name")
    if name:
        return name
    for child in getattr(node, "named_children", []) or []:
        if getattr(child, "type", "") in {"identifier", "property_identifier"}:
            return _ts_text(source_bytes, child)
    return ""


def _declaration_name(source_bytes: bytes, node: object) -> tuple[str, str] | None:
    node_type = getattr(node, "type", "")
    if node_type in {"function_declaration", "generator_function_declaration"}:
        return _ts_field_text(source_bytes, node, "name"), "function"
    if node_type in {"class_declaration", "abstract_class_declaration"}:
        return _ts_field_text(source_bytes, node, "name"), "class"
    if node_type in {"method_definition", "method_signature", "public_field_definition", "property_signature"}:
        return _ts_field_text(source_bytes, node, "name"), "method"
    if node_type == "variable_declarator":
        name = _variable_declarator_name(source_bytes, node)
        value = _ts_field(node, "value")
        value_type = getattr(value, "type", "") if value is not None else ""
        symbol_type = "class" if value_type == "class" else "function" if value_type in {"arrow_function", "function", "function_expression"} else "constant"
        return name, symbol_type
    return None


def _make_symbol(
    *,
    file_nodes: list[GraphNode],
    file_edges: list[GraphEdge],
    file_id: str,
    rel_path: str,
    symbol_name: str,
    symbol_type: str,
    language: str | None,
    area_name: str | None,
    build_id: str,
    extraction_source: str,
    analyzer: str,
) -> str:
    symbol_id = _node_id("symbol", f"{rel_path}:{symbol_name}")
    confidence = "high" if extraction_source == "tree-sitter" else "medium"
    file_nodes.append(
        GraphNode(
            node_id=symbol_id,
            kind="symbol",
            name=symbol_name,
            language=language,
            path=rel_path,
            area=area_name,
            build_id=build_id,
            metadata={
                **fact_metadata(extraction_source, confidence, analyzer=analyzer),
                "symbol_type": symbol_type,
                "simple_name": symbol_name,
                "surface_kind": "ui_surface" if _is_ui_surface(rel_path, symbol_name) else "operational",
            },
        )
    )
    file_edges.append(
        GraphEdge(
            edge_id=_edge_id("declares", file_id, symbol_id),
            kind="declares",
            src_id=file_id,
            dst_id=symbol_id,
            build_id=build_id,
            metadata=fact_metadata(extraction_source, confidence, analyzer=analyzer),
        )
    )
    if _is_ui_surface(rel_path, symbol_name):
        entrypoint_id = _node_id("entrypoint", f"{rel_path}:{symbol_name}")
        file_nodes.append(
            GraphNode(
                node_id=entrypoint_id,
                kind="entrypoint",
                name=symbol_name,
                language=language,
                path=rel_path,
                area=area_name,
                build_id=build_id,
                metadata=fact_metadata(
                    extraction_source,
                    confidence,
                    analyzer=analyzer,
                    surface_kind="ui_surface",
                    source_symbol=symbol_id,
                ),
            )
        )
        file_edges.append(
            GraphEdge(
                edge_id=_edge_id("enters_at", file_id, entrypoint_id),
                kind="enters_at",
                src_id=file_id,
                dst_id=entrypoint_id,
                build_id=build_id,
                metadata=fact_metadata(extraction_source, confidence, analyzer=analyzer),
            )
        )
        file_edges.append(
            GraphEdge(
                edge_id=_edge_id("declares", symbol_id, entrypoint_id),
                kind="declares",
                src_id=symbol_id,
                dst_id=entrypoint_id,
                build_id=build_id,
                metadata=fact_metadata(extraction_source, confidence, analyzer=analyzer),
            )
        )
    return symbol_id


def _make_external_dep(
    *,
    file_nodes: list[GraphNode],
    file_edges: list[GraphEdge],
    file_id: str,
    rel_path: str,
    imported: str,
    language: str | None,
    area_name: str | None,
    build_id: str,
    extraction_source: str,
    analyzer: str,
) -> None:
    confidence = "high" if extraction_source == "tree-sitter" else "medium"
    dep_id = _node_id("external_dep", imported)
    file_nodes.append(
        GraphNode(
            node_id=dep_id,
            kind="external_dep",
            name=imported,
            language=language,
            path=rel_path,
            area=area_name,
            build_id=build_id,
            metadata=fact_metadata(extraction_source, confidence, analyzer=analyzer, surface_kind="dependency"),
        )
    )
    file_edges.append(
        GraphEdge(
            edge_id=_edge_id("imports", file_id, dep_id),
            kind="imports",
            src_id=file_id,
            dst_id=dep_id,
            build_id=build_id,
            metadata=fact_metadata(extraction_source, confidence, analyzer=analyzer),
        )
    )


def _extract_file_with_tree_sitter(
    *,
    parser: object,
    root: Path,
    entry: dict,
    build_id: str,
    area_name: str | None,
) -> tuple[list[GraphNode], list[GraphEdge], int] | None:
    rel_path = entry["path"]
    path = root / rel_path
    try:
        source_bytes = _read_source_bytes(path)
        tree = parser.parse(source_bytes)
    except Exception:
        return None

    root_node = getattr(tree, "root_node", None)
    if root_node is None:
        return None

    file_id = _node_id("file", rel_path)
    file_nodes: list[GraphNode] = []
    file_edges: list[GraphEdge] = []
    symbols_indexed = 0
    seen_symbols: set[tuple[str, int]] = set()
    seen_imports: set[str] = set()
    language = entry.get("language")
    analyzer = "javascript-tree-sitter"

    def record_symbol(node: object, symbol_name: str, symbol_type: str) -> None:
        nonlocal symbols_indexed
        symbol_name = symbol_name.strip()
        if not symbol_name:
            return
        key = (symbol_name, int(getattr(node, "start_byte", 0) or 0))
        if key in seen_symbols:
            return
        seen_symbols.add(key)
        _make_symbol(
            file_nodes=file_nodes,
            file_edges=file_edges,
            file_id=file_id,
            rel_path=rel_path,
            symbol_name=symbol_name,
            symbol_type=symbol_type,
            language=language,
            area_name=area_name,
            build_id=build_id,
            extraction_source="tree-sitter",
            analyzer=analyzer,
        )
        symbols_indexed += 1

    def record_default_export(node: object) -> None:
        declaration = _first_named_child_of_type(
            node,
            {
                "function_declaration",
                "generator_function_declaration",
                "class_declaration",
                "abstract_class_declaration",
                "identifier",
            },
        )
        export_name = ""
        symbol_type = "default_export"
        if declaration is not None:
            if getattr(declaration, "type", "") == "identifier":
                export_name = _ts_text(source_bytes, declaration)
            else:
                declaration_info = _declaration_name(source_bytes, declaration)
                if declaration_info:
                    export_name, symbol_type = declaration_info
        if not export_name:
            export_name = Path(rel_path).stem
        if _is_ui_surface(rel_path, export_name):
            record_symbol(node, export_name, symbol_type)

    def visit(node: object) -> None:
        node_type = getattr(node, "type", "")
        if node_type in {"import_statement", "export_statement"}:
            source_node = _ts_field(node, "source")
            imported = _string_node_value(source_bytes, source_node)
            if imported and imported not in seen_imports:
                seen_imports.add(imported)
                _make_external_dep(
                    file_nodes=file_nodes,
                    file_edges=file_edges,
                    file_id=file_id,
                    rel_path=rel_path,
                    imported=imported,
                    language=language,
                    area_name=area_name,
                    build_id=build_id,
                    extraction_source="tree-sitter",
                    analyzer=analyzer,
                )
            if node_type == "export_statement" and "default" in _ts_text(source_bytes, node).splitlines()[0][:80]:
                record_default_export(node)

        declaration_info = _declaration_name(source_bytes, node)
        if declaration_info:
            record_symbol(node, declaration_info[0], declaration_info[1])

        for child in getattr(node, "named_children", []) or []:
            visit(child)

    visit(root_node)
    return file_nodes, file_edges, symbols_indexed


def _extract_file_with_regex(
    *,
    root: Path,
    entry: dict,
    build_id: str,
    area_name: str | None,
) -> tuple[list[GraphNode], list[GraphEdge], int] | None:
    rel_path = entry["path"]
    path = root / rel_path
    try:
        source = _read_source_text(path)
    except OSError:
        return None

    file_id = _node_id("file", rel_path)
    file_nodes: list[GraphNode] = []
    file_edges: list[GraphEdge] = []
    language = entry.get("language")
    analyzer = "javascript-regex"
    extraction_source = "fallback-structural"
    symbols_indexed = 0

    seen_symbols: set[str] = set()
    for matcher, symbol_type in ((FUNCTION_RE, "function"), (CLASS_RE, "class"), (CONST_RE, "function")):
        for match in matcher.finditer(source):
            symbol_name = match.group(1)
            if not symbol_name or symbol_name in seen_symbols:
                continue
            seen_symbols.add(symbol_name)
            _make_symbol(
                file_nodes=file_nodes,
                file_edges=file_edges,
                file_id=file_id,
                rel_path=rel_path,
                symbol_name=symbol_name,
                symbol_type=symbol_type,
                language=language,
                area_name=area_name,
                build_id=build_id,
                extraction_source=extraction_source,
                analyzer=analyzer,
            )
            symbols_indexed += 1

    default_match = DEFAULT_EXPORT_RE.search(source)
    if default_match and _is_ui_surface(rel_path, default_match.group(1) or Path(rel_path).stem):
        entrypoint_name = default_match.group(1) or Path(rel_path).stem
        _make_symbol(
            file_nodes=file_nodes,
            file_edges=file_edges,
            file_id=file_id,
            rel_path=rel_path,
            symbol_name=entrypoint_name,
            symbol_type="default_export",
            language=language,
            area_name=area_name,
            build_id=build_id,
            extraction_source=extraction_source,
            analyzer=analyzer,
        )
        symbols_indexed += 1

    imports = sorted(set(IMPORT_RE.findall(source) + EXPORT_FROM_RE.findall(source) + REQUIRE_RE.findall(source)))
    for imported in imports:
        _make_external_dep(
            file_nodes=file_nodes,
            file_edges=file_edges,
            file_id=file_id,
            rel_path=rel_path,
            imported=imported,
            language=language,
            area_name=area_name,
            build_id=build_id,
            extraction_source=extraction_source,
            analyzer=analyzer,
        )

    return file_nodes, file_edges, symbols_indexed


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
    capability = analyzer_capability()
    use_tree_sitter = bool(capability.get("available"))
    parsers: dict[str, object] = {}
    tree_sitter_files = 0
    fallback_files = 0

    if progress is not None:
        progress(
            {
                "phase": "javascript_extraction",
                "message": f"javascript extraction started ({total_js_files} files, {'tree-sitter' if use_tree_sitter else 'fallback-structural'})",
                "javascript_files_total": total_js_files,
                "javascript_files_processed": 0,
            }
        )

    for entry in js_entries:
        rel_path = entry["path"]
        area_name = area_lookup.get(rel_path)
        extracted: tuple[list[GraphNode], list[GraphEdge], int] | None = None
        if use_tree_sitter:
            language_key = _tree_sitter_language_for_path(rel_path, entry.get("language"))
            if language_key not in parsers:
                parser, parser_capability = _parser_for_language(language_key)
                if parser is not None:
                    parsers[language_key] = parser
                else:
                    capability[f"{language_key}_detail"] = parser_capability.get("detail")
            parser = parsers.get(language_key)
            if parser is not None:
                extracted = _extract_file_with_tree_sitter(
                    parser=parser,
                    root=root,
                    entry=entry,
                    build_id=build_id,
                    area_name=area_name,
                )
        if extracted is None:
            extracted = _extract_file_with_regex(root=root, entry=entry, build_id=build_id, area_name=area_name)
            fallback_files += 1
        else:
            tree_sitter_files += 1
        if extracted is None:
            processed_js_files += 1
            continue

        file_nodes, file_edges, file_symbols_indexed = extracted
        symbols_indexed += file_symbols_indexed

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
        "javascript_mode": "tree-sitter" if tree_sitter_files else "fallback-structural" if total_js_files else "disabled",
        "javascript_files_processed": processed_js_files,
        "tree_sitter_files_processed": tree_sitter_files,
        "fallback_files_processed": fallback_files,
        "capability": {
            **capability,
            "tree_sitter_files_processed": tree_sitter_files,
            "fallback_files_processed": fallback_files,
        },
    }
