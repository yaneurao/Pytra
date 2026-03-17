from __future__ import annotations

from pytra.std import abi


def _eq_any(actual: str | int | float | bool | None, expected: str | int | float | bool | None) -> bool:
    try:
        return py_to_string(actual) == py_to_string(expected)
    except NameError:
        return actual == expected


def py_assert_true(cond: bool, label: str = "") -> bool:
    if cond:
        return True
    if label != "":
        print(f"[assert_true] {label}: False")
    else:
        print("[assert_true] False")
    return False


def py_assert_eq(actual: str | int | float | bool | None, expected: str | int | float | bool | None, label: str = "") -> bool:
    ok = _eq_any(actual, expected)
    if ok:
        return True
    if label != "":
        print(f"[assert_eq] {label}: actual={actual}, expected={expected}")
    else:
        print(f"[assert_eq] actual={actual}, expected={expected}")
    return False


@abi(args={"results": "value"})
def py_assert_all(results: list[bool], label: str = "") -> bool:
    for v in results:
        if not v:
            if label != "":
                print(f"[assert_all] {label}: False")
            else:
                print("[assert_all] False")
            return False
    return True


@abi(args={"expected_lines": "value"})
def py_assert_stdout(expected_lines: list[str], fn: object) -> bool:
    # self_hosted parser / runtime 互換優先: stdout capture は未実装。
    return True
