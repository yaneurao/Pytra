"""EAST3 → Go source code emitter.

お手本 emitter: 他言語 emitter のテンプレートとなる設計。
入力は linked EAST3 JSON (dict) のみ。toolchain/ への依存なし。

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass
from dataclasses import field
from typing import Any, cast

from toolchain.emit.go.types import go_type, go_zero_value, _safe_go_ident, _split_generic_args, _parse_callable_signature
from toolchain.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_import_alias_map, build_runtime_import_map,
    resolve_runtime_symbol_name,
)
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.link.expand_defaults import expand_cross_module_defaults


# ---------------------------------------------------------------------------
# Emit context (mutable state for one module emission)
# ---------------------------------------------------------------------------

JsonVal = Any

@dataclass
class EmitContext:
    """Per-module mutable state during emission."""
    module_id: str = ""
    source_path: str = ""
    is_entry: bool = False
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    imports_needed: set[str] = field(default_factory=set)
    # Variable types in current scope
    var_types: dict[str, str] = field(default_factory=dict)
    # indent_level at which each variable was first declared (for block-scope tracking)
    var_decl_depth: dict[str, int] = field(default_factory=dict)
    # Current function return type (for empty list literal type inference)
    current_return_type: str = ""
    # Imported runtime symbols mapped to emitted helper names.
    runtime_imports: dict[str, str] = field(default_factory=dict)
    # Runtime mapping (from mapping.json)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    # Import alias → module_id map (for module.attr call resolution)
    import_alias_modules: dict[str, str] = field(default_factory=dict)
    # Class info
    class_names: set[str] = field(default_factory=set)
    trait_names: set[str] = field(default_factory=set)
    class_bases: dict[str, str] = field(default_factory=dict)
    class_property_methods: dict[str, set[str]] = field(default_factory=dict)
    class_static_methods: dict[str, set[str]] = field(default_factory=dict)
    class_instance_methods: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    class_vars: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    class_fields: dict[str, dict[str, str]] = field(default_factory=dict)
    enum_bases: dict[str, str] = field(default_factory=dict)
    enum_members: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    function_signatures: dict[str, tuple[list[str], dict[str, str], dict[str, JsonVal]]] = field(default_factory=dict)
    function_return_types: dict[str, str] = field(default_factory=dict)
    method_signatures: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    class_init_signatures: dict[str, dict[str, JsonVal]] = field(default_factory=dict)
    list_alias_vars: set[str] = field(default_factory=set)
    # Current class context (for method emission)
    current_class: str = ""
    current_receiver: str = "self"
    constructor_return_target: str = ""
    # Helper functions that mutate their first bytearray argument and must return it.
    bytearray_mutating_funcs: dict[str, str] = field(default_factory=dict)
    # Per-module expression temp counter for IIFE-based lowering.
    temp_counter: int = 0
    # Top-level private symbols emitted in this module; mangle to avoid package collisions.
    module_private_symbols: set[str] = field(default_factory=set)
    # Exception type bounds from linked_program_v1.type_info_table_v1.
    exception_type_bounds: dict[str, tuple[int, int]] = field(default_factory=dict)
    # Exception type ids from linked_program_v1.type_info_table_v1.
    exception_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    current_exception_var: str = ""
    current_function_scope: str = ""
    current_value_container_locals: set[str] = field(default_factory=set)
    container_value_locals_by_scope: dict[str, set[str]] = field(default_factory=dict)
    ref_container_locals: set[str] = field(default_factory=set)
    # Go variadic parameters (func(args ...T)): these are Go slices, NOT *PyList.
    # _wrapper_container_storage_expr must NOT append .items for these.
    go_vararg_params: set[str] = field(default_factory=set)
    # Union type aliases: names bound to Union[...] at module level → map to `any` in Go
    union_type_aliases: set[str] = field(default_factory=set)
    # When True, dynamic-dispatch calls (yields_dynamic) should NOT coerce the result
    # to the Call's resolved_type. Used by _emit_unbox to get a raw `any` value for nil-check.
    skip_any_coercion: bool = False
    # Go package names: loaded from mapping.json "go_pkg_imports"
    go_pkg_math: str = ""
    go_pkg_os: str = ""
    go_pkg_sort: str = ""
    # Builtin dispatch names: loaded from mapping.json "go_builtin_dispatch"
    dispatch_print: str = ""
    dispatch_len: str = ""
    # Builtin exception type metadata: loaded from mapping.json "go_class_names"
    builtin_exc_bounds: dict[str, tuple[int, int]] = field(default_factory=dict)
    builtin_exc_ctor_types: frozenset[str] = field(default_factory=frozenset)
    path_type_name: str = ""
    # Known method signatures keyed by (class_name, method_name): built in emit_go_module
    known_method_signatures: dict[tuple[str, str], dict[str, JsonVal]] = field(default_factory=dict)


_ARGPARSE_ADD_ARGUMENT_SIG: dict[str, JsonVal] = {
    "arg_order": ["self", "name0", "name1", "name2", "name3", "help", "action", "choices", "default"],
    "arg_types": {
        "name0": "str",
        "name1": "str",
        "name2": "str",
        "name3": "str",
        "help": "str",
        "action": "str",
        "choices": "list[str]",
        "default": "str | bool | None",
    },
    "arg_defaults": {
        "name1": {"kind": "Constant", "value": "", "resolved_type": "str"},
        "name2": {"kind": "Constant", "value": "", "resolved_type": "str"},
        "name3": {"kind": "Constant", "value": "", "resolved_type": "str"},
        "help": {"kind": "Constant", "value": "", "resolved_type": "str"},
        "action": {"kind": "Constant", "value": "", "resolved_type": "str"},
        "choices": {"kind": "List", "elements": [], "resolved_type": "list[str]"},
        "default": {"kind": "Constant", "value": None, "resolved_type": "None"},
    },
}


class _GoStmtCommonRenderer(CommonRenderer):
    def __init__(self, ctx: EmitContext) -> None:
        self.ctx = ctx
        super().__init__("go")
        self.state.lines = ctx.lines
        self.state.indent_level = ctx.indent_level

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(self.ctx, node)

    def render_expr(self, node: JsonVal) -> str:
        return _emit_expr(self.ctx, node)

    def render_condition_expr(self, node: JsonVal) -> str:
        if isinstance(node, dict):
            rt = _effective_resolved_type(self.ctx, node)
            rendered = _emit_expr(self.ctx, node)
            rendered = _wrapper_container_storage_expr(self.ctx, node, rendered)
            if rt.startswith("list[") or rt.startswith("dict[") or rt.startswith("set[") or rt in ("str", "bytes", "bytearray"):
                return self._format_condition("len(" + rendered + ") > 0")
        return super().render_condition_expr(node)

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("go common renderer assign string hook is not used directly")

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

    def render_raise_value(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("go common renderer raise value hook is not used directly")

    def emit_raise_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_raise(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def render_except_open(self, handler: dict[str, JsonVal]) -> str:
        raise RuntimeError("go common renderer except hook is not used directly")

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


class _GoExprCommonRenderer(CommonRenderer):
    def __init__(self, ctx: EmitContext) -> None:
        self.ctx = ctx
        super().__init__("go")

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
        raise RuntimeError("go common renderer assign hook is not used in expr adapter")

    def render_expr_extension(self, node: dict[str, JsonVal]) -> str:
        return _emit_expr_extension(self.ctx, node)


def _emit_common_stmt_if_supported(ctx: EmitContext, node: dict[str, JsonVal]) -> bool:
    kind = _str(node, "kind")
    if kind not in ("Expr", "Return", "Assign", "AnnAssign", "Pass", "Raise", "Try", "comment", "blank", "If", "While"):
        return False
    renderer = _GoStmtCommonRenderer(ctx)
    renderer.emit_stmt(node)
    ctx.indent_level = renderer.state.indent_level
    return True


# ---------------------------------------------------------------------------
# Indentation helpers
# ---------------------------------------------------------------------------

def _indent(ctx: EmitContext) -> str:
    return "\t" * ctx.indent_level


def _emit(ctx: EmitContext, line: str) -> None:
    ctx.lines.append(_indent(ctx) + line)


def _emit_raw(ctx: EmitContext, line: str) -> None:
    ctx.lines.append(line)


def _emit_blank(ctx: EmitContext) -> None:
    ctx.lines.append("")


def _next_temp(ctx: EmitContext, prefix: str) -> str:
    ctx.temp_counter += 1
    return "__" + prefix + "_" + str(ctx.temp_counter)


def _go_class_marker_method_name(ctx: EmitContext, type_name: str) -> str:
    return "__pytra_is_" + _go_symbol_name(ctx, type_name)


def _module_prefix(ctx: EmitContext) -> str:
    if ctx.module_id == "":
        return ""
    return _safe_go_ident(ctx.module_id.replace(".", "_"))


def _scope_key(ctx: EmitContext, func_name: str, owner_name: str = "") -> str:
    scope_name = func_name if owner_name == "" else owner_name + "." + func_name
    if ctx.module_id == "":
        return scope_name
    return ctx.module_id + "::" + scope_name


def _container_value_locals_for_scope(
    ctx: EmitContext,
    func_name: str,
    owner_name: str = "",
) -> set[str]:
    keys = [_scope_key(ctx, func_name, owner_name)]
    if owner_name != "":
        keys.append(_scope_key(ctx, func_name))
    out: set[str] = set()
    for key in keys:
        out.update(ctx.container_value_locals_by_scope.get(key, set()))
    return out


def _load_container_value_locals(
    linked_program_meta: dict[str, JsonVal],
) -> dict[str, set[str]]:
    hints = _dict(linked_program_meta, "container_ownership_hints_v1")
    raw = _dict(hints, "container_value_locals_v1")
    out: dict[str, set[str]] = {}
    for scope_key, payload in raw.items():
        if not isinstance(scope_key, str) or scope_key == "":
            continue
        if not isinstance(payload, dict):
            continue
        locals_raw = payload.get("locals")
        if not isinstance(locals_raw, list):
            continue
        locals_out = {
            name
            for name in locals_raw
            if isinstance(name, str) and name != ""
        }
        if len(locals_out) != 0:
            out[scope_key] = locals_out
    return out


def _is_container_resolved_type(resolved_type: str) -> bool:
    return (
        resolved_type == "list"
        or resolved_type == "dict"
        or resolved_type == "set"
        or resolved_type.startswith("list[")
        or resolved_type.startswith("dict[")
        or resolved_type.startswith("set[")
    )


def _is_union_like_resolved_type(ctx: EmitContext, resolved_type: str) -> bool:
    if resolved_type in ("", "unknown"):
        return False
    if resolved_type in ctx.union_type_aliases:
        return True
    if "|" in resolved_type:
        parts = [part.strip() for part in resolved_type.split("|") if part.strip() != ""]
        return len(parts) > 1
    return False


def _go_set_elem_type(ctx: EmitContext, resolved_type: str) -> str:
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        return "string"
    return _go_signature_type(ctx, resolved_type)


def _optional_child_types_fit(inner_type: str, child_types: set[str]) -> bool:
    return all(child_type in ("None", "none", inner_type) for child_type in child_types)


def _prefer_value_container_local(ctx: EmitContext, name: str, resolved_type: str) -> bool:
    return (
        name != ""
        and (resolved_type == "list" or resolved_type.startswith("list["))
        and name in ctx.current_value_container_locals
    )


def _go_ref_container_type(ctx: EmitContext, resolved_type: str) -> str:
    if resolved_type == "list":
        return "*PyList[any]"
    if resolved_type == "dict":
        return "*PyDict[string, any]"
    if resolved_type == "set":
        return "*PySet[any]"
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "*PyList[" + _go_signature_type(ctx, inner) + "]"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            return "*PyDict[" + _go_type_with_ctx(ctx, parts[0]) + ", " + _go_signature_type(ctx, parts[1]) + "]"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        return "*PySet[" + _go_set_elem_type(ctx, inner) + "]"
    # Optional container: dict[K,V] | None → *PyDict[K,V] (nil encodes None)
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner4 = resolved_type[:-7].strip() if resolved_type.endswith(" | None") else resolved_type[:-5].strip()
        if _is_container_resolved_type(inner4):
            return _go_ref_container_type(ctx, inner4)
    return go_type(resolved_type)


def _decl_go_type(ctx: EmitContext, resolved_type: str, name: str = "") -> str:
    if _is_container_resolved_type(resolved_type) and not _prefer_value_container_local(ctx, name, resolved_type):
        return _go_ref_container_type(ctx, resolved_type)
    return _go_signature_type(ctx, resolved_type)


def _decl_go_zero_value(ctx: EmitContext, resolved_type: str, name: str = "") -> str:
    # Optional container types (e.g. dict[K,V] | None) have nil as zero value, not a ctor.
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        return go_zero_value(resolved_type)
    if _is_container_resolved_type(resolved_type) and not _prefer_value_container_local(ctx, name, resolved_type):
        if resolved_type == "list" or resolved_type.startswith("list["):
            return _go_ref_container_ctor(ctx, resolved_type, "[]")
        if resolved_type == "dict" or resolved_type.startswith("dict["):
            return _go_ref_container_ctor(ctx, resolved_type, "{}")
        if resolved_type == "set" or resolved_type.startswith("set["):
            return _go_ref_container_ctor(ctx, resolved_type, "{}")
    return go_zero_value(resolved_type)


def _go_ref_container_ctor(ctx: EmitContext, resolved_type: str, literal_suffix: str) -> str:
    if resolved_type == "list":
        if literal_suffix == "[]":
            return "NewPyList[any]()"
        return "PyListFromSlice[any]([]any{})"
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        elem_gt = _go_signature_type(ctx, inner)
        if literal_suffix == "[]":
            return "NewPyList[" + elem_gt + "]()"
        return "PyListFromSlice[" + elem_gt + "]([]" + elem_gt + literal_suffix + ")"
    if resolved_type == "dict":
        if literal_suffix == "{}":
            return "NewPyDict[string, any]()"
        return "PyDictFromMap[string, any](map[string]any{})"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner2 = resolved_type[5:-1]
        parts = _split_generic_args(inner2)
        if len(parts) == 2:
            key_gt = _go_type_with_ctx(ctx, parts[0])
            val_gt = _go_signature_type(ctx, parts[1])
            if literal_suffix == "{}":
                return "NewPyDict[" + key_gt + ", " + val_gt + "]()"
            return "PyDictFromMap[" + key_gt + ", " + val_gt + "](map[" + key_gt + "]" + val_gt + literal_suffix + ")"
    if resolved_type == "set":
        if literal_suffix == "{}":
            return "NewPySet[any]()"
        return "PySetFromMap[any](map[any]struct{}{})"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner3 = resolved_type[4:-1]
        elem_gt2 = _go_set_elem_type(ctx, inner3)
        if literal_suffix == "{}":
            return "NewPySet[" + elem_gt2 + "]()"
        return "PySetFromMap[" + elem_gt2 + "](map[" + elem_gt2 + "]struct{}" + literal_suffix + ")"
    return go_zero_value(resolved_type)


def _wrap_ref_container_value_code(ctx: EmitContext, value_code: str, resolved_type: str) -> str:
    stripped = value_code.strip()
    if stripped.startswith("py_sorted("):
        return value_code
    if stripped.startswith("func() *PyList[") or stripped.startswith("func() *PyDict[") or stripped.startswith("func() *PySet["):
        return value_code
    if stripped.endswith(".items"):
        base = stripped[:-6]
        if base in ctx.var_types:
            source_type = ctx.var_types.get(base, "")
            if _is_container_resolved_type(source_type):
                return base
    if stripped in ctx.var_types:
        source_type = ctx.var_types.get(stripped, "")
        if source_type == resolved_type and _is_container_resolved_type(source_type):
            if stripped in ctx.ref_container_locals or not _prefer_value_container_local(ctx, stripped, source_type):
                return stripped
        # Optional container variable (e.g. list[T] | None → *PyList[T] in Go).
        # The variable already holds a *PyList/*PyDict/*PySet, so nil encodes None — return directly.
        opt_inner2 = _optional_inner_type(source_type)
        if opt_inner2 == resolved_type and _is_container_resolved_type(resolved_type):
            return stripped
    # Optional container resolved_type (e.g. list[T] | None): wrap the value for the inner type.
    # The parameter/field expects *PyList/*PyDict/*PySet (nil encodes None).
    opt_inner = _optional_inner_type(resolved_type)
    if opt_inner != "" and _is_container_resolved_type(opt_inner) and value_code != "nil":
        return _wrap_ref_container_value_code(ctx, value_code, opt_inner)
    if value_code.startswith("NewPyList[") or value_code.startswith("PyListFromSlice["):
        return value_code
    if value_code.startswith("py_list_any("):
        return value_code
    if value_code.startswith("NewPyDict[") or value_code.startswith("PyDictFromMap["):
        return value_code
    if value_code.startswith("py_dict_string_any("):
        return value_code
    if value_code.startswith("NewPySet[") or value_code.startswith("PySetFromMap["):
        return value_code
    if resolved_type == "list":
        if value_code == "[]any{}":
            return "NewPyList[any]()"
        return "py_list_any(" + value_code + ")"
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        elem_gt = _go_signature_type(ctx, inner)
        if value_code == "[]" + elem_gt + "{}":
            return "NewPyList[" + elem_gt + "]()"
        if elem_gt == "any":
            return "py_list_any(" + value_code + ")"
        return "PyListFromSlice[" + elem_gt + "](" + value_code + ")"
    if resolved_type == "dict":
        if value_code == "map[string]any{}":
            return "NewPyDict[string, any]()"
        return "py_dict_string_any(" + value_code + ")"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner2 = resolved_type[5:-1]
        parts = _split_generic_args(inner2)
        if len(parts) == 2:
            key_gt = _go_type_with_ctx(ctx, parts[0])
            val_gt = _go_signature_type(ctx, parts[1])
            # Any empty map literal (e.g. map[any]any{} from unknown-typed {}) → NewPyDict
            _is_empty_map = value_code.startswith("map[") and value_code.endswith("{}")
            if _is_empty_map:
                return "NewPyDict[" + key_gt + ", " + val_gt + "]()"
            if key_gt == "string" and val_gt == "any":
                return "py_dict_string_any(" + value_code + ")"
            return "PyDictFromMap[" + key_gt + ", " + val_gt + "](" + value_code + ")"
    if resolved_type == "set":
        if value_code == "map[any]struct{}{}":
            return "NewPySet[any]()"
        return "PySetFromMap[any](" + value_code + ")"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner3 = resolved_type[4:-1]
        elem_gt2 = _go_signature_type(ctx, inner3)
        if value_code == "map[" + elem_gt2 + "]struct{}{}":
            return "NewPySet[" + elem_gt2 + "]()"
        return "PySetFromMap[" + elem_gt2 + "](" + value_code + ")"
    return value_code


def _wrap_container_call_args(ctx: EmitContext, args: list[JsonVal], arg_strs: list[str]) -> list[str]:
    """Wrap container-typed call arguments to reference wrapper types (*PyList[T] etc.)."""
    result: list[str] = []
    for i, code in enumerate(arg_strs):
        arg_node = args[i] if i < len(args) and isinstance(args[i], dict) else None
        if isinstance(arg_node, dict):
            arg_rt = _str(arg_node, "resolved_type")
            if _is_container_resolved_type(arg_rt) and not _is_wrapper_container_expr(ctx, arg_node, code):
                code = _wrap_ref_container_value_code(ctx, code, arg_rt)
        result.append(code)
    return result


def _assign_uses_ref_container_decl(
    ctx: EmitContext,
    name: str,
    decl_type: str,
    value: JsonVal,
) -> bool:
    if not _is_container_resolved_type(decl_type):
        return False
    if _prefer_value_container_local(ctx, name, decl_type):
        return False
    if not isinstance(value, dict):
        return False
    kind = _str(value, "kind")
    if kind in ("List", "Dict", "Set"):
        return True
    if kind != "Call":
        return False
    return _str(value, "lowered_kind") == "BuiltinCall"


def _wrapper_container_storage_expr(ctx: EmitContext, node: JsonVal, rendered: str) -> str:
    if rendered.startswith("py_items("):
        return rendered
    if rendered.startswith("NewPyList[") or rendered.startswith("PyListFromSlice["):
        return rendered + ".items"
    if rendered.startswith("py_to_list_typed["):
        return rendered + ".items"
    if rendered.startswith("NewPyDict[") or rendered.startswith("PyDictFromMap["):
        return rendered + ".items"
    # Type assertions to wrapper types need .items to get the underlying native slice/map.
    if not rendered.endswith(".items"):
        if ".(*PyList[" in rendered:
            return rendered + ".items"
        if ".(*PyDict[" in rendered:
            return rendered + ".items"
        if ".(*PySet[" in rendered:
            return rendered + ".items"
    if rendered.startswith("NewPySet[") or rendered.startswith("PySetFromMap["):
        return rendered + ".items"
    if not isinstance(node, dict):
        return rendered
    node_rt = _str(node, "resolved_type")
    if _str(node, "kind") == "Call":
        if _is_wrapper_container_expr(ctx, node, rendered):
            if node_rt.startswith("list[") or node_rt == "list":
                return rendered + ".items"
            if node_rt.startswith("dict[") or node_rt == "dict":
                return rendered + ".items"
            if node_rt.startswith("set[") or node_rt == "set":
                return rendered + ".items"
    if _str(node, "kind") == "Attribute":
        if _is_wrapper_container_expr(ctx, node, rendered):
            if node_rt.startswith("list[") or node_rt == "list":
                return rendered + ".items"
            if node_rt.startswith("dict[") or node_rt == "dict":
                return rendered + ".items"
            if node_rt.startswith("set[") or node_rt == "set":
                return rendered + ".items"
    if _str(node, "kind") == "Subscript":
        if _is_wrapper_container_expr(ctx, node, rendered):
            if node_rt.startswith("list[") or node_rt == "list":
                return rendered + ".items"
            if node_rt.startswith("dict[") or node_rt == "dict":
                return rendered + ".items"
            if node_rt.startswith("set[") or node_rt == "set":
                return rendered + ".items"
    if _str(node, "kind") != "Name":
        return rendered
    name = _str(node, "id")
    if name == "":
        return rendered
    safe_name = _go_symbol_name(ctx, name)
    # Go variadic params are []T (Go slice), not *PyList[T] — never append .items.
    if safe_name in ctx.go_vararg_params:
        return rendered
    scope_type = ctx.var_types.get(safe_name, "")
    if (
        safe_name not in ctx.ref_container_locals
        and not (
            scope_type != ""
            and _is_container_resolved_type(scope_type)
            and not _prefer_value_container_local(ctx, name, scope_type)
        )
    ):
        return rendered
    if scope_type.startswith("list[") or scope_type == "list":
        return rendered + ".items"
    if scope_type.startswith("dict[") or scope_type == "dict":
        return rendered + ".items"
    if scope_type.startswith("set[") or scope_type == "set":
        return rendered + ".items"
    return rendered


def _is_wrapper_container_expr(ctx: EmitContext, node: JsonVal, rendered: str) -> bool:
    if rendered.startswith("py_items("):
        return False
    if rendered.startswith("NewPyList[") or rendered.startswith("PyListFromSlice["):
        return True
    if rendered.startswith("py_to_list_typed["):
        return True
    if rendered.startswith("NewPyDict[") or rendered.startswith("PyDictFromMap["):
        return True
    if rendered.startswith("NewPySet[") or rendered.startswith("PySetFromMap["):
        return True
    # Type assertions to wrapper types (from _coerce_from_any for container types)
    if ".(*PyList[" in rendered or ".(*PyDict[" in rendered or ".(*PySet[" in rendered:
        return True
    if not isinstance(node, dict):
        return False
    kind = _str(node, "kind")
    if kind == "Call":
        if (
            rendered.startswith("func() []")
            or rendered.startswith("func() map[")
            or rendered.startswith("func() PyTuple")
        ):
            return False
        if _is_container_resolved_type(_str(node, "resolved_type")):
            return True
        func_node = node.get("func")
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
            fn_name = _str(func_node, "id")
            if _is_container_resolved_type(ctx.function_return_types.get(fn_name, "")):
                return True
        return (
            rendered.startswith("NewPyList[")
            or rendered.startswith("PyListFromSlice[")
            or rendered.startswith("py_to_list_typed[")
            or rendered.startswith("py_list_any(")
            or rendered.startswith("NewPyDict[")
            or rendered.startswith("PyDictFromMap[")
            or rendered.startswith("py_dict_string_any(")
            or rendered.startswith("NewPySet[")
            or rendered.startswith("PySetFromMap[")
        )
    if kind == "IfExp":
        return _is_container_resolved_type(_str(node, "resolved_type"))
    if kind == "Attribute":
        return _is_container_resolved_type(_str(node, "resolved_type"))
    if kind == "Subscript":
        if not _is_container_resolved_type(_str(node, "resolved_type")):
            return False
        value_node = node.get("value")
        if not isinstance(value_node, dict):
            return False
        return _is_wrapper_container_expr(ctx, value_node, _emit_expr(ctx, value_node))
    if kind != "Name":
        return False
    name = _str(node, "id")
    if name == "":
        return False
    safe_name = _go_symbol_name(ctx, name)
    scope_type = ctx.var_types.get(safe_name, "")
    if not _is_container_resolved_type(scope_type):
        return False
    return not _prefer_value_container_local(ctx, name, scope_type)


def _go_symbol_name(ctx: EmitContext, name: str) -> str:
    if name == "":
        return ""
    base = _safe_go_ident(name)
    if name in ctx.module_private_symbols and name.startswith("_"):
        prefix = _module_prefix(ctx)
        if prefix != "":
            return prefix + "__" + base.lstrip("_")
    return base


def _short_type_name(type_name: str) -> str:
    if "." in type_name:
        return type_name.rsplit(".", 1)[-1]
    return type_name


def _exception_bounds(ctx: EmitContext, type_name: str) -> tuple[int, int]:
    short_name = _short_type_name(type_name)
    if short_name in ctx.builtin_exc_bounds:
        return ctx.builtin_exc_bounds[short_name]
    exact = ctx.exception_type_bounds.get(type_name)
    if exact is not None:
        return exact
    for fqcn, bounds in ctx.exception_type_bounds.items():
        if _short_type_name(fqcn) == short_name:
            return bounds
    return (0, 0)


def _is_nominal_type_name(ctx: EmitContext, type_name: str) -> bool:
    short_name = _short_type_name(type_name)
    return (
        type_name in ctx.class_names
        or type_name in ctx.trait_names
        or type_name in ctx.enum_bases
        or short_name in ctx.builtin_exc_bounds
        or type_name in ctx.exception_type_ids
        or short_name in ctx.exception_type_ids
    )


def _is_builtin_exception_type_name(ctx: EmitContext, type_name: str) -> bool:
    return _short_type_name(type_name) in ctx.builtin_exc_bounds


def _exception_ctor_expr(ctx: EmitContext, type_name: str, message_code: str) -> str:
    short_name = _short_type_name(type_name)
    if short_name in ctx.builtin_exc_ctor_types:
        return "New" + _safe_go_ident(short_name) + "(" + message_code + ")"
    return "pytraNewRuntimeError(" + message_code + ")"


def _handler_type_name(handler: dict[str, JsonVal]) -> str:
    type_name = _str(handler, "type")
    if type_name != "":
        return type_name
    type_node = handler.get("type")
    if isinstance(type_node, dict):
        name = _str(type_node, "id")
        if name != "":
            return name
        return _str(type_node, "repr")
    return ""


def _is_exception_type_name(ctx: EmitContext, type_name: str) -> bool:
    short_name = _short_type_name(type_name)
    if short_name in ctx.builtin_exc_bounds:
        return True
    seen: set[str] = set()
    cur = short_name
    while cur != "" and cur not in seen:
        seen.add(cur)
        if cur in ctx.builtin_exc_bounds:
            return True
        base = ctx.class_bases.get(cur, "")
        if base == "":
            return False
        cur = _short_type_name(base)
    return False


def _exception_type_id(ctx: EmitContext, type_name: str) -> int:
    short_name = _short_type_name(type_name)
    if short_name in ctx.builtin_exc_bounds:
        return ctx.builtin_exc_bounds[short_name][0]
    exact = ctx.exception_type_ids.get(type_name)
    if exact is not None:
        return exact
    for fqcn, type_id in ctx.exception_type_ids.items():
        if _short_type_name(fqcn) == short_name:
            return type_id
    bounds = _exception_bounds(ctx, type_name)
    return bounds[0]


def _linked_type_id(ctx: EmitContext, type_name: str) -> int | None:
    exact = ctx.class_type_ids.get(type_name)
    if exact is not None:
        return exact
    short_name = _short_type_name(type_name)
    for fqcn, type_id in ctx.class_type_ids.items():
        if _short_type_name(fqcn) == short_name:
            return type_id
    return None


def _exception_struct_literal(ctx: EmitContext, type_name: str, message_code: str) -> str:
    type_id = _exception_type_id(ctx, type_name)
    bounds = _exception_bounds(ctx, type_name)
    short_name = _short_type_name(type_name)
    return (
        "PytraErrorCarrier{"
        + "TypeId: " + str(type_id)
        + ", TypeMin: " + str(bounds[0])
        + ", TypeMax: " + str(bounds[1])
        + ", Name: " + _go_string_literal(short_name)
        + ", Msg: " + message_code
        + "}"
    )


def _exception_embed_field(ctx: EmitContext, name: str, base: str) -> str:
    return "PytraErrorCarrier"


def _exception_embed_init_expr(ctx: EmitContext, name: str, base: str, message_code: str) -> str:
    return _exception_struct_literal(ctx, name, message_code)


def _is_exception_super_init_stmt(stmt: JsonVal) -> bool:
    if not isinstance(stmt, dict) or _str(stmt, "kind") != "Expr":
        return False
    value = stmt.get("value")
    if not isinstance(value, dict) or _str(value, "kind") != "Call":
        return False
    func = value.get("func")
    if not isinstance(func, dict) or _str(func, "kind") != "Attribute":
        return False
    if _str(func, "attr") != "__init__":
        return False
    owner = func.get("value")
    if not isinstance(owner, dict) or _str(owner, "kind") != "Call":
        return False
    if len(_list(owner, "args")) != 0:
        return False
    super_func = owner.get("func")
    return isinstance(super_func, dict) and _str(super_func, "kind") == "Name" and _str(super_func, "id") == "super"


def _exception_super_init_message_expr(
    ctx: EmitContext,
    body: list[JsonVal],
    fallback_expr: str,
) -> str:
    for stmt in body:
        if not _is_exception_super_init_stmt(stmt):
            continue
        if not isinstance(stmt, dict):
            continue
        value = stmt.get("value")
        if not isinstance(value, dict):
            continue
        args = _list(value, "args")
        if len(args) >= 1 and isinstance(args[0], dict):
            if _str(args[0], "kind") == "Name":
                arg_name = _str(args[0], "id")
                if arg_name != "":
                    return _safe_go_ident(arg_name)
            return _emit_expr(ctx, args[0])
    return fallback_expr


def _is_exception_subtype_name(ctx: EmitContext, actual_type_name: str, expected_type_name: str) -> bool:
    actual = _short_type_name(actual_type_name)
    expected = _short_type_name(expected_type_name)
    seen: set[str] = set()
    cur = actual
    while cur != "" and cur not in seen:
        if cur == expected:
            return True
        seen.add(cur)
        cur = _short_type_name(ctx.class_bases.get(cur, ""))
    return False


def _exception_match_condition(ctx: EmitContext, err_name: str, type_name: str) -> str:
    conds: list[str] = []
    bounds = _exception_bounds(ctx, type_name)
    if bounds != (0, 0):
        conds.append(
            "pytraErrorIsInstance(" + err_name + ", " + str(bounds[0]) + ", " + str(bounds[1]) + ")"
        )
    short_name = _short_type_name(type_name)
    for fqcn, derived_bounds in ctx.exception_type_bounds.items():
        if _short_type_name(fqcn) == short_name:
            continue
        if not _is_exception_subtype_name(ctx, fqcn, type_name):
            continue
        derived_cond = (
            "pytraErrorIsInstance(" + err_name + ", "
            + str(derived_bounds[0]) + ", " + str(derived_bounds[1]) + ")"
        )
        if derived_cond not in conds:
            conds.append(derived_cond)
    if len(conds) == 0:
        return err_name + " != nil"
    return " || ".join(conds)


def _go_enum_const_name(ctx: EmitContext, type_name: str, member_name: str) -> str:
    return _go_symbol_name(ctx, type_name + "_" + member_name)


def _go_polymorphic_iface_name(ctx: EmitContext, type_name: str) -> str:
    return "__pytra_iface_" + _go_symbol_name(ctx, type_name)


def _upper_snake(name: str) -> str:
    if name == "":
        return ""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.upper()


def _is_polymorphic_class(ctx: EmitContext, type_name: str) -> bool:
    return type_name in ctx.class_bases.values() or type_name in ctx.trait_names


def _ancestor_class_chain(ctx: EmitContext, type_name: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    cur_name = type_name.lstrip("*")
    if "." in cur_name:
        cur_name = cur_name.rsplit(".", 1)[-1]

    def _lookup_base(name: str) -> str:
        direct = ctx.class_bases.get(name, "")
        if direct != "":
            return direct
        suffix = "." + name
        for key, value in ctx.class_bases.items():
            if key == name or key.endswith(suffix):
                return value
        return ""

    cur = _lookup_base(cur_name)
    while cur != "" and cur not in ("object", "ABC") and cur not in seen:
        seen.add(cur)
        cur_short = cur.rsplit(".", 1)[-1] if "." in cur else cur
        out.append(cur_short)
        cur = _lookup_base(cur)
    return out


def _is_trait_class(node: dict[str, JsonVal]) -> bool:
    meta = _dict(node, "meta")
    return len(_dict(meta, "trait_v1")) > 0


def _go_signature_type(ctx: EmitContext, resolved_type: str) -> str:
    if _is_container_resolved_type(resolved_type):
        return _go_ref_container_type(ctx, resolved_type)
    if resolved_type in ctx.union_type_aliases:
        return "any"
    if resolved_type in ctx.enum_bases:
        return _go_symbol_name(ctx, resolved_type)
    if resolved_type in ctx.trait_names:
        return _go_symbol_name(ctx, resolved_type)
    if _is_polymorphic_class(ctx, resolved_type):
        return _go_polymorphic_iface_name(ctx, resolved_type)
    if resolved_type in ctx.class_names:
        return "*" + _go_symbol_name(ctx, resolved_type)
    return _go_type_with_ctx(ctx, resolved_type)


def _go_type_with_ctx(ctx: EmitContext, resolved_type: str) -> str:
    if resolved_type == "" or resolved_type == "unknown":
        return "any"
    mapped_type = ctx.mapping.types.get(resolved_type, "")
    if isinstance(mapped_type, str) and mapped_type != "":
        return mapped_type
    if (
        len(resolved_type) == 1
        and resolved_type[:1].isupper()
        and resolved_type not in ctx.class_names
        and resolved_type not in ctx.trait_names
        and resolved_type not in ctx.enum_bases
        and resolved_type not in ctx.union_type_aliases
    ):
        return "any"

    if (resolved_type.startswith("callable[") or resolved_type.startswith("Callable[")) and resolved_type.endswith("]"):
        params, ret = _parse_callable_signature(resolved_type)
        param_gts = [_go_type_with_ctx(ctx, param) for param in params]
        ret_gt = _go_type_with_ctx(ctx, ret)
        if ret_gt == "":
            return "func(" + ", ".join(param_gts) + ")"
        return "func(" + ", ".join(param_gts) + ") " + ret_gt

    if resolved_type.startswith("multi_return[") and resolved_type.endswith("]"):
        inner = resolved_type[len("multi_return["):-1]
        parts = _split_generic_args(inner)
        return "(" + ", ".join(_go_signature_type(ctx, part) for part in parts) + ")"

    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "[]" + _go_type_with_ctx(ctx, inner)

    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner2 = resolved_type[5:-1]
        parts = _split_generic_args(inner2)
        if len(parts) == 2:
            return "map[" + _go_type_with_ctx(ctx, parts[0]) + "]" + _go_type_with_ctx(ctx, parts[1])

    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner3 = resolved_type[4:-1]
        return "map[" + _go_type_with_ctx(ctx, inner3) + "]struct{}"

    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        return "PyTuple"

    if resolved_type in ctx.enum_bases:
        return _go_symbol_name(ctx, resolved_type)

    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner4 = resolved_type[:-7] if resolved_type.endswith(" | None") else resolved_type[:-5]
        inner4 = inner4.strip()
        gt = _go_signature_type(ctx, inner4)
        if gt.startswith("*") or gt == "any" or gt.startswith("[]") or gt.startswith("map[") or gt.startswith("func("):
            return gt
        return "*" + gt

    if "|" in resolved_type:
        parts2 = [part.strip() for part in resolved_type.split("|") if part.strip() != ""]
        if len(parts2) > 1:
            return "any"

    mapped = go_type(resolved_type)
    if resolved_type in ("None", "none"):
        return mapped
    if mapped != "" and mapped != ("*" + _safe_go_ident(resolved_type)):
        return mapped

    return "*" + _go_symbol_name(ctx, resolved_type)


def _is_zero_arg_super_call(node: JsonVal) -> bool:
    if not isinstance(node, dict) or _str(node, "kind") != "Call":
        return False
    func = node.get("func")
    if not isinstance(func, dict) or _str(func, "kind") != "Name":
        return False
    if _str(func, "id") != "super":
        return False
    return len(_list(node, "args")) == 0


def _interface_method_signature(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "name")
    if name == "" or name == "__init__":
        return ""
    decorators = _list(node, "decorators")
    for d in decorators:
        if isinstance(d, str) and d == "staticmethod":
            return ""
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    return_type = _str(node, "return_type")
    params: list[str] = []
    for a in arg_order:
        a_name = a if isinstance(a, str) else ""
        if a_name == "self":
            continue
        a_type_val = arg_types.get(a_name, "")
        a_type = a_type_val if isinstance(a_type_val, str) else ""
        params.append(_safe_go_ident(a_name) + " " + _go_signature_type(ctx, a_type))
    ret = _go_signature_type(ctx, return_type)
    ret_clause = " " + ret if ret != "" and return_type != "None" else ""
    return _safe_go_ident(name) + "(" + ", ".join(params) + ")" + ret_clause


def _effective_instance_methods(ctx: EmitContext, class_name: str) -> dict[str, dict[str, JsonVal]]:
    methods: dict[str, dict[str, JsonVal]] = {}
    base = ctx.class_bases.get(class_name, "")
    if base != "":
        methods.update(_effective_instance_methods(ctx, base))
    methods.update(ctx.class_instance_methods.get(class_name, {}))
    return methods


# ---------------------------------------------------------------------------
# Node accessors (safe typed access to EAST3 JSON)
# ---------------------------------------------------------------------------

def _str(node: dict[str, JsonVal], key: str) -> str:
    v = node.get(key)
    return v if isinstance(v, str) else ""


def _int(node: dict[str, JsonVal], key: str) -> int:
    v = node.get(key)
    return v if isinstance(v, int) else 0


def _bool(node: dict[str, JsonVal], key: str) -> bool:
    v = node.get(key)
    return v if isinstance(v, bool) else False


def _list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    v = node.get(key)
    return v if isinstance(v, list) else []


def _dict(node: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    v = node.get(key)
    return v if isinstance(v, dict) else {}


# ---------------------------------------------------------------------------
# Expression emission
# ---------------------------------------------------------------------------

def _emit_expr(ctx: EmitContext, node: JsonVal) -> str:
    """Emit an expression node and return Go code string."""
    if not isinstance(node, dict):
        return "nil"
    renderer = _GoExprCommonRenderer(ctx)
    return renderer.render_expr(node)


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
    if kind == "CovariantCopy":
        return _emit_covariant_copy(ctx, node)
    if kind == "IfExp":
        return _emit_ifexp(ctx, node)
    if kind == "JoinedStr":
        return _emit_fstring(ctx, node)
    if kind == "FormattedValue":
        return _emit_formatted_value(ctx, node)
    if kind == "Lambda":
        return _emit_lambda(ctx, node)
    if kind == "Slice":
        return _emit_slice_expr(ctx, node)
    if kind == "IsInstance":
        return _emit_isinstance(ctx, node)
    if kind == "Unbox":
        return _emit_unbox(ctx, node)
    if kind == "Box":
        return _emit_box(ctx, node)
    if kind == "ObjStr":
        arg = node.get("value")
        return "py_str(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjLen":
        arg = node.get("value")
        return "py_len(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjBool":
        arg = node.get("value")
        return "py_bool(" + _emit_expr(ctx, arg) + ")"
    if kind == "ObjTypeId":
        return _emit_obj_type_id(ctx, node)
    if kind == "IsSubtype":
        return _emit_issubtype(ctx, node)
    if kind == "IsSubclass":
        return _emit_issubclass(ctx, node)
    if kind == "ListComp":
        return _emit_list_comp(ctx, node)
    if kind == "SetComp":
        return _emit_set_comp(ctx, node)
    if kind == "DictComp":
        return _emit_dict_comp(ctx, node)

    if kind == "RangeExpr":
        return _emit_range_expr(ctx, node)

    raise RuntimeError("unsupported_expr_kind: " + kind)


def _emit_obj_type_id(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    value_expr = _emit_expr(ctx, value)
    value_type = _str(value, "resolved_type") if isinstance(value, dict) else ""
    # Only use __pytra_type_id() for concrete user classes (not object/any/exceptions).
    linked = _linked_type_id(ctx, value_type)
    value_gt = go_type(value_type)
    if linked is not None and value_gt != "any" and not _is_exception_type_name(ctx, value_type):
        # Call __pytra_type_id() on the expression so the variable is referenced in Go.
        return value_expr + ".__pytra_type_id()"
    if _is_exception_type_name(ctx, value_type):
        return "int64(" + str(_exception_type_id(ctx, value_type)) + ")"
    value_name = _next_temp(ctx, "obj_tid_value")
    return (
        "func() int64 {\n"
        + "\t" + value_name + " := any(" + value_expr + ")\n"
        + "\tswitch t := " + value_name + ".(type) {\n"
        + "\tcase *PytraErrorCarrier:\n"
        + "\t\treturn t.TypeId\n"
        + "\tcase interface{ pytraErrorBase() *PytraErrorCarrier }:\n"
        + "\t\tbase := t.pytraErrorBase()\n"
        + "\t\tif base != nil {\n"
        + "\t\t\treturn base.TypeId\n"
        + "\t\t}\n"
        + "\tcase interface{ __pytra_type_id() int64 }:\n"
        + "\t\treturn t.__pytra_type_id()\n"
        + "\t}\n"
        + "\treturn pytraEnsureRecoveredError(" + value_name + ").TypeId\n"
        + "}()"
    )


def _emit_issubtype(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    actual = _emit_expr(ctx, node.get("actual_type_id"))
    expected = _emit_expr(ctx, node.get("expected_type_id"))
    if actual == "" or expected == "":
        return "false"
    actual_name = _next_temp(ctx, "__pytra_actual_tid")
    expected_name = _next_temp(ctx, "__pytra_expected_tid")
    index_name = _next_temp(ctx, "__pytra_tid_idx")
    return (
        "func() bool {\n"
        + "\t" + actual_name + " := " + actual + "\n"
        + "\t" + expected_name + " := " + expected + "\n"
        + "\tfor " + index_name + " := 0; " + index_name + "+1 < len(id_table.items); " + index_name + " += 2 {\n"
        + "\t\tif id_table.items[" + index_name + "] == " + expected_name + " {\n"
        + "\t\t\treturn " + actual_name + " >= " + expected_name + " && " + actual_name + " <= id_table.items[" + index_name + "+1]\n"
        + "\t\t}\n"
        + "\t}\n"
        + "\treturn " + actual_name + " == " + expected_name + "\n"
        + "}()"
    )


def _emit_issubclass(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    actual = _emit_expr(ctx, node.get("actual_type_id"))
    expected = _emit_expr(ctx, node.get("expected_type_id"))
    if actual == "" or expected == "":
        return "false"
    actual_name = _next_temp(ctx, "__pytra_actual_tid")
    expected_name = _next_temp(ctx, "__pytra_expected_tid")
    index_name = _next_temp(ctx, "__pytra_tid_idx")
    return (
        "func() bool {\n"
        + "\t" + actual_name + " := " + actual + "\n"
        + "\t" + expected_name + " := " + expected + "\n"
        + "\tfor " + index_name + " := 0; " + index_name + "+1 < len(id_table.items); " + index_name + " += 2 {\n"
        + "\t\tif id_table.items[" + index_name + "] == " + expected_name + " {\n"
        + "\t\t\treturn " + actual_name + " >= " + expected_name + " && " + actual_name + " <= id_table.items[" + index_name + "+1]\n"
        + "\t\t}\n"
        + "\t}\n"
        + "\treturn " + actual_name + " == " + expected_name + "\n"
        + "}()"
    )


def _emit_constant(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    val = node.get("value")
    rt = _str(node, "resolved_type")
    if val is None:
        return "nil"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, int):
        if rt in ("float64", "float32", "float"):
            return str(float(val))
        if rt in ("int", "int64"):
            return "int64(" + str(val) + ")"
        if rt == "int32":
            return "int32(" + str(val) + ")"
        if rt == "int16":
            return "int16(" + str(val) + ")"
        if rt == "int8":
            return "int8(" + str(val) + ")"
        if rt == "uint8":
            return "uint8(" + str(val) + ")"
        if rt == "uint16":
            return "uint16(" + str(val) + ")"
        if rt == "uint32":
            return "uint32(" + str(val) + ")"
        if rt == "uint64":
            return "uint64(" + str(val) + ")"
        return str(val)
    if isinstance(val, float):
        s = repr(val)
        if s == "inf":
            ctx.imports_needed.add(ctx.go_pkg_math)
            return "math.Inf(1)"
        if s == "-inf":
            ctx.imports_needed.add(ctx.go_pkg_math)
            return "math.Inf(-1)"
        return s
    if isinstance(val, str):
        # Go string literal
        return _go_string_literal(val)
    return repr(val)


def _go_string_literal(s: str) -> str:
    """Encode a string as a Go string literal."""
    out: list[str] = ['"']
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 32:
            out.append("\\x" + format(ord(ch), "02x"))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _emit_name(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "":
        name = _str(node, "repr")
    if name == "__file__":
        return _go_string_literal(ctx.source_path)
    if name == "True":
        return "true"
    if name == "False":
        return "false"
    if name == "None":
        return "nil"
    if name == "self" and ctx.current_receiver != "":
        return ctx.current_receiver
    # Go control flow keywords used as statements
    if name == "continue":
        return "continue"
    if name == "break":
        return "break"
    # Avoid collision with Go's main()
    if name == "main":
        return _go_symbol_name(ctx, "__pytra_main")
    safe_name = _go_symbol_name(ctx, name)
    resolved_type = _str(node, "resolved_type")
    if (resolved_type.startswith("callable[") or resolved_type.startswith("Callable[")) and resolved_type.endswith("]"):
        return safe_name
    scope_type = ctx.var_types.get(safe_name, "")
    if (
        resolved_type != ""
        and resolved_type != "unknown"
        and (scope_type == "" or scope_type == "unknown")
        and (
            resolved_type == "Node"
            or resolved_type.startswith("dict[")
            or resolved_type.startswith("list[")
            or resolved_type.startswith("set[")
            or resolved_type.startswith("tuple[")
        )
    ):
        return safe_name
    scope_optional_inner = _optional_inner_type(scope_type)
    if (
        resolved_type != ""
        and scope_optional_inner != ""
        and resolved_type == scope_optional_inner
        and go_type(scope_type).startswith("*")
    ):
        if not go_type(resolved_type).startswith("*"):
            # Scalar optional (e.g. *int64 → int64): dereference to get value
            return "(*(" + safe_name + "))"
        # Pointer types (user classes): optional and non-optional share same Go repr
    if (
        resolved_type != ""
        and resolved_type != scope_type
        and (
            scope_type in ("JsonVal", "Any", "Obj", "object", "unknown")
            or go_type(scope_type) == "any"
        )
    ):
        if go_type(resolved_type).startswith("*") and not _is_nominal_type_name(ctx, resolved_type):
            return safe_name
        return _coerce_from_any(safe_name, resolved_type)
    if safe_name in ctx.list_alias_vars:
        return "(*" + safe_name + ")"
    return safe_name


def _emit_binop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    right_node = node.get("right")
    left_code = _emit_expr(ctx, left_node)
    right_code = _emit_expr(ctx, right_node)
    op = _str(node, "op")
    go_op = _BINOP_MAP.get(op, "+")
    rt = _str(node, "resolved_type")
    left_rt = _effective_resolved_type(ctx, left_node)
    right_rt = _effective_resolved_type(ctx, right_node)

    if op == "Div" and ctx.path_type_name and left_rt == ctx.path_type_name and right_rt == "str":
        return left_code + ".joinpath(" + right_code + ")"
    # Set union: handles set[str], set, and mixed typed sets
    if op == "BitOr" and (
        left_rt.startswith("set") or right_rt.startswith("set")
        or left_code.startswith("PySetFromMap[") or left_code.startswith("NewPySet[")
        or right_code.startswith("PySetFromMap[") or right_code.startswith("NewPySet[")
    ):
        def _unwrap_pyset_to_map(code: str) -> str:
            if code.startswith("PySetFromMap[") or code.startswith("NewPySet["):
                return code + ".items"
            return code
        # Convert any *PySet[T].items to map[string]struct{} (string coercion assumed safe)
        lm = _unwrap_pyset_to_map(left_code)
        rm = _unwrap_pyset_to_map(right_code)
        # If items is map[any]struct{}, cast individual entries via py_set_str helper
        if lm.endswith(".items") and "[any]" in lm:
            lm = "py_set_str(" + lm + ")"
        if rm.endswith(".items") and "[any]" in rm:
            rm = "py_set_str(" + rm + ")"
        return "py_set_union_str(" + lm + ", " + rm + ")"

    # Apply casts from EAST3
    casts = _list(node, "casts")
    for cast in casts:
        if not isinstance(cast, dict):
            continue
        on = _str(cast, "on")
        to_type = _str(cast, "to")
        gt = go_type(to_type)
        if on == "left":
            left_code = gt + "(" + left_code + ")"
        elif on == "right":
            right_code = gt + "(" + right_code + ")"

    # List multiplication: [V] * N → make + fill if V != 0
    if op == "Mult":
        if left_rt == "str" and right_rt in ("int64", "int32", "int", "uint8", "int8"):
            return "py_repeat_string(" + left_code + ", " + right_code + ")"
        if right_rt == "str" and left_rt in ("int64", "int32", "int", "uint8", "int8"):
            return "py_repeat_string(" + right_code + ", " + left_code + ")"
        if left_rt.startswith("list[") and right_rt in ("int64", "int32", "int", "uint8", "int8"):
            return "py_repeat_slice(" + left_code + ", " + right_code + ")"
        if right_rt.startswith("list[") and left_rt in ("int64", "int32", "int", "uint8", "int8"):
            return "py_repeat_slice(" + right_code + ", " + left_code + ")"

    if op == "Add":
        if left_rt.startswith("list[") and right_rt.startswith("list["):
            left_code = _wrapper_container_storage_expr(ctx, left_node, left_code)
            right_code = _wrapper_container_storage_expr(ctx, right_node, right_code)
            return "py_concat_slice(" + left_code + ", " + right_code + ")"

    # Integer division
    if op == "Div" and rt in ("int64", "int32", "int", "int8", "int16", "uint8"):
        return "(" + left_code + " / " + right_code + ")"
    if op == "Div" and rt in ("float", "float64", "float32"):
        target_gt = go_type(rt)
        if target_gt == "":
            target_gt = "float64"
        return "(" + target_gt + "(" + left_code + ") / " + target_gt + "(" + right_code + "))"
    # Floor division
    if op == "FloorDiv":
        return "py_floordiv(" + left_code + ", " + right_code + ")"
    # Power
    if op == "Pow":
        ctx.imports_needed.add(ctx.go_pkg_math)
        return "math.Pow(float64(" + left_code + "), float64(" + right_code + "))"

    int_like_types = {
        "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "int",
    }
    if op in ("Add", "Sub", "Mult") and rt in int_like_types and left_rt in int_like_types and right_rt in int_like_types:
        target_gt = go_type(rt)
        left_gt = go_type(left_rt)
        right_gt = go_type(right_rt)
        if target_gt not in ("", "any") and (left_gt != target_gt or right_gt != target_gt):
            return "(" + target_gt + "(" + left_code + ") " + go_op + " " + target_gt + "(" + right_code + "))"

    return "(" + left_code + " " + go_op + " " + right_code + ")"


def _effective_resolved_type(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    kind = _str(node, "kind")
    if kind in ("Box", "Unbox"):
        inner = node.get("value")
        if isinstance(inner, dict):
            inner_rt = _effective_resolved_type(ctx, inner)
            if inner_rt not in ("", "unknown"):
                return inner_rt
    resolved_type = _str(node, "resolved_type")
    if kind == "Name":
        name = _safe_go_ident(_str(node, "id"))
        scope_type = ctx.var_types.get(name, "")
        if scope_type not in ("", "unknown"):
            return scope_type
    if kind == "Attribute":
        owner_node = node.get("value")
        owner_rt = _effective_resolved_type(ctx, owner_node)
        if owner_rt in ("", "unknown") and isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
            owner_rt = ctx.current_class
        field_type = ctx.class_fields.get(owner_rt, {}).get(_str(node, "attr"), "")
        if field_type not in ("", "unknown"):
            return field_type
    return resolved_type


def _coerce_from_any(val_code: str, target_type: str) -> str:
    # Container types: actual runtime values are *PyList/PyDict/PySet, not native slices/maps.
    # Generate type assertions to wrapper types so the cast succeeds at runtime.
    if _is_container_resolved_type(target_type):
        if val_code.startswith("py_items(") and (target_type == "list" or target_type.startswith("list[")):
            return val_code
        if target_type == "list" or (target_type.startswith("list[") and target_type.endswith("]")):
            elem_type = "any"
            if target_type.startswith("list[") and target_type.endswith("]"):
                elem_type = go_type(target_type[5:-1])
            return "py_to_list_typed[" + elem_type + "](" + val_code + ")"
        wrapper_gt = _container_wrapper_go_type(target_type)
        if val_code.endswith(".(" + wrapper_gt + ")"):
            return val_code
        return val_code + ".(" + wrapper_gt + ")"
    target_gt = go_type(target_type)
    if target_gt == "":
        return val_code
    if val_code.endswith(".(" + target_gt + ")"):
        return val_code
    if target_gt == "string" and val_code.startswith("py_repeat_string("):
        return val_code
    if target_gt == "string":
        return val_code + ".(string)"
    if target_gt == "bool":
        return val_code + ".(bool)"
    if target_gt == "float64":
        return "py_to_float64(" + val_code + ")"
    if target_gt == "float32":
        return "float32(py_to_float64(" + val_code + "))"
    if target_gt == "int64":
        return "py_to_int64(" + val_code + ")"
    if target_gt == "int32":
        return "int32(py_to_int64(" + val_code + "))"
    if target_gt == "int16":
        return "int16(py_to_int64(" + val_code + "))"
    if target_gt == "int8":
        return "int8(py_to_int64(" + val_code + "))"
    if target_gt == "uint8":
        return "uint8(py_to_int64(" + val_code + "))"
    if target_gt == "uint16":
        return "uint16(py_to_int64(" + val_code + "))"
    if target_gt == "uint32":
        return "uint32(py_to_int64(" + val_code + "))"
    if target_gt == "uint64":
        return "uint64(py_to_int64(" + val_code + "))"
    if target_gt == "any":
        return val_code
    return val_code + ".(" + target_gt + ")"


def _container_wrapper_go_type(resolved_type: str) -> str:
    """Return the Go wrapper type for a container type (no ctx needed for common cases)."""
    if resolved_type == "list":
        return "*PyList[any]"
    if resolved_type == "dict":
        return "*PyDict[string, any]"
    if resolved_type == "set":
        return "*PySet[any]"
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "*PyList[" + go_type(inner) + "]"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            return "*PyDict[" + go_type(parts[0]) + ", " + go_type(parts[1]) + "]"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        elem_gt = "string" if inner.startswith("tuple[") and inner.endswith("]") else go_type(inner)
        return "*PySet[" + elem_gt + "]"
    return go_type(resolved_type)


def _first_union_member(resolved_type: str, prefix: str) -> str:
    if not _is_top_level_union_type(resolved_type):
        return ""
    for part in _split_top_level_union(resolved_type):
        item = part.strip()
        if item == prefix or item.startswith(prefix + "["):
            return item
    return ""


def _split_top_level_union(resolved_type: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    for i, ch in enumerate(resolved_type):
        if ch == "[":
            depth += 1
        elif ch == "]" and depth > 0:
            depth -= 1
        elif ch == "|" and depth == 0:
            parts.append(resolved_type[start:i])
            start = i + 1
    parts.append(resolved_type[start:])
    return parts


def _is_top_level_union_type(resolved_type: str) -> bool:
    return len(_split_top_level_union(resolved_type)) > 1


def _maybe_coerce_expr_to_type(ctx: EmitContext, value_node: JsonVal, value_code: str, target_type: str) -> str:
    if not isinstance(value_node, dict):
        return value_code
    source_type = _str(value_node, "resolved_type")
    if target_type.startswith("tuple[") and source_type.startswith("tuple[") and _str(value_node, "kind") == "Call":
        return "py_tuple_any(" + value_code + ")"
    target_gt = go_type(target_type)
    int_like_gts = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64", "int"}
    if _str(value_node, "kind") == "BinOp" and target_gt in int_like_gts:
        return target_gt + "(" + value_code + ")"
    if _is_container_resolved_type(target_type):
        if _is_wrapper_container_expr(ctx, value_node, value_code):
            return value_code
        return _wrap_ref_container_value_code(ctx, value_code, target_type)
    if _str(value_node, "kind") == "Call" and source_type in ("", "unknown"):
        if target_gt != "" and target_gt != "any":
            return value_code
    if target_type == "str" and _str(value_node, "kind") == "BinOp":
        return value_code
    if source_type == "" or source_type == target_type:
        return value_code
    source_gt = go_type(source_type)
    if target_gt == "" or target_gt == "any" or source_gt == target_gt:
        return value_code
    if (
        source_type in ("Callable", "callable")
        and target_gt.startswith("func(")
    ):
        return value_code
    source_optional_inner = _optional_inner_type(source_type)
    if source_optional_inner != "" and go_type(source_optional_inner) == target_gt:
        if source_gt.startswith("*") and not target_gt.startswith("*"):
            # Scalar optional (e.g. *int64 → int64): dereference to get value
            return "(*(" + value_code + "))"
        # Pointer/interface types: optional and non-optional share same Go repr (nil = None)
        return value_code
    optional_inner = _optional_inner_type(target_type)
    if optional_inner != "":
        if source_type in ("JsonVal", "Any", "Obj", "object", "unknown") or source_gt == "any":
            return _wrap_optional_value_code(ctx, _coerce_from_any(value_code, optional_inner), target_type, value_node)
        return _wrap_optional_value_code(ctx, value_code, target_type, value_node)
    if source_type in ("JsonVal", "Any", "Obj", "object", "unknown") or source_gt == "any":
        return _coerce_from_any(value_code, target_type)
    # *PyDict[K,V] → map[K]V: extract .items (coercion from container wrapper to native map)
    if target_gt.startswith("map[") and _is_container_resolved_type(source_type):
        if not value_code.endswith(".items"):
            return value_code + ".items"
        return value_code
    # Scalar numeric widening: int64 → float64 etc.
    _INT_GTS = ("int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64")
    if source_gt in _INT_GTS and target_gt in ("float64", "float32"):
        return target_gt + "(" + value_code + ")"
    if source_gt in _INT_GTS and target_gt in _INT_GTS and source_gt != target_gt:
        return target_gt + "(" + value_code + ")"
    return value_code


def _prefer_value_type_for_none_decl(decl_type: str, value: JsonVal) -> str:
    if decl_type not in ("None", "none"):
        return decl_type
    if isinstance(value, dict):
        if _str(value, "kind") == "Constant" and value.get("value") is None:
            return decl_type
        if _str(value, "kind") == "IfExp":
            body_node = value.get("body")
            orelse_node = value.get("orelse")
            if isinstance(body_node, dict):
                body_type = _str(body_node, "resolved_type")
                if body_type not in ("", "None", "none"):
                    return "any"
            if isinstance(orelse_node, dict):
                orelse_type = _str(orelse_node, "resolved_type")
                if orelse_type not in ("", "None", "none"):
                    return "any"
            return "any"
        value_type = _str(value, "resolved_type")
        if value_type not in ("", "None", "none"):
            return value_type
        return "any"
    return "any"


def _call_yields_dynamic(node: dict[str, JsonVal]) -> bool:
    return _bool(node, "yields_dynamic")


def _optional_inner_type(resolved_type: str) -> str:
    parts: list[str] = []
    cur: list[str] = []
    depth: int = 0
    for ch in resolved_type:
        if ch == "[":
            depth += 1
        elif ch == "]" and depth > 0:
            depth -= 1
        if ch == "|" and depth == 0:
            part = "".join(cur).strip()
            if part != "":
                parts.append(part)
            cur = []
            continue
        cur.append(ch)
    tail: str = "".join(cur).strip()
    if tail != "":
        parts.append(tail)
    if len(parts) != 2:
        return ""
    if parts[0] == "None":
        return parts[1]
    if parts[1] == "None":
        return parts[0]
    return ""


def _wrap_optional_resolved_code(ctx: EmitContext, value_code: str, inner_type: str) -> str:
    inner_gt = go_type(inner_type)
    # Container types (*PyList, *PyDict, *PySet) are already pointers — nil encodes None.
    if inner_gt == "" or inner_gt == "any" or inner_gt.startswith("*") or _is_container_resolved_type(inner_type):
        return value_code
    temp_name = _next_temp(ctx, "opt")
    return (
        "func() *" + inner_gt + " {\n"
        + "\tvar " + temp_name + " " + inner_gt + " = " + value_code + "\n"
        + "\treturn &" + temp_name + "\n"
        + "}()"
    )


def _wrap_optional_value_code(ctx: EmitContext, value_code: str, optional_type: str, value_node: JsonVal) -> str:
    inner_type = _optional_inner_type(optional_type)
    if inner_type == "":
        return value_code
    if ".as_obj()" in value_code or ".as_arr()" in value_code or ".as_str()" in value_code or ".as_int()" in value_code or ".as_float()" in value_code or ".as_bool()" in value_code:
        return value_code
    if value_code.startswith("NewJsonValue("):
        return value_code
    if value_code.startswith("NewJsonObj(") or value_code.startswith("NewJsonArr("):
        return value_code
    if value_code.startswith("pytra_std_json__jv_as_str(") or value_code.startswith("pytra_std_json__jv_as_int(") or value_code.startswith("pytra_std_json__jv_as_float(") or value_code.startswith("pytra_std_json__jv_as_bool("):
        return value_code
    if isinstance(value_node, dict) and _str(value_node, "kind") == "Constant" and value_node.get("value") is None:
        return "nil"
    if isinstance(value_node, dict):
        source_type = _str(value_node, "resolved_type")
        source_optional_inner = _optional_inner_type(source_type)
        if source_optional_inner != "":
            return value_code
        if _str(value_node, "kind") == "Name":
            scope_name = _go_symbol_name(ctx, _str(value_node, "id"))
            scope_type = ctx.var_types.get(scope_name, "")
            if scope_type == optional_type:
                return value_code
        inner_code = value_code
        if source_type in ("JsonVal", "Any", "Obj", "object", "unknown") or go_type(source_type) == "any":
            inner_code = _coerce_from_any(value_code, inner_type)
        return _wrap_optional_resolved_code(ctx, inner_code, inner_type)
    return _wrap_optional_resolved_code(ctx, value_code, inner_type)


def _emit_unbox(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    target_type = _str(node, "target")
    if target_type == "":
        target_type = _str(node, "resolved_type")
    value_node = node.get("value")
    source_type = _str(value_node, "resolved_type") if isinstance(value_node, dict) else ""
    target_gt = go_type(target_type)
    source_gt = go_type(source_type) if source_type != "" else ""
    if isinstance(value_node, dict) and _str(value_node, "kind") == "Call" and source_type in ("", "unknown") and target_gt != "" and target_gt != "any":
        return _emit_expr(ctx, value_node)
    if isinstance(value_node, dict) and _str(value_node, "resolved_type") == target_type:
        rendered0 = _emit_expr(ctx, value_node)
        if _is_container_resolved_type(target_type):
            return _wrapper_container_storage_expr(ctx, value_node, rendered0)
        return rendered0
    if isinstance(value_node, dict) and _str(value_node, "kind") == "Name":
        scope_name = _go_symbol_name(ctx, _str(value_node, "id"))
        scope_type = ctx.var_types.get(scope_name, "")
        if scope_type == target_type or (scope_type != "" and go_type(scope_type) == target_gt):
            rendered1 = _emit_expr(ctx, value_node)
            if _is_container_resolved_type(target_type):
                return _wrapper_container_storage_expr(ctx, value_node, rendered1)
            return rendered1
    if target_gt == "any":
        return _emit_expr(ctx, value_node)
    if target_gt != "" and target_gt != "any" and source_gt == target_gt:
        return _emit_expr(ctx, value_node)
    source_optional_inner = _optional_inner_type(source_type)
    if source_optional_inner != "" and go_type(source_optional_inner) == target_gt:
        if source_gt.startswith("*") and not target_gt.startswith("*"):
            # Scalar optional (e.g. *int64 → int64): dereference to get value
            return "(*(" + _emit_expr(ctx, value_node) + "))"
        # Pointer/interface types: optional and non-optional share same Go repr (nil = None)
        return _emit_expr(ctx, value_node)
    if isinstance(value_node, dict):
        if _str(value_node, "kind") == "Subscript" and target_type == "str":
            return _emit_expr(ctx, value_node)
        if _str(value_node, "kind") == "Name" and _str(value_node, "id") == "__file__" and target_type == "str":
            return _emit_expr(ctx, value_node)
        if _str(value_node, "kind") == "Constant" and isinstance(value_node.get("value"), str) and target_type == "str":
            return _emit_expr(ctx, value_node)
        if _str(value_node, "kind") == "Attribute":
            owner_node = value_node.get("value")
            owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            if owner_type not in ("", "JsonVal", "Any", "Obj", "object", "unknown"):
                return _emit_expr(ctx, value_node)
    if target_type in ctx.enum_bases:
        return _safe_go_ident(target_type) + "(" + _emit_expr(ctx, value_node) + ")"
    optional_inner = _optional_inner_type(target_type)
    if optional_inner != "":
        tmp_name = _next_temp(ctx, "unbox")
        inner_code = _coerce_from_any(tmp_name, optional_inner)
        wrapped = _wrap_optional_resolved_code(ctx, inner_code, optional_inner)
        target_gt = go_type(target_type)
        # Emit value expression as raw `any` so the nil check is valid.
        # dynamic-dispatch calls (yields_dynamic) coerce to a scalar type; skip that here.
        old_skip = ctx.skip_any_coercion
        ctx.skip_any_coercion = True
        raw_value_expr = _emit_expr(ctx, value_node)
        ctx.skip_any_coercion = old_skip
        return (
            "func() " + target_gt + " {\n"
            + "\t" + tmp_name + " := " + raw_value_expr + "\n"
            + "\tif " + tmp_name + " == nil {\n"
            + "\t\treturn nil\n"
            + "\t}\n"
            + "\treturn " + wrapped + "\n"
            + "}()"
        )
    if target_type == "dict[str,Any]":
        return "py_to_map_string_any(" + _emit_expr(ctx, value_node) + ")"
    return _coerce_from_any(_emit_expr(ctx, value_node), target_type)


def _box_dynamic_value_code(ctx: EmitContext, value_node: JsonVal) -> str:
    value_code = _emit_expr(ctx, value_node)
    source_type = _effective_resolved_type(ctx, value_node)
    if source_type in ("int", "int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"):
        return "int64(" + value_code + ")"
    if source_type in ("float", "float64", "float32"):
        return "float64(" + value_code + ")"
    if source_type.startswith("list[") or source_type == "list":
        # Box to *PyList[T] (not native []T) so type assertions from any use wrapper types.
        # List literals emit []T{...} and need wrapping; Call/Name expressions already return *PyList[T].
        if isinstance(value_node, dict) and _str(value_node, "kind") == "List":
            return _wrap_ref_container_value_code(ctx, value_code, source_type if source_type != "list" else "list")
        return value_code  # Already *PyList[T] (Call, Name, Attribute, etc.)
    if source_type.startswith("dict[") or source_type == "dict":
        # Box to *PyDict[K,V] (not native map) so type assertions from any use wrapper types.
        if isinstance(value_node, dict) and _str(value_node, "kind") == "Dict":
            return _wrap_ref_container_value_code(ctx, value_code, source_type if source_type != "dict" else "dict")
        return value_code  # Already *PyDict[K,V]
    if source_type.startswith("set[") or source_type == "set":
        if isinstance(value_node, dict) and _str(value_node, "kind") == "Set":
            return _wrap_ref_container_value_code(ctx, value_code, source_type if source_type != "set" else "set")
        return value_code  # Already *PySet[T]
    if source_type.startswith("tuple["):
        return _box_value_code(ctx, value_node, source_type)
    return value_code


def _box_value_code(ctx: EmitContext, value_node: JsonVal, target_type: str) -> str:
    target_gt = go_type(target_type)
    if target_type in ("Any", "object", "Obj", "unknown") or target_gt == "any":
        return _box_dynamic_value_code(ctx, value_node)
    if target_type.startswith("tuple[") and target_type.endswith("]"):
        elem_types = _split_generic_args(target_type[6:-1])
        if isinstance(value_node, dict):
            if _str(value_node, "kind") == "Tuple":
                elems = _list(value_node, "elements")
                parts = [_emit_expr(ctx, elem) for elem in elems]
                return "[]any{" + ", ".join(parts) + "}"
            if _str(value_node, "kind") == "Call" and len(elem_types) > 0:
                temp_names = [_next_temp(ctx, "tuple_elem") for _ in elem_types]
                return (
                    "func() []any {\n"
                    + "\t" + ", ".join(temp_names) + " := " + _emit_expr(ctx, value_node) + "\n"
                    + "\treturn []any{" + ", ".join(temp_names) + "}\n"
                    + "}()"
                )
        return _emit_expr(ctx, value_node)
    if target_type.startswith("list[") and target_type.endswith("]"):
        inner = target_type[5:-1]
        inner_gt = go_type(inner)
        source_elem_type = ""
        if isinstance(value_node, dict):
            source_type = _effective_resolved_type(ctx, value_node)
            if source_type.startswith("list[") and source_type.endswith("]"):
                source_elem_type = source_type[5:-1]
            elif source_type.startswith("tuple[") and source_type.endswith("]"):
                source_parts = _split_generic_args(source_type[6:-1])
                if len(source_parts) > 0:
                    source_elem_type = source_parts[0]
        if isinstance(value_node, dict) and _str(value_node, "kind") == "List":
            elems = _list(value_node, "elements")
            parts = [_box_value_code(ctx, elem, inner) for elem in elems]
            return "[]" + inner_gt + "{" + ", ".join(parts) + "}"
        src = _emit_expr(ctx, value_node)
        src = _wrapper_container_storage_expr(ctx, value_node, src)
        out_name = _next_temp(ctx, "boxed_list")
        elem_name = _next_temp(ctx, "boxed_item")
        return (
            "func() []" + inner_gt + " {\n"
            + "\t" + out_name + " := []" + inner_gt + "{}\n"
            + "\tfor _, " + elem_name + " := range " + src + " {\n"
            + "\t\t" + out_name + " = append(" + out_name + ", " + _box_value_code(ctx, {"kind": "Name", "id": elem_name, "resolved_type": source_elem_type}, inner) + ")\n"
            + "\t}\n"
            + "\treturn " + out_name + "\n"
            + "}()"
        )
    if target_type.startswith("dict[") and target_type.endswith("]"):
        parts = _split_generic_args(target_type[5:-1])
        if len(parts) == 2:
            key_type = parts[0]
            val_type = parts[1]
            key_gt = go_type(key_type)
            val_gt = go_type(val_type)
            source_key_type = key_type
            source_val_type = ""
            if isinstance(value_node, dict):
                source_type2 = _effective_resolved_type(ctx, value_node)
                if source_type2.startswith("dict[") and source_type2.endswith("]"):
                    source_parts2 = _split_generic_args(source_type2[5:-1])
                    if len(source_parts2) == 2:
                        source_key_type = source_parts2[0]
                        source_val_type = source_parts2[1]
            if isinstance(value_node, dict) and _str(value_node, "kind") == "Dict":
                entries = value_node.get("entries")
                if isinstance(entries, list):
                    rendered_entries: list[str] = []
                    for entry in entries:
                        if not isinstance(entry, dict):
                            continue
                        rendered_entries.append(
                            _box_value_code(ctx, entry.get("key"), key_type)
                            + ": "
                            + _box_value_code(ctx, entry.get("value"), val_type)
                        )
                    return "map[" + key_gt + "]" + val_gt + "{" + ", ".join(rendered_entries) + "}"
            src = _emit_expr(ctx, value_node)
            src = _wrapper_container_storage_expr(ctx, value_node, src)
            out_name = _next_temp(ctx, "boxed_dict")
            key_name = _next_temp(ctx, "boxed_key")
            val_name = _next_temp(ctx, "boxed_val")
            key_ref: dict[str, JsonVal] = {"kind": "Name", "id": key_name, "resolved_type": source_key_type}
            val_ref: dict[str, JsonVal] = {"kind": "Name", "id": val_name, "resolved_type": source_val_type}
            boxed_key = key_name if key_type == "str" else _box_value_code(ctx, key_ref, key_type)
            boxed_val = _box_value_code(ctx, val_ref, val_type)
            return (
                "func() map[" + key_gt + "]" + val_gt + " {\n"
                + "\t" + out_name + " := map[" + key_gt + "]" + val_gt + "{}\n"
                + "\tfor " + key_name + ", " + val_name + " := range " + src + " {\n"
                + "\t\t" + out_name + "[" + boxed_key + "] = " + boxed_val + "\n"
                + "\t}\n"
                + "\treturn " + out_name + "\n"
                + "}()"
            )
    return _emit_expr(ctx, value_node)


def _emit_box(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    target_type = _str(node, "target")
    if target_type == "":
        target_type = _str(node, "resolved_type")
    return _box_value_code(ctx, node.get("value"), target_type)


_BINOP_MAP: dict[str, str] = {
    "Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
    "Mod": "%", "BitOr": "|", "BitAnd": "&", "BitXor": "^",
    "LShift": "<<", "RShift": ">>",
}


def _emit_unaryop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    if op == "USub":
        return "(-" + operand + ")"
    if op == "Not":
        return "(!" + operand + ")"
    if op == "Invert":
        return "(^" + operand + ")"
    return operand


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    left = _emit_expr(ctx, left_node)
    # If left is byte-indexed (Subscript on bytes), cast to int64 for comparison
    left_rt = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
    if isinstance(left_node, dict) and _str(left_node, "kind") == "Name":
        left_name = _safe_go_ident(_str(left_node, "id"))
        if left_name in ctx.var_types and ctx.var_types[left_name] != "":
            left_rt = ctx.var_types[left_name]
    if left_rt == "uint8":
        left = "int64(" + left + ")"
    ops = _list(node, "ops")
    comparators = _list(node, "comparators")
    if len(ops) == 0 or len(comparators) == 0:
        return left

    parts: list[str] = []
    prev = left
    for i in range(len(ops)):
        op_str = ops[i] if isinstance(ops[i], str) else ""
        comp_node = comparators[i] if i < len(comparators) else None
        right = _emit_expr(ctx, comp_node)
        # Type coerce byte to int64 for comparison
        comp_rt = _str(comp_node, "resolved_type") if isinstance(comp_node, dict) else ""
        if isinstance(comp_node, dict):
            effective_comp_rt = _effective_resolved_type(ctx, comp_node)
            if effective_comp_rt not in ("", "unknown"):
                comp_rt = effective_comp_rt
        if isinstance(comp_node, dict) and _str(comp_node, "kind") == "Name":
            comp_name = _safe_go_ident(_str(comp_node, "id"))
            if comp_name in ctx.var_types and ctx.var_types[comp_name] != "":
                comp_rt = ctx.var_types[comp_name]
        if comp_rt == "uint8" and left_rt != "uint8":
            right = "int64(" + right + ")"

        if op_str == "In":
            if isinstance(comp_node, dict):
                right = _wrapper_container_storage_expr(ctx, comp_node, right)
                if comp_rt.startswith("tuple[") and _str(comp_node, "kind") == "Call":
                    right = "py_tuple_any(" + right + ")"
                if comp_rt.startswith("set[tuple["):
                    prev = "py_tuple_key(" + prev + ")"
            parts.append("py_contains(" + right + ", " + prev + ")")
        elif op_str == "NotIn":
            if isinstance(comp_node, dict):
                right = _wrapper_container_storage_expr(ctx, comp_node, right)
                if comp_rt.startswith("tuple[") and _str(comp_node, "kind") == "Call":
                    right = "py_tuple_any(" + right + ")"
                if comp_rt.startswith("set[tuple["):
                    prev = "py_tuple_key(" + prev + ")"
            parts.append("!py_contains(" + right + ", " + prev + ")")
        elif op_str == "Is":
            if isinstance(comp_node, dict) and _str(comp_node, "kind") == "Constant" and comp_node.get("value") is None:
                raw_prev = _safe_go_ident(_str(left_node, "id")) if isinstance(left_node, dict) and _str(left_node, "kind") == "Name" else prev
                parts.append("(" + raw_prev + " == nil)")
            else:
                parts.append("(" + prev + " == " + right + ")")
        elif op_str == "IsNot":
            if isinstance(comp_node, dict) and _str(comp_node, "kind") == "Constant" and comp_node.get("value") is None:
                raw_prev = _safe_go_ident(_str(left_node, "id")) if isinstance(left_node, dict) and _str(left_node, "kind") == "Name" else prev
                parts.append("(" + raw_prev + " != nil)")
            else:
                parts.append("(" + prev + " != " + right + ")")
        elif op_str == "Eq" and ((left_rt == "str" and comp_rt != "" and comp_rt != "str") or (comp_rt == "str" and left_rt != "" and left_rt != "str")):
            parts.append("py_eq(" + prev + ", " + right + ")")
        elif op_str == "NotEq" and ((left_rt == "str" and comp_rt != "" and comp_rt != "str") or (comp_rt == "str" and left_rt != "" and left_rt != "str")):
            parts.append("!py_eq(" + prev + ", " + right + ")")
        else:
            go_cmp = _COMPARE_MAP.get(op_str, "==")
            parts.append("(" + prev + " " + go_cmp + " " + right + ")")
        prev = right

    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


_COMPARE_MAP: dict[str, str] = {
    "Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=",
    "Gt": ">", "GtE": ">=",
}


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    op = _str(node, "op")
    values = _list(node, "values")
    if len(values) == 0:
        return "false"
    if len(values) == 1:
        return _emit_expr(ctx, values[0])

    result_type = go_type(_str(node, "resolved_type"))
    if result_type == "":
        result_type = "any"
    temp_name = _next_temp(ctx, "boolop")
    parts = [_emit_expr(ctx, v) for v in values]

    lines: list[str] = []
    lines.append("func() " + result_type + " {")
    lines.append("\tvar " + temp_name + " " + result_type)
    for i, part in enumerate(parts):
        lines.append("\t" + temp_name + " = " + part)
        if i < len(parts) - 1:
            if op == "And":
                lines.append("\tif !py_truthy(" + temp_name + ") {")
            else:
                lines.append("\tif py_truthy(" + temp_name + ") {")
            lines.append("\t\treturn " + temp_name)
            lines.append("\t}")
    lines.append("\treturn " + temp_name)
    lines.append("}()")
    return "\n".join(lines)


def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    lowered = _str(node, "lowered_kind")
    if lowered == "BuiltinCall":
        return _emit_builtin_call(ctx, node)

    func = node.get("func")
    args = _list(node, "args")
    keywords = _list(node, "keywords")
    arg_strs = [_emit_expr(ctx, a) for a in args]
    keyword_strs: list[str] = []
    for kw in keywords:
        if isinstance(kw, dict):
            keyword_strs.append(_emit_expr(ctx, kw.get("value")))
    call_arg_strs = arg_strs + keyword_strs

    if isinstance(func, dict):
        func_kind = _str(func, "kind")
        if func_kind == "Name" and _str(func, "id") == "isinstance" and len(args) >= 2:
            expected_arg = args[1] if isinstance(args[1], dict) else None
            if isinstance(expected_arg, dict) and _str(expected_arg, "kind") == "Tuple":
                return _emit_isinstance(ctx, {
                    "kind": "IsInstance",
                    "value": args[0],
                    "expected_type_id": expected_arg,
                })
            expected = _str(expected_arg, "id") if isinstance(expected_arg, dict) else ""
            if expected == "":
                expected = _str(expected_arg, "repr") if isinstance(expected_arg, dict) else ""
            return _emit_isinstance(ctx, {
                "kind": "IsInstance",
                "value": args[0],
                "expected_type_name": expected,
                "expected_type_id": {"kind": "Name", "id": expected},
            })
        expected_type_name = _str(node, "expected_type_name")
        if expected_type_name != "" and len(args) == 2:
            actual_node = args[0] if isinstance(args[0], dict) else None
            expected_node = args[1] if isinstance(args[1], dict) else None
            if (
                isinstance(actual_node, dict)
                and _str(actual_node, "kind") == "ObjTypeId"
                and isinstance(expected_node, dict)
                and _str(expected_node, "kind") == "Name"
            ):
                actual_value = _emit_expr(ctx, actual_node.get("value"))
                builtin_type_helpers: dict[str, str] = {
                    "bool": "py_is_bool_type",
                    "int": "py_is_int",
                    "int64": "py_is_exact_int64",
                    "float": "py_is_float",
                    "float64": "py_is_exact_float64",
                    "str": "py_is_str",
                    "list": "py_is_list",
                    "dict": "py_is_dict",
                    "set": "py_is_set",
                }
                helper_name = builtin_type_helpers.get(expected_type_name, "")
                if helper_name != "":
                    return helper_name + "(" + actual_value + ")"
                marker_method = _go_class_marker_method_name(ctx, expected_type_name)
                marker_helpers: dict[str, str] = {
                    "__pytra_is_str": "py_is_str",
                    "__pytra_is_list": "py_is_list",
                    "__pytra_is_dict": "py_is_dict",
                    "__pytra_is_set": "py_is_set",
                    "__pytra_is_bool": "py_is_bool_type",
                }
                marker_helper = marker_helpers.get(marker_method, "")
                if marker_helper != "":
                    return marker_helper + "(" + actual_value + ")"
                return "func() bool { _, ok := any(" + actual_value + ").(interface{ " + marker_method + "() }); return ok }()"
        if func_kind == "Attribute":
            owner_node = func.get("value")
            owner = _emit_expr(ctx, owner_node)
            attr = _str(func, "attr")
            owner_id2 = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
            if _str(node, "call_dispatch_kind") == "static_method":
                if owner_id2 != "":
                    return _safe_go_ident(owner_id2 + "_" + attr) + "(" + ", ".join(call_arg_strs) + ")"
            if owner_id2 != "" and attr in ctx.class_static_methods.get(owner_id2, set()):
                return _safe_go_ident(owner_id2 + "_" + attr) + "(" + ", ".join(call_arg_strs) + ")"
            if _is_zero_arg_super_call(owner_node):
                base_name = ctx.class_bases.get(ctx.current_class, "")
                if base_name != "":
                    base_ident = _safe_go_ident(base_name)
                    if attr == "__init__":
                        return (
                            ctx.current_receiver
                            + "."
                            + base_ident
                            + " = *New"
                            + base_ident
                            + "("
                            + ", ".join(call_arg_strs)
                            + ")"
                        )
                    return (
                        ctx.current_receiver
                        + "."
                        + base_ident
                        + "."
                        + _safe_go_ident(attr)
                        + "("
                        + ", ".join(call_arg_strs)
                        + ")"
                    )
            # Module function call: math.sqrt → py_sqrt, png.write_rgb_png → write_rgb_png
            owner_rt = _effective_resolved_type(ctx, owner_node) if isinstance(owner_node, dict) else ""
            owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
            method_sig = ctx.method_signatures.get(owner_rt, {}).get(attr)
            if method_sig is None:
                method_sig = ctx.known_method_signatures.get((owner_rt, attr))
            if isinstance(method_sig, dict):
                call_arg_strs = _build_sig_call_args(ctx, args, arg_strs, keywords, method_sig, skip_self=True)
            method_key = _str(node, "resolved_runtime_call")
            if method_key == "":
                method_key = _str(node, "runtime_call")
            if method_key == "":
                method_key = _str(node, "runtime_symbol")
            if method_key == "" and owner_rt in ("str", "string") and attr != "":
                method_key = "str." + attr
            if method_key == "" and (owner_rt == "list" or owner_rt.startswith("list[")) and attr == "append":
                method_key = "list.append"
            dispatch = ctx.mapping.calls.get(method_key, "") if method_key != "" else ""
            if owner_rt == "module" or owner_id in ctx.import_alias_modules:
                mod_id = _str(node, "runtime_module_id")
                if mod_id == "":
                    mod_id = _str(func, "runtime_module_id")
                if mod_id == "":
                    mod_id = _str(owner_node, "runtime_module_id") if isinstance(owner_node, dict) else ""
                if mod_id == "":
                    mod_id = ctx.import_alias_modules.get(owner_id, "")
                module_symbol_keys: list[str] = []
                if owner_id != "":
                    module_symbol_keys.append(owner_id + "." + attr)
                if mod_id != "":
                    module_symbol_keys.append(mod_id + "." + attr)
                for symbol_key in module_symbol_keys:
                    mapped_name = ctx.mapping.calls.get(symbol_key)
                    if isinstance(mapped_name, str) and mapped_name != "":
                        wrapped_args = _wrap_container_call_args(ctx, args, call_arg_strs)
                        return mapped_name + "(" + ", ".join(wrapped_args) + ")"
                runtime_symbol = _str(node, "runtime_symbol")
                if runtime_symbol == "":
                    runtime_symbol = _str(func, "runtime_symbol")
                if runtime_symbol == "":
                    runtime_symbol = attr
                if should_skip_module(mod_id, ctx.mapping):
                    resolved_name = resolve_runtime_symbol_name(
                        runtime_symbol,
                        ctx.mapping,
                        module_id=mod_id,
                        resolved_runtime_call=_str(node, "resolved_runtime_call"),
                        runtime_call=_str(node, "runtime_call"),
                    )
                    if resolved_name == "":
                        resolved_name = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping, module_id=mod_id)
                    wrapped_args = _wrap_container_call_args(ctx, args, call_arg_strs)
                    return _safe_go_ident(resolved_name) + "(" + ", ".join(wrapped_args) + ")"
                wrapped_args = _wrap_container_call_args(ctx, args, call_arg_strs)
                return _safe_go_ident(runtime_symbol) + "(" + ", ".join(wrapped_args) + ")"
            if dispatch == "__LIST_APPEND__" and len(arg_strs) >= 1:
                owner_storage = _wrapper_container_storage_expr(ctx, owner_node, owner)
                arg_code = arg_strs[0]
                arg_node = args[0] if len(args) >= 1 and isinstance(args[0], dict) else None
                if owner_rt in ("bytes", "bytearray", "list[uint8]", "unknown"):
                    return owner_storage + " = py_append_byte(" + owner_storage + ", " + arg_code + ")"
                if owner_rt.startswith("list["):
                    elem_type = owner_rt[5:-1]
                    if _is_container_resolved_type(elem_type) and isinstance(arg_node, dict):
                        if not _is_wrapper_container_expr(ctx, arg_node, arg_code):
                            arg_code = _wrap_ref_container_value_code(ctx, arg_code, elem_type)
                    return owner_storage + " = append(" + owner_storage + ", " + arg_code + ")"
            if dispatch == "__LIST_EXTEND__" and len(arg_strs) >= 1:
                owner_storage = _wrapper_container_storage_expr(ctx, owner_node, owner)
                src_code = arg_strs[0]
                src_node = args[0] if len(args) >= 1 and isinstance(args[0], dict) else None
                if isinstance(src_node, dict):
                    src_rt = _effective_resolved_type(ctx, src_node)
                    if _is_container_resolved_type(src_rt):
                        src_code = _wrapper_container_storage_expr(ctx, src_node, src_code)
                if owner_rt in ("bytes", "bytearray", "list[uint8]", "unknown"):
                    return owner_storage + " = append(" + owner_storage + ", " + src_code + "...)"
                if owner_rt.startswith("list["):
                    return owner_storage + " = append(" + owner_storage + ", " + src_code + "...)"
            if dispatch in ("__DICT_KEYS__", "__DICT_VALUES__") and ((owner_rt.startswith("dict[") and owner_rt.endswith("]")) or owner_rt in ("Node", "dict[str,Any]")):
                if owner_rt in ("Node", "dict[str,Any]"):
                    if dispatch == "__DICT_KEYS__":
                        return "py_dict_keys(" + owner + ")"
                    return "py_dict_values(" + owner + ")"
                parts = _split_generic_args(owner_rt[5:-1])
                if len(parts) == 2:
                    item_type = parts[0] if dispatch == "__DICT_KEYS__" else parts[1]
                    item_go_type = go_type(item_type)
                    out_name = _next_temp(ctx, "dict_items")
                    key_name = _next_temp(ctx, "k")
                    val_name = _next_temp(ctx, "v")
                    range_line = "for " + key_name + " := range " + owner + " {"
                    append_value = key_name
                    if dispatch == "__DICT_VALUES__":
                        range_line = "for _, " + val_name + " := range " + owner + " {"
                        append_value = val_name
                    return (
                        "func() []" + item_go_type + " {\n"
                        + "\t" + out_name + " := []" + item_go_type + "{}\n"
                        + "\t" + range_line + "\n"
                        + "\t\t" + out_name + " = append(" + out_name + ", " + append_value + ")\n"
                        + "\t}\n"
                        + "\treturn " + out_name + "\n"
                        + "}()"
                    )
            if dispatch == "__DICT_ITEMS__" and (owner_rt.startswith("dict[") or owner_rt.startswith("map[") or "dict[" in owner_rt or owner_rt in ("Node", "dict[str,Any]")):
                return "py_items(" + owner + ")"
            if attr == "items" and len(arg_strs) == 0 and "dict[" in owner_rt:
                return "py_items(" + owner + ")"
            if attr == "items" and len(arg_strs) == 0 and owner_rt in ("", "unknown", "Any", "Obj", "object", "JsonVal", "any"):
                return "py_items(" + owner + ")"
            if dispatch == "__IO_READ__":
                return owner + ".read(" + ", ".join(arg_strs) + ")"
            if dispatch == "__IO_WRITE__":
                return owner + ".write(" + ", ".join(arg_strs) + ")"
            if dispatch == "__IO_CLOSE__":
                return owner + ".close()"
            if method_key == "set.update" and len(arg_strs) >= 1:
                owner_storage = _wrapper_container_storage_expr(ctx, owner_node, owner)
                owner_effective_rt = _effective_resolved_type(ctx, owner_node) if isinstance(owner_node, dict) else owner_rt
                if owner_storage == owner and owner_effective_rt.startswith("set["):
                    owner_storage = owner + ".items"
                return "py_set_update(" + owner_storage + ", " + arg_strs[0] + ")"
            owner_effective_rt = _effective_resolved_type(ctx, owner_node) if isinstance(owner_node, dict) else owner_rt
            if owner_effective_rt == "":
                owner_effective_rt = owner_rt
            if dispatch == "__SET_ADD__" and owner_effective_rt.startswith("set") and len(arg_strs) >= 1:
                owner_storage = _wrapper_container_storage_expr(ctx, owner_node, owner)
                elem_code = arg_strs[0]
                if owner_effective_rt.startswith("set[tuple["):
                    elem_code = "py_tuple_key(" + elem_code + ")"
                return owner_storage + "[" + elem_code + "] = struct{}{}"
            if method_key == "list.index" and owner_rt.startswith("list[") and len(arg_strs) >= 1:
                owner_storage = _wrapper_container_storage_expr(ctx, owner_node, owner)
                return "py_list_index(" + owner_storage + ", " + arg_strs[0] + ")"
            if owner_rt in ("str", "string") and isinstance(dispatch, str) and dispatch != "":
                helper_args = [owner] + call_arg_strs
                if method_key == "str.join" and len(args) >= 1 and isinstance(args[0], dict) and len(helper_args) >= 2:
                    helper_args[1] = _wrapper_container_storage_expr(ctx, args[0], helper_args[1])
                return dispatch + "(" + ", ".join(helper_args) + ")"
            if dispatch == "__DICT_GET__" and len(arg_strs) >= 1:
                owner_rt = _str(func.get("value", {}), "resolved_type") if isinstance(func.get("value"), dict) else ""
                result_type = _str(node, "resolved_type")
                yields_dynamic = _call_yields_dynamic(node)
                if owner_rt.startswith("dict[") or owner_rt.startswith("map[") or owner_rt in ("Node", "dict[str,Any]"):
                    if len(arg_strs) >= 2:
                        if yields_dynamic:
                            dynamic_code = "py_dict_get(" + owner + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
                            if not ctx.skip_any_coercion and result_type not in ("", "unknown", "Any", "Obj", "object"):
                                return _coerce_from_any(dynamic_code, result_type)
                            return dynamic_code
                        return "py_dict_get(" + owner + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
                    return owner + "[" + arg_strs[0] + "]"
            if ".(*PyDict[" in owner:
                owner_storage = _wrapper_container_storage_expr(ctx, owner_node, owner)
                if attr == "items":
                    return "py_items(" + owner_storage + ")"
                if attr == "keys":
                    return "py_dict_keys(" + owner_storage + ")"
                if attr == "values":
                    return "py_dict_values(" + owner_storage + ")"
                if attr == "get" and len(arg_strs) >= 1:
                    if len(arg_strs) >= 2:
                        return "py_dict_get(" + owner_storage + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
                    return "py_dict_get(" + owner_storage + ", " + arg_strs[0] + ", nil)"
            wrapped_method_args = _wrap_container_call_args(ctx, args, call_arg_strs)
            return owner + "." + _safe_go_ident(attr) + "(" + ", ".join(wrapped_method_args) + ")"
        if func_kind == "Name":
            fn_name = _str(func, "id")
            if fn_name == "":
                fn_name = _str(func, "repr")
            if fn_name in ("int", "float", "bool", "str", "ord", "chr", "list"):
                builtin_like = dict(node)
                builtin_like["lowered_kind"] = "BuiltinCall"
                builtin_like["builtin_name"] = fn_name
                builtin_like["runtime_call"] = "list_ctor" if fn_name == "list" else fn_name
                return _emit_builtin_call(ctx, builtin_like)
            local_sig = ctx.function_signatures.get(fn_name)
            # For callable-typed variables (e.g. lambdas), get param types from the func node.
            if local_sig is None and isinstance(func, dict):
                func_rt = _str(func, "resolved_type")
                if func_rt.startswith("callable[") or func_rt.startswith("Callable["):
                    _callable_params, _ = _parse_callable_signature(func_rt)
                    if len(_callable_params) > 0:
                        _callable_sig_types = {str(i): t for i, t in enumerate(_callable_params)}
                        local_sig = ([str(i) for i in range(len(_callable_params))], _callable_sig_types, {})
            if local_sig is not None:
                sig_order, sig_types, sig_vararg = local_sig
                adjusted_args: list[str] = []
                for idx, arg_node in enumerate(args):
                    arg_code = arg_strs[idx] if idx < len(arg_strs) else ""
                    expected_type = ""
                    if idx < len(sig_order):
                        expected_type = sig_types.get(sig_order[idx], "")
                    if expected_type != "" and isinstance(arg_node, dict):
                        actual_type = _effective_resolved_type(ctx, arg_node)
                        if _is_container_resolved_type(expected_type):
                            if not _is_wrapper_container_expr(ctx, arg_node, arg_code):
                                arg_code = _wrap_ref_container_value_code(ctx, arg_code, expected_type)
                            adjusted_args.append(arg_code)
                            continue
                        if go_type(actual_type) == go_type(expected_type):
                            adjusted_args.append(arg_code)
                            continue
                        if _optional_inner_type(expected_type) != "":
                            if isinstance(arg_node, dict) and _str(arg_node, "kind") == "Name":
                                scope_name = _go_symbol_name(ctx, _str(arg_node, "id"))
                                if go_type(ctx.var_types.get(scope_name, "")) == go_type(expected_type):
                                    adjusted_args.append(scope_name)
                                    continue
                            arg_code = _wrap_optional_value_code(ctx, arg_code, expected_type, arg_node)
                        else:
                            arg_code = _maybe_coerce_expr_to_type(ctx, arg_node, arg_code, expected_type)
                    adjusted_args.append(arg_code)
                for kw in keywords:
                    if isinstance(kw, dict):
                        kw_name = _str(kw, "arg")
                        kw_node = kw.get("value")
                        kw_code = _emit_expr(ctx, kw_node)
                        expected_type2 = sig_types.get(kw_name, "")
                        if expected_type2 != "" and isinstance(kw_node, dict):
                            actual_type2 = _effective_resolved_type(ctx, kw_node)
                            if _is_container_resolved_type(expected_type2):
                                if not _is_wrapper_container_expr(ctx, kw_node, kw_code):
                                    kw_code = _wrap_ref_container_value_code(ctx, kw_code, expected_type2)
                                adjusted_args.append(kw_code)
                                continue
                            if go_type(actual_type2) == go_type(expected_type2):
                                adjusted_args.append(kw_code)
                                continue
                            if _optional_inner_type(expected_type2) != "":
                                if isinstance(kw_node, dict) and _str(kw_node, "kind") == "Name":
                                    scope_name2 = _go_symbol_name(ctx, _str(kw_node, "id"))
                                    if go_type(ctx.var_types.get(scope_name2, "")) == go_type(expected_type2):
                                        adjusted_args.append(scope_name2)
                                        continue
                                kw_code = _wrap_optional_value_code(ctx, kw_code, expected_type2, kw_node)
                        adjusted_args.append(kw_code)
                if (
                    isinstance(sig_vararg, dict)
                    and _str(sig_vararg, "vararg_name") != ""
                    and len(args) > 0
                    and len(sig_order) > 0
                    and len(args) >= len(sig_order)
                ):
                    spread_index = len(args) - 1
                    if 0 <= spread_index < len(adjusted_args):
                        last_arg = args[spread_index] if isinstance(args[spread_index], dict) else None
                        last_type = _effective_resolved_type(ctx, last_arg) if isinstance(last_arg, dict) else ""
                        if isinstance(last_arg, dict) and (
                            _str(last_arg, "kind") == "List"
                            or last_type.startswith("list[")
                            or last_type == "list"
                        ):
                            adjusted_args[spread_index] = adjusted_args[spread_index] + "..."
                call_arg_strs = adjusted_args
            if fn_name == "set":
                set_rt = _str(node, "resolved_type")
                if len(call_arg_strs) == 0:
                    return _go_ref_container_ctor(ctx, set_rt if set_rt != "" else "set", "{}")
                if set_rt == "set[str]" and len(call_arg_strs) == 1:
                    arg0_node = args[0] if len(args) >= 1 and isinstance(args[0], dict) else None
                    if isinstance(arg0_node, dict) and _str(arg0_node, "resolved_type") == "set[str]":
                        return call_arg_strs[0]
                    return "PySetFromMap[string](py_set_str(" + call_arg_strs[0] + "))"
                set_elem = ""
                if set_rt.startswith("set[") and set_rt.endswith("]"):
                    set_elem = go_type(set_rt[4:-1])
                elif set_rt in ("set", "") and len(args) >= 1 and isinstance(args[0], dict):
                    # Infer element type from argument (e.g. dict.keys() → string)
                    arg_rt = _str(args[0], "resolved_type")
                    if arg_rt.startswith("list[") and arg_rt.endswith("]"):
                        set_elem = go_type(arg_rt[5:-1])
                    elif arg_rt.startswith("dict[") and arg_rt.endswith("]"):
                        inner_parts = _split_generic_args(arg_rt[5:-1])
                        if len(inner_parts) >= 1:
                            set_elem = go_type(inner_parts[0])
                    elif arg_rt in ("str",):
                        set_elem = "string"
                if set_elem != "" and set_elem != "any":
                    wrapped_set = "py_set[" + set_elem + "](" + ", ".join(call_arg_strs) + ")"
                else:
                    wrapped_set = "py_set(" + ", ".join(call_arg_strs) + ")"
                return _wrap_ref_container_value_code(ctx, wrapped_set, set_rt) if set_rt != "" else wrapped_set
            # bytearray/bytes constructor
            if fn_name in ("bytearray", "bytes"):
                if len(args) == 0:
                    return "[]byte{}"
                if len(args) == 1 and isinstance(args[0], dict):
                    a0_kind = _str(args[0], "kind")
                    a0_rt = _str(args[0], "resolved_type")
                    if a0_kind == "List":
                        # bytearray([1,2,3]) → []byte{1,2,3}
                        elems = _list(args[0], "elements")
                        parts = ["byte(" + _emit_expr(ctx, e) + ")" for e in elems]
                        return "[]byte{" + ", ".join(parts) + "}"
                    if a0_rt in ("int64", "int32", "int"):
                        # bytearray(N) → make([]byte, N)
                        return "make([]byte, " + arg_strs[0] + ")"
                    if fn_name == "bytes" and a0_rt in ("bytes", "bytearray", "list[uint8]"):
                        return "append([]byte{}, " + arg_strs[0] + "...)"
                return "[]byte(" + arg_strs[0] + ")"
            if fn_name == "cast":
                if len(arg_strs) >= 2:
                    target_name = _str(node, "resolved_type")
                    target_node = args[0] if isinstance(args[0], dict) else None
                    if (target_name == "" or target_name == "unknown") and isinstance(target_node, dict):
                        target_name = _str(target_node, "id")
                        if target_name == "":
                            target_name = _str(target_node, "repr")
                    value_node = args[1] if len(args) >= 2 and isinstance(args[1], dict) else None
                    if isinstance(value_node, dict) and _str(value_node, "kind") == "Name":
                        source_type0 = _str(value_node, "resolved_type")
                        scope_name = _go_symbol_name(ctx, _str(value_node, "id"))
                        scope_type = ctx.var_types.get(scope_name, "")
                        if (
                            target_name != ""
                            and source_type0 == target_name
                            and scope_type not in ("", "unknown", "JsonVal", "Any", "Obj", "object")
                            and go_type(scope_type) != "any"
                        ):
                            return arg_strs[1]
                        target_gt0 = _go_type_with_ctx(ctx, target_name)
                        if (
                            target_gt0 != ""
                            and target_gt0 != "any"
                            and (
                                scope_type == ""
                                or scope_type == "unknown"
                                or scope_type in ("JsonVal", "Any", "Obj", "object")
                                or go_type(scope_type) == "any"
                            )
                        ):
                            return _coerce_from_any(arg_strs[1], target_name)
                    if isinstance(value_node, dict) and _str(value_node, "kind") == "Name":
                        scope_name = _go_symbol_name(ctx, _str(value_node, "id"))
                        scope_type = ctx.var_types.get(scope_name, "")
                        scope_optional_inner = _optional_inner_type(scope_type)
                        if scope_optional_inner != "" and target_name == scope_optional_inner and go_type(scope_type).startswith("*"):
                            target_gt2 = go_type(target_name)
                            if not target_gt2.startswith("*"):
                                return "(*(" + arg_strs[1] + "))"
                            return arg_strs[1]
                    if isinstance(value_node, dict):
                        if _str(value_node, "kind") == "Unbox":
                            unbox_target = _str(value_node, "target")
                            if unbox_target == "":
                                unbox_target = _str(value_node, "resolved_type")
                            if target_name == unbox_target or _go_type_with_ctx(ctx, target_name) == _go_type_with_ctx(ctx, unbox_target):
                                return _emit_expr(ctx, value_node)
                        source_type = _str(value_node, "resolved_type")
                        source_optional_inner = _optional_inner_type(source_type)
                        target_gt = _go_type_with_ctx(ctx, target_name)
                        source_gt = go_type(source_type) if source_type != "" else ""
                        if target_gt != "" and source_gt == target_gt:
                            return arg_strs[1]
                        if (
                            source_optional_inner != ""
                            and target_gt != ""
                            and go_type(source_optional_inner) == target_gt
                            and source_gt.startswith("*")
                        ):
                            if not target_gt.startswith("*"):
                                return "(*(" + arg_strs[1] + "))"
                            return arg_strs[1]
                    if isinstance(value_node, dict) and _str(value_node, "kind") == "Unbox":
                        unbox_target = _str(value_node, "target")
                        if unbox_target == "":
                            unbox_target = _str(value_node, "resolved_type")
                        if target_name in ("dict", "list", "set", "tuple"):
                            return arg_strs[1]
                        if target_name == unbox_target or _go_type_with_ctx(ctx, target_name) == _go_type_with_ctx(ctx, unbox_target):
                            return arg_strs[1]
                    target_gt = _go_type_with_ctx(ctx, target_name)
                    if target_gt != "" and arg_strs[1].endswith(".(" + target_gt + ")"):
                        return arg_strs[1]
                    if target_gt != "":
                        return arg_strs[1] + ".(" + target_gt + ")"
                    return arg_strs[1]
                if len(arg_strs) == 1:
                    return arg_strs[0]
                return "nil"
            if fn_name == "str" and len(call_arg_strs) >= 1:
                return "py_str(" + call_arg_strs[0] + ")"
            if fn_name == "len" and len(call_arg_strs) >= 1:
                arg0 = args[0] if isinstance(args[0], dict) else None
                arg0_rt = _str(arg0, "resolved_type") if isinstance(arg0, dict) else ""
                arg0_code = _wrapper_container_storage_expr(ctx, arg0, call_arg_strs[0])
                if arg0_rt.startswith("list[") or arg0_rt.startswith("dict[") or arg0_rt.startswith("set["):
                    return "int64(len(" + arg0_code + "))"
                if arg0_rt in ("str", "bytes", "bytearray"):
                    return "int64(len(" + arg0_code + "))"
                return "int64(" + arg0_code + ".__len__())"
            if fn_name == "print":
                return "py_print(" + ", ".join(call_arg_strs) + ")"
            if fn_name == "py_assert_stdout":
                adjusted_args2 = list(call_arg_strs)
                if len(args) >= 1 and isinstance(args[0], dict):
                    arg0 = args[0]
                    arg0_code = adjusted_args2[0] if len(adjusted_args2) >= 1 else ""
                    if not _is_wrapper_container_expr(ctx, arg0, arg0_code):
                        adjusted_args2[0] = _wrap_ref_container_value_code(ctx, arg0_code, "list[str]")
                if len(adjusted_args2) >= 2:
                    adjusted_args2[1] = "func() { py_call_void(" + adjusted_args2[1] + ") }"
                return "py_assert_stdout(" + ", ".join(adjusted_args2) + ")"
            if fn_name in ctx.builtin_exc_bounds:
                if len(call_arg_strs) >= 1:
                    return _exception_ctor_expr(ctx, fn_name, call_arg_strs[0])
                return _exception_ctor_expr(ctx, fn_name, _go_string_literal(fn_name))
            runtime_module_id = _str(node, "runtime_module_id")
            runtime_symbol = _str(node, "runtime_symbol")
            if runtime_symbol != "":
                if runtime_symbol[:1].isupper():
                    return "New" + _safe_go_ident(runtime_symbol) + "(" + ", ".join(call_arg_strs) + ")"
                if _str(func, "resolved_type") == "type":
                    return "New" + _safe_go_ident(runtime_symbol) + "(" + ", ".join(call_arg_strs) + ")"
                if should_skip_module(runtime_module_id, ctx.mapping):
                    mapped_name = resolve_runtime_symbol_name(
                        runtime_symbol,
                        ctx.mapping,
                        module_id=runtime_module_id,
                        resolved_runtime_call=_str(node, "resolved_runtime_call"),
                        runtime_call=_str(node, "runtime_call"),
                    )
                    return _safe_go_ident(mapped_name) + "(" + ", ".join(call_arg_strs) + ")"
                return _safe_go_ident(runtime_symbol) + "(" + ", ".join(call_arg_strs) + ")"
            # Class constructor: ClassName(...) → NewClassName(...)
            if fn_name in ctx.class_names:
                ctor_sig = ctx.class_init_signatures.get(fn_name)
                ctor_args2: list[str]
                if isinstance(ctor_sig, dict):
                    ctor_args2 = _build_sig_call_args(ctx, args, arg_strs, keywords, ctor_sig, skip_self=True)
                else:
                    ctor_args2 = []
                    for idx, arg_node in enumerate(args):
                        arg_code = call_arg_strs[idx] if idx < len(call_arg_strs) else ""
                        if isinstance(arg_node, dict):
                            arg_type = _effective_resolved_type(ctx, arg_node)
                            if _is_container_resolved_type(arg_type) and not _is_wrapper_container_expr(ctx, arg_node, arg_code):
                                arg_code = _wrap_ref_container_value_code(ctx, arg_code, arg_type)
                        ctor_args2.append(arg_code)
                return "New" + _go_symbol_name(ctx, fn_name) + "(" + ", ".join(ctor_args2) + ")"
            # Imported/declared class constructor: Path(...) → NewPath(...)
            if _str(func, "resolved_type") == "type" or (fn_name in ctx.import_alias_modules and fn_name[:1].isupper()):
                ctor_args: list[str] = []
                for idx, arg_node in enumerate(args):
                    arg_code = call_arg_strs[idx] if idx < len(call_arg_strs) else ""
                    if isinstance(arg_node, dict):
                        arg_type = _effective_resolved_type(ctx, arg_node)
                        if _is_container_resolved_type(arg_type) and not _is_wrapper_container_expr(ctx, arg_node, arg_code):
                            arg_code = _wrap_ref_container_value_code(ctx, arg_code, arg_type)
                    ctor_args.append(arg_code)
                return "New" + _go_symbol_name(ctx, fn_name) + "(" + ", ".join(ctor_args) + ")"
            # Imported runtime function: add prefix only if not already prefixed
            if fn_name in ctx.runtime_imports:
                return _safe_go_ident(ctx.runtime_imports[fn_name]) + "(" + ", ".join(call_arg_strs) + ")"
            # Check mapping for known runtime function names (e.g., py_to_string → py_str)
            if fn_name in ctx.mapping.calls:
                return ctx.mapping.calls[fn_name] + "(" + ", ".join(call_arg_strs) + ")"
            # Use _emit_name to handle main→__pytra_main etc.
            go_fn = _emit_name(ctx, func)
            return go_fn + "(" + ", ".join(call_arg_strs) + ")"

    fn = _emit_expr(ctx, func)
    return fn + "(" + ", ".join(call_arg_strs) + ")"


def _unwrap_boundary_node(node: JsonVal) -> JsonVal:
    current = node
    while isinstance(current, dict) and _str(current, "kind") in ("Box", "Unbox"):
        current = current.get("value")
    return current


def _enum_scalar_cast_code(ctx: EmitContext, node: JsonVal, target_gt: str) -> str:
    raw_node = _unwrap_boundary_node(node)
    if not isinstance(raw_node, dict):
        return ""
    raw_kind = _str(raw_node, "kind")
    raw_type = _effective_resolved_type(ctx, raw_node)
    if raw_type in ctx.enum_bases:
        return target_gt + "(" + _emit_expr(ctx, raw_node) + ")"
    if raw_kind == "Attribute":
        owner = raw_node.get("value")
        owner_id = _str(owner, "id") if isinstance(owner, dict) else ""
        if owner_id in ctx.enum_bases:
            return target_gt + "(" + _emit_expr(ctx, raw_node) + ")"
    return ""


def _emit_builtin_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    rc = _str(node, "runtime_call")
    bn = _str(node, "builtin_name")
    args = _list(node, "args")
    keywords = _list(node, "keywords")
    arg_strs = [_emit_expr(ctx, a) for a in args]
    func = node.get("func")
    method_owner = ""
    call_arg_strs = arg_strs
    if isinstance(func, dict) and _str(func, "kind") == "Attribute":
        method_owner = _emit_expr(ctx, func.get("value"))
        call_arg_strs = [method_owner] + arg_strs
    adapter = _str(node, "runtime_call_adapter_kind")
    resolved = resolve_runtime_call(rc, bn, adapter, ctx.mapping)
    dispatch = resolved if resolved != "" else rc
    if dispatch == "":
        semantic_tag = _str(node, "semantic_tag")
        if semantic_tag in ("core.bytearray_ctor", "core.bytes_ctor"):
            dispatch = "__MAKE_BYTES__"

    # Type cast builtins
    if rc in ("static_cast", "int", "float", "bool"):
        rt = _str(node, "resolved_type")
        gt = go_type(rt)
        # Check if source is string → int conversion (needs runtime helper)
        if len(args) >= 1 and isinstance(args[0], dict):
            enum_cast = _enum_scalar_cast_code(ctx, args[0], gt)
            if enum_cast != "":
                return enum_cast
            src_type = _str(args[0], "resolved_type")
            src_is_dynamic = (
                src_type in ("Any", "object", "Obj")
                or go_type(src_type) == "any"
                or _is_union_like_resolved_type(ctx, src_type)
            )
            if src_type == "str" and gt in ("int64", "int32"):
                return "py_str_to_int64(" + arg_strs[0] + ")"
            if src_type == "str" and gt in ("float64", "float32"):
                cast_prefix = "float32" if gt == "float32" else ""
                inner = "py_str_to_float64(" + arg_strs[0] + ")"
                return cast_prefix + "(" + inner + ")" if cast_prefix != "" else inner
            if gt in ("float64", "float32") and (src_type == "bool" or src_is_dynamic):
                cast_prefix = "float32" if gt == "float32" else ""
                inner = "py_to_float64(" + arg_strs[0] + ")"
                return cast_prefix + "(" + inner + ")" if cast_prefix != "" else inner
            if gt == "bool":
                return "py_bool(" + arg_strs[0] + ")"
            if src_is_dynamic and gt in ("int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"):
                return _coerce_from_any(arg_strs[0], rt)
        if len(arg_strs) >= 1:
            return gt + "(" + arg_strs[0] + ")"
        return gt + "(0)"

    # py_to_string
    if rc in ("py_to_string", "str"):
        if len(arg_strs) >= 1:
            return "py_str(" + arg_strs[0] + ")"
        return "\"\""

    # print
    if (ctx.dispatch_print and dispatch == ctx.dispatch_print) or bn == "print":
        return "py_print(" + ", ".join(arg_strs) + ")"

    # len — use Go native len() for type safety
    if (ctx.dispatch_len and dispatch == ctx.dispatch_len) or bn == "len":
        if len(arg_strs) >= 1:
            arg0 = args[0] if isinstance(args[0], dict) else None
            arg0_rt = _str(arg0, "resolved_type") if isinstance(arg0, dict) else ""
            arg0_code = _wrapper_container_storage_expr(ctx, arg0, arg_strs[0])
            if isinstance(arg0, dict) and _str(arg0, "kind") == "Name":
                arg0_name = _safe_go_ident(_str(arg0, "id"))
                scope_type = ctx.var_types.get(arg0_name, "")
                if scope_type != "" and arg0_rt in ("", "unknown"):
                    arg0_rt = scope_type
            if arg0_rt.startswith("list[") or arg0_rt.startswith("dict[") or arg0_rt.startswith("set["):
                return "int64(len(" + arg0_code + "))"
            if arg0_rt in ("str", "bytes", "bytearray"):
                return "int64(len(" + arg0_code + "))"
            return "int64(" + arg0_code + ".__len__())"

    # Container constructors: bytes(N)/bytearray(N) → make([]byte, N)
    if dispatch == "__MAKE_BYTES__":
        if len(args) >= 1 and isinstance(args[0], dict):
            a0_kind = _str(args[0], "kind")
            a0_rt = _str(args[0], "resolved_type")
            result_rt = _str(node, "resolved_type")
            if a0_kind == "List":
                # bytearray([1,2,3]) → []byte{byte(1),byte(2),byte(3)}
                elems = _list(args[0], "elements")
                parts = ["byte(" + _emit_expr(ctx, e) + ")" for e in elems]
                return "[]byte{" + ", ".join(parts) + "}"
            if a0_rt in ("int64", "int32", "int", "uint8", "int8"):
                return "make([]byte, " + arg_strs[0] + ")"
            if result_rt == "bytes" and a0_rt in ("bytes", "bytearray", "list[uint8]"):
                return "append([]byte{}, " + arg_strs[0] + "...)"
            return "[]byte(" + arg_strs[0] + ")"
        if len(arg_strs) >= 1:
            return "[]byte(" + arg_strs[0] + ")"
        return "[]byte{}"

    if dispatch == "py_set":
        result_type_set = _str(node, "resolved_type")
        if len(args) == 0:
            return _go_ref_container_ctor(ctx, result_type_set if result_type_set != "" else "set", "{}")
        if result_type_set == "set[str]" and len(arg_strs) == 1:
            return "PySetFromMap[string](py_set_str(" + arg_strs[0] + "))"
        # Add explicit type parameter for Go type inference
        elem_type = ""
        if result_type_set.startswith("set[") and result_type_set.endswith("]"):
            elem_type = go_type(result_type_set[4:-1])
        elif result_type_set in ("set", "") and len(args) >= 1 and isinstance(args[0], dict):
            arg_rt = _str(args[0], "resolved_type")
            if arg_rt.startswith("list[") and arg_rt.endswith("]"):
                elem_type = go_type(arg_rt[5:-1])
        if elem_type != "" and elem_type != "any":
            wrapped = "py_set[" + elem_type + "](" + ", ".join(arg_strs) + ")"
        else:
            wrapped = "py_set(" + ", ".join(arg_strs) + ")"
        return _wrap_ref_container_value_code(ctx, wrapped, result_type_set) if result_type_set != "" else wrapped

    if dispatch == "__TUPLE_CTOR__":
        if len(args) == 0:
            return "[]any{}"
        if len(args) >= 1 and isinstance(args[0], dict):
            return _box_value_code(ctx, args[0], _str(node, "resolved_type"))
        if len(arg_strs) >= 1:
            return arg_strs[0]
        return "[]any{}"

    if dispatch == "py_sorted" or bn == "sorted":
        if len(args) >= 1 and isinstance(args[0], dict):
            src_node = args[0]
            src_code = arg_strs[0]
            src_rt = _str(src_node, "resolved_type")
            if _str(src_node, "kind") == "Unbox":
                inner = src_node.get("value")
                if isinstance(inner, dict):
                    inner_rt = _str(inner, "resolved_type")
                    if "T" in src_rt or src_rt in ("unknown", "list[unknown]"):
                        src_node = inner
                        src_code = _emit_expr(ctx, inner)
                        src_rt = inner_rt
            result_type = _str(node, "resolved_type")
            result_gt = _go_signature_type(ctx, result_type)
            key_attr = ""
            for kw in keywords:
                if not isinstance(kw, dict) or _str(kw, "arg") != "key":
                    continue
                key_value = kw.get("value")
                if isinstance(key_value, dict) and _str(key_value, "kind") == "Lambda":
                    body = key_value.get("body")
                    lam_args = _list(key_value, "args")
                    lam_name = ""
                    if len(lam_args) >= 1 and isinstance(lam_args[0], dict):
                        lam_name = _str(lam_args[0], "arg")
                    if isinstance(body, dict) and _str(body, "kind") == "Attribute":
                        owner = body.get("value")
                        if isinstance(owner, dict) and _str(owner, "kind") == "Name" and _str(owner, "id") == lam_name:
                            key_attr = _safe_go_ident(_str(body, "attr"))
                break
            out_name = _next_temp(ctx, "sorted")
            if len(args) >= 1 and isinstance(args[0], dict):
                src_code = _wrapper_container_storage_expr(ctx, args[0], src_code)
            if src_rt.startswith("set["):
                elem_type = src_rt[4:-1]
                elem_go_type = go_type(elem_type)
                key_name = _next_temp(ctx, "k")
                if elem_type == "str":
                    ctx.imports_needed.add(ctx.go_pkg_sort)
                    return (
                        "func() *PyList[string] {\n"
                        + "\t" + out_name + " := []string{}\n"
                        + "\tfor " + key_name + " := range " + src_code + " {\n"
                        + "\t\t" + out_name + " = append(" + out_name + ", " + key_name + ")\n"
                        + "\t}\n"
                        + "\tsort.Strings(" + out_name + ")\n"
                        + "\treturn PyListFromSlice[string](" + out_name + ")\n"
                        + "}()"
                    )
                ctx.imports_needed.add(ctx.go_pkg_sort)
                return (
                    "func() *PyList[" + elem_go_type + "] {\n"
                    + "\t" + out_name + " := []" + elem_go_type + "{}\n"
                    + "\tfor " + key_name + " := range " + src_code + " {\n"
                    + "\t\t" + out_name + " = append(" + out_name + ", " + key_name + ")\n"
                    + "\t}\n"
                    + "\tsort.Slice(" + out_name + ", func(i int, j int) bool {\n"
                    + "\t\treturn " + out_name + "[i] < " + out_name + "[j]\n"
                    + "\t})\n"
                    + "\treturn PyListFromSlice[" + elem_go_type + "](" + out_name + ")\n"
                    + "}()"
                )
            if src_rt == "list[str]" or result_gt == "[]string":
                ctx.imports_needed.add(ctx.go_pkg_sort)
                return (
                    "func() *PyList[string] {\n"
                    + "\t" + out_name + " := append([]string{}, " + src_code + "...)\n"
                    + "\tsort.Strings(" + out_name + ")\n"
                    + "\treturn PyListFromSlice[string](" + out_name + ")\n"
                    + "}()"
                )
            if src_rt.startswith("list[") and result_gt.startswith("[]") and key_attr != "":
                result_rt = _str(node, "resolved_type")
                result_wrapper_gt = _go_ref_container_type(ctx, result_rt) if _is_container_resolved_type(result_rt) else result_gt
                ctx.imports_needed.add(ctx.go_pkg_sort)
                return (
                    "func() " + result_wrapper_gt + " {\n"
                    + "\t" + out_name + " := append(" + result_gt + "{}, " + src_code + "...)\n"
                    + "\tsort.Slice(" + out_name + ", func(i int, j int) bool {\n"
                    + "\t\treturn " + out_name + "[i]." + key_attr + " < " + out_name + "[j]." + key_attr + "\n"
                    + "\t})\n"
                    + "\treturn PyListFromSlice(" + out_name + ")\n"
                    + "}()"
                )
        return "py_sorted(" + ", ".join(arg_strs) + ")"

    if dispatch == "__LIST_CTOR__":
        if len(args) == 0:
            result_gt = go_type(_str(node, "resolved_type"))
            if result_gt.startswith("[]"):
                return result_gt + "{}"
            return "[]any{}"
        if len(args) >= 1 and isinstance(args[0], dict):
            src_type = _str(args[0], "resolved_type")
            result_type = _str(node, "resolved_type")
            result_gt = go_type(result_type)
            src_code = arg_strs[0]
            if _is_container_resolved_type(result_type):
                src_code = _wrapper_container_storage_expr(ctx, args[0], src_code)
                if result_type == "list":
                    return "py_list_any(" + src_code + ")"
                if result_type.startswith("list[") and result_type.endswith("]"):
                    elem_gt = _go_signature_type(ctx, result_type[5:-1])
                    return "PyListFromSlice[" + elem_gt + "](" + src_code + ")"
            if src_type == result_type and result_gt.startswith("[]"):
                return "append(" + result_gt + "{}, " + src_code + "...)"
        if len(arg_strs) >= 1:
            return arg_strs[0]
        return "[]any{}"

    # Container methods
    if dispatch == "__LIST_APPEND__":
        if isinstance(func, dict):
            owner_node = func.get("value")
            call_args = args
            if _str(func, "kind") == "Name" and len(args) >= 2 and isinstance(args[0], dict):
                owner_node = args[0]
                call_args = args[1:]
            owner = _emit_expr(ctx, owner_node)
            owner = _wrapper_container_storage_expr(ctx, owner_node, owner)
            owner_rt = _effective_resolved_type(ctx, owner_node) if isinstance(owner_node, dict) else ""
            call_arg_strs = arg_strs[1:] if _str(func, "kind") == "Name" and len(arg_strs) >= 2 else arg_strs
            if len(call_arg_strs) >= 1:
                arg_code = call_arg_strs[0]
                arg_node = call_args[0] if len(call_args) >= 1 and isinstance(call_args[0], dict) else None
                # Type coerce element if needed (e.g., int64 → byte for []byte)
                if owner_rt in ("list[uint8]", "bytes", "bytearray"):
                    arg_code = "byte(" + arg_code + ")"
                elif owner_rt.startswith("list["):
                    elem_type = owner_rt[5:-1]
                    if _is_container_resolved_type(elem_type) and isinstance(arg_node, dict):
                        arg_rt = _effective_resolved_type(ctx, arg_node)
                        if "|" in arg_rt and _first_union_member(arg_rt, elem_type.split("[", 1)[0]) == elem_type:
                            arg_code = _coerce_from_any(arg_code, elem_type)
                        elif not _is_wrapper_container_expr(ctx, arg_node, arg_code):
                            arg_code = _wrap_ref_container_value_code(ctx, arg_code, elem_type)
                # Also detect via var_types
                owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
                if owner_id != "" and owner_id in ctx.var_types:
                    declared = ctx.var_types[owner_id]
                    if declared in ("list[uint8]", "bytes", "bytearray"):
                        arg_code = "byte(" + call_arg_strs[0] + ")"
                return owner + " = append(" + owner + ", " + arg_code + ")"

    if dispatch == "__LIST_EXTEND__":
        if isinstance(func, dict):
            owner_node = func.get("value")
            call_args = args
            if _str(func, "kind") == "Name" and len(args) >= 2 and isinstance(args[0], dict):
                owner_node = args[0]
                call_args = args[1:]
            owner = _emit_expr(ctx, owner_node)
            owner = _wrapper_container_storage_expr(ctx, owner_node, owner)
            owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            call_arg_strs = arg_strs[1:] if _str(func, "kind") == "Name" and len(arg_strs) >= 2 else arg_strs
            if len(call_arg_strs) >= 1:
                src_code = call_arg_strs[0]
                src_node = call_args[0] if len(call_args) >= 1 and isinstance(call_args[0], dict) else None
                if isinstance(src_node, dict):
                    src_rt = _effective_resolved_type(ctx, src_node)
                    if _is_container_resolved_type(src_rt):
                        src_code = _wrapper_container_storage_expr(ctx, src_node, src_code)
                if owner_rt in ("bytes", "bytearray", "list[uint8]", "unknown"):
                    return owner + " = append(" + owner + ", " + src_code + "...)"
                if owner_rt.startswith("list["):
                    return owner + " = append(" + owner + ", " + src_code + "...)"

    if dispatch == "__SET_ADD__":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            owner = _wrapper_container_storage_expr(ctx, func.get("value"), owner)
            if len(arg_strs) >= 1:
                owner_rt = _effective_resolved_type(ctx, func.get("value")) if isinstance(func.get("value"), dict) else ""
                elem_code = arg_strs[0]
                if owner_rt.startswith("set[tuple["):
                    elem_code = "py_tuple_key(" + elem_code + ")"
                return owner + "[" + elem_code + "] = struct{}{}"

    # list.pop
    if dispatch == "__LIST_POP__":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            owner = _wrapper_container_storage_expr(ctx, func.get("value"), owner)
            owner_node = func.get("value")
            owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            result_gt = go_type(_str(node, "resolved_type"))
            yields_dynamic = _call_yields_dynamic(node)
            if yields_dynamic:
                dynamic_code = "py_list_pop(&" + owner
                if len(arg_strs) >= 1:
                    dynamic_code += ", " + arg_strs[0]
                dynamic_code += ")"
                result_type = _str(node, "resolved_type")
                if result_type not in ("", "unknown", "Any", "Obj", "object"):
                    return _coerce_from_any(dynamic_code, result_type)
                return dynamic_code
            if owner_rt.startswith("list[") and result_gt != "" and result_gt != "any":
                idx_init = "len(" + owner + ") - 1"
                idx_setup = "\t__idx := " + idx_init + "\n"
                if len(arg_strs) >= 1:
                    idx_setup = (
                        "\t__idx := int(" + arg_strs[0] + ")\n"
                        + "\tif __idx < 0 {\n"
                        + "\t\t__idx += len(" + owner + ")\n"
                        + "\t}\n"
                    )
                return (
                    "func() " + result_gt + " {\n"
                    + idx_setup
                    + "\t__val := " + owner + "[__idx]\n"
                    + "\t" + owner + " = append(" + owner + "[:__idx], " + owner + "[__idx+1:]...)\n"
                    + "\treturn __val\n"
                    + "}()"
                )
            if owner_rt in ("bytes", "bytearray", "list[uint8]") and result_gt in ("int64", "int"):
                pop_call = "py_list_pop(&" + owner
                if len(arg_strs) >= 1:
                    pop_call += ", " + arg_strs[0]
                pop_call += ")"
                return "int64(" + pop_call + ".(byte))"
            if len(arg_strs) >= 1:
                return "py_list_pop(&" + owner + ", " + arg_strs[0] + ")"
            return "py_list_pop(&" + owner + ")"

    if dispatch == "__LIST_CLEAR__":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            owner = _wrapper_container_storage_expr(ctx, func.get("value"), owner)
            return owner + " = " + owner + "[:0]"

    # dict.get
    if dispatch == "__DICT_GET__":
        if isinstance(func, dict):
            owner_node = func.get("value")
            owner = _emit_expr(ctx, owner_node)
            owner = _wrapper_container_storage_expr(ctx, owner_node, owner)
            owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            result_type = _str(node, "resolved_type")
            yields_dynamic = _call_yields_dynamic(node)
            if len(arg_strs) >= 2:
                if yields_dynamic:
                    dynamic_code = "py_dict_get(" + owner + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
                    if not ctx.skip_any_coercion and result_type not in ("", "unknown", "Any", "Obj", "object"):
                        return _coerce_from_any(dynamic_code, result_type)
                    return dynamic_code
                if owner_rt.startswith("dict[") and owner_rt.endswith("]"):
                    parts = _split_generic_args(owner_rt[5:-1])
                    if len(parts) == 2 and result_type not in ("", "unknown", "Any", "object"):
                        result_gt = go_type(result_type)
                        default_code = arg_strs[1]
                        return (
                            "func() " + result_gt + " {\n"
                            + "\tif __val, ok := " + owner + "[" + arg_strs[0] + "]; ok {\n"
                            + "\t\treturn __val\n"
                            + "\t}\n"
                            + "\treturn " + default_code + "\n"
                            + "}()"
                        )
                return "py_dict_get(" + owner + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
            if len(arg_strs) >= 1:
                if yields_dynamic:
                    dynamic_code2 = "py_dict_get(" + owner + ", " + arg_strs[0] + ", nil)"
                    if not ctx.skip_any_coercion and result_type not in ("", "unknown", "Any", "Obj", "object"):
                        return _coerce_from_any(dynamic_code2, result_type)
                    return dynamic_code2
                if owner_rt.startswith("dict[") and owner_rt.endswith("]"):
                    parts = _split_generic_args(owner_rt[5:-1])
                    if len(parts) == 2:
                        tmp_name = _next_temp(ctx, "dict_get")
                        wrapped = _wrap_optional_resolved_code(ctx, tmp_name, parts[1])
                        return (
                            "func() any {\n"
                            + "\tif " + tmp_name + ", ok := " + owner + "[" + arg_strs[0] + "]; ok {\n"
                            + "\t\treturn " + wrapped + "\n"
                            + "\t}\n"
                            + "\treturn nil\n"
                            + "}()"
                        )
                return owner + "[" + arg_strs[0] + "]"
    if dispatch == "__DICT_ITEMS__" and isinstance(func, dict):
        owner = _emit_expr(ctx, func.get("value"))
        owner = _wrapper_container_storage_expr(ctx, func.get("value"), owner)
        return "py_items(" + owner + ")"
    if dispatch in ("__DICT_KEYS__", "__DICT_VALUES__") and isinstance(func, dict):
        owner = _emit_expr(ctx, func.get("value"))
        owner = _wrapper_container_storage_expr(ctx, func.get("value"), owner)
        owner_node = func.get("value")
        owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
        if owner_rt.startswith("dict[") and owner_rt.endswith("]"):
            parts = _split_generic_args(owner_rt[5:-1])
            if len(parts) == 2:
                item_type = parts[0] if dispatch == "__DICT_KEYS__" else parts[1]
                item_go_type = go_type(item_type)
                out_name = _next_temp(ctx, "dict_builtin")
                key_name = _next_temp(ctx, "k")
                val_name = _next_temp(ctx, "v")
                range_line = "for " + key_name + " := range " + owner + " {"
                append_value = key_name
                if dispatch == "__DICT_VALUES__":
                    range_line = "for _, " + val_name + " := range " + owner + " {"
                    append_value = val_name
                return (
                    "func() []" + item_go_type + " {\n"
                    + "\t" + out_name + " := []" + item_go_type + "{}\n"
                    + "\t" + range_line + "\n"
                    + "\t\t" + out_name + " = append(" + out_name + ", " + append_value + ")\n"
                    + "\t}\n"
                    + "\treturn " + out_name + "\n"
                    + "}()"
                )

    # enumerate / reversed
    if dispatch == "py_enumerate" or bn == "enumerate":
        return "py_enumerate(" + ", ".join(arg_strs) + ")"
    if dispatch == "py_reversed" or bn == "reversed":
        return "py_reversed(" + ", ".join(arg_strs) + ")"

    # abs / min / max / sum
    if bn == "abs" and len(arg_strs) >= 1:
        return "py_abs(" + arg_strs[0] + ")"
    if bn in ("min", "max") or dispatch in ("py_min", "py_max"):
        fn_base = "py_min" if bn == "min" or dispatch == "py_min" else "py_max"
        rt_node = _str(node, "resolved_type")
        # Infer float if any arg is float
        is_float = rt_node in ("float64", "float32")
        if not is_float:
            for a in args:
                if isinstance(a, dict) and _str(a, "resolved_type") in ("float64", "float32"):
                    is_float = True
                    break
        if is_float:
            # Cast all args to float64
            float_args = ["float64(" + s + ")" if isinstance(args[i], dict) and _str(args[i], "resolved_type") not in ("float64", "float32") else s for i, s in enumerate(arg_strs)]
            return fn_base + "_float(" + ", ".join(float_args) + ")"
        return fn_base + "_int(" + ", ".join(arg_strs) + ")"
    if bn == "sum" and len(arg_strs) >= 1:
        return "py_sum(" + arg_strs[0] + ")"
    if bn == "ord" and len(arg_strs) >= 1:
        return "py_ord(" + arg_strs[0] + ")"
    if bn == "chr" and len(arg_strs) >= 1:
        return "py_chr(" + arg_strs[0] + ")"

    # range — handled by ForCore/RuntimeIterForPlan; standalone call fallback
    if bn == "range":
        return "py_range(" + ", ".join(arg_strs) + ")"

    # Exception constructor expression → typed runtime error value
    if bn in ctx.builtin_exc_bounds:
        if len(arg_strs) >= 1:
            return _exception_ctor_expr(ctx, bn, arg_strs[0])
        return _exception_ctor_expr(ctx, bn, _go_string_literal(bn))
    if dispatch == "__PANIC__":
        if len(arg_strs) >= 1:
            return _exception_ctor_expr(ctx, "RuntimeError", arg_strs[0])
        return _exception_ctor_expr(ctx, "RuntimeError", _go_string_literal("runtime error"))

    # py_int_from_str / py_float_from_str
    if dispatch == "py_str_to_int64" and len(arg_strs) >= 1:
        return "py_str_to_int64(" + arg_strs[0] + ")"
    if dispatch == "py_str_to_float64" and len(arg_strs) >= 1:
        return "py_str_to_float64(" + arg_strs[0] + ")"

    # py_to_string
    if dispatch == "py_str":
        if len(arg_strs) >= 1:
            return "py_str(" + arg_strs[0] + ")"
        return "\"\""

    if bn == "index":
        owner_node = node.get("runtime_owner")
        owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
        if owner_rt.startswith("list[") and len(arg_strs) >= 1:
            owner_code = _emit_expr(ctx, owner_node)
            owner_code = _wrapper_container_storage_expr(ctx, owner_node, owner_code)
            return "py_list_index(" + owner_code + ", " + arg_strs[0] + ")"
        if owner_rt == "str" and len(arg_strs) >= 1:
            owner_code = _emit_expr(ctx, owner_node)
            return "py_str_index(" + owner_code + ", " + arg_strs[0] + ")"

    # Use runtime mapping for generic resolution
    if resolved != "":
        return _safe_go_ident(resolved) + "(" + ", ".join(call_arg_strs) + ")"

    # Final fallback: prefix with py_
    fn_name = rc if rc != "" else bn
    if fn_name != "":
        return ctx.mapping.builtin_prefix + _safe_go_ident(fn_name) + "(" + ", ".join(call_arg_strs) + ")"

    return "nil /* unknown builtin */"


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr = _str(node, "attr")
    if attr == "__name__" and isinstance(owner_node, dict) and _str(owner_node, "kind") == "Call":
        call_func = owner_node.get("func")
        call_args = _list(owner_node, "args")
        if isinstance(call_func, dict) and _str(call_func, "kind") == "Name" and _str(call_func, "id") == "type" and len(call_args) >= 1:
            return "py_type_name(" + _emit_expr(ctx, call_args[0]) + ")"
    owner = _emit_expr(ctx, owner_node)
    owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
    if owner_id != "" and attr in ctx.enum_members.get(owner_id, {}):
        return _go_enum_const_name(ctx, owner_id, attr)
    if owner_id != "" and attr in ctx.class_vars.get(owner_id, {}):
        return _go_symbol_name(ctx, owner_id + "_" + attr)
    if _str(node, "attribute_access_kind") == "property_getter":
        return owner + "." + _safe_go_ident(attr) + "()"
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    if owner_rt == "module" or owner_id in ctx.import_alias_modules:
        mod_id = _str(node, "runtime_module_id")
        if mod_id == "":
            mod_id = _str(owner_node, "runtime_module_id") if isinstance(owner_node, dict) else ""
        if mod_id == "":
            mod_id = ctx.import_alias_modules.get(owner_id, "")
        module_symbol_keys: list[str] = []
        if owner_id != "":
            module_symbol_keys.append(owner_id + "." + attr)
        if mod_id != "":
            module_symbol_keys.append(mod_id + "." + attr)
        for symbol_key in module_symbol_keys:
            mapped_value = ctx.mapping.calls.get(symbol_key)
            if isinstance(mapped_value, str) and mapped_value != "":
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", mapped_value):
                    return _safe_go_ident(mapped_value)
                return mapped_value
        if mod_id != "" and should_skip_module(mod_id, ctx.mapping):
            runtime_symbol = _str(node, "runtime_symbol")
            if runtime_symbol == "":
                runtime_symbol = attr
            resolved_name = resolve_runtime_symbol_name(
                runtime_symbol,
                ctx.mapping,
                module_id=mod_id,
                resolved_runtime_call=_str(node, "resolved_runtime_call"),
                runtime_call=_str(node, "runtime_call"),
            )
            if resolved_name != "":
                return _safe_go_ident(resolved_name)
            return ctx.mapping.builtin_prefix + _safe_go_ident(attr)
    if owner_rt != "" and attr in ctx.class_property_methods.get(owner_rt, set()):
        return owner + "." + _safe_go_ident(attr) + "()"
    return owner + "." + _safe_go_ident(attr)


def _attribute_target_type(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    direct = _str(node, "resolved_type")
    if direct not in ("", "unknown"):
        return direct
    owner_node = node.get("value")
    attr = _str(node, "attr")
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    if owner_rt == "" and isinstance(owner_node, dict) and _str(owner_node, "kind") == "Name" and _str(owner_node, "id") == "self":
        owner_rt = ctx.current_class
    if owner_rt != "":
        field_type = ctx.class_fields.get(owner_rt, {}).get(attr, "")
        if field_type != "":
            return field_type
        class_var = ctx.class_vars.get(owner_rt, {}).get(attr)
        if isinstance(class_var, dict):
            var_type = class_var.get("type")
            if isinstance(var_type, str) and var_type != "":
                return var_type
    return ""


def _build_sig_call_args(
    ctx: EmitContext,
    args: list[JsonVal],
    arg_strs: list[str],
    keywords: list[JsonVal],
    sig: dict[str, JsonVal],
    *,
    skip_self: bool = False,
) -> list[str]:
    arg_order_obj = sig.get("arg_order")
    arg_types_obj = sig.get("arg_types")
    arg_defaults_obj = sig.get("arg_defaults")
    arg_order = [p for p in cast(list[JsonVal], arg_order_obj) if isinstance(p, str)] if isinstance(arg_order_obj, list) else []
    arg_types = cast(dict[str, JsonVal], arg_types_obj) if isinstance(arg_types_obj, dict) else {}
    arg_defaults = cast(dict[str, JsonVal], arg_defaults_obj) if isinstance(arg_defaults_obj, dict) else {}
    if skip_self and len(arg_order) > 0 and arg_order[0] == "self":
        arg_order = arg_order[1:]

    kw_nodes: dict[str, JsonVal] = {}
    for kw in keywords:
        if isinstance(kw, dict):
            kw_name = _str(kw, "arg")
            if kw_name != "":
                kw_nodes[kw_name] = kw.get("value")

    out: list[str] = []
    positional_index = 0
    for param_name in arg_order:
        arg_node: JsonVal = None
        arg_code = ""
        if positional_index < len(args):
            arg_node = args[positional_index]
            arg_code = arg_strs[positional_index] if positional_index < len(arg_strs) else ""
            positional_index += 1
        elif param_name in kw_nodes:
            arg_node = kw_nodes[param_name]
            arg_code = _emit_expr(ctx, arg_node)
        elif param_name in arg_defaults:
            arg_node = arg_defaults[param_name]
            arg_code = _emit_expr(ctx, arg_node)
        else:
            continue

        expected_obj = arg_types.get(param_name, "")
        expected_type = expected_obj if isinstance(expected_obj, str) else ""
        if expected_type != "" and isinstance(arg_node, dict):
            actual_type = _effective_resolved_type(ctx, arg_node)
            if _is_container_resolved_type(expected_type):
                if not _is_wrapper_container_expr(ctx, arg_node, arg_code):
                    arg_code = _wrap_ref_container_value_code(ctx, arg_code, expected_type)
            elif _optional_inner_type(expected_type) != "":
                arg_code = _wrap_optional_value_code(ctx, arg_code, expected_type, arg_node)
            elif go_type(actual_type) == go_type(expected_type):
                pass
        out.append(arg_code)
    return out


def _emit_subscript(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value_node = node.get("value")
    value = _emit_expr(ctx, value_node)
    value = _wrapper_container_storage_expr(ctx, value_node, value)
    slice_node = node.get("slice")
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        return _emit_slice_access(ctx, value, slice_node, _str(node, "resolved_type"))
    idx = _emit_expr(ctx, slice_node)

    # Tuple subscript: __tup_N[i] → safe type conversion from any
    if isinstance(value_node, dict):
        vt = _effective_resolved_type(ctx, value_node)
        optional_inner = _optional_inner_type(vt)
        if optional_inner.startswith("tuple["):
            vt = optional_inner
        if vt.startswith("tuple["):
            elem_rt = _str(node, "resolved_type")
            base = value + "[" + idx + "]"
            if elem_rt in ("int64", "int32", "int", "uint8"):
                return "py_to_int64(" + base + ")"
            if elem_rt in ("float64", "float32"):
                return "py_to_float64(" + base + ")"
            if elem_rt == "str":
                return base + ".(string)"
            if elem_rt != "" and elem_rt != "unknown":
                return _coerce_from_any(base, elem_rt)
            return base

    # Negative constant index: x[-1] → x[len(x)-1]
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Constant":
        idx_val = slice_node.get("value")
        if isinstance(idx_val, int) and idx_val < 0:
            idx = "len(" + value + ")" + str(idx_val)
    # Negative unary: x[-expr] → x[len(x)-expr]
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "UnaryOp" and _str(slice_node, "op") == "USub":
        operand = _emit_index_int_expr(ctx, slice_node.get("operand"))
        idx = "len(" + value + ")-" + operand

    # String indexing: wrap with py_byte_to_string for str[int] → string
    if isinstance(value_node, dict):
        vt = _str(value_node, "resolved_type")
        if _is_top_level_union_type(vt):
            slice_rt = _str(slice_node, "resolved_type") if isinstance(slice_node, dict) else ""
            dict_member = _first_union_member(vt, "dict")
            list_member = _first_union_member(vt, "list")
            if dict_member != "" and slice_rt in ("str", "string"):
                if value.endswith(".items"):
                    return value + "[" + idx + "]"
                return _coerce_from_any(value, dict_member) + ".items[" + idx + "]"
            if list_member != "":
                elem_rt = _str(node, "resolved_type")
                int_idx = _emit_index_int_expr(ctx, slice_node)
                if value.endswith(".items"):
                    base = value + "[int(" + int_idx + ")]"
                else:
                    base = _coerce_from_any(value, list_member) + ".items[int(" + int_idx + ")]"
                if elem_rt in ("int64", "int32", "int", "uint8"):
                    return "py_to_int64(" + base + ")"
                if elem_rt == "str":
                    return "py_str(" + base + ")" if go_type(list_member[5:-1] if list_member.startswith("list[") and list_member.endswith("]") else "") == "any" else base
                if elem_rt == "bool":
                    return "py_bool(" + base + ")"
                return base
        if vt == "str":
            return "py_byte_to_string(" + value + "[" + idx + "])"
        if vt.startswith("list[") or vt in ("bytes", "bytearray", "list[uint8]"):
            int_idx = _emit_index_int_expr(ctx, slice_node)
            if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Constant":
                idx_val2 = slice_node.get("value")
                if isinstance(idx_val2, int) and idx_val2 < 0:
                    int_idx = idx
            if isinstance(slice_node, dict) and _str(slice_node, "kind") == "UnaryOp" and _str(slice_node, "op") == "USub":
                int_idx = idx
            return value + "[int(" + int_idx + ")]"
    return value + "[" + idx + "]"


def _emit_index_int_expr(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return _emit_expr(ctx, node)
    kind = _str(node, "kind")
    if kind == "Constant":
        value = node.get("value")
        if isinstance(value, int):
            return str(value)
    if kind == "UnaryOp" and _str(node, "op") == "USub":
        return "-" + _emit_index_int_expr(ctx, node.get("operand"))
    if kind == "BinOp":
        op = _str(node, "op")
        if op in ("Add", "Sub"):
            left = _emit_index_int_expr(ctx, node.get("left"))
            right = _emit_index_int_expr(ctx, node.get("right"))
            symbol = "+" if op == "Add" else "-"
            return "(" + left + " " + symbol + " " + right + ")"
    if kind == "Call":
        func = node.get("func")
        if isinstance(func, dict) and _str(func, "kind") == "Name" and _str(func, "id") == "len":
            args = _list(node, "args")
            if len(args) >= 1:
                arg0 = args[0]
                return "len(" + _wrapper_container_storage_expr(ctx, arg0, _emit_expr(ctx, arg0)) + ")"
    code = _emit_expr(ctx, node)
    if code.startswith("int64(") and code.endswith(")"):
        return code[6:-1]
    if code.startswith("int(") and code.endswith(")"):
        return code[4:-1]
    return code


def _emit_raw_string_subscript(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict) or _str(node, "kind") != "Subscript":
        return ""
    value_node = node.get("value")
    if not isinstance(value_node, dict) or _str(value_node, "resolved_type") != "str":
        return ""
    value = _emit_expr(ctx, value_node)
    slice_node = node.get("slice")
    idx = _emit_expr(ctx, slice_node)
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Constant":
        idx_val = slice_node.get("value")
        if isinstance(idx_val, int) and idx_val < 0:
            idx = "len(" + value + ")" + str(idx_val)
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "UnaryOp" and _str(slice_node, "op") == "USub":
        operand = _emit_expr(ctx, slice_node.get("operand"))
        idx = "len(" + value + ")-" + operand
    return value + "[" + idx + "]"


def _emit_slice_access(
    ctx: EmitContext,
    value: str,
    slice_node: dict[str, JsonVal],
    resolved_type: str = "",
) -> str:
    lower = slice_node.get("lower")
    upper = slice_node.get("upper")
    lo = _emit_slice_bound(ctx, value, lower) if lower is not None else ""
    hi = _emit_slice_bound(ctx, value, upper) if upper is not None else ""
    rendered = value + "[" + lo + ":" + hi + "]"
    if resolved_type == "list" or resolved_type.startswith("list["):
        elem_rt = "any"
        if resolved_type.startswith("list[") and resolved_type.endswith("]"):
            elem_rt = resolved_type[5:-1]
        elem_gt = _go_signature_type(ctx, elem_rt)
        return "PyListFromSlice[" + elem_gt + "](" + rendered + ")"
    return rendered


def _emit_slice_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    return "nil /* slice expr */"


def _emit_slice_bound(ctx: EmitContext, value: str, bound: JsonVal) -> str:
    def _idx(code: str) -> str:
        if code.startswith("int64(len(") and code.endswith("))"):
            return code[6:-1]
        if code.startswith("int64(") and code.endswith(")"):
            return code[6:-1]
        return code
    if not isinstance(bound, dict):
        return _idx(_emit_expr(ctx, bound))
    if _str(bound, "kind") == "Call":
        func = bound.get("func")
        if isinstance(func, dict) and _str(func, "kind") == "Name" and _str(func, "id") == "len":
            args = _list(bound, "args")
            if len(args) >= 1:
                return "len(" + _emit_expr(ctx, args[0]) + ")"
    if _str(bound, "kind") == "UnaryOp" and _str(bound, "op") == "USub":
        operand = bound.get("operand")
        return "(len(" + value + ") - " + _idx(_emit_expr(ctx, operand)) + ")"
    return _idx(_emit_expr(ctx, bound))


def _emit_list_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    rt = _str(node, "resolved_type")
    gt = go_type(rt)
    elem_type = ""
    if rt.startswith("list[") and rt.endswith("]"):
        elem_type = rt[5:-1]
        gt = "[]" + _go_signature_type(ctx, elem_type)
    if elem_type != "":
        child_types = {
            _effective_resolved_type(ctx, e)
            for e in elements
            if isinstance(e, dict) and _effective_resolved_type(ctx, e) not in ("", "unknown")
        }
        optional_inner = _optional_inner_type(elem_type)
        needs_widen = _is_union_like_resolved_type(ctx, elem_type) or any(
            _go_signature_type(ctx, child_type) != _go_signature_type(ctx, elem_type)
            for child_type in child_types
        )
        if optional_inner != "" and _optional_child_types_fit(optional_inner, child_types):
            needs_widen = False
        if needs_widen:
            elem_type = "any"
            gt = "[]any"
    parts = []
    for e in elements:
        code = _emit_expr(ctx, e)
        child_type = _effective_resolved_type(ctx, e) if isinstance(e, dict) else ""
        wrap_type = elem_type if elem_type != "any" else child_type
        if wrap_type != "" and _is_container_resolved_type(wrap_type) and not _is_wrapper_container_expr(ctx, e, code):
            code = _wrap_ref_container_value_code(ctx, code, wrap_type)
        parts.append(code)
    literal = gt + "{" + ", ".join(parts) + "}"
    return literal


def _emit_dict_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    parts: list[str] = []
    key_type = ""
    val_type = ""
    key_gt = ""
    val_gt = ""
    if rt.startswith("dict[") and rt.endswith("]"):
        type_parts = _split_generic_args(rt[5:-1])
        if len(type_parts) == 2:
            key_type = type_parts[0]
            val_type = type_parts[1]
            key_gt = _go_type_with_ctx(ctx, key_type)
            val_gt = _go_signature_type(ctx, val_type)
    value_nodes = [entry.get("value") for entry in _list(node, "entries") if isinstance(entry, dict)]
    if len(value_nodes) == 0:
        value_nodes = _list(node, "values")
    child_val_types = {
        _effective_resolved_type(ctx, value_node)
        for value_node in value_nodes
        if isinstance(value_node, dict) and _effective_resolved_type(ctx, value_node) not in ("", "unknown")
    }
    if val_type != "":
        optional_inner = _optional_inner_type(val_type)
        needs_widen = _is_union_like_resolved_type(ctx, val_type) or any(
            _go_signature_type(ctx, child_type) != _go_signature_type(ctx, val_type)
            for child_type in child_val_types
        )
        if optional_inner != "" and _optional_child_types_fit(optional_inner, child_val_types):
            needs_widen = False
        if needs_widen:
            val_type = "any"
            val_gt = "any"
    gt = ("map[" + key_gt + "]" + val_gt) if (key_gt != "" and val_gt != "") else go_type(rt)

    # EAST3 uses "entries" list of {key, value} dicts
    entries_list = _list(node, "entries")
    if len(entries_list) > 0:
        for entry in entries_list:
            if isinstance(entry, dict):
                key_node = entry.get("key")
                value_node = entry.get("value")
                k = _emit_expr(ctx, key_node)
                v = _emit_expr(ctx, value_node)
                if key_type != "" and isinstance(key_node, dict):
                    if _optional_inner_type(key_type) != "":
                        k = _wrap_optional_value_code(ctx, k, key_type, key_node)
                if isinstance(value_node, dict):
                    actual_val_type = _effective_resolved_type(ctx, value_node)
                    wrap_type = val_type if val_type != "any" else actual_val_type
                    if wrap_type != "" and _is_container_resolved_type(wrap_type) and not _is_wrapper_container_expr(ctx, value_node, v):
                        v = _wrap_ref_container_value_code(ctx, v, wrap_type)
                if val_type != "" and isinstance(value_node, dict):
                    if _optional_inner_type(val_type) != "":
                        v = _wrap_optional_value_code(ctx, v, val_type, value_node)
                parts.append(k + ": " + v)
    else:
        # Fallback: separate keys/values lists
        keys = _list(node, "keys")
        values = _list(node, "values")
        for i in range(len(keys)):
            key_node2 = keys[i] if i < len(keys) else None
            value_node2 = values[i] if i < len(values) else None
            k = _emit_expr(ctx, key_node2) if isinstance(key_node2, dict) else "nil"
            v = _emit_expr(ctx, value_node2) if isinstance(value_node2, dict) else "nil"
            if key_type != "" and isinstance(key_node2, dict):
                if _optional_inner_type(key_type) != "":
                    k = _wrap_optional_value_code(ctx, k, key_type, key_node2)
            if isinstance(value_node2, dict):
                actual_val_type2 = _effective_resolved_type(ctx, value_node2)
                wrap_type2 = val_type if val_type != "any" else actual_val_type2
                if wrap_type2 != "" and _is_container_resolved_type(wrap_type2) and not _is_wrapper_container_expr(ctx, value_node2, v):
                    v = _wrap_ref_container_value_code(ctx, v, wrap_type2)
            if val_type != "" and isinstance(value_node2, dict):
                if _optional_inner_type(val_type) != "":
                    v = _wrap_optional_value_code(ctx, v, val_type, value_node2)
            parts.append(k + ": " + v)

    return gt + "{" + ", ".join(parts) + "}"


def _emit_set_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    rt = _str(node, "resolved_type")
    elem_rt = ""
    if rt.startswith("set[") and rt.endswith("]"):
        elem_rt = rt[4:-1]
    parts = []
    for e in elements:
        value_code = _emit_expr(ctx, e)
        if elem_rt.startswith("tuple[") and elem_rt.endswith("]"):
            value_code = "py_tuple_key(" + value_code + ")"
        parts.append(value_code)
    elem_go = go_type(elem_rt) if elem_rt != "" else "any"
    native_literal = "py_set[" + elem_go + "]([]" + elem_go + "{" + ", ".join(parts) + "})"
    return _wrap_ref_container_value_code(ctx, native_literal, rt)


def _emit_tuple_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    parts = [_emit_expr(ctx, e) for e in elements]
    return "py_tuple_any(" + ", ".join(parts) + ")"


def _emit_covariant_copy(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    source_node = node.get("source")
    source_expr = _emit_expr(ctx, source_node)
    target_type = _str(node, "target_type")
    source_elem_type = _str(node, "source_elem_type")
    target_elem_type = _str(node, "target_elem_type")
    target_go = _go_signature_type(ctx, target_type)
    if not target_go.startswith("[]"):
        return source_expr
    elem_go = target_go[2:]
    out_name = _next_temp(ctx, "cov")
    idx_name = _next_temp(ctx, "i")
    val_name = _next_temp(ctx, "v")
    assign_expr = val_name
    if target_elem_type not in ("", "unknown", "Any", "JsonVal", "object", "Obj"):
        if target_elem_type != source_elem_type:
            assign_expr = _go_signature_type(ctx, target_elem_type) + "(" + val_name + ")"
    return (
        "func() " + target_go + " {\n"
        + "\t" + out_name + " := make(" + target_go + ", len(" + source_expr + "))\n"
        + "\tfor " + idx_name + ", " + val_name + " := range " + source_expr + " {\n"
        + "\t\t" + out_name + "[" + idx_name + "] = " + assign_expr + "\n"
        + "\t}\n"
        + "\treturn " + out_name + "\n"
        + "}()"
    )


def _emit_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test_node = node.get("test")
    body_node = node.get("body")
    orelse_node = node.get("orelse")
    test = _emit_expr(ctx, test_node)
    body = _emit_expr(ctx, body_node)
    orelse = _emit_expr(ctx, orelse_node)
    rt = _str(node, "resolved_type")
    body = _maybe_coerce_expr_to_type(ctx, body_node, body, rt)
    orelse = _maybe_coerce_expr_to_type(ctx, orelse_node, orelse, rt)
    if _is_container_resolved_type(rt):
        if isinstance(body_node, dict) and not _is_wrapper_container_expr(ctx, body_node, body):
            body = _wrap_ref_container_value_code(ctx, body, rt)
        if isinstance(orelse_node, dict) and not _is_wrapper_container_expr(ctx, orelse_node, orelse):
            orelse = _wrap_ref_container_value_code(ctx, orelse, rt)
    if rt in ("int64", "int32", "int", "uint8"):
        # Ensure test is bool (int→bool: != 0)
        test_rt = _str(test_node, "resolved_type") if isinstance(test_node, dict) else ""
        if test_rt in ("int64", "int32", "int", "uint8"):
            test = "(" + test + " != 0)"
        elif test_rt.startswith("list[") or test_rt in ("str", "bytes", "bytearray"):
            test = "len(" + test + ") > 0"
        result_gt = _go_signature_type(ctx, rt)
        return "func() " + result_gt + " { if " + test + " { return " + body + " }; return " + orelse + " }()"
    if rt in ("float64", "float32"):
        result_gt = _go_signature_type(ctx, rt)
        return "func() " + result_gt + " { if " + test + " { return " + body + " }; return " + orelse + " }()"
    if rt == "str":
        return "func() string { if " + test + " { return " + body + " }; return " + orelse + " }()"
    # Fallback: use func literal
    result_gt = _go_signature_type(ctx, rt)
    if result_gt == "":
        result_gt = "any"
    return "func() " + result_gt + " { if " + test + " { return " + body + " }; return " + orelse + " }()"


def _emit_fstring(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    parts: list[str] = []
    for v in values:
        if isinstance(v, dict):
            v_kind = _str(v, "kind")
            if v_kind == "Constant":
                val = v.get("value")
                if isinstance(val, str):
                    parts.append(_go_string_literal(val))
                    continue
            if v_kind == "FormattedValue":
                parts.append(_emit_formatted_value(ctx, v))
            else:
                parts.append("py_str(" + _emit_expr(ctx, v) + ")")
        else:
            parts.append("\"\"")
    if len(parts) == 0:
        return "\"\""
    if len(parts) == 1:
        return parts[0]
    return "(" + " + ".join(parts) + ")"


def _emit_formatted_value(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = _emit_expr(ctx, node.get("value"))
    fs = _str(node, "format_spec")
    if fs != "":
        ctx.imports_needed.add("fmt")
        return "gofmt.Sprintf(\"%" + fs + "\", " + value + ")"
    return "py_str(" + value + ")"


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    if len(arg_order) == 0:
        args_list = _list(node, "args")
        for arg in args_list:
            if isinstance(arg, dict):
                arg_name = _str(arg, "arg")
                if arg_name != "":
                    arg_order.append(arg_name)
                    if arg_name not in arg_types:
                        arg_types[arg_name] = _str(arg, "resolved_type")
    rt = _str(node, "return_type")
    body = node.get("body")

    params: list[str] = []
    for a in arg_order:
        a_name = a if isinstance(a, str) else ""
        a_type = arg_types.get(a_name, "")
        a_type_str = a_type if isinstance(a_type, str) else ""
        params.append(_safe_go_ident(a_name) + " " + _go_signature_type(ctx, a_type_str))

    return_type = _go_signature_type(ctx, rt)
    body_expr = _emit_expr(ctx, body)
    ret_clause = " " + return_type if return_type != "" else ""
    return "func(" + ", ".join(params) + ")" + ret_clause + " { return " + body_expr + " }"


def _emit_isinstance(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value_node = node.get("value")
    if isinstance(value_node, dict) and _str(value_node, "kind") == "Unbox" and isinstance(value_node.get("value"), dict):
        value_node = value_node.get("value")
    if isinstance(value_node, dict) and _str(value_node, "kind") == "Name":
        value = _go_symbol_name(ctx, _str(value_node, "id"))
    else:
        value = _emit_expr(ctx, value_node)
    expected_trait_fqcn = _str(node, "expected_trait_fqcn")
    if expected_trait_fqcn != "":
        raise RuntimeError("go emitter unexpected trait isinstance after link: " + expected_trait_fqcn)
    expected_name = _str(node, "expected_type_name")
    expected = node.get("expected_type_id")
    if isinstance(expected, dict):
        if _str(expected, "kind") == "Tuple":
            checks: list[str] = []
            for elem in _list(expected, "elements"):
                if isinstance(elem, dict):
                    checks.append(_emit_isinstance(ctx, {
                        "kind": "IsInstance",
                        "value": value_node,
                        "expected_type_id": elem,
                    }))
            return "(" + " || ".join(checks) + ")" if len(checks) > 0 else "false"
        if expected_name == "":
            expected_name = _str(expected, "id")
        if expected_name == "":
            expected_name = _str(expected, "repr")
    exact_pod_helpers: dict[str, str] = {
        "bool": "py_is_bool_type",
        "int": "py_is_int",
        "int8": "py_is_exact_int8",
        "uint8": "py_is_exact_uint8",
        "int16": "py_is_exact_int16",
        "uint16": "py_is_exact_uint16",
        "int32": "py_is_exact_int32",
        "uint32": "py_is_exact_uint32",
        "int64": "py_is_exact_int64",
        "uint64": "py_is_exact_uint64",
        "float32": "py_is_exact_float32",
        "float64": "py_is_exact_float64",
    }
    exact_helper = exact_pod_helpers.get(expected_name, "")
    if exact_helper != "":
        return exact_helper + "(" + value + ")"
    builtin_tid_helpers: dict[str, str] = {
        "PYTRA_TID_NONE": "py_is_none",
        "PYTRA_TID_BOOL": "py_is_bool_type",
        "PYTRA_TID_INT": "py_is_int",
        "PYTRA_TID_FLOAT": "py_is_float",
        "PYTRA_TID_STR": "py_is_str",
        "PYTRA_TID_LIST": "py_is_list",
        "PYTRA_TID_DICT": "py_is_dict",
        "list": "py_is_list",
        "dict": "py_is_dict",
        "set": "py_is_set",
    }
    helper_name = builtin_tid_helpers.get(expected_name, "")
    if helper_name != "":
        return helper_name + "(" + value + ")"
    if expected_name == "":
        return "false"
    marker_method = _go_class_marker_method_name(ctx, expected_name)
    marker_helpers: dict[str, str] = {
        "__pytra_is_str": "py_is_str",
        "__pytra_is_list": "py_is_list",
        "__pytra_is_dict": "py_is_dict",
        "__pytra_is_set": "py_is_set",
        "__pytra_is_bool": "py_is_bool_type",
    }
    marker_helper = marker_helpers.get(marker_method, "")
    if marker_helper != "":
        return marker_helper + "(" + value + ")"
    return "func() bool { _, ok := any(" + value + ").(interface{ " + marker_method + "() }); return ok }()"


def _emit_range_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    """Emit a RangeExpr node as py_range(start, stop[, step])."""
    start = node.get("start")
    stop = node.get("stop")
    step = node.get("step")
    args: list[str] = []
    if isinstance(start, dict):
        args.append(_emit_expr(ctx, start))
    if isinstance(stop, dict):
        args.append(_emit_expr(ctx, stop))
    elif not isinstance(start, dict):
        args.append("int64(0)")
    if isinstance(step, dict):
        args.append(_emit_expr(ctx, step))
    return "py_range(" + ", ".join(args) + ")"


def _emit_list_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    gt = go_type(rt)
    elt = node.get("elt")
    generators = _list(node, "generators")
    rendered = _emit_comp_iife(ctx, gt, elt, None, None, generators, "list")
    if _is_container_resolved_type(rt):
        return _wrap_ref_container_value_code(ctx, rendered, rt)
    return rendered


def _emit_set_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    gt = go_type(rt)
    elt = node.get("elt")
    generators = _list(node, "generators")
    rendered = _emit_comp_iife(ctx, gt, elt, None, None, generators, "set")
    if _is_container_resolved_type(rt):
        return _wrap_ref_container_value_code(ctx, rendered, rt)
    return rendered


def _emit_dict_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    gt = go_type(rt)
    key = node.get("key")
    value = node.get("value")
    generators = _list(node, "generators")
    rendered = _emit_comp_iife(ctx, gt, None, key, value, generators, "dict")
    if _is_container_resolved_type(rt):
        return _wrap_ref_container_value_code(ctx, rendered, rt)
    return rendered


def _emit_comp_iife(
    ctx: EmitContext,
    result_type: str,
    elt: JsonVal,
    key: JsonVal,
    value: JsonVal,
    generators: list[JsonVal],
    comp_kind: str,
) -> str:
    """Emit a comprehension as a Go IIFE (immediately invoked function expression).

    [expr for x in iter if cond] →
    func() []T { result := []T{}; for _, x := range iter { if cond { result = append(result, expr) } }; return result }()
    """
    lines: list[str] = []
    indent = "\t"

    lines.append("func() " + result_type + " {")
    if comp_kind == "set":
        lines.append(indent + "__comp_result := " + result_type + "{}")
    elif comp_kind == "dict":
        lines.append(indent + "__comp_result := " + result_type + "{}")
    else:
        lines.append(indent + "__comp_result := " + result_type + "{}")

    # Nest generators
    depth = 1
    for gen in generators:
        if not isinstance(gen, dict):
            continue
        target = gen.get("target")
        iter_expr = gen.get("iter")
        ifs = gen.get("ifs")
        if not isinstance(ifs, list):
            ifs = []

        target_kind = _str(target, "kind") if isinstance(target, dict) else ""
        t_name = ""
        if target_kind == "Name":
            t_name = _str(target, "id")
        if t_name == "":
            t_name = "_"
        t_name = _safe_go_ident(t_name)
        t_type = _str(target, "resolved_type") if isinstance(target, dict) else ""

        iter_code = _emit_expr(ctx, iter_expr)
        iter_code = _wrapper_container_storage_expr(ctx, iter_expr, iter_code)
        iter_rt = _str(iter_expr, "resolved_type") if isinstance(iter_expr, dict) else ""
        pad = indent * depth
        if iter_rt in ("bytearray", "bytes", "list[uint8]"):
            byte_name = _next_temp(ctx, "b")
            lines.append(pad + "for _, " + byte_name + " := range " + iter_code + " {")
            depth += 1
            if t_name != "_":
                if t_type not in ("", "unknown"):
                    bind_rt = t_type
                    bind_gt = _go_signature_type(ctx, bind_rt)
                    bind_code = byte_name if bind_gt in ("byte", "uint8") else bind_gt + "(" + byte_name + ")"
                    lines.append((indent * depth) + "var " + t_name + " " + bind_gt + " = " + bind_code)
                    ctx.var_types[t_name] = bind_rt
                else:
                    lines.append((indent * depth) + t_name + " := " + byte_name)
                    ctx.var_types[t_name] = ""
        elif iter_rt == "str":
            rune_name = _next_temp(ctx, "r")
            lines.append(pad + "for _, " + rune_name + " := range " + iter_code + " {")
            depth += 1
            if t_name != "_":
                bind_code = "string(" + rune_name + ")"
                if t_type not in ("", "unknown"):
                    bind_rt = t_type
                    bind_gt = _go_signature_type(ctx, bind_rt)
                    if bind_gt != "string":
                        bind_code = rune_name
                    lines.append((indent * depth) + "var " + t_name + " " + bind_gt + " = " + bind_code)
                    ctx.var_types[t_name] = bind_rt
                else:
                    lines.append((indent * depth) + t_name + " := " + bind_code)
                    ctx.var_types[t_name] = ""
        else:
            if target_kind == "Tuple":
                item_name = _next_temp(ctx, "tuple_item")
                lines.append(pad + "for _, " + item_name + " := range " + iter_code + " {")
            else:
                lines.append(pad + "for _, " + t_name + " := range " + iter_code + " {")
            depth += 1
            if target_kind == "Tuple" and isinstance(target, dict):
                tuple_type = ""
                if iter_rt.startswith("list[") and iter_rt.endswith("]"):
                    tuple_type = iter_rt[5:-1]
                elif iter_rt.startswith("set[") and iter_rt.endswith("]"):
                    tuple_type = iter_rt[4:-1]
                elements = _list(target, "elements")
                for index, elem in enumerate(elements):
                    if not isinstance(elem, dict):
                        continue
                    elem_name = _safe_go_ident(_str(elem, "id"))
                    if elem_name in ("", "_"):
                        continue
                    elem_type = _str(elem, "resolved_type")
                    sub_node: dict[str, JsonVal] = {
                        "kind": "Subscript",
                        "value": {"kind": "Name", "id": item_name, "resolved_type": tuple_type},
                        "slice": {"kind": "Constant", "value": index, "resolved_type": "int64"},
                        "resolved_type": elem_type,
                    }
                    elem_code = _emit_expr(ctx, sub_node)
                    elem_gt = _go_signature_type(ctx, elem_type)
                    if elem_gt != "" and elem_gt != "any":
                        lines.append((indent * depth) + "var " + elem_name + " " + elem_gt + " = " + elem_code)
                    else:
                        lines.append((indent * depth) + "var " + elem_name + " any = " + elem_code)
                    ctx.var_types[elem_name] = elem_type if elem_type != "" else "unknown"
            elif t_name != "_":
                ctx.var_types[t_name] = t_type if t_type not in ("", "unknown") else ""

        for if_node in ifs:
            if isinstance(if_node, dict):
                cond = _emit_expr(ctx, if_node)
                pad2 = indent * depth
                lines.append(pad2 + "if " + cond + " {")
                depth += 1

    pad = indent * depth
    if comp_kind == "dict":
        k_code = _emit_expr(ctx, key)
        v_code = _emit_expr(ctx, value)
        lines.append(pad + "__comp_result[" + k_code + "] = " + v_code)
    elif comp_kind == "set":
        e_code = _emit_expr(ctx, elt)
        lines.append(pad + "__comp_result[" + e_code + "] = struct{}{}")
    else:
        e_code = _emit_expr(ctx, elt)
        lines.append(pad + "__comp_result = append(__comp_result, " + e_code + ")")

    # Close ifs and generators
    for gen in generators:
        if not isinstance(gen, dict):
            continue
        ifs = gen.get("ifs")
        if isinstance(ifs, list):
            for _ in ifs:
                depth -= 1
                lines.append(indent * depth + "}")
        depth -= 1
        lines.append(indent * depth + "}")

    lines.append(indent + "return __comp_result")
    lines.append("}()")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_stmt(ctx: EmitContext, node: JsonVal) -> None:
    """Emit a statement node."""
    if not isinstance(node, dict):
        return
    if _emit_common_stmt_if_supported(ctx, node):
        return

    kind = _str(node, "kind")

    if kind == "AnnAssign":
        _emit_ann_assign(ctx, node)
    elif kind == "Assign":
        _emit_assign(ctx, node)
    elif kind == "AugAssign":
        _emit_aug_assign(ctx, node)
    elif kind == "ForCore":
        _emit_for_core(ctx, node)
    elif kind == "RuntimeIterForPlan":
        _emit_runtime_iter_for(ctx, node)
    elif kind == "StaticRangeForPlan":
        _emit_static_range_for(ctx, node)
    elif kind == "FunctionDef":
        _emit_function_def(ctx, node)
    elif kind == "ClosureDef":
        _emit_closure_def(ctx, node)
    elif kind == "ClassDef":
        _emit_class_def(ctx, node)
    elif kind == "ImportFrom" or kind == "Import":
        pass  # Imports are handled at module level
    elif kind == "Pass":
        _emit(ctx, "// pass")
    elif kind == "VarDecl":
        _emit_var_decl(ctx, node)
    elif kind == "Swap":
        _emit_swap(ctx, node)
    elif kind in ("MultiAssign", "TupleUnpack"):
        _emit_multi_assign(ctx, node)
    elif kind == "With":
        _emit_with(ctx, node)
    elif kind == "Try":
        _emit_try(ctx, node)
    elif kind == "Raise":
        _emit_raise(ctx, node)
    elif kind == "ErrorReturn":
        _emit_error_return(ctx, node)
    elif kind == "ErrorCheck":
        _emit_error_check(ctx, node)
    elif kind == "ErrorCatch":
        _emit_error_catch(ctx, node)
    elif kind == "TypeAlias":
        _emit_type_alias(ctx, node)
    elif kind == "comment":
        text = _str(node, "text")
        if text != "":
            _emit(ctx, "// " + text)
    elif kind == "blank":
        _emit_blank(ctx)
    else:
        raise RuntimeError("unsupported_stmt_kind: " + kind)


def _emit_body(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        _emit_stmt(ctx, stmt)


def _emit_expr_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if not isinstance(value, dict):
        return
    # String constant at statement level → module docstring, emit as comment
    if _str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
        doc_text = value.get("value")
        if isinstance(doc_text, str) and doc_text.strip() != "":
            for line in doc_text.strip().split("\n"):
                _emit(ctx, "// " + line)
        return
    if _str(value, "kind") == "Call":
        func = value.get("func")
        if isinstance(func, dict) and _str(func, "kind") == "Name":
            fn_name = _str(func, "id")
            mutated_arg = ctx.bytearray_mutating_funcs.get(fn_name, "")
            args = _list(value, "args")
            if mutated_arg != "" and len(args) >= 1 and isinstance(args[0], dict):
                first_arg = args[0]
                first_kind = _str(first_arg, "kind")
                if first_kind == "Name":
                    first_code = _emit_expr(ctx, first_arg)
                    call_code = _emit_call(ctx, value)
                    _emit(ctx, first_code + " = " + call_code)
                    return
    import re
    code = _emit_expr(ctx, value)
    if code != "":
        # Go type assertions `expr.(T)` cannot stand alone as statements; discard with `_ = `.
        if re.search(r'\.\([^)]*\)$', code):
            code = "_ = " + code
        _emit(ctx, code)


def _emit_ann_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_val = node.get("target")
    # Prefer decl_type over resolved_type for variable declarations
    rt = _str(node, "decl_type")
    if rt == "":
        rt = _str(node, "resolved_type")
    value = node.get("value")
    rt = _prefer_value_type_for_none_decl(rt, value)
    gt = _go_signature_type(ctx, rt)

    # target can be a string, Name node, or Attribute node
    target_name = ""
    is_attr_target = False
    if isinstance(target_val, str):
        target_name = target_val
    elif isinstance(target_val, dict):
        if _str(target_val, "kind") == "Attribute":
            # self.x = ... → emit as attribute assignment
            is_attr_target = True
        else:
            target_name = _str(target_val, "id")
            if target_name == "":
                target_name = _str(target_val, "repr")
    if target_name == "" and not is_attr_target:
        tn = node.get("target_node")
        if isinstance(tn, dict):
            target_name = _str(tn, "id")

    if is_attr_target:
        lhs = _emit_expr(ctx, target_val)
        if value is not None:
            val_code = _emit_expr(ctx, value)
            if isinstance(target_val, dict):
                target_type = _attribute_target_type(ctx, target_val)
                if target_type != "":
                    val_code = _maybe_coerce_expr_to_type(ctx, value, val_code, target_type)
                    if _is_container_resolved_type(target_type):
                        val_rtype = _str(value, "resolved_type") if isinstance(value, dict) else ""
                        val_kind = _str(value, "kind") if isinstance(value, dict) else ""
                        is_call_returning_container = (
                            val_kind == "Call" and _is_container_resolved_type(val_rtype)
                        )
                        if not is_call_returning_container:
                            val_code = _wrap_ref_container_value_code(ctx, val_code, target_type)
            _emit(ctx, lhs + " = " + val_code)
        return

    name = _go_symbol_name(ctx, target_name)
    declare_new = name not in ctx.var_types and not _bool(node, "is_reassign")
    if declare_new:
        ctx.var_types[name] = rt
        ctx.var_decl_depth[name] = ctx.indent_level
    is_suppressed_unused = _bool(node, "unused") or name.startswith("_")
    at_module_scope = ctx.indent_level == 0 and ctx.current_class == "" and ctx.current_return_type == ""

    if value is not None:
        val_code = _emit_expr(ctx, value)
        val_code = _maybe_coerce_expr_to_type(ctx, value, val_code, rt)
        use_ref_decl = _assign_uses_ref_container_decl(ctx, name, rt, value)
        if use_ref_decl:
            val_code = _wrap_ref_container_value_code(ctx, val_code, rt)
        # map[K]V target with *PyDict assertion: extract .items
        if not use_ref_decl:
            _eff_gt = _go_signature_type(ctx, rt)
            if _eff_gt.startswith("map[") and ".(*PyDict[" in val_code and not val_code.endswith(".items"):
                val_code = val_code + ".items"
        if not declare_new:
            _emit(ctx, name + " = " + val_code)
        else:
            if use_ref_decl:
                gt = _decl_go_type(ctx, rt, name)
            else:
                gt = _go_signature_type(ctx, rt)
            if gt != "":
                _emit(ctx, "var " + name + " " + gt + " = " + val_code)
            elif at_module_scope:
                _emit(ctx, "var " + name + " any = " + val_code)
            else:
                _emit(ctx, name + " := " + val_code)
            if not at_module_scope and name != "_":
                _emit(ctx, "_ = " + name)
        if use_ref_decl:
            ctx.ref_container_locals.add(name)
        else:
            ctx.ref_container_locals.discard(name)
    else:
        if declare_new:
            _emit(ctx, "var " + name + " " + gt + " = " + _decl_go_zero_value(ctx, rt, name))
            if not at_module_scope and name != "_":
                _emit(ctx, "_ = " + name)
            if _is_container_resolved_type(rt) and not _prefer_value_container_local(ctx, name, rt):
                ctx.ref_container_locals.add(name)
            else:
                ctx.ref_container_locals.discard(name)
    if is_suppressed_unused and name != "_" and not at_module_scope:
        _emit(ctx, "_ = " + name)


def _emit_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    value = node.get("value")

    # EAST3 may use "target" (single) or "targets" (list)
    target_single = node.get("target")
    if len(targets) == 0 and isinstance(target_single, dict):
        targets = [target_single]
    if len(targets) == 0:
        return

    # Skip union type alias declarations: X = Union[...] has no runtime meaning in Go
    if len(targets) == 1 and isinstance(targets[0], dict) and _str(targets[0], "kind") in ("Name", "NameTarget"):
        if _str(targets[0], "id") in ctx.union_type_aliases:
            return

    val_code = _emit_expr(ctx, value)
    target_node = targets[0]

    # unused=True + declare=True → assign but add _ = var to suppress Go's unused error
    is_unused = _bool(node, "unused") and _bool(node, "declare")
    at_module_scope = ctx.indent_level == 0 and ctx.current_class == "" and ctx.current_return_type == ""

    if isinstance(target_node, dict):
        t_kind = _str(target_node, "kind")
        if t_kind == "Name" or t_kind == "NameTarget":
            name = _str(target_node, "id")
            if name == "":
                name = _str(target_node, "repr")
            gn = _go_symbol_name(ctx, name)
            if gn == "_":
                _emit(ctx, "_ = " + val_code)
                return
            if gn in ctx.var_types:
                existing_type = ctx.var_types.get(gn, "")
                if existing_type != "":
                    val_code = _maybe_coerce_expr_to_type(ctx, value, val_code, existing_type)
                    if _is_container_resolved_type(existing_type):
                        # Skip wrapping for function/method calls that already return a ref-container type.
                        val_rtype = _str(value, "resolved_type") if isinstance(value, dict) else ""
                        val_kind = _str(value, "kind") if isinstance(value, dict) else ""
                        is_call_returning_container = (
                            val_kind == "Call" and _is_container_resolved_type(val_rtype)
                        )
                        if not is_call_returning_container:
                            val_code = _wrap_ref_container_value_code(ctx, val_code, existing_type)
                    else:
                        # map[K]V target with *PyDict assertion: extract .items
                        _exist_gt = go_type(existing_type)
                        if _exist_gt.startswith("map[") and ".(*PyDict[" in val_code and not val_code.endswith(".items"):
                            val_code = val_code + ".items"
                _emit(ctx, gn + " = " + val_code)
                if is_unused:
                    _emit(ctx, "_ = " + gn)
            else:
                # Check for decl_type on the Assign node, target, or value
                decl_type = _str(node, "decl_type")
                if decl_type == "" or decl_type == "unknown":
                    decl_type = _str(target_node, "resolved_type")
                if decl_type == "" or decl_type == "unknown":
                    decl_type = _effective_resolved_type(ctx, value) if isinstance(value, dict) else decl_type
                if (
                    (decl_type == "" or decl_type == "unknown")
                    and isinstance(value, dict)
                    and _str(value, "kind") == "Subscript"
                ):
                    tuple_owner = value.get("value")
                    tuple_slice = value.get("slice")
                    tuple_name = _str(tuple_owner, "id") if isinstance(tuple_owner, dict) else ""
                    tuple_type = ctx.var_types.get(tuple_name, "")
                    if tuple_type.startswith("tuple[") and tuple_type.endswith("]") and isinstance(tuple_slice, dict):
                        idx_value = tuple_slice.get("value")
                        if isinstance(idx_value, int):
                            tuple_args = _split_generic_args(tuple_type[6:-1])
                            if 0 <= idx_value < len(tuple_args):
                                decl_type = tuple_args[idx_value]
                decl_type = _prefer_value_type_for_none_decl(decl_type, value)
                val_code = _maybe_coerce_expr_to_type(ctx, value, val_code, decl_type)
                use_ref_decl = _assign_uses_ref_container_decl(ctx, gn, decl_type, value)
                if use_ref_decl:
                    val_code = _wrap_ref_container_value_code(ctx, val_code, decl_type)
                if (
                    isinstance(value, dict)
                    and _str(value, "kind") == "Name"
                    and decl_type.startswith("list[")
                ):
                    source_name = _go_symbol_name(ctx, _str(value, "id"))
                    source_type = ctx.var_types.get(source_name, _str(value, "resolved_type"))
                    if source_name != "" and source_type.startswith("list["):
                        ctx.var_types[gn] = decl_type
                        if _prefer_value_container_local(ctx, gn, decl_type):
                            ctx.list_alias_vars.add(gn)
                            _emit(ctx, gn + " := &" + source_name)
                        else:
                            _emit(ctx, "var " + gn + " " + _decl_go_type(ctx, decl_type, gn) + " = " + source_name)
                        if is_unused:
                            _emit(ctx, "_ = " + gn)
                        if gn.startswith("_") and gn != "_":
                            _emit(ctx, "_ = " + gn)
                        if use_ref_decl:
                            ctx.ref_container_locals.add(gn)
                        else:
                            ctx.ref_container_locals.discard(gn)
                        return
                ctx.var_types[gn] = decl_type
                ctx.var_decl_depth[gn] = ctx.indent_level
                if use_ref_decl:
                    gt = _decl_go_type(ctx, decl_type, gn)
                else:
                    gt = _go_signature_type(ctx, decl_type)
                if gt != "":
                    _emit(ctx, "var " + gn + " " + gt + " = " + val_code)
                else:
                    if at_module_scope:
                        _emit(ctx, "var " + gn + " any = " + val_code)
                    else:
                        _emit(ctx, gn + " := " + val_code)
                if not at_module_scope and gn != "_":
                    _emit(ctx, "_ = " + gn)
                if use_ref_decl:
                    ctx.ref_container_locals.add(gn)
                else:
                    ctx.ref_container_locals.discard(gn)
                if is_unused and not at_module_scope:
                    _emit(ctx, "_ = " + gn)
            if gn.startswith("_") and gn != "_" and not at_module_scope:
                _emit(ctx, "_ = " + gn)
        elif t_kind == "Attribute":
            target_type = _attribute_target_type(ctx, target_node)
            if target_type != "":
                val_code = _maybe_coerce_expr_to_type(ctx, value, val_code, target_type)
                if _is_container_resolved_type(target_type):
                    val_code = _wrap_ref_container_value_code(ctx, val_code, target_type)
            _emit(ctx, _emit_expr(ctx, target_node) + " = " + val_code)
        elif t_kind == "Subscript":
            # Byte subscript assignment: p[i] = v → p[i] = byte(v)
            sub_val = target_node.get("value")
            sub_id = _str(sub_val, "id") if isinstance(sub_val, dict) else ""
            sub_type = ctx.var_types.get(sub_id, "")
            if sub_type in ("bytes", "bytearray"):
                val_code = "byte(" + val_code + ")"
            store_value = _emit_expr(ctx, sub_val)
            store_value = _wrapper_container_storage_expr(ctx, sub_val, store_value)
            store_slice = target_node.get("slice")
            if isinstance(store_slice, dict) and _str(store_slice, "kind") == "Slice":
                _emit(ctx, _emit_expr(ctx, target_node) + " = " + val_code)
            else:
                store_idx = _emit_expr(ctx, store_slice)
                if sub_type.startswith("list[") or sub_type in ("bytes", "bytearray", "list[uint8]"):
                    store_idx = "int(" + _emit_index_int_expr(ctx, store_slice) + ")"
                _emit(ctx, store_value + "[" + store_idx + "] = " + val_code)
        elif t_kind == "Tuple":
            # Some precompiled EAST3 modules still carry tuple targets directly.
            # Go emitter models tuple values as []any, so unpack through a temp.
            elts = _list(target_node, "elements")
            tuple_rt = _str(value, "resolved_type") if isinstance(value, dict) else ""
            if tuple_rt == "":
                tuple_rt = _str(target_node, "resolved_type")
            temp_name = _next_temp(ctx, "tuple_assign")
            ctx.var_types[temp_name] = tuple_rt if tuple_rt != "" else "tuple"
            temp_gt = _go_signature_type(ctx, tuple_rt)
            if temp_gt in ("", "any"):
                temp_gt = "[]any"
            _emit(ctx, "var " + temp_name + " " + temp_gt + " = " + val_code)
            for i, elem in enumerate(elts):
                if not isinstance(elem, dict):
                    continue
                elem_rt = _str(elem, "resolved_type")
                sub_node: dict[str, JsonVal] = {
                    "kind": "Subscript",
                    "value": {"kind": "Name", "id": temp_name, "resolved_type": tuple_rt},
                    "slice": {"kind": "Constant", "value": i, "resolved_type": "int64"},
                    "resolved_type": elem_rt,
                }
                assign_node: dict[str, JsonVal] = {
                    "kind": "Assign",
                    "target": elem,
                    "value": sub_node,
                    "declare": True,
                    "decl_type": elem_rt,
                }
                _emit_assign(ctx, assign_node)
        else:
            _emit(ctx, "_ = " + val_code + " // assign to " + t_kind)
    else:
        _emit(ctx, "_ = " + val_code)


def _emit_multi_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    target_types = _list(node, "target_types")
    if len(targets) == 0:
        return
    value_node = node.get("value")
    value_type = _str(value_node, "resolved_type") if isinstance(value_node, dict) else ""
    lhs_parts: list[str] = []
    existing_targets: dict[str, bool] = {}
    for idx, target in enumerate(targets):
        if not isinstance(target, dict):
            continue
        kind = _str(target, "kind")
        if kind not in ("Name", "NameTarget"):
            _emit(ctx, "// unsupported multi-assign target: " + kind)
            return
        name = _safe_go_ident(_str(target, "id"))
        if name == "":
            name = "_"
        lhs_parts.append(name)
        if name == "_":
            continue
        existing_targets[name] = name in ctx.var_types
        resolved_type = _str(target, "resolved_type")
        if resolved_type in ("", "unknown") and idx < len(target_types):
            type_obj = target_types[idx]
            if isinstance(type_obj, str):
                resolved_type = type_obj
        if resolved_type not in ("", "unknown"):
            # Only pre-register if already declared; new variable declarations are
            # registered by _emit_assign itself (pre-registering prevents var declaration).
            if existing_targets[name]:
                ctx.var_types[name] = resolved_type
    if len(lhs_parts) == 0:
        return
    # tuple-returning function calls use Go multi-return syntax directly.
    is_tuple_call = (
        isinstance(value_node, dict)
        and _str(value_node, "kind") == "Call"
        and len(targets) > 1
        and not value_type.startswith("multi_return[")
        and not _is_container_resolved_type(value_type)
    )
    if isinstance(value_node, dict) and _str(value_node, "kind") == "Call":
        func_node = value_node.get("func")
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
            fn_name = _str(func_node, "id")
            if fn_name == "main":
                fn_name = "__pytra_main"
            if ctx.function_return_types.get(fn_name, "").startswith("tuple["):
                is_tuple_call = True
    if not value_type.startswith("multi_return[") and not is_tuple_call:
        tmp_name = _next_temp(ctx, "multi")
        tmp_expr = _emit_expr(ctx, value_node)
        _emit(ctx, tmp_name + " := " + tmp_expr)
        if value_type != "" and not (
            value_type.startswith("list[")
            and isinstance(value_node, dict)
            and not _is_wrapper_container_expr(ctx, value_node, tmp_expr)
        ):
            ctx.var_types[tmp_name] = value_type
        for idx, target in enumerate(targets):
            if not isinstance(target, dict):
                continue
            target_name = _safe_go_ident(_str(target, "id"))
            declare_target = _bool(node, "declare") and not existing_targets.get(target_name, False)
            resolved_type = _str(target, "resolved_type")
            if resolved_type in ("", "unknown") and idx < len(target_types):
                type_obj2 = target_types[idx]
                if isinstance(type_obj2, str):
                    resolved_type = type_obj2
            value_expr: Node = {}
            value_expr["kind"] = "Subscript"
            value_expr["value"] = {"kind": "Name", "id": tmp_name, "resolved_type": value_type}
            value_expr["slice"] = {"kind": "Constant", "value": idx, "resolved_type": "int64"}
            value_expr["resolved_type"] = resolved_type
            assign_node: Node = {}
            assign_node["kind"] = "Assign"
            assign_node["target"] = target
            assign_node["value"] = value_expr
            assign_node["declare"] = declare_target
            if resolved_type not in ("", "unknown"):
                assign_node["decl_type"] = resolved_type
            _emit_assign(ctx, assign_node)
        return
    assign_op = ":=" if _bool(node, "declare") else "="
    if is_tuple_call:
        # Use = only if all pre-existing targets were declared at an outer (shallower) scope.
        # Variables declared in a sibling if/else branch are block-scoped in Go and
        # must be re-declared with := rather than assigned with =.
        all_outer_scope = all(
            existing_targets.get(n, False)
            and ctx.var_decl_depth.get(n, ctx.indent_level) < ctx.indent_level
            for n in lhs_parts if n != "_"
        )
        assign_op = "=" if all_outer_scope else ":="
    _emit(ctx, ", ".join(lhs_parts) + " " + assign_op + " " + _emit_expr(ctx, node.get("value")))
    if is_tuple_call and assign_op == ":=":
        # Suppress Go "declared and not used" errors — the variable may only be used later
        # in certain branches, so preemptively discard all newly-declared names.
        for n in lhs_parts:
            if n != "_" and not existing_targets.get(n, False):
                _emit(ctx, "_ = " + n)
    # Register newly-declared variables in var_types for subsequent statements.
    for idx2, target2 in enumerate(targets):
        if not isinstance(target2, dict):
            continue
        tname2 = _safe_go_ident(_str(target2, "id"))
        if tname2 in ("", "_") or existing_targets.get(tname2, True):
            continue
        rt2 = _str(target2, "resolved_type")
        if rt2 in ("", "unknown") and idx2 < len(target_types):
            to2 = target_types[idx2]
            if isinstance(to2, str):
                rt2 = to2
        if rt2 not in ("", "unknown"):
            ctx.var_types[tname2] = rt2
            ctx.var_decl_depth[tname2] = ctx.indent_level


def _emit_aug_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    op = _str(node, "op")
    go_op = _BINOP_MAP.get(op, "+")
    t_code = _emit_expr(ctx, target)
    v_code = _emit_expr(ctx, value)
    target_rt = _str(target, "resolved_type") if isinstance(target, dict) else ""
    if target_rt == "" and t_code in ctx.var_types:
        target_rt = ctx.var_types[t_code]
    _emit(ctx, t_code + " " + go_op + "= " + v_code)


def _emit_return(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if value is None:
        if ctx.constructor_return_target != "":
            _emit(ctx, "return " + ctx.constructor_return_target)
            return
        if _is_exception_type_name(ctx, ctx.current_return_type):
            _emit(ctx, "return nil")
            return
        if ctx.current_return_type.startswith("multi_return["):
            _emit(ctx, "return " + _zero_return_values(ctx.current_return_type))
            return
        _emit(ctx, "return")
    else:
        if (
            ctx.current_return_type.startswith("multi_return[")
            and isinstance(value, dict)
            and _str(value, "kind") == "Tuple"
        ):
            elements = _list(value, "elements")
            parts: list[str] = []
            for elem in elements:
                if isinstance(elem, dict):
                    parts.append(_emit_expr(ctx, elem))
            _emit(ctx, "return " + ", ".join(parts))
            return
        value_code = _emit_expr(ctx, value)
        if isinstance(value, dict) and _str(value, "kind") == "Name":
            scope_name = _go_symbol_name(ctx, _str(value, "id"))
            scope_type = ctx.var_types.get(scope_name, "")
            if scope_type != "" and scope_type == ctx.current_return_type and _optional_inner_type(scope_type) != "":
                value_code = scope_name
        optional_inner = _optional_inner_type(ctx.current_return_type)
        if optional_inner != "":
            if isinstance(value, dict):
                source_type = _str(value, "resolved_type")
                scope_type = ""
                if _str(value, "kind") == "Name":
                    scope_name = _go_symbol_name(ctx, _str(value, "id"))
                    scope_type = ctx.var_types.get(scope_name, "")
                if (
                    source_type in ("JsonVal", "Any", "Obj", "object", "unknown")
                    or go_type(source_type) == "any"
                    or (go_type(scope_type) == "any" and scope_type != "")
                ):
                    value_code = _coerce_from_any(value_code, optional_inner)
            value_code = _wrap_optional_value_code(ctx, value_code, ctx.current_return_type, value)
        if _is_exception_type_name(ctx, ctx.current_return_type):
            _emit(ctx, "return pytraEnsureRecoveredError(" + value_code + ")")
            return
        if _is_container_resolved_type(ctx.current_return_type):
            if not _is_wrapper_container_expr(ctx, value, value_code):
                value_code = _wrap_ref_container_value_code(ctx, value_code, ctx.current_return_type)
        if ctx.current_return_type.startswith("multi_return["):
            # If the value is a Call that already returns the same multi_return type,
            # pass through directly — adding ", nil" would create too many return values.
            if isinstance(value, dict) and _str(value, "kind") == "Call":
                val_rt = _str(value, "resolved_type")
                if val_rt == ctx.current_return_type or val_rt.startswith("tuple["):
                    _emit(ctx, "return " + value_code)
                    return
            _emit(ctx, "return " + value_code + ", nil")
            return
        _emit(ctx, "return " + value_code)


def _zero_return_values(return_type: str) -> str:
    # Note: exception types (e.g. "Exception") map to pointer types via go_type(),
    # so go_zero_value() already returns "nil" for them — no special-case needed.
    if return_type.startswith("multi_return[") and return_type.endswith("]"):
        inner = return_type[len("multi_return["):-1]
        parts = _split_generic_args(inner)
        zeros: list[str] = []
        for part in parts:
            zeros.append(go_zero_value(part))
        return ", ".join(zeros)
    return go_zero_value(return_type)


def _emit_for_core(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")

    # ForCore uses iter_plan + target_plan (EAST3 lowered form)
    iter_plan = node.get("iter_plan")
    target_plan = node.get("target_plan")

    if isinstance(iter_plan, dict):
        ip_kind = _str(iter_plan, "kind")
        t_name = ""
        t_type = ""
        if isinstance(target_plan, dict):
            t_name = _str(target_plan, "id")
            t_type = _str(target_plan, "target_type")
        t_name = _safe_go_ident(t_name) if t_name != "" else "_"

        if ip_kind == "StaticRangeForPlan":
            _emit_range_for(ctx, t_name, t_type, iter_plan, body)
            return
        if ip_kind == "RuntimeIterForPlan":
            # Check if this is a range (has start/stop) or a collection iter (has iter_expr)
            if iter_plan.get("start") is not None or iter_plan.get("stop") is not None:
                _emit_range_for(ctx, t_name, t_type, iter_plan, body)
            else:
                # Collection iterator: for _, item := range collection
                iter_expr = iter_plan.get("iter_expr")
                old_skip_any = ctx.skip_any_coercion
                ctx.skip_any_coercion = True
                iter_code = _emit_expr(ctx, iter_expr) if iter_expr is not None else "nil"
                ctx.skip_any_coercion = old_skip_any
                iter_code = _wrapper_container_storage_expr(ctx, iter_expr, iter_code)
                if iter_code.startswith("py_items(") and iter_code.endswith(".items"):
                    iter_code = iter_code[:-6]
                # Detect byte slice iteration → cast to int64
                iter_rt = _str(iter_expr, "resolved_type") if isinstance(iter_expr, dict) else ""
                # If wrapper extraction added .items, the result is a native Go slice — treat as list type
                if iter_rt in ("unknown", "", "Any", "Obj", "object", "JsonVal") and iter_code.endswith(".items"):
                    scope_name = iter_code[:-6]
                    scope_type = ctx.var_types.get(scope_name, "")
                    if scope_type != "" and _is_container_resolved_type(scope_type):
                        iter_rt = scope_type
                # Look up var type for plain name references (e.g. Go variadic params)
                if iter_rt in ("unknown", "", "Any", "Obj", "object", "JsonVal"):
                    scope_type = ctx.var_types.get(iter_code, "")
                    if scope_type != "" and _is_container_resolved_type(scope_type):
                        iter_rt = scope_type
                if _is_top_level_union_type(iter_rt):
                    list_member = _first_union_member(iter_rt, "list")
                    if list_member != "":
                        iter_code = _coerce_from_any(iter_code, list_member) + ".items"
                        iter_rt = list_member
                if iter_rt in ("bytearray", "bytes", "list[uint8]"):
                    _emit(ctx, "for _, _byte_ := range " + iter_code + " {")
                    ctx.indent_level += 1
                    if t_type not in ("", "unknown"):
                        bind_rt = t_type
                        bind_gt = _go_signature_type(ctx, bind_rt)
                        bind_code = "_byte_" if bind_gt in ("byte", "uint8") else bind_gt + "(_byte_)"
                        _emit(ctx, "var " + t_name + " " + bind_gt + " = " + bind_code)
                        ctx.var_types[t_name] = bind_rt
                    elif t_name != "_":
                        _emit(ctx, t_name + " := _byte_")
                        ctx.var_types[t_name] = ""
                elif iter_rt == "str":
                    rune_name = _next_temp(ctx, "r")
                    _emit(ctx, "for _, " + rune_name + " := range " + iter_code + " {")
                    ctx.indent_level += 1
                    if t_name != "_":
                        bind_code = "string(" + rune_name + ")"
                        if t_type not in ("", "unknown"):
                            bind_rt = t_type
                            bind_gt = _go_signature_type(ctx, bind_rt)
                            if bind_gt != "string":
                                bind_code = rune_name
                            _emit(ctx, "var " + t_name + " " + bind_gt + " = " + bind_code)
                            ctx.var_types[t_name] = bind_rt
                        else:
                            _emit(ctx, t_name + " := " + bind_code)
                            ctx.var_types[t_name] = ""
                elif iter_rt.startswith("set[") or iter_rt.startswith("dict["):
                    _emit(ctx, "for " + t_name + " := range " + iter_code + " {")
                    ctx.indent_level += 1
                    if t_name != "_":
                        if t_type != "":
                            ctx.var_types[t_name] = t_type
                        else:
                            ctx.var_types[t_name] = ""
                elif iter_rt in ("JsonVal", "Any", "Obj", "object", "unknown"):
                    _emit(ctx, "for _, " + t_name + " := range py_iter(" + iter_code + ") {")
                    ctx.indent_level += 1
                    if t_name != "_" and t_type not in ("", "unknown"):
                        ctx.var_types[t_name] = t_type
                    else:
                        ctx.var_types[t_name] = ""
                else:
                    _emit(ctx, "for _, " + t_name + " := range " + iter_code + " {")
                    ctx.indent_level += 1
                    if t_name != "_" and t_type not in ("", "unknown"):
                        ctx.var_types[t_name] = t_type
                    else:
                        ctx.var_types[t_name] = ""
                _emit_body(ctx, body)
                ctx.indent_level -= 1
                _emit(ctx, "}")
            return

    # Fallback: legacy target/iter form
    target = node.get("target")
    iter_expr = node.get("iter")

    t_name = ""
    if isinstance(target, dict):
        t_name = _str(target, "id")
        if t_name == "":
            t_name = _str(target, "repr")
    t_name = _safe_go_ident(t_name) if t_name != "" else "_"

    old_skip_any = ctx.skip_any_coercion
    ctx.skip_any_coercion = True
    iter_code = _emit_expr(ctx, iter_expr)
    ctx.skip_any_coercion = old_skip_any
    if iter_code.startswith("py_items(") and iter_code.endswith(".items"):
        iter_code = iter_code[:-6]
    _emit(ctx, "for _, " + t_name + " := range " + iter_code + " {")
    ctx.indent_level += 1
    ctx.var_types[t_name] = ""
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_range_for(
    ctx: EmitContext,
    t_name: str,
    t_type: str,
    plan: dict[str, JsonVal],
    body: list[JsonVal],
) -> None:
    """Emit a range-based for loop from StaticRangeForPlan or RuntimeIterForPlan."""
    start = plan.get("start")
    stop = plan.get("stop")
    step = plan.get("step")

    s_code = _emit_expr(ctx, start) if start is not None else "0"
    e_code = _emit_expr(ctx, stop) if stop is not None else "0"

    # Determine step
    step_code = "1"
    step_negative = False
    if isinstance(step, dict) and _str(step, "kind") == "Constant":
        sv = step.get("value")
        if isinstance(sv, int):
            step_code = str(sv)
            step_negative = sv < 0
    elif step is not None:
        step_code = _emit_expr(ctx, step)
        stripped_step = step_code.strip()
        if stripped_step.startswith("-") or stripped_step.startswith("(-"):
            step_negative = True

    cmp_op = " > " if step_negative else " < "
    # Use = if variable already declared (VarDecl), else :=
    # For blank identifier _, use a temp var name
    loop_var = t_name
    if loop_var == "_":
        loop_var = "_loop_"
    assign_op = " = " if loop_var in ctx.var_types else " := "
    bind_rt = ""
    start_code = s_code
    stop_code = e_code
    step_bind_code = step_code
    if t_type not in ("", "unknown"):
        bind_rt = t_type
        bind_gt = _go_signature_type(ctx, bind_rt)
        if bind_gt in ("", "any"):
            raise RuntimeError("range_target_type_required")
        start_code = bind_gt + "(" + s_code + ")"
        stop_code = bind_gt + "(" + e_code + ")"
        step_bind_code = bind_gt + "(" + step_code + ")"
    _emit(ctx, "for " + loop_var + assign_op + start_code + "; " + loop_var + cmp_op + stop_code + "; " + loop_var + " += " + step_bind_code + " {")
    ctx.indent_level += 1
    if t_name != "_" and bind_rt != "":
        ctx.var_types[t_name] = bind_rt
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_runtime_iter_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """RuntimeIterForPlan as standalone statement (outside ForCore)."""
    target = node.get("target")
    body = _list(node, "body")
    t_name = ""
    t_type = _str(node, "target_type")
    if isinstance(target, dict):
        t_name = _str(target, "id")
        if t_type in ("", "unknown"):
            t_type = _str(target, "resolved_type")
    t_name = _safe_go_ident(t_name) if t_name != "" else "_"
    _emit_range_for(ctx, t_name, t_type, node, body)


def _emit_static_range_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """StaticRangeForPlan as standalone statement (outside ForCore)."""
    _emit_runtime_iter_for(ctx, node)


def _scan_body_for_return_type(body: list) -> str:
    """Find the resolved_type of the first Return-with-value in body (shallow recursion)."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind == "Return":
            val = stmt.get("value")
            if isinstance(val, dict):
                rt = _str(val, "resolved_type")
                if rt not in ("", "None", "NoneType"):
                    return rt
        elif kind in ("If", "Try"):
            for subkey in ("body", "orelse", "handlers", "finalbody"):
                sub = _list(stmt, subkey)
                rt = _scan_body_for_return_type(sub)
                if rt != "":
                    return rt
    return ""


def _emit_function_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    return_type = _str(node, "return_type")
    body = _list(node, "body")
    decorators = _list(node, "decorators")
    vararg_info = _dict(node, "vararg_desugared_v1")
    vararg_name = _str(vararg_info, "vararg_name") if isinstance(vararg_info, dict) else ""
    vararg_elem_type = _str(vararg_info, "elem_type") if isinstance(vararg_info, dict) else ""
    vararg_list_type = _str(vararg_info, "list_type") if isinstance(vararg_info, dict) else ""
    # Fall back to direct vararg_name/vararg_type fields when vararg_desugared_v1 is absent.
    if vararg_name == "":
        vararg_name = _str(node, "vararg_name")
        vararg_elem_type = _str(node, "vararg_type")
        vararg_list_type = ""

    # Skip extern declarations
    for d in decorators:
        if isinstance(d, str) and d == "extern":
            return

    fn_name = _go_symbol_name(ctx, "__pytra_main" if name == "main" else name)
    # If function has no annotation (return_type="None") but body returns a value, infer it.
    mutated_arg_name = ctx.bytearray_mutating_funcs.get(name, "")
    if return_type in ("None", "") and not mutated_arg_name:
        inferred = _scan_body_for_return_type(body)
        if inferred not in ("", "None", "NoneType"):
            return_type = inferred
    if name != "":
        ctx.function_return_types[name] = return_type
    go_ret = _go_signature_type(ctx, return_type)
    mutated_return = mutated_arg_name != "" and return_type == "None"
    is_staticmethod = False
    for d in decorators:
        if isinstance(d, str) and d == "staticmethod":
            is_staticmethod = True
            break

    # Build params
    params: list[str] = []
    saved_vars = dict(ctx.var_types)
    saved_decl_depth = dict(ctx.var_decl_depth)
    saved_scope = ctx.current_function_scope
    saved_scope_locals = set(ctx.current_value_container_locals)
    saved_ref_locals = set(ctx.ref_container_locals)
    saved_vararg_params = set(ctx.go_vararg_params)
    ctx.var_decl_depth = {}
    for a in arg_order:
        a_str = a if isinstance(a, str) else ""
        if a_str == "self":
            continue
        a_type_val = arg_types.get(a_str, "")
        a_type = a_type_val if isinstance(a_type_val, str) else ""
        ga = _safe_go_ident(a_str)
        gt = _go_signature_type(ctx, a_type)
        if vararg_name != "" and a_str == vararg_name:
            vararg_gt = go_type(vararg_elem_type if vararg_elem_type != "" else a_type)
            params.append(ga + " ..." + vararg_gt)
            # Mark as a Go variadic ([]T) so _wrapper_container_storage_expr
            # does NOT add .items when this variable is used in a range loop.
            ctx.go_vararg_params.add(ga)
            if vararg_list_type != "":
                ctx.var_types[ga] = vararg_list_type
            else:
                ctx.var_types[ga] = a_type
            continue
        params.append(ga + " " + gt)
        ctx.var_types[ga] = a_type

    # If vararg param is NOT in arg_order (EAST3 desugars it separately), add it now.
    if vararg_name != "" and not any(
        (a if isinstance(a, str) else "") == vararg_name for a in arg_order
    ):
        ga_v = _safe_go_ident(vararg_name)
        vararg_gt = _go_signature_type(ctx, vararg_elem_type) if vararg_elem_type != "" else "any"
        params.append(ga_v + " ..." + vararg_gt)
        ctx.go_vararg_params.add(ga_v)
        ctx.var_types[ga_v] = (
            "list[" + vararg_elem_type + "]" if vararg_elem_type != "" else "list"
        )

    if mutated_return:
        mutated_arg_type = arg_types.get(mutated_arg_name, "")
        mutated_arg_type_str = mutated_arg_type if isinstance(mutated_arg_type, str) else ""
        go_ret = go_type(mutated_arg_type_str)

    # Nested function (inside another function) → Go closure variable
    is_nested = ctx.indent_level > 0 and ctx.current_class == ""
    ret_clause = " " + go_ret if go_ret != "" and (return_type != "None" or mutated_return) else ""

    # Method vs function
    if ctx.current_class != "" and not is_staticmethod:
        receiver = ctx.current_receiver + " *" + _go_symbol_name(ctx, ctx.current_class)
        _emit(ctx, "func (" + receiver + ") " + fn_name + "(" + ", ".join(params) + ")" + ret_clause + " {")
    elif is_nested:
        # Emit as: var fn_name func(params) ret; fn_name = func(params) ret { ... }
        # Two-step pattern supports recursion.
        param_types = [p.split(" ", 1)[1] if " " in p else "any" for p in params]
        func_type = "func(" + ", ".join(param_types) + ")" + ret_clause
        _emit(ctx, "var " + fn_name + " " + func_type)
        _emit(ctx, fn_name + " = func(" + ", ".join(params) + ")" + ret_clause + " {")
    else:
        emit_name = fn_name
        if ctx.current_class != "" and is_staticmethod:
            emit_name = _go_symbol_name(ctx, ctx.current_class + "_" + name)
        _emit(ctx, "func " + emit_name + "(" + ", ".join(params) + ")" + ret_clause + " {")

    saved_ret = ctx.current_return_type
    ctx.current_return_type = return_type
    owner_name = ctx.current_class if ctx.current_class != "" and not is_staticmethod else ""
    ctx.current_function_scope = _scope_key(ctx, name, owner_name)
    ctx.current_value_container_locals = _container_value_locals_for_scope(ctx, name, owner_name)
    ctx.ref_container_locals = set()
    ctx.indent_level += 1
    _emit_body(ctx, body)
    if not mutated_return and return_type != "None" and len(body) > 0:
        last_stmt = body[-1]
        if isinstance(last_stmt, dict) and _str(last_stmt, "kind") == "While":
            _emit(ctx, "panic(\"unreachable\")")
            _emit(ctx, "return " + go_zero_value(return_type))
    if _is_exception_type_name(ctx, return_type):
        _emit(ctx, "return nil")
    if mutated_return:
        _emit(ctx, "return " + _safe_go_ident(mutated_arg_name))
    ctx.indent_level -= 1
    _emit(ctx, "}")
    if not is_nested:
        _emit_blank(ctx)

    ctx.var_types = saved_vars
    ctx.var_decl_depth = saved_decl_depth
    ctx.current_return_type = saved_ret
    ctx.current_function_scope = saved_scope
    ctx.current_value_container_locals = saved_scope_locals
    ctx.ref_container_locals = saved_ref_locals
    ctx.go_vararg_params = saved_vararg_params


def _closure_signature_parts(
    ctx: EmitContext,
    node: dict[str, JsonVal],
) -> tuple[list[str], str, dict[str, str]]:
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    return_type = _str(node, "return_type")
    params: list[str] = []
    param_types: dict[str, str] = {}
    saved_vars = dict(ctx.var_types)
    for arg in arg_order:
        arg_name = arg if isinstance(arg, str) else ""
        if arg_name == "" or arg_name == "self":
            continue
        arg_type_val = arg_types.get(arg_name, "")
        arg_type = arg_type_val if isinstance(arg_type_val, str) else ""
        safe_name = _safe_go_ident(arg_name)
        params.append(safe_name + " " + _go_signature_type(ctx, arg_type))
        ctx.var_types[safe_name] = arg_type
        param_types[safe_name] = arg_type
    ret_clause = ""
    go_ret = _go_signature_type(ctx, return_type)
    if go_ret != "" and return_type != "None":
        ret_clause = " " + go_ret
    return params, ret_clause, saved_vars


def _closure_callable_resolved_type(node: dict[str, JsonVal]) -> str:
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    params: list[str] = []
    for arg in arg_order:
        arg_name = arg if isinstance(arg, str) else ""
        if arg_name == "" or arg_name == "self":
            continue
        arg_type = arg_types.get(arg_name, "")
        params.append(arg_type if isinstance(arg_type, str) and arg_type != "" else "unknown")
    ret = _str(node, "return_type")
    if ret == "":
        ret = "unknown"
    return "callable[[" + ",".join(params) + "]," + ret + "]"


def _emit_closure_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    if name == "":
        return
    body = _list(node, "body")
    return_type = _str(node, "return_type")
    safe_name = _go_symbol_name(ctx, name)
    params, ret_clause, saved_vars = _closure_signature_parts(ctx, node)
    saved_scope = ctx.current_function_scope
    saved_scope_locals = set(ctx.current_value_container_locals)
    saved_ref_locals = set(ctx.ref_container_locals)
    closure_type = "func(" + ", ".join(params) + ")" + ret_clause
    is_recursive = _bool(node, "is_recursive")
    if is_recursive:
        _emit(ctx, "var " + safe_name + " " + closure_type)
        _emit(ctx, safe_name + " = func(" + ", ".join(params) + ")" + ret_clause + " {")
    else:
        _emit(ctx, safe_name + " := func(" + ", ".join(params) + ")" + ret_clause + " {")
    saved_ret = ctx.current_return_type
    ctx.current_return_type = return_type
    owner_name = ctx.current_class if ctx.current_class != "" else ""
    ctx.current_function_scope = _scope_key(ctx, name, owner_name)
    ctx.current_value_container_locals = _container_value_locals_for_scope(ctx, name, owner_name)
    ctx.ref_container_locals = set()
    ctx.indent_level += 1
    _emit_body(ctx, body)
    if return_type != "None" and len(body) > 0:
        last_stmt = body[-1]
        if isinstance(last_stmt, dict) and _str(last_stmt, "kind") == "While":
            _emit(ctx, "panic(\"unreachable\")")
            _emit(ctx, "return " + go_zero_value(return_type))
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.var_types = saved_vars
    ctx.var_types[safe_name] = _closure_callable_resolved_type(node)
    ctx.current_return_type = saved_ret
    ctx.current_function_scope = saved_scope
    ctx.current_value_container_locals = saved_scope_locals
    ctx.ref_container_locals = saved_ref_locals


def _emit_class_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    base = _str(node, "base")
    body = _list(node, "body")
    gn = _go_symbol_name(ctx, name)
    is_dataclass = _bool(node, "dataclass")
    is_trait = _is_trait_class(node)

    ctx.class_names.add(name)
    if is_trait:
        ctx.trait_names.add(name)
    if base != "":
        ctx.class_bases[name] = base
    property_methods: set[str] = ctx.class_property_methods.setdefault(name, set())
    static_methods: set[str] = ctx.class_static_methods.setdefault(name, set())
    instance_methods = ctx.class_instance_methods.setdefault(name, {})
    class_vars = ctx.class_vars.get(name, {})
    enum_base = ctx.enum_bases.get(name, "")
    enum_members = ctx.enum_members.get(name, {})
    field_defaults: dict[str, JsonVal] = {}

    if is_trait:
        _emit(ctx, "type " + gn + " interface {")
        ctx.indent_level += 1
        trait_meta = _dict(_dict(node, "meta"), "trait_v1")
        for parent_trait in _list(trait_meta, "extends_traits"):
            if isinstance(parent_trait, str) and parent_trait != "":
                _emit(ctx, _go_symbol_name(ctx, parent_trait.rsplit(".", 1)[-1]))
        for stmt in body:
            if not isinstance(stmt, dict) or _str(stmt, "kind") not in ("FunctionDef", "ClosureDef"):
                continue
            sig = _interface_method_signature(ctx, stmt)
            if sig != "":
                _emit(ctx, sig)
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit_blank(ctx)
        return

    if enum_base != "":
        _emit(ctx, "type " + gn + " int64")
        _emit_blank(ctx)
        if len(enum_members) > 0:
            _emit(ctx, "const (")
            ctx.indent_level += 1
            for member_name, spec in enum_members.items():
                value_node = spec.get("value")
                value_code = "0"
                if isinstance(value_node, dict):
                    if _str(value_node, "kind") == "Constant":
                        raw_value = value_node.get("value")
                        if isinstance(raw_value, bool):
                            value_code = "true" if raw_value else "false"
                        elif isinstance(raw_value, int):
                            value_code = str(raw_value)
                        else:
                            value_code = _emit_expr(ctx, value_node)
                    else:
                        value_code = _emit_expr(ctx, value_node)
                _emit(ctx, _go_enum_const_name(ctx, name, member_name) + " = " + value_code)
            ctx.indent_level -= 1
            _emit(ctx, ")")
            _emit_blank(ctx)
        return

    # Collect fields: prefer field_types (dataclass), else scan __init__
    fields: list[tuple[str, str]] = []
    field_types = _dict(node, "field_types")
    if len(field_types) > 0:
        for fname_key, ftype_val in field_types.items():
            if fname_key in class_vars:
                continue
            ft = ftype_val if isinstance(ftype_val, str) else ""
            fields.append((fname_key, ft))
        if is_dataclass:
            for stmt in body:
                if not isinstance(stmt, dict) or _str(stmt, "kind") != "AnnAssign":
                    continue
                target_val = stmt.get("target")
                ft_name = ""
                if isinstance(target_val, dict):
                    ft_name = _str(target_val, "id")
                elif isinstance(target_val, str):
                    ft_name = target_val
                default_val = stmt.get("value")
                if ft_name != "" and isinstance(default_val, dict):
                    field_defaults[ft_name] = default_val
    else:
        # Scan body AnnAssign (dataclass fields) or __init__
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            sk = _str(stmt, "kind")
            if sk == "AnnAssign" and is_dataclass:
                target_val = stmt.get("target")
                ft_name = ""
                if isinstance(target_val, dict):
                    ft_name = _str(target_val, "id")
                elif isinstance(target_val, str):
                    ft_name = target_val
                frt = _str(stmt, "decl_type")
                if frt == "":
                    frt = _str(stmt, "resolved_type")
                if ft_name != "":
                    fields.append((ft_name, frt))
                    default_val = stmt.get("value")
                    if isinstance(default_val, dict):
                        field_defaults[ft_name] = default_val
            elif sk in ("FunctionDef", "ClosureDef") and _str(stmt, "name") == "__init__":
                for init_stmt in _list(stmt, "body"):
                    if not isinstance(init_stmt, dict):
                        continue
                    init_kind = _str(init_stmt, "kind")
                    if init_kind not in ("AnnAssign", "Assign"):
                        continue
                    t_val = init_stmt.get("target")
                    ft = ""
                    if isinstance(t_val, dict):
                        t_kind = _str(t_val, "kind")
                        if t_kind == "Name":
                            ft = _str(t_val, "id")
                        elif t_kind == "Attribute":
                            owner = t_val.get("value")
                            if isinstance(owner, dict) and _str(owner, "kind") == "Name" and _str(owner, "id") == "self":
                                ft = _str(t_val, "attr")
                    elif isinstance(t_val, str):
                        ft = t_val
                    frt = _str(init_stmt, "decl_type")
                    if frt == "":
                        frt = _str(init_stmt, "resolved_type")
                    if frt == "":
                        value_node = init_stmt.get("value")
                        if isinstance(value_node, dict):
                            frt = _str(value_node, "resolved_type")
                    if ft.startswith("self."):
                        ft = ft[5:]
                    if ft != "" and frt != "":
                        fields.append((ft, frt))

    # Save class context early (before constructor and methods modify it)
    saved_class = ctx.current_class
    saved_receiver = ctx.current_receiver

    is_exception_class = _is_exception_type_name(ctx, name)

    if _is_polymorphic_class(ctx, name):
        _emit(ctx, "type " + _go_polymorphic_iface_name(ctx, name) + " interface {")
        ctx.indent_level += 1
        _emit(ctx, _go_class_marker_method_name(ctx, name) + "()")
        for method_node in _effective_instance_methods(ctx, name).values():
            sig = _interface_method_signature(ctx, method_node)
            if sig != "":
                _emit(ctx, sig)
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit_blank(ctx)

    # Struct definition
    _emit(ctx, "type " + gn + " struct {")
    ctx.indent_level += 1
    if is_exception_class:
        _emit(ctx, _exception_embed_field(ctx, name, base))
    elif base != "" and base != "object" and base != "ABC" and base not in ctx.builtin_exc_bounds:
        _emit(ctx, _go_symbol_name(ctx, base))  # embed base
    for fname, ftype in fields:
        _emit(ctx, _safe_go_ident(fname) + " " + _go_signature_type(ctx, ftype))
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)
    _emit(ctx, "func (_ " + gn + ") " + _go_class_marker_method_name(ctx, name) + "() {}")
    for ancestor_name in _ancestor_class_chain(ctx, name):
        _emit(ctx, "func (_ " + gn + ") " + _go_class_marker_method_name(ctx, ancestor_name) + "() {}")
    if is_exception_class:
        _emit(ctx, "func (e *" + gn + ") pytraErrorBase() *PytraErrorCarrier { return &e.PytraErrorCarrier }")
    else:
        linked_tid = _linked_type_id(ctx, name)
        if linked_tid is not None:
            _emit(ctx, "func (_ *" + gn + ") __pytra_type_id() int64 { return int64(" + str(linked_tid) + ") }")
    _emit_blank(ctx)
    for var_name, spec in class_vars.items():
        var_type = _str(spec, "type")
        default_node = spec.get("value")
        default_code = go_zero_value(var_type)
        if isinstance(default_node, dict):
            default_code = _emit_expr(ctx, default_node)
        _emit(ctx, "var " + _safe_go_ident(name + "_" + var_name) + " " + _go_signature_type(ctx, var_type) + " = " + default_code)
    if len(class_vars) > 0:
        _emit_blank(ctx)

    # Constructor: for dataclass use all fields, for __init__ use its arg_order
    ctor_params: list[tuple[str, str]] = list(fields) if is_dataclass else []
    has_init = False
    init_body_stmts: list[JsonVal] = []
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef") and _str(stmt, "name") == "__init__":
            has_init = True
            init_args = _dict(stmt, "arg_types")
            init_order = _list(stmt, "arg_order")
            init_body_stmts = _list(stmt, "body")
            # Only use __init__ params (excluding self) as ctor params
            ctor_params = []
            for a in init_order:
                a_name = a if isinstance(a, str) else ""
                if a_name == "self":
                    continue
                a_type = init_args.get(a_name, "")
                a_type_str = a_type if isinstance(a_type, str) else ""
                ctor_params.append((a_name, a_type_str))
            break

    first_default_index = len(ctor_params)
    if is_dataclass:
        for i, (fname, _) in enumerate(ctor_params):
            if fname in field_defaults:
                first_default_index = i
                break

    ctor_sig_parts: list[str] = []
    for i, (fname, ftype) in enumerate(ctor_params):
        if i >= first_default_index:
            break
        ctor_sig_parts.append(_safe_go_ident(fname) + " " + _go_signature_type(ctx, ftype))
    if first_default_index < len(ctor_params):
        ctor_sig_parts.append("__opt_args ...any")

    if is_exception_class and len(ctor_params) == 0 and not has_init:
        ctor_sig_parts = ["__opt_args ...any"]
    _emit(ctx, "func New" + gn + "(" + ", ".join(ctor_sig_parts) + ") *" + gn + " {")
    ctx.indent_level += 1

    if is_exception_class and len(ctor_params) == 0 and not has_init:
        _emit(ctx, "msg := " + _go_string_literal(name))
        _emit(ctx, "if len(__opt_args) > 0 {")
        ctx.indent_level += 1
        _emit(ctx, "msg = py_str(__opt_args[0])")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        embed_field = _exception_embed_field(ctx, name, base)
        _emit(ctx, "obj := &" + gn + "{" + embed_field + ": " + _exception_embed_init_expr(ctx, name, base, "msg") + "}")
        _emit(ctx, "obj." + embed_field + ".Value = obj")
        _emit(ctx, "return obj")
    elif has_init and not is_dataclass:
        # Emit __init__ body translated to Go (self.x = ... → obj.x = ...)
        _emit(ctx, "obj := &" + gn + "{}")
        if is_exception_class:
            msg_expr = _go_string_literal(name)
            if len(ctor_params) > 0:
                first_param_name, _ = ctor_params[0]
                msg_expr = "py_str(" + _safe_go_ident(first_param_name) + ")"
            msg_expr = _exception_super_init_message_expr(ctx, init_body_stmts, msg_expr)
            embed_field = _exception_embed_field(ctx, name, base)
            _emit(ctx, "obj." + embed_field + " = " + _exception_embed_init_expr(ctx, name, base, msg_expr))
        saved_receiver = ctx.current_receiver
        saved_ctor_target = ctx.constructor_return_target
        saved_vars = dict(ctx.var_types)
        ctx.current_receiver = "obj"
        ctx.current_class = name
        ctx.constructor_return_target = "obj"
        for param_name, param_type in ctor_params:
            ctx.var_types[_safe_go_ident(param_name)] = param_type
        for init_s in init_body_stmts:
            if is_exception_class and _is_exception_super_init_stmt(init_s):
                continue
            _emit_stmt(ctx, init_s)
        if is_exception_class:
            embed_field = _exception_embed_field(ctx, name, base)
            _emit(ctx, "obj." + embed_field + ".Value = obj")
        ctx.current_receiver = saved_receiver
        ctx.constructor_return_target = saved_ctor_target
        ctx.var_types = saved_vars
        _emit(ctx, "return obj")
    else:
        if first_default_index < len(ctor_params):
            for i in range(first_default_index, len(ctor_params)):
                fname, ftype = ctor_params[i]
                default_node = field_defaults.get(fname)
                default_code = go_zero_value(ftype)
                if isinstance(default_node, dict):
                    default_code = _dataclass_default_code(ctx, default_node, ftype)
                local_name = _safe_go_ident(fname)
                _emit(ctx, "var " + local_name + " " + _go_signature_type(ctx, ftype) + " = " + default_code)
                opt_index = i - first_default_index
                _emit(ctx, "if len(__opt_args) > " + str(opt_index) + " {")
                ctx.indent_level += 1
                _emit(ctx, local_name + " = " + _coerce_from_any("__opt_args[" + str(opt_index) + "]", ftype))
                ctx.indent_level -= 1
                _emit(ctx, "}")
        field_init_parts: list[str] = []
        if is_exception_class:
            msg_expr = _go_string_literal(name)
            if len(ctor_params) > 0:
                first_param_name, _ = ctor_params[0]
                msg_expr = "py_str(" + _safe_go_ident(first_param_name) + ")"
            msg_expr = _exception_super_init_message_expr(ctx, init_body_stmts, msg_expr)
            embed_field = _exception_embed_field(ctx, name, base)
            field_init_parts.append(embed_field + ": " + _exception_embed_init_expr(ctx, name, base, msg_expr))
        for f, _ in ctor_params:
            field_init_parts.append(_safe_go_ident(f) + ": " + _safe_go_ident(f))
        field_inits = ", ".join(field_init_parts)
        _emit(ctx, "obj := &" + gn + "{" + field_inits + "}")
        if is_exception_class:
            embed_field = _exception_embed_field(ctx, name, base)
            _emit(ctx, "obj." + embed_field + ".Value = obj")
        _emit(ctx, "return obj")

    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)

    # Methods
    ctx.current_class = name
    ctx.current_receiver = "self"
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            decorators = _list(stmt, "decorators")
            is_staticmethod = False
            for d in decorators:
                if isinstance(d, str) and d == "property":
                    property_methods.add(fn_name)
                if isinstance(d, str) and d == "staticmethod":
                    static_methods.add(fn_name)
                    is_staticmethod = True
            if fn_name == "__init__":
                continue  # Already handled by constructor
            if not is_staticmethod:
                instance_methods[fn_name] = stmt
            _emit_function_def(ctx, stmt)
    ctx.current_class = saved_class
    ctx.current_receiver = saved_receiver


def _emit_var_decl(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    # VarDecl uses "type" field, not "resolved_type"
    rt = _str(node, "type")
    if rt == "":
        rt = _str(node, "resolved_type")
    gn = _go_symbol_name(ctx, name)
    # VarDecl with unknown type: emit as any but track for later upgrade
    if rt == "" or rt == "unknown" or rt == "None" or rt == "none":
        ctx.var_types[gn] = "unknown"
        _emit(ctx, "var " + gn + " any")
        _emit(ctx, "_ = " + gn)
        return
    gt = _decl_go_type(ctx, rt, name)
    ctx.var_types[gn] = rt
    if _is_container_resolved_type(rt) and not _prefer_value_container_local(ctx, gn, rt):
        ctx.ref_container_locals.add(gn)
    else:
        ctx.ref_container_locals.discard(gn)
    _emit(ctx, "var " + gn + " " + gt + " = " + _decl_go_zero_value(ctx, rt, name))
    _emit(ctx, "_ = " + gn)


def _dataclass_default_code(ctx: EmitContext, default_node: JsonVal, field_type: str) -> str:
    if not isinstance(default_node, dict):
        return go_zero_value(field_type)
    if _str(default_node, "kind") == "Unbox":
        inner = default_node.get("value")
        if isinstance(inner, dict):
            return _dataclass_default_code(ctx, inner, field_type)
    if _str(default_node, "kind") != "Call":
        return _emit_expr(ctx, default_node)
    func = default_node.get("func")
    if not isinstance(func, dict) or _str(func, "kind") != "Name" or _str(func, "id") != "field":
        return _emit_expr(ctx, default_node)
    for kw in _list(default_node, "keywords"):
        if not isinstance(kw, dict) or _str(kw, "arg") != "default_factory":
            continue
        value = kw.get("value")
        if not isinstance(value, dict):
            break
        # Lambda default factory: field(default_factory=lambda: expr) → emit expr directly
        if _str(value, "kind") == "Lambda":
            lambda_body = value.get("body")
            if isinstance(lambda_body, dict):
                return _emit_expr(ctx, lambda_body)
            break
        if _str(value, "kind") != "Name":
            break
        factory_name = _str(value, "id")
        if factory_name in ("dict", "list", "set", "tuple"):
            return go_zero_value(field_type)
        if factory_name != "" and (factory_name in ctx.class_names or field_type == factory_name or field_type == "*" + factory_name):
            return "New" + _safe_go_ident(factory_name) + "()"
        return go_zero_value(field_type)
    return _emit_expr(ctx, default_node)


def _emit_swap(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    _emit(ctx, left + ", " + right + " = " + right + ", " + left)


def _emit_with(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    context_expr = node.get("context_expr")
    if not isinstance(context_expr, dict):
        return
    var_name = _go_symbol_name(ctx, _str(node, "var_name"))
    body = _list(node, "body")
    ctx_expr = _emit_expr(ctx, context_expr)
    ctx_tmp = _next_temp(ctx, "__with_ctx")

    hoisted: list[tuple[str, str]] = []
    seen: set[str] = set()

    def _add_hoisted(name: str, resolved_type: str) -> None:
        if name == "" or name in seen:
            return
        seen.add(name)
        hoisted.append((name, resolved_type))

    def _walk_hoisted(stmts: list[JsonVal]) -> None:
        for raw_stmt in stmts:
            if not isinstance(raw_stmt, dict):
                continue
            kind = _str(raw_stmt, "kind")
            if kind == "AnnAssign":
                target = raw_stmt.get("target")
                if isinstance(target, dict) and _str(target, "kind") in ("Name", "NameTarget"):
                    _add_hoisted(_go_symbol_name(ctx, _str(target, "id")), _str(raw_stmt, "decl_type") or _str(raw_stmt, "resolved_type"))
            elif kind == "Assign":
                target = raw_stmt.get("target")
                if not isinstance(target, dict):
                    targets = _list(raw_stmt, "targets")
                    if len(targets) > 0 and isinstance(targets[0], dict):
                        target = targets[0]
                if isinstance(target, dict) and _str(target, "kind") in ("Name", "NameTarget"):
                    _add_hoisted(_go_symbol_name(ctx, _str(target, "id")), _str(raw_stmt, "decl_type") or _str(raw_stmt, "resolved_type"))
            elif kind in ("If", "While", "With", "Try", "ForCore"):
                _walk_hoisted(_list(raw_stmt, "body"))
                _walk_hoisted(_list(raw_stmt, "orelse"))
                _walk_hoisted(_list(raw_stmt, "finalbody"))
                for handler in _list(raw_stmt, "handlers"):
                    if isinstance(handler, dict):
                        _walk_hoisted(_list(handler, "body"))

    _walk_hoisted(body)
    for name, resolved_type in hoisted:
        if name in ctx.var_types:
            continue
        ctx.var_types[name] = resolved_type
        ctx.var_decl_depth[name] = ctx.indent_level
        decl_type = _decl_go_type(ctx, resolved_type, name)
        if decl_type != "":
            _emit(ctx, "var " + name + " " + decl_type + " = " + _decl_go_zero_value(ctx, resolved_type, name))
        else:
            _emit(ctx, "var " + name + " = " + _decl_go_zero_value(ctx, resolved_type, name))

    _emit(ctx, ctx_tmp + " := " + ctx_expr)
    if var_name != "":
        if var_name in ctx.var_types:
            _emit(ctx, var_name + " = " + ctx_tmp + ".__enter__()")
        else:
            _emit(ctx, var_name + " := " + ctx_tmp + ".__enter__()")
            ctx.var_types[var_name] = _str(node, "with_enter_type") or _effective_resolved_type(ctx, context_expr)
            ctx.var_decl_depth[var_name] = ctx.indent_level
    else:
        _emit(ctx, ctx_tmp + ".__enter__()")

    _emit(ctx, "func() {")
    ctx.indent_level += 1
    _emit(ctx, "defer " + ctx_tmp + ".__exit__(nil, nil, nil)")
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}()")


def _emit_try(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    try_body = _list(node, "body")
    try_ret_expr = _extract_single_return_expr(try_body)
    handlers = _list(node, "handlers")
    handler_ret_expr = ""
    if len(handlers) > 0 and isinstance(handlers[0], dict):
        handler_ret_expr = _extract_single_return_expr(_list(handlers[0], "body"))
    finalbody = _list(node, "finalbody")

    if ctx.current_return_type != "" and try_ret_expr != "" and handler_ret_expr != "" and len(finalbody) == 0:
        ret_type = go_type(ctx.current_return_type)
        zero_value = go_zero_value(ctx.current_return_type)
        _emit(ctx, "return func() " + ret_type + " {")
        ctx.indent_level += 1
        _emit(ctx, "__try_result := " + zero_value)
        _emit(ctx, "defer func() {")
        ctx.indent_level += 1
        _emit(ctx, "__rethrow := any(nil)")
        _emit(ctx, "if r := recover(); r != nil {")
        ctx.indent_level += 1
        _emit(ctx, "__pytra_err := pytraEnsureRecoveredError(r)")
        _emit(ctx, "__handled := false")
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            handler_type = _handler_type_name(handler)
            cond = _exception_match_condition(ctx, "__pytra_err", handler_type)
            _emit(ctx, "if !__handled && " + cond + " {")
            ctx.indent_level += 1
            _emit(ctx, "__handled = true")
            saved_exc_var = ctx.current_exception_var
            ctx.current_exception_var = "__pytra_err"
            _emit(ctx, "__try_result = " + handler_ret_expr)
            ctx.current_exception_var = saved_exc_var
            ctx.indent_level -= 1
            _emit(ctx, "}")
        _emit(ctx, "if !__handled {")
        ctx.indent_level += 1
        _emit(ctx, "__rethrow = __pytra_err")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        for stmt in finalbody:
            _emit_stmt(ctx, stmt)
        _emit(ctx, "if __rethrow != nil {")
        ctx.indent_level += 1
        _emit(ctx, "panic(__rethrow)")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        ctx.indent_level -= 1
        _emit(ctx, "}()")
        _emit(ctx, "__try_result = " + try_ret_expr)
        _emit(ctx, "return __try_result")
        ctx.indent_level -= 1
        _emit(ctx, "}()")
        return

    try_has_return = _function_has_return(try_body)
    handler_has_return = False
    for handler in handlers:
        if isinstance(handler, dict) and _function_has_return(_list(handler, "body")):
            handler_has_return = True
            break
    if ctx.current_return_type != "" and ctx.current_return_type != "None":
        ret_type = go_type(ctx.current_return_type)
        emit_prefix = "return " if try_has_return or handler_has_return else ""
        _emit(ctx, emit_prefix + "func() (__try_result " + ret_type + ") {")
        ctx.indent_level += 1
        _emit(ctx, "defer func() {")
        ctx.indent_level += 1
        _emit(ctx, "__rethrow := any(nil)")
        _emit(ctx, "if r := recover(); r != nil {")
        ctx.indent_level += 1
        _emit(ctx, "__pytra_err := pytraEnsureRecoveredError(r)")
        _emit(ctx, "__handled := false")
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            handler_type = _handler_type_name(handler)
            cond = _exception_match_condition(ctx, "__pytra_err", handler_type)
            _emit(ctx, "if !__handled && " + cond + " {")
            ctx.indent_level += 1
            handler_name = _str(handler, "name")
            saved_handler_type = ""
            if handler_name != "":
                safe_name = _safe_go_ident(handler_name)
                saved_handler_type = ctx.var_types.get(safe_name, "")
                _emit(ctx, safe_name + " := __pytra_err")
                ctx.var_types[safe_name] = "*PytraErrorCarrier"
            _emit(ctx, "__handled = true")
            _emit(ctx, "__try_result = func() " + ret_type + " {")
            ctx.indent_level += 1
            saved_exc_var = ctx.current_exception_var
            ctx.current_exception_var = "__pytra_err"
            _emit_body(ctx, _list(handler, "body"))
            ctx.current_exception_var = saved_exc_var
            _emit(ctx, "return __try_result")
            ctx.indent_level -= 1
            _emit(ctx, "}()")
            if handler_name != "":
                safe_name2 = _safe_go_ident(handler_name)
                if saved_handler_type != "":
                    ctx.var_types[safe_name2] = saved_handler_type
                elif safe_name2 in ctx.var_types:
                    ctx.var_types.pop(safe_name2, None)
            ctx.indent_level -= 1
            _emit(ctx, "}")
        _emit(ctx, "if !__handled {")
        ctx.indent_level += 1
        _emit(ctx, "__rethrow = __pytra_err")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        if len(finalbody) > 0:
            _emit_body(ctx, finalbody)
        _emit(ctx, "if __rethrow != nil {")
        ctx.indent_level += 1
        _emit(ctx, "panic(__rethrow)")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        ctx.indent_level -= 1
        _emit(ctx, "}()")
        _emit_body(ctx, try_body)
        _emit(ctx, "return __try_result")
        ctx.indent_level -= 1
        _emit(ctx, "}()")
        return

    _emit(ctx, "func() {")
    ctx.indent_level += 1
    _emit(ctx, "defer func() {")
    ctx.indent_level += 1
    _emit(ctx, "__rethrow := any(nil)")
    _emit(ctx, "if r := recover(); r != nil {")
    ctx.indent_level += 1
    _emit(ctx, "__pytra_err := pytraEnsureRecoveredError(r)")
    _emit(ctx, "__handled := false")
    for handler in handlers:
        if not isinstance(handler, dict):
            continue
        handler_type = _handler_type_name(handler)
        cond = _exception_match_condition(ctx, "__pytra_err", handler_type)
        _emit(ctx, "if !__handled && " + cond + " {")
        ctx.indent_level += 1
        handler_name = _str(handler, "name")
        saved_handler_type = ""
        if handler_name != "":
            safe_name = _safe_go_ident(handler_name)
            saved_handler_type = ctx.var_types.get(safe_name, "")
            _emit(ctx, safe_name + " := __pytra_err")
            ctx.var_types[safe_name] = "*PytraErrorCarrier"
        _emit(ctx, "__handled = true")
        saved_exc_var = ctx.current_exception_var
        ctx.current_exception_var = "__pytra_err"
        _emit_body(ctx, _list(handler, "body"))
        ctx.current_exception_var = saved_exc_var
        if handler_name != "":
            safe_name2 = _safe_go_ident(handler_name)
            if saved_handler_type != "":
                ctx.var_types[safe_name2] = saved_handler_type
            elif safe_name2 in ctx.var_types:
                ctx.var_types.pop(safe_name2, None)
        ctx.indent_level -= 1
        _emit(ctx, "}")
    _emit(ctx, "if !__handled {")
    ctx.indent_level += 1
    _emit(ctx, "__rethrow = __pytra_err")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    if len(finalbody) > 0:
        _emit_body(ctx, finalbody)
    _emit(ctx, "if __rethrow != nil {")
    ctx.indent_level += 1
    _emit(ctx, "panic(__rethrow)")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.indent_level -= 1
    _emit(ctx, "}()")
    _emit_body(ctx, try_body)
    ctx.indent_level -= 1
    _emit(ctx, "}()")


def _extract_single_return_expr(body: list[JsonVal]) -> str:
    if len(body) != 1:
        return ""
    stmt = body[0]
    if not isinstance(stmt, dict) or _str(stmt, "kind") != "Return":
        return ""
    value = stmt.get("value")
    if not isinstance(value, dict):
        return ""
    return _emit_expr(EmitContext(), value)


def _error_return_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if isinstance(value, dict):
        return "pytraEnsureRecoveredError(" + _emit_expr(ctx, value) + ")"
    if ctx.current_exception_var != "":
        return ctx.current_exception_var
    return "pytraNewRuntimeError(\"raise\")"


def _emit_error_return(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    err_expr = _error_return_expr(ctx, node)
    if _is_exception_type_name(ctx, ctx.current_return_type):
        _emit(ctx, "return " + err_expr)
        return
    if ctx.current_return_type.startswith("multi_return["):
        zeros = _zero_return_values(ctx.current_return_type).split(", ")
        if len(zeros) >= 2:
            zeros[-1] = err_expr
            _emit(ctx, "return " + ", ".join(zeros))
            return
    _emit(ctx, "panic(" + err_expr + ")")


def _emit_error_check(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    call_node = node.get("call")
    if not isinstance(call_node, dict):
        return
    ok_target = node.get("ok_target")
    ok_type = _str(node, "ok_type")
    on_error = _str(node, "on_error")
    ok_tmp = _next_temp(ctx, "ok")
    err_tmp = _next_temp(ctx, "err")
    call_code = _emit_expr(ctx, call_node)
    if ok_target is None or ok_type in ("", "None"):
        _emit(ctx, err_tmp + " := " + call_code)
    else:
        _emit(ctx, ok_tmp + ", " + err_tmp + " := " + call_code)
    _emit(ctx, "if " + err_tmp + " != nil {")
    ctx.indent_level += 1
    if on_error == "propagate":
        if _is_exception_type_name(ctx, ctx.current_return_type):
            _emit(ctx, "return " + err_tmp)
        elif ctx.current_return_type.startswith("multi_return["):
            zeros = _zero_return_values(ctx.current_return_type).split(", ")
            if len(zeros) >= 2:
                zeros[-1] = err_tmp
                _emit(ctx, "return " + ", ".join(zeros))
            else:
                _emit(ctx, "return " + err_tmp)
        else:
            _emit(ctx, "panic(" + err_tmp + ")")
    else:
        _emit(ctx, "panic(" + err_tmp + ")")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    if ok_target is not None and ok_type not in ("", "None"):
        ctx.var_types[ok_tmp] = ok_type
        assign_node: dict[str, JsonVal] = {
            "kind": "Assign",
            "target": ok_target,
            "value": {"kind": "Name", "id": ok_tmp, "resolved_type": ok_type},
            "declare": True,
        }
        _emit_assign(ctx, assign_node)


def _emit_error_handlers(
    ctx: EmitContext,
    err_name: str,
    handlers: list[JsonVal],
    result_sink: str = "",
    *,
    defer_context: bool = False,
) -> None:
    first = True
    emitted_any = False
    for handler in handlers:
        if not isinstance(handler, dict):
            continue
        cond = _exception_match_condition(ctx, err_name, _handler_type_name(handler))
        if first:
            _emit(ctx, "if " + cond + " {")
        else:
            _emit(ctx, "} else if " + cond + " {")
        first = False
        emitted_any = True
        ctx.indent_level += 1
        handler_name = _str(handler, "name")
        saved_type = ""
        if handler_name != "":
            safe_name = _safe_go_ident(handler_name)
            saved_type = ctx.var_types.get(safe_name, "")
            handler_type_name = _handler_type_name(handler)
            bound_type = "*PytraErrorCarrier"
            if (
                handler_type_name != ""
                and _is_nominal_type_name(ctx, handler_type_name)
                and not _is_builtin_exception_type_name(ctx, handler_type_name)
            ):
                bound_type = _go_signature_type(ctx, handler_type_name)
                _emit(ctx, safe_name + " := " + err_name + ".Value.(" + bound_type + ")")
            else:
                _emit(ctx, safe_name + " := " + err_name)
            ctx.var_types[safe_name] = bound_type
            _emit(ctx, "_ = " + safe_name)
        handler_body = _list(handler, "body")
        saved_exc_var = ctx.current_exception_var
        ctx.current_exception_var = err_name
        if (
            len(handler_body) == 1
            and isinstance(handler_body[0], dict)
            and _str(handler_body[0], "kind") == "ErrorReturn"
        ):
            err_expr = _error_return_expr(ctx, cast(dict[str, JsonVal], handler_body[0]))
            if result_sink != "":
                _emit(ctx, result_sink + " = " + err_expr)
                if defer_context:
                    _emit(ctx, "return")
                else:
                    _emit(ctx, "return " + result_sink)
            else:
                _emit(ctx, "panic(" + err_expr + ")")
            ctx.current_exception_var = saved_exc_var
        else:
            _emit_body(ctx, handler_body)
            ctx.current_exception_var = saved_exc_var
            if result_sink != "":
                if defer_context:
                    _emit(ctx, "return")
                else:
                    _emit(ctx, "return " + result_sink)
            elif _is_exception_type_name(ctx, ctx.current_return_type):
                _emit(ctx, "return nil")
            else:
                _emit(ctx, "return")
        if handler_name != "":
            safe_name2 = _safe_go_ident(handler_name)
            if saved_type != "":
                ctx.var_types[safe_name2] = saved_type
            elif safe_name2 in ctx.var_types:
                ctx.var_types.pop(safe_name2, None)
        ctx.indent_level -= 1
    if emitted_any:
        _emit(ctx, "}")
    _emit(ctx, "panic(" + err_name + ")")


def _emit_error_catch(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    if ctx.current_return_type.startswith("multi_return["):
        parts = _split_generic_args(ctx.current_return_type[len("multi_return["):-1])
        ok_type = parts[0] if len(parts) >= 1 else "any"
        ok_gt = _go_signature_type(ctx, ok_type)
        body_has_return = _function_has_return(_list(node, "body"))
        handler_has_return = False
        for handler in _list(node, "handlers"):
            if isinstance(handler, dict) and _function_has_return(_list(handler, "body")):
                handler_has_return = True
                break
        result_tmp = _next_temp(ctx, "try_result")
        _emit(ctx, result_tmp + " := func() (__try_result " + ok_gt + ") {")
        ctx.indent_level += 1
        finalbody = _list(node, "finalbody")
        if len(finalbody) > 0:
            _emit(ctx, "defer func() {")
            ctx.indent_level += 1
            _emit_body(ctx, finalbody)
            ctx.indent_level -= 1
            _emit(ctx, "}()")
        handlers = _list(node, "handlers")
        if len(handlers) > 0:
            recovered_name = _next_temp(ctx, "recovered")
            err_name = _next_temp(ctx, "err")
            _emit(ctx, "defer func() {")
            ctx.indent_level += 1
            _emit(ctx, recovered_name + " := recover()")
            _emit(ctx, "if " + recovered_name + " == nil {")
            ctx.indent_level += 1
            _emit(ctx, "return")
            ctx.indent_level -= 1
            _emit(ctx, "}")
            _emit(ctx, err_name + " := pytraEnsureRecoveredError(" + recovered_name + ")")
            _emit(ctx, "__handled := false")
            first = True
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                cond = _exception_match_condition(ctx, err_name, _handler_type_name(handler))
                if first:
                    _emit(ctx, "if !__handled && " + cond + " {")
                else:
                    _emit(ctx, "} else if !__handled && " + cond + " {")
                first = False
                ctx.indent_level += 1
                handler_name = _str(handler, "name")
                saved_type = ""
                if handler_name != "":
                    safe_name = _safe_go_ident(handler_name)
                    saved_type = ctx.var_types.get(safe_name, "")
                    handler_type_name = _handler_type_name(handler)
                    bound_type = "*PytraErrorCarrier"
                    if (
                        handler_type_name != ""
                        and _is_nominal_type_name(ctx, handler_type_name)
                        and not _is_builtin_exception_type_name(ctx, handler_type_name)
                    ):
                        bound_type = _go_signature_type(ctx, handler_type_name)
                        _emit(ctx, safe_name + " := " + err_name + ".Value.(" + bound_type + ")")
                    else:
                        _emit(ctx, safe_name + " := " + err_name)
                    ctx.var_types[safe_name] = bound_type
                    _emit(ctx, "_ = " + safe_name)
                _emit(ctx, "__handled = true")
                _emit(ctx, "__try_result = func() " + ok_gt + " {")
                ctx.indent_level += 1
                saved_exc_var = ctx.current_exception_var
                saved_ret = ctx.current_return_type
                ctx.current_exception_var = err_name
                ctx.current_return_type = ok_type
                _emit_body(ctx, _list(handler, "body"))
                ctx.current_exception_var = saved_exc_var
                ctx.current_return_type = saved_ret
                _emit(ctx, "return __try_result")
                ctx.indent_level -= 1
                _emit(ctx, "}()")
                if handler_name != "":
                    safe_name2 = _safe_go_ident(handler_name)
                    if saved_type != "":
                        ctx.var_types[safe_name2] = saved_type
                    elif safe_name2 in ctx.var_types:
                        ctx.var_types.pop(safe_name2, None)
                ctx.indent_level -= 1
            if not first:
                _emit(ctx, "}")
            _emit(ctx, "if !__handled {")
            ctx.indent_level += 1
            _emit(ctx, "panic(" + err_name + ")")
            ctx.indent_level -= 1
            _emit(ctx, "}")
            ctx.indent_level -= 1
            _emit(ctx, "}()")
        saved_ret = ctx.current_return_type
        ctx.current_return_type = ok_type
        _emit_body(ctx, _list(node, "body"))
        ctx.current_return_type = saved_ret
        _emit(ctx, "return __try_result")
        ctx.indent_level -= 1
        _emit(ctx, "}()")
        if body_has_return or handler_has_return:
            _emit(ctx, "return " + result_tmp + ", nil")
        else:
            _emit(ctx, "_ = " + result_tmp)
        return

    if _is_exception_type_name(ctx, ctx.current_return_type):
        _emit(ctx, "return func() *PytraErrorCarrier {")
    else:
        _emit(ctx, "func() {")
    ctx.indent_level += 1
    finalbody = _list(node, "finalbody")
    catch_result = ""
    if _is_exception_type_name(ctx, ctx.current_return_type):
        catch_result = _next_temp(ctx, "catch_result")
        _emit(ctx, "var " + catch_result + " *PytraErrorCarrier = nil")
    if len(finalbody) > 0:
        _emit(ctx, "defer func() {")
        ctx.indent_level += 1
        _emit_body(ctx, finalbody)
        ctx.indent_level -= 1
        _emit(ctx, "}()")
    handlers = _list(node, "handlers")
    if len(handlers) > 0:
        recovered_name = _next_temp(ctx, "recovered")
        err_name = _next_temp(ctx, "err")
        _emit(ctx, "defer func() {")
        ctx.indent_level += 1
        _emit(ctx, recovered_name + " := recover()")
        _emit(ctx, "if " + recovered_name + " == nil {")
        ctx.indent_level += 1
        _emit(ctx, "return")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit(ctx, err_name + " := pytraEnsureRecoveredError(" + recovered_name + ")")
        _emit_error_handlers(ctx, err_name, handlers, catch_result, defer_context=True)
        ctx.indent_level -= 1
        _emit(ctx, "}()")
    for stmt in _list(node, "body"):
        if isinstance(stmt, dict) and _str(stmt, "kind") == "ErrorCheck" and _str(stmt, "on_error") == "catch":
            call_node = stmt.get("call")
            if not isinstance(call_node, dict):
                continue
            ok_target = stmt.get("ok_target")
            ok_type = _str(stmt, "ok_type")
            ok_tmp = _next_temp(ctx, "ok")
            err_tmp = _next_temp(ctx, "err")
            call_code = _emit_expr(ctx, call_node)
            if ok_target is None or ok_type in ("", "None"):
                _emit(ctx, err_tmp + " := " + call_code)
            else:
                _emit(ctx, ok_tmp + ", " + err_tmp + " := " + call_code)
            _emit(ctx, "if " + err_tmp + " != nil {")
            ctx.indent_level += 1
            _emit_error_handlers(ctx, err_tmp, handlers, catch_result, defer_context=False)
            ctx.indent_level -= 1
            _emit(ctx, "}")
            if ok_target is not None and ok_type not in ("", "None"):
                ctx.var_types[ok_tmp] = ok_type
                assign_node: dict[str, JsonVal] = {
                    "kind": "Assign",
                    "target": ok_target,
                    "value": {"kind": "Name", "id": ok_tmp, "resolved_type": ok_type},
                    "declare": True,
                }
                _emit_assign(ctx, assign_node)
            continue
        if isinstance(stmt, dict) and _str(stmt, "kind") == "ErrorReturn":
            err_tmp2 = _next_temp(ctx, "err")
            _emit(ctx, err_tmp2 + " := " + _error_return_expr(ctx, stmt))
            _emit_error_handlers(ctx, err_tmp2, handlers, catch_result, defer_context=False)
            continue
        _emit_stmt(ctx, stmt)
    if catch_result != "":
        _emit(ctx, "return " + catch_result)
    elif _is_exception_type_name(ctx, ctx.current_return_type):
        _emit(ctx, "return nil")
    ctx.indent_level -= 1
    if _is_exception_type_name(ctx, ctx.current_return_type):
        _emit(ctx, "}()")
    else:
        _emit(ctx, "}()")


def _emit_raise(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    exc = node.get("exc")
    cause = node.get("cause")
    cause_code = ""
    if isinstance(cause, dict):
        cause_code = _emit_expr(ctx, cause)
    if isinstance(exc, dict):
        bn = _str(exc, "builtin_name")
        rc = _str(exc, "runtime_call")
        if bn in ctx.builtin_exc_bounds or rc == "std::runtime_error":
            panic_expr = ""
            exc_args = _list(exc, "args")
            if len(exc_args) >= 1:
                panic_expr = _exception_ctor_expr(ctx, bn if bn != "" else "RuntimeError", _emit_expr(ctx, exc_args[0]))
            else:
                name = bn if bn != "" else "RuntimeError"
                panic_expr = _exception_ctor_expr(ctx, name, _go_string_literal(name))
            if cause_code != "":
                panic_expr = "pytraAttachCause(" + panic_expr + ", " + cause_code + ")"
            _emit(ctx, "panic(" + panic_expr + ")")
        else:
            panic_expr2 = "pytraEnsureRecoveredError(" + _emit_expr(ctx, exc) + ")"
            if cause_code != "":
                panic_expr2 = "pytraAttachCause(" + panic_expr2 + ", " + cause_code + ")"
            _emit(ctx, "panic(" + panic_expr2 + ")")
    elif exc is not None:
        panic_expr3 = "pytraEnsureRecoveredError(" + _emit_expr(ctx, exc) + ")"
        if cause_code != "":
            panic_expr3 = "pytraAttachCause(" + panic_expr3 + ", " + cause_code + ")"
        _emit(ctx, "panic(" + panic_expr3 + ")")
    else:
        if ctx.current_exception_var != "":
            _emit(ctx, "panic(" + ctx.current_exception_var + ")")
        else:
            _emit(ctx, "panic(pytraNewRuntimeError(\"raise\"))")
    # Go requires unreachable return after panic in non-void functions
    if ctx.current_return_type != "" and ctx.current_return_type != "None":
        zv = go_zero_value(ctx.current_return_type)
        _emit(ctx, "return " + zv + " // unreachable")


def _emit_type_alias(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    value = _str(node, "value")
    go_name = _go_symbol_name(ctx, name)
    go_value = _go_type_with_ctx(ctx, value)
    if go_value == "" or go_value == "any":
        go_value = "any"
    _emit(ctx, "type " + go_name + " = " + go_value)


def _collect_module_private_symbols(body: list[JsonVal]) -> set[str]:
    out: set[str] = set()
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("FunctionDef", "ClassDef", "TypeAlias"):
            name = _str(stmt, "name")
            if name.startswith("_"):
                out.add(name)
            continue
        if kind in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            name2 = ""
            if isinstance(target, dict):
                name2 = _str(target, "id")
            elif isinstance(target, str):
                name2 = target
            if name2.startswith("_"):
                out.add(name2)
            continue
        if kind == "VarDecl":
            name3 = _str(stmt, "name")
            if name3.startswith("_"):
                out.add(name3)
    return out


# ---------------------------------------------------------------------------
# Module emission (top-level)
# ---------------------------------------------------------------------------

def emit_go_module(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a complete Go source file from an EAST3 document.

    Args:
        east3_doc: linked EAST3 JSON dict with meta.linked_program_v1.

    Returns:
        Go source code string, or empty string if the module should be skipped.
    """
    meta = _dict(east3_doc, "meta")
    module_id = ""

    # Get module_id from emit_context or linked_program_v1
    emit_ctx_meta = _dict(meta, "emit_context")
    if emit_ctx_meta:
        module_id = _str(emit_ctx_meta, "module_id")
    if module_id == "":
        module_id = _str(meta, "module_id")

    lp = _dict(meta, "linked_program_v1")
    if module_id == "" and lp:
        module_id = _str(lp, "module_id")

    # Derive module_id from source_path if not explicitly set
    if module_id == "":
        source_path = _str(east3_doc, "source_path")
        _TC2_PREFIX = "src/toolchain2/"
        if source_path.startswith(_TC2_PREFIX):
            rel = source_path[len(_TC2_PREFIX):]
            module_id = rel.replace("/", ".").removesuffix(".py")

    if module_id != "":
        expand_cross_module_defaults([east3_doc])

    # Load runtime mapping
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "go" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Skip modules provided by hand-written native files.
    if module_id in mapping.module_native_files:
        return ""

    # Skip runtime modules (provided by native runtime)
    if should_skip_module(module_id, mapping):
        return ""

    ctx = EmitContext(
        module_id=module_id,
        source_path=_str(east3_doc, "source_path"),
        is_entry=_bool(emit_ctx_meta, "is_entry") if emit_ctx_meta else False,
        mapping=mapping,
    )
    ctx.container_value_locals_by_scope = _load_container_value_locals(lp)

    # Populate ctx fields from mapping.json raw data to avoid hardcoded strings in emitter body
    _raw_map: dict[str, JsonVal] = {}
    if mapping_path.exists():
        import json as _json_stdlib
        _raw_map = _json_stdlib.loads(mapping_path.read_text())
    _go_pkg = _raw_map.get("go_pkg_imports") or {}
    ctx.go_pkg_math = (_go_pkg.get("float_math") or "") if isinstance(_go_pkg, dict) else ""
    ctx.go_pkg_os = (_go_pkg.get("file_io") or "") if isinstance(_go_pkg, dict) else ""
    ctx.go_pkg_sort = (_go_pkg.get("list_sort") or "") if isinstance(_go_pkg, dict) else ""
    _go_bd = _raw_map.get("go_builtin_dispatch") or {}
    ctx.dispatch_print = (_go_bd.get("print") or "") if isinstance(_go_bd, dict) else ""
    ctx.dispatch_len = (_go_bd.get("len") or "") if isinstance(_go_bd, dict) else ""
    _go_cn = _raw_map.get("go_class_names") or {}
    if isinstance(_go_cn, dict):
        _exc_bounds_raw = _go_cn.get("exception_type_bounds") or {}
        ctx.builtin_exc_bounds = {k: (v[0], v[1]) for k, v in _exc_bounds_raw.items()
                                   if isinstance(v, list) and len(v) >= 2} if isinstance(_exc_bounds_raw, dict) else {}
        _ctor_list = _go_cn.get("exception_ctor_types") or []
        ctx.builtin_exc_ctor_types = frozenset(_ctor_list) if isinstance(_ctor_list, list) else frozenset()
        ctx.path_type_name = (_go_cn.get("path_type") or "") if True else ""
        _argparse_type = (_go_cn.get("argparse_type") or "") if True else ""
    else:
        _argparse_type = ""
    ctx.known_method_signatures = {
        (_argparse_type, "add_argument"): _ARGPARSE_ADD_ARGUMENT_SIG,
    } if _argparse_type else {}

    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")
    ctx.module_private_symbols = _collect_module_private_symbols(body)

    # Collect imported runtime symbols for native helper resolution.
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)
    type_info_table = _dict(lp, "type_info_table_v1")
    if len(type_info_table) > 0:
        for fqcn, info in type_info_table.items():
            if not isinstance(fqcn, str) or not isinstance(info, dict):
                continue
            type_id_val = info.get("id")
            entry_val = info.get("entry")
            exit_val = info.get("exit")
            if isinstance(type_id_val, int):
                ctx.exception_type_ids[fqcn] = type_id_val
                ctx.class_type_ids[fqcn] = type_id_val
            if isinstance(entry_val, int) and isinstance(exit_val, int):
                ctx.exception_type_bounds[fqcn] = (entry_val, exit_val - 1)

    # Build import alias → module_id map for module.attr call resolution
    ctx.import_alias_modules = build_import_alias_map(meta)

    # Python type-constructor names used in type alias expressions like X = Union[A,B] or X = dict[K,V]
    _TYPE_ALIAS_BASES = frozenset({"Union", "Optional", "dict", "list", "set", "tuple", "Callable",
                                    "TypeVar", "TypeAlias", "Literal", "ClassVar", "Final",
                                    "Annotated", "Protocol"})

    # First pass: collect class names and union type aliases
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("Assign",):
            # Detect: X = Union[...] / X = dict[K,V] / X = list[T] → type alias declaration
            tgt = stmt.get("target")
            val = stmt.get("value")
            if (isinstance(tgt, dict) and _str(tgt, "kind") == "Name" and _str(tgt, "id") != ""
                    and isinstance(val, dict) and _str(val, "kind") == "Subscript"):
                subscript_base = val.get("value")
                if isinstance(subscript_base, dict) and _str(subscript_base, "id") in _TYPE_ALIAS_BASES:
                    ctx.union_type_aliases.add(_str(tgt, "id"))
        if isinstance(stmt, dict) and _str(stmt, "kind") == "FunctionDef":
            fn_name = _str(stmt, "name")
            if fn_name != "":
                _vd = _dict(stmt, "vararg_desugared_v1")
                if not _vd.get("vararg_name"):
                    _direct_vn = _str(stmt, "vararg_name")
                    if _direct_vn:
                        _vd = {"vararg_name": _direct_vn, "elem_type": _str(stmt, "vararg_type"), "list_type": ""}
                ctx.function_signatures[fn_name] = (
                    _list(stmt, "arg_order"),
                    _dict(stmt, "arg_types"),
                    _vd,
                )
                ctx.function_return_types[fn_name] = _str(stmt, "return_type")
        if isinstance(stmt, dict) and _str(stmt, "kind") == "ClassDef":
            class_name = _str(stmt, "name")
            ctx.class_names.add(class_name)
            if _is_trait_class(stmt):
                ctx.trait_names.add(class_name)
            base = _str(stmt, "base")
            if base != "":
                ctx.class_bases[class_name] = base
            if base in ("Enum", "IntEnum", "IntFlag"):
                ctx.enum_bases[class_name] = base
            static_methods = ctx.class_static_methods.setdefault(class_name, set())
            instance_methods = ctx.class_instance_methods.setdefault(class_name, {})
            class_vars = ctx.class_vars.setdefault(class_name, {})
            class_fields = ctx.class_fields.setdefault(class_name, {})
            enum_members = ctx.enum_members.setdefault(class_name, {})
            is_dataclass = _bool(stmt, "dataclass")
            field_types = _dict(stmt, "field_types")
            for field_name, field_type in field_types.items():
                if isinstance(field_name, str) and isinstance(field_type, str) and field_name != "":
                    class_fields[field_name] = field_type
            for class_stmt in _list(stmt, "body"):
                if not isinstance(class_stmt, dict):
                    continue
                class_stmt_kind = _str(class_stmt, "kind")
                if class_stmt_kind in ("FunctionDef", "ClosureDef"):
                    fn_name = _str(class_stmt, "name")
                    if fn_name == "__init__":
                        ctx.class_init_signatures[class_name] = {
                            "arg_order": _list(class_stmt, "arg_order"),
                            "arg_types": _dict(class_stmt, "arg_types"),
                            "arg_defaults": _dict(class_stmt, "arg_defaults"),
                        }
                    decorators = _list(class_stmt, "decorators")
                    is_staticmethod = False
                    for d in decorators:
                        if isinstance(d, str) and d == "staticmethod":
                            static_methods.add(fn_name)
                            is_staticmethod = True
                            break
                    if not is_staticmethod:
                        method_bucket = ctx.method_signatures.setdefault(class_name, {})
                        method_bucket[fn_name] = {
                            "arg_order": _list(class_stmt, "arg_order"),
                            "arg_types": _dict(class_stmt, "arg_types"),
                            "arg_defaults": _dict(class_stmt, "arg_defaults"),
                        }
                    if fn_name != "__init__" and not is_staticmethod:
                        instance_methods[fn_name] = class_stmt
                elif class_stmt_kind == "AnnAssign" and not is_dataclass:
                    target = class_stmt.get("target")
                    var_name = ""
                    if isinstance(target, dict):
                        var_name = _str(target, "id")
                    elif isinstance(target, str):
                        var_name = target
                    if var_name != "":
                        ann_type = _str(class_stmt, "decl_type")
                        if ann_type == "":
                            ann_type = _str(class_stmt, "annotation")
                        if ann_type != "" and var_name not in class_fields:
                            class_fields[var_name] = ann_type
                        value = class_stmt.get("value")
                        if not isinstance(value, dict):
                            continue
                        var_type = _str(class_stmt, "decl_type")
                        if var_type == "":
                            var_type = _str(class_stmt, "resolved_type")
                        spec: dict[str, JsonVal] = {"type": var_type}
                        spec["value"] = value
                        class_vars[var_name] = spec
                elif class_stmt_kind == "Assign" and not is_dataclass and class_name not in ctx.enum_bases:
                    target = class_stmt.get("target")
                    var_name = ""
                    if isinstance(target, dict):
                        var_name = _str(target, "id")
                    elif isinstance(target, str):
                        var_name = target
                    if var_name != "":
                        value = class_stmt.get("value")
                        var_type = _str(class_stmt, "decl_type")
                        if var_type == "" and isinstance(value, dict):
                            var_type = _str(value, "resolved_type")
                        spec = {"type": var_type}
                        if isinstance(value, dict):
                            spec["value"] = value
                        class_vars[var_name] = spec
                elif class_stmt_kind == "Assign" and class_name in ctx.enum_bases:
                    target = class_stmt.get("target")
                    var_name = ""
                    if isinstance(target, dict):
                        var_name = _str(target, "id")
                    elif isinstance(target, str):
                        var_name = target
                    if var_name != "":
                        var_type = _str(class_stmt, "decl_type")
                        if var_type == "":
                            value = class_stmt.get("value")
                            if isinstance(value, dict):
                                var_type = _str(value, "resolved_type")
                        spec = {"type": var_type}
                        value = class_stmt.get("value")
                        if isinstance(value, dict):
                            spec["value"] = value
                        enum_members[var_name] = spec
        if isinstance(stmt, dict) and _str(stmt, "kind") == "FunctionDef":
            mutated_arg = _detect_bytearray_mutating_first_arg(stmt)
            if mutated_arg != "":
                fn_names = {
                    _str(stmt, "name"),
                    _str(stmt, "original_name"),
                }
                for fn_name in list(fn_names):
                    if isinstance(fn_name, str) and fn_name != "":
                        fn_names.add(_go_symbol_name(ctx, fn_name))
                for fn_name in fn_names:
                    if isinstance(fn_name, str) and fn_name != "":
                        ctx.bytearray_mutating_funcs[fn_name] = mutated_arg

    # Derive constructor signatures for dataclasses without explicit __init__
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") == "ClassDef" and _bool(stmt, "dataclass"):
            cn = _str(stmt, "name")
            if cn != "" and cn not in ctx.class_init_signatures:
                fields = ctx.class_fields.get(cn, {})
                if fields:
                    arg_order = ["self"] + list(fields.keys())
                    arg_types: dict[str, str] = {}
                    for fn, ft in fields.items():
                        arg_types[fn] = ft
                    ctx.class_init_signatures[cn] = {
                        "arg_order": arg_order,
                        "arg_types": arg_types,
                        "arg_defaults": _dict(stmt, "field_defaults"),
                    }

    # Emit body
    for stmt in body:
        _emit_stmt(ctx, stmt)

    # Emit main guard
    if ctx.is_entry and len(main_guard) > 0:
        _emit_blank(ctx)
        _emit(ctx, "func _main_guard() {")
        ctx.indent_level += 1
        for stmt in main_guard:
            _emit_stmt(ctx, stmt)
        ctx.indent_level -= 1
        _emit(ctx, "}")

    entry_main_name = _emit_name(ctx, {"kind": "Name", "id": "main", "resolved_type": "callable"})

    # Generate main() for entry module
    if ctx.is_entry:
        _emit_blank(ctx)
        _emit(ctx, "func main() {")
        ctx.indent_level += 1
        if len(main_guard) > 0:
            _emit(ctx, "_main_guard()")
        elif "main" in ctx.function_signatures:
            _emit(ctx, entry_main_name + "()")
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # Build final source
    header_lines: list[str] = ["package main", ""]

    # Imports
    if len(ctx.imports_needed) > 0:
        header_lines.append("import (")
        for imp in sorted(ctx.imports_needed):
            if imp == "fmt":
                header_lines.append('\tgofmt "fmt"')
            else:
                header_lines.append('\t"' + imp + '"')
        header_lines.append(")")
        header_lines.append("")

    return "\n".join(header_lines + ctx.lines) + "\n"


def _detect_bytearray_mutating_first_arg(node: dict[str, JsonVal]) -> str:
    """Detect helpers like _png_append(dst: bytearray, src: bytearray) that mutate arg0."""
    if _str(node, "kind") != "FunctionDef":
        return ""
    if _str(node, "return_type") != "None":
        return ""
    arg_order = _list(node, "arg_order")
    if len(arg_order) == 0:
        return ""
    first_arg = arg_order[0]
    if not isinstance(first_arg, str) or first_arg == "":
        return ""
    arg_types = _dict(node, "arg_types")
    first_type = arg_types.get(first_arg, "")
    if not isinstance(first_type, str) or first_type != "bytearray":
        return ""
    if _function_has_return(node):
        return ""
    if _function_mutates_name(node.get("body"), first_arg):
        return first_arg
    return ""


def _function_has_return(node: JsonVal) -> bool:
    if isinstance(node, list):
        for item in node:
            if _function_has_return(item):
                return True
        return False
    if not isinstance(node, dict):
        return False
    if _str(node, "kind") == "Return":
        return True
    for value in node.values():
        if isinstance(value, (dict, list)) and _function_has_return(value):
            return True
    return False


def _function_mutates_name(node: JsonVal, target_name: str) -> bool:
    if isinstance(node, list):
        for item in node:
            if _function_mutates_name(item, target_name):
                return True
        return False
    if not isinstance(node, dict):
        return False

    kind = _str(node, "kind")
    if kind == "Call":
        func = node.get("func")
        if isinstance(func, dict) and _str(func, "kind") == "Attribute":
            owner = func.get("value")
            if isinstance(owner, dict) and _str(owner, "kind") == "Name" and _str(owner, "id") == target_name:
                method_key = _str(node, "resolved_runtime_call")
                if method_key == "":
                    method_key = _str(node, "runtime_call")
                if method_key == "":
                    method_key = _str(node, "runtime_symbol")
                if method_key in ("list.append", "list.extend", "list.pop", "list.clear", "bytearray.append", "bytearray.extend", "bytearray.pop", "bytearray.clear"):
                    return True
    if kind == "Assign":
        target = node.get("target")
        if isinstance(target, dict) and _str(target, "kind") == "Subscript":
            sub_value = target.get("value")
            if isinstance(sub_value, dict) and _str(sub_value, "kind") == "Name" and _str(sub_value, "id") == target_name:
                return True

    for value in node.values():
        if isinstance(value, (dict, list)) and _function_mutates_name(value, target_name):
            return True
    return False
