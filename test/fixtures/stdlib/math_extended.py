
from pylib.tra.assertions import py_assert_all, py_assert_eq
import math


def run_math_extended() -> bool:
    checks: list[bool] = []
    checks.append(py_assert_eq(math.fabs(math.tan(0.0)) < 1e-12, True, "tan"))
    checks.append(py_assert_eq(math.fabs(math.log(math.exp(1.0)) - 1.0) < 1e-12, True, "logexp"))
    checks.append(py_assert_eq(int(math.log10(1000.0)), 3, "log10"))
    checks.append(py_assert_eq(int(math.fabs(-3.5) * 10.0), 35, "fabs"))
    checks.append(py_assert_eq(int(math.ceil(2.1)), 3, "ceil"))
    checks.append(py_assert_eq(int(math.pow(2.0, 5.0)), 32, "pow"))
    return py_assert_all(checks, "math_extended")


if __name__ == "__main__":
    print(run_math_extended())
