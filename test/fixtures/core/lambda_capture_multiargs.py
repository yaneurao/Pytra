# lambda capture + multi args
from pylib.assertions import py_assert_all, py_assert_eq


def run_lambda_capture_multiargs() -> bool:
    base: int = 10
    mix = lambda a, b: a + b + base

    checks: list[bool] = []
    checks.append(py_assert_eq(mix(1, 2), 13, "mix(1,2)"))
    checks.append(py_assert_eq(mix(-3, 4), 11, "mix(-3,4)"))
    return py_assert_all(checks, "lambda_capture_multiargs")


if __name__ == "__main__":
    print(run_lambda_capture_multiargs())
