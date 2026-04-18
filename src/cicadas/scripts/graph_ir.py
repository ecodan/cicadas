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

ExtractionSource = Literal["inventory", "fallback-structural", "python-ast", "tree-sitter", "resolver", "semantic"]
Confidence = Literal["low", "medium", "high"]
SemanticResolution = Literal["unresolved", "heuristic", "resolved"]


def fact_metadata(
    extraction_source: ExtractionSource,
    confidence: Confidence,
    *,
    semantic_resolution: SemanticResolution = "unresolved",
    analyzer: str | None = None,
    **extra: object,
) -> dict:
    metadata = {
        "extraction_source": extraction_source,
        "confidence": confidence,
        "semantic_resolution": semantic_resolution,
    }
    if analyzer:
        metadata["analyzer"] = analyzer
    metadata.update({key: value for key, value in extra.items() if value is not None})
    return metadata


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
