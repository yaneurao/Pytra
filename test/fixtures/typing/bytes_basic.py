# このファイルは `test/fixtures/typing/bytes_basic.py` のテスト/実装コードです。

from py_module.py_runtime import py_assert_all, py_assert_eq


def run_bytes_basic() -> bool:
    b: bytes = bytes([1, 2, 3, 255])
    total: int = 0
    for v in b:
        total += v

    checks: list[bool] = []
    checks.append(py_assert_eq(len(b), 4, "bytes len"))
    checks.append(py_assert_eq(b[0], 1, "bytes first"))
    checks.append(py_assert_eq(b[-1], 255, "bytes last"))
    checks.append(py_assert_eq(total, 261, "bytes sum"))
    return py_assert_all(checks, "bytes_basic")


if __name__ == "__main__":
    print(run_bytes_basic())
