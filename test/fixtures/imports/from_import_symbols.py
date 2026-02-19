from __future__ import annotations

from math import floor, sqrt as msqrt
from pylib.tra.assertions import py_assert_all, py_assert_eq, py_assert_true
from pylib.tra.png import write_rgb_png
from time import perf_counter


def run_case() -> None:
    t0: float = perf_counter()
    out_path = "from_import_symbols.png"
    pixels = bytearray([0, 0, 0, 255, 255, 255, 32, 64, 128])
    write_rgb_png(out_path, 1, 3, pixels)
    t1: float = perf_counter()
    results: list[bool] = []
    results.append(py_assert_eq(int(msqrt(81.0)), 9, "from math import sqrt as msqrt"))
    results.append(py_assert_eq(int(floor(3.9)), 3, "from math import floor"))
    results.append(py_assert_true(t1 >= t0, "from time import perf_counter"))
    results.append(py_assert_eq(len(pixels), 9, "from pylib.tra.png import write_rgb_png"))
    print(py_assert_all(results, "from-import symbols"))


def _case_main() -> None:
    run_case()


if __name__ == "__main__":
    _case_main()
