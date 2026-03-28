# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import fcntl
import json
import logging
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from utils import get_registry_root

LOG_FORMAT = "%(asctime)s [%(levelname)s] <%(filename)s:%(lineno)s> %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.WARNING)
logger = logging.getLogger(__name__)

INITIATIVE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _current_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "branch", "--show-current"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return ""


def emit_event(initiative: str, event_type: str, data: dict) -> None:
    if not INITIATIVE_RE.match(initiative):
        raise ValueError(f"Invalid initiative name: {initiative!r}. Must match [a-z0-9][a-z0-9-]*")

    events_path: Path = get_registry_root() / ".cicadas" / "active" / initiative / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)

    event: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "initiative": initiative,
        "branch": _current_branch(),
        "data": data,
    }
    line: str = json.dumps(event, separators=(",", ":")) + "\n"

    with open(events_path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a typed event to the initiative event log.")
    parser.add_argument("--initiative", required=True, help="Initiative name")
    parser.add_argument("--type", required=True, dest="event_type", help="Event type (dotted string)")
    parser.add_argument("--data", default="{}", help="JSON object payload (default: {})")
    args = parser.parse_args()

    try:
        data: dict = json.loads(args.data)
        if not isinstance(data, dict):
            raise ValueError("--data must be a JSON object")
    except json.JSONDecodeError as e:
        print(f"Error: --data is not valid JSON: {e}", file=sys.stderr)
        return 1

    try:
        emit_event(args.initiative, args.event_type, data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error("Failed to emit event: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
