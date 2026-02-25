from __future__ import annotations

from pytra.std.typing import Any


class CppTriviaEmitter:
    """Trivia/コメント/ディレクティブ処理を切り出すための薄いヘルパークラス。"""

    def render_trivia(self, stmt: dict[str, Any]) -> None:
        """Stmt の leading trivia を出力する。"""
        self.emit_leading_comments(stmt)

    def emit_leading_comments(self, stmt: dict[str, Any]) -> None:
        """self_hosted parser 由来の trivia は directive のみ反映する。"""
        if "leading_trivia" not in stmt:
            return
        trivia = self.any_to_dict_list(stmt.get("leading_trivia"))
        if len(trivia) == 0:
            return
        if not self._is_self_hosted_parser_doc():
            self._emit_trivia_items(trivia)
            return
        for item in trivia:
            if self.any_dict_get_str(item, "kind", "") != "comment":
                continue
            txt = self.any_dict_get_str(item, "text", "")
            self._handle_comment_trivia_directive(txt)
