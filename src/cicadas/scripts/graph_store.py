# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from graph_ir import GRAPH_SCHEMA_VERSION, GraphEdge, GraphNode


GRAPH_TABLES = ("graph_nodes", "graph_edges", "graph_meta")
STAGE_TABLES = ("graph_nodes_stage", "graph_edges_stage", "graph_meta_stage")


def connect_graph(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS graph_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS graph_nodes (
            node_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            name TEXT NOT NULL,
            language TEXT,
            path TEXT,
            area TEXT,
            build_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS graph_edges (
            edge_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            src_id TEXT NOT NULL,
            dst_id TEXT NOT NULL,
            weight REAL,
            derived INTEGER NOT NULL,
            build_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_graph_nodes_kind ON graph_nodes(kind);
        CREATE INDEX IF NOT EXISTS idx_graph_nodes_path ON graph_nodes(path);
        CREATE INDEX IF NOT EXISTS idx_graph_nodes_area ON graph_nodes(area);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_src_kind ON graph_edges(src_id, kind);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_dst_kind ON graph_edges(dst_id, kind);

        CREATE TABLE IF NOT EXISTS graph_meta_stage (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS graph_nodes_stage (
            node_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            name TEXT NOT NULL,
            language TEXT,
            path TEXT,
            area TEXT,
            build_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS graph_edges_stage (
            edge_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            src_id TEXT NOT NULL,
            dst_id TEXT NOT NULL,
            weight REAL,
            derived INTEGER NOT NULL,
            build_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_graph_nodes_stage_kind ON graph_nodes_stage(kind);
        CREATE INDEX IF NOT EXISTS idx_graph_nodes_stage_path ON graph_nodes_stage(path);
        CREATE INDEX IF NOT EXISTS idx_graph_nodes_stage_area ON graph_nodes_stage(area);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_stage_src_kind ON graph_edges_stage(src_id, kind);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_stage_dst_kind ON graph_edges_stage(dst_id, kind);
        """
    )
    conn.execute(
        "INSERT OR REPLACE INTO graph_meta(key, value) VALUES(?, ?)",
        ("schema_version", str(GRAPH_SCHEMA_VERSION)),
    )
    conn.execute(
        "INSERT OR REPLACE INTO graph_meta_stage(key, value) VALUES(?, ?)",
        ("schema_version", str(GRAPH_SCHEMA_VERSION)),
    )
    conn.commit()


def _dedupe_nodes(nodes: list[GraphNode]) -> list[GraphNode]:
    deduped: dict[str, GraphNode] = {}
    for node in nodes:
        deduped.setdefault(node.node_id, node)
    return list(deduped.values())


def _dedupe_edges(edges: list[GraphEdge]) -> list[GraphEdge]:
    deduped: dict[str, GraphEdge] = {}
    for edge in edges:
        deduped.setdefault(edge.edge_id, edge)
    return list(deduped.values())


def replace_graph(conn: sqlite3.Connection, nodes: list[GraphNode], edges: list[GraphEdge], build_id: str) -> None:
    unique_nodes = _dedupe_nodes(nodes)
    unique_edges = _dedupe_edges(edges)
    conn.execute("DELETE FROM graph_nodes")
    conn.execute("DELETE FROM graph_edges")
    conn.executemany(
        """
        INSERT INTO graph_nodes(node_id, kind, name, language, path, area, build_id, metadata_json)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                node.node_id,
                node.kind,
                node.name,
                node.language,
                node.path,
                node.area,
                build_id,
                json.dumps(node.metadata, sort_keys=True),
            )
            for node in unique_nodes
        ],
    )
    conn.executemany(
        """
        INSERT INTO graph_edges(edge_id, kind, src_id, dst_id, weight, derived, build_id, metadata_json)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                edge.edge_id,
                edge.kind,
                edge.src_id,
                edge.dst_id,
                edge.weight,
                int(edge.derived),
                build_id,
                json.dumps(edge.metadata, sort_keys=True),
            )
            for edge in unique_edges
        ],
    )
    conn.execute(
        "INSERT OR REPLACE INTO graph_meta(key, value) VALUES(?, ?)",
        ("active_build_id", build_id),
    )
    conn.commit()


def reset_stage_graph(conn: sqlite3.Connection, build_id: str) -> None:
    conn.execute("DELETE FROM graph_nodes_stage")
    conn.execute("DELETE FROM graph_edges_stage")
    conn.execute("DELETE FROM graph_meta_stage")
    conn.execute(
        "INSERT OR REPLACE INTO graph_meta_stage(key, value) VALUES(?, ?)",
        ("schema_version", str(GRAPH_SCHEMA_VERSION)),
    )
    conn.execute(
        "INSERT OR REPLACE INTO graph_meta_stage(key, value) VALUES(?, ?)",
        ("active_build_id", build_id),
    )
    conn.commit()


def insert_stage_nodes(conn: sqlite3.Connection, nodes: list[GraphNode], build_id: str) -> int:
    unique_nodes = _dedupe_nodes(nodes)
    if not unique_nodes:
        return 0
    cursor = conn.executemany(
        """
        INSERT INTO graph_nodes_stage(node_id, kind, name, language, path, area, build_id, metadata_json)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET
            kind = excluded.kind,
            name = excluded.name,
            language = excluded.language,
            path = excluded.path,
            area = excluded.area,
            build_id = excluded.build_id,
            metadata_json = excluded.metadata_json
        """,
        [
            (
                node.node_id,
                node.kind,
                node.name,
                node.language,
                node.path,
                node.area,
                build_id,
                json.dumps(node.metadata, sort_keys=True),
            )
            for node in unique_nodes
        ],
    )
    conn.commit()
    return cursor.rowcount if cursor.rowcount is not None and cursor.rowcount >= 0 else len(unique_nodes)


def insert_stage_edges(conn: sqlite3.Connection, edges: list[GraphEdge], build_id: str) -> int:
    unique_edges = _dedupe_edges(edges)
    if not unique_edges:
        return 0
    cursor = conn.executemany(
        """
        INSERT INTO graph_edges_stage(edge_id, kind, src_id, dst_id, weight, derived, build_id, metadata_json)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(edge_id) DO UPDATE SET
            kind = excluded.kind,
            src_id = excluded.src_id,
            dst_id = excluded.dst_id,
            weight = excluded.weight,
            derived = excluded.derived,
            build_id = excluded.build_id,
            metadata_json = excluded.metadata_json
        """,
        [
            (
                edge.edge_id,
                edge.kind,
                edge.src_id,
                edge.dst_id,
                edge.weight,
                int(edge.derived),
                build_id,
                json.dumps(edge.metadata, sort_keys=True),
            )
            for edge in unique_edges
        ],
    )
    conn.commit()
    return cursor.rowcount if cursor.rowcount is not None and cursor.rowcount >= 0 else len(unique_edges)


def stage_row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    node_count = conn.execute("SELECT COUNT(*) FROM graph_nodes_stage").fetchone()[0]
    edge_count = conn.execute("SELECT COUNT(*) FROM graph_edges_stage").fetchone()[0]
    return {"stage_nodes": int(node_count), "stage_edges": int(edge_count)}


def promote_stage_graph(conn: sqlite3.Connection, build_id: str) -> None:
    with conn:
        conn.execute("DELETE FROM graph_nodes")
        conn.execute("DELETE FROM graph_edges")
        conn.execute("DELETE FROM graph_meta")
        conn.execute(
            """
            INSERT INTO graph_nodes(node_id, kind, name, language, path, area, build_id, metadata_json)
            SELECT node_id, kind, name, language, path, area, build_id, metadata_json
            FROM graph_nodes_stage
            """
        )
        conn.execute(
            """
            INSERT INTO graph_edges(edge_id, kind, src_id, dst_id, weight, derived, build_id, metadata_json)
            SELECT edge_id, kind, src_id, dst_id, weight, derived, build_id, metadata_json
            FROM graph_edges_stage
            """
        )
        conn.execute(
            """
            INSERT INTO graph_meta(key, value)
            SELECT key, value FROM graph_meta_stage
            """
        )
        conn.execute(
            "INSERT OR REPLACE INTO graph_meta(key, value) VALUES(?, ?)",
            ("schema_version", str(GRAPH_SCHEMA_VERSION)),
        )
        conn.execute(
            "INSERT OR REPLACE INTO graph_meta(key, value) VALUES(?, ?)",
            ("active_build_id", build_id),
        )
