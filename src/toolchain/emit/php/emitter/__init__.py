"""PHP emitter helpers (native only)."""

from __future__ import annotations

from typing import Any

from toolchain.emit.js.emitter.js_emitter import load_js_profile

from .php_native_emitter import transpile_to_php_native


def load_php_profile() -> dict[str, Any]:
    """PHP backend 用 profile を返す。"""
    return load_js_profile()


def transpile_to_php(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """互換 API: native emitter へ委譲する。"""
    _ = js_entry_path
    return transpile_to_php_native(east_doc)


__all__ = ["load_php_profile", "transpile_to_php", "transpile_to_php_native"]

