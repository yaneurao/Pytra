# このファイルは `test/fixtures/typing/any_basic.py` のテスト/実装コードです。

from typing import Any
from pylib.runtime import py_assert_all, py_assert_eq, py_assert_true


def run_any_basic() -> bool:
    payload: dict[str, Any] = {
        "n": 1,
        "s": "x",
        "m": {"k": 2},
    }
    values: list[Any] = []
    values.append(payload["n"])
    values.append(payload["s"])
    n_value: int = int(values[0])
    s_value: str = str(values[1])

    nested: dict[str, Any] = payload.get("m", {})
    total: int = 0
    for _k, v in nested.items():
        total += v

    checks: list[bool] = []
    checks.append(py_assert_eq(n_value, 1, "any list int"))
    checks.append(py_assert_eq(s_value, "x", "any list str"))
    checks.append(py_assert_eq(total, 2, "dict[str,Any].get(...).items()"))
    checks.append(py_assert_true(isinstance(payload["m"], dict), "any dict type"))
    return py_assert_all(checks, "any_basic")


if __name__ == "__main__":
    print(run_any_basic())
