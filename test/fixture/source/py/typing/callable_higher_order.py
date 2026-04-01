from pytra.utils.assertions import py_assert_all, py_assert_eq


def apply_int(fn: callable, x: int) -> int:
    return fn(x)


def apply_float(fn: callable, x: float) -> float:
    return fn(x)


def apply_str(fn: callable, s: str) -> str:
    return fn(s)


def double(x: int) -> int:
    return x * 2


def negate(x: int) -> int:
    return -x


def square_float(x: float) -> float:
    return x * x


def to_upper(s: str) -> str:
    return s.upper()


def compose(f: callable, g: callable, x: int) -> int:
    return f(g(x))


def apply_twice(fn: callable, x: int) -> int:
    return fn(fn(x))


def apply_to_list(fn: callable, xs: list[int]) -> list[int]:
    result: list[int] = []
    for x in xs:
        result.append(fn(x))
    return result


def run_callable_higher_order() -> bool:
    checks: list[bool] = []

    # basic function passing
    checks.append(py_assert_eq(apply_int(double, 5), 10, "apply_double"))
    checks.append(py_assert_eq(apply_int(negate, 3), -3, "apply_negate"))
    checks.append(py_assert_eq(apply_float(square_float, 3.0), 9.0, "apply_square"))
    checks.append(py_assert_eq(apply_str(to_upper, "hello"), "HELLO", "apply_upper"))

    # composition
    checks.append(py_assert_eq(compose(double, negate, 4), -8, "compose_double_negate"))
    checks.append(py_assert_eq(compose(negate, double, 4), -8, "compose_negate_double"))

    # apply twice
    checks.append(py_assert_eq(apply_twice(double, 3), 12, "apply_twice_double"))
    checks.append(py_assert_eq(apply_twice(negate, 7), 7, "apply_twice_negate"))

    # apply to list (map pattern)
    checks.append(py_assert_eq(str(apply_to_list(double, [1, 2, 3])), str([2, 4, 6]), "map_double"))
    checks.append(py_assert_eq(str(apply_to_list(negate, [10, 20])), str([-10, -20]), "map_negate"))

    return py_assert_all(checks, "callable_higher_order")


if __name__ == "__main__":
    print(run_callable_higher_order())
