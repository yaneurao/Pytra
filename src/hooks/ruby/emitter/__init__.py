"""Ruby emitter helpers (native only)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile

from .ruby_native_emitter import transpile_to_ruby_native


def load_ruby_profile() -> dict[str, Any]:
    """Ruby backend 用 profile を返す。"""
    return load_js_profile()


def transpile_to_ruby(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """互換 API: native emitter へ委譲する。"""
    _ = js_entry_path
    return transpile_to_ruby_native(east_doc)


__all__ = ["load_ruby_profile", "transpile_to_ruby", "transpile_to_ruby_native"]
