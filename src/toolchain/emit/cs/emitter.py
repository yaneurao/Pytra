"""EAST3 → C# source emitter.

Minimal toolchain2 C# emitter built on CommonRenderer.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_import_alias_map,
)
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.emit.common.profile_loader import load_profile_doc
from toolchain.emit.cs.types import (
    _safe_cs_ident, _split_generic_args, cs_type, cs_zero_value,
    CS_PATH_MEMBER_NAMES, CS_EXCEPTION_BASE_NAME,
    PYTRA_STD_MODULE_PREFIX, PYTRA_BUILTIN_MODULE_PREFIX,
    is_cs_exception_type, is_cs_path_type, is_pytra_type_id_name,
)
from toolchain.link.expand_defaults import expand_cross_module_defaults


@dataclass
class EmitContext:
    module_id: str = ""
    source_path: str = ""
    is_entry: bool = False
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    import_alias_modules: dict[str, str] = field(default_factory=dict)
    runtime_imports: dict[str, str] = field(default_factory=dict)
    var_types: dict[str, str] = field(default_factory=dict)
    current_return_type: str = ""
    current_class_name: str = ""
    class_names: set[str] = field(default_factory=set)
    trait_names: set[str] = field(default_factory=set)
    class_bases: dict[str, str] = field(default_factory=dict)
    class_methods: dict[str, set[str]] = field(default_factory=dict)
    class_properties: dict[str, set[str]] = field(default_factory=dict)
    enum_constant_types: set[str] = field(default_factory=set)
    type_id_values: dict[str, int] = field(default_factory=dict)
    renamed_symbols: dict[str, str] = field(default_factory=dict)
    module_function_names: set[str] = field(default_factory=set)
    function_arg_types: dict[str, list[str]] = field(default_factory=dict)
    temp_index: int = 0
    current_base_class_name: str = ""
    current_function_name: str = ""


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
    if module_id == "":
        return "Module"
    tail = module_id.split(".")[-1]
    safe = _safe_cs_ident(tail)
    if safe == "":
        return "Module"
    return safe[0].upper() + safe[1:]


def _fqcn_to_tid_const(name: str) -> str:
    parts = [_safe_cs_ident(part).upper() for part in name.split(".") if part != ""]
    if len(parts) == 0:
        return ""
    return "_".join(parts) + "_TID"


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


def _safe_name(ctx: EmitContext, name: str) -> str:
    if name == "self":
        return "this"
    renamed = ctx.renamed_symbols.get(name, "")
    if renamed != "":
        return _safe_cs_ident(renamed)
    return _safe_cs_ident(name)


def _module_mapping_candidates(module_id: str) -> list[str]:
    if module_id == "":
        return []
    out: list[str] = []
    for candidate in (
        module_id,
        module_id[len(PYTRA_STD_MODULE_PREFIX):] if module_id.startswith(PYTRA_STD_MODULE_PREFIX) else "",
        module_id[len(PYTRA_BUILTIN_MODULE_PREFIX):] if module_id.startswith(PYTRA_BUILTIN_MODULE_PREFIX) else "",
        module_id.split(".")[-1],
    ):
        if candidate != "" and candidate not in out:
            out.append(candidate)
    return out


def _resolve_runtime_module_member(mapping: RuntimeMapping, module_id: str, member_name: str) -> str:
    safe_member = _safe_cs_ident(member_name)
    for candidate in _module_mapping_candidates(module_id):
        key = candidate + "." + member_name
        if key in mapping.calls:
            mapped = mapping.calls[key]
            if isinstance(mapped, str) and mapped != "":
                return mapped
    if member_name in mapping.calls:
        mapped2 = mapping.calls[member_name]
        if isinstance(mapped2, str) and mapped2 != "":
            return mapped2
    if module_id != "" and not should_skip_module(module_id, mapping):
        return _module_class_name(module_id) + "." + safe_member
    if module_id.startswith(PYTRA_STD_MODULE_PREFIX):
        return module_id.split(".")[-1] + "_native." + safe_member
    return ""


def _resolve_runtime_symbol_expr(
    mapping: RuntimeMapping,
    *,
    source_module_id: str,
    runtime_module_id: str,
    symbol_name: str,
) -> str:
    for module_id in (runtime_module_id, source_module_id):
        if module_id == "":
            continue
        resolved = _resolve_runtime_module_member(mapping, module_id, symbol_name)
        if resolved != "":
            return resolved
    if symbol_name in mapping.calls:
        mapped = mapping.calls[symbol_name]
        if isinstance(mapped, str):
            return mapped
    return ""


def _build_cs_runtime_import_map(meta: dict[str, JsonVal], mapping: RuntimeMapping) -> dict[str, str]:
    runtime_imports: dict[str, str] = {}
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        return runtime_imports
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        if binding.get("binding_kind") != "symbol":
            continue
        local_name = binding.get("local_name")
        if not isinstance(local_name, str) or local_name == "":
            continue
        mapped_type = mapping.types.get(local_name)
        if isinstance(mapped_type, str) and mapped_type != "":
            continue
        if binding.get("resolved_binding_kind") == "module":
            continue
        runtime_symbol_kind = binding.get("runtime_symbol_kind")
        if isinstance(runtime_symbol_kind, str) and runtime_symbol_kind not in ("", "function", "method", "callable"):
            continue
        runtime_symbol = binding.get("runtime_symbol")
        if not isinstance(runtime_symbol, str) or runtime_symbol == "":
            runtime_symbol = binding.get("export_name")
        if not isinstance(runtime_symbol, str) or runtime_symbol == "":
            runtime_symbol = local_name
        source_module_id = binding.get("module_id")
        runtime_module_id = binding.get("runtime_module_id")
        source_module = source_module_id if isinstance(source_module_id, str) else ""
        runtime_module = runtime_module_id if isinstance(runtime_module_id, str) else ""
        resolved = _resolve_runtime_symbol_expr(
            mapping,
            source_module_id=source_module,
            runtime_module_id=runtime_module,
            symbol_name=runtime_symbol,
        )
        if resolved != "" and "." in resolved:
            runtime_imports[local_name] = resolved
    return runtime_imports


def _next_temp(ctx: EmitContext, prefix: str) -> str:
    ctx.temp_index += 1
    return _safe_cs_ident(prefix + "_" + str(ctx.temp_index))


def _quote_string(value: str) -> str:
    escaped = (
        value
        .replace("\\", "\\\\")
        .replace("\"", "\\\"")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\b", "\\b")
        .replace("\f", "\\f")
    )
    return "\"" + escaped + "\""


def _target_type_from_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    for key in ("decl_type", "annotation", "resolved_type"):
        text = _str(node, key)
        if text != "":
            rendered = _render_type(ctx, text)
            qualified = _qualify_stmt_result_type(ctx, node, text, rendered)
            if qualified != "":
                return qualified
            return rendered
    target = node.get("target")
    if isinstance(target, dict):
        rt = _str(target, "resolved_type")
        if rt != "":
            rendered2 = _render_type(ctx, rt)
            qualified2 = _qualify_stmt_result_type(ctx, node, rt, rendered2)
            if qualified2 != "":
                return qualified2
            return rendered2
    return "object"


def _qualify_stmt_result_type(
    ctx: EmitContext,
    node: dict[str, JsonVal],
    resolved_type: str,
    rendered_type: str,
) -> str:
    if resolved_type == "":
        return ""
    candidate_names = {_safe_cs_ident(resolved_type)}
    if resolved_type.endswith(" | None"):
        candidate_names.add(_safe_cs_ident(resolved_type[:-7].strip()))
    if rendered_type not in candidate_names:
        return ""
    if resolved_type in ctx.class_names or resolved_type in ctx.trait_names or resolved_type in ctx.import_alias_modules:
        return ""
    value = node.get("value")
    if not isinstance(value, dict) or _str(value, "kind") != "Call":
        return ""
    func = value.get("func")
    if not isinstance(func, dict) or _str(func, "kind") != "Attribute":
        return ""
    owner = func.get("value")
    if not _is_module_owner(ctx, owner):
        return ""
    module_id = ""
    if isinstance(owner, dict):
        module_id = _str(owner, "runtime_module_id")
        if module_id == "":
            module_id = ctx.import_alias_modules.get(_str(owner, "id"), "")
    if module_id == "" or should_skip_module(module_id, ctx.mapping):
        return ""
    return _module_class_name(module_id) + "." + rendered_type


def _render_type(ctx: EmitContext, resolved_type: str, *, for_return: bool = False) -> str:
    if len(resolved_type) == 1 and resolved_type.isupper():
        return "object"
    if resolved_type in ctx.enum_constant_types:
        return "long"
    if resolved_type in ctx.class_names:
        return _safe_name(ctx, resolved_type)
    if is_cs_path_type(resolved_type) and resolved_type in ctx.import_alias_modules:
        module_id = ctx.import_alias_modules.get(resolved_type, "")
        if module_id != "" and not should_skip_module(module_id, ctx.mapping):
            return _module_class_name(module_id) + "." + _safe_name(ctx, resolved_type)
    for module_id in sorted(set(ctx.import_alias_modules.values())):
        fqcn = module_id + "." + resolved_type
        if fqcn in ctx.type_id_values and not should_skip_module(module_id, ctx.mapping):
            return _module_class_name(module_id) + "." + _safe_name(ctx, resolved_type)
    mapped_builtin = cs_type(resolved_type, mapping=ctx.mapping, for_return=for_return)
    if resolved_type in ctx.mapping.types or mapped_builtin != _safe_cs_ident(resolved_type):
        return mapped_builtin
    if resolved_type in ctx.import_alias_modules:
        module_id = ctx.import_alias_modules.get(resolved_type, "")
        if module_id != "" and not should_skip_module(module_id, ctx.mapping):
            return _module_class_name(module_id) + "." + _safe_name(ctx, resolved_type)
    return mapped_builtin


def _expected_type_name(node: JsonVal) -> str:
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    type_name = _str(node, "type_object_of")
    if type_name == "":
        type_name = _str(node, "id")
    legacy_type_names = {
        "PYTRA_TID_NONE": "None",
        "PYTRA_TID_BOOL": "bool",
        "PYTRA_TID_INT": "int",
        "PYTRA_TID_FLOAT": "float",
        "PYTRA_TID_STR": "str",
        "PYTRA_TID_LIST": "list",
        "PYTRA_TID_DICT": "dict",
        "PYTRA_TID_SET": "set",
        "PYTRA_TID_OBJECT": "object",
        "PYTRA_TID_INT8": "int8",
        "PYTRA_TID_INT16": "int16",
        "PYTRA_TID_INT32": "int32",
        "PYTRA_TID_INT64": "int64",
        "PYTRA_TID_UINT8": "uint8",
        "PYTRA_TID_UINT16": "uint16",
        "PYTRA_TID_UINT32": "uint32",
        "PYTRA_TID_UINT64": "uint64",
        "PYTRA_TID_FLOAT32": "float32",
        "PYTRA_TID_FLOAT64": "float64",
        "NONE_TID": "None",
        "BOOL_TID": "bool",
        "INT_TID": "int",
        "INT64_TID": "int64",
        "FLOAT_TID": "float",
        "FLOAT64_TID": "float64",
        "STR_TID": "str",
        "LIST_TID": "list",
        "DICT_TID": "dict",
        "SET_TID": "set",
        "OBJECT_TID": "object",
    }
    if type_name in legacy_type_names:
        return legacy_type_names[type_name]
    return type_name


def _emit_builtin_isinstance_expr(ctx: EmitContext, boxed_expr: str, type_name: str) -> str:
    cs_builtin_types: dict[str, str] = {
        "bool": "bool",
        "int8": "sbyte",
        "int16": "short",
        "int32": "int",
        "int": "long",
        "int64": "long",
        "uint8": "byte",
        "uint16": "ushort",
        "uint32": "uint",
        "uint64": "ulong",
        "float": "double",
        "float32": "float",
        "float64": "double",
        "str": "string",
        "tuple": "object[]",
    }
    if type_name in ("None", "none"):
        return "(" + boxed_expr + " == null)"
    if type_name in ("list", "bytes", "bytearray"):
        return "(" + boxed_expr + " is System.Collections.IList)"
    if type_name == "dict":
        return "(" + boxed_expr + " is System.Collections.IDictionary)"
    if type_name == "set":
        return "py_runtime.py_is_set(" + boxed_expr + ")"
    if type_name in ("object", "Obj", "Any"):
        return "(" + boxed_expr + " is object)"
    cs_type_name = cs_builtin_types.get(type_name, "")
    if cs_type_name != "":
        return "(" + boxed_expr + " is " + cs_type_name + ")"
    rendered_type = _render_type(ctx, type_name)
    if rendered_type == "" or rendered_type == "object":
        return ""
    return "(" + boxed_expr + " is " + rendered_type + ")"


def _arg_order_and_types(node: dict[str, JsonVal]) -> tuple[list[str], dict[str, str]]:
    arg_order: list[str] = []
    for item in _list(node, "arg_order"):
        if isinstance(item, str):
            arg_order.append(item)
    arg_types: dict[str, str] = {}
    for key, value in _dict(node, "arg_types").items():
        if isinstance(key, str) and isinstance(value, str):
            arg_types[key] = value
            if key not in arg_order:
                arg_order.append(key)
    return (arg_order, arg_types)


def _emit_constant(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    _ = ctx
    value = node.get("value")
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _quote_string(value)
    if isinstance(value, int) and _str(node, "resolved_type") in ("int", "int64"):
        return str(value) + "L"
    return str(value)


def _legacy_type_id_name_expr(name: str) -> str:
    return {
        "PYTRA_TID_NONE": "0L",
        "PYTRA_TID_BOOL": "1L",
        "PYTRA_TID_INT": "2L",
        "PYTRA_TID_FLOAT": "3L",
        "PYTRA_TID_STR": "4L",
        "PYTRA_TID_LIST": "5L",
        "PYTRA_TID_DICT": "6L",
        "PYTRA_TID_SET": "7L",
        "PYTRA_TID_OBJECT": "8L",
        "PYTRA_TID_BASE_EXCEPTION": "9L",
        "PYTRA_TID_EXCEPTION": "10L",
        "PYTRA_TID_RUNTIME_ERROR": "11L",
        "PYTRA_TID_VALUE_ERROR": "12L",
        "PYTRA_TID_TYPE_ERROR": "13L",
        "PYTRA_TID_INDEX_ERROR": "14L",
        "PYTRA_TID_KEY_ERROR": "15L",
        "PYTRA_TID_INT8": "16L",
        "PYTRA_TID_INT16": "17L",
        "PYTRA_TID_INT32": "18L",
        "PYTRA_TID_INT64": "19L",
        "PYTRA_TID_UINT8": "20L",
        "PYTRA_TID_UINT16": "21L",
        "PYTRA_TID_UINT32": "22L",
        "PYTRA_TID_UINT64": "23L",
        "PYTRA_TID_FLOAT32": "24L",
        "PYTRA_TID_FLOAT64": "25L",
        "NONE_TID": "0L",
        "BOOL_TID": "1L",
        "INT_TID": "2L",
        "INT64_TID": "19L",
        "FLOAT_TID": "3L",
        "FLOAT64_TID": "25L",
        "STR_TID": "4L",
        "LIST_TID": "5L",
        "DICT_TID": "6L",
        "SET_TID": "7L",
        "OBJECT_TID": "8L",
    }.get(name, "")


def _emit_name(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    ident = _str(node, "id")
    legacy_tid = _legacy_type_id_name_expr(ident)
    if legacy_tid != "":
        return legacy_tid
    if ident in ctx.class_names or ident in ctx.trait_names or ident in ctx.enum_constant_types:
        return _safe_name(ctx, ident)
    if ident.endswith("_TID") and ident in ctx.type_id_values:
        return str(ctx.type_id_values[ident]) + "L"
    if ident in ctx.type_id_values:
        return str(ctx.type_id_values[ident]) + "L"
    safe_ident = _safe_name(ctx, ident)
    resolved_type = _str(node, "resolved_type")
    known_type = ctx.var_types.get(safe_ident, "")
    if _is_dynamic_resolved_type(known_type) and not _is_dynamic_resolved_type(resolved_type):
        return _coerce_dynamic_expr(ctx, safe_ident, resolved_type)
    return safe_ident


def _render_list_literal(ctx: EmitContext, node: dict[str, JsonVal], *, preferred_type: str = "") -> str:
    elems = _list(node, "elements")
    node_rt = _str(node, "resolved_type")
    rt = preferred_type if preferred_type not in ("", "object", "Obj", "Any", "unknown") else node_rt
    if node_rt.startswith("list[") or node_rt == "list":
        if not (rt.startswith("list[") or rt == "list"):
            rt = node_rt
    out_type = "List<object>"
    elem_preferred_type = ""
    if rt != "":
        out_type = _render_type(ctx, rt)
        if rt.startswith("list[") and rt.endswith("]"):
            inner = rt[5:-1]
            parts = _split_generic_args(inner)
            if len(parts) == 1:
                elem_preferred_type = parts[0]
    rendered = [
        _render_expr_with_preferred_type(ctx, elem, preferred_type=elem_preferred_type)
        if elem_preferred_type != "" and isinstance(elem, dict)
        else _emit_expr(ctx, elem)
        for elem in elems
    ]
    if len(rendered) == 0:
        return "new " + out_type + "()"
    return "new " + out_type + " { " + ", ".join(rendered) + " }"


def _render_set_literal(ctx: EmitContext, node: dict[str, JsonVal], *, preferred_type: str = "") -> str:
    elems = _list(node, "elements")
    node_rt = _str(node, "resolved_type")
    rt = preferred_type if preferred_type not in ("", "object", "Obj", "Any", "unknown") else node_rt
    if node_rt.startswith("set[") or node_rt == "set":
        if not (rt.startswith("set[") or rt == "set"):
            rt = node_rt
    out_type = "HashSet<object>"
    elem_preferred_type = ""
    if rt != "":
        out_type = _render_type(ctx, rt)
        if rt.startswith("set[") and rt.endswith("]"):
            inner = rt[4:-1]
            parts = _split_generic_args(inner)
            if len(parts) == 1:
                elem_preferred_type = parts[0]
    rendered = [
        _render_expr_with_preferred_type(ctx, elem, preferred_type=elem_preferred_type)
        if elem_preferred_type != "" and isinstance(elem, dict)
        else _emit_expr(ctx, elem)
        for elem in elems
    ]
    if out_type.startswith("HashSet<") and out_type.endswith("[]>"):
        elem_type = out_type[len("HashSet<"):-3]
        if len(rendered) == 0:
            return "new " + out_type + "(py_runtime.array_comparer<" + elem_type + ">())"
        return (
            "new " + out_type + "(py_runtime.array_comparer<" + elem_type + ">()) { "
            + ", ".join(rendered)
            + " }"
        )
    if len(rendered) == 0:
        return "new " + out_type + "()"
    return "new " + out_type + " { " + ", ".join(rendered) + " }"


def _render_dict_literal(ctx: EmitContext, node: dict[str, JsonVal], *, preferred_type: str = "") -> str:
    entries = _list(node, "entries")
    node_rt = _str(node, "resolved_type")
    rt = preferred_type if preferred_type not in ("", "object", "Obj", "Any", "unknown") else node_rt
    if node_rt.startswith("dict[") or node_rt == "dict":
        if not (rt.startswith("dict[") or rt == "dict"):
            rt = node_rt
    out_type = "Dictionary<object, object>"
    if rt != "":
        out_type = _render_type(ctx, rt)
    rendered_entries: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        rendered_entries.append("{ " + _emit_expr(ctx, entry.get("key")) + ", " + _emit_expr(ctx, entry.get("value")) + " }")
    if len(rendered_entries) == 0:
        return "new " + out_type + "()"
    return "new " + out_type + " { " + ", ".join(rendered_entries) + " }"


def _render_subscript(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    owner = _emit_expr(ctx, owner_node)
    owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    if owner_type == "" and isinstance(owner_node, dict) and _str(owner_node, "kind") == "Name":
        owner_type = ctx.var_types.get(_safe_name(ctx, _str(owner_node, "id")), "")
    result_type = _str(node, "resolved_type")
    slice_node = node.get("slice")
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        lower_expr = _emit_expr(ctx, lower) if isinstance(lower, dict) else "null"
        upper_expr = _emit_expr(ctx, upper) if isinstance(upper, dict) else "null"
        return "py_runtime.py_slice(" + owner + ", " + lower_expr + ", " + upper_expr + ")"
    index = _emit_expr(ctx, slice_node)
    if owner_type == "str":
        text_expr = "py_runtime.py_get(" + owner + ", " + index + ")"
        if result_type not in ("", "str"):
            return "((" + _render_type(ctx, result_type) + ")py_runtime.py_ord(" + text_expr + "))"
        return text_expr
    if owner_type.startswith("list[") or owner_type in ("bytes", "bytearray"):
        return "py_runtime.py_get(" + owner + ", " + index + ")"
    if owner_type in ("tuple", "object[]") or owner_type.startswith("tuple[") or owner_type.endswith("[]"):
        return owner + "[((int)" + index + ")]"
    if _is_dynamic_resolved_type(owner_type):
        return "py_runtime.py_get(" + owner + ", " + index + ")"
    return owner + "[" + index + "]"


def _iter_expr_runtime_call(node: JsonVal) -> str:
    if not isinstance(node, dict) or _str(node, "kind") != "Call":
        return ""
    value = _str(node, "runtime_call")
    if value != "":
        return value
    return _str(node, "resolved_runtime_call")


def _render_ifexp(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    test = _emit_condition_expr(ctx, node.get("test"), wrap=False)
    body = _emit_expr(ctx, node.get("body"))
    orelse = _emit_expr(ctx, node.get("orelse"))
    return "(" + test + " ? " + body + " : " + orelse + ")"


def _emit_formatted_value(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    format_spec = _str(node, "format_spec")
    value_expr = _emit_expr(ctx, node.get("value"))
    if format_spec != "":
        return "py_runtime.py_format(" + value_expr + ", " + _quote_string(format_spec) + ")"
    return "Convert.ToString(" + value_expr + ")"


def _emit_fstring(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    parts: list[str] = []
    for value in _list(node, "values"):
        if not isinstance(value, dict):
            continue
        kind = _str(value, "kind")
        if kind == "Constant":
            raw = value.get("value")
            if isinstance(raw, str):
                parts.append(_quote_string(raw))
            continue
        if kind == "FormattedValue":
            parts.append(_emit_formatted_value(ctx, value))
            continue
        parts.append("Convert.ToString(" + _emit_expr(ctx, value) + ")")
    if len(parts) == 0:
        return "\"\""
    if len(parts) == 1:
        return parts[0]
    return "(" + " + ".join(parts) + ")"


def _emit_box(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if isinstance(value, dict) and _str(value, "resolved_type") in ("Callable", "callable"):
        if _str(value, "kind") == "Name":
            return "new Action(" + _safe_name(ctx, _str(value, "id")) + ")"
        return "new Action(" + _emit_expr(ctx, value) + ")"
    return _emit_expr(ctx, value)


def _emit_lambda(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    arg_order, arg_types = _arg_order_and_types(node)
    if len(arg_order) == 0:
        for arg in _list(node, "args"):
            if isinstance(arg, dict):
                arg_name = _str(arg, "arg")
                if arg_name != "":
                    arg_order.append(arg_name)
                    if arg_name not in arg_types:
                        arg_types[arg_name] = _str(arg, "resolved_type")
    params: list[str] = []
    for raw_arg_name in arg_order:
        arg_name = _safe_name(ctx, raw_arg_name)
        params.append(_render_type(ctx, arg_types.get(raw_arg_name, "")) + " " + arg_name)
    return "(" + ", ".join(params) + ") => " + _emit_expr(ctx, node.get("body"))


def _super_ctor_call(node: dict[str, JsonVal]) -> tuple[bool, list[str]]:
    body = _list(node, "body")
    if len(body) == 0:
        return (False, [])
    first = body[0]
    if not isinstance(first, dict) or _str(first, "kind") != "Expr":
        return (False, [])
    value = first.get("value")
    if not isinstance(value, dict) or _str(value, "kind") != "Call":
        return (False, [])
    func = value.get("func")
    if not isinstance(func, dict) or _str(func, "kind") != "Attribute" or _str(func, "attr") != "__init__":
        return (False, [])
    owner = func.get("value")
    if not isinstance(owner, dict) or _str(owner, "kind") != "Call":
        return (False, [])
    owner_func = owner.get("func")
    if not isinstance(owner_func, dict) or _str(owner_func, "kind") != "Name" or _str(owner_func, "id") != "super":
        return (False, [])
    return (True, [_emit_expr(EmitContext(mapping=node.get("mapping", RuntimeMapping())), arg) for arg in _list(value, "args")])


def _emit_attribute(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    owner_node = node.get("value")
    attr_name = _str(node, "attr")
    if attr_name == "__name__" and isinstance(owner_node, dict):
        if _str(owner_node, "kind") == "Call" and _call_builtin_name(owner_node) == "type":
            args = _list(owner_node, "args")
            if len(args) >= 1:
                return _emit_expr(ctx, args[0]) + ".GetType().Name"
    if _is_module_owner(ctx, owner_node):
        module_id = ""
        if isinstance(owner_node, dict):
            module_id = _str(owner_node, "runtime_module_id")
            if module_id == "":
                module_id = ctx.import_alias_modules.get(_str(owner_node, "id"), "")
        resolved = _resolve_runtime_module_member(ctx.mapping, module_id, attr_name)
        if resolved != "":
            return resolved
    owner = _emit_expr(ctx, owner_node)
    attr = _safe_cs_ident(attr_name)
    owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
    if is_cs_path_type(owner_type) and attr_name in CS_PATH_MEMBER_NAMES:
        return owner + "." + attr + "()"
    if attr_name in ctx.class_properties.get(owner_type, set()):
        return owner + "." + attr + "()"
    return owner + "." + attr


def _is_module_owner(ctx: EmitContext, node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    owner_id = _str(node, "id")
    return _str(node, "resolved_type") == "module" or owner_id in ctx.import_alias_modules


def _call_builtin_name(node: dict[str, JsonVal]) -> str:
    func = node.get("func")
    if isinstance(func, dict):
        kind = _str(func, "kind")
        if kind == "Name":
            return _str(func, "id")
        if kind == "Attribute":
            return _str(func, "attr")
    return ""


def _is_super_call(node: JsonVal) -> bool:
    if not isinstance(node, dict) or _str(node, "kind") != "Call":
        return False
    func = node.get("func")
    return isinstance(func, dict) and _str(func, "kind") == "Name" and _str(func, "id") == "super"


def _base_class_has_method(ctx: EmitContext, class_name: str, method_name: str) -> bool:
    base_name = ctx.class_bases.get(class_name, "")
    while base_name != "":
        if method_name in ctx.class_methods.get(base_name, set()):
            return True
        base_name = ctx.class_bases.get(base_name, "")
    return False


def _render_expr_with_preferred_type(ctx: EmitContext, node: JsonVal, preferred_type: str = "") -> str:
    if not isinstance(node, dict):
        return _emit_expr(ctx, node)
    kind = _str(node, "kind")
    if kind == "Box":
        return _render_expr_with_preferred_type(ctx, node.get("value"), preferred_type=preferred_type)
    if kind == "Unbox":
        return _emit_unbox(ctx, node)
    if kind == "Call" and _bool(node, "yields_dynamic") and preferred_type != "":
        return _coerce_dynamic_expr(ctx, _emit_expr(ctx, node), preferred_type)
    if preferred_type.startswith("callable[") and kind == "Name":
        return _safe_name(ctx, _str(node, "id"))
    if preferred_type.startswith("callable[") and kind == "Lambda":
        return _emit_expr(ctx, node)
    if preferred_type in ("callable", "Callable") and kind == "Name":
        return _safe_name(ctx, _str(node, "id"))
    if preferred_type in ("callable", "Callable") and kind == "Lambda":
        return _emit_expr(ctx, node)
    if kind == "Subscript":
        owner_node = node.get("value")
        owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
        slice_node = node.get("slice")
        is_slice = isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice"
        numeric_pref_types = {
            "int", "byte", "int8", "int16", "int32", "int64",
            "uint8", "uint16", "uint32", "uint64",
        }
        if owner_type == "str" and not is_slice and preferred_type in numeric_pref_types:
            return "((" + _render_type(ctx, preferred_type) + ")py_runtime.py_ord(" + _emit_expr(ctx, node) + "))"
        if preferred_type == "str":
            return "py_runtime.py_to_string(" + _emit_expr(ctx, node) + ")"
        rendered_preferred_type = _render_type(ctx, preferred_type) if preferred_type != "" else ""
        if rendered_preferred_type.endswith("[]") and (
            owner_type == "tuple" or owner_type.startswith("tuple[") or owner_type.endswith("[]") or _is_dynamic_resolved_type(owner_type)
        ):
            elem_type = rendered_preferred_type[:-2]
            return "py_runtime.py_array_cast<" + elem_type + ">(" + _emit_expr(ctx, node) + ")"
        if preferred_type not in ("", "object", "Obj", "Any", "unknown") and (
            owner_type == "tuple" or owner_type.startswith("tuple[") or owner_type.endswith("[]") or _is_dynamic_resolved_type(owner_type)
        ):
            return "((" + _render_type(ctx, preferred_type) + ")" + _emit_expr(ctx, node) + ")"
    if kind == "BinOp" and preferred_type in ("int8", "int16", "int32", "uint8", "uint16", "uint32"):
        return "((" + _render_type(ctx, preferred_type) + ")" + _emit_expr(ctx, node) + ")"
    if kind == "List":
        return _render_list_literal(ctx, node, preferred_type=preferred_type)
    if kind == "Set":
        return _render_set_literal(ctx, node, preferred_type=preferred_type)
    if kind == "Dict":
        return _render_dict_literal(ctx, node, preferred_type=preferred_type)
    if kind == "Call" and preferred_type != "":
        func = node.get("func")
        if isinstance(func, dict) and _str(func, "kind") == "Name":
            func_name = _str(func, "id")
            if func_name in ("list", "dict", "set", "bytes", "bytearray", "tuple"):
                cloned = dict(node)
                cloned["resolved_type"] = preferred_type
                return _emit_expr(ctx, cloned)
    return _emit_expr(ctx, node)


def _container_method_call(
    ctx: EmitContext,
    owner_expr: str,
    owner_type: str,
    method_name: str,
    args: list[str],
) -> str:
    list_marker = ""
    for key in (owner_type + "." + method_name, "list." + method_name):
        if key in ctx.mapping.calls:
            list_marker = ctx.mapping.calls[key]
            break
    dict_marker = ctx.mapping.calls.get("dict." + method_name, "")
    set_marker = ctx.mapping.calls.get("set." + method_name, "")
    str_marker = ctx.mapping.calls.get("str." + method_name, "")

    if owner_type.startswith("list[") or owner_type in ("bytes", "bytearray"):
        if list_marker == "py_runtime.py_append" and len(args) >= 1:
            return "py_runtime.py_append(" + owner_expr + ", " + args[0] + ")"
        if list_marker == "py_runtime.extend" and len(args) >= 1:
            return "py_runtime.extend(" + owner_expr + ", " + args[0] + ")"
        if list_marker == "py_runtime.py_pop":
            if len(args) >= 1:
                return "py_runtime.py_pop(" + owner_expr + ", " + args[0] + ")"
            return "py_runtime.py_pop(" + owner_expr + ")"
        if list_marker == "py_runtime.clear":
            return "py_runtime.clear(" + owner_expr + ")"
    if owner_type.startswith("dict["):
        if dict_marker == "py_runtime.get" and len(args) >= 1:
            default_expr = args[1] if len(args) > 1 else "null"
            temp_name = _next_temp(ctx, "__dict_value")
            return "(" + owner_expr + ".TryGetValue(" + args[0] + ", out var " + temp_name + ") ? " + temp_name + " : " + default_expr + ")"
        if dict_marker == "py_runtime.py_dict_items":
            return "py_runtime.py_dict_items(" + owner_expr + ")"
        if dict_marker == "py_runtime.py_dict_keys":
            key_type = "object"
            inner = owner_type[5:-1].strip()
            parts = [part.strip() for part in inner.split(",", 1)]
            if len(parts) >= 1 and parts[0] != "":
                key_type = _render_type(ctx, parts[0])
            return "new List<" + key_type + ">(" + owner_expr + ".Keys)"
        if dict_marker == "py_runtime.py_dict_values":
            value_type = "object"
            inner2 = owner_type[5:-1].strip()
            parts2 = [part.strip() for part in inner2.split(",", 1)]
            if len(parts2) == 2 and parts2[1] != "":
                value_type = _render_type(ctx, parts2[1])
            return "new List<" + value_type + ">(" + owner_expr + ".Values)"
    if owner_type.startswith("set["):
        if set_marker == "py_runtime.py_set_add" and len(args) >= 1:
            return owner_expr + ".Add(" + args[0] + ")"
        if set_marker in ("py_runtime.py_set_discard", "py_runtime.py_set_remove") and len(args) >= 1:
            return owner_expr + ".Remove(" + args[0] + ")"
    if owner_type == "str":
        if str_marker == "py_runtime.join" and len(args) == 1:
            return "string.Join(" + owner_expr + ", " + args[0] + ")"
        if str_marker == "py_runtime.count":
            return "py_runtime.count(" + owner_expr + (", " + ", ".join(args) if len(args) > 0 else "") + ")"
        if str_marker == "py_runtime.find":
            return "py_runtime.find(" + owner_expr + (", " + ", ".join(args) if len(args) > 0 else "") + ")"
        if str_marker == "py_runtime.index":
            return "py_runtime.index(" + owner_expr + (", " + ", ".join(args) if len(args) > 0 else "") + ")"
        if str_marker == "py_runtime.rfind":
            return "py_runtime.rfind(" + owner_expr + (", " + ", ".join(args) if len(args) > 0 else "") + ")"
        if str_marker == "py_runtime.split":
            return "py_runtime.split(" + owner_expr + (", " + ", ".join(args) if len(args) > 0 else "") + ")"
        if str_marker == "py_runtime.isspace":
            return "py_runtime.isspace(" + owner_expr + ")"
        if str_marker == "py_runtime.isalnum":
            return "py_runtime.isalnum(" + owner_expr + ")"
        if str_marker == "py_runtime.lower":
            return "py_runtime.lower(" + owner_expr + ")"
        if str_marker == "py_runtime.lstrip":
            return "py_runtime.lstrip(" + owner_expr + (", " + ", ".join(args) if len(args) > 0 else "") + ")"
    return ""


def _emit_builtin_ctor(ctx: EmitContext, func_name: str, node: dict[str, JsonVal], args: list[str]) -> str:
    resolved_ctor_type = _str(node, "resolved_type")
    target_type = _render_type(ctx, resolved_ctor_type if resolved_ctor_type != "" else func_name)
    if func_name == "bool":
        if len(args) == 0:
            return "false"
        return "py_runtime.py_bool(" + args[0] + ")"
    if func_name == "bytearray":
        if len(args) == 0:
            return "new List<byte>()"
        raw_args = _list(node, "args")
        first_arg = raw_args[0] if len(raw_args) > 0 else None
        arg_type = _str(first_arg, "resolved_type") if isinstance(first_arg, dict) else ""
        if arg_type in ("int", "int32", "int64", "byte", "uint8"):
            return "py_runtime.py_bytearray(" + args[0] + ")"
        return "py_runtime.py_bytes(" + args[0] + ")"
    if func_name == "bytes":
        if len(args) == 0:
            return "new List<byte>()"
        return "py_runtime.py_bytes(" + args[0] + ")"
    if func_name == "list":
        if len(args) == 0:
            return "new " + target_type + "()"
        return "new " + target_type + "(" + args[0] + ")"
    if func_name == "dict":
        if len(args) == 0:
            return "new " + target_type + "()"
    if func_name == "set":
        if len(args) == 0:
            if target_type.startswith("HashSet<") and target_type.endswith("[]>"):
                elem_type = target_type[len("HashSet<"):-3]
                return "new " + target_type + "(py_runtime.array_comparer<" + elem_type + ">())"
            return "new " + target_type + "()"
        return "new " + target_type + "(" + args[0] + ")"
    if func_name == "tuple":
        return "new " + target_type + " { " + ", ".join(args) + " }"
    if is_cs_exception_type(func_name):
        if len(args) == 0:
            return "new " + target_type + "()"
        return "new " + target_type + "(" + ", ".join(args) + ")"
    return "new " + target_type + "(" + ", ".join(args) + ")"


def _render_cast_expr(ctx: EmitContext, node: dict[str, JsonVal], args: list[str]) -> str:
    target_type = _render_type(ctx, _str(node, "resolved_type"))
    if len(args) == 0:
        return ""
    if target_type == "bool":
        return "py_runtime.py_bool(" + args[-1] + ")"
    raw_args = _list(node, "args")
    if len(args) == 1 and len(raw_args) >= 1 and isinstance(raw_args[0], dict):
        src_type = _str(raw_args[0], "resolved_type")
        if src_type == "bool" and target_type in ("double", "float"):
            true_lit = "1.0" if target_type == "double" else "1.0f"
            false_lit = "0.0" if target_type == "double" else "0.0f"
            return "(" + args[0] + " ? " + true_lit + " : " + false_lit + ")"
    if len(args) == 1:
        return "((" + target_type + ")(" + args[0] + "))"
    return "((" + target_type + ")(" + args[-1] + "))"


def _render_param_default(
    ctx: EmitContext,
    arg_name: str,
    src_type: str,
    default_node: JsonVal,
) -> tuple[str, str]:
    if not isinstance(default_node, dict):
        return ("", "")
    rendered_type = _render_type(ctx, src_type)
    if src_type.startswith("list[") or src_type.startswith("dict[") or src_type.startswith("set["):
        default_expr = _render_expr_with_preferred_type(ctx, default_node, preferred_type=src_type)
        return (" = null", "if (" + arg_name + " == null) { " + arg_name + " = " + default_expr + "; }")
    if rendered_type in ("string", "object") or rendered_type.startswith("List<") or rendered_type.startswith("Dictionary<") or rendered_type.startswith("HashSet<"):
        if rendered_type.startswith("List<") or rendered_type.startswith("Dictionary<") or rendered_type.startswith("HashSet<"):
            default_expr = _render_expr_with_preferred_type(ctx, default_node, preferred_type=src_type)
            return (" = null", "if (" + arg_name + " == null) { " + arg_name + " = " + default_expr + "; }")
        if _str(default_node, "kind") == "Constant" and default_node.get("value") is None:
            return (" = null", "")
        return (" = " + _render_expr_with_preferred_type(ctx, default_node, preferred_type=src_type), "")
    if _str(default_node, "kind") == "Constant" and default_node.get("value") is None:
        return (" = null", "")
    return (" = " + _render_expr_with_preferred_type(ctx, default_node, preferred_type=src_type), "")


def _class_name_from_tid_constant(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    const_name = _str(node, "id")
    if const_name == "":
        return ""
    for type_name in sorted(ctx.class_names | ctx.trait_names, key=len, reverse=True):
        if const_name.endswith(_safe_cs_ident(type_name).upper() + "_TID"):
            return type_name
    return ""


def _emit_call(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    func = node.get("func")
    preferred_arg_types: list[str] = []
    if isinstance(func, dict) and _str(func, "kind") == "Name":
        preferred_arg_types = ctx.function_arg_types.get(_str(func, "id"), [])
    args: list[str] = []
    for idx, arg in enumerate(_list(node, "args")):
        preferred_type = preferred_arg_types[idx] if idx < len(preferred_arg_types) else ""
        if preferred_type == "" and isinstance(arg, dict):
            preferred_type = _str(arg, "call_arg_type")
        args.append(_render_expr_with_preferred_type(ctx, arg, preferred_type=preferred_type))
    keyword_args: list[str] = []
    for keyword in _list(node, "keywords"):
        if not isinstance(keyword, dict):
            continue
        name = _str(keyword, "arg")
        value = keyword.get("value")
        if name == "":
            continue
        keyword_args.append(_safe_cs_ident(name) + ": " + _emit_expr(ctx, value))
    call_parts = list(args) + keyword_args
    runtime_call = _str(node, "runtime_call")
    builtin_name = _call_builtin_name(node)
    adapter = _str(node, "runtime_call_adapter_kind")
    owner_expr = ""
    owner_type = ""
    prepend_owner = False
    runtime_owner = node.get("runtime_owner")
    if isinstance(runtime_owner, dict):
        owner_expr = _emit_expr(ctx, runtime_owner)
        owner_type = _str(runtime_owner, "resolved_type")
        prepend_owner = True
    if isinstance(func, dict) and _str(func, "kind") == "Attribute":
        owner_node = func.get("value")
        attr_name = _str(func, "attr")
        if attr_name == "cast":
            return _render_cast_expr(ctx, node, args)
        if _is_super_call(owner_node) and ctx.current_base_class_name != "":
            return "base." + _safe_cs_ident(attr_name) + "(" + ", ".join(args) + ")"
        owner_expr = _emit_expr(ctx, owner_node)
        owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else owner_type
        prepend_owner = not _is_module_owner(ctx, owner_node)
        if _is_module_owner(ctx, owner_node):
            module_id = ""
            if isinstance(owner_node, dict):
                module_id = _str(owner_node, "runtime_module_id")
                if module_id == "":
                    module_id = ctx.import_alias_modules.get(_str(owner_node, "id"), "")
            if attr_name == "cast":
                return _render_cast_expr(ctx, node, args)
            mapped_ctor_type = ctx.mapping.types.get(attr_name, "")
            if isinstance(mapped_ctor_type, str) and mapped_ctor_type != "":
                return "new " + _render_type(ctx, attr_name) + "(" + ", ".join(call_parts) + ")"
            resolved_module_call = _resolve_runtime_module_member(ctx.mapping, module_id, attr_name)
            if resolved_module_call != "":
                if resolved_module_call == "__CAST__":
                    if len(args) == 1:
                        return "((" + _render_type(ctx, _str(node, "resolved_type")) + ")" + args[0] + ")"
                    return args[0] if len(args) > 0 else ""
                return resolved_module_call + "(" + ", ".join(call_parts) + ")"
        container_call = _container_method_call(ctx, owner_expr, owner_type, attr_name, args)
        if container_call != "":
            return container_call
    if isinstance(func, dict) and _str(func, "kind") == "Name":
        func_name = _str(func, "id")
        if func_name == "cast":
            return _render_cast_expr(ctx, node, args)
        if func_name in ("bool", "bytearray", "bytes", "list", "dict", "set", "tuple"):
            return _emit_builtin_ctor(ctx, func_name, node, call_parts)
        if func_name in ctx.runtime_imports and "." in ctx.runtime_imports[func_name]:
            return _maybe_cast_dynamic_call(ctx, node, ctx.runtime_imports[func_name] + "(" + ", ".join(call_parts) + ")")
        if func_name == "str":
            if len(args) == 0:
                return "\"\""
            return "py_runtime.py_to_string(" + args[0] + ")"
        mapped_ctor_type = ctx.mapping.types.get(func_name, "")
        if isinstance(mapped_ctor_type, str) and mapped_ctor_type != "" and (
            _str(node, "resolved_type") == func_name
            or _str(func, "resolved_type") == "type"
            or func_name in ctx.import_alias_modules
        ):
            return "new " + _render_type(ctx, func_name) + "(" + ", ".join(call_parts) + ")"
        if _str(func, "resolved_type") == "type":
            if func_name in ctx.import_alias_modules:
                module_id = ctx.import_alias_modules.get(func_name, "")
                if module_id != "" and not should_skip_module(module_id, ctx.mapping):
                    return "new " + _module_class_name(module_id) + "." + _safe_name(ctx, func_name) + "(" + ", ".join(call_parts) + ")"
            return _emit_builtin_ctor(ctx, func_name, node, call_parts)
        if func_name in ctx.import_alias_modules:
            module_id = ctx.import_alias_modules.get(func_name, "")
            if module_id != "" and not should_skip_module(module_id, ctx.mapping):
                mapped_ctor_type = ctx.mapping.types.get(func_name, "")
                if isinstance(mapped_ctor_type, str) and mapped_ctor_type != "":
                    return "new " + _render_type(ctx, func_name) + "(" + ", ".join(call_parts) + ")"
                return _module_class_name(module_id) + "." + _safe_name(ctx, func_name) + "(" + ", ".join(call_parts) + ")"
        if owner_expr != "":
            owner_call = _container_method_call(ctx, owner_expr, owner_type, func_name, args)
            if owner_call != "":
                return _maybe_cast_dynamic_call(ctx, node, owner_call)
    if isinstance(func, dict) and _str(func, "kind") == "Lambda":
        delegate_type = _render_type(ctx, _str(func, "resolved_type"))
        return "((" + delegate_type + ")(" + _emit_expr(ctx, func) + "))(" + ", ".join(call_parts) + ")"
    resolved = ""
    if runtime_call != "" or adapter != "":
        resolved = resolve_runtime_call(runtime_call, builtin_name, adapter, ctx.mapping)
    elif builtin_name in ctx.mapping.calls:
        resolved = resolve_runtime_call(runtime_call, builtin_name, adapter, ctx.mapping)
    if resolved == "__CAST__":
        return _render_cast_expr(ctx, node, args)
    if resolved != "" and not resolved.startswith("__"):
        call_args = list(call_parts)
        if prepend_owner and owner_expr != "":
            call_args = [owner_expr] + call_args
        return _maybe_cast_dynamic_call(ctx, node, resolved + "(" + ", ".join(call_args) + ")")
    if isinstance(func, dict) and _str(func, "kind") == "Name":
        if (
            ctx.current_class_name != ""
            and _str(func, "id") in ctx.module_function_names
            and _str(func, "id") not in ctx.runtime_imports
            and _str(func, "id") not in ctx.import_alias_modules
        ):
            qualified = _module_class_name(ctx.module_id) + "." + _safe_name(ctx, _str(func, "id"))
            return _maybe_cast_dynamic_call(ctx, node, qualified + "(" + ", ".join(call_parts) + ")")
        return _maybe_cast_dynamic_call(ctx, node, _safe_name(ctx, _str(func, "id")) + "(" + ", ".join(call_parts) + ")")
    fallback_callee = _emit_expr(ctx, func)
    ctor_type = _str(node, "resolved_type")
    mapped_ctor_type = ctx.mapping.types.get(ctor_type, "")
    if isinstance(mapped_ctor_type, str) and mapped_ctor_type != "":
        rendered_ctor_type = _render_type(ctx, ctor_type)
        if fallback_callee == rendered_ctor_type or fallback_callee == _safe_name(ctx, ctor_type):
            return "new " + rendered_ctor_type + "(" + ", ".join(call_parts) + ")"
    return _maybe_cast_dynamic_call(ctx, node, fallback_callee + "(" + ", ".join(call_parts) + ")")


def _emit_condition_expr(ctx: EmitContext, node: JsonVal, *, wrap: bool = True) -> str:
    expr = _emit_expr(ctx, node)
    if isinstance(node, dict):
        rt = _str(node, "resolved_type")
        if rt != "" and rt != "bool":
            expr = "py_runtime.py_bool(" + expr + ")"
    if wrap:
        return "(" + expr + ")"
    return expr


def _is_dynamic_resolved_type(resolved_type: str) -> bool:
    return resolved_type in ("", "Any", "object", "Obj", "unknown", "JsonVal", "Node")


def _coerce_dynamic_expr(ctx: EmitContext, expr: str, resolved_type: str) -> str:
    if _is_dynamic_resolved_type(resolved_type):
        return expr
    if _render_type(ctx, resolved_type) == "Dictionary<string, object>":
        return "py_runtime.py_dict_string_object(" + expr + ")"
    return "((" + _render_type(ctx, resolved_type) + ")" + expr + ")"


def _maybe_cast_dynamic_call(ctx: EmitContext, node: dict[str, JsonVal], expr: str) -> str:
    if not _bool(node, "yields_dynamic"):
        return expr
    return _coerce_dynamic_expr(ctx, expr, _str(node, "resolved_type"))


def _emit_list_repeat(ctx: EmitContext, left_node: JsonVal, right_node: JsonVal, result_type: str) -> str:
    left_expr = _emit_expr(ctx, left_node)
    right_expr = _emit_expr(ctx, right_node)
    if isinstance(right_node, dict) and _str(right_node, "resolved_type").startswith("list["):
        left_expr, right_expr = right_expr, left_expr
    target_type = _render_type(ctx, result_type)
    return "py_runtime.py_repeat<" + target_type[5:-1] + ">(" + left_expr + ", " + right_expr + ")"


def _emit_binop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    op = _str(node, "op")
    if op == "FloorDiv":
        left = _emit_expr(ctx, node.get("left"))
        right = _emit_expr(ctx, node.get("right"))
        return "py_runtime.py_floordiv(" + left + ", " + right + ")"
    if op == "Div":
        left = _emit_expr(ctx, node.get("left"))
        right = _emit_expr(ctx, node.get("right"))
        if _str(node, "resolved_type") == "float32":
            return "(((float)(" + left + ")) / (" + right + "))"
        return "(((double)(" + left + ")) / (" + right + "))"
    if op == "Add":
        result_type = _str(node, "resolved_type")
        if result_type.startswith("list[") or result_type in ("bytes", "bytearray"):
            left = _emit_expr(ctx, node.get("left"))
            right = _emit_expr(ctx, node.get("right"))
            return "py_runtime.py_concat(" + left + ", " + right + ")"
    if op == "Mult":
        left_node = node.get("left")
        right_node = node.get("right")
        left_type = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
        right_type = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""
        result_type = _str(node, "resolved_type")
        if left_type.startswith("list[") or right_type.startswith("list["):
            return _emit_list_repeat(ctx, left_node, right_node, result_type)
        if result_type == "str" and (left_type == "str" or right_type == "str"):
            left = _emit_expr(ctx, left_node)
            right = _emit_expr(ctx, right_node)
            if right_type == "str":
                left, right = right, left
            return "py_runtime.repeat_string(" + left + ", " + right + ")"
    rendered = CommonRenderer.render_binop(_CsExprCommonRenderer(ctx), node)
    if op in ("LShift", "RShift"):
        left_text = _emit_expr(ctx, node.get("left"))
        right_text = _emit_expr(ctx, node.get("right"))
        shift = ">>" if op == "RShift" else "<<"
        rendered = "(" + left_text + " " + shift + " ((int)" + right_text + "))"
    if _str(node, "resolved_type") in ("int8", "int16", "int32", "uint8", "uint16", "uint32"):
        return "((" + _render_type(ctx, _str(node, "resolved_type")) + ")" + rendered + ")"
    return rendered


def _emit_compare(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return _emit_expr(ctx, left_node)
    current_left = _emit_expr(ctx, left_node)
    current_left_type = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
    parts: list[str] = []
    for idx, comparator in enumerate(comparators):
        op_obj = ops[idx] if idx < len(ops) else None
        op_name = op_obj if isinstance(op_obj, str) else _str(op_obj, "kind") if isinstance(op_obj, dict) else ""
        right = _emit_expr(ctx, comparator)
        right_type = _str(comparator, "resolved_type") if isinstance(comparator, dict) else ""
        if op_name == "In":
            parts.append("py_runtime.py_in(" + current_left + ", " + right + ")")
        elif op_name == "NotIn":
            parts.append("(!py_runtime.py_in(" + current_left + ", " + right + "))")
        elif op_name == "Eq":
            parts.append("py_runtime.py_eq(" + current_left + ", " + right + ")")
        elif op_name == "NotEq":
            parts.append("(!py_runtime.py_eq(" + current_left + ", " + right + "))")
        elif current_left_type == "str" and right_type == "str" and op_name in ("Lt", "LtE", "Gt", "GtE"):
            compare_expr = "string.CompareOrdinal(" + current_left + ", " + right + ")"
            compare_op = {
                "Lt": "<",
                "LtE": "<=",
                "Gt": ">",
                "GtE": ">=",
            }.get(op_name, "==")
            parts.append("(" + compare_expr + " " + compare_op + " 0)")
        else:
            op_text = {
                "Lt": "<",
                "LtE": "<=",
                "Gt": ">",
                "GtE": ">=",
                "Is": "==",
                "IsNot": "!=",
            }.get(op_name, op_name)
            parts.append("(" + current_left + " " + op_text + " " + right + ")")
        current_left = right
        current_left_type = right_type
    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _emit_boolop(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    if len(values) == 0:
        return "false"
    if len(values) == 1:
        return _emit_expr(ctx, values[0])
    rendered = [_emit_expr(ctx, value) for value in values]
    if _str(node, "resolved_type") == "bool":
        op_text = "&&" if _str(node, "op") == "And" else "||"
        wrapped = [_emit_condition_expr(ctx, value, wrap=False) for value in values]
        return "(" + (" " + op_text + " ").join(wrapped) + ")"
    result = rendered[-1]
    for idx in range(len(rendered) - 2, -1, -1):
        current = rendered[idx]
        test = "py_runtime.py_bool(" + current + ")"
        if _str(node, "op") == "And":
            result = "(" + test + " ? " + result + " : " + current + ")"
        else:
            result = "(" + test + " ? " + current + " : " + result + ")"
    return result


def _tuple_target_bindings(ctx: EmitContext, target: JsonVal, source_expr: str, *, declare: bool) -> list[str]:
    if not isinstance(target, dict) or _str(target, "kind") != "Tuple":
        return []
    lines: list[str] = []
    for idx, elem in enumerate(_list(target, "elements")):
        if not isinstance(elem, dict) or _str(elem, "kind") != "Name":
            continue
        raw_name = _str(elem, "id")
        if raw_name == "":
            continue
        safe_name = _safe_name(ctx, raw_name)
        elem_type = _str(elem, "resolved_type")
        cs_elem_type = _render_type(ctx, elem_type) if elem_type != "" else "object"
        source_item = source_expr + "[" + str(idx) + "]"
        value_expr = source_item if cs_elem_type == "object" else "((" + cs_elem_type + ")" + source_item + ")"
        if declare:
            ctx.var_types[safe_name] = elem_type
            lines.append(cs_elem_type + " " + safe_name + " = " + value_expr + ";")
        else:
            lines.append(safe_name + " = " + value_expr + ";")
    return lines


def _iter_target_decl_type(ctx: EmitContext, target_node: JsonVal, iter_node: JsonVal) -> str:
    if not isinstance(target_node, dict):
        return "var"
    kind = _str(target_node, "kind")
    if kind == "Tuple":
        return "object[]"
    if kind not in ("Name", "NameTarget"):
        return "var"
    target_rt = _str(target_node, "resolved_type")
    if target_rt == "":
        target_rt = _str(target_node, "target_type")
    runtime_call = _iter_expr_runtime_call(iter_node)
    if runtime_call in ("enumerate", "py_enumerate_object", "zip", "dict.items", "items"):
        return "object[]"
    if target_rt == "str" and isinstance(iter_node, dict) and _str(iter_node, "resolved_type") == "str":
        return "char"
    if target_rt != "":
        return _render_type(ctx, target_rt)
    return "var"


def _emit_comprehension(ctx: EmitContext, node: dict[str, JsonVal], comp_kind: str) -> str:
    result_type = _render_type(ctx, _str(node, "resolved_type"))
    result_name = _next_temp(ctx, "__comp")
    iter_name = _next_temp(ctx, "__item")
    lines: list[str] = []
    lines.append("(new Func<" + result_type + ">(() => {")
    if comp_kind == "list":
        lines.append("    " + result_type + " " + result_name + " = new " + result_type + "();")
    else:
        lines.append("    " + result_type + " " + result_name + " = new " + result_type + "();")
    generators = _list(node, "generators")
    depth = 1
    target_expr = ""
    for gen in generators:
        if not isinstance(gen, dict):
            continue
        target = gen.get("target")
        target_name = iter_name
        target_type = _iter_target_decl_type(ctx, target, gen.get("iter"))
        target_kind = _str(target, "kind") if isinstance(target, dict) else ""
        if isinstance(target, dict) and _str(target, "kind") == "Name":
            raw_name = _str(target, "id")
            if raw_name != "":
                target_name = _safe_name(ctx, raw_name)
        if target_kind == "Tuple":
            target_name = _next_temp(ctx, "__tuple_item")
        elif target_kind == "Name" and target_type == "char" and _str(target, "resolved_type") == "str":
            target_name = _next_temp(ctx, "__char_item")
        target_expr = target_name
        iter_expr = _emit_expr(ctx, gen.get("iter"))
        iter_node = gen.get("iter")
        if isinstance(iter_node, dict) and _str(iter_node, "resolved_type").startswith("dict["):
            iter_expr = iter_expr + ".Keys"
        lines.append("    " * depth + "foreach (" + target_type + " " + target_name + " in " + iter_expr + ") {")
        depth += 1
        if isinstance(target, dict):
            if target_kind == "Tuple":
                for bind_line in _tuple_target_bindings(ctx, target, target_name, declare=True):
                    lines.append("    " * depth + bind_line)
            elif target_kind == "Name":
                raw_name2 = _str(target, "id")
                if raw_name2 != "" and target_type == "char" and _str(target, "resolved_type") == "str":
                    ctx.var_types[_safe_name(ctx, raw_name2)] = "str"
                    lines.append("    " * depth + "string " + _safe_name(ctx, raw_name2) + " = " + target_name + ".ToString();")
        for if_node in _list(gen, "ifs"):
            lines.append("    " * depth + "if (!" + _emit_condition_expr(ctx, if_node) + ") {")
            lines.append("    " * (depth + 1) + "continue;")
            lines.append("    " * depth + "}")
    if comp_kind == "dict":
        lines.append("    " * depth + result_name + "[" + _emit_expr(ctx, node.get("key")) + "] = " + _emit_expr(ctx, node.get("value")) + ";")
    elif comp_kind == "set":
        lines.append("    " * depth + result_name + ".Add(" + _emit_expr(ctx, node.get("elt")) + ");")
    else:
        lines.append("    " * depth + "py_runtime.py_append(" + result_name + ", " + _emit_expr(ctx, node.get("elt")) + ");")
    for _ in generators:
        depth -= 1
        lines.append("    " * depth + "}")
    lines.append("    return " + result_name + ";")
    lines.append("})())")
    _ = target_expr
    return "\n".join(lines)


def _emit_expr(ctx: EmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return "null"
    kind = _str(node, "kind")
    if kind == "IsInstance":
        return _emit_isinstance_expr(ctx, node)
    if kind == "ObjTypeId":
        value = node.get("value")
        return "py_runtime.py_runtime_value_type_id(" + _emit_expr(ctx, value) + ")"
    renderer = _CsExprCommonRenderer(ctx)
    return renderer.render_expr(node)


def _emit_unbox(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    target_type = _str(node, "target")
    if target_type == "":
        target_type = _str(node, "resolved_type")
    value = node.get("value")
    expr = _emit_expr(ctx, value)
    if not isinstance(value, dict):
        return expr
    if target_type == "" or _is_dynamic_resolved_type(target_type):
        return expr
    if _str(value, "resolved_type") == target_type:
        return expr
    return _coerce_dynamic_expr(ctx, expr, target_type)


def _emit_isinstance_expr(ctx: EmitContext, node: dict[str, JsonVal]) -> str:
    value_expr = _emit_expr(ctx, node.get("value"))
    boxed_expr = "((object)(" + value_expr + "))"
    expected_type = _expected_type_name(node.get("expected_type_id"))
    if expected_type == "":
        expected_type = _str(node, "expected_type_name")
    if expected_type == "":
        return "false"
    rendered = _emit_builtin_isinstance_expr(ctx, boxed_expr, expected_type)
    if rendered != "":
        return rendered
    return "false"


class _CsStmtCommonRenderer(CommonRenderer):
    def __init__(self, ctx: EmitContext) -> None:
        self.ctx = ctx
        super().__init__("cs")
        self.profile = load_profile_doc("cs")
        prec = self.profile.get("operators")
        prec_map: dict[str, int] = {}
        if isinstance(prec, dict):
            raw = prec.get("precedence")
            if isinstance(raw, dict):
                for key, value in raw.items():
                    if isinstance(key, str) and isinstance(value, int):
                        prec_map[key] = value
        self._op_prec_table = prec_map
        self.state.lines = ctx.lines
        self.state.indent_level = ctx.indent_level

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(self.ctx, node)

    def render_binop(self, node: dict[str, JsonVal]) -> str:
        return _emit_binop(self.ctx, node)

    def render_compare(self, node: dict[str, JsonVal]) -> str:
        return _emit_compare(self.ctx, node)

    def render_boolop(self, node: dict[str, JsonVal]) -> str:
        return _emit_boolop(self.ctx, node)

    def render_expr(self, node: JsonVal) -> str:
        return _emit_expr(self.ctx, node)

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        _ = node
        raise RuntimeError("cs assign string hook is not used directly")

    def render_condition_expr(self, node: JsonVal) -> str:
        return _emit_condition_expr(self.ctx, node)

    def emit_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_assign_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_return_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        value = node.get("value")
        if isinstance(value, dict):
            self._emit_stmt_line("return " + _emit_expr(self.ctx, value))
        else:
            self._emit_stmt_line("return")
        self.state.indent_level = self.ctx.indent_level

    def emit_expr_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        value = node.get("value")
        if isinstance(value, dict) and _str(value, "kind") == "Name":
            value_id = _str(value, "id")
            if value_id == "continue":
                self._emit_stmt_line("continue")
                self.state.indent_level = self.ctx.indent_level
                return
            if value_id == "break":
                self._emit_stmt_line("break")
                self.state.indent_level = self.ctx.indent_level
                return
        self._emit_stmt_line(_emit_expr(self.ctx, value))
        self.state.indent_level = self.ctx.indent_level

    def render_raise_value(self, node: dict[str, JsonVal]) -> str:
        exc = node.get("exc")
        if not isinstance(exc, dict):
            return ""
        return _emit_expr(self.ctx, exc)

    def render_except_open(self, handler: dict[str, JsonVal]) -> str:
        name = _str(handler, "name")
        if name == "":
            name = "ex"
        type_node = handler.get("type")
        type_name = CS_EXCEPTION_BASE_NAME
        if isinstance(type_node, dict):
            if _str(type_node, "kind") == "Name":
                type_name = cs_type(_str(type_node, "id"), mapping=self.ctx.mapping)
            else:
                type_name = cs_type(_str(type_node, "resolved_type"), mapping=self.ctx.mapping)
        return "catch (" + type_name + " " + _safe_cs_ident(name) + ") {"

    def emit_stmt_extension(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_stmt_extension(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_try_stmt(self, node: dict[str, JsonVal]) -> None:
        body = _list(node, "body")
        handlers = _list(node, "handlers")
        finalbody = _list(node, "finalbody")
        hoisted: list[tuple[str, str]] = []
        seen: set[str] = set()
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            kind = _str(stmt, "kind")
            if kind not in ("Assign", "AnnAssign"):
                continue
            target = stmt.get("target")
            if not isinstance(target, dict) or _str(target, "kind") not in ("Name", "NameTarget"):
                continue
            name = _safe_name(self.ctx, _str(target, "id"))
            if name == "" or name in seen or name in self.ctx.var_types:
                continue
            resolved_type = _str(stmt, "decl_type")
            if resolved_type == "":
                resolved_type = _str(stmt, "resolved_type")
            if resolved_type == "":
                resolved_type = _str(target, "resolved_type")
            seen.add(name)
            hoisted.append((name, resolved_type))
        for name, resolved_type in hoisted:
            self.ctx.var_types[name] = resolved_type if resolved_type != "" else "object"
            decl_type = _render_type(self.ctx, resolved_type if resolved_type != "" else "object")
            init = cs_zero_value(resolved_type, mapping=self.ctx.mapping) if resolved_type != "" else "null"
            self._emit_stmt_line(decl_type + " " + name + " = " + init)
        self._emit("try {")
        self.state.indent_level += 1
        self.emit_body(body)
        self.state.indent_level -= 1
        self._emit("}")
        for raw_handler in handlers:
            if not isinstance(raw_handler, dict):
                continue
            self._emit(self.render_except_open(raw_handler))
            self.state.indent_level += 1
            self.emit_try_handler_body(raw_handler)
            self.state.indent_level -= 1
            self._emit("}")
        if len(finalbody) > 0:
            self._emit("finally {")
            self.state.indent_level += 1
            self.emit_body(finalbody)
            self.state.indent_level -= 1
            self._emit("}")


class _CsExprCommonRenderer(CommonRenderer):
    def __init__(self, ctx: EmitContext) -> None:
        self.ctx = ctx
        super().__init__("cs")
        self.profile = load_profile_doc("cs")
        prec = self.profile.get("operators")
        prec_map: dict[str, int] = {}
        if isinstance(prec, dict):
            raw = prec.get("precedence")
            if isinstance(raw, dict):
                for key, value in raw.items():
                    if isinstance(key, str) and isinstance(value, int):
                        prec_map[key] = value
        self._op_prec_table = prec_map

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(self.ctx, node)

    def render_binop(self, node: dict[str, JsonVal]) -> str:
        return _emit_binop(self.ctx, node)

    def render_compare(self, node: dict[str, JsonVal]) -> str:
        return _emit_compare(self.ctx, node)

    def render_boolop(self, node: dict[str, JsonVal]) -> str:
        return _emit_boolop(self.ctx, node)

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        _ = node
        raise RuntimeError("cs assign hook is not used in expr adapter")

    def render_expr_extension(self, node: dict[str, JsonVal]) -> str:
        kind = _str(node, "kind")
        if kind == "List":
            return _render_list_literal(self.ctx, node)
        if kind == "Set":
            return _render_set_literal(self.ctx, node)
        if kind == "Dict":
            return _render_dict_literal(self.ctx, node)
        if kind == "Subscript":
            return _render_subscript(self.ctx, node)
        if kind == "IfExp":
            return _render_ifexp(self.ctx, node)
        if kind == "Tuple":
            items = [_emit_expr(self.ctx, item) for item in _list(node, "elements")]
            tuple_type = _render_type(self.ctx, _str(node, "resolved_type"))
            return "new " + tuple_type + " { " + ", ".join(items) + " }"
        if kind == "ListComp":
            return _emit_comprehension(self.ctx, node, "list")
        if kind == "SetComp":
            return _emit_comprehension(self.ctx, node, "set")
        if kind == "DictComp":
            return _emit_comprehension(self.ctx, node, "dict")
        if kind == "JoinedStr":
            return _emit_fstring(self.ctx, node)
        if kind == "FormattedValue":
            return _emit_formatted_value(self.ctx, node)
        if kind == "Box":
            return _emit_box(self.ctx, node)
        if kind == "Unbox":
            return _emit_unbox(self.ctx, node)
        if kind == "Lambda":
            return _emit_lambda(self.ctx, node)
        if kind == "Slice":
            return "null"
        if kind == "IsInstance":
            return _emit_isinstance_expr(self.ctx, node)
        if kind == "ObjTypeId":
            value = node.get("value")
            return "py_runtime.py_runtime_value_type_id(" + _emit_expr(self.ctx, value) + ")"
        return "/* unsupported:" + kind + " */"


def _emit_assign_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    target_text = _emit_expr(ctx, target)
    if isinstance(target, dict) and _str(target, "kind") == "Name":
        target_text = _safe_name(ctx, _str(target, "id"))
    preferred_type = _str(node, "decl_type")
    if preferred_type == "" and isinstance(target, dict):
        preferred_type = _str(target, "resolved_type")
    if isinstance(value, dict):
        value_text = _render_expr_with_preferred_type(ctx, value, preferred_type=preferred_type)
    else:
        value_text = cs_zero_value(preferred_type, mapping=ctx.mapping) if preferred_type != "" else "null"
    if isinstance(target, dict) and _str(target, "kind") == "Name" and _str(target, "id") == "_":
        ctx.lines.append("    " * ctx.indent_level + "_ = " + value_text + ";")
        return
    declare = _bool(node, "declare") or _str(node, "kind") == "AnnAssign"
    if isinstance(target, dict) and _str(target, "kind") == "Attribute":
        declare = False
    if isinstance(target, dict) and _str(target, "kind") == "Subscript":
        owner = _emit_expr(ctx, target.get("value"))
        index = _emit_expr(ctx, target.get("slice"))
        ctx.lines.append("    " * ctx.indent_level + "py_runtime.py_set(" + owner + ", " + index + ", " + value_text + ");")
        return
    if isinstance(target, dict) and _str(target, "kind") == "Name":
        if ctx.current_return_type != "" and target_text not in ctx.var_types:
            declare = True
        if target_text in ctx.var_types:
            declare = False
    if declare:
        decl_type = _target_type_from_stmt(ctx, node)
        inferred_type = preferred_type
        if inferred_type == "" and isinstance(value, dict):
            inferred_type = _str(value, "resolved_type")
        ctx.var_types[target_text] = inferred_type if inferred_type != "" else "object"
        ctx.lines.append("    " * ctx.indent_level + decl_type + " " + target_text + " = " + value_text + ";")
        return
    if isinstance(target, dict) and _str(target, "kind") == "Name" and target_text not in ctx.var_types and ctx.current_return_type != "":
        decl_type2 = _target_type_from_stmt(ctx, node)
        inferred_type2 = preferred_type
        if inferred_type2 == "" and isinstance(value, dict):
            inferred_type2 = _str(value, "resolved_type")
        ctx.var_types[target_text] = inferred_type2 if inferred_type2 != "" else "object"
        ctx.lines.append("    " * ctx.indent_level + decl_type2 + " " + target_text + " = " + value_text + ";")
        return
    ctx.lines.append("    " * ctx.indent_level + target_text + " = " + value_text + ";")


def _emit_for_range(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target")
    target = _emit_expr(ctx, target_node)
    if isinstance(target_node, dict) and _str(target_node, "kind") == "Name":
        target = _safe_name(ctx, _str(target_node, "id"))
    loop_var = target
    declared_before = target in ctx.var_types
    if declared_before:
        loop_var = _next_temp(ctx, "__range_item")
    start = _emit_expr(ctx, node.get("start"))
    stop = _emit_expr(ctx, node.get("stop"))
    step = _emit_expr(ctx, node.get("step"))
    indent = "    " * ctx.indent_level
    loop_cond = loop_var + " < " + stop
    loop_inc = loop_var + " += " + step
    step_text = step.strip()
    normalized_step = step_text.replace("(", "").replace(")", "").strip()
    if normalized_step.startswith("-"):
        loop_cond = loop_var + " > " + stop
    ctx.lines.append(indent + "for (long " + loop_var + " = " + start + "; " + loop_cond + "; " + loop_inc + ") {")
    ctx.indent_level += 1
    if declared_before:
        ctx.lines.append("    " * ctx.indent_level + target + " = " + loop_var + ";")
    _emit_stmt_list(ctx, _list(node, "body"))
    ctx.indent_level -= 1
    ctx.lines.append(indent + "}")


def _emit_for_each(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target")
    iter_node = node.get("iter")
    target = _emit_expr(ctx, target_node)
    if isinstance(target_node, dict) and _str(target_node, "kind") in ("Name", "NameTarget"):
        target = _safe_name(ctx, _str(target_node, "id"))
    iter_expr = _emit_expr(ctx, iter_node)
    if isinstance(iter_node, dict) and _str(iter_node, "resolved_type").startswith("dict["):
        iter_expr = iter_expr + ".Keys"
    target_type = _iter_target_decl_type(ctx, target_node, iter_node)
    target_kind = _str(target_node, "kind") if isinstance(target_node, dict) else ""
    loop_name = target
    declared_before = target in ctx.var_types
    existing_type = ctx.var_types.get(target, "")
    raw_target_name = _str(target_node, "id") if isinstance(target_node, dict) else ""
    alias_name = ""
    restore_alias = ""
    if target_kind == "Tuple":
        loop_name = _next_temp(ctx, "__tuple_item")
        ctx.var_types[loop_name] = "object[]"
    elif target_kind == "Name" and target_type == "char" and _str(target_node, "resolved_type") == "str":
        loop_name = _next_temp(ctx, "__char_item")
    elif declared_before and target_kind in ("Name", "NameTarget"):
        loop_name = _next_temp(ctx, "__loop_item")
    elif isinstance(target_node, dict) and target_kind in ("Name", "NameTarget"):
        raw_type = _str(target_node, "resolved_type")
        if raw_type == "":
            raw_type = _str(target_node, "target_type")
        if raw_type != "":
            ctx.var_types[target] = raw_type
    indent = "    " * ctx.indent_level
    ctx.lines.append(indent + "foreach (" + target_type + " " + loop_name + " in " + iter_expr + ") {")
    ctx.indent_level += 1
    if isinstance(target_node, dict):
        if target_kind == "Tuple":
            for bind_line in _tuple_target_bindings(ctx, target_node, loop_name, declare=True):
                ctx.lines.append("    " * ctx.indent_level + bind_line)
        elif target_kind == "Name" and target_type == "char" and _str(target_node, "resolved_type") == "str":
            if declared_before:
                alias_name = _next_temp(ctx, "__char_text")
                ctx.lines.append("    " * ctx.indent_level + "string " + alias_name + " = " + loop_name + ".ToString();")
                if raw_target_name != "":
                    restore_alias = ctx.renamed_symbols.get(raw_target_name, "")
                    ctx.renamed_symbols[raw_target_name] = alias_name
            else:
                ctx.var_types[target] = "str"
                ctx.lines.append("    " * ctx.indent_level + "string " + target + " = " + loop_name + ".ToString();")
        elif declared_before and target_kind in ("Name", "NameTarget") and existing_type != "" and existing_type != _str(target_node, "resolved_type"):
            if raw_target_name != "":
                restore_alias = ctx.renamed_symbols.get(raw_target_name, "")
                ctx.renamed_symbols[raw_target_name] = loop_name
        elif declared_before and target_kind in ("Name", "NameTarget"):
            ctx.lines.append("    " * ctx.indent_level + target + " = " + loop_name + ";")
    _emit_stmt_list(ctx, _list(node, "body"))
    if raw_target_name != "" and (alias_name != "" or (declared_before and existing_type != "" and existing_type != _str(target_node, "resolved_type"))):
        if restore_alias == "":
            ctx.renamed_symbols.pop(raw_target_name, None)
        else:
            ctx.renamed_symbols[raw_target_name] = restore_alias
    ctx.indent_level -= 1
    ctx.lines.append(indent + "}")


def _for_target_name_and_type(target_node: JsonVal) -> tuple[str, str]:
    if not isinstance(target_node, dict):
        return ("_item", "")
    kind = _str(target_node, "kind")
    if kind in ("Name", "NameTarget"):
        name = _str(target_node, "id")
        target_type = _str(target_node, "target_type")
        if target_type == "":
            target_type = _str(target_node, "resolved_type")
        return (name, target_type)
    return ("_item", "")


def _emit_for_core(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    target_node = node.get("target_plan")
    if target_node is None:
        target_node = node.get("target")
    iter_plan = node.get("iter_plan")
    body = _list(node, "body")
    orelse = _list(node, "orelse")
    target_name, target_type = _for_target_name_and_type(target_node)
    safe_target = _safe_name(ctx, target_name) if target_name not in ("", "_item") else "_item"
    if isinstance(iter_plan, dict):
        plan_kind = _str(iter_plan, "kind")
        if plan_kind == "StaticRangeForPlan":
            range_node = dict(iter_plan)
            range_node["target"] = {"kind": "Name", "id": safe_target, "resolved_type": target_type}
            range_node["body"] = body
            _emit_for_range(ctx, range_node)
            if len(orelse) > 0:
                _emit_stmt_list(ctx, orelse)
            return
        if plan_kind == "RuntimeIterForPlan":
            loop_target = target_node
            if not (isinstance(target_node, dict) and _str(target_node, "kind") == "Tuple"):
                loop_target = {"kind": "Name", "id": safe_target, "resolved_type": target_type}
            temp_node = {
                "kind": "For",
                "target": loop_target,
                "iter": iter_plan.get("iter_expr"),
                "body": body,
            }
            _emit_for_each(ctx, temp_node)
            if len(orelse) > 0:
                _emit_stmt_list(ctx, orelse)
            return
    loop_target2: JsonVal = target_node
    if not (isinstance(target_node, dict) and _str(target_node, "kind") == "Tuple"):
        loop_target2 = {"kind": "Name", "id": safe_target, "resolved_type": target_type}
    temp_node2 = {
        "kind": "For",
        "target": loop_target2,
        "iter": node.get("iter"),
        "body": body,
    }
    _emit_for_each(ctx, temp_node2)
    if len(orelse) > 0:
        _emit_stmt_list(ctx, orelse)


def _emit_aug_assign_stmt(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
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
    target_text = _emit_expr(ctx, node.get("target"))
    value_text = _emit_expr(ctx, node.get("value"))
    ctx.lines.append("    " * ctx.indent_level + target_text + " " + symbol + "= " + value_text + ";")


def _emit_function(ctx: EmitContext, node: dict[str, JsonVal], *, force_public: bool = True, static_method: bool = True) -> None:
    saved_function_name = ctx.current_function_name
    ctx.current_function_name = _str(node, "name")
    name = _safe_name(ctx, _str(node, "name"))
    return_type = _str(node, "return_type")
    if return_type == "":
        return_type = "None"
    body = _list(node, "body")
    if return_type == "None":
        for stmt in body:
            if not isinstance(stmt, dict) or _str(stmt, "kind") != "Return":
                continue
            value = stmt.get("value")
            if isinstance(value, dict):
                inferred = _str(value, "resolved_type")
                if inferred not in ("", "None", "none"):
                    return_type = inferred
                    break
    saved_var_types = dict(ctx.var_types)
    ctx.current_return_type = return_type
    arg_order, arg_types = _arg_order_and_types(node)
    arg_defaults = _dict(node, "arg_defaults") if ctx.current_class_name != "" else {}
    vararg_name = _str(node, "vararg_name")
    vararg_type = _str(node, "vararg_type")
    params: list[str] = []
    param_initializers: list[str] = []
    for idx, raw_arg_name in enumerate(arg_order):
        if ctx.current_class_name != "" and idx == 0 and raw_arg_name == "self":
            continue
        if raw_arg_name == vararg_name and vararg_name != "":
            continue
        arg_name = _safe_name(ctx, raw_arg_name)
        src_type = ""
        arg_type = arg_types.get(raw_arg_name)
        if isinstance(arg_type, str):
            src_type = arg_type
        if src_type == "":
            src_type = "object"
        ctx.var_types[arg_name] = src_type
        param_decl = _render_type(ctx, src_type) + " " + arg_name
        if raw_arg_name in arg_defaults:
            default_suffix, init_line = _render_param_default(ctx, arg_name, src_type, arg_defaults.get(raw_arg_name))
            param_decl += default_suffix
            if init_line != "":
                param_initializers.append(init_line)
        params.append(param_decl)
    if vararg_name != "" and vararg_type != "":
        safe_vararg = _safe_name(ctx, vararg_name)
        vararg_list_type = "list[" + vararg_type + "]"
        ctx.var_types[safe_vararg] = vararg_list_type
        if is_cs_path_type(ctx.current_class_name) and _str(node, "name") == "joinpath":
            params.append("params object[] " + safe_vararg)
        else:
            params.append(_render_type(ctx, vararg_list_type) + " " + safe_vararg)
    decorators = _decorators(node)
    is_staticmethod = "staticmethod" in decorators or "classmethod" in decorators
    modifiers: list[str] = []
    emit_static = static_method or (ctx.current_class_name != "" and is_staticmethod)
    if force_public:
        modifiers.append("public")
    if emit_static:
        modifiers.append("static")
    elif ctx.current_class_name != "" and _str(node, "name") != "__init__":
        if _base_class_has_method(ctx, ctx.current_class_name, _str(node, "name")):
            modifiers.append("override")
        else:
            modifiers.append("virtual")
    indent = "    " * ctx.indent_level
    if ctx.current_class_name != "" and _str(node, "name") == "__init__":
        base_init = ""
        if len(body) > 0 and ctx.current_base_class_name != "":
            first = body[0]
            if isinstance(first, dict) and _str(first, "kind") == "Expr":
                value = first.get("value")
                if isinstance(value, dict) and _str(value, "kind") == "Call":
                    func = value.get("func")
                    if isinstance(func, dict) and _str(func, "kind") == "Attribute" and _str(func, "attr") == "__init__":
                        owner = func.get("value")
                        if isinstance(owner, dict) and _str(owner, "kind") == "Call":
                            owner_func = owner.get("func")
                            if isinstance(owner_func, dict) and _str(owner_func, "kind") == "Name" and _str(owner_func, "id") == "super":
                                base_init = " : base(" + ", ".join(_emit_expr(ctx, arg) for arg in _list(value, "args")) + ")"
                                body = body[1:]
        ctx.lines.append(indent + "public " + ctx.current_class_name + "(" + ", ".join(params) + ")" + base_init + " {")
    else:
        signature = " ".join(modifiers + [_render_type(ctx, return_type, for_return=True), name])
        ctx.lines.append(indent + signature + "(" + ", ".join(params) + ") {")
    ctx.indent_level += 1
    for init_line in param_initializers:
        ctx.lines.append("    " * ctx.indent_level + init_line)
    _emit_stmt_list(ctx, body)
    ctx.indent_level -= 1
    ctx.lines.append(indent + "}")
    ctx.var_types = saved_var_types
    ctx.current_function_name = saved_function_name


def _emit_class(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    name = _safe_name(ctx, _str(node, "name"))
    indent = "    " * ctx.indent_level
    base_name = _str(node, "base")
    fqcn = ctx.module_id + "." + _str(node, "name") if ctx.module_id != "" else _str(node, "name")
    is_trait = _is_trait_class(node)
    is_enum_constants = base_name in ("Enum", "IntEnum", "IntFlag")
    implemented_traits = _implemented_traits(node)
    supertypes: list[str] = []
    if base_name != "" and base_name != "object" and not is_enum_constants:
        supertypes.append(_render_type(ctx, base_name))
    for trait_name in implemented_traits:
        rendered_trait = _render_type(ctx, trait_name)
        if rendered_trait not in supertypes:
            supertypes.append(rendered_trait)
    base_spec = (" : " + ", ".join(supertypes)) if len(supertypes) > 0 else ""
    if is_trait:
        ctx.lines.append(indent + "public interface " + name + base_spec + " {")
    elif is_enum_constants:
        ctx.lines.append(indent + "public static class " + name + " {")
    else:
        ctx.lines.append(indent + "public class " + name + base_spec + " {")
    ctx.indent_level += 1
    previous_class = ctx.current_class_name
    previous_base_class = ctx.current_base_class_name
    ctx.current_class_name = name
    ctx.current_base_class_name = base_name
    if is_enum_constants:
        for stmt in _list(node, "body"):
            if not isinstance(stmt, dict):
                continue
            kind = _str(stmt, "kind")
            target = stmt.get("target")
            if kind not in ("Assign", "AnnAssign"):
                continue
            if not isinstance(target, dict) or _str(target, "kind") != "Name":
                continue
            field_name = _safe_name(ctx, _str(target, "id"))
            value = stmt.get("value")
            value_expr = "0L"
            if isinstance(value, dict):
                value_expr = _render_expr_with_preferred_type(ctx, value, preferred_type="int64")
            ctx.lines.append("    " * ctx.indent_level + "public const long " + field_name + " = " + value_expr + ";")
        ctx.current_class_name = previous_class
        ctx.current_base_class_name = previous_base_class
        ctx.indent_level -= 1
        ctx.lines.append(indent + "}")
        return
    if is_trait:
        for stmt in _list(node, "body"):
            if not isinstance(stmt, dict) or _str(stmt, "kind") not in ("FunctionDef", "ClosureDef"):
                continue
            method_name = _safe_name(ctx, _str(stmt, "name"))
            return_type = _str(stmt, "return_type")
            if return_type == "":
                return_type = "None"
            arg_order, arg_types = _arg_order_and_types(stmt)
            params: list[str] = []
            for idx, raw_arg_name in enumerate(arg_order):
                if idx == 0 and raw_arg_name == "self":
                    continue
                params.append(_render_type(ctx, arg_types.get(raw_arg_name, "")) + " " + _safe_name(ctx, raw_arg_name))
            ctx.lines.append("    " * ctx.indent_level + _render_type(ctx, return_type, for_return=True) + " " + method_name + "(" + ", ".join(params) + ");")
        ctx.current_class_name = previous_class
        ctx.current_base_class_name = previous_base_class
        ctx.indent_level -= 1
        ctx.lines.append(indent + "}")
        return
    emitted_fields: set[str] = set()
    is_dataclass = _bool(node, "dataclass")
    static_field_names: set[str] = set()
    dataclass_defaults: dict[str, JsonVal] = {}
    for stmt in _list(node, "body"):
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind != "AnnAssign":
            continue
        target = stmt.get("target")
        if not isinstance(target, dict) or _str(target, "kind") != "Name":
            continue
        field_name = _safe_name(ctx, _str(target, "id"))
        if field_name == "":
            continue
        if is_dataclass:
            value = stmt.get("value")
            if isinstance(value, dict):
                dataclass_defaults[field_name] = value
        elif stmt.get("value") is not None:
            static_field_names.add(field_name)
    if not is_dataclass:
        for stmt in _list(node, "body"):
            if not isinstance(stmt, dict) or _str(stmt, "kind") != "Assign":
                continue
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                static_field_names.add(_emit_expr(ctx, target))
    for field_name, field_type in _dict(node, "field_types").items():
        if isinstance(field_name, str) and isinstance(field_type, str):
            if _safe_name(ctx, field_name) in static_field_names:
                continue
            ctx.lines.append("    " * ctx.indent_level + "public " + _render_type(ctx, field_type) + " " + _safe_name(ctx, field_name) + ";")
            emitted_fields.add(_safe_name(ctx, field_name))
    if is_dataclass and not any(isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef") and _str(stmt, "name") == "__init__" for stmt in _list(node, "body")):
        params: list[str] = []
        assignments: list[str] = []
        saw_default = False
        for field_name, field_type in _dict(node, "field_types").items():
            if not isinstance(field_name, str) or not isinstance(field_type, str):
                continue
            safe_field = _safe_name(ctx, field_name)
            param = _render_type(ctx, field_type) + " " + safe_field
            default_node = dataclass_defaults.get(safe_field)
            if isinstance(default_node, dict):
                param += " = " + _emit_expr(ctx, default_node)
                saw_default = True
            elif saw_default:
                param += " = " + cs_zero_value(field_type, mapping=ctx.mapping)
            params.append(param)
            assignments.append("    " * (ctx.indent_level + 1) + "this." + safe_field + " = " + safe_field + ";")
        ctx.lines.append("    " * ctx.indent_level + "public " + ctx.current_class_name + "(" + ", ".join(params) + ") {")
        for assignment in assignments:
            ctx.lines.append(assignment)
        ctx.lines.append("    " * ctx.indent_level + "}")
    for stmt in _list(node, "body"):
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind == "FunctionDef" or kind == "ClosureDef":
            _emit_function(ctx, stmt, force_public=True, static_method=False)
        elif kind == "AnnAssign":
            target_node = stmt.get("target")
            field_name = _emit_expr(ctx, target_node)
            if isinstance(target_node, dict) and _str(target_node, "kind") == "Name":
                field_name = _safe_name(ctx, _str(target_node, "id"))
            if field_name in emitted_fields:
                continue
            field_type = _target_type_from_stmt(ctx, stmt)
            value = stmt.get("value")
            init = cs_zero_value(_str(stmt, "decl_type"), mapping=ctx.mapping)
            if isinstance(value, dict):
                init = _render_expr_with_preferred_type(ctx, value, preferred_type=_str(stmt, "decl_type"))
            prefix = "public static " if field_name in static_field_names else "public "
            ctx.lines.append("    " * ctx.indent_level + prefix + field_type + " " + field_name + " = " + init + ";")
            emitted_fields.add(field_name)
        elif kind == "Assign":
            target_node2 = stmt.get("target")
            field_name2 = _emit_expr(ctx, target_node2)
            if isinstance(target_node2, dict) and _str(target_node2, "kind") == "Name":
                field_name2 = _safe_name(ctx, _str(target_node2, "id"))
            if field_name2 in emitted_fields:
                continue
            value2 = stmt.get("value")
            field_type2 = "object"
            init2 = "null"
            if isinstance(value2, dict):
                field_type2 = _render_type(ctx, _str(value2, "resolved_type"))
                init2 = _emit_expr(ctx, value2)
            ctx.lines.append("    " * ctx.indent_level + "public static " + field_type2 + " " + field_name2 + " = " + init2 + ";")
            emitted_fields.add(field_name2)
    ctx.current_class_name = previous_class
    ctx.current_base_class_name = previous_base_class
    ctx.indent_level -= 1
    ctx.lines.append(indent + "}")


def _emit_stmt_extension(ctx: EmitContext, node: dict[str, JsonVal]) -> None:
    kind = _str(node, "kind")
    indent = "    " * ctx.indent_level
    if kind == "FunctionDef":
        _emit_function(ctx, node)
        return
    if kind == "ClosureDef":
        _emit_function(ctx, node, force_public=False, static_method=False)
        return
    if kind == "ClassDef":
        _emit_class(ctx, node)
        return
    if kind == "ForRange":
        _emit_for_range(ctx, node)
        return
    if kind == "For":
        _emit_for_each(ctx, node)
        return
    if kind == "ForCore":
        _emit_for_core(ctx, node)
        return
    if kind == "AugAssign":
        _emit_aug_assign_stmt(ctx, node)
        return
    if kind == "Swap":
        left = node.get("left")
        right = node.get("right")
        left_text = _emit_expr(ctx, left)
        right_text = _emit_expr(ctx, right)
        temp_name = _next_temp(ctx, "__swap_tmp")
        temp_type = "object"
        if isinstance(left, dict):
            left_type = _str(left, "resolved_type")
            if left_type != "":
                temp_type = _render_type(ctx, left_type)
        ctx.lines.append(indent + temp_type + " " + temp_name + " = " + left_text + ";")
        if isinstance(left, dict) and _str(left, "kind") == "Subscript":
            ctx.lines.append(indent + "py_runtime.py_set(" + _emit_expr(ctx, left.get("value")) + ", " + _emit_expr(ctx, left.get("slice")) + ", " + right_text + ");")
        else:
            ctx.lines.append(indent + left_text + " = " + right_text + ";")
        if isinstance(right, dict) and _str(right, "kind") == "Subscript":
            ctx.lines.append(indent + "py_runtime.py_set(" + _emit_expr(ctx, right.get("value")) + ", " + _emit_expr(ctx, right.get("slice")) + ", " + temp_name + ");")
        else:
            ctx.lines.append(indent + right_text + " = " + temp_name + ";")
        return
    if kind == "VarDecl":
        name = _safe_name(ctx, _str(node, "name"))
        raw_type = _str(node, "type")
        if raw_type == "":
            raw_type = _str(node, "decl_type")
        if raw_type == "":
            raw_type = "object"
        ctx.var_types[name] = raw_type
        ctx.lines.append(indent + _render_type(ctx, raw_type) + " " + name + " = " + cs_zero_value(raw_type, mapping=ctx.mapping) + ";")
        return
    if kind == "Break":
        ctx.lines.append(indent + "break;")
        return
    if kind == "Continue":
        ctx.lines.append(indent + "continue;")
        return
    if kind == "Import" or kind == "ImportFrom":
        return
    ctx.lines.append(indent + "// unsupported stmt kind: " + kind)


def _emit_stmt_list(ctx: EmitContext, stmts: list[JsonVal]) -> None:
    renderer = _CsStmtCommonRenderer(ctx)
    renderer.state.lines = ctx.lines
    renderer.state.indent_level = ctx.indent_level
    for stmt in stmts:
        renderer.emit_stmt(stmt)
    ctx.indent_level = renderer.state.indent_level


def _emit_main_method(ctx: EmitContext, main_guard_body: list[JsonVal]) -> None:
    indent = "    " * ctx.indent_level
    ctx.lines.append(indent + "public static void Main(string[] args) {")
    ctx.indent_level += 1
    _emit_stmt_list(ctx, main_guard_body)
    ctx.indent_level -= 1
    ctx.lines.append(indent + "}")


def emit_cs_module(east3_doc: dict[str, JsonVal]) -> str:
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

    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "cs" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)
    if module_id == "pytra.built_in.type_id_table":
        return ""
    if should_skip_module(module_id, mapping):
        return ""

    renamed_symbols_raw = east3_doc.get("renamed_symbols")
    renamed_symbols: dict[str, str] = {}
    if isinstance(renamed_symbols_raw, dict):
        for key, value in renamed_symbols_raw.items():
            if isinstance(key, str) and isinstance(value, str):
                renamed_symbols[key] = value

    body = _list(east3_doc, "body")
    main_guard_body = _list(east3_doc, "main_guard_body")
    class_names: set[str] = set()
    trait_names: set[str] = set()
    enum_constant_types: set[str] = set()
    class_bases: dict[str, str] = {}
    class_methods: dict[str, set[str]] = {}
    class_properties: dict[str, set[str]] = {}
    type_id_values: dict[str, int] = {}
    module_function_names: set[str] = set()
    function_arg_types: dict[str, list[str]] = {}
    type_id_table = _dict(lp, "type_id_resolved_v1")
    for key, value in type_id_table.items():
        if isinstance(key, str) and isinstance(value, int):
            type_id_values[key] = value
            tail = key.split(".")[-1]
            if tail != "" and tail not in type_id_values:
                type_id_values[tail] = value
            tid_const = _fqcn_to_tid_const(key)
            if tid_const != "":
                type_id_values[tid_const] = value
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") == "ClassDef":
            name = _str(stmt, "name")
            if name != "":
                class_names.add(name)
                if _is_trait_class(stmt):
                    trait_names.add(name)
                if _str(stmt, "base") in ("Enum", "IntEnum", "IntFlag"):
                    enum_constant_types.add(name)
                base = _str(stmt, "base")
                if base != "":
                    class_bases[name] = base
                methods: set[str] = set()
                props: set[str] = set()
                for member in _list(stmt, "body"):
                    if isinstance(member, dict) and _str(member, "kind") in ("FunctionDef", "ClosureDef"):
                        method_name = _str(member, "name")
                        if method_name != "":
                            methods.add(method_name)
                            if "property" in _decorators(member):
                                props.add(method_name)
                class_methods[name] = methods
                class_properties[name] = props
        elif isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            if fn_name != "":
                module_function_names.add(fn_name)
                arg_order, arg_types = _arg_order_and_types(stmt)
                function_arg_types[fn_name] = [arg_types.get(arg_name, "") for arg_name in arg_order]

    ctx = EmitContext(
        module_id=module_id,
        source_path=_str(east3_doc, "source_path"),
        is_entry=_bool(emit_ctx_meta, "is_entry") if len(emit_ctx_meta) > 0 else False,
        mapping=mapping,
        import_alias_modules=build_import_alias_map(meta),
        runtime_imports=_build_cs_runtime_import_map(meta, mapping),
        class_names=class_names,
        trait_names=trait_names,
        class_bases=class_bases,
        class_methods=class_methods,
        class_properties=class_properties,
        enum_constant_types=enum_constant_types,
        type_id_values=type_id_values,
        module_function_names=module_function_names,
        function_arg_types=function_arg_types,
        renamed_symbols=renamed_symbols,
    )
    class_name = _module_class_name(module_id)

    ctx.lines.append("using System;")
    ctx.lines.append("using System.Collections.Generic;")
    ctx.lines.append("")
    ctx.lines.append("namespace Pytra.CsModule")
    ctx.lines.append("{")
    ctx.indent_level = 1
    ctx.lines.append("    public static class " + class_name)
    ctx.lines.append("    {")
    ctx.indent_level = 2

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind == "FunctionDef" or kind == "ClassDef":
            _emit_stmt_extension(ctx, stmt)
            continue
        if kind == "AnnAssign":
            target_node = stmt.get("target")
            target_name = _emit_expr(ctx, target_node)
            if isinstance(target_node, dict) and _str(target_node, "kind") == "Name":
                target_name = _safe_name(ctx, _str(target_node, "id"))
            decl_type = _target_type_from_stmt(ctx, stmt)
            value = stmt.get("value")
            init = cs_zero_value(_str(stmt, "decl_type"), mapping=ctx.mapping)
            if isinstance(value, dict):
                init = _emit_expr(ctx, value)
            ctx.lines.append("        public static " + decl_type + " " + target_name + " = " + init + ";")
            continue
        if kind == "Assign":
            target_node2 = stmt.get("target")
            target_name2 = _emit_expr(ctx, target_node2)
            if isinstance(target_node2, dict) and _str(target_node2, "kind") == "Name":
                target_name2 = _safe_name(ctx, _str(target_node2, "id"))
            value2 = stmt.get("value")
            init2 = _emit_expr(ctx, value2)
            target_type2 = "object"
            if isinstance(value2, dict):
                target_type2 = cs_type(_str(value2, "resolved_type"), mapping=ctx.mapping)
            ctx.lines.append("        public static " + target_type2 + " " + target_name2 + " = " + init2 + ";")

    if ctx.is_entry:
        if len(body) > 0:
            ctx.lines.append("")
        _emit_main_method(ctx, main_guard_body)

    ctx.indent_level = 1
    ctx.lines.append("    }")
    ctx.lines.append("}")
    return "\n".join(ctx.lines).rstrip() + "\n"
    if func_name == "bytearray":
        if len(args) == 0:
            return "new List<byte>()"
        first_arg = _list(node, "args")[0] if len(_list(node, "args")) > 0 else None
        arg_type = _str(first_arg, "resolved_type") if isinstance(first_arg, dict) else ""
        if arg_type in ("int", "int64", "int32", "uint8", "byte"):
            return "py_runtime.py_bytearray(" + args[0] + ")"
        return "py_runtime.py_bytes(" + args[0] + ")"
    if func_name == "bytes":
        if len(args) == 0:
            return "new List<byte>()"
        return "py_runtime.py_bytes(" + args[0] + ")"
