# comprehension equivalent of range-step behavior via prebuilt step list
from pylib.assertions import py_assert_all, py_assert_eq


def run_comprehension_range_step_like() -> bool:
    stepped: list[int] = [0, 2, 4, 6, 8]
    doubled: list[int] = [v * 2 for v in stepped]

    checks: list[bool] = []
    checks.append(py_assert_eq(len(doubled), 5, "doubled len"))
    checks.append(py_assert_eq(doubled[0], 0, "doubled[0]"))
    checks.append(py_assert_eq(doubled[-1], 16, "doubled[-1]"))
    return py_assert_all(checks, "comprehension_range_step_like")


if __name__ == "__main__":
    print(run_comprehension_range_step_like())
