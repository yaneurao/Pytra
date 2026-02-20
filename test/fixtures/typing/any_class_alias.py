# このファイルは `test/fixtures/typing/any_class_alias.py` のテスト/実装コードです。

from typing import Any
from pytra.utils.assertions import py_assert_all, py_assert_eq, py_assert_true


class Box:
    def __init__(self, v: int) -> None:
        self.v: int = v


def run_any_class_alias() -> bool:
    a: Any = Box(7)
    b: Any = a

    checks: list[bool] = []
    checks.append(py_assert_true(isinstance(b, Box), "is Box"))
    checks.append(py_assert_eq(b.v, 7, "shared object"))
    return py_assert_all(checks, "any_class_alias")


if __name__ == "__main__":
    print(run_any_class_alias())
