from pytra.runtime.assertions import py_assert_all, py_assert_eq
from pytra.std.enum import IntEnum


class Status(IntEnum):
    OK = 0
    ERROR = 1


def run_intenum_basic() -> bool:
    checks: list[bool] = []
    checks.append(py_assert_eq(Status.OK == 0, True, "int_compare"))
    checks.append(py_assert_eq(Status.ERROR == 1, True, "int_compare_2"))
    checks.append(py_assert_eq(int(Status.ERROR), 1, "to_int"))
    return py_assert_all(checks, "intenum_basic")


if __name__ == "__main__":
    print(run_intenum_basic())
