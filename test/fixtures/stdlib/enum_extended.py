from pytra.utils.assertions import py_assert_all, py_assert_eq
from pytra.std.enum import Enum, IntEnum, IntFlag


class Color(Enum):
    RED = 1
    BLUE = 2


class Status(IntEnum):
    OK = 0
    ERROR = 1


class Perm(IntFlag):
    READ = 1
    WRITE = 2
    EXEC = 4


def run_enum_extended() -> bool:
    checks: list[bool] = []
    checks.append(py_assert_eq(Color.RED == Color.RED, True, "enum-eq"))
    checks.append(py_assert_eq(Color.RED == Color.BLUE, False, "enum-neq"))
    checks.append(py_assert_eq(Status.OK == 0, True, "int-enum-eq"))
    checks.append(py_assert_eq(int(Status.ERROR), 1, "int-enum-int"))
    rw: Perm = Perm.READ | Perm.WRITE
    checks.append(py_assert_eq(int(rw), 3, "flag-or"))
    checks.append(py_assert_eq(int(rw & Perm.WRITE), 2, "flag-and"))
    checks.append(py_assert_eq(int(rw ^ Perm.WRITE), 1, "flag-xor"))
    return py_assert_all(checks, "enum_extended")


if __name__ == "__main__":
    print(run_enum_extended())
