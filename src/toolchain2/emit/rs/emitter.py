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
    set_mapping_types,
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
    # Classes that are base classes of other classes (used as function parameter types via dyn trait)
    parent_class_names: set[str] = field(default_factory=set)
    # Dense type IDs from linked manifest type_id_resolved_v1: {fqcn → dense_tid}
    class_type_ids: dict[str, int] = field(default_factory=dict)
    # Type info table from linked manifest type_info_table_v1: {name → {id, entry, exit}}
    class_type_info_table: dict[str, dict[str, int]] = field(default_factory=dict)
    # Name of variable holding the caught exception message inside a catch handler (for bare raise)
    catch_err_msg_var: str = ""


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
        if kind in ("Expr", "Return", "Assign", "AnnAssign", "Pass", "Raise", "Try", "comment", "blank", "If", "While"):
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
    has_float_body_cast = False
    for c in _list(node, "casts"):
        if isinstance(c, dict) and _str(c, "on") == "body" and _str(c, "to") in ("float64", "float32", "float"):
            has_float_body_cast = True
            break
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
    # Use declared var type (not narrowed type) for operand type checks — isinstance guards narrow
    # the resolved_type but the Rust variable is still Box<dyn Any> if originally a union type
    def _orig_type(nt: str, n: JsonVal) -> str:
        if isinstance(n, dict) and _str(n, "kind") == "Name":
            vt = ctx.var_types.get(_str(n, "id"), "")
            if vt != "":
                return vt
        return nt
    left_type_orig = _orig_type(left_type, left_node)
    right_type_orig = _orig_type(right_type, right_node)

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
    op_map: dict[str, str] = {}
    op_map["Add"] = "+"
    op_map["Sub"] = "-"
    op_map["Mult"] = "*"
    op_map["Div"] = "/"
    op_map["FloorDiv"] = "/"
    op_map["Mod"] = "%"
    op_map["BitAnd"] = "&"
    op_map["BitOr"] = "|"
    op_map["BitXor"] = "^"
    op_map["LShift"] = "<<"
    op_map["RShift"] = ">>"
    op_map["Pow"] = ".pow"
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
    # Cannot do arithmetic on Box<dyn Any> — use original declared type, not narrowed type
    left_rs = _rs_type_for_context(ctx, left_type_orig) if left_type_orig else ""
    right_rs = _rs_type_for_context(ctx, right_type_orig) if right_type_orig else ""
    if left_rs == "Box<dyn std::any::Any>" or right_rs == "Box<dyn std::any::Any>":
        # If EAST3 narrowed the type (e.g., inside isinstance guard), use downcast.
        # Also use the BinOp's own resolved_type as fallback (e.g., closure calls with unknown operands).
        _ANY_DOWNCAST_ARITH: dict[str, str] = {}
        _ANY_DOWNCAST_ARITH["int64"] = "i64"
        _ANY_DOWNCAST_ARITH["int32"] = "i32"
        _ANY_DOWNCAST_ARITH["float64"] = "f64"
        _ANY_DOWNCAST_ARITH["float32"] = "f32"
        _ANY_DOWNCAST_ARITH["bool"] = "bool"
        _ANY_DOWNCAST_ARITH["uint64"] = "u64"
        _ANY_DOWNCAST_ARITH["uint32"] = "u32"
        l_narrow = _ANY_DOWNCAST_ARITH.get(left_type, "")
        r_narrow = _ANY_DOWNCAST_ARITH.get(right_type, "")
        # Fallback: use the BinOp result type or the other operand's narrowed type
        # to infer the downcast target — but only when the operand is actually a
        # union type (contains "|"), not when it is merely "unknown".
        result_narrow = _ANY_DOWNCAST_ARITH.get(resolved_type, "")
        _is_union = lambda t: "|" in t and t != "unknown"
        if l_narrow == "" and left_rs == "Box<dyn std::any::Any>" and _is_union(left_type_orig):
            l_narrow = r_narrow if r_narrow != "" else result_narrow
        if r_narrow == "" and right_rs == "Box<dyn std::any::Any>" and _is_union(right_type_orig):
            r_narrow = l_narrow if l_narrow != "" else result_narrow
        def _downcast_expr(expr: str, narrow: str, is_any: bool) -> str:
            if not is_any or narrow == "":
                return expr
            zero = "0" if narrow not in ("f64", "f32") else "0.0"
            return expr + ".downcast_ref::<" + narrow + ">().copied().unwrap_or(" + zero + ")"
        l_any = left_rs == "Box<dyn std::any::Any>"
        r_any = right_rs == "Box<dyn std::any::Any>"
        if (l_narrow != "" or not l_any) and (r_narrow != "" or not r_any):
            l_cast = _downcast_expr(left, l_narrow, l_any)
            r_cast = _downcast_expr(right, r_narrow, r_any)
            return "(" + l_cast + " " + rs_op + " " + r_cast + ")"
        return 'todo!("Box<dyn Any> arithmetic: ' + op + '")'
    return "(" + left + " " + rs_op + " " + right + ")"


def _emit_unaryop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    op_map: dict[str, str] = {}
    op_map["Not"] = "!"
    op_map["USub"] = "-"
    op_map["UAdd"] = "+"
    op_map["Invert"] = "!"
    rs_op = op_map.get(op, op)
    return "(" + rs_op + operand + ")"


def _emit_compare(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    left = _emit_expr(ctx, left_node)
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return left
    op_map: dict[str, str] = {}
    op_map["Eq"] = "=="
    op_map["NotEq"] = "!="
    op_map["Lt"] = "<"
    op_map["LtE"] = "<="
    op_map["Gt"] = ">"
    op_map["GtE"] = ">="
    op_map["Is"] = "=="
    op_map["IsNot"] = "!="
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
                left_is_optional = "|None" in left_type or "Optional[" in left_type
                if not left_is_optional:
                    left_is_optional = "| None" in left_type
                right_is_optional = "|None" in right_type or "Optional[" in right_type
                if not right_is_optional:
                    right_is_optional = "| None" in right_type
                # Which side is the Option<T>?
                option_side = current_left if right == "None" else right
                if left_is_optional or right_is_optional:
                    # Use is_none()/is_some() for Option<T> comparisons to avoid type annotation issues
                    if rs_op == "==":
                        parts.append(option_side + ".is_none()")
                    else:
                        parts.append(option_side + ".is_some()")
                elif not left_is_optional and not right_is_optional and right == "None":
                    # Check if the type is PyAny enum (object/Any/Obj → PyAny enum)
                    left_is_pyany = left_type in ("object", "Any", "Obj") or left_type == ""
                    if left_is_pyany:
                        if rs_op == "==":
                            parts.append("matches!(" + option_side + ", PyAny::None)")
                        else:
                            parts.append("!matches!(" + option_side + ", PyAny::None)")
                    else:
                        # Non-optional, non-Any type compared to None: always not-None
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


def _emit_isinstance(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit an EAST3 IsInstance node as a Rust type check."""
    val_node = node.get("value")
    expected_node = node.get("expected_type_id")
    val_str = _emit_expr(ctx, val_node)
    val_rt = _str(val_node, "resolved_type") if isinstance(val_node, dict) else ""
    expected_id = _str(expected_node, "id") if isinstance(expected_node, dict) else ""

    # Normalize PYTRA_TID_* constants (used by C++ backend) to type names
    _PYTRA_TID_MAP: dict[str, str] = {}
    _PYTRA_TID_MAP["PYTRA_TID_INT"] = "int64"
    _PYTRA_TID_MAP["PYTRA_TID_FLOAT"] = "float64"
    _PYTRA_TID_MAP["PYTRA_TID_BOOL"] = "bool"
    _PYTRA_TID_MAP["PYTRA_TID_STR"] = "str"
    _PYTRA_TID_MAP["PYTRA_TID_LIST"] = "list"
    _PYTRA_TID_MAP["PYTRA_TID_DICT"] = "dict"
    _PYTRA_TID_MAP["PYTRA_TID_SET"] = "set"
    _PYTRA_TID_MAP["PYTRA_TID_NONE"] = "None"
    _PYTRA_TID_MAP["PYTRA_TID_BYTES"] = "bytes"
    _PYTRA_TID_MAP["PYTRA_TID_TUPLE"] = "tuple"
    if expected_id in _PYTRA_TID_MAP:
        expected_id = _PYTRA_TID_MAP[expected_id]

    # Union types (A | B) → Box<dyn Any>; object/Any/Obj/JsonVal → PyAny enum
    is_union_val = "|" in val_rt
    is_pyany_val = val_rt in ("object", "Any", "Obj", "JsonVal") and not is_union_val
    is_boxany_val = val_rt in ("unknown",) or is_union_val or val_rt == ""
    is_any_val = is_pyany_val or is_boxany_val

    if is_any_val:
        if is_pyany_val:
            # val_rt is object/Any/Obj → PyAny enum → use matches! or type-id check
            _ISINSTANCE_PYANY: dict[str, str] = {}
            _ISINSTANCE_PYANY["int64"] = "PyAny::Int(_)"
            _ISINSTANCE_PYANY["int"] = "PyAny::Int(_)"
            _ISINSTANCE_PYANY["float64"] = "PyAny::Float(_)"
            _ISINSTANCE_PYANY["float"] = "PyAny::Float(_)"
            _ISINSTANCE_PYANY["bool"] = "PyAny::Bool(_)"
            _ISINSTANCE_PYANY["str"] = "PyAny::Str(_)"
            _ISINSTANCE_PYANY["dict"] = "PyAny::Dict(_)"
            _ISINSTANCE_PYANY["list"] = "PyAny::List(_)"
            _ISINSTANCE_PYANY["None"] = "PyAny::None"
            pyany_pattern = _ISINSTANCE_PYANY.get(expected_id, "")
            if pyany_pattern != "":
                return "matches!(" + val_str + ", " + pyany_pattern + ")"
            # User-defined class: encoded as PyAny::Int(type_id) — check via py_is_subtype
            if expected_id in ctx.class_names:
                tid_const = ctx.module_prefix.upper() + safe_rs_ident(expected_id).upper() + "_TID"
                return ("(if let PyAny::Int(__tid) = &" + val_str +
                        " { py_is_subtype(*__tid, " + tid_const + ") } else { false })")
            return "false"
        # For Box<dyn Any> (union types) — use downcast_ref
        ref_val = "&" + val_str if not val_str.startswith("&") else val_str
        _ISINSTANCE_DOWNCAST: dict[str, str] = {}
        _ISINSTANCE_DOWNCAST["int64"] = "i64"
        _ISINSTANCE_DOWNCAST["int32"] = "i32"
        _ISINSTANCE_DOWNCAST["int16"] = "i16"
        _ISINSTANCE_DOWNCAST["int8"] = "i8"
        _ISINSTANCE_DOWNCAST["uint64"] = "u64"
        _ISINSTANCE_DOWNCAST["uint32"] = "u32"
        _ISINSTANCE_DOWNCAST["uint16"] = "u16"
        _ISINSTANCE_DOWNCAST["uint8"] = "u8"
        _ISINSTANCE_DOWNCAST["float64"] = "f64"
        _ISINSTANCE_DOWNCAST["float32"] = "f32"
        _ISINSTANCE_DOWNCAST["bool"] = "bool"
        _ISINSTANCE_DOWNCAST["str"] = "String"
        rust_type = _ISINSTANCE_DOWNCAST.get(expected_id, "")
        if rust_type == "":
            # User-defined class or unknown: check via PyRuntimeTypeId downcast
            if expected_id in ctx.class_names:
                return "(" + ref_val + ").downcast_ref::<" + expected_id + ">().is_some()"
            # Unknown type — fallback to false
            return "false"
        return "(" + ref_val + ").downcast_ref::<" + rust_type + ">().is_some()"

    # Value has a known concrete type — static isinstance always true/false
    # e.g., isinstance(x: int64, int) → true, isinstance(x: list[str], list) → true
    _TYPE_COMPAT: dict[str, list[str]] = {}
    _TYPE_COMPAT["int64"] = ["int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"]
    _TYPE_COMPAT["int32"] = ["int64", "int32"]
    _TYPE_COMPAT["int16"] = ["int64", "int16"]
    _TYPE_COMPAT["int8"] = ["int64", "int8"]
    _TYPE_COMPAT["float64"] = ["float64", "float32"]
    _TYPE_COMPAT["float32"] = ["float64", "float32"]
    _TYPE_COMPAT["bool"] = ["bool"]
    _TYPE_COMPAT["str"] = ["str"]
    _TYPE_COMPAT["list"] = ["list"]
    _TYPE_COMPAT["dict"] = ["dict"]
    _TYPE_COMPAT["set"] = ["set"]
    # Direct match
    if val_rt == expected_id:
        return "true"
    # Generic list/dict/set compatibility: list[str] isa list, etc.
    if expected_id in ("list", "dict", "set") and val_rt.startswith(expected_id + "["):
        return "true"
    # Numeric type aliases: int → int64
    _NUMERIC: dict[str, str] = {}
    _NUMERIC["int"] = "int64"
    _NUMERIC["float"] = "float64"
    mapped_expected = _NUMERIC.get(expected_id, expected_id)
    compat = _TYPE_COMPAT.get(val_rt, [val_rt])
    if mapped_expected in compat or expected_id in compat:
        return "true"
    return "false"


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
    # type(x).__name__ → static class name string when type is known at compile time
    if attr == "__name__" and isinstance(obj_node, dict) and _str(obj_node, "kind") == "Call":
        call_func = obj_node.get("func")
        if isinstance(call_func, dict) and _str(call_func, "id") == "type":
            call_args = _list(obj_node, "args")
            if len(call_args) >= 1:
                arg = call_args[0]
                arg_rt = _str(arg, "resolved_type") if isinstance(arg, dict) else ""
                if arg_rt == "" and isinstance(arg, dict) and _str(arg, "kind") == "Name":
                    arg_rt = ctx.var_types.get(_str(arg, "id"), "")
                if arg_rt in ctx.class_names:
                    return '"' + arg_rt + '".to_string()'
    # Module attribute (e.g. math.pi, env.target) → use just the attr name (resolved to runtime)
    if obj_type == "module" or obj_id in ctx.import_alias_modules:
        runtime_symbol = _str(node, "runtime_symbol") or attr
        # First try qualified name (alias.attr) in mapping.calls — handles "env.target": "\"rs\""
        qualified = obj_id + "." + attr if obj_id != "" else ""
        if qualified in ctx.mapping.calls:
            return ctx.mapping.calls[qualified]
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
    # PyPath string fields must be cloned when accessed (String is not Copy)
    if obj_type == "Path" and attr in ("name", "stem", "suffix"):
        return obj + "." + safe_rs_ident(attr) + ".clone()"
    return obj + "." + safe_rs_ident(attr)


def _expr_to_pyany(expr: str, inner_type: str) -> str:
    """Wrap a rendered expression in the appropriate PyAny variant."""
    if inner_type in ("int64", "int"):
        return "PyAny::Int(" + expr + ")"
    if inner_type in ("float64", "float32", "float"):
        return "PyAny::Float(" + expr + " as f64)"
    if inner_type == "bool":
        return "PyAny::Bool(" + expr + ")"
    if inner_type == "str":
        return "PyAny::Str(" + expr + ")"
    if inner_type == "None" or expr == "None":
        return "PyAny::None"
    # Fallback: for unknown types or already-wrapped exprs
    return expr


def _emit_dict_as_btree_pyany(ctx: "RsEmitContext", node: dict[str, JsonVal]) -> str:
    """Emit a Dict EAST3 node as PyAny::Dict(BTreeMap::from([...]))."""
    entries = _list(node, "entries")
    if entries:
        keys: list[JsonVal] = [e.get("key") for e in entries if isinstance(e, dict)]
        values: list[JsonVal] = [e.get("value") for e in entries if isinstance(e, dict)]
    else:
        keys = _list(node, "keys")
        values = _list(node, "values")
    if len(keys) == 0:
        return "PyAny::Dict(BTreeMap::new())"
    pairs: list[str] = []
    for i, key in enumerate(keys):
        k = _emit_expr(ctx, key)
        val_node = values[i] if i < len(values) else None
        val_rt = _str(val_node, "resolved_type") if isinstance(val_node, dict) else ""
        val_kind = _str(val_node, "kind") if isinstance(val_node, dict) else ""
        if val_kind == "Dict":
            v = _emit_dict_as_btree_pyany(ctx, val_node)
        else:
            v = _emit_expr(ctx, val_node) if val_node is not None else "PyAny::None"
            v = _expr_to_pyany(v, val_rt)
        pairs.append("(" + k + ", " + v + ")")
    return "PyAny::Dict(BTreeMap::from([" + ", ".join(pairs) + "]))"


def _emit_list_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    resolved_type = _str(node, "resolved_type")
    elem_type = ""
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        elem_type = rs_type(resolved_type[5:-1])
    need_box_elem = elem_type == "Box<dyn std::any::Any>"
    need_pyany_elem = elem_type == "PyAny"
    need_option_elem = elem_type.startswith("Option<")
    rendered_elems_raw = [(e, _emit_expr(ctx, e)) for e in elements]
    if need_box_elem:
        rendered_elems = [
            e_str if e_str.startswith("Box::new(") else "Box::new(" + e_str + ") as Box<dyn std::any::Any>"
            for _, e_str in rendered_elems_raw
        ]
    elif need_pyany_elem:
        rendered_elems = []
        for e_node, e_str in rendered_elems_raw:
            e_rt = _str(e_node, "resolved_type") if isinstance(e_node, dict) else ""
            rendered_elems.append(_expr_to_pyany(e_str, e_rt))
    elif need_option_elem:
        rendered_elems = []
        for e_node, e_str in rendered_elems_raw:
            if e_str == "None":
                rendered_elems.append(e_str)
            else:
                e_rt = _str(e_node, "resolved_type") if isinstance(e_node, dict) else ""
                if "None" not in e_rt and not e_rt.startswith("Option"):
                    rendered_elems.append("Some(" + e_str + ")")
                else:
                    rendered_elems.append(e_str)
    else:
        rendered_elems = [e_str for _, e_str in rendered_elems_raw]
    if len(rendered_elems) == 0:
        if elem_type != "":
            return "PyList::<" + elem_type + ">::new()"
        return "PyList::new()"
    elems_str = ", ".join(rendered_elems)
    if elem_type != "":
        return "PyList::<" + elem_type + ">::from_vec(vec![" + elems_str + "])"
    return "PyList::from_vec(vec![" + elems_str + "])"


def _emit_dict_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    # EAST3 uses "entries" (list of {key, value} dicts); fall back to separate keys/values
    entries = _list(node, "entries")
    keys: list[JsonVal]
    values: list[JsonVal]
    if entries:
        keys = [e.get("key") for e in entries if isinstance(e, dict)]
        values = [e.get("value") for e in entries if isinstance(e, dict)]
    else:
        keys = _list(node, "keys")
        values = _list(node, "values")
    resolved_type = _str(node, "resolved_type")
    k_type = "String"
    v_type = "PyAny"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            k_type = rs_type(parts[0])
            v_type = rs_type(parts[1])
    if len(keys) == 0:
        return "HashMap::<" + k_type + ", " + v_type + ">::new()"
    need_box_v = v_type == "Box<dyn std::any::Any>"
    need_pyany_v = v_type == "PyAny"
    need_option_v = v_type.startswith("Option<")
    pairs: list[str] = []
    for i, key in enumerate(keys):
        k = _emit_expr(ctx, key)
        val_node = values[i] if i < len(values) else None
        v = _emit_expr(ctx, val_node) if val_node is not None else "Default::default()"
        if need_box_v and not v.startswith("Box::new("):
            v = "Box::new(" + v + ") as Box<dyn std::any::Any>"
        elif need_pyany_v:
            val_rt = _str(val_node, "resolved_type") if isinstance(val_node, dict) else ""
            val_kind = _str(val_node, "kind") if isinstance(val_node, dict) else ""
            if val_kind == "Dict":
                v = _emit_dict_as_btree_pyany(ctx, val_node)
            else:
                v = _expr_to_pyany(v, val_rt)
        elif need_option_v and v != "None":
            # Wrap non-None values with Some(...) unless already Optional type
            val_rt = _str(val_node, "resolved_type") if isinstance(val_node, dict) else ""
            if "None" not in val_rt and not val_rt.startswith("Option"):
                v = "Some(" + v + ")"
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
    # If the tuple resolves to a PyList type (homogeneous), emit PyList::from_vec(vec![...])
    resolved_type = _str(node, "resolved_type")
    if resolved_type.startswith("tuple["):
        rt = _rs_type_for_context(ctx, resolved_type)
        if rt.startswith("PyList<"):
            # Use turbofish syntax: PyList::<T>::from_vec(...)
            inner_t = rt[7:-1]  # strip "PyList<" and ">"
            return "PyList::<" + inner_t + ">::from_vec(vec![" + ", ".join(rendered) + "])"
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
            # Handle negative indices: lo = if lo < 0 { max(0, len+lo) } else { lo }
            lo_safe = ("(let __loi = (" + lo + ") as i64; if __loi < 0 { (__s.len() as i64 + __loi).max(0) as usize } else { __loi as usize })"
                       if lo != "0" else "0")
            # Simpler: always use i64 arithmetic
            lo_expr = "({ let __loi = (" + lo + ") as i64; if __loi < 0 { (__s.len() as i64 + __loi).max(0) as usize } else { __loi as usize } })" if lo != "0" else "0"
            return "{ let __s = " + ref_obj + "; let __lo = " + lo_expr + "; let __hi = ((" + hi_raw + ") as usize).min(__s.len()); __s[__lo..__hi].to_string() }"
        # Default slice
        return obj + "[(" + lo + " as usize)..(" + hi_raw + " as usize)]"

    idx = _emit_expr(ctx, slice_node)
    # Tuple indexing (both "tuple" and "tuple[...]")
    if obj_type == "tuple" or obj_type.startswith("tuple["):
        tuple_rs = _rs_type_for_context(ctx, obj_type)
        if tuple_rs.startswith("PyList<"):
            # Homogeneous tuple as PyList<T> → .get() like list
            return obj + ".get(" + idx + ")"
        # Heterogeneous tuple as Rust tuple → .N notation
        if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Constant":
            val = slice_node.get("value")
            if isinstance(val, int) and val >= 0:
                return obj + "." + str(val)
        # Non-literal index into tuple: fallback to usize cast
        return obj + "[" + idx + " as usize]"
    if obj_type.startswith("list[") or obj_type == "list" or obj_type in ("bytes", "bytearray"):
        return obj + ".get(" + idx + ")"
    if obj_type.startswith("dict[") or obj_type == "dict":
        subscript_expr = obj + "[&" + idx + "]"
        # For dict[K, PyAny] (non-Copy value), subscript moves value — need .clone()
        if obj_type.startswith("dict[") and obj_type.endswith("]"):
            _inner = obj_type[5:-1]
            _parts = _split_generic_args(_inner)
            if len(_parts) == 2 and rs_type(_parts[1]) == "PyAny":
                subscript_expr = subscript_expr + ".clone()"
        return subscript_expr
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


def _box_target_is_any(node: dict[str, JsonVal]) -> bool:
    """Return True if the Box node's bridge_lane_v1 target dynamic_name is 'Any' or 'Obj'."""
    lane = node.get("bridge_lane_v1")
    if not isinstance(lane, dict):
        return False
    target = lane.get("target")
    if not isinstance(target, dict):
        return False
    dname = target.get("dynamic_name")
    return dname in ("Any", "Obj")


def _emit_box(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit a Box node (boxing a value for dynamic dispatch)."""
    inner = node.get("value")
    outer_rt = _str(node, "resolved_type")
    # All of object/Any/Obj → PyAny enum
    target_is_pyany = outer_rt in ("object", "Any", "Obj")
    # If inner is a None constant, emit PyAny::None
    if isinstance(inner, dict) and _str(inner, "kind") == "Constant" and inner.get("value") is None:
        if target_is_pyany:
            return "PyAny::None"
        return "Box::new(()) as Box<dyn std::any::Any>"
    # If the Box has a more general resolved_type, use it for container literals
    if isinstance(inner, dict) and outer_rt != "" and outer_rt != _str(inner, "resolved_type"):
        inner_kind = _str(inner, "kind")
        if inner_kind == "Dict":
            if target_is_pyany:
                # Box<object/Any/Obj>(dict) → PyAny::Dict(BTreeMap::from([...]))
                return _emit_dict_as_btree_pyany(ctx, inner)
            # Temporarily override inner resolved_type for dict literal
            inner_copy = dict(inner)
            inner_copy["resolved_type"] = outer_rt
            return _emit_dict_literal(ctx, inner_copy)
        if inner_kind == "List":
            # Temporarily override inner resolved_type for list literal (e.g. list[Any])
            inner_copy = dict(inner)
            inner_copy["resolved_type"] = outer_rt
            return _emit_list_literal(ctx, inner_copy)
        # PyAny enum wrapping for object/Any/Obj outer types
        if target_is_pyany:
            inner_rt = _str(inner, "resolved_type")
            rendered_inner = _emit_expr(ctx, inner)
            if inner_rt in ("int64", "int", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"):
                return "PyAny::Int(" + rendered_inner + " as i64)"
            if inner_rt in ("float64", "float32", "float"):
                return "PyAny::Float(" + rendered_inner + " as f64)"
            if inner_rt == "bool":
                return "PyAny::Bool(" + rendered_inner + ")"
            if inner_rt == "str":
                return "PyAny::Str(" + rendered_inner + ")"
            if inner_rt in ctx.class_names and inner_rt not in ctx.enum_bases:
                # User class → encode runtime type ID in PyAny::Int for isinstance checks
                return "PyAny::Int(" + rendered_inner + ".py_runtime_type_id())"
            # Fallback: for unknown/complex types, return as-is
            return rendered_inner
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

    # Handle zip(a, b) before runtime_call resolution: zip produces list of tuples
    if runtime_call in ("zip", "") and not func_is_method and len(args) == 2:
        fn_id = _str(func, "id") if isinstance(func, dict) else ""
        if fn_id == "zip" or runtime_call == "zip":
            a0 = _emit_call_arg(ctx, args[0])
            a1 = _emit_call_arg(ctx, args[1])
            t0 = _str(args[0], "resolved_type") if isinstance(args[0], dict) else ""
            t1 = _str(args[1], "resolved_type") if isinstance(args[1], dict) else ""
            elem0 = rs_type(t0[5:-1]) if t0.startswith("list[") and t0.endswith("]") else "f64"
            elem1 = rs_type(t1[5:-1]) if t1.startswith("list[") and t1.endswith("]") else "f64"
            return ("PyList::<(" + elem0 + ", " + elem1 + ")>::from_vec("
                    + a0 + ".iter_snapshot().into_iter().zip(" + a1 + ".iter_snapshot().into_iter()).collect())")

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
        # Handle sum() specially — emit as .iter_snapshot().into_iter().sum()
        if builtin_name == "sum" and len(args) == 1:
            arg_expr = _emit_call_arg(ctx, args[0])
            ret_type = _str(node, "resolved_type")
            rs_ret = rs_type(ret_type) if ret_type not in ("", "unknown") else "f64"
            return arg_expr + ".iter_snapshot().into_iter().sum::<" + rs_ret + ">()"
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

    # deque() constructor → deque::new() (Pytra stdlib struct)
    if func_name == "deque":
        return "deque::new()"

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

    # zip(a, b) → produce PyList of tuples; rendered as list of (a[i], b[i]) pairs
    if func_name == "zip" and len(args) == 2:
        a0 = _emit_call_arg(ctx, args[0])
        a1 = _emit_call_arg(ctx, args[1])
        # Determine element types
        t0 = _str(args[0], "resolved_type") if isinstance(args[0], dict) else ""
        t1 = _str(args[1], "resolved_type") if isinstance(args[1], dict) else ""
        elem0 = rs_type(t0[5:-1]) if t0.startswith("list[") and t0.endswith("]") else "f64"
        elem1 = rs_type(t1[5:-1]) if t1.startswith("list[") and t1.endswith("]") else "f64"
        return ("PyList::<(" + elem0 + ", " + elem1 + ")>::from_vec("
                + a0 + ".iter_snapshot().into_iter().zip(" + a1 + ".iter_snapshot().into_iter()).collect())")

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
        # Wrap plain closures/fn items in Box::new() when passing to Box<dyn Fn> parameters
        _is_callable_type = lambda t: t in ("Callable", "callable") or t.startswith("callable[") or t.startswith("Callable[")
        if _is_callable_type(resolved) and _is_callable_type(call_arg_type):
            inner_expr = _emit_expr(ctx, arg)
            return "Box::new(" + inner_expr + ")"
        # Box values when passing to Box<dyn Any> parameter.
        # Only applies for union-typed parameters (e.g. Scalar = int | float) because those
        # become Box<dyn Any> in Rust. Simple object/Any/Obj annotations use generics in Rust.
        if call_arg_type != "" and "|" in call_arg_type and resolved not in ("object", "Any", "Obj", "unknown", ""):
            call_arg_rs = _rs_type_for_context(ctx, call_arg_type)
            if call_arg_rs == "Box<dyn std::any::Any>":
                inner_expr = _emit_expr(ctx, arg)
                if resolved in ctx.class_names and resolved not in ctx.enum_bases:
                    return "Box::new(" + inner_expr + ".clone()) as Box<dyn std::any::Any>"
                return "Box::new(" + inner_expr + ") as Box<dyn std::any::Any>"
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


def _emit_runtime_call_arg(ctx: RsEmitContext, arg: JsonVal) -> str:
    """Emit a call argument for a runtime function (py_runtime.rs generics — no primitive boxing)."""
    if isinstance(arg, dict) and _str(arg, "kind") == "Box":
        outer_rt = _str(arg, "resolved_type")
        inner = arg.get("value")
        if isinstance(inner, dict) and outer_rt in ("object", "Any", "Obj"):
            inner_rt = _str(inner, "resolved_type")
            # Runtime functions use generics (PyStringify etc.), not Box<dyn Any>.
            # Don't box primitive/str values; let Rust generic inference handle them.
            if inner_rt in ("int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8",
                            "float64", "float32", "bool", "str"):
                return _emit_expr(ctx, inner)
    return _emit_call_arg(ctx, arg)


def _emit_runtime_call(
    ctx: RsEmitContext,
    mapped: str,
    func: JsonVal,
    args: list[JsonVal],
    keywords: list[JsonVal],
    node: dict[str, JsonVal],
) -> str:
    rendered_args = [_emit_runtime_call_arg(ctx, a) for a in args]
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            rendered_args.append(_emit_expr(ctx, kw_val))

    # first_ref_arg adapter: first argument passed as &T (borrow, not move)
    if ctx.mapping.call_adapters.get(mapped, "") == "first_ref_arg" and len(rendered_args) >= 1:
        first = rendered_args[0]
        if not first.startswith("&"):
            first = "&" + first
        rest = rendered_args[1:]
        all_args = [first] + rest
        return mapped + "(" + ", ".join(all_args) + ")"

    # ref_arg adapter: function takes &T — pass by reference, return i64 (Python int)
    if ctx.mapping.call_adapters.get(mapped, "") == "ref_arg" and len(rendered_args) == 1:
        # For deque (std lib struct with __len__ but no PyLen trait), call directly
        if len(args) == 1 and isinstance(args[0], dict) and _str(args[0], "resolved_type") == "deque":
            obj_expr = rendered_args[0]
            return "(" + obj_expr + ".__len__() as i64)"
        arg = rendered_args[0]
        if not arg.startswith("&"):
            arg = "&" + arg
        return mapped + "(" + arg + ") as i64"

    # py_int, py_float, py_str, py_bool, py_str_to_i64 take &T
    if mapped in ("py_int", "py_float", "py_str", "py_bool", "py_str_to_i64", "py_str_to_f64", "py_str_isdigit", "py_str_isalpha", "py_str_isupper", "py_str_islower") and len(rendered_args) == 1:
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

    # multi_arg_print adapter: todo!() arg → emit directly; multiple args → join with space
    if ctx.mapping.call_adapters.get(mapped, "") == "multi_arg_print":
        if len(rendered_args) >= 1 and all(a.startswith("todo!(") for a in rendered_args):
            return rendered_args[0]
        if len(rendered_args) > 1:
            fmt_parts = " ".join(["{}" for _ in rendered_args])
            # Wrap each arg in parens to avoid precedence issues (e.g. `x as i64.py_stringify()`)
            stringify_args = ", ".join("(" + a + ").py_stringify()" for a in rendered_args)
            return mapped + '(format!("' + fmt_parts + '", ' + stringify_args + "))"

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

    # super().method(args) → call parent class method via temp instance with inherited fields
    if isinstance(obj, dict) and _str(obj, "kind") == "Call":
        obj_func = obj.get("func")
        if isinstance(obj_func, dict) and _str(obj_func, "id") in ("super", "py_super"):
            parent = ctx.class_bases.get(ctx.current_class, "")
            if parent != "" and parent in ctx.class_names:
                rendered_args = [_emit_call_arg(ctx, a) for a in args]
                # Build a temporary parent instance that copies inherited fields from self
                parent_fields = ctx.class_fields.get(parent, {})
                if parent_fields:
                    field_inits = ", ".join(
                        safe_rs_ident(f) + ": self." + safe_rs_ident(f) + ".clone()"
                        for f in parent_fields
                    )
                    parent_expr = "{ let mut __p = " + safe_rs_ident(parent) + " { " + field_inits + " }; " + safe_rs_ident(parent) + "::" + safe_rs_ident(method) + "(&mut __p, " + ", ".join(rendered_args) + ") }"
                else:
                    parent_expr = safe_rs_ident(parent) + "::" + safe_rs_ident(method) + "(&mut " + safe_rs_ident(parent) + " {}, " + ", ".join(rendered_args) + ")"
                return parent_expr

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
        # Apply call_adapters for module-qualified calls
        if ctx.mapping.call_adapters.get(resolved_name, "") == "first_ref_arg" and len(rendered_args) >= 1:
            first = rendered_args[0]
            if not first.startswith("&"):
                first = "&" + first
            rendered_args = [first] + rendered_args[1:]
        return resolved_name + "(" + ", ".join(rendered_args) + ")"

    # Check runtime_call for method call
    # Skip runtime_call resolution for typed collection methods — handled below by type dispatch
    _typed_collection_obj = obj_type.startswith("set[") or obj_type == "set"
    if not _typed_collection_obj:
        _typed_collection_obj = obj_type.startswith("list[") or obj_type == "list"
    if not _typed_collection_obj:
        _typed_collection_obj = obj_type.startswith("dict[") or obj_type == "dict"
    if not _typed_collection_obj:
        _typed_collection_obj = obj_type == "deque"
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

    # JsonVal method calls (JsonVal → PyAny, dict-like .get())
    if obj_type == "JsonVal":
        if method == "get":
            key = rendered_args[0] if rendered_args else '""'
            return obj_str + ".pyany_get(&" + key + ")"

    # dict methods
    if obj_type.startswith("dict[") or obj_type == "dict":
        if method == "get":
            # Check if actual variable is dynamic (JsonVal/PyAny) — EAST3 may have narrowed the type
            # but the Rust variable is actually PyAny, needing py_any_as_hashmap conversion
            _actual_rt = (ctx.var_types.get(obj_id, "") or obj_type) if obj_id else obj_type
            _is_dynamic_var = _actual_rt in ("JsonVal", "Any", "object", "Obj")
            if not _is_dynamic_var:
                _is_dynamic_var = "JsonVal" in _actual_rt and "dict[" not in _actual_rt.split("|")[0].strip()[:10]
            if not _is_dynamic_var:
                _is_dynamic_var = "|" in _actual_rt and "JsonVal" in _actual_rt
            if _is_dynamic_var:
                _key = rendered_args[0] if rendered_args else '""'
                _default = rendered_args[1] if len(rendered_args) >= 2 else "PyAny::None"
                _unwrap = "clone().unwrap_or(PyAny::None)" if "|" in _actual_rt else "clone()"
                return "py_any_as_hashmap(" + obj_str + "." + _unwrap + ").get(&" + _key + ").cloned().unwrap_or(" + _default + ")"
            if len(rendered_args) >= 2:
                return obj_str + ".get(&" + rendered_args[0] + ").cloned().unwrap_or(" + rendered_args[1] + ")"
            elif len(rendered_args) == 1:
                # For dict[K, PyAny] return PyAny::None as default instead of Option<PyAny>
                if obj_type.startswith("dict[") and obj_type.endswith("]"):
                    _inner = obj_type[5:-1]
                    _parts = _split_generic_args(_inner)
                    if len(_parts) == 2 and rs_type(_parts[1]) == "PyAny":
                        return obj_str + ".get(&" + rendered_args[0] + ").cloned().unwrap_or(PyAny::None)"
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

    # deque methods — delegate to the deque struct's own methods (mirrors Python API)
    if obj_type == "deque":
        all_args_str = ", ".join(rendered_args)
        return obj_str + "." + safe_rs_ident(method) + "(" + all_args_str + ")"

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
        # Get runtime type ID of an object — sequential TID space
        val = node.get("value")
        value_type = _str(val, "resolved_type") if isinstance(val, dict) else ""
        inner = _emit_expr(ctx, val)
        # For PyAny typed values (object/Any/Obj), type ID is encoded as PyAny::Int(type_id)
        if value_type in ("object", "Any", "Obj"):
            return "(if let PyAny::Int(__tid) = &" + inner + " { *__tid } else { py_runtime_type_id(&" + inner + ") })"
        # For Box<dyn Any> (unknown / union types), use downcast chain to recover TID
        if value_type in ("unknown",) or value_type == "":
            user_cls = _sorted_user_classes_desc(ctx)
            if user_cls:
                ref_inner = "&" + inner if not inner.startswith("&") else inner
                return _emit_obj_type_id_downcast(ctx, ref_inner, user_cls)
        ref_inner = "&" + inner if not inner.startswith("&") else inner
        return "py_runtime_type_id(" + ref_inner + ")"
    if kind == "IsInstance":
        return _emit_isinstance(ctx, node)
    if kind == "Unbox":
        # Unbox: converts a dynamic (Any/object/JsonVal) value to a static type.
        # EAST3 inserts Unbox nodes for isinstance-narrowed JsonVal/Any variables;
        # inner node carries the original (pre-narrowing) storage type.
        inner_node = node.get("value")
        inner_rt = _str(inner_node, "resolved_type") if isinstance(inner_node, dict) else ""
        outer_rt = _str(node, "resolved_type")
        inner_expr = _emit_expr(ctx, inner_node)

        _PYANY = ("Any", "object", "Obj", "JsonVal")
        # Handle Option<X> inner types (e.g. dict[str,JsonVal] | None)
        inner_base_rt = inner_rt
        needs_unwrap = False
        if inner_rt.endswith(" | None") or inner_rt.endswith("|None"):
            inner_base_rt = inner_rt[:-7].strip() if inner_rt.endswith(" | None") else inner_rt[:-5].strip()
            needs_unwrap = True
        inner_base_is_dynamic = inner_base_rt in _PYANY
        is_dynamic_inner = (
            inner_base_is_dynamic
            or "JsonVal" in inner_base_rt
        )
        if is_dynamic_inner and outer_rt not in _PYANY and outer_rt != "":
            # Source expr: unwrap Option if needed, otherwise use directly
            if needs_unwrap:
                if inner_base_is_dynamic:
                    # Option<PyAny> → PyAny
                    src = inner_expr + ".clone().unwrap_or(PyAny::None)"
                else:
                    # Option<ConcreteType> → ConcreteType: already the right type
                    src = inner_expr + ".clone().unwrap_or_default()"
            else:
                src = inner_expr
            if outer_rt.startswith("list[") or outer_rt == "list":
                if needs_unwrap and not inner_base_is_dynamic:
                    # Already PyList — no conversion needed
                    return src
                clone_src = src if needs_unwrap else src + ".clone()"
                return "py_any_as_list(" + clone_src + ")"
            if outer_rt.startswith("dict["):
                if needs_unwrap and not inner_base_is_dynamic:
                    # Already HashMap — no conversion needed
                    return src
                clone_src = src if needs_unwrap else src + ".clone()"
                return "py_any_as_hashmap(" + clone_src + ")"
            if outer_rt == "str":
                return "py_str(&" + src + ")"
            if outer_rt in ("int64", "int", "int32", "int16", "int8",
                            "uint64", "uint32", "uint16", "uint8"):
                return "py_int(&" + src + ")"
            if outer_rt in ("float64", "float32", "float"):
                return "py_float(&" + src + ")"
            if outer_rt == "bool":
                return "py_bool(&" + src + ")"
        # Handle Box<dyn Any> union types (e.g. int64|float64 → int64).
        # When the inner Rust type is Box<dyn Any> (a non-PyAny union type), emit a downcast.
        if not is_dynamic_inner and not needs_unwrap and outer_rt not in _PYANY and outer_rt != "":
            inner_rs = _rs_type_for_context(ctx, inner_base_rt)
            if inner_rs == "Box<dyn std::any::Any>":
                _BOX_ANY_DOWNCAST: dict[str, tuple[str, str]] = {}
                _BOX_ANY_DOWNCAST["int64"] = ("i64", "0")
                _BOX_ANY_DOWNCAST["int32"] = ("i32", "0")
                _BOX_ANY_DOWNCAST["int16"] = ("i16", "0")
                _BOX_ANY_DOWNCAST["int8"] = ("i8", "0")
                _BOX_ANY_DOWNCAST["uint64"] = ("u64", "0")
                _BOX_ANY_DOWNCAST["uint32"] = ("u32", "0")
                _BOX_ANY_DOWNCAST["uint16"] = ("u16", "0")
                _BOX_ANY_DOWNCAST["uint8"] = ("u8", "0")
                _BOX_ANY_DOWNCAST["float64"] = ("f64", "0.0")
                _BOX_ANY_DOWNCAST["float32"] = ("f32", "0.0")
                _BOX_ANY_DOWNCAST["bool"] = ("bool", "false")
                _BOX_ANY_DOWNCAST["str"] = ("String", "String::new()")
                narrow = _BOX_ANY_DOWNCAST.get(outer_rt)
                if narrow is not None:
                    rs_narrow, zero = narrow
                    if rs_narrow == "String":
                        return inner_expr + ".downcast_ref::<String>().cloned().unwrap_or_default()"
                    return inner_expr + ".downcast_ref::<" + rs_narrow + ">().copied().unwrap_or(" + zero + ")"
        return inner_expr
    if kind == "ListComp":
        return _emit_listcomp(ctx, node)
    if kind == "SetComp":
        return _emit_setcomp(ctx, node)
    if kind == "DictComp":
        return _emit_dictcomp(ctx, node)
    # Fallback: use repr if available (emit todo! so it compiles but panics at runtime)
    # Escape { and } since todo! uses them as format specifiers
    repr_str = _str(node, "repr")
    if repr_str != "":
        safe_repr = repr_str.replace('"', "'").replace("{", "{{").replace("}", "}}")
        return "todo!(\"unsupported: " + safe_repr + "\")"
    return "todo!(\"unsupported_expr:" + kind + "\")"


def _emit_comp_generators(ctx: RsEmitContext, generators: list[JsonVal], push_stmt: str) -> str:
    """Emit nested for/if loops for a comprehension, ending with push_stmt."""
    parts: list[str] = []
    close_count = 0
    for gen in generators:
        if not isinstance(gen, dict):
            continue
        target_node = gen.get("target")
        iter_node = gen.get("iter")
        ifs = gen.get("ifs")
        # Build target pattern (support tuple destructuring)
        if isinstance(target_node, dict) and _str(target_node, "kind") == "Tuple":
            # Try "elements" then "elts" (different EAST3 versions)
            tuple_elts = _list(target_node, "elements") or _list(target_node, "elts")
            names = [_str(e, "id") if isinstance(e, dict) else "_" for e in tuple_elts]
            target_name = "(" + ", ".join(names) + ")" if names else "_"
        else:
            target_name = _str(target_node, "id") if isinstance(target_node, dict) else "_"
        iter_expr = _emit_expr(ctx, iter_node)
        iter_type = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
        if iter_type == "str":
            # Iterating over a string yields single-char strings
            iter_str = iter_expr + ".chars().map(|__c| __c.to_string()).collect::<Vec<String>>().into_iter()"
        elif iter_type.startswith("list[tuple["):
            # List of tuples (from zip): iter directly
            iter_str = iter_expr + ".iter_snapshot().into_iter()"
        else:
            iter_str = iter_expr + ".iter_snapshot().into_iter()"
        parts.append("for " + target_name + " in " + iter_str + " {")
        close_count += 1
        if isinstance(ifs, list) and len(ifs) > 0:
            cond_parts: list[str] = []
            for cond in ifs:
                if isinstance(cond, dict):
                    cond_parts.append(_emit_expr(ctx, cond))
            if cond_parts:
                parts.append("if " + " && ".join(cond_parts) + " {")
                close_count += 1
    parts.append(push_stmt)
    for _ in range(close_count):
        parts.append("}")
    return " ".join(parts)


def _emit_listcomp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit list comprehension as a Rust block expression."""
    elt = node.get("elt")
    generators = _list(node, "generators")
    resolved_type = _str(node, "resolved_type")
    elem_type = ""
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        elem_type = rs_type(resolved_type[5:-1])
    elif resolved_type.startswith("PyList<") and resolved_type.endswith(">"):
        elem_type = resolved_type[7:-1]
    decl = "let mut __comp = PyList::<" + elem_type + ">::new();" if elem_type else "let mut __comp = PyList::new();"
    elt_expr = _emit_expr(ctx, elt)
    body = _emit_comp_generators(ctx, generators, "__comp.push(" + elt_expr + ");")
    return "{ " + decl + " " + body + " __comp }"


def _emit_setcomp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit set comprehension as a Rust block expression."""
    elt = node.get("elt")
    generators = _list(node, "generators")
    resolved_type = _str(node, "resolved_type")
    elem_type = ""
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        elem_type = rs_type(resolved_type[4:-1])
    decl = "let mut __comp: HashSet<" + elem_type + "> = HashSet::new();" if elem_type else "let mut __comp = HashSet::new();"
    elt_expr = _emit_expr(ctx, elt)
    body = _emit_comp_generators(ctx, generators, "__comp.insert(" + elt_expr + ");")
    return "{ " + decl + " " + body + " __comp }"


def _emit_dictcomp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit dict comprehension as a Rust block expression."""
    key_node = node.get("key")
    val_node = node.get("value")
    generators = _list(node, "generators")
    resolved_type = _str(node, "resolved_type")
    k_type = ""
    v_type = ""
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        comma = inner.find(",")
        if comma != -1:
            k_type = rs_type(inner[:comma].strip())
            v_type = rs_type(inner[comma + 1:].strip())
    decl = ("let mut __comp: HashMap<" + k_type + ", " + v_type + "> = HashMap::new();"
            if k_type and v_type else "let mut __comp = HashMap::new();")
    key_expr = _emit_expr(ctx, key_node)
    val_expr = _emit_expr(ctx, val_node)
    body = _emit_comp_generators(ctx, generators, "__comp.insert(" + key_expr + ", " + val_expr + ");")
    return "{ " + decl + " " + body + " __comp }"


def _translate_py_format_spec(spec: str) -> str:
    """Translate Python format spec to Rust format spec string (without braces).

    Examples:
      "4d"   -> "4"     (width 4, integer type stripped)
      ".4f"  -> ".4"    (precision 4, float type stripped)
      "10.2f"-> "10.2"  (width 10, precision 2)
      ">10s" -> ">10"   (left-align, string type stripped)
      "02x"  -> "02x"   (hex kept, Rust supports :02x)
      "02X"  -> "02X"   (uppercase hex kept)
      ",d"   -> ""      (comma grouping removed, Rust doesn't support)
      ".1%"  -> ".1"    (percent stripped, value stays unchanged)
      "+d"   -> "+"     (sign kept)
      ""     -> ""
    """
    if spec == "":
        return ""
    # Remove comma grouping (Python ,  → not supported in Rust)
    spec = spec.replace(",", "")
    if spec == "":
        return ""
    # Strip trailing Python type characters that Rust doesn't use
    # Keep: x, X, o, b, e, E (Rust supports these as format types)
    # Strip: d, i, f, F, g, G, s, r, c, n, % (not valid in Rust format strings)
    if spec and spec[-1] in "difFgGsrcn%":
        spec = spec[:-1]
    return spec


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
                    # Escape backslashes first, then braces (for Rust format! string)
                    fmt_parts.append(s.replace("\\", "\\\\").replace("{", "{{").replace("}", "}}"))
            elif v_kind == "FormattedValue":
                raw_spec = v.get("format_spec")
                spec_str = raw_spec if isinstance(raw_spec, str) else ""
                rs_spec = _translate_py_format_spec(spec_str)
                fmt_parts.append("{:" + rs_spec + "}" if rs_spec else "{}")
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
    # If function has no return type (void), drop the return value
    if ctx.current_return_type in ("", "None", "none"):
        _emit(ctx, "return;")
        return
    # Wrap in Some() if returning a non-None value into an Optional return type
    if ctx.current_return_type != "":
        ret_rs = _rs_type_for_context(ctx, ctx.current_return_type)
        val_rt = _str(value, "resolved_type") if isinstance(value, dict) else ""
        if ret_rs.startswith("Option<") and rendered != "None":
            val_is_none = (val_rt in ("None", "none") or rendered == "None")
            # Don't wrap if value is already Optional (e.g., str | None → Option<String>)
            val_is_already_optional = (val_rt.endswith(" | None") or val_rt.endswith("|None"))
            val_rs = rs_type(val_rt) if val_rt != "" else ""
            val_is_option = val_rs.startswith("Option<")
            if not val_is_none and not val_is_already_optional and not val_is_option:
                rendered = "Some(" + rendered + ")"
        elif ret_rs == "Box<dyn std::any::Any>" and val_rt in ctx.class_names and val_rt not in ctx.enum_bases:
            # Returning a class instance as Box<dyn Any> — box and clone
            rendered = "Box::new(" + rendered + ".clone()) as Box<dyn std::any::Any>"
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
    aug_ops: dict[str, str] = {}
    aug_ops["Add"] = "+="
    aug_ops["Sub"] = "-="
    aug_ops["Mult"] = "*="
    aug_ops["Div"] = "/="
    aug_ops["FloorDiv"] = "/="
    aug_ops["Mod"] = "%="
    aug_ops["BitAnd"] = "&="
    aug_ops["BitOr"] = "|="
    aug_ops["BitXor"] = "^="
    aug_ops["LShift"] = "<<="
    aug_ops["RShift"] = ">>="
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
        # Bare raise: re-raise current exception
        if ctx.catch_err_msg_var:
            _emit(ctx, "panic!(\"{}\", " + ctx.catch_err_msg_var + ".clone());")
        else:
            _emit(ctx, 'panic!("re-raised");')
        return
    if isinstance(exc, dict):
        exc_kind = _str(exc, "kind")
        if exc_kind == "Call":
            func_node = exc.get("func")
            func_runtime_mod = _str(func_node, "runtime_module_id") if isinstance(func_node, dict) else ""
            exc_resolved = _str(exc, "resolved_type")
            # User-defined exception (no runtime_module_id, class defined in this module)
            if func_runtime_mod == "" and exc_resolved in ctx.class_names:
                # _emit_expr wraps constructors in Box::new() — we need the raw value for panic_any
                # Emit ClassName::new(args...) without Box wrapper
                exc_args = _list(exc, "args")
                exc_kwargs = _list(exc, "keywords")
                rendered_args = [_emit_expr(ctx, a) for a in exc_args]
                rs_exc_name = safe_rs_ident(exc_resolved)
                raw_call = rs_exc_name + "::new(" + ", ".join(rendered_args) + ")"
                _emit(ctx, "std::panic::panic_any(" + raw_call + ");")
                return
            args = _list(exc, "args")
            if len(args) > 0:
                msg = _emit_expr(ctx, args[0])
                _emit(ctx, "panic!(\"{}\", " + msg + ");")
                return
        msg = _emit_expr(ctx, exc)
        _emit(ctx, "panic!(\"{}\", " + msg + ");")
        return
    _emit(ctx, 'panic!("exception");')


def _body_has_return(stmts: list[JsonVal]) -> bool:
    """Recursively check if any statement in the body has a Return node with a value."""
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        if stmt.get("kind") == "Return":
            val = stmt.get("value")
            if val is not None:
                return True
        for key in ("body", "orelse", "finalbody"):
            sub = stmt.get(key)
            if isinstance(sub, list) and _body_has_return(sub):
                return True
        handlers = stmt.get("handlers")
        if isinstance(handlers, list):
            for h in handlers:
                if isinstance(h, dict):
                    hbody = h.get("body")
                    if isinstance(hbody, list) and _body_has_return(hbody):
                        return True
    return False


def _emit_try(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit try/except/finally using std::panic::catch_unwind."""
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")

    _emit(ctx, "{")
    ctx.indent_level += 1

    if len(handlers) == 0:
        # Only finally: catch, run finally, re-raise if panic
        _emit(ctx, "let __try_result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "}));")
        if finalbody:
            _emit_body(ctx, finalbody)
        _emit(ctx, "if let Err(__try_err) = __try_result { std::panic::resume_unwind(__try_err); }")
    else:
        # Catch and dispatch to handlers
        _emit(ctx, "let __try_result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "}));")
        # If the try body can return a value, use match to propagate Ok result.
        body_has_ret = _body_has_return(body) and ctx.current_return_type not in ("", "None")
        _emit(ctx, "match __try_result {")
        ctx.indent_level += 1
        if body_has_ret:
            _emit(ctx, "Ok(__try_ok) => { return __try_ok; }")
        else:
            _emit(ctx, "Ok(_) => {}")
        _emit(ctx, "Err(ref __catch_err) => {")
        ctx.indent_level += 1
        old_catch_var = ctx.catch_err_msg_var

        # Separate user-defined exception handlers from built-in string handlers
        user_handlers: list[dict[str, JsonVal]] = []
        string_handlers: list[dict[str, JsonVal]] = []
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            type_node = handler.get("type")
            if isinstance(type_node, dict):
                handler_type_id = _str(type_node, "id")
                handler_runtime_mod = _str(type_node, "runtime_module_id")
                # User-defined exception: no runtime_module_id, class in this module
                if handler_runtime_mod == "" and handler_type_id in ctx.class_names:
                    user_handlers.append(handler)
                    continue
            string_handlers.append(handler)

        # Emit user-defined exception handlers first (if any)
        if len(user_handlers) > 0:
            for i, handler in enumerate(user_handlers):
                type_node = handler.get("type")
                handler_type_id = _str(type_node, "id") if isinstance(type_node, dict) else ""
                exc_name = _str(handler, "name")
                handler_body = _list(handler, "body")
                rs_type = safe_rs_ident(handler_type_id)
                if i == 0:
                    _emit(ctx, "if let Some(" + safe_rs_ident(exc_name) + ") = __catch_err.downcast_ref::<" + rs_type + ">() {")
                else:
                    _emit(ctx, "} else if let Some(" + safe_rs_ident(exc_name) + ") = __catch_err.downcast_ref::<" + rs_type + ">() {")
                ctx.indent_level += 1
                ctx.declared_vars.add(exc_name)
                _emit_body(ctx, handler_body)
                ctx.indent_level -= 1
            # Remaining string handlers go in else block
            if len(string_handlers) > 0:
                _emit(ctx, "} else {")
                ctx.indent_level += 1
                _emit(ctx, "let __err_msg: String = if let Some(__s) = __catch_err.downcast_ref::<String>() { __s.clone() } else if let Some(__s) = __catch_err.downcast_ref::<&str>() { __s.to_string() } else { \"exception\".to_string() };")
                ctx.catch_err_msg_var = "__err_msg"
                for handler in string_handlers:
                    exc_name = _str(handler, "name")
                    handler_body = _list(handler, "body")
                    if exc_name != "":
                        _emit(ctx, "let " + safe_rs_ident(exc_name) + " = __err_msg.clone();")
                        ctx.declared_vars.add(exc_name)
                    _emit_body(ctx, handler_body)
                ctx.indent_level -= 1
            _emit(ctx, "}")
        else:
            # Only string handlers (original behavior)
            _emit(ctx, "let __err_msg: String = if let Some(__s) = __catch_err.downcast_ref::<String>() { __s.clone() } else if let Some(__s) = __catch_err.downcast_ref::<&str>() { __s.to_string() } else { \"exception\".to_string() };")
            ctx.catch_err_msg_var = "__err_msg"
            for handler in string_handlers:
                exc_name = _str(handler, "name")
                handler_body = _list(handler, "body")
                if exc_name != "":
                    _emit(ctx, "let " + safe_rs_ident(exc_name) + " = __err_msg.clone();")
                    ctx.declared_vars.add(exc_name)
                _emit_body(ctx, handler_body)

        ctx.catch_err_msg_var = old_catch_var
        ctx.indent_level -= 1
        _emit(ctx, "}")  # close Err arm
        ctx.indent_level -= 1
        _emit(ctx, "}")  # close match
        if finalbody:
            _emit_body(ctx, finalbody)

    ctx.indent_level -= 1
    _emit(ctx, "}")


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

    # Determine step value — handles Constant, int, and UnaryOp(USub, Constant)
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
    elif (isinstance(step, dict) and _str(step, "kind") == "UnaryOp"
          and _str(step, "op") == "USub"):
        operand = step.get("operand")
        if isinstance(operand, dict) and _str(operand, "kind") == "Constant":
            sv2 = operand.get("value")
            if isinstance(sv2, int):
                step_val = -sv2
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
        # Dynamic step — sign unknown at emit time, assume positive (forward range)
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

    # JsonVal / PyAny iteration (treats as list)
    if resolved_type in ("JsonVal", "object", "Any", "Obj"):
        iter_expr = _emit_expr(ctx, iter_node)
        return "py_any_as_list(" + iter_expr + ".clone()).iter_snapshot().into_iter()"

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
    elif kind == "Swap":
        # a, b = b, a → temp swap using a local __swap_tmp variable
        left_node = node.get("left")
        right_node = node.get("right")
        left_name = _str(left_node, "id") if isinstance(left_node, dict) else ""
        right_name = _str(right_node, "id") if isinstance(right_node, dict) else ""
        if left_name != "" and right_name != "":
            safe_l = safe_rs_ident(left_name)
            safe_r = safe_rs_ident(right_name)
            _emit(ctx, "let __swap_tmp = " + safe_l + ".clone();")
            _emit(ctx, safe_l + " = " + safe_r + ".clone();")
            _emit(ctx, safe_r + " = __swap_tmp;")
        else:
            _emit(ctx, "// unsupported Swap: non-Name targets")
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
    arg_usage = _dict(node, "arg_usage")
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
        elif arg_type in ctx.parent_class_names:
            # Parent class used as parameter type → use dyn trait for polymorphism
            rs_arg_type = "Box<dyn " + safe_rs_ident(arg_type) + "Methods>"
        else:
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
        # Add `mut` only if arg_usage says "reassigned" (EAST3 §arg_usage),
        # or if the type is Box<T> (fields may be mutated via &mut self patterns).
        is_reassigned = _str(arg_usage, arg) == "reassigned"
        is_box = rs_arg_type.startswith("Box<")
        mut_prefix = "mut " if (is_reassigned or is_box) else ""
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
        if return_type in ctx.parent_class_names:
            rt = "Box<dyn " + safe_rs_ident(return_type) + "Methods>"
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

    # Emit PyStringify for user-defined classes (needed for str(instance))
    if name not in ctx.enum_bases:
        _emit_blank(ctx)
        _emit(ctx, "impl PyStringify for " + rs_name + " {")
        ctx.indent_level += 1
        _emit(ctx, "fn py_stringify(&self) -> String { format!(\"{:?}\", self) }")
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # If this class is a parent class, emit a <Name>Methods trait and impl for it
    if name in ctx.parent_class_names:
        _emit_parent_class_methods_trait(ctx, name)
        _emit_parent_class_methods_impl(ctx, name)

    # If this class has ancestors in parent_class_names, emit impl <Ancestor>Methods for this class
    ancestor = ctx.class_bases.get(name, "")
    while ancestor != "" and ancestor in ctx.class_names:
        if ancestor in ctx.parent_class_names:
            _emit_parent_class_methods_impl(ctx, name, as_type=ancestor)
        ancestor = ctx.class_bases.get(ancestor, "")


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
    """Build the TID const name matching _fqcn_to_tid_const: {MODULE_UPPER}_{CLASS_SNAKE_UPPER}_TID."""
    import re
    # Use module_id (dotted path) to match the FQCN used in the manifest type_id_table
    if ctx.module_id != "":
        fqcn = ctx.module_id + "." + class_name
    else:
        import os
        source_path = ctx.source_path
        stem = os.path.splitext(os.path.basename(source_path))[0] if source_path != "" else "module"
        fqcn = stem + "." + class_name
    # Mirror _fqcn_to_tid_const logic from pytra-cli2.py
    flat = fqcn.replace(".", "_")
    snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", flat)
    snake = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", snake)
    return snake.upper() + "_TID"


def _lookup_class_dense_tid(ctx: RsEmitContext, type_name: str) -> int | None:
    """Look up the dense TID for a user-defined class from class_type_ids.

    Returns None if the type is not a known user class.
    """
    if type_name == "" or type_name in ("object", "Any", "Obj", "unknown"):
        return None
    # Try FQCN lookup
    if ctx.module_id != "":
        fqcn = ctx.module_id + "." + type_name
        if fqcn in ctx.class_type_ids:
            return ctx.class_type_ids[fqcn]
    # Try direct match
    if type_name in ctx.class_type_ids:
        return ctx.class_type_ids[type_name]
    # Try suffix match
    suffix = "." + type_name
    for fqcn, tid in ctx.class_type_ids.items():
        if fqcn.endswith(suffix) and not fqcn.startswith("pytra."):
            return tid
    return None


def _sorted_user_classes_desc(ctx: RsEmitContext) -> list[tuple[str, int]]:
    """Return user-defined class (fqcn, dense_tid) pairs sorted by dense_tid descending.

    Most-specific (leaf) classes have higher dense TIDs, so they come first.
    This is used to generate correct downcast chains (children before parents).
    """
    result: list[tuple[str, int]] = []
    for fqcn, dense_tid in ctx.class_type_ids.items():
        if fqcn.startswith("pytra."):
            continue
        if dense_tid < 1000:
            continue
        result.append((fqcn, dense_tid))
    result.sort(key=lambda kv: kv[1], reverse=True)
    return result


def _emit_obj_type_id_downcast(ctx: RsEmitContext, ref_expr: str, user_cls: list[tuple[str, int]]) -> str:
    """Emit a downcast chain to determine the sequential TID of a Box<dyn Any> value.

    The Box<dyn Any> typically contains a Box<ClassName> (due to double-boxing at call sites),
    so we try downcast_ref::<Box<ClassName>> first, then bare ClassName as fallback.
    Falls back to py_runtime_type_id for primitive types.
    """
    parts: list[str] = []
    for fqcn, _dense in user_cls:
        simple_name = fqcn.rsplit(".", 1)[-1] if "." in fqcn else fqcn
        rs_name = safe_rs_ident(simple_name)
        seq_const = _fqcn_to_tid_const_name(fqcn)
        # Try Box<ClassName> first (double-boxed case: Box<Box<ClassName>> as Box<dyn Any>)
        parts.append(
            "if (" + ref_expr + ").downcast_ref::<Box<" + rs_name + ">>().is_some() || "
            + "(" + ref_expr + ").downcast_ref::<" + rs_name + ">().is_some() "
            + "{ " + seq_const + " }"
        )
    fallback = "py_runtime_type_id(" + ref_expr + ")"
    if not parts:
        return fallback
    chain = " else ".join(parts) + " else { " + fallback + " }"
    return "{ " + chain + " }"


def _emit_parent_class_methods_trait(ctx: RsEmitContext, class_name: str) -> None:
    """Emit a `<ClassName>Methods` trait for a parent class, including all its public methods."""
    rs_name = safe_rs_ident(class_name)
    methods = ctx.class_instance_methods.get(class_name, {})
    trait_methods: list[str] = []
    for mname, mnode in methods.items():
        if mname.startswith("__"):
            continue
        arg_order = _list(mnode, "arg_order")
        arg_types = _dict(mnode, "arg_types")
        return_type = _str(mnode, "return_type")
        params: list[str] = []
        for arg in arg_order:
            if not isinstance(arg, str):
                continue
            if arg == "self":
                params.append("&mut self")
                continue
            arg_type = _str(arg_types, arg)
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
            params.append(safe_rs_ident(arg) + ": " + rs_arg_type)
        params_str = ", ".join(params)
        if return_type == "" or return_type in ("None", "none"):
            ret_str = ""
        else:
            rt = _rs_type_for_context(ctx, return_type)
            ret_str = " -> " + rt if rt != "()" else ""
        trait_methods.append("    fn " + safe_rs_ident(mname) + "(" + params_str + ")" + ret_str + ";")
    if not trait_methods:
        return
    _emit_blank(ctx)
    _emit(ctx, "pub trait " + rs_name + "Methods {")
    for tm in trait_methods:
        ctx.lines.append(tm)
    _emit(ctx, "}")


def _emit_parent_class_methods_impl(ctx: RsEmitContext, class_name: str, as_type: str = "") -> None:
    """Emit `impl <ParentName>Methods for <ClassName>` delegating to existing methods."""
    impl_class = safe_rs_ident(class_name)
    trait_class = safe_rs_ident(as_type if as_type != "" else class_name)
    methods = ctx.class_instance_methods.get(as_type if as_type != "" else class_name, {})
    trait_methods: list[str] = []
    for mname, mnode in methods.items():
        if mname.startswith("__"):
            continue
        arg_order = _list(mnode, "arg_order")
        arg_types = _dict(mnode, "arg_types")
        return_type = _str(mnode, "return_type")
        params: list[str] = []
        call_args: list[str] = []
        for arg in arg_order:
            if not isinstance(arg, str):
                continue
            if arg == "self":
                params.append("&mut self")
                continue
            arg_type = _str(arg_types, arg)
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
            params.append(safe_rs_ident(arg) + ": " + rs_arg_type)
            call_args.append(safe_rs_ident(arg))
        params_str = ", ".join(params)
        call_str = impl_class + "::" + safe_rs_ident(mname) + "(self, " + ", ".join(call_args) + ")"
        if return_type == "" or return_type in ("None", "none"):
            ret_str = ""
            body = call_str + ";"
        else:
            rt = _rs_type_for_context(ctx, return_type)
            ret_str = " -> " + rt if rt != "()" else ""
            body = "return " + call_str + ";"
        trait_methods.append((params_str, ret_str, mname, body))
    if not trait_methods:
        return
    _emit_blank(ctx)
    _emit(ctx, "impl " + trait_class + "Methods for " + impl_class + " {")
    ctx.indent_level += 1
    for (params_str, ret_str, mname, body) in trait_methods:
        _emit(ctx, "fn " + safe_rs_ident(mname) + "(" + params_str + ")" + ret_str + " {")
        ctx.indent_level += 1
        _emit(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "}")
    ctx.indent_level -= 1
    _emit(ctx, "}")


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


def _fqcn_to_tid_const_name(fqcn: str) -> str:
    """Mirror _fqcn_to_tid_const logic from pytra-cli2.py: FQCN → TID const name."""
    import re
    flat = fqcn.replace(".", "_")
    snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", flat)
    snake = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", snake)
    return snake.upper() + "_TID"


def _emit_type_registrations(ctx: RsEmitContext) -> None:
    """Emit py_register_type_info calls for user-defined classes at start of fn main().

    Uses a pure sequential TID space. Each class C gets:
        py_register_type_info(C_SEQ_TID, C_SEQ_TID, C_SEQ_TID, C_MAX_DESCENDANT_SEQ_TID)

    This way py_is_subtype(child_seq, base_seq) checks:
        base_seq <= child_seq <= base_max_seq  -- all in the same TID space.

    The sequential TIDs are the values of the TID constants generated in
    pytra_built_in_type_id_table.rs (e.g. CLASS_INHERIT_BASIC_BASE_TID = 19).
    We refer to them by const name so Rust evaluates the correct values at compile time.

    Dense TID ordering (type_id_resolved_v1 values >= 1000) is used as a proxy for
    sequential ordering: higher dense TID → higher sequential TID.
    """
    if not ctx.class_type_ids:
        return
    # Collect user-defined classes (dense TID >= 1000)
    user_classes: list[tuple[str, int]] = []  # (fqcn, dense_tid)
    for fqcn, dense_tid in ctx.class_type_ids.items():
        if fqcn.startswith("pytra."):
            continue
        if dense_tid < 1000:
            continue
        user_classes.append((fqcn, dense_tid))
    if not user_classes:
        return
    # Sort by dense TID ascending (reflects sequential ordering)
    user_classes.sort(key=lambda kv: kv[1])
    dense_to_fqcn: dict[int, str] = {d: f for f, d in user_classes}

    # Build children map: fqcn → list of child fqcns (using class_type_info_table's parent info)
    # We use type_id_resolved_v1: if FQCN "mod.Child" has dense=1012 and "mod.Base" has dense=1011,
    # and type_info_table says "mod.Base" entry=1011,exit=1013 covering 1012, then Child is under Base.
    children_map: dict[str, list[str]] = {f: [] for f, _ in user_classes}
    # Build parent → children from type_info_table_v1
    # A class P is the direct parent of class C if P's type_id_table entry contains C's dense TID
    # AND P's exit - P's entry is minimal (closest ancestor)
    fqcn_set = set(f for f, _ in user_classes)
    for fqcn, dense_tid in user_classes:
        simple_name = fqcn.rsplit(".", 1)[-1] if "." in fqcn else fqcn
        ti_c = ctx.class_type_info_table.get(fqcn) or ctx.class_type_info_table.get(simple_name)
        if ti_c is None:
            continue
        # Find the closest parent: the ancestor with smallest (exit - entry) that still covers dense_tid
        best_parent: str = ""
        best_span = -1
        for other_fqcn, other_dense in user_classes:
            if other_fqcn == fqcn:
                continue
            other_simple = other_fqcn.rsplit(".", 1)[-1] if "." in other_fqcn else other_fqcn
            ti_p = ctx.class_type_info_table.get(other_fqcn) or ctx.class_type_info_table.get(other_simple)
            if ti_p is None:
                continue
            # Does other contain fqcn? entry <= dense_tid <= exit-1 AND other != fqcn
            if ti_p["entry"] <= dense_tid <= ti_p["exit"] - 1 and ti_p["entry"] != dense_tid:
                span = ti_p["exit"] - ti_p["entry"]
                if best_parent == "" or span < best_span:
                    best_parent = other_fqcn
                    best_span = span
        if best_parent != "" and best_parent in children_map:
            children_map[best_parent].append(fqcn)

    def _max_descendant_dense(fqcn: str) -> int:
        """Return the max dense TID in the subtree rooted at fqcn."""
        max_d = ctx.class_type_ids.get(fqcn, 0)
        for child in children_map.get(fqcn, []):
            max_d = max(max_d, _max_descendant_dense(child))
        return max_d

    for fqcn, dense_tid in user_classes:
        seq_const = _fqcn_to_tid_const_name(fqcn)
        max_dense = _max_descendant_dense(fqcn)
        max_fqcn = dense_to_fqcn.get(max_dense, fqcn)
        max_const = _fqcn_to_tid_const_name(max_fqcn)
        # Register: id=seq_tid, order=seq_tid, min=seq_tid, max=max_descendant_seq_tid
        # All values use sequential TID const names so Rust evaluates them correctly.
        _emit(ctx, "py_register_type_info(" + seq_const + ", " + seq_const + ", " + seq_const + ", " + max_const + ");")


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
    set_mapping_types(mapping.types)

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

    # Compute parent class names (classes that are bases of other classes)
    ctx.parent_class_names = {
        base for base in ctx.class_bases.values()
        if base in ctx.class_names and base not in ctx.trait_names and base not in ctx.enum_bases
    }

    # Load type_id_resolved_v1 (FQCN → dense TID) and type_info_table_v1
    type_id_resolved = _dict(lp, "type_id_resolved_v1")
    for fqcn, dense_val in type_id_resolved.items():
        if isinstance(fqcn, str) and isinstance(dense_val, int):
            ctx.class_type_ids[fqcn] = dense_val
    type_info_raw = _dict(lp, "type_info_table_v1")
    for ti_name, ti_val in type_info_raw.items():
        if isinstance(ti_name, str) and isinstance(ti_val, dict):
            entry = ti_val.get("entry")
            exit_val = ti_val.get("exit")
            tid_id = ti_val.get("id")
            if isinstance(entry, int) and isinstance(exit_val, int) and isinstance(tid_id, int):
                ctx.class_type_info_table[ti_name] = {"id": tid_id, "entry": entry, "exit": exit_val}

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
        # Native .rs file table: pytra.std.* entries are fixed; short names come from mapping.json
        _STD_MODULE_FILES_FIXED: dict[str, str] = {}
        _STD_MODULE_FILES_FIXED["pytra.std.math"] = "math_native.rs"
        _STD_MODULE_FILES_FIXED["pytra.std.time"] = "time_native.rs"
        _STD_MODULE_FILES_FIXED["pytra.std.collections"] = "pytra_std_collections.rs"
        _std_module_files = {**_STD_MODULE_FILES_FIXED, **ctx.mapping.module_native_files}
        for alias, mod_id in ctx.import_alias_modules.items():
            rs_file = _std_module_files.get(mod_id, "")
            if rs_file == "":
                # Try prefix match
                for prefix, rs_f in _std_module_files.items():
                    if mod_id.startswith(prefix):
                        rs_file = rs_f
                        break
            if rs_file == "":
                # Try alias itself (e.g. alias == "math")
                rs_file = _std_module_files.get(alias, "")
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
        # Register user-defined class type info for py_is_subtype to work
        _emit_type_registrations(ctx)
        if len(main_guard) > 0:
            prev_declared = set(ctx.declared_vars)
            ctx.declared_vars = set()
            _emit_body(ctx, main_guard)
            ctx.declared_vars = prev_declared
        ctx.indent_level -= 1
        _emit(ctx, "}")

    return "\n".join(lines).rstrip() + "\n"
