# comprehension with chained predicates
from py_module.py_runtime import py_assert_all, py_assert_eq


def run_comprehension_if_chain() -> bool:
    xs: list[int] = [1, 2, 3, 4, 5, 6]
    picked: list[int] = [x for x in xs if x > 1 and x < 6 and x % 2 == 0]

    checks: list[bool] = []
    checks.append(py_assert_eq(len(picked), 2, "picked len"))
    checks.append(py_assert_eq(picked[0], 2, "picked[0]"))
    checks.append(py_assert_eq(picked[1], 4, "picked[1]"))
    return py_assert_all(checks, "comprehension_if_chain")


if __name__ == "__main__":
    print(run_comprehension_if_chain())
