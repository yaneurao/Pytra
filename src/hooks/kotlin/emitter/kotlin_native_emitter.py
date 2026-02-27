"""EAST3 -> Kotlin native emitter (skeleton stage)."""

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


def _emit_function(
    fn: dict[str, Any],
    *,
    indent: str,
    in_class: bool,
) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    return_type = _kotlin_type(fn.get("return_type"), allow_void=True)
    is_init = in_class and name == "__init__"

    params = _function_params(fn, drop_self=in_class)
    lines: list[str] = []
    if is_init:
        lines.append(indent + "constructor(" + ", ".join(params) + ") {")
        lines.append(indent + "    // TODO: constructor body lowering (native Kotlin)")
        lines.append(indent + "}")
        return lines

    sig = indent + "fun " + name + "(" + ", ".join(params) + ")"
    if return_type != "Unit":
        sig += ": " + return_type
    lines.append(sig + " {")
    lines.append(indent + "    // TODO: function body lowering (native Kotlin)")
    if return_type != "Unit":
        lines.append(indent + "    return " + _default_return_expr(return_type))
    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
    extends = " : " + base_name + "()" if base_name != "" else ""
    lines: list[str] = [indent + "open class " + class_name + extends + " {"]

    field_types_any = cls.get("field_types")
    field_types = field_types_any if isinstance(field_types_any, dict) else {}
    for raw_name, raw_type in field_types.items():
        if not isinstance(raw_name, str):
            continue
        field_name = _safe_ident(raw_name, "field")
        field_type = _kotlin_type(raw_type, allow_void=False)
        default = _default_return_expr(field_type)
        if default == "":
            default = "0L"
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
            lines.extend(_emit_function(node, indent=indent + "    ", in_class=True))
        i += 1

    if not has_init:
        if len(body) > 0:
            lines.append("")
        lines.append(indent + "    constructor()")

    lines.append(indent + "}")
    return lines


def transpile_to_kotlin_native(east_doc: dict[str, Any]) -> str:
    """Emit Kotlin native source from EAST3 Module (skeleton stage)."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("kotlin native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("kotlin native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("kotlin native emitter: Module.body must be list")

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

    lines: list[str] = []
    lines.append("// Auto-generated Pytra Kotlin native source from EAST3.")
    lines.append("import kotlin.system.exitProcess")
    lines.append("")
    lines.append("fun __pytra_noop(vararg args: Any?) { }")
    lines.append("fun __pytra_assert(vararg args: Any?): String = \"True\"")
    lines.append("fun __pytra_perf_counter(): Double = System.nanoTime().toDouble() / 1_000_000_000.0")

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
    lines.append("fun main(args: Array<String>) {")
    has_case_main = False
    i = 0
    while i < len(functions):
        if _safe_ident(functions[i].get("name"), "") == "_case_main":
            has_case_main = True
            break
        i += 1
    if has_case_main:
        lines.append("    _case_main()")
    else:
        lines.append("    // TODO: lower main_guard_body")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)
