"""Scala emitter helpers (native only)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile

from .scala_native_emitter import transpile_to_scala_native


def load_scala_profile() -> dict[str, Any]:
    """Scala backend で利用する profile を返す。"""
    return load_js_profile()


def transpile_to_scala(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """互換 API: native emitter へ委譲する。"""
    _ = js_entry_path
    return transpile_to_scala_native(east_doc)


__all__ = ["load_scala_profile", "transpile_to_scala", "transpile_to_scala_native"]
