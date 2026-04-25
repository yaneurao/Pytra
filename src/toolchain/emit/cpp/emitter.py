"""EAST3 → C++ source code emitter.

Based on the Go emitter template. Generates standalone C++ source files
from linked EAST3 JSON documents.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.cpp.types import (
    cpp_type,
    cpp_zero_value,
    cpp_signature_type,
    cpp_param_decl,
    cpp_alias_union_expansion,
    normalize_cpp_nominal_adt_type,
    collect_cpp_type_vars,
    cpp_container_value_type,
    is_container_resolved_type,
    _top_level_optional_inner,
    _split_generic_args,
    init_types_mapping,
    normalize_cpp_container_alias,
)
from toolchain.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_import_alias_map, build_runtime_import_map, resolve_runtime_symbol_name,
)
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.emit.cpp.runtime_paths import collect_cpp_dependency_module_ids, cpp_include_for_module
from toolchain.common.types import split_generic_types, select_union_member_type
from toolchain.link.type_id import is_builtin_exception_type_name


# ---------------------------------------------------------------------------
# Emit context
# ---------------------------------------------------------------------------

@dataclass
class CppEmitContext:
    module_id: str = ""
    source_path: str = ""
    is_entry: bool = False
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    includes_needed: set[str] = field(default_factory=set)
    var_types: dict[str, str] = field(default_factory=dict)
    class_names: set[str] = field(default_factory=set)
    class_field_types: dict[str, dict[str, str]] = field(default_factory=dict)
    class_vars: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    class_bases: dict[str, str] = field(default_factory=dict)
    enum_kinds: dict[str, str] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_info: dict[str, dict[str, int]] = field(default_factory=dict)
    class_symbol_fqcns: dict[str, str] = field(default_factory=dict)
    function_mutable_param_indexes: dict[str, set[int]] = field(default_factory=dict)
    function_defs: dict[str, dict[str, JsonVal]] = field(default_factory=dict)
    current_class: str = ""
    current_return_type: str = ""
    current_function_scope: str = ""
    current_value_container_locals: set[str] = field(default_factory=set)
    runtime_imports: dict[str, str] = field(default_factory=dict)
    import_aliases: dict[str, str] = field(default_factory=dict)
    container_value_locals_by_scope: dict[str, set[str]] = field(default_factory=dict)
    value_container_vars: set[str] = field(default_factory=set)
    visible_local_scopes: list[set[str]] = field(default_factory=list)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    temp_counter: int = 0
    emit_class_decls: bool = True


@dataclass
class CppClassVarSpecDraft:
    type_name: str
    value: JsonVal = None

    def to_jv(self) -> dict[str, JsonVal]:
        out: dict[str, JsonVal] = {}
        out["type"] = self.type_name
        value_obj = json.JsonValue(self.value).as_obj()
        if value_obj is not None:
            out["value"] = self.value
        return out


def _indent(ctx: CppEmitContext) -> str:
    return "    " * ctx.indent_level

def _emit(ctx: CppEmitContext, line: str) -> None:
    ctx.lines.append(_indent(ctx) + line)


def _push_local_scope(ctx: CppEmitContext) -> None:
    ctx.visible_local_scopes.append(set())


def _pop_local_scope(ctx: CppEmitContext) -> None:
    if len(ctx.visible_local_scopes) > 0:
        ctx.visible_local_scopes.pop()


def _declare_local_visible(ctx: CppEmitContext, name: str) -> None:
    if name == "":
        return
    if len(ctx.visible_local_scopes) == 0:
        ctx.visible_local_scopes.append(set())
    ctx.visible_local_scopes[-1].add(name)


def _is_local_visible(ctx: CppEmitContext, name: str) -> bool:
    for scope in reversed(ctx.visible_local_scopes):
        if name in scope:
            return True
    return False

def _emit_blank(ctx: CppEmitContext) -> None:
    ctx.lines.append("")


def _emit_fail(ctx: CppEmitContext, code: str, detail: str) -> None:
    module_label = ctx.module_id if ctx.module_id != "" else "<unknown>"
    raise RuntimeError("cpp emitter " + code + " in " + module_label + ": " + detail)


def _resolve_runtime_call_local(
    runtime_call: str,
    builtin_name: str,
    adapter_kind: str,
    mapping: RuntimeMapping,
) -> str:
    if runtime_call in mapping.calls:
        return mapping.calls[runtime_call]
    if adapter_kind == "builtin":
        if runtime_call != "" and "." not in runtime_call:
            if mapping.builtin_prefix != "" and runtime_call.startswith(mapping.builtin_prefix):
                return runtime_call
            return mapping.builtin_prefix + runtime_call
        return ""
    if adapter_kind == "extern_delegate":
        return runtime_call
    if runtime_call == "" and builtin_name != "" and "." not in builtin_name:
        if builtin_name in mapping.calls:
            return mapping.calls[builtin_name]
        return mapping.builtin_prefix + builtin_name
    if runtime_call != "":
        if "." in runtime_call:
            return ""
        if mapping.builtin_prefix != "" and runtime_call.startswith(mapping.builtin_prefix):
            return runtime_call
        return mapping.builtin_prefix + runtime_call
    return ""


def _selfhost_cpp_signature_type(resolved_type: str) -> str:
    if resolved_type in ("int", "int64"):
        return "int64"
    if resolved_type in ("float", "float64"):
        return "float64"
    if resolved_type == "bool":
        return "bool"
    if resolved_type == "str":
        return "str"
    if resolved_type in ("Obj", "Any", "object", "unknown", ""):
        return "object"
    return resolved_type


def _selfhost_normalize_cpp_container_alias(resolved_type: str) -> str:
    normalized = normalize_cpp_nominal_adt_type(resolved_type)
    if normalized == "Node":
        return "dict[str,JsonVal]"
    return normalized + ""


def _resolve_runtime_symbol_name_local(
    symbol: str,
    mapping: RuntimeMapping,
    module_id: str = "",
    resolved_runtime_call: str = "",
    runtime_call: str = "",
) -> str:
    if resolved_runtime_call in mapping.calls:
        return mapping.calls[resolved_runtime_call]
    if runtime_call in mapping.calls:
        return mapping.calls[runtime_call]
    if module_id != "" and symbol != "":
        fqcn = module_id + "." + symbol
        if fqcn in mapping.calls:
            return mapping.calls[fqcn]
    if symbol == "":
        return ""
    if symbol.startswith(mapping.builtin_prefix):
        return symbol[len(mapping.builtin_prefix):]
    return mapping.builtin_prefix + symbol


def _module_needs_error_header(node: JsonVal) -> bool:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is not None:
        node_dict = node_obj.raw
        kind = _str(node_dict, "kind")
        if kind in ("Raise", "Try"):
            return True
        if kind == "Name" and is_builtin_exception_type_name(_str(node_dict, "id")):
            return True
        if kind == "ClassDef" and is_builtin_exception_type_name(_str(node_dict, "base")):
            return True
        for _key, value in node_dict.items():
            if _module_needs_error_header(value):
                return True
        return False
    node_arr = json.JsonValue(node).as_arr()
    if node_arr is not None:
        for item in node_arr.raw:
            if _module_needs_error_header(item):
                return True
    return False


class _CppStmtCommonRenderer(CommonRenderer):
    ctx: CppEmitContext
    _mutation_count: int

    def __init__(self, ctx: CppEmitContext) -> None:
        self.ctx = ctx
        self._mutation_count = 0
        super().__init__("cpp")
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
        return _emit_condition_expr(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("cpp common renderer assign string hook is not used directly")

    def emit_return_stmt(self, node: dict[str, JsonVal]) -> None:
        self._mutation_count += 1
        self.ctx.indent_level = self.state.indent_level + 0
        _emit_return(ctx=self.ctx, node=node)
        self.state.indent_level = self.ctx.indent_level

    def emit_expr_stmt(self, node: dict[str, JsonVal]) -> None:
        self._mutation_count += 1
        self.ctx.indent_level = self.state.indent_level + 0
        _emit_expr_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        self._mutation_count += 1
        self.ctx.indent_level = self.state.indent_level + 0
        kind = self._str(node, "kind")
        if kind == "AnnAssign":
            _emit_ann_assign(self.ctx, node)
        else:
            _emit_assign(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_stmt(self, node: JsonVal) -> None:
        self._mutation_count += 1
        kind = self._str(node, "kind")
        if kind in ("Expr", "Return", "Assign", "AnnAssign", "Pass", "comment", "blank", "If", "While", "Raise", "Try", "With"):
            stmt = node
            super().emit_stmt(stmt)
            self.ctx.indent_level = self.state.indent_level + 0
            return
        node_obj = json.JsonValue(node).as_obj()
        if node_obj is not None:
            self.emit_stmt_extension(node_obj.raw)

    def emit_body(self, body: list[JsonVal]) -> None:
        self._mutation_count += 1
        _push_local_scope(self.ctx)
        try:
            super().emit_body(body)
        finally:
            _pop_local_scope(self.ctx)

    def emit_raise_stmt(self, node: dict[str, JsonVal]) -> None:
        self._mutation_count += 1
        self.ctx.indent_level = self.state.indent_level + 0
        value = _render_raise_value(self.ctx, node)
        if value != "":
            self._emit("throw " + value + ";")
        else:
            self._emit("throw;")

    def render_raise_value(self, node: dict[str, JsonVal]) -> str:
        return _render_raise_value(self.ctx, node)

    def render_except_open(self, handler: dict[str, JsonVal]) -> str:
        return _render_except_open(self.ctx, handler)

    def emit_try_setup(self, node: dict[str, JsonVal]) -> None:
        finalbody = self._list(node, "finalbody")
        if len(finalbody) == 0:
            return
        finally_name = _next_temp(self.ctx, "__finally")
        self._emit("{")
        self.state.indent_level += 1
        self.ctx.indent_level = self.state.indent_level + 0
        self._emit("auto " + finally_name + " = py_make_scope_exit([&]() {")
        self.state.indent_level += 1
        self.ctx.indent_level = self.state.indent_level + 0
        self.emit_body(finalbody)
        self.state.indent_level -= 1
        self.ctx.indent_level = self.state.indent_level + 0
        self._emit("});")

    def emit_try_teardown(self, node: dict[str, JsonVal]) -> None:
        if len(self._list(node, "finalbody")) == 0:
            return
        self.state.indent_level -= 1
        self.ctx.indent_level = self.state.indent_level + 0
        self._emit("}")

    def emit_try_stmt(self, node: dict[str, JsonVal]) -> None:
        if len(self._list(node, "orelse")) > 0:
            raise RuntimeError("try/except/else is not supported in common renderer")
        body = self._list(node, "body")
        handlers = self._list(node, "handlers")
        self.emit_try_setup(node)
        if len(handlers) == 0:
            self.emit_body(body)
            self.emit_try_teardown(node)
            return
        self._emit("try {")
        self.state.indent_level += 1
        self.emit_body(body)
        self.state.indent_level -= 1
        self._emit("}")
        for raw_handler in handlers:
            raw_handler_obj = json.JsonValue(raw_handler).as_obj()
            if raw_handler_obj is None:
                continue
            raw_handler_dict = raw_handler_obj.raw
            catch_opens: list[str] = []
            catch_opens.append(self.render_except_open(raw_handler_dict))
            catch_opens.extend(_render_except_alternates(self.ctx, raw_handler_dict))
            for catch_open in catch_opens:
                self._emit(catch_open)
                self.state.indent_level += 1
                self.emit_try_handler_body(raw_handler_dict)
                self.state.indent_level -= 1
                self._emit("}")
        self.emit_try_teardown(node)

    def emit_try_handler_body(self, handler: dict[str, JsonVal]) -> None:
        handler_name = self._str(handler, "name")
        saved_type = ""
        had_saved_type = False
        if handler_name != "":
            had_saved_type = handler_name in self.ctx.var_types
            saved_type = self.ctx.var_types.get(handler_name, "")
            self.ctx.var_types[handler_name] = _handler_type_name(handler)
        self.ctx.indent_level = self.state.indent_level + 0
        self.emit_body(self._list(handler, "body"))
        if handler_name != "":
            if had_saved_type:
                self.ctx.var_types[handler_name] = saved_type
            elif handler_name in self.ctx.var_types:
                self.ctx.var_types.pop(handler_name, None)
        self.state.indent_level = self.ctx.indent_level

    def emit_stmt_extension(self, node: dict[str, JsonVal]) -> None:
        # P3-CR-CPP-S1: C++ 固有ノードの直接ディスパッチ。
        # _emit_stmt を経由しないことで循環を回避する。
        self.ctx.indent_level = self.state.indent_level + 0
        kind = self._str(node, "kind")
        if kind == "AugAssign": _emit_aug_assign(self.ctx, node)
        elif kind == "ForCore": _emit_for_core(self.ctx, node)
        elif kind == "FunctionDef": _emit_function_def(self.ctx, node)
        elif kind == "ClosureDef": _emit_closure_def(self.ctx, node)
        elif kind == "ClassDef": _emit_class_def(self.ctx, node)
        elif kind in ("ImportFrom", "Import", "TypeAlias"): pass
        elif kind == "VarDecl": _emit_var_decl(self.ctx, node)
        elif kind == "TupleUnpack": _emit_tuple_unpack(self.ctx, node)
        elif kind == "Swap": _emit_swap(self.ctx, node)
        else: _emit_fail(self.ctx, "unsupported_stmt_kind", kind)
        self.state.indent_level = self.ctx.indent_level


class _CppExprCommonRenderer(CommonRenderer):
    ctx: CppEmitContext

    def __init__(self, ctx: CppEmitContext) -> None:
        self.ctx = ctx
        super().__init__("cpp")

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
        raise RuntimeError("cpp common renderer assign hook is not used in expr adapter")

    def render_expr_extension(self, node: dict[str, JsonVal]) -> str:
        return _emit_expr_extension(self.ctx, node)



# ---------------------------------------------------------------------------
# Node accessors
# ---------------------------------------------------------------------------

def _str(node: dict[str, JsonVal], key: str) -> str:
    v = node.get(key)
    value = json.JsonValue(v).as_str()
    if value is not None:
        return value
    return ""

def _int(node: dict[str, JsonVal], key: str) -> int:
    v = node.get(key)
    value = json.JsonValue(v).as_int()
    if value is not None:
        return value
    return 0

def _bool(node: dict[str, JsonVal], key: str) -> bool:
    v = node.get(key)
    value = json.JsonValue(v).as_bool()
    if value is not None:
        return value
    return False

def _json_str_value(value: JsonVal) -> str:
    raw = json.JsonValue(value).as_str()
    if raw is not None:
        return raw
    return ""

def _json_int_value(value: JsonVal) -> int | None:
    raw = json.JsonValue(value).as_int()
    return raw

def _list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    v = node.get(key)
    value = json.JsonValue(v).as_arr()
    if value is not None:
        return value.raw
    return []

def _dict(node: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    v = node.get(key)
    value = json.JsonValue(v).as_obj()
    if value is not None:
        return value.raw
    return {}


def _sanitize_ident(text: str) -> str:
    out: list[str] = []
    for ch in text:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)


# C++ reserved keywords that valid Python identifiers may shadow.
_CPP_RESERVED_KEYWORDS: set[str] = {
    "alignas", "alignof", "and", "and_eq", "asm", "auto",
    "bitand", "bitor", "bool", "break",
    "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class",
    "compl", "concept", "const", "consteval", "constexpr", "constinit",
    "const_cast", "continue", "co_await", "co_return", "co_yield",
    "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern",
    "false", "float", "for", "friend",
    "goto",
    "if", "inline", "int",
    "long",
    "mutable",
    "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
    "operator", "or", "or_eq",
    "private", "protected", "public",
    "register", "reinterpret_cast", "requires", "return",
    "short", "signed", "sizeof", "static", "static_assert", "static_cast",
    "struct", "switch",
    "template", "this", "thread_local", "throw", "true", "try", "typedef",
    "typeid", "typename",
    "union", "unsigned", "using",
    "virtual", "void", "volatile",
    "wchar_t", "while",
    "xor", "xor_eq",
}


def _safe_cpp_ident(name: str) -> str:
    """Rename C++ reserved-keyword identifiers to avoid compile errors.

    Appends ``_`` suffix (mirrors Go emitter's ``_safe_go_ident``).
    """
    if name in _CPP_RESERVED_KEYWORDS:
        return name + "_"
    return name


def _lookup_explicit_runtime_symbol_mapping(
    ctx: CppEmitContext,
    *,
    resolved_runtime_call: str = "",
    runtime_call: str = "",
    runtime_symbol: str = "",
    fallback_symbol: str = "",
) -> str:
    keys: list[str] = [resolved_runtime_call, runtime_call, runtime_symbol, fallback_symbol]
    for key in keys:
        if key != "" and key in ctx.mapping.calls:
            return ctx.mapping.calls[key]
    return ""


def _effective_resolved_type(node: JsonVal) -> str:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return ""
    node_dict = node_obj.raw
    resolved_type = _str(node_dict, "resolved_type")
    if resolved_type not in ("", "unknown"):
        normalized = normalize_cpp_nominal_adt_type(resolved_type)
        return normalized + ""
    summary = _dict(node_dict, "type_expr_summary_v1")
    if _str(summary, "category") == "static":
        mirror = _str(summary, "mirror")
        if mirror != "":
            normalized_mirror = normalize_cpp_nominal_adt_type(mirror)
            return normalized_mirror + ""
    return resolved_type


def _attribute_static_type(ctx: CppEmitContext, node: JsonVal) -> str:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return ""
    node_dict = node_obj.raw
    if _str(node_dict, "kind") != "Attribute":
        return ""
    owner_node = node_dict.get("value")
    owner_type = _effective_resolved_type(owner_node)
    owner_obj = json.JsonValue(owner_node).as_obj()
    if owner_type in ("", "unknown") and owner_obj is not None:
        owner_id = _str(owner_obj.raw, "id")
        if owner_id in ("self", "this") and ctx.current_class != "":
            owner_type = ctx.current_class
    if owner_type == "":
        if owner_obj is not None:
            owner_type = _str(owner_obj.raw, "id")
    fields = ctx.class_field_types.get(owner_type, {})
    attr = _str(node_dict, "attr")
    return fields.get(attr, "")


def _expr_static_type(ctx: CppEmitContext, node: JsonVal) -> str:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is not None:
        node_dict = node_obj.raw
        kind = _str(node_dict, "kind")
        # Prefer the actual storage type from context for Name nodes
        if kind in ("Name", "NameTarget"):
            name = _str(node_dict, "id")
            if name != "" and name in ctx.var_types:
                return ctx.var_types[name]
        if kind == "Attribute":
            attr_type = _attribute_static_type(ctx, node_dict)
            if attr_type not in ("", "unknown"):
                return attr_type
    inferred = _effective_resolved_type(node)
    if inferred not in ("", "unknown"):
        return inferred
    if node_obj is not None:
        node_dict = node_obj.raw
        kind = _str(node_dict, "kind")
        if kind in ("Name", "NameTarget"):
            name = _str(node_dict, "id")
            if name != "":
                return ctx.var_types.get(name, "")
        if kind == "Attribute":
            return _attribute_static_type(ctx, node_dict)
    return ""


def _expr_storage_type(ctx: CppEmitContext, node: JsonVal) -> str:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return ""
    node_dict = node_obj.raw
    kind = _str(node_dict, "kind")
    if kind in ("Name", "NameTarget"):
        name = _str(node_dict, "id")
        if name != "":
            return ctx.var_types.get(name, "")
    if kind == "Attribute":
        return _attribute_static_type(ctx, node_dict)
    if kind == "Subscript":
        value_node = node_dict.get("value")
        effective_type = _effective_resolved_type(value_node)
        container_type = normalize_cpp_container_alias(effective_type)
        if container_type in ("", "unknown"):
            storage_type = _expr_storage_type(ctx, value_node)
            container_type = normalize_cpp_container_alias(storage_type)
        if container_type.startswith("list[") or container_type.startswith("set["):
            parts = _container_type_args(container_type)
            return parts[0] if len(parts) == 1 else ""
        if container_type.startswith("dict["):
            parts = _container_type_args(container_type)
            return parts[1] if len(parts) == 2 else ""
        if container_type.startswith("tuple["):
            parts = _container_type_args(container_type)
            slice_node = node_dict.get("slice")
            slice_obj = json.JsonValue(slice_node).as_obj()
            if slice_obj is not None and _str(slice_obj.raw, "kind") == "Constant":
                idx_raw = slice_obj.raw.get("value")
                idx = json.JsonValue(idx_raw).as_int()
                if idx is not None and 0 <= idx < len(parts):
                    return parts[idx]
    if kind == "Call":
        func = node_dict.get("func")
        func_obj = json.JsonValue(func).as_obj()
        if func_obj is not None and _str(func_obj.raw, "kind") == "Name":
            func_name = _str(func_obj.raw, "id")
            func_type = ctx.var_types.get(func_name, "")
            ret = _extract_std_function_return_type(func_type)
            if ret not in ("", "unknown"):
                return ret
            ret = _extract_callable_return_type(func_type)
            if ret not in ("", "unknown"):
                return ret
    if kind == "Unbox":
        target_text = _str(node_dict, "target")
        target = normalize_cpp_container_alias(target_text)
        if target not in ("", "unknown", "Obj", "Any", "object"):
            return target + ""
    if kind == "BinOp":
        left_type = _expr_storage_type(ctx, node_dict.get("left"))
        right_type = _expr_storage_type(ctx, node_dict.get("right"))
        if (
            left_type not in ("", "unknown")
            and left_type == right_type
            and not _needs_object_cast(left_type)
        ):
            return left_type
    return ""


def _extract_std_function_return_type(func_type: str) -> str:
    """Extract return type from ::std::function<RetType(Params)> string."""
    prefix = "::std::function<"
    if not func_type.startswith(prefix):
        return ""
    inner = func_type[len(prefix):]
    if inner.endswith(">"):
        inner = inner[:-1]
    paren = inner.find("(")
    if paren < 0:
        return ""
    return inner[:paren].strip()


def _extract_callable_return_type(func_type: str) -> str:
    if not (func_type.startswith("callable[") and func_type.endswith("]")):
        return ""
    inner = func_type[9:-1]
    parts = _split_generic_args(inner)
    if len(parts) != 2:
        return ""
    stripped = parts[1].strip()
    return stripped + ""


def _scope_key(ctx: CppEmitContext, func_name: str, owner_name: str = "") -> str:
    scope_name = func_name if owner_name == "" else owner_name + "." + func_name
    if ctx.module_id == "":
        return scope_name
    return ctx.module_id + "::" + scope_name


def _container_value_locals_for_scope(
    ctx: CppEmitContext,
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


def _prefer_value_container_local(ctx: CppEmitContext, name: str, resolved_type: str) -> bool:
    resolved_type_copy = resolved_type + ""
    return (
        name != ""
        and is_container_resolved_type(resolved_type_copy)
        and name in ctx.current_value_container_locals
    )


def _register_local_storage(ctx: CppEmitContext, name: str, resolved_type: str) -> None:
    normalized_type = normalize_cpp_nominal_adt_type(resolved_type)
    ctx.var_types[name] = normalized_type if normalized_type != "" else resolved_type
    if _prefer_value_container_local(ctx, name, resolved_type):
        ctx.value_container_vars.add(name)
    else:
        ctx.value_container_vars.discard(name)


def _decl_cpp_type(ctx: CppEmitContext, resolved_type: str, name: str = "") -> str:
    if resolved_type.startswith("callable["):
        ctx.includes_needed.add("functional")
    # User class names that shadow reserved type aliases (e.g., "Obj" from pytra.typing)
    if resolved_type in ctx.class_names and resolved_type in ("Obj",):
        return resolved_type
    resolved_type_copy = resolved_type + ""
    out = cpp_signature_type(
        resolved_type_copy,
        prefer_value_container=_prefer_value_container_local(ctx, name, resolved_type),
    )
    return out + ""


def _decl_cpp_zero_value(ctx: CppEmitContext, resolved_type: str, name: str = "") -> str:
    resolved_type_copy = resolved_type + ""
    out = cpp_zero_value(
        resolved_type_copy,
        prefer_value_container=_prefer_value_container_local(ctx, name, resolved_type),
    )
    return out + ""


def _uses_ref_container_storage(ctx: CppEmitContext, node: JsonVal) -> bool:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return False
    node_dict = node_obj.raw
    resolved_type = _effective_resolved_type(node_dict)
    resolved_type_copy = resolved_type + ""
    if not is_container_resolved_type(resolved_type_copy):
        return False
    kind = _str(node_dict, "kind")
    if kind in ("Name", "NameTarget"):
        name = _str(node_dict, "id")
        return name == "" or name not in ctx.value_container_vars
    if kind == "Attribute":
        return True
    return True


def _wrap_container_value_expr(resolved_type: str, value_expr: str) -> str:
    if resolved_type.startswith("list[") or resolved_type.startswith("dict[") or resolved_type.startswith("set["):
        return "rc_from_value(" + value_expr + ")"
    return value_expr


def _emit_union_member_value_expr(ctx: CppEmitContext, node: JsonVal, member_type: str) -> str:
    expr = _emit_expr(ctx, node)
    member_type_copy = member_type + ""
    normalized_member = normalize_cpp_container_alias(member_type_copy)
    normalized_member_copy = normalized_member + ""
    if not is_container_resolved_type(normalized_member_copy):
        return expr
    if _uses_ref_container_storage(ctx, node):
        return "(*(" + expr + "))"
    return expr


def _wrap_container_result_if_needed(node: dict[str, JsonVal], value_expr: str) -> str:
    resolved_type = _str(node, "resolved_type")
    resolved_type_copy = resolved_type + ""
    if not is_container_resolved_type(resolved_type_copy):
        return value_expr
    trimmed = value_expr.strip()
    if (
        trimmed.startswith("rc_from_value(")
        or trimmed.startswith("rc_list_from_value(")
        or trimmed.startswith("rc_dict_from_value(")
        or trimmed.startswith("rc_set_from_value(")
        or ".as<" in trimmed
    ):
        return value_expr
    return _wrap_container_value_expr(resolved_type, value_expr)


def _note_runtime_symbol_include(ctx: CppEmitContext, symbol_name: str) -> None:
    if symbol_name in {
        "py_upper",
        "py_lower",
        "py_strip",
        "py_lstrip",
        "py_rstrip",
        "py_split",
        "py_join",
        "py_startswith",
        "py_endswith",
        "py_replace",
        "py_find",
        "py_count",
    }:
        ctx.includes_needed.add("built_in/string_ops_fwd.h")


def _wrap_jsonval_node_expr(ctx: CppEmitContext, target_type: str, value_expr: str, value_node: JsonVal = None) -> str:
    if target_type != "JsonVal":
        return value_expr
    trimmed = value_expr.strip()
    if trimmed.endswith(".to_jv())") or trimmed.endswith(".to_jv()"):
        return value_expr
    value_obj = json.JsonValue(value_node).as_obj()
    if value_obj is not None:
        source_raw_type = _effective_resolved_type(value_obj.raw)
        source_type = normalize_cpp_nominal_adt_type(source_raw_type)
        if source_type in ctx.class_names:
            return "JsonVal((" + value_expr + ").to_jv())"
    for class_name in ctx.class_names:
        if (
            trimmed.startswith("::" + class_name + "(")
            or trimmed.startswith(class_name + "(")
            or trimmed.startswith("::" + class_name + "{")
            or trimmed.startswith(class_name + "{")
        ):
            return "JsonVal((" + value_expr + ").to_jv())"
    return value_expr


def _wrap_expr_for_target_type(ctx: CppEmitContext, target_type: str, value_expr: str, value_node: JsonVal = None) -> str:
    json_wrapped = _wrap_jsonval_node_expr(ctx, target_type, value_expr, value_node)
    if json_wrapped != value_expr:
        return json_wrapped
    target_type_copy = target_type + ""
    if not is_container_resolved_type(target_type_copy):
        # When assigning dict.get(no-default) to an optional variable, use py_dict_get_opt
        # so that missing keys produce an empty optional (None), not a zero-valued optional.
        optional_inner = _top_level_optional_inner(target_type)
        if optional_inner not in ("", "unknown") and value_expr.startswith("py_dict_get("):
            # Only for the 2-arg version (no default); 3-arg keeps py_dict_get.
            inner = value_expr[len("py_dict_get("):-1]
            if len(_split_generic_args(inner)) == 2:
                return "py_dict_get_opt(" + inner + ")"
        return value_expr
    value_obj = json.JsonValue(value_node).as_obj()
    if value_obj is not None:
        value_node_dict = value_obj.raw
        value_kind = _str(value_node_dict, "kind")
        if value_kind == "Box":
            boxed_inner = value_node_dict.get("value")
            inner_obj = json.JsonValue(boxed_inner).as_obj()
            if inner_obj is not None:
                inner_node: JsonVal = inner_obj.raw
                target_type_arg = target_type + ""
                return _emit_expr_as_type(ctx, inner_node, target_type_arg)
        if value_kind == "Dict":
            return _emit_dict_literal_for_target_type(ctx, value_node_dict, target_type)
        if value_kind == "List":
            return _emit_list_literal_for_target_type(ctx, value_node_dict, target_type)
        if value_kind == "Set":
            return _emit_set_literal_for_target_type(ctx, value_node_dict, target_type)
    if value_obj is not None:
        value_node_dict = value_obj.raw
        value_resolved_type = _effective_resolved_type(value_node_dict)
        value_storage_type = _expr_storage_type(ctx, value_node_dict)
        if value_resolved_type == target_type and value_storage_type in ("", target_type):
            return value_expr
    trimmed = value_expr.strip()
    if trimmed in ctx.var_types and ctx.var_types.get(trimmed, "") == target_type:
        return value_expr
    if (
        trimmed.startswith("rc_from_value(")
        or trimmed.startswith("rc_list_from_value(")
        or trimmed.startswith("rc_dict_from_value(")
        or trimmed.startswith("rc_set_from_value(")
        or ".as<" in trimmed
    ):
        return value_expr
    return _wrap_container_value_expr(target_type, value_expr)


def _container_type_args(resolved_type: str) -> list[str]:
    if "[" not in resolved_type or not resolved_type.endswith("]"):
        return []
    inner = resolved_type[resolved_type.find("[") + 1 : -1]
    return split_generic_types(inner)


def _object_box_container_target(resolved_type: str) -> str:
    if resolved_type.startswith("dict["):
        parts = _container_type_args(resolved_type)
        if len(parts) == 2:
            key_type = parts[0] if parts[0] not in ("", "unknown") else "str"
            return "dict[" + key_type + ",object]"
    if resolved_type.startswith("list["):
        return "list[object]"
    if resolved_type.startswith("set["):
        return "set[object]"
    return ""


def _emit_expr_as_type(ctx: CppEmitContext, node: JsonVal, target_type: str) -> str:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return _emit_expr(ctx, node)
    node_dict = node_obj.raw
    if target_type == "JsonVal":
        value_expr = _emit_expr(ctx, node_dict)
        wrapped = _wrap_jsonval_node_expr(ctx, target_type, value_expr, node_dict)
        if wrapped != value_expr:
            return wrapped
    node = _normalize_cpp_boundary_expr(ctx, node_dict)
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return _emit_expr(ctx, node)
    node = node_obj.raw
    node_kind = _str(node, "kind")
    if node_kind == "Box" and target_type not in ("Any", "Obj", "object"):
        inner = node.get("value")
        inner_obj = json.JsonValue(inner).as_obj()
        if inner_obj is not None:
            inner_node: JsonVal = inner_obj.raw
            target_type_arg = target_type + ""
            return _emit_expr_as_type(ctx, inner_node, target_type_arg)
    if node_kind == "Unbox" and target_type not in ("Any", "Obj", "object"):
        inner = node.get("value")
        inner_obj = json.JsonValue(inner).as_obj()
        if inner_obj is not None and _str(inner_obj.raw, "kind") == "Box":
            boxed_value = inner_obj.raw.get("value")
            boxed_value_obj = json.JsonValue(boxed_value).as_obj()
            if boxed_value_obj is not None:
                boxed_node: JsonVal = boxed_value_obj.raw
                target_type_arg = target_type + ""
                return _emit_expr_as_type(ctx, boxed_node, target_type_arg)
    storage_type = _expr_storage_type(ctx, node)
    if storage_type == target_type:
        kind = _str(node, "kind")
        if kind in ("Name", "NameTarget"):
            name = _str(node, "id")
            if name in ("self", "this") and target_type == ctx.current_class and ctx.current_class != "":
                return "(*this)"
            return _emit_name_storage(node)
        return _emit_expr(ctx, node)
    node_type = _effective_resolved_type(node)
    union_storage_type = _expanded_union_type(storage_type)
    if _optional_inner_type(target_type) != "" and node_type == "None":
        return "::std::nullopt"
    optional_inner = _optional_inner_type(target_type)
    if optional_inner != "":
        inner_type = "int64" if optional_inner == "int" else optional_inner
        inner_cpp = cpp_signature_type(inner_type)
        target_cpp = cpp_signature_type(target_type)
        if node_kind == "Unbox":
            boxed_value = node.get("value")
            boxed_storage = _expr_storage_type(ctx, boxed_value)
            boxed_inner = _optional_inner_type(boxed_storage)
            boxed_value_obj = json.JsonValue(boxed_value).as_obj()
            if (
                boxed_value_obj is not None
                and boxed_inner not in ("", "unknown")
                and not _is_top_level_union_type(boxed_inner)
                and _is_top_level_union_type(inner_type)
            ):
                boxed_expr = _emit_expr(ctx, boxed_value)
                return (
                    "([&]() -> "
                    + target_cpp
                    + " { auto&& __pytra_opt = "
                    + boxed_expr
                    + "; if (__pytra_opt) return "
                    + target_cpp
                    + "("
                    + inner_cpp
                    + "(*(__pytra_opt))); return ::std::nullopt; })()"
                )
        expr = _emit_expr(ctx, node)
        storage_cpp = cpp_signature_type(storage_type) if storage_type not in ("", "unknown") else ""
        if storage_cpp.startswith("::std::optional<::std::variant<") and inner_type in ("str", "int64", "float64", "bool"):
            return target_cpp + "(::std::get<" + inner_cpp + ">(*(" + expr + ")))"
        if storage_cpp.startswith("::std::variant<") and inner_type in ("str", "int64", "float64", "bool"):
            return target_cpp + "(::std::get<" + inner_cpp + ">(" + expr + "))"
        if node_type == optional_inner or node_type == inner_type:
            return target_cpp + "(" + _emit_expr_as_type(ctx, node, inner_type) + ")"
    if target_type not in ("", "unknown") and node_type == target_type:
        expr = _emit_expr(ctx, node)
        if _optional_inner_type(union_storage_type) == target_type:
            return "(*(" + expr + "))"
        if _has_variant_storage(storage_type):
            lane_expr = _emit_union_get_expr(expr, union_storage_type, target_type)
            if lane_expr != expr:
                return lane_expr
    if _is_top_level_union_type(target_type):
        if _str(node, "kind") == "Dict":
            dict_lane_target = "dict"
            lane = _select_union_lane(target_type, dict_lane_target)
            if lane != "":
                return cpp_signature_type(target_type) + "(" + _emit_dict_literal_for_target_type(ctx, node, lane) + ")"
        if _str(node, "kind") == "List":
            list_lane_target = "list"
            lane = _select_union_lane(target_type, list_lane_target)
            if lane != "":
                return cpp_signature_type(target_type) + "(" + _emit_list_literal_for_target_type(ctx, node, lane) + ")"
        if _str(node, "kind") == "Set":
            set_lane_target = "set"
            lane = _select_union_lane(target_type, set_lane_target)
            if lane != "":
                return cpp_signature_type(target_type) + "(" + _emit_set_literal_for_target_type(ctx, node, lane) + ")"
        expr = _emit_expr(ctx, node)
        direct_source_type = ""
        storage_optional_inner = _optional_inner_type(storage_type)
        if (
            storage_type not in ("", "unknown")
            and storage_optional_inner == ""
            and not _has_variant_storage(storage_type)
            and not _needs_object_cast(storage_type)
        ):
            direct_source_type = _expanded_union_type(storage_type)
        elif storage_optional_inner == "":
            static_value_type = _expr_static_type(ctx, node)
            static_union_type = _expanded_union_type(static_value_type)
            if (
                static_union_type not in ("", "unknown")
                and not _is_top_level_union_type(static_union_type)
                and not _needs_object_cast(static_union_type)
            ):
                direct_source_type = static_union_type
        if direct_source_type != "":
            lane = _select_union_lane(target_type, direct_source_type)
            if lane != "":
                direct_source_type_copy = direct_source_type + ""
                lane_copy = lane + ""
                norm_direct: str = normalize_cpp_container_alias(direct_source_type_copy) + ""
                norm_lane: str = normalize_cpp_container_alias(lane_copy) + ""
                norm_direct_check = norm_direct + ""
                if is_container_resolved_type(norm_direct_check) and norm_direct == norm_lane:
                    return cpp_signature_type(target_type) + "(" + _emit_union_member_value_expr(ctx, node, lane) + ")"
                return cpp_signature_type(target_type) + "(" + _emit_expr_as_type(ctx, node, direct_source_type) + ")"
        if node_type == target_type:
            if _has_variant_storage(storage_type):
                return expr
            return expr
        source_union_type = ""
        if _has_variant_storage(storage_type):
            source_union_type = union_storage_type
        elif storage_type in ("", "unknown") and _is_top_level_union_type(node_type):
            source_union_type = node_type
        if source_union_type != "":
            return _emit_union_narrow_expr(expr, source_union_type, target_type)
        lane = _select_union_lane(target_type, node_type)
        if lane != "":
            node_type_copy = node_type + ""
            lane_copy = lane + ""
            norm_node_type: str = normalize_cpp_container_alias(node_type_copy) + ""
            norm_lane: str = normalize_cpp_container_alias(lane_copy) + ""
            norm_node_type_check = norm_node_type + ""
            norm_lane_check = norm_lane + ""
            if is_container_resolved_type(norm_node_type_check) and is_container_resolved_type(norm_lane_check):
                if norm_node_type == norm_lane:
                    return cpp_signature_type(target_type) + "(" + _emit_union_member_value_expr(ctx, node, lane) + ")"
                return cpp_signature_type(target_type) + "(" + _emit_covariant_copy_expr(
                    ctx,
                    source_expr=expr,
                    source_type=norm_node_type,
                    target_type=norm_lane,
                ) + ")"
        if node_type == "None":
            return "::std::nullopt"
        return cpp_signature_type(target_type) + "(" + expr + ")"
    target_type_check = target_type + ""
    if is_container_resolved_type(target_type_check):
        expr = _emit_expr(ctx, node)
        source_type = _expr_storage_type(ctx, node)
        if source_type in ("", "unknown"):
            source_type = node_type
        target_type_copy = target_type + ""
        source_type_copy = source_type + ""
        node_type_copy = node_type + ""
        norm_target_type: str = normalize_cpp_container_alias(target_type_copy) + ""
        norm_source_type: str = normalize_cpp_container_alias(source_type_copy) + ""
        norm_node_type: str = normalize_cpp_container_alias(node_type_copy) + ""
        if norm_source_type == norm_target_type or (
            norm_node_type == norm_target_type and source_type in ("", "unknown")
        ):
            return expr
        if _has_variant_storage(source_type):
            lane = _select_union_lane(source_type, norm_target_type)
            if lane != "":
                return _emit_union_get_expr(expr, source_type, lane)
        norm_source_type_check = norm_source_type + ""
        if is_container_resolved_type(norm_source_type_check) and norm_source_type != norm_target_type:
            return _emit_covariant_copy_expr(
                ctx,
                source_expr=expr,
                source_type=norm_source_type,
                target_type=norm_target_type,
            )
    if target_type in ("Any", "Obj", "object"):
        widened_container_type = _object_box_container_target(_effective_resolved_type(node))
        if widened_container_type != "":
            kind = _str(node, "kind")
            if kind == "Dict":
                return "object(" + _emit_dict_literal_for_target_type(ctx, node, widened_container_type) + ")"
            if kind == "List":
                return "object(" + _emit_list_literal_for_target_type(ctx, node, widened_container_type) + ")"
            if kind == "Set":
                return "object(" + _emit_set_literal_for_target_type(ctx, node, widened_container_type) + ")"
        boxed: dict[str, JsonVal] = {}
        boxed["kind"] = "Box"
        boxed["resolved_type"] = target_type
        boxed["value"] = node
        boxed_node: JsonVal = boxed
        return _emit_expr(ctx, boxed_node)
    if target_type in ("Callable", "callable"):
        kind = _str(node, "kind")
        if kind == "Lambda":
            return _emit_expr(ctx, node)
        if kind in ("Name", "Attribute"):
            callable_name = _emit_expr(ctx, node)
            static_type = _expr_static_type(ctx, node)
            if static_type not in ("", "unknown", "Callable", "callable"):
                return callable_name
            return "([&](object) -> object { " + callable_name + "(); return object(); })"
    return _emit_expr(ctx, node)


def _emit_dict_literal_for_target_type(
    ctx: CppEmitContext,
    node: dict[str, JsonVal],
    target_type: str,
) -> str:
    parts = _container_type_args(target_type)
    if len(parts) != 2:
        return _emit_dict_literal(ctx, node)
    key_type = parts[0]
    value_type = parts[1]
    target_type_copy = target_type + ""
    plain_ct = cpp_type(target_type_copy, prefer_value_container=True)
    entries = _list(node, "entries")
    rendered: list[str] = []
    for entry in entries:
        entry_obj = json.JsonValue(entry).as_obj()
        if entry_obj is None:
            continue
        entry_dict = entry_obj.raw
        key_node = entry_dict.get("key")
        value_node = entry_dict.get("value")
        key_expr = _emit_expr_as_type(ctx, key_node, key_type)
        value_expr = _emit_expr_as_type(ctx, value_node, value_type)
        rendered.append(plain_ct + "::value_type{" + key_expr + ", " + value_expr + "}")
    literal = plain_ct + "{" + ", ".join(rendered) + "}"
    target_type_check = target_type + ""
    return _wrap_container_value_expr(target_type, literal) if is_container_resolved_type(target_type_check) else literal


def _emit_list_literal_for_target_type(
    ctx: CppEmitContext,
    node: dict[str, JsonVal],
    target_type: str,
) -> str:
    parts = _container_type_args(target_type)
    if len(parts) != 1:
        return _emit_list_literal(ctx, node)
    item_type = parts[0]
    target_type_copy = target_type + ""
    plain_ct = cpp_type(target_type_copy, prefer_value_container=True)
    elements = _list(node, "elements")
    rendered = [_emit_expr_as_type(ctx, elem, item_type) for elem in elements]
    literal = plain_ct + "{" + ", ".join(rendered) + "}"
    target_type_check = target_type + ""
    return _wrap_container_value_expr(target_type, literal) if is_container_resolved_type(target_type_check) else literal


def _emit_set_literal_for_target_type(
    ctx: CppEmitContext,
    node: dict[str, JsonVal],
    target_type: str,
) -> str:
    parts = _container_type_args(target_type)
    if len(parts) != 1:
        return _emit_set_literal(ctx, node)
    item_type = parts[0]
    target_type_copy = target_type + ""
    plain_ct = cpp_type(target_type_copy, prefer_value_container=True)
    elements = _list(node, "elements")
    rendered = [_emit_expr_as_type(ctx, elem, item_type) for elem in elements]
    literal = plain_ct + "{" + ", ".join(rendered) + "}"
    target_type_check = target_type + ""
    return _wrap_container_value_expr(target_type, literal) if is_container_resolved_type(target_type_check) else literal


def _optional_inner_type(type_name: str) -> str:
    t = type_name.strip()
    inner = ""
    if t.endswith(" | None"):
        inner = t[:-7].strip()
    elif t.endswith("|None"):
        inner = t[:-6].strip()
    elif t.startswith("None | "):
        inner = t[7:].strip()
    elif t.startswith("None|"):
        inner = t[5:].strip()
    if inner == "":
        return ""
    t_copy = t + ""
    cpp_t = cpp_signature_type(t_copy)
    if not cpp_t.startswith("::std::optional<"):
        return ""
    return inner


def _expanded_union_type(type_name: str) -> str:
    type_name_copy = type_name + ""
    normalized = normalize_cpp_nominal_adt_type(type_name_copy) + ""
    normalized_copy = normalized + ""
    expanded = cpp_alias_union_expansion(normalized_copy) + ""
    if expanded != "":
        return expanded + ""
    return normalized + ""


def _split_top_level_union_type(type_name: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    i = 0
    while i < len(type_name):
        ch = type_name[i]
        if ch in "[<(":
            depth += 1
            current.append(ch)
        elif ch in "]>)":
            depth -= 1
            current.append(ch)
        elif ch == "|" and depth == 0:
            part = "".join(current).strip()
            if part != "":
                parts.append(part)
            current = []
        else:
            current.append(ch)
        i += 1
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _is_top_level_union_type(type_name: str) -> bool:
    return len(_split_top_level_union_type(type_name)) > 1


def _union_effectively_single_type(type_name: str, expected: str) -> bool:
    if not _is_top_level_union_type(type_name):
        return False
    lanes = [lane for lane in _split_top_level_union_type(type_name) if lane not in ("None", "none")]
    if len(lanes) == 0:
        return False
    for lane in lanes:
        if lane != expected:
            return False
    return True


def _has_variant_storage(type_name: str) -> bool:
    if type_name in ("", "unknown"):
        return False
    type_name_copy = type_name + ""
    normalized = normalize_cpp_nominal_adt_type(type_name_copy) + ""
    normalized_copy = normalized + ""
    cpp_t = cpp_signature_type(normalized_copy)
    if cpp_t.startswith("::std::variant<") or cpp_t.startswith("::std::optional<::std::variant<"):
        return True
    expanded = _expanded_union_type(normalized)
    return expanded != normalized and _is_top_level_union_type(expanded)


def _union_lane_matches_expected(lane: str, expected_name: str) -> bool:
    expected_name = _canonical_expected_type_name(expected_name)
    if expected_name in ("int", "int64"):
        return lane in ("int", "int64")
    if expected_name in ("float", "float64"):
        return lane in ("float", "float64")
    if expected_name == "bool":
        return lane == "bool"
    if expected_name == "str":
        return lane == "str"
    if expected_name == "dict":
        return lane.startswith("dict[")
    if expected_name == "list":
        return lane.startswith("list[")
    if expected_name == "set":
        return lane.startswith("set[")
    if expected_name in ("None", "none"):
        return lane in ("None", "none")
    if expected_name == "object":
        return True
    return lane == expected_name


def _union_lane_matches_nominal_expected(
    ctx: CppEmitContext,
    lane: str,
    expected_name: str,
) -> bool:
    if _union_lane_matches_expected(lane, expected_name):
        return True
    return _is_known_class_subtype(ctx, lane, expected_name)


def _canonical_expected_type_name(expected_name: str) -> str:
    if expected_name == "int":
        return "int64"
    if expected_name == "float":
        return "float64"
    return expected_name


def _builtin_type_id_value(type_name: str) -> int | None:
    normalized = _canonical_expected_type_name(type_name)
    return {
        "None": 0,
        "none": 0,
        "bool": 1,
        "int": 2,
        "int64": 2,
        "float": 3,
        "float64": 3,
        "str": 4,
        "list": 5,
        "dict": 6,
        "set": 7,
    }.get(normalized)


def _emit_builtin_isinstance(value_expr: str, expected_name: str) -> str:
    normalized = _canonical_expected_type_name(expected_name)
    if normalized in ("None", "none"):
        return "py_is_none(" + value_expr + ")"
    if normalized in ("int", "int64"):
        return "py_is_int(" + value_expr + ")"
    if normalized in ("float", "float64"):
        return "py_is_float(" + value_expr + ")"
    if normalized == "bool":
        return "py_is_bool(" + value_expr + ")"
    if normalized == "str":
        return "py_is_str(" + value_expr + ")"
    if normalized == "list":
        return "py_is_list(" + value_expr + ")"
    if normalized == "dict":
        return "py_is_dict(" + value_expr + ")"
    if normalized == "set":
        return "py_is_set(" + value_expr + ")"
    if normalized == "object":
        return "py_is_object(" + value_expr + ")"
    return ""


def _emit_static_type_id_expr(ctx: CppEmitContext, type_name: str) -> str:
    normalized = _canonical_expected_type_name(type_name)
    builtin_id = _builtin_type_id_value(normalized)
    if builtin_id is not None:
        return "static_cast<pytra_type_id>(" + str(builtin_id) + ")"
    if normalized.startswith("list["):
        return "static_cast<pytra_type_id>(5)"
    if normalized.startswith("dict["):
        return "static_cast<pytra_type_id>(6)"
    if normalized.startswith("set["):
        return "static_cast<pytra_type_id>(7)"
    class_type_id = _lookup_class_type_id(ctx, normalized)
    if class_type_id is not None:
        return "static_cast<pytra_type_id>(" + str(class_type_id) + ")"
    return ""


def _select_union_lane(union_type: str, target_type: str) -> str:
    union_type = _expanded_union_type(union_type)
    target_type = _expanded_union_type(target_type)
    lanes = _split_top_level_union_type(union_type)
    for lane in lanes:
        if lane == target_type:
            return lane
    if target_type in ("int", "int64"):
        for lane in lanes:
            if lane in ("int", "int64"):
                return lane
    if target_type in ("float", "float64"):
        for lane in lanes:
            if lane in ("float", "float64"):
                return lane
    if target_type == "dict" or target_type.startswith("dict["):
        for lane in lanes:
            if lane.startswith("dict["):
                return lane
    if target_type == "list" or target_type.startswith("list["):
        for lane in lanes:
            if lane.startswith("list["):
                return lane
    if target_type == "set" or target_type.startswith("set["):
        for lane in lanes:
            if lane.startswith("set["):
                return lane
    selected = select_union_member_type(union_type, target_type)
    return selected + ""


def _union_has_none(union_type: str) -> bool:
    union_type = _expanded_union_type(union_type)
    lanes = _split_top_level_union_type(union_type)
    for lane in lanes:
        if lane in ("None", "none"):
            return True
    return False


def _unwrap_optional_variant(value_expr: str, union_type: str) -> str:
    """If the union contains None, the C++ type is optional<variant>.
    Return an expression that unwraps the optional to get the inner variant."""
    if _union_has_none(union_type):
        return "(*" + value_expr + ")"
    return value_expr


def _emit_union_get_expr(value_expr: str, union_type: str, target_type: str) -> str:
    union_type = _expanded_union_type(union_type)
    target_type = _expanded_union_type(target_type)
    if not (_is_top_level_union_type(union_type) or _has_variant_storage(union_type)):
        return value_expr
    lane = _select_union_lane(union_type, target_type)
    if lane == "":
        return value_expr
    lane_copy = lane + ""
    lane_cpp = cpp_signature_type(lane_copy)
    direct_prefix = "::std::get<" + lane_cpp + ">("
    if value_expr.startswith(direct_prefix):
        return value_expr
    inner = _unwrap_optional_variant(value_expr, union_type)
    if inner.startswith(direct_prefix):
        return inner
    return direct_prefix + inner + ")"


def _emit_union_narrow_expr(value_expr: str, source_type: str, target_type: str) -> str:
    target_type_copy = target_type + ""
    target_cpp = cpp_signature_type(target_type_copy)
    if source_type == target_type:
        return value_expr
    return "py_variant_narrow<" + target_cpp + ">(" + value_expr + ")"


def _union_compare_storage_type(ctx: CppEmitContext, node: JsonVal) -> str:
    storage_type = _expanded_union_type(_expr_storage_type(ctx, node))
    if _has_variant_storage(_expr_storage_type(ctx, node)):
        return storage_type
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return ""
    node_dict = node_obj.raw
    kind = _str(node_dict, "kind")
    static_type = _expanded_union_type(_expr_static_type(ctx, node_dict))
    if kind in ("Name", "Attribute", "Subscript", "Call", "IfExp", "CovariantCopy", "Unbox", "Box") and _is_top_level_union_type(static_type):
        return static_type
    return ""


def _emit_union_scalar_eq_compare(
    ctx: CppEmitContext,
    union_node: JsonVal,
    union_expr: str,
    scalar_expr: str,
    scalar_type: str,
    op_str: str,
) -> str:
    expanded_union = _union_compare_storage_type(ctx, union_node)
    if expanded_union == "":
        return ""
    lane = _select_union_lane(expanded_union, scalar_type)
    if lane == "":
        return ""
    lane_cpp = cpp_signature_type(lane)
    if _union_has_none(expanded_union):
        test_expr = "(" + union_expr + ".has_value() && ::std::holds_alternative<" + lane_cpp + ">(*" + union_expr + "))"
    else:
        test_expr = "::std::holds_alternative<" + lane_cpp + ">(" + union_expr + ")"
    value_expr = _emit_union_get_expr(union_expr, expanded_union, lane)
    cmp = "==" if op_str == "Eq" else "!="
    fallback = "false" if op_str == "Eq" else "true"
    return "(" + test_expr + " ? (" + value_expr + " " + cmp + " " + scalar_expr + ") : " + fallback + ")"


def _node_type_mirror(node: JsonVal) -> str:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return ""
    node_dict = node_obj.raw
    summary = node_dict.get("type_expr_summary_v1")
    summary_obj = json.JsonValue(summary).as_obj()
    if summary_obj is not None:
        mirror = json.JsonValue(summary_obj.raw.get("mirror")).as_str()
        if mirror is not None and mirror != "":
            return mirror
    return ""


def _resolve_runtime_attr_symbol(
    ctx: CppEmitContext,
    *,
    runtime_module_id: str = "",
    resolved_runtime_call: str = "",
    runtime_call: str = "",
    runtime_symbol: str = "",
    fallback_symbol: str = "",
) -> str:
    mapped = _lookup_explicit_runtime_symbol_mapping(
        ctx,
        resolved_runtime_call=resolved_runtime_call,
        runtime_call=runtime_call,
        runtime_symbol=runtime_symbol,
        fallback_symbol=fallback_symbol,
    )
    if mapped != "":
        return mapped
    symbol_name = runtime_symbol if runtime_symbol != "" else fallback_symbol
    if symbol_name == "":
        return ""
    if (
        runtime_module_id.startswith("pytra.")
        and symbol_name == fallback_symbol
        and symbol_name not in ctx.mapping.calls
    ):
        return symbol_name
    if (
        runtime_module_id.startswith("pytra.")
        and runtime_symbol != ""
        and fallback_symbol != ""
        and symbol_name not in ctx.mapping.calls
        and symbol_name.startswith(ctx.mapping.builtin_prefix)
    ):
        symbol_name = fallback_symbol
    if runtime_module_id != "" and should_skip_module(runtime_module_id, ctx.mapping):
        resolved = resolve_runtime_symbol_name(
            symbol_name,
            ctx.mapping,
            module_id=runtime_module_id,
            resolved_runtime_call=resolved_runtime_call,
            runtime_call=runtime_call,
        )
        return resolved + ""
    return symbol_name


def _build_class_symbol_fqcn_map(
    meta: dict[str, JsonVal],
    module_id: str,
    class_names: set[str],
    type_id_table: dict[str, int],
) -> dict[str, str]:
    out: dict[str, str] = {}
    if module_id != "":
        for class_name in class_names:
            fqcn = module_id + "." + class_name
            if fqcn in type_id_table:
                out[class_name] = fqcn

    bindings_sources: list[JsonVal] = [meta.get("import_resolution"), meta.get("import_bindings")]
    for raw in bindings_sources:
        raw_obj = json.JsonValue(raw).as_obj()
        bindings = raw_obj.raw.get("bindings") if raw_obj is not None else raw
        bindings_arr = json.JsonValue(bindings).as_arr()
        if bindings_arr is None:
            continue
        for binding in bindings_arr.raw:
            binding_obj = json.JsonValue(binding).as_obj()
            if binding_obj is None:
                continue
            binding_dict = binding_obj.raw
            local_name_raw = json.JsonValue(binding_dict.get("local_name")).as_str()
            export_name_raw = json.JsonValue(binding_dict.get("export_name")).as_str()
            if local_name_raw is None:
                continue
            local_name = local_name_raw
            if local_name == "":
                continue
            if export_name_raw is None:
                continue
            export_name = export_name_raw
            if export_name == "":
                continue
            candidate_module_raw = json.JsonValue(binding_dict.get("runtime_module_id")).as_str()
            candidate_module = ""
            if candidate_module_raw is not None:
                candidate_module = candidate_module_raw
            if candidate_module == "":
                fallback_module = json.JsonValue(binding_dict.get("module_id")).as_str()
                if fallback_module is not None:
                    candidate_module = fallback_module
            if candidate_module == "":
                continue
            fqcn = candidate_module + "." + export_name
            if fqcn in type_id_table:
                out[local_name] = fqcn
    return out


def _lookup_class_fqcn(ctx: CppEmitContext, type_name: str) -> str:
    if type_name == "":
        return ""
    fqcn = ctx.class_symbol_fqcns.get(type_name, "")
    if fqcn != "":
        return fqcn
    if type_name in ctx.class_type_ids:
        return type_name
    if ctx.module_id != "":
        local_fqcn = ctx.module_id + "." + type_name
        if local_fqcn in ctx.class_type_ids:
            return local_fqcn
    matches = [fqcn_name for fqcn_name in ctx.class_type_ids if fqcn_name.endswith("." + type_name)]
    if len(matches) == 1:
        return matches[0]
    return ""


def _lookup_class_type_id(ctx: CppEmitContext, type_name: str) -> int | None:
    fqcn = _lookup_class_fqcn(ctx, type_name)
    if fqcn == "":
        return None
    return ctx.class_type_ids.get(fqcn)


def _is_known_class_subtype(ctx: CppEmitContext, actual_type: str, expected_type: str) -> bool:
    actual_fqcn = _lookup_class_fqcn(ctx, actual_type)
    expected_fqcn = _lookup_class_fqcn(ctx, expected_type)
    if actual_fqcn == "" or expected_fqcn == "":
        return False
    actual_info = ctx.class_type_info.get(actual_fqcn, {})
    expected_info = ctx.class_type_info.get(expected_fqcn, {})
    actual_id = actual_info.get("id", -1)
    expected_entry = expected_info.get("entry", -1)
    expected_exit = expected_info.get("exit", -1)
    if actual_id < 0 or expected_entry < 0 or expected_exit < 0:
        return False
    return expected_entry <= actual_id < expected_exit


def _qualify_runtime_call_symbol(symbol_name: str) -> str:
    if symbol_name == "" or symbol_name.startswith("::") or "::" in symbol_name:
        return symbol_name
    return "::" + symbol_name


# ---------------------------------------------------------------------------
# Expression emission
# ---------------------------------------------------------------------------

def _emit_expr(ctx: CppEmitContext, node: JsonVal) -> str:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        _emit_fail(ctx, "invalid_expr", "expected dict expression node")
        return ""
    node_dict = node_obj.raw
    renderer = _CppExprCommonRenderer(ctx)
    node_arg: JsonVal = node_dict
    rendered = renderer.render_expr(node_arg)
    return rendered + ""


def _normalize_cpp_boundary_expr(ctx: CppEmitContext, node: JsonVal) -> JsonVal:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return node
    node_dict = node_obj.raw
    renderer = _CppExprCommonRenderer(ctx)
    normalized = renderer._normalize_boundary_expr(node_dict)
    return normalized


def _emit_expr_extension(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    kind = _str(node, "kind")

    if kind == "ObjTypeId": return _emit_obj_type_id(ctx, node)
    if kind == "IsInstance": return _emit_isinstance(ctx, node)
    if kind == "IsSubclass": return _emit_issubclass(ctx, node)
    if kind == "IsSubtype": return _emit_issubtype(ctx, node)
    if kind == "Call": return _emit_call(ctx, node)
    if kind == "Attribute": return _emit_attribute(ctx, node)
    if kind == "Subscript": return _emit_subscript(ctx, node)
    if kind == "List": return _emit_list_literal(ctx, node)
    if kind == "Set": return _emit_set_literal(ctx, node)
    if kind == "Dict": return _emit_dict_literal(ctx, node)
    if kind == "Tuple": return _emit_tuple_literal(ctx, node)
    if kind == "RangeExpr": return _emit_range_expr(ctx, node)
    if kind == "ListComp": return _emit_list_comp(ctx, node)
    if kind == "SetComp": return _emit_set_comp(ctx, node)
    if kind == "DictComp": return _emit_dict_comp(ctx, node)
    if kind == "CovariantCopy": return _emit_covariant_copy(ctx, node)
    if kind == "IfExp": return _emit_ifexp(ctx, node)
    if kind == "JoinedStr": return _emit_fstring(ctx, node)
    if kind == "FormattedValue": return _emit_formatted_value(ctx, node)
    if kind == "Lambda": return _emit_lambda(ctx, node)
    if kind == "Unbox": return _emit_unbox(ctx, node)
    if kind == "Box": return _emit_box(ctx, node)
    if kind == "ObjStr":
        value_node = node.get("value")
        value_expr = _emit_expr(ctx, value_node)
        if _expr_static_type(ctx, value_node) == "str":
            return value_expr
        return "str(py_to_string(" + value_expr + "))"
    if kind == "ObjLen": return "py_len(" + _emit_expr(ctx, node.get("value")) + ")"
    if kind == "ObjBool": return "py_bool(" + _emit_expr(ctx, node.get("value")) + ")"
    _emit_fail(ctx, "unsupported_expr_kind", kind)


def _emit_constant(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    val = node.get("value")
    if val is None: return "::std::nullopt"
    val_bool = json.JsonValue(val).as_bool()
    if val_bool is not None:
        return "true" if val_bool else "false"
    val_int = json.JsonValue(val).as_int()
    if val_int is not None:
        rt = _str(node, "resolved_type")
        if rt in ("float64", "float32", "float"): return str(float(val_int))
        if rt in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
            if rt in ("int", "int64"):
                return str(val_int)
            rt_copy = rt + ""
            return cpp_type(rt_copy) + "(" + str(val_int) + ")"
        return str(val_int)
    val_float = json.JsonValue(val).as_float()
    if val_float is not None:
        s = repr(val_float)
        if s == "inf": return "std::numeric_limits<double>::infinity()"
        if s == "-inf": return "-std::numeric_limits<double>::infinity()"
        return s
    val_str = json.JsonValue(val).as_str()
    if val_str is not None:
        return _cpp_string(val_str)
    return repr(val)


def _cpp_string(s: str) -> str:
    out: list[str] = ['"']
    for ch in s:
        if ch == "\\": out.append("\\\\")
        elif ch == '"': out.append('\\"')
        elif ch == "\n": out.append("\\n")
        elif ch == "\r": out.append("\\r")
        elif ch == "\t": out.append("\\t")
        elif ord(ch) < 32: out.append("\\x00")
        else: out.append(ch)
    out.append('"')
    return "str(" + "".join(out) + ")"


def _emit_name(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "": name = _str(node, "repr")
    if name == "__file__": return _cpp_string(ctx.source_path)
    if name == "True": return "true"
    if name == "False": return "false"
    if name == "None": return "::std::nullopt"
    if name == "self": return "this"
    if name == "continue": return "continue"
    if name == "break": return "break"
    if name == "main": return "__pytra_main"
    name = _safe_cpp_ident(name)
    resolved_type = _effective_resolved_type(node)
    storage_type = _expr_storage_type(ctx, node)
    optional_storage_inner = _optional_inner_type(storage_type)
    if (
        name != ""
        and resolved_type not in ("", "unknown")
        and storage_type not in ("", "unknown")
        and resolved_type != storage_type
    ):
        expanded_resolved = _expanded_union_type(resolved_type)
        if _is_top_level_union_type(expanded_resolved):
            return name
        if optional_storage_inner != "" and optional_storage_inner == resolved_type:
            return "(*" + name + ")"
        if _needs_object_cast(storage_type):
            if resolved_type in ("str", "int", "int64", "float", "float64", "bool"):
                return _emit_object_unbox(name, resolved_type)
            if resolved_type in ctx.class_names:
                return "(*(" + name + ").as<" + resolved_type + ">())"
            if is_container_resolved_type(resolved_type):
                return "(" + name + ").as<" + cpp_container_value_type(resolved_type) + ">()"
            if resolved_type.startswith("tuple[") or resolved_type in ("bytes", "bytearray"):
                return "(*(" + name + ").as<" + cpp_signature_type(resolved_type) + ">())"
    return name


def _emit_name_storage(node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "":
        name = _str(node, "repr")
    if name == "True":
        return "true"
    if name == "False":
        return "false"
    if name == "None":
        return "::std::nullopt"
    if name == "self":
        return "this"
    if name == "continue":
        return "continue"
    if name == "break":
        return "break"
    if name == "main":
        return "__pytra_main"
    return _safe_cpp_ident(name)


def _emit_binop(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    left_type = _effective_resolved_type(node.get("left"))
    right_type = _effective_resolved_type(node.get("right"))
    op = _str(node, "op")
    rt = _str(node, "resolved_type")
    # Apply casts
    for cast in _list(node, "casts"):
        cast_obj = json.JsonValue(cast).as_obj()
        if cast_obj is not None:
            cast_dict = cast_obj.raw
            on = _str(cast_dict, "on")
            to_type = _str(cast_dict, "to")
            cast_reason = _str(cast_dict, "reason")
            if cast_reason == "numeric_promotion" and _is_cpp_integer_type(to_type):
                continue
            to_type_copy = to_type + ""
            to = cpp_type(to_type_copy)
            if on == "left":
                left = "static_cast<" + to + ">(" + left + ")"
            elif on == "right":
                right = "static_cast<" + to + ">(" + right + ")"
    # List multiply
    if op == "Mult":
        ln = node.get("left")
        rn = node.get("right")
        ln_obj = json.JsonValue(ln).as_obj()
        if ln_obj is not None and _str(ln_obj.raw, "kind") == "List":
            elems = _list(ln_obj.raw, "elements")
            rt_copy = rt + ""
            value_ct: str = cpp_type(rt_copy, prefer_value_container=True) + ""
            if len(elems) == 1:
                repeated = value_ct + "(::std::size_t(" + right + "), " + _emit_expr(ctx, elems[0]) + ")"
            else:
                elem_strs = [_emit_expr(ctx, e) for e in elems]
                repeated = "py_repeat(" + value_ct + "{" + ", ".join(elem_strs) + "}, " + right + ")"
            rt_check = rt + ""
            return _wrap_container_value_expr(rt, repeated) if is_container_resolved_type(rt_check) else repeated
        rn_obj = json.JsonValue(rn).as_obj()
        if rn_obj is not None and _str(rn_obj.raw, "kind") == "List":
            elems = _list(rn_obj.raw, "elements")
            rt_copy = rt + ""
            value_ct: str = cpp_type(rt_copy, prefer_value_container=True) + ""
            if len(elems) == 1:
                repeated = value_ct + "(::std::size_t(" + left + "), " + _emit_expr(ctx, elems[0]) + ")"
            else:
                elem_strs = [_emit_expr(ctx, e) for e in elems]
                repeated = "py_repeat(" + value_ct + "{" + ", ".join(elem_strs) + "}, " + left + ")"
            rt_check = rt + ""
            return _wrap_container_value_expr(rt, repeated) if is_container_resolved_type(rt_check) else repeated
    if op == "FloorDiv": return "py_floordiv(" + left + ", " + right + ")"
    if op == "Mod": return "py_mod(" + left + ", " + right + ")"
    if op == "Pow": return "std::pow(static_cast<double>(" + left + "), static_cast<double>(" + right + "))"
    if op in ("BitOr", "BitAnd", "BitXor") and left_type == right_type and _enum_kind(ctx, left_type) == "IntFlag":
        enum_cpp = cpp_signature_type(left_type)
        base_expr = "static_cast<int64>(" + left + ") " + {"BitOr": "|", "BitAnd": "&", "BitXor": "^"}[op] + " static_cast<int64>(" + right + ")"
        return "static_cast<" + enum_cpp + ">(" + base_expr + ")"
    cpp_op = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
              "BitOr": "|", "BitAnd": "&", "BitXor": "^", "LShift": "<<", "RShift": ">>"}.get(op, "+")
    return "(" + left + " " + cpp_op + " " + right + ")"


def _emit_unaryop(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    if op == "USub":
        return "(-" + operand + ")"
    if op == "Not":
        return "(!" + operand + ")"
    if op == "Invert":
        return "(~" + operand + ")"
    return operand


def _is_non_optional_type_node(node: JsonVal) -> bool:
    """Return True if the EAST node's type is definitively non-optional (e.g. nominal ADT).

    Checks type_expr_summary_v1 category first, then falls back to resolved_type string.
    """
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return False
    node_dict = node_obj.raw
    summary = node_dict.get("type_expr_summary_v1")
    summary_obj = json.JsonValue(summary).as_obj()
    if summary_obj is not None:
        category = json.JsonValue(summary_obj.raw.get("category")).as_str()
        if category in ("nominal_adt", "static"):
            return True
    # Fallback: inspect the resolved_type string directly.
    resolved = _str(node_dict, "resolved_type")
    if not resolved or resolved in ("", "unknown", "None", "object"):
        return False
    return " | None" not in resolved and "Optional" not in resolved


def _emit_compare(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    left_node: JsonVal = node.get("left")
    ops = _list(node, "ops")
    comparators = _list(node, "comparators")
    if len(ops) == 0: return left
    parts: list[str] = []
    prev = left
    prev_node = left_node
    for i in range(len(ops)):
        op_value = json.JsonValue(ops[i]).as_str()
        op_str: str = ""
        if op_value is not None:
            op_str = op_value
        comp: JsonVal = None
        if i < len(comparators):
            comp = comparators[i]
        right = _emit_expr(ctx, comp)
        prev_type = _expr_static_type(ctx, prev_node)
        comp_type = _expr_static_type(ctx, comp)
        prev_is_nominal = prev_type in ctx.class_names or _is_non_optional_type_node(prev_node)
        comp_is_nominal = comp_type in ctx.class_names or _is_non_optional_type_node(comp)
        prev_is_none = prev == "::std::nullopt" or prev_type == "None"
        comp_is_none = right == "::std::nullopt" or comp_type == "None"
        if op_str == "In":
            range_contains = _emit_range_call_contains_expr(ctx, comp, prev)
            if range_contains != "":
                parts.append(range_contains)
            else:
                parts.append("py_contains(" + right + ", " + prev + ")")
        elif op_str == "NotIn":
            range_contains = _emit_range_call_contains_expr(ctx, comp, prev)
            if range_contains != "":
                parts.append("!(" + range_contains + ")")
            else:
                parts.append("!py_contains(" + right + ", " + prev + ")")
        elif op_str == "Is":
            if prev_is_none and comp_is_none:
                parts.append("true")
            elif prev_is_none:
                parts.append("py_is_none(" + right + ")")
            elif comp_is_none:
                parts.append("py_is_none(" + prev + ")")
            elif prev_type in ctx.class_names and comp_type in ctx.class_names:
                parts.append(
                    "([&]() -> bool { auto&& __pytra_left = "
                    + prev
                    + "; auto&& __pytra_right = "
                    + right
                    + "; return &__pytra_left == &__pytra_right; }())"
                )
            else:
                parts.append(
                    "(" + prev + " == " + right + ")"
                )
        elif op_str == "IsNot":
            if prev_is_none and comp_is_none:
                parts.append("false")
            elif prev_is_none:
                parts.append("!py_is_none(" + right + ")")
            elif comp_is_none:
                parts.append("!py_is_none(" + prev + ")")
            elif prev_type in ctx.class_names and comp_type in ctx.class_names:
                parts.append(
                    "([&]() -> bool { auto&& __pytra_left = "
                    + prev
                    + "; auto&& __pytra_right = "
                    + right
                    + "; return &__pytra_left != &__pytra_right; }())"
                )
            else:
                parts.append(
                    "(" + prev + " != " + right + ")"
                )
        else:
            prev_union_cmp = _emit_union_scalar_eq_compare(ctx, prev_node, prev, right, comp_type, op_str) if op_str in ("Eq", "NotEq") else ""
            if prev_union_cmp != "":
                parts.append(prev_union_cmp)
                prev = right
                prev_node = comp
                continue
            comp_union_cmp = _emit_union_scalar_eq_compare(ctx, comp, right, prev, prev_type, op_str) if op_str in ("Eq", "NotEq") else ""
            if comp_union_cmp != "":
                parts.append(comp_union_cmp)
                prev = right
                prev_node = comp
                continue
            if op_str == "Eq" and ((prev_is_nominal and comp_is_none) or (prev_is_none and comp_is_nominal)):
                parts.append("false")
            elif op_str == "NotEq" and ((prev_is_nominal and comp_is_none) or (prev_is_none and comp_is_nominal)):
                parts.append("true")
            else:
                cmp = {"Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=", "Gt": ">", "GtE": ">="}.get(op_str, "==")
                prev_cmp = prev
                right_cmp = right
                if _is_int_like_enum(ctx, prev_type) and comp_type in ("int", "int64"):
                    prev_cmp = "static_cast<int64>(" + prev + ")"
                elif _is_int_like_enum(ctx, comp_type) and prev_type in ("int", "int64"):
                    right_cmp = "static_cast<int64>(" + right + ")"
                # Incompatible type comparison (e.g. str vs numeric): box to object
                _numeric = {"int", "int64", "int32", "int8", "uint8", "uint32", "uint64", "float64", "float32"}
                if (prev_type == "str" and comp_type in _numeric) or (comp_type == "str" and prev_type in _numeric):
                    if op_str in ("Eq", "NotEq"):
                        prev_cmp = "object(" + prev_cmp + ")"
                        right_cmp = "object(" + right_cmp + ")"
                parts.append(
                    "(" + prev_cmp + " " + cmp + " " + right_cmp + ")"
                )
        prev = right
        prev_node = comp
    return " && ".join(parts) if len(parts) > 1 else parts[0]


def _emit_range_call_contains_expr(ctx: CppEmitContext, range_node: JsonVal, needle_expr: str) -> str:
    range_obj = json.JsonValue(range_node).as_obj()
    if range_obj is None:
        return ""
    range_dict = range_obj.raw
    kind = _str(range_dict, "kind")
    if kind not in ("RangeExpr", "Call"):
        return ""
    start_expr = "int64(0)"
    stop_expr = ""
    step_expr = "int64(1)"
    if kind == "RangeExpr":
        start_node: JsonVal = range_dict.get("start")
        stop_node: JsonVal = range_dict.get("stop")
        step_node: JsonVal = range_dict.get("step")
        stop_obj = json.JsonValue(stop_node).as_obj()
        if stop_obj is None:
            return ""
        start_obj = json.JsonValue(start_node).as_obj()
        if start_obj is not None:
            start_expr = _emit_expr(ctx, start_node)
        stop_expr = _emit_expr(ctx, stop_node)
        step_obj = json.JsonValue(step_node).as_obj()
        if step_obj is not None:
            step_expr = _emit_expr(ctx, step_node)
    else:
        args = _list(range_dict, "args")
        if len(args) == 0 or len(args) > 3:
            return ""
        if len(args) == 1:
            stop_expr = _emit_expr(ctx, args[0])
        elif len(args) == 2:
            start_expr = _emit_expr(ctx, args[0])
            stop_expr = _emit_expr(ctx, args[1])
        else:
            start_expr = _emit_expr(ctx, args[0])
            stop_expr = _emit_expr(ctx, args[1])
            step_expr = _emit_expr(ctx, args[2])
    if stop_expr == "":
        return ""
    pos_lane = (
        "(" + step_expr + " > int64(0))"
        + " && (" + needle_expr + " >= " + start_expr + ")"
        + " && (" + needle_expr + " < " + stop_expr + ")"
        + " && (((" + needle_expr + " - " + start_expr + ") % " + step_expr + ") == int64(0))"
    )
    neg_lane = (
        "(" + step_expr + " < int64(0))"
        + " && (" + needle_expr + " <= " + start_expr + ")"
        + " && (" + needle_expr + " > " + stop_expr + ")"
        + " && (((" + start_expr + " - " + needle_expr + ") % (-(" + step_expr + "))) == int64(0))"
    )
    return "((" + pos_lane + ") || (" + neg_lane + "))"


def _emit_boolop(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    op = _str(node, "op")
    values = _list(node, "values")
    if len(values) == 0:
        return "false"
    expr = _emit_expr(ctx, values[0])
    expr_type = _effective_resolved_type(values[0])
    result_type = _str(node, "resolved_type")
    for value in values[1:]:
        right = _emit_expr(ctx, value)
        cond = _emit_condition_code(expr, expr_type)
        if op == "And":
            expr = "(" + cond + " ? " + right + " : " + expr + ")"
        else:
            expr = "(" + cond + " ? " + expr + " : " + right + ")"
        if result_type != "":
            expr_type = result_type
        else:
            expr_type = _effective_resolved_type(value)
    return expr


def _emit_call(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    func: JsonVal = node.get("func")
    func_obj = json.JsonValue(func).as_obj()
    func_dict: dict[str, JsonVal] = {}
    if func_obj is not None:
        func_dict = func_obj.raw
    args = _list(node, "args")
    if func_obj is not None and _str(func_dict, "kind") == "Name" and _str(func_dict, "id") == "cast" and len(args) >= 2:
        return _emit_cast_expr(ctx, args[0], args[1])
    if _str(node, "lowered_kind") == "BuiltinCall":
        return _emit_builtin_call(ctx, node)
    func_name = _str(func_dict, "id") if func_obj is not None and _str(func_dict, "kind") == "Name" else ""
    expected_arg_types: list[str] = []
    if func_name != "":
        if func_name in ctx.function_defs:
            expected_arg_types = [arg_type for _, arg_type, _ in _function_param_meta(ctx.function_defs[func_name], ctx)]
    method_sig = _dict(node, "method_signature_v1")
    if len(expected_arg_types) == 0 and len(method_sig) > 0:
        expected_arg_types = [arg_type for _, arg_type, _ in _function_param_meta(method_sig, ctx)]
    elif len(expected_arg_types) == 0:
        function_sig = _dict(node, "function_signature_v1")
        if len(function_sig) > 0:
            expected_arg_types = [arg_type for _, arg_type, _ in _function_param_meta(function_sig, ctx)]
    arg_strs: list[str] = []
    for index in range(len(args)):
        a = args[index]
        expected_type = expected_arg_types[index] if index < len(expected_arg_types) else ""
        a_obj = json.JsonValue(a).as_obj()
        a_dict: dict[str, JsonVal] = {}
        if a_obj is not None:
            a_dict = a_obj.raw
        if expected_type == "" and a_obj is not None:
            expected_type = _str(a_dict, "call_arg_type")
        if expected_type != "" and _is_top_level_union_type(expected_type) and a_obj is not None:
            direct_source_type = ""
            storage_type = _expanded_union_type(_expr_storage_type(ctx, a))
            storage_optional_inner = _optional_inner_type(storage_type)
            if (
                storage_type not in ("", "unknown")
                and storage_optional_inner == ""
                and not _is_top_level_union_type(storage_type)
                and not _needs_object_cast(storage_type)
            ):
                direct_source_type = storage_type
            elif storage_optional_inner == "":
                static_type = _expanded_union_type(_expr_static_type(ctx, a))
                if static_type not in ("", "unknown") and not _is_top_level_union_type(static_type) and not _needs_object_cast(static_type):
                    direct_source_type = static_type
            if direct_source_type != "":
                lane = _select_union_lane(expected_type, direct_source_type)
                if lane != "":
                    arg_strs.append(
                        cpp_signature_type(expected_type)
                        + "("
                        + _emit_expr_as_type(ctx, a, direct_source_type)
                        + ")"
                    )
                    continue
        if a_obj is not None and _str(a_dict, "kind") == "Box" and expected_type not in ("", "Obj", "Any", "object"):
            boxed_value: JsonVal = a_dict.get("value")
            arg_strs.append(_emit_expr_as_type(ctx, boxed_value, expected_type))
        elif expected_type in ("Callable", "callable") and a_obj is not None:
            arg_strs.append(_emit_expr_as_type(ctx, a, expected_type))
        elif expected_type in ("Obj", "Any", "object") and a_obj is not None:
            arg_strs.append(_emit_expr_as_type(ctx, a, "object"))
        elif expected_type != "" and a_obj is not None:
            arg_strs.append(_emit_expr_as_type(ctx, a, expected_type))
        else:
            arg_strs.append(_emit_expr(ctx, a))
    keywords = _list(node, "keywords")
    keyword_strs: list[str] = []
    for kw in keywords:
        kw_obj = json.JsonValue(kw).as_obj()
        if kw_obj is not None:
            keyword_value: JsonVal = kw_obj.raw.get("value")
            keyword_strs.append(_emit_expr(ctx, keyword_value))
    call_arg_strs = list(arg_strs) + keyword_strs
    adapter = _str(node, "runtime_call_adapter_kind")
    if func_obj is not None:
        fk = _str(func_dict, "kind")
        if fk == "Attribute":
            attr = _str(func_dict, "attr")
            owner_node: JsonVal = func_dict.get("value")
            owner_obj = json.JsonValue(owner_node).as_obj()
            owner_dict: dict[str, JsonVal] = {}
            if owner_obj is not None:
                owner_dict = owner_obj.raw
            owner_runtime_module_id = _str(owner_dict, "runtime_module_id") if owner_obj is not None else ""
            owner = _emit_expr(ctx, owner_node)
            owner_type = _effective_resolved_type(owner_node)
            owner_id = _str(owner_dict, "id") if owner_obj is not None else ""
            owner_module = ctx.import_aliases.get(owner_id, "")
            runtime_module_id = _str(func_dict, "runtime_module_id")
            runtime_symbol = _str(func_dict, "runtime_symbol")
            runtime_call = _str(node, "runtime_call")
            resolved_runtime_call = _str(node, "resolved_runtime_call")
            call_meta = node.get("meta")
            call_meta_obj = json.JsonValue(call_meta).as_obj()
            mutates_receiver = False
            if call_meta_obj is not None:
                mutates_receiver_value = json.JsonValue(call_meta_obj.raw.get("mutates_receiver")).as_bool()
                mutates_receiver = mutates_receiver_value is True
            owner_borrow_kind = _str(owner_dict, "borrow_kind") if owner_obj is not None else ""
            if mutates_receiver and owner_borrow_kind == "mutable_ref" and len(args) >= 1:
                item_type = ""
                if owner_type.startswith("list[") and owner_type.endswith("]"):
                    item_type = owner_type[5:-1]
                elif owner_type in ("bytes", "bytearray"):
                    item_type = "uint8"
                if item_type != "":
                    return "py_list_append_mut(" + owner + ", " + _emit_expr_as_type(ctx, args[0], item_type) + ")"
            if _is_zero_arg_super_call(owner_node):
                base_name = ctx.class_bases.get(ctx.current_class, "")
                if base_name != "":
                    if attr == "__init__":
                        return ""
                    return base_name + "::" + attr + "(" + ", ".join(call_arg_strs) + ")"
            if owner_runtime_module_id != "" and should_skip_module(owner_runtime_module_id, ctx.mapping):
                symbol_name = _resolve_runtime_attr_symbol(
                    ctx,
                    runtime_module_id=owner_runtime_module_id,
                    resolved_runtime_call=resolved_runtime_call,
                    runtime_call=runtime_call,
                    runtime_symbol=runtime_symbol,
                    fallback_symbol=attr,
                )
                return _qualify_runtime_call_symbol(symbol_name) + "(" + ", ".join(call_arg_strs) + ")"
            if attr == "add_argument" and (_str(node, "semantic_tag") == "stdlib.method.add_argument" or len(keywords) > 0):
                call_arg_strs = _emit_argparse_add_argument_args(ctx, args, keywords)
            if _is_type_owner(ctx, owner_node):
                return owner + "::" + _safe_cpp_ident(attr) + "(" + ", ".join(call_arg_strs) + ")"
            if owner_module != "":
                symbol_name = _resolve_runtime_attr_symbol(
                    ctx,
                    runtime_module_id=runtime_module_id if runtime_module_id != "" else owner_module,
                    resolved_runtime_call=resolved_runtime_call,
                    runtime_call=runtime_call,
                    runtime_symbol=runtime_symbol,
                    fallback_symbol=attr,
                )
                return _qualify_runtime_call_symbol(symbol_name) + "(" + ", ".join(call_arg_strs) + ")"
            if runtime_module_id != "" and should_skip_module(runtime_module_id, ctx.mapping):
                symbol_name = _resolve_runtime_attr_symbol(
                    ctx,
                    runtime_module_id=runtime_module_id,
                    resolved_runtime_call=resolved_runtime_call,
                    runtime_call=runtime_call,
                    runtime_symbol=runtime_symbol,
                    fallback_symbol=attr,
                )
                return _qualify_runtime_call_symbol(symbol_name) + "(" + ", ".join(call_arg_strs) + ")"
            if runtime_call != "" or resolved_runtime_call != "":
                mapped_name: str = _resolve_runtime_call_local(
                    resolved_runtime_call if resolved_runtime_call != "" else runtime_call,
                    attr,
                    adapter,
                    ctx.mapping,
                )
                if mapped_name != "":
                    _note_runtime_symbol_include(ctx, mapped_name)
                    return _wrap_container_result_if_needed(
                        node,
                        _qualify_runtime_call_symbol(mapped_name) + "(" + ", ".join([owner] + call_arg_strs) + ")",
                    )
            # Fallback: look up <static_owner_type>.<attr> in the mapping for known value types
            # (covers cases where the resolver left resolved_type="unknown" on the call node).
            owner_static_type = _expr_static_type(ctx, owner_node)
            _static_owner_type = normalize_cpp_container_alias(owner_static_type)
            if _static_owner_type != "" and _static_owner_type != "unknown":
                _type_attr_key = _static_owner_type + "." + attr
                _fallback_name: str = _resolve_runtime_call_local(_type_attr_key, attr, adapter, ctx.mapping)
                if _fallback_name == "" and _static_owner_type.startswith("dict["):
                    _fallback_name = _resolve_runtime_call_local("dict." + attr, attr, adapter, ctx.mapping)
                if _fallback_name != "":
                    _note_runtime_symbol_include(ctx, _fallback_name)
                    return _wrap_container_result_if_needed(
                        node,
                        _qualify_runtime_call_symbol(_fallback_name) + "(" + ", ".join([owner] + call_arg_strs) + ")",
                    )
            if owner == "this":
                return "this->" + _safe_cpp_ident(attr) + "(" + ", ".join(call_arg_strs) + ")"
            member_sep = "->" if _uses_ref_container_storage(ctx, owner_node) else "."
            return owner + member_sep + _safe_cpp_ident(attr) + "(" + ", ".join(call_arg_strs) + ")"
        if fk == "Name":
            fn = _str(func_dict, "id")
            if fn == "": fn = _str(func_dict, "repr")
            runtime_call = _str(node, "runtime_call")
            resolved_runtime_call = _str(node, "resolved_runtime_call")
            func_runtime_module_id = _str(func_dict, "runtime_module_id")
            func_storage_type = _expr_storage_type(ctx, func)
            func_resolved_type = _effective_resolved_type(func)
            if fn == "cast" and len(args) >= 2:
                return _emit_cast_expr(ctx, args[0], args[1])
            if fn in ("bytearray", "bytes"):
                a0: JsonVal = None
                a0_obj = json.JsonValue(a0).as_obj()
                if len(args) >= 1:
                    a0 = args[0]
                    a0_obj = json.JsonValue(a0).as_obj()
                if len(args) >= 1 and a0_obj is not None:
                    a0_dict = a0_obj.raw
                    a0_kind = _str(a0_dict, "kind")
                    a0_rt = _str(a0_dict, "resolved_type")
                    if a0_kind == "List":
                        elems = _list(a0_dict, "elements")
                        parts = ["uint8(" + _emit_expr(ctx, e) + ")" for e in elems]
                        return "bytes{" + ", ".join(parts) + "}"
                    if a0_rt in ("int64", "int32", "int", "uint8", "int8"):
                        return "bytes(" + arg_strs[0] + ")"
                if len(arg_strs) >= 1:
                    return "bytes(" + arg_strs[0] + ")"
                return "bytes{}"
            if fn in ctx.class_names: return fn + "(" + ", ".join(call_arg_strs) + ")"
            if fn in ctx.runtime_imports: return ctx.runtime_imports[fn] + "(" + ", ".join(call_arg_strs) + ")"
            if func_runtime_module_id == "pytra.built_in.error":
                return fn + "(" + ", ".join(call_arg_strs) + ")"
            if fn == "main": return "__pytra_main(" + ", ".join(call_arg_strs) + ")"
            # Transpiled (non-native) pytra.* modules: use bare function name without builtin prefix.
            call_runtime_module_id = _str(node, "runtime_module_id")
            if call_runtime_module_id == "":
                call_runtime_module_id = func_runtime_module_id
            if (
                call_runtime_module_id != ""
                and call_runtime_module_id.startswith("pytra.")
                and not should_skip_module(call_runtime_module_id, ctx.mapping)
            ):
                return "::" + _safe_cpp_ident(fn) + "(" + ", ".join(call_arg_strs) + ")"
            if runtime_call != "" or resolved_runtime_call != "":
                mapped_name: str = _resolve_runtime_call_local(
                    resolved_runtime_call if resolved_runtime_call != "" else runtime_call,
                    fn,
                    adapter,
                    ctx.mapping,
                )
                if mapped_name != "":
                    _note_runtime_symbol_include(ctx, mapped_name)
                    return _qualify_runtime_call_symbol(mapped_name) + "(" + ", ".join(call_arg_strs) + ")"
            # Qualify module-level calls with :: so class method names can't shadow them.
            # Only skip :: for local variables (closures/lambdas) visible in scope.
            safe_fn = _safe_cpp_ident(fn)
            if _type_uses_callable(_optional_inner_type(_expanded_union_type(func_storage_type))):
                return "(*(" + _emit_name_storage(func) + "))(" + ", ".join(call_arg_strs) + ")"
            if _is_local_visible(ctx, fn):
                return safe_fn + "(" + ", ".join(call_arg_strs) + ")"
            return "::" + safe_fn + "(" + ", ".join(call_arg_strs) + ")"
    func_expr = _emit_expr(ctx, func)
    func_storage_type = _expr_storage_type(ctx, func)
    func_resolved_type = _effective_resolved_type(func)
    if _type_uses_callable(_optional_inner_type(_expanded_union_type(func_storage_type))):
        return "(*(" + func_expr + "))(" + ", ".join(call_arg_strs) + ")"
    return func_expr + "(" + ", ".join(call_arg_strs) + ")"


def _emit_argparse_add_argument_args(
    ctx: CppEmitContext,
    args: list[JsonVal],
    keywords: list[JsonVal],
) -> list[str]:
    positional = [_emit_expr_as_type(ctx, arg, "str") for arg in args[:4]]
    while len(positional) < 4:
        positional.append('str("")')

    keyword_map: dict[str, str] = {}
    for kw in keywords:
        kw_obj = json.JsonValue(kw).as_obj()
        if kw_obj is None:
            continue
        kw_dict = kw_obj.raw
        name = _str(kw_dict, "arg")
        if name == "":
            continue
        value: JsonVal = kw_dict.get("value")
        if name in ("help", "action"):
            keyword_map[name] = _emit_expr_as_type(ctx, value, "str")
            continue
        if name == "choices":
            keyword_map[name] = _emit_expr_as_type(ctx, value, "list[str]")
            continue
        keyword_map[name] = _emit_expr(ctx, value)

    return positional + [
        keyword_map.get("help", 'str("")'),
        keyword_map.get("action", 'str("")'),
        keyword_map.get("choices", "rc_from_value(list<str>{})"),
        keyword_map.get("default", "object()"),
    ]


def _emit_condition_code(expr: str, resolved_type: str) -> str:
    if (
        resolved_type.startswith("list[")
        or resolved_type.startswith("dict[")
        or resolved_type.startswith("set[")
        or resolved_type in ("bytes", "bytearray")
    ):
        return "py_to_bool(" + expr + ")"
    return expr


def _emit_condition_expr(ctx: CppEmitContext, node: JsonVal) -> str:
    expr = _emit_expr(ctx, node)
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return expr
    return _emit_condition_code(expr, _str(node_obj.raw, "resolved_type"))


def _emit_builtin_call(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    rc = _str(node, "runtime_call")
    semantic_tag = _str(node, "semantic_tag")
    if rc == "":
        if semantic_tag == "core.bytearray_ctor":
            rc = "bytearray_ctor"
        elif semantic_tag == "core.bytes_ctor":
            rc = "bytes_ctor"
        elif semantic_tag == "core.dict_ctor":
            rc = "dict_ctor"
        elif semantic_tag == "core.list_ctor":
            rc = "list_ctor"
        elif semantic_tag == "core.set_ctor":
            rc = "set_ctor"
    args = _list(node, "args")
    a0: JsonVal = None
    a0_obj = json.JsonValue(a0).as_obj()
    a0_dict: dict[str, JsonVal] = {}
    if len(args) >= 1:
        a0 = args[0]
        a0_obj = json.JsonValue(a0).as_obj()
        if a0_obj is not None:
            a0_dict = a0_obj.raw
    func: JsonVal = node.get("func")
    func_obj = json.JsonValue(func).as_obj()
    func_dict: dict[str, JsonVal] = {}
    if func_obj is not None:
        func_dict = func_obj.raw
    if rc == "static_cast" and len(args) >= 2:
        return _emit_cast_expr(ctx, args[0], args[1])
    if func_obj is not None and _str(func_dict, "kind") == "Name" and _str(func_dict, "id") == "cast" and len(args) >= 2:
        return _emit_cast_expr(ctx, args[0], args[1])
    arg_strs = [_emit_expr(ctx, a) for a in args]
    call_arg_strs = arg_strs
    func_is_attr = func_obj is not None and _str(func_dict, "kind") == "Attribute"
    if func_is_attr:
        func_owner: JsonVal = func_dict.get("value")
        call_arg_strs = [_emit_expr(ctx, func_owner)] + arg_strs
    if rc == "list.append" and func_is_attr and len(args) >= 1:
        owner_node: JsonVal = func_dict.get("value")
        owner_type = _effective_resolved_type(owner_node)
        item_type = ""
        if owner_type.startswith("list[") and owner_type.endswith("]"):
            item_type = owner_type[5:-1]
        elif owner_type in ("bytes", "bytearray"):
            item_type = "uint8"
        if item_type != "":
            call_arg_strs = [_emit_expr(ctx, owner_node), _emit_expr_as_type(ctx, args[0], item_type)]
    if rc == "list.sort" and func_is_attr:
        ctx.includes_needed.add("built_in/list_ops.h")
        owner_value: JsonVal = func_dict.get("value")
        return "py_list_sort_mut(" + _emit_expr(ctx, owner_value) + ")"
    if rc == "list.reverse" and func_is_attr:
        ctx.includes_needed.add("built_in/list_ops.h")
        owner_value: JsonVal = func_dict.get("value")
        return "py_list_reverse_mut(" + _emit_expr(ctx, owner_value) + ")"
    if rc == "dict.get" and func_is_attr and len(args) >= 1:
        owner_node: JsonVal = func_dict.get("value")
        owner_type = _expanded_union_type(_effective_resolved_type(owner_node))
        owner_storage_type = _expanded_union_type(_expr_storage_type(ctx, owner_node))
        if _is_top_level_union_type(owner_storage_type):
            dict_lane_type = "dict"
            lane = _select_union_lane(owner_storage_type, dict_lane_type)
            if lane != "":
                owner_type = lane
        elif _is_top_level_union_type(owner_type):
            dict_lane_type = "dict"
            lane = _select_union_lane(owner_type, dict_lane_type)
            if lane != "":
                owner_type = lane
        if owner_type.startswith("dict[") and owner_type.endswith("]"):
            dparts = _container_type_args(owner_type)
            if len(dparts) == 2:
                value_type = dparts[1]
                owner_expr = _emit_expr(ctx, owner_node)
                if owner_storage_type not in ("", "unknown") and owner_storage_type != owner_type and _is_top_level_union_type(owner_storage_type):
                    owner_type_copy = owner_type + ""
                    lane = _select_union_lane(owner_storage_type, owner_type_copy)
                    if lane != "":
                        owner_expr = _emit_union_get_expr(owner_expr, owner_storage_type, lane)
                elif _is_top_level_union_type(owner_type):
                    dict_lane_type = "dict"
                    lane = _select_union_lane(owner_type, dict_lane_type)
                    if lane != "":
                        owner_expr = _emit_union_get_expr(owner_expr, owner_type, lane)
                rendered_args = [_emit_expr(ctx, args[0])]
                if len(args) >= 2:
                    rendered_args.append(_emit_expr_as_type(ctx, args[1], value_type))
                call_arg_strs = [owner_expr] + rendered_args
    if rc == "dict.pop" and func_is_attr and len(args) >= 1:
        ctx.includes_needed.add("built_in/dict_ops.h")
        owner_value: JsonVal = func_dict.get("value")
        owner_expr = _emit_expr(ctx, owner_value)
        rendered_args = [_emit_expr(ctx, args[0])]
        if len(args) >= 2:
            rendered_args.append(_emit_expr(ctx, args[1]))
        return "py_dict_pop_mut(" + ", ".join([owner_expr] + rendered_args) + ")"
    if rc == "dict.setdefault" and func_is_attr and len(args) >= 1:
        ctx.includes_needed.add("built_in/dict_ops.h")
        owner_value: JsonVal = func_dict.get("value")
        owner_expr = _emit_expr(ctx, owner_value)
        rendered_args = [_emit_expr(ctx, args[0])]
        if len(args) >= 2:
            rendered_args.append(_emit_expr(ctx, args[1]))
        return "py_dict_setdefault_mut(" + ", ".join([owner_expr] + rendered_args) + ")"

    if rc in ("py_min", "py_max") and len(args) >= 2:
        target_type = _str(node, "resolved_type")
        forced_args = [_emit_expr_with_forced_literal_type(ctx, arg, target_type) for arg in args]
        resolved = _resolve_runtime_call_local(rc, "", _str(node, "runtime_call_adapter_kind"), ctx.mapping)
        if resolved != "":
            return resolved + "(" + ", ".join(forced_args) + ")"

    if rc in ("static_cast", "int", "float", "bool"):
        rt = _str(node, "resolved_type")
        ct = cpp_signature_type(rt)
        if len(args) >= 1 and a0_obj is not None:
            arg_kind = _str(a0_dict, "kind")
            arg_resolved_type = _expanded_union_type(_str(a0_dict, "resolved_type"))
            if arg_kind == "Box" and rt not in ("", "unknown", "Any", "Obj", "object"):
                    return _emit_expr_as_type(ctx, a0, rt)
            if (
                rt not in ("", "unknown", "Any", "Obj", "object")
                and arg_kind in ("Name", "Attribute", "Subscript")
                and arg_resolved_type == rt
            ):
                return _emit_expr_as_type(ctx, a0, rt)
            arg_type = _expanded_union_type(_str(a0_dict, "resolved_type"))
            storage_type = _expanded_union_type(_expr_storage_type(ctx, a0))
            if _optional_inner_type(storage_type) == rt:
                if arg_kind == "Unbox":
                    return arg_strs[0]
                storage_expr = arg_strs[0]
                if arg_kind == "Name":
                    storage_expr = _emit_name_storage(a0_dict)
                return "(*(" + storage_expr + "))"
            if _is_top_level_union_type(storage_type):
                return _emit_union_get_expr(arg_strs[0], storage_type, rt)
            if _is_top_level_union_type(arg_type):
                return _emit_union_get_expr(arg_strs[0], arg_type, rt)
            if arg_kind == "Unbox" and arg_type in ("Obj", "Any", "object", "unknown"):
                if rt in ("int", "int64"):
                    return _emit_object_unbox(arg_strs[0], "int64")
                if rt in ("float", "float64"):
                    return _emit_object_unbox(arg_strs[0], "float64")
                if rt == "bool":
                    return _emit_object_unbox(arg_strs[0], "bool")
            if arg_kind != "Unbox" and storage_type not in ("", "unknown") and _needs_object_cast(storage_type):
                if rt in ("int", "int64"):
                    return _emit_object_unbox(arg_strs[0], "int64")
                if rt in ("float", "float64"):
                    return _emit_object_unbox(arg_strs[0], "float64")
                if rt == "bool":
                    return _emit_object_unbox(arg_strs[0], "bool")
        if len(arg_strs) >= 1: return "static_cast<" + ct + ">(" + arg_strs[0] + ")"
        return ct + "()"
    if rc in ("py_to_string", "str") and len(arg_strs) >= 1:
        if len(args) >= 1 and a0_obj is not None and _str(a0_dict, "resolved_type") == "str":
            arg_kind = _str(a0_dict, "kind")
            if arg_kind in ("Name", "Attribute", "Subscript"):
                return _emit_expr_as_type(ctx, a0, "str")
            storage_type = _expanded_union_type(_expr_storage_type(ctx, a0))
            if arg_kind != "Unbox" and storage_type not in ("", "unknown") and _needs_object_cast(storage_type):
                return _emit_object_unbox(arg_strs[0], "str")
            return arg_strs[0]
        if len(args) >= 1 and a0_obj is not None:
            arg_kind = _str(a0_dict, "kind")
            if arg_kind == "Box":
                boxed_value: JsonVal = a0_dict.get("value")
                boxed_value_obj = json.JsonValue(boxed_value).as_obj()
                if boxed_value_obj is not None:
                    return "str(py_to_string(" + _emit_expr(ctx, boxed_value) + "))"
            arg_type = _expanded_union_type(_str(a0_dict, "resolved_type"))
            storage_type = _expanded_union_type(_expr_storage_type(ctx, a0))
            if _optional_inner_type(storage_type) == "str":
                return "str(py_to_string((*(" + arg_strs[0] + "))))"
            if _union_effectively_single_type(storage_type, "str"):
                str_lane_type = "str"
                lane = _select_union_lane(storage_type, str_lane_type)
                if lane != "":
                    str_lane_type = "str"
                    return _emit_union_get_expr(arg_strs[0], storage_type, str_lane_type)
            if _union_effectively_single_type(arg_type, "str"):
                str_lane_type = "str"
                lane = _select_union_lane(arg_type, str_lane_type)
                if lane != "":
                    str_lane_type = "str"
                    return _emit_union_get_expr(arg_strs[0], arg_type, str_lane_type)
            if arg_kind == "Unbox":
                unbox_value: JsonVal = a0_dict.get("value")
                unbox_storage_type = _expr_storage_type(ctx, unbox_value)
                unbox_value_obj = json.JsonValue(unbox_value).as_obj()
                if unbox_value_obj is not None and _str(unbox_value_obj.raw, "kind") == "Name":
                    unbox_value_expr = _emit_name_storage(unbox_value_obj.raw)
                else:
                    unbox_value_expr = _emit_expr(ctx, unbox_value)
                if unbox_storage_type not in ("", "unknown") and not _needs_object_cast(unbox_storage_type):
                    return "str(py_to_string(" + unbox_value_expr + "))"
            if arg_kind == "Unbox" and arg_type in ("Obj", "Any", "object", "unknown"):
                unbox_value: JsonVal = a0_dict.get("value")
                unbox_value_obj = json.JsonValue(unbox_value).as_obj()
                if unbox_value_obj is not None and _str(unbox_value_obj.raw, "kind") == "Name":
                    unbox_value_expr = _emit_name_storage(unbox_value_obj.raw)
                else:
                    unbox_value_expr = _emit_expr(ctx, unbox_value)
                return "str(py_to_string(" + unbox_value_expr + "))"
        return "str(py_to_string(" + arg_strs[0] + "))"
    if rc in ("bytearray_ctor", "bytes_ctor"):
        if len(args) >= 1 and a0_obj is not None:
            a0_kind = _str(a0_dict, "kind")
            a0_rt = _str(a0_dict, "resolved_type")
            if a0_kind == "List":
                elems = _list(a0_dict, "elements")
                parts = ["uint8(" + _emit_expr(ctx, e) + ")" for e in elems]
                return "bytes{" + ", ".join(parts) + "}"
            if a0_rt in ("int64", "int32", "int", "uint8", "int8"):
                return "bytes(" + arg_strs[0] + ")"
        if len(arg_strs) >= 1:
            return "bytes(" + arg_strs[0] + ")"
        return "bytes{}"
    adapter_policy = ctx.mapping.call_adapters.get(rc, "")
    if adapter_policy == "multi_arg_print" and len(arg_strs) >= 1:
        return rc + "(" + ", ".join(arg_strs) + ")"
    if adapter_policy == "ref_arg" and len(arg_strs) >= 1:
        return rc + "(" + ", ".join(arg_strs) + ")"
    # Container constructor builtins: list(), dict(), set()
    if rc == "list_ctor":
        rt = _str(node, "resolved_type")
        if len(args) >= 1 and rt.startswith("list[") and rt.endswith("]"):
            return "rc_from_value(" + _emit_expr_as_type(ctx, args[0], rt) + ")"
        if rt.startswith("list[") and rt.endswith("]"):
            inner_type = rt[5:-1]
            inner: str = _selfhost_cpp_signature_type(inner_type)
            return "rc_list_new<" + inner + ">()"
        return "rc_list_new<object>()"
    if rc == "set_ctor":
        rt = _str(node, "resolved_type")
        if rt.startswith("set[") and rt.endswith("]"):
            inner_type = rt[4:-1]
            inner: str = _selfhost_cpp_signature_type(inner_type)
            return "rc_from_value(set<" + inner + ">{})"
        return "rc_set_new<object>()"
    if rc == "dict_ctor":
        rt = _str(node, "resolved_type")
        if rt.startswith("dict[") and rt.endswith("]"):
            dparts = _container_type_args(rt)
            if len(dparts) == 2:
                k = _selfhost_cpp_signature_type(dparts[0])
                v = _selfhost_cpp_signature_type(dparts[1])
                return "rc_dict_new<" + k + ", " + v + ">()"
        return "rc_dict_new<str, object>()"
    if rc == "std::runtime_error":
        if len(arg_strs) >= 1: return "throw std::runtime_error(" + arg_strs[0] + ")"
        return 'throw std::runtime_error("error")'
    if rc in ("py_write_text", "pathlib.write_text"):
        if func_obj is not None:
            owner_value: JsonVal = func_dict.get("value")
            owner = _emit_expr(ctx, owner_value)
            if len(arg_strs) >= 1: return "py_pathlib_write_text(" + owner + ", " + arg_strs[0] + ")"

    # Mapping resolution
    adapter = _str(node, "runtime_call_adapter_kind")
    resolved = _resolve_runtime_call_local(rc, "", adapter, ctx.mapping)
    if resolved != "":
        return _wrap_container_result_if_needed(node, resolved + "(" + ", ".join(call_arg_strs) + ")")
    if rc != "":
        if "." in rc:
            if func_is_attr:
                owner_node: JsonVal = func_dict.get("value")
                owner = _emit_expr(ctx, owner_node)
                attr = _str(func_dict, "attr")
                member_sep = "->" if _uses_ref_container_storage(ctx, owner_node) else "."
                return owner + member_sep + _safe_cpp_ident(attr) + "(" + ", ".join(arg_strs) + ")"
            _emit_fail(ctx, "unmapped_runtime_call", rc)
        return ctx.mapping.builtin_prefix + rc + "(" + ", ".join(call_arg_strs) + ")"
    _emit_fail(ctx, "unknown_builtin", repr(node))


def _emit_expr_with_forced_literal_type(ctx: CppEmitContext, node: JsonVal, target_type: str) -> str:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return _emit_expr(ctx, node)
    node_dict = node_obj.raw
    if _str(node_dict, "kind") == "Constant":
        value: JsonVal = node_dict.get("value")
        bool_value = json.JsonValue(value).as_bool()
        int_value = json.JsonValue(value).as_int()
        if int_value is not None and bool_value is None:
            if target_type in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
                target_copy = target_type + ""
                return cpp_signature_type(target_copy) + "(" + str(int_value) + ")"
    return _emit_expr(ctx, node)


def _emit_attribute(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    owner_node: JsonVal = node.get("value")
    owner_obj = json.JsonValue(owner_node).as_obj()
    owner_dict: dict[str, JsonVal] = {}
    if owner_obj is not None:
        owner_dict = owner_obj.raw
    attr = _str(node, "attr")
    # Specialize type(v).__name__ → string literal when type is statically known
    if attr == "__name__" and owner_obj is not None:
        if _str(owner_dict, "kind") == "Call":
            func: JsonVal = owner_dict.get("func")
            args_value: JsonVal = owner_dict.get("args")
            func_obj = json.JsonValue(func).as_obj()
            args_arr = json.JsonValue(args_value).as_arr()
            if func_obj is not None and _str(func_obj.raw, "id") == "type" and args_arr is not None and len(args_arr.raw) == 1:
                arg0 = args_arr.raw[0]
                arg0_obj = json.JsonValue(arg0).as_obj()
                arg_type = _str(arg0_obj.raw, "resolved_type") if arg0_obj is not None else ""
                if arg_type not in ("", "unknown"):
                    bare = arg_type.split(".")[-1]
                    return 'str("' + bare + '")'
    owner = _emit_expr(ctx, owner_node)
    access_kind = _str(node, "attribute_access_kind")
    owner_id = _str(owner_dict, "id") if owner_obj is not None else ""
    runtime_module_id = _str(node, "runtime_module_id")
    runtime_symbol = _str(node, "runtime_symbol")
    runtime_symbol_dispatch = _str(node, "runtime_symbol_dispatch")
    owner_module = ctx.import_aliases.get(owner_id, "")
    has_class_var = False
    if owner_id != "":
        for class_owner, class_var_map in ctx.class_vars.items():
            if class_owner == owner_id:
                for class_attr, _class_var_spec_value in class_var_map.items():
                    if class_attr == attr:
                        has_class_var = True
    if has_class_var:
        return owner_id + "_" + attr
    if _is_type_owner(ctx, owner_node):
        return owner + "::" + attr
    if owner_module != "":
        return _resolve_runtime_attr_symbol(
            ctx,
            runtime_module_id=runtime_module_id if runtime_module_id != "" else owner_module,
            resolved_runtime_call=_str(node, "resolved_runtime_call"),
            runtime_call=_str(node, "runtime_call"),
            runtime_symbol=runtime_symbol,
            fallback_symbol=attr,
        )
    if runtime_symbol_dispatch == "value" and runtime_module_id != "":
        return _resolve_runtime_attr_symbol(
            ctx,
            runtime_module_id=runtime_module_id,
            resolved_runtime_call=_str(node, "resolved_runtime_call"),
            runtime_call=_str(node, "runtime_call"),
            runtime_symbol=runtime_symbol,
            fallback_symbol=attr,
        )
    if (
        runtime_module_id != ""
        and should_skip_module(runtime_module_id, ctx.mapping)
        and runtime_symbol_dispatch == "value"
    ):
        if runtime_symbol == "":
            runtime_symbol = attr
        return _resolve_runtime_symbol_name_local(
            runtime_symbol,
            ctx.mapping,
            runtime_module_id,
            _str(node, "resolved_runtime_call"),
            _str(node, "runtime_call"),
        )
    if owner == "this":
        expr = "this->" + attr
        return expr + "()" if access_kind == "property_getter" else expr
    member_sep = "->" if _uses_ref_container_storage(ctx, owner_node) else "."
    expr = owner + member_sep + attr
    return expr + "()" if access_kind == "property_getter" else expr


def _class_var_spec(ctx: CppEmitContext, node: JsonVal) -> dict[str, JsonVal] | None:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return None
    node_dict = node_obj.raw
    if _str(node_dict, "kind") != "Attribute":
        return None
    owner_node: JsonVal = node_dict.get("value")
    owner_obj = json.JsonValue(owner_node).as_obj()
    if owner_obj is None:
        return None
    owner_id = _str(owner_obj.raw, "id")
    attr = _str(node_dict, "attr")
    if owner_id == "" or attr == "":
        return None
    for class_owner, class_var_map in ctx.class_vars.items():
        if class_owner == owner_id:
            for class_attr, spec in class_var_map.items():
                if class_attr == attr:
                    return spec
    return None


def _emit_subscript_index(ctx: CppEmitContext, value: str, slice_node: JsonVal) -> str:
    idx = _emit_expr(ctx, slice_node)
    size_expr = "py_len(" + value + ")"
    slice_obj = json.JsonValue(slice_node).as_obj()
    if slice_obj is not None and _str(slice_obj.raw, "kind") == "Constant":
        iv = json.JsonValue(slice_obj.raw.get("value")).as_int()
        if iv is not None and iv < 0:
            return "(" + size_expr + str(iv) + ")"
    if slice_obj is not None and _str(slice_obj.raw, "kind") == "UnaryOp" and _str(slice_obj.raw, "op") == "USub":
        operand_node: JsonVal = slice_obj.raw.get("operand")
        operand = _emit_expr(ctx, operand_node)
        return "(" + size_expr + " - " + operand + ")"
    return idx


def _subscript_access_hint(node: dict[str, JsonVal]) -> dict[str, JsonVal] | None:
    meta_obj = node.get("meta")
    meta_value = json.JsonValue(meta_obj).as_obj()
    if meta_value is None:
        return None
    hint_value = json.JsonValue(meta_value.raw.get("subscript_access_v1")).as_obj()
    if hint_value is None:
        return None
    hint = hint_value.raw
    if _str(hint, "schema_version") != "subscript_access_v1":
        return None
    negative_index = _str(hint, "negative_index")
    bounds_check = _str(hint, "bounds_check")
    if negative_index not in ("normalize", "skip"):
        return None
    if bounds_check not in ("full", "off"):
        return None
    out: dict[str, JsonVal] = {}
    for key, value in hint.items():
        out[key] = value
    return out


def _emit_direct_subscript_index(ctx: CppEmitContext, value: str, slice_node: JsonVal, negative_index: str) -> str:
    raw_idx = _emit_expr(ctx, slice_node)
    if negative_index != "normalize":
        return raw_idx
    slice_obj = json.JsonValue(slice_node).as_obj()
    if slice_obj is not None:
        slice_dict = slice_obj.raw
        kind = _str(slice_dict, "kind")
        if kind == "Constant":
            iv_value: JsonVal = slice_dict.get("value")
            iv = json.JsonValue(iv_value).as_int()
            iv_bool = json.JsonValue(iv_value).as_bool()
            if iv is not None and iv_bool is None and iv < 0:
                return _emit_subscript_index(ctx, value, slice_node)
        if kind == "UnaryOp" and _str(slice_dict, "op") == "USub":
            return _emit_subscript_index(ctx, value, slice_node)
    size_expr = "py_len(" + value + ")"
    return "((" + raw_idx + ") < 0 ? (" + size_expr + " + (" + raw_idx + ")) : (" + raw_idx + "))"


def _emit_direct_container_subscript(
    ctx: CppEmitContext,
    value: str,
    value_node: JsonVal,
    idx: str,
) -> str:
    base = value
    if _uses_ref_container_storage(ctx, value_node):
        base = "(*(" + value + "))"
    return base + "[static_cast<::std::size_t>(" + idx + ")]"


def _emit_subscript(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = _emit_expr(ctx, node.get("value"))
    sl: JsonVal = node.get("slice")
    sl_obj = json.JsonValue(sl).as_obj()
    sl_dict: dict[str, JsonVal] = {}
    if sl_obj is not None:
        sl_dict = sl_obj.raw
    value_node: JsonVal = node.get("value")
    value_obj = json.JsonValue(value_node).as_obj()
    value_dict: dict[str, JsonVal] = {}
    if value_obj is not None:
        value_dict = value_obj.raw
    value_type = _str(value_dict, "resolved_type") if value_obj is not None else ""
    storage_type = _expr_storage_type(ctx, value_node)
    if (value_type in ("", "unknown", "tuple", "list", "dict", "set") or value_type == storage_type) and storage_type != "":
        value_type = storage_type
    value_type = _selfhost_normalize_cpp_container_alias(value_type)
    class_var_spec = _class_var_spec(ctx, value_node)
    if class_var_spec is not None and value_type in ("", "unknown", "tuple", "list", "dict", "set"):
        spec_type = _str(class_var_spec, "type")
        if spec_type != "":
            value_type = spec_type
    if sl_obj is not None and _str(sl_dict, "kind") == "Slice":
        return _emit_slice_expr(ctx, node, value, sl_dict)
    if sl_obj is not None and _str(sl_dict, "kind") == "Constant":
        iv = json.JsonValue(sl_dict.get("value")).as_int()
        if iv is not None and iv >= 0:
            if value_type.startswith("tuple["):
                return "::std::get<" + str(iv) + ">(" + value + ")"
            if value_obj is not None and _str(value_dict, "kind") == "Name" and _str(value_dict, "id").startswith("__tuple_unpack_"):
                return "::std::get<" + str(iv) + ">(" + value + ")"
    if value_type == "str":
        raw_idx = _emit_expr(ctx, sl)
        return value + "[" + raw_idx + "]"
    idx = _emit_subscript_index(ctx, value, sl)
    if value_type.startswith("list[") or value_type in ("bytes", "bytearray"):
        hint = _subscript_access_hint(node)
        if hint is not None and _str(hint, "bounds_check") == "off":
            direct_idx = _emit_direct_subscript_index(ctx, value, sl, _str(hint, "negative_index"))
            return _emit_direct_container_subscript(ctx, value, value_node, direct_idx)
        return "py_list_at_ref(" + value + ", " + idx + ")"
    if value_type.startswith("dict["):
        return "py_at(" + value + ", " + idx + ")"
    return value + "[" + idx + "]"


def _emit_subscript_store_target(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = _emit_expr(ctx, node.get("value"))
    sl = node.get("slice")
    value_node = node.get("value")
    value_type = _selfhost_normalize_cpp_container_alias(_effective_resolved_type(value_node))
    class_var_spec = _class_var_spec(ctx, value_node)
    if class_var_spec is not None and value_type in ("", "unknown", "tuple", "list", "dict", "set"):
        spec_type = _str(class_var_spec, "type")
        if spec_type != "":
            value_type = spec_type
    idx = _emit_subscript_index(ctx, value, sl)
    if value_type.startswith("list[") or value_type in ("bytes", "bytearray"):
        hint = _subscript_access_hint(node)
        if hint is not None and _str(hint, "bounds_check") == "off":
            direct_idx = _emit_direct_subscript_index(ctx, value, sl, _str(hint, "negative_index"))
            return _emit_direct_container_subscript(ctx, value, value_node, direct_idx)
        return "py_list_at_ref(" + value + ", " + idx + ")"
    if value_type.startswith("dict["):
        if _uses_ref_container_storage(ctx, value_node):
            return "(*(" + value + "))[" + idx + "]"
        return "(" + value + ")[" + idx + "]"
    return value + "[" + idx + "]"


def _emit_list_literal(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    rt = _str(node, "resolved_type")
    parts = [_emit_expr(ctx, e) for e in elements]
    plain_ct = cpp_type(rt, prefer_value_container=True)
    literal = plain_ct + "{" + ", ".join(parts) + "}"
    return _wrap_container_value_expr(rt, literal) if is_container_resolved_type(rt) else literal


def _emit_dict_literal(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    entries = _list(node, "entries")
    if len(entries) == 0 and rt in ("", "unknown", "dict[unknown,unknown]"):
        return "rc_from_value(dict<str, object>{})"
    plain_ct = cpp_type(rt, prefer_value_container=True)
    if len(entries) > 0:
        parts: list[str] = []
        for e in entries:
            e_obj = json.JsonValue(e).as_obj()
            if e_obj is not None:
                entry = e_obj.raw
                key_node: JsonVal = entry.get("key")
                value_node: JsonVal = entry.get("value")
                parts.append(plain_ct + "::value_type{" + _emit_expr(ctx, key_node) + ", " + _emit_expr(ctx, value_node) + "}")
        literal = plain_ct + "{" + ", ".join(parts) + "}"
        return _wrap_container_value_expr(rt, literal) if is_container_resolved_type(rt) else literal
    literal = plain_ct + "{}"
    return _wrap_container_value_expr(rt, literal) if is_container_resolved_type(rt) else literal


def _emit_set_literal(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    plain_ct = cpp_type(rt, prefer_value_container=True)
    elements = _list(node, "elements")
    parts = [_emit_expr(ctx, e) for e in elements]
    literal = plain_ct + "{" + ", ".join(parts) + "}"
    return _wrap_container_value_expr(rt, literal) if is_container_resolved_type(rt) else literal


def _emit_tuple_literal(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    parts = [_emit_expr(ctx, e) for e in elements]
    return "std::make_tuple(" + ", ".join(parts) + ")"


def _is_python_type_alias_expr(node: JsonVal) -> bool:
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        return False
    node_dict = node_obj.raw
    if _str(node_dict, "kind") != "Subscript":
        return False
    base = node_dict.get("value")
    base_obj = json.JsonValue(base).as_obj()
    if base_obj is None:
        return False
    base_id = _str(base_obj.raw, "id")
    return base_id in {
        "Union",
        "Optional",
        "dict",
        "list",
        "set",
        "tuple",
        "Callable",
        "TypeVar",
        "TypeAlias",
        "Literal",
        "ClassVar",
        "Final",
        "Annotated",
        "Protocol",
    }


def _emit_range_expr(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    result_value_type = cpp_type(rt, prefer_value_container=True)
    start = node.get("start")
    stop = node.get("stop")
    step = node.get("step")
    start_code = "0"
    if json.JsonValue(start).as_obj() is not None:
        start_code = _emit_expr(ctx, start)
    stop_code = "0"
    if json.JsonValue(stop).as_obj() is not None:
        stop_code = _emit_expr(ctx, stop)
    step_code = "1"
    if json.JsonValue(step).as_obj() is not None:
        step_code = _emit_expr(ctx, step)
    mode = _str(node, "range_mode")
    if mode == "":
        mode = "dynamic"
    cond = (
        "__range_i < (" + stop_code + ")"
        if mode == "ascending"
        else (
            "__range_i > (" + stop_code + ")"
            if mode == "descending"
            else "((" + step_code + ") > 0 ? __range_i < (" + stop_code + ") : __range_i > (" + stop_code + "))"
        )
    )
    value_expr = (
        "([&]() -> " + result_value_type + " { "
        + result_value_type + " __range_out{}; "
        + "for (int64 __range_i = " + start_code + "; " + cond + "; __range_i += (" + step_code + ")) { "
        + "__range_out.push_back(__range_i); "
        + "} "
        + "return __range_out; "
        + "})()"
    )
    return _wrap_container_value_expr(rt, value_expr) if is_container_resolved_type(rt) else value_expr


def _emit_list_comp(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    return _emit_comp_lambda(ctx, node, "list")


def _emit_set_comp(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    return _emit_comp_lambda(ctx, node, "set")


def _emit_dict_comp(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    return _emit_comp_lambda(ctx, node, "dict")


def _emit_comp_lambda(ctx: CppEmitContext, node: dict[str, JsonVal], comp_kind: str) -> str:
    resolved_type = _str(node, "resolved_type")
    result_type = cpp_signature_type(resolved_type)
    generators = _list(node, "generators")
    elt = node.get("elt")
    key = node.get("key")
    value = node.get("value")
    lines: list[str] = []

    saved_var_types = dict(ctx.var_types)
    saved_value_container_vars = set(ctx.value_container_vars)
    saved_visible_scopes = [set(scope) for scope in ctx.visible_local_scopes]
    _push_local_scope(ctx)

    def _pad(depth: int) -> str:
        return "    " * depth

    depth = 1
    lines.append("([&]() -> " + result_type + " {")
    init_expr = _wrap_container_value_expr(resolved_type, cpp_type(resolved_type, prefer_value_container=True) + "{}")
    lines.append(_pad(depth) + result_type + " __comp_result = " + init_expr + ";")

    for gen in generators:
        gen_obj = json.JsonValue(gen).as_obj()
        if gen_obj is None:
            continue
        gen_dict = gen_obj.raw
        target: JsonVal = gen_dict.get("target")
        target_obj = json.JsonValue(target).as_obj()
        target_dict: dict[str, JsonVal] = {}
        if target_obj is not None:
            target_dict = target_obj.raw
        iter_expr = gen_dict.get("iter")
        ifs = _list(gen_dict, "ifs")
        target_kind = _str(target_dict, "kind") if target_obj is not None else ""
        iter_code = _emit_expr(ctx, iter_expr)
        iter_rt = _effective_resolved_type(iter_expr)

        if target_kind == "Tuple" and target_obj is not None:
            item_name = _next_temp(ctx, "__comp_item")
            lines.append(_pad(depth) + "for (auto " + item_name + " : " + iter_code + ") {")
            depth += 1
            tuple_type = ""
            if iter_rt.startswith("list[") and iter_rt.endswith("]"):
                tuple_type = iter_rt[5:-1]
            elif iter_rt.startswith("set[") and iter_rt.endswith("]"):
                tuple_type = iter_rt[4:-1]
            elems = _list(target_dict, "elements")
            for index in range(len(elems)):
                elem = elems[index]
                elem_obj = json.JsonValue(elem).as_obj()
                if elem_obj is None:
                    continue
                elem_dict = elem_obj.raw
                elem_name = _str(elem_dict, "id")
                if elem_name in ("", "_"):
                    continue
                elem_type = _effective_resolved_type(elem)
                elem_expr = item_name + "[" + str(index) + "]"
                if tuple_type.startswith("tuple["):
                    elem_expr = "::std::get<" + str(index) + ">(" + item_name + ")"
                elem_decl = _decl_cpp_type(ctx, elem_type, elem_name) if elem_type not in ("", "unknown") else "auto"
                lines.append(_pad(depth) + elem_decl + " " + elem_name + " = " + elem_expr + ";")
                _register_local_storage(ctx, elem_name, elem_type)
                _declare_local_visible(ctx, elem_name)
        else:
            target_name = "_"
            if target_obj is not None and target_kind == "Name":
                target_name = _str(target_dict, "id")
            lines.append(_pad(depth) + "for (auto " + target_name + " : " + iter_code + ") {")
            depth += 1
            if target_name != "_":
                target_type = _effective_resolved_type(target)
                _register_local_storage(ctx, target_name, target_type)
                _declare_local_visible(ctx, target_name)

        for if_node in ifs:
            if json.JsonValue(if_node).as_obj() is None:
                continue
            lines.append(_pad(depth) + "if (" + _emit_expr(ctx, if_node) + ") {")
            depth += 1

    if comp_kind == "dict":
        lines.append(_pad(depth) + "(*(__comp_result))[" + _emit_expr(ctx, key) + "] = " + _emit_expr(ctx, value) + ";")
    elif comp_kind == "set":
        lines.append(_pad(depth) + "py_set_add_mut(__comp_result, " + _emit_expr(ctx, elt) + ");")
    else:
        lines.append(_pad(depth) + "py_list_append_mut(__comp_result, " + _emit_expr(ctx, elt) + ");")

    for gen in generators:
        gen_obj = json.JsonValue(gen).as_obj()
        if gen_obj is None:
            continue
        gen_dict = gen_obj.raw
        for _ in _list(gen_dict, "ifs"):
            depth -= 1
            lines.append(_pad(depth) + "}")
        depth -= 1
        lines.append(_pad(depth) + "}")

    lines.append(_pad(1) + "return __comp_result;")
    lines.append("}())")

    ctx.var_types = saved_var_types
    ctx.value_container_vars = saved_value_container_vars
    ctx.visible_local_scopes = saved_visible_scopes
    return "\n".join(lines)


def _emit_covariant_copy(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    source_expr = _emit_expr(ctx, node.get("source"))
    target_type = _str(node, "target_type")
    source_type = _effective_resolved_type(node.get("source"))
    source_elem_type = _str(node, "source_elem_type")
    target_elem_type = _str(node, "target_elem_type")
    plain_ct = cpp_type(target_type, prefer_value_container=True)
    out_name = _next_temp(ctx, "__cov")
    val_name = _next_temp(ctx, "__item")
    key_name = _next_temp(ctx, "__key")
    push_expr = val_name
    if target_elem_type not in ("", "unknown", "Any", "JsonVal", "object", "Obj"):
        if target_elem_type != source_elem_type:
            val_node: dict[str, JsonVal] = {}
            val_node["kind"] = "Name"
            val_node["id"] = val_name
            val_node["resolved_type"] = source_elem_type if source_elem_type != "" else target_elem_type
            val_json: JsonVal = val_node
            push_expr = _emit_expr_as_type(
                ctx,
                val_json,
                target_elem_type,
            )
    if target_type.startswith("dict[") and source_type.startswith("dict["):
        source_parts = _container_type_args(source_type)
        target_parts = _container_type_args(target_type)
        source_key_type = source_parts[0] if len(source_parts) == 2 else ""
        target_key_type = target_parts[0] if len(target_parts) == 2 else ""
        key_expr = key_name
        if target_key_type not in ("", "unknown", source_key_type):
            key_node: dict[str, JsonVal] = {}
            key_node["kind"] = "Name"
            key_node["id"] = key_name
            key_node["resolved_type"] = source_key_type if source_key_type != "" else target_key_type
            key_json: JsonVal = key_node
            key_expr = _emit_expr_as_type(
                ctx,
                key_json,
                target_key_type,
            )
        return (
            "([&]() {\n"
            + "    " + plain_ct + " " + out_name + ";\n"
            + "    for (auto const& [" + key_name + ", " + val_name + "] : " + source_expr + ") {\n"
            + "        " + out_name + "[" + key_expr + "] = " + push_expr + ";\n"
            + "    }\n"
            + "    return " + _wrap_container_value_expr(target_type, out_name) + ";\n"
            + "}())"
        )
    append_stmt = out_name + ".push_back(" + push_expr + ");"
    if target_type.startswith("set["):
        append_stmt = "py_set_add_mut(" + out_name + ", " + push_expr + ");"
    return (
        "([&]() {\n"
        + "    " + plain_ct + " " + out_name + ";\n"
        + "    for (auto const& " + val_name + " : " + source_expr + ") {\n"
        + "        " + append_stmt + "\n"
        + "    }\n"
        + "    return " + _wrap_container_value_expr(target_type, out_name) + ";\n"
        + "}())"
    )


def _emit_covariant_copy_expr(
    ctx: CppEmitContext,
    *,
    source_expr: str,
    source_type: str,
    target_type: str,
) -> str:
    source_elem_type = ""
    target_elem_type = ""
    source_parts = _container_type_args(source_type)
    target_parts = _container_type_args(target_type)
    if len(source_parts) > 0:
        source_elem_type = source_parts[-1]
    if len(target_parts) > 0:
        target_elem_type = target_parts[-1]
    target_type_arg = target_type + ""
    plain_ct = cpp_type(target_type_arg, prefer_value_container=True)
    out_name = _next_temp(ctx, "__cov")
    val_name = _next_temp(ctx, "__item")
    key_name = _next_temp(ctx, "__key")
    push_expr = val_name
    if target_elem_type not in ("", "unknown", "Any", "JsonVal", "object", "Obj"):
        if target_elem_type != source_elem_type:
            val_node: dict[str, JsonVal] = {}
            val_node["kind"] = "Name"
            val_node["id"] = val_name
            val_node["resolved_type"] = source_elem_type if source_elem_type != "" else target_elem_type
            val_json: JsonVal = val_node
            push_expr = _emit_expr_as_type(
                ctx,
                val_json,
                target_elem_type,
            )
    if target_type.startswith("dict[") and source_type.startswith("dict["):
        source_key_type = source_parts[0] if len(source_parts) == 2 else ""
        target_key_type = target_parts[0] if len(target_parts) == 2 else ""
        key_expr = key_name
        if target_key_type not in ("", "unknown", source_key_type):
            key_node: dict[str, JsonVal] = {}
            key_node["kind"] = "Name"
            key_node["id"] = key_name
            key_node["resolved_type"] = source_key_type if source_key_type != "" else target_key_type
            key_json: JsonVal = key_node
            key_expr = _emit_expr_as_type(
                ctx,
                key_json,
                target_key_type,
            )
        return (
            "([&]() {\n"
            + "    " + plain_ct + " " + out_name + ";\n"
            + "    for (auto const& [" + key_name + ", " + val_name + "] : " + source_expr + ") {\n"
            + "        " + out_name + "[" + key_expr + "] = " + push_expr + ";\n"
            + "    }\n"
            + "    return " + _wrap_container_value_expr(target_type, out_name) + ";\n"
            + "}())"
        )
    append_stmt = out_name + ".push_back(" + push_expr + ");"
    if target_type.startswith("set["):
        append_stmt = "py_set_add_mut(" + out_name + ", " + push_expr + ");"
    return (
        "([&]() {\n"
        + "    " + plain_ct + " " + out_name + ";\n"
        + "    for (auto const& " + val_name + " : " + source_expr + ") {\n"
        + "        " + append_stmt + "\n"
        + "    }\n"
        + "    return " + _wrap_container_value_expr(target_type, out_name) + ";\n"
        + "}())"
    )


def _emit_unbox(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    normalized = _normalize_cpp_boundary_expr(ctx, node)
    normalized_obj = json.JsonValue(normalized).as_obj()
    if normalized_obj is not None:
        node = normalized_obj.raw
    value = node.get("value")
    value_obj = json.JsonValue(value).as_obj()
    value_dict: dict[str, JsonVal] = {}
    if value_obj is not None:
        value_dict = value_obj.raw
    target = _str(node, "target")
    if target == "":
        target = _str(node, "resolved_type")
    target_mirror = _node_type_mirror(node)
    if target_mirror != "":
        target = target_mirror
    if target not in ("", "object") and value_obj is not None and _str(value_dict, "kind") == "Box":
        boxed_value = value_dict.get("value")
        boxed_value_obj = json.JsonValue(boxed_value).as_obj()
        if boxed_value_obj is not None:
            boxed_node: JsonVal = boxed_value_obj.raw
            return _emit_expr_as_type(ctx, boxed_node, target)
    if value_obj is not None and _str(value_dict, "kind") == "Name":
        value_expr = _emit_name_storage(value_dict)
    else:
        value_expr = _emit_expr(ctx, value)
    value_type = _effective_resolved_type(value)
    storage_type = _expr_storage_type(ctx, value)
    union_value_type = _expanded_union_type(value_type)
    union_storage_type = _expanded_union_type(storage_type)
    if target == "" or target == "object":
        return value_expr
    bridge = _dict(node, "bridge_lane_v1")
    if _str(bridge, "value_category") == "optional":
        if _is_top_level_union_type(target):
            bridge_value = _dict(bridge, "value")
            source_type = _str(bridge_value, "mirror")
            if source_type == "":
                source_type = _expanded_union_type(_expr_storage_type(ctx, value))
            if source_type == "":
                source_type = _expanded_union_type(_effective_resolved_type(value))
            if source_type != "":
                return _emit_union_narrow_expr(value_expr, source_type, target)
        return "(*(" + value_expr + "))"
    if _str(bridge, "value_category") == "general_union":
        bridge_value = _dict(bridge, "value")
        source_type = _str(bridge_value, "mirror")
        if source_type != "":
            lane_expr = _emit_union_get_expr(value_expr, source_type, target)
            if lane_expr != value_expr:
                return lane_expr
    if _type_uses_callable(target):
        optional_callable_inner = _optional_inner_type(union_storage_type)
        if optional_callable_inner != "" and _type_uses_callable(optional_callable_inner):
            return "(*(" + value_expr + "))"
        if _type_uses_callable(union_storage_type):
            return value_expr
        if _type_uses_callable(union_value_type):
            return value_expr
    if _optional_inner_type(union_storage_type) == target:
        return "(*(" + value_expr + "))"
    if _has_variant_storage(storage_type) or _is_top_level_union_type(union_storage_type):
        lane_expr = _emit_union_get_expr(value_expr, union_storage_type, target)
        if lane_expr != value_expr:
            return lane_expr
    if _is_top_level_union_type(union_value_type):
        lane_expr = _emit_union_get_expr(value_expr, union_value_type, target)
        if lane_expr != value_expr:
            return lane_expr
    if (
        target == "str"
        and union_storage_type not in ("", "unknown")
        and not _needs_object_cast(union_storage_type)
    ):
        return "str(py_to_string(" + value_expr + "))"
    storage_requires_runtime_unbox = (
        union_storage_type not in ("", "unknown")
        and union_storage_type != target
        and (
            _needs_object_cast(union_storage_type)
            or _optional_inner_type(union_storage_type) != ""
        )
    )
    value_cpp = cpp_signature_type(value_type) if value_type not in ("", "unknown") else ""
    storage_cpp = cpp_signature_type(storage_type) if storage_type not in ("", "unknown") else ""
    target_cpp = cpp_signature_type(target)
    lane_prefix = "::std::get<" + target_cpp + ">("
    if lane_prefix in value_expr:
        return value_expr
    if not storage_requires_runtime_unbox and value_cpp != "" and value_cpp == target_cpp:
        return value_expr
    if storage_cpp != "" and storage_cpp == target_cpp:
        return value_expr
    needs_runtime_unbox = (
        storage_requires_runtime_unbox
        or (_needs_object_cast(union_storage_type) and union_storage_type != target)
        or (_needs_object_cast(union_value_type) and union_value_type != target)
    )
    if not needs_runtime_unbox and value_type == target:
        return value_expr
    if _attribute_static_type(ctx, value) == target:
        return value_expr
    if value_obj is not None and _str(value_dict, "kind") == "Call":
        func = value_dict.get("func")
        func_obj = json.JsonValue(func).as_obj()
        func_name = _str(func_obj.raw, "id") if func_obj is not None else ""
        if func_name in (
            "linked_module_id",
            "linked_module_source_path",
            "linked_module_east_doc",
            "linked_module_kind",
            "lower_east2_to_east3",
            "optimize_east3_doc_only",
            "write_runtime_module_artifacts",
            "write_helper_module_artifacts",
            "write_user_module_artifacts",
        ):
            return value_expr
    if target in ctx.class_names:
        return "(*(" + value_expr + ").as<" + target + ">())"
    if target in ("str", "int", "int64", "float", "float64", "bool"):
        return _emit_object_unbox(value_expr, target)
    if (
        target.startswith("list[")
        or target.startswith("dict[")
        or target.startswith("set[")
    ):
        return "(" + value_expr + ").as<" + cpp_container_value_type(target) + ">()"
    if target.startswith("tuple[") or target in ("bytes", "bytearray"):
        return "(*(" + value_expr + ").as<" + cpp_signature_type(target) + ">())"
    return value_expr


def _emit_box(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    normalized = _normalize_cpp_boundary_expr(ctx, node)
    normalized_obj = json.JsonValue(normalized).as_obj()
    if normalized_obj is not None:
        node = normalized_obj.raw
    value = node.get("value")
    value_obj = json.JsonValue(value).as_obj()
    value_dict: dict[str, JsonVal] = {}
    if value_obj is not None:
        value_dict = value_obj.raw
    target_type = _str(node, "resolved_type")
    if target_type in ("Any", "Obj", "object") and value_obj is not None:
        value_kind = _str(value_dict, "kind")
        value_type = _effective_resolved_type(value_dict)
        if value_kind == "Dict" and value_type == "dict[unknown,unknown]" and len(_list(value_dict, "entries")) == 0:
            return "object(" + _emit_expr(ctx, value_dict) + ")"
        if value_kind == "List" and value_type == "list[unknown]" and len(_list(value_dict, "elements")) == 0:
            return "object(" + _emit_expr(ctx, value_dict) + ")"
        if value_kind == "Set" and value_type == "set[unknown]" and len(_list(value_dict, "elements")) == 0:
            return "object(" + _emit_expr(ctx, value_dict) + ")"
    value_expr = _emit_expr(ctx, value)
    value_type = _expanded_union_type(_effective_resolved_type(value))
    if _is_top_level_union_type(value_type):
        union_lanes = _split_top_level_union_type(value_type)
        has_none = False
        non_none_lanes: list[str] = []
        for lane in union_lanes:
            if lane in ("None", "none"):
                has_none = True
            else:
                non_none_lanes.append(lane)
        if has_none and len(non_none_lanes) == 1:
            return (
                "(py_is_none(" + value_expr + ") ? object() : "
                + _emit_box_known_typed_expr(ctx, "*" + value_expr, non_none_lanes[0], value_node=None)
                + ")"
            )
        visit_body = (
            "::std::visit([&](const auto& __pytra_v) -> object { "
            + "using __PytraLane = ::std::decay_t<decltype(__pytra_v)>; "
            + "if constexpr (::std::is_same_v<__PytraLane, int64> || ::std::is_same_v<__PytraLane, float64> || ::std::is_same_v<__PytraLane, bool> || ::std::is_same_v<__PytraLane, str>) return object(__pytra_v); "
            + "else return object(__pytra_v); "
            + "}, "
        )
        if has_none:
            return (
                "(py_is_none(" + value_expr + ") ? object() : "
                + visit_body + "*" + value_expr + "))"
            )
        return visit_body + value_expr + ")"
    return _emit_box_known_typed_expr(ctx, value_expr, value_type, value_node=value)


def _emit_box_known_typed_expr(
    ctx: CppEmitContext,
    value_expr: str,
    value_type: str,
    *,
    value_node: JsonVal = None,
) -> str:
    if value_type in ("", "unknown", "Any", "Obj", "object"):
        return value_expr
    if value_type == "None":
        return "object()"
    if value_type in ("bool", "int", "int64", "float", "float64", "str"):
        return "object(" + value_expr + ")"
    if (
        value_type.startswith("list[")
        or value_type.startswith("dict[")
        or value_type.startswith("set[")
    ):
        if _uses_ref_container_storage(ctx, value_node):
            return "object(" + value_expr + ")"
        value_type_arg = value_type + ""
        cpp_value_type = cpp_signature_type(value_type_arg, prefer_value_container=True) + ""
        return (
            "object(make_object<"
            + cpp_value_type
            + ">("
            + value_expr
            + "))"
    )
    class_type_id = _lookup_class_type_id(ctx, value_type)
    if class_type_id is not None:
        value_type_arg = value_type + ""
        cpp_value_type = cpp_signature_type(value_type_arg) + ""
        # "this" is a raw pointer; dereference to copy-construct the value
        ctor_arg = ("*" + value_expr) if value_expr == "this" else value_expr
        return (
            "object(make_object<"
            + cpp_value_type
            + ">("
            + str(class_type_id)
            + ", "
            + ctor_arg
            + "))"
        )
    # Handle optional (T | None) types → box ::std::optional<T> to object
    optional_inner = _top_level_optional_inner(value_type)
    if optional_inner not in ("", "unknown"):
        return "(" + value_expr + ".has_value() ? object(*" + value_expr + ") : object())"
    return value_expr


def _emit_object_unbox(value_expr: str, target: str) -> str:
    if target == "str":
        return "(" + value_expr + ").unbox<str>()"
    if target in ("int", "int64"):
        return "(" + value_expr + ").unbox<int64>()"
    if target in ("float", "float64"):
        return "(" + value_expr + ").unbox<float64>()"
    if target == "bool":
        return "(" + value_expr + ").unbox<bool>()"
    return value_expr


def _emit_isinstance(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    expected_trait_fqcn = _str(node, "expected_trait_fqcn")
    if expected_trait_fqcn != "":
        _emit_fail(ctx, "unexpected_trait_isinstance", expected_trait_fqcn)
    expected_name = _str(node, "expected_type_name")
    if expected_name == "":
        expected = node.get("expected_type_id")
        expected_obj = json.JsonValue(expected).as_obj()
        expected_name = _str(expected_obj.raw, "id") if expected_obj is not None else ""
    expected_name = _canonical_expected_type_name(expected_name)
    value_expr = _emit_expr(ctx, value)
    value_type = _expanded_union_type(_effective_resolved_type(value))
    storage_type = _expanded_union_type(_expr_storage_type(ctx, value))
    union_type = storage_type if _is_top_level_union_type(storage_type) else value_type
    if _is_top_level_union_type(union_type):
        lanes = _split_top_level_union_type(union_type)
        inner = _unwrap_optional_variant(value_expr, union_type)
        has_none = _union_has_none(union_type)
        checks: list[str] = []
        for lane in lanes:
            if lane in ("None", "none"):
                continue
            if not _union_lane_matches_nominal_expected(ctx, lane, expected_name):
                continue
            checks.append("::std::holds_alternative<" + cpp_signature_type(lane) + ">(" + inner + ")")
        if len(checks) == 0:
            return "false"
        result = "(" + " || ".join(checks) + ")"
        if has_none:
            result = "(" + value_expr + ".has_value() && " + result + ")"
        return result
    builtin_check = _emit_builtin_isinstance(value_expr, expected_name)
    if builtin_check != "":
        return builtin_check
    exact_pod_cpp_types = {
        "bool": "bool",
        "int8": "int8",
        "uint8": "uint8",
        "int16": "int16",
        "uint16": "uint16",
        "int32": "int32",
        "uint32": "uint32",
        "int64": "int64",
        "uint64": "uint64",
        "float32": "float32",
        "float64": "float64",
    }
    cpp_exact_type = exact_pod_cpp_types.get(expected_name, "")
    if cpp_exact_type != "":
        return "py_runtime_value_exact_is<" + cpp_exact_type + ">(" + value_expr + ")"
    if _is_top_level_union_type(union_type):
        lanes = _split_top_level_union_type(union_type)
        inner = _unwrap_optional_variant(value_expr, union_type)
        has_none = _union_has_none(union_type)
        checks: list[str] = []
        for lane in lanes:
            if lane in ("None", "none"):
                continue
            if not _union_lane_matches_nominal_expected(ctx, lane, expected_name):
                continue
            checks.append("::std::holds_alternative<" + cpp_signature_type(lane) + ">(" + inner + ")")
        if len(checks) == 0:
            return "false"
        result = "(" + " || ".join(checks) + ")"
        if has_none:
            result = "(" + value_expr + ".has_value() && " + result + ")"
        return result
    class_type_id = _lookup_class_type_id(ctx, expected_name)
    if class_type_id is not None and value_type in ("object", "Any", "Obj", "unknown"):
        return (
            "([&]() -> bool { auto __pytra_value = "
            + value_expr
            + "; return static_cast<bool>(__pytra_value) && __pytra_value.isinstance(&"
            + expected_name
            + "::PYTRA_TYPE_INFO); }())"
        )
    if value_type in ("object", "Any", "Obj", "unknown") or "|" in value_type:
        return "false"
    if class_type_id is not None:
        return "true" if _is_known_class_subtype(ctx, value_type, expected_name) else "false"
    return "false"


def _emit_obj_type_id(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    value_expr = _emit_expr(ctx, value)
    value_type = _effective_resolved_type(value)
    static_expr = _emit_static_type_id_expr(ctx, value_type)
    if static_expr != "" and value_type not in ("object", "Any", "Obj", "unknown") and "|" not in value_type:
        return static_expr
    return (
        "([&]() -> pytra_type_id { auto __pytra_value = "
        + value_expr
        + "; return static_cast<bool>(__pytra_value) ? static_cast<pytra_type_id>(__pytra_value.type_id()) : static_cast<pytra_type_id>(0); }())"
    )


def _emit_issubtype(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    actual = _emit_expr(ctx, node.get("actual_type_id"))
    expected = _emit_expr(ctx, node.get("expected_type_id"))
    if actual == "" or expected == "":
        return "false"
    return "py_tid_is_subtype(static_cast<int64>(" + actual + "), static_cast<int64>(" + expected + "))"


def _emit_issubclass(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    actual = _emit_expr(ctx, node.get("actual_type_id"))
    expected = _emit_expr(ctx, node.get("expected_type_id"))
    if actual == "" or expected == "":
        return "false"
    return "py_tid_issubclass(static_cast<int64>(" + actual + "), static_cast<int64>(" + expected + "))"


def _emit_slice_expr(ctx: CppEmitContext, node: dict[str, JsonVal], value_expr: str, slice_node: dict[str, JsonVal]) -> str:
    value_node = node.get("value")
    value_obj = json.JsonValue(value_node).as_obj()
    value_type = _str(value_obj.raw, "resolved_type") if value_obj is not None else ""
    storage_type = _expr_storage_type(ctx, value_node)
    if (value_type in ("", "unknown", "tuple", "list", "dict", "set") or value_type == storage_type) and storage_type != "":
        value_type = storage_type
    class_var_spec = _class_var_spec(ctx, value_node)
    if class_var_spec is not None and value_type in ("", "unknown", "tuple", "list", "dict", "set"):
        spec_type = _str(class_var_spec, "type")
        if spec_type != "":
            value_type = spec_type
    lower = slice_node.get("lower")
    upper = slice_node.get("upper")
    lower_obj = json.JsonValue(lower).as_obj()
    upper_obj = json.JsonValue(upper).as_obj()
    lo_expr = _emit_expr(ctx, lower) if lower_obj is not None else "0"
    up_expr = _emit_expr(ctx, upper) if upper_obj is not None else "py_len(" + value_expr + ")"
    if value_type == "str":
        return "py_str_slice(" + value_expr + ", " + lo_expr + ", " + up_expr + ")"
    if value_type in ("", "unknown"):
        return "py_str_slice(" + value_expr + ", " + lo_expr + ", " + up_expr + ")"
    if value_type.startswith("list[") or value_type in ("bytes", "bytearray"):
        return "py_list_slice_copy(" + value_expr + ", " + lo_expr + ", " + up_expr + ")"
    _emit_fail(ctx, "unsupported_slice_shape", value_type if value_type != "" else "<unknown>")


def _emit_ifexp(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    test = _emit_condition_expr(ctx, node.get("test"))
    resolved_type = _str(node, "resolved_type")
    body_node = node.get("body")
    orelse_node = node.get("orelse")
    optional_inner = _optional_inner_type(resolved_type)
    if optional_inner != "":
        body_obj = json.JsonValue(body_node).as_obj()
        orelse_obj = json.JsonValue(orelse_node).as_obj()
        body_is_none = body_obj is not None and _str(body_obj.raw, "resolved_type") == "None"
        orelse_is_none = orelse_obj is not None and _str(orelse_obj.raw, "resolved_type") == "None"
        body_expr = _emit_expr_as_type(ctx, body_node, optional_inner) if not body_is_none else "::std::nullopt"
        orelse_expr = _emit_expr_as_type(ctx, orelse_node, optional_inner) if not orelse_is_none else "::std::nullopt"
        if body_expr != "::std::nullopt":
            body_expr = "::std::optional<" + cpp_signature_type(optional_inner) + ">(" + body_expr + ")"
        if orelse_expr != "::std::nullopt":
            orelse_expr = "::std::optional<" + cpp_signature_type(optional_inner) + ">(" + orelse_expr + ")"
        return "(" + test + " ? " + body_expr + " : " + orelse_expr + ")"
    if "|" in resolved_type:
        union_cpp = cpp_signature_type(resolved_type)
        body = union_cpp + "(" + _emit_expr(ctx, body_node) + ")"
        orelse = union_cpp + "(" + _emit_expr(ctx, orelse_node) + ")"
        return "(" + test + " ? " + body + " : " + orelse + ")"
    body = _emit_expr(ctx, body_node)
    orelse = _emit_expr(ctx, orelse_node)
    return "(" + test + " ? " + body + " : " + orelse + ")"


def _emit_fstring(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    parts: list[str] = []
    for v in values:
        v_obj = json.JsonValue(v).as_obj()
        if v_obj is not None:
            v_dict = v_obj.raw
            raw_text = json.JsonValue(v_dict.get("value")).as_str()
            if _str(v_dict, "kind") == "Constant" and raw_text is not None:
                parts.append(_cpp_string(raw_text))
                continue
            expr = _emit_expr(ctx, v_dict)
            value_type = _effective_resolved_type(v_dict)
            if value_type == "str" or _str(v_dict, "kind") == "FormattedValue":
                parts.append(expr)
            else:
                parts.append("str(py_to_string(" + expr + "))")
    if len(parts) == 0: return '""'
    return " + ".join(parts)


_CPP_INT_TYPES: set[str] = {"int64", "int32", "int16", "int8", "int", "int64_t"}
_CPP_FLOAT_TYPES: set[str] = {"float64", "float32", "double", "float"}


def _is_cpp_integer_type(type_name: str) -> bool:
    return type_name in {
        "int",
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
    }


def _emit_formatted_value(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value_node = node.get("value")
    expr = _emit_expr(ctx, value_node)
    fmt_spec = _str(node, "format_spec")
    if fmt_spec != "":
        value_obj = json.JsonValue(value_node).as_obj()
        vtype = _effective_resolved_type(value_node) if value_obj is not None else "unknown"
        ctx.includes_needed.add("built_in/format_ops.h")
        spec_lit = '"' + fmt_spec + '"'
        if vtype in _CPP_INT_TYPES:
            return "py_fmt_int(" + expr + ", " + spec_lit + ")"
        if vtype in _CPP_FLOAT_TYPES:
            return "py_fmt_float(" + expr + ", " + spec_lit + ")"
        return "py_fmt_str(str(py_to_string(" + expr + ")), " + spec_lit + ")"
    return "str(py_to_string(" + expr + "))"


def _emit_lambda(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    body = node.get("body")
    params: list[str] = []
    for a in arg_order:
        an = _json_str_value(a)
        at = arg_types.get(an, "")
        at_str = _json_str_value(at)
        params.append(cpp_param_decl(at_str, an))
    return "[&](" + ", ".join(params) + ") { return " + _emit_expr(ctx, body) + "; }"


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_stmt(ctx: CppEmitContext, node: JsonVal) -> None:
    """Emit a single statement via _CppStmtCommonRenderer (P3-CR-CPP-S1).

    All dispatch goes through the renderer: common nodes are handled by
    CommonRenderer base; C++ specific nodes by emit_stmt_extension.
    """
    node_obj = json.JsonValue(node).as_obj()
    if node_obj is None:
        _emit_fail(ctx, "invalid_stmt", "expected dict statement node")
        return
    renderer = _CppStmtCommonRenderer(ctx)
    renderer.emit_stmt(node_obj.raw)
    ctx.indent_level = renderer.state.indent_level + 0


def _emit_body(ctx: CppEmitContext, body: list[JsonVal]) -> None:
    """Emit a list of statements via _CppStmtCommonRenderer (P3-CR-CPP-S1)."""
    renderer = _CppStmtCommonRenderer(ctx)
    for s in body:
        renderer.emit_stmt(s)
        ctx.indent_level = renderer.state.indent_level + 0


def _emit_expr_stmt(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    value_obj = json.JsonValue(value).as_obj()
    if value_obj is None: return
    value_dict = value_obj.raw
    doc = json.JsonValue(value_dict.get("value")).as_str()
    if _str(value_dict, "kind") == "Constant" and doc is not None:
        if doc.strip() != "":
            for line in doc.strip().split("\n"): _emit(ctx, "// " + line)
        return
    code = _emit_expr(ctx, value_dict)
    if code != "": _emit(ctx, code + ";")


def _emit_ann_assign(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    target_val = node.get("target")
    rt = _str(node, "decl_type")
    if rt == "": rt = _str(node, "resolved_type")
    value = node.get("value")

    name = ""
    is_attr = False
    target_text = _json_str_value(target_val)
    target_obj = json.JsonValue(target_val).as_obj()
    if target_text != "":
        name = target_text
    elif target_obj is not None:
        target_dict = target_obj.raw
        if _str(target_dict, "kind") == "Attribute":
            is_attr = True
        else:
            name = _str(target_dict, "id")
            if name == "": name = _str(target_dict, "repr")

    if is_attr:
        lhs = _emit_expr(ctx, target_val)
        if value is not None:
            rhs = _emit_expr(ctx, value)
            rhs = _wrap_expr_for_target_type(ctx, _attribute_target_type(ctx, target_val), rhs, value)
            _emit(ctx, lhs + " = " + rhs + ";")
        return

    already_visible = _is_local_visible(ctx, name)
    _register_local_storage(ctx, name, rt)
    if not already_visible:
        _declare_local_visible(ctx, name)
    if already_visible:
        if value is not None:
            val_expr = _emit_expr(ctx, value)
            val_expr = _wrap_expr_for_target_type(ctx, rt, val_expr, value)
            _emit(ctx, name + " = " + val_expr + ";")
        return
    ct = "auto" if _cpp_type_is_unknownish(rt) else _decl_cpp_type(ctx, rt, name)
    if value is not None:
        val_expr = _emit_expr(ctx, value)
        val_expr = _wrap_expr_for_target_type(ctx, rt, val_expr, value)
        _emit(ctx, ct + " " + name + " = " + val_expr + ";")
    else:
        _emit(ctx, ct + " " + name + " = " + _decl_cpp_zero_value(ctx, rt, name) + ";")


def _emit_assign(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    target_single = node.get("target")
    value = node.get("value")
    target_single_obj = json.JsonValue(target_single).as_obj()
    if len(targets) == 0 and target_single_obj is not None:
        targets = [target_single_obj.raw]
    if len(targets) == 0: return
    if _is_python_type_alias_expr(value):
        return

    val_code = _emit_expr(ctx, value)
    t_value: JsonVal = targets[0]
    t_obj = json.JsonValue(t_value).as_obj()
    if t_obj is None:
        _emit_fail(ctx, "unsupported_assign_target", "non-dict target")
        return
    t = t_obj.raw

    tk = _str(t, "kind")
    if tk == "Name" or tk == "NameTarget":
        name = _str(t, "id")
        if name == "": name = _str(t, "repr")
        declare = _bool(node, "declare")
        if _is_local_visible(ctx, name) or not declare:
            target_type = ctx.var_types.get(name, "")
            if target_type != "":
                val_code = _wrap_expr_for_target_type(ctx, target_type, val_code, value)
            _emit(ctx, name + " = " + val_code + ";")
        else:
            dt = _str(node, "decl_type")
            value_obj = json.JsonValue(value).as_obj()
            if _cpp_type_is_unknownish(dt) and value_obj is not None and _str(value_obj.raw, "kind") == "Subscript":
                sub_value = value_obj.raw.get("value")
                sub_slice = value_obj.raw.get("slice")
                sub_source_type = _selfhost_normalize_cpp_container_alias(_expr_storage_type(ctx, sub_value))
                if sub_source_type == "":
                    sub_source_type = _selfhost_normalize_cpp_container_alias(_effective_resolved_type(sub_value))
                sub_slice_obj = json.JsonValue(sub_slice).as_obj()
                if sub_source_type.startswith("tuple[") and sub_slice_obj is not None and _str(sub_slice_obj.raw, "kind") == "Constant":
                    iv = _json_int_value(sub_slice_obj.raw.get("value"))
                    if iv is not None:
                        iv_index = iv + 0
                        parts = split_generic_types(sub_source_type[6:-1])
                        if 0 <= iv_index < len(parts):
                            dt = parts[iv_index] + ""
            _register_local_storage(ctx, name, dt)
            _declare_local_visible(ctx, name)
            if _cpp_type_is_unknownish(dt):
                _emit(ctx, "auto " + name + " = " + val_code + ";")
            else:
                ct = _decl_cpp_type(ctx, dt, name)
                if _bool(node, "bind_ref"):
                    _emit(ctx, ct + "& " + name + " = " + val_code + ";")
                else:
                    _emit(ctx, ct + " " + name + " = " + val_code + ";")
        if _bool(node, "unused") and _bool(node, "declare"):
            _emit(ctx, "(void)" + name + ";")
    elif tk == "Attribute":
        _emit(ctx, _emit_expr(ctx, t) + " = " + _wrap_expr_for_target_type(ctx, _attribute_target_type(ctx, t), val_code, value) + ";")
    elif tk == "Subscript":
        _emit(ctx, _emit_subscript_store_target(ctx, t) + " = " + val_code + ";")
    elif tk == "Tuple":
        elts = _list(t, "elements")
        names = [_emit_expr(ctx, e) for e in elts]
        all_visible = True
        for name in names:
            if not _is_local_visible(ctx, name):
                all_visible = False
        if all_visible:
            tmp_name = _next_temp(ctx, "__tuple")
            _emit(ctx, "auto " + tmp_name + " = " + val_code + ";")
            for i in range(len(names)):
                name = names[i]
                _emit(ctx, name + " = ::std::get<" + str(i) + ">(" + tmp_name + ");")
        else:
            _emit(ctx, "auto [" + ", ".join(names) + "] = " + val_code + ";")
            for name in names:
                _declare_local_visible(ctx, name)
    else:
        _emit_fail(ctx, "unsupported_assign_target", tk if tk != "" else "<unknown>")


def _emit_aug_assign(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    target = _emit_expr(ctx, node.get("target"))
    value = _emit_expr(ctx, node.get("value"))
    op_name = _str(node, "op")
    if op_name == "Mod":
        _emit(ctx, target + " = py_mod(" + target + ", " + value + ");")
        return
    op = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/"}.get(op_name, "+")
    _emit(ctx, target + " " + op + "= " + value + ";")


def _emit_return(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if value is None: _emit(ctx, "return;")
    elif ctx.current_return_type == "None":
        _emit(ctx, "(void)(" + _emit_expr(ctx, value) + ");")
        _emit(ctx, "return;")
    else:
        value_obj = json.JsonValue(value).as_obj()
        if value_obj is not None and _str(value_obj.raw, "kind") == "Name":
            name = _str(value_obj.raw, "id")
            if name in ("self", "this") and ctx.current_return_type == ctx.current_class and ctx.current_class != "":
                _emit(ctx, "return (*this);")
                return
        _emit(ctx, "return " + _emit_expr_as_type(ctx, value, ctx.current_return_type) + ";")


def _emit_for_core(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    iter_plan = node.get("iter_plan")
    target_plan = node.get("target_plan")
    iter_plan_obj = json.JsonValue(iter_plan).as_obj()
    target_plan_obj = json.JsonValue(target_plan).as_obj()
    if iter_plan_obj is not None:
        iter_plan_dict = iter_plan_obj.raw
        target_plan_dict: dict[str, JsonVal] = {}
        if target_plan_obj is not None:
            target_plan_dict = target_plan_obj.raw
        ip_kind = _str(iter_plan_dict, "kind")
        t_name = _str(target_plan_dict, "id") if target_plan_obj is not None else "_"
        if t_name == "": t_name = "_"
        if t_name == "_" or (target_plan_obj is not None and _bool(target_plan_dict, "unused")):
            t_name = _next_temp(ctx, "__discard")
        if ip_kind in ("StaticRangeForPlan", "RuntimeIterForPlan"):
            if iter_plan_dict.get("start") is not None or iter_plan_dict.get("stop") is not None:
                start = _emit_expr(ctx, iter_plan_dict.get("start")) if iter_plan_dict.get("start") else "0"
                stop = _emit_expr(ctx, iter_plan_dict.get("stop")) if iter_plan_dict.get("stop") else "0"
                step = "1"
                target_type = _str(target_plan_dict, "target_type") if target_plan_obj is not None else ""
                step_node = iter_plan_dict.get("step")
                step_obj = json.JsonValue(step_node).as_obj()
                neg = False
                if step_obj is not None and _str(step_obj.raw, "kind") == "Constant":
                    sv = _json_int_value(step_obj.raw.get("value"))
                    if sv is not None:
                        sv_index = sv + 0
                        step = str(sv_index)
                        neg = sv_index < 0
                elif (step_obj is not None and _str(step_obj.raw, "kind") == "UnaryOp"
                      and _str(step_obj.raw, "op") == "USub"):
                    operand = step_obj.raw.get("operand")
                    operand_obj = json.JsonValue(operand).as_obj()
                    if operand_obj is not None and _str(operand_obj.raw, "kind") == "Constant":
                        sv2_int = _json_int_value(operand_obj.raw.get("value"))
                        if sv2_int is not None and sv2_int > 0:
                            neg = True
                    step = _emit_expr(ctx, step_node)
                elif step_node is not None: step = _emit_expr(ctx, step_node)
                cmp = " > " if neg else " < "
                decl = ""
                if t_name not in ctx.var_types:
                    decl = (_decl_cpp_type(ctx, target_type, t_name) if target_type not in ("", "unknown") else "auto") + " "
                _emit(ctx, "for (" + decl + t_name + " = " + start + "; " + t_name + cmp + stop + "; " + t_name + " += " + step + ") {")
                ctx.indent_level += 1
                _register_local_storage(ctx, t_name, target_type)
                _emit_body(ctx, body)
                ctx.indent_level -= 1
                _emit(ctx, "}")
                return
            else:
                iter_expr = iter_plan_dict.get("iter_expr")
                iter_code = _emit_expr(ctx, iter_expr) if iter_expr else "{}"
                iter_type = _effective_resolved_type(iter_expr)
                iter_expr_obj = json.JsonValue(iter_expr).as_obj()
                if iter_type in ("", "unknown") and iter_expr_obj is not None and _str(iter_expr_obj.raw, "kind") == "Call":
                    func = iter_expr_obj.raw.get("func")
                    func_obj = json.JsonValue(func).as_obj()
                    if func_obj is not None and _str(func_obj.raw, "kind") == "Attribute" and _str(func_obj.raw, "attr") == "items":
                        owner_node = func_obj.raw.get("value")
                        owner_type = _selfhost_normalize_cpp_container_alias(_expr_storage_type(ctx, owner_node))
                        if owner_type == "":
                            owner_type = _selfhost_normalize_cpp_container_alias(_effective_resolved_type(owner_node))
                        owner_obj = json.JsonValue(owner_node).as_obj()
                        if owner_obj is not None and _str(owner_obj.raw, "kind") == "Unbox":
                            unbox_value = owner_obj.raw.get("value")
                            source_union = _selfhost_normalize_cpp_container_alias(_expr_storage_type(ctx, unbox_value))
                            if source_union == "":
                                source_union = _selfhost_normalize_cpp_container_alias(_effective_resolved_type(unbox_value))
                            if _is_top_level_union_type(source_union):
                                dict_lane_target = "dict"
                                lane = _select_union_lane(source_union, dict_lane_target)
                                if lane != "":
                                    owner_type = lane
                        if _is_top_level_union_type(owner_type):
                            dict_lane_target = "dict"
                            owner_type = _select_union_lane(owner_type, dict_lane_target)
                        if owner_type.startswith("dict[") and owner_type.endswith("]"):
                            parts = _container_type_args(owner_type)
                            if len(parts) == 2:
                                iter_type = "tuple[" + parts[0] + "," + parts[1] + "]"
                target_type = _str(target_plan_dict, "target_type") if target_plan_obj is not None else ""
                if target_type == "" and iter_type.startswith("tuple["):
                    target_type = iter_type
                if iter_type == "str" and target_type == "str":
                    iter_tmp = _next_temp(ctx, "__iter")
                    idx_name = _next_temp(ctx, "__str_idx")
                    _emit(ctx, "auto " + iter_tmp + " = " + iter_code + ";")
                    _emit(ctx, "for (int64 " + idx_name + " = int64(0); " + idx_name + " < py_len(" + iter_tmp + "); " + idx_name + " += int64(1)) {")
                    ctx.indent_level += 1
                    decl = ""
                    if t_name not in ctx.var_types:
                        decl = "str "
                    _emit(ctx, decl + t_name + " = py_str_slice(" + iter_tmp + ", " + idx_name + ", (" + idx_name + " + int64(1)));")
                    _register_local_storage(ctx, t_name, "str")
                    _emit_body(ctx, body)
                    ctx.indent_level -= 1
                    _emit(ctx, "}")
                    return
                if iter_type.startswith("dict["):
                    entry_name = _next_temp(ctx, "__entry")
                    _emit(ctx, "for (const auto& " + entry_name + " : " + iter_code + ") {")
                    ctx.indent_level += 1
                    decl = ""
                    if t_name not in ctx.var_types:
                        decl = (_decl_cpp_type(ctx, target_type, t_name) if target_type not in ("", "unknown") else "auto") + " "
                    _emit(ctx, decl + t_name + " = " + entry_name + ".first;")
                    _register_local_storage(ctx, t_name, target_type)
                    _emit_body(ctx, body)
                    ctx.indent_level -= 1
                    _emit(ctx, "}")
                    return
                _emit(ctx, "for (auto " + t_name + " : " + iter_code + ") {")
                ctx.indent_level += 1
                _register_local_storage(ctx, t_name, target_type)
                _emit_body(ctx, body)
                ctx.indent_level -= 1
                _emit(ctx, "}")
                return
    _emit_fail(ctx, "unsupported_for", repr(node))


def _emit_function_def(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    _emit_function_def_impl(ctx, node)


def _closure_function_type(node: dict[str, JsonVal]) -> str:
    params: list[str] = []
    for _, arg_type, _ in _function_param_meta(node):
        arg_type_arg = arg_type + ""
        params.append(cpp_signature_type(arg_type_arg) + "")
    return_type_arg = _return_type(node) + ""
    ret = cpp_signature_type(return_type_arg) + ""
    return "::std::function<" + ret + "(" + ", ".join(params) + ")>"


def _emit_closure_def(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    if name == "":
        return
    ctx.includes_needed.add("functional")
    saved = dict(ctx.var_types)
    saved_value_container_vars = set(ctx.value_container_vars)
    saved_ret = ctx.current_return_type
    saved_scope = ctx.current_function_scope
    saved_scope_locals = set(ctx.current_value_container_locals)
    saved_visible_scopes = [set(scope) for scope in ctx.visible_local_scopes]
    return_type = _return_type(node)
    ctx.current_return_type = return_type
    name = _str(node, "name")
    ctx.current_function_scope = _scope_key(ctx, name)
    ctx.current_value_container_locals = _container_value_locals_for_scope(ctx, name)
    if len(ctx.visible_local_scopes) == 0:
        empty_scope: set[str] = set()
        ctx.visible_local_scopes = [empty_scope]
    _declare_local_visible(ctx, name)
    ctx.visible_local_scopes = [set(scope) for scope in ctx.visible_local_scopes]
    if len(ctx.visible_local_scopes) == 0:
        empty_scope: set[str] = set()
        ctx.visible_local_scopes = [empty_scope]
    _declare_local_visible(ctx, name)
    for arg_name, arg_type, _ in _function_param_meta(node, ctx):
        _register_local_storage(ctx, arg_name, arg_type)
        _declare_local_visible(ctx, arg_name)
    _register_local_storage(ctx, name, _closure_function_type(node))
    params = [_param_decl_text(arg_type, arg_name, is_mutable) for arg_name, arg_type, is_mutable in _function_param_meta(node, ctx)]
    ret = cpp_signature_type(return_type)
    signature = "[" + "&" + "](" + ", ".join(params) + ")"
    if ret != "void":
        signature += " -> " + ret
    _emit(ctx, _closure_function_type(node) + " " + name + " = " + signature + " {")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    _emit(ctx, "};")
    _emit_blank(ctx)
    ctx.var_types = saved
    ctx.value_container_vars = saved_value_container_vars
    ctx.var_types[name] = _closure_function_type(node)
    ctx.current_return_type = saved_ret
    ctx.current_function_scope = saved_scope
    ctx.current_value_container_locals = saved_scope_locals
    ctx.visible_local_scopes = saved_visible_scopes
    _declare_local_visible(ctx, name)


def _emit_class_def(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    base = _str(node, "base")
    body = _list(node, "body")
    is_dc = _bool(node, "dataclass")
    is_trait = _is_trait_class(node)
    enum_kind = base if base in ("Enum", "IntEnum", "IntFlag") else ""
    trait_names = _trait_simple_names(node)
    if enum_kind == "":
        ctx.class_names.add(name)
    else:
        ctx.enum_kinds[name] = enum_kind

    fields: list[tuple[str, str]] = []
    class_vars = ctx.class_vars.get(name, {})
    ft = _dict(node, "field_types")
    if len(ft) > 0:
        for fn, fv in ft.items():
            fields.append((fn, _json_str_value(fv)))
    else:
        for s in body:
            s_obj = json.JsonValue(s).as_obj()
            if s_obj is not None and _str(s_obj.raw, "kind") == "AnnAssign" and is_dc:
                tv = s_obj.raw.get("target")
                tv_obj = json.JsonValue(tv).as_obj()
                tn = _str(tv_obj.raw, "id") if tv_obj is not None else ""
                tr = _str(s_obj.raw, "decl_type")
                if tr == "": tr = _str(s_obj.raw, "resolved_type")
                if tn != "": fields.append((tn, tr))

    if enum_kind != "":
        entries: list[str] = []
        for s in body:
            s_obj = json.JsonValue(s).as_obj()
            if s_obj is None or _str(s_obj.raw, "kind") != "Assign":
                continue
            target = s_obj.raw.get("target")
            target_obj = json.JsonValue(target).as_obj()
            if target_obj is None or _str(target_obj.raw, "kind") != "Name":
                continue
            member_name = _str(target_obj.raw, "id")
            if member_name == "":
                continue
            value_node = s_obj.raw.get("value")
            value_expr = _emit_expr(ctx, value_node)
            entries.append(member_name + " = " + value_expr)
        _emit(ctx, "enum class " + name + " : int64 {")
        ctx.indent_level += 1
        idx = 0
        while idx < len(entries):
            suffix = "," if idx + 1 < len(entries) else ""
            _emit(ctx, entries[idx] + suffix)
            idx += 1
        ctx.indent_level -= 1
        _emit(ctx, "};")
        _emit_blank(ctx)
        return

    if ctx.emit_class_decls:
        base_specs: list[str] = []
        if base != "" and base != "object" and not is_trait:
            base_specs.append("public " + base)
        idx_trait = 0
        while idx_trait < len(trait_names):
            base_specs.append("virtual public " + trait_names[idx_trait])
            idx_trait += 1
        header = "class " + name
        if len(base_specs) > 0:
            header += " : " + ", ".join(base_specs)
        header += " {"
        _emit(ctx, header)
        ctx.indent_level += 1
        _emit(ctx, "public:")
        ctx.indent_level += 1
        for fn, ftype in fields:
            ftype_arg = ftype + ""
            _emit(ctx, cpp_signature_type(ftype_arg) + " " + fn + ";")
        for s in body:
            s_obj = json.JsonValue(s).as_obj()
            if s_obj is None or _str(s_obj.raw, "kind") not in ("FunctionDef", "ClosureDef"):
                continue
            s_dict = s_obj.raw
            template_prefix = _function_template_prefix(s_dict)
            if template_prefix != "":
                _emit(ctx, template_prefix)
            decl = _function_signature(ctx, s_dict, owner_name=name, owner_is_trait=is_trait, declaration_only=True)
            if decl != "":
                _emit(ctx, decl + ";")
        if is_trait:
            _emit(ctx, "virtual ~" + name + "() = default;")
        ctx.indent_level -= 1
        ctx.indent_level -= 1
        _emit(ctx, "};")
        _emit_blank(ctx)

    if is_trait:
        return

    for var_name, spec in class_vars.items():
        var_type = _str(spec, "type")
        value_node = spec.get("value")
        init_expr = cpp_zero_value(var_type)
        if json.JsonValue(value_node).as_obj() is not None:
            init_expr = _emit_expr(ctx, value_node)
        decl_type = _decl_cpp_type(ctx, var_type, name + "_" + var_name) if var_type not in ("", "unknown") else "auto"
        _emit(ctx, decl_type + " " + name + "_" + var_name + " = " + init_expr + ";")
    if len(class_vars) > 0:
        _emit_blank(ctx)

    for s in body:
        s_obj = json.JsonValue(s).as_obj()
        if s_obj is not None and _str(s_obj.raw, "kind") in ("FunctionDef", "ClosureDef"):
            _emit_function_def_impl(ctx, s_obj.raw, owner_name=name)


def _emit_var_decl(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    rt = _str(node, "type")
    if rt == "": rt = _str(node, "resolved_type")
    ct = _decl_cpp_type(ctx, rt, name)
    _register_local_storage(ctx, name, rt)
    _declare_local_visible(ctx, name)
    _emit(ctx, ct + " " + name + " = " + _decl_cpp_zero_value(ctx, rt, name) + ";")


def _emit_tuple_unpack(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    target_types = _list(node, "target_types")
    value = node.get("value")
    tuple_expr = _emit_expr(ctx, value)
    temp_name = _next_temp(ctx, "__tup")
    source_type = _selfhost_normalize_cpp_container_alias(_effective_resolved_type(value))
    tuple_type = cpp_signature_type(source_type) + ""
    if tuple_type == "auto" or _cpp_type_is_unknownish(source_type):
        tuple_type = "auto"
    source_parts = _container_type_args(source_type)
    source_item_type = ""
    if source_type.startswith("list[") or source_type in ("bytes", "bytearray"):
        if len(source_parts) == 1:
            source_item_type = source_parts[0]
    _emit(ctx, tuple_type + " " + temp_name + " = " + tuple_expr + ";")
    for idx in range(len(targets)):
        target = targets[idx]
        target_obj = json.JsonValue(target).as_obj()
        if target_obj is None or _str(target_obj.raw, "kind") not in ("Name", "NameTarget"):
            _emit_fail(ctx, "unsupported_tuple_unpack_target", repr(target))
            continue
        target_dict = target_obj.raw
        name = _str(target_dict, "id")
        if name == "":
            continue
        resolved_type = _str(target_dict, "resolved_type")
        if resolved_type in ("", "unknown") and idx < len(target_types):
            target_type_item = _json_str_value(target_types[idx])
            if target_type_item != "":
                resolved_type = target_type_item
        if resolved_type in ("", "unknown"):
            if source_type.startswith("tuple[") and idx < len(source_parts):
                resolved_type = source_parts[idx]
            elif source_item_type != "":
                resolved_type = source_item_type
        if source_type.startswith("tuple[") or _cpp_type_is_unknownish(source_type):
            assign_expr = "::std::get<" + str(idx) + ">(" + temp_name + ")"
        elif source_type.startswith("list[") or source_type in ("bytes", "bytearray"):
            assign_expr = "py_list_at_ref(" + temp_name + ", int64(" + str(idx) + "))"
        else:
            assign_expr = temp_name + "[" + str(idx) + "]"
        if _is_local_visible(ctx, name):
            _emit(ctx, name + " = " + assign_expr + ";")
        else:
            decl_type = _decl_cpp_type(ctx, resolved_type, name) if resolved_type not in ("", "unknown") else "auto"
            _emit(ctx, decl_type + " " + name + " = " + assign_expr + ";")
            _declare_local_visible(ctx, name)
        if resolved_type not in ("", "unknown"):
            _register_local_storage(ctx, name, resolved_type)


def _emit_swap(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    _emit(ctx, "std::swap(" + left + ", " + right + ");")


def _cpp_type_is_unknownish(type_name: str) -> bool:
    return type_name == "" or type_name == "unknown" or "unknown" in type_name


def _handler_type_name(handler: dict[str, JsonVal]) -> str:
    handler_type = handler.get("type")
    handler_type_obj = json.JsonValue(handler_type).as_obj()
    if handler_type_obj is not None:
        handler_type_dict = handler_type_obj.raw
        kind = _str(handler_type_dict, "kind")
        if kind == "Name":
            return _str(handler_type_dict, "id")
    return ""


def _render_except_open(ctx: CppEmitContext, handler: dict[str, JsonVal]) -> str:
    handler_type = _handler_type_name(handler)
    handler_name = _str(handler, "name")
    if handler_type == "":
        return "catch (...) {"
    catch_decl = "const " + handler_type + "&"
    if handler_name != "":
        catch_decl += " " + handler_name
    return "catch (" + catch_decl + ") {"


def _render_except_alternates(ctx: CppEmitContext, handler: dict[str, JsonVal]) -> list[str]:
    handler_name = _str(handler, "name")
    if handler_name != "":
        return []
    handler_type = _handler_type_name(handler)
    if handler_type in ("IndexError", "KeyError"):
        return ["catch (const ::std::out_of_range&) {"]
    return []


def _render_raise_value(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    exc = node.get("exc")
    exc_obj = json.JsonValue(exc).as_obj()
    if exc_obj is not None:
        exc_dict = exc_obj.raw
        rc = _str(exc_dict, "runtime_call")
        if rc == "std::runtime_error":
            ea = _list(exc_dict, "args")
            if len(ea) >= 1:
                return "RuntimeError(" + _emit_expr(ctx, ea[0]) + ")"
            return "RuntimeError(" + _cpp_string("RuntimeError") + ")"
        else:
            return _emit_expr(ctx, exc_dict)
    if exc is None:
        return ""
    return _emit_expr(ctx, exc)


def _emit_try(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    renderer = _CppStmtCommonRenderer(ctx)
    renderer.emit_try_stmt(node)
    ctx.indent_level = renderer.state.indent_level + 0


def _emit_raise(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    renderer = _CppStmtCommonRenderer(ctx)
    renderer.emit_raise_stmt(node)
    ctx.indent_level = renderer.state.indent_level + 0


def _emit_with(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    context_expr = _emit_expr(ctx, node.get("context_expr"))
    var_name = _str(node, "var_name")
    if var_name == "":
        var_name = _next_temp(ctx, "__with")
    body = _list(node, "body")
    hoisted = _collect_with_hoisted_names(ctx, body)
    for name, resolved_type in hoisted:
        if _is_local_visible(ctx, name):
            continue
        storage_type = resolved_type if resolved_type != "" else ctx.var_types.get(name, "")
        _register_local_storage(ctx, name, storage_type)
        _declare_local_visible(ctx, name)
        if _cpp_type_is_unknownish(storage_type):
            _emit(ctx, "auto " + name + " = " + _decl_cpp_zero_value(ctx, storage_type, name) + ";")
        else:
            _emit(ctx, _decl_cpp_type(ctx, storage_type, name) + " " + name + " = " + _decl_cpp_zero_value(ctx, storage_type, name) + ";")
    finally_name = _next_temp(ctx, "__finally")
    if _is_local_visible(ctx, var_name):
        _emit(ctx, var_name + " = " + context_expr + ";")
    else:
        _register_local_storage(ctx, var_name, _effective_resolved_type(node.get("context_expr")))
        _declare_local_visible(ctx, var_name)
        _emit(ctx, "auto " + var_name + " = " + context_expr + ";")
    _emit(ctx, "{")
    ctx.indent_level += 1
    _emit(ctx, "auto " + finally_name + " = py_make_scope_exit([&]() {")
    ctx.indent_level += 1
    _emit(ctx, var_name + ".close();")
    ctx.indent_level -= 1
    _emit(ctx, "});")
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _collect_with_hoisted_names(ctx: CppEmitContext, body: list[JsonVal]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add_name(name: str, resolved_type: str) -> None:
        if name == "" or name in seen:
            return
        seen.add(name)
        out.append((name, resolved_type))

    def walk(stmts: list[JsonVal]) -> None:
        for raw_stmt in stmts:
            raw_stmt_obj = json.JsonValue(raw_stmt).as_obj()
            if raw_stmt_obj is None:
                continue
            raw_stmt_dict = raw_stmt_obj.raw
            kind = _str(raw_stmt_dict, "kind")
            if kind == "AnnAssign":
                target = raw_stmt_dict.get("target")
                target_obj = json.JsonValue(target).as_obj()
                if target_obj is not None and _str(target_obj.raw, "kind") in ("Name", "NameTarget"):
                    add_name(_str(target_obj.raw, "id"), _str(raw_stmt_dict, "decl_type"))
            elif kind == "Assign":
                target = raw_stmt_dict.get("target")
                target_obj = json.JsonValue(target).as_obj()
                if target_obj is None:
                    targets = _list(raw_stmt_dict, "targets")
                    first_obj = json.JsonValue(targets[0]).as_obj() if len(targets) > 0 else None
                    if first_obj is not None:
                        target = targets[0]
                        target_obj = first_obj
                if target_obj is not None and _str(target_obj.raw, "kind") in ("Name", "NameTarget"):
                    add_name(_str(target_obj.raw, "id"), _str(raw_stmt_dict, "decl_type"))
            elif kind in ("If", "While", "With", "Try", "ForCore"):
                walk(_list(raw_stmt_dict, "body"))
                walk(_list(raw_stmt_dict, "orelse"))
                walk(_list(raw_stmt_dict, "finalbody"))
                for handler in _list(raw_stmt_dict, "handlers"):
                    handler_obj = json.JsonValue(handler).as_obj()
                    if handler_obj is not None:
                        walk(_list(handler_obj.raw, "body"))

    walk(body)
    return out


def _emit_function_def_impl(ctx: CppEmitContext, node: dict[str, JsonVal], owner_name: str = "") -> None:
    if _has_decorator(node, "extern"):
        return
    saved = dict(ctx.var_types)
    saved_value_container_vars = set(ctx.value_container_vars)
    saved_ret = ctx.current_return_type
    saved_scope = ctx.current_function_scope
    saved_scope_locals = set(ctx.current_value_container_locals)
    saved_current_class = ctx.current_class
    saved_visible_scopes = [set(scope) for scope in ctx.visible_local_scopes]
    return_type = _return_type(node)
    ctx.current_return_type = return_type
    func_name = _str(node, "name")
    ctx.current_function_scope = _scope_key(ctx, func_name, owner_name)
    ctx.current_value_container_locals = _container_value_locals_for_scope(ctx, func_name, owner_name)
    ctx.current_class = owner_name
    empty_scope: set[str] = set()
    ctx.visible_local_scopes = [empty_scope]
    for arg_name, arg_type, _ in _function_param_meta(node, ctx):
        _register_local_storage(ctx, arg_name, arg_type)
        _declare_local_visible(ctx, arg_name)
    signature = _function_signature(ctx, node, owner_name=owner_name, declaration_only=False)
    if signature == "":
        ctx.var_types = saved
        ctx.value_container_vars = saved_value_container_vars
        ctx.current_return_type = saved_ret
        ctx.current_function_scope = saved_scope
        ctx.current_value_container_locals = saved_scope_locals
        ctx.current_class = saved_current_class
        ctx.visible_local_scopes = saved_visible_scopes
        return
    template_prefix = _function_template_prefix(node)
    if template_prefix != "":
        _emit(ctx, template_prefix)
    init_list = _constructor_init_list(ctx, node, owner_name)
    _emit(ctx, signature + init_list + " {")
    ctx.indent_level += 1
    if ctx.module_id == "toolchain.parse.py.nodes" and func_name in ("expr_to_jv", "stmt_to_jv"):
        params = _function_param_meta(node, ctx)
        arg_name = params[0][0] if len(params) > 0 else "e"
        _emit(ctx, "return ::std::get<Object<dict<str, JsonVal>>>(*" + arg_name + ");")
    else:
        _emit_body(ctx, _function_body_for_emit(ctx, node, owner_name, init_list))
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)
    ctx.var_types = saved
    ctx.value_container_vars = saved_value_container_vars
    ctx.current_return_type = saved_ret
    ctx.current_function_scope = saved_scope
    ctx.current_value_container_locals = saved_scope_locals
    ctx.current_class = saved_current_class
    ctx.visible_local_scopes = saved_visible_scopes


def _function_signature(
    ctx: CppEmitContext,
    node: dict[str, JsonVal],
    *,
    owner_name: str = "",
    owner_is_trait: bool = False,
    declaration_only: bool = False,
) -> str:
    name = _safe_cpp_ident(_str(node, "name"))
    if name == "":
        return ""
    is_static = _has_decorator(node, "staticmethod")
    params = [_param_decl_text(arg_type, arg_name, is_mutable) for arg_name, arg_type, is_mutable in _function_param_meta(node, ctx)]
    if declaration_only and owner_name != "":
        if owner_is_trait and not is_static:
            static_prefix = "virtual "
        elif is_static:
            static_prefix = "static "
        else:
            static_prefix = ""
    else:
        static_prefix = ""
    if name == "__init__" and owner_name != "":
        prefix = owner_name if declaration_only else owner_name + "::" + owner_name
        return static_prefix + prefix + "(" + ", ".join(params) + ")"
    return_type_arg = _return_type(node) + ""
    ret = cpp_signature_type(return_type_arg) + ""
    qual_name = name
    if owner_name != "" and not declaration_only:
        qual_name = owner_name + "::" + name
    suffix = ""
    self_mutates = (
        _function_self_mutates(node)
        or _node_mutates_self_fields(_list(node, "body"))
        or _node_mutates_class_storage(ctx, _list(node, "body"), owner_name)
    )
    if declaration_only and owner_name != "" and not is_static and not self_mutates:
        suffix = " const"
    if (not declaration_only) and owner_name != "" and not is_static and not self_mutates:
        suffix = " const"
    out = static_prefix + ret + " " + qual_name + "(" + ", ".join(params) + ")" + suffix
    if declaration_only and owner_name != "":
        if _method_trait_impl_count(node) > 0:
            out += " override"
        elif owner_is_trait:
            out += " = 0"
    return out


def _function_template_prefix(node: dict[str, JsonVal]) -> str:
    params = _function_template_params(node)
    if len(params) == 0:
        return ""
    return "template <" + ", ".join("class " + name for name in params) + ">"


def _constructor_init_list(ctx: CppEmitContext, node: dict[str, JsonVal], owner_name: str) -> str:
    if owner_name == "" or _str(node, "name") != "__init__":
        return ""
    base_name = ctx.class_bases.get(owner_name, "")
    if base_name == "" or base_name == "object":
        return ""
    body = _list(node, "body")
    if len(body) == 0:
        return ""
    first = body[0]
    first_obj = json.JsonValue(first).as_obj()
    if first_obj is None or _str(first_obj.raw, "kind") != "Expr":
        return ""
    value = first_obj.raw.get("value")
    value_obj = json.JsonValue(value).as_obj()
    if value_obj is None or _str(value_obj.raw, "kind") != "Call":
        return ""
    func = value_obj.raw.get("func")
    func_obj = json.JsonValue(func).as_obj()
    if func_obj is None or _str(func_obj.raw, "kind") != "Attribute" or _str(func_obj.raw, "attr") != "__init__":
        return ""
    owner = func_obj.raw.get("value")
    if not _is_zero_arg_super_call(owner):
        return ""
    args: list[str] = []
    for a in _list(value_obj.raw, "args"):
        args.append(_emit_expr(ctx, a))
    keywords = _list(value_obj.raw, "keywords")
    for kw in keywords:
        kw_obj = json.JsonValue(kw).as_obj()
        if kw_obj is not None:
            args.append(_emit_expr(ctx, kw_obj.raw.get("value")))
    return " : " + base_name + "(" + ", ".join(args) + ")"


def _function_body_for_emit(
    ctx: CppEmitContext,
    node: dict[str, JsonVal],
    owner_name: str,
    init_list: str,
) -> list[JsonVal]:
    body = _list(node, "body")
    if init_list == "" or owner_name == "" or _str(node, "name") != "__init__" or len(body) == 0:
        return body
    first = body[0]
    first_obj = json.JsonValue(first).as_obj()
    if first_obj is None or _str(first_obj.raw, "kind") != "Expr":
        return body
    value = first_obj.raw.get("value")
    value_obj = json.JsonValue(value).as_obj()
    if value_obj is None or _str(value_obj.raw, "kind") != "Call":
        return body
    func = value_obj.raw.get("func")
    func_obj = json.JsonValue(func).as_obj()
    if func_obj is None or _str(func_obj.raw, "kind") != "Attribute" or _str(func_obj.raw, "attr") != "__init__":
        return body
    owner = func_obj.raw.get("value")
    if not _is_zero_arg_super_call(owner):
        return body
    return body[1:]


def _function_template_params(node: dict[str, JsonVal]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for _arg_name, arg_type, _mutable in _function_param_meta(node):
        for type_var in collect_cpp_type_vars(arg_type):
            if type_var not in seen:
                seen.add(type_var)
                out.append(type_var)
    for type_var in collect_cpp_type_vars(_return_type(node)):
        if type_var not in seen:
            seen.add(type_var)
            out.append(type_var)
    return out


_BUILTIN_RESOLVED_TYPE_NAMES: set[str] = {
    "int", "int8", "int16", "int32", "int64",
    "uint8", "uint16", "uint32", "uint64",
    "float", "float32", "float64",
    "bool", "str", "bytes", "bytearray",
    "None", "none", "object", "Any", "Obj",
    "JsonVal", "Callable", "callable", "type",
    "unknown",
}


def _is_user_class_param_type(resolved_type: str) -> bool:
    """Return True if the type is a user-defined class (needs mutable C++ ref)."""
    if resolved_type in _BUILTIN_RESOLVED_TYPE_NAMES:
        return False
    if is_container_resolved_type(resolved_type):
        return False
    if resolved_type.startswith("tuple[") or resolved_type.startswith("callable["):
        return False
    if "|" in resolved_type:
        return False
    # Single uppercase letter = template parameter (A, B, T, etc.)
    if len(resolved_type) == 1 and resolved_type.isupper():
        return False
    return True


def _function_param_is_mutated_via_call(
    node: dict[str, JsonVal],
    arg_name: str,
    ctx: CppEmitContext | None,
) -> bool:
    if ctx is None:
        return False
    mutable_indexes = ctx.function_mutable_param_indexes

    def _walk(value: JsonVal) -> bool:
        value_obj = json.JsonValue(value).as_obj()
        if value_obj is not None:
            value_dict = value_obj.raw
            if _str(value_dict, "kind") == "Call":
                func = value_dict.get("func")
                func_obj = json.JsonValue(func).as_obj()
                callee_name = _str(func_obj.raw, "id") if func_obj is not None else ""
                callee_mutable = mutable_indexes.get(callee_name, set())
                if len(callee_mutable) > 0:
                    args = _list(value_dict, "args")
                    for idx in range(len(args)):
                        arg = args[idx]
                        if idx not in callee_mutable:
                            continue
                        arg_obj = json.JsonValue(arg).as_obj()
                        if arg_obj is not None and _str(arg_obj.raw, "kind") == "Name" and _str(arg_obj.raw, "id") == arg_name:
                            return True
            for child in value_dict.values():
                if _walk(child):
                    return True
            return False
        value_arr = json.JsonValue(value).as_arr()
        if value_arr is not None:
            for item in value_arr.raw:
                if _walk(item):
                    return True
        return False

    return _walk(_list(node, "body"))


def _function_param_meta(node: dict[str, JsonVal], ctx: CppEmitContext | None = None) -> list[tuple[str, str, bool]]:
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    arg_usage = _dict(node, "arg_usage")
    is_static = _has_decorator(node, "staticmethod")
    vararg_name_val = node.get("vararg_name")
    vararg_name_str = _json_str_value(vararg_name_val)
    out: list[tuple[str, str, bool]] = []
    for arg in arg_order:
        arg_name = _json_str_value(arg)
        if arg_name == "":
            continue
        if arg_name == "self" and not is_static:
            continue
        if arg_name == vararg_name_str:
            continue
        arg_type = arg_types.get(arg_name, "")
        arg_type_str = _json_str_value(arg_type)
        if arg_type_str == "":
            arg_type_str = "object"
        arg_type_str = normalize_cpp_nominal_adt_type(arg_type_str)
        inferred = _infer_callable_param_type(node, arg_name)
        if inferred != "":
            arg_type_str = inferred
        is_mutable = (arg_usage.get(arg_name) == "reassigned"
                      or _function_param_is_mutated_via_call(node, arg_name, ctx)
                      or (_is_user_class_param_type(arg_type_str)
                          and arg_usage.get(arg_name) != "readonly"))
        out.append((arg_name, arg_type_str, is_mutable))
    vararg_name = node.get("vararg_name")
    vararg_name_text = _json_str_value(vararg_name)
    if vararg_name_text != "":
        vararg_type = arg_types.get(vararg_name_text, "")
        vararg_type_str = _json_str_value(vararg_type)
        if vararg_type_str == "":
            vararg_type_str = "object"
        vararg_type_str = normalize_cpp_nominal_adt_type(vararg_type_str)
        out.append((vararg_name_text, vararg_type_str, False))
    return out


def _type_uses_callable(resolved_type: str) -> bool:
    return resolved_type == "callable" or resolved_type == "Callable" or resolved_type.startswith("callable[")


def _infer_callable_param_type(node: dict[str, JsonVal], param_name: str) -> str:
    arg_types = _dict(node, "arg_types")
    declared_obj = arg_types.get(param_name, "")
    declared = declared_obj if isinstance(declared_obj, str) else ""
    if not _type_uses_callable(declared):
        return ""
    inferred_arg = ""
    inferred_ret = ""

    def _visit(cur: JsonVal, parent: JsonVal = None, grandparent: JsonVal = None) -> None:
        nonlocal inferred_arg, inferred_ret
        if isinstance(cur, dict):
            if _str(cur, "kind") == "Call":
                func = cur.get("func")
                if isinstance(func, dict) and _str(func, "kind") == "Name" and _str(func, "id") == param_name:
                    args = _list(cur, "args")
                    if len(args) == 1 and isinstance(args[0], dict):
                        arg_type = _effective_resolved_type(args[0])
                        if arg_type not in ("", "unknown", "object", "Any", "Callable", "callable"):
                            inferred_arg = arg_type
                    ret_type = _infer_callable_return_from_parent(cur, parent, grandparent, node)
                    if ret_type not in ("", "unknown", "object", "Any", "Callable", "callable"):
                        inferred_ret = ret_type
            for child in cur.values():
                _visit(child, cur, parent)
        elif isinstance(cur, list):
            for child in cur:
                _visit(child, parent, grandparent)

    _visit(_list(node, "body"))
    if inferred_arg != "" and inferred_ret != "":
        return "callable[[" + inferred_arg + "]," + inferred_ret + "]"
    return ""


def _infer_callable_return_from_parent(
    call_node: dict[str, JsonVal],
    parent: JsonVal,
    grandparent: JsonVal,
    func_node: dict[str, JsonVal],
) -> str:
    if isinstance(parent, dict):
        parent_kind = _str(parent, "kind")
        if parent_kind == "Return":
            return _return_type(func_node)
        if parent_kind == "Unbox":
            resolved = _effective_resolved_type(parent)
            if resolved != "":
                return resolved
        if parent_kind == "Call":
            runtime_call = _str(parent, "runtime_call")
            if runtime_call == "list.append":
                owner = parent.get("runtime_owner")
                owner_type = _effective_resolved_type(owner) if isinstance(owner, dict) else ""
                if owner_type.startswith("list[") and owner_type.endswith("]"):
                    return owner_type[5:-1]
            func = parent.get("func")
            if isinstance(func, dict) and _str(func, "kind") == "Name" and _str(func, "id") == _str(call_node.get("func"), "id"):
                if isinstance(grandparent, dict) and _str(grandparent, "kind") == "Return":
                    return _return_type(func_node)
                if isinstance(grandparent, dict) and _str(grandparent, "kind") == "Unbox":
                    resolved = _effective_resolved_type(grandparent)
                    if resolved != "":
                        return resolved
        if parent_kind in ("Assign", "AnnAssign"):
            declared = _str(parent, "decl_type")
            if declared != "":
                return declared
    return ""


def _function_self_mutates(node: dict[str, JsonVal]) -> bool:
    if _bool(node, "mutates_self"):
        return True
    arg_usage = _dict(node, "arg_usage")
    if arg_usage.get("self") == "reassigned":
        return True
    return _node_mutates_self_fields(_list(node, "body"))


def _collect_function_mutable_param_indexes(node: JsonVal, out: dict[str, set[int]]) -> None:
    if not isinstance(node, dict):
        if isinstance(node, list):
            for item in node:
                _collect_function_mutable_param_indexes(item, out)
        return
    kind = _str(node, "kind")
    if kind in ("FunctionDef", "ClosureDef"):
        name = _str(node, "name")
        if name != "":
            indexes: set[int] = set()
            for idx, (_arg_name, _arg_type, is_mutable) in enumerate(_function_param_meta(node)):
                if is_mutable:
                    indexes.add(idx)
            out[name] = indexes
    for child in node.values():
        _collect_function_mutable_param_indexes(child, out)


def _attribute_target_type(ctx: CppEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict) or _str(node, "kind") != "Attribute":
        return ""
    owner = node.get("value")
    attr = _str(node, "attr")
    if not isinstance(owner, dict) or attr == "":
        return ""
    owner_type = _effective_resolved_type(owner)
    if owner_type in ("", "unknown"):
        owner_id = _str(owner, "id")
        if owner_id in ("self", "this") and ctx.current_class != "":
            owner_type = ctx.current_class
    if owner_type in ctx.class_field_types and attr in ctx.class_field_types[owner_type]:
        return ctx.class_field_types[owner_type][attr]
    owner_id = _str(owner, "id")
    if owner_id in ctx.class_field_types and attr in ctx.class_field_types[owner_id]:
        return ctx.class_field_types[owner_id][attr]
    return ""


def _param_decl_text(resolved_type: str, name: str, is_mutable: bool) -> str:
    return cpp_param_decl(resolved_type, name, is_mutable=is_mutable)


def _return_type(node: dict[str, JsonVal]) -> str:
    return_type = _str(node, "return_type")
    if return_type == "":
        return_type = _str(node, "returns")
    if return_type == "":
        return_type = "None"
    return normalize_cpp_nominal_adt_type(return_type)


def _has_decorator(node: dict[str, JsonVal], name: str) -> bool:
    for d in _list(node, "decorators"):
        if isinstance(d, str) and d == name:
            return True
    return False


def _trait_meta(node: dict[str, JsonVal]) -> dict[str, JsonVal]:
    meta = _dict(node, "meta")
    return _dict(meta, "trait_v1")


def _implements_meta(node: dict[str, JsonVal]) -> dict[str, JsonVal]:
    meta = _dict(node, "meta")
    return _dict(meta, "implements_v1")


def _is_trait_class(node: dict[str, JsonVal]) -> bool:
    return len(_trait_meta(node)) > 0 or _has_decorator(node, "trait")


def _trait_simple_names(node: dict[str, JsonVal]) -> list[str]:
    out: list[str] = []
    if _is_trait_class(node):
        traits = _list(_trait_meta(node), "extends_traits")
    else:
        traits = _list(_implements_meta(node), "traits")
    for item in traits:
        if isinstance(item, str) and item != "":
            out.append(item.rsplit(".", 1)[-1])
    return out


def _method_trait_impl_count(node: dict[str, JsonVal]) -> int:
    meta = _dict(node, "meta")
    impl = meta.get("trait_impl_v1")
    if isinstance(impl, dict):
        return 1
    if isinstance(impl, list):
        count = 0
        for item in impl:
            if isinstance(item, dict):
                count += 1
        return count
    return 0


def _is_type_owner(ctx: CppEmitContext, owner_node: JsonVal) -> bool:
    if not isinstance(owner_node, dict):
        return False
    if _str(owner_node, "type_object_of") != "":
        return True
    owner_id = _str(owner_node, "id")
    return owner_id != "" and (owner_id in ctx.class_names or owner_id in ctx.enum_kinds)


def _enum_kind(ctx: CppEmitContext, type_name: str) -> str:
    return ctx.enum_kinds.get(type_name, "")


def _is_int_like_enum(ctx: CppEmitContext, type_name: str) -> bool:
    return _enum_kind(ctx, type_name) in ("IntEnum", "IntFlag")


def _is_zero_arg_super_call(node: JsonVal) -> bool:
    if not isinstance(node, dict) or _str(node, "kind") != "Call":
        return False
    func = node.get("func")
    if not isinstance(func, dict) or _str(func, "kind") != "Name":
        return False
    return _str(func, "id") == "super" and len(_list(node, "args")) == 0 and len(_list(node, "keywords")) == 0


def _node_mutates_class_storage(ctx: CppEmitContext, node: JsonVal, owner_name: str = "") -> bool:
    if isinstance(node, dict):
        kind = _str(node, "kind")
        if kind in ("Assign", "AugAssign", "AnnAssign"):
            targets: list[JsonVal] = []
            target = node.get("target")
            if target is not None:
                targets.append(target)
            targets.extend(_list(node, "targets"))
            for candidate in targets:
                if not isinstance(candidate, dict) or _str(candidate, "kind") != "Attribute":
                    continue
                value_node = candidate.get("value")
                if _is_type_owner(ctx, value_node):
                    return True
                if isinstance(value_node, dict) and _str(value_node, "kind") == "Name":
                    owner_id = _str(value_node, "id")
                    if owner_id != "" and owner_id == owner_name:
                        return True
        for value in node.values():
            if _node_mutates_class_storage(ctx, value, owner_name):
                return True
        return False
    if isinstance(node, list):
        for item in node:
            if _node_mutates_class_storage(ctx, item, owner_name):
                return True
    return False


def _node_mutates_self_fields(node: JsonVal) -> bool:
    if isinstance(node, dict):
        kind = _str(node, "kind")
        if kind in ("Assign", "AugAssign", "AnnAssign"):
            targets: list[JsonVal] = []
            target = node.get("target")
            if target is not None:
                targets.append(target)
            targets.extend(_list(node, "targets"))
            for candidate in targets:
                if not isinstance(candidate, dict) or _str(candidate, "kind") != "Attribute":
                    continue
                owner = candidate.get("value")
                if isinstance(owner, dict) and _str(owner, "kind") == "Name" and _str(owner, "id") == "self":
                    return True
        if kind == "Call":
            meta = node.get("meta")
            if isinstance(meta, dict) and meta.get("mutates_receiver") is True:
                return True
            func = node.get("func")
            if isinstance(func, dict) and _str(func, "kind") == "Attribute":
                owner = func.get("value")
                if isinstance(owner, dict) and _str(owner, "kind") == "Name" and _str(owner, "id") == "self":
                    return True
                if isinstance(owner, dict) and _str(owner, "kind") == "Attribute":
                    base = owner.get("value")
                    if isinstance(base, dict) and _str(base, "kind") == "Name" and _str(base, "id") == "self":
                        call_owner = node.get("runtime_owner")
                        if isinstance(call_owner, dict) and _str(call_owner, "borrow_kind") == "mutable_ref":
                            return True
                        runtime_call = _str(node, "runtime_call")
                        if runtime_call in {
                            "list.append",
                            "list.extend",
                            "list.insert",
                            "list.pop",
                            "list.clear",
                            "list.reverse",
                            "list.sort",
                            "dict.pop",
                            "dict.setdefault",
                            "dict.update",
                            "dict.clear",
                            "set.add",
                            "set.discard",
                            "set.remove",
                            "set.clear",
                            "bytearray.append",
                            "bytearray.extend",
                            "bytearray.pop",
                            "bytearray.clear",
                        }:
                            return True
        for value in node.values():
            if _node_mutates_self_fields(value):
                return True
        return False
    if isinstance(node, list):
        for item in node:
            if _node_mutates_self_fields(item):
                return True
    return False


def _emit_cast_expr(ctx: CppEmitContext, target_node: JsonVal, value_node: JsonVal) -> str:
    value_node = _normalize_cpp_boundary_expr(ctx, value_node)
    target_name = _node_type_mirror(target_node)
    if target_name == "":
        target_name = _effective_resolved_type(target_node)
    if target_name in ("", "unknown", "type", "callable") and isinstance(target_node, dict):
        target_name = _str(target_node, "id")
        if target_name == "":
            target_name = _str(target_node, "repr")
    value_type = _effective_resolved_type(value_node)
    value_kind = _str(value_node, "kind") if isinstance(value_node, dict) else ""
    if target_name not in ("", "unknown", "Any", "Obj", "object") and isinstance(value_node, dict) and _str(value_node, "kind") == "Box":
        boxed_value = value_node.get("value")
        if isinstance(boxed_value, dict):
            return _emit_expr_as_type(ctx, boxed_value, target_name)
    if (
        target_name not in ("", "unknown", "Any", "Obj", "object")
        and isinstance(value_node, dict)
        and value_kind in ("Name", "Attribute", "Subscript")
        and value_type == target_name
        and _optional_inner_type(_expanded_union_type(_expr_storage_type(ctx, value_node))) == ""
        and not _is_top_level_union_type(_expanded_union_type(_expr_storage_type(ctx, value_node)))
        and not _needs_object_cast(_expanded_union_type(_expr_storage_type(ctx, value_node)))
    ):
        return _emit_expr_as_type(ctx, value_node, target_name)
    if value_kind in ("Name", "NameTarget") and isinstance(value_node, dict):
        value_expr = _emit_name_storage(value_node)
    else:
        value_expr = _emit_expr(ctx, value_node)
    static_value_type = _expr_static_type(ctx, value_node)
    storage_type = _expr_storage_type(ctx, value_node)
    union_value_type = _expanded_union_type(value_type)
    union_storage_type = _expanded_union_type(storage_type)
    storage_cpp = cpp_signature_type(storage_type) if storage_type not in ("", "unknown") else ""
    if target_name == "":
        return value_expr
    if (
        target_name in (value_type, static_value_type)
        and _optional_inner_type(union_storage_type) == ""
        and not _is_top_level_union_type(union_storage_type)
        and not _needs_object_cast(union_storage_type)
    ):
        return value_expr
    if _optional_inner_type(union_storage_type) == target_name:
        if value_kind == "Name" and isinstance(value_node, dict):
            return "(*(" + _emit_name_storage(value_node) + "))"
        return "(*(" + value_expr + "))"
    if _has_variant_storage(storage_type):
        source_lane = _select_union_lane(union_storage_type, target_name)
        lane_expr = _emit_union_get_expr(value_expr, union_storage_type, target_name)
        if lane_expr != value_expr:
            if source_lane != "" and is_container_resolved_type(source_lane) and is_container_resolved_type(target_name) and source_lane != target_name:
                return _emit_covariant_copy_expr(
                    ctx,
                    source_expr=lane_expr,
                    source_type=source_lane,
                    target_type=target_name,
                )
            return lane_expr
    if storage_type in ("", "unknown") and _is_top_level_union_type(union_value_type):
        if _is_top_level_union_type(target_name):
            return _emit_union_narrow_expr(value_expr, union_value_type, target_name)
        source_lane = _select_union_lane(union_value_type, target_name)
        lane_expr = _emit_union_get_expr(value_expr, union_value_type, target_name)
        if lane_expr != value_expr:
            if source_lane != "" and is_container_resolved_type(source_lane) and is_container_resolved_type(target_name) and source_lane != target_name:
                return _emit_covariant_copy_expr(
                    ctx,
                    source_expr=lane_expr,
                    source_type=source_lane,
                    target_type=target_name,
                )
            return lane_expr
    if _is_top_level_union_type(target_name):
        direct_source_type = ""
        storage_optional_inner = _optional_inner_type(storage_type)
        if (
            storage_type not in ("", "unknown")
            and storage_optional_inner == ""
            and not _has_variant_storage(storage_type)
            and not _needs_object_cast(storage_type)
        ):
            direct_source_type = union_storage_type
        elif storage_optional_inner == "" and static_value_type not in ("", "unknown"):
            static_union_type = _expanded_union_type(static_value_type)
            if not _is_top_level_union_type(static_union_type) and not _needs_object_cast(static_union_type):
                direct_source_type = static_union_type
        if direct_source_type != "":
            lane = _select_union_lane(target_name, direct_source_type)
            if lane != "":
                return cpp_signature_type(target_name) + "(" + _emit_expr_as_type(ctx, value_node, direct_source_type) + ")"
    scalar_target = target_name
    if scalar_target == "int":
        scalar_target = "int64"
    if scalar_target in ("str", "int64", "float64", "bool") and _is_top_level_union_type(union_value_type):
        lane_expr = _emit_union_get_expr(value_expr, union_value_type, scalar_target)
        if lane_expr != value_expr:
            return lane_expr
    if scalar_target in ("str", "int64", "float64", "bool"):
        scalar_cpp = cpp_signature_type(scalar_target)
        if storage_cpp.startswith("::std::optional<::std::variant<"):
            return "::std::get<" + scalar_cpp + ">(*(" + value_expr + "))"
        if storage_cpp.startswith("::std::variant<"):
            return "::std::get<" + scalar_cpp + ">(" + value_expr + ")"
    if target_name in (storage_type,):
        return value_expr
    if (
        value_kind == "Unbox"
        and value_type not in ("", "unknown")
        and cpp_signature_type(value_type) == cpp_signature_type(target_name)
    ):
        return value_expr
    needs_runtime_cast = (
        (_needs_object_cast(union_storage_type) and union_storage_type != target_name)
        or (_needs_object_cast(union_value_type) and union_value_type != target_name)
    )
    storage_unknown_ref = value_kind in ("Name", "Attribute", "Subscript") and union_storage_type in ("", "unknown")
    if not needs_runtime_cast and value_type == target_name:
        if not (target_name in ctx.class_names and storage_unknown_ref):
            return value_expr
    if target_name in ctx.class_names and (needs_runtime_cast or storage_unknown_ref):
        return "(*(" + value_expr + ").as<" + target_name + ">())"
    if is_container_resolved_type(target_name) and needs_runtime_cast:
        return "(" + value_expr + ").as<" + cpp_container_value_type(target_name) + ">()"
    if target_name == "str" and needs_runtime_cast:
        return _emit_object_unbox(value_expr, "str")
    if target_name in ("int", "int64") and needs_runtime_cast:
        return _emit_object_unbox(value_expr, "int64")
    if target_name in ("float", "float64") and needs_runtime_cast:
        return _emit_object_unbox(value_expr, "float64")
    if target_name == "bool" and needs_runtime_cast:
        return _emit_object_unbox(value_expr, "bool")
    return "static_cast<" + cpp_signature_type(target_name) + ">(" + value_expr + ")"


def _needs_object_cast(resolved_type: str) -> bool:
    return resolved_type in ("unknown", "Any", "Obj", "object") or "|" in resolved_type


def _next_temp(ctx: CppEmitContext, prefix: str) -> str:
    ctx.temp_counter += 1
    return prefix + "_" + str(ctx.temp_counter)


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
        if len(locals_out) > 0:
            out[scope_key] = locals_out
    return out


# ---------------------------------------------------------------------------
# Module emission
# ---------------------------------------------------------------------------

def emit_cpp_module(
    east3_doc: dict[str, JsonVal],
    *,
    allow_runtime_module: bool = False,
    self_header: str = "",
) -> str:
    meta = _dict(east3_doc, "meta")
    module_id = ""
    emit_ctx_meta = _dict(meta, "emit_context")
    if emit_ctx_meta: module_id = _str(emit_ctx_meta, "module_id")
    if module_id == "":
        module_id = _str(meta, "module_id")
    lp = _dict(meta, "linked_program_v1")
    if module_id == "" and lp: module_id = _str(lp, "module_id")

    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "cpp" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)
    init_types_mapping(mapping.types)  # P0-CPP-TYPEMAP-S3: inject types table into cpp type resolver

    if should_skip_module(module_id, mapping) and not allow_runtime_module: return ""

    ctx = CppEmitContext(
        module_id=module_id,
        is_entry=_bool(emit_ctx_meta, "is_entry") if emit_ctx_meta else False,
        mapping=mapping,
        emit_class_decls=(self_header == ""),
    )
    type_id_table_raw = _dict(lp, "type_id_table")
    if len(type_id_table_raw) == 0:
        type_id_table_raw = _dict(lp, "type_id_resolved_v1")
    type_info_table_raw = _dict(lp, "type_info_table_v1")
    ctx.class_type_ids = {
        key: value
        for key, value in type_id_table_raw.items()
        if isinstance(key, str) and isinstance(value, int)
    }
    ctx.class_type_info = {
        key: value
        for key, value in type_info_table_raw.items()
        if isinstance(key, str) and isinstance(value, dict)
    }
    ctx.container_value_locals_by_scope = _load_container_value_locals(lp)

    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")
    ctx.function_mutable_param_indexes = {}
    _collect_function_mutable_param_indexes(body, ctx.function_mutable_param_indexes)
    _collect_function_mutable_param_indexes(main_guard, ctx.function_mutable_param_indexes)

    # Collect imports and class names
    ctx.import_aliases = build_import_alias_map(meta)
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)
    for s in body:
        if isinstance(s, dict) and _str(s, "kind") == "FunctionDef":
            fn_name = _str(s, "name")
            if fn_name != "":
                ctx.function_defs[fn_name] = s
        if isinstance(s, dict) and _str(s, "kind") == "ClassDef":
            class_name = _str(s, "name")
            base_name = _str(s, "base")
            if base_name in ("Enum", "IntEnum", "IntFlag"):
                ctx.enum_kinds[class_name] = base_name
            else:
                ctx.class_names.add(class_name)
            if base_name != "":
                ctx.class_bases[class_name] = base_name
            ctx.class_field_types[class_name] = {
                k: normalize_cpp_nominal_adt_type(v)
                for k, v in _dict(s, "field_types").items()
                if isinstance(k, str) and isinstance(v, str)
            }
            class_vars = ctx.class_vars.setdefault(class_name, {})
            is_dataclass = _bool(s, "dataclass")
            if base_name not in ("Enum", "IntEnum", "IntFlag"):
                for class_stmt in _list(s, "body"):
                    if not isinstance(class_stmt, dict):
                        continue
                    class_stmt_kind = _str(class_stmt, "kind")
                    if class_stmt_kind == "AnnAssign" and not is_dataclass:
                        target = class_stmt.get("target")
                        var_name = _str(target, "id") if isinstance(target, dict) else ""
                        if var_name == "":
                            continue
                        value = class_stmt.get("value")
                        if not isinstance(value, dict):
                            continue
                        var_type = _str(class_stmt, "decl_type")
                        if var_type == "":
                            var_type = _str(class_stmt, "annotation")
                        class_vars[var_name] = CppClassVarSpecDraft(type_name=var_type, value=value).to_jv()
                    elif class_stmt_kind == "Assign" and not is_dataclass:
                        target = class_stmt.get("target")
                        var_name = _str(target, "id") if isinstance(target, dict) else ""
                        if var_name == "":
                            continue
                        value = class_stmt.get("value")
                        var_type = _str(class_stmt, "decl_type")
                        if var_type == "" and isinstance(value, dict):
                            var_type = _str(value, "resolved_type")
                        class_vars[var_name] = CppClassVarSpecDraft(type_name=var_type, value=value).to_jv()
    ctx.class_symbol_fqcns = _build_class_symbol_fqcn_map(meta, module_id, ctx.class_names, ctx.class_type_ids)

    # Emit body
    _emit_body(ctx, body)

    # Main guard
    if ctx.is_entry and len(main_guard) > 0:
        _emit_blank(ctx)
        _emit(ctx, "void __pytra_main_guard() {")
        ctx.indent_level += 1
        _emit_body(ctx, main_guard)
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # main() for entry
    if ctx.is_entry:
        _emit_blank(ctx)
        _emit(ctx, "int main(int argc, char** argv) {")
        ctx.indent_level += 1
        _emit(ctx, "pytra_configure_from_argv(argc, argv);")
        _emit(ctx, "set_argv(rc_list_from_value(py_runtime_argv()));")
        if len(main_guard) > 0:
            _emit(ctx, "__pytra_main_guard();")
        _emit(ctx, "return 0;")
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # Build header
    dep_ids = collect_cpp_dependency_module_ids(module_id, meta)

    for line in ctx.lines:
        if "::std::function<" in line:
            ctx.includes_needed.add("functional")
            break
    for line in ctx.lines:
        if (
            "py_upper(" in line
            or "py_lower(" in line
            or "py_strip(" in line
            or "py_lstrip(" in line
            or "py_rstrip(" in line
            or "py_split(" in line
            or "py_join(" in line
            or "py_startswith(" in line
            or "py_endswith(" in line
            or "py_replace(" in line
            or "py_find(" in line
            or "py_count(" in line
        ):
            ctx.includes_needed.add("built_in/string_ops.h")
            break

    header: list[str] = [
        "#include <cstdint>",
        "#include <string>",
        "#include <vector>",
        "#include <iostream>",
        "#include <stdexcept>",
        "#include <cmath>",
        '#include "core/py_runtime.h"',
        '#include "core/process_runtime.h"',
    ]
    if _module_needs_error_header(body):
        header.append('#include "built_in/error.h"')
    if "functional" in ctx.includes_needed:
        header.insert(6, "#include <functional>")
    if "built_in/format_ops.h" in ctx.includes_needed:
        header.append('#include "built_in/format_ops.h"')
    if "built_in/string_ops_fwd.h" in ctx.includes_needed:
        header.append('#include "built_in/string_ops_fwd.h"')

    seen_includes: set[str] = {"core/py_runtime.h"}
    if self_header != "":
        header.append('#include "' + self_header + '"')
    for dep_id in dep_ids:
        if dep_id == "" or dep_id == module_id:
            continue
        include_path = cpp_include_for_module(dep_id)
        if include_path == "" or include_path in seen_includes:
            continue
        seen_includes.add(include_path)
        header.append('#include "' + include_path + '"')

    header.extend([
        "",
        "// Generated by toolchain2/emit/cpp",
        "",
    ])

    return "\n".join(header + ctx.lines) + "\n"
