"""Swift emitter helpers (native only)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile

from .swift_native_emitter import transpile_to_swift_native


def load_swift_profile() -> dict[str, Any]:
    """Swift backend で利用する profile を返す。"""
    return load_js_profile()


def transpile_to_swift(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """互換 API: native emitter へ委譲する。"""
    _ = js_entry_path
    return transpile_to_swift_native(east_doc)


__all__ = ["load_swift_profile", "transpile_to_swift", "transpile_to_swift_native"]
