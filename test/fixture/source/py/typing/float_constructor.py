from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_float_constructor() -> bool:
    checks: list[bool] = []

    # from int
    checks.append(py_assert_eq(float(42), 42.0, "float from int"))
    checks.append(py_assert_eq(float(0), 0.0, "float from zero"))
    checks.append(py_assert_eq(float(-7), -7.0, "float from negative int"))

    # from string
    checks.append(py_assert_eq(float("3.14"), 3.14, "float from str"))
    checks.append(py_assert_eq(float("-2.5"), -2.5, "float from negative str"))
    checks.append(py_assert_eq(float("0"), 0.0, "float from str zero"))

    # from bool
    checks.append(py_assert_eq(float(True), 1.0, "float from True"))
    checks.append(py_assert_eq(float(False), 0.0, "float from False"))

    return py_assert_all(checks, "float_constructor")


if __name__ == "__main__":
    print(run_float_constructor())
