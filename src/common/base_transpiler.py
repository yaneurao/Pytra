"""トランスパイラ共通基底クラスと共通例外。"""

from __future__ import annotations

import ast
from typing import List, Set

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
    """言語別トランスパイラが共通利用する基底クラス。"""

    INDENT = "    "

    def __init__(self, *, temp_prefix: str = "__pytra") -> None:
        self.temp_names = TempNameFactory(prefix=temp_prefix)

    def _new_temp(self, base: str) -> str:
        return self.temp_names.new(base)

    def _requires_wide_int(self, fn: ast.FunctionDef) -> bool:
        return requires_wide_int(fn, int_min=INT32_MIN, int_max=INT32_MAX)

    def _compute_wide_int_functions(self, funcs: List[ast.FunctionDef]) -> Set[str]:
        return compute_wide_int_functions(funcs, int_min=INT32_MIN, int_max=INT32_MAX)

    def _is_main_guard(self, stmt: ast.stmt) -> bool:
        return is_main_guard(stmt)

    def _indent_block(self, lines: List[str]) -> List[str]:
        return [f"{self.INDENT}{line}" if line else "" for line in lines]

    def _parse_range_args(
        self,
        iter_expr: ast.expr,
        *,
        keyword_error: str = "range() with keyword args is not supported",
        argc_error: str = "range() with more than 3 arguments is not supported",
    ) -> tuple[str, str, str] | None:
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
