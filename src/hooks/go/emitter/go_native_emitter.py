"""EAST3 -> Go native emitter (skeleton stage)."""

from __future__ import annotations

from pytra.std.typing import Any


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


def _go_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "interface{}"
    if type_name == "None":
        return "" if allow_void else "interface{}"
    if type_name in {"int", "int64"}:
        return "int64"
    if type_name in {"float", "float64"}:
        return "float64"
    if type_name == "bool":
        return "bool"
    if type_name == "str":
        return "string"
    if type_name.startswith("list["):
        return "[]interface{}"
    if type_name.startswith("dict["):
        return "map[interface{}]interface{}"
    if type_name in {"bytes", "bytearray"}:
        return "[]byte"
    if type_name.isidentifier():
        return "*" + _safe_ident(type_name, "Any")
    return "interface{}"


def _default_return_expr(go_type: str) -> str:
    if go_type == "int64":
        return "0"
    if go_type == "float64":
        return "0.0"
    if go_type == "bool":
        return "false"
    if go_type == "string":
        return '""'
    if go_type == "[]interface{}":
        return "nil"
    if go_type == "map[interface{}]interface{}":
        return "nil"
    if go_type == "[]byte":
        return "nil"
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


def _emit_function(
    fn: dict[str, Any],
    *,
    indent: str,
    receiver_name: str | None,
) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    if name == "__init__":
        name = "Init"
    return_type = _go_type(fn.get("return_type"), allow_void=True)
    receiver = ""
    drop_self = False
    if isinstance(receiver_name, str):
        recv_var = "self"
        arg_order_any = fn.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        if len(arg_order) > 0 and isinstance(arg_order[0], str):
            recv_var = _safe_ident(arg_order[0], "self")
        receiver = "(" + recv_var + " *" + receiver_name + ") "
        drop_self = True
    params = _function_params(fn, drop_self=drop_self)
    signature = indent + "func " + receiver + name + "(" + ", ".join(params) + ")"
    if return_type != "":
        signature += " " + return_type
    lines: list[str] = [signature + " {"]
    lines.append(indent + "    // TODO: function body lowering (native Go)")
    if return_type != "":
        lines.append(indent + "    return " + _default_return_expr(return_type))
    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    lines: list[str] = []
    lines.append(indent + "type " + class_name + " struct {}")
    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            lines.append("")
            lines.extend(_emit_function(node, indent=indent, receiver_name=class_name))
        i += 1
    return lines


def transpile_to_go_native(east_doc: dict[str, Any]) -> str:
    """Emit Go native source from EAST3 Module (skeleton stage)."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("go native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("go native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("go native emitter: Module.body must be list")

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
    lines.append("// Auto-generated Pytra Go native source from EAST3.")
    lines.append("package main")

    i = 0
    while i < len(classes):
        lines.append("")
        lines.extend(_emit_class(classes[i], indent=""))
        i += 1

    i = 0
    while i < len(functions):
        lines.append("")
        lines.extend(_emit_function(functions[i], indent="", receiver_name=None))
        i += 1

    has_case_main = False
    i = 0
    while i < len(functions):
        if _safe_ident(functions[i].get("name"), "") == "_case_main":
            has_case_main = True
            break
        i += 1

    lines.append("")
    lines.append("func main() {")
    if has_case_main:
        lines.append("    _case_main()")
    else:
        lines.append("    // TODO: lower main_guard_body")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)

