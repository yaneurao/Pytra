"""Nim emitter helpers (native only)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile

from .nim_native_emitter import transpile_to_nim_native


def load_nim_profile() -> dict[str, Any]:
    """Nim backend 用 profile を返す。"""
    # JS 用を流用するか、必要に応じて独自定義する
    return load_js_profile()


def transpile_to_nim(east_doc: dict[str, Any]) -> str:
    """native emitter へ委譲する。"""
    return transpile_to_nim_native(east_doc)


__all__ = ["load_nim_profile", "transpile_to_nim", "transpile_to_nim_native"]
