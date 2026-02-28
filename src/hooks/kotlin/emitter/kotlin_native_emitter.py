"""EAST3 -> Kotlin native emitter (core lowering stage)."""

from __future__ import annotations

from pytra.std.typing import Any


_KOTLIN_KEYWORDS = {
    "as",
    "break",
    "class",
    "continue",
    "do",
    "else",
    "false",
    "for",
    "fun",
    "if",
    "in",
    "interface",
    "is",
    "null",
    "object",
    "package",
    "return",
    "super",
    "this",
    "throw",
    "true",
    "try",
    "typealias",
    "val",
    "var",
    "when",
    "while",
}

_CLASS_NAMES: set[str] = set()
_FUNCTION_NAMES: set[str] = set()


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
    if out in _KOTLIN_KEYWORDS:
        out = out + "_"
    return out


def _kotlin_string_literal(text: str) -> str:
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


def _kotlin_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "Any?"
    if type_name == "None":
        return "Unit" if allow_void else "Any?"
    if type_name in {"int", "int64", "uint8"}:
        return "Long"
    if type_name in {"float", "float64"}:
        return "Double"
    if type_name == "bool":
        return "Boolean"
    if type_name == "str":
        return "String"
    if type_name.startswith("list[") or type_name.startswith("tuple["):
        return "MutableList<Any?>"
    if type_name.startswith("dict["):
        return "MutableMap<Any, Any?>"
    if type_name in {"bytes", "bytearray"}:
        return "MutableList<Any?>"
    if type_name in {"unknown", "object", "any"}:
        return "Any?"
    if type_name.isidentifier():
        return _safe_ident(type_name, "Any")
    return "Any?"


def _default_return_expr(kotlin_type: str) -> str:
    if kotlin_type == "Long":
        return "0L"
    if kotlin_type == "Double":
        return "0.0"
    if kotlin_type == "Boolean":
        return "false"
    if kotlin_type == "String":
        return '""'
    if kotlin_type == "MutableList<Any?>":
        return "mutableListOf()"
    if kotlin_type == "MutableMap<Any, Any?>":
        return "mutableMapOf()"
    if kotlin_type == "Unit":
        return ""
    if kotlin_type == "Any?":
        return "null"
    return kotlin_type + "()"


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


def _cast_from_any(expr: str, kotlin_type: str) -> str:
    if kotlin_type == "Long":
        return "__pytra_int(" + expr + ")"
    if kotlin_type == "Double":
        return "__pytra_float(" + expr + ")"
    if kotlin_type == "Boolean":
        return "__pytra_truthy(" + expr + ")"
    if kotlin_type == "String":
        return "__pytra_str(" + expr + ")"
    if kotlin_type == "MutableList<Any?>":
        return "__pytra_as_list(" + expr + ")"
    if kotlin_type == "MutableMap<Any, Any?>":
        return "__pytra_as_dict(" + expr + ")"
    if kotlin_type == "Any?":
        return expr
    if kotlin_type in _CLASS_NAMES:
        return "__pytra_as_" + kotlin_type + "(" + expr + ")"
    return expr


def _render_name_expr(expr: dict[str, Any]) -> str:
    name = _safe_ident(expr.get("id"), "value")
    if name == "self":
        return "this"
    if name in _FUNCTION_NAMES:
        return "::" + name
    return name


def _render_constant_expr(expr: dict[str, Any]) -> str:
    if "value" not in expr:
        return "__pytra_any_default()"
    value = expr.get("value")
    if value is None:
        resolved = expr.get("resolved_type")
        if resolved in {"int", "int64", "uint8"}:
            return "0L"
        if resolved in {"float", "float64"}:
            return "0.0"
        if resolved == "bool":
            return "false"
        if resolved == "str":
            return '""'
        return "__pytra_any_default()"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value) + "L"
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _kotlin_string_literal(value)
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
            return "(" + rendered + " != 0L)"
        if resolved in {"float", "float64"}:
            return "(" + rendered + " != 0.0)"
        if resolved == "str":
            return "(" + rendered + " != \"\")"
        if resolved.startswith("list[") or resolved.startswith("tuple[") or resolved.startswith("dict[") or resolved in {"bytes", "bytearray"}:
            return "(__pytra_len(" + rendered + ") != 0L)"
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
        return "kotlin.math.sqrt"
    if attr == "sin":
        return "kotlin.math.sin"
    if attr == "cos":
        return "kotlin.math.cos"
    if attr == "tan":
        return "kotlin.math.tan"
    if attr == "exp":
        return "kotlin.math.exp"
    if attr == "log":
        return "kotlin.math.ln"
    if attr == "pow":
        return "kotlin.math.pow"
    if attr == "floor":
        return "kotlin.math.floor"
    if attr == "ceil":
        return "kotlin.math.ceil"
    if attr == "abs":
        return "kotlin.math.abs"
    return _safe_ident(attr, "call")


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
    raw = func_any.get("id")
    if not isinstance(raw, str):
        return ""
    if raw == "super":
        return "super"
    return _safe_ident(raw, "")


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
            return "mutableListOf<Any?>()"
        return "__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee_name == "bytes":
        if len(args) == 0:
            return "mutableListOf<Any?>()"
        return "__pytra_bytes(" + _render_expr(args[0]) + ")"
    if callee_name == "int":
        if len(args) == 0:
            return "0L"
        return "__pytra_int(" + _render_expr(args[0]) + ")"
    if callee_name == "float":
        if len(args) == 0:
            return "0.0"
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
            return "0L"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "enumerate":
        if len(args) == 0:
            return "mutableListOf<Any?>()"
        return "__pytra_enumerate(" + _render_expr(args[0]) + ")"
    if callee_name == "min":
        if len(args) == 0:
            return "0L"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_min(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name == "max":
        if len(args) == 0:
            return "0L"
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
        return "mutableListOf<Any?>()"
    if callee_name == "print":
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_print(" + ", ".join(rendered_args) + ")"
    if callee_name in {"RuntimeError", "ValueError", "TypeError", "Exception", "AssertionError"}:
        if len(args) == 0:
            return '""'
        return _render_expr(args[0])

    func_any = expr.get("func")
    if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
        attr_name = _safe_ident(func_any.get("attr"), "")
        owner_any = func_any.get("value")
        if attr_name == "__init__" and isinstance(owner_any, dict) and owner_any.get("kind") == "Call":
            if _call_name(owner_any) in {"super", "super_"}:
                return "__pytra_noop()"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner = _safe_ident(owner_any.get("id"), "")
            if owner == "math":
                rendered_math_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_math_args.append("__pytra_float(" + _render_expr(args[i]) + ")")
                    i += 1
                if attr_name == "pow" and len(rendered_math_args) == 2:
                    return rendered_math_args[0] + ".pow(" + rendered_math_args[1] + ")"
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

    rendered_args = []
    i = 0
    while i < len(args):
        rendered_args.append(_render_expr(args[i]))
        i += 1
    if callee_name != "":
        return callee_name + "(" + ", ".join(rendered_args) + ")"
    func_expr = _render_expr(expr.get("func"))
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
        if len(rendered) == 0:
            return "mutableListOf<Any?>()"
        return "mutableListOf(" + ", ".join(rendered) + ")"

    if kind == "Dict":
        keys_any = expr.get("keys")
        vals_any = expr.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        vals = vals_any if isinstance(vals_any, list) else []
        if len(keys) == 0 or len(vals) == 0:
            return "mutableMapOf<Any, Any?>()"
        parts: list[str] = []
        i = 0
        while i < len(keys) and i < len(vals):
            parts.append("Pair(__pytra_str(" + _render_expr(keys[i]) + "), " + _render_expr(vals[i]) + ")")
            i += 1
        return "mutableMapOf(" + ", ".join(parts) + ")"

    if kind == "ListComp":
        gens_any = expr.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "mutableListOf()"
        gen = gens[0]
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if len(ifs) != 0:
            return "mutableListOf()"
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
            return "mutableListOf()"
        if not isinstance(iter_any, dict) or iter_any.get("kind") != "RangeExpr":
            return "mutableListOf()"
        loop_var = _safe_ident(target_any.get("id"), "i")
        if loop_var == "_":
            loop_var = "__lc_i"
        start = _render_expr(iter_any.get("start"))
        stop = _render_expr(iter_any.get("stop"))
        step = _render_expr(iter_any.get("step"))
        elt = _render_expr(expr.get("elt"))
        return (
            "run { "
            "val __out = mutableListOf<Any?>(); "
            "val __step = __pytra_int(" + step + "); "
            "var " + loop_var + " = __pytra_int(" + start + "); "
            "while ((__step >= 0L && "
            + loop_var
            + " < __pytra_int(" + stop + ")) || (__step < 0L && "
            + loop_var
            + " > __pytra_int(" + stop + "))) { "
            "__out.add(" + elt + "); "
            + loop_var
            + " += __step "
            "}; "
            "__out "
            "}"
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
            lower = _render_expr(lower_any) if isinstance(lower_any, dict) else "0L"
            upper = _render_expr(upper_any) if isinstance(upper_any, dict) else "__pytra_len(" + owner + ")"
            return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"

        index = _render_expr(index_any)
        base = "__pytra_get_index(" + owner + ", " + index + ")"
        resolved = expr.get("resolved_type")
        kotlin_t = _kotlin_type(resolved, allow_void=False)
        return _cast_from_any(base, kotlin_t)

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
        out.append(name + ": " + _kotlin_type(arg_types.get(name), allow_void=False))
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


def _infer_kotlin_type(expr: Any, type_map: dict[str, str] | None = None) -> str:
    if not isinstance(expr, dict):
        return "Any?"
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
            return "Long"
        if name == "float":
            return "Double"
        if name == "bool":
            return "Boolean"
        if name == "str":
            return "String"
        if name == "bytearray" or name == "bytes":
            return "MutableList<Any?>"
        if name == "len":
            return "Long"
        if name in {"min", "max"}:
            args_any = expr.get("args")
            args = args_any if isinstance(args_any, list) else []
            seen_any = False
            i = 0
            while i < len(args):
                arg_t = _infer_kotlin_type(args[i], type_map)
                if arg_t == "Double":
                    return "Double"
                if arg_t == "Any?":
                    seen_any = True
                i += 1
            if seen_any:
                return "Any?"
            return "Long"
        if name in _CLASS_NAMES:
            return name
        func_any = expr.get("func")
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner_any = func_any.get("value")
            owner_name = ""
            if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
                owner_name = _safe_ident(owner_any.get("id"), "")
            attr_name = _safe_ident(func_any.get("attr"), "")
            if owner_name == "math":
                if attr_name in {"sqrt", "sin", "cos", "tan", "exp", "log", "pow", "floor", "ceil", "abs"}:
                    return "Double"
            if attr_name in {"isdigit", "isalpha"}:
                return "Boolean"
    if kind == "BinOp":
        op = expr.get("op")
        if op == "Div":
            return "Double"
        left_t = _infer_kotlin_type(expr.get("left"), type_map)
        right_t = _infer_kotlin_type(expr.get("right"), type_map)
        if left_t == "Double" or right_t == "Double":
            return "Double"
        if left_t == "Long" and right_t == "Long":
            return "Long"
        if op == "Mult":
            left_any = expr.get("left")
            right_any = expr.get("right")
            if isinstance(left_any, dict) and left_any.get("kind") == "List":
                return "MutableList<Any?>"
            if isinstance(right_any, dict) and right_any.get("kind") == "List":
                return "MutableList<Any?>"
    if kind == "IfExp":
        body_t = _infer_kotlin_type(expr.get("body"), type_map)
        else_t = _infer_kotlin_type(expr.get("orelse"), type_map)
        if body_t == else_t:
            return body_t
        if body_t == "Double" or else_t == "Double":
            return "Double"
        if body_t == "Long" and else_t == "Long":
            return "Long"
    resolved = expr.get("resolved_type")
    return _kotlin_type(resolved, allow_void=False)


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        raise RuntimeError("kotlin native emitter: unsupported ForCore iter_plan")
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("kotlin native emitter: unsupported ForCore target_plan")

    lines: list[str] = []
    if iter_plan_any.get("kind") == "StaticRangeForPlan" and target_plan_any.get("kind") == "NameTarget":
        target_name = _safe_ident(target_plan_any.get("id"), "i")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "loop")
        start = "__pytra_int(" + _render_expr(iter_plan_any.get("start")) + ")"
        stop = "__pytra_int(" + _render_expr(iter_plan_any.get("stop")) + ")"
        step = "__pytra_int(" + _render_expr(iter_plan_any.get("step")) + ")"
        step_tmp = _fresh_tmp(ctx, "step")
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        lines.append(indent + "val " + step_tmp + " = " + step)
        if target_name in declared:
            lines.append(indent + target_name + " = " + start)
        else:
            lines.append(indent + "var " + target_name + " = " + start)
            declared.add(target_name)
            type_map[target_name] = "Long"
        lines.append(
            indent
            + "while (("
            + step_tmp
            + " >= 0L && "
            + target_name
            + " < "
            + stop
            + ") || ("
            + step_tmp
            + " < 0L && "
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
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": target_name + " += " + step_tmp,
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = "Long"
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
        target_type_any = target_plan_any.get("target_type")
        target_type_txt = target_type_any if isinstance(target_type_any, str) else ""
        if target_type_txt in {"", "unknown"}:
            iter_expr_any = iter_plan_any.get("iter_expr")
            if isinstance(iter_expr_any, dict):
                iter_elem_t_any = iter_expr_any.get("iter_element_type")
                if isinstance(iter_elem_t_any, str) and iter_elem_t_any not in {"", "unknown"}:
                    target_type_txt = iter_elem_t_any
        target_kotlin_type = _kotlin_type(target_type_txt, allow_void=False)
        lines.append(indent + "val " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
        lines.append(indent + "var " + idx_tmp + ": Long = 0L")
        lines.append(indent + "while (" + idx_tmp + " < " + iter_tmp + ".size.toLong()) {")
        if target_kotlin_type == "Any?":
            lines.append(indent + "    val " + target_name + " = " + iter_tmp + "[" + idx_tmp + ".toInt()]")
        else:
            lines.append(
                indent
                + "    val "
                + target_name
                + ": "
                + target_kotlin_type
                + " = "
                + _cast_from_any(iter_tmp + "[" + idx_tmp + ".toInt()]", target_kotlin_type)
            )
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": idx_tmp + " += 1L",
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = target_kotlin_type
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        lines.append(indent + "    " + idx_tmp + " += 1L")
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if iter_plan_any.get("kind") == "RuntimeIterForPlan" and target_plan_any.get("kind") == "TupleTarget":
        iter_expr = _render_expr(iter_plan_any.get("iter_expr"))
        iter_tmp = _fresh_tmp(ctx, "iter")
        idx_tmp = _fresh_tmp(ctx, "i")
        item_tmp = _fresh_tmp(ctx, "it")
        tuple_tmp = _fresh_tmp(ctx, "tuple")
        lines.append(indent + "val " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
        lines.append(indent + "var " + idx_tmp + ": Long = 0L")
        lines.append(indent + "while (" + idx_tmp + " < " + iter_tmp + ".size.toLong()) {")
        lines.append(indent + "    val " + item_tmp + " = " + iter_tmp + "[" + idx_tmp + ".toInt()]")
        lines.append(indent + "    val " + tuple_tmp + " = __pytra_as_list(" + item_tmp + ")")

        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": idx_tmp + " += 1L",
        }
        declared = _declared_set(body_ctx)
        type_map = _type_map(body_ctx)

        elem_types: list[str] = []
        parent_t = target_plan_any.get("target_type")
        if isinstance(parent_t, str):
            elem_types = _tuple_element_types(parent_t)
        elem_any = target_plan_any.get("elements")
        elems = elem_any if isinstance(elem_any, list) else []

        i = 0
        while i < len(elems):
            elem = elems[i]
            if not isinstance(elem, dict) or elem.get("kind") != "NameTarget":
                raise RuntimeError("kotlin native emitter: unsupported RuntimeIter tuple target element")
            name = _safe_ident(elem.get("id"), "item_" + str(i))
            if name == "_":
                i += 1
                continue
            rhs = tuple_tmp + "[" + str(i) + "]"
            target_t_any = elem.get("target_type")
            target_t = target_t_any if isinstance(target_t_any, str) else ""
            if target_t in {"", "unknown"} and i < len(elem_types):
                target_t = elem_types[i]
            kotlin_t = _kotlin_type(target_t, allow_void=False)
            casted = _cast_from_any(rhs, kotlin_t)
            if name not in declared:
                lines.append(indent + "    var " + name + ": " + kotlin_t + " = " + casted)
                declared.add(name)
            else:
                lines.append(indent + "    " + name + " = " + casted)
            type_map[name] = kotlin_t
            i += 1

        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        lines.append(indent + "    " + idx_tmp + " += 1L")
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    raise RuntimeError("kotlin native emitter: unsupported ForCore plan")


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
    lines: list[str] = [indent + "val " + tuple_tmp + " = __pytra_as_list(" + _render_expr(value_any) + ")"]
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
        elem_type = "Any?"
        if i < len(tuple_types):
            elem_type = _kotlin_type(tuple_types[i], allow_void=False)
        casted = _cast_from_any(rhs, elem_type)

        if kind == "Name":
            name = _safe_ident(elem.get("id"), "tmp_" + str(i))
            if name not in declared:
                lines.append(indent + "var " + name + ": " + elem_type + " = " + casted)
                declared.add(name)
                type_map[name] = elem_type
            else:
                lines.append(indent + name + " = " + casted)
        elif kind == "Subscript":
            owner = _render_expr(elem.get("value"))
            index = _render_expr(elem.get("slice"))
            lines.append(indent + "__pytra_set_index(" + owner + ", " + index + ", " + casted + ")")
        else:
            return None
        i += 1

    return lines


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        raise RuntimeError("kotlin native emitter: unsupported statement")
    kind = stmt.get("kind")

    if kind == "Return":
        if "value" in stmt and stmt.get("value") is not None:
            value = _render_expr(stmt.get("value"))
            return_type_any = ctx.get("return_type")
            return_type = return_type_any if isinstance(return_type_any, str) else ""
            if return_type not in {"", "Any?"}:
                value = _cast_from_any(value, return_type)
            return [indent + "return " + value]
        return [indent + "return"]

    if kind == "Expr":
        value_any = stmt.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name":
            raw_ident = value_any.get("id")
            if raw_ident == "break":
                return [indent + "break"]
            if raw_ident == "continue":
                prefix_any = ctx.get("continue_prefix")
                prefix = prefix_any if isinstance(prefix_any, str) else ""
                if prefix != "":
                    return [indent + prefix, indent + "continue"]
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
                        return [indent + owner + " = __pytra_as_list(" + owner + "); " + owner + ".add(" + _render_expr(args[0]) + ")"]
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
        kotlin_type = _kotlin_type(stmt.get("decl_type") or stmt.get("annotation"), allow_void=False)
        if kotlin_type == "Any?":
            inferred = _infer_kotlin_type(stmt.get("value"), _type_map(ctx))
            if inferred != "Any?":
                kotlin_type = inferred

        stmt_value = stmt.get("value")
        if stmt_value is None:
            value = _default_return_expr(kotlin_type)
        else:
            value = _render_expr(stmt_value)
            if kotlin_type != "Any?":
                value = _cast_from_any(value, kotlin_type)
        if stmt.get("declare") is False or target in declared:
            if target not in declared:
                declared.add(target)
                type_map[target] = kotlin_type
                return [indent + "var " + target + ": " + kotlin_type + " = " + value]
            if target in type_map and type_map[target] != "Any?":
                if stmt_value is None:
                    return [indent + target + " = " + _default_return_expr(type_map[target])]
                return [indent + target + " = " + _cast_from_any(_render_expr(stmt_value), type_map[target])]
            return [indent + target + " = " + value]

        declared.add(target)
        type_map[target] = kotlin_type
        return [indent + "var " + target + ": " + kotlin_type + " = " + value]

    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            raise RuntimeError("kotlin native emitter: Assign without target")

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
            return [indent + "__pytra_set_index(" + owner + ", " + index + ", " + value + ")"]

        lhs = _target_name(targets[0])
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        value = _render_expr(stmt.get("value"))

        if stmt.get("declare"):
            if lhs in declared:
                if lhs in type_map and type_map[lhs] != "Any?":
                    return [indent + lhs + " = " + _cast_from_any(value, type_map[lhs])]
                return [indent + lhs + " = " + value]
            kotlin_type = _kotlin_type(stmt.get("decl_type"), allow_void=False)
            if kotlin_type == "Any?":
                inferred = _infer_kotlin_type(stmt.get("value"), _type_map(ctx))
                if inferred != "Any?":
                    kotlin_type = inferred
            if kotlin_type != "Any?":
                value = _cast_from_any(value, kotlin_type)
            declared.add(lhs)
            type_map[lhs] = kotlin_type
            return [indent + "var " + lhs + ": " + kotlin_type + " = " + value]

        if lhs not in declared:
            inferred = _infer_kotlin_type(stmt.get("value"), _type_map(ctx))
            declared.add(lhs)
            type_map[lhs] = inferred
            if inferred != "Any?":
                value = _cast_from_any(value, inferred)
            return [indent + "var " + lhs + ": " + inferred + " = " + value]
        if lhs in type_map and type_map[lhs] != "Any?":
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
        lines: list[str] = [indent + "if (" + test_expr + ") {"]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": ctx.get("continue_prefix", ""),
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
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": ctx.get("continue_prefix", ""),
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
        lines = [indent + "while (" + test_expr + ") {"]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": "",
        }
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if kind == "Pass":
        return [indent + "run { }"]

    if kind == "Break":
        return [indent + "break"]

    if kind == "Continue":
        prefix_any = ctx.get("continue_prefix")
        prefix = prefix_any if isinstance(prefix_any, str) else ""
        if prefix != "":
            return [indent + prefix, indent + "continue"]
        return [indent + "continue"]

    if kind == "Import" or kind == "ImportFrom":
        return []

    if kind == "Raise":
        exc_any = stmt.get("exc")
        if exc_any is None:
            return [indent + "throw RuntimeException(\"pytra raise\")"]
        return [indent + "throw RuntimeException(__pytra_str(" + _render_expr(exc_any) + "))"]

    raise RuntimeError("kotlin native emitter: unsupported stmt kind: " + str(kind))


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
    name = _safe_ident(fn.get("name"), "func")
    is_init = in_class and name == "__init__"

    return_type = _kotlin_type(fn.get("return_type"), allow_void=True)
    if is_init:
        return_type = "Unit"

    params = _function_params(fn, drop_self=in_class)

    lines: list[str] = []
    if is_init:
        if len(params) == 0:
            lines.append(indent + "init {")
        else:
            lines.append(indent + "constructor(" + ", ".join(params) + ") : this() {")
    else:
        sig = indent + "fun " + name + "(" + ", ".join(params) + ")"
        if return_type != "Unit":
            sig += ": " + return_type
        lines.append(sig + " {")

    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []

    ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}, "return_type": return_type}
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)

    param_names = _function_param_names(fn, drop_self=in_class)
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    i = 0
    while i < len(param_names):
        p = param_names[i]
        declared.add(p)
        type_map[p] = _kotlin_type(arg_types.get(p), allow_void=False)
        i += 1

    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1

    if len(body) == 0:
        lines.append(indent + "    // empty body")

    if not is_init and return_type != "Unit" and not _block_guarantees_return(body):
        lines.append(indent + "    return " + _default_return_expr(return_type))

    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
    extends = " : " + base_name + "()" if base_name != "" else ""

    lines: list[str] = []
    lines.append(indent + "open class " + class_name + "()" + extends + " {")

    field_types_any = cls.get("field_types")
    field_types = field_types_any if isinstance(field_types_any, dict) else {}
    instance_fields: list[tuple[str, str]] = []
    for raw_name, raw_type in field_types.items():
        if not isinstance(raw_name, str):
            continue
        field_name = _safe_ident(raw_name, "field")
        field_type = _kotlin_type(raw_type, allow_void=False)
        default = _default_return_expr(field_type)
        if default == "":
            default = "0L"
        lines.append(indent + "    var " + field_name + ": " + field_type + " = " + default)
        instance_fields.append((field_name, field_type))

    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []
    has_init = False
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            if _safe_ident(node.get("name"), "") == "__init__":
                has_init = True
                break
        i += 1

    if not has_init and len(instance_fields) > 0:
        ctor_params: list[str] = []
        i = 0
        while i < len(instance_fields):
            fname, ftype = instance_fields[i]
            ctor_params.append(fname + ": " + ftype)
            i += 1
        lines.append("")
        lines.append(indent + "    constructor(" + ", ".join(ctor_params) + ") : this() {")
        i = 0
        while i < len(instance_fields):
            fname, _ = instance_fields[i]
            lines.append(indent + "        this." + fname + " = " + fname)
            i += 1
        lines.append(indent + "    }")

    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            lines.append("")
            lines.extend(_emit_function(node, indent=indent + "    ", in_class=True))
        i += 1

    lines.append(indent + "}")
    return lines


def _emit_runtime_helpers() -> list[str]:
    return [
        "fun __pytra_noop(vararg args: Any?) { }",
        "",
        "fun __pytra_any_default(): Any? {",
        "    return 0L",
        "}",
        "",
        "fun __pytra_assert(vararg args: Any?): String {",
        "    return \"True\"",
        "}",
        "",
        "fun __pytra_perf_counter(): Double {",
        "    return System.nanoTime().toDouble() / 1_000_000_000.0",
        "}",
        "",
        "fun __pytra_truthy(v: Any?): Boolean {",
        "    if (v == null) return false",
        "    if (v is Boolean) return v",
        "    if (v is Long) return v != 0L",
        "    if (v is Int) return v != 0",
        "    if (v is Double) return v != 0.0",
        "    if (v is String) return v.isNotEmpty()",
        "    if (v is List<*>) return v.isNotEmpty()",
        "    if (v is Map<*, *>) return v.isNotEmpty()",
        "    return true",
        "}",
        "",
        "fun __pytra_int(v: Any?): Long {",
        "    if (v == null) return 0L",
        "    if (v is Long) return v",
        "    if (v is Int) return v.toLong()",
        "    if (v is Double) return v.toLong()",
        "    if (v is Boolean) return if (v) 1L else 0L",
        "    if (v is String) return v.toLongOrNull() ?: 0L",
        "    return 0L",
        "}",
        "",
        "fun __pytra_float(v: Any?): Double {",
        "    if (v == null) return 0.0",
        "    if (v is Double) return v",
        "    if (v is Float) return v.toDouble()",
        "    if (v is Long) return v.toDouble()",
        "    if (v is Int) return v.toDouble()",
        "    if (v is Boolean) return if (v) 1.0 else 0.0",
        "    if (v is String) return v.toDoubleOrNull() ?: 0.0",
        "    return 0.0",
        "}",
        "",
        "fun __pytra_str(v: Any?): String {",
        "    if (v == null) return \"\"",
        "    return v.toString()",
        "}",
        "",
        "fun __pytra_len(v: Any?): Long {",
        "    if (v == null) return 0L",
        "    if (v is String) return v.length.toLong()",
        "    if (v is List<*>) return v.size.toLong()",
        "    if (v is Map<*, *>) return v.size.toLong()",
        "    return 0L",
        "}",
        "",
        "fun __pytra_index(i: Long, n: Long): Long {",
        "    if (i < 0L) return i + n",
        "    return i",
        "}",
        "",
        "fun __pytra_get_index(container: Any?, index: Any?): Any? {",
        "    if (container is List<*>) {",
        "        if (container.isEmpty()) return __pytra_any_default()",
        "        val i = __pytra_index(__pytra_int(index), container.size.toLong())",
        "        if (i < 0L || i >= container.size.toLong()) return __pytra_any_default()",
        "        return container[i.toInt()]",
        "    }",
        "    if (container is Map<*, *>) {",
        "        return container[__pytra_str(index)] ?: __pytra_any_default()",
        "    }",
        "    if (container is String) {",
        "        if (container.isEmpty()) return \"\"",
        "        val chars = container.toCharArray()",
        "        val i = __pytra_index(__pytra_int(index), chars.size.toLong())",
        "        if (i < 0L || i >= chars.size.toLong()) return \"\"",
        "        return chars[i.toInt()].toString()",
        "    }",
        "    return __pytra_any_default()",
        "}",
        "",
        "fun __pytra_set_index(container: Any?, index: Any?, value: Any?) {",
        "    if (container is MutableList<*>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        val list = container as MutableList<Any?>",
        "        if (list.isEmpty()) return",
        "        val i = __pytra_index(__pytra_int(index), list.size.toLong())",
        "        if (i < 0L || i >= list.size.toLong()) return",
        "        list[i.toInt()] = value",
        "        return",
        "    }",
        "    if (container is MutableMap<*, *>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        val map = container as MutableMap<Any, Any?>",
        "        map[__pytra_str(index)] = value",
        "    }",
        "}",
        "",
        "fun __pytra_slice(container: Any?, lower: Any?, upper: Any?): Any? {",
        "    if (container is String) {",
        "        val n = container.length.toLong()",
        "        var lo = __pytra_index(__pytra_int(lower), n)",
        "        var hi = __pytra_index(__pytra_int(upper), n)",
        "        if (lo < 0L) lo = 0L",
        "        if (hi < 0L) hi = 0L",
        "        if (lo > n) lo = n",
        "        if (hi > n) hi = n",
        "        if (hi < lo) hi = lo",
        "        return container.substring(lo.toInt(), hi.toInt())",
        "    }",
        "    if (container is List<*>) {",
        "        val n = container.size.toLong()",
        "        var lo = __pytra_index(__pytra_int(lower), n)",
        "        var hi = __pytra_index(__pytra_int(upper), n)",
        "        if (lo < 0L) lo = 0L",
        "        if (hi < 0L) hi = 0L",
        "        if (lo > n) lo = n",
        "        if (hi > n) hi = n",
        "        if (hi < lo) hi = lo",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        return container.subList(lo.toInt(), hi.toInt()).toMutableList() as MutableList<Any?>",
        "    }",
        "    return __pytra_any_default()",
        "}",
        "",
        "fun __pytra_isdigit(v: Any?): Boolean {",
        "    val s = __pytra_str(v)",
        "    if (s.isEmpty()) return false",
        "    return s.all { it.isDigit() }",
        "}",
        "",
        "fun __pytra_isalpha(v: Any?): Boolean {",
        "    val s = __pytra_str(v)",
        "    if (s.isEmpty()) return false",
        "    return s.all { it.isLetter() }",
        "}",
        "",
        "fun __pytra_contains(container: Any?, value: Any?): Boolean {",
        "    if (container is List<*>) {",
        "        val needle = __pytra_str(value)",
        "        for (item in container) {",
        "            if (__pytra_str(item) == needle) return true",
        "        }",
        "        return false",
        "    }",
        "    if (container is Map<*, *>) {",
        "        return container.containsKey(__pytra_str(value))",
        "    }",
        "    if (container is String) {",
        "        return container.contains(__pytra_str(value))",
        "    }",
        "    return false",
        "}",
        "",
        "fun __pytra_ifexp(cond: Boolean, a: Any?, b: Any?): Any? {",
        "    return if (cond) a else b",
        "}",
        "",
        "fun __pytra_bytearray(initValue: Any?): MutableList<Any?> {",
        "    if (initValue is Long) {",
        "        val out = mutableListOf<Any?>()",
        "        var i = 0L",
        "        while (i < initValue) {",
        "            out.add(0L)",
        "            i += 1L",
        "        }",
        "        return out",
        "    }",
        "    if (initValue is Int) {",
        "        val out = mutableListOf<Any?>()",
        "        var i = 0",
        "        while (i < initValue) {",
        "            out.add(0L)",
        "            i += 1",
        "        }",
        "        return out",
        "    }",
        "    if (initValue is MutableList<*>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        return (initValue as MutableList<Any?>).toMutableList()",
        "    }",
        "    if (initValue is List<*>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        return (initValue as List<Any?>).toMutableList()",
        "    }",
        "    return mutableListOf()",
        "}",
        "",
        "fun __pytra_bytes(v: Any?): MutableList<Any?> {",
        "    if (v is MutableList<*>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        return (v as MutableList<Any?>).toMutableList()",
        "    }",
        "    if (v is List<*>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        return (v as List<Any?>).toMutableList()",
        "    }",
        "    return mutableListOf()",
        "}",
        "",
        "fun __pytra_list_repeat(value: Any?, count: Any?): MutableList<Any?> {",
        "    val out = mutableListOf<Any?>()",
        "    val n = __pytra_int(count)",
        "    var i = 0L",
        "    while (i < n) {",
        "        out.add(value)",
        "        i += 1L",
        "    }",
        "    return out",
        "}",
        "",
        "fun __pytra_enumerate(v: Any?): MutableList<Any?> {",
        "    val items = __pytra_as_list(v)",
        "    val out = mutableListOf<Any?>()",
        "    var i = 0L",
        "    while (i < items.size.toLong()) {",
        "        out.add(mutableListOf(i, items[i.toInt()]))",
        "        i += 1L",
        "    }",
        "    return out",
        "}",
        "",
        "fun __pytra_as_list(v: Any?): MutableList<Any?> {",
        "    if (v is MutableList<*>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        return v as MutableList<Any?>",
        "    }",
        "    if (v is List<*>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        return (v as List<Any?>).toMutableList()",
        "    }",
        "    return mutableListOf()",
        "}",
        "",
        "fun __pytra_as_dict(v: Any?): MutableMap<Any, Any?> {",
        "    if (v is MutableMap<*, *>) {",
        "        @Suppress(\"UNCHECKED_CAST\")",
        "        return v as MutableMap<Any, Any?>",
        "    }",
        "    if (v is Map<*, *>) {",
        "        val out = mutableMapOf<Any, Any?>()",
        "        for ((k, valAny) in v) {",
        "            if (k != null) out[k] = valAny",
        "        }",
        "        return out",
        "    }",
        "    return mutableMapOf()",
        "}",
        "",
        "fun __pytra_pop_last(v: MutableList<Any?>): MutableList<Any?> {",
        "    if (v.isEmpty()) return v",
        "    v.removeAt(v.size - 1)",
        "    return v",
        "}",
        "",
        "fun __pytra_print(vararg args: Any?) {",
        "    if (args.isEmpty()) {",
        "        println()",
        "        return",
        "    }",
        "    println(args.joinToString(\" \") { __pytra_str(it) })",
        "}",
        "",
        "fun __pytra_min(a: Any?, b: Any?): Any? {",
        "    val af = __pytra_float(a)",
        "    val bf = __pytra_float(b)",
        "    if (af < bf) {",
        "        if (__pytra_is_float(a) || __pytra_is_float(b)) return af",
        "        return __pytra_int(a)",
        "    }",
        "    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf",
        "    return __pytra_int(b)",
        "}",
        "",
        "fun __pytra_max(a: Any?, b: Any?): Any? {",
        "    val af = __pytra_float(a)",
        "    val bf = __pytra_float(b)",
        "    if (af > bf) {",
        "        if (__pytra_is_float(a) || __pytra_is_float(b)) return af",
        "        return __pytra_int(a)",
        "    }",
        "    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf",
        "    return __pytra_int(b)",
        "}",
        "",
        "fun __pytra_is_int(v: Any?): Boolean {",
        "    return (v is Long) || (v is Int)",
        "}",
        "",
        "fun __pytra_is_float(v: Any?): Boolean {",
        "    return v is Double",
        "}",
        "",
        "fun __pytra_is_bool(v: Any?): Boolean {",
        "    return v is Boolean",
        "}",
        "",
        "fun __pytra_is_str(v: Any?): Boolean {",
        "    return v is String",
        "}",
        "",
        "fun __pytra_is_list(v: Any?): Boolean {",
        "    return v is List<*>",
        "}",
    ]


def transpile_to_kotlin_native(east_doc: dict[str, Any]) -> str:
    """Emit Kotlin native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("kotlin native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("kotlin native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("kotlin native emitter: Module.body must be list")
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
    global _FUNCTION_NAMES
    _FUNCTION_NAMES = set()
    i = 0
    while i < len(classes):
        _CLASS_NAMES.add(_safe_ident(classes[i].get("name"), "PytraClass"))
        i += 1
    i = 0
    while i < len(functions):
        _FUNCTION_NAMES.add(_safe_ident(functions[i].get("name"), "func"))
        i += 1

    lines: list[str] = []
    lines.append("import kotlin.math.*")
    lines.append("")
    module_comments = _module_leading_comment_lines(east_doc, "// ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    i = 0
    while i < len(classes):
        cname = _safe_ident(classes[i].get("name"), "PytraClass")
        lines.append("")
        lines.append("fun __pytra_is_" + cname + "(v: Any?): Boolean {")
        lines.append("    return v is " + cname)
        lines.append("}")
        lines.append("")
        lines.append("fun __pytra_as_" + cname + "(v: Any?): " + cname + " {")
        lines.append("    return if (v is " + cname + ") v else " + cname + "()")
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
        lines.extend(_emit_function(functions[i], indent="", in_class=False))
        i += 1

    lines.append("")
    lines.append("fun main(args: Array<String>) {")
    ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}}
    if len(main_guard) > 0:
        has_pytra_main = False
        i = 0
        while i < len(functions):
            if _safe_ident(functions[i].get("name"), "") == "__pytra_main":
                has_pytra_main = True
                break
            i += 1
        i = 0
        while i < len(main_guard):
            st = main_guard[i]
            if has_pytra_main and isinstance(st, dict) and st.get("kind") == "Expr":
                value_any = st.get("value")
                if isinstance(value_any, dict) and value_any.get("kind") == "Call":
                    fn_any = value_any.get("func")
                    if isinstance(fn_any, dict) and fn_any.get("kind") == "Name":
                        if _safe_ident(fn_any.get("id"), "") == "main":
                            args_any = value_any.get("args")
                            args_main = args_any if isinstance(args_any, list) else []
                            rendered_args: list[str] = []
                            j = 0
                            while j < len(args_main):
                                rendered_args.append(_render_expr(args_main[j]))
                                j += 1
                            lines.append("    __pytra_main(" + ", ".join(rendered_args) + ")")
                            i += 1
                            continue
            lines.extend(_emit_stmt(st, indent="    ", ctx=ctx))
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
            lines.append("    _case_main()")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)
