"""EAST3 -> Lua source code emitter.

Lua emitter は CommonRenderer + override 構成。
Lua 固有のノード（1-based index, nil, tables, metatables 等）のみ override として実装する。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.lua.types import (
    lua_type, lua_zero_value, _safe_lua_ident, _split_generic_args,
    is_numeric_type, is_integer_type,
    LUA_EXCEPTION_TYPE_NAMES, LUA_PATH_TYPE_NAMES,
    LUA_NON_INHERITABLE_BASES, LUA_PYTRA_ISINSTANCE_NAME,
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
    var_types: dict[str, str] = field(default_factory=dict)
    current_return_type: str = ""
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    import_alias_modules: dict[str, str] = field(default_factory=dict)
    runtime_imports: dict[str, str] = field(default_factory=dict)
    class_names: set[str] = field(default_factory=set)
    class_bases: dict[str, str] = field(default_factory=dict)
    class_static_methods: dict[str, set[str]] = field(default_factory=dict)
    class_property_methods: dict[str, set[str]] = field(default_factory=dict)
    class_instance_methods: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    class_fields: dict[str, dict[str, str]] = field(default_factory=dict)
    enum_bases: dict[str, str] = field(default_factory=dict)
    enum_members: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    current_class: str = ""
    exception_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    tid_const_types: dict[str, str] = field(default_factory=dict)
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    temp_counter: int = 0
    current_exc_var: str = ""
    catch_stack: list[tuple[str, str]] = field(default_factory=list)
    vararg_functions: set[str] = field(default_factory=set)
    declared_locals: set[str] = field(default_factory=set)
    hoisted_locals: set[str] = field(default_factory=set)
    in_class_body: bool = False
    needs_continue_label: bool = False
    loaded_module_files: set[str] = field(default_factory=set)


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


def _int(node: dict[str, JsonVal], key: str) -> int:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, int):
            return value
    return 0


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


def _lua_symbol_name(ctx: EmitContext, name: str) -> str:
    """Return safe Lua identifier, applying renamed_symbols."""
    if name == "self":
        return "self"
    name = name.strip("() \t")
    renamed = ctx.renamed_symbols.get(name, "")
    if renamed != "":
        return _safe_lua_ident(renamed)
    return _safe_lua_ident(name)


def _quote_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("\0", "\\0") + '"'


def _lua_module_filename(module_id: str) -> str:
    return module_id.replace(".", "_") + ".lua"


def _emit_module_alias_table(ctx: EmitContext, local_name: str) -> None:
    safe_local = _lua_symbol_name(ctx, local_name)
    alias_expr = 'setmetatable({}, { __index = _G })'
    if safe_local not in ctx.declared_locals:
        ctx.declared_locals.add(safe_local)
        _emit(ctx, "local " + safe_local + " = " + alias_expr)
    else:
        _emit(ctx, safe_local + " = " + alias_expr)


def _is_exception_type_name(ctx: EmitContext, type_name: str) -> bool:
    if type_name in LUA_EXCEPTION_TYPE_NAMES:
        return True
    base = ctx.class_bases.get(type_name, "")
    if base != "":
        return _is_exception_type_name(ctx, base)
    return False


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


def _isinstance_lua_check(obj: str, type_name: str) -> str:
    if type_name in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float", "float32", "float64", "number", "byte"):
        return '(type(' + obj + ') == "number")'
    if type_name in ("bool", "boolean"):
        return '(type(' + obj + ') == "boolean")'
    if type_name in ("str", "string", "char"):
        return '(type(' + obj + ') == "string")'
    if type_name in ("list", "tuple", "dict", "set", "object"):
        return '(type(' + obj + ') == "table")'
    return LUA_PYTRA_ISINSTANCE_NAME + "(" + obj + ", " + _safe_lua_ident(type_name) + ")"


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
    return _isinstance_lua_check(obj, type_name)


def _emit_isinstance_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value_node = node.get("value")
    value = _emit_expr(ctx, value_node)
    value_rt = _str(value_node, "resolved_type") if isinstance(value_node, dict) else ""
    type_name = _str(node, "expected_type_name")
    if type_name == "":
        nominal = _dict(node, "nominal_adt_test_v1")
        if nominal:
            type_name = _str(nominal, "family_name")
            if type_name == "":
                type_name = _str(nominal, "variant_name")
    if type_name == "":
        type_name = _str(node, "type_name")
    if type_name == "":
        expected_type = node.get("expected_type_id")
        if isinstance(expected_type, dict):
            type_name = _str(expected_type, "type_object_of")
            if type_name == "":
                type_name = _str(expected_type, "id")
    if type_name != "":
        if value_rt != "" and value_rt == type_name:
            return "true"
        return _isinstance_lua_check(value, type_name)
    type_names = _list(node, "type_names")
    if len(type_names) > 0:
        checks: list[str] = []
        for item in type_names:
            item_name = item if isinstance(item, str) else ""
            if item_name != "":
                checks.append(_isinstance_lua_check(value, item_name))
        if len(checks) > 0:
            return "(" + " or ".join(checks) + ")"
    expected = node.get("expected_type_id")
    expected_id = _str(expected, "id") if isinstance(expected, dict) else ""
    if expected_id == "PYTRA_TID_DICT":
        return '(type(' + value + ') == "table")'
    if expected_id == "PYTRA_TID_LIST":
        return '(type(' + value + ') == "table")'
    if expected_id == "PYTRA_TID_STR":
        return '(type(' + value + ') == "string")'
    return "false"


def _split_union_types(type_name: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in type_name:
        if ch in "(<[":
            depth += 1
        elif ch in ")>]":
            depth -= 1
        if ch == "|" and depth == 0:
            part = "".join(current).strip()
            if part != "":
                parts.append(part)
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _type_contains(type_name: str, needle: str) -> bool:
    if type_name == needle or type_name.startswith(needle + "["):
        return True
    for part in _split_union_types(type_name):
        if part == needle or part.startswith(needle + "["):
            return True
    return False


def _is_boolean_type(type_name: str) -> bool:
    return type_name in ("bool", "boolean")


def _is_numeric_type(type_name: str) -> bool:
    return type_name in (
        "int", "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "float", "float32", "float64", "byte",
    )


def _is_union_error_return_type(ctx: EmitContext, type_name: str) -> bool:
    if type_name.startswith("multi_return[") and type_name.endswith("]"):
        inner = type_name[len("multi_return["):-1]
        parts = _split_generic_args(inner)
        return len(parts) == 2 and (parts[1] == "PytraError" or _is_exception_type_name(ctx, parts[1]))
    if type_name == "PytraError" or _is_exception_type_name(ctx, type_name):
        return True
    parts = _split_union_types(type_name)
    if len(parts) < 2:
        return False
    has_error = False
    for part in parts:
        if part == "PytraError" or _is_exception_type_name(ctx, part):
            has_error = True
    return has_error


def _union_error_value_type(ctx: EmitContext, type_name: str) -> str:
    if type_name.startswith("multi_return[") and type_name.endswith("]"):
        inner = type_name[len("multi_return["):-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2 and (parts[1] == "PytraError" or _is_exception_type_name(ctx, parts[1])):
            return parts[0]
        return ""
    if type_name == "PytraError" or _is_exception_type_name(ctx, type_name):
        return "None"
    for part in _split_union_types(type_name):
        if part == "PytraError" or _is_exception_type_name(ctx, part):
            continue
        return part
    return ""


def _is_none_error_return_type(ctx: EmitContext, type_name: str) -> bool:
    if not _is_union_error_return_type(ctx, type_name):
        return False
    value_type = _union_error_value_type(ctx, type_name)
    return value_type in ("", "None", "none", "nil")


def _is_guaranteed_lua_truthy_expr(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    kind = _str(node, "kind")
    if kind in ("List", "Tuple", "Dict"):
        return True
    if kind != "Constant":
        return False
    value = node.get("value")
    if value is True:
        return True
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value != ""
    return False


def _emit_cast_call(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    if len(args) == 0:
        return "nil"
    value_node = args[-1]
    value_code = _emit_expr(ctx, value_node)
    target_type = _str(node, "resolved_type")
    if len(args) >= 2 and isinstance(args[0], dict):
        explicit_type = _str(args[0], "type_object_of")
        if explicit_type == "":
            explicit_type = _str(args[0], "id")
        if explicit_type != "":
            target_type = explicit_type
    if target_type in ("int", "int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"):
        return "__pytra_int(" + value_code + ")"
    if target_type in ("float", "float64", "float32"):
        return "__pytra_float(" + value_code + ")"
    if target_type in ("str", "string"):
        return "__pytra_to_string(" + value_code + ")"
    if target_type in ("bool", "boolean"):
        return "__pytra_truthy(" + value_code + ")"
    return value_code


def _emit_bytearray_extend_arg(ctx: EmitContext, owner: str, arg_node: JsonVal) -> str:
    if not isinstance(arg_node, dict):
        return "__pytra_bytearray_extend(" + owner + ", " + _emit_expr(ctx, arg_node) + ")"
    if _str(arg_node, "kind") != "Subscript":
        return "__pytra_bytearray_extend(" + owner + ", " + _emit_expr(ctx, arg_node) + ")"
    slice_node = arg_node.get("slice")
    if not isinstance(slice_node, dict) or _str(slice_node, "kind") != "Slice":
        return "__pytra_bytearray_extend(" + owner + ", " + _emit_expr(ctx, arg_node) + ")"
    value_node = arg_node.get("value")
    if not isinstance(value_node, dict):
        return "__pytra_bytearray_extend(" + owner + ", " + _emit_expr(ctx, arg_node) + ")"
    source_rt = _str(value_node, "resolved_type")
    if source_rt not in ("bytes", "bytearray"):
        return "__pytra_bytearray_extend(" + owner + ", " + _emit_expr(ctx, arg_node) + ")"
    source_code = _emit_expr(ctx, value_node)
    lower = slice_node.get("lower")
    upper = slice_node.get("upper")
    lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "nil"
    upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else "nil"
    return "__pytra_bytearray_extend_slice(" + owner + ", " + source_code + ", " + lower_code + ", " + upper_code + ")"


def _emit_error_propagation(ctx: EmitContext, err_code: str, *, allow_current_catch: bool) -> None:
    if len(ctx.catch_stack) > 0:
        target_index = len(ctx.catch_stack) - 1 if allow_current_catch else len(ctx.catch_stack) - 2
        if target_index >= 0:
            catch_err_var, catch_label = ctx.catch_stack[target_index]
            _emit(ctx, catch_err_var + " = " + err_code)
            _emit(ctx, "goto " + catch_label)
            return
    if _is_none_error_return_type(ctx, ctx.current_return_type):
        _emit(ctx, "return " + err_code)
        return
    if _is_union_error_return_type(ctx, ctx.current_return_type):
        _emit(ctx, "return nil, " + err_code)
        return
    _emit(ctx, "error(" + err_code + ")")


def _emit_error_return(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if isinstance(value, dict):
        err_code = _emit_expr(ctx, value)
    elif ctx.current_exc_var != "":
        err_code = _lua_symbol_name(ctx, ctx.current_exc_var)
    else:
        err_code = _quote_string("raise")
    _emit_error_propagation(ctx, err_code, allow_current_catch=(ctx.current_exc_var == ""))


def _emit_error_check(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    call_node = node.get("call")
    if not isinstance(call_node, dict):
        return
    ok_target = node.get("ok_target")
    ok_type = _str(node, "ok_type")
    on_error = _str(node, "on_error")
    call_code = _emit_expr(ctx, call_node)
    err_tmp = _next_temp(ctx, "err")
    if ok_target is None or ok_type in ("", "None", "none", "nil"):
        _emit(ctx, "local " + err_tmp + " = " + call_code)
        _emit(ctx, "if " + err_tmp + " ~= nil then")
        ctx.indent_level += 1
        _emit_error_propagation(ctx, err_tmp, allow_current_catch=(on_error == "catch"))
        ctx.indent_level -= 1
        _emit(ctx, "end")
        return

    ok_tmp = _next_temp(ctx, "ok")
    _emit(ctx, "local " + ok_tmp + ", " + err_tmp + " = " + call_code)
    _emit(ctx, "if " + err_tmp + " ~= nil then")
    ctx.indent_level += 1
    _emit_error_propagation(ctx, err_tmp, allow_current_catch=(on_error == "catch"))
    ctx.indent_level -= 1
    _emit(ctx, "end")
    assign_node: dict[str, JsonVal] = {
        "kind": "Assign",
        "target": ok_target,
        "value": {"kind": "Name", "id": ok_tmp, "resolved_type": ok_type},
        "declare": isinstance(ok_target, dict) and _str(ok_target, "kind") == "Name" and _lua_symbol_name(ctx, _str(ok_target, "id")) not in ctx.declared_locals,
        "decl_type": ok_type,
        "resolved_type": ok_type,
    }
    _emit_assign(ctx, assign_node)


def _emit_error_catch(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")
    catch_err_var = _next_temp(ctx, "caught_err")
    handler_label = _next_temp(ctx, "catch_handler")
    matched_var = _next_temp(ctx, "catch_matched")

    _emit(ctx, "local " + catch_err_var + " = nil")
    _emit(ctx, "local " + matched_var + " = false")
    _emit(ctx, "repeat")
    ctx.indent_level += 1
    ctx.catch_stack.append((catch_err_var, handler_label))
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "until true")
    _emit(ctx, "::" + handler_label + "::")

    if len(handlers) > 0:
        _emit(ctx, "if " + catch_err_var + " ~= nil then")
        ctx.indent_level += 1
        first = True
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            exc_type_node = handler.get("type")
            exc_type = ""
            if isinstance(exc_type_node, dict):
                exc_type = _str(exc_type_node, "id")
                if exc_type == "":
                    exc_type = _str(exc_type_node, "resolved_type")
            elif isinstance(exc_type_node, str):
                exc_type = exc_type_node
            if exc_type == "":
                cond = "true"
            else:
                cond = LUA_PYTRA_ISINSTANCE_NAME + "(" + catch_err_var + ", " + _safe_lua_ident(exc_type) + ")"
            prefix = "if " if first else "elseif "
            _emit(ctx, prefix + cond + " then")
            ctx.indent_level += 1
            exc_name = _str(handler, "name")
            saved_exc_var = ctx.current_exc_var
            if exc_name != "":
                safe_exc = _lua_symbol_name(ctx, exc_name)
                _emit(ctx, "local " + safe_exc + " = " + catch_err_var)
                ctx.current_exc_var = exc_name
            else:
                reraised_exc = _next_temp(ctx, "reraised_exc")
                _emit(ctx, "local " + reraised_exc + " = " + catch_err_var)
                ctx.current_exc_var = reraised_exc
            _emit(ctx, matched_var + " = true")
            _emit(ctx, catch_err_var + " = nil")
            _emit_body(ctx, _list(handler, "body"))
            ctx.current_exc_var = saved_exc_var
            ctx.indent_level -= 1
            first = False
        if not first:
            _emit(ctx, "end")
        ctx.indent_level -= 1
        _emit(ctx, "end")

    _emit_body(ctx, finalbody)

    _emit(ctx, "if " + catch_err_var + " ~= nil and not " + matched_var + " then")
    ctx.indent_level += 1
    _emit_error_propagation(ctx, catch_err_var, allow_current_catch=False)
    ctx.indent_level -= 1
    _emit(ctx, "end")
    ctx.catch_stack.pop()


# ---------------------------------------------------------------------------
# Expression rendering
# ---------------------------------------------------------------------------

def _emit_expr(ctx: EmitContext, node: JsonVal) -> str:
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
    if kind == "Subscript":
        return _emit_subscript(ctx, node)
    if kind == "BinOp":
        return _emit_binop(ctx, node)
    if kind == "UnaryOp":
        return _emit_unaryop(ctx, node)
    if kind == "Compare":
        return _emit_compare(ctx, node)
    if kind == "BoolOp":
        return _emit_boolop(ctx, node)
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
    if kind == "ListComp":
        return _emit_list_comp(ctx, node)
    if kind == "SetComp":
        return _emit_set_comp(ctx, node)
    if kind == "DictComp":
        return _emit_dict_comp(ctx, node)
    if kind == "GeneratorExp":
        return _emit_list_comp(ctx, node)
    if kind == "Lambda":
        return _emit_lambda(ctx, node)
    if kind == "RangeExpr":
        return _emit_range_expr(ctx, node)
    if kind == "Slice":
        return _emit_slice_expr(ctx, node)
    if kind == "IsInstance":
        return _emit_isinstance_expr(ctx, node)
    if kind == "Box" or kind == "Unbox":
        return _emit_expr(ctx, node.get("value"))
    return "nil --[[ unsupported expr: " + kind + " ]]"


def _emit_constant(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _quote_string(value)
    if isinstance(value, float):
        s = str(value)
        if s == "inf":
            return "math.huge"
        if s == "-inf":
            return "-math.huge"
        if s == "nan":
            return "(0/0)"
        return s
    return str(value)


def _emit_name(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "":
        name = _str(node, "repr")
    if name == "None":
        return "nil"
    if name == "True":
        return "true"
    if name == "False":
        return "false"
    if name in ctx.runtime_imports:
        return ctx.runtime_imports[name]
    return _lua_symbol_name(ctx, name)


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr = _str(node, "attr")
    if isinstance(owner_node, dict):
        if attr == "__name__" and _str(owner_node, "kind") == "Call":
            call_func = owner_node.get("func")
            call_args = _list(owner_node, "args")
            if isinstance(call_func, dict) and _str(call_func, "kind") == "Name" and _str(call_func, "id") == "type" and len(call_args) >= 1:
                return "__pytra_type_name(" + _emit_expr(ctx, call_args[0]) + ")"
        owner = _emit_expr(ctx, owner_node)
        owner_rt = _str(owner_node, "resolved_type")
        if owner_rt in LUA_PATH_TYPE_NAMES and attr in ("name", "stem", "parent"):
            return owner + "." + attr
        if isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
            if _str(node, "attribute_access_kind") == "property_getter":
                return "self:" + _safe_lua_ident(attr) + "()"
            return "self." + _safe_lua_ident(attr)
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
                namespace_expr = ctx.mapping.module_namespace_exprs.get(mod_id, "")
                if namespace_expr != "":
                    return namespace_expr + "." + _safe_lua_ident(attr)
                mod_short = mod_id.rsplit(".", 1)[-1]
                qualified_key = mod_short + "." + runtime_symbol
                if qualified_key in ctx.mapping.calls:
                    return ctx.mapping.calls[qualified_key]
                resolved = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping, module_id=mod_id)
                return resolved
        if _str(node, "attribute_access_kind") == "property_getter":
            return owner + ":" + _safe_lua_ident(attr) + "()"
        if attr in ctx.class_property_methods.get(owner_rt, set()):
            return owner + ":" + _safe_lua_ident(attr) + "()"
    owner = _emit_expr(ctx, owner_node)
    return owner + "." + _safe_lua_ident(attr)


def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    # Check runtime_call mapping
    runtime_call = _str(node, "runtime_call")
    resolved_rt_call = _str(node, "resolved_runtime_call")
    semantic_tag = _str(node, "semantic_tag")
    adapter_kind = _str(node, "runtime_call_adapter_kind")

    args = _list(node, "args")
    arg_strs: list[str] = []
    for a in args:
        arg_strs.append(_emit_expr(ctx, a))
    keywords = _list(node, "keywords")
    func_node = node.get("func")

    meta = node.get("meta")
    copy_elision_meta = meta.get("copy_elision_safe_v1") if isinstance(meta, dict) else None
    copy_elision_safe = (
        isinstance(copy_elision_meta, dict)
        and copy_elision_meta.get("schema_version") == 1
        and copy_elision_meta.get("operation") == "bytes_from_bytearray"
        and len(arg_strs) >= 1
    )

    if (
        (runtime_call == "py_to_string" or resolved_rt_call == "py_to_string" or _str(node, "builtin_name") == "str")
        and len(args) >= 1
    ):
        arg0 = args[0]
        if isinstance(arg0, dict):
            arg0_kind = _str(arg0, "kind")
            arg0_rt = _str(arg0, "resolved_type")
            if arg0_kind == "List" and len(_list(arg0, "elements")) == 0 and arg0_rt.startswith("list["):
                return '"[]"'
            if arg0_kind == "Dict" and len(_list(arg0, "keys")) == 0 and len(_list(arg0, "entries")) == 0 and arg0_rt.startswith("dict["):
                return '"{}"'

    if semantic_tag == "core.bytearray_ctor":
        if len(arg_strs) >= 1:
            return "__pytra_bytearray(" + arg_strs[0] + ")"
        return "__pytra_bytearray()"
    if semantic_tag == "core.bytes_ctor":
        if len(arg_strs) >= 1:
            return "__pytra_bytes(" + arg_strs[0] + ")"
        return "__pytra_bytes()"
    if semantic_tag == "core.dict_ctor":
        if len(arg_strs) >= 1:
            return "__pytra_dict_ctor(" + arg_strs[0] + ")"
        return "{}"
    if semantic_tag == "core.list_ctor":
        if len(arg_strs) >= 1:
            return "__pytra_list_ctor(" + arg_strs[0] + ")"
        return "{}"
    if semantic_tag == "core.set_ctor":
        if len(arg_strs) >= 1:
            return "__pytra_set_ctor(" + arg_strs[0] + ")"
        return "__pytra_set_ctor()"
    if semantic_tag == "core.tuple_ctor":
        return "{" + ", ".join(arg_strs) + "}"

    if runtime_call == "ArgumentParser.add_argument" or resolved_rt_call == "ArgumentParser.add_argument":
        if len(keywords) > 0:
            parts: list[str] = []
            for kw in keywords:
                if not isinstance(kw, dict):
                    continue
                key = kw.get("arg")
                if not isinstance(key, str) or key == "":
                    continue
                parts.append(key + " = " + _emit_expr(ctx, kw.get("value")))
            if len(parts) > 0:
                arg_strs.append("{ " + ", ".join(parts) + " }")

    if runtime_call.startswith("str.") and isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
        owner_node = func_node.get("value")
        owner = _emit_expr(ctx, owner_node)
        return _emit_str_method(ctx, owner, _str(func_node, "attr"), arg_strs)

    # Resolve mapped call name
    call_name = ""
    if runtime_call != "":
        mapped = ctx.mapping.calls.get(runtime_call, "")
        if mapped != "":
            call_name = mapped
    if call_name == "" and resolved_rt_call != "":
        mapped = ctx.mapping.calls.get(resolved_rt_call, "")
        if mapped != "":
            call_name = mapped

    if (
        (
            call_name.startswith("__LIST_")
            or call_name.startswith("__DICT_")
            or call_name.startswith("__SET_")
            or call_name.startswith("__BYTEARRAY_")
        )
        and isinstance(func_node, dict)
        and _str(func_node, "kind") == "Attribute"
    ):
        owner_node = func_node.get("value")
        if isinstance(owner_node, dict):
            arg_strs = [_emit_expr(ctx, owner_node)] + arg_strs

    # Special markers
    if call_name == "__CAST__":
        return _emit_cast_call(ctx, node, args)

    if call_name == "__PANIC__":
        msg = arg_strs[0] if len(arg_strs) > 0 else '"error"'
        return 'error(' + msg + ')'

    if call_name == "__pytra_len" and len(args) >= 1:
        arg0 = args[0]
        arg0_code = arg_strs[0]
        arg0_rt = _str(arg0, "resolved_type") if isinstance(arg0, dict) else ""
        if arg0_rt in ("str", "string", "list", "tuple", "bytearray") or arg0_rt.startswith("list[") or arg0_rt.startswith("tuple["):
            return "#(" + arg0_code + ")"
        if _type_contains(arg0_rt, "deque"):
            return "#(" + arg0_code + "._items)"

    # Container operation markers
    if call_name == "__LIST_APPEND__":
        if len(arg_strs) >= 2:
            return "__pytra_list_append(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__LIST_POP__":
        if len(arg_strs) >= 2:
            return "table.remove(" + arg_strs[0] + ", " + arg_strs[1] + " + 1)"
        if len(arg_strs) >= 1:
            return "table.remove(" + arg_strs[0] + ")"
        return "nil"

    if call_name == "__LIST_CLEAR__":
        if len(arg_strs) >= 1:
            return "__pytra_list_clear(" + arg_strs[0] + ")"
        return "nil"

    if call_name == "__LIST_INDEX__":
        if len(arg_strs) >= 2:
            return "__pytra_list_index(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__LIST_EXTEND__":
        if len(arg_strs) >= 2:
            return "__pytra_list_extend(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__LIST_INSERT__":
        if len(arg_strs) >= 3:
            return "table.insert(" + arg_strs[0] + ", " + arg_strs[1] + " + 1, " + arg_strs[2] + ")"
        return "nil"

    if call_name == "__LIST_REMOVE__":
        if len(arg_strs) >= 2:
            return "__pytra_list_remove(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__LIST_REVERSE__":
        if len(arg_strs) >= 1:
            return "__pytra_list_reverse(" + arg_strs[0] + ")"
        return "nil"

    if call_name == "__LIST_SORT__":
        if len(arg_strs) >= 1:
            return "table.sort(" + arg_strs[0] + ")"
        return "nil"

    if call_name == "__LIST_CTOR__":
        if len(arg_strs) >= 1:
            return "__pytra_list_ctor(" + arg_strs[0] + ")"
        return "{}"

    if call_name == "__TUPLE_CTOR__":
        if len(arg_strs) >= 1:
            return "__pytra_list_ctor(" + arg_strs[0] + ")"
        return "{}"

    if call_name == "__SET_CTOR__":
        if len(arg_strs) >= 1:
            return "__pytra_set_ctor(" + arg_strs[0] + ")"
        return "{}"

    if call_name == "__SET_ADD__":
        if len(arg_strs) >= 2:
            return "__pytra_set_add(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__SET_DISCARD__":
        if len(arg_strs) >= 2:
            return "__pytra_set_discard(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__SET_REMOVE__":
        if len(arg_strs) >= 2:
            return "__pytra_set_remove(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__SET_CLEAR__":
        if len(arg_strs) >= 1:
            return "__pytra_set_clear(" + arg_strs[0] + ")"
        return "nil"

    if call_name == "__SET_UPDATE__":
        if len(arg_strs) >= 2:
            return "__pytra_set_update(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__BYTEARRAY_APPEND__":
        if len(arg_strs) >= 2:
            return "__pytra_bytearray_append(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__BYTEARRAY_EXTEND__":
        if len(arg_strs) >= 2:
            return "__pytra_bytearray_extend(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__DICT_GET__":
        if len(arg_strs) >= 3:
            return "__pytra_dict_get(" + arg_strs[0] + ", " + arg_strs[1] + ", " + arg_strs[2] + ")"
        if len(arg_strs) >= 2:
            return "__pytra_dict_get(" + arg_strs[0] + ", " + arg_strs[1] + ", nil)"
        return "nil"

    if call_name == "__DICT_ITEMS__":
        if len(arg_strs) >= 1:
            return "__pytra_dict_items(" + arg_strs[0] + ")"
        return "{}"

    if call_name == "__DICT_KEYS__":
        if len(arg_strs) >= 1:
            return "__pytra_dict_keys(" + arg_strs[0] + ")"
        return "{}"

    if call_name == "__DICT_VALUES__":
        if len(arg_strs) >= 1:
            return "__pytra_dict_values(" + arg_strs[0] + ")"
        return "{}"

    if call_name == "__DICT_POP__":
        if len(arg_strs) >= 2:
            return "__pytra_dict_pop(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__DICT_UPDATE__":
        if len(arg_strs) >= 2:
            return "__pytra_dict_update(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__DICT_SETDEFAULT__":
        if len(arg_strs) >= 3:
            return "__pytra_dict_setdefault(" + arg_strs[0] + ", " + arg_strs[1] + ", " + arg_strs[2] + ")"
        return "nil"

    if call_name == "__LIST_APPEND__":
        if len(arg_strs) >= 2:
            return "__pytra_list_append(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__LIST_CLEAR__":
        if len(arg_strs) >= 1:
            return "__pytra_list_clear(" + arg_strs[0] + ")"
        return "nil"

    if call_name == "__LIST_EXTEND__":
        if len(arg_strs) >= 2:
            return "__pytra_list_extend(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "nil"

    if call_name == "__LIST_INSERT__":
        if len(arg_strs) >= 3:
            return "table.insert(" + arg_strs[0] + ", (" + arg_strs[1] + ") + 1, " + arg_strs[2] + ")"
        return "nil"

    if call_name == "__LIST_INDEX__":
        if len(arg_strs) >= 2:
            return "__pytra_list_index(" + arg_strs[0] + ", " + arg_strs[1] + ")"
        return "-1"

    if call_name == "__LIST_POP__":
        if len(arg_strs) >= 2:
            return "table.remove(" + arg_strs[0] + ", (" + arg_strs[1] + ") + 1)"
        if len(arg_strs) >= 1:
            return "table.remove(" + arg_strs[0] + ")"
        return "nil"

    # Resolved mapped name
    if call_name != "":
        call_args = list(arg_strs)
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
            owner_node = func_node.get("value")
            owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
            owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            if not (owner_rt == "module" or owner_id in ctx.import_alias_modules):
                call_args = [_emit_expr(ctx, owner_node)] + call_args
        return call_name + "(" + ", ".join(call_args) + ")"

    # Fallback: emit callee from func node
    if isinstance(func_node, dict):
        func_id = _str(func_node, "id")

        # Try mapping by bare function name
        if call_name == "" and func_id != "":
            if func_id == "isinstance" and len(args) >= 2 and isinstance(args[0], dict) and isinstance(args[1], dict):
                type_node = args[1]
                type_name = _str(type_node, "id")
                if type_name == "":
                    type_name = _str(type_node, "repr")
                return _emit_isinstance_expr(ctx, {"kind": "IsInstance", "value": args[0], "expected_type_name": type_name})
            if func_id == LUA_PYTRA_ISINSTANCE_NAME:
                linked = _emit_linked_type_id_isinstance(ctx, args)
                if linked is not None:
                    return linked
            mapped = ctx.mapping.calls.get(func_id, "")
            if mapped != "":
                if mapped == "__CAST__":
                    return _emit_cast_call(ctx, node, args)
                if mapped == "__PANIC__":
                    msg = arg_strs[0] if len(arg_strs) > 0 else '"error"'
                    return "error(" + msg + ")"
                return mapped + "(" + ", ".join(arg_strs) + ")"

        callee = _emit_expr(ctx, func_node)

        # Class constructor call
        if func_id in ctx.class_names:
            return _emit_class_ctor_call(ctx, func_id, arg_strs)

        # Exception constructors
        if _is_exception_type_name(ctx, func_id):
            return _safe_lua_ident(func_id) + ".new(" + ", ".join(arg_strs) + ")"

        # Method calls on objects (obj:method pattern)
        if _str(func_node, "kind") == "Attribute":
            owner_node = func_node.get("value")
            attr = _str(func_node, "attr")
            if isinstance(owner_node, dict):
                owner = _emit_expr(ctx, owner_node)
                owner_rt = _str(owner_node, "resolved_type")
                owner_id = _str(owner_node, "id")
                dispatch_kind = _str(node, "call_dispatch_kind")
                if owner_rt == "module" or owner_id in ctx.import_alias_modules:
                    mod_id = _str(func_node, "runtime_module_id")
                    if mod_id == "":
                        mod_id = ctx.import_alias_modules.get(owner_id, "")
                    if should_skip_module(mod_id, ctx.mapping):
                        runtime_symbol = _str(node, "runtime_symbol")
                        if runtime_symbol == "":
                            runtime_symbol = _str(func_node, "runtime_symbol")
                        if runtime_symbol == "":
                            runtime_symbol = attr
                        mod_short = mod_id.rsplit(".", 1)[-1]
                        qualified_key = mod_short + "." + runtime_symbol
                        mapped = ctx.mapping.calls.get(qualified_key, "")
                        if mapped != "":
                            return mapped + "(" + ", ".join(arg_strs) + ")"
                    return owner + "." + _safe_lua_ident(attr) + "(" + ", ".join(arg_strs) + ")"
                if dispatch_kind == "static_method" or (owner_id in ctx.class_names and attr in ctx.class_static_methods.get(owner_id, set())):
                    return owner + "." + _safe_lua_ident(attr) + "(" + ", ".join(arg_strs) + ")"
                # String methods
                if owner_rt == "str" or owner_rt == "string":
                    return _emit_str_method(ctx, owner, attr, arg_strs)
                owner_method_key = ""
                if _type_contains(owner_rt, "dict"):
                    owner_method_key = "dict." + attr
                elif _type_contains(owner_rt, "set"):
                    owner_method_key = "set." + attr
                elif owner_rt.startswith("list[") or owner_rt == "list":
                    owner_method_key = "list." + attr
                elif owner_rt == "bytearray":
                    owner_method_key = "bytearray." + attr
                if owner_method_key != "":
                    mapped_owner_call = ctx.mapping.calls.get(owner_method_key, "")
                    owner_args = [owner] + arg_strs
                    if mapped_owner_call == "__DICT_GET__":
                        if len(owner_args) >= 3:
                            return "__pytra_dict_get(" + owner_args[0] + ", " + owner_args[1] + ", " + owner_args[2] + ")"
                        if len(owner_args) >= 2:
                            return "__pytra_dict_get(" + owner_args[0] + ", " + owner_args[1] + ", nil)"
                        return "nil"
                    if mapped_owner_call == "__pytra_clear__":
                        return "__pytra_clear(" + owner + ")"
                    if mapped_owner_call == "__DICT_ITEMS__":
                        return "__pytra_dict_items(" + owner + ")"
                    if mapped_owner_call == "__DICT_KEYS__":
                        return "__pytra_dict_keys(" + owner + ")"
                    if mapped_owner_call == "__DICT_VALUES__":
                        return "__pytra_dict_values(" + owner + ")"
                    if mapped_owner_call == "__SET_ADD__":
                        if len(owner_args) >= 2:
                            return "__pytra_set_add(" + owner_args[0] + ", " + owner_args[1] + ")"
                        return "nil"
                    if mapped_owner_call == "__SET_DISCARD__":
                        if len(owner_args) >= 2:
                            return "__pytra_set_discard(" + owner_args[0] + ", " + owner_args[1] + ")"
                        return "nil"
                    if mapped_owner_call == "__SET_REMOVE__":
                        if len(owner_args) >= 2:
                            return "__pytra_set_remove(" + owner_args[0] + ", " + owner_args[1] + ")"
                        return "nil"
                    if mapped_owner_call == "__LIST_APPEND__":
                        if len(owner_args) >= 2:
                            return "__pytra_list_append(" + owner_args[0] + ", " + owner_args[1] + ")"
                        return "nil"
                    if mapped_owner_call == "__LIST_CLEAR__":
                        return "__pytra_list_clear(" + owner + ")"
                    if mapped_owner_call == "__LIST_EXTEND__":
                        if len(owner_args) >= 2:
                            return "__pytra_list_extend(" + owner_args[0] + ", " + owner_args[1] + ")"
                        return "nil"
                    if mapped_owner_call == "__BYTEARRAY_APPEND__":
                        if len(owner_args) >= 2:
                            return "__pytra_bytearray_append(" + owner_args[0] + ", " + owner_args[1] + ")"
                        return "nil"
                    if mapped_owner_call == "__BYTEARRAY_EXTEND__":
                        if len(arg_strs) >= 1:
                            return _emit_bytearray_extend_arg(ctx, owner, args[0])
                        return "nil"
                # Path methods
                if owner_rt in LUA_PATH_TYPE_NAMES:
                    return _emit_path_method(ctx, owner, attr, arg_strs)
                if attr == "as_str":
                    return "tostring(" + owner + ")"
                if attr == "as_arr":
                    return owner
                return owner + ":" + _safe_lua_ident(attr) + "(" + ", ".join(arg_strs) + ")"

        if _str(func_node, "kind") == "Lambda":
            callee = "(" + callee + ")"
        return callee + "(" + ", ".join(arg_strs) + ")"

    return "nil"


def _needs_checked_runtime_call(ctx: EmitContext, value: JsonVal) -> bool:
    if len(ctx.catch_stack) == 0 or not isinstance(value, dict):
        return False
    if _str(value, "kind") != "Call":
        return False
    runtime_call = _str(value, "resolved_runtime_call")
    if runtime_call == "":
        runtime_call = _str(value, "runtime_call")
    adapter_kind = _str(value, "runtime_call_adapter_kind")
    fn_name = resolve_runtime_call(runtime_call, "", adapter_kind, ctx.mapping)
    return fn_name == "__pytra_str_index"


def _emit_checked_runtime_call(ctx: EmitContext, value: dict[str, JsonVal], target_code: str, *, declare_local: bool, decl_type: str = "") -> bool:
    if not _needs_checked_runtime_call(ctx, value):
        return False
    call_code = _emit_expr(ctx, value)
    ok_tmp = _next_temp(ctx, "ok")
    res_tmp = _next_temp(ctx, "res")
    _emit(ctx, "local " + ok_tmp + ", " + res_tmp + " = pcall(function() return " + call_code + " end)")
    _emit(ctx, "if not " + ok_tmp + " then")
    ctx.indent_level += 1
    _emit_error_propagation(ctx, res_tmp, allow_current_catch=True)
    ctx.indent_level -= 1
    _emit(ctx, "end")
    if declare_local:
        _emit(ctx, "local " + target_code + " = " + res_tmp)
        ctx.declared_locals.add(target_code)
        if decl_type != "":
            ctx.var_types[target_code] = decl_type
    else:
        _emit(ctx, target_code + " = " + res_tmp)
    return True


def _emit_class_ctor_call(ctx: EmitContext, class_name: str, arg_strs: list[str]) -> str:
    safe = _safe_lua_ident(class_name)
    return safe + ".new(" + ", ".join(arg_strs) + ")"


def _emit_str_method(ctx: EmitContext, owner: str, method: str, args: list[str]) -> str:
    """Emit string method calls using mapping or inline."""
    key = "str." + method
    if key in ctx.mapping.calls:
        mapped = ctx.mapping.calls[key]
        return mapped + "(" + owner + (", " + ", ".join(args) if len(args) > 0 else "") + ")"
    # Fallback for unmapped string methods
    if method == "format":
        return "string.format(" + owner + (", " + ", ".join(args) if len(args) > 0 else "") + ")"
    return owner + ":" + method + "(" + ", ".join(args) + ")"


def _emit_path_method(ctx: EmitContext, owner: str, method: str, args: list[str]) -> str:
    if method == "exists":
        return owner + ":exists()"
    if method == "mkdir":
        return owner + ":mkdir()"
    if method == "write_text":
        return owner + ":write_text(" + ", ".join(args) + ")"
    if method == "read_text":
        return owner + ":read_text()"
    return owner + ":" + method + "(" + ", ".join(args) + ")"


def _emit_subscript(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    if owner_rt in ("", "unknown") and isinstance(owner_node, dict) and _str(owner_node, "kind") == "Attribute":
        attr = _str(owner_node, "attr")
        owner_base = owner_node.get("value")
        if isinstance(owner_base, dict) and _str(owner_base, "kind") == "Name":
            owner_base_id = _str(owner_base, "id")
            owner_rt = ctx.class_fields.get(owner_base_id, {}).get(attr, owner_rt)
    slice_node = node.get("slice")
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "nil"
        upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else "nil"
        return "__pytra_slice(" + owner + ", " + lower_code + ", " + upper_code + ")"
    is_dict_type = owner_rt.startswith("dict[") or owner_rt == "dict"
    if is_dict_type and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        return owner + "[" + slice_code + "]"
    # For lists: adjust to 1-based index
    is_list_type = owner_rt.startswith("list[") or owner_rt in ("list", "bytes", "bytearray")
    is_tuple_type = owner_rt.startswith("tuple[") or owner_rt == "tuple"
    is_str_type = owner_rt in ("str", "string")
    if (is_list_type or is_tuple_type) and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        neg_val = _get_negative_int_literal(slice_node)
        if neg_val is not None:
            return owner + "[#" + owner + " + " + str(neg_val) + " + 1]"
        return owner + "[" + slice_code + " + 1]"
    if is_str_type and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        value_rt = _str(node, "resolved_type")
        neg_val = _get_negative_int_literal(slice_node)
        if neg_val is not None:
            idx = owner + ":len() + " + str(neg_val) + " + 1"
            if value_rt == "byte":
                return "string.byte(" + owner + ", " + idx + ")"
            return "string.sub(" + owner + ", " + idx + ", " + idx + ")"
        if value_rt == "byte":
            return "string.byte(" + owner + ", " + slice_code + " + 1)"
        return "string.sub(" + owner + ", " + slice_code + " + 1, " + slice_code + " + 1)"
    # Fallback
    if isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        return owner + "[" + slice_code + "]"
    return owner


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


def _subscript_access_hint(node: dict[str, JsonVal]) -> dict[str, JsonVal] | None:
    meta_obj = node.get("meta")
    meta = meta_obj if isinstance(meta_obj, dict) else None
    if meta is None:
        return None
    hint_obj = meta.get("subscript_access_v1")
    hint = hint_obj if isinstance(hint_obj, dict) else None
    if hint is None:
        return None
    if _str(hint, "schema_version") != "subscript_access_v1":
        return None
    negative_index = _str(hint, "negative_index")
    bounds_check = _str(hint, "bounds_check")
    if negative_index not in ("normalize", "skip"):
        return None
    if bounds_check not in ("full", "off"):
        return None
    return hint


def _emit_checked_subscript_call(ctx: EmitContext, value: JsonVal) -> str:
    if not isinstance(value, dict) or _str(value, "kind") != "Subscript":
        return ""
    hint = _subscript_access_hint(value)
    if hint is not None and _str(hint, "bounds_check") == "off" and _str(hint, "negative_index") == "skip":
        return ""
    owner_node = value.get("value")
    if not isinstance(owner_node, dict):
        return ""
    owner = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type")
    slice_node = value.get("slice")
    if not isinstance(slice_node, dict) or _str(slice_node, "kind") == "Slice":
        return ""
    slice_code = _emit_expr(ctx, slice_node)
    is_list_type = owner_rt.startswith("list[") or owner_rt in ("list", "bytes", "bytearray")
    is_tuple_type = owner_rt.startswith("tuple[") or owner_rt == "tuple"
    if is_list_type or is_tuple_type:
        return "__pytra_seq_get_checked(" + owner + ", " + slice_code + ")"
    if owner_rt in ("str", "string"):
        value_rt = _str(value, "resolved_type")
        if value_rt == "byte":
            return "__pytra_str_byte_get_checked(" + owner + ", " + slice_code + ")"
        return "__pytra_str_get_checked(" + owner + ", " + slice_code + ")"
    return ""


def _is_lua_one(code: str) -> bool:
    return code.replace(" ", "") in ("1", "(1)")


def _is_lua_minus_one(code: str) -> bool:
    return code.replace(" ", "") in ("-1", "(-1)")


def _emit_binop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    op = _str(node, "op")
    left_rt = ""
    right_rt = ""
    left_node = node.get("left")
    right_node = node.get("right")
    if isinstance(left_node, dict):
        left_rt = _str(left_node, "resolved_type")
    if isinstance(right_node, dict):
        right_rt = _str(right_node, "resolved_type")
    # String concatenation
    if op == "Add" and (left_rt == "str" or right_rt == "str"):
        return "(" + left + " .. " + right + ")"
    if op == "Add":
        if left_rt.startswith("list[") or right_rt.startswith("list[") or left_rt == "list" or right_rt == "list":
            return "__pytra_list_concat(" + left + ", " + right + ")"
    # Floor division
    if op == "FloorDiv":
        return "__pytra_floordiv(" + left + ", " + right + ")"
    # Bitwise ops (Lua 5.4 has native bitwise)
    if op == "BitAnd":
        return "(__pytra_int(" + left + ") & __pytra_int(" + right + "))"
    if op == "BitOr":
        return "(__pytra_int(" + left + ") | __pytra_int(" + right + "))"
    if op == "BitXor":
        return "(__pytra_int(" + left + ") ~ __pytra_int(" + right + "))"
    if op == "LShift":
        return "(__pytra_int(" + left + ") << __pytra_int(" + right + "))"
    if op == "RShift":
        return "(__pytra_int(" + left + ") >> __pytra_int(" + right + "))"
    # Path concatenation
    if op == "Div" and (left_rt in LUA_PATH_TYPE_NAMES or right_rt in LUA_PATH_TYPE_NAMES):
        return "__pytra_path_new(__pytra_path_join(" + left + ".path or " + left + ", tostring(" + right + ")))"
    # Multiplication with string/list (repeat)
    if op == "Mult":
        if left_rt == "str" or right_rt == "str":
            return "__pytra_repeat_seq(" + left + ", " + right + ")"
        if left_rt.startswith("list[") or right_rt.startswith("list["):
            return "__pytra_repeat_seq(" + left + ", " + right + ")"
    # Normal operators
    op_map: dict[str, str] = {
        "Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
        "Mod": "%", "Pow": "^",
    }
    lua_op = op_map.get(op, op)
    return "(" + left + " " + lua_op + " " + right + ")"


def _emit_unaryop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    if op == "Not":
        return "(not " + operand + ")"
    if op == "USub":
        return "(-" + operand + ")"
    if op == "Invert":
        return "(~" + operand + ")"
    if op == "UAdd":
        return operand
    return operand


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return left
    parts: list[str] = []
    current_left = left
    current_left_node = node.get("left")
    for idx, comparator in enumerate(comparators):
        op_obj = ops[idx] if idx < len(ops) else None
        op_name = op_obj if isinstance(op_obj, str) else ""
        if isinstance(op_obj, dict):
            op_name = _str(op_obj, "kind")
        right = _emit_expr(ctx, comparator)
        cmp_op = _cmp_op_text(op_name)
        if cmp_op == "__IN__":
            right_rt = _str(comparator, "resolved_type") if isinstance(comparator, dict) else ""
            if _type_contains(right_rt, "dict"):
                parts.append("(" + right + "[" + current_left + "] ~= nil)")
            else:
                parts.append("__pytra_contains(" + right + ", " + current_left + ")")
        elif cmp_op == "__NOT_IN__":
            right_rt = _str(comparator, "resolved_type") if isinstance(comparator, dict) else ""
            if _type_contains(right_rt, "dict"):
                parts.append("(" + right + "[" + current_left + "] == nil)")
            else:
                parts.append("(not __pytra_contains(" + right + ", " + current_left + "))")
        elif cmp_op == "__IS__":
            parts.append("(" + current_left + " == " + right + ")")
        elif cmp_op == "__IS_NOT__":
            parts.append("(" + current_left + " ~= " + right + ")")
        else:
            parts.append("(" + current_left + " " + cmp_op + " " + right + ")")
        current_left = right
        current_left_node = comparator
    if len(parts) == 1:
        return parts[0]
    return "(" + " and ".join(parts) + ")"


def _cmp_op_text(op: str) -> str:
    m: dict[str, str] = {
        "Eq": "==", "NotEq": "~=", "Lt": "<", "LtE": "<=",
        "Gt": ">", "GtE": ">=", "In": "__IN__", "NotIn": "__NOT_IN__",
        "Is": "__IS__", "IsNot": "__IS_NOT__",
    }
    return m.get(op, op)


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    op = _str(node, "op")
    if len(values) == 0:
        return "nil"
    node_rt = _str(node, "resolved_type")
    if _is_boolean_type(node_rt):
        parts: list[str] = []
        for value in values:
            if not isinstance(value, dict) or not _is_boolean_type(_str(value, "resolved_type")):
                parts = []
                break
            parts.append("(" + _emit_expr(ctx, value) + ")")
        if len(parts) == len(values):
            sep = " and " if op == "And" else " or "
            return "(" + sep.join(parts) + ")"
    current = _emit_expr(ctx, values[0])
    for value in values[1:]:
        right = _emit_expr(ctx, value)
        if op == "And":
            tmp = _next_temp(ctx, "boolop")
            current = (
                "(function() local " + tmp + " = " + current
                + "; if __pytra_truthy(" + tmp + ") then return " + right
                + " else return " + tmp + " end end)()"
            )
        else:
            tmp = _next_temp(ctx, "boolop")
            current = (
                "(function() local " + tmp + " = " + current
                + "; if __pytra_truthy(" + tmp + ") then return " + tmp
                + " else return " + right + " end end)()"
            )
    return "(" + current + ")"


def _emit_condition(ctx: EmitContext, node: JsonVal) -> str:
    expr = _emit_expr(ctx, node)
    if isinstance(node, dict):
        resolved_type = _str(node, "resolved_type")
        if _is_boolean_type(resolved_type):
            return expr
        if _is_numeric_type(resolved_type):
            return "(" + expr + " ~= 0)"
        if resolved_type in ("str", "string"):
            return "(#" + expr + " ~= 0)"
    return "__pytra_truthy(" + expr + ")"


def _emit_list_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    return "{" + ", ".join(elem_strs) + "}"


def _emit_dict_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    entries = _list(node, "entries")
    pairs: list[str] = []
    if len(entries) > 0:
        for entry in entries:
            if isinstance(entry, dict):
                kc = _emit_expr(ctx, entry.get("key"))
                vc = _emit_expr(ctx, entry.get("value"))
                pairs.append("[" + kc + "] = " + vc)
    else:
        keys = _list(node, "keys")
        values = _list(node, "values")
        for idx, key in enumerate(keys):
            kc = _emit_expr(ctx, key)
            val_node = values[idx] if idx < len(values) else None
            vc = _emit_expr(ctx, val_node) if val_node is not None else "nil"
            pairs.append("[" + kc + "] = " + vc)
    return "{" + ", ".join(pairs) + "}"


def _emit_set_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    pairs: list[str] = []
    for e in elements:
        ec = _emit_expr(ctx, e)
        pairs.append("[" + ec + "] = true")
    return "{" + ", ".join(pairs) + "}"


def _emit_tuple_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    return "__pytra_tuple({" + ", ".join(elem_strs) + "})"


def _emit_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test_node = node.get("test")
    body_node = node.get("body")
    orelse_node = node.get("orelse")
    test = _emit_condition(ctx, test_node)
    body = _emit_expr(ctx, body_node)
    orelse = _emit_expr(ctx, orelse_node)
    if _is_guaranteed_lua_truthy_expr(body_node):
        return "((" + test + ") and (" + body + ") or (" + orelse + "))"
    if _is_guaranteed_lua_truthy_expr(orelse_node):
        return "((not (" + test + ")) and (" + orelse + ") or (" + body + "))"
    return "(__pytra_ternary(" + test + ", " + body + ", " + orelse + "))"


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
                parts.append(_quote_string(raw_val))
            continue
        if vk == "FormattedValue":
            inner = v.get("value")
            fmt_spec = _str(v, "format_spec")
            if fmt_spec != "":
                parts.append('__pytra_fmt(' + _emit_expr(ctx, inner) + ', "' + fmt_spec.replace('"', '\\"') + '")')
            else:
                parts.append("tostring(" + _emit_expr(ctx, inner) + ")")
            continue
        parts.append("tostring(" + _emit_expr(ctx, v) + ")")
    if len(parts) == 0:
        return '""'
    return " .. ".join(parts)


def _emit_list_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    """Emit list comprehension as an IIFE."""
    elt = node.get("elt")
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "{}"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "{}"
    target = gen.get("target")
    iter_node = gen.get("iter")
    ifs = _list(gen, "ifs")

    target_code = _emit_expr(ctx, target) if isinstance(target, dict) else "_"
    iter_code = _emit_expr(ctx, iter_node)
    elt_code = _emit_expr(ctx, elt)

    result = "(function()"
    result += " local __r = {};"
    iter_rt = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
    is_dict = iter_rt.startswith("dict[") or iter_rt == "dict"
    is_str = iter_rt in ("str", "string")
    if isinstance(iter_node, dict) and _str(iter_node, "kind") == "RangeExpr":
        start = _emit_expr(ctx, iter_node.get("start")) if isinstance(iter_node.get("start"), dict) else "0"
        stop = _emit_expr(ctx, iter_node.get("stop")) if isinstance(iter_node.get("stop"), dict) else "0"
        step = _emit_expr(ctx, iter_node.get("step")) if isinstance(iter_node.get("step"), dict) else "1"
        if _is_lua_one(step):
            result += " for " + target_code + " = " + start + ", " + stop + " - 1 do"
        elif _is_lua_minus_one(step):
            result += " for " + target_code + " = " + start + ", " + stop + " + 1, -1 do"
        else:
            result += " for " + target_code + " = " + start + ", " + stop + " - 1, " + step + " do"
    elif is_dict:
        result += " for " + target_code + ", _ in pairs(" + iter_code + ") do"
    elif is_str:
        result += " for __i = 1, #" + iter_code + " do local " + target_code + " = string.sub(" + iter_code + ", __i, __i);"
    elif isinstance(target, dict) and _str(target, "kind") == "Tuple":
        temp_item = "__item"
        result += " for _, " + temp_item + " in ipairs(" + iter_code + ") do"
        for i, elem in enumerate(_list(target, "elements")):
            if isinstance(elem, dict):
                result += " local " + _emit_expr(ctx, elem) + " = " + temp_item + "[" + str(i + 1) + "];"
    else:
        result += " for _, " + target_code + " in ipairs(" + iter_code + ") do"
    if len(ifs) > 0:
        cond = _emit_expr(ctx, ifs[0])
        result += " if " + cond + " then"
        result += " __r[#__r + 1] = " + elt_code + ";"
        result += " end"
    else:
        result += " __r[#__r + 1] = " + elt_code + ";"
    result += " end;"
    result += " return __r"
    result += " end)()"
    return result


def _emit_comp_loop_prefix(
    ctx: EmitContext,
    target: JsonVal,
    iter_node: JsonVal,
    target_code: str,
    iter_code: str,
) -> str:
    iter_rt = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
    is_dict = iter_rt.startswith("dict[") or iter_rt == "dict"
    is_str = iter_rt in ("str", "string")
    if isinstance(iter_node, dict) and _str(iter_node, "kind") == "RangeExpr":
        start = _emit_expr(ctx, iter_node.get("start")) if isinstance(iter_node.get("start"), dict) else "0"
        stop = _emit_expr(ctx, iter_node.get("stop")) if isinstance(iter_node.get("stop"), dict) else "0"
        step = _emit_expr(ctx, iter_node.get("step")) if isinstance(iter_node.get("step"), dict) else "1"
        if _is_lua_one(step):
            return " for " + target_code + " = " + start + ", " + stop + " - 1 do"
        if _is_lua_minus_one(step):
            return " for " + target_code + " = " + start + ", " + stop + " + 1, -1 do"
        return " for " + target_code + " = " + start + ", " + stop + " - 1, " + step + " do"
    if is_dict:
        return " for " + target_code + ", _ in pairs(" + iter_code + ") do"
    if is_str:
        return " for __i = 1, #" + iter_code + " do local " + target_code + " = string.sub(" + iter_code + ", __i, __i);"
    if isinstance(target, dict) and _str(target, "kind") == "Tuple":
        temp_item = "__item"
        result = " for _, " + temp_item + " in ipairs(" + iter_code + ") do"
        for i, elem in enumerate(_list(target, "elements")):
            if isinstance(elem, dict):
                result += " local " + _emit_expr(ctx, elem) + " = " + temp_item + "[" + str(i + 1) + "];"
        return result
    return " for _, " + target_code + " in ipairs(" + iter_code + ") do"


def _emit_set_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = node.get("elt")
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "{}"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "{}"
    target = gen.get("target")
    iter_node = gen.get("iter")
    ifs = _list(gen, "ifs")
    target_code = _emit_expr(ctx, target) if isinstance(target, dict) else "_"
    iter_code = _emit_expr(ctx, iter_node)
    elt_code = _emit_expr(ctx, elt)
    result = "(function() local __r = {};"
    result += _emit_comp_loop_prefix(ctx, target, iter_node, target_code, iter_code)
    if len(ifs) > 0:
        result += " if " + _emit_expr(ctx, ifs[0]) + " then"
        result += " __r[" + elt_code + "] = true;"
        result += " end"
    else:
        result += " __r[" + elt_code + "] = true;"
    result += " end; return __r end)()"
    return result


def _emit_dict_comp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    key_code = _emit_expr(ctx, node.get("key"))
    value_code = _emit_expr(ctx, node.get("value"))
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "{[" + key_code + "] = " + value_code + "}"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "{[" + key_code + "] = " + value_code + "}"
    target = gen.get("target")
    iter_node = gen.get("iter")
    ifs = _list(gen, "ifs")
    target_code = _emit_expr(ctx, target) if isinstance(target, dict) else "_"
    iter_code = _emit_expr(ctx, iter_node)
    result = "(function() local __r = {};"
    result += _emit_comp_loop_prefix(ctx, target, iter_node, target_code, iter_code)
    if len(ifs) > 0:
        result += " if " + _emit_expr(ctx, ifs[0]) + " then"
        result += " __r[" + key_code + "] = " + value_code + ";"
        result += " end"
    else:
        result += " __r[" + key_code + "] = " + value_code + ";"
    result += " end; return __r end)()"
    return result


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    body_node = node.get("body")
    arg_order = _list(node, "arg_order")
    arg_names: list[str] = []
    raw_names: list[str] = []
    if len(arg_order) > 0:
        for a in arg_order:
            if isinstance(a, str):
                raw_names.append(a)
                arg_names.append(_lua_symbol_name(ctx, a))
    else:
        args = _list(node, "args")
        for a in args:
            if isinstance(a, dict):
                raw_name = _str(a, "arg")
                raw_names.append(raw_name)
                arg_names.append(_lua_symbol_name(ctx, raw_name))
    defaults = _dict(node, "arg_defaults")
    if len(defaults) == 0:
        for a in _list(node, "args"):
            if not isinstance(a, dict):
                continue
            raw_name = _str(a, "arg")
            default_node = a.get("default")
            if raw_name != "" and isinstance(default_node, dict):
                defaults[raw_name] = default_node
    body_code = _emit_expr(ctx, body_node)
    prefix: list[str] = []
    for raw_name, safe_name in zip(raw_names, arg_names):
        default_node = defaults.get(raw_name)
        if isinstance(default_node, dict):
            prefix.append("if " + safe_name + " == nil then " + safe_name + " = " + _emit_expr(ctx, default_node) + " end")
    if len(prefix) == 0:
        return "function(" + ", ".join(arg_names) + ") return " + body_code + " end"
    return "function(" + ", ".join(arg_names) + ") " + "; ".join(prefix) + "; return " + body_code + " end"


def _emit_range_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    start = node.get("start")
    stop = node.get("stop")
    step = node.get("step")
    start_code = _emit_expr(ctx, start) if isinstance(start, dict) else "0"
    stop_code = _emit_expr(ctx, stop) if isinstance(stop, dict) else "0"
    if isinstance(step, dict):
        step_code = _emit_expr(ctx, step)
        return "__pytra_range(" + start_code + ", " + stop_code + ", " + step_code + ")"
    if stop_code == "0" and start_code != "0":
        return "__pytra_range(" + start_code + ")"
    return "__pytra_range(" + start_code + ", " + stop_code + ")"


def _emit_slice_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    lower = node.get("lower")
    upper = node.get("upper")
    lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "nil"
    upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else "nil"
    return lower_code + ", " + upper_code


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_stmt(ctx: EmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        return
    # Leading trivia
    leading = _list(node, "leading_trivia")
    for trivia in leading:
        if not isinstance(trivia, dict):
            continue
        tk = _str(trivia, "kind")
        text = _str(trivia, "text")
        if tk == "comment":
            # Pytra::cpp / Pytra::pass directives - skip for Lua
            if text.startswith("Pytra::cpp") or text.startswith("Pytra::pass"):
                continue
            _emit(ctx, "-- " + text)
        elif tk == "blank":
            _emit_blank(ctx)

    kind = _str(node, "kind")
    if kind == "Expr":
        value = node.get("value")
        if isinstance(value, dict):
            if _emit_direct_expr_stmt_call(ctx, value):
                return
            if _str(value, "kind") == "Name" and _str(value, "id") == "break":
                _emit(ctx, "break")
                return
            if _str(value, "kind") == "Name" and _str(value, "id") == "continue":
                ctx.needs_continue_label = True
                _emit(ctx, "goto __continue__")
                return
            if _str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
                return
            code = _emit_expr(ctx, value)
        if code != "" and code != "nil":
            _emit(ctx, code)
    elif kind == "Return":
        _emit_return(ctx, node)
    elif kind == "Assign" or kind == "AnnAssign":
        _emit_assign(ctx, node)
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
    elif kind == "Try":
        _emit_try(ctx, node)
    elif kind == "Raise":
        _emit_raise(ctx, node)
    elif kind == "Break":
        _emit(ctx, "break")
    elif kind == "Continue":
        ctx.needs_continue_label = True
        _emit(ctx, "goto __continue__")
    elif kind == "Pass":
        _emit(ctx, "-- pass")
    elif kind == "TypeAlias":
        pass  # No type aliases in Lua
    elif kind == "comment":
        text = _str(node, "text")
        if text != "":
            _emit(ctx, "-- " + text)
    elif kind == "blank":
        _emit_blank(ctx)
    elif kind == "ErrorReturn":
        _emit_error_return(ctx, node)
    elif kind == "ErrorCheck":
        _emit_error_check(ctx, node)
    elif kind == "ErrorCatch":
        _emit_error_catch(ctx, node)
    elif kind == "Match":
        _emit_match(ctx, node)
    elif kind == "Delete":
        _emit_delete(ctx, node)
    else:
        _emit(ctx, "-- unsupported stmt: " + kind)


def _emit_direct_expr_stmt_call(ctx: EmitContext, node: dict[str, JsonVal]) -> bool:
    if _str(node, "kind") != "Call":
        return False
    func_node = node.get("func")
    if not isinstance(func_node, dict):
        return False
    args = _list(node, "args")
    if len(args) != 1:
        return False
    runtime_call = _str(node, "runtime_call")
    resolved_rt_call = _str(node, "resolved_runtime_call")
    call_name = ""
    if runtime_call != "":
        call_name = ctx.mapping.calls.get(runtime_call, "")
    if call_name == "" and resolved_rt_call != "":
        call_name = ctx.mapping.calls.get(resolved_rt_call, "")
    if call_name != "__LIST_APPEND__":
        return False
    if _str(func_node, "kind") != "Attribute":
        return False
    owner_node = func_node.get("value")
    if not isinstance(owner_node, dict):
        return False
    owner = _emit_expr(ctx, owner_node)
    value_code = _emit_expr(ctx, args[0])
    _emit(ctx, owner + "[#" + owner + " + 1] = " + value_code)
    return True


def _emit_body(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        _emit_stmt(ctx, stmt)


def _emit_body_with_continue(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Emit body and add ::__continue__:: label if needed."""
    saved = ctx.needs_continue_label
    ctx.needs_continue_label = False
    start_index = len(ctx.lines)
    _emit_body(ctx, body)
    if ctx.needs_continue_label:
        body_lines = ctx.lines[start_index:]
        del ctx.lines[start_index:]
        _emit(ctx, "do")
        extra_indent = "    "
        for line in body_lines:
            if line == "":
                ctx.lines.append("")
            else:
                ctx.lines.append(extra_indent + line)
        _emit(ctx, "end")
        _emit(ctx, "::__continue__::")
    ctx.needs_continue_label = saved


def _emit_return(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if isinstance(value, dict):
        # Multi-return (tuple)
        if _str(value, "kind") == "Tuple":
            elements = _list(value, "elements")
            parts = [_emit_expr(ctx, e) for e in elements]
            _emit(ctx, "return " + ", ".join(parts))
            return
        value_code = _emit_expr(ctx, value)
        if _is_union_error_return_type(ctx, ctx.current_return_type):
            if _is_none_error_return_type(ctx, ctx.current_return_type):
                _emit(ctx, "return " + value_code)
            else:
                _emit(ctx, "return " + value_code + ", nil")
            return
        _emit(ctx, "return " + value_code)
    else:
        if _is_union_error_return_type(ctx, ctx.current_return_type):
            _emit(ctx, "return nil")
            return
        if _is_exception_type_name(ctx, ctx.current_return_type):
            _emit(ctx, "return nil")
            return
        _emit(ctx, "return")


def _emit_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    # Check for extern_var_v1 (skip, handled by native runtime)
    meta = _dict(node, "meta")
    extern_v1 = meta.get("extern_var_v1") if isinstance(meta, dict) else None
    if isinstance(extern_v1, dict):
        return

    target = node.get("target")
    value = node.get("value")
    declare = _bool(node, "declare")
    unused = _bool(node, "unused")

    target_name = _str(target, "id") if isinstance(target, dict) else ""
    if unused and target_name == "_":
        # Still evaluate the value for side effects
        if isinstance(value, dict):
            val_code = _emit_expr(ctx, value)
            if val_code != "nil":
                _emit(ctx, "local _ = " + val_code)
        return

    # Tuple destructuring
    if isinstance(target, dict) and _str(target, "kind") == "Tuple":
        _emit_tuple_assign(ctx, target, value, declare)
        return

    if isinstance(target, dict):
        target_code = _emit_assign_target(ctx, target)
        checked_call = _emit_checked_subscript_call(ctx, value) if isinstance(value, dict) else ""
        if checked_call != "":
            err_tmp = _next_temp(ctx, "err")
            ok_tmp = _next_temp(ctx, "ok")
            _emit(ctx, "local " + ok_tmp + ", " + err_tmp + " = " + checked_call)
            _emit(ctx, "if " + err_tmp + " ~= nil then")
            ctx.indent_level += 1
            _emit_error_propagation(ctx, err_tmp, allow_current_catch=True)
            ctx.indent_level -= 1
            _emit(ctx, "end")
            val_code = ok_tmp
        else:
            val_code = _emit_expr(ctx, value)
        target_rt = _str(target, "resolved_type")
        value_rt = _str(value, "resolved_type") if isinstance(value, dict) else ""
        if isinstance(value, dict) and _str(value, "kind") == "Call":
            if target_rt.startswith("tuple[") or value_rt.startswith("tuple["):
                val_code = "{" + val_code + "}"
        if declare and _str(target, "kind") == "Name":
            name = _str(target, "id")
            safe = _lua_symbol_name(ctx, name)
            if safe not in ctx.declared_locals:
                decl_type = _str(node, "decl_type")
                if decl_type == "":
                    decl_type = _str(node, "resolved_type")
                if isinstance(value, dict) and _emit_checked_runtime_call(ctx, value, safe, declare_local=True, decl_type=decl_type):
                    return
                ctx.declared_locals.add(safe)
                _emit(ctx, "local " + safe + " = " + val_code)
                # Track type
                if decl_type != "":
                    ctx.var_types[safe] = decl_type
                return
        if isinstance(value, dict) and _emit_checked_runtime_call(ctx, value, target_code, declare_local=False):
            return
        _emit(ctx, target_code + " = " + val_code)
        return


def _emit_assign_target(ctx: EmitContext, target: dict[str, JsonVal]) -> str:
    kind = _str(target, "kind")
    if kind == "Name":
        return _lua_symbol_name(ctx, _str(target, "id"))
    if kind == "Attribute":
        return _emit_attribute(ctx, target)
    if kind == "Subscript":
        return _emit_subscript(ctx, target)
    return _emit_expr(ctx, target)


def _emit_tuple_assign(ctx: EmitContext, target: dict[str, JsonVal], value: JsonVal, declare: bool) -> None:
    elements = _list(target, "elements")
    targets: list[tuple[str, bool, str]] = []
    for e in elements:
        if isinstance(e, dict):
            if _bool(e, "unused"):
                targets.append(("_", False, ""))
            else:
                kind = _str(e, "kind")
                if kind == "Name":
                    safe = _lua_symbol_name(ctx, _str(e, "id"))
                    targets.append((safe, True, safe))
                else:
                    targets.append((_emit_assign_target(ctx, e), False, ""))
        else:
            targets.append(("_", False, ""))

    def _emit_tuple_target_assign(target_code: str, is_name_target: bool, safe_name: str, rhs_code: str) -> None:
        if target_code == "_":
            return
        if declare and is_name_target:
            if safe_name not in ctx.declared_locals:
                ctx.declared_locals.add(safe_name)
                _emit(ctx, "local " + safe_name + " = " + rhs_code)
                return
        _emit(ctx, target_code + " = " + rhs_code)

    # Check if RHS is a tuple literal
    if isinstance(value, dict) and _str(value, "kind") == "Tuple":
        rhs_elems = _list(value, "elements")
        rhs_temps: list[str] = []
        for elem in rhs_elems:
            tmp = _next_temp(ctx, "tupv")
            if isinstance(elem, dict):
                checked_call = _emit_checked_subscript_call(ctx, elem)
                if checked_call != "":
                    err_tmp = _next_temp(ctx, "err")
                    ok_tmp = _next_temp(ctx, "ok")
                    _emit(ctx, "local " + ok_tmp + ", " + err_tmp + " = " + checked_call)
                    _emit(ctx, "if " + err_tmp + " ~= nil then")
                    ctx.indent_level += 1
                    _emit_error_propagation(ctx, err_tmp, allow_current_catch=True)
                    ctx.indent_level -= 1
                    _emit(ctx, "end")
                    _emit(ctx, "local " + tmp + " = " + ok_tmp)
                else:
                    _emit(ctx, "local " + tmp + " = " + _emit_expr(ctx, elem))
            else:
                _emit(ctx, "local " + tmp + " = nil")
            rhs_temps.append(tmp)
        for i, (target_code, is_name_target, safe_name) in enumerate(targets):
            if i >= len(rhs_temps):
                break
            _emit_tuple_target_assign(target_code, is_name_target, safe_name, rhs_temps[i])
        return

    val_code = _emit_expr(ctx, value)
    # Unpack table
    temp = _next_temp(ctx, "tup")
    if isinstance(value, dict) and _str(value, "kind") == "Call":
        _emit(ctx, "local " + temp + " = {" + val_code + "}")
    else:
        _emit(ctx, "local " + temp + " = " + val_code)
    for i, (target_code, is_name_target, safe_name) in enumerate(targets):
        _emit_tuple_target_assign(target_code, is_name_target, safe_name, temp + "[" + str(i + 1) + "]")


def _emit_aug_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    op = _str(node, "op")
    target_code = _emit_assign_target(ctx, target) if isinstance(target, dict) else "nil"
    val_code = _emit_expr(ctx, value)
    target_rt = _str(target, "resolved_type") if isinstance(target, dict) else ""

    # String concatenation
    if op == "Add" and target_rt == "str":
        _emit(ctx, target_code + " = " + target_code + " .. " + val_code)
        return
    if op == "FloorDiv":
        _emit(ctx, target_code + " = __pytra_floordiv(" + target_code + ", " + val_code + ")")
        return

    op_map: dict[str, str] = {
        "Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
        "Mod": "%", "Pow": "^",
        "BitAnd": "&", "BitOr": "|", "BitXor": "~",
        "LShift": "<<", "RShift": ">>",
    }
    lua_op = op_map.get(op, "+")
    _emit(ctx, target_code + " = " + target_code + " " + lua_op + " " + val_code)


def _emit_if(ctx: EmitContext, node: dict[str, JsonVal], *, is_elif: bool = False) -> None:
    test = _emit_condition(ctx, node.get("test"))
    keyword = "elseif" if is_elif else "if"
    _emit(ctx, keyword + " " + test + " then")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    orelse = _list(node, "orelse")
    if len(orelse) > 0:
        if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
            _emit_if(ctx, orelse[0], is_elif=True)
            return
        _emit(ctx, "else")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_while(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    test = _emit_condition(ctx, node.get("test"))
    _emit(ctx, "while " + test + " do")
    ctx.indent_level += 1
    _emit_body_with_continue(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_for_core(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """Emit ForCore (lowered for loop)."""
    target = node.get("target")
    iter_node = node.get("iter")
    body = _list(node, "body")
    iter_mode = _str(node, "iter_mode")
    target_plan = _dict(node, "target_plan")
    iter_plan = _dict(node, "iter_plan")

    if _str(iter_plan, "kind") == "StaticRangeForPlan":
        _emit_static_range_for(ctx, node)
        return

    if not isinstance(target, dict) and len(target_plan) > 0:
        if _str(target_plan, "kind") == "NameTarget":
            target_code = _lua_symbol_name(ctx, _str(target_plan, "id"))
        else:
            target_code = "_"
    else:
        target_code = _emit_expr(ctx, target) if isinstance(target, dict) else "_"

    if not isinstance(iter_node, dict) and len(iter_plan) > 0:
        maybe_iter = iter_plan.get("iter_expr")
        if isinstance(maybe_iter, dict):
            iter_node = maybe_iter

    iter_code = _emit_expr(ctx, iter_node)

    iter_rt = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""

    if isinstance(iter_node, dict) and _str(iter_node, "kind") == "RangeExpr":
        range_node = iter_node
        start_node = range_node.get("start")
        stop_node = range_node.get("stop")
        step_node = range_node.get("step")
        start_code = _emit_expr(ctx, start_node) if isinstance(start_node, dict) else "0"
        stop_code = _emit_expr(ctx, stop_node) if isinstance(stop_node, dict) else "0"
        step_code = _emit_expr(ctx, step_node) if isinstance(step_node, dict) else "1"
        if _is_lua_one(step_code):
            _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " - 1 do")
        elif _is_lua_minus_one(step_code):
            _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " + 1, -1 do")
        else:
            _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " - 1, " + step_code + " do")
        ctx.indent_level += 1
        _emit_body_with_continue(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")
        return

    if iter_mode == "range" or _str(node, "kind_detail") == "ForRange":
        _emit_for_range_inner(ctx, node, body)
        return

    is_dict = iter_rt.startswith("dict[") or iter_rt == "dict"
    is_str = iter_rt in ("str", "string")
    is_set = iter_rt.startswith("set[") or iter_rt == "set"

    if is_dict:
        _emit(ctx, "for " + target_code + ", _ in pairs(" + iter_code + ") do")
    elif is_set:
        _emit(ctx, "for " + target_code + ", _ in pairs(" + iter_code + ") do")
    elif is_str:
        idx_var = _next_temp(ctx, "i")
        _emit(ctx, "for " + idx_var + " = 1, #" + iter_code + " do")
        ctx.indent_level += 1
        _emit(ctx, "local " + target_code + " = string.sub(" + iter_code + ", " + idx_var + ", " + idx_var + ")")
        ctx.indent_level -= 1
        # Continue with body
        ctx.indent_level += 1
        _emit_body_with_continue(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")
        return
    else:
        _emit(ctx, "for _, " + target_code + " in ipairs(" + iter_code + ") do")

    ctx.indent_level += 1
    _emit_body_with_continue(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_for_range_inner(ctx: EmitContext, node: dict[str, JsonVal], body: list[JsonVal]) -> None:
    """Emit a for range loop."""
    target = node.get("target")
    target_code = _emit_expr(ctx, target) if isinstance(target, dict) else "_i"
    start_node = node.get("start")
    stop_node = node.get("stop")
    step_node = node.get("step")
    start_code = _emit_expr(ctx, start_node) if isinstance(start_node, dict) else "0"
    stop_code = _emit_expr(ctx, stop_node) if isinstance(stop_node, dict) else "0"
    step_code = _emit_expr(ctx, step_node) if isinstance(step_node, dict) else "1"

    if _is_lua_one(step_code):
        _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " - 1 do")
    elif _is_lua_minus_one(step_code):
        _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " + 1, -1 do")
    else:
        _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " - 1, " + step_code + " do")

    ctx.indent_level += 1
    _emit_body_with_continue(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_runtime_iter_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """Emit RuntimeIterForPlan (enumerate, zip, etc.)."""
    target = node.get("target")
    iterable = node.get("iterable")
    body = _list(node, "body")
    semantic = _str(node, "semantic")
    plan = _dict(node, "iter_plan")
    plan_kind = _str(plan, "kind") if plan else ""

    target_code = _emit_expr(ctx, target) if isinstance(target, dict) else "_"
    iter_code = _emit_expr(ctx, iterable)

    if plan_kind == "enumerate" or semantic == "enumerate":
        idx_name = "_"
        val_name = "_"
        if isinstance(target, dict) and _str(target, "kind") == "Tuple":
            elems = _list(target, "elements")
            if len(elems) >= 2:
                idx_name = _emit_expr(ctx, elems[0]) if isinstance(elems[0], dict) else "_"
                val_name = _emit_expr(ctx, elems[1]) if isinstance(elems[1], dict) else "_"
        inner_iter = _emit_expr(ctx, plan.get("iter")) if plan and isinstance(plan.get("iter"), dict) else iter_code
        _emit(ctx, "for __ei, " + val_name + " in ipairs(" + inner_iter + ") do")
        ctx.indent_level += 1
        _emit(ctx, "local " + idx_name + " = __ei - 1")
        _emit_body_with_continue(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")
        return

    if plan_kind == "reversed":
        inner_iter = _emit_expr(ctx, plan.get("iter")) if plan and isinstance(plan.get("iter"), dict) else iter_code
        _emit(ctx, "for _, " + target_code + " in ipairs(__pytra_reversed(" + inner_iter + ")) do")
        ctx.indent_level += 1
        _emit_body_with_continue(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")
        return

    if plan_kind == "dict_items":
        k_name = "_k"
        v_name = "_v"
        if isinstance(target, dict) and _str(target, "kind") == "Tuple":
            elems = _list(target, "elements")
            if len(elems) >= 2:
                k_name = _emit_expr(ctx, elems[0]) if isinstance(elems[0], dict) else "_k"
                v_name = _emit_expr(ctx, elems[1]) if isinstance(elems[1], dict) else "_v"
        inner_iter = _emit_expr(ctx, plan.get("iter")) if plan and isinstance(plan.get("iter"), dict) else iter_code
        _emit(ctx, "for " + k_name + ", " + v_name + " in pairs(" + inner_iter + ") do")
        ctx.indent_level += 1
        _emit_body_with_continue(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "end")
        return

    # Fallback: generic iteration
    iter_rt = _str(iterable, "resolved_type") if isinstance(iterable, dict) else ""
    is_dict = iter_rt.startswith("dict[") or iter_rt == "dict"
    if is_dict:
        _emit(ctx, "for " + target_code + ", _ in pairs(" + iter_code + ") do")
    else:
        _emit(ctx, "for _, " + target_code + " in ipairs(" + iter_code + ") do")
    ctx.indent_level += 1
    _emit_body_with_continue(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_static_range_for(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """Emit StaticRangeForPlan (range-based for)."""
    target = node.get("target")
    body = _list(node, "body")
    plan = _dict(node, "iter_plan")
    target_plan = _dict(node, "target_plan")
    if isinstance(target, dict):
        target_code = _emit_expr(ctx, target)
    elif _str(target_plan, "kind") == "NameTarget":
        target_code = _lua_symbol_name(ctx, _str(target_plan, "id"))
    else:
        target_code = "_i"

    start_node = plan.get("start") if plan else None
    stop_node = plan.get("stop") if plan else None
    step_node = plan.get("step") if plan else None
    start_code = _emit_expr(ctx, start_node) if isinstance(start_node, dict) else "0"
    stop_code = _emit_expr(ctx, stop_node) if isinstance(stop_node, dict) else "0"
    step_code = _emit_expr(ctx, step_node) if isinstance(step_node, dict) else "1"

    if _is_lua_one(step_code):
        _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " - 1 do")
    elif _is_lua_minus_one(step_code):
        _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " + 1, -1 do")
    else:
        _emit(ctx, "for " + target_code + " = " + start_code + ", " + stop_code + " - 1, " + step_code + " do")

    ctx.indent_level += 1
    _emit_body_with_continue(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end")


def _emit_function_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    safe_name = _lua_symbol_name(ctx, name)
    body = _list(node, "body")
    decorators = _list(node, "decorators")

    # @extern: generate delegate
    if "extern" in decorators:
        _emit(ctx, "-- @extern: " + safe_name)
        return

    # Check for @property
    is_property = "property" in decorators
    is_static = "staticmethod" in decorators

    # Variadic
    is_vararg = False
    vararg_name = ""
    vararg_raw = node.get("vararg")
    if isinstance(vararg_raw, dict) or (isinstance(vararg_raw, str) and vararg_raw != ""):
        is_vararg = True
        if isinstance(vararg_raw, dict):
            vararg_name = _str(vararg_raw, "arg")
        elif isinstance(vararg_raw, str):
            vararg_name = vararg_raw
    if vararg_name == "":
        direct_vararg = _str(node, "vararg_name")
        if direct_vararg != "":
            is_vararg = True
            vararg_name = direct_vararg

    # Collect argument names from arg_order (EAST3 format)
    arg_order = _list(node, "arg_order")
    arg_names: list[str] = []
    if len(arg_order) > 0:
        for a in arg_order:
            if isinstance(a, str):
                if a == "self":
                    continue
                if is_vararg and a == vararg_name:
                    continue
                arg_names.append(_lua_symbol_name(ctx, a))
    arg_types = _dict(node, "arg_types")
    if len(arg_types) > 0:
        for a in arg_types.keys():
            if a == "self":
                continue
            safe_a = _lua_symbol_name(ctx, a)
            if is_vararg and a == vararg_name:
                continue
            if safe_a not in arg_names:
                arg_names.append(safe_a)
    if len(arg_names) == 0:
        # Fallback: try "args" list
        args = _list(node, "args")
        for a in args:
            if isinstance(a, dict):
                arg_name = _str(a, "arg")
                if arg_name == "self":
                    continue
                arg_names.append(_lua_symbol_name(ctx, arg_name))

    if is_vararg:
        arg_names.append("...")

    # In class context
    if ctx.in_class_body:
        cls = ctx.current_class
        if is_static:
            _emit(ctx, "function " + cls + "." + safe_name + "(" + ", ".join(arg_names) + ")")
        elif name == "__init__":
            _emit_init_method(ctx, cls, arg_names, body)
            return
        else:
            _emit(ctx, "function " + cls + ":" + safe_name + "(" + ", ".join(arg_names) + ")")
    elif _str(node, "kind") == "ClosureDef":
        _emit(ctx, "local function " + safe_name + "(" + ", ".join(arg_names) + ")")
    else:
        _emit(ctx, "function " + safe_name + "(" + ", ".join(arg_names) + ")")

    ctx.indent_level += 1
    saved_return_type = ctx.current_return_type
    ctx.current_return_type = _str(node, "return_type")
    saved_locals = ctx.declared_locals
    ctx.declared_locals = set()
    if is_vararg and vararg_name != "":
        safe_vararg = _lua_symbol_name(ctx, vararg_name)
        ctx.declared_locals.add(safe_vararg)
        _emit(ctx, "local " + safe_vararg + " = {...}")
    _emit_body(ctx, body)
    ctx.declared_locals = saved_locals
    ctx.current_return_type = saved_return_type
    ctx.indent_level -= 1
    _emit(ctx, "end")
    _emit_blank(ctx)


def _emit_init_method(ctx: EmitContext, cls: str, arg_names: list[str], body: list[JsonVal]) -> None:
    """Emit __init__ as Class.new(cls, ...) constructor pattern."""
    _emit(ctx, "function " + cls + ".new(" + ", ".join(arg_names) + ")")
    ctx.indent_level += 1
    base_name = ctx.class_bases.get(cls, "")
    super_init_args: list[str] = []
    filtered_body: list[JsonVal] = []
    for stmt in body:
        if not isinstance(stmt, dict) or _str(stmt, "kind") != "Expr":
            filtered_body.append(stmt)
            continue
        value = stmt.get("value")
        if not isinstance(value, dict) or _str(value, "kind") != "Call":
            filtered_body.append(stmt)
            continue
        func = value.get("func")
        if not isinstance(func, dict) or _str(func, "kind") != "Attribute":
            filtered_body.append(stmt)
            continue
        owner = func.get("value")
        if _str(func, "attr") == "__init__" and isinstance(owner, dict) and _str(owner, "kind") == "Call":
            owner_func = owner.get("func")
            if isinstance(owner_func, dict) and _str(owner_func, "id") == "super":
                super_init_args = [_emit_expr(ctx, arg) for arg in _list(value, "args")]
                continue
        filtered_body.append(stmt)
    if base_name != "" and base_name not in LUA_NON_INHERITABLE_BASES:
        base_ctor_args = ", ".join(super_init_args)
        if base_ctor_args != "":
            _emit(ctx, "local self = " + _safe_lua_ident(base_name) + ".new(" + base_ctor_args + ")")
        else:
            _emit(ctx, "local self = " + _safe_lua_ident(base_name) + ".new()")
        _emit(ctx, "setmetatable(self, " + cls + ")")
    else:
        _emit(ctx, "local self = setmetatable({}, " + cls + ")")
    saved_locals = ctx.declared_locals
    ctx.declared_locals = set()
    _emit_body(ctx, filtered_body)
    ctx.declared_locals = saved_locals
    _emit(ctx, "return self")
    ctx.indent_level -= 1
    _emit(ctx, "end")
    _emit_blank(ctx)


def _emit_class_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    safe = _safe_lua_ident(name)
    bases = _list(node, "bases")
    body = _list(node, "body")

    base_name = ctx.class_bases.get(name, "")
    if len(bases) > 0 and isinstance(bases[0], dict):
        base_name = _str(bases[0], "id")
    elif _str(node, "base") != "":
        base_name = _str(node, "base")

    _emit(ctx, safe + " = {}")
    _emit(ctx, safe + ".__index = " + safe)
    _emit(ctx, safe + ".__name = " + _quote_string(name))
    if base_name != "" and base_name not in LUA_NON_INHERITABLE_BASES:
        base_safe = _safe_lua_ident(base_name)
        _emit(ctx, "setmetatable(" + safe + ", {__index = " + base_safe + "})")
    _emit_blank(ctx)

    saved_class = ctx.current_class
    saved_in_class = ctx.in_class_body
    ctx.current_class = safe
    ctx.in_class_body = True

    has_init = False
    is_dataclass = _bool(node, "dataclass") or ("dataclass" in _list(node, "decorators"))
    # Emit class body (methods and class-level assignments)
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind == "FunctionDef" or kind == "ClosureDef":
            if _str(stmt, "name") == "__init__":
                has_init = True
            _emit_function_def(ctx, stmt)
        elif kind in ("Assign", "AnnAssign"):
            # Class-level field declarations or constants
            target = stmt.get("target")
            value = stmt.get("value")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                safe_field = _safe_lua_ident(field_name)
                if isinstance(value, dict):
                    val_code = _emit_expr(ctx, value)
                    _emit(ctx, safe + "." + safe_field + " = " + val_code)
                else:
                    _emit(ctx, safe + "." + safe_field + " = nil")
        elif kind == "Pass":
            pass
        elif kind in ("comment", "blank"):
            _emit_stmt(ctx, stmt)

    if not has_init:
        if is_dataclass:
            field_names: list[str] = []
            field_defaults: dict[str, str] = {}
            for member in body:
                if not isinstance(member, dict) or _str(member, "kind") != "AnnAssign":
                    continue
                target = member.get("target")
                if not isinstance(target, dict) or _str(target, "kind") != "Name":
                    continue
                field_name = _str(target, "id")
                if field_name == "":
                    continue
                field_names.append(field_name)
                if isinstance(member.get("value"), dict):
                    field_defaults[field_name] = _emit_expr(ctx, member.get("value"))
            params = [_safe_lua_ident(name) for name in field_names]
            _emit(ctx, "function " + safe + ".new(" + ", ".join(params) + ")")
            ctx.indent_level += 1
            _emit(ctx, "local self = setmetatable({}, " + safe + ")")
            for field_name in field_names:
                safe_field = _safe_lua_ident(field_name)
                if field_name in field_defaults:
                    _emit(ctx, "if " + safe_field + " == nil then " + safe_field + " = " + field_defaults[field_name] + " end")
                _emit(ctx, "self." + safe_field + " = " + safe_field)
            _emit(ctx, "return self")
            ctx.indent_level -= 1
            _emit(ctx, "end")
            _emit_blank(ctx)
        else:
            _emit(ctx, "function " + safe + ".new()")
            ctx.indent_level += 1
            _emit(ctx, "return setmetatable({}, " + safe + ")")
            ctx.indent_level -= 1
            _emit(ctx, "end")
            _emit_blank(ctx)

    ctx.current_class = saved_class
    ctx.in_class_body = saved_in_class
    _emit_blank(ctx)


def _emit_import_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    kind = _str(node, "kind")
    if kind == "Import":
        names = _list(node, "names")
        for item in names:
            if not isinstance(item, dict):
                continue
            mod_name = _str(item, "name")
            asname = _str(item, "asname")
            local_name = asname if asname != "" else mod_name
            module_ctor = ctx.mapping.calls.get("module_ctor." + mod_name, "")
            if module_ctor != "":
                safe_local = _lua_symbol_name(ctx, local_name)
                if safe_local not in ctx.declared_locals:
                    ctx.declared_locals.add(safe_local)
                    _emit(ctx, "local " + safe_local + " = " + module_ctor + "()")
                else:
                    _emit(ctx, safe_local + " = " + module_ctor + "()")
            elif mod_name != "" and not should_skip_module(mod_name, ctx.mapping):
                module_file = _lua_module_filename(mod_name)
                if module_file not in ctx.loaded_module_files:
                    ctx.loaded_module_files.add(module_file)
                    _emit(ctx, 'dofile(__script_dir .. "' + module_file + '")')
                if local_name != "":
                    _emit_module_alias_table(ctx, local_name)
        return
    if kind == "ImportFrom":
        module = _str(node, "module")
        if should_skip_module(module, ctx.mapping):
            return
        names = _list(node, "names")
        loaded_any = False
        for item in names:
            if not isinstance(item, dict):
                continue
            local_name = _str(item, "asname")
            if local_name == "":
                local_name = _str(item, "name")
            module_id = ctx.import_alias_modules.get(local_name, module)
            if module_id == "" or should_skip_module(module_id, ctx.mapping):
                continue
            module_file = _lua_module_filename(module_id)
            if module_file in ctx.loaded_module_files:
                loaded_any = True
                if module_id != module and local_name != "":
                    _emit_module_alias_table(ctx, local_name)
                continue
            ctx.loaded_module_files.add(module_file)
            _emit(ctx, 'dofile(__script_dir .. "' + module_file + '")')
            if module_id != module and local_name != "":
                _emit_module_alias_table(ctx, local_name)
            loaded_any = True
        if not loaded_any:
            module_file = _lua_module_filename(module)
            if module_file not in ctx.loaded_module_files:
                ctx.loaded_module_files.add(module_file)
                _emit(ctx, 'dofile(__script_dir .. "' + module_file + '")')
    # Module imports are typically handled by runtime in Lua


def _emit_var_decl(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    if name == "":
        return
    safe = _lua_symbol_name(ctx, name)
    unused = _bool(node, "unused")
    if unused:
        return
    decl_type = _str(node, "type")
    if decl_type == "":
        decl_type = _str(node, "resolved_type")
    value = node.get("value")
    if isinstance(value, dict) and _emit_checked_runtime_call(ctx, value, safe, declare_local=True, decl_type=decl_type):
        return
    zero = lua_zero_value(decl_type)
    ctx.declared_locals.add(safe)
    ctx.var_types[safe] = decl_type
    if safe in ctx.hoisted_locals:
        _emit(ctx, safe + " = " + zero)
    else:
        _emit(ctx, "local " + safe + " = " + zero)


def _collect_try_hoist_locals(body: list[JsonVal]) -> list[tuple[str, str]]:
    hoisted: list[tuple[str, str]] = []

    def walk(stmts: list[JsonVal]) -> None:
        for stmt in stmts:
            if not isinstance(stmt, dict):
                continue
            kind = _str(stmt, "kind")
            if kind == "VarDecl":
                name = _str(stmt, "name")
                if name != "":
                    decl_type = _str(stmt, "type")
                    if decl_type == "":
                        decl_type = _str(stmt, "resolved_type")
                    hoisted.append((name, decl_type))
            elif kind == "Assign":
                target = stmt.get("target")
                if isinstance(target, dict) and _str(target, "kind") == "Name" and _bool(stmt, "declare"):
                    name = _str(target, "id")
                    if name != "":
                        decl_type = _str(stmt, "decl_type")
                        if decl_type == "":
                            decl_type = _str(stmt, "resolved_type")
                        hoisted.append((name, decl_type))
            for key in ("body", "orelse", "finalbody"):
                inner = _list(stmt, key)
                if len(inner) > 0:
                    walk(inner)

    walk(body)
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for name, decl_type in hoisted:
        if name in seen:
            continue
        seen.add(name)
        unique.append((name, decl_type))
    return unique


def _emit_swap(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    left = node.get("left")
    right = node.get("right")
    if isinstance(left, dict) and isinstance(right, dict):
        left_tmp = _next_temp(ctx, "swap")
        right_tmp = _next_temp(ctx, "swap")

        left_checked = _emit_checked_subscript_call(ctx, left)
        if left_checked != "":
            err_tmp = _next_temp(ctx, "err")
            ok_tmp = _next_temp(ctx, "ok")
            _emit(ctx, "local " + ok_tmp + ", " + err_tmp + " = " + left_checked)
            _emit(ctx, "if " + err_tmp + " ~= nil then")
            ctx.indent_level += 1
            _emit_error_propagation(ctx, err_tmp, allow_current_catch=True)
            ctx.indent_level -= 1
            _emit(ctx, "end")
            _emit(ctx, "local " + left_tmp + " = " + ok_tmp)
        else:
            _emit(ctx, "local " + left_tmp + " = " + _emit_expr(ctx, left))

        right_checked = _emit_checked_subscript_call(ctx, right)
        if right_checked != "":
            err_tmp = _next_temp(ctx, "err")
            ok_tmp = _next_temp(ctx, "ok")
            _emit(ctx, "local " + ok_tmp + ", " + err_tmp + " = " + right_checked)
            _emit(ctx, "if " + err_tmp + " ~= nil then")
            ctx.indent_level += 1
            _emit_error_propagation(ctx, err_tmp, allow_current_catch=True)
            ctx.indent_level -= 1
            _emit(ctx, "end")
            _emit(ctx, "local " + right_tmp + " = " + ok_tmp)
        else:
            _emit(ctx, "local " + right_tmp + " = " + _emit_expr(ctx, right))

        _emit(ctx, _emit_assign_target(ctx, left) + " = " + right_tmp)
        _emit(ctx, _emit_assign_target(ctx, right) + " = " + left_tmp)


def _emit_multi_assign(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    value = node.get("value")
    val_code = _emit_expr(ctx, value)
    names: list[str] = []
    for t in targets:
        if isinstance(t, dict):
            names.append(_emit_assign_target(ctx, t))
        else:
            names.append("_")
    temp = _next_temp(ctx, "ma")
    if isinstance(value, dict) and _str(value, "kind") == "Call":
        _emit(ctx, "local " + temp + " = {" + val_code + "}")
    else:
        _emit(ctx, "local " + temp + " = " + val_code)
    for i, n in enumerate(names):
        _emit(ctx, n + " = " + temp + "[" + str(i + 1) + "]")


def _emit_with(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    context_expr = node.get("context_expr")
    var_name = _str(node, "var_name")
    body = _list(node, "body")
    ctx_code = _emit_expr(ctx, context_expr)
    ctx_name = _next_temp(ctx, "ctx")
    safe_var = _lua_symbol_name(ctx, var_name) if var_name != "" else _next_temp(ctx, "with_value")
    _emit(ctx, "local " + ctx_name + " = " + ctx_code)
    _emit(ctx, "local " + safe_var + " = " + ctx_name + ":__enter__()")
    _emit(ctx, "local __with_ok__, __with_err__ = pcall(function()")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end)")
    _emit(ctx, ctx_name + ":__exit__(nil, nil, nil)")
    _emit(ctx, "if not __with_ok__ then error(__with_err__) end")


def _emit_try(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")

    if len(handlers) == 0 and len(finalbody) == 0:
        _emit_body(ctx, body)
        return

    if len(handlers) > 0:
        catch_node = {
            "kind": "ErrorCatch",
            "body": body,
            "handlers": handlers,
            "finalbody": finalbody,
        }
        _emit_error_catch(ctx, catch_node)
        return

    if len(finalbody) > 0 and len(ctx.catch_stack) > 0:
        finally_err = _next_temp(ctx, "finally_err")
        finally_label = _next_temp(ctx, "finally")
        _emit(ctx, "local " + finally_err + " = nil")
        ctx.catch_stack.append((finally_err, finally_label))
        _emit_body(ctx, body)
        ctx.catch_stack.pop()
        _emit(ctx, "::" + finally_label + "::")
        _emit_body(ctx, finalbody)
        _emit(ctx, "if " + finally_err + " ~= nil then")
        ctx.indent_level += 1
        _emit_error_propagation(ctx, finally_err, allow_current_catch=True)
        ctx.indent_level -= 1
        _emit(ctx, "end")
        return

    if len(finalbody) > 0 and len(ctx.catch_stack) == 0:
        _emit_body(ctx, body)
        _emit_body(ctx, finalbody)
        return

    hoisted_locals = _collect_try_hoist_locals(body) if len(finalbody) > 0 else []
    saved_hoisted = set(ctx.hoisted_locals)
    for name, decl_type in hoisted_locals:
        safe = _lua_symbol_name(ctx, name)
        if safe not in ctx.declared_locals:
            ctx.declared_locals.add(safe)
            ctx.var_types[safe] = decl_type
            _emit(ctx, "local " + safe + " = " + lua_zero_value(decl_type))
        ctx.hoisted_locals.add(safe)

    _emit(ctx, "local __try_ok__, __try_err__ = pcall(function()")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end)")

    if len(handlers) > 0:
        _emit(ctx, "if not __try_ok__ then")
        ctx.indent_level += 1
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            exc_name = _str(handler, "name")
            if exc_name != "":
                safe_exc = _lua_symbol_name(ctx, exc_name)
                _emit(ctx, "local " + safe_exc + " = __try_err__")
            saved_exc = ctx.current_exc_var
            ctx.current_exc_var = exc_name if exc_name != "" else "__try_err__"
            _emit_body(ctx, _list(handler, "body"))
            ctx.current_exc_var = saved_exc
        ctx.indent_level -= 1
        _emit(ctx, "end")

    if len(finalbody) > 0:
        _emit_body(ctx, finalbody)
    ctx.hoisted_locals = saved_hoisted


def _emit_raise(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    exc = node.get("exc")
    if isinstance(exc, dict):
        val = _emit_expr(ctx, exc)
        _emit(ctx, "error(" + val + ")")
    else:
        # Bare raise: re-raise current exception
        if ctx.current_exc_var != "":
            _emit_error_propagation(ctx, _lua_symbol_name(ctx, ctx.current_exc_var), allow_current_catch=False)
        else:
            _emit(ctx, 'error("re-raise")')


def _emit_match(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    """Emit match/case as if/elseif chain."""
    subject = node.get("subject")
    cases = _list(node, "cases")
    subject_code = _emit_expr(ctx, subject)
    temp = _next_temp(ctx, "match")
    _emit(ctx, "local " + temp + " = " + subject_code)
    first = True
    for case in cases:
        if not isinstance(case, dict):
            continue
        pattern = case.get("pattern")
        body = _list(case, "body")
        if isinstance(pattern, dict):
            pk = _str(pattern, "kind")
            if pk == "PatternWildcard":
                if first:
                    _emit(ctx, "do")
                else:
                    _emit(ctx, "else")
                ctx.indent_level += 1
                _emit_body(ctx, body)
                ctx.indent_level -= 1
                if first:
                    _emit(ctx, "end")
                continue
            cond = _match_pattern_cond(ctx, temp, pattern)
            keyword = "if" if first else "elseif"
            _emit(ctx, keyword + " " + cond + " then")
            ctx.indent_level += 1
            _emit_match_bindings(ctx, temp, pattern)
            _emit_body(ctx, body)
            ctx.indent_level -= 1
        first = False
    _emit(ctx, "end")


def _match_pattern_cond(ctx: EmitContext, subject: str, pattern: dict[str, JsonVal]) -> str:
    pk = _str(pattern, "kind")
    if pk == "VariantPattern":
        variant_name = _str(pattern, "variant_name")
        return LUA_PYTRA_ISINSTANCE_NAME + "(" + subject + ", " + _safe_lua_ident(variant_name) + ")"
    return "true"


def _emit_match_bindings(ctx: EmitContext, subject: str, pattern: dict[str, JsonVal]) -> None:
    pk = _str(pattern, "kind")
    if pk == "VariantPattern":
        subpatterns = _list(pattern, "subpatterns")
        for i, sp in enumerate(subpatterns):
            if isinstance(sp, dict) and _str(sp, "kind") == "PatternBind":
                name = _str(sp, "name")
                if name != "" and name != "_":
                    _emit(ctx, "local " + _safe_lua_ident(name) + " = " + subject + ".__fields[" + str(i + 1) + "]")


def _emit_delete(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    for t in targets:
        if isinstance(t, dict):
            _emit(ctx, _emit_expr(ctx, t) + " = nil")


# ---------------------------------------------------------------------------
# Class info collection
# ---------------------------------------------------------------------------

def _collect_module_class_info(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _str(stmt, "kind") != "ClassDef":
            continue
        name = _str(stmt, "name")
        ctx.class_names.add(name)
        bases = _list(stmt, "bases")
        if len(bases) > 0 and isinstance(bases[0], dict):
            ctx.class_bases[name] = _str(bases[0], "id")
        elif _str(stmt, "base") != "":
            ctx.class_bases[name] = _str(stmt, "base")
        # Collect methods
        cls_body = _list(stmt, "body")
        methods: dict[str, dict[str, JsonVal]] = {}
        static_methods: set[str] = set()
        property_methods: set[str] = set()
        fields: dict[str, str] = {}
        for member in cls_body:
            if not isinstance(member, dict):
                continue
            mk = _str(member, "kind")
            if mk == "FunctionDef":
                mname = _str(member, "name")
                decorators = _list(member, "decorators")
                if "staticmethod" in decorators:
                    static_methods.add(mname)
                if "property" in decorators:
                    property_methods.add(mname)
                methods[mname] = member
            elif mk in ("Assign", "AnnAssign"):
                target = member.get("target")
                if isinstance(target, dict) and _str(target, "kind") == "Name":
                    fname = _str(target, "id")
                    ftype = _str(member, "decl_type")
                    if ftype == "":
                        ftype = _str(member, "resolved_type")
                    if ftype == "":
                        ftype = _str(target, "resolved_type")
                    fields[fname] = ftype
        ctx.class_instance_methods[name] = methods
        ctx.class_static_methods[name] = static_methods
        ctx.class_property_methods[name] = property_methods
        ctx.class_fields[name] = fields


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def emit_lua_module(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a complete Lua module from an EAST3 document."""
    meta = _dict(east3_doc, "meta")
    emit_ctx_meta = _dict(meta, "emit_context")
    module_id = ""
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
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "lua" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Skip runtime/native modules
    if should_skip_module(module_id, mapping):
        return ""

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
        type_id_resolved = _dict(lp, "type_id_resolved_v1")
        type_id_base_map = _dict(lp, "type_id_base_map_v1")
        id_to_fqcn: dict[int, str] = {}
        for fqcn, tid in type_id_resolved.items():
            if isinstance(fqcn, str) and isinstance(tid, int):
                id_to_fqcn[tid] = fqcn
        for fqcn, info in type_info_table.items():
            if not isinstance(fqcn, str) or not isinstance(info, dict):
                continue
            type_id_val = info.get("id")
            if isinstance(type_id_val, int):
                ctx.exception_type_ids[fqcn] = type_id_val
                ctx.class_type_ids[fqcn] = type_id_val
                ctx.tid_const_types[_tid_const_name(fqcn)] = fqcn.rsplit(".", 1)[-1]
        for fqcn, base_tid in type_id_base_map.items():
            if not isinstance(fqcn, str) or not isinstance(base_tid, int):
                continue
            if "." not in fqcn:
                continue
            base_fqcn = id_to_fqcn.get(base_tid, "")
            if base_fqcn == "" or "." not in base_fqcn:
                continue
            ctx.class_bases[fqcn.rsplit(".", 1)[-1]] = base_fqcn.rsplit(".", 1)[-1]

    ctx.import_alias_modules = build_import_alias_map(meta)
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)

    # First pass: collect class info
    _collect_module_class_info(ctx, body)

    # Emit runtime dofile for entry modules
    if ctx.is_entry:
        _emit(ctx, '-- Load runtime')
        _emit(ctx, 'local __script_dir = debug.getinfo(1, "S").source:match("^@(.*[\\\\/])") or ""')
        _emit(ctx, 'dofile(__script_dir .. "built_in/py_runtime.lua")')
        _emit(ctx, 'local __error_mod = __script_dir .. "pytra_built_in_error.lua"')
        _emit(ctx, 'local __error_fp = io.open(__error_mod, "r")')
        _emit(ctx, 'if __error_fp ~= nil then')
        ctx.indent_level += 1
        _emit(ctx, '__error_fp:close()')
        _emit(ctx, 'dofile(__error_mod)')
        ctx.indent_level -= 1
        _emit(ctx, 'end')
        _emit_blank(ctx)

    # Emit module body (skip imports, already handled by runtime)
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        _emit_stmt(ctx, stmt)

    # Emit main guard
    if len(main_guard) > 0 and ctx.is_entry:
        _emit_blank(ctx)
        _emit(ctx, "-- main")
        _emit_body(ctx, main_guard)

    output = "\n".join(ctx.lines).rstrip() + "\n"
    return output


def transpile_to_lua(east3_doc: dict[str, JsonVal]) -> str:
    """Transpile an EAST3 document to Lua source code.

    This is the public API matching the `(dict) -> str` signature.
    """
    meta = east3_doc.get("meta", {})
    emit_ctx = meta.get("emit_context", {}) if isinstance(meta, dict) else {}
    module_id = emit_ctx.get("module_id", "") if isinstance(emit_ctx, dict) else ""
    return emit_lua_module(east3_doc)
