from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_list_repeat() -> bool:
    checks: list[bool] = []

    a: list[int] = [0] * 8
    checks.append(py_assert_eq(len(a), 8, "repeat_len"))
    checks.append(py_assert_eq(a[0], 0, "repeat_val_0"))
    checks.append(py_assert_eq(a[7], 0, "repeat_val_7"))

    b: list[str] = ["x"] * 3
    checks.append(py_assert_eq(len(b), 3, "repeat_str_len"))
    checks.append(py_assert_eq(b[0], "x", "repeat_str_val"))

    c: list[int] = [1, 2] * 4
    checks.append(py_assert_eq(len(c), 8, "repeat_pattern_len"))
    checks.append(py_assert_eq(c[0], 1, "repeat_pattern_0"))
    checks.append(py_assert_eq(c[1], 2, "repeat_pattern_1"))
    checks.append(py_assert_eq(c[6], 1, "repeat_pattern_6"))
    checks.append(py_assert_eq(c[7], 2, "repeat_pattern_7"))

    d: list[int] = [5] * 0
    checks.append(py_assert_eq(len(d), 0, "repeat_zero"))

    return py_assert_all(checks, "list_repeat")


if __name__ == "__main__":
    print(run_list_repeat())
