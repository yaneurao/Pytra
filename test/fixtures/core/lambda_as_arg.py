# lambda passed as function argument
from py_module.py_runtime import py_assert_all, py_assert_eq


def apply_once(f: callable, x: int) -> int:
    return f(x)


def run_lambda_as_arg() -> bool:
    inc = lambda z: z + 1
    out: int = apply_once(inc, 41)

    checks: list[bool] = []
    checks.append(py_assert_eq(out, 42, "apply_once"))
    return py_assert_all(checks, "lambda_as_arg")


if __name__ == "__main__":
    print(run_lambda_as_arg())
