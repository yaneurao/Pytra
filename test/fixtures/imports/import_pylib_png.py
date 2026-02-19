from __future__ import annotations

from pytra.runtime import png
from pytra.runtime.assertions import py_assert_all, py_assert_eq, py_assert_true


def run_case() -> None:
    out_path = "import_pylib_png.png"
    pixels = bytearray([
        255, 0, 0,
        0, 255, 0,
        0, 0, 255,
        255, 255, 255,
    ])
    png.write_rgb_png(out_path, 2, 2, pixels)
    results: list[bool] = []
    results.append(py_assert_eq(len(pixels), 12, "pixels length"))
    results.append(py_assert_true(True, "png call reached"))
    print(py_assert_all(results, "import pylib png"))


def _case_main() -> None:
    run_case()


if __name__ == "__main__":
    _case_main()
