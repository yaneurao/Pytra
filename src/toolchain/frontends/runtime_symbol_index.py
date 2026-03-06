from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = ROOT / "tools" / "runtime_symbol_index.json"
_CACHE: dict[str, Any] | None = None


def _load_index() -> dict[str, Any]:
    global _CACHE
    if isinstance(_CACHE, dict):
        return _CACHE
    try:
        obj = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        obj = {}
    if not isinstance(obj, dict):
        obj = {}
    _CACHE = obj
    return obj


def clear_runtime_symbol_index_cache() -> None:
    global _CACHE
    _CACHE = None


def load_runtime_symbol_index() -> dict[str, Any]:
    return _load_index()


def lookup_target_module_artifacts(target: str, module_id: str) -> dict[str, Any]:
    doc = _load_index()
    targets = doc.get("targets")
    if not isinstance(targets, dict):
        return {}
    target_doc = targets.get(target)
    if not isinstance(target_doc, dict):
        return {}
    modules = target_doc.get("modules")
    if not isinstance(modules, dict):
        return {}
    artifacts = modules.get(module_id)
    if not isinstance(artifacts, dict):
        return {}
    return artifacts


def lookup_target_module_public_headers(target: str, module_id: str) -> list[str]:
    artifacts = lookup_target_module_artifacts(target, module_id)
    items = artifacts.get("public_headers")
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items:
        if isinstance(item, str) and item != "":
            out.append(item)
    return out


def lookup_target_module_compile_sources(target: str, module_id: str) -> list[str]:
    artifacts = lookup_target_module_artifacts(target, module_id)
    items = artifacts.get("compile_sources")
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items:
        if isinstance(item, str) and item != "":
            out.append(item)
    return out


def lookup_target_module_primary_header(target: str, module_id: str) -> str:
    headers = lookup_target_module_public_headers(target, module_id)
    for suffix in (".gen.h", ".ext.h", ".h"):
        for header in headers:
            if header.endswith(suffix):
                return header
    if len(headers) > 0:
        return headers[0]
    return ""


def repo_runtime_path_to_include(path_txt: str) -> str:
    if path_txt.startswith("src/"):
        return path_txt[4:]
    return path_txt
