# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import UTC, datetime
import json
import time
from pathlib import Path

from graph_extract.common import build_structural_graph
from graph_extract.javascript import analyzer_status as javascript_analyzer_status
from graph_extract.java import analyzer_status as java_analyzer_status
from graph_extract.rust import analyzer_status as rust_analyzer_status
from graph_ir import GraphEdge, GraphNode
from graph_store import (
    connect_graph,
    initialize_schema,
    insert_stage_edges,
    insert_stage_nodes,
    promote_stage_graph,
    reset_stage_graph,
    stage_row_counts,
)
from scan_repo import run_scan
from utils import (
    graph_db_path,
    graph_dir,
    graph_progress_path,
    graph_progress_log_path,
    load_graph_metadata,
    load_repo_metadata,
    load_repo_tree,
    save_graph_metadata,
    save_json,
)


class _GraphBuildProgress:
    def __init__(self, build_id: str, language_filter: str):
        self.build_id = build_id
        self.language_filter = language_filter
        self.started_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.started_monotonic = time.monotonic()
        self.path = graph_progress_path()
        self.log_path = graph_progress_log_path()
        self.repo_entries_total = 0
        self.structural_files_total = 0
        self.structural_files_processed = 0
        self.python_files_total = 0
        self.python_files_processed = 0
        self.java_files_total = 0
        self.java_files_processed = 0
        self.stage_nodes_written = 0
        self.stage_edges_written = 0

    def _percent_complete(self, *, phase: str, sqlite_written: bool = False, metadata_written: bool = False) -> int:
        total_work = self.structural_files_total + self.python_files_total + self.java_files_total + 3
        if total_work <= 0:
            return 0
        completed_work = self.structural_files_processed + self.python_files_processed + self.java_files_processed
        if phase in {"sqlite_stage_write", "sqlite_stage_write_complete", "promote_stage", "complete"}:
            completed_work += 1
        if sqlite_written or phase in {"promote_stage", "complete"}:
            completed_work += 1
        if metadata_written or phase == "complete":
            completed_work += 1
        percent = min(100, round((completed_work / total_work) * 100))
        # Keep running builds below 100 until the terminal "complete" phase is emitted.
        if phase != "complete" and percent >= 100:
            return 99
        return percent

    def _timing(self, percent_complete: int, phase: str) -> tuple[int, int | None]:
        elapsed_seconds = max(0, round(time.monotonic() - self.started_monotonic))
        if phase == "complete":
            return elapsed_seconds, 0
        if percent_complete <= 0:
            return elapsed_seconds, None
        remaining_percent = 100 - percent_complete
        if remaining_percent <= 0:
            return elapsed_seconds, None
        eta_seconds = round(elapsed_seconds * (remaining_percent / percent_complete))
        return elapsed_seconds, max(0, eta_seconds)

    def write(self, *, phase: str, message: str, status: str = "running", sqlite_written: bool = False, metadata_written: bool = False, **extra: object) -> None:
        self.repo_entries_total = int(extra.get("repo_entries_total", self.repo_entries_total) or 0)
        self.structural_files_total = int(extra.get("structural_files_total", self.structural_files_total) or 0)
        self.structural_files_processed = int(extra.get("structural_files_processed", self.structural_files_processed) or 0)
        self.python_files_total = int(extra.get("python_files_total", self.python_files_total) or 0)
        self.python_files_processed = int(extra.get("python_files_processed", self.python_files_processed) or 0)
        self.java_files_total = int(extra.get("java_files_total", self.java_files_total) or 0)
        self.java_files_processed = int(extra.get("java_files_processed", self.java_files_processed) or 0)
        self.stage_nodes_written = int(extra.get("stage_nodes_written", self.stage_nodes_written) or 0)
        self.stage_edges_written = int(extra.get("stage_edges_written", self.stage_edges_written) or 0)
        updated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "status": status,
            "build_id": self.build_id,
            "language_filter": self.language_filter,
            "started_at": self.started_at,
            "updated_at": updated_at,
            "phase": phase,
            "message": message,
            "repo_entries_total": self.repo_entries_total,
            "structural_files_total": self.structural_files_total,
            "structural_files_processed": self.structural_files_processed,
            "python_files_total": self.python_files_total,
            "python_files_processed": self.python_files_processed,
            "java_files_total": self.java_files_total,
            "java_files_processed": self.java_files_processed,
            "stage_nodes_written": self.stage_nodes_written,
            "stage_edges_written": self.stage_edges_written,
            "percent_complete": self._percent_complete(
                phase=phase,
                sqlite_written=sqlite_written,
                metadata_written=metadata_written,
            ),
        }
        elapsed_seconds, eta_seconds = self._timing(payload["percent_complete"], phase)
        payload["elapsed_seconds"] = elapsed_seconds
        payload["eta_seconds"] = eta_seconds
        payload.update(extra)
        save_json(self.path, payload)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
        print(f"[INFO] {message}", flush=True)


class _GraphBuildSpooler:
    def __init__(self, *, conn, build_id: str, progress: _GraphBuildProgress, batch_size: int = 1000):
        self.conn = conn
        self.build_id = build_id
        self.progress = progress
        self.batch_size = batch_size
        self.node_buffer: list[GraphNode] = []
        self.edge_buffer: list[GraphEdge] = []
        self.stage_nodes_written = 0
        self.stage_edges_written = 0
        self.spool_dir = graph_dir() / "spool"
        self.spool_dir.mkdir(parents=True, exist_ok=True)
        self.nodes_spool_path = self.spool_dir / "nodes.jsonl"
        self.edges_spool_path = self.spool_dir / "edges.jsonl"
        self._reset_spool_files()

    def _reset_spool_files(self) -> None:
        self.nodes_spool_path.write_text("", encoding="utf-8")
        self.edges_spool_path.write_text("", encoding="utf-8")

    def emit(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        if nodes:
            self.node_buffer.extend(nodes)
        if edges:
            self.edge_buffer.extend(edges)
        if len(self.node_buffer) >= self.batch_size or len(self.edge_buffer) >= self.batch_size:
            self.flush()

    def flush(self, *, force: bool = False) -> None:
        if not force and len(self.node_buffer) < self.batch_size and len(self.edge_buffer) < self.batch_size:
            return
        if not self.node_buffer and not self.edge_buffer:
            return
        self._append_spool(self.nodes_spool_path, self.node_buffer)
        self._append_spool(self.edges_spool_path, self.edge_buffer)
        inserted_nodes = insert_stage_nodes(self.conn, self.node_buffer, self.build_id)
        inserted_edges = insert_stage_edges(self.conn, self.edge_buffer, self.build_id)
        self.stage_nodes_written += inserted_nodes
        self.stage_edges_written += inserted_edges
        self.node_buffer = []
        self.edge_buffer = []
        counts = stage_row_counts(self.conn)
        self.progress.write(
            phase="sqlite_stage_write",
            message=f"SQLite stage write: {counts['stage_nodes']} nodes, {counts['stage_edges']} edges",
            stage_nodes_written=counts["stage_nodes"],
            stage_edges_written=counts["stage_edges"],
        )

    def _append_spool(self, path: Path, records: list[GraphNode] | list[GraphEdge]) -> None:
        if not records:
            return
        with open(path, "a", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record.__dict__, sort_keys=True))
                handle.write("\n")


def run_graph_build(language_filter: str = "auto", force: bool = False) -> int:
    existing = load_graph_metadata()
    build_id = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    progress = _GraphBuildProgress(build_id=build_id, language_filter=language_filter)

    try:
        if existing and not force:
            progress.write(
                phase="prepare",
                message="Existing graph metadata found. Rebuilding because graph builds are explicit and replace derived state.",
            )
        else:
            progress.write(
                phase="prepare",
                message=f"Graph build started (build_id={build_id}, languages={language_filter})",
            )

        if load_repo_metadata() is None or load_repo_tree() is None:
            progress.write(
                phase="scan_repo",
                message="Repo inventory missing. Running scan-repo before graph build.",
            )
            run_scan(progress_mode="off")

        conn = connect_graph(graph_db_path())
        try:
            initialize_schema(conn)
            reset_stage_graph(conn, build_id)
            spooler = _GraphBuildSpooler(conn=conn, build_id=build_id, progress=progress)
            progress.write(
                phase="sqlite_stage_write",
                message="Writing graph data to SQLite stage tables",
                stage_nodes_written=0,
                stage_edges_written=0,
            )
            _nodes, _edges, stats = build_structural_graph(
                build_id,
                progress=lambda update: progress.write(**update),
                emit=spooler.emit,
            )
            spooler.flush(force=True)
            counts = stage_row_counts(conn)
            progress.write(
                phase="sqlite_stage_write_complete",
                message=f"SQLite stage write complete ({counts['stage_nodes']} nodes, {counts['stage_edges']} edges)",
                stage_nodes_written=counts["stage_nodes"],
                stage_edges_written=counts["stage_edges"],
                repo_entries_total=progress.repo_entries_total,
                structural_files_total=progress.structural_files_total,
                structural_files_processed=progress.structural_files_total,
                python_files_total=progress.python_files_total,
                python_files_processed=progress.python_files_total,
                java_files_total=progress.java_files_total,
                java_files_processed=progress.java_files_total,
            )
            progress.write(
                phase="promote_stage",
                message="Promoting stage graph into active tables",
                stage_nodes_written=counts["stage_nodes"],
                stage_edges_written=counts["stage_edges"],
                repo_entries_total=progress.repo_entries_total,
                structural_files_total=progress.structural_files_total,
                structural_files_processed=progress.structural_files_total,
                python_files_total=progress.python_files_total,
                python_files_processed=progress.python_files_total,
                java_files_total=progress.java_files_total,
                java_files_processed=progress.java_files_total,
            )
            promote_stage_graph(conn, build_id)
        finally:
            conn.close()
        progress.write(
            phase="sqlite_write_complete",
            message="SQLite active graph write complete",
            sqlite_written=True,
            repo_entries_total=progress.repo_entries_total,
            structural_files_total=progress.structural_files_total,
            structural_files_processed=progress.structural_files_total,
            python_files_total=progress.python_files_total,
            python_files_processed=progress.python_files_total,
            java_files_total=progress.java_files_total,
            java_files_processed=progress.java_files_total,
            stage_nodes_written=progress.stage_nodes_written,
            stage_edges_written=progress.stage_edges_written,
        )

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
                    "java": stats.get("java_stats", {}).get("java_mode", java_analyzer_status()),
                    "rust": rust_analyzer_status(),
                },
                "symbols_indexed": stats.get("python_stats", {}).get("symbols_indexed", 0) + stats.get("java_stats", {}).get("symbols_indexed", 0),
                "java_symbols_indexed": stats.get("java_stats", {}).get("symbols_indexed", 0),
            }
        )
        progress.write(
            phase="complete",
            status="complete",
            message="Graph build complete",
            sqlite_written=True,
            metadata_written=True,
            repo_entries_total=progress.repo_entries_total,
            structural_files_total=progress.structural_files_total,
            structural_files_processed=progress.structural_files_total,
            python_files_total=progress.python_files_total,
            python_files_processed=progress.python_files_total,
            java_files_total=progress.java_files_total,
            java_files_processed=progress.java_files_total,
            stage_nodes_written=progress.stage_nodes_written,
            stage_edges_written=progress.stage_edges_written,
            indexed_languages=stats["indexed_languages"],
            seeded_areas=len(stats["seeded_areas"]),
            symbols_indexed=stats.get("python_stats", {}).get("symbols_indexed", 0) + stats.get("java_stats", {}).get("symbols_indexed", 0),
            java_symbols_indexed=stats.get("java_stats", {}).get("symbols_indexed", 0),
            db_path=str(graph_db_path()),
        )

        print(f"[OK]   Graph build complete: {graph_db_path()}")
        print(f"[INFO] Build ID: {build_id}")
        print(f"[INFO] Indexed languages: {', '.join(stats['indexed_languages']) if stats['indexed_languages'] else 'none'}")
        print(f"[INFO] Seeded areas: {len(stats['seeded_areas'])}")
        return 0
    except Exception as exc:
        progress.write(
            phase="failed",
            status="failed",
            message=f"Graph build failed: {exc}",
            repo_entries_total=progress.repo_entries_total,
            structural_files_total=progress.structural_files_total,
            structural_files_processed=progress.structural_files_processed,
            python_files_total=progress.python_files_total,
            python_files_processed=progress.python_files_processed,
            java_files_total=progress.java_files_total,
            java_files_processed=progress.java_files_processed,
            stage_nodes_written=progress.stage_nodes_written,
            stage_edges_written=progress.stage_edges_written,
            error=str(exc),
        )
        raise
