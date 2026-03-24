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

    start_weighted: int = 0
    for i, v in enumerate(values, 1):
        start_weighted += i * v

    pair_count: int = 0
    for pair in enumerate(values, 5):
        _ = pair
        pair_count += 1

    checks: list[bool] = []
    checks.append(py_assert_eq(weighted, 80, "weighted"))
    checks.append(py_assert_eq(idx_sum, 3, "idx_sum"))
    checks.append(py_assert_eq(value_sum, 60, "value_sum"))
    checks.append(py_assert_eq(start_weighted, 140, "start_weighted"))
    checks.append(py_assert_eq(pair_count, 3, "pair_count"))
    return py_assert_all(checks, "enumerate_basic")


if __name__ == "__main__":
    print(run_enumerate_basic())
