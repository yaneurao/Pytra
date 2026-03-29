"""EAST3 → Rust source code emitter.

Go emitter を参考に CommonRenderer + override 構成で作成。
入力は linked EAST3 JSON (dict) のみ。toolchain/ への依存なし。

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.emit.rs.types import (
    rs_type,
    rs_zero_value,
    rs_signature_type,
    safe_rs_ident,
    _split_generic_args,
)
from toolchain2.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_import_alias_map, build_runtime_import_map,
    resolve_runtime_symbol_name,
)
from toolchain2.emit.common.common_renderer import CommonRenderer


# ---------------------------------------------------------------------------
# Emit context (mutable state for one module emission)
# ---------------------------------------------------------------------------

@dataclass
class RsEmitContext:
    """Per-module mutable state during Rust emission."""
    module_id: str = ""
    source_path: str = ""
    is_entry: bool = False
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    # Variable types in current scope
    var_types: dict[str, str] = field(default_factory=dict)
    # Current function return type
    current_return_type: str = ""
    # Imported runtime symbols mapped to emitted helper names
    runtime_imports: dict[str, str] = field(default_factory=dict)
    # Runtime mapping (from mapping.json)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    # Import alias → module_id map
    import_alias_modules: dict[str, str] = field(default_factory=dict)
    # Class info
    class_names: set[str] = field(default_factory=set)
    trait_names: set[str] = field(default_factory=set)
    class_bases: dict[str, str] = field(default_factory=dict)
    class_fields: dict[str, dict[str, str]] = field(default_factory=dict)
    class_static_methods: dict[str, set[str]] = field(default_factory=dict)
    class_instance_methods: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    enum_members: dict[str, list[str]] = field(default_factory=dict)
    enum_bases: dict[str, str] = field(default_factory=dict)
    function_signatures: dict[str, dict[str, JsonVal]] = field(default_factory=dict)
    # Current class context (for method emission)
    current_class: str = ""
    # Variables that have been declared in the current scope
    declared_vars: set[str] = field(default_factory=set)
    # Temp counter
    temp_counter: int = 0
    # Module-level private symbols
    module_private_symbols: set[str] = field(default_factory=set)
    # Use statements needed
    uses_needed: set[str] = field(default_factory=set)
    # Map from original_name → renamed name (for compiler-renamed functions)
    original_name_map: dict[str, str] = field(default_factory=dict)
    # Whether we are currently at module level (outside any function/class body)
    at_module_level: bool = True
    # Module-level static variables (lowercase name → uppercase static name)
    module_statics: dict[str, str] = field(default_factory=dict)
    # Class field default values: {class_name: {field_name: default_expr_or_None}}
    class_field_defaults: dict[str, dict[str, str | None]] = field(default_factory=dict)
    # Class vars (class-level attributes): {class_name: {field_name: type}}
    class_vars: dict[str, dict[str, str]] = field(default_factory=dict)
    # Name of currently-being-defined nested closure (for self-recursive call detection)
    current_nested_fn: str = ""
    # @property methods: {class_name: {method_name}}
    class_property_methods: dict[str, set[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _str(node: JsonVal, key: str) -> str:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, str):
            return v
    return ""


def _list(node: JsonVal, key: str) -> list[JsonVal]:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, list):
            return v
    return []


def _dict(node: JsonVal, key: str) -> dict[str, JsonVal]:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, dict):
            return v
    return {}


def _bool(node: JsonVal, key: str) -> bool:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, bool):
            return v
    return False


def _indent(ctx: RsEmitContext) -> str:
    return "    " * ctx.indent_level


def _emit(ctx: RsEmitContext, line: str) -> None:
    ctx.lines.append(_indent(ctx) + line)


def _emit_raw(ctx: RsEmitContext, line: str) -> None:
    ctx.lines.append(line)


def _emit_blank(ctx: RsEmitContext) -> None:
    ctx.lines.append("")


def _next_temp(ctx: RsEmitContext, prefix: str) -> str:
    ctx.temp_counter += 1
    return "__" + prefix + "_" + str(ctx.temp_counter)


def _module_prefix(ctx: RsEmitContext) -> str:
    if ctx.module_id == "":
        return ""
    return safe_rs_ident(ctx.module_id.replace(".", "_"))


def _rs_symbol_name(ctx: RsEmitContext, name: str) -> str:
    """Resolve a module-level symbol name (add prefix for private module symbols)."""
    # Resolve original_name → renamed name (for compiler-renamed functions)
    resolved = ctx.original_name_map.get(name, name)
    if resolved.startswith("_") and resolved in ctx.module_private_symbols and ctx.module_id != "":
        prefix = _module_prefix(ctx)
        if prefix != "":
            return prefix + "__" + resolved[1:]
    return safe_rs_ident(resolved)


def _rs_var_name(ctx: RsEmitContext, name: str) -> str:
    """Resolve a local variable name."""
    return safe_rs_ident(name)


def _rs_type_for_context(ctx: RsEmitContext, resolved_type: str) -> str:
    """Get Rust type, considering class/trait names in context."""
    # Enum/IntFlag classes are Copy value types — no Box<> wrapper
    if resolved_type in ctx.enum_bases:
        return safe_rs_ident(resolved_type)
    return rs_signature_type(resolved_type, ctx.class_names, ctx.trait_names)


# ---------------------------------------------------------------------------
# CommonRenderer subclass
# ---------------------------------------------------------------------------

class _RsStmtCommonRenderer(CommonRenderer):
    def __init__(self, ctx: RsEmitContext) -> None:
        self.ctx = ctx
        super().__init__("rs")
        self.state.lines = ctx.lines
        self.state.indent_level = ctx.indent_level

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(self.ctx, node)

    def render_expr(self, node: JsonVal) -> str:
        return _emit_expr(self.ctx, node)

    def render_condition_expr(self, node: JsonVal) -> str:
        # Rust: no parens around condition
        return _emit_expr(self.ctx, node)

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("rs common renderer assign string hook is not used directly")

    def render_raise_value(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("rs common renderer raise value hook is not used directly")

    def render_except_open(self, handler: dict[str, JsonVal]) -> str:
        raise RuntimeError("rs common renderer except hook is not used directly")

    def emit_return_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_return(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_expr_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_expr_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        kind = self._str(node, "kind")
        if kind == "AnnAssign":
            _emit_ann_assign(self.ctx, node)
        else:
            _emit_assign(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_raise_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_raise(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_try_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_try(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_stmt(self, node: JsonVal) -> None:
        kind = self._str(node, "kind")
        if kind in ("Expr", "Return", "Assign", "AnnAssign", "Pass", "Raise", "Try",
                    "comment", "blank", "If", "While"):
            super().emit_stmt(node)
            self.ctx.indent_level = self.state.indent_level
            return
        if isinstance(node, dict):
            self.emit_stmt_extension(node)

    def emit_stmt_extension(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level


# ---------------------------------------------------------------------------
# Expression emission
# ---------------------------------------------------------------------------

def _emit_name(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "":
        return "_"
    if name == "None":
        return "None"
    if name == "True":
        return "true"
    if name == "False":
        return "false"
    if name == "self":
        return "self"
    # Check if it's a class name (constructor call handled elsewhere)
    if name in ctx.class_names:
        return safe_rs_ident(name)
    # Check for module-level static variable
    static_name = ctx.module_statics.get(name)
    if static_name is not None:
        return "unsafe { " + static_name + " }"
    # Check for runtime symbol
    mapped = ctx.runtime_imports.get(name)
    if mapped is not None and mapped != "":
        return mapped
    return _rs_symbol_name(ctx, name)


def _emit_constant(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    resolved_type = _str(node, "resolved_type")
    # Check for body cast (numeric_promotion: int → float)
    has_float_body_cast = any(
        isinstance(c, dict) and _str(c, "on") == "body" and _str(c, "to") in ("float64", "float32", "float")
        for c in _list(node, "casts")
    )
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        # String literals: emit as &str or String depending on context
        # For now emit as .to_string() for owned strings
        call_arg_type = _str(node, "call_arg_type")
        if call_arg_type == "str" or resolved_type == "str":
            return '"' + escaped + '".to_string()'
        return '"' + escaped + '"'
    if isinstance(value, int):
        # If there's a float promotion cast, emit without type suffix (let context/call-site determine)
        if has_float_body_cast:
            return str(value)
        # Emit typed integer literal
        if resolved_type == "int64" or resolved_type == "int":
            result = str(value) + "_i64"
        elif resolved_type == "int32":
            result = str(value) + "_i32"
        elif resolved_type == "int16":
            result = str(value) + "_i16"
        elif resolved_type == "int8":
            result = str(value) + "_i8"
        elif resolved_type == "uint64":
            result = str(value) + "_u64"
        elif resolved_type == "uint32":
            result = str(value) + "_u32"
        elif resolved_type == "uint16":
            result = str(value) + "_u16"
        elif resolved_type == "uint8":
            result = str(value) + "_u8"
        else:
            result = str(value)
        return result
    if isinstance(value, float):
        s = str(value)
        if "." not in s and "e" not in s and "E" not in s:
            s = s + ".0"
        if resolved_type == "float32":
            return s + "_f32"
        return s + "_f64"
    return str(value)


def _apply_cast(expr: str, cast_to: str) -> str:
    """Wrap expr with a Rust cast if needed."""
    rt = rs_type(cast_to)
    if rt in ("i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "f32", "f64", "usize", "isize"):
        return "(" + expr + " as " + rt + ")"
    return expr


def _emit_binop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    right_node = node.get("right")
    left = _emit_expr(ctx, left_node)
    right = _emit_expr(ctx, right_node)
    op = _str(node, "op")
    resolved_type = _str(node, "resolved_type")
    left_type = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
    right_type = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""

    # Apply casts from EAST3 casts field
    casts = _list(node, "casts")
    for cast in casts:
        if not isinstance(cast, dict):
            continue
        on = _str(cast, "on")
        cast_to = _str(cast, "to")
        if on == "left" and cast_to != "":
            left = _apply_cast(left, cast_to)
        elif on == "right" and cast_to != "":
            right = _apply_cast(right, cast_to)

    # Map operators
    op_map: dict[str, str] = {
        "Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
        "FloorDiv": "/", "Mod": "%",
        "BitAnd": "&", "BitOr": "|", "BitXor": "^",
        "LShift": "<<", "RShift": ">>",
        "Pow": ".pow",
    }
    rs_op = op_map.get(op, op)
    if op == "FloorDiv":
        return "(" + left + " / " + right + ")"
    if op == "Pow":
        return "(" + left + ".pow(" + right + " as u32))"
    # String concatenation: String + &str in Rust
    if op == "Add" and (resolved_type == "str" or left_type == "str"):
        # Rust requires: String + &str  OR  &str + &str (via format!)
        # Use format! for safety
        return "format!(\"{}{}\", " + left + ", " + right + ")"
    return "(" + left + " " + rs_op + " " + right + ")"


def _emit_unaryop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    op_map: dict[str, str] = {
        "Not": "!", "USub": "-", "UAdd": "+", "Invert": "!",
    }
    rs_op = op_map.get(op, op)
    return "(" + rs_op + operand + ")"


def _emit_compare(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    left = _emit_expr(ctx, left_node)
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return left
    op_map: dict[str, str] = {
        "Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=",
        "Gt": ">", "GtE": ">=", "Is": "==", "IsNot": "!=",
    }
    parts: list[str] = []
    current_left = left
    current_left_node = left_node
    for idx, comparator in enumerate(comparators):
        op_obj = ops[idx] if idx < len(ops) else None
        op_name = op_obj if isinstance(op_obj, str) else _str(op_obj, "kind")
        right = _emit_expr(ctx, comparator)
        if op_name == "In":
            # Python `x in container` → py_in(&container, &x)
            c = right if right.startswith("&") else "&" + right
            k = current_left if current_left.startswith("&") else "&" + current_left
            parts.append("py_in(" + c + ", " + k + ")")
        elif op_name == "NotIn":
            c = right if right.startswith("&") else "&" + right
            k = current_left if current_left.startswith("&") else "&" + current_left
            parts.append("!py_in(" + c + ", " + k + ")")
        else:
            rs_op = op_map.get(op_name, op_name)
            # Comparing to None: if LHS is not Optional, the result is known statically
            left_type = _str(current_left_node, "resolved_type") if isinstance(current_left_node, dict) else ""
            right_type = _str(comparator, "resolved_type") if isinstance(comparator, dict) else ""
            is_none_cmp = (right == "None" or current_left == "None")
            if is_none_cmp:
                left_is_optional = ("|None" in left_type or "Optional[" in left_type or
                                    "| None" in left_type)
                right_is_optional = ("|None" in right_type or "Optional[" in right_type or
                                     "| None" in right_type)
                # Which side is the Option<T>?
                option_side = current_left if right == "None" else right
                if left_is_optional or right_is_optional:
                    # Use is_none()/is_some() for Option<T> comparisons to avoid type annotation issues
                    if rs_op == "==":
                        parts.append(option_side + ".is_none()")
                    else:
                        parts.append(option_side + ".is_some()")
                elif not left_is_optional and not right_is_optional and right == "None":
                    # Non-optional type compared to None: always not-None
                    parts.append("true" if rs_op == "!=" else "false")
                else:
                    parts.append("(" + current_left + " " + rs_op + " " + right + ")")
            else:
                parts.append("(" + current_left + " " + rs_op + " " + right + ")")
        current_left = right
        current_left_node = comparator
    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _emit_boolop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    op = _str(node, "op")
    resolved_type = _str(node, "resolved_type")

    # For bool type, use native &&/||
    if resolved_type == "bool" or resolved_type == "":
        rs_op = "&&" if op == "And" else "||"
        rendered = [_emit_expr(ctx, v) for v in values]
        return "(" + (" " + rs_op + " ").join(rendered) + ")"

    # For value-returning or/and (Python semantics), use py_bool() checks
    # x or y → if x.py_bool() { x.clone() } else { y.clone() }
    # x and y → if x.py_bool() { y.clone() } else { x.clone() }
    rendered = [_emit_expr(ctx, v) for v in values]
    if len(rendered) == 2:
        a = rendered[0]
        b = rendered[1]
        if op == "Or":
            return "{ let __bop_a = " + a + "; if (&__bop_a).py_bool() { __bop_a } else { " + b + " } }"
        else:
            return "{ let __bop_a = " + a + "; if !(&__bop_a).py_bool() { __bop_a } else { " + b + " } }"
    # Multi-value fallback: fold
    if op == "Or":
        rs_op = "||"
    else:
        rs_op = "&&"
    return "(" + (" " + rs_op + " ").join(rendered) + ")"


def _emit_attribute(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    obj_node = node.get("value")
    obj_type = _str(obj_node, "resolved_type") if isinstance(obj_node, dict) else ""
    obj_id = _str(obj_node, "id") if isinstance(obj_node, dict) else ""
    attr = _str(node, "attr")
    # Module attribute (e.g. math.pi) → use just the attr name (resolved to runtime)
    if obj_type == "module" or obj_id in ctx.import_alias_modules:
        runtime_symbol = _str(node, "runtime_symbol") or attr
        resolved = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping,
            resolved_runtime_call=_str(node, "resolved_runtime_call"),
            runtime_call=_str(node, "runtime_call"))
        return resolved if resolved != "" else safe_rs_ident(attr)
    # Class variable access: ClassName.field
    # (when obj has type_object_of set, meaning it's a class reference not instance)
    type_object_of = _str(obj_node, "type_object_of") if isinstance(obj_node, dict) else ""
    if type_object_of != "":
        # Inside a method of the same class accessing own class variable → self.field
        if ctx.current_class == type_object_of and attr in ctx.class_vars.get(type_object_of, {}):
            return "self." + safe_rs_ident(attr)
        # Enum/static access from outside → ClassName::MEMBER
        return safe_rs_ident(type_object_of) + "::" + safe_rs_ident(attr)
    obj = _emit_expr(ctx, obj_node)
    # If attr is a @property method, call it with ()
    # Check both the current class context and the obj's type class
    obj_class = obj_type if obj_type in ctx.class_names else ""
    if obj_class == "" and isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name":
        # Check if the object's variable type is a known class
        var_type = ctx.var_types.get(_str(obj_node, "id"), "")
        if var_type in ctx.class_names:
            obj_class = var_type
    for cls in (ctx.current_class, obj_class):
        if cls != "" and attr in ctx.class_property_methods.get(cls, set()):
            return obj + "." + safe_rs_ident(attr) + "()"
    return obj + "." + safe_rs_ident(attr)


def _emit_list_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    resolved_type = _str(node, "resolved_type")
    elem_type = ""
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        elem_type = rs_type(resolved_type[5:-1])
    rendered_elems = [_emit_expr(ctx, e) for e in elements]
    if len(rendered_elems) == 0:
        if elem_type != "":
            return "PyList::<" + elem_type + ">::new()"
        return "PyList::new()"
    elems_str = ", ".join(rendered_elems)
    if elem_type != "":
        return "PyList::<" + elem_type + ">::from_vec(vec![" + elems_str + "])"
    return "PyList::from_vec(vec![" + elems_str + "])"


def _emit_dict_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    keys = _list(node, "keys")
    values = _list(node, "values")
    resolved_type = _str(node, "resolved_type")
    k_type = "String"
    v_type = "Box<dyn std::any::Any>"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            k_type = rs_type(parts[0])
            v_type = rs_type(parts[1])
    if len(keys) == 0:
        return "HashMap::<" + k_type + ", " + v_type + ">::new()"
    pairs: list[str] = []
    for i, key in enumerate(keys):
        k = _emit_expr(ctx, key)
        v = _emit_expr(ctx, values[i]) if i < len(values) else "Default::default()"
        pairs.append("(" + k + ", " + v + ")")
    return "HashMap::<" + k_type + ", " + v_type + ">::from([" + ", ".join(pairs) + "])"


def _emit_set_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    resolved_type = _str(node, "resolved_type")
    elem_type = "String"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        elem_type = rs_type(resolved_type[4:-1])
    rendered_elems = [_emit_expr(ctx, e) for e in elements]
    if len(rendered_elems) == 0:
        return "HashSet::<" + elem_type + ">::new()"
    return "HashSet::<" + elem_type + ">::from([" + ", ".join(rendered_elems) + "])"


def _emit_tuple_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    rendered = [_emit_expr(ctx, e) for e in elements]
    if len(rendered) == 0:
        return "()"
    if len(rendered) == 1:
        return "(" + rendered[0] + ",)"
    return "(" + ", ".join(rendered) + ")"


def _emit_subscript(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    obj_node = node.get("value")
    obj = _emit_expr(ctx, obj_node)
    slice_node = node.get("slice")
    obj_type = _str(obj_node, "resolved_type") if isinstance(obj_node, dict) else ""

    # Handle Slice (a[b:c]) — range slicing
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        lo = _emit_expr(ctx, lower) if lower is not None else "0"
        hi_raw = _emit_expr(ctx, upper) if upper is not None else "usize::MAX"
        if obj_type.startswith("list["):
            elem_type = obj_type[5:-1]
            rs_elem = _rs_type_for_context(ctx, elem_type)
            return "PyList::<" + rs_elem + ">::from_vec({ let __borrow = " + obj + ".py_borrow(); let __lo = (" + lo + ") as usize; let __hi = ((" + hi_raw + ") as usize).min(__borrow.len()); __borrow[__lo..__hi].to_vec() })"
        if obj_type == "str":
            ref_obj = "&" + obj if not obj.startswith("&") else obj
            return "{ let __s = " + ref_obj + "; let __lo = (" + lo + ") as usize; let __hi = ((" + hi_raw + ") as usize).min(__s.len()); __s[__lo..__hi].to_string() }"
        # Default slice
        return obj + "[(" + lo + " as usize)..(" + hi_raw + " as usize)]"

    idx = _emit_expr(ctx, slice_node)
    # Tuple indexing with literal integer → rust tuple.N notation
    if obj_type.startswith("tuple["):
        if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Constant":
            val = slice_node.get("value")
            if isinstance(val, int) and val >= 0:
                return obj + "." + str(val)
        # Non-literal index into tuple: fallback to usize cast
        return obj + "[" + idx + " as usize]"
    if obj_type.startswith("list[") or obj_type == "list" or obj_type in ("bytes", "bytearray"):
        return obj + ".get(" + idx + ")"
    if obj_type.startswith("dict[") or obj_type == "dict":
        return obj + "[&" + idx + "]"
    # String indexing: s[i] → py_str_get_at(&s, i) returning String
    if obj_type == "str":
        ref_obj = "&" + obj if not obj.startswith("&") else obj
        node_rt = _str(node, "resolved_type")
        if node_rt == "byte" or node_rt == "int64":
            return "py_str_char_at(" + ref_obj + ", " + idx + ")"
        return "py_str_get_at(" + ref_obj + ", " + idx + ")"
    # Default: use indexing
    return obj + "[" + idx + " as usize]"


def _emit_bool_test(ctx: RsEmitContext, test_node: JsonVal) -> str:
    """Emit a test expression as a boolean condition (handles list/bytes truthiness)."""
    expr_str = _emit_expr(ctx, test_node)
    if isinstance(test_node, dict):
        rt = _str(test_node, "resolved_type")
        if rt in ("bytes", "bytearray") or rt.startswith("list[") or rt == "list":
            return "!" + expr_str + ".is_empty()"
    return expr_str


def _emit_ifexp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    test_node = node.get("test")
    test = _emit_bool_test(ctx, test_node)
    body_node = node.get("body")
    orelse_node = node.get("orelse")
    body = _emit_expr(ctx, body_node)
    orelse = _emit_expr(ctx, orelse_node)
    # Optional[T] if-else: wrap T branch with Some(...)
    rt = _str(node, "resolved_type")
    is_optional = rt.endswith(" | None") or rt.endswith("|None")
    if is_optional:
        def _is_none_node(n: JsonVal) -> bool:
            return isinstance(n, dict) and _str(n, "kind") == "Constant" and n.get("value") is None
        if _is_none_node(orelse_node) and not _is_none_node(body_node):
            body = "Some(" + body + ")"
        elif _is_none_node(body_node) and not _is_none_node(orelse_node):
            orelse = "Some(" + orelse + ")"
    # Union type (A | B, not Optional): box both branches
    elif "|" in rt:
        body = "Box::new(" + body + ") as Box<dyn std::any::Any>"
        orelse = "Box::new(" + orelse + ") as Box<dyn std::any::Any>"
    return "(if " + test + " { " + body + " } else { " + orelse + " })"


def _emit_lambda(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    arg_order = _list(node, "arg_order")
    arg_types = _dict(node, "arg_types")
    body = node.get("body")
    params: list[str] = []
    for arg in arg_order:
        if isinstance(arg, str):
            arg_type = _str(arg_types, arg)
            if arg_type != "":
                params.append(safe_rs_ident(arg) + ": " + _rs_type_for_context(ctx, arg_type))
            else:
                params.append(safe_rs_ident(arg))
    params_str = ", ".join(params)
    body_str = _emit_expr(ctx, body)
    return "|" + params_str + "| " + body_str


def _emit_box(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit a Box node (boxing a value for dynamic dispatch)."""
    inner = node.get("value")
    # If inner is a None constant, use annotated None to help Rust type inference
    if isinstance(inner, dict) and _str(inner, "kind") == "Constant" and inner.get("value") is None:
        return "None::<_>"
    rendered = _emit_expr(ctx, inner)
    return rendered


def _emit_call(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    func = node.get("func")
    args = _list(node, "args")
    keywords = _list(node, "keywords")

    # Check for runtime_call mapping
    runtime_call = _str(node, "runtime_call")
    adapter_kind = _str(node, "runtime_call_adapter_kind")
    builtin_name_field = _str(node, "builtin_name")

    # Determine if this is a method call (Attribute func)
    func_is_method = isinstance(func, dict) and _str(func, "kind") == "Attribute"

    if runtime_call != "":
        mapped = resolve_runtime_call(runtime_call, builtin_name_field, adapter_kind, ctx.mapping)
        if mapped != "" and not mapped.startswith("__"):
            # Handle special mappings
            if mapped == "__CAST__":
                if len(args) >= 1:
                    return _emit_expr(ctx, args[0])
                return ""
            # For method calls, delegate to _emit_method_call so the receiver is included
            if func_is_method:
                return _emit_method_call(ctx, func, args, keywords, node)
            return _emit_runtime_call(ctx, mapped, func, args, keywords, node)

    # Check for lowered_kind
    lowered_kind = _str(node, "lowered_kind")
    if lowered_kind == "BuiltinCall":
        builtin_name = _str(node, "builtin_name")
        runtime_sym = _str(node, "runtime_symbol")
        mapped2 = resolve_runtime_call(runtime_sym, builtin_name, adapter_kind, ctx.mapping)
        if mapped2 != "" and not mapped2.startswith("__"):
            return _emit_runtime_call(ctx, mapped2, func, args, keywords, node)
        # If mapped to a __ placeholder, fall through to Attribute/func handling below
        # (method calls like list.append are handled in _emit_method_call)
        if mapped2 == "" or mapped2.startswith("__"):
            pass  # fall through
        else:
            call_name = mapped2
            rendered_args = [_emit_expr(ctx, a) for a in args]
            for kw in keywords:
                if isinstance(kw, dict):
                    kw_val = kw.get("value")
                    rendered_args.append(_emit_expr(ctx, kw_val))
            return call_name + "(" + ", ".join(rendered_args) + ")"

    if not isinstance(func, dict):
        rendered_args = [_emit_expr(ctx, a) for a in args]
        return "unknown_func(" + ", ".join(rendered_args) + ")"

    func_kind = _str(func, "kind")

    # Method call: obj.method(args)
    if func_kind == "Attribute":
        return _emit_method_call(ctx, func, args, keywords, node)

    # Direct name call
    func_name = _str(func, "id")
    if func_name == "":
        func_expr = _emit_expr(ctx, func)
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        # Wrap func_expr in parens for IIFEs (lambda/closure expressions called immediately)
        return "(" + func_expr + ")(" + ", ".join(rendered_args) + ")"

    # Check for class constructor
    if func_name in ctx.class_names:
        return _emit_constructor_call(ctx, func_name, args, keywords, node)

    # deque() constructor → VecDeque::new()
    if func_name == "deque":
        rt = _str(node, "resolved_type") if isinstance(node, dict) else ""
        elem_type = "_"
        return "VecDeque::<" + elem_type + ">::new()"

    # bytes()/bytearray() constructor → PyList<i64> (bytes elements are accessed as ints)
    if func_name in ("bytes", "bytearray"):
        if len(args) == 1:
            arg0 = args[0]
            inner = _emit_expr(ctx, arg0)
            arg_type = _str(arg0, "resolved_type") if isinstance(arg0, dict) else ""
            if arg_type.startswith("list[") or arg_type in ("list", "bytes", "bytearray"):
                return inner  # already a PyList<i64>
            return inner
        return "PyList::<i64>::new()"

    # Check for runtime imports
    mapped3 = ctx.runtime_imports.get(func_name)
    if mapped3 is not None and mapped3 != "":
        return _emit_runtime_call(ctx, mapped3, func, args, keywords, node)

    # Regular call
    # Determine callable parameter types (for int→float coercion at call sites)
    func_resolved = _str(func, "resolved_type") if isinstance(func, dict) else ""
    callable_param_types: list[str] = []
    if (func_resolved.startswith("callable[") or func_resolved.startswith("Callable[")) and func_resolved.endswith("]"):
        from toolchain2.emit.rs.types import _parse_callable_signature
        callable_param_types, _ = _parse_callable_signature(func_resolved)

    rendered_args: list[str] = []
    for i, a in enumerate(args):
        rendered = _emit_call_arg(ctx, a)
        # Apply int→float coercion when callable expects float64 but arg is int with float body cast
        if (
            i < len(callable_param_types)
            and callable_param_types[i] in ("float64", "float32", "float")
            and isinstance(a, dict)
            and _str(a, "resolved_type") == "int64"
            and any(
                isinstance(c, dict) and _str(c, "on") == "body" and _str(c, "to") in ("float64", "float32", "float")
                for c in _list(a, "casts")
            )
        ):
            rendered = rendered + ".0_f64"
        rendered_args.append(rendered)
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            rendered_args.append(_emit_expr(ctx, kw_val))
    call_target = _rs_symbol_name(ctx, func_name)
    # Self-recursive call inside a nested closure — not supported; use zero value of return type
    if ctx.current_nested_fn != "" and call_target == ctx.current_nested_fn:
        from toolchain2.emit.rs.types import rs_zero_value
        return rs_zero_value(ctx.current_return_type if ctx.current_return_type else "int")
    return call_target + "(" + ", ".join(rendered_args) + ")"


def _emit_call_arg(ctx: RsEmitContext, arg: JsonVal) -> str:
    """Emit a call argument, handling Box nodes and trait coercion."""
    if isinstance(arg, dict) and _str(arg, "kind") == "Box":
        return _emit_box(ctx, arg)
    if isinstance(arg, dict):
        call_arg_type = _str(arg, "call_arg_type")
        resolved = _str(arg, "resolved_type")
        if call_arg_type in ctx.trait_names:
            # Coerce Box<UserClass> → &dyn Trait: use &* to dereference Box
            return "&*" + _emit_expr(ctx, arg)
        # Wrap plain closures in Box::new() when passing to Box<dyn Fn> parameters
        if (resolved.startswith("callable[") or resolved.startswith("Callable[")) and (call_arg_type.startswith("callable") or call_arg_type.startswith("Callable")):
            inner_expr = _emit_expr(ctx, arg)
            return "Box::new(" + inner_expr + ")"
        # Clone PyList<T>/bytes/bytearray when passed to functions (Rc-based, cheap clone)
        if resolved.startswith("list[") or resolved == "list" or resolved in ("bytes", "bytearray"):
            inner_expr = _emit_expr(ctx, arg)
            return inner_expr + ".clone()"
        # Clone Box<UserClass> when passed as readonly_ref (caller needs to use value after call)
        borrow_kind = _str(arg, "borrow_kind")
        if borrow_kind == "readonly_ref" and resolved in ctx.class_names:
            inner_expr = _emit_expr(ctx, arg)
            return inner_expr + ".clone()"
    return _emit_expr(ctx, arg)


def _emit_runtime_call(
    ctx: RsEmitContext,
    mapped: str,
    func: JsonVal,
    args: list[JsonVal],
    keywords: list[JsonVal],
    node: dict[str, JsonVal],
) -> str:
    rendered_args = [_emit_call_arg(ctx, a) for a in args]
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            rendered_args.append(_emit_expr(ctx, kw_val))

    # py_len takes &T — pass by reference, and return i64 (Python int)
    if mapped == "py_len" and len(rendered_args) == 1:
        arg = rendered_args[0]
        if not arg.startswith("&"):
            arg = "&" + arg
        return "py_len(" + arg + ") as i64"

    # py_int, py_float, py_str, py_str_to_i64 take &T
    if mapped in ("py_int", "py_float", "py_str", "py_str_to_i64", "py_str_to_f64", "py_str_isdigit", "py_str_isalpha", "py_str_isupper", "py_str_islower") and len(rendered_args) == 1:
        arg = rendered_args[0]
        if not arg.startswith("&"):
            arg = "&" + arg
        return mapped + "(" + arg + ")"

    # py_in takes (&C, &K)
    if mapped == "py_in" and len(rendered_args) == 2:
        c = rendered_args[0]
        k = rendered_args[1]
        if not c.startswith("&"):
            c = "&" + c
        if not k.startswith("&"):
            k = "&" + k
        return "py_in(" + c + ", " + k + ")"

    # py_print with a todo!() arg: emit todo! directly (avoids never-type inference issues)
    if mapped == "py_print" and len(rendered_args) >= 1 and all(a.startswith("todo!(") for a in rendered_args):
        return rendered_args[0]

    # py_print with multiple args: join with space
    if mapped == "py_print" and len(rendered_args) > 1:
        fmt_parts = " ".join(["{}" for _ in rendered_args])
        # Wrap each arg in parens to avoid precedence issues (e.g. `x as i64.py_stringify()`)
        stringify_args = ", ".join("(" + a + ").py_stringify()" for a in rendered_args)
        return 'py_print(format!("' + fmt_parts + '", ' + stringify_args + "))"

    # py_assert_eq(opt, None, label) or py_assert_eq(None, opt, label) → py_assert_true(opt.is_none(), label)
    if mapped == "py_assert_eq" and len(args) >= 2:
        def _is_none_arg(a: JsonVal) -> bool:
            if not isinstance(a, dict):
                return False
            inner = a.get("value") if _str(a, "kind") == "Box" else a
            return isinstance(inner, dict) and _str(inner, "kind") == "Constant" and inner.get("value") is None
        def _is_optional_arg(a: JsonVal) -> bool:
            if not isinstance(a, dict):
                return False
            inner = a.get("value") if _str(a, "kind") == "Box" else a
            if not isinstance(inner, dict):
                return False
            rt = _str(inner, "resolved_type")
            return "|None" in rt or "| None" in rt
        if _is_none_arg(args[0]) and len(args) >= 3:
            opt_expr = rendered_args[1]
            label_expr = rendered_args[2]
            return "py_assert_true(" + opt_expr + ".is_none(), " + label_expr + ")"
        if _is_none_arg(args[1]) and _is_optional_arg(args[0]) and len(args) >= 3:
            opt_expr = rendered_args[0]
            label_expr = rendered_args[2]
            return "py_assert_true(" + opt_expr + ".is_none(), " + label_expr + ")"

    # py_set() with no args → empty HashSet
    if mapped == "py_set" and len(rendered_args) == 0:
        rt = _str(node, "resolved_type") if isinstance(node, dict) else ""
        elem_type = "i64"
        if rt.startswith("set["):
            inner = rt[4:-1]
            elem_type = _rs_type_for_context(ctx, inner)
        return "HashSet::<" + elem_type + ">::new()"

    return mapped + "(" + ", ".join(rendered_args) + ")"


def _emit_method_call(
    ctx: RsEmitContext,
    attr_node: dict[str, JsonVal],
    args: list[JsonVal],
    keywords: list[JsonVal],
    call_node: dict[str, JsonVal],
) -> str:
    obj = attr_node.get("value")
    method = _str(attr_node, "attr")
    obj_type = _str(obj, "resolved_type") if isinstance(obj, dict) else ""
    obj_id = _str(obj, "id") if isinstance(obj, dict) else ""

    # Static method call: ClassName.method(args) → ClassName::method(args)
    type_object_of = _str(obj, "type_object_of") if isinstance(obj, dict) else ""
    if type_object_of != "" and obj_type == "type":
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        for kw in keywords:
            if isinstance(kw, dict):
                rendered_args.append(_emit_expr(ctx, kw.get("value")))
        return safe_rs_ident(type_object_of) + "::" + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"

    # Module-qualified call: math.sqrt(x) → sqrt(x) or mapped runtime name
    if obj_type == "module" or obj_id in ctx.import_alias_modules:
        # Try runtime_call or runtime_symbol from call_node / attr_node
        runtime_call_cn = _str(call_node, "runtime_call")
        runtime_symbol_cn = _str(call_node, "runtime_symbol")
        runtime_symbol_an = _str(attr_node, "runtime_symbol")
        runtime_symbol = runtime_symbol_cn or runtime_symbol_an or method
        adapter_kind = _str(call_node, "runtime_call_adapter_kind")
        builtin_name = _str(call_node, "builtin_name")
        # Resolve via mapping
        resolved_name = ""
        if runtime_call_cn != "":
            resolved_name = resolve_runtime_call(runtime_call_cn, builtin_name, adapter_kind, ctx.mapping)
        if resolved_name == "" and runtime_symbol != "":
            resolved_name = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping,
                resolved_runtime_call=_str(call_node, "resolved_runtime_call"),
                runtime_call=runtime_call_cn)
        if resolved_name == "":
            resolved_name = safe_rs_ident(method)
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        for kw in keywords:
            if isinstance(kw, dict):
                kw_val = kw.get("value")
                rendered_args.append(_emit_expr(ctx, kw_val))
        return resolved_name + "(" + ", ".join(rendered_args) + ")"

    # Check runtime_call for method call
    # Skip runtime_call resolution for typed collection methods — handled below by type dispatch
    _typed_collection_obj = (
        obj_type.startswith("set[") or obj_type == "set"
        or obj_type.startswith("list[") or obj_type == "list"
        or obj_type.startswith("dict[") or obj_type == "dict"
        or obj_type == "deque"
    )
    runtime_call = _str(call_node, "runtime_call")
    call_adapter_kind = _str(call_node, "runtime_call_adapter_kind")
    call_builtin = _str(call_node, "builtin_name")
    if runtime_call != "" and not _typed_collection_obj:
        mapped = resolve_runtime_call(runtime_call, call_builtin, call_adapter_kind, ctx.mapping)
        if mapped != "" and not mapped.startswith("__"):
            obj_str = _emit_expr(ctx, obj)
            rendered_args = [_emit_call_arg(ctx, a) for a in args]
            for kw in keywords:
                if isinstance(kw, dict):
                    kw_val = kw.get("value")
                    rendered_args.append(_emit_expr(ctx, kw_val))
            # For str.* functions: receiver and all args need & (Rust &str)
            if runtime_call.startswith("str."):
                if not obj_str.startswith("&"):
                    obj_str = "&" + obj_str
                rendered_args = [
                    a if a.startswith("&") else "&" + a
                    for a in rendered_args
                ]
            all_args = [obj_str] + rendered_args
            return mapped + "(" + ", ".join(all_args) + ")"

    obj_str = _emit_expr(ctx, obj)
    rendered_args = [_emit_expr(ctx, a) for a in args]
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            rendered_args.append(_emit_expr(ctx, kw_val))

    # PyList methods (list, bytes, bytearray all use PyList<T>)
    if obj_type.startswith("list[") or obj_type == "list" or obj_type in ("bytes", "bytearray"):
        if method == "append":
            return obj_str + ".push(" + ", ".join(rendered_args) + ")"
        if method == "pop":
            if len(rendered_args) == 0:
                return obj_str + ".pop().unwrap_or_default()"
            return "{ let __pop_idx = " + rendered_args[0] + "; let __v = " + obj_str + ".get(__pop_idx); " + obj_str + ".py_borrow_mut().remove(__pop_idx as usize); __v }"
        if method == "clear":
            return "{ " + obj_str + ".py_borrow_mut().clear(); }"
        if method == "extend":
            return obj_str + ".py_borrow_mut().extend(" + ", ".join(rendered_args) + ")"
        if method == "insert":
            if len(rendered_args) >= 2:
                return obj_str + ".py_borrow_mut().insert(" + rendered_args[0] + " as usize, " + rendered_args[1] + ")"
        if method == "remove":
            return "{ let __remove_val = " + rendered_args[0] + "; let mut __v = " + obj_str + ".py_borrow_mut(); if let Some(pos) = __v.iter().position(|x| *x == __remove_val) { __v.remove(pos); } }"
        if method == "index":
            return obj_str + ".py_borrow().iter().position(|x| *x == " + rendered_args[0] + ").unwrap_or(usize::MAX) as i64"
        if method == "count":
            return obj_str + ".py_borrow().iter().filter(|x| **x == " + rendered_args[0] + ").count() as i64"
        if method == "sort":
            return "{ " + obj_str + ".py_borrow_mut().sort(); }"
        if method == "reverse":
            return "{ " + obj_str + ".py_borrow_mut().reverse(); }"
        if method == "copy":
            return obj_str + ".clone()"

    # str methods (on &str or String)
    if obj_type == "str":
        if method == "format":
            # Basic: emit format!(...) - simplified
            return "format!(\"...\", " + ", ".join(rendered_args) + ")"
        if method in ("upper", "lower", "strip", "lstrip", "rstrip",
                      "startswith", "endswith", "replace", "split", "find",
                      "rfind", "join", "count", "index", "isdigit", "isalpha",
                      "isalnum", "isspace"):
            mapped_fn = "py_str_" + method
            all_args = ["&" + obj_str] + ["&" + a if i > 0 else a for i, a in enumerate(rendered_args)]
            return mapped_fn + "(" + ", ".join(["&" + obj_str] + rendered_args) + ")"

    # dict methods
    if obj_type.startswith("dict[") or obj_type == "dict":
        if method == "get":
            if len(rendered_args) >= 2:
                return obj_str + ".get(&" + rendered_args[0] + ").cloned().unwrap_or(" + rendered_args[1] + ")"
            elif len(rendered_args) == 1:
                return obj_str + ".get(&" + rendered_args[0] + ").cloned()"
        if method == "keys":
            return "PyList::from_vec(" + obj_str + ".keys().cloned().collect())"
        if method == "values":
            return "PyList::from_vec(" + obj_str + ".values().cloned().collect())"
        if method == "items":
            return "PyList::from_vec(" + obj_str + ".iter().map(|(k, v)| (k.clone(), v.clone())).collect())"
        if method in ("pop", "remove"):
            if len(rendered_args) >= 1:
                return obj_str + ".remove(&" + rendered_args[0] + ").unwrap_or_default()"
        if method == "update":
            return "{ for (k, v) in " + rendered_args[0] + ".iter() { " + obj_str + ".insert(k.clone(), v.clone()); } }"
        if method == "clear":
            return "{ " + obj_str + ".clear(); }"

    # set methods
    if obj_type.startswith("set[") or obj_type == "set":
        if method == "add":
            return obj_str + ".insert(" + ", ".join(rendered_args) + ")"
        if method == "remove" or method == "discard":
            return obj_str + ".remove(&" + rendered_args[0] + ")"
        if method == "clear":
            return obj_str + ".clear()"
        if method == "union":
            return obj_str + ".union(&" + rendered_args[0] + ").cloned().collect::<HashSet<_>>()"
        if method == "intersection":
            return obj_str + ".intersection(&" + rendered_args[0] + ").cloned().collect::<HashSet<_>>()"

    # deque methods (VecDeque)
    if obj_type == "deque":
        if method == "append":
            return obj_str + ".push_back(" + ", ".join(rendered_args) + ")"
        if method == "appendleft":
            return obj_str + ".push_front(" + ", ".join(rendered_args) + ")"
        if method == "popleft":
            return obj_str + ".pop_front().unwrap_or_default()"
        if method == "pop":
            return obj_str + ".pop_back().unwrap_or_default()"
        if method == "clear":
            return obj_str + ".clear()"

    # Generic method call
    all_args_str = ", ".join(rendered_args)
    return obj_str + "." + safe_rs_ident(method) + "(" + all_args_str + ")"


def _emit_constructor_call(
    ctx: RsEmitContext,
    class_name: str,
    args: list[JsonVal],
    keywords: list[JsonVal],
    node: dict[str, JsonVal],
) -> str:
    rendered_args = [_emit_expr(ctx, a) for a in args]
    # Handle keyword args: insert at correct position
    kw_map: dict[str, str] = {}
    for kw in keywords:
        if isinstance(kw, dict):
            kw_arg = _str(kw, "arg")
            kw_val = kw.get("value")
            if kw_arg != "":
                kw_map[kw_arg] = _emit_expr(ctx, kw_val)
            else:
                rendered_args.append(_emit_expr(ctx, kw_val))
    rs_name = safe_rs_ident(class_name)
    # Fill in missing args from __init__ param list (not all fields)
    # Only fill args for params that __init__ actually accepts (excluding self)
    init_method = ctx.class_instance_methods.get(class_name, {}).get("__init__")
    if init_method is not None:
        init_arg_order = [a for a in _list(init_method, "arg_order") if isinstance(a, str) and a != "self"]
        init_arg_types = _dict(init_method, "arg_types")
        init_arg_defaults = _dict(init_method, "arg_defaults")
        fields = ctx.class_fields.get(class_name, {})
        defaults = ctx.class_field_defaults.get(class_name, {})
        if len(init_arg_order) > 0:
            full_args: list[str] = list(rendered_args)
            for i, arg_name in enumerate(init_arg_order):
                if i < len(full_args):
                    continue
                if arg_name in kw_map:
                    full_args.append(kw_map[arg_name])
                else:
                    # Check __init__ arg_defaults first
                    ad = init_arg_defaults.get(arg_name)
                    if isinstance(ad, dict):
                        full_args.append(_emit_expr(ctx, ad))
                    else:
                        # Fall back to field default
                        default_val = defaults.get(arg_name)
                        if default_val is not None:
                            full_args.append(default_val)
                        else:
                            arg_type = _str(init_arg_types, arg_name)
                            full_args.append(rs_zero_value(arg_type) if arg_type else "Default::default()")
            rendered_args = full_args
        # If __init__ takes no params, rendered_args stays empty
    else:
        # No __init__ (dataclass-style): use fields and defaults to fill positional args
        fields = ctx.class_fields.get(class_name, {})
        defaults = ctx.class_field_defaults.get(class_name, {})
        field_list = list(fields.keys())
        if len(field_list) > 0:
            full_args2: list[str] = list(rendered_args)
            for i, field_name in enumerate(field_list):
                if i < len(full_args2):
                    continue
                if field_name in kw_map:
                    full_args2.append(kw_map[field_name])
                else:
                    default_val = defaults.get(field_name)
                    if default_val is not None:
                        full_args2.append(default_val)
                    else:
                        full_args2.append(rs_zero_value(fields[field_name]))
            rendered_args = full_args2
    return "Box::new(" + rs_name + "::new(" + ", ".join(rendered_args) + "))"


def _emit_expr_with_body_casts(ctx: RsEmitContext, node: JsonVal, result: str) -> str:
    """Apply 'on: body' casts from EAST3 node to the emitted expression."""
    if not isinstance(node, dict):
        return result
    casts = _list(node, "casts")
    for cast in casts:
        if not isinstance(cast, dict):
            continue
        on = _str(cast, "on")
        cast_to = _str(cast, "to")
        if on == "body" and cast_to != "":
            result = _apply_cast(result, cast_to)
    return result


def _emit_expr(ctx: RsEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return "_"
    kind = _str(node, "kind")
    if kind == "Constant":
        return _emit_constant(ctx, node)
    if kind == "Name":
        return _emit_name(ctx, node)
    if kind == "BinOp":
        return _emit_binop(ctx, node)
    if kind == "UnaryOp":
        return _emit_unaryop(ctx, node)
    if kind == "Compare":
        return _emit_compare(ctx, node)
    if kind == "BoolOp":
        return _emit_boolop(ctx, node)
    if kind == "Attribute":
        return _emit_attribute(ctx, node)
    if kind == "Call":
        return _emit_call(ctx, node)
    if kind == "List":
        return _emit_list_literal(ctx, node)
    if kind == "Dict":
        return _emit_dict_literal(ctx, node)
    if kind == "Set":
        return _emit_set_literal(ctx, node)
    if kind == "Tuple":
        return _emit_tuple_literal(ctx, node)
    if kind == "Subscript":
        return _emit_subscript(ctx, node)
    if kind == "IfExp":
        return _emit_ifexp(ctx, node)
    if kind == "Lambda":
        return _emit_lambda(ctx, node)
    if kind == "Box":
        return _emit_box(ctx, node)
    if kind == "JoinedStr":
        return _emit_fstring(ctx, node)
    if kind == "ObjTypeId":
        # Get runtime type ID of an object
        val = node.get("value")
        inner = _emit_expr(ctx, val)
        ref_inner = "&" + inner if not inner.startswith("&") else inner
        return "py_runtime_type_id(" + ref_inner + ")"
    if kind == "Unbox":
        # Unbox: wraps an expression promoting it to Optional/nullable; passthrough inner value
        inner_node = node.get("value")
        return _emit_expr(ctx, inner_node)
    # Fallback: use repr if available (emit todo! so it compiles but panics at runtime)
    # Escape { and } since todo! uses them as format specifiers
    repr_str = _str(node, "repr")
    if repr_str != "":
        safe_repr = repr_str.replace('"', "'").replace("{", "{{").replace("}", "}}")
        return "todo!(\"unsupported: " + safe_repr + "\")"
    return "todo!(\"unsupported_expr:" + kind + "\")"


def _emit_fstring(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit f-string as format!()."""
    values = _list(node, "values")
    fmt_parts: list[str] = []
    fmt_args: list[str] = []
    for v in values:
        if isinstance(v, dict):
            v_kind = _str(v, "kind")
            if v_kind == "Constant":
                s = v.get("value")
                if isinstance(s, str):
                    fmt_parts.append(s.replace("{", "{{").replace("}", "}}"))
            elif v_kind == "FormattedValue":
                fmt_parts.append("{}")
                inner = v.get("value")
                fmt_args.append(_emit_expr(ctx, inner))
            else:
                fmt_parts.append("{}")
                fmt_args.append(_emit_expr(ctx, v))
    fmt_str = "".join(fmt_parts)
    if len(fmt_args) == 0:
        return '"' + fmt_str + '".to_string()'
    return 'format!("' + fmt_str + '", ' + ", ".join(fmt_args) + ")"


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_expr_stmt(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    # Skip bare string literal statements (module/class docstrings)
    if isinstance(value, dict) and _str(value, "kind") == "Constant":
        v = value.get("value")
        if isinstance(v, str):
            _emit(ctx, "// " + v.replace("\n", " ").replace("\"", "'")[:120])
            return
    # Handle `continue` and `break` used as expressions (Python control flow)
    if isinstance(value, dict) and _str(value, "kind") == "Name":
        vid = _str(value, "id")
        if vid == "continue":
            _emit(ctx, "continue;")
            return
        if vid == "break":
            _emit(ctx, "break;")
            return
    rendered = _emit_expr(ctx, value)
    # Skip no-op renders (e.g. pure comment placeholders)
    if rendered.strip() == "" or rendered == "()":
        return
    _emit(ctx, rendered + ";")


def _emit_return(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if value is None:
        _emit(ctx, "return;")
        return
    rendered = _emit_expr(ctx, value)
    # Wrap in Some() if returning a non-None value into an Optional return type
    if ctx.current_return_type != "":
        ret_rs = _rs_type_for_context(ctx, ctx.current_return_type)
        if ret_rs.startswith("Option<") and rendered != "None":
            val_rs_type = _str(value, "resolved_type") if isinstance(value, dict) else ""
            val_is_none = (val_rs_type in ("None", "none") or rendered == "None")
            if not val_is_none:
                rendered = "Some(" + rendered + ")"
    _emit(ctx, "return " + rendered + ";")


def _emit_ann_assign(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    resolved_type = _str(node, "resolved_type")
    # Fall back to decl_type if resolved_type is empty
    if resolved_type == "":
        resolved_type = _str(node, "decl_type")

    if isinstance(target, dict):
        target_kind = _str(target, "kind")

        if target_kind == "Attribute":
            # self.field = value
            lhs = _emit_attribute(ctx, target)
            if value is not None:
                rhs = _emit_expr(ctx, value)
                _emit(ctx, lhs + " = " + rhs + ";")
            return

        target_name = _str(target, "id")
        if target_name == "":
            return

        rs_name = _rs_var_name(ctx, target_name)
        annotation = _str(node, "annotation")
        rt = _rs_type_for_context(ctx, resolved_type) if resolved_type != "" else ""

        if target_name in ctx.declared_vars:
            # Reassignment
            if value is not None:
                rhs = _emit_expr(ctx, value)
                _emit(ctx, rs_name + " = " + rhs + ";")
        else:
            # New declaration
            ctx.declared_vars.add(target_name)
            ctx.var_types[target_name] = resolved_type
            # Module-level vars: emit as const or static (can't use `let` at module level)
            if ctx.at_module_level:
                rs_upper = rs_name.upper()
                val_is_const = isinstance(value, dict) and value.get("kind") == "Constant"
                if value is not None:
                    rhs = _emit_expr(ctx, value)
                    t = rt if rt != "" and rt != "()" else "i64"
                    if val_is_const:
                        # Simple constant: use `const`
                        _emit(ctx, "const " + rs_upper + ": " + t + " = " + rhs + ";")
                    elif t.startswith("Box<") or t.startswith("PyList") or t.startswith("HashMap") or t.startswith("Vec<"):
                        # Complex types can't be zero-initialized as statics - skip
                        _emit(ctx, "// static " + rs_upper + ": " + t + " = " + rhs + "; // (non-const skip)")
                    else:
                        _emit(ctx, "static mut " + rs_upper + ": " + t + " = 0; // init: " + rhs)
                else:
                    t = rt if rt != "" and rt != "()" else "i64"
                    _emit(ctx, "static mut " + rs_upper + ": " + t + " = 0;")
                # Register the static name for later name resolution
                ctx.module_statics[target_name] = rs_upper
                return
            if value is not None:
                rhs = _emit_expr(ctx, value)
                # When declared as byte (uint8) but subscript returns String, use char_at
                if annotation in ("uint8", "byte") and isinstance(value, dict) and value.get("kind") == "Subscript":
                    sub_obj = value.get("value")
                    sub_obj_type = _str(sub_obj, "resolved_type") if isinstance(sub_obj, dict) else ""
                    if sub_obj_type == "str":
                        obj_str = _emit_expr(ctx, sub_obj)
                        if not obj_str.startswith("&"):
                            obj_str = "&" + obj_str
                        idx_str = _emit_expr(ctx, value.get("slice"))
                        rhs = "py_str_char_at(" + obj_str + ", " + idx_str + ")"
                        rt = "i64"
                # Cast rhs to small/narrow numeric types (py_int returns i64, py_float returns f64)
                _NARROW_RS = {"i8", "i16", "i32", "u8", "u16", "u32", "u64", "f32"}
                _WIDE_RS = _NARROW_RS | {"i64", "f64"}
                if rt in _NARROW_RS and isinstance(value, dict):
                    val_rt = _str(value, "resolved_type")
                    val_rs = rs_type(val_rt) if val_rt != "" else ""
                    if val_rs in _WIDE_RS:
                        rhs = rhs + " as " + rt
                # Inheritance: declared type is Box<Parent> but value is Subclass — use value type
                if rt.startswith("Box<") and isinstance(value, dict):
                    val_rt2 = _str(value, "resolved_type")
                    if val_rt2 != resolved_type and val_rt2 in ctx.class_names and val_rt2 not in ctx.enum_bases:
                        rt = _rs_type_for_context(ctx, val_rt2)
                        ctx.var_types[target_name] = val_rt2
                # `_` is the wildcard pattern - Rust doesn't allow `mut _`
                if rs_name == "_":
                    _emit(ctx, "let _ = " + rhs + ";")
                elif rt != "" and rt != "()":
                    _emit(ctx, "let mut " + rs_name + ": " + rt + " = " + rhs + ";")
                else:
                    _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")
            else:
                if rs_name == "_":
                    return  # discard with no value: nothing to emit
                if rt != "" and rt != "()":
                    zero = rs_zero_value(resolved_type)
                    _emit(ctx, "let mut " + rs_name + ": " + rt + " = " + zero + ";")
                else:
                    _emit(ctx, "let mut " + rs_name + ";")


def _emit_assign(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")

    if isinstance(target, dict):
        target_kind = _str(target, "kind")

        if target_kind == "Attribute":
            lhs = _emit_attribute(ctx, target)
            rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
            _emit(ctx, lhs + " = " + rhs + ";")
            return

        if target_kind == "Subscript":
            obj = _emit_expr(ctx, target.get("value"))
            slice_node = target.get("slice")
            obj_type = _str(target.get("value"), "resolved_type") if isinstance(target.get("value"), dict) else ""
            idx = _emit_expr(ctx, slice_node)
            rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
            if obj_type.startswith("list[") or obj_type == "list" or obj_type in ("bytes", "bytearray"):
                _emit(ctx, obj + ".set(" + idx + ", " + rhs + ");")
            elif obj_type.startswith("dict[") or obj_type == "dict":
                _emit(ctx, obj + ".insert(" + idx + ", " + rhs + ");")
            else:
                _emit(ctx, obj + "[" + idx + " as usize] = " + rhs + ";")
            return

        if target_kind == "Tuple" or target_kind == "List":
            # Tuple unpacking
            elements = _list(target, "elements")
            if value is not None and len(elements) > 0:
                temp = _next_temp(ctx, "unpack")
                rhs = _emit_expr(ctx, value)
                _emit(ctx, "let " + temp + " = " + rhs + ";")
                for idx, elem in enumerate(elements):
                    if isinstance(elem, dict):
                        elem_name = _str(elem, "id")
                        if elem_name != "" and elem_name != "_":
                            rs_elem = _rs_var_name(ctx, elem_name)
                            if elem_name in ctx.declared_vars:
                                _emit(ctx, rs_elem + " = " + temp + "." + str(idx) + ";")
                            else:
                                ctx.declared_vars.add(elem_name)
                                _emit(ctx, "let mut " + rs_elem + " = " + temp + "." + str(idx) + ";")
            return

        target_name = _str(target, "id")
        if target_name == "":
            return

        rs_name = _rs_var_name(ctx, target_name)
        rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
        # PyList is Rc-wrapped — assignment needs .clone() to share reference (not move)
        # User class Box<T> also needs .clone() to avoid move
        if isinstance(value, dict) and value.get("kind") == "Name":
            val_type = _str(value, "resolved_type")
            if val_type.startswith("list[") or val_type == "list":
                rhs = rhs + ".clone()"
            elif val_type in ctx.class_names:
                rhs = rhs + ".clone()"

        if target_name in ctx.declared_vars:
            _emit(ctx, rs_name + " = " + rhs + ";")
        else:
            ctx.declared_vars.add(target_name)
            resolved_type = _str(value, "resolved_type") if isinstance(value, dict) else ""
            if resolved_type != "":
                ctx.var_types[target_name] = resolved_type
            # Module-level assignment: use const/static
            if ctx.at_module_level:
                rs_upper = rs_name.upper()
                val_is_const = isinstance(value, dict) and value.get("kind") == "Constant"
                rt = _rs_type_for_context(ctx, resolved_type) if resolved_type not in ("", "unknown") else "i64"
                if val_is_const:
                    _emit(ctx, "const " + rs_upper + ": " + rt + " = " + rhs + ";")
                elif rt.startswith("Box<") or rt.startswith("PyList") or rt.startswith("HashMap") or rt.startswith("Vec<"):
                    _emit(ctx, "// static " + rs_upper + ": " + rt + " = " + rhs + "; // (non-const skip)")
                else:
                    _emit(ctx, "static mut " + rs_upper + ": " + rt + " = 0; // init: " + rhs)
                ctx.module_statics[target_name] = rs_upper
            else:
                if rs_name == "_":
                    _emit(ctx, "let _ = " + rhs + ";")
                else:
                    _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")

    elif isinstance(target, str):
        rs_name = _rs_var_name(ctx, target)
        rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
        if target in ctx.declared_vars:
            _emit(ctx, rs_name + " = " + rhs + ";")
        else:
            ctx.declared_vars.add(target)
            if rs_name == "_":
                _emit(ctx, "let _ = " + rhs + ";")
            else:
                _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")


def _emit_aug_assign(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    op = _str(node, "op")
    aug_ops: dict[str, str] = {
        "Add": "+=", "Sub": "-=", "Mult": "*=", "Div": "/=",
        "FloorDiv": "/=", "Mod": "%=",
        "BitAnd": "&=", "BitOr": "|=", "BitXor": "^=",
        "LShift": "<<=", "RShift": ">>=",
    }
    rs_op = aug_ops.get(op, "+=")
    lhs = _emit_expr(ctx, target)
    rhs = _emit_expr(ctx, value) if value is not None else "0"
    # String += &str in Rust (String += String is invalid)
    if op == "Add":
        target_type = _str(target, "resolved_type") if isinstance(target, dict) else ""
        if target_type == "str" and not rhs.startswith("&"):
            rhs = "&" + rhs
    _emit(ctx, lhs + " " + rs_op + " " + rhs + ";")


def _emit_raise(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    exc = node.get("exc")
    if exc is None:
        _emit(ctx, 'panic!("re-raised");')
        return
    if isinstance(exc, dict):
        exc_kind = _str(exc, "kind")
        if exc_kind == "Call":
            args = _list(exc, "args")
            if len(args) > 0:
                msg = _emit_expr(ctx, args[0])
                _emit(ctx, "panic!(\"{}\", " + msg + ");")
                return
        msg = _emit_expr(ctx, exc)
        _emit(ctx, "panic!(\"{}\", " + msg + ");")
        return
    _emit(ctx, 'panic!("exception");')


def _emit_try(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    # Rust doesn't have try/except in the same way.
    # For now, emit the body with a comment about exception handling.
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")
    orelse = _list(node, "orelse")

    if len(handlers) == 0 and len(finalbody) > 0:
        # Just finally - use a drop guard pattern (simplified: just emit)
        _emit_body(ctx, body)
        _emit_body(ctx, finalbody)
        return

    # Simplified: emit body only (proper panic/unwind handling would require std::panic::catch_unwind)
    _emit(ctx, "// try block (Rust: panic on exception)")
    _emit_body(ctx, body)

    if len(handlers) > 0:
        _emit(ctx, "// except handlers (simplified - not fully translated)")
        for handler in handlers:
            if isinstance(handler, dict):
                # Declare the exception variable as placeholder so body compiles
                exc_name = _str(handler, "name")
                if exc_name != "":
                    _emit(ctx, "let " + safe_rs_ident(exc_name) + " = \"exception\".to_string();")
                    ctx.declared_vars.add(exc_name)
                handler_body = _list(handler, "body")
                _emit_body(ctx, handler_body)

    if len(finalbody) > 0:
        _emit(ctx, "// finally block")
        _emit_body(ctx, finalbody)


def _emit_for_core(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit ForCore statement (EAST3 for-loop)."""
    body = _list(node, "body")

    # Check for iter_plan (EAST3 lowered loop plan)
    iter_plan = node.get("iter_plan")
    target_plan = node.get("target_plan")

    if isinstance(iter_plan, dict):
        plan_kind = _str(iter_plan, "kind")
        if plan_kind == "StaticRangeForPlan":
            _emit_static_range_for_from_plan(ctx, iter_plan, target_plan, body)
            return
        if plan_kind == "RuntimeIterForPlan":
            _emit_runtime_iter_for_from_plan(ctx, iter_plan, target_plan, body)
            return

    # Fallback: use target/iter fields
    target = node.get("target")
    iter_node = node.get("iter")

    target_str = _emit_loop_target(ctx, target, target_plan)
    iter_str = _emit_for_iter(ctx, iter_node, target)

    _emit_loop_var_declared(ctx, target, target_plan)
    # Infer element type from iterator's resolved_type for nested loop dispatch
    if isinstance(iter_node, dict):
        iter_rt = _str(iter_node, "resolved_type")
        target_id = _str(target, "id") if isinstance(target, dict) else ""
        if target_id == "" and isinstance(target_plan, dict):
            target_id = _str(target_plan, "id")
        if target_id != "" and iter_rt.startswith("list["):
            ctx.var_types[target_id] = iter_rt[5:-1]
    _emit(ctx, "for " + target_str + " in " + iter_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_loop_target(ctx: RsEmitContext, target: JsonVal, target_plan: JsonVal) -> str:
    """Get Rust loop variable expression."""
    if isinstance(target_plan, dict):
        plan_kind = _str(target_plan, "kind")
        if plan_kind == "NameTarget":
            return _rs_var_name(ctx, _str(target_plan, "id"))
        if plan_kind == "TupleTarget":
            elements = _list(target_plan, "elements")
            parts = [_rs_var_name(ctx, _str(e, "id")) if isinstance(e, dict) else "_" for e in elements]
            return "(" + ", ".join(parts) + ")"
    if isinstance(target, dict):
        target_kind = _str(target, "kind")
        if target_kind == "Name":
            return _rs_var_name(ctx, _str(target, "id"))
        elif target_kind == "Tuple":
            elements = _list(target, "elements")
            parts = [_rs_var_name(ctx, _str(e, "id")) if isinstance(e, dict) else "_" for e in elements]
            return "(" + ", ".join(parts) + ")"
    if isinstance(target, str):
        return _rs_var_name(ctx, target)
    return "_item"


def _emit_loop_var_declared(ctx: RsEmitContext, target: JsonVal, target_plan: JsonVal) -> None:
    """Mark loop variable as declared."""
    if isinstance(target_plan, dict) and _str(target_plan, "kind") == "NameTarget":
        ctx.declared_vars.add(_str(target_plan, "id"))
        return
    if isinstance(target, dict) and _str(target, "kind") == "Name":
        ctx.declared_vars.add(_str(target, "id"))


def _emit_static_range_for_from_plan(
    ctx: RsEmitContext,
    plan: dict[str, JsonVal],
    target_plan: JsonVal,
    body: list[JsonVal],
) -> None:
    """Emit StaticRangeForPlan from iter_plan."""
    start = plan.get("start")
    stop = plan.get("stop")
    step = plan.get("step")

    target_str = "_i"
    target_type = "i64"
    if isinstance(target_plan, dict):
        target_str = _rs_var_name(ctx, _str(target_plan, "id"))
        tp = _str(target_plan, "target_type")
        if tp != "":
            target_type = rs_type(tp)
    ctx.declared_vars.add(target_str)

    start_str = _emit_expr(ctx, start) if start is not None else "0_i64"
    stop_str = _emit_expr(ctx, stop) if stop is not None else "0_i64"

    # Determine step value
    step_val = 1
    step_is_const = False
    if isinstance(step, dict) and _str(step, "kind") == "Constant":
        sv = step.get("value")
        if isinstance(sv, int):
            step_val = sv
            step_is_const = True
    elif isinstance(step, int):
        step_val = step
        step_is_const = True

    if step_is_const:
        if step_val == 1:
            _emit(ctx, "for " + target_str + " in " + start_str + ".." + stop_str + " {")
        elif step_val == -1:
            _emit(ctx, "for " + target_str + " in (" + stop_str + ".." + start_str + ").rev() {")
        elif step_val > 1:
            _emit(ctx, "for " + target_str + " in (" + start_str + ".." + stop_str + ").step_by(" + str(step_val) + ") {")
        elif step_val < -1:
            abs_step = -step_val
            _emit(ctx, "for " + target_str + " in (" + stop_str + ".." + start_str + ").step_by(" + str(abs_step) + ").rev() {")
        else:
            _emit(ctx, "for " + target_str + " in " + start_str + ".." + stop_str + " {")
    else:
        # Dynamic step - use while loop
        step_str = _emit_expr(ctx, step)
        _emit(ctx, "let mut " + target_str + ": " + target_type + " = " + start_str + ";")
        _emit(ctx, "while " + target_str + " < " + stop_str + " {")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        _emit(ctx, target_str + " += (" + step_str + ") as " + target_type + ";")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        return

    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_runtime_iter_for_from_plan(
    ctx: RsEmitContext,
    plan: dict[str, JsonVal],
    target_plan: JsonVal,
    body: list[JsonVal],
) -> None:
    """Emit RuntimeIterForPlan from iter_plan."""
    iter_expr = plan.get("iter_expr")
    if iter_expr is None:
        iter_expr = plan.get("iter")

    target_str = _emit_loop_target(ctx, None, target_plan)
    _emit_loop_var_declared(ctx, None, target_plan)
    # Infer element type from iterator's resolved_type for nested loop dispatch
    if isinstance(iter_expr, dict) and isinstance(target_plan, dict):
        iter_rt = _str(iter_expr, "resolved_type")
        target_id = _str(target_plan, "id")
        if target_id != "" and iter_rt.startswith("list["):
            elem_type = iter_rt[5:-1]
            ctx.var_types[target_id] = elem_type

    if iter_expr is not None:
        iter_str = _emit_for_iter(ctx, iter_expr, None)
    else:
        iter_str = "Vec::<Box<dyn std::any::Any>>::new().into_iter()"

    _emit(ctx, "for " + target_str + " in " + iter_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_for_iter(ctx: RsEmitContext, iter_node: JsonVal, target: JsonVal) -> str:
    """Generate the Rust iterator expression for a for-loop."""
    if not isinstance(iter_node, dict):
        return "[]"
    kind = _str(iter_node, "kind")
    resolved_type = _str(iter_node, "resolved_type")

    if kind == "Call":
        func = iter_node.get("func")
        args = _list(iter_node, "args")
        func_name = ""
        if isinstance(func, dict):
            func_name = _str(func, "id")

        # range() call
        if func_name == "range":
            if len(args) == 1:
                end = _emit_expr(ctx, args[0])
                return "(0_i64.." + end + ")"
            elif len(args) == 2:
                start = _emit_expr(ctx, args[0])
                end = _emit_expr(ctx, args[1])
                return "(" + start + ".." + end + ")"
            elif len(args) == 3:
                start = _emit_expr(ctx, args[0])
                end = _emit_expr(ctx, args[1])
                step = _emit_expr(ctx, args[2])
                # For now, use a simple range (step handling simplified)
                return "(" + start + ".." + end + ").step_by(" + step + " as usize)"

        # enumerate()
        if func_name == "enumerate":
            if len(args) >= 1:
                inner_iter = _emit_for_iter(ctx, args[0], target)
                if len(args) == 2:
                    start_expr = _emit_expr(ctx, args[1])
                    return inner_iter + ".enumerate().map(|(i, v)| (" + start_expr + " + i as i64, v))"
                return inner_iter + ".enumerate().map(|(i, v)| (i as i64, v))"

        # reversed()
        if func_name == "reversed":
            if len(args) == 1:
                inner = _emit_expr(ctx, args[0])
                return inner + ".iter_snapshot().into_iter().rev()"

    # If resolved_type is unknown/empty, check ctx.var_types for the variable
    if resolved_type in ("", "unknown") and isinstance(iter_node, dict) and _str(iter_node, "kind") == "Name":
        var_id = _str(iter_node, "id")
        if var_id in ctx.var_types:
            resolved_type = ctx.var_types[var_id]

    # List/collection iteration
    if resolved_type.startswith("list[") or resolved_type == "list":
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".iter_snapshot().into_iter()"

    # String iteration (character by character)
    if resolved_type == "str":
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".chars().map(|c| c.to_string())"

    # Bytes/bytearray iteration (PyList<i64> uses iter_snapshot)
    if resolved_type in ("bytes", "bytearray"):
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".iter_snapshot().into_iter()"

    # Dict iteration (keys)
    if resolved_type.startswith("dict[") or resolved_type == "dict":
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".keys().cloned().collect::<Vec<_>>().into_iter()"

    # Set iteration
    if resolved_type.startswith("set[") or resolved_type == "set":
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".iter().cloned().collect::<Vec<_>>().into_iter()"

    # Default: try iter_snapshot for PyList, otherwise direct
    iter_expr = _emit_expr(ctx, iter_node)
    return iter_expr + ".into_iter()"


def _emit_static_range_for(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit StaticRangeForPlan."""
    target = node.get("target")
    start = node.get("start")
    stop = node.get("stop")
    step = node.get("step")
    body = _list(node, "body")

    target_str = "_i"
    if isinstance(target, dict):
        target_str = _rs_var_name(ctx, _str(target, "id"))
    elif isinstance(target, str):
        target_str = _rs_var_name(ctx, target)

    start_str = start if isinstance(start, str) else (_emit_expr(ctx, start) if start is not None else "0_i64")
    stop_str = stop if isinstance(stop, str) else (_emit_expr(ctx, stop) if stop is not None else "0_i64")
    step_val = 1
    if isinstance(step, int):
        step_val = step
    elif step is not None:
        step_str = _emit_expr(ctx, step)
        # Simplified: can't easily express negative step in Rust range
        _emit(ctx, "let mut " + target_str + ": i64 = " + start_str + ";")
        _emit(ctx, "while " + target_str + " < " + stop_str + " {")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        _emit(ctx, target_str + " += " + step_str + ";")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        return

    if step_val == 1:
        _emit(ctx, "for " + target_str + " in " + start_str + ".." + stop_str + " {")
    elif step_val == -1:
        _emit(ctx, "for " + target_str + " in (" + stop_str + ".." + start_str + ").rev() {")
    else:
        abs_step = abs(step_val)
        if step_val > 0:
            _emit(ctx, "for " + target_str + " in (" + start_str + ".." + stop_str + ").step_by(" + str(abs_step) + ") {")
        else:
            _emit(ctx, "for " + target_str + " in (" + stop_str + ".." + start_str + ").step_by(" + str(abs_step) + ").rev() {")

    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_runtime_iter_for(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit RuntimeIterForPlan."""
    _emit_for_core(ctx, node)


def _emit_while(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    test = node.get("test")
    body = _list(node, "body")
    orelse = _list(node, "orelse")

    test_str = _emit_bool_test(ctx, test)
    _emit(ctx, "while " + test_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")

    if len(orelse) > 0:
        _emit(ctx, "// while/else not supported in Rust")


def _emit_body(ctx: RsEmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        _emit_stmt(ctx, stmt)


def _emit_stmt(ctx: RsEmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        return
    kind = _str(node, "kind")

    if kind == "Expr":
        _emit_expr_stmt(ctx, node)
    elif kind == "Return":
        _emit_return(ctx, node)
    elif kind == "AnnAssign":
        _emit_ann_assign(ctx, node)
    elif kind == "Assign":
        _emit_assign(ctx, node)
    elif kind == "AugAssign":
        _emit_aug_assign(ctx, node)
    elif kind in ("FunctionDef", "ClosureDef"):
        _emit_function_def(ctx, node)
    elif kind == "ClassDef":
        _emit_class_def(ctx, node)
    elif kind == "If":
        _emit_if(ctx, node)
    elif kind == "While":
        _emit_while(ctx, node)
    elif kind == "ForCore":
        _emit_for_core(ctx, node)
    elif kind == "StaticRangeForPlan":
        _emit_static_range_for(ctx, node)
    elif kind == "RuntimeIterForPlan":
        _emit_runtime_iter_for(ctx, node)
    elif kind == "Raise":
        _emit_raise(ctx, node)
    elif kind == "Try":
        _emit_try(ctx, node)
    elif kind == "Pass":
        _emit(ctx, "// pass")
    elif kind == "Break":
        _emit(ctx, "break;")
    elif kind == "Continue":
        _emit(ctx, "continue;")
    elif kind == "comment":
        text = _str(node, "text")
        if text != "":
            _emit(ctx, "// " + text)
    elif kind == "blank":
        _emit_blank(ctx)
    elif kind in ("Import", "ImportFrom"):
        pass  # handled separately
    elif kind == "Delete":
        pass  # ignore del
    elif kind == "Global" or kind == "Nonlocal":
        pass  # ignore global/nonlocal
    elif kind == "Assert":
        test = node.get("test")
        msg = node.get("msg")
        test_str = _emit_expr(ctx, test)
        if msg is not None:
            msg_str = _emit_expr(ctx, msg)
            _emit(ctx, "assert!(" + test_str + ", \"{}\", " + msg_str + ");")
        else:
            _emit(ctx, "assert!(" + test_str + ");")
    elif kind == "With":
        _emit_with(ctx, node)
    elif kind == "TypeAlias":
        _emit_type_alias(ctx, node)
    elif kind == "VarDecl":
        _emit_var_decl(ctx, node)
    else:
        _emit(ctx, "// unsupported stmt: " + kind)


def _emit_if(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    test = node.get("test")
    body = _list(node, "body")
    orelse = _list(node, "orelse")

    test_str = _emit_bool_test(ctx, test)
    _emit(ctx, "if " + test_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1

    if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
        _emit(ctx, "} else if " + _emit_bool_test(ctx, orelse[0].get("test")) + " {")
        ctx.indent_level += 1
        _emit_body(ctx, _list(orelse[0], "body"))
        ctx.indent_level -= 1
        _emit_remaining_orelse(ctx, orelse[0])
    elif len(orelse) > 0:
        _emit(ctx, "} else {")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        _emit(ctx, "}")


def _emit_remaining_orelse(ctx: RsEmitContext, if_node: dict[str, JsonVal]) -> None:
    orelse = _list(if_node, "orelse")
    if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
        _emit(ctx, "} else if " + _emit_bool_test(ctx, orelse[0].get("test")) + " {")
        ctx.indent_level += 1
        _emit_body(ctx, _list(orelse[0], "body"))
        ctx.indent_level -= 1
        _emit_remaining_orelse(ctx, orelse[0])
    elif len(orelse) > 0:
        _emit(ctx, "} else {")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        _emit(ctx, "}")


def _emit_with(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    items = _list(node, "items")
    body = _list(node, "body")
    # Simplified: emit body only, RAII handles cleanup
    _emit(ctx, "// with block (RAII-based)")
    for item in items:
        if isinstance(item, dict):
            context_expr = item.get("context_expr")
            opt_vars = item.get("optional_vars")
            if context_expr is not None:
                ctx_str = _emit_expr(ctx, context_expr)
                if opt_vars is not None:
                    var_str = _emit_expr(ctx, opt_vars)
                    _emit(ctx, "let mut " + var_str + " = " + ctx_str + ";")
    _emit(ctx, "{")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_type_alias(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    value = node.get("value")
    if value is not None:
        if isinstance(value, dict):
            resolved_type = _str(value, "resolved_type")
            if resolved_type != "":
                _emit(ctx, "type " + safe_rs_ident(name) + " = " + rs_type(resolved_type) + ";")
                return
    _emit(ctx, "// type alias: " + name)


def _emit_var_decl(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    resolved_type = _str(node, "resolved_type")
    value = node.get("value")
    rs_name = _rs_var_name(ctx, name)
    ctx.declared_vars.add(name)
    rt = _rs_type_for_context(ctx, resolved_type) if resolved_type != "" else ""
    if value is not None:
        rhs = _emit_expr(ctx, value)
        if rt != "" and rt != "()":
            _emit(ctx, "let mut " + rs_name + ": " + rt + " = " + rhs + ";")
        else:
            _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")
    else:
        if rt != "" and rt != "()":
            zero = rs_zero_value(resolved_type)
            _emit(ctx, "let mut " + rs_name + ": " + rt + " = " + zero + ";")
        else:
            _emit(ctx, "let mut " + rs_name + ": i64 = 0;")


# ---------------------------------------------------------------------------
# Function definition
# ---------------------------------------------------------------------------

def _emit_function_def(ctx: RsEmitContext, node: dict[str, JsonVal], owner: str = "") -> None:
    name = _str(node, "name")
    arg_order = _list(node, "arg_order")
    arg_types = _dict(node, "arg_types")
    return_type = _str(node, "return_type")
    body = _list(node, "body")
    decorators = _list(node, "decorator_list")
    is_static = any(
        isinstance(d, dict) and _str(d, "id") == "staticmethod"
        for d in decorators
    )
    is_property = any(
        isinstance(d, dict) and _str(d, "id") == "property"
        for d in decorators
    )
    is_classmethod = any(
        isinstance(d, dict) and _str(d, "id") == "classmethod"
        for d in decorators
    )

    leading_trivia = _list(node, "leading_trivia")
    for trivia in leading_trivia:
        if isinstance(trivia, dict):
            trivia_kind = _str(trivia, "kind")
            if trivia_kind == "comment":
                text = _str(trivia, "text")
                if text != "":
                    _emit(ctx, "// " + text)
            elif trivia_kind == "blank":
                _emit_blank(ctx)

    # Build parameter list
    params: list[str] = []
    has_self = "self" in arg_order
    is_method = owner != "" and has_self

    for arg in arg_order:
        if not isinstance(arg, str):
            continue
        if arg == "self":
            params.append("&mut self")
            continue
        arg_type = _str(arg_types, arg)
        if arg_type in ctx.trait_names:
            rs_arg_type = "&dyn " + safe_rs_ident(arg_type)
        else:
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
        # Owned Box<UserClass> params may have fields mutated — emit as `mut param`
        mut_prefix = "mut " if rs_arg_type.startswith("Box<") else ""
        params.append(mut_prefix + safe_rs_ident(arg) + ": " + rs_arg_type)

    # Varargs (*args) → PyList<ElemType>
    vararg_name = _str(node, "vararg_name")
    vararg_type = _str(node, "vararg_type")
    if vararg_name != "":
        elem_type = _rs_type_for_context(ctx, vararg_type) if vararg_type != "" else "Box<dyn std::any::Any>"
        params.append(safe_rs_ident(vararg_name) + ": PyList<" + elem_type + ">")

    params_str = ", ".join(params)

    # Return type
    if return_type == "" or return_type == "None" or return_type == "none":
        ret_str = ""
    else:
        rt = _rs_type_for_context(ctx, return_type)
        if rt == "()":
            ret_str = ""
        else:
            ret_str = " -> " + rt

    # Function name (handle module private symbol prefix)
    if owner != "":
        fn_name = safe_rs_ident(name)
    else:
        fn_name = _rs_symbol_name(ctx, name)

    # Save/restore context
    prev_return_type = ctx.current_return_type
    prev_declared = set(ctx.declared_vars)
    prev_var_types = dict(ctx.var_types)
    prev_nested_fn = ctx.current_nested_fn
    ctx.current_return_type = return_type
    ctx.declared_vars = set()

    # Add parameters to declared vars
    for arg in arg_order:
        if isinstance(arg, str) and arg != "self":
            ctx.declared_vars.add(arg)
            arg_type = _str(arg_types, arg)
            if arg_type != "":
                ctx.var_types[arg] = arg_type
    if vararg_name != "":
        ctx.declared_vars.add(vararg_name)
        if vararg_type != "":
            ctx.var_types[vararg_name] = "list[" + vararg_type + "]"

    # Nested function (inside another function body, not a class method): emit as closure
    is_nested = not ctx.at_module_level and owner == ""
    if is_nested:
        ctx.current_nested_fn = fn_name
        _emit(ctx, "let " + fn_name + " = move |" + params_str + "|" + ret_str + " {")
    else:
        ctx.current_nested_fn = ""
        _emit(ctx, "fn " + fn_name + "(" + params_str + ")" + ret_str + " {")
    ctx.indent_level += 1
    prev_module_level = ctx.at_module_level
    ctx.at_module_level = False
    body_is_empty = len(body) == 0 or all(
        isinstance(s, dict) and _str(s, "kind") == "Pass"
        for s in body
    )
    if body_is_empty and return_type not in ("", "None", "NoneType"):
        # Abstract/stub method: emit todo!()
        _emit(ctx, 'todo!("abstract method ' + fn_name + '")')
    else:
        _emit_body(ctx, body)
    ctx.at_module_level = prev_module_level
    ctx.indent_level -= 1
    if is_nested:
        _emit(ctx, "};")
    else:
        _emit(ctx, "}")

    # Restore context
    ctx.current_return_type = prev_return_type
    ctx.declared_vars = prev_declared
    ctx.var_types = prev_var_types
    ctx.current_nested_fn = prev_nested_fn


# ---------------------------------------------------------------------------
# Class definition
# ---------------------------------------------------------------------------

def _repr_constant_default(node: dict[str, JsonVal]) -> str:
    """Return a simple Rust literal string for a constant node (for default values)."""
    value = node.get("value")
    resolved_type = _str(node, "resolved_type")
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value) + "_i64"
    if isinstance(value, float):
        return str(value) + "_f64"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
        return "\"" + escaped + "\".to_string()"
    return "Default::default()"


def _collect_class_info(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Collect class metadata for later use during emission."""
    name = _str(node, "name")
    if name == "":
        return
    ctx.class_names.add(name)
    body = _list(node, "body")

    base_str = _str(node, "base")
    if base_str != "" and base_str != "None":
        ctx.class_bases[name] = base_str
    else:
        bases = _list(node, "bases")
        if len(bases) > 0:
            base = bases[0]
            if isinstance(base, dict):
                ctx.class_bases[name] = _str(base, "id")

    fields: dict[str, str] = {}
    field_defaults: dict[str, str | None] = {}
    methods: dict[str, dict[str, JsonVal]] = {}
    statics: set[str] = set()
    class_vars: dict[str, str] = {}

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            decorators = _list(stmt, "decorator_list")
            is_static = any(isinstance(d, dict) and _str(d, "id") == "staticmethod" for d in decorators)
            if is_static:
                statics.add(fn_name)
            methods[fn_name] = stmt
            # Collect instance fields from __init__ body
            if fn_name == "__init__":
                for init_stmt in _list(stmt, "body"):
                    if not isinstance(init_stmt, dict):
                        continue
                    init_kind = _str(init_stmt, "kind")
                    if init_kind in ("AnnAssign", "Assign"):
                        itarget = init_stmt.get("target")
                        if isinstance(itarget, dict) and _str(itarget, "kind") == "Attribute":
                            iobj = itarget.get("value")
                            if isinstance(iobj, dict) and _str(iobj, "id") == "self":
                                ifield = _str(itarget, "attr")
                                itype = _str(init_stmt, "resolved_type")
                                if itype == "":
                                    itype = _str(init_stmt, "decl_type")
                                if itype == "":
                                    itype = _str(itarget, "resolved_type")
                                if ifield != "" and itype != "":
                                    fields[ifield] = itype
                                    ival = init_stmt.get("value")
                                    if isinstance(ival, dict) and ival.get("kind") == "Constant":
                                        field_defaults[ifield] = _repr_constant_default(ival)
                                    else:
                                        field_defaults[ifield] = None
        elif stmt_kind in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                resolved_type = _str(stmt, "resolved_type")
                if resolved_type == "":
                    resolved_type = _str(stmt, "decl_type")
                if field_name != "" and resolved_type != "":
                    fields[field_name] = resolved_type
                    class_vars[field_name] = resolved_type
                    # Track the default value
                    val_node = stmt.get("value")
                    if isinstance(val_node, dict) and val_node.get("kind") == "Constant":
                        field_defaults[field_name] = _repr_constant_default(val_node)
                    else:
                        field_defaults[field_name] = None

    ctx.class_fields[name] = fields
    ctx.class_field_defaults[name] = field_defaults
    ctx.class_vars[name] = class_vars
    ctx.class_instance_methods[name] = methods
    ctx.class_static_methods[name] = statics
    # Collect @property methods
    property_methods: set[str] = set()
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            # EAST3 uses "decorators" list (strings or dicts); AST uses "decorator_list"
            decs = _list(stmt, "decorators") + _list(stmt, "decorator_list")
            is_prop = any(
                (isinstance(d, str) and d == "property") or
                (isinstance(d, dict) and _str(d, "id") == "property")
                for d in decs
            )
            if is_prop:
                property_methods.add(fn_name)
    ctx.class_property_methods[name] = property_methods

    # Detect @trait decorator (string or dict form)
    decorators_raw = node.get("decorators") or []
    for dec in decorators_raw:
        if isinstance(dec, str) and dec in ("trait", "@trait"):
            ctx.trait_names.add(name)
        elif isinstance(dec, dict) and _str(dec, "id") in ("trait", "@trait"):
            ctx.trait_names.add(name)

    # Check if this is an Enum subclass
    base_raw = _str(node, "base")
    base_id = ctx.class_bases.get(name, base_raw)
    if base_id in ("Enum", "IntEnum", "IntFlag", "Flag"):
        # Collect enum members (class-level assignments)
        members: list[str] = []
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            stmt_kind = _str(stmt, "kind")
            if stmt_kind == "Assign":
                target = stmt.get("target")
                if isinstance(target, dict) and _str(target, "kind") == "Name":
                    members.append(_str(target, "id"))
        ctx.enum_members[name] = members
        ctx.enum_bases[name] = base_id


def _emit_enum_class(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit a Python Enum subclass as a Rust newtype struct with const members."""
    name = _str(node, "name")
    rs_name = safe_rs_ident(name)
    body = _list(node, "body")
    base = ctx.enum_bases.get(name, "Enum")
    # Use i64 as the underlying type
    _emit_blank(ctx)
    _emit(ctx, "#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]")
    _emit(ctx, "pub struct " + rs_name + "(pub i64);")
    _emit_blank(ctx)
    _emit(ctx, "impl " + rs_name + " {")
    ctx.indent_level += 1
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind == "Assign":
            target = stmt.get("target")
            val_node = stmt.get("value")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                member_name = _str(target, "id")
                if isinstance(val_node, dict):
                    val_str = _emit_expr(ctx, val_node)
                else:
                    val_str = "0"
                _emit(ctx, "pub const " + member_name + ": " + rs_name + " = " + rs_name + "(" + val_str + ");")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    # Implement PyStringify
    _emit_blank(ctx)
    _emit(ctx, "impl PyStringify for " + rs_name + " {")
    ctx.indent_level += 1
    _emit(ctx, "fn py_stringify(&self) -> String {")
    ctx.indent_level += 1
    _emit(ctx, "self.0.to_string()")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    # Implement PartialEq<i64> for comparisons like Status::OK == 0
    _emit_blank(ctx)
    _emit(ctx, "impl PartialEq<i64> for " + rs_name + " {")
    ctx.indent_level += 1
    _emit(ctx, "fn eq(&self, other: &i64) -> bool { self.0 == *other }")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit(ctx, "impl PartialEq<" + rs_name + "> for i64 {")
    ctx.indent_level += 1
    _emit(ctx, "fn eq(&self, other: &" + rs_name + ") -> bool { *self == other.0 }")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    # Implement PyAnyToI64Arg for py_int() conversions
    _emit(ctx, "impl PyAnyToI64Arg for " + rs_name + " {")
    ctx.indent_level += 1
    _emit(ctx, "fn py_any_to_i64_arg(&self) -> i64 { self.0 }")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    # For IntFlag: also emit BitOr, BitAnd, BitXor
    if base in ("IntFlag", "Flag"):
        _emit_blank(ctx)
        _emit(ctx, "impl std::ops::BitOr for " + rs_name + " {")
        ctx.indent_level += 1
        _emit(ctx, "type Output = " + rs_name + ";")
        _emit(ctx, "fn bitor(self, rhs: " + rs_name + ") -> " + rs_name + " { " + rs_name + "(self.0 | rhs.0) }")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit(ctx, "impl std::ops::BitAnd for " + rs_name + " {")
        ctx.indent_level += 1
        _emit(ctx, "type Output = " + rs_name + ";")
        _emit(ctx, "fn bitand(self, rhs: " + rs_name + ") -> " + rs_name + " { " + rs_name + "(self.0 & rhs.0) }")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit(ctx, "impl std::ops::BitXor for " + rs_name + " {")
        ctx.indent_level += 1
        _emit(ctx, "type Output = " + rs_name + ";")
        _emit(ctx, "fn bitxor(self, rhs: " + rs_name + ") -> " + rs_name + " { " + rs_name + "(self.0 ^ rhs.0) }")
        ctx.indent_level -= 1
        _emit(ctx, "}")


def _emit_class_def(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    if name == "":
        return
    body = _list(node, "body")
    bases = _list(node, "bases")
    decorators = _list(node, "decorators")  # EAST3 uses "decorators", not "decorator_list"
    rs_name = safe_rs_ident(name)

    # Emit Enum subclasses as a newtype struct with const members
    if name in ctx.enum_bases:
        _emit_enum_class(ctx, node)
        return

    is_trait = name in ctx.trait_names or any(
        (isinstance(d, str) and d in ("trait", "@trait")) or
        (isinstance(d, dict) and _str(d, "id") in ("trait", "@trait"))
        for d in decorators
    )

    # Detect @implements(...) decorator to get trait implementations for this class
    implements_traits: list[str] = []
    for dec in decorators:
        dec_str = dec if isinstance(dec, str) else (_str(dec, "repr") or _str(dec, "id"))
        if dec_str.startswith("implements(") and dec_str.endswith(")"):
            inner = dec_str[len("implements("):-1]
            for part in inner.split(","):
                t = part.strip()
                if t != "":
                    implements_traits.append(t)

    if is_trait:
        _emit_trait_definition(ctx, name, body)
        return

    leading_trivia = _list(node, "leading_trivia")
    for trivia in leading_trivia:
        if isinstance(trivia, dict):
            trivia_kind = _str(trivia, "kind")
            if trivia_kind == "comment":
                text = _str(trivia, "text")
                if text != "":
                    _emit(ctx, "// " + text)
            elif trivia_kind == "blank":
                _emit_blank(ctx)

    # Collect field types from __init__
    fields: dict[str, str] = {}
    init_method = None
    other_methods: list[dict[str, JsonVal]] = []
    class_assign_stmts: list[dict[str, JsonVal]] = []  # class-level Assign stmts (class vars)

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            if fn_name == "__init__":
                init_method = stmt
                # Collect field assignments from __init__ body
                for init_stmt in _list(stmt, "body"):
                    if not isinstance(init_stmt, dict):
                        continue
                    init_kind = _str(init_stmt, "kind")
                    if init_kind in ("AnnAssign", "Assign"):
                        target = init_stmt.get("target")
                        if isinstance(target, dict) and _str(target, "kind") == "Attribute":
                            attr_obj = target.get("value")
                            if isinstance(attr_obj, dict) and _str(attr_obj, "id") == "self":
                                field_name = _str(target, "attr")
                                # Try multiple sources for the field type
                                resolved_type = _str(init_stmt, "resolved_type")
                                if resolved_type == "":
                                    resolved_type = _str(init_stmt, "decl_type")
                                if resolved_type == "":
                                    resolved_type = _str(target, "resolved_type")
                                if field_name != "" and resolved_type != "":
                                    fields[field_name] = resolved_type
            else:
                other_methods.append(stmt)
        elif stmt_kind == "AnnAssign":
            # Class-level type-annotated field declarations (dataclass fields, etc.)
            # AnnAssign always becomes an instance struct field (with or without default value)
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                resolved_type = _str(stmt, "resolved_type")
                if resolved_type == "":
                    resolved_type = _str(stmt, "decl_type")
                if resolved_type == "" and isinstance(stmt.get("annotation"), str):
                    resolved_type = _str(stmt, "annotation")
                if field_name != "" and resolved_type != "" and not field_name.startswith("__"):
                    fields[field_name] = resolved_type
        elif stmt_kind == "Assign":
            # Class-level plain assignment (no type annotation) = class variable (not instance field)
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                if field_name != "" and not field_name.startswith("__"):
                    class_assign_stmts.append(stmt)

    # Inherit parent fields (struct fields from parent class)
    parent_class = ctx.class_bases.get(name, "")
    if parent_class != "" and parent_class in ctx.class_fields:
        for pf, pt in ctx.class_fields[parent_class].items():
            if pf not in fields:
                fields[pf] = pt

    # Emit struct definition
    _emit_blank(ctx)
    if len(fields) > 0:
        _emit(ctx, "#[derive(Debug, Clone)]")
        _emit(ctx, "pub struct " + rs_name + " {")
        ctx.indent_level += 1
        for field_name, field_type in fields.items():
            rt = _rs_type_for_context(ctx, field_type)
            _emit(ctx, "pub " + safe_rs_ident(field_name) + ": " + rt + ",")
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        _emit(ctx, "#[derive(Debug, Clone)]")
        _emit(ctx, "pub struct " + rs_name + " {}")

    # Emit impl block
    prev_class = ctx.current_class
    ctx.current_class = name
    prev_declared = set(ctx.declared_vars)
    prev_var_types = dict(ctx.var_types)

    _emit_blank(ctx)
    _emit(ctx, "impl " + rs_name + " {")
    ctx.indent_level += 1

    # Emit new() constructor from __init__
    if init_method is not None:
        _emit_init_as_new(ctx, init_method, rs_name, fields)
    elif len(fields) > 0:
        # Generate new() taking all fields as args (works for both dataclasses and regular classes)
        params = ", ".join(
            safe_rs_ident(fn) + ": " + _rs_type_for_context(ctx, ft)
            for fn, ft in fields.items()
        )
        _emit(ctx, "fn new(" + params + ") -> Self {")
        ctx.indent_level += 1
        _emit(ctx, rs_name + " {")
        ctx.indent_level += 1
        for fn in fields:
            _emit(ctx, safe_rs_ident(fn) + ": " + safe_rs_ident(fn) + ",")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        _emit(ctx, "fn new() -> Self {")
        ctx.indent_level += 1
        _emit(ctx, rs_name + " {}")
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # Emit other methods
    for method in other_methods:
        _emit_blank(ctx)
        _emit_function_def(ctx, method, owner=name)

    # Emit inherited methods from parent class (not overridden in child)
    child_method_names: set[str] = {_str(m, "name") for m in other_methods if isinstance(m, dict)}
    if init_method is not None:
        child_method_names.add("__init__")
    parent_class = ctx.class_bases.get(name, "")
    if parent_class != "" and parent_class in ctx.class_instance_methods and parent_class not in ctx.trait_names:
        parent_methods = ctx.class_instance_methods[parent_class]
        for mname, mnode in parent_methods.items():
            if mname not in child_method_names and mname != "__init__":
                _emit_blank(ctx)
                _emit_function_def(ctx, mnode, owner=name)

    # Emit class-level variables as associated consts (for Holder::X pattern)
    for ca_stmt in class_assign_stmts:
        ca_target = ca_stmt.get("target")
        if not isinstance(ca_target, dict):
            continue
        ca_name = _str(ca_target, "id")
        ca_val = ca_stmt.get("value")
        ca_type = _str(ca_stmt, "resolved_type") or _str(ca_stmt, "decl_type")
        if ca_name == "" or ca_val is None:
            continue
        rs_ca_name = safe_rs_ident(ca_name).upper()
        # For tuple/list of homogeneous constants → const &'static [T]
        if isinstance(ca_val, dict) and ca_val.get("kind") in ("Tuple", "List"):
            elems = _list(ca_val, "elements")
            all_const = all(isinstance(e, dict) and e.get("kind") == "Constant" for e in elems)
            if all_const and len(elems) > 0:
                elem_type = _str(elems[0], "resolved_type") if elems else "int64"
                rs_elem = _rs_type_for_context(ctx, elem_type)
                const_elems = ", ".join(_emit_expr(ctx, e) for e in elems)
                _emit_blank(ctx)
                _emit(ctx, "const " + rs_ca_name + ": &'static [" + rs_elem + "] = &[" + const_elems + "];")
                continue
        # For simple constants → const T
        if isinstance(ca_val, dict) and ca_val.get("kind") == "Constant":
            rs_t = _rs_type_for_context(ctx, ca_type) if ca_type != "" else "i64"
            const_val = _emit_expr(ctx, ca_val)
            _emit_blank(ctx)
            _emit(ctx, "const " + rs_ca_name + ": " + rs_t + " = " + const_val + ";")
            continue
        # Fallback: emit as comment
        _emit_blank(ctx)
        _emit(ctx, "// class_var " + rs_ca_name + ": (non-const value, skipped)")

    ctx.indent_level -= 1
    _emit(ctx, "}")

    ctx.current_class = prev_class
    ctx.declared_vars = prev_declared
    ctx.var_types = prev_var_types

    # Emit trait implementations
    for base_node in bases:
        if isinstance(base_node, dict):
            base_name = _str(base_node, "id")
            if base_name != "" and base_name in ctx.trait_names:
                _emit_trait_impl(ctx, name, base_name)

    # Emit @implements trait impls for this class (including transitive base traits)
    emitted_trait_impls: set[str] = set()
    def _emit_trait_impl_recursive(class_name: str, trait_name: str) -> None:
        if trait_name in emitted_trait_impls:
            return
        if trait_name not in ctx.trait_names:
            return
        # First emit base trait impls (for traits that extend other traits)
        base_of_trait = ctx.class_bases.get(trait_name, "")
        if base_of_trait != "" and base_of_trait in ctx.trait_names:
            _emit_trait_impl_recursive(class_name, base_of_trait)
        emitted_trait_impls.add(trait_name)
        _emit_trait_methods_impl(ctx, class_name, trait_name)

    for trait_name in implements_traits:
        _emit_trait_impl_recursive(name, trait_name)

    # Emit PyRuntimeTypeId for user-defined classes (needed for isinstance checks)
    # TID constant name: {MODULE_STEM_UPPER}_{CLASS_UPPER}_TID
    if name not in ctx.enum_bases:
        _emit_class_runtime_type_id(ctx, name)


def _emit_init_as_new(
    ctx: RsEmitContext,
    init_method: dict[str, JsonVal],
    rs_name: str,
    fields: dict[str, str],
) -> None:
    """Emit __init__ as Rust new() constructor."""
    arg_order = _list(init_method, "arg_order")
    arg_types = _dict(init_method, "arg_types")
    body = _list(init_method, "body")

    params: list[str] = []
    for arg in arg_order:
        if not isinstance(arg, str) or arg == "self":
            continue
        arg_type = _str(arg_types, arg)
        rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
        params.append(safe_rs_ident(arg) + ": " + rs_arg_type)

    params_str = ", ".join(params)
    _emit(ctx, "fn new(" + params_str + ") -> Self {")
    ctx.indent_level += 1

    # Add params to declared vars
    prev_declared = set(ctx.declared_vars)
    ctx.declared_vars = set()
    for arg in arg_order:
        if isinstance(arg, str) and arg != "self":
            ctx.declared_vars.add(arg)

    # Emit body, collecting field assignments
    field_assignments: dict[str, str] = {}
    other_stmts: list[dict[str, JsonVal]] = []

    # Seed field_assignments with parent field defaults for AugAssign support
    parent_class_for_init = ctx.class_bases.get(rs_name, "")
    if parent_class_for_init == "":
        parent_class_for_init = ctx.class_bases.get(ctx.current_class, "")
    if parent_class_for_init != "" and parent_class_for_init in ctx.class_field_defaults:
        for pf, pdefault in ctx.class_field_defaults[parent_class_for_init].items():
            if pdefault is not None and pf not in field_assignments:
                field_assignments[pf] = pdefault

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Attribute":
                attr_obj = target.get("value")
                if isinstance(attr_obj, dict) and _str(attr_obj, "id") == "self":
                    field_name = _str(target, "attr")
                    value = stmt.get("value")
                    if field_name != "" and value is not None:
                        field_assignments[field_name] = _emit_expr(ctx, value)
                    continue
        if stmt_kind == "AugAssign":
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Attribute":
                attr_obj = target.get("value")
                if isinstance(attr_obj, dict) and _str(attr_obj, "id") == "self":
                    field_name = _str(target, "attr")
                    op = _str(stmt, "op")
                    rhs_expr = _emit_expr(ctx, stmt.get("value")) if stmt.get("value") is not None else "0"
                    _RS_OP = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "Mod": "%"}
                    rs_op = _RS_OP.get(op, "+")
                    base = field_assignments.get(field_name, rs_zero_value(fields.get(field_name, "int")))
                    field_assignments[field_name] = base + " " + rs_op + " " + rhs_expr
                    continue
        # Skip super().__init__() calls — parent fields are inherited at struct level
        if stmt_kind == "Expr":
            val = stmt.get("value")
            if isinstance(val, dict) and _str(val, "kind") == "Call":
                func = val.get("func")
                if isinstance(func, dict) and _str(func, "kind") == "Attribute":
                    fn_attr = _str(func, "attr")
                    fn_obj = func.get("value")
                    if fn_attr == "__init__" and isinstance(fn_obj, dict) and _str(fn_obj, "kind") == "Call":
                        fn_obj_func = fn_obj.get("func")
                        if isinstance(fn_obj_func, dict) and _str(fn_obj_func, "id") in ("super", "py_super"):
                            continue
        other_stmts.append(stmt)

    # Emit non-field-assignment statements
    _emit_body(ctx, other_stmts)

    # Emit struct literal
    _emit(ctx, rs_name + " {")
    ctx.indent_level += 1
    for field_name, field_type in fields.items():
        rs_field = safe_rs_ident(field_name)
        if field_name in field_assignments:
            _emit(ctx, rs_field + ": " + field_assignments[field_name] + ",")
        else:
            _emit(ctx, rs_field + ": " + rs_zero_value(field_type) + ",")
    ctx.indent_level -= 1
    _emit(ctx, "}")

    ctx.declared_vars = prev_declared
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _camel_to_screaming_snake(name: str) -> str:
    """Convert CamelCase to SCREAMING_SNAKE_CASE: MathUtil → MATH_UTIL."""
    import re
    # Insert underscore before uppercase letters that follow lowercase letters or digits
    s = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', name)
    # Insert underscore before uppercase letters that are followed by lowercase letters (acronym handling)
    s = re.sub(r'(?<=[A-Z])([A-Z][a-z])', r'_\1', s)
    return s.upper()


def _class_tid_const_name(ctx: RsEmitContext, class_name: str) -> str:
    """Build the TID const name for a user-defined class: {MODULE_STEM_UPPER}_{CLASS_SNAKE_UPPER}_TID."""
    source_path = ctx.source_path
    if source_path != "":
        import os
        stem = os.path.splitext(os.path.basename(source_path))[0]
    elif ctx.module_id != "":
        stem = ctx.module_id.split(".")[-1]
    else:
        stem = "module"
    # Convert class name to SCREAMING_SNAKE_CASE (CamelCase → CAMEL_CASE)
    # Use original Python class name (not safe_rs_ident) for TID const name matching
    cls_safe = _camel_to_screaming_snake(class_name)
    stem_safe = stem.upper().replace("-", "_").replace(".", "_")
    return stem_safe + "_" + cls_safe + "_TID"


def _emit_class_runtime_type_id(ctx: RsEmitContext, class_name: str) -> None:
    """Emit `impl PyRuntimeTypeId for ClassName` using the module-scoped TID constant."""
    rs_name = safe_rs_ident(class_name)
    tid_const = _class_tid_const_name(ctx, class_name)
    _emit_blank(ctx)
    _emit(ctx, "impl PyRuntimeTypeId for " + rs_name + " {")
    ctx.indent_level += 1
    _emit(ctx, "fn py_runtime_type_id(&self) -> i64 { " + tid_const + " }")
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_trait_definition(ctx: RsEmitContext, name: str, body: list[JsonVal]) -> None:
    """Emit a @trait decorated class as a Rust trait."""
    rs_name = safe_rs_ident(name)
    _emit_blank(ctx)
    _emit(ctx, "pub trait " + rs_name + " {")
    ctx.indent_level += 1
    prev_class = ctx.current_class
    ctx.current_class = name
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            if fn_name == "__init__":
                continue
            arg_order = _list(stmt, "arg_order")
            arg_types = _dict(stmt, "arg_types")
            return_type = _str(stmt, "return_type")
            stmt_mutates = bool(stmt.get("mutates_self", True))
            params: list[str] = []
            for arg in arg_order:
                if not isinstance(arg, str):
                    continue
                if arg == "self":
                    params.append("&mut self" if stmt_mutates else "&self")
                    continue
                arg_type = _str(arg_types, arg)
                if arg_type in ctx.trait_names:
                    rs_arg_type = "&dyn " + safe_rs_ident(arg_type)
                else:
                    rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
                params.append(safe_rs_ident(arg) + ": " + rs_arg_type)
            params_str = ", ".join(params)
            if return_type in ("", "None", "none"):
                ret_str = ""
            else:
                rt = _rs_type_for_context(ctx, return_type)
                ret_str = "" if rt == "()" else " -> " + rt
            _emit(ctx, "fn " + safe_rs_ident(fn_name) + "(" + params_str + ")" + ret_str + ";")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.current_class = prev_class


def _emit_trait_methods_impl(ctx: RsEmitContext, class_name: str, trait_name: str) -> None:
    """Emit trait impl for a class using its own methods that match the trait."""
    rs_class = safe_rs_ident(class_name)
    rs_trait = safe_rs_ident(trait_name)
    trait_methods = ctx.class_instance_methods.get(trait_name, {})
    class_methods = ctx.class_instance_methods.get(class_name, {})
    _emit_blank(ctx)
    _emit(ctx, "impl " + rs_trait + " for " + rs_class + " {")
    ctx.indent_level += 1
    prev_class = ctx.current_class
    ctx.current_class = class_name
    for mname, trait_method_node in trait_methods.items():
        if mname == "__init__":
            continue
        method_node = class_methods.get(mname)
        if method_node is not None:
            # Use trait method's mutates_self to determine &self vs &mut self in the impl
            # so it matches the trait definition signature
            trait_mutates = bool(trait_method_node.get("mutates_self", True)) if isinstance(trait_method_node, dict) else True
            self_ref = "&mut self" if trait_mutates else "&self"
            # Emit method signature and body with correct self ref
            _emit_blank(ctx)
            _emit_trait_impl_method(ctx, method_node, class_name, self_ref)
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.current_class = prev_class


def _emit_trait_impl_method(ctx: RsEmitContext, node: dict, owner: str, self_ref: str) -> None:
    """Emit a method for a trait impl block, using self_ref (&self or &mut self)."""
    name = _str(node, "name")
    arg_order = _list(node, "arg_order")
    arg_types = _dict(node, "arg_types")
    arg_defaults = _dict(node, "arg_defaults")
    return_type = _str(node, "return_type")
    body = _list(node, "body")

    params: list[str] = []
    for arg in arg_order:
        if not isinstance(arg, str):
            continue
        if arg == "self":
            params.append(self_ref)
            continue
        arg_type = _str(arg_types, arg)
        if arg_type in ctx.trait_names:
            rs_arg_type = "&dyn " + safe_rs_ident(arg_type)
        else:
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
        params.append(safe_rs_ident(arg) + ": " + rs_arg_type)

    params_str = ", ".join(params)
    if return_type in ("", "None", "none"):
        ret_str = ""
    else:
        rt = _rs_type_for_context(ctx, return_type)
        ret_str = "" if rt == "()" else " -> " + rt

    fn_name = safe_rs_ident(name)
    _emit(ctx, "fn " + fn_name + "(" + params_str + ")" + ret_str + " {")
    ctx.indent_level += 1

    prev_return_type = ctx.current_return_type
    prev_declared = set(ctx.declared_vars)
    prev_var_types = dict(ctx.var_types)
    ctx.current_return_type = return_type
    ctx.declared_vars = set()
    for arg in arg_order:
        if isinstance(arg, str) and arg != "self":
            ctx.declared_vars.add(arg)
            arg_type = _str(arg_types, arg)
            if arg_type != "":
                ctx.var_types[arg] = arg_type

    _emit_body(ctx, body)
    ctx.current_return_type = prev_return_type
    ctx.declared_vars = prev_declared
    ctx.var_types = prev_var_types

    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_trait_impl(ctx: RsEmitContext, class_name: str, trait_name: str) -> None:
    _emit_blank(ctx)
    _emit(ctx, "impl " + safe_rs_ident(trait_name) + " for " + safe_rs_ident(class_name) + " {")
    ctx.indent_level += 1
    # Trait methods would go here (from the class)
    ctx.indent_level -= 1
    _emit(ctx, "}")


# ---------------------------------------------------------------------------
# First pass: collect signatures
# ---------------------------------------------------------------------------

def _first_pass(ctx: RsEmitContext, body: list[JsonVal]) -> None:
    """Collect class and function info before emission."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind == "ClassDef":
            name = _str(stmt, "name")
            ctx.class_names.add(name)
            _collect_class_info(ctx, stmt)
        elif kind in ("FunctionDef", "ClosureDef"):
            name = _str(stmt, "name")
            ctx.function_signatures[name] = stmt
            # Track original_name → name remapping (compiler-renamed functions)
            original_name = _str(stmt, "original_name")
            if original_name != "" and original_name != name:
                ctx.original_name_map[original_name] = name


# ---------------------------------------------------------------------------
# Module-level emission
# ---------------------------------------------------------------------------

def _emit_module_body(ctx: RsEmitContext, body: list[JsonVal]) -> None:
    ctx.at_module_level = True
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("Import", "ImportFrom"):
            continue  # handled separately
        _emit_stmt(ctx, stmt)
    ctx.at_module_level = False


def _collect_uses(ctx: RsEmitContext) -> list[str]:
    """Determine which `use` statements are needed."""
    # py_runtime.rs already imports HashMap, HashSet, VecDeque, etc.
    # Never re-emit them to avoid "defined multiple times" compile errors.
    return []


def emit_rs_module(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a complete Rust source file from an EAST3 document.

    Args:
        east3_doc: linked EAST3 JSON dict with meta.linked_program_v1.

    Returns:
        Rust source code string, or empty string if the module should be skipped.
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

    # Load runtime mapping
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "rs" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Skip runtime modules
    if should_skip_module(module_id, mapping):
        return ""

    ctx = RsEmitContext(
        module_id=module_id,
        source_path=_str(east3_doc, "source_path"),
        is_entry=_bool(emit_ctx_meta, "is_entry") if emit_ctx_meta else False,
        mapping=mapping,
    )

    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")

    # Collect runtime imports
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)

    # Collect module private symbols
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("FunctionDef", "ClassDef"):
            name = _str(stmt, "name")
            if name.startswith("_"):
                ctx.module_private_symbols.add(name)
        elif kind in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            if isinstance(target, dict):
                name2 = _str(target, "id")
                if name2.startswith("_"):
                    ctx.module_private_symbols.add(name2)

    # First pass: collect class/function info
    _first_pass(ctx, body)

    # Collect import alias modules
    ctx.import_alias_modules = build_import_alias_map(meta)

    # Start emitting
    lines: list[str] = ctx.lines

    # Emit use statements
    for use_stmt in _collect_uses(ctx):
        lines.append(use_stmt)

    # Include runtime header
    if ctx.is_entry:
        lines.append("include!(\"py_runtime.rs\");")
        lines.append("include!(\"pytra_built_in_type_id_table.rs\");")
        # Include std module files for any imported modules that have a native .rs file
        _STD_MODULE_FILES: dict[str, str] = {
            "pytra.std.math": "math_native.rs",
            "pytra.std.time": "time_native.rs",
            "math": "math_native.rs",
            "time": "time_native.rs",
        }
        for alias, mod_id in ctx.import_alias_modules.items():
            rs_file = _STD_MODULE_FILES.get(mod_id, "")
            if rs_file == "":
                # Try prefix match
                for prefix, rs_f in _STD_MODULE_FILES.items():
                    if mod_id.startswith(prefix):
                        rs_file = rs_f
                        break
            if rs_file == "":
                # Try alias itself (e.g. alias == "math")
                rs_file = _STD_MODULE_FILES.get(alias, "")
            if rs_file != "":
                inc = "include!(\"" + rs_file + "\");"
                if inc not in lines:
                    lines.append(inc)
    lines.append("")

    # Emit body
    _emit_module_body(ctx, body)

    # Emit main_guard as fn main()
    if ctx.is_entry:
        _emit_blank(ctx)
        _emit(ctx, "fn main() {")
        ctx.indent_level += 1
        if len(main_guard) > 0:
            prev_declared = set(ctx.declared_vars)
            ctx.declared_vars = set()
            _emit_body(ctx, main_guard)
            ctx.declared_vars = prev_declared
        ctx.indent_level -= 1
        _emit(ctx, "}")

    return "\n".join(lines).rstrip() + "\n"
