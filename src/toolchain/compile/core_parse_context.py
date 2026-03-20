#!/usr/bin/env python3
"""Shared EAST parser context state for self-hosted expression parsing."""

from __future__ import annotations

from typing import Any

from toolchain.compile.core_type_semantics import _sh_default_type_aliases

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
