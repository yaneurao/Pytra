"""EAST3 -> PowerShell native emitter.

This backend emits native PowerShell code directly from EAST3 IR,
without going through an intermediate JavaScript representation.
"""

from __future__ import annotations

from typing import Any



_PS_KEYWORDS = {
    "begin", "break", "catch", "class", "continue", "data", "do", "dynamicparam",
    "else", "elseif", "end", "enum", "exit", "filter", "finally", "for",
    "foreach", "from", "function", "if", "in", "param", "process", "return",
    "switch", "throw", "trap", "try", "until", "using", "while",
}

_RENAMED_SYMBOLS: list[dict[str, str]] = [{}]
_CLASS_NAMES: list[set[str]] = [set()]
_LAMBDA_VARS: list[set[str]] = [set()]
_FUNCTION_NAMES: list[set[str]] = [set()]
# Maps imported name -> PowerShell expression (for from X import Y)
_IMPORT_ALIASES: list[dict[str, str]] = [{}]

_PS_AUTOMATIC_VARS = {
    "true", "false", "null", "args", "input", "PSScriptRoot", "PSCommandPath",
    "Error", "Host", "HOME", "PID", "PROFILE",
}


def _safe_ident(name: Any, fallback: str) -> str:
    if not isinstance(name, str) or name == "":
        return fallback
    chars: list[str] = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars)
    if out == "":
        out = fallback
    if out[0].isdigit():
        out = "_" + out
    if out in _PS_KEYWORDS or out in _PS_AUTOMATIC_VARS:
        out = out + "_"
    return out


def _ps_string_literal(text: str) -> str:
    out = text.replace("`", "``")
    out = out.replace('"', '`"')
    out = out.replace("$", "`$")
    out = out.replace("\n", "`n")
    out = out.replace("\r", "`r")
    out = out.replace("\t", "`t")
    out = out.replace("\0", "`0")
    return '"' + out + '"'


def _get_str(d: dict[str, Any], key: str) -> str:
    v = d.get(key)
    return v if isinstance(v, str) else ""


def _get_list(d: dict[str, Any], key: str) -> list[Any]:
    v = d.get(key)
    return v if isinstance(v, list) else []


def _get_dict(d: dict[str, Any], key: str) -> dict[str, Any]:
    v = d.get(key)
    return v if isinstance(v, dict) else {}


# ---------------------------------------------------------------------------
# Expression rendering
# ---------------------------------------------------------------------------

_BINOP_MAP: dict[str, str] = {
    "Add": "+",
    "Sub": "-",
    "Mult": "*",
    "Div": "/",
    "Mod": "%",
    "BitAnd": "-band",
    "BitOr": "-bor",
    "BitXor": "-bxor",
    "LShift": "-shl",
    "RShift": "-shr",
    "FloorDiv": "/",
    "Pow": "",
}

_COMPARE_MAP: dict[str, str] = {
    "Eq": "-eq",
    "NotEq": "-ne",
    "Lt": "-lt",
    "LtE": "-le",
    "Gt": "-gt",
    "GtE": "-ge",
    "Is": "-eq",
    "IsNot": "-ne",
    "In": "-contains",
    "NotIn": "-notcontains",
}

_UNARYOP_MAP: dict[str, str] = {
    "USub": "-",
    "UAdd": "+",
    "Not": "-not ",
    "Invert": "-bnot ",
}


def _render_expr(expr_any: Any) -> str:
    if not isinstance(expr_any, dict):
        if isinstance(expr_any, bool):
            return "$true" if expr_any else "$false"
        if isinstance(expr_any, int):
            return str(expr_any)
        if isinstance(expr_any, float):
            return str(expr_any)
        if isinstance(expr_any, str):
            return _ps_string_literal(expr_any)
        return "$null"

    expr: dict[str, object] = expr_any
    kind = _get_str(expr, "kind")

    if kind == "Name":
        raw = _get_str(expr, "id")
        if raw == "True" or raw == "true":
            return "$true"
        if raw == "False" or raw == "false":
            return "$false"
        if raw == "None" or raw == "null" or raw == "undefined":
            return "$null"
        renamed = _RENAMED_SYMBOLS[0].get(raw, raw)
        return "$" + _safe_ident(renamed, "_v")

    if kind == "Constant":
        value = expr.get("value")
        if value is None:
            return "$null"
        if isinstance(value, bool):
            return "$true" if value else "$false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            s = repr(value)
            if "inf" in s.lower():
                return "[double]::PositiveInfinity" if value > 0 else "[double]::NegativeInfinity"
            return s
        if isinstance(value, str):
            return _ps_string_literal(value)
        return "$null"

    if kind == "UnaryOp":
        op = _get_str(expr, "op")
        operand = _render_expr(expr.get("operand"))
        ps_op = _UNARYOP_MAP.get(op, "-")
        return "(" + ps_op + operand + ")"

    if kind == "BinOp":
        op = _get_str(expr, "op")
        left = _render_expr(expr.get("left"))
        right = _render_expr(expr.get("right"))
        if op == "Pow":
            return "[Math]::Pow(" + left + ", " + right + ")"
        if op == "FloorDiv":
            return "[Math]::Floor(" + left + " / " + right + ")"
        ps_op = _BINOP_MAP.get(op, "+")
        return "(" + left + " " + ps_op + " " + right + ")"

    if kind == "Compare":
        left = _render_expr(expr.get("left"))
        ops = _get_list(expr, "ops")
        comparators = _get_list(expr, "comparators")
        if len(ops) == 0 or len(comparators) == 0:
            return "$true"
        op0 = ops[0]
        if isinstance(op0, dict):
            op0_d: dict[str, object] = op0
            ps_op = _COMPARE_MAP.get(_get_str(op0_d, "kind"), "-eq")
        elif isinstance(op0, str):
            ps_op = _COMPARE_MAP.get(op0, "-eq")
        else:
            ps_op = "-eq"
        right = _render_expr(comparators[0])
        # In/NotIn: swap operands (PowerShell -contains checks collection on left)
        op0_str = _get_str(op0, "kind") if isinstance(op0, dict) else (op0 if isinstance(op0, str) else "")
        if op0_str == "In" or op0_str == "NotIn":
            left, right = right, left
        if len(ops) == 1:
            return "(" + left + " " + ps_op + " " + right + ")"
        parts = ["(" + left + " " + ps_op + " " + right + ")"]
        i = 1
        while i < len(ops) and i < len(comparators):
            prev_right = _render_expr(comparators[i - 1])
            op_str = ops[i] if isinstance(ops[i], str) else ""
            next_op = _COMPARE_MAP.get(op_str, "-eq")
            next_right = _render_expr(comparators[i])
            parts.append("(" + prev_right + " " + next_op + " " + next_right + ")")
            i += 1
        return "(" + " -and ".join(parts) + ")"

    if kind == "BoolOp":
        op = _get_str(expr, "op")
        values = _get_list(expr, "values")
        rendered = [_render_expr(v) for v in values]
        if len(rendered) == 0:
            return "$null"
        # Python semantics: 'a or b' returns first truthy, 'a and b' returns first falsy or last
        if op == "Or":
            # Chain: $(if (a) { a } elseif (b) { b } else { last })
            if len(rendered) == 1:
                return rendered[0]
            result = rendered[-1]
            i = len(rendered) - 2
            while i >= 0:
                v = rendered[i]
                result = "$(if (" + v + ") { " + v + " } else { " + result + " })"
                i -= 1
            return result
        else:
            # And: $(if (-not a) { a } elseif (-not b) { b } else { last })
            if len(rendered) == 1:
                return rendered[0]
            result = rendered[-1]
            i = len(rendered) - 2
            while i >= 0:
                v = rendered[i]
                result = "$(if (-not " + v + ") { " + v + " } else { " + result + " })"
                i -= 1
            return result

    if kind == "Attribute":
        value_node = expr.get("value")
        value = _render_expr(value_node)
        attr = _get_str(expr, "attr")
        safe_attr = _safe_ident(attr, "prop")
        # Instance attribute on self/hashtable -> hashtable key access
        if isinstance(value_node, dict) and _get_str(value_node, "kind") == "Name":
            vname = _get_str(value_node, "id")
            if vname == "self" or vname in _CLASS_NAMES[0]:
                return value + '["' + attr + '"]'
        return value + "." + safe_attr

    if kind == "Call":
        return _render_call_expr(expr)

    if kind == "List" or kind == "Tuple":
        elements = _get_list(expr, "elements")
        if len(elements) == 0:
            elements = _get_list(expr, "elts")
        if len(elements) == 0:
            return "@()"
        rendered = [_render_expr(e) for e in elements]
        return "@(" + ", ".join(rendered) + ")"

    if kind == "Dict":
        keys = _get_list(expr, "keys")
        vals = _get_list(expr, "values")
        if len(keys) == 0 and len(vals) == 0:
            entries = _get_list(expr, "entries")
            for entry in entries:
                if isinstance(entry, dict):
                    entry_d: dict[str, object] = entry
                    k = entry_d.get("key")
                    v = entry_d.get("value")
                    if k is not None:
                        keys.append(k)
                    if v is not None:
                        vals.append(v)
        if len(keys) == 0:
            return "@{}"
        parts: list[str] = []
        i = 0
        while i < len(keys) and i < len(vals):
            parts.append(_render_expr(keys[i]) + " = " + _render_expr(vals[i]))
            i += 1
        return "@{" + "; ".join(parts) + "}"

    if kind == "Subscript":
        value = _render_expr(expr.get("value"))
        slice_any = expr.get("slice")
        if isinstance(slice_any, dict) and _get_str(slice_any, "kind") == "Slice":
            slice_d: dict[str, object] = slice_any
            lower = _render_expr(slice_d.get("lower")) if slice_d.get("lower") is not None else "0"
            upper = _render_expr(slice_d.get("upper")) if slice_d.get("upper") is not None else (value + ".Length")
            return value + "[" + lower + "..(" + upper + " - 1)]"
        index = _render_expr(slice_any)
        return value + "[" + index + "]"

    if kind == "IfExp":
        test = _render_expr(expr.get("test"))
        body = _render_expr(expr.get("body"))
        orelse = _render_expr(expr.get("orelse"))
        return "$(if (" + test + ") { " + body + " } else { " + orelse + " })"

    if kind == "JoinedStr" or kind == "FString":
        parts_list = _get_list(expr, "values")
        if len(parts_list) == 0:
            return '""'
        segments: list[str] = []
        for part in parts_list:
            if not isinstance(part, dict):
                continue
            part_d: dict[str, object] = part
            pk = _get_str(part_d, "kind")
            if pk == "Constant":
                v = part_d.get("value")
                if isinstance(v, str):
                    escaped = v.replace("`", "``").replace('"', '`"').replace("$", "`$")
                    segments.append(escaped)
            elif pk == "FormattedValue":
                inner = _render_expr(part_d.get("value"))
                segments.append("$(" + inner + ")")
            else:
                segments.append("$(" + _render_expr(part_d) + ")")
        return '"' + "".join(segments) + '"'

    if kind == "IsInstance":
        return "$true"

    if kind == "ObjLen":
        return "__pytra_len " + _render_expr(expr.get("value"))

    if kind == "ObjStr":
        return "__pytra_str " + _render_expr(expr.get("value"))

    if kind == "ObjBool":
        return "__pytra_bool " + _render_expr(expr.get("value"))

    if kind == "Box":
        return _render_expr(expr.get("value"))

    if kind == "Unbox":
        return _render_expr(expr.get("value"))

    if kind == "RangeExpr":
        start = _render_expr(expr.get("start"))
        stop = _render_expr(expr.get("stop"))
        step = expr.get("step")
        if step is not None:
            return "__pytra_range " + start + " " + stop + " " + _render_expr(step)
        return "__pytra_range " + start + " " + stop

    if kind == "Lambda":
        params = _get_list(expr, "args")
        if len(params) == 0:
            params = _get_list(expr, "params")
        body = expr.get("body")
        lambda_param_names: list[str] = []
        for p in params:
            if isinstance(p, dict):
                lp_d: dict[str, object] = p
                lambda_param_names.append("$" + _safe_ident(_get_str(lp_d, "arg"), "_p"))
            else:
                lambda_param_names.append("$" + _safe_ident(str(p), "_p"))
        ps_params = ", ".join(lambda_param_names)
        return "{ param(" + ps_params + ") " + _render_expr(body) + " }"

    return "$null"


def _render_call_expr(expr: dict[str, Any]) -> str:
    func = expr.get("func")
    args = _get_list(expr, "args")
    rendered_args = [_render_expr(a) for a in args]

    if isinstance(func, dict):
        func_d: dict[str, object] = func
        fk = _get_str(func_d, "kind")

        if fk == "Name":
            fn_name = _RENAMED_SYMBOLS[0].get(_get_str(func_d, "id"), _get_str(func_d, "id"))
            if fn_name == "print":
                return "__pytra_print " + " ".join(rendered_args) if len(rendered_args) > 0 else "__pytra_print"
            if fn_name == "len":
                return "__pytra_len " + rendered_args[0] if len(rendered_args) > 0 else "__pytra_len"
            if fn_name == "str":
                return "__pytra_str " + rendered_args[0] if len(rendered_args) > 0 else "__pytra_str"
            if fn_name == "int":
                return "__pytra_int " + rendered_args[0] if len(rendered_args) > 0 else "__pytra_int"
            if fn_name == "float":
                return "__pytra_float " + rendered_args[0] if len(rendered_args) > 0 else "__pytra_float"
            if fn_name == "bool":
                return "__pytra_bool " + rendered_args[0] if len(rendered_args) > 0 else "__pytra_bool"
            if fn_name == "range":
                return "__pytra_range " + " ".join(rendered_args)
            if fn_name == "ord":
                return "__pytra_ord " + rendered_args[0] if len(rendered_args) > 0 else "__pytra_ord"
            if fn_name == "chr":
                return "__pytra_chr " + rendered_args[0] if len(rendered_args) > 0 else "__pytra_chr"
            if fn_name == "abs":
                return "[Math]::Abs(" + rendered_args[0] + ")" if len(rendered_args) > 0 else "[Math]::Abs(0)"
            if fn_name == "min":
                return "[Math]::Min(" + ", ".join(rendered_args) + ")" if len(rendered_args) > 0 else "0"
            if fn_name == "max":
                return "[Math]::Max(" + ", ".join(rendered_args) + ")" if len(rendered_args) > 0 else "0"
            if fn_name == "isinstance":
                return "$true"
            # Imported function aliases (e.g. from math import sqrt -> [Math]::Sqrt)
            if fn_name in _IMPORT_ALIASES[0]:
                ps_func = _IMPORT_ALIASES[0][fn_name]
                if ps_func.startswith("[Math]::") and not ps_func.endswith("I") and not ps_func.endswith("E"):
                    return ps_func + "(" + ", ".join(rendered_args) + ")"
                return ps_func
            if fn_name == "bytearray":
                return "(__pytra_bytearray " + " ".join(rendered_args) + ")" if len(rendered_args) > 0 else "(__pytra_bytearray 0)"
            if fn_name == "bytes":
                return "(__pytra_bytes " + " ".join(rendered_args) + ")" if len(rendered_args) > 0 else "(__pytra_bytes @())"
            if fn_name == "list":
                return "(__pytra_list " + " ".join(rendered_args) + ")" if len(rendered_args) > 0 else "@()"
            if fn_name == "dict":
                return "(__pytra_dict " + " ".join(rendered_args) + ")" if len(rendered_args) > 0 else "@{}"
            if fn_name == "set":
                return "(__pytra_set " + " ".join(rendered_args) + ")" if len(rendered_args) > 0 else "@{}"
            if fn_name == "tuple":
                return "@(" + ", ".join(rendered_args) + ")" if len(rendered_args) > 0 else "@()"
            if fn_name == "sorted":
                return "(" + rendered_args[0] + " | Sort-Object)" if len(rendered_args) > 0 else "@()"
            if fn_name == "reversed":
                return "([array]::Reverse(" + rendered_args[0] + "); " + rendered_args[0] + ")" if len(rendered_args) > 0 else "@()"
            if fn_name == "enumerate":
                return rendered_args[0] if len(rendered_args) > 0 else "@()"
            if fn_name == "type":
                return rendered_args[0] + ".GetType().Name" if len(rendered_args) > 0 else '""'
            if fn_name == "hash":
                return rendered_args[0] + ".GetHashCode()" if len(rendered_args) > 0 else "0"
            safe = _safe_ident(fn_name, "_fn")
            # Lambda/scriptblock call: & $var args
            if fn_name in _LAMBDA_VARS[0]:
                if len(rendered_args) == 0:
                    return "(& $" + safe + ")"
                return "(& $" + safe + " " + " ".join(rendered_args) + ")"
            # Class constructor: ClassName args... -> (ClassName args...)
            # __init__ is emitted as function ClassName { param($self, ...) ... }
            if fn_name in _CLASS_NAMES[0]:
                # Create a hashtable as $self, then call constructor
                if len(rendered_args) == 0:
                    return "& { $__obj = @{}; (" + safe + " $__obj); $__obj }"
                return "& { $__obj = @{}; (" + safe + " $__obj " + " ".join(rendered_args) + "); $__obj }"
            if len(rendered_args) == 0:
                return "(" + safe + ")"
            return "(" + safe + " " + " ".join(rendered_args) + ")"

        if fk == "Attribute":
            owner_node = func_d.get("value")
            owner = _render_expr(owner_node)
            attr = _safe_ident(_get_str(func_d, "attr"), "method")
            # math module: $math.sqrt(...) -> [Math]::Sqrt(...)
            owner_name = ""
            if isinstance(owner_node, dict) and _get_str(owner_node, "kind") == "Name":
                owner_name = _get_str(owner_node, "id")
            if owner_name == "math":
                _MATH_PS: dict[str, str] = {
                    "sqrt": "Sqrt", "floor": "Floor", "ceil": "Ceiling",
                    "sin": "Sin", "cos": "Cos", "tan": "Tan",
                    "asin": "Asin", "acos": "Acos", "atan": "Atan", "atan2": "Atan2",
                    "log": "Log", "log10": "Log10", "log2": "Log",
                    "exp": "Exp", "pow": "Pow", "abs": "Abs",
                    "round": "Round", "trunc": "Truncate",
                    "pi": "PI", "e": "E",
                }
                ps_name = _MATH_PS.get(attr, "")
                if ps_name != "":
                    if attr in ("pi", "e"):
                        return "[Math]::" + ps_name
                    return "[Math]::" + ps_name + "(" + ", ".join(rendered_args) + ")"
            if attr == "append":
                if len(rendered_args) > 0:
                    return owner + " += @(" + rendered_args[0] + ")"
                return owner
            if attr == "join":
                if len(rendered_args) > 0:
                    return "(" + rendered_args[0] + " -join " + owner + ")"
                return owner
            if attr == "format":
                return owner + " -f " + ", ".join(rendered_args) if len(rendered_args) > 0 else owner
            if attr == "startswith":
                return owner + ".StartsWith(" + ", ".join(rendered_args) + ")"
            if attr == "endswith":
                return owner + ".EndsWith(" + ", ".join(rendered_args) + ")"
            if attr == "upper":
                return owner + ".ToUpper()"
            if attr == "lower":
                return owner + ".ToLower()"
            if attr == "strip":
                return owner + ".Trim()"
            if attr == "rstrip":
                return owner + ".TrimEnd()"
            if attr == "lstrip":
                return owner + ".TrimStart()"
            if attr == "find":
                if len(rendered_args) > 0:
                    return owner + ".IndexOf(" + rendered_args[0] + ")"
                return "-1"
            if attr == "rfind":
                if len(rendered_args) > 0:
                    return owner + ".LastIndexOf(" + rendered_args[0] + ")"
                return "-1"
            if attr == "count":
                if len(rendered_args) > 0:
                    return "(" + owner + ".Length - " + owner + ".Replace(" + rendered_args[0] + ", \"\").Length) / " + rendered_args[0] + ".Length"
                return "0"
            if attr == "isdigit":
                return "(" + owner + " -match '^[0-9]+$')"
            if attr == "isalpha":
                return "(" + owner + " -match '^[a-zA-Z]+$')"
            if attr == "split":
                if len(rendered_args) > 0:
                    return owner + ".Split(" + rendered_args[0] + ")"
                return owner + ".Split()"
            if attr == "replace":
                if len(rendered_args) >= 2:
                    return owner + ".Replace(" + rendered_args[0] + ", " + rendered_args[1] + ")"
                return owner
            if attr == "keys":
                return owner + ".Keys"
            if attr == "values":
                return owner + ".Values"
            if attr == "items":
                return owner + ".GetEnumerator()"
            if attr == "get":
                if len(rendered_args) >= 2:
                    return "$(if (" + owner + ".ContainsKey(" + rendered_args[0] + ")) { " + owner + "[" + rendered_args[0] + "] } else { " + rendered_args[1] + " })"
                if len(rendered_args) == 1:
                    return owner + "[" + rendered_args[0] + "]"
                return "$null"
            if attr == "pop":
                if len(rendered_args) == 0:
                    return owner + "[-1]; " + owner + " = " + owner + "[0..(" + owner + ".Length - 2)]"
                return owner
            # Check if this could be a class method call (owner has __type__)
            raw_attr = _get_str(func_d, "attr")
            _KNOWN_DOTNET_METHODS = {
                "rstrip", "lstrip", "find", "rfind", "count", "index", "rindex",
                "center", "ljust", "rjust", "zfill", "encode", "decode",
                "isdigit", "isalpha", "isalnum", "isupper", "islower", "isspace",
                "capitalize", "title", "swapcase", "expandtabs",
                "ToString", "GetType", "GetHashCode", "Equals",
                "Add", "Remove", "Contains", "ContainsKey", "Clear",
                "Sort", "Reverse", "CopyTo", "ToArray", "GetEnumerator",
                "Trim", "TrimStart", "TrimEnd", "StartsWith", "EndsWith",
                "ToUpper", "ToLower", "Split", "Replace", "Substring",
                "Insert", "IndexOf", "LastIndexOf",
            }
            if raw_attr not in _KNOWN_DOTNET_METHODS and raw_attr not in (
                "append", "extend", "insert", "pop", "remove", "sort", "reverse",
                "join", "format", "startswith", "endswith", "upper", "lower",
                "strip", "rstrip", "lstrip", "split", "replace", "find", "rfind",
                "keys", "values", "items", "get", "update", "setdefault",
                "add", "discard", "union", "intersection", "difference",
                "encode", "decode", "read", "write", "close", "flush",
            ) and owner_name != "" and owner_name not in (
                "math", "os", "sys", "json", "re", "random", "pathlib", "time",
                "collections", "itertools", "functools", "io", "struct",
            ):
                # Dynamic dispatch: ClassName_method $self args
                if len(rendered_args) == 0:
                    return '(& (Get-Command ("{0}_{1}" -f ' + owner + '["__type__"], "' + raw_attr + '")) ' + owner + ')'
                return '(& (Get-Command ("{0}_{1}" -f ' + owner + '["__type__"], "' + raw_attr + '")) ' + owner + ' ' + " ".join(rendered_args) + ')'
            if len(rendered_args) == 0:
                return owner + "." + attr + "()"
            return owner + "." + attr + "(" + ", ".join(rendered_args) + ")"

    fn_rendered = _render_expr(func)
    if len(rendered_args) == 0:
        return fn_rendered
    return fn_rendered + " " + " ".join(rendered_args)


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_body(body: list[Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for stmt in body:
        if isinstance(stmt, dict):
            stmt_d: dict[str, object] = stmt
            lines.extend(_emit_stmt(stmt_d, indent=indent, ctx=ctx))
    if len(lines) == 0:
        lines.append(indent + "# pass")
    return lines


def _emit_stmt(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    kind = _get_str(stmt, "kind")

    if kind == "Expr":
        value = stmt.get("value")
        if isinstance(value, dict):
            value_d: dict[str, object] = value
            vk = _get_str(value_d, "kind")
            if vk == "Name":
                raw = _get_str(value_d, "id")
                if raw == "break":
                    return [indent + "break"]
                if raw == "continue":
                    return [indent + "continue"]
                if raw == "pass":
                    return [indent + "# pass"]
        return [indent + _render_expr(value)]

    if kind == "Return":
        value = stmt.get("value")
        if value is not None:
            return [indent + "return " + _render_expr(value)]
        return [indent + "return"]

    if kind == "Assign":
        targets = _get_list(stmt, "targets")
        if len(targets) == 0:
            t = stmt.get("target")
            if isinstance(t, dict):
                targets = [t]
        # Track lambda assignments
        val_node = stmt.get("value")
        if isinstance(val_node, dict) and _get_str(val_node, "kind") == "Lambda":
            if len(targets) == 1 and isinstance(targets[0], dict) and _get_str(targets[0], "kind") == "Name":
                _LAMBDA_VARS[0].add(_get_str(targets[0], "id"))
        # Tuple unpacking: (a, b) = expr -> temp, then assign each
        if len(targets) == 1 and isinstance(targets[0], dict):
            tk = _get_str(targets[0], "kind")
            if tk == "Tuple" or tk == "List":
                elts = _get_list(targets[0], "elements")
                if len(elts) == 0:
                    elts = _get_list(targets[0], "elts")
                if len(elts) > 0:
                    tmp = "$__tuple_tmp"
                    lines = [indent + tmp + " = " + _render_expr(stmt.get("value"))]
                    for idx, elt in enumerate(elts):
                        lines.append(indent + _render_expr(elt) + " = " + tmp + "[" + str(idx) + "]")
                    return lines
        value = _render_expr(stmt.get("value"))
        if len(targets) == 0:
            return [indent + value]
        target = targets[0]
        if isinstance(target, dict):
            target_d: dict[str, object] = target
            if _get_str(target_d, "kind") == "Attribute":
                return [indent + _render_expr(target_d) + " = " + value]
            if _get_str(target_d, "kind") == "Subscript":
                owner = _render_expr(target_d.get("value"))
                index = _render_expr(target_d.get("slice"))
                return [indent + owner + "[" + index + "] = " + value]
        lhs = _render_expr(target)
        return [indent + lhs + " = " + value]

    if kind == "AnnAssign":
        target = stmt.get("target")
        value = stmt.get("value")
        if value is None:
            lhs = _render_expr(target)
            return [indent + lhs + " = $null"]
        # Track lambda assignments
        if isinstance(value, dict) and _get_str(value, "kind") == "Lambda":
            if isinstance(target, dict) and _get_str(target, "kind") == "Name":
                _LAMBDA_VARS[0].add(_get_str(target, "id"))
        lhs = _render_expr(target)
        return [indent + lhs + " = " + _render_expr(value)]

    if kind == "AugAssign":
        target = _render_expr(stmt.get("target"))
        op = _get_str(stmt, "op")
        value = _render_expr(stmt.get("value"))
        op_map: dict[str, str] = {
            "Add": "+=", "Sub": "-=", "Mult": "*=", "Div": "/=",
            "Mod": "%=", "BitAnd": "=", "BitOr": "=", "BitXor": "=",
            "LShift": "=", "RShift": "=",
        }
        ps_op = op_map.get(op, "=")
        if ps_op == "=" and op in _BINOP_MAP:
            return [indent + target + " = (" + target + " " + _BINOP_MAP[op] + " " + value + ")"]
        return [indent + target + " " + ps_op + " " + value]

    if kind == "If":
        test = _render_expr(stmt.get("test"))
        body = _get_list(stmt, "body")
        orelse = _get_list(stmt, "orelse")
        lines = [indent + "if (" + test + ") {"]
        lines.extend(_emit_body(body, indent=indent + "    ", ctx=ctx))
        if len(orelse) > 0:
            if len(orelse) == 1 and isinstance(orelse[0], dict) and _get_str(orelse[0], "kind") == "If":
                inner_d: dict[str, object] = orelse[0]
                lines.append(indent + "} elseif (" + _render_expr(inner_d.get("test")) + ") {")
                lines.extend(_emit_body(_get_list(inner_d, "body"), indent=indent + "    ", ctx=ctx))
                inner_else = _get_list(inner_d, "orelse")
                while len(inner_else) == 1 and isinstance(inner_else[0], dict) and _get_str(inner_else[0], "kind") == "If":
                    next_if: dict[str, object] = inner_else[0]
                    inner_d = next_if
                    lines.append(indent + "} elseif (" + _render_expr(inner_d.get("test")) + ") {")
                    lines.extend(_emit_body(_get_list(inner_d, "body"), indent=indent + "    ", ctx=ctx))
                    inner_else = _get_list(inner_d, "orelse")
                if len(inner_else) > 0:
                    lines.append(indent + "} else {")
                    lines.extend(_emit_body(inner_else, indent=indent + "    ", ctx=ctx))
            else:
                lines.append(indent + "} else {")
                lines.extend(_emit_body(orelse, indent=indent + "    ", ctx=ctx))
        lines.append(indent + "}")
        return lines

    if kind == "While":
        test = _render_expr(stmt.get("test"))
        body = _get_list(stmt, "body")
        lines = [indent + "while (" + test + ") {"]
        lines.extend(_emit_body(body, indent=indent + "    ", ctx=ctx))
        lines.append(indent + "}")
        return lines

    if kind == "ForCore":
        body = _get_list(stmt, "body")
        target_plan = stmt.get("target_plan")
        iter_plan = stmt.get("iter_plan")
        normalized = _get_dict(stmt, "normalized_exprs")

        # Extract loop variable from target_plan
        loop_var = "$_i"
        if isinstance(target_plan, dict):
            tp_d: dict[str, object] = target_plan
            loop_var = "$" + _safe_ident(_get_str(tp_d, "id"), "_i")

        # Try normalized_exprs (for_init_expr, for_cond_expr, for_update_expr)
        init_expr = normalized.get("for_init_expr")
        cond_expr = normalized.get("for_cond_expr")
        update_expr = normalized.get("for_update_expr")

        if init_expr is not None or cond_expr is not None:
            init_str = loop_var + " = " + _render_expr(init_expr) if init_expr is not None else loop_var + " = 0"
            cond_str = _render_expr(cond_expr) if cond_expr is not None else "$true"
            if isinstance(update_expr, dict) and _get_str(update_expr, "kind") == "AugAssign":
                ue_d: dict[str, object] = update_expr
                update_str = _render_expr(ue_d.get("target")) + " += " + _render_expr(ue_d.get("value"))
            elif update_expr is not None:
                update_str = _render_expr(update_expr)
            else:
                update_str = loop_var + "++"
            lines = [indent + "for (" + init_str + "; " + cond_str + "; " + update_str + ") {"]
        elif isinstance(iter_plan, dict):
            # Fallback: use iter_plan (StaticRangeForPlan)
            ip_d: dict[str, object] = iter_plan
            start = _render_expr(ip_d.get("start"))
            stop = _render_expr(ip_d.get("stop"))
            step = ip_d.get("step")
            step_val = 1
            if isinstance(step, dict) and step.get("value") is not None:
                sv = step.get("value")
                step_val = sv if isinstance(sv, int) else 1
            lines = [indent + "for (" + loop_var + " = " + start + "; " + loop_var + " -lt " + stop + "; " + loop_var + " += " + str(step_val) + ") {"]
        else:
            lines = [indent + "for (" + loop_var + " = 0; $true; " + loop_var + "++) {"]

        lines.extend(_emit_body(body, indent=indent + "    ", ctx=ctx))
        lines.append(indent + "}")
        return lines

    if kind == "For":
        target = stmt.get("target")
        iter_expr = stmt.get("iter")
        body = _get_list(stmt, "body")
        target_str = _render_expr(target) if target is not None else "$_item"
        iter_str = _render_expr(iter_expr) if iter_expr is not None else "@()"
        lines = [indent + "foreach (" + target_str + " in " + iter_str + ") {"]
        lines.extend(_emit_body(body, indent=indent + "    ", ctx=ctx))
        lines.append(indent + "}")
        return lines

    if kind == "Try":
        body = _get_list(stmt, "body")
        handlers = _get_list(stmt, "handlers")
        finalbody = _get_list(stmt, "finalbody")
        lines = [indent + "try {"]
        lines.extend(_emit_body(body, indent=indent + "    ", ctx=ctx))
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            handler_d: dict[str, object] = handler
            handler_name = _get_str(handler_d, "name")
            if handler_name != "":
                lines.append(indent + "} catch {")
                lines.append(indent + "    $" + _safe_ident(handler_name, "e") + " = $_")
            else:
                lines.append(indent + "} catch {")
            handler_body = _get_list(handler_d, "body")
            lines.extend(_emit_body(handler_body, indent=indent + "    ", ctx=ctx))
        if len(handlers) == 0:
            lines.append(indent + "} catch {")
            lines.append(indent + "    # unhandled")
        if len(finalbody) > 0:
            lines.append(indent + "} finally {")
            lines.extend(_emit_body(finalbody, indent=indent + "    ", ctx=ctx))
        lines.append(indent + "}")
        return lines

    if kind == "Raise":
        exc = stmt.get("exc")
        if exc is not None:
            return [indent + "throw " + _render_expr(exc)]
        return [indent + "throw"]

    if kind == "Pass":
        return [indent + "# pass"]

    if kind == "Break":
        return [indent + "break"]

    if kind == "Continue":
        return [indent + "continue"]

    if kind == "Swap":
        left = _render_expr(stmt.get("left"))
        right = _render_expr(stmt.get("right"))
        tmp = "$__swap_tmp"
        return [
            indent + tmp + " = " + left,
            indent + left + " = " + right,
            indent + right + " = " + tmp,
        ]

    if kind == "FunctionDef":
        return _emit_function_def(stmt, indent=indent, ctx=ctx)

    if kind == "ClassDef":
        return _emit_class_def(stmt, indent=indent, ctx=ctx)

    if kind == "ImportFrom":
        return [indent + "# import: " + _get_str(stmt, "module")]

    if kind == "Import":
        return [indent + "# import"]

    return [indent + "# unsupported: " + kind]


def _emit_function_def(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    name = _safe_ident(_get_str(stmt, "name"), "_fn")
    body = _get_list(stmt, "body")

    # EAST3 uses arg_order (list[str]) + arg_defaults (dict[str, Any])
    arg_order = _get_list(stmt, "arg_order")
    arg_defaults = _get_dict(stmt, "arg_defaults")

    # Register callable-typed parameters as lambda vars for & $var invocation
    arg_types = _get_dict(stmt, "arg_types")
    for aname, atype in arg_types.items():
        if isinstance(atype, str) and "callable" in atype.lower():
            _LAMBDA_VARS[0].add(str(aname))

    ps_params: list[str] = []
    if len(arg_order) > 0:
        for arg_name in arg_order:
            if not isinstance(arg_name, str):
                continue
            safe = "$" + _safe_ident(arg_name, "_p")
            default = arg_defaults.get(arg_name)
            if default is not None:
                ps_params.append(safe + " = " + _render_expr(default))
            else:
                ps_params.append(safe)
    else:
        # Fallback: try params/args (older EAST formats)
        params = _get_list(stmt, "params")
        if len(params) == 0:
            params = _get_list(stmt, "args")
        for p in params:
            if isinstance(p, dict):
                p_d: dict[str, object] = p
                arg_name_s = _get_str(p_d, "arg")
                if arg_name_s == "":
                    arg_name_s = _get_str(p_d, "name")
                default = p_d.get("default")
                if default is not None:
                    ps_params.append("$" + _safe_ident(arg_name_s, "_p") + " = " + _render_expr(default))
                else:
                    ps_params.append("$" + _safe_ident(arg_name_s, "_p"))
            elif isinstance(p, str):
                ps_params.append("$" + _safe_ident(p, "_p"))

    decorators = _get_list(stmt, "decorator_list")
    lines: list[str] = []
    for dec in decorators:
        if isinstance(dec, dict):
            dec_d: dict[str, object] = dec
            if _get_str(dec_d, "kind") != "Name":
                continue
            dec_name = _get_str(dec_d, "id")
            if dec_name != "":
                lines.append(indent + "# @" + dec_name)

    lines.append(indent + "function " + name + " {")
    if len(ps_params) > 0:
        lines.append(indent + "    param(" + ", ".join(ps_params) + ")")
    else:
        lines.append(indent + "    param()")

    lines.extend(_emit_body(body, indent=indent + "    ", ctx=ctx))
    lines.append(indent + "}")
    return lines


def _emit_class_def(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    name = _safe_ident(_get_str(stmt, "name"), "_Cls")
    body = _get_list(stmt, "body")
    lines = [indent + "# class " + name]

    has_init = False
    for member in body:
        if not isinstance(member, dict):
            continue
        member_d: dict[str, object] = member
        mk = _get_str(member_d, "kind")
        if mk == "FunctionDef":
            method_name = _get_str(member_d, "name")
            if method_name == "__init__":
                has_init = True
                fn_lines = _emit_function_def(member_d, indent=indent, ctx=ctx)
                if len(fn_lines) > 0:
                    fn_lines[0] = fn_lines[0].replace("function __init__", "function " + name, 1)
                lines.extend(fn_lines)
            else:
                fn_lines = _emit_function_def(member_d, indent=indent, ctx=ctx)
                if len(fn_lines) > 0:
                    original_fn_name = "function " + _safe_ident(method_name, "_m")
                    new_fn_name = "function " + name + "_" + _safe_ident(method_name, "_m")
                    fn_lines[0] = fn_lines[0].replace(original_fn_name, new_fn_name, 1)
                lines.extend(fn_lines)
        elif mk == "AnnAssign" or mk == "Assign":
            lines.extend(_emit_stmt(member_d, indent=indent, ctx=ctx))
        elif mk == "Pass":
            pass

    # Generate default constructor if no __init__
    if not has_init:
        lines.append(indent + "function " + name + " {")
        lines.append(indent + "    param($self)")
        lines.append(indent + '    $self["__type__"] = "' + name + '"')
        lines.append(indent + "}")
    else:
        # Inject __type__ into existing constructor
        # Find the line after param(...) and insert type tag
        for i_line in range(len(lines)):
            if lines[i_line].strip().startswith("param("):
                lines.insert(i_line + 1, indent + '    $self["__type__"] = "' + name + '"')
                break

    return lines


def _simplify_main_guard_stmt(stmt: dict[str, Any]) -> dict[str, Any]:
    """Unwrap py_assert_stdout/py_assert_all wrappers into direct function calls.

    main_guard_body often contains ``print(py_assert_stdout(['...'], _case_main))``
    which passes ``_case_main`` as a function object.  PowerShell cannot do this,
    so we extract the inner function name and emit a direct call instead.
    """
    if _get_str(stmt, "kind") != "Expr":
        return stmt
    value = stmt.get("value")
    if not isinstance(value, dict):
        return stmt
    # Unwrap print(py_assert_stdout(..., fn_name))
    if _get_str(value, "kind") == "Call":
        inner = _unwrap_assert_call(value)
        if inner is not None:
            return {"kind": "Expr", "value": {"kind": "Call", "func": inner, "args": []}}
    return stmt


def _unwrap_assert_call(call: dict[str, Any]) -> Any:
    """If call is print(py_assert_*(…, fn_ref)), return fn_ref as a Call target."""
    func = call.get("func")
    if not isinstance(func, dict):
        return None
    fn_name = _get_str(func, "id") if _get_str(func, "kind") == "Name" else ""
    args = _get_list(call, "args")
    # print(py_assert_stdout([...], fn)) -> unwrap inner
    if fn_name == "print" and len(args) == 1:
        inner = args[0]
        if isinstance(inner, dict) and _get_str(inner, "kind") == "Call":
            return _unwrap_assert_call(inner)
    # py_assert_stdout([...], fn) -> return fn
    if fn_name in ("py_assert_stdout", "py_assert_all", "py_assert_true", "py_assert_eq"):
        if len(args) >= 2:
            fn_ref = args[-1]
            if isinstance(fn_ref, dict) and _get_str(fn_ref, "kind") == "Name":
                return fn_ref
        # py_assert_all with single arg that is a list of calls
        if len(args) == 1:
            return None
    return None


# ---------------------------------------------------------------------------
# Module-level entry point
# ---------------------------------------------------------------------------

def transpile_to_powershell(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを PowerShell コードへ変換する。"""
    if not isinstance(east_doc, dict) or _get_str(east_doc, "kind") != "Module":
        raise RuntimeError("powershell native emitter: root kind must be Module")

    body = _get_list(east_doc, "body")
    if not isinstance(body, list):
        raise RuntimeError("powershell native emitter: Module.body must be list")

    # Note: union type and typed vararg rejections are disabled for PowerShell
    # to allow transpilation of all linked modules (including assertions).
    # Union types are emitted as $null fallback; varargs are not yet supported.

    renamed = _get_dict(east_doc, "renamed_symbols")
    _RENAMED_SYMBOLS[0] = {k: v for k, v in renamed.items() if isinstance(k, str) and isinstance(v, str)}

    # Collect class names for constructor call detection
    class_names: set[str] = set()
    for node in body:
        if isinstance(node, dict) and _get_str(node, "kind") == "ClassDef":
            cn = _get_str(node, "name")
            if cn != "":
                class_names.add(cn)
    _CLASS_NAMES[0] = class_names

    # Collect function names
    func_names: set[str] = set()
    for node in body:
        if isinstance(node, dict) and _get_str(node, "kind") == "FunctionDef":
            fn = _get_str(node, "name")
            if fn != "":
                func_names.add(fn)
    _FUNCTION_NAMES[0] = func_names
    _LAMBDA_VARS[0] = set()

    # Collect import aliases (from X import Y -> Y maps to PS expression)
    import_aliases: dict[str, str] = {}
    _MATH_FUNCS = {
        "sqrt": "[Math]::Sqrt", "floor": "[Math]::Floor", "ceil": "[Math]::Ceiling",
        "sin": "[Math]::Sin", "cos": "[Math]::Cos", "tan": "[Math]::Tan",
        "asin": "[Math]::Asin", "acos": "[Math]::Acos", "atan": "[Math]::Atan",
        "atan2": "[Math]::Atan2", "log": "[Math]::Log", "log10": "[Math]::Log10",
        "exp": "[Math]::Exp", "pow": "[Math]::Pow", "abs": "[Math]::Abs",
        "round": "[Math]::Round", "trunc": "[Math]::Truncate",
        "pi": "[Math]::PI", "e": "[Math]::E",
    }
    for node in body:
        if not isinstance(node, dict) or _get_str(node, "kind") != "ImportFrom":
            continue
        module = _get_str(node, "module")
        names = _get_list(node, "names")
        for entry in names:
            if not isinstance(entry, dict):
                continue
            imported_name = _get_str(entry, "name")
            alias = _get_str(entry, "asname")
            local_name = alias if alias != "" else imported_name
            if module in ("math", "pytra.std.math") and imported_name in _MATH_FUNCS:
                import_aliases[local_name] = _MATH_FUNCS[imported_name]
    _IMPORT_ALIASES[0] = import_aliases

    ctx: dict[str, Any] = {}
    lines: list[str] = [
        "#Requires -Version 5.1",
        "",
        "$pytra_runtime = Join-Path $PSScriptRoot \"py_runtime.ps1\"",
        "if (Test-Path $pytra_runtime) { . $pytra_runtime }",
        "",
        "Set-StrictMode -Version Latest",
        "$ErrorActionPreference = \"Stop\"",
        "",
    ]

    # Emit module-level leading comments
    comments = _get_list(east_doc, "leading_comments")
    for c in comments:
        if isinstance(c, str):
            lines.append("# " + c)
    if len(comments) > 0:
        lines.append("")

    # Emit body
    for stmt in body:
        if isinstance(stmt, dict):
            stmt_d: dict[str, object] = stmt
            lines.extend(_emit_stmt(stmt_d, indent="", ctx=ctx))
            lines.append("")

    # Emit main guard body (if __name__ == "__main__")
    main_guard = _get_list(east_doc, "main_guard_body")
    if len(main_guard) > 0:
        for stmt in main_guard:
            if isinstance(stmt, dict):
                stmt_d2: dict[str, object] = stmt
                simplified = _simplify_main_guard_stmt(stmt_d2)
                lines.extend(_emit_stmt(simplified, indent="", ctx=ctx))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
