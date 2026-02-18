# comprehension with range(start, stop, step)
from pylib.runtime import py_assert_all, py_assert_eq


def run_comprehension_range_step() -> bool:
    xs: list[int] = [i for i in range(1, 10, 3)]

    checks: list[bool] = []
    checks.append(py_assert_eq(len(xs), 3, "xs len"))
    checks.append(py_assert_eq(xs[0], 1, "xs[0]"))
    checks.append(py_assert_eq(xs[1], 4, "xs[1]"))
    checks.append(py_assert_eq(xs[2], 7, "xs[2]"))
    return py_assert_all(checks, "comprehension_range_step")


if __name__ == "__main__":
    print(run_comprehension_range_step())
