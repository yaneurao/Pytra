from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_in_membership() -> bool:
    xs: list[int] = [1, 3, 5]
    d: dict[str, int] = {"a": 10, "b": 20}
    ts: tuple[int, int, int] = (2, 4, 6)

    checks: list[bool] = []
    checks.append(py_assert_eq(3 in xs, True, "list_in_true"))
    checks.append(py_assert_eq(2 in xs, False, "list_in_false"))
    checks.append(py_assert_eq("a" in d, True, "dict_in_true"))
    checks.append(py_assert_eq("z" in d, False, "dict_in_false"))
    checks.append(py_assert_eq(4 in ts, True, "tuple_in_true"))
    checks.append(py_assert_eq(9 in ts, False, "tuple_in_false"))
    return py_assert_all(checks, "in_membership")


if __name__ == "__main__":
    print(run_in_membership())
