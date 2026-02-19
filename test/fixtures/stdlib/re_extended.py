from pylib.std import re
from pylib.tra.assertions import py_assert_all, py_assert_eq


def run_re_extended() -> bool:
    checks: list[bool] = []
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", "x = 1")
    if m is None:
        checks.append(py_assert_eq("None", "match", "match-none"))
        return py_assert_all(checks, "re_extended")
    checks.append(py_assert_eq(m.group(1), "x", "group1"))
    checks.append(py_assert_eq(m.group(2), "1", "group2"))
    out = re.sub(r"\s+", " ", "a   b\tc")
    checks.append(py_assert_eq(out, "a b c", "sub"))
    return py_assert_all(checks, "re_extended")


if __name__ == "__main__":
    print(run_re_extended())
