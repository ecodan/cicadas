# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_project_root, load_json


def classify(name: str) -> str:
    if name.startswith("fix/") or name.startswith("fix-"):
        return "fix"
    if name.startswith("tweak/") or name.startswith("tweak-"):
        return "tweak"
    return "initiative"


def extract_summary(folder: Path) -> str:
    """Pull executive summary / intent from the best available spec file."""
    for filename in ("tweaklet.md", "buglet.md", "prd.md"):
        spec = folder / filename
        if not spec.exists():
            continue
        text = spec.read_text()
        # tweaklet/buglet: use ## Intent section
        m = re.search(r"##\s+Intent\s*\n+(.*?)(?=\n##|\Z)", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        # prd: use ## Executive Summary section
        m = re.search(r"##\s+Executive Summary\s*\n+(.*?)(?=\n##|\Z)", text, re.DOTALL)
        if m:
            return m.group(1).strip()[:600]
    return ""


def count_tasks(folder: Path) -> tuple[int, int]:
    """Return (total, completed) task counts from tasks.md or tweaklet/buglet."""
    for filename in ("tasks.md", "tweaklet.md", "buglet.md"):
        spec = folder / filename
        if not spec.exists():
            continue
        text = spec.read_text()
        total = len(re.findall(r"- \[[ xX]\]", text))
        done = len(re.findall(r"- \[[xX]\]", text))
        if total:
            return total, done
    return 0, 0


def parse_archive_entry(folder: Path, index_by_branch: dict) -> dict:
    # folder name: {timestamp}-{name}
    parts = folder.name.split("-", 1)
    timestamp_str = parts[0] if parts else ""
    name = parts[1] if len(parts) > 1 else folder.name

    try:
        dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        date_str = dt.strftime("%b %d, %Y")
    except ValueError:
        date_str = timestamp_str

    kind = classify(name)
    summary = extract_summary(folder)
    total_tasks, done_tasks = count_tasks(folder)
    ledger_summary = index_by_branch.get(name, {}).get("summary", "")

    return {
        "name": name,
        "kind": kind,
        "date": date_str,
        "summary": summary,
        "ledger_summary": ledger_summary,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
    }


def render_html(entries: list[dict]) -> str:
    kind_labels = {"initiative": "Initiative", "tweak": "Tweak", "fix": "Bug Fix"}
    kind_colors = {"initiative": "#4f46e5", "tweak": "#0891b2", "fix": "#dc2626"}

    cards = []
    for e in entries:
        color = kind_colors.get(e["kind"], "#6b7280")
        label = kind_labels.get(e["kind"], e["kind"].title())
        task_line = f"<p class='tasks'>{e['done_tasks']}/{e['total_tasks']} tasks completed</p>" if e["total_tasks"] else ""
        ledger = f"<p class='ledger'><em>{e['ledger_summary']}</em></p>" if e["ledger_summary"] else ""
        summary_text = e["summary"].replace("\n\n", "</p><p>").replace("\n", " ")
        summary_block = f"<p>{summary_text}</p>" if summary_text else ""

        cards.append(f"""
        <div class="entry">
          <div class="dot" style="background:{color}"></div>
          <div class="card">
            <div class="card-header">
              <span class="badge" style="background:{color}">{label}</span>
              <span class="date">{e["date"]}</span>
            </div>
            <h3>{e["name"]}</h3>
            {task_line}
            {summary_block}
            {ledger}
          </div>
        </div>""")

    cards_html = "\n".join(cards) if cards else "<p style='color:#6b7280'>No archived entries found.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Project History</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; color: #1e293b; padding: 2rem; }}
  h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 0.25rem; }}
  .subtitle {{ color: #64748b; margin-bottom: 2.5rem; font-size: 0.95rem; }}
  .timeline {{ position: relative; max-width: 780px; }}
  .timeline::before {{ content: ""; position: absolute; left: 11px; top: 0; bottom: 0; width: 2px; background: #e2e8f0; }}
  .entry {{ display: flex; gap: 1.25rem; margin-bottom: 1.75rem; position: relative; }}
  .dot {{ width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0; margin-top: 0.9rem;
    border: 3px solid #f8fafc; box-shadow: 0 0 0 2px #e2e8f0; }}
  .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem 1.25rem; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
  .card-header {{ display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.4rem; }}
  .badge {{ color: #fff; font-size: 0.7rem; font-weight: 600; padding: 2px 8px;
    border-radius: 999px; text-transform: uppercase; letter-spacing: .04em; }}
  .date {{ color: #94a3b8; font-size: 0.82rem; margin-left: auto; }}
  h3 {{ font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; word-break: break-word; }}
  .tasks {{ font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem; }}
  p {{ font-size: 0.88rem; color: #475569; line-height: 1.55; margin-bottom: 0.4rem; }}
  .ledger {{ color: #64748b !important; border-top: 1px solid #f1f5f9; padding-top: 0.4rem; margin-top: 0.4rem; }}
</style>
</head>
<body>
<h1>Project History</h1>
<p class="subtitle">Completed initiatives, tweaks, and bug fixes &mdash; generated from .cicadas/archive</p>
<div class="timeline">
{cards_html}
</div>
</body>
</html>"""


def generate(output_path: Path | None = None) -> Path:
    root = get_project_root()
    archive_dir = root / ".cicadas" / "archive"
    index_path = root / ".cicadas" / "index.json"

    index = load_json(index_path)
    index_by_branch = {e["branch"]: e for e in index.get("entries", [])}

    entries = []
    if archive_dir.exists():
        for folder in sorted(archive_dir.iterdir(), reverse=True):
            if folder.is_dir():
                entries.append(parse_archive_entry(folder, index_by_branch))

    html = render_html(entries)

    if output_path is None:
        output_path = root / ".cicadas" / "canon" / "history.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate project history HTML timeline.")
    parser.add_argument("--output", type=Path, default=None, help="Output path (default: .cicadas/canon/history.html)")
    args = parser.parse_args()
    out = generate(args.output)
    print(f"Generated: {out}")
