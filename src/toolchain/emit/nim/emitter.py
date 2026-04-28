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

from toolchain.emit.nim.types import (
    nim_type, nim_zero_value, _safe_nim_ident, _split_generic_args,
    is_general_union_type, union_options, nim_union_type_name,
)
from toolchain.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping,
    should_skip_module, build_import_alias_map, build_runtime_import_map,
)
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.link.expand_defaults import expand_cross_module_defaults


def _emit_discard(ctx: "EmitContext") -> None:
    _emit(ctx, "discard")


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
    storage_var_types: dict[str, str] = field(default_factory=dict)
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
    class_static_attrs: dict[str, dict[str, JsonVal]] = field(default_factory=dict)
    enum_bases: dict[str, str] = field(default_factory=dict)
    enum_members: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    trait_names: set[str] = field(default_factory=set)
    class_traits: dict[str, list[str]] = field(default_factory=dict)
    current_class: str = ""
    current_base_class: str = ""
    exception_type_ids: dict[str, int] = field(default_factory=dict)
    class_type_ids: dict[str, int] = field(default_factory=dict)
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    temp_counter: int = 0
    loop_depth: int = 0
    root_rel_prefix: str = ""
    is_type_id_table: bool = False
    current_exc_var: str = ""
    vararg_functions: set[str] = field(default_factory=set)
    pass_directive_block: bool = False
    # Track declared variables so we can use `var` only on first assign
    declared_vars: set[str] = field(default_factory=set)
    general_unions: list[str] = field(default_factory=list)
    function_arg_types: dict[str, list[str]] = field(default_factory=dict)
    function_return_types: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _indent(ctx: EmitContext) -> str:
    return "  " * ctx.indent_level


def _emit(ctx: EmitContext, line: str) -> None:
    lines = line.splitlines()
    if len(lines) == 0:
        ctx.lines.append(_indent(ctx))
        return
    for part in lines:
        ctx.lines.append(_indent(ctx) + part)


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


def _strip_tuple_name(name: str) -> str:
    start = 0
    end = len(name)
    while start < end and name[start] in ("(", ")", " ", "\t"):
        start += 1
    while end > start and name[end - 1] in ("(", ")", " ", "\t"):
        end -= 1
    return name[start:end]


def _last_dot_part(value: str) -> str:
    idx = value.rfind(".")
    if idx < 0:
        return value
    return value[idx + 1:]


def _before_last_dot(value: str) -> str:
    idx = value.rfind(".")
    if idx < 0:
        return value
    return value[:idx]


def _starts_with_nested_type(value: str) -> bool:
    return (
        value.startswith("list[")
        or value.startswith("dict[")
        or value.startswith("set[")
        or value.startswith("tuple[")
        or value.startswith("deque[")
        or value.startswith("callable[")
        or value.startswith("multi_return[")
    )


def _mapped_target_type(ctx: EmitContext, type_name: str) -> str:
    if type_name == "":
        return ""
    return ctx.mapping.types.get(type_name, type_name)


def _is_nim_byte_seq_type(ctx: "EmitContext", type_name: str) -> bool:
    if type_name in ("bytes", "bytearray"):
        return True
    mapped_bytes = _mapped_target_type(ctx, "bytes")
    mapped_bytearray = _mapped_target_type(ctx, "bytearray")
    return type_name == mapped_bytes or type_name == mapped_bytearray


def _native_module_name(ctx: EmitContext, module_name: str) -> str:
    native_module = ctx.mapping.module_native_files.get(module_name, "")
    if native_module != "":
        return _before_last_dot(native_module)
    if "." not in module_name:
        for runtime_module_id in ctx.mapping.module_native_files:
            if _last_dot_part(runtime_module_id) == module_name:
                mapped_name = ctx.mapping.module_native_files.get(runtime_module_id, "")
                if mapped_name != "":
                    return _before_last_dot(mapped_name)
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


def _as_dict(value: JsonVal) -> dict[str, JsonVal]:
    if isinstance(value, dict):
        return value
    return {}


def _str_at(values: list[str], idx: int) -> str:
    return values[idx]


def _json_at(values: list[JsonVal], idx: int) -> JsonVal:
    return values[idx]


def _copy_str_dict(src: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in src.items():
        out[key] = value
    return out


def _copy_str_set(src: set[str]) -> set[str]:
    out: set[str] = set()
    for value in src:
        out.add(value)
    return out


def _nim_name(ctx: EmitContext, name: str) -> str:
    """Return safe Nim identifier, applying renamed_symbols and self."""
    if name == "self":
        return "self"
    cleaned = _strip_tuple_name(name)
    renamed = ctx.renamed_symbols.get(cleaned, "")
    if renamed != "":
        return _safe_nim_ident(renamed)
    return _safe_nim_ident(cleaned)


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


def _nim_exception_type_name(ctx: EmitContext, type_name: str) -> str:
    exc_type = _render_type(ctx, type_name)
    if exc_type.startswith("ref "):
        exc_type = exc_type[4:]
    if exc_type == "IndexError":
        return "py_runtime.IndexError"
    return exc_type


def _decorators(node: dict[str, JsonVal]) -> list[str]:
    decorators: list[str] = []
    for value in _list(node, "decorators"):
        if isinstance(value, str):
            decorators.append(value)
    return decorators


def _is_trait_class(node: dict[str, JsonVal]) -> bool:
    for decorator in _decorators(node):
        if decorator == "trait":
            return True
    return False


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


def _trait_matches(ctx: EmitContext, trait_name: str, expected_name: str) -> bool:
    if trait_name == expected_name:
        return True
    base = ctx.class_bases.get(trait_name, "")
    while base != "":
        if base == expected_name:
            return True
        base = ctx.class_bases.get(base, "")
    return False


def _class_implements_trait(ctx: EmitContext, class_name: str, expected_name: str) -> bool:
    for trait_name in ctx.class_traits.get(class_name, []):
        if _trait_matches(ctx, trait_name, expected_name):
            return True
    return False


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


def _get_static_int_literal(node: dict[str, JsonVal], missing: int) -> int:
    kind = _str(node, "kind")
    if kind == "Constant":
        v = node.get("value")
        if isinstance(v, int) and not isinstance(v, bool):
            return v
    if kind == "UnaryOp" and _str(node, "op") == "USub":
        operand = node.get("operand")
        if isinstance(operand, dict) and _str(operand, "kind") == "Constant":
            v = operand.get("value")
            if isinstance(v, int) and not isinstance(v, bool):
                return -v
    return missing


def _render_type(ctx: EmitContext, resolved_type: str, *, for_return: bool = False) -> str:
    rt = _strip_tuple_name(resolved_type)
    if is_general_union_type(rt):
        return nim_union_type_name(rt)
    mapped_type = _mapped_target_type(ctx, rt)
    if mapped_type != rt:
        return mapped_type
    if rt in ctx.class_names:
        return _nim_name(ctx, rt)
    if rt in ctx.trait_names:
        return _nim_name(ctx, rt)
    return nim_type(rt, for_return=for_return)


def _type_annotation(ctx: EmitContext, resolved_type: str, *, for_return: bool = False) -> str:
    if resolved_type == "" or resolved_type == "unknown":
        return ""
    if _should_infer_local_type(resolved_type):
        return ""
    tt = _render_type(ctx, resolved_type, for_return=for_return)
    if tt == "" or (tt == "void" and not for_return):
        return ""
    return ": " + tt


def _return_type_annotation(ctx: EmitContext, return_type: str) -> str:
    if return_type == "" or return_type == "unknown" or return_type == "None":
        return ""
    if return_type == "auto":
        return ": auto"
    if return_type in ("JsonVal", "pytra.std.json.JsonVal"):
        return ""
    if _is_generic_typevar_name(ctx, return_type):
        return ""
    tt = _render_type(ctx, return_type, for_return=True)
    if tt == "" or tt == "void":
        return ""
    return ": " + tt


def _should_infer_local_type(resolved_type: str) -> bool:
    return "JsonVal" in resolved_type or ("|" in resolved_type and "None" not in resolved_type)


def _should_use_auto_param_type(resolved_type: str) -> bool:
    return "JsonVal" in resolved_type


def _is_generic_typevar_name(ctx: EmitContext, resolved_type: str) -> bool:
    if resolved_type in ctx.class_names or resolved_type in ctx.trait_names:
        return False
    if len(resolved_type) == 1 and "A" <= resolved_type <= "Z":
        return True
    return False


def _union_tag_name(union_type: str, option_type: str) -> str:
    union_name = nim_union_type_name(union_type).lower()
    option_name = _safe_nim_ident(option_type.replace("[", "_").replace("]", "").replace(", ", "_").replace(",", "_")).lower()
    return union_name + "_" + option_name


def _union_field_name(option_type: str) -> str:
    base = _safe_nim_ident(option_type.replace("[", "_").replace("]", "").replace(", ", "_").replace(",", "_")).lower()
    if base.endswith("_"):
        base = base[:-1]
    return base + "_val"


def _collect_general_unions_from_type(resolved_type: str, out: list[str]) -> None:
    rt = _strip_tuple_name(resolved_type)
    if rt == "" or rt == "unknown":
        return
    if is_general_union_type(rt):
        rt_name = nim_union_type_name(rt)
        exists = False
        for current in out:
            if nim_union_type_name(current) == rt_name:
                exists = True
                break
        if not exists:
            out.append(rt)
        for option in union_options(rt):
            _collect_general_unions_from_type(option, out)
        return
    if _starts_with_nested_type(rt) and rt.endswith("]"):
        head = rt.split("[", 1)[0]
        inner = rt[len(head) + 1:-1]
        for part in _split_generic_args(inner):
            _collect_general_unions_from_type(part, out)


def _collect_general_unions_from_json(node: JsonVal, out: list[str]) -> None:
    if isinstance(node, dict):
        rt = node.get("resolved_type")
        if isinstance(rt, str):
            _collect_general_unions_from_type(rt, out)
        for value in node.values():
            _collect_general_unions_from_json(value, out)
    elif isinstance(node, list):
        for value in node:
            _collect_general_unions_from_json(value, out)


def _emit_general_union_defs(ctx: EmitContext) -> None:
    for union_type in ctx.general_unions:
        union_name = nim_union_type_name(union_type)
        kind_name = union_name + "Kind"
        options: list[str] = union_options(union_type)
        tags: list[str] = []
        tag_idx = 0
        while tag_idx < len(options):
            option = _str_at(options, tag_idx)
            tags.append(_union_tag_name(union_type, option))
            tag_idx += 1
        _emit(ctx, "type " + kind_name + "* = enum")
        ctx.indent_level += 1
        for tag in tags:
            _emit(ctx, tag)
        ctx.indent_level -= 1
        _emit(ctx, "type " + union_name + "* = object")
        ctx.indent_level += 1
        _emit(ctx, "case kind*: " + kind_name)
        dict_option = ""
        list_option = ""
        none_option = ""
        scalar_options: list[tuple[str, str]] = []
        opt_idx = 0
        while opt_idx < len(options):
            option = _str_at(options, opt_idx)
            tag = _union_tag_name(union_type, option)
            field_name = _union_field_name(option)
            field_type = _render_type(ctx, option)
            if dict_option == "" and option.startswith("dict["):
                dict_option = option
            if list_option == "" and option.startswith("list["):
                list_option = option
            if none_option == "" and option == "None":
                none_option = option
            if option in ("int", "int64", "str", "string", "bool", "float", "float64"):
                scalar_options.append((field_name, field_type))
            _emit(ctx, "of " + tag + ":")
            ctx.indent_level += 1
            if option == "None":
                _emit(ctx, "discard")
            else:
                _emit(ctx, field_name + "*: " + field_type)
            ctx.indent_level -= 1
            opt_idx += 1
        ctx.indent_level -= 1
        _emit_blank(ctx)
        opt_idx2 = 0
        while opt_idx2 < len(options):
            option = _str_at(options, opt_idx2)
            field_name = _union_field_name(option)
            field_type = _render_type(ctx, option)
            tag = _union_tag_name(union_type, option)
            if option == "None":
                _emit(ctx, "converter to_" + _safe_nim_ident(union_name.lower()) + "_from_" + _safe_nim_ident(field_name.lower()) + "*(v: typeof(nil)): " + union_name + " =")
                ctx.indent_level += 1
                _emit(ctx, union_name + "(kind: " + tag + ")")
                ctx.indent_level -= 1
                _emit_blank(ctx)
            else:
                _emit(ctx, "converter to_" + _safe_nim_ident(union_name.lower()) + "_from_" + _safe_nim_ident(field_name.lower()) + "*(v: " + field_type + "): " + union_name + " =")
                ctx.indent_level += 1
                _emit(ctx, union_name + "(kind: " + tag + ", " + field_name + ": v)")
                ctx.indent_level -= 1
                _emit_blank(ctx)
            if field_type == "int64":
                _emit(ctx, "converter to_" + _safe_nim_ident(union_name.lower()) + "_from_" + _safe_nim_ident(field_name.lower()) + "_int*(v: int): " + union_name + " =")
                ctx.indent_level += 1
                _emit(ctx, union_name + "(kind: " + tag + ", " + field_name + ": int64(v))")
                ctx.indent_level -= 1
                _emit_blank(ctx)
            opt_idx2 += 1
        if dict_option != "":
            dict_parts = _split_generic_args(dict_option[5:-1])
            if len(dict_parts) == 2:
                key_type = _render_type(ctx, dict_parts[0])
                value_type = _render_type(ctx, dict_parts[1])
                dict_tag = _union_tag_name(union_type, dict_option)
                dict_field = _union_field_name(dict_option)
                _emit(ctx, "iterator pairs*(v: " + union_name + "): (" + key_type + ", " + value_type + ") =")
                ctx.indent_level += 1
                _emit(ctx, "case v.kind")
                _emit(ctx, "of " + dict_tag + ":")
                ctx.indent_level += 1
                _emit(ctx, "for item in v." + dict_field + ".pairs:")
                ctx.indent_level += 1
                _emit(ctx, "yield item")
                ctx.indent_level -= 2
                opt_idx3 = 0
                while opt_idx3 < len(options):
                    option = _str_at(options, opt_idx3)
                    if option == dict_option:
                        opt_idx3 += 1
                        continue
                    _emit(ctx, "of " + _union_tag_name(union_type, option) + ":")
                    ctx.indent_level += 1
                    _emit_discard(ctx)
                    ctx.indent_level -= 1
                    opt_idx3 += 1
                ctx.indent_level -= 1
                _emit_blank(ctx)
                # Only emit `items` for dict when the union has no list option.
                # Otherwise the list-based `items` iterator (below) would
                # conflict and Nim raises "overloaded 'items' leads to ambiguous calls".
                if list_option == "":
                    _emit(ctx, "iterator items*(v: " + union_name + "): (" + key_type + ", " + value_type + ") =")
                    ctx.indent_level += 1
                    _emit(ctx, "for item in v.pairs:")
                    ctx.indent_level += 1
                    _emit(ctx, "yield item")
                    ctx.indent_level -= 2
                    _emit_blank(ctx)
                _emit(ctx, "iterator keys*(v: " + union_name + "): " + key_type + " =")
                ctx.indent_level += 1
                _emit(ctx, "for item in v.pairs:")
                ctx.indent_level += 1
                _emit(ctx, "yield item[0]")
                ctx.indent_level -= 2
                _emit_blank(ctx)
                _emit(ctx, "iterator values*(v: " + union_name + "): " + value_type + " =")
                ctx.indent_level += 1
                _emit(ctx, "for item in v.pairs:")
                ctx.indent_level += 1
                _emit(ctx, "yield item[1]")
                ctx.indent_level -= 2
                _emit_blank(ctx)
                _emit(ctx, "converter to_" + _safe_nim_ident(union_name.lower()) + "_dict*(v: " + union_name + "): Table[" + key_type + ", " + value_type + "] =")
                ctx.indent_level += 1
                _emit(ctx, "v." + dict_field)
                ctx.indent_level -= 1
                _emit_blank(ctx)
        if list_option != "":
            list_parts = _split_generic_args(list_option[5:-1])
            if len(list_parts) == 1:
                elem_type = _render_type(ctx, list_parts[0])
                list_field = _union_field_name(list_option)
                _emit(ctx, "proc py_index*(v: " + union_name + ", idx: int): " + elem_type + " =")
                ctx.indent_level += 1
                _emit(ctx, "v." + list_field + "[idx]")
                ctx.indent_level -= 1
                _emit_blank(ctx)
                _emit(ctx, "iterator items*(v: " + union_name + "): " + elem_type + " =")
                ctx.indent_level += 1
                _emit(ctx, "for item in v." + list_field + ":")
                ctx.indent_level += 1
                _emit(ctx, "yield item")
                ctx.indent_level -= 2
                _emit_blank(ctx)
        for field_name, field_type in scalar_options:
            _emit(ctx, "converter to_" + _safe_nim_ident(union_name.lower()) + "_" + _safe_nim_ident(field_type.lower()) + "*(v: " + union_name + "): " + field_type + " =")
            ctx.indent_level += 1
            _emit(ctx, "v." + field_name)
            ctx.indent_level -= 1
            _emit_blank(ctx)
        if none_option != "":
            none_tag = _union_tag_name(union_type, none_option)
            _emit(ctx, "proc `==`*(v: " + union_name + ", other: typeof(nil)): bool =")
            ctx.indent_level += 1
            _emit(ctx, "v.kind == " + none_tag)
            ctx.indent_level -= 1
            _emit_blank(ctx)
        _emit(ctx, "proc py_to_string*(v: " + union_name + "): string =")
        ctx.indent_level += 1
        _emit(ctx, "case v.kind")
        for option in options:
            _emit(ctx, "of " + _union_tag_name(union_type, option) + ":")
            ctx.indent_level += 1
            if option == "None":
                _emit(ctx, '"None"')
            else:
                _emit(ctx, "py_to_string(v." + _union_field_name(option) + ")")
            ctx.indent_level -= 1
        ctx.indent_level -= 1
        _emit_blank(ctx)


def _union_has_nominal_option(ctx: EmitContext, union_type: str) -> bool:
    for option in union_options(union_type):
        if option in ctx.class_names or option in ctx.trait_names:
            return True
    return False


def _find_union_option_for_source(target_type: str, source_type: str) -> str:
    target_options: list[str] = union_options(target_type)
    if source_type in target_options:
        return source_type
    source_rendered = nim_type(source_type)
    option_idx = 0
    while option_idx < len(target_options):
        option: str = target_options[option_idx]
        if nim_type(option) == source_rendered:
            return option
        option_idx += 1
    return target_options[0] if len(target_options) > 0 else ""


def _emit_union_wrap(ctx: EmitContext, expr_code: str, node: JsonVal, target_type: str) -> str:
    source_type = _str(node, "resolved_type") if isinstance(node, dict) else ""
    if isinstance(node, dict):
        node_kind = _str(node, "kind")
        if node_kind == "Dict":
            dict_options: list[str] = union_options(target_type)
            option_idx = 0
            while option_idx < len(dict_options):
                option: str = dict_options[option_idx]
                if option.startswith("dict["):
                    source_type = option
                    break
                option_idx += 1
        elif node_kind == "List":
            list_options: list[str] = union_options(target_type)
            option_idx = 0
            while option_idx < len(list_options):
                option: str = list_options[option_idx]
                if option.startswith("list["):
                    source_type = option
                    break
                option_idx += 1
        elif node_kind == "Set":
            set_options: list[str] = union_options(target_type)
            option_idx = 0
            while option_idx < len(set_options):
                option: str = set_options[option_idx]
                if option.startswith("set["):
                    source_type = option
                    break
                option_idx += 1
        elif node_kind == "Constant":
            value = node.get("value")
            if isinstance(value, bool):
                source_type = "bool"
            elif isinstance(value, int) and not isinstance(value, bool):
                source_type = "int64"
            elif isinstance(value, float):
                source_type = "float64"
            elif isinstance(value, str):
                source_type = "str"
            elif value is None:
                source_type = "None"
    if source_type == target_type:
        return expr_code
    if is_general_union_type(source_type):
        source_union_name = nim_union_type_name(source_type)
        target_union_name = nim_union_type_name(target_type)
        lines = ["(block:", "  let union_tmp = " + expr_code, "  case union_tmp.kind"]
        target_options: list[str] = union_options(target_type)
        fallback_option = target_options[0] if len(target_options) > 0 else ""
        fallback_expr = "default(" + target_union_name + ")"
        if fallback_option != "":
            fallback_expr = target_union_name + "(kind: " + _union_tag_name(target_type, fallback_option) + ", " + _union_field_name(fallback_option) + ": " + nim_zero_value(fallback_option) + ")"
        source_options: list[str] = union_options(source_type)
        source_idx = 0
        while source_idx < len(source_options):
            option = _str_at(source_options, source_idx)
            source_tag = _union_tag_name(source_type, option)
            source_field = "union_tmp." + _union_field_name(option)
            if option in target_options:
                lines.append(
                    "  of " + source_tag + ": " + target_union_name + "(kind: " + _union_tag_name(target_type, option) + ", " + _union_field_name(option) + ": " + source_field + ")"
                )
            else:
                lines.append("  of " + source_tag + ": " + fallback_expr)
            source_idx += 1
        lines.append(")")
        return "\n".join(lines)
    option_type = _find_union_option_for_source(target_type, source_type)
    if option_type == "":
        return expr_code
    union_name = nim_union_type_name(target_type)
    tag = _union_tag_name(target_type, option_type)
    if option_type == "None":
        return union_name + "(kind: " + tag + ")"
    field_name = _union_field_name(option_type)
    casted = _maybe_cast_expr_to_type(ctx, expr_code, node, option_type)
    return union_name + "(kind: " + tag + ", " + field_name + ": " + casted + ")"


def _emit_union_case_access(
    ctx: EmitContext,
    expr_code: str,
    union_type: str,
    wanted_type: str,
    *,
    fallback: str,
) -> str:
    lines = ["(block:", "  let union_tmp = " + expr_code, "  case union_tmp.kind"]
    options: list[str] = union_options(union_type)
    opt_idx = 0
    while opt_idx < len(options):
        option = _str_at(options, opt_idx)
        tag = _union_tag_name(union_type, option)
        field_name = _union_field_name(option)
        if option == wanted_type:
            lines.append("  of " + tag + ": union_tmp." + field_name)
        else:
            lines.append("  of " + tag + ": " + fallback)
        opt_idx += 1
    lines.append(")")
    return "\n".join(lines)


def _emit_union_to_string(ctx: EmitContext, expr_code: str, union_type: str) -> str:
    return "py_to_string(" + expr_code + ")"


def _emit_union_to_int(ctx: EmitContext, expr_code: str, union_type: str) -> str:
    return "int64(py_int(py_to_string(" + expr_code + ")))"


def _emit_union_to_bool(ctx: EmitContext, expr_code: str, union_type: str) -> str:
    lines = ["(block:", "  let union_tmp = " + expr_code, "  case union_tmp.kind"]
    options: list[str] = union_options(union_type)
    opt_idx = 0
    while opt_idx < len(options):
        option = _str_at(options, opt_idx)
        field_expr = "union_tmp." + _union_field_name(option)
        lines.append("  of " + _union_tag_name(union_type, option) + ": py_truthy(" + field_expr + ")")
        opt_idx += 1
    lines.append(")")
    return "\n".join(lines)


def _emit_union_to_float(ctx: EmitContext, expr_code: str, union_type: str) -> str:
    lines = ["(block:", "  let union_tmp = " + expr_code, "  case union_tmp.kind"]
    options: list[str] = union_options(union_type)
    opt_idx = 0
    while opt_idx < len(options):
        option = _str_at(options, opt_idx)
        field_expr = "union_tmp." + _union_field_name(option)
        if option in ("int", "int64", "byte", "uint8", "bool", "float", "float64", "str"):
            value_expr = "float64(py_float(" + field_expr + "))"
        else:
            value_expr = "float64(py_float(py_to_string(" + field_expr + ")))"
        lines.append("  of " + _union_tag_name(union_type, option) + ": " + value_expr)
        opt_idx += 1
    lines.append(")")
    return "\n".join(lines)


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
    if kind == "IsInstance":
        return _emit_isinstance_node(ctx, node)
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
    if kind == "SetComp":
        return _emit_setcomp(ctx, node)
    if kind == "DictComp":
        return _emit_dictcomp(ctx, node)
    if kind == "JoinedStr":
        return _emit_fstring(ctx, node)
    if kind == "Lambda" or kind == "ClosureDef":
        return _emit_lambda(ctx, node)
    if kind == "Unbox" or kind == "Box":
        return _emit_expr(ctx, node.get("value"))
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
        text = _str(node, "value")
        return _nim_string(text)
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
        mapped = ctx.runtime_imports[name]
        if "." in mapped and _last_dot_part(mapped) == name:
            return _nim_name(ctx, name)
        return mapped
    actual_type = ctx.var_types.get(_nim_name(ctx, name), "")
    node_type = _str(node, "resolved_type")
    if _is_top_level_union_type(actual_type) and node_type != "" and node_type != actual_type:
        options: list[str] = union_options(actual_type)
        opt_idx = 0
        while opt_idx < len(options):
            option = _str_at(options, opt_idx)
            if option == node_type:
                field = _safe_nim_ident(option.replace("[", "_").replace("]", "").replace(", ", "_").replace(",", "_")).lower() + "_val"
                return _nim_name(ctx, name) + "." + field
            opt_idx += 1
    return _nim_name(ctx, name)


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr = _str(node, "attr")

    if attr == "__name__" and isinstance(owner_node, dict) and _str(owner_node, "kind") == "Call":
        func_node = owner_node.get("func")
        if _str(owner_node, "builtin_name") == "type" or (isinstance(func_node, dict) and _str(func_node, "kind") == "Name" and _str(func_node, "id") == "type"):
            args = _list(owner_node, "args")
            if len(args) > 0 and isinstance(args[0], dict):
                type_name = _str(args[0], "resolved_type")
                if type_name != "":
                    return _nim_string(_safe_nim_ident(type_name))

    # self.field -> self.field
    if isinstance(owner_node, dict) and _str(owner_node, "id") == "self":
        return "self." + _safe_nim_ident(attr)

    if isinstance(owner_node, dict):
        owner_id = _str(owner_node, "id")
        if owner_id in ctx.enum_bases:
            return _safe_nim_ident(attr)
        if owner_id in ctx.class_names:
            if owner_id in ctx.class_static_methods:
                static_methods = ctx.class_static_methods[owner_id]
                if attr in static_methods:
                    return _safe_nim_ident(attr)
            if owner_id in ctx.class_static_attrs:
                static_attrs = ctx.class_static_attrs[owner_id]
                if attr in static_attrs:
                    return _nim_name(ctx, owner_id) + "_" + _safe_nim_ident(attr)

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
                mod_short = _last_dot_part(mod_id)
                qualified_key = mod_short + "." + runtime_symbol
                if qualified_key in ctx.mapping.calls:
                    return ctx.mapping.calls[qualified_key]
                if runtime_symbol.startswith(ctx.mapping.builtin_prefix):
                    return runtime_symbol[len(ctx.mapping.builtin_prefix):]
                return ctx.mapping.builtin_prefix + runtime_symbol

    owner = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Name":
        actual_owner_rt = ctx.var_types.get(owner, "")
        if actual_owner_rt == "":
            actual_owner_rt = ctx.var_types.get(_nim_name(ctx, _str(owner_node, "id")), "")
        if actual_owner_rt != "":
            owner_rt = actual_owner_rt
    if is_general_union_type(owner_rt) and attr in ("pairs", "keys", "values"):
        dict_option = ""
        owner_options: list[str] = union_options(owner_rt)
        opt_idx = 0
        while opt_idx < len(owner_options):
            option: str = owner_options[opt_idx]
            if option.startswith("dict["):
                dict_option = option
                break
            opt_idx += 1
        if dict_option != "":
            dict_expr = _emit_union_case_access(ctx, owner, owner_rt, dict_option, fallback="default(" + _render_type(ctx, dict_option) + ")")
            return dict_expr + "." + _safe_nim_ident(attr)
    return owner + "." + _safe_nim_ident(attr)


def _emit_subscript(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Name":
        actual_owner_rt = ctx.var_types.get(_nim_name(ctx, _str(owner_node, "id")), "")
        if actual_owner_rt != "":
            owner_rt = actual_owner_rt
    if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Name":
        actual_owner_rt = ctx.var_types.get(_nim_name(ctx, _str(owner_node, "id")), "")
        if _is_top_level_union_type(actual_owner_rt):
            actual_options: list[str] = union_options(actual_owner_rt)
            opt_idx = 0
            while opt_idx < len(actual_options):
                option: str = actual_options[opt_idx]
                if option.startswith("dict["):
                    owner_rt = option
                    field = _safe_nim_ident(option.replace("[", "_").replace("]", "").replace(", ", "_").replace(",", "_")).lower() + "_val"
                    owner = _nim_name(ctx, _str(owner_node, "id")) + "." + field
                    break
                if option.startswith("list["):
                    owner_rt = option
                    field = _safe_nim_ident(option.replace("[", "_").replace("]", "").replace(", ", "_").replace(",", "_")).lower() + "_val"
                    owner = _nim_name(ctx, _str(owner_node, "id")) + "." + field
                    break
                opt_idx += 1
    result_rt = _str(node, "resolved_type")
    slice_node = node.get("slice")

    # Slice
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        lower_code = _emit_expr(ctx, lower) if isinstance(lower, dict) else "0"
        upper_code = _emit_expr(ctx, upper) if isinstance(upper, dict) else owner + ".len"
        if isinstance(lower, dict):
            neg_val = _get_negative_int_literal(lower)
            if neg_val is not None:
                lower_code = owner + ".len + (" + str(neg_val) + ")"
        if isinstance(upper, dict):
            neg_val = _get_negative_int_literal(upper)
            if neg_val is not None:
                upper_code = owner + ".len + (" + str(neg_val) + ")"
        return owner + "[" + lower_code + " ..< " + upper_code + "]"

    # dict -> [] access
    is_dict = owner_rt.startswith("dict[") or owner_rt == "dict"
    if is_dict and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        access = owner + "[" + slice_code + "]"
        rendered_owner = _render_type(ctx, owner_rt)
        if rendered_owner.endswith(", PyObj]"):
            if result_rt in ("bool",):
                return "py_bool(" + access + ")"
            if result_rt in ("str", "string"):
                return "py_str(" + access + ")"
            if result_rt in ("int", "int64"):
                return "int64(py_int(" + access + "))"
            if result_rt in ("float", "float64"):
                return "float64(py_float(" + access + "))"
        return access

    # list/string/bytes -> route through runtime helper so negative indices and
    # out-of-range behavior raise Python-compatible IndexError instead of Nim defects.
    if owner_rt.startswith("list[") and isinstance(owner_node, dict) and _str(owner_node, "kind") == "Name" and owner != _nim_name(ctx, _str(owner_node, "id")) and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        return owner + "[" + slice_code + "]"
    if is_general_union_type(owner_rt):
        owner_options: list[str] = union_options(owner_rt)
        owner_idx = 0
        while owner_idx < len(owner_options):
            option = _str_at(owner_options, owner_idx)
            if option.startswith("list[") and isinstance(slice_node, dict):
                slice_code = _emit_expr(ctx, slice_node)
                return owner + "[" + slice_code + "]"
            owner_idx += 1
    is_array_like = (
        owner_rt.startswith("list[") or owner_rt in ("list", "str", "string", "bytes", "bytearray")
    )
    if is_array_like and isinstance(slice_node, dict):
        slice_code = _emit_expr(ctx, slice_node)
        access = "py_runtime.py_index(" + owner + ", " + slice_code + ")"
        if owner_rt in ("str", "string") and result_rt == "str":
            return "$(" + access + ")"
        return access

    slice_code = _emit_expr(ctx, slice_node)
    access = owner + "[" + slice_code + "]"
    if owner_rt in ("str", "string") and result_rt == "str":
        return "$(" + access + ")"
    return access


def _emit_subscript_target(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Subscript":
        owner = _emit_subscript_target(ctx, owner_node)
    else:
        owner = _emit_expr(ctx, owner_node)
    slice_node = node.get("slice")
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
    result_rt = _str(node, "resolved_type")

    if isinstance(left_node, dict) and _str(left_node, "kind") == "Name":
        actual_left_rt = ctx.var_types.get(_nim_name(ctx, _str(left_node, "id")), "")
        if actual_left_rt != "" and actual_left_rt != left_rt:
            left_rt = actual_left_rt
    if isinstance(right_node, dict) and _str(right_node, "kind") == "Name":
        actual_right_rt = ctx.var_types.get(_nim_name(ctx, _str(right_node, "id")), "")
        if actual_right_rt != "" and actual_right_rt != right_rt:
            right_rt = actual_right_rt

    if op == "Div" and left_rt in ("Path", "PyPath", "pytra.std.pathlib.Path") and right_rt in ("str", "string"):
        return "joinpath(" + left + ", " + right + ")"

    numeric_types = {
        "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "float32", "float64", "float",
    }
    if left_rt in numeric_types and right_rt in numeric_types and result_rt in numeric_types:
        if left_rt != result_rt:
            left = _render_type(ctx, result_rt) + "(" + left + ")"
        if right_rt != result_rt:
            right = _render_type(ctx, result_rt) + "(" + right + ")"

    # str + str -> string concatenation
    if op == "Add" and (left_rt == "str" or right_rt == "str"):
        return "(" + left + " & " + right + ")"

    # list + list -> concat
    if op == "Add" and (left_rt.startswith("list[") or right_rt.startswith("list[")):
        return "(" + left + " & " + right + ")"

    # str * int / list * int -> repeat
    if op == "Mult":
        if left_rt == "str" or left_rt.startswith("list["):
            return "py_repeat(" + left + ", " + right + ")"
        if right_rt == "str" or right_rt.startswith("list["):
            return "py_repeat(" + right + ", " + left + ")"

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
    if op == "Not":
        return "(not (" + operand + "))"
    op_map: dict[str, str] = {
        "USub": "-", "UAdd": "+", "Invert": "not ",
    }
    op_text = op_map.get(op, op)
    return "(" + op_text + operand + ")"


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left = _emit_expr(ctx, node.get("left"))
    left_node = node.get("left")
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return left
    parts: list[str] = []
    current_left = left
    current_left_rt = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
    if isinstance(left_node, dict) and _str(left_node, "kind") == "Name":
        actual_left_rt = ctx.var_types.get(_nim_name(ctx, _str(left_node, "id")), "")
        if actual_left_rt != "":
            current_left_rt = actual_left_rt
    for idx, comparator in enumerate(comparators):
        op_name = ""
        if idx < len(ops):
            op_val = ops[idx]
            if isinstance(op_val, str):
                op_name = op_val
        right = _emit_expr(ctx, comparator)
        right_rt = _str(comparator, "resolved_type") if isinstance(comparator, dict) else ""
        if isinstance(comparator, dict) and _str(comparator, "kind") == "Name":
            actual_right_rt = ctx.var_types.get(_nim_name(ctx, _str(comparator, "id")), "")
            if actual_right_rt != "":
                right_rt = actual_right_rt
        if op_name == "In":
            if isinstance(comparator, dict) and _str(comparator, "kind") == "Call" and right.startswith("py_range("):
                parts.append("contains(toSeq(" + right + "), " + current_left + ")")
            elif right_rt.startswith("tuple[") and isinstance(comparator, dict) and _str(comparator, "kind") == "Name":
                tuple_parts: list[str] = _split_generic_args(right_rt[6:-1])
                checks: list[str] = []
                tuple_idx = 0
                while tuple_idx < len(tuple_parts):
                    checks.append(current_left + " == " + right + "[" + str(tuple_idx) + "]")
                    tuple_idx += 1
                parts.append("(" + " or ".join(checks) + ")")
            else:
                parts.append(current_left + " in " + right)
        elif op_name == "NotIn":
            if isinstance(comparator, dict) and _str(comparator, "kind") == "Call" and right.startswith("py_range("):
                parts.append("not contains(toSeq(" + right + "), " + current_left + ")")
            elif right_rt.startswith("tuple[") and isinstance(comparator, dict) and _str(comparator, "kind") == "Name":
                tuple_parts: list[str] = _split_generic_args(right_rt[6:-1])
                checks: list[str] = []
                tuple_idx = 0
                while tuple_idx < len(tuple_parts):
                    checks.append(current_left + " != " + right + "[" + str(tuple_idx) + "]")
                    tuple_idx += 1
                parts.append("(" + " and ".join(checks) + ")")
            else:
                parts.append(current_left + " notin " + right)
        elif op_name == "Is":
            if (
                isinstance(comparator, dict)
                and _str(comparator, "kind") == "Constant"
                and comparator.get("value") is None
                and isinstance(left_node, dict)
                and _str(left_node, "kind") == "Name"
            ):
                actual_left_rt = ctx.var_types.get(_nim_name(ctx, _str(left_node, "id")), "")
                has_none_option = False
                if is_general_union_type(actual_left_rt):
                    none_options: list[str] = union_options(actual_left_rt)
                    for none_option in none_options:
                        if none_option == "None":
                            has_none_option = True
                            break
                if has_none_option:
                    parts.append("(" + _nim_name(ctx, _str(left_node, "id")) + ".kind == " + _union_tag_name(actual_left_rt, "None") + ")")
                    current_left = right
                    current_left_rt = right_rt
                    continue
            parts.append("(" + current_left + " == " + right + ")")
        elif op_name == "IsNot":
            parts.append("(" + current_left + " != " + right + ")")
        else:
            cmp_map: dict[str, str] = {
                "Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=",
                "Gt": ">", "GtE": ">=",
            }
            cmp_text = cmp_map.get(op_name, "==")
            left_is_string = current_left_rt in ("str", "string")
            right_is_string = right_rt in ("str", "string")
            left_is_numeric = current_left_rt in ("byte", "uint8", "int", "int64", "float", "float64", "bool")
            right_is_numeric = right_rt in ("byte", "uint8", "int", "int64", "float", "float64", "bool")
            if (left_is_string and right_is_numeric) or (left_is_numeric and right_is_string):
                parts.append("false" if op_name == "Eq" else "true")
            else:
                if left_is_numeric and right_is_numeric:
                    if current_left_rt != right_rt:
                        if current_left_rt in ("byte", "uint8") and right_rt in ("int", "int64"):
                            current_left = "int64(" + current_left + ")"
                        elif right_rt in ("byte", "uint8") and current_left_rt in ("int", "int64"):
                            right = "int64(" + right + ")"
                        elif current_left_rt in ("float", "float64") or right_rt in ("float", "float64"):
                            current_left = "float64(" + current_left + ")"
                            right = "float64(" + right + ")"
                parts.append("(" + current_left + " " + cmp_text + " " + right + ")")
        current_left = right
        current_left_rt = right_rt
    if len(parts) == 1:
        return parts[0]
    return "(" + " and ".join(parts) + ")"


def _emit_condition_expr(ctx: EmitContext, node: JsonVal) -> str:
    expr_code = _emit_expr(ctx, node)
    if not isinstance(node, dict):
        return "py_truthy(" + expr_code + ")"
    resolved_type = _str(node, "resolved_type")
    kind = _str(node, "kind")
    if resolved_type == "bool" or kind in ("Compare", "BoolOp"):
        return expr_code
    return "py_truthy(" + expr_code + ")"


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    op = _str(node, "op")
    if len(values) == 0:
        return "false"
    all_bool_values = True
    for value in values:
        if not isinstance(value, dict):
            all_bool_values = False
            break
        value_rt = _str(value, "resolved_type")
        value_kind = _str(value, "kind")
        if value_rt != "bool" and value_kind not in ("Compare", "BoolOp", "IsInstance", "UnaryOp"):
            all_bool_values = False
            break
    if all_bool_values:
        op_text = "and" if op == "And" else "or"
        return "(" + (" " + op_text + " ").join(_emit_condition_expr(ctx, v) for v in values) + ")"
    acc = _emit_expr(ctx, values[0])
    idx = 1
    while idx < len(values):
        next_value = _emit_expr(ctx, values[idx])
        cond = _emit_condition_expr(ctx, values[idx - 1])
        if op == "And":
            acc = "(if " + cond + ": " + next_value + " else: " + acc + ")"
        else:
            acc = "(if " + cond + ": " + acc + " else: " + next_value + ")"
        idx += 1
    return acc


def _emit_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test = _emit_condition_expr(ctx, node.get("test"))
    body = _emit_expr(ctx, node.get("body"))
    orelse = _emit_expr(ctx, node.get("orelse"))
    resolved_type = _str(node, "resolved_type")
    if "str" in resolved_type and "None" in resolved_type:
        if body == "nil":
            body = '""'
        if orelse == "nil":
            orelse = '""'
    elif "|" in resolved_type and "None" not in resolved_type:
        body = "py_to_string(" + body + ")"
        orelse = "py_to_string(" + orelse + ")"
    return "(if " + test + ": " + body + " else: " + orelse + ")"


def _emit_list_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    rt = _str(node, "resolved_type")
    if len(elements) == 0:
        if rt.startswith("list[") and rt.endswith("]"):
            inner = rt[5:-1]
            return "newSeq[" + _render_type(ctx, inner) + "]()"
        return "@[]"
    inner_type = ""
    if rt.startswith("list[") and rt.endswith("]"):
        inner_type = rt[5:-1]
    elif "|" in rt:
        # Union type (e.g. Optional): extract the list[...] option if present
        options: list[str] = union_options(rt)
        opt_idx = 0
        while opt_idx < len(options):
            _opt = _str_at(options, opt_idx)
            if _opt.startswith("list[") and _opt.endswith("]"):
                inner_type = _opt[5:-1]
                break
            opt_idx += 1
    elem_strs: list[str] = []
    for element in elements:
        element_code = _emit_expr(ctx, element)
        if inner_type != "" and is_general_union_type(inner_type):
            element_code = _maybe_cast_expr_to_type(ctx, element_code, element, inner_type)
        elif _render_type(ctx, inner_type) == "PyObj":
            element_code = _maybe_cast_expr_to_type(ctx, element_code, element, inner_type)
        if (
            inner_type in ("int", "int64", "uint8", "float", "float64")
            and isinstance(element, dict)
            and _str(element, "kind") == "Constant"
        ):
            element_code = _render_type(ctx, inner_type) + "(" + element_code + ")"
        elem_strs.append(element_code)
    return "@[" + ", ".join(elem_strs) + "]"


def _emit_dict_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    entries = _list(node, "entries")
    rt = _str(node, "resolved_type")
    k_type = "string"
    v_type = "PyObj"
    parts: list[str] = []
    expected_key_type = ""
    expected_value_type = ""
    if rt.startswith("dict[") and rt.endswith("]"):
        parts = _split_generic_args(rt[5:-1])
        if len(parts) == 2:
            expected_key_type = parts[0]
            expected_value_type = parts[1]
            k_type = _render_type(ctx, parts[0])
            v_type = _render_type(ctx, parts[1])

    if len(entries) == 0:
        return "initTable[" + k_type + ", " + v_type + "]()"

    pairs: list[str] = []
    if len(entries) > 0:
        for entry in entries:
            if isinstance(entry, dict):
                key_node = entry.get("key")
                value_node = entry.get("value")
                kc = _emit_expr(ctx, key_node)
                vc = _emit_expr(ctx, value_node)
                kc = _maybe_cast_expr_to_type(ctx, kc, key_node, expected_key_type)
                vc = _maybe_cast_expr_to_type(ctx, vc, value_node, expected_value_type)
                if len(parts) == 2 and (
                    _render_type(ctx, parts[1]) == "PyObj"
                    or "object" in parts[1]
                ):
                    if vc != "nil" and not vc.startswith("py_box("):
                        vc = "py_box(" + vc + ")"
                pairs.append("(" + kc + ", " + vc + ")")
    else:
        keys = _list(node, "keys")
        values = _list(node, "values")
        for idx, key in enumerate(keys):
            kc = _emit_expr(ctx, key)
            val_node: JsonVal = None
            vc = "nil"
            if idx < len(values):
                val_node = values[idx]
                vc = _emit_expr(ctx, val_node)
            kc = _maybe_cast_expr_to_type(ctx, kc, key, expected_key_type)
            vc = _maybe_cast_expr_to_type(ctx, vc, val_node, expected_value_type)
            if len(parts) == 2 and (
                _render_type(ctx, parts[1]) == "PyObj"
                or "object" in parts[1]
            ):
                if vc != "nil" and not vc.startswith("py_box("):
                    vc = "py_box(" + vc + ")"
            pairs.append("(" + kc + ", " + vc + ")")

    return "toTable([" + ", ".join(pairs) + "])"


def _emit_object_dict_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    entries = _list(node, "entries")
    pairs: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key_node = entry.get("key")
        value_node = entry.get("value")
        kc = _emit_expr(ctx, key_node)
        vc = _emit_expr(ctx, value_node)
        if vc != "nil" and not vc.startswith("py_box("):
            vc = "py_box(" + vc + ")"
        pairs.append("(" + kc + ", " + vc + ")")
    return "toTable([" + ", ".join(pairs) + "])"


def _boxed_dict_inner(node: JsonVal) -> dict[str, JsonVal] | None:
    if not isinstance(node, dict):
        return None
    if _str(node, "kind") == "Dict":
        return node
    if _str(node, "kind") == "Box":
        inner = node.get("value")
        if isinstance(inner, dict) and _str(inner, "kind") == "Dict":
            return inner
    return None


def _emit_set_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    rt = _str(node, "resolved_type")
    if len(elements) == 0:
        if rt.startswith("set[") and rt.endswith("]"):
            inner = rt[4:-1]
            return "initHashSet[" + _render_type(ctx, inner) + "]()"
        return "initHashSet[PyObj]()"
    inner_type = ""
    if rt.startswith("set[") and rt.endswith("]"):
        inner_type = rt[4:-1]
    elem_strs: list[str] = []
    for element in elements:
        element_code = _emit_expr(ctx, element)
        if (
            inner_type in ("int", "int64", "uint8", "float", "float64")
            and isinstance(element, dict)
            and _str(element, "kind") == "Constant"
        ):
            element_code = _render_type(ctx, inner_type) + "(" + element_code + ")"
        elem_strs.append(element_code)
    return "[" + ", ".join(elem_strs) + "].toHashSet"


def _emit_tuple_literal(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    tuple_rt = _str(node, "resolved_type")
    expected_parts: list[str] = []
    if tuple_rt.startswith("tuple[") and tuple_rt.endswith("]"):
        expected_parts = _split_generic_args(tuple_rt[6:-1])
    elem_strs: list[str] = []
    for idx, element in enumerate(elements):
        if idx < len(expected_parts):
            elem_strs.append(_emit_expr_with_expected_type(ctx, element, expected_parts[idx]))
        else:
            elem_strs.append(_emit_expr(ctx, element))
    if len(elem_strs) == 1:
        return "(" + elem_strs[0] + ",)"
    return "(" + ", ".join(elem_strs) + ")"


def _maybe_cast_expr_to_type(ctx: EmitContext, expr_code: str, node: JsonVal, target_type: str) -> str:
    if target_type != "" and is_general_union_type(target_type):
        if expr_code == "nil":
            return expr_code
        return _emit_union_wrap(ctx, expr_code, node, target_type)
    if "|" in target_type:
        if expr_code == "nil":
            return "nil"
        return "py_box(" + expr_code + ")"
    if target_type != "" and _render_type(ctx, target_type) == "PyObj":
        if expr_code == "nil":
            return "nil"
        return "py_box(" + expr_code + ")"
    if (
        target_type in ("bool", "byte", "int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float", "float32", "float64", "str")
        and isinstance(node, dict)
        and _str(node, "kind") in ("IfExp", "BinOp")
    ):
        return _render_type(ctx, target_type) + "(" + expr_code + ")"
    if target_type not in ("bool", "byte", "int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float", "float32", "float64", "str"):
        return expr_code
    if not isinstance(node, dict):
        return expr_code
    if _str(node, "kind") == "Constant":
        return _render_type(ctx, target_type) + "(" + expr_code + ")"
    node_type = _str(node, "resolved_type")
    if node_type == "" or node_type == target_type:
        return expr_code
    return _render_type(ctx, target_type) + "(" + expr_code + ")"


def _cast_expr_code(ctx: EmitContext, target_type: str, expr_code: str) -> str:
    if target_type == "str":
        return "$(" + expr_code + ")"
    return _render_type(ctx, target_type) + "(" + expr_code + ")"


def _is_top_level_union_type(resolved_type: str) -> bool:
    if "|" not in resolved_type:
        return False
    return not (
        resolved_type.startswith("list[")
        or resolved_type.startswith("dict[")
        or resolved_type.startswith("set[")
        or resolved_type.startswith("tuple[")
        or resolved_type.startswith("deque[")
    )


def _normalized_pod_name(type_name: str) -> str:
    if type_name == "int":
        return "int64"
    if type_name == "float":
        return "float64"
    if type_name == "string":
        return "str"
    return type_name


def _union_option_matches_type_name(option: str, type_name: str) -> bool:
    normalized_type = _normalized_pod_name(type_name)
    normalized_option = _normalized_pod_name(option)
    return (
        normalized_option == normalized_type
        or normalized_option.startswith(normalized_type + "[")
        or (normalized_type == "dict" and normalized_option.startswith("dict["))
        or (normalized_type == "list" and normalized_option.startswith("list["))
        or (normalized_type == "set" and normalized_option.startswith("set["))
    )


def _emit_expr_with_expected_type(ctx: EmitContext, node: JsonVal, expected_type: str) -> str:
    if (
        isinstance(node, dict)
        and _str(node, "kind") == "Constant"
        and node.get("value") is None
    ):
        rendered_expected = _render_type(ctx, expected_type) if expected_type != "" else ""
        if is_general_union_type(expected_type):
            expected_options: list[str] = union_options(expected_type)
            expected_idx = 0
            while expected_idx < len(expected_options):
                expected_option = _str_at(expected_options, expected_idx)
                if expected_option == "None":
                    return nim_union_type_name(expected_type) + "(kind: " + _union_tag_name(expected_type, "None") + ")"
                expected_idx += 1
        if rendered_expected.startswith("seq["):
            return "newSeq[" + rendered_expected[4:-1] + "]()"
        if rendered_expected.startswith("Table["):
            return "init" + rendered_expected + "()"
        if rendered_expected.startswith("HashSet["):
            return "init" + rendered_expected + "()"
        if rendered_expected not in ("", "PyObj") and not rendered_expected.startswith("ref "):
            zero: str = nim_zero_value(expected_type)
            if zero != "":
                return zero
    if isinstance(node, dict):
        node_rt = _str(node, "resolved_type")
        if _render_type(ctx, node_rt) == "PyObj":
            expr_code = _emit_expr(ctx, node)
            if expected_type in ("str", "string"):
                return "py_str(" + expr_code + ")"
            if expected_type in ("bool",):
                return "py_bool(" + expr_code + ")"
            if expected_type in ("int", "int8", "int16", "int32", "int64", "byte", "uint8", "uint16", "uint32", "uint64"):
                return _render_type(ctx, expected_type) + "(py_int(" + expr_code + "))"
            if expected_type in ("float", "float32", "float64"):
                return _render_type(ctx, expected_type) + "(py_float(" + expr_code + "))"
        if is_general_union_type(node_rt):
            expr_code = _emit_expr(ctx, node)
            if expected_type in ("str", "string"):
                return _emit_union_to_string(ctx, expr_code, node_rt)
            if expected_type in ("int", "int8", "int16", "int32", "int64", "byte", "uint8", "uint16", "uint32", "uint64"):
                return _emit_union_to_int(ctx, expr_code, node_rt)
            if expected_type in ("bool",):
                return _emit_union_to_bool(ctx, expr_code, node_rt)
            if expected_type in ("float", "float32", "float64"):
                return _emit_union_to_float(ctx, expr_code, node_rt)
        if node_rt != "" and expected_type in ("int", "int8", "int16", "int32", "int64", "byte", "uint8", "uint16", "uint32", "uint64", "float", "float32", "float64"):
            expr_code = _emit_expr(ctx, node)
            rendered_expected = _render_type(ctx, expected_type)
            rendered_node = _render_type(ctx, node_rt)
            if _str(node, "kind") == "Constant" or rendered_expected != rendered_node:
                return rendered_expected + "(" + expr_code + ")"
    if (
        expected_type in ("byte", "uint8")
        and isinstance(node, dict)
        and _str(node, "kind") == "Subscript"
    ):
        owner = node.get("value")
        owner_rt = _str(owner, "resolved_type") if isinstance(owner, dict) else ""
        if owner_rt in ("str", "string"):
            return "uint8(py_ord(" + _emit_expr(ctx, node) + "))"
    if (
        expected_type != ""
        and isinstance(node, dict)
        and _str(node, "kind") in ("List", "Dict", "Set", "Tuple")
    ):
        if _str(node, "kind") == "Tuple" and expected_type.startswith("tuple[") and expected_type.endswith("]"):
            expected_parts = _split_generic_args(expected_type[6:-1])
            elements = _list(node, "elements")
            rendered: list[str] = []
            for idx, element in enumerate(elements):
                part_type = expected_parts[idx] if idx < len(expected_parts) else ""
                if part_type != "":
                    rendered.append(_emit_expr_with_expected_type(ctx, element, part_type))
                else:
                    rendered.append(_emit_expr(ctx, element))
            if len(rendered) == 1:
                return "(" + rendered[0] + ",)"
            return "(" + ", ".join(rendered) + ")"
        typed_node = dict(node)
        if is_general_union_type(expected_type):
            node_kind = _str(node, "kind")
            lane_type = expected_type
            lane_options: list[str] = union_options(expected_type)
            lane_idx = 0
            while lane_idx < len(lane_options):
                option = _str_at(lane_options, lane_idx)
                if node_kind == "Dict" and option.startswith("dict["):
                    lane_type = option
                    break
                if node_kind == "List" and option.startswith("list["):
                    lane_type = option
                    break
                if node_kind == "Set" and option.startswith("set["):
                    lane_type = option
                    break
                lane_idx += 1
                if node_kind == "Tuple" and option.startswith("tuple["):
                    lane_type = option
                    break
            typed_node["resolved_type"] = lane_type
        else:
            typed_node["resolved_type"] = expected_type
        return _emit_expr(ctx, typed_node)
    return _emit_expr(ctx, node)


def _emit_listcomp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = node.get("elt")
    generators = _list(node, "generators")
    rt = _str(node, "resolved_type")
    inner_type = "PyObj"
    if rt.startswith("list[") and rt.endswith("]"):
        inner_type = rt[5:-1]
    temp_name = _next_temp(ctx, "listcomp")
    lines = [
        "(block:",
        "  var " + temp_name + " = newSeq[" + _render_type(ctx, inner_type) + "]()",
    ]
    lines.extend(_emit_comp_loops(ctx, generators, temp_name + ".add(" + _emit_expr(ctx, elt) + ")", indent="  "))
    lines.append("  " + temp_name)
    lines.append(")")
    return "\n".join(lines)


def _emit_setcomp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    elt = node.get("elt")
    generators = _list(node, "generators")
    rt = _str(node, "resolved_type")
    inner_type = "PyObj"
    if rt.startswith("set[") and rt.endswith("]"):
        inner_type = rt[4:-1]
    temp_name = _next_temp(ctx, "setcomp")
    lines = [
        "(block:",
        "  var " + temp_name + " = initHashSet[" + _render_type(ctx, inner_type) + "]()",
    ]
    lines.extend(_emit_comp_loops(ctx, generators, temp_name + ".incl(" + _emit_expr(ctx, elt) + ")", indent="  "))
    lines.append("  " + temp_name)
    lines.append(")")
    return "\n".join(lines)


def _emit_dictcomp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    key_node = node.get("key")
    value_node = node.get("value")
    generators = _list(node, "generators")
    rt = _str(node, "resolved_type")
    key_type = "string"
    value_type = "PyObj"
    if rt.startswith("dict[") and rt.endswith("]"):
        parts = _split_generic_args(rt[5:-1])
        if len(parts) == 2:
            key_type = parts[0]
            value_type = parts[1]
    temp_name = _next_temp(ctx, "dictcomp")
    lines = [
        "(block:",
        "  var " + temp_name + " = initTable[" + _render_type(ctx, key_type) + ", " + _render_type(ctx, value_type) + "]()",
    ]
    lines.extend(
        _emit_comp_loops(
            ctx,
            generators,
            temp_name + "[" + _emit_expr(ctx, key_node) + "] = " + _emit_expr(ctx, value_node),
            indent="  ",
        )
    )
    lines.append("  " + temp_name)
    lines.append(")")
    return "\n".join(lines)


def _emit_comp_loops(
    ctx: EmitContext,
    generators: list[JsonVal],
    leaf_stmt: str,
    *,
    indent: str,
    index: int = 0,
) -> list[str]:
    if index >= len(generators):
        parts = leaf_stmt.splitlines()
        if len(parts) == 0:
            return [indent]
        return [indent + part for part in parts]
    gen = generators[index]
    if not isinstance(gen, dict):
        return [indent + leaf_stmt]
    target_code = _emit_expr(ctx, gen.get("target"))
    iter_code = _emit_expr(ctx, gen.get("iter"))
    lines = [indent + "for " + target_code + " in " + iter_code + ":"]
    body_indent = indent + "  "
    ifs = _list(gen, "ifs")
    if len(ifs) > 0:
        filter_code = " and ".join(_emit_condition_expr(ctx, f) for f in ifs)
        lines.append(body_indent + "if " + filter_code + ":")
        body_indent += "  "
    lines.extend(_emit_comp_loops(ctx, generators, leaf_stmt, indent=body_indent, index=index + 1))
    return lines


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
    arg_types_dict = _dict(node, "arg_types")
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
        at = ""
        if len(arg_types_dict) > 0:
            val = arg_types_dict.get(arg_name)
            if isinstance(val, str):
                at = val
        elif idx < len(arg_types):
            val = arg_types[idx]
            if isinstance(val, str):
                at = val
        if at != "" and at != "unknown":
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
    if runtime_call == "" and builtin_name == "":
        runtime_symbol = _str(node, "runtime_symbol")
        if runtime_symbol != "":
            runtime_call = runtime_symbol
    resolved = ""
    if runtime_call != "" and runtime_call in ctx.mapping.calls:
        resolved = ctx.mapping.calls[runtime_call]
    if resolved == "" and builtin_name != "" and builtin_name in ctx.mapping.calls:
        resolved = ctx.mapping.calls[builtin_name]
    if resolved == "" and adapter_kind == "method":
        method_key = "method." + builtin_name
        if method_key in ctx.mapping.calls:
            resolved = ctx.mapping.calls[method_key]
    return resolved


def _expected_arg_type_at(ctx: EmitContext, func_node: JsonVal, idx: int) -> str:
    if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
        raw_name = _str(func_node, "id")
        safe_name = _nim_name(ctx, raw_name)
        values: list[str] = []
        if safe_name in ctx.function_arg_types:
            values = ctx.function_arg_types[safe_name]
        elif raw_name in ctx.function_arg_types:
            values = ctx.function_arg_types[raw_name]
        if idx < len(values):
            return _str_at(values, idx)
    return ""


def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    func_node = node.get("func")
    args = _list(node, "args")
    builtin_name = _str(node, "builtin_name")

    def _render_call_arg(arg: JsonVal, expected_type: str = "") -> str:
        if isinstance(arg, dict):
            expected = _str(arg, "call_arg_type")
            if expected == "":
                expected = expected_type
            if expected != "":
                return _emit_expr_with_expected_type(ctx, arg, expected)
        return _emit_expr(ctx, arg)

    if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
        bare_name = _str(func_node, "id")
        if bare_name == "bool" and len(args) == 1:
            if isinstance(args[0], dict):
                _arg_node_bool = _as_dict(_json_at(args, 0))
                _check_node_bool = _arg_node_bool
                if _str(_arg_node_bool, "kind") in ("Unbox", "Box"):
                    _iv_bool = _arg_node_bool.get("value")
                    if isinstance(_iv_bool, dict):
                        _check_node_bool = _iv_bool
                _arg_rt_bool = _str(_check_node_bool, "resolved_type")
                if is_general_union_type(_arg_rt_bool):
                    return _emit_union_to_bool(ctx, _emit_expr(ctx, _check_node_bool), _arg_rt_bool)
            return "py_bool(" + _emit_expr(ctx, args[0]) + ")"
        if bare_name == "str" and len(args) == 1:
            if isinstance(args[0], dict):
                _arg_node_str = _as_dict(_json_at(args, 0))
                # look through Unbox/Box wrappers to find the real type
                if _str(_arg_node_str, "kind") in ("Unbox", "Box"):
                    _inner_val = _arg_node_str.get("value")
                    if isinstance(_inner_val, dict):
                        _inner_rt = _str(_inner_val, "resolved_type")
                        if is_general_union_type(_inner_rt):
                            return _emit_union_to_string(ctx, _emit_expr(ctx, _inner_val), _inner_rt)
                _arg_rt_str = _str(_arg_node_str, "resolved_type")
                if is_general_union_type(_arg_rt_str):
                    return _emit_union_to_string(ctx, _emit_expr(ctx, _arg_node_str), _arg_rt_str)
            return "py_str(" + _emit_expr(ctx, args[0]) + ")"
        if bare_name == "int" and len(args) == 1:
            _INT_POD = ("int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64")
            _call_rt = _str(node, "resolved_type")
            if isinstance(args[0], dict):
                _arg_node_int = _as_dict(_json_at(args, 0))
                # look through Unbox/Box wrappers to find the real type
                _check_node_int = _arg_node_int
                if _str(_arg_node_int, "kind") in ("Unbox", "Box"):
                    _iv = _arg_node_int.get("value")
                    if isinstance(_iv, dict):
                        _check_node_int = _iv
                _arg_rt_int = _str(_check_node_int, "resolved_type")
                if is_general_union_type(_arg_rt_int):
                    _target_int = _call_rt if _call_rt in _INT_POD else "int64"
                    return _target_int + "(" + _emit_union_to_int(ctx, _emit_expr(ctx, _check_node_int), _arg_rt_int) + ")"
            _inner_int = _emit_expr(ctx, args[0])
            if _call_rt in _INT_POD:
                return _call_rt + "(py_int(" + _inner_int + "))"
            return "int64(py_int(" + _inner_int + "))"
        if bare_name == "float" and len(args) == 1:
            return "float64(py_float(" + _emit_expr(ctx, args[0]) + "))"
        if bare_name == "isinstance" and len(args) >= 2:
            return _emit_isinstance(ctx, node, args)

    # Check for runtime call resolution
    runtime_name = _resolve_runtime_call_name(ctx, node)
    resolved_runtime_source = _str(node, "resolved_runtime_source")
    range_runtime_name = ""
    if "range" in ctx.mapping.calls:
        range_runtime_name = ctx.mapping.calls["range"]
    if builtin_name == "range" or (range_runtime_name != "" and runtime_name == range_runtime_name):
        arg_strs: list[str] = []
        arg_idx = 0
        while arg_idx < len(args):
            arg_strs.append(_emit_expr(ctx, _json_at(args, arg_idx)))
            arg_idx += 1
        range_name = range_runtime_name if range_runtime_name != "" else runtime_name
        if len(arg_strs) == 1:
            return range_name + "(0, " + arg_strs[0] + ", 1)"
        if len(arg_strs) == 2:
            return range_name + "(" + arg_strs[0] + ", " + arg_strs[1] + ", 1)"
        return range_name + "(" + ", ".join(arg_strs) + ")"

    if builtin_name in ("bool", "str", "int", "float") and len(args) == 1:
        arg_code = _emit_expr(ctx, args[0])
        if builtin_name == "bool":
            return "py_bool(" + arg_code + ")"
        if builtin_name == "str":
            return "py_str(" + arg_code + ")"
        if builtin_name == "int":
            return "int64(py_int(" + arg_code + "))"
        if builtin_name == "float":
            return "float64(py_float(" + arg_code + "))"

    # isinstance
    semantic_tag = _str(node, "semantic_tag")
    if semantic_tag == "builtin.isinstance" or runtime_name == "py_isinstance":
        return _emit_isinstance(ctx, node, args)

    func_node = node.get("func")
    if (
        isinstance(func_node, dict)
        and _str(func_node, "kind") == "Attribute"
        and runtime_name in (
            "__LIST_APPEND__",
            "__LIST_POP__",
            "__LIST_CLEAR__",
            "__LIST_INDEX__",
            "__DICT_GET__",
            "__DICT_ITEMS__",
            "__DICT_KEYS__",
            "__DICT_VALUES__",
            "__SET_ADD__",
            "__SET_DISCARD__",
            "__SET_REMOVE__",
        )
    ):
        return _emit_method_call(ctx, node, runtime_name, args)

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
    if runtime_name == "collections.deque":
        return _emit_list_ctor(ctx, node, args)

    # Method call on object (attribute call)
    if isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
        owner_node = func_node.get("value")
        attr = _str(func_node, "attr")
        if attr == "deque":
            owner_id = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
            if owner_id == "collections":
                return _emit_list_ctor(ctx, node, args)
        return _emit_method_call(ctx, node, runtime_name, args)

    # Resolved runtime name -> direct call
    if runtime_name != "":
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
            local_name = _str(func_node, "id")
            if resolved_runtime_source == "import_symbol" and local_name != "":
                runtime_name = _emit_name(ctx, func_node)
            if local_name != "" and _last_dot_part(runtime_name) == local_name and local_name in ctx.runtime_imports:
                runtime_name = _emit_name(ctx, func_node)
        if runtime_name == "py_assert_eq" and len(args) >= 2:
            left_raw = _json_at(args, 0)
            right_raw = _json_at(args, 1)
            left_node = _as_dict(left_raw)
            right_node = _as_dict(right_raw)
            left_rt = _str(left_node, "resolved_type") if len(left_node) > 0 else ""
            right_rt = _str(right_node, "resolved_type") if len(right_node) > 0 else ""
            if is_general_union_type(left_rt) and right_rt in ("bool", "int", "int64", "uint8", "float", "float64", "str"):
                rendered_args = [_emit_expr_with_expected_type(ctx, left_node, right_rt), _emit_expr(ctx, args[1])]
                for extra in args[2:]:
                    rendered_args.append(_emit_expr(ctx, extra))
                return runtime_name + "(" + ", ".join(rendered_args) + ")"
            rendered_args = []
            for arg in args:
                rendered_args.append(_emit_expr(ctx, arg))
            return runtime_name + "(" + ", ".join(rendered_args) + ")"
        arg_strs: list[str] = []
        arg_idx = 0
        while arg_idx < len(args):
            expected_arg_type = _expected_arg_type_at(ctx, func_node, arg_idx)
            arg_strs.append(_render_call_arg(_json_at(args, arg_idx), expected_arg_type))
            arg_idx += 1
        if builtin_name == "print":
            rendered_args: list[str] = []
            for arg_code in arg_strs:
                rendered_args.append("py_to_string(" + arg_code + ")")
            return runtime_name + "(" + ", ".join(rendered_args) + ")"
        return runtime_name + "(" + ", ".join(arg_strs) + ")"

    # Constructor call (ClassName(...))
    if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
        fn_name = _str(func_node, "id")
        if fn_name == "bool" and len(args) == 1:
            return "py_bool(" + _emit_expr(ctx, args[0]) + ")"
        if fn_name == "str" and len(args) == 1:
            return "py_str(" + _emit_expr(ctx, args[0]) + ")"
        if fn_name == "int" and len(args) == 1:
            return "int64(py_int(" + _emit_expr(ctx, args[0]) + "))"
        if fn_name == "float" and len(args) == 1:
            return "float64(py_float(" + _emit_expr(ctx, args[0]) + "))"
        if fn_name == "deque":
            return _emit_list_ctor(ctx, node, args)
        if fn_name == "bytes" or fn_name == "bytearray":
            return _emit_bytes_ctor(ctx, fn_name, args)
        if fn_name in ctx.class_names or _is_exception_type_name(ctx, fn_name):
            return _emit_constructor(ctx, fn_name, args)

    # Regular function call
    callee = _emit_expr(ctx, func_node)
    arg_strs: list[str] = []
    arg_idx = 0
    while arg_idx < len(args):
        expected_arg_type = _expected_arg_type_at(ctx, func_node, arg_idx)
        arg_strs.append(_render_call_arg(_json_at(args, arg_idx), expected_arg_type))
        arg_idx += 1
    if callee == "bool" and len(arg_strs) == 1:
        return "py_bool(" + arg_strs[0] + ")"
    if callee == "str" and len(arg_strs) == 1:
        return "py_str(" + arg_strs[0] + ")"
    if callee == "int" and len(arg_strs) == 1:
        return "int64(py_int(" + arg_strs[0] + "))"
    if callee == "float" and len(arg_strs) == 1:
        return "float64(py_float(" + arg_strs[0] + "))"
    if isinstance(func_node, dict) and _str(func_node, "kind") in ("Lambda", "ClosureDef"):
        callee = "(" + callee + ")"
    return callee + "(" + ", ".join(arg_strs) + ")"


def _emit_isinstance(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    if len(args) < 2:
        return "false"
    obj_node = _json_at(args, 0)
    raw_obj_node = _as_dict(obj_node)
    raw_inner = raw_obj_node.get("value")
    if _str(raw_obj_node, "kind") == "Unbox" and isinstance(raw_inner, dict):
        raw_obj_node = _as_dict(raw_inner)
    obj = _emit_expr(ctx, obj_node)
    obj_rt = _str(raw_obj_node, "resolved_type") if len(raw_obj_node) > 0 else ""
    if len(raw_obj_node) > 0 and _str(raw_obj_node, "kind") == "Name":
        storage_rt = ctx.storage_var_types.get(_nim_name(ctx, _str(raw_obj_node, "id")), "")
        if storage_rt != "":
            obj_rt = storage_rt
    type_node = _json_at(args, 1)
    if isinstance(type_node, dict):
        if _str(type_node, "kind") == "Tuple":
            checks: list[str] = []
            for elem in _list(type_node, "elements"):
                if isinstance(elem, dict):
                    checks.append(_emit_isinstance(ctx, node, [args[0], elem]))
            if len(checks) == 0:
                return "false"
            return "(" + " or ".join(checks) + ")"
        type_name = _str(type_node, "id")
        if type_name == "":
            type_name = _str(type_node, "repr")
        if type_name != "":
            primitive_exact = {"bool", "str", "string", "int", "int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8", "float", "float64", "float32"}
            if obj_rt in primitive_exact and type_name in primitive_exact:
                def _norm_pod(t: str) -> str:
                    if t == "int":
                        return "int64"
                    if t == "float":
                        return "float64"
                    if t == "string":
                        return "str"
                    return t
                return "true" if _norm_pod(obj_rt) == _norm_pod(type_name) else "false"
            if type_name in ctx.trait_names and obj_rt in ctx.class_names and _class_implements_trait(ctx, obj_rt, type_name):
                return "true"
            if is_general_union_type(obj_rt):
                for option in union_options(obj_rt):
                    if _union_option_matches_type_name(option, type_name):
                        return "(block:\n  when compiles(" + obj + ".kind):\n    " + obj + ".kind == " + _union_tag_name(obj_rt, option) + "\n  else:\n    py_instanceof(" + obj + ", " + _render_type(ctx, option) + ")\n)"
                return "false"
            return "(" + obj + " of " + _render_type(ctx, type_name) + ")"
    return "false"


def _emit_cast(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    if len(args) == 0:
        return "nil"
    cast_to = _str(node, "resolved_type")
    if cast_to == "":
        cast_to = _str(node, "cast_to")
    arg_raw = _json_at(args, 0)
    arg_node = _as_dict(arg_raw)
    arg_code = _emit_expr(ctx, arg_raw)
    if cast_to == "" or cast_to == "unknown":
        return arg_code
    arg_rt = _str(arg_node, "resolved_type") if len(arg_node) > 0 else ""
    arg_is_dynamic = (
        arg_rt == "unknown"
        or "|" in arg_rt
        or _render_type(ctx, arg_rt) == "PyObj"
    )
    if is_general_union_type(arg_rt):
        if cast_to in ("str",):
            return _emit_union_to_string(ctx, arg_code, arg_rt)
        if cast_to in ("int", "int64"):
            return _emit_union_to_int(ctx, arg_code, arg_rt)
        if cast_to in ("bool",):
            return _emit_union_to_bool(ctx, arg_code, arg_rt)
        if cast_to in ("float", "float64"):
            return _emit_union_to_float(ctx, arg_code, arg_rt)
    if cast_to in ("int", "int64") and arg_is_dynamic:
        return "int64(py_int(" + arg_code + "))"
    if cast_to in ("bool",) and arg_is_dynamic:
        return "py_bool(" + arg_code + ")"
    if cast_to in ("str",) and arg_is_dynamic:
        return "py_str(" + arg_code + ")"
    if cast_to in ("float", "float64") and arg_is_dynamic:
        return "float64(py_float(" + arg_code + "))"
    target_type = _render_type(ctx, cast_to)
    return target_type + "(" + arg_code + ")"


def _emit_isinstance_node(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value_node = node.get("value")
    expected = node.get("expected_type_id")
    obj = _emit_expr(ctx, value_node)
    raw_value_node = value_node
    if isinstance(raw_value_node, dict) and _str(raw_value_node, "kind") == "Unbox" and isinstance(raw_value_node.get("value"), dict):
        raw_value_node = raw_value_node.get("value")
    value_rt = _str(raw_value_node, "resolved_type") if isinstance(raw_value_node, dict) else ""
    if isinstance(raw_value_node, dict) and _str(raw_value_node, "kind") == "Name":
        storage_rt = ctx.storage_var_types.get(_nim_name(ctx, _str(raw_value_node, "id")), "")
        if storage_rt != "":
            value_rt = storage_rt
    expected_name = _str(node, "expected_type_name")
    if expected_name != "":
        primitive_exact = {"bool", "str", "string", "int", "int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8", "float", "float64", "float32"}
        if value_rt in primitive_exact and expected_name in primitive_exact:
            def _norm_pod(t: str) -> str:
                if t == "int":
                    return "int64"
                if t == "float":
                    return "float64"
                if t == "string":
                    return "str"
                return t
            return "true" if _norm_pod(value_rt) == _norm_pod(expected_name) else "false"
        if expected_name == "list" and value_rt.startswith("list["):
            return "true"
        if expected_name == "dict" and value_rt.startswith("dict["):
            return "true"
        if expected_name in ("str", "string") and value_rt in ("str", "string"):
            return "true"
        if expected_name in ("int", "int64") and value_rt in ("int", "int64"):
            return "true"
        if expected_name == "bool" and value_rt == "bool":
            return "true"
        if expected_name in ("float", "float64") and value_rt in ("float", "float64"):
            return "true"
        if expected_name in ctx.trait_names and value_rt in ctx.class_names and _class_implements_trait(ctx, value_rt, expected_name):
            return "true"
        if is_general_union_type(value_rt):
            for option in union_options(value_rt):
                if _union_option_matches_type_name(option, expected_name):
                    return "(block:\n  when compiles(" + obj + ".kind):\n    " + obj + ".kind == " + _union_tag_name(value_rt, option) + "\n  else:\n    py_instanceof(" + obj + ", " + _render_type(ctx, option) + ")\n)"
            return "false"
        return "py_instanceof(" + obj + ", " + _render_type(ctx, expected_name) + ")"
    if isinstance(expected, dict):
        type_name = _str(expected, "type_object_of")
        if type_name != "":
            if type_name in ctx.trait_names and value_rt in ctx.class_names and _class_implements_trait(ctx, value_rt, type_name):
                return "true"
            return "py_instanceof(" + obj + ", " + _render_type(ctx, type_name) + ")"
        expected_id = _str(expected, "id")
        if expected_id == "PYTRA_TID_LIST" and value_rt.startswith("list["):
            return "true"
        if expected_id == "PYTRA_TID_DICT" and value_rt.startswith("dict["):
            return "true"
        builtin_checks = {
            "PYTRA_TID_DICT": "py_is_dict",
            "PYTRA_TID_LIST": "py_is_list",
            "PYTRA_TID_STR": "py_is_str",
            "PYTRA_TID_INT": "py_is_int",
            "PYTRA_TID_BOOL": "py_is_bool",
            "PYTRA_TID_FLOAT": "py_is_float",
        }
        check_name = builtin_checks.get(expected_id, "")
        if check_name != "":
            return check_name + "(" + obj + ")"
        type_name = _str(expected, "type_object_of")
        if type_name == "":
            type_name = expected_id
        if type_name == "":
            type_name = _str(expected, "repr")
        if type_name != "":
            return "py_instanceof(" + obj + ", " + _render_type(ctx, type_name) + ")"
    return "false"


def _emit_method_on_owner(ctx: EmitContext, node: dict[str, JsonVal], method: str, args: list[JsonVal]) -> str:
    func_node = node.get("func")
    owner_code = ""
    owner_rt = ""
    if isinstance(func_node, dict):
        owner_node = func_node.get("value")
        if isinstance(owner_node, dict):
            owner_code = _emit_expr(ctx, owner_node)
            owner_rt = _str(owner_node, "resolved_type")
            if _str(owner_node, "kind") == "Name":
                actual_owner_rt = ctx.var_types.get(owner_code, "")
                if actual_owner_rt == "":
                    actual_owner_rt = ctx.var_types.get(_nim_name(ctx, _str(owner_node, "id")), "")
                if actual_owner_rt != "":
                    owner_rt = actual_owner_rt
    if owner_code == "":
        owner_code = "self"
    arg_strs: list[str] = []
    arg_idx = 0
    while arg_idx < len(args):
        arg_strs.append(_emit_expr(ctx, _json_at(args, arg_idx)))
        arg_idx += 1
    if owner_rt.startswith("list[") and owner_rt.endswith("]") and len(arg_strs) > 0:
        inner_type = owner_rt[5:-1]
        if is_general_union_type(inner_type):
            arg_strs[0] = _maybe_cast_expr_to_type(ctx, arg_strs[0], args[0], inner_type)
    if is_general_union_type(owner_rt):
        dict_option = ""
        owner_options: list[str] = union_options(owner_rt)
        owner_option_idx = 0
        while owner_option_idx < len(owner_options):
            option = _str_at(owner_options, owner_option_idx)
            if option.startswith("dict["):
                dict_option = option
                break
            owner_option_idx += 1
        if dict_option != "":
            dict_expr = _emit_union_case_access(ctx, owner_code, owner_rt, dict_option, fallback="default(" + _render_type(ctx, dict_option) + ")")
            if method == "pairs":
                return dict_expr + ".pairs"
            if method == "keys":
                return dict_expr + ".keys"
            if method == "values":
                return dict_expr + ".values"
    if owner_rt.startswith("list[str]") and method == "find" and len(arg_strs) > 0:
        return owner_code + ".find(py_str(" + arg_strs[0] + "))"
    if method.endswith("(0"):
        return owner_code + "." + method + ")"
    return owner_code + "." + method + "(" + ", ".join(arg_strs) + ")"


def _emit_list_pop(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    func_node = node.get("func")
    owner_code = ""
    owner_rt = ""
    if isinstance(func_node, dict):
        owner_node = func_node.get("value")
        if isinstance(owner_node, dict):
            owner_code = _emit_expr(ctx, owner_node)
            owner_rt = _str(owner_node, "resolved_type")
    if owner_code == "":
        owner_code = "self"
    call = ""
    if len(args) > 0:
        idx_code = _emit_expr(ctx, args[0])
        call = "py_runtime.pop(" + owner_code + ", " + idx_code + ")"
    else:
        call = "py_runtime.pop(" + owner_code + ")"
    if owner_rt in ("bytes", "bytearray", "list[byte]", "list[uint8]"):
        expected_rt = _str(node, "resolved_type")
        if expected_rt in ("int", "int64"):
            return "int64(" + call + ")"
    return call


def _emit_dict_get(ctx: EmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    func_node = node.get("func")
    owner_code = ""
    owner_rt = ""
    call_rt = _str(node, "resolved_type")
    if isinstance(func_node, dict):
        owner_node = func_node.get("value")
        if isinstance(owner_node, dict):
            owner_code = _emit_expr(ctx, owner_node)
            owner_rt = _str(owner_node, "resolved_type")
    if owner_code == "":
        owner_code = "self"
    if len(args) == 0:
        return owner_code
    key_code = _emit_expr(ctx, args[0])
    if len(args) > 1:
        if owner_rt.startswith("dict[") and owner_rt.endswith("]"):
            owner_parts: list[str] = _split_generic_args(owner_rt[5:-1])
            if len(owner_parts) == 2 and is_general_union_type(_str_at(owner_parts, 1)):
                owner_value_type = _str_at(owner_parts, 1)
                default_code = _emit_expr_with_expected_type(ctx, args[1], owner_value_type)
                default_code = _maybe_cast_expr_to_type(ctx, default_code, args[1], owner_value_type)
            else:
                default_code = _emit_expr(ctx, args[1])
        else:
            default_code = _emit_expr(ctx, args[1])
        if _render_type(ctx, owner_rt).startswith("Table[") and _render_type(ctx, owner_rt).endswith(", PyObj]"):
            default_code = _maybe_cast_expr_to_type(ctx, default_code, args[1], "PyObj")
        return owner_code + ".getOrDefault(" + key_code + ", " + default_code + ")"
    if owner_rt.startswith("dict[") and owner_rt.endswith("]"):
        owner_parts: list[str] = _split_generic_args(owner_rt[5:-1])
        if len(owner_parts) == 2 and is_general_union_type(_str_at(owner_parts, 1)):
            owner_value_type = _str_at(owner_parts, 1)
            return owner_code + ".getOrDefault(" + key_code + ", default(" + _render_type(ctx, owner_value_type) + "))"
    if _render_type(ctx, owner_rt).startswith("Table[") and _render_type(ctx, owner_rt).endswith(", PyObj]"):
        return "(if " + owner_code + ".hasKey(" + key_code + "): " + owner_code + "[" + key_code + "] else: nil)"
    return "(if " + owner_code + ".hasKey(" + key_code + "): py_box(" + owner_code + "[" + key_code + "]) else: nil)"


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
        rt = _str(node, "resolved_type")
        inner_type = ""
        if rt.startswith("set[") and rt.endswith("]"):
            inner_type = rt[4:-1]
        arg_codes: list[str] = []
        for arg in args:
            arg_code = _emit_expr(ctx, arg)
            if (
                inner_type in ("int", "int64", "uint8", "float", "float64")
                and isinstance(arg, dict)
                and _str(arg, "kind") == "Constant"
            ):
                arg_code = _render_type(ctx, inner_type) + "(" + arg_code + ")"
            arg_codes.append(arg_code)
        return "[" + ", ".join(arg_codes) + "].toHashSet"
    rt = _str(node, "resolved_type")
    if rt.startswith("set[") and rt.endswith("]"):
        inner = rt[4:-1]
        return "initHashSet[" + _render_type(ctx, inner) + "]()"
    return "initHashSet[PyObj]()"


def _emit_bytes_ctor(ctx: EmitContext, ctor_name: str, args: list[JsonVal]) -> str:
    if len(args) == 0:
        return "newSeq[uint8]()"
    arg_node = args[0]
    arg_code = _emit_expr(ctx, arg_node)
    arg_rt = _str(arg_node, "resolved_type") if isinstance(arg_node, dict) else ""
    if arg_rt in ("int", "int64"):
        return "newSeq[uint8](" + arg_code + ")"
    if isinstance(arg_node, dict) and _str(arg_node, "kind") == "List":
        elements = _list(arg_node, "elements")
        return "@[" + ", ".join("uint8(" + _emit_expr(ctx, element) + ")" for element in elements) + "]"
    if arg_rt in ("bytes", "bytearray"):
        return "@(" + arg_code + ")"
    if arg_rt.startswith("list[") or arg_rt.startswith("tuple[") or arg_rt.startswith("set["):
        return "(" + arg_code + ").mapIt(uint8(it))"
    return "@(" + arg_code + ")"


def _emit_method_call(ctx: EmitContext, node: dict[str, JsonVal], runtime_name: str, args: list[JsonVal]) -> str:
    func_node = node.get("func")
    if not isinstance(func_node, dict):
        return ""
    owner_node = func_node.get("value")
    attr = _str(func_node, "attr")
    semantic_tag = _str(node, "semantic_tag")
    method_tag = runtime_name if runtime_name != "" else semantic_tag
    owner_code = _emit_expr(ctx, owner_node)
    owner_rt = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Subscript":
        if method_tag in {
            "__LIST_APPEND__",
            "__LIST_POP__",
            "__LIST_CLEAR__",
            "__SET_ADD__",
            "__SET_DISCARD__",
            "__SET_REMOVE__",
            "__DICT_SETDEFAULT__",
            "stdlib.method.append",
            "stdlib.method.pop",
            "stdlib.method.clear",
            "stdlib.method.add",
            "stdlib.method.discard",
            "stdlib.method.remove",
            "stdlib.method.setdefault",
        }:
            owner_code = _emit_subscript_target(ctx, owner_node)
    if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Name":
        actual_owner_rt = ctx.var_types.get(owner_code, "")
        if actual_owner_rt == "":
            actual_owner_rt = ctx.var_types.get(_nim_name(ctx, _str(owner_node, "id")), "")
        if actual_owner_rt != "" and (owner_rt in ("", "unknown") or is_general_union_type(owner_rt)):
            owner_rt = actual_owner_rt
    if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Attribute" and owner_rt in ("", "unknown"):
        base_node = owner_node.get("value")
        base_rt = _str(base_node, "resolved_type") if isinstance(base_node, dict) else ""
        if isinstance(base_node, dict) and _str(base_node, "id") == "self":
            base_rt = ctx.current_class
        field_rt = ctx.class_fields.get(base_rt, {}).get(_str(owner_node, "attr"), "")
        if field_rt != "":
            owner_rt = field_rt
    arg_strs: list[str] = []
    arg_idx = 0
    while arg_idx < len(args):
        arg_strs.append(_emit_expr(ctx, _json_at(args, arg_idx)))
        arg_idx += 1

    if isinstance(owner_node, dict):
        owner_id = _str(owner_node, "id")
        has_static_method = False
        if owner_id in ctx.class_static_methods:
            static_methods = ctx.class_static_methods[owner_id]
            has_static_method = attr in static_methods
        if owner_id in ctx.class_names and (has_static_method or owner_rt == "type"):
            return _safe_nim_ident(attr) + "(" + ", ".join(arg_strs) + ")"

    if is_general_union_type(owner_rt):
        dict_option = ""
        owner_options: list[str] = union_options(owner_rt)
        owner_option_idx = 0
        while owner_option_idx < len(owner_options):
            option = _str_at(owner_options, owner_option_idx)
            if option.startswith("dict["):
                dict_option = option
                break
            owner_option_idx += 1
        if dict_option != "":
            dict_expr = _emit_union_case_access(ctx, owner_code, owner_rt, dict_option, fallback="default(" + _render_type(ctx, dict_option) + ")")
            if attr == "items":
                return "toSeq(" + dict_expr + ".pairs)"
            if attr == "keys":
                return "toSeq(" + dict_expr + ".keys)"
            if attr == "values":
                return "toSeq(" + dict_expr + ".values)"
            if attr == "get":
                key_code = arg_strs[0] if len(arg_strs) > 0 else '""'
                dict_parts = _split_generic_args(dict_option[5:-1])
                dict_value_type = "PyObj"
                if len(dict_parts) > 1:
                    dict_value_type = _str_at(dict_parts, 1)
                if len(arg_strs) > 1:
                    default_code = _maybe_cast_expr_to_type(ctx, arg_strs[1], args[1], dict_value_type)
                    return dict_expr + ".getOrDefault(" + key_code + ", " + default_code + ")"
                return dict_expr + ".getOrDefault(" + key_code + ", default(" + _render_type(ctx, dict_value_type) + "))"

    # str methods
    if owner_rt == "str" and runtime_name != "":
        return runtime_name + "(" + owner_code + ", " + ", ".join(arg_strs) + ")" if len(arg_strs) > 0 else runtime_name + "(" + owner_code + ")"

    # list methods
    if owner_rt.startswith("list[") or owner_rt == "list" or _is_nim_byte_seq_type(ctx, owner_rt):
        if runtime_name == "__LIST_CLEAR__" or method_tag == "stdlib.method.clear":
            return owner_code + ".setLen(0)"
        if runtime_name == "__LIST_POP__" or method_tag == "stdlib.method.pop":
            pop_call = ""
            if len(arg_strs) == 0:
                pop_call = "py_runtime.pop(" + owner_code + ")"
            else:
                pop_call = "py_runtime.pop(" + owner_code + ", " + ", ".join(arg_strs) + ")"
            if _is_nim_byte_seq_type(ctx, owner_rt):
                expected_rt = _str(node, "resolved_type")
                if expected_rt in ("int", "int64"):
                    return "int64(" + pop_call + ")"
            return pop_call
        if _is_nim_byte_seq_type(ctx, owner_rt):
            if (runtime_name == "__LIST_APPEND__" or method_tag == "stdlib.method.append" or attr == "append") and len(arg_strs) == 1:
                return owner_code + ".add(uint8(" + arg_strs[0] + "))"
            if (runtime_name == "py_extend" or method_tag == "stdlib.method.extend") and len(arg_strs) == 1:
                return owner_code + ".add(" + arg_strs[0] + ".mapIt(uint8(it)))"
        if (runtime_name == "__LIST_APPEND__" or method_tag == "stdlib.method.append" or attr == "append") and len(args) == 1 and owner_rt.startswith("list[") and owner_rt.endswith("]"):
            item_type = owner_rt[5:-1]
            item_code = _emit_expr_with_expected_type(ctx, args[0], item_type)
            item_code = _maybe_cast_expr_to_type(ctx, item_code, args[0], item_type)
            return owner_code + ".add(" + item_code + ")"
        if runtime_name == "__LIST_APPEND__" or runtime_name == "py_extend" or method_tag in ("stdlib.method.append", "stdlib.method.extend"):
            return owner_code + ".add(" + ", ".join(arg_strs) + ")"
        if runtime_name == "__LIST_INDEX__" or method_tag == "stdlib.method.index":
            if owner_rt.startswith("list[str]") and len(arg_strs) > 0:
                return owner_code + ".find($(" + arg_strs[0] + "))"
            return owner_code + ".find(" + ", ".join(arg_strs) + ")"
        if runtime_name != "":
            return owner_code + "." + runtime_name + "(" + ", ".join(arg_strs) + ")"

    if owner_rt == "deque" or owner_rt.startswith("deque["):
        if runtime_name == "__LIST_APPEND__" or method_tag == "stdlib.method.append":
            return owner_code + ".add(" + ", ".join(arg_strs) + ")"
        if attr == "appendleft" and len(arg_strs) == 1:
            return owner_code + ".insert(" + arg_strs[0] + ", 0)"
        if attr == "popleft":
            return "py_runtime.pop(" + owner_code + ", 0)"
        if runtime_name == "__LIST_POP__" or method_tag == "stdlib.method.pop":
            return "py_runtime.pop(" + owner_code + ")"
        if runtime_name == "__LIST_CLEAR__" or method_tag == "stdlib.method.clear":
            return owner_code + ".setLen(0)"

    # dict methods
    if owner_rt.startswith("dict[") or owner_rt == "dict":
        if runtime_name == "__DICT_GET__" or runtime_name == "dict.get" or method_tag == "stdlib.method.get":
            return _emit_dict_get(ctx, node, args)
        if runtime_name == "__DICT_KEYS__" or runtime_name == "dict.keys" or method_tag == "stdlib.method.keys":
            return "toSeq(" + owner_code + ".keys)"
        if runtime_name == "__DICT_VALUES__" or runtime_name == "dict.values" or method_tag == "stdlib.method.values":
            return "toSeq(" + owner_code + ".values)"
        if runtime_name == "__DICT_ITEMS__" or runtime_name == "dict.items" or method_tag == "stdlib.method.items":
            return "toSeq(" + owner_code + ".pairs)"
        if runtime_name == "__DICT_POP__" or method_tag == "stdlib.method.pop":
            if len(arg_strs) > 0:
                temp = _next_temp(ctx, "tmp_dict_value")
                return "(let " + temp + " = " + owner_code + "[" + arg_strs[0] + "]; " + owner_code + ".del(" + arg_strs[0] + "); " + temp + ")"
        if runtime_name == "py_update" or method_tag == "stdlib.method.update":
            if len(arg_strs) > 0:
                return "(for k, v in " + arg_strs[0] + ": " + owner_code + "[k] = v)"
        if runtime_name == "__DICT_SETDEFAULT__" or method_tag == "stdlib.method.setdefault":
            if len(arg_strs) == 2:
                return owner_code + ".mgetOrPut(" + arg_strs[0] + ", " + arg_strs[1] + ")"
            if len(arg_strs) == 1:
                return owner_code + ".mgetOrPut(" + arg_strs[0] + ", nil)"

    # set methods
    if owner_rt.startswith("set[") or owner_rt == "set":
        if runtime_name == "__SET_ADD__" or method_tag == "stdlib.method.add":
            return owner_code + ".incl(" + ", ".join(arg_strs) + ")"
        if runtime_name == "py_update" or method_tag == "stdlib.method.update":
            if len(arg_strs) > 0:
                return "py_update(" + owner_code + ", " + arg_strs[0] + ")"
        if runtime_name == "__SET_DISCARD__" or method_tag == "stdlib.method.discard":
            return owner_code + ".excl(" + ", ".join(arg_strs) + ")"
        if runtime_name == "__SET_REMOVE__" or method_tag == "stdlib.method.remove":
            return owner_code + ".excl(" + ", ".join(arg_strs) + ")"
        if runtime_name == "__SET_CLEAR__" or method_tag == "stdlib.method.clear":
            return owner_code + ".clear()"

    # super() call
    if attr == "__init__" and _is_super_call(owner_node):
        base = ctx.current_base_class
        if base == "":
            base = ctx.class_bases.get(ctx.current_class, "")
        if base != "":
            if _is_exception_type_name(ctx, base) and len(arg_strs) > 0:
                return "self.msg = " + arg_strs[0]
            return "initInto" + _nim_name(ctx, base) + "(" + ", ".join(["self"] + arg_strs) + ")"
        return "discard"

    if _is_super_call(owner_node):
        base = ctx.current_base_class
        if base == "":
            base = ctx.class_bases.get(ctx.current_class, "")
        if base != "":
            return "procCall " + _safe_nim_ident(attr) + "(" + _safe_nim_ident(base) + "(self)" + (", " + ", ".join(arg_strs) if len(arg_strs) > 0 else "") + ")"

    # General method call
    return owner_code + "." + _safe_nim_ident(attr) + "(" + ", ".join(arg_strs) + ")"


def _emit_constructor(ctx: EmitContext, class_name: str, args: list[JsonVal]) -> str:
    safe_name = _nim_name(ctx, class_name)
    arg_strs: list[str] = []
    arg_idx = 0
    while arg_idx < len(args):
        arg_strs.append(_emit_expr(ctx, _json_at(args, arg_idx)))
        arg_idx += 1

    if class_name in ctx.class_names:
        return "init" + safe_name + "(" + ", ".join(arg_strs) + ")"

    # Builtin exception classes
    if _is_exception_type_name(ctx, class_name):
        msg = arg_strs[0] if len(arg_strs) > 0 else _nim_string(class_name)
        exc_type = _nim_exception_type_name(ctx, class_name)
        if exc_type == "":
            exc_type = "CatchableError"
        return "newException(" + exc_type + ", " + msg + ")"

    return "init" + safe_name + "(" + ", ".join(arg_strs) + ")"


def _for_target_code(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    target_plan = _dict(node, "target_plan")
    target = node.get("target")
    if len(target_plan) > 0:
        kind = _str(target_plan, "kind")
        if kind in ("NameTarget", "Name"):
            name = _str(target_plan, "id")
            if name != "":
                return _nim_name(ctx, name)
    if isinstance(target, dict):
        return _emit_expr(ctx, target)
    return "_"


def _declare_loop_target(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_plan = _dict(node, "target_plan")
    target = node.get("target")
    if len(target_plan) > 0:
        name = _str(target_plan, "id")
        if name != "":
            ctx.declared_vars.add(_nim_name(ctx, name))
        return
    if isinstance(target, dict):
        tname = _str(target, "id")
        if tname != "":
            ctx.declared_vars.add(_nim_name(ctx, tname))


def _for_target_type(node: dict[str, JsonVal]) -> str:
    target_plan = _dict(node, "target_plan")
    if len(target_plan) > 0:
        target_type = _str(target_plan, "target_type")
        if target_type != "":
            return target_type
        return _str(target_plan, "resolved_type")
    target = node.get("target")
    if isinstance(target, dict):
        return _str(target, "resolved_type")
    return ""


def _emit_for_core_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    iter_plan = _dict(node, "iter_plan")
    body = _list(node, "body")
    orelse = _list(node, "orelse")
    target_code = _for_target_code(ctx, node)
    saved_declared = _copy_str_set(ctx.declared_vars)
    _declare_loop_target(ctx, node)

    plan_kind = _str(iter_plan, "kind")
    if plan_kind == "StaticRangeForPlan":
        start_node = iter_plan.get("start")
        stop_node = iter_plan.get("stop")
        step_node = iter_plan.get("step")
        start_code = _emit_expr(ctx, start_node) if isinstance(start_node, dict) else "0"
        stop_code = _emit_expr(ctx, stop_node) if isinstance(stop_node, dict) else "0"

        step_val: int = 0
        step_has_value = False
        if isinstance(step_node, dict):
            step_val = _get_static_int_literal(step_node, 2147483647)
            if step_val != 2147483647:
                step_has_value = True

        if step_has_value and step_val == -1:
            _emit(ctx, "for " + target_code + " in countdown(" + start_code + ", (" + stop_code + " + 1)):")
        elif step_has_value and step_val < 0:
            _emit(ctx, "for " + target_code + " in countdown(" + start_code + ", (" + stop_code + " + 1), " + str(-step_val) + "):")
        elif step_has_value and step_val == 1:
            _emit(ctx, "for " + target_code + " in " + start_code + " ..< " + stop_code + ":")
        elif step_has_value and step_val > 1:
            _emit(ctx, "for " + target_code + " in countup(" + start_code + ", " + stop_code + " - 1, " + str(step_val) + "):")
        elif isinstance(step_node, dict):
            step_code = _emit_expr(ctx, step_node)
            _emit(ctx, "for " + target_code + " in py_range(" + start_code + ", " + stop_code + ", " + step_code + "):")
        else:
            _emit(ctx, "for " + target_code + " in " + start_code + " ..< " + stop_code + ":")
        ctx.loop_depth += 1
        ctx.indent_level += 1
        _emit_body(ctx, body)
        ctx.indent_level -= 1
        ctx.loop_depth -= 1
        ctx.declared_vars = saved_declared
    else:
        iter_expr = iter_plan.get("iter_expr")
        if not isinstance(iter_expr, dict):
            iter_expr = node.get("iter")
        iter_code = _emit_expr(ctx, iter_expr)
        target_node = node.get("target")
        if isinstance(target_node, dict) and _str(target_node, "kind") == "Tuple":
            tuple_elements = _list(target_node, "elements")
            raw_target = _next_temp(ctx, "item")
            tuple_types: list[str] = []
            tuple_rt = _str(target_node, "resolved_type")
            if tuple_rt.startswith("tuple[") and tuple_rt.endswith("]"):
                tuple_types = _split_generic_args(tuple_rt[6:-1])
            elif isinstance(iter_expr, dict):
                iter_rt = _str(iter_expr, "resolved_type")
                if iter_rt.startswith("list[tuple[") and iter_rt.endswith("]]"):
                    tuple_types = _split_generic_args(iter_rt[11:-2])
            _emit(ctx, "for " + raw_target + " in " + iter_code + ":")
            ctx.loop_depth += 1
            ctx.indent_level += 1
            for idx, elem in enumerate(tuple_elements):
                if not isinstance(elem, dict):
                    continue
                elem_name = _str(elem, "id")
                if elem_name == "":
                    elem_name = _str(elem, "repr")
                if elem_name == "":
                    continue
                safe = _nim_name(ctx, elem_name)
                elem_code = raw_target + "[" + str(idx) + "]"
                elem_type = tuple_types[idx] if idx < len(tuple_types) else _str(elem, "resolved_type")
                if elem_type in ("str", "string", "bool", "int", "int64", "uint8", "float", "float64"):
                    elem_code = _cast_expr_code(ctx, elem_type, elem_code)
                _emit(ctx, "let " + safe + " = " + elem_code)
            _emit_body(ctx, body)
            ctx.indent_level -= 1
            ctx.loop_depth -= 1
            ctx.declared_vars = saved_declared
            if len(orelse) > 0:
                _emit_body(ctx, orelse)
            return
        target_type = _for_target_type(node)
        castable_target_type = target_type in ("bool", "int", "int64", "uint8", "float", "float64", "str")
        if castable_target_type and target_code != "_":
            raw_target = _next_temp(ctx, "item")
            _emit(ctx, "for " + raw_target + " in " + iter_code + ":")
            ctx.loop_depth += 1
            ctx.indent_level += 1
            _emit(ctx, "let " + target_code + " = " + _cast_expr_code(ctx, target_type, raw_target) + "")
            _emit_body(ctx, body)
            ctx.indent_level -= 1
            ctx.loop_depth -= 1
            ctx.declared_vars = saved_declared
        else:
            _emit(ctx, "for " + target_code + " in " + iter_code + ":")
            ctx.loop_depth += 1
            ctx.indent_level += 1
            _emit_body(ctx, body)
            ctx.indent_level -= 1
            ctx.loop_depth -= 1
            ctx.declared_vars = saved_declared

    if len(orelse) > 0:
        _emit_body(ctx, orelse)


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_body(ctx: EmitContext, body: list[JsonVal]) -> None:
    if len(body) == 0:
        _emit_discard(ctx)
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
                if ctx.pass_directive_block:
                    if text.startswith("Pytra::pass end") or text.startswith("Pytra::pass: end"):
                        ctx.pass_directive_block = False
                    continue
                # Check for Pytra::pass / Pytra::cpp directives
                if text.startswith("Pytra::pass begin") or text.startswith("Pytra::pass: begin"):
                    ctx.pass_directive_block = True
                    continue
                if text.startswith("Pytra::pass ") or text.startswith("Pytra::pass: "):
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
    elif kind == "TupleUnpack":
        _emit_tuple_unpack_stmt(ctx, node)
    elif kind == "AnnAssign":
        _emit_ann_assign_stmt(ctx, node)
    elif kind == "VarDecl":
        _emit_var_decl_stmt(ctx, node)
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
    elif kind == "ForCore":
        _emit_for_core_stmt(ctx, node)
    elif kind == "FunctionDef" or kind == "ClosureDef":
        _emit_function_def(ctx, node)
    elif kind == "ClassDef":
        _emit_class_def(ctx, node)
    elif kind == "Pass":
        _emit_discard(ctx)
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
        if _str(value, "kind") == "Name":
            name = _str(value, "id")
            if name == "continue" or name == "break":
                _emit(ctx, name)
                return
        code = _emit_expr(ctx, value)
        # Docstrings
        if _str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
            doc = value.get("value")
            if isinstance(doc, str):
                _emit(ctx, "## " + doc.replace("\n", "\n## "))
                return
        if _str(value, "kind") == "Call" and _str(value, "resolved_type") not in ("", "None", "unknown", "void"):
            _emit(ctx, "discard " + code)
            return
        _emit(ctx, code)


def _emit_return_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if isinstance(value, dict):
        code = _emit_expr(ctx, value)
        if ctx.current_return_type in ("", "unknown", "None"):
            _emit(ctx, "discard " + code)
            return
        if _render_type(ctx, ctx.current_return_type) == "PyObj":
            code = _maybe_cast_expr_to_type(ctx, code, value, "PyObj")
        _emit(ctx, "return " + code)
    else:
        _emit(ctx, "return")


def _emit_assign_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    declare = _bool(node, "declare")
    decl_type = _str(node, "decl_type")
    raw_target_name = _str(target, "id") if isinstance(target, dict) else ""
    is_tuple_temp = raw_target_name.startswith("__tup_")
    expected_type = _str(target, "resolved_type") if isinstance(target, dict) else ""
    if declare and decl_type != "":
        expected_type = decl_type
    if expected_type in ("", "unknown") and isinstance(value, dict) and _str(value, "kind") == "Call":
        func_node = value.get("func")
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
            inferred_ret = ctx.function_return_types.get(_nim_name(ctx, _str(func_node, "id")), "")
            if inferred_ret not in ("", "unknown"):
                expected_type = inferred_ret
                if decl_type in ("", "unknown"):
                    decl_type = inferred_ret
    boxed_dict = _boxed_dict_inner(value)
    if (
        boxed_dict is not None
        and expected_type.startswith("dict[")
        and "object" in expected_type
        and "|" not in expected_type
    ):
        value_code = _emit_object_dict_literal(ctx, boxed_dict)
    else:
        value_code = _emit_expr_with_expected_type(ctx, value, expected_type)
    if is_tuple_temp and isinstance(value, dict):
        value_code = _emit_expr(ctx, value)
    elif _render_type(ctx, expected_type) == "PyObj":
        value_code = _maybe_cast_expr_to_type(ctx, value_code, value, "PyObj")

    if isinstance(target, dict) and _str(target, "kind") == "Name" and _str(target, "id") == "_":
        _emit(ctx, "discard " + value_code)
        return

    # Tuple assignment
    if isinstance(target, dict) and _str(target, "kind") == "Tuple":
        elements = _list(target, "elements")
        if len(elements) > 0:
            temp = _next_temp(ctx, "tup")
            tuple_value_code = _emit_expr(ctx, value) if isinstance(value, dict) else value_code
            _emit(ctx, "let " + temp + " = " + tuple_value_code)
            for idx, elem in enumerate(elements):
                elem_name = ""
                if isinstance(elem, dict):
                    elem_name = _str(elem, "id")
                    if elem_name == "":
                        elem_name = _str(elem, "repr")
                if elem_name != "":
                    safe = _nim_name(ctx, elem_name)
                    if ctx.loop_depth > 0:
                        _emit(ctx, "let " + safe + " = " + temp + "[" + str(idx) + "]")
                    elif safe in ctx.declared_vars:
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
        target_value = target.get("value")
        target_owner_rt = _str(target_value, "resolved_type") if isinstance(target_value, dict) else ""
        target_rt = _str(target, "resolved_type")
        if _render_type(ctx, target_owner_rt).startswith("Table[") and _render_type(ctx, target_owner_rt).endswith(", PyObj]") and isinstance(value, dict):
            value_code = _maybe_cast_expr_to_type(ctx, value_code, value, "PyObj")
        if (
            target_rt in ("byte", "uint8")
            or target_owner_rt in ("bytes", "bytearray", "list[byte]", "list[uint8]")
        ) and isinstance(value, dict):
            value_rt = _str(value, "resolved_type")
            if value_rt in ("int", "int64") and not value_code.startswith("uint8("):
                value_code = "uint8(" + value_code + ")"
        target_code = _emit_subscript_target(ctx, target)
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
        rt = decl_type if decl_type != "" else (_str(target, "resolved_type") if isinstance(target, dict) else "")
        if rt == "" and isinstance(value, dict):
            rt = _str(value, "resolved_type")
        ann = _type_annotation(ctx, rt)
        if ((_is_top_level_union_type(rt) and "None" not in rt and _render_type(ctx, rt) == "PyObj") or rt.startswith("tuple[")):
            ann = ""
        if (
            isinstance(value, dict)
            and _str(value, "kind") in ("BinOp", "IfExp")
            and rt in ("int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float32", "float64")
        ):
            value_code = _render_type(ctx, rt) + "(" + value_code + ")"
        if _should_emit_list_alias_template(rt, value):
            _emit(ctx, "template " + safe + ": untyped = " + value_code)
        else:
            _emit(ctx, "var " + safe + ann + " = " + value_code)
            ctx.declared_vars.add(safe)
        if rt != "":
            ctx.var_types[safe] = rt


def _emit_var_decl_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    decl_type = _str(node, "type")
    if name == "":
        return
    safe = _nim_name(ctx, name)
    if safe in ctx.declared_vars:
        return
    ann = _type_annotation(ctx, decl_type)
    zero = nim_zero_value(decl_type)
    _emit(ctx, "var " + safe + ann + " = " + zero)
    ctx.declared_vars.add(safe)
    if decl_type != "":
        ctx.var_types[safe] = decl_type


def _emit_tuple_unpack_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    targets = _list(node, "targets")
    value = node.get("value")
    if len(targets) == 0 or not isinstance(value, dict):
        return
    temp = _next_temp(ctx, "tup_unpack")
    _emit(ctx, "let " + temp + " = " + _emit_expr(ctx, value))
    for idx, target in enumerate(targets):
        if not isinstance(target, dict):
            continue
        target_name = _str(target, "id")
        if target_name == "":
            target_name = _str(target, "repr")
        if target_name == "":
            continue
        safe = _nim_name(ctx, target_name)
        rt = _str(target, "resolved_type")
        ann = _type_annotation(ctx, rt)
        if safe in ctx.declared_vars:
            _emit(ctx, safe + " = " + temp + "[" + str(idx) + "]")
        else:
            _emit(ctx, "var " + safe + ann + " = " + temp + "[" + str(idx) + "]")
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

    if isinstance(target, dict) and _str(target, "kind") == "Attribute" and isinstance(value, dict):
        target_code = _emit_expr(ctx, target)
        value_code = _emit_expr_with_expected_type(ctx, value, decl_type)
        if _render_type(ctx, decl_type) == "PyObj":
            value_code = _maybe_cast_expr_to_type(ctx, value_code, value, "PyObj")
        if (
            decl_type in ("byte", "uint8")
            and _str(value, "resolved_type") == "str"
            and not value_code.startswith("uint8(py_ord(")
        ):
            value_code = "uint8(py_ord(" + value_code + "))"
        _emit(ctx, target_code + " = " + value_code)
        return

    target_name = ""
    if isinstance(target, dict):
        target_name = _str(target, "id")
        if target_name == "":
            target_name = _str(target, "repr")
    elif isinstance(target, str):
        target_name = target

    if target_name == "":
        if isinstance(target, dict) and _str(target, "kind") == "Attribute" and isinstance(value, dict):
            target_code = _emit_expr(ctx, target)
            value_code = _emit_expr_with_expected_type(ctx, value, decl_type)
            if _is_top_level_union_type(decl_type):
                value_code = _maybe_cast_expr_to_type(ctx, value_code, value, "PyObj")
            _emit(ctx, target_code + " = " + value_code)
        return

    safe = _nim_name(ctx, target_name)
    ann = _type_annotation(ctx, decl_type)
    if ((_is_top_level_union_type(decl_type) and "None" not in decl_type and _render_type(ctx, decl_type) == "PyObj") or decl_type.startswith("tuple[")):
        ann = ""

    if isinstance(value, dict):
        boxed_dict = _boxed_dict_inner(value)
        if (
            boxed_dict is not None
            and decl_type.startswith("dict[")
            and "object" in decl_type
            and "|" not in decl_type
        ):
            value_code = _emit_object_dict_literal(ctx, boxed_dict)
        else:
            value_code = _emit_expr_with_expected_type(ctx, value, decl_type)
        if _render_type(ctx, decl_type) == "PyObj":
            value_code = _maybe_cast_expr_to_type(ctx, value_code, value, "PyObj")
        if (
            decl_type in ("byte", "uint8")
            and _str(value, "resolved_type") == "str"
            and not value_code.startswith("uint8(py_ord(")
        ):
            value_code = "uint8(py_ord(" + value_code + "))"
        if (
            _str(value, "kind") in ("BinOp", "IfExp")
            and decl_type in ("int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float32", "float64")
        ):
            value_code = _render_type(ctx, decl_type) + "(" + value_code + ")"
        if safe in ctx.declared_vars:
            _emit(ctx, safe + " = " + value_code)
        else:
            if _should_emit_list_alias_template(decl_type, value):
                _emit(ctx, "template " + safe + ": untyped = " + value_code)
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
    value_rt = ""
    if isinstance(target, dict):
        target_rt = _str(target, "resolved_type")
        if _str(target, "kind") == "Name":
            actual_target_rt = ctx.var_types.get(_nim_name(ctx, _str(target, "id")), "")
            if actual_target_rt != "":
                target_rt = actual_target_rt
    if isinstance(value, dict):
        value_rt = _str(value, "resolved_type")
        if _str(value, "kind") == "Name":
            actual_value_rt = ctx.var_types.get(_nim_name(ctx, _str(value, "id")), "")
            if actual_value_rt != "":
                value_rt = actual_value_rt

    if (
        target_rt in ("int", "int64", "float", "float64", "uint8")
        and value_rt != ""
        and value_rt != target_rt
        and value_rt in ("int", "int64", "float", "float64", "uint8")
    ):
        value_code = _render_type(ctx, target_rt) + "(" + value_code + ")"
    elif target_rt in ("int", "int64") and (value_rt in ("", "unknown") or _render_type(ctx, value_rt) == "PyObj"):
        value_code = "int64(py_int(" + value_code + "))"
    elif target_rt in ("float", "float64") and (value_rt in ("", "unknown") or _render_type(ctx, value_rt) == "PyObj"):
        value_code = "float64(py_float(" + value_code + "))"

    # str += str -> &=
    if op == "Add" and target_rt == "str":
        _emit(ctx, target_code + " &= " + value_code)
        return

    # list += list -> add
    if op == "Add" and (target_rt.startswith("list[") or target_rt in ("list", "bytes", "bytearray")):
        _emit(ctx, target_code + ".add(" + value_code + ")")
        return

    if target_rt in ("int", "int64") and not (value_code.startswith("int64(") or value_code.startswith("int(") or value_code.startswith("uint8(")):
        value_code = "int64(py_int(" + value_code + "))"
    if target_rt in ("float", "float64") and not (value_code.startswith("float64(") or value_code.startswith("float(")):
        value_code = "float64(py_float(" + value_code + "))"

    op_text = aug_map.get(op, "+=")
    # Nim doesn't have div=, mod= etc as combined operators; split them
    if op_text in ("div=", "mod=", "and=", "or=", "xor=", "shl=", "shr="):
        base_op = op_text[:-1]
        _emit(ctx, target_code + " = " + target_code + " " + base_op + " " + value_code)
    else:
        _emit(ctx, target_code + " " + op_text + " " + value_code)


def _emit_if_stmt(ctx: EmitContext, node: dict[str, JsonVal], *, is_elif: bool = False) -> None:
    test = _emit_condition_expr(ctx, node.get("test"))
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
    test = _emit_condition_expr(ctx, node.get("test"))
    _emit(ctx, "while " + test + ":")
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1


def _emit_for_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    iter_node = node.get("iter")
    target_code = _emit_expr(ctx, target)
    iter_code = _emit_expr(ctx, iter_node)
    saved_declared = _copy_str_set(ctx.declared_vars)

    # Mark loop var as declared
    if isinstance(target, dict):
        tname = _str(target, "id")
        if tname != "":
            ctx.declared_vars.add(_nim_name(ctx, tname))

    _emit(ctx, "for " + target_code + " in " + iter_code + ":")
    ctx.loop_depth += 1
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    ctx.loop_depth -= 1
    ctx.declared_vars = saved_declared


def _emit_for_range_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    target_code = _emit_expr(ctx, target)
    saved_declared = _copy_str_set(ctx.declared_vars)

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
    step_val: int = 0
    step_has_value = False
    if isinstance(step_node, dict):
        step_val = _get_static_int_literal(step_node, 2147483647)
        if step_val != 2147483647:
            step_has_value = True

    if step_has_value and step_val == -1:
        _emit(ctx, "for " + target_code + " in countdown(" + start_code + ", (" + stop_code + " + 1)):")
    elif step_has_value and step_val < 0:
        _emit(ctx, "for " + target_code + " in countdown(" + start_code + ", (" + stop_code + " + 1), " + str(-step_val) + "):")
    elif step_has_value and step_val == 1:
        _emit(ctx, "for " + target_code + " in " + start_code + " ..< " + stop_code + ":")
    elif step_has_value and step_val > 1:
        _emit(ctx, "for " + target_code + " in countup(" + start_code + ", " + stop_code + " - 1, " + str(step_val) + "):")
    elif isinstance(step_node, dict):
        step_code = _emit_expr(ctx, step_node)
        _emit(ctx, "for " + target_code + " in py_range(" + start_code + ", " + stop_code + ", " + step_code + "):")
    else:
        _emit(ctx, "for " + target_code + " in " + start_code + " ..< " + stop_code + ":")

    ctx.loop_depth += 1
    ctx.indent_level += 1
    _emit_body(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    ctx.loop_depth -= 1
    ctx.declared_vars = saved_declared


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


def _except_type_name(handler: dict[str, JsonVal]) -> str:
    exc_type = handler.get("type")
    if isinstance(exc_type, str):
        return exc_type
    if isinstance(exc_type, dict):
        name = _str(exc_type, "id")
        if name == "":
            name = _str(exc_type, "repr")
        return name
    return ""


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
        exc_type = _except_type_name(handler)
        exc_name = _str(handler, "name")

        if exc_type != "":
            nim_exc_type = _nim_exception_type_name(ctx, exc_type)
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
    left_code = _emit_subscript_target(ctx, left) if isinstance(left, dict) and _str(left, "kind") == "Subscript" else _emit_expr(ctx, left)
    right_code = _emit_subscript_target(ctx, right) if isinstance(right, dict) and _str(right, "kind") == "Subscript" else _emit_expr(ctx, right)
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
    items = _list(node, "items")
    if len(items) == 0:
        items = [node]
    for item in items:
        if not isinstance(item, dict):
            continue
        item_dict = _as_dict(item)
        context_expr = item_dict.get("context_expr")
        ctx_code = _emit_expr(ctx, context_expr)
        ctx_name = _next_temp(ctx, "pytra_with_ctx")
        _emit(ctx, "var " + ctx_name + " = " + ctx_code)

        var_name = _str(item_dict, "var_name")
        if var_name == "":
            optional_vars = item_dict.get("optional_vars")
            if isinstance(optional_vars, dict):
                var_name = _str(optional_vars, "id")

        if var_name != "":
            safe = _nim_name(ctx, var_name)
            if safe in ctx.declared_vars:
                _emit(ctx, safe + " = v_enter(" + ctx_name + ")")
            else:
                _emit(ctx, "var " + safe + " = v_enter(" + ctx_name + ")")
                ctx.declared_vars.add(safe)
            enter_type = _str(item_dict, "with_enter_type")
            if enter_type != "":
                ctx.var_types[safe] = enter_type
        else:
            _emit(ctx, "discard v_enter(" + ctx_name + ")")

        hoisted: list[tuple[str, str]] = []
        seen: set[str] = set()
        for stmt in _list(item_dict, "body"):
            if not isinstance(stmt, dict):
                continue
            kind = _str(stmt, "kind")
            if kind not in ("Assign", "AnnAssign"):
                continue
            target = stmt.get("target")
            if not isinstance(target, dict) or _str(target, "kind") not in ("Name", "NameTarget"):
                continue
            name = _str(target, "id")
            if name == "":
                continue
            safe_target = _nim_name(ctx, name)
            if safe_target in seen or safe_target in ctx.declared_vars:
                continue
            resolved_type = _str(stmt, "decl_type")
            if resolved_type == "":
                resolved_type = _str(stmt, "resolved_type")
            if resolved_type == "":
                resolved_type = _str(target, "resolved_type")
            seen.add(safe_target)
            hoisted.append((safe_target, resolved_type))
        for safe_target, resolved_type in hoisted:
            ann = _type_annotation(ctx, resolved_type)
            zero = nim_zero_value(resolved_type)
            _emit(ctx, "var " + safe_target + ann + " = " + zero)
            ctx.declared_vars.add(safe_target)
            if resolved_type != "":
                ctx.var_types[safe_target] = resolved_type

        _emit(ctx, "try:")
        ctx.indent_level += 1
        _emit_body(ctx, _list(item_dict, "body"))
        ctx.indent_level -= 1
        _emit(ctx, "finally:")
        ctx.indent_level += 1
        _emit(ctx, "v_exit(" + ctx_name + ", nil, nil, nil)")
        ctx.indent_level -= 1


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


def _node_reassigns_name(node: JsonVal, arg_name: str) -> bool:
    """Return True if the AST node reassigns the given simple name via `name = ...`.

    Nim parameters are immutable unless declared `var`. When the Python source
    rebinds a parameter (e.g. `x = x.strip()`), the Nim emitter must introduce a
    local `var x = x` shadow so the body compiles.
    """
    if isinstance(node, dict):
        kind = _str(node, "kind")
        if kind == "Assign":
            target = node.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name" and _str(target, "id") == arg_name:
                return True
        if kind == "AugAssign":
            target = node.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name" and _str(target, "id") == arg_name:
                return True
        for value in node.values():
            if _node_reassigns_name(value, arg_name):
                return True
    elif isinstance(node, list):
        for item in node:
            if _node_reassigns_name(item, arg_name):
                return True
    return False


def _node_uses_mutating_method_on_name(node: JsonVal, arg_name: str) -> bool:
    if isinstance(node, dict):
        kind = _str(node, "kind")
        if kind == "Call":
            func = node.get("func")
            if isinstance(func, dict) and _str(func, "kind") == "Attribute":
                owner = func.get("value")
                owner_id = _str(owner, "id") if isinstance(owner, dict) else ""
                meta = func.get("meta")
                mutates_receiver = False
                if isinstance(meta, dict):
                    meta_mutates = meta.get("mutates_receiver")
                    if isinstance(meta_mutates, bool) and meta_mutates:
                        mutates_receiver = True
                if owner_id == arg_name and (mutates_receiver or _str(owner, "borrow_kind") == "mutable_ref"):
                    return True
        if kind == "Assign":
            target = node.get("target")
            if isinstance(target, dict):
                if _str(target, "kind") == "Subscript":
                    value_node = target.get("value")
                    if isinstance(value_node, dict) and _str(value_node, "id") == arg_name:
                        return True
                if _str(target, "kind") == "Attribute":
                    value_node = target.get("value")
                    if isinstance(value_node, dict) and _str(value_node, "id") == arg_name:
                        return True
        if kind == "AugAssign":
            target = node.get("target")
            if isinstance(target, dict) and _str(target, "id") == arg_name:
                return True
        for value in node.values():
            if _node_uses_mutating_method_on_name(value, arg_name):
                return True
    elif isinstance(node, list):
        for item in node:
            if _node_uses_mutating_method_on_name(item, arg_name):
                return True
    return False


def _arg_should_be_var(node: dict[str, JsonVal], arg_name: str, arg_type: str) -> bool:
    if not (
        arg_type.startswith("list[")
        or arg_type.startswith("dict[")
        or arg_type.startswith("set[")
        or arg_type.startswith("deque[")
        or arg_type in ("list", "dict", "set", "deque", "bytes", "bytearray")
    ):
        return False
    return _node_uses_mutating_method_on_name(_list(node, "body"), arg_name)


def _emit_function_def(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    arg_names = _get_arg_order(node)
    return_type = _str(node, "return_type")
    body = _list(node, "body")
    if return_type in ("", "unknown", "None", "void"):
        for body_stmt in body:
            if isinstance(body_stmt, dict) and _str(body_stmt, "kind").startswith("Return") and isinstance(body_stmt.get("value"), dict):
                return_type = "auto"
                break
    decs = _decorators(node)

    is_static = "staticmethod" in decs
    is_property = "property" in decs
    is_method = ctx.current_class != "" and not is_static
    has_subclasses = False
    for base in ctx.class_bases.values():
        if base == ctx.current_class:
            has_subclasses = True
            break
    use_dynamic_method = is_method and name != "__init__" and (ctx.current_base_class != "" or has_subclasses)

    safe_name = _nim_name(ctx, name)
    function_arg_types: list[str] = []
    arg_type_idx = 0
    while arg_type_idx < len(arg_names):
        arg_name_for_type = _str_at(arg_names, arg_type_idx)
        if not (is_method and arg_name_for_type == "self"):
            function_arg_types.append(_get_arg_type(node, arg_name_for_type))
        arg_type_idx += 1
    ctx.function_arg_types[safe_name] = function_arg_types
    if return_type not in ("", "unknown"):
        ctx.function_return_types[safe_name] = return_type

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
        arg_name = _str_at(arg_names, idx)
        safe_arg: str = _safe_nim_ident(arg_name)
        at = _get_arg_type(node, arg_name)
        ann = ""
        if at != "" and at != "unknown":
            if _should_use_auto_param_type(at) or at in ctx.trait_names or _is_generic_typevar_name(ctx, at):
                ann = ": auto"
            else:
                rendered_arg_type = _render_type(ctx, at)
                if _arg_should_be_var(node, arg_name, at):
                    ann = ": var " + rendered_arg_type
                else:
                    ann = ": " + rendered_arg_type
        default_val = _get_arg_default(node, arg_name)
        if isinstance(default_val, dict):
            default_code = _emit_expr(ctx, default_val)
            params.append(safe_arg + ann + " = " + default_code)
        else:
            params.append(safe_arg + ann)
        idx += 1

    vararg_name = _str(node, "vararg_name")
    if vararg_name != "":
        safe_vararg = _safe_nim_ident(vararg_name)
        vararg_type = _str(node, "vararg_type")
        ann = ": seq[PyObj]"
        if vararg_type != "" and vararg_type != "unknown":
            ann = ": varargs[" + _render_type(ctx, vararg_type) + "]"
        params.append(safe_vararg + ann)

    ret_ann = _return_type_annotation(ctx, return_type)

    # Emit function header
    if is_method:
        kw = "method" if use_dynamic_method else "proc"
        pragmas = ""
        if use_dynamic_method and ctx.current_base_class == "" and has_subclasses:
            pragmas = " {.base.}"
        _emit(ctx, kw + " " + safe_name + "*(" + ", ".join(params) + ")" + ret_ann + pragmas + " =")
    else:
        export_marker = _export_marker(safe_name, top_level=ctx.indent_level == 0)
        _emit(ctx, "proc " + safe_name + export_marker + "(" + ", ".join(params) + ")" + ret_ann + " =")

    # Save context and emit body
    saved_vars = _copy_str_dict(ctx.var_types)
    saved_storage_vars = _copy_str_dict(ctx.storage_var_types)
    saved_ret = ctx.current_return_type
    saved_declared = _copy_str_set(ctx.declared_vars)
    ctx.current_return_type = return_type

    # Add parameters to declared vars
    arg_idx = 0
    while arg_idx < len(arg_names):
        arg_name = _str_at(arg_names, arg_idx)
        if arg_name != "self":
            safe_arg_name = _safe_nim_ident(arg_name)
            ctx.declared_vars.add(safe_arg_name)
            arg_type = _get_arg_type(node, arg_name)
            if arg_type != "" and arg_type != "unknown":
                ctx.var_types[safe_arg_name] = arg_type
                ctx.storage_var_types[safe_arg_name] = arg_type
        arg_idx += 1

    ctx.indent_level += 1
    # Emit shadow `var <param> = <param>` for parameters that are reassigned in the body.
    # Nim parameters are immutable by default; Python source routinely rebinds them
    # (e.g. `x = x.strip()`), so introduce a mutable local shadow to preserve semantics.
    shadow_idx = 0
    while shadow_idx < len(arg_names):
        arg_name = _str_at(arg_names, shadow_idx)
        if arg_name == "self":
            shadow_idx += 1
            continue
        arg_type = _get_arg_type(node, arg_name)
        if _arg_should_be_var(node, arg_name, arg_type):
            shadow_idx += 1
            continue  # already declared as `var T`; no shadow needed
        if _node_reassigns_name(body, arg_name):
            safe_arg: str = _safe_nim_ident(arg_name)
            _emit(ctx, "var " + safe_arg + " = " + safe_arg)
        shadow_idx += 1
    if len(body) == 0:
        _emit_discard(ctx)
    else:
        _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit_blank(ctx)

    ctx.var_types = saved_vars
    ctx.storage_var_types = saved_storage_vars
    ctx.current_return_type = saved_ret
    ctx.declared_vars = saved_declared


def _emit_function_decl(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    arg_names = _get_arg_order(node)
    return_type = _str(node, "return_type")
    decs = _decorators(node)

    is_static = "staticmethod" in decs
    is_method = ctx.current_class != "" and not is_static
    has_subclasses = False
    for base in ctx.class_bases.values():
        if base == ctx.current_class:
            has_subclasses = True
            break
    use_dynamic_method = is_method and name != "__init__" and (ctx.current_base_class != "" or has_subclasses)
    safe_name = _nim_name(ctx, name)

    params: list[str] = []
    skip_first = False
    if is_method and len(arg_names) > 0 and arg_names[0] == "self":
        skip_first = True
        params.append("self: " + _nim_name(ctx, ctx.current_class))

    start_idx = 1 if skip_first else 0
    idx = start_idx
    while idx < len(arg_names):
        arg_name = _str_at(arg_names, idx)
        safe_arg: str = _safe_nim_ident(arg_name)
        at = _get_arg_type(node, arg_name)
        ann = ""
        if at != "" and at != "unknown":
            if _should_use_auto_param_type(at) or at in ctx.trait_names or _is_generic_typevar_name(ctx, at):
                ann = ": auto"
            else:
                rendered_arg_type = _render_type(ctx, at)
                if _arg_should_be_var(node, arg_name, at):
                    ann = ": var " + rendered_arg_type
                else:
                    ann = ": " + rendered_arg_type
        params.append(safe_arg + ann)
        idx += 1

    vararg_name = _str(node, "vararg_name")
    if vararg_name != "":
        safe_vararg = _safe_nim_ident(vararg_name)
        vararg_type = _str(node, "vararg_type")
        ann = ": seq[PyObj]"
        if vararg_type != "" and vararg_type != "unknown":
            ann = ": varargs[" + _render_type(ctx, vararg_type) + "]"
        params.append(safe_vararg + ann)

    ret_ann = _return_type_annotation(ctx, return_type)
    if is_method:
        kw = "method" if use_dynamic_method else "proc"
        pragmas = ""
        if use_dynamic_method and ctx.current_base_class == "" and has_subclasses:
            pragmas = " {.base.}"
        _emit(ctx, kw + " " + safe_name + "*(" + ", ".join(params) + ")" + ret_ann + pragmas)
    else:
        export_marker = _export_marker(safe_name, top_level=ctx.indent_level == 0)
        _emit(ctx, "proc " + safe_name + export_marker + "(" + ", ".join(params) + ")" + ret_ann)


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
    field_defaults = _collect_class_field_defaults(node)
    static_attrs = ctx.class_static_attrs.get(name, {})

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
        _emit_discard(ctx)
    ctx.indent_level -= 1
    _emit_blank(ctx)

    if len(static_attrs) > 0:
        for attr_name, attr_stmt in static_attrs.items():
            attr_stmt_dict = _as_dict(attr_stmt)
            raw_value_node = attr_stmt_dict.get("value")
            if not isinstance(raw_value_node, dict):
                continue
            value_node = _as_dict(raw_value_node)
            attr_type = _str(attr_stmt_dict, "decl_type")
            if attr_type == "":
                attr_type = _str(value_node, "resolved_type")
            attr_code = _emit_expr(ctx, value_node)
            ann = ""
            if _str(value_node, "kind") != "Tuple":
                ann = _type_annotation(ctx, attr_type)
            _emit(ctx, "var " + safe_name + "_" + _safe_nim_ident(attr_name) + ann + " = " + attr_code)
        _emit_blank(ctx)

    # Save class context
    saved_class = ctx.current_class
    saved_base = ctx.current_base_class
    ctx.current_class = name
    ctx.current_base_class = base

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        sk = _str(stmt, "kind")
        if sk not in ("FunctionDef", "ClosureDef"):
            continue
        mname = _str(stmt, "name")
        if mname == "__init__":
            continue
        _emit_function_decl(ctx, stmt)
    has_non_init_method = False
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef") and _str(stmt, "name") != "__init__":
            has_non_init_method = True
            break
    if has_non_init_method:
        _emit_blank(ctx)

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

    if not has_init:
        _emit_default_constructor(ctx, name, fields, field_defaults)

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


def _collect_class_field_defaults(node: dict[str, JsonVal]) -> dict[str, JsonVal]:
    defaults: dict[str, JsonVal] = {}
    for stmt in _list(node, "body"):
        if not isinstance(stmt, dict) or _str(stmt, "kind") != "AnnAssign":
            continue
        target_val = stmt.get("target")
        field_name = ""
        if isinstance(target_val, dict):
            field_name = _str(target_val, "id")
        elif isinstance(target_val, str):
            field_name = target_val
        default_value = stmt.get("value")
        if field_name != "" and isinstance(default_value, dict):
            defaults[field_name] = default_value
    return defaults


def _emit_init_as_constructor(
    ctx: EmitContext,
    node: dict[str, JsonVal],
    class_name: str,
    fields: list[tuple[str, str]],
) -> None:
    """Emit __init__ as a mutating helper plus a constructor proc."""
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
        an = _str_at(arg_names, idx)
        safe_arg: str = _safe_nim_ident(an)
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

    saved_vars = _copy_str_dict(ctx.var_types)
    saved_ret = ctx.current_return_type
    saved_declared = _copy_str_set(ctx.declared_vars)
    ctx.current_return_type = class_name

    _emit(ctx, "proc initInto" + safe_name + "(self: " + safe_name + (", " + ", ".join(params) if len(params) > 0 else "") + ") =")
    decl_idx = 0
    while decl_idx < len(arg_names):
        an = _str_at(arg_names, decl_idx)
        if an != "self":
            ctx.declared_vars.add(_safe_nim_ident(an))
        decl_idx += 1
    ctx.indent_level += 1
    ctx.declared_vars.add("self")
    for stmt in body:
        _emit_stmt(ctx, stmt)
    ctx.indent_level -= 1
    _emit_blank(ctx)

    ctx.var_types = _copy_str_dict(saved_vars)
    ctx.current_return_type = class_name
    ctx.declared_vars = _copy_str_set(saved_declared)

    _emit(ctx, "proc init" + safe_name + "*(" + ", ".join(params) + "): " + safe_name + " =")
    init_decl_idx = 0
    while init_decl_idx < len(arg_names):
        an = _str_at(arg_names, init_decl_idx)
        if an != "self":
            ctx.declared_vars.add(_safe_nim_ident(an))
        init_decl_idx += 1
    ctx.indent_level += 1
    _emit(ctx, "var self = " + safe_name + "()")
    ctx.declared_vars.add("self")
    init_arg_parts: list[str] = []
    init_arg_idx = start_idx
    while init_arg_idx < len(arg_names):
        init_arg_parts.append(_safe_nim_ident(_str_at(arg_names, init_arg_idx)))
        init_arg_idx += 1
    init_suffix = ""
    if len(init_arg_parts) > 0:
        init_suffix = ", " + ", ".join(init_arg_parts)
    _emit(ctx, "initInto" + safe_name + "(self" + init_suffix + ")")
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
    field_defaults: dict[str, JsonVal] | None = None,
) -> None:
    safe_name = _nim_name(ctx, class_name)
    params: list[str] = []
    defaults: dict[str, JsonVal] = {}
    if field_defaults is not None:
        defaults = field_defaults
    for fname, ftype in fields:
        default_code = nim_zero_value(ftype)
        default_node = defaults.get(fname)
        if isinstance(default_node, dict):
            default_code = _emit_expr(ctx, default_node)
        params.append(_safe_nim_ident(fname) + ": " + _render_type(ctx, ftype) + " = " + default_code)

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
    saved_vars = _copy_str_dict(ctx.var_types)
    saved_ret = ctx.current_return_type
    saved_declared = _copy_str_set(ctx.declared_vars)
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
            implemented = _implemented_traits(stmt)
            if len(implemented) > 0:
                ctx.class_traits[class_name] = implemented
            field_types = _dict(stmt, "field_types")
            class_fields: dict[str, str] = {}
            for fname, ftype in field_types.items():
                if isinstance(fname, str) and isinstance(ftype, str):
                    class_fields[fname] = ftype
            ctx.class_fields[class_name] = class_fields
            static_attrs: dict[str, JsonVal] = {}
            for body_stmt in _list(stmt, "body"):
                if not isinstance(body_stmt, dict):
                    continue
                sk2 = _str(body_stmt, "kind")
                if sk2 == "AnnAssign":
                    target_val = body_stmt.get("target")
                    attr_name = _str(target_val, "id") if isinstance(target_val, dict) else ""
                    if attr_name != "" and isinstance(body_stmt.get("value"), dict):
                        static_attrs[attr_name] = body_stmt
                elif sk2 == "Assign":
                    target_val = body_stmt.get("target")
                    attr_name = _str(target_val, "id") if isinstance(target_val, dict) else ""
                    if attr_name != "" and isinstance(body_stmt.get("value"), dict):
                        static_attrs[attr_name] = body_stmt
            ctx.class_static_attrs[class_name] = static_attrs


def _emit_nim_imports(ctx: EmitContext) -> None:
    """Emit Nim standard library imports needed by the generated code."""
    _emit(ctx, "import std/algorithm")
    _emit(ctx, "import std/tables")
    _emit(ctx, "import std/sets")
    _emit(ctx, "import std/sequtils")
    _emit(ctx, "import std/strutils")
    _emit(ctx, "import std/sugar")
    runtime_import = "py_runtime" if ctx.root_rel_prefix == "" else ctx.root_rel_prefix + "py_runtime"
    _emit(ctx, "import " + runtime_import)
    _emit_blank(ctx)


def _should_emit_list_alias_template(target_rt: str, value: JsonVal) -> bool:
    return (
        target_rt.startswith("list[")
        and isinstance(value, dict)
        and _str(value, "kind") == "Name"
        and _str(value, "resolved_type") == target_rt
    )


def _emit_module_imports(ctx: EmitContext, body: list[JsonVal]) -> None:
    """Emit import statements for user modules."""
    src_pytra_root = Path(__file__).resolve().parents[3] / "pytra"
    native_helper_imports: dict[str, dict[str, list[str]]] = {
        "argparse_native": {
            "*": ["add_argument", "parse_args"],
        },
        "pathlib_native": {
            "*": ["parent", "name", "stem", "mkdir", "joinpath", "exists", "write_text", "read_text"],
        },
        "sys_native": {
            "*": ["set_argv", "set_path"],
        },
    }

    def _native_module_for(module_name: str) -> str:
        return _native_module_name(ctx, module_name)

    def _extend_native_helper_imports(native_module: str, imported_names: list[str]) -> list[str]:
        if native_module not in native_helper_imports:
            return imported_names
        helper_spec = native_helper_imports[native_module]
        if len(helper_spec) == 0:
            return imported_names
        out = list(imported_names)
        if "*" in helper_spec:
            helpers = helper_spec["*"]
            for helper_name in helpers:
                if helper_name not in out:
                    out.append(helper_name)
        return out

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind == "ImportFrom":
            module_id = _str(stmt, "module")
            if module_id == "":
                continue
            if module_id == "pytra.std":
                for name_entry in _list(stmt, "names"):
                    if not isinstance(name_entry, dict):
                        continue
                    imported_name = _str(name_entry, "name")
                    native_module: str = _native_module_for(module_id + "." + imported_name)
                    if native_module == "":
                        continue
                    asname = _str(name_entry, "asname")
                    alias_name = asname if asname != "" else imported_name
                    native_import: str = native_module
                    if ctx.root_rel_prefix != "":
                        native_import = ctx.root_rel_prefix + native_module
                    _emit(ctx, "import " + native_import + " as " + _nim_name(ctx, alias_name))
                    if native_module == "os_native":
                        py_path_import = "os_path_native"
                        if ctx.root_rel_prefix != "":
                            py_path_import = ctx.root_rel_prefix + "os_path_native"
                        _emit(ctx, "import " + py_path_import + " as py_path")
                continue
            native_module: str = _native_module_for(module_id)
            if should_skip_module(module_id, ctx.mapping) or native_module != "":
                if native_module != "":
                    # Names that are Python-side type aliases already mapped to PyObj/built-in Nim types;
                    # they don't exist in the native Nim modules and should not be imported.
                    _NIM_SKIPPED_IMPORT_NAMES: set[str] = {"JsonVal"}
                    imported_names: list[str] = []
                    for name_entry in _list(stmt, "names"):
                        if not isinstance(name_entry, dict):
                            continue
                        imported_name = _str(name_entry, "name")
                        if imported_name != "" and imported_name not in _NIM_SKIPPED_IMPORT_NAMES:
                            imported_names.append(imported_name)
                            asname = _str(name_entry, "asname")
                            local_name = asname if asname != "" else imported_name
                            mapped_name = ctx.runtime_imports.get(local_name, "")
                            if (
                                isinstance(mapped_name, str)
                                and mapped_name != ""
                                and mapped_name not in imported_names
                                and "." not in mapped_name
                            ):
                                imported_names.append(mapped_name)
                    imported_names = _extend_native_helper_imports(native_module, imported_names)
                    if len(imported_names) > 0:
                        native_import: str = native_module
                        if ctx.root_rel_prefix != "":
                            native_import = ctx.root_rel_prefix + native_module
                        _emit(ctx, "from " + native_import + " import " + ", ".join(imported_names))
                continue
            if module_id.startswith("pytra."):
                rel_module = module_id[len("pytra."):]
                rel_module_path = src_pytra_root / (rel_module.replace(".", "/") + ".py")
                if rel_module_path.exists():
                    imported_names: list[str] = []
                    for name_entry in _list(stmt, "names"):
                        if not isinstance(name_entry, dict):
                            continue
                        imported_name = _str(name_entry, "name")
                        if imported_name != "":
                            imported_names.append(imported_name)
                    if len(imported_names) > 0:
                        import_module = module_id.replace(".", "_")
                        if module_id.startswith("pytra.utils."):
                            import_module = "utils/" + _last_dot_part(module_id)
                        if ctx.root_rel_prefix != "":
                            import_module = ctx.root_rel_prefix + import_module
                        _emit(ctx, "from " + import_module + " import " + ", ".join(imported_names))
                        continue
                emitted_submodule_import = False
                for name_entry in _list(stmt, "names"):
                    if not isinstance(name_entry, dict):
                        continue
                    imported_name = _str(name_entry, "name")
                    if imported_name == "":
                        continue
                    candidate_module_rel = rel_module.replace(".", "/") + "/" + imported_name
                    candidate_path = src_pytra_root / (candidate_module_rel + ".py")
                    if not candidate_path.exists():
                        continue
                    asname = _str(name_entry, "asname")
                    alias_name = asname if asname != "" else imported_name
                    candidate_module = module_id.replace(".", "_") + "_" + imported_name
                    _emit(ctx, "import " + candidate_module + " as " + _nim_name(ctx, alias_name))
                    emitted_submodule_import = True
                if emitted_submodule_import:
                    continue
            # Relative module import
            nim_module = module_id.replace(".", "_")
            _emit(ctx, "import " + nim_module)
        elif kind == "Import":
            names = _list(stmt, "names")
            for name_entry in names:
                if not isinstance(name_entry, dict):
                    continue
                mod_name = _str(name_entry, "name")
                if mod_name == "":
                    continue
                native_module: str = _native_module_for(mod_name)
                if should_skip_module(mod_name, ctx.mapping) or native_module != "":
                    if native_module != "":
                        asname = _str(name_entry, "asname")
                        alias_name = asname if asname != "" else _last_dot_part(mod_name)
                        native_import: str = native_module
                        if ctx.root_rel_prefix != "":
                            native_import = ctx.root_rel_prefix + native_module
                        _emit(ctx, "import " + native_import + " as " + _nim_name(ctx, alias_name))
                        if native_module == "os_native":
                            py_path_import = "os_path_native"
                            if ctx.root_rel_prefix != "":
                                py_path_import = ctx.root_rel_prefix + "os_path_native"
                            _emit(ctx, "import " + py_path_import + " as py_path")
                    continue
                if mod_name.startswith("pytra.utils."):
                    rel_module = mod_name[len("pytra."):]
                    rel_module_path = src_pytra_root / (rel_module.replace(".", "/") + ".py")
                    if rel_module_path.exists():
                        asname = _str(name_entry, "asname")
                        alias_name = asname if asname != "" else _last_dot_part(mod_name)
                        import_module = "utils/" + _last_dot_part(mod_name)
                        if ctx.root_rel_prefix != "":
                            import_module = ctx.root_rel_prefix + import_module
                        _emit(ctx, "import " + import_module + " as " + _nim_name(ctx, alias_name))
                        continue
                nim_module = mod_name.replace(".", "_")
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
        modules_for_defaults: list[JsonVal] = [east3_doc]
        expand_cross_module_defaults(modules_for_defaults)

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

    ctx = EmitContext()
    ctx.module_id = module_id
    ctx.source_path = _str(east3_doc, "source_path")
    if len(emit_ctx_meta) > 0:
        ctx.is_entry = _bool(emit_ctx_meta, "is_entry")
        ctx.root_rel_prefix = _str(emit_ctx_meta, "root_rel_prefix")
    ctx.mapping = mapping
    ctx.renamed_symbols = renamed_symbols
    ctx.is_type_id_table = is_type_id_table

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
    _collect_general_unions_from_json(body, ctx.general_unions)
    _collect_general_unions_from_json(main_guard, ctx.general_unions)

    # Emit standard imports
    _emit_nim_imports(ctx)

    # Emit user module imports
    _emit_module_imports(ctx, body)

    pre_class_unions = [u for u in ctx.general_unions if not _union_has_nominal_option(ctx, u)]
    post_class_unions = [u for u in ctx.general_unions if _union_has_nominal_option(ctx, u)]

    if len(pre_class_unions) > 0:
        _emit_blank(ctx)
        saved = ctx.general_unions
        ctx.general_unions = pre_class_unions
        _emit_general_union_defs(ctx)
        ctx.general_unions = saved

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _str(stmt, "kind") != "ClassDef":
            continue
        _emit_stmt(ctx, stmt)

    if len(post_class_unions) > 0:
        _emit_blank(ctx)
        saved = ctx.general_unions
        ctx.general_unions = post_class_unions
        _emit_general_union_defs(ctx)
        ctx.general_unions = saved

    # Emit module body
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("ImportFrom", "Import", "ClassDef"):
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
