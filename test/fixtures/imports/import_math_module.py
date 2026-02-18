from __future__ import annotations

import math

from pylib.runtime import py_assert_all, py_assert_eq, py_assert_true


def run_case() -> None:
    results: list[bool] = []
    results.append(py_assert_eq(int(math.sqrt(81.0)), 9, "math.sqrt"))
    results.append(py_assert_eq(int(math.floor(3.9)), 3, "math.floor"))
    results.append(py_assert_true(math.fabs(-2.0) == 2.0, "math.fabs"))
    print(py_assert_all(results, "import math module"))


def _case_main() -> None:
    run_case()


if __name__ == "__main__":
    _case_main()
