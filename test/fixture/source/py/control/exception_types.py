from pytra.utils.assertions import py_assert_all, py_assert_eq, py_assert_true


def run_exception_types() -> bool:
    checks: list[bool] = []

    # ValueError
    caught_ve: bool = False
    msg_ve: str = ""
    try:
        raise ValueError("bad value")
    except ValueError as e:
        caught_ve = True
        msg_ve = str(e)
    checks.append(py_assert_true(caught_ve, "ValueError caught"))
    checks.append(py_assert_eq(msg_ve, "bad value", "ValueError msg"))

    # TypeError
    caught_te: bool = False
    msg_te: str = ""
    try:
        raise TypeError("wrong type")
    except TypeError as e:
        caught_te = True
        msg_te = str(e)
    checks.append(py_assert_true(caught_te, "TypeError caught"))
    checks.append(py_assert_eq(msg_te, "wrong type", "TypeError msg"))

    # IndexError
    caught_ie: bool = False
    msg_ie: str = ""
    try:
        raise IndexError("out of range")
    except IndexError as e:
        caught_ie = True
        msg_ie = str(e)
    checks.append(py_assert_true(caught_ie, "IndexError caught"))
    checks.append(py_assert_eq(msg_ie, "out of range", "IndexError msg"))

    # KeyError
    caught_ke: bool = False
    try:
        raise KeyError("missing key")
    except KeyError as e:
        caught_ke = True
    checks.append(py_assert_true(caught_ke, "KeyError caught"))

    # RuntimeError
    caught_re: bool = False
    msg_re: str = ""
    try:
        raise RuntimeError("runtime failure")
    except RuntimeError as e:
        caught_re = True
        msg_re = str(e)
    checks.append(py_assert_true(caught_re, "RuntimeError caught"))
    checks.append(py_assert_eq(msg_re, "runtime failure", "RuntimeError msg"))

    # Exception catches all
    caught_base: bool = False
    try:
        raise ValueError("caught by base")
    except Exception as e:
        caught_base = True
    checks.append(py_assert_true(caught_base, "Exception catches ValueError"))

    return py_assert_all(checks, "exception_types")


if __name__ == "__main__":
    print(run_exception_types())
