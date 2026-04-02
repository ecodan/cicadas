# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from scan_repo import run_scan
from utils import (
    build_canon_plan,
    build_reconcile_scope,
    canon_dir,
    collect_code_context,
    enumerate_canon_targets,
    changed_paths_since_last_commit,
    get_project_root,
    load_json,
    load_repo_context,
    load_repo_metadata,
    load_repo_tree,
)


def _ensure_repo_metadata(root: Path) -> tuple[dict | None, list[dict] | None, str | None]:
    metadata = load_repo_metadata()
    tree = load_repo_tree()
    context = load_repo_context()
    if metadata is None:
        run_scan(root=root)
        metadata = load_repo_metadata()
        tree = load_repo_tree()
        context = load_repo_context()
    return metadata, tree, context


def _gather_canon_docs(canon_root: Path, plan: dict, allowed_scope: set[str] | None = None) -> dict[str, str]:
    canon_docs: dict[str, str] = {}
    for doc in sorted(canon_root.glob("*.md")):
        if allowed_scope is not None and doc.name not in allowed_scope:
            continue
        canon_docs[doc.name] = doc.read_text()
    for target in enumerate_canon_targets(plan):
        if target.endswith("/"):
            directory = canon_root / target.rstrip("/")
            if not directory.exists():
                continue
            for doc in sorted(directory.rglob("*.md")):
                rel = doc.relative_to(canon_root).as_posix()
                if allowed_scope is not None and rel not in allowed_scope:
                    continue
                canon_docs[rel] = doc.read_text()
            continue
        doc_path = canon_root / target
        if doc_path.exists():
            if allowed_scope is not None and target not in allowed_scope:
                continue
            canon_docs[target] = doc_path.read_text()
    return canon_docs


def gather_context(name, is_initiative=False):
    root = get_project_root()
    cicadas = root / ".cicadas"
    registry = load_json(cicadas / "registry.json")

    metadata, repo_tree, repo_context = _ensure_repo_metadata(root)
    plan = build_canon_plan(metadata)
    context = {
        "active_docs": {},
        "code_context": {},
        "canon_docs": {},
        "repo_metadata": metadata or {},
        "repo_tree": repo_tree or [],
        "repo_context": repo_context or "",
        "canon_plan": plan,
    }

    source_dir = cicadas / "active" / name
    if source_dir.exists():
        for doc in source_dir.glob("*.md"):
            context["active_docs"][doc.name] = doc.read_text()

    reconcile_scope = {
        "mode": "full",
        "repo_mode": (metadata or {}).get("repo_mode", "unknown"),
        "reason": "default broad synthesis scope",
        "touched_paths": [],
        "touched_slices": [],
        "neighbor_slices": [],
        "global_docs": [],
        "canon_doc_scope": [],
        "code_scope": [],
    }
    if is_initiative:
        reconcile_scope = build_reconcile_scope(
            metadata,
            context["active_docs"],
            changed_paths_since_last_commit(root),
        )
    context["reconcile_scope"] = reconcile_scope

    modules = []
    if not is_initiative:
        branch_info = registry.get("branches", {}).get(name, {})
        modules = branch_info.get("modules", [])
    else:
        modules = reconcile_scope.get("code_scope", [])
    context["code_context"] = collect_code_context(root, modules, repo_tree)

    canon_root = canon_dir(root)
    if canon_root.exists():
        allowed_scope = set(reconcile_scope.get("canon_doc_scope", [])) if reconcile_scope.get("mode") == "targeted" else None
        context["canon_docs"] = _gather_canon_docs(canon_root, plan, allowed_scope=allowed_scope)

    context["index"] = load_json(cicadas / "index.json")
    return context


def generate_prompt(context):
    prompt_template = Path(__file__).parent.parent / "templates" / "synthesis-prompt.md"
    template_text = prompt_template.read_text()

    prompt = f"{template_text}\n\n"
    prompt += "### DATA CONTEXT ###\n\n"

    if context.get("repo_metadata"):
        prompt += "#### REPO METADATA ####\n"
        prompt += f"```json\n{json.dumps(context['repo_metadata'], indent=2)}\n```\n\n"

    if context.get("repo_context"):
        prompt += "#### REPO CONTEXT ####\n"
        prompt += f"```markdown\n{context['repo_context']}\n```\n\n"

    if context.get("reconcile_scope"):
        prompt += "#### RECONCILE SCOPE ####\n"
        prompt += f"```json\n{json.dumps(context['reconcile_scope'], indent=2)}\n```\n\n"

    if context.get("repo_tree"):
        prompt += "#### REPO TREE SAMPLE ####\n"
        prompt += "```jsonl\n"
        for entry in context["repo_tree"][:40]:
            prompt += json.dumps(entry, sort_keys=True) + "\n"
        prompt += "```\n\n"

    prompt += "#### EXISTING CANON ####\n"
    for name, content in context["canon_docs"].items():
        prompt += f"File: canon/{name}\n```markdown\n{content}\n```\n\n"

    prompt += "#### ACTIVE SPECS ####\n"
    for name, content in context["active_docs"].items():
        prompt += f"File: {name}\n```markdown\n{content}\n```\n\n"

    prompt += "#### CODE CONTEXT ####\n"
    for path, content in context["code_context"].items():
        prompt += f"File: {path}\n```python\n{content}\n```\n\n"

    prompt += "#### CHANGE LEDGER ####\n"
    prompt += f"```json\n{json.dumps(context.get('index', {}), indent=2)}\n```\n\n"

    return prompt


def apply_response(response_text):
    root = get_project_root()
    cicadas = root / ".cicadas"

    pattern = r"File: (canon/[\w\/\.-]+)\n```(?:markdown|python|json|jsonl|text)?\n(.*?)\n```"
    matches = re.findall(pattern, response_text, re.DOTALL)

    if not matches:
        print("No file content blocks found in response.")
        return

    for file_path, content in matches:
        target = cicadas / file_path.replace("canon/", "canon/", 1)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.strip() + "\n")
        print(f"✅ Updated {file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthesis Orchestrator — gather context and generate prompt")
    parser.add_argument("name", help="Name of the branch or initiative")
    parser.add_argument("--initiative", action="store_true", help="Synthesize for an initiative")
    parser.add_argument("--apply", help="Path to a file containing the LLM response to apply to the canon")

    args = parser.parse_args()

    if args.apply:
        response_path = Path(args.apply)
        if response_path.exists():
            apply_response(response_path.read_text())
        else:
            print(f"Error: Response file {args.apply} not found.")
    else:
        ctx = gather_context(args.name, is_initiative=args.initiative)
        print(generate_prompt(ctx))
