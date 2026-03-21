"""Block-scope variable hoist pass for EAST3 lowering.

Python does not have block scoping: variables assigned inside if/else/for/while
are visible in the enclosing function scope.  Block-scoped target languages
(C++, Dart, Zig, Julia, …) require the declaration to appear *before* the
block.  This module inserts ``VarDecl`` nodes at the correct scope level so
that every downstream emitter receives a hoist-ready EAST3 without needing
language-specific analysis.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# helpers – name collection
# ---------------------------------------------------------------------------

def _stmt_kind(node: Any) -> str:
    if isinstance(node, dict):
        nd: dict[str, Any] = node
        kind = nd.get("kind")
        if isinstance(kind, str):
            return kind
    return ""


def _collect_assigned_names_in_stmts(stmts: list[Any]) -> dict[str, str]:
    """Return ``{name: type}`` for every ``Name`` target assigned in *stmts*.

    Recurses into nested blocks (if/for/while) so that deeply-nested
    assignments are surfaced.
    """
    out: dict[str, str] = {}
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        sd: dict[str, Any] = stmt
        kind = _stmt_kind(sd)

        if kind in ("Assign", "AnnAssign"):
            _collect_assign_target_names(sd, out)
        elif kind == "If":
            body = sd.get("body")
            orelse = sd.get("orelse")
            if isinstance(body, list):
                sub = _collect_assigned_names_in_stmts(body)
                _merge_name_types(out, sub)
            if isinstance(orelse, list):
                sub = _collect_assigned_names_in_stmts(orelse)
                _merge_name_types(out, sub)
        elif kind in ("While", "For", "ForRange", "ForCore"):
            body = sd.get("body")
            orelse = sd.get("orelse")
            if isinstance(body, list):
                sub = _collect_assigned_names_in_stmts(body)
                _merge_name_types(out, sub)
            if isinstance(orelse, list):
                sub = _collect_assigned_names_in_stmts(orelse)
                _merge_name_types(out, sub)
    return out


def _collect_assign_target_names(stmt: dict[str, Any], out: dict[str, str]) -> None:
    """Extract Name target(s) and their types from an Assign/AnnAssign."""
    target = stmt.get("target")
    if isinstance(target, dict):
        td: dict[str, Any] = target
        tkind = td.get("kind")
        if tkind == "Name":
            name = td.get("id")
            if isinstance(name, str) and name != "":
                if name not in out:
                    out[name] = _resolve_assign_type(stmt)
        elif tkind == "Tuple":
            _collect_tuple_target_names(td, stmt, out)
    targets = stmt.get("targets")
    if isinstance(targets, list):
        for t in targets:
            if isinstance(t, dict):
                tgd: dict[str, Any] = t
                if tgd.get("kind") == "Name":
                    name = tgd.get("id")
                    if isinstance(name, str) and name != "":
                        if name not in out:
                            out[name] = _resolve_assign_type(stmt)
                elif tgd.get("kind") == "Tuple":
                    _collect_tuple_target_names(tgd, stmt, out)


def _collect_tuple_target_names(
    tuple_node: dict[str, Any],
    stmt: dict[str, Any],
    out: dict[str, str],
) -> None:
    """Extract Name elements from a Tuple target."""
    elements = tuple_node.get("elements")
    if not isinstance(elements, list):
        return
    # Try to get element types from the value type
    value_type = _resolve_assign_type(stmt)
    elem_types: list[str] = []
    if value_type.startswith("tuple[") and value_type.endswith("]"):
        inner = value_type[6:-1]
        elem_types = _split_generic_types(inner)

    for i, elem in enumerate(elements):
        if not isinstance(elem, dict):
            continue
        ed: dict[str, Any] = elem
        if ed.get("kind") == "Name":
            name = ed.get("id")
            if isinstance(name, str) and name != "":
                elem_t = ""
                if i < len(elem_types):
                    elem_t = elem_types[i]
                if elem_t == "":
                    rt = ed.get("resolved_type")
                    if isinstance(rt, str):
                        elem_t = rt
                if name not in out:
                    out[name] = elem_t


def _split_generic_types(type_name: str) -> list[str]:
    """Split comma-separated generic type args respecting bracket depth."""
    parts: list[str] = []
    cur = ""
    depth = 0
    for ch in type_name:
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            part = cur.strip()
            if part != "":
                parts.append(part)
            cur = ""
        else:
            cur += ch
    tail = cur.strip()
    if tail != "":
        parts.append(tail)
    return parts


def _resolve_assign_type(stmt: dict[str, Any]) -> str:
    """Best-effort type for an Assign/AnnAssign statement."""
    decl_type = stmt.get("decl_type")
    if isinstance(decl_type, str) and decl_type.strip() not in ("", "unknown"):
        return decl_type.strip()
    annotation = stmt.get("annotation")
    if isinstance(annotation, str) and annotation.strip() not in ("", "unknown"):
        return annotation.strip()
    target = stmt.get("target")
    if isinstance(target, dict):
        td: dict[str, Any] = target
        rt = td.get("resolved_type")
        if isinstance(rt, str) and rt.strip() not in ("", "unknown"):
            return rt.strip()
    return ""


def _merge_name_types(target: dict[str, str], source: dict[str, str]) -> None:
    """Merge *source* into *target*, keeping existing entries."""
    for name, typ in source.items():
        if name not in target:
            target[name] = typ
        elif target[name] == "" and typ != "":
            target[name] = typ


def _collect_referenced_names(node: Any) -> set[str]:
    """Return all ``Name.id`` values referenced in *node* (read positions)."""
    out: set[str] = set()
    _walk_referenced_names(node, out)
    return out


def _walk_referenced_names(node: Any, out: set[str]) -> None:
    if isinstance(node, list):
        nl: list[Any] = node
        for item in nl:
            _walk_referenced_names(item, out)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    kind = nd.get("kind")
    if kind == "Name":
        name = nd.get("id")
        if isinstance(name, str) and name != "":
            out.add(name)
    for value in nd.values():
        if isinstance(value, (dict, list)):
            _walk_referenced_names(value, out)


def _collect_scope_declared_names(stmts: list[Any], up_to: int) -> set[str]:
    """Return names declared/assigned at this scope level before index *up_to*.

    Only considers direct assignments (not inside nested blocks), plus
    function parameters are tracked via FunctionDef arg_order.
    """
    out: set[str] = set()
    for i in range(up_to):
        stmt = stmts[i]
        if not isinstance(stmt, dict):
            continue
        sd: dict[str, Any] = stmt
        kind = _stmt_kind(sd)
        if kind in ("Assign", "AnnAssign"):
            target = sd.get("target")
            if isinstance(target, dict):
                td: dict[str, Any] = target
                if td.get("kind") == "Name":
                    name = td.get("id")
                    if isinstance(name, str) and name != "":
                        out.add(name)
                elif td.get("kind") == "Tuple":
                    _collect_tuple_names_flat(td, out)
            targets = sd.get("targets")
            if isinstance(targets, list):
                for t in targets:
                    if isinstance(t, dict):
                        tgd: dict[str, Any] = t
                        if tgd.get("kind") == "Name":
                            name = tgd.get("id")
                            if isinstance(name, str) and name != "":
                                out.add(name)
                        elif tgd.get("kind") == "Tuple":
                            _collect_tuple_names_flat(tgd, out)
        elif kind == "VarDecl":
            name = sd.get("name")
            if isinstance(name, str) and name != "":
                out.add(name)
    return out


def _collect_tuple_names_flat(tuple_node: dict[str, Any], out: set[str]) -> None:
    elements = tuple_node.get("elements")
    if not isinstance(elements, list):
        return
    for elem in elements:
        if isinstance(elem, dict):
            ed: dict[str, Any] = elem
            if ed.get("kind") == "Name":
                name = ed.get("id")
                if isinstance(name, str) and name != "":
                    out.add(name)


# ---------------------------------------------------------------------------
# VarDecl node construction
# ---------------------------------------------------------------------------

def _make_var_decl(name: str, var_type: str) -> dict[str, Any]:
    """Create a ``VarDecl`` node for a hoisted variable."""
    out: dict[str, Any] = {
        "kind": "VarDecl",
        "name": name,
        "type": var_type if var_type != "" else "object",
        "hoisted": True,
    }
    return out


# ---------------------------------------------------------------------------
# is_reassign marking
# ---------------------------------------------------------------------------

def _mark_reassign_in_stmts(stmts: list[Any], hoisted_names: set[str]) -> list[Any]:
    """Deep-copy–free walk: set ``is_reassign`` on Assign/AnnAssign whose
    target is a hoisted name.  Also recurses into nested blocks.
    """
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        sd: dict[str, Any] = stmt
        kind = _stmt_kind(sd)
        if kind in ("Assign", "AnnAssign"):
            target = sd.get("target")
            if isinstance(target, dict):
                td: dict[str, Any] = target
                if td.get("kind") == "Name":
                    name = td.get("id")
                    if isinstance(name, str) and name in hoisted_names:
                        sd["is_reassign"] = True
                elif td.get("kind") == "Tuple":
                    _mark_tuple_reassign(td, hoisted_names, sd)
        if kind == "If":
            body = sd.get("body")
            orelse = sd.get("orelse")
            if isinstance(body, list):
                _mark_reassign_in_stmts(body, hoisted_names)
            if isinstance(orelse, list):
                _mark_reassign_in_stmts(orelse, hoisted_names)
        elif kind in ("While", "For", "ForRange", "ForCore"):
            body = sd.get("body")
            orelse = sd.get("orelse")
            if isinstance(body, list):
                _mark_reassign_in_stmts(body, hoisted_names)
            if isinstance(orelse, list):
                _mark_reassign_in_stmts(orelse, hoisted_names)
    return stmts


def _mark_tuple_reassign(
    tuple_node: dict[str, Any],
    hoisted_names: set[str],
    stmt: dict[str, Any],
) -> None:
    """If any element of a Tuple target is hoisted, mark the stmt."""
    elements = tuple_node.get("elements")
    if not isinstance(elements, list):
        return
    for elem in elements:
        if isinstance(elem, dict):
            ed: dict[str, Any] = elem
            if ed.get("kind") == "Name":
                name = ed.get("id")
                if isinstance(name, str) and name in hoisted_names:
                    stmt["is_reassign"] = True
                    return


# ---------------------------------------------------------------------------
# block-internal assigned names (only names first assigned *inside* a block)
# ---------------------------------------------------------------------------

def _collect_block_assigned_names(stmt: dict[str, Any]) -> dict[str, str]:
    """For a block-creating statement (If/While/For/ForRange/ForCore), return
    names assigned inside any of its bodies.
    """
    kind = _stmt_kind(stmt)
    all_names: dict[str, str] = {}
    if kind == "If":
        body = stmt.get("body")
        orelse = stmt.get("orelse")
        if isinstance(body, list):
            sub = _collect_assigned_names_in_stmts(body)
            _merge_name_types(all_names, sub)
        if isinstance(orelse, list):
            sub = _collect_assigned_names_in_stmts(orelse)
            _merge_name_types(all_names, sub)
    elif kind in ("While", "For", "ForRange", "ForCore"):
        body = stmt.get("body")
        orelse = stmt.get("orelse")
        if isinstance(body, list):
            sub = _collect_assigned_names_in_stmts(body)
            _merge_name_types(all_names, sub)
        if isinstance(orelse, list):
            sub = _collect_assigned_names_in_stmts(orelse)
            _merge_name_types(all_names, sub)
    return all_names


def _collect_multi_branch_assigned_names(if_stmt: dict[str, Any]) -> set[str]:
    """For an If statement, return names assigned in more than one branch.

    Handles if/elif/else chains (where else contains a nested If).
    A variable assigned in multiple branches needs hoisting because each
    branch creates a separate block scope in target languages.
    """
    branches: list[set[str]] = []

    def _walk_if_chain(node: dict[str, Any]) -> None:
        body = node.get("body")
        orelse = node.get("orelse")
        if isinstance(body, list):
            branch_names: set[str] = set()
            body_assigned = _collect_assigned_names_in_stmts(body)
            for name in body_assigned:
                branch_names.add(name)
            branches.append(branch_names)
        if isinstance(orelse, list) and len(orelse) == 1:
            nested = orelse[0]
            if isinstance(nested, dict) and _stmt_kind(nested) == "If":
                _walk_if_chain(nested)
                return
        if isinstance(orelse, list) and len(orelse) > 0:
            branch_names = set()
            orelse_assigned = _collect_assigned_names_in_stmts(orelse)
            for name in orelse_assigned:
                branch_names.add(name)
            branches.append(branch_names)

    _walk_if_chain(if_stmt)

    if len(branches) < 2:
        return set()

    # Names that appear in at least 2 branches
    count: dict[str, int] = {}
    for branch in branches:
        for name in branch:
            count[name] = count.get(name, 0) + 1
    return {name for name, c in count.items() if c >= 2}


# ---------------------------------------------------------------------------
# main hoist pass – operates on a single statement list
# ---------------------------------------------------------------------------

def _hoist_block_scope_vars_in_stmt_list(stmts: list[Any], param_names: set[str]) -> list[Any]:
    """Process *stmts* and return a new list with ``VarDecl`` nodes inserted
    before blocks that assign variables used later.

    *param_names* contains function parameter names (always in scope).
    """
    result: list[Any] = []
    already_declared: set[str] = set(param_names)

    for i in range(len(stmts)):
        stmt = stmts[i]
        if not isinstance(stmt, dict):
            result.append(stmt)
            continue
        sd: dict[str, Any] = stmt
        kind = _stmt_kind(sd)

        # Track names declared at this scope level
        if kind in ("Assign", "AnnAssign"):
            target = sd.get("target")
            if isinstance(target, dict):
                td: dict[str, Any] = target
                if td.get("kind") == "Name":
                    name = td.get("id")
                    if isinstance(name, str) and name != "":
                        already_declared.add(name)
                elif td.get("kind") == "Tuple":
                    _collect_tuple_names_flat(td, already_declared)
            targets = sd.get("targets")
            if isinstance(targets, list):
                for t in targets:
                    if isinstance(t, dict):
                        tgd: dict[str, Any] = t
                        if tgd.get("kind") == "Name":
                            name = tgd.get("id")
                            if isinstance(name, str) and name != "":
                                already_declared.add(name)
                        elif tgd.get("kind") == "Tuple":
                            _collect_tuple_names_flat(tgd, already_declared)
            result.append(stmt)
            continue

        if kind == "VarDecl":
            name = sd.get("name")
            if isinstance(name, str) and name != "":
                already_declared.add(name)
            result.append(stmt)
            continue

        if kind not in ("If", "While", "For", "ForRange", "ForCore"):
            result.append(stmt)
            continue

        # This is a block-creating statement.
        # 1. Collect names assigned inside the block
        block_assigned = _collect_block_assigned_names(sd)

        # 2. Collect names referenced after this block
        names_used_after: set[str] = set()
        for j in range(i + 1, len(stmts)):
            refs = _collect_referenced_names(stmts[j])
            names_used_after |= refs

        # 2b. For If statements, find names assigned in multiple branches.
        #     These need hoisting even if not used after the block, because
        #     each branch creates a separate block scope in target languages.
        names_in_multiple_branches: set[str] = set()
        if kind == "If":
            names_in_multiple_branches = _collect_multi_branch_assigned_names(sd)

        # 3. Determine names that need hoisting
        to_hoist: dict[str, str] = {}
        for name, var_type in block_assigned.items():
            if name in already_declared:
                continue
            if name not in names_used_after and name not in names_in_multiple_branches:
                continue
            to_hoist[name] = var_type

        # 4. Insert VarDecl nodes before the block
        for name in sorted(to_hoist.keys()):
            var_decl = _make_var_decl(name, to_hoist[name])
            result.append(var_decl)
            already_declared.add(name)

        # 5. Mark assignments inside the block as is_reassign
        if to_hoist:
            hoisted_set = set(to_hoist.keys())
            _mark_reassign_in_stmts_for_block(sd, hoisted_set)

        # 6. Recurse into the block's bodies
        _recurse_hoist_into_block(sd, already_declared)

        result.append(stmt)

    return result


def _mark_reassign_in_stmts_for_block(block_stmt: dict[str, Any], hoisted_names: set[str]) -> None:
    """Mark Assign/AnnAssign inside a block statement as is_reassign."""
    kind = _stmt_kind(block_stmt)
    if kind == "If":
        body = block_stmt.get("body")
        orelse = block_stmt.get("orelse")
        if isinstance(body, list):
            _mark_reassign_in_stmts(body, hoisted_names)
        if isinstance(orelse, list):
            _mark_reassign_in_stmts(orelse, hoisted_names)
    elif kind in ("While", "For", "ForRange", "ForCore"):
        body = block_stmt.get("body")
        orelse = block_stmt.get("orelse")
        if isinstance(body, list):
            _mark_reassign_in_stmts(body, hoisted_names)
        if isinstance(orelse, list):
            _mark_reassign_in_stmts(orelse, hoisted_names)


def _recurse_hoist_into_block(block_stmt: dict[str, Any], parent_declared: set[str]) -> None:
    """Recursively apply hoist to nested bodies within a block statement."""
    kind = _stmt_kind(block_stmt)
    if kind == "If":
        body = block_stmt.get("body")
        orelse = block_stmt.get("orelse")
        if isinstance(body, list):
            block_stmt["body"] = _hoist_block_scope_vars_in_stmt_list(body, parent_declared)
        if isinstance(orelse, list):
            block_stmt["orelse"] = _hoist_block_scope_vars_in_stmt_list(orelse, parent_declared)
    elif kind in ("While", "For", "ForRange", "ForCore"):
        body = block_stmt.get("body")
        orelse = block_stmt.get("orelse")
        if isinstance(body, list):
            block_stmt["body"] = _hoist_block_scope_vars_in_stmt_list(body, parent_declared)
        if isinstance(orelse, list):
            block_stmt["orelse"] = _hoist_block_scope_vars_in_stmt_list(orelse, parent_declared)


# ---------------------------------------------------------------------------
# function body processing
# ---------------------------------------------------------------------------

def _collect_function_param_names(func: dict[str, Any]) -> set[str]:
    """Collect parameter names from a FunctionDef node."""
    params: set[str] = set()
    arg_order = func.get("arg_order")
    if isinstance(arg_order, list):
        for arg in arg_order:
            if isinstance(arg, str) and arg != "":
                params.add(arg)
    # Legacy: some EAST payloads use "args" list of dicts
    args = func.get("args")
    if isinstance(args, list):
        for arg in args:
            if isinstance(arg, dict):
                ad: dict[str, Any] = arg
                name = ad.get("arg")
                if isinstance(name, str) and name != "":
                    params.add(name)
    return params


def _hoist_in_function_def(func: dict[str, Any]) -> None:
    """Apply hoist pass to a FunctionDef body."""
    body = func.get("body")
    if not isinstance(body, list):
        return
    params = _collect_function_param_names(func)
    func["body"] = _hoist_block_scope_vars_in_stmt_list(body, params)


# ---------------------------------------------------------------------------
# module-level entry point
# ---------------------------------------------------------------------------

def _walk_and_hoist(node: Any) -> None:
    """Recursively walk *node*, applying hoist to every FunctionDef body."""
    if isinstance(node, list):
        nl: list[Any] = node
        for item in nl:
            _walk_and_hoist(item)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    kind = _stmt_kind(nd)
    if kind == "FunctionDef":
        _hoist_in_function_def(nd)
        # Also recurse into body for nested functions
        body = nd.get("body")
        if isinstance(body, list):
            for stmt in body:
                _walk_and_hoist(stmt)
        return
    if kind == "ClassDef":
        body = nd.get("body")
        if isinstance(body, list):
            for stmt in body:
                _walk_and_hoist(stmt)
        return
    if kind == "Module":
        body = nd.get("body")
        if isinstance(body, list):
            for stmt in body:
                _walk_and_hoist(stmt)
        return
    # Generic recurse
    for value in nd.values():
        if isinstance(value, (dict, list)):
            _walk_and_hoist(value)


def hoist_block_scope_variables(module: dict[str, Any]) -> dict[str, Any]:
    """Top-level entry: apply block-scope variable hoist to an EAST3 Module.

    Mutates *module* in place and returns it.
    """
    _walk_and_hoist(module)
    return module
