# このファイルは `test/fixtures/core/lambda_basic.py` のテストコードです。

from pylib.runtime import py_assert_all, py_assert_eq


def run_lambda_basic() -> bool:
    base: int = 7
    add_base = lambda x: x + base
    always_true = lambda: True
    is_positive = lambda x: x > 0

    y: int = add_base(5)
    z: int = add_base(-2)
    b1: bool = is_positive(3)
    b2: bool = is_positive(-1)

    checks: list[bool] = []
    checks.append(py_assert_eq(y, 12, "lambda add_base(5)"))
    checks.append(py_assert_eq(z, 5, "lambda add_base(-2)"))
    checks.append(py_assert_eq(always_true(), True, "lambda no-arg"))
    checks.append(py_assert_eq(b1, True, "lambda is_positive(3)"))
    checks.append(py_assert_eq(b2, False, "lambda is_positive(-1)"))
    return py_assert_all(checks, "lambda_basic")


if __name__ == "__main__":
    print(run_lambda_basic())
