# このファイルは `test/fixtures/typing/any_dict_items.py` のテスト/実装コードです。

from typing import Any
from pytra.runtime.assertions import py_assert_all, py_assert_eq


def run_any_dict_items() -> bool:
    root: dict[str, Any] = {
        "meta": {"a": 2, "b": 3},
        "name": "demo",
    }

    total: int = 0
    meta: dict[str, Any] = root.get("meta", {})
    for _k, v in meta.items():
        total += v

    checks: list[bool] = []
    checks.append(py_assert_eq(total, 5, "sum meta"))
    checks.append(py_assert_eq(str(root.get("name", "")), "demo", "name"))
    return py_assert_all(checks, "any_dict_items")


if __name__ == "__main__":
    print(run_any_dict_items())
