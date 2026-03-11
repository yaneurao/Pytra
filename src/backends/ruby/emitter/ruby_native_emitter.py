"""EAST3 -> Ruby native emitter (minimal skeleton)."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id


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
_INT_TYPES = {"int", "int64"}
_FLOAT_TYPES = {"float", "float64"}
_NIL_FREE_DECL_TYPES = {"int", "int64", "float", "float64", "bool", "str"}


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
    if op == "BitOr":
        return "|"
    if op == "BitXor":
        return "^"
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


def _resolved_runtime_symbol(runtime_call: str, runtime_source: str) -> str:
    call = runtime_call.strip()
    if call == "":
        return ""
    dot = call.find(".")
    if dot >= 0:
        module_name = call[:dot].strip()
        symbol_name = call[dot + 1 :].strip()
        if module_name == "" or symbol_name == "":
            return ""
        return "py" + _snake_to_pascal(module_name) + _snake_to_pascal(symbol_name)
    if runtime_source == "runtime_call":
        return "__pytra_" + call
    return call


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


def _render_positional_call_args(args: list[Any]) -> list[str]:
    rendered: list[str] = []
    i = 0
    while i < len(args):
        rendered.append(_render_expr(args[i]))
        i += 1
    return rendered


def _render_keyword_call_args(expr: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    keywords_any = expr.get("keywords")
    keywords = keywords_any if isinstance(keywords_any, list) else []
    i = 0
    while i < len(keywords):
        kw = keywords[i]
        if isinstance(kw, dict):
            arg_name = kw.get("arg")
            value_any = kw.get("value")
            if isinstance(arg_name, str) and isinstance(value_any, dict):
                out[arg_name] = _render_expr(value_any)
        i += 1
    return out


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


def _const_int_literal(node: Any) -> int | None:
    if not isinstance(node, dict):
        return None
    if node.get("kind") != "Constant":
        return None
    value_any = node.get("value")
    if isinstance(value_any, bool):
        return None
    if isinstance(value_any, int):
        return int(value_any)
    return None


def _is_nonzero_numeric_constant(node: Any) -> bool:
    if not isinstance(node, dict) or node.get("kind") != "Constant":
        return False
    value_any = node.get("value")
    if isinstance(value_any, bool):
        return False
    if isinstance(value_any, int):
        return value_any != 0
    if isinstance(value_any, float):
        return value_any != 0.0
    return False


def _resolved_type_name(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    resolved = node.get("resolved_type")
    if not isinstance(resolved, str):
        return ""
    return resolved.strip()


def _is_int_like_expr(node: Any) -> bool:
    if isinstance(node, bool):
        return False
    if isinstance(node, int):
        return True
    if not isinstance(node, dict):
        return False
    if node.get("kind") == "Constant":
        value_any = node.get("value")
        return isinstance(value_any, int) and not isinstance(value_any, bool)
    return _resolved_type_name(node) in _INT_TYPES


def _is_float_like_expr(node: Any) -> bool:
    if isinstance(node, float):
        return True
    if not isinstance(node, dict):
        return False
    if node.get("kind") == "Constant":
        return isinstance(node.get("value"), float)
    return _resolved_type_name(node) in _FLOAT_TYPES


def _is_bool_like_expr(node: Any) -> bool:
    if isinstance(node, bool):
        return True
    if not isinstance(node, dict):
        return False
    if node.get("kind") == "Constant":
        return isinstance(node.get("value"), bool)
    return _resolved_type_name(node) == "bool"


def _render_int_cast(node: Any) -> str:
    rendered = _render_expr(node)
    if _is_int_like_expr(node):
        return rendered
    return "__pytra_int(" + rendered + ")"


def _render_float_cast(node: Any) -> str:
    if isinstance(node, dict) and node.get("kind") == "Constant":
        value_any = node.get("value")
        if isinstance(value_any, bool):
            return "1.0" if value_any else "0.0"
        if isinstance(value_any, int):
            return str(value_any) + ".0"
        if isinstance(value_any, float):
            return str(value_any)
    rendered = _render_expr(node)
    if _is_float_like_expr(node):
        return rendered
    return "__pytra_float(" + rendered + ")"


def _render_bool_cast(node: Any) -> str:
    rendered = _render_expr(node)
    if _is_bool_like_expr(node):
        return rendered
    return "__pytra_truthy(" + rendered + ")"


def _render_condition_expr(node: Any) -> str:
    rendered = _render_expr(node)
    if _is_bool_like_expr(node):
        return rendered
    return "__pytra_truthy(" + rendered + ")"


def _strip_outer_parens(text: str) -> str:
    s = text.strip()
    while len(s) >= 2 and s.startswith("(") and s.endswith(")"):
        depth = 0
        in_str = False
        esc = False
        quote = ""
        wrapped = True
        i = 0
        while i < len(s):
            ch = s[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == quote:
                    in_str = False
                i += 1
                continue
            if ch == "'" or ch == '"':
                in_str = True
                quote = ch
                i += 1
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    wrapped = False
                    break
            i += 1
        if wrapped and depth == 0:
            s = s[1:-1].strip()
            continue
        break
    return s


def _is_simple_binop_operand(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    kind = node.get("kind")
    return kind in {"Name", "Constant", "Attribute", "Call", "Subscript"}


def _join_binop_expr(left: str, right: str, op_symbol: str, left_node: Any, right_node: Any) -> str:
    if _is_simple_binop_operand(left_node) and _is_simple_binop_operand(right_node):
        return _strip_outer_parens(left) + " " + op_symbol + " " + _strip_outer_parens(right)
    return "(" + left + " " + op_symbol + " " + right + ")"


def _bin_op_precedence(op: Any) -> int:
    if op in {"Mult", "Div", "FloorDiv", "Mod"}:
        return 20
    if op in {"Add", "Sub"}:
        return 10
    if op in {"LShift", "RShift"}:
        return 9
    if op == "BitAnd":
        return 8
    if op == "BitXor":
        return 7
    if op == "BitOr":
        return 6
    return 0


def _wrap_binop_operand_if_needed(text: str, node: Any, parent_op: Any, *, is_right: bool) -> str:
    if not isinstance(node, dict) or node.get("kind") != "BinOp":
        return text
    child_op = node.get("op")
    parent_prec = _bin_op_precedence(parent_op)
    child_prec = _bin_op_precedence(child_op)
    need_wrap = False
    if child_prec < parent_prec:
        need_wrap = True
    elif child_prec == parent_prec and is_right and parent_op in {"Sub", "Div", "FloorDiv", "Mod", "LShift", "RShift"}:
        need_wrap = True
    if not need_wrap:
        return text
    return "(" + _strip_outer_parens(text) + ")"


def _render_name_expr(expr: dict[str, Any]) -> str:
    raw = expr.get("id")
    if raw == "self":
        return "self"
    ident = _safe_ident(raw, "value")
    if ident == "main" and "__pytra_main" in _FUNCTION_NAMES and "main" not in _FUNCTION_NAMES:
        return "__pytra_main"
    if ident == "self":
        return "self"
    return ident


def _render_isinstance_check(lhs: str, typ: Any) -> str:
    if not isinstance(typ, dict):
        return "false"
    if typ.get("kind") == "Name":
        name = _safe_ident(typ.get("id"), "")
        if name in {"int", "int64"}:
            return lhs + ".is_a?(Integer)"
        if name in {"float", "float64"}:
            return lhs + ".is_a?(Float)"
        if name == "bool":
            return "(" + lhs + ".is_a?(TrueClass) || " + lhs + ".is_a?(FalseClass))"
        if name == "str":
            return lhs + ".is_a?(String)"
        if name in {"list", "tuple", "bytes", "bytearray"}:
            return lhs + ".is_a?(Array)"
        if name == "dict":
            return lhs + ".is_a?(Hash)"
        if name in _CLASS_NAMES:
            return lhs + ".is_a?(" + name + ")"
        return "false"
    if typ.get("kind") == "Tuple":
        elems_any = typ.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        checks: list[str] = []
        i = 0
        while i < len(elems):
            checks.append(_render_isinstance_check(lhs, elems[i]))
            i += 1
        if len(checks) == 0:
            return "false"
        return "(" + " || ".join(checks) + ")"
    return "false"


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    semantic_tag_any = expr.get("semantic_tag")
    semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
    runtime_call, runtime_source = _resolved_runtime_call(expr)
    if semantic_tag.startswith("stdlib.") and runtime_call == "":
        raise RuntimeError("ruby native emitter: unresolved stdlib runtime attribute: " + semantic_tag)
    if runtime_call == "path_parent":
        return _render_expr(expr.get("value")) + ".parent"
    if runtime_call == "path_name":
        return _render_expr(expr.get("value")) + ".name"
    if runtime_call == "path_stem":
        return _render_expr(expr.get("value")) + ".stem"
    runtime_symbol = _resolved_runtime_symbol(runtime_call, runtime_source)
    if runtime_symbol != "":
        if _is_math_constant(expr):
            return runtime_symbol + "()"
        return runtime_symbol

    value = _render_expr(expr.get("value"))
    attr = _safe_ident(expr.get("attr"), "field")
    return value + "." + attr


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
        return "(!" + _render_condition_expr(expr.get("operand")) + ")"
    return operand


def _render_binop_expr(expr: dict[str, Any]) -> str:
    left_node = expr.get("left")
    right_node = expr.get("right")
    left = _render_expr(left_node)
    right = _render_expr(right_node)
    op = expr.get("op")
    left_wrapped = _wrap_binop_operand_if_needed(left, left_node, op, is_right=False)
    right_wrapped = _wrap_binop_operand_if_needed(right, right_node, op, is_right=True)
    if op == "Div":
        if _is_nonzero_numeric_constant(right_node):
            return _join_binop_expr(
                _wrap_binop_operand_if_needed(_render_float_cast(left_node), left_node, op, is_right=False),
                _wrap_binop_operand_if_needed(_render_float_cast(right_node), right_node, op, is_right=True),
                "/",
                left_node,
                right_node,
            )
        return "__pytra_div(" + left_wrapped + ", " + right_wrapped + ")"
    if op == "FloorDiv":
        return _join_binop_expr(
            _wrap_binop_operand_if_needed(_render_int_cast(left_node), left_node, op, is_right=False),
            _wrap_binop_operand_if_needed(_render_int_cast(right_node), right_node, op, is_right=True),
            "/",
            left_node,
            right_node,
        )
    return _join_binop_expr(left_wrapped, right_wrapped, _bin_op_symbol(op), left_node, right_node)


def _render_compare_expr(expr: dict[str, Any]) -> str:
    ops_any = expr.get("ops")
    comps_any = expr.get("comparators")
    ops = ops_any if isinstance(ops_any, list) else []
    comps = comps_any if isinstance(comps_any, list) else []
    if len(ops) == 0 or len(comps) == 0:
        return "false"
    left = _render_expr(expr.get("left"))
    right = _render_expr(comps[0])
    op0 = ops[0]
    if op0 == "In":
        return "__pytra_contains(" + right + ", " + left + ")"
    if op0 == "NotIn":
        return "(!__pytra_contains(" + right + ", " + left + "))"
    symbol = _cmp_symbol(op0)
    return "(" + left + " " + symbol + " " + right + ")"


def _render_boolop_expr(expr: dict[str, Any]) -> str:
    values_any = expr.get("values")
    values = values_any if isinstance(values_any, list) else []
    if len(values) == 0:
        return "false"
    rendered: list[str] = []
    i = 0
    while i < len(values):
        rendered.append(_render_condition_expr(values[i]))
        i += 1
    op = expr.get("op")
    delim = " && " if op == "And" else " || "
    return "(" + delim.join(rendered) + ")"


def _render_subscript_expr(expr: dict[str, Any]) -> str:
    owner = _render_expr(expr.get("value"))
    slice_any = expr.get("slice")
    if isinstance(slice_any, dict) and slice_any.get("kind") == "Slice":
        lower_any = slice_any.get("lower")
        upper_any = slice_any.get("upper")
        lower = _render_expr(lower_any) if isinstance(lower_any, dict) else "0"
        upper = _render_expr(upper_any) if isinstance(upper_any, dict) else "__pytra_len(" + owner + ")"
        return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"
    index = _render_expr(slice_any)
    return "__pytra_get_index(" + owner + ", " + index + ")"


def _render_ifexp_expr(expr: dict[str, Any]) -> str:
    test = _render_condition_expr(expr.get("test"))
    body = _render_expr(expr.get("body"))
    orelse = _render_expr(expr.get("orelse"))
    return "(" + test + " ? " + body + " : " + orelse + ")"


def _render_list_expr(expr: dict[str, Any]) -> str:
    elems_any = expr.get("elements")
    elems = elems_any if isinstance(elems_any, list) else []
    out: list[str] = []
    i = 0
    while i < len(elems):
        out.append(_render_expr(elems[i]))
        i += 1
    return "[" + ", ".join(out) + "]"


def _render_dict_expr(expr: dict[str, Any]) -> str:
    entries_any = expr.get("entries")
    entries = entries_any if isinstance(entries_any, list) else []
    if len(entries) > 0:
        pairs_from_entries: list[str] = []
        i = 0
        while i < len(entries):
            entry_any = entries[i]
            if isinstance(entry_any, dict):
                key_any = entry_any.get("key")
                value_any = entry_any.get("value")
                if key_any is not None and value_any is not None:
                    pairs_from_entries.append(_render_expr(key_any) + " => " + _render_expr(value_any))
            i += 1
        if len(pairs_from_entries) == 0:
            return "{}"
        return "{ " + ", ".join(pairs_from_entries) + " }"

    keys_any = expr.get("keys")
    vals_any = expr.get("values")
    keys = keys_any if isinstance(keys_any, list) else []
    vals = vals_any if isinstance(vals_any, list) else []
    if len(keys) == 0 or len(vals) == 0:
        return "{}"
    pairs: list[str] = []
    i = 0
    while i < len(keys) and i < len(vals):
        pairs.append(_render_expr(keys[i]) + " => " + _render_expr(vals[i]))
        i += 1
    return "{ " + ", ".join(pairs) + " }"


def _render_range_expr(expr: dict[str, Any]) -> str:
    start = _render_expr(expr.get("start"))
    stop = _render_expr(expr.get("stop"))
    step = _render_expr(expr.get("step"))
    return "__pytra_range(" + start + ", " + stop + ", " + step + ")"


def _render_list_comp_expr(expr: dict[str, Any]) -> str:
    gens_any = expr.get("generators")
    gens = gens_any if isinstance(gens_any, list) else []
    if len(gens) != 1 or not isinstance(gens[0], dict):
        return "[]"
    gen = gens[0]
    ifs_any = gen.get("ifs")
    ifs = ifs_any if isinstance(ifs_any, list) else []
    if len(ifs) != 0:
        return "[]"
    target_any = gen.get("target")
    if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
        return "[]"
    loop_var = _safe_ident(target_any.get("id"), "__lc_i")
    if loop_var == "_":
        loop_var = "__lc_i"
    elt = _render_expr(expr.get("elt"))
    iter_any = gen.get("iter")
    if isinstance(iter_any, dict) and iter_any.get("kind") == "RangeExpr":
        start = _render_expr(iter_any.get("start"))
        stop = _render_expr(iter_any.get("stop"))
        step = _render_expr(iter_any.get("step"))
        return "__pytra_list_comp_range(" + start + ", " + stop + ", " + step + ") { |" + loop_var + "| " + elt + " }"
    iter_expr = "__pytra_as_list(" + _render_expr(iter_any) + ")"
    return iter_expr + ".map { |" + loop_var + "| " + elt + " }"


def _render_call_expr(expr: dict[str, Any]) -> str:
    args_any = expr.get("args")
    args = args_any if isinstance(args_any, list) else []
    callee_name = _call_name(expr)
    if callee_name.startswith("py_assert_"):
        return "true"

    semantic_tag_any = expr.get("semantic_tag")
    semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
    runtime_call, runtime_source = _resolved_runtime_call(expr)
    if semantic_tag.startswith("stdlib.") and runtime_call == "":
        raise RuntimeError("ruby native emitter: unresolved stdlib runtime call: " + semantic_tag)

    if semantic_tag == "stdlib.symbol.Path":
        rendered_path_args = _render_positional_call_args(args)
        if len(rendered_path_args) == 0:
            return "Path.new(\"\")"
        return "Path.new(" + ", ".join(rendered_path_args) + ")"

    runtime_symbol = _resolved_runtime_symbol(runtime_call, runtime_source)
    if runtime_symbol != "":
        rendered_runtime_args = _render_positional_call_args(args)
        kw_runtime = _render_keyword_call_args(expr)
        if len(kw_runtime) > 0:
            kw_names = list(kw_runtime.keys())
            kw_names.sort()
            i = 0
            while i < len(kw_names):
                rendered_runtime_args.append(kw_runtime[kw_names[i]])
                i += 1
        if runtime_source == "runtime_call":
            if semantic_tag.startswith("stdlib.fn."):
                return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
        elif runtime_source == "resolved_runtime_call":
            return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"

    if callee_name == "bytearray":
        if len(args) == 0:
            return "__pytra_bytearray()"
        return "__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee_name == "bytes":
        if len(args) == 0:
            return "__pytra_bytes([])"
        return "__pytra_bytes(" + _render_expr(args[0]) + ")"
    if callee_name == "range":
        if len(args) == 0:
            return "[]"
        if len(args) == 1:
            return "__pytra_range(0, " + _render_expr(args[0]) + ", 1)"
        if len(args) == 2:
            return "__pytra_range(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ", 1)"
        return "__pytra_range(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ", " + _render_expr(args[2]) + ")"
    if callee_name == "enumerate":
        if len(args) == 0:
            return "[]"
        return "__pytra_enumerate(" + _render_expr(args[0]) + ")"
    if callee_name == "list":
        if len(args) == 0:
            return "[]"
        return "__pytra_as_list(" + _render_expr(args[0]) + ")"
    if callee_name == "dict":
        if len(args) == 0:
            return "{}"
        return "__pytra_as_dict(" + _render_expr(args[0]) + ")"
    if callee_name == "abs":
        if len(args) == 0:
            return "0"
        return "__pytra_abs(" + _render_expr(args[0]) + ")"
    if callee_name == "isinstance":
        if len(args) < 2:
            return "false"
        return _render_isinstance_check(_render_expr(args[0]), args[1])
    if callee_name == "int":
        if len(args) == 0:
            return "0"
        return _render_int_cast(args[0])
    if callee_name == "float":
        if len(args) == 0:
            return "0.0"
        return _render_float_cast(args[0])
    if callee_name == "bool":
        if len(args) == 0:
            return "false"
        return _render_bool_cast(args[0])
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
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Call":
            if _call_name(owner_any) in {"super", "super_"}:
                rendered_super_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_super_args.append(_render_expr(args[i]))
                    i += 1
                if attr_name == "__init__":
                    return "super(" + ", ".join(rendered_super_args) + ")"
                return (
                    "self.class.superclass.instance_method(:"
                    + attr_name
                    + ").bind(self).call("
                    + ", ".join(rendered_super_args)
                    + ")"
                )
        owner = _render_expr(owner_any)
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner_name = _safe_ident(owner_any.get("id"), "")
            _ = owner_name
        if attr_name == "isdigit" and len(args) == 0:
            return "__pytra_isdigit(" + owner + ")"
        if attr_name == "isalpha" and len(args) == 0:
            return "__pytra_isalpha(" + owner + ")"
        owner_type = _resolved_type_name(owner_any)
        if attr_name == "get" and owner_type.startswith("dict[") and len(args) in {1, 2}:
            key_expr = _render_expr(args[0])
            default_expr = "nil" if len(args) == 1 else _render_expr(args[1])
            return "__pytra_as_dict(" + owner + ").fetch(" + key_expr + ", " + default_expr + ")"
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
    if kind == "Dict":
        return _render_dict_expr(expr)
    if kind == "RangeExpr":
        return _render_range_expr(expr)
    if kind == "ListComp":
        return _render_list_comp_expr(expr)
    if kind == "ObjLen":
        return "__pytra_len(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjStr":
        return "__pytra_str(" + _render_expr(expr.get("value")) + ")"
    if kind == "ObjBool":
        return "__pytra_truthy(" + _render_expr(expr.get("value")) + ")"
    if kind == "IsInstance":
        return _render_isinstance_check(_render_expr(expr.get("value")), expr.get("expected_type_id"))
    if kind == "Unbox" or kind == "Box":
        return _render_expr(expr.get("value"))
    return "nil"


def _fresh_tmp(ctx: dict[str, Any], prefix: str) -> str:
    idx = ctx.get("tmp", 0)
    if not isinstance(idx, int):
        idx = 0
    ctx["tmp"] = idx + 1
    return "__" + prefix + "_" + str(idx)


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


def _container_kind_from_decl_type(type_name: Any) -> str:
    if not isinstance(type_name, str):
        return ""
    if type_name.startswith("dict["):
        return "dict"
    if type_name.startswith("list[") or type_name.startswith("tuple["):
        return "list"
    if type_name in {"bytes", "bytearray"}:
        return "list"
    return ""


def _is_container_east_type(type_name: Any) -> bool:
    return _container_kind_from_decl_type(type_name) != ""


def _materialize_container_value_from_ref(
    value_any: Any,
    *,
    target_name: str,
    target_decl_type: Any,
    ctx: dict[str, Any],
) -> str | None:
    if target_name == "":
        return None
    if not isinstance(value_any, dict) or value_any.get("kind") != "Name":
        return None
    source_name = _safe_ident(value_any.get("id"), "")
    if source_name == "" or source_name == target_name:
        return None
    if source_name not in _ref_var_set(ctx):
        return None
    container_kind = _container_kind_from_decl_type(target_decl_type)
    if container_kind == "":
        return None
    source_expr = _render_expr(value_any)
    if container_kind == "dict":
        return "__pytra_as_dict(" + source_expr + ").dup"
    return "__pytra_as_list(" + source_expr + ").dup"


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        raise RuntimeError("ruby native emitter: unsupported ForCore iter_plan")
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("ruby native emitter: unsupported ForCore target_plan")

    lines: list[str] = []
    iter_kind = target_plan_any.get("kind")

    if iter_plan_any.get("kind") == "StaticRangeForPlan" and iter_kind == "NameTarget":
        target = _safe_ident(target_plan_any.get("id"), "i")
        if target == "_":
            target = _fresh_tmp(ctx, "loop")
        start = _render_int_cast(iter_plan_any.get("start"))
        stop = _render_int_cast(iter_plan_any.get("stop"))
        step_node = iter_plan_any.get("step")
        step = _render_int_cast(step_node)
        step_const = _const_int_literal(step_node)

        # Fastpath: canonical single-direction loops for common range forms.
        cond = ""
        inc = ""
        if step_const == 1:
            cond = target + " < " + stop
            inc = target + " += 1"
        elif step_const == -1:
            cond = target + " > " + stop
            inc = target + " -= 1"

        lines.append(indent + target + " = " + start)
        if cond == "":
            step_tmp = _fresh_tmp(ctx, "step")
            lines.append(indent + step_tmp + " = " + step)
            cond = "((" + step_tmp + " >= 0 && " + target + " < " + stop + ") || (" + step_tmp + " < 0 && " + target + " > " + stop + "))"
            inc = target + " += " + step_tmp
        lines.append(indent + "while " + cond)
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        lines.extend(_emit_stmt_list(body, indent=indent + "  ", ctx=ctx))
        lines.append(indent + "  " + inc)
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
            lines.extend(_emit_stmt_list(body, indent=indent + "  ", ctx=ctx))
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
            lines.extend(_emit_stmt_list(body, indent=indent + "  ", ctx=ctx))
            lines.append(indent + "end")
            return lines

    raise RuntimeError("ruby native emitter: unsupported ForCore plan")


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


def _is_safe_append_chain_arg(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    return node.get("kind") in {"Name", "Constant", "Attribute", "Subscript"}


def _append_chain_stmt_parts(stmt: Any) -> tuple[str, str] | None:
    if not isinstance(stmt, dict) or stmt.get("kind") != "Expr":
        return None
    value_any = stmt.get("value")
    if not isinstance(value_any, dict) or value_any.get("kind") != "Call":
        return None
    func_any = value_any.get("func")
    if not isinstance(func_any, dict) or func_any.get("kind") != "Attribute":
        return None
    if _safe_ident(func_any.get("attr"), "") != "append":
        return None
    owner_any = func_any.get("value")
    if not isinstance(owner_any, dict) or owner_any.get("kind") != "Name":
        return None
    args_any = value_any.get("args")
    args = args_any if isinstance(args_any, list) else []
    keywords_any = value_any.get("keywords")
    keywords = keywords_any if isinstance(keywords_any, list) else []
    if len(args) != 1 or len(keywords) != 0:
        return None
    arg_node = args[0]
    if not _is_safe_append_chain_arg(arg_node):
        return None
    return (_render_expr(owner_any), _render_expr(arg_node))


def _simple_name_assign_parts(stmt: Any) -> tuple[str, str] | None:
    if not isinstance(stmt, dict):
        return None
    kind = stmt.get("kind")
    if kind == "AnnAssign":
        target_any = stmt.get("target")
        value_any = stmt.get("value")
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name" or value_any is None:
            return None
        return (_render_expr(target_any), _render_expr(value_any))
    if kind != "Assign":
        return None
    targets_any = stmt.get("targets")
    targets = targets_any if isinstance(targets_any, list) else []
    if len(targets) == 0 and isinstance(stmt.get("target"), dict):
        targets = [stmt.get("target")]
    if len(targets) != 1:
        return None
    target_any = targets[0]
    value_any = stmt.get("value")
    if not isinstance(target_any, dict) or target_any.get("kind") != "Name" or value_any is None:
        return None
    return (_render_expr(target_any), _render_expr(value_any))


def _collect_leading_name_assign_map(stmts: list[Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    while i < len(stmts):
        parts = _simple_name_assign_parts(stmts[i])
        if parts is None:
            break
        out[parts[0]] = parts[1]
        i += 1
    return out


def _node_uses_any_name(node: Any, names: set[str]) -> bool:
    if isinstance(node, dict):
        if node.get("kind") == "Name":
            ident = _safe_ident(node.get("id"), "")
            if ident in names:
                return True
        for value in node.values():
            if _node_uses_any_name(value, names):
                return True
        return False
    if isinstance(node, list):
        i = 0
        while i < len(node):
            if _node_uses_any_name(node[i], names):
                return True
            i += 1
    return False


def _can_drop_preinit_before_if(stmts: list[Any], start: int, if_index: int) -> bool:
    if if_index <= start or if_index >= len(stmts):
        return False
    defaults: dict[str, str] = {}
    i = start
    while i < if_index:
        parts = _simple_name_assign_parts(stmts[i])
        if parts is None:
            return False
        defaults[parts[0]] = parts[1]
        i += 1
    if len(defaults) == 0:
        return False
    if_stmt = stmts[if_index]
    if not isinstance(if_stmt, dict) or if_stmt.get("kind") != "If":
        return False
    names = set(defaults.keys())
    if _node_uses_any_name(if_stmt.get("test"), names):
        return False
    body_any = if_stmt.get("body")
    orelse_any = if_stmt.get("orelse")
    body = body_any if isinstance(body_any, list) else []
    orelse = orelse_any if isinstance(orelse_any, list) else []
    if len(body) == 0 or len(orelse) == 0:
        return False
    body_assign = _collect_leading_name_assign_map(body)
    orelse_assign = _collect_leading_name_assign_map(orelse)
    for name, default_value in defaults.items():
        if name not in body_assign or name not in orelse_assign:
            return False
        if body_assign[name] != default_value:
            return False
    return True


def _emit_stmt_list(stmts: list[Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(stmts):
        j = i
        while j < len(stmts):
            if not isinstance(stmts[j], dict):
                break
            if stmts[j].get("kind") == "If":
                if _can_drop_preinit_before_if(stmts, i, j):
                    i = j
                break
            if _simple_name_assign_parts(stmts[j]) is None:
                break
            j += 1
        if i >= len(stmts):
            break
        head = _append_chain_stmt_parts(stmts[i])
        if head is not None:
            owner = head[0]
            args: list[str] = [head[1]]
            j = i + 1
            while j < len(stmts):
                nxt = _append_chain_stmt_parts(stmts[j])
                if nxt is None or nxt[0] != owner:
                    break
                args.append(nxt[1])
                j += 1
            if len(args) >= 2:
                out.append(indent + owner + ".concat([" + ", ".join(args) + "])")
                i = j
                continue
        out.extend(_emit_stmt(stmts[i], indent=indent, ctx=ctx))
        i += 1
    return out


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        raise RuntimeError("ruby native emitter: unsupported statement")
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
        value_any = stmt.get("value")
        target_name = _safe_ident(target_any.get("id"), "") if isinstance(target_any, dict) and target_any.get("kind") == "Name" else ""
        decl_type_any = stmt.get("decl_type")
        decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
        if decl_type == "":
            annotation_any = stmt.get("annotation")
            if isinstance(annotation_any, str):
                decl_type = annotation_any.strip()
        if value_any is None:
            if bool(stmt.get("declare")) and decl_type in _NIL_FREE_DECL_TYPES:
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    if target_name != "" and decl_type != "":
                        _type_map(ctx)[target_name] = decl_type
                    return []
        target = _render_expr(target_any)
        value = "nil" if value_any is None else _render_expr(value_any)
        materialized = _materialize_container_value_from_ref(
            value_any,
            target_name=target_name,
            target_decl_type=decl_type,
            ctx=ctx,
        )
        if materialized is not None:
            value = materialized
        if target_name != "" and decl_type != "":
            _type_map(ctx)[target_name] = decl_type
        return [indent + target + " = " + value]

    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        if len(targets) == 0:
            raise RuntimeError("ruby native emitter: Assign without target")
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
        target_name = _safe_ident(targets[0].get("id"), "") if isinstance(targets[0], dict) and targets[0].get("kind") == "Name" else ""
        decl_type_any = stmt.get("decl_type")
        decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
        if decl_type == "" and target_name != "":
            mapped_decl = _type_map(ctx).get(target_name)
            decl_type = mapped_decl.strip() if isinstance(mapped_decl, str) else ""
        materialized_assign = _materialize_container_value_from_ref(
            stmt.get("value"),
            target_name=target_name,
            target_decl_type=decl_type,
            ctx=ctx,
        )
        if materialized_assign is not None:
            value = materialized_assign
        if target_name != "" and isinstance(decl_type_any, str) and decl_type != "":
            _type_map(ctx)[target_name] = decl_type
        return [indent + target + " = " + value]

    if kind == "AugAssign":
        lhs = _render_expr(stmt.get("target"))
        rhs = _render_expr(stmt.get("value"))
        op = stmt.get("op")
        symbol = _bin_op_symbol(op)
        return [indent + lhs + " " + symbol + "= " + rhs]

    if kind == "If":
        test_expr = _strip_outer_parens(_render_condition_expr(stmt.get("test")))
        lines = [indent + "if " + test_expr]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        lines.extend(_emit_stmt_list(body, indent=indent + "  ", ctx=ctx))
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        if len(orelse) > 0:
            lines.append(indent + "else")
            lines.extend(_emit_stmt_list(orelse, indent=indent + "  ", ctx=ctx))
        lines.append(indent + "end")
        return lines

    if kind == "ForCore":
        return _emit_for_core(stmt, indent=indent, ctx=ctx)

    if kind == "While":
        test_expr = _strip_outer_parens(_render_condition_expr(stmt.get("test")))
        lines = [indent + "while " + test_expr]
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        lines.extend(_emit_stmt_list(body, indent=indent + "  ", ctx=ctx))
        lines.append(indent + "end")
        return lines

    if kind == "Pass":
        return [indent + "nil"]

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

    if kind == "Try":
        lines: list[str] = []
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        lines.extend(_emit_stmt_list(body, indent=indent, ctx=ctx))
        handlers_any = stmt.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        i = 0
        while i < len(handlers):
            h = handlers[i]
            if isinstance(h, dict):
                h_body_any = h.get("body")
                h_body = h_body_any if isinstance(h_body_any, list) else []
                lines.extend(_emit_stmt_list(h_body, indent=indent, ctx=ctx))
            i += 1
        orelse_any = stmt.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        lines.extend(_emit_stmt_list(orelse, indent=indent, ctx=ctx))
        final_any = stmt.get("finalbody")
        final = final_any if isinstance(final_any, list) else []
        lines.extend(_emit_stmt_list(final, indent=indent, ctx=ctx))
        return lines

    raise RuntimeError("ruby native emitter: unsupported stmt kind: " + str(kind))


def _function_params(fn: dict[str, Any], *, drop_self: bool) -> list[str]:
    out: list[str] = []
    order_any = fn.get("arg_order")
    order = order_any if isinstance(order_any, list) else []
    i = 0
    while i < len(order):
        raw = order[i]
        if isinstance(raw, str):
            if drop_self and i == 0 and raw == "self":
                i += 1
                continue
            name = _safe_ident(raw, "arg" + str(i))
            if drop_self and i == 0 and (name == "self" or name == "self_"):
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
    ctx: dict[str, Any] = {"tmp": 0, "types": {}, "ref_vars": set()}
    type_map = _type_map(ctx)
    ref_vars = _ref_var_set(ctx)
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    i = 0
    while i < len(params):
        param_name = params[i]
        param_type = arg_types.get(param_name)
        if isinstance(param_type, str) and param_type != "":
            type_map[param_name] = param_type
            if _is_container_east_type(param_type):
                ref_vars.add(param_name)
        i += 1
    lines.extend(_emit_stmt_list(body, indent=indent + "  ", ctx=ctx))
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
    field_names: list[str] = []
    seen_fields: set[str] = set()

    field_types_any = cls.get("field_types")
    if isinstance(field_types_any, dict):
        for raw in field_types_any.keys():
            if not isinstance(raw, str):
                continue
            nm = _safe_ident(raw, "")
            if nm == "" or nm in seen_fields:
                continue
            seen_fields.add(nm)
            field_names.append(nm)

    if len(field_names) == 0:
        i = 0
        while i < len(body):
            node = body[i]
            if isinstance(node, dict) and node.get("kind") == "AnnAssign":
                target_any = node.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    nm = _safe_ident(target_any.get("id"), "")
                    if nm != "" and nm not in seen_fields:
                        seen_fields.add(nm)
                        field_names.append(nm)
            i += 1

    if len(field_names) > 0:
        lines.append(indent + "  attr_accessor " + ", ".join([":" + n for n in field_names]))

    is_dataclass = bool(cls.get("dataclass"))
    has_init = False
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            if _safe_ident(node.get("name"), "") == "__init__":
                has_init = True
                break
        i += 1

    if is_dataclass and not has_init and len(field_names) > 0:
        lines.append("")
        lines.append(indent + "  def initialize(" + ", ".join(field_names) + ")")
        i = 0
        while i < len(field_names):
            nm = field_names[i]
            lines.append(indent + "    self." + nm + " = " + nm)
            i += 1
        lines.append(indent + "  end")

    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            lines.append("")
            lines.extend(_emit_function(node, indent=indent + "  ", in_class=True))
        i += 1
    lines.append(indent + "end")
    return lines


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
    lines.append("require_relative \"py_runtime\"")
    lines.append("")
    module_comments = _module_leading_comment_lines(east_doc, "# ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    i = 0
    while i < len(classes):
        cls_comments = _leading_comment_lines(classes[i], "# ")
        if len(cls_comments) > 0:
            lines.append("")
            lines.extend(cls_comments)
        lines.append("")
        lines.extend(_emit_class(classes[i], indent=""))
        i += 1

    i = 0
    while i < len(functions):
        fn_comments = _leading_comment_lines(functions[i], "# ")
        if len(fn_comments) > 0:
            lines.append("")
            lines.extend(fn_comments)
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
