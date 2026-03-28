# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

"""
Open a Pull Request from the current branch to a target branch.
Host-agnostic: tries gh, then glab, then Bitbucket URL, else prints fallback.
No API keys; uses host CLI auth (e.g. gh auth login) when available.

Note: --body-file paths are resolved relative to the project root (where .cicadas lives),
not the current working directory.
"""

import argparse
import re
import shutil
import subprocess
from pathlib import Path

from review import parse_verdict
from utils import emit, get_default_branch, get_project_root, load_json


def _initiative_for_branch(root: "Path", branch: str) -> str:
    """Return initiative name for a registered branch, or the branch name itself."""
    registry: dict = load_json(root / ".cicadas" / "registry.json")
    return registry.get("branches", {}).get(branch, {}).get("initiative", branch)


def _current_branch(root: Path) -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, text=True)
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _remote_url(root: Path, remote: str = "origin") -> str | None:
    try:
        out = subprocess.check_output(["git", "remote", "get-url", remote], cwd=root, text=True, stderr=subprocess.DEVNULL)
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _bitbucket_pr_url(remote_url: str | None, source_branch: str | None, target_branch: str | None) -> str | None:
    """Build Bitbucket 'new pull request' URL if remote looks like Bitbucket."""
    if not remote_url or not source_branch or not target_branch:
        return None
    # e.g. https://bitbucket.org/workspace/repo or git@bitbucket.org:workspace/repo.git
    m = re.match(r"(?:https?://bitbucket\.org/|git@bitbucket\.org:)([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
    if not m:
        return None
    workspace, repo = m.group(1), m.group(2)
    return f"https://bitbucket.org/{workspace}/{repo}/pull-requests/new?source={source_branch}&dest={target_branch}"


def _check_review_verdict(root: Path, current_branch: str) -> int:
    """
    Check review.md verdict for the current branch's initiative.
    Returns 0 to proceed, 1 to abort (BLOCK verdict).
    Prints warnings for PASS WITH NOTES or missing review.md; does not abort those cases.
    """
    registry: dict = load_json(root / ".cicadas" / "registry.json")
    entry: dict | None = registry.get("branches", {}).get(current_branch)
    if not entry:
        return 0  # unregistered branch — no review gate applies
    initiative: str = entry.get("initiative", "")
    review_path: Path = root / ".cicadas" / "active" / initiative / "review.md"
    if not review_path.exists():
        print(f"[WARN] No review.md found for '{initiative}'. Run Code Review before opening a PR.")
        return 0
    verdict: str | None = parse_verdict(review_path.read_text())
    if verdict == "BLOCK":
        print(f"[BLOCK] Code review verdict for '{initiative}' is BLOCK.")
        print("  Resolve all Blocking findings before opening a PR.")
        print(f"  See: {review_path}")
        emit(initiative, "pr.blocked", {"reason": "BLOCK verdict from code review", "branch": current_branch})
        return 1
    if verdict == "PASS WITH NOTES":
        print(f"[NOTE] Code review verdict for '{initiative}' is PASS WITH NOTES.")
        print("  Advisory findings present — review recommended before merging.")
    return 0


def open_pr(base_branch: str | None = None, body_file: str | None = None) -> int:
    root: Path = get_project_root()
    current: str | None = _current_branch(root)
    initiative: str = _initiative_for_branch(root, current) if current else ""
    if not current:
        print("Not a git repository or detached HEAD.")
        return 1
    base: str = base_branch or get_default_branch()
    if current == base:
        print(f"Current branch is already {base}. Switch to a feature branch first.")
        return 1

    if _check_review_verdict(root, current) != 0:
        return 1

    # Check if this is an initiative branch and suggest archiving first for 1-PR flow
    if current.startswith("initiative/"):
        name = current.split("/", 1)[1]
        active_dir = root / ".cicadas" / "active" / name
        if active_dir.exists():
            print(f"[TIP]  To include finalization in this PR (1-PR flow):")
            print(f"       1. Run 'cicadas synthesize {name} --initiative'")
            print(f"       2. Run 'cicadas archive {name} --type initiative'")
            print(f"       3. Commit and push the archive move and registry deletion.")
            print(f"       (You can always undo with 'cicadas unarchive {name}' if rework is needed.)")
            print("-" * 40)

    body_path: Path | None = (root / body_file) if body_file else None

    # 1) GitHub CLI
    gh: str | None = shutil.which("gh")
    if gh:
        cmd: list[str] = [gh, "pr", "create", "--base", base, "--head", current]
        if body_path and body_path.exists():
            cmd.extend(["--body-file", str(body_path)])
        try:
            subprocess.run(cmd, cwd=root, check=True)
            emit(initiative, "pr.opened", {"base": base, "head": current})
            return 0
        except subprocess.CalledProcessError:
            pass

    # 2) GitLab CLI
    glab: str | None = shutil.which("glab")
    if glab:
        cmd = [glab, "mr", "create", "--target-branch", base]
        if body_path and body_path.exists():
            cmd.extend(["--description-file", str(body_path)])
        try:
            subprocess.run(cmd, cwd=root, check=True)
            emit(initiative, "pr.opened", {"base": base, "head": current})
            return 0
        except subprocess.CalledProcessError:
            pass

    # 3) Bitbucket URL
    url: str | None = _bitbucket_pr_url(_remote_url(root), current, base)
    if url:
        print(f"Open a Pull Request in Bitbucket:\n  {url}")
        return 0

    # 4) Fallback
    print("No PR CLI found (gh, glab). Push your branch and open a Pull Request in your host's UI:")
    print(f"  Branch: {current} → {base}")
    print("  (GitHub, GitLab, Bitbucket, or merge locally.)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open a PR from current branch to target (host-agnostic)")
    parser.add_argument("--base", default=None, help="Target branch (default: default branch)")
    parser.add_argument("--body-file", default=None, help="Path to PR description file (relative to project root)")
    args = parser.parse_args()
    exit(open_pr(base_branch=args.base, body_file=args.body_file) or 0)
