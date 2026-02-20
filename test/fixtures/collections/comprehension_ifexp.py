from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_comprehension_ifexp() -> bool:
    xs: list[int] = [1, 2, 3, 4]
    ys: list[int] = [x if x % 2 == 0 else -x for x in xs]

    checks: list[bool] = []
    checks.append(py_assert_eq(len(ys), 4, "len ys"))
    checks.append(py_assert_eq(ys[0], -1, "ys[0]"))
    checks.append(py_assert_eq(ys[1], 2, "ys[1]"))
    checks.append(py_assert_eq(ys[2], -3, "ys[2]"))
    checks.append(py_assert_eq(ys[3], 4, "ys[3]"))
    return py_assert_all(checks, "comprehension_ifexp")


if __name__ == "__main__":
    print(run_comprehension_ifexp())
