# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from graph_ir import GRAPH_SCHEMA_VERSION, GraphEdge, GraphNode


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
        """
    )
    conn.execute(
        "INSERT OR REPLACE INTO graph_meta(key, value) VALUES(?, ?)",
        ("schema_version", str(GRAPH_SCHEMA_VERSION)),
    )
    conn.commit()


def replace_graph(conn: sqlite3.Connection, nodes: list[GraphNode], edges: list[GraphEdge], build_id: str) -> None:
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
            for node in nodes
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
            for edge in edges
        ],
    )
    conn.execute(
        "INSERT OR REPLACE INTO graph_meta(key, value) VALUES(?, ?)",
        ("active_build_id", build_id),
    )
    conn.commit()

