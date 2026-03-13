#!/usr/bin/env python3
"""Shared runtime-call and named-call helper semantics for self-hosted EAST parsing."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.frontend_semantics import lookup_builtin_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_owner_method_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_runtime_binding_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_function_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_method_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_symbol_semantic_tag
from toolchain.frontends.runtime_symbol_index import lookup_runtime_call_adapter_kind
from toolchain.frontends.signature_registry import lookup_noncpp_imported_symbol_runtime_call
from toolchain.frontends.signature_registry import lookup_noncpp_module_attr_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_function_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_function_runtime_binding
from toolchain.frontends.signature_registry import lookup_stdlib_function_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_runtime_binding
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_binding
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_call


def _set_runtime_binding_fields(payload: dict[str, Any], module_id: str, runtime_symbol: str) -> None:
    if module_id.strip() == "" or runtime_symbol.strip() == "":
        return
    payload["runtime_module_id"] = module_id
    payload["runtime_symbol"] = runtime_symbol
    adapter_kind = lookup_runtime_call_adapter_kind(module_id, runtime_symbol)
    if adapter_kind != "":
        payload["runtime_call_adapter_kind"] = adapter_kind


def _sh_annotate_runtime_call_expr(
    payload: dict[str, Any],
    *,
    lowered_kind: str,
    builtin_name: str,
    runtime_call: str = "",
    module_id: str = "",
    runtime_symbol: str = "",
    semantic_tag: str | None = None,
    runtime_owner: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload["lowered_kind"] = lowered_kind
    payload["builtin_name"] = builtin_name
    if runtime_call != "":
        payload["runtime_call"] = runtime_call
    _set_runtime_binding_fields(payload, module_id, runtime_symbol)
    if semantic_tag is not None and semantic_tag != "":
        payload["semantic_tag"] = semantic_tag
    if runtime_owner is not None:
        payload["runtime_owner"] = runtime_owner
    return payload


def _sh_annotate_resolved_runtime_expr(
    payload: dict[str, Any],
    *,
    runtime_call: str,
    runtime_source: str,
    module_id: str = "",
    runtime_symbol: str = "",
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    payload["resolved_runtime_call"] = runtime_call
    payload["resolved_runtime_source"] = runtime_source
    _set_runtime_binding_fields(payload, module_id, runtime_symbol)
    if semantic_tag is not None and semantic_tag != "":
        payload["semantic_tag"] = semantic_tag
    return payload


def _sh_annotate_runtime_attr_expr(
    payload: dict[str, Any],
    *,
    runtime_call: str,
    module_id: str = "",
    runtime_symbol: str = "",
    semantic_tag: str | None = None,
    runtime_owner: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload["lowered_kind"] = "BuiltinAttr"
    payload["runtime_call"] = runtime_call
    _set_runtime_binding_fields(payload, module_id, runtime_symbol)
    if semantic_tag is not None and semantic_tag != "":
        payload["semantic_tag"] = semantic_tag
    if runtime_owner is not None:
        payload["runtime_owner"] = runtime_owner
    return payload


def _sh_annotate_runtime_method_call_expr(
    payload: dict[str, Any],
    *,
    owner_type: str,
    attr: str,
    runtime_owner: dict[str, Any] | None = None,
) -> dict[str, Any]:
    owner_method_semantic_tag = lookup_owner_method_semantic_tag(owner_type, attr)
    if owner_method_semantic_tag != "":
        payload["semantic_tag"] = owner_method_semantic_tag
    runtime_call = lookup_stdlib_method_runtime_call(owner_type, attr)
    if runtime_call == "":
        return payload
    mod_id, runtime_symbol = lookup_stdlib_method_runtime_binding(owner_type, attr)
    method_semantic_tag = lookup_stdlib_method_semantic_tag(attr)
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=attr,
        runtime_call=runtime_call,
        module_id=mod_id,
        runtime_symbol=runtime_symbol,
        semantic_tag=(
            owner_method_semantic_tag if owner_method_semantic_tag != "" else method_semantic_tag
        ),
        runtime_owner=runtime_owner,
    )


def _sh_annotate_enumerate_call_expr(
    payload: dict[str, Any],
    *,
    iter_element_type: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name="enumerate",
        runtime_call="py_enumerate",
        module_id="pytra.built_in.iter_ops",
        runtime_symbol="enumerate",
        semantic_tag=semantic_tag,
    )
    payload["iterable_trait"] = "yes" if iter_element_type != "unknown" else "unknown"
    payload["iter_protocol"] = "static_range"
    payload["iter_element_type"] = iter_element_type
    payload["resolved_type"] = f"list[tuple[int64, {iter_element_type}]]"
    return payload


def _sh_annotate_stdlib_function_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    runtime_call: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    mod_id, runtime_symbol = lookup_stdlib_function_runtime_binding(fn_name)
    _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call=runtime_call,
        module_id=mod_id,
        runtime_symbol=runtime_symbol,
        semantic_tag=semantic_tag,
    )
    sig_ret = lookup_stdlib_function_return_type(fn_name)
    if sig_ret != "":
        payload["resolved_type"] = sig_ret
    return payload


def _sh_annotate_stdlib_symbol_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    runtime_call: str,
    import_symbols: dict[str, dict[str, str]],
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    mod_id, runtime_symbol = lookup_stdlib_imported_symbol_runtime_binding(fn_name, import_symbols)
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call=runtime_call,
        module_id=mod_id,
        runtime_symbol=runtime_symbol,
        semantic_tag=semantic_tag,
    )


def _sh_annotate_noncpp_symbol_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    runtime_call: str,
    import_symbols: dict[str, dict[str, str]],
) -> dict[str, Any]:
    mod_id = ""
    runtime_symbol = ""
    binding_semantic_tag = ""
    binding = import_symbols.get(fn_name)
    if isinstance(binding, dict):
        mod_id = str(binding.get("module", "")).strip()
        runtime_symbol = str(binding.get("name", "")).strip()
        binding_semantic_tag = lookup_runtime_binding_semantic_tag(mod_id, runtime_symbol)
    return _sh_annotate_resolved_runtime_expr(
        payload,
        runtime_call=runtime_call,
        runtime_source="import_symbol",
        module_id=mod_id,
        runtime_symbol=runtime_symbol,
        semantic_tag=binding_semantic_tag,
    )


def _sh_lookup_noncpp_attr_runtime_call(
    owner_expr: dict[str, Any] | None,
    attr_name: str,
    *,
    import_modules: dict[str, str],
    import_symbols: dict[str, dict[str, str]],
) -> tuple[str, str]:
    if not isinstance(owner_expr, dict) or owner_expr.get("kind") != "Name":
        return "", ""
    owner_name = str(owner_expr.get("id", "")).strip()
    if owner_name == "":
        return "", ""
    if owner_name in import_modules:
        runtime_owner = import_modules[owner_name]
        runtime_call = lookup_noncpp_module_attr_runtime_call(runtime_owner, attr_name)
        if runtime_call != "":
            return runtime_owner, runtime_call
    if owner_name in import_symbols:
        binding = import_symbols[owner_name]
        mod_name = str(binding.get("module", "")).strip()
        sym_name = str(binding.get("name", "")).strip()
        if mod_name != "" and sym_name != "":
            runtime_owner = mod_name + "." + sym_name
            runtime_call = lookup_noncpp_module_attr_runtime_call(runtime_owner, attr_name)
            if runtime_call != "":
                return runtime_owner, runtime_call
    return "", ""


def _sh_annotate_noncpp_attr_call_expr(
    payload: dict[str, Any],
    *,
    owner_expr: dict[str, Any] | None,
    attr_name: str,
    import_modules: dict[str, str],
    import_symbols: dict[str, dict[str, str]],
) -> dict[str, Any]:
    runtime_owner, runtime_call = _sh_lookup_noncpp_attr_runtime_call(
        owner_expr,
        attr_name,
        import_modules=import_modules,
        import_symbols=import_symbols,
    )
    if runtime_call == "":
        return payload
    binding_semantic_tag = lookup_runtime_binding_semantic_tag(runtime_owner, attr_name)
    _sh_annotate_resolved_runtime_expr(
        payload,
        runtime_call=runtime_call,
        runtime_source="module_attr",
        module_id=runtime_owner,
        runtime_symbol=attr_name,
        semantic_tag=binding_semantic_tag,
    )
    std_module_attr_ret = lookup_stdlib_function_return_type(attr_name)
    if std_module_attr_ret != "":
        payload["resolved_type"] = std_module_attr_ret
    return payload


def _sh_annotate_scalar_ctor_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    arg_count: int,
    use_truthy_runtime: bool = False,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    runtime_call = "static_cast"
    runtime_module_id = "pytra.core.py_runtime"
    runtime_symbol = fn_name
    if fn_name == "int" and arg_count == 2:
        runtime_call = "py_to_int64_base"
        runtime_module_id = "pytra.built_in.scalar_ops"
        runtime_symbol = "py_to_int64_base"
    elif fn_name == "bool" and arg_count == 1 and use_truthy_runtime:
        runtime_call = "py_to_bool"
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call=runtime_call,
        module_id=runtime_module_id,
        runtime_symbol=runtime_symbol,
        semantic_tag=semantic_tag,
    )


def _sh_annotate_minmax_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call="py_min" if fn_name == "min" else "py_max",
        module_id="pytra.core.py_runtime",
        runtime_symbol=fn_name,
        semantic_tag=semantic_tag,
    )


def _sh_annotate_collection_ctor_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    runtime_call = fn_name + "_ctor"
    if fn_name == "bytes":
        runtime_call = "bytes_ctor"
    elif fn_name == "bytearray":
        runtime_call = "bytearray_ctor"
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call=runtime_call,
        module_id="pytra.core.py_runtime",
        runtime_symbol=fn_name,
        semantic_tag=semantic_tag,
    )


def _sh_annotate_anyall_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call="py_any" if fn_name == "any" else "py_all",
        module_id="pytra.built_in.predicates",
        runtime_symbol=fn_name,
        semantic_tag=semantic_tag,
    )


def _sh_annotate_ordchr_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call="py_ord" if fn_name == "ord" else "py_chr",
        module_id="pytra.built_in.scalar_ops",
        runtime_symbol="py_ord" if fn_name == "ord" else "py_chr",
        semantic_tag=semantic_tag,
    )


def _sh_annotate_iterator_builtin_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    runtime_call = "py_iter_or_raise"
    module_id = "pytra.core.py_runtime"
    if fn_name == "next":
        runtime_call = "py_next_or_stop"
    elif fn_name == "reversed":
        runtime_call = "py_reversed"
        module_id = "pytra.built_in.iter_ops"
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call=runtime_call,
        module_id=module_id,
        runtime_symbol=fn_name,
        semantic_tag=semantic_tag,
    )


def _sh_annotate_open_call_expr(
    payload: dict[str, Any],
    *,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name="open",
        runtime_call="open",
        module_id="pytra.core.py_runtime",
        runtime_symbol="open",
        semantic_tag=semantic_tag,
    )


def _sh_annotate_exception_ctor_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call="std::runtime_error",
        module_id="pytra.core.py_runtime",
        runtime_symbol=fn_name,
        semantic_tag=semantic_tag,
    )


def _sh_annotate_type_predicate_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="TypePredicateCall",
        builtin_name=fn_name,
        semantic_tag=semantic_tag,
    )


def _sh_annotate_fixed_runtime_builtin_call_expr(
    payload: dict[str, Any],
    *,
    fn_name: str,
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    runtime_call = "py_to_string"
    module_id = "pytra.core.py_runtime"
    runtime_symbol = fn_name
    if fn_name == "print":
        runtime_call = "py_print"
        module_id = "pytra.built_in.io_ops"
        runtime_symbol = "py_print"
    elif fn_name == "len":
        runtime_call = "py_len"
    elif fn_name == "range":
        runtime_call = "py_range"
    elif fn_name == "zip":
        runtime_call = "zip"
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=fn_name,
        runtime_call=runtime_call,
        module_id=module_id,
        runtime_symbol=runtime_symbol,
        semantic_tag=semantic_tag,
    )


def _sh_lookup_named_call_dispatch(
    fn_name: str,
    *,
    import_symbols: dict[str, dict[str, str]],
) -> dict[str, str]:
    if fn_name.strip() == "":
        return {
            "builtin_semantic_tag": "",
            "stdlib_fn_runtime_call": "",
            "stdlib_fn_semantic_tag": "",
            "stdlib_symbol_runtime_call": "",
            "stdlib_symbol_semantic_tag": "",
            "noncpp_symbol_runtime_call": "",
        }
    return {
        "builtin_semantic_tag": lookup_builtin_semantic_tag(fn_name),
        "stdlib_fn_runtime_call": lookup_stdlib_function_runtime_call(fn_name),
        "stdlib_fn_semantic_tag": lookup_stdlib_function_semantic_tag(fn_name),
        "stdlib_symbol_runtime_call": lookup_stdlib_imported_symbol_runtime_call(fn_name, import_symbols),
        "stdlib_symbol_semantic_tag": lookup_stdlib_symbol_semantic_tag(fn_name),
        "noncpp_symbol_runtime_call": lookup_noncpp_imported_symbol_runtime_call(fn_name, import_symbols),
    }


def _sh_infer_known_name_call_return_type(
    fn_name: str,
    args: list[dict[str, Any]],
    stdlib_imported_ret: str,
    *,
    infer_item_type: Any,
) -> str:
    if fn_name == "print":
        return "None"
    if stdlib_imported_ret != "":
        return stdlib_imported_ret
    if fn_name == "open":
        return "PyFile"
    if fn_name == "int":
        return "int64"
    if fn_name == "float":
        return "float64"
    if fn_name == "bool":
        return "bool"
    if fn_name == "str":
        return "str"
    if fn_name == "len":
        return "int64"
    if fn_name == "range":
        return "range"
    if fn_name == "zip":
        zip_item_types: list[str] = []
        for arg_node in args:
            if isinstance(arg_node, dict):
                zip_item_types.append(infer_item_type(arg_node))
        return f"list[tuple[{','.join(zip_item_types)}]]"
    if fn_name == "list":
        return "list[unknown]"
    if fn_name == "set":
        return "set[unknown]"
    if fn_name == "dict":
        return "dict[unknown,unknown]"
    if fn_name == "bytes":
        return "bytes"
    if fn_name == "bytearray":
        return "bytearray"
    if fn_name in {"Exception", "RuntimeError", "NotImplementedError"}:
        return "Exception"
    return ""


def _sh_infer_enumerate_item_type(
    args: list[dict[str, Any]],
    *,
    infer_item_type: Any,
) -> str:
    if len(args) < 1:
        return "unknown"
    arg0 = args[0]
    if not isinstance(arg0, dict):
        return "unknown"
    return infer_item_type(arg0)
