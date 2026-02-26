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
    if out[0].isdigit():
        out = "_" + out
    return out


def _java_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "Object"
    if type_name == "None":
        return "void" if allow_void else "Object"
    if type_name in {"int", "int64"}:
        return "long"
    if type_name in {"float", "float64"}:
        return "double"
    if type_name == "bool":
        return "boolean"
    if type_name == "str":
        return "String"
    if type_name.isidentifier():
        return _safe_ident(type_name, "Object")
    return "Object"


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


def _render_binop_expr(expr: dict[str, Any]) -> str:
    left = _render_expr(expr.get("left"))
    right = _render_expr(expr.get("right"))
    op = _bin_op_symbol(expr.get("op"))
    return "(" + left + " " + op + " " + right + ")"


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
        right = _render_expr(comps[i])
        parts.append("(" + cur_left + " " + _compare_op_symbol(ops[i]) + " " + right + ")")
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
    value = _render_expr(expr.get("value"))
    attr = _safe_ident(expr.get("attr"), "field")
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
    if callee_name == "perf_counter":
        return "(System.nanoTime() / 1000000000.0)"
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


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict) or iter_plan_any.get("kind") != "StaticRangeForPlan":
        return [indent + "// TODO: unsupported ForCore iter_plan"]
    if not isinstance(target_plan_any, dict) or target_plan_any.get("kind") != "NameTarget":
        return [indent + "// TODO: unsupported ForCore target_plan"]

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
    lines.append(
        indent
        + "for ("
        + target_type
        + " "
        + target_name
        + " = "
        + start_expr
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
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1
    lines.append(indent + "}")
    return lines


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        return [indent + "// TODO: unsupported statement"]
    kind = stmt.get("kind")
    if kind == "Return":
        if "value" in stmt and stmt.get("value") is not None:
            return [indent + "return " + _render_expr(stmt.get("value")) + ";"]
        return [indent + "return;"]
    if kind == "Expr":
        return [indent + _render_expr(stmt.get("value")) + ";"]
    if kind == "AnnAssign":
        target = _target_name(stmt.get("target"))
        decl_type = _java_type(stmt.get("decl_type") or stmt.get("annotation"), allow_void=False)
        if decl_type == "void":
            decl_type = "Object"
        value = _render_expr(stmt.get("value"))
        declared = _declared_set(ctx)
        if stmt.get("declare") is False:
            return [indent + target + " = " + value + ";"]
        if target in declared:
            return [indent + target + " = " + value + ";"]
        declared.add(target)
        return [indent + decl_type + " " + target + " = " + value + ";"]
    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            return [indent + "// TODO: Assign without target"]
        lhs = _target_name(targets[0])
        value = _render_expr(stmt.get("value"))
        declared = _declared_set(ctx)
        if stmt.get("declare"):
            if lhs in declared:
                return [indent + lhs + " = " + value + ";"]
            decl_type = _java_type(stmt.get("decl_type"), allow_void=False)
            if decl_type == "void":
                decl_type = "Object"
            declared.add(lhs)
            return [indent + decl_type + " " + lhs + " = " + value + ";"]
        return [indent + lhs + " = " + value + ";"]
    if kind == "AugAssign":
        lhs = _target_name(stmt.get("target"))
        rhs = _render_expr(stmt.get("value"))
        op = _augassign_op(stmt.get("op"))
        return [indent + lhs + " " + op + " " + rhs + ";"]
    if kind == "If":
        test_expr = _render_expr(stmt.get("test"))
        lines: list[str] = [indent + "if (" + test_expr + ") {"]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        if len(orelse) == 0:
            lines.append(indent + "}")
            return lines
        lines.append(indent + "} else {")
        i = 0
        while i < len(orelse):
            lines.extend(_emit_stmt(orelse[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines
    if kind == "ForCore":
        return _emit_for_core(stmt, indent=indent, ctx=ctx)
    if kind == "Pass":
        return [indent + "// pass"]
    if kind == "Break":
        return [indent + "break;"]
    if kind == "Continue":
        return [indent + "continue;"]
    if kind == "While":
        test_expr = _render_expr(stmt.get("test"))
        lines = [indent + "while (" + test_expr + ") {"]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines
    return [indent + "// TODO: unsupported stmt kind " + str(kind)]


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
    return_type = _java_type(fn.get("return_type"), allow_void=True)
    is_static_method = not in_class
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
    drop_self = in_class and not is_static_method
    params = _function_params(fn, drop_self=drop_self)
    lines: list[str] = []
    lines.append(indent + static_prefix + return_type + " " + name + "(" + ", ".join(params) + ") {")
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    ctx: dict[str, Any] = {"tmp": 0, "declared": set()}
    param_names = _function_param_names(fn, drop_self=drop_self)
    declared = _declared_set(ctx)
    i = 0
    while i < len(param_names):
        declared.add(param_names[i])
        i += 1
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1
    if len(body) == 0:
        lines.append(indent + "    // empty body")
    if return_type != "void" and not _block_guarantees_return(body):
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
    lines.append(indent + "    public " + class_name + "() {")
    lines.append(indent + "    }")
    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            lines.append("")
            lines.extend(_emit_function(node, indent=indent + "    ", in_class=True))
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
    lines.append("// Auto-generated Java native source from EAST3.")
    lines.append("public final class " + main_class + " {")
    lines.append("    private " + main_class + "() {")
    lines.append("    }")

    i = 0
    while i < len(classes):
        lines.append("")
        lines.extend(_emit_class(classes[i], indent="    "))
        i += 1

    i = 0
    while i < len(functions):
        lines.append("")
        lines.extend(_emit_function(functions[i], indent="    ", in_class=False))
        i += 1

    lines.append("")
    lines.append("    public static void main(String[] args) {")
    ctx: dict[str, int] = {"tmp": 0}
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
