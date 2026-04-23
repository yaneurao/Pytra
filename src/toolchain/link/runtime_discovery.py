"""Runtime module discovery: transitive closure of import dependencies.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/program_loader.py (import はしない)。
"""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path
from pytra.std import json
from toolchain.compile.jv import jv_str, jv_is_dict, jv_is_list, jv_dict, jv_list


def _repo_root() -> Path:
    cwd = Path.cwd()
    if cwd.joinpath("src").exists():
        return cwd
    if cwd.joinpath("Pytra").joinpath("src").exists():
        return cwd.joinpath("Pytra")
    return cwd


_REPO_ROOT = _repo_root()
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
    override = _RUNTIME_ARTIFACT_OVERRIDES.get(module_id, "")
    if override != "":
        return override
    for prefix, bucket in _RUNTIME_MODULE_BUCKETS.items():
        if module_id.startswith(prefix):
            name = module_id[len(prefix):]
            return bucket + "/" + name.replace(".", "/")
    if module_id != "" and "." not in module_id:
        bare_std = "std/" + module_id
        east_path = _RUNTIME_EAST_ROOT.joinpath(bare_std + ".east")
        cpp_header = _REPO_ROOT.joinpath("src").joinpath("runtime").joinpath("cpp").joinpath(bare_std + ".h")
        cpp_source = _REPO_ROOT.joinpath("src").joinpath("runtime").joinpath("cpp").joinpath(bare_std + ".cpp")
        if east_path.exists() or cpp_header.exists() or cpp_source.exists():
            return bare_std
    return ""


def resolve_runtime_east_path(module_id: str) -> str:
    """Resolve a runtime module_id to its .east file path, or empty string."""
    rel = resolve_runtime_module_rel_tail(module_id)
    if rel != "" and not rel.startswith("core/"):
        east_path = _RUNTIME_EAST_ROOT.joinpath(rel + ".east")
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
    if jv_is_dict(node):
        node_dict = jv_dict(node)
        if jv_str(node_dict.get("kind")) == "FormattedValue":
            fs = "" + jv_str(node_dict.get("format_spec"))
            if fs != "":
                return True
        for key in node_dict.keys():
            if _has_format_spec(node_dict.get(key)):
                return True
    elif jv_is_list(node):
        for item in jv_list(node):
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
    if not jv_is_dict(obj):
        raise RuntimeError("invalid runtime EAST document: " + path_str)
    return jv_dict(obj)


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
    if not jv_is_list(names_val):
        return False
    names = jv_list(names_val)
    if len(names) == 0:
        return False
    saw_symbol = False
    for ent in names:
        if not jv_is_dict(ent):
            return False
        sym = "" + jv_str(jv_dict(ent).get("name"))
        if sym == "":
            return False
        saw_symbol = True
        if not _is_type_only_symbol_binding(module_id, sym, target=target):
            return False
    return saw_symbol


def _scan_runtime_refs(node: JsonVal, out: set[str], *, include_type_id_runtime: bool) -> None:
    """Collect embedded runtime_module_id references from lowered nodes."""
    if jv_is_list(node):
        for item in jv_list(node):
            _scan_runtime_refs(item, out, include_type_id_runtime=include_type_id_runtime)
        return
    if not jv_is_dict(node):
        return

    node_dict = jv_dict(node)
    kind = "" + jv_str(node_dict.get("kind"))
    runtime_module_id = _normalized_runtime_module_id(node_dict)
    if kind != "" and runtime_module_id != "":
        out.add(runtime_module_id)
    if include_type_id_runtime and kind in _TYPE_ID_RUNTIME_NODE_KINDS:
        out.add("pytra.built_in.type_id")

    for key in node_dict.keys():
        value = node_dict.get(key)
        if jv_is_dict(value) or jv_is_list(value):
            _scan_runtime_refs(value, out, include_type_id_runtime=include_type_id_runtime)


def _normalized_runtime_module_id(node: dict[str, JsonVal]) -> str:
    runtime_module_id = "" + jv_str(node.get("runtime_module_id"))
    if runtime_module_id == "":
        return ""
    if runtime_module_id == "pytra.core.str":
        runtime_symbol = "" + jv_str(node.get("runtime_symbol"))
        runtime_call = "" + jv_str(node.get("runtime_call"))
        if runtime_symbol in _STRING_OP_RUNTIME_SYMBOLS or runtime_call in _STRING_OP_RUNTIME_SYMBOLS:
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

            # Scan meta.import_bindings
            meta_val = east_doc.get("meta")
            if jv_is_dict(meta_val):
                meta = jv_dict(meta_val)
                bindings_val = meta.get("import_bindings")
                if jv_is_list(bindings_val):
                    for binding_val in jv_list(bindings_val):
                        if not jv_is_dict(binding_val):
                            continue
                        binding = jv_dict(binding_val)
                        export_name = binding.get("export_name")
                        mod_id = binding.get("module_id")
                        mod_id_text = "" + jv_str(mod_id)
                        export_name_text = "" + jv_str(export_name)
                        if (
                            mod_id_text != ""
                            and not (
                                export_name_text != ""
                                and _is_type_only_symbol_binding(mod_id_text, export_name_text, target=target)
                            )
                        ):
                            _append_runtime_dep(new_deps, seen_paths, mod_id_text, required=True)

            # Scan body for Import/ImportFrom
            body_val = east_doc.get("body")
            if jv_is_list(body_val):
                for stmt_val in jv_list(body_val):
                    if not jv_is_dict(stmt_val):
                        continue
                    stmt = jv_dict(stmt_val)
                    kind_text = "" + jv_str(stmt.get("kind"))
                    if kind_text == "ImportFrom":
                        mod = stmt.get("module")
                        mod_text = "" + jv_str(mod)
                        if mod_text != "":
                            names_val: JsonVal = stmt.get("names")
                            if _import_from_is_type_only(mod_text, names_val, target=target):
                                continue
                            _append_runtime_dep(new_deps, seen_paths, mod_text, required=True)
                            # Sub-module imports: from pytra.utils import png → pytra.utils.png
                            if jv_is_list(names_val):
                                for ent_val in jv_list(names_val):
                                    if jv_is_dict(ent_val):
                                        ent: dict[str, JsonVal] = jv_dict(ent_val)
                                        sym = "" + jv_str(ent.get("name"))
                                        if sym != "":
                                            sub_mod = mod_text + "." + sym
                                            _append_runtime_dep(new_deps, seen_paths, sub_mod, required=False)
                    elif kind_text == "Import":
                        names_val: JsonVal = stmt.get("names")
                        if jv_is_list(names_val):
                            for ent_val in jv_list(names_val):
                                if jv_is_dict(ent_val):
                                    ent: dict[str, JsonVal] = jv_dict(ent_val)
                                    name_val = "" + jv_str(ent.get("name"))
                                    if name_val != "":
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
