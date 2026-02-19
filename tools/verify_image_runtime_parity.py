#!/usr/bin/env python3
"""Verify parity between Python canonical image runtimes and C++ runtimes.

This script generates tiny PNG/GIF outputs with:
- Python canonical implementations: src/pylib/png.py, src/pylib/gif.py
- C++ runtimes: src/runtime/cpp/pytra/runtime/png.cpp, src/runtime/cpp/pytra/runtime/gif.cpp

It compares resulting bytes and exits non-zero on mismatch.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _write_cpp_harness(path: Path) -> None:
    src = r'''
#include "runtime/cpp/pytra/runtime/png.h"
#include "runtime/cpp/pytra/runtime/gif.h"

#include <cstdint>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc < 3) return 2;
    std::string out_png = argv[1];
    std::string out_gif = argv[2];

    std::vector<std::uint8_t> png_pixels = {
        255, 0, 0,
        0, 255, 0,
        0, 0, 255,
        255, 255, 255,
    };
    pytra::png::write_rgb_png(out_png, 2, 2, png_pixels);

    std::vector<std::uint8_t> frame0 = {0, 1, 2, 3};
    std::vector<std::uint8_t> frame1 = {3, 2, 1, 0};
    std::vector<std::vector<std::uint8_t>> frames = {frame0, frame1};
    auto palette = pytra::gif::grayscale_palette();
    pytra::gif::save_gif(out_gif, 2, 2, frames, palette, 4, 0);
    return 0;
}
'''
    path.write_text(src, encoding="utf-8")


def _build_and_run_cpp(work: Path, out_png: Path, out_gif: Path) -> None:
    if shutil.which("g++") is None:
        raise RuntimeError("g++ is required for image parity verification")

    harness = work / "image_parity_harness.cpp"
    exe = work / "image_parity_harness.out"
    _write_cpp_harness(harness)
    cmd_compile = [
        "g++",
        "-std=c++20",
        "-O2",
        "-I",
        "src",
        "-I",
        "src/runtime/cpp",
        str(harness),
        "src/runtime/cpp/pytra/runtime/png.cpp",
        "src/runtime/cpp/pytra/runtime/gif.cpp",
        "src/runtime/cpp/base/io.cpp",
        "src/runtime/cpp/base/bytes_util.cpp",
        "-o",
        str(exe),
    ]
    comp = subprocess.run(cmd_compile, cwd=ROOT, capture_output=True, text=True)
    if comp.returncode != 0:
        raise RuntimeError(f"compile failed:\n{comp.stderr}")
    run = subprocess.run([str(exe), str(out_png), str(out_gif)], cwd=ROOT, capture_output=True, text=True)
    if run.returncode != 0:
        raise RuntimeError(f"runtime failed:\nstdout={run.stdout}\nstderr={run.stderr}")


def _run_python_canonical(out_png: Path, out_gif: Path) -> None:
    import sys

    sys.path.insert(0, str((ROOT / "src").resolve()))
    from pylib.tra import gif, png

    png_pixels = bytearray(
        [
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            255,
            255,
            255,
        ]
    )
    png.write_rgb_png(str(out_png), 2, 2, png_pixels)

    frames = [bytes([0, 1, 2, 3]), bytes([3, 2, 1, 0])]
    palette = gif.grayscale_palette()
    gif.save_gif(str(out_gif), 2, 2, frames, palette, delay_cs=4, loop=0)


def _assert_same_bytes(path_a: Path, path_b: Path, label: str) -> None:
    a = path_a.read_bytes()
    b = path_b.read_bytes()
    if a != b:
        raise RuntimeError(
            f"{label} mismatch: {path_a} ({len(a)} bytes) != {path_b} ({len(b)} bytes)"
        )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        py_png = work / "py.png"
        py_gif = work / "py.gif"
        cpp_png = work / "cpp.png"
        cpp_gif = work / "cpp.gif"

        _run_python_canonical(py_png, py_gif)
        _build_and_run_cpp(work, cpp_png, cpp_gif)

        _assert_same_bytes(py_png, cpp_png, "png")
        _assert_same_bytes(py_gif, cpp_gif, "gif")
    print("True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
