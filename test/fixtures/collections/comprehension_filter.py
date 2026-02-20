# このファイルは `test/fixtures/collections/comprehension_filter.py` のテストコードです。

from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_comprehension_filter() -> bool:
    xs: list[int] = [1, 2, 3, 4, 5, 6]
    evens_sq: list[int] = [x * x for x in xs if x % 2 == 0]
    shifted: list[int] = [n + 1 for n in [10, 20] if n > 10]

    checks: list[bool] = []
    checks.append(py_assert_eq(len(evens_sq), 3, "len evens_sq"))
    checks.append(py_assert_eq(evens_sq[0], 4, "evens_sq[0]"))
    checks.append(py_assert_eq(evens_sq[1], 16, "evens_sq[1]"))
    checks.append(py_assert_eq(evens_sq[2], 36, "evens_sq[2]"))
    checks.append(py_assert_eq(len(shifted), 1, "len shifted"))
    checks.append(py_assert_eq(shifted[0], 21, "shifted[0]"))
    return py_assert_all(checks, "comprehension_filter")


if __name__ == "__main__":
    print(run_comprehension_filter())
