"""EAST3 -> Scala 3 native emitter (core lowering stage)."""

from __future__ import annotations

from pytra.std.typing import Any


_SCALA_KEYWORDS = {
    "abstract",
    "case",
    "catch",
    "class",
    "def",
    "do",
    "else",
    "enum",
    "extends",
    "false",
    "final",
    "finally",
    "for",
    "forSome",
    "given",
    "if",
    "implicit",
    "import",
    "lazy",
    "match",
    "new",
    "null",
    "object",
    "override",
    "package",
    "private",
    "protected",
    "return",
    "sealed",
    "super",
    "then",
    "this",
    "throw",
    "trait",
    "true",
    "try",
    "type",
    "val",
    "var",
    "while",
    "with",
    "yield",
    "_",
    "break",
    "continue",
}

_CLASS_NAMES: set[str] = set()
_FUNCTION_NAMES: set[str] = set()
_CLASS_BASES: dict[str, str] = {}
_CLASS_METHODS: dict[str, set[str]] = {}


def _method_overrides_base(class_name: str, method_name: str) -> bool:
    base = _CLASS_BASES.get(class_name, "")
    seen: set[str] = set()
    while base != "":
        if base in seen:
            break
        seen.add(base)
        methods = _CLASS_METHODS.get(base)
        if isinstance(methods, set) and method_name in methods:
            return True
        base = _CLASS_BASES.get(base, "")
    return False


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
    if out == "_":
        out = fallback
    if out == "":
        out = "value"
    if out[0].isdigit():
        out = "_" + out
    if out in _SCALA_KEYWORDS:
        out = "py_" + out
    return out


def _arraybuffer_elem_scala_type(py_type_name: str) -> str:
    if py_type_name in {"int", "int64", "uint8"}:
        return "Long"
    if py_type_name in {"float", "float64"}:
        return "Double"
    if py_type_name == "bool":
        return "Boolean"
    if py_type_name in {"str", "Path"}:
        return "String"
    return "Any"


def _list_scala_type(type_name: str) -> str:
    if not type_name.startswith("list[") or not type_name.endswith("]"):
        return "mutable.ArrayBuffer[Any]"
    inner = type_name[5:-1].strip()
    elem_t = _arraybuffer_elem_scala_type(inner)
    if elem_t == "Any":
        return "mutable.ArrayBuffer[Any]"
    return "mutable.ArrayBuffer[" + elem_t + "]"


def _tuple_scala_type(type_name: str) -> str:
    if not type_name.startswith("tuple[") or not type_name.endswith("]"):
        return "mutable.ArrayBuffer[Any]"
    elems = _tuple_element_types(type_name)
    if len(elems) == 0:
        return "mutable.ArrayBuffer[Any]"
    first_t = _arraybuffer_elem_scala_type(elems[0])
    if first_t == "Any":
        return "mutable.ArrayBuffer[Any]"
    i = 1
    while i < len(elems):
        if _arraybuffer_elem_scala_type(elems[i]) != first_t:
            return "mutable.ArrayBuffer[Any]"
        i += 1
    return "mutable.ArrayBuffer[" + first_t + "]"


def _scala_string_literal(text: str) -> str:
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


def _scala_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "Any"
    if type_name == "None":
        return "Unit" if allow_void else "Any"
    if type_name in {"int", "int64", "uint8"}:
        return "Long"
    if type_name in {"float", "float64"}:
        return "Double"
    if type_name == "bool":
        return "Boolean"
    if type_name == "str":
        return "String"
    if type_name == "Path":
        return "String"
    if type_name.startswith("list["):
        return _list_scala_type(type_name)
    if type_name.startswith("tuple["):
        return _tuple_scala_type(type_name)
    if type_name.startswith("dict["):
        return "mutable.LinkedHashMap[Any, Any]"
    if type_name in {"bytes", "bytearray"}:
        return "mutable.ArrayBuffer[Long]"
    if type_name in {"unknown", "object", "any"}:
        return "Any"
    if type_name.isidentifier():
        return _safe_ident(type_name, "Any")
    return "Any"


def _default_return_expr(scala_type: str) -> str:
    if scala_type == "Long":
        return "0L"
    if scala_type == "Double":
        return "0.0"
    if scala_type == "Boolean":
        return "false"
    if scala_type == "String":
        return '""'
    if scala_type.startswith("mutable.ArrayBuffer[") and scala_type.endswith("]"):
        return scala_type + "()"
    if scala_type == "mutable.LinkedHashMap[Any, Any]":
        return "mutable.LinkedHashMap[Any, Any]()"
    if scala_type == "Unit":
        return ""
    if scala_type == "Any":
        return "null"
    return "new " + scala_type + "()"


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


def _strip_outer_parens(expr: str) -> str:
    cur = expr.strip()
    while len(cur) >= 2 and cur[0] == "(" and cur[-1] == ")":
        depth = 0
        ok = True
        i = 0
        while i < len(cur):
            ch = cur[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(cur) - 1:
                    ok = False
                    break
                if depth < 0:
                    ok = False
                    break
            i += 1
        if not ok or depth != 0:
            break
        cur = cur[1:-1].strip()
    return cur


def _is_direct_call(expr: str, fn_name: str) -> bool:
    txt = _strip_outer_parens(expr)
    prefix = fn_name + "("
    if not txt.startswith(prefix) or not txt.endswith(")"):
        return False
    depth = 0
    i = len(fn_name)
    while i < len(txt):
        ch = txt[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and i != len(txt) - 1:
                return False
            if depth < 0:
                return False
        i += 1
    return depth == 0


def _wrap_runtime_call(expr: str, fn_name: str) -> str:
    inner = _strip_outer_parens(expr)
    if _is_direct_call(inner, fn_name):
        return inner
    return fn_name + "(" + inner + ")"


def _to_int_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_int")


def _to_float_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_float")


def _to_truthy_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_truthy")


def _to_str_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_str")


def _to_list_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_as_list")


def _to_dict_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_as_dict")


def _has_resolved_type(node: Any, expected: set[str]) -> bool:
    if not isinstance(node, dict):
        return False
    resolved_any = node.get("resolved_type")
    if not isinstance(resolved_any, str):
        return False
    return resolved_any in expected


def _int_operand(expr: str, node: Any) -> str:
    if _has_resolved_type(node, {"int", "int64", "uint8"}):
        return expr
    return _to_int_expr(expr)


def _float_operand(expr: str, node: Any) -> str:
    if _has_resolved_type(node, {"float", "float64"}):
        return expr
    return _to_float_expr(expr)


def _is_int_literal(node: Any, expected: int) -> bool:
    if isinstance(node, int) and not isinstance(node, bool):
        return node == expected
    if not isinstance(node, dict):
        return False
    if node.get("kind") != "Constant":
        return False
    value = node.get("value")
    if isinstance(value, bool):
        return False
    return isinstance(value, int) and value == expected


def _cast_from_any(expr: str, scala_type: str) -> str:
    if scala_type == "Long":
        return _to_int_expr(expr)
    if scala_type == "Double":
        return _to_float_expr(expr)
    if scala_type == "Boolean":
        return _to_truthy_expr(expr)
    if scala_type == "String":
        return _to_str_expr(expr)
    if scala_type == "mutable.ArrayBuffer[Any]":
        return _to_list_expr(expr)
    if scala_type == "mutable.LinkedHashMap[Any, Any]":
        return _to_dict_expr(expr)
    if scala_type == "Any":
        return expr
    if scala_type in _CLASS_NAMES:
        return "__pytra_as_" + scala_type + "(" + expr + ")"
    return expr


def _render_name_expr(expr: dict[str, Any]) -> str:
    name = _safe_ident(expr.get("id"), "value")
    if name == "self":
        return "this"
    if name in _FUNCTION_NAMES:
        return "(() => " + name + "())"
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
        return _scala_string_literal(value)
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
    return _to_truthy_expr(rendered)


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
    left_type = ""
    right_type = ""
    left_any = expr.get("left")
    right_any = expr.get("right")
    if isinstance(left_any, dict):
        left_resolved_any = left_any.get("resolved_type")
        left_type = left_resolved_any if isinstance(left_resolved_any, str) else ""
    if isinstance(right_any, dict):
        right_resolved_any = right_any.get("resolved_type")
        right_type = right_resolved_any if isinstance(right_resolved_any, str) else ""

    if op == "Div" and (resolved == "Path" or left_type == "Path" or right_type == "Path"):
        return "__pytra_path_join(" + left_expr + ", " + right_expr + ")"

    if op == "Div":
        return "(" + _float_operand(left_expr, left_any) + " / " + _float_operand(right_expr, right_any) + ")"

    if op == "FloorDiv":
        lhs = _int_operand(left_expr, left_any)
        rhs = _int_operand(right_expr, right_any)
        return "(" + _to_int_expr(lhs + " / " + rhs) + ")"

    if op == "Mod":
        return "(" + _int_operand(left_expr, left_any) + " % " + _int_operand(right_expr, right_any) + ")"

    if resolved == "str" and op == "Add":
        return "(" + _to_str_expr(left_expr) + " + " + _to_str_expr(right_expr) + ")"

    if resolved in {"int", "int64", "uint8"}:
        sym = _bin_op_symbol(op)
        return "(" + _int_operand(left_expr, left_any) + " " + sym + " " + _int_operand(right_expr, right_any) + ")"

    if resolved in {"float", "float64"}:
        sym = _bin_op_symbol(op)
        return "(" + _float_operand(left_expr, left_any) + " " + sym + " " + _float_operand(right_expr, right_any) + ")"

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
        left_node: Any = None
        right_node: Any = comp_node
        if i == 0 and isinstance(expr.get("left"), dict):
            left_node = expr.get("left")
            left_any = expr.get("left", {}).get("resolved_type")
            left_type = left_any if isinstance(left_any, str) else ""
        elif i > 0 and isinstance(comps[i - 1], dict):
            left_node = comps[i - 1]
            left_any = comps[i - 1].get("resolved_type")
            left_type = left_any if isinstance(left_any, str) else ""
        if isinstance(comp_node, dict):
            right_any = comp_node.get("resolved_type")
            right_type = right_any if isinstance(right_any, str) else ""

        symbol = _compare_op_symbol(op)
        if left_type == "str" or right_type == "str":
            lhs = _to_str_expr(cur_left)
            rhs = _to_str_expr(right)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        elif left_type in {"int", "int64", "uint8"} or right_type in {"int", "int64", "uint8"}:
            lhs = _int_operand(cur_left, left_node)
            rhs = _int_operand(right, right_node)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        elif left_type in {"float", "float64"} or right_type in {"float", "float64"}:
            lhs = _float_operand(cur_left, left_node)
            rhs = _float_operand(right, right_node)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        else:
            if op in {"Eq", "NotEq"}:
                lhs = _to_str_expr(cur_left)
                rhs = _to_str_expr(right)
                parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
            else:
                lhs = _float_operand(cur_left, left_node)
                rhs = _float_operand(right, right_node)
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
        return "scala.math.sqrt"
    if attr == "sin":
        return "scala.math.sin"
    if attr == "cos":
        return "scala.math.cos"
    if attr == "tan":
        return "scala.math.tan"
    if attr == "exp":
        return "scala.math.exp"
    if attr == "log":
        return "scala.math.log"
    if attr == "pow":
        return "scala.math.pow"
    if attr == "floor":
        return "scala.math.floor"
    if attr == "ceil":
        return "scala.math.ceil"
    if attr == "abs":
        return "scala.math.abs"
    if attr == "fabs":
        return "scala.math.abs"
    return _safe_ident(attr, "call")


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    value_any = expr.get("value")
    attr = _safe_ident(expr.get("attr"), "field")
    owner_type = ""
    if isinstance(value_any, dict):
        owner_type_any = value_any.get("resolved_type")
        owner_type = owner_type_any if isinstance(owner_type_any, str) else ""
    if isinstance(value_any, dict) and value_any.get("kind") == "Name":
        owner = _safe_ident(value_any.get("id"), "")
        if owner == "math" and attr == "pi":
            return "Math.PI"
        if owner == "math" and attr == "e":
            return "Math.E"
    value = _render_expr(value_any)
    if owner_type == "Path" and attr == "name":
        return "__pytra_path_name(" + value + ")"
    if owner_type == "Path" and attr == "stem":
        return "__pytra_path_stem(" + value + ")"
    if owner_type == "Path" and attr == "parent":
        return "__pytra_path_parent(" + value + ")"
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
    if callee_name == "super":
        if len(args) == 0:
            return "super"
        rendered_super_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_super_args.append(_render_expr(args[i]))
            i += 1
        return "super(" + ", ".join(rendered_super_args) + ")"
    if callee_name.startswith("py_assert_"):
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered_assert_args) + ")"
    if callee_name == "perf_counter":
        return "__pytra_perf_counter()"
    if callee_name == "Path":
        if len(args) == 0:
            return "__pytra_path_new(\"\")"
        return "__pytra_path_new(" + _render_expr(args[0]) + ")"
    if callee_name == "bytearray":
        if len(args) == 0:
            return "mutable.ArrayBuffer[Long]()"
        return "__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee_name == "bytes":
        if len(args) == 0:
            return "mutable.ArrayBuffer[Long]()"
        return "__pytra_bytes(" + _render_expr(args[0]) + ")"
    if callee_name == "int":
        if len(args) == 0:
            return "0L"
        arg0 = args[0]
        rendered_arg0 = _render_expr(arg0)
        if _has_resolved_type(arg0, {"int", "int64", "uint8"}):
            return rendered_arg0
        return _to_int_expr(rendered_arg0)
    if callee_name == "float":
        if len(args) == 0:
            return "0.0"
        arg0 = args[0]
        rendered_arg0 = _render_expr(arg0)
        if _has_resolved_type(arg0, {"float", "float64"}):
            return rendered_arg0
        return _to_float_expr(rendered_arg0)
    if callee_name == "bool":
        if len(args) == 0:
            return "false"
        return _to_truthy_expr(_render_expr(args[0]))
    if callee_name == "str":
        if len(args) == 0:
            return '""'
        return _to_str_expr(_render_expr(args[0]))
    if callee_name == "len":
        if len(args) == 0:
            return "0L"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "enumerate":
        if len(args) == 0:
            return "mutable.ArrayBuffer[Any]()"
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
    if callee_name == "write_rgb_png":
        rendered_args_png: list[str] = []
        i = 0
        while i < len(args):
            rendered_args_png.append(_render_expr(args[i]))
            i += 1
        return "__pytra_write_rgb_png(" + ", ".join(rendered_args_png) + ")"
    if callee_name == "save_gif":
        rendered_args_gif: list[str] = []
        i = 0
        while i < len(args):
            rendered_args_gif.append(_render_expr(args[i]))
            i += 1
        return "__pytra_save_gif(" + ", ".join(rendered_args_gif) + ")"
    if callee_name == "grayscale_palette":
        return "__pytra_grayscale_palette()"
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
                    rendered_math_args.append(_to_float_expr(_render_expr(args[i])))
                    i += 1
                if attr_name == "pow" and len(rendered_math_args) == 2:
                    return "scala.math.pow(" + rendered_math_args[0] + ", " + rendered_math_args[1] + ")"
                return _math_call_name(attr_name) + "(" + ", ".join(rendered_math_args) + ")"
        if attr_name == "isdigit" and len(args) == 0:
            return "__pytra_isdigit(" + _render_expr(owner_any) + ")"
        if attr_name == "isalpha" and len(args) == 0:
            return "__pytra_isalpha(" + _render_expr(owner_any) + ")"
        if attr_name == "get":
            if len(args) == 0:
                return "__pytra_any_default()"
            key_expr = _render_expr(args[0])
            default_expr = "__pytra_any_default()"
            if len(args) >= 2:
                default_expr = _render_expr(args[1])
            owner_expr = _render_expr(owner_any)
            return "__pytra_as_dict(" + owner_expr + ").getOrElse(__pytra_str(" + key_expr + "), " + default_expr + ")"
        owner_type = ""
        if isinstance(owner_any, dict):
            owner_type_any = owner_any.get("resolved_type")
            owner_type = owner_type_any if isinstance(owner_type_any, str) else ""
        owner_expr = _render_expr(owner_any)
        if owner_type == "Path" and attr_name == "exists" and len(args) == 0:
            return "__pytra_path_exists(" + owner_expr + ")"
        if owner_type == "Path" and attr_name == "mkdir":
            return "__pytra_path_mkdir(" + owner_expr + ")"
        if owner_type == "Path" and attr_name == "write_text" and len(args) >= 1:
            return "__pytra_path_write_text(" + owner_expr + ", " + _render_expr(args[0]) + ")"
        if owner_type == "Path" and attr_name == "read_text" and len(args) == 0:
            return "__pytra_path_read_text(" + owner_expr + ")"
        if attr_name == "write_rgb_png":
            rendered_args_png: list[str] = []
            i = 0
            while i < len(args):
                rendered_args_png.append(_render_expr(args[i]))
                i += 1
            return "__pytra_write_rgb_png(" + ", ".join(rendered_args_png) + ")"
        if attr_name == "save_gif":
            rendered_args_gif: list[str] = []
            i = 0
            while i < len(args):
                rendered_args_gif.append(_render_expr(args[i]))
                i += 1
            return "__pytra_save_gif(" + ", ".join(rendered_args_gif) + ")"
        if attr_name == "grayscale_palette" and len(args) == 0:
            return "__pytra_grayscale_palette()"
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
        return "new " + callee_name + "(" + ", ".join(rendered_ctor_args) + ")"

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
        list_type = "mutable.ArrayBuffer[Any]"
        resolved_any = expr.get("resolved_type")
        resolved = resolved_any if isinstance(resolved_any, str) else ""
        if kind == "List" and resolved.startswith("list["):
            list_type = _list_scala_type(resolved)
        if kind == "Tuple" and resolved.startswith("tuple["):
            list_type = _tuple_scala_type(resolved)
        if len(rendered) == 0:
            return list_type + "()"
        return list_type + "(" + ", ".join(rendered) + ")"

    if kind == "Dict":
        keys_any = expr.get("keys")
        vals_any = expr.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        vals = vals_any if isinstance(vals_any, list) else []
        if len(keys) == 0 or len(vals) == 0:
            entries_any = expr.get("entries")
            entries = entries_any if isinstance(entries_any, list) else []
            parts: list[str] = []
            i = 0
            while i < len(entries):
                entry = entries[i]
                if isinstance(entry, dict):
                    key_any = entry.get("key")
                    value_any = entry.get("value")
                    if isinstance(key_any, dict):
                        parts.append("(__pytra_str(" + _render_expr(key_any) + "), " + _render_expr(value_any) + ")")
                i += 1
            if len(parts) == 0:
                return "mutable.LinkedHashMap[Any, Any]()"
            return "mutable.LinkedHashMap[Any, Any](" + ", ".join(parts) + ")"
        if len(keys) == 0 or len(vals) == 0:
            return "mutable.LinkedHashMap[Any, Any]()"
        parts: list[str] = []
        i = 0
        while i < len(keys) and i < len(vals):
            parts.append("(__pytra_str(" + _render_expr(keys[i]) + "), " + _render_expr(vals[i]) + ")")
            i += 1
        return "mutable.LinkedHashMap[Any, Any](" + ", ".join(parts) + ")"

    if kind == "ListComp":
        gens_any = expr.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "mutable.ArrayBuffer[Any]()"
        gen = gens[0]
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if len(ifs) != 0:
            return "mutable.ArrayBuffer[Any]()"
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
            return "mutable.ArrayBuffer[Any]()"
        if not isinstance(iter_any, dict) or iter_any.get("kind") != "RangeExpr":
            return "mutable.ArrayBuffer[Any]()"
        loop_var = _safe_ident(target_any.get("id"), "i")
        if loop_var == "_":
            loop_var = "__lc_i"
        start = _render_expr(iter_any.get("start"))
        stop = _render_expr(iter_any.get("stop"))
        step = _render_expr(iter_any.get("step"))
        elt = _render_expr(expr.get("elt"))
        return (
            "({ "
            "val __out = mutable.ArrayBuffer[Any](); "
            "val __step = __pytra_int(" + step + "); "
            "var " + loop_var + " = __pytra_int(" + start + "); "
            "while ((__step >= 0L && "
            + loop_var
            + " < __pytra_int(" + stop + ")) || (__step < 0L && "
            + loop_var
            + " > __pytra_int(" + stop + "))) { "
            "__out.append(" + elt + "); "
            + loop_var
            + " += __step "
            "}; "
            "__out "
            "})"
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
        scala_t = _scala_type(resolved, allow_void=False)
        return _cast_from_any(base, scala_t)

    if kind == "IsInstance":
        lhs = _render_expr(expr.get("value"))
        return _render_isinstance_check(lhs, expr.get("expected_type_id"))

    if kind == "ObjLen":
        return "__pytra_len(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjStr":
        return _to_str_expr(_render_expr(expr.get("value")))
    if kind == "ObjBool":
        return _to_truthy_expr(_render_expr(expr.get("value")))

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
        out.append(name + ": " + _scala_type(arg_types.get(name), allow_void=False))
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


def _infer_scala_type(expr: Any, type_map: dict[str, str] | None = None) -> str:
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
            return "Long"
        if name == "float":
            return "Double"
        if name == "bool":
            return "Boolean"
        if name == "str":
            return "String"
        if name == "Path":
            return "String"
        if name == "bytearray" or name == "bytes":
            return "mutable.ArrayBuffer[Long]"
        if name == "len":
            return "Long"
        if name in {"min", "max"}:
            args_any = expr.get("args")
            args = args_any if isinstance(args_any, list) else []
            seen_any = False
            i = 0
            while i < len(args):
                arg_t = _infer_scala_type(args[i], type_map)
                if arg_t == "Double":
                    return "Double"
                if arg_t == "Any":
                    seen_any = True
                i += 1
            if seen_any:
                return "Any"
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
                if attr_name in {"sqrt", "sin", "cos", "tan", "exp", "log", "pow", "floor", "ceil", "abs", "fabs"}:
                    return "Double"
            if attr_name in {"isdigit", "isalpha"}:
                return "Boolean"
    if kind == "BinOp":
        op = expr.get("op")
        if op == "Div":
            return "Double"
        left_t = _infer_scala_type(expr.get("left"), type_map)
        right_t = _infer_scala_type(expr.get("right"), type_map)
        if left_t == "Double" or right_t == "Double":
            return "Double"
        if left_t == "Long" and right_t == "Long":
            return "Long"
        if op == "Mult":
            left_any = expr.get("left")
            right_any = expr.get("right")
            if isinstance(left_any, dict) and left_any.get("kind") == "List":
                return "mutable.ArrayBuffer[Any]"
            if isinstance(right_any, dict) and right_any.get("kind") == "List":
                return "mutable.ArrayBuffer[Any]"
    if kind == "IfExp":
        body_t = _infer_scala_type(expr.get("body"), type_map)
        else_t = _infer_scala_type(expr.get("orelse"), type_map)
        if body_t == else_t:
            return body_t
        if body_t == "Double" or else_t == "Double":
            return "Double"
        if body_t == "Long" and else_t == "Long":
            return "Long"
    resolved = expr.get("resolved_type")
    return _scala_type(resolved, allow_void=False)


def _expr_emits_target_type(value_expr: Any, target_type: str, type_map: dict[str, str] | None = None) -> bool:
    if not isinstance(value_expr, dict):
        return False
    kind = value_expr.get("kind")
    if kind == "Name":
        if isinstance(type_map, dict):
            ident = _safe_ident(value_expr.get("id"), "")
            mapped_any = type_map.get(ident)
            mapped = mapped_any if isinstance(mapped_any, str) else ""
            return mapped == target_type
        return False
    if kind == "Constant":
        value = value_expr.get("value")
        if target_type == "Long":
            return isinstance(value, int) and not isinstance(value, bool)
        if target_type == "Double":
            return isinstance(value, float)
        if target_type == "Boolean":
            return isinstance(value, bool)
        if target_type == "String":
            return isinstance(value, str)
        return False
    if kind == "BinOp":
        resolved = _scala_type(value_expr.get("resolved_type"), allow_void=False)
        return resolved == target_type
    if kind in {"Compare", "BoolOp", "IsInstance"}:
        return target_type == "Boolean"
    if kind == "Call":
        callee = _call_name(value_expr)
        if callee == "int":
            return target_type == "Long"
        if callee == "float":
            return target_type == "Double"
        if callee == "bool":
            return target_type == "Boolean"
        if callee == "str":
            return target_type == "String"
        if callee == "perf_counter":
            return target_type == "Double"
        if callee == "len":
            return target_type == "Long"
    return False


def _needs_cast(value_expr: Any, target_type: str, type_map: dict[str, str] | None = None) -> bool:
    if target_type in {"", "Any"}:
        return False
    return not _expr_emits_target_type(value_expr, target_type, type_map)


def _stmt_uses_loop_control(stmt_any: Any) -> bool:
    if not isinstance(stmt_any, dict):
        return False
    kind = stmt_any.get("kind")
    if kind in {"Break", "Continue"}:
        return True
    if kind == "Expr":
        value_any = stmt_any.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name":
            ident = _safe_ident(value_any.get("id"), "")
            return ident in {"break", "continue"}
        return False
    if kind in {"ForCore", "While", "FunctionDef", "ClassDef"}:
        # break/continue inside nested loops/functions do not require boundary for this loop.
        return False

    for key in ("body", "orelse", "finalbody"):
        block_any = stmt_any.get(key)
        if isinstance(block_any, list):
            i = 0
            while i < len(block_any):
                if _stmt_uses_loop_control(block_any[i]):
                    return True
                i += 1

    handlers_any = stmt_any.get("handlers")
    handlers = handlers_any if isinstance(handlers_any, list) else []
    i = 0
    while i < len(handlers):
        handler_any = handlers[i]
        if isinstance(handler_any, dict):
            h_body_any = handler_any.get("body")
            h_body = h_body_any if isinstance(h_body_any, list) else []
            j = 0
            while j < len(h_body):
                if _stmt_uses_loop_control(h_body[j]):
                    return True
                j += 1
        i += 1
    return False


def _body_uses_loop_control(body_any: Any) -> bool:
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        if _stmt_uses_loop_control(body[i]):
            return True
        i += 1
    return False


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        raise RuntimeError("scala native emitter: unsupported ForCore iter_plan")
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("scala native emitter: unsupported ForCore target_plan")

    lines: list[str] = []
    if iter_plan_any.get("kind") == "StaticRangeForPlan" and target_plan_any.get("kind") == "NameTarget":
        target_name = _safe_ident(target_plan_any.get("id"), "i")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "loop")
        start_node = iter_plan_any.get("start")
        stop_node = iter_plan_any.get("stop")
        step_node = iter_plan_any.get("step")
        start = _int_operand(_render_expr(start_node), start_node)
        stop = _int_operand(_render_expr(stop_node), stop_node)
        step = _int_operand(_render_expr(step_node), step_node)
        step_is_one = _is_int_literal(step_node, 1)
        normalized_cond = ""
        normalized_version_any = stmt.get("normalized_expr_version")
        if isinstance(normalized_version_any, str) and normalized_version_any == "east3_expr_v1":
            normalized_exprs_any = stmt.get("normalized_exprs")
            if isinstance(normalized_exprs_any, dict):
                for_cond_any = normalized_exprs_any.get("for_cond_expr")
                if isinstance(for_cond_any, dict):
                    normalized_cond = _render_expr(for_cond_any)
        step_tmp = _fresh_tmp(ctx, "step")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        loop_uses_control = _body_uses_loop_control(body)
        break_label = _fresh_tmp(ctx, "breakLabel") if loop_uses_control else ""
        continue_label = _fresh_tmp(ctx, "continueLabel") if loop_uses_control else ""
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        if target_name in declared:
            lines.append(indent + target_name + " = " + start)
        else:
            # Python for-loop variables leak to outer scope; keep declaration outside boundary.
            lines.append(indent + "var " + target_name + ": Long = " + start)
            declared.add(target_name)
            type_map[target_name] = "Long"
        if loop_uses_control:
            lines.append(indent + "boundary:")
            lines.append(indent + "    given " + break_label + ": boundary.Label[Unit] = summon[boundary.Label[Unit]]")
        if step_is_one:
            while_prefix = indent + "    " if loop_uses_control else indent
            cond_text = normalized_cond if normalized_cond != "" else target_name + " < " + stop
            lines.append(while_prefix + "while (" + cond_text + ") {")
        else:
            step_prefix = indent + "    " if loop_uses_control else indent
            lines.append(step_prefix + "val " + step_tmp + " = " + step)
            while_prefix = indent + "    " if loop_uses_control else indent
            cond_text = ""
            range_mode_any = iter_plan_any.get("range_mode")
            range_mode = range_mode_any if isinstance(range_mode_any, str) else ""
            if normalized_cond != "" and range_mode in {"ascending", "descending"}:
                cond_text = normalized_cond
            if cond_text == "":
                cond_text = (
                    "("
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
                    + ")"
                )
            lines.append(while_prefix + "while (" + cond_text + ") {")
        if loop_uses_control:
            lines.append(indent + "        boundary:")
            lines.append(indent + "            given " + continue_label + ": boundary.Label[Unit] = summon[boundary.Label[Unit]]")
            body_indent = indent + "            "
            step_indent = indent + "        "
        else:
            body_indent = indent + "    "
            step_indent = indent + "    "
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": target_name + (" += 1L" if step_is_one else " += " + step_tmp),
            "break_label": break_label if loop_uses_control else "",
            "continue_label": continue_label if loop_uses_control else "",
            "yield_buffer": ctx.get("yield_buffer", ""),
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = "Long"
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=body_indent, ctx=body_ctx))
            i += 1
        if step_is_one:
            lines.append(step_indent + target_name + " += 1L")
        else:
            lines.append(step_indent + target_name + " += " + step_tmp)
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        while_end_prefix = indent + "    " if loop_uses_control else indent
        lines.append(while_end_prefix + "}")
        return lines

    if iter_plan_any.get("kind") == "RuntimeIterForPlan" and target_plan_any.get("kind") == "NameTarget":
        iter_expr = _render_expr(iter_plan_any.get("iter_expr"))
        iter_tmp = _fresh_tmp(ctx, "iter")
        idx_tmp = _fresh_tmp(ctx, "i")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        loop_uses_control = _body_uses_loop_control(body)
        break_label = _fresh_tmp(ctx, "breakLabel") if loop_uses_control else ""
        continue_label = _fresh_tmp(ctx, "continueLabel") if loop_uses_control else ""
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
        target_scala_type = _scala_type(target_type_txt, allow_void=False)
        if loop_uses_control:
            lines.append(indent + "boundary:")
            lines.append(indent + "    given " + break_label + ": boundary.Label[Unit] = summon[boundary.Label[Unit]]")
            while_prefix = indent + "    "
            value_prefix = indent + "            "
            body_indent = indent + "            "
            inc_prefix = indent + "        "
            lines.append(indent + "    val " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
            lines.append(indent + "    var " + idx_tmp + ": Long = 0L")
            lines.append(indent + "    while (" + idx_tmp + " < " + iter_tmp + ".size.toLong) {")
            lines.append(indent + "        boundary:")
            lines.append(indent + "            given " + continue_label + ": boundary.Label[Unit] = summon[boundary.Label[Unit]]")
        else:
            while_prefix = indent
            value_prefix = indent + "    "
            body_indent = indent + "    "
            inc_prefix = indent + "    "
            lines.append(indent + "val " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
            lines.append(indent + "var " + idx_tmp + ": Long = 0L")
            lines.append(indent + "while (" + idx_tmp + " < " + iter_tmp + ".size.toLong) {")
        if target_scala_type == "Any":
            lines.append(value_prefix + "val " + target_name + " = " + iter_tmp + "(" + idx_tmp + ".toInt)")
        else:
            lines.append(
                value_prefix
                + "val "
                + target_name
                + ": "
                + target_scala_type
                + " = "
                + _cast_from_any(iter_tmp + "(" + idx_tmp + ".toInt)", target_scala_type)
            )
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": idx_tmp + " += 1L",
            "break_label": break_label if loop_uses_control else "",
            "continue_label": continue_label if loop_uses_control else "",
            "yield_buffer": ctx.get("yield_buffer", ""),
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = target_scala_type
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=body_indent, ctx=body_ctx))
            i += 1
        lines.append(inc_prefix + idx_tmp + " += 1L")
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(while_prefix + "}")
        return lines

    if iter_plan_any.get("kind") == "RuntimeIterForPlan" and target_plan_any.get("kind") == "TupleTarget":
        iter_expr = _render_expr(iter_plan_any.get("iter_expr"))
        iter_tmp = _fresh_tmp(ctx, "iter")
        idx_tmp = _fresh_tmp(ctx, "i")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        loop_uses_control = _body_uses_loop_control(body)
        break_label = _fresh_tmp(ctx, "breakLabel") if loop_uses_control else ""
        continue_label = _fresh_tmp(ctx, "continueLabel") if loop_uses_control else ""
        item_tmp = _fresh_tmp(ctx, "it")
        tuple_tmp = _fresh_tmp(ctx, "tuple")
        if loop_uses_control:
            lines.append(indent + "boundary:")
            lines.append(indent + "    given " + break_label + ": boundary.Label[Unit] = summon[boundary.Label[Unit]]")
            while_prefix = indent + "    "
            value_prefix = indent + "            "
            body_indent = indent + "            "
            inc_prefix = indent + "        "
            lines.append(indent + "    val " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
            lines.append(indent + "    var " + idx_tmp + ": Long = 0L")
            lines.append(indent + "    while (" + idx_tmp + " < " + iter_tmp + ".size.toLong) {")
            lines.append(indent + "        boundary:")
            lines.append(indent + "            given " + continue_label + ": boundary.Label[Unit] = summon[boundary.Label[Unit]]")
        else:
            while_prefix = indent
            value_prefix = indent + "    "
            body_indent = indent + "    "
            inc_prefix = indent + "    "
            lines.append(indent + "val " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
            lines.append(indent + "var " + idx_tmp + ": Long = 0L")
            lines.append(indent + "while (" + idx_tmp + " < " + iter_tmp + ".size.toLong) {")
        lines.append(value_prefix + "val " + item_tmp + " = " + iter_tmp + "(" + idx_tmp + ".toInt)")
        lines.append(value_prefix + "val " + tuple_tmp + " = __pytra_as_list(" + item_tmp + ")")

        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": idx_tmp + " += 1L",
            "break_label": break_label if loop_uses_control else "",
            "continue_label": continue_label if loop_uses_control else "",
            "yield_buffer": ctx.get("yield_buffer", ""),
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
                raise RuntimeError("scala native emitter: unsupported tuple target element")
            name = _safe_ident(elem.get("id"), "item_" + str(i))
            if name == "_":
                i += 1
                continue
            rhs = tuple_tmp + "(" + str(i) + ")"
            target_t_any = elem.get("target_type")
            target_t = target_t_any if isinstance(target_t_any, str) else ""
            if target_t in {"", "unknown"} and i < len(elem_types):
                target_t = elem_types[i]
            scala_t = _scala_type(target_t, allow_void=False)
            casted = _cast_from_any(rhs, scala_t)
            if name not in declared:
                lines.append(value_prefix + "var " + name + ": " + scala_t + " = " + casted)
                declared.add(name)
            else:
                lines.append(value_prefix + name + " = " + casted)
            type_map[name] = scala_t
            i += 1

        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=body_indent, ctx=body_ctx))
            i += 1
        lines.append(inc_prefix + idx_tmp + " += 1L")
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(while_prefix + "}")
        return lines

    raise RuntimeError("scala native emitter: unsupported ForCore plan")


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
        rhs = tuple_tmp + "(" + str(i) + ")"
        elem_type = "Any"
        if i < len(tuple_types):
            elem_type = _scala_type(tuple_types[i], allow_void=False)
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
        raise RuntimeError("scala native emitter: unsupported statement node")
    kind = stmt.get("kind")

    if kind == "Return":
        if "value" in stmt and stmt.get("value") is not None:
            value = _render_expr(stmt.get("value"))
            return_type_any = ctx.get("return_type")
            return_type = return_type_any if isinstance(return_type_any, str) else ""
            if return_type not in {"", "Any"} and _needs_cast(stmt.get("value"), return_type, _type_map(ctx)):
                value = _cast_from_any(value, return_type)
            return [indent + "return " + value]
        return [indent + "return"]

    if kind == "Expr":
        value_any = stmt.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name":
            raw_ident = value_any.get("id")
            if raw_ident == "break":
                break_label_any = ctx.get("break_label")
                break_label = break_label_any if isinstance(break_label_any, str) else ""
                if break_label != "":
                    return [indent + "break(())(using " + break_label + ")"]
                return [indent + "throw new RuntimeException(\"pytra break outside loop\")"]
            if raw_ident == "continue":
                continue_label_any = ctx.get("continue_label")
                continue_label = continue_label_any if isinstance(continue_label_any, str) else ""
                if continue_label != "":
                    return [indent + "break(())(using " + continue_label + ")"]
                return [indent + "throw new RuntimeException(\"pytra continue outside loop\")"]
        if isinstance(value_any, dict) and value_any.get("kind") == "Call":
            func_any = value_any.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
                attr = _safe_ident(func_any.get("attr"), "")
                if attr == "append":
                    owner_any = func_any.get("value")
                    owner = _render_expr(owner_any)
                    owner_type = ""
                    if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
                        owner_name = _safe_ident(owner_any.get("id"), "")
                        type_hint_any = _type_map(ctx).get(owner_name)
                        owner_type = type_hint_any if isinstance(type_hint_any, str) else ""
                    args_any = value_any.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) == 1:
                        if owner_type.startswith("mutable.ArrayBuffer["):
                            return [indent + owner + ".append(" + _render_expr(args[0]) + ")"]
                        return [indent + owner + " = " + _to_list_expr(owner) + "; " + owner + ".append(" + _render_expr(args[0]) + ")"]
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
        scala_type = _scala_type(stmt.get("decl_type") or stmt.get("annotation"), allow_void=False)
        if scala_type == "Any":
            inferred = _infer_scala_type(stmt.get("value"), _type_map(ctx))
            if inferred != "Any":
                scala_type = inferred

        stmt_value = stmt.get("value")
        if stmt_value is None:
            value = _default_return_expr(scala_type)
        else:
            value = _render_expr(stmt_value)
            if scala_type != "Any" and _needs_cast(stmt_value, scala_type, _type_map(ctx)):
                value = _cast_from_any(value, scala_type)
        if stmt.get("declare") is False or target in declared:
            if target not in declared:
                declared.add(target)
                type_map[target] = scala_type
                return [indent + "var " + target + ": " + scala_type + " = " + value]
            if target in type_map and type_map[target] != "Any":
                if stmt_value is None:
                    return [indent + target + " = " + _default_return_expr(type_map[target])]
                reassigned = _render_expr(stmt_value)
                if _needs_cast(stmt_value, type_map[target], _type_map(ctx)):
                    reassigned = _cast_from_any(reassigned, type_map[target])
                return [indent + target + " = " + reassigned]
            return [indent + target + " = " + value]

        declared.add(target)
        type_map[target] = scala_type
        return [indent + "var " + target + ": " + scala_type + " = " + value]

    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            raise RuntimeError("scala native emitter: Assign without target")

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
                if lhs in type_map and type_map[lhs] != "Any":
                    if _needs_cast(stmt.get("value"), type_map[lhs], _type_map(ctx)):
                        return [indent + lhs + " = " + _cast_from_any(value, type_map[lhs])]
                    return [indent + lhs + " = " + value]
                return [indent + lhs + " = " + value]
            scala_type = _scala_type(stmt.get("decl_type"), allow_void=False)
            if scala_type == "Any":
                inferred = _infer_scala_type(stmt.get("value"), _type_map(ctx))
                if inferred != "Any":
                    scala_type = inferred
            if scala_type != "Any" and _needs_cast(stmt.get("value"), scala_type, _type_map(ctx)):
                value = _cast_from_any(value, scala_type)
            declared.add(lhs)
            type_map[lhs] = scala_type
            return [indent + "var " + lhs + ": " + scala_type + " = " + value]

        if lhs not in declared:
            inferred = _infer_scala_type(stmt.get("value"), _type_map(ctx))
            declared.add(lhs)
            type_map[lhs] = inferred
            if inferred != "Any" and _needs_cast(stmt.get("value"), inferred, _type_map(ctx)):
                value = _cast_from_any(value, inferred)
            return [indent + "var " + lhs + ": " + inferred + " = " + value]
        if lhs in type_map and type_map[lhs] != "Any":
            if _needs_cast(stmt.get("value"), type_map[lhs], _type_map(ctx)):
                return [indent + lhs + " = " + _cast_from_any(value, type_map[lhs])]
            return [indent + lhs + " = " + value]
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

    if kind == "Swap":
        left = _target_name(stmt.get("left"))
        right = _target_name(stmt.get("right"))
        tmp = _fresh_tmp(ctx, "swap")
        return [
            indent + "val " + tmp + " = " + left,
            indent + left + " = " + right,
            indent + right + " = " + tmp,
        ]

    if kind == "Yield":
        yield_buffer_any = ctx.get("yield_buffer")
        yield_buffer = yield_buffer_any if isinstance(yield_buffer_any, str) else ""
        if yield_buffer == "":
            raise RuntimeError("scala native emitter: unsupported yield outside generator")
        value_any = stmt.get("value")
        if value_any is None:
            return [indent + yield_buffer + ".append(__pytra_any_default())"]
        return [indent + yield_buffer + ".append(" + _render_expr(value_any) + ")"]

    if kind == "Try":
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        handlers_any = stmt.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        final_any = stmt.get("finalbody")
        finalbody = final_any if isinstance(final_any, list) else []
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []

        lines: list[str] = [indent + "try {"]
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        i = 0
        while i < len(orelse):
            lines.extend(_emit_stmt(orelse[i], indent=indent + "    ", ctx=ctx))
            i += 1

        if len(handlers) > 0:
            if len(handlers) > 1:
                raise RuntimeError("scala native emitter: multiple except handlers are unsupported")
            lines.append(indent + "} catch {")
            base_ex = _fresh_tmp(ctx, "ex")
            lines.append(indent + "    case " + base_ex + ": Throwable =>")
            first = handlers[0]
            if not isinstance(first, dict):
                raise RuntimeError("scala native emitter: invalid except handler node")
            alias_any = first.get("name")
            alias_raw = alias_any if isinstance(alias_any, str) else ""
            alias = _safe_ident(alias_raw, "") if alias_raw != "" else ""
            if alias != "" and alias != base_ex:
                lines.append(indent + "        val " + alias + " = " + base_ex)
            h_body_any = first.get("body")
            h_body = h_body_any if isinstance(h_body_any, list) else []
            i = 0
            while i < len(h_body):
                lines.extend(_emit_stmt(h_body[i], indent=indent + "        ", ctx=ctx))
                i += 1

        if len(finalbody) > 0:
            if len(handlers) == 0:
                lines.append(indent + "} finally {")
            else:
                lines.append(indent + "} finally {")
            i = 0
            while i < len(finalbody):
                lines.extend(_emit_stmt(finalbody[i], indent=indent + "    ", ctx=ctx))
                i += 1

        lines.append(indent + "}")
        return lines

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
            "break_label": ctx.get("break_label", ""),
            "continue_label": ctx.get("continue_label", ""),
            "yield_buffer": ctx.get("yield_buffer", ""),
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
            "break_label": ctx.get("break_label", ""),
            "continue_label": ctx.get("continue_label", ""),
            "yield_buffer": ctx.get("yield_buffer", ""),
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
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        loop_uses_control = _body_uses_loop_control(body)
        break_label = _fresh_tmp(ctx, "breakLabel") if loop_uses_control else ""
        continue_label = _fresh_tmp(ctx, "continueLabel") if loop_uses_control else ""
        if loop_uses_control:
            lines = [
                indent + "boundary:",
                indent + "    given " + break_label + ": boundary.Label[Unit] = summon[boundary.Label[Unit]]",
                indent + "    while (" + test_expr + ") {",
                indent + "        boundary:",
                indent + "            given " + continue_label + ": boundary.Label[Unit] = summon[boundary.Label[Unit]]",
            ]
            body_indent = indent + "            "
            while_end = indent + "    }"
        else:
            lines = [indent + "while (" + test_expr + ") {"]
            body_indent = indent + "    "
            while_end = indent + "}"
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": "",
            "break_label": break_label if loop_uses_control else "",
            "continue_label": continue_label if loop_uses_control else "",
            "yield_buffer": ctx.get("yield_buffer", ""),
        }
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=body_indent, ctx=body_ctx))
            i += 1
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(while_end)
        return lines

    if kind == "Pass":
        return [indent + "// pass"]

    if kind == "Break":
        break_label_any = ctx.get("break_label")
        break_label = break_label_any if isinstance(break_label_any, str) else ""
        if break_label != "":
            return [indent + "break(())(using " + break_label + ")"]
        return [indent + "throw new RuntimeException(\"pytra break outside loop\")"]

    if kind == "Continue":
        continue_label_any = ctx.get("continue_label")
        continue_label = continue_label_any if isinstance(continue_label_any, str) else ""
        if continue_label != "":
            return [indent + "break(())(using " + continue_label + ")"]
        return [indent + "throw new RuntimeException(\"pytra continue outside loop\")"]

    if kind == "Import" or kind == "ImportFrom":
        return []

    if kind == "Raise":
        exc_any = stmt.get("exc")
        if exc_any is None:
            return [indent + "throw new RuntimeException(\"pytra raise\")"]
        return [indent + "throw new RuntimeException(__pytra_str(" + _render_expr(exc_any) + "))"]

    raise RuntimeError("scala native emitter: unsupported stmt kind " + str(kind))


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


def _stmt_contains_yield(stmt: Any) -> bool:
    if not isinstance(stmt, dict):
        return False
    kind = stmt.get("kind")
    if kind == "Yield":
        return True
    body_any = stmt.get("body")
    body = body_any if isinstance(body_any, list) else []
    if _block_contains_yield(body):
        return True
    orelse_any = stmt.get("orelse")
    orelse = orelse_any if isinstance(orelse_any, list) else []
    if _block_contains_yield(orelse):
        return True
    if kind == "Try":
        handlers_any = stmt.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        i = 0
        while i < len(handlers):
            handler = handlers[i]
            if isinstance(handler, dict):
                h_body_any = handler.get("body")
                h_body = h_body_any if isinstance(h_body_any, list) else []
                if _block_contains_yield(h_body):
                    return True
            i += 1
        final_any = stmt.get("finalbody")
        finalbody = final_any if isinstance(final_any, list) else []
        if _block_contains_yield(finalbody):
            return True
    return False


def _block_contains_yield(body: list[Any]) -> bool:
    i = 0
    while i < len(body):
        if _stmt_contains_yield(body[i]):
            return True
        i += 1
    return False


def _emit_function(fn: dict[str, Any], *, indent: str, in_class: bool, is_override: bool = False) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    is_init = in_class and name == "__init__"

    return_type = _scala_type(fn.get("return_type"), allow_void=True)
    if is_init:
        return_type = "Unit"

    params = _function_params(fn, drop_self=in_class)

    lines: list[str] = []
    if is_init:
        if len(params) == 0:
            lines.append(indent + "def __init__(): Unit = {")
        else:
            lines.append(indent + "def this(" + ", ".join(params) + ") = {")
            lines.append(indent + "    this()")
    else:
        override_prefix = "override " if in_class and is_override else ""
        sig = indent + override_prefix + "def " + name + "(" + ", ".join(params) + "): " + return_type + " = {"
        lines.append(sig)

    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    is_generator = (not is_init) and _block_contains_yield(body)

    ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}, "return_type": return_type}
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    if is_generator:
        yield_buffer = _fresh_tmp(ctx, "yielded")
        ctx["yield_buffer"] = yield_buffer
        lines.append(indent + "    val " + yield_buffer + " = mutable.ArrayBuffer[Any]()")

    param_names = _function_param_names(fn, drop_self=in_class)
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    i = 0
    while i < len(param_names):
        p = param_names[i]
        declared.add(p)
        type_map[p] = _scala_type(arg_types.get(p), allow_void=False)
        i += 1

    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1

    if len(body) == 0:
        lines.append(indent + "    // empty body")

    if is_generator:
        yield_buffer_any = ctx.get("yield_buffer")
        yield_buffer = yield_buffer_any if isinstance(yield_buffer_any, str) else ""
        if yield_buffer == "":
            raise RuntimeError("scala native emitter: missing yield buffer")
        lines.append(indent + "    return " + yield_buffer)
    elif not is_init and return_type != "Unit" and not _block_guarantees_return(body):
        lines.append(indent + "    return " + _default_return_expr(return_type))

    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
    extends = " extends " + base_name + "()" if base_name != "" else ""

    lines: list[str] = []
    lines.append(indent + "class " + class_name + "()" + extends + " {")

    field_types_any = cls.get("field_types")
    field_types = field_types_any if isinstance(field_types_any, dict) else {}
    instance_fields: list[tuple[str, str]] = []
    for raw_name, raw_type in field_types.items():
        if not isinstance(raw_name, str):
            continue
        field_name = _safe_ident(raw_name, "field")
        field_type = _scala_type(raw_type, allow_void=False)
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
        lines.append(indent + "    def this(" + ", ".join(ctor_params) + ") = {")
        lines.append(indent + "        this()")
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
            method_name = _safe_ident(node.get("name"), "")
            is_override = method_name != "__init__" and _method_overrides_base(class_name, method_name)
            lines.append("")
            lines.extend(_emit_function(node, indent=indent + "    ", in_class=True, is_override=is_override))
        i += 1

    lines.append(indent + "}")
    return lines


def _emit_runtime_helpers() -> list[str]:
    return [
        "def __pytra_noop(args: Any*): Unit = { }",
        "",
        "def __pytra_to_byte(v: Any): Int = {",
        "    (__pytra_int(v) & 0xFFL).toInt",
        "}",
        "",
        "def __pytra_to_byte_buffer(v: Any): mutable.ArrayBuffer[Byte] = {",
        "    val src = __pytra_as_list(v)",
        "    val out = mutable.ArrayBuffer[Byte]()",
        "    var i = 0",
        "    while (i < src.size) {",
        "        out.append(__pytra_to_byte(src(i)).toByte)",
        "        i += 1",
        "    }",
        "    out",
        "}",
        "",
        "def __pytra_append_u16le(out: mutable.ArrayBuffer[Byte], value: Int): Unit = {",
        "    out.append((value & 0xFF).toByte)",
        "    out.append(((value >>> 8) & 0xFF).toByte)",
        "}",
        "",
        "def __pytra_append_u32be(out: mutable.ArrayBuffer[Byte], value: Int): Unit = {",
        "    out.append(((value >>> 24) & 0xFF).toByte)",
        "    out.append(((value >>> 16) & 0xFF).toByte)",
        "    out.append(((value >>> 8) & 0xFF).toByte)",
        "    out.append((value & 0xFF).toByte)",
        "}",
        "",
        "def __pytra_crc32(data: mutable.ArrayBuffer[Byte]): Int = {",
        "    var crc = 0xFFFFFFFFL",
        "    val poly = 0xEDB88320L",
        "    var i = 0",
        "    while (i < data.size) {",
        "        crc ^= (data(i) & 0xFF).toLong",
        "        var j = 0",
        "        while (j < 8) {",
        "            if ((crc & 1L) != 0L) crc = (crc >>> 1) ^ poly",
        "            else crc = crc >>> 1",
        "            j += 1",
        "        }",
        "        i += 1",
        "    }",
        "    (crc ^ 0xFFFFFFFFL).toInt",
        "}",
        "",
        "def __pytra_adler32(data: mutable.ArrayBuffer[Byte]): Int = {",
        "    val mod = 65521",
        "    var s1 = 1",
        "    var s2 = 0",
        "    var i = 0",
        "    while (i < data.size) {",
        "        s1 += (data(i) & 0xFF)",
        "        if (s1 >= mod) s1 -= mod",
        "        s2 += s1",
        "        s2 %= mod",
        "        i += 1",
        "    }",
        "    ((s2 << 16) | s1) & 0xFFFFFFFF",
        "}",
        "",
        "def __pytra_zlib_deflate_store(data: mutable.ArrayBuffer[Byte]): mutable.ArrayBuffer[Byte] = {",
        "    val out = mutable.ArrayBuffer[Byte](0x78.toByte, 0x01.toByte)",
        "    val n = data.size",
        "    var pos = 0",
        "    while (pos < n) {",
        "        val remain = n - pos",
        "        val chunkLen = if (remain > 65535) 65535 else remain",
        "        val finalFlag = if ((pos + chunkLen) >= n) 1 else 0",
        "        out.append(finalFlag.toByte)",
        "        __pytra_append_u16le(out, chunkLen)",
        "        __pytra_append_u16le(out, 0xFFFF ^ chunkLen)",
        "        var i = 0",
        "        while (i < chunkLen) {",
        "            out.append(data(pos + i))",
        "            i += 1",
        "        }",
        "        pos += chunkLen",
        "    }",
        "    __pytra_append_u32be(out, __pytra_adler32(data))",
        "    out",
        "}",
        "",
        "def __pytra_png_chunk(chunkType: String, data: mutable.ArrayBuffer[Byte]): mutable.ArrayBuffer[Byte] = {",
        "    val out = mutable.ArrayBuffer[Byte]()",
        "    __pytra_append_u32be(out, data.size)",
        "    val ct = chunkType.getBytes(\"US-ASCII\")",
        "    val crcData = mutable.ArrayBuffer[Byte]()",
        "    var i = 0",
        "    while (i < ct.length) {",
        "        out.append(ct(i))",
        "        crcData.append(ct(i))",
        "        i += 1",
        "    }",
        "    i = 0",
        "    while (i < data.size) {",
        "        out.append(data(i))",
        "        crcData.append(data(i))",
        "        i += 1",
        "    }",
        "    __pytra_append_u32be(out, __pytra_crc32(crcData))",
        "    out",
        "}",
        "",
        "def __pytra_write_file_bytes(path: Any, data: mutable.ArrayBuffer[Byte]): Unit = {",
        "    val p = Paths.get(__pytra_str(path))",
        "    val parent = p.getParent",
        "    if (parent != null) Files.createDirectories(parent)",
        "    Files.write(p, data.toArray)",
        "}",
        "",
        "def __pytra_path_new(path: Any): String = {",
        "    Paths.get(__pytra_str(path)).toString",
        "}",
        "",
        "def __pytra_path_join(base: Any, child: Any): String = {",
        "    Paths.get(__pytra_str(base)).resolve(__pytra_str(child)).toString",
        "}",
        "",
        "def __pytra_path_parent(path: Any): String = {",
        "    val parent = Paths.get(__pytra_str(path)).getParent",
        "    if (parent == null) \"\" else parent.toString",
        "}",
        "",
        "def __pytra_path_name(path: Any): String = {",
        "    val name = Paths.get(__pytra_str(path)).getFileName",
        "    if (name == null) \"\" else name.toString",
        "}",
        "",
        "def __pytra_path_stem(path: Any): String = {",
        "    val name = __pytra_path_name(path)",
        "    val idx = name.lastIndexOf('.')",
        "    if (idx <= 0) name else name.substring(0, idx)",
        "}",
        "",
        "def __pytra_path_exists(path: Any): Boolean = {",
        "    Files.exists(Paths.get(__pytra_str(path)))",
        "}",
        "",
        "def __pytra_path_mkdir(path: Any): Unit = {",
        "    Files.createDirectories(Paths.get(__pytra_str(path)))",
        "}",
        "",
        "def __pytra_path_write_text(path: Any, text: Any): Unit = {",
        "    val p = Paths.get(__pytra_str(path))",
        "    val parent = p.getParent",
        "    if (parent != null) Files.createDirectories(parent)",
        "    Files.writeString(p, __pytra_str(text))",
        "}",
        "",
        "def __pytra_path_read_text(path: Any): String = {",
        "    Files.readString(Paths.get(__pytra_str(path)))",
        "}",
        "",
        "def __pytra_grayscale_palette(): mutable.ArrayBuffer[Any] = {",
        "    val p = mutable.ArrayBuffer[Any]()",
        "    var i = 0L",
        "    while (i < 256L) {",
        "        p.append(i)",
        "        p.append(i)",
        "        p.append(i)",
        "        i += 1L",
        "    }",
        "    p",
        "}",
        "",
        "def __pytra_write_rgb_png(path: Any, width: Any, height: Any, pixels: Any): Unit = {",
        "    val w = __pytra_int(width).toInt",
        "    val h = __pytra_int(height).toInt",
        "    val raw = __pytra_to_byte_buffer(pixels)",
        "    val expected = w * h * 3",
        "    if (raw.size != expected) {",
        "        throw new RuntimeException(\"pixels length mismatch\")",
        "    }",
        "    val scanlines = mutable.ArrayBuffer[Byte]()",
        "    val rowBytes = w * 3",
        "    var y = 0",
        "    while (y < h) {",
        "        scanlines.append(0.toByte)",
        "        val start = y * rowBytes",
        "        var x = 0",
        "        while (x < rowBytes) {",
        "            scanlines.append(raw(start + x))",
        "            x += 1",
        "        }",
        "        y += 1",
        "    }",
        "    val ihdr = mutable.ArrayBuffer[Byte]()",
        "    __pytra_append_u32be(ihdr, w)",
        "    __pytra_append_u32be(ihdr, h)",
        "    ihdr.append(8.toByte)",
        "    ihdr.append(2.toByte)",
        "    ihdr.append(0.toByte)",
        "    ihdr.append(0.toByte)",
        "    ihdr.append(0.toByte)",
        "    val idat = __pytra_zlib_deflate_store(scanlines)",
        "    val png = mutable.ArrayBuffer[Byte](0x89.toByte, 'P'.toByte, 'N'.toByte, 'G'.toByte, 0x0D.toByte, 0x0A.toByte, 0x1A.toByte, 0x0A.toByte)",
        "    png ++= __pytra_png_chunk(\"IHDR\", ihdr)",
        "    png ++= __pytra_png_chunk(\"IDAT\", idat)",
        "    png ++= __pytra_png_chunk(\"IEND\", mutable.ArrayBuffer[Byte]())",
        "    __pytra_write_file_bytes(path, png)",
        "}",
        "",
        "def __pytra_gif_lzw_encode(data: mutable.ArrayBuffer[Byte], minCodeSize: Int = 8): mutable.ArrayBuffer[Byte] = {",
        "    if (data.isEmpty) return mutable.ArrayBuffer[Byte]()",
        "    val clearCode = 1 << minCodeSize",
        "    val endCode = clearCode + 1",
        "    var codeSize = minCodeSize + 1",
        "    val out = mutable.ArrayBuffer[Byte]()",
        "    var bitBuffer = 0",
        "    var bitCount = 0",
        "    def writeCode(code: Int): Unit = {",
        "        bitBuffer |= (code << bitCount)",
        "        bitCount += codeSize",
        "        while (bitCount >= 8) {",
        "            out.append((bitBuffer & 0xFF).toByte)",
        "            bitBuffer = bitBuffer >>> 8",
        "            bitCount -= 8",
        "        }",
        "    }",
        "    writeCode(clearCode)",
        "    codeSize = minCodeSize + 1",
        "    var i = 0",
        "    while (i < data.size) {",
        "        val v = data(i) & 0xFF",
        "        writeCode(v)",
        "        writeCode(clearCode)",
        "        codeSize = minCodeSize + 1",
        "        i += 1",
        "    }",
        "    writeCode(endCode)",
        "    if (bitCount > 0) out.append((bitBuffer & 0xFF).toByte)",
        "    out",
        "}",
        "",
        "def __pytra_save_gif(path: Any, width: Any, height: Any, frames: Any, palette: Any, delayCsArg: Any = 4L, loopArg: Any = 0L): Unit = {",
        "    val w = __pytra_int(width).toInt",
        "    val h = __pytra_int(height).toInt",
        "    val delayCs = __pytra_int(delayCsArg).toInt",
        "    val loop = __pytra_int(loopArg).toInt",
        "    val paletteBytes = __pytra_to_byte_buffer(palette)",
        "    if (paletteBytes.size != 256 * 3) {",
        "        throw new RuntimeException(\"palette must be 256*3 bytes\")",
        "    }",
        "    val frameItems = __pytra_as_list(frames)",
        "    val out = mutable.ArrayBuffer[Byte]('G'.toByte, 'I'.toByte, 'F'.toByte, '8'.toByte, '9'.toByte, 'a'.toByte)",
        "    __pytra_append_u16le(out, w)",
        "    __pytra_append_u16le(out, h)",
        "    out.append(0xF7.toByte)",
        "    out.append(0.toByte)",
        "    out.append(0.toByte)",
        "    out ++= paletteBytes",
        "    out.append(0x21.toByte)",
        "    out.append(0xFF.toByte)",
        "    out.append(0x0B.toByte)",
        "    out ++= mutable.ArrayBuffer[Byte]('N'.toByte, 'E'.toByte, 'T'.toByte, 'S'.toByte, 'C'.toByte, 'A'.toByte, 'P'.toByte, 'E'.toByte, '2'.toByte, '.'.toByte, '0'.toByte)",
        "    out.append(0x03.toByte)",
        "    out.append(0x01.toByte)",
        "    __pytra_append_u16le(out, loop)",
        "    out.append(0.toByte)",
        "    var i = 0",
        "    while (i < frameItems.size) {",
        "        val fr = __pytra_to_byte_buffer(frameItems(i))",
        "        if (fr.size != w * h) {",
        "            throw new RuntimeException(\"frame size mismatch\")",
        "        }",
        "        out.append(0x21.toByte)",
        "        out.append(0xF9.toByte)",
        "        out.append(0x04.toByte)",
        "        out.append(0x00.toByte)",
        "        __pytra_append_u16le(out, delayCs)",
        "        out.append(0x00.toByte)",
        "        out.append(0x00.toByte)",
        "        out.append(0x2C.toByte)",
        "        __pytra_append_u16le(out, 0)",
        "        __pytra_append_u16le(out, 0)",
        "        __pytra_append_u16le(out, w)",
        "        __pytra_append_u16le(out, h)",
        "        out.append(0x00.toByte)",
        "        out.append(8.toByte)",
        "        val compressed = __pytra_gif_lzw_encode(fr, 8)",
        "        var pos = 0",
        "        while (pos < compressed.size) {",
        "            val remain = compressed.size - pos",
        "            val chunkLen = if (remain > 255) 255 else remain",
        "            out.append(chunkLen.toByte)",
        "            var j = 0",
        "            while (j < chunkLen) {",
        "                out.append(compressed(pos + j))",
        "                j += 1",
        "            }",
        "            pos += chunkLen",
        "        }",
        "        out.append(0.toByte)",
        "        i += 1",
        "    }",
        "    out.append(0x3B.toByte)",
        "    __pytra_write_file_bytes(path, out)",
        "}",
        "",
        "def __pytra_any_default(): Any = {",
        "    0L",
        "}",
        "",
        "def __pytra_assert(args: Any*): String = {",
        "    \"True\"",
        "}",
        "",
        "def __pytra_perf_counter(): Double = {",
        "    System.nanoTime().toDouble / 1_000_000_000.0",
        "}",
        "",
        "def __pytra_truthy(v: Any): Boolean = {",
        "    if (v == null) return false",
        "    v match {",
        "        case b: Boolean => b",
        "        case l: Long => l != 0L",
        "        case i: Int => i != 0",
        "        case d: Double => d != 0.0",
        "        case f: Float => f != 0.0f",
        "        case s: String => s.nonEmpty",
        "        case xs: scala.collection.Seq[?] => xs.nonEmpty",
        "        case m: scala.collection.Map[?, ?] => m.nonEmpty",
        "        case _ => true",
        "    }",
        "}",
        "",
        "def __pytra_int(v: Any): Long = {",
        "    if (v == null) return 0L",
        "    v match {",
        "        case l: Long => l",
        "        case i: Int => i.toLong",
        "        case d: Double => d.toLong",
        "        case f: Float => f.toLong",
        "        case b: Boolean => if (b) 1L else 0L",
        "        case s: String =>",
        "            try s.toLong",
        "            catch { case _: NumberFormatException => 0L }",
        "        case _ => 0L",
        "    }",
        "}",
        "",
        "def __pytra_float(v: Any): Double = {",
        "    if (v == null) return 0.0",
        "    v match {",
        "        case d: Double => d",
        "        case f: Float => f.toDouble",
        "        case l: Long => l.toDouble",
        "        case i: Int => i.toDouble",
        "        case b: Boolean => if (b) 1.0 else 0.0",
        "        case s: String =>",
        "            try s.toDouble",
        "            catch { case _: NumberFormatException => 0.0 }",
        "        case _ => 0.0",
        "    }",
        "}",
        "",
        "def __pytra_str(v: Any): String = {",
        "    if (v == null) return \"None\"",
        "    v match {",
        "        case b: Boolean => if (b) \"True\" else \"False\"",
        "        case _ => v.toString",
        "    }",
        "}",
        "",
        "def __pytra_len(v: Any): Long = {",
        "    if (v == null) return 0L",
        "    v match {",
        "        case s: String => s.length.toLong",
        "        case xs: scala.collection.Seq[?] => xs.size.toLong",
        "        case m: scala.collection.Map[?, ?] => m.size.toLong",
        "        case _ => 0L",
        "    }",
        "}",
        "",
        "def __pytra_index(i: Long, n: Long): Long = {",
        "    if (i < 0L) i + n else i",
        "}",
        "",
        "def __pytra_get_index(container: Any, index: Any): Any = {",
        "    container match {",
        "        case s: String =>",
        "            if (s.isEmpty) return \"\"",
        "            val i = __pytra_index(__pytra_int(index), s.length.toLong)",
        "            if (i < 0L || i >= s.length.toLong) return \"\"",
        "            s.charAt(i.toInt).toString",
        "        case m: mutable.LinkedHashMap[?, ?] =>",
        "            m.asInstanceOf[mutable.LinkedHashMap[Any, Any]].getOrElse(__pytra_str(index), __pytra_any_default())",
        "        case m: scala.collection.Map[?, ?] =>",
        "            m.asInstanceOf[scala.collection.Map[Any, Any]].getOrElse(__pytra_str(index), __pytra_any_default())",
        "        case _ =>",
            "            val list = __pytra_as_list(container)",
            "            if (list.nonEmpty) {",
                "                val i = __pytra_index(__pytra_int(index), list.size.toLong)",
                "                if (i >= 0L && i < list.size.toLong) return list(i.toInt)",
            "            }",
            "            __pytra_any_default()",
        "    }",
        "}",
        "",
        "def __pytra_set_index(container: Any, index: Any, value: Any): Unit = {",
        "    container match {",
        "        case m: mutable.LinkedHashMap[?, ?] =>",
        "            m.asInstanceOf[mutable.LinkedHashMap[Any, Any]](__pytra_str(index)) = value",
        "            return",
        "        case m: scala.collection.mutable.Map[?, ?] =>",
        "            m.asInstanceOf[scala.collection.mutable.Map[Any, Any]](__pytra_str(index)) = value",
        "            return",
        "        case _ =>",
        "    }",
        "    val list = __pytra_as_list(container)",
        "    if (list.nonEmpty) {",
        "        val i = __pytra_index(__pytra_int(index), list.size.toLong)",
        "        if (i >= 0L && i < list.size.toLong) list(i.toInt) = value",
        "        return",
        "    }",
        "    val map = __pytra_as_dict(container)",
        "    map(__pytra_str(index)) = value",
        "}",
        "",
        "def __pytra_slice(container: Any, lower: Any, upper: Any): Any = {",
        "    container match {",
        "        case s: String =>",
        "            val n = s.length.toLong",
        "            var lo = __pytra_index(__pytra_int(lower), n)",
        "            var hi = __pytra_index(__pytra_int(upper), n)",
        "            if (lo < 0L) lo = 0L",
        "            if (hi < 0L) hi = 0L",
        "            if (lo > n) lo = n",
        "            if (hi > n) hi = n",
        "            if (hi < lo) hi = lo",
        "            s.substring(lo.toInt, hi.toInt)",
        "        case _ =>",
        "            val list = __pytra_as_list(container)",
        "            val n = list.size.toLong",
        "            var lo = __pytra_index(__pytra_int(lower), n)",
        "            var hi = __pytra_index(__pytra_int(upper), n)",
        "            if (lo < 0L) lo = 0L",
        "            if (hi < 0L) hi = 0L",
        "            if (lo > n) lo = n",
        "            if (hi > n) hi = n",
        "            if (hi < lo) hi = lo",
        "            val out = mutable.ArrayBuffer[Any]()",
        "            var i = lo",
        "            while (i < hi) {",
        "                out.append(list(i.toInt))",
        "                i += 1L",
        "            }",
        "            out",
        "    }",
        "}",
        "",
        "def __pytra_isdigit(v: Any): Boolean = {",
        "    val s = __pytra_str(v)",
        "    if (s.isEmpty) return false",
        "    s.forall(_.isDigit)",
        "}",
        "",
        "def __pytra_isalpha(v: Any): Boolean = {",
        "    val s = __pytra_str(v)",
        "    if (s.isEmpty) return false",
        "    s.forall(_.isLetter)",
        "}",
        "",
        "def __pytra_contains(container: Any, value: Any): Boolean = {",
        "    val needle = __pytra_str(value)",
        "    container match {",
        "        case s: String => s.contains(needle)",
        "        case m: scala.collection.Map[?, ?] => m.asInstanceOf[scala.collection.Map[Any, Any]].contains(needle)",
        "        case _ =>",
        "            val list = __pytra_as_list(container)",
        "            var i = 0",
        "            while (i < list.size) {",
        "                if (__pytra_str(list(i)) == needle) return true",
        "                i += 1",
        "            }",
        "            false",
        "    }",
        "}",
        "",
        "def __pytra_ifexp(cond: Boolean, a: Any, b: Any): Any = {",
        "    if (cond) a else b",
        "}",
        "",
        "def __pytra_bytearray(initValue: Any): mutable.ArrayBuffer[Any] = {",
        "    initValue match {",
        "        case n: Long =>",
        "            val out = mutable.ArrayBuffer[Any]()",
        "            var i = 0L",
        "            while (i < n) {",
        "                out.append(0L)",
        "                i += 1L",
        "            }",
        "            out",
        "        case n: Int =>",
        "            val out = mutable.ArrayBuffer[Any]()",
        "            var i = 0",
        "            while (i < n) {",
        "                out.append(0L)",
        "                i += 1",
        "            }",
        "            out",
        "        case _ => __pytra_as_list(initValue).clone()",
        "    }",
        "}",
        "",
        "def __pytra_bytes(v: Any): mutable.ArrayBuffer[Any] = {",
        "    __pytra_as_list(v).clone()",
        "}",
        "",
        "def __pytra_list_repeat(value: Any, count: Any): mutable.ArrayBuffer[Any] = {",
        "    val out = mutable.ArrayBuffer[Any]()",
        "    val n = __pytra_int(count)",
        "    var i = 0L",
        "    while (i < n) {",
        "        out.append(value)",
        "        i += 1L",
        "    }",
        "    out",
        "}",
        "",
        "def __pytra_enumerate(v: Any): mutable.ArrayBuffer[Any] = {",
        "    val items = __pytra_as_list(v)",
        "    val out = mutable.ArrayBuffer[Any]()",
        "    var i = 0L",
        "    while (i < items.size.toLong) {",
        "        out.append(mutable.ArrayBuffer[Any](i, items(i.toInt)))",
        "        i += 1L",
        "    }",
        "    out",
        "}",
        "",
        "def __pytra_as_list(v: Any): mutable.ArrayBuffer[Any] = {",
        "    v match {",
        "        case xs: mutable.ArrayBuffer[?] => xs.asInstanceOf[mutable.ArrayBuffer[Any]]",
        "        case xs: scala.collection.Seq[?] =>",
        "            val out = mutable.ArrayBuffer[Any]()",
        "            for (item <- xs) out.append(item)",
        "            out",
        "        case _ => mutable.ArrayBuffer[Any]()",
        "    }",
        "}",
        "",
        "def __pytra_as_dict(v: Any): mutable.LinkedHashMap[Any, Any] = {",
        "    v match {",
        "        case m: mutable.LinkedHashMap[?, ?] => m.asInstanceOf[mutable.LinkedHashMap[Any, Any]]",
        "        case m: scala.collection.Map[?, ?] =>",
        "            val out = mutable.LinkedHashMap[Any, Any]()",
        "            for ((k, valueAny) <- m) {",
        "                if (k != null) out(k) = valueAny",
        "            }",
        "            out",
        "        case _ => mutable.LinkedHashMap[Any, Any]()",
        "    }",
        "}",
        "",
        "def __pytra_pop_last(v: mutable.ArrayBuffer[Any]): mutable.ArrayBuffer[Any] = {",
        "    if (v.nonEmpty) v.remove(v.size - 1)",
        "    v",
        "}",
        "",
        "def __pytra_print(args: Any*): Unit = {",
        "    if (args.isEmpty) {",
        "        println()",
        "        return",
        "    }",
        "    println(args.map(__pytra_str).mkString(\" \"))",
        "}",
        "",
        "def __pytra_min(a: Any, b: Any): Any = {",
        "    val af = __pytra_float(a)",
        "    val bf = __pytra_float(b)",
        "    if (af < bf) {",
        "        if (__pytra_is_float(a) || __pytra_is_float(b)) return af",
        "        return __pytra_int(a)",
        "    }",
        "    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf",
        "    __pytra_int(b)",
        "}",
        "",
        "def __pytra_max(a: Any, b: Any): Any = {",
        "    val af = __pytra_float(a)",
        "    val bf = __pytra_float(b)",
        "    if (af > bf) {",
        "        if (__pytra_is_float(a) || __pytra_is_float(b)) return af",
        "        return __pytra_int(a)",
        "    }",
        "    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf",
        "    __pytra_int(b)",
        "}",
        "",
        "def __pytra_is_int(v: Any): Boolean = v.isInstanceOf[Long] || v.isInstanceOf[Int]",
        "",
        "def __pytra_is_float(v: Any): Boolean = v.isInstanceOf[Double] || v.isInstanceOf[Float]",
        "",
        "def __pytra_is_bool(v: Any): Boolean = v.isInstanceOf[Boolean]",
        "",
        "def __pytra_is_str(v: Any): Boolean = v.isInstanceOf[String]",
        "",
        "def __pytra_is_list(v: Any): Boolean = v.isInstanceOf[scala.collection.Seq[?]]",
    ]


def _extract_pytra_refs(text: str) -> set[str]:
    out: set[str] = set()
    marker = "__pytra_"
    i = 0
    while True:
        pos = text.find(marker, i)
        if pos < 0:
            break
        j = pos + len(marker)
        while j < len(text):
            ch = text[j]
            if ch.isalnum() or ch == "_":
                j += 1
                continue
            break
        out.add(text[pos:j])
        i = j
    return out


def _runtime_helper_blocks() -> tuple[list[str], dict[str, list[str]]]:
    raw_lines = _emit_runtime_helpers()
    order: list[str] = []
    blocks: dict[str, list[str]] = {}
    current_name = ""
    current_lines: list[str] = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        if line.startswith("def __pytra_"):
            if current_name != "":
                while len(current_lines) > 0 and current_lines[-1] == "":
                    current_lines.pop()
                blocks[current_name] = current_lines
            header = line[4:]
            fn_name = header.split("(", 1)[0].strip()
            current_name = fn_name
            order.append(fn_name)
            current_lines = [line]
        elif current_name != "":
            current_lines.append(line)
        i += 1
    if current_name != "":
        while len(current_lines) > 0 and current_lines[-1] == "":
            current_lines.pop()
        blocks[current_name] = current_lines
    return order, blocks


def _emit_runtime_helpers_minimal(program_lines: list[str]) -> list[str]:
    order, blocks = _runtime_helper_blocks()
    needed: set[str] = set()

    i = 0
    while i < len(program_lines):
        refs = _extract_pytra_refs(program_lines[i])
        for ref in refs:
            if ref in blocks:
                needed.add(ref)
        i += 1

    queue: list[str] = list(needed)
    while len(queue) > 0:
        name = queue.pop()
        block = blocks.get(name)
        if not isinstance(block, list):
            continue
        j = 0
        while j < len(block):
            refs = _extract_pytra_refs(block[j])
            for ref in refs:
                if ref in blocks and ref not in needed:
                    needed.add(ref)
                    queue.append(ref)
            j += 1

    out: list[str] = []
    i = 0
    while i < len(order):
        name = order[i]
        if name in needed:
            block = blocks.get(name)
            if isinstance(block, list):
                out.extend(block)
                out.append("")
        i += 1
    while len(out) > 0 and out[-1] == "":
        out.pop()
    return out


def transpile_to_scala_native(east_doc: dict[str, Any]) -> str:
    """Emit Scala 3 native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("scala native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("scala native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("scala native emitter: Module.body must be list")
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
    global _CLASS_BASES
    _CLASS_BASES = {}
    global _CLASS_METHODS
    _CLASS_METHODS = {}
    i = 0
    while i < len(classes):
        class_node = classes[i]
        class_name = _safe_ident(class_node.get("name"), "PytraClass")
        _CLASS_NAMES.add(class_name)
        base_any = class_node.get("base")
        base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
        _CLASS_BASES[class_name] = base_name
        methods: set[str] = set()
        class_body_any = class_node.get("body")
        class_body = class_body_any if isinstance(class_body_any, list) else []
        j = 0
        while j < len(class_body):
            member = class_body[j]
            if isinstance(member, dict) and member.get("kind") == "FunctionDef":
                method_name = _safe_ident(member.get("name"), "")
                if method_name != "":
                    methods.add(method_name)
            j += 1
        _CLASS_METHODS[class_name] = methods
        i += 1
    i = 0
    while i < len(functions):
        _FUNCTION_NAMES.add(_safe_ident(functions[i].get("name"), "func"))
        i += 1

    lines: list[str] = []
    lines.append("// Auto-generated Pytra Scala 3 native source from EAST3.")
    lines.append("import scala.collection.mutable")
    lines.append("import scala.util.boundary, boundary.break")
    lines.append("import scala.math.*")
    lines.append("import java.nio.file.{Files, Paths}")
    lines.append("")
    module_comments = _module_leading_comment_lines(east_doc, "// ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    i = 0
    while i < len(classes):
        cname = _safe_ident(classes[i].get("name"), "PytraClass")
        lines.append("")
        lines.append("def __pytra_is_" + cname + "(v: Any): Boolean = {")
        lines.append("    v.isInstanceOf[" + cname + "]")
        lines.append("}")
        lines.append("")
        lines.append("def __pytra_as_" + cname + "(v: Any): " + cname + " = {")
        lines.append("    v match {")
        lines.append("        case obj: " + cname + " => obj")
        lines.append("        case _ => new " + cname + "()")
        lines.append("    }")
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
    lines.append("def main(args: Array[String]): Unit = {")
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
    return "\n".join(lines)
