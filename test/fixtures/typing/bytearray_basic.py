# このファイルは `test/fixtures/typing/bytearray_basic.py` のテスト/実装コードです。

from pylib.assertions import py_assert_all, py_assert_eq


def run_bytearray_basic() -> bool:
    ba: bytearray = bytearray([10, 20, 30])
    ba.append(40)
    ba[1] = 25
    total: int = 0
    for v in ba:
        total += v

    checks: list[bool] = []
    checks.append(py_assert_eq(len(ba), 4, "bytearray len"))
    checks.append(py_assert_eq(ba[0], 10, "bytearray first"))
    checks.append(py_assert_eq(ba[1], 25, "bytearray mutate"))
    checks.append(py_assert_eq(ba[-1], 40, "bytearray last"))
    checks.append(py_assert_eq(total, 105, "bytearray sum"))
    return py_assert_all(checks, "bytearray_basic")


if __name__ == "__main__":
    print(run_bytearray_basic())
