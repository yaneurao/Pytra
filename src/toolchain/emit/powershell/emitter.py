"""EAST3 → PowerShell source code emitter (toolchain2).

CommonRenderer + override 構成ではなく、PS1 固有の動的型付け言語特性を直接レンダリングする
スタンドアロン関数ベース emitter。

§5 準拠: pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

import re

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.common.code_emitter import (
    RuntimeMapping,
    build_import_alias_map,
    load_runtime_mapping,
    should_skip_module,
)
from toolchain.emit.powershell.types import ps1_string_literal
from toolchain.emit.powershell.types import safe_ps1_ident


# ---------------------------------------------------------------------------
# Emit context
# ---------------------------------------------------------------------------

@dataclass
class EmitContext:
    """Per-module mutable state during PS1 emission."""
    module_id: str = ""
    root_rel_prefix: str = ""
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    class_names: set[str] = field(default_factory=set)
    class_bases: dict[str, str] = field(default_factory=dict)
    class_method_names: dict[str, set[str]] = field(default_factory=dict)
    class_properties: dict[str, set[str]] = field(default_factory=dict)
    current_class: str = ""
    lambda_vars: set[str] = field(default_factory=set)
    function_names: set[str] = field(default_factory=set)
    import_alias_map: dict[str, str] = field(default_factory=dict)
    import_func_aliases: dict[str, str] = field(default_factory=dict)
    arg_types: dict[str, str] = field(default_factory=dict)
    in_main_guard: bool = False
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    leaf_classes: set[str] = field(default_factory=set)  # classes with no subclasses (safe for static dispatch)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NO_EMIT_IMPORT_MODULES: frozenset[str] = frozenset({
    "typing", "pytra.typing", "dataclasses", "__future__",
    "pytra.std.extern", "pytra.std.abi",
})


def _gs(node: JsonVal, key: str) -> str:
    """Get string value from JsonVal dict."""
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, str):
            return v
    return ""


def _gl(node: JsonVal, key: str) -> list[JsonVal]:
    """Get list value from JsonVal dict."""
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, list):
            return v
    return []


def _gd(node: JsonVal, key: str) -> dict[str, JsonVal]:
    """Get dict value from JsonVal dict."""
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, dict):
            return v
    return {}


def _call_keyword_map(expr: dict[str, JsonVal]) -> dict[str, JsonVal]:
    out: dict[str, JsonVal] = {}
    keywords = _gl(expr, "keywords")
    for kw in keywords:
        if isinstance(kw, dict):
            key = _gs(kw, "arg")
            if key != "":
                out[key] = kw.get("value")
    return out


def _safe(name: str, fallback: str) -> str:
    return safe_ps1_ident(name, fallback)


def _var(name: str) -> str:
    """Convert identifier name to $-prefixed PS1 variable."""
    return "$" + _safe(name, "_v")


def _is_extern_value(value: JsonVal) -> bool:
    """Check if value is extern(...) call or Unbox(extern(...))."""
    if not isinstance(value, dict):
        return False
    kind = _gs(value, "kind")
    if kind == "Unbox":
        return _is_extern_value(value.get("value"))
    if kind == "Call":
        func = value.get("func")
        if isinstance(func, dict) and _gs(func, "id") == "extern":
            return True
    return False


def _has_format_spec(doc: JsonVal) -> bool:
    """Check if doc contains FormattedValue with format_spec."""
    if isinstance(doc, dict):
        if _gs(doc, "kind") == "FormattedValue":
            fs = doc.get("format_spec")
            if isinstance(fs, str) and fs != "":
                return True
        for v in doc.values():
            if _has_format_spec(v):
                return True
    elif isinstance(doc, list):
        for item in doc:
            if _has_format_spec(item):
                return True
    return False


def _is_type_alias_like_assign(stmt: dict[str, JsonVal]) -> bool:
    target = stmt.get("target")
    if not isinstance(target, dict):
        targets = _gl(stmt, "targets")
        if len(targets) == 1 and isinstance(targets[0], dict):
            target = targets[0]
    if not isinstance(target, dict) or _gs(target, "kind") != "Name":
        return False
    name = _gs(target, "id")
    if name == "" or not name[0].isupper():
        return False
    value = stmt.get("value")
    if not isinstance(value, dict):
        return False
    value_kind = _gs(value, "kind")
    if value_kind == "Subscript":
        owner = value.get("value")
        if isinstance(owner, dict):
            return _gs(owner, "id") in ("dict", "list", "set", "tuple", "Callable")
    if value_kind == "Name":
        return _gs(value, "id") in ("dict", "list", "set", "tuple", "Callable")
    return False


def _postprocess_ps1_native_code(text: str) -> str:
    text = text.replace("$cli_argv = (__pytra_str_slice $argv 1 $argv.Length)", "$cli_argv = @($args)")
    text = text.replace("$cli_argv = (__pytra_str_slice $args 1 $args.Length)", "$cli_argv = @($args)")
    helper_prefixes = (
        "run_", "write_", "emit_", "build_", "load_", "init_", "should_", "normalize_", "cpp_", "runtime_", "resolve_", "native_",
        "collect_", "is_", "jv_", "nd_", "_rb_", "split_", "extract_", "parse_", "map_", "render_",
        "loads", "dumps",
    )

    def _rewrite_helper_call(match: re.Match[str]) -> str:
        name = match.group(1)
        if name.startswith(helper_prefixes):
            return "(& " + name + " "
        return match.group(0)

    text = re.sub(r"\(& \$([A-Za-z_][A-Za-z0-9_]*)\s+", _rewrite_helper_call, text)
    text = text.replace("(active_direct_emit_fn $east_doc $output_dir)", "(& $active_direct_emit_fn $east_doc $output_dir)")
    text = text.replace("(active_emit_fn $east_doc)", "(& $active_emit_fn $east_doc)")
    text = text.replace('.Contains($cache_key)', '.ContainsKey($cache_key)')
    text = text.replace("if (($cached.Count -gt 0)) {", "if (((__pytra_len $cached) -gt 0)) {")
    text = text.replace(").raw", ')[\"raw\"]')
    text = text.replace("JsonValue_as_obj (JsonValue $node)", "JsonValue_as_obj $node")
    text = text.replace("JsonValue_as_arr (JsonValue $node)", "JsonValue_as_arr $node")
    text = text.replace("JsonValue_as_str (JsonValue $node)", "JsonValue_as_str $node")
    text = text.replace(
        '    if (($module_id -eq "")) {\n        $module_id = (& _str $meta "module_id")\n    }\n',
        '    if (($module_id -eq "")) {\n        $module_id = (& _str $meta "module_id")\n    }\n'
        '    if (($module_id -eq "")) {\n        $module_id = (& _str $meta "_cli_module_id")\n    }\n',
    )
    text = text.replace(
        '$ctx["is_entry"] = $(if (((__pytra_len $emit_ctx_meta) -gt 0)) { (& _bool $emit_ctx_meta "is_entry") } else { $false })',
        '$ctx["is_entry"] = $(if (((__pytra_len $emit_ctx_meta) -gt 0)) { (& _bool $emit_ctx_meta "is_entry") } else { (& _bool $meta "_cli_is_entry") })',
    )
    return text


def _module_id_to_import_path(module_id: str, root_rel_prefix: str) -> str:
    """Convert module_id to relative .ps1 import path (flat filename)."""
    if module_id == "":
        return ""
    # Flat multi-module emit writes files as module_id.replace(".", "_") + ".ps1"
    flat = module_id.replace(".", "_") + ".ps1"
    return root_rel_prefix + flat


# ---------------------------------------------------------------------------
# Expression rendering
# ---------------------------------------------------------------------------

_BINOP_MAP: dict[str, str] = {
    "Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "Mod": "%",
    "BitAnd": "-band", "BitOr": "-bor", "BitXor": "-bxor",
    "LShift": "-shl", "RShift": "-shr",
}

_COMPARE_MAP: dict[str, str] = {
    "Eq": "-eq", "NotEq": "-ne", "Lt": "-lt", "LtE": "-le",
    "Gt": "-gt", "GtE": "-ge", "Is": "-eq", "IsNot": "-ne",
}

_UNARYOP_MAP: dict[str, str] = {
    "USub": "-", "UAdd": "+", "Not": "-not ", "Invert": "-bnot ",
}


def _static_pod_isinstance(value_type: str, expected_type: str) -> str:
    pod_types = {
        "bool", "str", "string",
        "int", "int64", "int32", "int16", "int8",
        "uint64", "uint32", "uint16", "uint8",
        "float", "float64", "float32",
    }
    if value_type not in pod_types or expected_type not in pod_types:
        return ""
    def _norm(t: str) -> str:
        if t == "int":
            return "int64"
        if t == "float":
            return "float64"
        if t == "string":
            return "str"
        return t
    return "$true" if _norm(value_type) == _norm(expected_type) else "$false"


def _render_lvalue(ctx: EmitContext, expr: JsonVal) -> str:
    """Render left-hand side (assignment target)."""
    if not isinstance(expr, dict):
        return _render_expr(ctx, expr)
    kind = _gs(expr, "kind")
    if kind == "Attribute":
        value_node = expr.get("value")
        attr = _gs(expr, "attr")
        if isinstance(value_node, dict):
            vname = _gs(value_node, "id") if _gs(value_node, "kind") == "Name" else ""
            if vname == "sys" and attr == "argv":
                return "$args"
            if vname == "self":
                return '$self["' + attr + '"]'
            if vname in ctx.class_names:
                return "$script:" + _safe(attr, "_cv")
        value = _render_expr(ctx, value_node)
        return value + '["' + attr + '"]'
    if kind == "Subscript":
        value = _render_expr(ctx, expr.get("value"))
        index = _render_expr(ctx, expr.get("slice"))
        return value + "[" + index + "]"
    return _render_expr(ctx, expr)


def _render_expr(ctx: EmitContext, expr: JsonVal) -> str:
    if expr is None:
        return "$null"
    if isinstance(expr, bool):
        return "$true" if expr else "$false"
    if isinstance(expr, int):
        return str(expr)
    if isinstance(expr, float):
        s = repr(expr)
        if "inf" in s.lower():
            return "[double]::PositiveInfinity" if expr > 0.0 else "[double]::NegativeInfinity"
        return s
    if isinstance(expr, str):
        return ps1_string_literal(expr)
    if not isinstance(expr, dict):
        return "$null"

    kind = _gs(expr, "kind")

    if kind == "Name":
        raw = _gs(expr, "id")
        if raw == "True" or raw == "true":
            return "$true"
        if raw == "False" or raw == "false":
            return "$false"
        if raw == "None" or raw == "null":
            return "$null"
        renamed = ctx.renamed_symbols.get(raw, raw)
        rt = _gs(expr, "resolved_type")
        if rt.startswith("callable[") or rt == "callable" or rt.startswith("Callable[") or rt == "Callable":
            if (raw in ctx.function_names or renamed in ctx.function_names) and raw not in ctx.lambda_vars:
                return '"' + _safe(renamed, "_fn") + '"'
        return "$" + _safe(renamed, "_v")

    if kind == "Constant":
        value = expr.get("value")
        if value is None:
            return "$null"
        if isinstance(value, bool):
            return "$true" if value else "$false"
        if isinstance(value, int):
            # PS1 stores integer literals ≤ Int32.MaxValue as Int32.
            # Int32 * Int32 overflow promotes to Double (not Int64), breaking integer arithmetic.
            # Use [long] cast only for large values where overflow is a real risk.
            # Small constants (|N| ≤ 32767) fit in 16 bits; 32767*32767 < Int32.MaxValue so
            # they cannot cause Int32 overflow even when multiplied together.
            # Large constants need [long] to prevent overflow in multiplications.
            if abs(value) > 32767:
                return "([long]" + str(value) + ")"
            return str(value)
        if isinstance(value, float):
            s = repr(value)
            if "inf" in s.lower():
                return "[double]::PositiveInfinity" if value > 0.0 else "[double]::NegativeInfinity"
            return s
        if isinstance(value, str):
            return ps1_string_literal(value)
        return "$null"

    if kind == "UnaryOp":
        op = _gs(expr, "op")
        operand = _render_expr(ctx, expr.get("operand"))
        ps_op = _UNARYOP_MAP.get(op, "-")
        return "(" + ps_op + operand + ")"

    if kind == "BinOp":
        op = _gs(expr, "op")
        left_node = expr.get("left")
        right_node = expr.get("right")
        left = _render_expr(ctx, left_node)
        right = _render_expr(ctx, right_node)
        left_rt = _gs(left_node, "resolved_type") if isinstance(left_node, dict) else ""
        right_rt = _gs(right_node, "resolved_type") if isinstance(right_node, dict) else ""
        if op == "Div" and left_rt in ("Path", "PyPath", "pytra.std.pathlib.Path") and right_rt in ("str", "string"):
            return "(Path_joinpath " + left + " " + right + ")"
        if op == "Pow":
            return "[Math]::Pow(" + left + ", " + right + ")"
        if op == "FloorDiv":
            return "([long][Math]::Floor([double](" + left + ") / [double](" + right + ")))"
        # List concatenation: preserve List[object] type
        if op == "Add":
            rt_bin = _gs(expr, "resolved_type")
            if isinstance(rt_bin, str) and rt_bin.lower().startswith("list["):
                return "(__pytra_list (" + left + " + " + right + "))"
        ps_op = _BINOP_MAP.get(op, "+")
        return "(" + left + " " + ps_op + " " + right + ")"

    if kind == "Compare":
        left = _render_expr(ctx, expr.get("left"))
        ops = _gl(expr, "ops")
        comparators = _gl(expr, "comparators")
        if len(ops) == 0 or len(comparators) == 0:
            return "$true"
        op0 = ops[0]
        op0_str = _gs(op0, "kind") if isinstance(op0, dict) else (op0 if isinstance(op0, str) else "")
        if op0_str == "In":
            _cmp0 = comparators[0]
            _cmp_rt = _gs(_cmp0, "resolved_type") if isinstance(_cmp0, dict) else ""
            right = _render_expr(ctx, _cmp0)
            if _cmp_rt.lower().startswith("dict[") or _cmp_rt == "dict":
                return right + ".ContainsKey(" + left + ")"
            return "(__pytra_in " + left + " " + right + ")"
        if op0_str == "NotIn":
            _cmp0 = comparators[0]
            _cmp_rt = _gs(_cmp0, "resolved_type") if isinstance(_cmp0, dict) else ""
            right = _render_expr(ctx, _cmp0)
            if _cmp_rt.lower().startswith("dict[") or _cmp_rt == "dict":
                return "-not " + right + ".ContainsKey(" + left + ")"
            return "(__pytra_not_in " + left + " " + right + ")"
        ps_op = _COMPARE_MAP.get(op0_str, "-eq")
        right = _render_expr(ctx, comparators[0])
        if len(ops) == 1:
            return "(" + left + " " + ps_op + " " + right + ")"
        parts: list[str] = ["(" + left + " " + ps_op + " " + right + ")"]
        i = 1
        while i < len(ops) and i < len(comparators):
            prev_right = _render_expr(ctx, comparators[i - 1])
            op_i = ops[i]
            op_i_str = _gs(op_i, "kind") if isinstance(op_i, dict) else (op_i if isinstance(op_i, str) else "")
            next_op = _COMPARE_MAP.get(op_i_str, "-eq")
            next_right = _render_expr(ctx, comparators[i])
            parts.append("(" + prev_right + " " + next_op + " " + next_right + ")")
            i += 1
        return "(" + " -and ".join(parts) + ")"

    if kind == "BoolOp":
        op = _gs(expr, "op")
        values = _gl(expr, "values")
        rendered = [_render_expr(ctx, v) for v in values]
        if len(rendered) == 0:
            return "$null"

        def _is_trivial(s: str) -> bool:
            """True if cheap and safe to evaluate twice."""
            if s.startswith("$") and " " not in s:  # simple var ref or $null/$true/$false
                return True
            if s.startswith("($") and s.endswith(")"):  # parenthesized compare e.g. ($i -lt $n)
                return True
            return False

        def _is_bool_typed(node: JsonVal) -> bool:
            """True if node always produces a PS1 bool — safe to use directly in if condition."""
            if not isinstance(node, dict):
                return False
            nk = _gs(node, "kind")
            if nk == "Compare":
                return True
            if nk == "UnaryOp" and _gs(node, "op") == "Not":
                return True
            if nk == "BoolOp":
                return True
            if nk == "Call":
                rt = _gs(node, "runtime_call")
                if rt in ("str.isdigit", "str.isalpha", "str.isalnum", "str.isspace",
                          "str.startswith", "str.endswith"):
                    return True
                # resolved_type == "bool" from type resolver
                if _gs(node, "resolved_type") in ("bool",):
                    return True
            if nk == "Name" and _gs(node, "resolved_type") in ("bool",):
                return True
            return False

        if op == "Or":
            if len(rendered) == 1:
                return rendered[0]
            result = rendered[-1]
            i = len(rendered) - 2
            while i >= 0:
                v = rendered[i]
                vnode = values[i] if i < len(values) else None
                if _is_bool_typed(vnode):
                    # v is always bool: no __pytra_bool needed, return $true/$false directly
                    result = "$(if (" + v + ") { $true } else { " + result + " })"
                elif _is_trivial(v):
                    result = "$(if ((__pytra_bool " + v + ")) { " + v + " } else { " + result + " })"
                else:
                    tmp = "$__or" + str(i)
                    result = "$(" + tmp + " = " + v + "; if ((__pytra_bool " + tmp + ")) { " + tmp + " } else { " + result + " })"
                i -= 1
            return result
        else:
            if len(rendered) == 1:
                return rendered[0]
            result = rendered[-1]
            i = len(rendered) - 2
            while i >= 0:
                v = rendered[i]
                vnode = values[i] if i < len(values) else None
                if _is_bool_typed(vnode):
                    # v is always bool: no __pytra_bool needed, return $false directly on falsy
                    result = "$(if (-not " + v + ") { $false } else { " + result + " })"
                elif _is_trivial(v):
                    result = "$(if (-not (__pytra_bool " + v + ")) { " + v + " } else { " + result + " })"
                else:
                    tmp = "$__and" + str(i)
                    result = "$(" + tmp + " = " + v + "; if (-not (__pytra_bool " + tmp + ")) { " + tmp + " } else { " + result + " })"
                i -= 1
            return result

    if kind == "Attribute":
        value_node = expr.get("value")
        value = _render_expr(ctx, value_node)
        attr = _gs(expr, "attr")
        # type(v).__name__ → $v["__type__"]
        if attr == "__name__" and isinstance(value_node, dict) and _gs(value_node, "kind") == "Call":
            type_func_n = value_node.get("func")
            if isinstance(type_func_n, dict) and _gs(type_func_n, "id") == "type":
                type_args_n = _gl(value_node, "args")
                if len(type_args_n) > 0:
                    return _render_expr(ctx, type_args_n[0]) + '["__type__"]'
        if isinstance(value_node, dict):
            vname = _gs(value_node, "id") if _gs(value_node, "kind") == "Name" else ""
            if vname == "self":
                cur_cls = ctx.current_class
                if cur_cls != "" and attr in ctx.class_properties.get(cur_cls, set()):
                    return "(" + cur_cls + "_" + _safe(attr, "_p") + " $self)"
                return '$self["' + attr + '"]'
            if vname in ctx.import_alias_map:
                mod_full_ia = ctx.import_alias_map.get(vname, vname)
                mod_short_ia = mod_full_ia.rsplit(".", 1)[-1] if "." in mod_full_ia else mod_full_ia
                qualified_key_ia = mod_short_ia + "." + attr
                if qualified_key_ia in ctx.mapping.calls:
                    return ctx.mapping.calls[qualified_key_ia]
                return "$" + _safe(attr, "_f")
            if vname in ctx.class_names:
                return "$script:" + _safe(attr, "_cv")
            vtype = _gs(value_node, "resolved_type")
            if vtype in ctx.class_names:
                props = ctx.class_properties.get(vtype, set())
                if attr in props:
                    return "(& (Get-Command (\"{0}_{1}\" -f " + value + '["__type__"], "' + attr + '")) ' + value + ")"
                return value + '["' + attr + '"]'
            if vtype == "module":
                # Generic module attribute access: look up from mapping.calls
                mod_full = ctx.import_alias_map.get(vname, vname)
                mod_short = mod_full.rsplit(".", 1)[-1] if "." in mod_full else mod_full
                qualified_key = mod_short + "." + attr
                if qualified_key in ctx.mapping.calls:
                    return ctx.mapping.calls[qualified_key]
        _DOTNET_PROPS: frozenset[str] = frozenset({
            "Length", "Count", "Keys", "Values",
            "Name", "FullName", "Extension", "Directory",
        })
        safe_attr = _safe(attr, "prop")
        if safe_attr in _DOTNET_PROPS or (safe_attr != "" and safe_attr[0].isupper()):
            return value + "." + safe_attr
        if isinstance(value_node, dict):
            vtype2 = _gs(value_node, "resolved_type")
            if vtype2 not in ctx.class_names and vtype2 not in ("str", "int", "int64", "float", "float64", "bool"):
                return "(__pytra_getattr " + value + ' "' + attr + '")'
        return value + '["' + attr + '"]'

    if kind == "Call":
        return _render_call(ctx, expr)

    if kind == "List":
        elements = _gl(expr, "elements")
        if len(elements) == 0:
            elements = _gl(expr, "elts")
        if len(elements) == 0:
            return "([System.Collections.Generic.List[object]]::new())"
        rendered = [_render_expr(ctx, e) for e in elements]
        # Use __pytra_mklist (not [List]@(...)) to avoid PS1's @() flattening of inner arrays.
        # [List]@(@(1,2), @(3,4)) flattens to 4 scalar elements; mklist preserves tuple elements.
        return "(__pytra_mklist " + " ".join(rendered) + ")"

    if kind == "Tuple":
        elements = _gl(expr, "elements")
        if len(elements) == 0:
            elements = _gl(expr, "elts")
        if len(elements) == 0:
            return "@()"
        rendered = [_render_expr(ctx, e) for e in elements]
        return "@(" + ", ".join(rendered) + ")"

    if kind == "Set":
        elements = _gl(expr, "elements")
        if len(elements) == 0:
            elements = _gl(expr, "elts")
        if len(elements) == 0:
            return "(__pytra_set)"
        rendered = [_render_expr(ctx, e) for e in elements]
        return "(__pytra_set " + " ".join(rendered) + ")"

    if kind == "Dict":
        keys = _gl(expr, "keys")
        vals = _gl(expr, "values")
        if len(keys) == 0 and len(vals) == 0:
            entries = _gl(expr, "entries")
            for entry in entries:
                if isinstance(entry, dict):
                    k = entry.get("key")
                    v = entry.get("value")
                    if k is not None:
                        keys.append(k)
                    if v is not None:
                        vals.append(v)
        if len(keys) == 0:
            return "@{}"
        parts3: list[str] = []
        seen_ps_keys: set[str] = set()
        i2 = 0
        while i2 < len(keys) and i2 < len(vals):
            key_node = keys[i2]
            if isinstance(key_node, dict) and _gs(key_node, "kind") == "Constant":
                key_value = key_node.get("value")
                if isinstance(key_value, str):
                    normalized_key = key_value.lower()
                    if normalized_key in seen_ps_keys:
                        i2 += 1
                        continue
                    seen_ps_keys.add(normalized_key)
            parts3.append(_render_expr(ctx, keys[i2]) + " = " + _render_expr(ctx, vals[i2]))
            i2 += 1
        return "@{" + "; ".join(parts3) + "}"

    if kind == "ListComp":
        elt = expr.get("elt")
        generators = _gl(expr, "generators")
        if len(generators) == 0:
            return "([System.Collections.Generic.List[object]]::new())"

        def _build_lc(gens: list[JsonVal], elt_node: JsonVal, depth: int) -> str:
            if depth >= len(gens):
                rendered_elt2 = _render_expr(ctx, elt_node)
                if isinstance(elt_node, dict) and _gs(elt_node, "kind") in ("ListComp", "List", "Tuple"):
                    rendered_elt2 = "," + rendered_elt2
                return rendered_elt2
            gen_item = gens[depth]
            if not isinstance(gen_item, dict):
                return _render_expr(ctx, elt_node)
            gen_target = gen_item.get("target")
            gen_iter = gen_item.get("iter")
            gen_ifs = _gl(gen_item, "ifs")
            irendered = _render_expr(ctx, gen_iter)
            if isinstance(gen_iter, dict) and _gs(gen_iter, "resolved_type") == "str":
                irendered = irendered + ".ToCharArray()"
            elif isinstance(gen_iter, dict):
                _girt = _gs(gen_iter, "resolved_type")
                if _girt.startswith("set[") or _girt == "set":
                    irendered = irendered + ".Keys"
            inner = _build_lc(gens, elt_node, depth + 1)
            # Tuple target: unpack elements
            if isinstance(gen_target, dict) and _gs(gen_target, "kind") == "Tuple":
                elts = _gl(gen_target, "elements")
                unpack_parts = [
                    "$" + _safe(_gs(e, "id"), "_lc" + str(i)) + " = $_[" + str(i) + "]"
                    for i, e in enumerate(elts) if isinstance(e, dict)
                ]
                unpack_stmt = "; ".join(unpack_parts) + "; " if unpack_parts else ""
                if len(gen_ifs) > 0:
                    cond_parts2 = " -and ".join(["(" + _render_expr(ctx, c) + ")" for c in gen_ifs])
                    return "@(" + irendered + " | ForEach-Object { " + unpack_stmt + "if (" + cond_parts2 + ") { " + inner + " } })"
                return "@(" + irendered + " | ForEach-Object { " + unpack_stmt + inner + " })"
            tname = "$" + _safe(
                _gs(gen_target, "id") if isinstance(gen_target, dict) else "_lc" + str(depth),
                "_lc"
            )
            if len(gen_ifs) > 0:
                cond_parts2 = " -and ".join(["(" + _render_expr(ctx, c) + ")" for c in gen_ifs])
                return "@(" + irendered + " | ForEach-Object { " + tname + " = $_; if (" + cond_parts2 + ") { " + inner + " } })"
            return "@(" + irendered + " | ForEach-Object { " + tname + " = $_; " + inner + " })"

        return "(__pytra_list (" + _build_lc(generators, elt, 0) + "))"

    if kind == "DictComp":
        key_expr = expr.get("key")
        value_expr = expr.get("value")
        generators = _gl(expr, "generators")
        if len(generators) == 0 or key_expr is None or value_expr is None:
            return "@{}"
        gen = generators[0]
        if not isinstance(gen, dict):
            return "@{}"
        gen_target = gen.get("target")
        gen_iter = gen.get("iter")
        gen_ifs = _gl(gen, "ifs")
        tname = "$" + _safe(_gs(gen_target, "id") if isinstance(gen_target, dict) else "_dc", "_dc")
        irendered = _render_expr(ctx, gen_iter)
        k_rendered = _render_expr(ctx, key_expr)
        v_rendered = _render_expr(ctx, value_expr)
        body = "$__dc_result[" + k_rendered + "] = " + v_rendered
        if len(gen_ifs) > 0:
            cond = " -and ".join(["(" + _render_expr(ctx, c) + ")" for c in gen_ifs])
            body = "if (" + cond + ") { " + body + " }"
        return "& { $__dc_result = @{}; foreach (" + tname + " in " + irendered + ") { " + body + " }; $__dc_result }"

    if kind == "SetComp":
        elt = expr.get("elt")
        generators = _gl(expr, "generators")
        if len(generators) == 0 or elt is None:
            return "@{}"
        gen = generators[0]
        if not isinstance(gen, dict):
            return "@{}"
        gen_target = gen.get("target")
        gen_iter = gen.get("iter")
        gen_ifs = _gl(gen, "ifs")
        tname = "$" + _safe(_gs(gen_target, "id") if isinstance(gen_target, dict) else "_sc", "_sc")
        irendered = _render_expr(ctx, gen_iter)
        e_rendered = _render_expr(ctx, elt)
        body = "$__sc_result[" + e_rendered + "] = $true"
        if len(gen_ifs) > 0:
            cond = " -and ".join(["(" + _render_expr(ctx, c) + ")" for c in gen_ifs])
            body = "if (" + cond + ") { " + body + " }"
        return "& { $__sc_result = @{}; foreach (" + tname + " in " + irendered + ") { " + body + " }; $__sc_result }"

    if kind == "Subscript":
        value_node = expr.get("value")
        value = _render_expr(ctx, value_node)
        slice_any = expr.get("slice")
        if isinstance(slice_any, dict) and _gs(slice_any, "kind") == "Slice":
            lower = _render_expr(ctx, slice_any.get("lower")) if slice_any.get("lower") is not None else "0"
            upper_node = slice_any.get("upper")
            if upper_node is not None:
                upper = _render_expr(ctx, upper_node)
            else:
                upper = value + ".Length"
            if isinstance(value_node, dict) and _gs(value_node, "kind") == "Name" and _gs(value_node, "id") == "argv":
                return "@(" + value + ")[" + lower + "..(" + upper + " - 1)]"
            return "(__pytra_str_slice " + value + " " + lower + " " + upper + ")"
        index = _render_expr(ctx, slice_any)
        val_type = _gs(value_node, "resolved_type") if isinstance(value_node, dict) else ""
        if val_type == "str":
            return "([string]" + value + "[" + index + "])"
        raw_vt = val_type.lower() if isinstance(val_type, str) else ""
        if raw_vt.startswith("list[") or raw_vt in ("list", "bytes", "bytearray"):
            # Use direct $list[$i] when optimizer guarantees non-negative index.
            # This avoids __pytra_list_idx function-call overhead in tight loops and
            # also correctly preserves tuple elements (no pipeline enumeration).
            meta = expr.get("meta") if isinstance(expr, dict) else None
            access_v1 = meta.get("subscript_access_v1") if isinstance(meta, dict) else None
            if isinstance(access_v1, dict) and access_v1.get("negative_index") == "skip":
                return value + "[" + index + "]"
            return "(__pytra_list_idx " + value + " " + index + ")"
        return value + "[" + index + "]"

    if kind == "IfExp":
        test = _render_expr(ctx, expr.get("test"))
        body = _render_expr(ctx, expr.get("body"))
        orelse = _render_expr(ctx, expr.get("orelse"))
        return "$(if (" + test + ") { " + body + " } else { " + orelse + " })"

    if kind in ("JoinedStr", "FString"):
        parts_list = _gl(expr, "values")
        if len(parts_list) == 0:
            return '""'
        segments: list[str] = []
        for part in parts_list:
            if not isinstance(part, dict):
                continue
            pk = _gs(part, "kind")
            if pk == "Constant":
                v2 = part.get("value")
                if isinstance(v2, str):
                    escaped = v2.replace("`", "``").replace('"', '`"').replace("$", "`$")
                    segments.append(escaped)
            elif pk == "FormattedValue":
                inner = _render_expr(ctx, part.get("value"))
                conversion = _gs(part, "conversion")
                format_spec = _gs(part, "format_spec")
                if conversion != "" and conversion != "-1":
                    segments.append("$(py_format_conversion " + inner + " " + ps1_string_literal(conversion) + ")")
                elif format_spec != "":
                    segments.append("$(py_format_value " + inner + " " + ps1_string_literal(format_spec) + ")")
                else:
                    segments.append("$(" + inner + ")")
            else:
                segments.append("$(" + _render_expr(ctx, part) + ")")
        return '"' + "".join(segments) + '"'

    if kind == "IsInstance":
        value_node2 = expr.get("value")
        type_name = _gs(expr, "expected_type_name")
        if type_name != "":
            value_type = _gs(value_node2, "resolved_type") if isinstance(value_node2, dict) else ""
            static_check = _static_pod_isinstance(value_type, type_name)
            if static_check != "":
                return static_check
            isinstance_fn = ctx.mapping.calls.get("py_isinstance", "__pytra_type_check")
            return "(" + isinstance_fn + " " + _render_expr(ctx, value_node2) + ' "' + type_name + '")'
        return "$true"

    if kind in ("Cast", "Unbox", "Box"):
        return _render_expr(ctx, expr.get("value"))

    if kind == "ObjLen":
        _olen_val = expr.get("value")
        _olen_rt = _gs(_olen_val, "resolved_type") if isinstance(_olen_val, dict) else ""
        _olen_rendered = _render_expr(ctx, _olen_val)
        if _olen_rt.lower().startswith("list[") or _olen_rt == "list":
            return _olen_rendered + ".Count"
        if _olen_rt == "str":
            return _olen_rendered + ".Length"
        return "(__pytra_len " + _olen_rendered + ")"

    if kind == "ObjStr":
        return "(__pytra_str " + _render_expr(ctx, expr.get("value")) + ")"

    if kind == "ObjBool":
        return "(__pytra_bool " + _render_expr(ctx, expr.get("value")) + ")"

    if kind == "RangeExpr":
        start = _render_expr(ctx, expr.get("start"))
        stop = _render_expr(ctx, expr.get("stop"))
        step = expr.get("step")
        if step is not None:
            return "__pytra_range " + start + " " + stop + " " + _render_expr(ctx, step)
        return "__pytra_range " + start + " " + stop

    if kind == "Lambda":
        params = _gl(expr, "args")
        if len(params) == 0:
            params = _gl(expr, "params")
        body = expr.get("body")
        lambda_params: list[str] = []
        for p in params:
            if isinstance(p, dict):
                pname = "$" + _safe(_gs(p, "arg"), "_p")
                default_node = p.get("default")
                if default_node is not None:
                    lambda_params.append(pname + " = " + _render_expr(ctx, default_node))
                else:
                    lambda_params.append(pname)
            elif isinstance(p, str):
                lambda_params.append("$" + _safe(p, "_p"))
        ps_params = ", ".join(lambda_params)
        return "{ param(" + ps_params + ") " + _render_expr(ctx, body) + " }"

    if kind == "TupleUnpack":
        # lowered by EAST3 — render as parenthesized tuple for assignments
        targets = _gl(expr, "targets")
        if len(targets) == 0:
            return "$null"
        rendered_targets = [_render_lvalue(ctx, t) for t in targets]
        return "@(" + ", ".join(rendered_targets) + ")"

    return "$null"


def _render_call(ctx: EmitContext, expr: dict[str, JsonVal]) -> str:
    func = expr.get("func")
    args = _gl(expr, "args")
    rendered_args = [_render_expr(ctx, a) for a in args]
    keywords = _gl(expr, "keywords")
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            if kw_val is not None:
                rendered_args.append(_render_expr(ctx, kw_val))

    # Check Call-level runtime_call first (covers Attribute method calls like list.clear)
    call_runtime_call = _gs(expr, "runtime_call")
    if call_runtime_call != "" and call_runtime_call not in ("__CAST__", "__THROW__"):
        call_mapped = ctx.mapping.calls.get(call_runtime_call, "")
        if call_mapped != "" and call_mapped not in ("__CAST__", "__THROW__", "__LIST_APPEND__", "__DICT_GET__", "__DICT_ITEMS__", "__DICT_KEYS__", "__DICT_VALUES__", "__SET_ADD__"):
            # For Attribute calls (obj.method()), prepend the receiver as first arg
            _rcall_args = list(rendered_args)
            if isinstance(func, dict) and _gs(func, "kind") == "Attribute":
                receiver_node = func.get("value")
                if receiver_node is not None:
                    _rcall_args = [_render_expr(ctx, receiver_node)] + _rcall_args
            # Inline string predicates using PS1 regex (avoids function-call overhead, ~10x faster)
            _STR_PRED = {
                "str.isdigit": r"^\d+$",
                "str.isalpha": r"^[A-Za-z]+$",
                "str.isalnum": r"^[A-Za-z0-9]+$",
                "str.isspace": r"^\s+$",
            }
            if call_runtime_call in _STR_PRED and len(_rcall_args) == 1:
                return "(([string](" + _rcall_args[0] + ")) -match '" + _STR_PRED[call_runtime_call] + "')"
            if call_mapped.startswith("[Math]::"):
                if call_mapped.endswith("::PI") or call_mapped.endswith("::E"):
                    return "(" + call_mapped + ")"
                return "(" + call_mapped + "(" + ", ".join(_rcall_args) + "))"
            if call_mapped.startswith("[char]::"):
                return "(" + call_mapped + "(" + ", ".join(_rcall_args) + "))"
            if len(_rcall_args) == 0:
                return "(" + call_mapped + ")"
            return "(" + call_mapped + " " + " ".join(_rcall_args) + ")"

    if isinstance(func, dict):
        fk = _gs(func, "kind")

        if fk in ("Cast", "Unbox", "Box"):
            fn_expr = _render_expr(ctx, func.get("value"))
            if len(rendered_args) == 0:
                return "(& " + fn_expr + ")"
            return "(& " + fn_expr + " " + " ".join(rendered_args) + ")"

        if fk == "Name":
            fn_name_raw = _gs(func, "id")
            fn_name = ctx.renamed_symbols.get(fn_name_raw, fn_name_raw)

            # Builtin functions
            if fn_name == "field":
                kw_map = _call_keyword_map(expr)
                factory = kw_map.get("default_factory")
                if factory is None and len(args) > 0:
                    factory = args[0]
                if isinstance(factory, dict) and _gs(factory, "kind") == "Name":
                    factory_name = _gs(factory, "id")
                    if factory_name == "dict":
                        return "@{}"
                    if factory_name == "list":
                        return "([System.Collections.Generic.List[object]]::new())"
                    if factory_name == "set":
                        return "(__pytra_set)"
                default_value = kw_map.get("default")
                if isinstance(default_value, dict):
                    return _render_expr(ctx, default_value)
                return "$null"
            if fn_name == "print":
                return "__pytra_print " + " ".join(rendered_args) if len(rendered_args) > 0 else "__pytra_print"
            if fn_name == "len":
                if len(rendered_args) > 0:
                    _len_arg = args[0] if len(args) > 0 else None
                    _len_rt = _gs(_len_arg, "resolved_type") if isinstance(_len_arg, dict) else ""
                    if _len_rt.lower().startswith("list[") or _len_rt == "list":
                        return rendered_args[0] + ".Count"
                    if _len_rt == "str":
                        return rendered_args[0] + ".Length"
                    return "(__pytra_len " + rendered_args[0] + ")"
                return "(__pytra_len)"
            if fn_name == "str":
                return "(__pytra_str " + rendered_args[0] + ")" if len(rendered_args) > 0 else "(__pytra_str)"
            if fn_name == "int":
                # Inline int() as truncate-toward-zero cast (avoids PS1 function-call overhead).
                # [long][Math]::Truncate([double]x) matches Python semantics and is 22x faster.
                if len(rendered_args) > 0:
                    return "([long][Math]::Truncate([double](" + rendered_args[0] + ")))"
                return "0"
            if fn_name == "float":
                if len(rendered_args) > 0:
                    return "(__pytra_float " + rendered_args[0] + ")"
                return "0.0"
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
            if fn_name in ("min", "py_min"):
                return "[Math]::Min(" + ", ".join(rendered_args) + ")" if len(rendered_args) > 0 else "0"
            if fn_name in ("max", "py_max"):
                return "[Math]::Max(" + ", ".join(rendered_args) + ")" if len(rendered_args) > 0 else "0"
            if fn_name in ("sum", "py_sum"):
                return "(__pytra_sum " + " ".join(rendered_args) + ")" if len(rendered_args) > 0 else "0"
            if fn_name == "isinstance":
                if len(args) >= 2:
                    type_arg = args[1]
                    if isinstance(type_arg, dict) and _gs(type_arg, "kind") == "Tuple":
                        checks: list[str] = []
                        for elem in _gl(type_arg, "elements"):
                            elem_type = _gs(elem, "id") if isinstance(elem, dict) else ""
                            if elem_type == "" and isinstance(elem, dict):
                                elem_type = _gs(elem, "repr")
                            if elem_type != "":
                                value_type = _gs(args[0], "resolved_type") if len(args) >= 1 and isinstance(args[0], dict) else ""
                                static_check = _static_pod_isinstance(value_type, elem_type)
                                if static_check != "":
                                    checks.append("(" + static_check + ")")
                                else:
                                    isinstance_fn = ctx.mapping.calls.get("py_isinstance", "__pytra_type_check")
                                    checks.append("(" + isinstance_fn + " " + rendered_args[0] + " " + ps1_string_literal(elem_type) + ")")
                        return "(" + " -or ".join(checks) + ")" if len(checks) > 0 else "$false"
                    type_name = _gs(type_arg, "id") if isinstance(type_arg, dict) else ""
                    if type_name == "" and isinstance(type_arg, dict) and _gs(type_arg, "kind") == "Constant":
                        raw_type_name = type_arg.get("value")
                        type_name = raw_type_name if isinstance(raw_type_name, str) else ""
                    if type_name != "":
                        value_type = _gs(args[0], "resolved_type") if len(args) >= 1 and isinstance(args[0], dict) else ""
                        static_check = _static_pod_isinstance(value_type, type_name)
                        if static_check != "":
                            return static_check
                        isinstance_fn = ctx.mapping.calls.get("py_isinstance", "__pytra_type_check")
                        return "(" + isinstance_fn + " " + rendered_args[0] + " " + ps1_string_literal(type_name) + ")"
                return "$false"
            if fn_name in ("cast", "typing.cast"):
                return rendered_args[1] if len(rendered_args) >= 2 else "$null"
            if fn_name == "extern":
                return rendered_args[0] if len(rendered_args) >= 1 else "$null"
            if fn_name == "sorted":
                return "(" + rendered_args[0] + " | Sort-Object)" if len(rendered_args) > 0 else "@()"
            if fn_name == "reversed":
                return "(__pytra_reversed " + rendered_args[0] + ")" if len(rendered_args) > 0 else "@()"
            if fn_name == "enumerate":
                return "(__pytra_enumerate " + rendered_args[0] + ")" if len(rendered_args) > 0 else "@()"
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
            if fn_name == "py_assert_stdout" and len(args) >= 2:
                last_arg = args[-1]
                if isinstance(last_arg, dict) and _gs(last_arg, "kind") == "Name":
                    fn_ref = _safe(_gs(last_arg, "id"), "_fn")
                    other = rendered_args[:-1]
                    return "(py_assert_stdout " + " ".join(other) + ' "' + fn_ref + '")'

            # Check resolved runtime mapping
            runtime_call = _gs(expr, "runtime_call")
            resolved_runtime_call = _gs(expr, "resolved_runtime_call")
            runtime_symbol = _gs(expr, "runtime_symbol")
            runtime_module_id = _gs(expr, "runtime_module_id")
            runtime_keys: list[str] = []
            if runtime_call != "":
                runtime_keys.append(runtime_call)
            if resolved_runtime_call != "":
                runtime_keys.append(resolved_runtime_call)
            if runtime_module_id != "" and runtime_symbol != "":
                runtime_keys.append(runtime_module_id + "." + runtime_symbol)
            if runtime_symbol != "":
                runtime_keys.append(runtime_symbol)
            mapped = ""
            for key in runtime_keys:
                maybe = ctx.mapping.calls.get(key, "")
                if maybe != "":
                    mapped = maybe
                    break
            if mapped != "" and mapped != "__CAST__" and mapped != "__THROW__":
                if mapped.startswith("[Math]::"):
                    if mapped.endswith("::PI") or mapped.endswith("::E"):
                        return "(" + mapped + ")"
                    return "(" + mapped + "(" + ", ".join(rendered_args) + "))"
                if len(rendered_args) == 0:
                    return "(" + mapped + ")"
                return "(" + mapped + " " + " ".join(rendered_args) + ")"

            # Import aliases (e.g. from math import sqrt)
            if fn_name in ctx.import_func_aliases:
                ps_func = ctx.import_func_aliases[fn_name]
                if ps_func.startswith("[Math]::"):
                    if ps_func.endswith("::PI") or ps_func.endswith("::E"):
                        return "(" + ps_func + ")"
                    return "(" + ps_func + "(" + ", ".join(rendered_args) + "))"
                return "(" + ps_func + " " + " ".join(rendered_args) + ")"

            safe_fn = _safe(fn_name, "_fn")

            # Callable variable: call via & $var (handles string names and scriptblocks)
            # Use & $var whenever resolved_type is callable and it's not a top-level function/class.
            func_rt = _gs(func, "resolved_type")
            if (func_rt.startswith("callable") or func_rt.startswith("Callable")) and fn_name not in ctx.class_names and mapped == "":
                if fn_name in ctx.function_names:
                    if len(rendered_args) == 0:
                        return "(& " + safe_fn + ")"
                    return "(& " + safe_fn + " " + " ".join(rendered_args) + ")"
                if len(rendered_args) == 0:
                    return "(& $" + safe_fn + ")"
                return "(& $" + safe_fn + " " + " ".join(rendered_args) + ")"

            # Lambda / scriptblock call: & $var args
            if fn_name in ctx.lambda_vars:
                if len(rendered_args) == 0:
                    return "(& $" + safe_fn + ")"
                return "(& $" + safe_fn + " " + " ".join(rendered_args) + ")"

            # Class constructor — use $() subexpression (faster than & {} script block)
            if fn_name in ctx.class_names:
                if len(rendered_args) == 0:
                    return "$($__obj = @{}; " + safe_fn + " $__obj; $__obj)"
                return "$($__obj = @{}; " + safe_fn + " $__obj " + " ".join(rendered_args) + "; $__obj)"

            if len(rendered_args) == 0:
                return "(" + safe_fn + ")"
            return "(" + safe_fn + " " + " ".join(rendered_args) + ")"

        if fk == "Attribute":
            owner_node = func.get("value")
            owner = _render_expr(ctx, owner_node)
            attr = _safe(_gs(func, "attr"), "method")
            raw_attr = _gs(func, "attr")
            owner_name = ""
            owner_type = ""
            if isinstance(owner_node, dict):
                if _gs(owner_node, "kind") == "Name":
                    owner_name = _gs(owner_node, "id")
                owner_type = _gs(owner_node, "resolved_type")
            runtime_call = _gs(expr, "runtime_call")
            resolved_runtime_call = _gs(expr, "resolved_runtime_call")
            runtime_symbol = _gs(expr, "runtime_symbol")
            runtime_module_id = _gs(expr, "runtime_module_id")
            runtime_keys_attr: list[str] = []
            if runtime_call != "":
                runtime_keys_attr.append(runtime_call)
            if resolved_runtime_call != "":
                runtime_keys_attr.append(resolved_runtime_call)
            if runtime_module_id != "" and runtime_symbol != "":
                runtime_keys_attr.append(runtime_module_id + "." + runtime_symbol)
            if owner_type != "":
                runtime_keys_attr.append(owner_type + "." + raw_attr)
                if "dict[" in owner_type:
                    runtime_keys_attr.append("dict." + raw_attr)
                if "list[" in owner_type:
                    runtime_keys_attr.append("list." + raw_attr)
                if "set[" in owner_type:
                    runtime_keys_attr.append("set." + raw_attr)
            mapped_runtime_attr = ""
            for key in runtime_keys_attr:
                maybe = ctx.mapping.calls.get(key, "")
                if maybe != "":
                    mapped_runtime_attr = maybe
                    break
            if mapped_runtime_attr != "":
                if owner_name in ctx.import_alias_map:
                    if mapped_runtime_attr.startswith("[Math]::"):
                        if mapped_runtime_attr.endswith("::PI") or mapped_runtime_attr.endswith("::E"):
                            return "(" + mapped_runtime_attr + ")"
                        return "(" + mapped_runtime_attr + "(" + ", ".join(rendered_args) + "))"
                    if len(rendered_args) == 0:
                        return "(" + mapped_runtime_attr + ")"
                    return "(" + mapped_runtime_attr + " " + " ".join(rendered_args) + ")"
                if mapped_runtime_attr.startswith("__pytra_str_"):
                    if len(rendered_args) == 0:
                        return "(" + mapped_runtime_attr + " " + owner + ")"
                    return "(" + mapped_runtime_attr + " " + owner + " " + " ".join(rendered_args) + ")"
                if mapped_runtime_attr == "__LIST_APPEND__":
                    if len(rendered_args) > 0:
                        return owner + ".Add(" + rendered_args[0] + ")"
                    return owner
                if mapped_runtime_attr == "__LIST_POP__":
                    if len(rendered_args) == 0:
                        return "(__pytra_list_pop " + owner + ")"
                    return "(__pytra_list_pop " + owner + " " + rendered_args[0] + ")"
                if mapped_runtime_attr == "__LIST_CLEAR__":
                    return "(__pytra_list_clear " + owner + ")"
                if mapped_runtime_attr == "__DICT_GET__":
                    if len(rendered_args) >= 2:
                        return "$(if (" + owner + ".Contains(" + rendered_args[0] + ")) { " + owner + "[" + rendered_args[0] + "] } else { " + rendered_args[1] + " })"
                    if len(rendered_args) == 1:
                        return owner + "[" + rendered_args[0] + "]"
                    return "$null"
                if mapped_runtime_attr == "__DICT_KEYS__":
                    return owner + ".Keys"
                if mapped_runtime_attr == "__DICT_VALUES__":
                    return owner + ".Values"
                if mapped_runtime_attr == "__DICT_ITEMS__":
                    return "(@(" + owner + ".GetEnumerator() | ForEach-Object { ,@($_.Key, $_.Value) }))"
                if mapped_runtime_attr == "__SET_ADD__":
                    if len(rendered_args) > 0:
                        return owner + "[(__pytra_set_key " + rendered_args[0] + ")] = $true"
                    return owner
                if mapped_runtime_attr == "__SET_DISCARD__" or mapped_runtime_attr == "__SET_REMOVE__":
                    if len(rendered_args) > 0:
                        return owner + ".Remove(" + rendered_args[0] + ")"
                    return owner
                if mapped_runtime_attr in (
                    "__pytra_list_extend", "__pytra_list_insert", "__pytra_list_remove",
                    "__pytra_list_copy", "__pytra_list_clear", "__pytra_list_sort",
                    "__pytra_list_reverse", "__pytra_list_index",
                    "__pytra_dict_pop", "__pytra_dict_setdefault", "__pytra_dict_update",
                    "__pytra_dict_clear", "__pytra_set_clear", "__pytra_file_write",
                    "__pytra_file_read", "__pytra_file_enter", "__pytra_file_exit",
                ):
                    if len(rendered_args) == 0:
                        return "(" + mapped_runtime_attr + " " + owner + ")"
                    return "(" + mapped_runtime_attr + " " + owner + " " + " ".join(rendered_args) + ")"
                if len(rendered_args) == 0:
                    return "(" + mapped_runtime_attr + " " + owner + ")"
                return "(" + mapped_runtime_attr + " " + owner + " " + " ".join(rendered_args) + ")"

            # Nested module attribute call: mod.sub.func() e.g. os.path.join(...)
            if isinstance(owner_node, dict) and _gs(owner_node, "kind") == "Attribute":
                sub_attr = _gs(owner_node, "attr")
                sub_owner = owner_node.get("value")
                sub_owner_name = _gs(sub_owner, "id") if isinstance(sub_owner, dict) and _gs(sub_owner, "kind") == "Name" else ""
                if sub_owner_name in ctx.import_alias_map:
                    # Try "sub.func" key (e.g. "path.join") then "mod.sub.func" (e.g. "os.path.join")
                    nested_key = sub_attr + "." + raw_attr
                    full_nested_key = sub_owner_name + "." + sub_attr + "." + raw_attr
                    mapped_fn = ctx.mapping.calls.get(nested_key, ctx.mapping.calls.get(full_nested_key, ""))
                    fn_name2 = mapped_fn if mapped_fn != "" else _safe(raw_attr, "_f")
                    if len(rendered_args) == 0:
                        return "(" + fn_name2 + ")"
                    return "(" + fn_name2 + " " + " ".join(rendered_args) + ")"

            # Module attribute call: mod.func()
            if owner_name in ctx.import_alias_map:
                # Look up mapped name from runtime calls (e.g. math.sqrt → __native_sqrt)
                # Try "mod.func" first, then bare "func"
                mod_full_name = ctx.import_alias_map.get(owner_name, owner_name)
                mod_short_name = mod_full_name.rsplit(".", 1)[-1] if "." in mod_full_name else mod_full_name
                qualified_fn_key = mod_short_name + "." + raw_attr
                mapped_fn = ctx.mapping.calls.get(qualified_fn_key, ctx.mapping.calls.get(raw_attr, ""))
                fn_name2 = mapped_fn if mapped_fn != "" else _safe(raw_attr, "_f")
                if mapped_fn != "" and mapped_fn.startswith("[Math]::"):
                    if mapped_fn.endswith("::PI") or mapped_fn.endswith("::E"):
                        return "(" + mapped_fn + ")"
                    return "(" + mapped_fn + "(" + ", ".join(rendered_args) + "))"
                if len(rendered_args) == 0:
                    return "(" + fn_name2 + ")"
                return "(" + fn_name2 + " " + " ".join(rendered_args) + ")"

            # Static / class-level call: ClassName.method(args) where owner is the class type
            if owner_name in ctx.class_names and _gs(owner_node, "resolved_type") == "type":
                static_fn = _safe(owner_name, "_Cls") + "_" + _safe(raw_attr, "_m")
                if len(rendered_args) == 0:
                    return "(" + static_fn + ")"
                return "(" + static_fn + " " + " ".join(rendered_args) + ")"

            # In method body: ClassName.method() → self.method()
            if owner_name in ctx.class_names:
                owner = "$self"

            # super().__init__() → ParentClass $self args
            if isinstance(owner_node, dict) and _gs(owner_node, "kind") == "Call":
                super_func = owner_node.get("func")
                if isinstance(super_func, dict) and _gs(super_func, "id") == "super":
                    cur_cls = ctx.current_class
                    parent_cls = ctx.class_bases.get(cur_cls, "")
                    if parent_cls == "":
                        for cls_name, base_name in ctx.class_bases.items():
                            if base_name != "":
                                parent_cls = base_name
                                break
                    if parent_cls != "":
                        parent_fn = _safe(parent_cls, "_Base")
                        if raw_attr == "__init__":
                            if len(rendered_args) == 0:
                                return "(" + parent_fn + " $self)"
                            return "(" + parent_fn + " $self " + " ".join(rendered_args) + ")"
                        else:
                            method_fn = parent_fn + "_" + _safe(raw_attr, "_m")
                            if len(rendered_args) == 0:
                                return "(" + method_fn + " $self)"
                            return "(" + method_fn + " $self " + " ".join(rendered_args) + ")"

            # os.path.X() → (X args)
            if owner_name == "os_path" or (
                isinstance(owner_node, dict) and _gs(owner_node, "kind") == "Attribute"
                and _gs(owner_node, "attr") == "path"
            ):
                safe_fn3 = _safe(raw_attr, "_f")
                if len(rendered_args) == 0:
                    return "(" + safe_fn3 + ")"
                return "(" + safe_fn3 + " " + " ".join(rendered_args) + ")"

            # Common non-runtime method mappings that remain target-specific
            if raw_attr == "close":
                return owner + ".Close()"
            if raw_attr == "flush":
                return owner + ".Flush()"

            # Dynamic class method dispatch applies only to user-defined classes.
            if (
                owner_name == "self"
                or owner_name in ctx.class_names
                or owner_type in ctx.class_names
            ):
                # Determine if static dispatch is safe.
                # Use static dispatch for:
                #   (a) self.method() within a leaf class (no subclasses), OR
                #   (b) obj.method() where resolved_type is a leaf class.
                # Leaf classes have no subclasses, so no polymorphism is possible and
                # direct FunctionName calls are equivalent to Get-Command dynamic dispatch.
                # Trait/base-class parameters use non-leaf types as owner_type, so they
                # naturally fall through to dynamic dispatch.
                dispatch_cls = ""
                if owner_name == "self" and ctx.current_class in ctx.leaf_classes:
                    dispatch_cls = ctx.current_class
                elif owner_type in ctx.leaf_classes:
                    dispatch_cls = owner_type
                if dispatch_cls:
                    fn = dispatch_cls + "_" + raw_attr
                    if len(rendered_args) == 0:
                        return "(" + fn + " " + owner + ")"
                    return "(" + fn + " " + owner + " " + " ".join(rendered_args) + ")"
                if len(rendered_args) == 0:
                    return '(& (Get-Command ("{0}_{1}" -f ' + owner + '["__type__"], "' + raw_attr + '")) ' + owner + ')'
                return '(& (Get-Command ("{0}_{1}" -f ' + owner + '["__type__"], "' + raw_attr + '")) ' + owner + ' ' + " ".join(rendered_args) + ')'

            if len(rendered_args) == 0:
                return owner + "." + attr + "()"
            return owner + "." + attr + "(" + ", ".join(rendered_args) + ")"

    # Lambda immediate call
    if isinstance(func, dict) and _gs(func, "kind") == "Lambda":
        fn_rendered = _render_expr(ctx, func)
        if len(rendered_args) == 0:
            return "(& " + fn_rendered + ")"
        return "(& " + fn_rendered + " " + " ".join(rendered_args) + ")"

    fn_rendered = _render_expr(ctx, func)
    if len(rendered_args) == 0:
        return fn_rendered
    return fn_rendered + " " + " ".join(rendered_args)


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_body(ctx: EmitContext, body: list[JsonVal], indent: str) -> list[str]:
    lines: list[str] = []
    for stmt in body:
        if isinstance(stmt, dict):
            lines.extend(_emit_stmt(ctx, stmt, indent))
    if len(lines) == 0:
        lines.append(indent + "# pass")
    return lines


def _emit_stmt(ctx: EmitContext, stmt: dict[str, JsonVal], indent: str) -> list[str]:
    kind = _gs(stmt, "kind")
    if kind in ("Assign", "AnnAssign") and _is_type_alias_like_assign(stmt):
        return []

    if kind == "Expr":
        value = stmt.get("value")
        if isinstance(value, dict):
            vk = _gs(value, "kind")
            if vk == "Constant":
                cv = value.get("value")
                if isinstance(cv, str):
                    first_line = cv.split("\n")[0][:80]
                    return [indent + "# " + first_line]
            if vk == "Name":
                raw = _gs(value, "id")
                if raw == "break":
                    return [indent + "break"]
                if raw == "continue":
                    return [indent + "continue"]
                if raw == "pass":
                    return [indent + "# pass"]
        rendered = _render_expr(ctx, value)
        if isinstance(value, dict) and _gs(value, "kind") == "Call":
            fn_node = value.get("func")
            is_print = isinstance(fn_node, dict) and _gs(fn_node, "id") in ("print", "__pytra_print")
            if not is_print:
                return [indent + "[void](" + rendered + ")"]
        return [indent + rendered]

    if kind == "Return":
        value = stmt.get("value")
        if value is not None:
            rendered = _render_expr(ctx, value)
            return [indent + "return ,(" + rendered + ")"]
        return [indent + "return"]

    if kind == "Assign":
        targets = _gl(stmt, "targets")
        if len(targets) == 0:
            t = stmt.get("target")
            if isinstance(t, dict):
                targets = [t]
        val_node = stmt.get("value")
        if _is_extern_value(val_node):
            tname = ""
            if len(targets) == 1 and isinstance(targets[0], dict):
                tname = _gs(targets[0], "id")
            if tname != "":
                return [indent + "$" + _safe(tname, "_v") + " = $__native_" + _safe(tname, "_v")]
            return [indent + "# extern var (no target)"]
        # Track lambda assignments and callable-typed variable assignments
        if isinstance(val_node, dict) and _gs(val_node, "kind") == "Lambda":
            if len(targets) == 1 and isinstance(targets[0], dict) and _gs(targets[0], "kind") == "Name":
                ctx.lambda_vars.add(_gs(targets[0], "id"))
        if len(targets) == 1 and isinstance(targets[0], dict) and _gs(targets[0], "kind") == "Name":
            tgt_rt = _gs(targets[0], "resolved_type")
            if "callable" in tgt_rt.lower():
                ctx.lambda_vars.add(_gs(targets[0], "id"))
        # Tuple unpacking: (a, b) = expr
        if len(targets) == 1 and isinstance(targets[0], dict):
            tk = _gs(targets[0], "kind")
            if tk == "Tuple" or tk == "List":
                elts = _gl(targets[0], "elements")
                if len(elts) == 0:
                    elts = _gl(targets[0], "elts")
                if len(elts) > 0:
                    tmp = "$__tuple_tmp"
                    lines_a: list[str] = [indent + tmp + " = " + _render_expr(ctx, stmt.get("value"))]
                    for idx, elt in enumerate(elts):
                        lines_a.append(indent + _render_expr(ctx, elt) + " = " + tmp + "[" + str(idx) + "]")
                    return lines_a
        value = _render_expr(ctx, stmt.get("value"))
        if len(targets) == 0:
            return [indent + value]
        target = targets[0]
        if isinstance(target, dict):
            if _gs(target, "kind") == "Attribute":
                return [indent + _render_lvalue(ctx, target) + " = " + value]
            if _gs(target, "kind") == "Subscript":
                owner = _render_expr(ctx, target.get("value"))
                index = _render_expr(ctx, target.get("slice"))
                return [indent + owner + "[" + index + "] = " + value]
        lhs = _render_lvalue(ctx, target)
        return [indent + lhs + " = " + value]

    if kind == "AnnAssign":
        target = stmt.get("target")
        value = stmt.get("value")
        if value is None:
            lhs = _render_expr(ctx, target)
            return [indent + lhs + " = $null"]
        if _is_extern_value(value):
            tname = _gs(target, "id") if isinstance(target, dict) else ""
            if tname != "":
                return [indent + "$" + _safe(tname, "_v") + " = $__native_" + _safe(tname, "_v")]
            return [indent + "# extern var (no target)"]
        if isinstance(value, dict) and _gs(value, "kind") == "Lambda":
            if isinstance(target, dict) and _gs(target, "kind") == "Name":
                ctx.lambda_vars.add(_gs(target, "id"))
        if isinstance(target, dict) and _gs(target, "kind") == "Name":
            tgt_rt_ann = _gs(target, "resolved_type")
            if "callable" in tgt_rt_ann.lower():
                ctx.lambda_vars.add(_gs(target, "id"))
        lhs = _render_expr(ctx, target)
        return [indent + lhs + " = " + _render_expr(ctx, value)]

    if kind == "TupleUnpack":
        # EAST3 lowered tuple unpack: individual_temps style
        targets = _gl(stmt, "targets")
        value = stmt.get("value")
        if len(targets) == 0:
            return [indent + "# tuple unpack (no targets)"]
        tmp = "$__unpack_tmp"
        lines_b: list[str] = [indent + tmp + " = " + _render_expr(ctx, value)]
        for idx, tgt in enumerate(targets):
            if isinstance(tgt, dict):
                lhs = _render_lvalue(ctx, tgt)
                lines_b.append(indent + lhs + " = " + tmp + "[" + str(idx) + "]")
        return lines_b

    if kind == "AugAssign":
        target = _render_lvalue(ctx, stmt.get("target"))
        op = _gs(stmt, "op")
        value = _render_expr(ctx, stmt.get("value"))
        op_map: dict[str, str] = {
            "Add": "+=", "Sub": "-=", "Mult": "*=", "Div": "/=", "Mod": "%=",
        }
        if op in op_map:
            return [indent + target + " " + op_map[op] + " " + value]
        if op in _BINOP_MAP:
            return [indent + target + " = (" + target + " " + _BINOP_MAP[op] + " " + value + ")"]
        if op == "Pow":
            return [indent + target + " = [Math]::Pow(" + target + ", " + value + ")"]
        if op == "FloorDiv":
            return [indent + target + " = ([long][Math]::Floor([double](" + target + ") / [double](" + value + ")))"]
        return [indent + target + " = " + value]

    if kind == "Swap":
        # Use _render_lvalue so subscript targets are valid PS1 assignment targets.
        # PS1 supports $arr[$i] as both lvalue and rvalue (including negative indexes).
        left_lv = _render_lvalue(ctx, stmt.get("left"))
        right_lv = _render_lvalue(ctx, stmt.get("right"))
        tmp = "$__swap_tmp"
        return [
            indent + tmp + " = " + left_lv,
            indent + left_lv + " = " + right_lv,
            indent + right_lv + " = " + tmp,
        ]

    if kind == "If":
        test = _render_expr(ctx, stmt.get("test"))
        body = _gl(stmt, "body")
        orelse = _gl(stmt, "orelse")
        lines_c: list[str] = [indent + "if (" + test + ") {"]
        lines_c.extend(_emit_body(ctx, body, indent + "    "))
        if len(orelse) > 0:
            if len(orelse) == 1 and isinstance(orelse[0], dict) and _gs(orelse[0], "kind") == "If":
                inner = orelse[0]
                lines_c.append(indent + "} elseif (" + _render_expr(ctx, inner.get("test")) + ") {")
                lines_c.extend(_emit_body(ctx, _gl(inner, "body"), indent + "    "))
                inner_else = _gl(inner, "orelse")
                while len(inner_else) == 1 and isinstance(inner_else[0], dict) and _gs(inner_else[0], "kind") == "If":
                    inner = inner_else[0]
                    lines_c.append(indent + "} elseif (" + _render_expr(ctx, inner.get("test")) + ") {")
                    lines_c.extend(_emit_body(ctx, _gl(inner, "body"), indent + "    "))
                    inner_else = _gl(inner, "orelse")
                if len(inner_else) > 0:
                    lines_c.append(indent + "} else {")
                    lines_c.extend(_emit_body(ctx, inner_else, indent + "    "))
            else:
                lines_c.append(indent + "} else {")
                lines_c.extend(_emit_body(ctx, orelse, indent + "    "))
        lines_c.append(indent + "}")
        return lines_c

    if kind == "While":
        test = _render_expr(ctx, stmt.get("test"))
        body = _gl(stmt, "body")
        lines_d: list[str] = [indent + "while (" + test + ") {"]
        lines_d.extend(_emit_body(ctx, body, indent + "    "))
        lines_d.append(indent + "}")
        return lines_d

    if kind == "ForCore":
        body = _gl(stmt, "body")
        target_plan = stmt.get("target_plan")
        iter_plan = stmt.get("iter_plan")

        loop_var = "$_i"
        if isinstance(target_plan, dict):
            tp_id = _gs(target_plan, "id")
            if tp_id != "":
                loop_var = "$" + _safe(tp_id, "_i")

        # RuntimeIterForPlan: foreach ($item in collection) { ... }
        if isinstance(iter_plan, dict) and _gs(iter_plan, "kind") == "RuntimeIterForPlan":
            iter_expr = iter_plan.get("iter_expr")
            iter_rendered = _render_expr(ctx, iter_expr)
            if isinstance(iter_expr, dict) and _gs(iter_expr, "resolved_type") == "str":
                iter_rendered = iter_rendered + ".ToCharArray()"
            if isinstance(iter_expr, dict):
                rt = _gs(iter_expr, "resolved_type")
                if rt.startswith("set[") or rt == "set":
                    iter_rendered = iter_rendered + ".Keys"
            # Use loop_var for foreach; body handles tuple unpacking via Assign stmts
            lines_f: list[str] = [indent + "foreach (" + loop_var + " in " + iter_rendered + ") {"]
            lines_f.extend(_emit_body(ctx, body, indent + "    "))
            lines_f.append(indent + "}")
            return lines_f

        # StaticRangeForPlan: for ($i = start; $i -lt stop; $i += step) { ... }
        if isinstance(iter_plan, dict) and _gs(iter_plan, "kind") == "StaticRangeForPlan":
            start = _render_expr(ctx, iter_plan.get("start"))
            stop = _render_expr(ctx, iter_plan.get("stop"))
            step = iter_plan.get("step")
            step_val = 1
            if isinstance(step, dict):
                sk = _gs(step, "kind")
                if sk == "Constant":
                    sv = step.get("value")
                    step_val = sv if isinstance(sv, int) else 1
                elif sk == "UnaryOp" and _gs(step, "op") == "USub":
                    operand = step.get("operand")
                    if isinstance(operand, dict):
                        ov = operand.get("value")
                        step_val = -(ov if isinstance(ov, int) else 1)
            if step_val >= 0:
                header = indent + "for (" + loop_var + " = " + start + "; " + loop_var + " -lt " + stop + "; " + loop_var + " += " + str(step_val) + ") {"
            else:
                header = indent + "for (" + loop_var + " = " + start + "; " + loop_var + " -gt " + stop + "; " + loop_var + " += " + str(step_val) + ") {"
            lines_g: list[str] = [header]
            lines_g.extend(_emit_body(ctx, body, indent + "    "))
            lines_g.append(indent + "}")
            return lines_g

        # Fallback
        lines_h: list[str] = [indent + "for (" + loop_var + " = 0; $true; " + loop_var + " += 1) {"]
        lines_h.extend(_emit_body(ctx, body, indent + "    "))
        lines_h.append(indent + "}")
        return lines_h

    if kind == "For":
        target = stmt.get("target")
        iter_expr = stmt.get("iter")
        body = _gl(stmt, "body")
        target_str = _render_expr(ctx, target) if target is not None else "$_item"
        iter_str = _render_expr(ctx, iter_expr) if iter_expr is not None else "@()"
        lines_i: list[str] = [indent + "foreach (" + target_str + " in " + iter_str + ") {"]
        lines_i.extend(_emit_body(ctx, body, indent + "    "))
        lines_i.append(indent + "}")
        return lines_i

    if kind == "Try":
        body = _gl(stmt, "body")
        handlers = _gl(stmt, "handlers")
        finalbody = _gl(stmt, "finalbody")
        lines_j: list[str] = [indent + "try {"]
        lines_j.extend(_emit_body(ctx, body, indent + "    "))
        # Collect real handlers (with optional type)
        real_handlers = [h for h in handlers if isinstance(h, dict)]
        if len(real_handlers) > 1:
            # Multiple handlers: combine into a single catch with if/elseif
            lines_j.append(indent + "} catch {")
            lines_j.append(indent + "    $__exc_val = if ($_.TargetObject -is [hashtable]) { $_.TargetObject } else { $_ }")
            lines_j.append(indent + "    $__exc_type = if (Test-Path variable:script:__pytra_exc_type) { $script:__pytra_exc_type } else { \"\" }")
            first = True
            for handler in real_handlers:
                htype_node = handler.get("type")
                htype = _gs(htype_node, "id") if isinstance(htype_node, dict) else ""
                handler_name = _gs(handler, "name")
                handler_body = _gl(handler, "body")
                kw = "if" if first else "} elseif"
                first = False
                if htype != "":
                    lines_j.append(indent + "    " + kw + " ((__pytra_exc_is $__exc_type \"" + htype + "\")) {")
                else:
                    lines_j.append(indent + "    " + kw + " ($true) {")
                if handler_name != "":
                    lines_j.append(indent + "        $" + _safe(handler_name, "e") + " = $__exc_val")
                lines_j.extend(_emit_body(ctx, handler_body, indent + "        "))
            lines_j.append(indent + "    } else { throw }")
        elif len(real_handlers) == 1:
            handler = real_handlers[0]
            handler_name = _gs(handler, "name")
            lines_j.append(indent + "} catch {")
            if handler_name != "":
                lines_j.append(indent + "    $" + _safe(handler_name, "e") + " = if ($_.TargetObject -is [hashtable]) { $_.TargetObject } else { $_ }")
            handler_body = _gl(handler, "body")
            lines_j.extend(_emit_body(ctx, handler_body, indent + "    "))
        elif len(finalbody) == 0:
            lines_j.append(indent + "} catch {")
            lines_j.append(indent + "    # unhandled")
        if len(finalbody) > 0:
            lines_j.append(indent + "} finally {")
            lines_j.extend(_emit_body(ctx, finalbody, indent + "    "))
        lines_j.append(indent + "}")
        return lines_j

    if kind == "Raise":
        exc = stmt.get("exc")
        if exc is not None:
            if isinstance(exc, dict) and _gs(exc, "kind") == "Call":
                exc_func = exc.get("func")
                exc_args = _gl(exc, "args")
                if isinstance(exc_func, dict) and _gs(exc_func, "kind") == "Name":
                    exc_name = _gs(exc_func, "id")
                    set_type = indent + '$script:__pytra_exc_type = "' + exc_name + '"'
                    if exc_name in ctx.class_names:
                        # User-defined class: create object and call constructor
                        rendered_ctor_args = " ".join(["$__exc_obj"] + [_render_expr(ctx, a) for a in exc_args])
                        return [
                            set_type,
                            indent + "$__exc_obj = @{}",
                            indent + "[void](" + exc_name + " " + rendered_ctor_args + ")",
                            indent + "throw $__exc_obj",
                        ]
                    if len(exc_args) > 0:
                        return [set_type, indent + "throw " + _render_expr(ctx, exc_args[0])]
                    return [set_type, indent + "throw " + ps1_string_literal(exc_name)]
            return [indent + "throw " + _render_expr(ctx, exc)]
        return [indent + "throw"]

    if kind == "Pass":
        return [indent + "# pass"]

    if kind == "Break":
        return [indent + "break"]

    if kind == "Continue":
        return [indent + "continue"]

    if kind == "FunctionDef":
        return _emit_function_def(ctx, stmt, indent)

    if kind == "ClosureDef":
        return _emit_function_def(ctx, stmt, indent)

    if kind == "ClassDef":
        return _emit_class_def(ctx, stmt, indent)

    if kind == "ImportFrom":
        module = _gs(stmt, "module")
        if module in _NO_EMIT_IMPORT_MODULES:
            return [indent + "# import: " + module]
        if should_skip_module(module, ctx.mapping):
            native = ctx.mapping.module_native_files.get(module, "")
            if native != "":
                return [indent + '. (Join-Path $PSScriptRoot "' + ctx.root_rel_prefix + native + '")']
            return [indent + "# skip: " + module]
        if module in ("pytra.std", "pytra.utils", "pytra.built_in"):
            sub_lines2: list[str] = []
            seen_natives: set[str] = set()
            for entry in _gl(stmt, "names"):
                if not isinstance(entry, dict):
                    continue
                sub_name = _gs(entry, "name")
                sub_mod = module + "." + sub_name
                if sub_mod in _NO_EMIT_IMPORT_MODULES:
                    continue
                if should_skip_module(sub_mod, ctx.mapping):
                    native = ctx.mapping.module_native_files.get(sub_mod, "")
                    if native != "" and native not in seen_natives:
                        seen_natives.add(native)
                        sub_lines2.append(indent + '. (Join-Path $PSScriptRoot "' + ctx.root_rel_prefix + native + '")')
                    continue
                ps_path = _module_id_to_import_path(sub_mod, ctx.root_rel_prefix)
                sub_lines2.append(indent + '. (Join-Path $PSScriptRoot "' + ps_path + '")')
            return sub_lines2 if len(sub_lines2) > 0 else [indent + "# import: " + module]
        ps_path = _module_id_to_import_path(module, ctx.root_rel_prefix)
        return [indent + '. (Join-Path $PSScriptRoot "' + ps_path + '")']

    if kind == "Import":
        names = _gl(stmt, "names")
        lines_k: list[str] = []
        seen_natives_k: set[str] = set()
        for entry in names:
            if not isinstance(entry, dict):
                continue
            mod_name = _gs(entry, "name")
            if mod_name in _NO_EMIT_IMPORT_MODULES:
                continue
            if should_skip_module(mod_name, ctx.mapping):
                native = ctx.mapping.module_native_files.get(mod_name, "")
                if native != "" and native not in seen_natives_k:
                    seen_natives_k.add(native)
                    lines_k.append(indent + '. (Join-Path $PSScriptRoot "' + ctx.root_rel_prefix + native + '")')
                continue
            ps_path = _module_id_to_import_path(mod_name, ctx.root_rel_prefix)
            if ps_path != "":
                lines_k.append(indent + '. (Join-Path $PSScriptRoot "' + ps_path + '")')
            else:
                lines_k.append(indent + "# import: " + mod_name)
        return lines_k if len(lines_k) > 0 else [indent + "# import"]

    return [indent + "# unsupported: " + kind]


def _emit_function_def(ctx: EmitContext, stmt: dict[str, JsonVal], indent: str) -> list[str]:
    name = _safe(_gs(stmt, "name"), "_fn")
    decs = _gl(stmt, "decorators")
    if "extern" in decs and ctx.current_class == "":
        arg_order = _gl(stmt, "arg_order")
        ps_params = ["$" + _safe(a, "_p") for a in arg_order if isinstance(a, str)]
        lines_l: list[str] = [indent + "function " + name + " {"]
        if len(ps_params) > 0:
            lines_l.append(indent + "    param(" + ", ".join(ps_params) + ")")
        else:
            lines_l.append(indent + "    param()")
        call_args = " " + " ".join(ps_params) if len(ps_params) > 0 else ""
        lines_l.append(indent + "    return (__native_" + name + call_args + ")")
        lines_l.append(indent + "}")
        return lines_l

    body = _gl(stmt, "body")
    arg_order = _gl(stmt, "arg_order")
    arg_defaults = _gd(stmt, "arg_defaults")
    arg_types_raw = _gd(stmt, "arg_types")
    vararg_name = _gs(stmt, "vararg_name")

    # Register callable-typed params as lambda vars
    for aname, atype in arg_types_raw.items():
        if isinstance(aname, str) and isinstance(atype, str) and "callable" in atype.lower():
            ctx.lambda_vars.add(aname)

    ps_params: list[str] = []
    if len(arg_order) > 0:
        for arg_name in arg_order:
            if not isinstance(arg_name, str):
                continue
            if vararg_name != "" and arg_name == vararg_name:
                continue
            safe_a = "$" + _safe(arg_name, "_p")
            default = arg_defaults.get(arg_name)
            if default is not None:
                ps_params.append(safe_a + " = " + _render_expr(ctx, default))
            else:
                ps_params.append(safe_a)
        # Emit vararg params (in arg_types but not arg_order, not "self")
        for extra_name, extra_type in arg_types_raw.items():
            if isinstance(extra_name, str) and extra_name != "self" and extra_name not in arg_order:
                safe_ea = "$" + _safe(extra_name, "_p")
                ps_params.append(safe_ea + " = $null")
        if vararg_name != "":
            ps_params.append("[Parameter(ValueFromRemainingArguments=$true)] [object[]]$" + _safe(vararg_name, "_p"))
    else:
        params = _gl(stmt, "params")
        if len(params) == 0:
            params = _gl(stmt, "args")
        for p in params:
            if isinstance(p, dict):
                arg_name_s = _gs(p, "arg")
                if arg_name_s == "":
                    arg_name_s = _gs(p, "name")
                default = p.get("default")
                if default is not None:
                    ps_params.append("$" + _safe(arg_name_s, "_p") + " = " + _render_expr(ctx, default))
                else:
                    ps_params.append("$" + _safe(arg_name_s, "_p"))
            elif isinstance(p, str):
                ps_params.append("$" + _safe(p, "_p"))

    # Emit decorator comments
    lines_m: list[str] = []
    for dec in _gl(stmt, "decorator_list"):
        if isinstance(dec, dict) and _gs(dec, "kind") == "Name":
            dec_name = _gs(dec, "id")
            if dec_name != "":
                lines_m.append(indent + "# @" + dec_name)

    lines_m.append(indent + "function " + name + " {")
    if len(ps_params) > 0:
        lines_m.append(indent + "    param(" + ", ".join(ps_params) + ")")
    else:
        lines_m.append(indent + "    param()")
    lines_m.extend(_emit_body(ctx, body, indent + "    "))
    lines_m.append(indent + "}")
    return lines_m


def _emit_class_def(ctx: EmitContext, stmt: dict[str, JsonVal], indent: str) -> list[str]:
    name = _safe(_gs(stmt, "name"), "_Cls")
    prev_class = ctx.current_class
    ctx.current_class = name
    body = _gl(stmt, "body")
    lines_n: list[str] = [indent + "# class " + name]

    has_init = False
    for member in body:
        if not isinstance(member, dict):
            continue
        mk = _gs(member, "kind")
        if mk in ("FunctionDef", "ClosureDef"):
            method_name = _gs(member, "name")
            if method_name == "__init__":
                has_init = True
                fn_lines = _emit_function_def(ctx, member, indent)
                if len(fn_lines) > 0:
                    fn_lines[0] = fn_lines[0].replace("function __init__", "function " + name, 1)
                type_assign = indent + '    $self["__type__"] = "' + name + '"'
                for i_fn in range(len(fn_lines)):
                    if "param(" in fn_lines[i_fn]:
                        fn_lines.insert(i_fn + 1, type_assign)
                        break
                for i_fn in range(len(fn_lines) - 1, -1, -1):
                    if fn_lines[i_fn].strip() == "}":
                        fn_lines.insert(i_fn, type_assign)
                        break
                lines_n.extend(fn_lines)
            else:
                fn_lines = _emit_function_def(ctx, member, indent)
                if len(fn_lines) > 0:
                    orig = "function " + _safe(method_name, "_m")
                    new_fn = "function " + name + "_" + _safe(method_name, "_m")
                    fn_lines[0] = fn_lines[0].replace(orig, new_fn, 1)
                lines_n.extend(fn_lines)
        elif mk in ("AnnAssign", "Assign"):
            lines_n.extend(_emit_stmt(ctx, member, indent))
        elif mk == "Pass":
            pass

    # Default constructor if no __init__
    if not has_init:
        field_types = _gd(stmt, "field_types")
        field_defaults = _gd(stmt, "field_defaults")
        field_names: list[str] = []
        for member in body:
            if isinstance(member, dict) and _gs(member, "kind") in ("AnnAssign", "Assign"):
                tgt = member.get("target")
                if isinstance(tgt, dict) and _gs(tgt, "kind") == "Name":
                    fn_id = _gs(tgt, "id")
                    if fn_id != "":
                        field_names.append(fn_id)
        if len(field_names) == 0 and len(field_types) > 0:
            for ft_name in field_types:
                if isinstance(ft_name, str):
                    field_names.append(ft_name)
        field_params: list[str] = ["$self"]
        field_assigns: list[str] = []
        for fn_id in field_names:
            safe_fn = "$" + _safe(fn_id, "_f")
            default_val = field_defaults.get(fn_id)
            if default_val is not None:
                field_params.append(safe_fn + " = " + _render_expr(ctx, default_val))
            else:
                for member in body:
                    if isinstance(member, dict) and _gs(member, "kind") in ("AnnAssign", "Assign"):
                        tgt2 = member.get("target")
                        if isinstance(tgt2, dict) and _gs(tgt2, "id") == fn_id:
                            val = member.get("value")
                            if val is not None:
                                field_params.append(safe_fn + " = " + _render_expr(ctx, val))
                            else:
                                field_params.append(safe_fn)
                            break
                else:
                    field_params.append(safe_fn)
            field_assigns.append(indent + '    $self["' + fn_id + '"] = ' + safe_fn)
        lines_n.append(indent + "function " + name + " {")
        lines_n.append(indent + "    param(" + ", ".join(field_params) + ")")
        for fa in field_assigns:
            lines_n.append(fa)
        lines_n.append(indent + '    $self["__type__"] = "' + name + '"')
        lines_n.append(indent + "}")

    # Inherited method aliases
    base = _gs(stmt, "base")
    if base != "":
        own_methods: set[str] = set()
        for member in body:
            if isinstance(member, dict) and _gs(member, "kind") in ("FunctionDef", "ClosureDef"):
                mn = _gs(member, "name")
                if mn != "" and mn != "__init__":
                    own_methods.add(mn)
        for bm in ctx.class_method_names.get(base, set()):
            if bm not in own_methods:
                base_fn = _safe(base, "_Base") + "_" + _safe(bm, "_m")
                child_fn = name + "_" + _safe(bm, "_m")
                lines_n.append(indent + "function " + child_fn + " { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$__args) " + base_fn + " @__args }")

    ctx.current_class = prev_class
    return lines_n


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

def emit_ps1_module(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a PowerShell source file from an EAST3 document.

    Returns:
        PowerShell source code string, or empty string if module should be skipped.
    """
    if not isinstance(east3_doc, dict) or _gs(east3_doc, "kind") != "Module":
        return ""

    # Load runtime mapping
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "powershell" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Extract module_id
    meta = _gd(east3_doc, "meta")
    module_id = _gs(meta, "module_id")
    emit_ctx_meta = _gd(meta, "emit_context")
    if module_id == "":
        module_id = _gs(emit_ctx_meta, "module_id")

    # Skip if this module is provided by native runtime
    if should_skip_module(module_id, mapping):
        return ""

    root_rel_prefix = _gs(emit_ctx_meta, "root_rel_prefix")

    # Collect renamed symbols
    renamed_raw = east3_doc.get("renamed_symbols")
    renamed: dict[str, str] = {}
    if isinstance(renamed_raw, dict):
        for orig, rn in renamed_raw.items():
            if isinstance(orig, str) and isinstance(rn, str):
                renamed[orig] = rn

    body = _gl(east3_doc, "body")
    main_guard = _gl(east3_doc, "main_guard_body")

    # Collect class names
    class_names: set[str] = set()
    for node in body:
        if isinstance(node, dict) and _gs(node, "kind") == "ClassDef":
            cn = _gs(node, "name")
            if cn != "":
                class_names.add(cn)
    for binding in _gl(meta, "import_bindings"):
        if isinstance(binding, dict):
            local = _gs(binding, "local_name")
            if local != "" and local[0].isupper() and local not in {
                "Any", "Optional", "Union", "List", "Dict", "Tuple", "Set",
                "Callable", "Iterator", "Iterable", "Enum", "IntEnum", "IntFlag",
            }:
                class_names.add(local)
    class_names.update({"JsonValue", "JsonObj", "JsonArr", "Path"})

    class_bases_multi: dict[str, list[str]] = {}
    for node in body:
        if isinstance(node, dict) and _gs(node, "kind") == "ClassDef":
            cn = _gs(node, "name")
            base = _gs(node, "base")
            if cn != "" and base != "":
                class_bases_multi.setdefault(cn, []).append(base)
            for dec in _gl(node, "decorators"):
                if isinstance(dec, str) and dec.startswith("implements(") and dec.endswith(")"):
                    inner = dec[len("implements("):-1]
                    for trait_name in inner.split(","):
                        trait_name = trait_name.strip()
                        if cn != "" and trait_name != "":
                            class_bases_multi.setdefault(cn, []).append(trait_name)
    class_bases: dict[str, str] = {
        child: bases[0]
        for child, bases in class_bases_multi.items()
        if len(bases) > 0
    }

    class_method_names: dict[str, set[str]] = {}
    for node in body:
        if isinstance(node, dict) and _gs(node, "kind") == "ClassDef":
            cn = _gs(node, "name")
            methods: set[str] = set()
            for member in _gl(node, "body"):
                if isinstance(member, dict) and _gs(member, "kind") in ("FunctionDef", "ClosureDef"):
                    mn = _gs(member, "name")
                    if mn != "" and mn != "__init__":
                        methods.add(mn)
            class_method_names[cn] = methods

    class_properties: dict[str, set[str]] = {}
    for node in body:
        if isinstance(node, dict) and _gs(node, "kind") == "ClassDef":
            cn = _gs(node, "name")
            props: set[str] = set()
            for member in _gl(node, "body"):
                if isinstance(member, dict) and _gs(member, "kind") in ("FunctionDef", "ClosureDef"):
                    if "property" in _gl(member, "decorators"):
                        mn = _gs(member, "name")
                        if mn != "":
                            props.add(mn)
            if len(props) > 0:
                class_properties[cn] = props

    # Collect function names
    function_names: set[str] = set()
    for node in body:
        if isinstance(node, dict) and _gs(node, "kind") == "FunctionDef":
            fn = _gs(node, "name")
            if fn != "":
                function_names.add(fn)

    # Collect math import aliases
    import_alias_map = build_import_alias_map(meta)
    import_func_aliases: dict[str, str] = {}
    for node in body:
        if not isinstance(node, dict) or _gs(node, "kind") != "ImportFrom":
            continue
        module = _gs(node, "module")
        for entry in _gl(node, "names"):
            if not isinstance(entry, dict):
                continue
            imported_name = _gs(entry, "name")
            alias = _gs(entry, "asname")
            local_name = alias if alias != "" else imported_name
            # Try "mod_short.func" first (e.g. "json.dumps"), then bare "func" (e.g. "dumps")
            mod_short_ia = module.rsplit(".", 1)[-1] if "." in module else module
            qualified_ia_key = mod_short_ia + "." + imported_name
            mapped_func = mapping.calls.get(qualified_ia_key, mapping.calls.get(imported_name, ""))
            if mapped_func != "":
                import_func_aliases[local_name] = mapped_func

    # Leaf classes: concrete classes that are NOT base of any other class (safe for static dispatch).
    # Trait classes are excluded because they are used for structural/polymorphic dispatch
    # (a variable typed as a trait can hold any implementing class at runtime).
    trait_class_names: set[str] = set()
    for node in body:
        if isinstance(node, dict) and _gs(node, "kind") == "ClassDef":
            cn = _gs(node, "name")
            if cn != "" and "trait" in _gl(node, "decorators"):
                trait_class_names.add(cn)
    base_class_set: set[str] = {base for bases in class_bases_multi.values() for base in bases}
    leaf_classes: set[str] = class_names - base_class_set - trait_class_names

    ctx = EmitContext(
        module_id=module_id,
        root_rel_prefix=root_rel_prefix,
        renamed_symbols=renamed,
        class_names=class_names,
        class_bases=class_bases,
        class_method_names=class_method_names,
        class_properties=class_properties,
        function_names=function_names,
        import_alias_map=import_alias_map,
        import_func_aliases=import_func_aliases,
        mapping=mapping,
        leaf_classes=leaf_classes,
    )

    lines: list[str] = [
        "#Requires -Version 5.1",
        "",
        "$pytra_runtime = Join-Path $PSScriptRoot \"" + root_rel_prefix + "built_in/py_runtime.ps1\"",
        "if (Test-Path $pytra_runtime) { . $pytra_runtime }",
        "",
        "Set-StrictMode -Version Latest",
        "$ErrorActionPreference = \"Stop\"",
        "",
    ]

    # Dot-source native seam for stdlib modules
    if module_id.startswith("pytra."):
        mod_tail = module_id[len("pytra."):]
        native_path = root_rel_prefix + mod_tail.replace(".", "/") + "_native.ps1"
        lines.append('$__native_seam = Join-Path $PSScriptRoot "' + native_path + '"')
        lines.append('if (Test-Path $__native_seam) { . $__native_seam }')
        lines.append("")

    # py_format_value is provided by py_runtime.ps1 — no extra dot-source needed

    # Emit __pytra_bases for isinstance inheritance chain
    if len(class_bases_multi) > 0:
        parts4: list[str] = []
        for child, bases in class_bases_multi.items():
            unique_bases: list[str] = []
            for base in bases:
                if base not in unique_bases:
                    unique_bases.append(base)
            if len(unique_bases) == 1:
                parts4.append('"' + child + '" = "' + unique_bases[0] + '"')
            else:
                parts4.append('"' + child + '" = @(' + ", ".join('"' + base + '"' for base in unique_bases) + ')')
        lines.append("$__pytra_bases = @{" + "; ".join(parts4) + "}")
        lines.append("")

    # Module body
    for node in body:
        if isinstance(node, dict):
            lines.extend(_emit_stmt(ctx, node, ""))
            lines.append("")

    # Main guard
    if len(main_guard) > 0:
        ctx.in_main_guard = True
        for node in main_guard:
            if isinstance(node, dict):
                lines.extend(_emit_stmt(ctx, node, ""))
        ctx.in_main_guard = False
        lines.append("")

    return _postprocess_ps1_native_code("\n".join(lines).rstrip() + "\n")
