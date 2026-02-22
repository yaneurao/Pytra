"""複数ターゲットのトランスパイラで共有する補助機能。"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pytra.std.typing import List, Set

INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1


@dataclass
class Scope:
    """変換中スコープで宣言済みの変数名を保持する。

    Attributes:
        declared: そのスコープで既に宣言済みとして扱う識別子の集合。
    """

    declared: Set[str]


class TempNameFactory:
    """衝突しない一時変数名を生成する。

    Attributes:
        prefix: 生成名の先頭に付与する固定プレフィックス。
        counter: 生成済み件数。呼び出しごとに増加して一意性を担保する。
    """

    def __init__(self, prefix: str = "__pytra") -> None:
        """一時変数名生成器を初期化する。

        Args:
            prefix: 一時変数名の先頭に付与する接頭辞。
        """
        self.prefix = prefix
        self.counter = 0

    def new(self, base: str) -> str:
        """指定ベース名に連番を付与した一意な名前を返す。

        Args:
            base: 可読性のために含めるベース文字列。

        Returns:
            prefix/base/counter を合成した新しい識別子。
        """
        self.counter += 1
        return f"{self.prefix}_{base}_{self.counter}"


def requires_wide_int(fn: ast.FunctionDef, *, int_min: int = INT32_MIN, int_max: int = INT32_MAX) -> bool:
    """関数内に 32-bit 範囲外の整数リテラルがあるかを判定する。

    Args:
        fn: 判定対象の関数 AST。
        int_min: 許容する最小整数値。
        int_max: 許容する最大整数値。
    """

    for node in ast.walk(fn):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            if node.value < int_min or node.value > int_max:
                return True
    return False


def called_function_names(fn: ast.FunctionDef) -> Set[str]:
    """関数内で直接呼ばれている関数名の集合を返す。

    Args:
        fn: 解析対象の関数 AST。
    """

    called: Set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called.add(node.func.id)
    return called


def compute_wide_int_functions(
    funcs: List[ast.FunctionDef], *, int_min: int = INT32_MIN, int_max: int = INT32_MAX
) -> Set[str]:
    """wide-int が必要な関数集合を呼び出し関係を含めて求める。

    直接 32bit 範囲外整数を含む関数だけでなく、
    それらを呼び出す関数も伝播的に wide-int 対象へ含める。

    Args:
        funcs: 解析対象の関数定義一覧。
        int_min: 許容する最小整数値。
        int_max: 許容する最大整数値。
    """

    func_names = {fn.name for fn in funcs}
    wide = {fn.name for fn in funcs if requires_wide_int(fn, int_min=int_min, int_max=int_max)}
    changed = True
    while changed:
        changed = False
        for fn in funcs:
            if fn.name in wide:
                continue
            called = called_function_names(fn)
            if any(name in wide for name in called if name in func_names):
                wide.add(fn.name)
                changed = True
    return wide


def is_main_guard(stmt: ast.stmt) -> bool:
    """if __name__ == '__main__' を判定する。

    Args:
        stmt: 判定対象の文ノード。
    """

    if not isinstance(stmt, ast.If):
        return False
    test = stmt.test
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq):
        return False
    return (
        isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )
