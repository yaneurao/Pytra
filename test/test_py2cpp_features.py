"""py2cpp の主要互換機能を実行レベルで確認する回帰テスト。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.py2cpp import transpile

CPP_RUNTIME_SRCS = [
    "src/cpp_module/ast.cpp",
    "src/cpp_module/pathlib.cpp",
    "src/cpp_module/time.cpp",
    "src/cpp_module/math.cpp",
    "src/cpp_module/dataclasses.cpp",
    "src/cpp_module/sys.cpp",
    "src/cpp_module/png.cpp",
    "src/cpp_module/gif.cpp",
    "src/cpp_module/gc.cpp",
]


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
                ["python", str(py_file)], cwd=ROOT, capture_output=True, text=True
            )
            cpp_run = subprocess.run(
                [str(exe_file)], cwd=ROOT, capture_output=True, text=True
            )
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
def build() -> list[int]:
    return [x + y for x in [1, 2] for y in [10, 20] if y > 10]

if __name__ == "__main__":
    v: list[int] = build()
    print(len(v))
    print(v[0])
    print(v[1])
"""
        py_out, cpp_out = self._run_python_and_cpp(src)
        self.assertEqual(py_out, cpp_out)


if __name__ == "__main__":
    unittest.main()
