"""EAST3 -> Nim source emitter.

Nim emitter は CommonRenderer + override 構成。
Nim 固有のノード（インデントブロック、proc/var/let、import 等）のみ override として実装する。

selfhost 対象。pytra.std.* のみ import 可。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.emit.nim.types import (
    nim_type, nim_zero_value, _safe_nim_ident, _split_generic_args,
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
    class_fields: dict[str, dict[str, str]] = field(default_factory=dict)
    class_methods: dict[str, set[str]] = field(default_factory=dict)
    class_static_methods: dict[str, set[str]] = field(default_factory=dict)
    class_property_methods: dict[str, set[str]] = field(default_factory=dict)
    enum_bases: dict[str, str] = field(default_factory=dict)
    enum_members: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    trait_names: set[str] = field(default_factory=set)
    current_class: str = ""
    current_base_class: str = ""
    exception_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    temp_counter: int = 0
    is_type_id_table: bool = False
    current_exc_var: str = ""
    vararg_functions: set[str] = field(default_factory=set)
    # Track declared variables so we can use `var` only on first assign
    declared_vars: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _indent(ctx: EmitContext) -> str:
    return "  " * ctx.indent_level


def _emit(ctx: EmitContext, line: str) -> None:
    ctx.lines.append(_indent(ctx) + line)


def _emit_raw(ctx: EmitContext, line: str) -> None:
    ctx.lines.append(line)


def _emit_blank(ctx: EmitContext) -> None:
    ctx.lines.append("")


def _next_temp(ctx: EmitContext, prefix: str) -> str:
    ctx.temp_counter += 1
    return prefix + "_" + str(ctx.temp_counter)


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


def _int(node: JsonVal, key: str) -> int:
    if isinstance(node, dict):
        value = node.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return 0


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


def _nim_name(ctx: EmitContext, name: str) -> str:
    """Return safe Nim identifier, applying renamed_symbols and self."""
    if name == "self":
        return "self"
    name = name.strip("() \t")
    renamed = ctx.renamed_symbols.get(name, "")
    if renamed != "":
        return _safe_nim_ident(renamed)
    return _safe_nim_ident(name)


def _nim_string(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\n", "\\n")
    return '"' + out + '"'


def _export_marker(name: str, *, top_level: bool) -> str:
    if not top_level:
        return ""
    if name.startswith("_"):
        return ""
    return "*"


def _is_super_call(node: JsonVal) -> bool:
    if not isinstance(node, dict) or _str(node, "kind") != "Call":
        return False
    func = node.get("func")
    return isinstance(func, dict) and _str(func, "kind") == "Name" and _str(func, "id") == "super"


def _is_exception_type_name(ctx: EmitContext, type_name: str) -> bool:
    if type_name in ctx.mapping.exception_types:
        return True
    base = ctx.class_bases.get(type_name, "")
    if base != "":
        return _is_exception_type_name(ctx, base)
    return False


def _decorators(node: dict[str, JsonVal]) -> list[str]:
    decorators: list[str] = []
    for value in _list(node, "decorators"):
        if isinstance(value, str):
            decorators.append(value)
    return decorators


def _is_trait_class(node: dict[str, JsonVal]) -> bool:
    return "trait" in _decorators(node)


def _implemented_traits(node: dict[str, JsonVal]) -> list[str]:
    out: list[str] = []
    for decorator in _decorators(node):
        if not decorator.startswith("implements(") or not decorator.endswith(")"):
            continue
        inner = decorator[len("implements("):-1].strip()
        if inner == "":
            continue
        for part in inner.split(","):
            name = part.strip()
            if name != "":
                out.append(name)
    return out


def _get_negative_int_literal(node: dict[str, JsonVal]) -> int | None:
    kind = _str(node, "kind")
    if kind == "Constant":
        v = node.get("value")
        if isinstance(v, int) and not isinstance(v, bool) and v < 0:
            return v
    if kind == "UnaryOp" and _str(node, "op") == "USub":
        operand = node.get("operand")
        if isinstance(operand, dict) and _str(operand, "kind") == "Constant":
            v = operand.get("value")
            if isinstance(v, int) and not isinstance(v, bool) and v > 0:
                return -v
    return None


def _render_type(ctx: EmitContext, resolved_type: str, *, for_return: bool = False) -> str:
    if resolved_type in ctx.class_names:
        return _nim_name(ctx, resolved_type)
    if resolved_type in ctx.trait_names:
        return _nim_name(ctx, resolved_type)
    return nim_type(resolved_type, for_return=for_return)


def _type_annotation(ctx: EmitContext, resolved_type: str, *, for_return: bool = False) -> str:
    if resolved_type == "" or resolved_type == "unknown":
        return ""
    tt = _render_type(ctx, resolved_type, for_return=for_return)
    if tt == "" or (tt == "void" and not for_return):
        return ""
    return ": " + tt


def _return_type_annotation(ctx: EmitContext, return_type: str) -> str:
    if return_type == "" or return_type == "unknown" or return_type == "None":
        return ""
    tt = _render_type(ctx, return_type, for_return=True)
    if tt == "" or tt == "void":
        return ""
    return ": " + tt


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
    if kind == "BinOp":
        return _emit_binop(ctx, node)
    if kind == "UnaryOp":
        return _emit_unaryop(ctx, node)
    if kind == "Compare":
        return _emit_compare(ctx, node)
    if kind == "BoolOp":
        return _emit_boolop(ctx, node)
    if kind == "Subscript":
        return _emit_subscript(ctx, node)
    if kind == "IfExp":
        return _emit_ifexp(ctx, node)
    if kind == "List":
        return _emit_list_literal(ctx, node)
    if kind == "Dict":
        return _emit_dict_literal(ctx, node)
    if kind == "Set":
        return _emit_set_literal(ctx, node)
    if kind == "Tuple":
        return _emit_tuple_literal(ctx, node)
    if kind == "ListComp":
        return _emit_listcomp(ctx, node)
    if kind == "JoinedStr":
        return _emit_fstring(ctx, node)
    if kind == "Lambda" or kind == "ClosureDef":
        return _emit_lambda(ctx, node)
    if kind == "Starred":
        inner = node.get("value")
        return _emit_expr(ctx, inner)
    return "nil"


def _emit_constant(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _nim_string(value)
    if isinstance(value, float):
        s = str(value)
        if "." not in s and "e" not in s and "E" not in s:
            s = s + ".0"
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
    return _nim_name(ctx, name)


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr = _str(node, "attr")

    # self.field -> self.field
    if isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
        return "self." + _safe_nim_ident(attr)

    # Module constant access (math.pi, sys.argv)
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

    owner = _emit_expr(ctx, owner_node)
    return owner + "." + _safe_nim_ident(attr)


def _emit_subscript(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    slice_node = node.get("slice")

    # Slice
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "0"
        upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else owner + ".len"
        return owner + "[" + lower_code + " ..< " + upper_code + "]"

    # dict -> [] access
    is_dict = owner_rt.startswith("dict[") or owner_rt == "dict"
    if is_dict and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        return owner + "[" + slice_code + "]"

    # list/string -> handle negative indices
    is_array_like = (
        owner_rt.startswith("list[") or owner_rt in ("list", "str", "string", "bytes", "bytearray")
    )
    if is_array_like and isinstance(slice_node, dict):
        neg_val = _get_negative_int_literal(slice_node)
        if neg_val is not None:
            return owner + "[" + owner + ".len + (" + str(neg_val) + ")]"

    slice_code = _emit_expr(ctx, slice_node)
    return owner + "[" + slice_code + "]"


def _emit_binop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    right_node = node.get("right")
    left = _emit_expr(ctx, left_node)
    right = _emit_expr(ctx, right_node)
    op = _str(node, "op")

    left_rt = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
    right_rt = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""

    # str + str -> string concatenation
    if op == "Add" and (left_rt == "str" or right_rt == "str"):
        return "(" + left + " & " + right + ")"

    # list + list -> concat
    if op == "Add" and (left_rt.startswith("list[") or right_rt.startswith("list[")):
        return "(" + left + " & " + right + ")"

    # str * int / list * int -> repeat
    if op == "Mult":
        if left_rt == "str" or left_rt.startswith("list["):
            return left + ".repeat(" + right + ")"
        if right_rt == "str" or right_rt.startswith("list["):
            return right + ".repeat(" + left + ")"

    # Pow
    if op == "Pow":
        return "pow(" + left + ", " + right + ")"

    op_map: dict[str, str] = {
        "Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
        "FloorDiv": "div", "Mod": "mod",
        "BitAnd": "and", "BitOr": "or", "BitXor": "xor",
        "LShift": "shl", "RShift": "shr",
    }
    op_text = op_map.get(op, op)
    return "(" + left + " " + op_text + " " + right + ")"


def _emit_unaryop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    op_map: dict[str, str] = {
        "USub": "-", "UAdd": "+", "Not": "not ", "Invert": "not ",
    }
    op_text = op_map.get(op, op)
    return "(" + op_text + operand + ")"


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return left
    parts: list[str] = []
    current_left = left
    for idx, comparator in enumerate(comparators):
        op_val = ops[idx] if idx < len(ops) else None
        op_name = op_val if isinstance(op_val, str) else ""
        right = _emit_expr(ctx, comparator)
        if op_name == "In":
            parts.append(current_left + " in " + right)
        elif op_name == "NotIn":
            parts.append(current_left + " notin " + right)
        elif op_name == "Is":
            parts.append("(" + current_left + " == " + right + ")")
        elif op_name == "IsNot":
            parts.append("(" + current_left + " != " + right + ")")
        else:
            cmp_map: dict[str, str] = {
                "Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=",
                "Gt": ">", "GtE": ">=",
            }
            cmp_text = cmp_map.get(op_name, "==")
            parts.append("(" + current_left + " " + cmp_text + " " + right + ")")
        current_left = right
    if len(parts) == 1:
        return parts[0]
    return "(" + " and ".join(parts) + ")"


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    op = _str(node, "op")
    op_text = "and" if op == "And" else "or"
    rendered = [_emit_expr(ctx, v) for v in values]
    return "(" + (" " + op_text + " ").join(rendered) + ")"


def _emit_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test = _emit_expr(ctx, node.get("test"))
    body = _emit_expr(ctx, node.get("body"))
    orelse = _emit_expr(ctx, node.get("orelse"))
    return "(if " + test + ": " + body + " else: " + orelse + ")"


def _emit_list_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    if len(elements) == 0:
        rt = _str(node, "resolved_type")
        if rt.startswith("list[") and rt.endswith("]"):
            inner = rt[5:-1]
            return "newSeq[" + _render_type(ctx, inner) + "]()"
        return "@[]"
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    return "@[" + ", ".join(elem_strs) + "]"


def _emit_dict_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    entries = _list(node, "entries")
    rt = _str(node, "resolved_type")
    k_type = "string"
    v_type = "PyObj"
    if rt.startswith("dict[") and rt.endswith("]"):
        parts = _split_generic_args(rt[5:-1])
        if len(parts) == 2:
            k_type = _render_type(ctx, parts[0])
            v_type = _render_type(ctx, parts[1])

    if len(entries) == 0:
        return "initTable[" + k_type + ", " + v_type + "]()"

    pairs: list[str] = []
    if len(entries) > 0:
        for entry in entries:
            if isinstance(entry, dict):
                kc = _emit_expr(ctx, entry.get("key"))
                vc = _emit_expr(ctx, entry.get("value"))
                pairs.append(kc + ": " + vc)
    else:
        keys = _list(node, "keys")
        values = _list(node, "values")
        for idx, key in enumerate(keys):
            kc = _emit_expr(ctx, key)
            val_node = values[idx] if idx < len(values) else None
            vc = _emit_expr(ctx, val_node) if val_node is not None else "nil"
            pairs.append(kc + ": " + vc)

    return "{" + ", ".join(pairs) + "}.toTable"


def _emit_set_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    if len(elements) == 0:
        rt = _str(node, "resolved_type")
        if rt.startswith("set[") and rt.endswith("]"):
            inner = rt[4:-1]
            return "initHashSet[" + _render_type(ctx, inner) + "]()"
        return "initHashSet[PyObj]()"
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    return "[" + ", ".join(elem_strs) + "].toHashSet"


def _emit_tuple_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    elem_strs = [_emit_expr(ctx, e) for e in elements]
    return "(" + ", ".join(elem_strs) + ")"


def _emit_listcomp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = node.get("elt")
    generators = _list(node, "generators")
    if len(generators) == 0:
        return "@[]"
    gen = generators[0]
    if not isinstance(gen, dict):
        return "@[]"
    target = gen.get("target")
    iter_node = gen.get("iter")
    target_code = _emit_expr(ctx, target)
    iter_code = _emit_expr(ctx, iter_node)
    elt_code = _emit_expr(ctx, elt)

    # Handle filter (if clause)
    ifs = _list(gen, "ifs")
    if len(ifs) > 0:
        filter_parts: list[str] = []
        for f in ifs:
            filter_parts.append(_emit_expr(ctx, f))
        filter_code = " and ".join(filter_parts)
        return "collect(newSeq[auto](), for " + target_code + " in " + iter_code + ": (if " + filter_code + ": " + elt_code + "))"

    return "collect(newSeq[auto](), for " + target_code + " in " + iter_code + ": " + elt_code + ")"


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
                parts.append(_nim_string(raw_val))
            continue
        if vk == "FormattedValue":
            inner = v.get("value")
            expr_code = _emit_expr(ctx, inner)
            fmt_spec = _str(v, "format_spec")
            if fmt_spec != "":
                parts.append("py_fmt(" + expr_code + ", " + _nim_string(fmt_spec) + ")")
            else:
                parts.append("$(" + expr_code + ")")
            continue
        expr_code = _emit_expr(ctx, v)
        parts.append("$(" + expr_code + ")")
    if len(parts) == 0:
        return '""'
    if len(parts) == 1:
        return parts[0]
    return " & ".join(parts)


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    args = _list(node, "args")
    arg_types = _list(node, "arg_types")
    body_node = node.get("body")

    params: list[str] = []
    for idx, arg in enumerate(args):
        arg_name = ""
        if isinstance(arg, dict):
            arg_name = _str(arg, "arg")
            if arg_name == "":
                arg_name = _str(arg, "id")
        elif isinstance(arg, str):
            arg_name = arg
        if arg_name == "":
            arg_name = "a" + str(idx)
        safe_name = _safe_nim_ident(arg_name)
        ann = ""
        if idx < len(arg_types):
            at = arg_types[idx]
            if isinstance(at, str) and at != "" and at != "unknown":
                ann = ": " + _render_type(ctx, at)
        params.append(safe_name + ann)

    return_type = _str(node, "return_type")
    ret_ann = ""
    if return_type != "" and return_type != "unknown" and return_type != "None":
        ret_ann = ": " + _render_type(ctx, return_type, for_return=True)

    body_code = _emit_expr(ctx, body_node)
    return "proc(" + ", ".join(params) + ")" + ret_ann + " = " + body_code


# ---------------------------------------------------------------------------
# Call rendering
# ---------------------------------------------------------------------------

def _resolve_runtime_call_name(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    runtime_call = _str(node, "runtime_call")
    builtin_name = _str(node, "builtin_name")
    adapter_kind = _str(node, "runtime_call_adapter_kind")
    if runtime_call == "" and builtin_name == "":
        resolved_rc = _str(node, "resolved_runtime_call")
        if resolved_rc != "":
            runtime_call = resolved_rc
    resolved = resolve_runtime_call(runtime_call, builtin_name, adapter_kind, ctx.mapping)
    return resolved


def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    func_node = node.get("func")
    args = _list(node, "args")
    builtin_name = _str(node, "builtin_name")

    # Check for runtime call resolution
    runtime_name = _resolve_runtime_call_name(ctx, node)

    # isinstance
    semantic_tag = _str(node, "semantic_tag")
    if semantic_tag == "builtin.isinstance" or runtime_name == "py_isinstance":
        return _emit_isinstance(ctx, node, args)

    # Special markers from mapping
    if runtime_name == "__CAST__":
        return _emit_cast(ctx, node, args)
    if runtime_name == "__LIST_APPEND__":
        return _emit_method_on_owner(ctx, node, "add", args)
    if runtime_name == "__LIST_POP__":
        return _emit_list_pop(ctx, node, args)
    if runtime_name == "__LIST_CLEAR__":
        return _emit_method_on_owner(ctx, node, "setLen(0", args)
    if runtime_name == "__LIST_INDEX__":
        return _emit_method_on_owner(ctx, node, "find", args)
    if runtime_name == "__DICT_GET__":
        return _emit_dict_get(ctx, node, args)
    if runtime_name == "__DICT_ITEMS__":
        return _emit_method_on_owner(ctx, node, "pairs", args)
    if runtime_name == "__DICT_KEYS__":
        return _emit_method_on_owner(ctx, node, "keys", args)
    if runtime_name == "__DICT_VALUES__":
        return _emit_method_on_owner(ctx, node, "values", args)
    if runtime_name == "__SET_ADD__":
        return _emit_method_on_owner(ctx, node, "incl", args)
    if runtime_name == "__SET_DISCARD__":
        return _emit_method_on_owner(ctx, node, "excl", args)
    if runtime_name == "__SET_REMOVE__":
        return _emit_method_on_owner(ctx, node, "excl", args)
    if runtime_name == "__PANIC__":
        msg_code = _emit_expr(ctx, args[0]) if len(args) > 0 else '""'
        return "raise newException(ValueError, " + msg_code + ")"
    if runtime_name == "__LIST_CTOR__":
        return _emit_list_ctor(ctx, node, args)
    if runtime_name == "__TUPLE_CTOR__":
        return _emit_tuple_ctor(ctx, args)
    if runtime_name == "__SET_CTOR__":
        return _emit_set_ctor(ctx, node, args)
    if runtime_name == "__MAKE_BYTES__":
        if len(args) > 0:
            return "newSeq[uint8](" + _emit_expr(ctx, args[0]) + ")"
        return "newSeq[uint8]()"

    # Resolved runtime name -> direct call
    if runtime_name != "":
        arg_strs = [_emit_expr(ctx, a) for a in args]
        if builtin_name == "print":
            rendered_args: list[str] = []
            for arg_code in arg_strs:
                rendered_args.append("py_to_string(" + arg_code + ")")
            return runtime_name + "(" + ", ".join(rendered_args) + ")"
        return runtime_name + "(" + ", ".join(arg_strs) + ")"

    # Method call on object (attribute call)
    if isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
        return _emit_method_call(ctx, func_node, args)

    # Constructor call (ClassName(...))
    if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
        fn_name = _str(func_node, "id")
        if fn_name in ctx.class_names:
            return _emit_constructor(ctx, fn_name, args)

    # Regular function call
    callee = _emit_expr(ctx, func_node)
    arg_strs = [_emit_expr(ctx, a) for a in args]
    return callee + "(" + ", ".join(arg_strs) + ")"


def _emit_isinstance(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    if len(args) < 2:
        return "false"
    obj = _emit_expr(ctx, args[0])
    type_node = args[1]
    if isinstance(type_node, dict):
        type_name = _str(type_node, "id")
        if type_name == "":
            type_name = _str(type_node, "repr")
        if type_name != "":
            return "(" + obj + " of " + _render_type(ctx, type_name) + ")"
    return "false"


def _emit_cast(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    if len(args) == 0:
        return "nil"
    cast_to = _str(node, "resolved_type")
    if cast_to == "":
        cast_to = _str(node, "cast_to")
    arg_code = _emit_expr(ctx, args[0])
    if cast_to == "" or cast_to == "unknown":
        return arg_code
    target_type = _render_type(ctx, cast_to)
    return target_type + "(" + arg_code + ")"


def _emit_method_on_owner(ctx: EmitContext, node: dict[str, JsonVal], method: str, args: list[JsonVal]) -> str:
    func_node = node.get("func")
    owner_code = ""
    if isinstance(func_node, dict):
        owner_node = func_node.get("value")
        if isinstance(owner_node, dict):
            owner_code = _emit_expr(ctx, owner_node)
    if owner_code == "":
        owner_code = "self"
    arg_strs = [_emit_expr(ctx, a) for a in args]
    if method.endswith("(0"):
        return owner_code + "." + method + ")"
    return owner_code + "." + method + "(" + ", ".join(arg_strs) + ")"


def _emit_list_pop(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    func_node = node.get("func")
    owner_code = ""
    if isinstance(func_node, dict):
        owner_node = func_node.get("value")
        if isinstance(owner_node, dict):
            owner_code = _emit_expr(ctx, owner_node)
    if owner_code == "":
        owner_code = "self"
    if len(args) > 0:
        idx_code = _emit_expr(ctx, args[0])
        return owner_code + ".pop(" + idx_code + ")"
    return owner_code + ".pop()"


def _emit_dict_get(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    func_node = node.get("func")
    owner_code = ""
    if isinstance(func_node, dict):
        owner_node = func_node.get("value")
        if isinstance(owner_node, dict):
            owner_code = _emit_expr(ctx, owner_node)
    if owner_code == "":
        owner_code = "self"
    if len(args) == 0:
        return owner_code
    key_code = _emit_expr(ctx, args[0])
    if len(args) > 1:
        default_code = _emit_expr(ctx, args[1])
        return owner_code + ".getOrDefault(" + key_code + ", " + default_code + ")"
    return owner_code + ".getOrDefault(" + key_code + ")"


def _emit_list_ctor(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    if len(args) > 0:
        return "@[" + ", ".join(_emit_expr(ctx, a) for a in args) + "]"
    rt = _str(node, "resolved_type")
    if rt.startswith("list[") and rt.endswith("]"):
        inner = rt[5:-1]
        return "newSeq[" + _render_type(ctx, inner) + "]()"
    return "@[]"


def _emit_tuple_ctor(ctx: EmitContext, args: list[JsonVal]) -> str:
    return "(" + ", ".join(_emit_expr(ctx, a) for a in args) + ")"


def _emit_set_ctor(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    if len(args) > 0:
        return "[" + ", ".join(_emit_expr(ctx, a) for a in args) + "].toHashSet"
    rt = _str(node, "resolved_type")
    if rt.startswith("set[") and rt.endswith("]"):
        inner = rt[4:-1]
        return "initHashSet[" + _render_type(ctx, inner) + "]()"
    return "initHashSet[PyObj]()"


def _emit_method_call(ctx: EmitContext, func_node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    owner_node = func_node.get("value")
    attr = _str(func_node, "attr")
    owner_code = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    arg_strs = [_emit_expr(ctx, a) for a in args]

    # str methods
    if owner_rt == "str":
        str_method_map: dict[str, str] = {
            "strip": "py_str_strip", "lstrip": "py_str_lstrip", "rstrip": "py_str_rstrip",
            "startswith": "py_str_startswith", "endswith": "py_str_endswith",
            "replace": "py_str_replace", "find": "py_str_find", "rfind": "py_str_rfind",
            "split": "py_str_split", "join": "py_str_join",
            "upper": "py_str_upper", "lower": "py_str_lower",
            "count": "py_str_count", "index": "py_str_index",
            "isdigit": "py_str_isdigit", "isalpha": "py_str_isalpha",
            "isalnum": "py_str_isalnum", "isspace": "py_str_isspace",
        }
        mapped = str_method_map.get(attr, "")
        if mapped != "":
            return mapped + "(" + owner_code + ", " + ", ".join(arg_strs) + ")" if len(arg_strs) > 0 else mapped + "(" + owner_code + ")"

    # list methods
    if owner_rt.startswith("list[") or owner_rt in ("list", "bytes", "bytearray"):
        list_method_map: dict[str, str] = {
            "append": "add", "extend": "add", "pop": "pop",
            "clear": "setLen", "reverse": "reverse", "sort": "sort",
            "insert": "insert", "remove": "delete", "index": "find",
        }
        mapped = list_method_map.get(attr, "")
        if mapped != "":
            if mapped == "setLen":
                return owner_code + ".setLen(0)"
            return owner_code + "." + mapped + "(" + ", ".join(arg_strs) + ")"

    # dict methods
    if owner_rt.startswith("dict[") or owner_rt == "dict":
        if attr == "get":
            if len(arg_strs) > 1:
                return owner_code + ".getOrDefault(" + ", ".join(arg_strs) + ")"
            if len(arg_strs) == 1:
                return owner_code + ".getOrDefault(" + arg_strs[0] + ")"
        if attr == "keys":
            return "toSeq(" + owner_code + ".keys)"
        if attr == "values":
            return "toSeq(" + owner_code + ".values)"
        if attr == "items":
            return "toSeq(" + owner_code + ".pairs)"
        if attr == "pop":
            if len(arg_strs) > 0:
                temp = _next_temp(ctx, "pop")
                return "(let " + temp + " = " + owner_code + "[" + arg_strs[0] + "]; " + owner_code + ".del(" + arg_strs[0] + "); " + temp + ")"
        if attr == "update":
            if len(arg_strs) > 0:
                return "(for k, v in " + arg_strs[0] + ": " + owner_code + "[k] = v)"
        if attr == "setdefault":
            if len(arg_strs) == 2:
                return owner_code + ".mgetOrPut(" + arg_strs[0] + ", " + arg_strs[1] + ")"
            if len(arg_strs) == 1:
                return owner_code + ".mgetOrPut(" + arg_strs[0] + ", nil)"

    # set methods
    if owner_rt.startswith("set[") or owner_rt == "set":
        if attr == "add":
            return owner_code + ".incl(" + ", ".join(arg_strs) + ")"
        if attr == "discard":
            return owner_code + ".excl(" + ", ".join(arg_strs) + ")"
        if attr == "remove":
            return owner_code + ".excl(" + ", ".join(arg_strs) + ")"
        if attr == "clear":
            return owner_code + ".clear()"

    # super() call
    if attr == "__init__" and _is_super_call(owner_node):
        base = ctx.current_base_class
        if base == "":
            base = ctx.class_bases.get(ctx.current_class, "")
        if base != "":
            return _safe_nim_ident(base) + ".init(" + ", ".join(["self"] + arg_strs) + ")"
        return "discard"

    # General method call
    return owner_code + "." + _safe_nim_ident(attr) + "(" + ", ".join(arg_strs) + ")"


def _emit_constructor(ctx: EmitContext, class_name: str, args: list[JsonVal]) -> str:
    safe_name = _nim_name(ctx, class_name)
    arg_strs = [_emit_expr(ctx, a) for a in args]

    # Exception classes
    if _is_exception_type_name(ctx, class_name):
        msg = arg_strs[0] if len(arg_strs) > 0 else _nim_string(class_name)
        return "newException(ValueError, " + msg + ")"

    return safe_name + "(" + ", ".join(arg_strs) + ")"


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_body(ctx: EmitContext, body: list[JsonVal]) -> None:
    if len(body) == 0:
        _emit(ctx, "discard")
        return
    for stmt in body:
        _emit_stmt(ctx, stmt)


def _emit_stmt(ctx: EmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        return
    kind = _str(node, "kind")

    # Trivia: leading comments/blanks
    leading_trivia = _list(node, "leading_trivia")
    for trivia in leading_trivia:
        if isinstance(trivia, dict):
            trivia_kind = _str(trivia, "kind")
            if trivia_kind == "comment":
                text = _str(trivia, "text")
                # Check for Pytra::pass / Pytra::cpp directives
                if text.startswith("Pytra::pass ") or text.startswith("Pytra::pass: "):
                    directive = text.split(" ", 1)[1] if " " in text else ""
                    _emit(ctx, directive)
                    continue
                if text.startswith("Pytra::cpp ") or text.startswith("Pytra::cpp: "):
                    continue
                _emit(ctx, "# " + text)
            elif trivia_kind == "blank":
                _emit_blank(ctx)

    if kind == "Expr":
        _emit_expr_stmt(ctx, node)
    elif kind == "Return":
        _emit_return_stmt(ctx, node)
    elif kind == "Assign":
        _emit_assign_stmt(ctx, node)
    elif kind == "AnnAssign":
        _emit_ann_assign_stmt(ctx, node)
    elif kind == "AugAssign":
        _emit_aug_assign_stmt(ctx, node)
    elif kind == "If":
        _emit_if_stmt(ctx, node)
    elif kind == "While":
        _emit_while_stmt(ctx, node)
    elif kind == "For":
        _emit_for_stmt(ctx, node)
    elif kind == "ForRange":
        _emit_for_range_stmt(ctx, node)
    elif kind == "FunctionDef" or kind == "ClosureDef":
        _emit_function_def(ctx, node)
    elif kind == "ClassDef":
        _emit_class_def(ctx, node)
    elif kind == "Pass":
        _emit(ctx, "discard")
    elif kind == "Break":
        _emit(ctx, "break")
    elif kind == "Continue":
        _emit(ctx, "continue")
    elif kind == "Raise":
        _emit_raise_stmt(ctx, node)
    elif kind == "Try":
        _emit_try_stmt(ctx, node)
    elif kind == "Import" or kind == "ImportFrom":
        pass  # handled in module header
    elif kind == "Swap":
        _emit_swap_stmt(ctx, node)
    elif kind == "Delete":
        _emit_delete_stmt(ctx, node)
    elif kind == "comment":
        text = _str(node, "text")
        if text != "":
            _emit(ctx, "# " + text)
    elif kind == "blank":
        _emit_blank(ctx)
    elif kind == "With":
        _emit_with_stmt(ctx, node)


def _emit_expr_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if isinstance(value, dict):
        code = _emit_expr(ctx, value)
        # Docstrings
        if _str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
            doc = value.get("value")
            if isinstance(doc, str):
                _emit(ctx, "## " + doc.replace("\n", "\n## "))
                return
        _emit(ctx, code)


def _emit_return_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if isinstance(value, dict):
        code = _emit_expr(ctx, value)
        _emit(ctx, "return " + code)
    else:
        _emit(ctx, "return")


def _emit_assign_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    value_code = _emit_expr(ctx, value)

    # Tuple assignment
    if isinstance(target, dict) and _str(target, "kind") == "Tuple":
        elements = _list(target, "elements")
        if len(elements) > 0:
            temp = _next_temp(ctx, "tup")
            _emit(ctx, "let " + temp + " = " + value_code)
            for idx, elem in enumerate(elements):
                elem_name = ""
                if isinstance(elem, dict):
                    elem_name = _str(elem, "id")
                    if elem_name == "":
                        elem_name = _str(elem, "repr")
                if elem_name != "":
                    safe = _nim_name(ctx, elem_name)
                    if safe in ctx.declared_vars:
                        _emit(ctx, safe + " = " + temp + "[" + str(idx) + "]")
                    else:
                        _emit(ctx, "var " + safe + " = " + temp + "[" + str(idx) + "]")
                        ctx.declared_vars.add(safe)
            return

    # Attribute assignment (self.x = ...)
    if isinstance(target, dict) and _str(target, "kind") == "Attribute":
        target_code = _emit_expr(ctx, target)
        _emit(ctx, target_code + " = " + value_code)
        return

    # Subscript assignment (a[i] = ...)
    if isinstance(target, dict) and _str(target, "kind") == "Subscript":
        target_code = _emit_expr(ctx, target)
        _emit(ctx, target_code + " = " + value_code)
        return

    # Simple name assignment
    target_name = ""
    if isinstance(target, dict):
        target_name = _str(target, "id")
        if target_name == "":
            target_name = _str(target, "repr")
    elif isinstance(target, str):
        target_name = target
    if target_name == "":
        _emit(ctx, value_code)
        return

    safe = _nim_name(ctx, target_name)
    if safe in ctx.declared_vars:
        _emit(ctx, safe + " = " + value_code)
    else:
        rt = _str(target, "resolved_type") if isinstance(target, dict) else ""
        ann = _type_annotation(ctx, rt)
        _emit(ctx, "var " + safe + ann + " = " + value_code)
        ctx.declared_vars.add(safe)
        if rt != "":
            ctx.var_types[safe] = rt


def _emit_ann_assign_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    decl_type = _str(node, "decl_type")
    if decl_type == "":
        decl_type = _str(node, "annotation")
    if decl_type == "":
        decl_type = _str(node, "resolved_type")

    target_name = ""
    if isinstance(target, dict):
        target_name = _str(target, "id")
        if target_name == "":
            target_name = _str(target, "repr")
    elif isinstance(target, str):
        target_name = target

    if target_name == "":
        return

    safe = _nim_name(ctx, target_name)
    ann = _type_annotation(ctx, decl_type)

    if isinstance(value, dict):
        value_code = _emit_expr(ctx, value)
        if safe in ctx.declared_vars:
            _emit(ctx, safe + " = " + value_code)
        else:
            _emit(ctx, "var " + safe + ann + " = " + value_code)
            ctx.declared_vars.add(safe)
    else:
        # Declaration without value
        zero = nim_zero_value(decl_type)
        if safe not in ctx.declared_vars:
            _emit(ctx, "var " + safe + ann + " = " + zero)
            ctx.declared_vars.add(safe)

    if decl_type != "":
        ctx.var_types[safe] = decl_type


def _emit_aug_assign_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    op = _str(node, "op")
    target_code = _emit_expr(ctx, target)
    value_code = _emit_expr(ctx, value)

    aug_map: dict[str, str] = {
        "Add": "+=", "Sub": "-=", "Mult": "*=", "Div": "/=",
        "FloorDiv": "div=", "Mod": "mod=",
        "BitAnd": "and=", "BitOr": "or=", "BitXor": "xor=",
        "LShift": "shl=", "RShift": "shr=",
    }

    target_rt = ""
    if isinstance(target, dict):
        target_rt = _str(target, "resolved_type")

    # str += str -> &=
    if op == "Add" and target_rt == "str":
        _emit(ctx, target_code + " &= " + value_code)
        return

    # list += list -> add
    if op == "Add" and (target_rt.startswith("list[") or target_rt in ("list", "bytes", "bytearray")):
        _emit(ctx, target_code + ".add(" + value_code + ")")
        return

    op_text = aug_map.get(op, "+=")
    # Nim doesn't have div=, mod= etc as combined operators; split them
    if op_text in ("div=", "mod=", "and=", "or=", "xor=", "shl=", "shr="):
        base_op = op_text[:-1]
        _emit(ctx, target_code + " = " + target_code + " " + base_op + " " + value_code)
    else:
        _emit(ctx, target_code + " " + op_text + " " + value_code)


def _emit_if_stmt(ctx: EmitContext, node: dict[str, JsonVal], *, is_elif: bool = False) -> None:
    test = _emit_expr(ctx, node.get("test"))
    keyword = "elif" if is_elif else "if"
    _emit(ctx, keyword + " " + test + ":")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    orelse = _list(node, "orelse")
    if len(orelse) > 0:
        if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
            _emit_if_stmt(ctx, orelse[0], is_elif=True)
            return
        _emit(ctx, "else:")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1


def _emit_while_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    test = _emit_expr(ctx, node.get("test"))
    _emit(ctx, "while " + test + ":")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1


def _emit_for_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    iter_node = node.get("iter")
    target_code = _emit_expr(ctx, target)
    iter_code = _emit_expr(ctx, iter_node)

    # Mark loop var as declared
    if isinstance(target, dict):
        tname = _str(target, "id")
        if tname != "":
            ctx.declared_vars.add(_nim_name(ctx, tname))

    _emit(ctx, "for " + target_code + " in " + iter_code + ":")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1


def _emit_for_range_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    target_code = _emit_expr(ctx, target)

    if isinstance(target, dict):
        tname = _str(target, "id")
        if tname != "":
            ctx.declared_vars.add(_nim_name(ctx, tname))

    start_node = node.get("start")
    stop_node = node.get("stop")
    step_node = node.get("step")

    start_code = _emit_expr(ctx, start_node) if isinstance(start_node, dict) else "0"
    stop_code = _emit_expr(ctx, stop_node) if isinstance(stop_node, dict) else "0"

    # Step
    step_val = None
    if isinstance(step_node, dict):
        step_val = _get_negative_int_literal(step_node)
        if step_val is None:
            v = step_node.get("value")
            if isinstance(v, int) and not isinstance(v, bool):
                step_val = v

    if step_val is not None and step_val == -1:
        _emit(ctx, "for " + target_code + " in countdown(" + start_code + " - 1, " + stop_code + "):")
    elif step_val is not None and step_val < 0:
        _emit(ctx, "for " + target_code + " in countdown(" + start_code + " - 1, " + stop_code + ", " + str(-step_val) + "):")
    elif step_val is not None and step_val == 1:
        _emit(ctx, "for " + target_code + " in " + start_code + " ..< " + stop_code + ":")
    elif step_val is not None and step_val > 1:
        _emit(ctx, "for " + target_code + " in countup(" + start_code + ", " + stop_code + " - 1, " + str(step_val) + "):")
    elif isinstance(step_node, dict):
        step_code = _emit_expr(ctx, step_node)
        _emit(ctx, "for " + target_code + " in py_range(" + start_code + ", " + stop_code + ", " + step_code + "):")
    else:
        _emit(ctx, "for " + target_code + " in " + start_code + " ..< " + stop_code + ":")

    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1


def _emit_raise_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    exc_node = node.get("exc")
    if isinstance(exc_node, dict):
        exc_code = _emit_expr(ctx, exc_node)
        # If it's already a newException(...) expression, use directly
        if exc_code.startswith("newException("):
            _emit(ctx, "raise " + exc_code)
        else:
            _emit(ctx, "raise " + exc_code)
    else:
        # Bare raise (re-raise)
        if ctx.current_exc_var != "":
            _emit(ctx, "raise " + ctx.current_exc_var)
        else:
            _emit(ctx, "raise")


def _emit_try_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    body = _list(node, "body")
    handlers = _list(node, "handlers")
    finalbody = _list(node, "finalbody")

    _emit(ctx, "try:")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1

    for handler in handlers:
        if not isinstance(handler, dict):
            continue
        exc_type = _str(handler, "type")
        exc_name = _str(handler, "name")

        if exc_type != "":
            nim_exc_type = _render_type(ctx, exc_type)
            # Normalize to CatchableError for common exception types
            if nim_exc_type.startswith("ref "):
                nim_exc_type = nim_exc_type[4:]
            if exc_name != "":
                _emit(ctx, "except " + nim_exc_type + " as " + _safe_nim_ident(exc_name) + ":")
                saved_exc = ctx.current_exc_var
                ctx.current_exc_var = _safe_nim_ident(exc_name)
                ctx.declared_vars.add(_safe_nim_ident(exc_name))
                ctx.indent_level += 1
                _emit_body(ctx, _list(handler, "body"))
                ctx.indent_level -= 1
                ctx.current_exc_var = saved_exc
            else:
                _emit(ctx, "except " + nim_exc_type + ":")
                ctx.indent_level += 1
                _emit_body(ctx, _list(handler, "body"))
                ctx.indent_level -= 1
        else:
            if exc_name != "":
                _emit(ctx, "except CatchableError as " + _safe_nim_ident(exc_name) + ":")
                saved_exc = ctx.current_exc_var
                ctx.current_exc_var = _safe_nim_ident(exc_name)
                ctx.declared_vars.add(_safe_nim_ident(exc_name))
                ctx.indent_level += 1
                _emit_body(ctx, _list(handler, "body"))
                ctx.indent_level -= 1
                ctx.current_exc_var = saved_exc
            else:
                _emit(ctx, "except CatchableError:")
                ctx.indent_level += 1
                _emit_body(ctx, _list(handler, "body"))
                ctx.indent_level -= 1

    if len(finalbody) > 0:
        _emit(ctx, "finally:")
        ctx.indent_level += 1
        _emit_body(ctx, finalbody)
        ctx.indent_level -= 1


def _emit_swap_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    left = node.get("left")
    right = node.get("right")
    left_code = _emit_expr(ctx, left)
    right_code = _emit_expr(ctx, right)
    _emit(ctx, "swap(" + left_code + ", " + right_code + ")")


def _emit_delete_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    for target in targets:
        if isinstance(target, dict) and _str(target, "kind") == "Subscript":
            owner = target.get("value")
            slice_node = target.get("slice")
            owner_code = _emit_expr(ctx, owner)
            key_code = _emit_expr(ctx, slice_node)
            owner_rt = _str(owner, "resolved_type") if isinstance(owner, dict) else ""
            if owner_rt.startswith("dict[") or owner_rt == "dict":
                _emit(ctx, owner_code + ".del(" + key_code + ")")
            else:
                _emit(ctx, owner_code + ".delete(" + key_code + ")")


def _emit_with_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    # Use defer style for with statements
    items = _list(node, "items")
    for item in items:
        if not isinstance(item, dict):
            continue
        context_expr = item.get("context_expr")
        optional_vars = item.get("optional_vars")
        ctx_code = _emit_expr(ctx, context_expr)
        if isinstance(optional_vars, dict):
            var_name = _str(optional_vars, "id")
            if var_name != "":
                safe = _nim_name(ctx, var_name)
                _emit(ctx, "var " + safe + " = " + ctx_code)
                ctx.declared_vars.add(safe)
                _emit(ctx, "defer: " + safe + ".close()")
        else:
            temp = _next_temp(ctx, "ctx")
            _emit(ctx, "var " + temp + " = " + ctx_code)
            _emit(ctx, "defer: " + temp + ".close()")
    _emit_body(ctx, _list(node, "body"))


# ---------------------------------------------------------------------------
# Function definition
# ---------------------------------------------------------------------------

def _get_arg_order(node: dict[str, JsonVal]) -> list[str]:
    """Get function argument names in order from EAST node."""
    # Try arg_order first (EAST2/EAST3 format)
    arg_order = _list(node, "arg_order")
    if len(arg_order) > 0:
        result: list[str] = []
        for item in arg_order:
            if isinstance(item, str):
                result.append(item)
        return result
    # Fallback: args list (linked format)
    args = _list(node, "args")
    result2: list[str] = []
    for arg in args:
        if isinstance(arg, dict):
            name = _str(arg, "arg")
            if name == "":
                name = _str(arg, "id")
            if name != "":
                result2.append(name)
        elif isinstance(arg, str):
            result2.append(arg)
    return result2


def _get_arg_type(node: dict[str, JsonVal], arg_name: str) -> str:
    """Get type for a specific argument from EAST node."""
    # Try arg_types dict first (EAST format: {name: type_str})
    arg_types_dict = _dict(node, "arg_types")
    if len(arg_types_dict) > 0:
        val = arg_types_dict.get(arg_name)
        if isinstance(val, str):
            return val
        return ""
    # Fallback: arg_types list
    arg_types_list = _list(node, "arg_types")
    arg_order = _get_arg_order(node)
    idx = 0
    for name in arg_order:
        if name == arg_name:
            if idx < len(arg_types_list):
                at = arg_types_list[idx]
                if isinstance(at, str):
                    return at
            return ""
        idx += 1
    return ""


def _get_arg_default(node: dict[str, JsonVal], arg_name: str) -> JsonVal:
    """Get default value for a specific argument from EAST node."""
    # Try arg_defaults dict (EAST format: {name: default_node})
    defaults_dict = _dict(node, "arg_defaults")
    if len(defaults_dict) > 0:
        val = defaults_dict.get(arg_name)
        return val
    # Fallback: args list with default field
    args = _list(node, "args")
    for arg in args:
        if isinstance(arg, dict):
            name = _str(arg, "arg")
            if name == "":
                name = _str(arg, "id")
            if name == arg_name:
                return arg.get("default")
    return None


def _emit_function_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    arg_names = _get_arg_order(node)
    return_type = _str(node, "return_type")
    body = _list(node, "body")
    decs = _decorators(node)

    is_static = "staticmethod" in decs
    is_property = "property" in decs
    is_method = ctx.current_class != "" and not is_static

    safe_name = _nim_name(ctx, name)

    # Build parameter list
    params: list[str] = []
    skip_first = False
    if is_method and len(arg_names) > 0:
        if arg_names[0] == "self":
            skip_first = True
            params.append("self: " + _nim_name(ctx, ctx.current_class))

    start_idx = 1 if skip_first else 0
    idx = start_idx
    while idx < len(arg_names):
        arg_name = arg_names[idx]
        safe_arg = _safe_nim_ident(arg_name)
        at = _get_arg_type(node, arg_name)
        ann = ""
        if at != "" and at != "unknown":
            ann = ": " + _render_type(ctx, at)
        default_val = _get_arg_default(node, arg_name)
        if isinstance(default_val, dict):
            default_code = _emit_expr(ctx, default_val)
            params.append(safe_arg + ann + " = " + default_code)
        else:
            params.append(safe_arg + ann)
        idx += 1

    ret_ann = _return_type_annotation(ctx, return_type)

    # Emit function header
    if is_method:
        _emit(ctx, "proc " + safe_name + "*(" + ", ".join(params) + ")" + ret_ann + " =")
    else:
        export_marker = _export_marker(safe_name, top_level=ctx.indent_level == 0)
        _emit(ctx, "proc " + safe_name + export_marker + "(" + ", ".join(params) + ")" + ret_ann + " =")

    # Save context and emit body
    saved_vars = ctx.var_types.copy()
    saved_ret = ctx.current_return_type
    saved_declared = ctx.declared_vars.copy()
    ctx.current_return_type = return_type

    # Add parameters to declared vars
    for arg_name in arg_names:
        if arg_name != "self":
            ctx.declared_vars.add(_safe_nim_ident(arg_name))

    ctx.indent_level += 1
    if len(body) == 0:
        _emit(ctx, "discard")
    else:
        _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit_blank(ctx)

    ctx.var_types = saved_vars
    ctx.current_return_type = saved_ret
    ctx.declared_vars = saved_declared


# ---------------------------------------------------------------------------
# Class definition
# ---------------------------------------------------------------------------

def _emit_class_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    base = _str(node, "base")
    body = _list(node, "body")
    is_dataclass = _bool(node, "dataclass")

    ctx.class_names.add(name)
    if base != "":
        ctx.class_bases[name] = base

    # Check for trait
    if _is_trait_class(node):
        ctx.trait_names.add(name)
        _emit_trait_def(ctx, node, name)
        return

    # Check for enum
    enum_base = ctx.enum_bases.get(name, "")
    if enum_base in ("Enum", "IntEnum", "IntFlag"):
        _emit_enum_class(ctx, node, name)
        return

    safe_name = _nim_name(ctx, name)

    # Collect fields
    fields = _collect_class_fields(ctx, node)

    # Emit type definition
    base_clause = ""
    if base != "" and not _is_exception_type_name(ctx, name):
        base_clause = " of " + _nim_name(ctx, base)
    elif _is_exception_type_name(ctx, name):
        base_clause = " of CatchableError"
    else:
        base_clause = " of RootObj"

    _emit(ctx, "type " + safe_name + "* = ref object" + base_clause)
    ctx.indent_level += 1
    if len(fields) > 0:
        for fname, ftype in fields:
            _emit(ctx, _safe_nim_ident(fname) + "*: " + _render_type(ctx, ftype))
    else:
        _emit(ctx, "discard")
    ctx.indent_level -= 1
    _emit_blank(ctx)

    # Save class context
    saved_class = ctx.current_class
    saved_base = ctx.current_base_class
    ctx.current_class = name
    ctx.current_base_class = base

    # Emit constructor if needed
    has_init = False
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef") and _str(stmt, "name") == "__init__":
            has_init = True
            break

    if has_init:
        for stmt in body:
            if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef") and _str(stmt, "name") == "__init__":
                _emit_init_as_constructor(ctx, stmt, name, fields)
                break

    # Emit methods (skip __init__)
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        if sk in ("FunctionDef", "ClosureDef"):
            mname = _str(stmt, "name")
            if mname == "__init__":
                continue
            # __repr__ -> $ operator
            if mname == "__repr__" or mname == "__str__":
                _emit_repr_method(ctx, stmt, name)
                continue
            _emit_function_def(ctx, stmt)
        elif sk in ("comment", "blank"):
            _emit_stmt(ctx, stmt)

    if not has_init and (is_dataclass or len(fields) > 0):
        _emit_default_constructor(ctx, name, fields)

    ctx.current_class = saved_class
    ctx.current_base_class = saved_base


def _collect_class_fields(ctx: EmitContext, node: dict[str, JsonVal]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    field_types = _dict(node, "field_types")
    if len(field_types) > 0:
        for fname, ftype in field_types.items():
            if isinstance(fname, str) and isinstance(ftype, str) and fname != "":
                fields.append((fname, ftype))
        return fields
    body = _list(node, "body")
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _str(stmt, "kind") == "AnnAssign":
            target_val = stmt.get("target")
            ft_name = ""
            if isinstance(target_val, dict):
                ft_name = _str(target_val, "id")
            elif isinstance(target_val, str):
                ft_name = target_val
            frt = _str(stmt, "decl_type")
            if frt == "":
                frt = _str(stmt, "resolved_type")
            if ft_name != "" and frt != "":
                fields.append((ft_name, frt))
    return fields


def _emit_init_as_constructor(
    ctx: EmitContext,
    node: dict[str, JsonVal],
    class_name: str,
    fields: list[tuple[str, str]],
) -> None:
    """Emit __init__ as a proc that creates and returns a new object."""
    arg_names = _get_arg_order(node)
    body = _list(node, "body")
    safe_name = _nim_name(ctx, class_name)

    # Build parameter list (skip self)
    params: list[str] = []
    start_idx = 0
    if len(arg_names) > 0 and arg_names[0] == "self":
        start_idx = 1

    idx = start_idx
    while idx < len(arg_names):
        an = arg_names[idx]
        safe_arg = _safe_nim_ident(an)
        at = _get_arg_type(node, an)
        ann = ""
        if at != "" and at != "unknown":
            ann = ": " + _render_type(ctx, at)
        default_val = _get_arg_default(node, an)
        if isinstance(default_val, dict):
            default_code = _emit_expr(ctx, default_val)
            params.append(safe_arg + ann + " = " + default_code)
        else:
            params.append(safe_arg + ann)
        idx += 1

    _emit(ctx, "proc init" + safe_name + "*(" + ", ".join(params) + "): " + safe_name + " =")

    saved_vars = ctx.var_types.copy()
    saved_ret = ctx.current_return_type
    saved_declared = ctx.declared_vars.copy()
    ctx.current_return_type = class_name

    # Mark params as declared
    for an in arg_names:
        if an != "self":
            ctx.declared_vars.add(_safe_nim_ident(an))

    ctx.indent_level += 1
    _emit(ctx, "var self = " + safe_name + "()")
    ctx.declared_vars.add("self")

    # Emit body
    for stmt in body:
        _emit_stmt(ctx, stmt)

    _emit(ctx, "return self")
    ctx.indent_level -= 1
    _emit_blank(ctx)

    ctx.var_types = saved_vars
    ctx.current_return_type = saved_ret
    ctx.declared_vars = saved_declared


def _emit_default_constructor(
    ctx: EmitContext,
    class_name: str,
    fields: list[tuple[str, str]],
) -> None:
    safe_name = _nim_name(ctx, class_name)
    params: list[str] = []
    for fname, ftype in fields:
        params.append(_safe_nim_ident(fname) + ": " + _render_type(ctx, ftype) + " = " + nim_zero_value(ftype))

    _emit(ctx, "proc init" + safe_name + "*(" + ", ".join(params) + "): " + safe_name + " =")
    ctx.indent_level += 1
    _emit(ctx, "var self = " + safe_name + "()")
    for fname, _ in fields:
        safe_f = _safe_nim_ident(fname)
        _emit(ctx, "self." + safe_f + " = " + safe_f)
    _emit(ctx, "return self")
    ctx.indent_level -= 1
    _emit_blank(ctx)


def _emit_repr_method(ctx: EmitContext, node: dict[str, JsonVal], class_name: str) -> None:
    body = _list(node, "body")
    safe_class = _nim_name(ctx, class_name)
    _emit(ctx, "proc `$`*(self: " + safe_class + "): string =")
    saved_vars = ctx.var_types.copy()
    saved_ret = ctx.current_return_type
    saved_declared = ctx.declared_vars.copy()
    ctx.current_return_type = "str"
    ctx.declared_vars.add("self")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit_blank(ctx)
    ctx.var_types = saved_vars
    ctx.current_return_type = saved_ret
    ctx.declared_vars = saved_declared


def _emit_trait_def(ctx: EmitContext, node: dict[str, JsonVal], name: str) -> None:
    safe_name = _nim_name(ctx, name)
    body = _list(node, "body")

    # Emit as abstract base type (concept-like)
    _emit(ctx, "type " + safe_name + "* = ref object of RootObj")
    _emit_blank(ctx)

    saved_class = ctx.current_class
    ctx.current_class = name
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef"):
            _emit_function_def(ctx, stmt)
    ctx.current_class = saved_class


def _emit_enum_class(ctx: EmitContext, node: dict[str, JsonVal], name: str) -> None:
    body = _list(node, "body")
    safe_name = _nim_name(ctx, name)
    enum_base = ctx.enum_bases.get(name, "")

    if enum_base == "IntEnum" or enum_base == "IntFlag":
        # Emit as const block
        _emit(ctx, "type " + safe_name + "* = int64")
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            sk = _str(stmt, "kind")
            if sk in ("AnnAssign", "Assign"):
                target = stmt.get("target")
                value = stmt.get("value")
                member_name = ""
                if isinstance(target, dict):
                    member_name = _str(target, "id")
                elif isinstance(target, str):
                    member_name = target
                if member_name != "" and isinstance(value, dict):
                    val_code = _emit_expr(ctx, value)
                    _emit(ctx, "const " + _safe_nim_ident(member_name) + "*: " + safe_name + " = " + val_code)
    else:
        # String enum
        _emit(ctx, "type " + safe_name + "* = string")
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            sk = _str(stmt, "kind")
            if sk in ("AnnAssign", "Assign"):
                target = stmt.get("target")
                value = stmt.get("value")
                member_name = ""
                if isinstance(target, dict):
                    member_name = _str(target, "id")
                elif isinstance(target, str):
                    member_name = target
                if member_name != "" and isinstance(value, dict):
                    val_code = _emit_expr(ctx, value)
                    _emit(ctx, "const " + _safe_nim_ident(member_name) + "*: " + safe_name + " = " + val_code)
    _emit_blank(ctx)


# ---------------------------------------------------------------------------
# Module-level emission
# ---------------------------------------------------------------------------

def _collect_module_class_info(ctx: EmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        if sk in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            vararg_name = _str(stmt, "vararg_name")
            if fn_name != "" and vararg_name != "":
                ctx.vararg_functions.add(fn_name)
        if sk == "ClassDef":
            class_name = _str(stmt, "name")
            ctx.class_names.add(class_name)
            base = _str(stmt, "base")
            if base != "":
                ctx.class_bases[class_name] = base
            if base in ("Enum", "IntEnum", "IntFlag"):
                ctx.enum_bases[class_name] = base
            if _is_trait_class(stmt):
                ctx.trait_names.add(class_name)
            field_types = _dict(stmt, "field_types")
            class_fields: dict[str, str] = {}
            for fname, ftype in field_types.items():
                if isinstance(fname, str) and isinstance(ftype, str):
                    class_fields[fname] = ftype
            ctx.class_fields[class_name] = class_fields


def _emit_nim_imports(ctx: EmitContext) -> None:
    """Emit Nim standard library imports needed by the generated code."""
    _emit(ctx, "import std/tables")
    _emit(ctx, "import std/sets")
    _emit(ctx, "import std/sequtils")
    _emit(ctx, "import std/strutils")
    _emit(ctx, "import std/sugar")
    _emit(ctx, "import py_runtime")
    _emit_blank(ctx)


def _emit_module_imports(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Emit import statements for user modules."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind == "ImportFrom":
            module_id = _str(stmt, "module")
            if module_id == "":
                continue
            if should_skip_module(module_id, ctx.mapping):
                continue
            # Relative module import
            rel_module = module_id
            if rel_module.startswith("pytra."):
                rel_module = rel_module[len("pytra."):]
            nim_module = rel_module.replace(".", "/")
            _emit(ctx, "import " + nim_module)
        elif kind == "Import":
            names = _list(stmt, "names")
            for name_entry in names:
                if not isinstance(name_entry, dict):
                    continue
                mod_name = _str(name_entry, "name")
                if mod_name == "" or should_skip_module(mod_name, ctx.mapping):
                    continue
                nim_module = mod_name.replace(".", "/")
                _emit(ctx, "import " + nim_module)


def emit_nim_module(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a complete Nim source file from an EAST3 document.

    Args:
        east3_doc: linked EAST3 JSON dict with meta.linked_program_v1.

    Returns:
        Nim source code string, or empty string if module should be skipped.
    """
    meta = _dict(east3_doc, "meta")
    module_id = ""

    emit_ctx_meta = _dict(meta, "emit_context")
    if len(emit_ctx_meta) > 0:
        module_id = _str(emit_ctx_meta, "module_id")
    if module_id == "":
        module_id = _str(meta, "module_id")
    lp = _dict(meta, "linked_program_v1")
    if module_id == "" and len(lp) > 0:
        module_id = _str(lp, "module_id")

    if module_id != "":
        expand_cross_module_defaults([(module_id, east3_doc)])

    # Load runtime mapping
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "nim" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)

    # Skip runtime modules
    if should_skip_module(module_id, mapping):
        return ""

    # Load renamed symbols
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
        is_entry=_bool(emit_ctx_meta, "is_entry") if len(emit_ctx_meta) > 0 else False,
        mapping=mapping,
        renamed_symbols=renamed_symbols,
        is_type_id_table=is_type_id_table,
    )

    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")

    # Collect type info from linked_program_v1
    if len(lp) > 0:
        type_info_table = _dict(lp, "type_info_table_v1")
        for fqcn, info in type_info_table.items():
            if not isinstance(fqcn, str) or not isinstance(info, dict):
                continue
            type_id_val = info.get("id")
            if isinstance(type_id_val, int):
                ctx.exception_type_ids[fqcn] = type_id_val
                ctx.class_type_ids[fqcn] = type_id_val

    ctx.import_alias_modules = build_import_alias_map(meta)
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)

    # First pass: collect class info
    _collect_module_class_info(ctx, body)

    # Emit standard imports
    _emit_nim_imports(ctx)

    # Emit user module imports
    _emit_module_imports(ctx, body)

    # Emit module body
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("ImportFrom", "Import"):
            continue
        _emit_stmt(ctx, stmt)

    # Emit main guard
    if len(main_guard) > 0:
        _emit_blank(ctx)
        _emit(ctx, "# main")
        _emit(ctx, "when isMainModule:")
        ctx.indent_level += 1
        _emit_body(ctx, main_guard)
        ctx.indent_level -= 1

    output = "\n".join(ctx.lines).rstrip() + "\n"
    return output
