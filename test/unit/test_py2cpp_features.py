"""py2cpp の主要互換機能を実行レベルで確認する回帰テスト。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2cpp import transpile

CPP_RUNTIME_SRCS = [
    "src/cpp_module/pathlib.cpp",
    "src/cpp_module/time.cpp",
    "src/cpp_module/math.cpp",
    "src/cpp_module/dataclasses.cpp",
    "src/cpp_module/sys.cpp",
    "src/cpp_module/png.cpp",
    "src/cpp_module/gif.cpp",
    "src/cpp_module/gc.cpp",
]


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2CppFeatureTest(unittest.TestCase):
    def _run_python_and_cpp(self, source: str) -> tuple[str, str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            py_file = work / "case.py"
            cpp_file = work / "case.cpp"
            exe_file = work / "case.out"
            py_file.write_text(source, encoding="utf-8")

            transpile(str(py_file), str(cpp_file))
            compile_cmd = [
                "g++",
                "-std=c++20",
                "-O2",
                "-I",
                "src",
                str(cpp_file),
                *CPP_RUNTIME_SRCS,
                "-o",
                str(exe_file),
            ]
            comp = subprocess.run(
                compile_cmd, cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

            py_run = subprocess.run(
                ["python", str(py_file)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            cpp_run = subprocess.run(
                [str(exe_file)], cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(py_run.returncode, 0, msg=py_run.stderr)
            self.assertEqual(cpp_run.returncode, 0, msg=cpp_run.stderr)
            return py_run.stdout.replace("\r\n", "\n"), cpp_run.stdout.replace("\r\n", "\n")

    def test_augassign_and_floor_div_and_pow(self) -> None:
        src = """
def calc() -> None:
    x: int = 5
    x += 2
    x *= 3
    x //= 2
    y: float = 2.0
    y **= 3
    print(x)
    print(y)

if __name__ == "__main__":
    calc()
"""
        py_out, cpp_out = self._run_python_and_cpp(src)
        # py_print は float の .0 を省略するため、行ごとに数値比較する。
        py_lines = py_out.strip().splitlines()
        cpp_lines = cpp_out.strip().splitlines()
        self.assertEqual(py_lines[0], cpp_lines[0])
        self.assertAlmostEqual(float(py_lines[1]), float(cpp_lines[1]), places=9)

    def test_chained_compare_and_main_rename(self) -> None:
        src = """
def main() -> int:
    return 3

def ok(v: int) -> bool:
    return 0 <= v < 5

if __name__ == "__main__":
    print(main())
    print(ok(3))
    print(ok(9))
"""
        py_out, cpp_out = self._run_python_and_cpp(src)
        self.assertEqual(py_out, cpp_out)

    def test_list_pop_variants_and_subscript_assign(self) -> None:
        src = """
def run() -> None:
    a: list[int] = [10, 20, 30, 40]
    a[1] = 25
    v1: int = a.pop()
    v2: int = a.pop(0)
    print(v1)
    print(v2)
    print(a[0])
    print(len(a))

if __name__ == "__main__":
    run()
"""
        py_out, cpp_out = self._run_python_and_cpp(src)
        self.assertEqual(py_out, cpp_out)

    def test_append_extend_and_subscript_assign(self) -> None:
        src = """
def run() -> None:
    a: list[int] = []
    a.append(1)
    a.extend([2, 3, 4])
    a[2] = 9
    print(len(a))
    print(a[0])
    print(a[2])

if __name__ == "__main__":
    run()
"""
        py_out, cpp_out = self._run_python_and_cpp(src)
        self.assertEqual(py_out, cpp_out)

    def test_nested_list_comprehension(self) -> None:
        src = """
if __name__ == "__main__":
    v = [x + y for x in [1, 2] for y in [10, 20] if y > 10]
    print(len(v))
    print(v[0])
    print(v[1])
"""
        py_out, cpp_out = self._run_python_and_cpp(src)
        self.assertEqual(py_out, cpp_out)

    def test_int_str_string_index_chained_compare_and_negative_mod(self) -> None:
        src = """
def run() -> None:
    n: int = int("42")
    s: str = "abc"
    ch: str = s[1]
    print(n)
    print(ch)
    print("a" <= ch <= "z")
    print((-7) // 3)
    print((-7) % 3)

if __name__ == "__main__":
    run()
"""
        py_out, cpp_out = self._run_python_and_cpp(src)
        self.assertEqual(py_out, cpp_out)

    def test_gif_helper_python_cpp_compat(self) -> None:
        src = """
from py_module.gif_helper import grayscale_palette, save_gif

def run() -> None:
    w: int = 4
    h: int = 4
    fr0: bytes = bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    fr1: bytes = bytes([15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0])
    frames: list[bytes] = [fr0, fr1]
    out_path: str = "case.gif"
    save_gif(out_path, w, h, frames, grayscale_palette(), 4, 0)

if __name__ == "__main__":
    run()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            py_file = work / "case.py"
            cpp_file = work / "case.cpp"
            exe_file = work / "case.out"
            py_gif = work / "py.gif"
            cpp_gif = work / "cpp.gif"
            py_file.write_text(src, encoding="utf-8")

            transpile(str(py_file), str(cpp_file))
            comp = subprocess.run(
                ["g++", "-std=c++20", "-O2", "-I", "src", str(cpp_file), *CPP_RUNTIME_SRCS, "-o", str(exe_file)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

            py_run = subprocess.run(
                ["python", str(py_file)],
                cwd=work,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            self.assertEqual(py_run.returncode, 0, msg=py_run.stderr)
            (work / "case.gif").replace(py_gif)

            cpp_run = subprocess.run([str(exe_file)], cwd=work, capture_output=True, text=True)
            self.assertEqual(cpp_run.returncode, 0, msg=cpp_run.stderr)
            (work / "case.gif").replace(cpp_gif)

            py_bytes = py_gif.read_bytes()
            cpp_bytes = cpp_gif.read_bytes()
            self.assertEqual(py_bytes, cpp_bytes)

    def test_class_storage_strategy_case15_case34(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)

            case15_py = find_fixture_case("case15_class_member")
            case15_cpp = work / "case15.cpp"
            transpile(str(case15_py), str(case15_cpp))
            case15_txt = case15_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Counter {", case15_txt)
            self.assertIn("Counter c = Counter();", case15_txt)
            self.assertNotIn("rc<Counter>", case15_txt)

            case34_py = find_fixture_case("case34_gc_reassign")
            case34_cpp = work / "case34.cpp"
            transpile(str(case34_py), str(case34_cpp))
            case34_txt = case34_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Tracked : public PyObj {", case34_txt)
            self.assertIn("rc<Tracked> a = rc_new<Tracked>(\"A\");", case34_txt)
            self.assertIn("a = b;", case34_txt)


if __name__ == "__main__":
    unittest.main()
