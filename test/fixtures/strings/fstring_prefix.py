# このファイルは `test/fixtures/fstring_prefix.py` のテスト/実装コードです。


from pytra.utils.assertions import py_assert_all, py_assert_eq
def run_fstring_prefix() -> bool:
    name: str = "Pytra"
    x: int = 7
    y: int = 5
    s1: str = f"name={name}, x={x}"
    s2: str = f"{{escaped}}:{x + y}"
    s3: str = rf"raw\\path\\{name}"
    s4: str = f"mix:{name}:{'ok' if x > y else 'ng'}"
    checks: list[bool] = []
    checks.append(py_assert_eq(s1, "name=Pytra, x=7", "s1"))
    checks.append(py_assert_eq(s2, "{escaped}:12", "s2"))
    checks.append(py_assert_eq(s3, "raw\\\\path\\\\Pytra", "s3"))
    checks.append(py_assert_eq(s4, "mix:Pytra:ok", "s4"))
    return py_assert_all(checks, "case37")


if __name__ == "__main__":
    print(run_fstring_prefix())
