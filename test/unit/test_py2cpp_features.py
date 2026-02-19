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

from src.common.transpile_cli import dump_codegen_options_text, parse_py2cpp_argv, resolve_codegen_options
from src.py2cpp import load_cpp_module_attr_call_map, load_east, transpile_to_cpp

CPP_RUNTIME_SRCS = [
    "src/runtime/cpp/core/pathlib.cpp",
    "src/runtime/cpp/core/time.cpp",
    "src/runtime/cpp/core/math.cpp",
    "src/runtime/cpp/core/dataclasses.cpp",
    "src/runtime/cpp/core/sys.cpp",
    "src/runtime/cpp/base/io.cpp",
    "src/runtime/cpp/base/bytes_util.cpp",
    "src/runtime/cpp/pylib/png.cpp",
    "src/runtime/cpp/pylib/gif.cpp",
    "src/runtime/cpp/base/gc.cpp",
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
    def test_preset_resolution_and_override(self) -> None:
        neg, bnd, fdiv, mod, iw, sidx, ssli = resolve_codegen_options("native", "", "", "", "", "", "", "")
        self.assertEqual((neg, bnd, fdiv, mod, iw, sidx, ssli), ("off", "off", "native", "native", "64", "native", "byte"))

        neg, bnd, fdiv, mod, iw, sidx, ssli = resolve_codegen_options("balanced", "", "", "", "", "", "", "")
        self.assertEqual((neg, bnd, fdiv, mod, iw, sidx, ssli), ("const_only", "debug", "python", "python", "64", "byte", "byte"))

        neg, bnd, fdiv, mod, iw, sidx, ssli = resolve_codegen_options("python", "", "", "", "", "", "", "")
        self.assertEqual((neg, bnd, fdiv, mod, iw, sidx, ssli), ("always", "always", "python", "python", "bigint", "codepoint", "codepoint"))

        neg, bnd, fdiv, mod, iw, sidx, ssli = resolve_codegen_options("native", "", "", "python", "", "32", "byte", "byte")
        self.assertEqual((neg, bnd, fdiv, mod, iw, sidx, ssli), ("off", "off", "python", "native", "32", "byte", "byte"))

    def test_dump_options_text_contains_resolved_values(self) -> None:
        txt = dump_codegen_options_text("balanced", "const_only", "debug", "python", "python", "64", "byte", "byte")
        self.assertIn("preset: balanced", txt)
        self.assertIn("negative-index-mode: const_only", txt)
        self.assertIn("bounds-check-mode: debug", txt)
        self.assertIn("floor-div-mode: python", txt)
        self.assertIn("mod-mode: python", txt)
        self.assertIn("int-width: 64", txt)
        self.assertIn("str-index-mode: byte", txt)
        self.assertIn("str-slice-mode: byte", txt)

    def test_parse_py2cpp_argv(self) -> None:
        parsed, err = parse_py2cpp_argv(
            [
                "input.py",
                "-o",
                "out.cpp",
                "--preset",
                "balanced",
                "--mod-mode",
                "native",
                "--dump-options",
            ]
        )
        self.assertEqual(err, "")
        self.assertEqual(parsed.get("input"), "input.py")
        self.assertEqual(parsed.get("output"), "out.cpp")
        self.assertEqual(parsed.get("preset"), "balanced")
        self.assertEqual(parsed.get("mod_mode_opt"), "native")
        self.assertEqual(parsed.get("dump_options"), "1")

    def test_reserved_identifier_is_renamed_by_profile_rule(self) -> None:
        src = """def main() -> None:
    auto: int = 1
    print(auto)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "reserved_name.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("int64 py_auto = 1;", cpp)
        self.assertIn("py_print(py_auto);", cpp)

    def test_runtime_call_map_for_math_is_loaded_from_json(self) -> None:
        mp = load_cpp_module_attr_call_map()
        self.assertIn("math", mp)
        self.assertEqual(mp["math"].get("sqrt"), "py_math::sqrt")

    def test_math_module_call_uses_runtime_call_map(self) -> None:
        src = """import math

def main() -> None:
    x: float = math.sqrt(9.0)
    print(x)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "math_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("py_math::sqrt(9.0)", cpp)

    def test_from_import_symbol_uses_runtime_call_map(self) -> None:
        src = """from math import sqrt as msqrt

def main() -> None:
    x: float = msqrt(9.0)
    print(x)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "from_math_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("py_math::sqrt(9.0)", cpp)

    def test_import_module_alias_uses_runtime_call_map(self) -> None:
        src = """import math as m

def main() -> None:
    x: float = m.sqrt(9.0)
    print(x)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "math_alias_call.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)
        self.assertIn("py_math::sqrt(9.0)", cpp)

    def test_floor_div_mode_native_and_python(self) -> None:
        src = """def main() -> None:
    a: int = 7
    b: int = 3
    c: int = a // b
    a //= b
    print(c, a)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "floor_div_mode.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp_native = transpile_to_cpp(east, floor_div_mode="native")
            cpp_python = transpile_to_cpp(east, floor_div_mode="python")
        self.assertIn("a / b", cpp_native)
        self.assertIn("a /= b;", cpp_native)
        self.assertNotIn("py_floordiv(", cpp_native)
        self.assertIn("py_floordiv(a, b)", cpp_python)
        self.assertIn("a = py_floordiv(a, b);", cpp_python)

    def test_mod_mode_native_and_python(self) -> None:
        src = """def main() -> None:
    a: int = 7
    b: int = 3
    c: int = a % b
    a %= b
    print(c, a)

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "mod_mode.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp_native = transpile_to_cpp(east, mod_mode="native")
            cpp_python = transpile_to_cpp(east, mod_mode="python")
        self.assertIn("a % b", cpp_native)
        self.assertIn("a %= b;", cpp_native)
        self.assertNotIn("py_mod(", cpp_native)
        self.assertIn("py_mod(a, b)", cpp_python)
        self.assertIn("a = py_mod(a, b);", cpp_python)

    def test_bounds_check_mode_off_always_debug(self) -> None:
        src = """def main() -> None:
    xs: list[int] = [1, 2, 3]
    i: int = 1
    s: str = "ABC"
    print(xs[i], s[i])

if __name__ == "__main__":
    main()
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "bounds_mode.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp_off = transpile_to_cpp(east, bounds_check_mode="off")
            cpp_always = transpile_to_cpp(east, bounds_check_mode="always")
            cpp_debug = transpile_to_cpp(east, bounds_check_mode="debug")
        self.assertIn("xs[i]", cpp_off)
        self.assertIn("s[i]", cpp_off)
        self.assertNotIn("py_at_bounds(", cpp_off)
        self.assertIn("py_at_bounds(xs, i)", cpp_always)
        self.assertIn("py_at_bounds(s, i)", cpp_always)
        self.assertIn("py_at_bounds_debug(xs, i)", cpp_debug)
        self.assertIn("py_at_bounds_debug(s, i)", cpp_debug)

    def test_int_width_32_and_64(self) -> None:
        src = """def main() -> None:
    x: int = 1
    y: int = x + 2
    print(y)
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "int_width.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp64 = transpile_to_cpp(east, int_width="64")
            cpp32 = transpile_to_cpp(east, int_width="32")
        self.assertIn("int64 x = 1;", cpp64)
        self.assertIn("int32 x = 1;", cpp32)

    def test_ifexp_renders_cpp_ternary(self) -> None:
        src = """def pick(v: int) -> int:
    return 1 if v > 0 else 2
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ifexp.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east, emit_main=False)
        self.assertIn("? 1 : 2", cpp)

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

    def test_cli_reports_user_syntax_error_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_py = Path(tmpdir) / "bad.py"
            bad_py.write_text("def main(:\n    pass\n", encoding="utf-8")
            out_cpp = Path(tmpdir) / "bad.cpp"
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(bad_py), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("[user_syntax_error]", proc.stderr)

    def test_cli_reports_input_invalid_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_json = Path(tmpdir) / "bad.json"
            bad_json.write_text("[1,2,3]", encoding="utf-8")
            out_cpp = Path(tmpdir) / "bad.cpp"
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(bad_json), "-o", str(out_cpp)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("[input_invalid]", proc.stderr)

    def test_cli_dump_options_allows_planned_bigint_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ok.py"
            src_py.write_text("print(1)\n", encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(src_py), "--preset", "python", "--dump-options"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertIn("preset: python", proc.stdout)
            self.assertIn("int-width: bigint", proc.stdout)
            self.assertIn("str-index-mode: codepoint", proc.stdout)
            self.assertIn("str-slice-mode: codepoint", proc.stdout)

    def test_cli_rejects_codepoint_modes_without_dump_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "ok.py"
            src_py.write_text("print(1)\n", encoding="utf-8")
            proc = subprocess.run(
                ["python3", "src/py2cpp.py", str(src_py), "--str-index-mode", "codepoint"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("--str-index-mode=codepoint is not implemented yet", proc.stderr)

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

    def test_from_import_symbols_runtime(self) -> None:
        out = self._compile_and_run_fixture("from_import_symbols")
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

    def test_super_init_runtime(self) -> None:
        out = self._compile_and_run_fixture("super_init")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_import_math_module_runtime(self) -> None:
        out = self._compile_and_run_fixture("import_math_module")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_import_time_from_runtime(self) -> None:
        out = self._compile_and_run_fixture("import_time_from")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_import_pylib_png_runtime(self) -> None:
        out = self._compile_and_run_fixture("import_pylib_png")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_str_index_char_compare_optimized_and_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src_py = find_fixture_case("str_index_char_compare")
            out_cpp = work / "str_index_char_compare.cpp"
            transpile(src_py, out_cpp)
            txt = out_cpp.read_text(encoding="utf-8")
            self.assertIn("s.at(i) == 'B'", txt)
            self.assertIn("s.at(0) != 'B'", txt)
        out = self._compile_and_run_fixture("str_index_char_compare")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_str_for_each_runtime(self) -> None:
        out = self._compile_and_run_fixture("str_for_each")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_str_slice_runtime(self) -> None:
        out = self._compile_and_run_fixture("str_slice")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_enumerate_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("enumerate_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_in_membership_runtime(self) -> None:
        out = self._compile_and_run_fixture("in_membership")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_enum_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("enum_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_intenum_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("intenum_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_intflag_basic_runtime(self) -> None:
        out = self._compile_and_run_fixture("intflag_basic")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
        self.assertGreater(len(lines), 0)
        self.assertEqual(lines[-1], "True")

    def test_emit_guard_rejects_object_receiver_call(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "x", "resolved_type": "object"},
                            "attr": "bit_length",
                        },
                        "args": [],
                        "keywords": [],
                        "resolved_type": "unknown",
                    },
                }
            ],
        }
        with self.assertRaisesRegex(RuntimeError, "object receiver method call"):
            transpile_to_cpp(east)


if __name__ == "__main__":
    unittest.main()
