"""Compatibility wrapper for Nim native emitter."""

from __future__ import annotations

from backends.nim.emitter.nim_native_emitter import NimNativeEmitter, transpile_to_nim_native

__all__ = ["NimNativeEmitter", "transpile_to_nim_native"]
