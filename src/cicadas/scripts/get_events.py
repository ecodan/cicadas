# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from utils import get_registry_root

LOG_FORMAT = "%(asctime)s [%(levelname)s] <%(filename)s:%(lineno)s> %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.WARNING)
logger = logging.getLogger(__name__)


def _parse_timestamp(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime."""
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def get_events(
    initiative: str,
    event_type: str | None = None,
    since: str | None = None,
    last: int | None = None,
) -> list[dict]:
    """Read and filter the event log for an initiative.

    Args:
        initiative: Initiative name.
        event_type: Exact type or prefix match (e.g. "partition" matches "partition.complete").
        since: ISO 8601 timestamp; only return events at or after this time.
        last: Return only the N most recent events after other filters.

    Returns:
        List of event dicts sorted by timestamp ascending.
    """
    events_path: Path = get_registry_root() / ".cicadas" / "active" / initiative / "events.jsonl"

    if not events_path.exists():
        return []

    events: list[dict] = []
    try:
        with open(events_path) as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError as e:
                    logger.warning("Skipping malformed line %d in %s: %s", lineno, events_path, e)
    except OSError as e:
        logger.error("Failed to read events file: %s", e)
        raise

    # Sort by timestamp ascending
    events.sort(key=lambda e: _parse_timestamp(e.get("timestamp", "")))

    # Filter by type (exact or prefix)
    if event_type is not None:
        events = [
            e for e in events
            if e.get("type") == event_type or e.get("type", "").startswith(event_type + ".")
        ]

    # Filter by since
    if since is not None:
        since_dt = _parse_timestamp(since)
        events = [e for e in events if _parse_timestamp(e.get("timestamp", "")) >= since_dt]

    # Apply --last N (most recent after other filters)
    if last is not None and last > 0:
        events = events[-last:]

    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="Read and filter the Cicadas event log.")
    parser.add_argument("--initiative", required=True, help="Initiative name")
    parser.add_argument("--type", default=None, dest="event_type",
                        help="Filter by event type (exact or prefix match)")
    parser.add_argument("--since", default=None, help="ISO 8601 timestamp; return events at or after")
    parser.add_argument("--last", type=int, default=None, help="Return only the N most recent events")
    args = parser.parse_args()

    try:
        events = get_events(
            initiative=args.initiative,
            event_type=args.event_type,
            since=args.since,
            last=args.last,
        )
    except OSError as e:
        print(f"Error reading events: {e}", file=sys.stderr)
        return 1

    for event in events:
        print(json.dumps(event, separators=(",", ":")))

    return 0


if __name__ == "__main__":
    sys.exit(main())
