# Copyright 2026 Cicadas Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any


_LANGUAGE_MODULES: dict[str, tuple[str, ...]] = {
    "javascript": (
        "tree_sitter_javascript",
        "tree_sitter_languages",
        "tree_sitter_language_pack",
    ),
    "rust": (
        "tree_sitter_rust",
        "tree_sitter_languages",
        "tree_sitter_language_pack",
        "tree_sitter_rust_grammar",
    ),
    "typescript": (
        "tree_sitter_typescript",
        "tree_sitter_languages",
        "tree_sitter_language_pack",
    ),
    "tsx": (
        "tree_sitter_typescript",
        "tree_sitter_languages",
        "tree_sitter_language_pack",
    ),
}


def _safe_import(module_name: str) -> tuple[ModuleType | None, str | None]:
    try:
        return import_module(module_name), None
    except Exception as exc:  # pragma: no cover - metadata path
        return None, f"{module_name}: {exc.__class__.__name__}: {exc}"


def _call_language_loader(module: ModuleType, language: str) -> tuple[Any | None, str | None]:
    candidate_attrs = (
        language,
        f"{language}_language",
        language.upper(),
        "LANGUAGE",
    )
    for attr_name in candidate_attrs:
        if not hasattr(module, attr_name):
            continue
        candidate = getattr(module, attr_name)
        if callable(candidate):
            try:
                return candidate(), None
            except TypeError:
                try:
                    return candidate(language), None
                except Exception as exc:  # pragma: no cover - metadata path
                    return None, f"{module.__name__}.{attr_name}({language!r}): {exc.__class__.__name__}: {exc}"
            except Exception as exc:  # pragma: no cover - metadata path
                return None, f"{module.__name__}.{attr_name}(): {exc.__class__.__name__}: {exc}"
        return candidate, None

    for func_name in ("get_language", "language"):
        if not hasattr(module, func_name):
            continue
        candidate = getattr(module, func_name)
        if not callable(candidate):
            continue
        try:
            return candidate(language), None
        except TypeError:
            try:
                return candidate(), None
            except Exception as exc:  # pragma: no cover - metadata path
                return None, f"{module.__name__}.{func_name}(): {exc.__class__.__name__}: {exc}"
        except Exception as exc:  # pragma: no cover - metadata path
            return None, f"{module.__name__}.{func_name}({language!r}): {exc.__class__.__name__}: {exc}"

    return None, f"{module.__name__}: no language loader found"


def load_language(language: str) -> tuple[Any | None, dict[str, object]]:
    language_key = language.lower().replace("-", "_")
    tree_sitter_module, tree_sitter_error = _safe_import("tree_sitter")
    if tree_sitter_module is None:
        return None, {
            "available": False,
            "package": None,
            "grammar": None,
            "mode": "unavailable",
            "detail": tree_sitter_error or "tree_sitter package is not installed",
        }

    attempted: list[str] = []
    errors: list[str] = []
    for module_name in _LANGUAGE_MODULES.get(language_key, (f"tree_sitter_{language_key}",)):
        attempted.append(module_name)
        module, module_error = _safe_import(module_name)
        if module is None:
            if module_error:
                errors.append(module_error)
            continue

        language_object, language_error = _call_language_loader(module, language_key)
        if language_object is not None:
            return language_object, {
                "available": True,
                "package": module.__name__,
                "grammar": language_key,
                "mode": "tree-sitter",
                "detail": f"loaded {language_key} grammar from {module.__name__}",
            }
        if language_error:
            errors.append(language_error)

    detail_bits = [f"attempted {', '.join(attempted) or language_key}"]
    if errors:
        detail_bits.extend(errors)
    return None, {
        "available": False,
        "package": "tree_sitter",
        "grammar": None,
        "mode": "unavailable",
        "detail": "; ".join(detail_bits),
    }


def language_capability(language: str) -> dict[str, object]:
    _, capability = load_language(language)
    return capability
