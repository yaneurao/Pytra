"""EAST3 -> Ruby native emitter (minimal skeleton)."""

from __future__ import annotations

from pytra.std.typing import Any


_RUBY_KEYWORDS = {
    "BEGIN",
    "END",
    "alias",
    "and",
    "begin",
    "break",
    "case",
    "class",
    "def",
    "defined?",
    "do",
    "else",
    "elsif",
    "end",
    "ensure",
    "false",
    "for",
    "if",
    "in",
    "module",
    "next",
    "nil",
    "not",
    "or",
    "redo",
    "rescue",
    "retry",
    "return",
    "self",
    "super",
    "then",
    "true",
    "undef",
    "unless",
    "until",
    "when",
    "while",
    "yield",
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
    if out in _RUBY_KEYWORDS:
        out = out + "_"
    return out


def _ruby_string_literal(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\n", "\\n")
    return '"' + out + '"'


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


def _cmp_symbol(op: Any) -> str:
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


def _call_name(expr: dict[str, Any]) -> str:
    func_any = expr.get("func")
    if not isinstance(func_any, dict):
        return ""
    if func_any.get("kind") != "Name":
        return ""
    return _safe_ident(func_any.get("id"), "")


def _render_constant_expr(expr: dict[str, Any]) -> str:
    if "value" not in expr:
        return "nil"
    value = expr.get("value")
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _ruby_string_literal(value)
    return "nil"


def _render_name_expr(expr: dict[str, Any]) -> str:
    ident = _safe_ident(expr.get("id"), "value")
    if ident == "self":
        return "self"
    return ident


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    value = _render_expr(expr.get("value"))
    attr = _safe_ident(expr.get("attr"), "field")
    if isinstance(expr.get("value"), dict) and expr.get("value", {}).get("kind") == "Name":
        owner = _safe_ident(expr.get("value", {}).get("id"), "")
        if owner == "math" and attr == "pi":
            return "Math::PI"
        if owner == "math" and attr == "e":
            return "Math::E"
    return value + "." + attr


def _render_unary_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    operand = _render_expr(expr.get("operand"))
    if op == "USub":
        return "(-" + operand + ")"
    if op == "UAdd":
        return "(+" + operand + ")"
    if op == "Not":
        return "(!__pytra_truthy(" + operand + "))"
    return operand


def _render_binop_expr(expr: dict[str, Any]) -> str:
    left = _render_expr(expr.get("left"))
    right = _render_expr(expr.get("right"))
    op = expr.get("op")
    if op == "FloorDiv":
        return "(__pytra_int(" + left + ") / __pytra_int(" + right + "))"
    return "(" + left + " " + _bin_op_symbol(op) + " " + right + ")"


def _render_compare_expr(expr: dict[str, Any]) -> str:
    ops_any = expr.get("ops")
    comps_any = expr.get("comparators")
    ops = ops_any if isinstance(ops_any, list) else []
    comps = comps_any if isinstance(comps_any, list) else []
    if len(ops) == 0 or len(comps) == 0:
        return "false"
    left = _render_expr(expr.get("left"))
    right = _render_expr(comps[0])
    symbol = _cmp_symbol(ops[0])
    return "(" + left + " " + symbol + " " + right + ")"


def _render_boolop_expr(expr: dict[str, Any]) -> str:
    values_any = expr.get("values")
    values = values_any if isinstance(values_any, list) else []
    if len(values) == 0:
        return "false"
    rendered: list[str] = []
    i = 0
    while i < len(values):
        rendered.append("__pytra_truthy(" + _render_expr(values[i]) + ")")
        i += 1
    op = expr.get("op")
    delim = " && " if op == "And" else " || "
    return "(" + delim.join(rendered) + ")"


def _render_subscript_expr(expr: dict[str, Any]) -> str:
    owner = _render_expr(expr.get("value"))
    index = _render_expr(expr.get("slice"))
    return "__pytra_get_index(" + owner + ", " + index + ")"


def _render_ifexp_expr(expr: dict[str, Any]) -> str:
    test = _render_expr(expr.get("test"))
    body = _render_expr(expr.get("body"))
    orelse = _render_expr(expr.get("orelse"))
    return "(__pytra_truthy(" + test + ") ? " + body + " : " + orelse + ")"


def _render_list_expr(expr: dict[str, Any]) -> str:
    elems_any = expr.get("elements")
    elems = elems_any if isinstance(elems_any, list) else []
    out: list[str] = []
    i = 0
    while i < len(elems):
        out.append(_render_expr(elems[i]))
        i += 1
    return "[" + ", ".join(out) + "]"


def _render_call_expr(expr: dict[str, Any]) -> str:
    args_any = expr.get("args")
    args = args_any if isinstance(args_any, list) else []
    callee_name = _call_name(expr)

    if callee_name.startswith("py_assert_"):
        rendered: list[str] = []
        i = 0
        while i < len(args):
            rendered.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered) + ")"
    if callee_name == "py_assert_stdout":
        return "true"
    if callee_name == "perf_counter":
        return "__pytra_perf_counter()"
    if callee_name == "int":
        if len(args) == 0:
            return "0"
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
            return "0"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "min":
        if len(args) == 0:
            return "0"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_min(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name == "max":
        if len(args) == 0:
            return "0"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_max(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name in {"save_gif", "write_rgb_png"}:
        rendered_noop: list[str] = []
        i = 0
        while i < len(args):
            rendered_noop.append(_render_expr(args[i]))
            i += 1
        return "__pytra_noop(" + ", ".join(rendered_noop) + ")"
    if callee_name == "grayscale_palette":
        return "[]"
    if callee_name == "print":
        rendered_print: list[str] = []
        i = 0
        while i < len(args):
            rendered_print.append(_render_expr(args[i]))
            i += 1
        return "__pytra_print(" + ", ".join(rendered_print) + ")"
    if callee_name in {"RuntimeError", "ValueError", "TypeError", "Exception", "AssertionError"}:
        if len(args) == 0:
            return '""'
        return _render_expr(args[0])

    func_any = expr.get("func")
    if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
        attr_name = _safe_ident(func_any.get("attr"), "")
        owner_any = func_any.get("value")
        owner = _render_expr(owner_any)
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner_name = _safe_ident(owner_any.get("id"), "")
            if owner_name == "math":
                rendered_math: list[str] = []
                i = 0
                while i < len(args):
                    rendered_math.append("__pytra_float(" + _render_expr(args[i]) + ")")
                    i += 1
                if attr_name == "sqrt":
                    return "Math.sqrt(" + ", ".join(rendered_math) + ")"
                if attr_name == "sin":
                    return "Math.sin(" + ", ".join(rendered_math) + ")"
                if attr_name == "cos":
                    return "Math.cos(" + ", ".join(rendered_math) + ")"
                if attr_name == "tan":
                    return "Math.tan(" + ", ".join(rendered_math) + ")"
                if attr_name == "exp":
                    return "Math.exp(" + ", ".join(rendered_math) + ")"
                if attr_name == "log":
                    return "Math.log(" + ", ".join(rendered_math) + ")"
                if attr_name == "pow" and len(rendered_math) == 2:
                    return "(" + rendered_math[0] + " ** " + rendered_math[1] + ")"
                if attr_name == "floor":
                    return "(" + rendered_math[0] + ").floor"
                if attr_name == "ceil":
                    return "(" + rendered_math[0] + ").ceil"
                if attr_name == "abs":
                    return "(" + rendered_math[0] + ").abs"
        if attr_name == "isdigit" and len(args) == 0:
            return "__pytra_isdigit(" + owner + ")"
        if attr_name == "isalpha" and len(args) == 0:
            return "__pytra_isalpha(" + owner + ")"
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return owner + "." + attr_name + "(" + ", ".join(rendered_args) + ")"

    if callee_name in _CLASS_NAMES:
        rendered_ctor: list[str] = []
        i = 0
        while i < len(args):
            rendered_ctor.append(_render_expr(args[i]))
            i += 1
        return callee_name + ".new(" + ", ".join(rendered_ctor) + ")"

    func = _render_expr(expr.get("func"))
    rendered: list[str] = []
    i = 0
    while i < len(args):
        rendered.append(_render_expr(args[i]))
        i += 1
    return func + "(" + ", ".join(rendered) + ")"


def _render_expr(expr: Any) -> str:
    if not isinstance(expr, dict):
        if expr is None:
            return "nil"
        return str(expr)
    kind = expr.get("kind")
    if kind == "Name":
        return _render_name_expr(expr)
    if kind == "Constant":
        return _render_constant_expr(expr)
    if kind == "Attribute":
        return _render_attribute_expr(expr)
    if kind == "Call":
        return _render_call_expr(expr)
    if kind == "BinOp":
        return _render_binop_expr(expr)
    if kind == "UnaryOp":
        return _render_unary_expr(expr)
    if kind == "Compare":
        return _render_compare_expr(expr)
    if kind == "BoolOp":
        return _render_boolop_expr(expr)
    if kind == "Subscript":
        return _render_subscript_expr(expr)
    if kind == "IfExp":
        return _render_ifexp_expr(expr)
    if kind == "List" or kind == "Tuple":
        return _render_list_expr(expr)
    return "nil"


def _fresh_tmp(ctx: dict[str, Any], prefix: str) -> str:
    idx = ctx.get("tmp", 0)
    if not isinstance(idx, int):
        idx = 0
    ctx["tmp"] = idx + 1
    return "__" + prefix + "_" + str(idx)


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        return [indent + "# TODO: unsupported ForCore iter_plan"]
    if not isinstance(target_plan_any, dict):
        return [indent + "# TODO: unsupported ForCore target_plan"]

    lines: list[str] = []
    iter_kind = target_plan_any.get("kind")

    if iter_plan_any.get("kind") == "StaticRangeForPlan" and iter_kind == "NameTarget":
        target = _safe_ident(target_plan_any.get("id"), "i")
        if target == "_":
            target = _fresh_tmp(ctx, "loop")
        start = "__pytra_int(" + _render_expr(iter_plan_any.get("start")) + ")"
        stop = "__pytra_int(" + _render_expr(iter_plan_any.get("stop")) + ")"
        step = "__pytra_int(" + _render_expr(iter_plan_any.get("step")) + ")"
        step_tmp = _fresh_tmp(ctx, "step")
        lines.append(indent + step_tmp + " = " + step)
        lines.append(indent + target + " = " + start)
        lines.append(indent + "while ((" + step_tmp + " >= 0 && " + target + " < " + stop + ") || (" + step_tmp + " < 0 && " + target + " > " + stop + "))")
        lines.append(indent + "  ")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "  ", ctx=ctx))
            i += 1
        lines.append(indent + "  " + target + " += " + step_tmp)
        lines.append(indent + "end")
        return lines

    if iter_plan_any.get("kind") == "RuntimeIterForPlan":
        iter_expr = "__pytra_as_list(" + _render_expr(iter_plan_any.get("iter_expr")) + ")"
        if iter_kind == "NameTarget":
            target = _safe_ident(target_plan_any.get("id"), "item")
            if target == "_":
                target = _fresh_tmp(ctx, "item")
            lines.append(indent + "for " + target + " in " + iter_expr)
            body_any = stmt.get("body")
            body = body_any if isinstance(body_any, list) else []
            i = 0
            while i < len(body):
                lines.extend(_emit_stmt(body[i], indent=indent + "  ", ctx=ctx))
                i += 1
            lines.append(indent + "end")
            return lines
        if iter_kind == "TupleTarget":
            iter_tmp = _fresh_tmp(ctx, "iter")
            item_tmp = _fresh_tmp(ctx, "it")
            tuple_tmp = _fresh_tmp(ctx, "tuple")
            lines.append(indent + iter_tmp + " = " + iter_expr)
            lines.append(indent + "for " + item_tmp + " in " + iter_tmp)
            lines.append(indent + "  " + tuple_tmp + " = __pytra_as_list(" + item_tmp + ")")
            elems_any = target_plan_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            i = 0
            while i < len(elems):
                elem = elems[i]
                if isinstance(elem, dict) and elem.get("kind") == "NameTarget":
                    nm = _safe_ident(elem.get("id"), "item_" + str(i))
                    if nm != "_":
                        lines.append(indent + "  " + nm + " = " + tuple_tmp + "[" + str(i) + "]")
                i += 1
            body_any = stmt.get("body")
            body = body_any if isinstance(body_any, list) else []
            i = 0
            while i < len(body):
                lines.extend(_emit_stmt(body[i], indent=indent + "  ", ctx=ctx))
                i += 1
            lines.append(indent + "end")
            return lines

    return [indent + "# TODO: unsupported ForCore plan"]


def _emit_tuple_assign(target_any: Any, value_any: Any, *, indent: str, ctx: dict[str, Any]) -> list[str] | None:
    if not isinstance(target_any, dict) or target_any.get("kind") != "Tuple":
        return None
    elems_any = target_any.get("elements")
    elems = elems_any if isinstance(elems_any, list) else []
    if len(elems) == 0:
        return None
    tuple_tmp = _fresh_tmp(ctx, "tuple")
    lines: list[str] = [indent + tuple_tmp + " = __pytra_as_list(" + _render_expr(value_any) + ")"]
    i = 0
    while i < len(elems):
        elem = elems[i]
        if not isinstance(elem, dict):
            return None
        kind = elem.get("kind")
        rhs = tuple_tmp + "[" + str(i) + "]"
        if kind == "Name":
            nm = _safe_ident(elem.get("id"), "tmp_" + str(i))
            lines.append(indent + nm + " = " + rhs)
        elif kind == "Subscript":
            owner = _render_expr(elem.get("value"))
            index = _render_expr(elem.get("slice"))
            lines.append(indent + "__pytra_set_index(" + owner + ", " + index + ", " + rhs + ")")
        else:
            return None
        i += 1
    return lines


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        return [indent + "# TODO: unsupported statement"]
    kind = stmt.get("kind")

    if kind == "Return":
        if "value" in stmt and stmt.get("value") is not None:
            return [indent + "return " + _render_expr(stmt.get("value"))]
        return [indent + "return nil"]

    if kind == "Expr":
        value_any = stmt.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name":
            raw = value_any.get("id")
            if raw == "break":
                return [indent + "break"]
            if raw == "continue":
                return [indent + "next"]
        return [indent + _render_expr(value_any)]

    if kind == "AnnAssign":
        target_any = stmt.get("target")
        tuple_lines = _emit_tuple_assign(target_any, stmt.get("value"), indent=indent, ctx=ctx)
        if tuple_lines is not None:
            return tuple_lines
        target = _render_expr(target_any)
        value_any = stmt.get("value")
        value = "nil" if value_any is None else _render_expr(value_any)
        return [indent + target + " = " + value]

    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            return [indent + "# TODO: Assign without target"]
        tuple_lines = _emit_tuple_assign(targets[0], stmt.get("value"), indent=indent, ctx=ctx)
        if tuple_lines is not None:
            return tuple_lines
        if isinstance(targets[0], dict) and targets[0].get("kind") == "Subscript":
            owner = _render_expr(targets[0].get("value"))
            index = _render_expr(targets[0].get("slice"))
            value = _render_expr(stmt.get("value"))
            return [indent + "__pytra_set_index(" + owner + ", " + index + ", " + value + ")"]
        target = _render_expr(targets[0])
        value = _render_expr(stmt.get("value"))
        return [indent + target + " = " + value]

    if kind == "AugAssign":
        lhs = _render_expr(stmt.get("target"))
        rhs = _render_expr(stmt.get("value"))
        op = stmt.get("op")
        symbol = _bin_op_symbol(op)
        return [indent + lhs + " " + symbol + "= " + rhs]

    if kind == "If":
        test_expr = "__pytra_truthy(" + _render_expr(stmt.get("test")) + ")"
        lines = [indent + "if " + test_expr]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "  ", ctx=ctx))
            i += 1
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        if len(orelse) > 0:
            lines.append(indent + "else")
            i = 0
            while i < len(orelse):
                lines.extend(_emit_stmt(orelse[i], indent=indent + "  ", ctx=ctx))
                i += 1
        lines.append(indent + "end")
        return lines

    if kind == "ForCore":
        return _emit_for_core(stmt, indent=indent, ctx=ctx)

    if kind == "While":
        test_expr = "__pytra_truthy(" + _render_expr(stmt.get("test")) + ")"
        lines = [indent + "while " + test_expr]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "  ", ctx=ctx))
            i += 1
        lines.append(indent + "end")
        return lines

    if kind == "Pass":
        return [indent + "# pass"]

    if kind == "Break":
        return [indent + "break"]

    if kind == "Continue":
        return [indent + "next"]

    if kind == "Import" or kind == "ImportFrom":
        return []

    if kind == "Raise":
        exc_any = stmt.get("exc")
        if exc_any is None:
            return [indent + "raise RuntimeError, \"pytra raise\""]
        return [indent + "raise RuntimeError, __pytra_str(" + _render_expr(exc_any) + ")"]

    return [indent + "# TODO: unsupported stmt kind " + str(kind)]


def _function_params(fn: dict[str, Any], *, drop_self: bool) -> list[str]:
    out: list[str] = []
    order_any = fn.get("arg_order")
    order = order_any if isinstance(order_any, list) else []
    i = 0
    while i < len(order):
        raw = order[i]
        if isinstance(raw, str):
            name = _safe_ident(raw, "arg" + str(i))
            if drop_self and i == 0 and name == "self":
                i += 1
                continue
            out.append(name)
        i += 1
    return out


def _emit_function(fn: dict[str, Any], *, indent: str, in_class: bool) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    if in_class and name == "__init__":
        name = "initialize"
    params = _function_params(fn, drop_self=in_class)
    lines: list[str] = [indent + "def " + name + "(" + ", ".join(params) + ")"]
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    ctx: dict[str, Any] = {"tmp": 0}
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "  ", ctx=ctx))
        i += 1
    if len(body) == 0:
        lines.append(indent + "  nil")
    lines.append(indent + "end")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
    head = indent + "class " + class_name
    if base_name != "":
        head += " < " + base_name
    lines: list[str] = [head]
    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            lines.append("")
            lines.extend(_emit_function(node, indent=indent + "  ", in_class=True))
        i += 1
    lines.append(indent + "end")
    return lines


def _emit_runtime_helpers() -> list[str]:
    return [
        "def __pytra_noop(*args)",
        "  nil",
        "end",
        "",
        "def __pytra_assert(*args)",
        '  "True"',
        "end",
        "",
        "def __pytra_perf_counter",
        "  Process.clock_gettime(Process::CLOCK_MONOTONIC)",
        "end",
        "",
        "def __pytra_truthy(v)",
        "  return false if v.nil?",
        "  return v if v == true || v == false",
        "  return v != 0 if v.is_a?(Integer)",
        "  return v != 0.0 if v.is_a?(Float)",
        "  return !v.empty? if v.respond_to?(:empty?)",
        "  true",
        "end",
        "",
        "def __pytra_int(v)",
        "  return 0 if v.nil?",
        "  return v.to_i",
        "end",
        "",
        "def __pytra_float(v)",
        "  return 0.0 if v.nil?",
        "  return v.to_f",
        "end",
        "",
        "def __pytra_str(v)",
        '  return "" if v.nil?',
        "  v.to_s",
        "end",
        "",
        "def __pytra_len(v)",
        "  return 0 if v.nil?",
        "  return v.length if v.respond_to?(:length)",
        "  0",
        "end",
        "",
        "def __pytra_as_list(v)",
        "  return v if v.is_a?(Array)",
        "  []",
        "end",
        "",
        "def __pytra_get_index(container, index)",
        "  if container.is_a?(Array)",
        "    i = __pytra_int(index)",
        "    i += container.length if i < 0",
        "    return nil if i < 0 || i >= container.length",
        "    return container[i]",
        "  end",
        "  if container.is_a?(Hash)",
        "    return container[index]",
        "  end",
        "  if container.is_a?(String)",
        "    i = __pytra_int(index)",
        "    i += container.length if i < 0",
        "    return \"\" if i < 0 || i >= container.length",
        "    return container[i] || \"\"",
        "  end",
        "  nil",
        "end",
        "",
        "def __pytra_set_index(container, index, value)",
        "  if container.is_a?(Array)",
        "    i = __pytra_int(index)",
        "    i += container.length if i < 0",
        "    return if i < 0 || i >= container.length",
        "    container[i] = value",
        "    return",
        "  end",
        "  if container.is_a?(Hash)",
        "    container[index] = value",
        "  end",
        "end",
        "",
        "def __pytra_slice(container, lower, upper)",
        "  return nil if container.nil?",
        "  lo = __pytra_int(lower)",
        "  hi = __pytra_int(upper)",
        "  return container[lo...hi]",
        "end",
        "",
        "def __pytra_min(a, b)",
        "  __pytra_float(a) < __pytra_float(b) ? a : b",
        "end",
        "",
        "def __pytra_max(a, b)",
        "  __pytra_float(a) > __pytra_float(b) ? a : b",
        "end",
        "",
        "def __pytra_isdigit(v)",
        "  s = __pytra_str(v)",
        "  return false if s.empty?",
        "  !!(s =~ /\\A[0-9]+\\z/)",
        "end",
        "",
        "def __pytra_isalpha(v)",
        "  s = __pytra_str(v)",
        "  return false if s.empty?",
        "  !!(s =~ /\\A[A-Za-z]+\\z/)",
        "end",
        "",
        "def __pytra_print(*args)",
        "  if args.empty?",
        "    puts",
        "    return",
        "  end",
        "  puts(args.map { |x| __pytra_str(x) }.join(\" \"))",
        "end",
    ]


def transpile_to_ruby_native(east_doc: dict[str, Any]) -> str:
    """Emit Ruby native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("ruby native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("ruby native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("ruby native emitter: Module.body must be list")
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
    lines.append("# Auto-generated Pytra Ruby native source from EAST3.")
    lines.append("")
    lines.extend(_emit_runtime_helpers())

    i = 0
    while i < len(classes):
        lines.append("")
        lines.extend(_emit_class(classes[i], indent=""))
        i += 1

    i = 0
    while i < len(functions):
        lines.append("")
        lines.extend(_emit_function(functions[i], indent="", in_class=False))
        i += 1

    lines.append("")
    lines.append("if __FILE__ == $PROGRAM_NAME")
    ctx: dict[str, Any] = {"tmp": 0}
    if len(main_guard) > 0:
        i = 0
        while i < len(main_guard):
            lines.extend(_emit_stmt(main_guard[i], indent="  ", ctx=ctx))
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
            lines.append("  _case_main()")
    lines.append("end")
    lines.append("")
    return "\n".join(lines)
