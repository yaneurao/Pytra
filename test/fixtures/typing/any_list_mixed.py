# このファイルは `test/fixtures/typing/any_list_mixed.py` のテスト/実装コードです。

from typing import Any
from pylib.runtime import py_assert_all, py_assert_eq


def run_any_list_mixed() -> bool:
    values: list[Any] = [1, "x", True]

    i: int = int(values[0])
    s: str = str(values[1])
    b: bool = bool(values[2])

    checks: list[bool] = []
    checks.append(py_assert_eq(i, 1, "int cast"))
    checks.append(py_assert_eq(s, "x", "str cast"))
    checks.append(py_assert_eq(b, True, "bool cast"))
    return py_assert_all(checks, "any_list_mixed")


if __name__ == "__main__":
    print(run_any_list_mixed())
