"""トランスパイラ共通基底クラスと共通例外。"""

from __future__ import annotations

import ast
from pytra.std.typing import List, Set

from .transpile_shared import (
    INT32_MAX,
    INT32_MIN,
    TempNameFactory,
    compute_wide_int_functions,
    is_main_guard,
    requires_wide_int,
)


class TranspileError(Exception):
    """トランスパイル時の仕様違反・未対応構文を通知する例外。"""


class BaseTranspiler:
    """言語別トランスパイラが共通利用する基底クラス。

    Attributes:
        temp_names: 競合しない一時変数名を発行するための生成器。
    """

    INDENT = "    "

    def __init__(self, *, temp_prefix: str = "__pytra") -> None:
        """共通基底の状態を初期化する。

        Args:
            temp_prefix: 一時変数生成時に利用する識別子プレフィックス。
        """
        self.temp_names = TempNameFactory(prefix=temp_prefix)

    def _new_temp(self, base: str) -> str:
        """一時変数名を 1 つ払い出す。"""
        return self.temp_names.new(base)

    def _requires_wide_int(self, fn: ast.FunctionDef) -> bool:
        """関数が wide-int を必要とするか判定する。"""
        return requires_wide_int(fn, int_min=INT32_MIN, int_max=INT32_MAX)

    def _compute_wide_int_functions(self, funcs: List[ast.FunctionDef]) -> Set[str]:
        """wide-int が必要な関数集合を呼び出し関係込みで求める。"""
        return compute_wide_int_functions(funcs, int_min=INT32_MIN, int_max=INT32_MAX)

    def _is_main_guard(self, stmt: ast.stmt) -> bool:
        """`if __name__ == "__main__"` 判定を共通化して提供する。"""
        return is_main_guard(stmt)

    def _indent_block(self, lines: List[str]) -> List[str]:
        """与えられた複数行へ 1 段インデントを付与する。"""
        return [f"{self.INDENT}{line}" if line else "" for line in lines]

    def _parse_range_args(
        self,
        iter_expr: ast.expr,
        *,
        keyword_error: str = "range() with keyword args is not supported",
        argc_error: str = "range() with more than 3 arguments is not supported",
    ) -> tuple[str, str, str] | None:
        """`range(...)` 呼び出しを `(start, stop, step)` へ正規化する。

        Args:
            iter_expr: `for ... in ...` の反復対象式。
            keyword_error: キーワード引数が与えられた場合のエラーメッセージ。
            argc_error: 引数個数が 1-3 以外の場合のエラーメッセージ。

        Returns:
            `range` の場合は `(start, stop, step)` の式文字列タプル。
            `range` 以外の場合は `None`。
        """
        if not (
            isinstance(iter_expr, ast.Call)
            and isinstance(iter_expr.func, ast.Name)
            and iter_expr.func.id == "range"
        ):
            return None
        if iter_expr.keywords:
            raise TranspileError(keyword_error)
        argc = len(iter_expr.args)
        if argc == 1:
            return "0", self.transpile_expr(iter_expr.args[0]), "1"  # type: ignore[attr-defined]
        if argc == 2:
            return (
                self.transpile_expr(iter_expr.args[0]),  # type: ignore[attr-defined]
                self.transpile_expr(iter_expr.args[1]),  # type: ignore[attr-defined]
                "1",
            )
        if argc == 3:
            return (
                self.transpile_expr(iter_expr.args[0]),  # type: ignore[attr-defined]
                self.transpile_expr(iter_expr.args[1]),  # type: ignore[attr-defined]
                self.transpile_expr(iter_expr.args[2]),  # type: ignore[attr-defined]
            )
        raise TranspileError(argc_error)
