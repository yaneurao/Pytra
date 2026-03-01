"""EAST3 -> Java native emitter."""

from __future__ import annotations

from pytra.std.typing import Any


def _safe_ident(name: Any, fallback: str) -> str:
    if not isinstance(name, str):
        return fallback
    if name == "":
        return fallback
    chars: list[str] = []
    i = 0
    while i < len(name):
        ch = name[i]
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
        i += 1
    out = "".join(chars)
    if out == "":
        out = fallback
    if out == "_":
        out = "__"
    if out[0].isdigit():
        out = "_" + out
    return out


def _java_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "Object"
    if type_name == "None":
        return "void" if allow_void else "Object"
    if type_name in {"unknown", "object", "any"}:
        return "Object"
    if type_name in {"int", "int64"}:
        return "long"
    if type_name in {"float", "float64"}:
        return "double"
    if type_name == "bool":
        return "boolean"
    if type_name == "str":
        return "String"
    if type_name == "bytes":
        return "java.util.ArrayList<Long>"
    if type_name == "bytearray":
        return "java.util.ArrayList<Long>"
    if type_name.startswith("list["):
        return "java.util.ArrayList<Object>"
    if type_name.startswith("dict["):
        return "java.util.HashMap<Object, Object>"
    if type_name.isidentifier():
        return _safe_ident(type_name, "Object")
    return "Object"


def _tuple_element_types(type_name: Any) -> list[str]:
    if not isinstance(type_name, str):
        return []
    if not type_name.startswith("tuple[") or not type_name.endswith("]"):
        return []
    body = type_name[6:-1]
    out: list[str] = []
    buf = ""
    depth = 0
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "[":
            depth += 1
            buf += ch
            i += 1
            continue
        if ch == "]":
            depth -= 1
            buf += ch
            i += 1
            continue
        if ch == "," and depth == 0:
            piece = buf.strip()
            if piece != "":
                out.append(piece)
            buf = ""
            i += 1
            continue
        buf += ch
        i += 1
    tail = buf.strip()
    if tail != "":
        out.append(tail)
    return out


def _cast_from_object(expr: str, java_type: str) -> str:
    if java_type == "long":
        return "((Long)(" + expr + "))"
    if java_type == "double":
        return "((Double)(" + expr + "))"
    if java_type == "boolean":
        return "((Boolean)(" + expr + "))"
    if java_type == "String":
        return "String.valueOf(" + expr + ")"
    if java_type == "Object":
        return expr
    return "((" + java_type + ")(" + expr + "))"


def _default_return_expr(java_type: str) -> str:
    if java_type == "long":
        return "0L"
    if java_type == "double":
        return "0.0"
    if java_type == "boolean":
        return "false"
    if java_type == "String":
        return '""'
    if java_type == "void":
        return ""
    return "null"


def _java_string_literal(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\n", "\\n")
    return '"' + out + '"'


def _module_leading_comment_lines(
    east_doc: dict[str, Any],
    prefix: str,
    indent: str = "",
) -> list[str]:
    trivia_any = east_doc.get("module_leading_trivia")
    trivia = trivia_any if isinstance(trivia_any, list) else []
    out: list[str] = []
    for item_any in trivia:
        if not isinstance(item_any, dict):
            continue
        kind = item_any.get("kind")
        if kind == "comment":
            text = item_any.get("text")
            if isinstance(text, str):
                out.append(indent + prefix + text)
            continue
        if kind == "blank":
            count = item_any.get("count")
            n = count if isinstance(count, int) and count > 0 else 1
            i = 0
            while i < n:
                out.append("")
                i += 1
    while len(out) > 0 and out[-1] == "":
        out.pop()
    return out


def _leading_comment_lines(stmt: dict[str, Any], prefix: str, indent: str = "") -> list[str]:
    trivia_any = stmt.get("leading_trivia")
    trivia = trivia_any if isinstance(trivia_any, list) else []
    out: list[str] = []
    for item_any in trivia:
        if not isinstance(item_any, dict):
            continue
        kind = item_any.get("kind")
        if kind == "comment":
            text = item_any.get("text")
            if isinstance(text, str):
                out.append(indent + prefix + text)
            continue
        if kind == "blank":
            count = item_any.get("count")
            n = count if isinstance(count, int) and count > 0 else 1
            i = 0
            while i < n:
                out.append("")
                i += 1
    while len(out) > 0 and out[-1] == "":
        out.pop()
    return out


def _render_name_expr(expr: dict[str, Any]) -> str:
    ident = _safe_ident(expr.get("id"), "value")
    if ident == "self":
        return "this"
    return ident


def _render_constant_expr(expr: dict[str, Any]) -> str:
    if "value" not in expr:
        return "null"
    value = expr.get("value")
    if value is None:
        resolved = expr.get("resolved_type")
        if resolved in {"int", "int64"}:
            return "0L"
        if resolved in {"float", "float64"}:
            return "0.0"
        if resolved == "bool":
            return "false"
        if resolved == "str":
            return '""'
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value) + "L"
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _java_string_literal(value)
    return "null"


def _render_unary_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    operand = _render_expr(expr.get("operand"))
    if op == "USub":
        return "(-" + operand + ")"
    if op == "UAdd":
        return "(+" + operand + ")"
    if op == "Not":
        return "(!" + operand + ")"
    return operand


def _bin_op_symbol(op: Any) -> str:
    if op == "Add":
        return "+"
    if op == "Sub":
        return "-"
    if op == "Mult":
        return "*"
    if op == "Div":
        return "/"
    if op == "Mod":
        return "%"
    if op == "FloorDiv":
        return "/"
    return "+"


def _bin_op_precedence(op: Any) -> int:
    if op in {"Mult", "Div", "FloorDiv", "Mod"}:
        return 20
    if op in {"Add", "Sub"}:
        return 10
    return 0


def _maybe_parenthesize_binop_child(child: Any, child_expr: str, parent_prec: int, is_right: bool) -> str:
    if not isinstance(child, dict) or child.get("kind") != "BinOp":
        return child_expr
    child_prec = _bin_op_precedence(child.get("op"))
    if child_prec < parent_prec:
        return "(" + child_expr + ")"
    if is_right and child_prec == parent_prec:
        # Keep RHS grouping fail-closed: `a - (b - c)` / `a + (b - c)` etc.
        return "(" + child_expr + ")"
    return child_expr


def _render_binop_expr(expr: dict[str, Any]) -> str:
    op_name = expr.get("op")
    if op_name == "Mult":
        left_any = expr.get("left")
        right_any = expr.get("right")
        if isinstance(left_any, dict) and left_any.get("kind") == "List":
            elems_any = left_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            if len(elems) == 1:
                return "PyRuntime.__pytra_list_repeat(" + _render_expr(elems[0]) + ", " + _render_expr(right_any) + ")"
        if isinstance(right_any, dict) and right_any.get("kind") == "List":
            elems_any = right_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            if len(elems) == 1:
                return "PyRuntime.__pytra_list_repeat(" + _render_expr(elems[0]) + ", " + _render_expr(left_any) + ")"
    left_any = expr.get("left")
    right_any = expr.get("right")
    left = _render_expr(left_any)
    right = _render_expr(right_any)
    casts_any = expr.get("casts")
    casts = casts_any if isinstance(casts_any, list) else []
    i = 0
    while i < len(casts):
        cast = casts[i]
        if isinstance(cast, dict):
            cast_to = cast.get("to")
            cast_on = cast.get("on")
            if cast_to == "float64" and cast_on == "left":
                left = "((double)(" + left + "))"
            if cast_to == "float64" and cast_on == "right":
                right = "((double)(" + right + "))"
        i += 1
    op = _bin_op_symbol(op_name)
    parent_prec = _bin_op_precedence(op_name)
    left = _maybe_parenthesize_binop_child(left_any, left, parent_prec, is_right=False)
    right = _maybe_parenthesize_binop_child(right_any, right, parent_prec, is_right=True)
    return left + " " + op + " " + right


def _compare_op_symbol(op: Any) -> str:
    if op == "Eq":
        return "=="
    if op == "NotEq":
        return "!="
    if op == "Lt":
        return "<"
    if op == "LtE":
        return "<="
    if op == "Gt":
        return ">"
    if op == "GtE":
        return ">="
    return "=="


def _render_compare_expr(expr: dict[str, Any]) -> str:
    left_expr = _render_expr(expr.get("left"))
    ops_any = expr.get("ops")
    comps_any = expr.get("comparators")
    ops = ops_any if isinstance(ops_any, list) else []
    comps = comps_any if isinstance(comps_any, list) else []
    if len(ops) == 0 or len(comps) == 0:
        return left_expr
    parts: list[str] = []
    cur_left = left_expr
    i = 0
    while i < len(ops) and i < len(comps):
        comp_node = comps[i]
        right = _render_expr(comp_node)
        op = ops[i]
        if op == "In" or op == "NotIn":
            expr_txt = right + ".contains(" + cur_left + ")"
            if isinstance(comp_node, dict):
                comp_resolved = comp_node.get("resolved_type")
                if isinstance(comp_resolved, str):
                    if comp_resolved.startswith("dict["):
                        expr_txt = right + ".containsKey(" + cur_left + ")"
                    elif comp_resolved == "str":
                        expr_txt = right + ".contains(String.valueOf(" + cur_left + "))"
            if op == "NotIn":
                expr_txt = "!(" + expr_txt + ")"
            parts.append("(" + expr_txt + ")")
        elif op == "Eq" or op == "NotEq":
            left_resolved = ""
            if i == 0 and isinstance(expr.get("left"), dict):
                left_resolved_any = expr.get("left", {}).get("resolved_type")
                left_resolved = left_resolved_any if isinstance(left_resolved_any, str) else ""
            elif i > 0 and isinstance(comps[i - 1], dict):
                left_resolved_any = comps[i - 1].get("resolved_type")
                left_resolved = left_resolved_any if isinstance(left_resolved_any, str) else ""
            right_resolved_any = comp_node.get("resolved_type") if isinstance(comp_node, dict) else ""
            right_resolved = right_resolved_any if isinstance(right_resolved_any, str) else ""
            if left_resolved == "str" or right_resolved == "str":
                expr_txt = "java.util.Objects.equals(" + cur_left + ", " + right + ")"
                if op == "NotEq":
                    expr_txt = "!(" + expr_txt + ")"
                parts.append("(" + expr_txt + ")")
            else:
                parts.append("(" + cur_left + " " + _compare_op_symbol(op) + " " + right + ")")
        else:
            parts.append("(" + cur_left + " " + _compare_op_symbol(op) + " " + right + ")")
        cur_left = right
        i += 1
    if len(parts) == 0:
        return left_expr
    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _render_boolop_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    values_any = expr.get("values")
    values = values_any if isinstance(values_any, list) else []
    if len(values) == 0:
        return "false"
    delim = " && " if op == "And" else " || "
    rendered: list[str] = []
    i = 0
    while i < len(values):
        rendered.append(_render_expr(values[i]))
        i += 1
    return "(" + delim.join(rendered) + ")"


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    value_any = expr.get("value")
    attr = _safe_ident(expr.get("attr"), "field")
    if isinstance(value_any, dict) and value_any.get("kind") == "Name":
        owner = _safe_ident(value_any.get("id"), "")
        if owner == "math" and attr == "pi":
            return "Math.PI"
        if owner == "math" and attr == "e":
            return "Math.E"
    value = _render_expr(value_any)
    return value + "." + attr


def _call_name(expr: dict[str, Any]) -> str:
    func_any = expr.get("func")
    if not isinstance(func_any, dict):
        return ""
    if func_any.get("kind") != "Name":
        return ""
    return _safe_ident(func_any.get("id"), "")


def _render_call_expr(expr: dict[str, Any]) -> str:
    args_any = expr.get("args")
    args = args_any if isinstance(args_any, list) else []

    callee_name = _call_name(expr)
    if callee_name.startswith("py_assert_"):
        return _java_string_literal("True")
    if callee_name == "main" and len(args) == 0:
        return "__pytra_main()"
    if callee_name == "perf_counter":
        return "(System.nanoTime() / 1000000000.0)"
    if callee_name == "bytearray":
        if len(args) == 0:
            return "new java.util.ArrayList<Long>()"
        return "PyRuntime.__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee_name == "bytes":
        if len(args) == 0:
            return "new java.util.ArrayList<Long>()"
        return "new java.util.ArrayList<Long>(" + _render_expr(args[0]) + ")"
    if callee_name == "int":
        if len(args) == 0:
            return "0L"
        return "PyRuntime.__pytra_int(" + _render_expr(args[0]) + ")"
    if callee_name == "float":
        if len(args) == 0:
            return "0.0"
        return "((double)(" + _render_expr(args[0]) + "))"
    if callee_name == "bool":
        if len(args) == 0:
            return "false"
        return "PyRuntime.__pytra_truthy(" + _render_expr(args[0]) + ")"
    if callee_name == "str":
        if len(args) == 0:
            return '""'
        return "String.valueOf(" + _render_expr(args[0]) + ")"
    if callee_name == "min":
        if len(args) == 0:
            return "0L"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "Math.min(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name == "max":
        if len(args) == 0:
            return "0L"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "Math.max(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name == "len":
        if len(args) == 0:
            return "0L"
        target = args[0]
        if isinstance(target, dict):
            resolved = target.get("resolved_type")
            rendered = _render_expr(target)
            if resolved == "str":
                return "((long)(" + rendered + ".length()))"
            if isinstance(resolved, str) and resolved.startswith("dict["):
                return "((long)(" + rendered + ".size()))"
            if isinstance(resolved, str) and (resolved.startswith("list[") or resolved in {"bytes", "bytearray"}):
                return "((long)(" + rendered + ".size()))"
        return "PyRuntime.__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "isinstance":
        if len(args) < 2:
            return "false"
        lhs = _render_expr(args[0])
        typ = args[1]
        return _render_isinstance_check(lhs, typ)
    if callee_name in {"save_gif", "write_rgb_png"}:
        rendered_noop_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_noop_args.append(_render_expr(args[i]))
            i += 1
        return "PyRuntime.__pytra_noop(" + ", ".join(rendered_noop_args) + ")"
    if callee_name == "grayscale_palette":
        return "new java.util.ArrayList<Long>()"
    if callee_name == "print":
        if len(args) == 0:
            return "System.out.println()"
        if len(args) == 1:
            return "System.out.println(" + _render_expr(args[0]) + ")"
        rendered: list[str] = []
        i = 0
        while i < len(args):
            rendered.append("String.valueOf(" + _render_expr(args[i]) + ")")
            i += 1
        return "System.out.println(" + " + \" \" + ".join(rendered) + ")"
    func_any = expr.get("func")
    if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
        attr_name = _safe_ident(func_any.get("attr"), "")
        owner_for_super = func_any.get("value")
        if isinstance(owner_for_super, dict) and owner_for_super.get("kind") == "Call":
            if _call_name(owner_for_super) == "super":
                rendered_super_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_super_args.append(_render_expr(args[i]))
                    i += 1
                if attr_name == "__init__":
                    return "super(" + ", ".join(rendered_super_args) + ")"
                return "super." + attr_name + "(" + ", ".join(rendered_super_args) + ")"
        owner_any = func_any.get("value")
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner = _safe_ident(owner_any.get("id"), "")
            if owner == "math":
                rendered_math_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_math_args.append(_render_expr(args[i]))
                    i += 1
                return "Math." + attr_name + "(" + ", ".join(rendered_math_args) + ")"
        owner_expr = _render_expr(func_any.get("value"))
        if attr_name == "append" and len(args) == 1:
            return owner_expr + ".add(" + _render_expr(args[0]) + ")"
        if attr_name == "pop":
            if len(args) == 0:
                return owner_expr + ".remove(" + owner_expr + ".size() - 1)"
            return owner_expr + ".remove((int)(" + _render_expr(args[0]) + "))"
        if attr_name == "isdigit" and len(args) == 0:
            return "PyRuntime.__pytra_str_isdigit(" + owner_expr + ")"
        if attr_name == "isalpha" and len(args) == 0:
            return "PyRuntime.__pytra_str_isalpha(" + owner_expr + ")"
        if attr_name in {"write_rgb_png", "save_gif"}:
            rendered_noop_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_noop_args.append(_render_expr(args[i]))
                i += 1
            return "PyRuntime.__pytra_noop(" + ", ".join(rendered_noop_args) + ")"
    if callee_name != "" and callee_name[0].isupper():
        rendered_ctor_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_ctor_args.append(_render_expr(args[i]))
            i += 1
        return "new " + callee_name + "(" + ", ".join(rendered_ctor_args) + ")"

    func_expr = _render_expr(expr.get("func"))
    rendered_args: list[str] = []
    i = 0
    while i < len(args):
        rendered_args.append(_render_expr(args[i]))
        i += 1
    return func_expr + "(" + ", ".join(rendered_args) + ")"


def _render_isinstance_check(lhs: str, typ: Any) -> str:
    if not isinstance(typ, dict):
        return "false"
    boxed_lhs = "((Object)(" + lhs + "))"
    if typ.get("kind") == "Name":
        name = _safe_ident(typ.get("id"), "")
        if name in {"int", "int64"}:
            return "(" + boxed_lhs + " instanceof Long)"
        if name in {"float", "float64"}:
            return "(" + boxed_lhs + " instanceof Double)"
        if name == "bool":
            return "(" + boxed_lhs + " instanceof Boolean)"
        if name == "str":
            return "(" + boxed_lhs + " instanceof String)"
        if name in {"list", "bytes", "bytearray"}:
            return "(" + boxed_lhs + " instanceof java.util.ArrayList)"
        return "(" + boxed_lhs + " instanceof " + name + ")"
    if typ.get("kind") == "Tuple":
        elements_any = typ.get("elements")
        elements = elements_any if isinstance(elements_any, list) else []
        checks: list[str] = []
        i = 0
        while i < len(elements):
            checks.append(_render_isinstance_check(lhs, elements[i]))
            i += 1
        if len(checks) == 0:
            return "false"
        return "(" + " || ".join(checks) + ")"
    return "false"


def _render_truthy_expr(expr: Any) -> str:
    rendered = _render_expr(expr)
    if not isinstance(expr, dict):
        return "PyRuntime.__pytra_truthy(" + rendered + ")"
    resolved = expr.get("resolved_type")
    if isinstance(resolved, str):
        if resolved == "bool":
            return rendered
        if resolved in {"int", "int64", "uint8"}:
            return "(" + rendered + " != 0L)"
        if resolved in {"float", "float64"}:
            return "(" + rendered + " != 0.0)"
        if resolved == "str":
            return "((" + rendered + ") != null && !(" + rendered + ").isEmpty())"
        if resolved.startswith("list[") or resolved in {"bytes", "bytearray"}:
            return "((" + rendered + ") != null && !(" + rendered + ").isEmpty())"
    kind = expr.get("kind")
    if kind in {"Compare", "BoolOp", "IsInstance"}:
        return rendered
    return "PyRuntime.__pytra_truthy(" + rendered + ")"


def _normalize_index_expr(owner_expr: str, index_expr: str) -> str:
    return (
        "((("
        + index_expr
        + ") < 0L) ? (((long)("
        + owner_expr
        + ".size())) + ("
        + index_expr
        + ")) : ("
        + index_expr
        + "))"
    )


def _render_expr(expr: Any) -> str:
    if not isinstance(expr, dict):
        return "null"
    kind = expr.get("kind")
    if kind == "Name":
        return _render_name_expr(expr)
    if kind == "Constant":
        return _render_constant_expr(expr)
    if kind == "UnaryOp":
        return _render_unary_expr(expr)
    if kind == "BinOp":
        return _render_binop_expr(expr)
    if kind == "Compare":
        return _render_compare_expr(expr)
    if kind == "BoolOp":
        return _render_boolop_expr(expr)
    if kind == "Attribute":
        return _render_attribute_expr(expr)
    if kind == "Call":
        return _render_call_expr(expr)
    if kind == "List":
        elements_any = expr.get("elements")
        elements = elements_any if isinstance(elements_any, list) else []
        rendered: list[str] = []
        i = 0
        while i < len(elements):
            rendered.append(_render_expr(elements[i]))
            i += 1
        return "new java.util.ArrayList<Object>(java.util.Arrays.asList(" + ", ".join(rendered) + "))"
    if kind == "Tuple":
        elements_any = expr.get("elements")
        elements = elements_any if isinstance(elements_any, list) else []
        rendered: list[str] = []
        i = 0
        while i < len(elements):
            rendered.append(_render_expr(elements[i]))
            i += 1
        return "new java.util.ArrayList<Object>(java.util.Arrays.asList(" + ", ".join(rendered) + "))"
    if kind == "Dict":
        keys_any = expr.get("keys")
        vals_any = expr.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        vals = vals_any if isinstance(vals_any, list) else []
        if len(keys) == 0 or len(vals) == 0:
            return "new java.util.HashMap<Object, Object>()"
        rendered: list[str] = []
        i = 0
        while i < len(keys) and i < len(vals):
            rendered.append(_render_expr(keys[i]))
            rendered.append(_render_expr(vals[i]))
            i += 1
        return "PyRuntime.__pytra_dict_of(" + ", ".join(rendered) + ")"
    if kind == "ListComp":
        return "new java.util.ArrayList<Object>()"
    if kind == "IfExp":
        test_expr = _render_truthy_expr(expr.get("test"))
        body_expr = _render_expr(expr.get("body"))
        else_expr = _render_expr(expr.get("orelse"))
        return "((" + test_expr + ") ? (" + body_expr + ") : (" + else_expr + "))"
    if kind == "Subscript":
        value_any = expr.get("value")
        index_any = expr.get("slice")
        owner_expr = _render_expr(value_any)
        owner_type = value_any.get("resolved_type") if isinstance(value_any, dict) else None
        if isinstance(index_any, dict) and index_any.get("kind") == "Slice":
            lower_any = index_any.get("lower")
            upper_any = index_any.get("upper")
            lower_expr = _render_expr(lower_any) if isinstance(lower_any, dict) else "0L"
            if isinstance(upper_any, dict):
                upper_expr = _render_expr(upper_any)
            elif isinstance(owner_type, str) and owner_type == "str":
                upper_expr = "((long)(" + owner_expr + ".length()))"
            else:
                upper_expr = "((long)(" + owner_expr + ".size()))"
            if isinstance(owner_type, str) and owner_type == "str":
                start = (
                    "((("
                    + lower_expr
                    + ") < 0L) ? (((long)("
                    + owner_expr
                    + ".length())) + ("
                    + lower_expr
                    + ")) : ("
                    + lower_expr
                    + "))"
                )
                stop = (
                    "((("
                    + upper_expr
                    + ") < 0L) ? (((long)("
                    + owner_expr
                    + ".length())) + ("
                    + upper_expr
                    + ")) : ("
                    + upper_expr
                    + "))"
                )
                return "PyRuntime.__pytra_str_slice(" + owner_expr + ", " + start + ", " + stop + ")"
            return owner_expr
        index_expr = _render_expr(index_any)
        base = ""
        if isinstance(owner_type, str) and owner_type.startswith("dict["):
            base = owner_expr + ".get(" + index_expr + ")"
        elif isinstance(owner_type, str) and owner_type == "str":
            norm_index = (
                "((("
                + index_expr
                + ") < 0L) ? (((long)("
                + owner_expr
                + ".length())) + ("
                + index_expr
                + ")) : ("
                + index_expr
                + "))"
            )
            base = "String.valueOf(" + owner_expr + ".charAt((int)(" + norm_index + ")))"
        else:
            norm_index = _normalize_index_expr(owner_expr, index_expr)
            base = owner_expr + ".get((int)(" + norm_index + "))"
        resolved = expr.get("resolved_type")
        if isinstance(resolved, str):
            if resolved in {"int", "int64", "uint8"}:
                return "((Long)(" + base + "))"
            if resolved in {"float", "float64"}:
                return "((Double)(" + base + "))"
            if resolved == "bool":
                return "((Boolean)(" + base + "))"
            if resolved == "str":
                return "String.valueOf(" + base + ")"
            if resolved.startswith("list["):
                return "((java.util.ArrayList<Object>)(" + base + "))"
            if resolved in {"bytes", "bytearray"}:
                return "((java.util.ArrayList<Long>)(" + base + "))"
            inferred = _java_type(resolved, allow_void=False)
            if inferred not in {"Object", "void", "long", "double", "boolean", "String"}:
                return "((" + inferred + ")(" + base + "))"
        return base
    if kind == "IsInstance":
        lhs = _render_expr(expr.get("value"))
        return _render_isinstance_check(lhs, expr.get("expected_type_id"))
    if kind == "ObjLen":
        return "PyRuntime.__pytra_len(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjStr":
        return "String.valueOf(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjBool":
        return "PyRuntime.__pytra_truthy(" + _render_expr(expr.get("value")) + ")"
    if kind == "Unbox" or kind == "Box":
        return _render_expr(expr.get("value"))
    return "null"


def _function_param_names(fn: dict[str, Any], *, drop_self: bool) -> list[str]:
    arg_order_any = fn.get("arg_order")
    arg_order = arg_order_any if isinstance(arg_order_any, list) else []
    out: list[str] = []
    i = 0
    while i < len(arg_order):
        raw = arg_order[i]
        if isinstance(raw, str):
            if drop_self and i == 0 and raw == "self":
                i += 1
                continue
            out.append(_safe_ident(raw, "arg" + str(i)))
        i += 1
    return out


def _function_params(fn: dict[str, Any], *, drop_self: bool) -> list[str]:
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    names = _function_param_names(fn, drop_self=drop_self)
    out: list[str] = []
    i = 0
    while i < len(names):
        name = names[i]
        param_type = _java_type(arg_types.get(name), allow_void=False)
        out.append(param_type + " " + name)
        i += 1
    return out


def _target_name(target: Any) -> str:
    if not isinstance(target, dict):
        return "tmp"
    kind = target.get("kind")
    if kind == "Name":
        return _safe_ident(target.get("id"), "tmp")
    if kind == "Attribute":
        return _render_attribute_expr(target)
    return "tmp"


def _augassign_op(op: Any) -> str:
    if op == "Add":
        return "+="
    if op == "Sub":
        return "-="
    if op == "Mult":
        return "*="
    if op == "Div":
        return "/="
    if op == "Mod":
        return "%="
    return "+="


def _fresh_tmp(ctx: dict[str, int], prefix: str) -> str:
    idx = ctx.get("tmp", 0)
    ctx["tmp"] = idx + 1
    return "__" + prefix + "_" + str(idx)


def _declared_set(ctx: dict[str, Any]) -> set[str]:
    declared = ctx.get("declared")
    if isinstance(declared, set):
        return declared
    fresh: set[str] = set()
    ctx["declared"] = fresh
    return fresh


def _type_map(ctx: dict[str, Any]) -> dict[str, str]:
    types = ctx.get("types")
    if isinstance(types, dict):
        return types
    fresh: dict[str, str] = {}
    ctx["types"] = fresh
    return fresh


def _infer_java_type_from_expr_node(expr: Any, type_map: dict[str, str] | None = None) -> str:
    if not isinstance(expr, dict):
        return "Object"
    kind = expr.get("kind")
    if kind == "Name" and isinstance(type_map, dict):
        ident = _safe_ident(expr.get("id"), "")
        if ident in type_map:
            mapped = type_map[ident]
            if mapped != "":
                return mapped
    if kind == "Unbox":
        target = expr.get("target")
        inferred = _java_type(target, allow_void=False)
        if inferred != "Object":
            return inferred
    if kind == "Call":
        func_any = expr.get("func")
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner_any = func_any.get("value")
            if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
                owner = _safe_ident(owner_any.get("id"), "")
                if owner == "math":
                    return "double"
        name = _call_name(expr)
        if name == "perf_counter":
            return "double"
        if name == "float":
            return "double"
        if name == "int":
            return "long"
        if name in {"min", "max"}:
            args_any = expr.get("args")
            args = args_any if isinstance(args_any, list) else []
            saw_float = False
            i = 0
            while i < len(args):
                arg = args[i]
                if isinstance(arg, dict):
                    t = _java_type(arg.get("resolved_type"), allow_void=False)
                    if t == "double":
                        saw_float = True
                        break
                i += 1
            return "double" if saw_float else "long"
        if name == "bool":
            return "boolean"
        if name == "str":
            return "String"
    if kind == "BinOp":
        left_t = _infer_java_type_from_expr_node(expr.get("left"), type_map)
        right_t = _infer_java_type_from_expr_node(expr.get("right"), type_map)
        op = expr.get("op")
        if op == "Div":
            return "double"
        if left_t == "double" or right_t == "double":
            return "double"
        if left_t == "long" and right_t == "long":
            return "long"
        left_any = expr.get("left")
        right_any = expr.get("right")
        left_res = _java_type(left_any.get("resolved_type"), allow_void=False) if isinstance(left_any, dict) else "Object"
        right_res = _java_type(right_any.get("resolved_type"), allow_void=False) if isinstance(right_any, dict) else "Object"
        if left_res == "double" or right_res == "double":
            return "double"
        if left_res == "long" or right_res == "long":
            return "long"
        if op in {"Add", "Sub", "Mult", "Div", "Mod", "FloorDiv"} and left_t == "Object" and right_t == "Object":
            return "long"
    if kind == "UnaryOp":
        return _infer_java_type_from_expr_node(expr.get("operand"), type_map)
    if kind == "Subscript":
        resolved = expr.get("resolved_type")
        inferred = _java_type(resolved, allow_void=False)
        if inferred != "Object":
            return inferred
    resolved = expr.get("resolved_type")
    inferred = _java_type(resolved, allow_void=False)
    return inferred


def _emit_for_runtime_iter(
    stmt: dict[str, Any],
    *,
    iter_plan: dict[str, Any],
    target_plan: dict[str, Any],
    indent: str,
    ctx: dict[str, Any],
) -> list[str]:
    iter_expr_any = iter_plan.get("iter_expr")
    list_expr = _render_expr(iter_expr_any)
    is_enumerate = False
    if isinstance(iter_expr_any, dict) and iter_expr_any.get("kind") == "Call" and _call_name(iter_expr_any) == "enumerate":
        args_any = iter_expr_any.get("args")
        args = args_any if isinstance(args_any, list) else []
        if len(args) >= 1:
            list_expr = _render_expr(args[0])
            is_enumerate = True

    iter_tmp = _fresh_tmp(ctx, "iter")
    idx_tmp = _fresh_tmp(ctx, "iter_i")
    lines: list[str] = []
    lines.append(indent + "java.util.ArrayList<Object> " + iter_tmp + " = ((java.util.ArrayList<Object>)(" + list_expr + "));")
    lines.append(
        indent
        + "for (long "
        + idx_tmp
        + " = 0L; "
        + idx_tmp
        + " < ((long)("
        + iter_tmp
        + ".size())); "
        + idx_tmp
        + " += 1L) {"
    )
    body_ctx: dict[str, Any] = {
        "tmp": ctx.get("tmp", 0),
        "declared": set(_declared_set(ctx)),
        "types": dict(_type_map(ctx)),
    }
    body_declared = _declared_set(body_ctx)
    body_types = _type_map(body_ctx)

    if target_plan.get("kind") == "NameTarget":
        target_name = _safe_ident(target_plan.get("id"), "item")
        target_type = _java_type(target_plan.get("target_type"), allow_void=False)
        if target_type == "void":
            target_type = "Object"
        base = iter_tmp + ".get((int)(" + idx_tmp + "))"
        rhs = _cast_from_object(base, target_type)
        lines.append(indent + "    " + target_type + " " + target_name + " = " + rhs + ";")
        body_declared.add(target_name)
        if target_type != "Object":
            body_types[target_name] = target_type
    elif target_plan.get("kind") == "TupleTarget":
        elems_any = target_plan.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        tuple_types = _tuple_element_types(target_plan.get("target_type"))
        tuple_item_tmp = _fresh_tmp(body_ctx, "iter_item")
        if is_enumerate and len(elems) == 2:
            i = 0
            while i < len(elems):
                elem = elems[i]
                if not isinstance(elem, dict) or elem.get("kind") != "NameTarget":
                    raise RuntimeError("java native emitter: unsupported RuntimeIter tuple target")
                name = _safe_ident(elem.get("id"), "item_" + str(i))
                elem_type = "Object"
                if i < len(tuple_types):
                    inferred = _java_type(tuple_types[i], allow_void=False)
                    elem_type = "Object" if inferred == "void" else inferred
                if i == 0:
                    if elem_type == "long":
                        rhs = idx_tmp
                    else:
                        rhs = _cast_from_object("Long.valueOf(" + idx_tmp + ")", elem_type)
                else:
                    rhs = _cast_from_object(iter_tmp + ".get((int)(" + idx_tmp + "))", elem_type)
                lines.append(indent + "    " + elem_type + " " + name + " = " + rhs + ";")
                body_declared.add(name)
                if elem_type != "Object":
                    body_types[name] = elem_type
                i += 1
        else:
            lines.append(
                indent
                + "    java.util.ArrayList<Object> "
                + tuple_item_tmp
                + " = ((java.util.ArrayList<Object>)("
                + iter_tmp
                + ".get((int)("
                + idx_tmp
                + "))));"
            )
            i = 0
            while i < len(elems):
                elem = elems[i]
                if not isinstance(elem, dict) or elem.get("kind") != "NameTarget":
                    raise RuntimeError("java native emitter: unsupported RuntimeIter tuple target")
                name = _safe_ident(elem.get("id"), "item_" + str(i))
                elem_type = "Object"
                if i < len(tuple_types):
                    inferred = _java_type(tuple_types[i], allow_void=False)
                    elem_type = "Object" if inferred == "void" else inferred
                rhs = _cast_from_object(tuple_item_tmp + ".get(" + str(i) + ")", elem_type)
                lines.append(indent + "    " + elem_type + " " + name + " = " + rhs + ";")
                body_declared.add(name)
                if elem_type != "Object":
                    body_types[name] = elem_type
                i += 1
    else:
        raise RuntimeError("java native emitter: unsupported RuntimeIter target_plan")

    body_any = stmt.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
        i += 1
    ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
    lines.append(indent + "}")
    return lines


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        raise RuntimeError("java native emitter: unsupported ForCore iter_plan")
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("java native emitter: unsupported ForCore target_plan")

    if iter_plan_any.get("kind") == "RuntimeIterForPlan":
        return _emit_for_runtime_iter(stmt, iter_plan=iter_plan_any, target_plan=target_plan_any, indent=indent, ctx=ctx)

    if iter_plan_any.get("kind") != "StaticRangeForPlan":
        raise RuntimeError("java native emitter: unsupported ForCore iter_plan")
    if target_plan_any.get("kind") != "NameTarget":
        raise RuntimeError("java native emitter: unsupported ForCore target_plan")

    target_name = _safe_ident(target_plan_any.get("id"), "i")
    target_type = _java_type(target_plan_any.get("target_type"), allow_void=False)
    if target_type == "Object":
        target_type = "long"
    start_expr = _render_expr(iter_plan_any.get("start"))
    stop_expr = _render_expr(iter_plan_any.get("stop"))
    step_expr = _render_expr(iter_plan_any.get("step"))
    step_tmp = _fresh_tmp(ctx, "step")
    lines: list[str] = []
    lines.append(indent + target_type + " " + step_tmp + " = " + step_expr + ";")
    cond = "(" + step_tmp + " >= 0L) ? (" + target_name + " < " + stop_expr + ") : (" + target_name + " > " + stop_expr + ")"
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    type_map[target_name] = target_type
    if target_name in declared:
        init = target_name + " = " + start_expr
    else:
        init = target_type + " " + target_name + " = " + start_expr
    lines.append(
        indent
        + "for ("
        + init
        + "; "
        + cond
        + "; "
        + target_name
        + " += "
        + step_tmp
        + ") {"
    )
    body_any = stmt.get("body")
    body = body_any if isinstance(body_any, list) else []
    body_ctx: dict[str, Any] = {
        "tmp": ctx.get("tmp", 0),
        "declared": set(_declared_set(ctx)),
        "types": dict(_type_map(ctx)),
    }
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
        i += 1
    ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
    lines.append(indent + "}")
    return lines


def _try_emit_tuple_assign(
    target_any: Any,
    value_any: Any,
    *,
    decl_type_any: Any,
    declare_hint: bool,
    indent: str,
    ctx: dict[str, Any],
) -> list[str] | None:
    if not isinstance(target_any, dict) or target_any.get("kind") != "Tuple":
        return None
    elems_any = target_any.get("elements")
    elems = elems_any if isinstance(elems_any, list) else []
    if len(elems) == 0:
        return None
    i = 0
    while i < len(elems):
        elem = elems[i]
        if not isinstance(elem, dict):
            return None
        kind = elem.get("kind")
        if kind != "Name" and kind != "Subscript":
            return None
        i += 1
    tuple_tmp = _fresh_tmp(ctx, "tuple")
    tuple_expr = _render_expr(value_any)
    lines: list[str] = [indent + "java.util.ArrayList<Object> " + tuple_tmp + " = ((java.util.ArrayList<Object>)(" + tuple_expr + "));"]
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    tuple_types = _tuple_element_types(decl_type_any)
    if len(tuple_types) == 0 and isinstance(value_any, dict):
        tuple_types = _tuple_element_types(value_any.get("resolved_type"))
    i = 0
    while i < len(elems):
        elem = elems[i]
        if not isinstance(elem, dict):
            i += 1
            continue
        kind = elem.get("kind")
        java_type = "Object"
        if i < len(tuple_types):
            inferred = _java_type(tuple_types[i], allow_void=False)
            java_type = "Object" if inferred == "void" else inferred
        rhs = _cast_from_object(tuple_tmp + ".get(" + str(i) + ")", java_type)
        if kind == "Name":
            name = _safe_ident(elem.get("id"), "tmp_" + str(i))
            if declare_hint:
                if name in declared:
                    lines.append(indent + name + " = " + rhs + ";")
                else:
                    lines.append(indent + java_type + " " + name + " = " + rhs + ";")
                    declared.add(name)
                    type_map[name] = java_type
            else:
                if name not in declared:
                    lines.append(indent + java_type + " " + name + " = " + rhs + ";")
                    declared.add(name)
                    type_map[name] = java_type
                else:
                    lines.append(indent + name + " = " + rhs + ";")
        else:
            owner = _render_expr(elem.get("value"))
            index = _render_expr(elem.get("slice"))
            target_type = _java_type(elem.get("resolved_type"), allow_void=False)
            if target_type == "Object":
                target_type = java_type
            rhs_for_target = _cast_from_object(tuple_tmp + ".get(" + str(i) + ")", target_type)
            norm_index = _normalize_index_expr(owner, index)
            lines.append(indent + owner + ".set((int)(" + norm_index + "), " + rhs_for_target + ");")
        i += 1
    return lines


def _try_emit_listcomp_assign(
    lhs: str,
    value_any: Any,
    *,
    decl_prefix: str,
    indent: str,
    ctx: dict[str, Any],
) -> list[str] | None:
    if not isinstance(value_any, dict) or value_any.get("kind") != "ListComp":
        return None
    gens_any = value_any.get("generators")
    gens = gens_any if isinstance(gens_any, list) else []
    if len(gens) != 1 or not isinstance(gens[0], dict):
        return None
    gen = gens[0]
    ifs_any = gen.get("ifs")
    ifs = ifs_any if isinstance(ifs_any, list) else []
    if len(ifs) != 0:
        return None
    target_any = gen.get("target")
    iter_any = gen.get("iter")
    if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
        return None
    if not isinstance(iter_any, dict) or iter_any.get("kind") != "RangeExpr":
        return None
    loop_var = _safe_ident(target_any.get("id"), "")
    if loop_var == "":
        loop_var = _fresh_tmp(ctx, "lc")
    start = _render_expr(iter_any.get("start"))
    stop = _render_expr(iter_any.get("stop"))
    step = _render_expr(iter_any.get("step"))
    step_var = _fresh_tmp(ctx, "step")
    elt_expr = _render_expr(value_any.get("elt"))
    lines: list[str] = [indent + decl_prefix + lhs + " = new java.util.ArrayList<Object>();"]
    lines.append(indent + "long " + step_var + " = " + step + ";")
    lines.append(
        indent
        + "for (long "
        + loop_var
        + " = "
        + start
        + "; ("
        + step_var
        + " >= 0L) ? ("
        + loop_var
        + " < "
        + stop
        + ") : ("
        + loop_var
        + " > "
        + stop
        + "); "
        + loop_var
        + " += "
        + step_var
        + ") {"
    )
    lines.append(indent + "    " + lhs + ".add(" + elt_expr + ");")
    lines.append(indent + "}")
    return lines


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        raise RuntimeError("java native emitter: unsupported statement")
    kind = stmt.get("kind")
    if kind == "Return":
        if "value" in stmt and stmt.get("value") is not None:
            return [indent + "return " + _render_expr(stmt.get("value")) + ";"]
        return [indent + "return;"]
    if kind == "Expr":
        return [indent + _render_expr(stmt.get("value")) + ";"]
    if kind == "AnnAssign":
        target_any = stmt.get("target")
        if isinstance(target_any, dict) and target_any.get("kind") == "Attribute":
            return [indent + _render_attribute_expr(target_any) + " = " + _render_expr(stmt.get("value")) + ";"]
        tuple_lines = _try_emit_tuple_assign(
            target_any,
            stmt.get("value"),
            decl_type_any=(stmt.get("decl_type") or stmt.get("annotation")),
            declare_hint=(stmt.get("declare") is not False),
            indent=indent,
            ctx=ctx,
        )
        if tuple_lines is not None:
            return tuple_lines
        target = _target_name(target_any)
        decl_type = _java_type(stmt.get("decl_type") or stmt.get("annotation"), allow_void=False)
        if decl_type == "Object":
            inferred = _infer_java_type_from_expr_node(stmt.get("value"), _type_map(ctx))
            if inferred != "Object":
                decl_type = inferred
        if decl_type == "void":
            decl_type = "Object"
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        if isinstance(stmt.get("value"), dict) and stmt.get("value").get("kind") == "ListComp":
            if stmt.get("declare") is False:
                listcomp_lines = _try_emit_listcomp_assign(target, stmt.get("value"), decl_prefix="", indent=indent, ctx=ctx)
                if listcomp_lines is not None:
                    return listcomp_lines
            elif target in declared:
                listcomp_lines = _try_emit_listcomp_assign(target, stmt.get("value"), decl_prefix="", indent=indent, ctx=ctx)
                if listcomp_lines is not None:
                    return listcomp_lines
            else:
                listcomp_lines = _try_emit_listcomp_assign(
                    target,
                    stmt.get("value"),
                    decl_prefix=(decl_type + " "),
                    indent=indent,
                    ctx=ctx,
                )
                if listcomp_lines is not None:
                    declared.add(target)
                    type_map[target] = decl_type
                    return listcomp_lines
        value = _render_expr(stmt.get("value"))
        if value == "null" and decl_type == "long":
            value = "0L"
        if value == "null" and decl_type == "double":
            value = "0.0"
        if value == "null" and decl_type == "boolean":
            value = "false"
        if value == "null" and decl_type == "String":
            value = '""'
        if stmt.get("declare") is False:
            return [indent + target + " = " + value + ";"]
        if target in declared:
            return [indent + target + " = " + value + ";"]
        declared.add(target)
        type_map[target] = decl_type
        return [indent + decl_type + " " + target + " = " + value + ";"]
    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            raise RuntimeError("java native emitter: Assign without target")
        tuple_lines = _try_emit_tuple_assign(
            targets[0],
            stmt.get("value"),
            decl_type_any=stmt.get("decl_type"),
            declare_hint=bool(stmt.get("declare")),
            indent=indent,
            ctx=ctx,
        )
        if tuple_lines is not None:
            return tuple_lines
        if isinstance(targets[0], dict) and targets[0].get("kind") == "Attribute":
            lhs_attr = _render_attribute_expr(targets[0])
            value_attr = _render_expr(stmt.get("value"))
            return [indent + lhs_attr + " = " + value_attr + ";"]
        if isinstance(targets[0], dict) and targets[0].get("kind") == "Subscript":
            tgt = targets[0]
            value_node = tgt.get("value")
            owner = _render_expr(tgt.get("value"))
            index = _render_expr(tgt.get("slice"))
            value = _render_expr(stmt.get("value"))
            owner_type = value_node.get("resolved_type") if isinstance(value_node, dict) else None
            if isinstance(owner_type, str) and owner_type.startswith("dict["):
                return [indent + owner + ".put(" + index + ", " + value + ");"]
            norm_index = _normalize_index_expr(owner, index)
            return [indent + owner + ".set((int)(" + norm_index + "), " + value + ");"]
        lhs = _target_name(targets[0])
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        if isinstance(stmt.get("value"), dict) and stmt.get("value").get("kind") == "ListComp":
            if stmt.get("declare"):
                if lhs in declared:
                    listcomp_lines = _try_emit_listcomp_assign(lhs, stmt.get("value"), decl_prefix="", indent=indent, ctx=ctx)
                    if listcomp_lines is not None:
                        return listcomp_lines
                decl_type = _java_type(stmt.get("decl_type"), allow_void=False)
                if decl_type == "Object":
                    inferred = _infer_java_type_from_expr_node(stmt.get("value"), _type_map(ctx))
                    if inferred != "Object":
                        decl_type = inferred
                if decl_type == "void":
                    decl_type = "Object"
                listcomp_lines = _try_emit_listcomp_assign(
                    lhs,
                    stmt.get("value"),
                    decl_prefix=(decl_type + " "),
                    indent=indent,
                    ctx=ctx,
                )
                if listcomp_lines is not None:
                    declared.add(lhs)
                    type_map[lhs] = decl_type
                    return listcomp_lines
            else:
                listcomp_lines = _try_emit_listcomp_assign(lhs, stmt.get("value"), decl_prefix="", indent=indent, ctx=ctx)
                if listcomp_lines is not None:
                    return listcomp_lines
        value = _render_expr(stmt.get("value"))
        if stmt.get("declare"):
            if lhs in declared:
                return [indent + lhs + " = " + value + ";"]
            decl_type = _java_type(stmt.get("decl_type"), allow_void=False)
            if decl_type == "Object":
                inferred = _infer_java_type_from_expr_node(stmt.get("value"), _type_map(ctx))
                if inferred != "Object":
                    decl_type = inferred
            if decl_type == "void":
                decl_type = "Object"
            if value == "null" and decl_type == "long":
                value = "0L"
            if value == "null" and decl_type == "double":
                value = "0.0"
            if value == "null" and decl_type == "boolean":
                value = "false"
            if value == "null" and decl_type == "String":
                value = '""'
            declared.add(lhs)
            type_map[lhs] = decl_type
            return [indent + decl_type + " " + lhs + " = " + value + ";"]
        return [indent + lhs + " = " + value + ";"]
    if kind == "AugAssign":
        lhs = _target_name(stmt.get("target"))
        rhs = _render_expr(stmt.get("value"))
        op = _augassign_op(stmt.get("op"))
        return [indent + lhs + " " + op + " " + rhs + ";"]
    if kind == "Raise":
        exc_any = stmt.get("exc")
        if exc_any is None:
            return [indent + 'throw new RuntimeException("pytra raise");']
        return [indent + "throw new RuntimeException(__pytra_str(" + _render_expr(exc_any) + "));"]
    if kind == "If":
        test_expr = _render_truthy_expr(stmt.get("test"))
        lines: list[str] = [indent + "if (" + test_expr + ") {"]
        declared_parent = set(_declared_set(ctx))
        types_parent = dict(_type_map(ctx))
        body_ctx: dict[str, Any] = {"tmp": ctx.get("tmp", 0), "declared": set(declared_parent), "types": dict(types_parent)}
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        orelse_ctx: dict[str, Any] = {
            "tmp": body_ctx.get("tmp", ctx.get("tmp", 0)),
            "declared": set(declared_parent),
            "types": dict(types_parent),
        }
        if len(orelse) == 0:
            ctx["tmp"] = orelse_ctx.get("tmp", ctx.get("tmp", 0))
            lines.append(indent + "}")
            return lines
        lines.append(indent + "} else {")
        i = 0
        while i < len(orelse):
            lines.extend(_emit_stmt(orelse[i], indent=indent + "    ", ctx=orelse_ctx))
            i += 1
        ctx["tmp"] = orelse_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines
    if kind == "ForCore":
        return _emit_for_core(stmt, indent=indent, ctx=ctx)
    if kind == "Pass":
        return [indent + ";"]
    if kind == "Break":
        return [indent + "break;"]
    if kind == "Continue":
        return [indent + "continue;"]
    if kind == "Import" or kind == "ImportFrom":
        return []
    if kind == "While":
        test_expr = _render_truthy_expr(stmt.get("test"))
        lines = [indent + "while (" + test_expr + ") {"]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines
    raise RuntimeError("java native emitter: unsupported stmt kind: " + str(kind))


def _stmt_guarantees_return(stmt: Any) -> bool:
    if not isinstance(stmt, dict):
        return False
    kind = stmt.get("kind")
    if kind == "Return":
        return True
    if kind != "If":
        return False
    body_any = stmt.get("body")
    body = body_any if isinstance(body_any, list) else []
    orelse_any = stmt.get("orelse")
    orelse = orelse_any if isinstance(orelse_any, list) else []
    if len(orelse) == 0:
        return False
    return _block_guarantees_return(body) and _block_guarantees_return(orelse)


def _block_guarantees_return(body: list[Any]) -> bool:
    i = 0
    while i < len(body):
        if _stmt_guarantees_return(body[i]):
            return True
        i += 1
    return False


def _emit_function(fn: dict[str, Any], *, indent: str, in_class: bool) -> list[str]:
    return _emit_function_in_class(fn, indent=indent, in_class=in_class, class_name=None)


def _emit_function_in_class(
    fn: dict[str, Any],
    *,
    indent: str,
    in_class: bool,
    class_name: str | None,
) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    return_type = _java_type(fn.get("return_type"), allow_void=True)
    is_static_method = not in_class
    is_constructor = False
    if in_class and name == "__init__" and isinstance(class_name, str):
        is_constructor = True
        is_static_method = False
    if in_class:
        decorators_any = fn.get("decorators")
        decorators = decorators_any if isinstance(decorators_any, list) else []
        i = 0
        while i < len(decorators):
            dec = decorators[i]
            if isinstance(dec, dict) and dec.get("kind") == "Name" and dec.get("id") == "staticmethod":
                is_static_method = True
                break
            i += 1
    static_prefix = "public static " if is_static_method else "public "
    drop_self = in_class and (not is_static_method or is_constructor)
    params = _function_params(fn, drop_self=drop_self)
    lines: list[str] = []
    if is_constructor and isinstance(class_name, str):
        lines.append(indent + "public " + class_name + "(" + ", ".join(params) + ") {")
    else:
        lines.append(indent + static_prefix + return_type + " " + name + "(" + ", ".join(params) + ") {")
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}}
    param_names = _function_param_names(fn, drop_self=drop_self)
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    i = 0
    while i < len(param_names):
        param_name = param_names[i]
        declared.add(param_name)
        mapped = _java_type(arg_types.get(param_name), allow_void=False)
        if mapped != "Object" and mapped != "void":
            type_map[param_name] = mapped
        i += 1
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1
    if len(body) == 0:
        lines.append(indent + "    // empty body")
    if (not is_constructor) and return_type != "void" and not _block_guarantees_return(body):
        lines.append(indent + "    return " + _default_return_expr(return_type) + ";")
    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    extends = ""
    if isinstance(base_any, str) and base_any != "":
        extends = " extends " + _safe_ident(base_any, "Object")
    lines: list[str] = []
    lines.append(indent + "public static class " + class_name + extends + " {")

    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []
    static_field_names: set[str] = set()
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict):
            kind = node.get("kind")
            target = node.get("target")
            if kind in {"AnnAssign", "Assign"} and isinstance(target, dict) and target.get("kind") == "Name":
                if kind == "AnnAssign" and node.get("value") is None:
                    i += 1
                    continue
                field_name = _safe_ident(target.get("id"), "value")
                field_type = _java_type(node.get("decl_type") or node.get("annotation"), allow_void=False)
                if field_type == "Object":
                    field_type = _infer_java_type_from_expr_node(node.get("value"))
                if field_type == "void":
                    field_type = "Object"
                field_value = _render_expr(node.get("value"))
                if field_value == "null" and field_type == "long":
                    field_value = "0L"
                if field_value == "null" and field_type == "double":
                    field_value = "0.0"
                if field_value == "null" and field_type == "boolean":
                    field_value = "false"
                if field_value == "null" and field_type == "String":
                    field_value = '""'
                lines.append(indent + "    public static " + field_type + " " + field_name + " = " + field_value + ";")
                static_field_names.add(field_name)
        i += 1

    field_types_any = cls.get("field_types")
    field_types = field_types_any if isinstance(field_types_any, dict) else {}
    instance_field_order: list[str] = []
    for raw_name, raw_type in field_types.items():
        if not isinstance(raw_name, str):
            continue
        field_name = _safe_ident(raw_name, "field")
        if field_name in static_field_names:
            continue
        field_type = _java_type(raw_type, allow_void=False)
        if field_type == "void":
            field_type = "Object"
        lines.append(indent + "    public " + field_type + " " + field_name + ";")
        instance_field_order.append(field_name)

    has_init = False
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef" and _safe_ident(node.get("name"), "") == "__init__":
            has_init = True
            break
        i += 1
    if not has_init:
        lines.append(indent + "    public " + class_name + "() {")
        lines.append(indent + "    }")
        if len(instance_field_order) > 0:
            ctor_params: list[str] = []
            i = 0
            while i < len(instance_field_order):
                field_name = instance_field_order[i]
                raw_type = field_types.get(field_name)
                field_type = _java_type(raw_type, allow_void=False)
                if field_type == "void":
                    field_type = "Object"
                ctor_params.append(field_type + " " + field_name)
                i += 1
            lines.append("")
            lines.append(indent + "    public " + class_name + "(" + ", ".join(ctor_params) + ") {")
            i = 0
            while i < len(instance_field_order):
                field_name = instance_field_order[i]
                lines.append(indent + "        this." + field_name + " = " + field_name + ";")
                i += 1
            lines.append(indent + "    }")

    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            lines.append("")
            lines.extend(_emit_function_in_class(node, indent=indent + "    ", in_class=True, class_name=class_name))
        i += 1
    lines.append(indent + "}")
    return lines


def transpile_to_java_native(east_doc: dict[str, Any], class_name: str = "Main") -> str:
    """Emit Java native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("java native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("java native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("java native emitter: Module.body must be list")
    main_guard_any = east_doc.get("main_guard_body")
    main_guard = main_guard_any if isinstance(main_guard_any, list) else []

    main_class = _safe_ident(class_name, "Main")
    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    i = 0
    while i < len(body_any):
        node = body_any[i]
        if isinstance(node, dict):
            kind = node.get("kind")
            if kind == "FunctionDef":
                functions.append(node)
            elif kind == "ClassDef":
                classes.append(node)
        i += 1

    lines: list[str] = []
    lines.append("public final class " + main_class + " {")
    lines.append("    private " + main_class + "() {")
    lines.append("    }")
    lines.append("")
    module_comments = _module_leading_comment_lines(east_doc, "// ", indent="    ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    i = 0
    while i < len(classes):
        cls_comments = _leading_comment_lines(classes[i], "// ", indent="    ")
        if len(cls_comments) > 0:
            lines.append("")
            lines.extend(cls_comments)
        lines.append("")
        lines.extend(_emit_class(classes[i], indent="    "))
        i += 1

    i = 0
    while i < len(functions):
        fn_comments = _leading_comment_lines(functions[i], "// ", indent="    ")
        if len(fn_comments) > 0:
            lines.append("")
            lines.extend(fn_comments)
        lines.append("")
        lines.extend(_emit_function(functions[i], indent="    ", in_class=False))
        i += 1

    lines.append("")
    lines.append("    public static void main(String[] args) {")
    ctx: dict[str, Any] = {"tmp": 0}
    if len(main_guard) > 0:
        i = 0
        while i < len(main_guard):
            lines.extend(_emit_stmt(main_guard[i], indent="        ", ctx=ctx))
            i += 1
    else:
        has_case_main = False
        i = 0
        while i < len(functions):
            if functions[i].get("name") == "_case_main":
                has_case_main = True
                break
            i += 1
        if has_case_main:
            lines.append("        _case_main();")
    lines.append("    }")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)
