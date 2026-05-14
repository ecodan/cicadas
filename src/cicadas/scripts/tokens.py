# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

VALID_SOURCES = {"agent-reported", "unavailable", "estimated"}


@contextmanager
def _locked_log(log_path: Path):
    lock_path = log_path.with_name(f".{log_path.name}.lock")
    with open(lock_path, "a+") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _atomic_write_log(log_path: Path, entries: list[dict]) -> None:
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=log_path.parent,
            prefix=f".{log_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp_name = tmp.name
            json.dump({"entries": entries}, tmp, indent=2)
            tmp.write("\n")
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, log_path)
        tmp_name = None
        dir_fd = os.open(log_path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def init_log(log_path: Path) -> None:
    """Create tokens.json with empty entries list if it doesn't exist."""
    log_path = Path(log_path)
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w") as f:
            json.dump({"entries": []}, f, indent=2)


def load_log(log_path: Path) -> list[dict]:
    """Return entries list. Returns [] if file absent or corrupt, never raises."""
    try:
        log_path = Path(log_path)
        if not log_path.exists():
            return []
        with open(log_path) as f:
            data = json.load(f)
        return data.get("entries", [])
    except (json.JSONDecodeError, OSError):
        return []


def append_entry(
    log_path: Path,
    initiative: str,
    phase: str,
    source: str,
    *,
    subphase: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cached_tokens: int | None = None,
    model: str | None = None,
    notes: str | None = None,
) -> None:
    """Append a validated token entry to the log. Creates file if absent."""
    if not initiative:
        raise ValueError("initiative is required")
    if not phase:
        raise ValueError("phase is required")
    if source not in VALID_SOURCES:
        raise ValueError(f"source must be one of {VALID_SOURCES}, got {source!r}")

    entry: dict = {
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "initiative": initiative,
        "phase": phase,
        "subphase": subphase,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "model": model,
        "source": source,
        "notes": notes,
    }

    log_path = Path(log_path)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with _locked_log(log_path):
            entries = load_log(log_path)
            entries.append(entry)
            _atomic_write_log(log_path, entries)
    except OSError as e:
        print(f"[WARN] Could not write token entry to {log_path}: {e}")
