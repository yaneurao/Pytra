"""Kotlin emitter helpers (native only)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile

from .kotlin_native_emitter import transpile_to_kotlin_native


def load_kotlin_profile() -> dict[str, Any]:
    """Kotlin backend で利用する profile を返す。"""
    return load_js_profile()


def transpile_to_kotlin(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """互換 API: native emitter へ委譲する。"""
    _ = js_entry_path
    return transpile_to_kotlin_native(east_doc)


__all__ = ["load_kotlin_profile", "transpile_to_kotlin", "transpile_to_kotlin_native"]
