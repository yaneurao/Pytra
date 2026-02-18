# このファイルは `test/fixtures/dict_get_items.py` のテスト/実装コードです。

from pylib.assertions import py_assert_eq
from typing import Any


def run_dict_get_items() -> bool:
    table: dict[str, Any] = {
        "a": {"x": 1, "y": 2},
        "b": {"z": 3},
    }
    total: int = 0
    for _k, v in table.get("a", {}).items():
        total += v
    for _k, v in table.get("missing", {}).items():
        total += v
    return py_assert_eq(total, 3, "total")


if __name__ == "__main__":
    print(run_dict_get_items())
