"""Compatibility shim for CodeEmitter/EmitterHooks.

Canonical implementation moved to ``backends.common.emitter.code_emitter``.
"""

from __future__ import annotations

from toolchain.emit.common.emitter.code_emitter import CodeEmitter, EmitterHooks

__all__ = ["CodeEmitter", "EmitterHooks"]
