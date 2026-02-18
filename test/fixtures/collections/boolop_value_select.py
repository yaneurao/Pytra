# このファイルは `test/fixtures/boolop_value_select.py` のテスト/実装コードです。


from pylib.runtime import py_assert_all, py_assert_eq
def run_boolop_value_select() -> bool:
    x: str = ""
    y: str = "fallback"
    z: str = x or y
    p: str = "left"
    q: str = "right"
    r: str = p and q
    n: int = 0
    m: int = 9
    t: int = n or m
    checks: list[bool] = []
    checks.append(py_assert_eq(z, "fallback", "or value select"))
    checks.append(py_assert_eq(r, "right", "and value select"))
    checks.append(py_assert_eq(t, 9, "int or value select"))
    return py_assert_all(checks, "case42")


if __name__ == "__main__":
    print(run_boolop_value_select())
