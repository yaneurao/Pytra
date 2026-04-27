"""EAST3 → PHP source code emitter.

PHP emitter は CommonRenderer + override 構成。
PHP 固有のノード（$変数, ->アクセス, require_once 等）のみ override として実装する。

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.php.types import (
    php_type, php_zero_value, _safe_php_ident, _split_generic_args,
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
    # Current class context
    current_class: str = ""
    # Exception type IDs
    exception_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    # Module-level symbol renames
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    # Per-module temp counter
    temp_counter: int = 0
    # Current exception variable (set inside catch blocks for bare raise)
    current_exc_var: str = ""
    # Functions that have variadic (*args) parameters
    vararg_functions: set[str] = field(default_factory=set)
    # require_once lines already emitted
    required_files: set[str] = field(default_factory=set)
    # Function names (no $ prefix)
    function_names: set[str] = field(default_factory=set)


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
    value = node.get(key)
    if isinstance(value, str):
        return value
    return ""


def _bool(node: dict[str, JsonVal], key: str) -> bool:
    value = node.get(key)
    if isinstance(value, bool):
        return value
    return False


def _list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    value = node.get(key)
    if isinstance(value, list):
        return value
    return []


def _dict(node: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    value = node.get(key)
    if isinstance(value, dict):
        return value
    return {}


def _php_symbol_name(ctx: EmitContext, name: str) -> str:
    """Convert a name to a PHP symbol, applying renames."""
    if name in ctx.renamed_symbols:
        return _safe_php_ident(ctx.renamed_symbols[name])
    return _safe_php_ident(name)


def _php_var(name: str) -> str:
    """Add $ prefix for PHP variable names."""
    if name.startswith("$"):
        return name
    return "$" + name


def _php_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$") + '"'


def _is_exception_type_name(ctx: EmitContext, type_name: str) -> bool:
    """Check if a type name is an exception class."""
    if php_type(type_name).startswith("\\"):
        return True
    fqcn = ctx.module_id + "." + type_name
    if fqcn in ctx.exception_type_ids:
        return True
    if type_name in ctx.exception_type_ids:
        return True
    return False


def _class_extends_exception(ctx: EmitContext, class_name: str) -> bool:
    current = class_name
    seen: set[str] = set()
    while current != "" and current not in seen:
        seen.add(current)
        if _is_exception_type_name(ctx, current):
            return True
        current = ctx.class_bases.get(current, "")
    return False


def _exception_ctor_expr(type_name: str, message_code: str) -> str:
    php_exc = php_type(type_name)
    if php_exc in ("\\Exception", "\\RuntimeException", "\\InvalidArgumentException",
                    "\\TypeError", "\\OutOfRangeException"):
        return "new " + php_exc + "(" + message_code + ")"
    return "new \\Exception(" + message_code + ")"


def _is_function_symbol(ctx: EmitContext, name: str) -> bool:
    if name in ctx.function_names:
        return True
    resolved = _php_symbol_name(ctx, name)
    for fn_name in ctx.function_names:
        if _php_symbol_name(ctx, fn_name) == resolved:
            return True
    return False


# ---------------------------------------------------------------------------
# Expression emission
# ---------------------------------------------------------------------------

def _emit_expr(ctx: EmitContext, node: JsonVal) -> str:
    """Emit an expression and return PHP code string."""
    if not isinstance(node, dict):
        return "null"
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
    if kind == "Compare":
        return _emit_compare(ctx, node)
    if kind == "BoolOp":
        return _emit_boolop(ctx, node)
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
    if kind == "JoinedStr" or kind == "FString":
        return _emit_fstring(ctx, node)
    if kind == "Lambda" or kind == "ClosureExpr":
        return _emit_lambda(ctx, node)
    if kind == "ListComp":
        return _emit_list_comp(ctx, node)
    if kind == "GeneratorExp":
        return _emit_generator_exp(ctx, node)
    if kind == "SetComp":
        return _emit_set_comp(ctx, node)
    if kind == "DictComp":
        return _emit_dict_comp(ctx, node)
    if kind == "ObjBox" or kind == "ObjUnbox" or kind == "Box" or kind == "Unbox":
        inner = node.get("value")
        if inner is None:
            inner = node.get("body")
        if kind in ("Box", "Unbox") and isinstance(inner, dict) and _str(inner, "kind") == "Name":
            inner_name = _str(inner, "id")
            if inner_name in ctx.function_names:
                return "'" + _php_symbol_name(ctx, inner_name) + "'"
        return _emit_expr(ctx, inner)
    if kind == "IsInstance":
        return _emit_isinstance(ctx, node)
    if kind == "Slice":
        return _emit_slice(ctx, node)
    if kind == "RangeExpr":
        return _emit_range_expr(ctx, node)
    return "null /* unsupported: " + kind + " */"


def _emit_constant(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("$", "\\$") + '"'
    if isinstance(value, float):
        s = str(value)
        if s == "inf":
            return "INF"
        if s == "-inf":
            return "-INF"
        if s == "nan":
            return "NAN"
        return s
    return str(value)


def _emit_name(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "":
        name = _str(node, "repr")
    if name == "self" and ctx.current_class != "":
        return "$this"
    safe_name = _safe_php_ident(name)
    if name == "None":
        return "null"
    if name == "True":
        return "true"
    if name == "False":
        return "false"
    if name in ctx.var_types or safe_name in ctx.var_types:
        return _php_var(safe_name)
    # Check runtime_imports for mapped names
    if name in ctx.runtime_imports:
        return ctx.runtime_imports[name]
    if name in ("bytearray", "bytes"):
        return name
    if name in ctx.mapping.calls:
        mapped = ctx.mapping.calls[name]
        if isinstance(mapped, str) and mapped != "":
            return mapped
    rt = _str(node, "resolved_type")
    # Class names don't get $ prefix
    if name in ctx.class_names:
        return _php_symbol_name(ctx, name)
    # Function names as values should be emitted as PHP callables
    if _is_function_symbol(ctx, name):
        if rt.startswith("callable[") or rt.startswith("Callable[") or rt in ("callable", "Callable"):
            return "'" + _php_symbol_name(ctx, name) + "'"
        return _php_symbol_name(ctx, name)
    # Module-level constants (UPPER_CASE) don't get $ prefix when used as constants
    if rt == "module":
        return _php_symbol_name(ctx, name)
    if safe_name in ctx.var_types and (rt.startswith("callable[") or rt.startswith("Callable[") or rt in ("callable", "Callable")):
        return _php_var(safe_name)
    if rt.startswith("callable[") or rt.startswith("Callable[") or rt in ("callable", "Callable"):
        return _php_symbol_name(ctx, name)
    # Callable variables use PHP variable call syntax elsewhere
    return _php_var(_php_symbol_name(ctx, name))


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr = _str(node, "attr")
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
    if attr == "line" and (
        (owner_rt != "" and _class_extends_exception(ctx, owner_rt))
        or (owner_id == "self" and _class_extends_exception(ctx, ctx.current_class))
        or (owner_id != "" and owner_id == ctx.current_exc_var)
    ):
        attr = "_pytra_line"
    if attr == "__name__" and isinstance(owner_node, dict) and _str(owner_node, "kind") == "Call":
        owner_func = owner_node.get("func")
        if isinstance(owner_func, dict) and _str(owner_func, "kind") == "Name" and _str(owner_func, "id") == "type":
            args = _list(owner_node, "args")
            if len(args) >= 1:
                return "type(" + _emit_expr(ctx, args[0]) + ")->__name__"
    # Handle 'self.field' → '$this->field'
    if isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
        if attr in ctx.class_property_methods.get(owner_rt, set()):
            return "$this->" + attr + "()"
        return "$this->" + attr
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
                # Try module-qualified key first
                mod_short = mod_id.rsplit(".", 1)[-1]
                qualified_key = mod_short + "." + runtime_symbol
                if qualified_key in ctx.mapping.calls:
                    resolved = ctx.mapping.calls[qualified_key]
                    if resolved in ("__pytra_argv", "__pytra_path"):
                        return '$GLOBALS["' + resolved + '"]'
                    return resolved
                resolved = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping, module_id=mod_id)
                if resolved in ("__pytra_argv", "__pytra_path"):
                    return '$GLOBALS["' + resolved + '"]'
                return resolved
    # Class static access: ClassName::attr
    if isinstance(owner_node, dict):
        owner_id = _str(owner_node, "id")
        if owner_id in ctx.class_names:
            # Static property
            static_methods = ctx.class_static_methods.get(owner_id, set())
            if attr in static_methods:
                return owner_id + "::" + attr
            return owner_id + "::$" + attr
    owner = _emit_expr(ctx, owner_node)
    if isinstance(owner_node, dict):
        owner_rt = _str(owner_node, "resolved_type")
        if attr in ctx.class_property_methods.get(owner_rt, set()):
            return owner + "->" + attr + "()"
    # Check if owner is a class name (no $)
    if isinstance(owner_node, dict):
        owner_id = _str(owner_node, "id")
        if owner_id in ctx.class_names:
            return owner_id + "::" + attr
    return owner + "->" + attr


def _emit_subscript(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    slice_node = node.get("slice")
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        is_str = owner_rt == "str" or owner_rt == "string"
        if is_str:
            lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "0"
            if isinstance(upper, dict):
                upper_code = _emit_expr(ctx, upper)
                return "substr(" + owner + ", " + lower_code + ", " + upper_code + " - " + lower_code + ")"
            return "substr(" + owner + ", " + lower_code + ")"
        lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "0"
        if isinstance(upper, dict):
            upper_code = _emit_expr(ctx, upper)
            return "array_slice(" + owner + ", " + lower_code + ", " + upper_code + " - " + lower_code + ")"
        return "array_slice(" + owner + ", " + lower_code + ")"
    # For strings: use indexing
    is_str = owner_rt == "str" or owner_rt == "string"
    if is_str and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        return owner + "[__pytra_index(" + owner + ", " + slice_code + ")]"
    # For dicts: key access
    is_dict_type = owner_rt.startswith("dict[") or owner_rt == "dict"
    if is_dict_type and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        return owner + "[" + slice_code + "]"
    # For lists: handle negative constant indices
    is_array_like = (
        owner_rt.startswith("list[") or owner_rt in ("list", "bytes", "bytearray")
        or owner_rt.startswith("tuple[") or owner_rt == "tuple"
    )
    if is_array_like and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        return owner + "[__pytra_index(" + owner + ", " + slice_code + ")]"
    slice_code = _emit_expr(ctx, slice_node)
    return owner + "[" + slice_code + "]"


def _get_negative_int_literal(node: dict[str, JsonVal]) -> int | None:
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
    return "[" + ", ".join(elem_strs) + "]"


def _emit_dict_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    keys = _list(node, "keys")
    values = _list(node, "values")
    pairs: list[str] = []
    if len(keys) > 0:
        for i in range(len(keys)):
            k = _emit_expr(ctx, keys[i])
            v = _emit_expr(ctx, values[i]) if i < len(values) else "null"
            pairs.append(k + " => " + v)
    else:
        entries = _list(node, "entries")
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            pairs.append(_emit_expr(ctx, entry.get("key")) + " => " + _emit_expr(ctx, entry.get("value")))
    if len(pairs) == 0:
        return "[]"
    return "[" + ", ".join(pairs) + "]"


def _emit_set_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    # PHP sets are represented as associative arrays with values as keys
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    if len(elem_strs) == 0:
        return "[]"
    # Use array_flip or just map value => true
    pairs: list[str] = []
    for e in elem_strs:
        pairs.append(e + " => true")
    return "[" + ", ".join(pairs) + "]"


def _emit_tuple_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    return "[" + ", ".join(elem_strs) + "]"


def _php_condition_expr(ctx: EmitContext, node: JsonVal) -> str:
    """Render a condition expression, wrapping in truthiness check if needed."""
    if not isinstance(node, dict):
        return "false"
    rt = _str(node, "resolved_type")
    expr_code = _emit_expr(ctx, node)
    # bool is naturally truthy in PHP
    if rt == "bool":
        return expr_code
    # Numeric types: PHP handles 0/non-zero truthiness correctly
    if rt in ("int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64", "float64", "float32"):
        return expr_code
    # For containers and strings, PHP's truthiness differs from Python
    # PHP: empty string is falsy, "0" is falsy (Python: "0" is truthy)
    # Use __pytra_truthy for safety on non-trivial types
    is_collection = (
        rt.startswith("list[") or rt == "list"
        or rt.startswith("dict[") or rt == "dict"
        or rt.startswith("set[") or rt == "set"
        or rt.startswith("tuple[") or rt == "tuple"
    )
    if rt == "str" or rt == "string" or is_collection:
        return "__pytra_truthy(" + expr_code + ")"
    return expr_code


def _emit_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test = node.get("test")
    body = node.get("body")
    orelse = node.get("orelse")
    test_code = _php_condition_expr(ctx, test)
    body_code = _emit_expr(ctx, body)
    orelse_code = _emit_expr(ctx, orelse)
    return "(" + test_code + " ? " + body_code + " : " + orelse_code + ")"


def _emit_fstring(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    if len(values) == 0:
        return '""'
    parts: list[str] = []
    for v in values:
        if not isinstance(v, dict):
            continue
        kind = _str(v, "kind")
        if kind == "Constant":
            val = v.get("value")
            if isinstance(val, str):
                parts.append('"' + val.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$") + '"')
            else:
                parts.append(str(val))
        elif kind == "FormattedValue":
            fmt_value = v.get("value")
            conversion = _str(v, "conversion")
            format_spec = _str(v, "format_spec")
            expr_code = _emit_expr(ctx, fmt_value)
            fmt_rt = _str(fmt_value, "resolved_type") if isinstance(fmt_value, dict) else ""
            if format_spec != "":
                if format_spec.endswith("f"):
                    precision = format_spec[:-1]
                    if precision.startswith("."):
                        precision = precision[1:]
                    parts.append("number_format(" + expr_code + ", " + precision + ", '.', '')")
                elif format_spec.endswith("d"):
                    parts.append("sprintf('%" + format_spec + "', intval(" + expr_code + "))")
                else:
                    parts.append("sprintf('%" + format_spec + "', " + expr_code + ")")
            elif fmt_rt in ("int64", "int32", "int", "float64", "float32", "float", "bool"):
                parts.append("py_to_string(" + expr_code + ")")
            else:
                parts.append("py_to_string(" + expr_code + ")")
        else:
            parts.append(_emit_expr(ctx, v))
    if len(parts) == 0:
        return '""'
    if len(parts) == 1:
        return parts[0]
    return " . ".join(parts)


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    arg_order = _list(node, "arg_order")
    raw_args = _list(node, "args")
    if len(arg_order) == 0:
        for arg in raw_args:
            if isinstance(arg, dict):
                arg_name = _str(arg, "arg")
                if arg_name != "":
                    arg_order.append(arg_name)
    body_node = node.get("body")
    params: list[str] = []
    for a in arg_order:
        a_str = a if isinstance(a, str) else ""
        if a_str == "self":
            continue
        param_code = _php_var(_safe_php_ident(a_str))
        for raw_arg in raw_args:
            if not isinstance(raw_arg, dict) or _str(raw_arg, "arg") != a_str:
                continue
            default_node = raw_arg.get("default")
            if isinstance(default_node, dict):
                param_code += " = " + _emit_expr(ctx, default_node)
            break
        params.append(param_code)
    body_code = _emit_expr(ctx, body_node)
    # Check for captures
    captures = _list(node, "captures")
    if len(captures) == 0:
        param_names = {_safe_php_ident(a if isinstance(a, str) else "") for a in arg_order}
        captures = [name for name in sorted(ctx.var_types.keys()) if name not in ("",) and name not in param_names]
    use_clause = ""
    if len(captures) > 0:
        use_vars: list[str] = []
        for cap in captures:
            if isinstance(cap, dict):
                cap_name = _str(cap, "name")
                if cap_name != "":
                    use_vars.append(_php_var(_safe_php_ident(cap_name)))
            elif isinstance(cap, str) and cap != "":
                use_vars.append(_php_var(_safe_php_ident(cap)))
        if len(use_vars) > 0:
            use_clause = " use (" + ", ".join(use_vars) + ")"
    return "function(" + ", ".join(params) + ")" + use_clause + " { return " + body_code + "; }"


def _normalize_isinstance_type_name(type_name: str) -> str:
    parts = type_name.split("_")
    if len(parts) >= 3 and parts[0] == "PYTRA" and parts[1] == "TID":
        return parts[-1].lower()
    return type_name


def _emit_isinstance(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    obj_node = node.get("value")
    if obj_node is None:
        obj_node = node.get("obj")
    type_node = node.get("type")
    obj_code = _emit_expr(ctx, obj_node)
    type_name = _str(node, "expected_type_name")
    if isinstance(type_node, dict):
        if type_name == "":
            type_name = _str(type_node, "id")
        if type_name == "":
            type_name = _str(type_node, "repr")
    if type_name == "":
        type_name = _str(node, "type_name")
    if type_name == "":
        expected_type_id = node.get("expected_type_id")
        if isinstance(expected_type_id, dict):
            type_name = _str(expected_type_id, "type_object_of")
            if type_name == "":
                type_name = _str(expected_type_id, "id")
    type_name = _normalize_isinstance_type_name(type_name)
    # Map to PHP type check
    if type_name in ("int", "int64", "int32"):
        return "is_int(" + obj_code + ")"
    if type_name in ("float", "float64", "float32"):
        return "is_float(" + obj_code + ")"
    if type_name in ("str", "string"):
        return "is_string(" + obj_code + ")"
    if type_name in ("bool",):
        return "is_bool(" + obj_code + ")"
    if type_name in ("list", "dict", "set", "tuple"):
        return "is_array(" + obj_code + ")"
    return obj_code + " instanceof " + _safe_php_ident(type_name)


def _emit_slice(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    return "null /* slice */"


def _emit_range_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    start_node = node.get("start")
    stop_node = node.get("stop")
    step_node = node.get("step")
    start = _emit_expr(ctx, start_node) if isinstance(start_node, dict) else "0"
    stop = _emit_expr(ctx, stop_node) if isinstance(stop_node, dict) else "0"
    if isinstance(step_node, dict):
        step = _emit_expr(ctx, step_node)
        return "__pytra_range(" + start + ", " + stop + ", " + step + ")"
    return "__pytra_range(" + start + ", " + stop + ")"


# ---------------------------------------------------------------------------
# Comprehensions
# ---------------------------------------------------------------------------

def _comp_iter_code(ctx: EmitContext, gen: dict) -> str:
    iter_node = gen.get("iter")
    if not isinstance(iter_node, dict):
        return "[]"
    iter_code = _emit_expr(ctx, iter_node)
    iter_rt = _str(iter_node, "resolved_type")
    if iter_rt in ("str", "string"):
        return "__pytra_str_iter(" + iter_code + ")"
    if iter_rt.startswith("set[") or iter_rt == "set":
        return "__pytra_set_iter(" + iter_code + ")"
    return iter_code


def _emit_list_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = node.get("elt")
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "[]"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "[]"
    target = gen.get("target")
    iter_code = _comp_iter_code(ctx, gen)
    ifs = _list(gen, "ifs")
    target_name = "_item"
    setup = ""
    if isinstance(target, dict) and _str(target, "kind") == "Tuple":
        elts = _list(target, "elements")
        if len(elts) == 0:
            elts = _list(target, "elts")
        iter_tmp = _php_var(_next_temp(ctx, "it"))
        tv = iter_tmp
        parts: list[str] = []
        for i, elt_node in enumerate(elts):
            if isinstance(elt_node, dict):
                elt_name = _str(elt_node, "id")
                if elt_name != "":
                    safe_name = _safe_php_ident(elt_name)
                    ctx.var_types[safe_name] = ""
                    parts.append(_php_var(safe_name) + " = " + iter_tmp + "[" + str(i) + "];")
        if len(parts) > 0:
            setup = " " + " ".join(parts)
    else:
        target_name = _str(target, "id") if isinstance(target, dict) else "_item"
        tv = _php_var(_safe_php_ident(target_name))
        if target_name not in ("", "_item"):
            ctx.var_types[_safe_php_ident(target_name)] = ""
    elt_code = _emit_expr(ctx, elt)
    use_vars = [_php_var(name) for name in sorted(ctx.var_types.keys()) if name not in ("", target_name)]
    use_clause = " use (" + ", ".join(use_vars) + ")" if len(use_vars) > 0 else ""
    tmp = _next_temp(ctx, "lc")
    body_stmt = _php_var(tmp) + "[] = " + elt_code + ";"
    if len(ifs) > 0:
        body_stmt = "if (" + _php_condition_expr(ctx, ifs[0]) + ") { " + body_stmt + " }"
    return "(function()" + use_clause + " { " + _php_var(tmp) + " = []; foreach (" + iter_code + " as " + tv + ") {" + setup + " " + body_stmt + " } return " + _php_var(tmp) + "; })()"


def _emit_generator_exp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = node.get("elt")
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "[]"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "[]"
    target = gen.get("target")
    iter_code = _comp_iter_code(ctx, gen)
    ifs = _list(gen, "ifs")
    tmp = _next_temp(ctx, "ge")
    use_vars = [_php_var(name) for name in sorted(ctx.var_types.keys()) if name != ""]
    use_clause = " use (" + ", ".join(use_vars) + ")" if len(use_vars) > 0 else ""
    setup = ""
    if isinstance(target, dict) and _str(target, "kind") == "Tuple":
        elts = _list(target, "elements")
        if len(elts) == 0:
            elts = _list(target, "elts")
        iter_tmp = _php_var(_next_temp(ctx, "it"))
        parts: list[str] = []
        for i, elt_node in enumerate(elts):
            if isinstance(elt_node, dict):
                elt_name = _str(elt_node, "id")
                if elt_name != "":
                    parts.append(_php_var(_safe_php_ident(elt_name)) + " = " + iter_tmp + "[" + str(i) + "];")
        tv = iter_tmp
        if len(parts) > 0:
            setup = " " + " ".join(parts)
    else:
        target_name = _str(target, "id") if isinstance(target, dict) else "_item"
        tv = _php_var(_safe_php_ident(target_name))
        if target_name not in ("", "_item"):
            ctx.var_types[_safe_php_ident(target_name)] = ""
    elt_code = _emit_expr(ctx, elt)
    body_stmt = _php_var(tmp) + "[] = " + elt_code + ";"
    if len(ifs) > 0:
        body_stmt = "if (" + _php_condition_expr(ctx, ifs[0]) + ") { " + body_stmt + " }"
    return "(function()" + use_clause + " { " + _php_var(tmp) + " = []; foreach (" + iter_code + " as " + tv + ") {" + setup + " " + body_stmt + " } return " + _php_var(tmp) + "; })()"


def _emit_set_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = node.get("elt")
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "[]"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "[]"
    target = gen.get("target")
    target_name = _str(target, "id") if isinstance(target, dict) else "_item"
    iter_code = _comp_iter_code(ctx, gen)
    ifs = _list(gen, "ifs")
    tv = _php_var(_safe_php_ident(target_name))
    elt_code = _emit_expr(ctx, elt)
    use_vars = [_php_var(name) for name in sorted(ctx.var_types.keys()) if name not in ("", target_name)]
    use_clause = " use (" + ", ".join(use_vars) + ")" if len(use_vars) > 0 else ""
    tmp = _next_temp(ctx, "sc")
    body_stmt = _php_var(tmp) + "[" + elt_code + "] = true;"
    if len(ifs) > 0:
        body_stmt = "if (" + _php_condition_expr(ctx, ifs[0]) + ") { " + body_stmt + " }"
    return "(function()" + use_clause + " { " + _php_var(tmp) + " = []; foreach (" + iter_code + " as " + tv + ") { " + body_stmt + " } return " + _php_var(tmp) + "; })()"


def _emit_dict_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    key_node = node.get("key")
    value_node = node.get("value")
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "[]"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "[]"
    target = gen.get("target")
    target_name = _str(target, "id") if isinstance(target, dict) else "_item"
    iter_code = _comp_iter_code(ctx, gen)
    ifs = _list(gen, "ifs")
    tv = _php_var(_safe_php_ident(target_name))
    key_code = _emit_expr(ctx, key_node)
    val_code = _emit_expr(ctx, value_node)
    tmp = _next_temp(ctx, "dc")
    use_vars = [_php_var(name) for name in sorted(ctx.var_types.keys()) if name not in ("", target_name)]
    use_clause = " use (" + ", ".join(use_vars) + ")" if len(use_vars) > 0 else ""
    body_stmt = _php_var(tmp) + "[" + key_code + "] = " + val_code + ";"
    if len(ifs) > 0:
        body_stmt = "if (" + _php_condition_expr(ctx, ifs[0]) + ") { " + body_stmt + " }"
    return "(function()" + use_clause + " { " + _php_var(tmp) + " = []; foreach (" + iter_code + " as " + tv + ") { " + body_stmt + " } return " + _php_var(tmp) + "; })()"


# ---------------------------------------------------------------------------
# Call emission
# ---------------------------------------------------------------------------

def _resolve_runtime_call_name(ctx: EmitContext, node: dict[str, JsonVal], func: JsonVal) -> str:
    runtime_call = _str(node, "runtime_call")
    resolved_runtime_call = _str(node, "resolved_runtime_call")
    adapter_kind = _str(node, "runtime_call_adapter_kind")
    builtin_name = ""
    if isinstance(func, dict):
        builtin_name = _str(func, "id")
    lookup_key = resolved_runtime_call if resolved_runtime_call != "" else runtime_call
    if lookup_key != "" and lookup_key in ctx.mapping.calls:
        return ctx.mapping.calls[lookup_key]
    return resolve_runtime_call(runtime_call, builtin_name, adapter_kind, ctx.mapping)


def _is_float_type(rt: str) -> bool:
    return rt in ("float64", "float32", "float")


def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    func = node.get("func")
    args = _list(node, "args")
    keywords = _list(node, "keywords")
    arg_strs = [_emit_expr(ctx, a) for a in args]
    kw_strs: list[str] = []
    for kw in keywords:
        if isinstance(kw, dict):
            kw_strs.append(_emit_expr(ctx, kw.get("value")))
    all_arg_strs = arg_strs + kw_strs
    spread_arg = ""
    if isinstance(func, dict) and _str(func, "kind") == "Name":
        fn_id = _str(func, "id")
        if fn_id == "isinstance" and len(args) >= 2 and isinstance(args[0], dict) and isinstance(args[1], dict):
            type_node = args[1]
            type_name = _str(type_node, "id")
            if type_name == "":
                type_name = _str(type_node, "repr")
            return _emit_isinstance(ctx, {"kind": "IsInstance", "value": args[0], "expected_type_name": type_name})
        if fn_id in ctx.vararg_functions and len(args) >= 1:
            packed_arg = args[-1]
            if isinstance(packed_arg, dict) and _str(packed_arg, "kind") in ("List", "Tuple"):
                spread_arg = "..." + _emit_expr(ctx, packed_arg)
                arg_strs = [_emit_expr(ctx, a) for a in args[:-1]]
                all_arg_strs = arg_strs + kw_strs

    # BuiltinCall: runtime function
    lowered = _str(node, "lowered_kind")
    semantic_tag = _str(node, "semantic_tag")
    if lowered == "BuiltinCall" or lowered == "RuntimeCall":
        method_owner = ""
        builtin_arg_strs = list(all_arg_strs)
        if isinstance(func, dict) and _str(func, "kind") == "Attribute":
            owner_val = func.get("value")
            method_owner = _emit_expr(ctx, owner_val)
            builtin_arg_strs = [method_owner] + list(arg_strs)

        if semantic_tag == "core.bytearray_ctor":
            if len(all_arg_strs) >= 1:
                return "bytearray(" + all_arg_strs[0] + ")"
            return "bytearray()"
        if semantic_tag == "core.bytes_ctor":
            if len(all_arg_strs) >= 1:
                return "__pytra_bytes(" + all_arg_strs[0] + ")"
            return "__pytra_bytes()"
        if semantic_tag == "core.dict_ctor":
            if len(all_arg_strs) >= 1:
                return "(array)" + all_arg_strs[0]
            return "[]"
        if semantic_tag == "core.list_ctor":
            if len(all_arg_strs) >= 1:
                return "array_values(" + all_arg_strs[0] + ")"
            return "[]"
        if semantic_tag == "core.set_ctor":
            if len(all_arg_strs) > 0:
                return "set(" + all_arg_strs[0] + ")"
            return "set()"
        if semantic_tag == "core.tuple_ctor":
            return "[" + ", ".join(all_arg_strs) + "]"

        fn_name = _resolve_runtime_call_name(ctx, node, func)
        if fn_name != "" and fn_name != "__CAST__" and fn_name != "__PANIC__":
            runtime_symbol = _str(node, "runtime_symbol")
            if fn_name == "__LIST_CTOR__":
                if len(all_arg_strs) >= 1:
                    return "array_values(" + all_arg_strs[0] + ")"
                return "[]"
            if fn_name == "__TUPLE_CTOR__":
                return "[" + ", ".join(all_arg_strs) + "]"
            if fn_name == "__SET_CTOR__":
                if len(all_arg_strs) > 0:
                    return "set(" + all_arg_strs[0] + ")"
                return "set()"
            if fn_name == "__LIST_APPEND__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return owner + "[] = " + item
            if fn_name == "__LIST_POP__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                if len(builtin_arg_strs) >= 2:
                    return "array_splice(" + owner + ", " + builtin_arg_strs[1] + ", 1)[0]"
                return "array_pop(" + owner + ")"
            if fn_name == "__LIST_CLEAR__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + " = []"
            if fn_name == "__LIST_INDEX__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return "array_search(" + item + ", " + owner + ")"
            if fn_name == "__LIST_EXTEND__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                other = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "[]"
                return "__pytra_list_extend(" + owner + ", " + other + ")"
            if fn_name == "__LIST_INSERT__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                idx = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "0"
                item = builtin_arg_strs[2] if len(builtin_arg_strs) >= 3 else "null"
                return "array_splice(" + owner + ", " + idx + ", 0, [" + item + "])"
            if fn_name == "__LIST_SORT__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return "sort(" + owner + ")"
            if fn_name == "__LIST_REVERSE__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + " = array_reverse(" + owner + ")"
            if fn_name == "__DICT_GET__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                key = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                default = builtin_arg_strs[2] if len(builtin_arg_strs) >= 3 else "null"
                return "(array_key_exists(" + key + ", " + owner + ") ? " + owner + "[" + key + "] : " + default + ")"
            if fn_name == "__DICT_ITEMS__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return "__pytra_dict_items(" + owner + ")"
            if fn_name == "__DICT_KEYS__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return "array_keys(" + owner + ")"
            if fn_name == "__DICT_VALUES__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return "array_values(" + owner + ")"
            if fn_name == "__DICT_POP__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                key = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return "(function() use (&" + owner + ") { $__v = " + owner + "[" + key + "]; unset(" + owner + "[" + key + "]); return $__v; })()"
            if fn_name == "__DICT_UPDATE__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                other = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "[]"
                return owner + " = array_merge(" + owner + ", " + other + ")"
            if fn_name == "__SET_ADD__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return "__pytra_set_add(" + owner + ", " + item + ")"
            if fn_name == "__SET_UPDATE__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                other = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "[]"
                return "__pytra_set_update(" + owner + ", " + other + ")"
            if fn_name == "__SET_DISCARD__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return "unset(" + owner + "[" + item + "])"
            if fn_name == "__SET_REMOVE__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                item = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "null"
                return "unset(" + owner + "[" + item + "])"
            if fn_name == "__SET_CLEAR__":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else "null"
                return owner + " = set()"
            if runtime_symbol == "str.strip":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else '""'
                return "trim(" + owner + ")"
            if runtime_symbol == "str.rstrip":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else '""'
                return "rtrim(" + owner + ")"
            if runtime_symbol == "str.lstrip":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else '""'
                return "ltrim(" + owner + ")"
            if runtime_symbol == "str.startswith":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else '""'
                arg0 = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else '""'
                return "__pytra_str_startswith(" + owner + ", " + arg0 + ")"
            if runtime_symbol == "str.endswith":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else '""'
                arg0 = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else '""'
                return "__pytra_str_endswith(" + owner + ", " + arg0 + ")"
            if runtime_symbol == "str.replace":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else '""'
                old = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else '""'
                new = builtin_arg_strs[2] if len(builtin_arg_strs) >= 3 else '""'
                return "str_replace(" + old + ", " + new + ", " + owner + ")"
            if runtime_symbol == "str.join":
                owner = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else '""'
                arg0 = builtin_arg_strs[1] if len(builtin_arg_strs) >= 2 else "[]"
                return "implode(" + owner + ", " + arg0 + ")"
            if fn_name == "py_to_string" or runtime_symbol == "str":
                value = builtin_arg_strs[0] if len(builtin_arg_strs) >= 1 else '""'
                value_node = args[0] if len(args) >= 1 and isinstance(args[0], dict) else None
                value_rt = _str(value_node, "resolved_type") if isinstance(value_node, dict) else ""
                if value_rt != "":
                    return "py_to_string(" + value + ", " + _php_string(value_rt) + ")"
                return "py_to_string(" + value + ")"
            # Generic runtime call
            return fn_name + "(" + ", ".join(builtin_arg_strs) + ")"

        # static_cast → PHP cast
        if fn_name == "__CAST__":
            rt = _str(node, "resolved_type")
            if len(all_arg_strs) >= 1:
                if rt in ("int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64", "int"):
                    return "(int)(" + all_arg_strs[0] + ")"
                if rt in ("float64", "float32", "float"):
                    return "(float)(" + all_arg_strs[0] + ")"
                if rt in ("str", "string"):
                    return "(string)(" + all_arg_strs[0] + ")"
                if rt == "bool":
                    return "(bool)(" + all_arg_strs[0] + ")"
                return all_arg_strs[0]
            return "null"

        # Exception constructor
        if fn_name == "__PANIC__":
            msg = all_arg_strs[0] if len(all_arg_strs) >= 1 else '""'
            return "new \\RuntimeException(" + msg + ")"

    # Class constructor: new ClassName(args)
    if isinstance(func, dict) and _str(func, "kind") == "Name":
        fn_id = _str(func, "id")
        if fn_id in ctx.class_names:
            return "new " + _safe_php_ident(fn_id) + "(" + ", ".join(all_arg_strs) + ")"
        if _is_exception_type_name(ctx, fn_id):
            msg = all_arg_strs[0] if len(all_arg_strs) >= 1 else '""'
            return _exception_ctor_expr(fn_id, msg)
        if _is_function_symbol(ctx, fn_id):
            call_args = list(all_arg_strs)
            if spread_arg != "":
                call_args.append(spread_arg)
            return _php_symbol_name(ctx, fn_id) + "(" + ", ".join(call_args) + ")"

    # Static method call: ClassName.method(args) → ClassName::method(args)
    if isinstance(func, dict) and _str(func, "kind") == "Attribute":
        owner_val = func.get("value")
        attr = _str(func, "attr")
        if isinstance(owner_val, dict):
            owner_id = _str(owner_val, "id")
            if owner_id in ctx.class_names:
                static_methods = ctx.class_static_methods.get(owner_id, set())
                if attr in static_methods:
                    return owner_id + "::" + _safe_php_ident(attr) + "(" + ", ".join(all_arg_strs) + ")"

    # Method call: obj.method(args) → $obj->method(args)
    if isinstance(func, dict) and _str(func, "kind") == "Attribute":
        owner_val = func.get("value")
        attr = _str(func, "attr")
        if isinstance(owner_val, dict) and _str(owner_val, "kind") == "Name" and _str(owner_val, "id") == "super":
            return "parent::" + _safe_php_ident(attr) + "(" + ", ".join(all_arg_strs) + ")"
        if (
            isinstance(owner_val, dict)
            and _str(owner_val, "kind") == "Call"
            and isinstance(owner_val.get("func"), dict)
            and _str(owner_val.get("func"), "kind") == "Name"
            and _str(owner_val.get("func"), "id") == "super"
        ):
            if attr == "__init__":
                return "parent::__construct(" + ", ".join(all_arg_strs) + ")"
            return "parent::" + _safe_php_ident(attr) + "(" + ", ".join(all_arg_strs) + ")"
        if isinstance(owner_val, dict):
            owner_id = _str(owner_val, "id")
            owner_rt = _str(owner_val, "resolved_type")
            if owner_rt == "module" or owner_id in ctx.import_alias_modules:
                mod_id = _str(node, "runtime_module_id")
                if mod_id == "":
                    mod_id = ctx.import_alias_modules.get(owner_id, "")
                runtime_symbol = _str(node, "runtime_symbol")
                resolved_runtime_call = _str(node, "resolved_runtime_call")
                if runtime_symbol == "":
                    runtime_symbol = attr
                if should_skip_module(mod_id, ctx.mapping):
                    callee = resolve_runtime_symbol_name(
                        runtime_symbol,
                        ctx.mapping,
                        module_id=mod_id,
                        resolved_runtime_call=resolved_runtime_call,
                    )
                    return callee + "(" + ", ".join(all_arg_strs) + ")"
                return _safe_php_ident(runtime_symbol) + "(" + ", ".join(all_arg_strs) + ")"
        owner_code = _emit_expr(ctx, owner_val)
        # self.method() → $this->method()
        if isinstance(owner_val, dict) and _str(owner_val, "id") == "self":
            return "$this->" + _safe_php_ident(attr) + "(" + ", ".join(all_arg_strs) + ")"

        # String methods that take self as first arg → PHP string function
        owner_rt = _str(owner_val, "resolved_type") if isinstance(owner_val, dict) else ""
        owner_method_key = ""
        if owner_rt.startswith("list[") or "list[" in owner_rt or owner_rt in ("list", "bytes", "bytearray"):
            owner_method_key = ("bytearray." if owner_rt == "bytearray" else "list.") + attr
        elif owner_rt.startswith("dict[") or "dict[" in owner_rt or owner_rt == "dict":
            owner_method_key = "dict." + attr
        elif owner_rt in ("str", "string"):
            owner_method_key = "str." + attr
        elif owner_rt.startswith("set[") or "set[" in owner_rt or owner_rt == "set":
            owner_method_key = "set." + attr

        if owner_method_key != "":
            mapped_owner = ctx.mapping.calls.get(owner_method_key, "")
            owner_args = [owner_code] + all_arg_strs
            if mapped_owner == "__LIST_APPEND__":
                item = owner_args[1] if len(owner_args) >= 2 else "null"
                return owner_args[0] + "[] = " + item
            if mapped_owner == "__LIST_CLEAR__":
                return owner_args[0] + " = []"
            if mapped_owner == "__LIST_EXTEND__":
                other = owner_args[1] if len(owner_args) >= 2 else "[]"
                return "__pytra_list_extend(" + owner_args[0] + ", " + other + ")"
            if mapped_owner == "__LIST_POP__":
                if len(owner_args) >= 2:
                    return "array_splice(" + owner_args[0] + ", " + owner_args[1] + ", 1)[0]"
                return "array_pop(" + owner_args[0] + ")"
            if mapped_owner == "__LIST_INDEX__":
                item = owner_args[1] if len(owner_args) >= 2 else "null"
                return "array_search(" + item + ", " + owner_args[0] + ", true)"
            if mapped_owner == "__DICT_GET__":
                key = owner_args[1] if len(owner_args) >= 2 else "null"
                default = owner_args[2] if len(owner_args) >= 3 else "null"
                return "(array_key_exists(" + key + ", " + owner_args[0] + ") ? " + owner_args[0] + "[" + key + "] : " + default + ")"
            if mapped_owner == "__DICT_ITEMS__":
                return "__pytra_dict_items(" + owner_args[0] + ")"
            if mapped_owner == "__DICT_KEYS__":
                return "array_keys(" + owner_args[0] + ")"
            if mapped_owner == "__DICT_VALUES__":
                return "array_values(" + owner_args[0] + ")"
            if mapped_owner == "implode":
                return "implode(" + owner_args[0] + ", " + (owner_args[1] if len(owner_args) >= 2 else "[]") + ")"
            if mapped_owner == "__pytra_str_split":
                return "__pytra_str_split(" + owner_args[0] + ", " + (owner_args[1] if len(owner_args) >= 2 else '" "') + ")"
            if mapped_owner == "str_replace":
                return "str_replace(" + (owner_args[1] if len(owner_args) >= 2 else '""') + ", " + (owner_args[2] if len(owner_args) >= 3 else '""') + ", " + owner_args[0] + ")"
            if mapped_owner == "__pytra_str_startswith":
                return "__pytra_str_startswith(" + owner_args[0] + ", " + (owner_args[1] if len(owner_args) >= 2 else '""') + ")"
            if mapped_owner == "__pytra_str_endswith":
                return "__pytra_str_endswith(" + owner_args[0] + ", " + (owner_args[1] if len(owner_args) >= 2 else '""') + ")"
            if mapped_owner == "__pytra_str_find":
                return "__pytra_str_find(" + owner_args[0] + ", " + (owner_args[1] if len(owner_args) >= 2 else '""') + ")"
            if mapped_owner == "__pytra_str_rfind":
                return "__pytra_str_rfind(" + owner_args[0] + ", " + (owner_args[1] if len(owner_args) >= 2 else '""') + ")"
            if mapped_owner == "substr_count":
                return "substr_count(" + owner_args[0] + ", " + (owner_args[1] if len(owner_args) >= 2 else '""') + ")"
            if mapped_owner in {"trim", "ltrim", "rtrim", "strtoupper", "strtolower", "__pytra_str_isdigit", "__pytra_str_isalpha", "__pytra_str_isalnum", "__pytra_str_isspace"}:
                return mapped_owner + "(" + ", ".join(owner_args) + ")"
            if mapped_owner == "__SET_ADD__":
                item = owner_args[1] if len(owner_args) >= 2 else "null"
                return "__pytra_set_add(" + owner_args[0] + ", " + item + ")"
            if mapped_owner == "__SET_DISCARD__":
                item = owner_args[1] if len(owner_args) >= 2 else "null"
                return "__pytra_set_discard(" + owner_args[0] + ", " + item + ")"
            if mapped_owner == "__SET_REMOVE__":
                item = owner_args[1] if len(owner_args) >= 2 else "null"
                return "__pytra_set_remove(" + owner_args[0] + ", " + item + ")"
            if mapped_owner == "__SET_CLEAR__":
                return "__pytra_set_clear(" + owner_args[0] + ")"

        return owner_code + "->" + _safe_php_ident(attr) + "(" + ", ".join(all_arg_strs) + ")"

    # Regular function call
    fn_code = _emit_expr(ctx, func)
    if isinstance(func, dict) and _str(func, "kind") in ("Lambda", "ClosureExpr", "IfExp"):
        fn_code = "(" + fn_code + ")"
    # If fn_code starts with $ it's a variable call
    call_args = list(all_arg_strs)
    if spread_arg != "":
        call_args.append(spread_arg)
    return fn_code + "(" + ", ".join(call_args) + ")"


# ---------------------------------------------------------------------------
# Operator emission
# ---------------------------------------------------------------------------

def _emit_binop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    op = _str(node, "op")
    left_rt = _str(node.get("left"), "resolved_type") if isinstance(node.get("left"), dict) else ""
    right_rt = _str(node.get("right"), "resolved_type") if isinstance(node.get("right"), dict) else ""
    # Floor division
    if op == "FloorDiv":
        return "intdiv(" + left + ", " + right + ")"
    # Power
    if op == "Pow":
        return "(" + left + " ** " + right + ")"
    # String concatenation
    if op == "Add" and (left_rt == "str" or left_rt == "string" or right_rt == "str" or right_rt == "string"):
        return "(" + left + " . " + right + ")"
    # List concatenation
    if op == "Add" and (left_rt.startswith("list[") or left_rt == "list"):
        return "array_merge(" + left + ", " + right + ")"
    # String repetition
    if op == "Mult" and (left_rt == "str" or left_rt == "string"):
        return "str_repeat(" + left + ", " + right + ")"
    if op == "Mult" and (right_rt == "str" or right_rt == "string"):
        return "str_repeat(" + right + ", " + left + ")"
    # List repetition
    if op == "Mult" and (left_rt.startswith("list[") or left_rt == "list"):
        return "__pytra_list_repeat(" + left + ", " + right + ")"
    # Modulo
    if op == "Mod" and (left_rt == "str" or left_rt == "string"):
        # Python string formatting with % → use sprintf
        return "sprintf(" + left + ", " + right + ")"
    # Standard binary operators
    op_map: dict[str, str] = {
        "Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
        "Mod": "%", "BitAnd": "&", "BitOr": "|",
        "BitXor": "^", "LShift": "<<", "RShift": ">>",
    }
    op_text = op_map.get(op, op)
    return "(" + left + " " + op_text + " " + right + ")"


def _emit_unaryop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    op_map: dict[str, str] = {"USub": "-", "UAdd": "+", "Not": "!", "Invert": "~"}
    op_text = op_map.get(op, op)
    return "(" + op_text + operand + ")"


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return left
    parts: list[str] = []
    current_left = left
    for idx, comparator in enumerate(comparators):
        op_obj = ops[idx] if idx < len(ops) else None
        op_name = op_obj if isinstance(op_obj, str) else ""
        comp_code = _emit_expr(ctx, comparator)
        # In/NotIn → special handling
        if op_name == "In":
            comp_rt = _str(comparator, "resolved_type") if isinstance(comparator, dict) else ""
            if comp_rt in ("str", "string"):
                parts.append("(__pytra_contains(" + comp_code + ", " + current_left + "))")
            elif comp_rt.startswith("dict[") or comp_rt == "dict":
                parts.append("(__pytra_contains(" + comp_code + ", " + current_left + "))")
            elif comp_rt.startswith("set[") or comp_rt == "set":
                parts.append("(__pytra_contains(" + comp_code + ", " + current_left + "))")
            else:
                parts.append("(__pytra_contains(" + comp_code + ", " + current_left + "))")
        elif op_name == "NotIn":
            comp_rt = _str(comparator, "resolved_type") if isinstance(comparator, dict) else ""
            if comp_rt in ("str", "string"):
                parts.append("(!__pytra_contains(" + comp_code + ", " + current_left + "))")
            elif comp_rt.startswith("dict[") or comp_rt == "dict":
                parts.append("(!__pytra_contains(" + comp_code + ", " + current_left + "))")
            elif comp_rt.startswith("set[") or comp_rt == "set":
                parts.append("(!__pytra_contains(" + comp_code + ", " + current_left + "))")
            else:
                parts.append("(!__pytra_contains(" + comp_code + ", " + current_left + "))")
        elif op_name == "Is":
            parts.append("(" + current_left + " === " + comp_code + ")")
        elif op_name == "IsNot":
            parts.append("(" + current_left + " !== " + comp_code + ")")
        else:
            op_map: dict[str, str] = {
                "Eq": "===", "NotEq": "!==", "Lt": "<", "LtE": "<=",
                "Gt": ">", "GtE": ">=",
            }
            op_text = op_map.get(op_name, op_name)
            parts.append("(" + current_left + " " + op_text + " " + comp_code + ")")
        current_left = comp_code
    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    op = _str(node, "op")
    if len(values) == 0:
        return "false"
    result = _emit_expr(ctx, values[0])
    for value in values[1:]:
        rhs = _emit_expr(ctx, value)
        if op == "And":
            result = "(__pytra_truthy(" + result + ") ? " + rhs + " : " + result + ")"
        else:
            result = "(__pytra_truthy(" + result + ") ? " + result + " : " + rhs + ")"
    return result


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
    if vk == "Name":
        name_id = _str(value, "id")
        if name_id == "break":
            _emit(ctx, "break;")
            return
        if name_id == "continue":
            _emit(ctx, "continue;")
            return
        if name_id in ("del", "else", "pass"):
            return
        if _str(value, "resolved_type") == "unknown" and name_id in ("else", "pass", "Python", "Blank"):
            return
    _emit(ctx, _emit_expr(ctx, value) + ";")


def _emit_ann_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_val = node.get("target")
    rt = _str(node, "decl_type")
    if rt == "":
        rt = _str(node, "resolved_type")
    value = node.get("value")

    # Attribute assignment (self.x = ...)
    is_attr_target = isinstance(target_val, dict) and _str(target_val, "kind") == "Attribute"
    if is_attr_target:
        lhs = _emit_expr(ctx, target_val)
        if value is not None:
            _emit(ctx, lhs + " = " + _emit_expr(ctx, value) + ";")
        return

    # extern var → skip (handled by native runtime)
    meta = _dict(node, "meta")
    extern_v1 = meta.get("extern_var_v1")
    if isinstance(extern_v1, dict):
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

    name = _php_symbol_name(ctx, target_name)
    var_name = _php_var(name)

    if value is not None:
        val_code = _emit_expr(ctx, value)
        _emit(ctx, var_name + " = " + val_code + ";")
    else:
        zero = php_zero_value(rt)
        if zero != "":
            _emit(ctx, var_name + " = " + zero + ";")
    ctx.var_types[name] = rt


def _emit_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_val = node.get("target")
    value = node.get("value")

    # extern var → skip
    meta = _dict(node, "meta")
    extern_v1 = meta.get("extern_var_v1")
    if isinstance(extern_v1, dict):
        return

    # Attribute target
    if isinstance(target_val, dict) and _str(target_val, "kind") == "Attribute":
        lhs = _emit_expr(ctx, target_val)
        val_code = _emit_expr(ctx, value)
        _emit(ctx, lhs + " = " + val_code + ";")
        return

    # Subscript target
    if isinstance(target_val, dict) and _str(target_val, "kind") == "Subscript":
        lhs = _emit_expr(ctx, target_val)
        val_code = _emit_expr(ctx, value)
        _emit(ctx, lhs + " = " + val_code + ";")
        return

    # Tuple target (destructuring)
    if isinstance(target_val, dict) and _str(target_val, "kind") == "Tuple":
        elts = _list(target_val, "elements")
        if len(elts) == 0:
            elts = _list(target_val, "elts")
        val_code = _emit_expr(ctx, value)
        if len(elts) > 0:
            tmp = _next_temp(ctx, "tup")
            _emit(ctx, _php_var(tmp) + " = " + val_code + ";")
            for i, elt in enumerate(elts):
                if isinstance(elt, dict):
                    elt_name = _str(elt, "id")
                    if elt_name != "" and elt_name != "_":
                        _emit(ctx, _php_var(_php_symbol_name(ctx, elt_name)) + " = " + _php_var(tmp) + "[" + str(i) + "];")
                        ctx.var_types[_php_symbol_name(ctx, elt_name)] = ""
            return

    # Simple name target
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

    name = _php_symbol_name(ctx, target_name)
    var_name = _php_var(name)
    val_code = _emit_expr(ctx, value)
    value_rt = _str(value, "resolved_type") if isinstance(value, dict) else ""
    if (
        isinstance(value, dict)
        and _str(value, "kind") == "Name"
        and (
            value_rt.startswith("list[") or value_rt == "list"
            or value_rt.startswith("dict[") or value_rt == "dict"
            or value_rt.startswith("set[") or value_rt == "set"
        )
    ):
        _emit(ctx, var_name + " =& " + val_code + ";")
    else:
        _emit(ctx, var_name + " = " + val_code + ";")
    rt = _str(node, "resolved_type")
    if rt == "":
        rt = _str(node, "decl_type")
    ctx.var_types[name] = rt


def _emit_aug_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_val = node.get("target")
    value = node.get("value")
    op = _str(node, "op")
    lhs = _emit_expr(ctx, target_val)
    rhs = _emit_expr(ctx, value)
    target_rt = ""
    if isinstance(target_val, dict):
        target_rt = _str(target_val, "resolved_type")
    # String += is concatenation
    if op == "Add" and (target_rt == "str" or target_rt == "string"):
        _emit(ctx, lhs + " .= " + rhs + ";")
        return
    # List += is extend
    if op == "Add" and (target_rt.startswith("list[") or target_rt == "list"):
        _emit(ctx, lhs + " = array_merge(" + lhs + ", " + rhs + ");")
        return
    # FloorDiv
    if op == "FloorDiv":
        _emit(ctx, lhs + " = intdiv(" + lhs + ", " + rhs + ");")
        return
    op_map: dict[str, str] = {
        "Add": "+=", "Sub": "-=", "Mult": "*=", "Div": "/=",
        "Mod": "%=", "BitAnd": "&=", "BitOr": "|=",
        "BitXor": "^=", "LShift": "<<=", "RShift": ">>=",
        "Pow": "**=",
    }
    op_text = op_map.get(op, "+= /* unknown op: " + op + " */")
    _emit(ctx, lhs + " " + op_text + " " + rhs + ";")


def _emit_return(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if isinstance(value, dict):
        _emit(ctx, "return " + _emit_expr(ctx, value) + ";")
    else:
        _emit(ctx, "return;")


def _emit_raise(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    exc = node.get("exc")
    if isinstance(exc, dict):
        exc_code = _emit_expr(ctx, exc)
        exc_rt = _str(exc, "resolved_type")
        # If it's already an exception object, throw directly
        if _is_exception_type_name(ctx, exc_rt):
            if not exc_code.startswith("new "):
                exc_code = "new \\RuntimeException((string)" + exc_code + ")"
        _emit(ctx, "throw " + exc_code + ";")
    elif ctx.current_exc_var != "":
        _emit(ctx, "throw " + _php_var(ctx.current_exc_var) + ";")
    else:
        _emit(ctx, "throw new \\RuntimeException('');")


def _emit_try(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")
    _emit(ctx, "try {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    for handler in handlers:
        if not isinstance(handler, dict):
            continue
        handler_name = _str(handler, "name")
        handler_type = handler.get("type")
        type_name = ""
        if isinstance(handler_type, dict):
            type_name = _str(handler_type, "id")
        php_exc_type = "\\Exception"
        if type_name != "":
            mapped = php_type(type_name)
            if mapped.startswith("\\"):
                php_exc_type = mapped
            else:
                php_exc_type = _safe_php_ident(type_name)
        catch_var = handler_name if handler_name != "" else "__e"
        saved_exc = ctx.current_exc_var
        saved_var_type = ctx.var_types.get(catch_var)
        ctx.current_exc_var = catch_var
        if type_name != "":
            ctx.var_types[catch_var] = type_name
        _emit(ctx, "} catch (" + php_exc_type + " " + _php_var(catch_var) + ") {")
        ctx.indent_level += 1
        _emit_body(ctx, _list(handler, "body"))
        ctx.indent_level -= 1
        ctx.current_exc_var = saved_exc
        if saved_var_type is None:
            ctx.var_types.pop(catch_var, None)
        else:
            ctx.var_types[catch_var] = saved_var_type
    if len(finalbody) > 0:
        _emit(ctx, "} finally {")
        ctx.indent_level += 1
        _emit_body(ctx, finalbody)
        ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_var_decl(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    rt = _str(node, "resolved_type")
    if rt == "":
        rt = _str(node, "decl_type")
    value = node.get("value")
    var_name = _php_var(_php_symbol_name(ctx, name))
    if value is not None:
        val_code = _emit_expr(ctx, value)
        _emit(ctx, var_name + " = " + val_code + ";")
    else:
        zero = php_zero_value(rt)
        if zero != "":
            _emit(ctx, var_name + " = " + zero + ";")
    ctx.var_types[_php_symbol_name(ctx, name)] = rt


def _emit_swap(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    left_node = node.get("left")
    right_node = node.get("right")
    left_code = _emit_expr(ctx, left_node)
    right_code = _emit_expr(ctx, right_node)
    tmp = _next_temp(ctx, "swap")
    _emit(ctx, _php_var(tmp) + " = " + left_code + ";")
    _emit(ctx, left_code + " = " + right_code + ";")
    _emit(ctx, right_code + " = " + _php_var(tmp) + ";")


def _emit_multi_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    value = node.get("value")
    val_code = _emit_expr(ctx, value)
    if len(targets) > 0:
        tmp = _next_temp(ctx, "ma")
        _emit(ctx, _php_var(tmp) + " = " + val_code + ";")
        for i, tgt in enumerate(targets):
            if isinstance(tgt, dict):
                tgt_name = _str(tgt, "id")
                if tgt_name != "" and tgt_name != "_":
                    _emit(ctx, _php_var(_php_symbol_name(ctx, tgt_name)) + " = " + _php_var(tmp) + "[" + str(i) + "];")
                    ctx.var_types[_php_symbol_name(ctx, tgt_name)] = ""


# ---------------------------------------------------------------------------
# For loop emission
# ---------------------------------------------------------------------------

def _for_target_name_and_type(target_node: JsonVal) -> tuple[str, str]:
    if not isinstance(target_node, dict):
        return ("_item", "")
    tk = _str(target_node, "kind")
    if tk in ("Name", "NameTarget"):
        name = _str(target_node, "id")
        rt = _str(target_node, "target_type")
        if rt == "":
            rt = _str(target_node, "resolved_type")
        return (name, rt)
    return ("_item", "")


def _emit_for_core(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target_plan")
    if target_node is None:
        target_node = node.get("target")
    iter_plan = node.get("iter_plan")
    body = _list(node, "body")
    orelse = _list(node, "orelse")

    target_name, target_rt = _for_target_name_and_type(target_node)
    safe_target = _safe_php_ident(target_name) if target_name not in ("_item", "") else "_item"
    if safe_target != "_item" and safe_target != "_":
        ctx.var_types[safe_target] = target_rt

    if isinstance(iter_plan, dict):
        plan_kind = _str(iter_plan, "kind")
        if plan_kind == "StaticRangeForPlan":
            _emit_static_range_for_plan(ctx, iter_plan, safe_target, body)
            if len(orelse) > 0:
                _emit_body(ctx, orelse)
            return
        if plan_kind == "RuntimeIterForPlan":
            iter_node = iter_plan.get("iter_expr")
            iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"
            iter_rt = _str(iter_plan, "iter_type")
            if iter_rt == "":
                iter_rt = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
            if iter_rt in ("str", "string"):
                iter_code = "str_split(" + iter_code + ")"
            if iter_rt.startswith("set[") or iter_rt == "set":
                iter_code = "__pytra_set_iter(" + iter_code + ")"
            # Dict iteration → foreach with key => value
            is_dict = iter_rt.startswith("dict[") or iter_rt == "dict"
            if is_dict:
                # Tuple target for dict.items()
                if isinstance(target_node, dict) and _str(target_node, "kind") == "TupleTarget":
                    elts = _list(target_node, "elements")
                    if len(elts) >= 2:
                        k_name = _str(elts[0], "id") if isinstance(elts[0], dict) else "_k"
                        v_name = _str(elts[1], "id") if isinstance(elts[1], dict) else "_v"
                        _emit(ctx, "foreach (" + iter_code + " as " + _php_var(_safe_php_ident(k_name)) + " => " + _php_var(_safe_php_ident(v_name)) + ") {")
                        ctx.indent_level += 1
                        _emit_body(ctx, body)
                        ctx.indent_level -= 1
                        _emit(ctx, "}")
                        if len(orelse) > 0:
                            _emit_body(ctx, orelse)
                        return
            _emit(ctx, "foreach (" + iter_code + " as " + _php_var(safe_target) + ") {")
            ctx.indent_level += 1
            _emit_body(ctx, body)
            ctx.indent_level -= 1
            _emit(ctx, "}")
            if len(orelse) > 0:
                _emit_body(ctx, orelse)
            return

    # Fallback
    iter_node = node.get("iter")
    if iter_node is None:
        iter_node = iter_plan
    iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"
    iter_rt = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
    if iter_rt in ("str", "string"):
        iter_code = "str_split(" + iter_code + ")"
    if iter_rt.startswith("set[") or iter_rt == "set":
        iter_code = "__pytra_set_iter(" + iter_code + ")"
    _emit(ctx, "foreach (" + iter_code + " as " + _php_var(safe_target) + ") {")
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
    body: list[JsonVal],
) -> None:
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
        kind = _str(sn, "kind")
        if kind == "Constant":
            v = sn.get("value")
            return isinstance(v, (int, float)) and v < 0
        if kind == "UnaryOp" and _str(sn, "op") == "USub":
            return True
        return False
    descending = range_mode == "descending" or _is_negative_step(step_node)

    tv = _php_var(target_code)
    if descending:
        cmp_op = " > "
    else:
        cmp_op = " < "

    if step_is_one and not descending:
        _emit(ctx, "for (" + tv + " = " + start_code + "; " + tv + cmp_op + stop_code + "; " + tv + "++) {")
    else:
        _emit(ctx, "for (" + tv + " = " + start_code + "; " + tv + cmp_op + stop_code + "; " + tv + " += " + step_code + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_static_range_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target")
    body = _list(node, "body")
    target_name, target_rt = _for_target_name_and_type(target_node)
    safe_target = _safe_php_ident(target_name) if target_name not in ("_item", "") else "_i"
    if safe_target != "_i":
        ctx.var_types[safe_target] = target_rt
    _emit_static_range_for_plan(ctx, node, safe_target, body)


def _emit_runtime_iter_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target")
    iter_node = node.get("iter_expr")
    if iter_node is None:
        iter_node = node.get("iter")
    body = _list(node, "body")
    target_name, target_rt = _for_target_name_and_type(target_node)
    safe_target = _safe_php_ident(target_name) if target_name not in ("_item", "") else "_item"
    if safe_target != "_item":
        ctx.var_types[safe_target] = target_rt
    iter_code = _emit_expr(ctx, iter_node) if isinstance(iter_node, dict) else "[]"
    iter_rt = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
    if iter_rt in ("str", "string"):
        iter_code = "str_split(" + iter_code + ")"
    _emit(ctx, "foreach (" + iter_code + " as " + _php_var(safe_target) + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_with(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    items = _list(node, "items")
    body = _list(node, "body")
    for item in items:
        if not isinstance(item, dict):
            continue
        ctx_expr = item.get("context_expr")
        optional_var = item.get("optional_vars")
        ctx_code = _emit_expr(ctx, ctx_expr)
        if isinstance(optional_var, dict):
            var_name = _str(optional_var, "id")
            if var_name != "":
                _emit(ctx, _php_var(_safe_php_ident(var_name)) + " = " + ctx_code + ";")
    _emit(ctx, "try {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "} finally {")
    ctx.indent_level += 1
    for item in items:
        if not isinstance(item, dict):
            continue
        optional_var = item.get("optional_vars")
        if isinstance(optional_var, dict):
            var_name = _str(optional_var, "id")
            if var_name != "":
                _emit(ctx, _php_var(_safe_php_ident(var_name)) + "->close();")
    ctx.indent_level -= 1
    _emit(ctx, "}")


# ---------------------------------------------------------------------------
# Statement dispatch
# ---------------------------------------------------------------------------

def _emit_stmt(ctx: EmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        return
    kind = _str(node, "kind")
    if kind == "Expr":
        _emit_expr_stmt(ctx, node)
    elif kind == "AnnAssign":
        _emit_ann_assign(ctx, node)
    elif kind == "Assign":
        _emit_assign(ctx, node)
    elif kind == "AugAssign":
        _emit_aug_assign(ctx, node)
    elif kind == "Return":
        _emit_return(ctx, node)
    elif kind == "Raise":
        _emit_raise(ctx, node)
    elif kind == "Try":
        _emit_try(ctx, node)
    elif kind == "If":
        _emit_if_chain(ctx, node)
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
    elif kind == "TypeAlias":
        pass  # PHP has no type aliases
    elif kind == "Break":
        _emit(ctx, "break;")
    elif kind == "Continue":
        _emit(ctx, "continue;")
    elif kind == "Pass":
        _emit(ctx, "// pass")
    elif kind == "ErrorReturn" or kind == "ErrorCheck" or kind == "ErrorCatch":
        pass  # native_throw style: no-op
    elif kind == "comment":
        text = _str(node, "text")
        if text != "":
            _emit(ctx, "// " + text)
    elif kind == "blank":
        _emit_blank(ctx)
    elif kind == "Delete":
        targets = _list(node, "targets")
        for t in targets:
            if isinstance(t, dict):
                target_code = _emit_expr(ctx, t)
                _emit(ctx, "unset(" + target_code + ");")
    else:
        _emit(ctx, "// unsupported: " + kind)


def _emit_body(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        _emit_stmt(ctx, stmt)


def _emit_if_chain(ctx: EmitContext, node: dict[str, JsonVal], *, is_elif: bool = False) -> None:
    test = _php_condition_expr(ctx, node.get("test"))
    if is_elif:
        _emit(ctx, "} elseif (" + test + ") {")
    else:
        _emit(ctx, "if (" + test + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    orelse = _list(node, "orelse")
    if len(orelse) > 0:
        if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
            _emit_if_chain(ctx, orelse[0], is_elif=True)
            return
        _emit(ctx, "} else {")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_while(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    test = _php_condition_expr(ctx, node.get("test"))
    _emit(ctx, "while (" + test + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    _emit(ctx, "}")


# ---------------------------------------------------------------------------
# Import emission
# ---------------------------------------------------------------------------

def _emit_import_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    # PHP uses require_once for imports
    # Most imports of runtime modules are skipped (provided by py_runtime.php)
    pass


def _module_id_to_path(module_id: str) -> str:
    """Convert a module_id to a relative PHP file path."""
    rel = module_id
    if rel.startswith("pytra."):
        rel = rel[len("pytra."):]
    return rel.replace(".", "/") + ".php"


# ---------------------------------------------------------------------------
# Function definition
# ---------------------------------------------------------------------------

def _emit_function_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    return_type = _str(node, "return_type")
    body = _list(node, "body")
    decorators = _list(node, "decorators")
    is_closure = _str(node, "kind") == "ClosureDef" and ctx.current_class == ""

    # Skip extern declarations
    for d in decorators:
        if isinstance(d, str) and d == "extern":
            return

    is_staticmethod = False
    is_property = False
    for d in decorators:
        if isinstance(d, str):
            if d == "staticmethod":
                is_staticmethod = True
            elif d == "property":
                is_property = True

    # Map Python special method names
    if name == "__init__" and ctx.current_class != "":
        fn_name = "__construct"
    elif name == "__str__" and ctx.current_class != "":
        fn_name = "__toString"
    elif name == "__len__" and ctx.current_class != "":
        fn_name = "count"
    else:
        fn_name = _safe_php_ident(name)

    saved_vars = dict(ctx.var_types)
    saved_ret = ctx.current_return_type
    ctx.current_return_type = return_type

    arg_usage = _dict(node, "arg_usage")

    # Build parameter list
    params: list[str] = []
    for a in arg_order:
        a_str = a if isinstance(a, str) else ""
        if a_str == "self":
            continue
        if a_str == "cls":
            continue
        a_type_val = arg_types.get(a_str, "")
        a_type = a_type_val if isinstance(a_type_val, str) else ""
        safe_a = _safe_php_ident(a_str)
        ctx.var_types[safe_a] = a_type
        by_ref = _str(arg_usage, a_str) == "reassigned"
        params.append(("&" if by_ref else "") + _php_var(safe_a))

    # Handle varargs
    vararg_name_raw = _str(node, "vararg_name")
    if vararg_name_raw != "":
        safe_varg = _safe_php_ident(vararg_name_raw)
        params.append("..." + _php_var(safe_varg))
        ctx.vararg_functions.add(fn_name)

    # Return type
    ret_ann = ""
    if return_type in ("None", "none", "void", ""):
        has_value_return = False
        for stmt in body:
            if isinstance(stmt, dict) and _str(stmt, "kind") == "Return" and isinstance(stmt.get("value"), dict):
                has_value_return = True
                break
        if fn_name == "__construct":
            ret_ann = ""
        elif has_value_return:
            ret_ann = ""
        else:
            ret_ann = ": void"
    else:
        pt = php_type(return_type, for_return=True)
        if pt not in ("mixed", "void"):
            ret_ann = ": " + pt

    # Emit function
    if ctx.current_class != "" and not is_staticmethod:
        if is_property:
            _emit(ctx, "public function " + fn_name + "()" + ret_ann + " {")
        else:
            _emit(ctx, "public function " + fn_name + "(" + ", ".join(params) + ")" + ret_ann + " {")
    elif ctx.current_class != "" and is_staticmethod:
        _emit(ctx, "public static function " + fn_name + "(" + ", ".join(params) + ")" + ret_ann + " {")
    elif is_closure:
        # ClosureDef: anonymous function assigned to variable
        captures = _list(node, "captures")
        use_clause = ""
        if len(captures) > 0:
            use_vars: list[str] = []
            for cap in captures:
                if isinstance(cap, dict):
                    cap_name = _str(cap, "name")
                    mode = _str(cap, "mode")
                    if cap_name != "":
                        prefix = "&" if mode == "mutable" else ""
                        use_vars.append(prefix + _php_var(_safe_php_ident(cap_name)))
                elif isinstance(cap, str) and cap != "":
                    use_vars.append(_php_var(_safe_php_ident(cap)))
            if len(use_vars) > 0:
                use_clause = " use (" + ", ".join(use_vars) + ")"
        _emit(ctx, _php_var(fn_name) + " = function(" + ", ".join(params) + ")" + use_clause + ret_ann + " {")
    else:
        _emit(ctx, "function " + fn_name + "(" + ", ".join(params) + ")" + ret_ann + " {")

    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1

    if is_closure:
        _emit(ctx, "};")
    else:
        _emit(ctx, "}")
    if ctx.current_class == "":
        _emit_blank(ctx)

    ctx.var_types = saved_vars
    ctx.current_return_type = saved_ret


# ---------------------------------------------------------------------------
# Class definition
# ---------------------------------------------------------------------------

def _collect_class_fields(ctx: EmitContext, node: dict[str, JsonVal]) -> list[tuple[str, str]]:
    """Collect class fields from field_types or __init__ body."""
    fields: list[tuple[str, str]] = []
    field_types = _dict(node, "field_types")
    if field_types:
        for fname, ftype in field_types.items():
            if isinstance(fname, str) and isinstance(ftype, str):
                fields.append((fname, ftype))
        return fields
    # Look for self.x assignments in __init__
    body = _list(node, "body")
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _str(stmt, "kind") == "FunctionDef" and _str(stmt, "name") == "__init__":
            init_body = _list(stmt, "body")
            for s in init_body:
                if not isinstance(s, dict):
                    continue
                sk = _str(s, "kind")
                if sk in ("Assign", "AnnAssign"):
                    target = s.get("target")
                    if isinstance(target, dict) and _str(target, "kind") == "Attribute":
                        owner = target.get("value")
                        if isinstance(owner, dict) and _str(owner, "id") == "self":
                            attr = _str(target, "attr")
                            rt = _str(s, "decl_type")
                            if rt == "":
                                rt = _str(s, "resolved_type")
                            if rt == "":
                                rt = "mixed"
                            fields.append((attr, rt))
    return fields


def _emit_class_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    bases = _list(node, "bases")
    body = _list(node, "body")
    decorators = _list(node, "decorators")

    safe_name = _safe_php_ident(name)
    # Try "base" (singular, EAST3 format) then "bases" (list format)
    base_class = _str(node, "base")
    if base_class == "" and len(bases) > 0:
        first_base = bases[0]
        if isinstance(first_base, dict):
            base_class = _str(first_base, "id")
        elif isinstance(first_base, str):
            base_class = first_base
    if base_class in ("object",):
        base_class = ""

    extends_clause = ""
    if base_class != "":
        if _is_exception_type_name(ctx, base_class):
            php_base = php_type(base_class)
            if php_base.startswith("\\"):
                extends_clause = " extends " + php_base
            else:
                extends_clause = " extends " + _safe_php_ident(base_class)
        else:
            extends_clause = " extends " + _safe_php_ident(base_class)

    _emit(ctx, "class " + safe_name + extends_clause + " {")
    ctx.indent_level += 1

    saved_class = ctx.current_class
    ctx.current_class = name

    # Emit field declarations
    fields = _collect_class_fields(ctx, node)
    is_enum_like = base_class in ("Enum", "IntEnum", "IntFlag")
    if is_enum_like:
        fields = []
    field_names = {fname for fname, _ in fields}
    field_defaults: dict[str, JsonVal] = {}
    static_field_names: set[str] = set()
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _str(stmt, "kind") not in ("AnnAssign", "Assign"):
            continue
        target = stmt.get("target")
        if isinstance(target, dict):
            tid = _str(target, "id")
            if tid != "":
                if tid in field_names and isinstance(stmt.get("value"), dict):
                    field_defaults[tid] = stmt.get("value")
                    continue
                static_field_names.add(tid)
        elif isinstance(target, str) and target != "":
            if target in field_names and isinstance(stmt.get("value"), dict):
                field_defaults[target] = stmt.get("value")
                continue
            static_field_names.add(target)
    for fname, ftype in fields:
        emit_name = fname
        if _class_extends_exception(ctx, name) and fname == "line":
            emit_name = "_pytra_line"
        if fname in static_field_names:
            continue
        pt = php_type(ftype)
        _emit(ctx, "public " + _php_var(emit_name) + ";")

    if len(fields) > 0:
        _emit_blank(ctx)

    has_init = False
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef") and _str(stmt, "name") == "__init__":
            has_init = True
            break
    if len(fields) > 0 and not has_init:
        ctor_params: list[str] = []
        for fname, _ftype in fields:
            param = _php_var(_safe_php_ident(fname))
            default_node = field_defaults.get(fname)
            if isinstance(default_node, dict):
                param += " = " + _emit_expr(ctx, default_node)
            else:
                param += " = " + php_zero_value(_ftype)
            ctor_params.append(param)
        _emit(ctx, "public function __construct(" + ", ".join(ctor_params) + ") {")
        ctx.indent_level += 1
        for fname, _ftype in fields:
            emit_name = fname
            if _class_extends_exception(ctx, name) and fname == "line":
                emit_name = "_pytra_line"
            _emit(ctx, "$this->" + emit_name + " = " + _php_var(_safe_php_ident(fname)) + ";")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit_blank(ctx)

    # Emit methods
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("AnnAssign", "Assign"):
            # Class-level variable declarations (constants, defaults)
            target = stmt.get("target")
            value = stmt.get("value")
            if isinstance(target, dict):
                attr = _str(target, "attr")
                if attr != "" and value is not None:
                    # self.x = ... already handled in __init__
                    owner = target.get("value")
                    if isinstance(owner, dict) and _str(owner, "id") == "self":
                        continue
                tid = _str(target, "id")
                if tid != "" and value is not None:
                    if tid in field_names:
                        continue
                    val_code = _emit_expr(ctx, value)
                    _emit(ctx, "public static " + _php_var(_safe_php_ident(tid)) + " = " + val_code + ";")
            elif isinstance(target, str) and value is not None:
                if target in field_names:
                    continue
                val_code = _emit_expr(ctx, value)
                _emit(ctx, "public static " + _php_var(_safe_php_ident(target)) + " = " + val_code + ";")
            continue
        if kind == "FunctionDef" or kind == "ClosureDef":
            _emit_function_def(ctx, stmt)
            continue
        if kind == "Pass":
            continue
        if kind == "comment":
            text = _str(stmt, "text")
            if text != "":
                _emit(ctx, "// " + text)
            continue
        if kind == "blank":
            _emit_blank(ctx)
            continue
        _emit_stmt(ctx, stmt)

    ctx.current_class = saved_class
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)


# ---------------------------------------------------------------------------
# Module-level collection
# ---------------------------------------------------------------------------

def _collect_module_class_info(ctx: EmitContext, body: list[JsonVal]) -> None:
    """First pass: collect class names, function names, inheritance, static methods."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            if fn_name != "":
                ctx.function_names.add(fn_name)
            continue
        if kind != "ClassDef":
            continue
        name = _str(stmt, "name")
        ctx.class_names.add(name)
        # Try "base" (singular, EAST3 format) then "bases" (list format)
        base_name = _str(stmt, "base")
        if base_name == "":
            bases = _list(stmt, "bases")
            if len(bases) > 0:
                first_base = bases[0]
                if isinstance(first_base, dict):
                    base_name = _str(first_base, "id")
                elif isinstance(first_base, str):
                    base_name = first_base
        if base_name not in ("", "object"):
            ctx.class_bases[name] = base_name
        static_methods: set[str] = set()
        property_methods: set[str] = set()
        class_body = _list(stmt, "body")
        for method in class_body:
            if not isinstance(method, dict):
                continue
            if _str(method, "kind") in ("FunctionDef", "ClosureDef"):
                method_name = _str(method, "name")
                decs = _list(method, "decorators")
                for d in decs:
                    if isinstance(d, str):
                        if d == "staticmethod":
                            static_methods.add(method_name)
                        elif d == "property":
                            property_methods.add(method_name)
        ctx.class_static_methods[name] = static_methods
        ctx.class_property_methods[name] = property_methods


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

def emit_php_module(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a complete PHP source file from an EAST3 document.

    Args:
        east3_doc: linked EAST3 JSON dict with meta.linked_program_v1.

    Returns:
        PHP source code string, or empty string if module should be skipped.
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
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "php" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Skip runtime modules
    if should_skip_module(module_id, mapping):
        return ""

    # Load module-level renamed symbols
    renamed_symbols_raw = east3_doc.get("renamed_symbols")
    renamed_symbols: dict[str, str] = {}
    if isinstance(renamed_symbols_raw, dict):
        for orig, rn in renamed_symbols_raw.items():
            if isinstance(orig, str) and isinstance(rn, str):
                renamed_symbols[orig] = rn

    ctx = EmitContext(
        module_id=module_id,
        source_path=_str(east3_doc, "source_path"),
        is_entry=_bool(emit_ctx_meta, "is_entry") if emit_ctx_meta else False,
        mapping=mapping,
        renamed_symbols=renamed_symbols,
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
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)

    # First pass: collect class info
    _collect_module_class_info(ctx, body)

    # Emit PHP header
    _emit(ctx, "<?php")
    _emit(ctx, "declare(strict_types=1);")
    _emit_blank(ctx)

    # Emit require_once for runtime
    _emit(ctx, "require_once __DIR__ . '/built_in/py_runtime.php';")

    # Emit require_once for native modules referenced by imports
    import_bindings = meta.get("import_bindings")
    if isinstance(import_bindings, list):
        for binding in import_bindings:
            if not isinstance(binding, dict):
                continue
            mod_id = binding.get("module_id")
            if not isinstance(mod_id, str):
                continue
            runtime_mod_id = binding.get("runtime_module_id")
            runtime_mod = runtime_mod_id if isinstance(runtime_mod_id, str) and runtime_mod_id != "" else mod_id
            if runtime_mod in mapping.module_native_files:
                native_file = mapping.module_native_files[runtime_mod]
                if native_file not in ctx.required_files:
                    ctx.required_files.add(native_file)
                    _emit(ctx, "require_once __DIR__ . '/" + native_file + "';")
            elif runtime_mod.startswith("pytra.") and not should_skip_module(runtime_mod, mapping):
                module_file = runtime_mod.replace(".", "_") + ".php"
                if module_file not in ctx.required_files:
                    ctx.required_files.add(module_file)
                    _emit(ctx, "require_once __DIR__ . '/" + module_file + "';")

    _emit_blank(ctx)

    # Emit module body (skip imports, already handled)
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

    return "\n".join(ctx.lines).rstrip() + "\n"


def transpile_to_php(east3_doc: dict[str, JsonVal]) -> str:
    """Compatibility entry point."""
    return emit_php_module(east3_doc)
