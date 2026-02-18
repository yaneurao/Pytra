"""py2cpp の主要互換機能を実行レベルで確認する回帰テスト。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2cpp import load_east, transpile_to_cpp

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


def transpile(input_py: Path, output_cpp: Path) -> None:
    east = load_east(input_py)
    cpp = transpile_to_cpp(east)
    output_cpp.write_text(cpp, encoding="utf-8")


class Py2CppFeatureTest(unittest.TestCase):
    def _compile_and_run_fixture(self, stem: str) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src_py = find_fixture_case(stem)
            out_cpp = work / f"{stem}.cpp"
            out_exe = work / f"{stem}.out"
            transpile(src_py, out_cpp)
            comp = subprocess.run(
                [
                    "g++",
                    "-std=c++20",
                    "-O2",
                    "-I",
                    "src",
                    str(out_cpp),
                    *CPP_RUNTIME_SRCS,
                    "-o",
                    str(out_exe),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)
            run = subprocess.run([str(out_exe)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            return run.stdout.replace("\r\n", "\n")

    def test_class_storage_strategy_case15_case34(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)

            case15_py = find_fixture_case("case15_class_member")
            case15_cpp = work / "case15.cpp"
            transpile(case15_py, case15_cpp)
            case15_txt = case15_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Counter {", case15_txt)
            self.assertIn("Counter c = Counter();", case15_txt)
            self.assertNotIn("rc<Counter>", case15_txt)

            case34_py = find_fixture_case("case34_gc_reassign")
            case34_cpp = work / "case34.cpp"
            transpile(case34_py, case34_cpp)
            case34_txt = case34_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Tracked : public PyObj {", case34_txt)
            self.assertIn("rc<Tracked> a = ", case34_txt)
            self.assertIn("rc_new<Tracked>(\"A\")", case34_txt)
            self.assertIn("a = b;", case34_txt)

    def test_case41_dict_get_items_runtime(self) -> None:
        out = self._compile_and_run_fixture("case41_dict_get_items")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_case42_boolop_value_select_runtime(self) -> None:
        out = self._compile_and_run_fixture("case42_boolop_value_select")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")


if __name__ == "__main__":
    unittest.main()
