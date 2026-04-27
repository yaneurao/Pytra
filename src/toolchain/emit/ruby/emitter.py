"""EAST3 -> Ruby source code emitter.

Ruby emitter は CommonRenderer + override 構成。
Ruby 固有のノード（クラス、def/end、require 等）のみ override として実装する。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.ruby.types import (
    ruby_type, ruby_zero_value, ruby_exception_class,
    ruby_is_builtin_exception, _safe_ruby_ident, _split_generic_args,
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
    # Variable types in current scope
    var_types: dict[str, str] = field(default_factory=dict)
    # Current function return type
    current_return_type: str = ""
    # Runtime mapping (from mapping.json)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    # Import alias -> module_id map
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
    function_names: set[str] = field(default_factory=set)
    function_varargs: set[str] = field(default_factory=set)
    enum_bases: dict[str, str] = field(default_factory=dict)
    enum_members: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    # Current class context
    current_class: str = ""
    # Exception type IDs
    exception_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    # Module-level symbol renames
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    # Per-module temp counter
    temp_counter: int = 0
    # Whether this module is pytra.built_in.type_id_table
    is_type_id_table: bool = False
    # Current exception variable
    current_exc_var: str = ""
    # Declared variables in current scope (for avoiding re-declaration)
    declared_vars: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _emit(ctx: EmitContext, line: str) -> None:
    ctx.lines.append("  " * ctx.indent_level + line)


def _emit_blank(ctx: EmitContext) -> None:
    ctx.lines.append("")


def _indent(ctx: EmitContext) -> str:
    return "  " * ctx.indent_level


def _str(node: dict[str, JsonVal], key: str) -> str:
    v = node.get(key, "")
    return v if isinstance(v, str) else ""


def _bool(node: dict[str, JsonVal], key: str) -> bool:
    v = node.get(key, False)
    return v if isinstance(v, bool) else False


def _int(node: dict[str, JsonVal], key: str) -> int:
    v = node.get(key, 0)
    return v if isinstance(v, int) else 0


def _list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    v = node.get(key, [])
    return v if isinstance(v, list) else []


def _dict(node: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    v = node.get(key, {})
    return v if isinstance(v, dict) else {}


def _next_temp(ctx: EmitContext, prefix: str = "tmp") -> str:
    ctx.temp_counter += 1
    return "__" + prefix + "_" + str(ctx.temp_counter)


def _ruby_symbol_name(ctx: EmitContext, name: str) -> str:
    """Resolve a symbol name with module-level renames."""
    renamed = ctx.renamed_symbols.get(name, "")
    if renamed != "":
        return _safe_ruby_ident(renamed)
    return _safe_ruby_ident(name)


def _ruby_constant_name(name: str) -> str:
    trimmed = name.lstrip("_")
    safe_name = _safe_ruby_ident(trimmed)
    if safe_name == "":
        return "PytraConst"
    if not safe_name[0].isupper():
        return safe_name
    return safe_name


def _is_ruby_constant_like(name: str) -> bool:
    trimmed = name.lstrip("_")
    return trimmed != "" and trimmed[0].isupper()


def _ruby_local_name(ctx: EmitContext, name: str) -> str:
    safe_name = _ruby_symbol_name(ctx, name)
    if ctx.current_return_type != "" and safe_name != "" and safe_name[0].isupper():
        return "_" + safe_name
    if name in ctx.var_types and safe_name != "" and safe_name[0].isupper():
        return "_" + safe_name
    return safe_name


def _ruby_class_name(name: str) -> str:
    safe_name = _safe_ruby_ident(name).lstrip("_")
    if safe_name == "":
        return "PytraAnon"
    if not safe_name[0].isupper():
        return safe_name[0].upper() + safe_name[1:]
    return safe_name


def _lookup_class_field(ctx: EmitContext, class_name: str, attr: str) -> str:
    cur = class_name
    while cur != "":
        field_map = ctx.class_fields.get(cur, {})
        field_type = field_map.get(attr, "")
        if field_type != "":
            return field_type
        cur = ctx.class_bases.get(cur, "")
    return ""


def _should_skip_module_ruby(module_id: str, mapping: RuntimeMapping) -> bool:
    if module_id in ("pytra.built_in.error", "pytra.types", "pytra.std.extern", "pytra.std.template"):
        return True
    return should_skip_module(module_id, mapping)


def _is_type_only_import_from(module: str, names: list[JsonVal]) -> bool:
    if module != "pytra.std.json":
        return False
    imported_names: list[str] = []
    for item in names:
        if isinstance(item, dict):
            imported_names.append(_str(item, "name"))
        elif isinstance(item, str):
            imported_names.append(item)
    return len(imported_names) > 0 and all(name == "JsonVal" for name in imported_names)


def _is_function_symbol(ctx: EmitContext, name: str) -> bool:
    if name in ctx.function_names:
        return True
    resolved_name = _ruby_symbol_name(ctx, name)
    for fn_name in ctx.function_names:
        if _ruby_symbol_name(ctx, fn_name) == resolved_name:
            return True
    return False


def _is_exception_type_name(ctx: EmitContext, name: str) -> bool:
    if ruby_is_builtin_exception(name):
        return True
    # Check if its base is an exception type
    base = ctx.class_bases.get(name, "")
    if base == "":
        return False
    return _is_exception_type_name(ctx, base)


def _is_super_receiver(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    if _str(node, "kind") != "Call":
        return False
    func = node.get("func")
    if not isinstance(func, dict):
        return False
    return _str(func, "kind") == "Name" and _str(func, "id") == "super"


def _render_super_call(args: list[str]) -> str:
    return "super" + "(" + ", ".join(args) + ")"


def _ruby_method_name(name: str) -> str:
    method_map: dict[str, str] = {
        "__init__": "initialize",
        "__str__": "to_s",
        "__len__": "length",
        "__repr__": "inspect",
        "__eq__": "==",
        "__lt__": "<",
        "__le__": "<=",
        "__gt__": ">",
        "__ge__": ">=",
        "__hash__": "hash",
        "__contains__": "include?",
        "__getitem__": "[]",
        "__setitem__": "[]=",
    }
    if name in method_map:
        return method_map[name]
    return _safe_ruby_ident(name)


def _target_binding_name(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return "_item"
    kind = _str(node, "kind")
    if kind == "Name" or kind == "NameTarget":
        name = _str(node, "id")
        return _safe_ruby_ident(name) if name != "" else "_item"
    if kind == "Tuple" or kind == "TupleTarget":
        elems = _list(node, "elements")
        names: list[str] = []
        for elem in elems:
            names.append(_target_binding_name(elem))
        return ", ".join(names) if len(names) > 0 else "_item"
    return "_item"


# ---------------------------------------------------------------------------
# Expression emission
# ---------------------------------------------------------------------------

def _emit_expr(ctx: EmitContext, node: JsonVal) -> str:
    """Emit an expression and return Ruby code string."""
    if not isinstance(node, dict):
        return "nil"
    kind = _str(node, "kind")
    if kind == "Constant":
        return _emit_constant(ctx, node)
    if kind == "Name":
        return _emit_name(ctx, node)
    if kind == "Attribute":
        return _emit_attribute(ctx, node)
    if kind == "Call":
        return _emit_call(ctx, node)
    if kind == "BinOp":
        return _emit_binop(ctx, node)
    if kind == "UnaryOp":
        return _emit_unaryop(ctx, node)
    if kind == "BoolOp":
        return _emit_boolop(ctx, node)
    if kind == "Compare":
        return _emit_compare(ctx, node)
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
        return "__pytra_str(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjLen":
        arg = node.get("value")
        return "__pytra_len(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjBool":
        arg = node.get("value")
        return "__pytra_truthy(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjTruthy":
        arg = node.get("value")
        return "__pytra_truthy(" + _emit_expr(ctx, arg) + ")"
    if kind == "ListComp":
        return _emit_list_comp(ctx, node)
    if kind == "DictComp":
        return _emit_dict_comp(ctx, node)
    if kind == "SetComp":
        return _emit_set_comp(ctx, node)
    if kind == "GeneratorExp":
        return _emit_list_comp(ctx, node)
    if kind == "RangeExpr":
        return _emit_range_expr(ctx, node)
    if kind == "Starred":
        inner = node.get("value")
        return "*" + _emit_expr(ctx, inner)
    # Fallback: repr
    repr_val = _str(node, "repr")
    if repr_val != "":
        return repr_val
    return "nil"


def _emit_constant(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'
    if isinstance(value, float):
        s = repr(value)
        if s == "inf":
            return "Float::INFINITY"
        if s == "-inf":
            return "-Float::INFINITY"
        if s == "nan":
            return "Float::NAN"
        return s
    return str(value)


def _emit_name(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "":
        name = _str(node, "repr")
    if name == "self" and ctx.current_class != "":
        return "self"
    if name == "None":
        return "nil"
    if name == "True":
        return "true"
    if name == "False":
        return "false"
    if name == "super":
        return "super"
    if name in ctx.runtime_imports:
        return ctx.runtime_imports[name]
    if name in ctx.class_names:
        return _ruby_class_name(name)
    local_name = _ruby_local_name(ctx, name)
    if name in ctx.var_types or local_name in ctx.var_types:
        return local_name
    if _is_ruby_constant_like(name):
        return _ruby_constant_name(name)
    if _is_function_symbol(ctx, name):
        return "method(:" + _ruby_symbol_name(ctx, name) + ")"
    return local_name


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr = _str(node, "attr")
    # Handle 'self.field' -> '@field'
    if isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
        if attr.startswith("_"):
            return "@" + attr
        field_type = _lookup_class_field(ctx, ctx.current_class, attr)
        if attr in ctx.class_property_methods.get(ctx.current_class, set()) or field_type == "":
            return _ruby_method_name(attr)
        return "@" + attr
    # Handle module constant access (e.g. math.pi, sys.argv)
    if isinstance(owner_node, dict):
        owner_rt = _str(owner_node, "resolved_type")
        owner_id = _str(owner_node, "id")
        is_module = owner_rt == "module" or owner_id in ctx.import_alias_modules
        if is_module:
            mod_id = _str(node, "runtime_module_id")
            if mod_id == "" or not _should_skip_module_ruby(mod_id, ctx.mapping):
                mod_id = ctx.import_alias_modules.get(owner_id, "")
            runtime_symbol = _str(node, "runtime_symbol")
            if runtime_symbol == "":
                runtime_symbol = attr
            if mod_id != "":
                mod_short = mod_id.rsplit(".", 1)[-1]
                qualified_key = mod_short + "." + runtime_symbol
                if qualified_key in ctx.mapping.calls:
                    return ctx.mapping.calls[qualified_key]
            namespace_expr = ctx.mapping.module_namespace_exprs.get(mod_id, "")
            if namespace_expr != "":
                return namespace_expr + "." + _ruby_method_name(attr)
            if _should_skip_module_ruby(mod_id, ctx.mapping):
                resolved = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping, module_id=mod_id)
                return resolved
    # Property access
    if isinstance(owner_node, dict) and _str(owner_node, "id") != "":
        owner_id = _str(owner_node, "id")
        # Class.static_method / Class.member
        if owner_id in ctx.class_names:
            if len(attr) > 0 and attr[0].isupper():
                return _ruby_class_name(owner_id) + "::" + attr
            return _ruby_class_name(owner_id) + "." + _ruby_method_name(attr)
    owner = _emit_expr(ctx, owner_node)
    if attr == "__name__":
        return owner + ".name"
    if len(attr) > 0 and attr[0].isupper():
        return owner + "::" + attr
    return owner + "." + _ruby_method_name(attr)


def _emit_subscript(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    slice_node = node.get("slice")
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "0"
        upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else owner + ".length"
        return "__pytra_slice(" + owner + ", " + lower_code + ", " + upper_code + ")"
    slice_code = _emit_expr(ctx, slice_node)
    # For dicts/Hashes: use [] directly
    is_dict_type = owner_rt.startswith("dict[") or owner_rt == "dict"
    if is_dict_type:
        return owner + "[" + slice_code + "]"
    return "__pytra_get_index(" + owner + ", " + slice_code + ")"


def _emit_binop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left = node.get("left")
    right = node.get("right")
    op = _str(node, "op")
    left_code = _emit_expr(ctx, left)
    right_code = _emit_expr(ctx, right)
    # Handle casts
    casts = _list(node, "casts")
    for cast in casts:
        if isinstance(cast, dict):
            on = _str(cast, "on")
            to = _str(cast, "to")
            if not to.startswith("float"):
                continue
            if on == "left":
                left_code = left_code + ".to_f"
            elif on == "right":
                right_code = right_code + ".to_f"
    if op == "FloorDiv":
        return "__pytra_floordiv(" + left_code + ", " + right_code + ")"
    if op == "Div":
        return "__pytra_div(" + left_code + ", " + right_code + ")"
    if op == "Pow":
        return left_code + " ** " + right_code
    if op == "Mod":
        return left_code + " % " + right_code
    op_map: dict[str, str] = {
        "Add": "+", "Sub": "-", "Mult": "*",
        "BitAnd": "&", "BitOr": "|", "BitXor": "^",
        "LShift": "<<", "RShift": ">>",
    }
    op_str = op_map.get(op, "+")
    # Preserve EAST3 grouping explicitly so Ruby precedence cannot reorder.
    return "(" + left_code + " " + op_str + " " + right_code + ")"


def _emit_unaryop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    op = _str(node, "op")
    operand = node.get("operand")
    operand_code = _emit_expr(ctx, operand)
    if op == "USub":
        return "-" + operand_code
    if op == "UAdd":
        return "+" + operand_code
    if op == "Not":
        return "!" + _emit_truthy(ctx, operand)
    if op == "Invert":
        return "~" + operand_code
    return operand_code


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    op = _str(node, "op")
    values = _list(node, "values")
    if len(values) == 0:
        return "nil"
    expr_code = _emit_expr(ctx, values[0])
    for v in values[1:]:
        rhs_code = _emit_expr(ctx, v)
        if op == "And":
            expr_code = "(__pytra_truthy(" + expr_code + ") ? " + rhs_code + " : " + expr_code + ")"
        else:
            expr_code = "(__pytra_truthy(" + expr_code + ") ? " + expr_code + " : " + rhs_code + ")"
    return expr_code


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left = node.get("left")
    ops = _list(node, "ops")
    comparators = _list(node, "comparators")
    left_code = _emit_expr(ctx, left)
    parts: list[str] = []
    prev_code = left_code
    for i in range(len(ops)):
        op = ops[i] if isinstance(ops[i], str) else ""
        comp = comparators[i] if i < len(comparators) else None
        comp_code = _emit_expr(ctx, comp)
        if op == "In":
            parts.append("__pytra_contains(" + comp_code + ", " + prev_code + ")")
        elif op == "NotIn":
            parts.append("!__pytra_contains(" + comp_code + ", " + prev_code + ")")
        elif op == "Is":
            parts.append(prev_code + ".equal?(" + comp_code + ")")
        elif op == "IsNot":
            parts.append("!" + prev_code + ".equal?(" + comp_code + ")")
        else:
            op_map: dict[str, str] = {
                "Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=",
                "Gt": ">", "GtE": ">=",
            }
            op_str = op_map.get(op, "==")
            parts.append(prev_code + " " + op_str + " " + comp_code)
        prev_code = comp_code
    if len(parts) == 1:
        return parts[0]
    return " && ".join(parts)


def _emit_list_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    if len(elements) == 0:
        return "[]"
    parts: list[str] = []
    for e in elements:
        parts.append(_emit_expr(ctx, e))
    return "[" + ", ".join(parts) + "]"


def _emit_dict_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    keys = _list(node, "keys")
    values = _list(node, "values")
    if len(keys) == 0 and len(values) == 0:
        entries = _list(node, "entries")
        if len(entries) > 0:
            parts_from_entries: list[str] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                k_code = _emit_expr(ctx, entry.get("key"))
                v_code = _emit_expr(ctx, entry.get("value"))
                parts_from_entries.append(k_code + " => " + v_code)
            if len(parts_from_entries) > 0:
                return "{" + ", ".join(parts_from_entries) + "}"
    if len(keys) == 0:
        return "{}"
    parts: list[str] = []
    for i in range(len(keys)):
        k = keys[i] if i < len(keys) else None
        v = values[i] if i < len(values) else None
        k_code = _emit_expr(ctx, k)
        v_code = _emit_expr(ctx, v)
        parts.append(k_code + " => " + v_code)
    return "{" + ", ".join(parts) + "}"


def _emit_set_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    if len(elements) == 0:
        return "Set.new"
    parts: list[str] = []
    for e in elements:
        parts.append(_emit_expr(ctx, e))
    return "Set.new([" + ", ".join(parts) + "])"


def _emit_tuple_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    if len(elements) == 0:
        return "[]"
    parts: list[str] = []
    for e in elements:
        parts.append(_emit_expr(ctx, e))
    return "__pytra_tuple([" + ", ".join(parts) + "])"


def _emit_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test = node.get("test")
    body = node.get("body")
    orelse = node.get("orelse")
    test_code = "__pytra_truthy(" + _emit_expr(ctx, test) + ")"
    body_code = _emit_expr(ctx, body)
    orelse_code = _emit_expr(ctx, orelse)
    return "(" + test_code + " ? " + body_code + " : " + orelse_code + ")"


def _emit_fstring(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    parts: list[str] = []
    for v in values:
        if not isinstance(v, dict):
            continue
        kind = _str(v, "kind")
        if kind == "Constant":
            val = v.get("value")
            if isinstance(val, str):
                parts.append(val.replace("\\", "\\\\").replace('"', '\\"').replace("#", "\\#"))
            else:
                parts.append(str(val) if val is not None else "")
        elif kind == "FormattedValue":
            inner = v.get("value")
            fmt_spec = _str(v, "format_spec")
            inner_code = _emit_expr(ctx, inner)
            if fmt_spec != "":
                parts.append("#{sprintf(\"%" + fmt_spec + "\", " + inner_code + ")}")
            else:
                parts.append("#{" + inner_code + "}")
        else:
            parts.append("#{" + _emit_expr(ctx, v) + "}")
    return '"' + "".join(parts) + '"'


def _emit_truthy(ctx: EmitContext, node: JsonVal) -> str:
    return "__pytra_truthy(" + _emit_expr(ctx, node) + ")"


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    args = _list(node, "args")
    body = node.get("body")
    params: list[str] = []
    for a in args:
        if isinstance(a, dict):
            params.append(_safe_ruby_ident(_str(a, "arg")))
        elif isinstance(a, str):
            params.append(_safe_ruby_ident(a))
    body_code = _emit_expr(ctx, body)
    if len(params) > 0:
        return "lambda { |" + ", ".join(params) + "| " + body_code + " }"
    return "lambda { " + body_code + " }"


def _emit_isinstance(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    type_node = node.get("type")
    value_code = _emit_expr(ctx, value)
    type_name = ""
    nominal = _dict(node, "nominal_adt_test_v1")
    family_name = nominal.get("family_name")
    if isinstance(family_name, str):
        type_name = family_name
    if type_name == "" and isinstance(type_node, dict):
        type_name = _str(type_node, "id")
        if type_name == "":
            type_name = _str(type_node, "repr")
    if type_name == "":
        type_name = _str(node, "expected_type_name")
    if type_name == "":
        type_name = _str(node, "type_name")
    if type_name == "":
        expected_node = node.get("expected_type_id")
        if isinstance(expected_node, dict):
            type_name = _str(expected_node, "type_object_of")
            if type_name == "":
                type_name = _str(expected_node, "family_name")
            if type_name == "":
                type_name = _str(expected_node, "id")
            if type_name == "":
                type_name = _str(expected_node, "repr")
    # Map to Ruby type check
    type_map: dict[str, str] = {
        "int": "Integer", "int64": "Integer", "float": "Float", "float64": "Float",
        "str": "String", "bool": "TrueClass", "list": "Array",
        "dict": "Hash", "set": "Set", "tuple": "Array",
    }
    ruby_cls = type_map.get(type_name, type_name)
    return value_code + ".is_a?(" + ruby_cls + ")"


def _emit_unbox(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    return _emit_expr(ctx, value)


def _emit_box(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    return _emit_expr(ctx, value)


def _emit_list_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = node.get("elt")
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "[]"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "[]"
    target = gen.get("target")
    iter_node = gen.get("iter")
    ifs = _list(gen, "ifs")
    safe_target = _target_binding_name(target)
    if safe_target == "":
        safe_target = "_item"

    # Check if iter is a RangeExpr -> use range
    iter_code = _emit_expr(ctx, iter_node)
    if isinstance(iter_node, dict) and _str(iter_node, "resolved_type") == "str":
        iter_code = "(" + iter_code + ").each_char"
    elt_code = _emit_expr(ctx, elt)

    if len(ifs) > 0:
        cond_parts: list[str] = []
        for cond in ifs:
            cond_parts.append(_emit_expr(ctx, cond))
        cond_code = " && ".join(cond_parts)
        return "(" + iter_code + ").select { |" + safe_target + "| " + cond_code + " }.map { |" + safe_target + "| " + elt_code + " }"
    return "(" + iter_code + ").map { |" + safe_target + "| " + elt_code + " }"


def _emit_dict_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    generators = _list(node, "generators")
    key_node = node.get("key")
    value_node = node.get("value")
    if len(generators) == 0:
        return "{}"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "{}"
    target_code = _target_binding_name(gen.get("target"))
    iter_code = _emit_expr(ctx, gen.get("iter"))
    key_code = _emit_expr(ctx, key_node)
    value_code = _emit_expr(ctx, value_node)
    ifs = _list(gen, "ifs")
    body_code = "acc[" + key_code + "] = " + value_code
    if len(ifs) > 0:
        cond_parts: list[str] = []
        for cond in ifs:
            cond_parts.append(_emit_expr(ctx, cond))
        body_code = body_code + " if " + " && ".join(cond_parts)
    return "(" + iter_code + ").each_with_object({}) { |" + target_code + ", acc| " + body_code + " }"


def _emit_set_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    generators = _list(node, "generators")
    elt_node = node.get("elt")
    if len(generators) == 0:
        return "Set.new"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "Set.new"
    target_code = _target_binding_name(gen.get("target"))
    iter_code = _emit_expr(ctx, gen.get("iter"))
    elt_code = _emit_expr(ctx, elt_node)
    ifs = _list(gen, "ifs")
    mapped = "(" + iter_code + ")"
    if len(ifs) > 0:
        cond_parts: list[str] = []
        for cond in ifs:
            cond_parts.append(_emit_expr(ctx, cond))
        mapped = mapped + ".select { |" + target_code + "| " + " && ".join(cond_parts) + " }"
    mapped = mapped + ".map { |" + target_code + "| " + elt_code + " }"
    return "Set.new(" + mapped + ")"


def _emit_range_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    start = node.get("start")
    stop = node.get("stop")
    step = node.get("step")
    start_code = _emit_expr(ctx, start) if isinstance(start, dict) else "0"
    stop_code = _emit_expr(ctx, stop) if isinstance(stop, dict) else "0"
    step_code = _emit_expr(ctx, step) if isinstance(step, dict) else "1"
    return "__pytra_range(" + start_code + ", " + stop_code + ", " + step_code + ")"


# ---------------------------------------------------------------------------
# Call emission
# ---------------------------------------------------------------------------

def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    func = node.get("func")
    args = _list(node, "args")
    keywords = _list(node, "keywords")
    runtime_call = _str(node, "runtime_call")
    resolved_runtime_call = _str(node, "resolved_runtime_call")
    runtime_symbol = _str(node, "runtime_symbol")
    runtime_symbol_dispatch = _str(node, "runtime_symbol_dispatch")
    semantic_tag = _str(node, "semantic_tag")
    adapter_kind = _str(node, "runtime_call_adapter_kind")

    # Resolve via mapping
    call_key = runtime_call
    if call_key == "":
        call_key = resolved_runtime_call
    # Extract builtin_name from func node
    builtin_name = ""
    module_attr_owner_skip = False
    module_attr_owner_transpiled = False
    if isinstance(func, dict):
        func_kind = _str(func, "kind")
        if func_kind == "Attribute":
            builtin_name = _str(func, "attr")
            owner_node = func.get("value")
            if isinstance(owner_node, dict):
                owner_id = _str(owner_node, "id")
                owner_mod = ctx.import_alias_modules.get(owner_id, "")
                module_attr_owner_skip = owner_mod != "" and _should_skip_module_ruby(owner_mod, ctx.mapping)
                module_attr_owner_transpiled = owner_mod != "" and not _should_skip_module_ruby(owner_mod, ctx.mapping)
        else:
            builtin_name = _str(func, "id")
            if builtin_name == "":
                builtin_name = _str(func, "repr")
    if builtin_name == "cast":
        return _emit_cast_call(ctx, node, args)
    if builtin_name == "isinstance" and len(args) >= 2 and isinstance(args[0], dict) and isinstance(args[1], dict):
        type_node = args[1]
        type_name = _str(type_node, "id")
        if type_name == "":
            type_name = _str(type_node, "repr")
        return _emit_isinstance(ctx, {"kind": "IsInstance", "value": args[0], "expected_type_name": type_name})
    if semantic_tag == "core.bytearray_ctor":
        if len(args) >= 1:
            return "__pytra_bytearray(" + _emit_expr(ctx, args[0]) + ")"
        return "__pytra_bytearray()"
    if semantic_tag == "core.bytes_ctor":
        if len(args) >= 1:
            return "__pytra_bytes(" + _emit_expr(ctx, args[0]) + ")"
        return "__pytra_bytes()"
    if semantic_tag == "core.dict_ctor":
        if len(args) >= 1:
            return "Hash[(" + _emit_expr(ctx, args[0]) + ")]"
        return "{}"
    if semantic_tag == "core.list_ctor":
        return _emit_list_ctor(ctx, args)
    if semantic_tag == "core.set_ctor":
        return _emit_set_ctor(ctx, args)
    if semantic_tag == "core.tuple_ctor":
        return _emit_tuple_ctor(ctx, args)
    should_resolve_runtime = call_key != "" or adapter_kind != ""
    if isinstance(func, dict) and _str(func, "kind") == "Attribute":
        owner_node = func.get("value")
        if isinstance(owner_node, dict):
            owner_id = _str(owner_node, "id")
            owner_mod = ctx.import_alias_modules.get(owner_id, "")
            if owner_mod != "" and not _should_skip_module_ruby(owner_mod, ctx.mapping):
                should_resolve_runtime = False
    if not should_resolve_runtime and builtin_name in ctx.runtime_imports:
        should_resolve_runtime = True
    if (
        not should_resolve_runtime
        and builtin_name in ctx.mapping.calls
        and not module_attr_owner_transpiled
        and builtin_name not in ctx.function_names
        and builtin_name not in ctx.class_names
        and builtin_name not in ctx.var_types
        and builtin_name not in ctx.import_alias_modules
    ):
        should_resolve_runtime = True
    alias_module_id = ctx.import_alias_modules.get(builtin_name, "")
    if builtin_name in ctx.import_alias_modules and builtin_name not in ctx.runtime_imports:
        if alias_module_id != "" and not _should_skip_module_ruby(alias_module_id, ctx.mapping):
            should_resolve_runtime = False
    mapped = resolve_runtime_call(call_key, builtin_name, adapter_kind, ctx.mapping) if should_resolve_runtime else ""

    # When func is Attribute (method call), prepend owner to builtin args
    builtin_args = list(args)
    method_owner = ""
    if isinstance(func, dict) and _str(func, "kind") == "Attribute":
        owner_val = func.get("value")
        method_owner = _emit_expr(ctx, owner_val)
        # For builtin calls, prepend owner as first arg
        if mapped != "":
            builtin_args_strs = []
            if not module_attr_owner_skip:
                builtin_args_strs.append(method_owner)
            for a in args:
                builtin_args_strs.append(_emit_expr(ctx, a))
        else:
            builtin_args_strs = []
    else:
        builtin_args_strs = []
        for a in args:
            builtin_args_strs.append(_emit_expr(ctx, a))

    if isinstance(func, dict) and _str(func, "kind") == "Attribute":
        owner_val = func.get("value")
        if _is_super_receiver(owner_val) and builtin_name == "__init__":
            arg_strs_super: list[str] = []
            for a in args:
                arg_strs_super.append(_emit_expr(ctx, a))
            return _render_super_call(arg_strs_super)

    # Special markers
    if mapped == "__CAST__":
        return _emit_cast_call(ctx, node, args)
    if mapped == "__PANIC__":
        return _emit_panic_call(ctx, args)
    if mapped == "__LIST_CTOR__":
        return _emit_list_ctor(ctx, args)
    if mapped == "__TUPLE_CTOR__":
        return _emit_tuple_ctor(ctx, args)
    if mapped == "__SET_CTOR__":
        return _emit_set_ctor(ctx, args)
    if mapped == "__LIST_APPEND__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "push")
    if mapped == "__LIST_EXTEND__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "concat")
    if mapped == "__LIST_POP__":
        return _emit_list_pop_strs(builtin_args_strs)
    if mapped == "__pytra_clear__":
        return "__pytra_clear(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__LIST_INDEX__":
        return _emit_list_index_strs(builtin_args_strs)
    if mapped == "__DICT_GET__":
        return _emit_dict_get_strs(builtin_args_strs)
    if mapped == "__DICT_ITEMS__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "items")
    if mapped == "__DICT_KEYS__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "keys")
    if mapped == "__DICT_VALUES__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "values")
    if mapped == "__SET_ADD__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "add")
    if mapped == "__SET_UPDATE__":
        return "__pytra_set_update(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__SET_DISCARD__":
        return _emit_set_discard_strs(builtin_args_strs)
    if mapped == "__SET_REMOVE__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "delete")
    # String method markers
    if mapped == "__STR_STRIP__":
        return "__pytra_strip(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__STR_LSTRIP__":
        return "__pytra_lstrip(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__STR_RSTRIP__":
        return "__pytra_rstrip(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__STR_STARTSWITH__":
        return _emit_str_method_strs(builtin_args_strs, "start_with?")
    if mapped == "__STR_ENDSWITH__":
        return _emit_str_method_strs(builtin_args_strs, "end_with?")
    if mapped == "__STR_REPLACE__":
        return _emit_str_replace_strs(builtin_args_strs)
    if mapped == "__STR_FIND__":
        return _emit_str_method_strs(builtin_args_strs, "find")
    if mapped == "__pytra_str_rfind":
        return "__pytra_str_rfind(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__STR_SPLIT__":
        return _emit_str_split_strs(builtin_args_strs)
    if mapped == "__STR_JOIN__":
        return _emit_str_join_strs(builtin_args_strs)
    if mapped == "__STR_UPPER__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "upcase")
    if mapped == "__STR_LOWER__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "downcase")
    if mapped == "__STR_COUNT__":
        return _emit_str_method_strs(builtin_args_strs, "count")
    if mapped == "__STR_INDEX__":
        return _emit_str_method_strs(builtin_args_strs, "index")
    if mapped == "__STR_ISALNUM__":
        return _emit_str_isalnum_strs(builtin_args_strs)
    if mapped == "__STR_ISSPACE__":
        return _emit_str_isspace_strs(builtin_args_strs)
    is_ctor_call = runtime_symbol_dispatch == "ctor"
    if not is_ctor_call and adapter_kind == "extern_delegate":
        ctor_name_hint = runtime_symbol if runtime_symbol != "" else builtin_name
        is_ctor_call = ctor_name_hint != "" and ctor_name_hint[0].isupper()
    if is_ctor_call:
        ctor_name = runtime_symbol if runtime_symbol != "" else builtin_name
        ctor_args = builtin_args_strs if len(builtin_args_strs) > 0 else [_emit_expr(ctx, a) for a in args]
        return _ruby_class_name(ctor_name) + ".new(" + ", ".join(ctor_args) + ")"

    if mapped != "":
        # Regular mapped call - use builtin_args_strs if available, else emit args
        if len(builtin_args_strs) > 0:
            return mapped + "(" + ", ".join(builtin_args_strs) + ")"
        arg_strs: list[str] = []
        for a in args:
            arg_strs.append(_emit_expr(ctx, a))
        return mapped + "(" + ", ".join(arg_strs) + ")"

    # Unmapped: emit from EAST3 node
    if isinstance(func, dict):
        func_kind = _str(func, "kind")
        if func_kind == "Name":
            fn_name = _str(func, "id")
            if fn_name == "":
                fn_name = _str(func, "repr")
            if fn_name == "cast":
                return _emit_cast_call(ctx, node, args)
            if fn_name in ("ArgSpec", "_ArgSpec") and len(keywords) > 0:
                kw_map = _keyword_arg_map(ctx, keywords)
                ctor_args: list[str] = []
                if len(args) > 0:
                    ctor_args.append(_emit_expr(ctx, args[0]))
                ctor_args.append(kw_map.get("action", '""'))
                ctor_args.append(kw_map.get("choices", "[]"))
                ctor_args.append(kw_map.get("default", "nil"))
                ctor_args.append(kw_map.get("help_text", kw_map.get("help", '""')))
                return "ArgSpec.new(" + ", ".join(ctor_args) + ")"
            if runtime_symbol_dispatch == "ctor":
                ctor_name = runtime_symbol if runtime_symbol != "" else fn_name
                arg_ctor: list[str] = []
                for a in args:
                    arg_ctor.append(_emit_expr(ctx, a))
                return _ruby_class_name(ctor_name) + ".new(" + ", ".join(arg_ctor) + ")"
            if fn_name == "super":
                arg_strs0: list[str] = []
                for a in args:
                    arg_strs0.append(_emit_expr(ctx, a))
                return _render_super_call(arg_strs0)
            if fn_name in ctx.runtime_imports:
                arg_strs_import: list[str] = []
                for a in args:
                    arg_strs_import.append(_emit_expr(ctx, a))
                return ctx.runtime_imports[fn_name] + "(" + ", ".join(arg_strs_import) + ")"
            # Class constructors
            if fn_name in ctx.class_names:
                arg_strs2: list[str] = []
                for a in args:
                    arg_strs2.append(_emit_expr(ctx, a))
                return _ruby_class_name(fn_name) + ".new(" + ", ".join(arg_strs2) + ")"
            # Exception constructors
            if _is_exception_type_name(ctx, fn_name):
                exc_cls = ruby_exception_class(fn_name)
                arg_strs3: list[str] = []
                for a in args:
                    arg_strs3.append(_emit_expr(ctx, a))
                if len(arg_strs3) > 0:
                    return exc_cls + ".new(" + ", ".join(arg_strs3) + ")"
                return exc_cls + ".new"
            safe_fn = _ruby_symbol_name(ctx, fn_name)
            arg_strs4: list[str] = []
            for a in args:
                arg_strs4.append(_emit_expr(ctx, a))
            if fn_name in ctx.function_varargs and len(args) > 0 and isinstance(args[-1], dict) and _str(args[-1], "kind") == "List":
                fixed_args = arg_strs4[:-1]
                fixed_args.append("*" + arg_strs4[-1])
                return safe_fn + "(" + ", ".join(fixed_args) + ")"
            fn_type = _str(func, "resolved_type")
            local_type = ctx.var_types.get(safe_fn, "")
            fn_type_l = fn_type.lower()
            local_type_l = local_type.lower()
            if (
                fn_type == "callable"
                or local_type == "callable"
                or fn_type.startswith("callable[")
                or local_type.startswith("callable[")
                or "callable" in fn_type_l
                or "callable" in local_type_l
            ) and safe_fn not in ctx.runtime_imports and not _is_function_symbol(ctx, fn_name) and fn_name not in ctx.import_alias_modules and fn_name not in ctx.mapping.calls:
                return safe_fn + ".call(" + ", ".join(arg_strs4) + ")"
            return safe_fn + "(" + ", ".join(arg_strs4) + ")"

        if func_kind == "Attribute":
            return _emit_method_call(ctx, func, args, keywords)

    # Fallback
    func_code = _emit_expr(ctx, func)
    arg_strs5: list[str] = []
    for a in args:
        arg_strs5.append(_emit_expr(ctx, a))
    if isinstance(func, dict) and _str(func, "kind") == "Lambda":
        return "(" + func_code + ").call(" + ", ".join(arg_strs5) + ")"
    if isinstance(func, dict):
        func_rt = _str(func, "resolved_type")
        if func_rt in ("callable", "Callable") or func_rt.startswith("callable[") or func_rt.startswith("Callable["):
            return func_code + ".call(" + ", ".join(arg_strs5) + ")"
        if _str(func, "kind") == "Unbox" and _str(func, "target").lower() == "callable":
            return func_code + ".call(" + ", ".join(arg_strs5) + ")"
        if _str(func, "kind") == "Name":
            func_name = _str(func, "id")
            local_type = ctx.var_types.get(_ruby_local_name(ctx, func_name), "")
            if "callable" in local_type.lower():
                return func_code + ".call(" + ", ".join(arg_strs5) + ")"
    return func_code + "(" + ", ".join(arg_strs5) + ")"


def _emit_method_call(
    ctx: EmitContext,
    func: dict[str, JsonVal],
    args: list[JsonVal],
    keywords: list[JsonVal],
) -> str:
    owner_node = func.get("value")
    attr = _str(func, "attr")
    owner_code = _emit_expr(ctx, owner_node)
    owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    arg_strs: list[str] = []
    for a in args:
        arg_strs.append(_emit_expr(ctx, a))
    if len(keywords) > 0:
        keyword_map = _keyword_arg_map(ctx, keywords)
        if attr == "add_argument":
            ordered = ["name0", "name1", "name2", "name3", "help", "action", "choices", "default"]
            defaults = {
                "name1": '""',
                "name2": '""',
                "name3": '""',
                "help": '""',
                "action": '""',
                "choices": "[]",
                "default": "nil",
            }
            merged = list(arg_strs)
            while len(merged) < len(ordered):
                merged.append(defaults.get(ordered[len(merged)], "nil"))
            for idx, param_name in enumerate(ordered):
                if param_name in keyword_map:
                    merged[idx] = keyword_map[param_name]
            arg_strs = merged
        elif attr == "mkdir":
            merged = list(arg_strs)
            while len(merged) < 2:
                merged.append("false")
            if "parents" in keyword_map:
                merged[0] = keyword_map["parents"]
            if "exist_ok" in keyword_map:
                merged[1] = keyword_map["exist_ok"]
            arg_strs = merged
    runtime_key = ""
    if owner_type == "str":
        runtime_key = "str." + attr
    elif owner_type == "dict" or owner_type.startswith("dict[") or "dict[" in owner_type:
        runtime_key = "dict." + attr
    elif owner_type == "set" or owner_type.startswith("set[") or "set[" in owner_type:
        runtime_key = "set." + attr
    elif owner_type == "list" or owner_type.startswith("list[") or "list[" in owner_type or owner_type == "bytearray" or owner_type == "bytes":
        runtime_key = "list." + attr
    builtin_args_strs = [owner_code] + arg_strs
    if isinstance(owner_node, dict):
        owner_id = _str(owner_node, "id")
        owner_mod = ctx.import_alias_modules.get(owner_id, "")
        if owner_mod != "":
            mod_short = owner_mod.rsplit(".", 1)[-1]
            qualified_key = mod_short + "." + attr
            if qualified_key in ctx.mapping.calls:
                mapped_mod = ctx.mapping.calls[qualified_key]
                return mapped_mod + "(" + ", ".join(arg_strs) + ")"
            if _should_skip_module_ruby(owner_mod, ctx.mapping):
                resolved = resolve_runtime_symbol_name(attr, ctx.mapping, module_id=owner_mod)
                if resolved != "":
                    return resolved + "(" + ", ".join(arg_strs) + ")"
            if not _should_skip_module_ruby(owner_mod, ctx.mapping):
                return _ruby_method_name(attr) + "(" + ", ".join(arg_strs) + ")"
    mapped = ctx.mapping.calls.get(runtime_key, "")
    if mapped == "__LIST_APPEND__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "push")
    if mapped == "__LIST_EXTEND__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "concat")
    if mapped == "__LIST_POP__":
        return _emit_list_pop_strs(builtin_args_strs)
    if mapped == "__pytra_clear__":
        return "__pytra_clear(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__LIST_INDEX__":
        return _emit_list_index_strs(builtin_args_strs)
    if mapped == "__DICT_GET__":
        return _emit_dict_get_strs(builtin_args_strs)
    if mapped == "__DICT_ITEMS__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "to_a")
    if mapped == "__DICT_KEYS__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "keys")
    if mapped == "__DICT_VALUES__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "values")
    if mapped == "__SET_ADD__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "add")
    if mapped == "__SET_DISCARD__":
        return _emit_set_discard_strs(builtin_args_strs)
    if mapped == "__SET_REMOVE__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "delete")
    if mapped == "__STR_STRIP__":
        return "__pytra_strip(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__STR_LSTRIP__":
        return "__pytra_lstrip(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__STR_RSTRIP__":
        return "__pytra_rstrip(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__STR_STARTSWITH__":
        return _emit_str_method_strs(builtin_args_strs, "start_with?")
    if mapped == "__STR_ENDSWITH__":
        return _emit_str_method_strs(builtin_args_strs, "end_with?")
    if mapped == "__STR_REPLACE__":
        return _emit_str_replace_strs(builtin_args_strs)
    if mapped == "__STR_FIND__":
        return _emit_str_method_strs(builtin_args_strs, "find")
    if mapped == "__pytra_str_rfind":
        return "__pytra_str_rfind(" + ", ".join(builtin_args_strs) + ")"
    if mapped == "__STR_SPLIT__":
        return _emit_str_split_strs(builtin_args_strs)
    if mapped == "__STR_JOIN__":
        return _emit_str_join_strs(builtin_args_strs)
    if mapped == "__STR_UPPER__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "upcase")
    if mapped == "__STR_LOWER__":
        return _emit_method_call_on_first_arg_strs(builtin_args_strs, "downcase")
    if mapped == "__STR_COUNT__":
        return _emit_str_method_strs(builtin_args_strs, "count")
    if mapped == "__STR_INDEX__":
        return _emit_str_method_strs(builtin_args_strs, "index")
    if mapped == "__STR_ISALNUM__":
        return _emit_str_isalnum_strs(builtin_args_strs)
    if mapped == "__STR_ISSPACE__":
        return _emit_str_isspace_strs(builtin_args_strs)
    if mapped != "":
        return mapped + "(" + ", ".join(builtin_args_strs) + ")"
    # self.method() -> method() with self context
    if isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
        return attr + "(" + ", ".join(arg_strs) + ")"
    # Class.static_method()
    if isinstance(owner_node, dict):
        owner_id = _str(owner_node, "id")
        if owner_id in ctx.class_names:
            static_set = ctx.class_static_methods.get(owner_id, set())
            if attr in static_set:
                return _ruby_class_name(owner_id) + "." + _ruby_method_name(attr) + "(" + ", ".join(arg_strs) + ")"
    # super().__init__(*args) -> super(*args)
    if _is_super_receiver(owner_node):
        if attr == "__init__":
            return _render_super_call(arg_strs)
        return "super." + _ruby_method_name(attr) + "(" + ", ".join(arg_strs) + ")"
    # Regular method
    return owner_code + "." + _ruby_method_name(attr) + "(" + ", ".join(arg_strs) + ")"


def _emit_cast_call(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    """static_cast → Ruby type conversion."""
    resolved_type = _str(node, "resolved_type")
    if len(args) == 0:
        return "nil"
    value_node = args[-1]
    value_code = _emit_expr(ctx, value_node)
    target_type = resolved_type
    if len(args) >= 2 and isinstance(args[0], dict):
        explicit_type = _str(args[0], "type_object_of")
        if explicit_type == "":
            explicit_type = _str(args[0], "id")
        if explicit_type != "":
            target_type = explicit_type
    if target_type in ("int", "int64", "int32", "int16", "int8",
                          "uint8", "uint16", "uint32", "uint64"):
        return value_code + ".to_i"
    if target_type in ("float", "float64", "float32"):
        return "__pytra_float(" + value_code + ")"
    if target_type == "str":
        return "__pytra_str(" + value_code + ")"
    if target_type == "bool":
        return "__pytra_truthy(" + value_code + ")"
    return value_code


def _emit_panic_call(ctx: EmitContext, args: list[JsonVal]) -> str:
    if len(args) > 0:
        msg = _emit_expr(ctx, args[0])
        return "raise RuntimeError.new(" + msg + ")"
    return "raise RuntimeError.new"


def _emit_list_ctor(ctx: EmitContext, args: list[JsonVal]) -> str:
    if len(args) == 0:
        return "[]"
    arg_code = _emit_expr(ctx, args[0])
    return "Array(" + arg_code + ")"


def _emit_tuple_ctor(ctx: EmitContext, args: list[JsonVal]) -> str:
    if len(args) == 0:
        return "[]"
    arg_code = _emit_expr(ctx, args[0])
    return "Array(" + arg_code + ")"


def _emit_set_ctor(ctx: EmitContext, args: list[JsonVal]) -> str:
    if len(args) == 0:
        return "Set.new"
    arg_code = _emit_expr(ctx, args[0])
    return "Set.new(" + arg_code + ")"


def _emit_method_call_on_first_arg_strs(arg_strs: list[str], method: str) -> str:
    if len(arg_strs) == 0:
        return "nil"
    owner = arg_strs[0]
    rest = arg_strs[1:]
    if len(rest) > 0:
        return owner + "." + method + "(" + ", ".join(rest) + ")"
    return owner + "." + method


def _emit_list_pop_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) == 0:
        return "nil"
    owner = arg_strs[0]
    if len(arg_strs) > 1:
        return owner + ".delete_at(" + arg_strs[1] + ")"
    return owner + ".pop"


def _emit_list_index_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) < 2:
        return "nil"
    return arg_strs[0] + ".index(" + arg_strs[1] + ")"


def _emit_lvalue(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return "_"
    kind = _str(node, "kind")
    if kind == "Name":
        name = _str(node, "id")
        return _safe_ruby_ident(name) if name != "" else "_"
    if kind == "Attribute":
        return _emit_attribute(ctx, node)
    if kind == "Subscript":
        owner = _emit_expr(ctx, node.get("value"))
        slice_code = _emit_expr(ctx, node.get("slice"))
        return owner + "[" + slice_code + "]"
    return _emit_expr(ctx, node)


def _emit_dict_get_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) < 2:
        return "nil"
    owner = arg_strs[0]
    key = arg_strs[1]
    if len(arg_strs) > 2:
        return owner + ".get(" + key + ", " + arg_strs[2] + ")"
    return owner + ".get(" + key + ")"


def _emit_set_discard_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) < 2:
        return "nil"
    return arg_strs[0] + ".delete(" + arg_strs[1] + ")"


def _emit_str_method_strs(arg_strs: list[str], method: str) -> str:
    if len(arg_strs) < 2:
        return "nil"
    owner = arg_strs[0]
    rest = arg_strs[1:]
    return owner + "." + method + "(" + ", ".join(rest) + ")"


def _emit_str_replace_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) < 3:
        return "nil"
    return arg_strs[0] + ".gsub(" + arg_strs[1] + ", " + arg_strs[2] + ")"


def _emit_str_split_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) == 0:
        return "nil"
    if len(arg_strs) > 1:
        return arg_strs[0] + ".split(" + arg_strs[1] + ")"
    return arg_strs[0] + ".split"


def _emit_str_join_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) < 2:
        return "nil"
    # Ruby: iterable.join(separator) — first arg is separator, second is iterable
    return arg_strs[1] + ".join(" + arg_strs[0] + ")"


def _emit_str_isalnum_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) == 0:
        return "false"
    return "!!" + arg_strs[0] + ".match?(/\\A[A-Za-z0-9]+\\z/)"


def _emit_str_isspace_strs(arg_strs: list[str]) -> str:
    if len(arg_strs) == 0:
        return "false"
    return "!!" + arg_strs[0] + ".match?(/\\A\\s+\\z/)"


def _keyword_arg_map(ctx: EmitContext, keywords: list[JsonVal]) -> dict[str, str]:
    out: dict[str, str] = {}
    for kw in keywords:
        if not isinstance(kw, dict):
            continue
        kw_name = _str(kw, "arg")
        kw_value = kw.get("value")
        if kw_name == "" or not isinstance(kw_value, dict):
            continue
        out[kw_name] = _emit_expr(ctx, kw_value)
    return out


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_leading_trivia(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """Emit leading_trivia (comments, blank lines, passthrough directives)."""
    trivia = _list(node, "leading_trivia")
    for t in trivia:
        if not isinstance(t, dict):
            continue
        tk = _str(t, "kind")
        if tk == "comment":
            text = _str(t, "text")
            # Check for passthrough directives
            for prefix in ("# Pytra::ruby ", "# Pytra::ruby: ",
                           "# Pytra::pass ", "# Pytra::pass: "):
                if text.startswith(prefix):
                    _emit(ctx, text[len(prefix):])
                    break
            else:
                if text.startswith("# Pytra::ruby begin") or text.startswith("# Pytra::pass begin"):
                    pass  # handled in block
                elif text.startswith("# Pytra::ruby end") or text.startswith("# Pytra::pass end"):
                    pass  # handled in block
                else:
                    _emit(ctx, "# " + text.lstrip("# "))
        elif tk == "blank":
            _emit_blank(ctx)


def _emit_stmt(ctx: EmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        return
    _emit_leading_trivia(ctx, node)
    kind = _str(node, "kind")
    if kind == "Expr":
        _emit_expr_stmt(ctx, node)
    elif kind == "Return":
        _emit_return_stmt(ctx, node)
    elif kind == "Assign":
        _emit_assign(ctx, node)
    elif kind == "AnnAssign":
        _emit_ann_assign(ctx, node)
    elif kind == "AugAssign":
        _emit_aug_assign(ctx, node)
    elif kind == "If":
        _emit_if(ctx, node)
    elif kind == "While":
        _emit_while(ctx, node)
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
    elif kind == "Pass":
        _emit(ctx, "# pass")
    elif kind == "Raise":
        _emit_raise(ctx, node)
    elif kind == "Try":
        _emit_try(ctx, node)
    elif kind == "Break":
        _emit(ctx, "break")
    elif kind == "Continue":
        _emit(ctx, "next")
    elif kind == "TypeAlias":
        pass  # Ruby doesn't have type aliases
    elif kind == "Match":
        _emit_match(ctx, node)
    elif kind in ("ErrorReturn", "ErrorCheck", "ErrorCatch"):
        pass  # native_throw style: no-op
    elif kind == "comment":
        text = _str(node, "text")
        if text != "":
            _emit(ctx, "# " + text)
    elif kind == "blank":
        _emit_blank(ctx)
    else:
        _emit(ctx, "# unsupported: " + kind)


def _emit_body(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        _emit_stmt(ctx, stmt)


def _emit_expr_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    discard = _bool(node, "discard_result")
    if isinstance(value, dict):
        if _str(value, "kind") == "Name":
            control_name = _str(value, "id")
            if control_name == "continue":
                _emit(ctx, "next")
                return
            if control_name == "break":
                _emit(ctx, "break")
                return
        code = _emit_expr(ctx, value)
        if discard:
            _emit(ctx, code)
        else:
            _emit(ctx, code)


def _emit_return_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if value is None or (isinstance(value, dict) and _str(value, "kind") == "Constant" and value.get("value") is None):
        _emit(ctx, "return")
    else:
        code = _emit_expr(ctx, value)
        _emit(ctx, "return " + code)


def _emit_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    if not isinstance(target, dict):
        return
    target_kind = _str(target, "kind")
    # Tuple destructuring
    if target_kind == "Tuple":
        elements = _list(target, "elements")
        value_code = _emit_expr(ctx, value)
        names: list[str] = []
        for e in elements:
            if isinstance(e, dict):
                n = _str(e, "id")
                unused = _bool(e, "unused")
                if unused:
                    names.append("_")
                elif n != "":
                    names.append(_safe_ruby_ident(n))
                else:
                    names.append("_")
            else:
                names.append("_")
        _emit(ctx, ", ".join(names) + " = " + value_code)
        return
    # Subscript assignment
    if target_kind == "Subscript":
        owner_node = target.get("value")
        slice_node = target.get("slice")
        owner_code = _emit_expr(ctx, owner_node)
        slice_code = _emit_expr(ctx, slice_node)
        value_code = _emit_expr(ctx, value)
        _emit(ctx, owner_code + "[" + slice_code + "] = " + value_code)
        return
    # Attribute assignment (self.x = ...)
    if target_kind == "Attribute":
        attr_code = _emit_attribute(ctx, target)
        value_code = _emit_expr(ctx, value)
        _emit(ctx, attr_code + " = " + value_code)
        return
    # Simple name
    name = _str(target, "id")
    if name == "":
        name = _str(target, "repr")
    safe_name = _ruby_local_name(ctx, name)
    if ctx.current_class == "" and ctx.current_return_type == "" and _is_ruby_constant_like(name):
        safe_name = _ruby_constant_name(name)
    value_code = _emit_expr(ctx, value)
    if isinstance(value, dict):
        value_type = _str(value, "resolved_type")
        if value_type == "" and _str(value, "kind") == "Lambda":
            value_type = "callable"
        if value_type != "":
            ctx.var_types[safe_name] = value_type
    # Check for extern_var_v1
    meta = _dict(node, "meta")
    extern_v1 = meta.get("extern_var_v1")
    if isinstance(extern_v1, dict):
        # Extern variable -> delegate to __native
        symbol = _str(extern_v1, "symbol")
        if symbol == "":
            symbol = safe_name
        _emit(ctx, safe_name + " = __native_" + symbol)
        return
    _emit(ctx, safe_name + " = " + value_code)


def _emit_ann_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    if isinstance(target, dict) and _str(target, "kind") == "Attribute":
        attr_code = _emit_attribute(ctx, target)
        if isinstance(value, dict):
            value_code = _emit_expr(ctx, value)
            _emit(ctx, attr_code + " = " + value_code)
        return
    name = ""
    if isinstance(target, dict):
        name = _str(target, "id")
    if name == "":
        name = _str(node, "target")
        if not isinstance(name, str):
            name = ""
    safe_name = _ruby_local_name(ctx, name) if name != "" else "_"
    if name != "" and ctx.current_class == "" and ctx.current_return_type == "" and _is_ruby_constant_like(name):
        safe_name = _ruby_constant_name(name)
    anno = node.get("annotation")
    if name != "" and not (ctx.current_class == "" and ctx.current_return_type == "" and _is_ruby_constant_like(name)):
        declared_type = ""
        if isinstance(anno, dict):
            declared_type = _str(anno, "resolved_type")
            if declared_type == "":
                declared_type = _str(anno, "repr")
        elif isinstance(anno, str):
            declared_type = anno
        if declared_type == "":
            declared_type = _str(node, "decl_type")
        if declared_type == "":
            declared_type = _str(node, "resolved_type")
        if declared_type != "":
            ctx.var_types[safe_name] = declared_type
    # Check for extern_var_v1
    meta = _dict(node, "meta")
    extern_v1 = meta.get("extern_var_v1")
    if isinstance(extern_v1, dict):
        symbol = _str(extern_v1, "symbol")
        if symbol == "":
            symbol = safe_name
        _emit(ctx, safe_name + " = __native_" + symbol)
        return
    if value is not None and isinstance(value, dict):
        value_code = _emit_expr(ctx, value)
        _emit(ctx, safe_name + " = " + value_code)
    else:
        # Just a type declaration with no value: initialize to zero value
        decl_type = _str(node, "decl_type")
        if decl_type == "":
            decl_type = _str(node, "resolved_type")
        _emit(ctx, safe_name + " = " + ruby_zero_value(decl_type))


def _emit_aug_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    op = _str(node, "op")
    target_code = _emit_lvalue(ctx, target)
    value_code = _emit_expr(ctx, value)
    op_map: dict[str, str] = {
        "Add": "+=", "Sub": "-=", "Mult": "*=",
        "Div": "/=", "Mod": "%=",
        "BitAnd": "&=", "BitOr": "|=", "BitXor": "^=",
        "LShift": "<<=", "RShift": ">>=",
        "Pow": "**=",
    }
    if op == "FloorDiv":
        _emit(ctx, target_code + " = __pytra_floordiv(" + target_code + ", " + value_code + ")")
        return
    op_str = op_map.get(op, "+=")
    _emit(ctx, target_code + " " + op_str + " " + value_code)


def _emit_if(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    test = node.get("test")
    body = _list(node, "body")
    orelse = _list(node, "orelse")
    test_code = _emit_truthy(ctx, test)
    _emit(ctx, "if " + test_code)
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
        # elsif chain
        _emit_elsif(ctx, orelse[0])
    elif len(orelse) > 0:
        _emit(ctx, "else")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_elsif(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    test = node.get("test")
    body = _list(node, "body")
    orelse = _list(node, "orelse")
    test_code = _emit_truthy(ctx, test)
    _emit(ctx, "elsif " + test_code)
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
        _emit_elsif(ctx, orelse[0])
    elif len(orelse) > 0:
        _emit(ctx, "else")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1


def _emit_while(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    test = node.get("test")
    body = _list(node, "body")
    test_code = _emit_truthy(ctx, test)
    _emit(ctx, "while " + test_code)
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_for_core(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target")
    if not isinstance(target_node, dict):
        target_node = node.get("target_plan")
    iter_plan = node.get("iter_plan")
    body = _list(node, "body")
    orelse = _list(node, "orelse")

    safe_target = _target_binding_name(target_node)

    if isinstance(iter_plan, dict):
        plan_kind = _str(iter_plan, "kind")
        if plan_kind == "StaticRangeForPlan":
            _emit_static_range_for_plan(ctx, iter_plan, safe_target, body)
            return
        if plan_kind == "RuntimeIterForPlan":
            iter_node = iter_plan.get("iter_expr")
            if iter_node is None:
                iter_node = iter_plan.get("iter")
            iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"
            if isinstance(iter_node, dict) and _str(iter_node, "resolved_type") == "str":
                iter_code = "(" + iter_code + ").each_char"
                _emit(ctx, iter_code + " do |" + safe_target + "|")
                ctx.indent_level += 1
                _emit_body(ctx, body)
                ctx.indent_level -= 1
                _emit(ctx, "end")
                return
            _emit(ctx, "(" + iter_code + ").each do |" + safe_target + "|")
            ctx.indent_level += 1
            _emit_body(ctx, body)
            ctx.indent_level -= 1
            _emit(ctx, "end")
            return

    # Fallback: direct iter
    iter_node = node.get("iter")
    if iter_node is None:
        iter_node = iter_plan
    iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"
    _emit(ctx, "(" + iter_code + ").each do |" + safe_target + "|")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end")
    if len(orelse) > 0:
        _emit_body(ctx, orelse)


def _emit_static_range_for_plan(
    ctx: EmitContext,
    iter_plan: dict[str, JsonVal],
    target_code: str,
    body: list[JsonVal],
) -> None:
    """Emit a StaticRangeForPlan as a Ruby while loop."""
    start_node = iter_plan.get("start")
    stop_node = iter_plan.get("stop")
    step_node = iter_plan.get("step")
    range_mode = _str(iter_plan, "range_mode")

    start_code = _emit_expr(ctx, start_node) if isinstance(start_node, dict) else "0"
    stop_code = _emit_expr(ctx, stop_node) if isinstance(stop_node, dict) else "0"
    step_code = _emit_expr(ctx, step_node) if isinstance(step_node, dict) else "1"
    step_is_one = isinstance(step_node, dict) and _str(step_node, "kind") == "Constant" and step_node.get("value") == 1

    def _is_negative_step(sn: JsonVal) -> bool:
        if not isinstance(sn, dict):
            return False
        sk = _str(sn, "kind")
        if sk == "Constant":
            v = sn.get("value")
            return isinstance(v, (int, float)) and v < 0
        if sk == "UnaryOp" and _str(sn, "op") == "USub":
            return True
        return False

    descending = range_mode == "descending" or _is_negative_step(step_node)

    _emit(ctx, target_code + " = " + start_code)
    if descending:
        _emit(ctx, "while " + target_code + " > " + stop_code)
    else:
        _emit(ctx, "while " + target_code + " < " + stop_code)
    ctx.indent_level += 1
    _emit_body(ctx, body)
    if step_is_one and not descending:
        _emit(ctx, target_code + " += 1")
    else:
        _emit(ctx, target_code + " += " + step_code)
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_static_range_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target")
    body = _list(node, "body")
    target_name = ""
    if isinstance(target_node, dict):
        target_name = _str(target_node, "id")
    if target_name == "":
        target_name = "_i"
    safe_target = _safe_ruby_ident(target_name)
    _emit_static_range_for_plan(ctx, node, safe_target, body)


def _emit_runtime_iter_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target")
    iter_node = node.get("iter_expr")
    if iter_node is None:
        iter_node = node.get("iter")
    body = _list(node, "body")
    target_name = ""
    if isinstance(target_node, dict):
        target_name = _str(target_node, "id")
    if target_name == "":
        target_name = "_item"
    safe_target = _safe_ruby_ident(target_name)
    iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"
    _emit(ctx, "(" + iter_code + ").each do |" + safe_target + "|")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_var_decl(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    if name == "":
        return
    unused = _bool(node, "unused")
    if unused:
        return
    safe_name = _ruby_local_name(ctx, name)
    decl_type = _str(node, "type")
    if decl_type == "":
        decl_type = _str(node, "decl_type")
    ctx.var_types[safe_name] = decl_type
    # Ruby doesn't need variable pre-declarations; just track the type
    # Only emit if there's an initializer value
    value = node.get("value")
    if isinstance(value, dict):
        value_code = _emit_expr(ctx, value)
        _emit(ctx, safe_name + " = " + value_code)
    else:
        _emit(ctx, safe_name + " = " + ruby_zero_value(decl_type))


def _emit_swap(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    left = node.get("left")
    right = node.get("right")
    left_code = _emit_lvalue(ctx, left) if isinstance(left, dict) else "_"
    right_code = _emit_lvalue(ctx, right) if isinstance(right, dict) else "_"
    _emit(ctx, left_code + ", " + right_code + " = " + right_code + ", " + left_code)


def _emit_multi_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    value = node.get("value")
    value_code = _emit_expr(ctx, value)
    names: list[str] = []
    for t in targets:
        if isinstance(t, dict):
            n = _str(t, "id")
            unused = _bool(t, "unused")
            if unused:
                names.append("_")
            elif n != "":
                names.append(_safe_ruby_ident(n))
            else:
                names.append("_")
        else:
            names.append("_")
    _emit(ctx, ", ".join(names) + " = " + value_code)


def _emit_with(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    ctx_expr = node.get("context_expr")
    ctx_code = _emit_expr(ctx, ctx_expr) if isinstance(ctx_expr, dict) else "nil"
    var_name = _safe_ruby_ident(_str(node, "var_name"))
    comp_name = "__comp_" + str(len(ctx.lines) + 1)
    _emit(ctx, comp_name + " = " + ctx_code)
    if var_name != "":
        _emit(ctx, var_name + " = " + comp_name + ".__enter__")
    else:
        _emit(ctx, comp_name + ".__enter__")
    _emit(ctx, "begin")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "ensure")
    ctx.indent_level += 1
    _emit(ctx, comp_name + ".__exit__(nil, nil, nil)")
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_raise(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    exc = node.get("exc")
    if exc is None or (isinstance(exc, dict) and _str(exc, "kind") == ""):
        # Bare raise (re-raise)
        if ctx.current_exc_var != "":
            _emit(ctx, "raise " + ctx.current_exc_var)
        else:
            _emit(ctx, "raise")
        return
    exc_code = _emit_expr(ctx, exc)
    _emit(ctx, "raise " + exc_code)


def _emit_try(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    orelse = _list(node, "orelse")
    finalbody = _list(node, "finalbody")

    _emit(ctx, "begin")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1

    for handler in handlers:
        if not isinstance(handler, dict):
            continue
        exc_type = _str(handler, "type")
        if exc_type == "":
            exc_type_node = handler.get("type")
            if isinstance(exc_type_node, dict):
                exc_type = _str(exc_type_node, "id")
                if exc_type == "":
                    exc_type = _str(exc_type_node, "repr")
        exc_name = _str(handler, "name")
        ruby_exc = ruby_exception_class(exc_type) if exc_type != "" else "StandardError"
        if exc_type in ctx.class_names:
            ruby_exc = _ruby_class_name(exc_type)
        saved_exc_var = ctx.current_exc_var
        if exc_name != "":
            safe_exc = _safe_ruby_ident(exc_name)
            ctx.current_exc_var = safe_exc
            _emit(ctx, "rescue " + ruby_exc + " => " + safe_exc)
        else:
            _emit(ctx, "rescue " + ruby_exc)
        ctx.indent_level += 1
        handler_body = _list(handler, "body")
        _emit_body(ctx, handler_body)
        ctx.indent_level -= 1
        ctx.current_exc_var = saved_exc_var

    if len(orelse) > 0:
        # Ruby doesn't have try/else, emit after rescue (executes if no exception)
        # This is an approximation
        _emit_body(ctx, orelse)

    if len(finalbody) > 0:
        _emit(ctx, "ensure")
        ctx.indent_level += 1
        _emit_body(ctx, finalbody)
        ctx.indent_level -= 1

    _emit(ctx, "end")


def _emit_match(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    subject = node.get("subject")
    cases = _list(node, "cases")
    subject_code = _emit_expr(ctx, subject)
    _emit(ctx, "case " + subject_code)
    for case_node in cases:
        if not isinstance(case_node, dict):
            continue
        pattern = case_node.get("pattern")
        body = _list(case_node, "body")
        if isinstance(pattern, dict):
            pk = _str(pattern, "kind")
            if pk == "PatternWildcard":
                _emit(ctx, "else")
            elif pk == "VariantPattern":
                variant_name = _str(pattern, "variant_name")
                _emit(ctx, "when " + variant_name)
            elif pk == "PatternBind":
                bind_name = _str(pattern, "name")
                _emit(ctx, "when " + bind_name)
            else:
                _emit(ctx, "else")
        else:
            _emit(ctx, "else")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_import_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """Emit require/require_relative for Ruby."""
    kind = _str(node, "kind")
    if kind == "ImportFrom":
        module = _str(node, "module")
        names = _list(node, "names")
        if module in ("pytra.std", "pytra.utils"):
            return
        if _is_type_only_import_from(module, names):
            return
        # Skip standard library and built-in modules
        if _should_skip_module_ruby(module, ctx.mapping):
            return
        rel_path = module.replace(".", "_")
        _emit(ctx, 'require_relative "' + rel_path + '"')
    elif kind == "Import":
        names = _list(node, "names")
        for name_item in names:
            mod_name = ""
            if isinstance(name_item, dict):
                mod_name = _str(name_item, "name")
            elif isinstance(name_item, str):
                mod_name = name_item
            if mod_name != "" and not _should_skip_module_ruby(mod_name, ctx.mapping):
                rel_path = mod_name.replace(".", "_")
                _emit(ctx, 'require_relative "' + rel_path + '"')


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
    is_closure = _str(node, "kind") == "ClosureDef" and ctx.current_class == ""
    defaults = _dict(node, "arg_defaults")
    if len(defaults) == 0:
        defaults = _dict(node, "defaults")

    # Skip extern declarations (will be provided by native module)
    for d in decorators:
        if isinstance(d, str) and d == "extern":
            _emit_extern_delegate(ctx, node)
            return

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

    if name == "__init__" and ctx.current_class != "":
        fn_name = "initialize"
    elif name == "__str__" and ctx.current_class != "":
        fn_name = "to_s"
    elif name == "__len__" and ctx.current_class != "":
        fn_name = "length"
    elif name == "__repr__" and ctx.current_class != "":
        fn_name = "inspect"
    elif name == "__eq__" and ctx.current_class != "":
        fn_name = "=="
    elif name == "__lt__" and ctx.current_class != "":
        fn_name = "<"
    elif name == "__le__" and ctx.current_class != "":
        fn_name = "<="
    elif name == "__gt__" and ctx.current_class != "":
        fn_name = ">"
    elif name == "__ge__" and ctx.current_class != "":
        fn_name = ">="
    elif name == "__hash__" and ctx.current_class != "":
        fn_name = "hash"
    elif name == "__contains__" and ctx.current_class != "":
        fn_name = "include?"
    elif name == "__getitem__" and ctx.current_class != "":
        fn_name = "[]"
    elif name == "__setitem__" and ctx.current_class != "":
        fn_name = "[]="
    else:
        fn_name = _ruby_method_name(name)

    saved_vars = dict(ctx.var_types)
    saved_ret = ctx.current_return_type
    ctx.current_return_type = return_type

    # Build parameter list
    params: list[str] = []
    for a in arg_order:
        a_str = a if isinstance(a, str) else ""
        if a_str == "self":
            continue
        if a_str == "cls" and is_classmethod:
            continue
        safe_a = _safe_ruby_ident(a_str)
        a_type_val = arg_types.get(a_str, "")
        a_type = a_type_val if isinstance(a_type_val, str) else ""
        ctx.var_types[safe_a] = a_type
        # Check for default value
        default_val = defaults.get(a_str)
        if isinstance(default_val, dict):
            default_code = _emit_expr(ctx, default_val)
            params.append(safe_a + " = " + default_code)
        else:
            params.append(safe_a)

    # Handle varargs
    vararg_name_raw = _str(node, "vararg_name")
    if vararg_name_raw != "":
        safe_varg = _safe_ruby_ident(vararg_name_raw)
        params.append("*" + safe_varg)

    if is_closure:
        # ClosureDef -> lambda or proc
        ctx.var_types[_safe_ruby_ident(name)] = "callable"
        if len(params) > 0:
            _emit(ctx, fn_name + " = lambda { |" + ", ".join(params) + "|")
        else:
            _emit(ctx, fn_name + " = lambda {")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "}")
    elif is_property:
        # Property → getter method
        _emit(ctx, "def " + fn_name)
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")
    elif is_staticmethod and ctx.current_class != "":
        if len(params) > 0:
            _emit(ctx, "def self." + fn_name + "(" + ", ".join(params) + ")")
        else:
            _emit(ctx, "def self." + fn_name)
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")
    elif is_classmethod and ctx.current_class != "":
        if len(params) > 0:
            _emit(ctx, "def self." + fn_name + "(" + ", ".join(params) + ")")
        else:
            _emit(ctx, "def self." + fn_name)
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")
    else:
        if len(params) > 0:
            _emit(ctx, "def " + fn_name + "(" + ", ".join(params) + ")")
        else:
            _emit(ctx, "def " + fn_name)
        ctx.indent_level += 1
        # For __init__ (initialize): inject super if needed
        if fn_name == "initialize" and ctx.current_class != "":
            base_class = ctx.class_bases.get(ctx.current_class, "")
            if base_class != "":
                has_super_call = False
                for s in body:
                    if isinstance(s, dict) and isinstance(s.get("value"), dict):
                        repr_val = s.get("value", {}).get("repr", "")
                        if isinstance(repr_val, str) and "super" in repr_val:
                            has_super_call = True
                            break
                if not has_super_call and not _is_exception_type_name(ctx, base_class):
                    _emit(ctx, _render_super_call([]))
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")

    if ctx.current_class == "":
        _emit_blank(ctx)

    if is_closure:
        saved_vars[_safe_ruby_ident(name)] = "callable"
    ctx.var_types = saved_vars
    ctx.current_return_type = saved_ret


def _emit_extern_delegate(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """Emit extern function delegation to __native module."""
    name = _str(node, "name")
    arg_order = _list(node, "arg_order")
    safe_name = _safe_ruby_ident(name)
    params: list[str] = []
    for a in arg_order:
        a_str = a if isinstance(a, str) else ""
        if a_str == "self":
            continue
        params.append(_safe_ruby_ident(a_str))
    if len(params) > 0:
        _emit(ctx, "def " + safe_name + "(" + ", ".join(params) + ")")
    else:
        _emit(ctx, "def " + safe_name)
    ctx.indent_level += 1
    _emit(ctx, "__native_" + safe_name + "(" + ", ".join(params) + ")")
    ctx.indent_level -= 1
    _emit(ctx, "end")
    _emit_blank(ctx)


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
    bases = _list(node, "bases")
    body = _list(node, "body")
    decorators = _list(node, "decorators")
    is_dataclass = _bool(node, "dataclass")

    safe_name = _ruby_class_name(name)

    # Check for trait/interface
    is_trait = False
    for d in decorators:
        if isinstance(d, str) and d == "trait":
            is_trait = True

    # Check for enum
    is_enum = False
    enum_base = ctx.enum_bases.get(name, "")
    if enum_base != "":
        is_enum = True

    # Base class - check both 'base' (singular, EAST3) and 'bases' (list)
    base_name = _str(node, "base")
    if base_name == "" and len(bases) > 0:
        first_base = bases[0]
        if isinstance(first_base, dict):
            base_name = _str(first_base, "id")
            if base_name == "":
                base_name = _str(first_base, "repr")
        elif isinstance(first_base, str):
            base_name = first_base

    saved_class = ctx.current_class
    ctx.current_class = name

    if is_trait:
        # Trait -> Ruby module
        _emit(ctx, "module " + safe_name)
    elif base_name != "" and base_name != "object":
        ruby_base = _ruby_class_name(base_name)
        if _is_exception_type_name(ctx, base_name):
            ruby_base = ruby_exception_class(base_name)
        _emit(ctx, "class " + safe_name + " < " + ruby_base)
    else:
        _emit(ctx, "class " + safe_name)

    ctx.indent_level += 1

    # Emit attr_accessor for fields
    fields = _collect_class_fields(ctx, node)
    if len(fields) > 0 and not is_enum:
        field_names: list[str] = []
        for fname, _ in fields:
            field_names.append(":" + fname)
        _emit(ctx, "attr_accessor " + ", ".join(field_names))
    if is_dataclass and len(fields) > 0 and not is_enum:
        ctor_params: list[str] = []
        for fname, _ in fields:
            default_expr: JsonVal = None
            for stmt in body:
                if not isinstance(stmt, dict):
                    continue
                if _str(stmt, "kind") != "AnnAssign":
                    continue
                target = stmt.get("target")
                if isinstance(target, dict) and _str(target, "id") == fname:
                    default_expr = stmt.get("value")
                    break
            if isinstance(default_expr, dict):
                ctor_params.append(fname + " = " + _emit_expr(ctx, default_expr))
            else:
                ctor_params.append(fname)
        _emit(ctx, "def initialize(" + ", ".join(ctor_params) + ")")
        ctx.indent_level += 1
        for fname, _ in fields:
            _emit(ctx, "@" + fname + " = " + fname)
        ctx.indent_level -= 1
        _emit(ctx, "end")
    class_member_names: list[str] = []
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        if sk != "AnnAssign" and sk != "Assign":
            continue
        target = stmt.get("target")
        target_name = ""
        if isinstance(target, dict):
            target_name = _str(target, "id")
        if target_name == "" or target_name[0].isupper():
            continue
        if target_name not in class_member_names:
            class_member_names.append(target_name)
    if len(class_member_names) > 0:
        _emit(ctx, "class << self")
        ctx.indent_level += 1
        names: list[str] = []
        for member_name in class_member_names:
            names.append(":" + _safe_ruby_ident(member_name))
        _emit(ctx, "attr_accessor " + ", ".join(names))
        ctx.indent_level -= 1
        _emit(ctx, "end")

    # Emit body
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        # Skip class-level field annotations (handled by attr_accessor)
        if sk == "AnnAssign":
            # Check if it has a value (class-level constant/default)
            value = stmt.get("value")
            meta = _dict(stmt, "meta")
            if isinstance(value, dict) and not isinstance(meta.get("extern_var_v1"), dict):
                # Class constant or enum member
                target = stmt.get("target")
                target_name = ""
                if isinstance(target, dict):
                    target_name = _str(target, "id")
                if target_name != "":
                    value_code = _emit_expr(ctx, value)
                    safe_target_name = _safe_ruby_ident(target_name)
                    if target_name[0].isupper():
                        _emit(ctx, safe_target_name + " = " + value_code)
                    else:
                        _emit(ctx, "self." + safe_target_name + " = " + value_code)
            continue
        if sk == "Assign":
            # Class-level assignments (constants, enum members, etc.)
            target = stmt.get("target")
            value = stmt.get("value")
            if isinstance(target, dict):
                target_name = _str(target, "id")
                if target_name != "" and isinstance(value, dict):
                    value_code = _emit_expr(ctx, value)
                    safe_tname = _safe_ruby_ident(target_name)
                    if target_name[0].isupper():
                        _emit(ctx, safe_tname + " = " + value_code)
                    else:
                        _emit(ctx, "self." + safe_tname + " = " + value_code)
            continue
        _emit_stmt(ctx, stmt)

    ctx.indent_level -= 1
    _emit(ctx, "end")
    if name != "" and name[0].islower():
        _emit_blank(ctx)
        _emit(ctx, "def " + _safe_ruby_ident(name) + "(*args)")
        ctx.indent_level += 1
        _emit(ctx, _ruby_class_name(name) + ".new(*args)")
        ctx.indent_level -= 1
        _emit(ctx, "end")
    _emit_blank(ctx)

    ctx.current_class = saved_class


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _collect_module_class_info(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Pre-scan body to collect class names, bases, static methods, enum info."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _str(stmt, "kind") == "FunctionDef":
            name = _str(stmt, "name")
            if name != "":
                ctx.function_names.add(name)
                if _str(stmt, "vararg_name") != "":
                    ctx.function_varargs.add(name)
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind != "ClassDef":
            continue
        name = _str(stmt, "name")
        if name == "":
            continue
        ctx.class_names.add(name)
        # Check both 'base' (singular, EAST3) and 'bases' (list)
        base_name = _str(stmt, "base")
        if base_name == "":
            bases = _list(stmt, "bases")
            if len(bases) > 0:
                first_base = bases[0]
                if isinstance(first_base, dict):
                    base_name = _str(first_base, "id")
                    if base_name == "":
                        base_name = _str(first_base, "repr")
                elif isinstance(first_base, str):
                    base_name = first_base
        if base_name != "":
            ctx.class_bases[name] = base_name
            if base_name in ("Enum", "IntEnum", "IntFlag"):
                ctx.enum_bases[name] = base_name

        # Collect static methods, property methods, fields
        class_body = _list(stmt, "body")
        statics: set[str] = set()
        props: set[str] = set()
        field_map: dict[str, str] = {}
        for cs in class_body:
            if not isinstance(cs, dict):
                continue
            sk = _str(cs, "kind")
            if sk == "FunctionDef" or sk == "ClosureDef":
                fn_name = _str(cs, "name")
                fn_decorators = _list(cs, "decorators")
                for d in fn_decorators:
                    if isinstance(d, str):
                        if d == "staticmethod":
                            statics.add(fn_name)
                        elif d == "property":
                            props.add(fn_name)
            elif sk == "AnnAssign":
                target = cs.get("target")
                ft = ""
                if isinstance(target, dict):
                    target_kind = _str(target, "kind")
                    if target_kind == "Attribute":
                        owner = target.get("value")
                        if isinstance(owner, dict) and _str(owner, "id") == "self":
                            ft = _str(target, "attr")
                    else:
                        ft = _str(target, "id")
                dt = _str(cs, "decl_type")
                if dt == "":
                    dt = _str(cs, "resolved_type")
                if ft != "" and dt != "":
                    field_map[ft] = dt
        if len(field_map) == 0:
            for fname, ftype in _collect_class_fields(ctx, stmt):
                field_map[fname] = ftype
        ctx.class_static_methods[name] = statics
        ctx.class_property_methods[name] = props
        ctx.class_fields[name] = field_map


def _emit_module_header(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Emit require_relative statements for imports."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("ImportFrom", "Import"):
            _emit_import_stmt(ctx, stmt)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def transpile_to_ruby(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a complete Ruby source file from an EAST3 document.

    Returns:
        Ruby source code string, or empty string if module should be skipped.
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
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "ruby" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Skip runtime modules
    if _should_skip_module_ruby(module_id, mapping):
        return ""

    # built_in modules are provided by py_runtime; skip_modules in mapping handles this

    # Load module-level renamed symbols
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

    ctx.import_alias_modules = build_import_alias_map(meta)
    bindings = meta.get("import_bindings")
    if isinstance(bindings, list):
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            local_name = binding.get("local_name")
            runtime_module_id = binding.get("runtime_module_id")
            binding_kind = binding.get("binding_kind")
            resolved_binding_kind = binding.get("resolved_binding_kind")
            is_module_binding = binding_kind == "module" or resolved_binding_kind == "module"
            if not is_module_binding:
                continue
            if isinstance(local_name, str) and local_name != "" and isinstance(runtime_module_id, str) and runtime_module_id != "":
                ctx.import_alias_modules[local_name] = runtime_module_id
    if isinstance(bindings, list):
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            if binding.get("binding_kind") != "symbol":
                continue
            local_name = binding.get("local_name")
            export_name = binding.get("export_name")
            if not isinstance(local_name, str) or local_name == "":
                continue
            if isinstance(export_name, str) and export_name != "" and export_name[0].isupper():
                ctx.class_names.add(local_name)
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)

    # First pass: collect class info
    _collect_module_class_info(ctx, body)

    # Preamble
    _emit(ctx, "# frozen_string_literal: true")
    _emit_blank(ctx)

    # Emit require for py_runtime
    is_submodule = not ctx.is_entry
    if not is_submodule or is_type_id_table:
        emit_ctx_obj = _dict(meta, "emit_context")
        root_rel = _str(emit_ctx_obj, "root_rel_prefix") if emit_ctx_obj else "./"
        _emit(ctx, 'require_relative "' + root_rel + 'built_in/py_runtime"')
    _emit(ctx, "require 'set'")

    # Emit imports
    _emit_module_header(ctx, body)
    if isinstance(bindings, list):
        emitted_extra_imports: set[str] = set()
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            if binding.get("binding_kind") != "symbol":
                continue
            runtime_module_id = binding.get("runtime_module_id")
            if not isinstance(runtime_module_id, str) or runtime_module_id == "":
                continue
            export_name = binding.get("export_name")
            if runtime_module_id == "pytra.std.json" and export_name == "JsonVal":
                continue
            if _should_skip_module_ruby(runtime_module_id, ctx.mapping):
                continue
            rel_path = runtime_module_id.replace(".", "_")
            if rel_path in emitted_extra_imports:
                continue
            _emit(ctx, 'require_relative "' + rel_path + '"')
            emitted_extra_imports.add(rel_path)
    _emit_blank(ctx)

    # Emit module body (skip imports, already emitted)
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("ImportFrom", "Import"):
            continue
        _emit_stmt(ctx, stmt)

    # Emit main guard
    if len(main_guard) > 0 and ctx.is_entry:
        _emit_blank(ctx)
        _emit(ctx, "# main")
        _emit_body(ctx, main_guard)

    # For type_id_table module: append pytra_isinstance
    if is_type_id_table:
        _emit_blank(ctx)
        _emit(ctx, "def pytra_isinstance(actual, tid)")
        ctx.indent_level += 1
        _emit(ctx, "id_table[tid * 2] <= actual && actual <= id_table[tid * 2 + 1]")
        ctx.indent_level -= 1
        _emit(ctx, "end")

    result = "\n".join(ctx.lines)
    if not result.endswith("\n"):
        result = result + "\n"
    return result


emit_ruby_module = transpile_to_ruby
