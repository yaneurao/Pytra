# This file contains test/implementation code for `test/fixtures/typing/bytes_truthiness.py`.

from pytra.utils.assertions import py_assert_all, py_assert_eq


def has_data_if(payload: bytes) -> bool:
    if payload:
        return True
    return False


def has_data_while(payload: bytes) -> bool:
    while payload:
        return True
    return False


def choose_payload(payload: bytes) -> int:
    return 1 if payload else 0


def run_bytes_truthiness() -> bool:
    empty: bytes = bytes()
    filled: bytes = bytes([1, 2, 3])

    checks: list[bool] = []
    checks.append(py_assert_eq(has_data_if(empty), False, "bytes if empty"))
    checks.append(py_assert_eq(has_data_if(filled), True, "bytes if filled"))
    checks.append(py_assert_eq(has_data_while(empty), False, "bytes while empty"))
    checks.append(py_assert_eq(has_data_while(filled), True, "bytes while filled"))
    checks.append(py_assert_eq(choose_payload(empty), 0, "bytes ifexp empty"))
    checks.append(py_assert_eq(choose_payload(filled), 1, "bytes ifexp filled"))
    return py_assert_all(checks, "bytes_truthiness")


if __name__ == "__main__":
    print(run_bytes_truthiness())
