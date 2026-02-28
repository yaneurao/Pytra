"""EAST -> TypeScript transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile, transpile_to_js


def load_ts_profile() -> dict[str, Any]:
    """TypeScript backend で利用する profile を返す。"""
    return load_js_profile()


def transpile_to_typescript(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを TypeScript ソース（JS互換）へ変換する。"""
    js = transpile_to_js(east_doc)
    out = js
    if out != "" and not out.endswith("\n"):
        out += "\n"
    return out
