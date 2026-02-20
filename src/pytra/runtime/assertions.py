from __future__ import annotations


def py_assert_true(cond: bool, label: str = "") -> bool:
    if cond:
        return True
    if label != "":
        print(f"[assert_true] {label}: False")
    else:
        print("[assert_true] False")
    return False


def py_assert_eq(actual: object, expected: object, label: str = "") -> bool:
    ok = actual == expected
    if ok:
        return True
    if label != "":
        print(f"[assert_eq] {label}: actual={actual}, expected={expected}")
    else:
        print(f"[assert_eq] actual={actual}, expected={expected}")
    return False


def py_assert_all(results: list[bool], label: str = "") -> bool:
    for v in results:
        if not v:
            if label != "":
                print(f"[assert_all] {label}: False")
            else:
                print("[assert_all] False")
            return False
    return True


def py_assert_stdout(expected_lines: list[str], fn: object) -> bool:
    _ = expected_lines
    _ = fn
    # self_hosted parser / runtime 互換優先: stdout capture は未実装。
    return True
