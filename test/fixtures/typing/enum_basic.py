from pytra.utils.assertions import py_assert_all, py_assert_eq
from pytra.std.enum import Enum


class Color(Enum):
    RED = 1
    BLUE = 2


def run_enum_basic() -> bool:
    checks: list[bool] = []
    checks.append(py_assert_eq(Color.RED == Color.RED, True, "same_member"))
    checks.append(py_assert_eq(Color.RED == Color.BLUE, False, "different_member"))
    checks.append(py_assert_eq(Color.BLUE == Color.BLUE, True, "same_member_blue"))
    checks.append(py_assert_eq(Color.BLUE == Color.RED, False, "different_member_reverse"))
    return py_assert_all(checks, "enum_basic")


if __name__ == "__main__":
    print(run_enum_basic())
