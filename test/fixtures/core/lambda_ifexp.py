# lambda containing if-expression
from py_module.py_runtime import py_assert_all, py_assert_eq


def run_lambda_ifexp() -> bool:
    choose = lambda x: "pos" if x > 0 else "non-pos"

    checks: list[bool] = []
    checks.append(py_assert_eq(choose(2), "pos", "choose(2)"))
    checks.append(py_assert_eq(choose(0), "non-pos", "choose(0)"))
    checks.append(py_assert_eq(choose(-7), "non-pos", "choose(-7)"))
    return py_assert_all(checks, "lambda_ifexp")


if __name__ == "__main__":
    print(run_lambda_ifexp())
