"""Post-link pass: resolve module attribute types from export tables.

Collects top-level variable/constant/function type information from each
module's EAST3 body, then updates Attribute nodes whose resolved_type is
unknown by looking up the export table of the owner module.
"""

from __future__ import annotations

from typing import Any


def _safe_str(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _collect_module_exports(east_doc: dict[str, Any]) -> dict[str, str]:
    """Collect top-level exported names and their types from a module's EAST3.

    Returns ``{name: type}`` for variables, constants, and functions.
    """
    exports: dict[str, str] = {}
    body = east_doc.get("body")
    if not isinstance(body, list):
        return exports
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind", "")
        if kind in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            if isinstance(target, dict) and target.get("kind") == "Name":
                name = _safe_str(target.get("id"))
                if name == "":
                    continue
                # Try decl_type, annotation, target resolved_type, value resolved_type
                t = _safe_str(stmt.get("decl_type"))
                if t in ("", "unknown"):
                    t = _safe_str(stmt.get("annotation"))
                if t in ("", "unknown"):
                    t = _safe_str(target.get("resolved_type"))
                if t in ("", "unknown"):
                    value = stmt.get("value")
                    if isinstance(value, dict):
                        t = _safe_str(value.get("resolved_type"))
                if t not in ("", "unknown"):
                    exports[name] = t
        elif kind == "FunctionDef":
            name = _safe_str(stmt.get("name"))
            ret_type = _safe_str(stmt.get("return_type"))
            if name != "" and ret_type not in ("", "unknown"):
                # Store as callable with return type (for future use)
                exports[name] = "callable:" + ret_type
    return exports


def _build_module_export_table(
    modules: tuple[Any, ...],
) -> dict[str, dict[str, str]]:
    """Build export tables for all modules.

    Returns ``{module_id: {name: type}}``.
    """
    table: dict[str, dict[str, str]] = {}
    for module in modules:
        module_id = getattr(module, "module_id", "")
        east_doc = getattr(module, "east_doc", None)
        if not isinstance(east_doc, dict) or module_id == "":
            continue
        exports = _collect_module_exports(east_doc)
        if len(exports) > 0:
            table[module_id] = exports
    return table


def _build_import_module_map(east_doc: dict[str, Any]) -> dict[str, str]:
    """Build {local_name: module_id} from import_bindings in a module's meta."""
    out: dict[str, str] = {}
    meta = east_doc.get("meta")
    if not isinstance(meta, dict):
        return out

    # Try import_resolution.bindings first, fallback to import_bindings
    resolution = meta.get("import_resolution")
    binds = None
    if isinstance(resolution, dict):
        binds = resolution.get("bindings")
    if not isinstance(binds, list):
        binds = meta.get("import_bindings")
    if not isinstance(binds, list):
        return out

    for ent in binds:
        if not isinstance(ent, dict):
            continue
        binding_kind = _safe_str(ent.get("binding_kind"))
        local_name = _safe_str(ent.get("local_name"))
        module_id = _safe_str(ent.get("module_id"))
        export_name = _safe_str(ent.get("export_name"))
        if local_name == "" or module_id == "":
            continue
        if binding_kind == "module":
            out[local_name] = module_id
        elif binding_kind == "symbol" and export_name != "":
            # from pytra.std import os_path as path → path → pytra.std.os_path
            out[local_name] = module_id + "." + export_name
    return out


def _resolve_attribute_types(
    node: Any,
    import_map: dict[str, str],
    export_table: dict[str, dict[str, str]],
) -> int:
    """Walk EAST3 and resolve Attribute nodes whose resolved_type is unknown.

    Returns the number of resolved attributes.
    """
    count = 0
    if isinstance(node, list):
        for item in node:
            count += _resolve_attribute_types(item, import_map, export_table)
        return count
    if not isinstance(node, dict):
        return 0
    nd: dict[str, Any] = node

    if nd.get("kind") == "Attribute":
        resolved = _safe_str(nd.get("resolved_type"))
        if resolved in ("", "unknown"):
            value = nd.get("value")
            attr = _safe_str(nd.get("attr"))
            if isinstance(value, dict) and value.get("kind") == "Name" and attr != "":
                owner_name = _safe_str(value.get("id"))
                owner_module = import_map.get(owner_name, "")
                if owner_module != "":
                    exports = export_table.get(owner_module, {})
                    attr_type = exports.get(attr, "")
                    if attr_type != "":
                        # Strip "callable:" prefix for function return types
                        if attr_type.startswith("callable:"):
                            # For attribute access on a function, keep unknown
                            # (it's a function, not a value)
                            pass
                        else:
                            nd["resolved_type"] = attr_type
                            count += 1

    for v in nd.values():
        if isinstance(v, (dict, list)):
            count += _resolve_attribute_types(v, import_map, export_table)
    return count


def resolve_module_attribute_types(modules: tuple[Any, ...]) -> int:
    """Post-link pass: resolve module attribute types across all modules.

    Returns total number of resolved attributes.
    """
    export_table = _build_module_export_table(modules)
    if len(export_table) == 0:
        return 0

    total = 0
    for module in modules:
        east_doc = getattr(module, "east_doc", None)
        if not isinstance(east_doc, dict):
            continue
        import_map = _build_import_module_map(east_doc)
        if len(import_map) == 0:
            continue
        total += _resolve_attribute_types(east_doc, import_map, export_table)
    return total
