"""EAST3 → TypeScript / JavaScript source code emitter.

TypeScript emitter は CommonRenderer + override 構成。
TS/JS 固有のノード（クラス、arrow function、import 等）のみ override として実装する。

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.ts.types import (
    ts_type, ts_zero_value, ts_array_type, _safe_ts_ident, _split_generic_args,
    TS_BUILTIN_RUNTIME_SYMBOLS, TS_BUILTIN_EXCEPTION_NAMES, TS_BUILTIN_EXCEPTION_MAP,
)
from toolchain.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_import_alias_map, build_runtime_import_map,
    resolve_runtime_symbol_name,
)
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.link.expand_defaults import expand_cross_module_defaults


# ---------------------------------------------------------------------------
# Emit context
# ---------------------------------------------------------------------------

@dataclass
class EmitContext:
    """Per-module mutable state during emission."""
    module_id: str = ""
    source_path: str = ""
    is_entry: bool = False
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    strip_types: bool = False
    # Variable types in current scope
    var_types: dict[str, str] = field(default_factory=dict)
    # Current function return type
    current_return_type: str = ""
    # Runtime mapping (from mapping.json)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    # Import alias → module_id map
    import_alias_modules: dict[str, str] = field(default_factory=dict)
    # Imported runtime symbols
    runtime_imports: dict[str, str] = field(default_factory=dict)
    # Class info
    class_names: set[str] = field(default_factory=set)
    class_bases: dict[str, str] = field(default_factory=dict)
    class_static_methods: dict[str, set[str]] = field(default_factory=dict)
    class_property_methods: dict[str, set[str]] = field(default_factory=dict)
    class_instance_methods: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    class_fields: dict[str, dict[str, str]] = field(default_factory=dict)
    enum_bases: dict[str, str] = field(default_factory=dict)
    enum_members: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    # Current class context
    current_class: str = ""
    # Exception type IDs
    exception_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    tid_const_types: dict[str, str] = field(default_factory=dict)
    # Module-level symbol renames (original → renamed), e.g. main → __pytra_main
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    # Per-module temp counter
    temp_counter: int = 0
    # Whether this module is pytra.built_in.type_id_table (exports all vars)
    is_type_id_table: bool = False
    # Current exception variable (set inside catch blocks for bare raise)
    current_exc_var: str = ""
    # Functions that have variadic (*args) parameters
    vararg_functions: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Built-in runtime symbols exported by py_runtime.ts
# ---------------------------------------------------------------------------

# All symbols exported by src/runtime/ts/built_in/py_runtime.ts
_BUILTIN_RUNTIME_SYMBOLS: set[str] = set()
for _builtin_runtime_symbol in TS_BUILTIN_RUNTIME_SYMBOLS:
    _BUILTIN_RUNTIME_SYMBOLS.add(_builtin_runtime_symbol)

_BUILTIN_RUNTIME_MODULE: str = "pytra_built_in_py_runtime"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _indent(ctx: EmitContext) -> str:
    return "    " * ctx.indent_level


def _emit(ctx: EmitContext, line: str) -> None:
    ctx.lines.append(_indent(ctx) + line)


def _emit_blank(ctx: EmitContext) -> None:
    ctx.lines.append("")


def _next_temp(ctx: EmitContext, prefix: str) -> str:
    ctx.temp_counter += 1
    return "__" + prefix + "_" + str(ctx.temp_counter)


def _str(node: dict[str, JsonVal], key: str) -> str:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, str):
            return value
    return ""


def _bool(node: dict[str, JsonVal], key: str) -> bool:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, bool):
            return value
    return False


def _list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, list):
            return value
    return []


def _dict(node: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _ts_symbol_name(ctx: EmitContext, name: str) -> str:
    """Return safe TS identifier, applying renamed_symbols and 'self'→'this'."""
    if name == "self":
        return "this"
    # Strip parentheses from names like "(had_local" or "value)" from tuple syntax
    name = name.strip("() \t")
    renamed = ctx.renamed_symbols.get(name, "")
    if renamed != "":
        return _safe_ts_ident(renamed)
    return _safe_ts_ident(name)


def _type_annotation(ctx: EmitContext, resolved_type: str, *, for_return: bool = False) -> str:
    """Return ': TypeAnnotation' if not in strip_types mode, else ''."""
    if ctx.strip_types:
        return ""
    if resolved_type == "" or resolved_type == "unknown":
        return ""
    tt = ts_type(resolved_type, for_return=for_return)
    if tt == "" or tt == "void" and not for_return:
        return ""
    return ": " + tt


def _return_type_annotation(ctx: EmitContext, return_type: str) -> str:
    """Return ': ReturnType' or '' for strip_types mode."""
    if ctx.strip_types:
        return ""
    if return_type == "" or return_type == "unknown":
        return ""
    tt = ts_type(return_type, for_return=True)
    if tt == "":
        return ""
    return ": " + tt


def _is_top_level_public_name(ctx: EmitContext, name: str) -> bool:
    if ctx.indent_level != 0:
        return False
    if ctx.current_class != "":
        return False
    return not name.startswith("_")


def _is_exception_type_name(ctx: EmitContext, type_name: str) -> bool:
    """Check if a type name is an exception class."""
    if type_name in TS_BUILTIN_EXCEPTION_NAMES:
        return True
    # Check inherited from exception class
    base = ctx.class_bases.get(type_name, "")
    if base != "":
        return _is_exception_type_name(ctx, base)
    return False


def _exception_ctor_expr(type_name: str, message_code: str) -> str:
    """Build a new ExcType(...) expression for exception types."""
    js_cls = _map_builtin_exception(type_name)
    if message_code != "":
        return "new " + js_cls + "(" + message_code + ")"
    return "new " + js_cls + '("' + type_name + '")'


# ---------------------------------------------------------------------------
# Expression rendering (used by CommonRenderer override and standalone)
# ---------------------------------------------------------------------------

def _emit_expr(ctx: EmitContext, node: JsonVal) -> str:
    """Emit an expression and return TS code string."""
    if not isinstance(node, dict):
        return "null"
    renderer = _TsExprRenderer(ctx)
    return renderer.render_expr(node)


def _emit_constant(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        escaped: str = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return '"' + escaped + '"'
    return str(value)


def _emit_name(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "":
        name = _str(node, "repr")
    if name == "None":
        return "null"
    if name == "True":
        return "true"
    if name == "False":
        return "false"
    # Check runtime_imports for mapped names
    if name in ctx.runtime_imports:
        return ctx.runtime_imports[name]
    return _ts_symbol_name(ctx, name)


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr = _str(node, "attr")
    # Handle 'self.field' → 'this.field'
    if isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
        return "this." + attr
    # Handle module constant access (e.g. math.pi, sys.argv)
    if isinstance(owner_node, dict):
        owner_rt = _str(owner_node, "resolved_type")
        owner_id = _str(owner_node, "id")
        is_module = owner_rt == "module" or owner_id in ctx.import_alias_modules
        if is_module:
            mod_id = _str(node, "runtime_module_id")
            if mod_id == "":
                mod_id = ctx.import_alias_modules.get(owner_id, "")
            if should_skip_module(mod_id, ctx.mapping):
                runtime_symbol = _str(node, "runtime_symbol")
                if runtime_symbol == "":
                    runtime_symbol = attr
                # Try module-qualified key first: e.g. "math.pi"
                mod_short = mod_id.rsplit(".", 1)[-1]
                qualified_key = mod_short + "." + runtime_symbol
                if qualified_key in ctx.mapping.calls:
                    return ctx.mapping.calls[qualified_key]
                resolved = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping, module_id=mod_id)
                return resolved
    owner = _emit_expr(ctx, owner_node)
    return owner + "." + attr


def _emit_subscript(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    slice_node = node.get("slice")
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "0"
        upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else "undefined"
        return owner + ".slice(" + lower_code + ", " + upper_code + ")"
    # For dicts/Maps: use .get() instead of []
    is_dict_type = owner_rt.startswith("dict[") or owner_rt == "dict"
    if is_dict_type and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        out = owner + ".get(" + slice_code + ")"
        return out if ctx.strip_types else out + "!"
    # For lists/strings: handle negative constant indices (Python arr[-1] → JS arr[arr.length - 1])
    is_array_like = (owner_rt.startswith("list[") or owner_rt in ("list", "str", "string", "bytes", "bytearray"))
    if is_array_like and isinstance(slice_node, dict):
        neg_val = _get_negative_int_literal(slice_node)
        if neg_val is not None:
            # Preserve Python semantics for negative constant indices:
            # normalize once, then raise if still out of range.
            idx_expr = "__owner.length + (" + str(neg_val) + ")"
            return (
                "((__owner) => { const __idx = "
                + idx_expr
                + "; if (__idx < 0 || __idx >= __owner.length) { throw new RangeError(\"index out of range\"); } "
                + "return __owner[__idx]; })("
                + owner
                + ")"
            )
    slice_code = _emit_expr(ctx, slice_node)
    out = owner + "[" + slice_code + "]"
    is_tuple_like = owner_rt.startswith("tuple[") or owner_rt == "tuple"
    if not ctx.strip_types and (is_array_like or is_tuple_like):
        return out + "!"
    return out


def _get_negative_int_literal(node: dict[str, JsonVal]) -> int | None:
    """If node is a negative integer literal, return the negative value; else None."""
    kind = _str(node, "kind")
    if kind == "Constant":
        v = node.get("value")
        if isinstance(v, int) and v < 0:
            return v
    if kind == "UnaryOp" and _str(node, "op") == "USub":
        operand = node.get("operand")
        if isinstance(operand, dict) and _str(operand, "kind") == "Constant":
            v = operand.get("value")
            if isinstance(v, int) and v > 0:
                return -v
    return None


def _emit_list_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    rt = _str(node, "resolved_type")
    elem_type = ""
    if rt.startswith("list[") and rt.endswith("]"):
        elem_type = rt[5:-1]
    if ctx.strip_types or elem_type == "":
        return "[" + ", ".join(elem_strs) + "]"
    ts_elem = ts_type(elem_type)
    return "<" + ts_array_type(ts_elem) + ">[" + ", ".join(elem_strs) + "]"


def _emit_dict_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    pairs: list[str] = []
    value_rts: set[str] = set()
    # EAST3 Dict node uses "entries": [{key, value}, ...] format
    entries = _list(node, "entries")
    if len(entries) > 0:
        for entry in entries:
            if isinstance(entry, dict):
                kc = _emit_expr(ctx, entry.get("key"))
                val_node = entry.get("value")
                vc = _emit_expr(ctx, val_node)
                if isinstance(val_node, dict):
                    vrt = _str(val_node, "resolved_type")
                    if vrt:
                        value_rts.add(vrt)
                pairs.append("[" + kc + ", " + vc + "]")
    else:
        # Fallback: old keys/values format
        keys = _list(node, "keys")
        values = _list(node, "values")
        for idx, key in enumerate(keys):
            kc = _emit_expr(ctx, key)
            val_node = values[idx] if idx < len(values) else None
            vc = _emit_expr(ctx, val_node) if val_node is not None else "null"
            if isinstance(val_node, dict):
                vrt = _str(val_node, "resolved_type")
                if vrt:
                    value_rts.add(vrt)
            pairs.append("[" + kc + ", " + vc + "]")
    if ctx.strip_types or rt == "":
        return "new Map([" + ", ".join(pairs) + "])"
    k_type = "any"
    v_type = "any"
    if rt.startswith("dict[") and rt.endswith("]"):
        parts = _split_generic_args(rt[5:-1])
        if len(parts) == 2:
            k_type = ts_type(parts[0])
            v_type = ts_type(parts[1])
    # If values have heterogeneous types, widen to any
    if len(value_rts) > 1 or "Any" in value_rts or "unknown" in value_rts or "any" in value_rts:
        v_type = "any"
    return "new Map<" + k_type + ", " + v_type + ">([" + ", ".join(pairs) + "])"


def _emit_set_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    rt = _str(node, "resolved_type")
    if ctx.strip_types or rt == "":
        return "new Set([" + ", ".join(elem_strs) + "])"
    elem_type = "any"
    if rt.startswith("set[") and rt.endswith("]"):
        elem_type = ts_type(rt[4:-1])
    return "new Set<" + elem_type + ">([" + ", ".join(elem_strs) + "])"


def _emit_tuple_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    return "pyTuple(" + ", ".join(elem_strs) + ")"


def _emit_binding_pattern(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return "_item"
    kind = _str(node, "kind")
    if kind in ("Name", "NameTarget"):
        name = _str(node, "id")
        if name == "":
            name = _str(node, "repr")
        return _safe_ts_ident(name) if name != "" else "_item"
    if kind == "Tuple":
        items = _list(node, "elements")
        return "[" + ", ".join(_emit_binding_pattern(item) for item in items) + "]"
    return "_item"


def _ts_condition_expr(ctx: EmitContext, node: JsonVal) -> str:
    """Emit a condition expression, handling array/dict truthiness for TypeScript."""
    rendered = _emit_expr(ctx, node)
    if isinstance(node, dict):
        rt = _str(node, "resolved_type")
        is_sequence = rt in ("bytes", "bytearray")
        if not is_sequence:
            is_sequence = rt.startswith("list[") or rt == "list"
        if not is_sequence:
            is_sequence = rt.startswith("tuple[") or rt == "tuple"
        if is_sequence:
            return rendered + ".length > 0"
        is_mapping = rt.startswith("dict[") or rt == "dict"
        if not is_mapping:
            is_mapping = rt.startswith("set[") or rt == "set"
        if is_mapping:
            return rendered + ".size > 0"
    return rendered


def _emit_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test = _ts_condition_expr(ctx, node.get("test"))
    body = _emit_expr(ctx, node.get("body"))
    orelse = _emit_expr(ctx, node.get("orelse"))
    return "(" + test + " ? " + body + " : " + orelse + ")"


def _emit_fstring(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    parts: list[str] = []
    for v in values:
        if not isinstance(v, dict):
            continue
        vk = _str(v, "kind")
        if vk == "Constant":
            raw_val = v.get("value")
            if isinstance(raw_val, str):
                # Escape template literal
                escaped = raw_val.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                parts.append(escaped)
            continue
        if vk == "FormattedValue":
            inner = v.get("value")
            expr_code = _emit_expr(ctx, inner)
            fmt_spec = _str(v, "format_spec")
            if fmt_spec != "":
                escaped_spec = fmt_spec.replace("\\", "\\\\").replace('"', '\\"')
                parts.append("${" + "pyFmt(" + expr_code + ', "' + escaped_spec + '")' + "}")
            else:
                parts.append("${" + expr_code + "}")
            continue
        expr_code = _emit_expr(ctx, v)
        parts.append("${" + expr_code + "}")
    return "`" + "".join(parts) + "`"


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    arg_order = _list(node, "arg_order")
    arg_types = _dict(node, "arg_types")
    body = node.get("body")
    params: list[str] = []
    for a in arg_order:
        a_str = a if isinstance(a, str) else ""
        if ctx.strip_types:
            params.append(_safe_ts_ident(a_str))
        else:
            a_type = arg_types.get(a_str, "")
            a_type_str = a_type if isinstance(a_type, str) else ""
            ann = _type_annotation(ctx, a_type_str)
            params.append(_safe_ts_ident(a_str) + ann)
    body_code = _emit_expr(ctx, body)
    return "(" + ", ".join(params) + ") => " + body_code


_POD_NUMERIC_TYPES_VALUES: set[str] = set()
for _pod_numeric_type in [
    "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
    "float32", "float64", "int", "float", "number", "byte",
]:
    _POD_NUMERIC_TYPES_VALUES.add(_pod_numeric_type)
_POD_NUMERIC_TYPES: frozenset[str] = frozenset(_POD_NUMERIC_TYPES_VALUES)


def _isinstance_ts_check(obj: str, obj_rt: str, type_name: str) -> str:
    """Return a TypeScript expression for isinstance(obj, type_name)."""
    # dict / PYTRA_TID_DICT → obj instanceof Map
    if type_name in ("PYTRA_TID_DICT", "dict"):
        return "(" + obj + " instanceof Map)"
    # list / PYTRA_TID_LIST → Array.isArray(obj)
    if type_name in ("PYTRA_TID_LIST", "list"):
        return "(Array.isArray(" + obj + "))"
    # set / PYTRA_TID_SET → obj instanceof Set
    if type_name in ("PYTRA_TID_SET", "set", "frozenset"):
        return "(" + obj + " instanceof Set)"
    # str / PYTRA_TID_STR → typeof obj === 'string'
    if type_name in ("PYTRA_TID_STR", "str", "string", "char"):
        return "(typeof " + obj + " === 'string')"
    # POD numeric types: compare EAST3 resolved_type with expected type
    if type_name in _POD_NUMERIC_TYPES:
        if obj_rt in _POD_NUMERIC_TYPES:
            # Statically known: same type → true, different → false
            return "true" if obj_rt == type_name else "false"
        return "(typeof " + obj + " === 'number')"
    # Default: instanceof (for user-defined classes etc.)
    return "(" + obj + " instanceof " + _safe_ts_ident(type_name) + ")"


def _emit_isinstance(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    obj_node = node.get("value")
    obj = _emit_expr(ctx, obj_node)
    obj_rt = _str(obj_node, "resolved_type") if isinstance(obj_node, dict) else ""
    # EAST3 IsInstance uses expected_type_id node with type_object_of/id for class name
    type_name = _str(node, "type_name")
    if type_name == "":
        type_name = _str(node, "expected_type_name")
    if type_name == "":
        expected_type_id = node.get("expected_type_id")
        if isinstance(expected_type_id, dict):
            type_name = _str(expected_type_id, "type_object_of")
            if type_name == "":
                type_name = _str(expected_type_id, "id")
    if type_name == "":
        type_names = _list(node, "type_names")
        if len(type_names) > 0:
            checks: list[str] = []
            for tn in type_names:
                tn_str = tn if isinstance(tn, str) else ""
                checks.append(_isinstance_ts_check(obj, obj_rt, tn_str))
            return "(" + " || ".join(checks) + ")"
    methods: list[str] = []
    current_trait = type_name
    while current_trait != "":
        for method_name in ctx.class_instance_methods.get(current_trait, {}).keys():
            if method_name != "__init__" and method_name not in methods:
                methods.append(method_name)
        current_trait = ctx.class_bases.get(current_trait, "")
    if len(methods) > 0:
        checks = ["(" + obj + " != null)"]
        for method_name in methods:
            checks.append("(typeof (" + obj + " as any)." + _safe_ts_ident(method_name) + " === 'function')" if not ctx.strip_types else "(typeof " + obj + "." + _safe_ts_ident(method_name) + " === 'function')")
        return "(" + " && ".join(checks) + ")"
    return _isinstance_ts_check(obj, obj_rt, type_name)


def _tid_const_name(fqcn: str) -> str:
    dotted = fqcn.replace(".", "_")
    chars: list[str] = []
    prev_is_lower = False
    for ch in dotted:
        is_upper = "A" <= ch and ch <= "Z"
        is_lower = "a" <= ch and ch <= "z"
        if is_upper and prev_is_lower:
            chars.append("_")
        chars.append(ch.upper())
        prev_is_lower = is_lower
    result = "".join(chars) + "_TID"
    if result != "" and result[0].isdigit():
        result = "_" + result
    return result


def _emit_linked_type_id_isinstance(ctx: EmitContext, args: list[JsonVal]) -> str | None:
    if len(args) != 2:
        return None
    type_id_arg = args[0]
    expected_arg = args[1]
    if not isinstance(type_id_arg, dict) or _str(type_id_arg, "kind") != "ObjTypeId":
        return None
    if not isinstance(expected_arg, dict) or _str(expected_arg, "kind") != "Name":
        return None
    expected_const = _str(expected_arg, "id")
    type_name = ctx.tid_const_types.get(expected_const, "")
    if type_name == "":
        return None
    value_node = type_id_arg.get("value")
    obj = _emit_expr(ctx, value_node)
    obj_rt = _str(value_node, "resolved_type") if isinstance(value_node, dict) else ""
    return _isinstance_ts_check(obj, obj_rt, type_name)


def _emit_unbox(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    return _emit_expr(ctx, node.get("value"))


def _emit_box(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    return _emit_expr(ctx, node.get("value"))


def _is_module_call(ctx: EmitContext, owner_node: JsonVal) -> bool:
    """Check if owner is a module reference."""
    if not isinstance(owner_node, dict):
        return False
    rt = _str(owner_node, "resolved_type")
    owner_id = _str(owner_node, "id")
    return rt == "module" or owner_id in ctx.import_alias_modules


def _resolve_runtime_call_name(ctx: EmitContext, node: dict[str, JsonVal], func: JsonVal) -> str:
    """Resolve a runtime_call to the mapped TS function name."""
    runtime_call = _str(node, "runtime_call")
    resolved_runtime_call = _str(node, "resolved_runtime_call")
    adapter_kind = _str(node, "runtime_call_adapter_kind")
    builtin_name = _str(node, "builtin_name")
    if builtin_name == "" and isinstance(func, dict):
        builtin_name = _str(func, "builtin_name")
    if runtime_call == "" and resolved_runtime_call != "":
        runtime_call = resolved_runtime_call
    if runtime_call == "" and isinstance(func, dict):
        runtime_call = _str(func, "runtime_call")
    name = resolve_runtime_call(runtime_call, builtin_name, adapter_kind, ctx.mapping)
    if name == "" and "." not in runtime_call:
        name = runtime_call
    return name


def _owner_runtime_mapping_key(owner_rt: str, attr: str) -> str:
    rt = owner_rt
    if rt.startswith("list[") or "list[" in rt:
        return "list." + attr
    if rt in ("list", "bytes", "bytearray"):
        return "list." + attr if rt == "list" else rt + "." + attr
    if rt.startswith("dict[") or "dict[" in rt or rt == "dict":
        return "dict." + attr
    if rt.startswith("set[") or "set[" in rt or rt == "set":
        return "set." + attr
    if rt in ("str", "string"):
        return "str." + attr
    return ""


def _expand_owner_mapped_call(ctx: EmitContext, mapped: str, owner_code: str, arg_strs: list[str]) -> str:
    if mapped == "__LIST_APPEND__" and len(arg_strs) >= 1:
        return owner_code + ".push(" + arg_strs[0] + ")"
    if mapped == "__LIST_POP__":
        if len(arg_strs) >= 1:
            return owner_code + ".splice(" + arg_strs[0] + ", 1)[0]"
        return owner_code + ".pop()!" if not ctx.strip_types else owner_code + ".pop()"
    if mapped == "__LIST_CLEAR__":
        return owner_code + ".splice(0)"
    if mapped == "__LIST_COPY__":
        return owner_code + ".slice()"
    if mapped == "__LIST_INDEX__" and len(arg_strs) >= 1:
        return owner_code + ".indexOf(" + arg_strs[0] + ")"
    if mapped == "__LIST_COUNT__" and len(arg_strs) >= 1:
        return owner_code + ".filter((__item) => __item === " + arg_strs[0] + ").length"
    if mapped == "__LIST_REVERSE__":
        return owner_code + ".reverse()"
    if mapped == "__LIST_SORT__":
        return owner_code + ".sort()"
    if mapped == "__LIST_INSERT__" and len(arg_strs) >= 2:
        return owner_code + ".splice(" + arg_strs[0] + ", 0, " + arg_strs[1] + ")"
    if mapped == "__LIST_REMOVE__" and len(arg_strs) >= 1:
        return owner_code + ".splice(" + owner_code + ".indexOf(" + arg_strs[0] + "), 1)"
    if mapped == "__LIST_EXTEND__" and len(arg_strs) >= 1:
        return "pyextend(" + owner_code + ", " + arg_strs[0] + ")"
    if mapped == "__DICT_GET__":
        if len(arg_strs) >= 2:
            return "(" + owner_code + ".get(" + arg_strs[0] + ") ?? " + arg_strs[1] + ")"
        if len(arg_strs) >= 1:
            return owner_code + ".get(" + arg_strs[0] + ")"
    if mapped == "__DICT_ITEMS__":
        return owner_code + ".entries()"
    if mapped == "__DICT_KEYS__":
        return "Array.from(" + owner_code + ".keys())"
    if mapped == "__DICT_VALUES__":
        return "Array.from(" + owner_code + ".values())"
    if mapped == "__DICT_CLEAR__":
        return owner_code + ".clear()"
    if mapped == "__DICT_POP__" and len(arg_strs) >= 1:
        return "pypop(" + owner_code + ", " + arg_strs[0] + ")"
    if mapped == "__DICT_SETDEFAULT__" and len(arg_strs) >= 2:
        return "pysetdefault(" + owner_code + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
    if mapped == "__DICT_UPDATE__" and len(arg_strs) >= 1:
        return "pyupdate(" + owner_code + ", " + arg_strs[0] + ")"
    if mapped == "__SET_ADD__" and len(arg_strs) >= 1:
        return owner_code + ".add(" + arg_strs[0] + ")"
    if mapped == "__SET_DISCARD__" and len(arg_strs) >= 1:
        return owner_code + ".delete(" + arg_strs[0] + ")"
    if mapped == "__SET_REMOVE__" and len(arg_strs) >= 1:
        return owner_code + ".delete(" + arg_strs[0] + ")"
    if mapped == "__SET_CLEAR__":
        return owner_code + ".clear()"
    if mapped.startswith("pyStr"):
        mapped_safe = mapped if "." in mapped else _safe_ts_ident(mapped)
        return mapped_safe + "(" + ", ".join([owner_code] + arg_strs) + ")"
    return ""


def _is_float_type(rt: str) -> bool:
    return rt in ("float", "float32", "float64")


def _wrap_pyprint_arg(a_str: str, a_node: JsonVal) -> str:
    """Wrap a pyPrint argument with pyFloatStr or float-list formatter as needed."""
    if not isinstance(a_node, dict):
        return a_str
    rt = _str(a_node, "resolved_type")
    if _is_float_type(rt):
        return "pyFloatStr(" + a_str + ")"
    # list[float] → format each element
    if rt.startswith("list[") and rt.endswith("]") and _is_float_type(rt[5:-1]):
        return '"[" + ' + a_str + '.map(pyFloatStr).join(", ") + "]"'
    return a_str


def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    func = node.get("func")
    args = _list(node, "args")
    keywords = _list(node, "keywords")
    arg_strs = [_emit_expr(ctx, a) for a in args]
    kw_strs: list[str] = []
    for kw in keywords:
        if isinstance(kw, dict):
            kw_strs.append(_emit_expr(ctx, kw.get("value")))
    # Handle vararg spread: if calling a known vararg function and the last arg is a List literal,
    # expand the list elements inline (pass each element individually as spread args).
    fn_id_for_vararg = ""
    if isinstance(func, dict) and _str(func, "kind") == "Name":
        fn_id_for_vararg = _str(func, "id")
    has_vararg_list = fn_id_for_vararg in ctx.vararg_functions
    if has_vararg_list:
        has_vararg_list = len(args) > 0
    if has_vararg_list:
        has_vararg_list = isinstance(args[-1], dict)
    if has_vararg_list:
        has_vararg_list = _str(args[-1], "kind") == "List"
    if has_vararg_list:
        vararg_list_node = args[-1]
        elems = _list(vararg_list_node, "elements")
        elem_strs = [_emit_expr(ctx, e) for e in elems]
        arg_strs = arg_strs[:-1] + elem_strs
    all_arg_strs = arg_strs + kw_strs

    # BuiltinCall: runtime function
    lowered = _str(node, "lowered_kind")
    if lowered == "BuiltinCall" or lowered == "RuntimeCall":
        semantic_tag = _str(node, "semantic_tag")
        # When func is Attribute (e.g., checks.append), prepend owner to args
        method_owner = ""
        builtin_arg_strs = list(all_arg_strs)
        if isinstance(func, dict) and _str(func, "kind") == "Attribute":
            owner_val = func.get("value")
            method_owner = _emit_expr(ctx, owner_val)
            builtin_arg_strs = [method_owner] + list(arg_strs)

        if semantic_tag == "core.list_ctor":
            rt = _str(node, "resolved_type")
            if len(all_arg_strs) >= 1:
                return "Array.from(" + all_arg_strs[0] + ")"
            if not ctx.strip_types and rt.startswith("list[") and rt.endswith("]"):
                elem_type = ts_type(rt[5:-1])
                return "<" + ts_array_type(elem_type) + ">[]"
            return "[]"
        if semantic_tag == "core.set_ctor":
            rt = _str(node, "resolved_type")
            if not ctx.strip_types and rt.startswith("set[") and rt.endswith("]"):
                elem_type = ts_type(rt[4:-1])
                return "new Set<" + elem_type + ">([" + ", ".join(all_arg_strs) + "])"
            return "new Set([" + ", ".join(all_arg_strs) + "])"
        if semantic_tag == "error.raise_ctor":
            exc_name = _str(node, "runtime_symbol")
            if exc_name == "" and isinstance(func, dict):
                exc_name = _str(func, "id")
            msg = all_arg_strs[0] if len(all_arg_strs) >= 1 else ('"' + (exc_name or "RuntimeError") + '"')
            if exc_name == "":
                exc_name = "RuntimeError"
            return _exception_ctor_expr(exc_name, msg)

        fn_name = _resolve_runtime_call_name(ctx, node, func)
        if fn_name != "" and fn_name != "__CAST__" and fn_name != "__PANIC__":
            if fn_name == "__LIST_CTOR__":
                rt = _str(node, "resolved_type")
                # list(iterable) → Array.from(iterable)
                if len(all_arg_strs) >= 1:
                    return "Array.from(" + all_arg_strs[0] + ")"
                if not ctx.strip_types and rt.startswith("list[") and rt.endswith("]"):
                    elem_type = ts_type(rt[5:-1])
                    return "<" + ts_array_type(elem_type) + ">[]"
                return "[]"
            if fn_name == "__TUPLE_CTOR__":
                return "pyTuple(" + ", ".join(all_arg_strs) + ")"
            if fn_name == "__SET_CTOR__":
                rt = _str(node, "resolved_type")
                if not ctx.strip_types and rt.startswith("set[") and rt.endswith("]"):
                    elem_type = ts_type(rt[4:-1])
                    return "new Set<" + elem_type + ">([" + ", ".join(all_arg_strs) + "])"
                return "new Set([" + ", ".join(all_arg_strs) + "])"
            if fn_name == "__LIST_APPEND__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                if not ctx.strip_types:
                    item = "(" + item + " as any)"
                return owner + ".push(" + item + ")"
            if fn_name == "__LIST_POP__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                if len(builtin_arg_strs) >= 2:
                    return owner + ".splice(" + builtin_arg_strs[1] + ", 1)[0]"
                return owner + ".pop()!" if not ctx.strip_types else owner + ".pop()"
            if fn_name == "__LIST_CLEAR__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + ".splice(0)"
            if fn_name == "__LIST_INDEX__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return owner + ".indexOf(" + item + ")"
            if fn_name == "__LIST_EXTEND__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                values = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "[]"
                return "pyextend(" + owner + ", " + values + ")"
            if fn_name == "__LIST_SORT__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + ".sort()"
            if fn_name == "__LIST_REVERSE__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + ".reverse()"
            if fn_name == "__DICT_CLEAR__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + ".clear()"
            if fn_name == "__DICT_POP__" and len(builtin_arg_strs) >= 2:
                return "pypop(" + builtin_arg_strs[0] + ", " + builtin_arg_strs[1] + ")"
            if fn_name == "__DICT_SETDEFAULT__" and len(builtin_arg_strs) >= 3:
                return "pysetdefault(" + builtin_arg_strs[0] + ", " + builtin_arg_strs[1] + ", " + builtin_arg_strs[2] + ")"
            if fn_name == "__SET_CLEAR__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + ".clear()"
            if fn_name == "py_reversed_object" and len(builtin_arg_strs) >= 1:
                return "Array.from(" + builtin_arg_strs[0] + ").reverse()"
            if fn_name == "__DICT_GET__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                key = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                default = builtin_arg_strs[2] if len(builtin_arg_strs) >= 3 else "null"
                return "(" + owner + ".get(" + key + ") ?? " + default + ")"
            if fn_name == "__DICT_ITEMS__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + ".entries()"
            if fn_name == "__DICT_KEYS__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return "Array.from(" + owner + ".keys())"
            if fn_name == "__DICT_VALUES__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return "Array.from(" + owner + ".values())"
            if fn_name == "__SET_ADD__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return owner + ".add(" + item + ")"
            if fn_name == "__SET_DISCARD__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return owner + ".delete(" + item + ")"
            if fn_name == "__SET_REMOVE__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return owner + ".delete(" + item + ")"
            if fn_name == "pyPrint":
                wrapped_bc: list[str] = []
                for i, a_node in enumerate(args):
                    a_s = arg_strs[i] if i < len(arg_strs) else ""
                    wrapped_bc.append(_wrap_pyprint_arg(a_s, a_node))
                return "pyPrint(" + ", ".join(wrapped_bc + kw_strs) + ")"
            # extern_delegate with Attribute func: emit as method call owner.method(args)
            # instead of free function call method(owner, args)
            attr_name = _str(func, "attr") if isinstance(func, dict) else ""
            if method_owner != "" and attr_name != "" and fn_name == attr_name:
                return method_owner + "." + _safe_ts_ident(fn_name) + "(" + ", ".join(all_arg_strs) + ")"
            fn_name_safe = fn_name if "." in fn_name else _safe_ts_ident(fn_name)
            return fn_name_safe + "(" + ", ".join(builtin_arg_strs) + ")"
        if fn_name == "__CAST__":
            if len(all_arg_strs) >= 1:
                semantic_tag = _str(node, "semantic_tag")
                if semantic_tag == "cast.float":
                    return "Number(" + all_arg_strs[0] + ")"
                fn_id_cast = _str(func, "id") if isinstance(func, dict) else ""
                if fn_id_cast in ctx.mapping.calls:
                    mapped_cast = ctx.mapping.calls[fn_id_cast]
                    if isinstance(mapped_cast, str) and mapped_cast not in ("", "__CAST__"):
                        mapped_safe = mapped_cast if "." in mapped_cast else _safe_ts_ident(mapped_cast)
                        if mapped_cast == "Math.trunc":
                            return mapped_safe + "(Number(" + all_arg_strs[0] + "))"
                        return mapped_safe + "(" + all_arg_strs[0] + ")"
                return all_arg_strs[0]
            return "null"
        if fn_name == "__PANIC__":
            msg = all_arg_strs[0] if len(all_arg_strs) >= 1 else '"error"'
            return "(() => { throw new Error(" + msg + "); })()"

    if isinstance(func, dict):
        func_kind = _str(func, "kind")

        if func_kind == "Attribute":
            owner_node = func.get("value")
            attr = _str(func, "attr")
            owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""

            # Static method call: ClassName.method(...)
            if _str(node, "call_dispatch_kind") == "static_method":
                return _safe_ts_ident(owner_id) + "." + _safe_ts_ident(attr) + "(" + ", ".join(all_arg_strs) + ")"

            # super().__init__() → super(...)
            if isinstance(owner_node, dict):
                owner_kind = _str(owner_node, "kind")
                if owner_kind == "Call":
                    inner_func = owner_node.get("func")
                    if isinstance(inner_func, dict) and _str(inner_func, "id") == "super":
                        if attr == "__init__":
                            return "super(" + ", ".join(all_arg_strs) + ")"
                        return "super." + _safe_ts_ident(attr) + "(" + ", ".join(all_arg_strs) + ")"
                if owner_kind == "Name" and _str(owner_node, "id") == "super":
                    if attr == "__init__":
                        return "super(" + ", ".join(all_arg_strs) + ")"
                    return "super." + _safe_ts_ident(attr) + "(" + ", ".join(all_arg_strs) + ")"

            # Module method call: math.sqrt etc.
            if _is_module_call(ctx, owner_node):
                mod_id = _str(node, "runtime_module_id")
                if mod_id == "":
                    mod_id = ctx.import_alias_modules.get(owner_id, "")
                runtime_symbol = _str(node, "runtime_symbol")
                if runtime_symbol == "":
                    runtime_symbol = _str(func, "runtime_symbol")
                if runtime_symbol == "":
                    runtime_symbol = attr
                if should_skip_module(mod_id, ctx.mapping):
                    resolved_runtime_call = _str(node, "resolved_runtime_call")
                    runtime_call = _str(node, "runtime_call")
                    resolved = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping, module_id=mod_id, resolved_runtime_call=resolved_runtime_call, runtime_call=runtime_call)
                    if resolved == "":
                        resolved = runtime_symbol
                    return _safe_ts_ident(resolved) + "(" + ", ".join(all_arg_strs) + ")"
                # Non-skipped module: keep the module prefix (e.g. png.write_rgb_png)
                return _safe_ts_ident(owner_id) + "." + _safe_ts_ident(runtime_symbol) + "(" + ", ".join(all_arg_strs) + ")"

            # Regular method call: obj.method(...)
            owner_code = _emit_expr(ctx, owner_node)
            owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            owner_key = _owner_runtime_mapping_key(owner_rt, attr)
            if owner_key == "" and owner_rt in ("", "unknown"):
                owner_key = "str." + attr if ("str." + attr) in ctx.mapping.calls else ""
            if owner_key != "":
                mapped_owner = ctx.mapping.calls.get(owner_key, "")
                if isinstance(mapped_owner, str) and mapped_owner != "":
                    expanded = _expand_owner_mapped_call(ctx, mapped_owner, owner_code, all_arg_strs)
                    if expanded != "":
                        return expanded
                    mapped_safe = mapped_owner if "." in mapped_owner else _safe_ts_ident(mapped_owner)
                    return mapped_safe + "(" + ", ".join([owner_code] + all_arg_strs) + ")"
            return owner_code + "." + attr + "(" + ", ".join(all_arg_strs) + ")"

        if func_kind == "Name":
            fn_id = _str(func, "id")
            semantic_tag = _str(node, "semantic_tag")
            call_rt = _str(node, "resolved_type")
            func_rt = _str(func, "resolved_type")

            if fn_id == "isinstance" and len(args) >= 2:
                type_arg = args[1] if isinstance(args[1], dict) else None
                type_name = _str(type_arg, "id") if isinstance(type_arg, dict) else ""
                if type_name == "":
                    type_name = _str(type_arg, "repr") if isinstance(type_arg, dict) else ""
                return _emit_isinstance(ctx, {
                    "kind": "IsInstance",
                    "value": args[0],
                    "expected_type_name": type_name,
                    "expected_type_id": {"kind": "Name", "id": type_name},
                })
            if fn_id == "py_reversed_object" and len(all_arg_strs) >= 1:
                return "Array.from(" + all_arg_strs[0] + ").reverse()"
            if fn_id == "__LIST_SORT__" and len(all_arg_strs) >= 1:
                return all_arg_strs[0] + ".sort()"
            if fn_id == "__LIST_REVERSE__" and len(all_arg_strs) >= 1:
                return all_arg_strs[0] + ".reverse()"
            if fn_id == "__DICT_CLEAR__" and len(all_arg_strs) >= 1:
                return all_arg_strs[0] + ".clear()"
            if fn_id == "__SET_CLEAR__" and len(all_arg_strs) >= 1:
                return all_arg_strs[0] + ".clear()"

            if fn_id in ("__init__", "py__init__") and len(args) >= 1:
                first_arg = args[0]
                if isinstance(first_arg, dict) and _str(first_arg, "kind") == "Call":
                    super_func = first_arg.get("func")
                    if isinstance(super_func, dict) and _str(super_func, "id") == "super":
                        return "super(" + ", ".join(all_arg_strs[1:]) + ")"

            # cast(type_arg, value) → (value as TypeScriptType)
            # Python's cast() is a no-op at runtime; emit as a TS type assertion.
            if fn_id == "cast" and len(args) >= 2:
                val_code = all_arg_strs[1]
                if not ctx.strip_types:
                    type_arg = args[0]
                    type_str = _str(type_arg, "resolved_type") if isinstance(type_arg, dict) else ""
                    ts_t = ts_type(type_str) if type_str else ""
                    if ts_t and ts_t != "any":
                        return "(" + val_code + " as " + ts_t + ")"
                return val_code

            # super() call
            if fn_id == "super":
                return "super(" + ", ".join(all_arg_strs) + ")"

            if semantic_tag == "core.bytearray_ctor":
                if len(all_arg_strs) == 0:
                    return "pyBytearray()"
                return "pyBytearray(" + all_arg_strs[0] + ")"
            if semantic_tag == "core.bytes_ctor":
                if len(all_arg_strs) == 0:
                    return "pyBytes()"
                return "pyBytes(" + all_arg_strs[0] + ")"
            if func_rt == "type" and call_rt == "bytearray":
                if len(all_arg_strs) == 0:
                    return "pyBytearray()"
                return "pyBytearray(" + all_arg_strs[0] + ")"
            if func_rt == "type" and call_rt == "bytes":
                if len(all_arg_strs) == 0:
                    return "pyBytes()"
                return "pyBytes(" + all_arg_strs[0] + ")"

            # Constructor call for known classes
            if fn_id in ctx.class_names:
                return "new " + _safe_ts_ident(fn_id) + "(" + ", ".join(all_arg_strs) + ")"

            # Exception constructor
            if _is_exception_type_name(ctx, fn_id):
                msg = all_arg_strs[0] if len(all_arg_strs) >= 1 else '"' + fn_id + '"'
                return "new Error(" + msg + ")"

            # runtime import
            if fn_id in ctx.runtime_imports:
                resolved = ctx.runtime_imports[fn_id]
                if resolved == "pyIsInstance":
                    linked_isinstance = _emit_linked_type_id_isinstance(ctx, args)
                    if linked_isinstance is not None:
                        return linked_isinstance
                if resolved == "pyPrint":
                    wrapped_ri: list[str] = []
                    for i, a_node in enumerate(args):
                        a_s = arg_strs[i] if i < len(arg_strs) else ""
                        wrapped_ri.append(_wrap_pyprint_arg(a_s, a_node))
                    return "pyPrint(" + ", ".join(wrapped_ri + kw_strs) + ")"
                return _safe_ts_ident(resolved) + "(" + ", ".join(all_arg_strs) + ")"

            # Check mapping for runtime calls
            runtime_call = _str(func, "runtime_call")
            if runtime_call == "":
                runtime_call = _str(node, "runtime_call")
            if runtime_call != "":
                adapter_kind = _str(node, "runtime_call_adapter_kind")
                if adapter_kind == "":
                    adapter_kind = "builtin"
                name = resolve_runtime_call(runtime_call, fn_id, adapter_kind, ctx.mapping)
                if name != "" and name != "__CAST__":
                    if name == "pyIsInstance":
                        linked_isinstance = _emit_linked_type_id_isinstance(ctx, args)
                        if linked_isinstance is not None:
                            return linked_isinstance
                    if name == "pyPrint":
                        wrapped: list[str] = []
                        for i, a_node in enumerate(args):
                            a_s = arg_strs[i] if i < len(arg_strs) else ""
                            wrapped.append(_wrap_pyprint_arg(a_s, a_node))
                        return "pyPrint(" + ", ".join(wrapped + kw_strs) + ")"
                    name_safe = name if "." in name else _safe_ts_ident(name)
                    return name_safe + "(" + ", ".join(all_arg_strs) + ")"

            # Direct fn_id match in mapping.calls (e.g., py_to_string → pyStr)
            if fn_id in ctx.mapping.calls:
                mapped = ctx.mapping.calls[fn_id]
                if isinstance(mapped, str) and mapped != "" and mapped != "__CAST__":
                    if mapped == "pyIsInstance":
                        linked_isinstance = _emit_linked_type_id_isinstance(ctx, args)
                        if linked_isinstance is not None:
                            return linked_isinstance
                    # For pyPrint: wrap float-typed args with pyFloatStr to preserve "2.0" format
                    if mapped == "pyPrint":
                        print_arg_strs: list[str] = []
                        for i, a_node in enumerate(args):
                            a_s2 = arg_strs[i] if i < len(arg_strs) else ""
                            print_arg_strs.append(_wrap_pyprint_arg(a_s2, a_node))
                        return "pyPrint(" + ", ".join(print_arg_strs + kw_strs) + ")"
                    mapped_safe = mapped if "." in mapped else _safe_ts_ident(mapped)
                    return mapped_safe + "(" + ", ".join(all_arg_strs) + ")"

            return _ts_symbol_name(ctx, fn_id) + "(" + ", ".join(all_arg_strs) + ")"

    # Lambda IIFE: wrap in parens so `((x) => x+1)(3)` is valid
    if isinstance(func, dict) and _str(func, "kind") == "Lambda":
        func_code = _emit_expr(ctx, func)
        return "(" + func_code + ")(" + ", ".join(all_arg_strs) + ")"

    func_code = _emit_expr(ctx, func)
    return func_code + "(" + ", ".join(all_arg_strs) + ")"


def _emit_binop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    right_node = node.get("right")
    left = _emit_expr(ctx, left_node)
    right = _emit_expr(ctx, right_node)
    op = _str(node, "op")
    _OP_MAP: dict[str, str] = {}
    _OP_MAP["Add"] = "+"
    _OP_MAP["Sub"] = "-"
    _OP_MAP["Mult"] = "*"
    _OP_MAP["Div"] = "/"
    _OP_MAP["FloorDiv"] = "__floordiv"
    _OP_MAP["Mod"] = "%"
    _OP_MAP["Pow"] = "**"
    _OP_MAP["BitAnd"] = "&"
    _OP_MAP["BitOr"] = "|"
    _OP_MAP["BitXor"] = "^"
    _OP_MAP["LShift"] = "<<"
    _OP_MAP["RShift"] = ">>>"
    op_str = _OP_MAP.get(op, op)
    if op_str == "__floordiv":
        return "pyFloorDiv(" + left + ", " + right + ")"
    # List concat: list + list → .concat()
    if op_str == "+":
        left_rt = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
        right_rt = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""
        left_is_list = left_rt.startswith("list[") or left_rt == "list"
        right_is_list = right_rt.startswith("list[") or right_rt == "list"
        if left_is_list and right_is_list:
            return left + ".concat(" + right + ")"
    # List repeat: list * number → Array.from({length: n}, (_, i) => template[i % len])
    if op_str == "*":
        left_rt = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
        right_rt = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""
        _INT_TYPES = ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "number")
        left_is_list = left_rt.startswith("list[") or left_rt == "list"
        right_is_list = right_rt.startswith("list[") or right_rt == "list"
        if left_is_list and right_rt in _INT_TYPES:
            return "(() => { const _arr = " + left + "; const _n = " + right + "; return Array.from({length: _n * _arr.length}, (_, i) => _arr[i % _arr.length]); })()"
        if right_is_list and left_rt in _INT_TYPES:
            return "(() => { const _arr = " + right + "; const _n = " + left + "; return Array.from({length: _n * _arr.length}, (_, i) => _arr[i % _arr.length]); })()"
    return "(" + left + " " + op_str + " " + right + ")"


def _emit_unaryop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    _OP_MAP: dict[str, str] = {}
    _OP_MAP["USub"] = "-"
    _OP_MAP["UAdd"] = "+"
    _OP_MAP["Not"] = "!"
    _OP_MAP["Invert"] = "~"
    op_str = _OP_MAP.get(op, op)
    return "(" + op_str + operand + ")"


def _types_may_mismatch(left_rt: str, right_rt: str) -> bool:
    """Return True if left/right types could cause TS2367 (e.g., string vs number)."""
    _STR: set[str] = set()
    _STR.add("str")
    _STR.add("string")
    _STR.add("char")
    _NUM: set[str] = set()
    for _num_name in [
        "int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
        "number", "float", "float32", "float64", "byte",
    ]:
        _NUM.add(_num_name)
    return (left_rt in _STR and right_rt in _NUM) or (left_rt in _NUM and right_rt in _STR)


def _is_none_constant(node_or_none: JsonVal) -> bool:
    if not isinstance(node_or_none, dict):
        return False
    if _str(node_or_none, "kind") != "Constant":
        return False
    value = node_or_none.get("value")
    return value is None or value == "None"


def _is_primitive_ts_rt(rt: str) -> bool:
    if rt in ("", "str", "string", "char", "bool", "boolean", "None", "null"):
        return True
    return rt in (
        "int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
        "number", "float", "float32", "float64", "byte",
    )


def _get_ts_rt(ctx: EmitContext, node_or_none: JsonVal) -> str:
    """Get the TypeScript type for a node, preferring ctx.var_types for Name nodes."""
    if not isinstance(node_or_none, dict):
        return ""
    node = node_or_none
    rt = _str(node, "resolved_type")
    if _str(node, "kind") == "Name":
        var_name = _str(node, "id") or _str(node, "repr")
        ts_type_from_ctx = ctx.var_types.get(_ts_symbol_name(ctx, var_name), "")
        if ts_type_from_ctx != "":
            return ts_type_from_ctx
    return rt


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    left = _emit_expr(ctx, left_node)
    left_rt = _get_ts_rt(ctx, left_node)
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return left
    _OP_MAP: dict[str, str] = {}
    _OP_MAP["Eq"] = "==="
    _OP_MAP["NotEq"] = "!=="
    _OP_MAP["Lt"] = "<"
    _OP_MAP["LtE"] = "<="
    _OP_MAP["Gt"] = ">"
    _OP_MAP["GtE"] = ">="
    _OP_MAP["Is"] = "==="
    _OP_MAP["IsNot"] = "!=="
    _OP_MAP["In"] = "__IN__"
    _OP_MAP["NotIn"] = "__NOT_IN__"
    parts: list[str] = []
    current_left = left
    current_left_rt = left_rt
    for idx, comparator in enumerate(comparators):
        op_obj = ops[idx] if idx < len(ops) else None
        op_name = op_obj if isinstance(op_obj, str) else _str(op_obj, "kind") if isinstance(op_obj, dict) else ""
        op_text = _OP_MAP.get(op_name, op_name)
        right_node = comparator
        right = _emit_expr(ctx, right_node)
        right_rt = _get_ts_rt(ctx, right_node)
        if op_text == "__IN__":
            parts.append("pyIn(" + current_left + ", " + right + ")")
        elif op_text == "__NOT_IN__":
            parts.append("(!pyIn(" + current_left + ", " + right + "))")
        else:
            # Cast to any if types may mismatch to avoid TS2367
            lhs = current_left
            rhs = right
            if op_text in ("===", "!=="):
                if _types_may_mismatch(current_left_rt, right_rt) and not ctx.strip_types:
                    lhs = "(" + lhs + " as unknown as any)"
                if not ctx.strip_types:
                    prev_node = left_node if idx == 0 else comparators[idx - 1]
                    if _str(prev_node, "kind") == "Constant" and not _is_none_constant(prev_node):
                        lhs = "(" + lhs + " as string | number | boolean | null)"
                    if _str(right_node, "kind") == "Constant" and not _is_none_constant(right_node):
                        rhs = "(" + rhs + " as string | number | boolean | null)"
                    if (_str(right_node, "kind") == "Constant" and not _is_none_constant(right_node)
                            and not _is_primitive_ts_rt(current_left_rt)):
                        lhs = "(" + lhs + " as unknown as any)"
                    if (_str(prev_node, "kind") == "Constant" and not _is_none_constant(prev_node)
                            and not _is_primitive_ts_rt(right_rt)):
                        rhs = "(" + rhs + " as unknown as any)"
            parts.append("(" + lhs + " " + op_text + " " + rhs + ")")
        current_left = right
        current_left_rt = right_rt
    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    op = _str(node, "op")
    op_text = "&&" if op == "And" else "||"
    return "(" + (" " + op_text + " ").join(_emit_expr(ctx, v) for v in values) + ")"


# ---------------------------------------------------------------------------
# CommonRenderer subclasses
# ---------------------------------------------------------------------------

class _TsExprRenderer(CommonRenderer):
    def __init__(self, ctx: EmitContext) -> None:
        self.ctx = ctx
        super().__init__("ts")

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(self.ctx, node)

    def render_binop(self, node: dict[str, JsonVal]) -> str:
        return _emit_binop(self.ctx, node)

    def render_unaryop(self, node: dict[str, JsonVal]) -> str:
        return _emit_unaryop(self.ctx, node)

    def render_compare(self, node: dict[str, JsonVal]) -> str:
        return _emit_compare(self.ctx, node)

    def render_boolop(self, node: dict[str, JsonVal]) -> str:
        return _emit_boolop(self.ctx, node)

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("ts expr renderer does not handle assign")

    def render_expr_extension(self, node: dict[str, JsonVal]) -> str:
        return _emit_expr_extension(self.ctx, node)


class _TsStmtRenderer(CommonRenderer):
    def __init__(self, ctx: EmitContext) -> None:
        self.ctx = ctx
        super().__init__("ts")
        self.state.lines = ctx.lines
        self.state.indent_level = ctx.indent_level

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(self.ctx, node)

    def render_expr(self, node: JsonVal) -> str:
        return _emit_expr(self.ctx, node)

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_condition_expr(self, node: JsonVal) -> str:
        result = _ts_condition_expr(self.ctx, node)
        # If truthiness was rewritten (no extra parens needed), return as-is
        if isinstance(node, dict):
            rt = _str(node, "resolved_type")
            is_collection = rt in ("bytes", "bytearray")
            if not is_collection:
                is_collection = rt.startswith("list[") or rt == "list"
            if not is_collection:
                is_collection = rt.startswith("tuple[") or rt == "tuple"
            if not is_collection:
                is_collection = rt.startswith("dict[") or rt == "dict"
            if not is_collection:
                is_collection = rt.startswith("set[") or rt == "set"
            if is_collection:
                return result
        return self._format_condition(result)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("ts stmt renderer assign not used as string")

    def emit_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        kind = self._str(node, "kind")
        if kind == "AnnAssign":
            _emit_ann_assign(self.ctx, node)
        else:
            _emit_assign(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_return_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_return(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_expr_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_expr_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_raise_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_raise(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def render_raise_value(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("ts stmt renderer raise value not used directly")

    def render_except_open(self, handler: dict[str, JsonVal]) -> str:
        name = _str(handler, "name")
        if name != "":
            return "} catch (" + _safe_ts_ident(name) + ") {"
        return "} catch (e) {"

    def emit_try_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_try(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_stmt(self, node: JsonVal) -> None:
        _COMMON_KINDS: set[str] = {"Expr", "Return", "Assign", "AnnAssign", "Pass", "Raise", "Try", "comment", "blank", "If", "While"}
        if isinstance(node, dict):
            kind = self._str(node, "kind")
            if kind in _COMMON_KINDS:
                super().emit_stmt(node)
                self.ctx.indent_level = self.state.indent_level
                return
        if isinstance(node, dict):
            self.emit_stmt_extension(node)

    def emit_stmt_extension(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level


def _emit_common_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> bool:
    _COMMON_KINDS: set[str] = {"Expr", "Return", "Assign", "AnnAssign", "Pass", "Raise", "Try", "comment", "blank", "If", "While"}
    kind = _str(node, "kind")
    if kind not in _COMMON_KINDS:
        return False
    renderer = _TsStmtRenderer(ctx)
    renderer.emit_stmt(node)
    ctx.indent_level = renderer.state.indent_level
    return True


# ---------------------------------------------------------------------------
# Expression extensions
# ---------------------------------------------------------------------------

def _emit_expr_extension(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    kind = _str(node, "kind")
    if kind == "Subscript":
        return _emit_subscript(ctx, node)
    if kind == "List":
        return _emit_list_literal(ctx, node)
    if kind == "Dict":
        return _emit_dict_literal(ctx, node)
    if kind == "Set":
        return _emit_set_literal(ctx, node)
    if kind == "Tuple":
        return _emit_tuple_literal(ctx, node)
    if kind == "IfExp":
        return _emit_ifexp(ctx, node)
    if kind == "JoinedStr":
        return _emit_fstring(ctx, node)
    if kind == "FormattedValue":
        inner = node.get("value")
        return _emit_expr(ctx, inner)
    if kind == "Lambda":
        return _emit_lambda(ctx, node)
    if kind == "IsInstance":
        return _emit_isinstance(ctx, node)
    if kind == "Unbox":
        return _emit_unbox(ctx, node)
    if kind == "Box":
        return _emit_box(ctx, node)
    if kind == "ObjStr":
        arg = node.get("value")
        return "pyStr(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjLen":
        arg = node.get("value")
        return "pyLen(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjBool":
        arg = node.get("value")
        return "pyBool(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjTypeId":
        arg = node.get("value")
        return "pyTypeId(" + _emit_expr(ctx, arg) + ")"
    if kind == "IsSubtype":
        actual = _emit_expr(ctx, node.get("actual_type_id"))
        expected = _emit_expr(ctx, node.get("expected_type_id"))
        return "pyIsSubtype(" + actual + ", " + expected + ")"
    if kind == "IsSubclass":
        actual = _emit_expr(ctx, node.get("actual_type_id"))
        expected = _emit_expr(ctx, node.get("expected_type_id"))
        return "pyIsSubtype(" + actual + ", " + expected + ")"
    if kind == "CovariantCopy":
        return _emit_expr(ctx, node.get("value"))
    if kind == "ListComp":
        return _emit_list_comp(ctx, node)
    if kind == "SetComp":
        return _emit_set_comp(ctx, node)
    if kind == "DictComp":
        return _emit_dict_comp(ctx, node)
    if kind == "Slice":
        # Bare slice — not in subscript context
        lower = node.get("lower")
        upper = node.get("upper")
        lc = _emit_expr(ctx, lower) if isinstance(lower, dict) else "null"
        uc = _emit_expr(ctx, upper) if isinstance(upper, dict) else "null"
        return "pySlice(__obj__, " + lc + ", " + uc + ")"
    raise RuntimeError("unsupported_expr_kind_ts: " + kind)


def _comp_iter_code(ctx: EmitContext, gen: dict) -> str:
    """Emit the iterable for a comprehension generator, wrapping strings with Array.from."""
    iter_node = gen.get("iter")
    iter_code = _emit_expr(ctx, iter_node)
    iter_rt = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
    if iter_rt in ("str", "string"):
        iter_code = "Array.from(" + iter_code + ")"
    return iter_code


def _comp_filter_code(ctx: EmitContext, gen: dict, iter_code: str) -> str:
    """Apply ifs filter to an iterable expression."""
    ifs = gen.get("ifs")
    if not isinstance(ifs, list) or len(ifs) == 0:
        return iter_code
    target_node = gen.get("target")
    target_code = _emit_binding_pattern(target_node)
    filter_parts = [_emit_expr(ctx, cond) for cond in ifs if isinstance(cond, dict)]
    if not filter_parts:
        return iter_code
    filter_expr = " && ".join(filter_parts)
    return iter_code + ".filter((" + target_code + ") => " + filter_expr + ")"


def _emit_list_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = _emit_expr(ctx, node.get("elt"))
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "[" + elt + "]"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "[" + elt + "]"
    iter_code = _comp_iter_code(ctx, gen)
    iter_code = _comp_filter_code(ctx, gen, iter_code)
    target_node = gen.get("target")
    target_code = _emit_binding_pattern(target_node)
    return iter_code + ".map((" + target_code + ") => " + elt + ")"


def _emit_set_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = _emit_expr(ctx, node.get("elt"))
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "new Set([" + elt + "])"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "new Set([" + elt + "])"
    iter_code = _comp_iter_code(ctx, gen)
    iter_code = _comp_filter_code(ctx, gen, iter_code)
    target_node = gen.get("target")
    target_code = _emit_binding_pattern(target_node)
    return "new Set(" + iter_code + ".map((" + target_code + ") => " + elt + "))"


def _emit_dict_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    key = _emit_expr(ctx, node.get("key"))
    value = _emit_expr(ctx, node.get("value"))
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "new Map([[" + key + ", " + value + "]])"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "new Map([[" + key + ", " + value + "]])"
    iter_code = _comp_iter_code(ctx, gen)
    iter_code = _comp_filter_code(ctx, gen, iter_code)
    target_node = gen.get("target")
    target_code = _emit_binding_pattern(target_node)
    return "new Map(" + iter_code + ".map((" + target_code + ") => [" + key + ", " + value + "]))"


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_expr_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if not isinstance(value, dict):
        return
    vk = _str(value, "kind")
    # String constant at statement level → docstring/comment
    if vk == "Constant" and isinstance(value.get("value"), str):
        doc_text = value.get("value")
        if isinstance(doc_text, str) and doc_text.strip() != "":
            for line in doc_text.strip().split("\n"):
                _emit(ctx, "// " + line)
        return
    # Name "continue"/"break" as expr stmt → TS control flow keyword
    if vk == "Name":
        name_id = _str(value, "id")
        if name_id == "continue":
            _emit(ctx, "continue;")
            return
        if name_id == "break":
            _emit(ctx, "break;")
            return
        # "del" as standalone expr stmt → Python del keyword placeholder (data lost in east3)
        if name_id == "del":
            return  # no-op: delete target info was lost during lowering
        # "else" as standalone expr stmt → Python for/else construct (no TS equivalent)
        if name_id == "else":
            return  # no-op: for/else in Python; TS has no equivalent standalone marker
        # Skip any standalone Name with unknown resolved_type that is a Python-only keyword artifact
        if _str(value, "resolved_type") == "unknown" and name_id in ("else", "pass", "Python", "Blank"):
            return
    _emit(ctx, _emit_expr(ctx, value) + ";")


def _emit_ann_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_val = node.get("target")
    rt = _str(node, "decl_type")
    if rt == "":
        rt = _str(node, "resolved_type")
    value = node.get("value")
    annotation_field = _str(node, "annotation")

    # Attribute assignment (self.x = ...)
    is_attr_target = isinstance(target_val, dict) and _str(target_val, "kind") == "Attribute"
    if is_attr_target:
        lhs = _emit_expr(ctx, target_val)
        if value is not None:
            _emit(ctx, lhs + " = " + _emit_expr(ctx, value) + ";")
        return

    # Get target name
    target_name = ""
    if isinstance(target_val, str):
        target_name = target_val
    elif isinstance(target_val, dict):
        target_name = _str(target_val, "id")
        if target_name == "":
            target_name = _str(target_val, "repr")
    if target_name == "":
        tn = node.get("target_node")
        if isinstance(tn, dict):
            target_name = _str(tn, "id")

    name = _ts_symbol_name(ctx, target_name)
    is_reassign = _bool(node, "is_reassign") or name in ctx.var_types
    ann = _type_annotation(ctx, rt)

    is_top_level_public = _is_top_level_public_name(ctx, name)
    if value is not None:
        val_code = _emit_expr(ctx, value)
        if is_reassign:
            _emit(ctx, name + " = " + val_code + ";")
        else:
            ctx.var_types[name] = rt
            # Use const if arg_usage says readonly, otherwise let
            kw = "const" if _bool(node, "arg_usage_readonly") else "let"
            export_prefix = "export " if is_top_level_public else ""
            _emit(ctx, export_prefix + kw + " " + name + ann + " = " + val_code + ";")
    else:
        if not is_reassign:
            ctx.var_types[name] = rt
            zero = ts_zero_value(rt)
            export_prefix = "export " if is_top_level_public else ""
            _emit(ctx, export_prefix + "let " + name + ann + " = " + zero + ";")


_PY_TO_TS_TYPE_NAME: dict[str, str] = {}
_PY_TO_TS_TYPE_NAME["None"] = "null"
_PY_TO_TS_TYPE_NAME["none"] = "null"
_PY_TO_TS_TYPE_NAME["bool"] = "boolean"
_PY_TO_TS_TYPE_NAME["int"] = "number"
_PY_TO_TS_TYPE_NAME["int64"] = "number"
_PY_TO_TS_TYPE_NAME["int32"] = "number"
_PY_TO_TS_TYPE_NAME["float"] = "number"
_PY_TO_TS_TYPE_NAME["float32"] = "number"
_PY_TO_TS_TYPE_NAME["float64"] = "number"
_PY_TO_TS_TYPE_NAME["str"] = "string"
_PY_TO_TS_TYPE_NAME["string"] = "string"
_PY_TO_TS_TYPE_NAME["bytes"] = "number[]"
_PY_TO_TS_TYPE_NAME["bytearray"] = "number[]"
_PY_TO_TS_TYPE_NAME["TextIOWrapper"] = "any"
_PY_TO_TS_TYPE_NAME["IOBase"] = "any"
_PY_TO_TS_TYPE_NAME["BufferedReader"] = "any"
_PY_TO_TS_TYPE_NAME["BufferedWriter"] = "any"
_PY_TO_TS_TYPE_NAME["any"] = "any"
_PY_TO_TS_TYPE_NAME["Any"] = "any"
_PY_TO_TS_TYPE_NAME["object"] = "any"


def _py_type_name_to_ts(name: str) -> str:
    """Convert a Python type name to TypeScript type."""
    if name in _PY_TO_TS_TYPE_NAME:
        return _PY_TO_TS_TYPE_NAME[name]
    # Try ts_type conversion for compound types
    converted = ts_type(name)
    if converted and converted != "any":
        return converted
    return _safe_ts_ident(name)


def _elem_to_ts_type(elem: JsonVal) -> str:
    """Convert a Union element (Name or Subscript node) to a TypeScript type string."""
    if not isinstance(elem, dict):
        return "any"
    elem_rt = _str(elem, "resolved_type")
    elem_kind = _str(elem, "kind")
    # For Name nodes or when resolved_type is "type" (Python type object), use id/repr
    if elem_kind == "Name" or elem_rt in ("type", ""):
        raw = _str(elem, "id") or _str(elem, "repr")
        return _py_type_name_to_ts(raw) if raw else "any"
    # For Subscript nodes like list[T] or dict[K, V], use repr for conversion
    if elem_kind == "Subscript" and (elem_rt == "type" or elem_rt in ("unknown", "")):
        raw = _str(elem, "repr")
        return _py_type_name_to_ts(raw) if raw else "any"
    if elem_rt and elem_rt not in ("unknown",):
        return _py_type_name_to_ts(elem_rt)
    raw = _str(elem, "id") or _str(elem, "repr")
    return _py_type_name_to_ts(raw) if raw else "any"


def _union_subscript_members(value_node: JsonVal) -> list[str] | None:
    """If value_node is Union[A, B, ...] or Optional[A], return TS member type names; else None."""
    if not isinstance(value_node, dict):
        return None
    if _str(value_node, "kind") != "Subscript":
        return None
    base = value_node.get("value")
    if not isinstance(base, dict):
        return None
    base_id = _str(base, "id")
    if base_id not in ("Union", "Optional"):
        return None
    slice_node = value_node.get("slice")
    if not isinstance(slice_node, dict):
        return None
    members: list[str] = []
    if _str(slice_node, "kind") == "Tuple":
        for elem in _list(slice_node, "elements"):
            members.append(_elem_to_ts_type(elem))
    else:
        members.append(_elem_to_ts_type(slice_node))
    if base_id == "Optional":
        members.append("null")
    return members if members else None


def _container_type_alias(value_node: JsonVal) -> str | None:
    """If value_node is dict[K,V], list[T], set[T] (Python type alias), return TS type string.

    Returns None if not recognized as a container type alias.
    """
    if not isinstance(value_node, dict):
        return None
    if _str(value_node, "kind") != "Subscript":
        return None
    base = value_node.get("value")
    if not isinstance(base, dict):
        return None
    base_id = _str(base, "id")
    # Only treat as type alias when the base is a builtin type constructor.
    # Regular subscript expressions like `my_list[i]` must NOT be mistaken for type aliases.
    if base_id not in ("dict", "list", "set", "tuple"):
        return None
    rt = _str(value_node, "resolved_type")
    if rt and rt not in ("unknown", ""):
        return ts_type(rt)
    repr_str = _str(value_node, "repr")
    if repr_str:
        return ts_type(repr_str)
    return None


def _emit_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    value = node.get("value")
    target_single = node.get("target")
    if len(targets) == 0 and isinstance(target_single, dict):
        targets = [target_single]
    if len(targets) == 0:
        return

    target_node = targets[0]

    if isinstance(target_node, dict):
        t_kind = _str(target_node, "kind")
        if t_kind in ("Name", "NameTarget"):
            name_raw = _str(target_node, "id")
            if name_raw == "":
                name_raw = _str(target_node, "repr")
            name = _ts_symbol_name(ctx, name_raw)
            if name == "_":
                val_code = _emit_expr(ctx, value)
                _emit(ctx, "void (" + val_code + ");")
                return
            is_top_level_public = _is_top_level_public_name(ctx, name)
            should_emit_type_alias = name not in ctx.var_types
            if should_emit_type_alias:
                should_emit_type_alias = not ctx.strip_types
            if should_emit_type_alias:
                members = _union_subscript_members(value)
                if members is not None:
                    _TS_PRIMITIVE_TYPES: set[str] = set()
                    for _ts_primitive_type in ["null", "boolean", "number", "string", "any", "void", "never", "unknown"]:
                        _TS_PRIMITIVE_TYPES.add(_ts_primitive_type)
                    safe_members: list[str] = []
                    for m in members:
                        is_safe = m in _TS_PRIMITIVE_TYPES or m.startswith("Map<")
                        if not is_safe:
                            is_safe = m.startswith("Set<") or "[]" in m
                        if is_safe:
                            safe_members.append(m)
                        else:
                            safe_members.append(_safe_ts_ident(m))
                    export_kw = ""
                    if is_top_level_public:
                        export_kw = "export "
                    _emit(ctx, export_kw + "type " + _safe_ts_ident(name) + " = " + " | ".join(safe_members) + ";")
                    _emit_blank(ctx)
                    return
                # Detect dict[K,V] / list[T] / set[T] type alias → emit as TS type
                ts_alias = _container_type_alias(value)
                if ts_alias and ts_alias not in ("any", ""):
                    export_kw = ""
                    if is_top_level_public:
                        export_kw = "export "
                    _emit(ctx, export_kw + "type " + _safe_ts_ident(name) + " = " + ts_alias + ";")
                    _emit_blank(ctx)
                    return
            val_code = _emit_expr(ctx, value)
            if name in ctx.var_types:
                _emit(ctx, name + " = " + val_code + ";")
            else:
                decl_type = _str(node, "decl_type")
                if decl_type == "" or decl_type == "unknown":
                    decl_type = _str(target_node, "resolved_type")
                if decl_type == "" or decl_type == "unknown":
                    decl_type = _str(value, "resolved_type") if isinstance(value, dict) else ""
                ctx.var_types[name] = decl_type
                ann = _type_annotation(ctx, decl_type)
                kw = "const" if _bool(node, "declare_const") else "let"
                export_prefix = "export " if is_top_level_public else ""
                _emit(ctx, export_prefix + kw + " " + name + ann + " = " + val_code + ";")
            return
        if t_kind == "Tuple":
            # Tuple unpacking: fwd_x, fwd_y, fwd_z = normalize(...)
            val_code = _emit_expr(ctx, value)
            elements = _list(target_node, "elements")
            names: list[str] = []
            all_declared = True
            for elem in elements:
                if isinstance(elem, dict) and _str(elem, "kind") in ("Name", "NameTarget"):
                    n = _ts_symbol_name(ctx, _str(elem, "id") or _str(elem, "repr"))
                    names.append(n)
                    if n not in ctx.var_types:
                        all_declared = False
                        ctx.var_types[n] = _str(elem, "resolved_type")
                else:
                    names.append("_")
            if all_declared:
                _emit(ctx, "[" + ", ".join(names) + "] = " + val_code + ";")
            else:
                _emit(ctx, "let [" + ", ".join(names) + "] = " + val_code + ";")
            return
        val_code = _emit_expr(ctx, value)
        if t_kind == "Attribute":
            lhs = _emit_expr(ctx, target_node)
            _emit(ctx, lhs + " = " + val_code + ";")
            return
        if t_kind == "Subscript":
            owner_node = target_node.get("value")
            owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            is_dict_type = owner_rt.startswith("dict[") or owner_rt == "dict"
            if is_dict_type:
                # dict[key] = val → Map.set(key, val)
                slice_node = target_node.get("slice")
                owner_code = _emit_expr(ctx, owner_node)
                key_code = _emit_expr(ctx, slice_node) if isinstance(slice_node, dict) else "undefined"
                _emit(ctx, owner_code + ".set(" + key_code + ", " + val_code + ");")
                return
            lhs = _emit_expr(ctx, target_node)
            _emit(ctx, lhs + " = " + val_code + ";")
            return

    val_code = _emit_expr(ctx, value)
    _emit(ctx, _emit_expr(ctx, target_node) + " = " + val_code + ";")


def _emit_aug_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = _emit_expr(ctx, node.get("target"))
    value = _emit_expr(ctx, node.get("value"))
    op = _str(node, "op")
    _AUG_OP: dict[str, str] = {}
    _AUG_OP["Add"] = "+="
    _AUG_OP["Sub"] = "-="
    _AUG_OP["Mult"] = "*="
    _AUG_OP["Div"] = "/="
    _AUG_OP["Mod"] = "%="
    _AUG_OP["Pow"] = "**="
    _AUG_OP["BitAnd"] = "&="
    _AUG_OP["BitOr"] = "|="
    _AUG_OP["BitXor"] = "^="
    _AUG_OP["LShift"] = "<<="
    _AUG_OP["RShift"] = ">>>="
    op_str = _AUG_OP.get(op, op + "=")
    if op == "FloorDiv":
        _emit(ctx, target + " = pyFloorDiv(" + target + ", " + value + ");")
    else:
        _emit(ctx, target + " " + op_str + " " + value + ";")


def _emit_return(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if value is not None and isinstance(value, dict):
        _emit(ctx, "return " + _emit_expr(ctx, value) + ";")
    else:
        _emit(ctx, "return;")


def _emit_raise(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    exc = node.get("exc")
    if exc is None:
        exc = node.get("value")
    if exc is not None and isinstance(exc, dict):
        exc_code = _emit_expr(ctx, exc)
        exc_type = _str(exc, "resolved_type")
        # If it looks like a constructor call, wrap in new ExcType(...)
        if _str(exc, "kind") == "Call":
            func = exc.get("func")
            func_name = _str(func, "id") if isinstance(func, dict) else ""
            if _is_exception_type_name(ctx, func_name):
                args = _list(exc, "args")
                arg_strs = [_emit_expr(ctx, a) for a in args]
                if func_name in ctx.class_names:
                    # User-defined exception: use its actual constructor
                    _emit(ctx, "throw new " + _safe_ts_ident(func_name) + "(" + ", ".join(arg_strs) + ");")
                else:
                    # Built-in exception: map to JS error type with message
                    msg = arg_strs[0] if len(arg_strs) >= 1 else '"' + func_name + '"'
                    js_exc_cls = _map_builtin_exception(func_name)
                    _emit(ctx, "throw new " + js_exc_cls + "(" + msg + ");")
                return
        _emit(ctx, "throw " + exc_code + ";")
    else:
        if ctx.current_exc_var != "":
            _emit(ctx, "throw " + ctx.current_exc_var + ";")
        else:
            _emit(ctx, "throw new Error(\"unknown error\");")


def _collect_nested_assigns(stmts: list[JsonVal], out: list[tuple[str, dict]]) -> None:
    """Recursively collect (name_raw, assign_node) from all nested block bodies.

    Python variables are function-scoped, but TypeScript `let` is block-scoped.
    We must pre-declare any variable that is first assigned inside a nested block
    (for/while/if/try) so it's accessible in the full function scope.

    This does NOT collect assignments at the outermost level (stmts) — only
    assignments inside nested blocks within those stmts.
    """
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        # Recurse into block bodies — collect their assignments AND their nested blocks
        if kind in ("For", "ForIn", "ForCore", "While"):
            body = _list(stmt, "body")
            _collect_assigns_from_block(body, out)
        elif kind == "If":
            _collect_assigns_from_block(_list(stmt, "body"), out)
            _collect_assigns_from_block(_list(stmt, "orelse"), out)
        elif kind == "Try":
            _collect_assigns_from_block(_list(stmt, "body"), out)
            for h in _list(stmt, "handlers"):
                if isinstance(h, dict):
                    _collect_assigns_from_block(_list(h, "body"), out)
            _collect_assigns_from_block(_list(stmt, "finalbody"), out)
        elif kind == "With":
            _collect_assigns_from_block(_list(stmt, "body"), out)
        # FunctionDef / ClosureDef: their inner vars are that function's scope — skip
        # ClassDef: inner vars are class scope — skip


def _collect_assigns_from_block(stmts: list[JsonVal], out: list[tuple[str, dict]]) -> None:
    """Collect (name_raw, assign_node) pairs from direct Assign/VarDecl nodes in stmts, then recurse."""
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("Assign", "AnnAssign"):
            targets = _list(stmt, "targets")
            target_single = stmt.get("target")
            if len(targets) == 0 and isinstance(target_single, dict):
                targets = [target_single]
            for t in targets:
                if not isinstance(t, dict):
                    continue
                t_kind = _str(t, "kind")
                if t_kind in ("Name", "NameTarget"):
                    name_raw = _str(t, "id") or _str(t, "repr")
                    if name_raw:
                        out.append((name_raw, stmt))
                elif t_kind == "Tuple":
                    # Tuple unpacking: fwd_x, fwd_y, fwd_z = normalize(...)
                    for elem in _list(t, "elements"):
                        if isinstance(elem, dict) and _str(elem, "kind") in ("Name", "NameTarget"):
                            name_raw = _str(elem, "id") or _str(elem, "repr")
                            if name_raw:
                                out.append((name_raw, elem))
        elif kind == "VarDecl":
            name_raw = _str(stmt, "name")
            if name_raw:
                out.append((name_raw, stmt))
        elif kind in ("TupleUnpack", "MultiAssign"):
            for t in _list(stmt, "targets"):
                if isinstance(t, dict) and _str(t, "kind") in ("Name", "NameTarget"):
                    name_raw = _str(t, "id") or _str(t, "repr")
                    if name_raw:
                        # Store the target node as the "stmt" so we can get its type
                        out.append((name_raw, t))
        # Recurse into nested blocks
        _collect_nested_assigns([stmt], out)


def _hoist_nested_declarations(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Pre-declare all variables first-assigned inside nested blocks.

    Emits `let varname: type;` for each such variable before the body starts,
    and registers them in ctx.var_types so _emit_assign won't re-declare them.
    """
    collected: list[tuple[str, dict]] = []
    _collect_nested_assigns(body, collected)

    seen: set[str] = set()
    for name_raw, stmt in collected:
        name = _ts_symbol_name(ctx, name_raw)
        if name in ctx.var_types or name in seen or name == "_":
            continue
        # Skip type alias assignments
        value = stmt.get("value")
        if _union_subscript_members(value) is not None:
            continue
        if _container_type_alias(value) is not None:
            continue
        seen.add(name)
        # Extract the declared type from the stmt node
        stmt_kind = _str(stmt, "kind")
        if stmt_kind == "VarDecl":
            decl_type = _str(stmt, "resolved_type")
        elif stmt_kind in ("Name", "NameTarget"):
            # For TupleUnpack/MultiAssign, we stored the target node itself as "stmt"
            decl_type = _str(stmt, "resolved_type")
        else:
            target_single = stmt.get("target")
            targets = _list(stmt, "targets")
            if len(targets) == 0 and isinstance(target_single, dict):
                targets = [target_single]
            t = next((x for x in targets if isinstance(x, dict) and
                       (_str(x, "id") == name_raw or _str(x, "repr") == name_raw)), None)
            decl_type = _str(stmt, "decl_type")
            if decl_type in ("", "unknown") and isinstance(t, dict):
                decl_type = _str(t, "resolved_type")
        ctx.var_types[name] = decl_type
        ann = _type_annotation(ctx, decl_type)
        _emit(ctx, "let " + name + ann + ";")


def _emit_try(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")

    _emit(ctx, "try {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1

    if len(handlers) > 0:
        # JS/TS only supports one catch block; use if/else chains inside it
        _emit(ctx, "} catch (__exc) {")
        ctx.indent_level += 1
        prev_exc_var = ctx.current_exc_var
        ctx.current_exc_var = "__exc"
        has_bare = False
        opened_if = False  # True once first typed handler is emitted
        for raw_handler in handlers:
            if not isinstance(raw_handler, dict):
                continue
            exc_type_node = raw_handler.get("type")
            name = _str(raw_handler, "name")
            handler_body = _list(raw_handler, "body")

            if exc_type_node is None:
                # bare except — catch-all
                has_bare = True
                if opened_if:
                    _emit(ctx, "} else {")
                    ctx.indent_level += 1
                    if name != "":
                        _emit(ctx, "const " + _safe_ts_ident(name) + " = __exc;")
                    _emit_body(ctx, handler_body)
                    ctx.indent_level -= 1
                else:
                    # bare except is the only/first handler
                    if name != "":
                        _emit(ctx, "const " + _safe_ts_ident(name) + " = __exc;")
                    _emit_body(ctx, handler_body)
            else:
                # Build instanceof condition
                cond = _exc_handler_condition(ctx, exc_type_node, "__exc")
                if not opened_if:
                    _emit(ctx, "if (" + cond + ") {")
                else:
                    _emit(ctx, "} else if (" + cond + ") {")
                opened_if = True
                ctx.indent_level += 1
                if name != "":
                    bound_name = _safe_ts_ident(name)
                    if ctx.strip_types:
                        _emit(ctx, "const " + bound_name + " = __exc;")
                    else:
                        _emit(ctx, "const " + bound_name + ": any = __exc;")
                _emit_body(ctx, handler_body)
                ctx.indent_level -= 1

        if opened_if:
            if not has_bare:
                # re-throw if no handler matched
                _emit(ctx, "} else {")
                ctx.indent_level += 1
                _emit(ctx, "throw __exc;")
                ctx.indent_level -= 1
            _emit(ctx, "}")
        ctx.current_exc_var = prev_exc_var
        ctx.indent_level -= 1

    if len(finalbody) > 0:
        _emit(ctx, "} finally {")
        ctx.indent_level += 1
        _emit_body(ctx, finalbody)
        ctx.indent_level -= 1

    _emit(ctx, "}")


def _exc_handler_condition(ctx: EmitContext, exc_type_node: JsonVal, catch_var: str) -> str:
    """Build the instanceof condition for an exception handler type node."""
    if not isinstance(exc_type_node, dict):
        return "true"
    kind = _str(exc_type_node, "kind")
    if kind == "Tuple":
        elts = _list(exc_type_node, "elts")
        parts: list[str] = []
        for elt in elts:
            parts.append(_exc_type_instanceof(ctx, elt, catch_var))
        return " || ".join(parts) if parts else "true"
    return _exc_type_instanceof(ctx, exc_type_node, catch_var)


def _exc_type_instanceof(ctx: EmitContext, type_node: JsonVal, catch_var: str) -> str:
    """Return `catch_var instanceof TypeName` for a single exception type node."""
    if not isinstance(type_node, dict):
        return "true"
    name = _str(type_node, "id")
    if name == "":
        name = _str(type_node, "repr")
    if name == "":
        return "true"
    # Map Python built-in exceptions to JS Error subclasses
    mapped = _map_builtin_exception(name)
    return catch_var + " instanceof " + mapped


def _map_builtin_exception(name: str) -> str:
    """Map Python built-in exception names to the best matching JS error class.

    For isinstance checks, TypeError matches only TypeError; Error matches all.
    We use the most specific JS type to preserve semantics.
    """
    return TS_BUILTIN_EXCEPTION_MAP.get(name, _safe_ts_ident(name))


def _emit_var_decl(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name_raw = _str(node, "name")
    name = _ts_symbol_name(ctx, name_raw)
    rt = _str(node, "resolved_type")
    value = node.get("value")
    ann = _type_annotation(ctx, rt)
    already_declared = name in ctx.var_types
    if value is not None:
        val_code = _emit_expr(ctx, value)
        # If target is byte/integer but value is a string (e.g., s[i]), wrap with pyOrd
        if rt in ("byte", "int", "int8", "uint8") and isinstance(value, dict):
            val_rt = _str(value, "resolved_type")
            if val_rt in ("str", "string", "char"):
                val_code = "pyOrd(" + val_code + ")"
        if already_declared:
            _emit(ctx, name + " = " + val_code + ";")
        else:
            _emit(ctx, "let " + name + ann + " = " + val_code + ";")
    else:
        if already_declared:
            return  # already declared with let varname;, no need to re-declare
        zero = ts_zero_value(rt)
        _emit(ctx, "let " + name + ann + " = " + zero + ";")
    ctx.var_types[name] = rt


def _emit_swap(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    # EAST3 Swap node uses "left"/"right" keys
    a_node = node.get("left") if node.get("left") is not None else node.get("a")
    b_node = node.get("right") if node.get("right") is not None else node.get("b")
    a = _emit_expr(ctx, a_node)
    b = _emit_expr(ctx, b_node)
    tmp = _next_temp(ctx, "swap")
    ann = _type_annotation(ctx, _str(node, "resolved_type"))
    _emit(ctx, "let " + tmp + ann + " = " + a + ";")
    _emit(ctx, a + " = " + b + ";")
    _emit(ctx, b + " = " + tmp + ";")


def _emit_multi_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    # MultiAssign: a, b = expr — unpack a tuple
    targets = _list(node, "targets")
    value = node.get("value")
    val_code = _emit_expr(ctx, value)
    tmp = _next_temp(ctx, "tup")
    rt = _str(node, "resolved_type") if isinstance(node, dict) else ""
    val_rt = _str(value, "resolved_type") if isinstance(value, dict) else ""
    if rt == "":
        rt = val_rt
    ann = _type_annotation(ctx, rt)
    _emit(ctx, "const " + tmp + ann + " = " + val_code + ";")
    for idx, target in enumerate(targets):
        if not isinstance(target, dict):
            continue
        t_kind = _str(target, "kind")
        if t_kind in ("Name", "NameTarget"):
            name_raw = _str(target, "id")
            if name_raw == "":
                name_raw = _str(target, "repr")
            name = _ts_symbol_name(ctx, name_raw)
            t_rt = _str(target, "resolved_type")
            t_ann = _type_annotation(ctx, t_rt)
            if name in ctx.var_types:
                _emit(ctx, name + " = " + tmp + "[" + str(idx) + "];")
            else:
                ctx.var_types[name] = t_rt
                _emit(ctx, "let " + name + t_ann + " = " + tmp + "[" + str(idx) + "];")


def _for_target_name_and_type(target_node: JsonVal) -> tuple[str, str]:
    """Extract (identifier, resolved_type) from a ForCore target_plan node."""
    if not isinstance(target_node, dict):
        return ("_item", "")
    tk = _str(target_node, "kind")
    if tk in ("Name", "NameTarget"):
        name = _str(target_node, "id")
        rt = _str(target_node, "target_type")
        if rt == "":
            rt = _str(target_node, "resolved_type")
        return (name, rt)
    # Tuple unpack target — just use _item
    return ("_item", "")


def _emit_for_core(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """ForCore: outer for-loop node. Dispatches to iter_plan."""
    # EAST3 ForCore uses target_plan and iter_plan
    target_node = node.get("target_plan")
    if target_node is None:
        target_node = node.get("target")
    iter_plan = node.get("iter_plan")
    body = _list(node, "body")
    orelse = _list(node, "orelse")

    target_name, target_rt = _for_target_name_and_type(target_node)
    safe_target = _safe_ts_ident(target_name) if target_name not in ("_item", "") else "_item"
    ann = _type_annotation(ctx, target_rt)
    if safe_target != "_item" and safe_target != "_":
        ctx.var_types[safe_target] = target_rt

    if isinstance(iter_plan, dict):
        plan_kind = _str(iter_plan, "kind")
        if plan_kind == "StaticRangeForPlan":
            _emit_static_range_for_plan(ctx, iter_plan, safe_target, ann, body)
            if len(orelse) > 0:
                _emit_body(ctx, orelse)
            return
        if plan_kind == "RuntimeIterForPlan":
            iter_node = iter_plan.get("iter_expr")
            iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"
            _emit(ctx, "for (const " + safe_target + " of " + iter_code + ") {")
            ctx.indent_level += 1
            _emit_body(ctx, body)
            ctx.indent_level -= 1
            _emit(ctx, "}")
            if len(orelse) > 0:
                _emit_body(ctx, orelse)
            return

    # Fallback: check direct iter
    iter_node = node.get("iter")
    if iter_node is None:
        iter_node = iter_plan
    iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"
    _emit(ctx, "for (const " + safe_target + " of " + iter_code + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")
    if len(orelse) > 0:
        _emit_body(ctx, orelse)


def _emit_static_range_for_plan(
    ctx: EmitContext,
    iter_plan: dict[str, JsonVal],
    target_code: str,
    ann: str,
    body: list[JsonVal],
) -> None:
    """Emit a StaticRangeForPlan as a C-style for loop."""
    start_node = iter_plan.get("start")
    stop_node = iter_plan.get("stop")
    step_node = iter_plan.get("step")
    range_mode = _str(iter_plan, "range_mode")

    start_code = _emit_expr(ctx, start_node) if isinstance(start_node, dict) else "0"
    stop_code = _emit_expr(ctx, stop_node) if isinstance(stop_node, dict) else "0"
    step_code = _emit_expr(ctx, step_node) if isinstance(step_node, dict) else "1"
    step_is_one = isinstance(step_node, dict) and _str(step_node, "kind") == "Constant" and step_node.get("value") == 1

    # When start expr mentions the target variable, use a temp to avoid mutation
    start_mentions_target = isinstance(start_node, dict) and (
        _str(start_node, "id") == target_code or _str(start_node, "repr") == target_code
    )
    if start_mentions_target:
        start_tmp = _next_temp(ctx, "start")
        _emit(ctx, "const " + start_tmp + " = " + start_code + ";")
        start_code = start_tmp

    def _is_negative_step(sn: JsonVal) -> bool:
        if not isinstance(sn, dict):
            return False
        kind = _str(sn, "kind")
        if kind == "Constant":
            v = sn.get("value")
            return isinstance(v, (int, float)) and v < 0
        if kind == "UnaryOp" and _str(sn, "op") == "USub":
            return True
        return False
    descending = range_mode == "descending" or _is_negative_step(step_node)

    if descending:
        cmp_op = " > "
    else:
        cmp_op = " < "

    if step_is_one and not descending:
        _emit(ctx, "for (let " + target_code + ann + " = " + start_code + ";" + target_code + cmp_op + stop_code + "; " + target_code + "++) {")
    else:
        _emit(ctx, "for (let " + target_code + ann + " = " + start_code + ";" + target_code + cmp_op + stop_code + "; " + target_code + " += " + step_code + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_static_range_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """StaticRangeForPlan at top-level body (legacy, should be wrapped in ForCore)."""
    # This shouldn't normally be at the top level, but handle it anyway
    target_node = node.get("target")
    body = _list(node, "body")
    target_name, target_rt = _for_target_name_and_type(target_node)
    safe_target = _safe_ts_ident(target_name) if target_name not in ("_item", "") else "_i"
    ann = _type_annotation(ctx, target_rt)
    if safe_target != "_i":
        ctx.var_types[safe_target] = target_rt
    _emit_static_range_for_plan(ctx, node, safe_target, ann, body)


def _emit_runtime_iter_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """RuntimeIterForPlan at top-level body (legacy, should be wrapped in ForCore)."""
    target_node = node.get("target")
    iter_node = node.get("iter_expr")
    if iter_node is None:
        iter_node = node.get("iter")
    body = _list(node, "body")

    target_name, target_rt = _for_target_name_and_type(target_node)
    safe_target = _safe_ts_ident(target_name) if target_name not in ("_item", "") else "_item"
    if safe_target != "_item":
        ctx.var_types[safe_target] = target_rt
    iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"

    _emit(ctx, "for (const " + safe_target + " of " + iter_code + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_with(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """With statement → context-manager protocol using __enter__/__exit__."""
    items = _list(node, "items")
    if len(items) == 0:
        items = [node]
    body = _list(node, "body")

    collected: list[tuple[str, dict]] = []
    _collect_assigns_from_block(body, collected)
    seen: set[str] = set()
    for name_raw, stmt in collected:
        name = _ts_symbol_name(ctx, name_raw)
        if name in ctx.var_types or name in seen or name == "_":
            continue
        seen.add(name)
        stmt_kind = _str(stmt, "kind")
        decl_type = ""
        if stmt_kind == "VarDecl":
            decl_type = _str(stmt, "resolved_type")
        elif stmt_kind in ("Name", "NameTarget"):
            decl_type = _str(stmt, "resolved_type")
        else:
            decl_type = _str(stmt, "decl_type")
            if decl_type in ("", "unknown"):
                decl_type = _str(stmt, "resolved_type")
        ctx.var_types[name] = decl_type
        ann = _type_annotation(ctx, decl_type)
        _emit(ctx, "let " + name + ann + ";")

    ctx_vars: list[tuple[str, str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        ctx_expr = item.get("context_expr")
        if not isinstance(ctx_expr, dict):
            continue
        ctx_code = _emit_expr(ctx, ctx_expr)
        ctx_tmp = _next_temp(ctx, "comp")
        _emit(ctx, "let " + ctx_tmp + " = " + ctx_code + ";")

        var_name = ""
        opt_var = item.get("optional_vars")
        if isinstance(opt_var, dict):
            var_name = _ts_symbol_name(ctx, _str(opt_var, "id"))
        if var_name == "":
            var_name = _ts_symbol_name(ctx, _str(item, "var_name"))
        if var_name != "":
            enter_type = _str(ctx_expr, "resolved_type")
            if var_name not in ctx.var_types:
                ctx.var_types[var_name] = enter_type
                ann = _type_annotation(ctx, enter_type)
                _emit(ctx, "let " + var_name + ann + " = " + ctx_tmp + ".__enter__();")
            else:
                _emit(ctx, var_name + " = " + ctx_tmp + ".__enter__();")
        else:
            _emit(ctx, ctx_tmp + ".__enter__();")
        ctx_vars.append((ctx_tmp, var_name, _str(ctx_expr, "resolved_type")))

    _emit(ctx, "try {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "} finally {")
    ctx.indent_level += 1
    for ctx_tmp, _, _ in reversed(ctx_vars):
        _emit(ctx, ctx_tmp + ".__exit__(null, null, null);")
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_type_alias(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    rt = _str(node, "value_type")
    if rt == "" or ctx.strip_types:
        return
    tt = ts_type(rt)
    _emit(ctx, "type " + _safe_ts_ident(name) + " = " + tt + ";")
    _emit_blank(ctx)


def _emit_break(ctx: EmitContext) -> None:
    _emit(ctx, "break;")


def _emit_continue(ctx: EmitContext) -> None:
    _emit(ctx, "continue;")


def _emit_stmt(ctx: EmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        return
    if _emit_common_stmt(ctx, node):
        return
    kind = _str(node, "kind")
    if kind == "AugAssign":
        _emit_aug_assign(ctx, node)
    elif kind == "ForCore":
        _emit_for_core(ctx, node)
    elif kind == "RuntimeIterForPlan":
        _emit_runtime_iter_for(ctx, node)
    elif kind == "StaticRangeForPlan":
        _emit_static_range_for(ctx, node)
    elif kind == "FunctionDef" or kind == "ClosureDef":
        _emit_function_def(ctx, node)
    elif kind == "ClassDef":
        _emit_class_def(ctx, node)
    elif kind in ("ImportFrom", "Import"):
        _emit_import_stmt(ctx, node)
    elif kind == "VarDecl":
        _emit_var_decl(ctx, node)
    elif kind == "Swap":
        _emit_swap(ctx, node)
    elif kind in ("MultiAssign", "TupleUnpack"):
        _emit_multi_assign(ctx, node)
    elif kind == "With":
        _emit_with(ctx, node)
    elif kind == "TypeAlias":
        _emit_type_alias(ctx, node)
    elif kind == "Break":
        _emit_break(ctx)
    elif kind == "Continue":
        _emit_continue(ctx)
    elif kind == "ErrorReturn":
        # native_throw style: no-op (errors are thrown, not returned)
        pass
    elif kind == "ErrorCheck":
        pass
    elif kind == "ErrorCatch":
        pass
    elif kind == "comment":
        text = _str(node, "text")
        if text != "":
            _emit(ctx, "// " + text)
    elif kind == "blank":
        _emit_blank(ctx)
    else:
        raise RuntimeError("unsupported_stmt_kind_ts: " + kind)


def _emit_body(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        _emit_stmt(ctx, stmt)


# ---------------------------------------------------------------------------
# Import emission
# ---------------------------------------------------------------------------

def _emit_import_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """Emit an import statement as an ES module import or skip for runtime modules."""
    kind = _str(node, "kind")
    if kind == "ImportFrom":
        module = _str(node, "module")
        if should_skip_module(module, ctx.mapping):
            return
        if module.startswith("typing") or module.startswith("__future__") or module.startswith("dataclasses"):
            return
        names = _list(node, "names")
        imported: list[str] = []
        reexported: list[str] = []
        for nm in names:
            if not isinstance(nm, dict):
                continue
            name = _str(nm, "name").strip("() \t")
            asname = _str(nm, "asname")
            if name == "" or name == "*":
                continue
            local = asname if asname != "" else name
            # Check if this name is a sub-module alias (e.g. from pytra.utils import png)
            resolved_sub_mod = ctx.import_alias_modules.get(local, "")
            if resolved_sub_mod != "" and resolved_sub_mod != module:
                # Sub-module import: emit as namespace star import if not skipped
                if not should_skip_module(resolved_sub_mod, ctx.mapping):
                    sub_mod_path = _module_id_to_path(resolved_sub_mod)
                    js_ext = ".js" if ctx.strip_types else ""
                    _emit(ctx, "import * as " + _safe_ts_ident(local) + " from \"" + sub_mod_path + js_ext + "\";")
                continue
            # `from X import Y as Y` (asname == name) is the Python re-export pattern
            if asname != "" and asname == name and not ctx.strip_types:
                reexported.append(_safe_ts_ident(name))
            elif asname != "":
                imported.append(name + " as " + _safe_ts_ident(asname))
            else:
                imported.append(_safe_ts_ident(name))
        mod_path = _module_id_to_path(module)
        ext = ".js" if ctx.strip_types else ""
        if len(reexported) > 0:
            _emit(ctx, "export { " + ", ".join(reexported) + " } from \"" + mod_path + ext + "\";")
        if len(imported) == 0:
            return
        _emit(ctx, "import { " + ", ".join(imported) + " } from \"" + mod_path + ext + "\";")
    elif kind == "Import":
        names = _list(node, "names")
        for nm in names:
            if not isinstance(nm, dict):
                continue
            name = _str(nm, "name")
            asname = _str(nm, "asname")
            if name == "":
                continue
            if should_skip_module(name, ctx.mapping):
                continue
            mod_path = _module_id_to_path(name)
            local = _safe_ts_ident(asname if asname != "" else name.rsplit(".", 1)[-1])
            js_ext = ".js" if ctx.strip_types else ""
            _emit(ctx, "import * as " + local + " from \"" + mod_path + js_ext + "\";")


def _module_id_to_path(module_id: str) -> str:
    """Convert a module ID like 'pytra.std.math' to a relative import path.

    Emitted files are named with underscores (pytra_std_math.ts), so import
    paths use underscores to match the flat output directory structure.
    """
    return "./" + module_id.replace(".", "_")


# ---------------------------------------------------------------------------
# Function definition emission
# ---------------------------------------------------------------------------

def _emit_function_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    return_type = _str(node, "return_type")
    body = _list(node, "body")
    decorators = _list(node, "decorators")
    is_closure = _str(node, "kind") == "ClosureDef"

    # Skip extern declarations
    for d in decorators:
        if isinstance(d, str) and d == "extern":
            return

    # When return_type is "None" (resolver default), check if body actually returns a value.
    # If so, use the value's resolved_type to avoid TypeScript void return mismatch.
    if return_type in ("None", "none"):
        for stmt in body:
            if isinstance(stmt, dict) and stmt.get("kind") == "Return":
                val = stmt.get("value")
                if isinstance(val, dict):
                    actual_rt = _str(val, "resolved_type")
                    if actual_rt and actual_rt not in ("None", "none", "void", "unknown", ""):
                        return_type = actual_rt
                        break

    is_staticmethod = False
    is_classmethod = False
    is_property = False
    for d in decorators:
        if isinstance(d, str):
            if d == "staticmethod":
                is_staticmethod = True
            elif d == "classmethod":
                is_classmethod = True
            elif d == "property":
                is_property = True

    # Translate Python special method names to TypeScript equivalents
    if name == "__init__" and ctx.current_class != "":
        fn_name = "constructor"
    elif name == "__str__" and ctx.current_class != "":
        fn_name = "toString"
    elif name == "__len__" and ctx.current_class != "":
        fn_name = "length"
    else:
        fn_name = _safe_ts_ident(name)
    saved_vars = dict(ctx.var_types)
    saved_ret = ctx.current_return_type
    ctx.current_return_type = return_type

    # Build parameter list
    params: list[str] = []
    for a in arg_order:
        a_str = a if isinstance(a, str) else ""
        # Skip 'self' always; skip 'cls' only for classmethods (first param is class receiver)
        if a_str == "self":
            continue
        if a_str == "cls" and is_classmethod:
            continue
        a_type_val = arg_types.get(a_str, "")
        a_type = a_type_val if isinstance(a_type_val, str) else ""
        safe_a = _safe_ts_ident(a_str)
        ctx.var_types[safe_a] = a_type
        ann = _type_annotation(ctx, a_type)
        params.append(safe_a + ann)

    # Handle varargs (*args) - becomes rest parameter ...args: T[]
    vararg_name_raw = _str(node, "vararg_name")
    if vararg_name_raw != "":
        vararg_type = _str(node, "vararg_type")
        safe_varg = _safe_ts_ident(vararg_name_raw)
        ctx.var_types[safe_varg] = vararg_type
        # vararg_type is list[T]; rest param is T[]
        if vararg_type.startswith("list[") and vararg_type.endswith("]"):
            elem_type = vararg_type[5:-1]
            varg_elem_ts = ts_type(elem_type)
        else:
            varg_elem_ts = ts_type(vararg_type) if vararg_type else "any"
        if ctx.strip_types:
            params.append("..." + safe_varg)
        else:
            params.append("..." + safe_varg + ": " + ts_array_type(varg_elem_ts))

    # Return type annotation (constructor has no return type annotation in TS)
    if fn_name == "constructor":
        ret_ann = ""
    else:
        ret_ann = _return_type_annotation(ctx, return_type)

    # Method in class context
    if ctx.current_class != "" and not is_staticmethod and not is_classmethod:
        if is_property:
            _emit(ctx, "get " + fn_name + "()" + ret_ann + " {")
        else:
            _emit(ctx, fn_name + "(" + ", ".join(params) + ")" + ret_ann + " {")
    elif ctx.current_class != "" and is_staticmethod:
        _emit(ctx, "static " + fn_name + "(" + ", ".join(params) + ")" + ret_ann + " {")
    elif ctx.current_class != "" and is_classmethod:
        _emit(ctx, "static " + fn_name + "(" + ", ".join(params) + ")" + ret_ann + " {")
    elif is_closure:
        # ClosureDef: arrow function assigned to variable
        _emit(ctx, "const " + fn_name + " = (" + ", ".join(params) + ")" + ret_ann + " => {")
    else:
        # Top-level functions: export them unless they start with _ (private convention)
        export_kw = "" if fn_name.startswith("_") else "export "
        _emit(ctx, export_kw + "function " + fn_name + "(" + ", ".join(params) + ")" + ret_ann + " {")

    ctx.indent_level += 1
    # For constructors in derived classes: inject super() if not already in body
    base_class = ctx.class_bases.get(ctx.current_class, "")
    if fn_name == "constructor" and ctx.current_class != "" and base_class != "":
        if not _is_exception_type_name(ctx, ctx.current_class) and not _is_exception_type_name(ctx, base_class):
            has_super_call = any(
                isinstance(s, dict) and isinstance(s.get("value"), dict)
                and "super" in s.get("value", {}).get("repr", "")
                for s in body
            )
            if not has_super_call:
                _emit(ctx, "super();")
    # Pre-declare variables first-assigned inside nested blocks (Python is function-scoped,
    # TypeScript `let` is block-scoped; hoisting ensures cross-block accessibility).
    _hoist_nested_declarations(ctx, body)
    _emit_body(ctx, body)
    # For abstract/stub methods (empty body, non-void return type): emit stub return
    if len(body) == 0 and fn_name != "constructor" and return_type not in ("None", "void", "", "never"):
        _emit(ctx, "return undefined as any;")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    if ctx.current_class == "":
        _emit_blank(ctx)

    ctx.var_types = saved_vars
    ctx.current_return_type = saved_ret


# ---------------------------------------------------------------------------
# Class definition emission
# ---------------------------------------------------------------------------

def _collect_class_fields(ctx: EmitContext, node: dict[str, JsonVal]) -> list[tuple[str, str]]:
    """Collect class fields from field_types or __init__ body."""
    fields: list[tuple[str, str]] = []
    field_types = _dict(node, "field_types")
    if len(field_types) > 0:
        for fname, ftype in field_types.items():
            if isinstance(fname, str) and isinstance(ftype, str) and fname != "":
                fields.append((fname, ftype))
        return fields
    # Scan AnnAssign in class body (dataclass and regular classes)
    body = _list(node, "body")
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        if sk == "AnnAssign":
            target_val = stmt.get("target")
            ft_name = ""
            if isinstance(target_val, dict):
                ft_name = _str(target_val, "id")
            elif isinstance(target_val, str):
                ft_name = target_val
            frt = _str(stmt, "decl_type")
            if frt == "":
                frt = _str(stmt, "resolved_type")
            if ft_name != "" and frt != "":
                fields.append((ft_name, frt))
    return fields


def _emit_class_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    base = _str(node, "base")
    body = _list(node, "body")
    is_dataclass = _bool(node, "dataclass")

    ctx.class_names.add(name)
    if base != "":
        ctx.class_bases[name] = base

    # Check for enum
    enum_base = ctx.enum_bases.get(name, "")
    if enum_base in ("Enum", "IntEnum", "IntFlag"):
        _emit_enum_class(ctx, node, name)
        return

    fields = _collect_class_fields(ctx, node)

    # Collect static/instance methods in first pass
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        if sk not in ("FunctionDef", "ClosureDef"):
            continue
        mname = _str(stmt, "name")
        decorators = _list(stmt, "decorators")
        is_static = False
        for d in decorators:
            if isinstance(d, str) and d == "staticmethod":
                is_static = True
                break
        if is_static:
            ctx.class_static_methods.setdefault(name, set()).add(mname)
        else:
            ctx.class_instance_methods.setdefault(name, {})[mname] = stmt

    # Save class context
    saved_class = ctx.current_class
    ctx.current_class = name

    # Emit class declaration
    extends = " extends " + _safe_ts_ident(base) if base != "" and not _is_exception_type_name(ctx, name) else ""
    if _is_exception_type_name(ctx, name):
        extends = " extends Error"
    # Export class unless nested (ctx.current_class was "" before we set it above)
    export_kw = "" if saved_class != "" else "export "
    _emit(ctx, export_kw + "class " + _safe_ts_ident(name) + extends + " {")
    ctx.indent_level += 1

    # Collect class-level variables with initial values → emit as static fields
    # (Python class variables accessed as ClassName.var → TS static fields)
    # For dataclasses, AnnAssign with value = field default, NOT static
    static_field_names: set[str] = set()
    if not is_dataclass:
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            if _str(stmt, "kind") == "AnnAssign" and stmt.get("value") is not None:
                target_val = stmt.get("target")
                fname = ""
                if isinstance(target_val, dict):
                    fname = _str(target_val, "id")
                elif isinstance(target_val, str):
                    fname = target_val
                if fname != "":
                    static_field_names.add(fname)

    # Collect dataclass field defaults: {name: default_value_node}
    dataclass_defaults: dict[str, JsonVal] = {}
    if is_dataclass:
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            if _str(stmt, "kind") == "AnnAssign" and stmt.get("value") is not None:
                target_val = stmt.get("target")
                fname = ""
                if isinstance(target_val, dict):
                    fname = _str(target_val, "id")
                elif isinstance(target_val, str):
                    fname = target_val
                if fname != "":
                    dataclass_defaults[fname] = stmt.get("value")

    # Emit instance field declarations (skip static ones)
    if not ctx.strip_types and len(fields) > 0:
        instance_fields = [(fn, ft) for fn, ft in fields if fn not in static_field_names]
        for fname, ftype in instance_fields:
            ann = _type_annotation(ctx, ftype)
            _emit(ctx, fname + "!" + ann + ";")
        if len(instance_fields) > 0:
            _emit_blank(ctx)

    # Check if body has an explicit __init__ method
    has_init = any(
        isinstance(s, dict) and _str(s, "kind") in ("FunctionDef", "ClosureDef") and _str(s, "name") == "__init__"
        for s in body
    )

    # Emit body (methods, AnnAssign at class level)
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        if sk in ("FunctionDef", "ClosureDef"):
            _emit_function_def(ctx, stmt)
        elif sk == "AnnAssign":
            # Class-level AnnAssign with initial value → static field (unless dataclass)
            # Dataclass fields with defaults are handled in synthesized constructor
            # Class-level AnnAssign without initial value → skip (already emitted as instance field)
            if stmt.get("value") is not None and not is_dataclass:
                target_val = stmt.get("target")
                fname = ""
                if isinstance(target_val, dict):
                    fname = _str(target_val, "id")
                elif isinstance(target_val, str):
                    fname = target_val
                frt = _str(stmt, "decl_type")
                if frt == "":
                    frt = _str(stmt, "annotation")
                val_code = _emit_expr(ctx, stmt.get("value"))
                ann = _type_annotation(ctx, frt)
                _emit(ctx, "static " + _safe_ts_ident(fname) + ann + " = " + val_code + ";")
        elif sk in ("comment", "blank"):
            _emit_stmt(ctx, stmt)
        elif sk == "ClassDef":
            _emit_class_def(ctx, stmt)
        elif sk == "Pass":
            pass
        elif sk == "Assign":
            # Class-level Assign → static field
            target_node = stmt.get("target")
            if isinstance(target_node, dict) and _str(target_node, "kind") == "Name":
                tname = _ts_symbol_name(ctx, _str(target_node, "id"))
                val_node = stmt.get("value")
                val_code = _emit_expr(ctx, val_node)
                rt = _str(target_node, "resolved_type")
                ann = _type_annotation(ctx, rt)
                _emit(ctx, "static " + tname + ann + " = " + val_code + ";")
            else:
                _emit_stmt(ctx, stmt)
        else:
            _emit_stmt(ctx, stmt)

    # Synthesize constructor for dataclass if no __init__ exists
    if not has_init and not _is_exception_type_name(ctx, name):
        if is_dataclass and len(fields) > 0:
            # Build constructor params (for dataclasses: all fields)
            ctor_params: list[str] = []
            if is_dataclass:
                for fname, ftype in fields:
                    ann = _type_annotation(ctx, ftype)
                    default_node = dataclass_defaults.get(fname)
                    if default_node is not None:
                        default_val = _emit_expr(ctx, default_node)
                        ctor_params.append(_safe_ts_ident(fname) + ann + " = " + default_val)
                    else:
                        ctor_params.append(_safe_ts_ident(fname) + ann)
            _emit(ctx, "constructor(" + ", ".join(ctor_params) + ") {")
            ctx.indent_level += 1
            if base != "" and not _is_exception_type_name(ctx, base):
                _emit(ctx, "super();")
            # For dataclasses: assign fields
            if is_dataclass:
                for fname, _ in fields:
                    _emit(ctx, "this." + _safe_ts_ident(fname) + " = " + _safe_ts_ident(fname) + ";")
            ctx.indent_level -= 1
            _emit(ctx, "}")

    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)

    ctx.current_class = saved_class


def _emit_enum_class(ctx: EmitContext, node: dict[str, JsonVal], name: str) -> None:
    enum_members = ctx.enum_members.get(name, {})
    body = _list(node, "body")

    _emit(ctx, "const " + _safe_ts_ident(name) + " = {")
    ctx.indent_level += 1
    # Collect member assignments from body
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        if sk in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            value = stmt.get("value")
            member_name = ""
            if isinstance(target, dict):
                member_name = _str(target, "id")
            elif isinstance(target, str):
                member_name = target
            if member_name != "" and isinstance(value, dict):
                val_code = _emit_expr(ctx, value)
                _emit(ctx, _safe_ts_ident(member_name) + ": " + val_code + ",")
    ctx.indent_level -= 1
    _emit(ctx, "};")
    if not ctx.strip_types:
        _emit(ctx, "type " + _safe_ts_ident(name) + " = number;")
    _emit_blank(ctx)


# ---------------------------------------------------------------------------
# Module-level emission
# ---------------------------------------------------------------------------

def _collect_module_class_info(ctx: EmitContext, body: list[JsonVal]) -> None:
    """First pass: collect all class names, bases, enum types, method info, and vararg functions."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        # Collect vararg functions
        if sk in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            vararg_name = _str(stmt, "vararg_name")
            if fn_name != "" and vararg_name != "":
                ctx.vararg_functions.add(fn_name)
        if sk == "ClassDef":
            class_name = _str(stmt, "name")
            ctx.class_names.add(class_name)
            base = _str(stmt, "base")
            if base != "":
                ctx.class_bases[class_name] = base
            if base in ("Enum", "IntEnum", "IntFlag"):
                ctx.enum_bases[class_name] = base
            field_types = _dict(stmt, "field_types")
            class_fields: dict[str, str] = {}
            for fname, ftype in field_types.items():
                if isinstance(fname, str) and isinstance(ftype, str):
                    class_fields[fname] = ftype
            ctx.class_fields[class_name] = class_fields
            # Collect enum members
            enum_members: dict[str, dict[str, JsonVal]] = {}
            for sub_stmt in _list(stmt, "body"):
                if not isinstance(sub_stmt, dict):
                    continue
                sub_sk = _str(sub_stmt, "kind")
                if sub_sk in ("AnnAssign", "Assign"):
                    target = sub_stmt.get("target")
                    mname = ""
                    if isinstance(target, dict):
                        mname = _str(target, "id")
                    elif isinstance(target, str):
                        mname = target
                    if mname != "":
                        enum_members[mname] = sub_stmt
            ctx.enum_members[class_name] = enum_members


def _emit_module_header(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Emit top-level import statements."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("ImportFrom", "Import"):
            _emit_import_stmt(ctx, stmt)


def emit_ts_module(east3_doc: dict[str, JsonVal], *, strip_types: bool = False) -> str:
    """Emit a complete TypeScript (or JavaScript) source file from an EAST3 document.

    Args:
        east3_doc: linked EAST3 JSON dict with meta.linked_program_v1.
        strip_types: If True, emit JavaScript (no type annotations).

    Returns:
        TypeScript/JavaScript source code string, or empty string if module should be skipped.
    """
    meta = _dict(east3_doc, "meta")
    module_id = ""

    emit_ctx_meta = _dict(meta, "emit_context")
    if emit_ctx_meta:
        module_id = _str(emit_ctx_meta, "module_id")
    if module_id == "":
        module_id = _str(meta, "module_id")
    lp = _dict(meta, "linked_program_v1")
    if module_id == "" and lp:
        module_id = _str(lp, "module_id")

    if module_id != "":
        expand_cross_module_defaults([east3_doc])

    # Load runtime mapping
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "ts" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Skip runtime modules
    if should_skip_module(module_id, mapping):
        return ""

    # Load module-level renamed symbols (e.g. main → __pytra_main)
    renamed_symbols_raw = east3_doc.get("renamed_symbols")
    renamed_symbols: dict[str, str] = {}
    if isinstance(renamed_symbols_raw, dict):
        for orig, rn in renamed_symbols_raw.items():
            if isinstance(orig, str) and isinstance(rn, str):
                renamed_symbols[orig] = rn

    is_type_id_table = (module_id == "pytra.built_in.type_id_table")

    ctx = EmitContext(
        module_id=module_id,
        source_path=_str(east3_doc, "source_path"),
        is_entry=_bool(emit_ctx_meta, "is_entry") if emit_ctx_meta else False,
        strip_types=strip_types,
        mapping=mapping,
        renamed_symbols=renamed_symbols,
        is_type_id_table=is_type_id_table,
    )

    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")

    # Collect type info from linked_program_v1
    if len(lp) > 0:
        type_info_table = _dict(lp, "type_info_table_v1")
        for fqcn, info in type_info_table.items():
            if not isinstance(fqcn, str) or not isinstance(info, dict):
                continue
            type_id_val = info.get("id")
            if isinstance(type_id_val, int):
                ctx.exception_type_ids[fqcn] = type_id_val
                ctx.class_type_ids[fqcn] = type_id_val
                ctx.tid_const_types[_tid_const_name(fqcn)] = fqcn.rsplit(".", 1)[-1]

    ctx.import_alias_modules = build_import_alias_map(meta)
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)

    # First pass: collect class info
    _collect_module_class_info(ctx, body)

    # Emit imports
    _emit_module_header(ctx, body)

    # Emit module body (skip imports, already emitted)
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("ImportFrom", "Import"):
            continue
        _emit_stmt(ctx, stmt)

    # Emit main guard
    if len(main_guard) > 0:
        _emit_blank(ctx)
        _emit(ctx, "// main")
        _emit_body(ctx, main_guard)

    # Detect built-in runtime symbols used in the output and prepend import
    body_text = "\n".join(ctx.lines)
    used_builtins: list[str] = []
    for sym in sorted(_BUILTIN_RUNTIME_SYMBOLS):
        sym_used = sym + "(" in body_text or sym + ";" in body_text
        if not sym_used:
            sym_used = sym + "," in body_text or sym + "]" in body_text
        if not sym_used:
            sym_used = sym + ")" in body_text or sym + " " in body_text
        if not sym_used:
            sym_used = sym + "|" in body_text or sym + "\n" in body_text
        if not sym_used:
            sym_used = sym + "." in body_text
        if sym_used:
            used_builtins.append(sym)

    # Also include native symbols resolved via runtime_imports
    # (e.g. save_gif, grayscale_palette, perf_counter from skipped modules not in _BUILTIN_RUNTIME_SYMBOLS)
    used_set = set(used_builtins)
    for native_sym in sorted(set(ctx.runtime_imports.values())):
        if native_sym not in used_set:
            sym_used = native_sym + "(" in body_text or native_sym + ";" in body_text
            if not sym_used:
                sym_used = native_sym + "," in body_text or native_sym + "]" in body_text
            if not sym_used:
                sym_used = native_sym + ")" in body_text or native_sym + " " in body_text
            if not sym_used:
                sym_used = native_sym + "|" in body_text or native_sym + "\n" in body_text
            if not sym_used:
                sym_used = native_sym + "." in body_text
            if sym_used:
                used_builtins.append(native_sym)
                used_set.add(native_sym)

    js_ext = ".js" if strip_types else ""
    preamble_lines: list[str] = []
    if len(used_builtins) > 0:
        preamble_lines.append(
            "import { " + ", ".join(used_builtins) + " } from \"./" + _BUILTIN_RUNTIME_MODULE + js_ext + "\";"
        )

    if len(preamble_lines) > 0:
        output = "\n".join(preamble_lines) + "\n" + body_text.rstrip() + "\n"
    else:
        output = body_text.rstrip() + "\n"
    output = output.replace("py__init__(super(), ", "super(")
    if strip_types:
        output = output.replace(" as unknown as any", "")
        output = output.replace(" as string | number | boolean | null", "")
        output = output.replace(" as any", "")
    return output
