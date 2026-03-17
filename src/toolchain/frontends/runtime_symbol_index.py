from __future__ import annotations

from pathlib import Path
from typing import Any

from pytra.std import json
from toolchain.json_adapters import export_json_object_dict


ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = ROOT / "tools" / "runtime_symbol_index.json"
_CACHE: dict[str, Any] | None = None
_FRONTEND_FACADE_RUNTIME_MODULE_BY_SYMBOL: dict[str, str] = {
    "add_common_transpile_args": "toolchain.compiler.transpile_cli",
    "build_module_east_map": "toolchain.compiler.transpile_cli",
    "load_east3_document": "toolchain.compiler.transpile_cli",
    "load_east3_document_typed": "toolchain.compiler.transpile_cli",
    "normalize_common_transpile_args": "toolchain.compiler.transpile_cli",
}


def _load_index() -> dict[str, Any]:
    global _CACHE
    if isinstance(_CACHE, dict):
        return _CACHE
    try:
        obj = json.loads_obj(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        obj = None
    if obj is None:
        _CACHE = {}
        return _CACHE
    _CACHE = export_json_object_dict(obj)
    return _CACHE


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


def lookup_runtime_module_extern_contract(module_id: str) -> dict[str, Any]:
    mod = lookup_runtime_module_doc(canonical_runtime_module_id(module_id.strip()))
    extern_contract = mod.get("extern_contract_v1")
    if not isinstance(extern_contract, dict):
        return {}
    return extern_contract


def lookup_runtime_symbol_doc(module_id: str, symbol_name: str) -> dict[str, Any]:
    mod = canonical_runtime_module_id(module_id.strip())
    if mod == "":
        return {}
    symbols = lookup_runtime_module_symbols(mod)
    symbol = symbols.get(symbol_name.strip())
    if not isinstance(symbol, dict):
        return {}
    return symbol


def lookup_runtime_symbol_extern_doc(module_id: str, symbol_name: str) -> dict[str, Any]:
    symbol_doc = lookup_runtime_symbol_doc(module_id, symbol_name)
    extern_doc = symbol_doc.get("extern_v1")
    if not isinstance(extern_doc, dict):
        return {}
    return extern_doc


def lookup_runtime_call_adapter_kind(module_id: str, symbol_name: str) -> str:
    symbol_doc = lookup_runtime_symbol_doc(module_id, symbol_name)
    adapter_kind = symbol_doc.get("call_adapter_kind")
    if isinstance(adapter_kind, str):
        return adapter_kind
    return ""


def resolve_import_binding_doc(module_id: str, export_name: str, binding_kind: str) -> dict[str, Any]:
    source_module_id = module_id.strip()
    source_export_name = export_name.strip()
    source_binding_kind = binding_kind.strip()
    runtime_module_id = resolve_import_binding_runtime_module(
        source_module_id,
        source_export_name,
        source_binding_kind,
    )
    if runtime_module_id == "":
        return {}
    out: dict[str, Any] = {
        "source_module_id": source_module_id,
        "source_export_name": source_export_name,
        "source_binding_kind": source_binding_kind,
        "runtime_module_id": runtime_module_id,
        "runtime_group": lookup_runtime_module_group(runtime_module_id),
    }
    if source_binding_kind == "module":
        out["resolved_binding_kind"] = "module"
        return out
    child_module = canonical_runtime_module_id(source_module_id)
    if child_module != "" and runtime_module_id != child_module:
        out["resolved_binding_kind"] = "module"
        return out
    symbol_doc = lookup_runtime_symbol_doc(runtime_module_id, source_export_name)
    if len(symbol_doc) == 0:
        return out
    out["resolved_binding_kind"] = "symbol"
    out["runtime_symbol"] = source_export_name
    kind = symbol_doc.get("kind")
    if isinstance(kind, str) and kind != "":
        out["runtime_symbol_kind"] = kind
    dispatch = symbol_doc.get("dispatch")
    if isinstance(dispatch, str) and dispatch != "":
        out["runtime_symbol_dispatch"] = dispatch
    semantic_tag = symbol_doc.get("semantic_tag")
    if isinstance(semantic_tag, str) and semantic_tag != "":
        out["runtime_semantic_tag"] = semantic_tag
    adapter_kind = symbol_doc.get("call_adapter_kind")
    if isinstance(adapter_kind, str) and adapter_kind != "":
        out["runtime_call_adapter_kind"] = adapter_kind
    extern_doc = symbol_doc.get("extern_v1")
    if isinstance(extern_doc, dict):
        extern_kind = extern_doc.get("kind")
        if isinstance(extern_kind, str) and extern_kind != "":
            out["runtime_extern_kind"] = extern_kind
    return out


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


def _resolve_frontend_facade_runtime_module(module_id: str, export_name: str, binding_kind: str) -> str:
    source_module = module_id.strip()
    source_export = export_name.strip()
    if source_module != "toolchain.frontends" or binding_kind != "symbol":
        return ""
    return _FRONTEND_FACADE_RUNTIME_MODULE_BY_SYMBOL.get(source_export, "")


def resolve_import_binding_runtime_module(module_id: str, export_name: str, binding_kind: str) -> str:
    facade_module = _resolve_frontend_facade_runtime_module(module_id, export_name, binding_kind)
    if facade_module != "":
        return facade_module
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


def lookup_target_module_compiler_headers(target: str, module_id: str) -> list[str]:
    artifacts = lookup_target_module_artifacts(target, module_id)
    items = artifacts.get("compiler_headers")
    if not isinstance(items, list):
        return lookup_target_module_public_headers(target, module_id)
    out: list[str] = []
    for item in items:
        if isinstance(item, str) and item != "":
            out.append(item)
    if len(out) > 0:
        return out
    return lookup_target_module_public_headers(target, module_id)


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
            if header.startswith("src/runtime/cpp/generated/"):
                return header
        for header in headers:
            if header.startswith("src/runtime/cpp/native/"):
                return header
    for suffix in (".gen.h", ".ext.h", ".h"):
        for header in headers:
            if header.endswith(suffix):
                return header
    if len(headers) > 0:
        return headers[0]
    return ""


def lookup_target_module_primary_compiler_header(target: str, module_id: str) -> str:
    headers = lookup_target_module_compiler_headers(target, module_id)
    if target == "cpp":
        for header in headers:
            if header.startswith("src/runtime/cpp/generated/"):
                return header
        for header in headers:
            if header.startswith("src/runtime/cpp/native/"):
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
