from __future__ import annotations

from time import perf_counter

from pylib.runtime import py_assert_true


def run_case() -> None:
    start: float = perf_counter()
    end: float = perf_counter()
    print(py_assert_true(end >= start, "from time import perf_counter"))


def _case_main() -> None:
    run_case()


if __name__ == "__main__":
    _case_main()
