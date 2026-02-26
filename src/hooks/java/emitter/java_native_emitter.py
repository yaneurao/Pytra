"""EAST3 -> Java native emitter skeleton.

S1 scope:
- accept EAST3 Module document
- emit executable Java scaffold for module/function/class frames
- keep function/method bodies as conservative placeholders
"""

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


def _function_params(fn: dict[str, Any], *, drop_self: bool) -> list[str]:
    arg_order_any = fn.get("arg_order")
    arg_types_any = fn.get("arg_types")
    arg_order = arg_order_any if isinstance(arg_order_any, list) else []
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    out: list[str] = []
    i = 0
    while i < len(arg_order):
        raw = arg_order[i]
        if isinstance(raw, str):
            if drop_self and i == 0 and raw == "self":
                i += 1
                continue
            param_name = _safe_ident(raw, "arg" + str(i))
            param_type = _java_type(arg_types.get(raw), allow_void=False)
            out.append(param_type + " " + param_name)
        i += 1
    return out


def _emit_function(fn: dict[str, Any], *, indent: str, in_class: bool) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    return_type = _java_type(fn.get("return_type"), allow_void=True)
    static_prefix = "public static " if not in_class else "public "
    params = _function_params(fn, drop_self=in_class)
    lines: list[str] = []
    lines.append(indent + static_prefix + return_type + " " + name + "(" + ", ".join(params) + ") {")
    lines.append(indent + "    // TODO(P3-JAVA-NATIVE-01-S2): lower function body from EAST3 statements.")
    default_expr = _default_return_expr(return_type)
    if return_type != "void":
        lines.append(indent + "    return " + default_expr + ";")
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
    """Emit Java native skeleton from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("java native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("java native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("java native emitter: Module.body must be list")

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
    lines.append("// Auto-generated Java native skeleton from EAST3.")
    lines.append("// NOTE: Function/method body lowering is completed in P3-JAVA-NATIVE-01-S2.")
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

