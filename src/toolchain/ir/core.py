#!/usr/bin/env python3
"""EAST parser core (self-hosted)."""

from __future__ import annotations

from pytra.std import argparse
from pytra.std import json
from pytra.std import re
from dataclasses import dataclass
from typing import Any
from pytra.std.pathlib import Path
from pytra.std import sys
from toolchain.frontends.signature_registry import is_stdlib_path_type
from toolchain.frontends.signature_registry import lookup_stdlib_attribute_type
from toolchain.frontends.signature_registry import lookup_stdlib_function_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_function_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_function_runtime_binding
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_return_type
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_imported_symbol_runtime_binding
from toolchain.frontends.signature_registry import lookup_noncpp_imported_symbol_runtime_call
from toolchain.frontends.signature_registry import lookup_noncpp_module_attr_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_binding
from toolchain.frontends.signature_registry import lookup_stdlib_method_runtime_call
from toolchain.frontends.signature_registry import lookup_stdlib_method_return_type
from toolchain.frontends.frontend_semantics import lookup_builtin_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_owner_method_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_runtime_binding_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_function_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_method_semantic_tag
from toolchain.frontends.frontend_semantics import lookup_stdlib_symbol_semantic_tag
from toolchain.frontends.runtime_abi import validate_runtime_abi_module
from toolchain.frontends.runtime_template import validate_template_module
from toolchain.frontends.runtime_symbol_index import lookup_runtime_call_adapter_kind
from toolchain.frontends.runtime_symbol_index import resolve_import_binding_doc
from toolchain.frontends.type_expr import parse_type_expr_text
from toolchain.frontends.type_expr import sync_type_expr_mirrors
from toolchain.frontends.type_expr import type_expr_to_string


# `BorrowKind` は実体のない型エイリアス用途のみなので、
# selfhost 生成コードでは値として生成しない。
INT_TYPES = {
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
}
FLOAT_TYPES = {"float32", "float64"}
_SH_STR_PREFIX_CHARS = {"r", "R", "b", "B", "u", "U", "f", "F"}

# `_sh_parse_expr_lowered` が参照する self-hosted 解析コンテキスト。
_SH_FN_RETURNS: dict[str, str] = {}
_SH_CLASS_METHOD_RETURNS: dict[str, dict[str, str]] = {}
_SH_CLASS_BASE: dict[str, str | None] = {}
_SH_IMPORT_SYMBOLS: dict[str, dict[str, str]] = {}
_SH_IMPORT_MODULES: dict[str, str] = {}
_SH_TYPE_ALIASES: dict[str, str] = {
    "List": "list",
    "Dict": "dict",
    "Tuple": "tuple",
    "Set": "set",
}
_SH_EMPTY_SPAN: dict[str, Any] = {}
_SH_RUNTIME_ABI_ARG_MODES = {"default", "value", "value_mut"}
_SH_RUNTIME_ABI_RET_MODES = {"default", "value"}
_SH_RUNTIME_ABI_MODE_ALIASES = {"value_readonly": "value"}
_SH_TEMPLATE_SCOPE = "runtime_helper"
_SH_TEMPLATE_INSTANTIATION_MODE = "linked_implicit"


def _sh_default_type_aliases() -> dict[str, str]:
    """型解決用の初期別名テーブルを作成する。"""
    return {
        "List": "list",
        "Dict": "dict",
        "Tuple": "tuple",
        "Set": "set",
        "Optional": "Optional",
        "Any": "Any",
        "None": "None",
        "str": "str",
        "int": "int64",
        "float": "float64",
        "bool": "bool",
    }


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
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    mod_id, runtime_symbol = lookup_stdlib_imported_symbol_runtime_binding(fn_name, _SH_IMPORT_SYMBOLS)
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
) -> dict[str, Any]:
    mod_id = ""
    runtime_symbol = ""
    binding_semantic_tag = ""
    binding = _SH_IMPORT_SYMBOLS.get(fn_name)
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
) -> tuple[str, str]:
    if not isinstance(owner_expr, dict) or owner_expr.get("kind") != "Name":
        return "", ""
    owner_name = str(owner_expr.get("id", "")).strip()
    if owner_name == "":
        return "", ""
    if owner_name in _SH_IMPORT_MODULES:
        runtime_owner = _SH_IMPORT_MODULES[owner_name]
        runtime_call = lookup_noncpp_module_attr_runtime_call(runtime_owner, attr_name)
        if runtime_call != "":
            return runtime_owner, runtime_call
    if owner_name in _SH_IMPORT_SYMBOLS:
        binding = _SH_IMPORT_SYMBOLS[owner_name]
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
) -> dict[str, Any]:
    runtime_owner, runtime_call = _sh_lookup_noncpp_attr_runtime_call(owner_expr, attr_name)
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


def _sh_lookup_named_call_dispatch(fn_name: str) -> dict[str, str]:
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
        "stdlib_symbol_runtime_call": lookup_stdlib_imported_symbol_runtime_call(fn_name, _SH_IMPORT_SYMBOLS),
        "stdlib_symbol_semantic_tag": lookup_stdlib_symbol_semantic_tag(fn_name),
        "noncpp_symbol_runtime_call": lookup_noncpp_imported_symbol_runtime_call(fn_name, _SH_IMPORT_SYMBOLS),
    }


def _sh_infer_known_name_call_return_type(
    fn_name: str,
    args: list[dict[str, Any]],
    stdlib_imported_ret: str,
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
                zip_item_types.append(_sh_infer_item_type(arg_node))
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
    if fn_name in {"Exception", "RuntimeError"}:
        return "Exception"
    return ""


def _sh_infer_enumerate_item_type(args: list[dict[str, Any]]) -> str:
    if len(args) < 1:
        return "unknown"
    arg0 = args[0]
    if not isinstance(arg0, dict):
        return "unknown"
    return _sh_infer_item_type(arg0)


def _sh_set_parse_context(
    fn_returns: dict[str, str],
    class_method_returns: dict[str, dict[str, str]],
    class_base: dict[str, str | None],
    type_aliases: dict[str, str] | None = None,
) -> None:
    """式解析で使う関数戻り値/クラス情報のコンテキストを更新する。"""
    _SH_FN_RETURNS.clear()
    _SH_FN_RETURNS.update(fn_returns)
    _SH_CLASS_METHOD_RETURNS.clear()
    _SH_CLASS_METHOD_RETURNS.update(class_method_returns)
    _SH_CLASS_BASE.clear()
    _SH_CLASS_BASE.update(class_base)
    _SH_TYPE_ALIASES.clear()
    if type_aliases is None:
        _SH_TYPE_ALIASES.update(_sh_default_type_aliases())
    else:
        _SH_TYPE_ALIASES.update(type_aliases)


def _sh_is_type_expr_text(txt: str) -> bool:
    """型注釈として妥当そうな文字列かを軽量判定する。"""
    raw: str = txt.strip()
    if raw == "":
        return False
    for ch in raw:
        if ch.isspace():
            continue
        if ch.isalnum() or ch in {"[", "]", ",", "|", ":", ".", "_"}:
            continue
        return False
    return True


def _sh_typing_alias_to_type_name(sym: str) -> str:
    """`from typing` で import される代表的シンボルを EAST 型名へ正規化する。"""
    key = sym.strip()
    if key.startswith("typing."):
        key = key[len("typing.") :].strip()
    mapping = {
        "List": "list",
        "Dict": "dict",
        "Tuple": "tuple",
        "Set": "set",
        "Optional": "Optional",
        "Any": "Any",
        "None": "None",
        "bool": "bool",
        "float": "float64",
        "int": "int64",
        "str": "str",
        "bytes": "bytes",
        "bytearray": "bytearray",
    }
    return mapping.get(key, "")


def _sh_register_type_alias(type_aliases: dict[str, str], alias_name: str, rhs_txt: str) -> None:
    """型っぽい代入式からトップレベルの型エイリアス定義を登録する。"""
    name = alias_name.strip()
    rhs = rhs_txt.strip()
    if not _sh_is_identifier(name):
        return
    if rhs == "":
        return
    if not _sh_is_type_expr_text(rhs):
        return
    normalized = _sh_typing_alias_to_type_name(rhs)
    ann_type = _sh_ann_to_type(rhs, type_aliases=type_aliases)
    if normalized != "":
        type_aliases[name] = normalized
    elif ann_type == "Any":
        type_aliases[name] = ann_type
    elif ann_type != "unknown" and ann_type != rhs:
        type_aliases[name] = ann_type


class EastBuildError(Exception):
    kind: str
    message: str
    source_span: dict[str, Any]
    hint: str

    def __init__(
        self,
        kind: str,
        message: str,
        source_span: dict[str, Any],
        hint: str,
    ) -> None:
        self.kind = kind
        self.message = message
        self.source_span = dict(source_span)
        self.hint = hint

    def to_payload(self) -> dict[str, Any]:
        """例外情報を EAST エラー応答用 dict に整形する。"""
        out: dict[str, Any] = {}
        out["kind"] = self.kind
        out["message"] = self.message
        out["source_span"] = self.source_span
        out["hint"] = self.hint
        return out


def _make_east_build_error(kind: str, message: str, source_span: dict[str, Any], hint: str) -> RuntimeError:
    """self-hosted 生成で投げる例外を std::exception 互換（RuntimeError）に統一する。"""
    src_line = int(source_span.get("lineno", 0))
    src_col = int(source_span.get("col", 0))
    return RuntimeError(f"{kind}: {message} at {src_line}:{src_col} hint={hint}")


def convert_source_to_east(source: str, filename: str) -> dict[str, Any]:
    """後方互換用の入口。self-hosted パーサで EAST を生成する。"""
    return convert_source_to_east_self_hosted(source, filename)

def _sh_span(line: int, col: int, end_col: int, *, end_lineno: int | None = None) -> dict[str, int]:
    """self-hosted parser 用の source_span を生成する。"""
    return {"lineno": line, "col": col, "end_lineno": line if end_lineno is None else end_lineno, "end_col": end_col}


def _sh_make_kind_carrier(kind: str) -> dict[str, Any]:
    """`kind` だけを持つ薄い carrier を生成する。"""
    return {"kind": kind}


def _sh_make_node(kind: str, **fields: Any) -> dict[str, Any]:
    """`kind` 付き node の共通 envelope を構築する。"""
    node = _sh_make_kind_carrier(kind)
    node.update(fields)
    return node


def _sh_make_stmt_node(kind: str, source_span: dict[str, Any]) -> dict[str, Any]:
    """statement node の共通 envelope を構築する。"""
    return _sh_make_node(kind, source_span=source_span)


def _sh_make_trivia_blank(count: int) -> dict[str, Any]:
    """blank trivia item を生成する。"""
    return _sh_make_node("blank", count=count)


def _sh_make_trivia_comment(text: str) -> dict[str, Any]:
    """comment trivia item を生成する。"""
    return _sh_make_node("comment", text=text)


def _sh_make_expr_token(kind: str, value: str, start: int, end: int) -> dict[str, Any]:
    """self-hosted 式 parser 用の token carrier を構築する。"""
    return {
        "k": kind,
        "v": value,
        "s": start,
        "e": end,
    }


def _sh_make_expr_stmt(value: dict[str, Any], source_span: dict[str, Any]) -> dict[str, Any]:
    """`Expr` 文 node を構築する。"""
    node = _sh_make_stmt_node("Expr", source_span)
    node["value"] = value
    return node


def _sh_make_value_expr(
    kind: str,
    source_span: dict[str, Any] | None,
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
    casts: list[dict[str, Any]] | None = None,
    borrow_kind: str = "value",
) -> dict[str, Any]:
    """値を返す式 node の共通 envelope を構築する。"""
    return _sh_make_node(
        kind,
        source_span=source_span,
        resolved_type=resolved_type,
        borrow_kind=borrow_kind,
        casts=[] if casts is None else casts,
        repr=repr_text,
    )


def _sh_make_name_expr(
    source_span: dict[str, Any],
    name: str,
    resolved_type: str = "unknown",
    *,
    borrow_kind: str = "value",
    type_expr: dict[str, Any] | None = None,
    repr_text: str = "",
) -> dict[str, Any]:
    """`Name` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Name",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text if repr_text != "" else name,
        borrow_kind=borrow_kind,
    )
    node["id"] = name
    if type_expr is not None:
        node["type_expr"] = type_expr
    return node


def _sh_make_tuple_expr(
    source_span: dict[str, Any],
    elements: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Tuple` 式 node を構築する。"""
    tuple_type = resolved_type
    if tuple_type == "":
        elem_types = [str(elem.get("resolved_type", "unknown")) for elem in elements]
        tuple_type = f"tuple[{', '.join(elem_types)}]" if len(elem_types) > 0 else "tuple[]"
    tuple_repr = repr_text
    if tuple_repr == "":
        tuple_repr = ", ".join(str(elem.get("repr", "")) for elem in elements)
    node = _sh_make_value_expr(
        "Tuple",
        source_span,
        resolved_type=tuple_type,
        repr_text=tuple_repr,
    )
    node["elements"] = elements
    return node


def _sh_make_constant_expr(
    source_span: dict[str, Any],
    value: Any,
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Constant` 式 node を構築する。"""
    constant_type = resolved_type
    if constant_type == "":
        if value is None:
            constant_type = "None"
        elif isinstance(value, bool):
            constant_type = "bool"
        elif isinstance(value, int):
            constant_type = "int64"
        elif isinstance(value, float):
            constant_type = "float64"
        else:
            constant_type = "str"
    node = _sh_make_value_expr(
        "Constant",
        source_span,
        resolved_type=constant_type,
        repr_text=repr_text if repr_text != "" else str(value),
    )
    node["value"] = value
    return node


def _sh_make_unaryop_expr(
    source_span: dict[str, Any],
    op: str,
    operand: dict[str, Any],
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
) -> dict[str, Any]:
    """`UnaryOp` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "UnaryOp",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["op"] = op
    node["operand"] = operand
    return node


def _sh_make_boolop_expr(
    source_span: dict[str, Any],
    op: str,
    values: list[dict[str, Any]],
    *,
    resolved_type: str = "bool",
    repr_text: str = "",
) -> dict[str, Any]:
    """`BoolOp` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "BoolOp",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["op"] = op
    node["values"] = values
    return node


def _sh_make_compare_expr(
    source_span: dict[str, Any],
    left: dict[str, Any],
    ops: list[str],
    comparators: list[dict[str, Any]],
    *,
    resolved_type: str = "bool",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Compare` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Compare",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["left"] = left
    node["ops"] = ops
    node["comparators"] = comparators
    return node


def _sh_make_binop_expr(
    source_span: dict[str, Any],
    left: dict[str, Any],
    op: str,
    right: dict[str, Any],
    *,
    resolved_type: str = "unknown",
    casts: list[dict[str, Any]] | None = None,
    repr_text: str = "",
) -> dict[str, Any]:
    """`BinOp` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "BinOp",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
        casts=casts,
    )
    node["left"] = left
    node["op"] = op
    node["right"] = right
    return node


def _sh_make_cast_entry(on: str, from_type: str, to_type: str, reason: str) -> dict[str, Any]:
    """`casts` metadata item を構築する。"""
    return {
        "on": on,
        "from": from_type,
        "to": to_type,
        "reason": reason,
    }


def _sh_make_ifexp_expr(
    source_span: dict[str, Any],
    test: dict[str, Any],
    body: dict[str, Any],
    orelse: dict[str, Any],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`IfExp` 式 node を構築する。"""
    out_type = resolved_type
    if out_type == "":
        body_type = str(body.get("resolved_type", "unknown"))
        orelse_type = str(orelse.get("resolved_type", "unknown"))
        out_type = body_type if body_type == orelse_type else "unknown"
    node = _sh_make_value_expr(
        "IfExp",
        source_span,
        resolved_type=out_type,
        repr_text=repr_text,
    )
    node["test"] = test
    node["body"] = body
    node["orelse"] = orelse
    return node


def _sh_make_attribute_expr(
    source_span: dict[str, Any],
    value: dict[str, Any],
    attr: str,
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Attribute` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Attribute",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["value"] = value
    node["attr"] = attr
    return node


def _sh_make_call_expr(
    source_span: dict[str, Any],
    func: dict[str, Any],
    args: list[dict[str, Any]],
    keywords: list[dict[str, Any]],
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Call` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Call",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["func"] = func
    node["args"] = args
    node["keywords"] = keywords
    return node


def _sh_make_keyword_arg(arg: str, value: dict[str, Any]) -> dict[str, Any]:
    """Call.keyword carrier を構築する。"""
    return {
        "arg": arg,
        "value": value,
    }


def _sh_make_slice_node(
    lower: dict[str, Any] | None,
    upper: dict[str, Any] | None,
    step: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Slice` node を構築する。"""
    return _sh_make_node("Slice", lower=lower, upper=upper, step=step)


def _sh_make_subscript_expr(
    source_span: dict[str, Any],
    value: dict[str, Any],
    slice_node: dict[str, Any],
    *,
    resolved_type: str = "unknown",
    repr_text: str = "",
    lowered_kind: str = "",
    lower: dict[str, Any] | None = None,
    upper: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Subscript` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "Subscript",
        source_span,
        resolved_type=resolved_type,
        repr_text=repr_text,
    )
    node["value"] = value
    node["slice"] = slice_node
    if lowered_kind != "":
        node["lowered_kind"] = lowered_kind
    if lower is not None or lowered_kind == "SliceExpr":
        node["lower"] = lower
    if upper is not None or lowered_kind == "SliceExpr":
        node["upper"] = upper
    return node


def _sh_make_comp_generator(
    target: dict[str, Any],
    iter_expr: dict[str, Any],
    ifs: list[dict[str, Any]],
    *,
    is_async: bool = False,
) -> dict[str, Any]:
    """comprehension generator item を構築する。"""
    return {
        "target": target,
        "iter": iter_expr,
        "ifs": ifs,
        "is_async": is_async,
    }


def _sh_make_list_expr(
    source_span: dict[str, Any],
    elements: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`List` 式 node を構築する。"""
    list_type = resolved_type
    if list_type == "":
        elem_type = "unknown"
        if len(elements) > 0:
            elem_type = str(elements[0].get("resolved_type", "unknown"))
            for elem in elements[1:]:
                if str(elem.get("resolved_type", "unknown")) != elem_type:
                    elem_type = "unknown"
                    break
        list_type = f"list[{elem_type}]"
    node = _sh_make_value_expr(
        "List",
        source_span,
        resolved_type=list_type,
        repr_text=repr_text,
    )
    node["elements"] = elements
    return node


def _sh_make_set_expr(
    source_span: dict[str, Any],
    elements: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Set` 式 node を構築する。"""
    set_type = resolved_type
    if set_type == "":
        elem_type = str(elements[0].get("resolved_type", "unknown")) if len(elements) > 0 else "unknown"
        set_type = f"set[{elem_type}]"
    node = _sh_make_value_expr(
        "Set",
        source_span,
        resolved_type=set_type,
        repr_text=repr_text,
    )
    node["elements"] = elements
    return node


def _sh_make_dict_entry(key: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
    """`Dict` entry carrier を構築する。"""
    return {"key": key, "value": value}


def _sh_make_dict_expr(
    source_span: dict[str, Any],
    *,
    keys: list[dict[str, Any]] | None = None,
    values: list[dict[str, Any]] | None = None,
    entries: list[dict[str, Any]] | None = None,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Dict` 式 node を構築する。"""
    dict_type = resolved_type
    if entries is not None:
        entry_nodes = entries
        if dict_type == "":
            key_type = "unknown"
            value_type = "unknown"
            if len(entry_nodes) > 0:
                first_key = entry_nodes[0].get("key", {})
                first_value = entry_nodes[0].get("value", {})
                key_type = str(first_key.get("resolved_type", "unknown"))
                value_type = str(first_value.get("resolved_type", "unknown"))
            dict_type = f"dict[{key_type},{value_type}]"
        node = _sh_make_value_expr(
            "Dict",
            source_span,
            resolved_type=dict_type,
            repr_text=repr_text,
        )
        node["entries"] = entry_nodes
        return node

    key_nodes = keys if keys is not None else []
    value_nodes = values if values is not None else []
    if dict_type == "":
        key_type = "unknown"
        value_type = "unknown"
        if len(key_nodes) > 0 and len(value_nodes) > 0:
            key_type = str(key_nodes[0].get("resolved_type", "unknown"))
            value_type = str(value_nodes[0].get("resolved_type", "unknown"))
        dict_type = f"dict[{key_type},{value_type}]"
    node = _sh_make_value_expr(
        "Dict",
        source_span,
        resolved_type=dict_type,
        repr_text=repr_text,
    )
    node["keys"] = key_nodes
    node["values"] = value_nodes
    return node


def _sh_make_list_comp_expr(
    source_span: dict[str, Any],
    elt: dict[str, Any],
    generators: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
    lowered_kind: str | None = None,
) -> dict[str, Any]:
    """`ListComp` 式 node を構築する。"""
    list_type = resolved_type if resolved_type != "" else f"list[{str(elt.get('resolved_type', 'unknown'))}]"
    node = _sh_make_value_expr(
        "ListComp",
        source_span,
        resolved_type=list_type,
        repr_text=repr_text,
    )
    node["elt"] = elt
    node["generators"] = generators
    if lowered_kind is not None:
        node["lowered_kind"] = lowered_kind
    return node


def _sh_make_simple_name_list_comp_expr(
    source_span: dict[str, Any],
    *,
    line_no: int,
    base_col: int,
    elt_name: str,
    target_name: str,
    iter_expr: dict[str, Any],
    elem_type: str,
    repr_text: str = "",
) -> dict[str, Any]:
    """単純な `[x for x in items]` を helper 1 個で構築する。"""
    elt_node = _sh_make_name_expr(
        _sh_span(line_no, base_col, base_col + len(elt_name)),
        elt_name,
        resolved_type=elem_type if elt_name == target_name else "unknown",
    )
    return _sh_make_list_comp_expr(
        source_span,
        elt_node,
        [_sh_make_simple_name_comp_generator(line_no, base_col, target_name, iter_expr)],
        resolved_type=f"list[{elem_type}]",
        repr_text=repr_text,
        lowered_kind="ListCompSimple",
    )


def _sh_make_simple_name_comp_generator(
    line_no: int,
    base_col: int,
    target_name: str,
    iter_expr: dict[str, Any],
) -> dict[str, Any]:
    """simple list-comp 用の target `Name` + generator を構築する。"""
    return _sh_make_comp_generator(
        _sh_make_name_expr(
            _sh_span(line_no, base_col, base_col + len(target_name)),
            target_name,
            resolved_type="unknown",
        ),
        iter_expr,
        [],
    )


def _sh_make_builtin_listcomp_call_expr(
    source_span: dict[str, Any],
    *,
    line_no: int,
    base_col: int,
    func_name: str,
    arg: dict[str, Any],
    repr_text: str = "",
    runtime_call: str = "",
    semantic_tag: str | None = None,
) -> dict[str, Any]:
    """`any/all(<list-comp>)` の lowered builtin call を構築する。"""
    payload = _sh_make_call_expr(
        source_span,
        _sh_make_name_expr(
            _sh_span(line_no, base_col, base_col + len(func_name)),
            func_name,
            repr_text=func_name,
        ),
        [arg],
        [],
        resolved_type="bool",
        repr_text=repr_text,
    )
    return _sh_annotate_runtime_call_expr(
        payload,
        lowered_kind="BuiltinCall",
        builtin_name=func_name,
        runtime_call=runtime_call,
        semantic_tag=semantic_tag,
    )


def _sh_make_dict_comp_expr(
    source_span: dict[str, Any],
    key: dict[str, Any],
    value: dict[str, Any],
    generators: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`DictComp` 式 node を構築する。"""
    dict_type = resolved_type
    if dict_type == "":
        dict_type = f"dict[{key.get('resolved_type', 'unknown')},{value.get('resolved_type', 'unknown')}]"
    node = _sh_make_value_expr(
        "DictComp",
        source_span,
        resolved_type=dict_type,
        repr_text=repr_text,
    )
    node["key"] = key
    node["value"] = value
    node["generators"] = generators
    return node


def _sh_make_set_comp_expr(
    source_span: dict[str, Any],
    elt: dict[str, Any],
    generators: list[dict[str, Any]],
    *,
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`SetComp` 式 node を構築する。"""
    set_type = resolved_type if resolved_type != "" else f"set[{str(elt.get('resolved_type', 'unknown'))}]"
    node = _sh_make_value_expr(
        "SetComp",
        source_span,
        resolved_type=set_type,
        repr_text=repr_text,
    )
    node["elt"] = elt
    node["generators"] = generators
    return node


def _sh_make_range_expr(
    source_span: dict[str, Any] | None,
    start: dict[str, Any],
    stop: dict[str, Any],
    step: dict[str, Any],
    *,
    repr_text: str = "",
    range_mode: str = "",
) -> dict[str, Any]:
    """`RangeExpr` node を構築する。"""
    mode = range_mode
    if mode == "":
        step_const_obj: Any = None
        if isinstance(step, dict):
            step_const_obj = step.get("value")
        if step_const_obj == 1:
            mode = "ascending"
        elif step_const_obj == -1:
            mode = "descending"
        else:
            mode = "dynamic"
    node = _sh_make_value_expr(
        "RangeExpr",
        source_span,
        resolved_type="range",
        repr_text=repr_text if repr_text != "" else "range(...)",
    )
    node["start"] = start
    node["stop"] = stop
    node["step"] = step
    node["range_mode"] = mode
    return node


def _sh_make_arg_node(
    arg: str,
    *,
    annotation: str | None = None,
    resolved_type: str = "unknown",
    default: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`arg` node を構築する。"""
    node = _sh_make_node(
        "arg",
        arg=arg,
        annotation=annotation,
        resolved_type=resolved_type,
    )
    if default is not None:
        node["default"] = default
    return node


def _sh_make_lambda_arg_entry(
    name: str,
    default: dict[str, Any] | None,
    resolved_type: str,
) -> dict[str, Any]:
    """lambda parameter の補助 carrier を構築する。"""
    return {
        "name": name,
        "default": default,
        "resolved_type": resolved_type,
    }


def _sh_make_lambda_expr(
    source_span: dict[str, Any],
    args: list[dict[str, Any]],
    body: dict[str, Any],
    *,
    return_type: str = "unknown",
    resolved_type: str = "",
    repr_text: str = "",
) -> dict[str, Any]:
    """`Lambda` 式 node を構築する。"""
    callable_type = resolved_type
    if callable_type == "":
        param_types: list[str] = []
        for arg in args:
            arg_type = str(arg.get("resolved_type", "unknown"))
            param_types.append(arg_type if arg_type != "" else "unknown")
        callable_type = f"callable[{','.join(param_types)}->{return_type}]"
    node = _sh_make_value_expr(
        "Lambda",
        source_span,
        resolved_type=callable_type,
        repr_text=repr_text,
    )
    node["args"] = args
    node["body"] = body
    node["return_type"] = return_type
    return node


def _sh_make_formatted_value_node(
    value: dict[str, Any],
    *,
    conversion: str = "",
    format_spec: str = "",
) -> dict[str, Any]:
    """`FormattedValue` node を構築する。"""
    node = _sh_make_node("FormattedValue", value=value)
    if conversion != "":
        node["conversion"] = conversion
    if format_spec != "":
        node["format_spec"] = format_spec
    return node


def _sh_make_joined_str_expr(
    source_span: dict[str, Any],
    values: list[dict[str, Any]],
    *,
    repr_text: str = "",
) -> dict[str, Any]:
    """`JoinedStr` 式 node を構築する。"""
    node = _sh_make_value_expr(
        "JoinedStr",
        source_span,
        resolved_type="str",
        repr_text=repr_text,
    )
    node["values"] = values
    return node


def _sh_make_assign_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    value: dict[str, Any],
    *,
    declare: bool,
    declare_init: bool = False,
    decl_type: str | None = None,
) -> dict[str, Any]:
    """`Assign` 文 node を構築する。"""
    node = _sh_make_stmt_node("Assign", source_span)
    node["target"] = target
    node["value"] = value
    node["declare"] = declare
    node["decl_type"] = decl_type
    if declare_init:
        node["declare_init"] = True
    return node


def _sh_make_tuple_destructure_assign_stmt(
    source_span: dict[str, Any],
    *,
    line_no: int,
    first_name: str,
    first_col: int,
    first_type: str,
    second_name: str,
    second_col: int,
    second_type: str,
    value: dict[str, Any],
) -> dict[str, Any]:
    """2 要素 tuple destructuring の代入文 node を構築する。"""
    return _sh_make_assign_stmt(
        source_span,
        _sh_make_tuple_expr(
            _sh_span(line_no, first_col, second_col + len(second_name)),
            [
                _sh_make_name_expr(
                    _sh_span(line_no, first_col, first_col + len(first_name)),
                    first_name,
                    resolved_type=first_type,
                ),
                _sh_make_name_expr(
                    _sh_span(line_no, second_col, second_col + len(second_name)),
                    second_name,
                    resolved_type=second_type,
                ),
            ],
            resolved_type="unknown",
            repr_text=f"{first_name}, {second_name}",
        ),
        value,
        declare=False,
        decl_type=None,
    )


def _sh_make_ann_assign_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    annotation: str,
    *,
    annotation_type_expr: dict[str, Any] | None = None,
    value: dict[str, Any] | None = None,
    declare: bool = True,
    decl_type: str | None = None,
    decl_type_expr: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`AnnAssign` 文 node を構築する。"""
    node = _sh_make_stmt_node("AnnAssign", source_span)
    node["target"] = target
    node["annotation"] = annotation
    node["value"] = value
    node["declare"] = declare
    node["decl_type"] = decl_type
    if annotation_type_expr is not None:
        node["annotation_type_expr"] = annotation_type_expr
    if decl_type_expr is not None:
        node["decl_type_expr"] = decl_type_expr
    if meta is not None:
        node["meta"] = meta
    return node


def _sh_make_raise_stmt(
    source_span: dict[str, Any],
    exc: dict[str, Any],
    *,
    cause: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Raise` 文 node を構築する。"""
    node = _sh_make_stmt_node("Raise", source_span)
    node["exc"] = exc
    node["cause"] = cause
    return node


def _sh_make_pass_stmt(source_span: dict[str, Any]) -> dict[str, Any]:
    """`Pass` 文 node を構築する。"""
    return _sh_make_stmt_node("Pass", source_span)


def _sh_make_return_stmt(
    source_span: dict[str, Any],
    value: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Return` 文 node を構築する。"""
    node = _sh_make_stmt_node("Return", source_span)
    node["value"] = value
    return node


def _sh_make_yield_stmt(
    source_span: dict[str, Any],
    value: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`Yield` 文 node を構築する。"""
    node = _sh_make_stmt_node("Yield", source_span)
    node["value"] = value
    return node


def _sh_make_augassign_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    op: str,
    value: dict[str, Any],
    *,
    declare: bool = False,
    decl_type: str | None = None,
) -> dict[str, Any]:
    """`AugAssign` 文 node を構築する。"""
    node = _sh_make_stmt_node("AugAssign", source_span)
    node["target"] = target
    node["op"] = op
    node["value"] = value
    node["declare"] = declare
    node["decl_type"] = decl_type
    return node


def _sh_make_swap_stmt(
    source_span: dict[str, Any],
    left: dict[str, Any],
    right: dict[str, Any],
) -> dict[str, Any]:
    """`Swap` 文 node を構築する。"""
    node = _sh_make_stmt_node("Swap", source_span)
    node["left"] = left
    node["right"] = right
    return node


def _sh_make_import_alias(name: str, asname: str | None = None) -> dict[str, str | None]:
    """import alias item を構築する。"""
    return {
        "name": name,
        "asname": asname,
    }


def _sh_make_import_binding(
    *,
    module_id: str,
    export_name: str,
    local_name: str,
    binding_kind: str,
    source_file: str,
    source_line: int,
) -> dict[str, Any]:
    """import metadata carrier を構築する。"""
    return {
        "module_id": module_id,
        "export_name": export_name,
        "local_name": local_name,
        "binding_kind": binding_kind,
        "source_file": source_file,
        "source_line": source_line,
    }


def _sh_make_import_symbol_binding(module: str, name: str) -> dict[str, str]:
    """import symbol metadata carrier を構築する。"""
    return {
        "module": module,
        "name": name,
    }


def _sh_make_qualified_symbol_ref(module_id: str, symbol: str, local_name: str) -> dict[str, str]:
    """qualified symbol reference carrier を構築する。"""
    return {
        "module_id": module_id,
        "symbol": symbol,
        "local_name": local_name,
    }


def _sh_make_import_stmt(
    source_span: dict[str, Any],
    names: list[dict[str, str | None]],
) -> dict[str, Any]:
    """`Import` 文 node を構築する。"""
    node = _sh_make_stmt_node("Import", source_span)
    node["names"] = names
    return node


def _sh_make_import_from_stmt(
    source_span: dict[str, Any],
    module: str,
    names: list[dict[str, str | None]],
    *,
    level: int = 0,
) -> dict[str, Any]:
    """`ImportFrom` 文 node を構築する。"""
    node = _sh_make_stmt_node("ImportFrom", source_span)
    node["module"] = module
    node["names"] = names
    node["level"] = level
    return node


def _sh_make_if_stmt(
    source_span: dict[str, Any],
    test: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    orelse: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`If` 文 node を構築する。"""
    node = _sh_make_stmt_node("If", source_span)
    node["test"] = test
    node["body"] = body
    node["orelse"] = [] if orelse is None else orelse
    return node


def _sh_make_while_stmt(
    source_span: dict[str, Any],
    test: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    orelse: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`While` 文 node を構築する。"""
    node = _sh_make_stmt_node("While", source_span)
    node["test"] = test
    node["body"] = body
    node["orelse"] = [] if orelse is None else orelse
    return node


def _sh_make_except_handler(
    type_expr: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    name: str | None = None,
) -> dict[str, Any]:
    """`ExceptHandler` node を構築する。"""
    return _sh_make_node("ExceptHandler", type=type_expr, name=name, body=body)


def _sh_make_try_stmt(
    source_span: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    handlers: list[dict[str, Any]] | None = None,
    orelse: list[dict[str, Any]] | None = None,
    finalbody: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`Try` 文 node を構築する。"""
    node = _sh_make_stmt_node("Try", source_span)
    node["body"] = body
    node["handlers"] = [] if handlers is None else handlers
    node["orelse"] = [] if orelse is None else orelse
    node["finalbody"] = [] if finalbody is None else finalbody
    return node


def _sh_make_for_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    iter_expr: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    target_type: str = "unknown",
    iter_mode: str = "static_fastpath",
    iter_source_type: str = "unknown",
    iter_element_type: str = "unknown",
    orelse: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`For` 文 node を構築する。"""
    node = _sh_make_stmt_node("For", source_span)
    node["target"] = target
    node["target_type"] = target_type
    node["iter_mode"] = iter_mode
    node["iter_source_type"] = iter_source_type
    node["iter_element_type"] = iter_element_type
    node["iter"] = iter_expr
    node["body"] = body
    node["orelse"] = [] if orelse is None else orelse
    return node


def _sh_make_for_range_stmt(
    source_span: dict[str, Any],
    target: dict[str, Any],
    start: dict[str, Any],
    stop: dict[str, Any],
    step: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    target_type: str = "int64",
    range_mode: str = "",
    orelse: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """`ForRange` 文 node を構築する。"""
    mode = range_mode
    if mode == "":
        step_const_obj: Any = None
        if isinstance(step, dict):
            step_const_obj = step.get("value")
        if step_const_obj == 1:
            mode = "ascending"
        elif step_const_obj == -1:
            mode = "descending"
        else:
            mode = "dynamic"
    node = _sh_make_stmt_node("ForRange", source_span)
    node["target"] = target
    node["target_type"] = target_type
    node["start"] = start
    node["stop"] = stop
    node["step"] = step
    node["range_mode"] = mode
    node["body"] = body
    node["orelse"] = [] if orelse is None else orelse
    return node


def _sh_make_function_def_stmt(
    name: str,
    source_span: dict[str, Any],
    arg_types: dict[str, str],
    arg_order: list[str],
    return_type: str,
    body: list[dict[str, Any]],
    *,
    original_name: str = "",
    arg_type_exprs: dict[str, Any] | None = None,
    arg_defaults: dict[str, Any] | None = None,
    arg_index: dict[str, int] | None = None,
    return_type_expr: dict[str, Any] | None = None,
    arg_usage: dict[str, Any] | None = None,
    renamed_symbols: dict[str, str] | None = None,
    decorators: list[str] | None = None,
    leading_comments: list[str] | None = None,
    leading_trivia: list[dict[str, Any]] | None = None,
    docstring: str | None = None,
    meta: dict[str, Any] | None = None,
    is_generator: bool = False,
    yield_value_type: str = "unknown",
) -> dict[str, Any]:
    """`FunctionDef` 文 node を構築する。"""
    node = _sh_make_stmt_node("FunctionDef", source_span)
    node["name"] = name
    node["original_name"] = original_name if original_name != "" else name
    node["arg_types"] = arg_types
    node["arg_order"] = arg_order
    node["arg_defaults"] = {} if arg_defaults is None else arg_defaults
    node["arg_index"] = {} if arg_index is None else arg_index
    node["return_type"] = return_type
    node["arg_usage"] = {} if arg_usage is None else arg_usage
    node["renamed_symbols"] = {} if renamed_symbols is None else renamed_symbols
    node["docstring"] = docstring
    node["body"] = body
    node["is_generator"] = 1 if is_generator else 0
    node["yield_value_type"] = yield_value_type
    if arg_type_exprs is not None:
        node["arg_type_exprs"] = arg_type_exprs
    if return_type_expr is not None:
        node["return_type_expr"] = return_type_expr
    if decorators is not None:
        node["decorators"] = decorators
    if leading_comments is not None:
        node["leading_comments"] = leading_comments
    if leading_trivia is not None:
        node["leading_trivia"] = leading_trivia
    if meta is not None:
        node["meta"] = meta
    return node


def _sh_make_class_def_stmt(
    name: str,
    source_span: dict[str, Any],
    field_types: dict[str, str],
    body: list[dict[str, Any]],
    *,
    original_name: str = "",
    base: str | None = None,
    dataclass: bool = False,
    dataclass_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`ClassDef` 文 node を構築する。"""
    node = _sh_make_stmt_node("ClassDef", source_span)
    node["name"] = name
    node["original_name"] = original_name if original_name != "" else name
    node["base"] = base
    node["dataclass"] = dataclass
    node["field_types"] = field_types
    node["body"] = body
    if dataclass_options is not None:
        node["dataclass_options"] = dataclass_options
    return node


def _sh_make_def_sig_info(
    name: str,
    return_type: str,
    arg_types: dict[str, str],
    arg_type_exprs: dict[str, dict[str, Any]],
    return_type_expr: dict[str, Any],
    arg_order: list[str],
    arg_defaults: dict[str, str],
) -> dict[str, Any]:
    """`_sh_parse_def_sig()` の戻り carrier を構築する。"""
    return {
        "name": name,
        "ret": return_type,
        "arg_types": arg_types,
        "arg_type_exprs": arg_type_exprs,
        "return_type_expr": return_type_expr,
        "arg_order": arg_order,
        "arg_defaults": arg_defaults,
    }


def _sh_make_module_source_span() -> dict[str, Any]:
    """Module root 用の空 source_span carrier を構築する。"""
    return {
        "lineno": None,
        "col": None,
        "end_lineno": None,
        "end_col": None,
    }


def _sh_make_import_resolution_meta(
    bindings: list[dict[str, Any]],
    qualified_refs: list[dict[str, str]],
) -> dict[str, Any]:
    """module meta.import_resolution carrier を構築する。"""
    return {
        "schema_version": 1,
        "bindings": bindings,
        "qualified_refs": qualified_refs,
    }


def _sh_make_module_meta(
    *,
    import_resolution: dict[str, Any],
    import_bindings: list[dict[str, Any]],
    qualified_symbol_refs: list[dict[str, str]],
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Module root の meta carrier を構築する。"""
    return {
        "parser_backend": "self_hosted",
        "import_resolution": import_resolution,
        "import_bindings": import_bindings,
        "qualified_symbol_refs": qualified_symbol_refs,
        "import_modules": import_module_bindings,
        "import_symbols": import_symbol_bindings,
    }


def _sh_make_decl_meta(
    *,
    runtime_abi_v1: dict[str, Any] | None = None,
    template_v1: dict[str, Any] | None = None,
    extern_var_v1: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """宣言 node の metadata carrier を構築する。"""
    meta: dict[str, Any] = {}
    if runtime_abi_v1 is not None:
        meta["runtime_abi_v1"] = runtime_abi_v1
    if template_v1 is not None:
        meta["template_v1"] = template_v1
    if extern_var_v1 is not None:
        meta["extern_var_v1"] = extern_var_v1
    return meta


def _sh_make_module_root(
    *,
    filename: str,
    body_items: list[dict[str, Any]],
    main_stmts: list[dict[str, Any]],
    renamed_symbols: dict[str, str],
    import_resolution_bindings: list[dict[str, Any]],
    qualified_symbol_refs: list[dict[str, str]],
    import_bindings: list[dict[str, Any]],
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Module root を構築する。"""
    source_span = _sh_make_module_source_span()
    import_resolution = _sh_make_import_resolution_meta(import_resolution_bindings, qualified_symbol_refs)
    meta = _sh_make_module_meta(
        import_resolution=import_resolution,
        import_bindings=import_bindings,
        qualified_symbol_refs=qualified_symbol_refs,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    )
    return _sh_make_node(
        "Module",
        source_path=filename,
        source_span=source_span,
        body=body_items,
        main_guard_body=main_stmts,
        renamed_symbols=renamed_symbols,
        meta=meta,
    )


def _sh_ann_to_type(ann: str, *, type_aliases: dict[str, str] | None = None) -> str:
    """型注釈文字列を EAST 正規型へ変換する。"""
    aliases: dict[str, str] = type_aliases if type_aliases is not None else _SH_TYPE_ALIASES
    return type_expr_to_string(parse_type_expr_text(ann, type_aliases=aliases))


def _sh_ann_to_type_expr(
    ann: str,
    *,
    type_aliases: dict[str, str] | None = None,
) -> dict[str, Any]:
    aliases: dict[str, str] = type_aliases if type_aliases is not None else _SH_TYPE_ALIASES
    return parse_type_expr_text(ann, type_aliases=aliases)


def _sh_type_expr_to_type_name(expr: dict[str, Any]) -> str:
    return type_expr_to_string(expr)


def _sh_split_args_with_offsets(arg_text: str) -> list[tuple[str, int]]:
    """引数文字列をトップレベルのカンマで分割し、相対オフセットも返す。"""
    out: list[tuple[str, int]] = []
    depth = 0
    in_str: str | None = None
    esc = False
    start = 0
    for i, ch in enumerate(arg_text):
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == "," and depth == 0:
            part = arg_text[start:i]
            out.append((part.strip(), start + (len(part) - len(part.lstrip()))))
            start = i + 1
    tail = arg_text[start:]
    if tail.strip() != "":
        out.append((tail.strip(), start + (len(tail) - len(tail.lstrip()))))
    return out


def _sh_parse_typed_binding(text: str, *, allow_dotted_name: bool = False) -> tuple[str, str, str] | None:
    """`name: Type` / `name: Type = expr` を手書きパースし、(name, type, default) を返す。"""
    raw = text.strip()
    if raw == "":
        return None
    colon = raw.find(":")
    if colon <= 0:
        return None
    name_txt = raw[:colon].strip()
    ann_txt = raw[colon + 1 :].strip()
    if ann_txt == "":
        return None
    if allow_dotted_name:
        name_parts = name_txt.split(".")
        if len(name_parts) == 0:
            return None
        norm_parts: list[str] = []
        for seg in name_parts:
            seg_norm = seg.strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", seg_norm) is None:
                return None
            norm_parts.append(seg_norm)
        name_txt = ".".join(norm_parts)
    else:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name_txt) is None:
            return None
    default_txt = ""
    split_ann = _sh_split_top_level_assign(ann_txt)
    if split_ann is not None:
        ann_lhs, ann_rhs = split_ann
        ann_txt = ann_lhs.strip()
        default_txt = ann_rhs.strip()
    if ann_txt == "":
        return None
    return name_txt, ann_txt, default_txt


def _sh_is_identifier(text: str) -> bool:
    """ASCII 識別子（先頭英字/`_`）かを返す。"""
    if text == "":
        return False
    c0 = text[0:1]
    is_head = ("A" <= c0 <= "Z") or ("a" <= c0 <= "z") or c0 == "_"
    if not is_head:
        return False
    for ch in text[1:]:
        is_body = ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ("0" <= ch <= "9") or ch == "_"
        if not is_body:
            return False
    return True


def _sh_strip_utf8_bom(source: str) -> str:
    """UTF-8 BOM を先頭から除去する。"""
    if source.startswith("\ufeff"):
        return source[1:]
    return source


def _sh_is_dotted_identifier(text: str) -> bool:
    """`a.b.c` 形式の識別子列かを返す。"""
    if text.strip() == "":
        return False
    parts = text.split(".")
    if len(parts) == 0:
        return False
    for seg in parts:
        if not _sh_is_identifier(seg):
            return False
    return True


def _sh_parse_import_alias(text: str, *, allow_dotted_name: bool) -> tuple[str, str] | None:
    """`name` / `name as alias` を手書きパースして (name, alias_or_empty) を返す。"""
    raw = text.strip()
    if raw == "":
        return None
    name_txt = raw
    alias_txt = ""
    as_split = _sh_split_top_level_as(raw)
    if as_split is not None:
        name_txt, alias_txt = as_split
        name_txt = name_txt.strip()
        alias_txt = alias_txt.strip()
    if name_txt == "":
        return None
    if allow_dotted_name:
        if not _sh_is_dotted_identifier(name_txt):
            return None
    else:
        if not _sh_is_identifier(name_txt):
            return None
    if alias_txt != "" and not _sh_is_identifier(alias_txt):
        return None
    return name_txt, alias_txt


def _sh_parse_decorator_head_and_args(text: str) -> tuple[str, str]:
    """`decorator` / `decorator(...)` を (head, args_txt_or_empty) に分解する。"""
    raw = text.strip()
    if raw == "":
        return "", ""
    depth = 0
    in_str: str | None = None
    esc = False
    lp = -1
    for i, ch in enumerate(raw):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            if ch == "(" and depth == 0:
                lp = i
                break
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
    if lp < 0:
        return raw, ""
    if not raw.endswith(")"):
        return raw, ""
    depth = 0
    in_str = None
    esc = False
    rp = -1
    i = lp
    while i < len(raw):
        ch = raw[i]
        if in_str is not None:
            if esc:
                esc = False
                i += 1
                continue
            if ch == "\\":
                esc = True
                i += 1
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in {"'", '"'}:
            in_str = ch
            i += 1
            continue
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            depth -= 1
            if depth == 0:
                rp = i
                break
            i += 1
            continue
        i += 1
    if rp < 0 or rp != len(raw) - 1:
        return raw, ""
    head = raw[:lp].strip()
    if head == "":
        return raw, ""
    return head, raw[lp + 1 : rp].strip()


def _sh_is_dataclass_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> bool:
    """decorator 文字列が dataclass 系（標準 dataclasses 由来）か判定する。"""
    head, _args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    if head == "":
        return False
    if head == "dataclass":
        return True
    if head.endswith(".dataclass"):
        owner = head[:-len(".dataclass")]
        if owner == "dataclasses":
            return True
        mod_name = import_module_bindings.get(owner, "")
        return mod_name == "dataclasses"
    ent = import_symbol_bindings.get(head)
    if not isinstance(ent, dict):
        return False
    mod_name = str(ent.get("module", ""))
    sym_name = str(ent.get("name", ""))
    return mod_name == "dataclasses" and sym_name == "dataclass"


def _sh_parse_dataclass_decorator_options(args_txt: str, *, line_no: int, line_text: str) -> dict[str, bool]:
    """`@dataclass(...)` の keyword bool オプションを抽出する。"""
    out: dict[str, bool] = {}
    if args_txt.strip() == "":
        return out
    parts = _sh_split_top_commas(args_txt)
    for part_raw in parts:
        part = part_raw.strip()
        if part == "":
            continue
        kv = _sh_split_top_level_assign(part)
        if kv is None:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"unsupported dataclass decorator argument: {part}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint="Use keyword bool args only: dataclass(init=..., repr=..., eq=...).",
            )
        key, val = kv
        k = key.strip()
        v = val.strip()
        if not _sh_is_identifier(k):
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"invalid dataclass option name: {k}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint="Use identifier keyword options: dataclass(name=True/False, ...).",
            )
        if v == "True":
            out[k] = True
            continue
        if v == "False":
            out[k] = False
            continue
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"dataclass option must be bool literal: {k}={v}",
            source_span=_sh_span(line_no, 0, len(line_text)),
            hint="Use True/False literal values.",
        )
    return out


def _sh_is_abi_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> bool:
    """decorator 文字列が `pytra.std.abi` を指すか判定する。"""
    head, _args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    if head == "":
        return False
    if head == "abi":
        return True
    if head.endswith(".abi"):
        owner = head[:-len(".abi")]
        if owner == "pytra.std":
            return True
        mod_name = import_module_bindings.get(owner, "")
        return mod_name == "pytra.std"
    ent = import_symbol_bindings.get(head)
    if not isinstance(ent, dict):
        return False
    mod_name = str(ent.get("module", ""))
    sym_name = str(ent.get("name", ""))
    return mod_name == "pytra.std" and sym_name == "abi"


def _sh_is_template_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> bool:
    """decorator 文字列が `pytra.std.template.template` 系を指すか判定する。"""
    head, _args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    if head == "":
        return False
    if head == "template":
        return True
    if head.endswith(".template"):
        owner = head[:-len(".template")]
        if owner in {"pytra.std", "pytra.std.template"}:
            return True
        mod_name = import_module_bindings.get(owner, "")
        return mod_name in {"pytra.std", "pytra.std.template"}
    ent = import_symbol_bindings.get(head)
    if not isinstance(ent, dict):
        return False
    mod_name = str(ent.get("module", ""))
    sym_name = str(ent.get("name", ""))
    return mod_name in {"pytra.std", "pytra.std.template"} and sym_name == "template"


def _sh_expr_attr_chain(expr: Any) -> str:
    """Name/Attribute 式から `a.b.c` 形式の head 文字列を抽出する。"""
    if not isinstance(expr, dict):
        return ""
    kind = str(expr.get("kind", ""))
    if kind == "Name":
        return str(expr.get("id", ""))
    if kind != "Attribute":
        return ""
    owner = _sh_expr_attr_chain(expr.get("value"))
    attr = str(expr.get("attr", ""))
    if owner == "" or attr == "":
        return ""
    return owner + "." + attr


def _sh_is_extern_symbol_ref(
    head: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> bool:
    """call head が `pytra.std.extern` を指すか判定する。"""
    if head == "":
        return False
    ent = import_symbol_bindings.get(head)
    if isinstance(ent, dict):
        return str(ent.get("module", "")) == "pytra.std" and str(ent.get("name", "")) == "extern"
    if head.endswith(".extern"):
        owner = head[: -len(".extern")]
        if owner == "pytra.std":
            return True
        mod_name = import_module_bindings.get(owner, "")
        return mod_name == "pytra.std"
    return False


def _sh_collect_extern_var_metadata(
    *,
    target_name: str,
    annotation: str,
    value_expr: Any,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> dict[str, Any] | None:
    """`name: Any = extern(...)` から ambient global metadata を抽出する。"""
    if annotation != "Any":
        return None
    if not isinstance(value_expr, dict) or str(value_expr.get("kind", "")) != "Call":
        return None
    call_head = _sh_expr_attr_chain(value_expr.get("func"))
    if not _sh_is_extern_symbol_ref(
        call_head,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    ):
        return None
    args = value_expr.get("args")
    keywords = value_expr.get("keywords")
    if not isinstance(args, list) or not isinstance(keywords, list) or len(keywords) != 0:
        return None
    symbol = target_name
    if len(args) == 0:
        symbol = target_name
    elif len(args) == 1:
        arg0 = args[0]
        if (
            not isinstance(arg0, dict)
            or str(arg0.get("kind", "")) != "Constant"
            or str(arg0.get("resolved_type", "")) != "str"
        ):
            return None
        symbol = str(arg0.get("value", "")).strip()
        if symbol == "":
            return None
    else:
        return None
    return {
        "schema_version": 1,
        "symbol": symbol,
        "same_name": 1 if symbol == target_name else 0,
    }


def _sh_parse_runtime_abi_string_literal(text: str, *, line_no: int, line_text: str, field_name: str) -> str:
    raw = text.strip()
    if len(raw) >= 2 and raw[0] in {"'", '"'} and raw[-1] == raw[0]:
        return raw[1:-1]
    raise _make_east_build_error(
        kind="unsupported_syntax",
        message=f"{field_name} must be a string literal: {raw}",
        source_span=_sh_span(line_no, 0, len(line_text)),
        hint="Use quoted string literals such as \"value\" or \"parts\".",
    )


def _sh_parse_runtime_abi_mode(
    text: str,
    *,
    line_no: int,
    line_text: str,
    field_name: str,
    allowed_modes: set[str],
    hint_text: str,
) -> str:
    mode = _sh_parse_runtime_abi_string_literal(text, line_no=line_no, line_text=line_text, field_name=field_name)
    normalized = _SH_RUNTIME_ABI_MODE_ALIASES.get(mode, mode)
    if normalized in allowed_modes:
        return normalized
    raise _make_east_build_error(
        kind="unsupported_syntax",
        message=f"unsupported abi mode for {field_name}: {mode}",
        source_span=_sh_span(line_no, 0, len(line_text)),
        hint=hint_text,
    )


def _sh_parse_runtime_abi_args_map(text: str, *, line_no: int, line_text: str) -> dict[str, str]:
    raw = text.strip()
    if raw in {"", "None"}:
        return {}
    if not (raw.startswith("{") and raw.endswith("}")):
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"abi args must be a dict literal: {raw}",
            source_span=_sh_span(line_no, 0, len(line_text)),
            hint='Use args={"param": "value"} form.',
        )
    inner = raw[1:-1].strip()
    if inner == "":
        return {}
    out: dict[str, str] = {}
    for part_raw in _sh_split_top_commas(inner):
        part = part_raw.strip()
        if part == "":
            continue
        split = _sh_split_top_level_colon(part)
        if split is None:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"unsupported abi args entry: {part}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint='Use args={"param": "value"} entries only.',
            )
        key_txt, value_txt = split
        key = _sh_parse_runtime_abi_string_literal(
            key_txt,
            line_no=line_no,
            line_text=line_text,
            field_name="abi args key",
        )
        if not _sh_is_identifier(key):
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"abi args key must be an identifier name: {key}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint='Use quoted parameter names such as "parts".',
            )
        if key in out:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"duplicate abi args entry: {key}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint="Specify each parameter at most once.",
            )
        out[key] = _sh_parse_runtime_abi_mode(
            value_txt,
            line_no=line_no,
            line_text=line_text,
            field_name=f"abi args[{key}]",
            allowed_modes=_SH_RUNTIME_ABI_ARG_MODES,
            hint_text='Use one of "default", "value", or "value_mut".',
        )
    return out


def _sh_parse_runtime_abi_decorator(
    decorator_text: str,
    *,
    arg_order: list[str],
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
) -> dict[str, Any] | None:
    if not _sh_is_abi_decorator(
        decorator_text,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    ):
        return None
    _head, args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    if args_txt == "":
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="abi decorator requires keyword-only call form",
            source_span=_sh_span(line_no, 0, len(line_text)),
            hint='Use `@abi(args={"name": "value"}, ret="value")`.',
        )
    out_args: dict[str, str] = {}
    out_ret = "default"
    seen_keys: set[str] = set()
    for part_raw in _sh_split_top_commas(args_txt):
        part = part_raw.strip()
        if part == "":
            continue
        split = _sh_split_top_level_assign(part)
        if split is None:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"abi decorator accepts keyword arguments only: {part}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint='Use `args=...` and `ret=...` keyword arguments only.',
            )
        key_txt, value_txt = split
        key = key_txt.strip()
        if key in seen_keys:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"duplicate abi decorator option: {key}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint="Specify each abi decorator option at most once.",
            )
        seen_keys.add(key)
        if key == "args":
            out_args = _sh_parse_runtime_abi_args_map(value_txt, line_no=line_no, line_text=line_text)
            continue
        if key == "ret":
            out_ret = _sh_parse_runtime_abi_mode(
                value_txt,
                line_no=line_no,
                line_text=line_text,
                field_name="abi ret",
                allowed_modes=_SH_RUNTIME_ABI_RET_MODES,
                hint_text='Use one of "default" or "value".',
            )
            continue
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"unsupported abi decorator option: {key}",
            source_span=_sh_span(line_no, 0, len(line_text)),
            hint='Supported keys are `args` and `ret` only.',
        )
    valid_args = set(arg_order)
    for param_name in out_args.keys():
        if param_name not in valid_args:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"abi decorator references unknown parameter: {param_name}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint="Use only declared function parameter names in abi args.",
            )
    return {
        "schema_version": 1,
        "args": out_args,
        "ret": out_ret,
    }


def _sh_collect_runtime_abi_metadata(
    decorators: list[str],
    *,
    arg_order: list[str],
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
) -> dict[str, Any] | None:
    runtime_abi_meta: dict[str, Any] | None = None
    for decorator_text in decorators:
        parsed = _sh_parse_runtime_abi_decorator(
            decorator_text,
            arg_order=arg_order,
            import_module_bindings=import_module_bindings,
            import_symbol_bindings=import_symbol_bindings,
            line_no=line_no,
            line_text=line_text,
        )
        if parsed is None:
            continue
        if runtime_abi_meta is not None:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message="multiple abi decorators on one function are not supported",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint="Use a single @abi(args=..., ret=...) decorator.",
            )
        runtime_abi_meta = parsed
    return runtime_abi_meta


def _sh_parse_template_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
) -> dict[str, Any] | None:
    if not _sh_is_template_decorator(
        decorator_text,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    ):
        return None
    _head, args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    if args_txt == "":
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="template decorator requires one or more string literal parameters",
            source_span=_sh_span(line_no, 0, len(line_text)),
            hint='Use `@template("T")` or `@template("K", "V")`.',
        )
    params: list[str] = []
    seen: set[str] = set()
    for part_raw in _sh_split_top_commas(args_txt):
        part = part_raw.strip()
        if part == "":
            continue
        if _sh_split_top_level_assign(part) is not None:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"template decorator accepts positional string literal parameters only: {part}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint='Use `@template("T", "U")` form.',
            )
        param = _sh_parse_runtime_abi_string_literal(
            part,
            line_no=line_no,
            line_text=line_text,
            field_name="template parameter",
        )
        if not _sh_is_identifier(param):
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"template parameter must be an identifier name: {param}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint='Use identifier-like strings such as "T" or "Value".',
            )
        if param in seen:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"duplicate template parameter: {param}",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint="Specify each template parameter at most once.",
            )
        seen.add(param)
        params.append(param)
    if len(params) == 0:
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="template decorator requires one or more string literal parameters",
            source_span=_sh_span(line_no, 0, len(line_text)),
            hint='Use `@template("T")` or `@template("K", "V")`.',
        )
    return {
        "schema_version": 1,
        "params": params,
        "scope": _SH_TEMPLATE_SCOPE,
        "instantiation_mode": _SH_TEMPLATE_INSTANTIATION_MODE,
    }


def _sh_collect_template_metadata(
    decorators: list[str],
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
) -> dict[str, Any] | None:
    template_meta: dict[str, Any] | None = None
    for decorator_text in decorators:
        parsed = _sh_parse_template_decorator(
            decorator_text,
            import_module_bindings=import_module_bindings,
            import_symbol_bindings=import_symbol_bindings,
            line_no=line_no,
            line_text=line_text,
        )
        if parsed is None:
            continue
        if template_meta is not None:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message="multiple template decorators on one function are not supported",
                source_span=_sh_span(line_no, 0, len(line_text)),
                hint='Use a single `@template("T", ...)` decorator.',
            )
        template_meta = parsed
    return template_meta


def _sh_parse_augassign(text: str) -> tuple[str, str, str] | None:
    """`target <op>= expr` をトップレベルで分解して返す。"""
    raw = text.strip()
    if raw == "":
        return None
    ops = ["<<=", ">>=", "//=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="]
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(raw):
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if depth == 0:
            for op in ops:
                if raw[i : i + len(op)] == op:
                    left = raw[:i].strip()
                    right = raw[i + len(op) :].strip()
                    if left == "" or right == "":
                        return None
                    # allow Name / Attribute / Subscript lvalues, e.g. "a[i] += 1"
                    if left.count("=") > 0:
                        return None
                    return left, op, right
    return None


def _sh_scan_string_token(text: str, start: int, quote_pos: int, line_no: int, col_base: int) -> int:
    """文字列リテラルの終端位置を走査して返す。"""
    if quote_pos + 2 < len(text) and text[quote_pos : quote_pos + 3] in {"'''", '"""'}:
        q3 = text[quote_pos : quote_pos + 3]
        j = quote_pos + 3
        while j + 2 < len(text):
            if text[j : j + 3] == q3:
                return j + 3
            j += 1
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="unterminated triple-quoted string literal in self_hosted parser",
            source_span=_sh_span(line_no, col_base + start, col_base + len(text)),
            hint="Close triple-quoted string with matching quote.",
        )
    q = text[quote_pos]
    j = quote_pos + 1
    while j < len(text):
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == q:
            return j + 1
        j += 1
    raise _make_east_build_error(
        kind="unsupported_syntax",
        message="unterminated string literal in self_hosted parser",
        source_span=_sh_span(line_no, col_base + start, col_base + len(text)),
        hint="Close string literal with matching quote.",
    )


def _sh_decode_py_string_body(text: str, raw_mode: bool) -> str:
    """Python 文字列リテラル本体（引用符除去後）を簡易復号する。"""
    if raw_mode:
        return text
    out = ""
    skip = 0
    for i, ch in enumerate(text):
        if skip > 0:
            skip -= 1
            continue
        if ch != "\\":
            out += ch
            continue
        if i + 1 >= len(text):
            out += "\\"
            break
        esc = text[i + 1 : i + 2]
        skip = 1
        if esc == "n":
            out += "\n"
        elif esc == "r":
            out += "\r"
        elif esc == "t":
            out += "\t"
        elif esc == "b":
            out += "\b"
        elif esc == "f":
            out += "\f"
        elif esc == "v":
            out += "\v"
        elif esc == "a":
            out += "\a"
        elif esc in {'"', "'", "\\"}:
            out += esc
        elif esc == "x" and i + 2 < len(text):
            hex2 = text[i + 1 : i + 3]
            try:
                out += chr(int(hex2, 16))
                skip = 3
            except ValueError:
                out += "x"
        elif esc == "u" and i + 4 < len(text):
            hex4 = text[i + 1 : i + 5]
            try:
                out += chr(int(hex4, 16))
                skip = 4
            except ValueError:
                out += "u"
        else:
            out += esc
    return out


def _sh_append_fstring_literal(values: list[dict[str, Any]], segment: str, span: dict[str, int], *, raw_mode: bool = False) -> None:
    """f-string の生文字列片を Constant(str) ノードとして values に追加する。"""
    lit = segment.replace("{{", "{").replace("}}", "}")
    lit = _sh_decode_py_string_body(lit, raw_mode)
    if lit == "":
        return
    node: dict[str, Any] = {}
    node["kind"] = "Constant"
    node["source_span"] = span
    node["resolved_type"] = "str"
    node["borrow_kind"] = "value"
    node["casts"] = []
    node["repr"] = json.dumps(lit)
    node["value"] = lit
    values.append(node)


def _sh_parse_def_sig(
    ln_no: int,
    ln: str,
    *,
    in_class: str = "",
) -> dict[str, Any] | None:
    """`def ...` 行から関数名・引数型・戻り型を抽出する。"""
    aliases = _SH_TYPE_ALIASES
    ln_norm: str = re.sub(r"\s+", " ", ln.strip())
    if not ln_norm.startswith("def ") or not ln_norm.endswith(":"):
        return None
    head = ln_norm[4:-1].strip()
    lp = head.find("(")
    rp = head.rfind(")")
    if lp <= 0 or rp < lp:
        return None
    fn_name = ""
    args_raw: str = ""
    ret_group: str = ""
    fn_name = head[:lp].strip()
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", fn_name) is None:
        return None
    args_raw = head[lp + 1 : rp]
    tail = head[rp + 1 :].strip()
    if tail == "":
        ret_group = ""
    elif tail.startswith("->"):
        ret_group = tail[2:].strip()
        if ret_group == "":
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message="self_hosted parser cannot parse return annotation in function signature",
                source_span=_sh_span(ln_no, 0, len(ln_norm)),
                hint="Use `def name(args) -> Type:` style signature.",
            )
    else:
        return None
    arg_types: dict[str, str] = {}
    arg_type_exprs: dict[str, dict[str, Any]] = {}
    arg_order: list[str] = []
    arg_defaults: dict[str, str] = {}
    if args_raw.strip() != "":
        # Supported:
        # - name: Type
        # - name: Type = default
        # - "*" keyword-only marker
        # Not supported:
        # - "/" positional-only marker
        for p_txt, _off in _sh_split_args_with_offsets(args_raw):
            p: str = p_txt.strip()
            if p == "":
                continue
            if p == "*":
                continue
            if p == "/":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="self_hosted parser cannot parse positional-only marker '/' in parameter list",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Remove '/' from signature for now.",
                )
            if p.startswith("**"):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse variadic kwargs parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use explicit parameters instead of **kwargs.",
                )
            if p.startswith("*"):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse variadic args parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use explicit parameters instead of *args.",
                )
            if in_class != "" and p == "self":
                arg_types["self"] = in_class
                arg_type_exprs["self"] = _sh_ann_to_type_expr(in_class, type_aliases=aliases)
                arg_order.append("self")
                continue
            if ":" not in p:
                p_name = p
                p_default = ""
                p_assign = _sh_split_top_level_assign(p)
                if p_assign is not None:
                    p_name = p_assign[0].strip()
                    p_default = p_assign[1].strip()
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", p_name):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter name: {p_txt}",
                        source_span=_sh_span(ln_no, 0, len(ln_norm)),
                        hint="Use valid identifier for parameter name.",
                    )
                if in_class != "" and p_name == "self":
                    arg_types["self"] = in_class
                    arg_type_exprs["self"] = _sh_ann_to_type_expr(in_class, type_aliases=aliases)
                    arg_order.append("self")
                    if p_default != "":
                        arg_defaults["self"] = p_default
                    continue
                arg_types[p_name] = "unknown"
                arg_type_exprs[p_name] = _sh_ann_to_type_expr("unknown", type_aliases=aliases)
                arg_order.append(p_name)
                if p_default != "":
                    arg_defaults[p_name] = p_default
                continue
            parsed_param = _sh_parse_typed_binding(p, allow_dotted_name=False)
            if parsed_param is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use `name: Type` style parameters.",
                )
            pn, pt, pdef = parsed_param
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", pn):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter name: {pn}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use valid identifier for parameter name.",
                )
            if pt == "":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter type: {p_txt}",
                    source_span=_sh_span(ln_no, 0, len(ln_norm)),
                    hint="Use `name: Type` style parameters.",
                )
            arg_expr = _sh_ann_to_type_expr(pt, type_aliases=aliases)
            arg_types[pn] = _sh_type_expr_to_type_name(arg_expr)
            arg_type_exprs[pn] = arg_expr
            arg_order.append(pn)
            if pdef != "":
                default_txt = pdef.strip()
                if default_txt != "":
                    arg_defaults[pn] = default_txt
    ret_expr = _sh_ann_to_type_expr(ret_group.strip(), type_aliases=aliases) if ret_group != "" else _sh_ann_to_type_expr("None", type_aliases=aliases)
    return _sh_make_def_sig_info(
        fn_name,
        _sh_type_expr_to_type_name(ret_expr),
        arg_types,
        arg_type_exprs,
        ret_expr,
        arg_order,
        arg_defaults,
    )


def _sh_split_def_header_and_inline_stmt(text: str) -> tuple[str, str]:
    """`def ...:` と同一行本文（`def ...: stmt`）を分割する。"""
    txt = text.strip()
    if not txt.startswith("def "):
        return txt, ""
    if txt.endswith(":"):
        return txt, ""
    split = _sh_split_top_level_colon(txt)
    if split is None:
        return txt, ""
    head, inline_stmt = split
    head = head.strip()
    inline_stmt = inline_stmt.strip()
    if not head.startswith("def ") or inline_stmt == "":
        return txt, ""
    return head + ":", inline_stmt


def _sh_scan_logical_line_state(
    txt: str,
    depth: int,
    mode: str,
) -> tuple[int, str]:
    """論理行マージ用に括弧深度と文字列モードを更新する。"""
    mode_cur = mode
    skip = 0
    for i, ch in enumerate(txt):
        if skip > 0:
            skip -= 1
            continue
        if mode_cur in {"'''", '"""'}:
            close = txt.find(mode_cur, i)
            if close < 0:
                break
            skip = close + 3 - i - 1
            mode_cur = ""
            continue
        if mode_cur in {"'", '"'}:
            if ch == "\\":
                skip = 1
                continue
            if ch == mode_cur:
                mode_cur = ""
            continue
        if i + 2 < len(txt) and txt[i : i + 3] in {"'''", '"""'}:
            mode_cur = txt[i : i + 3]
            skip = 2
            continue
        if ch in {"'", '"'}:
            mode_cur = ch
            continue
        if ch == "#":
            break
        if ch in {"(", "[", "{"}:
            depth += 1
        elif ch in {")", "]", "}"}:
            depth -= 1
    return depth, mode_cur


def _sh_has_explicit_line_continuation(txt: str) -> bool:
    """行末 `\\` による明示継続かを返す（文字列/コメント外のみ）。"""
    body = _sh_strip_inline_comment(txt).rstrip()
    if body == "":
        return False
    backslashes = 0
    for i in range(len(body) - 1, -1, -1):
        if body[i] == "\\":
            backslashes += 1
        else:
            break
    return (backslashes % 2) == 1


def _sh_merge_logical_lines(raw_lines: list[tuple[int, str]]) -> tuple[list[tuple[int, str]], dict[int, tuple[int, int]]]:
    """物理行を論理行へマージし、開始行ごとの終了行情報も返す。"""
    merged: list[tuple[int, str]] = []
    merged_line_end: dict[int, tuple[int, int]] = {}
    idx = 0
    while idx < len(raw_lines):
        start_no, start_txt = raw_lines[idx]
        acc = start_txt
        depth = 0
        mode = ""
        depth, mode = _sh_scan_logical_line_state(start_txt, depth, mode)
        explicit_cont = _sh_has_explicit_line_continuation(start_txt)
        end_no = start_no
        end_txt = start_txt
        while (depth > 0 or mode in {"'''", '"""'} or explicit_cont) and idx + 1 < len(raw_lines):
            idx += 1
            next_no, next_txt = raw_lines[idx]
            if mode in {"'''", '"""'}:
                acc += "\n" + next_txt
            else:
                # Merge continuation lines after stripping per-line inline comments.
                # (Stripping only after full merge loses code that appears after
                # comment-bearing continuation lines.)
                left_txt = _sh_strip_inline_comment(acc).rstrip()
                if explicit_cont:
                    bs_count = 0
                    j = len(left_txt) - 1
                    while j >= 0 and left_txt[j] == "\\":
                        bs_count += 1
                        j -= 1
                    if (bs_count % 2) == 1:
                        left_txt = left_txt[:-1].rstrip()
                right_txt = _sh_strip_inline_comment(next_txt).strip()
                acc = left_txt + " " + right_txt
            depth, mode = _sh_scan_logical_line_state(next_txt, depth, mode)
            explicit_cont = _sh_has_explicit_line_continuation(next_txt)
            end_no = next_no
            end_txt = next_txt
        merged.append((start_no, acc))
        merged_line_end[start_no] = (end_no, len(end_txt))
        idx += 1
    return merged, merged_line_end


def _sh_split_top_commas(txt: str) -> list[str]:
    """文字列/括弧深度を考慮してトップレベルのカンマ分割を行う。"""
    out: list[str] = []
    depth = 0
    in_str: str | None = None
    esc = False
    start = 0
    for i, ch in enumerate(txt):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == "," and depth == 0:
            out.append(txt[start:i].strip())
            start = i + 1
    tail = txt[start:].strip()
    if tail != "":
        out.append(tail)
    return out


def _sh_split_top_keyword(text: str, kw: str) -> int:
    """トップレベルでキーワード出現位置を探す（未検出なら -1）。"""
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if depth == 0 and text[i:].startswith(kw):
            prev_ok = i == 0 or text[i - 1].isspace()
            next_ok = (i + len(kw) >= len(text)) or text[i + len(kw)].isspace()
            if prev_ok and next_ok:
                return i
    return -1


def _sh_split_top_plus(text: str) -> list[str]:
    """トップレベルの `+` で式を分割する。"""
    out: list[str] = []
    depth = 0
    in_str: str | None = None
    esc = False
    start = 0
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == "+" and depth == 0:
            out.append(text[start:i].strip())
            start = i + 1
    tail = text[start:].strip()
    if tail != "":
        out.append(tail)
    return out


def _sh_extract_adjacent_string_parts(
    text: str,
    line_no: int,
    col_base: int,
    name_types: dict[str, str],
) -> list[tuple[str, int]] | None:
    """トップレベルで `STR STR ...` のみで構成される式を、文字列トークン分割して返す。

    タプルを構成する `("a", "b")` のようなケースは除外し、括弧付きでも
    外側が1組の `()` で全体を包む形式に対応する。
    """
    parser = _ShExprParser(
        text,
        line_no,
        col_base,
        dict(name_types),
        _SH_FN_RETURNS,
        _SH_CLASS_METHOD_RETURNS,
        _SH_CLASS_BASE,
    )
    toks = parser._tokenize(text)
    if len(toks) <= 1:
        return None
    if toks[-1].get("k") != "EOF":
        return None
    end = len(toks) - 1
    start = 0
    if end > 1 and toks[0].get("k") == "(" and toks[end - 1].get("k") == ")":
        start = 1
        end -= 1
    inner = toks[start:end]
    if len(inner) == 0:
        return None
    for tok in inner:
        if tok.get("k") != "STR":
            return None
    if len(inner) < 2:
        return None
    return [(str(tok.get("v", "")), int(tok.get("s", 0)) + col_base) for tok in inner]


def _sh_find_top_char(text: str, needle: str) -> int:
    """文字列/括弧深度を考慮してトップレベルの1文字を探す（未検出なら -1）。"""
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == needle and depth == 0:
            return i
    return -1


def _sh_infer_item_type(node: dict[str, Any]) -> str:
    """dict/list/set/range 由来の反復要素型を簡易推論する。"""
    t = str(node.get("resolved_type", "unknown"))
    if t == "range":
        return "int64"
    if t.startswith("list[") and t.endswith("]"):
        inner = t[5:-1].strip()
        if inner != "":
            return inner
        return "unknown"
    if t.startswith("set[") and t.endswith("]"):
        inner = t[4:-1].strip()
        if inner != "":
            return inner
        return "unknown"
    if t in {"bytes", "bytearray"}:
        return "uint8"
    if t == "str":
        return "str"
    return "unknown"


def _sh_bind_comp_target_types(
    base_types: dict[str, str],
    target_node: dict[str, Any],
    iter_node: dict[str, Any],
) -> dict[str, str]:
    """内包表記 target へ反復要素型を束縛した name_types を返す。"""
    out: dict[str, str] = dict(base_types)
    item_t = _sh_infer_item_type(iter_node)
    if target_node.get("kind") == "Name":
        nm = str(target_node.get("id", ""))
        if nm != "":
            out[nm] = item_t
        return out
    if target_node.get("kind") != "Tuple":
        return out
    elem_nodes = target_node.get("elements", [])
    elem_types: list[str] = []
    if item_t.startswith("tuple[") and item_t.endswith("]"):
        inner = item_t[6:-1].strip()
        if inner != "":
            elem_types = _sh_split_top_commas(inner)
    for idx, e in enumerate(elem_nodes):
        if isinstance(e, dict) and e.get("kind") == "Name":
            nm = str(e.get("id", ""))
            if nm != "":
                if idx < len(elem_types):
                    et = elem_types[idx].strip()
                    if et == "":
                        et = "unknown"
                    out[nm] = et
                else:
                    out[nm] = "unknown"
    return out


def _sh_block_end_span(
    body_lines: list[tuple[int, str]],
    start_ln: int,
    start_col: int,
    fallback_end_col: int,
    end_idx_exclusive: int,
) -> dict[str, int]:
    """複数行文の終端まで含む source_span を生成する。"""
    if end_idx_exclusive > 0 and end_idx_exclusive - 1 < len(body_lines):
        end_ln, end_txt = body_lines[end_idx_exclusive - 1]
        return _sh_span(start_ln, start_col, len(end_txt), end_lineno=end_ln)
    return _sh_span(start_ln, start_col, fallback_end_col)


def _sh_stmt_span(
    merged_line_end: dict[int, tuple[int, int]],
    start_ln: int,
    start_col: int,
    fallback_end_col: int,
) -> dict[str, int]:
    """単文の source_span を論理行終端まで含めて生成する。"""
    end_pair: tuple[int, int] = merged_line_end.get(start_ln, (start_ln, fallback_end_col))
    end_ln: int = int(end_pair[0])
    end_col: int = int(end_pair[1])
    return _sh_span(start_ln, start_col, end_col, end_lineno=end_ln)


def _sh_push_stmt_with_trivia(
    stmts: list[dict[str, Any]],
    pending_leading_trivia: list[dict[str, Any]],
    pending_blank_count: int,
    stmt: dict[str, Any],
) -> int:
    """保留中 trivia を付与して文リストへ追加し、更新後 blank 数を返す。"""
    stmt_copy: dict[str, Any] = dict(stmt)
    if pending_blank_count > 0:
        pending_leading_trivia.append(_sh_make_trivia_blank(pending_blank_count))
        pending_blank_count = 0
    if len(pending_leading_trivia) > 0:
        stmt_copy["leading_trivia"] = list(pending_leading_trivia)
        comments = [x.get("text") for x in pending_leading_trivia if x.get("kind") == "comment" and isinstance(x.get("text"), str)]
        if len(comments) > 0:
            stmt_copy["leading_comments"] = comments
        pending_leading_trivia.clear()
    stmts.append(stmt_copy)
    return pending_blank_count


def _sh_collect_indented_block(
    body_lines: list[tuple[int, str]],
    start: int,
    parent_indent: int,
) -> tuple[list[tuple[int, str]], int]:
    """指定インデント配下のブロック行を収集する。"""
    out: list[tuple[int, str]] = []

    depth = 0
    mode = ""
    if 0 <= start - 1 < len(body_lines):
        prev_txt = body_lines[start - 1][1]
        depth, mode = _sh_scan_logical_line_state(prev_txt, 0, "")

    j = start
    while j < len(body_lines):
        n_no, n_ln = body_lines[j]
        if n_ln.strip() == "":
            if mode in {"'''", '"""'} or depth > 0:
                out.append((n_no, n_ln))
                depth, mode = _sh_scan_logical_line_state(n_ln, depth, mode)
                j += 1
                continue
            t = j + 1
            while t < len(body_lines) and body_lines[t][1].strip() == "":
                t += 1
            if t >= len(body_lines):
                break
            t_ln = body_lines[t][1]
            t_indent = len(t_ln) - len(t_ln.lstrip(" "))
            if t_indent <= parent_indent:
                # Blank lines right before dedent/elif/else should not pin j on
                # the blank line; advance to the next logical statement.
                j = t
                break
            out.append((n_no, n_ln))
            j += 1
            continue
        n_indent = len(n_ln) - len(n_ln.lstrip(" "))
        if n_indent <= parent_indent and not (mode in {"'''", '"""'} or depth > 0):
            break
        out.append((n_no, n_ln))
        depth, mode = _sh_scan_logical_line_state(n_ln, depth, mode)
        j += 1
    return out, j


def _sh_split_top_level_assign(text: str) -> tuple[str, str] | None:
    """トップレベルの `=` を 1 つだけ持つ代入式を分割する。"""
    depth = 0
    in_str = ""
    in_str_len = 0
    esc = False
    skip = 0
    for i, ch in enumerate(text):
        if skip > 0:
            skip -= 1
            continue
        if in_str != "":
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                if in_str_len == 3 and i + 2 < len(text) and text[i : i + 3] == (in_str + in_str + in_str):
                    skip = 2
                else:
                    in_str = ""
                    in_str_len = 0
            continue
        if i + 2 < len(text) and text[i : i + 3] in {"'''", '"""'}:
            in_str = text[i]
            in_str_len = 3
            skip = 2
            continue
        if ch in {"'", '"'}:
            in_str = ch
            in_str_len = 1
            continue
        if ch == "#":
            break
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == "=" and depth == 0:
            prev = text[i - 1] if i - 1 >= 0 else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if prev in {"!", "<", ">", "="} or nxt == "=":
                continue
            lhs = text[:i].strip()
            rhs = text[i + 1 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
    return None


def _sh_strip_inline_comment(text: str) -> str:
    """文字列リテラル外の末尾コメントを除去する。"""
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch == "#":
            return text[:i].rstrip()
    return text


def _sh_raise_if_trailing_stmt_terminator(text: str, *, line_no: int, line_text: str) -> None:
    """文末 `;` を検出したらエラーにする。"""
    out = text.rstrip()
    if out.endswith(";"):
        raise _make_east_build_error(
            kind="input_invalid",
            message="self_hosted parser does not accept statement terminator ';'",
            source_span=_sh_span(line_no, 0, len(line_text)),
            hint="Remove trailing ';' from the statement.",
        )


def _sh_split_top_level_from(text: str) -> tuple[str, str] | None:
    """トップレベルの `for ... in ...` を target/iter に分解する。"""
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if depth == 0 and text[i:].startswith(" from "):
            lhs = text[:i].strip()
            rhs = text[i + 6 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
    return None


def _sh_split_top_level_in(text: str) -> tuple[str, str] | None:
    """トップレベルの `target in iter` を target/iter に分割する。"""
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if depth == 0 and text[i:].startswith(" in "):
            lhs = text[:i].strip()
            rhs = text[i + 4 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
    return None


def _sh_split_top_level_colon(text: str) -> tuple[str, str] | None:
    """トップレベルの `head: tail` を 1 箇所分割する。"""
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(text):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if ch == ":" and depth == 0:
            lhs = text[:i].strip()
            rhs = text[i + 1 :].strip()
            if lhs != "" and rhs != "":
                return lhs, rhs
            return None
    return None


def _sh_split_top_level_as(text: str) -> tuple[str, str] | None:
    """トップレベルの `lhs as rhs` を分割する。"""
    pos = _sh_split_top_keyword(text, "as")
    if pos < 0:
        return None
    lhs = text[:pos].strip()
    rhs = text[pos + 2 :].strip()
    if lhs == "" or rhs == "":
        return None
    return lhs, rhs


def _sh_parse_except_clause(header_text: str) -> tuple[str, str | None] | None:
    """`except <Type> [as <name>]:` を手書きパースする。"""
    raw = header_text.strip()
    if not raw.startswith("except") or not raw.endswith(":"):
        return None
    inner = raw[len("except") : -1].strip()
    if inner == "":
        return "Exception", None
    as_split = _sh_split_top_level_as(inner)
    if as_split is None:
        return inner, None
    ex_type_txt, ex_name_txt = as_split
    if ex_type_txt.strip() == "":
        return None
    if not _sh_is_identifier(ex_name_txt.strip()):
        return None
    return ex_type_txt.strip(), ex_name_txt.strip()


def _sh_parse_class_header_base_list(ln: str) -> tuple[str, list[str]] | None:
    """`class Name(...):` から class 名と基底リスト（0..n）を抽出する。"""
    s = ln.strip()
    if not s.startswith("class ") or not s.endswith(":"):
        return None
    head = s[len("class ") : -1].strip()
    if head == "":
        return None
    lp = head.find("(")
    if lp < 0:
        if not _sh_is_identifier(head):
            return None
        return head, []
    rp = head.rfind(")")
    if rp < 0 or rp < lp:
        return None
    if head[rp + 1 :].strip() != "":
        return None
    cls_name = head[:lp].strip()
    if not _sh_is_identifier(cls_name):
        return None
    base_expr = head[lp + 1 : rp].strip()
    bases = _sh_split_top_commas(base_expr)
    return cls_name, bases


def _sh_parse_class_header(ln: str) -> tuple[str, str] | None:
    """`class Name:` / `class Name(Base):` を簡易解析する。"""
    parsed = _sh_parse_class_header_base_list(ln)
    if parsed is None:
        return None
    cls_name, bases = parsed
    if len(bases) == 0:
        return cls_name, ""
    if len(bases) != 1:
        return None
    base_name = bases[0]
    if not _sh_is_identifier(base_name):
        return None
    return cls_name, base_name


def _sh_parse_if_tail(
    *,
    start_idx: int,
    parent_indent: int,
    body_lines: list[tuple[int, str]],
    name_types: dict[str, str],
    scope_label: str,
) -> tuple[list[dict[str, Any]], int]:
    """if/elif/else 連鎖の後続ブロックを再帰的に解析する。"""
    if start_idx >= len(body_lines):
        return [], start_idx
    idx = start_idx
    while idx < len(body_lines):
        t_no, t_ln = body_lines[idx]
        t_indent = len(t_ln) - len(t_ln.lstrip(" "))
        if t_indent != parent_indent:
            return [], idx
        t_s = _sh_strip_inline_comment(t_ln.strip())
        _sh_raise_if_trailing_stmt_terminator(t_s, line_no=t_no, line_text=t_ln)
        if t_s == "":
            idx += 1
            continue
        break
    if idx >= len(body_lines):
        return [], idx
    t_no, t_ln = body_lines[idx]
    t_indent = len(t_ln) - len(t_ln.lstrip(" "))
    t_s = _sh_strip_inline_comment(t_ln.strip())
    if t_indent != parent_indent:
        return [], idx
    if t_s == "else:":
        else_block, k2 = _sh_collect_indented_block(body_lines, idx + 1, parent_indent)
        if len(else_block) == 0:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"else body is missing in '{scope_label}'",
                source_span=_sh_span(t_no, 0, len(t_ln)),
                hint="Add indented else-body.",
            )
        return _sh_parse_stmt_block(else_block, name_types=dict(name_types), scope_label=scope_label), k2
    if t_s.startswith("elif ") and t_s.endswith(":"):
        cond_txt2 = t_s[len("elif ") : -1].strip()
        cond_col2 = t_ln.find(cond_txt2)
        cond_expr2 = _sh_parse_expr_lowered(cond_txt2, ln_no=t_no, col=cond_col2, name_types=dict(name_types))
        elif_block, k2 = _sh_collect_indented_block(body_lines, idx + 1, parent_indent)
        if len(elif_block) == 0:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"elif body is missing in '{scope_label}'",
                source_span=_sh_span(t_no, 0, len(t_ln)),
                hint="Add indented elif-body.",
            )
        nested_orelse, k3 = _sh_parse_if_tail(
            start_idx=k2,
            parent_indent=parent_indent,
            body_lines=body_lines,
            name_types=dict(name_types),
            scope_label=scope_label,
        )
        return [
            _sh_make_if_stmt(
                _sh_block_end_span(body_lines, t_no, t_ln.find("elif "), len(t_ln), k3),
                cond_expr2,
                _sh_parse_stmt_block(elif_block, name_types=dict(name_types), scope_label=scope_label),
                orelse=nested_orelse,
            )
        ], k3
    return [], idx


def _sh_extract_leading_docstring(stmts: list[dict[str, Any]]) -> tuple[str | None, list[dict[str, Any]]]:
    """先頭文が docstring の場合に抽出し、残り文リストを返す。"""
    if len(stmts) == 0:
        return None, stmts
    first = stmts[0]
    if not isinstance(first, dict) or first.get("kind") != "Expr":
        return None, stmts
    val = first.get("value")
    if not isinstance(val, dict) or val.get("kind") != "Constant":
        return None, stmts
    s = val.get("value")
    if not isinstance(s, str):
        return None, stmts
    return s, stmts[1:]


def _sh_collect_yield_value_types(stmts: list[dict[str, Any]]) -> list[str]:
    """文リストから yield 値型を再帰収集する（入れ子関数/クラスは除外）。"""
    out: list[str] = []
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind == "Yield":
            val = st.get("value")
            if isinstance(val, dict):
                t_val = val.get("resolved_type", "unknown")
                if isinstance(t_val, str) and t_val != "":
                    out.append(t_val)
                else:
                    out.append("unknown")
            else:
                out.append("None")
            continue
        if kind in {"FunctionDef", "ClassDef"}:
            continue
        if kind in {"If", "While", "For", "ForRange"}:
            body_obj: Any = st.get("body")
            body_list: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_yield_value_types(body_list))
            orelse_obj: Any = st.get("orelse")
            orelse_list: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_yield_value_types(orelse_list))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body_list = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_yield_value_types(body_list))
            orelse_obj = st.get("orelse")
            orelse_list = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_yield_value_types(orelse_list))
            final_obj = st.get("finalbody")
            final_list = final_obj if isinstance(final_obj, list) else []
            out.extend(_sh_collect_yield_value_types(final_list))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for h in handlers:
                if not isinstance(h, dict):
                    continue
                h_body_obj: Any = h.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.extend(_sh_collect_yield_value_types(h_body))
    return out


def _sh_collect_return_value_types(stmts: list[dict[str, Any]]) -> list[str]:
    """文リストから `return <expr>` の戻り値型を再帰収集する（入れ子関数/クラスは除外）。"""
    out: list[str] = []
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind == "Return":
            val = st.get("value")
            if not isinstance(val, dict):
                continue
            t_val_obj: Any = val.get("resolved_type")
            t_val = str(t_val_obj) if isinstance(t_val_obj, str) else "unknown"
            out.append(t_val if t_val != "" else "unknown")
            continue
        if kind in {"FunctionDef", "ClassDef"}:
            continue
        if kind in {"If", "While", "For", "ForRange"}:
            body_obj: Any = st.get("body")
            body_list: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_return_value_types(body_list))
            orelse_obj: Any = st.get("orelse")
            orelse_list: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_return_value_types(orelse_list))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body_list = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_return_value_types(body_list))
            orelse_obj = st.get("orelse")
            orelse_list = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_return_value_types(orelse_list))
            final_obj = st.get("finalbody")
            final_list = final_obj if isinstance(final_obj, list) else []
            out.extend(_sh_collect_return_value_types(final_list))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for h in handlers:
                if not isinstance(h, dict):
                    continue
                h_body_obj: Any = h.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.extend(_sh_collect_return_value_types(h_body))
    return out


def _sh_infer_return_type_for_untyped_def(declared_ret: str, stmts: list[dict[str, Any]]) -> str:
    """戻り注釈なし（`None`）関数に対し `return <expr>` から戻り型を推定する。"""
    if declared_ret != "None":
        return declared_ret
    ret_types = _sh_collect_return_value_types(stmts)
    if len(ret_types) == 0:
        return declared_ret
    picked = ""
    for rt in ret_types:
        t = rt if rt != "" else "unknown"
        if t == "None":
            continue
        if picked == "":
            picked = t
            continue
        if picked == t:
            continue
        if picked == "unknown" or t == "unknown":
            picked = "unknown"
            continue
        picked = "Any"
        break
    if picked == "":
        return declared_ret
    return picked


def _sh_collect_store_name_ids(target: Any, out: set[str]) -> None:
    """代入ターゲットから Name 識別子を再帰収集する。"""
    if isinstance(target, dict):
        kind = str(target.get("kind", ""))
        if kind == "Name":
            name = target.get("id")
            if isinstance(name, str) and name != "":
                out.add(name)
            return
        if kind == "Starred":
            _sh_collect_store_name_ids(target.get("value"), out)
            return
        if kind in {"Tuple", "List"}:
            elems_obj: Any = target.get("elements")
            elems: list[Any] = elems_obj if isinstance(elems_obj, list) else []
            for elem in elems:
                _sh_collect_store_name_ids(elem, out)
            return
        return
    if isinstance(target, list):
        for item in target:
            _sh_collect_store_name_ids(item, out)


def _sh_collect_reassigned_names(stmts: list[dict[str, Any]]) -> set[str]:
    """文リストから再代入（再束縛）されたローカル名を収集する。"""
    out: set[str] = set()
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind in {"FunctionDef", "ClassDef"}:
            # 入れ子スコープ内の代入は外側関数引数の再代入に含めない。
            continue
        if kind in {"Assign", "AnnAssign", "AugAssign"}:
            _sh_collect_store_name_ids(st.get("target"), out)
            continue
        if kind == "Swap":
            _sh_collect_store_name_ids(st.get("left"), out)
            _sh_collect_store_name_ids(st.get("right"), out)
            continue
        if kind in {"For", "ForRange"}:
            _sh_collect_store_name_ids(st.get("target"), out)
            body_obj: Any = st.get("body")
            body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj: Any = st.get("orelse")
            orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            continue
        if kind in {"If", "While"}:
            body_obj = st.get("body")
            body = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj = st.get("orelse")
            orelse = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj = st.get("orelse")
            orelse = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            final_obj = st.get("finalbody")
            finalbody = final_obj if isinstance(final_obj, list) else []
            out.update(_sh_collect_reassigned_names(finalbody))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                h_name = handler.get("name")
                if isinstance(h_name, str) and h_name != "":
                    out.add(h_name)
                h_body_obj: Any = handler.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.update(_sh_collect_reassigned_names(h_body))
    return out


def _sh_build_arg_usage_map(
    arg_order: list[str],
    arg_types: dict[str, str],
    fn_stmts: list[dict[str, Any]],
) -> dict[str, str]:
    """関数本文の代入状況から `arg_usage` を構築する。"""
    usage: dict[str, str] = {}
    for arg_name in arg_types.keys():
        usage[arg_name] = "readonly"
    for arg_name in arg_order:
        usage[arg_name] = "readonly"

    reassigned = _sh_collect_reassigned_names(fn_stmts)
    for arg_name in arg_types.keys():
        if arg_name in reassigned:
            usage[arg_name] = "reassigned"
    for arg_name in arg_order:
        if arg_name in reassigned:
            usage[arg_name] = "reassigned"
    return usage


def _sh_make_generator_return_type(declared_ret: str, yield_types: list[str]) -> tuple[str, str]:
    """yield 検出時の関数戻り型（list[...]）と要素型を決定する。"""
    elem = "unknown"
    if declared_ret != "" and declared_ret != "None":
        elem = declared_ret
    for yt in yield_types:
        if yt in {"", "unknown", "None"}:
            continue
        if elem == "unknown":
            elem = yt
            continue
        if elem != yt:
            elem = "Any"
            break
    return "list[" + elem + "]", elem


def _sh_append_import_binding(
    *,
    import_bindings: list[dict[str, Any]],
    import_binding_names: set[str],
    module_id: str,
    export_name: str,
    local_name: str,
    binding_kind: str,
    source_file: str,
    source_line: int,
) -> None:
    """import 情報の正本 `ImportBinding` を追加する。"""
    if local_name in import_binding_names:
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"duplicate import binding: {local_name}",
            source_span=_sh_span(source_line, 0, 0),
            hint="Rename alias to avoid duplicate imported names.",
        )
    import_binding_names.add(local_name)
    import_bindings.append(
        _sh_make_import_binding(
            module_id=module_id,
            export_name=export_name,
            local_name=local_name,
            binding_kind=binding_kind,
            source_file=source_file,
            source_line=source_line,
        )
    )


def _sh_import_binding_fields(binding: dict[str, Any]) -> tuple[str, str, str, str, str, int]:
    """import binding raw dict から共通 field を取り出す。"""
    module_id_obj = binding.get("module_id")
    export_name_obj = binding.get("export_name")
    local_name_obj = binding.get("local_name")
    binding_kind_obj = binding.get("binding_kind")
    source_file_obj = binding.get("source_file")
    source_line_obj = binding.get("source_line")
    module_id = module_id_obj if isinstance(module_id_obj, str) else ""
    export_name = export_name_obj if isinstance(export_name_obj, str) else ""
    local_name = local_name_obj if isinstance(local_name_obj, str) else ""
    binding_kind = binding_kind_obj if isinstance(binding_kind_obj, str) else ""
    source_file = source_file_obj if isinstance(source_file_obj, str) else ""
    source_line = source_line_obj if isinstance(source_line_obj, int) else 0
    return module_id, export_name, local_name, binding_kind, source_file, source_line


def _sh_make_import_resolution_binding(binding: dict[str, Any]) -> dict[str, Any]:
    module_id, export_name, local_name, binding_kind, source_file, source_line = _sh_import_binding_fields(binding)
    out = _sh_make_import_binding(
        module_id=module_id,
        export_name=export_name,
        local_name=local_name,
        binding_kind=binding_kind,
        source_file=source_file,
        source_line=source_line,
    )
    resolution = resolve_import_binding_doc(
        module_id,
        export_name,
        binding_kind,
    )
    for key in (
        "source_module_id",
        "source_export_name",
        "source_binding_kind",
        "runtime_module_id",
        "runtime_group",
        "resolved_binding_kind",
        "runtime_symbol",
        "runtime_symbol_kind",
        "runtime_symbol_dispatch",
        "runtime_semantic_tag",
        "runtime_call_adapter_kind",
    ):
        value = resolution.get(key)
        if isinstance(value, str) and value != "":
            out[key] = value
    return out


def _sh_is_host_only_alias(local_name: str) -> bool:
    """`__name` 形式の host-only import alias か判定する。"""
    local = local_name.strip()
    return local.startswith("__") and local != ""


def _sh_register_import_symbol(local_name: str, module_id: str, export_name: str) -> None:
    """from-import で導入されたシンボル解決情報を式パーサ共有コンテキストへ反映する。"""
    local = local_name.strip()
    module = module_id.strip()
    export = export_name.strip()
    if local == "" or module == "" or export == "":
        return
    _SH_IMPORT_SYMBOLS[local] = _sh_make_import_symbol_binding(module, export)


def _sh_register_import_module(local_name: str, module_id: str) -> None:
    """import で導入されたモジュール別名を式パーサ共有コンテキストへ反映する。"""
    local = local_name.strip()
    module = module_id.strip()
    if local == "" or module == "":
        return
    _SH_IMPORT_MODULES[local] = module


class _ShExprParser:
    src: str
    line_no: int
    col_base: int
    name_types: dict[str, str]
    fn_return_types: dict[str, str]
    class_method_return_types: dict[str, dict[str, str]]
    class_base: dict[str, str | None]
    tokens: list[dict[str, Any]]
    pos: int

    def __init__(
        self,
        text: str,
        line_no: int,
        col_base: int,
        name_types: dict[str, str],
        fn_return_types: dict[str, str],
        class_method_return_types: dict[str, dict[str, str]] = {},
        class_base: dict[str, str | None] = {},
    ) -> None:
        """式パースに必要な入力と型環境を初期化する。"""
        self.src = text
        self.line_no = line_no
        self.col_base = col_base
        self.name_types = name_types
        self.fn_return_types = fn_return_types
        self.class_method_return_types = class_method_return_types
        self.class_base = class_base
        self.tokens: list[dict[str, Any]] = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> list[dict[str, Any]]:
        """式テキストを self-hosted 用トークン列へ変換する。"""
        out: list[dict[str, Any]] = []
        skip = 0
        text_len = len(text)
        for i, ch in enumerate(text):
            if skip > 0:
                skip -= 1
                continue
            if ch.isspace():
                continue
            # string literal prefixes: r"...", f"...", b"...", u"...", rf"...", fr"...", ...
            pref_len = 0
            if i + 1 < text_len:
                p1 = text[i]
                if p1 in _SH_STR_PREFIX_CHARS and text[i + 1] in {"'", '"'}:
                    pref_len = 1
                elif i + 2 < text_len:
                    p2 = text[i : i + 2]
                    if all(c in _SH_STR_PREFIX_CHARS for c in p2) and text[i + 2] in {"'", '"'}:
                        pref_len = 2
            if pref_len > 0:
                end = _sh_scan_string_token(text, i, i + pref_len, self.line_no, self.col_base)
                out.append(_sh_make_expr_token("STR", text[i:end], i, end))
                skip = end - i - 1
                continue
            if ch.isdigit():
                if ch == "0" and i + 2 < text_len and text[i + 1] in {"x", "X"}:
                    j = i + 2
                    while j < text_len and (text[j].isdigit() or text[j].lower() in {"a", "b", "c", "d", "e", "f"}):
                        j += 1
                    if j > i + 2:
                        out.append(_sh_make_expr_token("INT", text[i:j], i, j))
                        skip = j - i - 1
                        continue
                j = i + 1
                while j < text_len and text[j].isdigit():
                    j += 1
                has_float = False
                if j < text_len and text[j] == ".":
                    k = j + 1
                    while k < text_len and text[k].isdigit():
                        k += 1
                    if k > j + 1:
                        j = k
                        has_float = True
                if j < text_len and text[j] in {"e", "E"}:
                    k = j + 1
                    if k < text_len and text[k] in {"+", "-"}:
                        k += 1
                    d0 = k
                    while k < text_len and text[k].isdigit():
                        k += 1
                    if k > d0:
                        j = k
                        has_float = True
                if has_float:
                    out.append(_sh_make_expr_token("FLOAT", text[i:j], i, j))
                    skip = j - i - 1
                    continue
                out.append(_sh_make_expr_token("INT", text[i:j], i, j))
                skip = j - i - 1
                continue
            if ch.isalpha() or ch == "_":
                j = i + 1
                while j < text_len and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                out.append(_sh_make_expr_token("NAME", text[i:j], i, j))
                skip = j - i - 1
                continue
            if i + 2 < text_len and text[i : i + 3] in {"'''", '"""'}:
                end = _sh_scan_string_token(text, i, i, self.line_no, self.col_base)
                out.append(_sh_make_expr_token("STR", text[i:end], i, end))
                skip = end - i - 1
                continue
            if ch in {"'", '"'}:
                end = _sh_scan_string_token(text, i, i, self.line_no, self.col_base)
                out.append(_sh_make_expr_token("STR", text[i:end], i, end))
                skip = end - i - 1
                continue
            if i + 1 < text_len and text[i : i + 2] in {"<=", ">=", "==", "!=", "//", "<<", ">>", "**"}:
                out.append(_sh_make_expr_token(text[i : i + 2], text[i : i + 2], i, i + 2))
                skip = 1
                continue
            if ch in {"<", ">"}:
                out.append(_sh_make_expr_token(ch, ch, i, i + 1))
                continue
            if ch in {"+", "-", "*", "/", "%", "&", "|", "^", "(", ")", ",", ".", "[", "]", ":", "=", "{", "}"}:
                out.append(_sh_make_expr_token(ch, ch, i, i + 1))
                continue
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"unsupported token '{ch}' in self_hosted parser",
                source_span=_sh_span(self.line_no, self.col_base + i, self.col_base + i + 1),
                hint="Extend tokenizer for this syntax.",
            )
        out.append(_sh_make_expr_token("EOF", "", len(text), len(text)))
        return out

    def _cur(self) -> dict[str, Any]:
        """現在トークンを返す。"""
        return self.tokens[self.pos]

    def _eat(self, kind: str | None = None) -> dict[str, Any]:
        """現在トークンを消費して返す。kind 指定時は一致を検証する。"""
        tok = self._cur()
        if kind is not None and tok["k"] != kind:
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"expected token {kind}, got {tok['k']}",
                source_span=_sh_span(self.line_no, self.col_base + tok["s"], self.col_base + tok["e"]),
                hint="Fix expression syntax for self_hosted parser.",
            )
        self.pos += 1
        return tok

    def _node_span(self, s: int, e: int) -> dict[str, int]:
        """式内相対位置をファイル基準の source_span へ変換する。"""
        return _sh_span(self.line_no, self.col_base + s, self.col_base + e)

    def _src_slice(self, s: int, e: int) -> str:
        """元ソースから該当区間の repr 用文字列を取り出す。"""
        return self.src[s:e].strip()

    def parse(self) -> dict[str, Any]:
        """式を最後まで解析し、EAST 式ノードを返す。"""
        node = self._parse_ifexp()
        self._eat("EOF")
        return node

    def _parse_lambda(self) -> dict[str, Any]:
        """lambda 式を解析する。lambda でなければ次順位へ委譲する。"""
        tok = self._cur()
        if not (tok["k"] == "NAME" and tok["v"] == "lambda"):
            return self._parse_or()
        lam_tok = self._eat("NAME")
        arg_entries: list[dict[str, Any]] = []
        seen_default = False
        while self._cur()["k"] != ":":
            if self._cur()["k"] == ",":
                self._eat(",")
                continue
            if self._cur()["k"] == "NAME":
                nm = str(self._eat("NAME")["v"])
                default_expr: dict[str, Any] | None = None
                if self._cur()["k"] == "=":
                    self._eat("=")
                    default_expr = self._parse_ifexp()
                    seen_default = True
                elif seen_default:
                    cur = self._cur()
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="lambda non-default parameter follows default parameter",
                        source_span=self._node_span(cur["s"], cur["e"]),
                        hint="Reorder lambda parameters so defaulted ones come last.",
                    )
                param_t = "unknown"
                if isinstance(default_expr, dict):
                    default_t = str(default_expr.get("resolved_type", "unknown"))
                    if default_t != "":
                        param_t = default_t
                arg_entries.append(_sh_make_lambda_arg_entry(nm, default_expr, param_t))
                continue
            cur = self._cur()
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message=f"unsupported lambda parameter token: {cur['k']}",
                source_span=self._node_span(cur["s"], cur["e"]),
                hint="Use `lambda x, y=default: expr` form (annotations are not supported).",
            )
        self._eat(":")
        bak: dict[str, str] = {}
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            if nm == "":
                continue
            bak[nm] = self.name_types.get(nm, "")
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            self.name_types[nm] = param_t
        body = self._parse_ifexp()
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            if nm == "":
                continue
            old = bak.get(nm, "")
            if old == "":
                self.name_types.pop(nm, None)
            else:
                self.name_types[nm] = old
        s = lam_tok["s"]
        e = int(body["source_span"]["end_col"]) - self.col_base
        body_t = str(body.get("resolved_type", "unknown"))
        ret_t = body_t if body_t != "" else "unknown"
        param_types: list[str] = []
        for ent in arg_entries:
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            param_types.append(param_t)
        params = ",".join(param_types)
        callable_t = f"callable[{params}->{ret_t}]"
        args: list[dict[str, Any]] = []
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            default_expr = ent.get("default")
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            args.append(
                _sh_make_arg_node(
                    nm,
                    annotation=None,
                    resolved_type=param_t,
                    default=default_expr if isinstance(default_expr, dict) else None,
                )
            )
        return _sh_make_lambda_expr(
            self._node_span(s, e),
            args,
            body,
            return_type=ret_t,
            resolved_type=callable_t,
            repr_text=self._src_slice(s, e),
        )

    def _callable_return_type(self, t: str) -> str:
        """`callable[...]` 型文字列から戻り型だけを抽出する。"""
        if not (t.startswith("callable[") and t.endswith("]")):
            return "unknown"
        core = t[len("callable[") : -1]
        p = core.rfind("->")
        if p < 0:
            return "unknown"
        out = core[p + 2 :].strip()
        return out if out != "" else "unknown"

    def _parse_ifexp(self) -> dict[str, Any]:
        """条件式 `a if cond else b` を解析する。"""
        body = self._parse_lambda()
        if self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
            self._eat("NAME")
            test = self._parse_lambda()
            else_tok = self._eat("NAME")
            if else_tok["v"] != "else":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="expected 'else' in conditional expression",
                    source_span=self._node_span(else_tok["s"], else_tok["e"]),
                    hint="Use `a if cond else b` syntax.",
                )
            orelse = self._parse_ifexp()
            s = int(body["source_span"]["col"]) - self.col_base
            e = int(orelse["source_span"]["end_col"]) - self.col_base
            return _sh_make_ifexp_expr(
                self._node_span(s, e),
                test,
                body,
                orelse,
                repr_text=self._src_slice(s, e),
            )
        return body

    def _parse_or(self) -> dict[str, Any]:
        """論理和（or）式を解析する。"""
        node = self._parse_and()
        values = [node]
        while self._cur()["k"] == "NAME" and self._cur()["v"] == "or":
            self._eat("NAME")
            values.append(self._parse_and())
        if len(values) == 1:
            return node
        s = int(values[0]["source_span"]["col"]) - self.col_base
        e = int(values[-1]["source_span"]["end_col"]) - self.col_base
        return _sh_make_boolop_expr(self._node_span(s, e), "Or", values, repr_text=self._src_slice(s, e))

    def _parse_and(self) -> dict[str, Any]:
        """論理積（and）式を解析する。"""
        node = self._parse_not()
        values = [node]
        while self._cur()["k"] == "NAME" and self._cur()["v"] == "and":
            self._eat("NAME")
            values.append(self._parse_not())
        if len(values) == 1:
            return node
        s = int(values[0]["source_span"]["col"]) - self.col_base
        e = int(values[-1]["source_span"]["end_col"]) - self.col_base
        return _sh_make_boolop_expr(self._node_span(s, e), "And", values, repr_text=self._src_slice(s, e))

    def _parse_not(self) -> dict[str, Any]:
        """単項 not を解析する。"""
        tok = self._cur()
        if tok["k"] == "NAME" and tok["v"] == "not":
            self._eat("NAME")
            operand = self._parse_not()
            s = tok["s"]
            e = int(operand["source_span"]["end_col"]) - self.col_base
            return _sh_make_unaryop_expr(
                self._node_span(s, e),
                "Not",
                operand,
                resolved_type="bool",
                repr_text=self._src_slice(s, e),
            )
        return self._parse_compare()

    def _parse_compare(self) -> dict[str, Any]:
        """比較演算（連鎖比較含む）を解析する。"""
        node = self._parse_bitor()
        cmp_map = {"<": "Lt", "<=": "LtE", ">": "Gt", ">=": "GtE", "==": "Eq", "!=": "NotEq"}
        ops: list[str] = []
        comparators: list[dict[str, Any]] = []
        while True:
            if self._cur()["k"] in cmp_map:
                tok = self._eat()
                ops.append(cmp_map[tok["k"]])
                comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "in":
                self._eat("NAME")
                ops.append("In")
                comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "is":
                self._eat("NAME")
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "not":
                    self._eat("NAME")
                    ops.append("IsNot")
                    comparators.append(self._parse_bitor())
                else:
                    ops.append("Is")
                    comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "not":
                pos = self.pos
                self._eat("NAME")
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "in":
                    self._eat("NAME")
                    ops.append("NotIn")
                    comparators.append(self._parse_bitor())
                    continue
                self.pos = pos
            break
        if len(ops) == 0:
            return node
        start_col = int(node["source_span"]["col"]) - self.col_base
        end_col = int(comparators[-1]["source_span"]["end_col"]) - self.col_base
        return _sh_make_compare_expr(
            self._node_span(start_col, end_col),
            node,
            ops,
            comparators,
            repr_text=self._src_slice(start_col, end_col),
        )

    def _parse_bitor(self) -> dict[str, Any]:
        """ビット OR を解析する。"""
        node = self._parse_bitxor()
        while self._cur()["k"] == "|":
            op_tok = self._eat()
            right = self._parse_bitxor()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_bitxor(self) -> dict[str, Any]:
        """ビット XOR を解析する。"""
        node = self._parse_bitand()
        while self._cur()["k"] == "^":
            op_tok = self._eat()
            right = self._parse_bitand()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_bitand(self) -> dict[str, Any]:
        """ビット AND を解析する。"""
        node = self._parse_shift()
        while self._cur()["k"] == "&":
            op_tok = self._eat()
            right = self._parse_shift()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_shift(self) -> dict[str, Any]:
        """シフト演算を解析する。"""
        node = self._parse_addsub()
        while self._cur()["k"] in {"<<", ">>"}:
            op_tok = self._eat()
            right = self._parse_addsub()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_addsub(self) -> dict[str, Any]:
        """加減算を解析する。"""
        node = self._parse_muldiv()
        while self._cur()["k"] in {"+", "-"}:
            op_tok = self._eat()
            right = self._parse_muldiv()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_muldiv(self) -> dict[str, Any]:
        """乗除算（`* / // %`）を解析する。"""
        node = self._parse_unary()
        while self._cur()["k"] in {"*", "/", "//", "%"}:
            op_tok = self._eat()
            right = self._parse_unary()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_power(self) -> dict[str, Any]:
        """べき乗（`**`）を右結合で解析する。"""
        node = self._parse_postfix()
        if self._cur()["k"] == "**":
            op_tok = self._eat("**")
            right = self._parse_unary()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_unary(self) -> dict[str, Any]:
        """単項演算（`+` / `-`）を解析する。"""
        if self._cur()["k"] in {"+", "-"}:
            tok = self._eat()
            operand = self._parse_unary()
            s = tok["s"]
            e = int(operand["source_span"]["end_col"]) - self.col_base
            out_t = str(operand.get("resolved_type", "unknown"))
            return _sh_make_unaryop_expr(
                self._node_span(s, e),
                "USub" if tok["k"] == "-" else "UAdd",
                operand,
                resolved_type=out_t if out_t in {"int64", "float64"} else "unknown",
                repr_text=self._src_slice(s, e),
            )
        return self._parse_power()

    def _lookup_method_return(self, cls_name: str, method: str) -> str:
        """クラス継承を辿ってメソッド戻り型を解決する。"""
        cur: str = cls_name
        while True:
            methods: dict[str, str] = {}
            if cur in self.class_method_return_types:
                methods = self.class_method_return_types[cur]
            if method in methods:
                value_obj: Any = methods[method]
                if isinstance(value_obj, str):
                    return value_obj
                return str(value_obj)
            next_cur_obj: Any = None
            if cur in self.class_base:
                next_cur_obj = self.class_base[cur]
            if not isinstance(next_cur_obj, str):
                break
            cur = next_cur_obj
        return "unknown"

    def _lookup_builtin_method_return(self, cls_name: str, method: str) -> str:
        """既知の組み込み型メソッドの戻り型を補助的に解決する。"""
        methods: dict[str, str] = {}
        if cls_name == "str":
            methods = {
                "strip": "str",
                "lstrip": "str",
                "rstrip": "str",
                "upper": "str",
                "lower": "str",
                "capitalize": "str",
                "split": "list[str]",
                "splitlines": "list[str]",
            }
        return methods.get(method, "unknown")

    def _infer_attr_call_return_type(self, owner: dict[str, Any] | None, attr: str) -> str:
        """属性呼び出しの戻り型を owner type から推定する。"""
        if not isinstance(owner, dict):
            return "unknown"
        owner_t = self._owner_expr_resolved_type(owner)
        if owner_t == "unknown":
            return "unknown"
        if owner_t == "PyFile" and attr in {"close", "write"}:
            return "None"
        call_ret = self._lookup_method_return(owner_t, attr)
        if call_ret == "unknown":
            call_ret = self._lookup_builtin_method_return(owner_t, attr)
        stdlib_method_ret = lookup_stdlib_method_return_type(owner_t, attr)
        if stdlib_method_ret != "":
            return stdlib_method_ret
        return call_ret

    def _resolve_named_call_declared_return_type(
        self,
        *,
        fn_name: str,
    ) -> str:
        """named-call の declared fallback 戻り型を helper へ寄せる。"""
        if fn_name in self.fn_return_types:
            return self.fn_return_types[fn_name]
        if fn_name in self.class_method_return_types:
            return fn_name
        return self._callable_return_type(str(self.name_types.get(fn_name, "unknown")))

    def _resolve_named_call_return_state(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> tuple[str, str]:
        """named-call の imported/declaration return state を helper へ寄せる。"""
        stdlib_imported_ret = (
            lookup_stdlib_imported_symbol_return_type(fn_name, _SH_IMPORT_SYMBOLS)
            if fn_name != ""
            else ""
        )
        call_ret = _sh_infer_known_name_call_return_type(
            fn_name,
            args,
            stdlib_imported_ret,
        )
        declared_ret = self._resolve_named_call_declared_return_type(
            fn_name=fn_name,
        )
        return call_ret, declared_ret

    def _infer_named_call_return_type(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> str:
        """Name callee の戻り型推論を helper へ寄せる。"""
        call_ret, declared_ret = self._resolve_named_call_return_state(
            fn_name=fn_name,
            args=args,
        )
        if call_ret != "":
            return call_ret
        return declared_ret

    def _infer_call_expr_return_type(
        self,
        callee: dict[str, Any] | None,
        args: list[dict[str, Any]],
    ) -> tuple[str, str]:
        """呼び出し式の戻り型と name-callee 名を推定する。"""
        if not isinstance(callee, dict):
            return "unknown", ""
        kind = str(callee.get("kind", ""))
        fn_name = ""
        if kind == "Name":
            fn_name = str(callee.get("id", ""))
            return self._infer_named_call_return_type(fn_name=fn_name, args=args), fn_name
        if kind == "Attribute":
            owner = callee.get("value")
            attr = str(callee.get("attr", ""))
            return self._infer_attr_call_return_type(
                owner if isinstance(owner, dict) else None,
                attr,
            ), fn_name
        if kind == "Lambda":
            return str(callee.get("return_type", "unknown")), fn_name
        return "unknown", fn_name

    def _lookup_attr_expr_metadata(
        self,
        owner_expr: dict[str, Any] | None,
        owner_type: str,
        attr_name: str,
    ) -> dict[str, str]:
        """属性アクセスの型と runtime metadata lookup を共有 helper へ寄せる。"""
        attr_t = "unknown"
        if (
            isinstance(owner_expr, dict)
            and owner_expr.get("kind") == "Name"
            and owner_expr.get("id") == "self"
        ):
            maybe_field_t = self.name_types.get(attr_name)
            if isinstance(maybe_field_t, str) and maybe_field_t != "":
                attr_t = maybe_field_t
        runtime_call = ""
        semantic_tag = ""
        module_id = ""
        runtime_symbol = ""
        std_attr_t = lookup_stdlib_attribute_type(owner_type, attr_name)
        if std_attr_t != "":
            attr_t = std_attr_t
            runtime_call = lookup_stdlib_method_runtime_call(owner_type, attr_name)
            semantic_tag = lookup_stdlib_method_semantic_tag(attr_name)
            if runtime_call != "":
                module_id, runtime_symbol = lookup_stdlib_method_runtime_binding(owner_type, attr_name)
        noncpp_module_id, noncpp_runtime_call = _sh_lookup_noncpp_attr_runtime_call(owner_expr, attr_name)
        return {
            "resolved_type": attr_t,
            "runtime_call": runtime_call,
            "semantic_tag": semantic_tag,
            "module_id": module_id,
            "runtime_symbol": runtime_symbol,
            "noncpp_module_id": noncpp_module_id,
            "noncpp_runtime_call": noncpp_runtime_call,
        }

    def _split_generic_types(self, s: str) -> list[str]:
        """ジェネリック型引数をトップレベルカンマで分割する。"""
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out

    def _split_union_types(self, s: str) -> list[str]:
        """Union 型引数をトップレベル `|` で分割する。"""
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "|" and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out

    def _is_forbidden_object_receiver_type(self, t: str) -> bool:
        """object レシーバ禁止ルールに該当する型か判定する。"""
        s = t.strip()
        if s in {"object", "Any", "any"}:
            return True
        if "|" in s:
            parts = self._split_union_types(s)
            return any(p in {"object", "Any", "any"} for p in parts if p != "None")
        return False

    def _is_forbidden_dynamic_helper_type(self, t: str) -> bool:
        """decode-first helper に直接渡してはいけない動的型か判定する。"""
        s = t.strip()
        if s in {"object", "Any", "any"}:
            return True
        if "|" in s:
            parts = self._split_union_types(s)
            return any(p in {"object", "Any", "any"} for p in parts if p != "None")
        return False

    def _guard_dynamic_helper_receiver(self, helper_name: str, owner_t: str, source_span: dict[str, int]) -> None:
        """dynamic helper の receiver が decode-first 契約に違反していないか検査する。"""
        if not self._is_forbidden_dynamic_helper_type(owner_t):
            return
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"{helper_name}() does not accept object/Any receivers under decode-first constraints",
            source_span=source_span,
            hint=f"Decode JSON values to a concrete type before calling {helper_name}().",
        )

    def _guard_dynamic_helper_args(
        self,
        helper_name: str,
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> None:
        """dynamic helper に object/Any 引数が直接渡っていないか検査する。"""
        for arg in args:
            if not isinstance(arg, dict):
                continue
            arg_t = str(arg.get("resolved_type", "unknown")).strip()
            if arg_t == "":
                arg_t = "unknown"
            if self._is_forbidden_dynamic_helper_type(arg_t):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"{helper_name}() does not accept object/Any values under decode-first constraints",
                    source_span=source_span,
                    hint=f"Decode JSON values to a concrete type before calling {helper_name}().",
                )

    def _parse_call_arg_entry(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional/keyword 分岐を parser helper へ寄せる。"""
        save_pos, name_tok, is_keyword = self._resolve_call_arg_entry_state()
        return self._apply_call_arg_entry_state(
            save_pos=save_pos,
            name_tok=name_tok,
            is_keyword=is_keyword,
        )

    def _resolve_call_arg_entry_state(
        self,
    ) -> tuple[int | None, dict[str, Any] | None, bool]:
        """call argument 1件分の token/state resolve を helper へ寄せる。"""
        if self._cur()["k"] != "NAME":
            return None, None, False
        save_pos = self.pos
        name_tok = self._eat("NAME")
        return save_pos, name_tok, self._cur()["k"] == "="

    def _apply_call_arg_entry_state(
        self,
        *,
        save_pos: int | None,
        name_tok: dict[str, Any] | None,
        is_keyword: bool,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional/keyword apply を helper へ寄せる。"""
        if is_keyword and name_tok is not None:
            return self._apply_keyword_call_arg_entry(
                name_tok=name_tok,
            )
        return self._apply_positional_call_arg_entry(
            save_pos=save_pos,
        )

    def _apply_keyword_call_arg_entry(
        self,
        *,
        name_tok: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の keyword apply を helper へ寄せる。"""
        self._eat("=")
        kw_val = self._parse_ifexp()
        return None, _sh_make_keyword_arg(str(name_tok["v"]), kw_val)

    def _apply_positional_call_arg_entry(
        self,
        *,
        save_pos: int | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """call argument 1件分の positional apply を helper へ寄せる。"""
        if save_pos is not None:
            self.pos = save_pos
        return self._parse_call_arg_expr(), None

    def _apply_call_arg_entry(
        self,
        *,
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        arg_entry: dict[str, Any] | None,
        keyword_entry: dict[str, Any] | None,
    ) -> None:
        """call argument loop の positional/keyword append を helper へ寄せる。"""
        if keyword_entry is not None:
            keywords.append(keyword_entry)
            return
        if arg_entry is not None:
            args.append(arg_entry)

    def _advance_call_arg_loop(self) -> bool:
        """call argument loop の comma/terminator 制御を helper へ寄せる。"""
        if self._cur()["k"] != ",":
            return False
        self._eat(",")
        return self._cur()["k"] != ")"

    def _parse_call_args(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Call expr の位置引数と keyword 引数を parser helper へ寄せる。"""
        args: list[dict[str, Any]] = []
        keywords: list[dict[str, Any]] = []
        if self._cur()["k"] == ")":
            return args, keywords
        while True:
            arg_entry, keyword_entry = self._parse_call_arg_entry()
            self._apply_call_arg_entry(
                args=args,
                keywords=keywords,
                arg_entry=arg_entry,
                keyword_entry=keyword_entry,
            )
            if not self._advance_call_arg_loop():
                break
        return args, keywords

    def _resolve_postfix_span_repr(
        self,
        *,
        owner_expr: dict[str, Any],
        end_tok: dict[str, Any],
    ) -> tuple[dict[str, int], str]:
        """postfix suffix 共通の source_span / repr 計算を helper へ寄せる。"""
        s = int(owner_expr["source_span"]["col"]) - self.col_base
        e = end_tok["e"]
        return self._node_span(s, e), self._src_slice(s, e)

    def _resolve_call_suffix_state(
        self,
        *,
        callee: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int], str]:
        """call suffix の token/state resolve を parser helper へ寄せる。"""
        args, keywords, rtok = self._resolve_call_suffix_token_state()
        source_span, repr_text = self._resolve_call_suffix_span_repr(
            callee=callee,
            end_tok=rtok,
        )
        return args, keywords, source_span, repr_text

    def _resolve_call_suffix_span_repr(
        self,
        *,
        callee: dict[str, Any],
        end_tok: dict[str, Any],
    ) -> tuple[dict[str, int], str]:
        """call suffix の postfix span/repr resolve を helper へ寄せる。"""
        return self._resolve_postfix_span_repr(
            owner_expr=callee,
            end_tok=end_tok,
        )

    def _resolve_call_suffix_token_state(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """call suffix の token-state resolve を parser helper へ寄せる。"""
        return self._consume_call_suffix_tokens()

    def _consume_call_suffix_open_token(self) -> dict[str, Any]:
        """call suffix の `(` open token consume を helper へ寄せる。"""
        return self._eat("(")

    def _consume_call_suffix_close_token(self) -> dict[str, Any]:
        """call suffix の `)` close token consume を helper へ寄せる。"""
        return self._eat(")")

    def _consume_call_suffix_tokens(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """call suffix の token consume を parser helper へ寄せる。"""
        self._consume_call_suffix_open_token()
        args, keywords = self._parse_call_args()
        rtok = self._consume_call_suffix_close_token()
        return args, keywords, rtok

    def _parse_call_suffix(self, *, callee: dict[str, Any]) -> dict[str, Any]:
        """`(` postfix 全体の token 消費と call annotation を parser helper へ寄せる。"""
        args, keywords, source_span, repr_text = self._resolve_call_suffix_state(
            callee=callee,
        )
        return self._apply_call_suffix_state(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_call_suffix_state(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """call suffix の apply を parser helper へ寄せる。"""
        return self._annotate_call_expr(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _guard_named_call_args(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> None:
        """decode-first 制約がある named-call 引数検査を helper へ寄せる。"""
        if fn_name in {"sum", "zip", "sorted", "min", "max"}:
            self._guard_dynamic_helper_args(
                helper_name=fn_name,
                args=args,
                source_span=source_span,
            )

    def _apply_callee_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        callee: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
        callee_kind: str,
    ) -> dict[str, Any]:
        """callee kind ごとの call annotation 適用を helper へ寄せる。"""
        if callee_kind == "named":
            return self._apply_named_callee_call_annotation(
                payload,
                fn_name=fn_name,
                args=args,
            )
        if callee_kind == "attr":
            return self._apply_attr_callee_call_annotation(
                payload,
                callee=callee,
            )
        return payload

    def _apply_named_callee_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """named callee-call apply を helper へ寄せる。"""
        return self._annotate_named_call_expr(
            payload,
            fn_name=fn_name,
            args=args,
        )

    def _apply_attr_callee_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        callee: dict[str, Any],
    ) -> dict[str, Any]:
        """attr callee-call apply を helper へ寄せる。"""
        return self._annotate_attr_call_expr(
            payload,
            callee=callee,
        )

    def _resolve_callee_call_annotation_kind(
        self,
        *,
        callee: dict[str, Any],
        fn_name: str,
    ) -> str:
        """callee kind ごとの call annotation 分類を helper へ寄せる。"""
        if fn_name != "":
            return "named"
        if callee.get("kind") == "Attribute":
            return "attr"
        return ""

    def _resolve_callee_call_annotation_state(
        self,
        *,
        callee: dict[str, Any],
        fn_name: str,
    ) -> str:
        """callee-call の kind resolve を annotation-state helper へ寄せる。"""
        return self._resolve_callee_call_annotation_kind(
            callee=callee,
            fn_name=fn_name,
        )

    def _annotate_callee_call_expr(
        self,
        payload: dict[str, Any],
        *,
        callee: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """callee kind ごとの call annotation dispatch を helper へ寄せる。"""
        callee_kind = self._resolve_callee_call_annotation_state(
            callee=callee,
            fn_name=fn_name,
        )
        return self._apply_callee_call_annotation(
            payload,
            callee=callee,
            fn_name=fn_name,
            args=args,
            callee_kind=callee_kind,
        )

    def _resolve_call_expr_annotation_state(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        source_span: dict[str, int],
    ) -> tuple[str, str]:
        """call annotation 前段の return-type 推論と guard を helper へ寄せる。"""
        call_ret, fn_name = self._infer_call_expr_return_type(callee, args)
        self._guard_named_call_args(
            fn_name=fn_name,
            args=args,
            source_span=source_span,
        )
        return call_ret, fn_name

    def _build_call_expr_payload(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
        call_ret: str,
    ) -> dict[str, Any]:
        """Call expr payload 組み立てを helper へ寄せる。"""
        return _sh_make_call_expr(
            source_span,
            callee,
            args,
            keywords,
            resolved_type=call_ret,
            repr_text=repr_text,
        )

    def _apply_call_expr_annotation(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
        call_ret: str,
        fn_name: str,
    ) -> dict[str, Any]:
        """Call expr annotation 適用を helper へ寄せる。"""
        payload = self._build_call_expr_payload(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
            call_ret=call_ret,
        )
        return self._annotate_callee_call_expr(
            payload,
            callee=callee,
            fn_name=fn_name,
            args=args,
        )

    def _annotate_call_expr(
        self,
        *,
        callee: dict[str, Any],
        args: list[dict[str, Any]],
        keywords: list[dict[str, Any]],
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Call expr の payload 構築と annotation を parser helper へ寄せる。"""
        call_ret, fn_name = self._resolve_call_expr_annotation_state(
            callee=callee,
            args=args,
            source_span=source_span,
        )
        return self._apply_call_expr_annotation(
            callee=callee,
            args=args,
            keywords=keywords,
            source_span=source_span,
            repr_text=repr_text,
            call_ret=call_ret,
            fn_name=fn_name,
        )

    def _apply_named_call_dispatch(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
        dispatch_kind: str,
    ) -> dict[str, Any]:
        """named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "builtin":
            return self._apply_builtin_named_call_annotation(
                payload,
                fn_name=fn_name,
                args=args,
                call_dispatch=call_dispatch,
            )
        if dispatch_kind == "runtime":
            return self._apply_runtime_named_call_annotation(
                payload,
                fn_name=fn_name,
                call_dispatch=call_dispatch,
            )
        return payload

    def _coalesce_optional_annotation_payload(
        self,
        *,
        payload: dict[str, Any],
        annotated_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """optional annotation payload の fallback を helper へ寄せる。"""
        return payload if annotated_payload is None else annotated_payload

    def _apply_builtin_named_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
    ) -> dict[str, Any]:
        """builtin named-call apply を helper へ寄せる。"""
        builtin_payload = self._annotate_builtin_named_call_expr(
            payload,
            fn_name=fn_name,
            args=args,
            call_dispatch=call_dispatch,
        )
        return self._coalesce_optional_annotation_payload(
            payload=payload,
            annotated_payload=builtin_payload,
        )

    def _apply_runtime_named_call_annotation(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> dict[str, Any]:
        """runtime named-call apply を helper へ寄せる。"""
        runtime_payload = self._annotate_runtime_named_call_expr(
            payload,
            fn_name=fn_name,
            call_dispatch=call_dispatch,
        )
        return self._coalesce_optional_annotation_payload(
            payload=payload,
            annotated_payload=runtime_payload,
        )

    def _resolve_named_call_dispatch(
        self,
        *,
        fn_name: str,
    ) -> dict[str, str]:
        """named-call dispatch lookup を helper へ寄せる。"""
        return _sh_lookup_named_call_dispatch(fn_name)

    def _resolve_named_call_dispatch_kind(
        self,
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> str:
        """named-call dispatch の builtin/runtime 分類を helper へ寄せる。"""
        if self._resolve_builtin_named_call_kind(fn_name=fn_name) != "":
            return "builtin"
        dispatch_kind, *_ = self._resolve_runtime_named_call_annotation(
            call_dispatch=call_dispatch,
        )
        if dispatch_kind != "":
            return "runtime"
        return ""

    def _resolve_named_call_annotation_state(
        self,
        *,
        fn_name: str,
    ) -> tuple[dict[str, str], str]:
        """named-call の dispatch resolve を annotation-state helper へ寄せる。"""
        call_dispatch = self._resolve_named_call_dispatch(
            fn_name=fn_name,
        )
        dispatch_kind = self._resolve_named_call_dispatch_kind(
            fn_name=fn_name,
            call_dispatch=call_dispatch,
        )
        return call_dispatch, dispatch_kind

    def _annotate_named_call_expr(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Name callee の metadata annotation を shared helper へ寄せる。"""
        call_dispatch, dispatch_kind = self._resolve_named_call_annotation_state(
            fn_name=fn_name,
        )
        return self._apply_named_call_dispatch(
            payload,
            fn_name=fn_name,
            args=args,
            call_dispatch=call_dispatch,
            dispatch_kind=dispatch_kind,
        )

    def _should_use_truthy_runtime_for_bool_ctor(
        self,
        *,
        args: list[dict[str, Any]],
    ) -> bool:
        """bool(...) が truthy runtime helper を使うべきか判定する。"""
        if len(args) != 1:
            return False
        arg0 = args[0]
        if not isinstance(arg0, dict):
            return False
        arg0_t = str(arg0.get("resolved_type", "unknown"))
        return self._is_forbidden_object_receiver_type(arg0_t)

    def _resolve_builtin_named_call_semantic_tag(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> str:
        """builtin named-call dispatch の semantic tag unpack を helper へ寄せる。"""
        return str(call_dispatch.get("builtin_semantic_tag", ""))

    def _resolve_builtin_named_call_kind(self, *, fn_name: str) -> str:
        """builtin named-call の分類決定を helper へ寄せる。"""
        if fn_name in {"print", "len", "range", "zip", "str"}:
            return "fixed_runtime"
        if fn_name in {"int", "float", "bool"}:
            return "scalar_ctor"
        if fn_name in {"min", "max"}:
            return "minmax"
        if fn_name in {"Exception", "RuntimeError"}:
            return "exception_ctor"
        if fn_name == "open":
            return "open"
        if fn_name in {"iter", "next", "reversed"}:
            return "iterator"
        if fn_name == "enumerate":
            return "enumerate"
        if fn_name in {"any", "all"}:
            return "anyall"
        if fn_name in {"ord", "chr"}:
            return "ordchr"
        if fn_name in {"bytes", "bytearray", "list", "set", "dict"}:
            return "collection_ctor"
        if fn_name in {"isinstance", "issubclass"}:
            return "type_predicate"
        return ""

    def _resolve_builtin_named_call_dispatch(
        self,
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str]:
        """builtin named-call の semantic tag / kind 解決を helper へ寄せる。"""
        semantic_tag = self._resolve_builtin_named_call_semantic_tag(
            call_dispatch=call_dispatch,
        )
        dispatch_kind = self._resolve_builtin_named_call_kind(
            fn_name=fn_name,
        )
        return semantic_tag, dispatch_kind

    def _resolve_builtin_named_call_annotation_state(
        self,
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, bool, str]:
        """builtin named-call の annotation 前段 state を helper へ寄せる。"""
        semantic_tag, dispatch_kind = self._resolve_builtin_named_call_dispatch(
            fn_name=fn_name,
            call_dispatch=call_dispatch,
        )
        use_truthy_runtime = self._resolve_builtin_named_call_truthy_state(
            fn_name=fn_name,
            dispatch_kind=dispatch_kind,
            args=args,
        )
        iter_element_type = self._resolve_builtin_named_call_iter_element_type(
            dispatch_kind=dispatch_kind,
            args=args,
        )
        return semantic_tag, dispatch_kind, use_truthy_runtime, iter_element_type

    def _resolve_builtin_named_call_truthy_state(
        self,
        *,
        fn_name: str,
        dispatch_kind: str,
        args: list[dict[str, Any]],
    ) -> bool:
        """builtin named-call の truthy-runtime 特例を helper へ寄せる。"""
        return (
            dispatch_kind == "scalar_ctor"
            and fn_name == "bool"
            and self._should_use_truthy_runtime_for_bool_ctor(args=args)
        )

    def _resolve_builtin_named_call_iter_element_type(
        self,
        *,
        dispatch_kind: str,
        args: list[dict[str, Any]],
    ) -> str:
        """builtin named-call の enumerate item 型推論を helper へ寄せる。"""
        if dispatch_kind == "enumerate":
            return _sh_infer_enumerate_item_type(args)
        return "unknown"

    def _apply_fixed_runtime_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """fixed-runtime builtin apply を helper へ寄せる。"""
        return _sh_annotate_fixed_runtime_builtin_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_scalar_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
        use_truthy_runtime: bool,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """scalar ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_scalar_ctor_call_expr(
            payload,
            fn_name=fn_name,
            arg_count=len(args),
            use_truthy_runtime=use_truthy_runtime,
            semantic_tag=semantic_tag,
        )

    def _apply_minmax_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """min/max builtin apply を helper へ寄せる。"""
        return _sh_annotate_minmax_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_exception_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """exception ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_exception_ctor_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_open_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        semantic_tag: str,
    ) -> dict[str, Any]:
        """open builtin apply を helper へ寄せる。"""
        return _sh_annotate_open_call_expr(
            payload,
            semantic_tag=semantic_tag,
        )

    def _apply_iterator_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """iterator builtin apply を helper へ寄せる。"""
        return _sh_annotate_iterator_builtin_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_enumerate_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        iter_element_type: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """enumerate builtin apply を helper へ寄せる。"""
        return _sh_annotate_enumerate_call_expr(
            payload,
            iter_element_type=iter_element_type,
            semantic_tag=semantic_tag,
        )

    def _apply_anyall_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """any/all builtin apply を helper へ寄せる。"""
        return _sh_annotate_anyall_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_ordchr_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """ord/chr builtin apply を helper へ寄せる。"""
        return _sh_annotate_ordchr_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_collection_ctor_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """collection ctor builtin apply を helper へ寄せる。"""
        return _sh_annotate_collection_ctor_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_type_predicate_builtin_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """type predicate builtin apply を helper へ寄せる。"""
        return _sh_annotate_type_predicate_call_expr(
            payload,
            fn_name=fn_name,
            semantic_tag=semantic_tag,
        )

    def _apply_builtin_named_call_dispatch(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        args: list[dict[str, Any]],
        dispatch_kind: str,
        semantic_tag: str,
        use_truthy_runtime: bool,
        iter_element_type: str,
    ) -> dict[str, Any] | None:
        """builtin named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "fixed_runtime":
            return self._apply_fixed_runtime_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "scalar_ctor":
            return self._apply_scalar_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                args=args,
                use_truthy_runtime=use_truthy_runtime,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "minmax":
            return self._apply_minmax_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "exception_ctor":
            return self._apply_exception_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "open":
            return self._apply_open_builtin_named_call_annotation(
                payload=payload,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "iterator":
            return self._apply_iterator_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "enumerate":
            return self._apply_enumerate_builtin_named_call_annotation(
                payload=payload,
                iter_element_type=iter_element_type,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "anyall":
            return self._apply_anyall_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "ordchr":
            return self._apply_ordchr_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "collection_ctor":
            return self._apply_collection_ctor_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "type_predicate":
            return self._apply_type_predicate_builtin_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                semantic_tag=semantic_tag,
            )
        return None

    def _annotate_builtin_named_call_expr(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        args: list[dict[str, Any]],
        call_dispatch: dict[str, str],
    ) -> dict[str, Any] | None:
        """builtin named-call の annotation dispatch を parser helper へ寄せる。"""
        semantic_tag, dispatch_kind, use_truthy_runtime, iter_element_type = (
            self._resolve_builtin_named_call_annotation_state(
                fn_name=fn_name,
                args=args,
                call_dispatch=call_dispatch,
            )
        )
        return self._apply_builtin_named_call_dispatch(
            payload=payload,
            fn_name=fn_name,
            args=args,
            dispatch_kind=dispatch_kind,
            semantic_tag=semantic_tag,
            use_truthy_runtime=use_truthy_runtime,
            iter_element_type=iter_element_type,
        )

    def _resolve_runtime_named_call_dispatch(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, str, str, str]:
        """runtime named-call dispatch field unpack を helper へ寄せる。"""
        stdlib_fn_runtime_call = str(call_dispatch.get("stdlib_fn_runtime_call", ""))
        stdlib_symbol_runtime_call = str(call_dispatch.get("stdlib_symbol_runtime_call", ""))
        noncpp_symbol_runtime_call = str(call_dispatch.get("noncpp_symbol_runtime_call", ""))
        stdlib_fn_semantic_tag = str(call_dispatch.get("stdlib_fn_semantic_tag", ""))
        stdlib_symbol_semantic_tag = str(call_dispatch.get("stdlib_symbol_semantic_tag", ""))
        return (
            stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call,
            stdlib_fn_semantic_tag,
            stdlib_symbol_semantic_tag,
        )

    def _resolve_runtime_named_call_kind(
        self,
        *,
        stdlib_fn_runtime_call: str,
        stdlib_symbol_runtime_call: str,
        noncpp_symbol_runtime_call: str,
    ) -> str:
        """runtime named-call の分類決定を helper へ寄せる。"""
        if stdlib_fn_runtime_call != "":
            return "stdlib_function"
        if stdlib_symbol_runtime_call != "":
            return "stdlib_symbol"
        if noncpp_symbol_runtime_call != "":
            return "noncpp_symbol"
        return ""

    def _resolve_runtime_named_call_annotation(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, str, str, str, str]:
        """runtime named-call の unpack と kind 判定を helper へ寄せる。"""
        (
            stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call,
            stdlib_fn_semantic_tag,
            stdlib_symbol_semantic_tag,
        ) = self._resolve_runtime_named_call_dispatch(
            call_dispatch=call_dispatch,
        )
        dispatch_kind = self._resolve_runtime_named_call_kind(
            stdlib_fn_runtime_call=stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call=stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call=noncpp_symbol_runtime_call,
        )
        return (
            dispatch_kind,
            stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call,
            stdlib_fn_semantic_tag,
            stdlib_symbol_semantic_tag,
        )

    def _resolve_runtime_named_call_apply_state(
        self,
        *,
        call_dispatch: dict[str, str],
    ) -> tuple[str, str, str]:
        """runtime named-call apply 用の state を helper へ寄せる。"""
        (
            dispatch_kind,
            stdlib_fn_runtime_call,
            stdlib_symbol_runtime_call,
            noncpp_symbol_runtime_call,
            stdlib_fn_semantic_tag,
            stdlib_symbol_semantic_tag,
        ) = self._resolve_runtime_named_call_annotation(
            call_dispatch=call_dispatch,
        )
        if dispatch_kind == "stdlib_function":
            return dispatch_kind, stdlib_fn_runtime_call, stdlib_fn_semantic_tag
        if dispatch_kind == "stdlib_symbol":
            return dispatch_kind, stdlib_symbol_runtime_call, stdlib_symbol_semantic_tag
        if dispatch_kind == "noncpp_symbol":
            return dispatch_kind, noncpp_symbol_runtime_call, ""
        return "", "", ""

    def _apply_stdlib_function_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """stdlib function named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_stdlib_function_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
            semantic_tag=semantic_tag,
        )

    def _apply_stdlib_symbol_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any]:
        """stdlib symbol named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_stdlib_symbol_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
            semantic_tag=semantic_tag,
        )

    def _apply_noncpp_symbol_named_call_annotation(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        runtime_call: str,
    ) -> dict[str, Any]:
        """non-C++ symbol named-call annotation 適用を helper へ寄せる。"""
        return _sh_annotate_noncpp_symbol_call_expr(
            payload,
            fn_name=fn_name,
            runtime_call=runtime_call,
        )

    def _apply_runtime_named_call_dispatch(
        self,
        *,
        payload: dict[str, Any],
        fn_name: str,
        dispatch_kind: str,
        runtime_call: str,
        semantic_tag: str,
    ) -> dict[str, Any] | None:
        """runtime named-call dispatch の annotation 適用を helper へ寄せる。"""
        if dispatch_kind == "stdlib_function":
            return self._apply_stdlib_function_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "stdlib_symbol":
            return self._apply_stdlib_symbol_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )
        if dispatch_kind == "noncpp_symbol":
            return self._apply_noncpp_symbol_named_call_annotation(
                payload=payload,
                fn_name=fn_name,
                runtime_call=runtime_call,
            )
        return None

    def _annotate_runtime_named_call_expr(
        self,
        payload: dict[str, Any],
        *,
        fn_name: str,
        call_dispatch: dict[str, str],
    ) -> dict[str, Any] | None:
        """stdlib / non-C++ named-call dispatch を parser helper へ寄せる。"""
        dispatch_kind, runtime_call, semantic_tag = self._resolve_runtime_named_call_apply_state(
            call_dispatch=call_dispatch,
        )
        return self._apply_runtime_named_call_dispatch(
            payload=payload,
            fn_name=fn_name,
            dispatch_kind=dispatch_kind,
            runtime_call=runtime_call,
            semantic_tag=semantic_tag,
        )

    def _owner_expr_resolved_type(self, owner_expr: dict[str, Any]) -> str:
        """owner expr から resolved_type を取る処理を helper へ寄せる。"""
        owner_t = str(owner_expr.get("resolved_type", "unknown"))
        if str(owner_expr.get("kind", "")) == "Name":
            owner_t = self.name_types.get(str(owner_expr.get("id", "")), owner_t)
        return owner_t

    def _resolve_attr_expr_owner_state(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
    ) -> str:
        """Attribute access の owner 型判定と preflight guard を helper へ寄せる。"""
        owner_t = self._owner_expr_resolved_type(owner_expr)
        if attr_name in {"keys", "items", "values"}:
            self._guard_dynamic_helper_receiver(
                helper_name=attr_name,
                owner_t=owner_t,
                source_span=source_span,
            )
        if self._is_forbidden_object_receiver_type(owner_t):
            raise _make_east_build_error(
                kind="unsupported_syntax",
                message="object receiver attribute/method access is forbidden by language constraints",
                source_span=source_span,
                hint="Cast or assign to a concrete type before attribute/method access.",
            )
        return owner_t

    def _resolve_attr_callee(
        self,
        *,
        callee: dict[str, Any],
        source_span: dict[str, int],
    ) -> tuple[dict[str, Any] | None, str, str]:
        """Attribute callee の owner / type / attr 抽出を helper へ寄せる。"""
        attr = str(callee.get("attr", ""))
        owner = callee.get("value")
        owner_expr = owner if isinstance(owner, dict) else None
        owner_t = (
            self._resolve_attr_expr_owner_state(
                owner_expr=owner_expr,
                attr_name=attr,
                source_span=source_span,
            )
            if owner_expr is not None
            else "unknown"
        )
        return owner_expr, owner_t, attr

    def _payload_source_span(self, payload: dict[str, Any]) -> dict[str, int]:
        """payload から source_span dict を正規化して取り出す。"""
        source_span = payload.get("source_span")
        return source_span if isinstance(source_span, dict) else {}

    def _resolve_attr_call_annotation_state(
        self,
        *,
        payload: dict[str, Any],
        callee: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str, str]:
        """Attribute call の source span normalize と callee resolve を helper へ寄せる。"""
        return self._resolve_attr_callee(
            callee=callee,
            source_span=self._payload_source_span(payload),
        )

    def _apply_noncpp_attr_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        attr: str,
    ) -> None:
        """non-C++ attr-call annotation 適用を helper へ寄せる。"""
        _sh_annotate_noncpp_attr_call_expr(
            payload,
            owner_expr=owner_expr,
            attr_name=attr,
        )

    def _apply_runtime_method_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        owner_t: str,
        attr: str,
    ) -> None:
        """runtime method-call annotation 適用を helper へ寄せる。"""
        _sh_annotate_runtime_method_call_expr(
            payload,
            owner_type=owner_t,
            attr=attr,
            runtime_owner=owner_expr,
        )

    def _apply_attr_call_expr_annotation(
        self,
        *,
        payload: dict[str, Any],
        owner_expr: dict[str, Any] | None,
        owner_t: str,
        attr: str,
    ) -> dict[str, Any]:
        """Attribute callee annotation の適用を helper へ寄せる。"""
        self._apply_noncpp_attr_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            attr=attr,
        )
        self._apply_runtime_method_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            owner_t=owner_t,
            attr=attr,
        )
        return payload

    def _annotate_attr_call_expr(
        self,
        payload: dict[str, Any],
        *,
        callee: dict[str, Any],
    ) -> dict[str, Any]:
        """Attribute callee の annotation を shared parser helper へ寄せる。"""
        owner_expr, owner_t, attr = self._resolve_attr_call_annotation_state(
            payload=payload,
            callee=callee,
        )
        return self._apply_attr_call_expr_annotation(
            payload=payload,
            owner_expr=owner_expr,
            owner_t=owner_t,
            attr=attr,
        )

    def _parse_attr_suffix(self, *, owner_expr: dict[str, Any]) -> dict[str, Any]:
        """Attribute suffix の token 消費を parser helper へ寄せる。"""
        attr_name, source_span, repr_text = self._resolve_attr_suffix_state(
            owner_expr=owner_expr,
        )
        return self._apply_attr_suffix_state(
            owner_expr=owner_expr,
            attr_name=attr_name,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_attr_suffix_state(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Attribute suffix の apply を parser helper へ寄せる。"""
        return self._annotate_attr_expr(
            owner_expr=owner_expr,
            attr_name=attr_name,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _consume_attr_suffix_dot_token(self) -> dict[str, Any]:
        """Attribute suffix の `.` token consume を helper へ寄せる。"""
        return self._eat(".")

    def _resolve_attr_suffix_name_token(self) -> dict[str, Any]:
        """Attribute suffix の `.` + NAME consume を helper へ寄せる。"""
        self._consume_attr_suffix_dot_token()
        return self._consume_attr_suffix_name_token()

    def _consume_attr_suffix_name_token(self) -> dict[str, Any]:
        """Attribute suffix の `NAME` token consume を helper へ寄せる。"""
        return self._eat("NAME")

    def _resolve_attr_suffix_state(
        self,
        *,
        owner_expr: dict[str, Any],
    ) -> tuple[str, dict[str, int], str]:
        """Attribute suffix の token/state resolve を helper へ寄せる。"""
        name_tok = self._resolve_attr_suffix_token_state()
        source_span, repr_text = self._resolve_attr_suffix_span_repr(
            owner_expr=owner_expr,
            end_tok=name_tok,
        )
        return str(name_tok["v"]), source_span, repr_text

    def _resolve_attr_suffix_token_state(self) -> dict[str, Any]:
        """Attribute suffix の token-state resolve を helper へ寄せる。"""
        return self._resolve_attr_suffix_name_token()

    def _resolve_attr_suffix_span_repr(
        self,
        *,
        owner_expr: dict[str, Any],
        end_tok: dict[str, Any],
    ) -> tuple[dict[str, int], str]:
        """Attribute suffix の postfix span/repr resolve を helper へ寄せる。"""
        return self._resolve_postfix_span_repr(
            owner_expr=owner_expr,
            end_tok=end_tok,
        )

    def _resolve_attr_expr_annotation(
        self,
        *,
        attr_meta: dict[str, Any],
    ) -> tuple[str, str, str, str, str, str, str]:
        """Attribute access metadata dict の field unpack を helper へ寄せる。"""
        resolved_type = str(attr_meta.get("resolved_type", "unknown"))
        attr_runtime_call = str(attr_meta.get("runtime_call", ""))
        attr_semantic_tag = str(attr_meta.get("semantic_tag", ""))
        attr_module_id = str(attr_meta.get("module_id", ""))
        attr_runtime_symbol = str(attr_meta.get("runtime_symbol", ""))
        noncpp_module_attr_runtime_call = str(attr_meta.get("noncpp_runtime_call", ""))
        noncpp_module_id = str(attr_meta.get("noncpp_module_id", ""))
        return (
            resolved_type,
            attr_runtime_call,
            attr_semantic_tag,
            attr_module_id,
            attr_runtime_symbol,
            noncpp_module_attr_runtime_call,
            noncpp_module_id,
        )

    def _resolve_attr_expr_metadata(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        attr_name: str,
    ) -> tuple[str, str, str, str, str, str, str]:
        """Attribute access metadata の lookup と unpack を helper へ寄せる。"""
        attr_meta = self._lookup_attr_expr_metadata(owner_expr, owner_t, attr_name)
        return self._resolve_attr_expr_annotation(
            attr_meta=attr_meta,
        )

    def _resolve_attr_expr_annotation_state(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
    ) -> tuple[str, str, str, str, str, str, str]:
        """Attribute access の owner-state と metadata resolve を helper へ寄せる。"""
        owner_t = self._resolve_attr_expr_owner_state(
            owner_expr=owner_expr,
            attr_name=attr_name,
            source_span=source_span,
        )
        (
            resolved_type,
            attr_runtime_call,
            attr_semantic_tag,
            attr_module_id,
            attr_runtime_symbol,
            noncpp_module_attr_runtime_call,
            noncpp_module_id,
        ) = self._resolve_attr_expr_metadata(
            owner_expr=owner_expr,
            owner_t=owner_t,
            attr_name=attr_name,
        )
        return (
            resolved_type,
            attr_runtime_call,
            attr_semantic_tag,
            attr_module_id,
            attr_runtime_symbol,
            noncpp_module_attr_runtime_call,
            noncpp_module_id,
        )

    def _build_attr_expr_payload(
        self,
        *,
        source_span: dict[str, int],
        owner_expr: dict[str, Any],
        attr_name: str,
        resolved_type: str,
        repr_text: str,
    ) -> dict[str, Any]:
        """Attribute access node 組み立てを helper へ寄せる。"""
        node = _sh_make_attribute_expr(
            source_span,
            owner_expr,
            attr_name,
            resolved_type=resolved_type,
            repr_text=repr_text,
        )
        return node

    def _apply_runtime_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        owner_expr: dict[str, Any],
        attr_runtime_call: str,
        attr_semantic_tag: str,
        attr_module_id: str,
        attr_runtime_symbol: str,
    ) -> None:
        """runtime attr annotation 適用を helper へ寄せる。"""
        if self._apply_runtime_call_attr_expr_annotation(
            node=node,
            owner_expr=owner_expr,
            attr_runtime_call=attr_runtime_call,
            attr_semantic_tag=attr_semantic_tag,
            attr_module_id=attr_module_id,
            attr_runtime_symbol=attr_runtime_symbol,
        ):
            return
        self._apply_runtime_semantic_attr_expr_annotation(
            node=node,
            attr_semantic_tag=attr_semantic_tag,
        )

    def _apply_runtime_call_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        owner_expr: dict[str, Any],
        attr_runtime_call: str,
        attr_semantic_tag: str,
        attr_module_id: str,
        attr_runtime_symbol: str,
    ) -> bool:
        """runtime-call attr annotation 適用を helper へ寄せる。"""
        if attr_runtime_call == "":
            return False
        _sh_annotate_runtime_attr_expr(
            node,
            runtime_call=attr_runtime_call,
            module_id=attr_module_id,
            runtime_symbol=attr_runtime_symbol,
            semantic_tag=attr_semantic_tag,
            runtime_owner=owner_expr,
        )
        return True

    def _apply_runtime_semantic_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        attr_semantic_tag: str,
    ) -> None:
        """semantic-tag fallback attr annotation 適用を helper へ寄せる。"""
        if attr_semantic_tag != "":
            node["semantic_tag"] = attr_semantic_tag

    def _apply_noncpp_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        attr_name: str,
        noncpp_module_attr_runtime_call: str,
        noncpp_module_id: str,
    ) -> None:
        """non-C++ attr annotation 適用を helper へ寄せる。"""
        if noncpp_module_attr_runtime_call != "":
            _sh_annotate_resolved_runtime_expr(
                node,
                runtime_call=noncpp_module_attr_runtime_call,
                runtime_source="module_attr",
                module_id=noncpp_module_id,
                runtime_symbol=attr_name,
            )

    def _apply_attr_expr_annotation(
        self,
        *,
        node: dict[str, Any],
        owner_expr: dict[str, Any],
        attr_name: str,
        attr_runtime_call: str,
        attr_semantic_tag: str,
        attr_module_id: str,
        attr_runtime_symbol: str,
        noncpp_module_attr_runtime_call: str,
        noncpp_module_id: str,
    ) -> dict[str, Any]:
        """Attribute access node への annotation 適用を helper へ寄せる。"""
        self._apply_runtime_attr_expr_annotation(
            node=node,
            owner_expr=owner_expr,
            attr_runtime_call=attr_runtime_call,
            attr_semantic_tag=attr_semantic_tag,
            attr_module_id=attr_module_id,
            attr_runtime_symbol=attr_runtime_symbol,
        )
        self._apply_noncpp_attr_expr_annotation(
            node=node,
            attr_name=attr_name,
            noncpp_module_attr_runtime_call=noncpp_module_attr_runtime_call,
            noncpp_module_id=noncpp_module_id,
        )
        return node

    def _annotate_attr_expr(
        self,
        *,
        owner_expr: dict[str, Any],
        attr_name: str,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Attribute access node の生成と annotation を parser helper へ寄せる。"""
        (
            resolved_type,
            attr_runtime_call,
            attr_semantic_tag,
            attr_module_id,
            attr_runtime_symbol,
            noncpp_module_attr_runtime_call,
            noncpp_module_id,
        ) = self._resolve_attr_expr_annotation_state(
            owner_expr=owner_expr,
            attr_name=attr_name,
            source_span=source_span,
        )
        node = self._build_attr_expr_payload(
            source_span=source_span,
            owner_expr=owner_expr,
            attr_name=attr_name,
            resolved_type=resolved_type,
            repr_text=repr_text,
        )
        return self._apply_attr_expr_annotation(
            node=node,
            owner_expr=owner_expr,
            attr_name=attr_name,
            attr_runtime_call=attr_runtime_call,
            attr_semantic_tag=attr_semantic_tag,
            attr_module_id=attr_module_id,
            attr_runtime_symbol=attr_runtime_symbol,
            noncpp_module_attr_runtime_call=noncpp_module_attr_runtime_call,
            noncpp_module_id=noncpp_module_id,
        )

    def _build_slice_subscript_expr(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """slice subscript node 組み立てを helper へ寄せる。"""
        return _sh_make_subscript_expr(
            source_span,
            owner_expr,
            _sh_make_slice_node(lower, upper),
            resolved_type=owner_t,
            repr_text=repr_text,
            lowered_kind="SliceExpr",
            lower=lower,
            upper=upper,
        )

    def _build_index_subscript_expr(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        index_expr: dict[str, Any],
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """index subscript node 組み立てを helper へ寄せる。"""
        return _sh_make_subscript_expr(
            source_span,
            owner_expr,
            index_expr,
            resolved_type=self._subscript_result_type(owner_t),
            repr_text=repr_text,
        )

    def _resolve_subscript_expr_annotation_state(
        self,
        *,
        owner_expr: dict[str, Any],
    ) -> str:
        """Subscript / slice の owner-type resolve を helper へ寄せる。"""
        return self._owner_expr_resolved_type(owner_expr)

    def _resolve_subscript_expr_build_kind(
        self,
        *,
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
    ) -> str:
        """Subscript / Slice の build 分岐を helper へ寄せる。"""
        if index_expr is None or lower is not None or upper is not None:
            return "slice"
        return "index"

    def _resolve_subscript_expr_apply_state(
        self,
        *,
        owner_expr: dict[str, Any],
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
    ) -> tuple[str, str]:
        """Subscript / Slice の annotation-state resolve を helper へ寄せる。"""
        owner_t = self._resolve_subscript_expr_annotation_state(
            owner_expr=owner_expr,
        )
        build_kind = self._resolve_subscript_expr_build_kind(
            index_expr=index_expr,
            lower=lower,
            upper=upper,
        )
        return owner_t, build_kind

    def _apply_slice_subscript_expr_build(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """slice subscript build apply を helper へ寄せる。"""
        return self._build_slice_subscript_expr(
            owner_expr=owner_expr,
            owner_t=owner_t,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_index_subscript_expr_build(
        self,
        *,
        owner_expr: dict[str, Any],
        owner_t: str,
        index_expr: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """index subscript build apply を helper へ寄せる。"""
        assert index_expr is not None
        return self._build_index_subscript_expr(
            owner_expr=owner_expr,
            owner_t=owner_t,
            index_expr=index_expr,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_subscript_expr_build(
        self,
        *,
        build_kind: str,
        owner_expr: dict[str, Any],
        owner_t: str,
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Subscript / Slice の build dispatch を helper へ寄せる。"""
        if build_kind == "slice":
            return self._apply_slice_subscript_expr_build(
                owner_expr=owner_expr,
                owner_t=owner_t,
                lower=lower,
                upper=upper,
                source_span=source_span,
                repr_text=repr_text,
            )
        return self._apply_index_subscript_expr_build(
            owner_expr=owner_expr,
            owner_t=owner_t,
            index_expr=index_expr,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _annotate_subscript_expr(
        self,
        *,
        owner_expr: dict[str, Any],
        index_expr: dict[str, Any] | None = None,
        lower: dict[str, Any] | None = None,
        upper: dict[str, Any] | None = None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Subscript / slice node の構築を parser helper へ寄せる。"""
        owner_t, build_kind = self._resolve_subscript_expr_apply_state(
            owner_expr=owner_expr,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
        )
        return self._apply_subscript_expr_build(
            build_kind=build_kind,
            owner_expr=owner_expr,
            owner_t=owner_t,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _parse_subscript_slice_tail(
        self,
        *,
        lower: dict[str, Any] | None,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript slice tail の `:` 以降 parse を helper へ寄せる。"""
        upper, rtok = self._resolve_subscript_slice_tail_state()
        return None, lower, upper, rtok

    def _resolve_subscript_slice_tail_state(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の token/state resolve を helper へ寄せる。"""
        return self._consume_subscript_slice_tail_tokens()

    def _resolve_subscript_slice_upper_expr_state(self) -> bool:
        """Subscript slice tail の upper expr state resolve を helper へ寄せる。"""
        return self._cur()["k"] == "]"

    def _parse_subscript_slice_upper_expr(self) -> dict[str, Any] | None:
        """Subscript slice tail の upper expr parse を helper へ寄せる。"""
        is_empty = self._resolve_subscript_slice_upper_expr_state()
        return self._apply_subscript_slice_upper_expr_state(is_empty=is_empty)

    def _apply_subscript_slice_upper_expr_state(
        self,
        *,
        is_empty: bool,
    ) -> dict[str, Any] | None:
        """Subscript slice tail の upper expr apply を helper へ寄せる。"""
        if is_empty:
            return None
        return self._parse_ifexp()

    def _consume_subscript_slice_tail_colon_token(self) -> dict[str, Any]:
        """Subscript slice tail の `:` token consume を helper へ寄せる。"""
        return self._eat(":")

    def _consume_subscript_slice_tail_close_token(self) -> dict[str, Any]:
        """Subscript slice tail の `]` token consume を helper へ寄せる。"""
        return self._eat("]")

    def _consume_subscript_slice_tail_tokens(
        self,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Subscript slice tail の token consume を helper へ寄せる。"""
        self._consume_subscript_slice_tail_colon_token()
        upper = self._parse_subscript_slice_upper_expr()
        rtok = self._consume_subscript_slice_tail_close_token()
        return upper, rtok

    def _parse_subscript_suffix_components(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript / slice suffix の component parse を helper へ寄せる。"""
        starts_with_slice = self._resolve_subscript_suffix_component_state()
        return self._apply_subscript_suffix_component_state(
            starts_with_slice=starts_with_slice,
        )

    def _resolve_subscript_suffix_component_state(self) -> bool:
        """Subscript suffix の component 先頭 state resolve を helper へ寄せる。"""
        return self._cur()["k"] == ":"

    def _apply_subscript_suffix_component_state(
        self,
        *,
        starts_with_slice: bool,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の component apply を helper へ寄せる。"""
        if starts_with_slice:
            return self._parse_subscript_slice_tail(lower=None)
        return self._parse_subscript_suffix_first_component()

    def _parse_subscript_suffix_first_component(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の first expr 側 parse を helper へ寄せる。"""
        first, is_slice = self._resolve_subscript_suffix_first_component_state()
        return self._apply_subscript_suffix_first_component_state(
            first=first,
            is_slice=is_slice,
        )

    def _resolve_subscript_suffix_first_component_state(
        self,
    ) -> tuple[dict[str, Any], bool]:
        """Subscript suffix の first expr 側 state resolve を helper へ寄せる。"""
        first = self._parse_ifexp()
        return first, self._cur()["k"] == ":"

    def _apply_subscript_suffix_first_component_state(
        self,
        *,
        first: dict[str, Any],
        is_slice: bool,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の first expr 側 apply を helper へ寄せる。"""
        if is_slice:
            return self._apply_subscript_slice_first_component(first=first)
        return self._apply_subscript_index_first_component(first=first)

    def _apply_subscript_slice_first_component(
        self,
        *,
        first: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の first expr 側 slice apply を helper へ寄せる。"""
        return self._parse_subscript_slice_tail(lower=first)

    def _apply_subscript_index_first_component(
        self,
        *,
        first: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript suffix の first expr 側 index apply を helper へ寄せる。"""
        return self._parse_subscript_index_tail(index_expr=first)

    def _parse_subscript_index_tail(
        self,
        *,
        index_expr: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript index tail の `]` close を helper へ寄せる。"""
        rtok = self._resolve_subscript_index_tail_state()
        return index_expr, None, None, rtok

    def _resolve_subscript_index_tail_state(self) -> dict[str, Any]:
        """Subscript index tail の close-token state resolve を helper へ寄せる。"""
        return self._consume_subscript_index_tail_close_token()

    def _consume_subscript_index_tail_close_token(self) -> dict[str, Any]:
        """Subscript index tail の `]` close token consume を helper へ寄せる。"""
        return self._eat("]")

    def _resolve_subscript_suffix_state(
        self,
        *,
        owner_expr: dict[str, Any],
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, int],
        str,
    ]:
        """Subscript / slice suffix の token/state resolve を helper へ寄せる。"""
        index_expr, lower, upper, rtok = self._resolve_subscript_suffix_token_state()
        source_span, repr_text = self._resolve_subscript_suffix_span_repr(
            owner_expr=owner_expr,
            end_tok=rtok,
        )
        return index_expr, lower, upper, source_span, repr_text

    def _resolve_subscript_suffix_span_repr(
        self,
        *,
        owner_expr: dict[str, Any],
        end_tok: dict[str, Any],
    ) -> tuple[dict[str, int], str]:
        """Subscript suffix の postfix span/repr resolve を helper へ寄せる。"""
        return self._resolve_postfix_span_repr(
            owner_expr=owner_expr,
            end_tok=end_tok,
        )

    def _consume_subscript_suffix_open_token(self) -> dict[str, Any]:
        """Subscript suffix の `[` open token consume を helper へ寄せる。"""
        return self._eat("[")

    def _consume_subscript_suffix_tokens(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript / slice suffix の token consume を helper へ寄せる。"""
        self._consume_subscript_suffix_open_token()
        return self._parse_subscript_suffix_components()

    def _resolve_subscript_suffix_token_state(
        self,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Subscript / slice suffix の token-state resolve を helper へ寄せる。"""
        return self._consume_subscript_suffix_tokens()

    def _parse_subscript_suffix(self, *, owner_expr: dict[str, Any]) -> dict[str, Any]:
        """Subscript / slice suffix の token 消費を parser helper へ寄せる。"""
        index_expr, lower, upper, source_span, repr_text = self._resolve_subscript_suffix_state(
            owner_expr=owner_expr,
        )
        return self._apply_subscript_suffix_state(
            owner_expr=owner_expr,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _apply_subscript_suffix_state(
        self,
        *,
        owner_expr: dict[str, Any],
        index_expr: dict[str, Any] | None,
        lower: dict[str, Any] | None,
        upper: dict[str, Any] | None,
        source_span: dict[str, int],
        repr_text: str,
    ) -> dict[str, Any]:
        """Subscript suffix の apply を helper へ寄せる。"""
        return self._annotate_subscript_expr(
            owner_expr=owner_expr,
            index_expr=index_expr,
            lower=lower,
            upper=upper,
            source_span=source_span,
            repr_text=repr_text,
        )

    def _parse_postfix_suffix(self, *, owner_expr: dict[str, Any]) -> dict[str, Any] | None:
        """postfix suffix dispatch を parser helper へ寄せる。"""
        tok_kind = str(self._cur()["k"])
        if tok_kind == ".":
            return self._parse_attr_suffix(owner_expr=owner_expr)
        if tok_kind == "(":
            return self._parse_call_suffix(callee=owner_expr)
        if tok_kind == "[":
            return self._parse_subscript_suffix(owner_expr=owner_expr)
        return None

    def _subscript_result_type(self, container_type: str) -> str:
        """添字アクセスの結果型をコンテナ型から推論する。"""
        if container_type.startswith("list[") and container_type.endswith("]"):
            inner = container_type[5:-1].strip()
            return inner if inner != "" else "unknown"
        if container_type.startswith("dict[") and container_type.endswith("]"):
            inner = self._split_generic_types(container_type[5:-1].strip())
            if len(inner) == 2 and inner[1] != "":
                return inner[1]
            return "unknown"
        if container_type == "str":
            return "str"
        if container_type in {"bytes", "bytearray"}:
            return "uint8"
        return "unknown"

    def _dict_stmt_list(self, raw: Any) -> list[dict[str, Any]]:
        """動的値から `list[dict]` を安全に取り出す。"""
        out: list[dict[str, Any]] = []
        if not isinstance(raw, list):
            return out
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
        return out

    def _node_kind_from_dict(self, node_dict: dict[str, Any]) -> str:
        """dict 化されたノードから kind を安全に文字列取得する。"""
        if not isinstance(node_dict, dict):
            return ""
        kind = node_dict.get("kind")
        if isinstance(kind, str):
            return kind.strip()
        if kind is None:
            return ""
        txt = str(kind).strip()
        return txt if txt != "" else ""

    def _iter_item_type(self, iter_expr: dict[str, Any] | None) -> str:
        """for 反復対象の要素型を推論する。"""
        if not isinstance(iter_expr, dict):
            return "unknown"
        t = str(iter_expr.get("resolved_type", "unknown"))
        if t.startswith("List[") and t.endswith("]"):
            t = "list[" + t[5:-1] + "]"
        if t.startswith("Set[") and t.endswith("]"):
            t = "set[" + t[4:-1] + "]"
        if t.startswith("Dict[") and t.endswith("]"):
            t = "dict[" + t[5:-1] + "]"
        if t == "range":
            return "int64"
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1].strip()
            return inner if inner != "" else "unknown"
        if t.startswith("set[") and t.endswith("]"):
            inner = t[4:-1].strip()
            return inner if inner != "" else "unknown"
        if t == "bytearray" or t == "bytes":
            return "uint8"
        if t == "str":
            return "str"
        return "unknown"

    def _parse_postfix(self) -> dict[str, Any]:
        """属性参照・呼び出し・添字・スライスなど後置構文を解析する。"""
        node = self._parse_primary()
        while True:
            next_node = self._parse_postfix_suffix(owner_expr=node)
            if next_node is None:
                return node
            node = next_node

    def _parse_comp_target(self) -> dict[str, Any]:
        """内包表現のターゲット（name / tuple）を解析する。"""
        if self._cur()["k"] == "NAME":
            first = self._eat("NAME")
            first_name = str(first["v"])
            first_t = self.name_types.get(first_name, "unknown")
            first_node = _sh_make_name_expr(
                self._node_span(first["s"], first["e"]),
                first_name,
                resolved_type=first_t,
            )
            if self._cur()["k"] != ",":
                return first_node
            elems: list[dict[str, Any]] = [first_node]
            last_e = first["e"]
            while self._cur()["k"] == ",":
                self._eat(",")
                if self._cur()["k"] != "NAME":
                    break
                nm_tok = self._eat("NAME")
                nm = str(nm_tok["v"])
                t = self.name_types.get(nm, "unknown")
                elems.append(_sh_make_name_expr(self._node_span(nm_tok["s"], nm_tok["e"]), nm, resolved_type=t))
                last_e = nm_tok["e"]
            return _sh_make_tuple_expr(
                self._node_span(first["s"], last_e),
                elems,
                repr_text=self._src_slice(first["s"], last_e),
            )
        if self._cur()["k"] == "(":
            l = self._eat("(")
            elems: list[dict[str, Any]] = []
            elems.append(self._parse_comp_target())
            while self._cur()["k"] == ",":
                self._eat(",")
                if self._cur()["k"] == ")":
                    break
                elems.append(self._parse_comp_target())
            r = self._eat(")")
            return _sh_make_tuple_expr(
                self._node_span(l["s"], r["e"]),
                elems,
                resolved_type="tuple[unknown]",
                repr_text=self._src_slice(l["s"], r["e"]),
            )
        tok = self._cur()
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="invalid comprehension target in call argument",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Use name or tuple target in generator expression.",
        )

    def _collect_and_bind_comp_target_types(
        self,
        target_expr: dict[str, Any],
        value_type: str,
        snapshots: dict[str, str],
    ) -> None:
        """内包ターゲットの各 Name へ一時的に型を設定する。"""
        kind = self._node_kind_from_dict(target_expr)
        if kind == "Name":
            nm = str(target_expr.get("id", "")).strip()
            if nm == "":
                return
            if nm not in snapshots:
                snapshots[nm] = str(self.name_types.get(nm, ""))
            target_expr["resolved_type"] = value_type
            self.name_types[nm] = value_type
            return

        if kind != "Tuple":
            return

        target_elements = self._dict_stmt_list(target_expr.get("elements"))
        elem_types: list[str] = []
        if isinstance(value_type, str) and value_type.startswith("tuple[") and value_type.endswith("]"):
            inner = value_type[6:-1].strip()
            if inner != "":
                elem_types = [p.strip() for p in _sh_split_top_commas(inner)]
        for idx, elem in enumerate(target_elements):
            if not isinstance(elem, dict):
                continue
            et = value_type
            if idx < len(elem_types):
                et0 = elem_types[idx]
                if et0 != "":
                    et = et0
            self._collect_and_bind_comp_target_types(elem, et, snapshots)

    def _restore_comp_target_types(self, snapshots: dict[str, str]) -> None:
        """内包ターゲット一時型束縛を復元する。"""
        for nm, old_t in snapshots.items():
            if old_t == "":
                self.name_types.pop(nm, None)
            else:
                self.name_types[nm] = old_t

    def _parse_call_arg_expr(self) -> dict[str, Any]:
        """呼び出し引数式を解析し、必要なら generator 引数へ lower する。"""
        first = self._parse_ifexp()
        if not (self._cur()["k"] == "NAME" and self._cur()["v"] == "for"):
            return first

        snapshots: dict[str, str] = {}
        generators: list[dict[str, Any]] = []
        first_norm = first
        end_node: Any = first

        def _reparse_expr(expr_node: dict[str, Any]) -> dict[str, Any]:
            expr_repr = expr_node.get("repr")
            if not isinstance(expr_repr, str) or expr_repr == "":
                return expr_node
            return _sh_parse_expr(
                expr_repr,
                line_no=self.line_no,
                col_base=int(expr_node.get("source_span", {}).get("col", self.col_base)),
                name_types=self.name_types,
                fn_return_types=self.fn_return_types,
                class_method_return_types=self.class_method_return_types,
                class_base=self.class_base,
            )

        while self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
            self._eat("NAME")
            target = self._parse_comp_target()
            in_tok = self._eat("NAME")
            if in_tok["v"] != "in":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="expected 'in' in generator expression",
                    source_span=self._node_span(in_tok["s"], in_tok["e"]),
                    hint="Use `for x in iterable` form.",
                )
            iter_expr = self._parse_or()
            if not isinstance(iter_expr, dict):
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="unsupported iterator expression in generator argument",
                    source_span=self._node_span(
                        int(iter_expr["source_span"]["col"]) if isinstance(iter_expr, dict) else self.col_base,
                        int(iter_expr["source_span"]["end_col"]) if isinstance(iter_expr, dict) else self.col_base + 1,
                    ),
                    hint="Use a resolvable iterable expression.",
                )

            conds: list[dict[str, Any]] = []
            while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                self._eat("NAME")
                conds.append(self._parse_or())
            conds_norm: list[dict[str, Any]] = list(conds)

            tgt_ty = self._iter_item_type(iter_expr)
            if tgt_ty != "unknown":
                self._collect_and_bind_comp_target_types(target, tgt_ty, snapshots)
                if len(generators) == 0:
                    first_norm = _reparse_expr(first)
                conds_norm = [_reparse_expr(cond) if isinstance(cond, dict) else cond for cond in conds]

            if len(conds_norm) > 0:
                end_node = conds_norm[-1]
            else:
                end_node = iter_expr

            generators.append(_sh_make_comp_generator(target, iter_expr, conds_norm))

        self._restore_comp_target_types(snapshots)
        s = int(first["source_span"]["col"]) - self.col_base
        if not isinstance(end_node, dict):
            return first
        e = int(end_node["source_span"]["end_col"]) - self.col_base
        return _sh_make_list_comp_expr(
            self._node_span(s, e),
            first_norm,
            generators,
            repr_text=self._src_slice(s, e),
            lowered_kind="GeneratorArg",
        )

    def _make_bin(self, left: dict[str, Any], op_sym: str, right: dict[str, Any]) -> dict[str, Any]:
        """二項演算ノードを構築し、数値昇格 cast も付与する。"""
        op_map = {
            "+": "Add",
            "-": "Sub",
            "*": "Mult",
            "**": "Pow",
            "/": "Div",
            "//": "FloorDiv",
            "%": "Mod",
            "&": "BitAnd",
            "|": "BitOr",
            "^": "BitXor",
            "<<": "LShift",
            ">>": "RShift",
        }
        lt = str(left.get("resolved_type", "unknown"))
        rt = str(right.get("resolved_type", "unknown"))
        casts: list[dict[str, Any]] = []
        if op_sym == "/":
            if is_stdlib_path_type(lt) and (rt == "str" or is_stdlib_path_type(rt)):
                out_t = "Path"
            elif (lt in INT_TYPES or lt in FLOAT_TYPES) and (rt in INT_TYPES or rt in FLOAT_TYPES):
                out_t = "float64"
                if lt in INT_TYPES:
                    casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
                if rt in INT_TYPES:
                    casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
            else:
                # object/unknown を数値に固定化しない。
                out_t = "unknown"
        elif op_sym == "//":
            out_t = "int64" if lt in {"int64", "unknown"} and rt in {"int64", "unknown"} else "float64"
        elif op_sym == "+" and (
            (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"})
            or (lt == "str" and rt == "str")
        ):
            out_t = "bytes" if (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"}) else "str"
        elif op_sym == "**" and lt in {"int64", "float64"} and rt in {"int64", "float64"}:
            out_t = "float64"
            if lt == "int64":
                casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
            if rt == "int64":
                casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
        elif lt == rt and lt in {"int64", "float64"}:
            out_t = lt
        elif lt in {"int64", "float64"} and rt in {"int64", "float64"}:
            out_t = "float64"
            if lt == "int64":
                casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
            if rt == "int64":
                casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
        elif op_sym in {"&", "|", "^", "<<", ">>"} and lt == "int64" and rt == "int64":
            out_t = "int64"
        else:
            out_t = "unknown"

        ls = int(left["source_span"]["col"]) - self.col_base
        rs = int(right["source_span"]["end_col"]) - self.col_base
        return _sh_make_binop_expr(
            self._node_span(ls, rs),
            left,
            op_map[op_sym],
            right,
            resolved_type=out_t,
            casts=casts,
            repr_text=self._src_slice(ls, rs),
        )

    def _parse_primary(self) -> dict[str, Any]:
        """リテラル・名前・括弧式などの primary 式を解析する。"""
        tok = self._cur()
        if tok["k"] == "INT":
            self._eat("INT")
            tok_v: str = str(tok["v"])
            if tok_v.startswith("0x") or tok_v.startswith("0X"):
                tok_value = int(tok_v[2:], 16)
            elif tok_v.startswith("0b") or tok_v.startswith("0B"):
                tok_value = int(tok_v[2:], 2)
            elif tok_v.startswith("0o") or tok_v.startswith("0O"):
                tok_value = int(tok_v[2:], 8)
            else:
                tok_value = int(tok_v)
            return _sh_make_constant_expr(
                self._node_span(tok["s"], tok["e"]),
                tok_value,
                resolved_type="int64",
                repr_text=str(tok["v"]),
            )
        if tok["k"] == "FLOAT":
            self._eat("FLOAT")
            return _sh_make_constant_expr(
                self._node_span(tok["s"], tok["e"]),
                float(tok["v"]),
                resolved_type="float64",
                repr_text=str(tok["v"]),
            )
        if tok["k"] == "STR":
            str_parts: list[dict[str, Any]] = [self._eat("STR")]
            while self._cur()["k"] == "STR":
                str_parts.append(self._eat("STR"))
            if len(str_parts) > 1:
                str_nodes = [
                    _sh_parse_expr(
                        part["v"],
                        line_no=self.line_no,
                        col_base=self.col_base + int(part["s"]),
                        name_types=self.name_types,
                        fn_return_types=self.fn_return_types,
                        class_method_return_types=self.class_method_return_types,
                        class_base=self.class_base,
                    )
                    for part in str_parts
                ]
                node = str_nodes[0]
                for str_rhs in str_nodes[1:]:
                    node = _sh_make_binop_expr(
                        self._node_span(str_parts[0]["s"], str_parts[-1]["e"]),
                        node,
                        "Add",
                        str_rhs,
                        resolved_type="str",
                        repr_text=self._src_slice(str_parts[0]["s"], str_parts[-1]["e"]),
                    )
                return node

            tok = str_parts[0]
            raw: str = tok["v"]
            # Support prefixed literals (f/r/b/u/rf/fr...) in expression parser.
            p = 0
            while p < len(raw) and raw[p] in "rRbBuUfF":
                p += 1
            prefix = raw[:p].lower()
            if p >= len(raw):
                p = 0

            is_triple = p + 2 < len(raw) and raw[p : p + 3] in {"'''", '"""'}
            if is_triple:
                body = raw[p + 3 : -3]
            else:
                body = raw[p + 1 : -1]

            if "f" in prefix:
                values: list[dict[str, Any]] = []
                is_raw = "r" in prefix

                i = 0
                while i < len(body):
                    j = body.find("{", i)
                    if j < 0:
                        _sh_append_fstring_literal(values, body[i:], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                        break
                    if j + 1 < len(body) and body[j + 1] == "{":
                        _sh_append_fstring_literal(values, body[i : j + 1], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                        i = j + 2
                        continue
                    if j > i:
                        _sh_append_fstring_literal(values, body[i:j], self._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                    k = body.find("}", j + 1)
                    if k < 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="unterminated f-string placeholder in self_hosted parser",
                            source_span=self._node_span(tok["s"], tok["e"]),
                            hint="Close f-string placeholder with `}`.",
                        )
                    inner_expr = body[j + 1 : k].strip()
                    expr_txt = inner_expr
                    conv_txt = ""
                    fmt_txt = ""
                    conv_pos = _sh_find_top_char(inner_expr, "!")
                    fmt_pos = _sh_find_top_char(inner_expr, ":")
                    if conv_pos >= 0 and (fmt_pos < 0 or conv_pos < fmt_pos):
                        expr_txt = inner_expr[:conv_pos].strip()
                        conv_tail_end = fmt_pos if fmt_pos >= 0 else len(inner_expr)
                        conv_txt = inner_expr[conv_pos + 1 : conv_tail_end].strip()
                        if fmt_pos >= 0:
                            fmt_txt = inner_expr[fmt_pos + 1 :].strip()
                    elif fmt_pos >= 0:
                        expr_txt = inner_expr[:fmt_pos].strip()
                        fmt_txt = inner_expr[fmt_pos + 1 :].strip()
                    if expr_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="empty f-string placeholder expression in self_hosted parser",
                            source_span=self._node_span(tok["s"], tok["e"]),
                            hint="Use `{expr}` form inside f-string placeholders.",
                        )
                    values.append(
                        _sh_make_formatted_value_node(
                            _sh_parse_expr(
                                expr_txt,
                                line_no=self.line_no,
                                col_base=self.col_base + tok["s"] + j + 1,
                                name_types=self.name_types,
                                fn_return_types=self.fn_return_types,
                                class_method_return_types=self.class_method_return_types,
                                class_base=self.class_base,
                            ),
                            conversion=conv_txt,
                            format_spec=fmt_txt,
                        )
                    )
                    i = k + 1
                return _sh_make_joined_str_expr(
                    self._node_span(tok["s"], tok["e"]),
                    values,
                    repr_text=raw,
                )
            resolved_type = "str"
            if "b" in prefix and "f" not in prefix:
                resolved_type = "bytes"
            body = _sh_decode_py_string_body(body, "r" in prefix)
            return _sh_make_constant_expr(
                self._node_span(tok["s"], tok["e"]),
                body,
                resolved_type=resolved_type,
                repr_text=raw,
            )
        if tok["k"] == "NAME":
            name_tok = self._eat("NAME")
            nm = str(name_tok["v"])
            if nm in {"True", "False"}:
                return _sh_make_constant_expr(
                    self._node_span(name_tok["s"], name_tok["e"]),
                    nm == "True",
                    resolved_type="bool",
                    repr_text=nm,
                )
            if nm == "None":
                return _sh_make_constant_expr(
                    self._node_span(name_tok["s"], name_tok["e"]),
                    None,
                    resolved_type="None",
                    repr_text=nm,
                )
            t = self.name_types.get(nm, "unknown")
            return _sh_make_name_expr(
                self._node_span(name_tok["s"], name_tok["e"]),
                nm,
                resolved_type=t,
                borrow_kind="readonly_ref" if t != "unknown" else "value",
            )
        if tok["k"] == "(":
            l = self._eat("(")
            if self._cur()["k"] == ")":
                r = self._eat(")")
                return _sh_make_tuple_expr(
                    self._node_span(l["s"], r["e"]),
                    [],
                    resolved_type="tuple[]",
                    repr_text=self._src_slice(l["s"], r["e"]),
                )
            first = self._parse_ifexp()
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                self._eat("NAME")
                target = self._parse_comp_target()
                in_tok = self._eat("NAME")
                if in_tok["v"] != "in":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="expected 'in' in generator expression",
                        source_span=self._node_span(in_tok["s"], in_tok["e"]),
                        hint="Use `(expr for x in iterable)` syntax.",
                    )
                iter_expr = self._parse_or()
                ifs: list[dict[str, Any]] = []
                while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                    self._eat("NAME")
                    ifs.append(self._parse_or())
                r = self._eat(")")
                end_node = ifs[-1] if len(ifs) > 0 else iter_expr
                s = l["s"]
                e = int(end_node["source_span"]["end_col"]) - self.col_base
                return _sh_make_list_comp_expr(
                    self._node_span(s, r["e"]),
                    first,
                    [_sh_make_comp_generator(target, iter_expr, ifs)],
                    repr_text=self._src_slice(s, r["e"]),
                    lowered_kind="GeneratorArg",
                )
            if self._cur()["k"] == ",":
                elements = [first]
                while self._cur()["k"] == ",":
                    self._eat(",")
                    if self._cur()["k"] == ")":
                        break
                    elements.append(self._parse_ifexp())
                r = self._eat(")")
                return _sh_make_tuple_expr(
                    self._node_span(l["s"], r["e"]),
                    elements,
                    repr_text=self._src_slice(l["s"], r["e"]),
                )
            r = self._eat(")")
            first["source_span"] = self._node_span(l["s"], r["e"])
            first["repr"] = self._src_slice(l["s"], r["e"])
            return first
        if tok["k"] == "[":
            l = self._eat("[")
            elements: list[dict[str, Any]] = []
            if self._cur()["k"] != "]":
                first = self._parse_ifexp()
                # list comprehension: [elt for x in iter if cond]
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                    self._eat("NAME")
                    target = self._parse_comp_target()
                    in_tok = self._eat("NAME")
                    if in_tok["v"] != "in":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="expected 'in' in list comprehension",
                            source_span=self._node_span(in_tok["s"], in_tok["e"]),
                            hint="Use `[x for x in iterable]` syntax.",
                        )
                    iter_expr = self._parse_or()
                    if (
                        isinstance(iter_expr, dict)
                        and iter_expr.get("kind") == "Call"
                        and isinstance(iter_expr.get("func"), dict)
                        and iter_expr.get("func", {}).get("kind") == "Name"
                        and iter_expr.get("func", {}).get("id") == "range"
                    ):
                        rargs = list(iter_expr.get("args", []))
                        range_target_span = self._node_span(self.col_base, self.col_base)
                        if isinstance(target, dict):
                            target_span_obj = target.get("source_span")
                            if isinstance(target_span_obj, dict):
                                ts = target_span_obj.get("col")
                                te = target_span_obj.get("end_col")
                            else:
                                ts = None
                                te = None
                            if isinstance(ts, int) and isinstance(te, int):
                                range_target_span = self._node_span(ts, te)
                        if len(rargs) == 1:
                            start_node = _sh_make_constant_expr(
                                range_target_span,
                                0,
                                resolved_type="int64",
                                repr_text="0",
                            )
                            stop_node = rargs[0]
                            step_node = _sh_make_constant_expr(
                                range_target_span,
                                1,
                                resolved_type="int64",
                                repr_text="1",
                            )
                        elif len(rargs) == 2:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = _sh_make_constant_expr(
                                range_target_span,
                                1,
                                resolved_type="int64",
                                repr_text="1",
                            )
                        else:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = rargs[2]
                        iter_expr = _sh_make_range_expr(
                            iter_expr.get("source_span"),
                            start_node,
                            stop_node,
                            step_node,
                            repr_text=str(iter_expr.get("repr", "range(...)")),
                        )
                    ifs: list[dict[str, Any]] = []
                    while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                        self._eat("NAME")
                        ifs.append(self._parse_or())
                    r = self._eat("]")
                    tgt_ty = self._iter_item_type(iter_expr)
                    first_norm = first
                    ifs_norm = ifs
                    if tgt_ty != "unknown":
                        snaps: dict[str, str] = {}
                        self._collect_and_bind_comp_target_types(target, tgt_ty, snaps)
                        first_repr = first.get("repr")
                        first_col = int(first.get("source_span", {}).get("col", self.col_base))
                        if isinstance(first_repr, str) and first_repr != "":
                            first_norm = _sh_parse_expr(
                                first_repr,
                                line_no=self.line_no,
                                col_base=first_col,
                                name_types=self.name_types,
                                fn_return_types=self.fn_return_types,
                                class_method_return_types=self.class_method_return_types,
                                class_base=self.class_base,
                            )
                        ifs_norm = []
                        for cond in ifs:
                            cond_repr = cond.get("repr")
                            cond_col = int(cond.get("source_span", {}).get("col", self.col_base))
                            if isinstance(cond_repr, str) and cond_repr != "":
                                ifs_norm.append(
                                    _sh_parse_expr(
                                        cond_repr,
                                        line_no=self.line_no,
                                        col_base=cond_col,
                                        name_types=self.name_types,
                                        fn_return_types=self.fn_return_types,
                                        class_method_return_types=self.class_method_return_types,
                                        class_base=self.class_base,
                                    )
                                )
                            else:
                                ifs_norm.append(cond)
                        self._restore_comp_target_types(snaps)
                    return _sh_make_list_comp_expr(
                        self._node_span(l["s"], r["e"]),
                        first_norm,
                        [_sh_make_comp_generator(target, iter_expr, ifs_norm)],
                        repr_text=self._src_slice(l["s"], r["e"]),
                    )

                elements.append(first)
                while True:
                    if self._cur()["k"] == ",":
                        self._eat(",")
                        if self._cur()["k"] == "]":
                            break
                        elements.append(self._parse_ifexp())
                        continue
                    break
            r = self._eat("]")
            return _sh_make_list_expr(
                self._node_span(l["s"], r["e"]),
                elements,
                repr_text=self._src_slice(l["s"], r["e"]),
            )
        if tok["k"] == "{":
            l = self._eat("{")
            if self._cur()["k"] == "}":
                r = self._eat("}")
                return _sh_make_dict_expr(
                    self._node_span(l["s"], r["e"]),
                    keys=[],
                    values=[],
                    repr_text=self._src_slice(l["s"], r["e"]),
                )
            first = self._parse_ifexp()
            if self._cur()["k"] == ":":
                keys = [first]
                vals: list[dict[str, Any]] = []
                self._eat(":")
                vals.append(self._parse_ifexp())
                first_key = keys[0]
                first_val = vals[0]
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "for":
                    self._eat("NAME")
                    target = self._parse_comp_target()
                    in_tok = self._eat("NAME")
                    if in_tok["v"] != "in":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="expected 'in' in dict comprehension",
                            source_span=self._node_span(in_tok["s"], in_tok["e"]),
                            hint="Use `for x in iterable` form.",
                        )
                    iter_expr = self._parse_or()
                    ifs: list[dict[str, Any]] = []
                    while self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
                        self._eat("NAME")
                        ifs.append(self._parse_or())

                    key_node = first_key
                    val_node = first_val
                    ifs_norm: list[dict[str, Any]] = list(ifs)
                    iter_ty = self._iter_item_type(iter_expr)
                    if iter_ty != "unknown":
                        snapshots: dict[str, str] = {}
                        self._collect_and_bind_comp_target_types(target, iter_ty, snapshots)
                        try:
                            key_repr = first_key.get("repr")
                            val_repr = first_val.get("repr")
                            if isinstance(key_repr, str) and key_repr != "":
                                key_node = _sh_parse_expr(
                                    key_repr,
                                    line_no=self.line_no,
                                    col_base=int(first_key.get("source_span", {}).get("col", self.col_base)),
                                    name_types=self.name_types,
                                    fn_return_types=self.fn_return_types,
                                    class_method_return_types=self.class_method_return_types,
                                    class_base=self.class_base,
                                )
                            if isinstance(val_repr, str) and val_repr != "":
                                val_node = _sh_parse_expr(
                                    val_repr,
                                    line_no=self.line_no,
                                    col_base=int(first_val.get("source_span", {}).get("col", self.col_base)),
                                    name_types=self.name_types,
                                    fn_return_types=self.fn_return_types,
                                    class_method_return_types=self.class_method_return_types,
                                    class_base=self.class_base,
                                )
                            ifs_norm = []
                            for cond in ifs:
                                cond_repr = cond.get("repr")
                                cond_col = int(cond.get("source_span", {}).get("col", self.col_base))
                                if isinstance(cond_repr, str) and cond_repr != "":
                                    ifs_norm.append(
                                        _sh_parse_expr(
                                            cond_repr,
                                            line_no=self.line_no,
                                            col_base=cond_col,
                                            name_types=self.name_types,
                                            fn_return_types=self.fn_return_types,
                                            class_method_return_types=self.class_method_return_types,
                                            class_base=self.class_base,
                                        )
                                    )
                                else:
                                    ifs_norm.append(cond)
                        finally:
                            self._restore_comp_target_types(snapshots)
                    end_node = ifs_norm[-1] if len(ifs_norm) > 0 else iter_expr
                    end_col = int(end_node.get("source_span", {}).get("end_col", self.col_base))
                    r = self._eat("}")
                    return _sh_make_dict_comp_expr(
                        self._node_span(l["s"], end_col - self.col_base),
                        key_node,
                        val_node,
                        [_sh_make_comp_generator(target, iter_expr, ifs_norm)],
                        repr_text=self._src_slice(l["s"], end_col - self.col_base),
                    )
                while self._cur()["k"] == ",":
                    self._eat(",")
                    if self._cur()["k"] == "}":
                        break
                    keys.append(self._parse_ifexp())
                    self._eat(":")
                    vals.append(self._parse_ifexp())
                r = self._eat("}")
                return _sh_make_dict_expr(
                    self._node_span(l["s"], r["e"]),
                    keys=keys,
                    values=vals,
                    repr_text=self._src_slice(l["s"], r["e"]),
                )
            elements = [first]
            while self._cur()["k"] == ",":
                self._eat(",")
                if self._cur()["k"] == "}":
                    break
                elements.append(self._parse_ifexp())
            r = self._eat("}")
            return _sh_make_set_expr(
                self._node_span(l["s"], r["e"]),
                elements,
                repr_text=self._src_slice(l["s"], r["e"]),
            )
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"self_hosted parser cannot parse expression token: {tok['k']}",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Extend self_hosted expression parser for this syntax.",
        )


def _sh_parse_expr(
    text: str,
    line_no: int,
    col_base: int,
    name_types: dict[str, str],
    fn_return_types: dict[str, str],
    class_method_return_types: dict[str, dict[str, str]] = {},
    class_base: dict[str, str | None] = {},
) -> dict[str, Any]:
    """1つの式文字列を self-hosted 方式で EAST 式ノードに変換する。"""
    txt = text.strip()
    if txt == "":
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message="empty expression in self_hosted backend",
            source_span=_sh_span(line_no, col_base, col_base),
            hint="Provide a non-empty expression.",
        )
    parser = _ShExprParser(
        txt,
        line_no,
        col_base + (len(text) - len(text.lstrip())),
        name_types,
        fn_return_types,
        class_method_return_types,
        class_base,
    )
    return parser.parse()


def _sh_parse_expr_lowered(expr_txt: str, *, ln_no: int, col: int, name_types: dict[str, str]) -> dict[str, Any]:
    """式文字列を EAST 式ノードへ変換する（簡易 lower を含む）。"""
    raw = expr_txt
    txt = raw.strip()

    # lambda は if-expression より結合が弱いので、
    # ここでの簡易 ifexp 分解を回避して self_hosted 式パーサへ委譲する。
    if txt.startswith("lambda "):
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    # if-expression: a if cond else b
    p_if = _sh_split_top_keyword(txt, "if")
    p_else = _sh_split_top_keyword(txt, "else")
    if p_if >= 0 and p_else > p_if:
        body_txt = txt[:p_if].strip()
        test_txt = txt[p_if + 2 : p_else].strip()
        else_txt = txt[p_else + 4 :].strip()
        body_node = _sh_parse_expr_lowered(body_txt, ln_no=ln_no, col=col + txt.find(body_txt), name_types=dict(name_types))
        test_node = _sh_parse_expr_lowered(test_txt, ln_no=ln_no, col=col + txt.find(test_txt), name_types=dict(name_types))
        else_node = _sh_parse_expr_lowered(else_txt, ln_no=ln_no, col=col + txt.rfind(else_txt), name_types=dict(name_types))
        return _sh_make_ifexp_expr(
            _sh_span(ln_no, col, col + len(raw)),
            test_node,
            body_node,
            else_node,
            repr_text=txt,
        )

    # Normalize generator-arg any/all into list-comp form for self_hosted parser.
    m_any_all: re.Match | None = re.match(r"^(any|all)\((.+)\)$", txt, flags=re.S)
    if m_any_all is not None:
        fn_name = re.group(m_any_all, 1)
        inner_arg = re.strip_group(m_any_all, 2)
        if _sh_split_top_keyword(inner_arg, "for") > 0 and _sh_split_top_keyword(inner_arg, "in") > 0:
            lc = _sh_parse_expr_lowered(f"[{inner_arg}]", ln_no=ln_no, col=col + txt.find(inner_arg), name_types=dict(name_types))
            runtime_call = "py_any" if fn_name == "any" else ("py_all" if fn_name == "all" else "")
            semantic_tag = lookup_builtin_semantic_tag(fn_name)
            return _sh_make_builtin_listcomp_call_expr(
                _sh_span(ln_no, col, col + len(raw)),
                line_no=ln_no,
                base_col=col,
                func_name=fn_name,
                arg=lc,
                repr_text=txt,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )

    # Normalize single generator-argument calls into list-comp argument form.
    # Example: ", ".join(f(x) for x in items) -> ", ".join([f(x) for x in items])
    if txt.endswith(")"):
        depth = 0
        in_str: str | None = None
        esc = False
        open_idx = -1
        close_idx = -1
        for idx, ch in enumerate(txt):
            if in_str is not None:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == in_str:
                    in_str = None
                continue
            if ch in {"'", '"'}:
                in_str = ch
                continue
            if ch == "(":
                if depth == 0 and open_idx < 0:
                    open_idx = idx
                depth += 1
                continue
            if ch == ")":
                depth -= 1
                if depth == 0:
                    close_idx = idx
                continue
            if open_idx > 0 and close_idx == len(txt) - 1:
                inner = txt[open_idx + 1 : close_idx].strip()
                inner_parts: list[str] = _sh_split_top_commas(inner)
                if len(inner_parts) == 1 and inner_parts[0] == inner and _sh_split_top_keyword(inner, "for") > 0 and _sh_split_top_keyword(inner, "in") > 0:
                    rewritten = txt[: open_idx + 1] + "[" + inner + "]" + txt[close_idx:]
                    return _sh_parse_expr_lowered(rewritten, ln_no=ln_no, col=col, name_types=dict(name_types))

    # Handle concatenation chains that include f-strings before generic parsing.
    top_comma_parts = _sh_split_top_commas(txt)
    is_single_top_expr = len(top_comma_parts) == 1

    adjacent_strings = _sh_extract_adjacent_string_parts(txt, ln_no, col, name_types)
    if adjacent_strings is not None and len(adjacent_strings) >= 2:
        nodes = [
            _sh_parse_expr(
                part,
                line_no=ln_no,
                col_base=part_col,
                name_types=name_types,
                fn_return_types=_SH_FN_RETURNS,
                class_method_return_types=_SH_CLASS_METHOD_RETURNS,
                class_base=_SH_CLASS_BASE,
            )
            for part, part_col in adjacent_strings
        ]
        node = nodes[0]
        for rhs in nodes[1:]:
            node = _sh_make_binop_expr(
                _sh_span(ln_no, col, col + len(raw)),
                node,
                "Add",
                rhs,
                resolved_type="str",
                repr_text=txt,
            )
        return node

    plus_parts = _sh_split_top_plus(txt)
    if len(plus_parts) >= 2 and any(p.startswith("f\"") or p.startswith("f'") for p in plus_parts):
        nodes = [_sh_parse_expr_lowered(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in plus_parts]
        node = nodes[0]
        for rhs in nodes[1:]:
            node = _sh_make_binop_expr(
                _sh_span(ln_no, col, col + len(raw)),
                node,
                "Add",
                rhs,
                resolved_type="str",
                repr_text=txt,
            )
        return node
    if len(plus_parts) >= 2 and is_single_top_expr:
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    # dict-comp support: {k: v for x in it} / {k: v for a, b in it}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt and is_single_top_expr:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            head = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid dict comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `{key: value for item in iterable}` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            if ":" not in head:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid dict comprehension pair in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `key: value` pair before `for`.",
                )
            ktxt, vtxt = head.split(":", 1)
            ktxt = ktxt.strip()
            vtxt = vtxt.strip()
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            key_node = _sh_parse_expr_lowered(ktxt, ln_no=ln_no, col=col + txt.find(ktxt), name_types=dict(comp_types))
            val_node = _sh_parse_expr_lowered(vtxt, ln_no=ln_no, col=col + txt.find(vtxt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            kt = str(key_node.get("resolved_type", "unknown"))
            vt = str(val_node.get("resolved_type", "unknown"))
            return _sh_make_dict_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                key_node,
                val_node,
                [_sh_make_comp_generator(target_node, iter_node, if_nodes)],
                resolved_type=f"dict[{kt},{vt}]",
                repr_text=txt,
            )

    # set-comp support: {x for x in it} / {x for a, b in it if cond}
    if txt.startswith("{") and txt.endswith("}") and ":" not in txt and is_single_top_expr:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid set comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `{elem for item in iterable}` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            return _sh_make_set_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                elt_node,
                [_sh_make_comp_generator(target_node, iter_node, if_nodes)],
                repr_text=txt,
            )

    # dict literal: {"a": 1, "b": 2}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt:
        inner = txt[1:-1].strip()
        entries: list[dict[str, Any]] = []
        if inner != "":
            for part in _sh_split_top_commas(inner):
                if ":" not in part:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid dict entry in self_hosted parser: {part}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `key: value` form in dict literals.",
                    )
                ktxt, vtxt = part.split(":", 1)
                ktxt = ktxt.strip()
                vtxt = vtxt.strip()
                entries.append(
                    _sh_make_dict_entry(
                        _sh_parse_expr_lowered(
                            ktxt,
                            ln_no=ln_no,
                            col=col + txt.find(ktxt),
                            name_types=dict(name_types),
                        ),
                        _sh_parse_expr_lowered(
                            vtxt,
                            ln_no=ln_no,
                            col=col + txt.find(vtxt),
                            name_types=dict(name_types),
                        ),
                    )
                )
        return _sh_make_dict_expr(
            _sh_span(ln_no, col, col + len(raw)),
            entries=entries,
            repr_text=txt,
        )

    # list-comp support: [expr for target in iter if cond] + chained for-clauses
    if txt.startswith("[") and txt.endswith("]") and is_single_top_expr:
        first_closing = -1
        depth = 0
        in_str3: str | None = None
        esc3 = False
        for i, ch in enumerate(txt):
            if in_str3 is not None:
                if esc3:
                    esc3 = False
                    continue
                if ch == "\\":
                    esc3 = True
                elif ch == in_str3:
                    in_str3 = None
                continue
            if ch in {"'", '"'}:
                in_str3 = ch
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                if depth == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid bracket nesting in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Check list/tuple bracket balance.",
                    )
                depth -= 1
                if depth == 0:
                    first_closing = i
                    break
        if first_closing != len(txt) - 1:
            # Delegate to full parser when this is not a standalone list expression
            # (e.g. list-comprehension result with trailing slice/index).
            return _sh_parse_expr(
                txt,
                line_no=ln_no,
                col_base=col,
                name_types=name_types,
                fn_return_types=_SH_FN_RETURNS,
                class_method_return_types=_SH_CLASS_METHOD_RETURNS,
                class_base=_SH_CLASS_BASE,
            )

        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            rest = inner[p_for + 3 :].strip()
            generators: list[dict[str, Any]] = []
            comp_types: dict[str, str] = dict(name_types)
            while True:
                    p_in = _sh_split_top_keyword(rest, "in")
                    if p_in <= 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )
                    tgt_txt = rest[:p_in].strip()
                    iter_and_suffix_txt = rest[p_in + 2 :].strip()
                    if tgt_txt == "" or iter_and_suffix_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )
                    p_next_for = _sh_split_top_keyword(iter_and_suffix_txt, "for")
                    p_next_if = _sh_split_top_keyword(iter_and_suffix_txt, "if")
                    next_pos = -1
                    if p_next_for >= 0 and (p_next_if < 0 or p_next_for < p_next_if):
                        next_pos = p_next_for
                    elif p_next_if >= 0:
                        next_pos = p_next_if
                    iter_txt = iter_and_suffix_txt
                    suffix_txt = ""
                    if next_pos >= 0:
                        iter_txt = iter_and_suffix_txt[:next_pos].strip()
                        suffix_txt = iter_and_suffix_txt[next_pos:].strip()
                    if iter_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable]` form.",
                        )

                    target_node = _sh_parse_expr_lowered(
                        tgt_txt,
                        ln_no=ln_no,
                        col=col + txt.find(tgt_txt),
                        name_types=dict(comp_types),
                    )
                    iter_node = _sh_parse_expr_lowered(
                        iter_txt,
                        ln_no=ln_no,
                        col=col + txt.find(iter_txt),
                        name_types=dict(comp_types),
                    )
                    if (
                        isinstance(iter_node, dict)
                        and iter_node.get("kind") == "Call"
                        and isinstance(iter_node.get("func"), dict)
                        and iter_node.get("func", {}).get("kind") == "Name"
                        and iter_node.get("func", {}).get("id") == "range"
                    ):
                        rargs = list(iter_node.get("args", []))
                        if len(rargs) == 1:
                            start_node = _sh_make_constant_expr(
                                _sh_span(ln_no, col, col),
                                0,
                                resolved_type="int64",
                                repr_text="0",
                            )
                            stop_node = rargs[0]
                            step_node = _sh_make_constant_expr(
                                _sh_span(ln_no, col, col),
                                1,
                                resolved_type="int64",
                                repr_text="1",
                            )
                        elif len(rargs) == 2:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = _sh_make_constant_expr(
                                _sh_span(ln_no, col, col),
                                1,
                                resolved_type="int64",
                                repr_text="1",
                            )
                        else:
                            start_node = rargs[0]
                            stop_node = rargs[1]
                            step_node = rargs[2]
                        iter_node = _sh_make_range_expr(
                            iter_node.get("source_span"),
                            start_node,
                            stop_node,
                            step_node,
                            repr_text=str(iter_node.get("repr", "range(...)")),
                        )

                    comp_types = _sh_bind_comp_target_types(dict(comp_types), target_node, iter_node)
                    if_nodes: list[dict[str, Any]] = []
                    while suffix_txt.startswith("if "):
                        cond_tail = suffix_txt[3:].strip()
                        p_cond_for = _sh_split_top_keyword(cond_tail, "for")
                        p_cond_if = _sh_split_top_keyword(cond_tail, "if")
                        split_pos = -1
                        if p_cond_for >= 0 and (p_cond_if < 0 or p_cond_for < p_cond_if):
                            split_pos = p_cond_for
                        elif p_cond_if >= 0:
                            split_pos = p_cond_if
                        cond_txt = cond_tail
                        suffix_txt = ""
                        if split_pos >= 0:
                            cond_txt = cond_tail[:split_pos].strip()
                            suffix_txt = cond_tail[split_pos:].strip()
                        if cond_txt == "":
                            raise _make_east_build_error(
                                kind="unsupported_syntax",
                                message=f"invalid list comprehension condition in self_hosted parser: {txt}",
                                source_span=_sh_span(ln_no, col, col + len(raw)),
                                hint="Use `[elem for item in iterable if cond]` form.",
                            )
                        if_nodes.append(
                            _sh_parse_expr_lowered(
                                cond_txt,
                                ln_no=ln_no,
                                col=col + txt.find(cond_txt),
                                name_types=dict(comp_types),
                            )
                        )

                    generators.append(_sh_make_comp_generator(target_node, iter_node, if_nodes))
                    if suffix_txt == "":
                        break
                    if not suffix_txt.startswith("for "):
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable for item2 in iterable2]` form.",
                        )
                    rest = suffix_txt[4:].strip()
                    if rest == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable for item2 in iterable2]` form.",
                        )

            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            elem_t = str(elt_node.get("resolved_type", "unknown"))
            return _sh_make_list_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                elt_node,
                generators,
                resolved_type=f"list[{elem_t}]",
                repr_text=txt,
            )

    # Very simple list-comp support: [x for x in <iter>]
    m_lc: re.Match | None = re.match(r"^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s+for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)\]$", txt)
    if m_lc is not None:
        elt_name = re.group(m_lc, 1)
        tgt_name = re.group(m_lc, 2)
        iter_txt = re.strip_group(m_lc, 3)
        iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
        it_t = str(iter_node.get("resolved_type", "unknown"))
        elem_t = "unknown"
        if it_t.startswith("list[") and it_t.endswith("]"):
            elem_t = it_t[5:-1]
        return _sh_make_simple_name_list_comp_expr(
            _sh_span(ln_no, col, col + len(raw)),
            line_no=ln_no,
            base_col=col,
            elt_name=elt_name,
            target_name=tgt_name,
            iter_expr=iter_node,
            elem_type=elem_t,
            repr_text=txt,
        )

    if len(txt) >= 3 and txt[0] == "f" and txt[1] in {"'", '"'} and txt[-1] == txt[1]:
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    tuple_parts = _sh_split_top_commas(txt)
    if len(tuple_parts) >= 2 or (len(tuple_parts) == 1 and txt.endswith(",")):
        elems = [_sh_parse_expr_lowered(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in tuple_parts]
        elem_ts = [str(e.get("resolved_type", "unknown")) for e in elems]
        return _sh_make_tuple_expr(
            _sh_span(ln_no, col, col + len(raw)),
            elems,
            resolved_type="tuple[" + ", ".join(elem_ts) + "]",
            repr_text=txt,
        )

    return _sh_parse_expr(
        txt,
        line_no=ln_no,
        col_base=col,
        name_types=name_types,
        fn_return_types=_SH_FN_RETURNS,
        class_method_return_types=_SH_CLASS_METHOD_RETURNS,
        class_base=_SH_CLASS_BASE,
    )

def _sh_parse_stmt_block_mutable(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """インデントブロックを文単位で解析し、EAST 文リストを返す。"""
    def _maybe_bind_self_field(
        target_expr: dict[str, Any] | None,
        value_type: str | None,
        *,
        explicit: str | None = None,
    ) -> None:
        """`self.xxx` への代入時、self フィールドの型推論を更新する。"""
        if not isinstance(target_expr, dict):
            return
        if target_expr.get("kind") != "Attribute":
            return
        owner = target_expr.get("value")
        if not isinstance(owner, dict):
            return
        if owner.get("kind") != "Name" or owner.get("id") != "self":
            return
        field_name = str(target_expr.get("attr", "")).strip()
        if field_name == "":
            return
        candidate = value_type or ""
        if candidate != "":
            name_types[field_name] = candidate
            return
        if isinstance(explicit, str) and explicit.strip() != "":
            name_types[field_name] = explicit.strip()

    body_lines, merged_line_end = _sh_merge_logical_lines(body_lines)

    stmts: list[dict[str, Any]] = []
    pending_leading_trivia: list[dict[str, Any]] = []
    pending_blank_count = 0

    skip = 0
    for i, (_, ln_txt) in enumerate(body_lines):
        if skip > 0:
            skip -= 1
            continue
        ln_no, ln_txt = body_lines[i]
        indent = len(ln_txt) - len(ln_txt.lstrip(" "))
        raw_s = ln_txt.strip()
        s = _sh_strip_inline_comment(raw_s)
        _sh_raise_if_trailing_stmt_terminator(s, line_no=ln_no, line_text=ln_txt)

        if raw_s == "":
            pending_blank_count += 1
            continue
        if raw_s.startswith("#"):
            if pending_blank_count > 0:
                pending_leading_trivia.append(_sh_make_trivia_blank(pending_blank_count))
                pending_blank_count = 0
            text = raw_s[1:]
            if text.startswith(" "):
                text = text[1:]
            pending_leading_trivia.append(_sh_make_trivia_comment(text))
            continue
        if s == "":
            continue

        sig_line, inline_fn_stmt = _sh_split_def_header_and_inline_stmt(s)
        sig = _sh_parse_def_sig(ln_no, sig_line)
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types: dict[str, str] = dict(sig["arg_types"])
            arg_type_exprs_obj: Any = sig.get("arg_type_exprs")
            arg_type_exprs: dict[str, Any] = arg_type_exprs_obj if isinstance(arg_type_exprs_obj, dict) else {}
            arg_order: list[str] = list(sig["arg_order"])
            arg_defaults_raw_obj: Any = sig.get("arg_defaults")
            arg_defaults_raw: dict[str, Any] = arg_defaults_raw_obj if isinstance(arg_defaults_raw_obj, dict) else {}
            fn_block: list[tuple[int, str]] = []
            j = i + 1
            if inline_fn_stmt != "":
                fn_block = [(ln_no, " " * (indent + 4) + inline_fn_stmt)]
            else:
                fn_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
                if len(fn_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser requires non-empty nested function body '{fn_name}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add nested function statements.",
                    )
            fn_scope_types: dict[str, str] = dict(name_types)
            for arg_name, arg_ty in arg_types.items():
                fn_scope_types[arg_name] = arg_ty
            fn_stmts = _sh_parse_stmt_block(fn_block, name_types=fn_scope_types, scope_label=f"{scope_label}.{fn_name}")
            docstring, fn_stmts = _sh_extract_leading_docstring(fn_stmts)
            fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, fn_stmts)
            yield_types = _sh_collect_yield_value_types(fn_stmts)
            is_generator = len(yield_types) > 0
            fn_ret_effective = fn_ret
            yield_value_type = "unknown"
            if is_generator:
                fn_ret_effective, yield_value_type = _sh_make_generator_return_type(fn_ret, yield_types)
            fn_ret_type_expr = _sh_ann_to_type_expr(fn_ret_effective)
            arg_defaults: dict[str, Any] = {}
            arg_index_map: dict[str, int] = {}
            for arg_pos, arg_name in enumerate(arg_order):
                arg_index_map[arg_name] = int(arg_pos)
                if arg_name in arg_defaults_raw:
                    default_obj: Any = arg_defaults_raw[arg_name]
                    default_txt: str = str(default_obj).strip()
                    if default_txt != "":
                        default_col = ln_txt.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = _sh_parse_expr_lowered(
                            default_txt,
                            ln_no=ln_no,
                            col=default_col,
                            name_types=dict(name_types),
                        )
            arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, fn_stmts)
            callable_parts: list[str] = []
            for arg_name in arg_order:
                callable_parts.append(arg_types.get(arg_name, "unknown"))
            name_types[fn_name] = "callable[" + ", ".join(callable_parts) + "->" + fn_ret_effective + "]"
            _SH_FN_RETURNS[fn_name] = fn_ret_effective
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_function_def_stmt(
                    fn_name,
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    arg_types,
                    arg_order,
                    fn_ret_effective,
                    fn_stmts,
                    arg_type_exprs=arg_type_exprs,
                    arg_defaults=arg_defaults,
                    arg_index=arg_index_map,
                    return_type_expr=fn_ret_type_expr,
                    arg_usage=arg_usage_map,
                    docstring=docstring,
                    is_generator=is_generator,
                    yield_value_type=yield_value_type,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("if ") and s.endswith(":"):
            cond_txt = s[len("if ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            then_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(then_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"if body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented if-body.",
                )
            else_stmt_list, j = _sh_parse_if_tail(
                start_idx=j,
                parent_indent=indent,
                body_lines=body_lines,
                name_types=dict(name_types),
                scope_label=scope_label,
            )
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_if_stmt(
                    _sh_block_end_span(body_lines, ln_no, ln_txt.find("if "), len(ln_txt), j),
                    cond_expr,
                    _sh_parse_stmt_block(then_block, name_types=dict(name_types), scope_label=scope_label),
                    orelse=else_stmt_list,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("for "):
            for_full = s[len("for ") :].strip()
            for_head = ""
            inline_stmt_text = ""
            if for_full.endswith(":"):
                for_head = for_full[:-1].strip()
            else:
                split_colon = _sh_split_top_level_colon(for_full)
                if split_colon is not None:
                    for_head = split_colon[0]
                    inline_stmt_text = split_colon[1]
            if for_head == "":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            split_for = _sh_split_top_level_in(for_head)
            if split_for is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            tgt_txt, iter_txt = split_for
            tgt_col = ln_txt.find(tgt_txt)
            iter_col = ln_txt.find(iter_txt)
            target_expr = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=tgt_col, name_types=dict(name_types))
            iter_expr = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=iter_col, name_types=dict(name_types))
            body_block: list[tuple[int, str]] = []
            j = i + 1
            if inline_stmt_text != "":
                body_block.append((ln_no, " " * (indent + 4) + inline_stmt_text))
            else:
                body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
                if len(body_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"for body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented for-body.",
                    )
            t_ty = "unknown"
            i_ty = str(iter_expr.get("resolved_type", "unknown"))
            i_ty_norm = i_ty.strip()
            iter_mode = "static_fastpath"
            iterable_trait = "unknown"
            iter_protocol = "static_range"
            tuple_target_elem_types: list[str] = []
            if i_ty.startswith("list[") and i_ty.endswith("]"):
                inner_t = i_ty[5:-1].strip()
                t_ty = inner_t
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
                if inner_t.startswith("tuple[") and inner_t.endswith("]"):
                    tuple_inner = inner_t[6:-1].strip()
                    if tuple_inner != "":
                        tuple_target_elem_types = _sh_split_top_commas(tuple_inner)
            elif i_ty.startswith("dict[") and i_ty.endswith("]"):
                dict_inner = i_ty[5:-1].strip()
                dict_parts = _sh_split_top_commas(dict_inner)
                if len(dict_parts) >= 1:
                    key_t = dict_parts[0].strip()
                    t_ty = key_t if key_t != "" else "unknown"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty.startswith("tuple[") and i_ty.endswith("]"):
                t_ty = "unknown"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty.startswith("set[") and i_ty.endswith("]"):
                t_ty = i_ty[4:-1]
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty == "str":
                t_ty = "str"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty in {"bytes", "bytearray"}:
                t_ty = "uint8"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty_norm == "Any" or i_ty_norm == "object":
                iter_mode = "runtime_protocol"
                iterable_trait = "unknown"
                iter_protocol = "runtime_protocol"
            elif i_ty_norm in {"int", "int64", "float", "float64", "bool"}:
                iterable_trait = "no"
                iter_mode = "runtime_protocol"
                iter_protocol = "runtime_protocol"
            elif "|" in i_ty_norm:
                union_parts = _sh_split_top_commas(i_ty_norm.replace("|", ","))
                for up in union_parts:
                    u = up.strip()
                    if u == "Any" or u == "object":
                        iter_mode = "runtime_protocol"
                        iter_protocol = "runtime_protocol"
                        break
            if isinstance(iter_expr, dict):
                iter_expr["iterable_trait"] = iterable_trait
                iter_expr["iter_protocol"] = iter_protocol
                iter_expr["iter_element_type"] = t_ty
            target_names: list[str] = []
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    target_names.append(nm)
            elif isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                elem_nodes_obj: Any = target_expr.get("elements", [])
                elem_nodes: list[dict[str, Any]] = elem_nodes_obj if isinstance(elem_nodes_obj, list) else []
                for e in elem_nodes:
                    if isinstance(e, dict) and e.get("kind") == "Name":
                        nm = str(e.get("id", ""))
                        if nm != "":
                            target_names.append(nm)
            if len(tuple_target_elem_types) > 0 and isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                target_expr["resolved_type"] = f"tuple[{','.join([t.strip() if t.strip() != '' else 'unknown' for t in tuple_target_elem_types])}]"
                for idx, nm in enumerate(target_names):
                    if idx < len(tuple_target_elem_types):
                        et = tuple_target_elem_types[idx].strip()
                        if et == "":
                            et = "unknown"
                        name_types[nm] = et
                        try:
                            elem_nodes[idx]["resolved_type"] = et
                        except Exception:
                            pass
                    else:
                        name_types[nm] = "unknown"
                        try:
                            elem_nodes[idx]["resolved_type"] = "unknown"
                        except Exception:
                            pass
            elif t_ty != "unknown":
                for nm in target_names:
                    name_types[nm] = t_ty
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    target_expr["resolved_type"] = t_ty
            if (
                isinstance(target_expr, dict)
                and target_expr.get("kind") == "Name"
                and
                isinstance(iter_expr, dict)
                and iter_expr.get("kind") == "Call"
                and isinstance(iter_expr.get("func"), dict)
                and iter_expr.get("func", {}).get("kind") == "Name"
                and iter_expr.get("func", {}).get("id") == "range"
            ):
                rargs = list(iter_expr.get("args", []))
                start_node: dict[str, Any]
                stop_node: dict[str, Any]
                step_node: dict[str, Any]
                if len(rargs) == 1:
                    start_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        0,
                        resolved_type="int64",
                        repr_text="0",
                    )
                    stop_node = rargs[0]
                    step_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        1,
                        resolved_type="int64",
                        repr_text="1",
                    )
                elif len(rargs) == 2:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        1,
                        resolved_type="int64",
                        repr_text="1",
                    )
                else:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = rargs[2]
                tgt = str(target_expr.get("id", ""))
                if tgt != "":
                    name_types[tgt] = "int64"
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_for_range_stmt(
                        _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                        target_expr,
                        start_node,
                        stop_node,
                        step_node,
                        _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    ),
                )
                skip = j - i - 1
                continue
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_for_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    target_expr,
                    iter_expr,
                    _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    target_type=t_ty,
                    iter_mode=iter_mode,
                    iter_source_type=i_ty_norm if i_ty_norm != "" else "unknown",
                    iter_element_type=t_ty,
                ),
            )
            skip = j - i - 1
            continue

        m_import: re.Match | None = re.match(r"^import\s+(.+)$", s, flags=re.S)
        if m_import is not None:
            names_txt = re.strip_group(m_import, 1)
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="import statement has no module names",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name, as_name_txt = parsed_alias
                if mod_name == "typing":
                    # `typing` は注釈専用モジュールとして扱い、EAST 依存には積まない。
                    continue
                if mod_name == "dataclasses":
                    # `dataclasses` は decorator 解決専用モジュールとして扱い、EAST 依存には積まない。
                    bind_name_dc = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                    _sh_register_import_module(bind_name_dc, mod_name)
                    continue
                bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                _sh_register_import_module(bind_name, mod_name)
                if _sh_is_host_only_alias(bind_name):
                    continue
                aliases.append(_sh_make_import_alias(mod_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_stmt(
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        aliases,
                    ),
                )
            continue

        if s.startswith("from "):
            marker = " import "
            pos = s.find(marker)
            if pos >= 0:
                mod_txt = s[5:pos].strip()
                if mod_txt.startswith("."):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="relative import is not supported",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use absolute import form: `from module import name`.",
                    )
        m_import_from: re.Match | None = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
        if m_import_from is not None:
            mod_name = re.strip_group(m_import_from, 1)
            names_txt = re.strip_group(m_import_from, 2)
            if mod_name == "typing":
                # `from typing import ...` は注釈解決専用で、EAST には出力しない。
                continue
            if mod_name == "dataclasses":
                # `from dataclasses import ...` は decorator 解決専用で、EAST には出力しない。
                if names_txt != "*":
                    raw_parts_dc: list[str] = []
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts_dc.append(p2)
                    for part in raw_parts_dc:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_name, as_name_txt = parsed_alias
                        bind_name_dc = as_name_txt if as_name_txt != "" else sym_name
                        _sh_register_import_symbol(bind_name_dc, mod_name, sym_name)
                continue
            if mod_name == "__future__":
                if names_txt == "*":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from __future__ import * is not supported",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from __future__ import annotations` only.",
                    )
                raw_parts: list[str] = []
                for p in names_txt.split(","):
                    p2: str = p.strip()
                    if p2 != "":
                        raw_parts.append(p2)
                if len(raw_parts) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from-import statement has no symbol names",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from module import name` form.",
                    )
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported from-import clause: {part}",
                            source_span=_sh_span(ln_no, 0, len(ln_txt)),
                            hint="Use `from module import name` or `... as alias`.",
                        )
                    sym_name, as_name_txt = parsed_alias
                    if sym_name != "annotations" or as_name_txt != "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported __future__ feature: {part}",
                            source_span=_sh_span(ln_no, 0, len(ln_txt)),
                            hint="Only `from __future__ import annotations` is supported.",
                        )
                # `from __future__ import annotations` is frontend-only and does not appear in EAST.
                continue
            if names_txt == "*":
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_from_stmt(
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        mod_name,
                        [_sh_make_import_alias("*")],
                    ),
                )
                continue
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="from-import statement has no symbol names",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from module import name` or `... as alias`.",
                    )
                sym_name, as_name_txt = parsed_alias
                bind_name = as_name_txt if as_name_txt != "" else sym_name
                _sh_register_import_symbol(bind_name, mod_name, sym_name)
                if _sh_is_host_only_alias(bind_name):
                    continue
                aliases.append(_sh_make_import_alias(sym_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_from_stmt(
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        mod_name,
                        aliases,
                    ),
                )
            continue

        if s.startswith("with ") and s.endswith(":"):
            m_with: re.Match | None = re.match(r"^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", s, flags=re.S)
            if m_with is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse with statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `with expr as name:` form.",
                )
            ctx_txt = re.strip_group(m_with, 1)
            as_name = re.strip_group(m_with, 2)
            ctx_col = ln_txt.find(ctx_txt)
            as_col = ln_txt.find(as_name, ctx_col + len(ctx_txt))
            ctx_expr = _sh_parse_expr_lowered(ctx_txt, ln_no=ln_no, col=ctx_col, name_types=dict(name_types))
            name_types[as_name] = str(ctx_expr.get("resolved_type", "unknown"))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"with body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented with-body.",
                )
            assign_stmt = _sh_make_assign_stmt(
                _sh_stmt_span(merged_line_end, ln_no, as_col, len(ln_txt)),
                _sh_make_name_expr(
                    _sh_span(ln_no, as_col, as_col + len(as_name)),
                    as_name,
                    resolved_type=str(ctx_expr.get("resolved_type", "unknown")),
                ),
                ctx_expr,
                declare=True,
                declare_init=True,
                decl_type=str(ctx_expr.get("resolved_type", "unknown")),
            )
            close_expr = _sh_parse_expr_lowered(f"{as_name}.close()", ln_no=ln_no, col=as_col, name_types=dict(name_types))
            try_stmt = _sh_make_try_stmt(
                _sh_block_end_span(body_lines, ln_no, ln_txt.find("with "), len(ln_txt), j),
                _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                finalbody=[_sh_make_expr_stmt(close_expr, _sh_stmt_span(merged_line_end, ln_no, as_col, len(ln_txt)))],
            )
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, assign_stmt)
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, try_stmt)
            skip = j - i - 1
            continue

        if s.startswith("while ") and s.endswith(":"):
            cond_txt = s[len("while ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"while body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented while-body.",
                )
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_while_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    cond_expr,
                    _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                ),
            )
            skip = j - i - 1
            continue

        if s == "try:":
            try_body, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(try_body) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"try body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented try-body.",
                )
            handlers: list[dict[str, Any]] = []
            finalbody: list[dict[str, Any]] = []
            while j < len(body_lines):
                h_no, h_ln = body_lines[j]
                h_s = h_ln.strip()
                h_indent = len(h_ln) - len(h_ln.lstrip(" "))
                if h_indent != indent:
                    break
                exc_clause = _sh_parse_except_clause(h_s)
                if exc_clause is not None:
                    ex_type_txt, ex_name = exc_clause
                    ex_type_col = h_ln.find(ex_type_txt)
                    if ex_type_col < 0:
                        ex_type_col = h_ln.find("except")
                        if ex_type_col < 0:
                            ex_type_col = 0
                    h_body, k = _sh_collect_indented_block(body_lines, j + 1, indent)
                    handlers.append(
                        _sh_make_except_handler(
                            _sh_parse_expr_lowered(
                                ex_type_txt,
                                ln_no=h_no,
                                col=ex_type_col,
                                name_types=dict(name_types),
                            ),
                            _sh_parse_stmt_block(h_body, name_types=dict(name_types), scope_label=scope_label),
                            name=ex_name,
                        )
                    )
                    j = k
                    continue
                if h_s == "finally:":
                    f_body, k = _sh_collect_indented_block(body_lines, j + 1, indent)
                    finalbody = _sh_parse_stmt_block(f_body, name_types=dict(name_types), scope_label=scope_label)
                    j = k
                    continue
                break
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_try_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    _sh_parse_stmt_block(try_body, name_types=dict(name_types), scope_label=scope_label),
                    handlers=handlers,
                    finalbody=finalbody,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("raise "):
            expr_txt = s[len("raise ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            cause_expr = None
            cause_split = _sh_split_top_level_from(expr_txt)
            if cause_split is not None:
                exc_txt, cause_txt = cause_split
                expr_txt = exc_txt
                expr_col = ln_txt.find(expr_txt)
                cause_col = ln_txt.find(cause_txt)
                cause_expr = _sh_parse_expr_lowered(cause_txt, ln_no=ln_no, col=cause_col, name_types=dict(name_types))
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_raise_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, ln_txt.find("raise "), len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                    cause=cause_expr,
                )
            )
            continue

        if s == "pass":
            pass_stmt = _sh_make_pass_stmt(_sh_stmt_span(merged_line_end, ln_no, indent, indent + 4))
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, pass_stmt)
            continue

        if s == "return":
            rcol = ln_txt.find("return")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_return_stmt(_sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)))
            )
            continue

        if s.startswith("return "):
            rcol = ln_txt.find("return ")
            expr_txt = s[len("return ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            if expr_col < 0:
                expr_col = rcol + len("return ")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_return_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                )
            )
            continue

        if s == "yield":
            ycol = ln_txt.find("yield")
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_yield_stmt(_sh_stmt_span(merged_line_end, ln_no, ycol, len(ln_txt))),
            )
            continue

        if s.startswith("yield "):
            ycol = ln_txt.find("yield ")
            expr_txt = s[len("yield ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            if expr_col < 0:
                expr_col = ycol + len("yield ")
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_yield_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, ycol, len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                ),
            )
            continue

        parsed_typed = _sh_parse_typed_binding(s, allow_dotted_name=True)
        if parsed_typed is not None:
            typed_target, typed_ann, typed_default = parsed_typed
        else:
            typed_target, typed_ann, typed_default = "", "", ""
        if parsed_typed is not None and typed_default == "":
            target_txt = typed_target
            ann_txt = typed_ann
            ann = _sh_ann_to_type(ann_txt)
            ann_expr = _sh_ann_to_type_expr(ann)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            _maybe_bind_self_field(target_expr, None, explicit=ann)
            if isinstance(target_expr, dict):
                target_expr["type_expr"] = ann_expr
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                name_types[str(target_expr.get("id", ""))] = ann
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_ann_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    ann,
                    annotation_type_expr=ann_expr,
                    value=None,
                    declare=True,
                    decl_type=ann,
                    decl_type_expr=ann_expr,
                ),
            )
            continue

        if parsed_typed is not None and typed_default != "":
            target_txt = typed_target
            ann_txt = typed_ann
            expr_txt = typed_default
            ann = _sh_ann_to_type(ann_txt)
            ann_expr = _sh_ann_to_type_expr(ann)
            expr_col = ln_txt.find(expr_txt)
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            _maybe_bind_self_field(target_expr, None, explicit=ann)
            if isinstance(target_expr, dict):
                target_expr["type_expr"] = ann_expr
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                name_types[str(target_expr.get("id", ""))] = ann
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_ann_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    ann,
                    annotation_type_expr=ann_expr,
                    value=val_expr,
                    declare=True,
                    decl_type=ann,
                    decl_type_expr=ann_expr,
                ),
            )
            continue

        parsed_aug = _sh_parse_augassign(s)
        if parsed_aug is not None:
            target_txt, aug_op, expr_txt = parsed_aug
            op_map = {
                "+=": "Add",
                "-=": "Sub",
                "*=": "Mult",
                "/=": "Div",
                "//=": "FloorDiv",
                "%=": "Mod",
                "&=": "BitAnd",
                "|=": "BitOr",
                "^=": "BitXor",
                "<<=": "LShift",
                ">>=": "RShift",
            }
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_ty = "unknown"
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                target_ty = name_types.get(str(target_expr.get("id", "")), "unknown")
            decl_type: str | None = None
            if target_ty != "unknown":
                decl_type = target_ty
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_augassign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    op_map[aug_op],
                    val_expr,
                    declare=False,
                    decl_type=decl_type,
                )
            )
            continue

        m_tasg: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
        if m_tasg is not None:
            n1 = re.group(m_tasg, 1)
            n2 = re.group(m_tasg, 2)
            expr_txt = re.strip_group(m_tasg, 3)
            expr_col = ln_txt.find(expr_txt)
            rhs = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            c1 = ln_txt.find(n1)
            c2 = ln_txt.find(n2, c1 + len(n1))
            if (
                isinstance(rhs, dict)
                and rhs.get("kind") == "Tuple"
                and len(rhs.get("elements", [])) == 2
                and isinstance(rhs.get("elements")[0], dict)
                and isinstance(rhs.get("elements")[1], dict)
                and rhs.get("elements")[0].get("kind") == "Name"
                and rhs.get("elements")[1].get("kind") == "Name"
                and str(rhs.get("elements")[0].get("id", "")) == n2
                and str(rhs.get("elements")[1].get("id", "")) == n1
            ):
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                    _sh_make_swap_stmt(
                        _sh_stmt_span(merged_line_end, ln_no, c1, len(ln_txt)),
                        _sh_make_name_expr(
                            _sh_span(ln_no, c1, c1 + len(n1)),
                            n1,
                            resolved_type=name_types.get(n1, "unknown"),
                        ),
                        _sh_make_name_expr(
                            _sh_span(ln_no, c2, c2 + len(n2)),
                            n2,
                            resolved_type=name_types.get(n2, "unknown"),
                        ),
                    )
                )
                continue
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_tuple_destructure_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, c1, len(ln_txt)),
                    line_no=ln_no,
                    first_name=n1,
                    first_col=c1,
                    first_type=name_types.get(n1, "unknown"),
                    second_name=n2,
                    second_col=c2,
                    second_type=name_types.get(n2, "unknown"),
                    value=rhs,
                ),
            )
            continue

        asg_split = _sh_split_top_level_assign(s)
        if asg_split is not None:
            target_txt, expr_txt = asg_split
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            decl_type = val_expr.get("resolved_type", "unknown")
            _maybe_bind_self_field(target_expr, str(decl_type) if isinstance(decl_type, str) else "")
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    name_types[nm] = str(decl_type)
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    val_expr,
                    declare=True,
                    declare_init=True,
                    decl_type=str(decl_type),
                ),
            )
            continue

        expr_col = len(ln_txt) - len(ln_txt.lstrip(" "))
        expr_stmt = _sh_parse_expr_lowered(s, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
        pending_blank_count = _sh_push_stmt_with_trivia(
            stmts,
            pending_leading_trivia,
            pending_blank_count,
            _sh_make_expr_stmt(expr_stmt, _sh_stmt_span(merged_line_end, ln_no, expr_col, len(ln_txt))),
        )
    return stmts


def _sh_parse_stmt_block(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """読み取り専用引数で受け取り、mutable 実体へコピーを渡す。"""
    body_lines_copy: list[tuple[int, str]] = list(body_lines)
    name_types_copy: dict[str, str] = dict(name_types)
    return _sh_parse_stmt_block_mutable(body_lines_copy, name_types=name_types_copy, scope_label=scope_label)


_SH_VALUE_SAFE_CLASS_FIELD_TYPES: set[str] = {
    "bool",
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "float32",
    "float64",
    "str",
    "bytes",
    "bytearray",
}


def _sh_is_value_safe_dataclass_field_type(type_name: str) -> bool:
    """dataclass 自動 value 判定用の保守的な型チェック。"""
    t = type_name.strip()
    if t in _SH_VALUE_SAFE_CLASS_FIELD_TYPES:
        return True
    if t.startswith("tuple[") and t.endswith("]"):
        inner = t[6:-1].strip()
        if inner == "":
            return True
        parts = _sh_split_top_commas(inner)
        if len(parts) == 0:
            return False
        for part in parts:
            if not _sh_is_value_safe_dataclass_field_type(part):
                return False
        return True
    return False


def _sh_is_value_safe_dataclass_candidate(
    *,
    is_dataclass: bool,
    base: str,
    has_del: bool,
    class_body: list[dict[str, Any]],
    field_types: dict[str, str],
) -> bool:
    """参照共有が不要な dataclass を value 候補として判定する。"""
    if not is_dataclass or base != "" or has_del:
        return False
    # dataclass の自動 value は「データ保持専用クラス」に限定する。
    for st in class_body:
        if isinstance(st, dict) and st.get("kind") == "FunctionDef":
            return False
    if len(field_types) == 0:
        return True
    for field_t in field_types.values():
        if not isinstance(field_t, str):
            return False
        if not _sh_is_value_safe_dataclass_field_type(field_t):
            return False
    return True


def convert_source_to_east_self_hosted(source: str, filename: str) -> dict[str, Any]:
    """Python ソースを self-hosted パーサで EAST Module に変換する。"""
    source = _sh_strip_utf8_bom(source)
    lines = source.splitlines()
    leading_file_comments: list[str] = []
    leading_file_trivia: list[dict[str, Any]] = []
    for ln in lines:
        s = ln.strip()
        if s == "":
            if len(leading_file_comments) > 0:
                leading_file_trivia.append(_sh_make_trivia_blank(1))
            continue
        if s.startswith("#"):
            text = s[1:].lstrip()
            leading_file_comments.append(text)
            leading_file_trivia.append(_sh_make_trivia_comment(text))
            continue
        break

    class_method_return_types: dict[str, dict[str, str]] = {}
    class_base: dict[str, str | None] = {}
    fn_returns: dict[str, str] = {}
    pre_import_symbol_bindings: dict[str, dict[str, str]] = {}
    pre_import_module_bindings: dict[str, str] = {}
    type_aliases: dict[str, str] = _sh_default_type_aliases()

    cur_cls: str | None = None
    cur_cls_indent = 0
    for ln_no, ln in enumerate(lines, start=1):
        s = _sh_strip_inline_comment(ln.strip())
        if s == "":
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if cur_cls is not None and indent <= cur_cls_indent and not s.startswith("#"):
            cur_cls = None
        if cur_cls is None and indent == 0:
            m_import = re.match(r"^import\s+(.+)$", s, flags=re.S)
            if m_import is not None:
                names_txt = re.strip_group(m_import, 1)
                raw_parts: list[str] = []
                for p in names_txt.split(","):
                    p2 = p.strip()
                    if p2 != "":
                        raw_parts.append(p2)
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                    if parsed_alias is None:
                        continue
                    mod_name, as_name_txt = parsed_alias
                    bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                    if bind_name != "":
                        pre_import_module_bindings[bind_name] = mod_name
                continue
            m_import_from = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
            if m_import_from is not None:
                mod_txt = re.strip_group(m_import_from, 1)
                names_txt = re.strip_group(m_import_from, 2)
                if names_txt != "*":
                    raw_parts: list[str] = []
                    for p in names_txt.split(","):
                        p2 = p.strip()
                        if p2 != "":
                            raw_parts.append(p2)
                    for part in raw_parts:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_txt, as_name = parsed_alias
                        alias_name = as_name if as_name != "" else sym_txt
                        if alias_name != "":
                            pre_import_symbol_bindings[alias_name] = _sh_make_import_symbol_binding(
                                mod_txt,
                                sym_txt,
                            )
                if mod_txt == "typing":
                    raw_parts: list[str] = []
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts.append(p2)
                    for part in raw_parts:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_txt, as_name = parsed_alias
                        alias_name = as_name if as_name != "" else sym_txt
                        target = _sh_typing_alias_to_type_name(sym_txt)
                        if target != "":
                            type_aliases[alias_name] = target
                continue
            asg_pre = _sh_split_top_level_assign(s)
            if asg_pre is not None:
                pre_left, pre_right = asg_pre
                _sh_register_type_alias(type_aliases, pre_left, pre_right)
                continue
        cls_hdr_info = _sh_parse_class_header_base_list(s)
        if cls_hdr_info is not None:
            cls_name_info, bases_info = cls_hdr_info
            if len(bases_info) > 1:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"multiple inheritance is not supported: class '{cls_name_info}'",
                    source_span=_sh_span(ln_no, 0, len(ln)),
                    hint="Use single inheritance (`class Child(Base):`) or composition.",
                )
        cls_hdr = _sh_parse_class_header(s)
        if cls_hdr is not None:
            cur_cls_name, cur_base = cls_hdr
            cur_cls = cur_cls_name
            cur_cls_indent = indent
            if cur_base != "":
                class_base[cur_cls_name] = cur_base
            else:
                class_base[cur_cls_name] = None
            if cur_cls_name not in class_method_return_types:
                empty_methods: dict[str, str] = {}
                class_method_return_types[cur_cls_name] = empty_methods
            continue
        if cur_cls is None:
            sig_line_scan, _inline_scan = _sh_split_def_header_and_inline_stmt(s)
            sig = _sh_parse_def_sig(ln_no, sig_line_scan)
            if sig is not None:
                fn_returns[str(sig["name"])] = str(sig["ret"])
            continue
        cur_cls_name: str = cur_cls
        sig_line_scan, _inline_scan = _sh_split_def_header_and_inline_stmt(s)
        sig = _sh_parse_def_sig(ln_no, sig_line_scan, in_class=cur_cls_name)
        if sig is not None:
            methods: dict[str, str] = class_method_return_types[cur_cls_name]
            methods[str(sig["name"])] = str(sig["ret"])
            class_method_return_types[cur_cls_name] = methods

    _sh_set_parse_context(fn_returns, class_method_return_types, class_base, type_aliases)
    _SH_IMPORT_SYMBOLS.clear()
    _SH_IMPORT_SYMBOLS.update(pre_import_symbol_bindings)
    _SH_IMPORT_MODULES.clear()
    _SH_IMPORT_MODULES.update(pre_import_module_bindings)

    body_items: list[dict[str, Any]] = []
    main_stmts: list[dict[str, Any]] = []
    import_module_bindings: dict[str, str] = {}
    import_symbol_bindings: dict[str, dict[str, str]] = {}
    import_bindings: list[dict[str, Any]] = []
    import_binding_names: set[str] = set()
    first_item_attached = False
    pending_dataclass = False
    pending_dataclass_options: dict[str, bool] = {}
    pending_top_level_decorators: list[str] = []

    top_lines: list[tuple[int, str]] = []
    line_idx = 1
    while line_idx <= len(lines):
        top_lines.append((line_idx, lines[line_idx - 1]))
        line_idx += 1
    top_merged_lines, top_merged_end = _sh_merge_logical_lines(top_lines)
    top_merged_map: dict[int, str] = {}
    top_merged_index: dict[int, int] = {}
    for top_idx, top_pair in enumerate(top_merged_lines):
        top_ln_no, top_txt = top_pair
        top_merged_map[int(top_ln_no)] = str(top_txt)
        top_merged_index[int(top_ln_no)] = int(top_idx)
    i = 1
    while i <= len(lines):
        ln_obj = top_merged_map.get(i, lines[i - 1])
        ln: str = str(ln_obj)
        logical_end_pair = top_merged_end.get(i, (i, len(lines[i - 1])))
        logical_end = int(logical_end_pair[0])
        raw_s = ln.strip()
        s = _sh_strip_inline_comment(raw_s)
        _sh_raise_if_trailing_stmt_terminator(s, line_no=i, line_text=ln)
        if s == "" or s.startswith("#"):
            i += 1
            continue
        if ln.startswith(" "):
            i += 1
            continue
        if s.startswith("@"):
            dec_name = s[1:].strip()
            if _sh_is_dataclass_decorator(
                dec_name,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
            ):
                pending_dataclass = True
                _dec_head, args_txt = _sh_parse_decorator_head_and_args(dec_name)
                if args_txt != "":
                    parsed_opts = _sh_parse_dataclass_decorator_options(
                        args_txt,
                        line_no=i,
                        line_text=ln,
                    )
                    for k_opt, v_opt in parsed_opts.items():
                        pending_dataclass_options[k_opt] = v_opt
            elif dec_name != "":
                pending_top_level_decorators.append(dec_name)
            i += 1
            continue

        ln_main = s
        is_main_guard = False
        if ln_main.startswith("if ") and ln_main.endswith(":"):
            cond = ln_main[3:-1].strip()
            if cond in {
                "__name__ == \"__main__\"",
                "__name__ == '__main__'",
                "\"__main__\" == __name__",
                "'__main__' == __name__",
            }:
                is_main_guard = True
        if is_main_guard:
            block: list[tuple[int, str]] = []
            if i < len(top_lines):
                block, block_end_idx = _sh_collect_indented_block(top_lines, i, 0)
                j = block_end_idx + 1
            main_name_types: dict[str, str] = {}
            main_stmts = _sh_parse_stmt_block(block, name_types=main_name_types, scope_label="__main__")
            i = j
            continue
        sig_line_full: str = s
        sig_line, inline_fn_stmt = _sh_split_def_header_and_inline_stmt(sig_line_full)
        sig_end_line = logical_end
        sig = _sh_parse_def_sig(i, sig_line)
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types: dict[str, str] = dict(sig["arg_types"])
            arg_type_exprs_obj: Any = sig.get("arg_type_exprs")
            arg_type_exprs: dict[str, Any] = arg_type_exprs_obj if isinstance(arg_type_exprs_obj, dict) else {}
            arg_order: list[str] = list(sig["arg_order"])
            arg_defaults_raw_obj: Any = sig.get("arg_defaults")
            arg_defaults_raw: dict[str, Any] = arg_defaults_raw_obj if isinstance(arg_defaults_raw_obj, dict) else {}
            block: list[tuple[int, str]] = []
            j = sig_end_line + 1
            if inline_fn_stmt != "":
                block = [(i, "    " + inline_fn_stmt)]
                j = i + 1
            else:
                block, block_end_idx = _sh_collect_indented_block(top_lines, j - 1, 0)
                j = block_end_idx + 1
                if len(block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser requires non-empty function body '{fn_name}'",
                        source_span=_sh_span(i, 0, len(sig_line)),
                        hint="Add return or assignment statements in function body.",
                    )
            stmts = _sh_parse_stmt_block(block, name_types=dict(arg_types), scope_label=fn_name)
            docstring, stmts = _sh_extract_leading_docstring(stmts)
            fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, stmts)
            yield_types = _sh_collect_yield_value_types(stmts)
            is_generator = len(yield_types) > 0
            fn_ret_effective = fn_ret
            yield_value_type = "unknown"
            if is_generator:
                fn_ret_effective, yield_value_type = _sh_make_generator_return_type(fn_ret, yield_types)
            fn_ret_type_expr = _sh_ann_to_type_expr(fn_ret_effective)
            arg_defaults: dict[str, Any] = {}
            arg_index_map: dict[str, int] = {}
            for arg_pos, arg_name in enumerate(arg_order):
                arg_index_map[arg_name] = int(arg_pos)
            arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, stmts)
            for arg_name in arg_order:
                if arg_name in arg_defaults_raw:
                    default_obj: Any = arg_defaults_raw[arg_name]
                    default_txt: str = str(default_obj).strip()
                    if default_txt != "":
                        default_col = sig_line.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = _sh_parse_expr_lowered(
                            default_txt,
                            ln_no=i,
                            col=default_col,
                            name_types=dict(arg_types),
                        )
            fn_decorators = list(pending_top_level_decorators)
            pending_top_level_decorators = []
            runtime_abi_meta = _sh_collect_runtime_abi_metadata(
                fn_decorators,
                arg_order=arg_order,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
                line_no=i,
                line_text=ln,
            )
            template_meta = _sh_collect_template_metadata(
                fn_decorators,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
                line_no=i,
                line_text=ln,
            )
            item = _sh_make_function_def_stmt(
                fn_name,
                _sh_block_end_span(block, i, 0, len(ln), len(block)),
                arg_types,
                arg_order,
                fn_ret_effective,
                stmts,
                arg_type_exprs=arg_type_exprs,
                arg_defaults=arg_defaults,
                arg_index=arg_index_map,
                return_type_expr=fn_ret_type_expr,
                arg_usage=arg_usage_map,
                decorators=list(fn_decorators) if len(fn_decorators) > 0 else None,
                leading_comments=[],
                leading_trivia=[],
                docstring=docstring,
                is_generator=is_generator,
                yield_value_type=yield_value_type,
            )
            if runtime_abi_meta is not None or template_meta is not None:
                item["meta"] = _sh_make_decl_meta(
                    runtime_abi_v1=runtime_abi_meta,
                    template_v1=template_meta,
                )
            fn_returns[fn_name] = fn_ret_effective
            _SH_FN_RETURNS[fn_name] = fn_ret_effective
            if not first_item_attached:
                item["leading_comments"] = list(leading_file_comments)
                item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(item)
            i = j
            continue

        if len(pending_top_level_decorators) > 0:
            for decorator_text in pending_top_level_decorators:
                if _sh_is_abi_decorator(
                    decorator_text,
                    import_module_bindings=import_module_bindings,
                    import_symbol_bindings=import_symbol_bindings,
                ):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="@abi is supported on top-level functions only",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Move @abi to a top-level runtime helper function definition.",
                    )
                if _sh_is_template_decorator(
                    decorator_text,
                    import_module_bindings=import_module_bindings,
                    import_symbol_bindings=import_symbol_bindings,
                ):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="@template is supported on top-level functions only",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Move @template to a top-level runtime helper function definition.",
                    )
            pending_top_level_decorators = []
        m_import: re.Match | None = re.match(r"^import\s+(.+)$", s, flags=re.S)
        if m_import is not None:
            names_txt = re.strip_group(m_import, 1)
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="import statement has no module names",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name, as_name_txt = parsed_alias
                if mod_name == "typing":
                    # `typing` は注釈専用モジュールとして扱い、ImportBinding/EAST へは出さない。
                    continue
                if mod_name == "dataclasses":
                    # `dataclasses` は decorator 解決専用モジュールとして扱う（no-op import）。
                    bind_name_dc = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                    import_module_bindings[bind_name_dc] = mod_name
                    _sh_register_import_module(bind_name_dc, mod_name)
                    continue
                bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                _sh_register_import_module(bind_name, mod_name)
                if _sh_is_host_only_alias(bind_name):
                    continue
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name="",
                    local_name=bind_name,
                    binding_kind="module",
                    source_file=filename,
                    source_line=i,
                )
                aliases.append(_sh_make_import_alias(mod_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                body_items.append(_sh_make_import_stmt(_sh_span(i, 0, len(ln)), aliases))
            i = logical_end + 1
            continue
        if s.startswith("from "):
            marker = " import "
            pos = s.find(marker)
            if pos >= 0:
                mod_txt = s[5:pos].strip()
                if mod_txt.startswith("."):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="relative import is not supported",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use absolute import form: `from module import name`.",
                    )
        m_import_from: re.Match | None = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
        if m_import_from is not None:
            mod_name = re.strip_group(m_import_from, 1)
            names_txt = re.strip_group(m_import_from, 2)
            if mod_name == "typing":
                # `typing` の from-import は型別名解決にだけ使い、依存/AST には残さない。
                raw_parts_typing: list[str] = []
                if names_txt != "*":
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts_typing.append(p2)
                for part in raw_parts_typing:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        continue
                    sym_name, as_name_txt = parsed_alias
                    alias_name = as_name_txt if as_name_txt != "" else sym_name
                    target = _sh_typing_alias_to_type_name(sym_name)
                    if target != "":
                        type_aliases[alias_name] = target
                i = logical_end + 1
                continue
            if mod_name == "dataclasses":
                # `from dataclasses import ...` は decorator 解決専用で、依存/AST には残さない。
                if names_txt == "*":
                    i = logical_end + 1
                    continue
                raw_parts_dc: list[str] = []
                for p in names_txt.split(","):
                    p2: str = p.strip()
                    if p2 != "":
                        raw_parts_dc.append(p2)
                if len(raw_parts_dc) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from-import statement has no symbol names",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` form.",
                    )
                for part in raw_parts_dc:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported from-import clause: {part}",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Use `from module import name` or `... as alias`.",
                        )
                    sym_name, as_name_txt = parsed_alias
                    bind_name_dc = as_name_txt if as_name_txt != "" else sym_name
                    import_symbol_bindings[bind_name_dc] = _sh_make_import_symbol_binding(
                        mod_name,
                        sym_name,
                    )
                    _sh_register_import_symbol(bind_name_dc, mod_name, sym_name)
                i = logical_end + 1
                continue
            if mod_name == "__future__":
                if names_txt == "*":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from __future__ import * is not supported",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from __future__ import annotations` only.",
                    )
                raw_parts: list[str] = []
                for p in names_txt.split(","):
                    p2: str = p.strip()
                    if p2 != "":
                        raw_parts.append(p2)
                if len(raw_parts) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from-import statement has no symbol names",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` form.",
                    )
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported from-import clause: {part}",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Use `from module import name` or `... as alias`.",
                        )
                    sym_name, as_name_txt = parsed_alias
                    if sym_name != "annotations" or as_name_txt != "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported __future__ feature: {part}",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Only `from __future__ import annotations` is supported.",
                        )
                # `from __future__ import annotations` is frontend-only and does not appear in EAST.
                i = logical_end + 1
                continue
            if names_txt == "*":
                wildcard_local = "__wildcard__" + mod_name.replace(".", "_")
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name="*",
                    local_name=wildcard_local,
                    binding_kind="wildcard",
                    source_file=filename,
                    source_line=i,
                )
                body_items.append(
                    _sh_make_import_from_stmt(
                        _sh_span(i, 0, len(ln)),
                        mod_name,
                        [_sh_make_import_alias("*")],
                    )
                )
                i = logical_end + 1
                continue
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="from-import statement has no symbol names",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` or `... as alias`.",
                )
                sym_name, as_name_txt = parsed_alias
                bind_name = as_name_txt if as_name_txt != "" else sym_name
                if _sh_is_host_only_alias(bind_name):
                    _sh_register_import_symbol(bind_name, mod_name, sym_name)
                    continue
                # `Enum/IntEnum/IntFlag` は class 定義の lowering で吸収されるため、
                # 依存ヘッダ解決用の ImportBinding には積まない。
                if not (mod_name == "pytra.std.enum" and sym_name in {"Enum", "IntEnum", "IntFlag"}):
                    _sh_append_import_binding(
                        import_bindings=import_bindings,
                        import_binding_names=import_binding_names,
                        module_id=mod_name,
                        export_name=sym_name,
                        local_name=bind_name,
                        binding_kind="symbol",
                        source_file=filename,
                        source_line=i,
                    )
                    import_symbol_bindings[bind_name] = _sh_make_import_symbol_binding(
                        mod_name,
                        sym_name,
                    )
                    _sh_register_import_symbol(bind_name, mod_name, sym_name)
                aliases.append(_sh_make_import_alias(sym_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                body_items.append(
                    _sh_make_import_from_stmt(
                        _sh_span(i, 0, len(ln)),
                        mod_name,
                        aliases,
                    )
                )
            i = logical_end + 1
            continue
        cls_hdr_info = _sh_parse_class_header_base_list(s)
        if cls_hdr_info is not None:
            cls_name_info, bases_info = cls_hdr_info
            if len(bases_info) > 1:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"multiple inheritance is not supported: class '{cls_name_info}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use single inheritance (`class Child(Base):`) or composition.",
                )
        cls_hdr = _sh_parse_class_header(s)
        if cls_hdr is not None:
            for decorator_text in pending_top_level_decorators:
                if _sh_is_abi_decorator(
                    decorator_text,
                    import_module_bindings=import_module_bindings,
                    import_symbol_bindings=import_symbol_bindings,
                ):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="@abi is not supported on class definitions",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use @abi on top-level runtime helper functions only.",
                    )
                if _sh_is_template_decorator(
                    decorator_text,
                    import_module_bindings=import_module_bindings,
                    import_symbol_bindings=import_symbol_bindings,
                ):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="@template is not supported on class definitions",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use @template on top-level runtime helper functions only.",
                    )
            cls_name, base = cls_hdr
            base_name = base
            is_enum_base = base_name in {"Enum", "IntEnum", "IntFlag"}
            cls_indent = len(ln) - len(ln.lstrip(" "))
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    block.append((j, bl))
                    j += 1
                    continue
                bind = len(bl) - len(bl.lstrip(" "))
                if bind <= cls_indent:
                    break
                block.append((j, bl))
                j += 1
            if len(block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser requires non-empty class body '{cls_name}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Add field or method definitions.",
                )
            class_block, _class_line_end = _sh_merge_logical_lines(block)

            field_types: dict[str, str] = {}
            class_body: list[dict[str, Any]] = []
            pending_method_decorators: list[str] = []
            class_storage_hint_override = ""
            k = 0
            while k < len(class_block):
                ln_no_raw, ln_txt_raw = class_block[k]
                ln_no = int(ln_no_raw)
                ln_txt: str = str(ln_txt_raw)
                s2 = re.sub(r"\s+#.*$", "", ln_txt).strip()
                bind = len(ln_txt) - len(ln_txt.lstrip(" "))
                if s2 == "":
                    k += 1
                    continue
                if bind == cls_indent + 4 and s2.startswith("@"):
                    dec_name = s2[1:].strip()
                    if dec_name != "":
                        if _sh_is_abi_decorator(
                            dec_name,
                            import_module_bindings=import_module_bindings,
                            import_symbol_bindings=import_symbol_bindings,
                        ):
                            raise _make_east_build_error(
                                kind="unsupported_syntax",
                                message="@abi is not supported on methods",
                                source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                hint="Use @abi on top-level runtime helper functions only.",
                            )
                        if _sh_is_template_decorator(
                            dec_name,
                            import_module_bindings=import_module_bindings,
                            import_symbol_bindings=import_symbol_bindings,
                        ):
                            raise _make_east_build_error(
                                kind="unsupported_syntax",
                                message="@template is not supported on methods",
                                source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                hint="Use @template on top-level runtime helper functions only.",
                            )
                        pending_method_decorators.append(dec_name)
                    k += 1
                    continue
                if bind == cls_indent + 4 and (s2.startswith('"""') or s2.startswith("'''")):
                    q = s2[:3]
                    if s2.count(q) >= 2 and len(s2) > 3:
                        k += 1
                        continue
                    k += 1
                    while k < len(class_block):
                        _doc_no, doc_txt = class_block[k]
                        if q in doc_txt:
                            k += 1
                            break
                        k += 1
                    continue
                if bind == cls_indent + 4:
                    if s2 == "pass":
                        class_body.append(
                            _sh_make_pass_stmt(_sh_span(ln_no, 0, len(ln_txt)))
                        )
                        k += 1
                        continue
                    if s2.startswith("__pytra_class_storage_hint__") or s2.startswith("__pytra_storage_hint__"):
                        parts = s2.split("=", 1)
                        if len(parts) == 2:
                            rhs = parts[1].strip()
                            if rhs in {'"value"', "'value'"}:
                                class_storage_hint_override = "value"
                                k += 1
                                continue
                            if rhs in {'"ref"', "'ref'"}:
                                class_storage_hint_override = "ref"
                                k += 1
                                continue
                    parsed_field = _sh_parse_typed_binding(s2, allow_dotted_name=False)
                    if parsed_field is not None:
                        fname, fty_txt, fdefault = parsed_field
                        fty = _sh_ann_to_type(fty_txt)
                        fty_expr = _sh_ann_to_type_expr(fty)
                        field_types[fname] = fty
                        val_node: dict[str, Any] | None = None
                        if fdefault != "":
                            fexpr_txt = fdefault.strip()
                            fexpr_col = ln_txt.find(fexpr_txt)
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=fexpr_col, name_types={})
                        class_body.append(
                            _sh_make_ann_assign_stmt(
                                _sh_span(ln_no, ln_txt.find(fname), len(ln_txt)),
                                _sh_make_name_expr(
                                    _sh_span(ln_no, ln_txt.find(fname), ln_txt.find(fname) + len(fname)),
                                    fname,
                                    resolved_type=fty,
                                    type_expr=fty_expr,
                                ),
                                fty,
                                annotation_type_expr=fty_expr,
                                value=val_node,
                                declare=True,
                                decl_type=fty,
                                decl_type_expr=fty_expr,
                            )
                        )
                        k += 1
                        continue
                    class_assign = _sh_split_top_level_assign(s2)
                    if class_assign is not None:
                        fname, fexpr_txt = class_assign
                        fname = fname.strip()
                        fexpr_txt = fexpr_txt.strip()
                        if _sh_is_identifier(fname) and fexpr_txt != "":
                            name_col = ln_txt.find(fname)
                            if name_col < 0:
                                name_col = 0
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            if expr_col < 0:
                                expr_col = name_col + len(fname) + 1
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
                            class_body.append(
                                _sh_make_assign_stmt(
                                    _sh_span(ln_no, name_col, len(ln_txt)),
                                    _sh_make_name_expr(
                                        _sh_span(ln_no, name_col, name_col + len(fname)),
                                        fname,
                                        resolved_type=str(val_node.get("resolved_type", "unknown")),
                                    ),
                                    val_node,
                                    declare=True,
                                    declare_init=True,
                                    decl_type=str(val_node.get("resolved_type", "unknown")),
                                )
                            )
                            k += 1
                            continue
                    if is_enum_base:
                        enum_assign = _sh_split_top_level_assign(s2)
                        if enum_assign is not None:
                            fname, fexpr_txt = enum_assign
                            fname = fname.strip()
                            fexpr_txt = fexpr_txt.strip()
                            if not _sh_is_identifier(fname) or fexpr_txt == "":
                                k += 1
                                continue
                            name_col = ln_txt.find(fname)
                            if name_col < 0:
                                name_col = 0
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            if expr_col < 0:
                                expr_col = name_col + len(fname) + 1
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
                            class_body.append(
                                _sh_make_assign_stmt(
                                    _sh_span(ln_no, name_col, len(ln_txt)),
                                    _sh_make_name_expr(
                                        _sh_span(ln_no, name_col, name_col + len(fname)),
                                        fname,
                                        resolved_type=str(val_node.get("resolved_type", "unknown")),
                                    ),
                                    val_node,
                                    declare=True,
                                    declare_init=True,
                                    decl_type=str(val_node.get("resolved_type", "unknown")),
                                )
                            )
                            k += 1
                            continue
                    sig_line, inline_method_stmt = _sh_split_def_header_and_inline_stmt(s2)
                    sig = _sh_parse_def_sig(ln_no, sig_line, in_class=cls_name)
                    if sig is not None:
                        mname = str(sig["name"])
                        marg_types: dict[str, str] = dict(sig["arg_types"])
                        marg_order: list[str] = list(sig["arg_order"])
                        marg_defaults_raw_obj: Any = sig.get("arg_defaults")
                        marg_defaults_raw: dict[str, Any] = marg_defaults_raw_obj if isinstance(marg_defaults_raw_obj, dict) else {}
                        mret = str(sig["ret"])
                        method_block: list[tuple[int, str]] = []
                        m = k + 1
                        if inline_method_stmt != "":
                            method_block = [(ln_no, " " * (bind + 4) + inline_method_stmt)]
                        else:
                            while m < len(class_block):
                                n_pair: tuple[int, str] = class_block[m]
                                n_no: int = int(n_pair[0])
                                n_txt: str = str(n_pair[1])
                                if n_txt.strip() == "":
                                    t = m + 1
                                    while t < len(class_block) and class_block[t][1].strip() == "":
                                        t += 1
                                    if t >= len(class_block):
                                        break
                                    t_pair: tuple[int, str] = class_block[t]
                                    t_txt: str = str(t_pair[1])
                                    t_indent = len(t_txt) - len(t_txt.lstrip(" "))
                                    if t_indent <= bind:
                                        break
                                    method_block.append((n_no, n_txt))
                                    m += 1
                                    continue
                                n_indent = len(n_txt) - len(n_txt.lstrip(" "))
                                if n_indent <= bind:
                                    break
                                method_block.append((n_no, n_txt))
                                m += 1
                            if len(method_block) == 0:
                                raise _make_east_build_error(
                                    kind="unsupported_syntax",
                                    message=f"self_hosted parser requires non-empty method body '{cls_name}.{mname}'",
                                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                    hint="Add method statements.",
                                )
                        local_types: dict[str, str] = dict(marg_types)
                        field_names: list[str] = list(field_types.keys())
                        for fnm in field_names:
                            fty: str = field_types[fnm]
                            local_types[fnm] = fty
                        stmts = _sh_parse_stmt_block(method_block, name_types=local_types, scope_label=f"{cls_name}.{mname}")
                        docstring, stmts = _sh_extract_leading_docstring(stmts)
                        mret = _sh_infer_return_type_for_untyped_def(mret, stmts)
                        yield_types = _sh_collect_yield_value_types(stmts)
                        is_generator = len(yield_types) > 0
                        mret_effective = mret
                        yield_value_type = "unknown"
                        if is_generator:
                            mret_effective, yield_value_type = _sh_make_generator_return_type(mret, yield_types)
                        marg_defaults: dict[str, Any] = {}
                        for arg_name in marg_order:
                            if arg_name in marg_defaults_raw:
                                default_obj: Any = marg_defaults_raw[arg_name]
                                default_txt: str = str(default_obj).strip()
                                if default_txt != "":
                                    default_col = ln_txt.find(default_txt)
                                    if default_col < 0:
                                        default_col = bind
                                    marg_defaults[arg_name] = _sh_parse_expr_lowered(
                                        default_txt,
                                        ln_no=ln_no,
                                        col=default_col,
                                        name_types=local_types,
                                    )
                        if mname == "__init__":
                            for st in stmts:
                                if st.get("kind") == "Assign":
                                    tgt = st.get("target")
                                    tgt_value: Any = None
                                    if isinstance(tgt, dict):
                                        tgt_value = tgt.get("value")
                                    tgt_value_dict: dict[str, Any] | None = None
                                    if isinstance(tgt_value, dict):
                                        tgt_value_dict = tgt_value
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and tgt_value_dict is not None
                                        and tgt_value_dict.get("kind") == "Name"
                                        and tgt_value_dict.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        if fname != "":
                                            st_value = st.get("value")
                                            st_value_rt: Any = None
                                            if isinstance(st_value, dict):
                                                st_value_rt = st_value.get("resolved_type")
                                            t_val: Any = st.get("decl_type")
                                            if not isinstance(t_val, str) or t_val == "":
                                                t_val = st_value_rt
                                            if isinstance(t_val, str) and t_val != "":
                                                field_types[fname] = t_val
                                if st.get("kind") == "AnnAssign":
                                    tgt = st.get("target")
                                    tgt_value: Any = None
                                    if isinstance(tgt, dict):
                                        tgt_value = tgt.get("value")
                                    tgt_value_dict: dict[str, Any] | None = None
                                    if isinstance(tgt_value, dict):
                                        tgt_value_dict = tgt_value
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and tgt_value_dict is not None
                                        and tgt_value_dict.get("kind") == "Name"
                                        and tgt_value_dict.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        ann = st.get("annotation")
                                        if fname != "" and isinstance(ann, str) and ann != "":
                                            field_types[fname] = ann
                        arg_index_map: dict[str, int] = {}
                        arg_pos = 0
                        while arg_pos < len(marg_order):
                            arg_name = marg_order[arg_pos]
                            arg_index_map[arg_name] = arg_pos
                            arg_pos += 1
                        arg_usage_map = _sh_build_arg_usage_map(marg_order, marg_types, stmts)
                        if cls_name in class_method_return_types:
                            methods_map = class_method_return_types[cls_name]
                            methods_map[mname] = mret_effective
                            class_method_return_types[cls_name] = methods_map
                        if cls_name in _SH_CLASS_METHOD_RETURNS:
                            methods_map2 = _SH_CLASS_METHOD_RETURNS[cls_name]
                            methods_map2[mname] = mret_effective
                            _SH_CLASS_METHOD_RETURNS[cls_name] = methods_map2
                        class_body.append(
                            _sh_make_function_def_stmt(
                                mname,
                                _sh_block_end_span(method_block, ln_no, bind, len(ln_txt), len(method_block)),
                                marg_types,
                                marg_order,
                                mret_effective,
                                stmts,
                                arg_defaults=marg_defaults,
                                arg_index=arg_index_map,
                                arg_usage=arg_usage_map,
                                decorators=list(pending_method_decorators),
                                docstring=docstring,
                                is_generator=is_generator,
                                yield_value_type=yield_value_type,
                            )
                        )
                        pending_method_decorators = []
                        k = m
                        continue
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse class statement: {s2}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use field annotation or method definitions in class body.",
                )

            storage_hint_override = class_storage_hint_override
            base_value: str | None = None
            if base != "":
                base_value = base

            cls_item = _sh_make_class_def_stmt(
                cls_name,
                _sh_block_end_span(block, i, 0, len(ln), len(block)),
                field_types,
                class_body,
                base=base_value,
                dataclass=pending_dataclass,
                dataclass_options=dict(pending_dataclass_options) if len(pending_dataclass_options) > 0 else None,
            )
            static_field_names: set[str] = set()
            if not pending_dataclass:
                for st in class_body:
                    if st.get("kind") == "AnnAssign":
                        tgt = st.get("target")
                        if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                            fname = str(tgt.get("id", ""))
                            if fname != "":
                                static_field_names.add(fname)
            has_del = any(
                isinstance(st, dict) and st.get("kind") == "FunctionDef" and st.get("name") == "__del__"
                for st in class_body
            )
            instance_field_names: set[str] = set()
            for field_name in field_types.keys():
                if field_name not in static_field_names:
                    instance_field_names.add(field_name)
            # conservative hint:
            # - classes with instance state / __del__ / inheritance should keep reference semantics
            # - stateless, non-inherited classes can be value candidates
            if storage_hint_override != "":
                cls_item["class_storage_hint"] = storage_hint_override
            elif _sh_is_value_safe_dataclass_candidate(
                is_dataclass=pending_dataclass,
                base=base,
                has_del=has_del,
                class_body=class_body,
                field_types=field_types,
            ):
                cls_item["class_storage_hint"] = "value"
            elif base_name in {"Enum", "IntEnum", "IntFlag"}:
                cls_item["class_storage_hint"] = "value"
            elif len(instance_field_names) == 0 and not has_del and base == "":
                cls_item["class_storage_hint"] = "value"
            else:
                cls_item["class_storage_hint"] = "ref"
            pending_dataclass = False
            pending_dataclass_options.clear()
            if not first_item_attached:
                cls_item["leading_comments"] = list(leading_file_comments)
                cls_item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(cls_item)
            i = j
            continue

        top_indent = len(ln) - len(ln.lstrip(" "))
        if s.startswith("if ") and s.endswith(":"):
            cur_idx_obj = top_merged_index.get(i)
            if isinstance(cur_idx_obj, int):
                cur_idx = int(cur_idx_obj)
                then_block, j_idx = _sh_collect_indented_block(top_merged_lines, cur_idx + 1, top_indent)
                if len(then_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="if body is missing in 'module'",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Add indented if-body.",
                    )
                _else_stmt_list, j_idx = _sh_parse_if_tail(
                    start_idx=j_idx,
                    parent_indent=top_indent,
                    body_lines=top_merged_lines,
                    name_types={},
                    scope_label="module",
                )
                stmt_chunk = top_merged_lines[cur_idx:j_idx]
                parsed_items = _sh_parse_stmt_block(stmt_chunk, name_types={}, scope_label="module")
                if not first_item_attached and len(parsed_items) > 0:
                    first_item = parsed_items[0]
                    if isinstance(first_item, dict):
                        first_item["leading_comments"] = list(leading_file_comments)
                        first_item["leading_trivia"] = list(leading_file_trivia)
                        first_item_attached = True
                for parsed_item in parsed_items:
                    body_items.append(parsed_item)
                if j_idx < len(top_merged_lines):
                    i = int(top_merged_lines[j_idx][0])
                else:
                    i = len(lines) + 1
                continue

        if s.startswith("for "):
            cur_idx_obj = top_merged_index.get(i)
            if isinstance(cur_idx_obj, int):
                cur_idx = int(cur_idx_obj)
                for_full = s[len("for ") :].strip()
                inline_for = False
                if not for_full.endswith(":"):
                    inline_for = _sh_split_top_level_colon(for_full) is not None
                j_idx = cur_idx + 1
                if for_full.endswith(":"):
                    body_block, j_idx = _sh_collect_indented_block(top_merged_lines, cur_idx + 1, top_indent)
                    if len(body_block) == 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="for body is missing in 'module'",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Add indented for-body.",
                        )
                elif not inline_for:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse for statement: {s}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `for target in iterable:` form.",
                    )
                stmt_chunk = top_merged_lines[cur_idx:j_idx]
                parsed_items = _sh_parse_stmt_block(stmt_chunk, name_types={}, scope_label="module")
                if not first_item_attached and len(parsed_items) > 0:
                    first_item = parsed_items[0]
                    if isinstance(first_item, dict):
                        first_item["leading_comments"] = list(leading_file_comments)
                        first_item["leading_trivia"] = list(leading_file_trivia)
                        first_item_attached = True
                for parsed_item in parsed_items:
                    body_items.append(parsed_item)
                if j_idx < len(top_merged_lines):
                    i = int(top_merged_lines[j_idx][0])
                else:
                    i = len(lines) + 1
                continue

        parsed_top_typed = _sh_parse_typed_binding(s, allow_dotted_name=False)
        if parsed_top_typed is not None:
            top_name, top_ann, top_default = parsed_top_typed
        else:
            top_name, top_ann, top_default = "", "", ""
        if parsed_top_typed is not None and top_default != "":
            name = top_name
            ann_txt = top_ann
            expr_txt = top_default
            ann = _sh_ann_to_type(ann_txt)
            ann_expr = _sh_ann_to_type_expr(ann)
            expr_col = ln.find(expr_txt)
            value_expr = _sh_parse_expr_lowered(expr_txt, ln_no=i, col=expr_col, name_types={})
            ann_item = _sh_make_ann_assign_stmt(
                _sh_span(i, ln.find(name), len(ln)),
                _sh_make_name_expr(
                    _sh_span(i, ln.find(name), ln.find(name) + len(name)),
                    name,
                    resolved_type=ann,
                    type_expr=ann_expr,
                ),
                ann,
                annotation_type_expr=ann_expr,
                value=value_expr,
                declare=True,
                decl_type=ann,
                decl_type_expr=ann_expr,
            )
            extern_var_meta = _sh_collect_extern_var_metadata(
                target_name=name,
                annotation=ann,
                value_expr=value_expr,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
            )
            if extern_var_meta is not None:
                ann_item["meta"] = _sh_make_decl_meta(extern_var_v1=extern_var_meta)
            body_items.append(ann_item)
            i = logical_end + 1
            continue

        asg_top = _sh_split_top_level_assign(s)
        if asg_top is not None:
            asg_left, asg_right = asg_top
            target_txt = asg_left.strip()
            expr_txt = asg_right.strip()
            expr_col = ln.find(expr_txt)
            if expr_col < 0:
                expr_col = 0
            target_col = ln.find(target_txt)
            if target_col < 0:
                target_col = 0
            target_node = _sh_parse_expr_lowered(target_txt, ln_no=i, col=target_col, name_types={})
            val_node = _sh_parse_expr_lowered(expr_txt, ln_no=i, col=expr_col, name_types={})
            decl_type = str(val_node.get("resolved_type", "unknown"))
            declare_name = isinstance(target_node, dict) and target_node.get("kind") == "Name"
            body_items.append(
                _sh_make_assign_stmt(
                    _sh_span(i, target_col, len(ln)),
                    target_node,
                    val_node,
                    declare=declare_name,
                    declare_init=declare_name,
                    decl_type=decl_type if declare_name else None,
                )
            )
            i = logical_end + 1
            continue

        if (s.startswith('"""') and s.endswith('"""')) or (s.startswith("'''") and s.endswith("'''")):
            # Module-level docstring / standalone string expression.
            body_items.append(
                _sh_make_expr_stmt(
                    _sh_parse_expr_lowered(s, ln_no=i, col=0, name_types={}),
                    _sh_span(i, 0, len(ln)),
                )
            )
            i = logical_end + 1
            continue

        expr_col = len(ln) - len(ln.lstrip(" "))
        body_items.append(
            _sh_make_expr_stmt(
                _sh_parse_expr_lowered(s, ln_no=i, col=expr_col, name_types={}),
                _sh_span(i, expr_col, len(ln)),
            )
        )
        i = logical_end + 1
        continue

    renamed_symbols: dict[str, str] = {}
    for item in body_items:
        if item.get("kind") == "FunctionDef" and item.get("name") == "main":
            renamed_symbols["main"] = "__pytra_main"
            item["name"] = "__pytra_main"

    # 互換メタデータは ImportBinding 正本から導出する。
    import_module_bindings = {}
    import_symbol_bindings = {}
    qualified_symbol_refs: list[dict[str, str]] = []
    import_resolution_bindings: list[dict[str, Any]] = []
    for binding in import_bindings:
        import_resolution_bindings.append(_sh_make_import_resolution_binding(binding))
        module_id, export_name, local_name, binding_kind, _source_file, _source_line = _sh_import_binding_fields(binding)
        if module_id == "" or local_name == "":
            continue
        if binding_kind == "module":
            import_module_bindings[local_name] = module_id
            continue
        if binding_kind == "symbol" and export_name != "":
            import_symbol_bindings[local_name] = _sh_make_import_symbol_binding(module_id, export_name)
            qualified_symbol_refs.append(_sh_make_qualified_symbol_ref(module_id, export_name, local_name))

    out = _sh_make_module_root(
        filename=filename,
        body_items=body_items,
        main_stmts=main_stmts,
        renamed_symbols=renamed_symbols,
        import_resolution_bindings=import_resolution_bindings,
        qualified_symbol_refs=qualified_symbol_refs,
        import_bindings=import_bindings,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    )
    sync_type_expr_mirrors(out)
    return validate_template_module(validate_runtime_abi_module(out))


def convert_source_to_east_with_backend(source: str, filename: str, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """指定バックエンドでソースを EAST へ変換する統一入口。"""
    if parser_backend != "self_hosted":
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"unknown parser backend: {parser_backend}",
            source_span={},
            hint="Use parser_backend=self_hosted.",
        )
    return convert_source_to_east_self_hosted(source, filename)


def convert_path(input_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """Python ファイルを読み込み、EAST ドキュメントへ変換する。"""
    source = input_path.read_text(encoding="utf-8")
    return convert_source_to_east_with_backend(source, str(input_path), parser_backend=parser_backend)
