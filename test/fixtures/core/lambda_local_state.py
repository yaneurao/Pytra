# lambda consuming local state-like value
from py_module.py_runtime import py_assert_all, py_assert_eq


def run_lambda_local_state() -> bool:
    factor: int = 3
    scale = lambda x: x * factor

    checks: list[bool] = []
    checks.append(py_assert_eq(scale(0), 0, "scale(0)"))
    checks.append(py_assert_eq(scale(5), 15, "scale(5)"))
    return py_assert_all(checks, "lambda_local_state")


if __name__ == "__main__":
    print(run_lambda_local_state())
