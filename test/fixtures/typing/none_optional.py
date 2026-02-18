# このファイルは `test/fixtures/none_optional.py` のテスト/実装コードです。


from pylib.runtime import py_assert_all, py_assert_eq, py_assert_true
def maybe_value(flag: bool) -> int | None:
    if flag:
        return 42
    return None


def run_none_optional() -> bool:
    a: int | None = maybe_value(True)
    b: int | None = maybe_value(False)
    d: dict[str, int] = {"x": 10}
    g1: int | None = d.get("x")
    g2: int | None = d.get("y")
    checks: list[bool] = []
    checks.append(py_assert_eq(a, 42, "a"))
    checks.append(py_assert_eq(b, None, "b"))
    checks.append(py_assert_true(g1 is not None, "g1 is not None"))
    checks.append(py_assert_true(g2 is None, "g2 is None"))
    return py_assert_all(checks, "case40")


if __name__ == "__main__":
    print(run_none_optional())
