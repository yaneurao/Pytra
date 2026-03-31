from pytra.utils.assertions import py_assert_all, py_assert_eq


def _make_large_tuple() -> tuple[int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int]:
    return (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19)


def run_in_membership_iterable() -> bool:
    checks: list[bool] = []

    # large tuple (20 elements) — must work without per-arity specialization
    big: tuple[int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int] = _make_large_tuple()
    checks.append(py_assert_eq(0 in big, True, "large_tuple_first"))
    checks.append(py_assert_eq(19 in big, True, "large_tuple_last"))
    checks.append(py_assert_eq(20 in big, False, "large_tuple_absent"))

    # range as iterable
    checks.append(py_assert_eq(500 in range(1000), True, "range_in_true"))
    checks.append(py_assert_eq(1000 in range(1000), False, "range_in_false"))
    checks.append(py_assert_eq(-1 in range(1000), False, "range_in_negative"))
    checks.append(py_assert_eq(5 in range(0, 10, 2), False, "range_step_odd"))
    checks.append(py_assert_eq(6 in range(0, 10, 2), True, "range_step_even"))

    # set membership (for comparison)
    s: set[str] = {"x", "y", "z"}
    checks.append(py_assert_eq("y" in s, True, "set_in_true"))
    checks.append(py_assert_eq("w" in s, False, "set_in_false"))

    # string membership
    checks.append(py_assert_eq("bc" in "abcd", True, "str_in_true"))
    checks.append(py_assert_eq("xy" in "abcd", False, "str_in_false"))

    # not in
    checks.append(py_assert_eq(99 not in big, True, "large_tuple_not_in_true"))
    checks.append(py_assert_eq(10 not in big, False, "large_tuple_not_in_false"))
    checks.append(py_assert_eq(999 not in range(1000), False, "range_not_in_false"))

    return py_assert_all(checks, "in_membership_iterable")


if __name__ == "__main__":
    print(run_in_membership_iterable())
