"""EAST3 -> Scala 3 native emitter (core lowering stage)."""

from __future__ import annotations

from typing import Any
from toolchain.emit.common.emitter.code_emitter import (
    reject_backend_general_union_type_exprs,
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
    reject_backend_typed_vararg_signatures,
)
from toolchain.frontends.runtime_call_adapters import normalize_rendered_runtime_args
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id
from toolchain.frontends.runtime_symbol_index import resolve_import_binding_doc
from toolchain.frontends.runtime_symbol_index import lookup_runtime_module_extern_contract


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

_CLASS_NAMES: list[set[str]] = [set()]
_FUNCTION_NAMES: list[set[str]] = [set()]
_CLASS_BASES: list[dict[str, str]] = [{}]
_CLASS_METHODS: list[dict[str, set[str]]] = [{}]
_RELATIVE_IMPORT_NAME_ALIASES: dict[str, str] = {}
_PYTRA_MODULE_IMPORTS: list[set[str]] = [set()]


def _method_overrides_base(class_name: str, method_name: str) -> bool:
    base = _CLASS_BASES[0].get(class_name, "")
    seen: set[str] = set()
    while base != "":
        if base in seen:
            break
        seen.add(base)
        methods = _CLASS_METHODS[0].get(base)
        if isinstance(methods, set) and method_name in methods:
            return True
        base = _CLASS_BASES[0].get(base, "")
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


def _relative_import_module_path(module_id: str) -> str:
    module_path = module_id.lstrip(".").strip()
    if module_path == "":
        return ""
    parts = module_path.split(".")
    out: list[str] = []
    i = 0
    while i < len(parts):
        safe = _safe_ident(parts[i], "")
        if safe != "":
            out.append(safe)
        i += 1
    return ".".join(out)


def _relative_import_target_expr(module_id: str, imported_name: str) -> str:
    module_path = _relative_import_module_path(module_id)
    symbol = _safe_ident(imported_name, "")
    if module_path == "":
        return symbol
    if symbol == "":
        return module_path
    return module_path + "." + symbol


def _collect_relative_import_name_aliases(east_doc: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    wildcard_modules: dict[str, str] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        stmt = body[i]
        i += 1
        if not isinstance(stmt, dict):
            continue
        sd4: dict[str, Any] = stmt
        if sd4.get("kind") != "ImportFrom":
            continue
        module_any = sd4.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        if not module_id.startswith("."):
            continue
        names_any = sd4.get("names")
        names = names_any if isinstance(names_any, list) else []
        j = 0
        while j < len(names):
            entry = names[j]
            j += 1
            if not isinstance(entry, dict):
                continue
            imported_any = entry.get("name")
            imported_name = imported_any if isinstance(imported_any, str) else ""
            if imported_name == "":
                continue
            if imported_name == "*":
                wildcard_module = _relative_import_module_path(module_id)
                if wildcard_module != "":
                    wildcard_modules[wildcard_module] = wildcard_module
                continue
            local_any = entry.get("asname")
            local_name = local_any if isinstance(local_any, str) and local_any != "" else imported_name
            local_ident = _safe_ident(local_name, "")
            target_expr = _relative_import_target_expr(module_id, imported_name)
            if local_ident != "" and target_expr != "":
                out[local_ident] = target_expr
    if len(wildcard_modules) == 0:
        return out
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
        local_ident = _safe_ident(local_name_any, "")
        target_expr = _relative_import_target_expr(binding_module_any, binding_symbol)
        if local_ident != "" and target_expr != "":
            out[local_ident] = target_expr
            wildcard_resolved[binding_module] = True
    unresolved = [module_id for module_id, resolved in wildcard_resolved.items() if not resolved]
    if len(unresolved) > 0:
        raise RuntimeError(
            "scala native emitter: unsupported relative import form: wildcard import"
        )
    return out


def _collect_pytra_module_imports(east_doc: dict[str, Any]) -> set[str]:
    """Collect names imported as linked sub-modules from pytra.* packages."""
    result: set[str] = set()
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if stmt.get("kind") != "ImportFrom":
            continue
        module_any = stmt.get("module")
        module = module_any if isinstance(module_any, str) else ""
        if not module.startswith("pytra."):
            continue
        level_any = stmt.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level > 0:
            continue
        names_any = stmt.get("names")
        names = names_any if isinstance(names_any, list) else []
        for entry in names:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not isinstance(name, str) or name == "":
                continue
            asname = entry.get("asname")
            local = asname if isinstance(asname, str) and asname != "" else name
            resolved = resolve_import_binding_doc(module, name, "symbol")
            if isinstance(resolved, dict) and resolved.get("resolved_binding_kind") == "module":
                result.add(_safe_ident(local, "mod"))
    return result


def _arraybuffer_elem_scala_type(py_type_name: str) -> str:
    if py_type_name in {"int", "int64", "uint8"}:
        return "Long"
    if py_type_name in {"float", "float64"}:
        return "Double"
    if py_type_name == "bool":
        return "Boolean"
    if py_type_name == "str":
        return "String"
    if py_type_name == "Path":
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
    ts2: str = type_name
    if type_name == "None":
        return "Unit" if allow_void else "Any"
    if type_name in {"int", "int32", "int64", "uint8"}:
        return "Long"
    if type_name in {"float", "float64"}:
        return "Double"
    if type_name == "bool":
        return "Boolean"
    if type_name == "str":
        return "String"
    if type_name == "Path":
        return "String"
    if ts2.startswith("list["):
        return _list_scala_type(type_name)
    if ts2.startswith("tuple["):
        return _tuple_scala_type(type_name)
    if ts2.startswith("dict["):
        return "mutable.LinkedHashMap[Any, Any]"
    if type_name in {"bytes", "bytearray"}:
        return "mutable.ArrayBuffer[Long]"
    if type_name in {"unknown", "object", "any"}:
        return "Any"
    if ts2.isidentifier():
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
    ts: str = type_name
    if not ts.startswith("tuple[") or not ts.endswith("]"):
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


def _mentions_ident(expr: str, ident: str) -> bool:
    if ident == "":
        return False
    i = 0
    n = len(expr)
    m = len(ident)
    while i + m <= n:
        if expr[i : i + m] == ident:
            prev_ok = i == 0 or not (expr[i - 1].isalnum() or expr[i - 1] == "_")
            j = i + m
            next_ok = j >= n or not (expr[j].isalnum() or expr[j] == "_")
            if prev_ok and next_ok:
                return True
        i += 1
    return False


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
    nd6: dict[str, Any] = node
    resolved_any = nd6.get("resolved_type")
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
    nd5: dict[str, Any] = node
    if nd5.get("kind") != "Constant":
        return False
    value = nd5.get("value")
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
    if scala_type.startswith("mutable.ArrayBuffer[") and scala_type.endswith("]"):
        return _to_list_expr(expr) + ".asInstanceOf[" + scala_type + "]"
    if scala_type == "mutable.LinkedHashMap[Any, Any]":
        return _to_dict_expr(expr)
    if scala_type == "Any":
        return expr
    if scala_type in _CLASS_NAMES[0]:
        return "__pytra_as_" + scala_type + "(" + expr + ")"
    return expr


def _render_name_expr(expr: dict[str, Any]) -> str:
    name = _safe_ident(expr.get("id"), "value")
    if name == "self":
        return "this"
    relative_alias = _RELATIVE_IMPORT_NAME_ALIASES.get(name, "")
    if relative_alias != "":
        return relative_alias
    if name in _FUNCTION_NAMES[0]:
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
    ed3: dict[str, Any] = expr
    resolved = ed3.get("resolved_type")
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
    kind = ed3.get("kind")
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
    if op == "LShift":
        return "<<"
    if op == "RShift":
        return ">>"
    if op == "BitAnd":
        return "&"
    if op == "BitXor":
        return "^"
    if op == "BitOr":
        return "|"
    if op == "FloorDiv":
        return "/"
    return "+"


def _binop_precedence(op: Any) -> int:
    if op == "Mult" or op == "Div" or op == "FloorDiv" or op == "Mod":
        return 12
    if op == "Add" or op == "Sub":
        return 11
    if op == "LShift" or op == "RShift":
        return 10
    if op == "BitAnd":
        return 9
    if op == "BitXor":
        return 8
    if op == "BitOr":
        return 7
    return 0


def _is_simple_binop_operand(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    nd4: dict[str, Any] = node
    kind = nd4.get("kind")
    return kind in {"Name", "Constant", "Attribute", "Call", "Subscript"}


def _wrap_binop_operand(expr: str, node: Any, parent_op: Any, is_right: bool) -> str:
    if not isinstance(node, dict):
        return expr
    nd3: dict[str, Any] = node
    kind = nd3.get("kind")
    if kind == "IfExp" or kind == "BoolOp" or kind == "Compare":
        return "(" + expr + ")"
    if kind != "BinOp":
        return expr
    child_op = nd3.get("op")
    parent_prec = _binop_precedence(parent_op)
    child_prec = _binop_precedence(child_op)
    if child_prec < parent_prec:
        return "(" + expr + ")"
    if parent_op == "Mult" and (child_op == "Div" or child_op == "FloorDiv"):
        return "(" + expr + ")"
    if is_right and child_prec == parent_prec and parent_op in {"Sub", "Div", "FloorDiv", "Mod", "LShift", "RShift"}:
        return "(" + expr + ")"
    return expr


def _join_binop_expr(left_expr: str, right_expr: str, op_symbol: str, left_node: Any, right_node: Any, parent_op: Any) -> str:
    left_rendered = _wrap_binop_operand(left_expr, left_node, parent_op, False)
    right_rendered = _wrap_binop_operand(right_expr, right_node, parent_op, True)
    if (
        _is_simple_binop_operand(left_node)
        and _is_simple_binop_operand(right_node)
        and left_rendered == left_expr
        and right_rendered == right_expr
    ):
        return _strip_outer_parens(left_rendered) + " " + op_symbol + " " + _strip_outer_parens(right_rendered)
    return "(" + left_rendered + " " + op_symbol + " " + right_rendered + ")"


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
        ld: dict[str, Any] = left_any
        left_resolved_any = ld.get("resolved_type")
        left_type = left_resolved_any if isinstance(left_resolved_any, str) else ""
    if isinstance(right_any, dict):
        rd: dict[str, Any] = right_any
        right_resolved_any = rd.get("resolved_type")
        right_type = right_resolved_any if isinstance(right_resolved_any, str) else ""

    if op == "Div" and (resolved == "Path" or left_type == "Path" or right_type == "Path"):
        return "__pytra_path_join(" + left_expr + ", " + right_expr + ")"

    if op == "Div":
        return _join_binop_expr(
            _float_operand(left_expr, left_any),
            _float_operand(right_expr, right_any),
            "/",
            left_any,
            right_any,
            op,
        )

    if op == "FloorDiv":
        lhs = _int_operand(left_expr, left_any)
        rhs = _int_operand(right_expr, right_any)
        return _to_int_expr(lhs + " / " + rhs)

    if op == "Mod":
        return _join_binop_expr(
            _int_operand(left_expr, left_any),
            _int_operand(right_expr, right_any),
            "%",
            left_any,
            right_any,
            op,
        )

    if resolved == "str" and op == "Add":
        return _join_binop_expr(
            _to_str_expr(left_expr),
            _to_str_expr(right_expr),
            "+",
            left_any,
            right_any,
            op,
        )

    if resolved in {"int", "int64", "uint8"}:
        sym = _bin_op_symbol(op)
        return _join_binop_expr(
            _int_operand(left_expr, left_any),
            _int_operand(right_expr, right_any),
            sym,
            left_any,
            right_any,
            op,
        )

    if resolved in {"float", "float64"}:
        sym = _bin_op_symbol(op)
        return _join_binop_expr(
            _float_operand(left_expr, left_any),
            _float_operand(right_expr, right_any),
            sym,
            left_any,
            right_any,
            op,
        )

    sym = _bin_op_symbol(op)
    return _join_binop_expr(left_expr, right_expr, sym, left_any, right_any, op)


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
            cd: dict[str, Any] = comp_node
            right_any = cd.get("resolved_type")
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


def _camel_to_snake(name: str) -> str:
    if name == "":
        return ""
    out: list[str] = []
    i = 0
    while i < len(name):
        ch = name[i]
        if ch.isupper():
            if i > 0:
                prev = name[i - 1]
                if prev != "_" and (prev.islower() or (i + 1 < len(name) and name[i + 1].islower())):
                    out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch)
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


def _runtime_module_id(expr: dict[str, Any], runtime_call: str) -> str:
    runtime_module_any = expr.get("runtime_module_id")
    runtime_module = runtime_module_any if isinstance(runtime_module_any, str) else ""
    if runtime_module == "":
        canonical = runtime_call.replace("::", ".")
        dot = canonical.find(".")
        if dot >= 0:
            runtime_module = canonical[:dot].strip()
    return canonical_runtime_module_id(runtime_module)


def _runtime_symbol_name(expr: dict[str, Any], runtime_call: str) -> str:
    runtime_symbol_any = expr.get("runtime_symbol")
    if isinstance(runtime_symbol_any, str) and runtime_symbol_any.strip() != "":
        return runtime_symbol_any.strip()
    canonical = runtime_call.replace("::", ".")
    dot = canonical.find(".")
    if dot >= 0:
        return canonical[dot + 1 :].strip()
    return ""


def _runtime_call_adapter_kind(expr: dict[str, Any]) -> str:
    adapter_kind_any = expr.get("runtime_call_adapter_kind")
    if isinstance(adapter_kind_any, str):
        as_str: str = adapter_kind_any
        return as_str.strip()
    return ""


def _uses_math_value_getter(expr: dict[str, Any]) -> bool:
    if _runtime_call_adapter_kind(expr) == "math.value_getter":
        return True
    runtime_call, _ = _resolved_runtime_call(expr)
    return runtime_call.strip() in {"math.pi", "math.e"}


def _uses_math_float_args(expr: dict[str, Any]) -> bool:
    if _runtime_call_adapter_kind(expr) == "math.float_args":
        return True
    runtime_call, _ = _resolved_runtime_call(expr)
    return runtime_call.strip() in {
        "math.ceil",
        "math.cos",
        "math.exp",
        "math.fabs",
        "math.floor",
        "math.log",
        "math.log10",
        "math.pow",
        "math.sin",
        "math.sqrt",
        "math.tan",
    }


def _resolved_runtime_symbol(expr: dict[str, Any], runtime_call: str, runtime_source: str) -> str:
    name = runtime_call.strip()
    if name == "":
        return ""
    canonical = name.replace("::", ".")
    dot = canonical.find(".")
    if dot >= 0:
        module_name = canonical[:dot].strip()
        symbol_name = canonical[dot + 1 :].strip()
        if module_name == "" or symbol_name == "":
            return ""
        if runtime_source == "runtime_call":
            if canonical.endswith("filesystem.exists"):
                return "__pytra_path_exists"
            if canonical.endswith("filesystem.create_directories"):
                return "__pytra_path_mkdir"
            return ""
        return "py" + _snake_to_pascal(module_name) + _snake_to_pascal(symbol_name)
    normalized = _camel_to_snake(name)
    if runtime_source == "runtime_call":
        if normalized == "py_write_text":
            return "__pytra_path_write_text"
        if normalized == "py_read_text":
            return "__pytra_path_read_text"
        if normalized == "path":
            return "__pytra_path_new"
        if normalized in {"path_parent", "path_name", "path_stem", "perf_counter"}:
            return "__pytra_" + normalized
        if normalized in {"write_rgb_png", "save_gif", "grayscale_palette", "fire_palette"}:
            return normalized
        if normalized.startswith("py_"):
            return "__pytra_" + normalized[3:]
        return ""
    if normalized.startswith("py_assert_"):
        return normalized
    # For resolved_runtime_call: the function is provided by an EAST-merged
    # shim module, so return the name as-is (no __pytra_ prefix needed).
    if runtime_source == "resolved_runtime_call":
        return normalized
    return "__pytra_" + normalized


_EXTERN_NATIVE_OWNER_CACHE: dict[str, str] = {}


def _extern_native_owner(owner_name: str) -> str:
    """Return '<module>_native' if owner_name is a known @extern stdlib module."""
    if owner_name in _EXTERN_NATIVE_OWNER_CACHE:
        return _EXTERN_NATIVE_OWNER_CACHE[owner_name]
    module_id = "pytra.std." + owner_name
    contract = lookup_runtime_module_extern_contract(module_id)
    if len(contract) > 0:
        result = owner_name + "_native"
    else:
        result = ""
    _EXTERN_NATIVE_OWNER_CACHE[owner_name] = result
    return result


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    value_any = expr.get("value")
    field = _safe_ident(expr.get("attr"), "field")
    semantic_tag_any = expr.get("semantic_tag")
    semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
    adapter_kind_any = expr.get("runtime_call_adapter_kind")
    adapter_kind = adapter_kind_any if isinstance(adapter_kind_any, str) else ""
    runtime_call, runtime_source = _resolved_runtime_call(expr)
    if semantic_tag.startswith("stdlib.") and runtime_call == "":
        raise RuntimeError("scala native emitter: unresolved stdlib runtime attribute: " + semantic_tag)
    if runtime_call != "":
        runtime_symbol = _resolved_runtime_symbol(expr, runtime_call, runtime_source)
        if runtime_symbol != "":
            if runtime_call in {"path_parent", "path_name", "path_stem"}:
                return runtime_symbol + "(" + _render_expr(value_any) + ")"
            if runtime_source == "resolved_runtime_call":
                if _uses_math_value_getter(expr):
                    return runtime_symbol + "()"
                return runtime_symbol
    if isinstance(value_any, dict) and value_any.get("kind") == "Name":
        owner_ident = _safe_ident(value_any.get("id"), "")
        # @extern module delegation: math -> math_native, time -> time_native
        # Must be checked before _PYTRA_MODULE_IMPORTS stripping.
        native_name = _extern_native_owner(owner_ident)
        if native_name != "":
            return native_name + "." + field
        if owner_ident in _PYTRA_MODULE_IMPORTS[0]:
            return field
    value = _render_expr(value_any)
    return value + "." + field


def _call_arg_nodes(expr: dict[str, Any]) -> tuple[list[Any], Any]:
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
                kd2: dict[str, Any] = kw
                out.append(kd2.get("value"))
            else:
                out.append(kw)
            j += 1
        return out, keywords_any
    kw_values_any = expr.get("kw_values")
    kw_values = kw_values_any if isinstance(kw_values_any, list) else []
    if len(kw_values) > 0:
        j = 0
        while j < len(kw_values):
            out.append(kw_values[j])
            j += 1
        return out, kw_values_any
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
    return out, kw_nodes_any


def _render_runtime_args(adapter_kind: str, args: list[Any], keywords_any: Any) -> list[str]:
    args_to_render = args
    keywords = keywords_any if isinstance(keywords_any, list) else []
    if adapter_kind == "image.save_gif.keyword_defaults" and len(keywords) > 0 and len(args) >= len(keywords):
        args_to_render = args[: len(args) - len(keywords)]
    rendered: list[str] = []
    i = 0
    while i < len(args_to_render):
        rendered.append(_render_expr(args_to_render[i]))
        i += 1
    if adapter_kind == "image.save_gif.keyword_defaults":
        rendered_keywords: list[tuple[str, str]] = []
        k = 0
        while k < len(keywords):
            kw = keywords[k]
            if isinstance(kw, dict):
                kd: dict[str, Any] = kw
                kw_name_any = kd.get("arg")
                if isinstance(kw_name_any, str):
                    rendered_keywords.append((kw_name_any, _render_expr(kd.get("value"))))
            k += 1
        return normalize_rendered_runtime_args(
            adapter_kind,
            rendered,
            rendered_keywords,
            default_values={"delay_cs": "4L", "loop": "0L"},
            error_prefix="scala native emitter",
        )
    return rendered


def _render_call_via_runtime_call(
    runtime_call: str,
    runtime_source: str,
    semantic_tag: str,
    args: list[Any],
    keywords_any: Any,
    adapter_kind: str,
    call_expr: dict[str, Any] | None = None,
) -> str:
    if runtime_call.startswith("py_assert_"):
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered_assert_args) + ")"
    def _inject_method_owner(rendered_args: list[str]) -> list[str]:
        if not semantic_tag.startswith("stdlib.method.") or not isinstance(call_expr, dict):
            return rendered_args
        owner_any = call_expr.get("runtime_owner")
        if not isinstance(owner_any, dict):
            func_any = call_expr.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
                owner_any = func_any.get("value")
        if isinstance(owner_any, dict):
            return [_render_expr(owner_any)] + rendered_args
        return rendered_args

    if runtime_source == "runtime_call":
        if not semantic_tag.startswith("stdlib."):
            return ""
        runtime_symbol = _resolved_runtime_symbol(call_expr if isinstance(call_expr, dict) else {}, runtime_call, runtime_source)
        if runtime_symbol == "":
            return ""
        rendered_runtime_args = _render_runtime_args(adapter_kind, args, keywords_any)
        rendered_runtime_args = _inject_method_owner(rendered_runtime_args)
        return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
    runtime_symbol = _resolved_runtime_symbol(call_expr if isinstance(call_expr, dict) else {}, runtime_call, runtime_source)
    if runtime_symbol == "":
        return ""
    rendered_runtime_args = _render_runtime_args(adapter_kind, args, keywords_any)
    rendered_runtime_args = _inject_method_owner(rendered_runtime_args)
    if runtime_call.find(".") >= 0:
        if isinstance(call_expr, dict) and _uses_math_value_getter(call_expr) and len(rendered_runtime_args) == 0:
            return runtime_symbol + "()"
        if isinstance(call_expr, dict) and _uses_math_float_args(call_expr):
            rendered_math_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_math_args.append(_to_float_expr(_render_expr(args[i])))
                i += 1
            return runtime_symbol + "(" + ", ".join(rendered_math_args) + ")"
        return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
    return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"


def _call_name(expr: dict[str, Any]) -> str:
    func_any = expr.get("func")
    if not isinstance(func_any, dict):
        return ""
    fd2: dict[str, Any] = func_any
    if fd2.get("kind") != "Name":
        return ""
    raw = fd2.get("id")
    if not isinstance(raw, str):
        return ""
    if raw == "super":
        return "super"
    ident = _safe_ident(raw, "")
    relative_alias = _RELATIVE_IMPORT_NAME_ALIASES.get(ident, "")
    if relative_alias != "":
        return relative_alias
    return ident


def _render_call_expr(expr: dict[str, Any]) -> str:
    args, keywords_any = _call_arg_nodes(expr)
    callee = _call_name(expr)

    if callee == "super":
        if len(args) == 0:
            return "super"
        rendered_super_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_super_args.append(_render_expr(args[i]))
            i += 1
        return "super(" + ", ".join(rendered_super_args) + ")"

    semantic_tag_any = expr.get("semantic_tag")
    semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
    adapter_kind_any = expr.get("runtime_call_adapter_kind")
    adapter_kind = adapter_kind_any if isinstance(adapter_kind_any, str) else ""
    resolved_type_any = expr.get("resolved_type")
    resolved_type = resolved_type_any if isinstance(resolved_type_any, str) else ""
    if semantic_tag == "stdlib.symbol.Path" or (
        callee == "Path" and resolved_type == "Path" and "Path" not in _CLASS_NAMES[0]
    ):
        if len(args) == 0:
            return "__pytra_path_new(\"\")"
        return "__pytra_path_new(" + _render_expr(args[0]) + ")"
    runtime_call, runtime_source = _resolved_runtime_call(expr)
    if semantic_tag.startswith("stdlib.") and runtime_call == "":
        raise RuntimeError("scala native emitter: unresolved stdlib runtime call: " + semantic_tag)
    if runtime_call != "":
        rendered_runtime = _render_call_via_runtime_call(
            runtime_call,
            runtime_source,
            semantic_tag,
            args,
            keywords_any,
            adapter_kind,
            call_expr=expr,
        )
        if rendered_runtime != "":
            return rendered_runtime

    if callee.startswith("py_assert_"):
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered_assert_args) + ")"
    if callee == "bytearray":
        if len(args) == 0:
            return "mutable.ArrayBuffer[Long]()"
        return "__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee == "bytes":
        if len(args) == 0:
            return "mutable.ArrayBuffer[Long]()"
        return "__pytra_bytes(" + _render_expr(args[0]) + ")"
    if callee == "int":
        if len(args) == 0:
            return "0L"
        arg0 = args[0]
        rendered_arg0 = _render_expr(arg0)
        if _has_resolved_type(arg0, {"int", "int64", "uint8"}):
            return rendered_arg0
        return _to_int_expr(rendered_arg0)
    if callee == "float":
        if len(args) == 0:
            return "0.0"
        arg0 = args[0]
        rendered_arg0 = _render_expr(arg0)
        if _has_resolved_type(arg0, {"float", "float64"}):
            return rendered_arg0
        return _to_float_expr(rendered_arg0)
    if callee == "bool":
        if len(args) == 0:
            return "false"
        return _to_truthy_expr(_render_expr(args[0]))
    if callee == "str":
        if len(args) == 0:
            return '""'
        return _to_str_expr(_render_expr(args[0]))
    if callee == "len":
        if len(args) == 0:
            return "0L"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee == "enumerate":
        if len(args) == 0:
            return "mutable.ArrayBuffer[Any]()"
        return "__pytra_enumerate(" + _render_expr(args[0]) + ")"
    if callee == "min":
        if len(args) == 0:
            return "0L"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_min(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee == "max":
        if len(args) == 0:
            return "0L"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_max(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee == "print":
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_print(" + ", ".join(rendered_args) + ")"
    if callee in {"RuntimeError", "ValueError", "TypeError", "Exception", "AssertionError"}:
        if len(args) == 0:
            return '""'
        return _render_expr(args[0])

    func_any = expr.get("func")
    if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
        method = _safe_ident(func_any.get("attr"), "")
        owner_any = func_any.get("value")
        if method == "__init__" and isinstance(owner_any, dict) and owner_any.get("kind") == "Call":
            if _call_name(owner_any) in {"super", "super_"}:
                return "__pytra_noop()"
        if method == "isdigit" and len(args) == 0:
            return "__pytra_isdigit(" + _render_expr(owner_any) + ")"
        if method == "isalpha" and len(args) == 0:
            return "__pytra_isalpha(" + _render_expr(owner_any) + ")"
        if method == "get":
            if len(args) == 0:
                return "__pytra_any_default()"
            key_expr = _render_expr(args[0])
            default_expr = "__pytra_any_default()"
            if len(args) >= 2:
                default_expr = _render_expr(args[1])
            owner_expr = _render_expr(owner_any)
            return "__pytra_as_dict(" + owner_expr + ").getOrElse(__pytra_str(" + key_expr + "), " + default_expr + ")"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner_ident = _safe_ident(owner_any.get("id"), "")
            # @extern module delegation: math.sqrt(x) -> math_native.sqrt(x)
            native_owner = _extern_native_owner(owner_ident)
            if native_owner != "":
                rendered_args_n: list[str] = []
                i = 0
                while i < len(args):
                    rendered_args_n.append(_render_expr(args[i]))
                    i += 1
                return native_owner + "." + method + "(" + ", ".join(rendered_args_n) + ")"
            if owner_ident in _PYTRA_MODULE_IMPORTS[0]:
                rendered_args_m: list[str] = []
                i = 0
                while i < len(args):
                    rendered_args_m.append(_render_expr(args[i]))
                    i += 1
                return method + "(" + ", ".join(rendered_args_m) + ")"
        owner_expr = _render_expr(owner_any)
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return owner_expr + "." + method + "(" + ", ".join(rendered_args) + ")"

    if callee in _CLASS_NAMES[0]:
        rendered_ctor_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_ctor_args.append(_render_expr(args[i]))
            i += 1
        return "new " + callee + "(" + ", ".join(rendered_ctor_args) + ")"

    rendered_args = []
    i = 0
    while i < len(args):
        rendered_args.append(_render_expr(args[i]))
        i += 1
    if callee != "":
        return callee + "(" + ", ".join(rendered_args) + ")"
    func_expr = _render_expr(expr.get("func"))
    return func_expr + "(" + ", ".join(rendered_args) + ")"


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
        list_type = "mutable.ArrayBuffer[Any]"
        resolved_any = ed2.get("resolved_type")
        resolved = resolved_any if isinstance(resolved_any, str) else ""
        if kind == "List" and resolved.startswith("list["):
            list_type = _list_scala_type(resolved)
        if kind == "Tuple" and resolved.startswith("tuple["):
            list_type = _tuple_scala_type(resolved)
        if len(rendered) == 0:
            return list_type + "()"
        return list_type + "(" + ", ".join(rendered) + ")"

    if kind == "Dict":
        keys_any = ed2.get("keys")
        vals_any = ed2.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        vals = vals_any if isinstance(vals_any, list) else []
        if len(keys) == 0 or len(vals) == 0:
            entries_any = ed2.get("entries")
            entries = entries_any if isinstance(entries_any, list) else []
            parts: list[str] = []
            i = 0
            while i < len(entries):
                entry = entries[i]
                if isinstance(entry, dict):
                    ed: dict[str, Any] = entry
                    key_any = ed.get("key")
                    value_any = ed.get("value")
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
        gens_any = ed2.get("generators")
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
        if not isinstance(target_any, dict):
            return "mutable.ArrayBuffer[Any]()"
        td2: dict[str, Any] = target_any
        if td2.get("kind") != "Name":
            return "mutable.ArrayBuffer[Any]()"
        if not isinstance(iter_any, dict):
            return "mutable.ArrayBuffer[Any]()"
        id: dict[str, Any] = iter_any
        if id.get("kind") != "RangeExpr":
            return "mutable.ArrayBuffer[Any]()"
        loop_var = _safe_ident(td2.get("id"), "i")
        if loop_var == "_":
            loop_var = "__lc_i"
        start = _render_expr(id.get("start"))
        stop = _render_expr(id.get("stop"))
        step = _render_expr(id.get("step"))
        elt = _render_expr(ed2.get("elt"))
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
        test_expr = _render_truthy_expr(ed2.get("test"))
        body_expr = _render_expr(ed2.get("body"))
        else_expr = _render_expr(ed2.get("orelse"))
        return "__pytra_ifexp(" + test_expr + ", " + body_expr + ", " + else_expr + ")"

    if kind == "Subscript":
        owner = _render_expr(ed2.get("value"))
        index_any = ed2.get("slice")
        if isinstance(index_any, dict) and index_any.get("kind") == "Slice":
            lower_any = index_any.get("lower")
            upper_any = index_any.get("upper")
            lower = _render_expr(lower_any) if isinstance(lower_any, dict) else "0L"
            upper = _render_expr(upper_any) if isinstance(upper_any, dict) else "__pytra_len(" + owner + ")"
            return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"

        index = _render_expr(index_any)
        base = "__pytra_get_index(" + owner + ", " + index + ")"
        resolved = ed2.get("resolved_type")
        scala_t = _scala_type(resolved, allow_void=False)
        return _cast_from_any(base, scala_t)

    if kind == "IsInstance":
        lhs = _render_expr(ed2.get("value"))
        return _render_isinstance_check(lhs, ed2.get("expected_type_id"))

    if kind == "ObjLen":
        return "__pytra_len(" + _render_expr(ed2.get("value")) + ")"
    if kind == "ObjStr":
        return _to_str_expr(_render_expr(ed2.get("value")))
    if kind == "ObjBool":
        return _to_truthy_expr(_render_expr(ed2.get("value")))

    if kind == "Unbox" or kind == "Box":
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
    td: dict[str, Any] = target
    kind = td.get("kind")
    if kind == "Name":
        return _safe_ident(td.get("id"), "tmp")
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
    ed: dict[str, Any] = expr
    kind = ed.get("kind")
    if kind == "Name" and isinstance(type_map, dict):
        ident = _safe_ident(ed.get("id"), "")
        if ident in type_map:
            return type_map[ident]
    if kind == "Call":
        runtime_call, runtime_source = _resolved_runtime_call(expr)
        if runtime_call != "":
            runtime_symbol = _resolved_runtime_symbol(expr, runtime_call, runtime_source)
            if _uses_math_value_getter(expr):
                return "Double"
            if _uses_math_float_args(expr):
                return "Double"
            if runtime_symbol in {"__pytra_perf_counter", "__pytra_float"}:
                return "Double"
            if runtime_symbol == "__pytra_int":
                return "Long"
            if runtime_symbol == "__pytra_truthy":
                return "Boolean"
            if runtime_symbol in {"__pytra_path_new", "__pytra_path_join", "__pytra_path_parent", "__pytra_path_name", "__pytra_path_stem"}:
                return "String"
        name = _call_name(expr)
        if name == "int":
            return "Long"
        if name == "float":
            return "Double"
        if name == "bool":
            return "Boolean"
        if name == "str":
            return "String"
        if name == "bytearray" or name == "bytes":
            return "mutable.ArrayBuffer[Long]"
        if name == "len":
            return "Long"
        if name in {"min", "max"}:
            args_any = ed.get("args")
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
        if name in _CLASS_NAMES[0]:
            return name
        func_any = ed.get("func")
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner_any = func_any.get("value")
            attr_name = _safe_ident(func_any.get("attr"), "")
            if attr_name in {"isdigit", "isalpha"}:
                return "Boolean"
    if kind == "BinOp":
        op = ed.get("op")
        if op == "Div":
            return "Double"
        left_t = _infer_scala_type(ed.get("left"), type_map)
        right_t = _infer_scala_type(ed.get("right"), type_map)
        if left_t == "Double" or right_t == "Double":
            return "Double"
        if left_t == "Long" and right_t == "Long":
            return "Long"
        if op == "Mult":
            left_any = ed.get("left")
            right_any = ed.get("right")
            if isinstance(left_any, dict) and left_any.get("kind") == "List":
                return "mutable.ArrayBuffer[Any]"
            if isinstance(right_any, dict) and right_any.get("kind") == "List":
                return "mutable.ArrayBuffer[Any]"
    if kind == "IfExp":
        body_t = _infer_scala_type(ed.get("body"), type_map)
        else_t = _infer_scala_type(ed.get("orelse"), type_map)
        if body_t == else_t:
            return body_t
        if body_t == "Double" or else_t == "Double":
            return "Double"
        if body_t == "Long" and else_t == "Long":
            return "Long"
    resolved = ed.get("resolved_type")
    return _scala_type(resolved, allow_void=False)


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
        resolved = _scala_type(vd.get("resolved_type"), allow_void=False)
        return resolved == target_type
    if kind in {"Compare", "BoolOp", "IsInstance"}:
        return target_type == "Boolean"
    if kind == "Call":
        runtime_call, runtime_source = _resolved_runtime_call(value_expr)
        if runtime_call != "":
            runtime_symbol = _resolved_runtime_symbol(value_expr, runtime_call, runtime_source)
            if target_type == "Double" and (
                _uses_math_float_args(value_expr)
                or _uses_math_value_getter(value_expr)
                or runtime_symbol in {"__pytra_perf_counter", "__pytra_float"}
            ):
                return True
            if target_type == "Long" and runtime_symbol == "__pytra_int":
                return True
            if target_type == "Boolean" and runtime_symbol == "__pytra_truthy":
                return True
            if target_type == "String" and runtime_symbol in {
                "__pytra_path_new",
                "__pytra_path_join",
                "__pytra_path_parent",
                "__pytra_path_name",
                "__pytra_path_stem",
            }:
                return True
        callee = _call_name(value_expr)
        if callee == "int":
            return target_type == "Long"
        if callee == "float":
            return target_type == "Double"
        if callee == "bool":
            return target_type == "Boolean"
        if callee == "str":
            return target_type == "String"
        if callee == "len":
            return target_type == "Long"
        resolved = _scala_type(vd.get("resolved_type"), allow_void=False)
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


def _stmt_uses_loop_control(stmt_any: Any) -> bool:
    if not isinstance(stmt_any, dict):
        return False
    sd: dict[str, Any] = stmt_any
    kind = sd.get("kind")
    if kind in {"Break", "Continue"}:
        return True
    if kind == "Expr":
        value_any = sd.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name":
            ident_any = value_any.get("id")
            ident = ident_any if isinstance(ident_any, str) else ""
            return ident in {"break", "continue"}
        return False
    if kind in {"ForCore", "While", "FunctionDef", "ClassDef"}:
        # break/continue inside nested loops/functions do not require boundary for this loop.
        return False

    for key in ("body", "orelse", "finalbody"):
        block_any = sd.get(key)
        if isinstance(block_any, list):
            i = 0
            while i < len(block_any):
                if _stmt_uses_loop_control(block_any[i]):
                    return True
                i += 1

    handlers_any = sd.get("handlers")
    handlers = handlers_any if isinstance(handlers_any, list) else []
    i = 0
    while i < len(handlers):
        handler_any = handlers[i]
        if isinstance(handler_any, dict):
            hd: dict[str, Any] = handler_any
            h_body_any = hd.get("body")
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
    id: dict[str, Any] = iter_plan_any
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("scala native emitter: unsupported ForCore target_plan")
    td: dict[str, Any] = target_plan_any

    lines: list[str] = []
    if id.get("kind") == "StaticRangeForPlan" and td.get("kind") == "NameTarget":
        target_name = _safe_ident(td.get("id"), "i")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "loop")
        start_node = id.get("start")
        stop_node = id.get("stop")
        step_node = id.get("step")
        start = _int_operand(_render_expr(start_node), start_node)
        stop = _int_operand(_render_expr(stop_node), stop_node)
        step = _int_operand(_render_expr(step_node), step_node)
        step_is_one = _is_int_literal(step_node, 1)
        normalized_cond = ""
        normalized_version_any = stmt.get("normalized_expr_version")
        if isinstance(normalized_version_any, str) and normalized_version_any == "east3_expr_v1":
            normalized_exprs_any = stmt.get("normalized_exprs")
            if isinstance(normalized_exprs_any, dict):
                nd: dict[str, Any] = normalized_exprs_any
                for_cond_any = nd.get("for_cond_expr")
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
            cond_text = target_name + " < " + stop
            if normalized_cond != "":
                normalized_cond_text = _strip_outer_parens(normalized_cond)
                if _mentions_ident(normalized_cond_text, target_name):
                    cond_text = normalized_cond_text
            lines.append(while_prefix + "while (" + _strip_outer_parens(cond_text) + ") {")
        else:
            step_prefix = indent + "    " if loop_uses_control else indent
            lines.append(step_prefix + "val " + step_tmp + " = " + step)
            while_prefix = indent + "    " if loop_uses_control else indent
            cond_text = ""
            range_mode_any = id.get("range_mode")
            range_mode = range_mode_any if isinstance(range_mode_any, str) else ""
            if normalized_cond != "" and range_mode in {"ascending", "descending"}:
                normalized_cond_text = _strip_outer_parens(normalized_cond)
                if _mentions_ident(normalized_cond_text, target_name):
                    cond_text = normalized_cond_text
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
            lines.append(while_prefix + "while (" + _strip_outer_parens(cond_text) + ") {")
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

    if id.get("kind") == "RuntimeIterForPlan" and td.get("kind") == "NameTarget":
        iter_expr = _render_expr(id.get("iter_expr"))
        iter_tmp = _fresh_tmp(ctx, "iter")
        idx_tmp = _fresh_tmp(ctx, "i")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        loop_uses_control = _body_uses_loop_control(body)
        break_label = _fresh_tmp(ctx, "breakLabel") if loop_uses_control else ""
        continue_label = _fresh_tmp(ctx, "continueLabel") if loop_uses_control else ""
        target_name = _safe_ident(td.get("id"), "item")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "item")
        target_type_any = td.get("target_type")
        target_type_txt = target_type_any if isinstance(target_type_any, str) else ""
        if target_type_txt in {"", "unknown"}:
            iter_expr_any = id.get("iter_expr")
            if isinstance(iter_expr_any, dict):
                id: dict[str, Any] = iter_expr_any
                iter_elem_t_any = id.get("iter_element_type")
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

    if id.get("kind") == "RuntimeIterForPlan" and td.get("kind") == "TupleTarget":
        iter_expr = _render_expr(id.get("iter_expr"))
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
        parent_t = td.get("target_type")
        if isinstance(parent_t, str):
            elem_types = _tuple_element_types(parent_t)
        elem_any = td.get("elements")
        elems = elem_any if isinstance(elem_any, list) else []

        i = 0
        while i < len(elems):
            elem = elems[i]
            if not isinstance(elem, dict):
                raise RuntimeError("scala native emitter: unsupported tuple target element")
            ed2: dict[str, Any] = elem
            if ed2.get("kind") != "NameTarget":
                raise RuntimeError("scala native emitter: unsupported tuple target element")
            name = _safe_ident(ed2.get("id"), "item_" + str(i))
            if name == "_":
                i += 1
                continue
            rhs = tuple_tmp + "(" + str(i) + ")"
            target_t_any = ed2.get("target_type")
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
    lines: list[str] = [indent + "val " + tuple_tmp + " = __pytra_as_list(" + _render_expr(value_any) + ")"]
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
        rhs = tuple_tmp + "(" + str(i) + ")"
        elem_type = "Any"
        if i < len(tuple_types):
            elem_type = _scala_type(tuple_types[i], allow_void=False)
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
            owner = _render_expr(ed.get("value"))
            index = _render_expr(ed.get("slice"))
            lines.append(indent + "__pytra_set_index(" + owner + ", " + index + ", " + casted + ")")
        else:
            return None
        i += 1

    return lines


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        raise RuntimeError("scala native emitter: unsupported statement node")
    sd3: dict[str, Any] = stmt
    kind = sd3.get("kind")

    if kind == "Return":
        if "value" in stmt and sd3.get("value") is not None:
            value = _render_expr(sd3.get("value"))
            return_type_any = ctx.get("return_type")
            return_type = return_type_any if isinstance(return_type_any, str) else ""
            if return_type not in {"", "Any"} and _needs_cast(sd3.get("value"), return_type, _type_map(ctx)):
                value = _cast_from_any(value, return_type)
            return [indent + "return " + value]
        return [indent + "return"]

    if kind == "Expr":
        value_any = sd3.get("value")
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
        target_any = sd3.get("target")
        if isinstance(target_any, dict) and target_any.get("kind") == "Attribute":
            return [indent + _render_attribute_expr(target_any) + " = " + _render_expr(sd3.get("value"))]

        tuple_lines = _emit_tuple_assign(
            target_any,
            sd3.get("value"),
            decl_type_any=(sd3.get("decl_type") or sd3.get("annotation")),
            declare_hint=(sd3.get("declare") is not False),
            indent=indent,
            ctx=ctx,
        )
        if tuple_lines is not None:
            return tuple_lines

        target = _target_name(target_any)
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        scala_type = _scala_type(sd3.get("decl_type") or sd3.get("annotation"), allow_void=False)
        if scala_type == "Any":
            inferred = _infer_scala_type(sd3.get("value"), _type_map(ctx))
            if inferred != "Any":
                scala_type = inferred

        stmt_value = sd3.get("value")
        if stmt_value is None:
            value = _default_return_expr(scala_type)
        else:
            value = _render_expr(stmt_value)
            if scala_type != "Any" and _needs_cast(stmt_value, scala_type, _type_map(ctx)):
                value = _cast_from_any(value, scala_type)
        if sd3.get("declare") is False or target in declared:
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
        targets_any = sd3.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(sd3.get("target"), dict):
            targets = [sd3.get("target")]
        if len(targets) == 0:
            raise RuntimeError("scala native emitter: Assign without target")

        tuple_lines = _emit_tuple_assign(
            targets[0],
            sd3.get("value"),
            decl_type_any=sd3.get("decl_type"),
            declare_hint=bool(sd3.get("declare")),
            indent=indent,
            ctx=ctx,
        )
        if tuple_lines is not None:
            return tuple_lines

        if isinstance(targets[0], dict) and targets[0].get("kind") == "Attribute":
            lhs_attr = _render_attribute_expr(targets[0])
            value_attr = _render_expr(sd3.get("value"))
            return [indent + lhs_attr + " = " + value_attr]

        if isinstance(targets[0], dict) and targets[0].get("kind") == "Subscript":
            tgt = targets[0]
            owner = _render_expr(tgt.get("value"))
            index = _render_expr(tgt.get("slice"))
            value = _render_expr(sd3.get("value"))
            return [indent + "__pytra_set_index(" + owner + ", " + index + ", " + value + ")"]

        lhs = _target_name(targets[0])
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        value = _render_expr(sd3.get("value"))

        if sd3.get("declare"):
            if lhs in declared:
                if lhs in type_map and type_map[lhs] != "Any":
                    if _needs_cast(sd3.get("value"), type_map[lhs], _type_map(ctx)):
                        return [indent + lhs + " = " + _cast_from_any(value, type_map[lhs])]
                    return [indent + lhs + " = " + value]
                return [indent + lhs + " = " + value]
            scala_type = _scala_type(sd3.get("decl_type"), allow_void=False)
            if scala_type == "Any":
                inferred = _infer_scala_type(sd3.get("value"), _type_map(ctx))
                if inferred != "Any":
                    scala_type = inferred
            if scala_type != "Any" and _needs_cast(sd3.get("value"), scala_type, _type_map(ctx)):
                value = _cast_from_any(value, scala_type)
            declared.add(lhs)
            type_map[lhs] = scala_type
            return [indent + "var " + lhs + ": " + scala_type + " = " + value]

        if lhs not in declared:
            inferred = _infer_scala_type(sd3.get("value"), _type_map(ctx))
            declared.add(lhs)
            type_map[lhs] = inferred
            if inferred != "Any" and _needs_cast(sd3.get("value"), inferred, _type_map(ctx)):
                value = _cast_from_any(value, inferred)
            return [indent + "var " + lhs + ": " + inferred + " = " + value]
        if lhs in type_map and type_map[lhs] != "Any":
            if _needs_cast(sd3.get("value"), type_map[lhs], _type_map(ctx)):
                return [indent + lhs + " = " + _cast_from_any(value, type_map[lhs])]
            return [indent + lhs + " = " + value]
        return [indent + lhs + " = " + value]

    if kind == "AugAssign":
        lhs = _target_name(sd3.get("target"))
        rhs = _render_expr(sd3.get("value"))
        op = sd3.get("op")
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
        left = _target_name(sd3.get("left"))
        right = _target_name(sd3.get("right"))
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
        value_any = sd3.get("value")
        if value_any is None:
            return [indent + yield_buffer + ".append(__pytra_any_default())"]
        return [indent + yield_buffer + ".append(" + _render_expr(value_any) + ")"]

    if kind == "Try":
        body_any = sd3.get("body")
        body = body_any if isinstance(body_any, list) else []
        handlers_any = sd3.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        final_any = sd3.get("finalbody")
        finalbody = final_any if isinstance(final_any, list) else []
        orelse_any = sd3.get("orelse")
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
            fd: dict[str, Any] = first
            alias_any = fd.get("name")
            alias_raw = alias_any if isinstance(alias_any, str) else ""
            alias = _safe_ident(alias_raw, "") if alias_raw != "" else ""
            if alias != "" and alias != base_ex:
                lines.append(indent + "        val " + alias + " = " + base_ex)
            h_body_any = fd.get("body")
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
        test_expr = _strip_outer_parens(_render_truthy_expr(sd3.get("test")))
        lines: list[str] = [indent + "if (" + test_expr + ") {"]
        body_any = sd3.get("body")
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

        orelse_any = sd3.get("orelse")
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
        test_expr = _strip_outer_parens(_render_truthy_expr(sd3.get("test")))
        body_any = sd3.get("body")
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
        exc_any = sd3.get("exc")
        if exc_any is None:
            return [indent + "throw new RuntimeException(\"pytra raise\")"]
        return [indent + "throw new RuntimeException(__pytra_str(" + _render_expr(exc_any) + "))"]

    if kind == "VarDecl":
        name = _safe_ident(sd3.get("name"), "v")
        var_type = _scala_type(sd3.get("type"), allow_void=False)
        type_map = _type_map(ctx)
        type_map[name] = var_type
        return [indent + "var " + name + ": " + var_type + " = " + _default_return_expr(var_type)]

    raise RuntimeError("scala native emitter: unsupported stmt kind " + str(kind))


def _stmt_guarantees_return(stmt: Any) -> bool:
    if not isinstance(stmt, dict):
        return False
    sd2: dict[str, Any] = stmt
    kind = sd2.get("kind")
    if kind == "Return":
        return True
    if kind != "If":
        return False
    body_any = sd2.get("body")
    body = body_any if isinstance(body_any, list) else []
    orelse_any = sd2.get("orelse")
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
    sd: dict[str, Any] = stmt
    kind = sd.get("kind")
    if kind == "Yield":
        return True
    body_any = sd.get("body")
    body = body_any if isinstance(body_any, list) else []
    if _block_contains_yield(body):
        return True
    orelse_any = sd.get("orelse")
    orelse = orelse_any if isinstance(orelse_any, list) else []
    if _block_contains_yield(orelse):
        return True
    if kind == "Try":
        handlers_any = sd.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        i = 0
        while i < len(handlers):
            handler = handlers[i]
            if isinstance(handler, dict):
                hd: dict[str, Any] = handler
                h_body_any = hd.get("body")
                h_body = h_body_any if isinstance(h_body_any, list) else []
                if _block_contains_yield(h_body):
                    return True
            i += 1
        final_any = sd.get("finalbody")
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


def transpile_to_scala_native(east_doc: dict[str, Any], *, emit_main: bool = True, object_wrapper: str = "") -> str:
    """Emit Scala 3 native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("scala native emitter: east_doc must be dict")
    ed: dict[str, Any] = east_doc
    if ed.get("kind") != "Module":
        raise RuntimeError("scala native emitter: root kind must be Module")
    body_any = ed.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("scala native emitter: Module.body must be list")
    _RELATIVE_IMPORT_NAME_ALIASES.clear()
    _RELATIVE_IMPORT_NAME_ALIASES.update(_collect_relative_import_name_aliases(east_doc))
    _PYTRA_MODULE_IMPORTS[0] = _collect_pytra_module_imports(east_doc)
    reject_backend_typed_vararg_signatures(east_doc, backend_name="Scala backend")
    reject_backend_general_union_type_exprs(east_doc, backend_name="Scala backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Scala backend")
    main_guard_any = ed.get("main_guard_body")
    main_guard = main_guard_any if isinstance(main_guard_any, list) else []

    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    i = 0
    while i < len(body_any):
        node = body_any[i]
        if isinstance(node, dict):
            nd: dict[str, Any] = node
            kind = nd.get("kind")
            if kind == "ClassDef":
                classes.append(node)
            elif kind == "FunctionDef":
                functions.append(node)
        i += 1

    _CLASS_NAMES[0] = set()
    _FUNCTION_NAMES[0] = set()
    _CLASS_BASES[0] = {}
    _CLASS_METHODS[0] = {}
    i = 0
    while i < len(classes):
        class_node = classes[i]
        class_name = _safe_ident(class_node.get("name"), "PytraClass")
        _CLASS_NAMES[0].add(class_name)
        base_any = class_node.get("base")
        base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
        _CLASS_BASES[0][class_name] = base_name
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
        _CLASS_METHODS[0][class_name] = methods
        i += 1
    i = 0
    while i < len(functions):
        _FUNCTION_NAMES[0].add(_safe_ident(functions[i].get("name"), "func"))
        i += 1

    lines: list[str] = []
    lines.append("import scala.collection.mutable")
    lines.append("import scala.util.boundary, boundary.break")
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

    if emit_main:
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
    if object_wrapper != "":
        wrapped: list[str] = []
        # Keep import lines at top level
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import "):
                wrapped.append(line)
            else:
                break
        body_start = len(wrapped)
        wrapped.append("object " + object_wrapper + " {")
        i = body_start
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                wrapped.append("")
            else:
                wrapped.append("    " + line)
            i += 1
        wrapped.append("}")
        return "\n".join(wrapped)
    return "\n".join(lines)
