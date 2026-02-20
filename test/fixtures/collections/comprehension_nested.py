# comprehension nested lists
from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_comprehension_nested() -> bool:
    rows: list[list[int]] = [[i * j for j in [1, 2, 3]] for i in [2, 3]]

    checks: list[bool] = []
    checks.append(py_assert_eq(len(rows), 2, "rows len"))
    checks.append(py_assert_eq(rows[0][0], 2, "rows[0][0]"))
    checks.append(py_assert_eq(rows[0][2], 6, "rows[0][2]"))
    checks.append(py_assert_eq(rows[1][1], 6, "rows[1][1]"))
    checks.append(py_assert_eq(rows[1][2], 9, "rows[1][2]"))
    return py_assert_all(checks, "comprehension_nested")


if __name__ == "__main__":
    print(run_comprehension_nested())
