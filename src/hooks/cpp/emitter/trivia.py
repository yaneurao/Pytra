from __future__ import annotations

from pytra.std.typing import Any


class CppTriviaEmitter:
    """Trivia/コメント/ディレクティブ処理を切り出すための薄いヘルパークラス。"""

    def render_trivia(self, stmt: dict[str, Any]) -> None:
        """Stmt の leading trivia を出力する。"""
        self.emit_leading_comments(stmt)

    def emit_leading_comments(self, stmt: dict[str, Any]) -> None:
        """leading trivia をコメント/空行として出力する。"""
        if "leading_trivia" not in stmt:
            return
        trivia = self.any_to_dict_list(stmt.get("leading_trivia"))
        if len(trivia) == 0:
            return
        self._emit_trivia_items(trivia)
