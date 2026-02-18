"""EAST ベースの言語エミッタ共通基底。"""

from __future__ import annotations

from typing import Any


class BaseEmitter:
    """EAST -> 各言語のコード生成で共通利用する最小基底クラス。"""

    def __init__(self, east_doc: dict[str, Any]) -> None:
        self.doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_id = 0

    def emit(self, line: str = "") -> None:
        self.lines.append(("    " * self.indent) + line)

    def emit_stmt_list(self, stmts: list[Any]) -> None:
        for stmt in stmts:
            self.emit_stmt(stmt)  # type: ignore[attr-defined]

    def next_tmp(self, prefix: str = "__tmp") -> str:
        self.tmp_id += 1
        return f"{prefix}_{self.tmp_id}"

