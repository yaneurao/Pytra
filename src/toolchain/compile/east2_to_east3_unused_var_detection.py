"""EAST3 unused variable detection pass.

Walks each FunctionDef and marks variables (Assign target / VarDecl)
that are assigned but never referenced afterwards with ``unused: true``.
Emitters can use this flag to suppress unused-variable warnings/errors.
"""

from __future__ import annotations

from typing import Any


def _collect_referenced_names(node: Any, exclude_assign_targets: bool = True) -> set[str]:
    """Collect all Name.id values referenced in *node* (read positions)."""
    out: set[str] = set()
    _walk_refs(node, out, exclude_assign_targets)
    return out


def _walk_refs(node: Any, out: set[str], exclude_targets: bool) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_refs(item, out, exclude_targets)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    kind = nd.get("kind", "")

    if kind == "Name":
        name = nd.get("id")
        if isinstance(name, str) and name != "":
            out.add(name)
    elif kind in ("Assign", "AnnAssign", "AugAssign"):
        # Don't count the target as a reference (it's a write)
        # But DO count the value and any nested references
        value = nd.get("value")
        if isinstance(value, (dict, list)):
            _walk_refs(value, out, exclude_targets)
        # For AugAssign, the target is also read
        if kind == "AugAssign":
            target = nd.get("target")
            if isinstance(target, dict) and target.get("kind") == "Name":
                name = target.get("id")
                if isinstance(name, str) and name != "":
                    out.add(name)
        return  # Don't recurse into target for Assign/AnnAssign

    for value in nd.values():
        if isinstance(value, (dict, list)):
            _walk_refs(value, out, exclude_targets)


def _mark_unused_in_function(func: dict[str, Any]) -> None:
    """Mark unused variables in a FunctionDef body."""
    body = func.get("body")
    if not isinstance(body, list):
        return

    # Collect all referenced names in the entire body
    all_refs: set[str] = set()
    _walk_refs(body, all_refs, exclude_targets=True)

    # Also include parameter names as "used" (they're declared externally)
    arg_order = func.get("arg_order")
    if isinstance(arg_order, list):
        for arg in arg_order:
            if isinstance(arg, str):
                all_refs.add(arg)

    # Walk body and mark unused assignments
    _mark_unused_in_stmts(body, all_refs)


def _mark_unused_in_stmts(stmts: list[Any], all_refs: set[str]) -> None:
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind", "")
        if kind == "VarDecl":
            name = stmt.get("name")
            if isinstance(name, str) and name != "" and name not in all_refs:
                stmt["unused"] = True
        elif kind in ("Assign", "AnnAssign"):
            target = stmt.get("target")
            if isinstance(target, dict) and target.get("kind") == "Name":
                name = target.get("id")
                if isinstance(name, str) and name != "" and name not in all_refs:
                    stmt["unused"] = True
            elif isinstance(target, dict) and target.get("kind") == "Tuple":
                # Mark individual tuple elements as unused
                elements = target.get("elements")
                if isinstance(elements, list):
                    for elem in elements:
                        if isinstance(elem, dict) and elem.get("kind") == "Name":
                            elem_name = elem.get("id")
                            if isinstance(elem_name, str) and elem_name != "" and elem_name not in all_refs:
                                elem["unused"] = True
        # Recurse into nested blocks
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                _mark_unused_in_stmts(nested, all_refs)
        if kind == "Try":
            handlers = stmt.get("handlers")
            if isinstance(handlers, list):
                for h in handlers:
                    if isinstance(h, dict):
                        hbody = h.get("body")
                        if isinstance(hbody, list):
                            _mark_unused_in_stmts(hbody, all_refs)


def _walk_and_detect(node: Any) -> None:
    """Walk EAST3 and detect unused variables in each FunctionDef."""
    if isinstance(node, list):
        for item in node:
            _walk_and_detect(item)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    kind = nd.get("kind", "")
    if kind == "FunctionDef":
        _mark_unused_in_function(nd)
    # Recurse
    for value in nd.values():
        if isinstance(value, (dict, list)):
            _walk_and_detect(value)


def detect_unused_variables(module: dict[str, Any]) -> dict[str, Any]:
    """Top-level entry: detect unused variables in an EAST3 Module.

    Mutates *module* in place and returns it.
    """
    _walk_and_detect(module)
    return module
