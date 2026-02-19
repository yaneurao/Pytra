from __future__ import annotations

from pytra.runtime.assertions import py_assert_all, py_assert_eq
from pytra.std.math import floor, sqrt as msqrt


def run_case() -> None:
    results: list[bool] = []
    results.append(py_assert_eq(int(msqrt(81.0)), 9, "from pytra.std.math import sqrt as msqrt"))
    results.append(py_assert_eq(int(floor(3.9)), 3, "from pytra.std.math import floor"))
    print(py_assert_all(results, "from pytra std import symbols"))


def _case_main() -> None:
    run_case()


if __name__ == "__main__":
    _case_main()
