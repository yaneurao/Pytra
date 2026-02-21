"""JavaScript 向け CodeEmitter hooks 実装。"""

from __future__ import annotations

from pytra.compiler.east_parts.code_emitter import EmitterHooks


def build_js_hooks() -> dict[str, object]:
    """JavaScript 向け hook を返す（現時点では最小構成）。"""
    hooks = EmitterHooks()
    return hooks.to_dict()

