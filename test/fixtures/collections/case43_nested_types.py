# このファイルは `test/fixtures/case43_nested_types.py` のテスト/実装コードです。

from py_module.py_runtime import py_assert_all, py_assert_eq, py_assert_true
from typing import Any


def run_case43_nested_types() -> bool:
    m: dict[str, str | None] = {"a": "x", "b": None}
    buckets: list[set[str]] = [set(), {"u", "v"}]
    payload: dict[str, Any] = {"k1": 1, "k2": "s"}

    a_is_none: bool = m["b"] is None
    buckets[0].add("t")
    checks: list[bool] = []
    checks.append(py_assert_true(a_is_none, "optional value"))
    checks.append(py_assert_eq(len(buckets[0]) + len(buckets[1]), 3, "nested container sizes"))
    checks.append(py_assert_eq(payload["k1"], 1, "any payload"))
    return py_assert_all(checks, "case43")


if __name__ == "__main__":
    print(run_case43_nested_types())
