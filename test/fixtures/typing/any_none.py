# このファイルは `test/fixtures/typing/any_none.py` のテスト/実装コードです。

from typing import Any
from pylib.py_runtime import py_assert_all, py_assert_eq, py_assert_true


def run_any_none() -> bool:
    v: Any = None
    w: Any = "x"

    is_none_v: bool = v is None
    is_not_none_w: bool = w is not None

    out: str = "fallback" if v is None else str(v)

    checks: list[bool] = []
    checks.append(py_assert_true(is_none_v, "v is None"))
    checks.append(py_assert_true(is_not_none_w, "w is not None"))
    checks.append(py_assert_eq(out, "fallback", "none fallback"))
    return py_assert_all(checks, "any_none")


if __name__ == "__main__":
    print(run_any_none())
