from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_lambda_immediate() -> bool:
    a: int = (lambda x: x + 1)(3)
    b: int = (lambda x, y: x + y)(4, 5)

    checks: list[bool] = []
    checks.append(py_assert_eq(a, 4, "lambda immediate unary"))
    checks.append(py_assert_eq(b, 9, "lambda immediate binary"))
    return py_assert_all(checks, "lambda_immediate")


if __name__ == "__main__":
    print(run_lambda_immediate())
