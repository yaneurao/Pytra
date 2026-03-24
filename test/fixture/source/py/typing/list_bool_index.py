# This file contains test/implementation code for `test/fixtures/typing/list_bool_index.py`.

from pytra.utils.assertions import py_assert_all, py_assert_eq


def invert_flag(flags: list[bool], index: int) -> bool:
    current = flags[index]
    flags[index] = not current
    return flags[index]


def run_list_bool_index() -> bool:
    flags: list[bool] = [True, False, True]
    checks: list[bool] = []
    checks.append(py_assert_eq(flags[0], True, "initial read true"))
    checks.append(py_assert_eq(flags[1], False, "initial read false"))
    checks.append(py_assert_eq(invert_flag(flags, 0), False, "write false"))
    checks.append(py_assert_eq(flags[0], False, "reread false"))
    checks.append(py_assert_eq(invert_flag(flags, 1), True, "write true"))
    checks.append(py_assert_eq(flags[1], True, "reread true"))
    return py_assert_all(checks, "list_bool_index")


if __name__ == "__main__":
    print(run_list_bool_index())
