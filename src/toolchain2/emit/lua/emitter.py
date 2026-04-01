"""EAST3 -> Lua source code emitter.

Lua emitter は CommonRenderer + override 構成。
Lua 固有のノード（1-based index, nil, tables, metatables 等）のみ override として実装する。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.emit.lua.types import (
    lua_type, lua_zero_value, _safe_lua_ident, _split_generic_args,
    is_numeric_type, is_integer_type,
    LUA_EXCEPTION_TYPE_NAMES, LUA_PATH_TYPE_NAMES, LUA_BUILTIN_MODULE_PREFIX,
    LUA_NON_INHERITABLE_BASES, LUA_PYTRA_ISINSTANCE_NAME,
)
from toolchain2.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_import_alias_map, build_runtime_import_map,
    resolve_runtime_symbol_name,
)
from toolchain2.emit.common.common_renderer import CommonRenderer
from toolchain2.link.expand_defaults import expand_cross_module_defaults


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
    is_type_id_table: bool = False
    current_exc_var: str = ""
    catch_stack: list[tuple[str, str]] = field(default_factory=list)
    vararg_functions: set[str] = field(default_factory=set)
    declared_locals: set[str] = field(default_factory=set)
    in_class_body: bool = False
    needs_continue_label: bool = False


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
    return "__pytra_isinstance(" + obj + ", " + _safe_lua_ident(type_name) + ")"


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
    value = _emit_expr(ctx, node.get("value"))
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
    _emit_error_propagation(ctx, err_code, allow_current_catch=False)


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
                cond = "__pytra_isinstance(" + catch_err_var + ", " + _safe_lua_ident(exc_type) + ")"
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
                ctx.current_exc_var = catch_err_var
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
    if isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
        return "self." + _safe_lua_ident(attr)
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
                mod_short = mod_id.rsplit(".", 1)[-1]
                qualified_key = mod_short + "." + runtime_symbol
                if qualified_key in ctx.mapping.calls:
                    return ctx.mapping.calls[qualified_key]
                resolved = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping)
                return resolved
    # Property access
    if isinstance(owner_node, dict):
        owner_rt = _str(owner_node, "resolved_type")
        # Path properties
        if owner_rt in LUA_PATH_TYPE_NAMES:
            if attr in ("name", "stem", "parent"):
                owner = _emit_expr(ctx, owner_node)
                return owner + "." + attr
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
    func_node = node.get("func")

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

    if call_name.startswith("__LIST_") and isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
        owner_node = func_node.get("value")
        if isinstance(owner_node, dict):
            arg_strs = [_emit_expr(ctx, owner_node)] + arg_strs

    # Special markers
    if call_name == "__CAST__":
        if len(arg_strs) >= 2:
            return arg_strs[1]
        if len(arg_strs) == 1:
            return arg_strs[0]
        return "nil"

    if call_name == "__PANIC__":
        msg = arg_strs[0] if len(arg_strs) > 0 else '"error"'
        return 'error(' + msg + ')'

    # Container operation markers
    if call_name == "__LIST_APPEND__":
        if len(arg_strs) >= 2:
            return "table.insert(" + arg_strs[0] + ", " + arg_strs[1] + ")"
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
            return "table.insert(" + arg_strs[0] + ", " + arg_strs[1] + ")"
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
        return call_name + "(" + ", ".join(arg_strs) + ")"

    # Fallback: emit callee from func node
    if isinstance(func_node, dict):
        func_id = _str(func_node, "id")

        # Try mapping by bare function name
        if call_name == "" and func_id != "":
            if func_id == LUA_PYTRA_ISINSTANCE_NAME:
                linked = _emit_linked_type_id_isinstance(ctx, args)
                if linked is not None:
                    return linked
            mapped = ctx.mapping.calls.get(func_id, "")
            if mapped != "":
                if mapped == "__CAST__":
                    if len(arg_strs) >= 2:
                        return arg_strs[1]
                    if len(arg_strs) == 1:
                        return arg_strs[0]
                    return "nil"
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
                    return owner + "." + _safe_lua_ident(attr) + "(" + ", ".join(arg_strs) + ")"
                if dispatch_kind == "static_method" or (owner_id in ctx.class_names and attr in ctx.class_static_methods.get(owner_id, set())):
                    return owner + "." + _safe_lua_ident(attr) + "(" + ", ".join(arg_strs) + ")"
                # String methods
                if owner_rt == "str" or owner_rt == "string":
                    return _emit_str_method(ctx, owner, attr, arg_strs)
                if owner_rt.startswith("list[") or owner_rt == "list":
                    if attr == "append" and len(arg_strs) >= 1:
                        return "table.insert(" + owner + ", " + arg_strs[0] + ")"
                    if attr == "clear":
                        return "__pytra_list_clear(" + owner + ")"
                    if attr == "extend" and len(arg_strs) >= 1:
                        return "__pytra_list_extend(" + owner + ", " + arg_strs[0] + ")"
                if owner_rt == "bytearray":
                    if attr == "append" and len(arg_strs) >= 1:
                        return "__pytra_bytearray_append(" + owner + ", " + arg_strs[0] + ")"
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
        neg_val = _get_negative_int_literal(slice_node)
        if neg_val is not None:
            idx = owner + ":len() + " + str(neg_val) + " + 1"
            return "string.sub(" + owner + ", " + idx + ", " + idx + ")"
        idx = slice_code + " + 1"
        return "string.sub(" + owner + ", " + idx + ", " + idx + ")"
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
        return "(" + left + " & " + right + ")"
    if op == "BitOr":
        return "(" + left + " | " + right + ")"
    if op == "BitXor":
        return "(" + left + " ~ " + right + ")"
    if op == "LShift":
        return "(" + left + " << " + right + ")"
    if op == "RShift":
        return "(" + left + " >> " + right + ")"
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
    for idx, comparator in enumerate(comparators):
        op_obj = ops[idx] if idx < len(ops) else None
        op_name = op_obj if isinstance(op_obj, str) else ""
        if isinstance(op_obj, dict):
            op_name = _str(op_obj, "kind")
        right = _emit_expr(ctx, comparator)
        cmp_op = _cmp_op_text(op_name)
        if cmp_op == "__IN__":
            parts.append("__pytra_contains(" + right + ", " + current_left + ")")
        elif cmp_op == "__NOT_IN__":
            parts.append("(not __pytra_contains(" + right + ", " + current_left + "))")
        elif cmp_op == "__IS__":
            parts.append("(" + current_left + " == " + right + ")")
        elif cmp_op == "__IS_NOT__":
            parts.append("(" + current_left + " ~= " + right + ")")
        else:
            parts.append("(" + current_left + " " + cmp_op + " " + right + ")")
        current_left = right
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
    lua_op = "and" if op == "And" else "or"
    parts = [_emit_expr(ctx, v) for v in values]
    return "(" + (" " + lua_op + " ").join(parts) + ")"


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
    return "{" + ", ".join(elem_strs) + "}"


def _emit_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test = _emit_expr(ctx, node.get("test"))
    body = _emit_expr(ctx, node.get("body"))
    orelse = _emit_expr(ctx, node.get("orelse"))
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


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    body_node = node.get("body")
    arg_order = _list(node, "arg_order")
    arg_names: list[str] = []
    if len(arg_order) > 0:
        for a in arg_order:
            if isinstance(a, str):
                arg_names.append(_lua_symbol_name(ctx, a))
    else:
        args = _list(node, "args")
        for a in args:
            if isinstance(a, dict):
                arg_names.append(_lua_symbol_name(ctx, _str(a, "arg")))
    body_code = _emit_expr(ctx, body_node)
    return "function(" + ", ".join(arg_names) + ") return " + body_code + " end"


def _emit_range_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    start = node.get("start")
    stop = node.get("stop")
    step = node.get("step")
    start_code = _emit_expr(ctx, start) if isinstance(start, dict) else "0"
    stop_code = _emit_expr(ctx, stop) if isinstance(stop, dict) else "0"
    if isinstance(step, dict):
        step_code = _emit_expr(ctx, step)
        return "__pytra_range(" + start_code + ", " + stop_code + ", " + step_code + ")"
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


def _emit_body(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        _emit_stmt(ctx, stmt)


def _emit_body_with_continue(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Emit body and add ::__continue__:: label if needed."""
    saved = ctx.needs_continue_label
    ctx.needs_continue_label = False
    _emit_body(ctx, body)
    if ctx.needs_continue_label:
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

    if unused:
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
        val_code = _emit_expr(ctx, value)
        if declare and _str(target, "kind") == "Name":
            name = _str(target, "id")
            safe = _lua_symbol_name(ctx, name)
            if safe not in ctx.declared_locals:
                ctx.declared_locals.add(safe)
                _emit(ctx, "local " + safe + " = " + val_code)
                # Track type
                decl_type = _str(node, "decl_type")
                if decl_type == "":
                    decl_type = _str(node, "resolved_type")
                if decl_type != "":
                    ctx.var_types[safe] = decl_type
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
    names: list[str] = []
    for e in elements:
        if isinstance(e, dict):
            name = _str(e, "id")
            if _bool(e, "unused"):
                names.append("_")
            else:
                safe = _lua_symbol_name(ctx, name)
                names.append(safe)
        else:
            names.append("_")
    val_code = _emit_expr(ctx, value)
    # Check if RHS is a tuple literal
    if isinstance(value, dict) and _str(value, "kind") == "Tuple":
        rhs_elems = _list(value, "elements")
        rhs_parts = [_emit_expr(ctx, e) for e in rhs_elems]
        if declare:
            _emit(ctx, "local " + ", ".join(names) + " = " + ", ".join(rhs_parts))
        else:
            _emit(ctx, ", ".join(names) + " = " + ", ".join(rhs_parts))
        return
    # Unpack table
    temp = _next_temp(ctx, "tup")
    _emit(ctx, "local " + temp + " = " + val_code)
    for i, n in enumerate(names):
        if n == "_":
            continue
        if declare:
            _emit(ctx, "local " + n + " = " + temp + "[" + str(i + 1) + "]")
        else:
            _emit(ctx, n + " = " + temp + "[" + str(i + 1) + "]")


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
    test = _emit_expr(ctx, node.get("test"))
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
    test = _emit_expr(ctx, node.get("test"))
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

    # Collect argument names from arg_order (EAST3 format)
    arg_order = _list(node, "arg_order")
    arg_names: list[str] = []
    if len(arg_order) > 0:
        for a in arg_order:
            if isinstance(a, str):
                if a == "self":
                    continue
                arg_names.append(_lua_symbol_name(ctx, a))
    arg_types = _dict(node, "arg_types")
    if len(arg_types) > 0:
        for a in arg_types.keys():
            if a == "self":
                continue
            safe_a = _lua_symbol_name(ctx, a)
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
    if base_name != "" and base_name not in LUA_NON_INHERITABLE_BASES:
        base_safe = _safe_lua_ident(base_name)
        _emit(ctx, "setmetatable(" + safe + ", {__index = " + base_safe + "})")
    _emit_blank(ctx)

    saved_class = ctx.current_class
    saved_in_class = ctx.in_class_body
    ctx.current_class = safe
    ctx.in_class_body = True

    has_init = False
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
    if kind == "ImportFrom":
        module = _str(node, "module")
        if should_skip_module(module, ctx.mapping):
            return
        if module.startswith("typing") or module.startswith("__future__") or module.startswith("dataclasses"):
            return
        # For Lua, use dofile/require for user modules
        # Skip for most stdlib modules already handled by runtime
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
    zero = lua_zero_value(decl_type)
    ctx.declared_locals.add(safe)
    ctx.var_types[safe] = decl_type
    _emit(ctx, "local " + safe + " = " + zero)


def _emit_swap(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    left = node.get("left")
    right = node.get("right")
    if isinstance(left, dict) and isinstance(right, dict):
        lc = _lua_symbol_name(ctx, _str(left, "id"))
        rc = _lua_symbol_name(ctx, _str(right, "id"))
        _emit(ctx, lc + ", " + rc + " = " + rc + ", " + lc)


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
    _emit(ctx, "local " + temp + " = " + val_code)
    for i, n in enumerate(names):
        _emit(ctx, n + " = " + temp + "[" + str(i + 1) + "]")


def _emit_with(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    context_expr = node.get("context_expr")
    var_name = _str(node, "var_name")
    body = _list(node, "body")
    ctx_code = _emit_expr(ctx, context_expr)
    safe_var = _lua_symbol_name(ctx, var_name) if var_name != "" else _next_temp(ctx, "ctx")
    _emit(ctx, "local " + safe_var + " = " + ctx_code)
    _emit(ctx, "local __with_ok__, __with_err__ = pcall(function()")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "end)")
    _emit(ctx, "if " + safe_var + " and " + safe_var + ".close then " + safe_var + ":close() end")
    _emit(ctx, "if not __with_ok__ then error(__with_err__) end")


def _emit_try(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")

    if len(handlers) == 0 and len(finalbody) == 0:
        _emit_body(ctx, body)
        return

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


def _emit_raise(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    exc = node.get("exc")
    if isinstance(exc, dict):
        val = _emit_expr(ctx, exc)
        _emit(ctx, "error(" + val + ")")
    else:
        # Bare raise: re-raise current exception
        if ctx.current_exc_var != "":
            _emit(ctx, "error(" + _lua_symbol_name(ctx, ctx.current_exc_var) + ")")
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
        return "__pytra_isinstance(" + subject + ", " + _safe_lua_ident(variant_name) + ")"
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
                    ftype = _str(member, "resolved_type")
                    fields[fname] = ftype
        ctx.class_instance_methods[name] = methods
        ctx.class_static_methods[name] = static_methods
        ctx.class_property_methods[name] = property_methods
        ctx.class_fields[name] = fields


# ---------------------------------------------------------------------------
# Module header (dofile for runtime)
# ---------------------------------------------------------------------------

def _emit_module_header(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Emit the Lua module header with dofile for runtime."""
    # Runtime is loaded via dofile
    pass


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
        expand_cross_module_defaults([(module_id, east3_doc)])

    # Load runtime mapping
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "lua" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Skip runtime/built_in modules
    if should_skip_module(module_id, mapping):
        return ""

    # built_in.error is emitted as pure Python exception classes.
    if module_id.startswith(LUA_BUILTIN_MODULE_PREFIX) and module_id != "pytra.built_in.error":
        return ""

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
        if kind in ("ImportFrom", "Import"):
            continue
        _emit_stmt(ctx, stmt)

    # Emit main guard
    if len(main_guard) > 0 and ctx.is_entry:
        _emit_blank(ctx)
        _emit(ctx, "-- main")
        _emit_body(ctx, main_guard)

    # type_id_table: emit pytra_isinstance
    if is_type_id_table:
        _emit_blank(ctx)
        _emit(ctx, "function pytra_isinstance(actual, tid)")
        ctx.indent_level += 1
        _emit(ctx, "return id_table[tid * 2 + 1] <= actual and actual <= id_table[tid * 2 + 2]")
        ctx.indent_level -= 1
        _emit(ctx, "end")

    output = "\n".join(ctx.lines).rstrip() + "\n"
    return output


def transpile_to_lua(east3_doc: dict[str, JsonVal]) -> str:
    """Transpile an EAST3 document to Lua source code.

    This is the public API matching the `(dict) -> str` signature.
    """
    meta = east3_doc.get("meta", {})
    emit_ctx = meta.get("emit_context", {}) if isinstance(meta, dict) else {}
    module_id = emit_ctx.get("module_id", "") if isinstance(emit_ctx, dict) else ""
    # built_in.error is emitted as pure Python exception classes.
    if isinstance(module_id, str) and module_id.startswith(LUA_BUILTIN_MODULE_PREFIX) and module_id != "pytra.built_in.error":
        return ""
    return emit_lua_module(east3_doc)
