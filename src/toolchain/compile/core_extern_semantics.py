#!/usr/bin/env python3
"""Self-hosted EAST extern metadata helpers."""

from __future__ import annotations

from typing import Any


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
    """`name: T = extern(...)` から ambient global metadata を抽出する。"""
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
        if isinstance(arg0, dict) and str(arg0.get("kind", "")) == "Constant" and str(arg0.get("resolved_type", "")) == "str":
            symbol = str(arg0.get("value", "")).strip()
            if symbol == "":
                return None
        else:
            # extern(expr) — expr is a Python host fallback value.
            # Transpiler ignores it and delegates to _native module.
            symbol = target_name
    else:
        return None
    return {
        "schema_version": 1,
        "symbol": symbol,
        "same_name": 1 if symbol == target_name else 0,
    }
