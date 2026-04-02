"""EAST3 -> Swift native emitter (core lowering stage)."""

from __future__ import annotations

from typing import Any

from toolchain.emit.common.emitter.code_emitter import (
    build_import_alias_map,
    collect_reassigned_params,
    mutable_param_name,
    reject_backend_general_union_type_exprs,
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
    reject_backend_typed_vararg_signatures,
)
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id
from toolchain.frontends.runtime_symbol_index import lookup_runtime_module_extern_contract


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

_CLASS_NAMES: list[set[str]] = [set()]
_CLASS_BASES: list[dict[str, str]] = [{}]
_CLASS_METHODS: list[dict[str, set[str]]] = [{}]
_MAIN_CALL_ALIAS: list[str] = [""]
_RELATIVE_IMPORT_NAME_ALIASES: list[dict[str, str]] = [{}]
_THROWING_FUNCTIONS: list[set[str]] = [set()]
_INOUT_PARAM_POSITIONS: list[dict[str, set[int]]] = [{}]


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


def _relative_import_module_path(module_id: str) -> str:
    parts = [
        _safe_ident(part, "module")
        for part in module_id.lstrip(".").split(".")
        if part != ""
    ]
    return ".".join(parts)


def _collect_relative_import_name_aliases(east_doc: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    wildcard_modules: dict[str, str] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        stmt = body[i]
        if not isinstance(stmt, dict):
            i += 1
        sd3: dict[str, Any] = stmt
        if sd3.get("kind") != "ImportFrom":
            i += 1
            continue
        module_any = sd3.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = sd3.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            i += 1
            continue
        module_path = _relative_import_module_path(module_id)
        names_any = sd3.get("names")
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
                wildcard_module = module_path if module_path != "" else _relative_import_module_path(module_id)
                if wildcard_module != "":
                    wildcard_modules[wildcard_module] = wildcard_module
                j += 1
                continue
            asname_any = ent.get("asname")
            local_name = asname_any if isinstance(asname_any, str) and asname_any != "" else name
            local_rendered = _safe_ident(local_name, "value")
            target_name = _safe_ident(name, "value")
            aliases[local_rendered] = (
                target_name if module_path == "" else module_path + "." + target_name
            )
            j += 1
        i += 1
    if len(wildcard_modules) == 0:
        return aliases
    meta_any = east_doc.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    import_symbols_any = meta.get("import_symbols")
    import_symbols = import_symbols_any if isinstance(import_symbols_any, dict) else {}
    wildcard_resolved: dict[str, bool] = {module_id: False for module_id in wildcard_modules}
    for local_name_any, binding_any in import_symbols.items():
        if not isinstance(local_name_any, str) or local_name_any == "":
            continue
        if not isinstance(binding_any, dict):
            continue
        binding_module_any = binding_any.get("module")
        binding_symbol_any = binding_any.get("name")
        binding_module = (
            _relative_import_module_path(binding_module_any)
            if isinstance(binding_module_any, str)
            else ""
        )
        binding_symbol = binding_symbol_any if isinstance(binding_symbol_any, str) else ""
        if binding_module not in wildcard_resolved or binding_symbol == "":
            continue
        local_rendered = _safe_ident(local_name_any, "value")
        target_name = _safe_ident(binding_symbol, "value")
        aliases[local_rendered] = (
            target_name if binding_module == "" else binding_module + "." + target_name
        )
        wildcard_resolved[binding_module] = True
    unresolved = [module_id for module_id, resolved in wildcard_resolved.items() if not resolved]
    if len(unresolved) > 0:
        raise RuntimeError(
            "swift native emitter: unsupported relative import form: wildcard import"
        )
    return aliases


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


def _split_generic_args(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in text:
        if ch == "[" or ch == "<":
            depth += 1
            current.append(ch)
            continue
        if ch == "]" or ch == ">":
            depth -= 1
            current.append(ch)
            continue
        if ch == "," and depth == 0:
            piece = "".join(current).strip()
            if piece != "":
                parts.append(piece)
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _callable_signature_parts(type_name: str) -> tuple[list[str], str] | None:
    if not type_name.startswith("callable[") or not type_name.endswith("]"):
        return None
    inner = type_name[9:-1].strip()
    if not inner.startswith("["):
        return None
    close = inner.find("]")
    if close < 0:
        return None
    args_text = inner[1:close].strip()
    ret_text = inner[close + 1:].lstrip(",").strip()
    args = _split_generic_args(args_text) if args_text != "" else []
    return (args, ret_text)


def _swift_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "Any"
    ts3: str = type_name
    callable_parts = _callable_signature_parts(ts3)
    if callable_parts is not None:
        arg_types, ret_type = callable_parts
        rendered_args = [_swift_type(item, allow_void=False) for item in arg_types]
        rendered_ret = _swift_type(ret_type, allow_void=True)
        return "(" + ", ".join(rendered_args) + ") -> " + rendered_ret
    if type_name == "None":
        return "Void" if allow_void else "Any"
    if type_name in {"int", "int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64", "byte"}:
        return "Int64"
    if type_name in {"float", "float32", "float64"}:
        return "Double"
    if type_name == "bool":
        return "Bool"
    if type_name == "str":
        return "String"
    if ts3 == "deque":
        return "[Any]"
    if ts3.startswith("list[") or ts3.startswith("tuple[") or ts3.startswith("set["):
        return "[Any]"
    if ts3.startswith("dict["):
        return "[AnyHashable: Any]"
    if type_name in {"bytes", "bytearray"}:
        return "[Any]"
    if type_name in {"unknown", "object", "any", "JsonVal"}:
        return "Any"
    if ts3.isidentifier():
        base_type = _CLASS_BASES[0].get(ts3, "")
        if base_type in {"IntEnum", "IntFlag"}:
            return "Int64"
        return _safe_ident(type_name, "Any")
    return "Any"


def _expr_called_function_names(expr: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(expr, dict):
        return out
    kind = expr.get("kind")
    if kind == "Call":
        func_any = expr.get("func")
        if isinstance(func_any, dict) and func_any.get("kind") == "Name":
            name = _safe_ident(func_any.get("id"), "")
            if name != "":
                out.add(name)
        out |= _expr_called_function_names(func_any)
        args_any = expr.get("args")
        args = args_any if isinstance(args_any, list) else []
        i = 0
        while i < len(args):
            out |= _expr_called_function_names(args[i])
            i += 1
        keywords_any = expr.get("keywords")
        keywords = keywords_any if isinstance(keywords_any, list) else []
        i = 0
        while i < len(keywords):
            kw = keywords[i]
            if isinstance(kw, dict):
                out |= _expr_called_function_names(kw.get("value"))
            i += 1
        return out
    for value in expr.values():
        if isinstance(value, dict):
            out |= _expr_called_function_names(value)
        elif isinstance(value, list):
            for item in value:
                out |= _expr_called_function_names(item)
    return out


def _stmt_has_raise_or_try(stmt: Any) -> bool:
    if not isinstance(stmt, dict):
        return False
    kind = stmt.get("kind")
    if kind in {"Raise", "Try"}:
        return True
    for value in stmt.values():
        if isinstance(value, dict) and _stmt_has_raise_or_try(value):
            return True
        if isinstance(value, dict) and _expr_has_subscript(value):
            return True
        if isinstance(value, list):
            for item in value:
                if _stmt_has_raise_or_try(item):
                    return True
                if _expr_has_subscript(item):
                    return True
    return False


def _expr_has_subscript(expr: Any) -> bool:
    if not isinstance(expr, dict):
        return False
    if expr.get("kind") == "Subscript":
        return True
    for value in expr.values():
        if isinstance(value, dict):
            if _expr_has_subscript(value):
                return True
        elif isinstance(value, list):
            i = 0
            while i < len(value):
                if _expr_has_subscript(value[i]):
                    return True
                i += 1
    return False


def _stmt_called_function_names(stmt: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(stmt, dict):
        return out
    for value in stmt.values():
        if isinstance(value, dict):
            out |= _expr_called_function_names(value)
            out |= _stmt_called_function_names(value)
        elif isinstance(value, list):
            for item in value:
                out |= _expr_called_function_names(item)
                out |= _stmt_called_function_names(item)
    return out


def _collect_throwing_functions(east_doc: dict[str, Any]) -> set[str]:
    function_bodies: dict[str, list[Any]] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    for node in body:
        if not isinstance(node, dict):
            continue
        if node.get("kind") == "FunctionDef":
            name = _safe_ident(node.get("name"), "")
            fn_body_any = node.get("body")
            fn_body = fn_body_any if isinstance(fn_body_any, list) else []
            if name != "":
                function_bodies[name] = fn_body
    throwing: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, fn_body in function_bodies.items():
            if name in throwing:
                continue
            direct_throw = False
            called_names: set[str] = set()
            i = 0
            while i < len(fn_body):
                direct_throw = direct_throw or _stmt_has_raise_or_try(fn_body[i])
                called_names |= _stmt_called_function_names(fn_body[i])
                i += 1
            if direct_throw or len(called_names & throwing) > 0:
                throwing.add(name)
                changed = True
    return throwing


def _stmt_mutates_param(stmt: Any, params: set[str]) -> set[str]:
    out: set[str] = set()
    if not isinstance(stmt, dict):
        return out
    kind = stmt.get("kind")
    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        i = 0
        while i < len(targets):
            tgt = targets[i]
            if isinstance(tgt, dict) and tgt.get("kind") == "Subscript":
                owner = tgt.get("value")
                if isinstance(owner, dict) and owner.get("kind") == "Name":
                    owner_id = _safe_ident(owner.get("id"), "")
                    if owner_id in params:
                        out.add(owner_id)
            i += 1
    for value in stmt.values():
        if isinstance(value, dict):
            out |= _stmt_mutates_param(value, params)
        elif isinstance(value, list):
            i = 0
            while i < len(value):
                out |= _stmt_mutates_param(value[i], params)
                i += 1
    return out


def _collect_inout_param_positions(fn: dict[str, Any], *, drop_self: bool) -> set[int]:
    names = _function_param_names(fn, drop_self=drop_self)
    params = set(names)
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    mutated: set[str] = set()
    i = 0
    while i < len(body):
        mutated |= _stmt_mutates_param(body[i], params)
        i += 1
    out: set[int] = set()
    i = 0
    while i < len(names):
        if names[i] in mutated:
            out.add(i)
        i += 1
    return out


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


def _collect_return_value_types(body: list[Any]) -> set[str]:
    out: set[str] = set()
    i = 0
    while i < len(body):
        stmt = body[i]
        if isinstance(stmt, dict):
            kind = stmt.get("kind")
            if kind == "Return":
                value_any = stmt.get("value")
                if isinstance(value_any, dict):
                    inferred = _swift_type(value_any.get("resolved_type"), allow_void=False)
                    if inferred == "Any":
                        inferred = _infer_swift_type(value_any)
                    out.add(inferred)
            for value in stmt.values():
                if isinstance(value, list):
                    out |= _collect_return_value_types(value)
        i += 1
    return out


def _function_return_swift_type(fn: dict[str, Any], *, allow_void: bool) -> str:
    return_type = _swift_type(fn.get("return_type"), allow_void=allow_void)
    if return_type != "Void":
        return return_type
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    inferred = _collect_return_value_types(body)
    inferred.discard("Void")
    if len(inferred) == 1:
        return next(iter(inferred))
    if len(inferred) > 1:
        return "Any"
    return return_type


def _tuple_element_types(type_name: Any) -> list[str]:
    if not isinstance(type_name, str):
        return []
    ts2: str = type_name
    if not ts2.startswith("tuple[") or not ts2.endswith("]"):
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
    nd4: dict[str, Any] = node
    resolved_any = nd4.get("resolved_type")
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
    nd3: dict[str, Any] = node
    if nd3.get("kind") != "Constant":
        return False
    value = nd3.get("value")
    if isinstance(value, bool):
        return False
    return isinstance(value, int) and value == expected


def _is_none_constant(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get("kind") != "Constant":
        return False
    return node.get("value") is None


def _cast_from_any(expr: str, swift_type: str) -> str:
    if swift_type == "Int64":
        return _to_int_expr(expr)
    if swift_type == "Double":
        return _to_float_expr(expr)
    if swift_type == "Bool":
        return _to_truthy_expr(expr)
    if swift_type == "String":
        return _to_str_expr(expr)
    if swift_type == "[Any]":
        return _to_list_expr(expr)
    if swift_type == "[AnyHashable: Any]":
        return _to_dict_expr(expr)
    if swift_type == "Any":
        return expr
    if swift_type in _CLASS_NAMES[0]:
        return "(" + expr + " as? " + swift_type + ") ?? " + swift_type + "()"
    return expr


def _render_binop_as_type(expr: dict[str, Any], swift_type: str) -> str:
    left_node = expr.get("left")
    right_node = expr.get("right")
    left_expr = _render_expr(left_node)
    right_expr = _render_expr(right_node)
    op = expr.get("op")
    sym = _bin_op_symbol(op)
    if swift_type == "Int64":
        return "(" + _int_operand(left_expr, left_node) + " " + sym + " " + _int_operand(right_expr, right_node) + ")"
    if swift_type == "Double":
        return "(" + _float_operand(left_expr, left_node) + " " + sym + " " + _float_operand(right_expr, right_node) + ")"
    return _render_binop_expr(expr)


def _render_name_expr(expr: dict[str, Any]) -> str:
    ident = _safe_ident(expr.get("id"), "value")
    if ident == "main" and _MAIN_CALL_ALIAS[0] != "":
        return _MAIN_CALL_ALIAS[0]
    return _RELATIVE_IMPORT_NAME_ALIASES[0].get(ident, ident)


def _render_format_spec(spec_expr: Any) -> str:
    if isinstance(spec_expr, str):
        return spec_expr
    if not isinstance(spec_expr, dict):
        return ""
    kind = spec_expr.get("kind")
    if kind == "Constant" and isinstance(spec_expr.get("value"), str):
        return spec_expr.get("value")
    if kind == "JoinedStr":
        values_any = spec_expr.get("values")
        values = values_any if isinstance(values_any, list) else []
        parts: list[str] = []
        i = 0
        while i < len(values):
            value_any = values[i]
            if isinstance(value_any, dict) and value_any.get("kind") == "Constant" and isinstance(value_any.get("value"), str):
                parts.append(value_any.get("value"))
            i += 1
        return "".join(parts)
    return ""


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
        return "__pytra_none()"
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
    ed3: dict[str, Any] = expr
    resolved = ed3.get("resolved_type")
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
    kind = ed3.get("kind")
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
    if op == "LShift":
        return "<<"
    if op == "RShift":
        return ">>"
    if op == "BitAnd":
        return "&"
    if op == "BitOr":
        return "|"
    if op == "BitXor":
        return "^"
    return "+"


def _render_unary_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    operand = _render_expr(expr.get("operand"))
    if op == "USub":
        return "(-" + operand + ")"
    if op == "UAdd":
        return "(+" + operand + ")"
    if op == "Invert":
        return "(~" + operand + ")"
    if op == "Not":
        return "(!" + _render_truthy_expr(expr.get("operand")) + ")"
    return operand


def _render_binop_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    if op == "Mult":
        left_any = expr.get("left")
        right_any = expr.get("right")
        if isinstance(left_any, dict) and left_any.get("kind") == "List":
            return "__pytra_list_repeat(" + _render_expr(left_any) + ", " + _render_expr(right_any) + ")"
        if isinstance(right_any, dict) and right_any.get("kind") == "List":
            return "__pytra_list_repeat(" + _render_expr(right_any) + ", " + _render_expr(left_any) + ")"

    left_node = expr.get("left")
    right_node = expr.get("right")
    left_expr = _render_expr(left_node)
    right_expr = _render_expr(right_node)
    resolved = expr.get("resolved_type")

    if op == "Div":
        return "(" + _float_operand(left_expr, left_node) + " / " + _float_operand(right_expr, right_node) + ")"

    if op == "FloorDiv":
        return "(" + _int_operand(left_expr, left_node) + " / " + _int_operand(right_expr, right_node) + ")"

    if op == "Mod":
        return "(" + _int_operand(left_expr, left_node) + " % " + _int_operand(right_expr, right_node) + ")"

    if resolved == "str" and op == "Add":
        return "(" + _to_str_expr(left_expr) + " + " + _to_str_expr(right_expr) + ")"

    if resolved in {"int", "int64", "uint8"}:
        sym = _bin_op_symbol(op)
        return "(" + _int_operand(left_expr, left_node) + " " + sym + " " + _int_operand(right_expr, right_node) + ")"

    if resolved in {"float", "float64"}:
        sym = _bin_op_symbol(op)
        return "(" + _float_operand(left_expr, left_node) + " " + sym + " " + _float_operand(right_expr, right_node) + ")"

    sym = _bin_op_symbol(op)
    return "(" + left_expr + " " + sym + " " + right_expr + ")"


def _compare_op_symbol(op: Any) -> str:
    if op == "Eq":
        return "=="
    if op == "NotEq":
        return "!="
    if op == "Is":
        return "=="
    if op == "IsNot":
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

        left_node = expr.get("left") if i == 0 else comps[i - 1]
        if op in {"Is", "IsNot"} and (_is_none_constant(left_node) or _is_none_constant(comp_node)):
            probe_node = comp_node if _is_none_constant(left_node) else left_node
            probe_type_any = probe_node.get("resolved_type") if isinstance(probe_node, dict) else ""
            probe_type = probe_type_any if isinstance(probe_type_any, str) else ""
            if probe_type.lower().startswith("callable"):
                is_none_expr = "false"
            else:
                probe_expr = _render_expr(probe_node)
                is_none_expr = "__pytra_is_none(" + probe_expr + ")"
            if op == "IsNot":
                is_none_expr = "(!" + is_none_expr + ")"
            parts.append("(" + is_none_expr + ")")
            cur_left = right
            i += 1
            continue

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
            cd: dict[str, Any] = comp_node
            right_any = cd.get("resolved_type")
            right_type = right_any if isinstance(right_any, str) else ""

        symbol = _compare_op_symbol(op)
        if left_type == "str" or right_type == "str":
            lhs = _to_str_expr(cur_left)
            rhs = _to_str_expr(right)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        elif left_type in {"int", "int64", "uint8"} or right_type in {"int", "int64", "uint8"}:
            lhs = _to_int_expr(cur_left)
            rhs = _to_int_expr(right)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        elif left_type in {"float", "float64"} or right_type in {"float", "float64"}:
            lhs = _to_float_expr(cur_left)
            rhs = _to_float_expr(right)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        else:
            if op in {"Eq", "NotEq"}:
                lhs = _to_str_expr(cur_left)
                rhs = _to_str_expr(right)
                parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
            else:
                lhs = _to_float_expr(cur_left)
                rhs = _to_float_expr(right)
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
    resolved = expr.get("resolved_type")
    if resolved == "bool":
        rendered: list[str] = []
        i = 0
        while i < len(values):
            rendered.append(_render_truthy_expr(values[i]))
            i += 1
        delim = " && " if op == "And" else " || "
        return "(" + delim.join(rendered) + ")"
    cur = _render_expr(values[0])
    i = 1
    while i < len(values):
        nxt = _render_expr(values[i])
        tmp = "__boolop_" + str(i)
        if op == "And":
            cur = "({ let " + tmp + " = " + cur + "; return __pytra_truthy(" + tmp + ") ? " + nxt + " : " + tmp + " })()"
        else:
            cur = "({ let " + tmp + " = " + cur + "; return __pytra_truthy(" + tmp + ") ? " + tmp + " : " + nxt + " })()"
        i += 1
    return _cast_from_any(cur, _swift_type(resolved, allow_void=False))


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


def _resolved_runtime_symbol(runtime_call: str, adapter_kind: str = "") -> str:
    """Resolve runtime call to Swift function name.

    Uses runtime_call_adapter_kind (§1) when available,
    falls back to runtime_call string parsing.
    """
    name = runtime_call.strip()
    if name == "":
        return ""
    # §1: use runtime_call_adapter_kind when available
    if adapter_kind == "extern_delegate":
        dot = name.find(".")
        if dot >= 0:
            module_name = name[:dot].strip()
            symbol_name = name[dot + 1 :].strip()
            if module_name != "" and symbol_name != "":
                return module_name + "_native_" + symbol_name
        return ""
    if adapter_kind == "builtin":
        dot = name.find(".")
        bare = name[dot + 1:].strip() if dot >= 0 else name
        return "__pytra_" + bare if bare != "" else ""
    # Fallback: infer from runtime_call string structure
    dot = name.find(".")
    if dot >= 0:
        module_name = name[:dot].strip()
        symbol_name = name[dot + 1 :].strip()
        if module_name == "" or symbol_name == "":
            return ""
        return module_name + "_native_" + symbol_name
    return "__pytra_" + name


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
        rs: str = runtime_symbol_any
        return rs.strip()
    runtime_call, _ = _resolved_runtime_call(expr)
    dot = runtime_call.find(".")
    if dot >= 0:
        return runtime_call[dot + 1 :].strip()
    return ""


_SWIFT_MATH_RUNTIME_SYMBOLS = {
    "pi",
    "e",
    "sin",
    "cos",
    "tan",
    "sqrt",
    "exp",
    "log",
    "log10",
    "fabs",
    "floor",
    "ceil",
    "pow",
}


def _has_runtime_extern_module(expr: dict[str, Any]) -> bool:
    runtime_module_any = expr.get("runtime_module_id")
    runtime_module = runtime_module_any if isinstance(runtime_module_any, str) else ""
    if runtime_module == "":
        return False
    return len(lookup_runtime_module_extern_contract(runtime_module)) > 0


def _matches_math_symbol(expr: dict[str, Any], symbol: str, semantic_tag: str) -> bool:
    if _runtime_symbol_name(expr) != symbol:
        return False
    semantic_tag_any = expr.get("semantic_tag")
    if isinstance(semantic_tag_any, str) and semantic_tag_any == semantic_tag:
        return True
    if _has_runtime_extern_module(expr):
        return True
    # §1: use runtime_call_adapter_kind instead of hardcoded module check
    adapter = expr.get("runtime_call_adapter_kind", "")
    if isinstance(adapter, str) and adapter == "extern_delegate":
        return True
    return False


def _is_math_runtime(expr: dict[str, Any]) -> bool:
    symbol = _runtime_symbol_name(expr)
    if symbol not in _SWIFT_MATH_RUNTIME_SYMBOLS:
        return False
    if _has_runtime_extern_module(expr):
        return True
    # §1: use runtime_call_adapter_kind instead of hardcoded module check
    adapter = expr.get("runtime_call_adapter_kind", "")
    if isinstance(adapter, str) and adapter == "extern_delegate":
        return True
    return False


def _is_math_constant(expr: dict[str, Any]) -> bool:
    return _matches_math_symbol(expr, "pi", "stdlib.symbol.pi") or _matches_math_symbol(
        expr, "e", "stdlib.symbol.e"
    )


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    value_any = expr.get("value")
    attr = _safe_ident(expr.get("attr"), "field")
    if attr == "__name__" and isinstance(value_any, dict) and value_any.get("kind") == "Call" and _call_name(value_any) == "type":
        call_args_any = value_any.get("args")
        call_args = call_args_any if isinstance(call_args_any, list) else []
        if len(call_args) == 1:
            return "__pytra_type_name(" + _render_expr(call_args[0]) + ")"
    if isinstance(value_any, dict) and value_any.get("kind") == "Name":
        owner_module = value_any.get("runtime_module_id")
        if owner_module == "pytra.std.env" and attr == "target":
            return "\"swift\""
        owner_type = value_any.get("resolved_type")
        if owner_type == "type":
            return _safe_ident(value_any.get("id"), "Type") + "." + attr
    semantic_tag_any = expr.get("semantic_tag")
    semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
    runtime_call, _ = _resolved_runtime_call(expr)
    if semantic_tag.startswith("stdlib.") and runtime_call == "" and not _is_math_constant(expr) and not _is_math_runtime(expr):
        raise RuntimeError("swift native emitter: unresolved stdlib runtime attribute: " + semantic_tag)
    resolved_runtime_any = expr.get("resolved_runtime_call")
    resolved_runtime = resolved_runtime_any if isinstance(resolved_runtime_any, str) else ""
    if resolved_runtime != "":
        resolved_source_any = expr.get("resolved_runtime_source")
        resolved_source = resolved_source_any if isinstance(resolved_source_any, str) else ""
        if resolved_source == "module_attr":
            runtime_module = _runtime_module_id(expr)
            runtime_name = _runtime_symbol_name(expr)
            if runtime_module == "pytra.std.env" and runtime_name == "target":
                return "\"swift\""
            adapter = expr.get("runtime_call_adapter_kind", "")
            adapter = adapter if isinstance(adapter, str) else ""
            runtime_symbol = _resolved_runtime_symbol(resolved_runtime, adapter)
            if runtime_symbol != "":
                if _is_math_constant(expr):
                    return runtime_symbol
                return runtime_symbol
            return resolved_runtime
    # math.pi / math.e → Swift constants
    if isinstance(value_any, dict) and value_any.get("kind") == "Name":
        owner_id = _safe_ident(value_any.get("id"), "")
        if owner_id == "math":
            if attr == "pi":
                return "Double.pi"
            if attr == "e":
                return "M_E"
    value = _render_expr(value_any)
    return value + "." + attr


def _call_name(expr: dict[str, Any]) -> str:
    func_any = expr.get("func")
    if not isinstance(func_any, dict):
        return ""
    fd2: dict[str, Any] = func_any
    kind = fd2.get("kind")
    if kind == "Name":
        return _safe_ident(fd2.get("id"), "")
    if kind == "Attribute":
        return _safe_ident(fd2.get("attr"), "")
    return ""


def _call_arg_nodes(expr: dict[str, Any]) -> list[Any]:
    args_any = expr.get("args")
    args = args_any if isinstance(args_any, list) else []
    out: list[Any] = []
    i = 0
    while i < len(args):
        out.append(args[i])
        i += 1
    keywords_any = expr.get("keywords")
    keywords = keywords_any if isinstance(keywords_any, list) else []
    if len(keywords) > 0:
        j = 0
        while j < len(keywords):
            kw = keywords[j]
            if isinstance(kw, dict):
                kd: dict[str, Any] = kw
                out.append(kd.get("value"))
            else:
                out.append(kw)
            j += 1
        return out
    kw_values_any = expr.get("kw_values")
    kw_values = kw_values_any if isinstance(kw_values_any, list) else []
    if len(kw_values) > 0:
        j = 0
        while j < len(kw_values):
            out.append(kw_values[j])
            j += 1
        return out
    kw_nodes_any = expr.get("kw_nodes")
    kw_nodes = kw_nodes_any if isinstance(kw_nodes_any, list) else []
    j = 0
    while j < len(kw_nodes):
        node = kw_nodes[j]
        if isinstance(node, dict):
            nd2: dict[str, Any] = node
            if nd2.get("kind") == "keyword":
                out.append(nd2.get("value"))
            else:
                out.append(node)
        else:
            out.append(node)
        j += 1
    return out


def _class_has_base_method(class_name: str, method_name: str) -> bool:
    seen: set[str] = set()
    cur = _CLASS_BASES[0].get(class_name, "")
    while cur != "" and cur not in seen:
        seen.add(cur)
        methods = _CLASS_METHODS[0].get(cur)
        if isinstance(methods, set) and method_name in methods:
            return True
        cur = _CLASS_BASES[0].get(cur, "")
    return False


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


def _render_call_via_runtime_call(
    runtime_call: str,
    runtime_source: str,
    semantic_tag: str,
    args: list[Any],
    expr: dict[str, Any],
) -> str:
    if runtime_call == "static_cast" and len(args) == 1:
        return _cast_from_any(_render_expr(args[0]), _swift_type(expr.get("resolved_type"), allow_void=False))
    if runtime_call in {"index", "__pytra_index"} and len(args) == 2:
        arg0 = args[0]
        arg0_type = arg0.get("resolved_type") if isinstance(arg0, dict) else ""
        if arg0_type == "str":
            return "__pytra_index_str(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
        return "__pytra_list_index(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
    if runtime_call == "py_to_string" and len(args) == 1:
        arg0 = args[0]
        if isinstance(arg0, dict):
            resolved_arg_type = arg0.get("resolved_type")
            if isinstance(resolved_arg_type, str) and resolved_arg_type.startswith("tuple["):
                return "__pytra_tuple_str(" + _render_expr(arg0) + ")"
    if runtime_call == "py_assert_true":
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_true(" + ", ".join(rendered_assert_args) + ")"
    if runtime_call == "py_assert_eq":
        rendered_assert_args = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_eq(" + ", ".join(rendered_assert_args) + ")"
    if runtime_call == "py_assert_all":
        rendered_assert_args = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_all(" + ", ".join(rendered_assert_args) + ")"
    if runtime_call.startswith("py_assert_"):
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered_assert_args) + ")"
    runtime_module = _runtime_module_id(expr)
    runtime_name = _runtime_symbol_name(expr)
    if runtime_module == "pytra.std.collections" and runtime_name == "deque":
        return "[]"
    adapter = expr.get("runtime_call_adapter_kind", "")
    adapter = adapter if isinstance(adapter, str) else ""
    if runtime_source == "runtime_call":
        if adapter == "builtin":
            runtime_owner = expr.get("runtime_owner")
            owner_expr = ""
            owner_type = ""
            if isinstance(runtime_owner, dict):
                if runtime_owner.get("kind") == "Call" and _call_name(runtime_owner) == "super":
                    owner_expr = "super"
                else:
                    owner_expr = _render_expr(runtime_owner)
                rt = runtime_owner.get("resolved_type")
                owner_type = rt if isinstance(rt, str) else ""
            if owner_expr != "":
                method_name = runtime_call.split(".")[-1].strip()
                if method_name == "__init__":
                    rendered_runtime_args: list[str] = []
                    i = 0
                    while i < len(args):
                        rendered_runtime_args.append(_render_expr(args[i]))
                        i += 1
                    return owner_expr + ".init(" + ", ".join(rendered_runtime_args) + ")"
                if method_name == "clear":
                    return owner_expr + ".removeAll()"
                if method_name == "extend" and len(args) == 1:
                    return "__pytra_extend(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if method_name == "reverse":
                    return owner_expr + ".reverse()"
                if method_name == "sort":
                    return owner_expr + ".sort { __pytra_float($0) < __pytra_float($1) }"
                if method_name == "append" and len(args) == 1:
                    return owner_expr + ".append(" + _render_expr(args[0]) + ")"
                if method_name == "add" and len(args) == 1:
                    return "__pytra_set_add(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if method_name == "discard" and len(args) == 1:
                    return "__pytra_discard(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if method_name == "remove" and len(args) == 1:
                    return "__pytra_remove(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if method_name == "pop" and owner_type.startswith("dict[") and len(args) == 1:
                    return _cast_from_any(
                        "__pytra_dict_pop(&" + owner_expr + ", " + _render_expr(args[0]) + ")",
                        _swift_type(expr.get("resolved_type"), allow_void=False),
                    )
                if method_name == "setdefault" and owner_type.startswith("dict[") and len(args) == 2:
                    return _cast_from_any(
                        "__pytra_dict_setdefault(&" + owner_expr + ", " + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")",
                        _swift_type(expr.get("resolved_type"), allow_void=False),
                    )
            runtime_symbol = _resolved_runtime_symbol(runtime_call, adapter)
            if runtime_symbol == "":
                return ""
            rendered_runtime_args: list[str] = []
            if owner_expr != "":
                rendered_runtime_args.append(owner_expr)
            i = 0
            while i < len(args):
                rendered_runtime_args.append(_render_expr(args[i]))
                i += 1
            return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
        if semantic_tag.startswith("stdlib.fn."):
            runtime_symbol = _resolved_runtime_symbol(runtime_call, adapter)
            if runtime_symbol == "":
                return ""
            rendered_runtime_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_runtime_args.append(_render_expr(args[i]))
                i += 1
            return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
        return ""
    runtime_symbol = _resolved_runtime_symbol(runtime_call, adapter)
    if runtime_module == "pytra.utils.png" and runtime_name == "write_rgb_png":
        rendered_runtime_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_runtime_args.append(_render_expr(args[i]))
            i += 1
        return "write_rgb_png(" + ", ".join(rendered_runtime_args) + ")"
    if runtime_module == "pytra.std.os" and runtime_name == "makedirs":
        rendered_runtime_args = []
        i = 0
        while i < len(args):
            rendered_runtime_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_makedirs(" + ", ".join(rendered_runtime_args) + ")"
    if runtime_symbol == "":
        return ""
    if runtime_symbol in {"__pytra_extend", "__pytra_discard", "__pytra_remove", "__pytra_set_add"} and len(args) > 0:
        rendered_runtime_args: list[str] = []
        first_arg = args[0]
        if isinstance(first_arg, dict) and first_arg.get("kind") == "Name":
            rendered_runtime_args.append("&" + _render_expr(first_arg))
        else:
            rendered_runtime_args.append(_render_expr(first_arg))
        i = 1
        while i < len(args):
            rendered_runtime_args.append(_render_expr(args[i]))
            i += 1
        return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
    if runtime_call.find(".") >= 0:
        rendered_call_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_arg = _render_expr(args[i])
            if _is_math_runtime(expr):
                rendered_arg = _to_float_expr(rendered_arg)
            rendered_call_args.append(rendered_arg)
            i += 1
        if _is_math_constant(expr):
            return "__pytra_float(" + runtime_symbol + "())"
        return runtime_symbol + "(" + ", ".join(rendered_call_args) + ")"
    rendered_runtime_args: list[str] = []
    i = 0
    while i < len(args):
        rendered_runtime_args.append(_render_expr(args[i]))
        i += 1
    return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"


def _render_call_expr(expr: dict[str, Any]) -> str:
    args = _call_arg_nodes(expr)

    callee_name = _call_name(expr)
    fn_any = expr.get("func")
    if (
        callee_name == "main"
        and _MAIN_CALL_ALIAS[0] != ""
        and isinstance(fn_any, dict)
        and fn_any.get("kind") == "Name"
    ):
        rendered_main_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_main_args.append(_render_expr(args[i]))
            i += 1
        call_code = _MAIN_CALL_ALIAS[0] + "(" + ", ".join(rendered_main_args) + ")"
        if _MAIN_CALL_ALIAS[0] in _THROWING_FUNCTIONS[0]:
            return "try " + call_code
        return call_code
    semantic_tag_any = expr.get("semantic_tag")
    semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
    if semantic_tag == "stdlib.symbol.Path":
        if len(args) == 0:
            return "Path(\"\")"
        return "Path(" + _render_expr(args[0]) + ")"
    runtime_call, runtime_source = _resolved_runtime_call(expr)
    if semantic_tag.startswith("stdlib.") and runtime_call == "":
        raise RuntimeError("swift native emitter: unresolved stdlib runtime call: " + semantic_tag)
    if runtime_call != "":
        rendered_runtime = _render_call_via_runtime_call(
            runtime_call,
            runtime_source,
            semantic_tag,
            args,
            expr,
        )
        if rendered_runtime != "":
            return rendered_runtime
    if callee_name == "py_assert_true":
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_true(" + ", ".join(rendered_assert_args) + ")"
    if callee_name == "py_assert_eq":
        rendered_assert_args = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_eq(" + ", ".join(rendered_assert_args) + ")"
    if callee_name == "py_assert_all":
        rendered_assert_args = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_all(" + ", ".join(rendered_assert_args) + ")"
    if callee_name.startswith("py_assert_"):
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered_assert_args) + ")"
    if callee_name == "bytearray":
        if len(args) == 0:
            return "[]"
        return "__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee_name == "deque":
        return "[]"
    if callee_name == "bytes":
        if len(args) == 0:
            return "[]"
        return "__pytra_bytes(" + _render_expr(args[0]) + ")"
    if callee_name == "extern":
        if len(args) == 0:
            return "__pytra_any_default()"
        return _render_expr(args[0])
    if callee_name == "int":
        if len(args) == 0:
            return "Int64(0)"
        arg0 = args[0]
        rendered_arg0 = _render_expr(arg0)
        if _has_resolved_type(arg0, {"int", "int64", "uint8"}):
            return rendered_arg0
        return _to_int_expr(rendered_arg0)
    if callee_name == "float":
        if len(args) == 0:
            return "Double(0)"
        arg0 = args[0]
        rendered_arg0 = _render_expr(arg0)
        if _has_resolved_type(arg0, {"float", "float64"}):
            return rendered_arg0
        return _to_float_expr(rendered_arg0)
    if callee_name == "bool":
        if len(args) == 0:
            return "false"
        return _to_truthy_expr(_render_expr(args[0]))
    if callee_name == "str" or callee_name == "py_to_string":
        if len(args) == 0:
            return '""'
        if isinstance(args[0], dict):
            resolved_arg_type = args[0].get("resolved_type")
            if isinstance(resolved_arg_type, str) and resolved_arg_type.startswith("tuple["):
                return "__pytra_tuple_str(" + _render_expr(args[0]) + ")"
        return _to_str_expr(_render_expr(args[0]))
    if callee_name == "len":
        if len(args) == 0:
            return "Int64(0)"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "sum":
        if len(args) == 0:
            return "Int64(0)"
        return "__pytra_sum(" + _render_expr(args[0]) + ")"
    if callee_name == "zip":
        if len(args) < 2:
            return "[]"
        return "__pytra_zip(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
    if callee_name == "type":
        if len(args) == 0:
            return '"Any"'
        return "__pytra_type_name(" + _render_expr(args[0]) + ")"
    if callee_name in {"index", "__pytra_index"} and len(args) == 2:
        first_any = args[0]
        first_type = first_any.get("resolved_type") if isinstance(first_any, dict) else ""
        if first_type == "str":
            return "__pytra_index_str(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
        return "__pytra_list_index(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
    if callee_name == "enumerate":
        if len(args) == 0:
            return "__pytra_enumerate([])"
        if len(args) == 1:
            return "__pytra_enumerate(" + _render_expr(args[0]) + ")"
        return "__pytra_py_enumerate_object(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
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
    if callee_name == "print":
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_print(" + ", ".join(rendered_args) + ")"
    if callee_name == "open":
        rendered_args = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_open(" + ", ".join(rendered_args) + ")"
    if callee_name in {"__pytra_extend", "__pytra_discard", "__pytra_remove", "__pytra_set_add"} and len(args) >= 1:
        rendered_args: list[str] = []
        first_arg = args[0]
        if isinstance(first_arg, dict) and first_arg.get("kind") == "Name":
            rendered_args.append("&" + _render_expr(first_arg))
        else:
            rendered_args.append(_render_expr(first_arg))
        i = 1
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return callee_name + "(" + ", ".join(rendered_args) + ")"

    func_any = expr.get("func")
    if callee_name == "__pytra___init__" and len(args) >= 1:
        first_arg = args[0]
        if isinstance(first_arg, dict) and first_arg.get("kind") == "Call" and _call_name(first_arg) == "super":
            rendered_super_args: list[str] = []
            i = 1
            while i < len(args):
                rendered_super_args.append(_render_expr(args[i]))
                i += 1
            return "super.init(" + ", ".join(rendered_super_args) + ")"
    if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
        attr_name = _safe_ident(func_any.get("attr"), "")
        owner_any = func_any.get("value")
        if attr_name == "__name__" and isinstance(owner_any, dict) and owner_any.get("kind") == "Call" and _call_name(owner_any) == "type":
            call_args_any = owner_any.get("args")
            call_args = call_args_any if isinstance(call_args_any, list) else []
            if len(call_args) == 1:
                return "__pytra_type_name(" + _render_expr(call_args[0]) + ")"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner_id = owner_any.get("id", "")
            # math module → Swift Foundation global functions
            if owner_id == "math" and attr_name in _SWIFT_MATH_RUNTIME_SYMBOLS:
                rendered_math_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_math_args.append(_to_float_expr(_render_expr(args[i])))
                    i += 1
                if attr_name == "pi":
                    return "Double.pi"
                if attr_name == "e":
                    return "M_E"
                if attr_name == "fabs":
                    return "abs(" + ", ".join(rendered_math_args) + ")"
                return attr_name + "(" + ", ".join(rendered_math_args) + ")"
            # png/gif module → direct function calls
            if owner_id == "png" or owner_id == "gif":
                rendered_mod_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_mod_args.append(_render_expr(args[i]))
                    i += 1
                return attr_name + "(" + ", ".join(rendered_mod_args) + ")"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Call" and _call_name(owner_any) == "super":
            rendered_super_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_super_args.append(_render_expr(args[i]))
                i += 1
            if attr_name == "__init__":
                return "super.init(" + ", ".join(rendered_super_args) + ")"
            return "super." + attr_name + "(" + ", ".join(rendered_super_args) + ")"
        if attr_name == "isdigit" and len(args) == 0:
            return "__pytra_isdigit(" + _render_expr(owner_any) + ")"
        if attr_name == "isalpha" and len(args) == 0:
            return "__pytra_isalpha(" + _render_expr(owner_any) + ")"
        if attr_name == "index" and len(args) == 1:
            if isinstance(owner_any, dict):
                owner_type = owner_any.get("resolved_type")
                if owner_type == "str":
                    return "__pytra_index_str(" + _render_expr(owner_any) + ", " + _render_expr(args[0]) + ")"
            return "__pytra_list_index(" + _render_expr(owner_any) + ", " + _render_expr(args[0]) + ")"
        owner_expr = _render_expr(owner_any)
        owner_type = owner_any.get("resolved_type", "") if isinstance(owner_any, dict) else ""
        if isinstance(owner_type, str):
            if (
                owner_type.startswith("list[")
                or owner_type.startswith("dict[")
                or owner_type.startswith("set[")
                or owner_type in {"bytes", "bytearray", "str", "deque"}
            ):
                if attr_name == "clear" and len(args) == 0:
                    return owner_expr + ".removeAll()"
                if (owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}) and attr_name == "append" and len(args) == 1:
                    return owner_expr + ".append(" + _render_expr(args[0]) + ")"
                if owner_type.startswith("list[") and attr_name == "extend" and len(args) == 1:
                    return "__pytra_extend(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type == "deque" and attr_name == "append" and len(args) == 1:
                    return owner_expr + ".append(" + _render_expr(args[0]) + ")"
                if owner_type == "deque" and attr_name == "appendleft" and len(args) == 1:
                    return "__pytra_deque_appendleft(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type == "deque" and attr_name == "popleft" and len(args) == 0:
                    return "__pytra_deque_popleft(&" + owner_expr + ")"
                if owner_type == "deque" and attr_name == "pop" and len(args) == 0:
                    return "__pytra_deque_pop(&" + owner_expr + ")"
                if (owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}) and attr_name == "reverse" and len(args) == 0:
                    return owner_expr + ".reverse()"
                if owner_type.startswith("list[") and attr_name == "sort" and len(args) == 0:
                    return owner_expr + ".sort { __pytra_float($0) < __pytra_float($1) }"
                if owner_type.startswith("dict[") and attr_name == "pop" and len(args) == 1:
                    return "__pytra_dict_pop(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type.startswith("dict[") and attr_name == "setdefault" and len(args) == 2:
                    return "__pytra_dict_setdefault(&" + owner_expr + ", " + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
                if owner_type.startswith("set[") and attr_name == "add" and len(args) == 1:
                    return "__pytra_set_add(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type.startswith("set[") and attr_name == "discard" and len(args) == 1:
                    return "__pytra_discard(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type.startswith("set[") and attr_name == "remove" and len(args) == 1:
                    return "__pytra_remove(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
        if attr_name == "get":
            if len(args) >= 2:
                return "__pytra_dict_get(" + owner_expr + ", " + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
            if len(args) == 1:
                return "__pytra_dict_get(" + owner_expr + ", " + _render_expr(args[0]) + ", __pytra_any_default())"
            return "__pytra_any_default()"
        if attr_name == "items" and len(args) == 0:
            return "__pytra_items(" + owner_expr + ")"
        if attr_name == "keys" and len(args) == 0:
            return "__pytra_keys(" + owner_expr + ")"
        if attr_name == "values" and len(args) == 0:
            return "__pytra_values(" + owner_expr + ")"
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return owner_expr + "." + attr_name + "(" + ", ".join(rendered_args) + ")"

    if callee_name in _CLASS_NAMES[0]:
        rendered_ctor_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_ctor_args.append(_render_expr(args[i]))
            i += 1
        return callee_name + "(" + ", ".join(rendered_ctor_args) + ")"

    func_expr = _render_expr(expr.get("func"))
    rendered_args = []
    inout_positions = _INOUT_PARAM_POSITIONS[0].get(callee_name, set())
    callee_type = ""
    func_node = expr.get("func")
    if isinstance(func_node, dict):
        callee_type_any = func_node.get("resolved_type")
        callee_type = callee_type_any if isinstance(callee_type_any, str) else ""
    callable_parts = _callable_signature_parts(callee_type)
    callable_arg_types = callable_parts[0] if callable_parts is not None else []
    i = 0
    while i < len(args):
        rendered_arg = _render_expr(args[i])
        if i in inout_positions and isinstance(args[i], dict) and args[i].get("kind") == "Name":
            rendered_arg = "&" + rendered_arg
        elif i < len(callable_arg_types):
            target_type = _swift_type(callable_arg_types[i], allow_void=False)
            if target_type not in {"", "Any"} and _needs_cast(args[i], target_type):
                rendered_arg = _cast_from_any(rendered_arg, target_type)
        rendered_args.append(rendered_arg)
        i += 1
    call_code = func_expr + "(" + ", ".join(rendered_args) + ")"
    if callee_name in _THROWING_FUNCTIONS[0]:
        return "try " + call_code
    return call_code


def _render_isinstance_check(lhs: str, typ: Any) -> str:
    if not isinstance(typ, dict):
        return "false"
    td: dict[str, Any] = typ
    if td.get("kind") == "Name":
        name = _safe_ident(td.get("id"), "")
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
        if name in {"dict", "PYTRA_TID_DICT"}:
            return "__pytra_is_dict(" + lhs + ")"
        if name in _CLASS_NAMES[0]:
            return "__pytra_is_" + name + "(" + lhs + ")"
        return "false"
    if td.get("kind") == "Tuple":
        elements_any = td.get("elements")
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
    ed2: dict[str, Any] = expr
    kind = ed2.get("kind")

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
    if kind == "JoinedStr":
        values_any = ed2.get("values")
        values = values_any if isinstance(values_any, list) else []
        if len(values) == 0:
            return '""'
        rendered_parts: list[str] = []
        i = 0
        while i < len(values):
            rendered_parts.append(_render_expr(values[i]))
            i += 1
        return "(" + " + ".join(rendered_parts) + ")"
    if kind == "FormattedValue":
        format_spec = _render_format_spec(ed2.get("format_spec"))
        if format_spec != "":
            return "__pytra_format_value(" + _render_expr(ed2.get("value")) + ", " + _swift_string_literal(format_spec) + ")"
        return _to_str_expr(_render_expr(ed2.get("value")))
    if kind == "Lambda":
        args_any = ed2.get("args")
        args = args_any if isinstance(args_any, list) else []
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            arg_any = args[i]
            if isinstance(arg_any, dict):
                arg_name = _safe_ident(arg_any.get("arg"), "arg")
                arg_type = _swift_type(arg_any.get("resolved_type"), allow_void=False)
                rendered_args.append("_ " + arg_name + ": " + arg_type)
            i += 1
        return_type = _function_return_swift_type(ed2, allow_void=True)
        body_expr = _render_expr(ed2.get("body"))
        return "{ (" + ", ".join(rendered_args) + ") -> " + return_type + " in return " + body_expr + " }"

    if kind == "List" or kind == "Tuple":
        elements_any = ed2.get("elements")
        if not isinstance(elements_any, list):
            elements_any = ed2.get("elts")
        elements = elements_any if isinstance(elements_any, list) else []
        rendered: list[str] = []
        i = 0
        while i < len(elements):
            rendered.append(_render_expr(elements[i]))
            i += 1
        return "[" + ", ".join(rendered) + "]"

    if kind == "Set":
        elements_any = ed2.get("elements")
        elements = elements_any if isinstance(elements_any, list) else []
        rendered: list[str] = []
        i = 0
        while i < len(elements):
            rendered.append(_render_expr(elements[i]))
            i += 1
        return "__pytra_set_literal([" + ", ".join(rendered) + "])"

    if kind == "Dict":
        parts: list[str] = []
        entries_any = ed2.get("entries")
        entries = entries_any if isinstance(entries_any, list) else []
        if len(entries) > 0:
            i = 0
            while i < len(entries):
                entry = entries[i]
                if isinstance(entry, dict):
                    ed: dict[str, Any] = entry
                    key_node = ed.get("key")
                    val_node = ed.get("value")
                    if key_node is not None and val_node is not None:
                        parts.append("AnyHashable(__pytra_str(" + _render_expr(key_node) + ")): " + _render_expr(val_node))
                i += 1
            if len(parts) == 0:
                return "[:]"
            return "[" + ", ".join(parts) + "]"
        keys_any = ed2.get("keys")
        vals_any = ed2.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        vals = vals_any if isinstance(vals_any, list) else []
        if len(keys) == 0 or len(vals) == 0:
            return "[:]"
        i = 0
        while i < len(keys) and i < len(vals):
            parts.append("AnyHashable(__pytra_str(" + _render_expr(keys[i]) + ")): " + _render_expr(vals[i]))
            i += 1
        return "[" + ", ".join(parts) + "]"

    if kind == "ListComp":
        gens_any = ed2.get("generators")
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
        if not isinstance(target_any, dict):
            return "[]"
        if not isinstance(iter_any, dict):
            return "[]"
        id: dict[str, Any] = iter_any
        elt = _render_expr(ed2.get("elt"))
        if id.get("kind") == "RangeExpr":
            td2: dict[str, Any] = target_any
            if td2.get("kind") != "Name":
                return "[]"
            loop_var = _safe_ident(td2.get("id"), "i")
            if loop_var == "_":
                loop_var = "__lc_i"
            start = _render_expr(id.get("start"))
            stop = _render_expr(id.get("stop"))
            step = _render_expr(id.get("step"))
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
        iter_expr = _render_expr(iter_any)
        cond = ""
        if len(ifs) == 1:
            cond = "if " + _render_truthy_expr(ifs[0]) + " { __out.append(" + elt + ") }"
        else:
            cond = "__out.append(" + elt + ")"
        td2 = target_any
        if td2.get("kind") == "Tuple":
            elements_any = td2.get("elements")
            elements = elements_any if isinstance(elements_any, list) else []
            if len(elements) == 0:
                return "[]"
            bindings: list[str] = []
            i = 0
            while i < len(elements):
                item_any = elements[i]
                if not isinstance(item_any, dict) or item_any.get("kind") != "Name":
                    return "[]"
                item_name = _safe_ident(item_any.get("id"), "item" + str(i))
                item_type = _swift_type(item_any.get("resolved_type"), allow_void=False)
                bindings.append(
                    "let " + item_name + ": " + item_type + " = " + _cast_from_any("__target[" + str(i) + "]", item_type) + "; "
                )
                i += 1
            return (
                "({ () -> [Any] in "
                "var __out: [Any] = []; "
                "for __item in __pytra_as_list(" + iter_expr + ") { let __target = __pytra_as_list(__item); "
                + "".join(bindings)
                + cond
                + " }; "
                "return __out "
                "})()"
            )
        if td2.get("kind") != "Name":
            return "[]"
        loop_var = _safe_ident(td2.get("id"), "i")
        if loop_var == "_":
            loop_var = "__lc_i"
        loop_type = _swift_type(td2.get("resolved_type"), allow_void=False)
        return (
            "({ () -> [Any] in "
            "var __out: [Any] = []; "
            "for __item in __pytra_as_list("
            + iter_expr
            + ") { let "
            + loop_var
            + ": "
            + loop_type
            + " = "
            + _cast_from_any("__item", loop_type)
            + "; "
            + cond
            + " }; "
            "return __out "
            "})()"
        )

    if kind == "SetComp":
        gens_any = ed2.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "[]"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
            return "[]"
        if not isinstance(iter_any, dict):
            return "[]"
        loop_var = _safe_ident(target_any.get("id"), "item")
        loop_type = _swift_type(target_any.get("resolved_type"), allow_void=False)
        iter_expr = _render_expr(iter_any)
        elt = _render_expr(ed2.get("elt"))
        cond = ""
        if len(ifs) == 1:
            cond = "if " + _render_truthy_expr(ifs[0]) + " { __pytra_set_add(&__out, " + elt + ") }"
        else:
            cond = "__pytra_set_add(&__out, " + elt + ")"
        return (
            "({ () -> [Any] in "
            "var __out: [Any] = []; "
            "for __item in __pytra_as_list(" + iter_expr + ") { let " + loop_var + ": " + loop_type + " = " + _cast_from_any("__item", loop_type) + "; " + cond + " }; "
            "return __out "
            "})()"
        )

    if kind == "DictComp":
        gens_any = ed2.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "[:]"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
            return "[:]"
        if not isinstance(iter_any, dict):
            return "[:]"
        loop_var = _safe_ident(target_any.get("id"), "item")
        loop_type = _swift_type(target_any.get("resolved_type"), allow_void=False)
        iter_expr = _render_expr(iter_any)
        key_expr = _render_expr(ed2.get("key"))
        value_expr = _render_expr(ed2.get("value"))
        store = "__out[AnyHashable(__pytra_str(" + key_expr + "))] = " + value_expr
        if len(ifs) == 1:
            store = "if " + _render_truthy_expr(ifs[0]) + " { " + store + " }"
        return (
            "({ () -> [AnyHashable: Any] in "
            "var __out: [AnyHashable: Any] = [:]; "
            "for __item in __pytra_as_list(" + iter_expr + ") { let " + loop_var + ": " + loop_type + " = " + _cast_from_any("__item", loop_type) + "; " + store + " }; "
            "return __out "
            "})()"
        )

    if kind == "IfExp":
        test_expr = _render_truthy_expr(ed2.get("test"))
        body_node = ed2.get("body")
        else_node = ed2.get("orelse")
        body_expr = _render_expr(body_node)
        else_expr = _render_expr(else_node)
        result_type = _swift_type(ed2.get("resolved_type"), allow_void=False)
        if result_type != "Any":
            if _needs_cast(body_node, result_type):
                body_expr = _cast_from_any(body_expr, result_type)
            if _needs_cast(else_node, result_type):
                else_expr = _cast_from_any(else_expr, result_type)
            return "(" + test_expr + " ? " + body_expr + " : " + else_expr + ")"
        return "__pytra_ifexp(" + test_expr + ", " + body_expr + ", " + else_expr + ")"

    if kind == "Subscript":
        owner = _render_expr(ed2.get("value"))
        index_any = ed2.get("slice")
        if isinstance(index_any, dict) and index_any.get("kind") == "Slice":
            lower_any = index_any.get("lower")
            upper_any = index_any.get("upper")
            lower = _render_expr(lower_any) if isinstance(lower_any, dict) else "Int64(0)"
            upper = _render_expr(upper_any) if isinstance(upper_any, dict) else "__pytra_len(" + owner + ")"
            return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"

        index = _render_expr(index_any)
        base = "try __pytra_getIndex(" + owner + ", " + index + ")"
        resolved = ed2.get("resolved_type")
        swift_t = _swift_type(resolved, allow_void=False)
        return _cast_from_any(base, swift_t)

    if kind == "IsInstance":
        lhs = _render_expr(ed2.get("value"))
        return _render_isinstance_check(lhs, ed2.get("expected_type_id"))

    if kind == "ObjLen":
        return "__pytra_len(" + _render_expr(ed2.get("value")) + ")"
    if kind == "ObjStr":
        return "__pytra_str(" + _render_expr(ed2.get("value")) + ")"
    if kind == "ObjBool":
        return "__pytra_truthy(" + _render_expr(ed2.get("value")) + ")"

    if kind == "Unbox":
        target_any = ed2.get("target")
        target = target_any if isinstance(target_any, str) else ""
        if target != "":
            return _cast_from_any(_render_expr(ed2.get("value")), _swift_type(target, allow_void=False))
        return _render_expr(ed2.get("value"))
    if kind == "Box":
        return _render_expr(ed2.get("value"))

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


def _function_params(fn: dict[str, Any], *, drop_self: bool, use_any: bool = False) -> list[str]:
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    names = _function_param_names(fn, drop_self=drop_self)
    reassigned = collect_reassigned_params(fn)
    inout_positions = _collect_inout_param_positions(fn, drop_self=drop_self)
    out: list[str] = []
    i = 0
    while i < len(names):
        name = names[i]
        param_name = mutable_param_name(name) if name in reassigned else name
        original_type = _swift_type(arg_types.get(name), allow_void=False)
        param_type = "Any" if use_any else original_type
        if i in inout_positions:
            param_type = "inout " + param_type
        out.append("_ " + param_name + ": " + param_type)
        i += 1
    return out


def _target_name(target: Any) -> str:
    if not isinstance(target, dict):
        return "tmp"
    td: dict[str, Any] = target
    kind = td.get("kind")
    if kind == "Name":
        return _safe_ident(td.get("id"), "tmp")
    if kind == "Attribute":
        return _render_attribute_expr(target)
    return "tmp"


def _emit_swap(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    lhs_node = stmt.get("lhs") if stmt.get("lhs") is not None else stmt.get("left")
    rhs_node = stmt.get("rhs") if stmt.get("rhs") is not None else stmt.get("right")
    # Handle Subscript swap (array element exchange) via __pytra_getIndex/__pytra_setIndex
    lhs_is_sub = isinstance(lhs_node, dict) and lhs_node.get("kind") == "Subscript"
    rhs_is_sub = isinstance(rhs_node, dict) and rhs_node.get("kind") == "Subscript"
    if lhs_is_sub and rhs_is_sub:
        tmp = _fresh_tmp(ctx, "swap")
        lhs_get = _render_expr(lhs_node)
        rhs_get = _render_expr(rhs_node)
        lhs_container = _render_expr(lhs_node.get("value"))
        lhs_index = _render_expr(lhs_node.get("slice"))
        rhs_container = _render_expr(rhs_node.get("value"))
        rhs_index = _render_expr(rhs_node.get("slice"))
        return [
            indent + "var " + tmp + ": Any = " + lhs_get,
            indent + "__pytra_setIndex(" + lhs_container + ", " + lhs_index + ", " + rhs_get + ")",
            indent + "__pytra_setIndex(" + rhs_container + ", " + rhs_index + ", " + tmp + ")",
        ]
    left = _target_name(lhs_node)
    right = _target_name(rhs_node)
    if left == "":
        left = _render_expr(lhs_node)
    if right == "":
        right = _render_expr(rhs_node)
    tmp = _fresh_tmp(ctx, "swap")
    tmp_type = _infer_swift_type(lhs_node, _type_map(ctx))
    if tmp_type == "Any":
        tmp_type = "Any"
    return [
        indent + "var " + tmp + ": " + tmp_type + " = " + left,
        indent + left + " = " + right,
        indent + right + " = " + tmp,
    ]


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


def _ref_var_set(ctx: dict[str, Any]) -> set[str]:
    ref_vars = ctx.get("ref_vars")
    if isinstance(ref_vars, set):
        return ref_vars
    out: set[str] = set()
    ctx["ref_vars"] = out
    return out


def _alias_map(ctx: dict[str, Any]) -> dict[str, str]:
    alias_map = ctx.get("alias_map")
    if isinstance(alias_map, dict):
        return alias_map
    out: dict[str, str] = {}
    ctx["alias_map"] = out
    return out


def _is_container_east_type(type_name: Any) -> bool:
    if not isinstance(type_name, str):
        return False
    ts: str = type_name
    if ts.startswith("list[") or ts.startswith("tuple[") or ts.startswith("dict["):
        return True
    return type_name in {"bytes", "bytearray"}


def _materialize_container_value_from_ref(
    value_expr: Any,
    *,
    target_type: str,
    target_name: str,
    ctx: dict[str, Any],
) -> str | None:
    _ = value_expr
    _ = target_type
    _ = target_name
    _ = ctx
    # Python assignment preserves aliasing for mutable containers.
    return None


def _infer_swift_type(expr: Any, type_map: dict[str, str] | None = None) -> str:
    if not isinstance(expr, dict):
        return "Any"
    ed: dict[str, Any] = expr
    kind = ed.get("kind")
    if kind == "Name" and isinstance(type_map, dict):
        ident = _safe_ident(ed.get("id"), "")
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
        if name in {
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "atan2",
            "sqrt",
            "exp",
            "log",
            "log10",
            "floor",
            "ceil",
            "pow",
        }:
            return "Double"
        if name in {"min", "max"}:
            args_any = ed.get("args")
            args = args_any if isinstance(args_any, list) else []
            saw_float = False
            saw_int = False
            i = 0
            while i < len(args):
                at = _infer_swift_type(args[i], type_map)
                if at == "Double":
                    saw_float = True
                elif at == "Int64":
                    saw_int = True
                i += 1
            if saw_float:
                return "Double"
            if saw_int:
                return "Int64"
            resolved = _swift_type(ed.get("resolved_type"), allow_void=False)
            if resolved in {"Int64", "Double"}:
                return resolved
            return "Any"
        if name in _CLASS_NAMES[0]:
            return name
    if kind == "Lambda":
        return _swift_type(ed.get("resolved_type"), allow_void=False)
    if kind == "BinOp":
        op = ed.get("op")
        if op == "Div":
            return "Double"
        left_t = _infer_swift_type(ed.get("left"), type_map)
        right_t = _infer_swift_type(ed.get("right"), type_map)
        if left_t == "Double" or right_t == "Double":
            return "Double"
        if left_t == "Int64" and right_t == "Int64":
            return "Int64"
        if op == "Mult":
            left_any = ed.get("left")
            right_any = ed.get("right")
            if isinstance(left_any, dict) and left_any.get("kind") == "List":
                return "[Any]"
            if isinstance(right_any, dict) and right_any.get("kind") == "List":
                return "[Any]"
    if kind == "IfExp":
        body_t = _infer_swift_type(ed.get("body"), type_map)
        else_t = _infer_swift_type(ed.get("orelse"), type_map)
        if body_t == else_t:
            return body_t
        if body_t == "Double" or else_t == "Double":
            return "Double"
        if body_t == "Int64" and else_t == "Int64":
            return "Int64"
    resolved = ed.get("resolved_type")
    return _swift_type(resolved, allow_void=False)


def _expr_emits_target_type(value_expr: Any, target_type: str, type_map: dict[str, str] | None = None) -> bool:
    if not isinstance(value_expr, dict):
        return False
    vd: dict[str, Any] = value_expr
    kind = vd.get("kind")
    if kind == "Name":
        if isinstance(type_map, dict):
            ident = _safe_ident(vd.get("id"), "")
            mapped_any = type_map.get(ident)
            mapped = mapped_any if isinstance(mapped_any, str) else ""
            return mapped == target_type
        return False
    if kind == "Constant":
        value = vd.get("value")
        if target_type == "Int64":
            return isinstance(value, int) and not isinstance(value, bool)
        if target_type == "Double":
            return isinstance(value, float)
        if target_type == "Bool":
            return isinstance(value, bool)
        if target_type == "String":
            return isinstance(value, str)
        return False
    if kind == "BinOp":
        resolved = _swift_type(vd.get("resolved_type"), allow_void=False)
        return resolved == target_type
    if kind in {"Compare", "BoolOp", "IsInstance"}:
        return target_type == "Bool"
    if kind == "Call":
        callee = _call_name(value_expr)
        if callee == "int":
            return target_type == "Int64"
        if callee == "float":
            return target_type == "Double"
        if callee == "bool":
            return target_type == "Bool"
        if callee == "str":
            return target_type == "String"
        if callee == "perf_counter":
            return target_type == "Double"
        if callee == "len":
            return target_type == "Int64"
        resolved = _swift_type(vd.get("resolved_type"), allow_void=False)
        func_any = vd.get("func")
        if isinstance(func_any, dict):
            fd: dict[str, Any] = func_any
            f_kind = fd.get("kind")
            if f_kind == "Name":
                if callee != "" and not callee.startswith("__pytra_") and resolved == target_type:
                    return True
            if f_kind == "Attribute":
                attr = _safe_ident(fd.get("attr"), "")
                if attr not in {"get", "getOrElse"} and not attr.startswith("__pytra_") and resolved == target_type:
                    return True
    return False


def _needs_cast(value_expr: Any, target_type: str, type_map: dict[str, str] | None = None) -> bool:
    if target_type in {"", "Any"}:
        return False
    return not _expr_emits_target_type(value_expr, target_type, type_map)


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        raise RuntimeError("swift native emitter: unsupported ForCore iter_plan")
    id: dict[str, Any] = iter_plan_any
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("swift native emitter: unsupported ForCore target_plan")
    td: dict[str, Any] = target_plan_any

    lines: list[str] = []
    if id.get("kind") == "StaticRangeForPlan" and td.get("kind") == "NameTarget":
        target_name = _safe_ident(td.get("id"), "i")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "loop")
        start_node = id.get("start")
        stop_node = id.get("stop")
        step_node = id.get("step")
        start = _to_int_expr(_render_expr(start_node))
        stop = _to_int_expr(_render_expr(stop_node))
        step = _to_int_expr(_render_expr(step_node))
        step_is_one = _is_int_literal(step_node, 1)
        step_tmp = _fresh_tmp(ctx, "step")
        lines.append(indent + "var " + target_name + " = " + start)
        if step_is_one:
            lines.append(indent + "while (" + target_name + " < " + stop + ") {")
        else:
            lines.append(indent + "let " + step_tmp + " = " + step)
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
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": target_name + (" += 1" if step_is_one else " += " + step_tmp),
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = "Int64"
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        if step_is_one:
            lines.append(indent + "    " + target_name + " += 1")
        else:
            lines.append(indent + "    " + target_name + " += " + step_tmp)
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if id.get("kind") == "RuntimeIterForPlan":
        iter_expr = _render_expr(id.get("iter_expr"))
        iter_tmp = _fresh_tmp(ctx, "iter")
        idx_tmp = _fresh_tmp(ctx, "i")
        lines.append(indent + "let " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
        lines.append(indent + "var " + idx_tmp + ": Int64 = 0")
        lines.append(indent + "while " + idx_tmp + " < Int64(" + iter_tmp + ".count) {")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": idx_tmp + " += 1",
        }
        target_kind = td.get("kind")
        if target_kind == "NameTarget":
            target_name = _safe_ident(td.get("id"), "item")
            if target_name == "_":
                target_name = _fresh_tmp(ctx, "item")
            target_type = _swift_type(td.get("target_type"), allow_void=False)
            rhs = iter_tmp + "[Int(" + idx_tmp + ")]"
            if target_type == "Any":
                lines.append(indent + "    let " + target_name + " = " + rhs)
            else:
                lines.append(indent + "    let " + target_name + ": " + target_type + " = " + _cast_from_any(rhs, target_type))
            _declared_set(body_ctx).add(target_name)
            _type_map(body_ctx)[target_name] = target_type
        elif target_kind == "TupleTarget":
            tuple_tmp = _fresh_tmp(ctx, "tuple")
            lines.append(indent + "    let " + tuple_tmp + " = __pytra_as_list(" + iter_tmp + "[Int(" + idx_tmp + ")])")
            elems_any = td.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            i = 0
            while i < len(elems):
                elem = elems[i]
                if not isinstance(elem, dict):
                    raise RuntimeError("swift native emitter: unsupported RuntimeIter tuple target element")
                ed2: dict[str, Any] = elem
                if ed2.get("kind") != "NameTarget":
                    raise RuntimeError("swift native emitter: unsupported RuntimeIter tuple target element")
                name = _safe_ident(ed2.get("id"), "item_" + str(i))
                if name != "_":
                    elem_type = _swift_type(ed2.get("target_type"), allow_void=False)
                    rhs = tuple_tmp + "[Int(" + str(i) + ")]"
                    if elem_type == "Any":
                        lines.append(indent + "    let " + name + " = " + rhs)
                    else:
                        lines.append(indent + "    let " + name + ": " + elem_type + " = " + _cast_from_any(rhs, elem_type))
                    _declared_set(body_ctx).add(name)
                    _type_map(body_ctx)[name] = elem_type
                i += 1
        else:
            raise RuntimeError("swift native emitter: unsupported RuntimeIter target_plan")
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
    if not isinstance(target_any, dict):
        return None
    td: dict[str, Any] = target_any
    if td.get("kind") != "Tuple":
        return None
    elems_any = td.get("elements")
    elems = elems_any if isinstance(elems_any, list) else []
    if len(elems) == 0:
        return None

    tuple_tmp = _fresh_tmp(ctx, "tuple")
    lines: list[str] = [indent + "let " + tuple_tmp + " = __pytra_as_list(" + _render_expr(value_any) + ")"]
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    tuple_types = _tuple_element_types(decl_type_any)
    if len(tuple_types) == 0 and isinstance(value_any, dict):
        vad: dict[str, Any] = value_any
        tuple_types = _tuple_element_types(vad.get("resolved_type"))

    i = 0
    while i < len(elems):
        elem = elems[i]
        if not isinstance(elem, dict):
            return None
        ed: dict[str, Any] = elem
        kind = ed.get("kind")
        rhs = tuple_tmp + "[" + str(i) + "]"
        elem_type = "Any"
        if i < len(tuple_types):
            elem_type = _swift_type(tuple_types[i], allow_void=False)
        casted = _cast_from_any(rhs, elem_type)

        if kind == "Name":
            name = _safe_ident(ed.get("id"), "tmp_" + str(i))
            if name not in declared:
                lines.append(indent + "var " + name + ": " + elem_type + " = " + casted)
                declared.add(name)
                type_map[name] = elem_type
            else:
                lines.append(indent + name + " = " + casted)
        elif kind == "Subscript":
            lines.extend(_emit_subscript_store(elem, casted, indent=indent, ctx=ctx))
        else:
            return None
        i += 1

    return lines


def _emit_subscript_store(target: dict[str, Any], value_expr: str, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    owner_node = target.get("value")
    owner_expr = _render_expr(owner_node)
    index_expr = _render_expr(target.get("slice"))
    # Fast path for nested list store: grid[y][x] = v
    # Keep mutation in-place by materializing inner list and writing it back.
    if isinstance(owner_node, dict) and owner_node.get("kind") == "Subscript":
        outer_owner_node = owner_node.get("value")
        outer_index_expr = _render_expr(owner_node.get("slice"))
        if isinstance(outer_owner_node, dict) and outer_owner_node.get("kind") == "Name":
            outer_name = _safe_ident(outer_owner_node.get("id"), "")
            outer_type_any = _type_map(ctx).get(outer_name)
            outer_type = outer_type_any if isinstance(outer_type_any, str) else ""
            if outer_type == "[Any]":
                outer_idx_tmp = _fresh_tmp(ctx, "idx")
                inner_tmp = _fresh_tmp(ctx, "inner")
                inner_idx_tmp = _fresh_tmp(ctx, "idx")
                return [
                    indent
                    + "let "
                    + outer_idx_tmp
                    + " = Int(__pytra_index(__pytra_int("
                    + outer_index_expr
                    + "), Int64("
                    + outer_name
                    + ".count)))",
                    indent + "if " + outer_idx_tmp + " >= 0 && " + outer_idx_tmp + " < " + outer_name + ".count {",
                    indent + "    var " + inner_tmp + ": [Any] = __pytra_as_list(" + outer_name + "[" + outer_idx_tmp + "])",
                    indent
                    + "    let "
                    + inner_idx_tmp
                    + " = Int(__pytra_index(__pytra_int("
                    + index_expr
                    + "), Int64("
                    + inner_tmp
                    + ".count)))",
                    indent + "    if " + inner_idx_tmp + " >= 0 && " + inner_idx_tmp + " < " + inner_tmp + ".count {",
                    indent + "        " + inner_tmp + "[" + inner_idx_tmp + "] = " + value_expr,
                    indent + "        " + outer_name + "[" + outer_idx_tmp + "] = " + inner_tmp,
                    indent + "    }",
                    indent + "}",
                ]
    if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
        owner_name = _safe_ident(owner_node.get("id"), "")
        owner_type_any = _type_map(ctx).get(owner_name)
        owner_type = owner_type_any if isinstance(owner_type_any, str) else ""
        if owner_type == "[Any]":
            idx_tmp = _fresh_tmp(ctx, "idx")
            lines = [
                indent + "let " + idx_tmp + " = Int(__pytra_index(__pytra_int(" + index_expr + "), Int64(" + owner_name + ".count)))",
                indent + "if " + idx_tmp + " >= 0 && " + idx_tmp + " < " + owner_name + ".count {",
                indent + "    " + owner_name + "[" + idx_tmp + "] = " + value_expr,
                indent + "}",
            ]
            alias_root = _alias_map(ctx).get(owner_name, "")
            if alias_root != "":
                lines.append(indent + alias_root + " = " + owner_name)
            return lines
        if owner_type == "[AnyHashable: Any]":
            lines = [indent + owner_name + "[AnyHashable(__pytra_str(" + index_expr + "))] = " + value_expr]
            alias_root = _alias_map(ctx).get(owner_name, "")
            if alias_root != "":
                lines.append(indent + alias_root + " = " + owner_name)
            return lines
    return [indent + "__pytra_setIndex(" + owner_expr + ", " + index_expr + ", " + value_expr + ")"]


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        raise RuntimeError("swift native emitter: unsupported statement")
    sd2: dict[str, Any] = stmt
    kind = sd2.get("kind")

    if kind == "Return":
        if "value" in stmt and sd2.get("value") is not None:
            value_node = sd2.get("value")
            value = _render_expr(value_node)
            return_type_any = ctx.get("return_type")
            return_type = return_type_any if isinstance(return_type_any, str) else ""
            if (
                return_type in {"Int64", "Double"}
                and isinstance(value_node, dict)
                and value_node.get("kind") == "BinOp"
            ):
                value = _render_binop_as_type(value_node, return_type)
            elif return_type not in {"", "Any"} and _needs_cast(value_node, return_type, _type_map(ctx)):
                value = _cast_from_any(value, return_type)
            return [indent + "return " + value]
        return [indent + "return"]

    if kind == "Expr":
        value_any = sd2.get("value")
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
                        alias_root = _alias_map(ctx).get(owner_name, "") if isinstance(owner_any, dict) and owner_any.get("kind") == "Name" else ""
                        if owner_type == "[Any]":
                            lines = [indent + owner + ".append(" + _render_expr(args[0]) + ")"]
                            if alias_root != "":
                                lines.append(indent + alias_root + " = " + owner)
                            return lines
                        lines = [indent + owner + " = __pytra_as_list(" + owner + "); " + owner + ".append(" + _render_expr(args[0]) + ")"]
                        if alias_root != "":
                            lines.append(indent + alias_root + " = " + owner)
                        return lines
                if attr == "pop":
                    owner = _render_expr(func_any.get("value"))
                    args_any = value_any.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) == 0:
                        alias_root = ""
                        owner_node = func_any.get("value")
                        if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                            alias_root = _alias_map(ctx).get(_safe_ident(owner_node.get("id"), ""), "")
                        lines = [indent + owner + " = __pytra_pop_last(__pytra_as_list(" + owner + "))"]
                        if alias_root != "":
                            lines.append(indent + alias_root + " = " + owner)
                        return lines
                if attr == "add":
                    owner_node = func_any.get("value")
                    if isinstance(owner_node, dict) and owner_node.get("kind") == "Subscript":
                        sub_owner_any = owner_node.get("value")
                        sub_index_any = owner_node.get("slice")
                        args_any = value_any.get("args")
                        args = args_any if isinstance(args_any, list) else []
                        if (
                            isinstance(sub_owner_any, dict)
                            and sub_owner_any.get("kind") == "Name"
                            and len(args) == 1
                        ):
                            outer_name = _safe_ident(sub_owner_any.get("id"), "")
                            outer_type_any = _type_map(ctx).get(outer_name)
                            outer_type = outer_type_any if isinstance(outer_type_any, str) else ""
                            if outer_type == "[Any]":
                                idx_expr = _render_expr(sub_index_any)
                                idx_tmp = _fresh_tmp(ctx, "idx")
                                set_tmp = _fresh_tmp(ctx, "set")
                                return [
                                    indent + "let " + idx_tmp + " = Int(__pytra_index(__pytra_int(" + idx_expr + "), Int64(" + outer_name + ".count)))",
                                    indent + "if " + idx_tmp + " >= 0 && " + idx_tmp + " < " + outer_name + ".count {",
                                    indent + "    var " + set_tmp + ": [Any] = __pytra_as_list(" + outer_name + "[" + idx_tmp + "])",
                                    indent + "    __pytra_set_add(&" + set_tmp + ", " + _render_expr(args[0]) + ")",
                                    indent + "    " + outer_name + "[" + idx_tmp + "] = " + set_tmp,
                                    indent + "}",
                                ]
        return [indent + _render_expr(value_any)]

    if kind == "AnnAssign":
        target_any = sd2.get("target")
        if isinstance(target_any, dict) and target_any.get("kind") == "Attribute":
            return [indent + _render_attribute_expr(target_any) + " = " + _render_expr(sd2.get("value"))]

        tuple_lines = _emit_tuple_assign(
            target_any,
            sd2.get("value"),
            decl_type_any=(sd2.get("decl_type") or sd2.get("annotation")),
            declare_hint=(sd2.get("declare") is not False),
            indent=indent,
            ctx=ctx,
        )
        if tuple_lines is not None:
            return tuple_lines

        target = _target_name(target_any)
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        swift_type = _swift_type(sd2.get("decl_type") or sd2.get("annotation"), allow_void=False)
        if swift_type == "Any":
            inferred = _infer_swift_type(sd2.get("value"), _type_map(ctx))
            if inferred != "Any":
                swift_type = inferred

        stmt_value = sd2.get("value")
        if stmt_value is None:
            value = _default_return_expr(swift_type)
        else:
            value = _render_expr(stmt_value)
            if swift_type != "Any" and _needs_cast(stmt_value, swift_type, _type_map(ctx)):
                value = _cast_from_any(value, swift_type)
            materialized = _materialize_container_value_from_ref(
                stmt_value,
                target_type=swift_type,
                target_name=target,
                ctx=ctx,
            )
            if materialized is not None:
                value = materialized
        if sd2.get("declare") is False or target in declared:
            if target not in declared:
                declared.add(target)
                type_map[target] = swift_type
                return [indent + "var " + target + ": " + swift_type + " = " + value]
            if target in type_map and type_map[target] != "Any":
                if stmt_value is None:
                    return [indent + target + " = " + _default_return_expr(type_map[target])]
                reassigned = _render_expr(stmt_value)
                if _needs_cast(stmt_value, type_map[target], _type_map(ctx)):
                    reassigned = _cast_from_any(reassigned, type_map[target])
                materialized_reassigned = _materialize_container_value_from_ref(
                    stmt_value,
                    target_type=type_map[target],
                    target_name=target,
                    ctx=ctx,
                )
                if materialized_reassigned is not None:
                    reassigned = materialized_reassigned
                return [indent + target + " = " + reassigned]
            return [indent + target + " = " + value]

        declared.add(target)
        type_map[target] = swift_type
        return [indent + "var " + target + ": " + swift_type + " = " + value]

    if kind == "Assign":
        targets_any = sd2.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(sd2.get("target"), dict):
            targets = [sd2.get("target")]
        if len(targets) == 0:
            raise RuntimeError("swift native emitter: Assign without target")

        tuple_lines = _emit_tuple_assign(
            targets[0],
            sd2.get("value"),
            decl_type_any=sd2.get("decl_type"),
            declare_hint=bool(sd2.get("declare")),
            indent=indent,
            ctx=ctx,
        )
        if tuple_lines is not None:
            return tuple_lines

        if isinstance(targets[0], dict) and targets[0].get("kind") == "Attribute":
            lhs_attr = _render_attribute_expr(targets[0])
            value_attr = _render_expr(sd2.get("value"))
            return [indent + lhs_attr + " = " + value_attr]

        if isinstance(targets[0], dict) and targets[0].get("kind") == "Subscript":
            tgt = targets[0]
            value = _render_expr(sd2.get("value"))
            return _emit_subscript_store(tgt, value, indent=indent, ctx=ctx)

        lhs = _target_name(targets[0])
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        value = _render_expr(sd2.get("value"))

        if sd2.get("declare"):
            if lhs in declared:
                _alias_map(ctx).pop(lhs, None)
                if lhs in type_map and type_map[lhs] != "Any":
                    if _needs_cast(sd2.get("value"), type_map[lhs], _type_map(ctx)):
                        value = _cast_from_any(value, type_map[lhs])
                    materialized_existing = _materialize_container_value_from_ref(
                        sd2.get("value"),
                        target_type=type_map[lhs],
                        target_name=lhs,
                        ctx=ctx,
                    )
                    if materialized_existing is not None:
                        value = materialized_existing
                return [indent + lhs + " = " + value]
            swift_type = _swift_type(sd2.get("decl_type"), allow_void=False)
            if swift_type == "Any":
                inferred = _infer_swift_type(sd2.get("value"), _type_map(ctx))
                if inferred != "Any":
                    swift_type = inferred
            if swift_type != "Any" and _needs_cast(sd2.get("value"), swift_type, _type_map(ctx)):
                value = _cast_from_any(value, swift_type)
            _alias_map(ctx).pop(lhs, None)
            if isinstance(sd2.get("value"), dict) and sd2.get("value").get("kind") == "Name":
                source_name = _safe_ident(sd2.get("value").get("id"), "")
                source_type = _type_map(ctx).get(source_name, "")
                if swift_type in {"[Any]", "[AnyHashable: Any]"} and source_type == swift_type:
                    _alias_map(ctx)[lhs] = source_name
            materialized_decl = _materialize_container_value_from_ref(
                sd2.get("value"),
                target_type=swift_type,
                target_name=lhs,
                ctx=ctx,
            )
            if materialized_decl is not None:
                value = materialized_decl
            declared.add(lhs)
            type_map[lhs] = swift_type
            return [indent + "var " + lhs + ": " + swift_type + " = " + value]

        if lhs not in declared:
            inferred = _infer_swift_type(sd2.get("value"), _type_map(ctx))
            declared.add(lhs)
            type_map[lhs] = inferred
            if inferred != "Any" and _needs_cast(sd2.get("value"), inferred, _type_map(ctx)):
                value = _cast_from_any(value, inferred)
            _alias_map(ctx).pop(lhs, None)
            if isinstance(sd2.get("value"), dict) and sd2.get("value").get("kind") == "Name":
                source_name = _safe_ident(sd2.get("value").get("id"), "")
                source_type = _type_map(ctx).get(source_name, "")
                if inferred in {"[Any]", "[AnyHashable: Any]"} and source_type == inferred:
                    _alias_map(ctx)[lhs] = source_name
            materialized_inferred = _materialize_container_value_from_ref(
                sd2.get("value"),
                target_type=inferred,
                target_name=lhs,
                ctx=ctx,
            )
            if materialized_inferred is not None:
                value = materialized_inferred
            return [indent + "var " + lhs + ": " + inferred + " = " + value]
        if lhs in type_map and type_map[lhs] != "Any":
            if _needs_cast(sd2.get("value"), type_map[lhs], _type_map(ctx)):
                value = _cast_from_any(value, type_map[lhs])
            _alias_map(ctx).pop(lhs, None)
            materialized_known = _materialize_container_value_from_ref(
                sd2.get("value"),
                target_type=type_map[lhs],
                target_name=lhs,
                ctx=ctx,
            )
            if materialized_known is not None:
                value = materialized_known
        return [indent + lhs + " = " + value]

    if kind == "AugAssign":
        lhs = _target_name(sd2.get("target"))
        rhs = _render_expr(sd2.get("value"))
        lhs_type_any = _type_map(ctx).get(lhs)
        lhs_type = lhs_type_any if isinstance(lhs_type_any, str) else ""
        if lhs_type not in {"", "Any"} and _needs_cast(sd2.get("value"), lhs_type, _type_map(ctx)):
            rhs = _cast_from_any(rhs, lhs_type)
        op = sd2.get("op")
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
        return _emit_swap(stmt, indent=indent, ctx=ctx)

    if kind == "If":
        test_expr = _render_truthy_expr(sd2.get("test"))
        lines: list[str] = [indent + "if " + test_expr + " {"]
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": ctx.get("continue_prefix", ""),
        }
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1

        orelse_any = sd2.get("orelse")
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
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
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
        lines = [indent + "do {"]
        lines.extend(_emit_for_core(stmt, indent=indent + "    ", ctx=ctx))
        lines.append(indent + "}")
        return lines

    if kind == "While":
        test_expr = _render_truthy_expr(sd2.get("test"))
        lines = [indent + "while " + test_expr + " {"]
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
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
        return [indent + "_ = 0"]

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

    if kind == "FunctionDef" or kind == "ClosureDef":
        fn_name = _safe_ident(sd2.get("name"), "")
        if fn_name != "":
            _INOUT_PARAM_POSITIONS[0][fn_name] = _collect_inout_param_positions(sd2, drop_self=False)
        return _emit_function(sd2, indent=indent, receiver_name=None)

    if kind == "Raise":
        exc_any = sd2.get("exc")
        if isinstance(exc_any, dict):
            return [indent + "throw " + _render_expr(exc_any)]
        current_exc_any = ctx.get("current_exc_var")
        current_exc = current_exc_any if isinstance(current_exc_any, str) else ""
        if current_exc != "":
            return [indent + "throw " + current_exc]
        return [indent + "throw RuntimeError(\"pytra raise\")"]

    if kind == "Try":
        lines: list[str] = []
        final_any = sd2.get("finalbody")
        final = final_any if isinstance(final_any, list) else []
        if len(final) > 0:
            lines.append(indent + "defer {")
            final_ctx: dict[str, Any] = {
                "tmp": ctx.get("tmp", 0),
                "declared": set(_declared_set(ctx)),
                "types": dict(_type_map(ctx)),
                "ref_vars": set(_ref_var_set(ctx)),
                "alias_map": dict(_alias_map(ctx)),
                "return_type": ctx.get("return_type", ""),
                "continue_prefix": ctx.get("continue_prefix", ""),
                "current_exc_var": ctx.get("current_exc_var", ""),
            }
            i = 0
            while i < len(final):
                lines.extend(_emit_stmt(final[i], indent=indent + "    ", ctx=final_ctx))
                i += 1
            lines.append(indent + "}")
        lines.append(indent + "do {")
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        handlers_any = sd2.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        i = 0
        while i < len(handlers):
            h = handlers[i]
            if isinstance(h, dict):
                hd: dict[str, Any] = h
                h_body_any = hd.get("body")
                h_body = h_body_any if isinstance(h_body_any, list) else []
                handler_name_any = hd.get("name")
                handler_name = _safe_ident(handler_name_any, "err") if isinstance(handler_name_any, str) and handler_name_any != "" else "err"
                handler_type_any = hd.get("type")
                if isinstance(handler_type_any, dict) and handler_type_any.get("kind") == "Name":
                    lines.append(indent + "} catch let " + handler_name + " as " + _safe_ident(handler_type_any.get("id"), "Exception") + " {")
                else:
                    lines.append(indent + "} catch {")
                    lines.append(indent + "    let " + handler_name + " = error")
                handler_ctx: dict[str, Any] = {
                    "tmp": ctx.get("tmp", 0),
                    "declared": set(_declared_set(ctx)),
                    "types": dict(_type_map(ctx)),
                    "ref_vars": set(_ref_var_set(ctx)),
                    "alias_map": dict(_alias_map(ctx)),
                    "return_type": ctx.get("return_type", ""),
                    "continue_prefix": ctx.get("continue_prefix", ""),
                    "current_exc_var": handler_name,
                }
                _declared_set(handler_ctx).add(handler_name)
                _type_map(handler_ctx)[handler_name] = "Any"
                j = 0
                while j < len(h_body):
                    lines.extend(_emit_stmt(h_body[j], indent=indent + "    ", ctx=handler_ctx))
                    j += 1
            i += 1
        orelse_any = sd2.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        if len(handlers) == 0:
            lines.append(indent + "} catch {")
            lines.append(indent + "    throw error")
        i = 0
        while i < len(orelse):
            lines.extend(_emit_stmt(orelse[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines

    if kind == "VarDecl":
        name = _safe_ident(sd2.get("name"), "v")
        var_type = _swift_type(sd2.get("type"), allow_void=False)
        type_map = _type_map(ctx)
        type_map[name] = var_type
        declared = _declared_set(ctx)
        declared.add(name)
        return [indent + "var " + name + ": " + var_type + " = " + _default_return_expr(var_type)]

    if kind == "ForRange":
        tgt = _safe_ident(sd2.get("target", {}).get("id") if isinstance(sd2.get("target"), dict) else None, "i")
        start_raw = _render_expr(sd2.get("start"))
        stop_raw = _render_expr(sd2.get("stop"))
        step_raw = _render_expr(sd2.get("step"))
        # Normalize to Int for stride compatibility
        start = "Int(" + start_raw + ")"
        stop = "Int(" + stop_raw + ")"
        step = step_raw
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        if step_raw == "1" or step_raw == "Int64(1)":
            header = "for " + tgt + " in " + start + "..<" + stop
        elif step_raw == "-1" or step_raw == "Int64(-1)":
            header = "for " + tgt + " in stride(from: " + start + ", to: " + stop + ", by: -1)"
        else:
            header = "for " + tgt + " in stride(from: " + start + ", to: " + stop + ", by: Int(" + step + "))"
        lines = [indent + header + " {"]
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": "",
        }
        declared = _declared_set(body_ctx)
        declared.add(tgt)
        type_map = _type_map(body_ctx)
        type_map[tgt] = "Int"
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    raise RuntimeError("swift native emitter: unsupported stmt kind: " + str(kind))


def _stmt_guarantees_return(stmt: Any) -> bool:
    if not isinstance(stmt, dict):
        return False
    sd: dict[str, Any] = stmt
    kind = sd.get("kind")
    if kind == "Return":
        return True
    if kind != "If":
        return False
    body_any = sd.get("body")
    body = body_any if isinstance(body_any, list) else []
    orelse_any = sd.get("orelse")
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


def _emit_function(
    fn: dict[str, Any],
    *,
    indent: str,
    receiver_name: str | None = None,
    in_class_name: str | None = None,
) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    is_init = receiver_name is not None and name == "__init__"
    decorators_any = fn.get("decorators")
    decorators = decorators_any if isinstance(decorators_any, list) else []
    is_staticmethod = receiver_name is not None and "staticmethod" in decorators
    is_property = receiver_name is not None and "property" in decorators

    # @extern functions → delegate to _native module
    if "extern" in decorators and receiver_name is None:
        return_type = _function_return_swift_type(fn, allow_void=True)
        drop_self = False
        params = _function_params(fn, drop_self=drop_self, use_any=False)
        param_names = _function_param_names(fn, drop_self=drop_self)
        sig = indent + "func " + name + "(" + ", ".join(params) + ")"
        if return_type != "Void":
            sig += " -> " + return_type
        # Determine native function prefix from _extern_module_stem (set by caller)
        native_prefix = fn.get("_extern_module_stem", "") + "_native_"
        if native_prefix == "_native_":
            native_prefix = ""
        call_args = ", ".join(p.split(":")[0].strip() for p in param_names)
        delegate = native_prefix + name + "(" + call_args + ")"
        if return_type != "Void":
            return [sig + " {", indent + "    return " + delegate, indent + "}"]
        return [sig + " {", indent + "    " + delegate, indent + "}"]

    return_type = _function_return_swift_type(fn, allow_void=True)
    if is_init:
        return_type = "Void"

    drop_self = receiver_name is not None
    params = _function_params(fn, drop_self=drop_self)
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    body_called_names = _stmt_called_function_names({"kind": "Block", "body": body})
    implicit_throw_via_main_alias = (
        receiver_name is None
        and _MAIN_CALL_ALIAS[0] != ""
        and "main" in body_called_names
        and _MAIN_CALL_ALIAS[0] in _THROWING_FUNCTIONS[0]
    )

    lines: list[str] = []
    if is_property:
        prop_sig = indent + "var " + name + ": " + return_type + " {"
        lines.append(prop_sig)
    elif is_init:
        init_prefix = "override " if receiver_name is not None and in_class_name is not None and _class_has_base_method(in_class_name, "__init__") else ""
        lines.append(indent + init_prefix + "init(" + ", ".join(params) + ") {")
    else:
        fn_prefix = ""
        if is_staticmethod:
            fn_prefix = "static "
        elif receiver_name is not None and in_class_name is not None and _class_has_base_method(in_class_name, name):
            fn_prefix = "override "
        sig = indent + fn_prefix + "func " + name + "(" + ", ".join(params) + ")"
        if receiver_name is None and (name in _THROWING_FUNCTIONS[0] or implicit_throw_via_main_alias):
            sig += " throws"
        if return_type != "Void":
            sig += " -> " + return_type
        lines.append(sig + " {")

    ctx: dict[str, Any] = {
        "tmp": 0,
        "declared": set(),
        "types": {},
        "ref_vars": set(),
        "alias_map": {},
        "return_type": return_type,
        "continue_prefix": "",
    }
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    ref_vars = _ref_var_set(ctx)

    param_names = _function_param_names(fn, drop_self=drop_self)
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    inout_positions = _collect_inout_param_positions(fn, drop_self=drop_self)
    # Swift parameters are immutable (let); detect reassigned params
    reassigned = collect_reassigned_params(fn)
    mutable_copies: list[tuple[str, str]] = []
    i = 0
    while i < len(param_names):
        p = param_names[i]
        declared.add(p)
        arg_type = arg_types.get(p)
        type_map[p] = _swift_type(arg_type, allow_void=False)
        if _is_container_east_type(arg_type):
            ref_vars.add(p)
        if p in reassigned:
            mutable_copies.append((p, mutable_param_name(p)))
        i += 1

    # Emit type-cast shadows for parameters declared as Any
    param_cast_names: set[str] = set()
    j = 0
    while j < len(param_names):
        p = param_names[j]
        if j in inout_positions:
            j += 1
            continue
        original_type = _swift_type(arg_types.get(p), allow_void=False)
        if original_type != "Any" and p not in reassigned:
            cast_fn = ""
            if original_type == "Int64":
                cast_fn = "__pytra_int"
            elif original_type == "Double":
                cast_fn = "__pytra_float"
            elif original_type == "String":
                cast_fn = "__pytra_str"
            elif original_type == "Bool":
                cast_fn = "__pytra_truthy"
            elif original_type == "[Any]":
                cast_fn = "__pytra_as_list"
            if cast_fn != "":
                # Container types use var (may need mutating methods like .append)
                decl_keyword = "var" if original_type == "[Any]" or original_type == "[AnyHashable: Any]" else "let"
                lines.append(indent + "    " + decl_keyword + " " + p + ": " + original_type + " = " + cast_fn + "(" + p + ")")
                param_cast_names.add(p)
        j += 1
    # Emit mutable copies for reassigned params
    for orig, renamed in mutable_copies:
        original_type = _swift_type(arg_types.get(orig), allow_void=False)
        cast_fn = ""
        if original_type == "Int64":
            cast_fn = "__pytra_int"
        elif original_type == "Double":
            cast_fn = "__pytra_float"
        elif original_type == "String":
            cast_fn = "__pytra_str"
        if cast_fn != "":
            lines.append(indent + "    var " + orig + ": " + original_type + " = " + cast_fn + "(" + renamed + ")")
        else:
            lines.append(indent + "    var " + orig + " = " + renamed)

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
    is_dataclass = bool(cls.get("dataclass"))
    meta_any = cls.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    is_trait = isinstance(meta.get("trait_v1"), dict) or "trait" in (cls.get("decorators") or [])
    implements_traits: list[str] = []
    implements_meta = meta.get("implements_v1")
    if isinstance(implements_meta, dict):
        traits_any = implements_meta.get("traits")
        if isinstance(traits_any, list):
            for trait_any in traits_any:
                if isinstance(trait_any, str) and trait_any != "":
                    implements_traits.append(_safe_ident(trait_any, "Trait"))
    supertypes: list[str] = []
    if base_name != "":
        supertypes.append(base_name)
    i = 0
    while i < len(implements_traits):
        if implements_traits[i] not in supertypes:
            supertypes.append(implements_traits[i])
        i += 1
    extends = ": " + ", ".join(supertypes) if len(supertypes) > 0 else ""

    lines: list[str] = []
    if base_name in {"IntEnum", "IntFlag"}:
        lines.append(indent + "enum " + class_name + " {")
    else:
        lines.append(indent + ("protocol " if is_trait else "class ") + class_name + extends + " {")

    field_types_any = cls.get("field_types")
    field_types = field_types_any if isinstance(field_types_any, dict) else {}
    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []
    if is_trait:
        i = 0
        while i < len(body):
            node = body[i]
            if isinstance(node, dict) and node.get("kind") in {"FunctionDef", "ClosureDef"}:
                fn_name = _safe_ident(node.get("name"), "func")
                drop_self = True
                params = _function_params(node, drop_self=drop_self, use_any=False)
                return_type = _function_return_swift_type(node, allow_void=True)
                sig = indent + "    func " + fn_name + "(" + ", ".join(params) + ")"
                if return_type != "Void":
                    sig += " -> " + return_type
                lines.append(sig)
            i += 1
        lines.append(indent + "}")
        return lines
    if base_name in {"Enum", "IntEnum", "IntFlag"}:
        i = 0
        while i < len(body):
            node = body[i]
            if isinstance(node, dict) and node.get("kind") == "Assign":
                target_any = node.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    member_name = _safe_ident(target_any.get("id"), "")
                    value_any = node.get("value")
                    if member_name != "" and isinstance(value_any, dict):
                        if base_name == "Enum":
                            lines.append(indent + "    static let " + member_name + " = " + class_name + "(" + _render_expr(value_any) + ")")
                        else:
                            lines.append(indent + "    static let " + member_name + ": Int64 = " + _to_int_expr(_render_expr(value_any)))
            i += 1
        lines.append(indent + "}")
        return lines
    static_field_specs: dict[str, tuple[str, str, bool]] = {}
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "AnnAssign":
            target_any = node.get("target")
            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                raw_name = target_any.get("id")
                if isinstance(raw_name, str) and raw_name != "":
                    field_name = _safe_ident(raw_name, "field")
                    if node.get("value") is not None:
                        field_type = _swift_type(node.get("decl_type") or node.get("annotation"), allow_void=False)
                        default_expr = _render_expr(node.get("value"))
                        static_field_specs[field_name] = (field_type, default_expr, True)
        if isinstance(node, dict) and node.get("kind") == "Assign":
            target_any = node.get("target")
            if not isinstance(target_any, dict):
                targets_any = node.get("targets")
                targets = targets_any if isinstance(targets_any, list) else []
                if len(targets) == 1 and isinstance(targets[0], dict):
                    target_any = targets[0]
            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                raw_name = target_any.get("id")
                value_any = node.get("value")
                if isinstance(raw_name, str) and raw_name != "" and isinstance(value_any, dict):
                    field_name = _safe_ident(raw_name, "field")
                    field_type = _swift_type(
                        node.get("decl_type") or value_any.get("resolved_type"),
                        allow_void=False,
                    )
                    default_expr = _render_expr(value_any)
                    static_field_specs[field_name] = (field_type, default_expr, True)
        i += 1
    field_specs: list[tuple[str, str, str, str | None, bool]] = []
    seen_fields: set[str] = set()
    for raw_name, raw_type in field_types.items():
        if not isinstance(raw_name, str):
            continue
        field_name = _safe_ident(raw_name, "field")
        seen_fields.add(field_name)
        field_type = _swift_type(raw_type, allow_void=False)
        spec = static_field_specs.get(field_name)
        default_expr = spec[1] if spec is not None and spec[1] != "" else None
        default_value = default_expr if default_expr is not None else _default_return_expr(field_type)
        if default_value == "":
            default_value = "__pytra_any_default()"
        is_static_field = (not is_dataclass) and spec is not None and spec[2]
        field_specs.append((field_name, field_type, default_value, default_expr, is_static_field))
        if is_dataclass:
            lines.append(indent + "    var " + field_name + ": " + field_type + " = " + default_value)
        elif is_static_field:
            lines.append(indent + "    static var " + field_name + ": " + field_type + " = " + default_value)
        else:
            lines.append(indent + "    var " + field_name + ": " + field_type + " = " + default_value)
    for field_name, (field_type, default_expr, is_static_field) in static_field_specs.items():
        if field_name in seen_fields or is_dataclass:
            continue
        default_value = default_expr if default_expr != "" else _default_return_expr(field_type)
        if default_value == "":
            default_value = "__pytra_any_default()"
        field_specs.append((field_name, field_type, default_value, default_expr if default_expr != "" else None, is_static_field))
        if is_static_field:
            lines.append(indent + "    static var " + field_name + ": " + field_type + " = " + default_value)
        else:
            lines.append(indent + "    var " + field_name + ": " + field_type + " = " + default_value)

    has_init = False
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") in {"FunctionDef", "ClosureDef"}:
            if _safe_ident(node.get("name"), "") == "__init__":
                has_init = True
            lines.append("")
            lines.extend(
                _emit_function(
                    node,
                    indent=indent + "    ",
                    receiver_name=class_name,
                    in_class_name=class_name,
                )
            )
        i += 1

    if not has_init:
        if len(body) > 0:
            lines.append("")
        init_prefix = "override " if base_name != "" else ""
        lines.append(indent + "    " + init_prefix + "init() {")
        if base_name != "":
            lines.append(indent + "        super.init()")
        for field_name, _, default_value, _, is_static_field in field_specs:
            if is_static_field:
                continue
            lines.append(indent + "        self." + field_name + " = " + default_value)
        lines.append(indent + "    }")
        init_fields = [spec for spec in field_specs if not spec[4]]
        if len(init_fields) > 0:
            lines.append("")
            params: list[str] = []
            for field_name, field_type, _, default_expr, _ in init_fields:
                param = "_ " + field_name + ": " + field_type
                if is_dataclass and default_expr is not None:
                    param += " = " + default_expr
                params.append(param)
            init_prefix = "override " if base_name != "" else ""
            lines.append(indent + "    " + init_prefix + "init(" + ", ".join(params) + ") {")
            if base_name != "":
                lines.append(indent + "        super.init()")
            for field_name, _, _, _, _ in init_fields:
                lines.append(indent + "        self." + field_name + " = " + field_name)
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
        "func __pytra_assert_true(_ cond: Any?, _ label: Any? = nil) -> Bool {",
        "    _ = label",
        "    return __pytra_truthy(cond)",
        "}",
        "",
        "func __pytra_assert_eq(_ actual: Any?, _ expected: Any?, _ label: Any? = nil) -> Bool {",
        "    _ = label",
        "    return __pytra_str(actual) == __pytra_str(expected)",
        "}",
        "",
        "func __pytra_assert_all(_ items: Any?, _ label: Any? = nil) -> Bool {",
        "    _ = label",
        "    if let arr = items as? [Any] {",
        "        for item in arr {",
        "            if !__pytra_truthy(item) { return false }",
        "        }",
        "        return true",
        "    }",
        "    return __pytra_truthy(items)",
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
        "func __pytra_py_to_string(_ v: Any?) -> String {",
        "    return __pytra_str(v)",
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
        "func __pytra_set_literal(_ items: [Any]) -> [Any] {",
        "    var out: [Any] = []",
        "    for item in items {",
        "        if !__pytra_contains(out, item) { out.append(item) }",
        "    }",
        "    return out",
        "}",
        "",
        "func __pytra_set_add(_ items: inout [Any], _ value: Any?) {",
        "    if !__pytra_contains(items, value) { items.append(value as Any) }",
        "}",
        "",
        "func __pytra_dict_pop(_ dict: inout [AnyHashable: Any], _ key: Any?) -> Any {",
        "    let hashed = AnyHashable(__pytra_str(key))",
        "    let value = dict[hashed] ?? __pytra_any_default()",
        "    dict.removeValue(forKey: hashed)",
        "    return value",
        "}",
        "",
        "func __pytra_dict_setdefault(_ dict: inout [AnyHashable: Any], _ key: Any?, _ defaultValue: Any?) -> Any {",
        "    let hashed = AnyHashable(__pytra_str(key))",
        "    if let value = dict[hashed] { return value }",
        "    let stored = defaultValue as Any",
        "    dict[hashed] = stored",
        "    return stored",
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
    ed: dict[str, Any] = east_doc
    if ed.get("kind") != "Module":
        raise RuntimeError("swift native emitter: root kind must be Module")
    body_any = ed.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("swift native emitter: Module.body must be list")
    reject_backend_typed_vararg_signatures(east_doc, backend_name="Swift backend")
    meta_any = ed.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    emit_ctx_any = meta.get("emit_context")
    emit_ctx = emit_ctx_any if isinstance(emit_ctx_any, dict) else {}
    is_entry = emit_ctx.get("is_entry", True)
    module_id = emit_ctx.get("module_id", "")
    # Extract stem for @extern delegation using canonical_runtime_module_id (§1).
    # e.g., "pytra.std.time" → canonical "pytra.std.time" → stem "time"
    _extern_module_stem = ""
    if isinstance(module_id, str) and module_id != "":
        canon = canonical_runtime_module_id(module_id)
        if canon == "":
            canon = module_id
        canon_parts = canon.split(".")
        _extern_module_stem = canon_parts[-1] if len(canon_parts) > 0 else ""
    main_guard_any = ed.get("main_guard_body")
    main_guard = main_guard_any if isinstance(main_guard_any, list) else []

    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    extern_var_lines: list[str] = []
    top_level_nodes: list[dict[str, Any]] = []
    i = 0
    while i < len(body_any):
        node = body_any[i]
        if isinstance(node, dict):
            nd: dict[str, Any] = node
            kind = nd.get("kind")
            if kind == "ClassDef":
                classes.append(node)
            elif kind == "FunctionDef" or kind == "ClosureDef":
                # Attach module stem for @extern delegation
                nd["_extern_module_stem"] = _extern_module_stem
                functions.append(node)
            elif kind in {"AnnAssign", "Assign"}:
                # §4: extern() variables → delegate to _native module
                node_meta = nd.get("meta")
                ev1 = node_meta.get("extern_var_v1") if isinstance(node_meta, dict) else None
                if isinstance(ev1, dict):
                    target_any = nd.get("target")
                    if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                        var_name = _safe_ident(target_any.get("id"), "value")
                        sym_name = ev1.get("symbol", "") if isinstance(ev1.get("symbol"), str) else ""
                        if sym_name == "":
                            sym_name = var_name
                        swift_type = _swift_type(nd.get("decl_type") or nd.get("annotation"), allow_void=False)
                        native_fn = _extern_module_stem + "_native_" + sym_name
                        extern_var_lines.append("let " + var_name + ": " + swift_type + " = " + native_fn + "()")
                else:
                    top_level_nodes.append(nd)
        i += 1

    _CLASS_NAMES[0] = set()
    _CLASS_BASES[0] = {}
    _CLASS_METHODS[0] = {}
    _MAIN_CALL_ALIAS[0] = ""
    _THROWING_FUNCTIONS[0] = _collect_throwing_functions(east_doc)
    _RELATIVE_IMPORT_NAME_ALIASES[0] = _collect_relative_import_name_aliases(east_doc)
    _INOUT_PARAM_POSITIONS[0] = {}
    meta = east_doc.get("meta") if isinstance(east_doc.get("meta"), dict) else {}
    pass  # import alias resolution handled by emit_context
    i = 0
    while i < len(classes):
        cls = classes[i]
        cls_name = _safe_ident(cls.get("name"), "PytraClass")
        _CLASS_NAMES[0].add(cls_name)
        base_any = cls.get("base")
        base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
        _CLASS_BASES[0][cls_name] = base_name
        method_names: set[str] = set()
        cls_body_any = cls.get("body")
        cls_body = cls_body_any if isinstance(cls_body_any, list) else []
        j = 0
        while j < len(cls_body):
            cls_node = cls_body[j]
            if isinstance(cls_node, dict) and cls_node.get("kind") in {"FunctionDef", "ClosureDef"}:
                method_names.add(_safe_ident(cls_node.get("name"), "func"))
            j += 1
        _CLASS_METHODS[0][cls_name] = method_names
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

    has_user_main = False
    has_pytra_main = False
    user_main_symbol = "main"
    i = 0
    while i < len(functions):
        fn_name = _safe_ident(functions[i].get("name"), "")
        if fn_name == "main":
            has_user_main = True
            user_main_symbol = "main"
            break
        if fn_name == "__pytra_main":
            has_pytra_main = True
        i += 1
    if not has_user_main and has_pytra_main:
        has_user_main = True
        user_main_symbol = "__pytra_main"
        _MAIN_CALL_ALIAS[0] = "__pytra_main"
    elif has_user_main:
        _MAIN_CALL_ALIAS[0] = "main"

    i = 0
    while i < len(functions):
        fn_name = _safe_ident(functions[i].get("name"), "")
        if fn_name != "":
            _INOUT_PARAM_POSITIONS[0][fn_name] = _collect_inout_param_positions(functions[i], drop_self=False)
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

    if len(top_level_nodes) > 0:
        top_level_ctx: dict[str, Any] = {
            "tmp": 0,
            "declared": set(),
            "types": {},
            "ref_vars": set(),
            "alias_map": {},
            "return_type": "",
            "continue_prefix": "",
        }
        i = 0
        while i < len(top_level_nodes):
            lines.append("")
            lines.extend(_emit_stmt(top_level_nodes[i], indent="", ctx=top_level_ctx))
            i += 1

    # §4: extern() variable declarations (e.g., pi, e)
    if len(extern_var_lines) > 0:
        lines.append("")
        lines.extend(extern_var_lines)

    if has_user_main:
        lines.append("")
        entry_main_throws = user_main_symbol in _THROWING_FUNCTIONS[0]
        lines.append("func __pytra_entry_main()" + (" throws" if entry_main_throws else "") + " {")
        lines.append("    " + ("try " if entry_main_throws else "") + user_main_symbol + "()")
        lines.append("}")

    has_main_guard = len(main_guard) > 0
    if has_main_guard:
        lines.append("")
        lines.append("func __pytra_entry_guard() throws {")
        guard_ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}, "ref_vars": set(), "current_exc_var": ""}
        i = 0
        while i < len(main_guard):
            lines.extend(_emit_stmt(main_guard[i], indent="    ", ctx=guard_ctx))
            i += 1
        lines.append("}")

    if is_entry:
        lines.append("")
        lines.append("@main")
        lines.append("struct Main {")
        lines.append("    static func main() {")
        lines.append("        do {")
        if has_main_guard:
            lines.append("            try __pytra_entry_guard()")
        else:
            has_case_main = False
            i = 0
            while i < len(functions):
                if _safe_ident(functions[i].get("name"), "") == "_case_main":
                    has_case_main = True
                    break
                i += 1
            if has_case_main:
                lines.append("            " + ("try " if "_case_main" in _THROWING_FUNCTIONS[0] else "") + "_case_main()")
            elif has_user_main:
                lines.append("            " + ("try " if user_main_symbol in _THROWING_FUNCTIONS[0] else "") + "__pytra_entry_main()")
        lines.append("        } catch {")
        lines.append("            __pytra_py_print(__pytra_py_to_string(error))")
        lines.append("        }")
        lines.append("    }")
        lines.append("}")
    lines.append("")
    return "\n".join(lines)


def emit_swift_module(east_doc: dict[str, Any]) -> str:
    """toolchain2 entrypoint for EAST3 -> Swift source emission."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("swift emitter: east_doc must be dict")
    meta = east_doc.get("meta")
    meta_dict = meta if isinstance(meta, dict) else {}
    emit_ctx_any = meta_dict.get("emit_context")
    emit_ctx = emit_ctx_any if isinstance(emit_ctx_any, dict) else {}
    module_id_any = emit_ctx.get("module_id")
    module_id = module_id_any if isinstance(module_id_any, str) else ""
    if (
        module_id.startswith("pytra.built_in.")
        or module_id.startswith("pytra.utils.")
        or module_id == "pytra.std.os"
        or module_id == "pytra.std.env"
        or module_id == "pytra.std.os_path"
        or module_id == "pytra.std.collections"
    ):
        return ""
    return transpile_to_swift_native(east_doc)


__all__ = ["emit_swift_module", "transpile_to_swift_native"]
