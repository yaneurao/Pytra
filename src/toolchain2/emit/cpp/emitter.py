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

from toolchain2.emit.cpp.types import cpp_type, cpp_zero_value
from toolchain2.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_runtime_import_map, resolve_runtime_symbol_name,
)


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
    current_class: str = ""
    current_return_type: str = ""
    runtime_imports: dict[str, str] = field(default_factory=dict)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)


def _indent(ctx: CppEmitContext) -> str:
    return "    " * ctx.indent_level

def _emit(ctx: CppEmitContext, line: str) -> None:
    ctx.lines.append(_indent(ctx) + line)

def _emit_blank(ctx: CppEmitContext) -> None:
    ctx.lines.append("")


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


# ---------------------------------------------------------------------------
# Expression emission
# ---------------------------------------------------------------------------

def _emit_expr(ctx: CppEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return "/* nil */"
    kind = _str(node, "kind")

    if kind == "Constant": return _emit_constant(ctx, node)
    if kind == "Name": return _emit_name(ctx, node)
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
    if kind == "Unbox": return _emit_expr(ctx, node.get("value"))
    if kind == "Box": return _emit_expr(ctx, node.get("value"))
    if kind == "ObjStr": return "py_str(" + _emit_expr(ctx, node.get("value")) + ")"
    if kind == "ObjLen": return "py_len(" + _emit_expr(ctx, node.get("value")) + ")"
    if kind == "ObjBool": return "py_bool(" + _emit_expr(ctx, node.get("value")) + ")"
    return "/* unsupported: " + kind + " */"


def _emit_constant(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    val = node.get("value")
    if val is None: return "nullptr"
    if isinstance(val, bool): return "true" if val else "false"
    if isinstance(val, int):
        rt = _str(node, "resolved_type")
        if rt in ("float64", "float32", "float"): return str(float(val))
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
    return "std::string(" + "".join(out) + ")"


def _emit_name(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "": name = _str(node, "repr")
    if name == "True": return "true"
    if name == "False": return "false"
    if name == "None": return "nullptr"
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
    if isinstance(func, dict):
        fk = _str(func, "kind")
        if fk == "Attribute":
            owner = _emit_expr(ctx, func.get("value"))
            attr = _str(func, "attr")
            if attr == "append" and len(arg_strs) >= 1:
                return owner + ".push_back(" + arg_strs[0] + ")"
            return owner + "." + attr + "(" + ", ".join(arg_strs) + ")"
        if fk == "Name":
            fn = _str(func, "id")
            if fn == "": fn = _str(func, "repr")
            if fn in ("bytearray", "bytes"):
                if len(args) >= 1 and isinstance(args[0], dict):
                    a0_kind = _str(args[0], "kind")
                    a0_rt = _str(args[0], "resolved_type")
                    if a0_kind == "List":
                        elems = _list(args[0], "elements")
                        parts = ["uint8_t(" + _emit_expr(ctx, e) + ")" for e in elems]
                        return "std::vector<uint8_t>{" + ", ".join(parts) + "}"
                    if a0_rt in ("int64", "int32", "int", "uint8", "int8"):
                        return "std::vector<uint8_t>(" + arg_strs[0] + ")"
                if len(arg_strs) >= 1:
                    return "std::vector<uint8_t>(" + arg_strs[0] + ")"
                return "std::vector<uint8_t>{}"
            if fn in ctx.class_names: return fn + "(" + ", ".join(arg_strs) + ")"
            if fn in ctx.runtime_imports: return ctx.runtime_imports[fn] + "(" + ", ".join(arg_strs) + ")"
            if fn == "main": return "__pytra_main(" + ", ".join(arg_strs) + ")"
            return fn + "(" + ", ".join(arg_strs) + ")"
    return _emit_expr(ctx, func) + "(" + ", ".join(arg_strs) + ")"


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
        ct = cpp_type(rt)
        if len(arg_strs) >= 1: return "static_cast<" + ct + ">(" + arg_strs[0] + ")"
        return ct + "()"
    if rc in ("py_to_string", "str") and len(arg_strs) >= 1:
        return "std::to_string(" + arg_strs[0] + ")"
    if rc in ("bytearray_ctor", "bytes_ctor"):
        if len(args) >= 1 and isinstance(args[0], dict):
            a0_kind = _str(args[0], "kind")
            a0_rt = _str(args[0], "resolved_type")
            if a0_kind == "List":
                elems = _list(args[0], "elements")
                parts = ["uint8_t(" + _emit_expr(ctx, e) + ")" for e in elems]
                return "std::vector<uint8_t>{" + ", ".join(parts) + "}"
            if a0_rt in ("int64", "int32", "int", "uint8", "int8"):
                return "std::vector<uint8_t>(" + arg_strs[0] + ")"
        if len(arg_strs) >= 1:
            return "std::vector<uint8_t>(" + arg_strs[0] + ")"
        return "std::vector<uint8_t>{}"
    if rc in ("py_print", "py_len") and len(arg_strs) >= 1:
        return rc + "(" + ", ".join(arg_strs) + ")"
    if rc == "py_int_from_str" and len(arg_strs) >= 1:
        return "std::stoll(" + arg_strs[0] + ")"
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
            return "py_list_pop(" + owner + ")"
    if rc == "list.index" and method_owner != "" and len(arg_strs) >= 1:
        return "py_index(" + method_owner + ", " + arg_strs[0] + ")"
    if rc == "dict.get":
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            if len(arg_strs) >= 2: return "py_dict_get(" + owner + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
            if len(arg_strs) >= 1: return owner + "[" + arg_strs[0] + "]"
    if rc in ("py_write_text", "pathlib.write_text"):
        if isinstance(func, dict):
            owner = _emit_expr(ctx, func.get("value"))
            if len(arg_strs) >= 1: return "py_pathlib_write_text(" + owner + ", " + arg_strs[0] + ")"

    # Mapping resolution
    adapter = _str(node, "runtime_call_adapter_kind")
    resolved = resolve_runtime_call(rc, bn, adapter, ctx.mapping)
    if resolved != "": return resolved + "(" + ", ".join(call_arg_strs) + ")"
    fn = rc if rc != "" else bn
    if fn != "": return ctx.mapping.builtin_prefix + fn.replace(".", "_") + "(" + ", ".join(call_arg_strs) + ")"
    return "/* unknown builtin */"


def _emit_attribute(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    attr = _str(node, "attr")
    owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
    runtime_module_id = _str(node, "runtime_module_id")
    runtime_symbol = _str(node, "runtime_symbol")
    runtime_symbol_dispatch = _str(node, "runtime_symbol_dispatch")
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
    if owner_id == "math":
        if attr == "pi": return "M_PI"
        if attr == "e": return "M_E"
    return owner + "." + attr


def _emit_subscript(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    value = _emit_expr(ctx, node.get("value"))
    sl = node.get("slice")
    if isinstance(sl, dict) and _str(sl, "kind") == "Slice":
        return value + " /* slice */"
    idx = _emit_expr(ctx, sl)
    # Negative index
    if isinstance(sl, dict) and _str(sl, "kind") == "Constant":
        iv = sl.get("value")
        if isinstance(iv, int) and iv < 0:
            idx = value + ".size()" + str(iv)
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
    return "std::to_string(" + _emit_expr(ctx, node.get("value")) + ")"


def _emit_lambda(ctx: CppEmitContext, node: dict[str, JsonVal]) -> str:
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    body = node.get("body")
    params = []
    for a in arg_order:
        an = a if isinstance(a, str) else ""
        at = arg_types.get(an, "")
        at_str = at if isinstance(at, str) else ""
        params.append(cpp_type(at_str) + " " + an)
    return "[&](" + ", ".join(params) + ") { return " + _emit_expr(ctx, body) + "; }"


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_stmt(ctx: CppEmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict): return
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
    elif kind == "ClassDef": _emit_class_def(ctx, node)
    elif kind == "ImportFrom" or kind == "Import": pass
    elif kind == "Pass": _emit(ctx, "// pass")
    elif kind == "VarDecl": _emit_var_decl(ctx, node)
    elif kind == "Swap": _emit_swap(ctx, node)
    elif kind == "Try": _emit_try(ctx, node)
    elif kind == "Raise": _emit_raise(ctx, node)
    elif kind == "comment":
        t = _str(node, "text")
        if t != "": _emit(ctx, "// " + t)
    elif kind == "blank": _emit_blank(ctx)


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
    ct = cpp_type(rt)
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
                ct = cpp_type(dt)
                _emit(ctx, ct + " " + name + " = " + val_code + ";")
        if _bool(node, "unused") and _bool(node, "declare"):
            _emit(ctx, "(void)" + name + ";")
    elif tk == "Attribute":
        _emit(ctx, _emit_expr(ctx, t) + " = " + val_code + ";")
    elif tk == "Subscript":
        _emit(ctx, _emit_expr(ctx, t) + " = " + val_code + ";")
    elif tk == "Tuple":
        elts = _list(t, "elements")
        names = [_emit_expr(ctx, e) for e in elts]
        # C++ structured binding: auto [a, b] = ...
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
    test = _emit_expr(ctx, node.get("test"))
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
    test = _emit_expr(ctx, node.get("test"))
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
                    decl = (cpp_type(target_type) if target_type not in ("", "unknown") else "auto") + " "
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
                _emit(ctx, "for (auto " + t_name + " : " + iter_code + ") {")
                ctx.indent_level += 1
                ctx.var_types[t_name] = ""
                _emit_body(ctx, body)
                ctx.indent_level -= 1
                _emit(ctx, "}")
                return
    _emit(ctx, "// unsupported for")


def _emit_function_def(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    arg_types = _dict(node, "arg_types")
    arg_order = _list(node, "arg_order")
    return_type = _str(node, "return_type")
    body = _list(node, "body")
    for d in _list(node, "decorators"):
        if isinstance(d, str) and d == "extern": return

    ct_ret = cpp_type(return_type)
    if return_type == "None": ct_ret = "void"
    params: list[str] = []
    saved = dict(ctx.var_types)
    for a in arg_order:
        an = a if isinstance(a, str) else ""
        if an == "self": continue
        at = arg_types.get(an, "")
        at_str = at if isinstance(at, str) else ""
        params.append(cpp_type(at_str) + " " + an)
        ctx.var_types[an] = at_str

    saved_ret = ctx.current_return_type
    ctx.current_return_type = return_type
    _emit(ctx, ct_ret + " " + name + "(" + ", ".join(params) + ") {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit_blank(ctx)
    ctx.var_types = saved
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

    _emit(ctx, "struct " + name + " {")
    ctx.indent_level += 1
    for fn, ftype in fields: _emit(ctx, cpp_type(ftype) + " " + fn + ";")
    ctx.indent_level -= 1
    _emit(ctx, "};")
    _emit_blank(ctx)

    for s in body:
        if isinstance(s, dict) and _str(s, "kind") == "FunctionDef":
            if _str(s, "name") == "__init__": continue
            _emit_function_def(ctx, s)


def _emit_var_decl(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    rt = _str(node, "type")
    if rt == "": rt = _str(node, "resolved_type")
    ct = cpp_type(rt)
    ctx.var_types[name] = rt
    _emit(ctx, ct + " " + name + " = " + cpp_zero_value(rt) + ";")


def _emit_swap(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    left = _emit_expr(ctx, node.get("left"))
    right = _emit_expr(ctx, node.get("right"))
    _emit(ctx, "std::swap(" + left + ", " + right + ");")


def _emit_try(ctx: CppEmitContext, node: dict[str, JsonVal]) -> None:
    _emit(ctx, "try {")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    handlers = _list(node, "handlers")
    if len(handlers) > 0:
        _emit(ctx, "} catch (...) {")
        ctx.indent_level += 1
        h = handlers[0]
        if isinstance(h, dict): _emit_body(ctx, _list(h, "body"))
        ctx.indent_level -= 1
    _emit(ctx, "}")
    fin = _list(node, "finalbody")
    if len(fin) > 0: _emit_body(ctx, fin)


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


# ---------------------------------------------------------------------------
# Module emission
# ---------------------------------------------------------------------------

def emit_cpp_module(east3_doc: dict[str, JsonVal]) -> str:
    meta = _dict(east3_doc, "meta")
    module_id = ""
    emit_ctx_meta = _dict(meta, "emit_context")
    if emit_ctx_meta: module_id = _str(emit_ctx_meta, "module_id")
    lp = _dict(meta, "linked_program_v1")
    if module_id == "" and lp: module_id = _str(lp, "module_id")

    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "cpp" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    if should_skip_module(module_id, mapping): return ""

    ctx = CppEmitContext(
        module_id=module_id,
        is_entry=_bool(emit_ctx_meta, "is_entry") if emit_ctx_meta else False,
        mapping=mapping,
    )

    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")

    # Collect imports and class names
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)
    for s in body:
        if isinstance(s, dict) and _str(s, "kind") == "ClassDef":
            ctx.class_names.add(_str(s, "name"))

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
    header: list[str] = [
        "#include <cstdint>",
        "#include <string>",
        "#include <vector>",
        "#include <iostream>",
        "#include <stdexcept>",
        "#include <cmath>",
        "",
        "// Generated by toolchain2/emit/cpp",
        "",
    ]

    return "\n".join(header + ctx.lines) + "\n"
