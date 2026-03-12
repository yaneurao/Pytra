"""EAST3 -> PHP native emitter."""

from __future__ import annotations

from typing import Any

from backends.common.emitter.code_emitter import (
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
    reject_backend_typed_vararg_signatures,
)
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id


_PHP_KEYWORDS = {
    "abstract",
    "and",
    "array",
    "as",
    "break",
    "callable",
    "case",
    "catch",
    "class",
    "clone",
    "const",
    "continue",
    "declare",
    "default",
    "do",
    "echo",
    "else",
    "elseif",
    "empty",
    "enddeclare",
    "endfor",
    "endforeach",
    "endif",
    "endswitch",
    "endwhile",
    "eval",
    "exit",
    "extends",
    "final",
    "finally",
    "fn",
    "for",
    "foreach",
    "function",
    "global",
    "goto",
    "if",
    "implements",
    "include",
    "include_once",
    "instanceof",
    "insteadof",
    "interface",
    "isset",
    "list",
    "match",
    "namespace",
    "new",
    "or",
    "print",
    "private",
    "protected",
    "public",
    "readonly",
    "require",
    "require_once",
    "return",
    "static",
    "switch",
    "throw",
    "trait",
    "try",
    "unset",
    "use",
    "var",
    "while",
    "xor",
    "yield",
}

_CLASS_NAMES: set[str] = set()
_RELATIVE_IMPORT_MODULE_ALIASES: dict[str, str] = {}
_RELATIVE_IMPORT_SYMBOL_ALIASES: dict[str, str] = {}


def _reject_unsupported_relative_import_forms(body_any: Any) -> None:
    if not isinstance(body_any, list):
        return
    i = 0
    while i < len(body_any):
        stmt = body_any[i]
        i += 1
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind")
        if kind != "Import" and kind != "ImportFrom":
            continue
        module_any = stmt.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = stmt.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            continue
        names_any = stmt.get("names")
        names = names_any if isinstance(names_any, list) else []
        j = 0
        while j < len(names):
            ent = names[j]
            if isinstance(ent, dict) and ent.get("name") == "*":
                raise RuntimeError(
                    "php native emitter: unsupported relative import form: wildcard import"
                )
            j += 1
        if kind == "ImportFrom":
            continue
        raise RuntimeError(
            "php native emitter: unsupported relative import form: relative import"
        )


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
    if out in _PHP_KEYWORDS:
        out = out + "_"
    return out


def _safe_var(name: Any, fallback: str) -> str:
    return "$" + _safe_ident(name, fallback)


def _relative_import_module_path(module_id: str) -> str:
    parts = [
        _safe_ident(part, "module")
        for part in module_id.lstrip(".").split(".")
        if part != ""
    ]
    return "_".join(parts)


def _collect_relative_import_module_aliases(body: list[Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    i = 0
    while i < len(body):
        stmt = body[i]
        if not isinstance(stmt, dict) or stmt.get("kind") != "ImportFrom":
            i += 1
            continue
        module_any = stmt.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = stmt.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            i += 1
            continue
        module_path = _relative_import_module_path(module_id)
        if module_path != "":
            i += 1
            continue
        names_any = stmt.get("names")
        names = names_any if isinstance(names_any, list) else []
        j = 0
        while j < len(names):
            ent = names[j]
            if not isinstance(ent, dict):
                j += 1
                continue
            name_any = ent.get("name")
            name = name_any if isinstance(name_any, str) else ""
            if name == "":
                j += 1
                continue
            if name == "*":
                raise RuntimeError(
                    "php native emitter: unsupported relative import form: wildcard import"
                )
            asname_any = ent.get("asname")
            local_name = asname_any if isinstance(asname_any, str) and asname_any != "" else name
            aliases[_safe_ident(local_name, "value")] = _safe_ident(name, "module")
            j += 1
        i += 1
    return aliases


def _collect_relative_import_symbol_aliases(body: list[Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    i = 0
    while i < len(body):
        stmt = body[i]
        if not isinstance(stmt, dict) or stmt.get("kind") != "ImportFrom":
            i += 1
            continue
        module_any = stmt.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = stmt.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            i += 1
            continue
        module_path = _relative_import_module_path(module_id)
        if module_path == "":
            i += 1
            continue
        names_any = stmt.get("names")
        names = names_any if isinstance(names_any, list) else []
        j = 0
        while j < len(names):
            ent = names[j]
            if not isinstance(ent, dict):
                j += 1
                continue
            name_any = ent.get("name")
            name = name_any if isinstance(name_any, str) else ""
            if name == "":
                j += 1
                continue
            if name == "*":
                raise RuntimeError(
                    "php native emitter: unsupported relative import form: wildcard import"
                )
            asname_any = ent.get("asname")
            local_name = asname_any if isinstance(asname_any, str) and asname_any != "" else name
            aliases[_safe_ident(local_name, "value")] = (
                module_path + "_" + _safe_ident(name, "fn")
            )
            j += 1
        i += 1
    return aliases


def _php_string_literal(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace("\"", "\\\"")
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


def _resolved_type_name(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    resolved = node.get("resolved_type")
    if not isinstance(resolved, str):
        return ""
    return resolved


def _type_is_dict(resolved_type: str) -> bool:
    t = resolved_type.replace(" ", "")
    return t.startswith("dict[")


def _type_is_sequence_like(resolved_type: str) -> bool:
    t = resolved_type.replace(" ", "")
    return t.startswith("list[") or t.startswith("tuple[") or t.startswith("set[") or t in {
        "list",
        "tuple",
        "set",
        "bytes",
        "bytearray",
    }


def _type_is_int_like(resolved_type: str) -> bool:
    t = resolved_type.replace(" ", "")
    return t in {"int", "int64", "uint8"}


def _render_membership_expr(container_expr: str, item_expr: str, container_node: Any) -> str:
    container_type = _resolved_type_name(container_node)
    if _type_is_dict(container_type):
        return "array_key_exists(" + item_expr + ", " + container_expr + ")"
    if _type_is_sequence_like(container_type):
        return "in_array(" + item_expr + ", " + container_expr + ", true)"
    if container_type == "str":
        return "(strpos(" + container_expr + ", strval(" + item_expr + ")) !== false)"
    return "__pytra_contains(" + container_expr + ", " + item_expr + ")"


def _call_name(expr: dict[str, Any]) -> str:
    func_any = expr.get("func")
    if not isinstance(func_any, dict):
        return ""
    if func_any.get("kind") != "Name":
        return ""
    name_any = func_any.get("id")
    if isinstance(name_any, str):
        ident = _safe_ident(name_any, "fn")
        mapped = _RELATIVE_IMPORT_SYMBOL_ALIASES.get(ident)
        if isinstance(mapped, str) and mapped != "":
            return mapped
        return name_any
    return ""


def _snake_to_pascal(name: str) -> str:
    parts = name.split("_")
    out: list[str] = []
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if part != "":
            out.append(part[0].upper() + part[1:])
        i += 1
    return "".join(out)


def _resolved_runtime_call(expr: dict[str, Any]) -> tuple[str, str]:
    runtime_call_any = expr.get("runtime_call")
    runtime_call = runtime_call_any if isinstance(runtime_call_any, str) else ""
    if runtime_call != "":
        return runtime_call, "runtime_call"
    resolved_any = expr.get("resolved_runtime_call")
    resolved = resolved_any if isinstance(resolved_any, str) else ""
    if resolved != "":
        return resolved, "resolved_runtime_call"
    return "", ""


def _resolved_runtime_matches_semantic_tag(runtime_call: str, semantic_tag: str) -> bool:
    if not semantic_tag.startswith("stdlib."):
        return True
    tail = semantic_tag.rsplit(".", 1)[-1].strip()
    call = runtime_call.strip()
    if tail == "" or call == "":
        return False
    if call == tail:
        return True
    return call.endswith("." + tail)


def _resolved_runtime_symbol(runtime_call: str, runtime_source: str) -> str:
    call = runtime_call.strip()
    if call == "":
        return ""
    if runtime_source == "resolved_runtime_call" and call.find(".") < 0:
        # resolved_runtime_call が単一シンボルの場合は lower/IR 側で確定済み。
        return call
    dot = call.find(".")
    if dot >= 0:
        module_name = call[:dot].strip()
        symbol_name = call[dot + 1 :].strip()
        if module_name == "" or symbol_name == "":
            return ""
        return "py" + _snake_to_pascal(module_name) + _snake_to_pascal(symbol_name)
    if runtime_source == "runtime_call":
        return "__pytra_" + call
    return "__pytra_" + call


def _runtime_module_id(expr: dict[str, Any]) -> str:
    runtime_module_any = expr.get("runtime_module_id")
    runtime_module = runtime_module_any if isinstance(runtime_module_any, str) else ""
    if runtime_module == "":
        runtime_call, _ = _resolved_runtime_call(expr)
        dot = runtime_call.find(".")
        if dot >= 0:
            runtime_module = runtime_call[:dot].strip()
    return canonical_runtime_module_id(runtime_module)


def _runtime_symbol_name(expr: dict[str, Any]) -> str:
    runtime_symbol_any = expr.get("runtime_symbol")
    if isinstance(runtime_symbol_any, str):
        return runtime_symbol_any.strip()
    runtime_call, _ = _resolved_runtime_call(expr)
    dot = runtime_call.find(".")
    if dot >= 0:
        return runtime_call[dot + 1 :].strip()
    return ""


def _is_math_constant(expr: dict[str, Any]) -> bool:
    if _runtime_module_id(expr) != "pytra.std.math":
        return False
    return _runtime_symbol_name(expr) in {"pi", "e"}


def _render_runtime_args(args: list[Any], keywords_any: Any) -> list[str]:
    keywords = keywords_any if isinstance(keywords_any, list) else []
    rendered: list[str] = []
    i = 0
    while i < len(args):
        rendered.append(_render_expr(args[i]))
        i += 1
    rendered_keywords: list[tuple[str, str]] = []
    i = 0
    while i < len(keywords):
        kw_any = keywords[i]
        if isinstance(kw_any, dict):
            kw_name_any = kw_any.get("arg")
            if isinstance(kw_name_any, str):
                rendered_keywords.append((_safe_ident(kw_name_any, ""), _render_expr(kw_any.get("value"))))
        i += 1
    if len(rendered_keywords) > 1:
        rendered_keywords.sort(key=lambda item: item[0])
    i = 0
    while i < len(rendered_keywords):
        rendered.append(rendered_keywords[i][1])
        i += 1
    return rendered


def _render_call_via_runtime_call(
    runtime_call: str,
    runtime_source: str,
    semantic_tag: str,
    args: list[Any],
    keywords_any: Any,
    expr: dict[str, Any],
) -> str:
    runtime_symbol = _resolved_runtime_symbol(runtime_call, runtime_source)
    if runtime_symbol == "":
        return ""

    rendered_args = _render_runtime_args(args, keywords_any)
    if runtime_source == "runtime_call":
        if semantic_tag.startswith("stdlib.fn."):
            return runtime_symbol + "(" + ", ".join(rendered_args) + ")"
        return ""
    if runtime_source == "resolved_runtime_call":
        if not _resolved_runtime_matches_semantic_tag(runtime_call, semantic_tag):
            return ""

    if runtime_call.find(".") >= 0:
        if _is_math_constant(expr):
            return runtime_symbol + "()"
        rendered_math_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_math_args.append(_render_expr(args[i]))
            i += 1
        return runtime_symbol + "(" + ", ".join(rendered_math_args) + ")"

    if runtime_source == "resolved_runtime_call":
        if len(args) == 0:
            return runtime_call + "()"
        return runtime_symbol + "(" + ", ".join(rendered_args) + ")"
    return ""


def _render_isinstance_check(lhs_expr: str, typ_expr: Any) -> str:
    if not isinstance(typ_expr, dict):
        return "false"
    if typ_expr.get("kind") == "Tuple":
        elems_any = typ_expr.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        checks: list[str] = []
        i = 0
        while i < len(elems):
            checks.append(_render_isinstance_check(lhs_expr, elems[i]))
            i += 1
        if len(checks) == 0:
            return "false"
        return "(" + " || ".join(checks) + ")"
    if typ_expr.get("kind") == "Set":
        elems_any = typ_expr.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        checks: list[str] = []
        i = 0
        while i < len(elems):
            checks.append(_render_isinstance_check(lhs_expr, elems[i]))
            i += 1
        if len(checks) == 0:
            return "false"
        return "(" + " || ".join(checks) + ")"
    if typ_expr.get("kind") != "Name":
        return "false"
    typ_name_any = typ_expr.get("id")
    if not isinstance(typ_name_any, str):
        return "false"
    typ_name = _safe_ident(typ_name_any, "Object")
    if typ_name_any in {"int", "int64"}:
        return "is_int(" + lhs_expr + ")"
    if typ_name_any in {"float", "float64"}:
        return "is_float(" + lhs_expr + ")"
    if typ_name_any == "bool":
        return "is_bool(" + lhs_expr + ")"
    if typ_name_any == "str":
        return "is_string(" + lhs_expr + ")"
    if typ_name_any in {"list", "tuple", "dict", "bytes", "bytearray"}:
        return "is_array(" + lhs_expr + ")"
    return "(" + lhs_expr + " instanceof " + typ_name + ")"


def _render_constant_expr(expr: dict[str, Any]) -> str:
    if "value" not in expr:
        return "null"
    value = expr.get("value")
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _php_string_literal(value)
    return "null"


def _bin_op_symbol(op: Any, *, left: Any, right: Any) -> str:
    if op == "Add":
        left_t = _resolved_type_name(left)
        right_t = _resolved_type_name(right)
        if left_t == "str" or right_t == "str":
            return "."
        return "+"
    if op == "Sub":
        return "-"
    if op == "Mult":
        return "*"
    if op == "Div":
        return "/"
    if op == "Mod":
        return "%"
    if op == "BitAnd":
        return "&"
    if op == "BitOr":
        return "|"
    if op == "BitXor":
        return "^"
    if op == "LShift":
        return "<<"
    if op == "RShift":
        return ">>"
    if op == "FloorDiv":
        return "//"
    return "+"


def _compare_symbol(op: Any) -> str:
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


def _render_name_expr(expr: dict[str, Any]) -> str:
    ident = _safe_ident(expr.get("id"), "value")
    if ident == "self":
        return "$this"
    return "$" + ident


def _render_call_expr(expr: dict[str, Any]) -> str:
    args_any = expr.get("args")
    args = args_any if isinstance(args_any, list) else []
    keywords_any = expr.get("keywords")
    semantic_tag_any = expr.get("semantic_tag")
    semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""

    if semantic_tag == "stdlib.symbol.Path":
        if len(args) == 0:
            return "new Path(\"\")"
        return "new Path(" + _render_expr(args[0]) + ")"

    runtime_call, runtime_source = _resolved_runtime_call(expr)
    if semantic_tag.startswith("stdlib.") and runtime_call == "":
        raise RuntimeError("php native emitter: unresolved stdlib runtime call: " + semantic_tag)
    if runtime_call != "":
        rendered_runtime = _render_call_via_runtime_call(
            runtime_call,
            runtime_source,
            semantic_tag,
            args,
            keywords_any,
            expr,
        )
        if rendered_runtime != "":
            return rendered_runtime
        if semantic_tag.startswith("stdlib.method."):
            runtime_call = ""
            runtime_source = ""
        if semantic_tag.startswith("stdlib.") and not semantic_tag.startswith("stdlib.method."):
            raise RuntimeError(
                "php native emitter: unresolved stdlib runtime mapping: "
                + semantic_tag
                + " ("
                + runtime_call
                + ")"
            )

    callee_name = _call_name(expr)

    if callee_name.startswith("py_assert_"):
        return "true"
    if callee_name == "print":
        rendered: list[str] = []
        i = 0
        while i < len(args):
            rendered.append(_render_expr(args[i]))
            i += 1
        return "__pytra_print(" + ", ".join(rendered) + ")"
    if callee_name == "int":
        if len(args) == 0:
            return "0"
        return "((int)(" + _render_expr(args[0]) + "))"
    if callee_name == "float":
        if len(args) == 0:
            return "0.0"
        return "((float)(" + _render_expr(args[0]) + "))"
    if callee_name == "bool":
        if len(args) == 0:
            return "false"
        return "__pytra_truthy(" + _render_expr(args[0]) + ")"
    if callee_name == "str":
        if len(args) == 0:
            return '""'
        return "strval(" + _render_expr(args[0]) + ")"
    if callee_name == "len":
        if len(args) == 0:
            return "0"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "min":
        rendered: list[str] = []
        i = 0
        while i < len(args):
            rendered.append(_render_expr(args[i]))
            i += 1
        return "min(" + ", ".join(rendered) + ")"
    if callee_name == "max":
        rendered: list[str] = []
        i = 0
        while i < len(args):
            rendered.append(_render_expr(args[i]))
            i += 1
        return "max(" + ", ".join(rendered) + ")"
    if callee_name == "isinstance":
        if len(args) < 2:
            return "false"
        return _render_isinstance_check(_render_expr(args[0]), args[1])
    if callee_name == "RuntimeError":
        if len(args) >= 1:
            return _render_expr(args[0])
        return "\"RuntimeError\""

    ctor_name = _safe_ident(callee_name, "")
    if ctor_name in _CLASS_NAMES:
        rendered_ctor_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_ctor_args.append(_render_expr(args[i]))
            i += 1
        return "new " + ctor_name + "(" + ", ".join(rendered_ctor_args) + ")"

    func_any = expr.get("func")
    if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
        owner_any = func_any.get("value")
        attr_name = _safe_ident(func_any.get("attr"), "call")
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner_ident = _safe_ident(owner_any.get("id"), "value")
            module_alias = _RELATIVE_IMPORT_MODULE_ALIASES.get(owner_ident, "")
            if module_alias != "":
                rendered_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_args.append(_render_expr(args[i]))
                    i += 1
                return module_alias + "_" + attr_name + "(" + ", ".join(rendered_args) + ")"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Call" and _call_name(owner_any) == "super":
            rendered_super_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_super_args.append(_render_expr(args[i]))
                i += 1
            if attr_name == "__init__":
                return "parent::__construct(" + ", ".join(rendered_super_args) + ")"
            return "parent::" + attr_name + "(" + ", ".join(rendered_super_args) + ")"
        owner_expr = _render_expr(owner_any)
        if attr_name == "get":
            if len(args) == 0:
                return "null"
            if len(args) == 1:
                return "(" + owner_expr + "[" + _render_expr(args[0]) + "] ?? null)"
            return "(" + owner_expr + "[" + _render_expr(args[0]) + "] ?? " + _render_expr(args[1]) + ")"
        if attr_name == "pop":
            if len(args) == 0:
                return "array_pop(" + owner_expr + ")"
            return owner_expr + "[" + _render_expr(args[0]) + "]"
        if attr_name == "isdigit" and len(args) == 0:
            return "__pytra_str_isdigit(" + owner_expr + ")"
        if attr_name == "isalpha" and len(args) == 0:
            return "__pytra_str_isalpha(" + owner_expr + ")"
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return owner_expr + "->" + attr_name + "(" + ", ".join(rendered_args) + ")"

    rendered_args: list[str] = []
    i = 0
    while i < len(args):
        rendered_args.append(_render_expr(args[i]))
        i += 1
    return _safe_ident(callee_name, "fn") + "(" + ", ".join(rendered_args) + ")"


def _render_expr(expr: Any) -> str:
    if not isinstance(expr, dict):
        return "null"
    kind = expr.get("kind")
    if kind == "Name":
        return _render_name_expr(expr)
    if kind == "Constant":
        return _render_constant_expr(expr)
    if kind == "UnaryOp":
        op = expr.get("op")
        operand = _render_expr(expr.get("operand"))
        if op == "USub":
            return "(-" + operand + ")"
        if op == "UAdd":
            return "(+" + operand + ")"
        if op == "Invert":
            return "(~" + operand + ")"
        if op == "Not":
            return "(!" + operand + ")"
        return operand
    if kind == "BinOp":
        op = expr.get("op")
        left_any = expr.get("left")
        right_any = expr.get("right")
        left = _render_expr(left_any)
        right = _render_expr(right_any)
        if op == "Mult":
            left_t = _resolved_type_name(left_any)
            right_t = _resolved_type_name(right_any)
            if _type_is_sequence_like(left_t) and _type_is_int_like(right_t):
                return "__pytra_list_repeat(" + left + ", __pytra_int(" + right + "))"
            if _type_is_sequence_like(right_t) and _type_is_int_like(left_t):
                return "__pytra_list_repeat(" + right + ", __pytra_int(" + left + "))"
        if op == "FloorDiv":
            return "intdiv(" + left + ", " + right + ")"
        return "(" + left + " " + _bin_op_symbol(op, left=left_any, right=right_any) + " " + right + ")"
    if kind == "Compare":
        left = _render_expr(expr.get("left"))
        ops_any = expr.get("ops")
        comps_any = expr.get("comparators")
        ops = ops_any if isinstance(ops_any, list) else []
        comps = comps_any if isinstance(comps_any, list) else []
        if len(ops) == 0 or len(comps) == 0:
            return left
        parts: list[str] = []
        cur_left = left
        i = 0
        while i < len(ops) and i < len(comps):
            right = _render_expr(comps[i])
            op_i = ops[i]
            if op_i == "In":
                parts.append("(" + _render_membership_expr(right, cur_left, comps[i]) + ")")
            elif op_i == "NotIn":
                parts.append("(!" + _render_membership_expr(right, cur_left, comps[i]) + ")")
            else:
                parts.append("(" + cur_left + " " + _compare_symbol(op_i) + " " + right + ")")
            cur_left = right
            i += 1
        if len(parts) == 1:
            return parts[0]
        return "(" + " && ".join(parts) + ")"
    if kind == "BoolOp":
        op = expr.get("op")
        values_any = expr.get("values")
        values = values_any if isinstance(values_any, list) else []
        if len(values) == 0:
            return "false"
        rendered: list[str] = []
        i = 0
        while i < len(values):
            rendered.append(_render_expr(values[i]))
            i += 1
        delim = " && " if op == "And" else " || "
        return "(" + delim.join(rendered) + ")"
    if kind == "Call":
        return _render_call_expr(expr)
    if kind == "Attribute":
        value_any = expr.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name":
            owner_ident = _safe_ident(value_any.get("id"), "value")
            module_alias = _RELATIVE_IMPORT_MODULE_ALIASES.get(owner_ident, "")
            if module_alias != "":
                attr = _safe_ident(expr.get("attr"), "field")
                return module_alias + "_" + attr
        attr = _safe_ident(expr.get("attr"), "field")
        semantic_tag_any = expr.get("semantic_tag")
        semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
        runtime_call, runtime_source = _resolved_runtime_call(expr)
        if semantic_tag.startswith("stdlib.") and runtime_call == "":
            raise RuntimeError("php native emitter: unresolved stdlib runtime attribute: " + semantic_tag)
        if runtime_call != "":
            if runtime_call == "path_parent":
                return _render_expr(value_any) + "->parent"
            if runtime_call == "path_name":
                return _render_expr(value_any) + "->name"
            if runtime_call == "path_stem":
                return _render_expr(value_any) + "->stem"
            if runtime_source == "resolved_runtime_call":
                runtime_symbol = _resolved_runtime_symbol(runtime_call, runtime_source)
                if runtime_symbol != "":
                    if _is_math_constant(expr):
                        return runtime_symbol + "()"
                    return runtime_symbol
            if semantic_tag.startswith("stdlib."):
                raise RuntimeError(
                    "php native emitter: unresolved stdlib runtime attribute mapping: "
                    + semantic_tag
                    + " ("
                    + runtime_call
                    + ")"
                )
        return _render_expr(value_any) + "->" + attr
    if kind == "Subscript":
        owner = _render_expr(expr.get("value"))
        owner_type = _resolved_type_name(expr.get("value"))
        index_any = expr.get("slice")
        if isinstance(index_any, dict) and index_any.get("kind") == "Slice":
            lower_any = index_any.get("lower")
            upper_any = index_any.get("upper")
            lower_expr = _render_expr(lower_any) if isinstance(lower_any, dict) else "0"
            upper_expr = _render_expr(upper_any) if isinstance(upper_any, dict) else "__pytra_len(" + owner + ")"
            return "__pytra_str_slice(" + owner + ", " + lower_expr + ", " + upper_expr + ")"
        index = _render_expr(index_any)
        if _type_is_sequence_like(owner_type):
            return owner + "[__pytra_index(" + owner + ", " + index + ")]"
        return owner + "[" + index + "]"
    if kind == "List" or kind == "Tuple":
        elems_any = expr.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        rendered: list[str] = []
        i = 0
        while i < len(elems):
            rendered.append(_render_expr(elems[i]))
            i += 1
        return "[" + ", ".join(rendered) + "]"
    if kind == "Dict":
        pairs: list[str] = []
        entries_any = expr.get("entries")
        entries = entries_any if isinstance(entries_any, list) else []
        if len(entries) > 0:
            i = 0
            while i < len(entries):
                entry = entries[i]
                if isinstance(entry, dict):
                    pairs.append(_render_expr(entry.get("key")) + " => " + _render_expr(entry.get("value")))
                i += 1
        else:
            keys_any = expr.get("keys")
            vals_any = expr.get("values")
            keys = keys_any if isinstance(keys_any, list) else []
            vals = vals_any if isinstance(vals_any, list) else []
            i = 0
            while i < len(keys) and i < len(vals):
                pairs.append(_render_expr(keys[i]) + " => " + _render_expr(vals[i]))
                i += 1
        return "[" + ", ".join(pairs) + "]"
    if kind == "IfExp":
        test = _render_expr(expr.get("test"))
        body = _render_expr(expr.get("body"))
        orelse = _render_expr(expr.get("orelse"))
        return "(" + test + " ? " + body + " : " + orelse + ")"
    if kind == "Unbox" or kind == "Box":
        return _render_expr(expr.get("value"))
    if kind == "ObjLen":
        return "__pytra_len(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjStr":
        return "strval(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjBool":
        return "((bool)(" + _render_expr(expr.get("value")) + "))"
    if kind == "IsInstance":
        lhs = _render_expr(expr.get("value"))
        return _render_isinstance_check(lhs, expr.get("expected_type_id"))
    return "null"


def _target_lhs(target: Any) -> str:
    if not isinstance(target, dict):
        return "$_"
    kind = target.get("kind")
    if kind == "Name":
        return _safe_var(target.get("id"), "tmp")
    if kind == "Attribute":
        value = _render_expr(target.get("value"))
        attr = _safe_ident(target.get("attr"), "field")
        return value + "->" + attr
    if kind == "Subscript":
        owner = _render_expr(target.get("value"))
        index = _render_expr(target.get("slice"))
        owner_type = _resolved_type_name(target.get("value"))
        if _type_is_sequence_like(owner_type):
            return owner + "[__pytra_index(" + owner + ", " + index + ")]"
        return owner + "[" + index + "]"
    return "$_"


def _const_int(node: Any) -> int | None:
    if not isinstance(node, dict):
        return None
    kind = node.get("kind")
    if kind == "Constant":
        value = node.get("value")
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        return None
    if kind == "UnaryOp" and node.get("op") == "USub":
        inner = _const_int(node.get("operand"))
        if inner is None:
            return None
        return -inner
    if kind == "UnaryOp" and node.get("op") == "UAdd":
        return _const_int(node.get("operand"))
    return None


def _next_tmp(ctx: dict[str, Any], prefix: str) -> str:
    seq_any = ctx.get("__tmp_seq")
    seq = seq_any if isinstance(seq_any, int) else 0
    ctx["__tmp_seq"] = seq + 1
    return "$__pytra_" + prefix + "_" + str(seq)


def _emit_listcomp_assign(
    lhs: str,
    value: Any,
    *,
    indent: str,
    ctx: dict[str, Any],
) -> list[str] | None:
    if not isinstance(value, dict) or value.get("kind") != "ListComp":
        return None
    gens_any = value.get("generators")
    gens = gens_any if isinstance(gens_any, list) else []
    if len(gens) != 1 or not isinstance(gens[0], dict):
        return None
    gen = gens[0]
    ifs_any = gen.get("ifs")
    ifs = ifs_any if isinstance(ifs_any, list) else []
    if len(ifs) != 0:
        return None
    target_any = gen.get("target")
    if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
        return None
    iter_any = gen.get("iter")
    if not isinstance(iter_any, dict) or iter_any.get("kind") != "RangeExpr":
        return None

    target_name = _target_lhs(target_any)
    start_expr = _render_expr(iter_any.get("start"))
    stop_expr = _render_expr(iter_any.get("stop"))
    step_node = iter_any.get("step")
    step_expr = _render_expr(step_node)
    step_value = _const_int(step_node)
    loop_var = _next_tmp(ctx, "lc_i")
    step_tmp = _next_tmp(ctx, "lc_step")

    lines: list[str] = [indent + lhs + " = [];"]
    if step_value is not None and step_value != 0:
        if step_value > 0:
            cond = loop_var + " < " + stop_expr
            update = loop_var + " += " + str(step_value)
        else:
            cond = loop_var + " > " + stop_expr
            update = loop_var + " -= " + str(-step_value)
        lines.append(indent + "for (" + loop_var + " = " + start_expr + "; " + cond + "; " + update + ") {")
    else:
        lines.append(indent + step_tmp + " = " + step_expr + ";")
        cond = "(" + step_tmp + " >= 0) ? (" + loop_var + " < " + stop_expr + ") : (" + loop_var + " > " + stop_expr + ")"
        lines.append(indent + "for (" + loop_var + " = " + start_expr + "; " + cond + "; " + loop_var + " += " + step_tmp + ") {")

    lines.append(indent + "    " + target_name + " = " + loop_var + ";")
    lines.append(indent + "    " + lhs + "[] = " + _render_expr(value.get("elt")) + ";")
    lines.append(indent + "}")
    return lines


def _emit_unpack_target_assign(
    target: dict[str, Any],
    source_expr: str,
    *,
    indent: str,
    tmp_seq: list[int],
) -> list[str]:
    kind = target.get("kind")
    if kind != "Tuple" and kind != "List":
        return [indent + _target_lhs(target) + " = " + source_expr + ";"]

    elems_any = target.get("elements")
    elems = elems_any if isinstance(elems_any, list) else []
    lines: list[str] = []
    i = 0
    while i < len(elems):
        elem = elems[i]
        item_expr = source_expr + "[" + str(i) + "]"
        if isinstance(elem, dict) and (elem.get("kind") == "Tuple" or elem.get("kind") == "List"):
            nested_tmp = "$__pytra_unpack_" + str(tmp_seq[0])
            tmp_seq[0] += 1
            lines.append(indent + nested_tmp + " = (" + item_expr + " ?? []);")
            lines.extend(_emit_unpack_target_assign(elem, nested_tmp, indent=indent, tmp_seq=tmp_seq))
        else:
            lines.append(indent + _target_lhs(elem) + " = (" + item_expr + " ?? null);")
        i += 1
    return lines


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict) or not isinstance(target_plan_any, dict):
        raise RuntimeError("php native emitter: unsupported ForCore plan")

    if iter_plan_any.get("kind") == "RuntimeIterForPlan":
        iter_expr_any = iter_plan_any.get("iter_expr")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        lines: list[str] = []

        if isinstance(iter_expr_any, dict) and iter_expr_any.get("kind") == "Call" and _call_name(iter_expr_any) == "enumerate":
            args_any = iter_expr_any.get("args")
            args = args_any if isinstance(args_any, list) else []
            list_expr = _render_expr(args[0]) if len(args) >= 1 else "[]"
            idx_name = "$__i"
            lines.append(indent + "for (" + idx_name + " = 0; " + idx_name + " < count(" + list_expr + "); " + idx_name + " += 1) {")
            if target_plan_any.get("kind") == "TupleTarget":
                elems_any = target_plan_any.get("elements")
                elems = elems_any if isinstance(elems_any, list) else []
                if len(elems) >= 1 and isinstance(elems[0], dict) and elems[0].get("kind") == "NameTarget":
                    lines.append(indent + "    " + _safe_var(elems[0].get("id"), "i") + " = " + idx_name + ";")
                if len(elems) >= 2 and isinstance(elems[1], dict) and elems[1].get("kind") == "NameTarget":
                    lines.append(indent + "    " + _safe_var(elems[1].get("id"), "item") + " = " + list_expr + "[" + idx_name + "];")
            elif target_plan_any.get("kind") == "NameTarget":
                lines.append(indent + "    " + _safe_var(target_plan_any.get("id"), "item") + " = " + list_expr + "[" + idx_name + "];")
            i = 0
            while i < len(body):
                lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
                i += 1
            lines.append(indent + "}")
            return lines

        iter_expr = _render_expr(iter_expr_any)
        if target_plan_any.get("kind") != "NameTarget":
            raise RuntimeError("php native emitter: unsupported RuntimeIter target")
        target_name = _safe_var(target_plan_any.get("id"), "item")
        lines.append(indent + "foreach (" + iter_expr + " as " + target_name + ") {")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines

    if iter_plan_any.get("kind") != "StaticRangeForPlan":
        raise RuntimeError("php native emitter: unsupported ForCore iter_plan")
    if target_plan_any.get("kind") != "NameTarget":
        raise RuntimeError("php native emitter: unsupported ForCore target")

    target_name = _safe_var(target_plan_any.get("id"), "i")
    start_expr = _render_expr(iter_plan_any.get("start"))
    stop_expr = _render_expr(iter_plan_any.get("stop"))
    step_node = iter_plan_any.get("step")
    step_expr = _render_expr(step_node)
    step_value = _const_int(step_node)
    lines: list[str] = []

    if step_value is not None and step_value != 0:
        if step_value > 0:
            cond = target_name + " < " + stop_expr
            update = target_name + " += " + str(step_value)
        else:
            cond = target_name + " > " + stop_expr
            update = target_name + " -= " + str(-step_value)
        lines.append(indent + "for (" + target_name + " = " + start_expr + "; " + cond + "; " + update + ") {")
    else:
        step_tmp = "$__step"
        lines.append(indent + step_tmp + " = " + step_expr + ";")
        cond = "(" + step_tmp + " >= 0) ? (" + target_name + " < " + stop_expr + ") : (" + target_name + " > " + stop_expr + ")"
        lines.append(indent + "for (" + target_name + " = " + start_expr + "; " + cond + "; " + target_name + " += " + step_tmp + ") {")

    body_any = stmt.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1
    lines.append(indent + "}")
    return lines


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    _ = ctx
    if not isinstance(stmt, dict):
        raise RuntimeError("php native emitter: unsupported statement")
    kind = stmt.get("kind")
    if kind == "Return":
        value = stmt.get("value")
        if value is None:
            return [indent + "return;"]
        return [indent + "return " + _render_expr(value) + ";"]
    if kind == "Expr":
        value = stmt.get("value")
        if isinstance(value, dict) and value.get("kind") == "Name":
            name = _safe_ident(value.get("id"), "")
            if name == "continue_":
                return [indent + "continue;"]
            if name == "break_":
                return [indent + "break;"]
        if isinstance(value, dict) and value.get("kind") == "Call":
            func_any = value.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
                attr = _safe_ident(func_any.get("attr"), "")
                args_any = value.get("args")
                args = args_any if isinstance(args_any, list) else []
                if attr == "append" and len(args) == 1:
                    owner = _render_expr(func_any.get("value"))
                    return [indent + owner + "[] = " + _render_expr(args[0]) + ";"]
        return [indent + _render_expr(value) + ";"]
    if kind == "AnnAssign":
        lhs = _target_lhs(stmt.get("target"))
        if stmt.get("value") is None:
            return [indent + lhs + " = null;"]
        listcomp_lines = _emit_listcomp_assign(lhs, stmt.get("value"), indent=indent, ctx=ctx)
        if listcomp_lines is not None:
            return listcomp_lines
        return [indent + lhs + " = " + _render_expr(stmt.get("value")) + ";"]
    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            raise RuntimeError("php native emitter: Assign without target")
        primary_target = targets[0]
        if isinstance(primary_target, dict) and (
            primary_target.get("kind") == "Tuple" or primary_target.get("kind") == "List"
        ):
            tmp_seq = [0]
            unpack_tmp = "$__pytra_unpack_" + str(tmp_seq[0])
            tmp_seq[0] += 1
            lines = [indent + unpack_tmp + " = " + _render_expr(stmt.get("value")) + ";"]
            lines.extend(_emit_unpack_target_assign(primary_target, unpack_tmp, indent=indent, tmp_seq=tmp_seq))
            return lines
        lhs = _target_lhs(targets[0])
        listcomp_lines = _emit_listcomp_assign(lhs, stmt.get("value"), indent=indent, ctx=ctx)
        if listcomp_lines is not None:
            return listcomp_lines
        return [indent + lhs + " = " + _render_expr(stmt.get("value")) + ";"]
    if kind == "AugAssign":
        lhs = _target_lhs(stmt.get("target"))
        op = stmt.get("op")
        symbol = _bin_op_symbol(op, left=stmt.get("target"), right=stmt.get("value"))
        return [indent + lhs + " " + symbol + "= " + _render_expr(stmt.get("value")) + ";"]
    if kind == "If":
        test = _render_expr(stmt.get("test"))
        lines: list[str] = [indent + "if (" + test + ") {"]
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
    if kind == "While":
        test = _render_expr(stmt.get("test"))
        lines: list[str] = [indent + "while (" + test + ") {"]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines
    if kind == "ForCore":
        return _emit_for_core(stmt, indent=indent, ctx=ctx)
    if kind == "Break":
        return [indent + "break;"]
    if kind == "Continue":
        return [indent + "continue;"]
    if kind == "Pass":
        return [indent + ";"]
    if kind == "Import" or kind == "ImportFrom":
        return []
    if kind == "Raise":
        exc = stmt.get("exc")
        if exc is None:
            return [indent + 'throw new Exception("pytra raise");']
        return [indent + "throw new Exception(strval(" + _render_expr(exc) + "));"]
    if kind == "Try":
        lines: list[str] = []
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent, ctx=ctx))
            i += 1
        handlers_any = stmt.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        i = 0
        while i < len(handlers):
            h = handlers[i]
            if isinstance(h, dict):
                h_body_any = h.get("body")
                h_body = h_body_any if isinstance(h_body_any, list) else []
                j = 0
                while j < len(h_body):
                    lines.extend(_emit_stmt(h_body[j], indent=indent, ctx=ctx))
                    j += 1
            i += 1
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        i = 0
        while i < len(orelse):
            lines.extend(_emit_stmt(orelse[i], indent=indent, ctx=ctx))
            i += 1
        final_any = stmt.get("finalbody")
        final = final_any if isinstance(final_any, list) else []
        i = 0
        while i < len(final):
            lines.extend(_emit_stmt(final[i], indent=indent, ctx=ctx))
            i += 1
        return lines
    raise RuntimeError("php native emitter: unsupported stmt kind: " + str(kind))


def _function_params(fn: dict[str, Any], *, drop_self: bool) -> str:
    arg_order_any = fn.get("arg_order")
    arg_order = arg_order_any if isinstance(arg_order_any, list) else []
    out: list[str] = []
    i = 0
    while i < len(arg_order):
        arg = arg_order[i]
        if isinstance(arg, str):
            if drop_self and i == 0 and arg == "self":
                i += 1
                continue
            out.append(_safe_var(arg, "arg" + str(i)))
        i += 1
    return ", ".join(out)


def _emit_function(
    fn: dict[str, Any],
    *,
    indent: str,
    in_class: bool = False,
    class_name: str = "",
) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    method_name = "__construct" if in_class and name == "__init__" else name
    params = _function_params(fn, drop_self=in_class)
    prefix = "public function " if in_class else "function "
    lines: list[str] = [indent + prefix + method_name + "(" + params + ") {"]
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    ctx: dict[str, Any] = {}
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1
    _ = class_name
    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    extends = ""
    if isinstance(base_any, str) and base_any != "":
        extends = " extends " + _safe_ident(base_any, "Object")
    lines: list[str] = [indent + "class " + class_name + extends + " {"]

    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []
    dataclass_fields: list[str] = []
    if cls.get("dataclass") is True:
        j = 0
        while j < len(body):
            node = body[j]
            if isinstance(node, dict) and node.get("kind") == "AnnAssign":
                target_any = node.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field = _safe_ident(target_any.get("id"), "field")
                    if field not in dataclass_fields:
                        dataclass_fields.append(field)
            j += 1
    if len(dataclass_fields) > 0:
        j = 0
        while j < len(dataclass_fields):
            lines.append(indent + "    public $" + dataclass_fields[j] + ";")
            j += 1
        lines.append("")

    has_init = False
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            fn_name = _safe_ident(node.get("name"), "")
            if fn_name == "__init__":
                has_init = True
            lines.extend(_emit_function(node, indent=indent + "    ", in_class=True, class_name=class_name))
            lines.append("")
        i += 1
    if len(lines) > 0 and lines[-1] == "":
        lines.pop()
    if not has_init:
        if len(dataclass_fields) > 0:
            params: list[str] = []
            j = 0
            while j < len(dataclass_fields):
                params.append("$" + dataclass_fields[j])
                j += 1
            lines.append(indent + "    public function __construct(" + ", ".join(params) + ") {")
            j = 0
            while j < len(dataclass_fields):
                field = dataclass_fields[j]
                lines.append(indent + "        $this->" + field + " = $" + field + ";")
                j += 1
            lines.append(indent + "    }")
        else:
            lines.append(indent + "    public function __construct() {")
            lines.append(indent + "    }")
    lines.append(indent + "}")
    return lines


def transpile_to_php_native(east_doc: dict[str, Any]) -> str:
    """Emit PHP native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("php native emitter: east_doc must be dict")
    if east_doc.get("kind") != "Module":
        raise RuntimeError("php native emitter: root kind must be Module")
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("php native emitter: Module.body must be list")
    _reject_unsupported_relative_import_forms(body_any)
    reject_backend_typed_vararg_signatures(east_doc, backend_name="PHP backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="PHP backend")
    main_guard_any = east_doc.get("main_guard_body")
    main_guard = main_guard_any if isinstance(main_guard_any, list) else []

    lines: list[str] = [
        "<?php",
        "declare(strict_types=1);",
        "",
        "require_once __DIR__ . '/pytra/py_runtime.php';",
        "",
    ]

    module_comments = _module_leading_comment_lines(east_doc, "// ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    global _CLASS_NAMES
    global _RELATIVE_IMPORT_MODULE_ALIASES
    global _RELATIVE_IMPORT_SYMBOL_ALIASES
    _CLASS_NAMES = set()
    _RELATIVE_IMPORT_MODULE_ALIASES = _collect_relative_import_module_aliases(body_any)
    _RELATIVE_IMPORT_SYMBOL_ALIASES = _collect_relative_import_symbol_aliases(body_any)
    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    i = 0
    while i < len(body_any):
        node = body_any[i]
        if isinstance(node, dict):
            if node.get("kind") == "FunctionDef":
                functions.append(node)
            elif node.get("kind") == "ClassDef":
                classes.append(node)
                _CLASS_NAMES.add(_safe_ident(node.get("name"), "PytraClass"))
        i += 1

    i = 0
    while i < len(classes):
        cls_comments = _leading_comment_lines(classes[i], "// ")
        if len(cls_comments) > 0:
            lines.extend(cls_comments)
        lines.extend(_emit_class(classes[i], indent=""))
        lines.append("")
        i += 1

    i = 0
    while i < len(functions):
        fn_comments = _leading_comment_lines(functions[i], "// ")
        if len(fn_comments) > 0:
            lines.extend(fn_comments)
        lines.extend(_emit_function(functions[i], indent="", in_class=False))
        lines.append("")
        i += 1

    fn_names: set[str] = set()
    i = 0
    while i < len(functions):
        name_any = functions[i].get("name")
        if isinstance(name_any, str):
            fn_names.add(_safe_ident(name_any, "f"))
        i += 1
    class_names: set[str] = set()
    i = 0
    while i < len(classes):
        name_any = classes[i].get("name")
        if isinstance(name_any, str):
            class_names.add(_safe_ident(name_any, "PytraClass"))
        i += 1

    if "__pytra_main" in fn_names and "main" not in fn_names:
        lines.append("function main(): void {")
        lines.append("    __pytra_main();")
        lines.append("}")
        lines.append("")
        fn_names.add("main")

    entry_name = "__pytra_main"
    if entry_name in fn_names or entry_name in class_names:
        entry_name = "__pytra_entry_main"
    while entry_name in fn_names or entry_name in class_names:
        entry_name = entry_name + "_"

    lines.append("function " + entry_name + "(): void {")
    ctx: dict[str, Any] = {}
    i = 0
    while i < len(main_guard):
        lines.extend(_emit_stmt(main_guard[i], indent="    ", ctx=ctx))
        i += 1
    lines.append("}")
    lines.append("")
    lines.append(entry_name + "();")
    lines.append("")
    return "\n".join(lines)
