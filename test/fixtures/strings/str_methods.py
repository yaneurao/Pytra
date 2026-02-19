# このファイルは `test/fixtures/str_methods.py` のテスト/実装コードです。


from pytra.runtime.assertions import py_assert_all, py_assert_eq, py_assert_true
def run_str_methods() -> bool:
    s: str = "  alpha_beta  "
    a: str = s.strip()
    b: str = s.rstrip()
    c: bool = a.startswith("alpha")
    d: bool = a.endswith("beta")
    e: str = a.replace("_", "-")
    parts: list[str] = ["A", "B", "C"]
    j: str = ":".join(parts)
    checks: list[bool] = []
    checks.append(py_assert_eq(a, "alpha_beta", "strip"))
    checks.append(py_assert_eq(b, "  alpha_beta", "rstrip"))
    checks.append(py_assert_true(c, "startswith"))
    checks.append(py_assert_true(d, "endswith"))
    checks.append(py_assert_eq(e, "alpha-beta", "replace"))
    checks.append(py_assert_eq(j, "A:B:C", "join"))
    return py_assert_all(checks, "case38")


if __name__ == "__main__":
    print(run_str_methods())
