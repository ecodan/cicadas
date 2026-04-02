# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


GRAPH_SCHEMA_VERSION = 1

NodeKind = Literal[
    "repo",
    "area",
    "package",
    "file",
    "symbol",
    "test",
    "build_target",
    "entrypoint",
    "external_dep",
]

EdgeKind = Literal[
    "contains",
    "declares",
    "imports",
    "references",
    "calls",
    "implements",
    "overrides",
    "tests",
    "builds_to",
    "enters_at",
    "depends_on",
    "neighbors",
    "owns",
]


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: NodeKind
    name: str
    language: str | None = None
    path: str | None = None
    area: str | None = None
    build_id: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    kind: EdgeKind
    src_id: str
    dst_id: str
    weight: float | None = None
    derived: bool = False
    build_id: str = ""
    metadata: dict = field(default_factory=dict)

