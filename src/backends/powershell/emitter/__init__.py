"""PowerShell emitter helpers (experimental)."""

from __future__ import annotations

from typing import Any

from backends.js.emitter.js_emitter import load_js_profile

from .powershell_emitter import transpile_to_powershell


def load_powershell_profile() -> dict[str, Any]:
    """PowerShell backend 用 profile を返す。"""
    return load_js_profile()


def transpile_to_powershell_native(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """互換 API: native emitter へ委譲する。"""
    _ = js_entry_path
    return transpile_to_powershell(east_doc)


__all__ = ["load_powershell_profile", "transpile_to_powershell", "transpile_to_powershell_native"]

