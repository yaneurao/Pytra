from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_enumerate_basic() -> bool:
    values: list[int] = [10, 20, 30]
    weighted: int = 0
    for i, v in enumerate(values):
        weighted += i * v

    idx_sum: int = 0
    value_sum: int = 0
    for i, v in enumerate(values):
        idx_sum += i
        value_sum += v

    checks: list[bool] = []
    checks.append(py_assert_eq(weighted, 80, "weighted"))
    checks.append(py_assert_eq(idx_sum, 3, "idx_sum"))
    checks.append(py_assert_eq(value_sum, 60, "value_sum"))
    return py_assert_all(checks, "enumerate_basic")


if __name__ == "__main__":
    print(run_enumerate_basic())
