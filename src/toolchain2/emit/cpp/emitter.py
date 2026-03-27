"""EAST3 → C++ source code emitter.

Based on the Go emitter template. Generates standalone C++ source files
from linked EAST3 JSON documents.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.emit.cpp.types import (
    cpp_type,
    cpp_zero_value,
    cpp_signature_type,
    cpp_param_decl,
    collect_cpp_type_vars,
)
from toolchain2.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_import_alias_map, build_runtime_import_map, resolve_runtime_symbol_name,
)
from toolchain2.emit.cpp.runtime_paths import collect_cpp_dependency_module_ids, cpp_include_for_module


# ---------------------------------------------------------------------------
# Emit context
# ---------------------------------------------------------------------------

@dataclass
class CppEmitContext:
    module_id: str = ""
    is_entry: bool = False
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    includes_needed: set[str] = field(default_factory=set)
    var_types: dict[str, str] = field(default_factory=dict)
    class_names: set[str] = field(default_factory=set)
    class_field_types: dict[str, dict[str, str]] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_info: dict[str, dict[str, int]] = field(default_factory=dict)
    class_symbol_fqcns: dict[str, str] = field(default_factory=dict)
    current_class: str = ""
    current_return_type: str = ""
    runtime_imports: dict[str, str] = field(default_factory=dict)
    import_aliases: dict[str, str] = field(default_factory=dict)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    temp_counter: int = 0
    emit_class_decls: bool = True


def _indent(ctx: CppEmitContext) -> str:
    return "    " * ctx.indent_level

def _emit(ctx: CppEmitContext, line: str) -> None:
    ctx.lines.append(_indent(ctx) + line)

def _emit_blank(ctx: CppEmitContext) -> None:
    ctx.lines.append("")


def _emit_fail(ctx: CppEmitContext, code: str, detail: str) -> None:
    module_label = ctx.module_id if ctx.module_id != "" else "<unknown>"
    raise RuntimeError("cpp emitter " + code + " in " + module_label + ": " + detail)


# ---------------------------------------------------------------------------
# Node accessors
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


def _lookup_explicit_runtime_symbol_mapping(
    ctx: CppEmitContext,
    *,
    resolved_runtime_call: str = "",
    runtime_call: str = "",
    runtime_symbol: str = "",
    fallback_symbol: str = "",
) -> str:
    for key in (resolved_runtime_call, runtime_call, runtime_symbol, fallback_symbol):
        if key != "" and key in ctx.mapping.calls:
            return ctx.mapping.calls[key]
    return ""


def _effective_resolved_type(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    resolved_type = _str(node, "resolved_type")
    if resolved_type not in ("", "unknown"):
        return resolved_type
    summary = _dict(node, "type_expr_summary_v1")
    if _str(summary, "category") == "static":
        mirror = _str(summary, "mirror")
        if mirror != "":
            return mirror
    return resolved_type


def _attribute_static_type(ctx: CppEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict) or _str(node, "kind") != "Attribute":
        return ""
    owner_node = node.get("value")
    owner_type = _effective_resolved_type(owner_node)
    if owner_type == "":
        owner_type = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
    fields = ctx.class_field_types.get(owner_type, {})
    attr = _str(node, "attr")
    field_type = fields.get(attr)
    return field_type if isinstance(field_type, str) else ""


def _expr_static_type(ctx: CppEmitContext, node: JsonVal) -> str:
    inferred = _effective_resolved_type(node)
    if inferred not in ("", "unknown"):
        return inferred
    if isinstance(node, dict):
        kind = _str(node, "kind")
        if kind in ("Name", "NameTarget"):
            name = _str(node, "id")
            if name != "":
                return ctx.var_types.get(name, "")
        if kind == "Attribute":
            return _attribute_static_type(ctx, node)
    return ""


def _expr_storage_type(ctx: CppEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    kind = _str(node, "kind")
    if kind in ("Name", "NameTarget"):
        name = _str(node, "id")
        if name != "":
            return ctx.var_types.get(name, "")
    if kind == "Attribute":
        return _attribute_static_type(ctx, node)
    return ""


def _optional_inner_type(type_name: str) -> str:
    t = type_name.strip()
    if t.endswith(" | None"):
        return t[:-7].strip()
    if t.endswith("|None"):
        return t[:-6].strip()
    if t.startswith("None | "):
        return t[7:].strip()
    if t.startswith("None|"):
        return t[5:].strip()
    return ""


def _node_type_mirror(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    summary = node.get("type_expr_summary_v1")
    if isinstance(summary, dict):
        mirror = summary.get("mirror")
        if isinstance(mirror, str) and mirror != "":
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
    if runtime_module_id != "" and should_skip_module(runtime_module_id, ctx.mapping):
        return resolve_runtime_symbol_name(
            symbol_name,
            ctx.mapping,
            resolved_runtime_call=resolved_runtime_call,
            runtime_call=runtime_call,
        )
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
        bindings = raw.get("bindings") if isinstance(raw, dict) else raw
        if not isinstance(bindings, list):
            continue
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            local_name = binding.get("local_name")
            export_name = binding.get("export_name")
            if not isinstance(local_name, str) or local_name == "":
                continue
            if not isinstance(export_name, str) or export_name == "":
                continue
            candidate_module = binding.get("runtime_module_id")
            if not isinstance(candidate_module, str) or candidate_module == "":
                candidate_module = binding.get("module_id")
            if not isinstance(candidate_module, str) or candidate_module == "":
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
    actual_id = actual_info.get("id")
    expected_entry = expected_info.get("entry")
    expected_exit = expected_info.get("exit")
    return (
        isinstance(actual_id, int)
        and isinstance(expected_entry, int)
        and isinstance(expected_exit, int)
        and expected_entry <= actual_id < expected_exit
    )


def _qualify_runtime_call_symbol(symbol_name: str) -> str:
    if symbol_name == "" or symbol_name.startswith("::") or "::" in symbol_name:
        return symbol_name
    return "::" + symbol_name


# ---------------------------------------------------------------------------
# Expression emission
# ---------------------------------------------------------------------------

def _emit_expr(ctx: CppEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        _emit_fail(ctx, "invalid_expr", "expected dict expression node")
    kind = _str(node, "kind")

    if kind == "Constant": return _emit_constant(ctx, node)
    if kind == "Name": return _emit_name(ctx, node)
    if kind == "ObjTypeId": return _emit_obj_type_id(ctx, node)
    if kind == "IsInstance": return _emit_isinstance(ctx, node)
    if kind == "IsSubclass": return _emit_issubclass(ctx, node)
    if kind == "IsSubtype": return _emit_issubtype(ctx, node)
    if kind == "BinOp": return _emit_binop(ctx, node)
    if kind == "UnaryOp": return _emit_unaryop(ctx, node)
    if kind == "Compare": return _emit_compare(ctx, node)
    if kind == "BoolOp": return _emit_boolop(ctx, node)
    if kind == "Call": return _emit_call(ctx, node)
    if kind == "Attribute": return _emit_attribute(ctx, node)
    if kind == "Subscript": return _emit_subscript(ctx, node)
    if kind == "List": return _emit_list_literal(ctx, node)
    if kind == "Dict": return _emit_dict_literal(ctx, node)
    if kind == "Tuple": return _emit_tuple_literal(ctx, node)
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
    if isinstance(val, bool): return "true" if val else "false"
    if isinstance(val, int):
        rt = _str(node, "resolved_type")
        if rt in ("float64", "float32", "float"): return str(float(val))
        if rt in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
            return cpp_signature_type(rt) + "(" + str(val) + ")"
        return str(val)
    if isinstance(val, float):
        s = repr(val)
        if s == "inf": return "std::numeric_limits<double>::infinity()"
        if s == "-inf": return "-std::numeric_limits<double>::infinity()"
        return s
    if isinstance(val, str):
        return _cpp_string(val)
    return repr(val)


def _cpp_string(s: str) -> str:
    out: list[str] = ['"']
    for ch in s:
        if ch == "\\": out.append("\\\\")
        elif ch == '"': out.append('\\"')
        elif ch == "\n": out.append("\\n")
        elif ch == "\r": out.append("\\r")
        elif ch == "\t": out.append("\\t")
        elif ord(ch) < 32: out.append("\\x" + format(ord(ch), "02x"))
        else: out.append(ch)
    out.append('"')
    return "str(" + "".join(out) + ")"


def _emit_name(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "": name = _str(node, "repr")
    if name == "True": return "true"
    if name == "False": return "false"
    if name == "None": return "::std::nullopt"
    if name == "self": return "this"
    if name == "continue": return "continue"
    if name == "break": return "break"
    if name == "main": return "__pytra_main"
    return name


def _emit_binop(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    op = _str(node, "op")
    rt = _str(node, "resolved_type")
    # Apply casts
    for cast in _list(node, "casts"):
        if isinstance(cast, dict):
            on = _str(cast, "on")
            to = cpp_type(_str(cast, "to"))
            if on == "left": left = "static_cast<" + to + ">(" + left + ")"
            elif on == "right": right = "static_cast<" + to + ">(" + right + ")"
    # List multiply
    if op == "Mult":
        ln = node.get("left")
        rn = node.get("right")
        if isinstance(ln, dict) and _str(ln, "kind") == "List":
            return cpp_type(rt) + "(" + right + ", " + (_emit_expr(ctx, _list(ln, "elements")[0]) if len(_list(ln, "elements")) == 1 else "0") + ")"
        if isinstance(rn, dict) and _str(rn, "kind") == "List":
            return cpp_type(rt) + "(" + left + ", " + (_emit_expr(ctx, _list(rn, "elements")[0]) if len(_list(rn, "elements")) == 1 else "0") + ")"
    if op == "FloorDiv": return "py_floordiv(" + left + ", " + right + ")"
    if op == "Pow": return "std::pow(static_cast<double>(" + left + "), static_cast<double>(" + right + "))"
    go_op = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "Mod": "%",
             "BitOr": "|", "BitAnd": "&", "BitXor": "^", "LShift": "<<", "RShift": ">>"}.get(op, "+")
    return "(" + left + " " + go_op + " " + right + ")"


def _emit_unaryop(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    if op == "USub": return "(-" + operand + ")"
    if op == "Not": return "(!" + operand + ")"
    if op == "Invert": return "(~" + operand + ")"
    return operand


def _emit_compare(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    ops = _list(node, "ops")
    comparators = _list(node, "comparators")
    if len(ops) == 0: return left
    parts: list[str] = []
    prev = left
    for i in range(len(ops)):
        op_str = ops[i] if isinstance(ops[i], str) else ""
        comp = comparators[i] if i < len(comparators) else None
        right = _emit_expr(ctx, comp)
        if op_str == "In": parts.append("py_contains(" + right + ", " + prev + ")")
        elif op_str == "NotIn": parts.append("!py_contains(" + right + ", " + prev + ")")
        elif op_str == "Is": parts.append("(" + prev + " == " + right + ")")
        elif op_str == "IsNot": parts.append("(" + prev + " != " + right + ")")
        else:
            cmp = {"Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=", "Gt": ">", "GtE": ">="}.get(op_str, "==")
            parts.append("(" + prev + " " + cmp + " " + right + ")")
        prev = right
    return "(" + " && ".join(parts) + ")" if len(parts) > 1 else parts[0]


def _emit_boolop(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    op = _str(node, "op")
    values = _list(node, "values")
    cpp_op = " && " if op == "And" else " || "
    return "(" + cpp_op.join(_emit_expr(ctx, v) for v in values) + ")"


def _emit_call(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    if _str(node, "lowered_kind") == "BuiltinCall":
        return _emit_builtin_call(ctx, node)
    func = node.get("func")
    args = _list(node, "args")
    arg_strs = [_emit_expr(ctx, a) for a in args]
    call_arg_strs = list(arg_strs)
    adapter = _str(node, "runtime_call_adapter_kind")
    if adapter == "image.save_gif.keyword_defaults":
        keywords = _list(node, "keywords")
        for kw in keywords:
            if isinstance(kw, dict):
                call_arg_strs.append(_emit_expr(ctx, kw.get("value")))
    if isinstance(func, dict):
        fk = _str(func, "kind")
        if fk == "Attribute":
            owner = _emit_expr(ctx, func.get("value"))
            attr = _str(func, "attr")
            owner_node = func.get("value")
            owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
            owner_module = ctx.import_aliases.get(owner_id, "")
            runtime_module_id = _str(func, "runtime_module_id")
            runtime_symbol = _str(func, "runtime_symbol")
            if _is_type_owner(ctx, owner_node):
                return owner + "::" + attr + "(" + ", ".join(call_arg_strs) + ")"
            if owner_module != "":
                symbol_name = _resolve_runtime_attr_symbol(
                    ctx,
                    runtime_module_id=runtime_module_id if runtime_module_id != "" else owner_module,
                    resolved_runtime_call=_str(node, "resolved_runtime_call"),
                    runtime_call=_str(node, "runtime_call"),
                    runtime_symbol=runtime_symbol,
                    fallback_symbol=attr,
                )
                return _qualify_runtime_call_symbol(symbol_name) + "(" + ", ".join(call_arg_strs) + ")"
            if runtime_module_id != "" and should_skip_module(runtime_module_id, ctx.mapping):
                symbol_name = _resolve_runtime_attr_symbol(
                    ctx,
                    runtime_module_id=runtime_module_id,
                    resolved_runtime_call=_str(node, "resolved_runtime_call"),
                    runtime_call=_str(node, "runtime_call"),
                    runtime_symbol=runtime_symbol,
                    fallback_symbol=attr,
                )
                return _qualify_runtime_call_symbol(symbol_name) + "(" + ", ".join(call_arg_strs) + ")"
            if attr == "append" and len(call_arg_strs) >= 1:
                return owner + ".push_back(" + call_arg_strs[0] + ")"
            if owner == "this":
                return "this->" + attr + "(" + ", ".join(call_arg_strs) + ")"
            return owner + "." + attr + "(" + ", ".join(call_arg_strs) + ")"
        if fk == "Name":
            fn = _str(func, "id")
            if fn == "": fn = _str(func, "repr")
            if fn == "cast" and len(args) >= 2:
                return _emit_cast_expr(ctx, args[0], args[1])
            if fn in ("bytearray", "bytes"):
                if len(args) >= 1 and isinstance(args[0], dict):
                    a0_kind = _str(args[0], "kind")
                    a0_rt = _str(args[0], "resolved_type")
                    if a0_kind == "List":
                        elems = _list(args[0], "elements")
                        parts = ["uint8(" + _emit_expr(ctx, e) + ")" for e in elems]
                        return "bytes{" + ", ".join(parts) + "}"
                    if a0_rt in ("int64", "int32", "int", "uint8", "int8"):
                        return "bytes(" + arg_strs[0] + ")"
                if len(arg_strs) >= 1:
                    return "bytes(" + arg_strs[0] + ")"
                return "bytes{}"
            if fn in ctx.class_names: return fn + "(" + ", ".join(call_arg_strs) + ")"
            if fn in ctx.runtime_imports: return ctx.runtime_imports[fn] + "(" + ", ".join(call_arg_strs) + ")"
            if fn == "main": return "__pytra_main(" + ", ".join(call_arg_strs) + ")"
            return fn + "(" + ", ".join(call_arg_strs) + ")"
    return _emit_expr(ctx, func) + "(" + ", ".join(call_arg_strs) + ")"


def _emit_condition_expr(ctx: CppEmitContext, node: JsonVal) -> str:
    expr = _emit_expr(ctx, node)
    if not isinstance(node, dict):
        return expr
    resolved_type = _str(node, "resolved_type")
    if (
        resolved_type.startswith("list[")
        or resolved_type.startswith("dict[")
        or resolved_type.startswith("set[")
        or resolved_type in ("bytes", "bytearray")
    ):
        return "(!(" + expr + ").empty())"
    return expr


def _emit_builtin_call(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    rc = _str(node, "runtime_call")
    bn = _str(node, "builtin_name")
    args = _list(node, "args")
    arg_strs = [_emit_expr(ctx, a) for a in args]
    func = node.get("func")
    method_owner = ""
    call_arg_strs = arg_strs
    if isinstance(func, dict) and _str(func, "kind") == "Attribute":
        method_owner = _emit_expr(ctx, func.get("value"))
        call_arg_strs = [method_owner] + arg_strs

    if rc in ("static_cast", "int", "float", "bool"):
        rt = _str(node, "resolved_type")
        ct = cpp_signature_type(rt)
        if len(args) >= 1 and isinstance(args[0], dict):
            arg_kind = _str(args[0], "kind")
            storage_type = _expr_storage_type(ctx, args[0])
            if _optional_inner_type(storage_type) == rt:
                return "(*(" + arg_strs[0] + "))"
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
        if len(args) >= 1 and isinstance(args[0], dict) and _str(args[0], "resolved_type") == "str":
            arg_kind = _str(args[0], "kind")
            storage_type = _expr_storage_type(ctx, args[0])
            if arg_kind != "Unbox" and storage_type not in ("", "unknown") and _needs_object_cast(storage_type):
                return _emit_object_unbox(arg_strs[0], "str")
            return arg_strs[0]
        return "str(py_to_string(" + arg_strs[0] + "))"
    if rc in ("bytearray_ctor", "bytes_ctor"):
        if len(args) >= 1 and isinstance(args[0], dict):
            a0_kind = _str(args[0], "kind")
            a0_rt = _str(args[0], "resolved_type")
            if a0_kind == "List":
                elems = _list(args[0], "elements")
                parts = ["uint8(" + _emit_expr(ctx, e) + ")" for e in elems]
                return "bytes{" + ", ".join(parts) + "}"
            if a0_rt in ("int64", "int32", "int", "uint8", "int8"):
                return "bytes(" + arg_strs[0] + ")"
        if len(arg_strs) >= 1:
            return "bytes(" + arg_strs[0] + ")"
        return "bytes{}"
    if rc in ("py_print", "py_len") and len(arg_strs) >= 1:
        return rc + "(" + ", ".join(arg_strs) + ")"
    if rc == "py_int_from_str" and len(arg_strs) >= 1:
        return "std::stoll(" + arg_strs[0] + ")"
    if rc == "py_float_from_str" and len(arg_strs) >= 1:
        return "std::stod(" + arg_strs[0] + ")"
    if bn in ("RuntimeError", "ValueError", "TypeError") or rc == "std::runtime_error":
        if len(arg_strs) >= 1: return "throw std::runtime_error(" + arg_strs[0] + ")"
        return 'throw std::runtime_error("' + bn + '")'
    if rc == "list.append":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            if len(arg_strs) >= 1: return owner + ".push_back(" + arg_strs[0] + ")"
    if rc == "list.pop":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            if len(arg_strs) >= 1:
                return "py_list_pop_mut(" + owner + ", " + arg_strs[0] + ")"
            return "py_list_pop_mut(" + owner + ")"
    if rc == "list.clear":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            return owner + ".clear()"
    if rc == "list.index" and method_owner != "" and len(arg_strs) >= 1:
        return "py_index(" + method_owner + ", " + arg_strs[0] + ")"
    if rc == "dict.get":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            if len(arg_strs) >= 2: return "py_dict_get(" + owner + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
            if len(arg_strs) >= 1: return owner + "[" + arg_strs[0] + "]"
    if rc == "dict.clear":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            return owner + ".clear()"
    if rc == "dict.items":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            return owner + ".items()"
    if rc in ("py_write_text", "pathlib.write_text"):
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            if len(arg_strs) >= 1: return "py_pathlib_write_text(" + owner + ", " + arg_strs[0] + ")"

    # Mapping resolution
    adapter = _str(node, "runtime_call_adapter_kind")
    resolved = resolve_runtime_call(rc, bn, adapter, ctx.mapping)
    if resolved != "": return resolved + "(" + ", ".join(call_arg_strs) + ")"
    fn = rc if rc != "" else bn
    if fn != "":
        if "." in fn:
            _emit_fail(ctx, "unmapped_runtime_call", fn)
        return ctx.mapping.builtin_prefix + fn + "(" + ", ".join(call_arg_strs) + ")"
    _emit_fail(ctx, "unknown_builtin", repr(node))


def _emit_attribute(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    attr = _str(node, "attr")
    owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
    runtime_module_id = _str(node, "runtime_module_id")
    runtime_symbol = _str(node, "runtime_symbol")
    runtime_symbol_dispatch = _str(node, "runtime_symbol_dispatch")
    owner_module = ctx.import_aliases.get(owner_id, "")
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
        return resolve_runtime_symbol_name(
            runtime_symbol,
            ctx.mapping,
            resolved_runtime_call=_str(node, "resolved_runtime_call"),
            runtime_call=_str(node, "runtime_call"),
        )
    if owner == "this":
        return "this->" + attr
    return owner + "." + attr


def _emit_subscript_index(ctx: CppEmitContext, value: str, slice_node: JsonVal) -> str:
    idx = _emit_expr(ctx, slice_node)
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Constant":
        iv = slice_node.get("value")
        if isinstance(iv, int) and iv < 0:
            return "(" + value + ".size()" + str(iv) + ")"
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "UnaryOp" and _str(slice_node, "op") == "USub":
        operand = _emit_expr(ctx, slice_node.get("operand"))
        return "(" + value + ".size() - " + operand + ")"
    return idx


def _emit_subscript(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = _emit_expr(ctx, node.get("value"))
    sl = node.get("slice")
    value_node = node.get("value")
    value_type = _str(value_node, "resolved_type") if isinstance(value_node, dict) else ""
    storage_type = _expr_storage_type(ctx, value_node)
    if (value_type in ("", "unknown", "tuple", "list", "dict", "set") or value_type == storage_type) and storage_type != "":
        value_type = storage_type
    if isinstance(sl, dict) and _str(sl, "kind") == "Slice":
        return _emit_slice_expr(ctx, node, value, sl)
    if value_type.startswith("tuple[") and isinstance(sl, dict) and _str(sl, "kind") == "Constant":
        iv = sl.get("value")
        if isinstance(iv, int) and iv >= 0:
            return "::std::get<" + str(iv) + ">(" + value + ")"
    idx = _emit_subscript_index(ctx, value, sl)
    if value_type == "str":
        return "py_str_slice(" + value + ", " + idx + ", (" + idx + " + int64(1)))"
    if value_type.startswith("dict["):
        return "py_at(" + value + ", " + idx + ")"
    return value + "[" + idx + "]"


def _emit_subscript_store_target(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = _emit_expr(ctx, node.get("value"))
    sl = node.get("slice")
    idx = _emit_subscript_index(ctx, value, sl)
    return value + "[" + idx + "]"


def _emit_list_literal(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    rt = _str(node, "resolved_type")
    ct = cpp_type(rt)
    parts = [_emit_expr(ctx, e) for e in elements]
    return ct + "{" + ", ".join(parts) + "}"


def _emit_dict_literal(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    rt = _str(node, "resolved_type")
    ct = cpp_type(rt)
    entries = _list(node, "entries")
    if len(entries) > 0:
        parts = []
        for e in entries:
            if isinstance(e, dict):
                parts.append("{" + _emit_expr(ctx, e.get("key")) + ", " + _emit_expr(ctx, e.get("value")) + "}")
        return ct + "{" + ", ".join(parts) + "}"
    return ct + "{}"


def _emit_tuple_literal(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    parts = [_emit_expr(ctx, e) for e in elements]
    return "std::make_tuple(" + ", ".join(parts) + ")"


def _emit_unbox(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    value_expr = _emit_expr(ctx, value)
    value_type = _effective_resolved_type(value)
    storage_type = _expr_storage_type(ctx, value)
    target = _str(node, "target")
    if target == "":
        target = _str(node, "resolved_type")
    target_mirror = _node_type_mirror(node)
    if target_mirror != "":
        target = target_mirror
    if target == "" or target == "object":
        return value_expr
    bridge = _dict(node, "bridge_lane_v1")
    if _str(bridge, "value_category") == "optional":
        return "(*(" + value_expr + "))"
    if _optional_inner_type(storage_type) == target:
        return "(*(" + value_expr + "))"
    storage_requires_runtime_unbox = (
        storage_type not in ("", "unknown")
        and storage_type != target
        and (
            _needs_object_cast(storage_type)
            or storage_type.endswith(" | None")
            or storage_type.endswith("|None")
        )
    )
    value_cpp = cpp_signature_type(value_type) if value_type not in ("", "unknown") else ""
    storage_cpp = cpp_signature_type(storage_type) if storage_type not in ("", "unknown") else ""
    target_cpp = cpp_signature_type(target)
    if not storage_requires_runtime_unbox and value_cpp != "" and value_cpp == target_cpp:
        return value_expr
    if storage_cpp != "" and storage_cpp == target_cpp:
        return value_expr
    needs_runtime_unbox = (
        storage_requires_runtime_unbox
        or (_needs_object_cast(storage_type) and storage_type != target)
        or (_needs_object_cast(value_type) and value_type != target)
    )
    if not needs_runtime_unbox and value_type == target:
        return value_expr
    if _attribute_static_type(ctx, value) == target:
        return value_expr
    if target in ctx.class_names:
        return "(*(" + value_expr + ").as<" + target + ">())"
    if target in ("str", "int", "int64", "float", "float64", "bool"):
        return _emit_object_unbox(value_expr, target)
    if (
        target.startswith("list[")
        or target.startswith("dict[")
        or target.startswith("set[")
        or target.startswith("tuple[")
        or target in ("bytes", "bytearray")
    ):
        return "(*(" + value_expr + ").as<" + cpp_signature_type(target) + ">())"
    return value_expr


def _emit_box(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    value_expr = _emit_expr(ctx, value)
    value_type = _effective_resolved_type(value)
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
        cpp_value_type = cpp_signature_type(value_type)
        return (
            "object(make_object<"
            + cpp_value_type
            + ">(py_runtime_value_type_id("
            + value_expr
            + "), "
            + value_expr
            + "))"
        )
    class_type_id = _lookup_class_type_id(ctx, value_type)
    if class_type_id is not None:
        cpp_value_type = cpp_signature_type(value_type)
        return (
            "object(make_object<"
            + cpp_value_type
            + ">("
            + str(class_type_id)
            + ", "
            + value_expr
            + "))"
        )
    return value_expr


def _emit_object_unbox(value_expr: str, target: str) -> str:
    if target == "str":
        return "(" + value_expr + ").unbox<str, PYTRA_TID_STR>()"
    if target in ("int", "int64"):
        return "(" + value_expr + ").unbox<int64, PYTRA_TID_INT>()"
    if target in ("float", "float64"):
        return "(" + value_expr + ").unbox<float64, PYTRA_TID_FLOAT>()"
    if target == "bool":
        return "(" + value_expr + ").unbox<bool, PYTRA_TID_BOOL>()"
    return value_expr


def _emit_isinstance(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    expected = node.get("expected_type_id")
    expected_name = _str(expected, "id") if isinstance(expected, dict) else ""
    value_expr = _emit_expr(ctx, value)
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
    value_type = _effective_resolved_type(value)
    tid = {
        "None": "PYTRA_TID_NONE",
        "bool": "PYTRA_TID_BOOL",
        "int": "PYTRA_TID_INT",
        "int64": "PYTRA_TID_INT",
        "float": "PYTRA_TID_FLOAT",
        "float64": "PYTRA_TID_FLOAT",
        "str": "PYTRA_TID_STR",
        "list": "PYTRA_TID_LIST",
        "dict": "PYTRA_TID_DICT",
        "set": "PYTRA_TID_SET",
        "object": "PYTRA_TID_OBJECT",
    }.get(expected_name, "")
    if tid == "" and expected_name.startswith("PYTRA_TID_"):
        tid = expected_name
    if tid == "":
        class_type_id = _lookup_class_type_id(ctx, expected_name)
        if class_type_id is not None:
            tid = str(class_type_id)
    if tid == "":
        return "false"
    if value_type in ("object", "Any", "Obj", "unknown") or "|" in value_type:
        return "py_runtime_object_isinstance(" + value_expr + ", static_cast<pytra_type_id>(" + tid + "))"
    if _lookup_class_type_id(ctx, expected_name) is not None:
        return "true" if _is_known_class_subtype(ctx, value_type, expected_name) else "false"
    return "py_runtime_value_isinstance(" + value_expr + ", " + tid + ")"


def _emit_obj_type_id(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    value_expr = _emit_expr(ctx, value)
    value_type = _effective_resolved_type(value)
    if value_type in ("object", "Any", "Obj", "unknown") or "|" in value_type:
        return "py_runtime_object_type_id(" + value_expr + ")"
    class_type_id = _lookup_class_type_id(ctx, value_type)
    if class_type_id is not None:
        return "static_cast<pytra_type_id>(" + str(class_type_id) + ")"
    return "py_runtime_value_type_id(" + value_expr + ")"


def _emit_issubtype(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    actual = _emit_expr(ctx, node.get("actual_type_id"))
    expected = _emit_expr(ctx, node.get("expected_type_id"))
    if actual == "" or expected == "":
        return "false"
    return "py_runtime_type_id_is_subtype(" + actual + ", " + expected + ")"


def _emit_issubclass(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    actual = _emit_expr(ctx, node.get("actual_type_id"))
    expected = _emit_expr(ctx, node.get("expected_type_id"))
    if actual == "" or expected == "":
        return "false"
    return "py_runtime_type_id_issubclass(" + actual + ", " + expected + ")"


def _emit_slice_expr(ctx: CppEmitContext, node: dict[str, JsonVal], value_expr: str, slice_node: dict[str, JsonVal]) -> str:
    value_node = node.get("value")
    value_type = _str(value_node, "resolved_type") if isinstance(value_node, dict) else ""
    lower = slice_node.get("lower")
    upper = slice_node.get("upper")
    lo_expr = _emit_expr(ctx, lower) if isinstance(lower, dict) else "0"
    up_expr = _emit_expr(ctx, upper) if isinstance(upper, dict) else "py_len(" + value_expr + ")"
    if value_type == "str":
        return "py_str_slice(" + value_expr + ", " + lo_expr + ", " + up_expr + ")"
    if value_type.startswith("list[") or value_type in ("bytes", "bytearray"):
        return "py_list_slice_copy(" + value_expr + ", " + lo_expr + ", " + up_expr + ")"
    return value_expr + " /* slice */"


def _emit_ifexp(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    test = _emit_expr(ctx, node.get("test"))
    body = _emit_expr(ctx, node.get("body"))
    orelse = _emit_expr(ctx, node.get("orelse"))
    return "(" + test + " ? " + body + " : " + orelse + ")"


def _emit_fstring(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    parts: list[str] = []
    for v in values:
        if isinstance(v, dict):
            if _str(v, "kind") == "Constant" and isinstance(v.get("value"), str):
                parts.append(_cpp_string(v["value"]))
                continue
            parts.append("std::to_string(" + _emit_expr(ctx, v) + ")")
    if len(parts) == 0: return '""'
    return " + ".join(parts)


def _emit_formatted_value(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    return "str(py_to_string(" + _emit_expr(ctx, node.get("value")) + "))"


def _emit_lambda(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    body = node.get("body")
    params = []
    for a in arg_order:
        an = a if isinstance(a, str) else ""
        at = arg_types.get(an, "")
        at_str = at if isinstance(at, str) else ""
        params.append(cpp_param_decl(at_str, an))
    return "[&](" + ", ".join(params) + ") { return " + _emit_expr(ctx, body) + "; }"


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_stmt(ctx: CppEmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        _emit_fail(ctx, "invalid_stmt", "expected dict statement node")
    kind = _str(node, "kind")

    if kind == "Expr": _emit_expr_stmt(ctx, node)
    elif kind == "AnnAssign": _emit_ann_assign(ctx, node)
    elif kind == "Assign": _emit_assign(ctx, node)
    elif kind == "AugAssign": _emit_aug_assign(ctx, node)
    elif kind == "Return": _emit_return(ctx, node)
    elif kind == "If": _emit_if(ctx, node)
    elif kind == "While": _emit_while(ctx, node)
    elif kind == "ForCore": _emit_for_core(ctx, node)
    elif kind == "FunctionDef": _emit_function_def(ctx, node)
    elif kind == "ClosureDef": _emit_closure_def(ctx, node)
    elif kind == "ClassDef": _emit_class_def(ctx, node)
    elif kind == "ImportFrom" or kind == "Import": pass
    elif kind == "Pass": _emit(ctx, "// pass")
    elif kind == "VarDecl": _emit_var_decl(ctx, node)
    elif kind == "Swap": _emit_swap(ctx, node)
    elif kind == "Try": _emit_try(ctx, node)
    elif kind == "Raise": _emit_raise(ctx, node)
    elif kind == "With": _emit_with(ctx, node)
    elif kind == "comment":
        t = _str(node, "text")
        if t != "": _emit(ctx, "// " + t)
    elif kind == "blank": _emit_blank(ctx)
    else:
        _emit_fail(ctx, "unsupported_stmt_kind", kind)


def _emit_body(ctx: CppEmitContext, body: list[JsonVal]) -> None:
    for s in body: _emit_stmt(ctx, s)


def _emit_expr_stmt(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if not isinstance(value, dict): return
    if _str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
        doc = value.get("value")
        if isinstance(doc, str) and doc.strip() != "":
            for line in doc.strip().split("\n"): _emit(ctx, "// " + line)
        return
    code = _emit_expr(ctx, value)
    if code != "": _emit(ctx, code + ";")


def _emit_ann_assign(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    target_val = node.get("target")
    rt = _str(node, "decl_type")
    if rt == "": rt = _str(node, "resolved_type")
    ct = cpp_signature_type(rt)
    value = node.get("value")

    name = ""
    is_attr = False
    if isinstance(target_val, str): name = target_val
    elif isinstance(target_val, dict):
        if _str(target_val, "kind") == "Attribute":
            is_attr = True
        else:
            name = _str(target_val, "id")
            if name == "": name = _str(target_val, "repr")

    if is_attr:
        lhs = _emit_expr(ctx, target_val)
        if value is not None: _emit(ctx, lhs + " = " + _emit_expr(ctx, value) + ";")
        return

    ctx.var_types[name] = rt
    if value is not None:
        _emit(ctx, ct + " " + name + " = " + _emit_expr(ctx, value) + ";")
    else:
        _emit(ctx, ct + " " + name + " = " + cpp_zero_value(rt) + ";")


def _emit_assign(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    target_single = node.get("target")
    value = node.get("value")
    if len(targets) == 0 and isinstance(target_single, dict): targets = [target_single]
    if len(targets) == 0: return

    val_code = _emit_expr(ctx, value)
    t = targets[0]
    if not isinstance(t, dict):
        _emit(ctx, "/* assign */ " + val_code + ";")
        return

    tk = _str(t, "kind")
    if tk == "Name" or tk == "NameTarget":
        name = _str(t, "id")
        if name == "": name = _str(t, "repr")
        declare = _bool(node, "declare")
        if name in ctx.var_types or not declare:
            _emit(ctx, name + " = " + val_code + ";")
        else:
            dt = _str(node, "decl_type")
            ctx.var_types[name] = dt
            if dt == "" or dt == "unknown":
                _emit(ctx, "auto " + name + " = " + val_code + ";")
            else:
                ct = cpp_signature_type(dt)
                _emit(ctx, ct + " " + name + " = " + val_code + ";")
        if _bool(node, "unused") and _bool(node, "declare"):
            _emit(ctx, "(void)" + name + ";")
    elif tk == "Attribute":
        _emit(ctx, _emit_expr(ctx, t) + " = " + val_code + ";")
    elif tk == "Subscript":
        _emit(ctx, _emit_subscript_store_target(ctx, t) + " = " + val_code + ";")
    elif tk == "Tuple":
        elts = _list(t, "elements")
        names = [_emit_expr(ctx, e) for e in elts]
        if all(name in ctx.var_types for name in names):
            tmp_name = _next_temp(ctx, "__tuple")
            _emit(ctx, "auto " + tmp_name + " = " + val_code + ";")
            for i, name in enumerate(names):
                _emit(ctx, name + " = ::std::get<" + str(i) + ">(" + tmp_name + ");")
        else:
            _emit(ctx, "auto [" + ", ".join(names) + "] = " + val_code + ";")


def _emit_aug_assign(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    target = _emit_expr(ctx, node.get("target"))
    value = _emit_expr(ctx, node.get("value"))
    op = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "Mod": "%"}.get(_str(node, "op"), "+")
    _emit(ctx, target + " " + op + "= " + value + ";")


def _emit_return(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if value is None: _emit(ctx, "return;")
    else: _emit(ctx, "return " + _emit_expr(ctx, value) + ";")


def _emit_if(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    test = _emit_condition_expr(ctx, node.get("test"))
    _emit(ctx, "if (" + test + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    orelse = _list(node, "orelse")
    if len(orelse) > 0:
        if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
            _emit(ctx, "} else ")
            ctx.lines[-1] = ctx.lines[-1].rstrip()
            _emit_if(ctx, orelse[0])
            return
        _emit(ctx, "} else {")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_while(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    test = _emit_condition_expr(ctx, node.get("test"))
    _emit(ctx, "while (" + test + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_for_core(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    iter_plan = node.get("iter_plan")
    target_plan = node.get("target_plan")
    if isinstance(iter_plan, dict):
        ip_kind = _str(iter_plan, "kind")
        t_name = _str(target_plan, "id") if isinstance(target_plan, dict) else "_"
        if t_name == "": t_name = "_"
        if t_name == "_" or (isinstance(target_plan, dict) and _bool(target_plan, "unused")):
            t_name = _next_temp(ctx, "__discard")
        if ip_kind in ("StaticRangeForPlan", "RuntimeIterForPlan"):
            if iter_plan.get("start") is not None or iter_plan.get("stop") is not None:
                start = _emit_expr(ctx, iter_plan.get("start")) if iter_plan.get("start") else "0"
                stop = _emit_expr(ctx, iter_plan.get("stop")) if iter_plan.get("stop") else "0"
                step = "1"
                target_type = _str(target_plan, "target_type") if isinstance(target_plan, dict) else ""
                step_node = iter_plan.get("step")
                neg = False
                if isinstance(step_node, dict) and _str(step_node, "kind") == "Constant":
                    sv = step_node.get("value")
                    if isinstance(sv, int): step = str(sv); neg = sv < 0
                elif step_node is not None: step = _emit_expr(ctx, step_node)
                cmp = " > " if neg else " < "
                decl = ""
                if t_name not in ctx.var_types:
                    decl = (cpp_signature_type(target_type) if target_type not in ("", "unknown") else "auto") + " "
                _emit(ctx, "for (" + decl + t_name + " = " + start + "; " + t_name + cmp + stop + "; " + t_name + " += " + step + ") {")
                ctx.indent_level += 1
                ctx.var_types[t_name] = target_type
                _emit_body(ctx, body)
                ctx.indent_level -= 1
                _emit(ctx, "}")
                return
            else:
                iter_expr = iter_plan.get("iter_expr")
                iter_code = _emit_expr(ctx, iter_expr) if iter_expr else "{}"
                iter_type = _effective_resolved_type(iter_expr)
                target_type = _str(target_plan, "target_type") if isinstance(target_plan, dict) else ""
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
                    ctx.var_types[t_name] = "str"
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
                        decl = (cpp_signature_type(target_type) if target_type not in ("", "unknown") else "auto") + " "
                    _emit(ctx, decl + t_name + " = " + entry_name + ".first;")
                    ctx.var_types[t_name] = target_type
                    _emit_body(ctx, body)
                    ctx.indent_level -= 1
                    _emit(ctx, "}")
                    return
                _emit(ctx, "for (auto " + t_name + " : " + iter_code + ") {")
                ctx.indent_level += 1
                ctx.var_types[t_name] = target_type
                _emit_body(ctx, body)
                ctx.indent_level -= 1
                _emit(ctx, "}")
                return
    _emit_fail(ctx, "unsupported_for", repr(node))


def _emit_function_def(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    _emit_function_def_impl(ctx, node)


def _closure_function_type(node: dict[str, JsonVal]) -> str:
    params = [cpp_signature_type(arg_type) for _, arg_type, _ in _function_param_meta(node)]
    ret = cpp_signature_type(_return_type(node))
    return "::std::function<" + ret + "(" + ", ".join(params) + ")>"


def _emit_closure_def(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    if name == "":
        return
    ctx.includes_needed.add("functional")
    saved = dict(ctx.var_types)
    saved_ret = ctx.current_return_type
    return_type = _return_type(node)
    ctx.current_return_type = return_type
    for arg_name, arg_type, _ in _function_param_meta(node):
        ctx.var_types[arg_name] = arg_type
    ctx.var_types[name] = _closure_function_type(node)
    params = [_param_decl_text(arg_type, arg_name, mutable) for arg_name, arg_type, mutable in _function_param_meta(node)]
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
    ctx.var_types[name] = _closure_function_type(node)
    ctx.current_return_type = saved_ret


def _emit_class_def(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    body = _list(node, "body")
    is_dc = _bool(node, "dataclass")
    ctx.class_names.add(name)

    fields: list[tuple[str, str]] = []
    ft = _dict(node, "field_types")
    if len(ft) > 0:
        for fn, fv in ft.items(): fields.append((fn, fv if isinstance(fv, str) else ""))
    else:
        for s in body:
            if isinstance(s, dict) and _str(s, "kind") == "AnnAssign" and is_dc:
                tv = s.get("target")
                tn = _str(tv, "id") if isinstance(tv, dict) else ""
                tr = _str(s, "decl_type")
                if tr == "": tr = _str(s, "resolved_type")
                if tn != "": fields.append((tn, tr))

    if ctx.emit_class_decls:
        _emit(ctx, "struct " + name + " {")
        ctx.indent_level += 1
        for fn, ftype in fields:
            _emit(ctx, cpp_signature_type(ftype) + " " + fn + ";")
        for s in body:
            if not isinstance(s, dict) or _str(s, "kind") not in ("FunctionDef", "ClosureDef"):
                continue
            decl = _function_signature(ctx, s, owner_name=name, declaration_only=True)
            if decl != "":
                _emit(ctx, decl + ";")
        ctx.indent_level -= 1
        _emit(ctx, "};")
        _emit_blank(ctx)

    for s in body:
        if isinstance(s, dict) and _str(s, "kind") in ("FunctionDef", "ClosureDef"):
            _emit_function_def_impl(ctx, s, owner_name=name)


def _emit_var_decl(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    rt = _str(node, "type")
    if rt == "": rt = _str(node, "resolved_type")
    ct = cpp_signature_type(rt)
    ctx.var_types[name] = rt
    _emit(ctx, ct + " " + name + " = " + cpp_zero_value(rt) + ";")


def _emit_swap(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    _emit(ctx, "std::swap(" + left + ", " + right + ");")


def _emit_try(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")
    if len(handlers) == 0 and len(finalbody) == 0:
        _emit_body(ctx, body)
        return
    _emit(ctx, "{")
    ctx.indent_level += 1
    if len(finalbody) > 0:
        finally_name = _next_temp(ctx, "__finally")
        _emit(ctx, "auto " + finally_name + " = py_make_scope_exit([&]() {")
        ctx.indent_level += 1
        _emit_body(ctx, finalbody)
        ctx.indent_level -= 1
        _emit(ctx, "});")
    if len(handlers) > 0:
        _emit(ctx, "try {")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "} catch (...) {")
        ctx.indent_level += 1
        h = handlers[0]
        if isinstance(h, dict):
            _emit_body(ctx, _list(h, "body"))
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_raise(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    exc = node.get("exc")
    if isinstance(exc, dict):
        bn = _str(exc, "builtin_name")
        rc = _str(exc, "runtime_call")
        if bn in ("RuntimeError", "ValueError", "TypeError") or rc == "std::runtime_error":
            ea = _list(exc, "args")
            if len(ea) >= 1: _emit(ctx, "throw std::runtime_error(" + _emit_expr(ctx, ea[0]) + ");")
            else: _emit(ctx, 'throw std::runtime_error("' + bn + '");')
        else:
            _emit(ctx, "throw " + _emit_expr(ctx, exc) + ";")
    else:
        _emit(ctx, "throw;")


def _emit_with(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    context_expr = _emit_expr(ctx, node.get("context_expr"))
    var_name = _str(node, "var_name")
    if var_name == "":
        var_name = _next_temp(ctx, "__with")
    finally_name = _next_temp(ctx, "__finally")
    _emit(ctx, "auto " + var_name + " = " + context_expr + ";")
    _emit(ctx, "{")
    ctx.indent_level += 1
    _emit(ctx, "auto " + finally_name + " = py_make_scope_exit([&]() {")
    ctx.indent_level += 1
    _emit(ctx, var_name + ".close();")
    ctx.indent_level -= 1
    _emit(ctx, "});")
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_function_def_impl(ctx: CppEmitContext, node: dict[str, JsonVal], owner_name: str = "") -> None:
    if _has_decorator(node, "extern"):
        return
    saved = dict(ctx.var_types)
    saved_ret = ctx.current_return_type
    return_type = _return_type(node)
    ctx.current_return_type = return_type
    for arg_name, arg_type, _ in _function_param_meta(node):
        ctx.var_types[arg_name] = arg_type
    signature = _function_signature(ctx, node, owner_name=owner_name, declaration_only=False)
    if signature == "":
        ctx.var_types = saved
        ctx.current_return_type = saved_ret
        return
    template_prefix = _function_template_prefix(node)
    if template_prefix != "":
        _emit(ctx, template_prefix)
    _emit(ctx, signature + " {")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)
    ctx.var_types = saved
    ctx.current_return_type = saved_ret


def _function_signature(
    ctx: CppEmitContext,
    node: dict[str, JsonVal],
    *,
    owner_name: str = "",
    declaration_only: bool,
) -> str:
    name = _str(node, "name")
    if name == "":
        return ""
    is_static = _has_decorator(node, "staticmethod")
    params = [_param_decl_text(arg_type, arg_name, mutable) for arg_name, arg_type, mutable in _function_param_meta(node)]
    if declaration_only and owner_name != "" and is_static:
        static_prefix = "static "
    else:
        static_prefix = ""
    if name == "__init__" and owner_name != "":
        prefix = owner_name if declaration_only else owner_name + "::" + owner_name
        return static_prefix + prefix + "(" + ", ".join(params) + ")"
    ret = cpp_signature_type(_return_type(node))
    qual_name = name
    if owner_name != "" and not declaration_only:
        qual_name = owner_name + "::" + name
    suffix = ""
    self_mutates = _function_self_mutates(node)
    if declaration_only and owner_name != "" and not is_static and not self_mutates:
        suffix = " const"
    if (not declaration_only) and owner_name != "" and not is_static and not self_mutates:
        suffix = " const"
    return static_prefix + ret + " " + qual_name + "(" + ", ".join(params) + ")" + suffix


def _function_template_prefix(node: dict[str, JsonVal]) -> str:
    params = _function_template_params(node)
    if len(params) == 0:
        return ""
    return "template <" + ", ".join("class " + name for name in params) + ">"


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


def _function_param_meta(node: dict[str, JsonVal]) -> list[tuple[str, str, bool]]:
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    arg_usage = _dict(node, "arg_usage")
    is_static = _has_decorator(node, "staticmethod")
    out: list[tuple[str, str, bool]] = []
    for arg in arg_order:
        arg_name = arg if isinstance(arg, str) else ""
        if arg_name == "":
            continue
        if arg_name == "self" and not is_static:
            continue
        arg_type = arg_types.get(arg_name, "")
        arg_type_str = arg_type if isinstance(arg_type, str) else "object"
        out.append((arg_name, arg_type_str, arg_usage.get(arg_name) == "reassigned"))
    return out


def _function_self_mutates(node: dict[str, JsonVal]) -> bool:
    if _bool(node, "mutates_self"):
        return True
    arg_usage = _dict(node, "arg_usage")
    return arg_usage.get("self") == "reassigned"


def _param_decl_text(resolved_type: str, name: str, mutable: bool) -> str:
    return cpp_param_decl(resolved_type, name, mutable=mutable)


def _return_type(node: dict[str, JsonVal]) -> str:
    return_type = _str(node, "return_type")
    if return_type == "":
        return_type = _str(node, "returns")
    if return_type == "":
        return_type = "None"
    return return_type


def _has_decorator(node: dict[str, JsonVal], name: str) -> bool:
    for d in _list(node, "decorators"):
        if isinstance(d, str) and d == name:
            return True
    return False


def _is_type_owner(ctx: CppEmitContext, owner_node: JsonVal) -> bool:
    if not isinstance(owner_node, dict):
        return False
    if _str(owner_node, "type_object_of") != "":
        return True
    owner_id = _str(owner_node, "id")
    return owner_id != "" and owner_id in ctx.class_names


def _emit_cast_expr(ctx: CppEmitContext, target_node: JsonVal, value_node: JsonVal) -> str:
    target_name = _node_type_mirror(target_node)
    if target_name == "":
        target_name = _effective_resolved_type(target_node)
    if target_name in ("", "unknown", "type", "callable") and isinstance(target_node, dict):
        target_name = _str(target_node, "id")
        if target_name == "":
            target_name = _str(target_node, "repr")
    value_expr = _emit_expr(ctx, value_node)
    value_type = _effective_resolved_type(value_node)
    storage_type = _expr_storage_type(ctx, value_node)
    value_kind = _str(value_node, "kind") if isinstance(value_node, dict) else ""
    if target_name == "":
        return value_expr
    if _optional_inner_type(storage_type) == target_name:
        return "(*(" + value_expr + "))"
    needs_runtime_cast = (
        (_needs_object_cast(storage_type) and storage_type != target_name)
        or (_needs_object_cast(value_type) and value_type != target_name)
    )
    storage_unknown_ref = value_kind in ("Name", "Attribute", "Subscript") and storage_type in ("", "unknown")
    if not needs_runtime_cast and value_type == target_name:
        if not (target_name in ctx.class_names and storage_unknown_ref):
            return value_expr
    if target_name in ctx.class_names and (needs_runtime_cast or storage_unknown_ref):
        return "(*(" + value_expr + ").as<" + target_name + ">())"
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
    lp = _dict(meta, "linked_program_v1")
    if module_id == "" and lp: module_id = _str(lp, "module_id")

    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "cpp" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

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

    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")

    # Collect imports and class names
    ctx.import_aliases = build_import_alias_map(meta)
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)
    for s in body:
        if isinstance(s, dict) and _str(s, "kind") == "ClassDef":
            class_name = _str(s, "name")
            ctx.class_names.add(class_name)
            ctx.class_field_types[class_name] = {
                k: v for k, v in _dict(s, "field_types").items() if isinstance(k, str) and isinstance(v, str)
            }
    ctx.class_symbol_fqcns = _build_class_symbol_fqcn_map(meta, module_id, ctx.class_names, ctx.class_type_ids)

    # Emit body
    for s in body: _emit_stmt(ctx, s)

    # Main guard
    if len(main_guard) > 0:
        _emit_blank(ctx)
        _emit(ctx, "void __pytra_main_guard() {")
        ctx.indent_level += 1
        for s in main_guard: _emit_stmt(ctx, s)
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # main() for entry
    if ctx.is_entry or len(main_guard) > 0:
        _emit_blank(ctx)
        _emit(ctx, "int main() {")
        ctx.indent_level += 1
        _emit(ctx, "__pytra_main_guard();")
        _emit(ctx, "return 0;")
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # Build header
    dep_ids = collect_cpp_dependency_module_ids(module_id, meta)

    header: list[str] = [
        "#include <cstdint>",
        "#include <string>",
        "#include <vector>",
        "#include <iostream>",
        "#include <stdexcept>",
        "#include <cmath>",
        '#include "core/py_runtime.h"',
    ]
    if "functional" in ctx.includes_needed:
        header.insert(6, "#include <functional>")

    if self_header != "":
        header.append('#include "' + self_header + '"')

    seen_includes: set[str] = set()
    for dep_id in dep_ids:
        if dep_id == "" or dep_id == module_id or dep_id == "pytra.core.py_runtime":
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
