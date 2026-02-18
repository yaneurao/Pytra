"""C++ 向け CodeEmitter hooks 実装。"""

from __future__ import annotations

from typing import Any


class CppHooks:
    """C++ エミッタの拡張フック定義。

    既定では全て None を返し、標準の出力経路を維持する。
    profile で表現しにくい例外ケースのみをここへ寄せる。
    """

    def on_emit_stmt(self, emitter: Any, stmt: dict[str, Any]) -> bool | None:
        """文出力前フック。True を返すと既定処理をスキップする。"""
        return None

    def on_render_call(
        self,
        emitter: Any,
        call_node: dict[str, Any],
        func_node: dict[str, Any],
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
    ) -> str | None:
        """Call 式出力フック。文字列を返すとその式を採用する。"""
        return None

    def on_render_binop(
        self,
        emitter: Any,
        binop_node: dict[str, Any],
        left: str,
        right: str,
    ) -> str | None:
        """BinOp 出力フック。文字列を返すとその式を採用する。"""
        return None

