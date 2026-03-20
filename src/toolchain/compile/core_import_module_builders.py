#!/usr/bin/env python3
"""Shared import/module builder helpers for self-hosted EAST parsing."""

from __future__ import annotations

from typing import Any


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
    make_stmt_node: Any,
    source_span: dict[str, Any],
    names: list[dict[str, str | None]],
) -> dict[str, Any]:
    """`Import` 文 node を構築する。"""
    node = make_stmt_node("Import", source_span)
    node["names"] = names
    return node


def _sh_make_import_from_stmt(
    make_stmt_node: Any,
    source_span: dict[str, Any],
    module: str,
    names: list[dict[str, str | None]],
    *,
    level: int = 0,
) -> dict[str, Any]:
    """`ImportFrom` 文 node を構築する。"""
    node = make_stmt_node("ImportFrom", source_span)
    node["module"] = module
    node["names"] = names
    node["level"] = level
    return node


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
    make_node: Any,
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
    return make_node(
        "Module",
        source_path=filename,
        source_span=source_span,
        body=body_items,
        main_guard_body=main_stmts,
        renamed_symbols=renamed_symbols,
        meta=meta,
    )
