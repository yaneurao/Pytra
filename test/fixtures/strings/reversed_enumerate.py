# このファイルは `test/fixtures/reversed_enumerate.py` のテスト/実装コードです。


from pylib.tra.assertions import py_assert_all, py_assert_eq
def run_reversed_enumerate() -> bool:
    values: list[int] = [3, 1, 4]
    acc: int = 0
    for i, v in enumerate(values):
        acc += i * v
    rev: list[int] = []
    for v in reversed(values):
        rev.append(v)
    checks: list[bool] = []
    checks.append(py_assert_eq(acc, 9, "acc"))
    checks.append(py_assert_eq(rev, [4, 1, 3], "reversed"))
    return py_assert_all(checks, "case39")


if __name__ == "__main__":
    print(run_reversed_enumerate())
