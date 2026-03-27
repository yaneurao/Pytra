"""Dependency table builder for linked programs.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/global_optimizer.py _build_all_resolved_dependencies (import はしない)。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytra.std.json import JsonVal

if TYPE_CHECKING:
    from toolchain2.link.linker import LinkedModule


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

_TYPE_ID_RUNTIME_NODE_KINDS: set[str] = {
    "IsInstance",
    "IsSubclass",
    "IsSubtype",
}


def _scan_runtime_refs(node: JsonVal, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _scan_runtime_refs(item, out)
        return
    if not isinstance(node, dict):
        return

    runtime_module_id = node.get("runtime_module_id")
    if isinstance(runtime_module_id, str) and runtime_module_id != "":
        out.add(runtime_module_id)
    kind = node.get("kind")
    if isinstance(kind, str) and kind in _TYPE_ID_RUNTIME_NODE_KINDS:
        out.add("pytra.built_in.type_id")

    for value in node.values():
        if isinstance(value, dict):
            _scan_runtime_refs(value, out)
        elif isinstance(value, list):
            _scan_runtime_refs(value, out)


def _binding_dependency_module_id(binding: JsonVal) -> str:
    if not isinstance(binding, dict):
        return ""

    runtime_module_id = binding.get("runtime_module_id")
    runtime_group = binding.get("runtime_group")
    module_id = binding.get("module_id")
    host_only = binding.get("host_only") is True
    binding_kind = binding.get("binding_kind")
    resolved_binding_kind = binding.get("resolved_binding_kind")

    if isinstance(runtime_module_id, str) and runtime_module_id != "":
        if runtime_module_id in _TYPE_ONLY_MODULE_IDS:
            return ""
        if runtime_module_id.startswith("pytra."):
            if host_only and binding_kind != "module" and resolved_binding_kind != "module":
                return ""
            return runtime_module_id
        if isinstance(runtime_group, str) and runtime_group != "" and not host_only:
            return runtime_module_id
        if host_only and (binding_kind == "module" or resolved_binding_kind == "module"):
            return ""
        if not host_only:
            return runtime_module_id
        return ""

    if isinstance(module_id, str) and module_id != "":
        if module_id in _TYPE_ONLY_MODULE_IDS:
            return ""
        if module_id.startswith("pytra.") or not host_only:
            return module_id
    return ""


def _build_resolved_dependencies(
    east_doc: dict[str, JsonVal],
) -> list[str]:
    """Build resolved dependency list for a single module from its EAST3 meta."""
    deps: list[str] = []
    seen: set[str] = set()

    meta_val = east_doc.get("meta")
    if not isinstance(meta_val, dict):
        return deps

    # Prefer resolved runtime binding metadata when present.
    bindings = meta_val.get("import_bindings")
    saw_import_bindings = False
    if isinstance(bindings, list):
        saw_import_bindings = True
        for binding in bindings:
            mod_id = _binding_dependency_module_id(binding)
            if mod_id != "" and mod_id not in seen:
                seen.add(mod_id)
                deps.append(mod_id)

    embedded_runtime_refs: set[str] = set()
    _scan_runtime_refs(east_doc.get("body"), embedded_runtime_refs)
    for runtime_module_id in sorted(embedded_runtime_refs):
        if runtime_module_id != "" and runtime_module_id not in seen:
            seen.add(runtime_module_id)
            deps.append(runtime_module_id)

    # Fallback for older docs that still lack import metadata.
    if not saw_import_bindings:
        body_val = east_doc.get("body")
        if isinstance(body_val, list):
            for stmt in body_val:
                if not isinstance(stmt, dict):
                    continue
                kind = stmt.get("kind")
                if kind == "ImportFrom":
                    mod = stmt.get("module")
                    if isinstance(mod, str) and mod.strip() != "" and mod not in seen:
                        seen.add(mod)
                        deps.append(mod)
                elif kind == "Import":
                    names = stmt.get("names")
                    if isinstance(names, list):
                        for ent in names:
                            if isinstance(ent, dict):
                                name = ent.get("name")
                                if isinstance(name, str) and name.strip() != "" and name not in seen:
                                    seen.add(name)
                                    deps.append(name)

    return sorted(deps)


def build_all_resolved_dependencies(
    modules: list[LinkedModule],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Build resolved_dependencies_v1 and user_module_dependencies_v1 for all modules.

    Returns:
        (resolved_deps_by_module, user_deps_by_module)
    """
    # Collect all user module IDs
    user_module_ids: set[str] = set()
    for module in modules:
        if module.module_kind == "user":
            user_module_ids.add(module.module_id)

    resolved: dict[str, list[str]] = {}
    user_deps: dict[str, list[str]] = {}

    for module in modules:
        if not isinstance(module.east_doc, dict):
            resolved[module.module_id] = []
            user_deps[module.module_id] = []
            continue

        deps = _build_resolved_dependencies(module.east_doc)
        resolved[module.module_id] = deps
        # Filter to only user module dependencies (exclude self)
        u_deps = [d for d in deps if d in user_module_ids and d != module.module_id]
        user_deps[module.module_id] = u_deps

    return resolved, user_deps
