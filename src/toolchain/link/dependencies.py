"""Dependency table builder for linked programs.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/global_optimizer.py _build_all_resolved_dependencies (import はしない)。
"""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.typing import cast

from toolchain.link.shared_types import LinkedModule
from toolchain.compile.jv import jv_is_dict, jv_is_list, jv_dict, jv_list, nd_get_str, nd_get_bool, nd_get_list


_TYPE_ONLY_MODULE_IDS: set[str] = {
    "__future__",
    "typing",
    "pytra.typing",
    "types",
    "pytra.types",
    "dataclasses",
    "pytra.dataclasses",
    "enum",
    "pytra.enum",
    "pytra.std.template",
}

_TYPE_ONLY_SYMBOL_BINDINGS: set[str] = {
    "pytra.std.json::JsonVal",
}

_DEPENDENCIES_TYPE_ID_RUNTIME_NODE_KINDS: set[str] = {
    "IsInstance",
    "IsSubclass",
    "IsSubtype",
    "ClassDef",
}

_DEPENDENCIES_STRING_OP_RUNTIME_SYMBOLS: set[str] = {
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


def is_type_only_dependency_module_id(module_id: str) -> bool:
    return module_id in _TYPE_ONLY_MODULE_IDS


def _dependencies_is_type_only_symbol_binding(binding: JsonVal) -> bool:
    if not jv_is_dict(binding):
        return False
    binding_node: dict[str, JsonVal] = jv_dict(binding)
    module_id: str = nd_get_str(binding_node, "module_id")
    export_name: str = nd_get_str(binding_node, "export_name")
    return module_id != "" and export_name != "" and (module_id + "::" + export_name) in _TYPE_ONLY_SYMBOL_BINDINGS


def _dependencies_scan_runtime_refs(node: JsonVal, out: set[str], *, include_type_id_runtime: bool = True) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _dependencies_scan_runtime_refs(item, out, include_type_id_runtime=include_type_id_runtime)
        return
    if not jv_is_dict(node):
        return

    node_map: dict[str, JsonVal] = jv_dict(node)
    runtime_module_id = _dependencies_normalized_runtime_module_id(node_map)
    if runtime_module_id != "":
        out.add(runtime_module_id)
    kind: str = nd_get_str(node_map, "kind")
    if include_type_id_runtime and kind in _DEPENDENCIES_TYPE_ID_RUNTIME_NODE_KINDS:
        out.add("pytra.built_in.type_id")

    for _key, value in node_map.items():
        if jv_is_dict(value) or jv_is_list(value):
            _dependencies_scan_runtime_refs(value, out, include_type_id_runtime=include_type_id_runtime)


def _dependencies_normalized_runtime_module_id(node: JsonVal) -> str:
    if not jv_is_dict(node):
        return ""
    node_map: dict[str, JsonVal] = jv_dict(node)
    runtime_module_id: str = nd_get_str(node_map, "runtime_module_id")
    if runtime_module_id == "":
        return ""
    if runtime_module_id == "pytra.core.str":
        runtime_symbol: str = nd_get_str(node_map, "runtime_symbol")
        runtime_call: str = nd_get_str(node_map, "runtime_call")
        if runtime_symbol in _DEPENDENCIES_STRING_OP_RUNTIME_SYMBOLS or runtime_call in _DEPENDENCIES_STRING_OP_RUNTIME_SYMBOLS:
            return "pytra.built_in.string_ops"
    return "" + runtime_module_id


def _binding_dependency_module_id(binding: JsonVal) -> str:
    if not jv_is_dict(binding):
        return ""
    if _dependencies_is_type_only_symbol_binding(binding):
        return ""

    binding_node: dict[str, JsonVal] = jv_dict(binding)
    runtime_module_id: str = nd_get_str(binding_node, "runtime_module_id")
    runtime_group: str = nd_get_str(binding_node, "runtime_group")
    module_id: str = nd_get_str(binding_node, "module_id")
    host_only: bool = nd_get_bool(binding_node, "host_only")
    binding_kind: str = nd_get_str(binding_node, "binding_kind")
    resolved_binding_kind: str = nd_get_str(binding_node, "resolved_binding_kind")

    if runtime_module_id != "":
        if is_type_only_dependency_module_id(runtime_module_id):
            return ""
        if runtime_module_id.startswith("pytra."):
            if host_only and binding_kind != "module" and resolved_binding_kind != "module":
                return ""
            return "" + runtime_module_id
        if runtime_group != "" and not host_only:
            return "" + runtime_module_id
        if host_only and (binding_kind == "module" or resolved_binding_kind == "module"):
            return ""
        if not host_only:
            return "" + runtime_module_id
        return ""

    if module_id != "":
        if is_type_only_dependency_module_id(module_id):
            return ""
        if module_id.startswith("pytra.") or not host_only:
            return "" + module_id
    return ""


def _build_resolved_dependencies(
    east_doc: dict[str, JsonVal],
    *,
    target: str = "",
) -> list[str]:
    deps: list[str] = []
    seen: set[str] = set()

    meta_val = east_doc.get("meta")
    if not jv_is_dict(meta_val):
        return deps
    meta_node: dict[str, JsonVal] = jv_dict(meta_val)

    bindings: list[JsonVal] = nd_get_list(meta_node, "import_bindings")
    saw_import_bindings = len(bindings) != 0
    for binding in bindings:
        mod_id = _binding_dependency_module_id(binding)
        if mod_id != "" and mod_id not in seen:
            seen.add(mod_id)
            deps.append(mod_id)

    embedded_runtime_refs: set[str] = set()
    _dependencies_scan_runtime_refs(
        east_doc.get("body"),
        embedded_runtime_refs,
        include_type_id_runtime=(target != "cpp"),
    )
    for runtime_module_id in sorted(embedded_runtime_refs):
        if runtime_module_id != "" and runtime_module_id not in seen:
            seen.add(runtime_module_id)
            deps.append(runtime_module_id)

    if not saw_import_bindings:
        body_val = east_doc.get("body")
        if jv_is_list(body_val):
            for stmt in jv_list(body_val):
                if not jv_is_dict(stmt):
                    continue
                stmt_node: dict[str, JsonVal] = jv_dict(stmt)
                kind: str = nd_get_str(stmt_node, "kind")
                if kind == "ImportFrom":
                    mod: str = nd_get_str(stmt_node, "module")
                    if mod.strip() != "" and mod not in seen:
                        seen.add(mod)
                        deps.append(mod)
                elif kind == "Import":
                    names: list[JsonVal] = nd_get_list(stmt_node, "names")
                    for ent in names:
                        if not jv_is_dict(ent):
                            continue
                        ent_node: dict[str, JsonVal] = jv_dict(ent)
                        name: str = nd_get_str(ent_node, "name")
                        if name.strip() != "" and name not in seen:
                            seen.add(name)
                            deps.append(name)

    return sorted(deps)


def build_all_resolved_dependencies(
    modules: list[LinkedModule],
    *,
    target: str = "",
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    user_module_ids: set[str] = set()
    for module in modules:
        if module.module_kind == "user":
            user_module_ids.add(module.module_id)

    resolved: dict[str, list[str]] = {}
    user_deps: dict[str, list[str]] = {}

    for module in modules:
        deps = _build_resolved_dependencies(module.east_doc, target=target)
        resolved[module.module_id] = deps
        u_deps: list[str] = []
        for dep in deps:
            if dep in user_module_ids and dep != module.module_id:
                u_deps.append(dep)
        user_deps[module.module_id] = u_deps

    return resolved, user_deps
