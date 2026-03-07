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


def lookup_runtime_module_doc(module_id: str) -> dict[str, Any]:
    doc = _load_index()
    modules = doc.get("modules")
    if not isinstance(modules, dict):
        return {}
    mod = modules.get(module_id)
    if not isinstance(mod, dict):
        return {}
    return mod


def lookup_runtime_module_group(module_id: str) -> str:
    mod = lookup_runtime_module_doc(module_id)
    group = mod.get("runtime_group")
    if isinstance(group, str):
        return group
    return ""


def lookup_runtime_module_symbols(module_id: str) -> dict[str, Any]:
    mod = lookup_runtime_module_doc(module_id)
    symbols = mod.get("symbols")
    if not isinstance(symbols, dict):
        return {}
    return symbols


def runtime_module_exists(module_id: str) -> bool:
    return len(lookup_runtime_module_doc(module_id)) > 0


def canonical_runtime_module_id(module_id: str) -> str:
    if runtime_module_exists(module_id):
        return module_id
    if "." not in module_id:
        mapped = "pytra.std." + module_id
        if runtime_module_exists(mapped):
            return mapped
    return module_id


def resolve_import_binding_runtime_module(module_id: str, export_name: str, binding_kind: str) -> str:
    mod = canonical_runtime_module_id(module_id.strip())
    if mod == "":
        return ""
    if binding_kind == "module":
        return mod if runtime_module_exists(mod) else ""
    if binding_kind != "symbol":
        return ""
    child_module = mod + "." + export_name.strip() if export_name.strip() != "" else ""
    if child_module != "" and runtime_module_exists(child_module):
        return child_module
    symbols = lookup_runtime_module_symbols(mod)
    if export_name in symbols:
        return mod
    return ""


def lookup_cpp_namespace_for_runtime_module(module_id: str) -> str:
    mod = canonical_runtime_module_id(module_id.strip())
    group = lookup_runtime_module_group(mod)
    if group == "std":
        tail = mod[len("pytra.std.") :] if mod.startswith("pytra.std.") else ""
        if tail != "":
            return "pytra::std::" + tail.replace(".", "::")
        return "pytra::std"
    if group == "utils":
        tail = mod[len("pytra.utils.") :] if mod.startswith("pytra.utils.") else ""
        if tail != "":
            return "pytra::utils::" + tail.replace(".", "::")
        return "pytra::utils"
    if group in {"built_in", "core"}:
        return ""
    if mod.startswith("pytra."):
        tail = mod[len("pytra.") :]
        if tail != "":
            return "pytra::" + tail.replace(".", "::")
        return "pytra"
    if mod.startswith("toolchain.compiler."):
        tail = mod[len("toolchain.compiler.") :]
        if tail != "":
            return "pytra::compiler::" + tail.replace(".", "::")
        return "pytra::compiler"
    return ""


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
    if target == "cpp":
        for header in headers:
            if header.startswith("src/runtime/cpp/pytra/"):
                return header
        for header in headers:
            if header.startswith("src/runtime/cpp/generated/"):
                return header
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
