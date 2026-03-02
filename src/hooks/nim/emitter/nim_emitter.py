"""Compatibility wrapper for Nim emitter helpers."""

from __future__ import annotations

from backends.nim.emitter import (
    load_nim_profile,
    transpile_to_nim,
    transpile_to_nim_native,
)

__all__ = ["load_nim_profile", "transpile_to_nim", "transpile_to_nim_native"]
