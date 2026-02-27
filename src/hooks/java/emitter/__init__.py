"""Java emitter helpers (native only)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile

from .java_native_emitter import transpile_to_java_native


def load_java_profile() -> dict[str, Any]:
    """Java backend で利用する profile を返す。"""
    return load_js_profile()


def transpile_to_java(
    east_doc: dict[str, Any],
    js_entry_path: str = "Main.js",
    class_name: str = "Main",
) -> str:
    """互換 API: native emitter へ委譲する。"""
    _ = js_entry_path
    return transpile_to_java_native(east_doc, class_name=class_name)


__all__ = ["load_java_profile", "transpile_to_java", "transpile_to_java_native"]
