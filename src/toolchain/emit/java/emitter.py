"""EAST3 -> Java source emitter for toolchain."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.common.code_emitter import (
    RuntimeMapping,
    build_import_alias_map,
    build_runtime_import_map,
    load_runtime_mapping,
    resolve_runtime_call,
    resolve_runtime_symbol_name,
    should_skip_module,
)
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.emit.common.profile_loader import load_profile_doc
from toolchain.emit.java.types import _safe_java_ident
from toolchain.emit.java.types import _java_ref_type
from toolchain.emit.java.types import _split_generic_args
from toolchain.emit.java.types import java_module_class_name
from toolchain.emit.java.types import java_type
from toolchain.emit.java.types import java_zero_value
from toolchain.link.expand_defaults import expand_cross_module_defaults

_TYPE_ID_ALIAS_PREFIX = "_".join(["PYTRA", "TID", ""])


@dataclass
class EmitContext:
    module_id: str = ""
    source_path: str = ""
    is_entry: bool = False
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    var_types: dict[str, str] = field(default_factory=dict)
    current_return_type: str = ""
    current_class: str = ""
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    import_alias_modules: dict[str, str] = field(default_factory=dict)
    runtime_imports: dict[str, str] = field(default_factory=dict)
    class_names: set[str] = field(default_factory=set)
    class_bases: dict[str, str] = field(default_factory=dict)
    enum_like_names: set[str] = field(default_factory=set)
    function_names: set[str] = field(default_factory=set)
    class_property_methods: dict[str, set[str]] = field(default_factory=dict)
    module_fields: set[str] = field(default_factory=set)
    class_fields: dict[str, set[str]] = field(default_factory=dict)
    linked_type_ids: dict[str, int] = field(default_factory=dict)
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    current_exc_var: str = ""
    closure_helpers: dict[str, dict[str, JsonVal]] = field(default_factory=dict)
    function_varargs: dict[str, str] = field(default_factory=dict)
    active_varargs: set[str] = field(default_factory=set)
    expr_renderer: object | None = None
    stmt_renderer: object | None = None
    symbol_name_cache: dict[str, str] = field(default_factory=dict)
    function_signatures: dict[str, tuple[list[str], str]] = field(default_factory=dict)


def _emit(ctx: EmitContext, line: str) -> None:
    ctx.lines.append("    " * ctx.indent_level + line)


def _emit_blank(ctx: EmitContext) -> None:
    ctx.lines.append("")


def _str(node: JsonVal, key: str) -> str:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, str):
            return value
    return ""


def _bool(node: JsonVal, key: str) -> bool:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, bool):
            return value
    return False


def _list(node: JsonVal, key: str) -> list[JsonVal]:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, list):
            return value
    return []


def _dict(node: JsonVal, key: str) -> dict[str, JsonVal]:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _module_class_name(module_id: str) -> str:
    return java_module_class_name(module_id)


def _fqcn_to_tid_const(fqcn: str) -> str:
    chars: list[str] = []
    prev_was_lower_or_digit = False
    for ch in fqcn.replace(".", "_"):
        if ch.isupper() and prev_was_lower_or_digit:
            chars.append("_")
        if ch.isalnum() or ch == "_":
            chars.append(ch.upper())
        else:
            chars.append("_")
        prev_was_lower_or_digit = ch.islower() or ch.isdigit()
    return "".join(chars) + "_TID"


def _java_symbol_name(ctx: EmitContext, name: str) -> str:
    cached = ctx.symbol_name_cache.get(name, "")
    if cached != "":
        return cached
    if name == "self":
        ctx.symbol_name_cache[name] = "this"
        return "this"
    mapped = ctx.renamed_symbols.get(name, "")
    if mapped != "":
        resolved = _safe_java_ident(mapped)
        ctx.symbol_name_cache[name] = resolved
        return resolved
    if ctx.module_id != "pytra.built_in.type_id_table":
        if name.find(_TYPE_ID_ALIAS_PREFIX) == 0:
            alias = name[len(_TYPE_ID_ALIAS_PREFIX):] + "_TID"
            resolved = _module_class_name("pytra.built_in.type_id_table") + "." + _safe_java_ident(alias)
            ctx.symbol_name_cache[name] = resolved
            return resolved
        if name.endswith("_TID"):
            resolved = _module_class_name("pytra.built_in.type_id_table") + "." + _safe_java_ident(name)
            ctx.symbol_name_cache[name] = resolved
            return resolved
    if name in ctx.runtime_imports:
        resolved = ctx.runtime_imports[name]
        ctx.symbol_name_cache[name] = resolved
        return resolved
    resolved = _safe_java_ident(name)
    ctx.symbol_name_cache[name] = resolved
    return resolved


def _tid_symbol_name(ctx: EmitContext, type_name: str) -> str:
    builtin_tid_names: dict[str, str] = {
        "None": "NONE_TID",
        "none": "NONE_TID",
        "bool": "BOOL_TID",
        "int": "INT_TID",
        "int8": "INT_TID",
        "int16": "INT_TID",
        "int32": "INT_TID",
        "int64": "INT_TID",
        "uint8": "INT_TID",
        "uint16": "INT_TID",
        "uint32": "INT_TID",
        "uint64": "INT_TID",
        "float": "FLOAT_TID",
        "float32": "FLOAT_TID",
        "float64": "FLOAT_TID",
        "str": "STR_TID",
        "list": "LIST_TID",
        "dict": "DICT_TID",
        "set": "SET_TID",
        "object": "OBJECT_TID",
        "Obj": "OBJECT_TID",
        "Any": "OBJECT_TID",
        "JsonVal": "OBJECT_TID",
    }
    if type_name in builtin_tid_names:
        return _module_class_name("pytra.built_in.type_id_table") + "." + builtin_tid_names[type_name]
    return _java_symbol_name(ctx, type_name)


def _effective_type(node: JsonVal) -> str:
    if isinstance(node, dict):
        return _str(node, "resolved_type")
    return ""


def _node_type(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    resolved = _str(node, "resolved_type")
    if resolved != "":
        return resolved
    if _str(node, "kind") == "Name":
        return ctx.var_types.get(_java_symbol_name(ctx, _str(node, "id")), "")
    return ""


def _is_list_type(resolved_type: str) -> bool:
    return resolved_type == "list" or resolved_type.startswith("list[") or resolved_type in ("bytes", "bytearray")


def _is_dict_type(resolved_type: str) -> bool:
    return resolved_type == "dict" or resolved_type.startswith("dict[") or resolved_type in ("Node", "dict[str,Any]")


def _is_set_type(resolved_type: str) -> bool:
    return resolved_type == "set" or resolved_type.startswith("set[")


def _is_deque_type(resolved_type: str) -> bool:
    return resolved_type == "deque"


def _is_int_type(resolved_type: str) -> bool:
    return resolved_type in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64")


def _is_float_type(resolved_type: str) -> bool:
    return resolved_type in ("float", "float32", "float64")


def _is_dynamic_type(resolved_type: str) -> bool:
    return resolved_type in ("", "Any", "Obj", "object", "unknown", "JsonVal")


def _java_type_in_ctx(ctx: EmitContext, resolved_type: str, *, allow_void: bool = False) -> str:
    if resolved_type in ctx.enum_like_names:
        return "long"
    if resolved_type in ctx.class_names or resolved_type in ctx.class_bases:
        return _safe_java_ident(resolved_type)
    return java_type(resolved_type, ctx.mapping.types, allow_void=allow_void)


def _linked_type_id(ctx: EmitContext, resolved_type: str) -> int | None:
    if resolved_type in ctx.linked_type_ids:
        return ctx.linked_type_ids[resolved_type]
    fqcn = ctx.module_id + "." + resolved_type
    if fqcn in ctx.linked_type_ids:
        return ctx.linked_type_ids[fqcn]
    return None


def _optional_inner_type(resolved_type: str) -> str:
    text = resolved_type.strip()
    for delim in (" | None", "|None", "None | ", "None|"):
        if delim in text:
            if text.startswith("None"):
                return text.split("|", 1)[1].strip()
            return text.split("|", 1)[0].strip()
    return ""


def _parse_callable_type(resolved_type: str) -> tuple[list[str], str] | None:
    inner_optional = _optional_inner_type(resolved_type)
    if inner_optional != "":
        resolved_type = inner_optional
    if not resolved_type.startswith("callable[") or not resolved_type.endswith("]"):
        return None
    inner = resolved_type[len("callable["):-1]
    depth = 0
    split_at = -1
    for idx, ch in enumerate(inner):
        if ch == "[":
            depth += 1
            continue
        if ch == "]":
            depth -= 1
            continue
        if ch == "," and depth == 0:
            split_at = idx
            break
    if split_at <= 0:
        return None
    args_part = inner[:split_at].strip()
    return_type = inner[split_at + 1:].strip()
    if not args_part.startswith("[") or not args_part.endswith("]"):
        return None
    args_text = args_part[1:-1].strip()
    if args_text == "":
        return ([], return_type)
    return (_split_generic_args(args_text), return_type)


def _normalized_callable_type(resolved_type: str) -> str:
    inner_optional = _optional_inner_type(resolved_type)
    if inner_optional != "" and _parse_callable_type(inner_optional) is not None:
        return inner_optional
    if _parse_callable_type(resolved_type) is not None:
        return resolved_type
    return ""


def _callable_type_for_node(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    resolved = _normalized_callable_type(_str(node, "resolved_type"))
    if resolved != "":
        return resolved
    if _str(node, "kind") == "Name":
        raw_name = _str(node, "id")
        mapped = _java_symbol_name(ctx, raw_name)
        stored = _normalized_callable_type(ctx.var_types.get(mapped, ""))
        if stored != "":
            return stored
        return _normalized_callable_type(ctx.var_types.get(raw_name, ""))
    return ""


def _collect_callable_types(node: JsonVal, out: set[str]) -> None:
    if isinstance(node, dict):
        for key in ("resolved_type", "decl_type", "return_type"):
            value = _str(node, key)
            normalized = _normalized_callable_type(value)
            if normalized != "":
                out.add(normalized)
        for value in node.values():
            _collect_callable_types(value, out)
        return
    if isinstance(node, list):
        for item in node:
            _collect_callable_types(item, out)


def _emit_callable_interfaces(ctx: EmitContext, root: JsonVal) -> None:
    callable_types: set[str] = set()
    _collect_callable_types(root, callable_types)
    for callable_type in sorted(callable_types):
        parsed = _parse_callable_type(callable_type)
        if parsed is None:
            continue
        arg_types, return_type = parsed
        iface_name = _safe_java_ident(callable_type)
        params: list[str] = []
        for idx, arg_type in enumerate(arg_types):
            params.append(_java_type_in_ctx(ctx, arg_type) + " arg" + str(idx))
        _emit(ctx, "@FunctionalInterface")
        _emit(ctx, "public interface " + iface_name + " {")
        ctx.indent_level += 1
        _emit(ctx, _java_type_in_ctx(ctx, return_type, allow_void=True) + " invoke(" + ", ".join(params) + ");")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit_blank(ctx)


def _emit_callable_bridge(ctx: EmitContext, callable_node: dict[str, JsonVal], target_code: str) -> str:
    parsed = _parse_callable_type(_callable_type_for_node(ctx, callable_node))
    if parsed is None:
        return target_code
    return _emit_callable_bridge_for_type(parsed, target_code)


def _emit_callable_bridge_for_type(parsed: tuple[list[str], str], target_code: str) -> str:
    arg_types, _return_type = parsed
    params: list[str] = []
    call_args: list[str] = []
    for idx, _arg_type in enumerate(arg_types):
        param = "arg" + str(idx)
        params.append(param)
        call_args.append(param)
    return "(" + ", ".join(params) + ") -> " + target_code + "(" + ", ".join(call_args) + ")"


def _wrap_callable_arg(ctx: EmitContext, arg_node: JsonVal, rendered: str) -> str:
    if not isinstance(arg_node, dict):
        return rendered
    node = arg_node
    while isinstance(node, dict) and _str(node, "kind") in ("Box", "Unbox"):
        inner = node.get("value")
        if not isinstance(inner, dict):
            break
        node = inner
    resolved_type = _callable_type_for_node(ctx, node)
    parsed = _parse_callable_type(resolved_type)
    callableish = parsed is not None or resolved_type in ("Callable", "callable") or _str(node, "call_arg_type") in ("Callable", "callable")
    if not callableish:
        return rendered
    kind = _str(node, "kind")
    if kind == "Name":
        name = _str(node, "id")
        mapped_name = _java_symbol_name(ctx, name)
        if name in ctx.function_names or mapped_name in ctx.function_names:
            sig = ctx.function_signatures.get(name)
            if sig is None:
                sig = ctx.function_signatures.get(mapped_name)
            if sig is not None:
                arg_types, _return_type = sig
                if len(arg_types) == 0:
                    if parsed is None:
                        return "(__unused) -> { " + mapped_name + "(); return null; }"
                    return "() -> " + mapped_name + "()"
                params: list[str] = []
                call_args: list[str] = []
                for idx, arg_type in enumerate(arg_types):
                    param = "arg" + str(idx)
                    params.append(param)
                    if parsed is None:
                        call_args.append(_emit_cast_expr(ctx, arg_type, param))
                    else:
                        call_args.append(param)
                return "(" + ", ".join(params) + ") -> " + mapped_name + "(" + ", ".join(call_args) + ")"
            return rendered
        if parsed is not None:
            return _emit_callable_bridge_for_type(parsed, mapped_name + ".invoke")
        return rendered
    if kind == "Attribute":
        if parsed is not None:
            return _emit_callable_bridge_for_type(parsed, _emit_attribute(ctx, node))
        return rendered
    return rendered


def _wrap_callable_args(ctx: EmitContext, arg_nodes: list[JsonVal], rendered_args: list[str]) -> list[str]:
    adjusted: list[str] = []
    for idx, rendered in enumerate(rendered_args):
        arg_node = arg_nodes[idx] if idx < len(arg_nodes) else None
        adjusted.append(_wrap_callable_arg(ctx, arg_node, rendered))
    return adjusted


def _emit_iterable_cast(ctx: EmitContext, iter_node: JsonVal, elem_type: str) -> str:
    iter_code = _emit_expr(ctx, iter_node)
    elem_ref = _java_ref_type(elem_type, ctx.mapping.types)
    if isinstance(iter_node, dict) and _str(iter_node, "kind") == "Name":
        iter_name = _str(iter_node, "id")
        if iter_name in ctx.active_varargs:
            return "((java.util.List<" + elem_ref + ">) java.util.Arrays.asList(" + iter_code + "))"
    return "((java.util.List<" + elem_ref + ">) (java.util.List<?>) PyRuntime.pyIter(" + iter_code + "))"


def _tuple_target_elements(target_node: JsonVal) -> list[tuple[str, str]]:
    if not isinstance(target_node, dict) or _str(target_node, "kind") != "Tuple":
        return []
    out: list[tuple[str, str]] = []
    for elem in _list(target_node, "elements"):
        if not isinstance(elem, dict):
            continue
        name = _str(elem, "id")
        if name == "":
            continue
        elem_type = _str(elem, "resolved_type")
        if elem_type == "":
            elem_type = "Object"
        out.append((_safe_java_ident(name), elem_type))
    return out


def _emit_comp_loops(ctx: EmitContext, generators: list[JsonVal], index: int, leaf_stmt: str) -> str:
    if index >= len(generators):
        return leaf_stmt
    gen = generators[index]
    if not isinstance(gen, dict):
        return leaf_stmt
    target_node = gen.get("target")
    tuple_targets = _tuple_target_elements(target_node)
    if len(tuple_targets) > 0:
        tuple_type = _str(target_node, "resolved_type")
        if tuple_type == "":
            tuple_type = "tuple"
        target_name = "_pytra_comp_item_" + str(index) + "_" + str(abs(id(gen)))
        saved = dict(ctx.var_types)
        for tuple_name, tuple_type_name in tuple_targets:
            ctx.var_types[tuple_name] = tuple_type_name
        inner = _emit_comp_loops(ctx, generators, index + 1, leaf_stmt)
        tuple_bindings: list[str] = []
        for tuple_index, (tuple_name, tuple_type_name) in enumerate(tuple_targets):
            tuple_bindings.append(
                _java_type_in_ctx(ctx, tuple_type_name)
                + " "
                + tuple_name
                + " = "
                + _emit_cast_expr(ctx, tuple_type_name, "PyRuntime.pyGet(" + target_name + ", " + str(tuple_index) + "L)")
                + ";"
            )
        filters = [_emit_expr(ctx, cond) for cond in _list(gen, "ifs") if isinstance(cond, dict)]
        parts = tuple_bindings + ([inner] if len(filters) == 0 else ["if (" + " && ".join(filters) + ") { " + inner + " }"])
        ctx.var_types = saved
        return "for (" + _java_type_in_ctx(ctx, tuple_type) + " " + target_name + " : " + _emit_iterable_cast(ctx, gen.get("iter"), tuple_type) + ") { " + " ".join(parts) + " }"
    target_name, target_type = _for_target_name(target_node)
    saved = dict(ctx.var_types)
    ctx.var_types[target_name] = target_type
    inner = _emit_comp_loops(ctx, generators, index + 1, leaf_stmt)
    filters = [_emit_expr(ctx, cond) for cond in _list(gen, "ifs") if isinstance(cond, dict)]
    if len(filters) > 0:
        inner = "if (" + " && ".join(filters) + ") { " + inner + " }"
    ctx.var_types = saved
    return "for (" + _java_type_in_ctx(ctx, target_type) + " " + target_name + " : " + _emit_iterable_cast(ctx, gen.get("iter"), target_type) + ") { " + inner + " }"


def _emit_condition_expr(ctx: EmitContext, node: JsonVal) -> str:
    expr = _emit_expr(ctx, node)
    rt = _node_type(ctx, node)
    if rt == "bool":
        return expr
    return "PyRuntime.pyBool(" + expr + ")"


def _emit_comp_expr(ctx: EmitContext, node: dict[str, JsonVal], result_type: str, init_expr: str, leaf_stmt: str) -> str:
    token = str(abs(id(node)))
    result_name = "_pytra_comp_" + token
    supplier_type = result_type
    body = _emit_comp_loops(ctx, _list(node, "generators"), 0, leaf_stmt.replace("__RESULT__", result_name))
    return "((java.util.function.Supplier<" + supplier_type + ">) () -> { " + supplier_type + " " + result_name + " = " + init_expr + "; " + body + " return " + result_name + "; }).get()"


def _emit_range_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    start = node.get("start")
    stop = node.get("stop")
    step = node.get("step")
    start_code = _emit_cast_expr(ctx, "int64", _emit_expr(ctx, start)) if isinstance(start, dict) else "0L"
    stop_code = _emit_cast_expr(ctx, "int64", _emit_expr(ctx, stop)) if isinstance(stop, dict) else "0L"
    step_code = _emit_cast_expr(ctx, "int64", _emit_expr(ctx, step)) if isinstance(step, dict) else "1L"
    return "PyRuntime.pyRange((int) (" + start_code + "), (int) (" + stop_code + "), (int) (" + step_code + "))"


def _call_yields_dynamic(node: dict[str, JsonVal]) -> bool:
    return _bool(node, "yields_dynamic")


def _maybe_cast_dynamic_call(ctx: EmitContext, node: dict[str, JsonVal], expr: str) -> str:
    if not _call_yields_dynamic(node):
        return expr
    result_type = _str(node, "resolved_type")
    if _is_dynamic_type(result_type):
        return expr
    return _emit_cast_expr(ctx, result_type, expr)


def _emit_container_method_call(ctx: EmitContext, owner_node: JsonVal, arg_strs: list[str], node: dict[str, JsonVal], fn_name: str) -> str:
    owner = _emit_expr(ctx, owner_node)
    owner_access = "(" + owner + ")"
    owner_type = _node_type(ctx, owner_node)
    call_type = _str(node, "resolved_type")
    if fn_name != "":
        special = _emit_builtin_placeholder(ctx, fn_name, [owner] + arg_strs, node)
        if special != "":
            return special
        if _is_list_type(owner_type) or _is_deque_type(owner_type) or _is_set_type(owner_type) or owner_type == "str":
            if fn_name == "PyRuntime.pyListIndex" and len(arg_strs) >= 1:
                return "PyRuntime.pyListIndex(" + owner_access + ", " + arg_strs[0] + ")"
            if fn_name == "PyRuntime.pyPop":
                idx_expr = arg_strs[0] if len(arg_strs) >= 1 else "null"
                popped = "PyRuntime.pyPop(" + owner_access + ", " + idx_expr + ")"
                if call_type != "" and not _is_dynamic_type(call_type):
                    return _emit_cast_expr(ctx, call_type, popped)
                return popped
            return fn_name + "(" + ", ".join([owner] + arg_strs) + ")"
    if _is_dict_type(owner_type) or _is_dynamic_type(owner_type):
        attr = _str(_unwrap_node(node.get("func")), "attr")
        if attr == "get":
            if _is_dynamic_type(owner_type):
                owner_access = "((HashMap<Object, Object>) (" + owner + "))"
            if len(arg_strs) >= 2:
                return _maybe_cast_dynamic_call(
                    ctx,
                    node,
                    "PyRuntime.__pytra_dict_get_default(" + owner_access + ", " + arg_strs[0] + ", " + arg_strs[1] + ")",
                )
            if len(arg_strs) >= 1:
                return _maybe_cast_dynamic_call(ctx, node, owner_access + ".get(" + arg_strs[0] + ")")
        if attr == "keys":
            if _is_dynamic_type(owner_type):
                owner_access = "((HashMap<Object, Object>) (" + owner + "))"
            jt = _java_type_in_ctx(ctx, call_type)
            return "(" + jt + ") (ArrayList<?>) PyRuntime.pyDictKeys(" + owner_access + ")"
        if attr == "values":
            if _is_dynamic_type(owner_type):
                owner_access = "((HashMap<Object, Object>) (" + owner + "))"
            jt = _java_type_in_ctx(ctx, call_type)
            return "(" + jt + ") (ArrayList<?>) PyRuntime.pyDictValues(" + owner_access + ")"
        if attr == "items":
            if _is_dynamic_type(owner_type):
                owner_access = "((HashMap<Object, Object>) (" + owner + "))"
            jt = _java_type_in_ctx(ctx, call_type)
            return "(" + jt + ") (ArrayList<?>) PyRuntime.pyDictItems(" + owner_access + ")"
    return ""


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    if len(values) == 0:
        return "false"
    if len(values) == 1:
        return _emit_expr(ctx, values[0])
    op = _str(node, "op")
    first = _emit_expr(ctx, values[0])
    rest_node: dict[str, JsonVal] = {"kind": "BoolOp", "op": op, "values": values[1:]}
    rest = _emit_boolop(ctx, rest_node)
    if op == "And":
        return "(PyRuntime.pyBool(" + first + ") ? " + rest + " : " + first + ")"
    return "(PyRuntime.pyBool(" + first + ") ? " + first + " : " + rest + ")"


class _JavaExprRenderer(CommonRenderer):
    def __init__(self, ctx: EmitContext) -> None:
        self.ctx = ctx
        super().__init__("java")
        self.profile = load_profile_doc("java")
        operators = self.profile.get("operators")
        precedence = operators.get("precedence") if isinstance(operators, dict) else None
        self._op_prec_table = {}
        if isinstance(precedence, dict):
            for key, value in precedence.items():
                if isinstance(key, str) and isinstance(value, int):
                    self._op_prec_table[key] = value

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(node)

    def render_binop(self, node: dict[str, JsonVal]) -> str:
        op = _str(node, "op")
        left_node = node.get("left")
        right_node = node.get("right")
        left = self.render_expr(node.get("left"))
        right = self.render_expr(node.get("right"))
        if op == "Div":
            return "(((double) (" + left + ")) / ((double) (" + right + ")))"
        if op == "FloorDiv":
            result = "PyRuntime.pyFloorDiv(" + left + ", " + right + ")"
            result_type = _str(node, "resolved_type")
            if result_type != "" and not _is_dynamic_type(result_type):
                return _emit_cast_expr(self.ctx, result_type, result)
            return result
        if op == "Mod":
            result = "PyRuntime.pyMod(" + left + ", " + right + ")"
            result_type = _str(node, "resolved_type")
            if result_type != "" and not _is_dynamic_type(result_type):
                return _emit_cast_expr(self.ctx, result_type, result)
            return result
        if op == "Pow":
            return "Math.pow(" + left + ", " + right + ")"
        if op == "Add":
            left_type = _effective_type(left_node)
            right_type = _effective_type(right_node)
            if _is_list_type(left_type) and _is_list_type(right_type):
                return "PyRuntime.__pytra_list_concat(" + left + ", " + right + ")"
        if op == "Mult":
            left_type = _effective_type(left_node)
            right_type = _effective_type(right_node)
            if _is_list_type(left_type) and _is_int_type(right_type):
                return "PyRuntime.__pytra_repeat_list(" + left + ", " + right + ")"
            if _is_list_type(right_type) and _is_int_type(left_type):
                return "PyRuntime.__pytra_repeat_list(" + right + ", " + left + ")"
        op_text = self._operator_text("bin", op, op)
        return "(" + left + " " + op_text + " " + right + ")"

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_compare(self, node: dict[str, JsonVal]) -> str:
        return _emit_compare(self.ctx, node)

    def render_boolop(self, node: dict[str, JsonVal]) -> str:
        return _emit_boolop(self.ctx, node)

    def render_condition_expr(self, node: JsonVal) -> str:
        return _emit_condition_expr(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("java common renderer assign hook is not used directly")

    def render_expr_extension(self, node: dict[str, JsonVal]) -> str:
        return _emit_expr_extension(self.ctx, node)


class _JavaStmtRenderer(CommonRenderer):
    def __init__(self, ctx: EmitContext) -> None:
        self.ctx = ctx
        super().__init__("java")
        self.profile = load_profile_doc("java")
        operators = self.profile.get("operators")
        precedence = operators.get("precedence") if isinstance(operators, dict) else None
        self._op_prec_table = {}
        if isinstance(precedence, dict):
            for key, value in precedence.items():
                if isinstance(key, str) and isinstance(value, int):
                    self._op_prec_table[key] = value
        self.state.lines = ctx.lines
        self.state.indent_level = ctx.indent_level

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(node)

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_compare(self, node: dict[str, JsonVal]) -> str:
        return _emit_compare(self.ctx, node)

    def render_boolop(self, node: dict[str, JsonVal]) -> str:
        return _emit_boolop(self.ctx, node)

    def render_condition_expr(self, node: JsonVal) -> str:
        return _emit_condition_expr(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("java common renderer assign hook is not used directly")

    def emit_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        if _str(node, "kind") == "AnnAssign":
            _emit_ann_assign(self.ctx, node)
        else:
            _emit_assign(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_expr_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        value = node.get("value")
        if isinstance(value, dict) and _str(value, "kind") == "Name":
            control_name = _str(value, "id")
            if control_name == "continue":
                _emit(ctx=self.ctx, line="continue;")
                self.state.indent_level = self.ctx.indent_level
                return
            if control_name == "break":
                _emit(ctx=self.ctx, line="break;")
                self.state.indent_level = self.ctx.indent_level
                return
        if isinstance(value, dict) and _str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
            self.state.indent_level = self.ctx.indent_level
            return
        if isinstance(value, dict) and _str(value, "kind") == "Call":
            fn_name = _runtime_call_name(self.ctx, value, value.get("func"))
            if fn_name == "PyRuntime.pyPop":
                args = _list(value, "args")
                arg_strs = [_emit_expr(self.ctx, arg) for arg in args]
                runtime_owner = value.get("runtime_owner")
                if isinstance(runtime_owner, dict) and not _is_module_owner(self.ctx, runtime_owner):
                    arg_strs = [_emit_expr(self.ctx, runtime_owner)] + arg_strs
                _emit(ctx=self.ctx, line=fn_name + "(" + ", ".join(arg_strs) + ");")
                self.state.indent_level = self.ctx.indent_level
                return
        _emit(ctx=self.ctx, line=_emit_expr(self.ctx, value) + ";")
        self.state.indent_level = self.ctx.indent_level

    def emit_return_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_return(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def render_raise_value(self, node: dict[str, JsonVal]) -> str:
        exc = node.get("exc")
        if not isinstance(exc, dict):
            exc = node.get("value")
        if not isinstance(exc, dict):
            return self.ctx.current_exc_var
        return _emit_expr(self.ctx, exc)

    def render_except_open(self, handler: dict[str, JsonVal]) -> str:
        name = _str(handler, "name")
        if name == "":
            name = "err"
        type_name = "RuntimeException"
        type_node = handler.get("type")
        if isinstance(type_node, dict):
            if _str(type_node, "kind") == "Name":
                type_name = _java_type_in_ctx(self.ctx, _str(type_node, "id"))
            else:
                type_name = _java_type_in_ctx(self.ctx, _str(type_node, "resolved_type"))
        return "catch (" + type_name + " " + _safe_java_ident(name) + ") {"

    def emit_try_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        body = _list(node, "body")
        handlers = _list(node, "handlers")
        finalbody = _list(node, "finalbody")
        self._emit("try {")
        self.state.indent_level += 1
        self.emit_body(body)
        self.state.indent_level -= 1
        self._emit("}")
        for raw_handler in handlers:
            if not isinstance(raw_handler, dict):
                continue
            prev_exc_var = self.ctx.current_exc_var
            self.ctx.current_exc_var = _safe_java_ident(_str(raw_handler, "name") or "err")
            self._emit(self.render_except_open(raw_handler))
            self.state.indent_level += 1
            self.emit_try_handler_body(raw_handler)
            self.state.indent_level -= 1
            self._emit("}")
            self.ctx.current_exc_var = prev_exc_var
        if len(finalbody) > 0:
            self._emit("finally {")
            self.state.indent_level += 1
            self.emit_body(finalbody)
            self.state.indent_level -= 1
            self._emit("}")
        self.ctx.indent_level = self.state.indent_level

    def emit_stmt_extension(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level


def _emit_expr(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return "null"
    renderer = ctx.expr_renderer
    if not isinstance(renderer, _JavaExprRenderer):
        renderer = _JavaExprRenderer(ctx)
        ctx.expr_renderer = renderer
    return renderer.render_expr(node)


def _emit_name(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    raw_name = _str(node, "id")
    rendered = _java_symbol_name(ctx, raw_name)
    name_type = _callable_type_for_node(ctx, node)
    if _parse_callable_type(name_type) is not None and (raw_name in ctx.function_names or rendered in ctx.function_names):
        return _wrap_callable_arg(ctx, node, rendered)
    original_type = ctx.var_types.get(rendered, "")
    if original_type == "":
        original_type = ctx.var_types.get(raw_name, "")
    if original_type == "" or name_type == "" or name_type == original_type:
        return rendered
    if _java_type_in_ctx(ctx, original_type) != "Object":
        return rendered
    if _java_type_in_ctx(ctx, name_type) == "Object":
        return rendered
    return _emit_cast_expr(ctx, name_type, rendered)


def _coerce_callable_assignment(ctx: EmitContext, value: JsonVal, target_type: str, value_code: str) -> str:
    normalized = _normalized_callable_type(target_type)
    parsed = _parse_callable_type(normalized)
    if parsed is None or not isinstance(value, dict):
        return value_code
    kind = _str(value, "kind")
    if kind == "Name":
        raw_name = _str(value, "id")
        rendered = _java_symbol_name(ctx, raw_name)
        if raw_name in ctx.function_names or rendered in ctx.function_names:
            return _emit_callable_bridge_for_type(parsed, rendered)
        return value_code
    if kind == "Attribute":
        return _emit_callable_bridge_for_type(parsed, _emit_attribute(ctx, value))
    return value_code


def _emit_constant(node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"'
    if isinstance(value, int):
        return str(value) + "L"
    return str(value)


def _unwrap_node(node: JsonVal) -> JsonVal:
    current = node
    while isinstance(current, dict) and _str(current, "kind") in ("Box", "Unbox"):
        inner = current.get("value")
        if not isinstance(inner, dict):
            break
        current = inner
    return current

def _module_owner_info(ctx: EmitContext, owner_node: JsonVal) -> tuple[bool, str, str]:
    node = _unwrap_node(owner_node)
    if not isinstance(node, dict):
        return (False, "", "")
    kind = _str(node, "kind")
    runtime_module_id = _str(node, "runtime_module_id")
    if runtime_module_id != "" and kind in ("Name", "Attribute"):
        owner_key = _str(node, "repr")
        if owner_key == "" and _str(node, "kind") == "Name":
            owner_key = _str(node, "id")
        return (True, owner_key, runtime_module_id)
    if _str(node, "kind") == "Name":
        owner_id = _str(node, "id")
        if owner_id in ctx.import_alias_modules:
            return (True, owner_id, ctx.import_alias_modules[owner_id])
    return (False, "", "")


def _is_module_owner(ctx: EmitContext, owner_node: JsonVal) -> bool:
    is_module, _owner_key, _module_id = _module_owner_info(ctx, owner_node)
    return is_module


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr = _str(node, "attr")
    if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Call":
        owner_func = owner_node.get("func")
        if isinstance(owner_func, dict) and _str(owner_func, "kind") == "Name" and _str(owner_func, "id") == "super":
            return "super." + _safe_java_ident(attr)
        if attr == "__name__" and isinstance(owner_func, dict) and _str(owner_func, "kind") == "Name" and _str(owner_func, "id") == "type":
            type_args = _list(owner_node, "args")
            if len(type_args) >= 1:
                return "PyRuntime.pyTypeName(" + _emit_expr(ctx, type_args[0]) + ")"
    is_module_owner, owner_key, owner_module_id = _module_owner_info(ctx, owner_node)
    if is_module_owner:
        mod_id = _str(node, "runtime_module_id")
        if mod_id == "":
            mod_id = owner_module_id
        qualified = _str(node, "repr")
        if qualified == "":
            qualified = owner_key + "." + attr if owner_key != "" else attr
        if qualified in ctx.mapping.calls:
            return ctx.mapping.calls[qualified]
        if should_skip_module(mod_id, ctx.mapping):
            resolved = resolve_runtime_symbol_name(
                attr,
                ctx.mapping,
                module_id=mod_id,
                resolved_runtime_call=_str(node, "resolved_runtime_call"),
                runtime_call=_str(node, "runtime_call"),
            )
            if resolved != "":
                return resolved
    owner = _emit_expr(ctx, owner_node)
    owner_access = owner
    if owner not in ("this", "super") and (" " in owner or owner.startswith("(") or owner.endswith(")")):
        owner_access = "(" + owner + ")"
    owner_type = _node_type(ctx, owner_node)
    if _str(node, "attribute_access_kind") == "property_getter" or attr in ctx.class_property_methods.get(owner_type, set()):
        if owner_access == "this":
            return "this." + _safe_java_ident(attr) + "()"
        return owner_access + "." + _safe_java_ident(attr) + "()"
    if owner_access == "this":
        return "this." + _safe_java_ident(attr)
    return owner_access + "." + _safe_java_ident(attr)


def _emit_expr_extension(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    kind = _str(node, "kind")
    if kind == "List":
        elements = [_emit_expr(ctx, elem) for elem in _list(node, "elements")]
        if len(elements) == 0:
            return "new ArrayList<>()"
        return "new ArrayList<>(java.util.Arrays.asList(" + ", ".join(elements) + "))"
    if kind == "Tuple":
        elements = [_emit_expr(ctx, elem) for elem in _list(node, "elements")]
        if len(elements) == 0:
            return "new ArrayList<>()"
        return "new ArrayList<>(java.util.Arrays.asList(" + ", ".join(elements) + "))"
    if kind == "Set":
        elements = [_emit_expr(ctx, elem) for elem in _list(node, "elements")]
        if len(elements) == 0:
            return "new HashSet<>()"
        return "new HashSet<>(java.util.Arrays.asList(" + ", ".join(elements) + "))"
    if kind == "Dict":
        entries = _list(node, "entries")
        if len(entries) == 0:
            return "new HashMap<>()"
        parts: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            parts.append(_emit_expr(ctx, entry.get("key")))
            parts.append(_emit_expr(ctx, entry.get("value")))
        dict_expr = "PyRuntime.__pytra_dict_of(" + ", ".join(parts) + ")"
        resolved_type = _str(node, "resolved_type")
        if resolved_type.startswith("dict["):
            return "(HashMap) " + dict_expr
        return dict_expr
    if kind == "Subscript":
        owner = _emit_expr(ctx, node.get("value"))
        slice_node = node.get("slice")
        if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
            lower = slice_node.get("lower")
            upper = slice_node.get("upper")
            lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "null"
            upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else "null"
            return "(" + _java_type_in_ctx(ctx, _str(node, "resolved_type")) + ") PyRuntime.pySlice(" + owner + ", " + lower_code + ", " + upper_code + ")"
        index = _emit_expr(ctx, slice_node)
        return "(" + _java_type_in_ctx(ctx, _str(node, "resolved_type")) + ") PyRuntime.pyGet(" + owner + ", " + index + ")"
    if kind == "IfExp":
        body_node = node.get("body")
        orelse_node = node.get("orelse")
        body_code = _emit_expr(ctx, body_node)
        orelse_code = _emit_expr(ctx, orelse_node)
        result_type = _str(node, "resolved_type")
        if not _is_dynamic_type(result_type) and result_type != "bool":
            body_type = _node_type(ctx, body_node)
            orelse_type = _node_type(ctx, orelse_node)
            if body_code != "null" and body_type != result_type:
                body_code = _emit_cast_expr(ctx, result_type, body_code)
            if orelse_code != "null" and orelse_type != result_type:
                orelse_code = _emit_cast_expr(ctx, result_type, orelse_code)
        return "(" + _emit_condition_expr(ctx, node.get("test")) + " ? " + body_code + " : " + orelse_code + ")"
    if kind == "Lambda":
        return _emit_lambda(ctx, node)
    if kind == "IsInstance":
        pod_exact_types = {
            "bool",
            "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
            "float32", "float64",
        }
        expected_name = _str(node, "expected_type_name")
        expected_node = node.get("expected_type_id")
        if isinstance(expected_node, dict):
            expected_name = _str(expected_node, "id")
            if expected_name == "":
                expected_name = _str(expected_node, "type_object_of")
        if expected_name in ctx.class_names or expected_name in ctx.class_bases:
            value_expr = _emit_expr(ctx, node.get("value"))
            return "(((Object) (" + value_expr + ")) instanceof " + _safe_java_ident(expected_name) + ")"
        value_expr = "PyRuntime.pyRuntimeValueTypeId(" + _emit_expr(ctx, node.get("value")) + ")"
        if isinstance(expected_node, dict):
            expected_tid = _str(expected_node, "id")
            actual_type = _node_type(ctx, node.get("value"))
            if actual_type in pod_exact_types and expected_tid in pod_exact_types:
                return "true" if actual_type == expected_tid else "false"
            if expected_tid == "":
                expected_type = _str(expected_node, "type_object_of")
                if expected_type != "":
                    expected_tid = _module_class_name("pytra.built_in.type_id_table") + "." + _fqcn_to_tid_const(expected_type)
            else:
                expected_tid = _tid_symbol_name(ctx, expected_tid)
            if expected_tid != "":
                return "PyRuntime.pytraIsinstance(" + value_expr + ", " + expected_tid + ")"
        return "false"
    if kind == "ObjTypeId":
        return "PyRuntime.pyRuntimeValueTypeId(" + _emit_expr(ctx, node.get("value")) + ")"
    if kind == "JoinedStr":
        values = _list(node, "values")
        if len(values) == 0:
            return "\"\""
        parts: list[str] = []
        for value in values:
            if not isinstance(value, dict):
                continue
            if _str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
                parts.append(_emit_constant(value))
            elif _str(value, "kind") == "FormattedValue":
                parts.append(_emit_expr(ctx, value))
            else:
                parts.append("PyRuntime.pyToString(" + _emit_expr(ctx, value) + ")")
        if len(parts) == 0:
            return "\"\""
        return "(" + " + ".join(parts) + ")"
    if kind == "FormattedValue":
        format_spec = _str(node, "format_spec")
        if format_spec == "":
            return "PyRuntime.pyToString(" + _emit_expr(ctx, node.get("value")) + ")"
        return "PyRuntime.pyFormat(" + _emit_expr(ctx, node.get("value")) + ", " + _emit_constant({"value": format_spec}) + ")"
    if kind == "Unbox":
        target_type = _str(node, "resolved_type")
        if "|" in target_type:
            return _emit_expr(ctx, node.get("value"))
        return _emit_cast_expr(ctx, target_type, _emit_expr(ctx, node.get("value")))
    if kind == "Box":
        return _emit_expr(ctx, node.get("value"))
    if kind == "Slice":
        lower = node.get("lower")
        upper = node.get("upper")
        lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "null"
        upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else "null"
        return "PyRuntime.pySlice(__obj__, " + lower_code + ", " + upper_code + ")"
    if kind == "ListComp":
        return _emit_comp_expr(
            ctx,
            node,
            _java_type_in_ctx(ctx, _str(node, "resolved_type")),
            "new ArrayList<>()",
            "__RESULT__.add(" + _emit_expr(ctx, node.get("elt")) + ");",
        )
    if kind == "SetComp":
        return _emit_comp_expr(
            ctx,
            node,
            _java_type_in_ctx(ctx, _str(node, "resolved_type")),
            "new HashSet<>()",
            "__RESULT__.add(" + _emit_expr(ctx, node.get("elt")) + ");",
        )
    if kind == "DictComp":
        return _emit_comp_expr(
            ctx,
            node,
            _java_type_in_ctx(ctx, _str(node, "resolved_type")),
            "new HashMap<>()",
            "__RESULT__.put(" + _emit_expr(ctx, node.get("key")) + ", " + _emit_expr(ctx, node.get("value")) + ");",
        )
    if kind == "RangeExpr":
        return _emit_range_expr(ctx, node)
    raise RuntimeError("unsupported_expr_kind_java: " + kind)


def _runtime_call_name(ctx: EmitContext, node: dict[str, JsonVal], func: JsonVal) -> str:
    runtime_call = _str(node, "resolved_runtime_call")
    if runtime_call == "":
        runtime_call = _str(node, "runtime_call")
    builtin_name = _str(node, "runtime_symbol")
    if builtin_name == "" and isinstance(func, dict):
        if _str(func, "kind") == "Name":
            builtin_name = _str(func, "id")
        elif _str(func, "kind") == "Attribute":
            builtin_name = _str(func, "attr")
    adapter = _str(node, "runtime_call_adapter_kind")
    return resolve_runtime_call(runtime_call, builtin_name, adapter, ctx.mapping)


def _emit_cast_expr(ctx: EmitContext, target_type: str, arg_code: str) -> str:
    if target_type == "":
        return arg_code
    optional_inner = _optional_inner_type(target_type)
    if optional_inner != "":
        nullable_arg = arg_code
        if _is_int_type(optional_inner) and arg_code.startswith("PyRuntime.pyToLong(") and arg_code.endswith(")"):
            nullable_arg = arg_code[len("PyRuntime.pyToLong("):-1]
        if _is_float_type(optional_inner) and arg_code.startswith("PyRuntime.pyToFloat(") and arg_code.endswith(")"):
            nullable_arg = arg_code[len("PyRuntime.pyToFloat("):-1]
        if _is_int_type(optional_inner):
            return "((" + nullable_arg + ") == null ? null : Long.valueOf(PyRuntime.pyToLong(" + nullable_arg + ")))"
        if _is_float_type(optional_inner):
            return "((" + nullable_arg + ") == null ? null : Double.valueOf(PyRuntime.pyToFloat(" + nullable_arg + ")))"
        if optional_inner == "bool":
            return "((" + nullable_arg + ") == null ? null : Boolean.valueOf(PyRuntime.pyBool(" + nullable_arg + ")))"
        if optional_inner == "str":
            return "((" + nullable_arg + ") == null ? null : PyRuntime.pyToString(" + nullable_arg + "))"
        return "((" + nullable_arg + ") == null ? null : (" + _java_type_in_ctx(ctx, target_type) + ") (" + nullable_arg + "))"
    if target_type in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
        return "PyRuntime.pyToLong(" + arg_code + ")"
    if target_type in ("float", "float32", "float64"):
        return "PyRuntime.pyToFloat(" + arg_code + ")"
    if target_type == "bool":
        return "PyRuntime.pyBool(" + arg_code + ")"
    if target_type == "str":
        return "PyRuntime.pyToString(" + arg_code + ")"
    return "(" + _java_type_in_ctx(ctx, target_type) + ") (" + arg_code + ")"


def _emit_builtin_placeholder(ctx: EmitContext, fn_name: str, all_arg_strs: list[str], node: dict[str, JsonVal]) -> str:
    owner = "(" + all_arg_strs[0] + ")" if len(all_arg_strs) >= 1 else "null"
    if fn_name == "__CAST__":
        if len(all_arg_strs) == 0:
            return "null"
        return _emit_cast_expr(ctx, _str(node, "resolved_type"), all_arg_strs[0])
    if fn_name == "__LIST_CTOR__":
        if len(all_arg_strs) == 0:
            return "new ArrayList<>()"
        return "new ArrayList<>(java.util.Arrays.asList(" + ", ".join(all_arg_strs) + "))"
    if fn_name == "__TUPLE_CTOR__":
        if len(all_arg_strs) == 0:
            return "new ArrayList<>()"
        return "new ArrayList<>(java.util.Arrays.asList(" + ", ".join(all_arg_strs) + "))"
    if fn_name == "__SET_CTOR__":
        if len(all_arg_strs) == 0:
            return "new HashSet<>()"
        return "new HashSet<>(java.util.Arrays.asList(" + ", ".join(all_arg_strs) + "))"
    if fn_name == "__LIST_APPEND__" and len(all_arg_strs) >= 2:
        return owner + ".add(" + all_arg_strs[1] + ")"
    if fn_name == "__LIST_EXTEND__" and len(all_arg_strs) >= 2:
        return owner + ".addAll(" + all_arg_strs[1] + ")"
    if fn_name == "__DEQUE_APPENDLEFT__" and len(all_arg_strs) >= 2:
        return owner + ".appendleft(" + all_arg_strs[1] + ")"
    if fn_name == "__DEQUE_POPLEFT__" and len(all_arg_strs) >= 1:
        return owner + ".popleft()"
    if fn_name == "__POP_LAST__" and len(all_arg_strs) >= 1:
        return owner + ".pop()"
    if fn_name == "__CLEAR__" and len(all_arg_strs) >= 1:
        return owner + ".clear()"
    if fn_name == "__REVERSE__" and len(all_arg_strs) >= 1:
        return owner + ".sort(java.util.Collections.reverseOrder())"
    if fn_name == "__SORT__" and len(all_arg_strs) >= 1:
        return owner + ".sort(null)"
    if fn_name == "__PATH_EXISTS__" and len(all_arg_strs) >= 1:
        return owner + ".exists()"
    if fn_name == "__DICT_GET__":
        if len(all_arg_strs) >= 3:
            return _maybe_cast_dynamic_call(
                ctx,
                node,
                "PyRuntime.__pytra_dict_get_default(" + owner + ", " + all_arg_strs[1] + ", " + all_arg_strs[2] + ")",
            )
        if len(all_arg_strs) >= 2:
            return _maybe_cast_dynamic_call(ctx, node, owner + ".get(" + all_arg_strs[1] + ")")
    if fn_name == "__DICT_KEYS__" and len(all_arg_strs) >= 1:
        call_type = _str(node, "resolved_type")
        jt = _java_type_in_ctx(ctx, call_type)
        return "(" + jt + ") (ArrayList<?>) PyRuntime.pyDictKeys(" + owner + ")"
    if fn_name == "__DICT_VALUES__" and len(all_arg_strs) >= 1:
        call_type = _str(node, "resolved_type")
        jt = _java_type_in_ctx(ctx, call_type)
        return "(" + jt + ") (ArrayList<?>) PyRuntime.pyDictValues(" + owner + ")"
    if fn_name == "__DICT_ITEMS__" and len(all_arg_strs) >= 1:
        call_type = _str(node, "resolved_type")
        jt = _java_type_in_ctx(ctx, call_type)
        return "(" + jt + ") (ArrayList<?>) PyRuntime.pyDictItems(" + owner + ")"
    if fn_name == "__SET_ADD__" and len(all_arg_strs) >= 2:
        return owner + ".add(" + all_arg_strs[1] + ")"
    if fn_name in ("__SET_DISCARD__", "__SET_REMOVE__") and len(all_arg_strs) >= 2:
        return owner + ".remove(" + all_arg_strs[1] + ")"
    if fn_name == "PyRuntime.pyRange":
        if len(all_arg_strs) == 1:
            return "PyRuntime.pyRange(0, (int) PyRuntime.pyToLong(" + all_arg_strs[0] + "), 1)"
        if len(all_arg_strs) == 2:
            return "PyRuntime.pyRange((int) PyRuntime.pyToLong(" + all_arg_strs[0] + "), (int) PyRuntime.pyToLong(" + all_arg_strs[1] + "), 1)"
        if len(all_arg_strs) >= 3:
            return "PyRuntime.pyRange((int) PyRuntime.pyToLong(" + all_arg_strs[0] + "), (int) PyRuntime.pyToLong(" + all_arg_strs[1] + "), (int) PyRuntime.pyToLong(" + all_arg_strs[2] + "))"
    return ""


def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    func = node.get("func")
    args = _list(node, "args")
    keywords = _list(node, "keywords")
    arg_strs = [_emit_expr(ctx, arg) for arg in args]
    for kw in keywords:
        if isinstance(kw, dict):
            arg_strs.append(_emit_expr(ctx, kw.get("value")))
    arg_nodes = list(args)
    for kw in keywords:
        if isinstance(kw, dict):
            arg_nodes.append(kw.get("value"))
    arg_strs = _wrap_callable_args(ctx, arg_nodes, arg_strs)

    def _wrap_stdout_callable_args(fn_name: str, rendered_args: list[str]) -> list[str]:
        if fn_name != "PyRuntime.pyAssertStdout" or len(args) < 2:
            return rendered_args
        adjusted = list(rendered_args)
        fn_arg = args[1]
        if isinstance(fn_arg, dict):
            while isinstance(fn_arg, dict) and _str(fn_arg, "kind") in ("Box", "Unbox"):
                fn_arg = fn_arg.get("value")
            if isinstance(fn_arg, dict):
                if _str(fn_arg, "kind") == "Name":
                    adjusted[1] = "() -> " + _java_symbol_name(ctx, _str(fn_arg, "id")) + "()"
                elif _str(fn_arg, "kind") == "Attribute":
                    adjusted[1] = "() -> " + _emit_attribute(ctx, fn_arg) + "()"
        return adjusted

    lowered = _str(node, "lowered_kind")
    if lowered in ("BuiltinCall", "RuntimeCall"):
        fn_name = _runtime_call_name(ctx, node, func)
        runtime_owner = node.get("runtime_owner")
        if isinstance(runtime_owner, dict):
            if not _is_module_owner(ctx, runtime_owner):
                arg_strs = [_emit_expr(ctx, runtime_owner)] + arg_strs
        if fn_name == "PyRuntime.pyToString" and len(args) >= 1:
            first_arg_type = _node_type(ctx, args[0])
            if first_arg_type.startswith("tuple["):
                return "PyRuntime.pyTupleToString(" + arg_strs[0] + ")"
        arg_strs = _wrap_stdout_callable_args(fn_name, arg_strs)
        placeholder = _emit_builtin_placeholder(ctx, fn_name, arg_strs, node)
        if placeholder != "":
            return placeholder
        if fn_name != "":
            if fn_name == "PyRuntime.pyPop":
                result_type = _str(node, "resolved_type")
                rendered = fn_name + "(" + ", ".join(arg_strs) + ")"
                if result_type != "" and not _is_dynamic_type(result_type):
                    return _emit_cast_expr(ctx, result_type, rendered)
                return rendered
            return fn_name + "(" + ", ".join(arg_strs) + ")"

    if isinstance(func, dict):
        func_kind = _str(func, "kind")
        if func_kind == "Attribute":
            owner_node = func.get("value")
            runtime_owner = node.get("runtime_owner")
            if isinstance(runtime_owner, dict):
                owner_node = runtime_owner
            attr = _str(func, "attr")
            owner = _emit_expr(ctx, owner_node)
            call_arg_strs = list(arg_strs)
            if len(call_arg_strs) > 0 and call_arg_strs[0] == owner:
                call_arg_strs = call_arg_strs[1:]
            fn_name = _runtime_call_name(ctx, node, func)
            special = _emit_container_method_call(ctx, owner_node, call_arg_strs, node, fn_name)
            if special != "":
                return special
            is_module_owner, owner_key, owner_module_id = _module_owner_info(ctx, owner_node)
            if is_module_owner:
                mod_id = _str(node, "runtime_module_id")
                if mod_id == "":
                    mod_id = owner_module_id
                qualified = _str(func, "repr")
                if qualified == "":
                    qualified = owner_key + "." + attr if owner_key != "" else attr
                if qualified in ctx.mapping.calls:
                    return ctx.mapping.calls[qualified] + "(" + ", ".join(arg_strs) + ")"
                if should_skip_module(mod_id, ctx.mapping):
                    resolved = resolve_runtime_symbol_name(
                        attr,
                        ctx.mapping,
                        module_id=mod_id,
                        resolved_runtime_call=_str(node, "resolved_runtime_call"),
                        runtime_call=_str(node, "runtime_call"),
                    )
                    if resolved != "":
                        return resolved + "(" + ", ".join(arg_strs) + ")"
            runtime_call = _str(node, "resolved_runtime_call")
            if runtime_call == "":
                runtime_call = _str(node, "runtime_call")
            if runtime_call != "" or fn_name in ctx.mapping.calls.values():
                method_args = [owner] + call_arg_strs
                if is_module_owner:
                    method_args = list(call_arg_strs)
                owner_type = _node_type(ctx, owner_node)
                if not is_module_owner and _is_dynamic_type(owner_type) and fn_name in (
                    "PyRuntime.pyStrJoin",
                    "PyRuntime.pyStrStrip",
                    "PyRuntime.pyStrRStrip",
                    "PyRuntime.pyStrStartswith",
                    "PyRuntime.pyStrEndswith",
                    "PyRuntime.pyStrReplace",
                ):
                    method_args[0] = _emit_cast_expr(ctx, "str", owner)
                method_args = _wrap_stdout_callable_args(fn_name, method_args)
                placeholder = _emit_builtin_placeholder(ctx, fn_name, method_args, node)
                if placeholder != "":
                    return placeholder
                if fn_name != "":
                    return fn_name + "(" + ", ".join(method_args) + ")"
            return _emit_attribute(ctx, func) + "(" + ", ".join(call_arg_strs) + ")"
        if func_kind == "Name":
            fn_id = _str(func, "id")
            vararg_type = ctx.function_varargs.get(fn_id, "")
            if vararg_type != "" and len(args) >= 1:
                last_arg = args[-1]
                if isinstance(last_arg, dict) and _str(last_arg, "kind") == "List":
                    call_args = [_emit_expr(ctx, arg) for arg in args[:-1]]
                    for elem in _list(last_arg, "elements"):
                        call_args.append(_emit_expr(ctx, elem))
                    return _java_symbol_name(ctx, fn_id) + "(" + ", ".join(call_args) + ")"
            closure_info = ctx.closure_helpers.get(fn_id)
            if isinstance(closure_info, dict):
                helper_name = closure_info.get("helper_name")
                capture_names = closure_info.get("capture_names")
                if isinstance(helper_name, str) and isinstance(capture_names, list):
                    helper_args: list[str] = []
                    for capture_name in capture_names:
                        if isinstance(capture_name, str) and capture_name != "":
                            helper_args.append(_java_symbol_name(ctx, capture_name))
                    helper_args.extend(arg_strs)
                    return _safe_java_ident(helper_name) + "(" + ", ".join(helper_args) + ")"
            if fn_id in ctx.class_names:
                return "new " + _safe_java_ident(fn_id) + "(" + ", ".join(arg_strs) + ")"
            mapped_ctor = _resolve_mapped_ctor_name(ctx, fn_id, node)
            if mapped_ctor != "":
                return "new " + mapped_ctor + "(" + ", ".join(arg_strs) + ")"
            if fn_id in ctx.runtime_imports:
                runtime_name = ctx.runtime_imports[fn_id]
                return runtime_name + "(" + ", ".join(_wrap_stdout_callable_args(runtime_name, arg_strs)) + ")"
            func_type = _callable_type_for_node(ctx, func)
            if _parse_callable_type(func_type) is not None:
                return _java_symbol_name(ctx, fn_id) + ".invoke(" + ", ".join(arg_strs) + ")"
            if (
                func_type in ("Callable", "callable")
                and fn_id not in ctx.function_names
                and _java_symbol_name(ctx, fn_id) not in ctx.function_names
            ):
                result = _java_symbol_name(ctx, fn_id) + ".apply(" + (arg_strs[0] if len(arg_strs) >= 1 else "null") + ")"
                result_type = _str(node, "resolved_type")
                if result_type != "" and not _is_dynamic_type(result_type):
                    return _emit_cast_expr(ctx, result_type, result)
                return result
            runtime_call = _str(node, "runtime_call")
            resolved_runtime_call = _str(node, "resolved_runtime_call")
            adapter_kind = _str(node, "runtime_call_adapter_kind")
            if runtime_call != "" or resolved_runtime_call != "" or adapter_kind != "" or fn_id in ctx.mapping.calls:
                fn_name = _runtime_call_name(ctx, node, func)
                arg_strs = _wrap_stdout_callable_args(fn_name, arg_strs)
                placeholder = _emit_builtin_placeholder(ctx, fn_name, arg_strs, node)
                if placeholder != "":
                    return placeholder
                if fn_name != "":
                    return fn_name + "(" + ", ".join(arg_strs) + ")"
            return _java_symbol_name(ctx, fn_id) + "(" + ", ".join(arg_strs) + ")"

    if isinstance(func, dict):
        func_type = _callable_type_for_node(ctx, func)
        if _str(func, "kind") == "Lambda" and _parse_callable_type(func_type) is not None:
            iface_name = _safe_java_ident(func_type)
            return "((" + iface_name + ") (" + _emit_expr(ctx, func) + ")).invoke(" + ", ".join(arg_strs) + ")"
        if _parse_callable_type(func_type) is not None:
            return _emit_expr(ctx, func) + ".invoke(" + ", ".join(arg_strs) + ")"
    return _emit_expr(ctx, func) + "(" + ", ".join(arg_strs) + ")"


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return _emit_expr(ctx, left_node)
    current_left = _emit_expr(ctx, left_node)
    parts: list[str] = []
    for idx, comparator in enumerate(comparators):
        op_obj = ops[idx] if idx < len(ops) else None
        op_name = op_obj if isinstance(op_obj, str) else _str(op_obj, "kind") if isinstance(op_obj, dict) else ""
        right = _emit_expr(ctx, comparator)
        if op_name == "Eq":
            parts.append("PyRuntime.pyEq(" + current_left + ", " + right + ")")
        elif op_name == "NotEq":
            parts.append("PyRuntime.pyNe(" + current_left + ", " + right + ")")
        elif op_name == "Lt":
            parts.append("PyRuntime.pyLt(" + current_left + ", " + right + ")")
        elif op_name == "LtE":
            parts.append("PyRuntime.pyLe(" + current_left + ", " + right + ")")
        elif op_name == "Gt":
            parts.append("PyRuntime.pyGt(" + current_left + ", " + right + ")")
        elif op_name == "GtE":
            parts.append("PyRuntime.pyGe(" + current_left + ", " + right + ")")
        elif op_name == "Is":
            parts.append("(" + current_left + " == " + right + ")")
        elif op_name == "IsNot":
            parts.append("(" + current_left + " != " + right + ")")
        elif op_name == "In":
            parts.append("PyRuntime.pyIn(" + current_left + ", " + right + ")")
        elif op_name == "NotIn":
            parts.append("(!PyRuntime.pyIn(" + current_left + ", " + right + "))")
        else:
            parts.append("(" + current_left + " " + op_name + " " + right + ")")
        current_left = right
    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _emit_common_stmt_if_supported(ctx: EmitContext, node: dict[str, JsonVal]) -> bool:
    kind = _str(node, "kind")
    if kind not in ("Expr", "Return", "Assign", "AnnAssign", "Pass", "Raise", "Try", "comment", "blank", "If", "While"):
        return False
    renderer = ctx.stmt_renderer
    if not isinstance(renderer, _JavaStmtRenderer):
        renderer = _JavaStmtRenderer(ctx)
        ctx.stmt_renderer = renderer
    renderer.emit_stmt(node)
    ctx.indent_level = renderer.state.indent_level
    return True


def _decl_type(node: dict[str, JsonVal], value: JsonVal) -> str:
    decl_type = _str(node, "decl_type")
    if decl_type in ("Callable", "callable"):
        target = node.get("target")
        if isinstance(target, dict):
            target_type = _normalized_callable_type(_str(target, "resolved_type"))
            if target_type != "":
                decl_type = target_type
    if decl_type == "":
        target = node.get("target")
        if isinstance(target, dict):
            decl_type = _str(target, "resolved_type")
    if decl_type == "" and isinstance(value, dict):
        decl_type = _str(value, "resolved_type")
    return decl_type


def _at_module_scope(ctx: EmitContext) -> bool:
    return ctx.current_return_type == "" and ctx.current_class == ""


def _at_class_field_scope(ctx: EmitContext) -> bool:
    return ctx.current_return_type == "" and ctx.current_class != ""


def _emit_name_assignment(ctx: EmitContext, name: str, target_type: str, value_code: str, *, annotated: bool) -> None:
    safe_name = _java_symbol_name(ctx, name)
    jt = _java_type_in_ctx(ctx, target_type)
    if _at_module_scope(ctx):
        if safe_name in ctx.module_fields:
            _emit(ctx, safe_name + " = " + value_code + ";")
            return
        ctx.module_fields.add(safe_name)
        _emit(ctx, "public static " + jt + " " + safe_name + " = " + value_code + ";")
        return
    if _at_class_field_scope(ctx):
        field_names = ctx.class_fields.get(ctx.current_class, set())
        if safe_name in field_names:
            _emit(ctx, safe_name + " = " + value_code + ";")
            return
        field_names.add(safe_name)
        ctx.class_fields[ctx.current_class] = field_names
        _emit(ctx, "public static " + jt + " " + safe_name + " = " + value_code + ";")
        return
    if safe_name in ctx.var_types:
        if target_type != "":
            ctx.var_types[safe_name] = target_type
        _emit(ctx, safe_name + " = " + value_code + ";")
        return
    if annotated or safe_name not in ctx.var_types:
        ctx.var_types[safe_name] = target_type
        _emit(ctx, jt + " " + safe_name + " = " + value_code + ";")
        return
    _emit(ctx, safe_name + " = " + value_code + ";")


def _with_hoisted_names(node: dict[str, JsonVal]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for stmt in _list(node, "body"):
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        target = stmt.get("target")
        if not isinstance(target, dict) or _str(target, "kind") not in ("Name", "NameTarget"):
            continue
        name = _str(target, "id")
        if name == "" or name in seen:
            continue
        decl_type = ""
        if kind == "AnnAssign":
            decl_type = _str(stmt, "decl_type") or _str(stmt, "annotation") or _str(target, "resolved_type")
        elif kind == "Assign" and _bool(stmt, "declare"):
            decl_type = _str(stmt, "decl_type") or _str(target, "resolved_type")
        if decl_type == "":
            continue
        seen.add(name)
        out.append((name, decl_type))
    return out


def _emit_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    targets = _list(node, "targets")
    if not isinstance(target, dict) and len(targets) > 0 and isinstance(targets[0], dict):
        target = targets[0]
    if not isinstance(target, dict):
        return
    value = node.get("value")
    target_kind = _str(target, "kind")
    target_type = _decl_type(node, value)
    value_code = _emit_expr(ctx, value) if isinstance(value, dict) else "null"
    value_code = _coerce_callable_assignment(ctx, value, target_type, value_code)
    if target_kind in ("Name", "NameTarget"):
        _emit_name_assignment(ctx, _str(target, "id"), target_type, value_code, annotated=False)
        return
    if target_kind == "Attribute":
        _emit(ctx, _emit_attribute(ctx, target) + " = " + value_code + ";")
        return
    if target_kind == "Subscript":
        owner = _emit_expr(ctx, target.get("value"))
        index = _emit_expr(ctx, target.get("slice"))
        _emit(ctx, "PyRuntime.pySet(" + owner + ", " + index + ", " + value_code + ");")
        return
    raise RuntimeError("unsupported_assign_target_java: " + target_kind)


def _emit_ann_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    if not isinstance(target, dict):
        return
    target_type = _str(node, "decl_type")
    if target_type == "":
        target_type = _str(node, "annotation")
    if target_type == "":
        target_type = _str(target, "resolved_type")
    value = node.get("value")
    value_code = _emit_expr(ctx, value) if isinstance(value, dict) else java_zero_value(target_type)
    value_code = _coerce_callable_assignment(ctx, value, target_type, value_code)
    target_kind = _str(target, "kind")
    if target_kind in ("Name", "NameTarget"):
        _emit_name_assignment(ctx, _str(target, "id"), target_type, value_code, annotated=True)
        return
    if target_kind == "Attribute":
        _emit(ctx, _emit_attribute(ctx, target) + " = " + value_code + ";")
        return
    raise RuntimeError("unsupported_ann_assign_target_java: " + target_kind)


def _emit_aug_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    symbol = {
        "Add": "+",
        "Sub": "-",
        "Mult": "*",
        "Div": "/",
        "BitAnd": "&",
        "BitOr": "|",
        "BitXor": "^",
        "LShift": "<<",
        "RShift": ">>",
    }.get(_str(node, "op"), "+")
    _emit(ctx, _emit_expr(ctx, node.get("target")) + " " + symbol + "= " + _emit_expr(ctx, node.get("value")) + ";")


def _emit_store_target(ctx: EmitContext, target: JsonVal, value_code: str) -> None:
    if not isinstance(target, dict):
        raise RuntimeError("unsupported_store_target_java")
    target_kind = _str(target, "kind")
    if target_kind in ("Name", "NameTarget"):
        _emit(ctx, _java_symbol_name(ctx, _str(target, "id")) + " = " + value_code + ";")
        return
    if target_kind == "Attribute":
        _emit(ctx, _emit_attribute(ctx, target) + " = " + value_code + ";")
        return
    if target_kind == "Subscript":
        owner = _emit_expr(ctx, target.get("value"))
        index = _emit_expr(ctx, target.get("slice"))
        _emit(ctx, "PyRuntime.pySet(" + owner + ", " + index + ", " + value_code + ");")
        return
    raise RuntimeError("unsupported_store_target_java: " + target_kind)


def _emit_return(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if isinstance(value, dict):
        _emit(ctx, "return " + _emit_expr(ctx, value) + ";")
        return
    _emit(ctx, "return;")


def _emit_static_range_for_plan(ctx: EmitContext, iter_plan: dict[str, JsonVal], target_name: str, target_type: str, body: list[JsonVal]) -> None:
    start = _emit_expr(ctx, iter_plan.get("start"))
    stop = _emit_expr(ctx, iter_plan.get("stop"))
    step_node = iter_plan.get("step")
    step = _emit_expr(ctx, step_node) if isinstance(step_node, dict) else "1L"
    descending = _str(iter_plan, "range_mode") == "descending"
    if not descending and isinstance(step_node, dict):
        if _str(step_node, "kind") == "UnaryOp" and _str(step_node, "op") == "USub":
            descending = True
        elif _str(step_node, "kind") == "Constant":
            value = step_node.get("value")
            if isinstance(value, (int, float)) and value < 0:
                descending = True
    compare = " > " if descending else " < "
    declared_target = target_name in ctx.var_types
    loop_name = target_name
    if declared_target:
        loop_name = "_pytra_loop_" + target_name + "_" + str(len(ctx.lines))
    update = loop_name + " += " + step
    _emit(ctx, "for (" + _java_type_in_ctx(ctx, target_type) + " " + loop_name + " = " + start + "; " + loop_name + compare + stop + "; " + update + ") {")
    ctx.indent_level += 1
    saved = dict(ctx.var_types)
    if declared_target:
        _emit(ctx, target_name + " = " + loop_name + ";")
    else:
        ctx.var_types[target_name] = target_type
    for stmt in body:
        _emit_stmt(ctx, stmt)
    ctx.var_types = saved
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _for_target_name(target_node: JsonVal) -> tuple[str, str]:
    if not isinstance(target_node, dict):
        return ("item", "Object")
    name = _str(target_node, "id")
    if name == "":
        name = "item"
    target_type = _str(target_node, "target_type")
    if target_type == "":
        target_type = _str(target_node, "resolved_type")
    if target_type == "":
        target_type = "Object"
    return (_safe_java_ident(name), target_type)


def _iter_element_type(ctx: EmitContext, iter_node: JsonVal) -> str:
    iter_type = _node_type(ctx, iter_node)
    if iter_type in ("", "unknown") and isinstance(iter_node, dict) and _str(iter_node, "kind") == "Name":
        iter_type = ctx.var_types.get(_java_symbol_name(ctx, _str(iter_node, "id")), "")
    if iter_type.startswith("list[") and iter_type.endswith("]"):
        return iter_type[5:-1]
    if iter_type.startswith("set[") and iter_type.endswith("]"):
        return iter_type[4:-1]
    if iter_type.startswith("tuple[") and iter_type.endswith("]"):
        return "Object"
    return ""


def _emit_for_core(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target_plan")
    if target_node is None:
        target_node = node.get("target")
    body = _list(node, "body")
    orelse = _list(node, "orelse")
    target_name, target_type = _for_target_name(target_node)
    iter_plan = node.get("iter_plan")
    if isinstance(iter_plan, dict) and _str(iter_plan, "kind") == "StaticRangeForPlan":
        _emit_static_range_for_plan(ctx, iter_plan, target_name, target_type, body)
    else:
        iter_expr = "new ArrayList<>()"
        iter_node = None
        if isinstance(iter_plan, dict) and _str(iter_plan, "kind") == "RuntimeIterForPlan":
            iter_node = iter_plan.get("iter_expr")
        elif isinstance(node.get("iter"), dict):
            iter_node = node.get("iter")
        if target_type in ("", "Object", "unknown"):
            inferred_type = _iter_element_type(ctx, iter_node)
            if inferred_type != "":
                target_type = inferred_type
        if isinstance(iter_node, dict):
            iter_expr = _emit_iterable_cast(ctx, iter_node, target_type)
        declared_target = target_name in ctx.var_types
        loop_name = target_name
        if declared_target:
            loop_name = "_pytra_iter_" + target_name + "_" + str(len(ctx.lines))
        _emit(ctx, "for (" + _java_type_in_ctx(ctx, target_type) + " " + loop_name + " : " + iter_expr + ") {")
        ctx.indent_level += 1
        saved = dict(ctx.var_types)
        if declared_target:
            _emit(ctx, target_name + " = " + loop_name + ";")
        else:
            ctx.var_types[target_name] = target_type
        for stmt in body:
            _emit_stmt(ctx, stmt)
        ctx.var_types = saved
        ctx.indent_level -= 1
        _emit(ctx, "}")
    for stmt in orelse:
        _emit_stmt(ctx, stmt)


def _emit_for_range(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_name, target_type = _for_target_name(node.get("target"))
    _emit_static_range_for_plan(ctx, node, target_name, target_type, _list(node, "body"))


def _arg_order_and_types(node: dict[str, JsonVal]) -> tuple[list[str], dict[str, str]]:
    arg_order: list[str] = []
    for item in _list(node, "arg_order"):
        if isinstance(item, str):
            arg_order.append(item)
    arg_types: dict[str, str] = {}
    for key, value in _dict(node, "arg_types").items():
        if isinstance(key, str) and isinstance(value, str):
            arg_types[key] = value
    return (arg_order, arg_types)


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    arg_order, _arg_types = _arg_order_and_types(node)
    params: list[str] = []
    for arg_name in arg_order:
        params.append(_safe_java_ident(arg_name))
    body = node.get("body")
    body_code = _emit_expr(ctx, body)
    return "(" + ", ".join(params) + ") -> " + body_code


def _function_return_type(node: dict[str, JsonVal]) -> str:
    return_type = _str(node, "return_type")
    if return_type != "" and return_type != "None":
        return return_type
    for stmt in _list(node, "body"):
        if not isinstance(stmt, dict) or _str(stmt, "kind") != "Return":
            continue
        value = stmt.get("value")
        if isinstance(value, dict):
            value_type = _str(value, "resolved_type")
            if value_type != "" and value_type != "None":
                return value_type
    return return_type


def _closure_helper_info(ctx: EmitContext, owner_name: str, node: dict[str, JsonVal]) -> dict[str, JsonVal]:
    helper_name = "__closure_" + _safe_java_ident(owner_name) + "_" + _safe_java_ident(_str(node, "name"))
    capture_names: list[str] = []
    capture_types: dict[str, str] = {}
    for capture in _list(node, "captures"):
        if not isinstance(capture, dict):
            continue
        capture_name = _str(capture, "name")
        if capture_name == "":
            continue
        capture_names.append(capture_name)
        capture_type = _str(capture, "type")
        if capture_type == "":
            capture_type = _dict(node, "capture_types").get(capture_name) if isinstance(_dict(node, "capture_types").get(capture_name), str) else ""
        if capture_type == "":
            capture_type = "Object"
        capture_types[capture_name] = capture_type
    return {
        "helper_name": helper_name,
        "capture_names": capture_names,
        "capture_types": capture_types,
    }


def _emit_closure_helper(ctx: EmitContext, owner_name: str, node: dict[str, JsonVal]) -> None:
    helper_info = _closure_helper_info(ctx, owner_name, node)
    capture_names = helper_info.get("capture_names")
    capture_types = helper_info.get("capture_types")
    if not isinstance(capture_names, list) or not isinstance(capture_types, dict):
        return
    helper_arg_order: list[str] = []
    helper_arg_types: dict[str, str] = {}
    for capture_name in capture_names:
        if not isinstance(capture_name, str) or capture_name == "":
            continue
        helper_arg_order.append(capture_name)
        capture_type = capture_types.get(capture_name)
        helper_arg_types[capture_name] = capture_type if isinstance(capture_type, str) and capture_type != "" else "Object"
    for arg_name in _list(node, "arg_order"):
        if not isinstance(arg_name, str) or arg_name == "":
            continue
        helper_arg_order.append(arg_name)
        helper_arg_types[arg_name] = _dict(node, "arg_types").get(arg_name) if isinstance(_dict(node, "arg_types").get(arg_name), str) else "Object"
    helper_node: dict[str, JsonVal] = dict(node)
    helper_node["kind"] = "FunctionDef"
    helper_node["name"] = helper_info.get("helper_name")
    helper_node["arg_order"] = helper_arg_order
    helper_node["arg_types"] = helper_arg_types
    saved_helpers = dict(ctx.closure_helpers)
    ctx.closure_helpers[_str(node, "name")] = helper_info
    _emit_function_def(ctx, helper_node, force_static=True)
    ctx.closure_helpers = saved_helpers


def _emit_function_def(ctx: EmitContext, node: dict[str, JsonVal], *, force_static: bool = False) -> None:
    name = _str(node, "name")
    return_type = _function_return_type(node)
    body = _list(node, "body")
    decorators = _list(node, "decorators")
    is_static = force_static
    is_property = False
    for deco in decorators:
        if isinstance(deco, str) and deco in ("staticmethod", "classmethod"):
            is_static = True
        if isinstance(deco, str) and deco == "property":
            is_property = True
    arg_order, arg_types = _arg_order_and_types(node)
    params: list[str] = []
    for idx, arg_name in enumerate(arg_order):
        if ctx.current_class != "" and idx == 0 and arg_name == "self":
            continue
        params.append(_java_type_in_ctx(ctx, arg_types.get(arg_name, "Object")) + " " + _safe_java_ident(arg_name))
    vararg_name = _str(node, "vararg_name")
    vararg_type = _str(node, "vararg_type")
    if vararg_name != "":
        if vararg_type == "":
            vararg_type = "Object"
        params.append(_java_type_in_ctx(ctx, vararg_type) + "... " + _safe_java_ident(vararg_name))

    local_closure_helpers: dict[str, dict[str, JsonVal]] = {}
    for stmt in body:
        if not isinstance(stmt, dict) or _str(stmt, "kind") != "ClosureDef":
            continue
        helper_info = _closure_helper_info(ctx, name, stmt)
        local_closure_helpers[_str(stmt, "name")] = helper_info
        _emit_closure_helper(ctx, name, stmt)

    saved_var_types = dict(ctx.var_types)
    saved_return_type = ctx.current_return_type
    saved_closure_helpers = dict(ctx.closure_helpers)
    saved_active_varargs = set(ctx.active_varargs)
    ctx.current_return_type = return_type
    ctx.closure_helpers.update(local_closure_helpers)
    for arg_name in arg_order:
        if arg_name == "self":
            continue
        ctx.var_types[_safe_java_ident(arg_name)] = arg_types.get(arg_name, "")
    if vararg_name != "":
        ctx.var_types[_safe_java_ident(vararg_name)] = "list[" + vararg_type + "]"
        ctx.active_varargs.add(vararg_name)

    base_init_args = ""
    if ctx.current_class != "" and name == "__init__":
        if len(body) > 0:
            first_stmt = body[0]
            if isinstance(first_stmt, dict) and _str(first_stmt, "kind") == "Expr":
                first_value = first_stmt.get("value")
                if isinstance(first_value, dict) and _str(first_value, "kind") == "Call":
                    first_func = first_value.get("func")
                    if isinstance(first_func, dict) and _str(first_func, "kind") == "Attribute" and _str(first_func, "attr") == "__init__":
                        owner = first_func.get("value")
                        if isinstance(owner, dict) and _str(owner, "kind") == "Call":
                            owner_func = owner.get("func")
                            if isinstance(owner_func, dict) and _str(owner_func, "kind") == "Name" and _str(owner_func, "id") == "super":
                                base_init_args = ", ".join(_emit_expr(ctx, arg) for arg in _list(first_value, "args"))
                                body = body[1:]
        _emit(ctx, "public " + _safe_java_ident(ctx.current_class) + "(" + ", ".join(params) + ") {")
    else:
        modifiers = "public "
        if ctx.current_class == "" or is_static:
            modifiers += "static "
        method_params = "" if is_property and ctx.current_class != "" else ", ".join(params)
        _emit(ctx, modifiers + _java_type_in_ctx(ctx, return_type, allow_void=True) + " " + _safe_java_ident(name) + "(" + method_params + ") {")
    ctx.indent_level += 1
    if base_init_args != "":
        _emit(ctx, "super(" + base_init_args + ");")
    for stmt in body:
        _emit_stmt(ctx, stmt)
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)
    ctx.var_types = saved_var_types
    ctx.current_return_type = saved_return_type
    ctx.closure_helpers = saved_closure_helpers
    ctx.active_varargs = saved_active_varargs


def _emit_class_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    base = _str(node, "base")
    is_dataclass = _bool(node, "dataclass")
    body = _list(node, "body")
    trait_meta = _dict(_dict(node, "meta"), "trait_v1")
    impl_meta = _dict(_dict(node, "meta"), "implements_v1")
    is_trait = len(trait_meta) > 0 or "trait" in _list(node, "decorators")
    interface_names: list[str] = []
    for item in _list(trait_meta, "extends_traits"):
        if isinstance(item, str) and item != "":
            interface_names.append(_safe_java_ident(item.split(".")[-1]))
    if len(interface_names) == 0 and is_trait and base != "" and base != "object":
        interface_names.append(_safe_java_ident(base.split(".")[-1]))
    if is_trait:
        header = "public interface " + _safe_java_ident(name)
        if len(interface_names) > 0:
            header += " extends " + ", ".join(interface_names)
        header += " {"
        _emit(ctx, header)
        _emit_blank(ctx)
        ctx.indent_level += 1
        for stmt in body:
            if not isinstance(stmt, dict) or _str(stmt, "kind") not in ("FunctionDef", "ClosureDef"):
                continue
            method_name = _safe_java_ident(_str(stmt, "name"))
            if method_name == "__init__":
                continue
            arg_order, arg_types = _arg_order_and_types(stmt)
            params: list[str] = []
            for idx, arg_name in enumerate(arg_order):
                if idx == 0 and arg_name == "self":
                    continue
                params.append(_java_type_in_ctx(ctx, arg_types.get(arg_name, "Object")) + " " + _safe_java_ident(arg_name))
            _emit(ctx, _java_type_in_ctx(ctx, _str(stmt, "return_type"), allow_void=True) + " " + method_name + "(" + ", ".join(params) + ");")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit_blank(ctx)
        return
    header = "public static class " + _safe_java_ident(name)
    if base != "" and base not in ("object", "Enum", "IntEnum", "IntFlag"):
        header += " extends " + _java_type_in_ctx(ctx, base)
    implemented_traits: list[str] = []
    for item in _list(impl_meta, "traits"):
        if isinstance(item, str) and item != "":
            trait_name = _safe_java_ident(item.split(".")[-1])
            if trait_name not in implemented_traits:
                implemented_traits.append(trait_name)
    if len(implemented_traits) > 0:
        header += " implements " + ", ".join(implemented_traits)
    header += " {"
    _emit(ctx, header)
    _emit_blank(ctx)
    saved_class = ctx.current_class
    saved_vars = dict(ctx.var_types)
    ctx.current_class = name
    ctx.var_types = {}
    ctx.indent_level += 1
    property_methods: set[str] = set()
    field_initializers: dict[str, JsonVal] = {}
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("FunctionDef", "ClosureDef"):
            if "property" in _list(stmt, "decorators"):
                property_methods.add(_str(stmt, "name"))
            continue
        target = stmt.get("target")
        if isinstance(target, dict) and _str(target, "kind") in ("Name", "NameTarget"):
            field_name = _str(target, "id")
            if field_name != "":
                value_node = stmt.get("value")
                if isinstance(value_node, dict):
                    field_initializers[field_name] = value_node
    ctx.class_property_methods[name] = property_methods
    if base in ("Enum", "IntEnum", "IntFlag"):
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            target = stmt.get("target")
            if not isinstance(target, dict) or _str(target, "kind") not in ("Name", "NameTarget"):
                continue
            field_name = _str(target, "id")
            if field_name == "":
                continue
            value_node = stmt.get("value")
            value_code = _emit_expr(ctx, value_node) if isinstance(value_node, dict) else "0L"
            _emit(ctx, "public static final long " + _safe_java_ident(field_name) + " = " + value_code + ";")
        ctx.indent_level -= 1
        ctx.current_class = saved_class
        ctx.var_types = saved_vars
        _emit(ctx, "}")
        _emit_blank(ctx)
        return
    _emit(ctx, "public long __pytra_type_id() {")
    ctx.indent_level += 1
    linked_tid = _linked_type_id(ctx, name)
    if linked_tid is None:
        linked_tid = _linked_type_id(ctx, ctx.module_id + "." + name)
    if linked_tid is None:
        linked_tid = 0
    _emit(ctx, "return " + str(linked_tid) + "L;")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)
    field_types = _dict(node, "field_types")
    for field_name, field_type in field_types.items():
        if isinstance(field_name, str) and isinstance(field_type, str) and field_name != "":
            field_names = ctx.class_fields.get(name, set())
            field_names.add(_safe_java_ident(field_name))
            ctx.class_fields[name] = field_names
            init_node = field_initializers.get(field_name)
            init_code = ""
            if isinstance(init_node, dict):
                init_code = " = " + _emit_expr(ctx, init_node)
            field_prefix = "public "
            if not is_dataclass and field_name in field_initializers:
                field_prefix = "public static "
            _emit(ctx, field_prefix + _java_type_in_ctx(ctx, field_type) + " " + _safe_java_ident(field_name) + init_code + ";")
    if len(field_types) > 0:
        _emit_blank(ctx)
    if is_dataclass:
        ctor_fields: list[tuple[str, str]] = []
        default_suffix_start = len(field_types)
        field_index = 0
        for field_name, field_type in field_types.items():
            if not isinstance(field_name, str) or not isinstance(field_type, str) or field_name == "":
                continue
            ctor_fields.append((field_name, field_type))
            if field_name in field_initializers and default_suffix_start == len(field_types):
                default_suffix_start = field_index
            field_index += 1
        ctor_params = [
            _java_type_in_ctx(ctx, field_type) + " " + _safe_java_ident(field_name)
            for field_name, field_type in ctor_fields
        ]
        _emit(ctx, "public " + _safe_java_ident(name) + "(" + ", ".join(ctor_params) + ") {")
        ctx.indent_level += 1
        for field_name, _field_type in ctor_fields:
            _emit(ctx, "this." + _safe_java_ident(field_name) + " = " + _safe_java_ident(field_name) + ";")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit_blank(ctx)
        if default_suffix_start < len(ctor_fields):
            for omit_from in range(default_suffix_start, len(ctor_fields)):
                short_params = [
                    _java_type_in_ctx(ctx, field_type) + " " + _safe_java_ident(field_name)
                    for field_name, field_type in ctor_fields[:omit_from]
                ]
                call_args: list[str] = []
                for field_name, _field_type in ctor_fields[:omit_from]:
                    call_args.append(_safe_java_ident(field_name))
                for field_name, _field_type in ctor_fields[omit_from:]:
                    init_node = field_initializers.get(field_name)
                    if isinstance(init_node, dict):
                        call_args.append(_emit_expr(ctx, init_node))
                    else:
                        call_args.append("null")
                _emit(ctx, "public " + _safe_java_ident(name) + "(" + ", ".join(short_params) + ") {")
                ctx.indent_level += 1
                _emit(ctx, "this(" + ", ".join(call_args) + ");")
                ctx.indent_level -= 1
                _emit(ctx, "}")
                _emit_blank(ctx)
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("Assign", "AnnAssign"):
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") in ("Name", "NameTarget"):
                field_name = _str(target, "id")
                if field_name in field_types:
                    continue
        _emit_stmt(ctx, stmt)
    ctx.indent_level -= 1
    ctx.current_class = saved_class
    ctx.var_types = saved_vars
    _emit(ctx, "}")
    _emit_blank(ctx)


def _emit_stmt(ctx: EmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        return
    if _emit_common_stmt_if_supported(ctx, node):
        return
    kind = _str(node, "kind")
    if kind in ("Import", "ImportFrom", "TypeAlias", "Global"):
        return
    if kind == "Delete":
        for target in _list(node, "targets"):
            if not isinstance(target, dict):
                continue
            target_kind = _str(target, "kind")
            if target_kind == "Subscript":
                owner_node = target.get("value")
                slice_node = target.get("slice")
                owner = _emit_expr(ctx, owner_node)
                index = _emit_expr(ctx, slice_node)
                owner_type = _node_type(ctx, owner_node)
                if _is_dict_type(owner_type):
                    _emit(ctx, owner + ".remove(" + index + ");")
                    continue
                if _is_list_type(owner_type):
                    _emit(ctx, owner + ".remove((int) PyRuntime.pyToLong(" + index + "));")
                    continue
            elif target_kind in ("Name", "NameTarget"):
                _emit(ctx, _java_symbol_name(ctx, _str(target, "id")) + " = null;")
                continue
        return
    if kind == "VarDecl":
        name = _str(node, "name")
        target_type = _str(node, "type")
        if name != "" and target_type != "":
            _emit_name_assignment(ctx, name, target_type, java_zero_value(target_type), annotated=True)
        return
    if kind == "AugAssign":
        _emit_aug_assign(ctx, node)
        return
    if kind == "ForCore":
        _emit_for_core(ctx, node)
        return
    if kind == "ForRange":
        _emit_for_range(ctx, node)
        return
    if kind == "FunctionDef":
        _emit_function_def(ctx, node, force_static=(ctx.current_class == ""))
        return
    if kind == "ClosureDef":
        if ctx.current_return_type == "":
            _emit_function_def(ctx, node, force_static=(ctx.current_class == ""))
        return
    if kind == "ClassDef":
        _emit_class_def(ctx, node)
        return
    if kind == "Swap":
        left = node.get("left")
        right = node.get("right")
        left_code = _emit_expr(ctx, left)
        right_code = _emit_expr(ctx, right)
        tmp_type = "Object"
        if isinstance(left, dict):
            tmp_type = _java_type_in_ctx(ctx, _str(left, "resolved_type"))
        tmp_name = "_pytra_swap_tmp_" + str(len(ctx.lines))
        _emit(ctx, tmp_type + " " + tmp_name + " = " + left_code + ";")
        _emit_store_target(ctx, left, right_code)
        _emit_store_target(ctx, right, tmp_name)
        return
    if kind == "Break":
        _emit(ctx, "break;")
        return
    if kind == "Continue":
        _emit(ctx, "continue;")
        return
    if kind == "With":
        context_expr = node.get("context_expr")
        context_type = _str(context_expr, "resolved_type") if isinstance(context_expr, dict) else "PyFile"
        if context_type == "":
            context_type = "PyFile"
        if context_type in ("TextIOWrapper", "BufferedReader", "BufferedWriter", "IOBase", "PyFile"):
            java_context_type = "PyRuntime.PyFile"
        else:
            java_context_type = _java_type_in_ctx(ctx, context_type)
        comp_name = "_pytra_with_ctx_" + str(len(ctx.lines))
        entered_name = "_pytra_with_value_" + str(len(ctx.lines))
        _emit(ctx, java_context_type + " " + comp_name + " = " + _emit_expr(ctx, context_expr) + ";")
        var_name = _str(node, "var_name")
        if var_name != "":
            safe_var = _java_symbol_name(ctx, var_name)
            if safe_var in ctx.var_types:
                _emit(ctx, safe_var + " = " + comp_name + ".__enter__();")
            else:
                ctx.var_types[safe_var] = context_type
                _emit(ctx, java_context_type + " " + safe_var + " = " + comp_name + ".__enter__();")
        else:
            _emit(ctx, java_context_type + " " + entered_name + " = " + comp_name + ".__enter__();")
        for hoisted_name, hoisted_type in _with_hoisted_names(node):
            if _java_symbol_name(ctx, hoisted_name) not in ctx.var_types:
                _emit_name_assignment(ctx, hoisted_name, hoisted_type, java_zero_value(hoisted_type), annotated=True)
        _emit(ctx, "try {")
        ctx.indent_level += 1
        for stmt in _list(node, "body"):
            _emit_stmt(ctx, stmt)
        ctx.indent_level -= 1
        _emit(ctx, "} finally {")
        ctx.indent_level += 1
        _emit(ctx, comp_name + ".__exit__(null, null, null);")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        return
    raise RuntimeError("unsupported_stmt_kind_java: " + kind)


def _collect_module_class_info(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("FunctionDef", "ClosureDef"):
            name = _str(stmt, "name")
            if name != "":
                ctx.function_names.add(name)
                ctx.function_names.add(_java_symbol_name(ctx, name))
                arg_order, arg_types = _arg_order_and_types(stmt)
                positional_arg_types: list[str] = []
                for idx, arg_name in enumerate(arg_order):
                    if idx == 0 and arg_name == "self":
                        continue
                    positional_arg_types.append(arg_types.get(arg_name, "Object"))
                ctx.function_signatures[name] = (positional_arg_types, _function_return_type(stmt))
                vararg_name = _str(stmt, "vararg_name")
                vararg_type = _str(stmt, "vararg_type")
                if vararg_name != "":
                    ctx.function_varargs[name] = vararg_type if vararg_type != "" else "Object"
        if kind == "ClassDef":
            name = _str(stmt, "name")
            if name == "":
                continue
            ctx.class_names.add(name)
            base_name = _str(stmt, "base")
            if base_name != "":
                ctx.class_bases[name] = base_name
                if base_name in ("Enum", "IntEnum", "IntFlag"):
                    ctx.enum_like_names.add(name)


def _build_java_runtime_import_map(meta: dict[str, JsonVal], mapping: RuntimeMapping) -> dict[str, str]:
    runtime_imports = build_runtime_import_map(meta, mapping)
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        bindings = []
    for binding in bindings:
        if not isinstance(binding, dict) or binding.get("binding_kind") != "symbol":
            continue
        local_name = binding.get("local_name")
        if not isinstance(local_name, str) or local_name == "":
            continue
        module_id = binding.get("runtime_module_id")
        if not isinstance(module_id, str) or module_id == "":
            module_id = binding.get("module_id")
        export_name = binding.get("export_name")
        if not isinstance(export_name, str) or export_name == "":
            export_name = local_name
        if module_id != "pytra.built_in.type_id_table":
            if not isinstance(module_id, str) or module_id == "":
                continue
            symbol_name = export_name
            if symbol_name == "":
                symbol_name = local_name
            module_tail = module_id.rsplit(".", 1)[-1] if "." in module_id else module_id
            qualified_symbol = module_tail + "." + symbol_name if module_tail != "" else symbol_name
            if qualified_symbol in mapping.calls:
                runtime_imports[local_name] = mapping.calls[qualified_symbol]
                continue
            if symbol_name in mapping.calls:
                runtime_imports[local_name] = mapping.calls[symbol_name]
                continue
            if not should_skip_module(module_id, mapping):
                runtime_imports[local_name] = _module_class_name(module_id) + "." + _safe_java_ident(export_name)
                continue
            resolved = resolve_runtime_symbol_name(symbol_name, mapping, module_id=module_id)
            if resolved != "":
                runtime_imports[local_name] = resolved
            continue
        runtime_imports[local_name] = _module_class_name(module_id) + "." + _safe_java_ident(export_name)

    import_symbols = meta.get("import_symbols")
    if isinstance(import_symbols, dict):
        for local_name, spec in import_symbols.items():
            if not isinstance(local_name, str) or local_name == "" or local_name in runtime_imports:
                continue
            if not isinstance(spec, dict):
                continue
            module_id = spec.get("module")
            export_name = spec.get("name")
            if not isinstance(module_id, str) or module_id == "":
                continue
            if not isinstance(export_name, str) or export_name == "":
                continue
            if not should_skip_module(module_id, mapping) and module_id != "pytra.built_in.type_id_table":
                continue
            resolved = mapping.calls.get(module_id + "." + export_name, "")
            if not isinstance(resolved, str) or resolved == "":
                resolved = mapping.calls.get(export_name, "")
            if not isinstance(resolved, str) or resolved == "":
                resolved = resolve_runtime_symbol_name(export_name, mapping, module_id=module_id)
            if isinstance(resolved, str) and resolved != "":
                runtime_imports[local_name] = resolved
    return runtime_imports


def _resolve_mapped_ctor_name(ctx: EmitContext, fn_id: str, node: dict[str, JsonVal]) -> str:
    mapped_type = ctx.mapping.types.get(fn_id, "")
    if mapped_type == "":
        return ""
    if fn_id in ctx.class_names or fn_id in ctx.runtime_imports or fn_id in ctx.mapping.calls:
        return ""
    result_type = _str(node, "resolved_type")
    if result_type == "":
        return ""
    if _java_type_in_ctx(ctx, result_type) != mapped_type:
        return ""
    return mapped_type


def _emit_java_type_id_table_module(module_id: str, linked_type_ids: dict[str, int], lp: dict[str, JsonVal]) -> str:
    builtin_type_ids: dict[str, int] = {
        "None": 0,
        "bool": 1,
        "int": 2,
        "float": 3,
        "str": 4,
        "list": 5,
        "dict": 6,
        "set": 7,
        "object": 8,
    }
    type_info_raw = _dict(lp, "type_info_table_v1")
    max_tid = 8
    for value in linked_type_ids.values():
        if value > max_tid:
            max_tid = value
    ranges: list[int] = []
    tid = 0
    while tid <= max_tid:
        ranges.append(tid)
        ranges.append(tid)
        tid += 1
    for builtin_name, builtin_tid in builtin_type_ids.items():
        ranges[builtin_tid * 2] = builtin_tid
        ranges[builtin_tid * 2 + 1] = builtin_tid
    for _name, info in type_info_raw.items():
        if not isinstance(info, dict):
            continue
        type_id_val = info.get("id")
        entry = info.get("entry")
        exit_val = info.get("exit")
        if not isinstance(type_id_val, int) or not isinstance(entry, int) or not isinstance(exit_val, int):
            continue
        base = type_id_val * 2
        if base + 1 >= len(ranges):
            continue
        ranges[base] = entry
        ranges[base + 1] = exit_val - 1

    lines: list[str] = []
    lines.append("import java.util.ArrayList;")
    lines.append("import java.util.HashMap;")
    lines.append("import java.util.HashSet;")
    lines.append("")
    lines.append("public final class " + _module_class_name(module_id) + " {")
    lines.append("")
    lines.append(
        "    public static ArrayList<Long> id_table = new ArrayList<>(java.util.Arrays.asList("
        + ", ".join(str(value) + "L" for value in ranges)
        + "));"
    )
    lines.append("    static {")
    lines.append("        PyRuntime.__pytra_register_type_ranges(id_table);")
    lines.append("    }")

    emitted_consts: set[str] = set()

    def _emit_const(name: str, value: int) -> None:
        safe_name = _safe_java_ident(name)
        if safe_name in emitted_consts:
            return
        emitted_consts.add(safe_name)
        lines.append("    public static long " + safe_name + " = " + str(value) + "L;")

    _emit_const("NONE_TID", 0)
    _emit_const("BOOL_TID", 1)
    _emit_const("INT_TID", 2)
    _emit_const("FLOAT_TID", 3)
    _emit_const("STR_TID", 4)
    _emit_const("LIST_TID", 5)
    _emit_const("DICT_TID", 6)
    _emit_const("SET_TID", 7)
    _emit_const("OBJECT_TID", 8)

    for fqcn, value in sorted(linked_type_ids.items(), key=lambda item: item[1]):
        _emit_const(_fqcn_to_tid_const(fqcn), value)

    lines.append("}")
    return "\n".join(lines) + "\n"


def emit_java_module(east3_doc: dict[str, JsonVal]) -> str:
    meta = _dict(east3_doc, "meta")
    emit_ctx_meta = _dict(meta, "emit_context")
    module_id = _str(emit_ctx_meta, "module_id")
    if module_id == "":
        module_id = _str(meta, "module_id")
    lp = _dict(meta, "linked_program_v1")
    if module_id == "":
        module_id = _str(lp, "module_id")

    if module_id != "":
        expand_cross_module_defaults([(module_id, east3_doc)])

    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "java" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)
    if should_skip_module(module_id, mapping):
        return ""

    renamed_symbols: dict[str, str] = {}
    renamed_symbols_raw = east3_doc.get("renamed_symbols")
    if isinstance(renamed_symbols_raw, dict):
        for key, value in renamed_symbols_raw.items():
            if isinstance(key, str) and isinstance(value, str):
                renamed_symbols[key] = value
    linked_type_ids: dict[str, int] = {}
    type_id_resolved_v1 = _dict(lp, "type_id_resolved_v1")
    for key, value in type_id_resolved_v1.items():
        if isinstance(key, str) and isinstance(value, int):
            linked_type_ids[key] = value

    if module_id == "pytra.built_in.type_id_table":
        return _emit_java_type_id_table_module(module_id, linked_type_ids, lp)

    ctx = EmitContext(
        module_id=module_id,
        source_path=_str(east3_doc, "source_path"),
        is_entry=_bool(emit_ctx_meta, "is_entry"),
        mapping=mapping,
        linked_type_ids=linked_type_ids,
        renamed_symbols=renamed_symbols,
    )
    ctx.import_alias_modules = build_import_alias_map(meta)
    ctx.runtime_imports = _build_java_runtime_import_map(meta, mapping)

    body = _list(east3_doc, "body")
    main_guard_body = _list(east3_doc, "main_guard_body")
    _collect_module_class_info(ctx, body)

    _emit(ctx, "import java.util.ArrayList;")
    _emit(ctx, "import java.util.HashMap;")
    _emit(ctx, "import java.util.HashSet;")
    _emit_blank(ctx)
    _emit(ctx, "public final class " + _module_class_name(module_id) + " {")
    _emit_blank(ctx)
    ctx.indent_level += 1

    _emit_callable_interfaces(ctx, east3_doc)

    for stmt in body:
        _emit_stmt(ctx, stmt)

    if len(main_guard_body) > 0:
        saved_vars = dict(ctx.var_types)
        saved_return_type = ctx.current_return_type
        ctx.var_types = {}
        ctx.current_return_type = "None"
        _emit(ctx, "public static void main(String[] args) {")
        ctx.indent_level += 1
        for stmt in main_guard_body:
            _emit_stmt(ctx, stmt)
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit_blank(ctx)
        ctx.var_types = saved_vars
        ctx.current_return_type = saved_return_type
    elif ctx.is_entry:
        _emit(ctx, "public static void main(String[] args) {")
        _emit(ctx, "}")
        _emit_blank(ctx)

    ctx.indent_level -= 1
    _emit(ctx, "}")
    return "\n".join(ctx.lines).rstrip() + "\n"


__all__ = ["emit_java_module"]
