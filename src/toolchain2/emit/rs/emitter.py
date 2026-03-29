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
    if name.startswith("_") and name in ctx.module_private_symbols and ctx.module_id != "":
        prefix = _module_prefix(ctx)
        if prefix != "":
            return prefix + "__" + name[1:]
    return safe_rs_ident(name)


def _rs_var_name(ctx: RsEmitContext, name: str) -> str:
    """Resolve a local variable name."""
    return safe_rs_ident(name)


def _rs_type_for_context(ctx: RsEmitContext, resolved_type: str) -> str:
    """Get Rust type, considering class/trait names in context."""
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
    # Check for runtime symbol
    mapped = ctx.runtime_imports.get(name)
    if mapped is not None and mapped != "":
        return mapped
    return _rs_symbol_name(ctx, name)


def _emit_constant(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    resolved_type = _str(node, "resolved_type")
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
        # Emit typed integer literal
        if resolved_type == "int64" or resolved_type == "int":
            return str(value) + "_i64"
        if resolved_type == "int32":
            return str(value) + "_i32"
        if resolved_type == "int16":
            return str(value) + "_i16"
        if resolved_type == "int8":
            return str(value) + "_i8"
        if resolved_type == "uint64":
            return str(value) + "_u64"
        if resolved_type == "uint32":
            return str(value) + "_u32"
        if resolved_type == "uint16":
            return str(value) + "_u16"
        if resolved_type == "uint8":
            return str(value) + "_u8"
        return str(value)
    if isinstance(value, float):
        s = str(value)
        if "." not in s and "e" not in s and "E" not in s:
            s = s + ".0"
        if resolved_type == "float32":
            return s + "_f32"
        return s + "_f64"
    return str(value)


def _emit_binop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    op = _str(node, "op")
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
        # Integer floor division in Rust is just /
        return "(" + left + " / " + right + ")"
    if op == "Pow":
        return "(" + left + ".pow(" + right + " as u32))"
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
    left = _emit_expr(ctx, node.get("left"))
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
    for idx, comparator in enumerate(comparators):
        op_obj = ops[idx] if idx < len(ops) else None
        op_name = op_obj if isinstance(op_obj, str) else _str(op_obj, "kind")
        rs_op = op_map.get(op_name, op_name)
        right = _emit_expr(ctx, comparator)
        parts.append("(" + current_left + " " + rs_op + " " + right + ")")
        current_left = right
    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _emit_boolop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    op = _str(node, "op")
    rs_op = "&&" if op == "And" else "||"
    rendered = [_emit_expr(ctx, v) for v in values]
    return "(" + (" " + rs_op + " ").join(rendered) + ")"


def _emit_attribute(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    obj = _emit_expr(ctx, node.get("value"))
    attr = _str(node, "attr")
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
    obj = _emit_expr(ctx, node.get("value"))
    slice_node = node.get("slice")
    obj_type = _str(node.get("value"), "resolved_type") if isinstance(node.get("value"), dict) else ""
    idx = _emit_expr(ctx, slice_node)
    if obj_type.startswith("list[") or obj_type == "list":
        return obj + ".get(" + idx + ")"
    if obj_type.startswith("dict[") or obj_type == "dict":
        return obj + "[&" + idx + "]"
    # Default: use indexing
    return obj + "[" + idx + " as usize]"


def _emit_ifexp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    test = _emit_expr(ctx, node.get("test"))
    body = _emit_expr(ctx, node.get("body"))
    orelse = _emit_expr(ctx, node.get("orelse"))
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
    if runtime_call != "":
        mapped = resolve_runtime_call(runtime_call, builtin_name_field, adapter_kind, ctx.mapping)
        if mapped != "" and not mapped.startswith("__"):
            # Handle special mappings
            if mapped == "__CAST__":
                if len(args) >= 1:
                    return _emit_expr(ctx, args[0])
                return ""
            return _emit_runtime_call(ctx, mapped, func, args, keywords, node)

    # Check for lowered_kind
    lowered_kind = _str(node, "lowered_kind")
    if lowered_kind == "BuiltinCall":
        builtin_name = _str(node, "builtin_name")
        runtime_sym = _str(node, "runtime_symbol")
        mapped2 = resolve_runtime_call(runtime_sym, builtin_name, adapter_kind, ctx.mapping)
        if mapped2 != "" and not mapped2.startswith("__"):
            return _emit_runtime_call(ctx, mapped2, func, args, keywords, node)
        # Fallthrough to normal call with builtin_name or runtime_sym
        call_name = mapped2 if mapped2 != "" else (runtime_sym if runtime_sym != "" else builtin_name)
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
        rendered_args = [_emit_expr(ctx, a) for a in args]
        return func_expr + "(" + ", ".join(rendered_args) + ")"

    # Check for class constructor
    if func_name in ctx.class_names:
        return _emit_constructor_call(ctx, func_name, args, keywords, node)

    # Check for runtime imports
    mapped3 = ctx.runtime_imports.get(func_name)
    if mapped3 is not None and mapped3 != "":
        return _emit_runtime_call(ctx, mapped3, func, args, keywords, node)

    # Regular call
    rendered_args = [_emit_call_arg(ctx, a) for a in args]
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            rendered_args.append(_emit_expr(ctx, kw_val))
    call_target = _rs_symbol_name(ctx, func_name)
    return call_target + "(" + ", ".join(rendered_args) + ")"


def _emit_call_arg(ctx: RsEmitContext, arg: JsonVal) -> str:
    """Emit a call argument, handling Box nodes."""
    if isinstance(arg, dict) and _str(arg, "kind") == "Box":
        inner = arg.get("value")
        return _emit_expr(ctx, inner)
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

    # Check runtime_call for method call
    runtime_call = _str(call_node, "runtime_call")
    call_adapter_kind = _str(call_node, "runtime_call_adapter_kind")
    call_builtin = _str(call_node, "builtin_name")
    if runtime_call != "":
        mapped = resolve_runtime_call(runtime_call, call_builtin, call_adapter_kind, ctx.mapping)
        if mapped != "" and not mapped.startswith("__"):
            obj_str = _emit_expr(ctx, obj)
            rendered_args = [_emit_call_arg(ctx, a) for a in args]
            for kw in keywords:
                if isinstance(kw, dict):
                    kw_val = kw.get("value")
                    rendered_args.append(_emit_expr(ctx, kw_val))
            all_args = [obj_str] + rendered_args
            return mapped + "(" + ", ".join(all_args) + ")"

    obj_str = _emit_expr(ctx, obj)
    rendered_args = [_emit_expr(ctx, a) for a in args]
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            rendered_args.append(_emit_expr(ctx, kw_val))

    # PyList methods
    if obj_type.startswith("list[") or obj_type == "list":
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
            return obj_str + ".keys().cloned().collect::<Vec<_>>()"
        if method == "values":
            return obj_str + ".values().cloned().collect::<Vec<_>>()"
        if method == "items":
            return obj_str + ".iter().map(|(k, v)| (k.clone(), v.clone())).collect::<Vec<_>>()"
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
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            rendered_args.append(_emit_expr(ctx, kw_val))
    rs_name = safe_rs_ident(class_name)
    return "Box::new(" + rs_name + "::new(" + ", ".join(rendered_args) + "))"


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
    # Fallback: use repr if available
    repr_str = _str(node, "repr")
    if repr_str != "":
        return "/* " + repr_str + " */"
    return "/* unsupported_expr:" + kind + " */"


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
    rendered = _emit_expr(ctx, value)
    _emit(ctx, rendered + ";")


def _emit_return(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if value is None:
        _emit(ctx, "return;")
        return
    rendered = _emit_expr(ctx, value)
    _emit(ctx, "return " + rendered + ";")


def _emit_ann_assign(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    resolved_type = _str(node, "resolved_type")

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
            if obj_type.startswith("list[") or obj_type == "list":
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

        if target_name in ctx.declared_vars:
            _emit(ctx, rs_name + " = " + rhs + ";")
        else:
            ctx.declared_vars.add(target_name)
            resolved_type = _str(value, "resolved_type") if isinstance(value, dict) else ""
            if resolved_type != "":
                ctx.var_types[target_name] = resolved_type
            _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")

    elif isinstance(target, str):
        rs_name = _rs_var_name(ctx, target)
        rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
        if target in ctx.declared_vars:
            _emit(ctx, rs_name + " = " + rhs + ";")
        else:
            ctx.declared_vars.add(target)
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
            if len(args) == 1:
                inner_iter = _emit_for_iter(ctx, args[0], target)
                return inner_iter + ".enumerate().map(|(i, v)| (i as i64, v))"

        # reversed()
        if func_name == "reversed":
            if len(args) == 1:
                inner = _emit_expr(ctx, args[0])
                return inner + ".iter_snapshot().into_iter().rev()"

    # List/collection iteration
    if resolved_type.startswith("list[") or resolved_type == "list":
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".iter_snapshot().into_iter()"

    # String iteration (character by character)
    if resolved_type == "str":
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".chars().map(|c| c.to_string())"

    # Bytes/bytearray iteration
    if resolved_type in ("bytes", "bytearray"):
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".iter().cloned()"

    # Dict iteration (keys)
    if resolved_type.startswith("dict[") or resolved_type == "dict":
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".keys().cloned()"

    # Set iteration
    if resolved_type.startswith("set[") or resolved_type == "set":
        iter_expr = _emit_expr(ctx, iter_node)
        return iter_expr + ".iter().cloned()"

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

    test_str = _emit_expr(ctx, test)
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

    test_str = _emit_expr(ctx, test)
    _emit(ctx, "if " + test_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1

    if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
        _emit(ctx, "} else if " + _emit_expr(ctx, orelse[0].get("test")) + " {")
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
        _emit(ctx, "} else if " + _emit_expr(ctx, orelse[0].get("test")) + " {")
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
        rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
        # Check if it's a class type (use reference)
        params.append(safe_rs_ident(arg) + ": " + rs_arg_type)

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
    ctx.current_return_type = return_type
    ctx.declared_vars = set()

    # Add parameters to declared vars
    for arg in arg_order:
        if isinstance(arg, str) and arg != "self":
            ctx.declared_vars.add(arg)
            arg_type = _str(arg_types, arg)
            if arg_type != "":
                ctx.var_types[arg] = arg_type

    _emit(ctx, "fn " + fn_name + "(" + params_str + ")" + ret_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")

    # Restore context
    ctx.current_return_type = prev_return_type
    ctx.declared_vars = prev_declared
    ctx.var_types = prev_var_types


# ---------------------------------------------------------------------------
# Class definition
# ---------------------------------------------------------------------------

def _collect_class_info(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Collect class metadata for later use during emission."""
    name = _str(node, "name")
    if name == "":
        return
    ctx.class_names.add(name)
    body = _list(node, "body")

    bases = _list(node, "bases")
    if len(bases) > 0:
        base = bases[0]
        if isinstance(base, dict):
            ctx.class_bases[name] = _str(base, "id")

    fields: dict[str, str] = {}
    methods: dict[str, dict[str, JsonVal]] = {}
    statics: set[str] = set()

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind == "FunctionDef":
            fn_name = _str(stmt, "name")
            decorators = _list(stmt, "decorator_list")
            is_static = any(isinstance(d, dict) and _str(d, "id") == "staticmethod" for d in decorators)
            if is_static:
                statics.add(fn_name)
            methods[fn_name] = stmt
        elif stmt_kind in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                resolved_type = _str(stmt, "resolved_type")
                if field_name != "" and resolved_type != "":
                    fields[field_name] = resolved_type

    ctx.class_fields[name] = fields
    ctx.class_instance_methods[name] = methods
    ctx.class_static_methods[name] = statics


def _emit_class_def(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    if name == "":
        return
    body = _list(node, "body")
    bases = _list(node, "bases")
    decorators = _list(node, "decorator_list")
    rs_name = safe_rs_ident(name)

    is_trait = any(isinstance(d, dict) and _str(d, "id") in ("trait", "@trait") for d in decorators)

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
                                resolved_type = _str(init_stmt, "resolved_type")
                                if field_name != "" and resolved_type != "":
                                    fields[field_name] = resolved_type
            else:
                other_methods.append(stmt)
        elif stmt_kind in ("AnnAssign", "Assign"):
            # Class-level field declarations
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                resolved_type = _str(stmt, "resolved_type")
                if field_name != "" and resolved_type != "" and not field_name.startswith("__"):
                    fields[field_name] = resolved_type

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
    elif len(fields) == 0:
        _emit(ctx, "fn new() -> Self {")
        ctx.indent_level += 1
        _emit(ctx, rs_name + " {}")
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # Emit other methods
    for method in other_methods:
        _emit_blank(ctx)
        _emit_function_def(ctx, method, owner=name)

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


# ---------------------------------------------------------------------------
# Module-level emission
# ---------------------------------------------------------------------------

def _emit_module_body(ctx: RsEmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("Import", "ImportFrom"):
            continue  # handled separately
        _emit_stmt(ctx, stmt)


def _collect_uses(ctx: RsEmitContext) -> list[str]:
    """Determine which `use` statements are needed."""
    uses: list[str] = [
        "use std::collections::HashMap;",
        "use std::collections::HashSet;",
    ]
    return uses


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
    lines.append("")

    # Emit body
    _emit_module_body(ctx, body)

    # Emit main_guard as fn main()
    if len(main_guard) > 0 and ctx.is_entry:
        _emit_blank(ctx)
        _emit(ctx, "fn main() {")
        ctx.indent_level += 1
        prev_declared = set(ctx.declared_vars)
        ctx.declared_vars = set()
        _emit_body(ctx, main_guard)
        ctx.declared_vars = prev_declared
        ctx.indent_level -= 1
        _emit(ctx, "}")

    return "\n".join(lines).rstrip() + "\n"
