from pylib.assertions import py_assert_all, py_assert_eq
from pylib.enum import IntFlag


class Perm(IntFlag):
    READ = 1
    WRITE = 2
    EXEC = 4


def run_intflag_basic() -> bool:
    rw: Perm = Perm.READ | Perm.WRITE
    has_write: Perm = rw & Perm.WRITE
    has_exec: Perm = rw & Perm.EXEC
    checks: list[bool] = []
    checks.append(py_assert_eq(int(rw), 3, "or_value"))
    checks.append(py_assert_eq(has_write == Perm.WRITE, True, "and_mask"))
    checks.append(py_assert_eq(has_exec == Perm.EXEC, False, "and_missing"))
    checks.append(py_assert_eq(int(Perm.READ ^ Perm.WRITE), 3, "xor"))
    return py_assert_all(checks, "intflag_basic")


if __name__ == "__main__":
    print(run_intflag_basic())
