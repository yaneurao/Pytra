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
    def test_east_builtin_call_normalization(self) -> None:
        src = """from pathlib import Path

def main() -> None:
    s: str = "  x  "
    xs: list[int] = []
    d: dict[str, int] = {"a": 1}
    p: Path = Path("tmp")
    xs.append(1)
    _ = s.strip()
    _ = d.get("a", 0)
    _ = p.exists()
    print(len(xs))

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "norm.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
        runtime_calls: set[str] = set()
        stack: list[object] = [east]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                if cur.get("kind") == "Call" and cur.get("lowered_kind") == "BuiltinCall":
                    rc = cur.get("runtime_call")
                    if isinstance(rc, str):
                        runtime_calls.add(rc)
                for v in cur.values():
                    stack.append(v)
            elif isinstance(cur, list):
                for it in cur:
                    stack.append(it)
        self.assertIn("list.append", runtime_calls)
        self.assertIn("py_strip", runtime_calls)
        self.assertIn("dict.get", runtime_calls)
        self.assertIn("std::filesystem::exists", runtime_calls)
        self.assertIn("py_len", runtime_calls)
        self.assertIn("py_print", runtime_calls)

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

            case15_py = find_fixture_case("class_member")
            case15_cpp = work / "case15.cpp"
            transpile(case15_py, case15_cpp)
            case15_txt = case15_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Counter {", case15_txt)
            self.assertIn("Counter c = Counter();", case15_txt)
            self.assertNotIn("rc<Counter>", case15_txt)

            case34_py = find_fixture_case("gc_reassign")
            case34_cpp = work / "case34.cpp"
            transpile(case34_py, case34_cpp)
            case34_txt = case34_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Tracked : public PyObj {", case34_txt)
            self.assertIn("rc<Tracked> a = ", case34_txt)
            self.assertIn("rc_new<Tracked>(\"A\")", case34_txt)
            self.assertIn("a = b;", case34_txt)

    def test_dict_get_items_runtime(self) -> None:
        out = self._compile_and_run_fixture("dict_get_items")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_dict_wrapper_methods_runtime(self) -> None:
        out = self._compile_and_run_fixture("dict_wrapper_methods")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_set_wrapper_methods_runtime(self) -> None:
        out = self._compile_and_run_fixture("set_wrapper_methods")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_boolop_value_select_runtime(self) -> None:
        out = self._compile_and_run_fixture("boolop_value_select")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_bytes_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("bytes_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_bytearray_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("bytearray_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_filter_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_filter")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_any_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("any_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_any_none_runtime(self) -> None:
        out = self._compile_and_run_fixture("any_none")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_any_dict_items_runtime(self) -> None:
        out = self._compile_and_run_fixture("any_dict_items")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_any_list_mixed_runtime(self) -> None:
        out = self._compile_and_run_fixture("any_list_mixed")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_nested_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_nested")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_if_chain_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_if_chain")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_range_step_like_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_range_step_like")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_comprehension_range_step_runtime(self) -> None:
        out = self._compile_and_run_fixture("comprehension_range_step")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_ifexp_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_ifexp")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_capture_multiargs_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_capture_multiargs")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_local_state_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_local_state")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_lambda_as_arg_runtime(self) -> None:
        out = self._compile_and_run_fixture("lambda_as_arg")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")


if __name__ == "__main__":
    unittest.main()
