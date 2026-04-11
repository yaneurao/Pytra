"""Runtime module discovery: transitive closure of import dependencies.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/program_loader.py (import はしない)。
"""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path
from pytra.std import json


_REPO_ROOT = Path.cwd()
_RUNTIME_EAST_ROOT = _REPO_ROOT.joinpath("src").joinpath("runtime").joinpath("east")

_RUNTIME_MODULE_BUCKETS: dict[str, str] = {
    "pytra.built_in.": "built_in",
    "pytra.std.": "std",
    "pytra.utils.": "utils",
}
_RUNTIME_NAMESPACE_MODULES: set[str] = {
    "pytra.built_in",
    "pytra.std",
    "pytra.utils",
    "pytra.core",
}
_RUNTIME_ARTIFACT_OVERRIDES: dict[str, str] = {
    "pytra.core.py_runtime": "core/py_runtime",
}

_TYPE_ID_RUNTIME_NODE_KINDS: set[str] = {
    "IsInstance",
    "IsSubclass",
    "IsSubtype",
    "ClassDef",
}

_STRING_OP_RUNTIME_SYMBOLS: set[str] = {
    "str.strip",
    "str.lstrip",
    "str.rstrip",
    "str.startswith",
    "str.endswith",
    "str.find",
    "str.rfind",
    "str.index",
    "str.replace",
    "str.join",
    "str.split",
    "str.splitlines",
    "str.count",
    "str.upper",
    "str.lower",
    "str.isdigit",
    "str.isalpha",
    "str.isalnum",
}

_TYPE_ONLY_SYMBOL_BINDING_KEYS: set[str] = {
    "pytra.std.json::JsonVal",
}


def _sorted_strings(values: list[str]) -> list[str]:
    out: list[str] = []
    used: set[str] = set()
    while len(out) < len(values):
        found = False
        min_value = ""
        for value in values:
            if value in used:
                continue
            if not found or value < min_value:
                min_value = value
                found = True
        if not found:
            break
        used.add(min_value)
        out.append(min_value)
    return out


def resolve_runtime_module_rel_tail(module_id: str) -> str:
    """Resolve a runtime module_id to its shared runtime-relative path tail."""
    override = _RUNTIME_ARTIFACT_OVERRIDES.get(module_id)
    if isinstance(override, str) and override != "":
        return override
    for prefix, bucket in _RUNTIME_MODULE_BUCKETS.items():
        if module_id.startswith(prefix):
            name = module_id[len(prefix):]
            return bucket + "/" + name.replace(".", "/")
    if module_id != "" and "." not in module_id:
        bare_std = "std/" + module_id
        east_path = _RUNTIME_EAST_ROOT / (bare_std + ".east")
        cpp_header = _REPO_ROOT / "src" / "runtime" / "cpp" / (bare_std + ".h")
        cpp_source = _REPO_ROOT / "src" / "runtime" / "cpp" / (bare_std + ".cpp")
        if east_path.exists() or cpp_header.exists() or cpp_source.exists():
            return bare_std
    return ""


def resolve_runtime_east_path(module_id: str) -> str:
    """Resolve a runtime module_id to its .east file path, or empty string."""
    rel = resolve_runtime_module_rel_tail(module_id)
    if rel != "" and not rel.startswith("core/"):
        east_path = _RUNTIME_EAST_ROOT / (rel + ".east")
        if east_path.exists():
            return str(east_path)
    # Fallback: bare module name → pytra.std.X
    bare_path = _RUNTIME_EAST_ROOT.joinpath("std").joinpath(module_id + ".east")
    if bare_path.exists():
        return str(bare_path)
    return ""


def is_runtime_namespace_module(module_id: str) -> bool:
    return module_id in _RUNTIME_NAMESPACE_MODULES


def is_runtime_internal_helper_module(module_id: str) -> bool:
    return module_id.startswith("pytra.core.") and resolve_runtime_module_rel_tail(module_id) == ""


def _is_explicit_runtime_module(module_id: str) -> bool:
    for prefix in _RUNTIME_MODULE_BUCKETS.keys():
        if module_id.startswith(prefix):
            return True
    return False


def _resolve_runtime_dep_or_fail(module_id: str, *, required: bool = True) -> str:
    """Resolve a runtime dependency path and fail closed for required runtime IDs."""
    east_path = resolve_runtime_east_path(module_id)
    if east_path != "":
        return east_path
    if required and _is_explicit_runtime_module(module_id):
        raise RuntimeError("input_invalid: runtime EAST module not found: " + module_id)
    return ""


def _has_format_spec(node: JsonVal) -> bool:
    """EAST ノードツリーに format_spec を持つ FormattedValue が含まれるか再帰検査。"""
    if isinstance(node, dict):
        if node.get("kind") == "FormattedValue":
            fs = node.get("format_spec")
            if isinstance(fs, str) and fs != "":
                return True
        for v in node.values():
            if _has_format_spec(v):
                return True
    elif isinstance(node, list):
        for item in node:
            if _has_format_spec(item):
                return True
    return False


def _load_east_file(path_str: str) -> dict[str, JsonVal]:
    """Load a .east file as a JSON dict."""
    text = ""
    try:
        text = Path(path_str).read_text(encoding="utf-8")
    except Exception as exc:
        raise RuntimeError("failed to read runtime EAST: " + path_str + ": " + str(exc)) from exc
    obj: JsonVal = None
    try:
        obj = json.loads(text).raw
    except Exception as exc:
        raise RuntimeError("failed to parse runtime EAST: " + path_str + ": " + str(exc)) from exc
    if not isinstance(obj, dict):
        raise RuntimeError("invalid runtime EAST document: " + path_str)
    return obj


def _append_runtime_dep(
    new_deps: list[tuple[str, str]],
    seen_paths: set[str],
    module_id: str,
    *,
    required: bool = True,
) -> None:
    """Resolve and queue a runtime dependency if needed."""
    east_path = _resolve_runtime_dep_or_fail(module_id, required=required)
    if east_path != "" and east_path not in seen_paths:
        new_deps.append((east_path, east_path))


def _is_type_only_symbol_binding(module_id: str, export_name: str, *, target: str = "") -> bool:
    if target == "cpp" and module_id == "pytra.std.json" and export_name == "JsonVal":
        return False
    return (module_id + "::" + export_name) in _TYPE_ONLY_SYMBOL_BINDING_KEYS


def _import_from_is_type_only(module_id: str, names_val: JsonVal, *, target: str = "") -> bool:
    if not isinstance(names_val, list) or len(names_val) == 0:
        return False
    saw_symbol = False
    for ent in names_val:
        if not isinstance(ent, dict):
            return False
        sym = ent.get("name")
        if not isinstance(sym, str) or sym == "":
            return False
        saw_symbol = True
        if not _is_type_only_symbol_binding(module_id, sym, target=target):
            return False
    return saw_symbol


def _scan_runtime_refs(node: JsonVal, out: set[str], *, include_type_id_runtime: bool) -> None:
    """Collect embedded runtime_module_id references from lowered nodes."""
    if isinstance(node, list):
        for item in node:
            _scan_runtime_refs(item, out, include_type_id_runtime=include_type_id_runtime)
        return
    if not isinstance(node, dict):
        return

    kind = node.get("kind")
    runtime_module_id = _normalized_runtime_module_id(node)
    if isinstance(kind, str) and kind != "" and runtime_module_id != "":
        out.add(runtime_module_id)
    if include_type_id_runtime and isinstance(kind, str) and kind in _TYPE_ID_RUNTIME_NODE_KINDS:
        out.add("pytra.built_in.type_id")

    for value in node.values():
        if isinstance(value, (dict, list)):
            _scan_runtime_refs(value, out, include_type_id_runtime=include_type_id_runtime)


def _normalized_runtime_module_id(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    runtime_module_id = node.get("runtime_module_id")
    if not isinstance(runtime_module_id, str) or runtime_module_id == "":
        return ""
    if runtime_module_id == "pytra.core.str":
        runtime_symbol = node.get("runtime_symbol")
        runtime_call = node.get("runtime_call")
        if (
            isinstance(runtime_symbol, str)
            and runtime_symbol in _STRING_OP_RUNTIME_SYMBOLS
        ) or (
            isinstance(runtime_call, str)
            and runtime_call in _STRING_OP_RUNTIME_SYMBOLS
        ):
            return "pytra.built_in.string_ops"
    return runtime_module_id


def discover_runtime_modules(
    module_map: dict[str, dict[str, JsonVal]],
    *,
    target: str = "",
) -> dict[str, dict[str, JsonVal]]:
    """Scan module_map for runtime imports and add their .east files.

    Iterates until no new runtime dependencies are found (transitive closure).
    """
    result: dict[str, dict[str, JsonVal]] = {}
    for module_path in module_map:
        result[module_path] = module_map[module_path]
    seen_paths: set[str] = set(result.keys())

    changed = True
    while changed:
        changed = False
        new_deps: list[tuple[str, str]] = []  # (path_str, path_str)

        for east_path in list(result.keys()):
            east_doc = result[east_path]
            if not isinstance(east_doc, dict):
                continue

            # Scan meta.import_bindings
            meta_val = east_doc.get("meta")
            if isinstance(meta_val, dict):
                bindings_val = meta_val.get("import_bindings")
                if isinstance(bindings_val, list):
                    for binding in bindings_val:
                        if not isinstance(binding, dict):
                            continue
                        export_name = binding.get("export_name")
                        mod_id = binding.get("module_id")
                        if (
                            isinstance(mod_id, str)
                            and mod_id != ""
                            and not (
                                isinstance(export_name, str)
                                and export_name != ""
                                and _is_type_only_symbol_binding(mod_id, export_name, target=target)
                            )
                        ):
                            _append_runtime_dep(new_deps, seen_paths, mod_id, required=True)

            # Scan body for Import/ImportFrom
            body_val = east_doc.get("body")
            if isinstance(body_val, list):
                for stmt in body_val:
                    if not isinstance(stmt, dict):
                        continue
                    kind = stmt.get("kind")
                    if kind == "ImportFrom":
                        mod = stmt.get("module")
                        if isinstance(mod, str) and mod != "":
                            names_val = stmt.get("names")
                            if _import_from_is_type_only(mod, names_val, target=target):
                                continue
                            _append_runtime_dep(new_deps, seen_paths, mod, required=True)
                            # Sub-module imports: from pytra.utils import png → pytra.utils.png
                            if isinstance(names_val, list):
                                for ent in names_val:
                                    if isinstance(ent, dict):
                                        sym = ent.get("name")
                                        if isinstance(sym, str) and sym != "":
                                            sub_mod = mod + "." + sym
                                            _append_runtime_dep(new_deps, seen_paths, sub_mod, required=False)
                    elif kind == "Import":
                        names_val = stmt.get("names")
                        if isinstance(names_val, list):
                            for ent in names_val:
                                if isinstance(ent, dict):
                                    name_val = ent.get("name")
                                    if isinstance(name_val, str):
                                        _append_runtime_dep(new_deps, seen_paths, name_val, required=True)

            # Detect implicit format_value dependency from f-string
            if _has_format_spec(east_doc):
                _append_runtime_dep(new_deps, seen_paths, "pytra.built_in.format_value", required=True)

            # Runtime EAST generated by older paths may omit builtin imports from
            # import_bindings while still carrying lowered runtime_module_id refs.
            embedded_runtime_refs: set[str] = set()
            _scan_runtime_refs(
                east_doc,
                embedded_runtime_refs,
                include_type_id_runtime=(target != "cpp"),
            )
            runtime_refs_sorted = _sorted_strings(list(embedded_runtime_refs))
            for runtime_module_id in runtime_refs_sorted:
                _append_runtime_dep(new_deps, seen_paths, runtime_module_id, required=True)

        for path_str, _ in new_deps:
            if path_str in seen_paths:
                continue
            seen_paths.add(path_str)
            doc = _load_east_file(path_str)
            result[path_str] = doc
            changed = True

    return result
