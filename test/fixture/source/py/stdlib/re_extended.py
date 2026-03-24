from pytra.std.re import sub
from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_re_extended() -> bool:
    checks: list[bool] = []
    out: str = sub(r"\s+", " ", "a   b\tc")
    checks.append(py_assert_eq(out, "a b c", "sub"))
    return py_assert_all(checks, "re_extended")


if __name__ == "__main__":
    print(run_re_extended())
