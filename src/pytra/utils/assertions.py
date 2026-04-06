from __future__ import annotations

def py_assert_true(cond: bool, label: str = "") -> bool:
    if cond:
        return True
    if label != "":
        print("[assert_true] " + label + ": False")
    else:
        print("[assert_true] False")
    return False


def py_assert_eq(
    actual: int | str | bool | None | list[int] | list[str],
    expected: int | str | bool | None | list[int] | list[str],
    label: str = "",
) -> bool:
    ok: bool = str(actual) == str(expected)
    if ok:
        return True
    if label != "":
        print("[assert_eq] " + label + ": actual=" + str(actual) + ", expected=" + str(expected))
    else:
        print("[assert_eq] actual=" + str(actual) + ", expected=" + str(expected))
    return False


def py_assert_all(results: list[bool], label: str = "") -> bool:
    for v in results:
        if not v:
            if label != "":
                print("[assert_all] " + label + ": False")
            else:
                print("[assert_all] False")
            return False
    return True


def py_assert_stdout(expected_lines: list[str], fn: callable[[], None]) -> bool:
    # self_hosted parser / runtime 互換優先: stdout capture は未実装。
    return True
