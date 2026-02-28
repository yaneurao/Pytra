"""Lua emitter helpers (native only)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile

from .lua_native_emitter import transpile_to_lua_native


def load_lua_profile() -> dict[str, Any]:
    """Lua backend 用 profile を返す。"""
    return load_js_profile()


def transpile_to_lua(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """互換 API: native emitter へ委譲する。"""
    _ = js_entry_path
    return transpile_to_lua_native(east_doc)


__all__ = ["load_lua_profile", "transpile_to_lua", "transpile_to_lua_native"]

