"""EAST3 -> PowerShell native emitter.

This backend emits native PowerShell code directly from EAST3 IR,
without going through an intermediate JavaScript representation.
"""

from __future__ import annotations

from typing import Any

from toolchain.emit.common.emitter.code_emitter import build_import_alias_map



_PS_KEYWORDS = {
    "begin", "break", "catch", "class", "continue", "data", "do", "dynamicparam",
    "else", "elseif", "end", "enum", "exit", "filter", "finally", "for",
    "foreach", "from", "function", "if", "in", "param", "process", "return",
    "switch", "throw", "trap", "try", "until", "using", "while",
}

_RENAMED_SYMBOLS: list[dict[str, str]] = [{}]
_CLASS_NAMES: list[set[str]] = [set()]
_CLASS_BASES: list[dict[str, str]] = [{}]
_CLASS_METHOD_NAMES: list[dict[str, set[str]]] = [{}]
_LAMBDA_VARS: list[set[str]] = [set()]
_FUNCTION_NAMES: list[set[str]] = [set()]
_IMPORT_ALIASES: list[dict[str, str]] = [{}]
_CURRENT_CLASS_NAME: list[str] = [""]
_CLASS_PROPERTIES: list[dict[str, set[str]]] = [{}]  # ClassName -> {property_name, ...}
_MODULE_ALIAS_MAP: list[dict[str, str]] = [{}]  # local_name -> resolved_module_id

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
    out_lower = out.lower()
    if out_lower in _PS_KEYWORDS or any(out_lower == v.lower() for v in _PS_AUTOMATIC_VARS):
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


def _has_format_spec_in_doc(doc: Any) -> bool:
    """EAST doc 内に format_spec を持つ FormattedValue があるか検査する。"""
    if isinstance(doc, dict):
        if doc.get("kind") == "FormattedValue":
            fs = doc.get("format_spec")
            if isinstance(fs, str) and fs != "":
                return True
        for v in doc.values():
            if _has_format_spec_in_doc(v):
                return True
    elif isinstance(doc, list):
        for item in doc:
            if _has_format_spec_in_doc(item):
                return True
    return False


def _render_lvalue(expr_any: Any) -> str:
    """左辺値（代入ターゲット）を render する。__pytra_getattr を使わない。"""
    if not isinstance(expr_any, dict):
        return _render_expr(expr_any)
    kind = _get_str(expr_any, "kind")
    if kind == "Attribute":
        value_node = expr_any.get("value")
        value = _render_expr(value_node)
        attr = _get_str(expr_any, "attr")
        if isinstance(value_node, dict):
            vname = _get_str(value_node, "id") if _get_str(value_node, "kind") == "Name" else ""
            if vname == "self":
                return '$self["' + attr + '"]'
            if vname in _CLASS_NAMES[0]:
                # ClassName.attr = X → $script:attr = X (module-scope class variable)
                return "$script:" + _safe_ident(attr, "_cv")
        return value + '["' + attr + '"]'
    if kind == "Subscript":
        value = _render_expr(expr_any.get("value"))
        index = _render_expr(expr_any.get("slice"))
        return value + "[" + index + "]"
    return _render_expr(expr_any)


def _is_extern_value(value: Any) -> bool:
    """Check if value is extern(...) call or Unbox(extern(...))."""
    if not isinstance(value, dict):
        return False
    kind = _get_str(value, "kind")
    if kind == "Unbox":
        return _is_extern_value(value.get("value"))
    if kind == "Call":
        func = value.get("func")
        if isinstance(func, dict) and _get_str(func, "id") == "extern":
            return True
    return False


_IGNORED_IMPORT_MODULES: set[str] = {
    "typing", "pytra.typing", "dataclasses", "__future__",
    "pytra.utils.assertions", "pytra.std.extern", "pytra.std.abi",
}


def _module_to_ps_path(module: str) -> str:
    """Python モジュール名をリンク済み PS1 の相対パスに変換する。

    emit_all_modules が pytra. prefix を strip して配置するので、
    pytra.std.time → std/time.ps1 に変換する。
    root_rel_prefix を付加して、サブモジュール間の相対パスを正しく解決する。
    """
    if module == "" or module in _IGNORED_IMPORT_MODULES:
        return ""
    if module in ("pytra.std", "pytra", "pytra.utils"):
        return ""
    raw = ""
    # pytra.X → X (strip pytra. prefix, matching emit_all_modules behavior)
    if module.startswith("pytra."):
        tail = module[len("pytra."):]
        if tail != "":
            raw = tail.replace(".", "/") + ".ps1"
    if raw == "" and module.startswith("browser"):
        return ""
    # bare stdlib name (e.g. "pathlib", "json") → std/X.ps1
    if raw == "":
        cur = _CURRENT_MODULE_ID[0]
        # Self-reference check
        mod_as_id = module.replace(".", "_")
        if cur != "" and (cur == "pytra.std." + module or cur.endswith("." + module)):
            return ""
        raw = "std/" + module.replace(".", "/") + ".ps1"
    if raw == "":
        # Self-reference check for any module
        cur = _CURRENT_MODULE_ID[0]
        mod_as_id = module.replace(".", "_")
        if cur != "" and (cur == mod_as_id + ".east" or cur == mod_as_id):
            return ""
        raw = module.replace(".", "/") + ".ps1"
    # Apply root_rel_prefix for sub-module relative path resolution
    prefix = _ROOT_REL_PREFIX[0]
    if prefix != "":
        return prefix + raw
    return raw


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
        # Callable type: function names (not lambda vars) are passed as string
        rt = _get_str(expr, "resolved_type")
        if isinstance(rt, str) and rt.startswith("callable["):
            # Check both original name and renamed name
            if (raw in _FUNCTION_NAMES[0] or renamed in _FUNCTION_NAMES[0]) and raw not in _LAMBDA_VARS[0]:
                return '"' + _safe_ident(renamed, "_fn") + '"'
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
        # In/NotIn: use runtime function for polymorphic containment check
        op0_str = _get_str(op0, "kind") if isinstance(op0, dict) else (op0 if isinstance(op0, str) else "")
        if op0_str == "In":
            return "(__pytra_in " + left + " " + right + ")"
        if op0_str == "NotIn":
            return "(__pytra_not_in " + left + " " + right + ")"
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
        # Use __pytra_bool for truthiness check (Python empty string/0/None are falsy)
        if op == "Or":
            if len(rendered) == 1:
                return rendered[0]
            result = rendered[-1]
            i = len(rendered) - 2
            while i >= 0:
                v = rendered[i]
                result = "$(if ((__pytra_bool " + v + ")) { " + v + " } else { " + result + " })"
                i -= 1
            return result
        else:
            if len(rendered) == 1:
                return rendered[0]
            result = rendered[-1]
            i = len(rendered) - 2
            while i >= 0:
                v = rendered[i]
                result = "$(if (-not (__pytra_bool " + v + ")) { " + v + " } else { " + result + " })"
                i -= 1
            return result

    if kind == "Attribute":
        value_node = expr.get("value")
        value = _render_expr(value_node)
        attr = _get_str(expr, "attr")
        safe_attr = _safe_ident(attr, "prop")
        # Instance attribute on self/hashtable -> hashtable key access
        if isinstance(value_node, dict):
            vname = _get_str(value_node, "id") if _get_str(value_node, "kind") == "Name" else ""
            vtype = _get_str(value_node, "resolved_type")
            if vname == "self":
                # Check if attr is a @property → call getter
                cur_cls = _CURRENT_CLASS_NAME[0]
                if cur_cls != "" and attr in _CLASS_PROPERTIES[0].get(cur_cls, set()):
                    return "(" + cur_cls + "_" + _safe_ident(attr, "_p") + " $self)"
                return '$self["' + attr + '"]'
            # Resolve import alias for module attribute access
            if vname in _MODULE_ALIAS_MAP[0]:
                return "$" + _safe_ident(attr, "_f")
            if vname in _CLASS_NAMES[0]:
                # ClassName.attr → クラス変数 $script:attr（モジュールスコープ）
                return "$script:" + _safe_ident(attr, "_cv")
            if vtype in _CLASS_NAMES[0]:
                # Check if attr is a @property on the resolved type (local class)
                props = _CLASS_PROPERTIES[0].get(vtype, set())
                if attr in props:
                    return "(& (Get-Command (\"" + "{0}_{1}" + '" -f ' + value + '["__type__"], "' + attr + '")) ' + value + ")"
                # For imported classes, use __pytra_getattr (handles property fallback)
                if vtype not in _CLASS_PROPERTIES[0]:
                    return "(__pytra_getattr " + value + ' "' + attr + '")'
                return value + '["' + attr + '"]'
            # sys module property: sys.argv, sys.maxsize etc
            if vname == "sys":
                if attr == "argv":
                    return "$argv"
                if attr == "path":
                    return "$path"
                if attr == "maxsize":
                    return "[int64]::MaxValue"
                if attr == "platform":
                    return '"powershell"'
                if attr in ("stderr", "stdout"):
                    return "$" + attr
            # Module attribute: mod.X → $X (module scope variable/function)
            if vname in _MODULE_ALIAS_MAP[0]:
                return "$" + _safe_ident(attr, "_f")
        # Hashtable-based object field access: prefer ["attr"] over .attr
        # .NET methods (ToUpper, Split etc.) use dot notation
        _DOTNET_PROPS = {
            "Length", "Count", "Keys", "Values",
            "Name", "FullName", "Extension", "Directory",
        }
        if safe_attr in _DOTNET_PROPS or safe_attr[0].isupper():
            return value + "." + safe_attr
        # Use __pytra_getattr for property-aware access on unknown-typed objects
        if isinstance(value_node, dict):
            vtype2 = _get_str(value_node, "resolved_type")
            if vtype2 not in _CLASS_NAMES[0] and vtype2 not in ("str", "int", "int64", "float", "float64", "bool"):
                return "(__pytra_getattr " + value + ' "' + attr + '")'
        return value + '["' + attr + '"]'

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

    if kind == "Set":
        elements = _get_list(expr, "elements")
        if len(elements) == 0:
            elements = _get_list(expr, "elts")
        if len(elements) == 0:
            return "@{}"
        parts = [_render_expr(e) + " = $true" for e in elements]
        return "@{" + "; ".join(parts) + "}"

    if kind == "ListComp":
        elt = expr.get("elt")
        generators = _get_list(expr, "generators")
        if len(generators) == 0:
            return "@()"

        def _build_listcomp_pipe(gens: list[Any], elt_node: Any, depth: int) -> str:
            if depth >= len(gens):
                rendered_elt = _render_expr(elt_node)
                if isinstance(elt_node, dict) and _get_str(elt_node, "kind") in ("ListComp", "List", "Tuple"):
                    rendered_elt = "," + rendered_elt
                return rendered_elt
            gen_item = gens[depth]
            if not isinstance(gen_item, dict):
                return _render_expr(elt_node)
            gen_target = gen_item.get("target")
            gen_iter = gen_item.get("iter")
            gen_ifs = _get_list(gen_item, "ifs")
            tname = "$" + _safe_ident(_get_str(gen_target, "id") if isinstance(gen_target, dict) else "_lc" + str(depth), "_lc")
            irendered = _render_expr(gen_iter)
            inner = _build_listcomp_pipe(gens, elt_node, depth + 1)
            if len(gen_ifs) > 0:
                cond_parts = " -and ".join(["(" + _render_expr(c) + ")" for c in gen_ifs])
                return "@(" + irendered + " | ForEach-Object { " + tname + " = $_; if (" + cond_parts + ") { " + inner + " } })"
            return "@(" + irendered + " | ForEach-Object { " + tname + " = $_; " + inner + " })"

        return _build_listcomp_pipe(generators, elt, 0)

    if kind == "DictComp":
        key_expr = expr.get("key")
        value_expr = expr.get("value")
        generators = _get_list(expr, "generators")
        if len(generators) == 0 or key_expr is None or value_expr is None:
            return "@{}"
        gen = generators[0]
        if not isinstance(gen, dict):
            return "@{}"
        gen_target = gen.get("target")
        gen_iter = gen.get("iter")
        gen_ifs = _get_list(gen, "ifs")
        tname = "$" + _safe_ident(_get_str(gen_target, "id") if isinstance(gen_target, dict) else "_dc", "_dc")
        irendered = _render_expr(gen_iter)
        k_rendered = _render_expr(key_expr)
        v_rendered = _render_expr(value_expr)
        body = "$__dc_result[" + k_rendered + "] = " + v_rendered
        if len(gen_ifs) > 0:
            cond = " -and ".join(["(" + _render_expr(c) + ")" for c in gen_ifs])
            body = "if (" + cond + ") { " + body + " }"
        return "& { $__dc_result = @{}; foreach (" + tname + " in " + irendered + ") { " + body + " }; $__dc_result }"

    if kind == "SetComp":
        elt = expr.get("elt")
        generators = _get_list(expr, "generators")
        if len(generators) == 0 or elt is None:
            return "@{}"
        gen = generators[0]
        if not isinstance(gen, dict):
            return "@{}"
        gen_target = gen.get("target")
        gen_iter = gen.get("iter")
        gen_ifs = _get_list(gen, "ifs")
        tname = "$" + _safe_ident(_get_str(gen_target, "id") if isinstance(gen_target, dict) else "_sc", "_sc")
        irendered = _render_expr(gen_iter)
        e_rendered = _render_expr(elt)
        body = "$__sc_result[" + e_rendered + "] = $true"
        if len(gen_ifs) > 0:
            cond = " -and ".join(["(" + _render_expr(c) + ")" for c in gen_ifs])
            body = "if (" + cond + ") { " + body + " }"
        return "& { $__sc_result = @{}; foreach (" + tname + " in " + irendered + ") { " + body + " }; $__sc_result }"

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
        value_node = expr.get("value")
        value = _render_expr(value_node)
        slice_any = expr.get("slice")
        if isinstance(slice_any, dict) and _get_str(slice_any, "kind") == "Slice":
            slice_d: dict[str, object] = slice_any
            lower = _render_expr(slice_d.get("lower")) if slice_d.get("lower") is not None else "0"
            upper = _render_expr(slice_d.get("upper")) if slice_d.get("upper") is not None else (value + ".Length")
            return "(__pytra_str_slice " + value + " " + lower + " " + upper + ")"
        index = _render_expr(slice_any)
        # str[i] returns [char] in PS — cast to [string] for consistency
        val_type = _get_str(value_node, "resolved_type") if isinstance(value_node, dict) else ""
        if val_type == "str":
            return "[string]" + value + "[" + index + "]"
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
                conversion = _get_str(part_d, "conversion")
                format_spec = _get_str(part_d, "format_spec")
                if conversion != "" and conversion != "-1":
                    segments.append("$(py_format_conversion " + inner + " " + _ps_string_literal(conversion) + ")")
                elif format_spec != "":
                    segments.append("$(py_format_value " + inner + " " + _ps_string_literal(format_spec) + ")")
                else:
                    segments.append("$(" + inner + ")")
            else:
                segments.append("$(" + _render_expr(part_d) + ")")
        return '"' + "".join(segments) + '"'

    if kind == "IsInstance":
        value_node = expr.get("value")
        expected_type_node = expr.get("expected_type_id")
        if isinstance(expected_type_node, dict):
            type_name = _get_str(expected_type_node, "id")
            if type_name != "":
                obj_expr = _render_expr(value_node)
                return "(__pytra_isinstance " + obj_expr + ' "' + type_name + '")'
        return "$true"

    if kind == "Cast":
        # 動的言語では cast は no-op: 値をそのまま返す
        return _render_expr(expr.get("value"))

    if kind == "ObjLen":
        return "(__pytra_len " + _render_expr(expr.get("value")) + ")"

    if kind == "ObjStr":
        return "(__pytra_str " + _render_expr(expr.get("value")) + ")"

    if kind == "ObjBool":
        return "(__pytra_bool " + _render_expr(expr.get("value")) + ")"

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
    # Append keyword arguments as positional (PS uses param() names)
    keywords = _get_list(expr, "keywords")
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            if kw_val is not None:
                rendered_args.append(_render_expr(kw_val))

    if isinstance(func, dict):
        func_d: dict[str, object] = func
        fk = _get_str(func_d, "kind")

        if fk == "Name":
            fn_name = _RENAMED_SYMBOLS[0].get(_get_str(func_d, "id"), _get_str(func_d, "id"))
            # py_assert_stdout: last arg is a function name → pass as string
            if fn_name == "py_assert_stdout" and len(args) >= 2:
                last_arg = args[-1]
                if isinstance(last_arg, dict) and _get_str(last_arg, "kind") == "Name":
                    fn_ref_name = _safe_ident(_get_str(last_arg, "id"), "_fn")
                    other_args = rendered_args[:-1]
                    return "(py_assert_stdout " + " ".join(other_args) + ' "' + fn_ref_name + '")'
            if fn_name == "print":
                return "__pytra_print " + " ".join(rendered_args) if len(rendered_args) > 0 else "__pytra_print"
            if fn_name == "len":
                return "(__pytra_len " + rendered_args[0] + ")" if len(rendered_args) > 0 else "(__pytra_len)"
            if fn_name == "str":
                return "(__pytra_str " + rendered_args[0] + ")" if len(rendered_args) > 0 else "(__pytra_str)"
            if fn_name == "int":
                return "(__pytra_int " + rendered_args[0] + ")" if len(rendered_args) > 0 else "(__pytra_int)"
            if fn_name == "float":
                return "(__pytra_float " + rendered_args[0] + ")" if len(rendered_args) > 0 else "(__pytra_float)"
            if fn_name == "bool":
                return "(__pytra_bool " + rendered_args[0] + ")" if len(rendered_args) > 0 else "(__pytra_bool)"
            if fn_name == "range":
                return "(__pytra_range " + " ".join(rendered_args) + ")"
            if fn_name == "ord":
                return "(__pytra_ord " + rendered_args[0] + ")" if len(rendered_args) > 0 else "(__pytra_ord)"
            if fn_name == "chr":
                return "(__pytra_chr " + rendered_args[0] + ")" if len(rendered_args) > 0 else "(__pytra_chr)"
            if fn_name == "abs":
                return "[Math]::Abs(" + rendered_args[0] + ")" if len(rendered_args) > 0 else "[Math]::Abs(0)"
            if fn_name == "min":
                return "[Math]::Min(" + ", ".join(rendered_args) + ")" if len(rendered_args) > 0 else "0"
            if fn_name == "max":
                return "[Math]::Max(" + ", ".join(rendered_args) + ")" if len(rendered_args) > 0 else "0"
            if fn_name == "isinstance":
                return "$true"
            if fn_name == "cast":
                # typing.cast(Type, value) → value (no-op in dynamic languages)
                if len(rendered_args) >= 2:
                    return rendered_args[1]
                return "$null"
            if fn_name == "extern":
                # @extern decorator / extern(value) → value (no-op)
                if len(rendered_args) >= 1:
                    return rendered_args[0]
                return "$null"
            # Imported function aliases (e.g. from math import sqrt -> [Math]::Sqrt)
            if fn_name in _IMPORT_ALIASES[0]:
                ps_func = _IMPORT_ALIASES[0][fn_name]
                if ps_func.startswith("[Math]::"):
                    if ps_func.endswith("PI") or ps_func.endswith("::E"):
                        return "(" + ps_func + ")"
                    return "(" + ps_func + "(" + ", ".join(rendered_args) + "))"
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
                return "(__pytra_reversed " + rendered_args[0] + ")" if len(rendered_args) > 0 else "@()"
            if fn_name == "enumerate":
                return rendered_args[0] if len(rendered_args) > 0 else "@()"
            if fn_name == "zip":
                if len(rendered_args) >= 2:
                    return "(__pytra_zip " + rendered_args[0] + " " + rendered_args[1] + ")"
                return "@()"
            if fn_name == "map":
                if len(rendered_args) >= 2:
                    return "(__pytra_map " + rendered_args[0] + " " + rendered_args[1] + ")"
                return "@()"
            if fn_name == "filter":
                if len(rendered_args) >= 2:
                    return "(__pytra_filter " + rendered_args[0] + " " + rendered_args[1] + ")"
                return "@()"
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
                # 括弧で囲む: -f 演算子の右辺等で & { } が裸だと ParserError になる
                if len(rendered_args) == 0:
                    return "(& { $__obj = @{}; (" + safe + " $__obj); $__obj })"
                return "(& { $__obj = @{}; (" + safe + " $__obj " + " ".join(rendered_args) + "); $__obj })"
            if len(rendered_args) == 0:
                return "(" + safe + ")"
            return "(" + safe + " " + " ".join(rendered_args) + ")"

        if fk == "Attribute":
            owner_node = func_d.get("value")
            owner = _render_expr(owner_node)
            attr = _safe_ident(_get_str(func_d, "attr"), "method")
            # math module: $math.sqrt(...) -> [Math]::Sqrt(...)
            owner_name = ""
            owner_type = ""
            if isinstance(owner_node, dict):
                if _get_str(owner_node, "kind") == "Name":
                    owner_name = _get_str(owner_node, "id")
                owner_type = _get_str(owner_node, "resolved_type")
            # Resolve import alias: path → pytra.std.os_path → direct function call
            if owner_name in _MODULE_ALIAS_MAP[0]:
                safe_fn = _safe_ident(_get_str(func_d, "attr"), "_f")
                if len(rendered_args) == 0:
                    return "(" + safe_fn + ")"
                return "(" + safe_fn + " " + " ".join(rendered_args) + ")"
            # In method body, ClassName.method() means self.method()
            if owner_name in _CLASS_NAMES[0]:
                owner = "$self"
            # super().__init__() -> ParentClass $self args
            if isinstance(owner_node, dict) and _get_str(owner_node, "kind") == "Call":
                super_func = owner_node.get("func")
                if isinstance(super_func, dict) and _get_str(super_func, "id") == "super":
                    raw_attr = _get_str(func_d, "attr")
                    # Find the direct parent of the current class
                    cur_cls = _CURRENT_CLASS_NAME[0]
                    parent_cls = _CLASS_BASES[0].get(cur_cls, "")
                    if parent_cls == "":
                        # Fallback: first base found
                        for cls_name, base_name in _CLASS_BASES[0].items():
                            if base_name != "":
                                parent_cls = base_name
                                break
                    if parent_cls != "":
                        parent_fn = _safe_ident(parent_cls, "_Base")
                        if raw_attr == "__init__":
                            if len(rendered_args) == 0:
                                return "(" + parent_fn + " $self)"
                            return "(" + parent_fn + " $self " + " ".join(rendered_args) + ")"
                        else:
                            method_fn = parent_fn + "_" + _safe_ident(raw_attr, "_m")
                            if len(rendered_args) == 0:
                                return "(" + method_fn + " $self)"
                            return "(" + method_fn + " $self " + " ".join(rendered_args) + ")"
            # Module method call: mod.func() → (func args)
            # Detected via _MODULE_ALIAS_MAP (built from import_bindings)
            if owner_name in _MODULE_ALIAS_MAP[0]:
                safe_fn = _safe_ident(attr, "_f")
                if len(rendered_args) == 0:
                    return "(" + safe_fn + ")"
                return "(" + safe_fn + " " + " ".join(rendered_args) + ")"
            # os.path.X() → (X args)
            if owner_name == "os_path" or (isinstance(owner_node, dict) and _get_str(owner_node, "kind") == "Attribute" and _get_str(owner_node, "attr") == "path"):
                safe_fn = _safe_ident(attr, "_f")
                if len(rendered_args) == 0:
                    return "(" + safe_fn + ")"
                return "(" + safe_fn + " " + " ".join(rendered_args) + ")"
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
                return "([char]::IsDigit([string]" + owner + ", 0))"
            if attr == "isalpha":
                return "([char]::IsLetter([string]" + owner + ", 0))"
            if attr == "isspace":
                return "([char]::IsWhiteSpace([string]" + owner + ", 0))"
            if attr == "isupper":
                return "([char]::IsUpper([string]" + owner + ", 0))"
            if attr == "islower":
                return "([char]::IsLower([string]" + owner + ", 0))"
            if attr == "isalnum":
                return "([char]::IsLetterOrDigit([string]" + owner + ", 0))"
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
                    return "(__pytra_list_pop " + owner + ")"
                return owner
            if attr == "write":
                # File write: use __pytra_file_write for bytes/string compatibility
                if len(rendered_args) > 0:
                    return "(__pytra_file_write " + owner + " " + rendered_args[0] + ")"
                return owner
            if attr == "read":
                return owner + ".ReadToEnd()"
            if attr == "close":
                return owner + ".Close()"
            if attr == "flush":
                return owner + ".Flush()"
            if attr == "index":
                if len(rendered_args) > 0:
                    return "[array]::IndexOf(" + owner + ", " + rendered_args[0] + ")"
                return "-1"
            if attr == "extend":
                if len(rendered_args) > 0:
                    return owner + " += @(" + rendered_args[0] + ")"
                return owner
            if attr == "insert":
                if len(rendered_args) >= 2:
                    return "(" + owner + " = @(" + owner + "[0..([Math]::Max(0, " + rendered_args[0] + " - 1))] + @(" + rendered_args[1] + ") + " + owner + "[" + rendered_args[0] + "..(" + owner + ".Length - 1)]))"
                return owner
            if attr == "discard":
                if len(rendered_args) > 0:
                    return owner + ".Remove(" + rendered_args[0] + ")"
                return owner
            if attr == "add":
                raw_owner_type = owner_type.lower() if isinstance(owner_type, str) else ""
                if raw_owner_type.startswith("set[") or raw_owner_type == "set":
                    if len(rendered_args) > 0:
                        return owner + "[" + rendered_args[0] + "] = $true"
                    return owner
                if len(rendered_args) > 0:
                    return owner + " += @(" + rendered_args[0] + ")"
                return owner
            if attr == "remove":
                raw_owner_type2 = owner_type.lower() if isinstance(owner_type, str) else ""
                if raw_owner_type2.startswith("set[") or raw_owner_type2 == "set":
                    if len(rendered_args) > 0:
                        return owner + ".Remove(" + rendered_args[0] + ")"
                    return owner
                if len(rendered_args) > 0:
                    return "(__pytra_list_remove " + owner + " " + rendered_args[0] + ")"
                return owner
            if attr == "copy":
                return "@(" + owner + ")"
            if attr == "update":
                if len(rendered_args) > 0:
                    return "foreach ($__k in " + rendered_args[0] + ".Keys) { " + owner + "[$__k] = " + rendered_args[0] + "[$__k] }"
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
            ) and (
                owner_name == "self" or owner_name in _CLASS_NAMES[0] or owner_type in _CLASS_NAMES[0]
                or (owner_name != "" and owner_name not in (
                    "math", "os", "sys", "json", "re", "random", "pathlib", "time",
                    "collections", "itertools", "functools", "io", "struct",
                ))
            ):
                # Dynamic dispatch: ClassName_method $self args
                if len(rendered_args) == 0:
                    return '(& (Get-Command ("{0}_{1}" -f ' + owner + '["__type__"], "' + raw_attr + '")) ' + owner + ')'
                return '(& (Get-Command ("{0}_{1}" -f ' + owner + '["__type__"], "' + raw_attr + '")) ' + owner + ' ' + " ".join(rendered_args) + ')'
            if len(rendered_args) == 0:
                return owner + "." + attr + "()"
            return owner + "." + attr + "(" + ", ".join(rendered_args) + ")"

    # Lambda immediate call: { param($x) expr } arg -> & { param($x) expr } arg
    if isinstance(func, dict) and _get_str(func, "kind") == "Lambda":
        fn_rendered = _render_expr(func)
        if len(rendered_args) == 0:
            return "(& " + fn_rendered + ")"
        return "(& " + fn_rendered + " " + " ".join(rendered_args) + ")"

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
            # Module-level docstring: 文字列リテラルをコメントに変換
            if vk == "Constant":
                cv = value_d.get("value")
                if isinstance(cv, str):
                    # docstring → コメント化（stdout に漏れるのを防ぐ）
                    first_line = cv.split("\n")[0][:80]
                    return [indent + "# " + first_line]
            if vk == "Name":
                raw = _get_str(value_d, "id")
                if raw == "break":
                    return [indent + "break"]
                if raw == "continue":
                    return [indent + "continue"]
                if raw == "pass":
                    return [indent + "# pass"]
        rendered = _render_expr(value)
        # discard_result flag: EAST3 marks Expr(Call) where return value is unused
        # Exclude print/__pytra_print — their output is intentional
        if stmt.get("discard_result"):
            is_print_call = False
            if isinstance(value, dict) and _get_str(value, "kind") == "Call":
                fn_node = value.get("func")
                if isinstance(fn_node, dict) and _get_str(fn_node, "id") in ("print", "__pytra_print"):
                    is_print_call = True
            if not is_print_call:
                return [indent + "[void](" + rendered + ")"]
        # Fallback: suppress known side-effect-only calls
        if isinstance(value, dict) and _get_str(value, "kind") == "Call":
            func_node = value.get("func")
            if isinstance(func_node, dict):
                fn = _get_str(func_node, "id")
                if fn.startswith("py_assert_"):
                    return [indent + "[void](" + rendered + ")"]
        return [indent + rendered]

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
        # Skip extern(...) variable assignments (native seam provides these)
        val_node = stmt.get("value")
        if _is_extern_value(val_node):
            tname = ""
            if len(targets) == 1 and isinstance(targets[0], dict):
                tname = _get_str(targets[0], "id")
            return [indent + "# extern var: " + tname + " (provided by native seam)"]
        # Track lambda assignments
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
                return [indent + _render_lvalue(target_d) + " = " + value]
            if _get_str(target_d, "kind") == "Subscript":
                owner = _render_expr(target_d.get("value"))
                index = _render_expr(target_d.get("slice"))
                return [indent + owner + "[" + index + "] = " + value]
        lhs = _render_lvalue(target)
        return [indent + lhs + " = " + value]

    if kind == "AnnAssign":
        target = stmt.get("target")
        value = stmt.get("value")
        if value is None:
            lhs = _render_expr(target)
            return [indent + lhs + " = $null"]
        # Skip extern(...) variable assignments (native seam provides these)
        if _is_extern_value(value):
            tname = _get_str(target, "id") if isinstance(target, dict) else ""
            return [indent + "# extern var: " + tname + " (provided by native seam)"]
        # Track lambda assignments
        if isinstance(value, dict) and _get_str(value, "kind") == "Lambda":
            if isinstance(target, dict) and _get_str(target, "kind") == "Name":
                _LAMBDA_VARS[0].add(_get_str(target, "id"))
        lhs = _render_expr(target)
        return [indent + lhs + " = " + _render_expr(value)]

    if kind == "AugAssign":
        target = _render_lvalue(stmt.get("target"))
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

        # RuntimeIterForPlan: foreach ($item in collection) { ... }
        if isinstance(iter_plan, dict) and _get_str(iter_plan, "kind") == "RuntimeIterForPlan":
            iter_expr = iter_plan.get("iter_expr")
            iter_rendered = _render_expr(iter_expr)
            # String iteration: foreach ($c in $s) doesn't split chars in PS
            if isinstance(iter_expr, dict) and _get_str(iter_expr, "resolved_type") == "str":
                iter_rendered = iter_rendered + ".ToCharArray()"
            # Set iteration: foreach ($k in $set) iterates keys, not the hashtable itself
            if isinstance(iter_expr, dict):
                rt = _get_str(iter_expr, "resolved_type")
                if rt.startswith("set[") or rt == "set":
                    iter_rendered = iter_rendered + ".Keys"
            # Simple foreach with single target (enumerate/TupleTarget already lowered by EAST3)
                loop_var = "$_item"
                if isinstance(target_plan, dict):
                    tp_name = _get_str(target_plan, "id")
                    if tp_name != "":
                        loop_var = "$" + _safe_ident(tp_name, "_item")
                lines = [indent + "foreach (" + loop_var + " in " + iter_rendered + ") {"]
                lines.extend(_emit_body(body, indent=indent + "    ", ctx=ctx))
                lines.append(indent + "}")
                return lines

        # Extract loop variable from target_plan
        loop_var = "$_i"
        if isinstance(target_plan, dict):
            tp_d: dict[str, object] = target_plan
            tp_id = _get_str(tp_d, "id")
            if tp_id != "":
                loop_var = "$" + _safe_ident(tp_id, "_i")

        # Try StaticRangeForPlan first (more reliable than normalized_exprs)
        if isinstance(iter_plan, dict) and _get_str(iter_plan, "kind") == "StaticRangeForPlan":
            ip_d: dict[str, object] = iter_plan
            start = _render_expr(ip_d.get("start"))
            stop = _render_expr(ip_d.get("stop"))
            step = ip_d.get("step")
            step_val = 1
            if isinstance(step, dict):
                sk = _get_str(step, "kind")
                if sk == "Constant" and step.get("value") is not None:
                    sv = step.get("value")
                    step_val = sv if isinstance(sv, int) else 1
                elif sk == "UnaryOp" and _get_str(step, "op") == "USub":
                    operand = step.get("operand")
                    if isinstance(operand, dict) and operand.get("value") is not None:
                        ov = operand.get("value")
                        step_val = -(ov if isinstance(ov, int) else 1)
            if step_val >= 0:
                lines = [indent + "for (" + loop_var + " = " + start + "; " + loop_var + " -lt " + stop + "; " + loop_var + " += " + str(step_val) + ") {"]
            else:
                lines = [indent + "for (" + loop_var + " = " + start + "; " + loop_var + " -gt " + stop + "; " + loop_var + " += " + str(step_val) + ") {"]
        else:
            # Fallback: try normalized_exprs (for_init_expr, for_cond_expr, for_update_expr)
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
                    update_str = loop_var + " += 1"
                lines = [indent + "for (" + init_str + "; " + cond_str + "; " + update_str + ") {"]
            else:
                lines = [indent + "for (" + loop_var + " = 0; $true; " + loop_var + " += 1) {"]

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
            # raise ExceptionType("msg") → throw "ExceptionType: msg"
            if isinstance(exc, dict) and _get_str(exc, "kind") == "Call":
                exc_func = exc.get("func")
                exc_args = _get_list(exc, "args")
                if isinstance(exc_func, dict) and _get_str(exc_func, "kind") == "Name":
                    exc_name = _get_str(exc_func, "id")
                    if len(exc_args) > 0:
                        return [indent + "throw " + _ps_string_literal(exc_name + ": " + "") + " + " + _render_expr(exc_args[0])]
                    return [indent + "throw " + _ps_string_literal(exc_name)]
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
        module = _get_str(stmt, "module")
        # typing / dataclasses は no-op
        if module in ("typing", "pytra.typing", "dataclasses", "__future__"):
            return [indent + "# import: " + module]
        # math の from-import は _IMPORT_ALIASES で処理済み
        if module in ("math", "pytra.std.math"):
            if module in _IMPORT_ALIASES[0] or any(
                _get_str(e, "name") in _IMPORT_ALIASES[0]
                for e in _get_list(stmt, "names") if isinstance(e, dict)
            ):
                return [indent + "# import: " + module + " (aliased)"]
        ps_path = _module_to_ps_path(module)
        if ps_path != "":
            return [indent + '. (Join-Path $PSScriptRoot "' + ps_path + '")']
        # from pytra.std import os, glob → dot-source each sub-module
        if module in ("pytra.std", "pytra.utils"):
            sub_lines: list[str] = []
            for entry in _get_list(stmt, "names"):
                if not isinstance(entry, dict):
                    continue
                sub_name = _get_str(entry, "name")
                sub_path = _module_to_ps_path(module + "." + sub_name)
                if sub_path != "":
                    sub_lines.append(indent + '. (Join-Path $PSScriptRoot "' + sub_path + '")')
            if len(sub_lines) > 0:
                return sub_lines
        return [indent + "# import: " + module]

    if kind == "Import":
        names = _get_list(stmt, "names")
        lines: list[str] = []
        for entry in names:
            if not isinstance(entry, dict):
                continue
            mod_name = _get_str(entry, "name")
            ps_path = _module_to_ps_path(mod_name)
            if ps_path != "":
                lines.append(indent + '. (Join-Path $PSScriptRoot "' + ps_path + '")')
            else:
                lines.append(indent + "# import: " + mod_name)
        return lines if len(lines) > 0 else [indent + "# import"]

    return [indent + "# unsupported: " + kind]


def _is_stdlib_passthrough_function(stmt: dict[str, Any]) -> bool:
    """Return True if this function is a stdlib passthrough (extern wrapper).

    Only applies to module-level functions, not class methods.

    Pattern: function body is a single return statement that calls
    $stdlib_module.same_name(args), e.g. return time.perf_counter().
    These should be skipped since py_runtime.ps1 already provides the implementation.
    """
    # Don't skip class methods — they are ClassName_method, not module-level
    if _CURRENT_CLASS_NAME[0] != "":
        return False
    body = _get_list(stmt, "body")
    if len(body) != 1:
        return False
    s = body[0]
    if not isinstance(s, dict) or _get_str(s, "kind") != "Return":
        return False
    val = s.get("value")
    if not isinstance(val, dict) or _get_str(val, "kind") != "Call":
        return False
    func = val.get("func")
    if not isinstance(func, dict) or _get_str(func, "kind") != "Attribute":
        return False
    owner = func.get("value")
    if not isinstance(owner, dict):
        return False
    func_attr = _get_str(func, "attr")
    fn_name = _get_str(stmt, "name")
    # 1-level: time.perf_counter, math.sqrt, os.getcwd etc.
    if _get_str(owner, "kind") == "Name":
        owner_name = _get_str(owner, "id")
        if owner_name in _MODULE_ALIAS_MAP[0] and func_attr == fn_name:
            return True
    # 2-level: os.path.join etc. — Attribute chain
    if _get_str(owner, "kind") == "Attribute":
        inner_owner = owner.get("value")
        if isinstance(inner_owner, dict) and _get_str(inner_owner, "kind") == "Name":
            inner_name = _get_str(inner_owner, "id")
            if inner_name in _MODULE_ALIAS_MAP[0] and func_attr == fn_name:
                    return True
    return False


def _emit_function_def(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    name = _safe_ident(_get_str(stmt, "name"), "_fn")
    # @extern: skip — native seam is dot-sourced and provides the function directly
    decs = _get_list(stmt, "decorators")
    if "extern" in decs and _CURRENT_CLASS_NAME[0] == "":
        return [indent + "# @extern " + name + " — provided by native seam"]
    # Skip stdlib passthrough functions (runtime already provides them)
    if _is_stdlib_passthrough_function(stmt):
        return [indent + "# passthrough: " + name]
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
    prev_class = _CURRENT_CLASS_NAME[0]
    _CURRENT_CLASS_NAME[0] = name
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
                type_assign = indent + '    $self["__type__"] = "' + name + '"'
                # Insert __type__ at start (after param) for self.method() in __init__
                for i_fn in range(len(fn_lines)):
                    if "param(" in fn_lines[i_fn]:
                        fn_lines.insert(i_fn + 1, type_assign)
                        break
                # Also insert at end (before }) to override super().__init__ setting
                for i_fn in range(len(fn_lines) - 1, -1, -1):
                    if fn_lines[i_fn].strip() == "}":
                        fn_lines.insert(i_fn, type_assign)
                        break
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
        # @dataclass: field_types からコンストラクタ引数を生成
        field_types = _get_dict(stmt, "field_types")
        field_defaults = _get_dict(stmt, "field_defaults")
        field_params: list[str] = ["$self"]
        field_assigns: list[str] = []
        # body 内の AnnAssign/Assign からフィールド名と順序を取得
        field_names: list[str] = []
        for member in body:
            if not isinstance(member, dict):
                continue
            mk2 = _get_str(member, "kind")
            if mk2 == "AnnAssign" or mk2 == "Assign":
                tgt = member.get("target")
                if isinstance(tgt, dict) and _get_str(tgt, "kind") == "Name":
                    fn_id = _get_str(tgt, "id")
                    if fn_id != "":
                        field_names.append(fn_id)
        if len(field_names) == 0 and len(field_types) > 0:
            for ft_name in field_types:
                if isinstance(ft_name, str):
                    field_names.append(ft_name)
        for fn_id in field_names:
            safe_fn = "$" + _safe_ident(fn_id, "_f")
            default_val = field_defaults.get(fn_id)
            if default_val is not None:
                field_params.append(safe_fn + " = " + _render_expr(default_val))
            else:
                # AnnAssign の value をデフォルトとして使う
                for member in body:
                    if isinstance(member, dict) and _get_str(member, "kind") in ("AnnAssign", "Assign"):
                        tgt2 = member.get("target")
                        if isinstance(tgt2, dict) and _get_str(tgt2, "id") == fn_id:
                            val = member.get("value")
                            if val is not None:
                                field_params.append(safe_fn + " = " + _render_expr(val))
                            else:
                                field_params.append(safe_fn)
                            break
                    else:
                        continue
                else:
                    field_params.append(safe_fn)
            field_assigns.append(indent + '    $self["' + fn_id + '"] = ' + safe_fn)
        lines.append(indent + "function " + name + " {")
        lines.append(indent + "    param(" + ", ".join(field_params) + ")")
        for fa in field_assigns:
            lines.append(fa)
        lines.append(indent + '    $self["__type__"] = "' + name + '"')
        lines.append(indent + "}")
    # else: __type__ already injected in fn_lines above

    # Generate inherited method aliases: ChildClass_method -> BaseClass_method
    base = _get_str(stmt, "base")
    if base != "":
        # Collect methods defined in this class
        own_methods: set[str] = set()
        for member in body:
            if isinstance(member, dict) and _get_str(member, "kind") == "FunctionDef":
                mn = _get_str(member, "name")
                if mn != "" and mn != "__init__":
                    own_methods.add(mn)
        # Collect methods from base class (walk all ClassDefs in module body)
        base_methods: set[str] = set()
        for node in _get_list(_get_dict(stmt, "_module_body_ref") if "_module_body_ref" in stmt else {}, "body"):
            pass  # Can't access module body from here
        # Fallback: collect from _CLASS_METHOD_NAMES
        for bm in _CLASS_METHOD_NAMES[0].get(base, set()):
            if bm not in own_methods:
                base_fn = _safe_ident(base, "_Base") + "_" + _safe_ident(bm, "_m")
                child_fn = name + "_" + _safe_ident(bm, "_m")
                lines.append(indent + "function " + child_fn + " { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$__args) " + base_fn + " @__args }")

    _CURRENT_CLASS_NAME[0] = prev_class
    return lines


def _simplify_main_guard_stmt(stmt: dict[str, Any]) -> dict[str, Any]:
    """main_guard_body をそのまま返す（simplify は行わない）。

    以前は py_assert_stdout ラッパーを剥がして直接関数呼び出しに変換していたが、
    それだと Python の出力と一致しない。runtime 側で py_assert_stdout を正しく
    実装し、EAST3 のノードをそのまま emit する方式に変更。
    """
    return stmt


# ---------------------------------------------------------------------------
# Module-level entry point
# ---------------------------------------------------------------------------

_CURRENT_MODULE_ID: list[str] = [""]
_ROOT_REL_PREFIX: list[str] = [""]


def transpile_to_powershell(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを PowerShell コードへ変換する。"""
    if not isinstance(east_doc, dict) or _get_str(east_doc, "kind") != "Module":
        raise RuntimeError("powershell native emitter: root kind must be Module")

    body = _get_list(east_doc, "body")
    if not isinstance(body, list):
        raise RuntimeError("powershell native emitter: Module.body must be list")

    # Track current module ID and root-relative prefix for path resolution
    meta = _get_dict(east_doc, "meta")
    _CURRENT_MODULE_ID[0] = _get_str(meta, "module_id")
    emit_ctx = _get_dict(meta, "emit_context")
    _ROOT_REL_PREFIX[0] = _get_str(emit_ctx, "root_rel_prefix")
    _MODULE_ALIAS_MAP[0] = build_import_alias_map(meta)

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
    # Also collect imported class names from import_bindings
    # Convention: class names start with uppercase
    meta = _get_dict(east_doc, "meta")
    for binding in _get_list(meta, "import_bindings"):
        if isinstance(binding, dict):
            local = _get_str(binding, "local_name")
            if local != "" and local[0].isupper() and local not in (
                "Any", "Optional", "Union", "List", "Dict", "Tuple", "Set",
                "Callable", "Iterator", "Iterable", "Enum", "IntEnum", "IntFlag",
            ):
                class_names.add(local)
    _CLASS_NAMES[0] = class_names
    class_bases: dict[str, str] = {}
    for node in body:
        if isinstance(node, dict) and _get_str(node, "kind") == "ClassDef":
            cn = _get_str(node, "name")
            base = _get_str(node, "base")
            if cn != "" and base != "":
                class_bases[cn] = base
    _CLASS_BASES[0] = class_bases
    class_method_names: dict[str, set[str]] = {}
    for node in body:
        if isinstance(node, dict) and _get_str(node, "kind") == "ClassDef":
            cn = _get_str(node, "name")
            methods: set[str] = set()
            for member in _get_list(node, "body"):
                if isinstance(member, dict) and _get_str(member, "kind") == "FunctionDef":
                    mn = _get_str(member, "name")
                    if mn != "" and mn != "__init__":
                        methods.add(mn)
            class_method_names[cn] = methods
    _CLASS_METHOD_NAMES[0] = class_method_names

    # Collect property names from decorators=['property']
    class_properties: dict[str, set[str]] = {}
    for node in body:
        if isinstance(node, dict) and _get_str(node, "kind") == "ClassDef":
            cn = _get_str(node, "name")
            props: set[str] = set()
            for member in _get_list(node, "body"):
                if isinstance(member, dict) and _get_str(member, "kind") == "FunctionDef":
                    decs = _get_list(member, "decorators")
                    if "property" in decs:
                        mn = _get_str(member, "name")
                        if mn != "":
                            props.add(mn)
            if len(props) > 0:
                class_properties[cn] = props
    _CLASS_PROPERTIES[0] = class_properties

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
    rp = _ROOT_REL_PREFIX[0]
    lines: list[str] = [
        "#Requires -Version 5.1",
        "",
        "$pytra_runtime = Join-Path $PSScriptRoot \"" + rp + "built_in/py_runtime.ps1\"",
        "if (Test-Path $pytra_runtime) { . $pytra_runtime }",
        "",
        "Set-StrictMode -Version Latest",
        "$ErrorActionPreference = \"Stop\"",
        "",
    ]

    # Dot-source native seam for stdlib modules (spec-runtime.md §0.6a)
    # module_id "pytra.std.time" → native seam "std/time_native.ps1"
    cur_mod = _CURRENT_MODULE_ID[0]
    if cur_mod.startswith("pytra.std.") or cur_mod.startswith("pytra.built_in."):
        # Strip pytra. prefix and add _native suffix
        mod_tail = cur_mod[len("pytra."):]  # e.g. "std.time"
        native_path = mod_tail.replace(".", "/") + "_native.ps1"  # e.g. "std/time_native.ps1"
        lines.append('. (Join-Path $PSScriptRoot "' + rp + native_path + '")')
        lines.append("")

    # Detect implicit format_value dependency (f-string format_spec)
    if _has_format_spec_in_doc(east_doc):
        lines.append('. (Join-Path $PSScriptRoot "' + rp + 'format_value/east.ps1")')
        lines.append("")

    # Emit __pytra_bases table for isinstance inheritance chain lookup
    if len(class_bases) > 0:
        parts = ['"' + child + '" = "' + base + '"' for child, base in class_bases.items()]
        lines.append("$__pytra_bases = @{" + "; ".join(parts) + "}")
        lines.append("")

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
                # Strip discard_result in main_guard_body:
                # [void] suppresses Write-Output inside called functions
                if isinstance(simplified, dict) and simplified.get("discard_result"):
                    simplified = dict(simplified)
                    simplified.pop("discard_result", None)
                emitted = _emit_stmt(simplified, indent="", ctx=ctx)
                lines.extend(emitted)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
