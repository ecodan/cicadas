# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
import hashlib
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from graph_ir import GraphEdge, GraphNode


def _hash_id(*parts: str) -> str:
    digest = hashlib.sha1("::".join(parts).encode()).hexdigest()[:16]
    return digest


def _node_id(kind: str, name: str) -> str:
    return f"{kind}:{_hash_id(kind, name)}"


def _edge_id(kind: str, src_id: str, dst_id: str) -> str:
    return f"{kind}:{_hash_id(kind, src_id, dst_id)}"


@dataclass
class _DiscoveredSymbol:
    node: GraphNode
    simple_name: str
    file_path: str
    is_test_symbol: bool


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self, rel_path: str, area: str | None, build_id: str):
        self.rel_path = rel_path
        self.area = area
        self.build_id = build_id
        self.class_stack: list[str] = []
        self.symbols: list[_DiscoveredSymbol] = []
        self.test_nodes: list[GraphNode] = []
        self.declare_edges: list[GraphEdge] = []
        self._current_file_id = _node_id("file", rel_path)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualname = ".".join([*self.class_stack, node.name]) if self.class_stack else node.name
        class_id = _node_id("symbol", f"{self.rel_path}:{qualname}")
        class_node = GraphNode(
            node_id=class_id,
            kind="symbol",
            name=qualname,
            language="python",
            path=self.rel_path,
            area=self.area,
            build_id=self.build_id,
            metadata={"symbol_type": "class", "simple_name": node.name},
        )
        self.symbols.append(_DiscoveredSymbol(node=class_node, simple_name=node.name, file_path=self.rel_path, is_test_symbol=False))
        self.declare_edges.append(GraphEdge(edge_id=_edge_id("declares", self._current_file_id, class_id), kind="declares", src_id=self._current_file_id, dst_id=class_id, build_id=self.build_id))
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualname = ".".join([*self.class_stack, node.name]) if self.class_stack else node.name
        symbol_id = _node_id("symbol", f"{self.rel_path}:{qualname}")
        is_test_symbol = node.name.startswith("test_") or self.rel_path.startswith("tests/")
        symbol_node = GraphNode(
            node_id=symbol_id,
            kind="symbol",
            name=qualname,
            language="python",
            path=self.rel_path,
            area=self.area,
            build_id=self.build_id,
            metadata={"symbol_type": "function", "simple_name": node.name},
        )
        self.symbols.append(_DiscoveredSymbol(node=symbol_node, simple_name=node.name, file_path=self.rel_path, is_test_symbol=is_test_symbol))
        self.declare_edges.append(GraphEdge(edge_id=_edge_id("declares", self._current_file_id, symbol_id), kind="declares", src_id=self._current_file_id, dst_id=symbol_id, build_id=self.build_id))
        if is_test_symbol:
            test_id = _node_id("test", f"{self.rel_path}:{qualname}")
            self.test_nodes.append(
                GraphNode(
                    node_id=test_id,
                    kind="test",
                    name=qualname,
                    language="python",
                    path=self.rel_path,
                    area=self.area,
                    build_id=self.build_id,
                    metadata={"source_symbol": symbol_id, "simple_name": node.name},
                )
            )
            self.declare_edges.append(GraphEdge(edge_id=_edge_id("declares", symbol_id, test_id), kind="declares", src_id=symbol_id, dst_id=test_id, build_id=self.build_id))
        self.generic_visit(node)


class _CallCollector(ast.NodeVisitor):
    def __init__(self):
        self.calls_by_qualname: dict[str, list[str]] = defaultdict(list)
        self._function_stack: list[str] = []
        self._class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualname = ".".join([*self._class_stack, node.name]) if self._class_stack else node.name
        self._function_stack.append(qualname)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if self._function_stack:
            callee = None
            if isinstance(node.func, ast.Name):
                callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee = node.func.attr
            if callee:
                self.calls_by_qualname[self._function_stack[-1]].append(callee)
        self.generic_visit(node)


def extract_python_graph(
    root: Path,
    file_entries: list[dict],
    build_id: str,
    area_lookup: dict[str, str | None],
    progress: Callable[[dict], None] | None = None,
    emit: Callable[[list[GraphNode], list[GraphEdge]], None] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], dict]:
    discovered: list[_DiscoveredSymbol] = []
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    calls_by_symbol: dict[str, list[str]] = {}
    python_file_entries = [entry for entry in file_entries if entry.get("language") == "python" and entry.get("path")]
    total_python_files = len(python_file_entries)

    if progress is not None:
        progress(
            {
                "phase": "python_extraction",
                "message": f"python extraction started ({total_python_files} files)",
                "python_files_processed": 0,
                "python_files_total": total_python_files,
            }
        )

    processed_python_files = 0
    for entry in python_file_entries:
        rel_path = entry.get("path")
        if not rel_path:
            continue
        path = root / rel_path
        try:
            tree = ast.parse(path.read_text())
        except (OSError, SyntaxError):
            processed_python_files += 1
            if progress is not None and (processed_python_files == total_python_files or processed_python_files % 200 == 0):
                progress(
                    {
                        "phase": "python_extraction",
                        "message": f"python extraction processed {processed_python_files}/{total_python_files} files",
                        "python_files_processed": processed_python_files,
                        "python_files_total": total_python_files,
                    }
                )
            continue

        collector = _FunctionCollector(rel_path=rel_path, area=area_lookup.get(rel_path), build_id=build_id)
        collector.visit(tree)
        discovered.extend(collector.symbols)
        node_batch = [item.node for item in collector.symbols]
        node_batch.extend(collector.test_nodes)
        edge_batch = list(collector.declare_edges)
        if emit is not None and (node_batch or edge_batch):
            emit(node_batch, edge_batch)
        else:
            nodes.extend(node_batch)
            edges.extend(edge_batch)

        call_collector = _CallCollector()
        call_collector.visit(tree)
        calls_by_symbol[rel_path] = call_collector.calls_by_qualname
        processed_python_files += 1
        if progress is not None and (processed_python_files == total_python_files or processed_python_files % 200 == 0):
            progress(
                {
                    "phase": "python_extraction",
                    "message": f"python extraction processed {processed_python_files}/{total_python_files} files",
                    "python_files_processed": processed_python_files,
                    "python_files_total": total_python_files,
                }
            )

    by_simple_name: dict[str, list[_DiscoveredSymbol]] = defaultdict(list)
    by_qualified_name: dict[str, _DiscoveredSymbol] = {}
    test_nodes_by_symbol: dict[str, str] = {}
    for item in discovered:
        by_simple_name[item.simple_name].append(item)
        by_qualified_name[item.node.name] = item
    for node in nodes:
        if node.kind == "test":
            source_symbol = node.metadata.get("source_symbol")
            if source_symbol:
                test_nodes_by_symbol[source_symbol] = node.node_id

    for item in discovered:
        edge_batch: list[GraphEdge] = []
        for callee_name in calls_by_symbol.get(item.file_path, {}).get(item.node.name, []):
            targets = by_simple_name.get(callee_name, [])
            if len(targets) != 1:
                continue
            target = targets[0]
            edge_batch.append(
                GraphEdge(
                    edge_id=_edge_id("calls", item.node.node_id, target.node.node_id),
                    kind="calls",
                    src_id=item.node.node_id,
                    dst_id=target.node.node_id,
                    build_id=build_id,
                )
            )
            if item.is_test_symbol and item.node.node_id in test_nodes_by_symbol:
                test_node_id = test_nodes_by_symbol[item.node.node_id]
                edge_batch.append(
                    GraphEdge(
                        edge_id=_edge_id("tests", test_node_id, target.node.node_id),
                        kind="tests",
                        src_id=test_node_id,
                        dst_id=target.node.node_id,
                        build_id=build_id,
                        derived=True,
                    )
                )
        if emit is not None and edge_batch:
            emit([], edge_batch)
        else:
            edges.extend(edge_batch)

    return nodes, edges, {
        "symbols_indexed": len(discovered),
        "python_mode": "semantic" if discovered else "structural",
        "python_files_processed": processed_python_files,
    }
