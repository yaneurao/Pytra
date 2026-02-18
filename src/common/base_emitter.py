"""互換レイヤ: 旧 `BaseEmitter` 名を `CodeEmitter` へ委譲する。"""

from __future__ import annotations

from pylib.east_parts.code_emitter import CodeEmitter

# Backward compatibility for incremental migration.
BaseEmitter = CodeEmitter

