"""EAST3 -> Swift native emitter (core lowering stage)."""

from __future__ import annotations

from pytra.std.typing import Any


_SWIFT_KEYWORDS = {
    "associatedtype",
    "class",
    "deinit",
    "enum",
    "extension",
    "func",
    "import",
    "init",
    "inout",
    "let",
    "operator",
    "precedencegroup",
    "protocol",
    "struct",
    "subscript",
    "typealias",
    "var",
    "break",
    "case",
    "continue",
    "default",
    "defer",
    "do",
    "else",
    "fallthrough",
    "for",
    "guard",
    "if",
    "in",
    "repeat",
    "return",
    "switch",
    "where",
    "while",
    "as",
    "is",
    "try",
    "throw",
}

_CLASS_NAMES: set[str] = set()


def _safe_ident(name: Any, fallback: str) -> str:
    if not isinstance(name, str) or name == "":
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
    if out[0].isdigit():
        out = "_" + out
    if out in _SWIFT_KEYWORDS:
        out = out + "_"
    return out


def _swift_string_literal(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\n", "\\n")
    return '"' + out + '"'


def _module_leading_comment_lines(east_doc: dict[str, Any], prefix: str) -> list[str]:
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
                out.append(prefix + text)
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


def _swift_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "Any"
    if type_name == "None":
        return "Void" if allow_void else "Any"
    if type_name in {"int", "int64", "uint8"}:
        return "Int64"
    if type_name in {"float", "float64"}:
        return "Double"
    if type_name == "bool":
        return "Bool"
    if type_name == "str":
        return "String"
    if type_name.startswith("list[") or type_name.startswith("tuple["):
        return "[Any]"
    if type_name.startswith("dict["):
        return "[AnyHashable: Any]"
    if type_name in {"bytes", "bytearray"}:
        return "[Any]"
    if type_name in {"unknown", "object", "any"}:
        return "Any"
    if type_name.isidentifier():
        return _safe_ident(type_name, "Any")
    return "Any"


def _default_return_expr(swift_type: str) -> str:
    if swift_type == "Int64":
        return "0"
    if swift_type == "Double":
        return "0.0"
    if swift_type == "Bool":
        return "false"
    if swift_type == "String":
        return '""'
    if swift_type == "[Any]":
        return "[]"
    if swift_type == "[AnyHashable: Any]":
        return "[:]"
    if swift_type == "Void":
        return ""
    if swift_type == "Any":
        return "__pytra_any_default()"
    return swift_type + "()"


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


def _cast_from_any(expr: str, swift_type: str) -> str:
    if swift_type == "Int64":
        return "__pytra_int(" + expr + ")"
    if swift_type == "Double":
        return "__pytra_float(" + expr + ")"
    if swift_type == "Bool":
        return "__pytra_truthy(" + expr + ")"
    if swift_type == "String":
        return "__pytra_str(" + expr + ")"
    if swift_type == "[Any]":
        return "__pytra_as_list(" + expr + ")"
    if swift_type == "[AnyHashable: Any]":
        return "__pytra_as_dict(" + expr + ")"
    if swift_type == "Any":
        return expr
    if swift_type in _CLASS_NAMES:
        return "(" + expr + " as? " + swift_type + ") ?? " + swift_type + "()"
    return expr


def _render_name_expr(expr: dict[str, Any]) -> str:
    return _safe_ident(expr.get("id"), "value")


def _render_constant_expr(expr: dict[str, Any]) -> str:
    if "value" not in expr:
        return "__pytra_any_default()"
    value = expr.get("value")
    if value is None:
        resolved = expr.get("resolved_type")
        if resolved in {"int", "int64", "uint8"}:
            return "Int64(0)"
        if resolved in {"float", "float64"}:
            return "Double(0)"
        if resolved == "bool":
            return "false"
        if resolved == "str":
            return '""'
        return "__pytra_any_default()"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "Int64(" + str(value) + ")"
    if isinstance(value, float):
        return "Double(" + str(value) + ")"
    if isinstance(value, str):
        return _swift_string_literal(value)
    return "__pytra_any_default()"


def _render_truthy_expr(expr: Any) -> str:
    if not isinstance(expr, dict):
        return "__pytra_truthy(" + _render_expr(expr) + ")"
    resolved = expr.get("resolved_type")
    rendered = _render_expr(expr)
    if isinstance(resolved, str):
        if resolved == "bool":
            return rendered
        if resolved in {"int", "int64", "uint8"}:
            return "(" + rendered + " != 0)"
        if resolved in {"float", "float64"}:
            return "(" + rendered + " != 0.0)"
        if resolved == "str":
            return "(" + rendered + " != \"\")"
        if resolved.startswith("list[") or resolved.startswith("tuple[") or resolved.startswith("dict[") or resolved in {"bytes", "bytearray"}:
            return "(__pytra_len(" + rendered + ") != 0)"
    kind = expr.get("kind")
    if kind in {"Compare", "BoolOp", "IsInstance"}:
        return rendered
    return "__pytra_truthy(" + rendered + ")"


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


def _render_unary_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    operand = _render_expr(expr.get("operand"))
    if op == "USub":
        return "(-" + operand + ")"
    if op == "UAdd":
        return "(+" + operand + ")"
    if op == "Not":
        return "(!" + _render_truthy_expr(expr.get("operand")) + ")"
    return operand


def _render_binop_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    if op == "Mult":
        left_any = expr.get("left")
        right_any = expr.get("right")
        if isinstance(left_any, dict) and left_any.get("kind") == "List":
            elems_any = left_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            if len(elems) == 1:
                return "__pytra_list_repeat(" + _render_expr(elems[0]) + ", " + _render_expr(right_any) + ")"
        if isinstance(right_any, dict) and right_any.get("kind") == "List":
            elems_any = right_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            if len(elems) == 1:
                return "__pytra_list_repeat(" + _render_expr(elems[0]) + ", " + _render_expr(left_any) + ")"

    left_expr = _render_expr(expr.get("left"))
    right_expr = _render_expr(expr.get("right"))
    resolved = expr.get("resolved_type")

    if op == "Div":
        return "(__pytra_float(" + left_expr + ") / __pytra_float(" + right_expr + "))"

    if op == "FloorDiv":
        return "(__pytra_int(__pytra_int(" + left_expr + ") / __pytra_int(" + right_expr + ")))"

    if op == "Mod":
        return "(__pytra_int(" + left_expr + ") % __pytra_int(" + right_expr + "))"

    if resolved == "str" and op == "Add":
        return "(__pytra_str(" + left_expr + ") + __pytra_str(" + right_expr + "))"

    if resolved in {"int", "int64", "uint8"}:
        sym = _bin_op_symbol(op)
        return "(__pytra_int(" + left_expr + ") " + sym + " __pytra_int(" + right_expr + "))"

    if resolved in {"float", "float64"}:
        sym = _bin_op_symbol(op)
        return "(__pytra_float(" + left_expr + ") " + sym + " __pytra_float(" + right_expr + "))"

    sym = _bin_op_symbol(op)
    return "(" + left_expr + " " + sym + " " + right_expr + ")"


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
    left = _render_expr(expr.get("left"))
    ops_any = expr.get("ops")
    comps_any = expr.get("comparators")
    ops = ops_any if isinstance(ops_any, list) else []
    comps = comps_any if isinstance(comps_any, list) else []
    if len(ops) == 0 or len(comps) == 0:
        return "false"

    parts: list[str] = []
    cur_left = left
    i = 0
    while i < len(ops) and i < len(comps):
        comp_node = comps[i]
        right = _render_expr(comp_node)
        op = ops[i]

        if op == "In" or op == "NotIn":
            expr_txt = "__pytra_contains(" + right + ", " + cur_left + ")"
            if op == "NotIn":
                expr_txt = "(!" + expr_txt + ")"
            parts.append("(" + expr_txt + ")")
            cur_left = right
            i += 1
            continue

        left_type = ""
        right_type = ""
        if i == 0 and isinstance(expr.get("left"), dict):
            left_any = expr.get("left", {}).get("resolved_type")
            left_type = left_any if isinstance(left_any, str) else ""
        elif i > 0 and isinstance(comps[i - 1], dict):
            left_any = comps[i - 1].get("resolved_type")
            left_type = left_any if isinstance(left_any, str) else ""
        if isinstance(comp_node, dict):
            right_any = comp_node.get("resolved_type")
            right_type = right_any if isinstance(right_any, str) else ""

        symbol = _compare_op_symbol(op)
        if left_type == "str" or right_type == "str":
            lhs = "__pytra_str(" + cur_left + ")"
            rhs = "__pytra_str(" + right + ")"
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        elif left_type in {"int", "int64", "uint8"} or right_type in {"int", "int64", "uint8"}:
            lhs = "__pytra_int(" + cur_left + ")"
            rhs = "__pytra_int(" + right + ")"
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        elif left_type in {"float", "float64"} or right_type in {"float", "float64"}:
            lhs = "__pytra_float(" + cur_left + ")"
            rhs = "__pytra_float(" + right + ")"
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        else:
            if op in {"Eq", "NotEq"}:
                lhs = "__pytra_str(" + cur_left + ")"
                rhs = "__pytra_str(" + right + ")"
                parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
            else:
                lhs = "__pytra_float(" + cur_left + ")"
                rhs = "__pytra_float(" + right + ")"
                parts.append("(" + lhs + " " + symbol + " " + rhs + ")")

        cur_left = right
        i += 1

    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _render_boolop_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    values_any = expr.get("values")
    values = values_any if isinstance(values_any, list) else []
    if len(values) == 0:
        return "false"
    rendered: list[str] = []
    i = 0
    while i < len(values):
        rendered.append(_render_truthy_expr(values[i]))
        i += 1
    delim = " && " if op == "And" else " || "
    return "(" + delim.join(rendered) + ")"


def _math_call_name(attr: str) -> str:
    if attr == "sqrt":
        return "sqrt"
    if attr == "sin":
        return "sin"
    if attr == "cos":
        return "cos"
    if attr == "tan":
        return "tan"
    if attr == "exp":
        return "exp"
    if attr == "log":
        return "log"
    if attr == "pow":
        return "pow"
    return _safe_ident(attr, "call")


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    value_any = expr.get("value")
    attr = _safe_ident(expr.get("attr"), "field")
    if isinstance(value_any, dict) and value_any.get("kind") == "Name":
        owner = _safe_ident(value_any.get("id"), "")
        if owner == "math" and attr == "pi":
            return "Double.pi"
        if owner == "math" and attr == "e":
            return "exp(1.0)"
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
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered_assert_args) + ")"
    if callee_name == "perf_counter":
        return "__pytra_perf_counter()"
    if callee_name == "bytearray":
        if len(args) == 0:
            return "[]"
        return "__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee_name == "bytes":
        if len(args) == 0:
            return "[]"
        return "__pytra_bytes(" + _render_expr(args[0]) + ")"
    if callee_name == "int":
        if len(args) == 0:
            return "Int64(0)"
        return "__pytra_int(" + _render_expr(args[0]) + ")"
    if callee_name == "float":
        if len(args) == 0:
            return "Double(0)"
        return "__pytra_float(" + _render_expr(args[0]) + ")"
    if callee_name == "bool":
        if len(args) == 0:
            return "false"
        return "__pytra_truthy(" + _render_expr(args[0]) + ")"
    if callee_name == "str":
        if len(args) == 0:
            return '""'
        return "__pytra_str(" + _render_expr(args[0]) + ")"
    if callee_name == "len":
        if len(args) == 0:
            return "Int64(0)"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "min":
        if len(args) == 0:
            return "Int64(0)"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_min(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name == "max":
        if len(args) == 0:
            return "Int64(0)"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_max(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name in {"save_gif", "write_rgb_png"}:
        rendered_noop_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_noop_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_noop(" + ", ".join(rendered_noop_args) + ")"
    if callee_name == "grayscale_palette":
        return "[]"
    if callee_name == "print":
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_print(" + ", ".join(rendered_args) + ")"

    func_any = expr.get("func")
    if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
        attr_name = _safe_ident(func_any.get("attr"), "")
        owner_any = func_any.get("value")
        if attr_name == "__init__" and isinstance(owner_any, dict) and owner_any.get("kind") == "Call":
            if _call_name(owner_any) == "super":
                return "__pytra_noop()"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner = _safe_ident(owner_any.get("id"), "")
            if owner == "math":
                rendered_math_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_math_args.append("__pytra_float(" + _render_expr(args[i]) + ")")
                    i += 1
                return _math_call_name(attr_name) + "(" + ", ".join(rendered_math_args) + ")"
        if attr_name == "isdigit" and len(args) == 0:
            return "__pytra_isdigit(" + _render_expr(owner_any) + ")"
        if attr_name == "isalpha" and len(args) == 0:
            return "__pytra_isalpha(" + _render_expr(owner_any) + ")"
        owner_expr = _render_expr(owner_any)
        if attr_name in {"write_rgb_png", "save_gif"}:
            rendered_noop_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_noop_args.append(_render_expr(args[i]))
                i += 1
            return "__pytra_noop(" + ", ".join(rendered_noop_args) + ")"
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return owner_expr + "." + attr_name + "(" + ", ".join(rendered_args) + ")"

    if callee_name in _CLASS_NAMES:
        rendered_ctor_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_ctor_args.append(_render_expr(args[i]))
            i += 1
        return callee_name + "(" + ", ".join(rendered_ctor_args) + ")"

    func_expr = _render_expr(expr.get("func"))
    rendered_args = []
    i = 0
    while i < len(args):
        rendered_args.append(_render_expr(args[i]))
        i += 1
    return func_expr + "(" + ", ".join(rendered_args) + ")"


def _render_isinstance_check(lhs: str, typ: Any) -> str:
    if not isinstance(typ, dict):
        return "false"
    if typ.get("kind") == "Name":
        name = _safe_ident(typ.get("id"), "")
        if name in {"int", "int64"}:
            return "__pytra_is_int(" + lhs + ")"
        if name in {"float", "float64"}:
            return "__pytra_is_float(" + lhs + ")"
        if name == "bool":
            return "__pytra_is_bool(" + lhs + ")"
        if name == "str":
            return "__pytra_is_str(" + lhs + ")"
        if name in {"list", "bytes", "bytearray"}:
            return "__pytra_is_list(" + lhs + ")"
        if name in _CLASS_NAMES:
            return "__pytra_is_" + name + "(" + lhs + ")"
        return "false"
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


def _render_expr(expr: Any) -> str:
    if not isinstance(expr, dict):
        return "__pytra_any_default()"
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

    if kind == "List" or kind == "Tuple":
        elements_any = expr.get("elements")
        if not isinstance(elements_any, list):
            elements_any = expr.get("elts")
        elements = elements_any if isinstance(elements_any, list) else []
        rendered: list[str] = []
        i = 0
        while i < len(elements):
            rendered.append(_render_expr(elements[i]))
            i += 1
        return "[" + ", ".join(rendered) + "]"

    if kind == "Dict":
        keys_any = expr.get("keys")
        vals_any = expr.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        vals = vals_any if isinstance(vals_any, list) else []
        if len(keys) == 0 or len(vals) == 0:
            return "[:]"
        parts: list[str] = []
        i = 0
        while i < len(keys) and i < len(vals):
            parts.append("AnyHashable(__pytra_str(" + _render_expr(keys[i]) + ")): " + _render_expr(vals[i]))
            i += 1
        return "[" + ", ".join(parts) + "]"

    if kind == "ListComp":
        gens_any = expr.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "[]"
        gen = gens[0]
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if len(ifs) != 0:
            return "[]"
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
            return "[]"
        if not isinstance(iter_any, dict) or iter_any.get("kind") != "RangeExpr":
            return "[]"
        loop_var = _safe_ident(target_any.get("id"), "i")
        if loop_var == "_":
            loop_var = "__lc_i"
        start = _render_expr(iter_any.get("start"))
        stop = _render_expr(iter_any.get("stop"))
        step = _render_expr(iter_any.get("step"))
        elt = _render_expr(expr.get("elt"))
        return (
            "({ () -> [Any] in "
            "var __out: [Any] = []; "
            "let __step = __pytra_int("
            + step
            + "); "
            "var "
            + loop_var
            + " = __pytra_int("
            + start
            + "); "
            "while ((__step >= 0 && "
            + loop_var
            + " < __pytra_int("
            + stop
            + ")) || (__step < 0 && "
            + loop_var
            + " > __pytra_int("
            + stop
            + "))) { "
            "__out.append("
            + elt
            + "); "
            + loop_var
            + " += __step "
            "}; "
            "return __out "
            "})()"
        )

    if kind == "IfExp":
        test_expr = _render_truthy_expr(expr.get("test"))
        body_expr = _render_expr(expr.get("body"))
        else_expr = _render_expr(expr.get("orelse"))
        return "__pytra_ifexp(" + test_expr + ", " + body_expr + ", " + else_expr + ")"

    if kind == "Subscript":
        owner = _render_expr(expr.get("value"))
        index_any = expr.get("slice")
        if isinstance(index_any, dict) and index_any.get("kind") == "Slice":
            lower_any = index_any.get("lower")
            upper_any = index_any.get("upper")
            lower = _render_expr(lower_any) if isinstance(lower_any, dict) else "Int64(0)"
            upper = _render_expr(upper_any) if isinstance(upper_any, dict) else "__pytra_len(" + owner + ")"
            return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"

        index = _render_expr(index_any)
        base = "__pytra_getIndex(" + owner + ", " + index + ")"
        resolved = expr.get("resolved_type")
        swift_t = _swift_type(resolved, allow_void=False)
        return _cast_from_any(base, swift_t)

    if kind == "IsInstance":
        lhs = _render_expr(expr.get("value"))
        return _render_isinstance_check(lhs, expr.get("expected_type_id"))

    if kind == "ObjLen":
        return "__pytra_len(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjStr":
        return "__pytra_str(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjBool":
        return "__pytra_truthy(" + _render_expr(expr.get("value")) + ")"

    if kind == "Unbox" or kind == "Box":
        return _render_expr(expr.get("value"))

    return "__pytra_any_default()"


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
        out.append(name + ": " + _swift_type(arg_types.get(name), allow_void=False))
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


def _fresh_tmp(ctx: dict[str, Any], prefix: str) -> str:
    idx = ctx.get("tmp", 0)
    if not isinstance(idx, int):
        idx = 0
    ctx["tmp"] = idx + 1
    return "__" + prefix + "_" + str(idx)


def _declared_set(ctx: dict[str, Any]) -> set[str]:
    declared = ctx.get("declared")
    if isinstance(declared, set):
        return declared
    out: set[str] = set()
    ctx["declared"] = out
    return out


def _type_map(ctx: dict[str, Any]) -> dict[str, str]:
    types = ctx.get("types")
    if isinstance(types, dict):
        return types
    out: dict[str, str] = {}
    ctx["types"] = out
    return out


def _infer_swift_type(expr: Any, type_map: dict[str, str] | None = None) -> str:
    if not isinstance(expr, dict):
        return "Any"
    kind = expr.get("kind")
    if kind == "Name" and isinstance(type_map, dict):
        ident = _safe_ident(expr.get("id"), "")
        if ident in type_map:
            return type_map[ident]
    if kind == "Call":
        name = _call_name(expr)
        if name == "perf_counter":
            return "Double"
        if name == "int":
            return "Int64"
        if name == "float":
            return "Double"
        if name == "bool":
            return "Bool"
        if name == "str":
            return "String"
        if name == "bytearray" or name == "bytes":
            return "[Any]"
        if name == "len":
            return "Int64"
        if name in {"min", "max"}:
            return "Int64"
        if name in _CLASS_NAMES:
            return name
    if kind == "BinOp":
        op = expr.get("op")
        if op == "Div":
            return "Double"
        left_t = _infer_swift_type(expr.get("left"), type_map)
        right_t = _infer_swift_type(expr.get("right"), type_map)
        if left_t == "Double" or right_t == "Double":
            return "Double"
        if left_t == "Int64" and right_t == "Int64":
            return "Int64"
        if op == "Mult":
            left_any = expr.get("left")
            right_any = expr.get("right")
            if isinstance(left_any, dict) and left_any.get("kind") == "List":
                return "[Any]"
            if isinstance(right_any, dict) and right_any.get("kind") == "List":
                return "[Any]"
    if kind == "IfExp":
        body_t = _infer_swift_type(expr.get("body"), type_map)
        else_t = _infer_swift_type(expr.get("orelse"), type_map)
        if body_t == else_t:
            return body_t
        if body_t == "Double" or else_t == "Double":
            return "Double"
        if body_t == "Int64" and else_t == "Int64":
            return "Int64"
    resolved = expr.get("resolved_type")
    return _swift_type(resolved, allow_void=False)


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        raise RuntimeError("swift native emitter: unsupported ForCore iter_plan")
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("swift native emitter: unsupported ForCore target_plan")

    lines: list[str] = []
    if iter_plan_any.get("kind") == "StaticRangeForPlan" and target_plan_any.get("kind") == "NameTarget":
        target_name = _safe_ident(target_plan_any.get("id"), "i")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "loop")
        start = "__pytra_int(" + _render_expr(iter_plan_any.get("start")) + ")"
        stop = "__pytra_int(" + _render_expr(iter_plan_any.get("stop")) + ")"
        step = "__pytra_int(" + _render_expr(iter_plan_any.get("step")) + ")"
        step_tmp = _fresh_tmp(ctx, "step")
        lines.append(indent + "let " + step_tmp + " = " + step)
        lines.append(indent + "var " + target_name + " = " + start)
        lines.append(
            indent
            + "while (("
            + step_tmp
            + " >= 0 && "
            + target_name
            + " < "
            + stop
            + ") || ("
            + step_tmp
            + " < 0 && "
            + target_name
            + " > "
            + stop
            + ")) {"
        )
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = "Int64"
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        lines.append(indent + "    " + target_name + " += " + step_tmp)
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if iter_plan_any.get("kind") == "RuntimeIterForPlan" and target_plan_any.get("kind") == "NameTarget":
        iter_expr = _render_expr(iter_plan_any.get("iter_expr"))
        iter_tmp = _fresh_tmp(ctx, "iter")
        idx_tmp = _fresh_tmp(ctx, "i")
        target_name = _safe_ident(target_plan_any.get("id"), "item")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "item")
        lines.append(indent + "let " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
        lines.append(indent + "var " + idx_tmp + ": Int64 = 0")
        lines.append(indent + "while " + idx_tmp + " < Int64(" + iter_tmp + ".count) {")
        lines.append(indent + "    let " + target_name + " = " + iter_tmp + "[Int(" + idx_tmp + ")]")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = "Any"
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        lines.append(indent + "    " + idx_tmp + " += 1")
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    raise RuntimeError("swift native emitter: unsupported ForCore plan")


def _emit_tuple_assign(
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

    tuple_tmp = _fresh_tmp(ctx, "tuple")
    lines: list[str] = [indent + "let " + tuple_tmp + " = __pytra_as_list(" + _render_expr(value_any) + ")"]
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    tuple_types = _tuple_element_types(decl_type_any)
    if len(tuple_types) == 0 and isinstance(value_any, dict):
        tuple_types = _tuple_element_types(value_any.get("resolved_type"))

    i = 0
    while i < len(elems):
        elem = elems[i]
        if not isinstance(elem, dict):
            return None
        kind = elem.get("kind")
        rhs = tuple_tmp + "[" + str(i) + "]"
        elem_type = "Any"
        if i < len(tuple_types):
            elem_type = _swift_type(tuple_types[i], allow_void=False)
        casted = _cast_from_any(rhs, elem_type)

        if kind == "Name":
            name = _safe_ident(elem.get("id"), "tmp_" + str(i))
            if declare_hint and name not in declared:
                lines.append(indent + "var " + name + ": " + elem_type + " = " + casted)
                declared.add(name)
                type_map[name] = elem_type
            else:
                lines.append(indent + name + " = " + casted)
        elif kind == "Subscript":
            owner = _render_expr(elem.get("value"))
            index = _render_expr(elem.get("slice"))
            lines.append(indent + "__pytra_setIndex(" + owner + ", " + index + ", " + casted + ")")
        else:
            return None
        i += 1

    return lines


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        raise RuntimeError("swift native emitter: unsupported statement")
    kind = stmt.get("kind")

    if kind == "Return":
        if "value" in stmt and stmt.get("value") is not None:
            return [indent + "return " + _render_expr(stmt.get("value"))]
        return [indent + "return"]

    if kind == "Expr":
        value_any = stmt.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name":
            raw_ident = value_any.get("id")
            if raw_ident == "break":
                return [indent + "break"]
            if raw_ident == "continue":
                return [indent + "continue"]
        if isinstance(value_any, dict) and value_any.get("kind") == "Call":
            func_any = value_any.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
                attr = _safe_ident(func_any.get("attr"), "")
                if attr == "append":
                    owner = _render_expr(func_any.get("value"))
                    args_any = value_any.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) == 1:
                        return [indent + owner + " = __pytra_as_list(" + owner + "); " + owner + ".append(" + _render_expr(args[0]) + ")"]
                if attr == "pop":
                    owner = _render_expr(func_any.get("value"))
                    args_any = value_any.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) == 0:
                        return [indent + owner + " = __pytra_pop_last(__pytra_as_list(" + owner + "))"]
        return [indent + _render_expr(value_any)]

    if kind == "AnnAssign":
        target_any = stmt.get("target")
        if isinstance(target_any, dict) and target_any.get("kind") == "Attribute":
            return [indent + _render_attribute_expr(target_any) + " = " + _render_expr(stmt.get("value"))]

        tuple_lines = _emit_tuple_assign(
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
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        swift_type = _swift_type(stmt.get("decl_type") or stmt.get("annotation"), allow_void=False)
        if swift_type == "Any":
            inferred = _infer_swift_type(stmt.get("value"), _type_map(ctx))
            if inferred != "Any":
                swift_type = inferred

        stmt_value = stmt.get("value")
        if stmt_value is None:
            value = _default_return_expr(swift_type)
        else:
            value = _render_expr(stmt_value)
            if swift_type != "Any":
                value = _cast_from_any(value, swift_type)
        if stmt.get("declare") is False or target in declared:
            if target not in declared:
                declared.add(target)
                type_map[target] = swift_type
                return [indent + "var " + target + ": " + swift_type + " = " + value]
            if target in type_map and type_map[target] != "Any":
                if stmt_value is None:
                    return [indent + target + " = " + _default_return_expr(type_map[target])]
                return [indent + target + " = " + _cast_from_any(_render_expr(stmt_value), type_map[target])]
            return [indent + target + " = " + value]

        declared.add(target)
        type_map[target] = swift_type
        return [indent + "var " + target + ": " + swift_type + " = " + value]

    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            raise RuntimeError("swift native emitter: Assign without target")

        tuple_lines = _emit_tuple_assign(
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
            return [indent + lhs_attr + " = " + value_attr]

        if isinstance(targets[0], dict) and targets[0].get("kind") == "Subscript":
            tgt = targets[0]
            owner = _render_expr(tgt.get("value"))
            index = _render_expr(tgt.get("slice"))
            value = _render_expr(stmt.get("value"))
            return [indent + "__pytra_setIndex(" + owner + ", " + index + ", " + value + ")"]

        lhs = _target_name(targets[0])
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        value = _render_expr(stmt.get("value"))

        if stmt.get("declare"):
            if lhs in declared:
                if lhs in type_map and type_map[lhs] != "Any":
                    return [indent + lhs + " = " + _cast_from_any(value, type_map[lhs])]
                return [indent + lhs + " = " + value]
            swift_type = _swift_type(stmt.get("decl_type"), allow_void=False)
            if swift_type == "Any":
                inferred = _infer_swift_type(stmt.get("value"), _type_map(ctx))
                if inferred != "Any":
                    swift_type = inferred
            if swift_type != "Any":
                value = _cast_from_any(value, swift_type)
            declared.add(lhs)
            type_map[lhs] = swift_type
            return [indent + "var " + lhs + ": " + swift_type + " = " + value]

        if lhs not in declared:
            inferred = _infer_swift_type(stmt.get("value"), _type_map(ctx))
            declared.add(lhs)
            type_map[lhs] = inferred
            if inferred != "Any":
                value = _cast_from_any(value, inferred)
            return [indent + "var " + lhs + ": " + inferred + " = " + value]
        if lhs in type_map and type_map[lhs] != "Any":
            return [indent + lhs + " = " + _cast_from_any(value, type_map[lhs])]
        return [indent + lhs + " = " + value]

    if kind == "AugAssign":
        lhs = _target_name(stmt.get("target"))
        rhs = _render_expr(stmt.get("value"))
        op = stmt.get("op")
        if op == "Add":
            return [indent + lhs + " += " + rhs]
        if op == "Sub":
            return [indent + lhs + " -= " + rhs]
        if op == "Mult":
            return [indent + lhs + " *= " + rhs]
        if op == "Div":
            return [indent + lhs + " /= " + rhs]
        if op == "Mod":
            return [indent + lhs + " %= " + rhs]
        return [indent + lhs + " += " + rhs]

    if kind == "If":
        test_expr = _render_truthy_expr(stmt.get("test"))
        lines: list[str] = [indent + "if " + test_expr + " {"]
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

        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        if len(orelse) == 0:
            ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
            lines.append(indent + "}")
            return lines

        lines.append(indent + "} else {")
        orelse_ctx: dict[str, Any] = {
            "tmp": body_ctx.get("tmp", ctx.get("tmp", 0)),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
        }
        i = 0
        while i < len(orelse):
            lines.extend(_emit_stmt(orelse[i], indent=indent + "    ", ctx=orelse_ctx))
            i += 1
        ctx["tmp"] = orelse_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if kind == "ForCore":
        return _emit_for_core(stmt, indent=indent, ctx=ctx)

    if kind == "While":
        test_expr = _render_truthy_expr(stmt.get("test"))
        lines = [indent + "while " + test_expr + " {"]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines

    if kind == "Pass":
        return [indent + "_ = 0"]

    if kind == "Break":
        return [indent + "break"]

    if kind == "Continue":
        return [indent + "continue"]

    if kind == "Import" or kind == "ImportFrom":
        return []

    if kind == "Raise":
        return [indent + "fatalError(\"pytra raise\")"]

    raise RuntimeError("swift native emitter: unsupported stmt kind: " + str(kind))


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


def _emit_function(fn: dict[str, Any], *, indent: str, receiver_name: str | None = None) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    is_init = receiver_name is not None and name == "__init__"

    return_type = _swift_type(fn.get("return_type"), allow_void=True)
    if is_init:
        return_type = "Void"

    drop_self = receiver_name is not None
    params = _function_params(fn, drop_self=drop_self)

    lines: list[str] = []
    if is_init:
        lines.append(indent + "init(" + ", ".join(params) + ") {")
    else:
        sig = indent + "func " + name + "(" + ", ".join(params) + ")"
        if return_type != "Void":
            sig += " -> " + return_type
        lines.append(sig + " {")

    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []

    ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}}
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)

    param_names = _function_param_names(fn, drop_self=drop_self)
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    i = 0
    while i < len(param_names):
        p = param_names[i]
        declared.add(p)
        type_map[p] = _swift_type(arg_types.get(p), allow_void=False)
        i += 1

    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1

    if len(body) == 0:
        lines.append(indent + "    // empty body")

    if not is_init and return_type != "Void" and not _block_guarantees_return(body):
        lines.append(indent + "    return " + _default_return_expr(return_type))

    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
    extends = ": " + base_name if base_name != "" else ""

    lines: list[str] = []
    lines.append(indent + "final class " + class_name + extends + " {")

    field_types_any = cls.get("field_types")
    field_types = field_types_any if isinstance(field_types_any, dict) else {}
    for raw_name, raw_type in field_types.items():
        if not isinstance(raw_name, str):
            continue
        field_name = _safe_ident(raw_name, "field")
        field_type = _swift_type(raw_type, allow_void=False)
        default = _default_return_expr(field_type)
        if default == "":
            default = "__pytra_any_default()"
        lines.append(indent + "    var " + field_name + ": " + field_type + " = " + default)

    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []

    has_init = False
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            if _safe_ident(node.get("name"), "") == "__init__":
                has_init = True
            lines.append("")
            lines.extend(_emit_function(node, indent=indent + "    ", receiver_name=class_name))
        i += 1

    if not has_init:
        if len(body) > 0:
            lines.append("")
        lines.append(indent + "    init() {")
        lines.append(indent + "    }")

    lines.append(indent + "}")
    return lines


def _emit_runtime_helpers() -> list[str]:
    return [
        "func __pytra_noop(_ args: Any...) {}",
        "",
        "func __pytra_any_default() -> Any {",
        "    return Int64(0)",
        "}",
        "",
        "func __pytra_assert(_ args: Any...) -> String {",
        "    _ = args",
        "    return \"True\"",
        "}",
        "",
        "func __pytra_perf_counter() -> Double {",
        "    return Date().timeIntervalSince1970",
        "}",
        "",
        "func __pytra_truthy(_ v: Any?) -> Bool {",
        "    guard let value = v else { return false }",
        "    if let b = value as? Bool { return b }",
        "    if let i = value as? Int64 { return i != 0 }",
        "    if let i = value as? Int { return i != 0 }",
        "    if let d = value as? Double { return d != 0.0 }",
        "    if let s = value as? String { return s != \"\" }",
        "    if let a = value as? [Any] { return !a.isEmpty }",
        "    if let m = value as? [AnyHashable: Any] { return !m.isEmpty }",
        "    return true",
        "}",
        "",
        "func __pytra_int(_ v: Any?) -> Int64 {",
        "    guard let value = v else { return 0 }",
        "    if let i = value as? Int64 { return i }",
        "    if let i = value as? Int { return Int64(i) }",
        "    if let d = value as? Double { return Int64(d) }",
        "    if let b = value as? Bool { return b ? 1 : 0 }",
        "    if let s = value as? String { return Int64(s) ?? 0 }",
        "    return 0",
        "}",
        "",
        "func __pytra_float(_ v: Any?) -> Double {",
        "    guard let value = v else { return 0.0 }",
        "    if let d = value as? Double { return d }",
        "    if let f = value as? Float { return Double(f) }",
        "    if let i = value as? Int64 { return Double(i) }",
        "    if let i = value as? Int { return Double(i) }",
        "    if let b = value as? Bool { return b ? 1.0 : 0.0 }",
        "    if let s = value as? String { return Double(s) ?? 0.0 }",
        "    return 0.0",
        "}",
        "",
        "func __pytra_str(_ v: Any?) -> String {",
        "    guard let value = v else { return \"\" }",
        "    if let s = value as? String { return s }",
        "    return String(describing: value)",
        "}",
        "",
        "func __pytra_len(_ v: Any?) -> Int64 {",
        "    guard let value = v else { return 0 }",
        "    if let s = value as? String { return Int64(s.count) }",
        "    if let a = value as? [Any] { return Int64(a.count) }",
        "    if let m = value as? [AnyHashable: Any] { return Int64(m.count) }",
        "    return 0",
        "}",
        "",
        "func __pytra_index(_ i: Int64, _ n: Int64) -> Int64 {",
        "    if i < 0 {",
        "        return i + n",
        "    }",
        "    return i",
        "}",
        "",
        "func __pytra_getIndex(_ container: Any?, _ index: Any?) -> Any {",
        "    if let list = container as? [Any] {",
        "        if list.isEmpty { return __pytra_any_default() }",
        "        let i = __pytra_index(__pytra_int(index), Int64(list.count))",
        "        if i < 0 || i >= Int64(list.count) { return __pytra_any_default() }",
        "        return list[Int(i)]",
        "    }",
        "    if let dict = container as? [AnyHashable: Any] {",
        "        let key = AnyHashable(__pytra_str(index))",
        "        return dict[key] ?? __pytra_any_default()",
        "    }",
        "    if let s = container as? String {",
        "        let chars = Array(s)",
        "        if chars.isEmpty { return \"\" }",
        "        let i = __pytra_index(__pytra_int(index), Int64(chars.count))",
        "        if i < 0 || i >= Int64(chars.count) { return \"\" }",
        "        return String(chars[Int(i)])",
        "    }",
        "    return __pytra_any_default()",
        "}",
        "",
        "func __pytra_setIndex(_ container: Any?, _ index: Any?, _ value: Any?) {",
        "    if var list = container as? [Any] {",
        "        if list.isEmpty { return }",
        "        let i = __pytra_index(__pytra_int(index), Int64(list.count))",
        "        if i < 0 || i >= Int64(list.count) { return }",
        "        list[Int(i)] = value as Any",
        "        return",
        "    }",
        "    if var dict = container as? [AnyHashable: Any] {",
        "        let key = AnyHashable(__pytra_str(index))",
        "        dict[key] = value",
        "    }",
        "}",
        "",
        "func __pytra_slice(_ container: Any?, _ lower: Any?, _ upper: Any?) -> Any {",
        "    if let s = container as? String {",
        "        let chars = Array(s)",
        "        let n = Int64(chars.count)",
        "        var lo = __pytra_index(__pytra_int(lower), n)",
        "        var hi = __pytra_index(__pytra_int(upper), n)",
        "        if lo < 0 { lo = 0 }",
        "        if hi < 0 { hi = 0 }",
        "        if lo > n { lo = n }",
        "        if hi > n { hi = n }",
        "        if hi < lo { hi = lo }",
        "        if lo >= hi { return \"\" }",
        "        return String(chars[Int(lo)..<Int(hi)])",
        "    }",
        "    if let list = container as? [Any] {",
        "        let n = Int64(list.count)",
        "        var lo = __pytra_index(__pytra_int(lower), n)",
        "        var hi = __pytra_index(__pytra_int(upper), n)",
        "        if lo < 0 { lo = 0 }",
        "        if hi < 0 { hi = 0 }",
        "        if lo > n { lo = n }",
        "        if hi > n { hi = n }",
        "        if hi < lo { hi = lo }",
        "        if lo >= hi { return [Any]() }",
        "        return Array(list[Int(lo)..<Int(hi)])",
        "    }",
        "    return __pytra_any_default()",
        "}",
        "",
        "func __pytra_isdigit(_ v: Any?) -> Bool {",
        "    let s = __pytra_str(v)",
        "    if s.isEmpty { return false }",
        "    return s.unicodeScalars.allSatisfy { CharacterSet.decimalDigits.contains($0) }",
        "}",
        "",
        "func __pytra_isalpha(_ v: Any?) -> Bool {",
        "    let s = __pytra_str(v)",
        "    if s.isEmpty { return false }",
        "    return s.unicodeScalars.allSatisfy { CharacterSet.letters.contains($0) }",
        "}",
        "",
        "func __pytra_contains(_ container: Any?, _ value: Any?) -> Bool {",
        "    if let list = container as? [Any] {",
        "        let needle = __pytra_str(value)",
        "        for item in list {",
        "            if __pytra_str(item) == needle {",
        "                return true",
        "            }",
        "        }",
        "        return false",
        "    }",
        "    if let dict = container as? [AnyHashable: Any] {",
        "        return dict[AnyHashable(__pytra_str(value))] != nil",
        "    }",
        "    if let s = container as? String {",
        "        let needle = __pytra_str(value)",
        "        return s.contains(needle)",
        "    }",
        "    return false",
        "}",
        "",
        "func __pytra_ifexp(_ cond: Bool, _ a: Any, _ b: Any) -> Any {",
        "    return cond ? a : b",
        "}",
        "",
        "func __pytra_bytearray(_ initValue: Any?) -> [Any] {",
        "    if let i = initValue as? Int64 {",
        "        return Array(repeating: Int64(0), count: max(0, Int(i)))",
        "    }",
        "    if let i = initValue as? Int {",
        "        return Array(repeating: Int64(0), count: max(0, i))",
        "    }",
        "    if let arr = initValue as? [Any] {",
        "        return arr",
        "    }",
        "    return []",
        "}",
        "",
        "func __pytra_bytes(_ v: Any?) -> [Any] {",
        "    if let arr = v as? [Any] {",
        "        return arr",
        "    }",
        "    return []",
        "}",
        "",
        "func __pytra_list_repeat(_ value: Any, _ count: Any?) -> [Any] {",
        "    var out: [Any] = []",
        "    var i: Int64 = 0",
        "    let n = __pytra_int(count)",
        "    while i < n {",
        "        out.append(value)",
        "        i += 1",
        "    }",
        "    return out",
        "}",
        "",
        "func __pytra_as_list(_ v: Any?) -> [Any] {",
        "    if let arr = v as? [Any] { return arr }",
        "    return []",
        "}",
        "",
        "func __pytra_as_u8_list(_ v: Any?) -> [UInt8] {",
        "    if let arr = v as? [UInt8] { return arr }",
        "    return []",
        "}",
        "",
        "func __pytra_as_dict(_ v: Any?) -> [AnyHashable: Any] {",
        "    if let dict = v as? [AnyHashable: Any] { return dict }",
        "    return [:]",
        "}",
        "",
        "func __pytra_pop_last(_ v: [Any]) -> [Any] {",
        "    if v.isEmpty { return v }",
        "    return Array(v.dropLast())",
        "}",
        "",
        "func __pytra_print(_ args: Any...) {",
        "    if args.isEmpty {",
        "        Swift.print()",
        "        return",
        "    }",
        "    Swift.print(args.map { String(describing: $0) }.joined(separator: \" \"))",
        "}",
        "",
        "func __pytra_min(_ a: Any?, _ b: Any?) -> Any {",
        "    let af = __pytra_float(a)",
        "    let bf = __pytra_float(b)",
        "    if af < bf {",
        "        if __pytra_is_float(a) || __pytra_is_float(b) { return af }",
        "        return __pytra_int(a)",
        "    }",
        "    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }",
        "    return __pytra_int(b)",
        "}",
        "",
        "func __pytra_max(_ a: Any?, _ b: Any?) -> Any {",
        "    let af = __pytra_float(a)",
        "    let bf = __pytra_float(b)",
        "    if af > bf {",
        "        if __pytra_is_float(a) || __pytra_is_float(b) { return af }",
        "        return __pytra_int(a)",
        "    }",
        "    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }",
        "    return __pytra_int(b)",
        "}",
        "",
        "func __pytra_is_int(_ v: Any?) -> Bool {",
        "    return (v is Int) || (v is Int64)",
        "}",
        "",
        "func __pytra_is_float(_ v: Any?) -> Bool {",
        "    return v is Double",
        "}",
        "",
        "func __pytra_is_bool(_ v: Any?) -> Bool {",
        "    return v is Bool",
        "}",
        "",
        "func __pytra_is_str(_ v: Any?) -> Bool {",
        "    return v is String",
        "}",
        "",
        "func __pytra_is_list(_ v: Any?) -> Bool {",
        "    return v is [Any]",
        "}",
    ]


def transpile_to_swift_native(east_doc: dict[str, Any]) -> str:
    """Emit Swift native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("swift native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("swift native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("swift native emitter: Module.body must be list")
    main_guard_any = east_doc.get("main_guard_body")
    main_guard = main_guard_any if isinstance(main_guard_any, list) else []

    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    i = 0
    while i < len(body_any):
        node = body_any[i]
        if isinstance(node, dict):
            kind = node.get("kind")
            if kind == "ClassDef":
                classes.append(node)
            elif kind == "FunctionDef":
                functions.append(node)
        i += 1

    global _CLASS_NAMES
    _CLASS_NAMES = set()
    i = 0
    while i < len(classes):
        _CLASS_NAMES.add(_safe_ident(classes[i].get("name"), "PytraClass"))
        i += 1

    lines: list[str] = []
    lines.append("import Foundation")
    lines.append("")
    module_comments = _module_leading_comment_lines(east_doc, "// ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    i = 0
    while i < len(classes):
        cname = _safe_ident(classes[i].get("name"), "PytraClass")
        lines.append("")
        lines.append("func __pytra_is_" + cname + "(_ v: Any?) -> Bool {")
        lines.append("    return v is " + cname)
        lines.append("}")
        i += 1

    i = 0
    while i < len(classes):
        cls_comments = _leading_comment_lines(classes[i], "// ")
        if len(cls_comments) > 0:
            lines.append("")
            lines.extend(cls_comments)
        lines.append("")
        lines.extend(_emit_class(classes[i], indent=""))
        i += 1

    i = 0
    while i < len(functions):
        fn_comments = _leading_comment_lines(functions[i], "// ")
        if len(fn_comments) > 0:
            lines.append("")
            lines.extend(fn_comments)
        lines.append("")
        lines.extend(_emit_function(functions[i], indent="", receiver_name=None))
        i += 1

    lines.append("")
    lines.append("@main")
    lines.append("struct Main {")
    lines.append("    static func main() {")
    ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}}
    if len(main_guard) > 0:
        i = 0
        while i < len(main_guard):
            lines.extend(_emit_stmt(main_guard[i], indent="        ", ctx=ctx))
            i += 1
    else:
        has_case_main = False
        i = 0
        while i < len(functions):
            if _safe_ident(functions[i].get("name"), "") == "_case_main":
                has_case_main = True
                break
            i += 1
        if has_case_main:
            lines.append("        _case_main()")
    lines.append("    }")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)
