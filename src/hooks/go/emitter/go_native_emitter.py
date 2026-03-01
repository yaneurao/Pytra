"""EAST3 -> Go native emitter."""

from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.east_parts.code_emitter import CodeEmitter


_GO_KEYWORDS = {
    "break",
    "case",
    "chan",
    "const",
    "continue",
    "default",
    "defer",
    "else",
    "fallthrough",
    "for",
    "func",
    "go",
    "goto",
    "if",
    "import",
    "interface",
    "map",
    "package",
    "range",
    "return",
    "select",
    "struct",
    "switch",
    "type",
    "var",
}

_CLASS_NAMES: set[str] = set()
_CLASS_BASE_MAP: dict[str, str] = {}
_CURRENT_RECEIVER_CLASS: str = ""
_CURRENT_RECEIVER_VAR: str = "self"


def _class_iface_name(class_name: str) -> str:
    return _safe_ident(class_name, "PytraClass") + "Like"


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
    if out in _GO_KEYWORDS:
        out = out + "_"
    return out


def _collect_go_deps(collector: CodeEmitter, node_any: Any) -> None:
    if isinstance(node_any, dict):
        kind = node_any.get("kind")
        if kind == "Attribute":
            owner_any = node_any.get("value")
            if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
                owner = _safe_ident(owner_any.get("id"), "")
                if owner == "math":
                    collector.require_dep("math")
        for child_any in node_any.values():
            _collect_go_deps(collector, child_any)
        return
    if isinstance(node_any, list):
        for item_any in node_any:
            _collect_go_deps(collector, item_any)


def _go_string_literal(text: str) -> str:
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


def _go_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "any"
    if type_name == "None":
        return "" if allow_void else "any"
    if type_name in {"int", "int64", "uint8"}:
        return "int64"
    if type_name in {"float", "float64"}:
        return "float64"
    if type_name == "bool":
        return "bool"
    if type_name == "str":
        return "string"
    if type_name.startswith("list["):
        return "[]any"
    if type_name.startswith("tuple["):
        return "[]any"
    if type_name.startswith("dict["):
        return "map[any]any"
    if type_name in {"bytes", "bytearray"}:
        return "[]any"
    if type_name in {"unknown", "object", "any"}:
        return "any"
    if type_name in _CLASS_NAMES:
        return _class_iface_name(type_name)
    if type_name.isidentifier():
        return "*" + _safe_ident(type_name, "Any")
    return "any"


def _default_return_expr(go_type: str) -> str:
    if go_type == "int64":
        return "0"
    if go_type == "float64":
        return "0.0"
    if go_type == "bool":
        return "false"
    if go_type == "string":
        return '""'
    return "nil"


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


def _cast_from_any(expr: str, go_type: str) -> str:
    if go_type == "int64":
        return "__pytra_int(" + expr + ")"
    if go_type == "float64":
        return "__pytra_float(" + expr + ")"
    if go_type == "bool":
        return "__pytra_truthy(" + expr + ")"
    if go_type == "string":
        return "__pytra_str(" + expr + ")"
    if go_type == "[]any":
        return "__pytra_as_list(" + expr + ")"
    if go_type == "map[any]any":
        return "__pytra_as_dict(" + expr + ")"
    if go_type == "any":
        return expr
    if go_type.startswith("*"):
        cls = _safe_ident(go_type[1:], "Any")
        return "__pytra_as_" + cls + "(" + expr + ")"
    return expr


def _render_name_expr(expr: dict[str, Any]) -> str:
    return _safe_ident(expr.get("id"), "value")


def _render_constant_expr(expr: dict[str, Any]) -> str:
    if "value" not in expr:
        return "nil"
    value = expr.get("value")
    if value is None:
        resolved = expr.get("resolved_type")
        if resolved in {"int", "int64", "uint8"}:
            return "int64(0)"
        if resolved in {"float", "float64"}:
            return "float64(0)"
        if resolved == "bool":
            return "false"
        if resolved == "str":
            return '""'
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "int64(" + str(value) + ")"
    if isinstance(value, float):
        return "float64(" + str(value) + ")"
    if isinstance(value, str):
        return _go_string_literal(value)
    return "nil"


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
            parts.append("(" + cur_left + " " + symbol + " " + right + ")")

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
        return "Sqrt"
    if attr == "sin":
        return "Sin"
    if attr == "cos":
        return "Cos"
    if attr == "tan":
        return "Tan"
    if attr == "exp":
        return "Exp"
    if attr == "log":
        return "Log"
    if attr == "pow":
        return "Pow"
    if attr == "floor":
        return "Floor"
    if attr == "ceil":
        return "Ceil"
    if attr == "abs":
        return "Abs"
    return _safe_ident(attr, "call")


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    value_any = expr.get("value")
    attr = _safe_ident(expr.get("attr"), "field")
    if isinstance(value_any, dict) and value_any.get("kind") == "Name":
        owner = _safe_ident(value_any.get("id"), "")
        if owner == "math" and attr == "pi":
            return "math.Pi"
        if owner == "math" and attr == "e":
            return "math.E"
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
            return "[]any{}"
        return "__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee_name == "bytes":
        if len(args) == 0:
            return "[]any{}"
        return "__pytra_bytes(" + _render_expr(args[0]) + ")"
    if callee_name == "int":
        if len(args) == 0:
            return "int64(0)"
        return "__pytra_int(" + _render_expr(args[0]) + ")"
    if callee_name == "float":
        if len(args) == 0:
            return "float64(0)"
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
            return "int64(0)"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "enumerate":
        if len(args) == 0:
            return "[]any{}"
        return "__pytra_enumerate(" + _render_expr(args[0]) + ")"
    if callee_name == "min":
        if len(args) == 0:
            return "int64(0)"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_min(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name == "max":
        if len(args) == 0:
            return "int64(0)"
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
        return "[]any{}"
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
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Call":
            if _call_name(owner_any) == "super":
                base_name = _CLASS_BASE_MAP.get(_CURRENT_RECEIVER_CLASS, "")
                recv = _CURRENT_RECEIVER_VAR if _CURRENT_RECEIVER_VAR != "" else "self"
                rendered_super_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_super_args.append(_render_expr(args[i]))
                    i += 1
                if attr_name == "__init__":
                    if base_name != "":
                        return recv + "." + base_name + ".Init(" + ", ".join(rendered_super_args) + ")"
                    return "__pytra_noop()"
                if base_name != "":
                    return recv + "." + base_name + "." + attr_name + "(" + ", ".join(rendered_super_args) + ")"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner = _safe_ident(owner_any.get("id"), "")
            if owner == "math":
                rendered_math_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_math_args.append("__pytra_float(" + _render_expr(args[i]) + ")")
                    i += 1
                return "math." + _math_call_name(attr_name) + "(" + ", ".join(rendered_math_args) + ")"
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
        return "New" + callee_name + "(" + ", ".join(rendered_ctor_args) + ")"

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
        return "nil"
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
        return "[]any{" + ", ".join(rendered) + "}"

    if kind == "Dict":
        keys_any = expr.get("keys")
        vals_any = expr.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        vals = vals_any if isinstance(vals_any, list) else []
        if len(keys) == 0 or len(vals) == 0:
            return "map[any]any{}"
        parts: list[str] = []
        i = 0
        while i < len(keys) and i < len(vals):
            parts.append(_render_expr(keys[i]) + ": " + _render_expr(vals[i]))
            i += 1
        return "map[any]any{" + ", ".join(parts) + "}"

    if kind == "ListComp":
        gens_any = expr.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "[]any{}"
        gen = gens[0]
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if len(ifs) != 0:
            return "[]any{}"
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
            return "[]any{}"
        if not isinstance(iter_any, dict) or iter_any.get("kind") != "RangeExpr":
            return "[]any{}"
        loop_var = _safe_ident(target_any.get("id"), "i")
        if loop_var == "_":
            loop_var = "__lc_i"
        start = _render_expr(iter_any.get("start"))
        stop = _render_expr(iter_any.get("stop"))
        step = _render_expr(iter_any.get("step"))
        elt = _render_expr(expr.get("elt"))
        return (
            "func() []any { "
            "__out := []any{}; "
            "__step := __pytra_int(" + step + "); "
            "for " + loop_var + " := __pytra_int(" + start + "); "
            "(__step >= 0 && " + loop_var + " < __pytra_int(" + stop + ")) || (__step < 0 && " + loop_var + " > __pytra_int(" + stop + ")); "
            + loop_var + " += __step { "
            "__out = append(__out, " + elt + ")"
            " }; "
            "return __out"
            " }()"
        )

    if kind == "IfExp":
        test_expr = _render_truthy_expr(expr.get("test"))
        body_expr = _render_expr(expr.get("body"))
        else_expr = _render_expr(expr.get("orelse"))
        return "__pytra_ifexp(" + test_expr + ", " + body_expr + ", " + else_expr + ")"

    if kind == "Subscript":
        value_any = expr.get("value")
        index_any = expr.get("slice")
        owner = _render_expr(value_any)
        if isinstance(index_any, dict) and index_any.get("kind") == "Slice":
            lower_any = index_any.get("lower")
            upper_any = index_any.get("upper")
            lower = _render_expr(lower_any) if isinstance(lower_any, dict) else "int64(0)"
            upper = _render_expr(upper_any) if isinstance(upper_any, dict) else "__pytra_len(" + owner + ")"
            return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"

        index = _render_expr(index_any)
        base = "__pytra_get_index(" + owner + ", " + index + ")"
        resolved = expr.get("resolved_type")
        go_t = _go_type(resolved, allow_void=False)
        return _cast_from_any(base, go_t)

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

    return "nil"


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
        out.append(name + " " + _go_type(arg_types.get(name), allow_void=False))
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


def _read_name_set(ctx: dict[str, Any]) -> set[str]:
    names = ctx.get("read_names")
    if isinstance(names, set):
        return names
    out: set[str] = set()
    ctx["read_names"] = out
    return out


def _collect_read_names_expr(expr: Any, out: set[str]) -> None:
    if not isinstance(expr, dict):
        return
    kind = expr.get("kind")
    if kind == "Name":
        out.add(_safe_ident(expr.get("id"), ""))
        return

    for val in expr.values():
        if isinstance(val, dict):
            _collect_read_names_expr(val, out)
            continue
        if isinstance(val, list):
            i = 0
            while i < len(val):
                _collect_read_names_expr(val[i], out)
                i += 1


def _collect_read_names_block(body: list[Any], out: set[str]) -> None:
    i = 0
    while i < len(body):
        _collect_read_names_stmt(body[i], out)
        i += 1


def _collect_read_names_stmt(stmt: Any, out: set[str]) -> None:
    if not isinstance(stmt, dict):
        return
    kind = stmt.get("kind")
    if kind == "Return":
        _collect_read_names_expr(stmt.get("value"), out)
        return
    if kind == "Expr":
        _collect_read_names_expr(stmt.get("value"), out)
        return
    if kind == "AnnAssign":
        _collect_read_names_expr(stmt.get("value"), out)
        target_any = stmt.get("target")
        if isinstance(target_any, dict):
            target_kind = target_any.get("kind")
            if target_kind == "Subscript":
                _collect_read_names_expr(target_any.get("value"), out)
                _collect_read_names_expr(target_any.get("slice"), out)
            elif target_kind == "Attribute":
                _collect_read_names_expr(target_any.get("value"), out)
        return
    if kind == "Assign":
        _collect_read_names_expr(stmt.get("value"), out)
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        i = 0
        while i < len(targets):
            tgt = targets[i]
            if isinstance(tgt, dict):
                tgt_kind = tgt.get("kind")
                if tgt_kind == "Subscript":
                    _collect_read_names_expr(tgt.get("value"), out)
                    _collect_read_names_expr(tgt.get("slice"), out)
                elif tgt_kind == "Attribute":
                    _collect_read_names_expr(tgt.get("value"), out)
            i += 1
        return
    if kind == "AugAssign":
        _collect_read_names_expr(stmt.get("target"), out)
        _collect_read_names_expr(stmt.get("value"), out)
        return
    if kind == "If":
        _collect_read_names_expr(stmt.get("test"), out)
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        _collect_read_names_block(body, out)
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        _collect_read_names_block(orelse, out)
        return
    if kind == "While":
        _collect_read_names_expr(stmt.get("test"), out)
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        _collect_read_names_block(body, out)
        return
    if kind == "ForCore":
        iter_plan_any = stmt.get("iter_plan")
        if isinstance(iter_plan_any, dict):
            _collect_read_names_expr(iter_plan_any.get("iter_expr"), out)
            _collect_read_names_expr(iter_plan_any.get("start"), out)
            _collect_read_names_expr(iter_plan_any.get("stop"), out)
            _collect_read_names_expr(iter_plan_any.get("step"), out)
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        _collect_read_names_block(body, out)
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        _collect_read_names_block(orelse, out)
        return
    if kind == "Raise":
        _collect_read_names_expr(stmt.get("exc"), out)


def _infer_go_type(expr: Any, type_map: dict[str, str] | None = None) -> str:
    if not isinstance(expr, dict):
        return "any"
    kind = expr.get("kind")
    if kind == "Name" and isinstance(type_map, dict):
        ident = _safe_ident(expr.get("id"), "")
        if ident in type_map:
            return type_map[ident]
    if kind == "Call":
        name = _call_name(expr)
        if name == "perf_counter":
            return "float64"
        if name == "int":
            return "int64"
        if name == "float":
            return "float64"
        if name == "bool":
            return "bool"
        if name == "str":
            return "string"
        if name == "bytearray" or name == "bytes":
            return "[]any"
        if name == "len":
            return "int64"
        if name in {"min", "max"}:
            args_any = expr.get("args")
            args = args_any if isinstance(args_any, list) else []
            seen_any = False
            i = 0
            while i < len(args):
                arg_t = _infer_go_type(args[i], type_map)
                if arg_t == "float64":
                    return "float64"
                if arg_t == "any":
                    seen_any = True
                i += 1
            if seen_any:
                return "any"
            return "int64"
        if name in _CLASS_NAMES:
            return "*" + name
        func_any = expr.get("func")
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner_any = func_any.get("value")
            owner_name = ""
            if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
                owner_name = _safe_ident(owner_any.get("id"), "")
            attr_name = _safe_ident(func_any.get("attr"), "")
            if owner_name == "math":
                if attr_name in {"sqrt", "sin", "cos", "tan", "exp", "log", "pow", "floor", "ceil", "abs"}:
                    return "float64"
            if attr_name in {"isdigit", "isalpha"}:
                return "bool"
    if kind == "BinOp":
        op = expr.get("op")
        if op == "Div":
            return "float64"
        left_t = _infer_go_type(expr.get("left"), type_map)
        right_t = _infer_go_type(expr.get("right"), type_map)
        if left_t == "float64" or right_t == "float64":
            return "float64"
        if left_t == "int64" and right_t == "int64":
            return "int64"
        if op == "Mult":
            left_any = expr.get("left")
            right_any = expr.get("right")
            if isinstance(left_any, dict) and left_any.get("kind") == "List":
                return "[]any"
            if isinstance(right_any, dict) and right_any.get("kind") == "List":
                return "[]any"
    if kind == "IfExp":
        body_t = _infer_go_type(expr.get("body"), type_map)
        else_t = _infer_go_type(expr.get("orelse"), type_map)
        if body_t == else_t:
            return body_t
        if body_t == "float64" or else_t == "float64":
            return "float64"
        if body_t == "int64" and else_t == "int64":
            return "int64"
    resolved = expr.get("resolved_type")
    return _go_type(resolved, allow_void=False)


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        raise RuntimeError("go native emitter: unsupported ForCore iter_plan")
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("go native emitter: unsupported ForCore target_plan")

    lines: list[str] = []
    if iter_plan_any.get("kind") == "StaticRangeForPlan" and target_plan_any.get("kind") == "NameTarget":
        target_name = _safe_ident(target_plan_any.get("id"), "i")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "loop")
        start = "__pytra_int(" + _render_expr(iter_plan_any.get("start")) + ")"
        stop = "__pytra_int(" + _render_expr(iter_plan_any.get("stop")) + ")"
        step = "__pytra_int(" + _render_expr(iter_plan_any.get("step")) + ")"
        step_tmp = _fresh_tmp(ctx, "step")
        lines.append(indent + step_tmp + " := " + step)
        lines.append(
            indent
            + "for "
            + target_name
            + " := "
            + start
            + "; ("
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
            + "); "
            + target_name
            + " += "
            + step_tmp
            + " {"
        )
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "read_names": set(_read_name_set(ctx)),
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = "int64"
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
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
        target_go_type = _go_type(target_type_txt, allow_void=False)
        used_names = _read_name_set(ctx)
        lines.append(indent + iter_tmp + " := __pytra_as_list(" + iter_expr + ")")
        lines.append(indent + "for " + idx_tmp + " := int64(0); " + idx_tmp + " < int64(len(" + iter_tmp + ")); " + idx_tmp + " += 1 {")
        if target_name in used_names:
            if target_go_type == "any":
                lines.append(indent + "    " + target_name + " := " + iter_tmp + "[" + idx_tmp + "]")
            else:
                lines.append(indent + "    var " + target_name + " " + target_go_type + " = " + _cast_from_any(iter_tmp + "[" + idx_tmp + "]", target_go_type))
        else:
            lines.append(indent + "    _ = " + iter_tmp + "[" + idx_tmp + "]")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "read_names": set(_read_name_set(ctx)),
        }
        if target_name in used_names:
            _declared_set(body_ctx).add(target_name)
            _type_map(body_ctx)[target_name] = target_go_type
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if iter_plan_any.get("kind") == "RuntimeIterForPlan" and target_plan_any.get("kind") == "TupleTarget":
        iter_expr = _render_expr(iter_plan_any.get("iter_expr"))
        iter_tmp = _fresh_tmp(ctx, "iter")
        idx_tmp = _fresh_tmp(ctx, "i")
        item_tmp = _fresh_tmp(ctx, "it")
        tuple_tmp = _fresh_tmp(ctx, "tuple")
        lines.append(indent + iter_tmp + " := __pytra_as_list(" + iter_expr + ")")
        lines.append(indent + "for " + idx_tmp + " := int64(0); " + idx_tmp + " < int64(len(" + iter_tmp + ")); " + idx_tmp + " += 1 {")
        lines.append(indent + "    " + item_tmp + " := " + iter_tmp + "[" + idx_tmp + "]")
        lines.append(indent + "    " + tuple_tmp + " := __pytra_as_list(" + item_tmp + ")")

        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "read_names": set(_read_name_set(ctx)),
        }
        declared = _declared_set(body_ctx)
        type_map = _type_map(body_ctx)
        used_names = _read_name_set(body_ctx)

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
                raise RuntimeError("go native emitter: unsupported RuntimeIter tuple target element")
            name = _safe_ident(elem.get("id"), "item_" + str(i))
            if name == "_":
                name = _fresh_tmp(body_ctx, "item")
            rhs = tuple_tmp + "[" + str(i) + "]"
            target_t_any = elem.get("target_type")
            target_t = target_t_any if isinstance(target_t_any, str) else ""
            if target_t in {"", "unknown"} and i < len(elem_types):
                target_t = elem_types[i]
            go_t = _go_type(target_t, allow_void=False)
            casted = _cast_from_any(rhs, go_t)
            if name not in used_names:
                lines.append(indent + "    _ = " + casted)
                i += 1
                continue
            if name not in declared:
                lines.append(indent + "    var " + name + " " + go_t + " = " + casted)
                declared.add(name)
                lines.append(indent + "    _ = " + name)
            else:
                lines.append(indent + "    " + name + " = " + casted)
            type_map[name] = go_t
            i += 1

        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    raise RuntimeError("go native emitter: unsupported ForCore plan")


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
    lines: list[str] = [indent + tuple_tmp + " := __pytra_as_list(" + _render_expr(value_any) + ")"]
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    used_names = _read_name_set(ctx)
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
        elem_type = "any"
        if i < len(tuple_types):
            elem_type = _go_type(tuple_types[i], allow_void=False)
        casted = _cast_from_any(rhs, elem_type)

        if kind == "Name":
            name = _safe_ident(elem.get("id"), "tmp_" + str(i))
            if name not in used_names:
                lines.append(indent + "_ = " + casted)
                i += 1
                continue
            if name not in declared:
                lines.append(indent + "var " + name + " " + elem_type + " = " + casted)
                declared.add(name)
                type_map[name] = elem_type
                lines.append(indent + "_ = " + name)
            else:
                lines.append(indent + name + " = " + casted)
        elif kind == "Subscript":
            value_node = elem.get("value")
            owner = _render_expr(value_node)
            index = _render_expr(elem.get("slice"))
            lines.append(indent + "__pytra_set_index(" + owner + ", " + index + ", " + casted + ")")
        else:
            return None
        i += 1

    return lines


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        raise RuntimeError("go native emitter: unsupported statement")
    kind = stmt.get("kind")

    if kind == "Return":
        if "value" in stmt and stmt.get("value") is not None:
            value = _render_expr(stmt.get("value"))
            return_type_any = ctx.get("return_type")
            return_type = return_type_any if isinstance(return_type_any, str) else ""
            if return_type not in {"", "any"}:
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
                        return [indent + owner + " = append(__pytra_as_list(" + owner + "), " + _render_expr(args[0]) + ")"]
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
        used_names = _read_name_set(ctx)
        target_is_name = isinstance(target_any, dict) and target_any.get("kind") == "Name"
        go_type = _go_type(stmt.get("decl_type") or stmt.get("annotation"), allow_void=False)
        if go_type == "any":
            inferred = _infer_go_type(stmt.get("value"), _type_map(ctx))
            if inferred != "any":
                go_type = inferred

        stmt_value = stmt.get("value")
        if stmt_value is None:
            value = _default_return_expr(go_type)
        else:
            value = _render_expr(stmt_value)
            if go_type != "any":
                value = _cast_from_any(value, go_type)
        if target_is_name and target not in used_names:
            if stmt_value is None:
                return []
            return [indent + "_ = " + value]
        if stmt.get("declare") is False or target in declared:
            if target not in declared:
                declared.add(target)
                type_map[target] = go_type
                return [indent + "var " + target + " " + go_type + " = " + value]
            if target in type_map and type_map[target] != "any":
                if stmt_value is None:
                    return [indent + target + " = " + _default_return_expr(type_map[target])]
                return [indent + target + " = " + _cast_from_any(_render_expr(stmt_value), type_map[target])]
            return [indent + target + " = " + value]

        declared.add(target)
        type_map[target] = go_type
        return [indent + "var " + target + " " + go_type + " = " + value]

    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            raise RuntimeError("go native emitter: Assign without target")

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
        used_names = _read_name_set(ctx)
        lhs_is_name = isinstance(targets[0], dict) and targets[0].get("kind") == "Name"
        value = _render_expr(stmt.get("value"))

        if lhs_is_name and lhs not in used_names:
            return [indent + "_ = " + value]

        if stmt.get("declare"):
            if lhs in declared:
                if lhs in type_map and type_map[lhs] != "any":
                    return [indent + lhs + " = " + _cast_from_any(value, type_map[lhs])]
                return [indent + lhs + " = " + value]
            go_type = _go_type(stmt.get("decl_type"), allow_void=False)
            if go_type == "any":
                inferred = _infer_go_type(stmt.get("value"), _type_map(ctx))
                if inferred != "any":
                    go_type = inferred
            if go_type != "any":
                value = _cast_from_any(value, go_type)
            declared.add(lhs)
            type_map[lhs] = go_type
            return [indent + "var " + lhs + " " + go_type + " = " + value]

        if lhs not in declared:
            inferred = _infer_go_type(stmt.get("value"), _type_map(ctx))
            declared.add(lhs)
            type_map[lhs] = inferred
            if inferred != "any":
                value = _cast_from_any(value, inferred)
            return [indent + "var " + lhs + " " + inferred + " = " + value]
        if lhs in type_map and type_map[lhs] != "any":
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
            "return_type": ctx.get("return_type", ""),
            "read_names": set(_read_name_set(ctx)),
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
            "read_names": set(_read_name_set(ctx)),
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
        lines: list[str] = [indent + "for " + test_expr + " {"]
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
        exc_any = stmt.get("exc")
        if isinstance(exc_any, dict):
            return [indent + "panic(__pytra_str(" + _render_expr(exc_any) + "))"]
        return [indent + "panic(\"pytra raise\")"]

    raise RuntimeError("go native emitter: unsupported stmt kind: " + str(kind))


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
    global _CURRENT_RECEIVER_CLASS, _CURRENT_RECEIVER_VAR
    name = _safe_ident(fn.get("name"), "func")
    is_init = receiver_name is not None and name == "__init__"
    if is_init:
        name = "Init"

    return_type = _go_type(fn.get("return_type"), allow_void=True)
    if is_init:
        return_type = ""

    receiver = ""
    drop_self = False
    recv_var = "self"
    if isinstance(receiver_name, str):
        arg_order_any = fn.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        if len(arg_order) > 0 and isinstance(arg_order[0], str):
            recv_var = _safe_ident(arg_order[0], "self")
        receiver = "(" + recv_var + " *" + receiver_name + ") "
        drop_self = True

    params = _function_params(fn, drop_self=drop_self)
    sig = indent + "func " + receiver + name + "(" + ", ".join(params) + ")"
    if return_type != "":
        sig += " " + return_type

    lines: list[str] = [sig + " {"]
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []

    read_names: set[str] = set()
    _collect_read_names_block(body, read_names)

    ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}, "return_type": return_type, "read_names": read_names}
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)

    param_names = _function_param_names(fn, drop_self=drop_self)
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    i = 0
    while i < len(param_names):
        p = param_names[i]
        declared.add(p)
        type_map[p] = _go_type(arg_types.get(p), allow_void=False)
        i += 1

    i = 0
    prev_receiver_class = _CURRENT_RECEIVER_CLASS
    prev_receiver_var = _CURRENT_RECEIVER_VAR
    if isinstance(receiver_name, str):
        _CURRENT_RECEIVER_CLASS = receiver_name
        _CURRENT_RECEIVER_VAR = recv_var
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1
    _CURRENT_RECEIVER_CLASS = prev_receiver_class
    _CURRENT_RECEIVER_VAR = prev_receiver_var

    if return_type != "" and not _block_guarantees_return(body):
        lines.append(indent + "    return " + _default_return_expr(return_type))

    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""

    lines: list[str] = []
    lines.append(indent + "type " + class_name + " struct {")
    if base_name != "":
        lines.append(indent + "    *" + base_name)

    field_types_any = cls.get("field_types")
    field_types = field_types_any if isinstance(field_types_any, dict) else {}
    instance_fields: list[tuple[str, str]] = []
    for raw_name, raw_type in field_types.items():
        if not isinstance(raw_name, str):
            continue
        field_name = _safe_ident(raw_name, "field")
        field_type = _go_type(raw_type, allow_void=False)
        if field_type == "":
            field_type = "any"
        lines.append(indent + "    " + field_name + " " + field_type)
        instance_fields.append((field_name, field_type))
    lines.append(indent + "}")

    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []

    init_fn: dict[str, Any] | None = None
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef" and _safe_ident(node.get("name"), "") == "__init__":
            init_fn = node
            break
        i += 1

    ctor_params: list[str] = []
    ctor_args: list[str] = []
    if isinstance(init_fn, dict):
        ctor_params = _function_params(init_fn, drop_self=True)
        arg_names = _function_param_names(init_fn, drop_self=True)
        j = 0
        while j < len(arg_names):
            ctor_args.append(arg_names[j])
            j += 1
    elif len(instance_fields) > 0:
        j = 0
        while j < len(instance_fields):
            fname, ftype = instance_fields[j]
            ctor_params.append(fname + " " + ftype)
            ctor_args.append(fname)
            j += 1

    lines.append("")
    lines.append(indent + "func New" + class_name + "(" + ", ".join(ctor_params) + ") *" + class_name + " {")
    lines.append(indent + "    self := &" + class_name + "{}")
    if base_name != "":
        lines.append(indent + "    self." + base_name + " = New" + base_name + "()")
    if isinstance(init_fn, dict):
        lines.append(indent + "    self.Init(" + ", ".join(ctor_args) + ")")
    elif len(instance_fields) > 0:
        j = 0
        while j < len(instance_fields):
            fname, _ = instance_fields[j]
            lines.append(indent + "    self." + fname + " = " + fname)
            j += 1
    lines.append(indent + "    return self")
    lines.append(indent + "}")

    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            lines.append("")
            lines.extend(_emit_function(node, indent=indent, receiver_name=class_name))
        i += 1

    return lines


def _collect_class_base_map(classes: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    while i < len(classes):
        cls = classes[i]
        class_name = _safe_ident(cls.get("name"), "PytraClass")
        base_any = cls.get("base")
        base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
        if class_name != "" and base_name != "":
            out[class_name] = base_name
        i += 1
    return out


def _method_signature_for_interface(fn: dict[str, Any]) -> str:
    method_name = _safe_ident(fn.get("name"), "method")
    params = _function_params(fn, drop_self=True)
    ret = _go_type(fn.get("return_type"), allow_void=True)
    sig = method_name + "(" + ", ".join(params) + ")"
    if ret != "":
        sig += " " + ret
    return sig


def _collect_class_method_sig_map(classes: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    i = 0
    while i < len(classes):
        cls = classes[i]
        class_name = _safe_ident(cls.get("name"), "PytraClass")
        body_any = cls.get("body")
        body = body_any if isinstance(body_any, list) else []
        sigs: dict[str, str] = {}
        j = 0
        while j < len(body):
            node = body[j]
            if isinstance(node, dict) and node.get("kind") == "FunctionDef":
                method_raw = _safe_ident(node.get("name"), "")
                if method_raw != "" and method_raw != "__init__":
                    sigs[method_raw] = _method_signature_for_interface(node)
            j += 1
        out[class_name] = sigs
        i += 1
    return out


def _resolve_interface_method_sigs(
    class_name: str,
    base_map: dict[str, str],
    method_sig_map: dict[str, dict[str, str]],
) -> list[str]:
    merged: dict[str, str] = {}
    chain: list[str] = []
    cur = class_name
    while cur != "":
        chain.append(cur)
        cur = base_map.get(cur, "")
    chain.reverse()
    i = 0
    while i < len(chain):
        sigs = method_sig_map.get(chain[i], {})
        for name, sig in sigs.items():
            merged[name] = sig
        i += 1
    out: list[str] = []
    for _, sig in merged.items():
        out.append(sig)
    return out


def transpile_to_go_native(east_doc: dict[str, Any]) -> str:
    """Emit Go native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("go native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("go native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("go native emitter: Module.body must be list")
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

    global _CLASS_NAMES, _CLASS_BASE_MAP
    _CLASS_NAMES = set()
    i = 0
    while i < len(classes):
        _CLASS_NAMES.add(_safe_ident(classes[i].get("name"), "PytraClass"))
        i += 1
    _CLASS_BASE_MAP = _collect_class_base_map(classes)
    class_method_sig_map = _collect_class_method_sig_map(classes)

    lines: list[str] = []
    lines.append("package main")
    lines.append("")
    dep_collector = CodeEmitter({})
    _collect_go_deps(dep_collector, east_doc)
    deps = dep_collector.finalize_deps()
    if len(deps) > 0:
        lines.append("import (")
        for dep in deps:
            lines.append('    "' + dep + '"')
        lines.append(")")
        lines.append("")
    module_comments = _module_leading_comment_lines(east_doc, "// ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    i = 0
    while i < len(classes):
        cname = _safe_ident(classes[i].get("name"), "PytraClass")
        iface_name = _class_iface_name(cname)
        method_sigs = _resolve_interface_method_sigs(cname, _CLASS_BASE_MAP, class_method_sig_map)
        lines.append("type " + iface_name + " interface {")
        j = 0
        while j < len(method_sigs):
            lines.append("    " + method_sigs[j])
            j += 1
        lines.append("}")
        lines.append("")
        i += 1

    i = 0
    while i < len(classes):
        cname = _safe_ident(classes[i].get("name"), "PytraClass")
        lines.append("")
        lines.append("func __pytra_is_" + cname + "(v any) bool {")
        lines.append("    _, ok := v.(*" + cname + ")")
        lines.append("    return ok")
        lines.append("}")
        lines.append("")
        lines.append("func __pytra_as_" + cname + "(v any) *" + cname + " {")
        lines.append("    if t, ok := v.(*" + cname + "); ok {")
        lines.append("        return t")
        lines.append("    }")
        lines.append("    return nil")
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
    lines.append("func main() {")
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
                            args = args_any if isinstance(args_any, list) else []
                            rendered_args: list[str] = []
                            j = 0
                            while j < len(args):
                                rendered_args.append(_render_expr(args[j]))
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
