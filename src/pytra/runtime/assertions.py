from __future__ import annotations


def py_assert_true(cond: bool, label: str = "") -> bool:
    if cond:
        return True
    if label != "":
        print(f"[assert_true] {label}: False")
    else:
        print("[assert_true] False")
    return False


def py_assert_eq(actual, expected, label: str = "") -> bool:
    ok = actual == expected
    if ok:
        return True
    if label != "":
        print(f"[assert_eq] {label}: actual={actual!r}, expected={expected!r}")
    else:
        print(f"[assert_eq] actual={actual!r}, expected={expected!r}")
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


def py_assert_stdout(expected_lines: list[str], fn) -> bool:
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn()
    out = buf.getvalue().splitlines()
    return py_assert_eq(out, expected_lines, "stdout")
