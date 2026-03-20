"""EAST -> TypeScript transpiler."""

from __future__ import annotations

from typing import Any

from toolchain.emit.common.emitter.code_emitter import (
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
    reject_backend_typed_vararg_signatures,
)
from toolchain.emit.js.emitter.js_emitter import load_js_profile, transpile_to_js


def load_ts_profile() -> dict[str, Any]:
    """TypeScript backend で利用する profile を返す。"""
    return load_js_profile()


def transpile_to_typescript(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを TypeScript ソース（JS互換）へ変換する。"""
    reject_backend_typed_vararg_signatures(east_doc, backend_name="TS backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="TS backend")
    js = transpile_to_js(east_doc)
    out = js
    if out != "" and not out.endswith("\n"):
        out += "\n"
    return out
