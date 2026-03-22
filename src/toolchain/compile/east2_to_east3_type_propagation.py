"""EAST3 type propagation pass.

Propagates resolved_type information where it is missing:

1. Assign/AnnAssign: target.resolved_type ← decl_type / annotation / value.resolved_type
2. Attribute Call: Call.resolved_type ← callee function's return type (for module.func() calls)
3. VarDecl: type ← corresponding Assign's inferred type
4. Tuple unpacking: element targets ← tuple element types from value's resolved_type
"""

from __future__ import annotations

from typing import Any


def _safe_str(v: Any) -> str:
    if isinstance(v, str):
        return v.strip()
    return ""


def _propagate_assign_target_type(node: Any) -> None:
    """Walk EAST3 and propagate types to Assign/AnnAssign targets."""
    if isinstance(node, list):
        for item in node:
            _propagate_assign_target_type(item)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    kind = nd.get("kind", "")

    if kind in ("Assign", "AnnAssign"):
        target = nd.get("target")
        value = nd.get("value")
        if isinstance(target, dict):
            target_type = _safe_str(target.get("resolved_type"))
            if target_type in ("", "unknown"):
                # Try decl_type → annotation → value.resolved_type
                inferred = _safe_str(nd.get("decl_type"))
                if inferred in ("", "unknown"):
                    inferred = _safe_str(nd.get("annotation"))
                if inferred in ("", "unknown") and isinstance(value, dict):
                    inferred = _safe_str(value.get("resolved_type"))
                if inferred not in ("", "unknown"):
                    target["resolved_type"] = inferred
                    # Also set decl_type if missing
                    if _safe_str(nd.get("decl_type")) in ("", "unknown"):
                        nd["decl_type"] = inferred

            # Propagate decl_type to empty container value ([] / {})
            if isinstance(value, dict):
                val_type = _safe_str(value.get("resolved_type"))
                decl_type = _safe_str(nd.get("decl_type"))
                if decl_type not in ("", "unknown") and "unknown" in val_type:
                    val_kind = value.get("kind", "")
                    if val_kind in ("List", "Dict", "Set"):
                        value["resolved_type"] = decl_type

            # Tuple target: propagate element types
            if target.get("kind") == "Tuple" and isinstance(value, dict):
                _propagate_tuple_target_types(target, value)

    # Recurse
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _propagate_assign_target_type(v)


def _propagate_tuple_target_types(target: dict[str, Any], value: dict[str, Any]) -> None:
    """Propagate types to tuple unpacking targets from the value's type."""
    value_type = _safe_str(value.get("resolved_type"))
    if not (value_type.startswith("tuple[") and value_type.endswith("]")):
        return
    inner = value_type[6:-1]
    elem_types = _split_generic_types(inner)
    elements = target.get("elements")
    if not isinstance(elements, list):
        return
    for i, elem in enumerate(elements):
        if not isinstance(elem, dict):
            continue
        if i >= len(elem_types):
            break
        elem_t = _safe_str(elem.get("resolved_type"))
        if elem_t in ("", "unknown"):
            elem["resolved_type"] = elem_types[i].strip()


def _split_generic_types(type_name: str) -> list[str]:
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


def _propagate_binop_result_type(node: Any) -> None:
    """Propagate BinOp result types from operands when result is unknown."""
    if isinstance(node, list):
        for item in node:
            _propagate_binop_result_type(item)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node

    # Recurse first (bottom-up)
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _propagate_binop_result_type(v)

    if nd.get("kind") == "BinOp":
        result_type = _safe_str(nd.get("resolved_type"))
        if result_type not in ("", "unknown"):
            return
        left = nd.get("left")
        right = nd.get("right")
        left_t = _safe_str(left.get("resolved_type")) if isinstance(left, dict) else ""
        right_t = _safe_str(right.get("resolved_type")) if isinstance(right, dict) else ""
        if left_t in ("", "unknown") and right_t in ("", "unknown"):
            return
        # Infer from known operand
        float_types = {"float32", "float64"}
        int_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        if left_t in float_types or right_t in float_types:
            nd["resolved_type"] = "float64"
        elif left_t in int_types and right_t in int_types:
            nd["resolved_type"] = "int64"
        elif left_t == "str" or right_t == "str":
            op = nd.get("op", "")
            if op == "Add":
                nd["resolved_type"] = "str"
        elif left_t not in ("", "unknown"):
            nd["resolved_type"] = left_t
        elif right_t not in ("", "unknown"):
            nd["resolved_type"] = right_t

    if nd.get("kind") == "Compare":
        result_type = _safe_str(nd.get("resolved_type"))
        if result_type in ("", "unknown"):
            nd["resolved_type"] = "bool"

    if nd.get("kind") == "Subscript":
        result_type = _safe_str(nd.get("resolved_type"))
        if result_type in ("", "unknown"):
            value = nd.get("value")
            if isinstance(value, dict):
                val_t = _safe_str(value.get("resolved_type"))
                if val_t == "str":
                    nd["resolved_type"] = "str"
                elif val_t == "bytes" or val_t == "bytearray":
                    nd["resolved_type"] = "int32"
                elif val_t.startswith("list[") and val_t.endswith("]"):
                    nd["resolved_type"] = val_t[5:-1].strip()
                elif val_t.startswith("dict[") and val_t.endswith("]"):
                    parts = _split_generic_types(val_t[5:-1])
                    if len(parts) >= 2:
                        nd["resolved_type"] = parts[1].strip()

    if nd.get("kind") == "UnaryOp":
        result_type = _safe_str(nd.get("resolved_type"))
        if result_type in ("", "unknown"):
            operand = nd.get("operand")
            if isinstance(operand, dict):
                op_t = _safe_str(operand.get("resolved_type"))
                if op_t == "bool" and nd.get("op") == "Not":
                    nd["resolved_type"] = "bool"
                elif op_t not in ("", "unknown"):
                    nd["resolved_type"] = op_t


def _lower_truediv_to_method_call(node: Any) -> None:
    """Convert Path / "child" (BinOp Div) to Path.joinpath("child") call."""
    if isinstance(node, list):
        for i in range(len(node)):
            item = node[i]
            replacement = _try_lower_truediv(item)
            if replacement is not None:
                node[i] = replacement
            _lower_truediv_to_method_call(item)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    # Check all dict values for BinOp replacement
    for key in list(nd.keys()):
        val = nd[key]
        if isinstance(val, dict):
            replacement = _try_lower_truediv(val)
            if replacement is not None:
                nd[key] = replacement
            else:
                _lower_truediv_to_method_call(val)
        elif isinstance(val, list):
            _lower_truediv_to_method_call(val)


def _try_lower_truediv(node: Any) -> dict[str, Any] | None:
    """If node is BinOp(Div) with Path-typed left, return a Call node."""
    if not isinstance(node, dict):
        return None
    if node.get("kind") != "BinOp" or node.get("op") != "Div":
        return None
    left = node.get("left")
    if not isinstance(left, dict):
        return None
    left_t = _safe_str(left.get("resolved_type"))
    if left_t != "Path":
        return None
    right = node.get("right")
    call: dict[str, Any] = {
        "kind": "Call",
        "func": {
            "kind": "Attribute",
            "value": left,
            "attr": "joinpath",
            "resolved_type": "Path",
        },
        "args": [right] if right is not None else [],
        "keywords": [],
        "resolved_type": "Path",
    }
    span = node.get("source_span")
    if isinstance(span, dict):
        call["source_span"] = span
    return call


def _collect_function_callable_types(module: dict[str, Any]) -> dict[str, str]:
    """Collect {func_name: callable_type} from top-level FunctionDefs.

    Also maps original names for renamed symbols (e.g. main → __pytra_main).
    """
    out: dict[str, str] = {}
    # Build reverse rename map: __pytra_main → main
    renamed = {}
    rs = module.get("renamed_symbols")
    if isinstance(rs, dict):
        for orig, renamed_name in rs.items():
            if isinstance(orig, str) and isinstance(renamed_name, str):
                renamed[renamed_name] = orig
    body = module.get("body")
    if not isinstance(body, list):
        return out
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind", "")
        if kind == "FunctionDef":
            name = _safe_str(stmt.get("name"))
            ret = _safe_str(stmt.get("return_type"))
            if name != "" and ret not in ("", "unknown"):
                arg_order = stmt.get("arg_order")
                arg_types = stmt.get("arg_types")
                if isinstance(arg_order, list) and isinstance(arg_types, dict):
                    params = [p for p in arg_order if isinstance(p, str) and p != "self"]
                    param_types = [_safe_str(arg_types.get(p)) for p in params]
                    callable_t = "callable[[" + ",".join(param_types) + "]," + ret + "]"
                else:
                    callable_t = "callable[[],"+ret+"]"
                out[name] = callable_t
                # Also register original name if this was renamed
                if name in renamed:
                    out[renamed[name]] = callable_t
        elif kind == "ClassDef":
            cls_body = stmt.get("body")
            if isinstance(cls_body, list):
                for m in cls_body:
                    if isinstance(m, dict) and m.get("kind") == "FunctionDef":
                        mname = _safe_str(m.get("name"))
                        if mname != "":
                            ret = _safe_str(m.get("return_type"))
                            if ret not in ("", "unknown"):
                                out[mname] = "callable"
    return out


def _propagate_function_ref_types(node: Any, func_types: dict[str, str]) -> None:
    """Set resolved_type on Name nodes that reference known functions."""
    if isinstance(node, list):
        for item in node:
            _propagate_function_ref_types(item, func_types)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node

    # Only propagate to Name nodes used as Call arguments (not callee)
    if nd.get("kind") == "Call":
        args = nd.get("args")
        if isinstance(args, list):
            for arg in args:
                if isinstance(arg, dict) and arg.get("kind") == "Name":
                    name = _safe_str(arg.get("id"))
                    if name in func_types:
                        cur = _safe_str(arg.get("resolved_type"))
                        if cur in ("", "unknown"):
                            arg["resolved_type"] = func_types[name]

    for v in nd.values():
        if isinstance(v, (dict, list)):
            _propagate_function_ref_types(v, func_types)


def apply_type_propagation(module: dict[str, Any]) -> dict[str, Any]:
    """Top-level entry: apply type propagation to an EAST3 Module.

    Mutates *module* in place and returns it.
    """
    # Bottom-up BinOp/Compare/UnaryOp/Subscript propagation first
    _propagate_binop_result_type(module)
    # Lower Path / "child" to Path.joinpath("child")
    _lower_truediv_to_method_call(module)
    # Then top-down Assign target propagation
    _propagate_assign_target_type(module)
    # Propagate callable types for function references used as arguments
    func_types = _collect_function_callable_types(module)
    if len(func_types) > 0:
        _propagate_function_ref_types(module, func_types)
    return module
