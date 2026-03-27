"""Type stub EAST3 generator for missing link inputs.

Provides minimal linked-module-compatible EAST3 documents for modules that are
currently outside the selfhost seed set or cannot yet be parsed by the
self-hosted frontend. These stubs are intentionally signature-oriented and are
meant to satisfy link-time completeness checks.
"""

from __future__ import annotations

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path


def _source_path_for_module_id(module_id: str) -> str:
    if module_id == "toolchain2.optimize.passes":
        return "src/toolchain2/optimize/passes/__init__.py"
    return "src/" + module_id.replace(".", "/") + ".py"


def _module_doc(module_id: str, body: list[JsonVal]) -> dict[str, JsonVal]:
    return {
        "kind": "Module",
        "east_stage": 3,
        "schema_version": 1,
        "source_path": _source_path_for_module_id(module_id),
        "body": body,
        "main_guard_body": [],
        "renamed_symbols": {},
        "meta": {
            "module_id": module_id,
            "dispatch_mode": "native",
            "generated_kind": "type_stub_v1",
        },
    }


def _pass_stmt() -> dict[str, JsonVal]:
    return {"kind": "Pass"}


def _return_none() -> dict[str, JsonVal]:
    return {
        "kind": "Return",
        "value": {
            "kind": "Constant",
            "value": None,
            "resolved_type": "None",
            "borrow_kind": "value",
            "casts": [],
            "repr": "None",
        },
    }


def _return_bool(value: bool) -> dict[str, JsonVal]:
    return {
        "kind": "Return",
        "value": {
            "kind": "Constant",
            "value": value,
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
            "repr": "True" if value else "False",
        },
    }


def _return_str(value: str) -> dict[str, JsonVal]:
    return {
        "kind": "Return",
        "value": {
            "kind": "Constant",
            "value": value,
            "resolved_type": "str",
            "borrow_kind": "value",
            "casts": [],
            "repr": '"' + value + '"',
        },
    }


def _return_int(value: int) -> dict[str, JsonVal]:
    return {
        "kind": "Return",
        "value": {
            "kind": "Constant",
            "value": value,
            "resolved_type": "int64",
            "borrow_kind": "value",
            "casts": [],
            "repr": str(value),
        },
    }


def _return_name(name: str, resolved_type: str) -> dict[str, JsonVal]:
    return {
        "kind": "Return",
        "value": {
            "kind": "Name",
            "id": name,
            "resolved_type": resolved_type,
            "borrow_kind": "value",
            "casts": [],
            "repr": name,
        },
    }


def _return_empty_list(resolved_type: str) -> dict[str, JsonVal]:
    return {
        "kind": "Return",
        "value": {
            "kind": "List",
            "elements": [],
            "resolved_type": resolved_type,
            "borrow_kind": "value",
            "casts": [],
            "repr": "[]",
        },
    }


def _return_empty_dict(resolved_type: str) -> dict[str, JsonVal]:
    return {
        "kind": "Return",
        "value": {
            "kind": "Dict",
            "keys": [],
            "values": [],
            "resolved_type": resolved_type,
            "borrow_kind": "value",
            "casts": [],
            "repr": "{}",
        },
    }


def _function_def(
    name: str,
    *,
    arg_order: list[str] | None = None,
    arg_types: dict[str, str] | None = None,
    return_type: str = "None",
    body: list[JsonVal] | None = None,
) -> dict[str, JsonVal]:
    order = list(arg_order) if isinstance(arg_order, list) else []
    types = dict(arg_types) if isinstance(arg_types, dict) else {}
    usage: dict[str, JsonVal] = {}
    defaults: dict[str, JsonVal] = {}
    for arg in order:
        usage[arg] = "readonly"
    return {
        "kind": "FunctionDef",
        "name": name,
        "original_name": name,
        "arg_types": types,
        "arg_order": order,
        "arg_defaults": defaults,
        "arg_index": {arg: idx for idx, arg in enumerate(order)},
        "return_type": return_type,
        "arg_usage": usage,
        "renamed_symbols": {},
        "docstring": None,
        "body": list(body) if isinstance(body, list) else ([_pass_stmt()] if return_type == "None" else [_return_none()]),
    }


def _ann_assign(name: str, typ: str, value: JsonVal) -> dict[str, JsonVal]:
    return {
        "kind": "AnnAssign",
        "target": {
            "kind": "Name",
            "id": name,
            "resolved_type": typ,
            "borrow_kind": "value",
            "casts": [],
            "repr": name,
        },
        "annotation": typ,
        "value": value,
        "declare": True,
        "decl_type": typ,
    }


def _class_def(
    name: str,
    *,
    field_types: dict[str, str] | None = None,
    body: list[JsonVal] | None = None,
    dataclass: bool = False,
) -> dict[str, JsonVal]:
    return {
        "kind": "ClassDef",
        "name": name,
        "original_name": name,
        "base": "object",
        "dataclass": dataclass,
        "field_types": dict(field_types) if isinstance(field_types, dict) else {},
        "body": list(body) if isinstance(body, list) else [],
    }


def _type_alias(name: str, value: str) -> dict[str, JsonVal]:
    return {"kind": "TypeAlias", "name": name, "value": value}


def _compile_jv_stub() -> dict[str, JsonVal]:
    body: list[JsonVal] = [
        _type_alias("Node", "dict[str,Any]"),
        _class_def(
            "CompileContext",
            dataclass=True,
            field_types={
                "nominal_adt_table": "dict[str,Node]",
                "legacy_compat_bridge": "bool",
                "comp_counter": "int64",
                "enum_counter": "int64",
                "tte_counter": "int64",
                "swap_counter": "int64",
                "tuple_unpack_counter": "int64",
                "current_return_type": "str",
            },
            body=[
                _ann_assign("nominal_adt_table", "dict[str,Node]", _return_empty_dict("dict[str,Node]")["value"]),
                _ann_assign("legacy_compat_bridge", "bool", _return_bool(True)["value"]),
                _ann_assign("comp_counter", "int64", _return_int(0)["value"]),
                _ann_assign("enum_counter", "int64", _return_int(0)["value"]),
                _ann_assign("tte_counter", "int64", _return_int(0)["value"]),
                _ann_assign("swap_counter", "int64", _return_int(0)["value"]),
                _ann_assign("tuple_unpack_counter", "int64", _return_int(0)["value"]),
                _ann_assign("current_return_type", "str", _return_str("")["value"]),
                _function_def("push_storage_scope", arg_order=["self"], arg_types={"self": "CompileContext"}, return_type="None", body=[_pass_stmt()]),
                _function_def("pop_storage_scope", arg_order=["self"], arg_types={"self": "CompileContext"}, return_type="None", body=[_pass_stmt()]),
                _function_def("set_storage_type", arg_order=["self", "name", "type_name"], arg_types={"self": "CompileContext", "name": "str", "type_name": "str"}, return_type="None", body=[_pass_stmt()]),
                _function_def("lookup_storage_type", arg_order=["self", "name"], arg_types={"self": "CompileContext", "name": "str"}, return_type="str", body=[_return_str("unknown")]),
                _function_def("next_comp_name", arg_order=["self"], arg_types={"self": "CompileContext"}, return_type="str", body=[_return_str("__comp_stub")]),
                _function_def("next_enum_name", arg_order=["self"], arg_types={"self": "CompileContext"}, return_type="str", body=[_return_str("__enum_stub")]),
                _function_def("next_tte_name", arg_order=["self"], arg_types={"self": "CompileContext"}, return_type="str", body=[_return_str("__tte_stub")]),
                _function_def("next_swap_name", arg_order=["self"], arg_types={"self": "CompileContext"}, return_type="str", body=[_return_str("__swap_stub")]),
                _function_def("next_tuple_tmp_name", arg_order=["self"], arg_types={"self": "CompileContext"}, return_type="str", body=[_return_str("__tup_stub")]),
            ],
        ),
        _function_def("jv_str", arg_order=["v"], arg_types={"v": "JsonVal"}, return_type="str", body=[_return_str("")]),
        _function_def("jv_str_or", arg_order=["v", "default"], arg_types={"v": "JsonVal", "default": "str"}, return_type="str", body=[_return_name("default", "str")]),
        _function_def("jv_int", arg_order=["v"], arg_types={"v": "JsonVal"}, return_type="int64", body=[_return_int(0)]),
        _function_def("jv_bool", arg_order=["v"], arg_types={"v": "JsonVal"}, return_type="bool", body=[_return_bool(False)]),
        _function_def("jv_list", arg_order=["v"], arg_types={"v": "JsonVal"}, return_type="list[JsonVal]", body=[_return_empty_list("list[JsonVal]")]),
        _function_def("jv_dict", arg_order=["v"], arg_types={"v": "JsonVal"}, return_type="Node", body=[_return_empty_dict("dict[str,Any]")]),
        _function_def("jv_is_dict", arg_order=["v"], arg_types={"v": "JsonVal"}, return_type="bool", body=[_return_bool(False)]),
        _function_def("jv_is_list", arg_order=["v"], arg_types={"v": "JsonVal"}, return_type="bool", body=[_return_bool(False)]),
        _function_def("nd_kind", arg_order=["node"], arg_types={"node": "Node"}, return_type="str", body=[_return_str("")]),
        _function_def("nd_get_str", arg_order=["node", "key"], arg_types={"node": "Node", "key": "str"}, return_type="str", body=[_return_str("")]),
        _function_def("nd_get_str_or", arg_order=["node", "key", "default"], arg_types={"node": "Node", "key": "str", "default": "str"}, return_type="str", body=[_return_name("default", "str")]),
        _function_def("nd_get_dict", arg_order=["node", "key"], arg_types={"node": "Node", "key": "str"}, return_type="Node", body=[_return_empty_dict("dict[str,Any]")]),
        _function_def("nd_get_list", arg_order=["node", "key"], arg_types={"node": "Node", "key": "str"}, return_type="list[JsonVal]", body=[_return_empty_list("list[JsonVal]")]),
        _function_def("nd_get_int", arg_order=["node", "key"], arg_types={"node": "Node", "key": "str"}, return_type="int64", body=[_return_int(0)]),
        _function_def("nd_get_bool", arg_order=["node", "key"], arg_types={"node": "Node", "key": "str"}, return_type="bool", body=[_return_bool(False)]),
        _function_def("nd_source_span", arg_order=["node"], arg_types={"node": "Node"}, return_type="JsonVal", body=[_return_none()]),
        _function_def("nd_repr", arg_order=["node"], arg_types={"node": "Node"}, return_type="str", body=[_return_str("")]),
    ]
    return _module_doc("toolchain2.compile.jv", body)


def _common_types_stub() -> dict[str, JsonVal]:
    body: list[JsonVal] = [
        _function_def("normalize_type_name", arg_order=["value"], arg_types={"value": "Any"}, return_type="str", body=[_return_str("unknown")]),
        _function_def("is_any_like_type", arg_order=["value"], arg_types={"value": "Any"}, return_type="bool", body=[_return_bool(True)]),
        _function_def("split_generic_types", arg_order=["text"], arg_types={"text": "str"}, return_type="list[str]", body=[_return_empty_list("list[str]")]),
    ]
    return _module_doc("toolchain2.common.types", body)


def _normalize_order_stub() -> dict[str, JsonVal]:
    return _module_doc(
        "toolchain2.resolve.py.normalize_order",
        [
            _function_def(
                "normalize_field_order",
                arg_order=["doc", "parent_key"],
                arg_types={"doc": "Any", "parent_key": "str"},
                return_type="Any",
                body=[_return_name("doc", "Any")],
            ),
        ],
    )


def _parse_nodes_stub() -> dict[str, JsonVal]:
    return _module_doc(
        "toolchain2.parse.py.nodes",
        [
            _class_def(
                "Module",
                body=[
                    _function_def("to_jv", arg_order=["self"], arg_types={"self": "Module"}, return_type="dict[str,Any]", body=[_return_empty_dict("dict[str,Any]")]),
                ],
            ),
        ],
    )


def _parse_parser_stub() -> dict[str, JsonVal]:
    return _module_doc(
        "toolchain2.parse.py.parser",
        [
            _function_def(
                "parse_python_source",
                arg_order=["source", "filename"],
                arg_types={"source": "str", "filename": "str"},
                return_type="Module",
                body=[
                    {
                        "kind": "Return",
                        "value": {
                            "kind": "Call",
                            "func": {
                                "kind": "Name",
                                "id": "Module",
                                "resolved_type": "callable[[],Module]",
                                "borrow_kind": "value",
                                "casts": [],
                                "repr": "Module",
                            },
                            "args": [],
                            "keywords": [],
                            "resolved_type": "Module",
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": "Module()",
                        },
                    }
                ],
            ),
        ],
    )


def _expand_defaults_stub() -> dict[str, JsonVal]:
    return _module_doc(
        "toolchain2.link.expand_defaults",
        [
            _function_def(
                "expand_cross_module_defaults",
                arg_order=["modules"],
                arg_types={"modules": "list[Any]"},
                return_type="None",
                body=[_pass_stmt()],
            ),
        ],
    )


def _optimize_passes_stub() -> dict[str, JsonVal]:
    body: list[JsonVal] = [
        _function_def("build_local_only_passes", arg_order=[], arg_types={}, return_type="list[East3OptimizerPass]", body=[_return_empty_list("list[East3OptimizerPass]")]),
        _function_def("build_default_passes", arg_order=[], arg_types={}, return_type="list[East3OptimizerPass]", body=[_return_empty_list("list[East3OptimizerPass]")]),
    ]
    return _module_doc("toolchain2.optimize.passes", body)


def _builtin_registry_stub() -> dict[str, JsonVal]:
    body: list[JsonVal] = [
        _class_def(
            "ExternV2",
            dataclass=True,
            field_types={"module": "str", "symbol": "str", "tag": "str", "kind": "str"},
            body=[
                _ann_assign("module", "str", _return_str("")["value"]),
                _ann_assign("symbol", "str", _return_str("")["value"]),
                _ann_assign("tag", "str", _return_str("")["value"]),
                _ann_assign("kind", "str", _return_str("")["value"]),
            ],
        ),
        _class_def(
            "FuncSig",
            dataclass=True,
            field_types={
                "name": "str",
                "arg_names": "list[str]",
                "arg_types": "dict[str,str]",
                "return_type": "str",
                "decorators": "list[str]",
                "vararg_name": "str",
                "vararg_type": "str",
                "is_method": "bool",
                "owner_class": "str",
                "extern": "ExternV2 | None",
            },
            body=[
                _ann_assign("name", "str", _return_str("")["value"]),
                _ann_assign("arg_names", "list[str]", _return_empty_list("list[str]")["value"]),
                _ann_assign("arg_types", "dict[str,str]", _return_empty_dict("dict[str,str]")["value"]),
                _ann_assign("return_type", "str", _return_str("")["value"]),
                _ann_assign("decorators", "list[str]", _return_empty_list("list[str]")["value"]),
                _ann_assign("vararg_name", "str", _return_str("")["value"]),
                _ann_assign("vararg_type", "str", _return_str("")["value"]),
                _ann_assign("is_method", "bool", _return_bool(False)["value"]),
                _ann_assign("owner_class", "str", _return_str("")["value"]),
                _ann_assign("extern", "ExternV2 | None", _return_none()["value"]),
            ],
        ),
        _class_def(
            "VarSig",
            dataclass=True,
            field_types={"name": "str", "var_type": "str", "extern": "ExternV2 | None"},
            body=[
                _ann_assign("name", "str", _return_str("")["value"]),
                _ann_assign("var_type", "str", _return_str("")["value"]),
                _ann_assign("extern", "ExternV2 | None", _return_none()["value"]),
            ],
        ),
        _class_def(
            "ClassSig",
            dataclass=True,
            field_types={
                "name": "str",
                "bases": "list[str]",
                "methods": "dict[str,FuncSig]",
                "fields": "dict[str,str]",
                "template_params": "list[str]",
                "extern": "ExternV2 | None",
            },
            body=[
                _ann_assign("name", "str", _return_str("")["value"]),
                _ann_assign("bases", "list[str]", _return_empty_list("list[str]")["value"]),
                _ann_assign("methods", "dict[str,FuncSig]", _return_empty_dict("dict[str,FuncSig]")["value"]),
                _ann_assign("fields", "dict[str,str]", _return_empty_dict("dict[str,str]")["value"]),
                _ann_assign("template_params", "list[str]", _return_empty_list("list[str]")["value"]),
                _ann_assign("extern", "ExternV2 | None", _return_none()["value"]),
            ],
        ),
        _class_def(
            "ModuleSig",
            dataclass=True,
            field_types={
                "module_id": "str",
                "functions": "dict[str,FuncSig]",
                "variables": "dict[str,VarSig]",
                "classes": "dict[str,ClassSig]",
            },
            body=[
                _ann_assign("module_id", "str", _return_str("")["value"]),
                _ann_assign("functions", "dict[str,FuncSig]", _return_empty_dict("dict[str,FuncSig]")["value"]),
                _ann_assign("variables", "dict[str,VarSig]", _return_empty_dict("dict[str,VarSig]")["value"]),
                _ann_assign("classes", "dict[str,ClassSig]", _return_empty_dict("dict[str,ClassSig]")["value"]),
            ],
        ),
        _class_def(
            "BuiltinRegistry",
            dataclass=True,
            field_types={
                "functions": "dict[str,FuncSig]",
                "classes": "dict[str,ClassSig]",
                "stdlib_modules": "dict[str,ModuleSig]",
            },
            body=[
                _ann_assign("functions", "dict[str,FuncSig]", _return_empty_dict("dict[str,FuncSig]")["value"]),
                _ann_assign("classes", "dict[str,ClassSig]", _return_empty_dict("dict[str,ClassSig]")["value"]),
                _ann_assign("stdlib_modules", "dict[str,ModuleSig]", _return_empty_dict("dict[str,ModuleSig]")["value"]),
                _function_def("lookup_function", arg_order=["self", "name"], arg_types={"self": "BuiltinRegistry", "name": "str"}, return_type="FuncSig | None", body=[_return_none()]),
                _function_def("lookup_method", arg_order=["self", "owner_base", "method"], arg_types={"self": "BuiltinRegistry", "owner_base": "str", "method": "str"}, return_type="FuncSig | None", body=[_return_none()]),
                _function_def("lookup_stdlib_function", arg_order=["self", "module_id", "name"], arg_types={"self": "BuiltinRegistry", "module_id": "str", "name": "str"}, return_type="FuncSig | None", body=[_return_none()]),
                _function_def("lookup_stdlib_class", arg_order=["self", "module_id", "name"], arg_types={"self": "BuiltinRegistry", "module_id": "str", "name": "str"}, return_type="ClassSig | None", body=[_return_none()]),
                _function_def("lookup_stdlib_variable", arg_order=["self", "module_id", "name"], arg_types={"self": "BuiltinRegistry", "module_id": "str", "name": "str"}, return_type="VarSig | None", body=[_return_none()]),
                _function_def("find_stdlib_class", arg_order=["self", "name"], arg_types={"self": "BuiltinRegistry", "name": "str"}, return_type="ClassSig | None", body=[_return_none()]),
                _function_def("is_builtin", arg_order=["self", "name"], arg_types={"self": "BuiltinRegistry", "name": "str"}, return_type="bool", body=[_return_bool(False)]),
            ],
        ),
        _function_def(
            "load_builtin_registry",
            arg_order=["builtins_path", "containers_path", "stdlib_dir"],
            arg_types={"builtins_path": "Path", "containers_path": "Path", "stdlib_dir": "Path"},
            return_type="BuiltinRegistry",
            body=[
                {
                    "kind": "Return",
                    "value": {
                        "kind": "Call",
                        "func": {
                            "kind": "Name",
                            "id": "BuiltinRegistry",
                            "resolved_type": "callable[[],BuiltinRegistry]",
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": "BuiltinRegistry",
                        },
                        "args": [],
                        "keywords": [],
                        "resolved_type": "BuiltinRegistry",
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": "BuiltinRegistry()",
                    },
                }
            ],
        ),
    ]
    return _module_doc("toolchain2.resolve.py.builtin_registry", body)


_STUB_BUILDERS: dict[str, callable] = {
    "toolchain2.common.types": _common_types_stub,
    "toolchain2.compile.jv": _compile_jv_stub,
    "toolchain2.link.expand_defaults": _expand_defaults_stub,
    "toolchain2.optimize.passes": _optimize_passes_stub,
    "toolchain2.parse.py.nodes": _parse_nodes_stub,
    "toolchain2.parse.py.parser": _parse_parser_stub,
    "toolchain2.resolve.py.builtin_registry": _builtin_registry_stub,
    "toolchain2.resolve.py.normalize_order": _normalize_order_stub,
}


def available_type_stub_module_ids() -> list[str]:
    return sorted(_STUB_BUILDERS.keys())


def build_type_stub_doc(module_id: str) -> dict[str, JsonVal]:
    builder = _STUB_BUILDERS.get(module_id)
    if builder is None:
        raise RuntimeError("type stub not available: " + module_id)
    doc = builder()
    if not isinstance(doc, dict):
        raise RuntimeError("invalid type stub document: " + module_id)
    return doc


def write_type_stub_files(module_ids: list[str], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_paths: list[str] = []
    seen: set[str] = set()
    for module_id in module_ids:
        if module_id in seen:
            continue
        seen.add(module_id)
        doc = build_type_stub_doc(module_id)
        filename = module_id.replace(".", "_") + ".stub.east3.json"
        path = output_dir / filename
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        out_paths.append(str(path))
    return out_paths
