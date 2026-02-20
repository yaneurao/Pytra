from pytra.std import sys
from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_sys_extended() -> bool:
    checks: list[bool] = []
    old_argv = sys.argv
    old_path = sys.path
    sys.set_argv(["a", "b"])
    sys.set_path(["x"])
    checks.append(py_assert_eq(isinstance(sys.argv, list), True, "argv-is-list"))
    checks.append(py_assert_eq(isinstance(sys.path, list), True, "path-is-list"))
    checks.append(py_assert_eq(sys.argv[0], "a", "argv0"))
    checks.append(py_assert_eq(sys.path[0], "x", "path0"))
    sys.set_argv(old_argv)
    sys.set_path(old_path)
    return py_assert_all(checks, "sys_extended")


if __name__ == "__main__":
    print(run_sys_extended())
